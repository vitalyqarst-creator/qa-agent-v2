# Test-design Applicability Matrix

| dimension | applicable | source_ref | reason | linked_atoms | linked_test_cases | gap_id |
| --- | --- | --- | --- | --- | --- | --- |
| `other` | `yes` | `BSR 35` | Visibility/availability is explicitly stated. | `ATOM-001` | `TC-ACCS-001` |  |
| `other` | `no` | `scope-contract.md` | No closed list or dictionary is referenced by rows 002-003. | `none_required:no_source` | `none_required:no_source` |  |
| `other` | `yes` | `BSR 36`; `BSR 37`; `BSR 38` | Rows define positive display/action outcomes; exact prefill mapping remains a separate gap. | `ATOM-002`; `ATOM-003`; `ATOM-004`; `ATOM-005` | `TC-ACCS-002`; `TC-ACCS-003`; `TC-ACCS-004`; `GAP-001` | `GAP-001` |
| `other` | `no` | `scope-contract.md` | No invalid action/input behavior is stated. | `none_required:no_source` | `none_required:no_source` |  |
| `other` | `yes` | `BSR 37`; `BSR 38` | Widget transition and button window opening are independently testable. | `ATOM-003`; `ATOM-004` | `TC-ACCS-003`; `TC-ACCS-004` | `GAP-001` |
| `other` | `no` | `scope-coverage-gaps.md` | Calculation logic belongs to external FT `Калькулятор`. | `none_required:out_of_scope` | `none_required:out_of_scope` | `GAP-001` |
| `other` | `no` | `scope-contract.md` | No backend/API effect is stated for rows 002-003. | `none_required:no_source` | `none_required:no_source` |  |
| `other` | `no` | `scope-contract.md` | No role/status/security rule is stated in rows 002-003. | `none_required:no_source` | `none_required:no_source` |  |
