# Linux Docker confinement — C# Native AOT experimental executor

Scope: **Linux container**, not Windows process isolation, and not full Pi/FineCode agent parity. Original FineCode and pinned Pi sources are not modified.

## Verified baseline

[GitHub Actions run #39044031294](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/39044031294) completed **2/2 Linux jobs PASS**: x64 and ARM64. The CI built a native C# .NET 9 AOT binary and placed it in a disposable Ubuntu 24.04 container. The Python verifier inspected the *created container's actual Docker HostConfig* and then invoked `sandbox-probe` inside it.

| Boundary | Docker config verified | In-container active test |
| --- | --- | --- |
| Network | `--network none` | TCP connect to public IP refused |
| Root filesystem | `--read-only` | write to `/var/tmp` denied |
| Writable scratch | `--tmpfs /tmp:rw,nosuid,nodev,noexec,size=8m` | read/write/delete temporary file succeeds |
| Privileges | `--user 65534:65534`, `--cap-drop ALL`, `no-new-privileges` | `CapEff` zero |
| Memory | `--memory 128m --memory-swap 128m` | cap checked in Docker HostConfig; active OOM test separately pending |
| Processes | `--pids-limit 32` | cap checked in Docker HostConfig, fork/process saturation not tested |
| CPU | `--cpus 1.0` | cgroup configuration inspected; CPU throttling not benchmarked |
| Host mounts | none | no host bindings found in Docker inspect |

The single binary is **not** mounted from the host; it is baked into the ephemeral image. All tests use synthetic data. Neither a paid model API call nor network access from the container is required. Image remains a Linux image and the Docker daemon is a trusted host service; do **not** treat this as a tested escape-resistant arbitrary-code sandbox.

## Limitations and separation of evidence

The CI workflow `.github/workflows/dotnet-docker-confinement.yml` tests the executor **inside Docker**, which is different from the earlier Windows x64 C# **process timeout only** test. There is **no demonstrated Windows Job Object, Hyper-V, Windows Sandbox, or container boundary** in this experiment. Do not claim Windows isolation.

The separate memory-allocation negative control creates a **second disposable container**; only a positively observed `State.OOMKilled=true` and exit code 137 may justify claiming that Docker actively enforced the 128 MiB cap. Configuring a cap alone does not prove enforcement.

Do not move this experimental isolation layer into FineCode main without a reviewed threat model, filesystem allowlists, external input/command authorization, privilege regression tests, container runtime governance and end-to-end agent tool contract tests.
