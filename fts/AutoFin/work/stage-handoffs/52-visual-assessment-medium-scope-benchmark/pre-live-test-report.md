# Visual Assessment Medium-Scope Benchmark — Pre-Live Test Report

## Результат

`PASS — live запрещён до checkpoint push и отдельной authorization`

## Scope И Package

- Scope: полный current-source блок `Визуальная информация` и Appendix 1.
- Current anchors: `BSR 311`-`BSR 317`, XHTML rows 182-184, PDF pp.34/40-41.
- Package: `visual-assessment-medium-scope-benchmark-v1`, version `6`.
- Package digest: `ffb7a7a8a44bd8ee53b76b6f8745fa0c8653eabbdfa7ef20bb0166c592be8d35`.
- Atomic-obligation SHA-256: `209fd75663b86f9c5a5da7dcbc51599dc70c1e1d64948b471262121b17ce8086`.
- Route: `standard-required`; unsupported dimensions: `dependency-state`, `evidence-qualified-ui-calibration`.
- Size: `13` obligations, `12` unique planned TC, `9` dictionary rows, `0` active gaps.
- Единственная grouping: `OBL-003` и `OBL-004` -> `TC-VAMB-003`; compiler подтвердил общий plan row и явный `grouping-justification`.
- Requiredness: `SO-REQ-001` и `SO-REQ-002` остаются `ui-calibration-required` / `candidate-ui-calibration`; точная UI-реакция не утверждается.

## Source Identity

- DOCX SHA-256: `c6892bfa57599f29fda84035c8ecd19e9ed5257cf88771bd52e910817a5af75b`.
- XHTML SHA-256: `cbf7ce8eca806f9f132c6bec26a8577eb544106a87cb79c46ace24e1b3d00a66`.
- PDF SHA-256: `8caee78cdf87fe27deb2ffa64b57791768c958703f249b8c85518283aeb8da58`.

## Validate-Only

- Runtime identity: pass; version/id/digest exactly match immutable package.
- Writer: structured, read-only, effective command budget `0`, LLM required `true`.
- Writer context: `49,375 / 131,072` bytes, pass.
- Writer output capacity: `12` TC / `13` obligations, one session, limit `12`, pass.
- Observable-oracle preflight: `13` checked, `0` findings, pass.
- Reviewer output capacity: `13 / 100` obligations, pass.
- Target absent; validate-only created no cycle attempts.

## Backend Dry-Run

- Backend requested/selected: `exec` / `exec`.
- Contract version: `2`.
- Capability: available and verified; missing flags: none.
- SDK fallback: `false`.

## Tests

- Full exec runner suite: `105 passed`.
- Prepared package/compiler/obligation, backend and architecture group: `134 passed`.
- Prepared reviewer/evidence/migration group: `28 passed`.
- Targeted candidate-oracle deferral regression: `1 passed`.
- Full artifact-validator file: `389 passed`, `2 failed` only because tracked repository has no `tests/fixtures/agent-artifacts/ui-evidence-policy/` directory. Both failures reproduce missing-fixture infrastructure debt; neither reaches changed validator logic.
- Strict H52 artifact validation: `0 errors`, `0 warnings`, `3` source-quality info findings.

## Production Boundary

- Existing visual-assessment baseline SHA-256: `3761f32df5babc77c22acb765ba0cb97925a7183dfcb81f1afc0c3be1ce577dc`.
- Protected personal-data baseline SHA-256: `98a3e7b4b28ab1b0f83a2b83706cdc9c8f785aba775712fad3746695585368fc`.
- Protected section 4.2 baseline SHA-256: `cbc46e9b8d44c8e7c19b887a6a2f59f64d096e6275d2bd45f521132dd133c8a3`.
- Promotion target `section-18-visual-assessment-medium-scope-benchmark.md`: absent.

## Benchmark Targets

- Exactly one fresh structured writer and one fresh semantic reviewer through one dispatcher invocation.
- No retry, resume, rebind, repair, assisted mode, sharding, SDK fallback or promotion.
- Target duration: `< 120 s` total.
- Target uncached input efficiency: `< 8,000 tokens / obligation`.
- Comparison baseline V4: `66,562 ms`, `43,535` total tokens, `41,458` uncached input tokens, `4` obligations, `10,364.5` uncached tokens / obligation.

## Stop Conditions

- Any package identity, context/output capacity, oracle, transport, deterministic, semantic, evidence-access or production-boundary blocker is terminal for this run.
- The two absent fixture tests are pre-existing infrastructure debt; any new failure in a benchmark-critical suite is blocking.
