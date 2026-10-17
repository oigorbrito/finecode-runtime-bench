# Evidence-based C# tool parity: pinned Pi contracts

Source baseline: `earendil-works/pi` commit `8efd314fa3d3232ce197d8d7a6a5660530b9d83e`, from `sources.json`. The benchmark fetches this exact commit for source inspection. No Pi/FineCode source is modified.

## API shape inventoried

| Pi tool | Required input | Optional inputs | Runtime features evident in pinned implementation |
| --- | --- | --- | --- |
| `read` | `path` | `offset`, `limit` | 1-indexed lines, truncation, image attachment handling, pluggable I/O |
| `grep` | `pattern` | `path`, `glob`, `ignoreCase`, `literal`, `context`, `limit` | Regex or literal, ripgrep, gitignore-aware matches, matching-line context, output limits, cancellation |
| `find` | `pattern` | `path`, `limit` | Glob discovery via fd, gitignore-aware filtering, path normalization, output limits, cancellation |

Sources within the immutable upstream commit: `packages/coding-agent/src/core/tools/read.ts`, `grep.ts`, `find.ts`. A fail-closed GitHub Actions inventory asserts the parameter names and descriptions and writes JSON evidence. It is not a dynamic parity test.

## Actual C# coverage as of this checkpoint

The Native AOT experiment implements only `scan-file <path> <literal>`, returning a checksum and aggregate line/literal counts. Independent tests cover these bespoke semantics on Windows x64, Linux x64 and ARM64. **This does not implement any of the three Pi tool API contracts**: it lacks their accepted parameter shapes, output formatting, line content and offsets, globs, ignore behavior, cancellation, limits, image support and extension integration.

## Gate decision

`PROCESS_FEASIBILITY=PASS`; `BOUNDED_SCAN=PASS`; `PINNED_UPSTREAM_CONTRACT_INVENTORY=PENDING_CI`; `PI_READ_GREPFIND_PARITY=NOT_IMPLEMENTED`; `FULL_AGENT_PARITY=NOT_IMPLEMENTED`.

Do not rank or replace Pi/FineCode on scan-file timings. Next functional progress must select a small subset of **actual Pi output and error behavior** and run both implementations against identical fixtures on the same host; pass only when return values and error semantics match with a reviewed normalization policy.
