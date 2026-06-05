# Canonical Round-Cap Test Cases

## Test-design Applicability Matrix

| dimension | applicable | source_ref | reason | linked_atoms | linked_test_cases | gap_id |
| --- | --- | --- | --- | --- | --- | --- |
| scenario-use-case | yes | FT-CANON-1 | Main success flow is in scope. | ATOM-001 | TC-CANON-RC-001 | - |
| traceability | yes | FT-CANON-2 | Secondary required behavior is not covered. | ATOM-002 | - | coverage_gap:missing-secondary-behavior |

## Risk / Priority Map

| atom_id | risk_level | risk_factors | source_ref | required_priority | linked_test_cases | gap_id | rationale |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ATOM-001 | medium | main flow | FT-CANON-1 | Medium | TC-CANON-RC-001 | - | Main user-visible behavior. |
| ATOM-002 | high | missing required behavior | FT-CANON-2 | High | - | coverage_gap:missing-secondary-behavior | Required behavior remains uncovered. |

## TC-CANON-RC-001

**Title:** Save canonical object successfully
**Priority:** Medium
**Type:** Positive
**Goal:** Verify `ATOM-001`.

**Preconditions:**
- User can open the canonical object form.

**Test Data:**
- Required fields contain valid values from `FT-CANON-1`.

**Steps:**
1. Open the canonical object form.
2. Fill the required fields with valid values.
3. Save the object.

**Expected Result:** The object is saved and can be opened again with the submitted values.

**Postconditions:**
- Created object can be removed by test cleanup.

**FT Reference:** `FT-CANON-1`
**Requirement Source:**
- `FT-CANON-1`
**Requirement Source Quote:** The canonical object can be saved when required values are valid.
