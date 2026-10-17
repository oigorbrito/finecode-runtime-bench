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
