# FT Package `AGENT-NOTES.md` Template

Используй этот шаблон для package-specific файла:

- `fts/<ft-slug>/AGENT-NOTES.md`

Цель файла:

- зафиксировать нюансы конкретного FT-пакета, которые должны переживать отдельные сессии;
- дать агенту package-specific context, который не является ни глобальным policy, ни phase-specific workflow;
- уменьшить зависимость от памяти предыдущих сессий.

## Когда нужен `AGENT-NOTES.md`

Создавай файл, если для конкретного FT-пакета есть хотя бы одно из следующего:

- важные сокращения или локальная терминология;
- особые правила чтения требований;
- package-specific ограничения scope;
- package-specific helper artifacts;
- устоявшиеся оговорки, которые агент должен учитывать во всех новых сессиях по этому пакету.

## Что туда помещать

- идентификацию пакета и основного ФТ;
- что считать источником истины именно для этого пакета;
- package-specific расшифровки сокращений и локальных терминов;
- package-specific cautions и known pitfalls;
- ссылки на helper artifacts внутри этого FT-пакета;
- правила сохранения результатов для этого пакета.

## Что туда не помещать

- глобальные правила проекта;
- phase-specific workflow locator / analyzer / writer / reviewer / iteration;
- общие QA-шаблоны и форматы;
- содержимое, которое уже канонически живет в `references/`.
- phase-specific UI operational notes для `ft-ui-automation-prep`, если для них подходит `fts/<ft-slug>/work/ui-automation-prep/UI-AGENT-NOTES.md`.

## Рекомендуемая структура

```md
# AGENT NOTES: <short FT name>

Этот файл содержит package-specific заметки для агента по ФТ:

- `<full FT document name>`

Используй его как обязательный контекст после выбора FT-пакета `<ft-slug>` и до анализа scope, написания тест-кейсов или review.

## Что считать источником истины

- Основной источник требований: `source/<main-doc>.docx`
- PDF того же ФТ обязателен для structural cross-check границ разделов и scope.
- `support/` и `mockups/` используются только как связанные материалы того же пакета.
- При расхождении приоритет у текста основного ФТ.

## Что важно именно для этого пакета

- `<package-specific nuance 1>`
- `<package-specific nuance 2>`

## Как работать по этому ФТ

- `<scope / slicing guidance 1>`
- `<scope / slicing guidance 2>`

## Готовые helper artifacts

- `<artifact path or description>`

## Куда сохранять результаты

- Финальные тест-кейсы:
  - `fts/<ft-slug>/test-cases/`
- Промежуточные артефакты session-based review-cycle:
  - `fts/<ft-slug>/work/review-cycles/<scope-slug>/`

## Что не делать

- `<package-specific anti-pattern 1>`
- `<package-specific anti-pattern 2>`
```

## Правило использования

Если в корне FT-пакета есть `AGENT-NOTES.md`, агент должен:

1. прочитать его сразу после выбора FT-пакета;
2. учитывать его как обязательный package-specific context;
3. не дублировать его содержимое в skill-ах или в глобальном `AGENTS.md`, если для него уже есть канонический источник.
4. не смешивать его с отдельными UI operational notes, если для пакета используется `work/ui-automation-prep/UI-AGENT-NOTES.md`.
