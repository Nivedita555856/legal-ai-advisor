"""
run_all.py  —  Full pipeline: clear → ingest → verify → test query
Run from backend/ with venv active:
    python run_all.py
"""
import sys, os, asyncio, json, time

# Always load the root .env first (correct keys)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)

from config import settings
from loguru import logger

DATA_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "data", "raw")
)

# ─────────────────────────────────────────────────────────────────────────────
def banner(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")

# ─────────────────────────────────────────────────────────────────────────────
def step1_clear_pinecone():
    banner("STEP 1 — Clearing Pinecone index")
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=settings.pinecone_api_key)
        idx = pc.Index(settings.pinecone_index_name)
        stats_before = idx.describe_index_stats()
        count_before = stats_before.total_vector_count
        print(f"  Vectors before: {count_before}")
        if count_before > 0:
            idx.delete(delete_all=True)
            time.sleep(3)
            print("  Deleted all vectors.")
        else:
            print("  Index already empty.")
        return True
    except Exception as e:
        print(f"  ERROR clearing Pinecone: {e}")
        return False

# ─────────────────────────────────────────────────────────────────────────────
def step2_clear_supabase():
    banner("STEP 2 — Clearing Supabase metadata")
    try:
        from supabase import create_client
        client = create_client(settings.supabase_url, settings.supabase_service_key)
        # Try to delete all documents
        client.table("documents").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print("  Supabase documents table cleared.")
        return True
    except Exception as e:
        print(f"  Supabase clear skipped (RLS or key issue): {e}")
        print("  Continuing without Supabase — Pinecone is the primary store.")
        return False

# ─────────────────────────────────────────────────────────────────────────────
async def step3_ingest():
    banner("STEP 3 — Ingesting all documents into Pinecone")
    from ingestion.ingest import DocumentIngester

    supported = {".pdf", ".txt", ".md"}
    files = sorted([
        f for f in os.listdir(DATA_DIR)
        if os.path.splitext(f)[1].lower() in supported
    ])

    if not files:
        print(f"  No files found in {DATA_DIR}")
        return 0

    print(f"  Found {len(files)} documents\n")
    ingester = DocumentIngester()
    ok, fail = 0, 0
    total_chunks = 0

    for i, fname in enumerate(files, 1):
        fpath = os.path.join(DATA_DIR, fname)
        print(f"  [{i:02d}/{len(files)}] {fname}", end=" ... ", flush=True)
        try:
            result = await ingester.ingest_file(fpath, fname)
            chunks = result["chunks"]
            total_chunks += chunks
            print(f"OK  ({chunks} chunks)")
            ok += 1
        except Exception as e:
            print(f"FAILED: {e}")
            fail += 1

    print(f"\n  Ingested: {ok}/{len(files)} documents | {total_chunks} total chunks")
    return total_chunks

# ─────────────────────────────────────────────────────────────────────────────
def step4_verify():
    banner("STEP 4 — Verifying Pinecone index")
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=settings.pinecone_api_key)
        idx = pc.Index(settings.pinecone_index_name)
        time.sleep(3)
        stats = idx.describe_index_stats()
        count = stats.total_vector_count
        print(f"  Pinecone vector count: {count}")
        if count > 0:
            print("  Pinecone index is ready.")
            return True
        else:
            print("  WARNING: No vectors found in Pinecone.")
            return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

# ─────────────────────────────────────────────────────────────────────────────
async def step5_test_query():
    banner("STEP 5 — Running live test query")
    from llm.groq_client import GroqClient
    from tools.vector_store import VectorStore

    print(f"  Model: {settings.groq_model}")
    query = "What is the notice period in an employment contract under Indian law?"
    print(f"  Query: {query}\n")

    try:
        vs = VectorStore()
        chunks = vs.search(query, top_k=5)
        if not chunks:
            print("  No chunks retrieved — index may need a moment to be ready.")
            return

        context = "\n\n".join([
            f"[{c.get('document','')}]: {c.get('text','')[:300]}"
            for c in chunks[:3]
        ])

        llm = GroqClient()
        prompt = f"""You are an expert Indian legal awareness advisor. Answer in plain English.
Do not use asterisks, markdown, or emojis. Write in clear numbered paragraphs.

Query: {query}

Relevant legal content:
{context}

Answer with:
1. DIRECT ANSWER
2. LEGAL BASIS (cite section/act)
3. ACTIONABLE STEP
4. WHERE TO VERIFY (link)

Answer:"""

        answer = await llm.generate(prompt, temperature=0.1, max_tokens=800)
        print(answer)

        print(f"\n  Sources used:")
        for c in chunks[:3]:
            score = round(c.get("score", 0), 3)
            print(f"    - {c.get('document','')} (score: {score})")

    except Exception as e:
        print(f"  Query failed: {e}")

# ─────────────────────────────────────────────────────────────────────────────
async def main():
    print("\n" + "="*60)
    print("  AI Legal Advisor — Full Pipeline Runner")
    print("="*60)
    print(f"  Groq model : {settings.groq_model}")
    print(f"  Pinecone   : {settings.pinecone_index_name}")
    print(f"  Data dir   : {DATA_DIR}")

    step1_clear_pinecone()
    step2_clear_supabase()
    total_chunks = await step3_ingest()

    if total_chunks == 0:
        print("\nERROR: No documents ingested. Check data/raw/ directory.")
        sys.exit(1)

    ready = step4_verify()
    if ready:
        await step5_test_query()

    banner("DONE")
    print("  Your Pinecone index is loaded and the AI is ready.")
    print("  Next: run your FastAPI backend and open the frontend.")
    print()

if __name__ == "__main__":
    asyncio.run(main())
