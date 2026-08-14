# Scope Selection Prompts Format

`scope-selection-prompts.md` сопровождает `scope-options.md` только в режиме
`agent-proposed-scope`.

## Назначение

- дать пользователю короткий готовый prompt для выбора одного внешнего scope;
- не заставлять пользователя вручную восстанавливать `scope_slug` и FT-пакет;
- не дублировать постоянные инструкции, workflow или будущий маршрут.

## Расположение

До выбора scope файл хранится рядом с `scope-options.md` в package-level
каталоге `fts/<ft-slug>/work/practical-v0.9/scope-selection/`.

## Содержание

Для каждого варианта укажи только:

- `candidate_id`;
- `scope_order`;
- `scope_slug`;
- короткое русское название;
- готовый prompt.

## Рекомендуемый шаблон

```md
## Шаблоны prompt для выбора scope

### SCOPE-OPTION-001

**Порядок области:** `01`
**Идентификатор области:** `2.1-lichnaya-informaciya`
**Название:** Личная информация

```text
Выполни ft-scope-analyzer для FT-пакета:
<FT package path>

Scope: `2.1-lichnaya-informaciya`
```
```

## Правила

- До выбора scope `workflow-state.json` не создаётся; ожидание выбора
  пользователя не является `blocked-input`.
- Prompt не перечисляет route restrictions, список будущих artifacts, reviewer
  mechanics или явные запреты, уже заданные постоянными инструкциями.
- Prompt не обещает writer, reviewer или canonical test cases: следующий этап
  лишь подтверждает выбранный scope.
- Все человекочитаемые поля — на русском языке.
