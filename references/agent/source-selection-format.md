# Формат выбора источников

Этот reference задает канонический формат `source-selection.md`: артефакта, который фиксирует выбранный FT-пакет, основной DOCX ФТ, обязательный XHTML для machine-readable extraction, PDF для structural/visual cross-check и связанные материалы перед `ft-scope-analyzer`.

## Назначение

- сделать выбор источников воспроизводимым без истории чата;
- не смешивать выбор FT-пакета с определением scope;
- явно отделить main FT от support/mockups/Figma;
- зафиксировать `main-ft-docx` как authoritative source of truth;
- зафиксировать `main-ft-xhtml` как mandatory primary machine-readable extraction source;
- зафиксировать source quality limitations до downstream writer/reviewer loop;
- предотвратить работу по неоднозначному, неподтвержденному или не имеющему XHTML источнику.

## Расположение

Для новых handoff-папок:

```text
fts/<ft-slug>/work/stage-handoffs/NN-<scope-or-container-slug>/source-selection.md
```

Если scope еще не выбран и создается предварительный контейнер для `agent-proposed-scope`, используй numbered directory вида:

```text
fts/<ft-slug>/work/stage-handoffs/00-<container-slug>/source-selection.md
```

`source-selection.md` не заменяет `workflow-state.yaml`: первый фиксирует содержательный выбор файлов, второй фиксирует process-status.

Не создавай `source-selection.md`, `scope-options.md`, `scope-selection-prompts.md`, `workflow-state.yaml` или session logs в корне FT-пакета `fts/<ft-slug>/`. Root-level workflow artifacts считаются contamination risk для clean runs. Используй только `work/stage-handoffs/NN-<scope-or-container-slug>/`.

## Validator Contract

- Для `current_stage: ft-source-locator` `workflow-state.yaml` обязан ссылаться на `source-selection.md` через `required_inputs` и/или `latest_artifacts.source_selection`.
- Source-locator handoff не должен содержать `scope-contract.md`, `prompt.scope-to-writer.md` или `prompt.scope-to-iteration.md`. Эти файлы создаются только стадией `ft-scope-analyzer`.
- Если `source-selection.md` отсутствует или не связан из `workflow-state.yaml`, handoff считается неполным даже при наличии session log.
- Если source-locator создал scope-stage artifacts, это считается нарушением границы skill-а, а не допустимым ускорением workflow.
- Если FT-пакет содержит root-level handoff artifacts (`source-selection.md`, `scope-options.md`, `scope-selection-prompts.md`, `workflow-state.yaml`, session logs), validator должен вернуть `ft-package-root-level-handoff-artifacts`.

Дополнительные проверки validator:

- `source-selection.md` содержит все обязательные разделы: `Контекст`, `Основные документы ФТ`, `Машиночитаемый источник XHTML`, `PDF для структурной и визуальной сверки`, `Вспомогательные файлы и макеты`, `Качество источников`, `Неоднозначности и журнал решений`, `Передача следующему этапу`.
- `Контекст` содержит `Выбранный FT slug` и `Статус выбора`; validator нормализует их к машинным ключам `selected_ft_slug` и `selection_status`.
- `selection_status` имеет одно из значений `selected`, `ambiguous`, `blocked-input`.
- Если `selection_status` не `selected`, workflow остаётся заблокированным и не маршрутизируется к `ft-scope-analyzer`, writer, iteration или reviewer.
- `Машиночитаемый источник XHTML` содержит `XHTML доступен: yes | no`.
- При отсутствии matching main FT XHTML source selection устанавливает `Статус выбора: blocked-input`, `XHTML доступен: no` и не маршрутизируется к downstream skill.
- Для ordinary practical route v0.9 видимые заголовки, столбцы и пояснения source-selection артефакта должны быть на русском; технические идентификаторы и значения перечислений могут оставаться без перевода.

## Required Sections

### Контекст

Минимальные поля:

- `request_summary`;
- `selected_ft_slug`;
- `selection_status`;
- `code_branch` — фактический вывод `git branch --show-current` в момент source selection;
- `code_commit` — точный 40-символьный SHA из `git rev-parse HEAD` в момент source selection;
- `source_locator_contract_version` — текущая версия контракта source locator:
  `source-locator-contract-v1`;
- `created_at`;
- `created_by`.

### Ограниченное обновление метаданных

Если source/support inputs, выбранный FT-пакет и состав выбора не изменились,
`ft-scope-analyzer` может актуализировать в существующем `source-selection.md`
только provenance: `code_branch`, `code_commit`, краткое описание запроса и
поля последнего обновления. Это не является повторным запуском
`ft-source-locator`.

- Сохрани `Создано` и `Создано кем`; добавь `Обновлено` и `Обновлено кем` с
  фактическим исполнителем. В пользовательском тексте пиши «ограниченное
  обновление метаданных», а не внутреннее `metadata-only`.
- Запиши краткое решение в `agent-decision-log.md`, но не переписывай
  исторический `source-locator-session-log.md`.
- При изменении источников, их хэшей, ролей или границ используй ограниченную
  содержательную пересборку.

Изменение `code_commit` само по себе не делает выбор источников устаревшим,
если записанная `source_locator_contract_version` совпадает с текущей. Такая
совместимость действует только для source locator: при изменении его правил
maintainer повышает версию контракта. Для scope/writer/reviewer по-прежнему
нужен их актуальный instruction context и version gate.

Допустимые `selection_status`:

- `selected`;
- `ambiguous`;
- `blocked-input`.

Если статус не `selected`, downstream `ft-scope-analyzer` не должен стартовать без явного решения пользователя или обновленного `source-selection.md`.

### Physical Availability Before Missing-Input Claim

`rg --files`, `git ls-files`, `git status` и `.gitignore` не доказывают отсутствие FT input: локальные материалы могут быть ignored by Git. Перед `blocked-input` проверь точный путь и родительский каталог через файловую систему; при расхождении сначала устрани его, не публикуя предварительный blocker.

### Состав выбора

Заполни минимальный шаблон ниже. DOCX — источник требований, matching XHTML —
обязательный источник извлечения, PDF — только сверка. Зарегистрируй support,
макеты, Figma и package notes без вывода из них бизнес-правил. До подтверждения
scope support и макеты — кандидаты; обязательны только package notes. Укажи
читаемость и все строгие предупреждения. Если matching XHTML отсутствует,
установи `Статус выбора: blocked-input` и не передавай работу дальше.
В practical route читай DOCX через `python-docx`, извлекай XHTML, PDF используй
только для сверки и не запускай LibreOffice. ФТ остаётся источником поведения.
Не сохраняй Figma token, cookie, одноразовый URL или персональный доступ.

### Неоднозначности и журнал решений

Если выбор неоднозначен, перечисли candidate FT packages / files и причину:

- похожее имя;
- несколько версий;
- отсутствующий main FT;
- отсутствующий main-ft-xhtml;
- несоответствие PDF;
- непонятная роль файла.

Не выбирай источник по догадке. Для `selection_status: ambiguous` `workflow-state.yaml` должен использовать `stage_status: blocked-input` или другой явно неготовый статус.

### Передача следующему этапу

Handoff к `ft-scope-analyzer` разрешен только при `selection_status: selected` и `xhtml_available: yes`:

```yaml
current_stage: ft-source-locator
stage_status: ready-for-next-stage
next_skill: ft-scope-analyzer
```

`latest_artifacts` в `workflow-state.yaml` должен ссылаться на:

- `source_selection`;
- active main FT document;
- `main_ft_xhtml`;
- structural cross-check PDF, если есть;
- Figma design index, если есть;
- package notes, если есть;
- artifact manifest, если aliases или local-only evidence значимы.

`source-selection.md` не должен создавать `scope-contract.md`, `prompt.scope-to-writer.md` или `prompt.scope-to-iteration.md`: это ответственность `ft-scope-analyzer`.

После записи source-locator handoff выполни read-only validation:

```text
python scripts/validate_agent_artifacts.py --root fts/<domain>/<ft-slug> --text --source-quality-policy strict --session-log-policy strict --decision-log-policy strict
```

В `source-locator-session-log.md` зафиксируй команду, counts `errors/warnings/info` и `downstream_allowed: yes | no`. `errors > 0` запрещают downstream; warning требует явного решения, но не блокирует автоматически. Не выполняй совместимый повторный прогон только ради формулировки «зелёный» результат: итоговый receipt всегда относится к strict-прогону.

Validator findings:

- `workflow-state-source-locator-missing-source-selection`: source-locator workflow не ссылается на `source-selection.md`.
- `workflow-state-source-locator-premature-scope-artifacts`: source-locator handoff содержит `scope-contract.md`, `prompt.scope-to-writer.md` или `prompt.scope-to-iteration.md`.

Additional validator findings:

- `source-selection-missing-required-sections`: `source-selection.md` misses one or more required handoff sections.
- `source-selection-missing-context-fields`: `Context` does not expose `selected_ft_slug` and/or `selection_status`.
- `source-selection-missing-code-provenance`: отсутствуют `code_branch` и/или `code_commit`; selected handoff не должен идти downstream.
- `source-selection-invalid-code-commit`: `code_commit` не является SHA-1 Git commit.
- `source-selection-code-commit-stale`: зафиксированный commit не совпадает с `HEAD` checkout, где запускается validator.
- Если `code_commit` отличается от commit в соседнем историческом
  `source-locator-session-log.md`, обязательны поля `Обновлено` и `Обновлено кем`;
  иначе validator возвращает
  `source-selection-provenance-update-missing-fields`.
- `source-selection-invalid-selection-status`: `selection_status` is outside `selected | ambiguous | blocked-input`.
- `workflow-state-source-selection-not-selected`: workflow routes downstream while `source-selection.md` is still `ambiguous` or `blocked-input`.

Validator-enforced XHTML findings:

- `source-selection-missing-xhtml-section`: `source-selection.md` misses `Machine-Readable XHTML Source`.
- `workflow-state-source-selection-missing-required-xhtml`: `selection_status = selected`, but `xhtml_available != yes`.
- `workflow-state-source-selection-xhtml-missing-routes-downstream`: workflow routes to scope/writer/reviewer/iteration while XHTML is missing.

## Минимальный шаблон

```md
# Выбор источников

## Контекст

- Краткое описание запроса:
- Выбранный FT slug:
- Статус выбора: `selected | ambiguous | blocked-input`
- Ветка кода:
- Коммит кода:
- Версия контракта source locator: `source-locator-contract-v1`
- Создано:
- Создано кем:
- Обновлено: <!-- только при актуализации provenance -->
- Обновлено кем: <!-- только при актуализации provenance -->

## Основные документы ФТ

| Путь | Роль | Причина выбора | Версия или дата | Примечания о качестве источника |
| --- | --- | --- | --- | --- |

## Машиночитаемый источник XHTML

- Выбранный XHTML ФТ:
- XHTML доступен: `yes | no`
- Путь к XHTML:
- Соответствует основному ФТ: `yes | no | not-checked`
- Роль XHTML: `mandatory_machine_readable_extraction_source`
- XHTML обязателен для следующих этапов: `yes`
- Причина блокировки:

## PDF для структурной и визуальной сверки

- PDF доступен: `yes | no`
- Путь к PDF:
- PDF соответствует основному ФТ: `yes | no | not-checked`
- Ограничение:

## Вспомогательные файлы и макеты

| Путь | Роль | Причина релевантности | Обязателен на следующих этапах | Ограничения |
| --- | --- | --- | --- | --- |

### Ссылки на Figma-дизайн (необязательно)

| Идентификатор Figma | Ссылка на дизайн | Страница/фрейм или идентификатор узла | Релевантные scope | Визуальное назначение | Статус доступа | Путь к снимку | Дата проверки | Ограничения |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `FIGMA-001` | `<https://www.figma.com/design/...>` | `<название страницы/фрейма, node-id или ->` | `<scope slug or package-wide>` | `optional_visual_reference` | `not_checked` | `->` | `<ISO date or ->` | `node-id` необязателен; не является источником требований |

На этапе source locator допустим исходный статус `not_checked`: он лишь
регистрирует доступную ссылку. При анализе релевантного scope агент сам ищет
страницу/фрейм по его названию, если `node-id` не передан пользователем, и
заменяет этот статус результатом visual-check.

## Качество источников

- Активные исходные документы:
- Читаемость:
- Уверенность в идентификаторах разделов:
- Крупные блоки:
- Строгие предупреждения:

## Неоднозначности и журнал решений

| Кандидат | Проблема | Требуемое решение |
| --- | --- | --- |

## Передача следующему этапу

- Следующий навык:
- Обязательные входы:
- Последние артефакты:
- Причины блокировки:
```
