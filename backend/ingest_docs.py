"""
Standalone ingestion runner for data/raw documents.
Run from backend/ folder with venv active:
    python ingest_docs.py
    python ingest_docs.py path/to/file.md
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


async def main():
    from ingestion.ingest import DocumentIngester

    print("=" * 55)
    print("  AI Legal Advisor - Document Ingestion Runner")
    print("=" * 55)

    if len(sys.argv) > 1:
        target = os.path.abspath(sys.argv[1])
    else:
        target = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "data", "raw")
        )

    print(f"\nTarget: {target}\n")

    if not os.path.exists(target):
        print(f"ERROR: Path not found: {target}")
        sys.exit(1)

    ingester = DocumentIngester()

    if os.path.isfile(target):
        print(f"Ingesting: {os.path.basename(target)}")
        result = await ingester.ingest_file(target)
        print(f"Done - {result['chunks']} chunks, {result['characters']:,} chars")

    elif os.path.isdir(target):
        supported = {".pdf", ".txt", ".md"}
        files = sorted([
            f for f in os.listdir(target)
            if os.path.splitext(f)[1].lower() in supported
        ])

        if not files:
            print("No supported files (.pdf .txt .md) found.")
            sys.exit(0)

        size_info = []
        for f in files:
            kb = os.path.getsize(os.path.join(target, f)) // 1024
            size_info.append((f, kb))

        print(f"Found {len(files)} document(s):\n")
        for fname, kb in size_info:
            print(f"  - {fname}  ({kb} KB)")
        print()

        results = []
        errors = []
        total = len(files)

        for idx, fname in enumerate(files, 1):
            fpath = os.path.join(target, fname)
            try:
                print(f"  [{idx}/{total}] {fname} ...", end=" ", flush=True)
                result = await ingester.ingest_file(fpath, fname)
                results.append(result)
                print(f"OK  ({result['chunks']} chunks)")
            except Exception as e:
                errors.append((fname, str(e)))
                print(f"FAILED: {e}")

        print("\n" + "=" * 55)
        print(f"  Ingested : {len(results)} / {total}")
        if errors:
            print(f"  Errors   : {len(errors)}")
            for n, e in errors:
                print(f"    x {n}: {e}")
        print("=" * 55)
        if results:
            print("\nDone! Open http://localhost:3000 to query your documents.")


if __name__ == "__main__":
    asyncio.run(main())
