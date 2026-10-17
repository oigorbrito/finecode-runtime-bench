import argparse
import json
import os
import platform
from pathlib import Path
import resource
import statistics
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument("--name", required=True)
p.add_argument("--out", required=True)
p.add_argument("--runs", type=int, default=11)
p.add_argument("cmd", nargs=argparse.REMAINDER)
a = p.parse_args()
cmd = a.cmd[1:] if a.cmd[:1] == ["--"] else a.cmd
if platform.system() != "Linux" or not cmd:
    p.error("Linux and a command are required")

def sample():
    start = time.perf_counter_ns()
    with subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) as proc:
        _, status, usage = os.wait4(proc.pid, 0)
        proc.returncode = os.waitstatus_to_exitcode(status)
        if proc.returncode:
            raise subprocess.CalledProcessError(proc.returncode, cmd)
    return {
        "wall_ms": (time.perf_counter_ns() - start) / 1e6,
        "cpu_ms": (usage.ru_utime + usage.ru_stime) * 1000,
        "rss_kib": usage.ru_maxrss,
    }

for _ in range(3):
    sample()
samples = [sample() for _ in range(a.runs)]
result = {
    "name": a.name, "arch": platform.machine(),
    "scope": "single CLI process invocation",
    "command": cmd, "runs": len(samples),
    "median": {k: statistics.median(s[k] for s in samples) for k in samples[0]},
    "samples": samples,
}
Path(a.out).parent.mkdir(parents=True, exist_ok=True)
Path(a.out).write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"name": a.name, "median": result["median"]}))
