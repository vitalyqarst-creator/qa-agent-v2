# Canary quality scorecard before broader test-case writing

## Purpose

Зафиксировать единую шкалу оценки canary-прогонов перед расширением написания тест-кейсов. Шкала привязана к основной цели: тест-кейсы должны максимально покрывать функциональные требования, оставаться проходимыми вручную и быть понятными исполнителю.

Этот scorecard является eval-протоколом, а не runtime-инструкцией writer/reviewer. Он используется для сравнения canary и pilot scopes после terminal validation.

## Scoring Rubric

| criterion | max | pass threshold | scoring rule |
| --- | ---: | ---: | --- |
| Functional coverage | 30 | 25 | Atomic statements/source rows covered by executable TC or explicit `GAP-*` / `unclear`; no fake executable coverage for undefined behavior. |
| Traceability and source fidelity | 20 | 17 | TC, ledger, design plan, coverage metrics and reviewer matrix consistently point to source refs/atoms/requirement codes. |
| Manual passability | 20 | 16 | Steps, preconditions, data and expected result can be executed manually without hidden backend assumptions or invented UI mechanisms. |
| Clarity and atomarity | 15 | 12 | TC are readable, narrowly scoped, grouped only for repeated same-action checks, and avoid generic/source-dump expected results. |
| Evidence hygiene and runner reliability | 15 | 12 | Terminal validator gate is clean for active scope; scoped profile is current; no stale lock/runtime/encoding issue affects evidence. |

Overall verdict rules:

| verdict | rule |
| --- | --- |
| `pass` | total score >= 85, no criterion below threshold, terminal `valid=true`, no unwaived blocking findings. |
| `conditional-pass` | total score >= 80, terminal `valid=true`, no unwaived blockers, but at least one criterion is below threshold or has material operational risk. |
| `fail` | total score < 80, terminal invalid, or unresolved semantic blocker remains. |

Readiness rules:

| readiness | rule |
| --- | --- |
| `limited-pilot-ready` | At least 3 canaries across different scope shapes are `pass` or better, and systemic runner/encoding blockers are guarded by tests. |
| `controlled-batch-ready` | Limited pilot on 2-3 real scopes is complete, at least 2 scopes score `pass`, no new systemic blocker appears, and manual review confirms passability. |
| `full-scale-ready` | Controlled batch is complete, score distribution is stable, and failure handling/retry protocol is documented. |

## Migrated Canary Scores

| canary | scope shape | terminal validation | coverage signal | coverage | traceability | passability | clarity | evidence | total | verdict |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `history-editing-fresh-canary-v2` | table/history behavior | `valid=true`; blockers `0`; scoped findings `0` | `12/12` atoms, `10` TC, no unresolved unclear | 30 | 20 | 19 | 14 | 11 | 94 | `pass` |
| `application-card-common-actions-flow-canary-v2` | action/dialog/status flow | `valid=true`; blockers `0`; scoped findings effectively nonblocking | `6/7` atoms covered, `1` explicit unclear `GAP-002` | 26 | 19 | 18 | 14 | 9 | 86 | `pass` |
| `document-print-form-tags-fresh-canary-v2` | document/tag table generation | `valid=true`; blockers `0`; scoped findings `2` nonblocking | `52/52` atoms, `16` TC, `2` explicit unclear gaps | 29 | 19 | 17 | 14 | 9 | 88 | `pass` |

## Evidence Notes

- `history-editing-fresh-canary-v2` is the cleanest quality signal: full atomic coverage, no scoped findings and no residual semantic uncertainty. Evidence score is reduced because the outer shell wait hit a long timeout even though the runner completed successfully.
- `application-card-common-actions-flow-canary-v2` is a positive signal for action/dialog/status flows. Coverage score is intentionally below perfect because one source-backed behavior remains `unclear:GAP-002`, which is correct but still limits executable coverage.
- `document-print-form-tags-fresh-canary-v2` is a positive signal for document-generation/table scopes. Coverage and traceability are strong; evidence score is reduced for stale-lock recoveries during the run and the reviewer-artifact encoding risk discovered after the run. The encoding risk is now guarded by `active-text-artifact-encoding-damage`.

## Decision

Current status: `limited-pilot-ready`.

Do not treat this as `full-scale-ready`. The canaries show that quality can be high across three scope shapes, but the next proof must be a limited pilot on real user-relevant scopes, using the same scorecard after terminal validation.

Mandatory gates for the next pilot:

| gate | requirement |
| --- | --- |
| terminal validation | `python scripts/codex_review_cycle_runner.py validate --state <cycle-state.yaml>` returns `valid=true`; `blocking_unwaived_count=0`. |
| semantic review | final semantic/regression review has no open warning/error findings. |
| gap discipline | every unresolved source ambiguity is a narrow `GAP-*` / `unclear`, not an executable TC. |
| encoding hygiene | no `active-text-artifact-encoding-damage` finding in active canonical TC, test-design artifacts, cycle outputs or session logs. |
| manual sampling | at least one human review pass checks TC executability and clarity before increasing batch size. |
