# Writer Quality Gate

| gate_item | status | evidence | affected_package | required_action | blocks_ready_for_review |
| --- | --- | --- | --- | --- | --- |
| `required-inputs-read` | `pass` | `writer-session-log.writer-r1.md` lists resolver output and required scope artifacts. | `WP-01` | `none_required` | `no` |
| `xhtml-source-available` | `pass` | `source-selection.md`: `xhtml_available: yes`; `source-excerpt.writer-r1.md` contains selected XHTML rows. | `WP-01` | `none_required` | `no` |
| `source-parity-check-read` | `pass` | `source-parity-check.md` reports no discrepancy for `SRC-001`..`SRC-003`. | `WP-01` | `none_required` | `no` |
| `scope-boundary-preserved` | `pass` | Canonical TCs reference only `SRC-001`..`SRC-003`. | `WP-01` | `none_required` | `no` |
| `no-generated-canary-source-basis` | `pass` | Session log contamination check excludes prior canary and generated artifacts. | `WP-01` | `none_required` | `no` |
| `atomic-ledger-complete` | `pass` | `atomic-requirements-ledger.md` has atoms for all source statements. | `WP-01` | `none_required` | `no` |
| `candidate-ui-calibration-markers` | `pass` | All TCs include oracle/test-case status and concrete fixture data to record. | `WP-01` | `none_required` | `no` |
| `unsupported-null-oracle-not-invented` | `pass` | `GAP-001` covers `ATOM-006`; canonical TC only asserts visible empty state. | `WP-01` | `none_required` | `no` |
| `runtime-tc-format` | `pass` | Canonical TCs use `## TC-*`, bold metadata and required runtime sections. | `WP-01` | `none_required` | `no` |
| `scoped-validator-profile` | `pass` | `scoped-validator-profile.writer-r1.json`: `unresolved_warning_error_count = 0`. | `WP-01` | `none_required` | `no` |
