# Контракт выбора источников

Source locator создаёт только:

- производное машинное представление канонического источника, если оно отсутствовало;
- `work/stage-handoffs/00-<ft>/source-selection.md`;
- `work/stage-handoffs/00-<ft>/workflow-state.yaml`;
- controller-owned `work/runtime-session-registry.json` уже существует до начала этапа.

`AGENT-NOTES.md` — пользовательский вход и package-specific контракт. Source locator читает его, но не изменяет. Фактическая runtime-классификация, происхождение сгенерированного XHTML и поздние support-файлы записываются в source handoff.

Созданный при инициализации пакета пустой `work/scope-clarification-requests.md` также допустим, но source locator не добавляет в него вопросы.

`workflow-state.yaml` содержит `source_contract_version: 2`, `stage: source-locator`, `status: completed`, путь к `source-selection.md`, списки `primary_sources`, `support_sources`, `visual_sources` и при наличии `figma_sources`. Для каждого локального файла обязательны repo-relative `path`, роль и SHA-256.

В `primary_sources` должны присутствовать ровно одна роль `semantic_primary` и одна роль `machine_readable_primary`. Это не обязательно два пользовательских файла: нативный XHTML может иметь объединённую роль `semantic_primary+machine_readable_primary`, а для канонического DOCX source locator создаёт производный XHTML через `scripts/normalize_ft_source.py`. Производное представление должно буквально сохранять видимые автонумерованные метки Word, включая коды требований и подписи таблиц, а также количество таблиц и строк; иначе source stage остаётся `blocked-input`. Для машинной записи обязательно поле `origin: canonical|generated|supplied`; при `generated` также указываются `derived_from`, `derived_from_sha256` и `generator`.

`visual_crosscheck` принимает `required` или `not_required`. При `required` в `visual_sources` регистрируется хотя бы один PDF/рендер с ролью `visual_structural_crosscheck_only`. При `not_required` визуальный файл не создаётся, а `visual_crosscheck_reason` конкретно объясняет, почему расположение, рисунки и сложная разметка не влияют на смысл scope-ов. Все фактически находящиеся в `source/`, `support/` и `mockups/` файлы регистрируются; скрытое игнорирование входа запрещено. Файлы из `support/` регистрируются только в `support_sources`, файлы из `mockups/` — только в `visual_sources`; файлы из `source/` относятся к `primary_sources` либо `visual_sources` в зависимости от роли.

PDF/рендер при наличии проверяется визуально и структурно, но не становится источником бизнес-правил. Локальный PDF рендерится штатной командой `python scripts/render_runtime_pdf.py <source.pdf> --pages all`; для ограниченного фрагмента допустим `--pages 8-17` или список `--pages 8,10-12`. Helper открывает Unicode-пути напрямую, возвращает JSON с отдельными страницами и contact sheets и не требует ручного вызова Poppler. Рендеры и другие временные файлы создаются только в отдельном системном временном каталоге `ft-runtime-<назначение>-<случайный-id>`. После просмотра source locator передаёт возвращённый `output_dir` в `python scripts/cleanup_runtime_temp.py <absolute-temp-path>`; ручные рекурсивные команды удаления не используются. Новые файлы в repo-local `tmp/` после регистрации source-locator считаются ошибкой этапа.

Source locator классифицирует support, но не выполняет его предметный анализ. По умолчанию достаточно `AGENT-NOTES.md`, имени/формата, SHA-256 и при необходимости заголовков либо небольшого начального фрагмента. Объёмный справочник или файл ответов целиком читает scope analyzer только когда он относится к выбранному scope. Реализацию validator-а source locator не читает: использует документированную команду и диагностирует код только после реальной ошибки, которую нельзя понять из вывода.

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

Новый support-файл, предоставленный после scope analysis, регистрирует та же source-locator-сессия в существующих `source-selection.md` и `workflow-state.yaml`; `AGENT-NOTES.md` остаётся неизменным. Primary и visual selection не пересматриваются, semantic stages не выполняются. Поскольку downstream-артефакты к этому моменту ожидаемы, используется ограниченная проверка:

```text
python scripts/validate_runtime_source.py <FT-package> <source-handoff-dir> --support-update
```

Она по-прежнему проверяет полный набор локальных входов, роли, пути и SHA-256, но не считает уже существующие scope/matrix/TC и поздние временные файлы ошибкой первоначальной source-стадии.
