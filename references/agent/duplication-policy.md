# Duplication Policy

В проекте действует правило единственного источника истины.

## Канонические зоны

- `AGENTS.md` - global policy и routing.
- `skills/*/SKILL.md` - phase-specific workflow.
- `references/agent/` - правила архитектуры агентного слоя.
- `references/qa/` - стабильные QA-правила, формат и трассировка.
- `fts/<ft-slug>/work/test-design/<scope>/` - единственный источник table-heavy writer artifacts для конкретного scope.
- `fts/<ft-slug>/test-cases/` - canonical `TC-*` набор, ссылки на split artifacts и краткое summary без полных копий таблиц.
- `test_case_agent/` - техническое исполнение.

## Допустимое повторение

Допустимы только:

- короткие ссылки на канонический документ;
- краткое напоминание без копирования полного правила;
- UI metadata в `agents/openai.yaml`.

## Недопустимое повторение

- одинаковые procedural steps в `AGENTS.md` и `SKILL.md`;
- одинаковые QA rules в нескольких `SKILL.md`;
- копии shared references внутри конкретного skill-а без веской причины;
- доменные policy-тексты внутри кода или helper scripts.
- полные копии `Source Table Normalization`, `Test Design Decision Table`, ledger, design plan, coverage gaps или gate одновременно в `work/test-design/<scope>/` и canonical test-case file.


