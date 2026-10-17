# Runtime comparison — evidence checkpoint (2026-10-17 UTC)

## Source fidelity and verdict

All candidates are pinned in `sources.json`. This report describes reproducible GitHub-hosted smoke and startup observations only. It is **not** a complete agent or Oracle Always Free benchmark.

| Candidate | Linux x64 | Linux ARM64 | Scope |
|---|---|---|---|
| Pi TypeScript / Node | PASS | PASS | upstream build and smoke; `--version` |
| Pi TypeScript / Bun standalone | PASS | PASS | official `build:binary`; `--version` |
| Pi Rust | PASS | PASS | upstream workspace tests + release CLI |
| Pi Go | PASS | PASS | upstream `go test ./...` and CLI build |
| Pi Python | FAIL | FAIL | missing imported `pi_agent.harness.env` in pinned source |
| Zig | NOT RUN | NOT RUN | implementation not pinned |
| C# Native AOT | NOT RUN | NOT RUN | implementation not pinned |

## Raw timing observations

Median wall-clock startup from 11 runs, after 3 warmups. **Not an identical-host controlled test.**

| Command | x64 median ms | ARM64 median ms | Run |
|---|---:|---:|---|
| TypeScript Node `--version` | 364.378066 | 716.016420 | 38995827906 |
| TypeScript Bun standalone `--version` | 364.762213 | 314.487751 | 38995827889 |
| Rust `--version` | pending final x64 value | 3.407494 | 38995827906 |
| Go `--help` | 3.391888 | 3.250158 | 38995055003 |

**Warnings:**
- Go invokes `--help`, so its figure cannot be ranked alongside `--version` without confirming equivalent command behavior and feature coverage.
- Runners may differ in CPU, load and caches. Bun ARM64 improvement is an observation, not a controlled causal estimate.
- No common agent task, memory RSS, peak CPU, token counts, cost, TUI, extensions, SDK parity, or Oracle VM experiment was completed.
- The Python failure is *not* a Go/Rust/TS comparative performance result. The original Python source imports `.env.python` from `packages/agent/src/pi_agent/harness/__init__.py` while no matching `env/python.py` exists at the pinned SHA. The harness now publishes source integrity JSON without altering the candidate.

## Audit trail

- Original baseline 38992881238
- Workspace preparation and validation 38993648845
- Python integrity detection 38994465088
- Go exploration 38995055003
- Standalone initial build failure (workspace dependencies not built) 38995436977
- Standalone official build passing 38995827889
- Latest full baseline 38995827906 (Python expected FAIL)

## Decision

**PASS for initial compilation/smoke and CLI timing, BLOCKED for full runtime parity ranking.**

Next substantive gate is cross-candidate deterministic mocked agent tasks plus peak RSS, CPU, executable size and same-host repeatability. Retain manual merge and preserve the main FineCode repository untouched.
