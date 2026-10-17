#!/usr/bin/env python3
"""Bounded text read subset oracle, pinned Pi read.ts lines 156-204.

No claim of full Pi parity; tests text within upstream truncation thresholds.
"""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--binary", required=True)
p.add_argument("--out", required=True)
args = p.parse_args()
binary = str(Path(args.binary).resolve())
fixtures = [
    ("empty", "", [(None, None), (1, 1), (2, None)]),
    ("trailing-newline", "alpha\nbeta\n", [(None, None), (2, None), (3, None), (4, None), (1, 2), (0, 1)]),
    ("unicode", "olá 🧪\nβήτα\nx", [(None, None), (2, 1), (-1, 1)]),
    ("crlf", "a\r\nb\r\n", [(None, None), (2, 1)]),
    ("one-line", "abc", [(None, None), (1, 0), (1, 1), (1, 2)]),
]
reports = []
with tempfile.TemporaryDirectory() as directory:
    for name, content, cases in fixtures:
        file = Path(directory, name + ".txt")
        file.write_bytes(content.encode("utf-8"))
        lines = content.split("\n")
        for offset, limit in cases:
            command = [binary, "read-subset", str(file)]
            if offset is not None:
                command.append(str(offset))
            if limit is not None:
                command.append(str(limit))
            start = max(0, (offset if offset is not None else 1) - 1)
            if offset == 0:
                start = 0
            invalid = start >= len(lines)
            end = min(start + limit, len(lines)) if limit is not None else len(lines)
            expected = "\n".join(lines[start:end]) if not invalid else None
            if not invalid and limit is not None and end < len(lines):
                expected += f"\n\n[{len(lines)-end} more lines in file. Use offset={end+1} to continue.]"
            result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=15)
            if invalid:
                if result.returncode != 2 or f"Offset {offset} is beyond end of file" not in result.stderr:
                    raise AssertionError(f"{name}, offset={offset}: expected upstream bounds error; got {result.returncode}, {result.stderr!r}")
            elif result.returncode != 0 or result.stdout != expected:
                raise AssertionError(f"{name}, offset={offset}, limit={limit}: expected={expected!r} got={result.stdout!r} exit={result.returncode} err={result.stderr!r}")
            reports.append({"fixture": name, "offset": offset, "limit": limit, "result": "PASS"})
    missing = subprocess.run([binary, "read-subset", str(Path(directory, "not-there.txt"))], capture_output=True, text=True, timeout=15)
    if missing.returncode != 2:
        raise AssertionError("missing file must return 2")
    reports.append({"fixture": "missing-file", "result": "PASS"})
out = Path(args.out)
out.parent.mkdir(parents=True, exist_ok=True)
summary = {
    "kind": "bounded_pi_read_text_subset_oracle_not_full_read_parity",
    "pinned_upstream": "8efd314fa3d3232ce197d8d7a6a5660530b9d83e",
    "passed": len(reports), "failed": 0, "cases": reports,
    "exclusions": ["images", "truncation", "path-resolution", "tool-envelope", "cancellation", "very-large-inputs"],
}
out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"passed": len(reports), "failed": 0}))
