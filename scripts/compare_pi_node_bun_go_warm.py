#!/usr/bin/env python3
"""Fair warmed Pi source Node/Bun vs pinned Go tool workloads.

Three persistent processes on one host. Byte-equivalent logical tool text is
required prior to any ranking. Measures single read/grep operations, NOT agent
token use, model latency, sessions or entire programming tasks.
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
p.add_argument("--pairs",type=int,default=90)
a=p.parse_args()
rng=random.Random(91827)
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    txt=root/"fixture.txt"
    txt.write_text("alpha\nTODO task\nbeta\nTODO second\nomega\n",encoding="utf-8")
    cases=[
      {"tool":"read","path":str(txt),"offset":1,"limit":2},
      {"tool":"read","path":str(txt),"offset":3,"limit":2},
      {"tool":"grep","path":str(txt),"pattern":"TODO"},
      {"tool":"grep","path":str(txt),"pattern":"ABSENT"},
    ]
    commands={
      "node":["node","scripts/adapters/pi_ts_warm.mjs",str(root)],
      "bun":["bun","scripts/adapters/pi_ts_warm.mjs",str(root)],
      "go":[str(Path(a.go_binary).resolve()),str(root)]
    }
    procs={}
    def call(name,request):
        t=time.perf_counter_ns()
        proc=procs[name]
        proc.stdin.write(json.dumps(request,ensure_ascii=False)+"\n")
        proc.stdin.flush()
        response=proc.stdout.readline()
        elapsed=(time.perf_counter_ns()-t)/1e6
        if not response:raise RuntimeError(f"{name} terminated without tool result (status {proc.poll()})")
        try:return json.loads(response),elapsed
        except json.JSONDecodeError as e:raise RuntimeError(f"Unparseable {name} response {response[:200]!r}") from e
    try:
        for name,cmd in commands.items():
            procs[name]=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,text=True,encoding="utf-8",bufsize=1)
        for request in cases:
            outputs={}
            for name in commands:
                outputs[name],_=call(name,request)
            assert len({json.dumps(x,sort_keys=True,ensure_ascii=False) for x in outputs.values()})==1,outputs
        # Warm real tools, avoid cold startup contaminating tool execution ranking.
        for _ in range(5):
            for req in cases:
                for name in commands:
                    output,_=call(name,req)
                    if output.get("error"):raise AssertionError((name,output))
        samples=[]
        for i in range(a.pairs):
            req=cases[i%len(cases)]
            order=list(commands);rng.shuffle(order)
            outputs={}
            timings={}
            for name in order:
                outputs[name],timings[name]=call(name,req)
            if len({json.dumps(x,sort_keys=True,ensure_ascii=False) for x in outputs.values()})!=1:
                raise AssertionError(f"Output mismatch on pair {i} {req}: {outputs}")
            samples.append({"case":i%len(cases),"tool":req["tool"],**{f"{k}_ms":v for k,v in timings.items()}})
        result={"kind":"three_way_pi_source_node_bun_vs_pinned_go_persistent_tool_performance",
            "pairs":a.pairs,"equal_output_trials":a.pairs,
            "go_source_revision":"53708dc48e03cdf59b7d7f63f059c65ad4bb45dc",
            "pinned_pi_source_revision":"8efd314fa3d3232ce197d8d7a6a5660530b9d83e",
            "overall_median_ms":{name:statistics.median(r[name+"_ms"] for r in samples) for name in commands},
            "per_tool_median_ms":{tool:{name:statistics.median(r[name+"_ms"] for r in samples if r["tool"]==tool)
              for name in commands} for tool in ("read","grep")},
            "runtime_versions":{"node":subprocess.check_output(["node","--version"],text=True).strip(),
              "bun":subprocess.check_output(["bun","--version"],text=True).strip(),
              "go":"pinned compiled binary"},
            "samples":samples,
            "scope":"Same source tool API for Node and Bun; original Go tool implementation. Not complete agent performance."}
        out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({k:v for k,v in result.items() if k!="samples"},indent=2))
    finally:
        for proc in procs.values():
            try:
                proc.stdin.close()
                proc.wait(timeout=5)
            except Exception:
                proc.kill();proc.wait(timeout=5)
