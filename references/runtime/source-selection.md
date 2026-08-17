# Контракт выбора источников

Source locator создаёт только:

- `AGENT-NOTES.md` с классификацией фактически доступных support-файлов;
- `work/stage-handoffs/00-<ft>/source-selection.md`;
- `work/stage-handoffs/00-<ft>/workflow-state.yaml`;
- controller-owned `work/runtime-session-registry.json` уже существует до начала этапа.

`workflow-state.yaml` содержит `stage: source-locator`, `status: completed`, путь к `source-selection.md`, списки `primary_sources`, `support_sources`, `visual_sources` и при наличии `figma_sources`. Для каждого локального файла обязательны repo-relative `path`, роль и SHA-256.

В `primary_sources` должны находиться ровно по одному существующему файлу ролей `semantic_primary`, `machine_readable_primary` и `visual_structural_crosscheck_only`. Все фактически находящиеся в `source/`, `support/` и `mockups/` файлы регистрируются; скрытое игнорирование входа запрещено.

PDF проверяется визуально и структурно, но не становится источником бизнес-правил. Рендеры и другие временные файлы создаются только в системном временном каталоге. Source locator удаляет созданный им временный каталог до завершения; новые файлы в repo-local `tmp/` после регистрации source-locator считаются ошибкой этапа.

До возврата результата обязательно выполнить:

```text
python scripts/validate_runtime_source.py <FT-package> <source-handoff-dir>
```

Validator проверяет registry, роли, пути, hashes, полноту регистрации локальных входов, отсутствие преждевременных downstream-артефактов и оставленных временных файлов. Самопроверка текстом или только `validate_runtime_tree.py` её не заменяет.
