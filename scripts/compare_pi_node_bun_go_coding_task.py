#!/usr/bin/env python3
"""Deterministic edit-and-test workload using real pinned Pi/Go coding tools.

Each candidate executes write -> edit -> read -> grep on its own isolated
fixture. Final Python assertions must pass; final bytes and read/grep output
must match. No LLM, token quality or API calls; do not infer agent superiority.
"""
import argparse
import json
import random
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument("--go-binary",required=True)
p.add_argument("--out",required=True)
p.add_argument("--rounds",type=int,default=24)
a=p.parse_args()
rng=random.Random(10217)
commands={
 "node":["node","scripts/adapters/pi_ts_warm.mjs"],
 "bun":["bun","scripts/adapters/pi_ts_warm.mjs"],
 "go":[str(Path(a.go_binary).resolve())]
}
initial="def calculate(n):\n    return n + 1\n"
expected="def calculate(n):\n    return n * 2\n"
edits=[{"oldText":"return n + 1","newText":"return n * 2"}]
with tempfile.TemporaryDirectory() as temp:
 root=Path(temp)
 processes={}
 for name in commands:
  folder=root/name;folder.mkdir()
  processes[name]=subprocess.Popen(commands[name]+[str(folder)],
   stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
   text=True,encoding="utf-8",bufsize=1)
 def invoke(name,req):
  proc=processes[name]
  proc.stdin.write(json.dumps(req)+"\n");proc.stdin.flush()
  response=proc.stdout.readline()
  if not response:raise RuntimeError(f"{name} process exited without response {proc.poll()}")
  result=json.loads(response)
  if result.get("error"):raise RuntimeError(f"{name} tool error: {result['error']}")
  return result
 samples=[]
 try:
  # Warm process startup without file mutation.
  for name in commands:
   warm=root/name/"warm.txt"
   warm.write_text("READY\n",encoding="utf-8")
   for _ in range(5):assert invoke(name,{"tool":"read","path":str(warm),"offset":1,"limit":1}).get("text","").startswith("READY")
  for i in range(a.rounds):
   order=list(commands);rng.shuffle(order)
   outcomes={}
   for name in order:
    file=root/name/f"task-{i:03d}.py"
    t=time.perf_counter_ns()
    invoke(name,{"tool":"write","path":str(file),"content":initial})
    invoke(name,{"tool":"edit","path":str(file),"edits":edits})
    read=invoke(name,{"tool":"read","path":str(file),"offset":1,"limit":2}).get("text")
    grep=invoke(name,{"tool":"grep","path":str(file),"pattern":"return n * 2"}).get("text")
    operations_ms=(time.perf_counter_ns()-t)/1e6
    actual=file.read_text(encoding="utf-8")
    assert actual==expected,(name,actual)
    assert read is not None and "return n * 2" in read,(name,read)
    assert grep is not None and "return n * 2" in grep,(name,grep)
    # Run real interpreter assertions against each candidate's edited file.
    oracle=subprocess.run(["python3","-c",
      "import runpy,sys; f=runpy.run_path(sys.argv[1])['calculate']; assert all(f(n)==2*n for n in (-13,-1,0,1,7,128))",
      str(file)],capture_output=True,text=True,timeout=10)
    assert oracle.returncode==0,(name,oracle.stderr)
    outcomes[name]={"text":actual,"read":read,"grep":grep,"operations_ms":operations_ms}
   # File basenames are the same across runtimes, so grep content must match.
   assert len({json.dumps({k:v for k,v in o.items() if k!="operations_ms"},sort_keys=True)
     for o in outcomes.values()})==1,(i,outcomes)
   samples.append({"round":i,**{name+"_operations_ms":outcomes[name]["operations_ms"] for name in commands}})
  result={"kind":"pinned_pi_node_bun_go_real_coding_tool_write_edit_read_grep_with_python_oracle",
    "rounds":a.rounds,"correct_tasks_per_candidate":a.rounds,"identical_final_files_and_read_grep":True,
    "median_tool_chain_ms":{name:statistics.median(x[name+"_operations_ms"] for x in samples) for name in commands},
    "scope":"Four genuine tool calls and Python correctness oracle per task, separately isolated files. Tool-chain timer excludes Python interpreter oracle. NOT autonomous AI agent, tokens or provider.",
    "samples":samples}
  out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
  out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
  print(json.dumps({k:v for k,v in result.items() if k!="samples"},indent=2))
 finally:
  for proc in processes.values():
   try:proc.stdin.close();proc.wait(timeout=6)
   except Exception:proc.kill();proc.wait(timeout=6)
