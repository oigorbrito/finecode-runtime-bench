#!/usr/bin/env python3
"""Measure a single-purpose Native AOT process probe, not a coding-agent runtime."""
import argparse
import json
import os
import resource
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--binary", required=True)
p.add_argument("--out", required=True)
p.add_argument("--iterations", type=int, default=25)
args = p.parse_args()
binary = str(Path(args.binary).resolve())
if args.iterations < 3:
    p.error("iterations must be >= 3")
wall_ms, cpu_ms, rss_kib = [], [], []
for _ in range(args.iterations):
    with tempfile.TemporaryDirectory() as directory:
        metrics = os.path.join(directory, "resource.txt")
        cpu_before = resource.getrusage(resource.RUSAGE_CHILDREN)
        started = time.perf_counter_ns()
        completed = subprocess.run(
            ["/usr/bin/time", "-f", "%U %S %M", "-o", metrics,
             binary, "--help"], capture_output=True, text=True, timeout=15, check=True)
        elapsed = (time.perf_counter_ns() - started) / 1_000_000
        cpu_after = resource.getrusage(resource.RUSAGE_CHILDREN)
        if "finecode-dotnet-aot-probe" not in completed.stdout:
            raise RuntimeError("unexpected process output")
        user, system, peak = Path(metrics).read_text().strip().split()
        wall_ms.append(elapsed)
        cpu_ms.append(((cpu_after.ru_utime - cpu_before.ru_utime) + (cpu_after.ru_stime - cpu_before.ru_stime)) * 1000)
        rss_kib.append(int(peak))
result = {
    "kind": "process_probe_only_not_agent_parity",
    "language": "C#", "publish": "Native AOT",
    "os": "linux", "arch": "x64", "command": "--help",
    "iterations": args.iterations,
    "wall_ms_median": statistics.median(wall_ms),
    "cpu_ms_median": statistics.median(cpu_ms),
    "cpu_measurement": "resource.getrusage(RUSAGE_CHILDREN) microsecond-resolution deltas",
    "peak_rss_mib_median": statistics.median(rss_kib) / 1024,
    "binary_bytes": os.stat(binary).st_size,
    "warning": "No Pi CLI contract, tools, providers, sessions, skills, or agent-loop parity."
}
destination = Path(args.out)
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
