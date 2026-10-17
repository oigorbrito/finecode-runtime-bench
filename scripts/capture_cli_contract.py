"""Capture actual CLI help behavior before claiming cross-port equivalence."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

p = argparse.ArgumentParser()
p.add_argument("--out", required=True)
p.add_argument("--name", required=True)
p.add_argument("command", nargs=argparse.REMAINDER)
a = p.parse_args()
cmd = a.command[1:] if a.command[:1] == ["--"] else a.command
if not cmd:
    p.error("missing command")
r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=30, check=False)
text = r.stdout + r.stderr
result = {
    "name": a.name, "command": cmd, "exit_code": r.returncode,
    "stdout_bytes": len(r.stdout.encode()), "stderr_bytes": len(r.stderr.encode()),
    "combined_sha256": hashlib.sha256(text.encode()).hexdigest(),
    "lines": text.splitlines(), "scope": "CLI help output only; no agent parity claim",
}
out = Path(a.out)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in result.items() if k != "lines"}))
if r.returncode != 0:
    raise SystemExit(f"CLI {a.name} returned {r.returncode}; evidence saved")
