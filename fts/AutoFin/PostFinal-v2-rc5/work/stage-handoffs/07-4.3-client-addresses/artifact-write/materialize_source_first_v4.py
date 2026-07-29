from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[7]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from test_case_agent.review_cycle.prepared_compiler import _expected_source_assertion_rows  # noqa: E402
from test_case_agent.review_cycle.source_assertions import (  # noqa: E402
    _clarification_requirement_codes,
    _clarification_table_rows,
)


FT_ROOT = ROOT / "fts" / "AutoFin" / "PostFinal-v2-rc5"
HANDOFF = FT_ROOT / "work" / "stage-handoffs" / "07-4.3-client-addresses"
SOURCE_PATH = "fts/AutoFin/PostFinal-v2-rc5/source/PostFinal-v2.xhtml"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_json_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def esc(value: object) -> str:
    return str(value).replace("\n", "<br>").replace("|", "\\|")


def explicit(values: list[str]) -> str:
    return "; ".join(values) if values else "none_required"


def row_no(locator: str) -> int | None:
    match = re.search(r"/\*\[116\]/\*\[(\d+)\]$", locator)
    return int(match.group(1)) if match else None


def split_bsr_fragments(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"\bBSR\s+(\d+)\.", text))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        code = f"BSR {match.group(1)}"
        result[code] = text[match.start() : end].strip()
    return result


def clause_binding(kind: str, index: int, source_row_id: str, fragment: str) -> dict[str, object]:
    return {
        "clause_kind": kind,
        "clause_index": index,
        "source_row_id": source_row_id,
        "evidence_role": kind,
        "exact_source_fragment": fragment,
    }


class Builder:
    def __init__(self) -> None:
        self.rows = {item.source_row_id: item.to_dict() for item in _expected_source_assertion_rows(HANDOFF / "source-row-inventory.md")}
        self.row_text = {row_id: row["bounded_source_text"] for row_id, row in self.rows.items()}
        self.fragments = {row_id: split_bsr_fragments(text) for row_id, text in self.row_text.items()}
        self.assertions: list[dict[str, object]] = []
        self.ledger_rows: list[dict[str, object]] = []
        self.obligation_rows: list[dict[str, object]] = []
        self.plan_rows: list[dict[str, object]] = []

    def add_na(
        self,
        *,
        row_id: str,
        statement: str,
        code: str | None = None,
        fragment: str | None = None,
        clarification_bindings: list[dict[str, object]] | None = None,
    ) -> None:
        index = len(self.assertions) + 1
        atom_id = f"ATOM-ADDR-{index:03d}"
        assertion_id = f"ASSERT-ADDR-{index:03d}"
        codes = [code] if code else []
        exact = fragment or self.row_text[row_id]
        req_bindings = []
        if code:
            req_bindings.append(
                {
                    "requirement_code": code,
                    "source_row_id": row_id,
                    "provenance_role": "xhtml-row",
                    "exact_source_fragment": fragment or code,
                    "evidence_source_path": None,
                    "evidence_locator": None,
                }
            )
        self.assertions.append(
            {
                "assertion_id": assertion_id,
                "source_path": SOURCE_PATH,
                "source_context_class": self.rows[row_id]["source_context_class"],
                "locator": self.rows[row_id]["source_locator"],
                "exact_source_text": exact,
                "canonical_statement": statement,
                "polarity": "neutral",
                "semantic_disposition": "not-applicable",
                "execution_readiness": "not-applicable",
                "execution_readiness_rationale": "none_required",
                "risk": "low",
                "condition_clauses": [],
                "action_clauses": [],
                "oracle_clauses": [],
                "requirement_codes": codes,
                "requirement_code_bindings": req_bindings,
                "clause_evidence_bindings": [],
                "source_row_id": row_id,
                "atom_id": atom_id,
                "obligation_ids": [],
                "execution_dependency_gap_ids": [],
                "primary_gap_id": None,
                "supporting_source_bindings": [],
                "clarification_clause_bindings": clarification_bindings or [],
                "disposition_rationale": "Контекстная или внутренне-техническая часть не задает самостоятельную исполнимую UI-проверку в рамках проекта.",
            }
        )
        prop_id = f"PROP-ADDR-{index:03d}"
        obligation_id = f"OBL-ADDR-{index:03d}"
        self.ledger_rows.append(
            {
                "atom_id": atom_id,
                "source_property_id": prop_id,
                "atomic_statement": statement,
                "coverage_status": "not-applicable",
                "source_row_id": row_id,
                "requirement_codes": explicit(codes),
                "constraint_gap_ids": "none_required",
            }
        )
        self.obligation_rows.append(
            {
                "obligation_id": obligation_id,
                "package_id": "WP-NA",
                "source_property_id": prop_id,
                "linked_atom_id": atom_id,
                "property_type": "other",
                "obligation_class": "not-applicable",
                "required_behavior": statement,
                "source_ref": f"{row_id}; {assertion_id}; not-applicable",
                "planned_tc_or_gap": "n/a",
                "status": "not-applicable",
                "review_notes": "non-executable source context retained for source-first traceability; no TC generated",
                "source_row_id": row_id,
                "requirement_codes": explicit(codes),
                "dictionary_refs": "none_required",
                "dictionary_coverage": "none_required",
            }
        )

    def add(
        self,
        *,
        row_id: str,
        code: str,
        statement: str,
        condition: str,
        action: str,
        oracle: str,
        package_id: str,
        property_type: str = "field-property",
        obligation_class: str = "source-backed",
        risk: str = "medium",
        constraint_gaps: list[str] | None = None,
        clarification_bindings: list[dict[str, object]] | None = None,
        dictionary_refs: str = "none_required",
        dictionary_coverage: str = "none_required",
    ) -> None:
        index = len(self.assertions) + 1
        assertion_id = f"ASSERT-ADDR-{index:03d}"
        atom_id = f"ATOM-ADDR-{index:03d}"
        obligation_id = f"OBL-ADDR-{index:03d}"
        prop_id = f"PROP-ADDR-{index:03d}"
        fragment = self.fragments[row_id][code]
        constraint_gaps = constraint_gaps or []
        self.assertions.append(
            {
                "assertion_id": assertion_id,
                "source_path": SOURCE_PATH,
                "source_context_class": self.rows[row_id]["source_context_class"],
                "locator": self.rows[row_id]["source_locator"],
                "exact_source_text": fragment,
                "canonical_statement": statement,
                "polarity": "positive",
                "semantic_disposition": "testable",
                "execution_readiness": "ready",
                "execution_readiness_rationale": "none_required",
                "risk": risk,
                "condition_clauses": [condition],
                "action_clauses": [action],
                "oracle_clauses": [oracle],
                "requirement_codes": [code],
                "requirement_code_bindings": [
                    {
                        "requirement_code": code,
                        "source_row_id": row_id,
                        "provenance_role": "xhtml-row",
                        "exact_source_fragment": fragment,
                        "evidence_source_path": None,
                        "evidence_locator": None,
                    }
                ],
                "clause_evidence_bindings": [
                    clause_binding("condition", 0, row_id, fragment),
                    clause_binding("action", 0, row_id, fragment),
                    clause_binding("oracle", 0, row_id, fragment),
                ],
                "source_row_id": row_id,
                "atom_id": atom_id,
                "obligation_ids": [obligation_id],
                "execution_dependency_gap_ids": [],
                "primary_gap_id": None,
                "supporting_source_bindings": [],
                "clarification_clause_bindings": clarification_bindings or [],
                "exact_source_fragments": [fragment],
            }
        )
        self.ledger_rows.append(
            {
                "atom_id": atom_id,
                "source_property_id": prop_id,
                "atomic_statement": statement,
                "coverage_status": "covered",
                "source_row_id": row_id,
                "requirement_codes": code,
                "constraint_gap_ids": explicit(constraint_gaps),
            }
        )
        self.obligation_rows.append(
            {
                "obligation_id": obligation_id,
                "package_id": package_id,
                "source_property_id": prop_id,
                "linked_atom_id": atom_id,
                "property_type": property_type,
                "obligation_class": obligation_class,
                "required_behavior": statement,
                "source_ref": f"{row_id}; {assertion_id}; {code}",
                "planned_tc_or_gap": f"TC-ADDR-{index:03d}",
                "status": "covered",
                "review_notes": "source-first assertion chain; exact validation message is not asserted where GAP-003 is linked",
                "source_row_id": row_id,
                "requirement_codes": code,
                "dictionary_refs": dictionary_refs,
                "dictionary_coverage": dictionary_coverage,
            }
        )
        self.plan_rows.append(
            {
                "planned_tc_id": f"TC-ADDR-{index:03d}",
                "planned_tc_or_gap": f"TC-ADDR-{index:03d}",
                "linked_atoms": atom_id,
                "planned_check": action,
                "single_expected_behavior": oracle,
                "test_data": "source-backed representative value; do not assert unlisted DaData ordering/count",
                "input_class": "positive",
                "status": "planned",
                "source_ref": f"{row_id}; {assertion_id}; {code}",
            }
        )

    def add_row(
        self,
        *,
        row_id: str,
        statement: str,
        condition: str,
        action: str,
        oracle: str,
        package_id: str,
        property_type: str = "field-property",
        obligation_class: str = "source-backed",
        risk: str = "medium",
        constraint_gaps: list[str] | None = None,
    ) -> None:
        index = len(self.assertions) + 1
        assertion_id = f"ASSERT-ADDR-{index:03d}"
        atom_id = f"ATOM-ADDR-{index:03d}"
        obligation_id = f"OBL-ADDR-{index:03d}"
        prop_id = f"PROP-ADDR-{index:03d}"
        fragment = self.row_text[row_id]
        constraint_gaps = constraint_gaps or []
        self.assertions.append(
            {
                "assertion_id": assertion_id,
                "source_path": SOURCE_PATH,
                "source_context_class": self.rows[row_id]["source_context_class"],
                "locator": self.rows[row_id]["source_locator"],
                "exact_source_text": fragment,
                "canonical_statement": statement,
                "polarity": "positive",
                "semantic_disposition": "testable",
                "execution_readiness": "ready",
                "execution_readiness_rationale": "none_required",
                "risk": risk,
                "condition_clauses": [condition],
                "action_clauses": [action],
                "oracle_clauses": [oracle],
                "requirement_codes": [],
                "requirement_code_bindings": [],
                "clause_evidence_bindings": [
                    clause_binding("condition", 0, row_id, fragment),
                    clause_binding("action", 0, row_id, fragment),
                    clause_binding("oracle", 0, row_id, fragment),
                ],
                "source_row_id": row_id,
                "atom_id": atom_id,
                "obligation_ids": [obligation_id],
                "execution_dependency_gap_ids": [],
                "primary_gap_id": None,
                "supporting_source_bindings": [],
                "clarification_clause_bindings": [],
                "exact_source_fragments": [fragment],
            }
        )
        self.ledger_rows.append(
            {
                "atom_id": atom_id,
                "source_property_id": prop_id,
                "atomic_statement": statement,
                "coverage_status": "covered",
                "source_row_id": row_id,
                "requirement_codes": "none_required",
                "constraint_gap_ids": explicit(constraint_gaps),
            }
        )
        self.obligation_rows.append(
            {
                "obligation_id": obligation_id,
                "package_id": package_id,
                "source_property_id": prop_id,
                "linked_atom_id": atom_id,
                "property_type": property_type,
                "obligation_class": obligation_class,
                "required_behavior": statement,
                "source_ref": f"{row_id}; {assertion_id}; row-typed-cells",
                "planned_tc_or_gap": f"TC-ADDR-{index:03d}",
                "status": "covered",
                "review_notes": "source-first row-typed assertion chain; exact validation message is not asserted where GAP-003 is linked",
                "source_row_id": row_id,
                "requirement_codes": "none_required",
                "dictionary_refs": "none_required",
                "dictionary_coverage": "none_required",
            }
        )
        self.plan_rows.append(
            {
                "planned_tc_id": f"TC-ADDR-{index:03d}",
                "planned_tc_or_gap": f"TC-ADDR-{index:03d}",
                "linked_atoms": atom_id,
                "planned_check": action,
                "single_expected_behavior": oracle,
                "test_data": "source-backed representative value",
                "input_class": "positive",
                "status": "planned",
                "source_ref": f"{row_id}; {assertion_id}; row-typed-cells",
            }
        )


def bind(clarification: dict[str, object], code: str, kind: str = "oracle") -> dict[str, object]:
    return {
        "clarification_id": clarification["clarification_id"],
        "clause_kind": kind,
        "clause_index": 0,
        "requirement_codes": [code],
        "exact_answer_sha256": clarification["exact_answer_sha256"],
    }


def load_clarifications() -> dict[str, dict[str, object]]:
    current_path = "fts/AutoFin/PostFinal-v2-rc5/work/stage-handoffs/07-4.3-client-addresses/scope-clarification-requests.md"
    support_path = "fts/AutoFin/PostFinal-v2-rc5/support/client-addresses-approved-clarifications-v3.md"
    current_rows = _clarification_table_rows((ROOT / current_path).read_text(encoding="utf-8"), source_path=current_path)
    support_rows = _clarification_table_rows((ROOT / support_path).read_text(encoding="utf-8"), source_path=support_path)
    result: dict[str, dict[str, object]] = {}
    for cid in ("CLR-001", "CLR-002"):
        row = current_rows[cid]
        result[cid] = {
            "clarification_id": cid,
            "gap_id": row["gap_id"],
            "scope_slug": "4-3-client-addresses",
            "requirement_codes": list(
                _clarification_requirement_codes(row["requirement_codes"], allow_empty=False)
            ),
            "authority": row["authority"],
            "response_status": row["response_status"],
            "response_type": row["response_type"],
            "answered_at": row["updated_at"],
            "exact_answer": row["user_response"],
            "exact_answer_sha256": sha256_text(row["user_response"]),
            "evidence_source_path": current_path,
            "evidence_source_sha256": sha256_file(ROOT / current_path),
            "binding_scope": "requirement-code",
            "source_row_ids": [],
        }
    for cid in ("CLR-ADDR-001", "CLR-ADDR-002", "CLR-ADDR-004", "CLR-ADDR-005"):
        row = support_rows[cid]
        result[cid] = {
            "clarification_id": cid,
            "gap_id": row["gap_id"],
            "scope_slug": "4-3-client-addresses",
            "requirement_codes": list(
                _clarification_requirement_codes(row["requirement_codes"], allow_empty=False)
            ),
            "authority": row["authority"],
            "response_status": row["response_status"],
            "response_type": row["response_type"],
            "answered_at": row["updated_at"],
            "exact_answer": row["user_response"],
            "exact_answer_sha256": sha256_text(row["user_response"]),
            "evidence_source_path": support_path,
            "evidence_source_sha256": sha256_file(ROOT / support_path),
            "binding_scope": "requirement-code",
            "source_row_ids": [],
            "source_scope_slug": row["scope_slug"],
            "scope_slug_override_reason": "CLR-002 confirmed support/client-addresses-approved-clarifications-v3.md applicability to current rc5 scope 4-3-client-addresses.",
        }
    return result


def add_gap_fields(text: str) -> str:
    text = text.replace("`resolution`: `approved-input:CLR-001`", "`resolution`: `approved-clarification:CLR-001`")
    additions = """

## Source-First Typed Gap Bindings

### GAP-001

**gap_id:** `GAP-001`
**gap_type:** `missing-source-definition`
**requirement_codes:** `BSR 116; BSR 118; BSR 119; BSR 125; BSR 141; BSR 143; BSR 144; BSR 150; BSR 324`
**Impact:** `non-blocking`
**blocks_ready_for_review:** `no`
**Status:** `resolved`
**resolution:** `approved-clarification:CLR-001`

### GAP-002

**gap_id:** `GAP-002`
**gap_type:** `ambiguity`
**requirement_codes:** `BSR 115; BSR 116; BSR 117; BSR 118; BSR 119; BSR 120; BSR 121; BSR 122; BSR 123; BSR 124; BSR 125; BSR 126; BSR 127; BSR 128; BSR 129; BSR 130; BSR 131; BSR 132; BSR 133; BSR 134; BSR 135; BSR 136; BSR 137; BSR 138; BSR 139; BSR 140; BSR 141; BSR 142; BSR 143; BSR 144; BSR 145; BSR 146; BSR 147; BSR 148; BSR 149; BSR 150; BSR 151; BSR 152; BSR 153; BSR 154; BSR 155; BSR 156; BSR 157; BSR 158; BSR 159; BSR 160; BSR 161; BSR 324`
**Impact:** `non-blocking`
**blocks_ready_for_review:** `no`
**Status:** `resolved`
**resolution:** `approved-clarification:CLR-002`

### GAP-003

**gap_id:** `GAP-003`
**gap_type:** `missing-expected-result`
**requirement_codes:** `BSR 117; BSR 124; BSR 125; BSR 127; BSR 128; BSR 130; BSR 132; BSR 133; BSR 134; BSR 142; BSR 150; BSR 153; BSR 154; BSR 155; BSR 157; BSR 159; BSR 161`
**Impact:** `non-blocking`
**blocks_ready_for_review:** `no`
**Status:** `open`
**resolution:** `not-provided`
**Problem:** FT defines requiredness or numeric restrictions, but not exact UI message/trigger for every invalid manual-input variant.
**Handling:** Generate only source-backed behavior and mark exact UI-message expectations as calibration-pending; do not invent message text.

### GAP-ADDR-001

**gap_id:** `GAP-ADDR-001`
**gap_type:** `ambiguity`
**requirement_codes:** `BSR 118; BSR 119; BSR 143; BSR 144`
**Impact:** `non-blocking`
**blocks_ready_for_review:** `no`
**Status:** `resolved`
**resolution:** `approved-clarification:CLR-ADDR-001`

### GAP-ADDR-002

**gap_id:** `GAP-ADDR-002`
**gap_type:** `ambiguity`
**requirement_codes:** `BSR 135`
**Impact:** `non-blocking`
**blocks_ready_for_review:** `no`
**Status:** `resolved`
**resolution:** `approved-clarification:CLR-ADDR-002`

### GAP-ADDR-004

**gap_id:** `GAP-ADDR-004`
**gap_type:** `missing-dictionary-values`
**requirement_codes:** `BSR 125; BSR 150`
**Impact:** `non-blocking`
**blocks_ready_for_review:** `no`
**Status:** `resolved`
**resolution:** `approved-clarification:CLR-ADDR-004`

### GAP-ADDR-005

**gap_id:** `GAP-ADDR-005`
**gap_type:** `observability`
**requirement_codes:** `BSR 324`
**Impact:** `non-blocking`
**blocks_ready_for_review:** `no`
**Status:** `resolved`
**resolution:** `approved-clarification:CLR-ADDR-005`
"""
    if "## Source-First Typed Gap Bindings" not in text:
        text = text.rstrip() + "\n" + additions.strip() + "\n"
    return text


def build_coverage_gaps(
    gap3_assertions: list[str],
    gap3_atoms: list[str],
    gap_addr_005_assertions: list[str],
    gap_addr_005_atoms: list[str],
) -> str:
    return f"""# Scope Coverage Gaps: 07-4.3-client-addresses

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
**affected_assertion_id:** {'; '.join(gap3_assertions)}
**affected_atom_id:** {'; '.join(gap3_atoms)}
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
**affected_assertion_id:** {'; '.join(gap_addr_005_assertions)}
**affected_atom_id:** {'; '.join(gap_addr_005_atoms)}
**Problem:** Internal model field `kladr` is not observable in UI scope.
**Handling:** Cover observable address decomposition only; exclude direct `kladr` verification from UI test cases.
"""


def main() -> None:
    clar = load_clarifications()
    b = Builder()
    gap3 = ["GAP-003"]
    b.add_na(row_id="SRC-ROW-001", statement="Строка заголовков таблицы свойств полей задает контекст колонок и не является самостоятельной UI-проверкой.")
    b.add_na(row_id="SRC-ROW-002", statement="Строка является заголовком блока «Адреса клиента» и не задает самостоятельную исполнимую проверку.")

    b.add(row_id="SRC-ROW-003", code="BSR 115", statement="Поле «Адрес регистрации» всегда видимо.", condition="Открыт блок «Адреса клиента».", action="Открыть блок «Адреса клиента».", oracle="Поле «Адрес регистрации» отображается.", package_id="WP-01", risk="low")
    b.add(row_id="SRC-ROW-003", code="BSR 116", statement="Поле «Адрес регистрации» использует интеграцию с DaData.", condition="Признак «Ввести вручную» для адреса регистрации имеет значение «Нет».", action="Ввести часть адреса в поле «Адрес регистрации».", oracle="Поле использует подсказки DaData; точные trigger/debounce/count/order не утверждаются.", package_id="WP-01", risk="high", clarification_bindings=[bind(clar["CLR-001"], "BSR 116")], dictionary_refs="DICT-DADATA-ADDRESS-SUGGESTIONS", dictionary_coverage="reference-only")
    b.add(row_id="SRC-ROW-003", code="BSR 117", statement="Для адреса регистрации должны быть введены регион и номер дома.", condition="Заполняется адрес регистрации.", action="Оставить регион или дом незаполненным и инициировать проверку адреса.", oracle="Система не принимает адрес регистрации без региона и номера дома; точный UI oracle по пустым полям не утвержден.", package_id="WP-01", risk="high", constraint_gaps=gap3)
    b.add(row_id="SRC-ROW-003", code="BSR 117", statement="Если в адресе регистрации не указана квартира и не отмечен частный дом, поле подсвечивается красным и отображается подсказка о квартире или частном доме.", condition="Адрес регистрации заполнен без квартиры, признак частного дома не активирован.", action="Инициировать проверку адреса регистрации.", oracle="Поле подсвечивается красным и отображается подсказка «Укажите номер квартиры или поставьте отметку о проживании в частном доме».", package_id="WP-01", risk="high")
    b.add(row_id="SRC-ROW-003", code="BSR 118", statement="Если DaData не находит адрес регистрации, отображается подсказка «Некорректно указан адрес».", condition="В поле «Адрес регистрации» введен адрес, который DaData не находит.", action="Инициировать поиск адреса регистрации через DaData.", oracle="Отображается подсказка «Некорректно указан адрес».", package_id="WP-01", risk="high", clarification_bindings=[bind(clar["CLR-001"], "BSR 118"), bind(clar["CLR-ADDR-001"], "BSR 118")])
    b.add(row_id="SRC-ROW-003", code="BSR 119", statement="Если адрес регистрации найден в DaData, он раскладывается по полям блока ручного ввода.", condition="DaData нашла адрес регистрации.", action="Выбрать найденный адрес регистрации.", oracle="Выбранный адрес раскладывается по полям блока ручного ввода.", package_id="WP-01", risk="high", clarification_bindings=[bind(clar["CLR-001"], "BSR 119"), bind(clar["CLR-ADDR-001"], "BSR 119")])
    b.add(row_id="SRC-ROW-003", code="BSR 120", statement="При ручном заполнении поле «Адрес регистрации» автоматически формируется из ручных адресных полей.", condition="Ручные поля адреса регистрации заполнены.", action="Заполнить компоненты адреса регистрации вручную.", oracle="Поле «Адрес регистрации» автоматически содержит почтовый индекс, регион, район при наличии, населенный пункт при наличии, город, улицу, дом, корпус при наличии и квартиру при наличии.", package_id="WP-01", risk="high")

    rows = [
        ("SRC-ROW-004", "BSR 121", "Признак «Ввести вручную» для адреса регистрации всегда видим.", "Открыть блок адресов.", "Переключатель «Ввести вручную» для адреса регистрации отображается.", "WP-01", "low", []),
        ("SRC-ROW-004", "BSR 122", "Значение по умолчанию для «Ввести вручную» адреса регистрации равно «Нет».", "Открыть блок адресов.", "Переключатель «Ввести вручную» имеет значение «Нет».", "WP-01", "low", []),
        ("SRC-ROW-005", "BSR 123", "Поле «Почтовый индекс» адреса регистрации видимо, если «Ввести вручную» = «Да».", "Установить «Ввести вручную» адреса регистрации = «Да».", "Поле «Почтовый индекс» отображается.", "WP-01", "medium", []),
        ("SRC-ROW-005", "BSR 124", "Почтовый индекс адреса регистрации допускает только 6 числовых символов.", "Попытаться ввести значение, не соответствующее 6 числовым символам.", "Нарушающее формат значение не принимается; точное сообщение не утверждено.", "WP-01", "medium", gap3),
        ("SRC-ROW-006", "BSR 125", "Поле «Регион» адреса регистрации видимо в ручном режиме и использует справочник регионов.", "Установить «Ввести вручную» адреса регистрации = «Да» и открыть поле «Регион».", "Поле «Регион» отображается и использует актуальные предложения регионов DaData как external dynamic dictionary.", "WP-01", "high", gap3),
        ("SRC-ROW-007", "BSR 126", "Поле «Район» адреса регистрации видимо в ручном режиме.", "Установить «Ввести вручную» адреса регистрации = «Да».", "Поле «Район» отображается.", "WP-01", "low", []),
        ("SRC-ROW-008", "BSR 127", "Поле «Населенный пункт» адреса регистрации видимо в ручном режиме и обязательно, если поле «Город» не заполнено.", "Установить ручной режим и оставить «Город» пустым.", "Поле «Населенный пункт» отображается и требуется к заполнению; точное empty-field сообщение не утверждено.", "WP-01", "medium", gap3),
        ("SRC-ROW-009", "BSR 128", "Поле «Город» адреса регистрации видимо в ручном режиме и обязательно, если поле «Населенный пункт» не заполнено.", "Установить ручной режим и оставить «Населенный пункт» пустым.", "Поле «Город» отображается и требуется к заполнению; точное empty-field сообщение не утверждено.", "WP-01", "medium", gap3),
        ("SRC-ROW-010", "BSR 129", "Поле «Улица» адреса регистрации видимо в ручном режиме.", "Установить «Ввести вручную» адреса регистрации = «Да».", "Поле «Улица» отображается.", "WP-01", "low", []),
        ("SRC-ROW-011", "BSR 130", "Поле «Дом» адреса регистрации видимо в ручном режиме и обязательно.", "Установить ручной режим и оставить «Дом» пустым.", "Поле «Дом» отображается и требуется к заполнению; точное empty-field сообщение не утверждено.", "WP-01", "medium", gap3),
        ("SRC-ROW-012", "BSR 131", "Поле «Корпус» адреса регистрации видимо в ручном режиме.", "Установить «Ввести вручную» адреса регистрации = «Да».", "Поле «Корпус» отображается.", "WP-01", "low", []),
        ("SRC-ROW-012", "BSR 132", "Поле «Корпус» адреса регистрации допускает ввод только числовых символов.", "Попытаться ввести нечисловой символ в «Корпус».", "Нечисловой символ не принимается; точное сообщение не утверждено.", "WP-01", "medium", gap3),
        ("SRC-ROW-013", "BSR 133", "Поле «Квартира» адреса регистрации видимо в ручном режиме и обязательно, если «Клиент зарегистрирован в частном доме» = «Нет».", "Установить ручной режим и значение частного дома «Нет».", "Поле «Квартира» отображается и требуется к заполнению; точное empty-field сообщение не утверждено.", "WP-01", "medium", gap3),
        ("SRC-ROW-013", "BSR 134", "Поле «Квартира» адреса регистрации допускает ввод только числовых символов.", "Попытаться ввести нечисловой символ в «Квартира».", "Нечисловой символ не принимается; точное сообщение не утверждено.", "WP-01", "medium", gap3),
        ("SRC-ROW-014", "BSR 135", "Флажок «Клиент зарегистрирован в частном доме» отображается только если в адресе регистрации не указан номер квартиры.", "Проверить адрес регистрации без номера квартиры, затем указать номер квартиры.", "Без номера квартиры флажок «Клиент зарегистрирован в частном доме» отображается; при указанном номере квартиры флажок не отображается.", "WP-01", "medium", []),
        ("SRC-ROW-014", "BSR 136", "Значение по умолчанию для «Клиент зарегистрирован в частном доме» равно «Нет».", "Открыть блок адресов.", "Флажок «Клиент зарегистрирован в частном доме» имеет значение «Нет».", "WP-01", "low", []),
        ("SRC-ROW-014", "BSR 137", "Если флажок «Клиент зарегистрирован в частном доме» активирован, подсказка о квартире или частном доме исчезает с поля адреса регистрации.", "Активировать флажок «Клиент зарегистрирован в частном доме».", "Подсказка «Укажите номер квартиры или поставьте отметку о проживании в частном доме» исчезает с поля адреса регистрации.", "WP-01", "medium", []),
        ("SRC-ROW-015", "BSR 138", "Признак совпадения фактического адреса с адресом регистрации всегда видим.", "Открыть блок адресов.", "Переключатель «Адрес фактического места жительства совпадает с адресом регистрации» отображается.", "WP-02", "low", []),
        ("SRC-ROW-015", "BSR 139", "Значение по умолчанию для признака совпадения фактического адреса с адресом регистрации равно «Да».", "Открыть блок адресов.", "Переключатель совпадения адресов имеет значение «Да».", "WP-02", "low", []),
    ]
    for row_id, code, statement, action, oracle, pkg, risk, gaps in rows:
        binds = [bind(clar["CLR-001"], code), bind(clar["CLR-ADDR-004"], code)] if code in {"BSR 125"} else [bind(clar["CLR-ADDR-002"], code)] if code == "BSR 135" else []
        b.add(row_id=row_id, code=code, statement=statement, condition="Открыт блок «Адреса клиента».", action=action, oracle=oracle, package_id=pkg, risk=risk, constraint_gaps=gaps, clarification_bindings=binds, dictionary_refs=("DICT-DADATA-REGION" if code in {"BSR 125"} else "none_required"), dictionary_coverage=("reference-only" if code in {"BSR 125"} else "none_required"))

    b.add(row_id="SRC-ROW-016", code="BSR 140", statement="Поле «Адрес фактического места жительства» видимо, если признак совпадения с адресом регистрации = «Нет».", condition="Признак совпадения фактического адреса с адресом регистрации имеет значение «Нет».", action="Установить признак совпадения адресов = «Нет».", oracle="Поле «Адрес фактического места жительства» отображается.", package_id="WP-02", risk="medium")
    b.add(row_id="SRC-ROW-016", code="BSR 141", statement="Поле «Адрес фактического места жительства» использует интеграцию с DaData.", condition="Признак совпадения адресов = «Нет», ручной режим фактического адреса = «Нет».", action="Ввести часть адреса в поле фактического адреса.", oracle="Поле использует подсказки DaData; точные trigger/debounce/count/order не утверждаются.", package_id="WP-02", risk="high", clarification_bindings=[bind(clar["CLR-001"], "BSR 141")], dictionary_refs="DICT-DADATA-ADDRESS-SUGGESTIONS", dictionary_coverage="reference-only")
    b.add(row_id="SRC-ROW-016", code="BSR 142", statement="Для фактического адреса должны быть введены регион и номер дома.", condition="Заполняется фактический адрес.", action="Оставить регион или дом незаполненным и инициировать проверку адреса.", oracle="Система не принимает фактический адрес без региона и номера дома; точный UI oracle по пустым полям не утвержден.", package_id="WP-02", risk="high", constraint_gaps=gap3)
    b.add(row_id="SRC-ROW-016", code="BSR 142", statement="Если в фактическом адресе не указана квартира и не отмечен частный дом, поле подсвечивается красным и отображается подсказка о квартире или частном доме.", condition="Фактический адрес заполнен без квартиры, признак частного дома не активирован.", action="Инициировать проверку фактического адреса.", oracle="Поле подсвечивается красным и отображается подсказка «Укажите номер квартиры или поставьте отметку о проживании в частном доме».", package_id="WP-02", risk="high")
    b.add(row_id="SRC-ROW-016", code="BSR 143", statement="Если DaData не находит фактический адрес, отображается подсказка «Некорректно указан адрес».", condition="В поле фактического адреса введен адрес, который DaData не находит.", action="Инициировать поиск фактического адреса через DaData.", oracle="Отображается подсказка «Некорректно указан адрес».", package_id="WP-02", risk="high", clarification_bindings=[bind(clar["CLR-001"], "BSR 143"), bind(clar["CLR-ADDR-001"], "BSR 143")])
    b.add(row_id="SRC-ROW-016", code="BSR 144", statement="Если фактический адрес найден в DaData, он раскладывается по полям блока ручного ввода.", condition="DaData нашла фактический адрес.", action="Выбрать найденный фактический адрес.", oracle="Выбранный фактический адрес раскладывается по полям блока ручного ввода.", package_id="WP-02", risk="high", clarification_bindings=[bind(clar["CLR-001"], "BSR 144"), bind(clar["CLR-ADDR-001"], "BSR 144")])
    b.add(row_id="SRC-ROW-016", code="BSR 145", statement="При ручном заполнении поле фактического адреса автоматически формируется из ручных адресных полей.", condition="Ручные поля фактического адреса заполнены.", action="Заполнить компоненты фактического адреса вручную.", oracle="Поле фактического адреса автоматически содержит почтовый индекс, регион, район при наличии, населенный пункт при наличии, город, улицу, дом, корпус при наличии и квартиру при наличии.", package_id="WP-02", risk="high")

    more = [
        ("SRC-ROW-017", "BSR 146", "Флажок «Клиент проживает в частном доме» видим, если адреса не совпадают и в фактическом адресе не указана квартира.", "Установить совпадение адресов = «Нет» и заполнить фактический адрес без квартиры.", "Флажок «Клиент проживает в частном доме» отображается.", "WP-02", "medium", []),
        ("SRC-ROW-017", "BSR 147", "Значение по умолчанию для «Клиент проживает в частном доме» равно «Нет».", "Открыть блок адресов при несовпадающих адресах.", "Флажок «Клиент проживает в частном доме» имеет значение «Нет».", "WP-02", "low", []),
        ("SRC-ROW-018", "BSR 148", "Признак «Ввести вручную» для фактического адреса видим, если адреса не совпадают.", "Установить совпадение адресов = «Нет».", "Переключатель «Ввести вручную» для фактического адреса отображается.", "WP-02", "low", []),
        ("SRC-ROW-018", "BSR 149", "Значение по умолчанию для «Ввести вручную» фактического адреса равно «Нет».", "Установить совпадение адресов = «Нет».", "Переключатель «Ввести вручную» фактического адреса имеет значение «Нет».", "WP-02", "low", []),
        ("SRC-ROW-019", "BSR 150", "Поле «Регион» фактического адреса видимо в ручном режиме и использует справочник регионов.", "Установить ручной режим фактического адреса = «Да» и открыть поле «Регион».", "Поле «Регион» отображается и использует актуальные предложения регионов DaData как external dynamic dictionary.", "WP-02", "high", gap3),
        ("SRC-ROW-020", "BSR 151", "Поле «Район» фактического адреса видимо в ручном режиме.", "Установить ручной режим фактического адреса = «Да».", "Поле «Район» отображается.", "WP-02", "low", []),
        ("SRC-ROW-021", "BSR 152", "Поле «Населенный пункт» фактического адреса видимо в ручном режиме.", "Установить ручной режим фактического адреса = «Да».", "Поле «Населенный пункт» отображается.", "WP-02", "low", []),
        ("SRC-ROW-022", "BSR 153", "Поле «Город» фактического адреса видимо в ручном режиме и обязательно.", "Установить ручной режим фактического адреса = «Да» и оставить «Город» пустым.", "Поле «Город» отображается и требуется к заполнению; точное empty-field сообщение не утверждено.", "WP-02", "medium", gap3),
        ("SRC-ROW-023", "BSR 154", "Поле «Улица» фактического адреса видимо в ручном режиме и обязательно.", "Установить ручной режим фактического адреса = «Да» и оставить «Улица» пустой.", "Поле «Улица» отображается и требуется к заполнению; точное empty-field сообщение не утверждено.", "WP-02", "medium", gap3),
        ("SRC-ROW-024", "BSR 155", "Поле «Дом» фактического адреса видимо в ручном режиме и обязательно.", "Установить ручной режим фактического адреса = «Да» и оставить «Дом» пустым.", "Поле «Дом» отображается и требуется к заполнению; точное empty-field сообщение не утверждено.", "WP-02", "medium", gap3),
        ("SRC-ROW-025", "BSR 156", "Поле «Корпус» фактического адреса видимо в ручном режиме.", "Установить ручной режим фактического адреса = «Да».", "Поле «Корпус» отображается.", "WP-02", "low", []),
        ("SRC-ROW-026", "BSR 157", "Поле «Квартира» фактического адреса обязательно, если «Клиент проживает в частном доме» = «Нет».", "Установить «Клиент проживает в частном доме» = «Нет» и оставить «Квартира» пустой.", "Поле «Квартира» требуется к заполнению; точное empty-field сообщение не утверждено.", "WP-02", "medium", gap3),
        ("SRC-ROW-026", "BSR 158", "Поле «Квартира» фактического адреса видимо в ручном режиме.", "Установить ручной режим фактического адреса = «Да».", "Поле «Квартира» отображается.", "WP-02", "low", []),
        ("SRC-ROW-026", "BSR 159", "Поле «Квартира» фактического адреса допускает ввод только числовых символов.", "Попытаться ввести нечисловой символ в «Квартира» фактического адреса.", "Нечисловой символ не принимается; точное сообщение не утверждено.", "WP-02", "medium", gap3),
        ("SRC-ROW-027", "BSR 160", "Поле «Почтовый индекс» фактического адреса видимо в ручном режиме.", "Установить ручной режим фактического адреса = «Да».", "Поле «Почтовый индекс» отображается.", "WP-02", "low", []),
        ("SRC-ROW-027", "BSR 161", "Почтовый индекс фактического адреса отклоняет нечисловые символы.", "Попытаться ввести нечисловой символ в «Почтовый индекс» фактического адреса.", "Нечисловой символ не принимается; точное сообщение не утверждено.", "WP-02", "medium", gap3),
        ("SRC-ROW-027", "BSR 161", "Почтовый индекс фактического адреса отклоняет значение короче 6 числовых символов.", "Попытаться ввести 5 числовых символов в «Почтовый индекс» фактического адреса.", "Значение короче 6 числовых символов не принимается; точное сообщение не утверждено.", "WP-02", "medium", gap3),
        ("SRC-ROW-027", "BSR 161", "Почтовый индекс фактического адреса отклоняет значение длиннее 6 числовых символов.", "Попытаться ввести 7 числовых символов в «Почтовый индекс» фактического адреса.", "Значение длиннее 6 числовых символов не принимается; точное сообщение не утверждено.", "WP-02", "medium", gap3),
    ]
    for row_id, code, statement, action, oracle, pkg, risk, gaps in more:
        binds = [bind(clar["CLR-001"], code), bind(clar["CLR-ADDR-004"], code)] if code == "BSR 150" else []
        b.add(row_id=row_id, code=code, statement=statement, condition="Открыт блок «Адреса клиента».", action=action, oracle=oracle, package_id=pkg, risk=risk, constraint_gaps=gaps, clarification_bindings=binds, dictionary_refs=("DICT-DADATA-REGION" if code == "BSR 150" else "none_required"), dictionary_coverage=("reference-only" if code == "BSR 150" else "none_required"))

    b.add(row_id="SRC-ROW-028", code="BSR 324", statement="Если адрес клиента заполнен посредством запроса DaData, он раскладывается по полям блока ручного ввода.", condition="Адрес регистрации или фактического места жительства выбран из подсказки DaData.", action="Выбрать адрес клиента из подсказки DaData.", oracle="Выбранный адрес раскладывается по ручным адресным полям.", package_id="WP-03", risk="high", clarification_bindings=[bind(clar["CLR-001"], "BSR 324"), bind(clar["CLR-002"], "BSR 324"), bind(clar["CLR-ADDR-005"], "BSR 324")])
    b.add_na(row_id="SRC-ROW-028", fragment=b.fragments["SRC-ROW-028"]["BSR 324"], statement="Внутреннее заполнение модели данных `kladr` исключено из исполнимого UI scope AutoFin и проверяется отдельно.")

    def revise_visibility(row_id: str, code: str, statement: str, condition: str, action: str, oracle: str) -> None:
        assertion = next(
            item
            for item in b.assertions
            if item["source_row_id"] == row_id and item["requirement_codes"] == [code]
        )
        assertion["canonical_statement"] = statement
        assertion["condition_clauses"] = [condition]
        assertion["action_clauses"] = [action]
        assertion["oracle_clauses"] = [oracle]
        assertion["risk"] = "low"
        atom_id = assertion["atom_id"]
        for row in b.ledger_rows:
            if row["atom_id"] == atom_id:
                row["atomic_statement"] = statement
                row["constraint_gap_ids"] = "none_required"
        for row in b.obligation_rows:
            if row["linked_atom_id"] == atom_id:
                row["required_behavior"] = statement
                row["review_notes"] = "source-first assertion chain; BSR code owns visibility only"
        for row in b.plan_rows:
            if row["linked_atoms"] == atom_id:
                row["planned_check"] = action
                row["single_expected_behavior"] = oracle

    visibility_repairs = [
        ("SRC-ROW-008", "BSR 127", "Поле «Населенный пункт» адреса регистрации видимо в ручном режиме.", "Включен ручной режим адреса регистрации.", "Установить «Ввести вручную» адреса регистрации = «Да».", "Поле «Населенный пункт» отображается."),
        ("SRC-ROW-009", "BSR 128", "Поле «Город» адреса регистрации видимо в ручном режиме.", "Включен ручной режим адреса регистрации.", "Установить «Ввести вручную» адреса регистрации = «Да».", "Поле «Город» отображается."),
        ("SRC-ROW-011", "BSR 130", "Поле «Дом» адреса регистрации видимо в ручном режиме.", "Включен ручной режим адреса регистрации.", "Установить «Ввести вручную» адреса регистрации = «Да».", "Поле «Дом» отображается."),
        ("SRC-ROW-013", "BSR 133", "Поле «Квартира» адреса регистрации видимо в ручном режиме.", "Включен ручной режим адреса регистрации.", "Установить «Ввести вручную» адреса регистрации = «Да».", "Поле «Квартира» отображается."),
        ("SRC-ROW-022", "BSR 153", "Поле «Город» фактического адреса видимо в ручном режиме.", "Включен ручной режим фактического адреса.", "Установить ручной режим фактического адреса = «Да».", "Поле «Город» отображается."),
        ("SRC-ROW-023", "BSR 154", "Поле «Улица» фактического адреса видимо в ручном режиме.", "Включен ручной режим фактического адреса.", "Установить ручной режим фактического адреса = «Да».", "Поле «Улица» отображается."),
        ("SRC-ROW-024", "BSR 155", "Поле «Дом» фактического адреса видимо в ручном режиме.", "Включен ручной режим фактического адреса.", "Установить ручной режим фактического адреса = «Да».", "Поле «Дом» отображается."),
    ]
    for repair in visibility_repairs:
        revise_visibility(*repair)

    b.add_row(row_id="SRC-ROW-008", statement="Поле «Населенный пункт» адреса регистрации обязательно, если поле «Город» не заполнено.", condition="Включен ручной режим адреса регистрации, поле «Город» не заполнено.", action="Оставить поле «Населенный пункт» пустым.", oracle="Поле «Населенный пункт» требуется к заполнению; точное empty-field сообщение не утверждено.", package_id="WP-01", risk="medium", constraint_gaps=gap3)
    b.add_row(row_id="SRC-ROW-009", statement="Поле «Город» адреса регистрации обязательно, если поле «Населенный пункт» не заполнено.", condition="Включен ручной режим адреса регистрации, поле «Населенный пункт» не заполнено.", action="Оставить поле «Город» пустым.", oracle="Поле «Город» требуется к заполнению; точное empty-field сообщение не утверждено.", package_id="WP-01", risk="medium", constraint_gaps=gap3)
    b.add_row(row_id="SRC-ROW-011", statement="Поле «Дом» адреса регистрации обязательно.", condition="Включен ручной режим адреса регистрации.", action="Оставить поле «Дом» пустым.", oracle="Поле «Дом» требуется к заполнению; точное empty-field сообщение не утверждено.", package_id="WP-01", risk="medium", constraint_gaps=gap3)
    b.add_row(row_id="SRC-ROW-013", statement="Поле «Квартира» адреса регистрации обязательно, если «Клиент зарегистрирован в частном доме» = «Нет».", condition="Включен ручной режим адреса регистрации, «Клиент зарегистрирован в частном доме» = «Нет».", action="Оставить поле «Квартира» пустым.", oracle="Поле «Квартира» требуется к заполнению; точное empty-field сообщение не утверждено.", package_id="WP-01", risk="medium", constraint_gaps=gap3)
    b.add_row(row_id="SRC-ROW-022", statement="Поле «Город» фактического адреса обязательно.", condition="Включен ручной режим фактического адреса.", action="Оставить поле «Город» пустым.", oracle="Поле «Город» требуется к заполнению; точное empty-field сообщение не утверждено.", package_id="WP-02", risk="medium", constraint_gaps=gap3)
    b.add_row(row_id="SRC-ROW-023", statement="Поле «Улица» фактического адреса обязательно.", condition="Включен ручной режим фактического адреса.", action="Оставить поле «Улица» пустым.", oracle="Поле «Улица» требуется к заполнению; точное empty-field сообщение не утверждено.", package_id="WP-02", risk="medium", constraint_gaps=gap3)
    b.add_row(row_id="SRC-ROW-024", statement="Поле «Дом» фактического адреса обязательно.", condition="Включен ручной режим фактического адреса.", action="Оставить поле «Дом» пустым.", oracle="Поле «Дом» требуется к заполнению; точное empty-field сообщение не утверждено.", package_id="WP-02", risk="medium", constraint_gaps=gap3)

    clr002_codes = set(clar["CLR-002"]["requirement_codes"])
    for assertion in b.assertions:
        if assertion["semantic_disposition"] != "testable":
            continue
        codes = assertion["requirement_codes"]
        if len(codes) != 1 or codes[0] not in clr002_codes:
            continue
        bindings = assertion["clarification_clause_bindings"]
        if not any(item["clarification_id"] == "CLR-002" for item in bindings):
            bindings.append(bind(clar["CLR-002"], codes[0]))

    assertion_by_atom = {assertion["atom_id"]: assertion for assertion in b.assertions}
    gap3_atoms = [
        row["atom_id"]
        for row in b.ledger_rows
        if "GAP-003" in str(row["constraint_gap_ids"])
    ]
    gap3_assertions = [assertion_by_atom[atom_id]["assertion_id"] for atom_id in gap3_atoms]
    gap_addr_005_atoms = [
        assertion["atom_id"]
        for assertion in b.assertions
        if assertion["source_row_id"] == "SRC-ROW-028"
        and assertion["semantic_disposition"] == "not-applicable"
    ]
    gap_addr_005_assertions = [
        assertion_by_atom[atom_id]["assertion_id"] for atom_id in gap_addr_005_atoms
    ]

    baseline = json.loads((HANDOFF / "source-row-baseline.json").read_text(encoding="utf-8"))
    manifest = {
        "version": 4,
        "scope_slug": "4-3-client-addresses",
        "source_row_extraction_spec_digest": baseline["extraction_spec_sha256"],
        "source_row_baseline_digest": canonical_json_sha256(baseline),
        "source_row_candidate_count": len(baseline["candidates"]),
        "coverage_gaps_artifact": {
            "path": "fts/AutoFin/PostFinal-v2-rc5/work/stage-handoffs/07-4.3-client-addresses/scope-coverage-gaps.md",
            "sha256": "",
        },
        "sources": [{"path": SOURCE_PATH, "sha256": sha256_file(ROOT / SOURCE_PATH)}],
        "source_rows": list(b.rows.values()),
        "assertions": b.assertions,
        "clarifications": [clar[item] for item in ("CLR-001", "CLR-002", "CLR-ADDR-001", "CLR-ADDR-002", "CLR-ADDR-004", "CLR-ADDR-005")],
        "evidence_sources": [
            {"path": "fts/AutoFin/PostFinal-v2-rc5/source/PostFinal-v2.docx", "sha256": sha256_file(FT_ROOT / "source" / "PostFinal-v2.docx"), "role": "semantic-source-of-truth"},
            {"path": "fts/AutoFin/PostFinal-v2-rc5/source/PostFinal-v2.pdf", "sha256": sha256_file(FT_ROOT / "source" / "PostFinal-v2.pdf"), "role": "structural-visual-parity"},
            {"path": "fts/AutoFin/PostFinal-v2-rc5/AGENT-NOTES.md", "sha256": sha256_file(FT_ROOT / "AGENT-NOTES.md"), "role": "supporting-material"},
            {"path": "fts/AutoFin/PostFinal-v2-rc5/work/vendor-references/dadata-reference.md", "sha256": sha256_file(FT_ROOT / "work" / "vendor-references" / "dadata-reference.md"), "role": "supporting-material"},
            {"path": "fts/AutoFin/PostFinal-v2-rc5/work/stage-handoffs/07-4.3-client-addresses/scope-clarification-requests.md", "sha256": sha256_file(HANDOFF / "scope-clarification-requests.md"), "role": "approved-clarification"},
            {"path": "fts/AutoFin/PostFinal-v2-rc5/support/client-addresses-approved-clarifications-v3.md", "sha256": sha256_file(FT_ROOT / "support" / "client-addresses-approved-clarifications-v3.md"), "role": "approved-clarification"},
        ],
        "mockups": [],
    }
    gap_path = HANDOFF / "scope-coverage-gaps.md"
    gap_path.write_text(
        build_coverage_gaps(
            gap3_assertions,
            gap3_atoms,
            gap_addr_005_assertions,
            gap_addr_005_atoms,
        ),
        encoding="utf-8",
        newline="\n",
    )
    manifest["coverage_gaps_artifact"]["sha256"] = sha256_file(gap_path)
    (HANDOFF / "source-assertions.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    source_selection = f"""# Scope-Local Source Selection

## Context

- selected_ft_slug: `AutoFin/PostFinal-v2-rc5`
- selected_input_root: `fts/AutoFin/PostFinal-v2-rc5`
- scope_slug: `4-3-client-addresses`
- xhtml_available: `yes`
- xhtml_path: `source/PostFinal-v2.xhtml`
- xhtml_matches_main_ft: `yes`
- source_selection_basis: `work/stage-handoffs/00-source-selection/source-selection.md`

## Scope-Local Manifest Binding Registry

| path | role | sha256 | manifest_binding | scope_usage |
| --- | --- | --- | --- | --- |
| `source/PostFinal-v2.docx` | `main-ft-docx` | `{sha256_file(FT_ROOT / "source" / "PostFinal-v2.docx")}` | `semantic-source-of-truth` | `4-3-client-addresses` |
| `source/PostFinal-v2.xhtml` | `main-ft-xhtml` | `{sha256_file(FT_ROOT / "source" / "PostFinal-v2.xhtml")}` | `assertion-source` | `4-3-client-addresses` |
| `source/PostFinal-v2.pdf` | `main-ft-pdf` | `{sha256_file(FT_ROOT / "source" / "PostFinal-v2.pdf")}` | `structural-visual-parity` | `4-3-client-addresses` |
| `AGENT-NOTES.md` | `mandatory-package-context` | `{sha256_file(FT_ROOT / "AGENT-NOTES.md")}` | `supporting-material` | `4-3-client-addresses` |
| `work/vendor-references/dadata-reference.md` | `external-vendor-reference` | `{sha256_file(FT_ROOT / "work" / "vendor-references" / "dadata-reference.md")}` | `supporting-material` | `4-3-client-addresses` |
| `work/stage-handoffs/07-4.3-client-addresses/scope-clarification-requests.md` | `approved-clarification` | `{sha256_file(HANDOFF / "scope-clarification-requests.md")}` | `approved-clarification` | `4-3-client-addresses` |
| `support/client-addresses-approved-clarifications-v3.md` | `approved-clarification` | `{sha256_file(FT_ROOT / "support" / "client-addresses-approved-clarifications-v3.md")}` | `approved-clarification` | `4-3-client-addresses` |

## Omitted Shared Registry Rows

- Support files and mockups from unrelated scopes are not used as semantic evidence for this scope.
- Older address clarification files are superseded by `support/client-addresses-approved-clarifications-v3.md`.
"""
    (HANDOFF / "source-selection.scope-local.md").write_text(source_selection, encoding="utf-8", newline="\n")

    boundary_fragment = "Ограничения по типам данных"
    boundary_extract = {
        "version": 1,
        "source_path": SOURCE_PATH,
        "source_sha256": sha256_file(ROOT / SOURCE_PATH),
        "extraction_method": "utf8-literal-fragments-v1",
        "fragments": [
            {
                "source_locator": "xhtml-literal:section-5-document-global-constraints",
                "exact_source_text": boundary_fragment,
                "exact_source_text_sha256": sha256_text(boundary_fragment),
            }
        ],
    }
    (HANDOFF / "bounded-boundary-exclusions.xhtml.json").write_text(
        json.dumps(boundary_extract, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    docx_fragment = "Адреса клиента"
    docx_extract = {
        "version": 1,
        "source_path": "fts/AutoFin/PostFinal-v2-rc5/source/PostFinal-v2.docx",
        "source_sha256": sha256_file(FT_ROOT / "source" / "PostFinal-v2.docx"),
        "extraction_method": "docx-xml-literal-fragments-v1",
        "fragments": [
            {
                "source_locator": "docx-text:address-scope-heading",
                "exact_source_text": docx_fragment,
                "exact_source_text_sha256": sha256_text(docx_fragment),
            }
        ],
    }
    (HANDOFF / "bounded-main-docx.json").write_text(
        json.dumps(docx_extract, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    pdf_fragment = "Адреса клиента"
    pdf_extract = {
        "version": 1,
        "source_path": "fts/AutoFin/PostFinal-v2-rc5/source/PostFinal-v2.pdf",
        "source_sha256": sha256_file(FT_ROOT / "source" / "PostFinal-v2.pdf"),
        "extraction_method": "pdf-page-literal-fragments-v1",
        "fragments": [
            {
                "source_locator": "page:20",
                "exact_source_text": pdf_fragment,
                "exact_source_text_sha256": sha256_text(pdf_fragment),
            }
        ],
    }
    (HANDOFF / "bounded-main-pdf.json").write_text(
        json.dumps(pdf_extract, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    ledger = ["# Atomic Requirements Ledger", "", "| atom_id | source_property_id | atomic_statement | coverage_status | source_row_id | requirement_codes | constraint_gap_ids |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for row in b.ledger_rows:
        ledger.append("| " + " | ".join(esc(row[key]) for key in ["atom_id", "source_property_id", "atomic_statement", "coverage_status", "source_row_id", "requirement_codes", "constraint_gap_ids"]) + " |")
    (HANDOFF / "atomic-requirements-ledger.md").write_text("\n".join(ledger) + "\n", encoding="utf-8", newline="\n")

    obligations = ["# Coverage Obligation Table", "", "| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | planned_tc_or_gap | status | review_notes | source_row_id | requirement_codes | dictionary_refs | dictionary_coverage |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in b.obligation_rows:
        obligations.append("| " + " | ".join(esc(row[key]) for key in ["obligation_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "obligation_class", "required_behavior", "source_ref", "planned_tc_or_gap", "status", "review_notes", "source_row_id", "requirement_codes", "dictionary_refs", "dictionary_coverage"]) + " |")
    (HANDOFF / "coverage-obligation-table.md").write_text("\n".join(obligations) + "\n", encoding="utf-8", newline="\n")

    plan = ["# Package Test Design Plan", "", "| planned_tc_id | planned_tc_or_gap | linked_atoms | planned_check | single_expected_behavior | test_data | input_class | status | source_ref |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in b.plan_rows:
        plan.append("| " + " | ".join(esc(row[key]) for key in ["planned_tc_id", "planned_tc_or_gap", "linked_atoms", "planned_check", "single_expected_behavior", "test_data", "input_class", "status", "source_ref"]) + " |")
    (HANDOFF / "package-test-design-plan.md").write_text("\n".join(plan) + "\n", encoding="utf-8", newline="\n")

    matrix = """# Test Design Applicability Matrix

| dimension | applicable | rationale | source_ref |
| --- | --- | --- | --- |
| field-property | yes | Address fields have visibility, default, editability, requiredness and format obligations. | `BSR 115-161; BSR 324` |
| requiredness | yes | Requiredness is source-backed; exact message text is only asserted where FT gives it. | `SRC-ROW-003; SRC-ROW-008; SRC-ROW-009; SRC-ROW-011; SRC-ROW-013; SRC-ROW-022; SRC-ROW-023; SRC-ROW-024` |
| dictionary | yes | Region fields use DaData as external dynamic dictionary per approved clarification. | `DICT-DADATA-ADDRESS-SUGGESTIONS; DICT-DADATA-REGION; CLR-001; CLR-ADDR-004` |
| integration | yes | DaData use is source-backed, but vendor trigger/debounce/fallback/order are excluded. | `BSR 116; BSR 118; BSR 119; BSR 141; BSR 143; BSR 144; BSR 324; work/vendor-references/dadata-reference.md` |
| persistence/internal-model | no | Internal `kladr` fill is excluded by approved clarification and not converted into UI TC. | `CLR-ADDR-005; ASSERT-ADDR-062` |
"""
    (HANDOFF / "test-design-applicability-matrix.md").write_text(matrix, encoding="utf-8", newline="\n")

    prompt = f"""# Source Assertion Review Request

- `scope_slug`: `4-3-client-addresses`
- `manifest`: `work/stage-handoffs/07-4.3-client-addresses/source-assertions.json`
- `manifest_digest`: `{canonical_json_sha256(manifest)}`
- `source_row_inventory`: `work/stage-handoffs/07-4.3-client-addresses/source-row-inventory.md`
- `source_row_extraction_spec`: `work/stage-handoffs/07-4.3-client-addresses/source-row-extraction-spec.json`
- `source_row_baseline`: `work/stage-handoffs/07-4.3-client-addresses/source-row-baseline.json`
- `coverage_gaps`: `work/stage-handoffs/07-4.3-client-addresses/scope-coverage-gaps.md`
- `source_selection`: `work/stage-handoffs/07-4.3-client-addresses/source-selection.scope-local.md`
- `package_notes`: `AGENT-NOTES.md`

Review the source-first manifest against the current rc5 handoff only. Verify source-row coverage, ASSERT->ATOM->OBL lineage, requirement-code provenance, approved clarification provenance, non-blocking GAP-003 calibration handling, and BSR 324 internal `kladr` exclusion. Do not write or review test cases.
"""
    (HANDOFF / "prompt.scope-assertions-to-reviewer.md").write_text(prompt, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
