# Workflow State Format

Канонический `workflow-state.yaml` фиксирует межэтапный статус FT pipeline и служит единственным источником process-status между `ft-source-locator`, `ft-scope-analyzer`, writer/reviewer loop и `ft-ui-automation-prep`.

## Назначение

- хранить текущий этап по конкретному `scope-slug`;
- явно показывать, какой skill должен запускаться следующим;
- фиксировать gate status и обязательные входы следующего этапа;
- давать handoff без необходимости восстанавливать контекст из истории чата.

## Расположение

- `fts/<ft-slug>/work/stage-handoffs/NN-<scope-slug>/workflow-state.yaml` для новых handoff-папок

Для одного `scope-slug` должен существовать один актуальный `workflow-state.yaml`.

Для новых handoff-папок фактический путь должен использовать numbered directory из `stage-handoff-model.md`:

```text
fts/<ft-slug>/work/stage-handoffs/NN-<scope-slug>/workflow-state.yaml
```

При этом поле `scope_slug` остается без числового префикса.

## Обязательные поля

- `ft_slug`
- `scope_slug`
- `current_stage`
- `stage_status`
- `current_round`
- `next_skill`
- `required_inputs`
- `latest_artifacts`
- `open_questions`
- `blocking_reasons`

## Допустимые значения

- `current_stage` = `ft-source-locator | ft-scope-analyzer | ft-test-case-writer | ft-test-case-reviewer | ft-test-case-iteration | ft-ui-automation-prep`
- `stage_status` = `ready-for-next-stage | ready-for-gap-review | ready-for-review | ready-for-writer-revision | signed-off | round-cap-reached | blocked-input`
- `next_skill` = `ft-source-locator | ft-scope-analyzer | ft-test-case-writer | ft-test-case-reviewer | ft-test-case-iteration | ft-ui-automation-prep | none`
- `current_round` — целое число, где `0` допустим для pre-writer handoff

## Правила полей

- `required_inputs` — список файлов, без которых следующий этап не должен стартовать.
- `latest_artifacts` — map с относительными путями к последним актуальным артефактам handoff и session-based review-cycle.
- Для `ft-source-locator`, `ft-scope-analyzer`, `ft-test-case-writer`, `ft-test-case-reviewer` и `ft-test-case-iteration` `latest_artifacts` должен ссылаться на актуальный `*session-log*.md` по `references/agent/session-log-format.md`.
- Для стадий, где агент принимает source/scope/writer/reviewer/routing решения, `latest_artifacts.decision_log` должен ссылаться на `agent-decision-log.md` по `references/agent/agent-decision-log-format.md`. Этот artifact фиксирует промежуточные решения и их rationale; `workflow-state.yaml` остается единственным источником process-status.
- Session log должен соответствовать текущему stage. Ссылка на лог другого stage не считается корректным handoff даже если файл существует. Примеры: `ft-source-locator` должен ссылаться на `source-locator-session-log.md` или лог с `skill = ft-source-locator`; writer должен ссылаться на `writer-session-log.md` или лог с `skill = ft-test-case-writer`.
- Если stage handoff лежит в numbered-папке, все stage-handoff пути в `latest_artifacts` должны указывать именно на `work/stage-handoffs/NN-<scope-slug>/...`.
- Если для подтвержденного scope доступны DOCX и PDF основного ФТ, `latest_artifacts.source_parity_check` должен указывать на `source-parity-check.md`, а writer/reviewer/iteration должны видеть этот artifact в `required_inputs`.
- Если `source-parity-check.md` содержит row-level/table parity или scope основан на таблице полей/действий, `latest_artifacts.source_row_inventory` должен указывать на `source-row-inventory.md`, а writer/reviewer/iteration должны видеть этот artifact в `required_inputs`.
- Если для подтвержденного UI scope доступен mockup, `latest_artifacts.mockup_visual_inventory` должен указывать на `mockup-visual-inventory.md`, а writer/reviewer/iteration должны видеть этот artifact в `required_inputs`.
- V3 workflow связывает `latest_artifacts.source_assertions` и accepted exact-digest `source_assertion_review`; оба входят в compiler `required_inputs`.
- Для writer outputs `latest_artifacts.test_design_dir` должен указывать на `work/test-design/<section-id>-<scope-slug>/`, а `latest_artifacts.canonical_test_cases` - на slim canonical file в `test-cases/`.
- Для `current_stage: ft-scope-analyzer`, `stage_status: ready-for-gap-review` и `next_skill: ft-test-case-reviewer` handoff обязан ссылаться на `source-selection.md`, `scope-contract.md`, `scope-coverage-gaps.md`, `scope-clarification-requests.md` и `prompt.scope-gaps-to-reviewer.md`. Этот переход используется только до writer и только для review найденных scope gaps.
- Для `current_stage: ft-scope-analyzer`, `stage_status: ready-for-next-stage` и `next_skill: ft-test-case-writer | ft-test-case-iteration` handoff обязан ссылаться на `source-selection.md`, `scope-contract.md`, `scope-coverage-gaps.md` и соответствующий prompt (`prompt.scope-to-writer.md` или `prompt.scope-to-iteration.md`).
- V3 pre-writer review: `ready-for-next-stage` → reviewer с `prompt.scope-assertions-to-reviewer.md`; accepted идёт к writer/iteration, иначе обратно к scope analyzer.
- Если `scope-coverage-gaps.md` содержит хотя бы один `GAP-*`, handoff обязан ссылаться на `scope-clarification-requests.md`. Даже non-blocking gap должен быть передан downstream явно, а не только упомянут в summary.
- Для session-based review-cycle итогов `latest_artifacts` должен содержать canonical aliases: `cycle_state`, `final_findings`, `final_traceability_matrix`, `final_traceability_matrix_xlsx`, `final_writer_response` если была revision, and `signed_off_snapshot` или `round_cap_snapshot`.
- `open_questions` — список еще не снятых неоднозначностей по scope или coverage.
- `blocking_reasons` — список причин, почему этап нельзя продвигать дальше.
- `accepted_risks` — необязательный список явно принятых blocking `GAP-*`, если владелец продукта/аналитик разрешил передать набор дальше без закрытия gap.

## Blocking Gap Gate

Если `coverage_gaps.blocking > 0` или связанный `scope-coverage-gaps.md` содержит `Есть blocking gaps: yes`, workflow нельзя переводить в `stage_status: ready-for-review`.

Допустимые варианты:

- `stage_status: blocked-input` и заполненный `blocking_reasons`;
- устранить blocking gaps и обновить `coverage_gaps.blocking: 0`;
- добавить явное accepted-risk решение в `accepted_risks`, если владелец продукта/аналитик осознанно разрешил deferred review.

Формат `accepted_risks`:

```yaml
accepted_risks:
  - GAP-001 | accepted-risk | owner: <name/role> | rationale: <why review may proceed> | revisit: <condition/date>
```

Accepted-risk не превращает gap в покрытое требование. Reviewer обязан видеть такой gap как residual risk, а downstream handoff не должен скрывать его в summary.

## Writer Quality Gate

Для `current_stage: ft-test-case-writer` и `stage_status: ready-for-review` writer output должен содержать split artifact `work/test-design/<scope-slug>/writer-quality-gate.md` с `Writer Quality Gate`.

`ready-for-review` допустим только если:

- `latest_artifacts` или `required_inputs` указывают на canonical test-case file;
- в split artifact `writer-quality-gate.md` есть секция `Writer Quality Gate`;
- для большого или package-based scope есть split artifact `artifact-write-strategy.md` с `scripts/write_artifact_sections.py --manifest <manifest.json>` preflight;
- если scope содержит mockup, в workflow-state есть resolving `mockup-visual-inventory.md`, а `writer-quality-gate.md` содержит gate row `mockup-visual-inventory`;
- все строки gate с `blocks_ready_for_review = yes` имеют `status = pass`;
- нет строк gate со `status = fail`, `blocked` или `needs-rewrite`, которые требуют переписать package.
- если workflow ссылается на handoff `source-row-inventory.md`, split artifact `work/test-design/<scope-slug>/source-row-inventory.md` содержит writer-side inventory со всеми in-scope/unclear `source_row_id` из handoff inventory.
- canonical test-case file и split test-design artifacts не содержат известных blocking quality smells: generic executable steps, generic expected results, merged valid/invalid checks, `Type: Positive` с rejection oracle, requiredness без empty/marker проверки, boundary rejection без exact-boundary acceptance, compressed/combined atoms, combined design-plan rows, source-row loss или unobservable action/internal behavior.

Даже если `Writer Quality Gate` формально заполнен как `pass`, workflow `ready-for-review` должен блокироваться, если validator находит такие дефекты в canonical test-case file или split test-design artifacts. Canonical finding: `workflow-state-ready-for-review-with-blocking-test-case-smells`.

Если gate failed, workflow должен оставаться вне review:

```yaml
stage_status: blocked-input
next_skill: ft-test-case-writer
blocking_reasons:
  - Writer Quality Gate failed for WP-02: compressed atoms / broad scenario rows.
```

Failed gate нельзя принять как `accepted_risk`: это дефект качества writer draft, а не осознанный продуктовый residual risk.

## Session Log

Для стадий `ft-source-locator`, `ft-scope-analyzer`, `ft-test-case-writer`, `ft-test-case-reviewer` и `ft-test-case-iteration` создавай persistent session log в текущей stage-handoff папке и связывай его из `latest_artifacts`.

Session log фиксирует audit trail решений, а не полный transcript команд. Минимум: `Inputs Read`, `Inputs Not Used`, `Key Decisions`, `Risks And Fallbacks`, `Validation`, `Contamination Check`.

Для clean eval и diagnostic runs добавляй audit-секции `Event Timeline`, `Quality Checkpoints`, `Technical Fallbacks`, `Handoff Notes For Next Session`, чтобы следующая сессия могла понять не только итог, но и ход решений. Любой command/patch/context/encoding fallback должен быть раскрыт в `Technical Fallbacks` как структурированная строка `TF-*`.

Пример:

```yaml
latest_artifacts:
  session_log: work/stage-handoffs/NN-<scope-slug>/writer-session-log.md
```

Для обычных новых eval/scope runs проверяй strict mode:

```powershell
python scripts\validate_agent_artifacts.py --root <ft-package> --json --fail-on warning --session-log-policy strict
```

Для diagnostic runs используй audit mode:

```powershell
python scripts\validate_agent_artifacts.py --root <ft-package> --json --fail-on warning --session-log-policy audit
```

## Reviewer-Loop Traceability Closure

Для `stage_status: signed-off` и `stage_status: round-cap-reached` state должен позволять восстановить итоговую трассировку без чтения истории чата:

- `latest_artifacts.final_traceability_matrix` указывает на последнюю matrix, по которой принято решение;
- `latest_artifacts.final_traceability_matrix_xlsx` указывает на XLSX-дубль той же matrix;
- `latest_artifacts.final_findings` указывает на findings последнего review round;
- `latest_artifacts.final_writer_response` указывает на writer response, если sign-off или round cap наступили после revision;
- `latest_artifacts.loop_summary` указывает на summary, где перечислены remaining `gap` / `unclear` refs через `traceability_ref` / `atom_id`.

Для новых `signed-off` и `round-cap-reached` handoff states отсутствие этих aliases считается дефектом handoff. Проверяй новые итоговые state в strict mode:

```powershell
python scripts\validate_agent_artifacts.py --root . --json --fail-on warning --final-alias-policy strict
```

Если итоговая matrix является legacy baseline без `atom_id`, это должно быть явно указано в final reviewer output; новый или обновленный reviewer round обязан создать matrix с `atom_id`.

## Рекомендуемый шаблон

```yaml
ft_slug: <ft-slug>
scope_slug: <scope-slug>
current_stage: ft-scope-analyzer
stage_status: ready-for-next-stage
current_round: 0
next_skill: ft-test-case-writer
required_inputs:
  - scope-contract.md
  - source-parity-check.md
  - source-row-inventory.md
  - scope-coverage-gaps.md
  - prompt.scope-to-writer.md
latest_artifacts:
  source_selection: work/stage-handoffs/01-2.1.1.1.1.1.2-lichnaya-informaciya/source-selection.md
  scope_contract: work/stage-handoffs/01-2.1.1.1.1.1.2-lichnaya-informaciya/scope-contract.md
  source_parity_check: work/stage-handoffs/01-2.1.1.1.1.1.2-lichnaya-informaciya/source-parity-check.md
  source_row_inventory: work/stage-handoffs/01-2.1.1.1.1.1.2-lichnaya-informaciya/source-row-inventory.md
  cycle_state: work/review-cycles/2.1.1.1.1.1.2-lichnaya-informaciya/cycle-state.yaml
  final_findings: work/review-cycles/2.1.1.1.1.1.2-lichnaya-informaciya/outputs/round-2-findings.md
  final_traceability_matrix: work/review-cycles/2.1.1.1.1.1.2-lichnaya-informaciya/outputs/round-2-traceability-matrix.md
  final_traceability_matrix_xlsx: work/review-cycles/2.1.1.1.1.1.2-lichnaya-informaciya/outputs/round-2-traceability-matrix.xlsx
open_questions: []
blocking_reasons: []
```

## Reviewer-loop final state snippets

Для `signed-off` и `round-cap-reached` не собирай `workflow-state.yaml` по памяти. Скопируй один из блоков ниже, замени placeholders и проверь, что все пути в `required_inputs` и `latest_artifacts` реально существуют.

### signed-off -> UI prep

```yaml
ft_slug: <ft-slug>
scope_slug: <scope-slug>
current_stage: ft-test-case-iteration
stage_status: signed-off
current_round: <1|2>
next_skill: ft-ui-automation-prep
required_inputs:
  - work/review-cycles/<scope-slug>/cycle-state.yaml
  - work/review-cycles/<scope-slug>/versions/signed-off/snapshot-manifest.yaml
  - work/stage-handoffs/NN-<scope-slug>/prompt.reviewer-to-ui-prep.md
latest_artifacts:
  canonical_test_cases: test-cases/<test-case-file>.md
  cycle_state: work/review-cycles/<scope-slug>/cycle-state.yaml
  final_findings: work/review-cycles/<scope-slug>/outputs/round-N-findings.md
  final_traceability_matrix: work/review-cycles/<scope-slug>/outputs/round-N-traceability-matrix.md
  final_traceability_matrix_xlsx: work/review-cycles/<scope-slug>/outputs/round-N-traceability-matrix.xlsx
  final_writer_response: none | work/review-cycles/<scope-slug>/outputs/writer-rN-response.md
  signed_off_snapshot: work/review-cycles/<scope-slug>/versions/signed-off
  prompt_reviewer_to_ui_prep: work/stage-handoffs/NN-<scope-slug>/prompt.reviewer-to-ui-prep.md
coverage_gaps:
  blocking: 0
  non_blocking: 0
open_questions: []
blocking_reasons: []
accepted_risks: []
```

### round-cap-reached -> stop

```yaml
ft_slug: <ft-slug>
scope_slug: <scope-slug>
current_stage: ft-test-case-iteration
stage_status: round-cap-reached
current_round: 2
next_skill: none
required_inputs:
  - work/review-cycles/<scope-slug>/cycle-state.yaml
  - work/review-cycles/<scope-slug>/versions/round-cap-reached/snapshot-manifest.yaml
latest_artifacts:
  canonical_test_cases: test-cases/<test-case-file>.md
  cycle_state: work/review-cycles/<scope-slug>/cycle-state.yaml
  final_findings: work/review-cycles/<scope-slug>/outputs/round-2-findings.md
  final_traceability_matrix: work/review-cycles/<scope-slug>/outputs/round-2-traceability-matrix.md
  final_traceability_matrix_xlsx: work/review-cycles/<scope-slug>/outputs/round-2-traceability-matrix.xlsx
  final_writer_response: work/review-cycles/<scope-slug>/outputs/writer-r2-response.md
  round_cap_snapshot: work/review-cycles/<scope-slug>/versions/round-cap-reached
coverage_gaps:
  blocking: <count>
  non_blocking: <count>
open_questions:
  - <question or []>
blocking_reasons:
  - <FINDING-* / GAP-* / ATOM-* reason that blocks sign-off>
accepted_risks: []
```

## Правила использования

- `workflow-state.yaml` фиксирует только process-status и не заменяет содержательные артефакты этапа.
- Следующий skill не должен стартовать, если в `required_inputs` отсутствует хотя бы один обязательный файл.
- После каждого handoff обновляй `current_stage`, `stage_status`, `next_skill`, `required_inputs` и `latest_artifacts`.
- Если `scope-coverage-gaps.md` содержит хотя бы один `GAP-*`, добавляй `scope-clarification-requests.md` в `latest_artifacts`; добавляй его в `required_inputs`, когда следующий этап должен учитывать открытые или подтвержденные ответы по gaps.
- Если этап заблокирован, используй `stage_status = blocked-input` и явно заполняй `blocking_reasons`.
- Статус `signed-off` используется только для завершенного review-cycle и handoff в `ft-ui-automation-prep`.
- Не используй `stage_status: not-signed-off`: это итоговая оценка review, но не process-status. При blocker findings выбирай `ready-for-writer-revision`, при лимите раундов `round-cap-reached`, при нехватке внешнего input `blocked-input`.

## Transition contract

- `stage_status: ready-for-next-stage` обязан иметь конкретный `next_skill`; `next_skill: null` допустим только для завершенных/заблокированных состояний без автоматического downstream handoff.
- `stage_status: round-cap-reached` не должен маршрутизировать следующий этап: `next_skill` должен быть `null` или `none`.
- Если `next_skill: ft-ui-automation-prep`, handoff обязан ссылаться на активный `prompt.reviewer-to-ui-prep.md` в `required_inputs` или `latest_artifacts`.
- `ft-ui-automation-prep` может стартовать только от signed-off baseline: `cycle-state.yaml` или совместимый `workflow-state.yaml` должны фиксировать `signed-off`.
- Если следующий этап writer revision, активный handoff prompt должен быть `prompt.reviewer-to-writer.round-N.md`.
- Если `scope_gap_review` завершился с verdict `passed` и следующий этап writer, активный handoff prompt должен быть `prompt.scope-to-writer.md` и должен ссылаться на `scope-gap-review.md`.
- Accepted `source_assertion_review` связывает receipt с тем же manifest digest и заменяет gap review.
- Если следующий этап reviewer, активный handoff prompt должен быть `prompt.writer-to-reviewer.round-N.md`.
- Если следующий этап reviewer для pre-writer gap review после scope analysis, активный handoff prompt должен быть `prompt.scope-gaps-to-reviewer.md`.
- V3 source-model reviewer использует `prompt.scope-assertions-to-reviewer.md`.
- Если `latest_artifacts.active_transition_prompt` задан, именно он считается активным handoff prompt и имеет приоритет над выводом имени по `current_round`.
- `active_transition_prompt` обязан существовать и соответствовать направлению перехода: `writer-to-reviewer`, `reviewer-to-writer`, `reviewer-to-ui-prep`, `scope-gaps-to-reviewer`, `scope-assertions-to-reviewer`, `scope-to-writer` или `scope-to-iteration`.
- Не оставляй рядом stale prompt того же направления, например старый `prompt.writer-to-reviewer.round-N.md`, если активный переход уже указывает на специальный prompt. Такой alias может увести следующую сессию в устаревший handoff.
