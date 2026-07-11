# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `prepared-autofin-expanded-matrix` |
| stage | `ft-scope-analyzer / compiler architecture` |
| started_from | `work/stage-handoffs/20-prepared-autofin-cross-scope/workflow-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `gap-classification` | print-form orphan gaps | Link source/setup limitations as constraints on testable atoms | Removing them would lose known limitations; changing atoms to gaps would suppress executable behavior | print-form ledger; package v4 | high | applied |
| `DEC-002` | 2 | `traceability-contract` | atoms and obligations were conflated | Require compiler contract v2 with explicit `OBL -> ATOM -> TC/GAP` | One atom may produce several independent coverage classes | compiler/reference/migrator | high | applied |
| `DEC-003` | 3 | `routing` | generic applicability labels hid navigation | Merge obligation property routing with applicability routing | Fast-path eligibility must follow actual obligation semantics | compiler tests and common-actions package | high | applied |
| `DEC-004` | 4 | `migration-boundary` | large scopes have incomplete obligation tables | Preserve them as blocked matrix candidates | Mechanical completion would invent or misattach obligations | expanded matrix report | high | blocked |
| `DEC-005` | 5 | `dictionary-hierarchy` | eight duplicate `DICT-001` rows | Create parent `DICT-001` with eight stable child ids | Preserves the list hierarchy and removes identity collision | visual dictionary inventory | high | applied |
| `DEC-006` | 6 | `live-gate` | six packages built; three legacy scopes blocked | Do not start live in this iteration | User authorized points 1-4 only; live belongs to the next gate | workflow state | high | applied |
