# Same-host CLI resource benchmark — 2026-10-17 UTC

Reproducible workflow: [run 38996676841](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/38996676841). All jobs PASS.

## Median across 11 samples after 3 warmups

Each architecture used a **single GitHub Actions runner to build and measure all four binaries**. These are separate hosts across architectures. All commands used `--help`.

| Runtime | ARM64 wall ms | ARM64 CPU ms | ARM64 peak RSS KiB | x64 wall ms | x64 CPU ms | x64 peak RSS KiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Node Pi | 754.454094 | 974.500 | 140356 | 782.170555 | 1034.268 | 143660 |
| Bun standalone Pi | 354.642668 | 448.666 | 96176 | 376.038937 | 508.874 | 94772 |
| Rust Pi port | 1.882451 | 2.138 | 13468 | 1.920103 | 2.253 | 14524 |
| Go Pi port | 2.371321 | 2.661 | 13468 | 2.612117 | 3.048 | 14480 |

Artifacts:
- `resources-ubuntu-24.04-arm` (artifact ID 12086584689)
- `resources-ubuntu-24.04` (artifact ID 12087054829)

Measurements: Python `os.wait4` child rusage, with `ru_maxrss` in KiB on Linux; per-invocation CPU time is user + system CPU, and wall time is monotonic perf counter. CPU time can exceed elapsed wall time under parallelism.

## Interpretation and limits

1. Both x64 and ARM64 measurements passed for Node, Bun, Rust and Go CLI help. Rust/Go's small CLI help path is not evidence of feature parity with upstream Pi.
2. This run controls for *runner within architecture* but not CPU architecture, model, thermal/noisy-neighbor effects, process caching, or environment outside the job.
3. The four commands share the flag `--help`, **not verified identical help output or internal initialization semantics**; this is closer to fair command selection than the previous `--version` / `--help` mix, but still not full workload equivalence.
4. No agent loop workload, tool I/O, memory under active inference, token utilization, API costs, extensions or TUI parity was measured.
5. Pi Python is excluded because its pinned source imports a missing module. Zig and C# Native AOT remain unimplemented feasibility candidates.
6. The next substantive gate is a deterministic mock-provider agent loop + tool execution with exact behavior assertions per candidate; only then compare CPU and RSS for agent work. Do not port Pi core or endorse migration from CLI help data.

No changes to FineCode production repository and no automated merges.
