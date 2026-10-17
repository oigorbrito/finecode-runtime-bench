"""Compare observable CLI help contracts without assuming full feature parity."""
import argparse
import json
from pathlib import Path
import re

p = argparse.ArgumentParser()
p.add_argument("--inputs", nargs="+", required=True)
p.add_argument("--out", required=True)
a = p.parse_args()
files = [json.loads(Path(path).read_text(encoding="utf-8")) for path in a.inputs]
def flags(lines):
    return sorted(set(re.findall(r"(?<![\\w-])--[a-z][a-z0-9-]*", "\\n".join(lines), flags=re.I)))
records = {f["name"]: {"exit_code": f["exit_code"], "sha256": f["combined_sha256"], "flags": flags(f["lines"]), "line_count": len(f["lines"])} for f in files}
names = list(records)
pairs = {}
for i, left in enumerate(names):
    for right in names[i+1:]:
        a_set, b_set = set(records[left]["flags"]), set(records[right]["flags"])
        pairs[f"{left}__{right}"] = {
            "common_flags": sorted(a_set & b_set),
            "only_left_flags": sorted(a_set - b_set),
            "only_right_flags": sorted(b_set - a_set),
            "identical_output_hash": records[left]["sha256"] == records[right]["sha256"],
        }
data = {
    "scope": "observable --help flags only, not proof of functional equivalence",
    "records": records, "pairs": pairs,
    "all_exit_zero": all(x["exit_code"] == 0 for x in records.values()),
}
out = Path(a.out)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: {"common": len(val["common_flags"]), "left_only": len(val["only_left_flags"]), "right_only": len(val["only_right_flags"])} for key, val in pairs.items()}))
if not data["all_exit_zero"]:
    raise SystemExit("one or more CLI help commands failed")
