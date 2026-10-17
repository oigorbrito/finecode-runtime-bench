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

## Pinned Go versus genuine Pi — warm tools (2026-10-17)

[GitHub Actions #39045890135](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/39045890135): **Linux x64 PASS and Linux ARM64 PASS**. Both runners built **pinned Pi TS/Node** and the immutable Go port SHA `53708dc48e03cdf59b7d7f63f059c65ad4bb45dc`. Only **test adapters** were copied into the working GitHub Actions checkout; upstream repositories were not modified. The benchmark kept both tool processes alive, executed actual exported `read` and `grep` tools against identical fixture content, randomized execution order for **60 pairs per runner**, and required **exact JSON text-output equality** on every comparison: **120/120 matching responses**.

| Target | Pi TS/Node median all calls | Go median all calls | Relative warm latency (Pi/Go) | Pi read | Go read | Pi grep | Go grep |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Linux x64 | 2.1092 ms | 0.0921 ms | 22.9× | 0.5623 ms | 0.0920 ms | 3.6398 ms | 0.0925 ms |
| Linux ARM64 | 2.2454 ms | 0.1127 ms | 19.9× | 0.5243 ms | 0.0995 ms | 3.9979 ms | 0.1186 ms |

Artifacts `pi-go-warm-linux-x64`, `pi-go-warm-linux-arm64` contain case-level timings and outputs-gated summaries. The Go candidate uses its **own in-process tool implementation**, while original Pi grep commonly calls `rg` as a child. This is a meaningful same-run tool implementation difference, not just an AOT startup result. It also means the compared tool mechanisms and resource accounting differ: no per-child CPU or RSS was measured, and neither full agent loop nor provider/token costs were exercised.

**Eliminatory claim scoped to this exact workload:** the original Pi Node tools are **not the lowest-latency option** for these warmed `read`/`grep` fixtures. The Go candidate must **not** be declared an agent winner without a larger parity/quality and full-task cost matrix, and this evidence cannot eliminate Pi as a mature functional reference.

The Rust pinned port's own source explicitly states that its `grep`/`find` search skips `.git` but does not fully honor `.gitignore`. A separately executable actual-Pi differential suite (`pi-rust-gitignore-eligibility.yml`) is being validated before issuing an elimination decision. **Do not eliminate Rust from an adapter's build failure.**

## Second pinned-candidate elimination — Rust port strict Pi tool parity (2026-10-17)

[Real original Pi vs pinned Rust tool differential #39046522338](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/39046522338): **Linux x64 PASS + Linux ARM64 PASS**. The suite built the actual Rust port `bigfish1913/pi-rust` SHA `b6b8e8311a4d6fd5dd1dc9e436e96f5d4cd22a52`, injected a **temporary test adapter** only into the CI worktree, and directly executed its exported `grep` and `find` tools against Pi's real compiled TypeScript tools. Both received the same initialized Git repository fixture: `.gitignore` containing `*.txt`, with `ignored.txt` containing `NEEDLE`.

| Tool | Actual Pi output (both runners) | Actual Rust port output (both runners) | Strict parity |
| --- | --- | --- | --- |
| find `*.txt` | `No files found matching pattern` | `ignored.txt` | FAIL |
| grep `NEEDLE` | `No matches found` | `ignored.txt:1: NEEDLE` | FAIL |

The CI assertions **PASS because they reproducibly detect the material Rust/Pi divergence**, not because the Rust tool is compatible. Two downloadable artifacts, `rust-gitignore-eligibility-linux-x64` and `rust-gitignore-eligibility-linux-arm64`, preserve actual tool outputs. The pinned Rust source itself notes that `grep` and `find` skip `.git/` directories but do not support full `.gitignore` semantics.

**Decision: `pi_rust@b6b8e831 = ELIMINATED_PINNED_REVISION_FOR_STRICT_TOOL_PARITY`.** This does not eliminate Rust as a programming language, nor deny Rust's startup/memory advantages or potential as an isolated executor. Re-admit a corrected port only after identical-fixture `.gitignore` functional checks pass on both architectures; then complete full agent task, cost and quality benchmarks.

The first two CI attempts failed while resolving **test-adapter Cargo dependencies** (`--locked` / offline cache), not due to Rust functional behavior. The harness was corrected, dependencies resolved on the next run, and the actual functional discrepancy was observed on both runners. Do not count earlier harness failures as candidate failure.

### Current elimination ledger

| Candidate/version | Gate result | Consequence |
| --- | --- | --- |
| Python pinned revision `95c8dc1` | Missing required source module, reproduced x64+ARM64 | ELIMINATE revision as currently runnable |
| Rust pinned revision `b6b8e83` | Actual Pi `grep` and `find` disagree on `.gitignore`, x64+ARM64 | ELIMINATE revision as strict Pi-compatible drop-in |
| Go pinned revision `53708dc4` | 120/120 matching warm `read`/`grep`, lower observed tool latency on x64+ARM64 | RETAIN; larger functionality and cost gates pending |
| Pi Node original | Reference correctness and full feature set; slower on measured warm read/grep | RETAIN as production baseline |
| Pi Bun | Same official Pi source with another runtime/distribution | RETAIN, same-host functionality/performance still needed |
| C# Native AOT probe | Small tool subset, strong cold execution; no complete agent | RETAIN as component research only |
| Zig | No pinned comparable implementation | INELIGIBLE pending runnable candidate |

**No new FineCode core migration authorized.** A performance win in warm tool microtasks is not an agent-level superiority verdict. Proven eliminations are version-specific and based on material functionality readiness; do not interpret them as universal language rankings.

## Three-way real pinned tool benchmark — Node, Bun, Go (2026-10-17)

[GitHub Actions #39048225310](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/39048225310): **2/2 jobs PASS**, Linux x64 and Linux ARM64. Each run kept three processes warm: original Pi TypeScript code loaded by Node 24.21.0, the **same original Pi source code** loaded by Bun 1.4.3, and the pinned Go port's actual exported tools. Each executed 90 randomized triplets of `read`/`grep` under the same runner; **180/180 equal tool text outputs** across the two runners. Per-platform JSON artifacts record raw samples, timings, runtimes and exact fixture protocol.

| Target | Tool | Node median ms | Bun median ms | Go median ms | Go speedup over Node |
| --- | --- | ---: | ---: | ---: | ---: |
| Linux x64 | read | 0.48778 | 0.35992 | **0.08534** | 5.7× |
| Linux x64 | grep | 3.50604 | 2.18606 | **0.09743** | 36.0× |
| Linux ARM64 | read | 0.55990 | 0.41606 | **0.10701** | 5.2× |
| Linux ARM64 | grep | 3.80603 | 1.85653 | **0.11970** | 31.8× |

**Elimination scoped to warm `read`/`grep` microtasks:** original Pi/Node is slower than Bun and the Go port; Go is fastest in all four comparisons. Bun's warmed Pi `grep` (still using its original code) improves relative to Node without reimplementation. Do not extrapolate to coding agent performance, model tokens, tool success under corner cases, RSS, CPU, multi-file search or entire tasks. Go `grep` is a different in-process algorithm; Pi uses ripgrep. Measure their fidelity beyond the deliberately small fixtures before declaring replacement.

### More meaningful follow-on gate: deterministic code repair task

Workflow `.github/workflows/pi-node-bun-go-coding-task.yml` and harness `scripts/compare_pi_node_bun_go_coding_task.py` execute a real **four-tool coding chain** `write → edit → read → grep` in separately isolated temporary directories for Node, Bun and Go. The task starts with broken Python code (`return n + 1`) and edits it to `return n * 2`; a separately invoked Python oracle asserts correct behavior on six values including negative numbers. 24 randomized rounds per target, identical final source bytes, and identical read/grep text outputs are required, and no model or API call is used. Tool-chain time is measured separately from oracle invocation. Failures gate the workflow rather than being silently discarded. This is still a deterministic *tool-chain* test, not an autonomous LLM agent programming task.

**Decision**: Results from true end-to-end agent loops (same replayed LLM outputs or identical model/provider responses, tokens and task corpus, equivalent capabilities and feature flags, memory including child processes) must precede any TypeScript core migration.

### VERIFIED: multi-step code repair and executable correctness (2026-10-17)

[GitHub Actions #39048384062](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/39048384062) completed **2/2 Linux jobs PASS** (x64 and ARM64). Three persistent candidate processes per runner — pinned Pi/Node, the same Pi code under Bun, and the actual pinned Go tool port — each executed **24 independent small Python repairs** using the original exported `write → edit → read → grep` tool APIs. The test starts from `return n + 1` and makes a precise edit to `return n * 2`. For every repaired file, the Python interpreter independently asserted results on six inputs including negatives. Final source bytes and the `read`/`grep` outputs had to be identical across all three runtimes. **24/24 correct tasks per runtime per OS** = **144 successful candidate-task executions total**; no observed wrong final files.

| OS | Pi/Node median tool-chain ms | Pi/Bun median tool-chain ms | Go median tool-chain ms | Node/Go ratio | Bun/Go ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| Linux x64 | 5.2424 | 3.7888 | **0.5576** | 9.4× | 6.8× |
| Linux ARM64 | 5.6481 | 3.8161 | **0.6376** | 8.9× | 6.0× |

The timer covers four tool API calls; the Python program execution oracle is performed **after** the timer. The task sequence is predetermined rather than chosen by an LLM. Although this is much stronger than process startup or `read`/`grep` alone, it still does **not** show that Go beats Pi on autonomous code generation, token use, model latency, diverse codebases, or full agent quality. The measurement is a straightforward fixed-operations tool benchmark under warm processes; C# was not in this contest because its harness is only a bounded partial implementation, not a drop-in `write`/`edit` agent.

Artifacts: `pi-node-bun-go-coding-linux-x64` and `pi-node-bun-go-coding-linux-arm64`, each containing round-level timings and success gating.

**Decision within measured workload:** retain Go as **speed winner for the tested persistent coding-tool chains on both platforms**, with Bun as a source-preserving faster alternative to Node. Eliminate neither original Pi nor Bun from the agent-level contest. Any replacement recommendation requires equal feature coverage and model/replay agent-loop tasks, peak CPU/RAM including subprocesses, errors and token/cost quality. The earlier Rust and Python eliminations are **pinned-revision compatibility/eligibility eliminations** only.

## Actual agent-loop replay — verified gate (2026-10-17)

[GitHub Actions #39049918558](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/39049918558) **PASS on Linux x64 and Linux ARM64**. The original pinned Pi TypeScript `Agent.prompt()` running under Node/Bun and the pinned Go port's `Agent.Prompt()` were driven with a deterministic, offline stream of four model-authored tool calls (`write → edit → read → grep`) followed by a final answer. Every candidate executed 20 scored tasks per runner, each independently validated on six Python inputs. **120/120 code repairs correct**, exactly four tool-result events per repair and five streamed model decisions.

| Platform | Node median agent loop | Bun median agent loop | Go median agent loop | Node/Go |
| --- | ---: | ---: | ---: | ---: |
| Linux x64 | 5.8302 ms | 4.4263 ms | **0.3113 ms** | 18.7× |
| Linux ARM64 | 8.3181 ms | 5.1835 ms | **0.5916 ms** | 14.1× |

**Important parity issue:** TypeScript/Node and TypeScript/Bun recorded **11 messages**, while Go recorded **10**, on both runners. This may reflect different system-message or tool-declaration handling, but the precise cause has **not** been validated. Therefore transcript structural parity is **NOT PROVEN**, despite equal tool calls and successful output. The replay is scripted, not real autonomous model reasoning or token/cost measurement.

A second run (same workflow) has been prepared to supply an identical explicit system prompt and verify each stream function actually receives it; its result must be checked independently. Do **not** promote Go to a full Pi replacement on current evidence. Narrow result: Go has lower agent-loop execution latency for this fixed 4-tool offline replay. Full production comparison still needs diverse agent tasks, failure handling, complete transcript semantics, peak RAM/CPU, and model token/cost metrics.

## Corrected shared-system-prompt agent replay: measured and contract-gated (2026-10-17)

[Successful rerun #39050502411](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/39050502411), Linux x64 and ARM64, **both success**. The original Pi agent with Node, the identical Pi source with Bun, and pinned Go agent all received **the same explicit system prompt**. Each model replay adapter now checks that the prompt actually reaches its model-stream function; every one of 120 scored repairs passed source-file correctness, tool event count, and six-value Python oracle.

| Runner | Node median agent replay ms | Bun median ms | Go median ms | Node/Go |
| --- | ---: | ---: | ---: | ---: |
| Linux x64 | 6.4038 | 4.5654 | **0.4131** | 15.5× |
| Linux ARM64 | 8.4866 | 4.9848 | **0.4632** | 18.3× |

**Confirmed transcript discrepancy:** Node/Bun Agent `state.messages` has **11** entries, while Go Agent `State().Messages` has **10**, reproducible on both platforms **even after system-prompt alignment**. The TypeScript upstream `createMutableAgentState()` creates and prepends a `system` message to state when starting with system prompt and tools; Go `NewAgent()` keeps `SystemPrompt` as a separate state property and only appends emitted message events to `Messages`. Go's model-context `SystemPrompt` was observed to carry the identical text, so this is specifically a **transcript representation/export compatibility gap**, not proven loss of model instruction. Strict drop-in transcript parity **FAIL**. It matters for serialized sessions and consumers of raw histories, not necessarily for a tool-execution-only adapter.

**Decision:** `GO_TOOL_EXECUTION_LATENCY=LEADER` on this fixed scripted replay; `GO_DROP_IN_AGENT_HISTORY_PARITY=FAIL` on the pinned revision. Do **not** replace Pi TypeScript core or session format based on the speed result. A Go tool executor behind the unchanged Pi agent remains a separate architecture worth measuring end-to-end if/when its IPC cost and fidelity justify it.

A further instrumented run records *individual message role sequences* in JSON to eliminate ambiguity about the extra message and distinguish history representation from tool-result count. Until that run completes, the confirmed discrepancy is the count and the source-based explanation; no unsupported claim of identical serialized history is made.
