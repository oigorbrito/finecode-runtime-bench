"""Convert Pi v1.3.0 session JSONL assistant usage to benchmark events.

Offline parser: never emits prompts, message contents, paths, or credentials.
"""
import argparse
import json
from pathlib import Path

MAP = {"input_tokens":"input","output_tokens":"output","cache_read_tokens":"cacheRead","cache_write_tokens":"cacheWrite","reasoning_tokens":"reasoning","provider_reported_total_tokens":"totalTokens"}

def convert(lines, *, run_id, task_id, variant):
    index = 0
    for line in lines:
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry.get("type") != "message":
            continue
        message = entry.get("message") or {}
        if message.get("role") != "assistant":
            continue
        usage = message.get("usage")
        if not isinstance(usage, dict):
            raise ValueError("assistant message without usage; refusing incomplete accounting")
        event = {"run_id":run_id,"task_id":task_id,"variant":variant,"request_index":index,
                 "usage_source":"pi-session-assistant-message"}
        for target, source in MAP.items():
            event[target] = usage.get(source)
        yield event
        index += 1
    if index == 0:
        raise ValueError("no assistant messages found; refusing empty measurement")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("session",type=Path)
    p.add_argument("--run-id",required=True)
    p.add_argument("--task-id",required=True)
    p.add_argument("--variant",required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    events=list(convert(a.session.read_text(encoding="utf-8").splitlines(),run_id=a.run_id,task_id=a.task_id,variant=a.variant))
    a.out.write_text("".join(json.dumps(e,sort_keys=True)+"\n" for e in events),encoding="utf-8")

if __name__=="__main__":
    main()
