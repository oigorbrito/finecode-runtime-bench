#!/usr/bin/env python3
"""Docker sandbox gate for Native AOT; does not claim full hostile-code isolation."""
import argparse
import json
import subprocess
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument("--image",required=True)
p.add_argument("--out",required=True)
a=p.parse_args()
flags=["--network","none","--read-only","--pids-limit","32",
       "--memory","128m","--memory-swap","128m","--cpus","1.0",
       "--cap-drop","ALL","--security-opt","no-new-privileges",
       "--tmpfs","/tmp:rw,nosuid,nodev,noexec,size=8m",
       "--user","65534:65534"]
def docker(*argv, timeout=60):
    return subprocess.run(["docker",*argv],text=True,capture_output=True,timeout=timeout)
created=docker("create",*flags,a.image,"sandbox-probe")
assert created.returncode==0,created.stderr
cid=created.stdout.strip()
try:
    inspected=docker("inspect",cid)
    assert inspected.returncode==0,inspected.stderr
    data=json.loads(inspected.stdout)[0]
    host=data["HostConfig"]
    config=data["Config"]
    checks={
      "network_none":host["NetworkMode"]=="none",
      "read_only_root":host["ReadonlyRootfs"] is True,
      "process_limit_32":host["PidsLimit"]==32,
      "memory_limit_128m":host["Memory"]==134217728,
      "swap_limit_128m":host["MemorySwap"]==134217728,
      "cpu_quota":host["NanoCpus"]==1_000_000_000,
      "all_capabilities_dropped":"ALL" in host["CapDrop"],
      "no_new_privileges":"no-new-privileges" in host["SecurityOpt"],
      "nonroot_user":config["User"]=="65534:65534",
      "only_tmpfs":list(host["Tmpfs"])==["/tmp"],
      "no_host_mounts":not host["Binds"] and not data["Mounts"]
    }
    assert all(checks.values()),checks
    started=docker("start","-a",cid,timeout=45)
    assert started.returncode==0,{"exit":started.returncode,"stderr":started.stderr,"stdout":started.stdout}
    runtime=json.loads(started.stdout)
    assert runtime["kind"]=="docker_sandbox_negative_boundary_probe"
    for k in ("readonly_root_denied","tmpfs_writable","external_tcp_denied","effective_capabilities_zero"):
        assert runtime[k] is True, runtime
    result={"kind":"native_aot_docker_confinement_gate","result":"PASS","docker_constraints":checks,
            "runtime_denial_checks":runtime,
            "scope":"No-network, nonroot read-only disposable container; no hostile code, host escape, or Windows parity tested."}
finally:
    docker("rm","-f",cid)
# Second disposable container: actively verify cgroup memory enforcement.
# Do not run the memory allocation test outside Docker.
created_memory=docker("create",*flags,a.image,"sandbox-memory-probe")
assert created_memory.returncode==0,created_memory.stderr
memory_cid=created_memory.stdout.strip()
try:
    memory_run=docker("start","-a",memory_cid,timeout=45)
    memory_state=docker("inspect",memory_cid)
    assert memory_state.returncode==0,memory_state.stderr
    state=json.loads(memory_state.stdout)[0]["State"]
    assert state["OOMKilled"] is True and state["ExitCode"]==137, {
        "state":state,"stdout":memory_run.stdout,"stderr":memory_run.stderr
    }
    result["memory_enforcement"]={
        "container_oom_killed":True,
        "container_exit_code":137,
        "requested_allocation_bytes":512 * 1024 * 1024,
        "configured_memory_cap_bytes":128 * 1024 * 1024,
        "scope":"Docker cgroup OOM kill in a disposable container only"
    }
finally:
    docker("rm","-f",memory_cid)

dest=Path(a.out)
dest.parent.mkdir(parents=True,exist_ok=True)
dest.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2))
