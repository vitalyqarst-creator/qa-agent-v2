---
name: ft-source-locator
description: Выбирает и регистрирует источники одного FT-пакета.
---

# FT Source Locator

Используй только для регистрации входных материалов. До чтения FT-пакета прочитай `references/runtime/session-topology.md` и `references/runtime/source-selection.md`, затем проверь controller-owned registry командой `runtime_session_registry.py verify --through source-locator --expected-role source-locator --expected-thread-id <own-threadId>`. При ошибке остановись.

1. Проверь `AGENT-NOTES.md` в корне FT-пакета и прочитай его. Без файла остановись как `blocked-input`.
2. Найди основной DOCX, соответствующий XHTML и PDF. Без DOCX или XHTML остановись как `blocked-input`.
3. Зарегистрируй support-файлы, словари, макеты и Figma-ссылки с их ролями. Роль и приоритет, явно заданные в `AGENT-NOTES.md`, обязательны и не понижаются из-за возраста файла или упоминания старого процесса внутри него. Старые рабочие папки не являются состоянием текущего процесса, но извлечённые из них утверждённые ответы остаются действующим входом, если так указано в `AGENT-NOTES.md`. Макет/Figma — только visual input.
4. Запиши компактный русскоязычный `source-selection.md` и `workflow-state.yaml` в `work/stage-handoffs/00-<ft>/`. Пути, SHA-256, URL и имена файлов сохраняй без перевода.
5. Временные PDF-рендеры создавай только в системном временном каталоге и удали созданный каталог. Затем обязательно запусти `python scripts/validate_runtime_source.py <package-root> <source-handoff-dir>`. Без `valid=true` этап не завершён.

Если пользователь добавил support-файл после появления вопросов или downstream-артефактов, повторно используй ту же source-locator-сессию и выполни только регистрацию позднего support: добавь файл с точной ролью и SHA-256 в существующие `AGENT-NOTES.md`, `source-selection.md` и `workflow-state.yaml`, не перечитывая и не переанализируя primary sources. Для такой ограниченной операции запусти `python scripts/validate_runtime_source.py <package-root> <source-handoff-dir> --support-update`. Этот режим не разрешает пропускать новый support-файл и не создаёт новый source stage; он лишь не считает уже существующие scope/matrix/TC ошибкой source locator-а.

Не создавай scope, matrix, fixtures, вопросы БА или TC.
