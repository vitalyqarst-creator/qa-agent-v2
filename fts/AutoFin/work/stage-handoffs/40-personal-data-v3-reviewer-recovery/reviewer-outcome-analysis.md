# Анализ reviewer outcome V3

## Вывод

V3 успешно доказал техническое исправление: writer и reviewer отработали в двух отдельных `codex exec` sessions, reviewer prompt уложился в лимит, а `changes-required` корректно сохранился в state.

Semantic sign-off не получен: 4 error findings затрагивают 11 obligations и 9 уникальных TC. Draft остаётся unsigned и не переносится в `test-cases/`.

## Доказанный технический результат

- Writer context: 96 886 / 131 072 bytes.
- Reviewer context: 120 519 / 131 072 bytes; headroom 10 553 bytes.
- Backend session IDs: two distinct IDs.
- Persisted state: `workflow_status=changes-required`, `reviewer_stage_status=changes-required`, `accepted_terminal_state=false`, `final_promoted=false`.
- Writer deterministic gates: structure pass; obligation coverage 65/65; quality bundle pass; semantic overlap clean; seed and evidence gates pass.
- Boundary: production target absent; V1/V2 artifacts unchanged.

## Blocking findings

| finding | obligations | TC | failure shape |
| --- | --- | --- | --- |
| `FIND-001` | `OBL-024` | `TC-ACPD-010` | Generic fixture for saving; no reproducible expected ABS client ID comparison. |
| `FIND-002` | `OBL-027` | `TC-ACPD-012` | No concrete DaData FIO/suggestion/gender fixture or captured comparison. |
| `FIND-003` | `OBL-028` | `TC-ACPD-013` | Vague valid date and non-observable field-type oracle. |
| `FIND-004` | `OBL-003`, `OBL-010`, `OBL-017`, `OBL-026`, `OBL-029`, `OBL-048`, `OBL-056`, `OBL-064` | `TC-ACPD-022`, `023`, `024`, `025`, `041`, `047` | Undefined "continue scenario" action; expected result repeats FT or defers the observable. |

The structured obligation review has 11 `incorrect` rows. The prose summary says "eight obligations"; this is a reviewer reporting-count defect, not a reason to invalidate the verdict, because the itemized rows and four findings are internally traceable.

## Root cause

This is not only a writer phrasing error.

1. The prepared package already instructs requiredness cases to "leave empty when attempting to continue the scenario" without naming a concrete action.
2. Its observables explicitly say the exact UI reaction is unknown, but the package still marks these obligations as testable without defining an evidence-collection oracle.
3. The ABS and DaData obligations contain intent, but no reproducible fixture or capture-and-compare protocol.
4. The deterministic quality bundle checks structure, identifiers, mappings and overlap, but does not reject generic fixtures, undefined transition verbs or source-rule-only expected results.
5. The writer therefore produced a structurally valid 47-case draft that remains partly non-executable.

## Required remediation before V4

- Refine design inputs for the 11 obligations: concrete fixture or explicit calibration fixture contract, concrete action, and observable result.
- Do not invent UI controls or exact validation text absent from FT; where `GAP-002` applies, define neutral UI evidence capture and preserve the gap.
- Add a deterministic/simulated regression that rejects the observed placeholder shapes.
- Recompile a new immutable package and require exact seed/hash/context preflight.
- Start V4 live only after the targeted regression and existing runner/compiler suite pass.

## Stop decision

No second V3 live is authorized. V3 draft, state and findings remain immutable evidence. Promotion and baseline changes are forbidden.
