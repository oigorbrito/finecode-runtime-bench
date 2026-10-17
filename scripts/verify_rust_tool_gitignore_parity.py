#!/usr/bin/env python3
"""Executable elimination check for pinned Rust tool compatibility with Pi."""
import json
import subprocess
import tempfile
from pathlib import Path
import argparse
a=argparse.ArgumentParser()
a.add_argument("--rust-binary",required=True)
a.add_argument("--out",required=True)
args=a.parse_args()
binary=str(Path(args.rust_binary).resolve())
runner=str(Path("scripts/pi_cold_tool.mjs").resolve())
def execute(cmd):
 r=subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8",timeout=30)
 if r.returncode:raise RuntimeError(f"exit {r.returncode}: {r.stderr}")
 return r.stdout
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp)
 subprocess.run(["git","init","--quiet",tmp],check=True,timeout=20)
 (root/".gitignore").write_text("*.txt\n",encoding="utf-8")
 (root/"ignored.txt").write_text("NEEDLE\n",encoding="utf-8")
 results=[]
 for tool,pattern in (("find","*.txt"),("grep","NEEDLE")):
  pi=execute(["node",runner,tool,tmp,tmp,pattern])
  rust=execute([binary,tmp,tool,pattern])
  diverged=pi!=rust
  expected=("ignored.txt" in rust and "ignored.txt" not in pi)
  results.append({"tool":tool,"pi_output":pi,"rust_output":rust,
     "diverged":diverged,"expected_missing_gitignore":expected})
 # Fail closed if discrepancy cannot be reproduced. This run does not
 # establish superiority of either language, only current source parity gap.
 assert all(x["diverged"] and x["expected_missing_gitignore"] for x in results),results
 report={"kind":"pinned_rust_port_actual_pi_tool_gitignore_differential",
   "rust_pin":"b6b8e8311a4d6fd5dd1dc9e436e96f5d4cd22a52",
   "outcome":"ELIMINATED_PINNED_REVISION_FOR_STRICT_TOOL_PARITY",
   "results":results,
   "scope":"Requires .gitignore-aware grep/find to reenter Pi full-parity contest; not Rust language elimination"}
 out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(report,indent=2))
