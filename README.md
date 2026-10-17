# FineCode Runtime Bench

Independent, offline-first comparison of the upstream Pi TypeScript runtime and third-party Rust/Python ports. This is **not** the FineCode production repository.

## Design

- Sources pinned to full commits in `sources.json`; checkout verifies HEAD.
- GitHub Actions matrix: Linux x64 and ARM64.
- Start with upstream test suites, then measure `--version` startup (where an equivalent executable exists).
- No external model API or paid tokens. No changes to FineCode.
- `results/*.json` uploaded as artifacts when produced.
- A passing smoke test is not proof of full feature parity. Startup timing is not token efficiency.
- Different test suites are **not** comparable as common workloads.
- Initial workflow is experimental; failures must be classified before reporting benchmark results.

## Reproduce

Open **Actions → Offline baseline → Run workflow**. Review every matrix job and its logs. Measurements are only valid after the corresponding setup/build/test job succeeds.

## Scope and limitations

No end-to-end LLM calls, agent reliability comparison, token costs, apples-to-apples feature test, controlled CPU/RSS measurement, or Oracle VM benchmark yet. Python currently has test execution but no equivalent CLI timing.

Commits and upstreams: see `sources.json`.
