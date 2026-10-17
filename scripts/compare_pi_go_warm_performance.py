#!/usr/bin/env python3
"""Persistent Pi Node vs pinned Go: true warm tool workload, output-gated.

Same runner, deterministic inputs, alternating randomized order. The original
tools remain unchanged; adapters ONLY expose their exported tool APIs.
"""
import argparse
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import tempfile
import time

p=argparse.ArgumentParser()
p.add_argument("--go-binary",required=True)
p.add_argument("--out",required=True)
p.add_argument("--pairs",type=int,default=60)
a=p.parse_args()
rng=random.Random(20261017)
with tempfile.TemporaryDirectory() as temp:
 root=Path(temp)
 file=root/"sample.txt"
 file.write_text("alpha\nTODO first\nmiddle\nTODO last\n",encoding="utf-8")
 requests=[
  {"tool":"read","path":str(file),"offset":1,"limit":2},
  {"tool":"read","path":str(file),"offset":2,"limit":2},
  {"tool":"grep","path":str(file),"pattern":"TODO"},
  {"tool":"grep","path":str(file),"pattern":"ABSENT"},
 ]
 cmds={
  "pi_node":["node","scripts/adapters/pi_ts_warm.mjs",str(root)],
  "pi_go":[str(Path(a.go_binary).resolve()),str(root)]
 }
 ps={}
 def call(name,req):
  start=time.perf_counter_ns()
  ps[name].stdin.write(json.dumps(req,ensure_ascii=False)+"\n")
  ps[name].stdin.flush()
  line=ps[name].stdout.readline()
  wall=(time.perf_counter_ns()-start)/1e6
  if not line:raise RuntimeError(f"{name} exited before reply: {ps[name].poll()}")
  return json.loads(line),wall
 try:
  for name,cmd in cmds.items():
   ps[name]=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,text=True,encoding="utf-8",bufsize=1,cwd=os.getcwd())
  # Warm each real tool in both runtimes before measurement.
  for _ in range(3):
   for req in requests:
    for name in cmds:
     resp,_=call(name,req)
     if "error" in resp:raise AssertionError(f"{name} warmup tool failed: {resp}")
  rows=[]
  for i in range(a.pairs):
   req=requests[i%len(requests)]
   order=list(cmds);rng.shuffle(order)
   pair={}
   for name in order:pair[name]=call(name,req)
   pi,go=pair["pi_node"][0],pair["pi_go"][0]
   if pi!=go:
    raise AssertionError(f"WARM PI VS GO TOOL MISMATCH pair {i}: input={req!r}, Pi={pi!r}, Go={go!r}")
   rows.append({"tool":req["tool"],"case":i%len(requests),
     "node_wall_ms":pair["pi_node"][1],"go_wall_ms":pair["pi_go"][1]})
  node_wall=statistics.median(r["node_wall_ms"] for r in rows)
  go_wall=statistics.median(r["go_wall_ms"] for r in rows)
  report={"kind":"pinned_pi_ts_vs_pi_go_persistent_warm_tools","pinned_pi_go":"53708dc48e03cdf59b7d7f63f059c65ad4bb45dc",
    "pairs":a.pairs,"seed":20261017,"identical_responses":a.pairs,
    "node_median_wall_ms":node_wall,"go_median_wall_ms":go_wall,
    "go_over_node_wall_ratio":go_wall/node_wall,
    "by_tool":{tool:{
      "node_median_ms":statistics.median(r["node_wall_ms"] for r in rows if r["tool"]==tool),
      "go_median_ms":statistics.median(r["go_wall_ms"] for r in rows if r["tool"]==tool)}
      for tool in ("read","grep")},
    "samples":rows,
    "scope":"Persistent Node Pi vs persistent Go Pi, real exported read/grep, same runner. No model, agent loop or token usage."}
  out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
  out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
  print(json.dumps({k:v for k,v in report.items() if k!="samples"},indent=2))
 finally:
  for proc in ps.values():
   try:
    proc.stdin.close()
    proc.wait(timeout=10)
   except Exception:
    proc.kill();proc.wait(timeout=10)
