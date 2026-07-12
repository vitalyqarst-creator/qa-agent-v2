# Контракт Scope: Персональные данные клиента — current-source rebase

## Контекст

- FT-пакет: `fts/AutoFin`.
- Основной FT DOCX: `source/FT4AutoFinFinal.docx`.
- Main FT XHTML: `source/FT4AutoFinFinal.xhtml`; mandatory XHTML-first extraction rows `57–66`.
- PDF structural cross-check: `source/FT4AutoFinFinal.pdf`, страницы `16–17`.
- `AGENT-NOTES.md`: обязателен.
- Source selection: `work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`, `xhtml_available: yes`.

## Scope Identity

- `scope_slug`: `application-card-client-personal-data`.
- Рабочее название: `Персональные данные клиента`.
- `source_path`: `4.3 Карточка «Заявка» -> Таблица 4 -> XHTML tr 56–66; BSR 47–77`.
- Режим получения: `manual-scope`.
- Этот handoff supersedes handoff `06` только для нового current-source rebase; исторический `signed-off` остается regression baseline.

## Что Входит В Scope

- Блок `Персональные данные`.
- Поля `Фамилия`, `Имя`, `Отчество`, `ID клиента`, `Пол`, `Дата рождения`, `Клиент менял ФИО`.
- Условные поля `Предыдущая фамилия`, `Предыдущее имя`, `Предыдущее отчество`.
- Обязательность, редактируемость, типы значений, допустимые символы, date boundaries и DaData/ABS success-path obligations из `BSR 47–77`.
- Значения справочника `Пол клиента` из support dictionary: `Мужчина`, `Женщина`.

## Что Не Входит В Scope

- Calculator summary `BSR 43–46`.
- Кнопка и popup распознавания документа `BSR 78–83`.
- Паспорт, адреса, контакты, документы, участники, занятость и последующие блоки Таблицы 4.
- Внутренние payloads, retry/fallback и backend attribution DaData/ABS без observable artifact.
- Макетные значения и расположение элементов не являются бизнес-требованиями.

## Разрешенные Источники

| source | type | usage_rule |
| --- | --- | --- |
| `source/FT4AutoFinFinal.docx` | `main-ft-docx` | Authoritative semantic source. |
| `source/FT4AutoFinFinal.xhtml` | `main-ft-xhtml` | Mandatory source для строк, колонок и `BSR 47–77`. |
| `source/FT4AutoFinFinal.pdf` | `pdf` | Structural/code cross-check, страницы 16–17. |
| `support/АФБ справочники 26.06.26.md` | `support` | Только значения справочника `Пол клиента`. |
| `mockups/Рисунок 2  Анкета Клиента. Минимальное состояние.jpg` | `mockup` | Interaction/layout hints only. |
| `mockups/Рисунок 5 Анкета Клиента. Максимальное состояние.jpg` | `mockup` | Interaction/layout hints only. |
| `test-cases/14-application-card-client-personal-data.md` | `regression-baseline` | Candidate baseline; не источник требований. |
| historical handoff `06` and review cycle | `regression-evidence` | Только lessons/delta; старые BSR mappings не переиспользовать. |

## Scope Complexity Assessment

| factor | value | risk | note |
| --- | --- | --- | --- |
| fields_or_blocks | `1 block; 10 fields` | `medium` | 11 source rows including block row. |
| conditional_dependencies | `previous FIO depends on changed-FIO = Да` | `high` | Visibility and group requiredness. |
| validation_domains | `text-symbols; date-time; allowed-values; requiredness` | `high` | Missing exact UI rejection oracle routes to calibration candidates. |
| action_flows | `edit/save; DaData suggestion selection` | `medium` | Backend attribution is not UI-observable. |
| integrations_api_async | `DaData; ABS` | `high` | Success-path visible effect only without technical evidence. |
| status_lifecycle | `none` | `low` | No lifecycle rules. |
| expected_gaps_or_unclear | `validation UI reaction; integration failure behavior` | `medium` | Non-blocking with explicit candidates/gaps. |

Complexity decision: `single_scope_with_internal_packages`; один связный блок, но writer обязан работать по двум пакетам.

## Внутренние Рабочие Пакеты

| package_id | focus | source_refs | included_requirements | design_method | expected_outputs | split_required |
| --- | --- | --- | --- | --- | --- | --- |
| `WP-01` | Основные персональные данные | `SRC-001..SRC-008`; `BSR 47–65` | visibility, requiredness, editability, dictionary, date boundaries, success-path integrations | `field-property coverage; equivalence-boundary; integration artifact gate` | ledger/design plan/TC/self-check | `yes` |
| `WP-02` | Предыдущая ФИО | `SRC-009..SRC-011`; `BSR 66–77` | conditional visibility, group requiredness, input class, DaData suggestions | `decision table; conditional-requiredness; equivalence` | ledger/design plan/TC/self-check | `yes` |

## Целевые Артефакты

- Canonical file: `test-cases/14-application-card-client-personal-data.md`.
- Handoff: `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/`.
- Новый review cycle должен быть отдельным от исторического cycle и сохранять before/after snapshots.

## Условия Старта Следующего Этапа

- Scope gap review подтверждает gaps и oracle inventories.
- Writer mode: `rebuild-from-scope` с delta reuse существующих кейсов, без слепого overwrite.
- Каждый `ATOM-*` и `TC-*` имеет `package_id`; выполнены package ledger, design-plan и TC gates.
- XHTML rows и `BSR 47–77` полностью отображены в `ATOM-*`, candidate TC или `GAP-*`.

## Ограничения И Правила Интерпретации

- Не использовать `AutoFinPreFinal.*` как requirement source.
- Не считать исторический `signed-off` доказательством current-process compliance.
- Не придумывать message/highlight/filtering/save behavior для invalid/empty values; создавать calibration candidates.
- Не утверждать вызов DaData/ABS по одному UI-результату без observable technical artifact.
