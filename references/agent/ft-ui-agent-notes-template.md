# FT Package `UI-AGENT-NOTES.md` Template

Используй этот шаблон для package-level UI notes:

- `fts/<ft-slug>/work/ui-automation-prep/UI-AGENT-NOTES.md`

Цель файла:

- зафиксировать package-level operational notes для фазы `ft-ui-automation-prep`;
- дать агенту устойчивый UI runtime context, который должен переживать отдельные UI-сессии;
- уменьшить зависимость от памяти предыдущих прогонов.

## Когда нужен `UI-AGENT-NOTES.md`

Создавай файл, если для конкретного FT-пакета есть хотя бы одно из следующего:

- стабильный runtime URL или набор entrypoints для UI-прогонов;
- test credentials, допустимые для хранения в репозитории;
- устойчивый flow создания тестовых заявок или других стартовых сущностей;
- package-level UI pitfalls или setup-правила, которые агент должен учитывать именно в `ft-ui-automation-prep`;
- operational notes, которые не являются ни правилами ФТ, ни per-scope результатами прогона.

## Что туда помещать

- URL стенда и стартовые маршруты;
- логин/пароль и правила повторного использования storage state, если это допустимо;
- пошаговый сценарий создания тестовых данных;
- package-level договоренности по UI-прогонам;
- устойчивые operational notes, полезные во всех новых UI-сессиях по этому пакету.

## Что туда не помещать

- текст требований ФТ и трактовки бизнес-логики как источник истины;
- глобальные правила проекта;
- per-scope результаты прогонов;
- `ui-validation-report.md`, `ui-evidence-index.md` и `automation-ready` содержимое;
- изменения статусов кейсов без фактической UI-проверки.

## Рекомендуемая структура

```md
# UI AGENT NOTES: <short FT name>

Этот файл содержит package-specific operational notes для UI-прогонов по FT-пакету `<ft-slug>`.

Используй его только на этапе `ft-ui-automation-prep`.
Не используй его как источник требований ФТ и не подменяй им `fts/<ft-slug>/AGENT-NOTES.md`.

## Доступ к стенду

- Стартовый экран:
  - `<url>`
- Рабочий runtime entrypoint:
  - `<url>`
- Логин:
  - `<login>`
- Пароль:
  - `<password>`

## Авторизация

- `<storage state rule>`

## Создание тестовой сущности

1. `<step 1>`
2. `<step 2>`
3. `<step 3>`

## Рабочие договоренности для UI-прогонов

- `<rule 1>`
- `<rule 2>`

## Что не делать

- `<anti-pattern 1>`
- `<anti-pattern 2>`
```
