from pinecone import Pinecone, ServerlessSpec
from loguru import logger
from typing import List, Dict
import time
import requests
from config import settings


def embed_text(text: str) -> List[float]:
    """Direct REST call to Gemini API — no SDK, no version issues."""
    try:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.embedding_model}:embedContent?key={settings.gemini_api_key}"
        )
        payload = {
            "content": {"parts": [{"text": text[:8000]}]},
            "outputDimensionality": settings.embedding_dimension,
        }
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()["embedding"]["values"]
    except Exception as e:
        logger.error(f"Embed error: {e}")
        return [0.0] * settings.embedding_dimension


class VectorStore:
    def __init__(self):
        self.pc = None
        self.index = None
        try:
            self.pc = Pinecone(api_key=settings.pinecone_api_key)
            self._ensure_index()
            self.index = self.pc.Index(settings.pinecone_index_name)
            logger.info("Pinecone index connected")
        except Exception as e:
            logger.warning(f"Pinecone init skipped: {e}")

    def _ensure_index(self):
        existing = {idx.name: idx for idx in self.pc.list_indexes()}
        if settings.pinecone_index_name in existing:
            idx_info = existing[settings.pinecone_index_name]
            current_dim = getattr(idx_info, 'dimension', settings.embedding_dimension)
            if current_dim != settings.embedding_dimension:
                logger.info(f"Recreating index: {current_dim} -> {settings.embedding_dimension} dims")
                self.pc.delete_index(settings.pinecone_index_name)
                time.sleep(10)
            else:
                return
        self.pc.create_index(
            name=settings.pinecone_index_name,
            dimension=settings.embedding_dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        logger.info(f"Pinecone index created ({settings.embedding_dimension} dims)")

    def _embed(self, text: str) -> List[float]:
        return embed_text(text)

    def upsert(self, vectors: List[Dict]):
        if not self.index:
            return
        try:
            for i in range(0, len(vectors), 100):
                self.index.upsert(vectors=vectors[i:i + 100])
        except Exception as e:
            logger.error(f"Upsert error: {e}")

    def search(self, query: str, top_k: int = 10, filter: Dict = None) -> List[Dict]:
        if not self.index:
            return []
        try:
            embedding = embed_text(query)
            kwargs = {"vector": embedding, "top_k": top_k, "include_metadata": True}
            if filter:
                kwargs["filter"] = filter
            result = self.index.query(**kwargs)
            return [
                {
                    "id": m.id, "score": m.score,
                    "text": m.metadata.get("text", ""),
                    "document": m.metadata.get("document", ""),
                    "doc_id": m.metadata.get("doc_id", ""),
                    "chunk_index": m.metadata.get("chunk_index", 0),
                    "page": m.metadata.get("page", 0),
                }
                for m in result.matches
            ]
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def get_stats(self) -> Dict:
        if not self.index:
            return {}
        try:
            return self.index.describe_index_stats().to_dict()
        except Exception:
            return {}

    def delete_all(self):
        if not self.index:
            return
        try:
            self.index.delete(delete_all=True)
        except Exception as e:
            logger.error(f"Delete error: {e}")

    def delete_by_doc_id(self, doc_id: str):
        if not self.index:
            return
        try:
            self.index.delete(filter={"doc_id": doc_id})
        except Exception as e:
            logger.error(f"Delete error: {e}")
