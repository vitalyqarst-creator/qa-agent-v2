## Цель этапа

Провести следующую bounded итерацию по standard route: использовать новый deterministic self-block guard, выбрать один небольшой `standard-required` scope и сократить время до содержательного reviewer verdict без ослабления semantic gates.

## Входные артефакты

- `../20-prepared-autofin-cross-scope/source-selection.md`
- `../09-application-card-client-addresses/scope-contract.md`
- `../09-application-card-client-addresses/scope-coverage-gaps.md`
- `../09-application-card-client-addresses/scope-clarification-requests.md`
- `iteration-summary.md`
- `iteration-session-log.md`
- `agent-decision-log.md`
- `client-address-static-properties-canary-selection.md`
- `../../review-cycles/codex-exec-prepared-client-address-static-live-v2-20260711/cycle-state.yaml`
- `../../review-cycles/codex-exec-prepared-client-address-static-live-v2-20260711/promotion-dry-run.json`
- `../../../../../evals/prepared-obligation-rollout/20260711/compiler-matrix.md`
- `../../../../../evals/prepared-obligation-rollout/20260711/client-address-static-live-report.md`

## Обязательные действия

- Сохранить fast eligibility без изменений.
- Выбрать компактный standard scope по фактической матрице unsupported dimensions.
- Проверить deterministic writer readiness до запуска semantic reviewer.
- Запускать writer и reviewer только в новых отдельных сессиях и новом immutable cycle.
- Сравнить runtime и качество с standard widget-selection v4 без выдачи failed результата за эквивалентный acceptance.

## Не делать

- Не расширять static canary на conditional, integration, numeric или persistence behavior.
- Не выполнять production promotion eval-only canary.
- Не ослаблять obligation closure, fixture binding или semantic reviewer gates.
- Не повторять terminal cycle и не использовать старый attempt-bound package.

## Ожидаемые выходы

- Новый eval report standard-route iteration.
- Immutable writer/reviewer cycle evidence.
- Измерение времени, команд, context bytes и reviewer outcome.
- Отдельный checkpoint-коммит для исправлений и финальный handoff-коммит.

## Gate завершения

Этап завершён, когда standard draft либо проходит deterministic readiness и получает валидный semantic verdict, либо блокируется до reviewer с точной machine-readable причиной; production test cases при диагностическом запуске не изменяются.
