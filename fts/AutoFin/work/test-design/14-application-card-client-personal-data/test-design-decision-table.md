# Test Design Decision Table

## Decision Table

| decision_id | package_id | linked_atom_or_obligation | decision | planned_tc_or_gap | oracle_status | rationale |
| --- | --- | --- | --- | --- | --- | --- |
| `DD-001` | `WP-01` | `ATOM-001` | `standalone_tc` | `TC-ACPD-001` | `source-backed` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-002` | `WP-01` | `ATOM-002` | `standalone_tc` | `TC-ACPD-001` | `source-backed` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-003` | `WP-01` | `ATOM-003` | `standalone_tc` | `TC-ACPD-022` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-004` | `WP-01` | `ATOM-004` | `standalone_tc` | `TC-ACPD-002` | `source-backed` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-005` | `WP-01` | `ATOM-005` | `standalone_tc` | `TC-ACPD-003; TC-ACPD-016; TC-ACPD-017` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-006` | `WP-01` | `ATOM-006` | `standalone_tc` | `TC-ACPD-004` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-007` | `WP-01` | `ATOM-007` | `standalone_tc` | `TC-ACPD-001` | `source-backed` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-008` | `WP-01` | `ATOM-008` | `standalone_tc` | `TC-ACPD-023` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-009` | `WP-01` | `ATOM-009` | `standalone_tc` | `TC-ACPD-002` | `source-backed` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-010` | `WP-01` | `ATOM-010` | `standalone_tc` | `TC-ACPD-005; TC-ACPD-018; TC-ACPD-019` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-011` | `WP-01` | `ATOM-011` | `standalone_tc` | `TC-ACPD-006` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-012` | `WP-01` | `ATOM-012` | `standalone_tc` | `TC-ACPD-001` | `source-backed` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-013` | `WP-01` | `ATOM-013` | `standalone_tc` | `TC-ACPD-047` | `source-backed` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-014` | `WP-01` | `ATOM-014` | `standalone_tc` | `TC-ACPD-002` | `source-backed` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-015` | `WP-01` | `ATOM-015` | `standalone_tc` | `TC-ACPD-007; TC-ACPD-020; TC-ACPD-021` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-016` | `WP-01` | `ATOM-016` | `standalone_tc` | `TC-ACPD-008` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-017` | `WP-01` | `ATOM-017` | `standalone_tc` | `TC-ACPD-009` | `source-backed` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-018` | `WP-01` | `ATOM-018` | `standalone_tc` | `TC-ACPD-010` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-019` | `WP-01` | `ATOM-019` | `standalone_tc` | `TC-ACPD-011; TC-ACPD-024` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-020` | `WP-01` | `ATOM-020` | `standalone_tc` | `TC-ACPD-012` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-021` | `WP-01` | `ATOM-021` | `standalone_tc` | `TC-ACPD-013; TC-ACPD-025` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-022` | `WP-01` | `ATOM-022` | `standalone_tc` | `TC-ACPD-014; TC-ACPD-025` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-023` | `WP-01` | `ATOM-023` | `standalone_tc` | `TC-ACPD-026` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-024` | `WP-01` | `ATOM-024` | `standalone_tc` | `TC-ACPD-015; TC-ACPD-027` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-025` | `WP-01` | `ATOM-025` | `standalone_tc` | `TC-ACPD-014; TC-ACPD-015; TC-ACPD-025; TC-ACPD-026; TC-ACPD-027` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-026` | `WP-01` | `ATOM-026` | `standalone_tc` | `TC-ACPD-028` | `source-backed` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-027` | `WP-01` | `ATOM-027` | `standalone_tc` | `TC-ACPD-029` | `source-backed` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-028` | `WP-02` | `ATOM-028` | `standalone_tc` | `TC-ACPD-030; TC-ACPD-031` | `source-backed` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-029` | `WP-02` | `ATOM-029` | `standalone_tc` | `TC-ACPD-032` | `source-backed` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-030` | `WP-02` | `ATOM-030` | `standalone_tc` | `TC-ACPD-033; TC-ACPD-034; TC-ACPD-035` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-031` | `WP-02` | `ATOM-031` | `standalone_tc` | `TC-ACPD-041` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-032` | `WP-02` | `ATOM-032` | `standalone_tc` | `TC-ACPD-037` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-033` | `WP-02` | `ATOM-033` | `standalone_tc` | `TC-ACPD-030; TC-ACPD-031` | `source-backed` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-034` | `WP-02` | `ATOM-034` | `standalone_tc` | `TC-ACPD-032` | `source-backed` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-035` | `WP-02` | `ATOM-035` | `standalone_tc` | `TC-ACPD-038; TC-ACPD-039; TC-ACPD-040` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-036` | `WP-02` | `ATOM-036` | `standalone_tc` | `TC-ACPD-041` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-037` | `WP-02` | `ATOM-037` | `standalone_tc` | `TC-ACPD-042` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-038` | `WP-02` | `ATOM-038` | `standalone_tc` | `TC-ACPD-030; TC-ACPD-031` | `source-backed` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-039` | `WP-02` | `ATOM-039` | `standalone_tc` | `TC-ACPD-032` | `source-backed` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-040` | `WP-02` | `ATOM-040` | `standalone_tc` | `TC-ACPD-043; TC-ACPD-044; TC-ACPD-045` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-041` | `WP-02` | `ATOM-041` | `standalone_tc` | `TC-ACPD-041` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-042` | `WP-02` | `ATOM-042` | `standalone_tc` | `TC-ACPD-046` | `ui-calibration-required \| source-backed-success-only` | Source row has a discrete observable or explicit calibration/gap constraint. |
| `DD-NEG-001` | `WP-01` | `SO-NEG-001` | `candidate_tc_required` | `TC-ACPD-016` | `ui-calibration-required` | Source defines invalid class but not exact UI reaction. |
| `DD-NEG-002` | `WP-01` | `SO-NEG-002` | `candidate_tc_required` | `TC-ACPD-017` | `ui-calibration-required` | Source defines invalid class but not exact UI reaction. |
| `DD-NEG-003` | `WP-01` | `SO-NEG-003` | `candidate_tc_required` | `TC-ACPD-018` | `ui-calibration-required` | Source defines invalid class but not exact UI reaction. |
| `DD-NEG-004` | `WP-01` | `SO-NEG-004` | `candidate_tc_required` | `TC-ACPD-019` | `ui-calibration-required` | Source defines invalid class but not exact UI reaction. |
| `DD-NEG-005` | `WP-01` | `SO-NEG-005` | `candidate_tc_required` | `TC-ACPD-020` | `ui-calibration-required` | Source defines invalid class but not exact UI reaction. |
| `DD-NEG-006` | `WP-01` | `SO-NEG-006` | `candidate_tc_required` | `TC-ACPD-021` | `ui-calibration-required` | Source defines invalid class but not exact UI reaction. |
| `DD-NEG-007` | `WP-01` | `SO-NEG-007` | `candidate_tc_required` | `TC-ACPD-025` | `ui-calibration-required` | Source defines invalid class but not exact UI reaction. |
| `DD-NEG-008` | `WP-01` | `SO-NEG-008` | `candidate_tc_required` | `TC-ACPD-026` | `ui-calibration-required` | Source defines invalid class but not exact UI reaction. |
| `DD-NEG-009` | `WP-01` | `SO-NEG-009` | `candidate_tc_required` | `TC-ACPD-027` | `ui-calibration-required` | Source defines invalid class but not exact UI reaction. |
| `DD-NEG-010` | `WP-02` | `SO-NEG-010` | `candidate_tc_required` | `TC-ACPD-035` | `ui-calibration-required` | Source defines invalid class but not exact UI reaction. |
| `DD-NEG-011` | `WP-02` | `SO-NEG-011` | `candidate_tc_required` | `TC-ACPD-036` | `ui-calibration-required` | Source defines invalid class but not exact UI reaction. |
| `DD-NEG-012` | `WP-02` | `SO-NEG-012` | `candidate_tc_required` | `TC-ACPD-039` | `ui-calibration-required` | Source defines invalid class but not exact UI reaction. |
| `DD-NEG-013` | `WP-02` | `SO-NEG-013` | `candidate_tc_required` | `TC-ACPD-040` | `ui-calibration-required` | Source defines invalid class but not exact UI reaction. |
| `DD-NEG-014` | `WP-02` | `SO-NEG-014` | `candidate_tc_required` | `TC-ACPD-044` | `ui-calibration-required` | Source defines invalid class but not exact UI reaction. |
| `DD-NEG-015` | `WP-02` | `SO-NEG-015` | `candidate_tc_required` | `TC-ACPD-045` | `ui-calibration-required` | Source defines invalid class but not exact UI reaction. |
| `DD-REQ-001` | `WP-01` | `SO-REQ-001` | `candidate_tc_required` | `TC-ACPD-022` | `ui-calibration-required` | Source defines requiredness but not exact empty-value reaction. |
| `DD-REQ-002` | `WP-01` | `SO-REQ-002` | `candidate_tc_required` | `TC-ACPD-023` | `ui-calibration-required` | Source defines requiredness but not exact empty-value reaction. |
| `DD-REQ-003` | `WP-01` | `SO-REQ-003` | `candidate_tc_required` | `TC-ACPD-024` | `ui-calibration-required` | Source defines requiredness but not exact empty-value reaction. |
| `DD-REQ-004` | `WP-01` | `SO-REQ-004` | `candidate_tc_required` | `TC-ACPD-025` | `ui-calibration-required` | Source defines requiredness but not exact empty-value reaction. |
| `DD-REQ-005` | `WP-02` | `SO-REQ-005` | `candidate_tc_required` | `TC-ACPD-041` | `ui-calibration-required` | Source defines requiredness but not exact empty-value reaction. |
