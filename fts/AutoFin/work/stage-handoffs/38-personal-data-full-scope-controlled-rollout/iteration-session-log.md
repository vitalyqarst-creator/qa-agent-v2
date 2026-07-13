# FT Test Case Iteration Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-iteration` |
| mode | `prepared-standard-full-scope-controlled-rollout` |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-client-personal-data` |
| status_after | `ready-for-next-stage` |

## Inputs Read

- `skills/ft-test-case-iteration/SKILL.md` — lifecycle, exec separation и stop rules.
- `AGENT-NOTES.md` — package-specific AutoFin context.
- Handoff 29 scope/source/parity/design artifacts — confirmed source-backed scope.
- Handoff 37 accepted canary evidence — eligibility baseline.
- Prior unsigned full-scope draft и findings — только regression evidence для SEM-001/SEM-002.
- Handoff 38 compiler inputs и mapping report — canonical inputs текущей итерации.

## Inputs Not Used

- Production test-case files не читались как requirement evidence и не изменялись.
- Blocked V1 draft не использовался для изменения compiler inputs; он проверялся только как runtime output.
- SDK diagnostics и соседние FT packages не использовались.

## Key Decisions

- Production test cases и blocked draft не использовались как requirement evidence.
- Input mappings исправлены до компиляции; exact-set consistency стала executable gate.
- Context duplication устранено до live, потому что preflight сначала корректно остановил oversized writer prompt.
- Выполнен один live writer; reviewer не запускался после deterministic blocker.
- Current cycle сохранён immutable; следующий прогон требует нового cycle identity.

## Risks And Fallbacks

- Post-fix writer/reviewer live ещё не выполнен; это обязательный acceptance gate следующей итерации.
- `GAP-001..003` остаются non-blocking calibration/evidence risks.
- Input-preparation exec остаётся главным performance debt из-за 2.306M input tokens.
- Все технические fallback подробно перечислены ниже; ни один не изменил production artifacts.

## Validation

- Compiler/migration tests: 44 pass.
- Target runner/compiler tests before live: 116 pass.
- Target runner/compiler tests after seed fix: 117 pass.
- Agent layer fast: 419 pass, 1 skip.
- Architecture: 61 checks, 0 findings.
- Validate-only: pass, 96 886 / 131 072 bytes.
- Live: `blocked-validator`, writer 233.375 s, 50 517 tokens.
- Offline blocked-draft obligation gate: 65/65, 47 TC, 0 findings.
- Offline quality bundle and semantic overlap: pass / clean.
- Post-fix real-package seed: contiguous `001..047`.

## Contamination Check

- `fts/AutoFin/test-cases/14-prepared-shadow-application-card-client-personal-data.md`: absent.
- FT-first production files: unchanged.
- User-owned `fts/AutoFin/test-cases/4.3-application-card-client-addresses-contacts.md`: untouched and untracked.
- User-owned `evals/sdk-turn-diagnostics/**`: untouched and untracked.
- Writer session: read-only, 0 commands, 0 file changes.

## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | helper | status |
| --- | --- | --- | --- | --- |
| `compiler-inputs/application-card-client-personal-data/` | bounded multi-file | separate exec input-preparation session | `codex exec` | written |
| `work/review-cycles/application-card-client-personal-data-shadow-v1-20260713/prepared-input/` | bounded compiler output | deterministic compiler | `compile_prepared_stage_package.py` | written |
| `work/review-cycles/application-card-client-personal-data-shadow-v1-20260713/attempts/` | immutable runtime output | exec runner | `codex_exec_review_cycle_runner.py` | written |
| handoff 38 reports | small structured | `apply_patch` | n/a | written |

## Event Timeline

| step | event | result |
| --- | --- | --- |
| 1 | SEM audit | `ATOM-025` omission and decision-table offsets confirmed |
| 2 | Compiler-input preparation | 42 atoms, 65 obligations, 47 TC; mappings equal |
| 3 | Package compilation | Evidence budget initially blocked; projection compacted; package built |
| 4 | First validate-only | Blocked at 157 908-byte writer context |
| 5 | Structured transport compaction | Context reduced to 96 886 bytes; validate-only pass |
| 6 | Controlled live | Writer draft materialized; structure validator blocked TC order |
| 7 | Offline gate analysis | 65/65 obligations and quality checks pass; order is sole deterministic blocker |
| 8 | Seed-order remediation | Numeric sorting added; real-package seed `001..047`; no second live |

## Technical Fallbacks And Incidents

| id | trigger | response | retained risk / follow-up |
| --- | --- | --- | --- |
| `TF-001` | `pytest` unavailable in runtime | Used canonical `unittest` suites through project runner | none |
| `TF-002` | Input-prep sandbox first decoded Russian output incorrectly | Re-read sources explicitly as UTF-8 | no production contamination |
| `TF-003` | Sandbox git reported dubious ownership | Used read-only safe-directory override inside child session | no repository mutation from override |
| `TF-004` | Raw evidence 50 570 > 49 152 bytes | Compacted obligation lines and deduplicated plan evidence | covered by tests |
| `TF-005` | Writer context 157 908 > 131 072 bytes | Removed redundant full obligations payload from structured writer | full artifact retained for gates/reviewer |
| `TF-006` | GitHub port 443 timeout on first push attempt | Preserve local commits and retry at handoff completion | push status must be verified |
| `TF-007` | Live seed order mismatched validator contract | Stop cycle; fix numeric seed sorting; require new immutable recovery cycle | post-fix live pending |

## Performance Debt

Generic input preparation consumed 2.306M input tokens. This dominates the optimized live writer path and must not become the normal production route. Prefer deterministic consolidation from already normalized design artifacts.
