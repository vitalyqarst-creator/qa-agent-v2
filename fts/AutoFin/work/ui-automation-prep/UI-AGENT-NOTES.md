# UI Agent Notes: AutoFin

Этот файл содержит package-specific operational notes для UI-прогонов AutoFin. Используй его только в фазе `ft-ui-automation-prep`; он не является источником требований.

## DaData Calibration

Если automation-ready scope включает поле с подтверждённой FT-интеграцией DaData:

- сначала прочитай `fts/AutoFin/work/vendor-references/dadata-reference.md`;
- выполняй проверку через normal UI path, без DOM-seeded подмены результата;
- сохраняй screenshot для подтверждённого FT-поведения;
- при расхождении с FT сохраняй screenshot и trace, если Playwright доступен;
- заполняй calibration table из vendor reference фактами наблюдения, не предполагаемыми правилами;
- отличай `confirmed-ft`, `observed-vendor-aligned`, `vendor-variation`, `mismatch-ft-ui`, `not-observed`, `blocked-observability` и `coverage-gap`;
- уточняй только automation-ready шаги и oracle, подтверждённые evidence; FT-first baseline не перезаписывай.

## Неизвестные Operational Inputs

Runtime URL, credentials, storage state и стабильный flow создания тестовой заявки пока не зафиксированы. Их отсутствие не разрешает обходить авторизацию, подменять DOM или объявлять UI-поведение подтверждённым.
