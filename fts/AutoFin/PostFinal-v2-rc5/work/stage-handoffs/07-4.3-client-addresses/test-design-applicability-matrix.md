# Test Design Applicability Matrix

| dimension | applicable | rationale | source_ref |
| --- | --- | --- | --- |
| field-property | yes | Address fields have visibility, default, editability, requiredness and format obligations. | `BSR 115-161; BSR 324` |
| requiredness | yes | Requiredness is source-backed; exact message text is only asserted where FT gives it. | `SRC-ROW-003; SRC-ROW-008; SRC-ROW-009; SRC-ROW-011; SRC-ROW-013; SRC-ROW-022; SRC-ROW-023; SRC-ROW-024` |
| dictionary | yes | Region fields use DaData as external dynamic dictionary per approved clarification. | `DICT-DADATA-ADDRESS-SUGGESTIONS; DICT-DADATA-REGION; CLR-001; CLR-ADDR-004` |
| integration | yes | DaData use is source-backed, but vendor trigger/debounce/fallback/order are excluded. | `BSR 116; BSR 118; BSR 119; BSR 141; BSR 143; BSR 144; BSR 324; work/vendor-references/dadata-reference.md` |
| persistence/internal-model | no | Internal `kladr` fill is excluded by approved clarification and not converted into UI TC. | `CLR-ADDR-005; ASSERT-ADDR-062` |
