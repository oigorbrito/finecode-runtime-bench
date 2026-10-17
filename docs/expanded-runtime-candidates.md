# Expanded language evaluation: standalone Pi, Zig, C# Native AOT

## Scope and evidence gates

| Candidate | Current classification | Entry gate | Benchmark gate |
| --- | --- | --- | --- |
| Pi TypeScript + Bun standalone | Same upstream source as Pi TS, different distribution/runtime | Build official `build:binary` from pinned source | Verify `--version` and equivalent functionality, then compare memory/CPU |
| Zig | Feasibility candidate only; no verified Pi-compatible port pinned | Identify real port or implement a separately authorized minimum contract with tests | Same behaviors, workload, pin, and architecture; no hello-world ranking |
| C# .NET Native AOT | Feasibility candidate only; no verified Pi-compatible port pinned | Identify real port and verify AOT support + feature contracts | Same behaviors/workload/measurement methodology; no hello-world ranking |

Do **not** compare an empty Zig/C# sample binary against a fully fledged Pi coding agent.

## Reproducibility

- Keep the upstream Pi revision fixed in `sources.json`.
- No paid model calls in the baseline. Run on Linux x64 and ARM64.
- Use the upstream-supported Bun build script `npm --prefix packages/coding-agent run build:binary`.
- First record installation/build failures without altering candidate sources.
- The Bun standalone startup measurement uses `--version`; comparisons with Node are preliminary until the exact CLI entry behavior and hardware/runtime conditions are matched.
- Next common benchmarks: startup, peak RSS, process CPU, executable size, session creation, filesystem tools and deterministic mock provider agent loop.
- Each measurement must record hardware details and repeat counts.

## Explicitly not demonstrated

- Zig or C# runtime parity with Pi.
- Token savings or operational agent quality.
- Oracle Always Free ARM64 performance solely from GitHub ARM64 runner timings.

No production FineCode files or candidate source files are changed by this evaluation.
