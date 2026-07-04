# Limited pilot manual sampling

## Purpose

Проверить после terminal validation, что pilot test cases не только валидатор-clean, но и пригодны для ручного выполнения: понятные предусловия, тестовые данные, шаги, итоговый ожидаемый результат и трассировка.

## Sampled Scopes

| scope | canonical file | TC count | structural runtime check |
| --- | --- | ---: | --- |
| `main-info-credit-parameters` | `fts/ft-2-OF_17/test-cases/2-1-1-1-1-1-2-main-info-credit-parameters.md` | 16 | `0` TC missing `Предусловия`, `Тестовые данные`, `Шаги`, `Итоговый ожидаемый результат`, `Постусловия`; every TC has numbered steps. |
| `common-application-fields` | `fts/ft-2-OF_17/test-cases/section-34-common-application-fields.md` | 22 | `0` TC missing runtime sections; every TC has numbered steps. |
| `document-print-form-tags` | `fts/ft-2-OF_17/test-cases/2-1-1-1-1-4-4-document-print-form-tags.md` | 12 | `0` TC missing runtime sections; every TC has numbered steps. |

## Manual Sample

| scope | sampled TC | check result |
| --- | --- | --- |
| `main-info-credit-parameters` | `TC-MICP-003`, `TC-MICP-013`, `TC-MICP-016` | Pass. Samples cover numeric positive input, conditional availability by product, and catalog max boundary. Preconditions/test data are explicit, residual `GAP-*` references are visible, and expected results stay observable without inventing negative validation feedback. |
| `common-application-fields` | `TC-CAF-001`, `TC-CAF-010`, `TC-CAF-022` | Pass. Samples cover non-display and non-editability checks. The final-format remediation restored full template fields (`Цель`, `Ссылка на ФТ`, source fields) and did not change semantic steps or expected results. |
| `document-print-form-tags` | `TC-DPFT-001`, `TC-DPFT-006`, `TC-DPFT-012` | Pass. Samples cover generated document creation, address block mapping, and loan amount tag substitution. Steps refer to a concrete fixture and expected results are observable in the generated document. |

## Caveats

- This was a manual sampling pass, not exhaustive human execution of all 50 TC in a live UI/document-generation environment.
- The pilot is retrospective over existing signed-off scopes after remediation. It is stronger than pure canary evidence, but weaker than a newly generated live pilot.
- `scoped_findings_count` remains nonzero for the three scopes, but `blocking_unwaived_count=0` in terminal validation. The remaining scoped findings are accepted nonblocking findings under current runner gate, not batch blockers.

## Decision

Current status: `controlled-batch-prep-ready`.

Allowed next step: run a small controlled batch, not full unsupervised generation.

Batch guardrails:

| guardrail | requirement |
| --- | --- |
| batch size | Start with `2-3` new scopes only. |
| terminal gate | Every scope must end with `codex_review_cycle_runner.py validate --state <cycle-state.yaml>` returning `valid=true` and `blocking_unwaived_count=0`. |
| scorecard | Score each scope with `evals/canary-quality-scorecard-2026-06-24.md`. |
| manual sampling | Manually sample at least `2` TC per scope before increasing batch size. |
| failure handling | Any current-scope warning/error without a narrow waiver stops the batch and becomes a remediation item. |
