"""
upload_docs.py — Upload all legal documents to the deployed backend.
Run from the project root:
    python upload_docs.py
"""

import os
import sys
import time
import requests

# ── Configuration ──────────────────────────────────────────────────────────────
BACKEND_URL = "https://legal-ai-advisor-sspd.onrender.com"
DATA_DIR    = os.path.join(os.path.dirname(__file__), "data", "raw")
TIMEOUT     = 120   # seconds per request (Render cold start can be slow)

# ── Helpers ────────────────────────────────────────────────────────────────────

def wake_backend(max_wait: int = 120) -> bool:
    """Hit the health endpoint and wait until the server responds."""
    print(f"Waking backend at {BACKEND_URL} ...")
    health_url = f"{BACKEND_URL}/api/health"
    deadline = time.time() + max_wait
    attempt = 0
    while time.time() < deadline:
        attempt += 1
        try:
            r = requests.get(health_url, timeout=30)
            if r.status_code == 200:
                print(f"  Backend is up! (attempt {attempt})")
                return True
            else:
                print(f"  Attempt {attempt}: HTTP {r.status_code} — retrying...")
        except requests.exceptions.ConnectionError:
            print(f"  Attempt {attempt}: connection refused — server may be starting...")
        except requests.exceptions.Timeout:
            print(f"  Attempt {attempt}: timed out — still waiting...")
        except Exception as e:
            print(f"  Attempt {attempt}: error — {e}")
        time.sleep(10)
    return False


def upload_file(fpath: str) -> bool:
    """Upload a single file; return True on success."""
    fname = os.path.basename(fpath)
    url   = f"{BACKEND_URL}/api/upload"
    try:
        with open(fpath, "rb") as fh:
            r = requests.post(
                url,
                files={"file": (fname, fh, "text/plain")},
                data={"doc_name": fname},
                timeout=TIMEOUT,
            )
        if r.status_code == 200:
            data = r.json()
            chunks = data.get("chunks", "?")
            print(f"  OK  — {fname} ({chunks} chunks)")
            return True
        else:
            print(f"  FAIL — {fname}: HTTP {r.status_code}: {r.text[:200]}")
            return False
    except requests.exceptions.Timeout:
        print(f"  FAIL — {fname}: request timed out after {TIMEOUT}s")
        return False
    except Exception as e:
        print(f"  FAIL — {fname}: {e}")
        return False


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    # 1. Collect files
    supported = {".pdf", ".txt", ".md"}
    if not os.path.isdir(DATA_DIR):
        print(f"ERROR: data directory not found: {DATA_DIR}")
        sys.exit(1)

    files = sorted([
        os.path.join(DATA_DIR, f)
        for f in os.listdir(DATA_DIR)
        if os.path.splitext(f)[1].lower() in supported
    ])

    if not files:
        print("No files found in data/raw/")
        sys.exit(1)

    print(f"\nFound {len(files)} document(s) to upload:")
    for f in files:
        print(f"  - {os.path.basename(f)}")
    print()

    # 2. Wake the backend first
    if not wake_backend(max_wait=120):
        print("\nERROR: Backend did not respond within 120 seconds.")
        print("Check your Render dashboard — the service may have an error.")
        sys.exit(1)

    print()

    # 3. Upload each file
    ok   = 0
    fail = 0
    for i, fpath in enumerate(files, 1):
        print(f"[{i}/{len(files)}] Uploading {os.path.basename(fpath)} ...", end=" ", flush=True)
        # Brief pause between uploads so Render doesn't get overloaded
        if i > 1:
            time.sleep(2)
        if upload_file(fpath):
            ok += 1
        else:
            fail += 1

    # 4. Summary
    print(f"\n{'='*50}")
    print(f"Upload complete: {ok} succeeded, {fail} failed")

    if ok > 0:
        # Verify via stats
        print("\nVerifying vector store ...")
        try:
            r = requests.get(f"{BACKEND_URL}/api/documents/stats", timeout=30)
            if r.status_code == 200:
                stats = r.json().get("stats", {})
                total = stats.get("total_vector_count", "unknown")
                print(f"  Pinecone now has {total} vectors")
            docs_r = requests.get(f"{BACKEND_URL}/api/documents", timeout=30)
            if docs_r.status_code == 200:
                count = docs_r.json().get("count", "?")
                print(f"  Supabase has {count} document records")
        except Exception as e:
            print(f"  Could not verify: {e}")

    if fail == 0:
        print("\nAll documents uploaded successfully!")
        print("Your app is ready — visit the frontend and ask a legal question.")
    else:
        print(f"\n{fail} file(s) failed. Re-run this script to retry.")


if __name__ == "__main__":
    main()
