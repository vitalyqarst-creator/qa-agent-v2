# Codex exec prepared reviewer fast path

This stage is read-only. Do not modify any workspace file.
Review only the verified package, draft and deterministic validator report listed below.
- `fts/AutoFin/work/review-cycles/codex-exec-prepared-live-canary-v2-20260710/prepared-input/autofin-widget-selection-prepared-v2/stage-package.json`
- `fts/AutoFin/work/review-cycles/codex-exec-prepared-live-canary-v2-20260710/prepared-input/autofin-widget-selection-prepared-v2/source-evidence.md`
- `fts/AutoFin/work/review-cycles/codex-exec-prepared-live-canary-v2-20260710/prepared-input/autofin-widget-selection-prepared-v2/atomic-obligations.json`
- `fts/AutoFin/work/review-cycles/codex-exec-prepared-live-canary-v2-20260710/prepared-input/autofin-widget-selection-prepared-v2/stage-instructions.md`
- writer draft: `fts/AutoFin/work/review-cycles/codex-exec-prepared-live-canary-v2-20260710/attempts/writer-r1/attempt-001/stage-output/draft.md`
- validator: `fts/AutoFin/work/review-cycles/codex-exec-prepared-live-canary-v2-20260710/attempts/writer-r1/attempt-001/runner-output/validator.json`
- obligation gate: `fts/AutoFin/work/review-cycles/codex-exec-prepared-live-canary-v2-20260710/attempts/writer-r1/attempt-001/runner-output/obligation-gate.json`
- seed gate: `fts/AutoFin/work/review-cycles/codex-exec-prepared-live-canary-v2-20260710/attempts/writer-r1/attempt-001/runner-output/seed-gate.json`
- evidence access gate: `fts/AutoFin/work/review-cycles/codex-exec-prepared-live-canary-v2-20260710/attempts/writer-r1/attempt-001/runner-output/evidence-access-report.json`
- response schema: `fts/AutoFin/work/review-cycles/codex-exec-prepared-live-canary-v2-20260710/attempts/reviewer-r1/attempt-001/review-contract.schema.json`

Return one JSON object in the final message and write no files:
{"decision":"accepted|changes-required","findings_markdown":"# Review findings\n..."}
Use `accepted` only when every testable ATOM is correctly covered and no blocking finding remains.
