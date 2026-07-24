# Scope Options Format

Канонический `scope-options.md` используется как результат режима `agent-proposed-scope`, когда агент должен сначала предложить разбиение FT на candidate scope, а не сразу выпускать `scope-contract.md`.

## Назначение

- зафиксировать candidate scope для большого или неоднозначного FT;
- дать пользователю воспроизводимый список вариантов, а не одноразовый ответ в чате;
- отделить проектирование scope от подтвержденного source-first handoff.

## Расположение

- `fts/<ft-slug>/work/stage-handoffs/NN-<scope-slug>/scope-options.md` для новых handoff-папок

Если пользователь еще не утвердил один конкретный рабочий `scope-slug`, допускается временный каталог-контейнер для stage handoff, в котором `scope-options.md` хранит shortlist вариантов до выбора одного scope.

Для новых handoff-папок применяй numbered naming из `stage-handoff-model.md`:

- контейнер candidate scope-ов: `fts/<ft-slug>/work/stage-handoffs/00-<container-slug>/scope-options.md`;
- подтвержденный scope: `fts/<ft-slug>/work/stage-handoffs/NN-<scope-slug>/scope-options.md`, если файл нужен в scope-level handoff.

## Когда использовать

- режим `agent-proposed-scope`;
- FT слишком большой для безопасного single-scope старта;
- пользователь не уверен, как правильно дробить документ;
- нужно зафиксировать несколько candidate scope перед утверждением одного из них.

## Правило Декомпозиции

Для большого ФТ, всего документа или нескольких разнородных разделов сначала формируй внешние candidate scope-ы по разделам ФТ. Если раздел объемный или смешивает разные test-design domains, дроби его по подразделам или самостоятельным функциональным блокам.

Не создавай стандартный candidate scope вида `all-sections`, `all-sections-without-bp`, `whole-ft` или аналогичный для большого ФТ. Такой широкий scope допустим только как явно подтвержденное исключение после предупреждения о рисках.

Внутренние рабочие пакеты не перечисляются вместо внешних candidate scope-ов. Они появляются позже в `scope-contract.md` только внутри одного уже выбранного внешнего scope.

Каноническое правило: `references/agent/scope-decomposition-policy.md`.

## Обязательные секции

- `## Контекст`
- `## Candidate Scope`
- `## Рекомендация`
- `## Что нужно от пользователя дальше`

## Что должно быть в каждом candidate scope

Для каждого candidate scope указывай:

- `scope_order` — двухзначный номер в рекомендуемом порядке работы;
- `scope_slug` или временный стабильный идентификатор;
- `stage_handoff_dir` — будущая numbered-папка вида `NN-<scope-slug>`;
- `title`;
- `source_path`;
- `что входит`;
- `что не входит`;
- `почему это отдельный scope`;
- `примерная сложность`;
- `риски / coverage gaps`;
- `рекомендуемый следующий шаг`.

## Рекомендуемый шаблон

```md
## Контекст

- FT-пакет: `fts/<ft-slug>/...`
- Основной источник: `...`
- Режим: `agent-proposed-scope`
- Цель разбиения: `...`

## Candidate Scope

### SCOPE-OPTION-001
**Scope Order:** `01`
**Scope Slug:** `2.1.1.1.1.1.2-lichnaya-informaciya`
**Stage Handoff Dir:** `01-2.1.1.1.1.1.2-lichnaya-informaciya`
**Title:** Личная информация
**Source Path:** `2.1.1.1.1.1.2 -> Блок "Личная информация"`

**Что входит:** ...
**Что не входит:** ...
**Почему это отдельный scope:** ...
**Примерная сложность:** low | medium | high
**Риски / Coverage Gaps:** ...
**Рекомендуемый следующий шаг:** ...

## Рекомендация

- С чего начать: `...`
- Почему: `...`

## Что нужно от пользователя дальше

- Выбрать один candidate scope для перехода в `manual-scope`.
```

## Правила использования

- `scope-options.md` не заменяет `scope-contract.md`.
- Пока пользователь не утвердил один конкретный scope, не создавай `prompt.scope-to-writer.md` или `prompt.scope-to-iteration.md`.
- После выбора одного candidate scope следующий шаг должен выпускать `scope-contract.md`, `scope-coverage-gaps.md`, source-first artifacts и `prompt.scope-assertions-to-reviewer.md`.
- Writer/iteration prompts появляются только после accepted `source_assertion_review` либо в явно legacy/non-promotion route.
- Для новых candidate scope-ов фиксируй `Scope Order` и `Stage Handoff Dir`, чтобы пользователю не приходилось восстанавливать порядок по содержимому файлов.
- Все человекочитаемые поля должны быть на русском языке.
