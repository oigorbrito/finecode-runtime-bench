# Comparative token benchmark: isolation and evidence gate

Verified external methodology: [nmlemus/harness-token-efficiency](https://github.com/nmlemus/harness-token-efficiency), README and `scripts/run_trial.py`. The author reports 19 Terminal-Bench tasks × 3 replicates × 3 harnesses, but documents local skill/plugin contamination even in Pi.

## Mandatory controls for Pi v1.3.0 / Pi-Bolt / FineCode
- Run each variant with `--no-skills --no-extensions --no-prompt-templates --no-context-files` **only after confirming those flags exist in that variant's CLI**. Otherwise report an unsupported isolation flag rather than silently changing the protocol.
- Use a clean temporary HOME/config directory, identical working tree and explicit model parameters. Capture `--help` output and hash each executable. Do not relocate or edit the user's real home/config.
- Verify every provider request, including retries and compaction, is accounted for. A session-only parser is not sufficient evidence of full billing coverage.
- Do not equate runtime speed improvements with token savings. Pi-Bolt AOT release provenance must be verified separately.
- Use the same task fixture and held-out test for every variant, randomized order and repeated runs.

## Observed CI evidence
- Commit `260506c`, Windows run 39077767314: SUCCESS, including synthetic session-to-token aggregation; **no real model tokens measured**.
- Same commit, candidate smoke run 39077767265: Python x64 and ARM64 fail with `ModuleNotFoundError: No module named 'pi_agent.harness.env'`; Rust x64 fails one update/downgrade test (501 passed, 1 failed). These are unrelated to the Windows token collector.
- Real token efficiency comparison remains NOT MEASURED until controlled model execution with provider usage evidence.
