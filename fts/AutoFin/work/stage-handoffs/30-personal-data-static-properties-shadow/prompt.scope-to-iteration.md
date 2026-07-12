# Следующая итерация prepared process

## Цель этапа

Устранить обнаруженные process gaps prepared compiler/reviewer и повторить тот же immutable shadow scope без лишнего live cycle.

## Входные артефакты

- `work/stage-handoffs/20-prepared-autofin-cross-scope/source-selection.md`;
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-contract.md`;
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/scope-coverage-gaps.md`;
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-parity-check.md`;
- `work/stage-handoffs/29-application-card-client-personal-data-current-source-rebase/source-row-inventory.md`;
- `work/stage-handoffs/30-personal-data-static-properties-shadow/workflow-state.yaml`;
- `work/stage-handoffs/30-personal-data-static-properties-shadow/scope-selection.md`;
- `work/stage-handoffs/30-personal-data-static-properties-shadow/iteration-summary.md`;
- `work/stage-handoffs/30-personal-data-static-properties-shadow/iteration-session-log.md`;
- `work/stage-handoffs/30-personal-data-static-properties-shadow/agent-decision-log.md`;
- `work/stage-handoffs/30-personal-data-static-properties-shadow/compiler-inputs/personal-data-static-properties/compiler-input.yaml`;
- `work/review-cycles/personal-data-static-properties-shadow-20260712/cycle-state.yaml`;
- `work/review-cycles/personal-data-static-properties-shadow-v2-20260712/cycle-state.yaml`.

## Обязательные действия

1. Добавить compiler preflight, который блокирует input-based obligation до live exec, если plan не содержит конкретного synthetic/source-backed fixture.
2. Добавить deterministic diagnostic для test cases с одинаковыми нормализованными шагами и итоговым expected result при разных названиях/obligations.
3. Оставить overlap diagnostic неблокирующим до классификации допустимых multi-obligation и действительно избыточных пар.
4. Повторить этот же immutable shadow scope новым cycle ID через `codex exec`, без SDK fallback, promotion и production write.

## Не делать

- Не использовать прежние или production test cases как requirement evidence.
- Не расширять micro-scope на format, DaData, conditional behavior или соседние поля.
- Не изменять `test-cases/14-application-card-client-personal-data.md` и не создавать shadow target в `test-cases/`.

## Ожидаемые выходы

- compiler diagnostic и regression tests для отсутствующего concrete fixture;
- overlap diagnostic, classification policy и regression tests;
- новый immutable shadow cycle и performance report;
- обновленные `iteration-summary.md`, session log, decision log и `workflow-state.yaml`.

## Gate завершения

Этап завершен, когда preflight не допускает fixture-less package до live writer, failed-cycle overhead отсутствует, obligations покрыты или обоснованно объединены, titles уникальны, reviewer принимает draft и production baseline остается неизменным.
