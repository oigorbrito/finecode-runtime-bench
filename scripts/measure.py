"""Measure repeated startup for an existing CLI; never invoke an LLM provider."""
import argparse
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument("--name", required=True)
p.add_argument("--out", required=True)
p.add_argument("--warmup", type=int, default=3)
p.add_argument("--runs", type=int, default=11)
p.add_argument("cmd", nargs=argparse.REMAINDER)
a = p.parse_args()
cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
if not cmd:
    p.error("command required after --")
for _ in range(a.warmup):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, timeout=30)
values = []
for _ in range(a.runs):
    start = time.perf_counter_ns()
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, timeout=30)
    values.append((time.perf_counter_ns() - start) / 1e6)
result = {"name":a.name,"metric":"cli_version_wall_ms","warmup":a.warmup,"runs":a.runs,
          "median_ms":statistics.median(values),"samples_ms":values,
          "arch":platform.machine(),"os":platform.platform(),"command":cmd,
          "github_runner":os.getenv("RUNNER_NAME", "local")}
Path(a.out).parent.mkdir(parents=True, exist_ok=True)
Path(a.out).write_text(json.dumps(result, indent=2)+"\n")
print(json.dumps({k:result[k] for k in ("name","median_ms","runs","arch")}))
