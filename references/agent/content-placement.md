# Content Placement

Этот документ задает каноническое размещение знаний в проекте.

## Что хранить в `AGENTS.md`

- роль агента;
- глобальные запреты;
- общие критерии качества результата;
- маршрутизацию между skill-ами;
- правило единственного источника истины.

## Что хранить в `skills/*/SKILL.md`

- phase-specific workflow;
- входы и выходы skill-а;
- триггеры использования;
- ограничения skill-а;
- ссылки на канонические references.

## Что хранить в `references/`

- стабильные, переиспользуемые документы;
- шаблоны и форматы;
- правила трассировки;
- границы ответственности;
- чек-листы архитектурного аудита.
- manifest-ы выбора instruction context, если они описывают только какие инструкции читать для сценария, а не сами QA/workflow правила.

## Что хранить в `fts/<ft-slug>/AGENT-NOTES.md`

- package-specific заметки для конкретного FT-пакета;
- локальные сокращения и термины;
- package-specific cautions и нюансы чтения требований;
- ссылки на helper artifacts этого пакета;
- указания, которые должны учитываться во всех новых сессиях по данному FT, но не являются глобальными правилами проекта.

## Что хранить в `fts/<ft-slug>/work/ui-automation-prep/UI-AGENT-NOTES.md`

- package-level operational notes именно для фазы `ft-ui-automation-prep`;
- runtime URL и entrypoints для UI-прогонов;
- test credentials и правила авторизации, если их допустимо хранить в репозитории;
- устойчивые сценарии создания тестовых данных и стартовых сущностей;
- package-specific UI pitfalls и воспроизводимые setup-правила, которые должны переживать отдельные UI-сессии.

## Что хранить в `fts/<ft-slug>/work/test-design/<scope>/`

- table-heavy writer artifacts: `Source Row Inventory`, `Source Table Normalization`, `Test Design Decision Table`, `Atomic Requirements Ledger`, `Package Test Design Plan`, `Test Design Review`, `Coverage Gaps`, `Writer Quality Gate` и связанные matrices;
- один canonical artifact на каждый тип таблицы для конкретного scope;
- данные, на которые reviewer/validator должны ссылаться как на источник истины перед чтением `TC-*`.

Canonical test-case file в `test-cases/` хранит ссылки, краткое summary и сами `TC-*`, но не полные копии этих таблиц.

## Что хранить в коде

- техническое исполнение;
- API, модели и скрипты;
- автоматические проверки.

## Что не делать

- не копировать один и тот же procedural workflow в `AGENTS.md` и в skill;
- не хранить доменные policy-тексты в коде;
- не использовать skill как еще одно место для глобальных правил, если они уже есть в `AGENTS.md`.
- не складывать package-specific нюансы конкретного FT в глобальный `AGENTS.md`, если для них подходит `fts/<ft-slug>/AGENT-NOTES.md`.
- не смешивать package-wide FT notes из `fts/<ft-slug>/AGENT-NOTES.md` с phase-specific UI operational notes, если для них подходит `fts/<ft-slug>/work/ui-automation-prep/UI-AGENT-NOTES.md`.


