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
  - Rust official tests **PASS in this run**, after path/symlink failure in previous run; release build/result must be checked separately before claiming runtime success.

## Engineering assessment

CLI build/run success does not establish functional parity. Windows currently has upstream test compatibility gaps for TS and Go and a Rust test that did not reliably reproduce. The benchmark harness must not patch or skip those official tests. The FineCode main repository and candidate source trees remain untouched. No automatic merge.
