# Live smoke blocker: `codex exec`

Дата: `2026-07-10`.

Статус: `blocked-timeout`.

## Результат

Live writer был запущен через `codex-cli 0.144.0-alpha.4` в `workspace-write`, `--ephemeral`, `--json`. CLI успешно прошёл auth и создал новую session identity `019f4b84-a767-72f3-bf2b-14240b28f05e`, но за `600.453` секунды не записал обязательный draft.

Runner корректно:

- завершил stage как `outcome: blocked`, `timed_out: true`;
- сохранил Stage Contract v2 manifest/result, streams, events, status и metrics;
- не запустил reviewer;
- не запустил автоматический повтор writer;
- не создал `fts/AutoFin/test-cases/3-codex-exec-live-smoke-widget-selection-types.md`;
- не выполнил promotion и не создал fake final artifact.

## Scope И Inputs

- FT: `AutoFin`, section `3 Ограничения`.
- Scope: single-select list, multi-select list, default `NULL`.
- Source-backed inputs: `FT4AutoFinFinal.docx`, `.xhtml`, `.pdf` и подтверждённые handoff artifacts из `18-iteration-smoke-widget-selection-types`.
- Старые canary, persistence и generated test cases не использовались как source.
- Input contract: `14` artifacts, `38,777,538` bytes.

## Диагностика Latency

- JSONL: `560,222` bytes; runner captured `thread.started` и `turn.started`, но timeout произошёл до `turn.completed`.
- Token usage отсутствует по честной причине: CLI не выдал terminal usage event.
- В events зафиксированы `62` command execution items и `4` промежуточных agent messages.
- Agent самостоятельно подключил writer/table/doc/pdf workflows и выполнял полную source parity работу внутри stage вместо ранней записи минимального draft.
- Одна PDF-render попытка писала в `C:\tmp` и получила `Permission denied`; workspace-write корректно не разрешил внешний scratch path.
- Последнее содержательное сообщение сообщало о шести спроектированных проверках и одном gap, но chat progress не заменил обязательный файловый draft.

## Blocker И Следующее Исправление

Blocker не в auth или CLI availability. Текущий writer prompt/context слишком широк для быстрого stage-per-process запуска: он провоцирует повторный source-locator/design workflow и работу с крупными binary sources.

Перед новым live запуском нужны отдельные изменения:

1. Передавать writer подготовленный row-level extraction/handoff, а DOCX/PDF оставить evidence refs, не требующие повторной полной обработки внутри stage.
2. Явно ограничить stage budget и command count; требовать раннюю атомарную запись draft после проверки обязательных inputs.
3. Направлять весь scratch внутрь attempt-root.
4. Не запускать reviewer или comparative benchmark, пока writer не завершает этот scope с обязательным draft в установленный latency budget.
