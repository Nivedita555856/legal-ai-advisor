"""
Upload all legal documents to the deployed Render backend.
Run: python upload_docs.py
"""
import os, sys, time

try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system(f"{sys.executable} -m pip install requests -q")
    import requests

BACKEND = "https://legal-ai-advisor-sspd.onrender.com/api"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "raw")

def wake(max_seconds=90):
    print("Checking backend...", end=" ", flush=True)
    for _ in range(max_seconds // 10):
        try:
            r = requests.get(f"{BACKEND}/health", timeout=15)
            if r.status_code == 200:
                print("UP")
                return True
        except Exception:
            pass
        print(".", end="", flush=True)
        time.sleep(10)
    print("\nBackend not responding.")
    return False

def upload(path, name):
    with open(path, "rb") as f:
        content = f.read()
    resp = requests.post(
        f"{BACKEND}/upload",
        files={"file": (name, content, "text/plain")},
        data={"doc_name": name},
        timeout=120,
    )
    return resp

def main():
    files = sorted([
        f for f in os.listdir(DATA_DIR)
        if f.endswith((".md", ".txt", ".pdf"))
    ])
    if not files:
        print(f"No files found in {DATA_DIR}")
        sys.exit(1)

    print(f"Found {len(files)} files to upload\n")
    if not wake():
        sys.exit(1)

    ok = fail = 0
    for i, fname in enumerate(files, 1):
        fpath = os.path.join(DATA_DIR, fname)
        print(f"[{i}/{len(files)}] {fname} ... ", end="", flush=True)
        try:
            r = upload(fpath, fname)
            if r.status_code == 200:
                data = r.json()
                print(f"OK ({data.get('chunks','?')} chunks)")
                ok += 1
            else:
                print(f"FAILED ({r.status_code}): {r.text[:120]}")
                fail += 1
        except Exception as e:
            print(f"ERROR: {e}")
            fail += 1
        time.sleep(0.5)

    print(f"\nDone: {ok} uploaded, {fail} failed")

    if ok > 0:
        print("\nVerifying...")
        try:
            stats = requests.get(f"{BACKEND}/documents/stats", timeout=20).json()
            docs  = requests.get(f"{BACKEND}/documents", timeout=20).json()
            print(f"  Pinecone vectors : {stats.get('stats',{}).get('total_vector_count','?')}")
            print(f"  Supabase records : {docs.get('count','?')}")
        except Exception as e:
            print(f"  Could not verify: {e}")

        print("\nRunning test query...")
        try:
            r = requests.post(
                f"{BACKEND}/query",
                json={"query": "What is the notice period in an employment contract in India?", "jurisdiction": "India"},
                timeout=120,
            )
            d = r.json()
            ans = d.get("answer", "")
            print(f"\nAnswer preview:\n{ans[:400]}...")
            print(f"\nRisk: {d.get('risk_score', {})}")
        except Exception as e:
            print(f"  Query failed: {e}")

if __name__ == "__main__":
    main()
