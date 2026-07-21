# Reviewer Output Format

Этот reference фиксирует, какие артефакты должен создавать `ft-test-case-reviewer`, где они должны храниться и когда reviewer может передавать набор дальше.

## Назначение

- отделить формат reviewer output от процедурных инструкций skill-а;
- сделать findings, traceability matrix и reviewer handoff воспроизводимыми;
- предотвратить неявный sign-off при оставшихся blocking проблемах;
- зафиксировать второй review как проверку актуального набора, writer response и traceability continuity.

## Review Cycle Outputs

Session-based reviewer outputs хранятся здесь:

```text
fts/<ft-slug>/work/review-cycles/<scope-slug>/outputs/
```

Stage handoff prompts хранятся в фактической numbered stage-handoff папке:

```text
fts/<ft-slug>/work/stage-handoffs/NN-<scope-slug>/
```

Prompt-файлы не заменяют findings, traceability matrix, writer response, final reviewer output или `cycle-state.yaml`.

## Findings Artifact

Каждый reviewer round должен создавать findings artifact:

```text
fts/<ft-slug>/work/review-cycles/<scope-slug>/outputs/round-N-findings.md
```

Artifact должен соответствовать `references/qa/review-findings-format.md`.

Findings сортируются по severity:

1. `error`
2. `warning`
3. `info`

Каждый finding должен иметь:

- `review_mode`;
- `severity`;
- `category`;
- `test_case_id` или `coverage_gap`;
- `traceability_ref` для findings режима `traceability`;
- `problem`;
- `evidence`;
- `required_change`;
- `source_reference`;
- `status`.

Reviewer не должен возвращать finding без проверяемого `required_change`. Если проблема не сводится к действию writer-а, фиксируй ее в human summary или как input limitation.

Для `traceability` findings `traceability_ref` должен ссылаться на `atom_id` строки matrix (`ATOM-*`) или на `coverage_gap:<short-id>`, если matrix row еще не создана. Не ссылайся только на `req_id`, потому что один код требования может распадаться на несколько атомарных утверждений.

## Traceability Matrix

В режимах `traceability` и `full` reviewer должен создавать:

```text
round-N-traceability-matrix.md
round-N-traceability-matrix.xlsx
```

Оба файла лежат в `work/review-cycles/<scope-slug>/outputs/`.

Markdown matrix является canonical text artifact. `.xlsx`-дубль обязателен и должен содержать те же строки, колонки и значения.

Matrix должна соответствовать `references/qa/traceability-matrix-format.md` и использовать:

```text
atom_id = ATOM-001, ATOM-002, ...
coverage_status = covered | gap | unclear
```

В source-first final matrix дополнительно допустим `coverage_status = not-applicable`, если строка дословно проецирует hash-bound accepted source assertion с `semantic_disposition = not-applicable`, не ссылается на `TC-*` и сохраняет source-backed rationale по `references/qa/traceability-matrix-format.md`. Этот статус не заменяет `gap` или `unclear` для тестируемого утверждения.

`gap` означает достаточную определенность требования при отсутствии покрытия.  
`unclear` означает, что требование нельзя однозначно превратить в проверку без домысливания.

Если `source-parity-check.md` обязателен для scope, reviewer должен сверить matrix с его секцией `Mandatory Traceability Inputs`. Отсутствие mandatory или PDF-only `req_id` в matrix является blocking traceability finding.

Если reviewer получает legacy matrix без `atom_id` как baseline предыдущего round, он не должен механически считать ее совместимой с новым traceability contract. В следующей создаваемой или обновляемой matrix reviewer назначает `atom_id` и фиксирует legacy-to-ATOM mapping в human summary, если это влияет на закрытие findings.

## Human Summary

Human summary может быть частью `round-N-findings.md` или отдельным разделом в начале artifact.

Минимально фиксируй:

- review mode;
- проверенные входы;
- наличие или отсутствие PDF structural cross-check;
- наличие или отсутствие source parity check, если DOCX+PDF доступны;
- summary по coverage counts;
- top blocking findings;
- residual `unclear` items;
- traceability closure по `traceability_ref` / `atom_id`: закрытые refs, оставшиеся `gap` refs, оставшиеся `unclear` refs;
- legacy matrix status, если baseline matrix была без `atom_id`;
- recommended next step.

Human summary не заменяет structured findings.

## Second Review

Во втором review reviewer обязан сверить:

- актуальный canonical test-case file;
- findings artifact предыдущего round;
- writer response artifact;
- previous traceability matrix, если она была;
- актуальную traceability matrix нового round, если выполняется `traceability` или `full`.

Reviewer не должен переоткрывать закрытый finding без нового evidence.

Если writer response artifact структурно невалиден, не содержит response на каждый finding или использует недопустимые enum-значения, reviewer фиксирует blocking `structure` / `format` finding.

Для каждого закрытого `traceability` finding reviewer должен проверить тот же `traceability_ref` в актуальной matrix: `coverage_status` больше не должен быть `gap`, а `covered_by_tc` должен ссылаться на реальные test case ids. Если writer изменил `traceability_ref`, reviewer должен принять это только при явном split/merge explanation в writer response.

## Handoff To Writer

Если остаются `error`, `warning` или нерешенные `gap`, reviewer создает:

```text
prompt.reviewer-to-writer.round-N.md
```

в stage-handoff папке текущего scope и обновляет `workflow-state.yaml`:

```yaml
stage_status: ready-for-writer-revision
next_skill: ft-test-case-writer
```

Нельзя использовать `stage_status: not-signed-off`. Это human summary verdict, а не lifecycle status. Если review не подписан и требуется writer revision, используй `ready-for-writer-revision`; если достигнут лимит раундов, используй `round-cap-reached`; если нужен внешний input, используй `blocked-input`.

`latest_artifacts` должен ссылаться на актуальные findings и traceability matrix, если она создана.

## Reviewer Sign-off Self-check

Перед созданием `prompt.reviewer-to-ui-prep.md` reviewer обязан добавить в final reviewer output явный блок:

```md
## Reviewer Sign-off Self-check

**traceability_checked:** yes|not-applicable
**source_parity_checked:** yes|not-applicable
**structure_checked:** yes
**test_case_grouping_checked:** yes
**test_case_numbering_checked:** yes
**test_design_checked:** yes
**applicability_dimensions_checked:** yes
**validator_checked:** yes
**blocking_findings_absent:** yes
**traceability_gaps_absent:** yes|not-applicable
**known_unclear_items:** none | <список допустимых unclear>
**sign_off_rationale:** <краткое объяснение, почему набор можно передать дальше>

Optional waiver heading: `## Validator Warning Waivers`; table columns: `finding_id | path | waiver_status | waiver_class | rationale | evidence`.

Allowed `waiver_class`: `false-positive`, `validator-schema-lag`, `accepted-source-gap`, `accepted-nonblocking-risk`. `accepted-source-gap` cites existing `GAP-*`; process-only status/history is invalid. `validator-schema-lag` is valid only when `rationale` explains the expected validator model vs actual artifact model, and `evidence` cites affected `PDP-*`/`PD-*`, `ATOM-*` or `TC-*` plus counter-evidence such as covered traceability, linked design rows or no open findings.
```

Правила заполнения:

- `traceability_checked` может быть `not-applicable` только если review_mode не включает `traceability` и handoff не заявляет полный review-cycle sign-off.
- `source_parity_checked` может быть `not-applicable` только если для scope нет пары DOCX+PDF или parity artifact явно не требуется.
- `structure_checked` и `test_design_checked` должны быть `yes` для sign-off после `full` review.
- `test_case_grouping_checked` должно быть `yes` только если canonical file логически сгруппирован по функциональности/блоку/элементу/операции или reviewer явно проверил, что для узкого scope отдельная группировка не нужна.
- `test_case_numbering_checked` должно быть `yes` только если `TC-*` ids в canonical file имеют сквозную нумерацию без дублей, пропусков и перезапуска внутри групп, а ссылки на измененные ids обновлены.
- `applicability_dimensions_checked` должно быть `yes` только если reviewer проверил каждую строку `Test-design applicability matrix`: все `applicable = yes` rows имеют реальное покрытие проверяемыми `TC-*` или явный `GAP-*`.
- `validator_checked` должно быть `yes` только если reviewer перед sign-off выполнил `python scripts\validate_agent_artifacts.py --root <ft-package> --json` или эквивалентный runner validator gate и отфильтровал findings текущего scope, включая canonical test-case file и split test-design artifacts.
- Reviewer must treat the full validator report as raw input, not as the scoped verdict. Current-scope validator filtering excludes historical `work/review-cycles/<scope>/versions/` snapshots, `_artifact_write/` scratch files and unrelated scopes; findings there may remain in the full report but must not block `blocking_findings_absent` unless the same finding exists in the active canonical TC file, active split test-design directory or current cycle outputs.
- `blocking_findings_absent` может быть `yes` только если нет findings с `severity = error` или `severity = warning`, включая validator warnings/errors по canonical test-case file и split test-design artifacts текущего scope. Non-blocking validator warning/error требует `Validator Warning Waivers` с `finding_id`, `path`, `waiver_status`, `waiver_class`, `rationale`, `evidence`; молчаливый `signed-off` недопустим.
- Waiver не должен быть мягче finding: `validator-schema-lag` без описания schema/model mismatch, affected refs и counter-evidence считается invalid; для semantic TC defects вроде duplicated source fields, missing `DICT-*` traceability, synthetic quote, missing cleanup, indistinct branch oracle, bundled negative input classes, missing full-valid fixture for negative transition, requiredness without empty/marker check, metadata behavior smell или metadata cross-section conflict reviewer должен требовать исправление, а не schema-lag waiver.
- `traceability_gaps_absent` может быть `yes` только если traceability matrix не содержит `coverage_status = gap`.
- `known_unclear_items` должен перечислять оставшиеся допустимые `unclear`, если они есть; `none` допустимо только при их отсутствии.
- `sign_off_rationale` должен объяснять решение reviewer-а, а не повторять слово `signed-off`.

Если reviewer не может честно заполнить этот self-check, он не должен создавать `prompt.reviewer-to-ui-prep.md`.

Узкое исключение для source-first controlled promotion: terminal producer принятого review contract v4 может заранее материализовать hash-bound prompt со статусом `pending-controlled-promotion`, если одновременно созданы и self-validated final Markdown/XLSX matrix, финальный reviewer output содержит этот self-check, а warnings и `coverage_status = gap` отсутствуют. Такой prompt не является lifecycle sign-off и прямо запрещает UI-запуск до атомарного перевода обоих state artifacts в `signed-off` controlled promotion transaction. Prompt остаётся generic и cycle-independent: scope-specific проверки берутся из canonical TC/traceability, а cycle state, findings, matrices и snapshot — из signed-off `workflow-state.yaml.latest_artifacts`, без прошитых путей конкретного cycle.

## Handoff To UI Prep

Reviewer может создать (либо активировать заранее материализованный `pending-controlled-promotion` prompt):

```text
prompt.reviewer-to-ui-prep.md
```

только если:

- нет findings с `severity = error`;
- нет findings с `severity = warning`;
- traceability matrix не содержит `coverage_status = gap`;
- оставшиеся `unclear`, если есть, явно допустимы и не блокируют выполнение ручного набора;
- `Reviewer Sign-off Self-check` заполнен и подтверждает проверку traceability, structure, grouping, сквозной нумерации, test-design, validator gate и отсутствие blocking findings;
- если DOCX+PDF доступны, `Reviewer Sign-off Self-check` подтверждает `source_parity_checked: yes`;
- `cycle-state.yaml` или связанный `workflow-state.yaml` фиксирует `signed-off`.

Для одиночного reviewer pass без orchestrator-а не выдавай полноценный `signed-off`, если проектный workflow требует `ft-test-case-iteration` для sign-off. В таком случае reviewer может рекомендовать следующий этап, но финальный lifecycle status должен фиксировать iteration.

## Round Cap

Если после финального разрешенного review round остаются `error`, `warning` или нерешенные `gap`, итоговый workflow status:

```yaml
stage_status: round-cap-reached
next_skill: none
```

Нельзя маршрутизировать `round-cap-reached` напрямую в `ft-ui-automation-prep`.

Reviewer / iteration должны сохранить unresolved work в final reviewer output или `cycle-state.yaml` в блоке:

```md
## Final Residual Risk

**remaining_blocking_findings:** none | FINDING-* ...
**remaining_traceability_gaps:** none | ATOM-* / coverage_gap:<short-id> ...
**remaining_coverage_gaps:** none | GAP-* ...
**remaining_unclear_items:** none | ATOM-* / GAP-* ...
**decision_rationale:** <почему loop завершен round-cap>
**next_action:** <что нужно сделать до следующего review/sign-off>
```

Нельзя указывать `none` для категории, по которой summary или final artifacts показывают оставшиеся `error`, `warning`, `gap`, `unclear` или `GAP-*`.

Все `FINDING-*`, `GAP-*`, `coverage_gap:*` и `ATOM-*` в `Final Residual Risk` должны ссылаться на artifacts из `latest_artifacts`: `final_findings`, `final_traceability_matrix`, `scope_coverage_gaps` или соответствующие `round-N-*`.

`remaining_blocking_findings` должен ссылаться только на open findings с `severity = error | warning`. `remaining_coverage_gaps` должен ссылаться на canonical `GAP-*` records с согласованными `Impact` и `Blocks Ready For Review`.

`ATOM-*` в `remaining_traceability_gaps` должен иметь `coverage_status = gap` в linked traceability matrix. `ATOM-*` в `remaining_unclear_items` должен иметь `coverage_status = unclear`.

## Terminal Output Copy/Fill Snippets

Reviewer или iteration должен копировать один из шаблонов ниже и заменить placeholders фактическими путями и счетчиками. Не удаляй строки про remaining risk: если риска нет, укажи `none`; если риск есть, перечисли ID.

### Signed-off final output

```md
## Loop Summary

- FT package: `<ft-slug>`
- Scope: `<scope-slug>`
- Current stage: `ft-test-case-iteration`
- Final status: `signed-off`
- Review rounds completed: `<1|2>`
- Canonical test-case file: `test-cases/<test-case-file>.md`
- Signed-off snapshot: `work/review-cycles/<scope-slug>/versions/signed-off`
- Final findings: `work/review-cycles/<scope-slug>/outputs/round-N-findings.md`
- Final traceability matrix: `work/review-cycles/<scope-slug>/outputs/round-N-traceability-matrix.md`
- Final traceability matrix xlsx: `work/review-cycles/<scope-slug>/outputs/round-N-traceability-matrix.xlsx`
- Final writer response: `none | work/review-cycles/<scope-slug>/outputs/writer-rN-response.md`

## Reviewer Pass Round N

- Findings `error`: `0`
- Findings `warning`: `0`
- Traceability `gap`: `0`
- Traceability `unclear`: `0 | <count>`
- Applicability dimensions unresolved: `0`

## Reviewer Sign-off Self-check

**traceability_checked:** yes
**source_parity_checked:** yes | not-applicable
**structure_checked:** yes
**test_case_grouping_checked:** yes
**test_case_numbering_checked:** yes
**test_design_checked:** yes
**applicability_dimensions_checked:** yes
**validator_checked:** yes
**blocking_findings_absent:** yes
**traceability_gaps_absent:** yes
**known_unclear_items:** none | <ATOM-* / GAP-* explicitly accepted as non-blocking>
**sign_off_rationale:** <why this exact set may move to UI prep>

## Gate Decision Result

Review-cycle received `signed-off`: the test-case set is ready for `ft-ui-automation-prep`.
```

### Round-cap final output

```md
## Loop Summary

- FT package: `<ft-slug>`
- Scope: `<scope-slug>`
- Current stage: `ft-test-case-iteration`
- Final status: `round-cap-reached`
- Review rounds completed: `2`
- Canonical test-case file: `test-cases/<test-case-file>.md`
- Round-cap snapshot: `work/review-cycles/<scope-slug>/versions/round-cap-reached`
- Final findings: `work/review-cycles/<scope-slug>/outputs/round-2-findings.md`
- Final traceability matrix: `work/review-cycles/<scope-slug>/outputs/round-2-traceability-matrix.md`
- Final traceability matrix xlsx: `work/review-cycles/<scope-slug>/outputs/round-2-traceability-matrix.xlsx`
- Final writer response: `work/review-cycles/<scope-slug>/outputs/writer-r2-response.md`

## Reviewer Pass Round 2

- Findings `error`: `<count>`
- Findings `warning`: `<count>`
- Traceability `gap`: `<count>`
- Traceability `unclear`: `<count>`
- Applicability dimensions unresolved: `<count>`

## Final Residual Risk

**remaining_blocking_findings:** none | FINDING-* ...
**remaining_traceability_gaps:** none | ATOM-* / coverage_gap:<short-id> ...
**remaining_coverage_gaps:** none | GAP-* ...
**remaining_unclear_items:** none | ATOM-* / GAP-* ...
**decision_rationale:** <why loop stopped at round cap instead of sign-off>
**next_action:** <what must happen before another review/sign-off>

## Gate Decision Result

Review-cycle stopped at `round-cap-reached`: unresolved work remains and the workflow must not route to UI automation prep.
```
