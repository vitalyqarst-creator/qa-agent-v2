# Test Design Review

| review_item | status | severity | affected_package | evidence | required_action | blocks_ready_for_review |
| --- | --- | --- | --- | --- | --- | --- |
| `decision-table-classification` | `pass` | `info` | `WP-01` | `test-design-decision-table.md` maps five testable properties and one exact-mapping gap. | `none_required:pass` | `no` |
| `ledger-plan-alignment` | `pass` | `info` | `WP-01` | Every `ATOM-*` has a TC or explicit `GAP-001` mapping. | `none_required:pass` | `no` |
| `coverage-class-completeness` | `pass` | `info` | `WP-01` | `coverage-obligation-table.md` contains all source-backed obligations. | `none_required:pass` | `no` |
| `numeric-length-boundaries` | `pass` | `info` | `WP-01` | No numeric input or boundary validation belongs to rows 002-003. | `none_required:pass` | `no` |
| `conditional-branches` | `pass` | `info` | `WP-01` | No inverse branch is stated for visibility/action behavior. | `none_required:pass` | `no` |
| `dictionary-closed-set` | `pass` | `info` | `WP-01` | No dictionary or closed list is referenced. | `none_required:pass` | `no` |
| `mask-format-coverage` | `pass` | `info` | `WP-01` | No mask/format rule is in rows 002-003. | `none_required:pass` | `no` |
| `negative-fixture-isolation` | `pass` | `info` | `WP-01` | No negative class is source-backed. | `none_required:pass` | `no` |
| `applicability-linked-tc-semantics` | `pass` | `info` | `WP-01` | Applicable dimensions link to semantic TC coverage or `GAP-001`. | `none_required:pass` | `no` |
| `gap-admissibility` | `pass` | `info` | `WP-01` | `GAP-001` is non-blocking and visible. | `none_required:pass` | `no` |
| `gap-specificity` | `pass` | `info` | `WP-01` | `GAP-001` names calculator screen, calculations, offer selection, exhaustive prefill fields and exact mapping while preserving observable prefill presence as testable. | `none_required:pass` | `no` |
| `unsupported-ui-mechanism` | `pass` | `info` | `WP-01` | No exact UI text, validation marker, calculation, offer selection or prefill mapping is invented. | `none_required:pass` | `no` |
| `internal-observability` | `pass` | `info` | `WP-01` | Expected results are visible widget, listed params/values, transition, opened window or observable prefill presence. | `none_required:pass` | `no` |
| `metadata-only-exclusion` | `pass` | `info` | `WP-01` | O/R/type metadata is not promoted into standalone TCs without behavior. | `none_required:pass` | `no` |
| `tc-mapping-atomicity` | `pass` | `info` | `WP-01` | Five TCs cover five atomic obligations; exact mapping remains a separate gap atom. | `none_required:pass` | `no` |
| `ready-for-tc-writing` | `pass` | `info` | `WP-01` | Canonical TC file and split artifacts are synchronized. | `none_required:pass` | `no` |
