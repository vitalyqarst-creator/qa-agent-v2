---
name: ft-source-locator
description: Выбирает и регистрирует источники одного FT-пакета.
---

# FT Source Locator

Используй только для регистрации входных материалов.

1. Проверь `AGENT-NOTES.md` в корне FT-пакета и прочитай его. Без файла остановись как `blocked-input`.
2. Найди основной DOCX, соответствующий XHTML и PDF. Без DOCX или XHTML остановись как `blocked-input`.
3. Зарегистрируй support-файлы, словари, макеты и Figma-ссылки с их ролями. Макет/Figma — только visual input.
4. Запиши компактный `source-selection.md` и `workflow-state.yaml` в `work/stage-handoffs/00-<ft>/`.

Не создавай scope, matrix, fixtures, вопросы БА или TC.
