# Scope Contract

## Контекст

- FT-пакет: `fts/AutoFin`
- Основной FT DOCX: `source/FT4AutoFinFinal.docx`
- Main FT XHTML: `source/FT4AutoFinFinal.xhtml`
- XHTML extraction notes: primary source for Table 4 rows 182-184 and Appendix 1 list values; parsed with huge-tree recovery and cross-checked against DOCX/PDF.
- PDF для structural cross-check: `source/FT4AutoFinFinal.pdf`
- `AGENT-NOTES.md`: обязательный package context.
- Benchmark purpose: проверить medium-size prepared writer-reviewer cycle без production promotion.

## Scope Identity

- `scope_slug`: `visual-assessment-medium-scope-benchmark`
- Функциональный scope: `visual-assessment-criteria`
- Рабочее название: поле и справочник параметров визуальной оценки клиента.
- `source_path`: `section-16 / Table 4 / Visual assessment block` и `section-20 / Appendix 1`.
- Режим получения: `manual-scope / user-delegated selection from ranked candidates`.

## Что Входит В Scope

- Блок `Визуальная информация`.
- Поле `Визуальная информация`: постоянная видимость, default `Нет`, ветка `Да` и multiple selection.
- Поле `Параметры визуальной оценки`: условная видимость, checkbox values, минимум одно значение.
- `BSR 311`-`BSR 317`.
- Все восемь групп и все значения Appendix 1.
- Checkbox `Другое`, условное поле комментария и его обязательность.
- Standalone `Комментарий` как отдельное поле ввода согласно сохранённому ответу аналитика.
- Mockup visual inventory: `work/stage-handoffs/52-visual-assessment-medium-scope-benchmark/mockup-visual-inventory.md`.

## Что Не Входит В Scope

- Согласия/FATCA/CRS/AML и соседние строки Table 4.
- Остальные поля карточки заявки, действия Table 5 и переход `Далее`.
- Скоринг, статусы, кредитное решение, роли, API, persistence и audit trail.
- Проверка фактической UI-реакции: для двух requiredness obligations сохраняется `ui-calibration-required`.
- Изменение `test-cases/section-18-visual-assessment-criteria.md` или любого production test-case file.

## Разрешенные Источники

| source | type | usage_rule |
| --- | --- | --- |
| `source/FT4AutoFinFinal.docx` | `main-ft-docx` | Authoritative meaning and scope boundary. |
| `source/FT4AutoFinFinal.xhtml` | `main-ft-xhtml` | Mandatory table/list extraction; rows 182-184 and Appendix 1. |
| `source/FT4AutoFinFinal.pdf` | `pdf` | Structural/visual parity and BSR 311-317 confirmation on p.34. |
| `AGENT-NOTES.md` | `package-notes` | Mandatory package context; does not add requirements. |
| `open-scope-coverage-gaps_ответы Соболева.md` | `analyst-answer` | Only the standalone-comment mapping answer. |
| `mockups/Рисунок 5 Анкета Клиента. Максимальное состояние.jpg` | `mockup` | Interaction hints only; not a source of rules or oracles. |
| `work/test-design/section-18-visual-assessment-criteria/*` | `regression-design` | Lessons/projection seed only; current FT sources remain authoritative. |

## Scope Complexity Assessment

| factor | value | risk | note |
| --- | --- | --- | --- |
| fields_or_blocks | `1 block; 2 fields; 8 dictionary groups; 52 source rows` | `medium` | Complete list evidence must remain intact. |
| conditional_dependencies | `Визуальная информация = Да -> parameters visible` | `medium` | BSR 313/314. |
| validation_domains | `minimum selection; mandatory Other comment` | `medium` | Exact UI reaction requires calibration. |
| action_flows | `toggle; checkbox selection; text input` | `low` | No save/status flow is defined. |
| integrations_api_async | `none` | `low` | Internal effects are out of scope. |
| status_lifecycle | `none` | `low` | Do not infer downstream decision effects. |
| expected_gaps_or_unclear | `0 active gaps; 2 candidate requiredness oracles` | `medium` | Candidate oracles are explicit, not hidden gaps. |

Complexity decision:

- `single_scope_with_internal_packages`
- Обоснование: один однородный UI/dictionary domain, 13 obligations и 12 planned TC; external split or sharding would distort the benchmark.

## Внутренние Рабочие Пакеты

| package_id | focus | source_refs | included_requirements | design_method | expected_outputs | split_required |
| --- | --- | --- | --- | --- | --- | --- |
| `WP-01` | field behavior, dependency and complete criteria dictionary | `SRC-001`-`SRC-052`; `BSR 311`-`BSR 317`; `DICT-001/101-108` | 13 obligations mapped to 12 TC; BSR 313/314 share one observable visibility case | field-property coverage; dependency matrix; table-list; dictionary-source; requiredness calibration | package ledger, 12-row design plan, 12-TC draft, package self-check | `no` |

## Целевые Артефакты

- Benchmark draft target: `test-cases/section-18-visual-assessment-medium-scope-benchmark.md` - promotion disabled; file must remain absent.
- Handoff: `work/stage-handoffs/52-visual-assessment-medium-scope-benchmark/`.
- Review cycle: `work/review-cycles/visual-assessment-medium-scope-benchmark-v1-20260713/`.

## Условия Старта Следующего Этапа

- Current source parity, 52-row inventory, complete dictionary and requiredness inventory exist.
- Active gaps and blocking reasons equal zero.
- Prepared projection contains 13 obligations, 12 planned TC and one `WP-01`.
- Package-by-package gates are mandatory: ledger self-check, Package Test Design Plan self-check, TC self-check.
- Live starts only after compile/identity/oracle/capacity/validator/dry-run gates, pushed checkpoint and separate pushed one-shot authorization.

## Ограничения И Правила Интерпретации

- One TC has one action focus and one main observable result.
- BSR 313/314 may share one case because the same selection action has the single result `parameters list visible`; both obligations remain separately traceable.
- Do not infer exact requiredness message, highlight, button state or persistence without UI evidence.
- All dictionary values must stay in evidence; examples cannot replace the complete list.
- Mockup refines steps only; FT and analyst answer define behavior.
