# Token-efficiency benchmark protocol (pre-registration)

Status: SPECIFICATION ONLY — no model-token measurements have been run.

## Objective
Compare Pi upstream, Pi-Bolt under Node, Pi-Bolt Windows AOT and FineCode on *correctly solved* C#, Python and Go coding tasks. Runtime startup, wall time, CPU and memory are secondary, not proxies for model token use.

## Controls and identity
- Pin every repository to a full commit SHA, and record upstream tag, binary release tag, SHA-256, runtime versions and OS. FineCode must be included only when a reproducible revision is available.
- Use one identical model ID and provider, temperature and other generation parameters, system/developer/user instructions, tool permissions, context limits, workspace snapshot and timeout across variants.
- Use a local deterministic mock provider first to test accounting, event collection and tool-call parity. Mock tokens are synthetic and MUST NOT be presented as measured savings.
- Then use a real provider with an explicit spending cap and user-approved credentials. Never place keys in logs or artifacts.
- Randomize variant execution order within each task and repeat runs to estimate stochastic variation. Record failures, retries and incomplete tasks, not just successes.

## Tasks
- At least one small bug fix plus one test-driven feature per language: C#, Python and Go.
- Each task starts from the same immutable fixture and has independent hidden or held-out tests, plus a public build/test command.
- Prevent cross-run state contamination: fresh workspace, fresh session, identical initial context, no network unless task requires it.

## Event schema (JSONL, one row per provider request)
- run_id, task_id, language, variant, source_sha, model_id, provider, attempt, request_index, timestamp
- input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, reasoning_tokens (nullable), provider_reported_total_tokens, usage_source
- tool_calls, tool_results_bytes, context_compactions, retry_count, stop_reason, latency_ms, error_type
- Never reconstruct cache or reasoning counts from total usage; store missing values as null, not zero.
- Store task-level pass/fail, exit codes, test counts, total wall time, peak RAM, CPU time and estimated price using a versioned price table.

## Aggregation and gates
- Primary: total provider-billed tokens and cost per *correctly completed* task; also report solve rate separately to avoid selecting only easy successes.
- Secondary: input/output/cache/reasoning breakdown, requests, tool calls, compactions, latency, CPU and RAM.
- Include unsuccessful runs in total spend; report spend per success as total spend across all attempts / number of successes, and mark undefined when there are no successes.
- Report per-task paired comparisons, median and dispersion; do not claim token savings from a single run or from runtime-only measurements.
- Do not merge runtime optimizations into FineCode unless functional parity and measurable benefit hold without material regression.

## Gates
1. Instrumentation self-test: controlled mock usage counts and failure/retry paths; no paid API.
2. Provider accounting validation: compare collected usage to provider response, verify cached-token semantics and cost formula.
3. Real task benchmark: C#/Python/Go, randomized paired repeats, bounded spend, tests and full provenance.
4. Decision report: distinguish runtime efficiency from actual token efficiency; preserve manual merge approval.
