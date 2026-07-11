# Итог prepared obligation rollout

## Что исправлено

- `client-addresses`: закрыты 27 отсутствовавших atom-to-obligation mappings.
- `document-files`: закрыты 47 отсутствовавших mappings; legacy gap IDs для date feedback и archive role access канонизированы.
- `document-recognition`: удалён фиктивный `OBL-N/A-001`, создан полный набор из 9 obligations.
- Evidence-qualified statuses сохраняются и автоматически требуют standard route.
- Compiler выдаёт machine-readable closure diagnostics с artifact/line anchors.
- Повторяющиеся atom/plan evidence строки дедуплицируются без потери structured obligations.

## Матрица

- Все девять исходных scope компилируются: `9/9`.
- Widget selection остаётся единственным fast scope исходной матрицы.
- Остальные восемь корректно route-ятся в standard по state/navigation/dependency/file/integration/numeric/lifecycle dimensions.

## Второй fast canary

Eval-only проекция `client-address-static-properties`:

| run | result | total | quality |
| --- | --- | ---: | --- |
| v1 | `accepted-not-promoted` | 120.768 s | 6/6 obligations, 0 findings |
| v2 | `accepted-promotion-dry-run` | 120.741 s | 6/6 obligations, 0 findings |

- Writer/reviewer использовали четыре разные backend sessions.
- Promotion dry-run прошёл; production write не выполнялся.
- Replay terminal cycle отклонён, state hash не изменился.
- Canary target остался отсутствующим.

## Standard-route guard

Standard writer output теперь блокируется до reviewer, если draft явно содержит `requires-binding`, сообщает blocked Writer Quality Gate или `0/N` execution-ready cases. Это сокращает дорогой review заведомо неисполняемого draft; semantic reviewer остаётся обязательным для прошедших deterministic gates результатов.

## Production decision

Реальный promotion не выполнен. Canary является eval-only проекцией и не должен создавать конкурирующий production baseline. Следующий production pilot должен использовать отдельный подтверждённый scope, а не расширять эту проекцию.

## Canonical reports

- `evals/prepared-obligation-rollout/20260711/compiler-matrix.md`.
- `evals/prepared-obligation-rollout/20260711/client-address-static-live-report.md`.
