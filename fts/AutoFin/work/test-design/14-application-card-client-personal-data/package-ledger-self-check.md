# Package Ledger Self-check

| package_id | check | status | evidence | required_action |
| --- | --- | --- | --- | --- |
| `WP-01` | `source-row-preservation` | `pass` | `SRC-001`..`SRC-011` preserved in writer-side inventory. | `none_required:pass` |
| `WP-01` | `atom-package-id` | `pass` | Every `ATOM-*` row has `package_id=WP-01`. | `none_required:pass` |
| `WP-01` | `req-id-preservation` | `pass` | Post-backfill `BSR 39`-`BSR 69` are present in ledger `req_id` values and remain tied to source rows `SRC-002`..`SRC-011`. | `none_required:pass` |
| `WP-01` | `gap-visibility` | `pass` | `GAP-001`; `GAP-002`; `GAP-003` retained. | `none_required:pass` |
