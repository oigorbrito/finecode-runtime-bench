"""Diagnostic-only Go overlay: align Windows USERPROFILE with a test's HOME fixture.

Does not alter pinned candidate source on disk; go test -overlay loads a copy.
"""
import argparse
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--source", required=True)
p.add_argument("--out-dir", required=True)
args = p.parse_args()
src = Path(args.source).resolve()
out = Path(args.out_dir).resolve()
out.mkdir(parents=True, exist_ok=True)
original = src.read_text(encoding="utf-8")
old = 't.Setenv("HOME", home)'
new = 't.Setenv("HOME", home)\n\tt.Setenv("USERPROFILE", home)'
if original.count(old) != 1:
    raise SystemExit(f"expected one fixture assignment in {src}, found {original.count(old)}")
replacement = out / src.name
replacement.write_text(original.replace(old, new), encoding="utf-8")
overlay = out / "overlay.json"
overlay.write_text(json.dumps({"Replace": {str(src): str(replacement)}}, indent=2), encoding="utf-8")
print(f"Diagnostic Go overlay: {overlay}")
