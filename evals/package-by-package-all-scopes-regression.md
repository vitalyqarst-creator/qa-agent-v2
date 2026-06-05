# Package-by-package All Scopes Regression

## Цель

Проверить, что writer больше не создает плоский набор тест-кейсов по scope без internal work packages, даже если scope кажется простым.

## Regression Source

Дефект воспроизвелся на `ui-main-info`: writer создал большой плоский `Atomic Requirements Ledger`, generic atoms вида `Требование GSR N выполняется`, неисполняемые generic TC steps и TC с чрезмерным fan-in атомов.

## Входные Артефакты

- `scope-contract.md` подтвержденного scope.
- `scope-coverage-gaps.md`.
- `source-parity-check.md`, если доступны DOCX и PDF.
- `prompt.scope-to-writer.md` или `prompt.scope-to-iteration.md`.

## Must-pass Rules

1. `scope-contract.md` содержит `Внутренние Рабочие Пакеты` минимум с одним `WP-01`.
2. `prompt.scope-to-writer.md` явно требует package-by-package workflow.
3. Каждый `ATOM-*` имеет `package_id`.
4. Каждый `TC-*` имеет `package_id`.
5. Для каждого package есть package ledger gate и package TC gate.
6. Ledger не содержит generic atoms вроде `Требование GSR N выполняется`.
7. TC не содержат generic steps вроде `Выполнить проверяемое действие`.
8. TC не закрывает много независимых atoms без scenario/use-case rationale.

## Fail Criteria

- Scope обработан плоским списком atoms.
- Internal/API/model/RabbitMQ/DB behavior помечен `covered` без observable artifact.
- Requirement codes сохранены только как номера разделов или исчезли из traceability.
- Reviewer ставит `signed-off`, хотя package gates отсутствуют.

## Ожидаемый Результат

Reviewer возвращает `signed-off` только если package workflow виден в артефактах и все package-level gates пройдены. Иначе reviewer создает blocker findings категории `scope`, `traceability`, `test-design`, `test-case-format` или `atomarity`.
