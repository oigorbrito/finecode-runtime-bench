"""Clone exact upstream commit; never modify FineCode."""
import json
import subprocess
import sys
from pathlib import Path

name = sys.argv[1]
source = json.loads(Path("sources.json").read_text())[name]
dest = Path("vendor") / name
subprocess.run(["git", "clone", "--no-checkout", source["url"], str(dest)], check=True)
subprocess.run(["git", "-C", str(dest), "checkout", "--detach", source["sha"]], check=True)
actual = subprocess.check_output(["git", "-C", str(dest), "rev-parse", "HEAD"], text=True).strip()
assert actual == source["sha"], (actual, source["sha"])
print(f"PINNED {name} {actual}")
