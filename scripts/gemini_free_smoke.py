"""One-request Gemini free-tier connectivity and provider-reported token usage smoke."""
import json
import os
import sys
import urllib.error
import urllib.request

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
URL = "https://generativelanguage.googleapis.com/v1beta/models/" + MODEL + ":generateContent"

def main():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("FAIL: GEMINI_API_KEY missing")
        return 1
    # Verify which generateContent models this key can actually access.\n    list_req = urllib.request.Request(\n        "https://generativelanguage.googleapis.com/v1beta/models?pageSize=100",\n        headers={"x-goog-api-key": key},\n    )\n    try:\n        with urllib.request.urlopen(list_req, timeout=30) as response:\n            catalog = json.load(response)\n    except urllib.error.HTTPError as exc:\n        print("FAIL: Gemini models listing HTTP status", exc.code)\n        return 1\n    except Exception as exc:\n        print("FAIL: Gemini models listing transport error:", type(exc).__name__)\n        return 1\n    supported = [item.get("name", "").removeprefix("models/")\n                 for item in catalog.get("models", [])\n                 if "generateContent" in item.get("supportedGenerationMethods", [])]\n    if MODEL not in supported:\n        print("FAIL: requested Gemini model not available for this key:", MODEL)\n        print("Available generateContent models:", ", ".join(supported[:30]))\n        return 1\n    payload = {
        "contents": [{"role": "user", "parts": [{"text": "Reply with exactly OK."}]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 64,
                             "thinkingConfig": {"thinkingBudget": 0}},
    }
    request = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        # Never log error body, headers, key, or model output.
        print("FAIL: Gemini HTTP status", exc.code)
        return 1
    except Exception as exc:
        print("FAIL: Gemini transport error:", type(exc).__name__)
        return 1
    usage = data.get("usageMetadata") or {}
    fields = ("promptTokenCount", "candidatesTokenCount", "totalTokenCount")
    values = [usage.get(field) for field in fields]
    if not all(type(value) is int and value >= 0 for value in values):
        print("FAIL: Gemini did not return complete numeric usage")
        return 1
    if not data.get("candidates"):
        print("FAIL: Gemini returned no candidates")
        return 1
    record = {
        "provider": "gemini", "model": MODEL, "variant": "connectivity-smoke",
        "run_id": "gemini-free-smoke", "task_id": "connectivity", "request_index": 0,
        "input_tokens": values[0], "output_tokens": values[1],
        "provider_reported_total_tokens": values[2],
        "reasoning_tokens": usage.get("thoughtsTokenCount"),
        "cache_read_tokens": usage.get("cachedContentTokenCount"),
        "cache_write_tokens": None,
    }
    with open("gemini-usage-events.jsonl", "w", encoding="utf-8") as output:
        output.write(json.dumps(record) + "\n")
    print("PASS: Gemini request and provider-reported token usage captured")
    return 0

if __name__ == "__main__":
    sys.exit(main())
