# Scope Contract

## Контекст

- FT-пакет: `fts/AutoFin`
- Основной FT DOCX: `source/FT4AutoFinFinal.docx`
- Main FT XHTML: `source/FT4AutoFinFinal.xhtml`
- XHTML extraction notes: `primary source for action-table row; bounded evidence in source-extraction/bsr-32-evidence.json`
- PDF для structural cross-check: `есть`, `source/FT4AutoFinFinal.pdf`
- `AGENT-NOTES.md`: `есть`

## Scope Identity

- `scope_slug`: `search-clear-context-exec-benchmark-v1`
- Рабочее название: Очистка контекста поиска — exec benchmark
- `source_path`: section `4.2`, action table, `BSR 32`
- Режим получения: `agent-proposed-scope -> confirmed`

## Что Входит В Scope

- Нажатие кнопки `Очистить`.
- Независимые эффекты BSR 32: очистка фильтров, сортировок, постраничности и выделения строк.
- Mockup visual inventory: `work/stage-handoffs/48-search-clear-context-exec-benchmark/mockup-visual-inventory.md`.

## Что Не Входит В Scope

- BSR 31 search execution/validation.
- BSR 33+ row information/navigation actions.
- Конкретные default filter/sort/page values, которых нет в BSR 32.
- Runtime UI calibration и production write.

## Разрешенные Источники

| source | type | usage_rule |
| --- | --- | --- |
| `source/FT4AutoFinFinal.docx` | `main-ft-docx` | Authoritative meaning of BSR 32 action row. |
| `source/FT4AutoFinFinal.xhtml` | `main-ft-xhtml` | Mandatory machine-readable row and code extraction. |
| `source/FT4AutoFinFinal.pdf` | `pdf` | Page 8 structural/code parity only. |
| `AGENT-NOTES.md` | `package-notes` | Mandatory context; does not add BSR 32 behavior. |
| `mockups/Рисунок 1 Макет раздела меню Заявки в системе.jpg` | `mockup` | Interaction hints and visible controls only. |

## Scope Complexity Assessment

| factor | value | risk | note |
| --- | --- | --- | --- |
| fields_or_blocks | `1 action row; 4 reset dimensions` | `low` | One source row requires property-level completeness. |
| conditional_dependencies | `pre-existing filter/sort/page/selection state` | `medium` | Each TC creates only the state it verifies. |
| validation_domains | `none` | `low` | No input restriction obligation in BSR 32. |
| action_flows | `single click -> reset one observed dimension per TC` | `low` | Four atomic TCs planned. |
| integrations_api_async | `none` | `low` | UI-visible state only. |
| status_lifecycle | `none` | `low` | No application status transition. |
| expected_gaps_or_unclear | `0` | `low` | Exact default values deliberately out of scope. |

Complexity decision:

- `single_scope_with_internal_packages`
- Обоснование: один BSR с четырьмя независимыми наблюдаемыми обязанностями; один internal package достаточен.

## Внутренние Рабочие Пакеты

| package_id | focus | source_refs | included_requirements | design_method | expected_outputs | split_required |
| --- | --- | --- | --- | --- | --- | --- |
| `WP-01` | reset search context | `SRC-001; BSR 32` | filters; sorting; pagination; row selection reset | state-transition; dependency setup; one-result atomarity | 4 atoms; 4 obligations; 4 planned TC | `no` |

## Benchmark Atomic Seed

| atom_id | req_id | atomic_statement | planned_tc_id |
| --- | --- | --- | --- |
| `ATOM-001` | `BSR 32` | Нажатие `Очистить` очищает применённые фильтры. | `TC-SCCB-001` |
| `ATOM-002` | `BSR 32` | Нажатие `Очистить` очищает применённую сортировку. | `TC-SCCB-002` |
| `ATOM-003` | `BSR 32` | Нажатие `Очистить` очищает постраничность. | `TC-SCCB-003` |
| `ATOM-004` | `BSR 32` | Нажатие `Очистить` очищает выделение строки. | `TC-SCCB-004` |

## Целевые Артефакты

- Promotion-disabled target: `fts/AutoFin/test-cases/4.2-prepared-shadow-search-clear-context-exec-benchmark-v1.md`
- Handoff-папка: `fts/AutoFin/work/stage-handoffs/48-search-clear-context-exec-benchmark/`
- Review-cycle папка: `fts/AutoFin/work/review-cycles/search-clear-context-exec-benchmark-v1-20260713/`

## Условия Старта Следующего Этапа

- Iteration использует current source selection, parity, row inventory, empty gaps file and opened mockup inventory.
- Writer mode: `fresh-eval-run`; existing H19 drafts/test cases are forbidden inputs.
- Каждый `ATOM-*`/`TC-*` получает `package_id = WP-01`; package ledger, design-plan and TC self-check gates обязательны.
- До live: compile, validate-only, artifact validator, exec dry-run, checkpoint/push и отдельная authorization.

## Ограничения И Правила Интерпретации

- Не расширять scope за BSR 32.
- Не придумывать exact defaults; проверять сброс созданного наблюдаемого состояния.
- Mockup уточняет действия, но FT определяет expected behavior.
- Не читать и не перезаписывать существующий production testcase.
