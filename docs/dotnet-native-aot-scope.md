# .NET Native AOT: bounded feasibility experiment

Status: **CI evidence pending**. This branch intentionally adds a minimal C# executable and measures its native-AOT process overhead on Linux x64.

## Defensible claims

- A successful CI run would establish that the runner can compile and execute a .NET 9 Native AOT binary.
- The independent measurement records median process invocation wall-time, user+system CPU time, peak RSS and binary size over 25 separate invocations.
- These metrics **cannot** be compared directly as agent-performance results against TypeScript Pi, Rust Pi or Go Pi. The C# process has no tool execution, providers, TUI, context handling, sessions, OAuth, or agent loop.
- A future C# implementation must pass the same functional contract suite before any performance ranking or core replacement discussion.
- No calls to paid model APIs, no changes to FineCode main or any upstream candidate, and no automatic merge.

Reproduce on an Ubuntu 24.04 x64 environment with .NET 9 SDK and Native AOT compilation toolchain:

```sh
dotnet publish candidates/dotnet-aot/Probe.csproj -c Release -r linux-x64 --self-contained true -p:PublishAot=true -o candidates/dotnet-aot/out
python3 scripts/measure_dotnet_aot.py --binary candidates/dotnet-aot/out/Probe --out results/dotnet-aot-linux-x64.json
```

## First CI evidence (2026-10-17)

[Linux x64 workflow run 39003348079](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/39003348079) **PASS**: .NET 9 Native AOT publish, executable `--help` and `--version`, and 25 independent process invocations.

| Measure | Observed median |
|---|---:|
| CLI `--help` wall time | 3.130823 ms |
| Peak RSS | 3.3984375 MiB |
| Binary size | 1,331,832 bytes |
| CPU (user + system) | 0.0 ms (measurement **below resolution**, not zero CPU consumption) |

The CPU fields originate from GNU `/usr/bin/time` with limited decimal precision. Values rounded to zero cannot demonstrate zero CPU usage. This experiment is a **trivial native-process lower bound**, not Pi feature parity; ranking against any coding agent would be invalid.

## Cross-platform reproducible gate — PASS

[GitHub Actions run #39003740125](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/39003740125) — **3/3 independent matrix jobs PASS**, .NET 9 Native AOT on Ubuntu x64, Ubuntu ARM64 and Windows x64. Each job built and executed the native binary and checked `--help` and `--version`; 25 independent CLI `--help` invocations were measured on each runner.

| Measurement | Linux x64 | Linux ARM64 | Windows x64 |
|---|---:|---:|---:|
| Median wall time (ms) | 2.389254 | 2.143172 | 11.789 |
| Median CPU (ms) | 2.236 | 2.032 | 15.625 |
| Median peak RSS/working set (MiB) | 3.3984375 | 2.83984375 | **unavailable**, not zero |
| Binary size (bytes) | 1,331,832 | 1,253,840 | 1,109,504 |
| Job conclusion | PASS | PASS | PASS |

**Methodology boundaries:** Linux process CPU uses microsecond-resolution `resource.getrusage(RUSAGE_CHILDREN)` deltas and includes the GNU `time` wrapper process; Windows uses `System.Diagnostics.Process.TotalProcessorTime` with coarse accounting precision. These CPU figures are **not** equivalent instruments. The Windows child terminates before `PeakWorkingSet64` can reliably report a peak, so the script intentionally emits `null` with `rss_status=unavailable_after_fast_process_exit` instead of an impossible 0 MiB. Do not rank the operating systems against each other using these measurements; runners differ. Linux peak RSS comes from GNU `time` and Windows working set is a different measure.

**Architectural decision:** This proves native C# **process feasibility** on all three targets, not a port of Pi. The feature parity and functional workflow gates remain **NOT RUN**; a Pi core replacement is **NOT AUTHORIZED** by these results.

Artifacts: `dotnet-aot-linux-x64`, `dotnet-aot-linux-arm64`, `dotnet-aot-win-x64` from the referenced workflow.

## First real operation: bounded read-only file scan (not Pi parity)

The probe now accepts `scan-file <path> <literal>` and returns JSON with UTF-8 byte count, deterministic newline-based line count, non-overlapping ordinal substring occurrences, and SHA-256 of the original bytes. Malformed UTF-8, missing files, missing/empty literals, and unknown commands fail closed with a nonzero exit code.

`scripts/verify_dotnet_scan_contract.py` provides a separately implemented Python oracle and checks deterministic empty, one-line, multiline, Unicode, overlapping literal, and approximately 200 KiB payload fixtures, plus three invalid-invocation cases. CI runs exactly the same contract suite on Windows x64, Linux x64, and Linux ARM64, saving a JSON case-level report per target. The C# source and Python oracle use different implementations of counting and hashing. No paid API calls.

**Unproven:** Pi tool APIs, sandboxing/path authorization, model providers, TUI, network, patch/edit, session persistence, extension discovery and agent loop. File-reading the path requested by the invoking test is intentional and not an isolated tool executor. These contracts are a small deterministic functional building block, not comparable agent workloads. Passing them must not authorize migration of FineCode's upstream TypeScript core.

## Bounded functional contract gate — PASS (2026-10-17)

[Windows x64 / Linux x64 / Linux ARM64 CI #39006400692](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/39006400692): **3/3 jobs PASS**. Independent Python oracle verified **7 groups on each operating system** (21 successful group checks, covering 6 valid fixtures and 3 invalid-invocation subcases per OS). Checks include deterministic UTF-8 byte count, line count, nonoverlapping ordinal search, SHA-256 and failure exit behavior. The test runner captures individual case outcomes in `results/dotnet-scan-<rid>.json`, included in each platform's `dotnet-aot-<rid>` artifact. The same matrix continues the initial build, CLI startup and resource probe.

These new results are a genuine **file-processing behavioral check**, not merely `--help` timing. They do **not** establish equivalent Pi `read` or `grep` tools (access controls, formatting, ignore semantics, limits, error contracts, cancellation, tool orchestration, and streaming have not been matched). Neither an agent port nor a full parity suite exists for C#. **Decision: C# process feasibility and bounded file-scanning behavior PASS; Pi functional parity NOT TESTED; core migration NOT JUSTIFIED.**
