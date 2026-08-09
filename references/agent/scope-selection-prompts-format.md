# Scope Selection Prompts Format

`scope-selection-prompts.md` сопровождает `scope-options.md` только в режиме
`agent-proposed-scope`.

## Назначение

- дать пользователю короткий готовый prompt для выбора одного внешнего scope;
- не заставлять пользователя вручную восстанавливать `scope_slug` и FT-пакет;
- не дублировать постоянные инструкции, workflow или будущий маршрут.

## Расположение

До выбора scope файл хранится рядом с `scope-options.md` в контейнере
`fts/<ft-slug>/work/stage-handoffs/00-<container-slug>/`.

## Содержание

Для каждого варианта укажи только:

- `candidate_id`;
- `scope_order`;
- `scope_slug`;
- короткое русское название;
- готовый prompt.

## Рекомендуемый шаблон

```md
## Prompt Templates

### SCOPE-OPTION-001

**Scope Order:** `01`
**Scope Slug:** `2.1-lichnaya-informaciya`
**Название:** Личная информация

```text
Выполни ft-scope-analyzer для FT-пакета:
<FT package path>

Scope: `2.1-lichnaya-informaciya`
```
```

## Правила

- До выбора scope `workflow-state.yaml` имеет
  `stage_status: awaiting-user-scope-selection`; это не `blocked-input`.
- Prompt не перечисляет route restrictions, список будущих artifacts, reviewer
  mechanics или явные запреты, уже заданные постоянными инструкциями.
- Prompt не обещает writer, reviewer или canonical test cases: следующий этап
  лишь подтверждает выбранный scope.
- Все человекочитаемые поля — на русском языке.
