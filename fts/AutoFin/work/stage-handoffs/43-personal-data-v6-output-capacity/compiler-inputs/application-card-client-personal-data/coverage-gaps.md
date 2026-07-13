# Coverage Gaps

### GAP-001

**FT Reference:** `BSR 48, 51, 54, 61–63, 67, 71, 75`; `SRC-002..SRC-004`; `SRC-007`; `SRC-009..SRC-011`.

| field | value |
| --- | --- |
| linked_atoms | `ATOM-005`; `ATOM-010`; `ATOM-015`; `ATOM-022`; `ATOM-023`; `ATOM-024`; `ATOM-025`; `ATOM-030`; `ATOM-035`; `ATOM-040` |
| status | `open` |
| impact | `non-blocking` |
| missing_behavior | Exact UI reaction to invalid text and date-boundary values is not specified. |
| handling | Keep calibration candidates; do not invent a message, highlight, filtering, blocked save, or transition. |

### GAP-002

**FT Reference:** Table 4 column `О`; `BSR 68, 72, 76`; `SRC-002`; `SRC-003`; `SRC-006`; `SRC-007`; `SRC-009..SRC-011`.

| field | value |
| --- | --- |
| linked_atoms | `ATOM-003`; `ATOM-008`; `ATOM-019`; `ATOM-021`; `ATOM-031`; `ATOM-036`; `ATOM-041` |
| status | `open` |
| impact | `non-blocking` |
| missing_behavior | Empty-value marker and validation reaction are not specified. |
| handling | Preserve requiredness calibration candidates and do not infer a message or save behavior. |

### GAP-003

**FT Reference:** `BSR 49, 52, 55, 57, 59, 69, 73, 77`; `SRC-002..SRC-006`; `SRC-009..SRC-011`.

| field | value |
| --- | --- |
| linked_atoms | `ATOM-006`; `ATOM-011`; `ATOM-016`; `ATOM-018`; `ATOM-020`; `ATOM-032`; `ATOM-037`; `ATOM-042` |
| status | `open` |
| impact | `non-blocking` |
| missing_behavior | DaData/ABS failure, retry, fallback and provider-attribution artifacts are not specified. |
| handling | Cover only source-backed UI-visible success effects; retain the technical-attribution limitation. |
