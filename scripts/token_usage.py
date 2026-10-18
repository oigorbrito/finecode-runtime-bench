"""Aggregate provider-reported usage; unknown values remain null."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

FIELDS = ("input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens", "reasoning_tokens", "provider_reported_total_tokens")

def aggregate(rows):
    groups = defaultdict(list)
    for row in rows:
        for key in ("run_id", "task_id", "variant", "request_index"):
            if key not in row:
                raise ValueError(f"missing required field: {key}")
        for key in FIELDS:
            value = row.get(key)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"{key} must be a nonnegative integer or null")
        groups[(row["run_id"], row["task_id"], row["variant"])].append(row)
    results = []
    for (run_id, task_id, variant), events in sorted(groups.items()):
        indices = [e["request_index"] for e in events]
        if len(indices) != len(set(indices)):
            raise ValueError(f"duplicate request_index for {run_id}/{task_id}/{variant}")
        record = dict(run_id=run_id, task_id=task_id, variant=variant, requests=len(events))
        for field in FIELDS:
            values = [e.get(field) for e in events]
            record[field] = sum(values) if all(v is not None for v in values) else None
        record["usage_complete"] = all(e.get("input_tokens") is not None and e.get("output_tokens") is not None for e in events)
        results.append(record)
    return results

def read_jsonl(path):
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"bad JSON at line {n}") from exc

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("events", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    data = "\n".join(json.dumps(row, sort_keys=True) for row in aggregate(read_jsonl(args.events))) + "\n"
    if args.out:
        args.out.write_text(data, encoding="utf-8")
    else:
        print(data, end="")

if __name__ == "__main__":
    main()
