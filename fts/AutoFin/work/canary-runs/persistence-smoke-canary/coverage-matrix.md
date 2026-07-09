# Persistence Smoke Coverage Matrix

| persistence area | source rows / BSR | TC id | saved data | reopen verification | cleanup strategy | out-of-scope notes |
| --- | --- | --- | --- | --- | --- | --- |
| Registration address via DaData | Table 7 row 33; primary `BSR 115`, `BSR 116`; reopen via `BSR 35` | `TC-AF43-PS-001` | Selected DaData address `г Красноярск, ул Мира, д 10` | Verify address field after reopening same card | Restore original address or use isolated application | Does not retest DaData no-result, invalid address feedback, or BSR 119 decomposition into manual components. |
| Manual registration address | Table 7 rows 34-44; `BSR 121`-`BSR 137`; reopen via `BSR 35` | `TC-AF43-PS-002` | Postal index, region, city, street, house, apartment | Verify manual component fields after reopen | Restore original manual address state or use isolated application | Does not exhaust all component combinations or private-house branch variants. |
| Fact address differs from registration | Table 7 rows 45-57; primary `BSR 138`, `BSR 140`, `BSR 141`, `BSR 144`; reopen via `BSR 35` | `TC-AF43-PS-003` | Same-as-registration = `Нет`; selected fact address | Verify branch value and fact address after reopen | Restore original fact-address state or use isolated application | Does not retest BSR 148 manual fact-address visibility or all manual fact-address components. |
| Client mobile phone and electronic mail | Table 7 rows 59-60; `BSR 162`-`BSR 166`; reopen via `BSR 35` | `TC-AF43-PS-004` | Mobile phone `9234567890`; electronic mail `ivanov.ps@example.ru` | Verify both fields after reopen | Restore original contact values or use isolated application | Grouped smoke is accepted only as a minimal persistence signal. Residual risk: a field-specific save defect for only phone or only e-mail may require a follow-up atomic persistence TC. |
| Added work phone | Table 7 rows 61-64; primary `BSR 168`, `BSR 171`, `BSR 172`; reopen via `BSR 35` | `TC-AF43-PS-005` | Added work phone `3912123456` | Verify added phone row after reopen | Delete added phone and save, or use isolated application | BSR 167 add-phone visibility is supporting setup, not the primary persistence oracle. Home-phone persistence sampled out; deletion of phone row left for follow-up if needed. |
| Added contact person | Table 7 rows 66-72; `BSR 173`-`BSR 185`; reopen via `BSR 35` | `TC-AF43-PS-006` | FIO, relation, phone and calculated birth date `D - 30 calendar years` in `DD.MM.YYYY` format | Verify added contact-person row after reopen | Delete added contact person and save, or use isolated application | Does not retest all relation dictionary values. `D` source requires BA/UI confirmation before execution. |
| Deleted contact person | Table 7 rows 72-73; `BSR 186`-`BSR 189`; reopen via `BSR 35` | `TC-AF43-PS-007` | Self-contained setup creates and saves `Петров Анна Сергеевна`; test then removes it | Verify removed row is absent after reopen | Restore contact person only if shared data was used | Requires BA/UI confirmation for safe restoration path. |

## Trace Exercise Review Summary

| TC id | reviewed source reference | decision |
| --- | --- | --- |
| `TC-AF43-PS-001` | `BSR 119` | Removed from primary trace. The TC selects and persists a DaData address; it does not verify decomposition into manual components. |
| `TC-AF43-PS-003` | `BSR 148` | Removed from primary trace. The TC selects a DaData fact address after setting the branch to `Нет`; it does not verify manual fact-address visibility. |
| `TC-AF43-PS-005` | `BSR 167` | Removed from primary trace. The TC verifies saved work-phone value after reopen; add-phone visibility is supporting setup only. |
| `TC-AF43-PS-006` | Birth date `D - 30 calendar years` | Formalized with `D`, `DD.MM.YYYY`, and example `09.07.2026 -> 09.07.1996`. |
| `TC-AF43-PS-007` | Delete contact-person persistence | Setup is self-contained: create, save, close, reopen, verify presence, then delete/save/reopen. |

## Representative / Pairwise Coverage Decisions

| fields | shared_restriction | source_rows_bsr | selected_strategy | tc_ids | covered_classes | omitted_combinations | residual_risk | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| email field | Single valid e-mail address; invalid e-mail classes stay in field-level v4 coverage | Table 7 row 60; `BSR 165`; `BSR 166` | Save one valid e-mail together with mobile phone as grouped smoke | `TC-AF43-PS-004` | valid single e-mail value | invalid missing `@`, multiple addresses, spaces, domain syntax | A field-specific persistence defect for e-mail only may require a later atomic persistence TC. | Minimal persistence signal for contact values after save/reopen. |
| phone fields | Ten-digit phone values; invalid phone classes stay in field-level v4 coverage | Table 7 rows 59, 61-64; `BSR 162`-`BSR 164`; `BSR 168`; `BSR 171`; `BSR 172` | Sample client mobile phone and one added work phone | `TC-AF43-PS-004`; `TC-AF43-PS-005` | valid mobile phone; valid added work phone | home-phone persistence, invalid phone classes, phone-row deletion persistence | A phone-type-specific persistence defect may require follow-up TC after BA confirms priority. | Covers both direct field persistence and repeatable phone-row persistence within the 10 TC hard cap. |
| postal indexes | Six-digit valid postal index in manual registration address | Table 7 rows 34-44; `BSR 121`-`BSR 137` | Sample one valid postal index as part of full manual registration address | `TC-AF43-PS-002` | valid six-digit postal index | invalid postal-index classes, fact-address manual postal-index branch | A component-specific persistence defect in another address branch may require later regression expansion. | Persistence smoke focuses on one full manual address payload rather than all branch/component combinations. |

## Residual Risk

This is representative persistence smoke, not a full persistence regression suite. It intentionally omits:
- exhaustive phone type combinations;
- all address component combinations;
- all relation dictionary values;
- invalid-value rejection persistence;
- backend/model-level assertions such as `kladr` storage unless observable in UI or separately instrumented.
