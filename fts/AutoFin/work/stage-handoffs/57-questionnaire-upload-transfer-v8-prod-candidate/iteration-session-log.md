# FT Test Case Iteration Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-iteration` |
| mode | `prod-candidate-canary` |
| ft_slug | `AutoFin` |
| scope_slug | `questionnaire-upload-transfer-v8-prod-candidate` |
| started_from | `workflow-state.yaml` |
| status_after | `signed-off` |

## Inputs Read

- `workflow-state.yaml` — канонический межэтапный статус и пути входов.
- `prompt.scope-to-iteration.md` — ограничения canary и terminal gate.
- `scope-gap-review.md` — независимый допуск scope к writer/reviewer iteration.
- `compiler-inputs/questionnaire-upload-transfer-v8-prod-candidate/*` — входы immutable package.
- `references/agent/prepared-stage-package-format.md` — package, route и completion gates.
- `references/agent/session-based-review-cycle-format.md` — разделение writer/reviewer и правила promotion.

## Inputs Not Used

- `test-cases/16-questionnaire-upload-transfer-v6.md` и любые V6/V7 drafts — не использовались как evidence требований.
- Пользовательские untracked `PostFinal-v2`, mockups, support и `4.3-application-card-client-addresses-contacts.md` — вне подтверждённого scope и не изменялись.

## Key Decisions

- Использован `standard-required` structured route: file-upload, input-boundaries, negative-oracle и visibility не допускают fast route.
- Подготовлен один immutable package для ровно 9 planned TC; package повторно проверен через `--reuse-if-current`.
- SDK fallback, retry, resume, автоматический promotion и ручная правка draft запрещены.
- Бюджет canary ограничен 120 секундами writer и 60 секундами reviewer; итоговый performance gate отдельно проверяет общий лимит 180 секунд и 75 000 tokens.

## Risks And Fallbacks

- `GAP-QUT-001` остаётся open-non-blocking: точная byte-граница 40 МБ не определена source-backed convention и не должна превращаться в исполнимый TC.
- Предыдущий независимый scope review занял около четырёх минут и 171 411 tokens; это performance debt pre-writer review, а не скрытый успех.
- Если live transport, deterministic gate, reviewer verdict или performance gate не пройдёт, цикл останавливается без retry и promotion.

## Validation

- `compile_prepared_stage_package.py` — `built`, 11 obligations, 1 gap, `standard-required`.
- Повторная компиляция с `--reuse-if-current` — `reused`; drift не обнаружен.
- SHA-256 `stage-package.json`: `f752f0488aa1917ac579ac27fbb3e830e41549d672ab882f08b01790caf49892`.
- Live cycle — `accepted-not-promoted`; 9 TC, 10/10 testable obligations, 1 preserved gap, 0 blocking findings.
- Performance — 95 391 ms stage time, 49 505 tokens, budgets passed.
- Targeted regression — `631 passed`; full regression — `1021 passed, 1 skipped`.
- Architecture audit — 61 checks, 0 findings/warnings/errors.
- Canonical post-hoc promotion readiness check — `passed`; write not performed.
- Controlled promotion — `passed`; candidate и production target побайтно совпадают, SHA-256 `30737645afe53d3535db78c005968225b495e63a11ec201edeed2db107e2080b`.
- Final traceability companion — 11 obligations: 10 `covered`, 1 `unclear` с сохранённым `GAP-QUT-001`; XLSX проверен через `openpyxl` и одностраничный LibreOffice render.
- MD/XLSX parity — `passed`; 11 строк и 7 колонок побуквенно совпадают после удаления Markdown backticks.
- Signed-off snapshot — candidate, production target и snapshot copy: 9893 bytes, одинаковый SHA-256.
- Scoped strict artifact validation — 0 errors, 0 warnings; остаются 3 informational source-extraction diagnostics, уже учтённые source parity/inventory.
- Terminal lifecycle validator — 5 heuristic/schema warnings классифицированы и закрыты structured waivers; production test cases не изменялись.

## Contamination Check

- Production target `test-cases/16-questionnaire-upload-transfer-v8-prod-candidate.md` отсутствовал до canary и создан только после явного разрешения владельца.
- Canonical FT-first baselines и пользовательские untracked файлы не использованы как write targets.
- Единственный production write — новый V8 target; остальные test-case baseline-файлы не изменялись.

## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| `test-cases/16-questionnaire-upload-transfer-v8-prod-candidate.md` | `small canonical promotion` | `apply_patch exact candidate content; then SHA-256 equality check` | `yes` | `apply_patch` | `yes` |
| `work/review-cycles/questionnaire-upload-transfer-v8-prod-candidate-20260714/versions/signed-off/**` | `small snapshot evidence` | `apply_patch manifest and receipt after canonical hash verification` | `yes` | `apply_patch` | `yes` |
| `work/review-cycles/questionnaire-upload-transfer-v8-prod-candidate-20260714/outputs/final-traceability-matrix.xlsx` | `small spreadsheet companion` | `openpyxl workbook generated from the reviewed final matrix, then rendered with LibreOffice` | `yes` | `tmp/spreadsheets/build_qut_traceability.py` | `yes` |

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Получен независимый scope-gap verdict | `passed`; 10 testable obligations, 1 gap, 9 planned TC | `scope-gap-review.md` |
| 2 | Скомпилирован immutable package | `built`; package version 8; standard-required | `prepared-input/questionnaire-upload-transfer-v8-prod-candidate-r1/stage-package.json` |
| 3 | Проверена воспроизводимость package | `reused`; тот же fingerprint и binding | compiler stdout; package hash |
| 4 | Создан iteration audit log | Live ещё не запускался | `iteration-session-log.md` |
| 5 | Выполнен exec-only canary | Writer `draft-ready`, reviewer `accepted`, session IDs различаются | `cycle-state.yaml`; `live-result.v8.json` |
| 6 | Выполнен manual quality gate | 9 уникальных TC; gap и literal fidelity сохранены | `manual-quality-gate.v8.md` |
| 7 | Проверена promotion readiness | Destination отсутствует; candidate hash совпадает; write не выполнен | `promotion-readiness.v8.json` |
| 8 | Исправлена production audit telemetry | Session IDs сохраняются без benchmark scans | `review_cycle_backend_dispatcher.py`; unit test |
| 9 | Выполнены regression и architecture gates | 1021 passed, 1 skipped; 61 architecture checks, 0 findings | test stdout; `architecture-audit.v8.md` |
| 10 | Получено явное разрешение владельца | Controlled promotion разрешён; writer/reviewer не перезапускаются | user approval; `agent-decision-log.iteration.md` |
| 11 | Первая byte-level проверка publication остановила promotion | Текст совпадает, но `apply_patch` создал LF вместо CRLF candidate; status не изменён | candidate/target hashes; byte diagnostic |
| 12 | Первый XLSX render выявил горизонтальное разбиение | Данные корректны; print layout возвращён на доработку до signed-off | rendered spreadsheet pages |
| 13 | Выполнена byte-identical публикация | Candidate и target: 9893 bytes, одинаковый SHA-256; overwrite не выполнялся | `promotion-receipt.v8.json` |
| 14 | Проверен повторный XLSX render | Все 7 столбцов и 11 obligations читаемы на одной странице | temporary rendered PNG; workbook validation |
| 15 | Сформированы финальные алиасы и handoff | `signed-off`; следующий skill — `ft-ui-automation-prep` | cycle/workflow states; signed-off snapshot; UI prompt |
| 16 | Нормализован финальный traceability status | Внутренний `gap-preserved` заменён каноническим `unclear`; `covered_by_tc` указывает `unclear:GAP-QUT-001` | final matrix MD/XLSX |
| 17 | Выполнены terminal validations | Hash equality, MD/XLSX parity, cycle-state и strict handoff validator пройдены | validator stdout; snapshot manifest |
| 18 | Проверен terminal current-scope gate | Пять warnings оказались двумя schema-contract collisions и тремя heuristic false/schema mismatches; добавлены evidence-backed waivers | `outputs/final-findings.md`; terminal validator gate |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Scope gap review | pass | `scope-gap-review.md` | Сохранить `GAP-QUT-001` |
| Prepared package fidelity | pass | package compiler и source hashes | Проверить deterministic gates после writer |
| Writer/reviewer live | pass | `live-result.v8.json` | none |
| Manual quality gate | pass | `manual-quality-gate.v8.md` | none |
| Promotion readiness | pass | `promotion-readiness.v8.json` | Требуется явное разрешение до write |
| Promotion | pass | `promotion-receipt.v8.json`; одинаковый SHA-256 | Не перезапускать writer/reviewer |
| Final traceability | pass | MD + XLSX; 10 covered, 1 unclear | Сохранить `GAP-QUT-001` |
| Signed-off handoff | pass | snapshot manifest; `prompt.reviewer-to-ui-prep.md` | Продолжить отдельным UI этапом |
| Terminal validator waivers | pass | пять structured waiver rows; runner-owned gate | Не менять byte-identical V8 для обхода heuristic findings |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | PowerShell pipeline передал BOM в одноразовый JSON summarizer при предыдущей scoped validation | Piped JSON parse | Повторный validator с `PYTHONIOENCODING=utf-8` и прямым stdout; релевантные source artifacts перечитаны через `Get-Content -Encoding UTF8` | `n/a` | `no` | `none`; distorted stdout был отброшен и не использовался как evidence для анализа или трассировки | Использовать явный UTF-8 и file-based JSON при последующих сводках |
| `TF-002` | Runner validate-only отклонил нулевой command budget standard writer | `--writer-command-budget 0` | Установлен минимально допустимый budget `1`; structured prompt по-прежнему не требует команд | `dispatcher-config.v8.json` | `yes` | `low`; фактическое число команд проверяется post-run | Блокировать canary, если writer использует команду без targeted fallback |
| `TF-003` | Первый targeted pytest вызов содержал отсутствующий test-файл | `tests/test_compile_prepared_stage_package.py` | Через `rg --files tests` выбраны фактические test modules | `n/a` | `no` | `none`; тесты в ошибочном вызове не запускались | Использовать repository test names |
| `TF-004` | Первый вызов architecture audit использовал неверный путь в `scripts/` | `scripts/audit_agent_architecture.py` | Применён skill-owned helper `skills/agent-architecture-auditor/scripts/audit_agent_architecture.py` | `architecture-audit.v8.md` | `yes` | `none`; ошибочный вызов ничего не изменил | Сохранять skill-owned canonical path |
| `TF-005` | Byte-level promotion gate обнаружил различие line endings при совпадающем тексте | `apply_patch` создал canonical target с LF, тогда как immutable candidate использует CRLF | Выполнить только механическую конверсию LF→CRLF без изменения Unicode text, затем повторить SHA-256 и `git diff --no-index` | `test-cases/16-questionnaire-upload-transfer-v8-prod-candidate.md` | `yes` | `none` при совпадении итогового SHA; первый target hash отклонён и не использован как promotion evidence | Не менять workflow status до exact hash equality |
| `TF-006` | LibreOffice render разнёс семь XLSX-столбцов по трём горизонтальным страницам | Default portrait print settings | Landscape A3, fit-to-width, narrow margins; повторный render через temporary helper | `tmp/spreadsheets/build_qut_traceability.py`; `tmp/spreadsheets/rendered-v2/` | `no` | `none`; workbook rows/statuses не изменялись | Визуально подтвердить читаемость всех столбцов |
| `TF-007` | Poppler сообщил `nameToUnicode` warnings для кириллического install path при PNG render | Default font-name mapping diagnostic | Использовать PNG только для layout; содержимое workbook перечитать через `openpyxl`, а текстовые артефакты — через explicit UTF-8 `Get-Content -Encoding UTF8` | temporary render output | `no` | `none`; искажённый console output не использован как evidence анализа или трассировки | Не трактовать renderer warning как source evidence |
| `TF-008` | Первый MD/XLSX diagnostic получил пустой Markdown row set | Literal Markdown backtick в PowerShell inline condition был интерпретирован shell | Заменить условие на ASCII-only `TR-QUT-` и удалять backticks внутри Python через `chr(96)` | `n/a` | `no` | `none`; неуспешное сравнение не использовалось как evidence | Принимать parity только после успешного equality assertion |
| `TF-009` | Первый финальный render вызвал `pdftoppm` до появления LibreOffice PDF | Headless LibreOffice завершил launcher раньше записи PDF | Проверить существование PDF с bounded wait, затем отдельно запустить PNG conversion | `tmp/spreadsheets/rendered-final/` | `no` | `none`; отсутствующий render не использовался | Очистить temporary render после визуальной проверки |
| `TF-010` | Финальная PowerShell hash summary вызвала отсутствующий статический метод `SHA256.HashData` | .NET runtime Windows PowerShell не предоставляет этот API | Использовать `Get-FileHash -Algorithm SHA256` и отдельное чтение `Length` | `n/a` | `no` | `none`; неуспешная summary не использовалась как evidence | Сверить три raw filesystem hash до коммита |

## Handoff Notes For Next Session

- Exact-boundary TC запрещён до ответа, задающего decimal/binary convention для 40 МБ.
- Все promotion gates пройдены; writer/reviewer повторно не запускались.
- V8 FT-first baseline подписан; следующий этап должен работать только с отдельной automation-ready версией.
- `GAP-QUT-001` нельзя закрывать по наблюдению UI без source-backed byte convention.
