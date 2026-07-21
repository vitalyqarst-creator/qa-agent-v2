# Negative UI Calibration Policy

Contract for negative / requiredness obligations with unknown exact UI reaction.

## Enum

`oracle_status`: `source-backed | common-standard-backed | analyst-confirmed | ui-calibration-required | observed-ui-backed | not-testable-gap`.

- `ui-calibration-required`: first UI run must record the reaction.
- `not-testable-gap`: not enough source data for candidate TC.

## Decision

- `executable_tc`: exact oracle is source/common-standard/analyst/observed backed.
- `candidate_tc_required`: source defines value/format/length/date/mask/symbol/list/requiredness obligation, exact UI mechanism unknown.
- `gap_required`: no stable source anchor, input class, condition, or executable user action exists.

Visible source-backed input restriction with unknown UI rejection mechanism is `candidate_tc_required`, not gap-only. BA question/parent `GAP-*` may coexist, but cannot replace candidate-negative TC coverage.

Do not collapse child obligations into one parent `GAP-*`; each child keeps `scope_obligation_id`.

## Candidate TC

Candidate UI calibration is an oracle-status marker, not a title taxonomy. `**Название:**` must describe the business check and must not contain process markers such as `UI calibration`, `candidate`, `oracle`, `requires confirmation`, `требует подтверждения` or `требуется подтверждение`.

Required fields:

- `**Статус oracle:** ui-calibration-required`
- `**Статус тест-кейса:** candidate-ui-calibration`
- `**Требуется подтверждение:** <specific missing oracle question>`

Inventory row: `decision = candidate_tc_required`, `oracle_status = ui-calibration-required`, `planned_tc_or_gap`, `calibration_notes`.

Candidate TC requirements:

- contain a concrete representative invalid or empty-required value in `Тестовые данные` or in the action step;
- preserve positive allowed-class TC for the same source-backed restriction;
- do not replace a positive allowed-class TC with a negative candidate;
- do not invent exact UI rejection mechanism, message, color, filtering, clearing, blocking or save/no-save effect.

## Expected Result

Invalid value candidate:

> Недопустимое значение не должно быть принято как валидное. Конкретный наблюдаемый механизм отклонения требуется зафиксировать при UI calibration: символ не вводится / значение очищается / отображается сообщение / поле подсвечивается / блокируется переход или сохранение / значение не сохраняется / другое фактическое поведение.

Requiredness candidate:

> Пустое обязательное поле не должно быть принято как валидное для продолжения целевого пользовательского сценария. Конкретный механизм обязательности требуется зафиксировать при UI calibration: видимый маркер / сообщение / подсветка / блокировка перехода или сохранения / другое фактическое поведение.

Do not assert exact message, color, disabled state, filtering, clearing, blocked transition, or save/no-save behavior without evidence.

## Calibration

Record trigger, observed reaction, message if present, transition/save effect, evidence, and expected-result / `oracle_status` update.

After evidence: use one observed oracle, set `oracle_status = observed-ui-backed | analyst-confirmed`, remove candidate marker, do not rewrite FT-first baseline without evidence.

## Canonical Suite Status

Кандидаты остаются в общем canonical и сохраняют `TC-ID`. При их наличии metadata
содержит `execution_ready_count`, `calibration_candidate_count` и
`suite_readiness: ft-first-reviewed-with-calibration-pending`; набор нельзя называть
полностью исполнимым. Evidence обновляет тот же `TC-ID`.
