## Test Design Review

| review_item | status | evidence | required_action | blocks_ready_for_review |
| --- | --- | --- | --- | --- |
| `source-row-completeness` | `pass` | `SRC-001`..`SRC-011` mapped. | `none_required:pass` | `no` |
| `bsr-completeness` | `pass` | `BSR 47`..`BSR 77` mapped. | `none_required:pass` | `no` |
| `atom-count` | `pass` | `ATOM-001`..`ATOM-042` materialized. | `none_required:pass` | `no` |
| `calibration-obligations` | `pass` | 15 negative + 5 requiredness candidate TC materialized. | `none_required:pass` | `no` |
| `unsupported-oracles` | `pass` | Candidate TC use `ui-calibration-required` and do not assert exact message/highlight/filter/save behavior. | `none_required:pass` | `no` |
| `package-sequence` | `pass` | `WP-01` rows precede `WP-02` rows in ledger and TC ordering. | `none_required:pass` | `no` |
