# Evidence: token capture source and Windows gate

- Pi upstream v1.3.0 supports `pi --mode json` in `packages/coding-agent/src/modes/print-mode.ts`; its session core emits `message_end` for assistant messages and persists their `usage`.
- `packages/ai/src/types.ts` defines `Usage.input`, `output`, `cacheRead`, `cacheWrite`, optional `reasoning`, `totalTokens`, and costs. Reasoning is included within output and MUST NOT be added to output a second time.
- Windows Actions run 39077767314 completed the `Validate token usage accounting (no paid API)` step successfully. This is an **instrumentation gate**, not an actual provider-token comparison.
- Real task runs require provider credentials and a spending ceiling. No paid calls are authorized by this gate; do not pretend synthetic tokens represent real consumption.
- The benchmark must separately capture agent event streams, distinguish error/retry/compaction requests, and reconcile usage totals with provider billing before declaring cost savings.
- `scripts/pi_session_usage.py` parses persisted assistant usage offline and strips message contents. It is not yet proof that every billed provider request is captured, particularly retries and summarization calls.
- Do not publish raw session JSONL as a GitHub artifact: sessions may contain user prompts, secrets or source code.
