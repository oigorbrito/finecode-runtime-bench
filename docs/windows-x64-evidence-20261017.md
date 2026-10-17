# Windows x64 independent candidate results (17 October 2026)

## Experimental design

Windows Server 2025 x64 GitHub runner. Official source pinned in `sources.json`. Independent `pi_ts`, `pi_rust`, `pi_go` jobs, so an upstream test failure in one candidate does not prevent another candidate from running. Upstream candidate files are never patched. Release builds/CLI calls are separately executed after failed tests, while the final official-test gate remains FAIL.

## Evidence

- Initial combined run [38998268602](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/38998268602): TypeScript 43 tests PASS, 1 fails (`spawnSync npm ENOENT`). Rust/Go not reached.
- Combined rerun [38998501446](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/38998501446): Rust CLI library 503 PASS, 1 FAIL, 2 ignored (`path_validation_resolves_ancestor_links_but_refuses_a_link_leaf`). Go not reached.
- Independent run [38999210665](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/38999210665): Go upstream `go test ./...` identifies 4 failing coding-package tests:
  - `TestFindGlobalCoreExcludesFile`
  - `TestGrepNodeModulesNotHardIgnored`
  - `TestGrepGlobAnchoring`
  - `TestLoadSkillsPreservesDiscoveryOrder`
  Their error messages involve backslash path rendering, glob behavior and skills discovery. Do not claim root cause is proved.
- Final independent build-and-test run [38999329945](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/38999329945):
  - Go native `go build -o pi-bench.exe ./cmd/pi` **PASS**; `--help` contract capture **PASS**; official tests **FAIL**.
  - Pi TypeScript `npm run build:offline` **PASS**; `--help` contract capture **PASS**; official script suite **FAIL** (`spawnSync npm ENOENT`).
  - Rust official tests **FAIL**: 503 PASS, 1 FAIL, 2 ignored in rpi-cli, same path/symlink test as previous run. The GitHub step conclusion looked green only because `continue-on-error` was set; the raw log and `steps.official_rust.outcome` confirm FAIL. Rust release build **PASS** and CLI help capture **PASS**. The final test-gate script itself also had a PowerShell interpolation error (`$candidate:`), corrected in commit `db64b32`.

## Engineering assessment

CLI build/run success does not establish functional parity. Windows currently has upstream test compatibility gaps for TS and Go and a Rust test that did not reliably reproduce. The benchmark harness must not patch or skip those official tests. The FineCode main repository and candidate source trees remain untouched. No automatic merge.

## Rust path-alias evidence (source-level diagnosis)

At pinned `pi_rust` SHA, `crates/rpi-cli/src/updates.rs:2643` asserts that the error message contains `real_file.display().to_string()`. The observed error for the linked-file fixture contains `C:\\Users\\runneradmin\\...\\real-file.exe`, whereas the fixture path uses `C:\\Users\\RUNNER~1\\...\\real-file.exe`. This is a Windows short-name (8.3) versus long-name string mismatch. Importantly the diagnostic states the leaf is **a link or junction**, therefore it is not evidence that the symlink leaf was accepted. The full official test gate still fails. No source modification or assertion removal is warranted in this benchmark.

Do not mistake a green `continue-on-error` *step conclusion* for passing tests: read the explicit `steps.official_rust.outcome` and raw test logs.

## Controlled diagnosis of Go user skill on Windows — confirmed

Run [39001216399](https://github.com/oigorbrito/finecode-runtime-bench/actions/runs/39001216399), Windows Go job:

1. Unmodified official `go test ./...`: **FAIL**, with four known `coding` tests failing.
2. Unmodified isolated `go test ./coding -run TestLoadSkillsPreservesDiscoveryOrder -count=1 -v`: **FAIL**, user skill not found.
3. Diagnostic `go test -overlay ... ./coding -run TestLoadSkillsPreservesDiscoveryOrder -count=1 -v`, virtual fixture copy containing `t.Setenv("USERPROFILE", home)` immediately after `t.Setenv("HOME", home)`: **PASS**.

This controlled A/B supports a Windows-specific test fixture environment mismatch, not a fix to the Go port, and resolves **only the diagnostic hypothesis**. The upstream test gate intentionally stays FAIL. TypeScript official scripts still fail `spawnSync npm ENOENT`. Rust official `rpi-cli` suite again fails its path-alias assertion (503 passed, 1 failed, 2 ignored), while native builds and help checks pass. No source files of the candidate repositories are edited.
