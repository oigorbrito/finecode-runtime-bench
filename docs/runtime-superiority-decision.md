# Runtime choice: outperform the pinned Pi, not just pass tests

## Decision gate

The decision variable is **correct, complete programming work per second, MiB and dollar** on the target constrained hardware. Passing a subset of `read`, `grep`, and `find` is a prerequisite for fair measurement, **not evidence that C# is a better replacement**.

### Phase 1 — cold tool comparison (new, deliberately narrow)

[Workflow #39045032146](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/39045032146) invokes the **original pinned Pi** and the .NET Native AOT probe with identical `read` and `grep` fixtures on the **same runner**: Linux x64, Linux ARM64, Windows x64. There are 30 randomized paired trials per task per runner. **Exact output equality gates every timing pair**. JSON artifacts record wall-time ratio, sampled parent RSS and raw samples; failures are reported rather than ranked.

A fresh Node process loads the real Pi implementation per sample; a fresh C# process executes the bounded equivalent. This measures **cold single-tool entrypoint overhead**, not an already running Pi agent. RSS is polled from the parent process only at ~1 ms intervals and can underestimate peaks. Processes are timed end-to-end including executable startup and output capture. The comparison does **not** justify core replacement even if AOT wins by a large margin.

### Phase 2 — decision-grade agent performance (not yet implemented)

An agent-quality benchmark must run the **same task corpus**, same API model and prompting configuration, identical tool permissions, same machine, same model responses or replay fixture, stable timeout/retry policy, and identical success oracle for Pi and the alternative. Measure at least: wall/CPU time, peak memory including children, successful tasks per dollar and token, test pass quality, token consumption and failure modes. Report medians and variance, paired seeds, distributional differences, and compile/startup/dependency costs. Do not compare a minimal C# probe to a full Pi agent.

**Explicit replacement gate:** a real C# agent must demonstrate matching required capabilities and correctness on the same tasks, followed by a meaningful, repeatable performance/cost advantage that exceeds migration and maintenance risk. If measured performance is worse, ambiguous or costly in engineering effort: **KEEP PINNED PI TYPESCRIPT**.

No production FineCode change, no merge, no paid API calls. All compatibility and isolated executor tests remain separate from any replacement recommendation.

## Verified eliminatory checkpoint (2026-10-17)

### A. Eliminate the **pinned Python port** from the current eligible set

[Eligibility gate #39045479591](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/39045479591) **2/2 PASS** (Linux x64, ARM64). This is a *successful detection of a disqualifying defect*, not successful Python agent tests. The pinned `pi_python` at `95c8dc1ffa260bc0080c00c1f66e19844e8f53a6` imports `from .env.python import ...` from `packages/agent/src/pi_agent/harness/__init__.py`, yet `env/python.py` is absent. Machine-readable evidence: `eliminated-python-port-ubuntu-24.04` and `eliminated-python-port-ubuntu-24.04-arm`.

**Decision: `pi_python@95c8dc1 = ELIMINATED_PINNED_REVISION`** from a *currently functional replacement candidate* pool. This does **not** eliminate Python as a language or a fixed future port; re-enter only after restoring required module and passing official tests.

### B. Head-to-head cold single-tool speed: C# Native AOT beats fresh Node process loading the pinned Pi

[Randomized paired run #39045032146](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/39045032146) **3/3 PASS**. Each test executes the actual pinned Pi `read` or `grep` tool in a new Node process and a bounded C# Native AOT counterpart in a new process. 30 randomized pairs **per operation per runner**, exact output match required in every pair. Latency below is median end-to-end wall ms. RSS is **~1 ms sampled parent-process memory only**, not an accurate peak or an agent-level footprint.

| Platform | Operation | Pi Node (ms) | C# AOT (ms) | Pi/C# cold latency ratio | Node sampled RSS (MiB) | C# sampled RSS (MiB) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Linux x64 | read | 284.84 | 3.99 | 71.4× | 81.96 | 5.69 |
| Linux x64 | grep | 289.32 | 4.00 | 72.3× | 81.76 | 5.72 |
| Linux ARM64 | read | 270.48 | 2.84 | 95.3× | 77.23 | 3.38 |
| Linux ARM64 | grep | 272.59 | 2.80 | 97.3× | 77.44 | 3.14 |
| Windows x64 | read | 427.31 | 14.67 | 29.1× | 62.71 | 8.67 |
| Windows x64 | grep | 437.87 | 15.12 | 29.0× | 63.09 | 8.47 |

Artifacts: `pi-aot-cold-linux-x64`, `pi-aot-cold-linux-arm64`, `pi-aot-cold-win-x64`, with per-pair measurements and output hashes.

**Narrow elimination:** `fresh-Node-process-per-single-tool-invocation` is an objectively **inferior deployment pattern** to the tested Native AOT probe on these cold workloads. **The Pi architecture itself is NOT eliminated**, since its genuine agent keeps Node running and avoids repeatedly importing its tooling for each operation. Neither Rust/Go/Bun was compared with this identical workload in this run, so none of them is eliminated or ranked against C# by this result. C# is still a deliberately incomplete subset and not a replacement. Any proposal to change FineCode's core must await warmed-agent, same-task and full-quality benchmarks.

**Gate decision:** eliminate defective pinned Python candidate and the *cold reinitialize-Node-on-every-tool-call design*, retain Pi TypeScript as production reference; Rust, Go, Bun and C# remain subject to comparable functional/performance gates.
