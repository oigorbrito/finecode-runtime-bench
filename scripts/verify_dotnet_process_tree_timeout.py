#!/usr/bin/env python3
"""Exercise the *same* process-tree timeout helper used by the delegated fd adapter.

This is a deterministic timeout/kill safety gate, not a claim of isolated
execution, memory quota enforcement or full Pi cancellation parity.
"""
import argparse
import json
import subprocess
import tempfile
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--binary", required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args()
binary = str(Path(args.binary).resolve())
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    start = time.monotonic()
    result = subprocess.run(
        [binary, "process-tree-probe", str(root), "1500"],
        capture_output=True, timeout=12, check=False
    )
    elapsed = time.monotonic() - start
    assert result.returncode == 124, (result.returncode, result.stderr)
    assert result.stdout.decode("utf-8") == "PROCESS_TREE_TIMEOUT", result.stdout
    started = {
        "parent": (root / "parent-started.txt").is_file(),
        "grandchild": (root / "grandchild-started.txt").is_file()
    }
    assert all(started.values()), f"fixture did not start both processes: {started}"
    # Both processes would emit sentinel after 3.5s if kill-tree failed.
    # Wait beyond this duration after observing the wrapper's timeout return.
    time.sleep(4.0)
    unexpected = [
        marker for marker in ("parent-survived.txt", "grandchild-survived.txt")
        if (root / marker).exists()
    ]
    assert not unexpected, f"orphan survived process tree termination: {unexpected}"
    evidence = {
        "kind": "bounded_child_real_timeout_and_process_tree_kill",
        "passed": True,
        "deadline_ms": 1500,
        "wrapper_elapsed_seconds": round(elapsed, 4),
        "actual_exit_code": result.returncode,
        "parent_started": started["parent"],
        "grandchild_started": started["grandchild"],
        "survival_sentinels": unexpected,
        "safety_scope": "Child process timeout and descendants killed; not OS sandbox or memory limit"
    }
out = Path(args.out)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
print(json.dumps(evidence, indent=2))
