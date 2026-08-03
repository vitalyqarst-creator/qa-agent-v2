# Scope Selection Prompts Format

Канонический `scope-selection-prompts.md` используется как сопроводительный артефакт к `scope-options.md` в режиме `agent-proposed-scope`.

## Назначение

- дать пользователю готовые prompt-шаблоны для выбора одного candidate scope;
- сократить ручную сборку следующего запроса после `scope-options.md`;
- не смешивать выбор scope с downstream handoff к writer или iteration.

## Расположение

- `fts/<ft-slug>/work/stage-handoffs/NN-<scope-slug>/scope-selection-prompts.md` для новых handoff-папок

Если один рабочий `scope-slug` еще не утвержден, файл может храниться рядом с `scope-options.md` во временном каталоге-контейнере stage handoff.

Для новых handoff-папок применяй numbered naming из `stage-handoff-model.md`: `00-<container-slug>` для контейнера выбора и `NN-<scope-slug>` для подтвержденного scope-level handoff.

## Когда использовать

- режим `agent-proposed-scope`;
- вместе с `scope-options.md`;
- до выпуска `scope-contract.md` и source-first handoff к независимому reviewer-у.

## Обязательные секции

- `## Как использовать`
- `## Prompt Templates`

## Что должно быть в prompt template

Для каждого candidate scope указывай:

- `candidate_id`;
- `scope_order`;
- `scope_slug`;
- `stage_handoff_dir`;
- краткое пояснение, что именно подтверждает пользователь;
- готовый prompt для перехода в `manual-scope`;
- явное указание, что новый production/promotion-capable маршрут не ведет напрямую к writer/iteration до `source_assertion_review`.

## Рекомендуемый шаблон

```md
## Как использовать

- Выбери один candidate scope из `scope-options.md`.
- Скопируй соответствующий prompt ниже.
- После подтверждения этого prompt агент должен выпустить `scope-contract.md`, `scope-coverage-gaps.md`, source-first artifacts и `prompt.scope-assertions-to-reviewer.md`.
- Writer/iteration стартуют только после accepted `source_assertion_review`; старые прямые writer/iteration prompts не являются output этого шага.

## Prompt Templates

### SCOPE-OPTION-001
**Scope Order:** `01`
**Scope Slug:** `2.1.1.1.1.1.2-lichnaya-informaciya`
**Stage Handoff Dir:** `01-2.1.1.1.1.1.2-lichnaya-informaciya`

```md
FT-пакет: `fts/<ft-slug>/...`
Этап: `ft-scope-analyzer`
Режим scope: `manual-scope`
Scope: `2.1.1.1.1.1.2-lichnaya-informaciya`
Stage handoff dir: `fts/<ft-slug>/work/stage-handoffs/01-2.1.1.1.1.1.2-lichnaya-informaciya/`
Задача: зафиксировать подтвержденный scope для дальнейшего написания тест-кейсов
Выходы: `scope-contract.md`, `scope-coverage-gaps.md`, `source-row-inventory.md` при row/table scope, `source-row-extraction-spec.json`, `source-row-baseline.json`, `source-assertions.json`, `prompt.scope-assertions-to-reviewer.md`, обновленный `workflow-state.yaml`
Следующий активный маршрут: `ft-test-case-reviewer` в режиме `source_assertion_review`
Ограничения: не расширять scope, не выходить за границы выбранного candidate scope
```
```

## Правила использования

- `scope-selection-prompts.md` не заменяет `scope-options.md`.
- Prompt templates из этого файла ведут только к подтверждению одного scope и выпуску source-first handoff.
- Пока пользователь не выбрал один конкретный scope, не создавай `prompt.scope-to-writer.md` или `prompt.scope-to-iteration.md`.
- Для нового production/promotion-capable workflow template не должен обещать `prompt.scope-to-writer.md` или `prompt.scope-to-iteration.md` как выход `manual-scope`; сначала требуется `prompt.scope-assertions-to-reviewer.md`.
- Prompt template должен явно указывать numbered handoff-папку, если она отличается от логического `scope_slug`.
- Все человекочитаемые поля должны быть на русском языке.
