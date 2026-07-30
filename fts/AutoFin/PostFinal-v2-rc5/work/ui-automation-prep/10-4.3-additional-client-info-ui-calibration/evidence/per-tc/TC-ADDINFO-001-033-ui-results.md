# Per-TC UI results: 10-4.3-additional-client-info

## confirmed-ui-ready

- `TC-ADDINFO-001`: `ИНН клиента` visible enabled text input.
- `TC-ADDINFO-002`: `ИНН клиента` required marker and invalid empty state confirmed; messages `Обязательно к заполнению`, `ИНН не заполнен`.
- `TC-ADDINFO-003`: `ИНН клиента` always visible.
- `TC-ADDINFO-004`: manual per-key input `123456789123` persists after blur; field state is valid.
- `TC-ADDINFO-005`: short INN does not persist after blur.
- `TC-ADDINFO-006`: long INN does not persist after blur.
- `TC-ADDINFO-007`: alphanumeric INN does not persist after blur.
- `TC-ADDINFO-009`: manual INN filling is available; `123456789123` persists after blur.
- `TC-ADDINFO-014`: `ИНН проверен` readonly checkbox confirmed.
- `TC-ADDINFO-015`: `ИНН проверен` is not manually required.
- `TC-ADDINFO-016`: `ИНН проверен` always visible.
- `TC-ADDINFO-021`: `Кодовое слово` editable text input confirmed.
- `TC-ADDINFO-022`: `Кодовое слово` optional confirmed.
- `TC-ADDINFO-023`: `Кодовое слово` always visible.
- `TC-ADDINFO-025`: `Семейное положение` required marker and empty invalid state after `ДАЛЕЕ` confirmed.
- `TC-ADDINFO-026`: `Семейное положение` always visible.
- `TC-ADDINFO-027`: `Количество иждивенцев` editable numeric input with spinner and default `0`.
- `TC-ADDINFO-028`: `Количество иждивенцев` is prefilled with `0`.
- `TC-ADDINFO-029`: `Количество иждивенцев` always visible.
- `TC-ADDINFO-030`: numeric `2` persists.
- `TC-ADDINFO-031`: nonnumeric `2A` normalizes back to `0`; no inline error observed.
- `TC-ADDINFO-032`: spinner buttons change value `0 -> 1 -> 2 -> 1`.
- `TC-ADDINFO-033`: spinner decrement at `0` keeps value `0`.

## source-retained / no baseline correction

- `TC-ADDINFO-010`: baseline kept as FT-first per user instruction.
- `TC-ADDINFO-011`: baseline kept as FT-first per user instruction.
- `TC-ADDINFO-024`: baseline kept as FT-first per user instruction.

## blocked-observability

- `TC-ADDINFO-008`: automatic INN request/autofill requires integration fixture and expected oracle.
- `TC-ADDINFO-012`: INN verification functionality is not implemented on the stand yet.
- `TC-ADDINFO-013`: failed INN verification path cannot be checked because verification is not implemented yet.
- `TC-ADDINFO-017`: automatic `ИНН проверен` fill depends on verification functionality, not implemented yet.
- `TC-ADDINFO-018`: successful verification setting `ИНН проверен = Да` cannot be checked yet.
- `TC-ADDINFO-019`: unavailable-verification behavior cannot be checked yet.
- `TC-ADDINFO-020`: field locking after `ИНН проверен = Да` cannot be checked because the verified state is not reachable yet.
