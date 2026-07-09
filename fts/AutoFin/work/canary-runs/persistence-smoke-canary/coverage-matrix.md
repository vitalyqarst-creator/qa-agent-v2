# Persistence Smoke Coverage Matrix

| persistence area | source rows / BSR | TC id | saved data | reopen verification | cleanup strategy | out-of-scope notes |
| --- | --- | --- | --- | --- | --- | --- |
| Registration address via DaData | Table 7 row 33; `BSR 115`-`BSR 120`; reopen via `BSR 35` | `TC-AF43-PS-001` | Selected DaData address `г Красноярск, ул Мира, д 10` | Verify address field after reopening same card | Restore original address or use isolated application | Does not retest DaData no-result or invalid address feedback. |
| Manual registration address | Table 7 rows 34-44; `BSR 121`-`BSR 137`; reopen via `BSR 35` | `TC-AF43-PS-002` | Postal index, region, city, street, house, apartment | Verify manual component fields after reopen | Restore original manual address state or use isolated application | Does not exhaust all component combinations or private-house branch variants. |
| Fact address differs from registration | Table 7 rows 45-57; `BSR 138`-`BSR 161`; reopen via `BSR 35` | `TC-AF43-PS-003` | Same-as-registration = `Нет`; selected fact address | Verify branch value and fact address after reopen | Restore original fact-address state or use isolated application | Does not retest all manual fact-address components. |
| Client mobile phone and electronic mail | Table 7 rows 59-60; `BSR 162`-`BSR 166`; reopen via `BSR 35` | `TC-AF43-PS-004` | Mobile phone `9234567890`; electronic mail `ivanov.ps@example.ru` | Verify both fields after reopen | Restore original contact values or use isolated application | Does not retest invalid contact values covered by v4. |
| Added work phone | Table 7 rows 61-64; `BSR 167`-`BSR 172`; reopen via `BSR 35` | `TC-AF43-PS-005` | Added work phone `3912123456` | Verify added phone row after reopen | Delete added phone and save, or use isolated application | Home-phone persistence sampled out; deletion of phone row left for follow-up if needed. |
| Added contact person | Table 7 rows 66-72; `BSR 173`-`BSR 185`; reopen via `BSR 35` | `TC-AF43-PS-006` | FIO, relation, phone and birth date | Verify added contact-person row after reopen | Delete added contact person and save, or use isolated application | Does not retest all relation dictionary values. |
| Deleted contact person | Table 7 rows 72-73; `BSR 186`-`BSR 189`; reopen via `BSR 35` | `TC-AF43-PS-007` | Removal of `Петров Анна Сергеевна` | Verify removed row is absent after reopen | Restore contact person if shared data was used | Requires BA/UI confirmation for safe restoration path. |

## Residual Risk

This is representative persistence smoke, not a full persistence regression suite. It intentionally omits:
- exhaustive phone type combinations;
- all address component combinations;
- all relation dictionary values;
- invalid-value rejection persistence;
- backend/model-level assertions such as `kladr` storage unless observable in UI or separately instrumented.
