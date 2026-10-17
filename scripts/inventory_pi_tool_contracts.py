#!/usr/bin/env python3
"""Fail-closed inventory of pinned Pi tool contract shape. NOT a parity test."""
import argparse
import json
import re
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--root", default="vendor/pi_ts")
p.add_argument("--out", default="results/pi-tools-contract-inventory.json")
args = p.parse_args()
root = Path(args.root)
names = ("read", "grep", "find")
required = {
 "read": {"path": "Path to the file to read", "offset": "Line number to start", "limit": "Maximum number of lines"},
 "grep": {"pattern": "Search pattern", "path": "Directory or file to search", "glob": "Filter files by glob", "ignoreCase": "Case-insensitive", "literal": "Treat pattern as literal", "context": "Number of lines to show", "limit": "Maximum number of matches"},
 "find": {"pattern": "Glob pattern to match files", "path": "Directory to search in", "limit": "Maximum number of results"}
}
report = {"kind": "pinned_upstream_static_tool_contract_inventory_not_execution_parity", "tools": {}}
for name in names:
    path = root / "packages" / "coding-agent" / "src" / "core" / "tools" / (name + ".ts")
    source = path.read_text(encoding="utf-8")
    schema = re.search(r"const " + name + r"Schema = Type\.Object\(\{(.*?)\n\}\);", source, re.S)
    if not schema:
        raise SystemExit(f"FAIL schema not found: {path}")
    parameters = {}
    for key, phrase in required[name].items():
        match = re.search(r"\b" + re.escape(key) + r":\s*(?:Type\.Optional\(\s*)?Type\.(?:String|Boolean|Number)\(", schema.group(1))
        if not match or phrase not in schema.group(1):
            raise SystemExit(f"FAIL pinned parameter {name}.{key} changed or missing")
        parameters[key] = {"declared": True, "optional": bool(re.search(r"\b" + re.escape(key) + r":\s*Type\.Optional", schema.group(1)))}
    report["tools"][name] = {"parameters": parameters, "source": str(path).replace("\\", "/")}
out = Path(args.out)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"result": "PASS", "tools": list(report["tools"]), "parameter_count": sum(len(x["parameters"]) for x in report["tools"].values())}))
