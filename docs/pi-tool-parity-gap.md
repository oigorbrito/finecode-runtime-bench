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

`PROCESS_FEASIBILITY=PASS`; `BOUNDED_SCAN=PASS`; `PINNED_UPSTREAM_CONTRACT_INVENTORY=PASS`; `PI_READ_GREPFIND_PARITY=NOT_IMPLEMENTED`; `FULL_AGENT_PARITY=NOT_IMPLEMENTED`.

Do not rank or replace Pi/FineCode on scan-file timings. Next functional progress must select a small subset of **actual Pi output and error behavior** and run both implementations against identical fixtures on the same host; pass only when return values and error semantics match with a reviewed normalization policy.

## Audited CI result — PASS

[GitHub Actions run #39007208435](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/39007208435), pinned commit `8efd314fa3d3232ce197d8d7a6a5660530b9d83e`, returned `{"result":"PASS","tools":["read","grep","find"],"parameter_count":13}`. All 13 schema parameters are detected, and the run uploads `pinned-pi-tool-contract-inventory` as a downloadable JSON evidence artifact. The initial source-schema matcher was **incorrect** for nested `Type.Optional(Type.Number(...))`; it caused a deliberate red CI gate and was repaired in `403f6d9` before this passing run. This is a source-schema **inventory only**: C# has **not** passed Pi's runtime behavior contracts.

## Bounded text-read behavioral gate — PASS

[Windows x64, Linux x64 and ARM64 run #39007871232](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/39007871232): all **3/3 Native AOT jobs PASS**, including **19 independently expected text read subset cases per target**, 57 passes, zero failures. A separate Python oracle validates empty files, terminal newline, CRLF, UTF-8, negative/zero/one-indexed offsets, out-of-bounds, optional line limits, continuation notices and missing-file failures.

The implementation is explicitly exposed as `read-subset`, **not** `read`: it mirrors a **bounded subset** of the immutable Pi `read.ts` logic at lines 156–204, for small text without truncation. The first CI invocation failed because the Python subprocess text decoder normalized CRLF; the oracle was corrected to capture raw bytes and then UTF-8 decode, preserving literal newline sequences. This was **a harness defect**, not proof of C# failure.

Remaining not implemented: exact agent-tool parameter/envelope contract, full truncation messages, images, line/byte limits under oversized input, path resolution, stream/cancel behavior and tool integration. The upstream Pi tool was **not executed head-to-head in this gate**; Python independently encodes the reviewed expected text behavior. Thus `BOUNDED_TEXT_READ=PASS`, `FULL_PI_READ_PARITY=NOT_PROVEN`, `PI_GREP_PARITY=NOT_RUN`, `PI_FIND_PARITY=NOT_RUN` and `AGENT_PARITY=NOT_RUN`. This cannot justify FineCode core migration.

## Direct execution against the real pinned Pi read tool — PASS

[GitHub Actions run #39008221402](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/39008221402), executed `createReadToolDefinition(...).execute(...)` from the **built original Pi** checked out at SHA `8efd314fa3d3232ce197d8d7a6a5660530b9d83e`; on the same runner the benchmark executed the .NET 9 Native AOT `read-subset` binary with identical file fixtures and offsets/limits. The harness compares successful text outputs **exactly**, including CRLF, and compares the offset-boundary error message when both calls fail.

| Runner | Direct read-subset comparisons | Result |
| --- | ---: | --- |
| Linux x64 | 11/11 | PASS |
| Linux ARM64 | 11/11 | PASS |
| Windows x64 | 11/11 | PASS |
| **Total** | **33/33** | **PASS** |

Artifacts `live-pi-read-linux-x64`, `live-pi-read-linux-arm64` and `live-pi-read-win-x64` contain case-level raw output and status. Tests exercise empty, one-line, limited, zero/negative/invalid offsets, trailing newline, CRLF, UTF-8, and zero line limit. No paid model/API calls; no changes to either upstream source tree or production FineCode.

**Decision:** `PINNED_PI_VS_DOTNET_SMALL_TEXT_READ_OUTPUT=PASS` for exactly the tested cases. This is the **first true head-to-head Pi tool execution** in this experiment. It still does **not** prove the full `read` contract: truncation beyond thresholds, images, path expansion, cancellation, virtual operations, tool-result envelope and agent-loop integration remain untested or unimplemented. Similarly `grep` and `find` parity remain not implemented. No core migration recommendation.

## Grep → find direct gate (evaluation scope)

The new `scripts/compare_pi_grep_find_live.mjs` explicitly executes **grep first, find second**, using the pinned upstream Pi implementations (`createGrepToolDefinition` and `createFindToolDefinition`) and the Native AOT probe on the same runner. The bounded C# `grep-subset` currently handles a **single file, literal case-sensitive searches, no context, no regex or limit**. The `find-subset` currently handles **immediate files in one directory, basename glob, no gitignore processing or recursive traversal**. Fixtures intentionally avoid multiple matching files for find, so ordering claims are not implied. Comparison uses exact outputs and fails CI on any mismatch.

These are *experimental narrow subsets*. Success must never be reported as complete Pi `grep`/`find` parity, since default Pi tools implement `rg`/`fd` search, gitignore semantics, path globs, context, limits, cancellation, and more. Native AOT file traversal is **not a secure isolated filesystem executor**.

## Direct pinned Pi grep → find comparison — PASS

[GitHub Actions run #39008597458](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/39008597458) completed **3/3 matrix jobs PASS** on Linux x64, Linux ARM64 and Windows x64. Each job built the exact pinned Pi TypeScript tools and .NET 9 Native AOT independently, then invoked the **actual Pi `grep` tool before the actual Pi `find` tool** with the same fixtures as the bounded C# counterparts.

| Tool / narrow feature | Linux x64 | Linux ARM64 | Windows x64 | Total |
| --- | ---: | ---: | ---: | ---: |
| `grep`: single-file case-sensitive literal searches, match/nonmatch | 4/4 | 4/4 | 4/4 | 12/12 |
| `find`: top-level basename glob, single-match/nonmatch fixtures | 3/3 | 3/3 | 3/3 | 9/9 |
| **Total** | **7/7** | **7/7** | **7/7** | **21/21** |

The harness compares successful tool text output **byte-for-byte after UTF-8 decoding**, and stores case-level expected and observed output, exit code and status in artifacts `live-pi-grep-find-linux-x64`, `live-pi-grep-find-linux-arm64`, and `live-pi-grep-find-win-x64`. This is a deliberately bounded direct comparison, **not complete Pi tool compatibility**. The C# implementation currently lacks regex, recursive traversal, gitignore behavior, glob path semantics, context, cancellation, output truncation, large files and extension integration. No claim of equivalent agent loops or lower total agent cost follows. FineCode main and the pinned Pi source have not been changed.

## Expanded direct parity and deliberate negative control — 2026-10-17

**Positive functional gate:** [run #39031505878](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/39031505878) passed **39/39** head-to-head Pi-versus-C# comparisons across Windows x64, Linux x64, Linux ARM64 (8 `grep` + 5 `find` per runner). New tested behavior includes basic regex anchors/classes/alternation and case-insensitive literal search for a single text file, plus recursive basename-glob discovery with an unambiguous matching file. These *specific cases* match actual pinned Pi output, not a Python simulation. The C# implementation uses .NET Regex with a timeout; it is not a ripgrep parser or full Pi implementation.

**Negative control / known incompatibility:** [run #39031770927](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/39031770927) separately reran **39/39 positive cases PASS** and demonstrated an **expected, material difference on all three platforms**: in a temporary Git repository with `.gitignore` matching `*.tmp`, the original Pi `find` returned `No files found matching pattern`, but the bounded C# `find-subset` returned `ignored.tmp`. This difference is intentionally included as `knownGaps[].expectedDivergence=true` in each JSON artifact, and the test fails if the characterization unexpectedly changes. The three known divergences **are not counted as parity passes**.

| Runner | Positive grep | Positive find | .gitignore negative control |
| --- | ---: | ---: | --- |
| Linux x64 | 8/8 PASS | 5/5 PASS | DIFFERENT (expected) |
| Linux ARM64 | 8/8 PASS | 5/5 PASS | DIFFERENT (expected) |
| Windows x64 | 8/8 PASS | 5/5 PASS | DIFFERENT (expected) |

**Decision:** `BOUNDED_LITERAL_REGEX_GREP=PASS`, `BOUNDED_RECURSIVE_BASENAME_FIND=PASS`, `FIND_GITIGNORE_COMPATIBILITY=FAIL/NOT_IMPLEMENTED`; overall `FULL_PI_GREP_FIND_PARITY=NOT_PROVEN`. No direct performance ranking or FineCode core migration justified. Implementing full gitignore handling, symlink traversal, path-aware globs, streaming, cancellation, output limits and tool-envelope equivalence requires separate source-based and executable tests.

## Reusing Pi's actual fd executable from C# Native AOT — verified gate

[GitHub Actions #39040655085](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/39040655085): 3/3 jobs **PASS** on Linux x64, Linux ARM64 and Windows x64. The identical pinned Pi tool was executed against the same fixtures as two experimental C# strategies:

1. `find-subset` is independently implemented in C# with recursive file enumeration, and is intentionally **not** gitignore-aware.
2. `find-fd-subset` is a **C# Native AOT wrapper around the same `fd` executable resolved by Pi's `ensureTool("fd")`**. It passes Pi-aligned flags and formats returned file paths. This creates an **external fd binary dependency**, rather than implementing fd/gitignore logic in C#.

| Measured contract / runner | Linux x64 | Linux ARM64 | Windows x64 |
| --- | ---: | ---: | ---: |
| Previous bounded `grep` positive tests | 8/8 | 8/8 | 8/8 |
| Independently implemented `find-subset` positives | 5/5 | 5/5 | 5/5 |
| New fd-delegated `find-fd-subset` comparisons | 4/4 | 4/4 | 4/4 |
| Native `find-subset` gitignore divergence | observed | observed | observed |

Across all targets: **39 existing positive tests PASS + 12 fd-delegation comparisons PASS**, and **three intentionally observed native gitignore mismatches remain**. The delegated fd test includes an ignored `*.tmp` file inside an initialized Git repo, a git repository case without glob matches, and recursive basename glob fixtures. The positive comparisons are output-identical to the pinned Pi results, and the native mismatch is separately asserted rather than hidden or counted as compatible. Each runner uploads case-level `live-pi-grep-find-<rid>` JSON evidence.

**Engineering decision:** a lightweight C# launcher can reuse the same optimized `fd` search backend as Pi on all three runner classes. This removes the *observed gitignore mismatch in the delegated branch only* while preserving the independent C# implementation as a known incomplete exploratory variant. It **does not** prove complete `find` semantics (all complex glob behaviors, nested ignore exceptions, symlinks, cancellation, result limits, streaming) or agent parity, and does not justify changing FineCode's TypeScript core. No automatic merge and no modification to main FineCode.

## Resource-bounded fd delegation — follow-on gate (2026-10-17)

The experimental `find-fd-subset` accepts an **optional result limit (1–1000)** and **child execution timeout (1–60000 ms)**, while keeping the Pi-aligned default limit of 1000. A delegated `fd` subprocess now drains stdout/stderr concurrently to avoid pipe deadlock; when the deadline expires the wrapper requests termination of its child process tree and returns error code 124. These are *wrapper-level resource controls*, not Pi's `AbortSignal` integration or isolation, and code presence does not independently validate the timeout branch.

The same-run Pi comparison now includes:
- `src/*.cs` path-containing glob, using the pinned Pi `find` tool on the same fixture
- a single-match `limit=1` case with Pi's original continuation notice
- an ignored `*.tmp` fixture with explicit `limit=1`
- three separate fail-closed argument checks (limit 0, limit greater than 1000, and timeout 0) that are **not** counted as Pi parity

The native `find-subset` .gitignore discrepancy is still a separately asserted known gap. The fd-delegated branch still requires an external executable and has no complete agent cancellation contract, sandboxing, deterministic memory budget, or guaranteed parity on every glob/ignore edge case. The timeout-and-kill branch itself requires a deterministic slow-child test before declaring `TIMEOUT_CANCEL=PASS`.

Reproducible matrix workflow: `.github/workflows/pi-dotnet-grep-find-live.yml`; implementation `candidates/dotnet-aot/Program.cs`; head-to-head harness `scripts/compare_pi_grep_find_live.mjs`.

### Verified direct matrix result — PASS

[Run #39042649278](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/39042649278) completed **3/3 jobs PASS**: Windows x64, Linux x64, Linux ARM64. On **each** runner the tested cases were: 8/8 existing single-file grep, 5/5 native recursive find, **7/7 fd-delegated find** (including three new path-glob/explicit-limit cases), and **3/3 separate argument-safety assertions**. Totals: **60 successful Pi-versus-C# positive comparisons** (20 per runner), **9 successful guard checks** (3 per runner), plus the **three independently observed native .gitignore known divergences** (not counted as parity). No unexpected mismatch. Three case-level JSON artifacts are published in the workflow.

The timeout branch is **implemented but not directly exercised by a deterministic slow-child fixture**; consequently cancellation/timeout semantics and actual resource-use budgets remain **NOT VERIFIED**. The guard checks verify rejection of invalid resource arguments, not runtime termination, full isolation, or memory limits. This is a probe/harness result and must not drive a FineCode core replacement.
