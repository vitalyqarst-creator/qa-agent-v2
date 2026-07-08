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

Do not collapse child obligations into one parent `GAP-*`; each child keeps `scope_obligation_id`.

## Candidate TC

Required fields:

- `**Статус oracle:** ui-calibration-required`
- `**Статус тест-кейса:** candidate-ui-calibration`
- `**Что нужно зафиксировать при UI calibration:** ...`

Inventory row: `decision = candidate_tc_required`, `oracle_status = ui-calibration-required`, `planned_tc_or_gap`, `calibration_notes`.

## Expected Result

Invalid value candidate:

> Недопустимое значение не должно быть принято как валидное. Конкретный наблюдаемый механизм отклонения требуется зафиксировать при UI calibration: символ не вводится / значение очищается / отображается сообщение / поле подсвечивается / блокируется переход или сохранение / значение не сохраняется / другое фактическое поведение.

Requiredness candidate:

> Пустое обязательное поле не должно быть принято как валидное для продолжения целевого пользовательского сценария. Конкретный механизм обязательности требуется зафиксировать при UI calibration: видимый маркер / сообщение / подсветка / блокировка перехода или сохранения / другое фактическое поведение.

Do not assert exact message, color, disabled state, filtering, clearing, blocked transition, or save/no-save behavior without evidence.

## Calibration

Record trigger, observed reaction, message if present, transition/save effect, evidence, and expected-result / `oracle_status` update.

After evidence: use one observed oracle, set `oracle_status = observed-ui-backed | analyst-confirmed`, remove candidate marker, do not rewrite FT-first baseline without evidence.
