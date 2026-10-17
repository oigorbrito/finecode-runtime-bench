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
