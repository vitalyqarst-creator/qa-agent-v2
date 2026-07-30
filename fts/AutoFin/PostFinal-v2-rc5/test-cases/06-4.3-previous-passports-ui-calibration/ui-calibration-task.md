# UI calibration task: 06-4.3-previous-passports

Scope: `4.3-previous-passports`.

Baseline test-cases file:

`fts/AutoFin/PostFinal-v2-rc5/test-cases/06-4.3-previous-passports.md`

Mode: UI calibration / automation readiness evidence. Do not rewrite FT-first baseline test-cases during this task.

## Goal

Check the previous-passports test-cases in the real UI and collect evidence needed to decide which TC are automation-ready and which must remain blocked by observability or missing clarification.

Primary expected output:

- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/06-4.3-previous-passports-ui-calibration/ui-validation-report.md`
- `fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/06-4.3-previous-passports-ui-calibration/ui-evidence-index.md`
- per-TC evidence files under `evidence/per-tc/`
- screenshots under `evidence/screenshots/`

## Scope boundaries

Use only:

- block controlled by `Клиент менял паспорт`;
- block `Данные предыдущих паспортов`;
- fields `Серия`, `Номер`, `Дата выдачи`;
- action `Добавить паспорт`;
- row action `Корзина`.

Do not calibrate current passport fields except as setup needed to reach the previous-passport block.

Do not edit:

- source DOCX/XHTML/PDF;
- support/mockups;
- baseline `fts/**/test-cases/*.md`;
- credentials, `.env`, cookies, auth/session/storage files.

## Source-backed rules to verify

Relevant BSR:

- `BSR 105`: block `Данные предыдущих паспортов` is visible when `Клиент менял паспорт = Да`; hidden when not `Да`.
- `BSR 106`: `Добавить паспорт` is visible when `Клиент менял паспорт = Да`.
- `BSR 107`: clicking `Добавить паспорт` adds fields `Серия`, `Номер`, `Дата выдачи` and widgets/actions `Добавить паспорт` and `Корзина`.
- `BSR 108`: `Корзина` is visible when `Клиент менял паспорт = Да`.
- `BSR 109`: clicking `Корзина` removes corresponding previous-passport fields, but exact delete set is unclear in source.
- `BSR 110`: `Серия` is visible when `Клиент менял паспорт = Да`.
- `BSR 111`: `Серия` accepts only 4 numeric symbols and must not contain 3 identical digits in a row.
- `BSR 112`: `Номер` is visible when `Клиент менял паспорт = Да`.
- `BSR 113`: `Номер` accepts only 6 numeric symbols and must not contain 6 identical digits in a row.
- `BSR 114`: code exists for `Дата выдачи`, but the source row contains no normative text after the code.

Known gaps:

- `GAP-PASS-PREV-001`: exact delete set for `Корзина` is not source-confirmed.
- `GAP-PASS-PREV-002`: BSR 114 has no normative text.
- `GAP-PASS-PREV-003`: `Дата выдачи` requiredness trigger and UI feedback are not source-confirmed.

Current-passport references may be used only as analogies for UI behavior, not as source of truth for previous passports.

## Test-cases to check

| TC-ID | Baseline status | Main UI question | Expected evidence decision |
| --- | --- | --- | --- |
| `TC-PASSPREV-001` | `confirmed` | Does `Данные предыдущих паспортов` appear after `Клиент менял паспорт = Да`? | `confirmed` if observable. |
| `TC-PASSPREV-002` | `confirmed` | Is the previous-passports block hidden when `Клиент менял паспорт = Нет`? | `confirmed` if observable. |
| `TC-PASSPREV-003` | `confirmed` | Is `Добавить паспорт` visible in previous-passports block? | `confirmed` if observable. |
| `TC-PASSPREV-004` | `confirmed` | What exactly appears after clicking `Добавить паспорт`? | `confirmed` if `Серия`, `Номер`, `Дата выдачи`, `Добавить паспорт`, `Корзина` appear. |
| `TC-PASSPREV-005` | `confirmed` | Is `Корзина` visible immediately after `Клиент менял паспорт = Да`, only after adding a row, or both? | `confirmed` if source behavior is observable; otherwise note exact UI condition. |
| `TC-PASSPREV-006` | `blocked-observability` | What exact fields disappear after clicking `Корзина`? Are `Код подразделения`, `Кем выдан`, manual subdivision switch present in previous-passport row? | Keep `blocked-observability` unless exact delete set is clearly observed and screenshot-backed. |
| `TC-PASSPREV-007` | `confirmed` | Is `Серия` visible when previous-passport row is available? | `confirmed` if observable. |
| `TC-PASSPREV-008` | `confirmed` | Does `1234` remain accepted in `Серия`? | `confirmed` if observable. |
| `TC-PASSPREV-009` | `confirmed` | What happens for short `Серия = 123` after blur/validation trigger? | `confirmed` if rejected or normalized according to field format; record exact UI mechanism. |
| `TC-PASSPREV-010` | `confirmed` | What happens for long `Серия = 12345`? | `confirmed` if extra digit is rejected/truncated or invalid state is shown; record exact UI mechanism. |
| `TC-PASSPREV-011` | `confirmed` | What happens for nonnumeric `Серия = 12A4`? | `confirmed` if rejected/filtered/invalid; record exact UI mechanism. |
| `TC-PASSPREV-012` | `confirmed` | What happens for repeated digits `Серия = 1112`? | `confirmed` if invalid according to FT; capture exact message/state if present. |
| `TC-PASSPREV-013` | `confirmed` | Is `Номер` visible when previous-passport row is available? | `confirmed` if observable. |
| `TC-PASSPREV-014` | `confirmed` | Does `123456` remain accepted in `Номер`? | `confirmed` if observable. |
| `TC-PASSPREV-015` | `confirmed` | What happens for short `Номер = 12345`? | `confirmed` if rejected/normalized according to field format; record exact UI mechanism. |
| `TC-PASSPREV-016` | `confirmed` | What happens for long `Номер = 1234567`? | `confirmed` if extra digit is rejected/truncated or invalid state is shown; record exact UI mechanism. |
| `TC-PASSPREV-017` | `confirmed` | What happens for nonnumeric `Номер = 12345A`? | `confirmed` if rejected/filtered/invalid; record exact UI mechanism. |
| `TC-PASSPREV-018` | `confirmed` | What happens for repeated digits `Номер = 111111`? | `confirmed` if invalid according to FT; capture exact message/state if present. |
| `TC-PASSPREV-019` | `confirmed` | Is `Дата выдачи` visible as a date input? | `confirmed` if observable. |
| `TC-PASSPREV-020` | `blocked-observability` | Does UI reveal any behavior that can be tied specifically to empty `BSR 114`? | Usually remains `blocked-observability` unless BA/source/UI evidence clarifies BSR 114. |
| `TC-PASSPREV-021` | `candidate-ui-calibration` | What trigger and exact UI feedback prove requiredness of `Дата выдачи`? | `confirmed` only if trigger/message/state are captured; otherwise keep `candidate-ui-calibration`. |

## Preferred shared setup

1. Open application list on the test stand.
2. Open or create an application card.
3. Navigate to the passport block.
4. Set `Клиент менял паспорт = Да`.
5. Use `Добавить паспорт` to create a previous-passport row when needed.
6. For format checks, start each value from a clean field state. Record the reset method.
7. For validation/requiredness checks, record the exact trigger:
   - blur / Tab;
   - click `ДАЛЕЕ`;
   - save/transition;
   - other observed UI action.

If the same application state contaminates later checks, open a fresh application or reset the row and document the reset.

## Specific values to test

`Серия`:

- positive: `1234`;
- short: `123`;
- long: `12345`;
- nonnumeric: `12A4`;
- repeated digits: `1112`.

`Номер`:

- positive: `123456`;
- short: `12345`;
- long: `1234567`;
- nonnumeric: `12345A`;
- repeated digits: `111111`.

`Дата выдачи`:

- empty value for requiredness check;
- if the UI requires date input for another check, use a clearly past date such as `01.01.2020`.

Do not add additional boundary/date rules for BSR 114 unless the UI/source explicitly shows them.

## Evidence requirements

For each checked TC, create a per-TC evidence markdown file with:

- `TC-ID`;
- final status: `confirmed`, `blocked-observability`, or `mismatch-ft-ui`;
- exact setup path;
- exact action performed;
- test data used;
- observed UI result;
- exact field state/message if present;
- screenshots used;
- selector/locator notes if relevant;
- whether baseline expected result remains valid;
- if blocked: exact missing data, missing UI path or missing source clarification.

Screenshot minimum:

- `Клиент менял паспорт = Нет` state;
- `Клиент менял паспорт = Да` state;
- previous-passport row after `Добавить паспорт`;
- `Корзина` before click;
- state after `Корзина` click;
- each invalid format state/message that is asserted;
- empty `Дата выдачи` after validation trigger.

## Status rules

Use `confirmed` when UI behavior matches FT-first expected result and the observable is stable enough for automation.

Use `blocked-observability` when behavior may be correct, but exact source rule, delete set, fixture, selector or UI path is not stable/observable enough.

Use `mismatch-ft-ui` only when UI clearly contradicts source-backed expected result. Do not update baseline test-cases in this task.

Do not use `not-reproducible` unless the UI path cannot be reached after reasonable attempts; prefer `blocked-observability` with exact reason.

## Report format

Create `ui-validation-report.md` with:

1. repo root, branch, commit;
2. stand URL;
3. date/time;
4. scope;
5. checked TC list;
6. status summary;
7. detailed table:

| TC-ID | Baseline status | Setup/data | Action | Observed result | Final UI status | Evidence path | Automation recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |

Create `ui-evidence-index.md` with one row per TC:

| TC-ID | Status | Topic | Trigger/action | Evidence file | Screenshots |
| --- | --- | --- | --- | --- | --- |

## Git rules

Work in a dedicated branch, for example:

`codex/postfinal-v2-rc5-previous-passports-ui-calibration`

Commit only new UI evidence files under:

`fts/AutoFin/PostFinal-v2-rc5/work/ui-automation-prep/06-4.3-previous-passports-ui-calibration/`

Do not stage or commit:

- baseline test-cases;
- source DOCX/XHTML/PDF;
- support/mockups;
- `.env`;
- credentials/cookies/auth/session/storage files;
- unrelated work artifacts.

Suggested commit message:

`Add previous passports UI calibration evidence`

## Final response expected from UI agent

Return:

- branch;
- commit SHA;
- pushed remote branch;
- status count by `confirmed`, `blocked-observability`, `mismatch-ft-ui`;
- exact list of TC by status;
- report path;
- evidence index path;
- whether baseline test-cases/source files remained unchanged.
