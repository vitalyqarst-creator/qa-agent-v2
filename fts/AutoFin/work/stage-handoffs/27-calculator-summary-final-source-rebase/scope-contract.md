# Контракт Scope: Calculator Summary Entrypoints

## Контекст

- FT-пакет: `fts/AutoFin`
- Основной FT DOCX: `source/FT4AutoFinFinal.docx`
- Main FT XHTML: `source/FT4AutoFinFinal.xhtml`
- XHTML extraction notes: обязательный источник строк таблицы и кодов `BSR 43–46`; совпадающие строки `tr 54–55`.
- PDF для structural cross-check: `есть`, `source/FT4AutoFinFinal.pdf`, страница 16.
- `AGENT-NOTES.md`: `есть`.

## Scope Identity

- `scope_slug`: `application-card-calculator-summary-entrypoints`
- Рабочее название: `Краткая информация с калькулятора и точки входа`
- `source_path`: `section 4.3 / таблица 4 / DOCX table 6 rows 1–2 / XHTML tr 54–55`
- Режим получения: `manual-scope`
- Этот handoff supersedes active use of handoff 05; handoff 05 remains historical evidence.

## Что Входит В Scope

- `BSR 43`: постоянная видимость виджета краткой информации.
- `BSR 44`: отображение пяти перечисленных параметров с этапа кредитного калькулятора.
- `BSR 45`: переход на этап кредитного калькулятора по нажатию виджета.
- `BSR 46`: открытие окна кредитного калькулятора с предзаполненными данными заявки.
- Наблюдаемое наличие предзаполнения до пользовательского ввода.

## Что Не Входит В Scope

- `BSR 35–38`: действия `Продолжить` и `Создать заявку`; это соседний scope `section-4.2-applications-menu-search`.
- Расчётная логика, подбор предложений и внутреннее поведение этапа кредитного калькулятора.
- Исчерпывающий состав предзаполненных полей и точный mapping к данным заявки без внешнего ФТ `Калькулятор`.
- `BSR 39–42` и требования персональных данных начиная с `BSR 47`.
- Макеты не задают бизнес-правила; они используются только для подтверждения расположения виджета/кнопки и простого click interaction.

## Разрешенные Источники

| source | type | usage_rule |
| --- | --- | --- |
| `source/FT4AutoFinFinal.docx` | `main-ft-docx` | Authoritative semantic source; matching table rows contain the calculator statements without BSR labels. |
| `source/FT4AutoFinFinal.xhtml` | `main-ft-xhtml` | Mandatory machine-readable row/list extraction and requirement-code source. |
| `source/FT4AutoFinFinal.pdf` | `pdf` | Page 16 structural and BSR-code cross-check only. |
| `AGENT-NOTES.md` | `package-notes` | Mandatory package context; does not add requirements. |
| `mockups/Рисунок 2  Анкета Клиента. Минимальное состояние.jpg`; `mockups/Рисунок 5 Анкета Клиента. Максимальное состояние.jpg` | `mockup` | UI interaction hints only; see `mockup-visual-inventory.md`. |
| `work/stage-handoffs/26-prepared-standard-calculator-summary/iteration-summary.md` | `regression-evidence` | May preserve discovered risks; must not replace Final FT evidence. |

## Scope Complexity Assessment

| factor | value | risk | note |
| --- | --- | --- | --- |
| fields_or_blocks | `2 UI rows; 1 widget; 1 button; 5 displayed parameters` | `medium` | Parameter values must be checked, not only labels. |
| conditional_dependencies | `source data exists on calculator stage` | `medium` | Visibility remains unconditional. |
| validation_domains | `none` | `low` | No negative validation oracle is defined. |
| action_flows | `widget navigation; button window opening` | `medium` | Two independently observable transitions. |
| integrations_api_async | `none in selected source` | `low` | No internal integration assertions. |
| status_lifecycle | `none` | `low` | No status rules in rows. |
| expected_gaps_or_unclear | `exact prefill field/value mapping` | `medium` | External calculator FT is referenced but unavailable. |

Complexity decision:

- `single_scope_with_internal_packages`
- Обоснование: один связный UI scope с одним лёгким внутренним пакетом; внешний split не требуется.

## Внутренние Рабочие Пакеты

| package_id | focus | source_refs | included_requirements | design_method | expected_outputs | split_required |
| --- | --- | --- | --- | --- | --- | --- |
| `WP-01` | Видимость, содержимое и две точки входа calculator-summary | `SRC-001`; `SRC-002`; Final DOCX/XHTML/PDF | `BSR 43–46` | `field-property coverage; table-list; scenario-use-case; dependency boundary` | atomic ledger, package design plan, 5 testable TCs, preserved gap | `no` |

## Целевые Артефакты

- Candidate draft: attempt-bound file inside a new prepared-standard review cycle.
- Canonical production path remains read-only: `test-cases/14-application-card-calculator-summary-entrypoints.md`.
- Handoff: `work/stage-handoffs/27-calculator-summary-final-source-rebase/`.
- New review cycle must use a unique immutable `codex-exec-prepared-standard-calculator-summary-final-*` path.

## Условия Старта Следующего Этапа

- `source-selection.md` from handoff 20 confirms `xhtml_available: yes`.
- `source-parity-check.md`, `source-row-inventory.md`, oracle inventories, mockup inventory, `scope-coverage-gaps.md` and clarification artifact pass strict validation.
- Because `GAP-001` exists, reviewer mode `scope_gap_review` must pass before prepared writer starts.
- Writer/reviewer must preserve `package_id = WP-01` and run ledger, Package Test Design Plan and TC self-check gates.

## Ограничения И Правила Интерпретации

- DOCX is authoritative for meaning; XHTML supplies exact rows/codes; PDF only cross-checks structure and codes.
- Do not use `AutoFinPreFinal.*`, production test cases, historical cycles or generated inventories as requirement sources.
- Do not infer that all five summary values are non-empty; compare displayed values with recorded source values for the same application.
- Do not infer the exhaustive prefill set or exact mapping from the phrase `предзаполненные данные`.
- Preserve `GAP-001` until an external calculator FT supplies a complete oracle.
