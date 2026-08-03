# Risk / Priority Map Format

`risk-priority-map.md` - split artifact в `work/test-design/<scope-slug>/`, который связывает риск requirement atoms с приоритетом тестов и residual risk decisions. Он обязателен, если scope содержит high-risk dimensions или high-risk atoms.

High-risk dimensions обычно включают `role-permission`, `status-lifecycle`, `api-server-validation`, `integration`, `security`, `file-upload`, `calculation`, а также любые атомы про деньги, доступы, потерю/искажение данных, необратимые статусы, критичную бизнес-валидацию или внешние side effects.

## Risk / Priority Map

| atom_id | coverage_dimension | impact | likelihood | risk_score | risk_level | risk_factors | source_ref | required_priority | linked_test_cases | gap_id | residual_risk_decision | rationale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ATOM-012` | `numeric` | `4` | `3` | `12` | `high` | `money; server-side-rejection` | `GSR 124` | `High` | `TC-EMP-004; TC-EMP-005` | `-` | `none` | `Неверная сумма влияет на решение заявки` |

## Scoring

- `impact`: `1` negligible, `2` minor, `3` moderate, `4` major, `5` critical.
- `likelihood`: `1` rare, `2` unlikely, `3` possible, `4` likely, `5` frequent.
- `risk_score = impact x likelihood`.
- `risk_level`: `high` при `score >= 12` или `impact = 5`; `medium` при `score 6..11`; `low` при `score <= 5`, если нет high-risk override.

## Rules

- `risk_level = high` требует `required_priority = High`.
- High-risk atom должен ссылаться на `TC-*` с `Priority: High` или на blocking `GAP-*`.
- Low-frequency/high-impact атом не понижается до low только из-за редкости: `impact = 5` всегда high.
- `residual_risk_decision` допустим только как `none | accepted-with-gap | deferred-by-scope | blocked-input`. Accepted residual risk не превращает gap в covered requirement.
- Если expected result для high-risk atom не выводится из source, создай blocking `GAP-*`; не снижай priority, чтобы пройти gate.
- Priority не является порядком выполнения, удобством automation или субъективной важностью раздела.

