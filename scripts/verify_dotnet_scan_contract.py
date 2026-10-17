#!/usr/bin/env python3
"""Independent Python oracle for a bounded C# read-only file-scan contract.

These tests establish scan-file correctness only, NOT Pi agent parity.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

parser = argparse.ArgumentParser()
parser.add_argument("--binary", required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args()
binary = str(Path(args.binary).resolve())
cases = [
    ("empty", "", "TODO"),
    ("single", "TODO", "TODO"),
    ("lines", "alpha\nTODO beta\nTODO\n", "TODO"),
    ("unicode", "olá 🧪\nTODO\n", "🧪"),
    ("overlap", "aaaaa", "aa"),
    ("large", ("TODO work\nno match\n" * 12000), "TODO"),
]
results = []
with tempfile.TemporaryDirectory() as directory:
    for name, contents, literal in cases:
        data = contents.encode("utf-8")
        sample = Path(directory, name + ".txt")
        sample.write_bytes(data)
        expected = {
            "schema": "finecode-process-probe-scan-v1",
            "bytes": len(data),
            "lines": 0 if not contents else len(contents.splitlines()),
            "matches": contents.count(literal),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        started = time.perf_counter_ns()
        run = subprocess.run([binary, "scan-file", str(sample), literal],
                             capture_output=True, text=True, timeout=20)
        wall_ms = (time.perf_counter_ns() - started) / 1e6
        if run.returncode != 0 or run.stderr:
            raise RuntimeError(f"{name}: exit={run.returncode}, stderr={run.stderr!r}")
        actual = json.loads(run.stdout)
        if actual != expected:
            raise AssertionError(f"{name}: expected={expected!r}, actual={actual!r}")
        results.append({"name": name, "result": "PASS", "input_bytes": len(data),
                        "wall_ms": wall_ms})
    invalid = [
        [binary, "scan-file", str(Path(directory, "missing.txt")), "TODO"],
        [binary, "scan-file", str(Path(directory, "single.txt")), ""],
        [binary, "not-a-command"],
    ]
    for command in invalid:
        result = subprocess.run(command, capture_output=True, text=True, timeout=20)
        if result.returncode != 2:
            raise AssertionError(f"Invalid invocation returned {result.returncode}: {command}")
    results.append({"name": "invalid-args-and-missing-file", "result": "PASS", "cases": 3})
summary = {
    "kind": "bounded_read_only_file_scan_not_pi_agent",
    "platform": os.name,
    "passed": len(results),
    "failed": 0,
    "cases": results,
    "warning": "Independent Python oracle for basic file scan; not agent, tool, session or provider parity."
}
destination = Path(args.out)
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=2))
