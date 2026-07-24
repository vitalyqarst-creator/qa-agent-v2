from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from test_case_agent.coverage_graph import CoverageGraph
from test_case_agent.review_cycle.production_tc_gate import (
    ACTION_STEP_RE,
    RUSSIAN_INFINITIVE_STEP_RE,
    production_precondition_problem,
    validate_production_tc_content,
)
from test_case_agent.test_design import (
    DesignContext,
    DesignError,
    TestCaseDesign,
    TestDesignPlan,
    WriterCard,
    runtime_preconditions_for_binding,
    validate_design_context_for_graph,
)


class IterationContractError(ValueError):
    """Writer/reviewer output violates the runner-owned iteration contract."""


_DECISIONS = {"accepted", "changes-required", "blocked"}
_RESULT_STATUSES = {
    "calibration-pending",
    "covered",
    "not-covered",
    "incorrect",
}
REVIEWER_FALSIFICATION_PROBES = (
    "false_pass",
    "false_fail",
    "failure_attribution",
    "trigger_fidelity",
)
_FALSIFICATION_OUTCOMES = {"passed", "finding", "not-recorded"}
_SOURCE_PROJECTION_FINDING_TYPES = {
    "dictionary-incomplete",
    "ft-mockup-contradiction",
    "literal-condition-lost",
    "projection-incorrect",
    "sibling-assertion-lost",
    "source-element-omitted",
    "source-row-decomposition-incorrect",
    "traceability-chain-incomplete",
}
_TEST_CASE_FINDING_TYPES = {
    "calibration-status-incorrect",
    "cleanup-missing",
    "commit-action-missing",
    "editability-incorrect",
    "execution-status-incorrect",
    "expected-result-unsupported",
    "negative-branch-missing",
    "positive-branch-missing",
    "repeater-lifecycle-incomplete",
    "requiredness-incorrect",
    "test-case-defect",
    "test-data-nonconcrete",
    "traceability-incorrect",
    "trigger-missing",
}
_DESIGN_SUPPORT_ROLE_FIELDS = {
    "setup": "preconditions",
    "action": "steps",
    "cleanup": "postconditions",
}
_DESIGN_SUPPORT_MAPPING_FIELDS = {
    "support_role",
    "test_case_field",
    "item_index",
    "materialized_text",
    "materialized_text_sha256",
    "source_action_fragment",
    "source_row_id",
    "assertion_id",
    "property_id",
    "obligation_id",
    "case_key",
    "tc_id",
}
_INTERNAL_RUNTIME_TOKEN_RE = re.compile(
    r"(?:\bsubject:[0-9a-f][0-9a-f_-]{7,}\b|"
    r"\b(?:OBL|ATOM|ASSERT|SRC)(?:-[A-Z0-9]+)+\b|"
    r"\bBSR\s+\d+\b)",
    re.IGNORECASE,
)
_RUNTIME_NO_SETUP_RE = re.compile(r"^не\s+требуются$", re.IGNORECASE)

REVIEWER_POLICY_VERSION_V2 = 2

REVIEWER_PROMPT_INSTRUCTION = (
    "Return JSON only. Independently check every projected source obligation "
    "against its bound test case. Review only projected conditions, actions, "
    "fixtures, and states; do not demand hypothetical or unprojected state axes. "
    "If the projection explicitly contains before/after states, missing coverage "
    "is a finding. Executable cases require status covered. "
    "candidate-ui-calibration cases require status calibration-pending and must "
    "be checked for honest pending classification, traceability, a concrete "
    "calibration question, and no invented oracle; non-executability alone is not "
    "a finding. Accepted requires every case's required status and zero findings, "
    "including warnings."
)

REVIEWER_PROMPT_INSTRUCTION_V2 = (
    "Return JSON only. Review the complete ReviewerEvidencePack in one pass. "
    "Literal bounded source evidence has priority over normalized properties, "
    "obligations, mockups, and test-case projections. Check every in-scope source "
    "row, including rows with no generated obligation, for lost words, sibling "
    "assertions, decomposition errors, dictionary omissions, and FT/mockup "
    "contradictions. Then check every test case for positive and negative coverage, "
    "concrete data, supported expected results, requiredness/editability, triggers, "
    "commit and cleanup actions, repeater lifecycle, traceability, and honest "
    "executable/calibration status. Exclusive allowed-set wording such as 'only' "
    "requires a representative disallowed equivalence class; an exact numeric "
    "length requires both length boundaries and a nonnumeric class. Unknown UI "
    "reactions may remain honest calibration candidates, but the negative class "
    "must not disappear. Repeater lifecycle expectations remain source-bound: do "
    "not invent post-delete or re-add defaults absent from literal source or an "
    "accepted clarification. Treat the complete registered coverage-gap artifact "
    "and every supporting cross-row evidence edge as binding review evidence; "
    "enforce each gap's temporary handling and do-not-test rule. Keep each case's "
    "primary coverage chain atomic, and review every role-tagged design-support "
    "chain where a sibling obligation is materialized in setup, action, or cleanup. "
    "For every behavioral case, try to construct a defective implementation under "
    "source-consistent inputs and preconditions that violates the bound rule but "
    "still passes the TC, a behavior conforming to all supplied evidence that would "
    "fail only because of an unsupported expectation, a failure caused by an invalid "
    "fixture or unrelated precondition, and a case whose steps miss the exact "
    "source-backed trigger. Record all four probes in case_results.falsification "
    "with the exact binding_role, obligation_id, binding_item_index (-1 for primary), "
    "reviewed trigger_or_step, oracle, and a specific detail. For outcome=passed, "
    "bind trigger_or_step to an actual "
    "TC step for primary/action, the exact bound TC field item for setup/cleanup "
    "(failure_attribution may instead bind a TC precondition or test-data item), "
    "and oracle to the TC expected_result. A source-only validation trigger "
    "or observable oracle may support outcome=finding, never outcome=passed. Use "
    "outcome=passed with this concrete basis, or outcome=finding with a concrete "
    "witness and one or more bound test_case_findings. A finding should name the "
    "exact falsification_probe when it is specific to one probe; if the same root "
    "defect affects multiple probes on the same case/evidence chain, one finding "
    "may name the most specific affected probe and the case_results.falsification "
    "receipt must record the remaining affected probes. The probe receipt must "
    "anchor at least one same-case bound finding; additional findings for the same "
    "probe may use other exact registered chains. outcome=not-recorded is "
    "reserved for the offline legacy adapter and is forbidden in live output. "
    "case_results must contain exactly one result for every case in "
    "reviewer_evidence_pack.normalized_projection.cases, including cases with "
    "no findings; never return only changed or failed cases. "
    "When a finding is caused by one of these probes, bind its witness to the exact "
    "registered chain; do not manufacture a finding when no such witness exists. "
    "Direct source, TC-design, digest, and binding defects proven by supplied artifacts "
    "do not require a hypothetical witness; use an empty falsification_probe for such "
    "direct test-case findings. "
    "A test-case finding must declare binding_role=primary or the exact "
    "design-support role and use the corresponding registered chain. Report projection "
    "defects only in "
    "source_projection_findings and case defects only in test_case_findings, with "
    "the most specific registered source/assertion/obligation/case bindings. Do not "
    "rewrite requirements or invent UI behavior. Images are supporting evidence; "
    "the literal FT remains authoritative. Accepted requires every case's required "
    "status and zero errors or warnings in both finding arrays."
)


def reviewer_prompt_instruction(schema_version: int) -> str:
    if schema_version == 2:
        return REVIEWER_PROMPT_INSTRUCTION_V2
    if schema_version == 1:
        return REVIEWER_PROMPT_INSTRUCTION
    raise IterationContractError(
        f"unsupported reviewer request schema_version: {schema_version}"
    )


def reviewer_acceptance_contract(*, schema_version: int = 1) -> dict[str, Any]:
    """Return the single runner-owned acceptance policy sent to the reviewer."""

    result = {
        "all_cases_must_have_required_status": True,
        "executable_result_status": "covered",
        "calibration_candidate_result_status": "calibration-pending",
        "accepted_requires_zero_findings": True,
        "calibration_review_checks": [
            "honest-pending-classification",
            "traceability",
            "concrete-calibration-question",
            "no-invented-oracle",
        ],
        "calibration_non_executability_alone_is_not_a_finding": True,
        "review_only_projected_behavior": True,
        "no_hypothetical_state_axes": True,
        "explicit_projected_before_after_states_must_be_covered": True,
        "old_test_cases_available": False,
    }
    if schema_version == 2:
        result.update(
            {
                "reviewer_policy_version": REVIEWER_POLICY_VERSION_V2,
                "literal_source_evidence_has_priority": True,
                "all_scope_rows_must_be_reviewed": True,
                "source_projection_findings_separate": True,
                "test_case_findings_separate": True,
                "accepted_requires_zero_source_projection_findings": True,
                "accepted_requires_zero_test_case_findings": True,
                "review_only_projected_behavior": False,
                "review_literal_source_against_projection": True,
                "mockups_cannot_override_ft": True,
                "exclusive_allowed_set_requires_disallowed_class": True,
                "exact_numeric_length_requires_length_boundaries_and_nonnumeric_class": True,
                "repeater_lifecycle_expectations_are_source_bound": True,
                "registered_coverage_gaps_are_binding": True,
                "supporting_source_bindings_must_be_reviewed": True,
                "design_support_chains_must_be_reviewed": True,
                "test_case_findings_require_exact_binding_role": True,
                "primary_coverage_mapping_is_one_per_case": True,
                "adversarial_false_pass_check": True,
                "adversarial_false_fail_check": True,
                "failure_attribution_check": True,
                "trigger_fidelity_check": True,
                "probe_findings_require_concrete_witness": True,
                "probe_findings_require_same_chain_bound_finding": True,
                "related_probe_findings_may_share_same_case_root_finding": True,
                "per_probe_evidence_chain_binding_required": True,
                "per_probe_evidence_item_binding_required": True,
                "artifact_proven_findings_do_not_require_hypothetical_witness": True,
                "per_case_falsification_receipt_required": True,
                "live_falsification_receipt_allows_not_recorded": False,
                "benchmark_context_available": False,
                "review_history_available": False,
            }
        )
    elif schema_version != 1:
        raise IterationContractError(
            f"unsupported reviewer acceptance schema_version: {schema_version}"
        )
    return result


def _canonical_digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def has_complete_all_row_parity(
    literal_rows: Sequence[Any],
    source_structure: Mapping[str, Any],
) -> bool:
    selected_xhtml = source_structure.get("selected_xhtml")
    selected_xhtml_path = (
        selected_xhtml.get("relative_path")
        if isinstance(selected_xhtml, Mapping)
        else None
    )
    selected_xhtml_sha256 = (
        selected_xhtml.get("sha256")
        if isinstance(selected_xhtml, Mapping)
        else None
    )
    if (
        not isinstance(selected_xhtml_path, str)
        or not selected_xhtml_path
        or not isinstance(selected_xhtml_sha256, str)
        or len(selected_xhtml_sha256) != 64
        or any(
            character not in "0123456789abcdef"
            for character in selected_xhtml_sha256
        )
    ):
        return False

    all_source_row_ids: set[str] = set()
    literal_rows_by_id: dict[str, Mapping[str, Any]] = {}
    xhtml_source_row_ids: set[str] = set()
    candidate_bindings: set[tuple[str, str]] = set()
    candidate_ids: set[str] = set()
    auxiliary_row_ids: set[str] = set()
    ordered_xhtml_row_ids: list[str] = []
    table_rows_by_identity: dict[str, list[str]] = {}
    headings_by_id: dict[str, Mapping[str, Any]] = {}
    heading_ids_by_row: dict[str, tuple[str, ...]] = {}
    for raw in literal_rows:
        if not isinstance(raw, Mapping) or "candidate_id" not in raw:
            return False
        source_row_id = raw.get("source_row_id")
        candidate_id = raw.get("candidate_id")
        source_path = raw.get("source_path")
        if (
            not isinstance(source_row_id, str)
            or not source_row_id
            or source_row_id in all_source_row_ids
            or not isinstance(source_path, str)
            or not source_path
        ):
            return False
        all_source_row_ids.add(source_row_id)
        literal_rows_by_id[source_row_id] = raw
        if source_path != selected_xhtml_path:
            if candidate_id is not None:
                return False
            continue
        xhtml_source_row_ids.add(source_row_id)
        ordered_xhtml_row_ids.append(source_row_id)
        source_file_sha256 = raw.get("source_file_sha256")
        source_locator = raw.get("source_locator")
        bounded_source_text = raw.get("bounded_source_text")
        bounded_source_text_sha256 = raw.get("bounded_source_text_sha256")
        if (
            not isinstance(source_file_sha256, str)
            or len(source_file_sha256) != 64
            or any(character not in "0123456789abcdef" for character in source_file_sha256)
            or source_file_sha256 != selected_xhtml_sha256
            or not isinstance(source_locator, str)
            or not source_locator
            or raw.get("row_identity") != source_locator
            or not isinstance(bounded_source_text, str)
            or not bounded_source_text
            or bounded_source_text_sha256
            != hashlib.sha256(bounded_source_text.encode("utf-8")).hexdigest()
        ):
            return False
        element_kind = raw.get("element_kind")
        table_identity = raw.get("table_identity")
        table_ancestry = raw.get("table_ancestry")
        if table_identity is not None:
            if (
                not isinstance(table_identity, str)
                or not table_identity
                or not isinstance(table_ancestry, list)
                or not table_ancestry
                or not isinstance(table_ancestry[-1], Mapping)
                or table_ancestry[-1].get("element_kind") != "table"
                or table_ancestry[-1].get("canonical_xpath") != table_identity
            ):
                return False
            table_rows_by_identity.setdefault(table_identity, []).append(
                source_row_id
            )
        elif element_kind == "tr":
            return False
        raw_headings = raw.get("section_heading_evidence")
        section_path = raw.get("section_path")
        if not isinstance(raw_headings, list) or not isinstance(section_path, list):
            return False
        heading_ids: list[str] = []
        heading_texts: list[str] = []
        for heading in raw_headings:
            if not isinstance(heading, Mapping):
                return False
            heading_id = heading.get("heading_evidence_id")
            heading_text = heading.get("bounded_source_text")
            heading_xpath = heading.get("canonical_xpath")
            expected_heading_id = (
                "XHTML-HEADING-"
                + hashlib.sha256(
                    "\u001f".join(
                        (selected_xhtml_path, str(heading_xpath), str(heading_text))
                    ).encode("utf-8")
                ).hexdigest()[:24].upper()
            )
            if (
                not isinstance(heading_id, str)
                or heading_id != expected_heading_id
                or not isinstance(heading_text, str)
                or not heading_text
                or heading.get("source_path") != selected_xhtml_path
                or heading.get("source_file_sha256") != source_file_sha256
                or heading.get("bounded_source_text_sha256")
                != hashlib.sha256(heading_text.encode("utf-8")).hexdigest()
                or not isinstance(heading_xpath, str)
                or type(heading.get("level")) is not int
                or not 1 <= heading["level"] <= 6
            ):
                return False
            previous = headings_by_id.get(heading_id)
            if previous is not None and previous != heading:
                return False
            headings_by_id[heading_id] = heading
            heading_ids.append(heading_id)
            heading_texts.append(heading_text)
        if section_path != heading_texts:
            return False
        heading_ids_by_row[source_row_id] = tuple(heading_ids)
        if candidate_id is None:
            auxiliary_row_ids.add(source_row_id)
        elif (
            not isinstance(candidate_id, str)
            or not candidate_id
            or candidate_id in candidate_ids
        ):
            return False
        else:
            candidate_ids.add(candidate_id)
            candidate_bindings.add((source_row_id, candidate_id))
    if not candidate_bindings:
        return False

    parity = source_structure.get("docx_xhtml_pdf_parity")
    docx_xhtml = (
        parity.get("docx_xhtml") if isinstance(parity, Mapping) else None
    )
    if not isinstance(docx_xhtml, Mapping):
        return False
    candidate_matches = docx_xhtml.get("row_matches")
    auxiliary_matches = docx_xhtml.get("auxiliary_row_matches")
    if not isinstance(candidate_matches, list) or not isinstance(
        auxiliary_matches,
        list,
    ):
        return False
    actual_candidate_bindings: list[tuple[str, str]] = []
    docx_matches_by_row: dict[str, Mapping[str, Any]] = {}
    for raw in candidate_matches:
        if not isinstance(raw, Mapping):
            return False
        source_row_id = raw.get("source_row_id")
        candidate_id = raw.get("candidate_id")
        if not isinstance(source_row_id, str) or not isinstance(candidate_id, str):
            return False
        actual_candidate_bindings.append((source_row_id, candidate_id))
        literal = literal_rows_by_id.get(source_row_id)
        if literal is None:
            return False
        for field in (
            "source_path",
            "source_file_sha256",
            "source_locator",
            "bounded_source_text_sha256",
            "element_kind",
        ):
            if raw.get(field) != literal.get(field):
                return False
        raw_docx_matches = raw.get("docx_matches")
        if (
            not isinstance(raw_docx_matches, list)
            or len(raw_docx_matches) != 1
            or not isinstance(raw_docx_matches[0], Mapping)
        ):
            return False
        docx_matches_by_row[source_row_id] = raw_docx_matches[0]
    actual_auxiliary_ids: list[str] = []
    for raw in auxiliary_matches:
        if not isinstance(raw, Mapping) or raw.get("candidate_id") is not None:
            return False
        source_row_id = raw.get("source_row_id")
        if not isinstance(source_row_id, str) or not source_row_id:
            return False
        actual_auxiliary_ids.append(source_row_id)
        literal = literal_rows_by_id.get(source_row_id)
        if literal is None:
            return False
        for field in (
            "source_path",
            "source_file_sha256",
            "source_locator",
            "bounded_source_text_sha256",
            "element_kind",
        ):
            if raw.get(field) != literal.get(field):
                return False
        raw_docx_matches = raw.get("docx_matches")
        if (
            not isinstance(raw_docx_matches, list)
            or len(raw_docx_matches) != 1
            or not isinstance(raw_docx_matches[0], Mapping)
        ):
            return False
        docx_matches_by_row[source_row_id] = raw_docx_matches[0]

    candidate_count = len(candidate_bindings)
    total_count = len(xhtml_source_row_ids)
    if (
        parity.get("contract") != "bounded-source-parity-v1"
        or parity.get("status") != "verified"
        or docx_xhtml.get("status") != "verified"
        or type(docx_xhtml.get("literal_candidate_count")) is not int
        or docx_xhtml.get("literal_candidate_count") != candidate_count
        or type(docx_xhtml.get("matched_literal_candidate_count")) is not int
        or docx_xhtml.get("matched_literal_candidate_count") != candidate_count
        or type(docx_xhtml.get("literal_xhtml_row_count")) is not int
        or docx_xhtml.get("literal_xhtml_row_count") != total_count
        or type(docx_xhtml.get("matched_literal_xhtml_row_count")) is not int
        or docx_xhtml.get("matched_literal_xhtml_row_count") != total_count
        or type(docx_xhtml.get("unique_docx_unit_count")) is not int
        or docx_xhtml.get("unique_docx_unit_count") != total_count
        or len(actual_candidate_bindings) != candidate_count
        or set(actual_candidate_bindings) != candidate_bindings
        or len(actual_auxiliary_ids) != len(auxiliary_row_ids)
        or set(actual_auxiliary_ids) != auxiliary_row_ids
    ):
        return False

    previous_docx_order = -1
    for source_row_id in ordered_xhtml_row_ids:
        match = docx_matches_by_row.get(source_row_id)
        document_order = (
            match.get("document_order") if isinstance(match, Mapping) else None
        )
        if type(document_order) is not int or document_order <= previous_docx_order:
            return False
        previous_docx_order = document_order

    table_matches = docx_xhtml.get("table_identity_matches")
    if not isinstance(table_matches, list) or len(table_matches) != len(
        table_rows_by_identity
    ):
        return False
    actual_table_bindings: dict[str, tuple[int, tuple[str, ...]]] = {}
    used_docx_table_indexes: set[int] = set()
    for raw in table_matches:
        if not isinstance(raw, Mapping):
            return False
        identity = raw.get("xhtml_table_identity")
        docx_table_index = raw.get("docx_table_index")
        row_ids = raw.get("source_row_ids")
        if (
            not isinstance(identity, str)
            or type(docx_table_index) is not int
            or docx_table_index in used_docx_table_indexes
            or not isinstance(row_ids, list)
            or any(not isinstance(item, str) for item in row_ids)
            or identity in actual_table_bindings
        ):
            return False
        used_docx_table_indexes.add(docx_table_index)
        actual_table_bindings[identity] = (docx_table_index, tuple(row_ids))
    if set(actual_table_bindings) != set(table_rows_by_identity):
        return False
    for identity, expected_row_ids in table_rows_by_identity.items():
        table_index, actual_row_ids = actual_table_bindings[identity]
        if actual_row_ids != tuple(expected_row_ids) or any(
            docx_matches_by_row[row_id].get("table_index") != table_index
            for row_id in expected_row_ids
        ):
            return False

    section_heading_matches = docx_xhtml.get("section_heading_matches")
    if (
        type(docx_xhtml.get("section_heading_match_count")) is not int
        or docx_xhtml.get("section_heading_match_count") != len(headings_by_id)
        or not isinstance(section_heading_matches, list)
        or len(section_heading_matches) != len(headings_by_id)
    ):
        return False
    heading_docx_orders: dict[str, int] = {}
    for raw in section_heading_matches:
        if not isinstance(raw, Mapping):
            return False
        heading_id = raw.get("heading_evidence_id")
        docx_match = raw.get("docx_match")
        expected_heading = headings_by_id.get(str(heading_id))
        if (
            expected_heading is None
            or any(raw.get(key) != value for key, value in expected_heading.items())
            or not isinstance(docx_match, Mapping)
            or docx_match.get("unit_kind") != "paragraph"
            or type(docx_match.get("document_order")) is not int
            or heading_id in heading_docx_orders
        ):
            return False
        heading_docx_orders[str(heading_id)] = docx_match["document_order"]
    for row_id, heading_ids in heading_ids_by_row.items():
        row_order = docx_matches_by_row[row_id]["document_order"]
        orders = [heading_docx_orders[heading_id] for heading_id in heading_ids]
        if orders != sorted(orders) or len(orders) != len(set(orders)):
            return False
        if orders and orders[-1] >= row_order:
            return False

    pdf_parity = parity.get("pdf_requirement_codes")
    scope_definition = source_structure.get("scope_definition")
    source_set = (
        scope_definition.get("source_set")
        if isinstance(scope_definition, Mapping)
        else None
    )
    if not isinstance(pdf_parity, Mapping) or not isinstance(source_set, Mapping):
        return False
    semantic_rows = pdf_parity.get("semantic_literal_rows")
    if not isinstance(semantic_rows, Mapping):
        return False
    pdf_registered = source_set.get("pdf") is not None
    if not pdf_registered:
        return (
            pdf_parity.get("status") == "not-registered"
            and semantic_rows.get("status") == "not-registered"
            and type(semantic_rows.get("literal_xhtml_row_count")) is int
            and semantic_rows.get("literal_xhtml_row_count") == total_count
        )

    pdf_matches = semantic_rows.get("row_matches")
    if not isinstance(pdf_matches, list):
        return False
    pdf_row_ids: list[str] = []
    for raw in pdf_matches:
        source_row_id = raw.get("source_row_id") if isinstance(raw, Mapping) else None
        if not isinstance(source_row_id, str) or not source_row_id:
            return False
        pdf_row_ids.append(source_row_id)
    return (
        pdf_parity.get("status") == "verified"
        and semantic_rows.get("status") == "verified"
        and type(semantic_rows.get("literal_xhtml_row_count")) is int
        and semantic_rows.get("literal_xhtml_row_count") == total_count
        and type(semantic_rows.get("matched_literal_xhtml_row_count")) is int
        and semantic_rows.get("matched_literal_xhtml_row_count") == total_count
        and len(pdf_row_ids) == total_count
        and set(pdf_row_ids) == xhtml_source_row_ids
    )


def _object(value: Any, path: str, keys: set[str]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise IterationContractError(f"{path} must be an object")
    if set(value) != keys:
        raise IterationContractError(
            f"{path} fields differ; missing={sorted(keys - set(value))}, "
            f"unknown={sorted(set(value) - keys)}"
        )
    return value


def _one_line(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\n" in value or "\r" in value:
        raise IterationContractError(f"{path} must be non-empty single-line text")
    return value.strip()


def _strings(value: Any, path: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise IterationContractError(f"{path} must be a non-empty string array")
    return tuple(_one_line(item, f"{path}[{index}]") for index, item in enumerate(value))


def _case_traceability(graph: CoverageGraph, card: WriterCard) -> tuple[str, ...]:
    prop = next(item for item in graph.properties if item.property_id == card.property_id)
    values = [
        card.obligation_id,
        card.atom_id,
        prop.assertion_id,
        *card.requirement_codes,
    ]
    if card.source_oracle_id:
        values.append(card.source_oracle_id)
    return tuple(dict.fromkeys(item for item in values if item))


def build_writer_request(
    graph: CoverageGraph,
    plan: TestDesignPlan,
) -> dict[str, Any]:
    if plan.graph_digest != graph.digest:
        raise IterationContractError("design plan is not bound to this coverage graph")
    if plan.blocked_cards:
        raise IterationContractError("blocked cards must be resolved before writer")
    return {
        "schema_version": 1,
        "graph_digest": graph.digest,
        "cards": [item.to_dict() for item in plan.writer_cards],
        "constraints": {
            "one_case_per_card": True,
            "runner_owned_fields": [
                "tc_id",
                "traceability",
                "priority",
                "preconditions",
                "title",
                "test_data",
                "steps",
                "expected_result",
                "postconditions",
                "calibration_status",
            ],
            "structured_references_only": True,
            "no_model_authored_case_prose": True,
            "old_test_cases_available": False,
        },
    }


def writer_response_schema(
    cards: Sequence[WriterCard], graph_digest: str
) -> dict[str, Any]:
    case_keys = [item.case_key for item in cards]
    subject_ids = sorted({item.subject_id for item in cards})
    oracle_ids = sorted({item.expected_result_id for item in cards})
    fixture_ids = sorted(
        {ref.reference_id for item in cards for ref in item.fixture_references}
    )
    data_ids = sorted(
        {ref.reference_id for item in cards for ref in item.data_references}
    )
    action_ids = sorted(
        {ref.reference_id for item in cards for ref in item.action_references}
    )

    def registered_id(values: Sequence[str]) -> dict[str, Any]:
        schema: dict[str, Any] = {"type": "string"}
        if values:
            schema["enum"] = list(values)
        return schema

    case = {
        "type": "object",
        "properties": {
            "case_key": {"type": "string", "enum": list(case_keys)},
            "case_type": {"type": "string", "enum": ["позитивный", "негативный"]},
            "subject_id": registered_id(subject_ids),
            "expected_result_id": registered_id(oracle_ids),
            "fixture_ids": {
                "type": "array",
                "items": registered_id(fixture_ids),
            },
            "data_ids": {
                "type": "array",
                "items": registered_id(data_ids),
            },
            "step_ids": {
                "type": "array",
                "items": registered_id(action_ids),
            },
        },
        "required": [
            "case_key",
            "case_type",
            "subject_id",
            "expected_result_id",
            "fixture_ids",
            "data_ids",
            "step_ids",
        ],
        "additionalProperties": False,
    }
    unresolved = {
        "type": "object",
        "properties": {
            "case_key": {"type": "string", "enum": list(case_keys)},
            "reason": {"type": "string"},
        },
        "required": ["case_key", "reason"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "schema_version": {"type": "integer", "enum": [1]},
            "graph_digest": {"type": "string", "enum": [graph_digest]},
            "cases": {"type": "array", "items": case},
            "unresolved": {"type": "array", "items": unresolved},
        },
        "required": ["schema_version", "graph_digest", "cases", "unresolved"],
        "additionalProperties": False,
    }


def validate_writer_response(
    response: Mapping[str, Any],
    *,
    graph: CoverageGraph,
    plan: TestDesignPlan,
    context: DesignContext,
) -> tuple[tuple[TestCaseDesign, ...], tuple[dict[str, str], ...]]:
    try:
        validate_design_context_for_graph(graph, context)
    except DesignError as exc:
        raise IterationContractError(f"writer design context is invalid: {exc}") from exc
    root = _object(
        response,
        "$",
        {"schema_version", "graph_digest", "cases", "unresolved"},
    )
    if root["schema_version"] != 1 or root["graph_digest"] != graph.digest:
        raise IterationContractError("writer response is not bound to this graph")
    cards = {item.case_key: item for item in plan.writer_cards}
    if plan.graph_digest != graph.digest or plan.blocked_cards:
        raise IterationContractError("writer cannot run for this design plan")
    properties = {item.property_id: item for item in graph.properties}
    obligations = {item.obligation_id: item for item in graph.obligations}
    raw_cases = root["cases"]
    raw_unresolved = root["unresolved"]
    if not isinstance(raw_cases, list) or not isinstance(raw_unresolved, list):
        raise IterationContractError("writer cases and unresolved must be arrays")
    seen: set[str] = set()
    designs: list[TestCaseDesign] = []
    unresolved: list[dict[str, str]] = []
    for index, raw in enumerate(raw_cases):
        item = _object(
            raw,
            f"$.cases[{index}]",
            {
                "case_key",
                "case_type",
                "subject_id",
                "expected_result_id",
                "fixture_ids",
                "data_ids",
                "step_ids",
            },
        )
        case_key = _one_line(item["case_key"], f"$.cases[{index}].case_key")
        if case_key not in cards or case_key in seen:
            raise IterationContractError(f"unknown or duplicate writer case_key: {case_key}")
        seen.add(case_key)
        card = cards[case_key]
        case_type = _one_line(item["case_type"], f"$.cases[{index}].case_type").casefold()
        if case_type not in {"позитивный", "негативный"}:
            raise IterationContractError(f"unsupported case_type for {case_key}")
        if item["subject_id"] != card.subject_id:
            raise IterationContractError(
                f"writer subject binding mismatch for {case_key}"
            )
        if item["expected_result_id"] != card.expected_result_id:
            raise IterationContractError(
                f"writer expected-result binding mismatch for {case_key}"
            )

        def exact_ids(field: str, references: Sequence[Any]) -> tuple[str, ...]:
            actual = _strings(
                item[field],
                f"$.cases[{index}].{field}",
                allow_empty=True,
            )
            expected = tuple(ref.reference_id for ref in references)
            if actual != expected:
                raise IterationContractError(
                    f"writer {field} binding mismatch for {case_key}; "
                    "only the ordered registered reference set is allowed"
                )
            return actual

        exact_ids("fixture_ids", card.fixture_references)
        exact_ids("data_ids", card.data_references)
        exact_ids("step_ids", card.action_references)
        test_data = tuple(ref.text for ref in card.data_references) or ("Не требуются.",)
        steps = tuple(ref.text for ref in card.action_references)
        if not steps:
            raise IterationContractError(
                f"writer card {case_key} has no registered source-backed action"
            )
        try:
            runtime_setup = runtime_preconditions_for_binding(
                prop=properties[card.property_id],
                obligation=obligations[card.obligation_id],
                context=context,
            )
        except (KeyError, DesignError) as exc:
            raise IterationContractError(
                f"writer runner-owned preconditions are not executable: {exc}"
            ) from exc
        preconditions = (
            []
            if runtime_setup == ("Не требуются.",)
            else list(runtime_setup)
        )
        postconditions = (
            (card.cleanup_strategy,)
            if card.cleanup_strategy.strip()
            else ("Не требуются.",)
        )
        designs.append(
            TestCaseDesign(
                case_key=case_key,
                tc_id=card.tc_id,
                status=card.status,
                title=card.runner_title,
                case_type=case_type,
                priority=(context.priorities or {}).get(case_key, "средний"),
                package_id=context.package_id,
                traceability=_case_traceability(graph, card),
                preconditions=tuple(preconditions or ["Не требуются."]),
                test_data=test_data,
                steps=steps,
                expected_result=card.observable_oracle,
                postconditions=postconditions,
                calibration_question=(
                    card.calibration_question
                    if card.status == "candidate-ui-calibration"
                    else ""
                ),
            )
        )
    for index, raw in enumerate(raw_unresolved):
        item = _object(raw, f"$.unresolved[{index}]", {"case_key", "reason"})
        case_key = _one_line(item["case_key"], f"$.unresolved[{index}].case_key")
        reason = _one_line(item["reason"], f"$.unresolved[{index}].reason")
        if case_key not in cards or case_key in seen:
            raise IterationContractError(
                f"unknown or duplicate unresolved case_key: {case_key}"
            )
        seen.add(case_key)
        unresolved.append({"case_key": case_key, "reason": reason})
    if seen != set(cards):
        raise IterationContractError(
            "writer omitted cases: " + ", ".join(sorted(set(cards) - seen))
        )
    return tuple(designs), tuple(unresolved)


def _property_and_obligation_for_design(
    graph: CoverageGraph,
    case: TestCaseDesign,
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    graph_case = next(item for item in graph.cases if item.case_key == case.case_key)
    obligation = next(
        item for item in graph.obligations if item.obligation_id == graph_case.obligation_ids[0]
    )
    prop = next(item for item in graph.properties if item.property_id == obligation.property_id)
    return asdict(prop), asdict(obligation)


def build_runtime_writer_request(
    graph: CoverageGraph,
    plan: TestDesignPlan,
    *,
    mockup_label_aliases: Sequence[Mapping[str, str]] = (),
    revision_findings: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a source-bound request where the model writes runtime TC prose.

    Unlike ``build_writer_request``, this route intentionally lets the writer
    author human-facing runtime fields.  The runner still owns identity,
    lifecycle, traceability, package and promotion fields.
    """

    if plan.graph_digest != graph.digest:
        raise IterationContractError("design plan is not bound to this coverage graph")
    if plan.blocked_cards:
        raise IterationContractError("blocked cards must be resolved before writer")
    if plan.writer_cards:
        raise IterationContractError(
            "model-runtime-prose requires deterministic seed cases; unsupported writer cards must be split upstream"
        )
    cases: list[dict[str, Any]] = []
    for design in sorted(plan.deterministic_cases, key=lambda item: item.case_key):
        prop, obligation = _property_and_obligation_for_design(graph, design)
        cases.append(
            {
                "case_key": design.case_key,
                "tc_id": design.tc_id,
                "status": design.status,
                "case_type": design.case_type,
                "priority": design.priority,
                "package_id": design.package_id,
                "runner_traceability": list(design.traceability),
                "source": {
                    "property": prop,
                    "obligation": obligation,
                },
                "seed_runtime": {
                    "title": design.title,
                    "preconditions": list(design.preconditions),
                    "test_data": list(design.test_data),
                    "steps": list(design.steps),
                    "expected_result": design.expected_result,
                    "postconditions": list(design.postconditions),
                    "calibration_question": design.calibration_question,
                },
            }
        )
    return {
        "schema_version": 1,
        "writer_mode": "model-runtime-prose",
        "graph_digest": graph.digest,
        "route_contract": {
            "route": "runtime-prose",
            "not_legacy_id_selection": True,
            "copy_fields_exactly": ["case_key", "tc_id"],
            "runner_owned_fields": [
                "case_key",
                "tc_id",
                "status",
                "traceability",
                "priority",
                "package_id",
                "calibration_status",
            ],
            "model_authored_fields": [
                "title",
                "preconditions",
                "test_data",
                "steps",
                "expected_result",
                "postconditions",
                "calibration_question",
            ],
            "one_output_case_per_input_seed_case": True,
            "unresolved_policy": (
                "Allowed only for a concrete case with a specific source-backed "
                "reason. Do not mark all valid seed cases unresolved because of "
                "schema or route confusion."
            ),
        },
        "cases": cases,
        "mockup_label_aliases": [dict(item) for item in mockup_label_aliases],
        "revision_findings": dict(revision_findings or {}),
        "constraints": {
            "return_exactly_one_case_per_input_case": True,
            "runner_owned_fields": [
                "case_key",
                "tc_id",
                "status",
                "traceability",
                "priority",
                "package_id",
                "calibration_status",
            ],
            "model_authors_runtime_prose": True,
            "old_test_cases_available": False,
            "mockups_refine_steps_only": True,
            "use_label_from_mockup_for_runtime_text": True,
        },
    }


def runtime_writer_response_schema(
    case_keys: Sequence[str],
    graph_digest: str,
) -> dict[str, Any]:
    text_array = {
        "type": "array",
        "items": {"type": "string"},
        "minItems": 1,
    }
    case = {
        "type": "object",
        "properties": {
            "case_key": {"type": "string", "enum": list(case_keys)},
            "tc_id": {"type": "string"},
            "title": {"type": "string"},
            "case_type": {"type": "string", "enum": ["позитивный", "негативный"]},
            "preconditions": text_array,
            "test_data": text_array,
            "steps": text_array,
            "expected_result": {"type": "string"},
            "postconditions": text_array,
            "calibration_question": {"type": "string"},
        },
        "required": [
            "case_key",
            "tc_id",
            "title",
            "case_type",
            "preconditions",
            "test_data",
            "steps",
            "expected_result",
            "postconditions",
            "calibration_question",
        ],
        "additionalProperties": False,
    }
    unresolved = {
        "type": "object",
        "properties": {
            "case_key": {"type": "string", "enum": list(case_keys)},
            "reason": {"type": "string"},
        },
        "required": ["case_key", "reason"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "schema_version": {"type": "integer", "enum": [1]},
            "writer_mode": {"type": "string", "enum": ["model-runtime-prose"]},
            "graph_digest": {"type": "string", "enum": [graph_digest]},
            "route_contract_ack": {
                "type": "string",
                "enum": ["runtime-prose-one-case-per-seed"],
            },
            "cases": {"type": "array", "items": case},
            "unresolved": {"type": "array", "items": unresolved},
        },
        "required": [
            "schema_version",
            "writer_mode",
            "graph_digest",
            "route_contract_ack",
            "cases",
            "unresolved",
        ],
        "additionalProperties": False,
    }


def _empty_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or "\n" in value or "\r" in value:
        raise IterationContractError(f"{path} must be single-line text")
    return value.strip()


def _normalized_ui_label(value: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        value.replace("`", "").replace("«", "").replace("»", "").strip().casefold(),
    )


def _runtime_text_uses_stale_mockup_alias(
    runtime_text: str,
    mockup_label_aliases: Sequence[Mapping[str, str]],
) -> tuple[str, str] | None:
    normalized_runtime = _normalized_ui_label(runtime_text)
    for alias in mockup_label_aliases:
        canonical_name = str(alias.get("canonical_ft_name", "")).strip()
        label_from_mockup = str(alias.get("label_from_mockup", "")).strip()
        if not canonical_name or not label_from_mockup:
            continue
        canonical_label = _normalized_ui_label(canonical_name)
        mockup_label = _normalized_ui_label(label_from_mockup)
        if (
            canonical_label
            and mockup_label
            and canonical_label in normalized_runtime
            and mockup_label not in normalized_runtime
        ):
            return canonical_name, label_from_mockup
    return None


def _runtime_no_setup_item(value: str) -> bool:
    normalized = _normalized_ui_label(value)
    normalized = re.sub(r"[^\w\s]+", "", normalized, flags=re.UNICODE)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return _RUNTIME_NO_SETUP_RE.fullmatch(normalized) is not None


def _runtime_precondition_problem(preconditions: Sequence[str]) -> str | None:
    if len(preconditions) == 1 and _runtime_no_setup_item(preconditions[0]):
        return None
    numbered = "\n".join(
        f"{index}. {item}" for index, item in enumerate(preconditions, start=1)
    )
    return production_precondition_problem(numbered)


def _runtime_has_executable_step(steps: Sequence[str]) -> bool:
    return any(
        ACTION_STEP_RE.search(step) is not None
        or RUSSIAN_INFINITIVE_STEP_RE.search(step) is not None
        for step in steps
    )


def _runtime_internal_token(
    *,
    case_key: str,
    field: str,
    values: Sequence[str],
) -> str | None:
    for value in values:
        match = _INTERNAL_RUNTIME_TOKEN_RE.search(value)
        if match is not None:
            return (
                f"runtime writer leaked internal identifier in {field} "
                f"for {case_key}: {match.group(0)}"
            )
    return None


def _validate_runtime_writer_prose(
    *,
    case_key: str,
    title: str,
    preconditions: Sequence[str],
    test_data: Sequence[str],
    steps: Sequence[str],
    expected_result: str,
    postconditions: Sequence[str],
    calibration_question: str,
) -> None:
    fields = (
        ("title", (title,)),
        ("preconditions", preconditions),
        ("test_data", test_data),
        ("steps", steps),
        ("expected_result", (expected_result,)),
        ("postconditions", postconditions),
        ("calibration_question", (calibration_question,)),
    )
    for field, values in fields:
        problem = _runtime_internal_token(
            case_key=case_key,
            field=field,
            values=values,
        )
        if problem is not None:
            raise IterationContractError(problem)
    precondition_problem = _runtime_precondition_problem(preconditions)
    if precondition_problem is not None:
        raise IterationContractError(
            "runtime writer returned non-reproducible precondition for "
            f"{case_key}: {precondition_problem}"
        )
    if not _runtime_has_executable_step(steps):
        raise IterationContractError(
            "runtime writer omitted executable user action/check step for "
            f"{case_key}"
        )


def validate_runtime_writer_response(
    response: Mapping[str, Any],
    *,
    graph: CoverageGraph,
    plan: TestDesignPlan,
    context: DesignContext,
    mockup_label_aliases: Sequence[Mapping[str, str]] = (),
) -> tuple[tuple[TestCaseDesign, ...], tuple[dict[str, str], ...]]:
    try:
        validate_design_context_for_graph(graph, context)
    except DesignError as exc:
        raise IterationContractError(f"writer design context is invalid: {exc}") from exc
    root = _object(
        response,
        "$",
        {
            "schema_version",
            "writer_mode",
            "graph_digest",
            "route_contract_ack",
            "cases",
            "unresolved",
        },
    )
    if (
        root["schema_version"] != 1
        or root["writer_mode"] != "model-runtime-prose"
        or root["graph_digest"] != graph.digest
        or root["route_contract_ack"] != "runtime-prose-one-case-per-seed"
    ):
        raise IterationContractError("runtime writer response is not bound to this graph")
    if plan.graph_digest != graph.digest or plan.blocked_cards:
        raise IterationContractError("writer cannot run for this design plan")
    if plan.writer_cards:
        raise IterationContractError(
            "runtime writer response cannot be validated while unsupported writer cards remain"
        )
    expected = {item.case_key: item for item in plan.deterministic_cases}
    raw_cases = root["cases"]
    raw_unresolved = root["unresolved"]
    if not isinstance(raw_cases, list) or not isinstance(raw_unresolved, list):
        raise IterationContractError("runtime writer cases and unresolved must be arrays")
    if not raw_cases and len(raw_unresolved) == len(expected) and expected:
        raise IterationContractError(
            "runtime writer route failure: all input seed cases were returned as "
            "unresolved; this route requires one human-runtime output case per "
            "valid seed case unless a specific individual source blocker exists"
        )
    seen: set[str] = set()
    designs: list[TestCaseDesign] = []
    unresolved: list[dict[str, str]] = []
    for index, raw in enumerate(raw_cases):
        item = _object(
            raw,
            f"$.cases[{index}]",
            {
                "case_key",
                "tc_id",
                "title",
                "case_type",
                "preconditions",
                "test_data",
                "steps",
                "expected_result",
                "postconditions",
                "calibration_question",
            },
        )
        case_key = _one_line(item["case_key"], f"$.cases[{index}].case_key")
        if case_key not in expected or case_key in seen:
            raise IterationContractError(f"unknown or duplicate runtime writer case_key: {case_key}")
        seen.add(case_key)
        seed = expected[case_key]
        tc_id = _one_line(item["tc_id"], f"$.cases[{index}].tc_id")
        if tc_id != seed.tc_id:
            raise IterationContractError(f"runtime writer TC-ID drift for {case_key}")
        case_type = _one_line(item["case_type"], f"$.cases[{index}].case_type").casefold()
        if case_type not in {"позитивный", "негативный"}:
            raise IterationContractError(f"unsupported case_type for {case_key}")
        calibration_question = _empty_string(
            item["calibration_question"],
            f"$.cases[{index}].calibration_question",
        )
        if seed.status == "candidate-ui-calibration":
            if not calibration_question:
                raise IterationContractError(
                    f"runtime writer omitted calibration question for {case_key}"
                )
        elif calibration_question:
            raise IterationContractError(
                f"runtime writer added calibration question to executable case {case_key}"
            )
        title = _one_line(item["title"], f"$.cases[{index}].title")
        preconditions = _strings(
            item["preconditions"],
            f"$.cases[{index}].preconditions",
        )
        test_data = _strings(item["test_data"], f"$.cases[{index}].test_data")
        steps = _strings(item["steps"], f"$.cases[{index}].steps")
        expected_result = _one_line(
            item["expected_result"],
            f"$.cases[{index}].expected_result",
        )
        postconditions = _strings(
            item["postconditions"],
            f"$.cases[{index}].postconditions",
        )
        _validate_runtime_writer_prose(
            case_key=case_key,
            title=title,
            preconditions=preconditions,
            test_data=test_data,
            steps=steps,
            expected_result=expected_result,
            postconditions=postconditions,
            calibration_question=calibration_question,
        )
        runtime_text = "\n".join(
            [
                title,
                "\n".join(preconditions),
                "\n".join(test_data),
                "\n".join(steps),
                "\n".join(postconditions),
            ]
        )
        stale_alias = _runtime_text_uses_stale_mockup_alias(
            runtime_text,
            mockup_label_aliases,
        )
        if stale_alias is not None:
            canonical_name, label_from_mockup = stale_alias
            raise IterationContractError(
                "runtime writer mockup visible label drift for "
                f"{case_key}: uses {canonical_name!r} instead of {label_from_mockup!r}"
            )
        designs.append(
            TestCaseDesign(
                case_key=case_key,
                tc_id=seed.tc_id,
                status=seed.status,
                title=title,
                case_type=case_type,
                priority=seed.priority,
                package_id=seed.package_id,
                traceability=seed.traceability,
                preconditions=preconditions,
                test_data=test_data,
                steps=steps,
                expected_result=expected_result,
                postconditions=postconditions,
                calibration_question=calibration_question,
            )
        )
    for index, raw in enumerate(raw_unresolved):
        item = _object(raw, f"$.unresolved[{index}]", {"case_key", "reason"})
        case_key = _one_line(item["case_key"], f"$.unresolved[{index}].case_key")
        reason = _one_line(item["reason"], f"$.unresolved[{index}].reason")
        if case_key not in expected or case_key in seen:
            raise IterationContractError(
                f"unknown or duplicate unresolved case_key: {case_key}"
            )
        seen.add(case_key)
        unresolved.append({"case_key": case_key, "reason": reason})
    if seen != set(expected):
        raise IterationContractError(
            "runtime writer omitted cases: " + ", ".join(sorted(set(expected) - seen))
        )
    return tuple(designs), tuple(unresolved)


@dataclass(frozen=True)
class SuiteGateReport:
    passed: bool
    graph_digest: str
    draft_sha256: str
    expected_case_count: int
    actual_case_count: int
    findings: tuple[str, ...]
    production_gate: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_suite(
    *,
    graph: CoverageGraph,
    cases: Sequence[TestCaseDesign],
    markdown: str,
    checked_path: str,
) -> SuiteGateReport:
    expected = {item.case_key: item for item in graph.cases}
    actual: dict[str, TestCaseDesign] = {}
    findings: list[str] = []
    for item in cases:
        if item.case_key in actual:
            findings.append(f"duplicate case_key: {item.case_key}")
            continue
        actual[item.case_key] = item
        source = expected.get(item.case_key)
        if source is None:
            findings.append(f"unknown case_key: {item.case_key}")
            continue
        if item.tc_id != source.tc_id:
            findings.append(f"stable TC-ID drift for {item.case_key}")
        if item.status != source.status:
            findings.append(f"case status drift for {item.case_key}")
        if set(source.obligation_ids) - set(item.traceability):
            findings.append(f"missing obligation traceability for {item.case_key}")
    for case_key in sorted(set(expected) - set(actual)):
        findings.append(f"missing case: {case_key}")
    production = validate_production_tc_content(markdown, checked_path=checked_path)
    production_payload = production.as_dict()
    remaining_production_findings = list(production_payload["findings"])
    production_payload["findings"] = remaining_production_findings
    production_payload["passed"] = not remaining_production_findings
    if remaining_production_findings:
        findings.append("production gate failed")
    return SuiteGateReport(
        passed=not findings,
        graph_digest=graph.digest,
        draft_sha256=hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        expected_case_count=len(expected),
        actual_case_count=len(actual),
        findings=tuple(findings),
        production_gate=production_payload,
    )


def build_reviewer_request(
    *,
    graph: CoverageGraph,
    cases: Sequence[TestCaseDesign],
    gate: SuiteGateReport,
    evidence_pack: Any | None = None,
) -> dict[str, Any]:
    if not gate.passed or gate.graph_digest != graph.digest:
        raise IterationContractError("reviewer may receive only a gate-passed suite")
    if evidence_pack is not None:
        if isinstance(evidence_pack, Mapping):
            pack_payload = dict(evidence_pack)
            declared_digest: Any = None
        else:
            to_dict = getattr(evidence_pack, "to_dict", None)
            if not callable(to_dict):
                raise IterationContractError(
                    "reviewer evidence pack must be a mapping or expose to_dict()"
                )
            pack_payload = to_dict()
            declared_digest = getattr(evidence_pack, "digest", None)
        if not isinstance(pack_payload, dict):
            raise IterationContractError("reviewer evidence pack must serialize to an object")
        expected_pack_fields = {
            "schema_version",
            "identity",
            "literal_source_evidence",
            "source_structure",
            "dictionaries",
            "coverage_gaps",
            "mockup_attachments",
            "normalized_projection",
            "test_cases",
            "coverage_mapping",
            "supporting_evidence_mapping",
            "design_support_mapping",
            "acceptance",
        }
        if set(pack_payload) != expected_pack_fields:
            raise IterationContractError(
                "reviewer evidence pack fields differ; "
                f"missing={sorted(expected_pack_fields - set(pack_payload))}, "
                f"unknown={sorted(set(pack_payload) - expected_pack_fields)}"
            )
        identity = pack_payload.get("identity")
        if not isinstance(identity, Mapping):
            raise IterationContractError("reviewer evidence identity must be an object")
        if (
            pack_payload.get("schema_version") != 2
            or identity.get("graph_digest") != graph.digest
            or identity.get("draft_sha256") != gate.draft_sha256
        ):
            raise IterationContractError(
                "reviewer evidence pack is not bound to this graph and draft"
            )
        expected_designs = [
            item.to_dict() for item in sorted(cases, key=lambda item: item.case_key)
        ]
        test_cases = pack_payload.get("test_cases")
        if (
            not isinstance(test_cases, Mapping)
            or _canonical_digest(test_cases.get("designs"))
            != _canonical_digest(expected_designs)
        ):
            raise IterationContractError(
                "reviewer evidence pack test-case designs differ from the gate-passed suite"
            )
        acceptance = reviewer_acceptance_contract(schema_version=2)
        if pack_payload.get("acceptance") != acceptance:
            raise IterationContractError(
                "reviewer evidence pack acceptance contract is not v2 production-safe"
            )
        literal_rows = pack_payload.get("literal_source_evidence")
        source_structure = pack_payload.get("source_structure")
        if not isinstance(literal_rows, list) or not isinstance(
            source_structure,
            Mapping,
        ):
            raise IterationContractError(
                "reviewer evidence literal rows and source structure are invalid"
            )
        scope_definition = source_structure.get("scope_definition")
        if not has_complete_all_row_parity(literal_rows, source_structure):
            raise IterationContractError(
                "reviewer evidence lacks a complete bounded DOCX/XHTML/PDF parity proof"
            )
        coverage_gaps = pack_payload.get("coverage_gaps")
        gap_ids = (
            scope_definition.get("gap_ids")
            if isinstance(scope_definition, Mapping)
            else None
        )
        gap_content = (
            coverage_gaps.get("content")
            if isinstance(coverage_gaps, Mapping)
            else None
        )
        if (
            not isinstance(gap_ids, list)
            or not isinstance(coverage_gaps, Mapping)
            or coverage_gaps.get("registered_gap_ids") != sorted(gap_ids)
            or coverage_gaps.get("materialized_gap_ids") != sorted(gap_ids)
            or coverage_gaps.get("status")
            != "complete-literal-registered-artifact"
            or not isinstance(gap_content, str)
            or not gap_content.strip()
            or coverage_gaps.get("content_sha256")
            != hashlib.sha256(gap_content.encode("utf-8")).hexdigest()
        ):
            raise IterationContractError(
                "reviewer evidence coverage-gap artifact is incomplete or stale"
            )
        if not isinstance(pack_payload.get("supporting_evidence_mapping"), list):
            raise IterationContractError(
                "reviewer evidence supporting mappings must be an array"
            )
        coverage_mapping = pack_payload.get("coverage_mapping")
        if not isinstance(coverage_mapping, list):
            raise IterationContractError(
                "reviewer evidence primary coverage mapping must be an array"
            )
        primary_bindings = [
            (
                item.get("case_key"),
                item.get("tc_id"),
                item.get("obligation_id"),
            )
            for item in coverage_mapping
            if isinstance(item, Mapping) and item.get("case_key")
        ]
        expected_primary_bindings = [
            (item.case_key, item.tc_id, item.obligation_ids[0])
            for item in graph.cases
        ]
        if sorted(primary_bindings) != sorted(expected_primary_bindings):
            raise IterationContractError(
                "reviewer evidence primary coverage mapping must bind every "
                "graph case exactly once"
            )
        design_support_mapping = pack_payload.get("design_support_mapping")
        if not isinstance(design_support_mapping, list):
            raise IterationContractError(
                "reviewer evidence design-support mapping must be an array"
            )
        # Import locally so the iteration contract remains the lower-level
        # dependency for callers that do not use source-qualified evidence.
        from test_case_agent.reviewer_evidence import build_design_support_mapping

        expected_design_support = build_design_support_mapping(graph, cases)
        if design_support_mapping != expected_design_support:
            raise IterationContractError(
                "reviewer evidence design-support mapping differs from exact "
                "sibling actions materialized by the gate-passed suite"
            )
        pack_digest = _canonical_digest(pack_payload)
        if declared_digest is not None and declared_digest != pack_digest:
            raise IterationContractError(
                "reviewer evidence pack declared digest differs from its payload"
            )
        return {
            "schema_version": 2,
            "graph_digest": graph.digest,
            "draft_sha256": gate.draft_sha256,
            "evidence_pack_sha256": pack_digest,
            "reviewer_evidence_pack": pack_payload,
            "acceptance": acceptance,
        }
    properties = {item.property_id: item for item in graph.properties}
    obligations = {item.obligation_id: item for item in graph.obligations}
    graph_cases = {item.case_key: item for item in graph.cases}
    projections: list[dict[str, Any]] = []
    for design in sorted(cases, key=lambda item: item.case_key):
        graph_case = graph_cases[design.case_key]
        obligation = obligations[graph_case.obligation_ids[0]]
        prop = properties[obligation.property_id]
        condition_precondition = ""
        if obligation.condition_key != "always":
            condition_precondition = (
                prop.condition_clauses[0]
                if len(prop.condition_clauses) == 1
                else prop.canonical_statement
            )
        projections.append(
            {
                "case_key": design.case_key,
                "tc_id": design.tc_id,
                "status": design.status,
                "source": {
                    "assertion_id": prop.assertion_id,
                    "property_kind": prop.property_kind,
                    "canonical_statement": prop.canonical_statement,
                    "requirement_codes": list(prop.requirement_codes),
                    "condition_clauses": list(prop.condition_clauses),
                },
                "obligation": {
                    "obligation_id": obligation.obligation_id,
                    "atom_id": obligation.atom_id,
                    "coverage_variant": obligation.coverage_variant,
                    "condition_key": obligation.condition_key,
                    "condition_precondition": condition_precondition,
                    "atomic_statement": obligation.atomic_statement,
                    "observable_oracle": obligation.observable_oracle,
                    "validation_trigger": obligation.validation_trigger,
                    "fixture_values": list(obligation.fixture_values),
                    "cleanup_strategy": obligation.cleanup_strategy,
                    "source_oracle_id": obligation.source_oracle_id,
                    "calibration_question": obligation.calibration_question,
                },
                "test_case": design.to_dict(),
            }
        )
    return {
        "schema_version": 1,
        "graph_digest": graph.digest,
        "draft_sha256": gate.draft_sha256,
        "cases": projections,
        "acceptance": reviewer_acceptance_contract(),
    }


def reviewer_response_schema(
    case_bindings: Sequence[tuple[str, str, str] | tuple[str, str, str, str]],
    *,
    graph_digest: str,
    draft_sha256: str,
    reviewer_request: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    case_keys = [item[0] for item in case_bindings]
    tc_ids = [item[1] for item in case_bindings]
    obligation_ids = [item[2] for item in case_bindings]
    result = {
        "type": "object",
        "properties": {
            "case_key": {"type": "string", "enum": case_keys},
            "tc_id": {"type": "string", "enum": tc_ids},
            "obligation_id": {"type": "string", "enum": obligation_ids},
            "status": {"type": "string", "enum": sorted(_RESULT_STATUSES)},
            "comment": {"type": "string"},
        },
        "required": ["case_key", "tc_id", "obligation_id", "status", "comment"],
        "additionalProperties": False,
    }
    finding = {
        "type": "object",
        "properties": {
            "severity": {"type": "string", "enum": ["error", "warning"]},
            "case_key": {"type": "string", "enum": case_keys},
            "tc_id": {"type": "string", "enum": tc_ids},
            "obligation_id": {"type": "string", "enum": obligation_ids},
            "message": {"type": "string"},
        },
        "required": ["severity", "case_key", "tc_id", "obligation_id", "message"],
        "additionalProperties": False,
    }
    if reviewer_request is not None and reviewer_request.get("schema_version") == 2:
        pack = reviewer_request.get("reviewer_evidence_pack")
        if not isinstance(pack, Mapping):
            raise IterationContractError("reviewer v2 request omits its evidence pack")
        raw_rows = pack.get("literal_source_evidence")
        raw_mapping = pack.get("coverage_mapping")
        raw_supporting = pack.get("supporting_evidence_mapping")
        raw_design_support = pack.get("design_support_mapping")
        if (
            not isinstance(raw_rows, list)
            or not isinstance(raw_mapping, list)
            or not isinstance(raw_supporting, list)
            or not isinstance(raw_design_support, list)
        ):
            raise IterationContractError(
                "reviewer evidence rows and all coverage/support mappings must be arrays"
            )
        source_row_ids = sorted(
            {
                item.get("source_row_id")
                for item in raw_rows
                if isinstance(item, Mapping)
                and isinstance(item.get("source_row_id"), str)
                and item.get("source_row_id")
            }
        )
        if not source_row_ids:
            raise IterationContractError("reviewer evidence pack has no source rows")

        def mapped_values(name: str) -> list[str]:
            values = {
                item.get(name)
                for item in raw_mapping
                if isinstance(item, Mapping)
                and isinstance(item.get(name), str)
                and item.get(name)
            }
            return sorted(values)

        assertion_ids = mapped_values("assertion_id")
        property_ids = mapped_values("property_id")
        mapped_obligations = mapped_values("obligation_id")
        mapped_case_keys = mapped_values("case_key")
        mapped_tc_ids = mapped_values("tc_id")
        if set(mapped_obligations) != set(obligation_ids):
            raise IterationContractError(
                "reviewer evidence obligation mapping differs from graph cases"
            )
        if set(mapped_case_keys) != set(case_keys) or set(mapped_tc_ids) != set(tc_ids):
            raise IterationContractError(
                "reviewer evidence case mapping differs from graph cases"
            )
        primary_chains = {
            tuple(item.get(name, "") for name in (
                "source_row_id",
                "assertion_id",
                "property_id",
                "obligation_id",
                "case_key",
                "tc_id",
            ))
            for item in raw_mapping
            if isinstance(item, Mapping) and item.get("case_key")
        }
        expected_primary = {
            (case_key, tc_id, obligation_id)
            for case_key, tc_id, obligation_id in zip(
                case_keys,
                tc_ids,
                obligation_ids,
            )
        }
        if (
            len(primary_chains) != len(expected_primary)
            or {(item[-2], item[-1], item[-3]) for item in primary_chains}
            != expected_primary
        ):
            raise IterationContractError(
                "reviewer evidence primary mapping is not one exact chain per case"
            )
        design_support_binding_roles = {"primary"}
        design_support_item_indices: set[int] = set()
        for index, item in enumerate(raw_design_support):
            if (
                not isinstance(item, Mapping)
                or set(item) != _DESIGN_SUPPORT_MAPPING_FIELDS
                or item.get("support_role") not in _DESIGN_SUPPORT_ROLE_FIELDS
                or item.get("test_case_field")
                != _DESIGN_SUPPORT_ROLE_FIELDS.get(item.get("support_role"))
                or type(item.get("item_index")) is not int
                or item["item_index"] < 0
            ):
                raise IterationContractError(
                    f"reviewer evidence design_support_mapping[{index}] is invalid"
                )
            design_support_binding_roles.add(
                f"design-support-{item['support_role']}"
            )
            design_support_item_indices.add(item["item_index"])
        test_assertion_ids = sorted(
            set(assertion_ids)
            | {
                item["assertion_id"]
                for item in raw_design_support
                if isinstance(item.get("assertion_id"), str)
            }
        )
        test_property_ids = sorted(
            set(property_ids)
            | {
                item["property_id"]
                for item in raw_design_support
                if isinstance(item.get("property_id"), str)
            }
        )
        test_obligation_ids = sorted(
            set(mapped_obligations)
            | {
                item["obligation_id"]
                for item in raw_design_support
                if isinstance(item.get("obligation_id"), str)
            }
        )

        def optional_enum(values: Sequence[str]) -> dict[str, Any]:
            return {"type": "string", "enum": ["", *values]}

        falsification_probe_result = {
            "type": "object",
            "properties": {
                "outcome": {
                    "type": "string",
                    "enum": sorted(_FALSIFICATION_OUTCOMES - {"not-recorded"}),
                },
                "detail": {"type": "string"},
                "binding_role": {
                    "type": "string",
                    "enum": sorted(design_support_binding_roles),
                },
                "obligation_id": {
                    "type": "string",
                    "enum": test_obligation_ids,
                },
                "binding_item_index": {
                    "type": "integer",
                    "enum": [-1, *sorted(design_support_item_indices)],
                },
                "trigger_or_step": {"type": "string"},
                "oracle": {"type": "string"},
            },
            "required": [
                "outcome",
                "detail",
                "binding_role",
                "obligation_id",
                "binding_item_index",
                "trigger_or_step",
                "oracle",
            ],
            "additionalProperties": False,
        }
        v2_result = {
            "type": "object",
            "properties": {
                **result["properties"],
                "falsification": {
                    "type": "object",
                    "properties": {
                        probe: falsification_probe_result
                        for probe in REVIEWER_FALSIFICATION_PROBES
                    },
                    "required": list(REVIEWER_FALSIFICATION_PROBES),
                    "additionalProperties": False,
                },
            },
            "required": [*result["required"], "falsification"],
            "additionalProperties": False,
        }

        source_finding = {
            "type": "object",
            "properties": {
                "severity": {"type": "string", "enum": ["error", "warning"]},
                "finding_type": {
                    "type": "string",
                    "enum": sorted(_SOURCE_PROJECTION_FINDING_TYPES),
                },
                "source_row_id": {"type": "string", "enum": source_row_ids},
                "assertion_id": optional_enum(assertion_ids),
                "property_id": optional_enum(property_ids),
                "obligation_id": optional_enum(mapped_obligations),
                "case_key": optional_enum(mapped_case_keys),
                "tc_id": optional_enum(mapped_tc_ids),
                "message": {"type": "string"},
            },
            "required": [
                "severity",
                "finding_type",
                "source_row_id",
                "assertion_id",
                "property_id",
                "obligation_id",
                "case_key",
                "tc_id",
                "message",
            ],
            "additionalProperties": False,
        }
        test_finding = {
            "type": "object",
            "properties": {
                "severity": {"type": "string", "enum": ["error", "warning"]},
                "finding_type": {
                    "type": "string",
                    "enum": sorted(_TEST_CASE_FINDING_TYPES),
                },
                "binding_role": {
                    "type": "string",
                    "enum": sorted(design_support_binding_roles),
                },
                "falsification_probe": {
                    "type": "string",
                    "enum": ["", *REVIEWER_FALSIFICATION_PROBES],
                },
                "source_row_id": {"type": "string", "enum": source_row_ids},
                "assertion_id": {"type": "string", "enum": test_assertion_ids},
                "property_id": {"type": "string", "enum": test_property_ids},
                "obligation_id": {"type": "string", "enum": test_obligation_ids},
                "case_key": {"type": "string", "enum": mapped_case_keys},
                "tc_id": {"type": "string", "enum": mapped_tc_ids},
                "message": {"type": "string"},
            },
            "required": [
                "severity",
                "finding_type",
                "binding_role",
                "falsification_probe",
                "source_row_id",
                "assertion_id",
                "property_id",
                "obligation_id",
                "case_key",
                "tc_id",
                "message",
            ],
            "additionalProperties": False,
        }
        evidence_pack_sha256 = reviewer_request.get("evidence_pack_sha256")
        if not isinstance(evidence_pack_sha256, str):
            raise IterationContractError("reviewer v2 request omits evidence pack digest")
        return {
            "type": "object",
            "properties": {
                "schema_version": {"type": "integer", "enum": [2]},
                "graph_digest": {"type": "string", "enum": [graph_digest]},
                "draft_sha256": {"type": "string", "enum": [draft_sha256]},
                "evidence_pack_sha256": {
                    "type": "string",
                    "enum": [evidence_pack_sha256],
                },
                "decision": {"type": "string", "enum": sorted(_DECISIONS)},
                "case_results": {
                    "type": "array",
                    "items": v2_result,
                    "minItems": len(case_keys),
                    "maxItems": len(case_keys),
                },
                "source_projection_findings": {
                    "type": "array",
                    "items": source_finding,
                },
                "test_case_findings": {"type": "array", "items": test_finding},
                "summary": {"type": "string"},
            },
            "required": [
                "schema_version",
                "graph_digest",
                "draft_sha256",
                "evidence_pack_sha256",
                "decision",
                "case_results",
                "source_projection_findings",
                "test_case_findings",
                "summary",
            ],
            "additionalProperties": False,
        }
    return {
        "type": "object",
        "properties": {
            "schema_version": {"type": "integer", "enum": [1]},
            "graph_digest": {"type": "string", "enum": [graph_digest]},
            "draft_sha256": {"type": "string", "enum": [draft_sha256]},
            "decision": {"type": "string", "enum": sorted(_DECISIONS)},
            "case_results": {"type": "array", "items": result},
            "findings": {"type": "array", "items": finding},
            "summary": {"type": "string"},
        },
        "required": [
            "schema_version",
            "graph_digest",
            "draft_sha256",
            "decision",
            "case_results",
            "findings",
            "summary",
        ],
        "additionalProperties": False,
    }


def _validate_reviewer_response_v2(
    response: Mapping[str, Any],
    *,
    graph: CoverageGraph,
    draft_sha256: str,
    reviewer_request: Mapping[str, Any],
    allow_legacy_unrecorded_falsification: bool = False,
) -> tuple[bool, str]:
    root = _object(
        response,
        "$",
        {
            "schema_version",
            "graph_digest",
            "draft_sha256",
            "evidence_pack_sha256",
            "decision",
            "case_results",
            "source_projection_findings",
            "test_case_findings",
            "summary",
        },
    )
    expected_pack_sha256 = reviewer_request.get("evidence_pack_sha256")
    if (
        root["schema_version"] != 2
        or root["graph_digest"] != graph.digest
        or root["draft_sha256"] != draft_sha256
        or root["evidence_pack_sha256"] != expected_pack_sha256
    ):
        raise IterationContractError(
            "reviewer response is not bound to this draft and evidence pack"
        )
    decision = _one_line(root["decision"], "$.decision")
    if decision not in _DECISIONS:
        raise IterationContractError(f"unsupported reviewer decision: {decision}")
    _one_line(root["summary"], "$.summary")
    expected: dict[str, tuple[str, str, str]] = {}
    obligations = {item.obligation_id: item for item in graph.obligations}
    for case in graph.cases:
        obligation_id = case.obligation_ids[0]
        if obligation_id not in obligations:  # pragma: no cover
            raise IterationContractError(f"graph case references unknown {obligation_id}")
        expected[case.case_key] = (
            case.tc_id,
            obligation_id,
            "calibration-pending"
            if case.status == "candidate-ui-calibration"
            else "covered",
        )
    raw_results = root["case_results"]
    source_findings = root["source_projection_findings"]
    test_findings = root["test_case_findings"]
    if not all(isinstance(item, list) for item in (raw_results, source_findings, test_findings)):
        raise IterationContractError(
            "reviewer results and both finding categories must be arrays"
        )
    seen: set[str] = set()
    falsification_by_case: dict[
        str,
        dict[str, tuple[str, str, str, str, str, int]],
    ] = {}
    all_required_statuses = True
    for index, raw in enumerate(raw_results):
        item = _object(
            raw,
            f"$.case_results[{index}]",
            {
                "case_key",
                "tc_id",
                "obligation_id",
                "status",
                "comment",
                "falsification",
            },
        )
        case_key = _one_line(item["case_key"], f"$.case_results[{index}].case_key")
        if case_key not in expected or case_key in seen:
            raise IterationContractError(
                f"reviewer has unknown or duplicate case_key: {case_key}"
            )
        seen.add(case_key)
        tc_id, obligation_id, required_status = expected[case_key]
        if item["tc_id"] != tc_id or item["obligation_id"] != obligation_id:
            raise IterationContractError(f"reviewer binding mismatch for {case_key}")
        status = _one_line(item["status"], f"$.case_results[{index}].status")
        if status not in _RESULT_STATUSES:
            raise IterationContractError(f"unsupported reviewer result status: {status}")
        if not isinstance(item["comment"], str):
            raise IterationContractError(f"reviewer comment for {case_key} must be text")
        falsification = _object(
            item["falsification"],
            f"$.case_results[{index}].falsification",
            set(REVIEWER_FALSIFICATION_PROBES),
        )
        probe_results: dict[str, tuple[str, str, str, str, str, int]] = {}
        for probe in REVIEWER_FALSIFICATION_PROBES:
            probe_result = _object(
                falsification[probe],
                f"$.case_results[{index}].falsification.{probe}",
                {
                    "outcome",
                    "detail",
                    "binding_role",
                    "obligation_id",
                    "binding_item_index",
                    "trigger_or_step",
                    "oracle",
                },
            )
            outcome = _one_line(
                probe_result["outcome"],
                f"$.case_results[{index}].falsification.{probe}.outcome",
            )
            if outcome not in _FALSIFICATION_OUTCOMES:
                raise IterationContractError(
                    f"reviewer falsification outcome is invalid for {case_key}/{probe}"
                )
            _one_line(
                probe_result["detail"],
                f"$.case_results[{index}].falsification.{probe}.detail",
            )
            binding_role = _one_line(
                probe_result["binding_role"],
                f"$.case_results[{index}].falsification.{probe}.binding_role",
            )
            probe_obligation_id = _one_line(
                probe_result["obligation_id"],
                f"$.case_results[{index}].falsification.{probe}.obligation_id",
            )
            binding_item_index = probe_result["binding_item_index"]
            if type(binding_item_index) is not int or binding_item_index < -1:
                raise IterationContractError(
                    f"reviewer falsification item index is invalid for "
                    f"{case_key}/{probe}"
                )
            trigger_or_step = _one_line(
                probe_result["trigger_or_step"],
                f"$.case_results[{index}].falsification.{probe}.trigger_or_step",
            )
            oracle = _one_line(
                probe_result["oracle"],
                f"$.case_results[{index}].falsification.{probe}.oracle",
            )
            if (
                outcome == "not-recorded"
                and not allow_legacy_unrecorded_falsification
            ):
                raise IterationContractError(
                    "live reviewer response cannot use not-recorded falsification"
                )
            probe_results[probe] = (
                outcome,
                trigger_or_step,
                oracle,
                binding_role,
                probe_obligation_id,
                binding_item_index,
            )
        outcomes = {item[0] for item in probe_results.values()}
        if "not-recorded" in outcomes and outcomes != {"not-recorded"}:
            raise IterationContractError(
                f"legacy falsification receipt is mixed for {case_key}"
            )
        falsification_by_case[case_key] = probe_results
        all_required_statuses = all_required_statuses and status == required_status
    if seen != set(expected):
        raise IterationContractError(
            "reviewer omitted cases: " + ", ".join(sorted(set(expected) - seen))
        )

    pack = reviewer_request.get("reviewer_evidence_pack")
    if not isinstance(pack, Mapping):  # pragma: no cover - request builder invariant
        raise IterationContractError("reviewer v2 request omits its evidence pack")
    raw_rows = pack.get("literal_source_evidence")
    raw_mapping = pack.get("coverage_mapping")
    raw_supporting = pack.get("supporting_evidence_mapping")
    raw_design_support = pack.get("design_support_mapping")
    raw_test_cases = pack.get("test_cases")
    raw_designs = (
        raw_test_cases.get("designs")
        if isinstance(raw_test_cases, Mapping)
        else None
    )
    if (
        not isinstance(raw_rows, list)
        or not isinstance(raw_mapping, list)
        or not isinstance(raw_supporting, list)
        or not isinstance(raw_design_support, list)
        or not isinstance(raw_designs, list)
    ):
        raise IterationContractError("reviewer v2 evidence bindings are invalid")
    designs_by_case: dict[str, Mapping[str, Any]] = {}
    for index, raw_design in enumerate(raw_designs):
        case_key = raw_design.get("case_key") if isinstance(raw_design, Mapping) else None
        if (
            not isinstance(case_key, str)
            or case_key not in expected
            or case_key in designs_by_case
        ):
            raise IterationContractError(
                f"reviewer v2 design[{index}] has an invalid case binding"
            )
        designs_by_case[case_key] = raw_design
    if set(designs_by_case) != set(expected):
        raise IterationContractError("reviewer v2 designs do not cover every case")
    allowed_probe_bindings: dict[str, set[tuple[str, str, int]]] = {
        case_key: {("primary", binding[1], -1)}
        for case_key, binding in expected.items()
    }
    support_materialized_items: dict[
        tuple[str, str, str, int],
        set[str],
    ] = {}
    for index, item in enumerate(raw_design_support):
        if (
            not isinstance(item, Mapping)
            or set(item) != _DESIGN_SUPPORT_MAPPING_FIELDS
            or item.get("support_role") not in _DESIGN_SUPPORT_ROLE_FIELDS
            or item.get("test_case_field")
            != _DESIGN_SUPPORT_ROLE_FIELDS.get(item.get("support_role"))
        ):
            raise IterationContractError(
                f"reviewer evidence design_support_mapping[{index}] is invalid"
            )
        case_key = item.get("case_key")
        obligation_id = item.get("obligation_id")
        item_index = item.get("item_index")
        materialized_text = item.get("materialized_text")
        test_case_field = item.get("test_case_field")
        design = designs_by_case.get(case_key) if isinstance(case_key, str) else None
        field_items = (
            design.get(test_case_field)
            if isinstance(design, Mapping) and isinstance(test_case_field, str)
            else None
        )
        if (
            not isinstance(case_key, str)
            or case_key not in expected
            or item.get("tc_id") != expected[case_key][0]
            or not isinstance(obligation_id, str)
            or obligation_id not in obligations
            or type(item_index) is not int
            or item_index < 0
            or not isinstance(materialized_text, str)
            or not materialized_text
            or not isinstance(field_items, (list, tuple))
            or item_index >= len(field_items)
            or field_items[item_index] != materialized_text
        ):
            raise IterationContractError(
                f"reviewer evidence design_support_mapping[{index}] binding is invalid"
            )
        binding_role = f"design-support-{item['support_role']}"
        allowed_probe_bindings[case_key].add(
            (binding_role, obligation_id, item_index)
        )
        support_materialized_items.setdefault(
            (case_key, binding_role, obligation_id, item_index),
            set(),
        ).add(materialized_text)
    for case_key, probe_results in falsification_by_case.items():
        design = designs_by_case[case_key]
        design_basis: dict[str, tuple[str, ...]] = {}
        for field in ("preconditions", "test_data", "steps", "postconditions"):
            values = design.get(field)
            if not isinstance(values, (list, tuple)) or any(
                not isinstance(value, str) or not value.strip() for value in values
            ):
                raise IterationContractError(
                    f"reviewer v2 design {case_key}.{field} is invalid"
                )
            design_basis[field] = tuple(values)
        expected_result = design.get("expected_result")
        if not isinstance(expected_result, str) or not expected_result.strip():
            raise IterationContractError(
                f"reviewer v2 design {case_key}.expected_result is invalid"
            )
        tc_steps = set(design_basis["steps"])
        tc_context = set().union(*design_basis.values())
        for probe, (
            outcome,
            trigger_or_step,
            oracle,
            binding_role,
            probe_obligation_id,
            binding_item_index,
        ) in probe_results.items():
            probe_binding = (
                binding_role,
                probe_obligation_id,
                binding_item_index,
            )
            if probe_binding not in allowed_probe_bindings[case_key]:
                raise IterationContractError(
                    f"reviewer falsification chain for {case_key}/{probe} is invalid"
                )
            obligation = obligations[probe_obligation_id]
            support_items = support_materialized_items.get(
                (
                    case_key,
                    binding_role,
                    probe_obligation_id,
                    binding_item_index,
                ),
                set(),
            )
            if outcome in {"passed", "not-recorded"}:
                if binding_role != "primary":
                    allowed_triggers = support_items
                elif probe == "failure_attribution":
                    allowed_triggers = set().union(
                        design_basis["preconditions"],
                        design_basis["test_data"],
                        design_basis["steps"],
                    )
                else:
                    allowed_triggers = tc_steps
                allowed_oracles = {expected_result}
            else:
                bound_tc_items = (
                    support_items if binding_role != "primary" else tc_context
                )
                allowed_triggers = {
                    *bound_tc_items,
                    obligation.validation_trigger,
                    obligation.cleanup_strategy,
                }
                allowed_oracles = {expected_result, obligation.observable_oracle}
            if trigger_or_step not in allowed_triggers or oracle not in allowed_oracles:
                raise IterationContractError(
                    f"reviewer falsification basis for {case_key}/{probe} "
                    "is not bound to the reviewed case and obligation"
                )
    source_row_ids = {
        item.get("source_row_id")
        for item in raw_rows
        if isinstance(item, Mapping) and isinstance(item.get("source_row_id"), str)
    }
    chain_fields = (
        "source_row_id",
        "assertion_id",
        "property_id",
        "obligation_id",
        "case_key",
        "tc_id",
    )
    primary_chains = {
        tuple(item.get(name, "") for name in chain_fields)
        for item in raw_mapping
        if isinstance(item, Mapping)
        and all(isinstance(item.get(name, ""), str) for name in chain_fields)
    }
    supporting_chains = {
        tuple(item.get(name, "") for name in chain_fields)
        for item in raw_supporting
        if isinstance(item, Mapping)
        and all(isinstance(item.get(name, ""), str) for name in chain_fields)
    }
    design_support_chains = {
        (
            f"design-support-{item.get('support_role')}",
            *(item.get(name, "") for name in chain_fields),
        )
        for item in raw_design_support
        if isinstance(item, Mapping)
        and item.get("support_role") in _DESIGN_SUPPORT_ROLE_FIELDS
        and all(isinstance(item.get(name, ""), str) for name in chain_fields)
    }
    primary_test_chains = {("primary", *chain) for chain in primary_chains}

    finding_fields = {
        "severity",
        "finding_type",
        *chain_fields,
        "message",
    }

    def validate_finding(
        raw: Any,
        *,
        path: str,
        allowed_types: set[str],
        require_complete_chain: bool,
        allowed_chains: set[tuple[str, ...]],
        require_binding_role: bool = False,
        require_falsification_probe: bool = False,
    ) -> str:
        expected_fields = set(finding_fields)
        if require_binding_role:
            expected_fields.add("binding_role")
        if require_falsification_probe:
            expected_fields.add("falsification_probe")
        item = _object(raw, path, expected_fields)
        if item["severity"] not in {"error", "warning"}:
            raise IterationContractError(f"{path}.severity is invalid")
        if item["finding_type"] not in allowed_types:
            raise IterationContractError(f"{path}.finding_type is invalid")
        message = item["message"]
        _one_line(message, f"{path}.message")
        values = tuple(item[name] for name in chain_fields)
        if any(not isinstance(value, str) for value in values):
            raise IterationContractError(f"{path} binding fields must be text")
        if values[0] not in source_row_ids:
            raise IterationContractError(f"{path} references unknown source row")
        if require_complete_chain and any(not value for value in values):
            raise IterationContractError(f"{path} must bind the complete evidence chain")
        first_empty = next((index for index, value in enumerate(values) if not value), len(values))
        if any(values[index] for index in range(first_empty, len(values))):
            raise IterationContractError(f"{path} skips an evidence binding level")
        binding_role = ""
        falsification_probe = ""
        chain_key = values
        if require_binding_role:
            binding_role = _one_line(item["binding_role"], f"{path}.binding_role")
            chain_key = (binding_role, *values)
        if require_falsification_probe:
            raw_probe = item["falsification_probe"]
            if (
                not isinstance(raw_probe, str)
                or "\n" in raw_probe
                or "\r" in raw_probe
                or raw_probe not in {"", *REVIEWER_FALSIFICATION_PROBES}
            ):
                raise IterationContractError(
                    f"{path}.falsification_probe is invalid"
                )
            falsification_probe = raw_probe
        if chain_key not in allowed_chains:
            matching_prefix = any(
                chain[:first_empty] == values[:first_empty]
                for chain in allowed_chains
            ) if not require_binding_role else False
            if not matching_prefix:
                raise IterationContractError(f"{path} evidence binding mismatch")
        if require_complete_chain:
            case_key = values[-2]
            tc_id = values[-1]
            obligation_id = values[-3]
            if case_key not in expected or expected[case_key][0] != tc_id:
                raise IterationContractError(f"{path} case binding mismatch")
            if binding_role == "primary" and expected[case_key][1] != obligation_id:
                raise IterationContractError(f"{path} primary case binding mismatch")
        return falsification_probe

    for index, raw in enumerate(source_findings):
        validate_finding(
            raw,
            path=f"$.source_projection_findings[{index}]",
            allowed_types=_SOURCE_PROJECTION_FINDING_TYPES,
            require_complete_chain=False,
            allowed_chains=primary_chains | supporting_chains,
        )
    probe_finding_bindings: set[tuple[str, str, str, str, str]] = set()
    same_chain_probe_finding_bindings: set[tuple[str, str, str, str]] = set()
    case_probe_finding_bindings: set[tuple[str, str]] = set()
    for index, raw in enumerate(test_findings):
        falsification_probe = validate_finding(
            raw,
            path=f"$.test_case_findings[{index}]",
            allowed_types=_TEST_CASE_FINDING_TYPES,
            require_complete_chain=True,
            allowed_chains=primary_test_chains | design_support_chains,
            require_binding_role=True,
            require_falsification_probe=True,
        )
        if isinstance(raw, Mapping) and falsification_probe:
            case_key = str(raw.get("case_key"))
            tc_id = str(raw.get("tc_id"))
            finding_binding = (
                case_key,
                tc_id,
                falsification_probe,
                str(raw.get("binding_role")),
                str(raw.get("obligation_id")),
            )
            same_chain_binding = (
                case_key,
                tc_id,
                str(raw.get("binding_role")),
                str(raw.get("obligation_id")),
            )
            probe_result = falsification_by_case[case_key][falsification_probe]
            if probe_result[0] != "finding":
                raise IterationContractError(
                    f"reviewer test_case_finding for {case_key}/"
                    f"{falsification_probe} has no matching falsification outcome"
                )
            probe_finding_bindings.add(finding_binding)
            same_chain_probe_finding_bindings.add(same_chain_binding)
            case_probe_finding_bindings.add((case_key, tc_id))

    for case_key, probe_results in falsification_by_case.items():
        tc_id = expected[case_key][0]
        for probe, (
            outcome,
            _trigger_or_step,
            _oracle,
            binding_role,
            probe_obligation_id,
            _binding_item_index,
        ) in probe_results.items():
            exact_binding = (
                case_key,
                tc_id,
                probe,
                binding_role,
                probe_obligation_id,
            )
            same_chain_binding = (
                case_key,
                tc_id,
                binding_role,
                probe_obligation_id,
            )
            if (
                outcome == "finding"
                and exact_binding not in probe_finding_bindings
                and same_chain_binding not in same_chain_probe_finding_bindings
                and (case_key, tc_id) not in case_probe_finding_bindings
            ):
                raise IterationContractError(
                    f"reviewer falsification finding for {case_key}/{probe} "
                    "has no bound test_case_finding"
                )
            if outcome != "finding" and exact_binding in probe_finding_bindings:
                raise IterationContractError(
                    f"reviewer test_case_finding for {case_key}/{probe} "
                    "has no matching falsification outcome"
                )

    accepted = (
        decision == "accepted"
        and all_required_statuses
        and not source_findings
        and not test_findings
    )
    if decision == "accepted" and not accepted:
        raise IterationContractError(
            "accepted review requires every case's required status and zero findings"
        )
    if (
        decision == "changes-required"
        and all_required_statuses
        and not source_findings
        and not test_findings
    ):
        raise IterationContractError("changes-required review has no bound reason")
    return accepted, decision


def validate_reviewer_response(
    response: Mapping[str, Any],
    *,
    graph: CoverageGraph,
    draft_sha256: str,
    reviewer_request: Mapping[str, Any] | None = None,
    allow_legacy_unrecorded_falsification: bool = False,
) -> tuple[bool, str]:
    if reviewer_request is not None and reviewer_request.get("schema_version") == 2:
        return _validate_reviewer_response_v2(
            response,
            graph=graph,
            draft_sha256=draft_sha256,
            reviewer_request=reviewer_request,
            allow_legacy_unrecorded_falsification=(
                allow_legacy_unrecorded_falsification
            ),
        )
    root = _object(
        response,
        "$",
        {
            "schema_version",
            "graph_digest",
            "draft_sha256",
            "decision",
            "case_results",
            "findings",
            "summary",
        },
    )
    if (
        root["schema_version"] != 1
        or root["graph_digest"] != graph.digest
        or root["draft_sha256"] != draft_sha256
    ):
        raise IterationContractError("reviewer response is not bound to this draft")
    decision = _one_line(root["decision"], "$.decision")
    if decision not in _DECISIONS:
        raise IterationContractError(f"unsupported reviewer decision: {decision}")
    _one_line(root["summary"], "$.summary")
    expected: dict[str, tuple[str, str, str]] = {}
    obligations = {item.obligation_id: item for item in graph.obligations}
    for case in graph.cases:
        obligation_id = case.obligation_ids[0]
        if obligation_id not in obligations:  # pragma: no cover
            raise IterationContractError(f"graph case references unknown {obligation_id}")
        required_status = (
            "calibration-pending"
            if case.status == "candidate-ui-calibration"
            else "covered"
        )
        expected[case.case_key] = (case.tc_id, obligation_id, required_status)
    raw_results = root["case_results"]
    raw_findings = root["findings"]
    if not isinstance(raw_results, list) or not isinstance(raw_findings, list):
        raise IterationContractError("reviewer results and findings must be arrays")
    seen: set[str] = set()
    all_required_statuses = True
    for index, raw in enumerate(raw_results):
        item = _object(
            raw,
            f"$.case_results[{index}]",
            {"case_key", "tc_id", "obligation_id", "status", "comment"},
        )
        case_key = _one_line(item["case_key"], f"$.case_results[{index}].case_key")
        if case_key not in expected or case_key in seen:
            raise IterationContractError(
                f"reviewer has unknown or duplicate case_key: {case_key}"
            )
        seen.add(case_key)
        tc_id, obligation_id, required_status = expected[case_key]
        if item["tc_id"] != tc_id or item["obligation_id"] != obligation_id:
            raise IterationContractError(f"reviewer binding mismatch for {case_key}")
        status = _one_line(item["status"], f"$.case_results[{index}].status")
        if status not in _RESULT_STATUSES:
            raise IterationContractError(f"unsupported reviewer result status: {status}")
        if not isinstance(item["comment"], str):
            raise IterationContractError(f"reviewer comment for {case_key} must be text")
        all_required_statuses = all_required_statuses and status == required_status
    if seen != set(expected):
        raise IterationContractError(
            "reviewer omitted cases: " + ", ".join(sorted(set(expected) - seen))
        )
    for index, raw in enumerate(raw_findings):
        item = _object(
            raw,
            f"$.findings[{index}]",
            {"severity", "case_key", "tc_id", "obligation_id", "message"},
        )
        case_key = _one_line(item["case_key"], f"$.findings[{index}].case_key")
        if case_key not in expected:
            raise IterationContractError(f"finding references unknown case {case_key}")
        tc_id, obligation_id, _ = expected[case_key]
        if item["tc_id"] != tc_id or item["obligation_id"] != obligation_id:
            raise IterationContractError(f"finding binding mismatch for {case_key}")
        if item["severity"] not in {"error", "warning"}:
            raise IterationContractError(f"finding {index} has invalid severity")
        _one_line(item["message"], f"$.findings[{index}].message")
    accepted = (
        decision == "accepted"
        and all_required_statuses
        and not raw_findings
    )
    if decision == "accepted" and not accepted:
        raise IterationContractError(
            "accepted review requires every executable case covered, every "
            "calibration candidate calibration-pending, and zero findings"
        )
    if decision == "changes-required" and all_required_statuses and not raw_findings:
        raise IterationContractError("changes-required review has no bound reason")
    return accepted, decision


def request_sha256(request: Mapping[str, Any]) -> str:
    return _canonical_digest(request)
