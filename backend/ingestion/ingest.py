import os
import sys
import uuid
import re
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger

# Allow running directly: python ingestion/ingest.py
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

import pypdf
from config import settings
from tools.vector_store import VectorStore
from tools.supabase_client import SupabaseClient
from tools.knowledge_graph import KnowledgeGraph


class DocumentIngester:
    """Ingests legal documents: extract → chunk → embed → store."""

    def __init__(self):
        self.vector_store = VectorStore()
        self.supabase = SupabaseClient()
        self.kg = KnowledgeGraph()
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap

    # ── Public ──────────────────────────────────────────────────────────────
    async def ingest_file(self, file_path: str, doc_name: str = None) -> Dict:
        """Ingest a single file (PDF or TXT)."""
        path = Path(file_path)
        doc_name = doc_name or path.name
        doc_id = str(uuid.uuid4())
        logger.info(f"Ingesting: {doc_name} [{doc_id}]")

        # Extract text
        if path.suffix.lower() == ".pdf":
            text = self._extract_pdf(file_path)
        else:
            text = path.read_text(errors="ignore")

        # Chunk
        chunks = self._chunk_text(text)
        logger.info(f"  {len(chunks)} chunks created")

        # Embed & upsert into Pinecone
        vectors = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_{i}"
            emb = self.vector_store._embed(chunk)
            vectors.append({
                "id": chunk_id,
                "values": emb,
                "metadata": {
                    "text": chunk,
                    "document": doc_name,
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "page": 0,
                },
            })
        if vectors:
            self.vector_store.upsert(vectors)

        # Save to Supabase
        doc_record = {
            "id": doc_id,
            "name": doc_name,
            "file_type": path.suffix.lower(),
            "content": text[:5000],
            "chunk_count": len(chunks),
        }
        await self.supabase.insert_document(doc_record)

        # Add to knowledge graph
        self.kg.add_document(doc_id, doc_name, path.suffix.lower())
        parties = self._extract_parties(text)
        for party in parties:
            self.kg.add_party(party, "unknown", doc_id)

        return {
            "doc_id": doc_id,
            "doc_name": doc_name,
            "chunks": len(chunks),
            "characters": len(text),
        }

    async def ingest_directory(self, directory: str) -> List[Dict]:
        """Ingest all documents in a directory."""
        results = []
        for fpath in Path(directory).glob("**/*"):
            if fpath.suffix.lower() in [".pdf", ".txt", ".md"]:
                try:
                    result = await self.ingest_file(str(fpath))
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to ingest {fpath}: {e}")
        return results

    # ── Helpers ─────────────────────────────────────────────────────────────
    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from a PDF."""
        text = ""
        try:
            reader = pypdf.PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text() or ""
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
        return text

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        text = re.sub(r"\s+", " ", text).strip()
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk)
            start += self.chunk_size - self.chunk_overlap
        return chunks

    def _extract_parties(self, text: str) -> List[str]:
        """Simple regex to extract party names from legal text."""
        patterns = [
            r"between\s+([A-Z][a-zA-Z\s]+(?:Ltd|Inc|Corp|LLP|Pvt|Limited)?)\s+and",
            r"Party\s+A[:\s]+([A-Z][a-zA-Z\s]+)",
            r"Party\s+B[:\s]+([A-Z][a-zA-Z\s]+)",
        ]
        parties = set()
        for pattern in patterns:
            matches = re.findall(pattern, text[:3000])
            parties.update(m.strip() for m in matches if len(m.strip()) > 3)
        return list(parties)[:5]


if __name__ == "__main__":
    async def run():
        ingester = DocumentIngester()

        # Default: ingest data/raw/
        if len(sys.argv) > 1:
            target = os.path.abspath(sys.argv[1])
        else:
            target = os.path.normpath(
                os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")
            )

        print(f"\nIngesting from: {target}\n")

        if os.path.isfile(target):
            result = await ingester.ingest_file(target)
            print(f"Done: {result['doc_name']} — {result['chunks']} chunks")

        elif os.path.isdir(target):
            supported = {".pdf", ".txt", ".md"}
            files = sorted([
                f for f in os.listdir(target)
                if Path(f).suffix.lower() in supported
            ])
            print(f"Found {len(files)} file(s): {', '.join(files)}\n")

            ok, fail = 0, 0
            for fname in files:
                fpath = os.path.join(target, fname)
                try:
                    print(f"  [{ok+fail+1}/{len(files)}] {fname} ...", end=" ", flush=True)
                    r = await ingester.ingest_file(fpath, fname)
                    print(f"OK ({r['chunks']} chunks)")
                    ok += 1
                except Exception as e:
                    print(f"FAILED: {e}")
                    fail += 1

            print(f"\nResult: {ok} ingested, {fail} failed")
            if ok:
                print("Documents ready — start the server and open http://localhost:3000")
        else:
            print(f"ERROR: Path not found: {target}")

    asyncio.run(run())
