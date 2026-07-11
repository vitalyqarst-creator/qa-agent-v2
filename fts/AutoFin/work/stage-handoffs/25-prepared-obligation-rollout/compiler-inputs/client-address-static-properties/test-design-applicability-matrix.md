# Test-design Applicability Matrix

| dimension | applicable | source_ref | reason | linked_atoms | linked_test_cases | gap_id |
| --- | --- | --- | --- | --- | --- | --- |
| `field-property` | `yes` | `SRC-001`; `BSR 107`; `BSR 113`; `BSR 130` | Selected canary rows define unconditional visible block, fields and toggles. | `ATOM-001`; `ATOM-002`; `ATOM-003`; `ATOM-005` | `TC-CASP-001`; `TC-CASP-002`; `TC-CASP-003`; `TC-CASP-005` |  |
| `default-state` | `yes` | `BSR 114`; `BSR 131` | Selected canary rows define directly observable initial values. | `ATOM-004`; `ATOM-006` | `TC-CASP-004`; `TC-CASP-006` |  |
| `conditional-visibility` | `no` | `scope projection` | Conditional address fields and private-house controls remain in the parent standard package. | `none_required:out_of_canary` |  |  |
| `numeric` | `no` | `scope projection` | Numeric address components remain in the parent standard package. | `none_required:out_of_canary` |  |  |
| `integration` | `no` | `scope projection` | DaData and model persistence remain in the parent standard package. | `none_required:out_of_canary` |  |  |
| `scope` | `no` | `application-card-client-addresses` | This is an eval-only prepared projection and cannot replace or promote over the full signed-off parent scope. | `none_required:eval-only` |  |  |
