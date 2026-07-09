# Fixture Catalog

## Fixture Catalog

| fixture_id | fixture_type | purpose | setup_source | used_by_tc | constraints | residual_risk |
| --- | --- | --- | --- | --- | --- | --- |
| FX-BSR32-001 | visible-list-state | Provide a visible `Заявки в системе` list with at least one filter that can be changed, one sortable column, one selectable row and enough records for pagination change. | Manual UI setup in each TC preconditions; source-backed action row `BSR 32` defines reset effect. | TC-BSR32-001; TC-BSR32-002; TC-BSR32-003; TC-BSR32-004 | The fixture must not rely on invented field names, page size, row count, messages, backend state or API effects. | Medium for pagination if current data set does not expose another page; reviewer should verify fixture feasibility. |

## Rules

- Production `TC-*` files inline the setup actions and do not reference this fixture as a setup profile.
- The catalog records reusable context only for reviewer audit.
