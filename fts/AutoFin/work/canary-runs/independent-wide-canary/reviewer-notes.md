# Reviewer Notes

## Review Mode

Direct post-generation review, not a full session-based sign-off cycle.

## Results

| pass | result | notes |
| --- | --- | --- |
| traceability | `needs-attention` | Every selected BSR range is represented in coverage matrix. Several restriction requirements are only partially covered because exact invalid-value UI oracle is absent from source. |
| structure | `needs-attention` | TC numbering is continuous, required runtime fields are present, and production file has no embedded diagnostic tables. Potential issue: some preconditions use generic setup via creating a blank application because the chosen field scope does not include a full saved-application fixture. |
| test-design | `needs-attention` | Positive and source-backed negative checks are present. Numeric/date/text invalid classes are intentionally not executable without source-backed observable reactions. |

## Findings

| finding_id | severity | mode | affected | description | required_change |
| --- | --- | --- | --- | --- | --- |
| `REV-AW-001` | warning | test-design | `GAP-AW-002`-`GAP-AW-005`; `GAP-AW-007`; `GAP-AW-009` | Source-backed restrictions are preserved as gaps where the exact UI oracle is missing. This is honest, but it means output is not full coverage. | Future agent-layer iteration should force negative-oracle inventory before writing and produce candidate UI-calibration TCs only when the candidate format can pass validator rules. |
| `REV-AW-002` | warning | structure | all TCs | Preconditions use the same setup path through creating a blank application. This is reproducible, but the FT field scope itself does not specify a reusable fixture for all mandatory surrounding fields. | Add package-level fixture catalog for AutoFin application-card field checks. |
| `REV-AW-003` | warning | traceability | `DICT-AW-REL-001` | The relation list is copied from the FT row, but closed-set behavior is not asserted because source does not say "only". | BA should confirm whether the list is closed or comes from a maintained dictionary. |

## Sign-Off Decision

`not-signed-off-direct-review`: the canary artifact is usable for manual review, but direct reviewer notes include warnings and unresolved source gaps. This should not be treated as lifecycle `signed-off`.

