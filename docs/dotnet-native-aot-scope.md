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
