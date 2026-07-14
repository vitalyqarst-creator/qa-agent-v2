# Architecture Decision V6

## Decision

Добавить guarded package-context projection перед writer/reviewer prompts: удалять только H2 DaData из mandatory package notes, если выбранное evidence вне этого блока не содержит DaData behavior.

## Why

- V5 передал один и тот же большой нерелевантный DaData раздел двум отдельным sessions.
- `AGENT-NOTES.md` остаётся обязательным: релевантная расшифровка `О/Р` сохраняется.
- Для DaData scope полный раздел сохраняется; тест покрывает обе ветки.

## Rejected Alternatives

- сокращать atomic statements/oracles: ухудшает независимый semantic review;
- убирать reviewer draft: нарушает независимую проверку результата writer-а;
- объединять writer/reviewer session: противоречит целевой архитектуре отдельных этапов;
- приписывать все uncached tokens repo prompt: event stream не даёт такого attribution.
