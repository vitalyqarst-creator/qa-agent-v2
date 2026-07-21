from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from test_case_agent.review_cycle.prepared_package import PreparedObligationSet
from test_case_agent.review_cycle.source_assertions import (
    EmbeddedSourceAssertionContract,
    SourceAssertionManifest,
)


WRITER_SOURCE_PROJECTION_MAX_BYTES = 256 * 1024
REVIEWER_SOURCE_PROJECTION_MAX_BYTES = 256 * 1024
TRACEABILITY_VALUE_RE = re.compile(
    r"(?im)^[^\S\r\n]*(?:[-+*][^\S\r\n]+)?"
    r"\*\*(?:Трассировка|Traceability):\*\*[^\S\r\n]*(.+)$"
)
TRACE_ID_RE = re.compile(r"\b(?:OBL|ATOM|SRC|DICT|GAP)-[A-Za-z0-9._-]+\b")
REQUIREMENT_CODE_RE = re.compile(
    r"\b(?:BSR|GSR|DIT)(?:\s+|-)[A-Za-z0-9][A-Za-z0-9._/-]*\b"
)
TC_HEADING_RE = re.compile(r"(?m)^##\s+(TC-[A-Za-z0-9][A-Za-z0-9_.-]*)\s*$")


class SourceProjectionError(ValueError):
    pass


@dataclass(frozen=True)
class CompactSourceProjection:
    rendered: str
    report: Mapping[str, Any]
    selected_obligation_ids: tuple[str, ...]
    selected_assertion_ids: tuple[str, ...]


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_receipt_sha256(contract: EmbeddedSourceAssertionContract) -> str:
    return hashlib.sha256(
        _canonical_json(contract.review_receipt.to_dict()).encode("utf-8")
    ).hexdigest()


def source_contract_digest_summary(
    contract: EmbeddedSourceAssertionContract,
) -> dict[str, str]:
    return {
        "manifest_digest": contract.manifest.digest,
        "review_receipt_sha256": canonical_receipt_sha256(contract),
        "review_decision": contract.review_receipt.decision,
    }


def _test_case_sections(draft_text: str) -> tuple[tuple[str, str], ...]:
    matches = tuple(TC_HEADING_RE.finditer(draft_text))
    return tuple(
        (
            match.group(1),
            draft_text[
                match.start() : (
                    matches[index + 1].start()
                    if index + 1 < len(matches)
                    else len(draft_text)
                )
            ],
        )
        for index, match in enumerate(matches)
    )


def select_draft_testable_obligation_ids(
    *,
    draft_text: str,
    obligations: PreparedObligationSet,
    manifest: SourceAssertionManifest,
) -> tuple[str, ...]:
    """Return known testable OBL ids actually named in TC traceability fields."""

    sections = _test_case_sections(draft_text)
    if not sections:
        raise SourceProjectionError(
            "reviewer source projection cannot bind a draft without TC sections"
        )
    known_trace_ids: set[str] = set()
    for item in obligations.obligations:
        known_trace_ids.add(item.obligation_id)
        known_trace_ids.add(item.traceability_atom_id)
        known_trace_ids.update(item.source_refs)
        known_trace_ids.update(item.dictionary_refs)
        known_trace_ids.update(item.constraint_gap_ids)
        if item.gap_id:
            known_trace_ids.add(item.gap_id)
    known_trace_ids.update(gap.gap_id for gap in obligations.coverage_gaps)
    known_trace_ids.update(row.source_row_id for row in manifest.source_rows)
    known_requirement_codes = {
        code
        for assertion in manifest.assertions
        for code in assertion.requirement_codes
    }
    known_requirement_codes.update(
        reference
        for item in obligations.obligations
        for reference in item.source_refs
        if REQUIREMENT_CODE_RE.fullmatch(reference)
    )
    testable_ids = {
        item.obligation_id
        for item in obligations.obligations
        if item.coverage_status == "testable"
    }
    traced_ids: set[str] = set()
    for test_case_id, section in sections:
        trace_values = TRACEABILITY_VALUE_RE.findall(section)
        if not trace_values:
            raise SourceProjectionError(
                f"reviewer source projection TC {test_case_id} has no traceability field"
            )
        section_trace_ids = {
            trace_id
            for trace_value in trace_values
            for trace_id in TRACE_ID_RE.findall(trace_value)
        }
        section_codes = {
            code
            for trace_value in trace_values
            for code in REQUIREMENT_CODE_RE.findall(trace_value)
        }
        unknown_trace_ids = sorted(section_trace_ids - known_trace_ids)
        if unknown_trace_ids:
            raise SourceProjectionError(
                f"reviewer source projection TC {test_case_id} found unknown draft "
                "trace IDs: " + ", ".join(unknown_trace_ids)
            )
        unknown_codes = sorted(section_codes - known_requirement_codes)
        if unknown_codes:
            raise SourceProjectionError(
                f"reviewer source projection TC {test_case_id} found unknown "
                "requirement codes: " + ", ".join(unknown_codes)
            )
        section_testable_ids = section_trace_ids & testable_ids
        if not section_testable_ids:
            raise SourceProjectionError(
                f"reviewer source projection TC {test_case_id} has no known "
                "testable OBL trace ID"
            )
        traced_ids.update(section_trace_ids)

    selected = tuple(
        item.obligation_id
        for item in obligations.obligations
        if item.coverage_status == "testable" and item.obligation_id in traced_ids
    )
    return selected


def build_compact_source_projection(
    *,
    role: str,
    contract: EmbeddedSourceAssertionContract,
    obligations: PreparedObligationSet,
    selected_obligation_ids: Sequence[str],
    source_evidence_path: str,
    source_evidence_sha256: str,
    source_evidence_bytes: int,
    atomic_obligations_path: str,
    atomic_obligations_sha256: str,
    reviewer_dimension_source_refs: Mapping[str, Sequence[str]] | None = None,
    include_source_row_siblings: bool = False,
    writer_max_bytes: int = WRITER_SOURCE_PROJECTION_MAX_BYTES,
    reviewer_max_bytes: int = REVIEWER_SOURCE_PROJECTION_MAX_BYTES,
) -> CompactSourceProjection:
    """Build a deterministic digest-bound role projection from accepted semantics."""

    if role not in {"writer", "reviewer"}:
        raise SourceProjectionError(f"unsupported compact source projection role: {role}")
    manifest = contract.manifest
    receipt = contract.review_receipt
    if receipt.decision != "accepted" or receipt.manifest_digest != manifest.digest:
        raise SourceProjectionError(
            "compact source projection requires an accepted receipt bound to the "
            "current manifest digest"
        )
    selected_ids = tuple(selected_obligation_ids)
    if len(selected_ids) != len(set(selected_ids)):
        raise SourceProjectionError(
            "compact source projection obligation selection contains duplicates"
        )

    obligations_by_id = {item.obligation_id: item for item in obligations.obligations}
    unknown_ids = sorted(set(selected_ids) - set(obligations_by_id))
    if unknown_ids:
        raise SourceProjectionError(
            "compact source projection references unknown obligations: "
            + ", ".join(unknown_ids)
        )
    non_testable_ids = sorted(
        obligation_id
        for obligation_id in selected_ids
        if obligations_by_id[obligation_id].coverage_status != "testable"
    )
    if non_testable_ids:
        raise SourceProjectionError(
            "compact source projection cannot claim source assertions for "
            "non-testable obligations: " + ", ".join(non_testable_ids)
        )

    assertion_by_obligation_id: dict[str, Any] = {}
    for assertion in manifest.assertions:
        for obligation_id in assertion.obligation_ids:
            if obligation_id in assertion_by_obligation_id:
                raise SourceProjectionError(
                    "compact source projection found duplicate source assertion "
                    f"binding for {obligation_id}"
                )
            assertion_by_obligation_id[obligation_id] = assertion
    missing_assertions = sorted(set(selected_ids) - set(assertion_by_obligation_id))
    if missing_assertions:
        raise SourceProjectionError(
            "compact source projection is missing accepted source assertions for: "
            + ", ".join(missing_assertions)
        )

    selected_id_set = set(selected_ids)
    directly_selected_assertions = tuple(
        assertion
        for assertion in manifest.assertions
        if selected_id_set.intersection(assertion.obligation_ids)
    )
    selected_source_row_ids = {
        assertion.source_row_id for assertion in directly_selected_assertions
    }
    selected_assertions = (
        tuple(
            assertion
            for assertion in manifest.assertions
            if assertion.source_row_id in selected_source_row_ids
        )
        if include_source_row_siblings
        else directly_selected_assertions
    )
    selected_assertion_ids = tuple(
        assertion.assertion_id for assertion in selected_assertions
    )
    review_by_assertion_id = {
        item.assertion_id: item for item in receipt.assertion_reviews
    }
    missing_reviews = sorted(set(selected_assertion_ids) - set(review_by_assertion_id))
    if missing_reviews:
        raise SourceProjectionError(
            "compact source projection is missing accepted review rows for: "
            + ", ".join(missing_reviews)
        )
    unverified_assertions = sorted(
        assertion_id
        for assertion_id in selected_assertion_ids
        if review_by_assertion_id[assertion_id].verdict != "verified"
    )
    if unverified_assertions:
        raise SourceProjectionError(
            "compact source projection cannot transport unverified assertions: "
            + ", ".join(unverified_assertions)
        )

    assertion_payloads: list[dict[str, Any]] = []
    selected_clarification_ids: set[str] = set()
    for assertion in selected_assertions:
        bound_obligations = tuple(
            obligations_by_id[obligation_id]
            for obligation_id in assertion.obligation_ids
            if obligation_id in selected_id_set
        )
        assertion_payload: dict[str, Any] = {
                "assertion_id": assertion.assertion_id,
                "source_row_id": assertion.source_row_id,
                **(
                    {"exact_source_text": assertion.exact_source_text}
                    if role == "writer"
                    and any(
                        item.calibration_status == "ui-calibration-required"
                        for item in bound_obligations
                    )
                    else {}
                ),
                "canonical_statement": assertion.canonical_statement,
                "polarity": assertion.polarity,
                "condition_clauses": list(assertion.condition_clauses),
                "action_clauses": list(assertion.action_clauses),
                "oracle_clauses": list(assertion.oracle_clauses),
                "requirement_codes": list(assertion.requirement_codes),
                "atom_id": assertion.atom_id,
                "obligation_bindings": [
                    {
                        "obligation_id": item.obligation_id,
                    }
                    for item in bound_obligations
                ],
                "primary_gap_id": assertion.primary_gap_id,
                "clarification_clause_bindings": [
                    item.to_dict()
                    for item in assertion.clarification_clause_bindings
                ],
            }
        if role == "writer":
            assertion_payload.update(
                {
                    "semantic_disposition": assertion.semantic_disposition,
                    "execution_readiness": assertion.execution_readiness,
                    "execution_readiness_rationale": (
                        assertion.execution_readiness_rationale
                    ),
                    "risk": assertion.risk,
                    "obligation_bindings": [
                        {
                            "obligation_id": item.obligation_id,
                            "dictionary_refs": list(item.dictionary_refs),
                            "dictionary_requirements": [
                                {
                                    "dictionary_id": requirement.dictionary_id,
                                    "coverage_mode": requirement.coverage_mode,
                                    "required_value_count": len(
                                        requirement.required_values
                                    ),
                                    "fixture_value_count": len(
                                        requirement.fixture_values
                                    ),
                                }
                                for requirement in item.dictionary_requirements
                            ],
                            "gap_id": item.gap_id or None,
                            "constraint_gap_ids": list(item.constraint_gap_ids),
                            "calibration_status": item.calibration_status,
                        }
                        for item in bound_obligations
                    ],
                    "disposition_rationale": (
                        assertion.disposition_rationale or None
                    ),
                }
            )
        assertion_payloads.append(assertion_payload)
        selected_clarification_ids.update(
            item.clarification_id
            for item in assertion.clarification_clause_bindings
        )

    clarification_by_id = {
        item.clarification_id: item for item in manifest.clarifications
    }
    missing_clarifications = sorted(
        selected_clarification_ids - set(clarification_by_id)
    )
    if missing_clarifications:
        raise SourceProjectionError(
            "compact source projection is missing registered approved clarifications: "
            + ", ".join(missing_clarifications)
        )
    clarification_payloads = [
        {
            "clarification_id": clarification.clarification_id,
            "gap_id": clarification.gap_id,
            "scope_slug": clarification.scope_slug,
            "requirement_codes": list(clarification.requirement_codes),
            "authority": clarification.authority,
            "response_status": clarification.response_status,
            "response_type": clarification.response_type,
            "answered_at": clarification.answered_at,
            "exact_answer": clarification.exact_answer,
            "exact_answer_sha256": clarification.exact_answer_sha256,
            "evidence_source": {
                "path": clarification.evidence_source_path,
                "sha256": clarification.evidence_source_sha256,
                "role": "approved-clarification",
            },
        }
        for clarification in manifest.clarifications
        if clarification.clarification_id in selected_clarification_ids
    ]
    if len(clarification_payloads) != len(selected_clarification_ids):
        raise SourceProjectionError(
            "compact source projection clarification selection is incomplete"
        )

    receipt_sha256 = canonical_receipt_sha256(contract)
    projection: dict[str, Any] = {
        "contract": "prepared-digest-bound-source-evidence-projection-v1",
        "role": role,
        "source_evidence_artifact": {
            "path": source_evidence_path,
            "sha256": source_evidence_sha256,
        },
        "atomic_obligations_artifact": {
            "path": atomic_obligations_path,
            "sha256": atomic_obligations_sha256,
        },
        "accepted_source_contract": {
            "scope_slug": manifest.scope_slug,
            "manifest_digest": manifest.digest,
            "review_receipt_sha256": receipt_sha256,
            "review_receipt_version": receipt.version,
            "review_decision": receipt.decision,
            "source_row_extraction_spec_digest": (
                manifest.source_row_extraction_spec_digest
            ),
            "source_row_baseline_digest": manifest.source_row_baseline_digest,
            "source_row_candidate_count": manifest.source_row_candidate_count,
        },
        "selection": {
            "obligation_ids": list(selected_ids),
            "assertion_ids": list(selected_assertion_ids),
        },
        "assertions": assertion_payloads,
        "approved_clarifications": clarification_payloads,
    }
    if role == "reviewer":
        projection["reviewer_dimension_source_bindings"] = {
            "contract": "reviewer-dimension-source-bindings-v1",
            "bindings": {
                dimension: list(source_refs)
                for dimension, source_refs in sorted(
                    (reviewer_dimension_source_refs or {}).items()
                )
            },
        }
    projection_sha256 = hashlib.sha256(
        _canonical_json(projection).encode("utf-8")
    ).hexdigest()
    projection["projection_sha256"] = projection_sha256
    rendered = _canonical_json(projection)
    projected_bytes = len(rendered.encode("utf-8"))
    limit_bytes = writer_max_bytes if role == "writer" else reviewer_max_bytes
    report = {
        "passed": projected_bytes <= limit_bytes,
        "validator": "prepared-digest-bound-source-evidence-projection-v1",
        "error_code": (
            ""
            if projected_bytes <= limit_bytes
            else "prepared-source-evidence-projection-budget-exceeded"
        ),
        "role": role,
        "source_evidence_artifact_sha256": source_evidence_sha256,
        "manifest_digest": manifest.digest,
        "review_receipt_sha256": receipt_sha256,
        "projection_sha256": projection_sha256,
        "selected_obligation_count": len(selected_ids),
        "selected_assertion_count": len(selected_assertions),
        "manifest_assertion_count": len(manifest.assertions),
        "selected_clarification_count": len(clarification_payloads),
        "manifest_source_row_count": len(manifest.source_rows),
        "review_note_count_omitted": len(receipt.assertion_reviews),
        "original_source_evidence_bytes": source_evidence_bytes,
        "projected_bytes": projected_bytes,
        "bytes_removed": source_evidence_bytes - projected_bytes,
        "limit_bytes": limit_bytes,
    }
    return CompactSourceProjection(
        rendered=rendered,
        report=report,
        selected_obligation_ids=selected_ids,
        selected_assertion_ids=selected_assertion_ids,
    )


def render_reviewer_obligation_semantic_projection(
    *,
    obligations: PreparedObligationSet,
    artifact_path: str,
    artifact_sha256: str,
    source_contract_summary: Mapping[str, str] | None,
    draft_referenced_testable_obligation_ids: Sequence[str],
    dictionary_evidence: Sequence[Mapping[str, Any]],
) -> str:
    payload = {
        "artifact": artifact_path,
        "artifact_sha256": artifact_sha256,
        "obligation_count": len(obligations.obligations),
        "semantic_evidence_source": "selected-source-evidence",
        "source_contract_digest_summary": source_contract_summary,
        "draft_referenced_testable_obligation_ids": list(
            draft_referenced_testable_obligation_ids
        ),
        "coverage_gaps": [item.to_dict() for item in obligations.coverage_gaps],
        "dictionary_evidence": list(dictionary_evidence),
        "obligations": [
            {
                "obligation_id": item.obligation_id,
                "atom_id": item.traceability_atom_id,
                "coverage_status": item.coverage_status,
                "planned_test_case_id": item.planned_test_case_id,
                "source_refs": list(item.source_refs),
                "atomic_statement": item.atomic_statement,
                "observable_oracle": item.observable_oracle,
                "test_intent": item.test_intent,
                "execution_semantics": item.execution_semantics,
                "state_change": (
                    item.state_change.to_dict()
                    if item.state_change is not None
                    else None
                ),
                "dictionary_refs": list(item.dictionary_refs),
                "dictionary_requirements": [
                    requirement.to_dict(include_fixture_contract=True)
                    for requirement in item.dictionary_requirements
                ],
                "calibration_status": item.calibration_status,
                "gap_id": item.gap_id,
                "constraint_gap_ids": list(item.constraint_gap_ids),
                "notes": item.notes,
            }
            for item in obligations.obligations
        ],
    }
    return _canonical_json(payload)
