# Формат `scope-contract.md`

Этот документ задает канонический формат для `scope-contract.md` в handoff-модели FT pipeline.

`scope-contract.md` фиксирует подтвержденные границы работы. Он не заменяет `scope-coverage-gaps.md` и не должен смешивать рамку scope с проблемами покрытия.

## Когда создавать

- только для подтвержденного scope;
- в режиме `manual-scope`;
- после `agent-proposed-scope` только после того, как пользователь утвердил один candidate scope;
- до создания handoff к writer.

Перед созданием `scope-contract.md` для большого ФТ должна быть выполнена декомпозиция по `references/agent/scope-decomposition-policy.md`: сначала внешние candidate scope-ы по разделам/подразделам, затем contract только для выбранного внешнего scope.

## Обязательные секции

- `## Контекст`
- `## Scope Identity`
- `## Что Входит В Scope`
- `## Что Не Входит В Scope`
- `## Разрешенные Источники`
- `## Scope Complexity Assessment`
- `## Внутренние Рабочие Пакеты`
- `## Целевые Артефакты`
- `## Условия Старта Следующего Этапа`
- `## Ограничения И Правила Интерпретации`

## Правила формата

- `scope-contract.md` обязателен только для подтвержденного scope.
- При `agent-proposed-scope` не создавай `scope-contract.md` до выбора одного candidate scope.
- В `Разрешенные Источники` явно отделяй допустимые cross-FT ссылки от запрещенного расширения scope.
- Документ фиксирует рамку работы, а не `coverage gaps`.
- Если PDF для structural cross-check отсутствует, укажи это явно в секции `Контекст`.
- Если `source-selection.md` не подтверждает `xhtml_available: yes`, не создавай `scope-contract.md`; останови workflow как `blocked-input`.
- Если DOCX и PDF основного ФТ доступны, `source-parity-check.md` должен быть создан рядом с `scope-contract.md` до handoff к writer/reviewer.
- Если `source-parity-check.md` содержит row-level/table parity или scope основан на таблице полей/действий, рядом со `scope-contract.md` должен быть создан `source-row-inventory.md` до handoff к writer/reviewer.
- Если подтвержденный UI scope содержит источник типа `mockup` или путь `mockups/*`, рядом со `scope-contract.md` должен быть создан `mockup-visual-inventory.md` по `references/agent/mockup-visual-inventory-format.md`. Недостаточно перечислить файл макета: его визуальное содержимое должно быть открыто и зафиксировано. Если макет нельзя открыть, не переводите scope в `ready-for-next-stage`; используйте `blocked-input`.
- `Scope Complexity Assessment` обязателен для каждого подтвержденного scope, даже если scope простой.
- `Внутренние Рабочие Пакеты` обязательны для каждого подтвержденного scope. Даже простой scope должен иметь минимум один пакет `WP-01`.
- Не используй формулировку `не требуются` для внутренних рабочих пакетов. Если scope простой, создай один легкий пакет `WP-01` с focus = весь подтвержденный scope и `split_required = no`.
- Внутренний рабочий пакет не является новым внешним scope и не создает отдельный canonical test-case file сам по себе.
- Внутренние рабочие пакеты не должны использоваться для маскировки слишком широкого внешнего scope. Если scope фактически покрывает весь большой FT или несколько независимых разделов, сначала вернись к `agent-proposed-scope` и предложи внешнее разбиение.
- Внутренний рабочий пакет является единицей обработки writer/reviewer: сначала package ledger, затем Package Test Design Plan, затем package TC, затем package self-check. Только после этого можно переходить к следующему package.

## Минимальный шаблон

```md
## Контекст

- FT-пакет: `fts/<ft-slug>/...`
- Основной FT: `...`
- Main FT XHTML: `source/<main-ft>.xhtml`
- XHTML extraction notes: `primary source for tables/lists/rows; limitations | none`
- PDF для structural cross-check: `есть | нет`
- `AGENT-NOTES.md`: `есть | нет`

## Scope Identity

- `scope_slug`: `...`
- Рабочее название: `...`
- `source_path`: `...`
- Режим получения: `manual-scope | agent-proposed-scope -> confirmed`

## Что Входит В Scope

- `...`

Для UI scope с mockup добавь:

- Mockup visual inventory: `fts/<ft-slug>/work/stage-handoffs/NN-<scope-slug>/mockup-visual-inventory.md`

## Что Не Входит В Scope

- `...`

## Разрешенные Источники

| source | type | usage_rule |
| --- | --- | --- |
| `...` | `main-ft-docx | main-ft-xhtml | pdf | support | related-ft | mockup` | `...` |

## Scope Complexity Assessment

| factor | value | risk | note |
| --- | --- | --- | --- |
| fields_or_blocks | `...` | `low | medium | high` | `...` |
| conditional_dependencies | `...` | `low | medium | high` | `...` |
| validation_domains | `numeric | date-time | length | text | none` | `low | medium | high` | `...` |
| action_flows | `...` | `low | medium | high` | `...` |
| integrations_api_async | `...` | `low | medium | high` | `...` |
| status_lifecycle | `...` | `low | medium | high` | `...` |
| expected_gaps_or_unclear | `...` | `low | medium | high` | `...` |

Complexity decision:

- `single_scope_with_internal_packages | split_into_external_scopes`
- Обоснование: `...`

## Внутренние Рабочие Пакеты

Каждый подтвержденный scope должен иметь минимум один package. Для простого scope используй один `WP-01`; для неоднородного scope раздели работу на несколько `WP-*`.

| package_id | focus | source_refs | included_requirements | design_method | expected_outputs | split_required |
| --- | --- | --- | --- | --- | --- | --- |
| `WP-01` | `...` | `...` | `...` | `field-property coverage | equivalence-boundary | dependency matrix | decision table | integration artifact gate | scenario-use-case` | `...` | `yes | no` |

## Целевые Артефакты

- Канонический файл тест-кейсов: `fts/<ft-slug>/test-cases/<section-id>-<scope-slug>.md`
- Handoff-папка: `fts/<ft-slug>/work/stage-handoffs/NN-<scope-slug>/`
- Review-cycle папка: `fts/<ft-slug>/work/review-cycles/<scope-slug>/`

## Условия Старта Следующего Этапа

- Writer использует:
  - `source-selection.md` с `xhtml_available: yes`
  - `scope-contract.md`
  - `source-parity-check.md`, если доступны DOCX+PDF
  - `source-row-inventory.md`, если `source-parity-check.md` содержит row-level/table parity или scope основан на таблице полей/действий
  - `mockup-visual-inventory.md`, если scope содержит mockup
  - `scope-coverage-gaps.md`
  - `prompt.scope-to-writer.md`
- Iteration использует:
  - `source-selection.md` с `xhtml_available: yes`
  - `scope-contract.md`
  - `source-parity-check.md`, если доступны DOCX+PDF
  - `source-row-inventory.md`, если `source-parity-check.md` содержит row-level/table parity или scope основан на таблице полей/действий
  - `mockup-visual-inventory.md`, если scope содержит mockup
  - `scope-coverage-gaps.md`
  - `prompt.scope-to-iteration.md`
- Scope готов к handoff, когда созданы все обязательные артефакты.
- Scope готов к handoff только если в `prompt.scope-to-writer.md` и `prompt.scope-to-iteration.md` явно перенесены package-by-package gate, обязательный `package_id` для `ATOM-*`/`TC-*`, Package Test Design Plan gate и запрет переходить к следующему package без package self-check.

## Ограничения И Правила Интерпретации

- Не расширять scope.
- Не выдумывать поведение вне текста FT.
- DOCX remains source of truth; XHTML is mandatory as the primary machine-readable extraction source; PDF is structural/visual cross-check.
- Связанные FT использовать только при явной ссылке из основного FT.
```

## Что не включать

- findings reviewer-а;
- решения writer-а по замечаниям;
- traceability matrix;
- список `coverage gaps` как замену `scope-coverage-gaps.md`.
