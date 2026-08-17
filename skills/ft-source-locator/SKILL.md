---
name: ft-source-locator
description: Выбирает и регистрирует источники одного FT-пакета.
---

# FT Source Locator

Используй только для регистрации входных материалов. До чтения FT-пакета прочитай `references/runtime/session-topology.md` и проверь controller-owned registry командой `runtime_session_registry.py verify --through source-locator --expected-role source-locator --expected-thread-id <own-threadId>`. При ошибке остановись.

1. Проверь `AGENT-NOTES.md` в корне FT-пакета и прочитай его. Без файла остановись как `blocked-input`.
2. Найди основной DOCX, соответствующий XHTML и PDF. Без DOCX или XHTML остановись как `blocked-input`.
3. Зарегистрируй support-файлы, словари, макеты и Figma-ссылки с их ролями. Роль и приоритет, явно заданные в `AGENT-NOTES.md`, обязательны и не понижаются из-за возраста файла или упоминания старого процесса внутри него. Старые рабочие папки не являются состоянием текущего процесса, но извлечённые из них утверждённые ответы остаются действующим входом, если так указано в `AGENT-NOTES.md`. Макет/Figma — только visual input.
4. Запиши компактный русскоязычный `source-selection.md` и `workflow-state.yaml` в `work/stage-handoffs/00-<ft>/`. Пути, SHA-256, URL и имена файлов сохраняй без перевода.

Не создавай scope, matrix, fixtures, вопросы БА или TC.
