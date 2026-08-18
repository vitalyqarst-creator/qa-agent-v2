# Контракт выбора источников

Source locator создаёт только:

- `AGENT-NOTES.md` с классификацией фактически доступных support-файлов;
- `work/stage-handoffs/00-<ft>/source-selection.md`;
- `work/stage-handoffs/00-<ft>/workflow-state.yaml`;
- controller-owned `work/runtime-session-registry.json` уже существует до начала этапа.

Созданный при инициализации пакета пустой `work/scope-clarification-requests.md` также допустим, но source locator не добавляет в него вопросы.

`workflow-state.yaml` содержит `source_contract_version: 2`, `stage: source-locator`, `status: completed`, путь к `source-selection.md`, списки `primary_sources`, `support_sources`, `visual_sources` и при наличии `figma_sources`. Для каждого локального файла обязательны repo-relative `path`, роль и SHA-256.

В `primary_sources` должны присутствовать ровно одна роль `semantic_primary` и одна роль `machine_readable_primary`. Это не обязательно два пользовательских файла: нативный XHTML может иметь объединённую роль `semantic_primary+machine_readable_primary`, а для канонического DOCX source locator создаёт производный XHTML через `scripts/normalize_ft_source.py`. Производное представление должно буквально сохранять видимые автонумерованные метки Word, включая коды требований и подписи таблиц, а также количество таблиц и строк; иначе source stage остаётся `blocked-input`. Для машинной записи обязательно поле `origin: canonical|generated|supplied`; при `generated` также указываются `derived_from`, `derived_from_sha256` и `generator`.

`visual_crosscheck` принимает `required` или `not_required`. При `required` в `visual_sources` регистрируется хотя бы один PDF/рендер с ролью `visual_structural_crosscheck_only`. При `not_required` визуальный файл не создаётся, а `visual_crosscheck_reason` конкретно объясняет, почему расположение, рисунки и сложная разметка не влияют на смысл scope-ов. Все фактически находящиеся в `source/`, `support/` и `mockups/` файлы регистрируются; скрытое игнорирование входа запрещено.

PDF/рендер при наличии проверяется визуально и структурно, но не становится источником бизнес-правил. Рендеры и другие временные файлы создаются только в системном временном каталоге. Source locator удаляет созданный им временный каталог до завершения; новые файлы в repo-local `tmp/` после регистрации source-locator считаются ошибкой этапа.

Минимальный вариант для DOCX без визуально значимой разметки:

```yaml
source_contract_version: 2
stage: source-locator
status: completed
source_selection: "fts/Project/FT/work/stage-handoffs/00-FT/source-selection.md"
visual_crosscheck: not_required
visual_crosscheck_reason: "ФТ содержит только линейный текст и простые таблицы без визуального оракула."
primary_sources:
  - path: "fts/Project/FT/source/requirements.docx"
    role: semantic_primary
    sha256: "<sha256>"
  - path: "fts/Project/FT/source/requirements.normalized.xhtml"
    role: machine_readable_primary
    origin: generated
    derived_from: "fts/Project/FT/source/requirements.docx"
    derived_from_sha256: "<sha256 DOCX>"
    generator: "scripts/normalize_ft_source.py"
    sha256: "<sha256 XHTML>"
support_sources:
visual_sources:
```

До возврата результата обязательно выполнить:

```text
python scripts/validate_runtime_source.py <FT-package> <source-handoff-dir>
```

Validator проверяет registry, роли, пути, hashes, полноту регистрации локальных входов, отсутствие преждевременных downstream-артефактов и оставленных временных файлов. Самопроверка текстом или только `validate_runtime_tree.py` её не заменяет.

## Возобновление существующего route

Если source selection уже завершён, входные hashes не менялись, а downstream-артефакты существуют, новый practical route не создаёт source stage заново. Controller переиспользует существующие source artifacts и проверяет их без удаления downstream:

```text
python scripts/validate_runtime_source.py <FT-package> <source-handoff-dir> --resume-existing
```

Этот режим ничего не регистрирует и не разрешает незарегистрированный новый input. Он только подтверждает, что исторический source selection по-прежнему соответствует текущим файлам.

## Поздний support после вопросов БА

Новый support-файл, предоставленный после scope analysis, регистрирует та же source-locator-сессия в существующих `AGENT-NOTES.md`, `source-selection.md` и `workflow-state.yaml`. Primary и visual selection не пересматриваются, semantic stages не выполняются. Поскольку downstream-артефакты к этому моменту ожидаемы, используется ограниченная проверка:

```text
python scripts/validate_runtime_source.py <FT-package> <source-handoff-dir> --support-update
```

Она по-прежнему проверяет полный набор локальных входов, роли, пути и SHA-256, но не считает уже существующие scope/matrix/TC и поздние временные файлы ошибкой первоначальной source-стадии.
