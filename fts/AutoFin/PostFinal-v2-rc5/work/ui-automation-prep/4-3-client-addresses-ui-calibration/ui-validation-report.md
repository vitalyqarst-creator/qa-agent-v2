# UI Validation Report: 4.3 Client Addresses

Scope: `4.3-client-addresses`, block `Адреса клиента`.

Stand: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/applicationlist/`

Date: 2026-07-30

Mode: FT UI automation prep / UI calibration. Baseline FT-first test-cases and source DOCX/XHTML/PDF/support/mockups were not edited.

## Execution Summary

Checked 17 candidate UI calibration cases.

Confirmed: `TC-ADDR-005`, `TC-ADDR-013`, `TC-ADDR-031`, `TC-ADDR-047`, `TC-ADDR-051`, `TC-ADDR-052`, `TC-ADDR-056`, `TC-ADDR-057`, `TC-ADDR-058`, `TC-ADDR-059`, `TC-ADDR-060`, `TC-ADDR-062`.

Mismatch FT/UI: `TC-ADDR-021`, `TC-ADDR-023`, `TC-ADDR-049`, `TC-ADDR-053`, `TC-ADDR-061`.

Blocked: none.

Needs test data: none.

## Shared UI Setup

Registration address:

1. Open application list.
2. Click `СОЗДАТЬ ЗАЯВКУ`.
3. In `Адреса клиента`, click the visible switch `Ввести вручную` for `Адрес регистрации`.
4. Use `ДАЛЕЕ` as the validation trigger for required fields; use `blur` for masked/format fields, then `ДАЛЕЕ` to confirm persisted field state.

Actual address:

1. Open a clean new card.
2. In `Адреса клиента`, turn off `Адрес фактического места жительства совпадает с адресом регистрации`.
3. Click the second visible `Ввести вручную` switch, the one located under `Адрес фактического места жительства`.
4. Use the same `blur` and `ДАЛЕЕ` triggers.

## Observed UI Behavior

Required field messages after `ДАЛЕЕ`:

| Address area | Field | Required marker | Invalid state | Exact message |
|---|---|---:|---:|---|
| Registration | `Регион` | yes | yes | `Выберите значение` |
| Registration | `Населенный пункт` | yes when both locality/city empty | yes | `Обязательно к заполнению` |
| Registration | `Город` | yes when both locality/city empty | yes | `Обязательно к заполнению` |
| Registration | `Улица` | no | no | none |
| Registration | `Дом` | yes | yes | `Обязательно к заполнению` |
| Registration | `Квартира` | yes when private-house checkbox is not selected | yes | `Обязательно к заполнению` |
| Actual | `Регион` | yes | yes | `Выберите значение` |
| Actual | `Населенный пункт` | yes | yes | `Обязательно к заполнению` |
| Actual | `Город` | yes | yes | `Обязательно к заполнению` |
| Actual | `Улица` | no | no | none |
| Actual | `Дом` | yes | yes | `Обязательно к заполнению` |
| Actual | `Квартира` | yes when `Клиент проживает в частном доме` is not selected | yes | `Обязательно к заполнению` |

Postal index:

| Value | Displayed after input | Displayed after blur | State/message |
|---|---|---|---|
| `443017` | `443017` | `443017` | valid, no message |
| `44301` | `44301_` | empty | empty, no message |
| `4430179` | `443017` | `443017` | valid, extra digit ignored/truncated |
| `44301A` | `44301_` | empty | letter filtered/incomplete mask clears on blur, no message |
| `443 17` | `44317_` | empty | space filtered/incomplete mask clears on blur, no message |
| `443-17` | `44317_` | empty | hyphen filtered/incomplete mask clears on blur, no message |

Registration `Корпус`:

| Value | Displayed after blur | State/message |
|---|---|---|
| `12` | `12` | valid |
| `12A` | `12A` | invalid, `Введено некорректное значение` |
| `12Д` | `12Д` | valid |
| `1 2` | `1 2` | valid |
| `1-2` | `1-2` | invalid, `Введено некорректное значение` |
| `1.2` | `1.2` | invalid, `Введено некорректное значение` |

Registration/actual `Квартира`:

| Value | Displayed after blur | State/message |
|---|---|---|
| `12` | `12` | valid |
| `12A` | `12A` | invalid, `Введено некорректное значение` |
| `12Д` | `12Д` | valid |
| `1 2` | `1 2` | invalid, `Введено некорректное значение` |
| `1-2` | `1-2` | valid |
| `1.2` | `1.2` | invalid, `Введено некорректное значение` |

Actual private-house checkbox:

When `Клиент проживает в частном доме` is unchecked, empty `Квартира` is required/invalid with `Обязательно к заполнению`. After checking it, `Квартира` becomes optional/valid empty, while `Дом` remains required/invalid.

## Required Test-Case Corrections

`TC-ADDR-021`: do not describe `Корпус` as numeric-only. Current UI accepts `1 2` and `12Д` as valid and rejects `12A`, `1-2`, `1.2` with `Введено некорректное значение`.

`TC-ADDR-023` and `TC-ADDR-049`: do not describe `Квартира` as numeric-only. Current UI accepts digits, hyphen (`1-2`) and the checked Cyrillic letter case `12Д`; it rejects Latin `12A`, spaces and dot with `Введено некорректное значение`.

`TC-ADDR-053`: do not expect an invalid state/message for a 7-digit postal index. Current UI truncates/ignores the extra digit and leaves `443017` valid.

`TC-ADDR-061`: update expected result. `Улица` in actual address manual mode is optional: no required marker, no invalid state, no message after `ДАЛЕЕ`.

All postal-index cases should state the real trigger: invalid/incomplete masked values are cleared on `blur`; no inline error message is shown for postal mask failures.

## Evidence

Evidence index: `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/ui-evidence-index.md`

Per-TC evidence files are under `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/per-tc/`.

Screenshots are under `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/4-3-client-addresses-ui-calibration/evidence/screenshots/`.
