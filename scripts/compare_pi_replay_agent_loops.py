#!/usr/bin/env python3
"""Replay an identical deterministic provider script through three REAL agent loops.

Asserts identical final file, tool executions and turn count before ranking
runtime time. Timed region includes actual agent loop + four built-in tools.
This is not autonomous LLM reasoning or live token/cost comparison.
"""
import argparse,json,random,statistics,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument("--go-binary",required=True)
p.add_argument("--out",required=True)
p.add_argument("--rounds",type=int,default=20)
a=p.parse_args()
rng=random.Random(20261017)
with tempfile.TemporaryDirectory() as temp:
 root=Path(temp)
 commands={"node":["node","scripts/adapters/pi_ts_replay_agent.mjs"],
           "bun":["bun","scripts/adapters/pi_ts_replay_agent.mjs"],
           "go":[str(Path(a.go_binary).resolve())]}
 procs={}
 def call(name,filename):
  x=procs[name];x.stdin.write(json.dumps({"filename":filename})+"\n");x.stdin.flush()
  line=x.stdout.readline()
  if not line:raise RuntimeError(f"{name} exited without agent response: status={x.poll()}")
  return json.loads(line)
 try:
  for name,command in commands.items():
   location=root/name;location.mkdir()
   procs[name]=subprocess.Popen(command+[str(location)],stdin=subprocess.PIPE,
       stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding="utf-8",bufsize=1)
  trials=[]
  for idx in range(a.rounds+3):
   case=f"repair-{idx:04d}.py"
   order=list(commands);rng.shuffle(order)
   results={name:call(name,case) for name in order}
   for name,out in results.items():
    if out.get("error") or not out.get("ok") or not out.get("model_system_prompt_seen"):
     raise AssertionError(f"{name} real agent failed on round {idx}: {out}")
    if out.get("tool_results")!=4 or out.get("turns")!=5:
     raise AssertionError(f"{name}: unexpected agent execution transcript: {out}")
    if len(out.get("message_roles",[]))!=out.get("messages"):
     raise AssertionError(f"{name}: transcript length/roles mismatch {out}")
    if out.get("final_text")!="def calculate(n):\n    return n * 2\n":
     raise AssertionError(f"{name}: incorrect final code {out}")
    filename=root/name/case
    test=subprocess.run(["python3","-c",
      "import runpy,sys; f=runpy.run_path(sys.argv[1])['calculate']; assert all(f(n)==n*2 for n in [-13,-1,0,1,7,128])",
      str(filename)],capture_output=True,text=True,timeout=12)
    if test.returncode:raise AssertionError(f"{name}: correctness oracle FAILED {test.stderr}")
   baseline_contexts=results["node"]["model_contexts"]
   for candidate in ("bun","go"):
    contexts=results[candidate].get("model_contexts")
    if not contexts or len(contexts)!=5 or len(baseline_contexts)!=5:
     raise AssertionError(f"ELIMINATION_GATE missing model contexts round={idx} candidate={candidate}: {contexts}")
    for turn,(base,other) in enumerate(zip(baseline_contexts,contexts)):
     if base["roles"]!=other["roles"] or base["system_prompt"]!=other["system_prompt"] or base["user_prompt"]!=other["user_prompt"]:
      raise AssertionError(f"ELIMINATION_GATE model-facing context differs round={idx} turn={turn} candidate={candidate} node={base} candidate_context={other}")
   baseline_roles=results["node"]["message_roles"]
   for candidate in ("bun","go"):
    roles=results[candidate]["message_roles"]
    if roles!=baseline_roles:
     mismatch=next((i for i,(left,right) in enumerate(zip(baseline_roles,roles)) if left!=right),min(len(baseline_roles),len(roles)))
     if candidate=="go" and baseline_roles==["system",*roles] and results[candidate]["model_system_prompt_seen"]:
      continue  # Go stores system prompt separately; semantic model context must be tested independently.
     raise AssertionError(f"ELIMINATION_GATE unexplained transcript role divergence at round={idx} candidate={candidate} first_difference={mismatch} node_roles={baseline_roles} candidate_roles={roles}")
   if idx>=3:trials.append({"round":idx-3,
       **{name+"_agent_ms":results[name]["elapsed_ms"] for name in commands},
       **{name+"_messages":results[name]["messages"] for name in commands},
       **{name+"_events":results[name]["events"] for name in commands},
       **{name+"_roles":results[name]["message_roles"] for name in commands}})
  report={"kind":"actual_pinned_agent_loop_three_runtime_offline_model_replay",
    "rounds":a.rounds,"correct_candidate_task_runs":3*a.rounds,
    "same_four_tool_calls":True,"same_replayed_model_script":True,"shared_system_prompt_confirmed_at_model":True,
    "median_agent_loop_ms":{name:statistics.median(x[name+"_agent_ms"] for x in trials) for name in commands},
    "median_message_count":{name:statistics.median(x[name+"_messages"] for x in trials) for name in commands},
    "history_role_parity":"Go excludes the leading system role but passes the system prompt separately to model stream; remaining role sequence must match Pi",
    "scope":"Original Agent loops and builtin tools; deterministic replayed assistant tool calls; external Python correctness oracle; no real provider, model inference, tokens, cache, or diverse task quality",
    "trials":trials}
  out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
  out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
  print(json.dumps({k:v for k,v in report.items() if k!="trials"},indent=2))
 finally:
  for proc in procs.values():
   try:proc.stdin.close();proc.wait(timeout=6)
   except Exception:proc.kill();proc.wait(timeout=6)
