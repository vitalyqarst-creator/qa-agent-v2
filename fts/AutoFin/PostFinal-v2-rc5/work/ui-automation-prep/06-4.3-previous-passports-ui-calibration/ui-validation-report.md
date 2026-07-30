# UI validation report: 06-4.3-previous-passports

Date: 2026-07-30

Repo root: `E:/Users/zhidkov/Documents/My_work/AI/Autofinans-Application/qa-agent-v2`

Branch: `codex/postfinal-v2-rc5-client-contacts-documents-ui-pass`

Stand: `http://fp-autofinance-dev.fisgroup.ru:8080/web/FormRunner/#/applicationlist/`

Scope: `fts/AutoFin/PostFinal-v2-rc5/test-cases/06-4.3-previous-passports.md`

Baseline test-cases were not edited.

## Summary

- Total TC checked: 21.
- Confirmed: 20.
- Blocked-observability: 1.
- Mismatch-ft-ui: 0.

## Confirmed UI Behavior

- `Клиент менял паспорт = Нет`: block `Данные предыдущих паспортов` is not present.
- `Клиент менял паспорт = Да`: block `Данные предыдущих паспортов` appears immediately.
- The first previous-passport row appears immediately after enabling `Клиент менял паспорт`; pressing `Добавить паспорт` adds a second row.
- Each previous-passport row contains only `Серия`, `Номер`, `Дата выдачи`, plus a delete/trash control. Fields `Код подразделения`, `Кем выдан`, and `Ввести вручную подразделение` are not present in previous-passport rows.
- Delete/trash removes the corresponding row immediately, without a JavaScript confirmation dialog.
- Required markers are represented by `field_container ... required` state for `Серия`, `Номер`, and `Дата выдачи`.

## Field Format Observations

### Серия

| Input | Trigger | Displayed value / state | Message |
|---|---|---|---|
| `1234` | manual keypress + blur | `1234`, `valid` | none |
| `123` | manual keypress + blur | while focused `123_`, after blur empty, `invalid empty required` | `Обязательно к заполнению` |
| `12345` | manual keypress + blur | `1234`, `valid`; 5th digit ignored | none |
| `12A4` | manual keypress + blur | while focused `124_`, after blur empty, `invalid empty required`; `A` filtered | `Обязательно к заполнению` |
| `1112` | manual keypress + blur | `1112`, `invalid` | `Не должно быть трех одинаковых цифр подряд` |

### Номер

| Input | Trigger | Displayed value / state | Message |
|---|---|---|---|
| `123456` | manual keypress + Tab/blur attempt | `123456`, `valid` | none |
| `12345` | manual keypress + Tab/blur attempt | `12345_`, `invalid` | `Обязательно к заполнению` |
| `1234567` | manual keypress + Tab/blur attempt | `123456`, `valid`; 7th digit ignored | none |
| `12345A` | manual keypress + Tab/blur attempt | `12345_`, `invalid`; `A` filtered | `Обязательно к заполнению` |
| `111111` | manual keypress + Tab/blur attempt | `111111`, `invalid` | `Не должно быть шести одинаковых цифр подряд` |

### Дата выдачи

- Empty state before focus: `field_container empty required label-align-top text-align-left`, value empty.
- Focus state: displayed mask `__.__.____`.
- `Tab` alone did not produce a visible validation message.
- `Ctrl+Enter` / top UI trigger `Следующее (Ctrl + Enter)` changed previous-passport `Дата выдачи` to `required ... invalid`.
- Exact message after `Ctrl+Enter`: `Введена неверная дата`.

## Detailed TC Results

| TC-ID | Baseline status | Setup/data | Action | Observed result | Final UI status | Evidence path | Automation recommendation |
|---|---|---|---|---|---|---|---|
| `TC-PASSPREV-001` | confirmed | New application card | Set `Клиент менял паспорт` to `Да` | Block `Данные предыдущих паспортов` appeared | confirmed | `evidence/per-tc/TC-PASSPREV-001.md` | Automation-ready |
| `TC-PASSPREV-002` | confirmed | New application card | Keep/set `Клиент менял паспорт` to `Нет` | Block `Данные предыдущих паспортов` absent | confirmed | `evidence/per-tc/TC-PASSPREV-002.md` | Automation-ready |
| `TC-PASSPREV-003` | confirmed | Previous-passport block visible | Inspect block | `ДОБАВИТЬ ПАСПОРТ` visible | confirmed | `evidence/per-tc/TC-PASSPREV-003.md` | Automation-ready |
| `TC-PASSPREV-004` | confirmed | Previous-passport block visible | Click `ДОБАВИТЬ ПАСПОРТ` | Second row added with `Серия`, `Номер`, `Дата выдачи`, delete/trash; add button remains | confirmed | `evidence/per-tc/TC-PASSPREV-004.md` | Automation-ready |
| `TC-PASSPREV-005` | confirmed | `Клиент менял паспорт = Да` | Inspect row header | Delete/trash icon is visible immediately on the first row and on each added row | confirmed | `evidence/per-tc/TC-PASSPREV-005.md` | Automation-ready |
| `TC-PASSPREV-006` | blocked-observability | Two previous-passport rows | Click delete/trash on the second row | Whole second row removed; first row remains; no confirmation dialog | confirmed | `evidence/per-tc/TC-PASSPREV-006.md` | Promote to automation-ready for observed delete set |
| `TC-PASSPREV-007` | confirmed | Previous-passport block visible | Inspect first row | `Серия` visible | confirmed | `evidence/per-tc/TC-PASSPREV-007.md` | Automation-ready |
| `TC-PASSPREV-008` | confirmed | Fresh card, previous row | Enter `1234` in `Серия` | Value remains `1234`, state `valid` | confirmed | `evidence/per-tc/TC-PASSPREV-008.md` | Automation-ready |
| `TC-PASSPREV-009` | confirmed | Fresh card, previous row | Enter `123` in `Серия` | Incomplete `123_` while focused; after blur field clears and shows `Обязательно к заполнению` | confirmed | `evidence/per-tc/TC-PASSPREV-009.md` | Automation-ready |
| `TC-PASSPREV-010` | confirmed | Fresh card, previous row | Enter `12345` in `Серия` | UI keeps `1234`, ignores 5th digit, state `valid` | confirmed | `evidence/per-tc/TC-PASSPREV-010.md` | Automation-ready |
| `TC-PASSPREV-011` | confirmed | Fresh card, previous row | Enter `12A4` in `Серия` | `A` filtered; incomplete `124_`; after blur field clears and shows `Обязательно к заполнению` | confirmed | `evidence/per-tc/TC-PASSPREV-011.md` | Automation-ready |
| `TC-PASSPREV-012` | confirmed | Fresh card, previous row | Enter `1112` in `Серия` | Value remains `1112`, state `invalid`, message `Не должно быть трех одинаковых цифр подряд` | confirmed | `evidence/per-tc/TC-PASSPREV-012.md` | Automation-ready |
| `TC-PASSPREV-013` | confirmed | Previous-passport block visible | Inspect first row | `Номер` visible | confirmed | `evidence/per-tc/TC-PASSPREV-013.md` | Automation-ready |
| `TC-PASSPREV-014` | confirmed | Fresh card, previous row | Enter `123456` in `Номер` | Value remains `123456`, state `valid` | confirmed | `evidence/per-tc/TC-PASSPREV-014.md` | Automation-ready |
| `TC-PASSPREV-015` | confirmed | Fresh card, previous row | Enter `12345` in `Номер` | Value `12345_`, state `invalid`, message `Обязательно к заполнению` | confirmed | `evidence/per-tc/TC-PASSPREV-015.md` | Automation-ready |
| `TC-PASSPREV-016` | confirmed | Fresh card, previous row | Enter `1234567` in `Номер` | UI keeps `123456`, ignores 7th digit, state `valid` | confirmed | `evidence/per-tc/TC-PASSPREV-016.md` | Automation-ready |
| `TC-PASSPREV-017` | confirmed | Fresh card, previous row | Enter `12345A` in `Номер` | `A` filtered; value `12345_`, state `invalid`, message `Обязательно к заполнению` | confirmed | `evidence/per-tc/TC-PASSPREV-017.md` | Automation-ready |
| `TC-PASSPREV-018` | confirmed | Fresh card, previous row | Enter `111111` in `Номер` | Value remains `111111`, state `invalid`, message `Не должно быть шести одинаковых цифр подряд` | confirmed | `evidence/per-tc/TC-PASSPREV-018.md` | Automation-ready |
| `TC-PASSPREV-019` | confirmed | Previous-passport block visible | Inspect first row | `Дата выдачи` visible as date input with mask `__.__.____` on focus | confirmed | `evidence/per-tc/TC-PASSPREV-019.md` | Automation-ready |
| `TC-PASSPREV-020` | blocked-observability | Previous-passport row visible | Inspect `Дата выдачи` behavior | UI shows required/date validation only; no separate behavior traceable specifically to empty BSR 114 | blocked-observability | `evidence/per-tc/TC-PASSPREV-020.md` | Keep blocked until source/BA clarification |
| `TC-PASSPREV-021` | candidate-ui-calibration | Previous-passport row visible, `Дата выдачи` empty | Focus `Дата выдачи`, then trigger `Ctrl+Enter` / `Следующее` | Field becomes invalid; message `Введена неверная дата` | confirmed | `evidence/per-tc/TC-PASSPREV-021.md` | Automation-ready with `Ctrl+Enter` validation trigger |

## Test-case Corrections Recommended

- For `TC-PASSPREV-004`, clarify that the first row appears immediately after `Клиент менял паспорт = Да`; `Добавить паспорт` adds an additional row, not the initial row.
- For `TC-PASSPREV-006`, replace the source uncertainty with observed UI delete set: delete/trash removes one whole previous-passport row containing `Серия`, `Номер`, `Дата выдачи`; it does not involve `Код подразделения`, `Кем выдан`, or manual subdivision switch because those controls are not present in the previous-passport row.
- For `TC-PASSPREV-009` and `TC-PASSPREV-011`, use the exact UI mechanism: incomplete series clears after blur and shows `Обязательно к заполнению`.
- For `TC-PASSPREV-010`, assert truncation/ignored 5th digit: `12345` results in `1234`, valid.
- For `TC-PASSPREV-012`, assert exact message `Не должно быть трех одинаковых цифр подряд`.
- For `TC-PASSPREV-015` and `TC-PASSPREV-017`, assert value `12345_`, invalid, message `Обязательно к заполнению`.
- For `TC-PASSPREV-016`, assert truncation/ignored 7th digit: `1234567` results in `123456`, valid.
- For `TC-PASSPREV-018`, assert exact message `Не должно быть шести одинаковых цифр подряд`.
- For `TC-PASSPREV-021`, set validation trigger to `Ctrl+Enter` / `Следующее (Ctrl + Enter)` and expected message to `Введена неверная дата`.
- Keep `TC-PASSPREV-020` blocked unless source clarifies BSR 114. UI did not show a separate BSR-114-specific rule.
