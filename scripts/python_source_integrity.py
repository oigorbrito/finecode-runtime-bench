"""Record source integrity without patching a third-party candidate."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--source", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
source = args.source.resolve()
harness = source / "packages/agent/src/pi_agent/harness"
init = harness / "__init__.py"
source_text = init.read_text(encoding="utf-8")
expected = "from .env.python import"
result = {
    "candidate": "pi_python",
    "check": "harness_env_import_resolves",
    "source_import_present": expected in source_text,
    "env_directory_exists": (harness / "env").is_dir(),
    "env_python_module_exists": (harness / "env/python.py").is_file(),
    "status": "missing_upstream_source_module" if expected in source_text and not (harness / "env/python.py").is_file() else "inspect",
    "note": "Evidence only; no third-party source files modified",
}
args.out.parent.mkdir(parents=True, exist_ok=True)
args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
