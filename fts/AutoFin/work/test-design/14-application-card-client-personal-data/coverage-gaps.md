## Coverage Gaps

### GAP-001

**FT Reference:** `BSR 48, 51, 54, 61-63, 67, 71, 75`.
**Source Path:** `SRC-002..SRC-004; SRC-007; SRC-009..SRC-011`.
**Description:** Exact observable UI reaction на invalid value не определена.
**Temporary Handling:** `SO-NEG-001`..`SO-NEG-015` materialized as separate candidate UI-calibration TC.
**Blocks Ready For Review:** `no`.

### GAP-002

**FT Reference:** Table 4 column `О`; `BSR 68, 72, 76`.
**Source Path:** `SRC-002; SRC-003; SRC-006; SRC-007; SRC-009..SRC-011`.
**Description:** Empty-value UI oracle and marker semantics are not specified.
**Temporary Handling:** `SO-REQ-001`..`SO-REQ-005` materialized as separate candidate UI-calibration TC.
**Blocks Ready For Review:** `no`.

### GAP-003

**FT Reference:** `BSR 49, 52, 55, 57, 59, 69, 73, 77`.
**Source Path:** `SRC-002..SRC-006; SRC-009..SRC-011`.
**Description:** Failure/retry/fallback and technical proof of DaData/ABS attribution are not defined.
**Temporary Handling:** Cover only UI-visible success effects; do not assert backend logs, retry, fallback or provider attribution.
**Blocks Ready For Review:** `no`.
