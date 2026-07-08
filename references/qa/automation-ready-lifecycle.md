# Automation-Ready Lifecycle

Канонические правила жизненного цикла `automation-ready` версии тест-кейсов.

## Назначение

- `automation-ready` не является FT-first baseline.
- `automation-ready` не появляется как побочный эффект первого UI-прогона.
- `automation-ready` — это отдельный рабочий артефакт для исполнимого UI-прогона и дальнейшего handoff в автоматизацию.

## Базовая цепочка

1. `baseline test-cases`
2. `initial automation-ready`
3. `UI rerun`
4. `updated automation-ready`

Формула:

`fts/<ft-slug>/test-cases/<section-id>-<scope>.md`
-> `fts/<ft-slug>/test-cases/automation-ready/<section-id>-<scope>.md`
-> `fts/<ft-slug>/work/ui-automation-prep/<scope>/ui-validation-report.md`
-> `fts/<ft-slug>/work/ui-automation-prep/<scope>/ui-evidence-index.md`

## Когда разрешено создавать initial automation-ready

Если для нужного scope:

- в `fts/<ft-slug>/test-cases/automation-ready/` файла еще нет;
- в `fts/<ft-slug>/test-cases/` baseline файл уже есть;
- набор уже пригоден как вход для `ft-ui-automation-prep`;

агенту разрешено самостоятельно создать initial `automation-ready` файл на основе baseline.

Если baseline файла нет, агент не должен создавать `automation-ready` с нуля.

## Фаза 1. Создание initial automation-ready

Источник:

- baseline файл из `fts/<ft-slug>/test-cases/`

Результат:

- парный файл в `fts/<ft-slug>/test-cases/automation-ready/`

На этой фазе агент должен:

- не менять baseline FT-first файл;
- не выдумывать новое поведение системы;
- не использовать старые UI-артефакты как источник требований;
- сохранить трассируемость к baseline кейсу и ФТ;
- преобразовать baseline кейсы в исполнимую для UI-прогона форму;
- добавить недостающие технические шаги только если они нужны для воспроизводимого прохождения.
- не считать кейс automation-ready, если `Предусловия` требуют специального UI-состояния, но дают только пассивное состояние без numbered action setup steps, fixture/API setup или reusable setup profile. `Дождаться...` / `Убедиться...` допустимо только после setup-действия, которое создает это состояние.

На этой фазе агент не должен:

- проставлять `confirmed`, `mismatch-ft-ui`, `blocked-*` только потому, что кейс подготовлен;
- переписывать expected result под предполагаемое UI behavior без реального прогона;
- считать пользовательский комментарий, старый screenshot или старый report достаточным основанием для смены смысла кейса.

## Фаза 2. UI rerun и актуализация automation-ready

Только после создания initial `automation-ready` агент использует его как входной файл для `ft-ui-automation-prep`.

На этой фазе агент:

- проходит кейсы в реальном UI;
- собирает Playwright evidence;
- обновляет `ui-validation-report.md`;
- обновляет `ui-evidence-index.md`;
- актуализирует `automation-ready` по фактически подтвержденному UI behavior;
- при необходимости обновляет агрегирующие списки неподтвержденных кейсов.

## Правила обновления после UI-прогона

- Baseline FT-first файл не перезаписывается.
- Если UI flow воспроизводится, но расходится с FT:
  - в `automation-ready` отражается реальный executable flow;
  - обязательно остается явный блок `FT/UI Divergence`.
- Если для воспроизведения нужен дополнительный шаг, неочевидный из baseline:
  - этот шаг нужно добавить в сам `automation-ready` кейс;
  - нельзя оставлять его только в `Automation Notes`.
- Статус кейса меняется только после фактического UI-прогона.

## Разделение ответственности артефактов

`test-cases/`

- FT-first baseline;
- источник требований для initial `automation-ready`;
- не перезаписывается в `ft-ui-automation-prep`.

`test-cases/automation-ready/`

- рабочая исполнимая версия baseline;
- сначала создается из baseline;
- потом актуализируется по результатам UI-прогона.

`work/ui-automation-prep/<scope>/ui-validation-report.md`

- фиксирует результаты фактического UI-прогона;
- не является источником требований.

`work/ui-automation-prep/<scope>/ui-evidence-index.md`

- индексирует evidence фактического UI-прогона;
- не является источником требований.

## Guardrails

- Если `automation-ready` уже существует, агент не должен пересоздавать его с нуля без явной причины.
- Если `automation-ready` отсутствует, но baseline есть, агент должен:
  1. сначала создать initial `automation-ready`;
  2. только потом переходить к UI-прогону.
- Если отсутствуют и baseline, и `automation-ready`, агент должен остановиться и зафиксировать отсутствие входного артефакта.

## UI Access Stop Condition

Если во время `ft-ui-automation-prep` агент не может получить доступ к рабочему UI после 2 последовательных попыток входа, включая не менее 1 fallback-способа, он должен остановить UI-прогон и зафиксировать блокировку в результатах. Продолжать попытки, менять runtime URL или использовать launcher/workaround-разработки можно только после явного подтверждения.
