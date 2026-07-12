# UI Validation Report

## Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-calculator-summary-entrypoints` |
| run_date | `2026-07-12` |
| closeout_date | `2026-07-12` |
| normal_ui_path | `yes` |
| final_status | `ui-prep-blocked` |
| evidence_publication | `local-restricted-not-published` |

## Итоговый Статус

Первое боевое испытание завершено со статусом `ui-prep-blocked`.

UI-прогон состоялся и дал проверяемые локальные наблюдения, но фазу нельзя завершить: два кейса заблокированы по observability, два выявили FT/UI divergence, а безопасная воспроизводимая fixture отсутствует. Screenshots/snapshots/traces содержат персональные, application или session-sensitive данные и остаются локальными; их непубликация сама по себе больше не считается blocker при наличии безопасного evidence index.

## Статусы Тест-Кейсов

| test_case_id | ui_verification_status | primary_result | automation_readiness |
| --- | --- | --- | --- |
| `TC-ACCS-001` | `confirmed` | Calculator-summary area наблюдается через normal UI path. | `blocked-nonportable-fixture-and-restricted-evidence` |
| `TC-ACCS-002` | `blocked-observability` | Пять summary-параметров видимы, но independent calculator-stage values недоступны. | `blocked` |
| `TC-ACCS-003` | `mismatch-ft-ui` | Клик по summary не открывает calculator stage. | `blocked-product-triage` |
| `TC-ACCS-004` | `mismatch-ft-ui` | Карточный action отсутствует; одноименный list action не открывает окно. | `blocked-product-triage` |
| `TC-ACCS-005` | `blocked-observability` | Calculator window не открывается, prefill не наблюдаем. | `blocked` |

## Подтвержденное Поведение

- Авторизация и запуск `cff` выполнены normal UI path.
- Существующая локальная restricted fixture открывается из списка заявок без изменения данных.
- В карточке наблюдается calculator-summary area с пятью label/value позициями из `BSR 44`.
- DOM seeding, direct state injection и старые screenshots как самостоятельное основание статусов не использовались.

## FT/UI Divergences

### TC-ACCS-003

- FT-first baseline: `BSR 45` требует переход на этап `Кредитный калькулятор` по нажатию summary.
- Наблюдаемый UI: normal UI clicks оставляют карточку открытой без перехода.
- Решение: сохранить `mismatch-ft-ui`; baseline не изменять; UI не объявлять источником правильного бизнес-поведения.

### TC-ACCS-004

- FT-first baseline: `BSR 46` и mockup interaction hint ожидают action в карточке и открытие окна калькулятора.
- Наблюдаемый UI: карточный action не найден; одноименный action в общем списке не открыл окно или новую вкладку.
- Решение: сохранить `mismatch-ft-ui`; list action не переносить в baseline как эквивалент без решения владельца требований.

## Blockers And Limitations

- Для `TC-ACCS-002` отсутствует normal UI path к independent calculator-stage values той же fixture.
- Для `TC-ACCS-005` calculator window не открывается, поэтому prefill не наблюдаем.
- Setup profile зависит от локальной restricted fixture без переносимого safe identifier и documented create/reset path.
- Все Playwright evidence остается локальным: screenshots содержат персональные и документные данные, snapshots содержат application data, trace/network artifacts могут содержать session state, headers и payloads.
- Storage state не был сохранен; это не причина статусов кейсов, но снижает воспроизводимость повторного запуска.

## Classified Findings

| finding_id | severity | affected_tc | category | factual_observation | ft_or_baseline_reference | evidence_reference | classification_reason | required_next_action | blocking | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `UI-F-001` | `high` | `TC-ACCS-003` | `ft-ui-divergence` | Summary click не выполняет переход. | `BSR 45`; `OBL-003`; `ATOM-003` | local restricted screenshot + trace | Наблюдаемый UI прямо расходится с FT transition oracle. | Product/frontend triage; исправить entrypoint либо получить формальное изменение FT. | `yes` | `Product owner / Frontend team` |
| `UI-F-002` | `high` | `TC-ACCS-004` | `ft-ui-divergence` | Карточный action отсутствует; list action не открывает окно. | `BSR 46`; `OBL-004`; `ATOM-004`; mockup inventory | local restricted screenshots + trace | UI placement/outcome расходятся с FT-first intent; UI не может заменить FT. | Product/frontend triage; подтвердить и восстановить intended entrypoint. | `yes` | `Product owner / Frontend team` |
| `UI-F-003` | `high` | `TC-ACCS-002`, `TC-ACCS-005` | `environment-or-fixture-blocker` | Нет воспроизводимого пути к calculator stage/window и независимому prefill oracle. | `BSR 44`; `BSR 46`; `OBL-002`; `OBL-005` | local restricted trace | Нужное состояние невозможно подготовить/наблюдать доступным normal UI path. | Предоставить safe synthetic fixture и рабочий calculator entrypoint с setup/reset path. | `yes` | `Environment owner / QA data owner` |
| `UI-F-004` | `medium` | `TC-ACCS-001..005` | `evidence-portability-limitation` | Raw evidence существует локально, но содержит PII/application data или session/payload risk. | UI evidence policy | `ui-evidence-index.md` | Публикация raw artifacts небезопасна; переносимый контракт ограничен безопасным индексом со стабильными IDs. | При controlled rerun получить sanitized artifacts, если возможно; иначе сохранить restricted-local evidence и безопасный индекс. | `no` | `QA automation / Environment owner` |
| `UI-F-005` | `medium` | `TC-ACCS-001..005` | `automation-ready-test-correction` | Initial automation-ready ссылался на конкретную restricted fixture и переносил list fallback только в notes. | automation-ready lifecycle; `GAP-001` | automation-ready diff | Технические детали были непереносимы и частично делали path недетерминированным. | Выполнено в closeout: sensitive literals удалены, list action не объявлен эквивалентным path, blockers сохранены. | `no` | `QA automation` |
| `UI-F-006` | `medium` | `stage` | `process-defect` | UI session log отсутствовал; workflow ссылался на iteration session log другого stage; closeout sections и prompt отсутствовали. | session-log format; workflow-state format | handoff diff | Handoff нельзя было восстановить без истории задачи. | Выполнено в closeout: создан UI session log, обновлены decision log/workflow/prompt. | `no` | `QA agent maintainers` |
| `UI-F-007` | `medium` | `TC-ACCS-003..005` | `requirement-gap` | Полный prefill set и exact mapping отсутствуют без внешнего FT `Калькулятор`. | `GAP-001`; `BSR 46`; `ATOM-006` | baseline + scope gaps | Oracle принципиально не выводится из доступного FT; gap существовал до UI run. | BA/FT owner предоставляет external Calculator FT при необходимости полного покрытия. | `no` | `BA / FT owner` |

Findings с primary category `product-defect`: `0`. Два функциональных отклонения классифицированы ровно как `ft-ui-divergence` до продуктового triage, чтобы не объявлять наблюдаемую реализацию правильной или неправильной бизнес-нормой сверх FT-first evidence.

## Evidence Quality Assessment

- Все указанные evidence paths существуют в текущем локальном workspace.
- Timestamps относятся к одному run window `2026-07-12T03:10:56Z`–`2026-07-12T03:22:23Z`.
- `confirmed` и `mismatch-ft-ui` имеют локальные screenshots; оба mismatch имеют trace.
- Evidence получен normal UI path; DOM-seeded observations не использовались.
- Portability verdict: `restricted-local` — raw Playwright artifacts не публикуются, но их безопасный индекс переносим.
- Downstream обязан считать raw evidence `local-restricted-not-published` и использовать стабильные `evidence_id` из индекса; наличие raw artifacts в clean checkout не является closeout gate.

## Security And Publication Assessment

- Screenshots: содержат ФИО, дату рождения, паспортные, адресные, телефонные, email и application data; не публикуются.
- Snapshots: содержат те же application fields/values; не публикуются.
- Trace/network/logs: потенциально содержат cookies, session state, headers или payloads; не публикуются без отдельной sanitization pipeline.
- Credentials, runtime URL, fixture identifier и observed sensitive literals удалены из публикуемых Markdown-артефактов.
- Published evidence files: `none`.

## Baseline Integrity Proof

- Baseline: `test-cases/14-application-card-calculator-summary-entrypoints.md`.
- Git diff относительно `origin/audit/stabilize-testcase-agent-stage-contract-v2`: отсутствует.
- Canonical LF-normalized SHA-256: `bb8b90d9b5e80482a486aa186247aae6031ea2ab21cdffce66f0598b3440b571`.
- Worktree использует CRLF, поэтому raw worktree SHA отличается; после EOL normalization байты совпадают с origin.
- Присутствуют ровно `TC-ACCS-001..005`, ссылки `BSR 43–46` и `GAP-001`.
- FT-first baseline в ходе UI-prep и closeout не изменялся.

## GAP-001 Preservation

`GAP-001` сохранен в baseline, automation-ready, workflow state и findings. UI evidence не используется для утверждения полного состава prefill, exact mapping, расчетов или выбора предложений.

## First Trial Metrics

| metric | value | note |
| --- | --- | --- |
| approximate_run_duration | `11m 27s` | По timestamps первого snapshot и последнего screenshot; отдельный timer не велся. |
| manual_interventions | `not-reliably-instrumented` | Были selector fallbacks, но единая метрика run не записывалась. |
| confirmed_tc | `1` | `TC-ACCS-001` |
| mismatch_tc | `2` | `TC-ACCS-003`, `TC-ACCS-004` |
| blocked_tc | `2` | `TC-ACCS-002`, `TC-ACCS-005` |
| manual_only_tc | `0` | none |
| product_defects | `0` | Отклонения первично классифицированы как FT/UI divergences. |
| ft_ui_divergences | `2` | `UI-F-001`, `UI-F-002` |
| test_case_corrections | `1` | `UI-F-005` |
| cross_pc_transfer_issues | `2` | ignored `work/` outputs и restricted local Playwright evidence. |

## Validation Results

- Strict scoped artifact validation (`session-log-policy=audit`, `decision-log-policy=strict`, `test-case-policy=strict`): `0 errors`, `0 warnings`, `1 info` (`ui-evidence-output-paths-declared-local`, expected).
- Relevant agent-layer tests: `12 passed` (`test_ui_automation_prep_contracts`, `test_stage_handoff_contracts`, `test_ui_evidence_policy`).
- Two optional validator-unit methods could not run correctly because `tests/fixtures/agent-artifacts/ui-evidence-policy` is absent in the branch; observed result: `1 error`, `1 failure`. No validator code or architecture was changed in this task.
- Package-wide AutoFin validation still reports inherited unrelated debt: `5 errors`, `155 warnings`; active closeout paths have no error or warning.
- Active closeout errors/warnings remaining: `none`.

### Inherited Package-Wide Errors Outside This Scope

1. `work/stage-handoffs/25-prepared-obligation-rollout/prompt.scope-to-iteration.md` - missing required scope inputs.
2. `work/stage-handoffs/24-prepared-fast-standard-comparison/workflow-state.yaml` - missing ignored runtime-cycle input.
3. `work/stage-handoffs/25-prepared-obligation-rollout/workflow-state.yaml` - missing historical inputs.
4. `work/stage-handoffs/26-prepared-standard-calculator-summary/workflow-state.yaml` - missing historical inputs.
5. `work/stage-handoffs/27-calculator-summary-final-source-rebase/workflow-state.yaml` - missing historical runtime-cycle input.

Эти ошибки и package-wide warnings не относятся к candidate diff и не исправляются в closeout согласно запрету на agent-architecture work.

## Recommendations For Next Iteration

1. Подготовить synthetic calculator fixture без PII с безопасным стабильным ID и documented create/reset path.
2. Исправить или формально переопределить оба calculator entrypoint; после решения выполнить явный rerun только затронутых кейсов.
3. Добавить sanitization/export flow для screenshots и traces; не менять архитектуру агента в рамках этого closeout.
4. Добавить run metrics capture для duration и selector/manual fallbacks в будущей итерации.
5. Вернуться к `GAP-001` только после появления внешнего FT `Калькулятор`.
6. В отдельной agent-layer задаче восстановить отсутствующую fixture `tests/fixtures/agent-artifacts/ui-evidence-policy` и только затем включать два validator-unit tests в обязательный gate.

## Closeout Gate

Повторный `ft-ui-automation-prep` разрешен только после одновременного выполнения условий:

- доступна safe synthetic fixture с переносимым setup/reset path;
- calculator stage/window открывается через подтвержденный normal UI entrypoint;
- evidence можно собрать без PII, credentials, cookies, tokens и sensitive payloads;
- владелец требований подтвердил трактовку entrypoint, если реализация остается отличной от FT/mockup.
