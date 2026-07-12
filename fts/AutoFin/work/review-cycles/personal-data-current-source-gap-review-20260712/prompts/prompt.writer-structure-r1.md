# Writer structure remediation

Resolve deterministic structure-preflight blockers from `structure-preflight-r1`.

## Blocking findings
- `structure-preflight-test-case-id-sequence-not-contiguous`: Test case IDs are not a contiguous ordered sequence
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md`
  Action: Renumber test cases into one contiguous ordered sequence without gaps.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-001 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-001`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-002 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-002`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-003 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-003`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-004 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-004`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-005 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-005`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-006 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-006`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-007 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-007`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-008 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-008`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-009 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-009`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-010 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-010`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-011 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-011`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-012 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-012`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-013 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-013`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-014 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-014`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-015 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-015`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-016 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-016`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-017 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-017`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-018 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-018`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-019 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-019`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-020 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-020`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-021 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-021`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-046 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-046`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-047 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-047`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-048 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-048`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-049 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-049`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-025 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-025`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-026 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-026`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-027 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-027`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-028 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-028`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-029 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-029`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-030 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-030`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-031 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-031`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-032 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-032`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-033 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-033`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-034 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-034`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-035 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-035`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-036 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-036`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-037 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-037`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-038 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-038`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-039 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-039`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-050 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-050`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-041 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-041`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-042 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-042`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-043 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-043`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-044 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-044`
  Action: Add every required runtime field and section to this test case.
- `structure-preflight-test-case-runtime-field-missing`: TC-ACPD-045 is missing required runtime fields
  Evidence: `work/review-cycles/personal-data-current-source-gap-review-20260712/outputs/writer-r1-draft.md#TC-ACPD-045`
  Action: Add every required runtime field and section to this test case.

After remediation, update the writer artifacts and scoped validator profile, then return the cycle to writer-draft-ready.
