# Source Parity Check Format

`source-parity-check.md` фиксирует сверку основного FT DOCX и PDF по подтвержденному scope до writer/reviewer handoff. Он не заменяет обязательный main FT XHTML extraction source из `source-selection.md`.

Цель artifact - не дать потерять коды требований, строки таблиц, условия и примечания из-за того, что один способ извлечения документа прочитал меньше данных, чем другой.

## Когда создавать

Создавай `source-parity-check.md` для каждого подтвержденного scope, если в FT-пакете есть и основной DOCX, и PDF-версия этого же ФТ.

Не создавай этот artifact для `agent-proposed-scope` контейнера с картой candidate scope-ов, пока пользователь не выбрал один scope. Для карты scope-ов достаточно structural cross-check по разделам.

Если PDF отсутствует, явно зафиксируй это ограничение в `scope-contract.md` и `scope-coverage-gaps.md`; не создавай пустой parity artifact.

## Расположение

```text
fts/<ft-slug>/work/stage-handoffs/NN-<scope-slug>/source-parity-check.md
```

`workflow-state.yaml` должен ссылаться на artifact в `latest_artifacts.source_parity_check`. Если следующий этап writer, reviewer или iteration работает по подтвержденному scope и DOCX+PDF доступны, добавь `source-parity-check.md` в `required_inputs`.

## Обязательная сверка

Сверяй только подтвержденный scope, а не весь документ.

Минимально проверь:

- инвентаризацию источников: DOCX path, PDF path, методы извлечения, релевантные разделы DOCX и страницы PDF;
- ссылку на XHTML extraction notes/source rows, если таблицы, списки или вложенные списки извлекались из XHTML;
- границы scope: номера разделов, заголовки, начало/конец блока;
- коды требований: все `GSR`, `REQ` или локальные коды из DOCX и PDF;
- таблицы: названия/блоки, строки полей, условия видимости/обязательности/редактируемости, примечания;
- cross-references: ссылки на другие GSR/разделы внутри выбранного scope;
- расхождения: PDF-only, DOCX-only, semantic mismatch, extraction-risk.

## Правила решения

- Если код требования есть хотя бы в одном источнике внутри подтвержденного scope, он обязателен для `req_id` в ledger/traceability matrix и для ссылок тест-кейсов через связанный `ATOM-*`.
- Если код есть только в PDF, используй PDF-код как `req_id`; не заменяй его названием раздела, поля или таблицы.
- Если PDF и DOCX различаются только наличием кода требования, поведение бери из текста/таблицы основного ФТ, но код сохраняй из PDF.
- Если PDF и DOCX дают разные смысловые требования, не выбирай молча один вариант: зафиксируй `coverage gap` с точной привязкой к обеим версиям.
- Если extractor DOCX теряет таблицу, строки или коды, зафиксируй `extraction-risk` и используй PDF как контрольную карту навигации и кодов.
- Если DOCX/PDF extraction теряет список, вложенный список, перечень значений или таблицу, но этот фрагмент есть в XHTML, используй XHTML extraction для row/list inventory и зафиксируй это в downstream source refs.

## Минимальный шаблон

```md
## Source Parity Check

- FT package: `fts/<ft-slug>`
- Scope: `<scope-slug>`
- DOCX source: `source/<main-ft>.docx`
- XHTML source: `source/<main-ft>.xhtml`
- PDF source: `source/<main-ft>.pdf`
- DOCX extraction: `<tool/method>`
- XHTML extraction: `<tool/method>`
- PDF extraction: `<tool/method>`
- DOCX scope refs: `<sections/headings>`
- PDF scope refs: `<pages/sections>`

## Boundary Parity

| item | docx_ref | pdf_ref | status | note |
| --- | --- | --- | --- | --- |
| `<section/block/table>` | `<ref>` | `<page/ref>` | `match | mismatch | docx-only | pdf-only` | `<note>` |

## Requirement Id Inventory

| req_id | docx_ref | pdf_ref | status | source_decision | note |
| --- | --- | --- | --- | --- | --- |
| `GSR 123` | `-` | `page 61, table ...` | `pdf-only` | `mandatory-req-id` | `Use as req_id in ledger/matrix` |

## Table / Row Parity

| row_anchor | docx_ref | pdf_ref | docx_text | pdf_text | status | action |
| --- | --- | --- | --- | --- | --- | --- |
| `<field/block>` | `<ref>` | `<page/ref>` | `<short>` | `<short>` | `match | mismatch | docx-only | pdf-only | extraction-risk` | `use | gap | exclude-out-of-scope` |

## Mandatory Traceability Inputs

- Requirement IDs to preserve: `GSR ...`
- PDF-only IDs to preserve: `GSR ... | none`
- DOCX-only IDs to preserve: `... | none`
- Semantic mismatches requiring gaps: `GAP-* | none`

## Decision

- Scope parity status: `pass | pass-with-extraction-risk | blocked-mismatch`
- Writer/reviewer rule: `<how downstream must use the parity result>`
- Open gaps/questions: `GAP-* | none`
```

## Downstream contract

Writer:

- читает `source-parity-check.md` перед atomic ledger;
- переносит все mandatory requirement IDs в `req_id`;
- не ставит `ready-for-review`, если обязательный parity artifact отсутствует при наличии DOCX+PDF.

Reviewer:

- в `traceability` и `full` проверяет, что все mandatory IDs из parity artifact есть в ledger/matrix;
- считает отсутствие PDF-only `req_id` blocking traceability defect;
- не подписывает набор, если parity artifact показывает `blocked-mismatch`.

Iteration:

- не считает loop готовым к `signed-off`, если обязательный parity artifact отсутствует или reviewer не проверил source parity.
