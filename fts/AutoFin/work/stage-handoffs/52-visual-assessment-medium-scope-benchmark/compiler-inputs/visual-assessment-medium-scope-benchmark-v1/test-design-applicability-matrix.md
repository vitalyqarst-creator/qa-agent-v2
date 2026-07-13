# Test-Design Applicability Matrix — Medium-Scope Benchmark

| dimension | applicable | source_ref | reason | linked_atoms | linked_test_cases | gap_id |
| --- | --- | --- | --- | --- | --- | --- |
| conditional-visibility | `yes` | `BSR 313; BSR 314; BSR 317` | Значение `Визуальная информация` и checkbox `Другое` управляют зависимыми controls. | `ATOM-003; ATOM-004; ATOM-005; ATOM-009` | `TC-VAMB-003; TC-VAMB-004; TC-VAMB-008` | `none_required:covered` |
| dependency | `yes` | `BSR 313; BSR 314` | Positive и inverse branches должны проверяться раздельно. | `ATOM-003; ATOM-004; ATOM-005` | `TC-VAMB-003; TC-VAMB-004` | `none_required:covered` |
| other | `yes` | `BSR 315; DICT-001` | Appendix 1 задаёт полный фиксированный состав и checkbox controls. | `ATOM-006; ATOM-007; ATOM-013` | `TC-VAMB-005; TC-VAMB-006; TC-VAMB-012` | `none_required:covered` |
| other | `yes` | `BSR 311; BSR 312` | Visibility и default value являются наблюдаемыми UI properties. | `ATOM-001; ATOM-002` | `TC-VAMB-001; TC-VAMB-002` | `none_required:covered` |
| requiredness | `yes` | `BSR 316; BSR 317; SO-REQ-001; SO-REQ-002` | Requiredness source-backed, exact UI mechanism needs later calibration. | `ATOM-008; ATOM-010` | `TC-VAMB-007; TC-VAMB-009` | `none_required:ui-calibration` |
| other | `yes` | `analyst-answer-2026-06-30` | Standalone comment input mapping is closed by analyst answer and mockup mapping. | `ATOM-011; ATOM-012` | `TC-VAMB-010; TC-VAMB-011` | `none_required:covered` |
