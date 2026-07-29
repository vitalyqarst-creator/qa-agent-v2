# Scope Coverage Gaps: 07-4.3-client-addresses

## Summary

- `scope_slug`: `4-3-client-addresses`
- `stage`: `ft-scope-analyzer`
- `status`: `source-first-rematerialized`
- `blocking_gaps`: `0`
- `non_blocking_gaps`: `1`

## GAP-001

**gap_id:** `GAP-001`
**gap_type:** `missing-source-definition`
**requirement_codes:** `BSR 116; BSR 118; BSR 119; BSR 125; BSR 141; BSR 143; BSR 144; BSR 150; BSR 324`
**Impact:** `non-blocking`
**blocks_ready_for_review:** `no`
**Status:** `resolved`
**resolution:** `approved-clarification:CLR-001`
**Problem:** `AGENT-NOTES.md` requires package-local DaData vendor reference for DaData-backed address fields.
**Handling:** Use `work/vendor-references/dadata-reference.md` as supporting source without inferring AutoFin trigger/debounce/fallback behavior.

## GAP-002

**gap_id:** `GAP-002`
**gap_type:** `ambiguity`
**requirement_codes:** `BSR 115; BSR 116; BSR 117; BSR 118; BSR 119; BSR 120; BSR 121; BSR 122; BSR 123; BSR 124; BSR 125; BSR 126; BSR 127; BSR 128; BSR 129; BSR 130; BSR 131; BSR 132; BSR 133; BSR 134; BSR 135; BSR 136; BSR 137; BSR 138; BSR 139; BSR 140; BSR 141; BSR 142; BSR 143; BSR 144; BSR 145; BSR 146; BSR 147; BSR 148; BSR 149; BSR 150; BSR 151; BSR 152; BSR 153; BSR 154; BSR 155; BSR 156; BSR 157; BSR 158; BSR 159; BSR 160; BSR 161; BSR 324`
**Impact:** `non-blocking`
**blocks_ready_for_review:** `no`
**Status:** `resolved`
**resolution:** `approved-clarification:CLR-002`
**Problem:** `support/client-addresses-approved-clarifications-v3.md` uses older scope metadata.
**Handling:** User confirmed v3 applicability to current rc5 scope `4-3-client-addresses`; preserve source-scope override in approved clarification records.

## GAP-003

**gap_id:** `GAP-003`
**gap_type:** `missing-expected-result`
**requirement_codes:** `BSR 117; BSR 124; BSR 125; BSR 127; BSR 128; BSR 130; BSR 132; BSR 133; BSR 134; BSR 142; BSR 150; BSR 153; BSR 154; BSR 155; BSR 157; BSR 159; BSR 161`
**Impact:** `non-blocking`
**blocks_ready_for_review:** `no`
**Status:** `open`
**resolution:** `not-provided`
**affected_assertion_id:** ASSERT-ADDR-005; ASSERT-ADDR-013; ASSERT-ADDR-014; ASSERT-ADDR-021; ASSERT-ADDR-023; ASSERT-ADDR-031; ASSERT-ADDR-040; ASSERT-ADDR-047; ASSERT-ADDR-049; ASSERT-ADDR-051; ASSERT-ADDR-052; ASSERT-ADDR-053; ASSERT-ADDR-056; ASSERT-ADDR-057; ASSERT-ADDR-058; ASSERT-ADDR-059; ASSERT-ADDR-060; ASSERT-ADDR-061; ASSERT-ADDR-062
**affected_atom_id:** ATOM-ADDR-005; ATOM-ADDR-013; ATOM-ADDR-014; ATOM-ADDR-021; ATOM-ADDR-023; ATOM-ADDR-031; ATOM-ADDR-040; ATOM-ADDR-047; ATOM-ADDR-049; ATOM-ADDR-051; ATOM-ADDR-052; ATOM-ADDR-053; ATOM-ADDR-056; ATOM-ADDR-057; ATOM-ADDR-058; ATOM-ADDR-059; ATOM-ADDR-060; ATOM-ADDR-061; ATOM-ADDR-062
**Problem:** FT defines requiredness or numeric restrictions, but not exact UI message/trigger for every invalid manual-input variant.
**Handling:** Generate only source-backed behavior and mark exact UI-message expectations as calibration-pending; do not invent message text.

## GAP-ADDR-001

**gap_id:** `GAP-ADDR-001`
**gap_type:** `ambiguity`
**requirement_codes:** `BSR 118; BSR 119; BSR 143; BSR 144`
**Impact:** `non-blocking`
**blocks_ready_for_review:** `no`
**Status:** `resolved`
**resolution:** `approved-clarification:CLR-ADDR-001`
**Problem:** Need exact DaData result-state classification for found/not-found address.
**Handling:** Use `CLR-ADDR-001`; do not create a partial-found state.

## GAP-ADDR-002

**gap_id:** `GAP-ADDR-002`
**gap_type:** `ambiguity`
**requirement_codes:** `BSR 135`
**Impact:** `non-blocking`
**blocks_ready_for_review:** `no`
**Status:** `resolved`
**resolution:** `approved-clarification:CLR-ADDR-002`
**Problem:** FT uses alias `Адрес постоянной регистрации`.
**Handling:** Treat it as `Адрес регистрации` only for this address scope.

## GAP-ADDR-004

**gap_id:** `GAP-ADDR-004`
**gap_type:** `missing-dictionary-values`
**requirement_codes:** `BSR 125; BSR 150`
**Impact:** `non-blocking`
**blocks_ready_for_review:** `no`
**Status:** `resolved`
**resolution:** `approved-clarification:CLR-ADDR-004`
**Problem:** Separate static project region dictionary is absent.
**Handling:** Use DaData official address suggestions contract as `external-dynamic-dictionary`; do not invent full region list.

## GAP-ADDR-005

**gap_id:** `GAP-ADDR-005`
**gap_type:** `observability`
**requirement_codes:** `BSR 324`
**Impact:** `non-blocking`
**blocks_ready_for_review:** `no`
**Status:** `resolved`
**resolution:** `approved-clarification:CLR-ADDR-005`
**affected_assertion_id:** ASSERT-ADDR-055
**affected_atom_id:** ATOM-ADDR-055
**Problem:** Internal model field `kladr` is not observable in UI scope.
**Handling:** Cover observable address decomposition only; exclude direct `kladr` verification from UI test cases.
