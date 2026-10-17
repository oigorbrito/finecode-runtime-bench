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
| Memory | `--memory 128m --memory-swap 128m` | cap checked in Docker HostConfig; active differential allocation test PASS on x64 and ARM64 |
| Processes | `--pids-limit 32` | cap checked in Docker HostConfig, fork/process saturation not tested |
| CPU | `--cpus 1.0` | cgroup configuration inspected; CPU throttling not benchmarked |
| Host mounts | none | no host bindings found in Docker inspect |

The single binary is **not** mounted from the host; it is baked into the ephemeral image. All tests use synthetic data. Neither a paid model API call nor network access from the container is required. Image remains a Linux image and the Docker daemon is a trusted host service; do **not** treat this as a tested escape-resistant arbitrary-code sandbox.

## Limitations and separation of evidence

The CI workflow `.github/workflows/dotnet-docker-confinement.yml` tests the executor **inside Docker**, which is different from the earlier Windows x64 C# **process timeout only** test. There is **no demonstrated Windows Job Object, Hyper-V, Windows Sandbox, or container boundary** in this experiment. Do not claim Windows isolation.

The separate memory-allocation negative control creates a **second disposable container**; only a positively observed `State.OOMKilled=true` and exit code 137 may justify claiming that Docker actively enforced the 128 MiB cap. Configuring a cap alone does not prove enforcement.

Do not move this experimental isolation layer into FineCode main without a reviewed threat model, filesystem allowlists, external input/command authorization, privilege regression tests, container runtime governance and end-to-end agent tool contract tests.

## Differential memory enforcement — PASS (2026-10-17)

[GitHub Actions #39044509964](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/39044509964): **Linux x64 PASS, Linux ARM64 PASS**. Each job builds the same C# Native AOT executable, then executes **identical 512 MiB allocation and page touching** inside two separately created Docker containers (no network, nonroot, read-only, no host mounts, limited processes and capabilities):

| Measurement | Linux x64 | Linux ARM64 |
| --- | --- | --- |
| 128 MiB container: allocation | refused, managed `OutOfMemoryException` | refused, managed `OutOfMemoryException` |
| 128 MiB container: process exit | 139 | 133 |
| 128 MiB container: Docker `State.OOMKilled` | false | false |
| 768 MiB container: same allocation | succeeds (exit 0) | succeeds (exit 0) |
| Docker confinement negative tests | PASS | PASS |
| Overall workflow job | PASS | PASS |

The **differential positive control is essential**: without it, the managed exception alone could be caused by another runtime limitation. The evidence supports **effective memory-constrained execution** at 128 MiB under the tested allocation, but not a Linux kernel OOM kill. The process did **not** report Docker `OOMKilled=true` on either platform, and the exit codes differed (139 vs 133). The harness therefore explicitly accepts a managed `OutOfMemoryException` or a Docker-recorded OOM kill **only if the same allocation succeeds under the 768 MiB control**. It does not silently convert managed OOM to kernel OOM.

Reproducible evidence: `scripts/verify_dotnet_docker_isolation.py`, `candidates/dotnet-aot/Program.cs`, workflow `.github/workflows/dotnet-docker-confinement.yml`, artifacts `dotnet-docker-confinement-linux-x64` and `dotnet-docker-confinement-linux-arm64`, including Docker-inspected configuration and live runtime observations.

## Decision

`LINUX_CONTAINER_BOUNDARIES=PASS` for these synthetic denied-write, external-network, nonroot/no-capability checks; `LINUX_MEMORY_RESTRICTION_DIFFERENTIAL=PASS` for two independent runner architectures. `WINDOWS_ISOLATED_EXECUTOR=NOT_TESTED`, `PROCESS_COUNT_ENFORCEMENT=CONFIG_ONLY`, `CPU_THROTTLE_ENFORCEMENT=CONFIG_ONLY`, `HOSTILE_CODE_CONTAINMENT=NOT_TESTED`, `AGENT_TOOL_PARITY=NOT_TESTED`. This does not authorize changing FineCode's core or deploying untrusted agents.
