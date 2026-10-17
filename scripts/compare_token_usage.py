"""Offline compare paired token usage summaries; never invent savings from missing data."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

def compare(rows, baseline, candidate):
    by_task=defaultdict(dict)
    for r in rows:
        key=(r["run_id"],r["task_id"])
        if r["variant"] in by_task[key]:
            raise ValueError("duplicate run/task/variant")
        by_task[key][r["variant"]]=r
    results=[]
    for (run,task), variants in sorted(by_task.items()):
        if baseline not in variants or candidate not in variants:
            raise ValueError(f"unpaired run/task: {run}/{task}")
        a,b=variants[baseline],variants[candidate]
        for field in ("input_tokens","output_tokens","provider_reported_total_tokens"):
            if a.get(field) is None or b.get(field) is None:
                raise ValueError(f"missing {field} in {run}/{task}")
        if not a.get("usage_complete") or not b.get("usage_complete"):
            raise ValueError(f"incomplete usage in {run}/{task}")
        # Sum billed totals as reported; do not add reasoning again (subset of output).
        av,bv=a["provider_reported_total_tokens"],b["provider_reported_total_tokens"]
        if av<=0:
            raise ValueError("baseline total tokens must be positive")
        results.append({"run_id":run,"task_id":task,"baseline":baseline,"candidate":candidate,
                        "baseline_total_tokens":av,"candidate_total_tokens":bv,
                        "candidate_delta_pct":round(100*(bv-av)/av,3)})
    if not results:
        raise ValueError("no paired tasks")
    return results

def main():
    p=argparse.ArgumentParser()
    p.add_argument("summaries",type=Path)
    p.add_argument("--baseline",required=True)
    p.add_argument("--candidate",required=True)
    args=p.parse_args()
    rows=[json.loads(line) for line in args.summaries.read_text(encoding="utf-8").splitlines() if line.strip()]
    for item in compare(rows,args.baseline,args.candidate):
        print(json.dumps(item,sort_keys=True))

if __name__=="__main__":
    main()
