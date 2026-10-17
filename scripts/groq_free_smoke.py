"""One-request Groq Free connectivity and provider-reported token usage smoke.
Never print the key, prompt, response content or response headers.
"""
import json
import os
import sys
import urllib.error
import urllib.request

def main():
    key=os.environ.get("GROQ_API_KEY")
    if not key:
        print("SKIP: GROQ_API_KEY is not available in runner secrets")
        return 0
    model="openai/gpt-oss-20b"
    payload=json.dumps({"model":model,"messages":[{"role":"user","content":"Reply with exactly OK."}],"max_completion_tokens":24,"temperature":0}).encode()
    req=urllib.request.Request("https://api.groq.com/openai/v1/chat/completions",data=payload,headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=30) as resp:
            data=json.load(resp)
    except urllib.error.HTTPError as e:
        # Error bodies and headers may include sensitive provider details.
        print("FAIL: Groq HTTP status",e.code)
        return 1
    except Exception as e:
        print("FAIL: Groq request transport error:",type(e).__name__)
        return 1
    usage=data.get("usage") or {}
    inp,out,total=(usage.get("prompt_tokens"),usage.get("completion_tokens"),usage.get("total_tokens"))
    if not all(isinstance(x,int) and not isinstance(x,bool) and x>=0 for x in (inp,out,total)):
        print("FAIL: provider did not return complete numeric usage")
        return 1
    if not data.get("choices"):
        print("FAIL: provider returned no choices")
        return 1
    result={"provider":"groq","model":model,"variant":"connectivity-smoke","run_id":"groq-free-smoke","task_id":"connectivity",
            "request_index":0,"input_tokens":inp,"output_tokens":out,"provider_reported_total_tokens":total,
            "cache_read_tokens":None,"cache_write_tokens":None,"reasoning_tokens":None}
    with open("groq-usage-events.jsonl","w",encoding="utf-8") as f:
        f.write(json.dumps(result)+"\n")
    print("PASS: Groq request and numeric usage verified; response and credentials omitted")
    return 0

if __name__=="__main__":
    sys.exit(main())
