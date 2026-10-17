#!/usr/bin/env python3
"""Paired cold tool invocation: actual pinned Pi Node vs Native AOT C#.

Strict scope: process startup + one bounded tool invocation; NOT warmed agent
throughput, overall token usage, full feature parity, or agent correctness.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys
import tempfile
import time

p=argparse.ArgumentParser()
p.add_argument("--binary",required=True)
p.add_argument("--out",required=True)
p.add_argument("--pairs",type=int,default=30)
args=p.parse_args()
if args.pairs<10: p.error("require >=10 paired repetitions")
try:
    import psutil
except ImportError:
    raise SystemExit("Install psutil before benchmarking; no silent RSS omission")
node="node"
csharp=str(Path(args.binary).resolve())
runner=str(Path("scripts/pi_cold_tool.mjs").resolve())
rng=random.Random(20261017)
def invoke(cmd):
    start=time.perf_counter_ns()
    ps=psutil.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    max_rss=0
    try:
        while ps.poll() is None:
            try: max_rss=max(max_rss,ps.memory_info().rss)
            except (psutil.NoSuchProcess,psutil.AccessDenied): break
            time.sleep(.001)
        stdout,stderr=ps.communicate(timeout=10)
        max_rss=max(max_rss,getattr(ps.memory_info(),"rss",0)) if ps.is_running() else max_rss
    except Exception:
        ps.kill();ps.communicate()
        raise
    wall=(time.perf_counter_ns()-start)/1e6
    if ps.returncode!=0: raise RuntimeError(f"{cmd[0]} exit {ps.returncode}: {stderr[:1000]!r}")
    return {"wall_ms":wall,"sampled_parent_peak_rss_mib":max_rss/1048576,"sha256":hashlib.sha256(stdout).hexdigest(),"stdout":stdout}

with tempfile.TemporaryDirectory() as temp:
    root=Path(temp)
    read=root/"read.txt";read.write_text("alpha\nbeta\ngamma\n",encoding="utf-8")
    grep=root/"grep.txt";grep.write_text("alpha\nTODO first\nmiddle\nTODO last\n",encoding="utf-8")
    find=root/"find";find.mkdir();(find/"one.xyz").write_text("x",encoding="utf-8")
    # Find uses shared fd; binary availability is resolved independently by Pi.
    # C# delegated fd resolution is not part of this cold invocation test.
    tasks={
      "read":{"pi":[node,runner,"read",str(root),str(read),"1","2"],
              "aot":[csharp,"read-subset",str(read),"1","2"]},
      "grep":{"pi":[node,runner,"grep",str(root),str(grep),"TODO"],
              "aot":[csharp,"grep-subset",str(grep),"TODO","literal"]},
    }
    report={"kind":"cold_single_tool_process_comparison_not_agent_benchmark",
            "pairs":args.pairs,"random_seed":20261017,
            "target_os":os.name,"tasks":{},
            "limitations":["Node starts a fresh process and imports genuine Pi per sample",
                           "C# starts a fresh Native AOT binary per sample",
                           "not equivalent to Pi's persistent warmed agent",
                           "RSS sampled every ~1ms for parent only; sampling may miss peaks",
                           "no providers, model tokens, agent loop, or quality metric"]}
    for name, commands in tasks.items():
        results={"pi":[],"aot":[]}
        for _ in range(args.pairs):
            order=["pi","aot"];rng.shuffle(order)
            pair={}
            for key in order: pair[key]=invoke(commands[key])
            if pair["pi"]["stdout"]!=pair["aot"]["stdout"]:
                raise AssertionError(f"{name}: outputs differ, refusing performance ranking")
            for key in order:
                result=pair[key]
                results[key].append({k:v for k,v in result.items() if k!="stdout"})
        a=statistics.median(x["wall_ms"] for x in results["aot"])
        b=statistics.median(x["wall_ms"] for x in results["pi"])
        report["tasks"][name]={
          "pi_median_wall_ms":b,"aot_median_wall_ms":a,
          "aot_over_pi_median_wall_ratio":a/b,
          "pi_median_sampled_parent_rss_mib":statistics.median(x["sampled_parent_peak_rss_mib"] for x in results["pi"]),
          "aot_median_sampled_parent_rss_mib":statistics.median(x["sampled_parent_peak_rss_mib"] for x in results["aot"]),
          "output_equal_all_pairs":True,
          "raw_pairs":results}
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:{x:y for x,y in v.items() if x!="raw_pairs"} for k,v in report["tasks"].items()},indent=2))
