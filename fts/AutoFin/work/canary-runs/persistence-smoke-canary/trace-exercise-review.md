# Trace Exercise Review

## Scope

Reviewed persistence smoke TC against section 4.3 source-backed BSR references after the independent canary repair pass. The goal is to keep only exercised source references as primary trace and document supporting/out-of-scope references separately.

## Decisions

| TC id | source reference | problem | decision | residual action |
| --- | --- | --- | --- | --- |
| `TC-AF43-PS-001` | `BSR 119` | The TC selects a DaData registration address and verifies the saved displayed value after reopen. It does not verify decomposition into manual address components. | Removed from primary trace. | Keep decomposition coverage in field-level/manual-address checks, not in this persistence smoke oracle. |
| `TC-AF43-PS-003` | `BSR 148` | The TC selects a fact address via DaData after setting the same-as-registration flag to `Нет`. It does not verify manual fact-address visibility. | Removed from primary trace. | Manual fact-address visibility remains v4/field-level coverage. |
| `TC-AF43-PS-005` | `BSR 167` | The TC verifies saved work-phone value after reopen. Add-phone visibility is only setup for creating the row. | Removed from primary trace and treated as supporting setup. | If phone-repeatable visibility needs persistence-specific coverage, add a separate TC or explicit follow-up. |
| `TC-AF43-PS-006` | Birth date `D - 30 years` | The earlier value did not define `D`, output format, or example value. | Formalized as `D - 30 calendar years` in `DD.MM.YYYY`; example `D = 09.07.2026 -> 09.07.1996`. | `BA-PS-005` must confirm the authoritative application date for `D`. |
| `TC-AF43-PS-007` | Deletion persistence setup | The earlier TC assumed a pre-existing contact person and was not self-contained. | Preconditions now create, save, close, reopen and verify the contact person before deletion. | Exact save/cleanup flow remains confirmation-required. |

## UI Block Naming

| source-backed section 4.3 term | production artifact term | rejected for this scope |
| --- | --- | --- |
| `Блок «Контакты клиента»` | `Контакты клиента` | `Контактная информация` |
| `Блок «Контактные лица» (блок-повторитель)` | `Контактные лица` | `Контактное лицо` as a block name |

Singular `контактное лицо` remains valid when describing the business entity, not the UI block label.

## Grouped Smoke Risk

`TC-AF43-PS-004` intentionally groups mobile phone and e-mail as a minimal persistence smoke because both fields are edited and saved in one simple form interaction. Residual risk is explicit: a field-specific persistence defect affecting only one of the two fields may require a later atomic persistence TC.
