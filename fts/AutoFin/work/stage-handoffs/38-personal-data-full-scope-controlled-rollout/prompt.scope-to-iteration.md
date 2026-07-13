# Следующий этап: immutable recovery rollout

Продолжай `ft-test-case-iteration` для scope `application-card-client-personal-data`.

## Goal

Подтвердить исправленный numeric seed order новым full-scope writer/reviewer cycle, не изменяя FT-first baseline.

## Inputs

- `fts/AutoFin/work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-clarification-requests.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-parity-check.md`
- `fts/AutoFin/work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-row-inventory.md`
- `fts/AutoFin/work/stage-handoffs/38-personal-data-full-scope-controlled-rollout/workflow-state.yaml`
- `fts/AutoFin/work/stage-handoffs/38-personal-data-full-scope-controlled-rollout/compiler-inputs/application-card-client-personal-data/compiler-input.yaml`
- остальные файлы из `fts/AutoFin/work/stage-handoffs/38-personal-data-full-scope-controlled-rollout/compiler-inputs/application-card-client-personal-data/`
- `fts/AutoFin/work/stage-handoffs/38-personal-data-full-scope-controlled-rollout/live-blocker-report.md`
- `fts/AutoFin/work/stage-handoffs/38-personal-data-full-scope-controlled-rollout/stop-gate.md`
- `fts/AutoFin/work/review-cycles/application-card-client-personal-data-shadow-v1-20260713/cycle-state.yaml` и blocked draft — только как regression evidence
- код не старее commit `1efc0d2`

## Steps

1. Не переиспользуй `application-card-client-personal-data-shadow-v1-20260713` и его package/attempt paths.
2. Создай новый immutable cycle, например `application-card-client-personal-data-shadow-v2-<date>`, и новый package id `application-card-client-personal-data-v2` из уже готовых compiler inputs. Не запускай новый generic input-preparation agent.
3. Убедись, что package mappings остаются: 42 atoms, 65 obligations, 47 TC, `GAP-001..003`, `DICT-001`.
4. До live проверь generated seed: заголовки должны быть точной последовательностью `TC-ACPD-001..047`.
5. Выполни validate-only. Требования: prepared-standard structured route, context <= 131 072, target absent, production boundary pass.
6. Выполни ровно один dispatcher live с `backend=auto`, exec selected, без SDK fallback, promotion и overwrite.
7. При любом новом реальном blocker остановись и сохрани immutable evidence.

## Acceptance Criteria

- Writer structure gate: pass.
- Obligation gate: 65/65.
- Quality bundle: pass.
- Semantic overlap: clean.
- Reviewer: `accepted`.
- Final artifact: not promoted.

## Guardrails

- Не изменять production test cases.
- Не использовать blocked V1 draft как requirement evidence.
- Не продолжать V1 cycle и не удалять его artifacts.
- Не повторять дорогостоящую смысловую сборку compiler inputs, если их digest/mappings не изменились.
