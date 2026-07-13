# Test Design Decision Table

Mappings are a direct projection of the immutable ledger; candidate calibration status does not change TC identity.

| decision_id | package_id | linked_atom_id | decision | planned_tc_or_gap | oracle_status | rationale |
| --- | --- | --- | --- | --- | --- | --- |
| `DD-001` | `WP-01` | `ATOM-001` | `shared-visibility` | `TC-ACPD-001` | `source-backed` | Block visibility. |
| `DD-002` | `WP-01` | `ATOM-002` | `shared-visibility` | `TC-ACPD-001` | `source-backed` | Always-visible surname. |
| `DD-003` | `WP-01` | `ATOM-003` | `requiredness-calibration` | `TC-ACPD-022` | `ui-calibration-required` | `GAP-002`. |
| `DD-004` | `WP-01` | `ATOM-004` | `shared-editability` | `TC-ACPD-002` | `source-backed` | Editable surname. |
| `DD-005` | `WP-01` | `ATOM-005` | `format-and-calibration` | `TC-ACPD-003`; `TC-ACPD-016`; `TC-ACPD-017` | `ui-calibration-required` | Valid text plus two invalid classes; `GAP-001`. |
| `DD-006` | `WP-01` | `ATOM-006` | `integration-success-path` | `TC-ACPD-004` | `source-backed-success-only` | `GAP-003`. |
| `DD-007` | `WP-01` | `ATOM-007` | `shared-visibility` | `TC-ACPD-001` | `source-backed` | Always-visible name. |
| `DD-008` | `WP-01` | `ATOM-008` | `requiredness-calibration` | `TC-ACPD-023` | `ui-calibration-required` | `GAP-002`. |
| `DD-009` | `WP-01` | `ATOM-009` | `shared-editability` | `TC-ACPD-002` | `source-backed` | Editable name. |
| `DD-010` | `WP-01` | `ATOM-010` | `format-and-calibration` | `TC-ACPD-005`; `TC-ACPD-018`; `TC-ACPD-019` | `ui-calibration-required` | Valid text plus two invalid classes; `GAP-001`. |
| `DD-011` | `WP-01` | `ATOM-011` | `integration-success-path` | `TC-ACPD-006` | `source-backed-success-only` | `GAP-003`. |
| `DD-012` | `WP-01` | `ATOM-012` | `shared-visibility` | `TC-ACPD-001` | `source-backed` | Always-visible patronymic. |
| `DD-013` | `WP-01` | `ATOM-013` | `optional-field` | `TC-ACPD-047` | `source-backed` | Column `О=Нет`. |
| `DD-014` | `WP-01` | `ATOM-014` | `shared-editability` | `TC-ACPD-002` | `source-backed` | Editable patronymic. |
| `DD-015` | `WP-01` | `ATOM-015` | `format-and-calibration` | `TC-ACPD-007`; `TC-ACPD-020`; `TC-ACPD-021` | `ui-calibration-required` | Valid text plus two invalid classes; `GAP-001`. |
| `DD-016` | `WP-01` | `ATOM-016` | `integration-success-path` | `TC-ACPD-008` | `source-backed-success-only` | `GAP-003`. |
| `DD-017` | `WP-01` | `ATOM-017` | `field-property` | `TC-ACPD-009` | `source-backed` | Visible and readonly. |
| `DD-018` | `WP-01` | `ATOM-018` | `integration-success-path` | `TC-ACPD-010` | `source-backed-success-only` | `GAP-003`. |
| `DD-019` | `WP-01` | `ATOM-019` | `dictionary-and-requiredness` | `TC-ACPD-011`; `TC-ACPD-024` | `ui-calibration-required` | `DICT-001`; `GAP-002`. |
| `DD-020` | `WP-01` | `ATOM-020` | `integration-success-path` | `TC-ACPD-012` | `source-backed-success-only` | `GAP-003`. |
| `DD-021` | `WP-01` | `ATOM-021` | `field-property-and-requiredness` | `TC-ACPD-013`; `TC-ACPD-025` | `ui-calibration-required` | `GAP-002`. |
| `DD-022` | `WP-01` | `ATOM-022` | `date-boundary-and-calibration` | `TC-ACPD-014`; `TC-ACPD-026` | `ui-calibration-required` | `GAP-001`. |
| `DD-023` | `WP-01` | `ATOM-023` | `date-boundary-calibration` | `TC-ACPD-027` | `ui-calibration-required` | `GAP-001`. |
| `DD-024` | `WP-01` | `ATOM-024` | `date-boundary-and-calibration` | `TC-ACPD-015`; `TC-ACPD-028` | `ui-calibration-required` | `GAP-001`. |
| `DD-025` | `WP-01` | `ATOM-025` | `d-relative-date-context` | `TC-ACPD-014`; `TC-ACPD-015`; `TC-ACPD-026`; `TC-ACPD-027`; `TC-ACPD-028` | `ui-calibration-required` | SEM-001 closure; `GAP-001`. |
| `DD-026` | `WP-01` | `ATOM-026` | `field-property` | `TC-ACPD-029` | `source-backed` | Toggle values. |
| `DD-027` | `WP-01` | `ATOM-027` | `default-state` | `TC-ACPD-030` | `source-backed` | Default `Нет`. |
| `DD-028` | `WP-02` | `ATOM-028` | `conditional-visibility` | `TC-ACPD-031`; `TC-ACPD-032` | `source-backed` | Both branches. |
| `DD-029` | `WP-02` | `ATOM-029` | `shared-editability` | `TC-ACPD-033` | `source-backed` | Visible branch. |
| `DD-030` | `WP-02` | `ATOM-030` | `format-and-calibration` | `TC-ACPD-034`; `TC-ACPD-035`; `TC-ACPD-036` | `ui-calibration-required` | `GAP-001`. |
| `DD-031` | `WP-02` | `ATOM-031` | `group-requiredness-calibration` | `TC-ACPD-041` | `ui-calibration-required` | `GAP-002`. |
| `DD-032` | `WP-02` | `ATOM-032` | `integration-success-path` | `TC-ACPD-037` | `source-backed-success-only` | `GAP-003`. |
| `DD-033` | `WP-02` | `ATOM-033` | `conditional-visibility` | `TC-ACPD-031`; `TC-ACPD-032` | `source-backed` | Both branches. |
| `DD-034` | `WP-02` | `ATOM-034` | `shared-editability` | `TC-ACPD-033` | `source-backed` | Visible branch. |
| `DD-035` | `WP-02` | `ATOM-035` | `format-and-calibration` | `TC-ACPD-038`; `TC-ACPD-039`; `TC-ACPD-040` | `ui-calibration-required` | `GAP-001`. |
| `DD-036` | `WP-02` | `ATOM-036` | `group-requiredness-calibration` | `TC-ACPD-041` | `ui-calibration-required` | `GAP-002`. |
| `DD-037` | `WP-02` | `ATOM-037` | `integration-success-path` | `TC-ACPD-042` | `source-backed-success-only` | `GAP-003`. |
| `DD-038` | `WP-02` | `ATOM-038` | `conditional-visibility` | `TC-ACPD-031`; `TC-ACPD-032` | `source-backed` | Both branches. |
| `DD-039` | `WP-02` | `ATOM-039` | `shared-editability` | `TC-ACPD-033` | `source-backed` | Visible branch. |
| `DD-040` | `WP-02` | `ATOM-040` | `format-and-calibration` | `TC-ACPD-043`; `TC-ACPD-044`; `TC-ACPD-045` | `ui-calibration-required` | `GAP-001`. |
| `DD-041` | `WP-02` | `ATOM-041` | `group-requiredness-calibration` | `TC-ACPD-041` | `ui-calibration-required` | `GAP-002`. |
| `DD-042` | `WP-02` | `ATOM-042` | `integration-success-path` | `TC-ACPD-046` | `source-backed-success-only` | `GAP-003`. |
