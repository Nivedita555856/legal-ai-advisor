"""
Run this once to fix any UTF-16 encoded Python files back to clean UTF-8.
Usage: python fix_encoding.py
"""
import os, pathlib, sys

backend_dir = pathlib.Path(__file__).parent
fixed = []
skipped = []
errors = []

for py_file in backend_dir.rglob("*.py"):
    # Skip venv
    if "venv" in py_file.parts or "__pycache__" in py_file.parts:
        continue
    try:
        raw = py_file.read_bytes()
        # Check for UTF-16 BOM or null bytes
        has_bom = raw[:2] in (b"\xff\xfe", b"\xfe\xff")
        has_nulls = b"\x00" in raw

        if has_bom or has_nulls:
            # Decode from UTF-16 and re-encode as UTF-8
            if has_bom:
                text = raw.decode("utf-16")
            else:
                # Null bytes without BOM: try stripping them
                text = raw.replace(b"\x00", b"").decode("utf-8", errors="ignore")
            clean = text.encode("utf-8")
            py_file.write_bytes(clean)
            fixed.append(str(py_file.relative_to(backend_dir)))
        else:
            skipped.append(str(py_file.relative_to(backend_dir)))
    except Exception as e:
        errors.append(f"{py_file.relative_to(backend_dir)}: {e}")

print(f"\nFixed {len(fixed)} file(s):")
for f in fixed:
    print(f"  FIXED: {f}")

print(f"\nClean {len(skipped)} file(s) - no changes needed")

if errors:
    print(f"\nErrors ({len(errors)}):")
    for e in errors:
        print(f"  ERROR: {e}")

print("\nDone. Now run: uvicorn main:app --reload --port 8000")
