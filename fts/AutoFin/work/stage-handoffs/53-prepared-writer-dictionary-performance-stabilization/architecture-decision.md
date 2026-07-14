# Architecture Decision: runner-owned exhaustive dictionary

## Decision

Для `full-hierarchy` и `all-leaf-values` writer формирует исполнимую проверку через точный `DICT-*`, но не перечисляет два и более значения exhaustive набора. Полную иерархию ровно один раз добавляет runner до structure/obligation/quality gates и reviewer handoff.

## Ownership

- Immutable prepared package: полный source-backed набор и hierarchy paths.
- Writer-only context: identity, name, source location, coverage mode, value count и child `DICT-*` ids; exact leaf payload исключается.
- Structured writer: уникальный TC, действия, oracle и точная трассировка.
- Runner: deterministic materialization и exact completeness check.
- Reviewer: полный materialized draft и immutable dictionary evidence.

## Guardrails

- `writer-owned-exhaustive-dictionary-values` блокирует два и более exact labels внутри связанного exhaustive TC до materialization.
- `dictionary-projection-missing` и `dictionary-projection-incomplete` продолжают проверять полный итоговый набор.
- `reference-only` значения не сокращаются: writer сохраняет concrete value и unambiguous group path.
- Production test cases и принятый V3 draft не переписываются.

## Trade-off

Writer больше не может самостоятельно форматировать exhaustive list. Это намеренное ограничение: runner имеет более надёжный source-backed payload и уже отвечает за exact completeness. Семантическая свобода writer сохраняется для шагов и observable oracle.
