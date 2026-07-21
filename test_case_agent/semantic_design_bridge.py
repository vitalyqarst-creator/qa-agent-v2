from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from test_case_agent.bounded_scope_boundary import (
    BoundedScopeBoundaryError,
    bare_requirement_codes,
    external_dynamic_dictionary_bindings,
    normalize_entity,
    validate_boundary_decision_v2,
    validate_source_cache_binding,
)
from test_case_agent.review_cycle.source_assertions import (
    ApprovedClarification,
    ClarificationClauseBinding,
    SourceAssertionContractError,
    contains_token_bounded_source_fragment,
    normalize_exact_source_text,
)


BRIDGE_CONTRACT_VERSION = 1
BRIDGE_CONTRACT_NAME = "scope-v2-to-semantic-design-v1"
SEMANTIC_DESIGN_VERSION = 4
SEMANTIC_DESIGN_CONTRACT = "semantic-design-bridge-v2"
APPLICABILITY_DIMENSIONS = (
    "conditional-visibility",
    "scenario-use-case",
    "traceability",
    "accessibility-ui",
    "role-permission",
    "status-lifecycle",
    "equivalence",
    "boundary",
    "table-list",
    "integration",
    "async",
    "persistence",
    "security",
)
APPROVED_AUTHORITY_TYPES = {
    "user": "user-confirmed",
    "analyst": "analyst-confirmed",
    "product-owner": "product-confirmed",
}
EXECUTABLE_ORACLE_STATUSES = (
    "source-backed",
    "common-standard-backed",
    "analyst-confirmed",
    "observed-ui-backed",
)
ORACLE_STATUS_VALUES = (
    *EXECUTABLE_ORACLE_STATUSES,
    "ui-calibration-required",
    "gap-required",
    "clarification-required",
    "not-applicable",
)
ORACLE_STATUS_ALIASES = {
    "source-backed-executable": "source-backed",
}
UNKNOWN_ORACLE_SOURCE_SENTINELS = {
    "not_found": "not_found",
    "not_observed": "not_observed",
    "none_found": "none_found",
    "unknown_ui_reaction": "unknown_ui_reaction",
    "не_найден": "не_найден",
    "не_наблюдался": "не_наблюдался",
}


def _is_conditional_requiredness_signal(signal: Mapping[str, Any]) -> bool:
    source = str(signal.get("requiredness_source", "")).casefold()
    return re.search(r"(?:^|\W)(?:если|if|when)(?:\W|$)", source) is not None
CLARIFICATION_COLUMNS = (
    "clarification_id",
    "gap_id",
    "scope_slug",
    "requirement_codes",
    "related_ft_reference",
    "question",
    "needed_for",
    "blocking",
    "requested_from",
    "authority",
    "user_response",
    "response_status",
    "response_type",
    "updated_at",
)


class SemanticDesignBridgeError(ValueError):
    pass


def canonical_payload_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def prepared_context_sha256(context: Mapping[str, Any]) -> str:
    try:
        validate_source_cache_binding(context, required=True)
    except BoundedScopeBoundaryError as exc:
        raise SemanticDesignBridgeError(str(exc)) from exc
    source_cache = context.get("source_cache")
    if not isinstance(source_cache, Mapping):
        raise SemanticDesignBridgeError("context.source_cache is required")
    digests = source_cache.get("component_digests")
    if not isinstance(digests, Mapping):
        raise SemanticDesignBridgeError(
            "context.source_cache.component_digests is required"
        )
    digest = digests.get("bounded_context_sha256")
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise SemanticDesignBridgeError(
            "context bounded_context_sha256 must be lowercase SHA-256"
        )
    return digest


def _redundant_pdf_parity_index(
    evidence: Sequence[Any],
    *,
    requirement_code: str,
    source_row_id: str,
) -> int | None:
    """Return one provably redundant PDF-parity binding, otherwise fail closed."""

    matching = [
        (index, item)
        for index, item in enumerate(evidence)
        if isinstance(item, Mapping)
        and str(item.get("requirement_code", "")) == requirement_code
    ]
    if len(matching) != 2 or not requirement_code or not source_row_id:
        return None
    xhtml = [item for item in matching if item[1].get("provenance_role") == "xhtml-row"]
    pdf = [item for item in matching if item[1].get("provenance_role") == "pdf-parity"]
    if len(xhtml) != 1 or len(pdf) != 1:
        return None
    _, xhtml_binding = xhtml[0]
    pdf_index, pdf_binding = pdf[0]
    if (
        str(xhtml_binding.get("source_row_id", "")) != source_row_id
        or str(pdf_binding.get("source_row_id", "")) != source_row_id
        or pdf_binding.get("exact_source_fragment") != "none_required"
    ):
        return None
    exact_source_fragment = xhtml_binding.get("exact_source_fragment")
    if not isinstance(exact_source_fragment, str):
        return None
    if not contains_token_bounded_source_fragment(
        normalize_exact_source_text(exact_source_fragment),
        normalize_exact_source_text(requirement_code),
    ):
        return None
    return pdf_index


def _canonical_repeated_requirement_code_evidence_span(
    binding: Mapping[str, Any],
    source_row: Mapping[str, Any],
) -> str | None:
    """Recover one literal same-requirement span from a duplicated code prefix.

    Models occasionally prefix a continuation sentence with the owning requirement
    code even though the code occurs only once at the start of the source rule.  A
    bare removal would make the evidence fail the code-token contract, so widen the
    evidence to the exact source span from that unique code occurrence through the
    uniquely matching continuation.  Ambiguous rows and spans crossing another
    declared requirement code remain blocking.
    """

    if binding.get("provenance_role") != "xhtml-row":
        return None
    requirement_code = str(binding.get("requirement_code", "")).strip()
    fragment = str(binding.get("exact_source_fragment", "")).strip()
    source_text = str(source_row.get("bounded_source_text", ""))
    if not requirement_code or not fragment or not source_text or fragment in source_text:
        return None
    prefixed = re.fullmatch(
        rf"{re.escape(requirement_code)}(?:\s*[.:;\-\u2013\u2014]\s*|\s+)(?P<body>.+)",
        fragment,
        flags=re.DOTALL,
    )
    if prefixed is None:
        return None
    body = prefixed.group("body").strip()
    if not body:
        return None
    code_pattern = re.compile(rf"(?<!\w){re.escape(requirement_code)}(?!\w)")
    if source_text.count(body) == 1:
        body_start = source_text.find(body)
        body_end = body_start + len(body)
        preceding_codes = [
            match
            for match in code_pattern.finditer(source_text)
            if match.end() <= body_start
        ]
        if len(preceding_codes) != 1:
            return None
        code_start = preceding_codes[0].start()
        canonical_span = source_text[code_start:body_end]
    else:
        code_matches = list(code_pattern.finditer(source_text))
        if len(code_matches) != 1:
            return None
        code_start = code_matches[0].start()
        region_end = len(source_text)
        for other_code in map(str, source_row.get("requirement_codes_hint", [])):
            if not other_code or other_code == requirement_code:
                continue
            other_match = re.search(
                rf"(?<!\w){re.escape(other_code)}(?!\w)",
                source_text[code_matches[0].end() :],
            )
            if other_match is not None:
                region_end = min(
                    region_end,
                    code_matches[0].end() + other_match.start(),
                )
        source_region = source_text[code_start:region_end].rstrip()
        common_prefix_length = 0
        for source_character, fragment_character in zip(source_region, fragment):
            if source_character != fragment_character:
                break
            common_prefix_length += 1
        if common_prefix_length < len(requirement_code) + 2:
            return None
        remainder = fragment[common_prefix_length:]
        if len(remainder) < 24:
            return None
        remainder_start = source_region.find(remainder, common_prefix_length)
        if (
            remainder_start <= common_prefix_length
            or source_region.find(remainder, remainder_start + 1) >= 0
            or not source_region[common_prefix_length:remainder_start].strip()
        ):
            return None
        canonical_span = source_region[: remainder_start + len(remainder)]
    for other_code in map(str, source_row.get("requirement_codes_hint", [])):
        if not other_code or other_code == requirement_code:
            continue
        if re.search(rf"(?<!\w){re.escape(other_code)}(?!\w)", canonical_span):
            return None
    return canonical_span


def _repeated_requirement_code_evidence_span_projections(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows_by_id = {
        str(row.get("source_row_id", "")): row
        for row in context.get("source_rows", [])
        if isinstance(row, Mapping)
    }
    projections: list[dict[str, Any]] = []
    for source_index, source_design in enumerate(payload.get("source_designs", [])):
        if not isinstance(source_design, Mapping):
            continue
        assertions = source_design.get("assertions", [])
        if not isinstance(assertions, list):
            continue
        for assertion_index, assertion in enumerate(assertions):
            if not isinstance(assertion, Mapping):
                continue
            evidence = assertion.get("requirement_code_evidence", [])
            if not isinstance(evidence, list):
                continue
            for binding_index, binding in enumerate(evidence):
                if not isinstance(binding, Mapping):
                    continue
                source_row_id = str(binding.get("source_row_id", ""))
                source_row = rows_by_id.get(source_row_id)
                if source_row is None:
                    continue
                canonical_span = _canonical_repeated_requirement_code_evidence_span(
                    binding,
                    source_row,
                )
                if canonical_span is None:
                    continue
                projections.append(
                    {
                        "source_index": source_index,
                        "assertion_index": assertion_index,
                        "binding_index": binding_index,
                        "source_row_id": source_row_id,
                        "assertion_id": str(assertion.get("assertion_id", "")),
                        "requirement_code": str(binding.get("requirement_code", "")),
                        "canonical_span": canonical_span,
                        "previous_value_sha256": hashlib.sha256(
                            str(binding.get("exact_source_fragment", "")).encode("utf-8")
                        ).hexdigest(),
                    }
                )
    return projections


def _provable_dependency_overlink_projection(
    payload: Mapping[str, Any],
    binding: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Return a safe projection when only literal-evidence-free links are extra."""

    linked_assertion_ids = binding.get("linked_assertion_ids")
    linked_atom_ids = binding.get("linked_atom_ids")
    linked_obligation_ids = binding.get("linked_obligation_ids")
    fragments = list(map(str, binding.get("exact_source_fragments", [])))
    source_rows = set(map(str, binding.get("source_row_ids", [])))
    dependency_rows = {
        *source_rows,
        *map(str, binding.get("target_source_row_ids", [])),
    }
    if not (
        binding.get("semantic_disposition") == "bound"
        and isinstance(linked_assertion_ids, list)
        and isinstance(linked_atom_ids, list)
        and isinstance(linked_obligation_ids, list)
        and linked_assertion_ids
        and fragments
        and source_rows
    ):
        return None
    assertions: dict[str, Mapping[str, Any]] = {}
    owner_rows: dict[str, str] = {}
    source_designs = payload.get("source_designs", [])
    if not isinstance(source_designs, list):
        return None
    for source_design in source_designs:
        if not isinstance(source_design, Mapping):
            continue
        owner_row = str(source_design.get("source_row_id", ""))
        for assertion in source_design.get("assertions", []):
            if not isinstance(assertion, Mapping):
                continue
            assertion_id = str(assertion.get("assertion_id", ""))
            assertions[assertion_id] = assertion
            owner_rows[assertion_id] = owner_row
    linked = list(map(str, linked_assertion_ids))
    if any(assertion_id not in assertions for assertion_id in linked):
        return None
    expected_atoms = [str(assertions[item].get("atom_id", "")) for item in linked]
    expected_obligations = [
        str(obligation_id)
        for item in linked
        for obligation_id in assertions[item].get("obligation_ids", [])
    ]
    if list(map(str, linked_atom_ids)) != expected_atoms or list(
        map(str, linked_obligation_ids)
    ) != expected_obligations:
        return None

    retained: list[str] = []
    dropped: list[str] = []
    covered_fragments: set[str] = set()
    covered_rows: set[str] = set()
    for assertion_id in linked:
        assertion = assertions[assertion_id]
        supporting_rows = {
            str(item.get("source_row_id", ""))
            for item in assertion.get("supporting_source_bindings", [])
            if isinstance(item, Mapping)
        }
        relation_rows = {owner_rows[assertion_id], *supporting_rows}
        matched_fragments = {
            fragment
            for evidence_row_id, evidence_fragment in _assertion_literal_evidence(
                assertion
            )
            if evidence_row_id in source_rows
            for fragment in fragments
            if fragment in evidence_fragment
        }
        if dependency_rows.intersection(relation_rows) and matched_fragments:
            retained.append(assertion_id)
            covered_fragments.update(matched_fragments)
            covered_rows.update(dependency_rows.intersection(relation_rows))
        else:
            dropped.append(assertion_id)
    if not dropped or not retained or covered_fragments != set(fragments):
        return None
    target_rows = set(map(str, binding.get("target_source_row_ids", [])))
    if target_rows and not target_rows.issubset(covered_rows):
        return None
    return {
        "dropped_assertion_ids": dropped,
        "linked_assertion_ids": retained,
        "linked_atom_ids": [str(assertions[item].get("atom_id", "")) for item in retained],
        "linked_obligation_ids": [
            str(obligation_id)
            for item in retained
            for obligation_id in assertions[item].get("obligation_ids", [])
        ],
    }


def _scope_excluded_na_link_projection(
    payload: Mapping[str, Any],
    binding: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Clear only a fully proved N/A ASSERT/ATOM link from an excluded dependency."""

    linked_assertion_ids = binding.get("linked_assertion_ids")
    linked_atom_ids = binding.get("linked_atom_ids")
    linked_obligation_ids = binding.get("linked_obligation_ids")
    dependency_name = str(binding.get("name", "")).strip().casefold()
    source_rows = set(map(str, binding.get("source_row_ids", [])))
    exact_fragments = [
        str(fragment).strip().casefold()
        for fragment in binding.get("exact_source_fragments", [])
        if str(fragment).strip()
    ]
    if not (
        binding.get("resolution") == "scope-excluded"
        and binding.get("semantic_disposition") == "not-applicable"
        and isinstance(linked_assertion_ids, list)
        and isinstance(linked_atom_ids, list)
        and isinstance(linked_obligation_ids, list)
        and linked_assertion_ids
        and not linked_obligation_ids
        and dependency_name
        and source_rows
        and exact_fragments
    ):
        return None
    assertions: dict[str, tuple[str, Mapping[str, Any]]] = {}
    for source_design in payload.get("source_designs", []):
        if not isinstance(source_design, Mapping):
            continue
        source_row_id = str(source_design.get("source_row_id", ""))
        for assertion in source_design.get("assertions", []):
            if isinstance(assertion, Mapping):
                assertions[str(assertion.get("assertion_id", ""))] = (
                    source_row_id,
                    assertion,
                )
    linked = list(map(str, linked_assertion_ids))
    if any(assertion_id not in assertions for assertion_id in linked):
        return None
    linked_assertions = [assertions[assertion_id] for assertion_id in linked]
    if list(map(str, linked_atom_ids)) != [
        str(assertion.get("atom_id", "")) for _row_id, assertion in linked_assertions
    ]:
        return None
    for source_row_id, assertion in linked_assertions:
        canonical_statement = str(assertion.get("canonical_statement", "")).casefold()
        if not (
            source_row_id in source_rows
            and assertion.get("semantic_disposition") == "not-applicable"
            and assertion.get("obligation_ids") == []
            and assertion.get("requirement_codes") == []
            and str(assertion.get("field_or_block", "")).strip().casefold()
            == dependency_name
            and any(fragment in canonical_statement for fragment in exact_fragments)
        ):
            return None
    return {
        "dropped_assertion_ids": linked,
        "linked_assertion_ids": [],
        "linked_atom_ids": [],
        "linked_obligation_ids": [],
    }


def _oracle_scope_registry_projections(
    payload: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Return the runner-owned OBL -> SO projection from oracle inventories.

    ``scope_obligation_ids`` is redundant transport data: negative and
    requiredness inventories already own the canonical SO id and its linked OBL.
    Materializing the projection here prevents a model copy/paste error from
    terminating an otherwise valid shard.  The strict validator still validates
    every inventory item and rechecks the derived projection afterwards.
    """

    expected_by_obligation: dict[str, list[str]] = {}
    for collection_name in ("negative_oracles", "requiredness_oracles"):
        collection = payload.get(collection_name, [])
        if not isinstance(collection, list):
            continue
        for item in collection:
            if not isinstance(item, Mapping):
                continue
            obligation_id = str(item.get("linked_obligation_id", ""))
            signal_id = str(item.get("signal_id", ""))
            if not obligation_id or not signal_id.startswith("SIG-"):
                continue
            expected_by_obligation.setdefault(obligation_id, []).append(
                "SO-" + signal_id.removeprefix("SIG-")
            )
    projections: list[dict[str, Any]] = []
    registry = payload.get("obligations", [])
    if not isinstance(registry, list):
        return projections
    for obligation_index, obligation in enumerate(registry):
        if not isinstance(obligation, Mapping):
            continue
        obligation_id = str(obligation.get("obligation_id", ""))
        expected = expected_by_obligation.get(obligation_id, [])
        current = obligation.get("scope_obligation_ids")
        if not isinstance(current, list) or current == expected:
            continue
        projections.append(
            {
                "obligation_index": obligation_index,
                "obligation_id": obligation_id,
                "previous_scope_obligation_ids": current,
                "scope_obligation_ids": expected,
            }
        )
    return projections


def _applicability_registry_projections(
    payload: Mapping[str, Any],
) -> list[dict[str, Any]]:
    obligations = payload.get("obligations", [])
    applicability = payload.get("applicability", [])
    if not isinstance(obligations, list) or not isinstance(applicability, list):
        return []
    dimensions = [
        str(item.get("dimension", ""))
        for item in applicability
        if isinstance(item, Mapping)
    ]
    if dimensions != list(APPLICABILITY_DIMENSIONS):
        return []
    pairs_by_dimension: dict[str, list[tuple[str, str]]] = {
        dimension: [] for dimension in APPLICABILITY_DIMENSIONS
    }
    traceability_pairs: list[tuple[str, str]] = []
    for obligation in obligations:
        if not isinstance(obligation, Mapping):
            continue
        atom_id = str(obligation.get("linked_atom_id", ""))
        test_case_id = str(obligation.get("planned_tc_id", ""))
        dimension = str(obligation.get("design_dimension", ""))
        if not atom_id or not test_case_id or dimension not in pairs_by_dimension:
            continue
        pair = (atom_id, test_case_id)
        traceability_pairs.append(pair)
        if dimension != "traceability":
            pairs_by_dimension[dimension].append(pair)
    pairs_by_dimension["traceability"] = traceability_pairs
    projections: list[dict[str, Any]] = []
    for row_index, row in enumerate(applicability):
        if not isinstance(row, Mapping):
            continue
        dimension = str(row.get("dimension", ""))
        pairs = pairs_by_dimension[dimension]
        expected_atoms = list(dict.fromkeys(atom_id for atom_id, _tc_id in pairs))
        expected_test_cases = list(
            dict.fromkeys(test_case_id for _atom_id, test_case_id in pairs)
        )
        expected_applicable = "yes" if pairs else "no"
        if (
            row.get("applicable") == expected_applicable
            and row.get("linked_atoms") == expected_atoms
            and row.get("linked_test_cases") == expected_test_cases
        ):
            continue
        projections.append(
            {
                "row_index": row_index,
                "dimension": dimension,
                "applicable": expected_applicable,
                "linked_atoms": expected_atoms,
                "linked_test_cases": expected_test_cases,
            }
        )
    return projections


def _external_dynamic_coverage_projections(
    payload: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Find the one safe transport alias for dynamic external dictionaries."""

    obligation_ids = {
        str(obligation_id)
        for binding in payload.get("dependency_bindings", [])
        if isinstance(binding, Mapping)
        and binding.get("kind") == "dictionary"
        and binding.get("resolution") == "external-dynamic"
        for obligation_id in binding.get("linked_obligation_ids", [])
    }
    projections: list[dict[str, Any]] = []
    for index, obligation in enumerate(payload.get("obligations", [])):
        if not isinstance(obligation, Mapping):
            continue
        obligation_id = str(obligation.get("obligation_id", ""))
        if (
            obligation_id in obligation_ids
            and obligation.get("dictionary_refs") == []
            and obligation.get("dictionary_coverage") == "reference-only"
        ):
            projections.append(
                {
                    "obligation_index": index,
                    "obligation_id": obligation_id,
                    "dictionary_coverage": "none_required",
                }
            )
    return projections


def _unknown_oracle_source_alias(value: Any) -> str | None:
    """Return a sentinel only when the text explicitly denies a UI-reaction oracle."""

    normalized = re.sub(
        r"[^a-zа-яё0-9]+",
        "_",
        str(value).casefold(),
    ).strip("_")
    if normalized in UNKNOWN_ORACLE_SOURCE_SENTINELS:
        return None
    for sentinel, canonical in UNKNOWN_ORACLE_SOURCE_SENTINELS.items():
        if normalized.endswith("_" + sentinel):
            return canonical
    explicit_denials = (
        r"(?:^|_)not_(?:the_)?exact_ui_(?:reaction|response)(?:_|$)",
        r"(?:^|_)does_not_(?:define|specify|provide)_(?:the_)?exact_ui_"
        r"(?:reaction|response)(?:_|$)",
        r"(?:^|_)(?:но_)?не_точн(?:ую|ый|ое)_ui_"
        r"(?:реакци(?:ю|и)|отклик|ответ)(?:_|$)",
        r"(?:^|_)точн(?:ая|ый|ое|ую)_ui_"
        r"(?:реакци(?:я|ю|и)|отклик|ответ)_"
        r"(?:не_найден(?:а|о)?|не_задан(?:а|о)?|не_указан(?:а|о)?|"
        r"не_определен(?:а|о)?|"
        r"неизвестн(?:а|о)?)(?:_|$)",
        r"(?:^|_)bsr_[0-9]+(?:_[0-9]+)?$",
        r"(?:^|_)typed_xhtml_(?:requiredness_)?cell$",
        r"(?:^|_)(?:restriction|format|requirement)_only$",
        r"(?:^|_)only_(?:the_)?(?:restriction|format|requirement)$",
        r"(?:^|_)ui_calibration_required$",
        r"(?:^|_)candidate_fallback$",
        r"(?:^|_)fallback(?:_so_req_[0-9]+)?$",
        r"(?:^|_)semantic_(?:requiredness|negative)_candidate_defaults"
        r"(?:_sig_(?:req|neg)_[0-9]+)?$",
    )
    if any(re.search(pattern, normalized) for pattern in explicit_denials):
        return "not_found"
    return None


def _candidate_oracle_source_alias_projections(
    payload: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Canonicalize oracle source from the already explicit candidate state."""

    projections: list[dict[str, Any]] = []
    candidate_obligation_ids: set[str] = set()
    for collection_name in ("negative_oracles", "requiredness_oracles"):
        collection = payload.get(collection_name, [])
        if not isinstance(collection, list):
            continue
        for item_index, item in enumerate(collection):
            if (
                not isinstance(item, Mapping)
                or item.get("decision") != "candidate_tc_required"
                or item.get("oracle_status") != "ui-calibration-required"
            ):
                continue
            candidate_obligation_ids.add(str(item.get("linked_obligation_id", "")))
            normalized_source = re.sub(
                r"[^a-zа-яё0-9]+",
                "_",
                str(item.get("oracle_source", "")).casefold(),
            ).strip("_")
            if normalized_source in UNKNOWN_ORACLE_SOURCE_SENTINELS:
                continue
            canonical = _unknown_oracle_source_alias(item.get("oracle_source"))
            if canonical is None:
                canonical = "not_found"
            projections.append(
                {
                    "path": f"$.{collection_name}[{item_index}].oracle_source",
                    "collection_name": collection_name,
                    "item_index": item_index,
                    "canonical_source": canonical,
                    "signal_id": str(item.get("signal_id", "")),
                }
            )
    obligations = payload.get("obligations", [])
    if isinstance(obligations, list):
        for obligation_index, obligation in enumerate(obligations):
            if not isinstance(obligation, Mapping):
                continue
            obligation_id = str(obligation.get("obligation_id", ""))
            if obligation_id not in candidate_obligation_ids:
                continue
            normalized_source = re.sub(
                r"[^a-zа-яё0-9]+",
                "_",
                str(obligation.get("oracle_source", "")).casefold(),
            ).strip("_")
            if normalized_source in UNKNOWN_ORACLE_SOURCE_SENTINELS:
                continue
            canonical = _unknown_oracle_source_alias(
                obligation.get("oracle_source")
            )
            if canonical is None:
                canonical = "not_found"
            projections.append(
                {
                    "path": f"$.obligations[{obligation_index}].oracle_source",
                    "collection_name": "obligations",
                    "item_index": obligation_index,
                    "canonical_source": canonical,
                    "obligation_id": obligation_id,
                }
            )
    return projections


_EXPLICIT_REQUIREDNESS_ORACLE_PATTERN = re.compile(
    r"(?:подсвеч|подсказк|сообщен(?:ие|ия)|ошибк|"
    r"не\s+(?:сохраня|подтвержда|принима|валид)|"
    r"нельзя\s+(?:сохран|подтверд|продолж)|блокир|"
    r"validation\s+message|error\s+message|rejected|"
    r"not\s+(?:accepted|saved|confirmed|valid))",
    re.IGNORECASE,
)


def _requiredness_signal_has_explicit_observable_oracle(
    signal: Mapping[str, Any],
) -> bool:
    """Return whether one authoritative signal sentence names a visible reaction.

    A compound statement that values are required proves the business rule, but it
    does not by itself prove a marker, message, save rejection or another executable
    UI reaction.  Keep the decision conservative unless that same projected signal
    sentence contains an explicit observable consequence.
    """

    if signal.get("source_binding") != "compound-text-requirement":
        return True
    source = normalize_exact_source_text(
        str(signal.get("requiredness_source", ""))
    )
    return _EXPLICIT_REQUIREDNESS_ORACLE_PATTERN.search(source) is not None


def _text_has_missing_required_value(value: Any) -> bool:
    """Recognize a concrete missing-value fixture without broad absence guesses."""

    if _text_has_empty_result(value):
        return True
    return re.search(
        r"(?:отсутств(?:ует|овал|овала|овало|уют)|"
        r"не\s+(?:указан|указана|указано|заполнен|заполнена|заполнено)|"
        r"\b(?:missing|omitted|absent)\b)",
        str(value).casefold(),
    ) is not None


def _text_has_no_action(value: Any) -> bool:
    return re.search(
        r"(?:не\s+(?:нажимать|использовать|активировать|взаимодействовать)|"
        r"взаимодействие\s+отсутствует|\bno[- ]action\b)",
        str(value).casefold(),
    ) is not None


def _action_control_kind(row: Mapping[str, Any]) -> str | None:
    for cell in row.get("physical_table_cells", []):
        if not isinstance(cell, Mapping):
            continue
        value = normalize_exact_source_text(
            str(cell.get("bounded_source_text", ""))
        ).casefold()
        if value == "кнопка":
            return "кнопка"
        if value == "виджет":
            return "виджет"
    return None


def _unsupported_executable_requiredness_candidate_projections(
    payload: Mapping[str, Any],
    *,
    expected_signals_by_scope: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Downgrade only provably unobservable requiredness results to UI calibration.

    The source can prove that a value is required without defining the concrete marker,
    message, focus change or submit reaction. A model must not turn that business rule
    into a source-backed executable UI oracle. The repair preserves the negative input
    and traceability chain while making the unknown reaction explicit.
    """

    obligations = payload.get("obligations", [])
    source_designs = payload.get("source_designs", [])
    oracles = payload.get("requiredness_oracles", [])
    if not all(isinstance(items, list) for items in (obligations, source_designs, oracles)):
        return []
    obligation_index_by_id = {
        str(item.get("obligation_id", "")): index
        for index, item in enumerate(obligations)
        if isinstance(item, Mapping)
    }
    owner_by_atom: dict[str, tuple[int, int, Mapping[str, Any]]] = {}
    for source_index, source_design in enumerate(source_designs):
        if not isinstance(source_design, Mapping):
            continue
        assertions = source_design.get("assertions", [])
        if not isinstance(assertions, list):
            continue
        for assertion_index, assertion in enumerate(assertions):
            if isinstance(assertion, Mapping):
                owner_by_atom[str(assertion.get("atom_id", ""))] = (
                    source_index,
                    assertion_index,
                    assertion,
                )

    projections: list[dict[str, Any]] = []
    for oracle_index, oracle in enumerate(oracles):
        if (
            not isinstance(oracle, Mapping)
            or oracle.get("restriction_type") != "requiredness"
            or oracle.get("decision") != "executable_tc"
        ):
            continue
        scope_id = str(oracle.get("scope_obligation_id", ""))
        expected_signal = (
            expected_signals_by_scope.get(scope_id)
            if expected_signals_by_scope is not None
            else None
        )
        model_reports_unobservable = (
            oracle.get("marker_oracle_found") != "yes"
            and oracle.get("empty_value_oracle_found") != "yes"
        )
        source_requires_calibration = (
            expected_signal is not None
            and not _requiredness_signal_has_explicit_observable_oracle(
                expected_signal
            )
        )
        if not model_reports_unobservable and not source_requires_calibration:
            continue
        owner_location = owner_by_atom.get(str(oracle.get("linked_atom_id", "")))
        obligation_index = obligation_index_by_id.get(
            str(oracle.get("linked_obligation_id", ""))
        )
        if owner_location is None or obligation_index is None or not scope_id:
            continue
        source_index, assertion_index, assertion = owner_location
        obligation = obligations[obligation_index]
        if (
            not isinstance(obligation, Mapping)
            or assertion.get("semantic_disposition") != "testable"
            or assertion.get("polarity") != "negative"
            or obligation.get("check_type") not in {"negative", "boundary"}
            or not _text_has_missing_required_value(
                obligation.get("test_data", "")
            )
        ):
            continue
        field = str(oracle.get("field_or_block", "")).strip() or "обязательное поле"
        assertion_fields = {
            "canonical_statement": (
                f"Проверяется обязательность «{field}»; точный UI-отклик "
                "требует калибровки."
            ),
            "oracle_clauses": [
                f"Система не принимает отсутствие обязательного значения «{field}»; "
                "точный UI-отклик требует калибровки."
            ],
            "disposition_rationale": (
                "Обязательность подтверждена источником, но конкретный наблюдаемый "
                "UI-отклик в источнике не задан."
            ),
        }
        obligation_fields = {
            "obligation_class": "calibration-candidate",
            "required_behavior": assertion_fields["oracle_clauses"][0],
            "planned_tc_id": f"TC-CAND-{scope_id}",
            "review_notes": "candidate-ui-calibration",
            "single_expected_behavior": assertion_fields["oracle_clauses"][0],
            "oracle_source": "not_found",
        }
        oracle_fields = {
            "marker_oracle_found": "no",
            "empty_value_oracle_found": (
                "partial"
                if source_requires_calibration
                or oracle.get("empty_value_oracle_found") == "partial"
                else "no"
            ),
            "oracle_source": "not_found",
            "oracle_status": "ui-calibration-required",
            "decision": "candidate_tc_required",
            "planned_tc_or_gap": f"candidate:{scope_id}",
            "gap_id": str(oracle.get("gap_id", "")) or "none_required",
            "analyst_question": (
                f"Какой точный UI-отклик отображается при отсутствии «{field}»?"
            ),
            "handoff_rule": (
                f"Сохранить отдельный candidate TC для «{field}» и не выдумывать "
                "текст или вид UI-реакции."
            ),
            "calibration_notes": (
                "candidate-ui-calibration: обязательность source-backed, точная "
                "UI-реакция не задана."
            ),
        }
        projections.append(
            {
                "path": (
                    f"$.source_designs[{source_index}].assertions[{assertion_index}]"
                ),
                "source_index": source_index,
                "assertion_index": assertion_index,
                "obligation_index": obligation_index,
                "oracle_index": oracle_index,
                "scope_obligation_id": scope_id,
                "source_requires_calibration": source_requires_calibration,
                "previous_value_sha256": canonical_payload_sha256(
                    {"assertion": assertion, "obligation": obligation, "oracle": oracle}
                ),
                "assertion_fields": assertion_fields,
                "obligation_fields": obligation_fields,
                "oracle_fields": oracle_fields,
            }
        )
    return projections


def _candidate_signal_code_binding_projections(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Recover candidate signal codes from one unique same-row evidence donor."""

    rows = _eligible_semantic_rows(context, boundary)
    code_registry = {
        str(item.get("source_row_id", "")): list(
            map(str, item.get("requirement_codes", []))
        )
        for item in boundary.get("source_decisions", [])
        if isinstance(item, Mapping)
    }
    expected_registry = _source_signal_registry(rows, code_registry)
    expected_by_collection = {
        "negative_oracles": {
            str(item["signal_id"]): item
            for item in expected_registry["negative"]
        },
        "requiredness_oracles": {
            str(item["signal_id"]): item
            for item in expected_registry["requiredness"]
        },
    }
    source_designs = payload.get("source_designs", [])
    if not isinstance(source_designs, list):
        return []
    projections: list[dict[str, Any]] = []
    for collection_name, expected_by_id in expected_by_collection.items():
        collection = payload.get(collection_name, [])
        if not isinstance(collection, list):
            continue
        for item in collection:
            if (
                not isinstance(item, Mapping)
                or item.get("decision") != "candidate_tc_required"
                or item.get("oracle_status") != "ui-calibration-required"
            ):
                continue
            signal_id = str(item.get("signal_id", ""))
            expected = expected_by_id.get(signal_id)
            if expected is None:
                continue
            expected_codes = list(map(str, expected.get("requirement_codes", [])))
            source_row_id = str(expected.get("source_row_id", ""))
            if (
                not expected_codes
                or item.get("requirement_codes") != expected_codes
                or item.get("source_row_id") != source_row_id
            ):
                continue
            linked_atom_id = str(item.get("linked_atom_id", ""))
            owner_location: tuple[int, int, Mapping[str, Any]] | None = None
            for source_index, source_design in enumerate(source_designs):
                if (
                    not isinstance(source_design, Mapping)
                    or source_design.get("source_row_id") != source_row_id
                ):
                    continue
                assertions = source_design.get("assertions", [])
                if not isinstance(assertions, list):
                    continue
                for assertion_index, assertion in enumerate(assertions):
                    if (
                        isinstance(assertion, Mapping)
                        and assertion.get("atom_id") == linked_atom_id
                    ):
                        owner_location = (source_index, assertion_index, assertion)
                        break
            if owner_location is None:
                continue
            source_index, assertion_index, owner = owner_location
            owner_codes = owner.get("requirement_codes")
            owner_evidence = owner.get("requirement_code_evidence")
            clause_evidence = owner.get("clause_evidence")
            if (
                not isinstance(owner_codes, list)
                or not isinstance(owner_evidence, list)
                or not isinstance(clause_evidence, list)
            ):
                continue
            missing_codes = [
                code for code in expected_codes if code not in set(map(str, owner_codes))
            ]
            if not missing_codes:
                continue
            literal_anchor = str(expected.get("literal_anchor", ""))
            if not any(
                isinstance(binding, Mapping)
                and binding.get("source_row_id") == source_row_id
                and literal_anchor in str(binding.get("exact_source_fragment", ""))
                for binding in clause_evidence
            ):
                continue
            source_design = source_designs[source_index]
            assertions = source_design.get("assertions", [])
            donors: list[dict[str, Any]] = []
            provable = True
            for code in missing_codes:
                matches = [
                    evidence
                    for assertion in assertions
                    if isinstance(assertion, Mapping)
                    for evidence in assertion.get("requirement_code_evidence", [])
                    if isinstance(evidence, Mapping)
                    and evidence.get("requirement_code") == code
                    and evidence.get("source_row_id") == source_row_id
                ]
                unique_matches = {
                    canonical_payload_sha256(match): match for match in matches
                }
                if len(unique_matches) != 1:
                    provable = False
                    break
                donors.append(copy.deepcopy(next(iter(unique_matches.values()))))
            if not provable:
                continue
            owned = set(map(str, owner_codes)) | set(missing_codes)
            canonical_codes = [
                code for code in code_registry.get(source_row_id, []) if code in owned
            ]
            if set(canonical_codes) != owned:
                continue
            projections.append(
                {
                    "source_index": source_index,
                    "assertion_index": assertion_index,
                    "assertion_id": str(owner.get("assertion_id", "")),
                    "signal_id": signal_id,
                    "missing_requirement_codes": missing_codes,
                    "canonical_requirement_codes": canonical_codes,
                    "canonical_requirement_code_evidence": [
                        *copy.deepcopy(owner_evidence),
                        *donors,
                    ],
                }
            )
    return projections


def _same_row_clause_evidence_span_projections(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Merge only duplicate clause evidence that forms one literal same-row span."""

    rows_by_id = {
        str(row.get("source_row_id", "")): str(
            row.get("bounded_source_text", "")
        )
        for row in context.get("source_rows", [])
        if isinstance(row, Mapping)
    }
    projections: list[dict[str, Any]] = []
    for source_index, source_design in enumerate(payload.get("source_designs", [])):
        if not isinstance(source_design, Mapping):
            continue
        assertions = source_design.get("assertions", [])
        if not isinstance(assertions, list):
            continue
        for assertion_index, assertion in enumerate(assertions):
            if not isinstance(assertion, Mapping):
                continue
            evidence = assertion.get("clause_evidence", [])
            if not isinstance(evidence, list):
                continue
            grouped: dict[tuple[str, int], list[int]] = defaultdict(list)
            for evidence_index, binding in enumerate(evidence):
                if (
                    isinstance(binding, Mapping)
                    and isinstance(binding.get("clause_kind"), str)
                    and type(binding.get("clause_index")) is int
                ):
                    grouped[
                        (
                            str(binding["clause_kind"]),
                            int(binding["clause_index"]),
                        )
                    ].append(evidence_index)
            replacements: dict[int, dict[str, Any]] = {}
            skipped: set[int] = set()
            merged_keys: list[str] = []
            for (clause_kind, clause_index), indices in grouped.items():
                if len(indices) < 2:
                    continue
                bindings = [evidence[index] for index in indices]
                row_ids = {
                    str(binding.get("source_row_id", ""))
                    for binding in bindings
                    if isinstance(binding, Mapping)
                }
                if len(row_ids) != 1:
                    continue
                row_id = next(iter(row_ids))
                source_text = rows_by_id.get(row_id)
                if source_text is None:
                    continue
                fragments = [
                    str(binding.get("exact_source_fragment", ""))
                    for binding in bindings
                    if isinstance(binding, Mapping)
                ]
                starts = [source_text.find(fragment) for fragment in fragments]
                if (
                    len(fragments) != len(indices)
                    or any(not fragment for fragment in fragments)
                    or any(start < 0 for start in starts)
                ):
                    continue
                span_start = min(starts)
                span_end = max(
                    start + len(fragment)
                    for start, fragment in zip(starts, fragments, strict=True)
                )
                replacement = copy.deepcopy(dict(bindings[0]))
                replacement["exact_source_fragment"] = source_text[
                    span_start:span_end
                ]
                replacements[indices[0]] = replacement
                skipped.update(indices[1:])
                merged_keys.append(f"{clause_kind}:{clause_index}")
            if not replacements:
                continue
            canonical_evidence = [
                copy.deepcopy(replacements.get(index, binding))
                for index, binding in enumerate(evidence)
                if index not in skipped
            ]
            projections.append(
                {
                    "source_index": source_index,
                    "assertion_index": assertion_index,
                    "assertion_id": str(assertion.get("assertion_id", "")),
                    "path": (
                        f"$.source_designs[{source_index}].assertions"
                        f"[{assertion_index}].clause_evidence"
                    ),
                    "merged_clause_keys": merged_keys,
                    "canonical_evidence": canonical_evidence,
                }
            )
    return projections


def _necessary_control_missing_clause_evidence_projections(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Rebind a derived negative branch to its literal necessary-condition rule.

    Counterfactual condition text (for example A becoming true instead of the source's
    ``A = false`` predicate) is intentionally not a literal source fragment. Only when
    that non-literal evidence belongs to a negative necessary-condition assertion do we
    replace it with the already authenticated full requirement fragment from the same
    row. The semantic clause itself is not changed.
    """

    rows_by_id = {
        str(row.get("source_row_id", "")): str(row.get("bounded_source_text", ""))
        for row in context.get("source_rows", [])
        if isinstance(row, Mapping)
    }
    projections: list[dict[str, Any]] = []
    for source_index, source_design in enumerate(payload.get("source_designs", [])):
        if not isinstance(source_design, Mapping):
            continue
        source_row_id = str(source_design.get("source_row_id", ""))
        source_text = rows_by_id.get(source_row_id, "")
        assertions = source_design.get("assertions", [])
        if not source_text or not isinstance(assertions, list):
            continue
        for assertion_index, assertion in enumerate(assertions):
            if (
                not isinstance(assertion, Mapping)
                or assertion.get("semantic_disposition") != "testable"
                or assertion.get("polarity") != "negative"
            ):
                continue
            requirement_evidence = assertion.get("requirement_code_evidence", [])
            if not isinstance(requirement_evidence, list):
                continue
            donors = [
                str(binding.get("exact_source_fragment", ""))
                for binding in requirement_evidence
                if isinstance(binding, Mapping)
                and binding.get("source_row_id") == source_row_id
                and _required_necessary_condition_negative_controls(
                    str(binding.get("exact_source_fragment", ""))
                )
                and str(binding.get("exact_source_fragment", "")) in source_text
            ]
            if len(set(donors)) != 1:
                continue
            donor = donors[0]
            evidence = assertion.get("clause_evidence", [])
            if not isinstance(evidence, list):
                continue
            replacements: list[int] = []
            canonical_evidence = copy.deepcopy(evidence)
            for evidence_index, binding in enumerate(evidence):
                if (
                    isinstance(binding, Mapping)
                    and binding.get("source_row_id") == source_row_id
                    and str(binding.get("exact_source_fragment", "")) not in source_text
                ):
                    canonical_evidence[evidence_index]["exact_source_fragment"] = donor
                    replacements.append(evidence_index)
            if replacements:
                projections.append(
                    {
                        "path": (
                            f"$.source_designs[{source_index}].assertions"
                            f"[{assertion_index}].clause_evidence"
                        ),
                        "source_index": source_index,
                        "assertion_index": assertion_index,
                        "assertion_id": str(assertion.get("assertion_id", "")),
                        "repaired_evidence_indices": replacements,
                        "canonical_evidence": canonical_evidence,
                    }
                )
    return projections


def _binary_optional_candidate_default_projections(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Rebind typed candidates to a source-backed default or no-action contract."""

    clarifications = tuple(
        item
        for item in context.get("approved_clarifications", [])
        if isinstance(item, Mapping)
    )
    preflight = validate_semantic_input_preflight(
        context,
        boundary,
        clarifications,
    )
    defaults_by_scope = {
        str(item.get("scope_obligation_id", "")): item
        for item in preflight.get("requiredness_candidate_defaults", [])
        if isinstance(item, Mapping)
        and item.get("fallback_input_mode")
        in {"binary-logical-default", "no-action-control"}
    }
    if not defaults_by_scope:
        return []
    rows_by_id = {
        str(row.get("source_row_id", "")): str(
            row.get("bounded_source_text", "")
        )
        for row in context.get("source_rows", [])
        if isinstance(row, Mapping)
    }
    obligations = payload.get("obligations", [])
    if not isinstance(obligations, list):
        return []
    obligation_index_by_id = {
        str(item.get("obligation_id", "")): index
        for index, item in enumerate(obligations)
        if isinstance(item, Mapping)
    }
    owners_by_atom: dict[str, tuple[int, int, Mapping[str, Any]]] = {}
    for source_index, source_design in enumerate(payload.get("source_designs", [])):
        if not isinstance(source_design, Mapping):
            continue
        for assertion_index, assertion in enumerate(
            source_design.get("assertions", [])
        ):
            if isinstance(assertion, Mapping):
                owners_by_atom[str(assertion.get("atom_id", ""))] = (
                    source_index,
                    assertion_index,
                    assertion,
                )
    projections: list[dict[str, Any]] = []
    for oracle_index, oracle in enumerate(payload.get("requiredness_oracles", [])):
        if (
            not isinstance(oracle, Mapping)
            or oracle.get("decision") != "candidate_tc_required"
            or oracle.get("restriction_type") not in {"requiredness", "optionality"}
        ):
            continue
        scope_id = str(oracle.get("scope_obligation_id", ""))
        default = defaults_by_scope.get(scope_id)
        if default is None:
            continue
        owner_location = owners_by_atom.get(str(oracle.get("linked_atom_id", "")))
        obligation_index = obligation_index_by_id.get(
            str(oracle.get("linked_obligation_id", ""))
        )
        if owner_location is None or obligation_index is None:
            continue
        source_index, assertion_index, assertion = owner_location
        obligation = obligations[obligation_index]
        if not isinstance(obligation, Mapping):
            continue
        source_row_id = str(default["source_row_id"])
        source_text = rows_by_id.get(source_row_id, "")
        condition_clauses = assertion.get("condition_clauses", [])
        action_clauses = assertion.get("action_clauses", [])
        oracle_clauses = assertion.get("oracle_clauses", [])
        evidence = assertion.get("clause_evidence", [])
        if (
            not source_text
            or not isinstance(condition_clauses, list)
            or not isinstance(action_clauses, list)
            or not isinstance(oracle_clauses, list)
            or len(action_clauses) != 1
            or len(oracle_clauses) != 1
            or not isinstance(evidence, list)
        ):
            continue
        condition_evidence = [
            copy.deepcopy(dict(binding))
            for binding in evidence
            if isinstance(binding, Mapping)
            and binding.get("clause_kind") == "condition"
            and type(binding.get("clause_index")) is int
        ]
        if sorted(
            int(binding["clause_index"]) for binding in condition_evidence
        ) != list(range(len(condition_clauses))):
            continue
        condition_evidence.sort(key=lambda binding: int(binding["clause_index"]))
        canonical_evidence = [
            *condition_evidence,
            {
                "clause_kind": "action",
                "clause_index": 0,
                "source_row_id": source_row_id,
                "exact_source_fragment": source_text,
            },
            {
                "clause_kind": "oracle",
                "clause_index": 0,
                "source_row_id": source_row_id,
                "exact_source_fragment": source_text,
            },
        ]
        assertion_fields = {
            "canonical_statement": str(default["fallback_canonical_statement"]),
            # The projected scenario observes a valid source-backed default.
            # It is positive even when the registry signal itself is typed as
            # requiredness; no invalid input or rejection is exercised here.
            "polarity": "positive",
            "action_clauses": [str(default["fallback_action"])],
            "oracle_clauses": [str(default["fallback_expected_behavior"])],
            "clause_evidence": canonical_evidence,
            "disposition_rationale": str(
                default["fallback_disposition_rationale"]
            ),
        }
        restriction_type = str(oracle.get("restriction_type", ""))
        optional = restriction_type == "optionality"
        no_action_control = default.get("fallback_input_mode") == "no-action-control"
        obligation_fields = {
            "obligation_class": (
                "optionality-action-control"
                if no_action_control
                else "optionality-binary-default"
                if optional
                else "requiredness-binary-default"
            ),
            "required_behavior": str(default["fallback_expected_behavior"]),
            "review_notes": str(default["fallback_disposition_rationale"]),
            "planned_check": str(default["fallback_action"]),
            "check_type": (
                "positive"
                if optional
                else (
                    "dependency"
                    if _is_conditional_requiredness_signal(
                        {"requiredness_source": default["fallback_required_when"]}
                    )
                    else "boundary"
                )
            ),
            "coverage_class": (
                "optionality-action-control"
                if no_action_control
                else "optionality-binary-default"
                if optional
                else "requiredness-binary-default"
            ),
            "input_class": (
                "no-action"
                if no_action_control
                else str(default["fallback_test_data"])
            ),
            "single_expected_behavior": str(
                default["fallback_expected_behavior"]
            ),
            "oracle_source": "not_found",
            "test_data": str(default["fallback_test_data"]),
        }
        oracle_fields = {
            "requiredness_class": (
                "optional-action-control"
                if no_action_control
                else "optional-binary-default"
                if optional
                else "required-binary-default"
            ),
            "required_when": str(default["fallback_required_when"]),
            "marker_oracle_found": "no",
            "empty_value_oracle_found": "no",
            "oracle_source": "not_found",
            "oracle_status": "ui-calibration-required",
            "decision": "candidate_tc_required",
            "planned_tc_or_gap": f"candidate:{scope_id}",
            "gap_id": "none_required",
            "analyst_question": str(default["analyst_question"]),
            "handoff_rule": str(default["handoff_rule"]),
            "calibration_notes": str(default["calibration_notes"]),
        }
        current = {
            "assertion": {
                key: assertion.get(key) for key in assertion_fields
            },
            "obligation": {
                key: obligation.get(key) for key in obligation_fields
            },
            "oracle": {key: oracle.get(key) for key in oracle_fields},
        }
        expected = {
            "assertion": assertion_fields,
            "obligation": obligation_fields,
            "oracle": oracle_fields,
        }
        if current == expected:
            continue
        projections.append(
            {
                "path": (
                    f"$.source_designs[{source_index}].assertions"
                    f"[{assertion_index}]"
                ),
                "source_index": source_index,
                "assertion_index": assertion_index,
                "obligation_index": obligation_index,
                "oracle_index": oracle_index,
                "source_row_id": source_row_id,
                "assertion_id": str(assertion.get("assertion_id", "")),
                "scope_obligation_id": scope_id,
                "restriction_type": restriction_type,
                "fallback_input_mode": str(default["fallback_input_mode"]),
                "previous_value_sha256": canonical_payload_sha256(current),
                "assertion_fields": assertion_fields,
                "obligation_fields": obligation_fields,
                "oracle_fields": oracle_fields,
            }
        )
    return projections


def _candidate_fallback_clause_evidence_projections(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Bind exact deterministic candidate fallbacks to their literal XHTML row."""

    clarifications = tuple(
        item
        for item in context.get("approved_clarifications", [])
        if isinstance(item, Mapping)
    )
    preflight = validate_semantic_input_preflight(
        context,
        boundary,
        clarifications,
    )
    defaults_by_scope = {
        str(item.get("scope_obligation_id", "")): item
        for item in preflight.get("requiredness_candidate_defaults", [])
        if isinstance(item, Mapping)
    }
    candidate_by_atom = {
        str(item.get("linked_atom_id", "")): item
        for item in payload.get("requiredness_oracles", [])
        if isinstance(item, Mapping)
        and item.get("decision") == "candidate_tc_required"
        and item.get("oracle_status") == "ui-calibration-required"
    }
    rows_by_id = {
        str(row.get("source_row_id", "")): str(
            row.get("bounded_source_text", "")
        )
        for row in context.get("source_rows", [])
        if isinstance(row, Mapping)
    }
    projections: list[dict[str, Any]] = []
    for source_index, source_design in enumerate(payload.get("source_designs", [])):
        if not isinstance(source_design, Mapping):
            continue
        assertions = source_design.get("assertions", [])
        if not isinstance(assertions, list):
            continue
        for assertion_index, assertion in enumerate(assertions):
            if not isinstance(assertion, Mapping):
                continue
            candidate = candidate_by_atom.get(str(assertion.get("atom_id", "")))
            if candidate is None:
                continue
            default = defaults_by_scope.get(
                str(candidate.get("scope_obligation_id", ""))
            )
            if default is None:
                continue
            source_row_id = str(default.get("source_row_id", ""))
            if candidate.get("source_row_id") != source_row_id:
                continue
            source_text = rows_by_id.get(source_row_id)
            if not source_text:
                continue
            clauses_by_kind = {
                "action": assertion.get("action_clauses", []),
                "oracle": assertion.get("oracle_clauses", []),
            }
            fallback_by_kind = {
                "action": str(default.get("fallback_action", "")),
                "oracle": str(default.get("fallback_expected_behavior", "")),
            }
            evidence = assertion.get("clause_evidence", [])
            if not isinstance(evidence, list):
                continue
            canonical_evidence = copy.deepcopy(evidence)
            repaired_keys: list[str] = []
            for evidence_index, binding in enumerate(evidence):
                if not isinstance(binding, Mapping):
                    continue
                clause_kind = str(binding.get("clause_kind", ""))
                clause_index = binding.get("clause_index")
                clauses = clauses_by_kind.get(clause_kind)
                if (
                    clauses is None
                    or type(clause_index) is not int
                    or clause_index < 0
                    or clause_index >= len(clauses)
                    or str(binding.get("source_row_id", "")) != source_row_id
                    or str(binding.get("exact_source_fragment", "")) in source_text
                    or str(clauses[clause_index]) != fallback_by_kind[clause_kind]
                ):
                    continue
                repaired = canonical_evidence[evidence_index]
                if not isinstance(repaired, dict):
                    continue
                repaired["exact_source_fragment"] = source_text
                repaired_keys.append(f"{clause_kind}:{clause_index}")
            if not repaired_keys:
                continue
            projections.append(
                {
                    "source_index": source_index,
                    "assertion_index": assertion_index,
                    "assertion_id": str(assertion.get("assertion_id", "")),
                    "path": (
                        f"$.source_designs[{source_index}].assertions"
                        f"[{assertion_index}].clause_evidence"
                    ),
                    "repaired_clause_keys": repaired_keys,
                    "canonical_evidence": canonical_evidence,
                }
            )
    return projections


def _negative_candidate_clause_evidence_projections(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Bind a calibration-only negative oracle clause to its exact source rule."""

    rows = _eligible_semantic_rows(context, boundary)
    code_registry = {
        str(item.get("source_row_id", "")): list(
            map(str, item.get("requirement_codes", []))
        )
        for item in boundary.get("source_decisions", [])
        if isinstance(item, Mapping)
    }
    expected_by_signal = {
        str(item["signal_id"]): item
        for item in _source_signal_registry(rows, code_registry)["negative"]
    }
    rows_by_id = {
        str(row.get("source_row_id", "")): str(
            row.get("bounded_source_text", "")
        )
        for row in context.get("source_rows", [])
        if isinstance(row, Mapping)
    }
    candidate_by_atom: dict[str, tuple[Mapping[str, Any], Mapping[str, Any]]] = {}
    for item in payload.get("negative_oracles", []):
        if (
            not isinstance(item, Mapping)
            or item.get("decision") != "candidate_tc_required"
            or item.get("oracle_status") != "ui-calibration-required"
        ):
            continue
        expected = expected_by_signal.get(str(item.get("signal_id", "")))
        if expected is None or any(
            item.get(field) != expected.get(field)
            for field in (
                "signal_id",
                "scope_obligation_id",
                "source_row_id",
                "requirement_codes",
                "restriction_type",
            )
        ):
            continue
        candidate_by_atom[str(item.get("linked_atom_id", ""))] = (item, expected)
    projections: list[dict[str, Any]] = []
    for source_index, source_design in enumerate(payload.get("source_designs", [])):
        if not isinstance(source_design, Mapping):
            continue
        assertions = source_design.get("assertions", [])
        if not isinstance(assertions, list):
            continue
        for assertion_index, assertion in enumerate(assertions):
            if not isinstance(assertion, Mapping):
                continue
            candidate_pair = candidate_by_atom.get(str(assertion.get("atom_id", "")))
            if candidate_pair is None:
                continue
            candidate, expected = candidate_pair
            source_row_id = str(expected.get("source_row_id", ""))
            source_text = rows_by_id.get(source_row_id, "")
            source_statement = str(candidate.get("source_statement", ""))
            literal_anchor = str(expected.get("literal_anchor", ""))
            if (
                not source_statement
                or source_statement not in source_text
                or literal_anchor not in source_statement
            ):
                continue
            oracle_clauses = assertion.get("oracle_clauses", [])
            evidence = assertion.get("clause_evidence", [])
            if not isinstance(oracle_clauses, list) or not isinstance(evidence, list):
                continue
            canonical_evidence = copy.deepcopy(evidence)
            repaired_keys: list[str] = []
            for evidence_index, binding in enumerate(evidence):
                if (
                    not isinstance(binding, Mapping)
                    or binding.get("clause_kind") != "oracle"
                    or type(binding.get("clause_index")) is not int
                    or binding.get("source_row_id") != source_row_id
                ):
                    continue
                clause_index = int(binding["clause_index"])
                if clause_index < 0 or clause_index >= len(oracle_clauses):
                    continue
                fragment = str(binding.get("exact_source_fragment", ""))
                clause_text = str(oracle_clauses[clause_index]).casefold()
                if fragment in source_text or not any(
                    marker in clause_text
                    for marker in (
                        "калибров",
                        "не выдум",
                        "не найден",
                        "not found",
                        "calibration",
                    )
                ):
                    continue
                repaired = canonical_evidence[evidence_index]
                if not isinstance(repaired, dict):
                    continue
                repaired["exact_source_fragment"] = source_statement
                repaired_keys.append(f"oracle:{clause_index}")
            if repaired_keys:
                projections.append(
                    {
                        "source_index": source_index,
                        "assertion_index": assertion_index,
                        "assertion_id": str(assertion.get("assertion_id", "")),
                        "path": (
                            f"$.source_designs[{source_index}].assertions"
                            f"[{assertion_index}].clause_evidence"
                        ),
                        "repaired_clause_keys": repaired_keys,
                        "canonical_evidence": canonical_evidence,
                    }
                )
    return projections


def _executable_negative_signal_evidence_projections(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Expand one literal clause span to retain an executable signal anchor.

    The oracle registry already carries a source-row-exact statement and an exact
    ASSERT/ATOM/OBL link. When the owning assertion cites another literal part of
    the same row, the smallest contiguous span containing both fragments is a
    mechanical provenance repair; it does not invent or reinterpret behavior.
    """

    expected_by_signal = {
        str(item["signal_id"]): item
        for item in semantic_source_signal_registry(context, boundary)["negative"]
    }
    rows_by_id = {
        str(row.get("source_row_id", "")): str(row.get("bounded_source_text", ""))
        for row in context.get("source_rows", [])
        if isinstance(row, Mapping)
    }
    owner_by_atom: dict[str, tuple[int, int, Mapping[str, Any]]] = {}
    for source_index, source_design in enumerate(payload.get("source_designs", [])):
        if not isinstance(source_design, Mapping):
            continue
        assertions = source_design.get("assertions", [])
        if not isinstance(assertions, list):
            continue
        for assertion_index, assertion in enumerate(assertions):
            if isinstance(assertion, Mapping):
                owner_by_atom[str(assertion.get("atom_id", ""))] = (
                    source_index,
                    assertion_index,
                    assertion,
                )

    projections: list[dict[str, Any]] = []
    collection = payload.get("negative_oracles", [])
    if not isinstance(collection, list):
        return projections
    for item in collection:
        if not isinstance(item, Mapping) or item.get("decision") != "executable_tc":
            continue
        signal_id = str(item.get("signal_id", ""))
        expected = expected_by_signal.get(signal_id)
        if expected is None:
            continue
        source_row_id = str(expected.get("source_row_id", ""))
        source_text = rows_by_id.get(source_row_id, "")
        source_statement = str(item.get("source_statement", ""))
        literal_anchor = str(expected.get("literal_anchor", ""))
        if (
            not source_text
            or not source_statement
            or source_statement not in source_text
            or literal_anchor not in source_statement
            or item.get("source_row_id") != source_row_id
            or item.get("scope_obligation_id")
            != expected.get("scope_obligation_id")
            or item.get("requirement_codes") != expected.get("requirement_codes")
            or item.get("restriction_type") != expected.get("restriction_type")
        ):
            continue
        owner_location = owner_by_atom.get(str(item.get("linked_atom_id", "")))
        if owner_location is None:
            continue
        source_index, assertion_index, owner = owner_location
        if str(item.get("linked_obligation_id", "")) not in set(
            map(str, owner.get("obligation_ids", []))
        ):
            continue
        if any(
            row_id == source_row_id and literal_anchor in fragment
            for row_id, fragment in _assertion_literal_evidence(owner)
        ):
            continue
        evidence = owner.get("clause_evidence", [])
        if not isinstance(evidence, list):
            continue
        statement_start = source_text.find(source_statement)
        statement_end = statement_start + len(source_statement)
        candidates: list[tuple[int, int, int, int, int]] = []
        for evidence_index, binding in enumerate(evidence):
            if (
                not isinstance(binding, Mapping)
                or binding.get("source_row_id") != source_row_id
            ):
                continue
            fragment = str(binding.get("exact_source_fragment", ""))
            fragment_start = source_text.find(fragment)
            if not fragment or fragment_start < 0:
                continue
            span_start = min(fragment_start, statement_start)
            span_end = max(fragment_start + len(fragment), statement_end)
            priority = {
                "condition": 0,
                "action": 1,
                "oracle": 2,
            }.get(str(binding.get("clause_kind", "")), 3)
            candidates.append(
                (span_end - span_start, priority, evidence_index, span_start, span_end)
            )
        if not candidates:
            continue
        _span_length, _priority, evidence_index, span_start, span_end = min(candidates)
        canonical_evidence = copy.deepcopy(evidence)
        repaired = canonical_evidence[evidence_index]
        if not isinstance(repaired, dict):
            continue
        repaired["exact_source_fragment"] = source_text[span_start:span_end]
        projections.append(
            {
                "source_index": source_index,
                "assertion_index": assertion_index,
                "assertion_id": str(owner.get("assertion_id", "")),
                "signal_id": signal_id,
                "path": (
                    f"$.source_designs[{source_index}].assertions"
                    f"[{assertion_index}].clause_evidence[{evidence_index}]"
                ),
                "canonical_evidence": canonical_evidence,
            }
        )
    return projections


def _collapsed_executable_negative_oracle_projection(
    payload: Mapping[str, Any],
    *,
    context: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Split one provably branch-aligned negative signal aggregate.

    This repair is deliberately narrow: one shared ASSERT/ATOM/OBL must own two or
    more executable negative oracle rows, and its condition/action/oracle arrays plus
    clause evidence must form an exact one-to-one ordered branch matrix. Anything
    less explicit remains a strict validation failure.
    """

    if context is None:
        return None
    source_text_by_row = {
        str(row.get("source_row_id", "")): str(row.get("bounded_source_text", ""))
        for row in context.get("source_rows", [])
        if isinstance(row, Mapping)
    }
    negative_oracles = payload.get("negative_oracles", [])
    source_designs = payload.get("source_designs", [])
    obligations = payload.get("obligations", [])
    dependency_bindings = payload.get("dependency_bindings", [])
    reset_bindings = payload.get("reset_lifecycle_bindings", [])
    if not all(
        isinstance(value, list)
        for value in (
            negative_oracles,
            source_designs,
            obligations,
            dependency_bindings,
            reset_bindings,
        )
    ):
        return None

    grouped_indices: dict[str, list[int]] = {}
    for oracle_index, oracle in enumerate(negative_oracles):
        if (
            isinstance(oracle, Mapping)
            and oracle.get("decision") == "executable_tc"
        ):
            grouped_indices.setdefault(
                str(oracle.get("linked_obligation_id", "")), []
            ).append(oracle_index)
    for obligation_id, oracle_indices in grouped_indices.items():
        if not obligation_id or len(oracle_indices) < 2:
            continue
        oracle_rows = [negative_oracles[index] for index in oracle_indices]
        if not all(isinstance(item, Mapping) for item in oracle_rows):
            continue
        scope_ids = [str(item.get("scope_obligation_id", "")) for item in oracle_rows]
        signal_ids = [str(item.get("signal_id", "")) for item in oracle_rows]
        shared_atom_ids = {str(item.get("linked_atom_id", "")) for item in oracle_rows}
        shared_planned_tc_ids = {
            str(item.get("planned_tc_or_gap", "")) for item in oracle_rows
        }
        if (
            len(set(scope_ids)) != len(scope_ids)
            or len(set(signal_ids)) != len(signal_ids)
            or len(shared_atom_ids) != 1
            or len(shared_planned_tc_ids) != 1
        ):
            continue
        original_atom_id = next(iter(shared_atom_ids))
        original_planned_tc_id = next(iter(shared_planned_tc_ids))

        obligation_matches = [
            (index, item)
            for index, item in enumerate(obligations)
            if isinstance(item, Mapping)
            and item.get("obligation_id") == obligation_id
        ]
        owner_matches = [
            (source_index, assertion_index, assertion)
            for source_index, source_design in enumerate(source_designs)
            if isinstance(source_design, Mapping)
            for assertion_index, assertion in enumerate(
                source_design.get("assertions", [])
            )
            if isinstance(assertion, Mapping)
            and assertion.get("atom_id") == original_atom_id
            and obligation_id in set(map(str, assertion.get("obligation_ids", [])))
        ]
        if len(obligation_matches) != 1 or len(owner_matches) != 1:
            continue
        obligation_index, obligation = obligation_matches[0]
        source_index, assertion_index, assertion = owner_matches[0]
        owner_source_row_id = str(source_designs[source_index].get("source_row_id", ""))
        owner_source_text = source_text_by_row.get(owner_source_row_id, "")
        if not owner_source_text:
            continue
        branch_count = len(oracle_rows)
        clause_arrays = {
            field: assertion.get(field, [])
            for field in ("condition_clauses", "action_clauses", "oracle_clauses")
        }
        if not all(
            isinstance(values, list) and len(values) == branch_count
            for values in clause_arrays.values()
        ):
            continue
        evidence = assertion.get("clause_evidence", [])
        if not isinstance(evidence, list) or len(evidence) != branch_count * 3:
            continue
        evidence_by_key: dict[tuple[str, int], Mapping[str, Any]] = {}
        evidence_valid = True
        for binding in evidence:
            if (
                not isinstance(binding, Mapping)
                or binding.get("clause_kind")
                not in {"condition", "action", "oracle"}
                or type(binding.get("clause_index")) is not int
            ):
                evidence_valid = False
                break
            key = (str(binding["clause_kind"]), int(binding["clause_index"]))
            if key in evidence_by_key or not 0 <= key[1] < branch_count:
                evidence_valid = False
                break
            evidence_by_key[key] = binding
        expected_keys = {
            (kind, index)
            for kind in ("condition", "action", "oracle")
            for index in range(branch_count)
        }
        if not evidence_valid or set(evidence_by_key) != expected_keys:
            continue
        if list(map(str, obligation.get("scope_obligation_ids", []))) != scope_ids:
            continue
        if (
            obligation.get("linked_atom_id") != original_atom_id
            or obligation.get("planned_tc_id") != original_planned_tc_id
            or any(
                isinstance(binding, Mapping)
                and binding.get("obligation_id") == obligation_id
                for binding in reset_bindings
            )
        ):
            continue

        existing_assertion_ids = {
            str(item.get("assertion_id", ""))
            for source_design in source_designs
            if isinstance(source_design, Mapping)
            for item in source_design.get("assertions", [])
            if isinstance(item, Mapping)
        }
        existing_atom_ids = {
            str(item.get("atom_id", ""))
            for source_design in source_designs
            if isinstance(source_design, Mapping)
            for item in source_design.get("assertions", [])
            if isinstance(item, Mapping)
        }
        existing_obligation_ids = {
            str(item.get("obligation_id", ""))
            for item in obligations
            if isinstance(item, Mapping)
        }
        existing_tc_ids = {
            str(item.get("planned_tc_id", ""))
            for item in obligations
            if isinstance(item, Mapping)
        }
        new_assertions: list[dict[str, Any]] = []
        new_obligations: list[dict[str, Any]] = []
        new_oracles: list[dict[str, Any]] = []
        new_assertion_ids: list[str] = []
        new_atom_ids: list[str] = []
        new_obligation_ids: list[str] = []
        new_tc_ids: list[str] = []
        safe = True
        for branch_index, oracle in enumerate(oracle_rows):
            suffix = re.sub(
                r"[^A-Za-z0-9]+",
                "-",
                scope_ids[branch_index],
            ).strip("-")
            assertion_id = f"{assertion.get('assertion_id')}-{suffix}"
            atom_id = f"{original_atom_id}-{suffix}"
            split_obligation_id = f"{obligation_id}-{suffix}"
            planned_tc_id = f"{original_planned_tc_id}-{suffix}"
            if (
                assertion_id in existing_assertion_ids
                or atom_id in existing_atom_ids
                or split_obligation_id in existing_obligation_ids
                or planned_tc_id in existing_tc_ids
                or not suffix
            ):
                safe = False
                break
            split_assertion = copy.deepcopy(dict(assertion))
            condition = str(clause_arrays["condition_clauses"][branch_index])
            action = str(clause_arrays["action_clauses"][branch_index])
            oracle_clause = str(clause_arrays["oracle_clauses"][branch_index])
            split_assertion.update(
                {
                    "assertion_id": assertion_id,
                    "canonical_statement": f"{condition} {oracle_clause}",
                    "condition_clauses": [condition],
                    "action_clauses": [action],
                    "oracle_clauses": [oracle_clause],
                    "atom_id": atom_id,
                    "obligation_ids": [split_obligation_id],
                    "disposition_rationale": (
                        f"Отдельная атомарная ветвь source-signal {signal_ids[branch_index]}."
                    ),
                }
            )
            split_evidence: list[dict[str, Any]] = []
            for kind in ("condition", "action", "oracle"):
                binding = copy.deepcopy(dict(evidence_by_key[(kind, branch_index)]))
                binding["clause_index"] = 0
                split_evidence.append(binding)
            for dependency in dependency_bindings:
                if (
                    not isinstance(dependency, Mapping)
                    or str(assertion.get("assertion_id", ""))
                    not in set(map(str, dependency.get("linked_assertion_ids", [])))
                    or owner_source_row_id
                    not in set(map(str, dependency.get("source_row_ids", [])))
                ):
                    continue
                dependency_fragments = list(
                    map(str, dependency.get("exact_source_fragments", []))
                )
                if any(
                    binding.get("source_row_id") == owner_source_row_id
                    and any(
                        fragment in str(binding.get("exact_source_fragment", ""))
                        for fragment in dependency_fragments
                    )
                    for binding in split_evidence
                    if isinstance(binding, Mapping)
                ):
                    continue
                span_candidates: list[tuple[int, int, int, int]] = []
                for split_evidence_index, binding in enumerate(split_evidence):
                    if binding.get("source_row_id") != owner_source_row_id:
                        continue
                    current_fragment = str(binding.get("exact_source_fragment", ""))
                    current_start = owner_source_text.find(current_fragment)
                    if not current_fragment or current_start < 0:
                        continue
                    for dependency_fragment in dependency_fragments:
                        dependency_start = owner_source_text.find(dependency_fragment)
                        if dependency_start < 0:
                            continue
                        span_start = min(current_start, dependency_start)
                        span_end = max(
                            current_start + len(current_fragment),
                            dependency_start + len(dependency_fragment),
                        )
                        span_candidates.append(
                            (
                                span_end - span_start,
                                split_evidence_index,
                                span_start,
                                span_end,
                            )
                        )
                if not span_candidates:
                    safe = False
                    break
                (
                    _span_length,
                    split_evidence_index,
                    span_start,
                    span_end,
                ) = min(span_candidates)
                split_evidence[split_evidence_index]["exact_source_fragment"] = (
                    owner_source_text[span_start:span_end]
                )
            if not safe:
                break
            split_assertion["clause_evidence"] = split_evidence
            clarification_bindings: list[dict[str, Any]] = []
            for binding in assertion.get("clarification_clause_bindings", []):
                if (
                    not isinstance(binding, Mapping)
                    or binding.get("clause_kind")
                    not in {"condition", "action", "oracle"}
                    or binding.get("clause_index") != branch_index
                ):
                    continue
                split_binding = copy.deepcopy(dict(binding))
                split_binding["clause_index"] = 0
                clarification_bindings.append(split_binding)
            split_assertion["clarification_clause_bindings"] = clarification_bindings

            split_obligation = copy.deepcopy(dict(obligation))
            split_obligation.update(
                {
                    "obligation_id": split_obligation_id,
                    "linked_atom_id": atom_id,
                    "obligation_class": str(oracle.get("restriction_type", "")),
                    "required_behavior": oracle_clause,
                    "planned_tc_id": planned_tc_id,
                    "planned_check": action,
                    "input_class": str(oracle.get("negative_class", "")),
                    "single_expected_behavior": oracle_clause,
                    "test_data": str(oracle.get("representative_invalid_value", "")),
                    "scope_obligation_ids": [scope_ids[branch_index]],
                }
            )
            split_oracle = copy.deepcopy(dict(oracle))
            split_oracle.update(
                {
                    "planned_tc_or_gap": planned_tc_id,
                    "linked_atom_id": atom_id,
                    "linked_obligation_id": split_obligation_id,
                }
            )
            new_assertions.append(split_assertion)
            new_obligations.append(split_obligation)
            new_oracles.append(split_oracle)
            new_assertion_ids.append(assertion_id)
            new_atom_ids.append(atom_id)
            new_obligation_ids.append(split_obligation_id)
            new_tc_ids.append(planned_tc_id)
        if not safe:
            continue

        canonical_dependency_bindings = copy.deepcopy(dependency_bindings)
        for binding in canonical_dependency_bindings:
            if not isinstance(binding, dict):
                continue
            linked_assertions = list(map(str, binding.get("linked_assertion_ids", [])))
            if str(assertion.get("assertion_id", "")) not in linked_assertions:
                continue
            position = linked_assertions.index(str(assertion.get("assertion_id", "")))
            for field, original, replacements in (
                ("linked_assertion_ids", str(assertion.get("assertion_id", "")), new_assertion_ids),
                ("linked_atom_ids", original_atom_id, new_atom_ids),
                ("linked_obligation_ids", obligation_id, new_obligation_ids),
            ):
                values = list(map(str, binding.get(field, [])))
                if original not in values or values.index(original) != position:
                    safe = False
                    break
                binding[field] = [
                    *values[:position],
                    *replacements,
                    *values[position + 1 :],
                ]
            if not safe:
                break
        if not safe:
            continue
        return {
            "source_index": source_index,
            "assertion_index": assertion_index,
            "obligation_index": obligation_index,
            "oracle_indices": oracle_indices,
            "original_assertion_id": str(assertion.get("assertion_id", "")),
            "original_obligation_id": obligation_id,
            "scope_obligation_ids": scope_ids,
            "new_assertions": new_assertions,
            "new_obligations": new_obligations,
            "new_oracles": new_oracles,
            "canonical_dependency_bindings": canonical_dependency_bindings,
        }
    return None


def _combined_calibration_allowed_class_projection(
    payload: Mapping[str, Any],
    *,
    context: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Split a literal valid/invalid calibration pair into two TC chains.

    A model may preserve both values in one candidate TC even though the bridge
    contract requires the source-backed allowed class to remain executable on its
    own.  The repair is allowed only for a numeric length restriction whose valid
    and invalid values, acceptance text, and calibration text are all explicit in
    the model output and whose two values can be checked against the source rule.
    """

    if context is None:
        return None
    source_text_by_row = {
        str(row.get("source_row_id", "")): str(row.get("bounded_source_text", ""))
        for row in context.get("source_rows", [])
        if isinstance(row, Mapping)
    }
    source_designs = payload.get("source_designs", [])
    obligations = payload.get("obligations", [])
    negative_oracles = payload.get("negative_oracles", [])
    dependency_bindings = payload.get("dependency_bindings", [])
    if not all(
        isinstance(value, list)
        for value in (
            source_designs,
            obligations,
            negative_oracles,
            dependency_bindings,
        )
    ):
        return None

    repeat_words = {
        "трех": 3,
        "трёх": 3,
        "четырех": 4,
        "четырёх": 4,
        "пяти": 5,
        "шести": 6,
        "семи": 7,
        "восьми": 8,
        "девяти": 9,
        "десяти": 10,
    }
    existing_assertion_ids = {
        str(assertion.get("assertion_id", ""))
        for source_design in source_designs
        if isinstance(source_design, Mapping)
        for assertion in source_design.get("assertions", [])
        if isinstance(assertion, Mapping)
    }
    existing_atom_ids = {
        str(assertion.get("atom_id", ""))
        for source_design in source_designs
        if isinstance(source_design, Mapping)
        for assertion in source_design.get("assertions", [])
        if isinstance(assertion, Mapping)
    }
    existing_obligation_ids = {
        str(obligation.get("obligation_id", ""))
        for obligation in obligations
        if isinstance(obligation, Mapping)
    }
    existing_tc_ids = {
        str(obligation.get("planned_tc_id", ""))
        for obligation in obligations
        if isinstance(obligation, Mapping)
    }

    for oracle_index, oracle in enumerate(negative_oracles):
        if (
            not isinstance(oracle, Mapping)
            or oracle.get("decision") != "candidate_tc_required"
            or oracle.get("oracle_status") != "ui-calibration-required"
            or oracle.get("restriction_type") != "format"
        ):
            continue
        obligation_id = str(oracle.get("linked_obligation_id", ""))
        atom_id = str(oracle.get("linked_atom_id", ""))
        obligation_matches = [
            (index, item)
            for index, item in enumerate(obligations)
            if isinstance(item, Mapping)
            and item.get("obligation_id") == obligation_id
        ]
        assertion_matches = [
            (source_index, assertion_index, assertion)
            for source_index, source_design in enumerate(source_designs)
            if isinstance(source_design, Mapping)
            for assertion_index, assertion in enumerate(
                source_design.get("assertions", [])
            )
            if isinstance(assertion, Mapping)
            and assertion.get("atom_id") == atom_id
            and obligation_id in set(map(str, assertion.get("obligation_ids", [])))
        ]
        if len(obligation_matches) != 1 or len(assertion_matches) != 1:
            continue
        obligation_index, obligation = obligation_matches[0]
        source_index, assertion_index, assertion = assertion_matches[0]
        if (
            obligation.get("check_type") != "negative"
            or obligation.get("source_property_id") != "none_required"
            or list(map(str, obligation.get("scope_obligation_ids", [])))
            != [str(oracle.get("scope_obligation_id", ""))]
        ):
            continue
        source_row_id = str(source_designs[source_index].get("source_row_id", ""))
        source_text = source_text_by_row.get(source_row_id, "")
        source_statement = str(oracle.get("source_statement", ""))
        invalid_value = str(oracle.get("representative_invalid_value", ""))
        test_values = [
            value.strip()
            for value in str(obligation.get("test_data", "")).split(";")
            if value.strip()
        ]
        if (
            len(test_values) != 2
            or len(set(test_values)) != 2
            or test_values[1] != invalid_value
            or not source_statement
            or source_statement not in source_text
        ):
            continue
        allowed_value = test_values[0]
        length_match = re.search(
            r"только\s+(\d+)\s+числов",
            source_statement.casefold(),
        )
        repeat_match = re.search(
            r"не\s+должно\s+быть\s+([^ \s]+)\s+одинаковых\s+цифр\s+подряд",
            source_statement.casefold(),
        )
        if length_match is None or repeat_match is None:
            continue
        required_length = int(length_match.group(1))
        repeat_length = repeat_words.get(repeat_match.group(1))
        if repeat_length is None:
            continue

        def has_repeated_run(value: str) -> bool:
            return any(
                len(set(value[index : index + repeat_length])) == 1
                for index in range(len(value) - repeat_length + 1)
            )

        if (
            not allowed_value.isdigit()
            or len(allowed_value) != required_length
            or has_repeated_run(allowed_value)
            or not invalid_value.isdigit()
            or len(invalid_value) != required_length
            or not has_repeated_run(invalid_value)
        ):
            continue
        action_text = " ".join(map(str, assertion.get("action_clauses", [])))
        oracle_text = " ".join(map(str, assertion.get("oracle_clauses", [])))
        if not (
            allowed_value in action_text
            and invalid_value in action_text
            and allowed_value in oracle_text
            and invalid_value in oracle_text
            and "допустим" in action_text.casefold()
            and "приним" in oracle_text.casefold()
            and "калибров" in oracle_text.casefold()
        ):
            continue

        scope_suffix = re.sub(
            r"[^A-Za-z0-9]+",
            "-",
            str(oracle.get("scope_obligation_id", "")),
        ).strip("-")
        positive_assertion_id = f"{assertion.get('assertion_id')}-POS"
        positive_atom_id = f"{atom_id}-POS"
        positive_obligation_id = f"{obligation_id}-POS"
        positive_tc_id = f"TC-POS-{scope_suffix}"
        if (
            not scope_suffix
            or positive_assertion_id in existing_assertion_ids
            or positive_atom_id in existing_atom_ids
            or positive_obligation_id in existing_obligation_ids
            or positive_tc_id in existing_tc_ids
        ):
            continue

        field_or_block = str(assertion.get("field_or_block", "")).strip()
        condition_clauses = copy.deepcopy(assertion.get("condition_clauses", []))
        if not isinstance(condition_clauses, list) or not condition_clauses:
            continue
        evidence = assertion.get("clause_evidence", [])
        if not isinstance(evidence, list):
            continue
        condition_evidence = [
            copy.deepcopy(dict(item))
            for item in evidence
            if isinstance(item, Mapping) and item.get("clause_kind") == "condition"
        ]
        if len(condition_evidence) != len(condition_clauses):
            continue
        positive_action = f"Ввести в поле «{field_or_block}» допустимое значение «{allowed_value}»."
        positive_oracle = f"Поле «{field_or_block}» принимает значение «{allowed_value}»."
        negative_action = f"Ввести в поле «{field_or_block}» недопустимое значение «{invalid_value}»."
        negative_oracle = (
            f"Точный UI-отклик для значения «{invalid_value}» требует "
            "калибровки."
        )

        positive_assertion = copy.deepcopy(dict(assertion))
        positive_assertion.update(
            {
                "assertion_id": positive_assertion_id,
                "canonical_statement": positive_oracle,
                "polarity": "positive",
                "action_clauses": [positive_action],
                "oracle_clauses": [positive_oracle],
                "clause_evidence": [
                    *condition_evidence,
                    {
                        "clause_kind": "action",
                        "clause_index": 0,
                        "source_row_id": source_row_id,
                        "exact_source_fragment": source_statement,
                    },
                    {
                        "clause_kind": "oracle",
                        "clause_index": 0,
                        "source_row_id": source_row_id,
                        "exact_source_fragment": source_statement,
                    },
                ],
                "atom_id": positive_atom_id,
                "obligation_ids": [positive_obligation_id],
                "disposition_rationale": (
                    "Допустимый класс отделён от UI-calibration для "
                    "недопустимого класса."
                ),
            }
        )
        negative_assertion = copy.deepcopy(dict(assertion))
        negative_assertion.update(
            {
                "canonical_statement": negative_oracle,
                "action_clauses": [negative_action],
                "oracle_clauses": [negative_oracle],
                "clause_evidence": [
                    *condition_evidence,
                    {
                        "clause_kind": "action",
                        "clause_index": 0,
                        "source_row_id": source_row_id,
                        "exact_source_fragment": source_statement,
                    },
                    {
                        "clause_kind": "oracle",
                        "clause_index": 0,
                        "source_row_id": source_row_id,
                        "exact_source_fragment": source_statement,
                    },
                ],
                "disposition_rationale": (
                    "Недопустимый класс сохранён как UI-calibration candidate "
                    "без выдуманного отклика."
                ),
            }
        )
        positive_obligation = copy.deepcopy(dict(obligation))
        positive_obligation.update(
            {
                "obligation_id": positive_obligation_id,
                "linked_atom_id": positive_atom_id,
                "obligation_class": "format",
                "required_behavior": positive_oracle,
                "planned_tc_id": positive_tc_id,
                "review_notes": "source-backed allowed-class companion",
                "planned_check": positive_action,
                "check_type": "positive",
                "coverage_class": "positive-allowed-class",
                "input_class": "valid-format",
                "single_expected_behavior": positive_oracle,
                "oracle_source": "source_statement",
                "test_data": allowed_value,
                "scope_obligation_ids": [],
            }
        )
        negative_obligation = copy.deepcopy(dict(obligation))
        negative_obligation.update(
            {
                "required_behavior": negative_oracle,
                "planned_check": negative_action,
                "single_expected_behavior": negative_oracle,
                "oracle_source": "not_found",
                "test_data": invalid_value,
            }
        )

        canonical_dependencies = copy.deepcopy(dependency_bindings)
        safe = True
        for binding in canonical_dependencies:
            if not isinstance(binding, dict):
                continue
            linked_assertions = list(map(str, binding.get("linked_assertion_ids", [])))
            original_assertion_id = str(assertion.get("assertion_id", ""))
            if original_assertion_id not in linked_assertions:
                continue
            position = linked_assertions.index(original_assertion_id)
            for field, original, replacements in (
                (
                    "linked_assertion_ids",
                    original_assertion_id,
                    [positive_assertion_id, original_assertion_id],
                ),
                ("linked_atom_ids", atom_id, [positive_atom_id, atom_id]),
                (
                    "linked_obligation_ids",
                    obligation_id,
                    [positive_obligation_id, obligation_id],
                ),
            ):
                values = list(map(str, binding.get(field, [])))
                if original not in values or values.index(original) != position:
                    safe = False
                    break
                binding[field] = [
                    *values[:position],
                    *replacements,
                    *values[position + 1 :],
                ]
            if not safe:
                break
        if not safe:
            continue
        return {
            "source_index": source_index,
            "assertion_index": assertion_index,
            "obligation_index": obligation_index,
            "oracle_index": oracle_index,
            "scope_obligation_id": str(oracle.get("scope_obligation_id", "")),
            "original_assertion_id": str(assertion.get("assertion_id", "")),
            "positive_assertion": positive_assertion,
            "negative_assertion": negative_assertion,
            "positive_obligation": positive_obligation,
            "negative_obligation": negative_obligation,
            "canonical_dependency_bindings": canonical_dependencies,
        }
    return None


def _clarification_exclusion_oracle_projections(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Keep a scope-exclusion clarification out of literal FT clause evidence.

    A requirement-code clarification may exclude one internal sibling effect while
    the same source row retains an observable ``если ..., то ...`` effect.  Models
    sometimes copy the clarification answer into the executable oracle even though
    that answer is not literal XHTML row text.  Reusing the row's single literal
    system-effect action as the oracle is mechanically safe only when the same row
    owns a scope-excluded dependency and the clarification is bound to that oracle.
    """

    clarifications = {
        str(item.get("clarification_id", "")): item
        for item in context.get("approved_clarifications", [])
        if isinstance(item, Mapping)
    }
    rows_by_id = {
        str(item.get("source_row_id", "")): str(
            item.get("bounded_source_text", "")
        )
        for item in context.get("source_rows", [])
        if isinstance(item, Mapping)
    }
    scope_excluded_rows = {
        str(source_row_id)
        for dependency in boundary.get("dependencies", [])
        if isinstance(dependency, Mapping)
        and dependency.get("resolution") == "scope-excluded"
        for source_row_id in dependency.get("source_row_ids", [])
    }
    projections: list[dict[str, Any]] = []
    for source_index, source_design in enumerate(payload.get("source_designs", [])):
        if not isinstance(source_design, Mapping):
            continue
        source_row_id = str(source_design.get("source_row_id", ""))
        source_text = rows_by_id.get(source_row_id, "")
        if source_row_id not in scope_excluded_rows or not source_text:
            continue
        assertions = source_design.get("assertions", [])
        if not isinstance(assertions, list):
            continue
        for assertion_index, assertion in enumerate(assertions):
            if (
                not isinstance(assertion, Mapping)
                or assertion.get("semantic_disposition") != "testable"
            ):
                continue
            actions = assertion.get("action_clauses", [])
            oracles = assertion.get("oracle_clauses", [])
            evidence = assertion.get("clause_evidence", [])
            bindings = assertion.get("clarification_clause_bindings", [])
            assertion_codes = set(map(str, assertion.get("requirement_codes", [])))
            if not all(
                isinstance(value, list)
                for value in (actions, oracles, evidence, bindings)
            ):
                continue
            action_candidates: list[tuple[str, str]] = []
            for action_index, action in enumerate(actions):
                action_text = str(action)
                if not action_text.casefold().startswith("то "):
                    continue
                matching_evidence = [
                    item
                    for item in evidence
                    if isinstance(item, Mapping)
                    and item.get("clause_kind") == "action"
                    and item.get("clause_index") == action_index
                    and item.get("source_row_id") == source_row_id
                    and str(item.get("exact_source_fragment", "")) in source_text
                ]
                if len(matching_evidence) == 1:
                    action_candidates.append(
                        (
                            action_text,
                            str(matching_evidence[0]["exact_source_fragment"]),
                        )
                    )
            if len(action_candidates) != 1:
                continue
            canonical_oracle, canonical_evidence = action_candidates[0]
            for binding in bindings:
                if (
                    not isinstance(binding, Mapping)
                    or binding.get("binding_scope") != "requirement-code"
                    or binding.get("clause_kind") != "oracle"
                    or type(binding.get("clause_index")) is not int
                ):
                    continue
                clarification_id = str(binding.get("clarification_id", ""))
                clarification = clarifications.get(clarification_id)
                oracle_index = int(binding["clause_index"])
                binding_codes = set(map(str, binding.get("requirement_codes", [])))
                if (
                    clarification is None
                    or oracle_index < 0
                    or oracle_index >= len(oracles)
                    or not binding_codes
                    or not binding_codes.issubset(assertion_codes)
                    or not binding_codes.issubset(
                        set(map(str, clarification.get("requirement_codes", [])))
                    )
                ):
                    continue
                exact_answer = str(clarification.get("exact_answer", ""))
                if not exact_answer or str(oracles[oracle_index]) != exact_answer:
                    continue
                evidence_matches = [
                    (index, item)
                    for index, item in enumerate(evidence)
                    if isinstance(item, Mapping)
                    and item.get("clause_kind") == "oracle"
                    and item.get("clause_index") == oracle_index
                    and item.get("source_row_id") == source_row_id
                    and item.get("exact_source_fragment") == exact_answer
                    and exact_answer not in source_text
                ]
                if len(evidence_matches) != 1:
                    continue
                evidence_index, _ = evidence_matches[0]
                projections.append(
                    {
                        "source_index": source_index,
                        "assertion_index": assertion_index,
                        "evidence_index": evidence_index,
                        "oracle_index": oracle_index,
                        "source_row_id": source_row_id,
                        "assertion_id": str(assertion.get("assertion_id", "")),
                        "clarification_id": clarification_id,
                        "canonical_oracle": canonical_oracle,
                        "canonical_evidence": canonical_evidence,
                    }
                )
    return projections


def _semantic_transport_header_projection(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Return canonical copy-only bridge fields for one current boundary."""

    scope_boundary = boundary.get("scope_boundary", {})
    if not isinstance(scope_boundary, Mapping):
        return None
    expected = {
        "prepared_context_sha256": prepared_context_sha256(context),
        "scope_boundary_decision_sha256": canonical_payload_sha256(boundary),
        "scope_summary": boundary.get("scope_summary"),
        "included": copy.deepcopy(scope_boundary.get("include")),
        "excluded": copy.deepcopy(scope_boundary.get("exclude")),
        "mockup_locators": copy.deepcopy(boundary.get("mockup_locators")),
    }
    changed_fields = [
        field for field, value in expected.items() if payload.get(field) != value
    ]
    if not changed_fields:
        return None
    return {
        "expected": expected,
        "changed_fields": changed_fields,
        "previous_value_sha256": canonical_payload_sha256(
            {field: payload.get(field) for field in expected}
        ),
    }


def _dependency_transport_projections(
    payload: Mapping[str, Any],
    boundary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Canonicalize copy-only dependency fields without changing semantic links."""

    bindings = payload.get("dependency_bindings", [])
    authoritative = boundary.get("dependencies", [])
    if not isinstance(bindings, list) or not isinstance(authoritative, list):
        return []
    if len(bindings) != len(authoritative):
        return []
    copied_fields = (
        "dependency_id",
        "kind",
        "name",
        "source_row_ids",
        "resolution",
        "target_source_row_ids",
        "exact_source_fragments",
        "gap_ids",
        "blocking",
        "rationale",
    )
    projections: list[dict[str, Any]] = []
    for index, (binding, expected) in enumerate(zip(bindings, authoritative, strict=True)):
        if not isinstance(binding, Mapping) or not isinstance(expected, Mapping):
            continue
        if binding.get("dependency_id") != expected.get("dependency_id"):
            continue
        changed_fields = [
            field
            for field in copied_fields
            if binding.get(field) != expected.get(field)
        ]
        if not changed_fields:
            continue
        projections.append(
            {
                "binding_index": index,
                "dependency_id": str(expected.get("dependency_id", "")),
                "changed_fields": changed_fields,
                "canonical_fields": {
                    field: copy.deepcopy(expected.get(field))
                    for field in copied_fields
                },
                "previous_value_sha256": canonical_payload_sha256(
                    {field: binding.get(field) for field in copied_fields}
                ),
            }
        )
    return projections


def _missing_scope_excluded_dependency_projection(
    payload: Mapping[str, Any],
    boundary: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Restore omitted not-applicable bindings and nothing executable."""

    bindings = payload.get("dependency_bindings", [])
    authoritative = boundary.get("dependencies", [])
    if not isinstance(bindings, list) or not isinstance(authoritative, list):
        return None
    if any(not isinstance(item, Mapping) for item in bindings + authoritative):
        return None
    authoritative_by_id = {
        str(item.get("dependency_id", "")): item for item in authoritative
    }
    binding_by_id = {
        str(item.get("dependency_id", "")): item for item in bindings
    }
    if (
        len(authoritative_by_id) != len(authoritative)
        or len(binding_by_id) != len(bindings)
        or not set(binding_by_id).issubset(authoritative_by_id)
    ):
        return None
    expected_existing_order = [
        str(item.get("dependency_id", ""))
        for item in authoritative
        if str(item.get("dependency_id", "")) in binding_by_id
    ]
    if list(binding_by_id) != expected_existing_order:
        return None
    missing = [
        item
        for item in authoritative
        if str(item.get("dependency_id", "")) not in binding_by_id
    ]
    if not missing or any(item.get("resolution") != "scope-excluded" for item in missing):
        return None
    canonical: list[dict[str, Any]] = []
    for dependency in authoritative:
        dependency_id = str(dependency.get("dependency_id", ""))
        existing = binding_by_id.get(dependency_id)
        if existing is not None:
            canonical.append(copy.deepcopy(dict(existing)))
            continue
        synthesized = copy.deepcopy(dict(dependency))
        synthesized.update(
            {
                "semantic_disposition": "not-applicable",
                "linked_assertion_ids": [],
                "linked_atom_ids": [],
                "linked_obligation_ids": [],
                "mapping_rationale": (
                    "Authoritative scope boundary explicitly excludes this dependency; "
                    "there are no executable semantic links."
                ),
            }
        )
        canonical.append(synthesized)
    return {
        "canonical_bindings": canonical,
        "missing_dependency_ids": [
            str(item.get("dependency_id", "")) for item in missing
        ],
        "previous_value_sha256": canonical_payload_sha256(bindings),
    }


def _clarification_missing_code_projections(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Recover one provably local clarification code and its typed evidence.

    A model may split one source-row requirement into sibling assertions and
    attach the clarification to the behavioral sibling while leaving the code
    on the sibling that first quoted it.  Inheritance is safe only when the
    clarification/row intersection contains exactly one code and the row has
    exactly one canonical evidence payload for that code.
    """

    clarifications = {
        str(item.get("clarification_id", "")): item
        for item in context.get("approved_clarifications", [])
        if isinstance(item, Mapping)
    }
    projections: list[dict[str, Any]] = []
    source_designs = payload.get("source_designs", [])
    if not isinstance(source_designs, list):
        return projections
    for source_index, source_design in enumerate(source_designs):
        if not isinstance(source_design, Mapping):
            continue
        source_row_id = str(source_design.get("source_row_id", ""))
        row_codes = set(map(str, source_design.get("requirement_codes", [])))
        assertions = source_design.get("assertions", [])
        if not isinstance(assertions, list):
            continue
        evidence_by_code: dict[str, dict[str, Mapping[str, Any]]] = {}
        for donor_assertion in assertions:
            if not isinstance(donor_assertion, Mapping):
                continue
            donor_evidence = donor_assertion.get("requirement_code_evidence", [])
            if not isinstance(donor_evidence, list):
                continue
            for evidence in donor_evidence:
                if (
                    not isinstance(evidence, Mapping)
                    or str(evidence.get("source_row_id", "")) != source_row_id
                ):
                    continue
                code = str(evidence.get("requirement_code", ""))
                evidence_by_code.setdefault(code, {})[
                    canonical_payload_sha256(evidence)
                ] = evidence
        for assertion_index, assertion in enumerate(assertions):
            if not isinstance(assertion, Mapping):
                continue
            assertion_codes = assertion.get("requirement_codes", [])
            bindings = assertion.get("clarification_clause_bindings", [])
            evidence = assertion.get("requirement_code_evidence", [])
            if (
                not isinstance(assertion_codes, list)
                or not isinstance(bindings, list)
                or not isinstance(evidence, list)
            ):
                continue
            for binding_index, binding in enumerate(bindings):
                if (
                    not isinstance(binding, Mapping)
                    or binding.get("binding_scope") != "requirement-code"
                    or not isinstance(binding.get("requirement_codes"), list)
                ):
                    continue
                clarification = clarifications.get(
                    str(binding.get("clarification_id", ""))
                )
                if clarification is None:
                    continue
                clarification_codes = set(
                    map(str, clarification.get("requirement_codes", []))
                )
                binding_codes = set(map(str, binding["requirement_codes"]))
                local_codes = set(map(str, assertion_codes))
                inherit_code = False
                if local_codes:
                    if binding_codes:
                        continue
                    candidates = clarification_codes & local_codes
                else:
                    candidates = clarification_codes & row_codes
                    if binding_codes:
                        candidates &= binding_codes
                    inherit_code = True
                if len(candidates) != 1:
                    continue
                code = next(iter(candidates))
                donor_variants = evidence_by_code.get(code, {})
                if inherit_code and len(donor_variants) != 1:
                    continue
                projections.append(
                    {
                        "source_index": source_index,
                        "assertion_index": assertion_index,
                        "binding_index": binding_index,
                        "source_row_id": source_row_id,
                        "assertion_id": str(assertion.get("assertion_id", "")),
                        "clarification_id": str(
                            binding.get("clarification_id", "")
                        ),
                        "requirement_code": code,
                        "inherit_code": inherit_code,
                        "canonical_evidence": (
                            copy.deepcopy(next(iter(donor_variants.values())))
                            if inherit_code
                            else None
                        ),
                    }
                )
    return projections


def _typed_interpretation_support_alias_projections(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Locate model aliases that mislabel a registered interpretation as row text."""

    try:
        properties = {
            str(item["source_property_id"]): item
            for item in _typed_field_property_registry(context)
        }
    except SemanticDesignBridgeError:
        return []
    result: list[dict[str, Any]] = []
    source_designs = payload.get("source_designs", [])
    if not isinstance(source_designs, list):
        return result
    for source_index, source_design in enumerate(source_designs):
        if not isinstance(source_design, Mapping):
            continue
        assertions = source_design.get("assertions", [])
        if not isinstance(assertions, list):
            continue
        for assertion_index, assertion in enumerate(assertions):
            if not isinstance(assertion, Mapping):
                continue
            property_record = properties.get(
                str(assertion.get("source_property_id", ""))
            )
            supporting = assertion.get("supporting_source_bindings", [])
            if not isinstance(property_record, Mapping) or not isinstance(
                supporting, list
            ):
                continue
            for binding_index, binding in enumerate(supporting):
                if (
                    isinstance(binding, Mapping)
                    and str(binding.get("source_row_id", ""))
                    == str(property_record.get("header_source_row_id", ""))
                    and binding.get("exact_source_fragment")
                    == property_record.get("interpretation_source_fragment")
                ):
                    result.append(
                        {
                            "source_index": source_index,
                            "assertion_index": assertion_index,
                            "binding_index": binding_index,
                            "assertion_id": str(assertion.get("assertion_id", "")),
                            "source_property_id": str(
                                assertion.get("source_property_id", "")
                            ),
                            "header_source_row_id": str(
                                property_record.get("header_source_row_id", "")
                            ),
                            "interpretation_source": str(
                                property_record.get("interpretation_source", "")
                            ),
                        }
                    )
    return result


def _typed_property_missing_literal_evidence_projections(
    payload: Mapping[str, Any],
    context: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Bind a known typed cell to one existing same-row clause literal span.

    The repair is intentionally narrow: the model must already own the exact
    registered ``source_property_id`` on its authoritative source row and must
    already provide a valid literal clause anchor from that row.  The runner
    only expands that anchor to a contiguous source span containing the exact
    typed-cell value.  Unknown properties, cross-row ownership and evidence
    that explicitly names a different typed-cell value remain fail-closed.
    """

    try:
        property_registry = _typed_field_property_registry(context)
    except SemanticDesignBridgeError:
        return []
    properties = {
        str(item["source_property_id"]): item for item in property_registry
    }
    typed_values_by_row: dict[str, set[str]] = defaultdict(set)
    for item in property_registry:
        typed_values_by_row[str(item["source_row_id"])].add(
            str(item["source_value"])
        )
    rows_by_id = {
        str(row.get("source_row_id", "")): row
        for row in context.get("source_rows", [])
        if isinstance(row, Mapping)
    }

    projections: list[dict[str, Any]] = []
    source_designs = payload.get("source_designs", [])
    if not isinstance(source_designs, list):
        return projections
    clause_priority = {"action": 0, "oracle": 1, "condition": 2}
    for source_index, source_design in enumerate(source_designs):
        if not isinstance(source_design, Mapping):
            continue
        owner_row_id = str(source_design.get("source_row_id", ""))
        assertions = source_design.get("assertions", [])
        if not isinstance(assertions, list):
            continue
        for assertion_index, assertion in enumerate(assertions):
            if (
                not isinstance(assertion, Mapping)
                or assertion.get("semantic_disposition") != "testable"
            ):
                continue
            property_id = str(assertion.get("source_property_id", ""))
            property_record = properties.get(property_id)
            if (
                property_record is None
                or str(property_record["source_row_id"]) != owner_row_id
            ):
                continue
            exact_anchor = str(property_record["source_value"])
            if any(
                evidence_row_id == owner_row_id
                and exact_anchor in evidence_fragment
                for evidence_row_id, evidence_fragment in _assertion_literal_evidence(
                    assertion
                )
            ):
                continue
            source_row = rows_by_id.get(owner_row_id)
            source_text = (
                str(source_row.get("bounded_source_text", ""))
                if isinstance(source_row, Mapping)
                else ""
            )
            if not source_text or exact_anchor not in source_text:
                continue
            clause_evidence = assertion.get("clause_evidence", [])
            if not isinstance(clause_evidence, list):
                continue
            conflicting_values = typed_values_by_row[owner_row_id] - {
                exact_anchor
            }
            candidates: list[tuple[int, int, int, str]] = []
            anchor_starts: list[int] = []
            physical_cells = (
                source_row.get("physical_table_cells", [])
                if isinstance(source_row, Mapping)
                else []
            )
            if isinstance(physical_cells, list):
                cursor = 0
                for cell in physical_cells:
                    if not isinstance(cell, Mapping):
                        anchor_starts = []
                        break
                    cell_text = str(cell.get("bounded_source_text", ""))
                    cell_start = source_text.find(cell_text, cursor)
                    if not cell_text or cell_start < 0:
                        anchor_starts = []
                        break
                    if (
                        str(cell.get("source_cell_locator", ""))
                        == str(property_record["source_cell_locator"])
                    ):
                        if cell_text == exact_anchor:
                            anchor_starts = [cell_start]
                        break
                    cursor = cell_start + len(cell_text)
            search_from = 0
            if not anchor_starts:
                while True:
                    anchor_start = source_text.find(exact_anchor, search_from)
                    if anchor_start < 0:
                        break
                    anchor_starts.append(anchor_start)
                    search_from = anchor_start + max(1, len(exact_anchor))
            for evidence_index, binding in enumerate(clause_evidence):
                if (
                    not isinstance(binding, Mapping)
                    or str(binding.get("source_row_id", "")) != owner_row_id
                    or str(binding.get("clause_kind", ""))
                    not in clause_priority
                    or type(binding.get("clause_index")) is not int
                ):
                    continue
                fragment = str(binding.get("exact_source_fragment", ""))
                fragment_start = source_text.find(fragment)
                if (
                    not fragment
                    or fragment_start < 0
                    or fragment in conflicting_values
                ):
                    continue
                fragment_end = fragment_start + len(fragment)
                for anchor_start in anchor_starts:
                    span_start = min(anchor_start, fragment_start)
                    span_end = max(anchor_start + len(exact_anchor), fragment_end)
                    candidates.append(
                        (
                            clause_priority[str(binding["clause_kind"])],
                            span_end - span_start,
                            evidence_index,
                            source_text[span_start:span_end],
                        )
                    )
            if not candidates:
                continue
            _, _, evidence_index, canonical_span = min(candidates)
            binding = clause_evidence[evidence_index]
            assert isinstance(binding, Mapping)
            projections.append(
                {
                    "source_index": source_index,
                    "assertion_index": assertion_index,
                    "evidence_index": evidence_index,
                    "assertion_id": str(assertion.get("assertion_id", "")),
                    "source_property_id": property_id,
                    "source_row_id": owner_row_id,
                    "source_cell_locator": str(
                        property_record["source_cell_locator"]
                    ),
                    "source_value": exact_anchor,
                    "canonical_span": canonical_span,
                    "path": (
                        f"$.source_designs[{source_index}].assertions"
                        f"[{assertion_index}].clause_evidence"
                        f"[{evidence_index}].exact_source_fragment"
                    ),
                    "previous_value_sha256": hashlib.sha256(
                        str(binding.get("exact_source_fragment", "")).encode(
                            "utf-8"
                        )
                    ).hexdigest(),
                }
            )
    return projections


def semantic_design_transport_diagnostics(
    payload: Mapping[str, Any],
    *,
    context: Mapping[str, Any] | None = None,
    boundary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Aggregate transport and registry anomalies without changing model output."""

    findings: list[dict[str, Any]] = []
    source_designs = payload.get("source_designs", [])
    if isinstance(source_designs, list):
        for source_index, source_design in enumerate(source_designs):
            if not isinstance(source_design, Mapping):
                continue
            source_row_id = str(source_design.get("source_row_id", ""))
            assertions = source_design.get("assertions", [])
            if not isinstance(assertions, list):
                continue
            for assertion_index, assertion in enumerate(assertions):
                if not isinstance(assertion, Mapping):
                    continue
                assertion_codes = assertion.get("requirement_codes")
                clarification_bindings = assertion.get(
                    "clarification_clause_bindings"
                )
                if isinstance(assertion_codes, list) and isinstance(
                    clarification_bindings, list
                ):
                    assertion_code_set = set(map(str, assertion_codes))
                    for binding_index, binding in enumerate(clarification_bindings):
                        if (
                            isinstance(binding, Mapping)
                            and binding.get("clause_kind") == "canonical"
                            and binding.get("binding_scope") != "source-context"
                        ):
                            findings.append(
                                {
                                    "code": "clarification-canonical-binding-scope-invalid",
                                    "severity": "blocking",
                                    "path": (
                                        f"$.source_designs[{source_index}].assertions"
                                        f"[{assertion_index}].clarification_clause_bindings"
                                        f"[{binding_index}]"
                                    ),
                                    "source_row_id": source_row_id,
                                    "assertion_id": str(
                                        assertion.get("assertion_id", "")
                                    ),
                                    "clarification_id": str(
                                        binding.get("clarification_id", "")
                                    ),
                                    "binding_scope": str(
                                        binding.get("binding_scope", "")
                                    ),
                                }
                            )
                        if (
                            not isinstance(binding, Mapping)
                            or binding.get("binding_scope") != "requirement-code"
                            or not isinstance(binding.get("requirement_codes"), list)
                        ):
                            continue
                        binding_codes = list(map(str, binding["requirement_codes"]))
                        retained_codes = [
                            code for code in binding_codes if code in assertion_code_set
                        ]
                        if retained_codes != binding_codes:
                            findings.append(
                                {
                                    "code": "clarification-binding-code-overreach",
                                    "severity": (
                                        "repairable" if retained_codes else "blocking"
                                    ),
                                    "path": (
                                        f"$.source_designs[{source_index}].assertions"
                                        f"[{assertion_index}].clarification_clause_bindings"
                                        f"[{binding_index}].requirement_codes"
                                    ),
                                    "source_row_id": source_row_id,
                                    "assertion_id": str(
                                        assertion.get("assertion_id", "")
                                    ),
                                    "clarification_id": str(
                                        binding.get("clarification_id", "")
                                    ),
                                    "outside_requirement_codes": [
                                        code
                                        for code in binding_codes
                                        if code not in assertion_code_set
                                    ],
                                    "retained_requirement_codes": retained_codes,
                                }
                            )
                evidence = assertion.get("requirement_code_evidence")
                if not isinstance(evidence, list):
                    continue
                code_counts: dict[str, int] = {}
                for item in evidence:
                    if isinstance(item, Mapping):
                        code = str(item.get("requirement_code", ""))
                        code_counts[code] = code_counts.get(code, 0) + 1
                for code, count in code_counts.items():
                    if count < 2:
                        continue
                    redundant_index = _redundant_pdf_parity_index(
                        evidence,
                        requirement_code=code,
                        source_row_id=source_row_id,
                    )
                    findings.append(
                        {
                            "code": "duplicate-requirement-code-evidence",
                            "severity": (
                                "repairable"
                                if redundant_index is not None
                                else "blocking"
                            ),
                            "path": (
                                f"$.source_designs[{source_index}].assertions"
                                f"[{assertion_index}].requirement_code_evidence"
                            ),
                            "source_row_id": source_row_id,
                            "assertion_id": str(assertion.get("assertion_id", "")),
                            "requirement_code": code,
                            "duplicate_count": count,
                            "provenance_roles": [
                                str(item.get("provenance_role", ""))
                                for item in evidence
                                if isinstance(item, Mapping)
                                and str(item.get("requirement_code", "")) == code
                            ],
                        }
                    )
    assertion_obligation_ids: list[str] = []
    if isinstance(source_designs, list):
        for source_design in source_designs:
            if not isinstance(source_design, Mapping):
                continue
            assertions = source_design.get("assertions", [])
            if not isinstance(assertions, list):
                continue
            for assertion in assertions:
                if not isinstance(assertion, Mapping):
                    continue
                obligation_ids = assertion.get("obligation_ids", [])
                if isinstance(obligation_ids, list):
                    assertion_obligation_ids.extend(map(str, obligation_ids))
    registry = payload.get("obligations", [])
    registry_obligation_ids = (
        [
            str(item.get("obligation_id", ""))
            for item in registry
            if isinstance(item, Mapping)
        ]
        if isinstance(registry, list)
        else []
    )
    missing_obligations = sorted(
        set(assertion_obligation_ids) - set(registry_obligation_ids)
    )
    extra_obligations = sorted(
        set(registry_obligation_ids) - set(assertion_obligation_ids)
    )
    if missing_obligations or extra_obligations:
        findings.append(
            {
                "code": "obligation-registry-mismatch",
                "severity": "blocking",
                "path": "$.obligations",
                "assertion_obligation_count": len(assertion_obligation_ids),
                "registry_obligation_count": len(registry_obligation_ids),
                "missing_obligation_ids": missing_obligations,
                "extra_obligation_ids": extra_obligations,
            }
        )
    legacy_state_fields = (
        "initial_state_capture",
        "changed_state_setup",
        "pre_action_state_oracle",
        "state_relation",
    )
    legacy_state_obligations: list[dict[str, Any]] = []
    legacy_non_neutral_state_obligations: list[dict[str, Any]] = []
    if isinstance(registry, list):
        for obligation_index, obligation in enumerate(registry):
            if not isinstance(obligation, Mapping):
                continue
            present_fields = [
                field for field in legacy_state_fields if field in obligation
            ]
            if present_fields:
                legacy_state_obligations.append(
                    {
                        "obligation_index": obligation_index,
                        "obligation_id": str(obligation.get("obligation_id", "")),
                        "present_fields": present_fields,
                    }
                )
                non_neutral_fields = [
                    field
                    for field in present_fields
                    if obligation.get(field) != "none_required"
                ]
                if non_neutral_fields:
                    legacy_non_neutral_state_obligations.append(
                        {
                            "obligation_index": obligation_index,
                            "obligation_id": str(
                                obligation.get("obligation_id", "")
                            ),
                            "non_neutral_fields": non_neutral_fields,
                        }
                    )
    if legacy_state_obligations:
        findings.append(
            {
                "code": "legacy-obligation-state-fields",
                "severity": "blocking",
                "path": "$.obligations",
                "affected_obligation_count": len(legacy_state_obligations),
                "affected_obligations": legacy_state_obligations,
            }
        )
    if legacy_non_neutral_state_obligations:
        findings.append(
            {
                "code": "legacy-non-neutral-state-bindings",
                "severity": "blocking",
                "path": "$.obligations",
                "affected_obligation_count": len(
                    legacy_non_neutral_state_obligations
                ),
                "affected_obligations": legacy_non_neutral_state_obligations,
            }
        )
    if "reset_lifecycle_bindings" in payload:
        reset_lifecycle_bindings = payload.get("reset_lifecycle_bindings")
        if isinstance(reset_lifecycle_bindings, list) and isinstance(registry, list):
            binding_ids = [
                str(item.get("obligation_id", ""))
                for item in reset_lifecycle_bindings
                if isinstance(item, Mapping)
            ]
            duplicate_binding_ids = sorted(
                {
                    obligation_id
                    for obligation_id in binding_ids
                    if binding_ids.count(obligation_id) > 1
                }
            )
            expected_binding_ids = {
                str(item.get("obligation_id", ""))
                for item in registry
                if isinstance(item, Mapping)
                and (_state_change_class(item) or _lifecycle_readd_class(item))
            }
            actual_binding_ids = set(binding_ids)
            missing_binding_ids = sorted(expected_binding_ids - actual_binding_ids)
            foreign_binding_ids = sorted(actual_binding_ids - expected_binding_ids)
            if (
                duplicate_binding_ids
                or missing_binding_ids
                or foreign_binding_ids
            ):
                findings.append(
                    {
                        "code": "reset-lifecycle-registry-mismatch",
                        "severity": "blocking",
                        "path": "$.reset_lifecycle_bindings",
                        "duplicate_obligation_ids": duplicate_binding_ids,
                        "missing_obligation_ids": missing_binding_ids,
                        "foreign_obligation_ids": foreign_binding_ids,
                    }
                )
    dependency_bindings = payload.get("dependency_bindings", [])
    if isinstance(dependency_bindings, list):
        for binding_index, binding in enumerate(dependency_bindings):
            if not isinstance(binding, Mapping):
                continue
            projection = _provable_dependency_overlink_projection(payload, binding)
            if projection is None:
                continue
            findings.append(
                {
                    "code": "dependency-assertion-overlink",
                    "severity": "repairable",
                    "path": f"$.dependency_bindings[{binding_index}]",
                    "dependency_id": str(binding.get("dependency_id", "")),
                    "dropped_assertion_ids": projection[
                        "dropped_assertion_ids"
                    ],
                    "retained_assertion_ids": projection[
                        "linked_assertion_ids"
                    ],
                }
            )
    for projection in _oracle_scope_registry_projections(payload):
        findings.append(
            {
                "code": "obligation-oracle-scope-projection-mismatch",
                "severity": "repairable",
                "path": (
                    f"$.obligations[{projection['obligation_index']}]"
                    ".scope_obligation_ids"
                ),
                "obligation_id": projection["obligation_id"],
                "previous_scope_obligation_ids": projection[
                    "previous_scope_obligation_ids"
                ],
                "canonical_scope_obligation_ids": projection[
                    "scope_obligation_ids"
                ],
            }
        )
    for projection in _applicability_registry_projections(payload):
        findings.append(
            {
                "code": "applicability-registry-projection-mismatch",
                "severity": "repairable",
                "path": f"$.applicability[{projection['row_index']}]",
                "dimension": projection["dimension"],
                "canonical_applicable": projection["applicable"],
                "canonical_linked_atom_count": len(projection["linked_atoms"]),
                "canonical_linked_test_case_count": len(
                    projection["linked_test_cases"]
                ),
            }
        )
    for projection in _external_dynamic_coverage_projections(payload):
        findings.append(
            {
                "code": "external-dynamic-static-coverage-alias",
                "severity": "repairable",
                "path": (
                    f"$.obligations[{projection['obligation_index']}]"
                    ".dictionary_coverage"
                ),
                "obligation_id": projection["obligation_id"],
                "canonical_coverage": projection["dictionary_coverage"],
            }
        )
    for projection in _candidate_oracle_source_alias_projections(payload):
        findings.append(
            {
                "code": "candidate-oracle-source-sentinel-alias",
                "severity": "repairable",
                "path": projection["path"],
                "canonical_source": projection["canonical_source"],
                "owner_id": projection.get(
                    "signal_id", projection.get("obligation_id", "")
                ),
            }
        )
    if context is not None:
        for projection in _typed_interpretation_support_alias_projections(
            payload,
            context,
        ):
            findings.append(
                {
                    "code": "typed-interpretation-mislabeled-as-row-support",
                    "severity": "repairable",
                    "path": (
                        f"$.source_designs[{projection['source_index']}].assertions"
                        f"[{projection['assertion_index']}].supporting_source_bindings"
                        f"[{projection['binding_index']}]"
                    ),
                    "assertion_id": projection["assertion_id"],
                    "source_property_id": projection["source_property_id"],
                    "interpretation_source": projection["interpretation_source"],
                }
            )
        for projection in _same_row_clause_evidence_span_projections(
            payload,
            context,
        ):
            findings.append(
                {
                    "code": "same-row-multi-fragment-clause-evidence-alias",
                    "severity": "repairable",
                    "path": projection["path"],
                    "assertion_id": projection["assertion_id"],
                    "merged_clause_keys": projection["merged_clause_keys"],
                }
            )
        for projection in _typed_property_missing_literal_evidence_projections(
            payload,
            context,
        ):
            findings.append(
                {
                    "code": "typed-property-literal-evidence-missing",
                    "severity": "repairable",
                    "path": projection["path"],
                    "assertion_id": projection["assertion_id"],
                    "source_property_id": projection["source_property_id"],
                    "source_row_id": projection["source_row_id"],
                    "source_cell_locator": projection["source_cell_locator"],
                }
            )
    if context is not None and boundary is not None:
        for projection in _candidate_signal_code_binding_projections(
            payload,
            context,
            boundary,
        ):
            findings.append(
                {
                    "code": "candidate-signal-code-binding-missing",
                    "severity": "repairable",
                    "path": (
                        f"$.source_designs[{projection['source_index']}].assertions"
                        f"[{projection['assertion_index']}].requirement_codes"
                    ),
                    "assertion_id": projection["assertion_id"],
                    "signal_id": projection["signal_id"],
                    "missing_requirement_codes": projection[
                        "missing_requirement_codes"
                    ],
                }
            )
        for projection in _candidate_fallback_clause_evidence_projections(
            payload,
            context,
            boundary,
        ):
            findings.append(
                {
                    "code": "candidate-fallback-clause-evidence-alias",
                    "severity": "repairable",
                    "path": projection["path"],
                    "assertion_id": projection["assertion_id"],
                    "repaired_clause_keys": projection[
                        "repaired_clause_keys"
                    ],
                }
            )
        for projection in _negative_candidate_clause_evidence_projections(
            payload,
            context,
            boundary,
        ):
            findings.append(
                {
                    "code": "negative-candidate-clause-evidence-alias",
                    "severity": "repairable",
                    "path": projection["path"],
                    "assertion_id": projection["assertion_id"],
                    "repaired_clause_keys": projection[
                        "repaired_clause_keys"
                    ],
                }
            )
    for collection_name in ("negative_oracles", "requiredness_oracles"):
        collection = payload.get(collection_name, [])
        if not isinstance(collection, list):
            continue
        for item_index, item in enumerate(collection):
            if not isinstance(item, Mapping):
                continue
            oracle_status = str(item.get("oracle_status", ""))
            canonical_status = ORACLE_STATUS_ALIASES.get(oracle_status)
            if canonical_status is None or item.get("decision") != "executable_tc":
                continue
            findings.append(
                {
                    "code": "oracle-status-noncanonical-alias",
                    "severity": "repairable",
                    "path": f"$.{collection_name}[{item_index}].oracle_status",
                    "signal_id": str(item.get("signal_id", "")),
                    "alias": oracle_status,
                    "canonical_status": canonical_status,
                }
            )
    if context is not None and boundary is not None:
        expected_requiredness = {
            str(item["signal_id"]): item
            for item in semantic_source_signal_registry(context, boundary)[
                "requiredness"
            ]
        }
        collection = payload.get("requiredness_oracles", [])
        if isinstance(collection, list):
            for item_index, item in enumerate(collection):
                if not isinstance(item, Mapping):
                    continue
                expected_signal = expected_requiredness.get(
                    str(item.get("signal_id", ""))
                )
                if (
                    expected_signal is None
                    or expected_signal.get("source_binding") != "typed-xhtml-cell"
                ):
                    continue
                if item.get("requiredness_source") == "typed-xhtml-cell":
                    findings.append(
                        {
                            "code": "typed-requiredness-source-placeholder",
                            "severity": "repairable",
                            "path": (
                                f"$.requiredness_oracles[{item_index}]"
                                ".requiredness_source"
                            ),
                            "signal_id": str(item.get("signal_id", "")),
                            "canonical_source": str(
                                expected_signal["requiredness_source"]
                            ),
                            "source_cell_locator": str(
                                expected_signal["source_cell_locator"]
                            ),
                        }
                    )
                if (
                    item.get("decision") == "candidate_tc_required"
                    and item.get("oracle_status") == "ui-calibration-required"
                    and item.get("marker_oracle_found") == "yes"
                ):
                    findings.append(
                        {
                            "code": "typed-candidate-executable-marker-claim",
                            "severity": "repairable",
                            "path": (
                                f"$.requiredness_oracles[{item_index}]"
                                ".marker_oracle_found"
                            ),
                            "signal_id": str(item.get("signal_id", "")),
                            "canonical_value": "no",
                        }
                    )
    return {
        "version": 1,
        "status": "findings" if findings else "clean",
        "finding_count": len(findings),
        "repairable_count": sum(item["severity"] == "repairable" for item in findings),
        "blocking_count": sum(item["severity"] == "blocking" for item in findings),
        "raw_sha256": canonical_payload_sha256(payload),
        "findings": findings,
    }


def semantic_design_completeness_diagnostics(
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Aggregate source-derived completeness failures before strict fail-fast validation."""

    clarifications = tuple(
        item
        for item in context.get("approved_clarifications", [])
        if isinstance(item, Mapping)
    )
    preflight = validate_semantic_input_preflight(
        context,
        boundary,
        clarifications,
    )
    cardinality = _semantic_output_cardinality(preflight, boundary)
    expected_properties = {
        str(item["source_property_id"]): str(item["source_row_id"])
        for item in preflight["field_property_registry"]
    }
    source_designs = payload.get("source_designs", [])
    designs_by_row: dict[str, list[Mapping[str, Any]]] = {}
    if isinstance(source_designs, list):
        for item in source_designs:
            if isinstance(item, Mapping):
                designs_by_row.setdefault(str(item.get("source_row_id", "")), []).append(
                    item
                )

    findings: list[dict[str, Any]] = []
    for row_cardinality in cardinality["rows"]:
        row_id = str(row_cardinality["source_row_id"])
        designs = designs_by_row.get(row_id, [])
        if len(designs) != 1:
            findings.append(
                {
                    "code": "source-design-count-mismatch",
                    "severity": "blocking",
                    "source_row_id": row_id,
                    "expected_count": 1,
                    "actual_count": len(designs),
                }
            )
            continue
        assertions = designs[0].get("assertions", [])
        assertion_rows = (
            [item for item in assertions if isinstance(item, Mapping)]
            if isinstance(assertions, list)
            else []
        )
        testable = [
            item
            for item in assertion_rows
            if item.get("semantic_disposition") == "testable"
        ]
        minimum_testable = int(
            row_cardinality["minimum_testable_assertion_count"]
        )
        if len(testable) < minimum_testable:
            findings.append(
                {
                    "code": "testable-assertion-cardinality-shortfall",
                    "severity": "blocking",
                    "source_row_id": row_id,
                    "minimum_count": minimum_testable,
                    "actual_count": len(testable),
                    "missing_count": minimum_testable - len(testable),
                }
            )
        required_na = int(
            row_cardinality["required_not_applicable_assertion_count"]
        )
        actual_na = sum(
            item.get("semantic_disposition") == "not-applicable"
            for item in assertion_rows
        )
        if required_na and actual_na < required_na:
            findings.append(
                {
                    "code": "not-applicable-assertion-cardinality-shortfall",
                    "severity": "blocking",
                    "source_row_id": row_id,
                    "minimum_count": required_na,
                    "actual_count": actual_na,
                }
            )
        expected_codes = set(map(str, row_cardinality["requirement_codes"]))
        actual_codes = {
            str(code)
            for assertion in assertion_rows
            for code in (
                assertion.get("requirement_codes", [])
                if isinstance(assertion.get("requirement_codes"), list)
                else []
            )
        }
        if actual_codes != expected_codes:
            findings.append(
                {
                    "code": "requirement-code-coverage-mismatch",
                    "severity": "blocking",
                    "source_row_id": row_id,
                    "missing_requirement_codes": sorted(expected_codes - actual_codes),
                    "unexpected_requirement_codes": sorted(actual_codes - expected_codes),
                }
            )

    all_assertions = [
        assertion
        for designs in designs_by_row.values()
        for design in designs
        for assertion in (
            design.get("assertions", [])
            if isinstance(design.get("assertions"), list)
            else []
        )
        if isinstance(assertion, Mapping)
        and assertion.get("semantic_disposition") == "testable"
    ]
    for property_id, row_id in expected_properties.items():
        matching = [
            assertion
            for assertion in all_assertions
            if assertion.get("source_property_id") == property_id
        ]
        if len(matching) != 1:
            findings.append(
                {
                    "code": "source-property-assertion-count-mismatch",
                    "severity": "blocking",
                    "source_row_id": row_id,
                    "source_property_id": property_id,
                    "expected_count": 1,
                    "actual_count": len(matching),
                }
            )
    return {
        "version": 1,
        "status": "findings" if findings else "clean",
        "finding_count": len(findings),
        "blocking_count": len(findings),
        "cardinality": cardinality,
        "findings": findings,
    }


def normalize_semantic_design_source_property_transport(
    payload: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Apply context-free, mechanically provable ASSERT/OBL transport repairs."""

    normalized = copy.deepcopy(dict(payload))
    repairs: list[dict[str, Any]] = []
    source_designs = normalized.get("source_designs", [])
    obligations_by_id = {
        str(item.get("obligation_id", "")): item
        for item in normalized.get("obligations", [])
        if isinstance(item, dict)
    }
    source_property_by_atom: dict[str, str] = {}
    if isinstance(source_designs, list):
        for source_index, source_design in enumerate(source_designs):
            if not isinstance(source_design, dict):
                continue
            assertions = source_design.get("assertions", [])
            if not isinstance(assertions, list):
                continue
            for assertion_index, assertion in enumerate(assertions):
                if not isinstance(assertion, dict):
                    continue
                source_property_id = assertion.get("source_property_id")
                if isinstance(source_property_id, str) and not source_property_id.strip():
                    repairs.append(
                        {
                            "rule": "make-non-property-assertion-explicit",
                            "path": (
                                f"$.source_designs[{source_index}].assertions"
                                f"[{assertion_index}].source_property_id"
                            ),
                        }
                    )
                    assertion["source_property_id"] = "none_required"
                atom_id = assertion.get("atom_id")
                if (
                    isinstance(atom_id, str)
                    and atom_id.strip()
                    and isinstance(assertion.get("source_property_id"), str)
                ):
                    source_property_by_atom[atom_id] = str(
                        assertion["source_property_id"]
                    )
    obligations = normalized.get("obligations", [])
    if isinstance(obligations, list):
        for obligation_index, obligation in enumerate(obligations):
            if not isinstance(obligation, dict):
                continue
            source_property_id = obligation.get("source_property_id")
            linked_atom_id = str(obligation.get("linked_atom_id", ""))
            if (
                isinstance(source_property_id, str)
                and not source_property_id.strip()
                and source_property_by_atom.get(linked_atom_id) == "none_required"
            ):
                repairs.append(
                    {
                        "rule": "make-non-property-obligation-explicit",
                        "path": (
                            f"$.obligations[{obligation_index}].source_property_id"
                        ),
                        "linked_atom_id": linked_atom_id,
                    }
                )
                obligation["source_property_id"] = "none_required"
    polarity_by_obligation: dict[str, str] = {}
    for item in normalized.get("negative_oracles", []):
        if isinstance(item, Mapping):
            obligation_id = str(item.get("linked_obligation_id", ""))
            if obligation_id:
                polarity_by_obligation[obligation_id] = "negative"
    for item in normalized.get("requiredness_oracles", []):
        if not isinstance(item, Mapping):
            continue
        obligation_id = str(item.get("linked_obligation_id", ""))
        restriction_type = str(item.get("restriction_type", ""))
        if obligation_id and restriction_type in {"requiredness", "optionality"}:
            polarity_by_obligation[obligation_id] = (
                "negative" if restriction_type == "requiredness" else "positive"
            )
    if isinstance(source_designs, list):
        for source_index, source_design in enumerate(source_designs):
            if not isinstance(source_design, dict):
                continue
            assertions = source_design.get("assertions", [])
            if not isinstance(assertions, list):
                continue
            for assertion_index, assertion in enumerate(assertions):
                if not isinstance(assertion, dict):
                    continue
                obligation_ids = assertion.get("obligation_ids", [])
                if not isinstance(obligation_ids, list) or not obligation_ids:
                    continue
                expected_polarities = {
                    polarity_by_obligation[str(obligation_id)]
                    for obligation_id in obligation_ids
                    if str(obligation_id) in polarity_by_obligation
                }
                if len(expected_polarities) != 1:
                    continue
                expected_polarity = next(iter(expected_polarities))
                if assertion.get("polarity") == expected_polarity:
                    continue
                repairs.append(
                    {
                        "rule": "canonicalize-source-signal-polarity",
                        "path": (
                            f"$.source_designs[{source_index}].assertions"
                            f"[{assertion_index}].polarity"
                        ),
                        "assertion_id": str(assertion.get("assertion_id", "")),
                        "linked_obligation_ids": list(map(str, obligation_ids)),
                        "previous_value_sha256": hashlib.sha256(
                            str(assertion.get("polarity", "")).encode("utf-8")
                        ).hexdigest(),
                    }
                )
                assertion["polarity"] = expected_polarity
    receipt = {
        "version": 1,
        "status": "applied" if repairs else "not-needed",
        "repair_count": len(repairs),
        "repairs": repairs,
        "raw_sha256": canonical_payload_sha256(payload),
        "normalized_sha256": canonical_payload_sha256(normalized),
    }
    return normalized, receipt


def _always_visibility_source_backed_clause_projection(
    assertion: Mapping[str, Any],
    source_row: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Build the mandatory two-state proof only when the row names both states."""

    if assertion.get("semantic_disposition") != "testable":
        return None
    requirement_evidence = assertion.get("requirement_code_evidence", [])
    if not isinstance(requirement_evidence, list):
        return None
    always_binding = next(
        (
            binding
            for binding in requirement_evidence
            if isinstance(binding, Mapping)
            and "видимость-всегда"
            in normalize_exact_source_text(
                str(binding.get("exact_source_fragment", ""))
            ).casefold()
        ),
        None,
    )
    if always_binding is None:
        return None
    clause_arrays = {
        field: assertion.get(field)
        for field in ("condition_clauses", "action_clauses", "oracle_clauses")
    }
    condition_clauses = clause_arrays["condition_clauses"]
    if (
        all(isinstance(values, list) and len(values) >= 2 for values in clause_arrays.values())
        and isinstance(condition_clauses, list)
        and len(
            {
                normalize_exact_source_text(str(value)).casefold()
                for value in condition_clauses
            }
        )
        >= 2
    ):
        return None

    source_row_id = str(source_row.get("source_row_id", ""))
    field_or_action = str(source_row.get("field_or_action", "")).strip()
    source_text = str(source_row.get("bounded_source_text", ""))
    if not source_row_id or not field_or_action or not source_text:
        return None
    normalized_source = normalize_exact_source_text(source_text).casefold()
    always_fragment = str(always_binding.get("exact_source_fragment", "")).strip()
    if not always_fragment or normalize_exact_source_text(always_fragment).casefold() not in normalized_source:
        return None

    logical_match = re.search(r"логическое\s+да\s*/\s*нет", source_text, re.IGNORECASE)
    manual_match = re.search(r"при\s+ручном\s+заполнении", source_text, re.IGNORECASE)
    automatic_match = re.search(
        r"«ввести\s+вручную»\s*=\s*«нет»",
        source_text,
        re.IGNORECASE,
    )
    if logical_match is not None:
        condition_fragment = logical_match.group(0)
        conditions = [
            f"Элемент «{field_or_action}» имеет значение «Нет».",
            f"Элемент «{field_or_action}» имеет значение «Да».",
        ]
        actions = [
            f"Проверить видимость элемента «{field_or_action}» при значении «Нет».",
            f"Проверить видимость элемента «{field_or_action}» при значении «Да».",
        ]
        oracles = [
            f"Элемент «{field_or_action}» видим при значении «Нет».",
            f"Элемент «{field_or_action}» видим при значении «Да».",
        ]
        condition_fragments = [condition_fragment, condition_fragment]
    elif manual_match is not None and automatic_match is not None:
        conditions = [
            "Признак «Ввести вручную» имеет значение «Нет».",
            "Включено ручное заполнение адреса.",
        ]
        actions = [
            f"Проверить видимость поля «{field_or_action}» при автоматическом заполнении.",
            f"Проверить видимость поля «{field_or_action}» при ручном заполнении.",
        ]
        oracles = [
            f"Поле «{field_or_action}» видимо при автоматическом заполнении.",
            f"Поле «{field_or_action}» видимо при ручном заполнении.",
        ]
        condition_fragments = [automatic_match.group(0), manual_match.group(0)]
    else:
        return None

    clause_evidence = [
        {
            "clause_kind": "condition",
            "clause_index": index,
            "source_row_id": source_row_id,
            "exact_source_fragment": fragment,
        }
        for index, fragment in enumerate(condition_fragments)
    ]
    for clause_kind in ("action", "oracle"):
        clause_evidence.extend(
            {
                "clause_kind": clause_kind,
                "clause_index": index,
                "source_row_id": source_row_id,
                "exact_source_fragment": always_fragment,
            }
            for index in range(2)
        )
    return {
        "condition_clauses": conditions,
        "action_clauses": actions,
        "oracle_clauses": oracles,
        "clause_evidence": clause_evidence,
    }


def _always_visibility_direct_observation_projection(
    assertion: Mapping[str, Any],
    source_row: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Project one direct observation when the owning row names no state pair."""

    if assertion.get("semantic_disposition") != "testable":
        return None
    evidence = assertion.get("requirement_code_evidence", [])
    if not isinstance(evidence, list):
        return None
    always_binding = next(
        (
            item
            for item in evidence
            if isinstance(item, Mapping)
            and "видимость-всегда"
            in normalize_exact_source_text(
                str(item.get("exact_source_fragment", ""))
            ).casefold()
        ),
        None,
    )
    if always_binding is None:
        return None
    source_text = str(source_row.get("bounded_source_text", ""))
    if (
        re.search(r"логическое\s+да\s*/\s*нет", source_text, re.IGNORECASE)
        is not None
        or (
            re.search(r"при\s+ручном\s+заполнении", source_text, re.IGNORECASE)
            is not None
            and re.search(
                r"«ввести\s+вручную»\s*=\s*«нет»",
                source_text,
                re.IGNORECASE,
            )
            is not None
        )
    ):
        return None
    row_id = str(source_row.get("source_row_id", ""))
    field = str(assertion.get("field_or_block", "")).strip() or str(
        source_row.get("field_or_action", "элемент")
    ).strip()
    fragment = str(always_binding.get("exact_source_fragment", "")).strip()
    if not row_id or not fragment or fragment not in source_text:
        return None
    condition = f"Открыта форма, содержащая элемент «{field}»."
    action = f"Проверить видимость элемента «{field}»."
    oracle = f"Элемент «{field}» отображается."
    return {
        "canonical_statement": f"Элемент «{field}» всегда отображается.",
        "condition_clauses": [condition],
        "action_clauses": [action],
        "oracle_clauses": [oracle],
        "clause_evidence": [
            {
                "clause_kind": kind,
                "clause_index": 0,
                "source_row_id": row_id,
                "exact_source_fragment": fragment,
            }
            for kind in ("condition", "action", "oracle")
        ],
        "disposition_rationale": (
            "Owning source row задаёт always-visible без собственной размерности "
            "состояний, поэтому используется прямое наблюдение без чужого toggle."
        ),
        "obligation_fields": {
            "property_type": "visibility",
            "obligation_class": "always-visible-direct-observation",
            "required_behavior": oracle,
            "planned_check": action,
            "check_type": "positive",
            "coverage_class": "always-visible",
            "input_class": "direct-observation",
            "single_expected_behavior": oracle,
            "test_data": "none_required:action-only",
        },
    }


def _read_only_action_control_projection(
    assertion: Mapping[str, Any],
    source_row: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Represent typed read-only on a button/widget without a fake text entry."""

    if (
        assertion.get("semantic_disposition") != "testable"
        or _action_control_kind(source_row) is None
    ):
        return None
    editability = source_row.get("field_properties", {}).get("editability", {})
    if not isinstance(editability, Mapping):
        return None
    property_id = str(editability.get("property_id", ""))
    if (
        editability.get("normalized_value") != "read-only"
        or str(assertion.get("source_property_id", "")) != property_id
    ):
        return None
    row_id = str(source_row.get("source_row_id", ""))
    field = str(assertion.get("field_or_block", "")).strip() or str(
        source_row.get("field_or_action", "элемент")
    ).strip()
    if not row_id or not field:
        return None
    condition = f"Элемент «{field}» отображается."
    action = f"Проверить наличие режима редактирования значения у элемента «{field}»."
    oracle = f"У элемента «{field}» отсутствует редактируемое значение поля."
    return {
        "canonical_statement": (
            f"Action control «{field}» не предоставляет "
            "редактируемое значение."
        ),
        "polarity": "neutral",
        "condition_clauses": [condition],
        "action_clauses": [action],
        "oracle_clauses": [oracle],
        "disposition_rationale": (
            "Typed R=Нет относится к action control; проверяется "
            "отсутствие редактируемого value interface, а не ввод текста в кнопку."
        ),
        "obligation_fields": {
            "obligation_class": "action-control-read-only",
            "required_behavior": oracle,
            "planned_check": action,
            "check_type": "positive",
            "coverage_class": "typed-read-only-action-control",
            "input_class": "direct-observation",
            "single_expected_behavior": oracle,
            "test_data": "none_required:action-only",
        },
    }


def _inclusive_twentieth_birthday_projection(
    assertion: Mapping[str, Any],
    clarifications: Sequence[Mapping[str, Any]],
) -> dict[str, Any] | None:
    """Preserve an approved inclusive 20th-birthday boundary mechanically.

    The source row names the 20-year interval, while a hash-bound approved
    clarification states that a passport issued *before or on* the twentieth
    birthday belongs to that interval.  A model occasionally shortens this to
    ``before the birthday``.  Repair only that exact, clarification-bound expiry
    branch; do not infer age rules from free text or from an unrelated assertion.
    """

    if (
        assertion.get("semantic_disposition") != "testable"
        or assertion.get("execution_readiness") != "ready"
    ):
        return None
    bindings = assertion.get("clarification_clause_bindings", [])
    if not isinstance(bindings, list):
        return None
    clarification_by_id = {
        str(item.get("clarification_id", "")): item
        for item in clarifications
        if isinstance(item, Mapping)
    }
    matching_bindings = [
        item
        for item in bindings
        if isinstance(item, Mapping)
        and item.get("clause_kind") == "condition"
        and isinstance(item.get("clause_index"), int)
        and (
            clarification := clarification_by_id.get(
                str(item.get("clarification_id", ""))
            )
        )
        is not None
        and item.get("exact_answer_sha256")
        == clarification.get("exact_answer_sha256")
        and "до или в день 20-летия" in str(
            clarification.get("exact_answer", "")
        ).casefold()
        and "20-летия + 90 дней включительно" in str(
            clarification.get("exact_answer", "")
        ).casefold()
    ]
    if len(matching_bindings) != 1:
        return None
    binding = matching_bindings[0]
    condition_index = int(binding["clause_index"])
    conditions = assertion.get("condition_clauses", [])
    if not isinstance(conditions, list) or condition_index >= len(conditions):
        return None
    condition = str(conditions[condition_index])
    normalized_condition = normalize_exact_source_text(condition).casefold()
    if (
        "20-лет" not in normalized_condition
        or "90 календар" not in normalized_condition
        or "текущ" not in normalized_condition
        or "позже" not in normalized_condition
        or "до или в день 20-летия" in normalized_condition
    ):
        return None
    canonical = str(assertion.get("canonical_statement", ""))
    normalized_canonical = normalize_exact_source_text(canonical).casefold()
    if (
        "паспорт" not in normalized_canonical
        or "просроч" not in normalized_canonical
        or "20-лет" not in normalized_canonical
        or "14 лет" not in normalized_canonical
    ):
        return None

    canonical_conditions = copy.deepcopy(conditions)
    canonical_conditions[condition_index] = (
        "Дата выдачи находится в диапазоне от 14 лет до или в день "
        "20-летия; текущая дата позже 20-летия плюс 90 календарных дней."
    )
    return {
        "canonical_statement": (
            "Паспорт, выданный в диапазоне от 14 лет до или в день "
            "20-летия, после допустимого срока признаётся просроченным."
        ),
        "condition_clauses": canonical_conditions,
        "obligation_fields": {
            "required_behavior": (
                "Паспорт, выданный до или в день 20-летия, после "
                "20-летия + 90 календарных дней признаётся просроченным."
            ),
            "planned_check": (
                "Проверить просроченный паспорт, выданный до или в день "
                "20-летия клиента."
            ),
            "test_data": (
                "Дата рождения клиента; дата выдачи до или в день 20-летия; "
                "текущая дата = 20-летие + 91 календарный день."
            ),
        },
    }


def _future_issue_date_save_block_projection(
    assertion: Mapping[str, Any],
    clarifications: Sequence[Mapping[str, Any]],
) -> dict[str, Any] | None:
    """Preserve the exact save-blocking oracle from an approved clarification."""

    if (
        assertion.get("semantic_disposition") != "testable"
        or assertion.get("execution_readiness") != "ready"
        or "BSR 101" not in set(map(str, assertion.get("requirement_codes", [])))
    ):
        return None
    clarification_by_id = {
        str(item.get("clarification_id", "")): item
        for item in clarifications
        if isinstance(item, Mapping)
    }
    bindings = assertion.get("clarification_clause_bindings", [])
    if not isinstance(bindings, list):
        return None
    matching = [
        binding
        for binding in bindings
        if isinstance(binding, Mapping)
        and binding.get("clause_kind") == "oracle"
        and isinstance(binding.get("clause_index"), int)
        and (
            clarification := clarification_by_id.get(
                str(binding.get("clarification_id", ""))
            )
        )
        is not None
        and binding.get("exact_answer_sha256")
        == clarification.get("exact_answer_sha256")
        and "дата выдачи позже текущей даты блокирует сохранение"
        in normalize_exact_source_text(
            str(clarification.get("exact_answer", ""))
        ).casefold()
    ]
    if len(matching) != 1:
        return None
    oracle_index = int(matching[0]["clause_index"])
    oracles = assertion.get("oracle_clauses", [])
    if not isinstance(oracles, list) or oracle_index >= len(oracles):
        return None
    current = normalize_exact_source_text(str(oracles[oracle_index])).casefold()
    if "позже текущ" not in current and "будущ" not in current:
        return None
    canonical_oracles = copy.deepcopy(oracles)
    canonical_oracles[oracle_index] = (
        "Сохранение формы блокируется для даты выдачи позже текущей даты."
    )
    return {
        "oracle_clauses": canonical_oracles,
        "obligation_fields": {
            "required_behavior": (
                "Сохранение формы блокируется для даты выдачи позже текущей даты."
            ),
            "single_expected_behavior": (
                "Сохранение формы блокируется для даты выдачи позже текущей даты."
            ),
            "oracle_source": "BSR 101 + CLR-PASS-003",
        },
    }


def _load_verified_fixture_contracts(
    context: Mapping[str, Any],
    repo_root: Path | None,
) -> dict[str, dict[str, Any]]:
    """Load only hash-bound verified fixture contracts registered in context."""

    if repo_root is None:
        return {}
    fingerprints = {
        str(item.get("path", "")): item
        for item in context.get("source_cache", {}).get("input_fingerprints", [])
        if isinstance(item, Mapping)
    }
    contracts: dict[str, dict[str, Any]] = {}
    root = repo_root.resolve()
    for source in context.get("sources", []):
        if not isinstance(source, Mapping):
            continue
        relative = str(source.get("path", ""))
        if not relative.casefold().endswith(".verification.json"):
            continue
        fingerprint = fingerprints.get(relative)
        if (
            not isinstance(fingerprint, Mapping)
            or fingerprint.get("role") != "external-vendor-reference"
        ):
            continue
        candidate = (root / Path(relative)).resolve()
        try:
            candidate.relative_to(root)
            raw = candidate.read_bytes()
        except (OSError, ValueError):
            continue
        if hashlib.sha256(raw).hexdigest() != fingerprint.get("sha256"):
            continue
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            continue
        if not isinstance(payload, Mapping) or payload.get("status") not in {
            "verified",
            "accepted",
        }:
            continue
        fixture_id = str(payload.get("fixture_id", ""))
        request = payload.get("request")
        expected = payload.get("expected_response")
        if (
            re.fullmatch(r"(?:FX|FIX)-[A-Za-z0-9_.-]+", fixture_id) is None
            or not isinstance(request, Mapping)
            or not isinstance(request.get("parameters"), Mapping)
            or not isinstance(expected, Mapping)
        ):
            continue
        contracts[fixture_id] = {
            "request_parameters": dict(request["parameters"]),
            "expected_response": dict(expected),
            "response_sha256": str(payload.get("response_sha256", "")),
        }
    return contracts


_FIXTURE_ID_RE = re.compile(r"\b(?:FX|FIX)-[A-Za-z0-9_.-]+\b")


def _verified_fixture_clause_projection(
    assertion: Mapping[str, Any],
    obligations_by_id: Mapping[str, Mapping[str, Any]],
    fixture_contracts: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any] | None:
    """Replace vague dynamic values with literals from one verified fixture."""

    if assertion.get("semantic_disposition") != "testable":
        return None
    owners = [
        obligations_by_id.get(str(obligation_id))
        for obligation_id in assertion.get("obligation_ids", [])
    ]
    owners = [item for item in owners if isinstance(item, Mapping)]
    fixture_ids = {
        fixture_id
        for owner in owners
        for fixture_id in _FIXTURE_ID_RE.findall(
            json.dumps(owner, ensure_ascii=False, sort_keys=True)
        )
        if fixture_id in fixture_contracts
    }
    if len(fixture_ids) != 1 or len(owners) != 1:
        return None
    fixture_id = next(iter(fixture_ids))
    contract = fixture_contracts[fixture_id]
    expected = contract.get("expected_response")
    parameters = contract.get("request_parameters")
    if not isinstance(expected, Mapping) or not isinstance(parameters, Mapping):
        return None
    suggestion = str(expected.get("exact_suggestion", "")).strip()
    query = str(parameters.get("query", "")).strip()
    if not suggestion or not query:
        return None
    owner = owners[0]
    property_type = str(owner.get("property_type", ""))
    field = str(assertion.get("field_or_block", "")).split("—", 1)[0].strip()
    if not field:
        return None
    if property_type == "dynamic-prefill":
        return {
            "canonical_statement": (
                f"Ввод кода «{query}» предлагает в поле «{field}» точное "
                f"значение «{suggestion}» из сохранённой fixture {fixture_id}."
            ),
            "oracle_clauses": [
                f"В списке «{field}» предлагается значение «{suggestion}»."
            ],
            "disposition_rationale": (
                f"Используется hash-bound fixture {fixture_id}; runtime API-вызов "
                "в тест-кейсе не требуется."
            ),
            "obligation_fields": {
                "required_behavior": f"Предложить значение «{suggestion}» по коду «{query}».",
                "planned_check": f"Ввести в продуктовом UI код «{query}».",
                "single_expected_behavior": f"Предложено значение «{suggestion}».",
                "test_data": (
                    f"{fixture_id}; query={query}; exact_suggestion={suggestion}"
                ),
            },
        }
    if property_type == "multi-suggestion-selection":
        minimum = expected.get("minimum_suggestion_count")
        if not isinstance(minimum, int) or minimum < 2:
            return None
        return {
            "canonical_statement": (
                f"Из нескольких предложений fixture {fixture_id} пользователь "
                f"выбирает «{suggestion}», и это значение отображается в поле «{field}»."
            ),
            "condition_clauses": [
                f"Сохранённая fixture {fixture_id} для кода «{query}» содержит "
                f"не менее {minimum} предложений."
            ],
            "action_clauses": [
                f"В списке «{field}» выбрать точное значение «{suggestion}» "
                f"из сохранённой fixture {fixture_id}."
            ],
            "oracle_clauses": [
                f"В поле «{field}» отображается значение «{suggestion}»."
            ],
            "disposition_rationale": (
                f"Выбор привязан к exact suggestion hash-bound fixture {fixture_id}; "
                "закрытый справочник не утверждается."
            ),
            "obligation_fields": {
                "required_behavior": f"Выбрать и отобразить значение «{suggestion}».",
                "planned_check": f"Выбрать в списке точное значение «{suggestion}».",
                "single_expected_behavior": f"Поле отображает значение «{suggestion}».",
                "test_data": (
                    f"{fixture_id}; query={query}; exact_suggestion={suggestion}; "
                    f"minimum_suggestion_count={minimum}"
                ),
            },
        }
    return None


_UI_CALIBRATION_TEXT_RE = re.compile(r"(?:калибр\w*|calibrat\w*)", re.IGNORECASE)
_CANONICAL_UI_CALIBRATION_SUFFIX = (
    "точный UI-триггер и отклик требуют калибровки."
)


def _canonicalize_declared_ui_calibration(
    assertion: dict[str, Any],
    obligations_by_id: Mapping[str, dict[str, Any]],
) -> bool:
    """Align an assertion-declared calibration need with obligation metadata.

    If the model itself says that the observable UI reaction requires
    calibration, the obligation cannot simultaneously claim a source-backed
    exact oracle.  Preserve the source-backed business rejection and make the
    unknown UI trigger/reaction explicit through the canonical candidate marker.
    """

    if assertion.get("semantic_disposition") != "testable":
        return False
    oracle_clauses = assertion.get("oracle_clauses", [])
    if not isinstance(oracle_clauses, list) or not any(
        isinstance(clause, str) and _UI_CALIBRATION_TEXT_RE.search(clause)
        for clause in oracle_clauses
    ):
        return False
    owners = [
        obligations_by_id.get(str(obligation_id))
        for obligation_id in assertion.get("obligation_ids", [])
    ]
    owners = [item for item in owners if isinstance(item, dict)]
    if not owners or all(
        item.get("review_notes") == "candidate-ui-calibration"
        and item.get("oracle_source") == "not_found"
        for item in owners
    ):
        return False

    canonical_oracles: list[str] = []
    for raw_clause in oracle_clauses:
        clause = str(raw_clause).strip()
        if _UI_CALIBRATION_TEXT_RE.search(clause):
            prefix = clause.split(";", 1)[0].rstrip(" .")
            canonical_oracles.append(
                f"{prefix}; {_CANONICAL_UI_CALIBRATION_SUFFIX}"
            )
        else:
            canonical_oracles.append(clause)
    assertion["oracle_clauses"] = canonical_oracles
    canonical_behavior = "; ".join(canonical_oracles)
    for obligation in owners:
        obligation.update(
            {
                "review_notes": "candidate-ui-calibration",
                "oracle_source": "not_found",
                "required_behavior": canonical_behavior,
                "single_expected_behavior": canonical_behavior,
            }
        )
    return True


_VISIBILITY_CODE_FRAGMENT_RE = re.compile(
    r"^(?P<code>[A-Za-z]+\s+\d+)\.\s*Видимость:\s*Да,\s*если\s+"
    r"признак\s+«(?P<trigger>[^»]+)»\s*=\s*«(?P<value>[^»]+)»\.?$",
    re.IGNORECASE,
)


def _split_visibility_code_from_typed_requiredness(
    payload: dict[str, Any],
    context: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Separate a visibility BSR from a typed requiredness property chain.

    A typed O-cell owns requiredness.  A BSR whose exact text defines only
    conditional visibility must own a separate observable assertion instead of
    being attached to that typed property merely to satisfy per-row code union.
    """

    rows = {
        str(row.get("source_row_id", "")): row
        for row in context.get("source_rows", [])
        if isinstance(row, Mapping)
    }
    existing_assertion_ids = {
        str(assertion.get("assertion_id", ""))
        for design in payload.get("source_designs", [])
        if isinstance(design, Mapping)
        for assertion in design.get("assertions", [])
        if isinstance(assertion, Mapping)
    }
    existing_atom_ids = {
        str(assertion.get("atom_id", ""))
        for design in payload.get("source_designs", [])
        if isinstance(design, Mapping)
        for assertion in design.get("assertions", [])
        if isinstance(assertion, Mapping)
    }
    existing_obligation_ids = {
        str(item.get("obligation_id", ""))
        for item in payload.get("obligations", [])
        if isinstance(item, Mapping)
    }
    existing_tc_ids = {
        str(item.get("planned_tc_id", ""))
        for item in payload.get("obligations", [])
        if isinstance(item, Mapping)
    }
    repairs: list[dict[str, Any]] = []
    for source_index, design in enumerate(payload.get("source_designs", [])):
        if not isinstance(design, dict):
            continue
        row_id = str(design.get("source_row_id", ""))
        source_row = rows.get(row_id)
        assertions = design.get("assertions", [])
        if source_row is None or not isinstance(assertions, list):
            continue
        additions: list[dict[str, Any]] = []
        for assertion_index, assertion in enumerate(assertions):
            if (
                not isinstance(assertion, dict)
                or assertion.get("semantic_disposition") != "testable"
                or "-REQUIREDNESS-" not in str(assertion.get("source_property_id", ""))
            ):
                continue
            evidence = assertion.get("requirement_code_evidence", [])
            if not isinstance(evidence, list):
                continue
            for binding in list(evidence):
                if not isinstance(binding, Mapping):
                    continue
                match = _VISIBILITY_CODE_FRAGMENT_RE.fullmatch(
                    normalize_exact_source_text(
                        str(binding.get("exact_source_fragment", ""))
                    )
                )
                code = str(binding.get("requirement_code", ""))
                if match is None or match.group("code").casefold() != code.casefold():
                    continue
                suffix = re.sub(r"[^A-Za-z0-9]+", "-", f"{row_id}-{code}").strip("-")
                assertion_id = f"ASSERT-AUTO-{suffix}-VIS"
                atom_id = f"ATOM-AUTO-{suffix}-VIS"
                obligation_id = f"OBL-AUTO-{suffix}-VIS"
                planned_tc_id = f"TC-AUTO-{suffix}-VIS"
                if (
                    assertion_id in existing_assertion_ids
                    or atom_id in existing_atom_ids
                    or obligation_id in existing_obligation_ids
                    or planned_tc_id in existing_tc_ids
                ):
                    continue
                trigger = match.group("trigger")
                value = match.group("value")
                field = str(assertion.get("field_or_block", "")).strip() or str(
                    source_row.get("field_or_action", row_id)
                )
                fragment = str(binding.get("exact_source_fragment", ""))
                moved_clarifications: list[dict[str, Any]] = []
                retained_clarifications: list[dict[str, Any]] = []
                for raw_clarification in assertion.get(
                    "clarification_clause_bindings", []
                ):
                    if not isinstance(raw_clarification, Mapping):
                        continue
                    clarification = copy.deepcopy(dict(raw_clarification))
                    codes = list(map(str, clarification.get("requirement_codes", [])))
                    if code in codes:
                        clarification["requirement_codes"] = [code]
                        clarification["clause_kind"] = "condition"
                        clarification["clause_index"] = 0
                        moved_clarifications.append(clarification)
                        remaining = [item for item in codes if item != code]
                        if remaining:
                            retained = copy.deepcopy(dict(raw_clarification))
                            retained["requirement_codes"] = remaining
                            retained_clarifications.append(retained)
                    else:
                        retained_clarifications.append(
                            copy.deepcopy(dict(raw_clarification))
                        )
                previous_sha256 = canonical_payload_sha256(assertion)
                assertion["requirement_codes"] = [
                    item
                    for item in map(str, assertion.get("requirement_codes", []))
                    if item != code
                ]
                assertion["requirement_code_evidence"] = [
                    item for item in evidence if item is not binding
                ]
                assertion["clarification_clause_bindings"] = retained_clarifications
                condition = f"Признак «{trigger}» доступен для изменения."
                action = f"Установить признак «{trigger}» в значение «{value}»."
                oracle = f"Поле «{field}» отображается."
                additions.append(
                    {
                        "assertion_id": assertion_id,
                        "canonical_statement": (
                            f"Поле «{field}» отображается, если признак "
                            f"«{trigger}» = «{value}»."
                        ),
                        "polarity": "positive",
                        "semantic_disposition": "testable",
                        "execution_readiness": "ready",
                        "execution_readiness_rationale": "none_required",
                        "risk": str(assertion.get("risk", "medium")),
                        "condition_clauses": [condition],
                        "action_clauses": [action],
                        "oracle_clauses": [oracle],
                        "requirement_codes": [code],
                        "requirement_code_evidence": [copy.deepcopy(dict(binding))],
                        "clause_evidence": [
                            {
                                "clause_kind": kind,
                                "clause_index": 0,
                                "source_row_id": row_id,
                                "exact_source_fragment": fragment,
                            }
                            for kind in ("condition", "action", "oracle")
                        ],
                        "supporting_source_bindings": copy.deepcopy(
                            assertion.get("supporting_source_bindings", [])
                        ),
                        "clarification_clause_bindings": moved_clarifications,
                        "atom_id": atom_id,
                        "obligation_ids": [obligation_id],
                        "disposition_rationale": (
                            "BSR-код определяет conditional visibility отдельно от "
                            "typed requiredness ячейки О."
                        ),
                        "source_property_id": "none_required",
                        "field_or_block": field,
                        "source_reference": str(
                            source_row.get("source_ref", assertion.get("source_reference", row_id))
                        ),
                    }
                )
                payload.setdefault("obligations", []).append(
                    {
                        "obligation_id": obligation_id,
                        "package_id": str(
                            next(
                                (
                                    owner.get("package_id")
                                    for owner in payload.get("obligations", [])
                                    if isinstance(owner, Mapping)
                                    and str(owner.get("obligation_id", ""))
                                    in set(map(str, assertion.get("obligation_ids", [])))
                                ),
                                "WP-01",
                            )
                        ),
                        "linked_atom_id": atom_id,
                        "source_property_id": "none_required",
                        "property_type": "conditional-visibility",
                        "obligation_class": "conditional-visibility",
                        "required_behavior": oracle,
                        "source_ref": code,
                        "planned_tc_id": planned_tc_id,
                        "review_notes": "none_required",
                        "design_dimension": "conditional-visibility",
                        "planned_check": action,
                        "check_type": "positive",
                        "coverage_class": code,
                        "input_class": f"{trigger}={value}",
                        "single_expected_behavior": oracle,
                        "oracle_source": code,
                        "test_data": f"{trigger}={value}",
                        "dictionary_refs": [],
                        "dictionary_coverage": "none_required",
                        "scope_obligation_ids": [],
                    }
                )
                existing_assertion_ids.add(assertion_id)
                existing_atom_ids.add(atom_id)
                existing_obligation_ids.add(obligation_id)
                existing_tc_ids.add(planned_tc_id)
                repairs.append(
                    {
                        "rule": "split-visibility-code-from-typed-requiredness",
                        "path": (
                            f"$.source_designs[{source_index}].assertions"
                            f"[{assertion_index}]"
                        ),
                        "source_row_id": row_id,
                        "requirement_code": code,
                        "typed_assertion_id": str(assertion.get("assertion_id", "")),
                        "visibility_assertion_id": assertion_id,
                        "previous_value_sha256": previous_sha256,
                    }
                )
        assertions.extend(additions)
    return repairs


def _materialize_bare_requirement_definition_gaps(
    payload: dict[str, Any],
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Turn invented semantics for an authoritative bare-code gap into ambiguity.

    The operation is deterministic: a boundary-v2 missing-source-definition gap
    and the literal bare token are both required. Typed sibling properties stay
    executable; only the assertion that claims behavior for the undecoded token
    loses its OBL/TC chain and remains dependency-blocked by the authoritative GAP.
    """

    rows_by_id = {
        str(row.get("source_row_id", "")): row
        for row in context.get("source_rows", [])
        if isinstance(row, Mapping)
    }
    gapped_codes_by_row: dict[str, set[str]] = defaultdict(set)
    for gap in boundary.get("gaps", []):
        if (
            not isinstance(gap, Mapping)
            or gap.get("gap_type") != "missing-source-definition"
            or gap.get("blocking") is not False
            or gap.get("downstream_handling") != "carry-to-source-model"
        ):
            continue
        fragments = " ".join(map(str, gap.get("exact_source_fragments", [])))
        for row_id in map(str, gap.get("source_row_ids", [])):
            row = rows_by_id.get(row_id)
            if row is None:
                continue
            for code in bare_requirement_codes(
                str(row.get("bounded_source_text", ""))
            ):
                if code.casefold() in fragments.casefold():
                    gapped_codes_by_row[row_id].add(code)
    if not gapped_codes_by_row:
        return []

    converted: dict[str, tuple[str, str, tuple[str, ...], tuple[str, ...]]] = {}
    repairs: list[dict[str, Any]] = []
    for source_index, source_design in enumerate(payload.get("source_designs", [])):
        if not isinstance(source_design, dict):
            continue
        row_id = str(source_design.get("source_row_id", ""))
        gapped_codes = gapped_codes_by_row.get(row_id, set())
        if not gapped_codes:
            continue
        for assertion_index, assertion in enumerate(source_design.get("assertions", [])):
            if (
                not isinstance(assertion, dict)
                or assertion.get("semantic_disposition") != "testable"
                or assertion.get("source_property_id") != "none_required"
            ):
                continue
            assertion_codes = set(map(str, assertion.get("requirement_codes", [])))
            matched_codes = assertion_codes & gapped_codes
            if not matched_codes:
                continue
            evidence = assertion.get("requirement_code_evidence", [])
            if not isinstance(evidence, list) or not all(
                any(
                    isinstance(binding, Mapping)
                    and str(binding.get("requirement_code", "")) == code
                    and str(binding.get("exact_source_fragment", "")).strip()
                    == bare_requirement_codes(
                        str(rows_by_id[row_id].get("bounded_source_text", ""))
                    ).get(code, "").strip()
                    for binding in evidence
                )
                for code in matched_codes
            ):
                continue
            old_obligation_ids = tuple(map(str, assertion.get("obligation_ids", [])))
            atom_id = str(assertion.get("atom_id", ""))
            assertion_id = str(assertion.get("assertion_id", ""))
            previous_sha256 = canonical_payload_sha256(assertion)
            code_label = ", ".join(sorted(matched_codes))
            assertion.update(
                {
                    "canonical_statement": (
                        f"{code_label} не содержит расшифрованного поведения в "
                        "доступном source row."
                    ),
                    "polarity": "neutral",
                    "semantic_disposition": "ambiguous",
                    "execution_readiness": "dependency-blocked",
                    "execution_readiness_rationale": (
                        "Открытый missing-source-definition GAP должен определить "
                        f"поведение {code_label} до создания исполнимой проверки."
                    ),
                    "condition_clauses": [],
                    "action_clauses": [],
                    "oracle_clauses": [],
                    "clause_evidence": [],
                    "supporting_source_bindings": [],
                    "clarification_clause_bindings": [],
                    "obligation_ids": [],
                    "disposition_rationale": (
                        "Authoritative boundary фиксирует missing-source-definition; "
                        "неизвестное поведение по одному коду нельзя признать "
                        "not-applicable или вывести из соседних typed cells."
                    ),
                }
            )
            converted[assertion_id] = (
                row_id,
                atom_id,
                old_obligation_ids,
                tuple(sorted(matched_codes)),
            )
            repairs.append(
                {
                    "rule": "bind-bare-requirement-code-to-definition-gap",
                    "path": (
                        f"$.source_designs[{source_index}].assertions"
                        f"[{assertion_index}]"
                    ),
                    "source_row_id": row_id,
                    "assertion_id": assertion_id,
                    "requirement_codes": sorted(matched_codes),
                    "removed_obligation_ids": list(old_obligation_ids),
                    "previous_value_sha256": previous_sha256,
                }
            )
    if not converted:
        return repairs

    removed_obligation_ids = {
        obligation_id
        for _row_id, _atom_id, obligation_ids, _codes in converted.values()
        for obligation_id in obligation_ids
    }
    removed_atoms = {atom_id for _row_id, atom_id, _obls, _codes in converted.values()}
    obligations = payload.get("obligations", [])
    removed_test_cases = {
        str(item.get("planned_tc_id", ""))
        for item in obligations
        if isinstance(item, Mapping)
        and str(item.get("obligation_id", "")) in removed_obligation_ids
    }
    payload["obligations"] = [
        item
        for item in obligations
        if not isinstance(item, Mapping)
        or str(item.get("obligation_id", "")) not in removed_obligation_ids
    ]

    assertion_by_id: dict[str, Mapping[str, Any]] = {}
    row_by_assertion: dict[str, str] = {}
    for source_design in payload.get("source_designs", []):
        if not isinstance(source_design, Mapping):
            continue
        row_id = str(source_design.get("source_row_id", ""))
        for assertion in source_design.get("assertions", []):
            if isinstance(assertion, Mapping):
                assertion_id = str(assertion.get("assertion_id", ""))
                assertion_by_id[assertion_id] = assertion
                row_by_assertion[assertion_id] = row_id

    for binding in payload.get("dependency_bindings", []):
        if not isinstance(binding, dict):
            continue
        old_ids = list(map(str, binding.get("linked_assertion_ids", [])))
        if not any(assertion_id in converted for assertion_id in old_ids):
            continue
        canonical_ids: list[str] = []
        for assertion_id in old_ids:
            converted_item = converted.get(assertion_id)
            if converted_item is None:
                canonical_ids.append(assertion_id)
                continue
            row_id = converted_item[0]
            fragments = list(map(str, binding.get("exact_source_fragments", [])))
            replacement = next(
                (
                    candidate_id
                    for candidate_id, candidate in assertion_by_id.items()
                    if row_by_assertion.get(candidate_id) == row_id
                    and candidate.get("semantic_disposition") == "testable"
                    and candidate.get("obligation_ids")
                    and any(
                        fragment in evidence_fragment
                        for _evidence_row, evidence_fragment in _assertion_literal_evidence(
                            candidate
                        )
                        for fragment in fragments
                    )
                ),
                None,
            )
            if replacement is not None and replacement not in canonical_ids:
                canonical_ids.append(replacement)
        binding["linked_assertion_ids"] = canonical_ids
        binding["linked_atom_ids"] = [
            str(assertion_by_id[item].get("atom_id", "")) for item in canonical_ids
        ]
        binding["linked_obligation_ids"] = [
            str(obligation_id)
            for item in canonical_ids
            for obligation_id in assertion_by_id[item].get("obligation_ids", [])
        ]

    for applicability in payload.get("applicability", []):
        if not isinstance(applicability, dict):
            continue
        applicability["linked_atoms"] = [
            atom
            for atom in applicability.get("linked_atoms", [])
            if str(atom) not in removed_atoms
        ]
        applicability["linked_test_cases"] = [
            tc
            for tc in applicability.get("linked_test_cases", [])
            if str(tc) not in removed_test_cases
        ]
        if applicability.get("applicable") == "yes" and not applicability[
            "linked_atoms"
        ]:
            applicability.update(
                {
                    "applicable": "no",
                    "source_ref": "none_required",
                    "reason": "No executable source-backed chain remains for this dimension.",
                }
            )
    for collection_name in ("negative_oracles", "requiredness_oracles"):
        payload[collection_name] = [
            item
            for item in payload.get(collection_name, [])
            if not isinstance(item, Mapping)
            or str(item.get("linked_obligation_id", ""))
            not in removed_obligation_ids
        ]
    return repairs


_EXACT_DIGIT_LENGTH_PATTERN = re.compile(
    r"\b(?:только|ровно)\s+(?P<length>[1-9][0-9]*)\s+"
    r"(?:числов(?:ых|ого)\s+символ(?:ов|а)|цифр(?:ы|а|у)?)\b",
    re.IGNORECASE,
)
_INLINE_REQUIREMENT_CODE_PATTERN = re.compile(
    r"\b(?:BSR|GSR|DIT)\s+[A-Za-z0-9._/-]+\b"
)
_ACTION_DIGIT_VALUE_PATTERN = re.compile(r"(?<![0-9A-Za-zА-Яа-яЁё])[0-9]+(?![0-9A-Za-zА-Яа-яЁё])")


def _assertion_action_digit_values(assertion: Mapping[str, Any]) -> tuple[str, ...]:
    values: list[str] = []
    for clause in assertion.get("action_clauses", []):
        if not isinstance(clause, str):
            continue
        for match in _ACTION_DIGIT_VALUE_PATTERN.finditer(clause):
            value = match.group(0)
            if value not in values:
                values.append(value)
    return tuple(values)


def _quote_concrete_action_value(
    assertion: dict[str, Any],
    value: str,
) -> bool:
    clauses = assertion.get("action_clauses", [])
    if not isinstance(clauses, list):
        return False
    changed = False
    for index, clause in enumerate(clauses):
        if not isinstance(clause, str) or f"«{value}»" in clause:
            continue
        replaced = False

        def replacement(match: re.Match[str]) -> str:
            nonlocal replaced
            if not replaced and match.group(0) == value:
                replaced = True
                return f"«{value}»"
            return match.group(0)

        normalized = _ACTION_DIGIT_VALUE_PATTERN.sub(replacement, clause)
        if replaced:
            clauses[index] = normalized
            changed = True
    return changed


def _safe_longer_digit_value(base_value: str, source_text: str) -> str:
    """Extend a valid digit value without creating a repeated-digit side class."""

    repeated_limit_match = re.search(
        r"не\s+должно\s+быть\s+([A-Za-zА-Яа-яЁё]+)\s+"
        r"одинаковых\s+цифр\s+подряд",
        source_text,
        re.IGNORECASE,
    )
    if repeated_limit_match is None or len(base_value) < 2:
        return base_value + "0"
    for digit in "0123456789":
        if not (base_value[-1] == digit and base_value[-2] == digit):
            return base_value + digit
    return base_value + "0"


def _materialize_missing_exact_length_boundaries(
    payload: dict[str, Any],
    context: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Add deterministic N-1/N+1 calibration chains around a proven exact N.

    The source defines the invalid classes, but usually not their observable UI
    reaction.  The bridge therefore adds concrete candidate-ui-calibration cases
    without claiming filtering, an error message, clearing, or navigation blocking.
    """

    source_designs = payload.get("source_designs", [])
    obligations = payload.get("obligations", [])
    applicability = payload.get("applicability", [])
    if not isinstance(source_designs, list) or not isinstance(obligations, list):
        return []
    rows_by_id = {
        str(row.get("source_row_id", "")): row
        for row in context.get("source_rows", [])
        if isinstance(row, Mapping)
    }
    obligations_by_id = {
        str(item.get("obligation_id", "")): item
        for item in obligations
        if isinstance(item, Mapping)
    }
    existing_ids = {
        str(value)
        for source_design in source_designs
        if isinstance(source_design, Mapping)
        for assertion in source_design.get("assertions", [])
        if isinstance(assertion, Mapping)
        for value in (assertion.get("assertion_id"), assertion.get("atom_id"))
    } | {
        str(value)
        for obligation in obligations
        if isinstance(obligation, Mapping)
        for value in (
            obligation.get("obligation_id"),
            obligation.get("planned_tc_id"),
        )
    }
    repairs: list[dict[str, Any]] = []
    for source_index, source_design in enumerate(source_designs):
        if not isinstance(source_design, dict):
            continue
        source_row_id = str(source_design.get("source_row_id", ""))
        source_row = rows_by_id.get(source_row_id)
        assertions = source_design.get("assertions", [])
        if source_row is None or not isinstance(assertions, list):
            continue
        source_text = str(source_row.get("bounded_source_text", ""))
        field_or_block = str(
            source_row.get("field_or_action", "")
            or source_design.get("field_or_block", "")
            or source_row_id
        )
        for rule_index, length_match in enumerate(
            _EXACT_DIGIT_LENGTH_PATTERN.finditer(source_text),
            start=1,
        ):
            exact_length = int(length_match.group("length"))
            if exact_length < 2:
                continue
            preceding_codes = _INLINE_REQUIREMENT_CODE_PATTERN.findall(
                source_text[: length_match.start()]
            )
            requirement_code = preceding_codes[-1] if preceding_codes else ""
            rule_assertions = [
                assertion
                for assertion in assertions
                if isinstance(assertion, Mapping)
                and (
                    not requirement_code
                    or requirement_code
                    in set(map(str, assertion.get("requirement_codes", [])))
                )
            ]
            base_assertion: Mapping[str, Any] | None = None
            base_value = ""
            for assertion in rule_assertions:
                if (
                    assertion.get("semantic_disposition") != "testable"
                    or assertion.get("polarity") != "positive"
                    or len(assertion.get("obligation_ids", [])) != 1
                ):
                    continue
                matching_values = [
                    value
                    for value in _assertion_action_digit_values(assertion)
                    if len(value) == exact_length
                ]
                if matching_values:
                    base_assertion = assertion
                    base_value = matching_values[0]
                    break
            if base_assertion is None:
                continue
            base_action_quoted = _quote_concrete_action_value(
                base_assertion,
                base_value,
            )
            if base_action_quoted:
                repairs.append(
                    {
                        "rule": "quote-exact-length-concrete-action-value",
                        "path": (
                            f"$.source_designs[{source_index}].assertions"
                            f"[{assertions.index(base_assertion)}].action_clauses"
                        ),
                        "source_row_id": source_row_id,
                        "requirement_code": requirement_code or "none_required",
                        "base_assertion_id": str(
                            base_assertion.get("assertion_id", "")
                        ),
                        "value": base_value,
                    }
                )
            base_obligation_id = str(base_assertion["obligation_ids"][0])
            base_obligation = obligations_by_id.get(base_obligation_id)
            if not isinstance(base_obligation, Mapping):
                continue
            present_classes = {
                len(value) - exact_length
                for assertion in rule_assertions
                for value in _assertion_action_digit_values(assertion)
                if len(value) - exact_length in {-1, 0, 1}
            }
            class_values = (
                (-1, "N-1", base_value[:-1], "shorter"),
                (
                    1,
                    "N+1",
                    _safe_longer_digit_value(base_value, source_text),
                    "longer",
                ),
            )
            additions: list[tuple[dict[str, Any], dict[str, Any]]] = []
            for offset, class_id, value, slug in class_values:
                if offset in present_classes:
                    continue
                identity = (
                    f"XLB-{source_row_id}-{rule_index}-{slug.upper()}"
                )
                assertion_id = f"ASSERT-{identity}"
                atom_id = f"ATOM-{identity}"
                obligation_id = f"OBL-{identity}"
                test_case_id = f"TC-{identity}"
                generated_ids = {
                    assertion_id,
                    atom_id,
                    obligation_id,
                    test_case_id,
                }
                if generated_ids & existing_ids:
                    continue
                exact_fragment = length_match.group(0)
                assertion = copy.deepcopy(dict(base_assertion))
                assertion.update(
                    {
                        "assertion_id": assertion_id,
                        "canonical_statement": (
                            f"Значение «{value}» класса {class_id} не соответствует "
                            f"правилу точной длины {exact_length} цифр для поля "
                            f"«{field_or_block}»; точная UI-реакция требует калибровки."
                        ),
                        "polarity": "negative",
                        "risk": "high",
                        "action_clauses": [
                            f"Ввести в поле «{field_or_block}» значение «{value}» "
                            f"класса {class_id}."
                        ],
                        "oracle_clauses": [
                            f"Точная наблюдаемая UI-реакция на значение «{value}» "
                            f"класса {class_id} требует candidate-ui-calibration; "
                            "фильтрация, сообщение, очистка и блокировка перехода "
                            "не утверждаются."
                        ],
                        "atom_id": atom_id,
                        "obligation_ids": [obligation_id],
                        "disposition_rationale": (
                            f"Отдельный {class_id} boundary детерминированно следует "
                            "из exact-length; механизм UI остаётся неизвестным."
                        ),
                        "source_property_id": "none_required",
                    }
                )
                assertion["clause_evidence"] = [
                    copy.deepcopy(dict(evidence))
                    for evidence in base_assertion.get("clause_evidence", [])
                    if isinstance(evidence, Mapping)
                    and evidence.get("clause_kind") == "condition"
                ] + [
                    {
                        "clause_kind": clause_kind,
                        "clause_index": 0,
                        "source_row_id": source_row_id,
                        "exact_source_fragment": exact_fragment,
                    }
                    for clause_kind in ("action", "oracle")
                ]
                obligation = copy.deepcopy(dict(base_obligation))
                obligation.update(
                    {
                        "obligation_id": obligation_id,
                        "linked_atom_id": atom_id,
                        "source_property_id": "none_required",
                        "property_type": "exact-length",
                        "obligation_class": "candidate-ui-calibration",
                        "required_behavior": (
                            f"Проверить отдельный класс {class_id} значения «{value}» "
                            f"для exact-length {exact_length} без выдумывания UI-реакции."
                        ),
                        "source_ref": requirement_code or source_row_id,
                        "planned_tc_id": test_case_id,
                        "review_notes": "candidate-ui-calibration",
                        "design_dimension": "boundary",
                        "planned_check": (
                            f"Ввести «{value}» ({class_id}) и зафиксировать "
                            "фактическую наблюдаемую UI-реакцию."
                        ),
                        "check_type": "boundary",
                        "coverage_class": f"exact-length-{slug}",
                        "input_class": f"{class_id}:{value}",
                        "single_expected_behavior": (
                            f"Точная реакция на «{value}» ({class_id}) устанавливается "
                            "наблюдением UI без предписания механизма."
                        ),
                        "oracle_source": "not_found",
                        "test_data": value,
                        "dictionary_refs": [],
                        "dictionary_coverage": "none_required",
                        "scope_obligation_ids": [],
                    }
                )
                additions.append((assertion, obligation))
                existing_ids.update(generated_ids)
            if not additions:
                continue
            base_index = assertions.index(base_assertion)
            new_assertions = [item[0] for item in additions]
            assertions[base_index + 1 : base_index + 1] = new_assertions
            new_obligations = [item[1] for item in additions]
            obligations.extend(new_obligations)
            obligations_by_id.update(
                {item["obligation_id"]: item for item in new_obligations}
            )
            new_atom_ids = [item["atom_id"] for item in new_assertions]
            new_test_case_ids = [
                item["planned_tc_id"] for item in new_obligations
            ]
            if isinstance(applicability, list):
                for row in applicability:
                    if (
                        isinstance(row, dict)
                        and row.get("dimension") in {"traceability", "boundary"}
                        and row.get("applicable") == "yes"
                    ):
                        row.setdefault("linked_atoms", []).extend(new_atom_ids)
                        row.setdefault("linked_test_cases", []).extend(
                            new_test_case_ids
                        )
            repairs.append(
                {
                    "rule": "materialize-exact-length-boundary-candidates",
                    "path": f"$.source_designs[{source_index}]",
                    "source_row_id": source_row_id,
                    "requirement_code": requirement_code or "none_required",
                    "exact_length": exact_length,
                    "added_classes": [
                        item[1]["input_class"].split(":", 1)[0]
                        for item in additions
                    ],
                    "base_assertion_id": str(
                        base_assertion.get("assertion_id", "")
                    ),
                }
            )
    return repairs


def _materialize_missing_definition_gap_assertions(
    payload: dict[str, Any],
    boundary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Give a partial missing-definition gap its own non-executable atom."""

    designs_by_row = {
        str(item.get("source_row_id", "")): item
        for item in payload.get("source_designs", [])
        if isinstance(item, dict)
    }
    existing_assertion_ids = {
        str(assertion.get("assertion_id", ""))
        for design in designs_by_row.values()
        for assertion in design.get("assertions", [])
        if isinstance(assertion, Mapping)
    }
    existing_atom_ids = {
        str(assertion.get("atom_id", ""))
        for design in designs_by_row.values()
        for assertion in design.get("assertions", [])
        if isinstance(assertion, Mapping)
    }
    repairs: list[dict[str, Any]] = []
    for gap in boundary.get("gaps", []):
        if (
            not isinstance(gap, Mapping)
            or gap.get("gap_type") != "missing-source-definition"
            or gap.get("blocking") is not False
            or gap.get("downstream_handling") != "carry-to-source-model"
        ):
            continue
        gap_id = str(gap.get("gap_id", ""))
        gap_fragments = tuple(
            normalize_exact_source_text(str(value))
            for value in gap.get("exact_source_fragments", [])
            if str(value).strip()
        )
        if not gap_id or not gap_fragments:
            continue
        for row_id in map(str, gap.get("source_row_ids", [])):
            source_design = designs_by_row.get(row_id)
            if source_design is None:
                continue
            assertions = source_design.get("assertions", [])
            if not isinstance(assertions, list):
                continue

            def matching_evidence(
                assertion: Mapping[str, Any],
            ) -> list[dict[str, Any]]:
                result: list[dict[str, Any]] = []
                for raw in assertion.get("requirement_code_evidence", []):
                    if not isinstance(raw, Mapping):
                        continue
                    evidence_fragment = normalize_exact_source_text(
                        str(raw.get("exact_source_fragment", ""))
                    )
                    if any(
                        fragment in evidence_fragment
                        or evidence_fragment in fragment
                        for fragment in gap_fragments
                        if evidence_fragment
                    ):
                        result.append(dict(raw))
                return result

            if any(
                isinstance(assertion, Mapping)
                and assertion.get("semantic_disposition")
                in {"ambiguous", "not-applicable"}
                and matching_evidence(assertion)
                for assertion in assertions
            ):
                continue
            owner = next(
                (
                    (assertion, evidence)
                    for assertion in assertions
                    if isinstance(assertion, Mapping)
                    for evidence in (matching_evidence(assertion),)
                    if evidence
                ),
                None,
            )
            if owner is None:
                continue
            owner_assertion, evidence = owner
            assertion_id = f"ASSERT-{row_id.removeprefix('SRC-')}-{gap_id}"
            atom_id = f"ATOM-{row_id.removeprefix('SRC-')}-{gap_id}"
            if assertion_id in existing_assertion_ids or atom_id in existing_atom_ids:
                continue
            # The executable sibling remains the sole owner of the requirement
            # code.  This mixed-observability sibling is code-less and is traced
            # through the exact GAP/source fragment only.
            requirement_codes: list[str] = []
            fragment_label = "; ".join(gap_fragments)
            assertions.append(
                {
                    "assertion_id": assertion_id,
                    "canonical_statement": (
                        "Source row не определяет локальное поведение "
                        f"элементов: {fragment_label}."
                    ),
                    "polarity": "neutral",
                    "semantic_disposition": "not-applicable",
                    "execution_readiness": "not-applicable",
                    "execution_readiness_rationale": "none_required",
                    "risk": "medium",
                    "condition_clauses": [],
                    "action_clauses": [],
                    "oracle_clauses": [],
                    "requirement_codes": requirement_codes,
                    "requirement_code_evidence": [],
                    "clause_evidence": [],
                    "supporting_source_bindings": [],
                    "clarification_clause_bindings": [],
                    "atom_id": atom_id,
                    "obligation_ids": [],
                    "disposition_rationale": (
                        f"{gap_id} из authoritative boundary отделяет "
                        "неопределённую часть от соседнего исполнимого поведения."
                    ),
                    "source_property_id": "none_required",
                    "field_or_block": str(
                        owner_assertion.get("field_or_block", row_id)
                    ),
                    "source_reference": str(
                        owner_assertion.get("source_reference", row_id)
                    ),
                }
            )
            existing_assertion_ids.add(assertion_id)
            existing_atom_ids.add(atom_id)
            repairs.append(
                {
                    "rule": "split-missing-definition-gap-from-executable-row",
                    "path": f"$.source_designs[{row_id}].assertions[-1]",
                    "gap_id": gap_id,
                    "source_row_id": row_id,
                    "assertion_id": assertion_id,
                    "atom_id": atom_id,
                    "requirement_codes": requirement_codes,
                }
            )
    return repairs


def normalize_semantic_design_transport(
    payload: Mapping[str, Any],
    *,
    context: Mapping[str, Any] | None = None,
    boundary: Mapping[str, Any] | None = None,
    repo_root: Path | None = None,
    fixture_context: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Repair only mechanically provable bridge transport fields."""

    normalized, source_property_receipt = (
        normalize_semantic_design_source_property_transport(payload)
    )
    repairs = list(source_property_receipt["repairs"])
    if context is not None and boundary is not None:
        header_projection = _semantic_transport_header_projection(
            normalized,
            context,
            boundary,
        )
        if header_projection is not None:
            normalized.update(header_projection["expected"])
            repairs.append(
                {
                    "rule": "bind-semantic-transport-header-to-authoritative-boundary",
                    "path": "$",
                    "changed_fields": header_projection["changed_fields"],
                    "previous_value_sha256": header_projection[
                        "previous_value_sha256"
                    ],
                }
            )
    source_designs = normalized.get("source_designs", [])
    obligations_by_id = {
        str(item.get("obligation_id", "")): item
        for item in normalized.get("obligations", [])
        if isinstance(item, dict)
    }
    fixture_contracts = (
        _load_verified_fixture_contracts(fixture_context or context, repo_root)
        if context is not None
        else {}
    )
    if context is not None and isinstance(source_designs, list):
        context_rows = {
            str(row.get("source_row_id", "")): row
            for row in context.get("source_rows", [])
            if isinstance(row, Mapping)
        }
        for source_index, source_design in enumerate(source_designs):
            if not isinstance(source_design, dict):
                continue
            source_row_id = str(source_design.get("source_row_id", ""))
            source_row = context_rows.get(source_row_id)
            assertions = source_design.get("assertions", [])
            if source_row is None or not isinstance(assertions, list):
                continue
            for assertion_index, assertion in enumerate(assertions):
                if not isinstance(assertion, dict):
                    continue
                read_only_projection = _read_only_action_control_projection(
                    assertion,
                    source_row,
                )
                if read_only_projection is not None:
                    previous_sha256 = canonical_payload_sha256(
                        {
                            field: assertion.get(field)
                            for field in (
                                "canonical_statement",
                                "condition_clauses",
                                "action_clauses",
                                "oracle_clauses",
                            )
                        }
                    )
                    obligation_fields = read_only_projection.pop(
                        "obligation_fields"
                    )
                    assertion.update(read_only_projection)
                    for obligation_id in map(
                        str, assertion.get("obligation_ids", [])
                    ):
                        obligation = obligations_by_id.get(obligation_id)
                        if isinstance(obligation, dict):
                            obligation.update(obligation_fields)
                    repairs.append(
                        {
                            "rule": "canonicalize-read-only-action-control",
                            "path": (
                                f"$.source_designs[{source_index}].assertions"
                                f"[{assertion_index}]"
                            ),
                            "source_row_id": source_row_id,
                            "assertion_id": str(
                                assertion.get("assertion_id", "")
                            ),
                            "previous_value_sha256": previous_sha256,
                        }
                    )
                inclusive_projection = _inclusive_twentieth_birthday_projection(
                    assertion,
                    [
                        item
                        for item in context.get("approved_clarifications", [])
                        if isinstance(item, Mapping)
                    ],
                )
                if inclusive_projection is not None:
                    previous_sha256 = canonical_payload_sha256(
                        {
                            field: assertion.get(field)
                            for field in (
                                "canonical_statement",
                                "condition_clauses",
                            )
                        }
                    )
                    obligation_fields = inclusive_projection.pop(
                        "obligation_fields"
                    )
                    assertion.update(inclusive_projection)
                    for obligation_id in map(
                        str, assertion.get("obligation_ids", [])
                    ):
                        obligation = obligations_by_id.get(obligation_id)
                        if isinstance(obligation, dict):
                            obligation.update(obligation_fields)
                    repairs.append(
                        {
                            "rule": "preserve-approved-inclusive-age-boundary",
                            "path": (
                                f"$.source_designs[{source_index}].assertions"
                                f"[{assertion_index}]"
                            ),
                            "source_row_id": source_row_id,
                            "assertion_id": str(
                                assertion.get("assertion_id", "")
                            ),
                            "previous_value_sha256": previous_sha256,
                        }
                    )
                future_date_projection = _future_issue_date_save_block_projection(
                    assertion,
                    [
                        item
                        for item in context.get("approved_clarifications", [])
                        if isinstance(item, Mapping)
                    ],
                )
                if future_date_projection is not None:
                    previous_sha256 = canonical_payload_sha256(
                        {
                            "oracle_clauses": assertion.get("oracle_clauses"),
                            "obligations": [
                                obligations_by_id.get(str(obligation_id))
                                for obligation_id in assertion.get(
                                    "obligation_ids", []
                                )
                            ],
                        }
                    )
                    obligation_fields = future_date_projection.pop(
                        "obligation_fields"
                    )
                    assertion.update(future_date_projection)
                    for obligation_id in map(
                        str, assertion.get("obligation_ids", [])
                    ):
                        obligation = obligations_by_id.get(obligation_id)
                        if isinstance(obligation, dict):
                            obligation.update(obligation_fields)
                    repairs.append(
                        {
                            "rule": "preserve-approved-future-date-save-block",
                            "path": (
                                f"$.source_designs[{source_index}].assertions"
                                f"[{assertion_index}]"
                            ),
                            "source_row_id": source_row_id,
                            "assertion_id": str(
                                assertion.get("assertion_id", "")
                            ),
                            "previous_value_sha256": previous_sha256,
                        }
                    )
                fixture_projection = _verified_fixture_clause_projection(
                    assertion,
                    obligations_by_id,
                    fixture_contracts,
                )
                if fixture_projection is not None:
                    previous_sha256 = canonical_payload_sha256(
                        {
                            field: assertion.get(field)
                            for field in (
                                "canonical_statement",
                                "condition_clauses",
                                "action_clauses",
                                "oracle_clauses",
                                "disposition_rationale",
                            )
                        }
                    )
                    obligation_fields = fixture_projection.pop(
                        "obligation_fields"
                    )
                    assertion.update(fixture_projection)
                    for obligation_id in map(
                        str, assertion.get("obligation_ids", [])
                    ):
                        obligation = obligations_by_id.get(obligation_id)
                        if isinstance(obligation, dict):
                            obligation.update(obligation_fields)
                    repairs.append(
                        {
                            "rule": "bind-exact-verified-fixture-literals",
                            "path": (
                                f"$.source_designs[{source_index}].assertions"
                                f"[{assertion_index}]"
                            ),
                            "source_row_id": source_row_id,
                            "assertion_id": str(
                                assertion.get("assertion_id", "")
                            ),
                            "previous_value_sha256": previous_sha256,
                        }
                    )
                calibration_previous_sha256 = canonical_payload_sha256(
                    {
                        "oracle_clauses": assertion.get("oracle_clauses"),
                        "obligations": [
                            obligations_by_id.get(str(obligation_id))
                            for obligation_id in assertion.get(
                                "obligation_ids", []
                            )
                        ],
                    }
                )
                if _canonicalize_declared_ui_calibration(
                    assertion,
                    obligations_by_id,
                ):
                    repairs.append(
                        {
                            "rule": "canonicalize-declared-ui-calibration-candidate",
                            "path": (
                                f"$.source_designs[{source_index}].assertions"
                                f"[{assertion_index}]"
                            ),
                            "source_row_id": source_row_id,
                            "assertion_id": str(
                                assertion.get("assertion_id", "")
                            ),
                            "previous_value_sha256": calibration_previous_sha256,
                        }
                    )
                block_heading = _BLOCK_HEADING_SOURCE_PATTERN.fullmatch(
                    str(source_row.get("bounded_source_text", "")).strip()
                )
                oracle_clauses = assertion.get("oracle_clauses", [])
                if block_heading is not None and isinstance(oracle_clauses, list):
                    for oracle_index, oracle_clause in enumerate(oracle_clauses):
                        wrapped = _DOUBLE_WRAPPED_BLOCK_ORACLE_PATTERN.fullmatch(
                            str(oracle_clause).strip()
                        )
                        if (
                            wrapped is None
                            or wrapped.group("title") != block_heading.group("title")
                        ):
                            continue
                        punctuation = wrapped.group("punctuation") or "."
                        canonical_oracle = (
                            f"Отображается блок «{block_heading.group('title')}»"
                            f"{punctuation}"
                        )
                        repairs.append(
                            {
                                "rule": "canonicalize-double-wrapped-block-heading",
                                "path": (
                                    f"$.source_designs[{source_index}].assertions"
                                    f"[{assertion_index}].oracle_clauses"
                                    f"[{oracle_index}]"
                                ),
                                "source_row_id": source_row_id,
                                "assertion_id": str(
                                    assertion.get("assertion_id", "")
                                ),
                                "previous_value_sha256": hashlib.sha256(
                                    str(oracle_clause).encode("utf-8")
                                ).hexdigest(),
                            }
                        )
                        oracle_clauses[oracle_index] = canonical_oracle
                projection = _always_visibility_source_backed_clause_projection(
                    assertion,
                    source_row,
                )
                repair_rule = "materialize-always-visibility-prestate-pair"
                if projection is None:
                    projection = _always_visibility_direct_observation_projection(
                        assertion,
                        source_row,
                    )
                    repair_rule = "canonicalize-always-visibility-direct-observation"
                if projection is None:
                    continue
                previous_sha256 = canonical_payload_sha256(
                    {
                        field: assertion.get(field)
                        for field in (
                            "condition_clauses",
                            "action_clauses",
                            "oracle_clauses",
                            "clause_evidence",
                        )
                    }
                )
                obligation_fields = projection.pop("obligation_fields", None)
                assertion.update(projection)
                if isinstance(obligation_fields, Mapping):
                    for obligation_id in map(str, assertion.get("obligation_ids", [])):
                        obligation = obligations_by_id.get(obligation_id)
                        if isinstance(obligation, dict):
                            obligation.update(obligation_fields)
                repairs.append(
                    {
                        "rule": repair_rule,
                        "path": (
                            f"$.source_designs[{source_index}].assertions"
                            f"[{assertion_index}]"
                        ),
                        "source_row_id": source_row_id,
                        "assertion_id": str(assertion.get("assertion_id", "")),
                        "previous_value_sha256": previous_sha256,
                    }
                )
    if context is not None:
        repairs.extend(
            _split_visibility_code_from_typed_requiredness(
                normalized,
                context,
            )
        )
        obligations_by_id = {
            str(item.get("obligation_id", "")): item
            for item in normalized.get("obligations", [])
            if isinstance(item, dict)
        }
    if context is not None and boundary is not None:
        repairs.extend(
            _materialize_bare_requirement_definition_gaps(
                normalized,
                context,
                boundary,
            )
        )
        repairs.extend(
            _materialize_missing_definition_gap_assertions(
                normalized,
                boundary,
            )
        )
    while True:
        split_projection = _collapsed_executable_negative_oracle_projection(
            normalized,
            context=context,
        )
        if split_projection is None:
            break
        split_source_design = normalized["source_designs"][
            int(split_projection["source_index"])
        ]
        split_assertions = split_source_design["assertions"]
        split_assertion_index = int(split_projection["assertion_index"])
        split_assertions[split_assertion_index : split_assertion_index + 1] = (
            split_projection["new_assertions"]
        )
        split_obligation_index = int(split_projection["obligation_index"])
        normalized["obligations"][
            split_obligation_index : split_obligation_index + 1
        ] = split_projection["new_obligations"]
        for oracle_index, new_oracle in zip(
            split_projection["oracle_indices"],
            split_projection["new_oracles"],
            strict=True,
        ):
            normalized["negative_oracles"][int(oracle_index)] = new_oracle
        normalized["dependency_bindings"] = split_projection[
            "canonical_dependency_bindings"
        ]
        repairs.append(
            {
                "rule": "split-branch-aligned-negative-oracle-chains",
                "path": (
                    f"$.source_designs[{split_projection['source_index']}].assertions"
                    f"[{split_projection['assertion_index']}]"
                ),
                "original_assertion_id": split_projection[
                    "original_assertion_id"
                ],
                "original_obligation_id": split_projection[
                    "original_obligation_id"
                ],
                "scope_obligation_ids": split_projection[
                    "scope_obligation_ids"
                ],
            }
        )
    while True:
        calibration_projection = _combined_calibration_allowed_class_projection(
            normalized,
            context=context,
        )
        if calibration_projection is None:
            break
        calibration_source_design = normalized["source_designs"][
            int(calibration_projection["source_index"])
        ]
        calibration_assertions = calibration_source_design["assertions"]
        calibration_assertion_index = int(
            calibration_projection["assertion_index"]
        )
        calibration_assertions[
            calibration_assertion_index : calibration_assertion_index + 1
        ] = [
            calibration_projection["positive_assertion"],
            calibration_projection["negative_assertion"],
        ]
        calibration_obligation_index = int(
            calibration_projection["obligation_index"]
        )
        normalized["obligations"][
            calibration_obligation_index : calibration_obligation_index + 1
        ] = [
            calibration_projection["positive_obligation"],
            calibration_projection["negative_obligation"],
        ]
        normalized["dependency_bindings"] = calibration_projection[
            "canonical_dependency_bindings"
        ]
        repairs.append(
            {
                "rule": "split-calibration-allowed-class-companion",
                "path": (
                    f"$.source_designs[{calibration_projection['source_index']}]"
                    f".assertions[{calibration_projection['assertion_index']}]"
                ),
                "original_assertion_id": calibration_projection[
                    "original_assertion_id"
                ],
                "scope_obligation_id": calibration_projection[
                    "scope_obligation_id"
                ],
            }
        )
    if context is not None:
        repairs.extend(
            _materialize_missing_exact_length_boundaries(normalized, context)
        )
    if context is not None and isinstance(source_designs, list):
        projections = _typed_interpretation_support_alias_projections(
            normalized,
            context,
        )
        removal_indices: dict[tuple[int, int], set[int]] = {}
        for projection in projections:
            key = (
                int(projection["source_index"]),
                int(projection["assertion_index"]),
            )
            removal_indices.setdefault(key, set()).add(
                int(projection["binding_index"])
            )
            repairs.append(
                {
                    "rule": "drop-typed-interpretation-row-support-alias",
                    "path": (
                        f"$.source_designs[{key[0]}].assertions[{key[1]}]"
                        f".supporting_source_bindings[{projection['binding_index']}]"
                    ),
                    "assertion_id": projection["assertion_id"],
                    "source_property_id": projection["source_property_id"],
                    "interpretation_source": projection["interpretation_source"],
                }
            )
        for (source_index, assertion_index), removed in removal_indices.items():
            source_design = source_designs[source_index]
            if not isinstance(source_design, dict):
                continue
            assertions = source_design.get("assertions", [])
            if not isinstance(assertions, list):
                continue
            assertion = assertions[assertion_index]
            if not isinstance(assertion, dict):
                continue
            supporting = assertion.get("supporting_source_bindings", [])
            if isinstance(supporting, list):
                assertion["supporting_source_bindings"] = [
                    binding
                    for binding_index, binding in enumerate(supporting)
                    if binding_index not in removed
                ]
    if context is not None and isinstance(source_designs, list):
        for projection in _clarification_missing_code_projections(
            normalized,
            context,
        ):
            source_design = source_designs[int(projection["source_index"])]
            if not isinstance(source_design, dict):
                continue
            assertions = source_design.get("assertions", [])
            if not isinstance(assertions, list):
                continue
            assertion = assertions[int(projection["assertion_index"])]
            if not isinstance(assertion, dict):
                continue
            bindings = assertion.get("clarification_clause_bindings", [])
            if not isinstance(bindings, list):
                continue
            binding = bindings[int(projection["binding_index"])]
            if not isinstance(binding, dict):
                continue
            code = str(projection["requirement_code"])
            binding["requirement_codes"] = [code]
            inherited = bool(projection["inherit_code"])
            if inherited:
                assertion["requirement_codes"] = [code]
                evidence = assertion.get("requirement_code_evidence", [])
                if not isinstance(evidence, list):
                    continue
                evidence.append(projection["canonical_evidence"])
            repairs.append(
                {
                    "rule": (
                        "inherit-unique-clarification-code-from-sibling-evidence"
                        if inherited
                        else "bind-unique-local-clarification-code"
                    ),
                    "path": (
                        f"$.source_designs[{projection['source_index']}].assertions"
                        f"[{projection['assertion_index']}].clarification_clause_bindings"
                        f"[{projection['binding_index']}].requirement_codes"
                    ),
                    "source_row_id": projection["source_row_id"],
                    "assertion_id": projection["assertion_id"],
                    "clarification_id": projection["clarification_id"],
                    "requirement_code": code,
                }
            )
    if context is not None:
        for projection in _repeated_requirement_code_evidence_span_projections(
            normalized,
            context,
        ):
            source_design = normalized["source_designs"][
                int(projection["source_index"])
            ]
            assertion = source_design["assertions"][
                int(projection["assertion_index"])
            ]
            binding = assertion["requirement_code_evidence"][
                int(projection["binding_index"])
            ]
            binding["exact_source_fragment"] = projection["canonical_span"]
            repairs.append(
                {
                    "rule": "expand-repeated-requirement-code-to-literal-source-span",
                    "path": (
                        f"$.source_designs[{projection['source_index']}].assertions"
                        f"[{projection['assertion_index']}].requirement_code_evidence"
                        f"[{projection['binding_index']}].exact_source_fragment"
                    ),
                    "source_row_id": projection["source_row_id"],
                    "assertion_id": projection["assertion_id"],
                    "requirement_code": projection["requirement_code"],
                    "previous_value_sha256": projection["previous_value_sha256"],
                }
            )
    if isinstance(source_designs, list):
        for source_index, source_design in enumerate(source_designs):
            if not isinstance(source_design, dict):
                continue
            primary_row = str(source_design.get("source_row_id", ""))
            assertions = source_design.get("assertions", [])
            if not isinstance(assertions, list):
                continue
            for assertion_index, assertion in enumerate(assertions):
                if not isinstance(assertion, dict):
                    continue
                assertion_path = (
                    f"$.source_designs[{source_index}].assertions[{assertion_index}]"
                )
                assertion_codes = assertion.get("requirement_codes")
                clarification_bindings = assertion.get(
                    "clarification_clause_bindings"
                )
                if isinstance(assertion_codes, list) and isinstance(
                    clarification_bindings, list
                ):
                    assertion_code_set = set(map(str, assertion_codes))
                    for binding_index, binding in enumerate(clarification_bindings):
                        if (
                            not isinstance(binding, dict)
                            or binding.get("binding_scope") != "requirement-code"
                            or not isinstance(binding.get("requirement_codes"), list)
                        ):
                            continue
                        binding_codes = list(map(str, binding["requirement_codes"]))
                        retained_codes = [
                            code for code in binding_codes if code in assertion_code_set
                        ]
                        if not retained_codes or retained_codes == binding_codes:
                            continue
                        repairs.append(
                            {
                                "rule": "restrict-clarification-codes-to-owning-assertion",
                                "path": (
                                    f"{assertion_path}.clarification_clause_bindings"
                                    f"[{binding_index}].requirement_codes"
                                ),
                                "previous_value_sha256": hashlib.sha256(
                                    json.dumps(
                                        binding_codes,
                                        ensure_ascii=False,
                                        separators=(",", ":"),
                                    ).encode("utf-8")
                                ).hexdigest(),
                            }
                        )
                        binding["requirement_codes"] = retained_codes
                supporting = assertion.get("supporting_source_bindings")
                is_clause_free_na = (
                    assertion.get("semantic_disposition") == "not-applicable"
                    and all(
                        assertion.get(field) == []
                        for field in (
                            "condition_clauses",
                            "action_clauses",
                            "oracle_clauses",
                            "obligation_ids",
                        )
                    )
                )
                if is_clause_free_na and isinstance(supporting, list):
                    retained: list[Any] = []
                    for binding_index, binding in enumerate(supporting):
                        if (
                            isinstance(binding, Mapping)
                            and str(binding.get("source_row_id", "")) == primary_row
                        ):
                            repairs.append(
                                {
                                    "rule": "remove-redundant-na-primary-self-support",
                                    "path": (
                                        f"{assertion_path}.supporting_source_bindings"
                                        f"[{binding_index}]"
                                    ),
                                }
                            )
                        else:
                            retained.append(binding)
                    assertion["supporting_source_bindings"] = retained
                requirement_evidence = assertion.get("requirement_code_evidence")
                if not isinstance(requirement_evidence, list):
                    continue
                duplicate_codes = {
                    str(binding.get("requirement_code", ""))
                    for binding in requirement_evidence
                    if isinstance(binding, Mapping)
                    and sum(
                        isinstance(candidate, Mapping)
                        and str(candidate.get("requirement_code", ""))
                        == str(binding.get("requirement_code", ""))
                        for candidate in requirement_evidence
                    )
                    > 1
                }
                redundant_indices = {
                    index
                    for code in duplicate_codes
                    if (
                        index := _redundant_pdf_parity_index(
                            requirement_evidence,
                            requirement_code=code,
                            source_row_id=primary_row,
                        )
                    )
                    is not None
                }
                if redundant_indices:
                    for binding_index in sorted(redundant_indices):
                        repairs.append(
                            {
                                "rule": "drop-redundant-pdf-parity-for-xhtml-code",
                                "path": (
                                    f"{assertion_path}.requirement_code_evidence"
                                    f"[{binding_index}]"
                                ),
                                "previous_value_sha256": canonical_payload_sha256(
                                    requirement_evidence[binding_index]
                                ),
                            }
                        )
                    requirement_evidence = [
                        binding
                        for binding_index, binding in enumerate(requirement_evidence)
                        if binding_index not in redundant_indices
                    ]
                    assertion["requirement_code_evidence"] = requirement_evidence
                for binding_index, binding in enumerate(requirement_evidence):
                    if not isinstance(binding, dict) or binding.get(
                        "provenance_role"
                    ) != "xhtml-row":
                        continue
                    for field in ("evidence_source_path", "evidence_locator"):
                        if binding.get(field) == "none_required":
                            continue
                        repairs.append(
                            {
                                "rule": "clear-pdf-fields-for-xhtml-provenance",
                                "path": (
                                    f"{assertion_path}.requirement_code_evidence"
                                    f"[{binding_index}].{field}"
                                ),
                                "previous_value_sha256": hashlib.sha256(
                                    str(binding.get(field, "")).encode("utf-8")
                                ).hexdigest(),
                            }
                        )
                        binding[field] = "none_required"
    dependency_bindings = normalized.get("dependency_bindings", [])
    if boundary is not None:
        missing_projection = _missing_scope_excluded_dependency_projection(
            normalized,
            boundary,
        )
        if missing_projection is not None:
            normalized["dependency_bindings"] = missing_projection[
                "canonical_bindings"
            ]
            dependency_bindings = normalized["dependency_bindings"]
            repairs.append(
                {
                    "rule": "materialize-missing-scope-excluded-dependency-bindings",
                    "path": "$.dependency_bindings",
                    "missing_dependency_ids": missing_projection[
                        "missing_dependency_ids"
                    ],
                    "previous_value_sha256": missing_projection[
                        "previous_value_sha256"
                    ],
                }
            )
    if boundary is not None and isinstance(dependency_bindings, list):
        for projection in _dependency_transport_projections(
            normalized,
            boundary,
        ):
            binding_index = int(projection["binding_index"])
            binding = dependency_bindings[binding_index]
            if not isinstance(binding, dict):
                continue
            binding.update(projection["canonical_fields"])
            repairs.append(
                {
                    "rule": "bind-dependency-transport-to-authoritative-boundary",
                    "path": f"$.dependency_bindings[{binding_index}]",
                    "dependency_id": projection["dependency_id"],
                    "changed_fields": projection["changed_fields"],
                    "previous_value_sha256": projection[
                        "previous_value_sha256"
                    ],
                }
            )
    if isinstance(dependency_bindings, list):
        for binding_index, binding in enumerate(dependency_bindings):
            if not isinstance(binding, dict):
                continue
            excluded_projection = _scope_excluded_na_link_projection(
                normalized,
                binding,
            )
            if excluded_projection is not None:
                repairs.append(
                    {
                        "rule": "clear-scope-excluded-na-dependency-links",
                        "path": f"$.dependency_bindings[{binding_index}]",
                        "dropped_assertion_ids": excluded_projection[
                            "dropped_assertion_ids"
                        ],
                        "previous_value_sha256": canonical_payload_sha256(binding),
                    }
                )
                for field in (
                    "linked_assertion_ids",
                    "linked_atom_ids",
                    "linked_obligation_ids",
                ):
                    binding[field] = excluded_projection[field]
            projection = _provable_dependency_overlink_projection(
                normalized,
                binding,
            )
            if projection is None:
                continue
            repairs.append(
                {
                    "rule": "drop-dependency-overlinks-without-literal-evidence",
                    "path": f"$.dependency_bindings[{binding_index}]",
                    "dropped_assertion_ids": projection[
                        "dropped_assertion_ids"
                    ],
                    "previous_value_sha256": canonical_payload_sha256(binding),
                }
            )
            for field in (
                "linked_assertion_ids",
                "linked_atom_ids",
                "linked_obligation_ids",
            ):
                binding[field] = projection[field]
    if context is not None:
        for projection in _same_row_clause_evidence_span_projections(
            normalized,
            context,
        ):
            source_designs = normalized.get("source_designs", [])
            if not isinstance(source_designs, list):
                continue
            source_design = source_designs[int(projection["source_index"])]
            if not isinstance(source_design, dict):
                continue
            assertions = source_design.get("assertions", [])
            if not isinstance(assertions, list):
                continue
            assertion = assertions[int(projection["assertion_index"])]
            if not isinstance(assertion, dict):
                continue
            repairs.append(
                {
                    "rule": "merge-same-row-clause-evidence-span",
                    "path": projection["path"],
                    "merged_clause_keys": projection["merged_clause_keys"],
                    "previous_value_sha256": canonical_payload_sha256(
                        {
                            "clause_evidence": assertion.get(
                                "clause_evidence", []
                            )
                        }
                    ),
                }
            )
            assertion["clause_evidence"] = projection["canonical_evidence"]
        for projection in _typed_property_missing_literal_evidence_projections(
            normalized,
            context,
        ):
            source_designs = normalized.get("source_designs", [])
            if not isinstance(source_designs, list):
                continue
            source_design = source_designs[int(projection["source_index"])]
            if not isinstance(source_design, dict):
                continue
            assertions = source_design.get("assertions", [])
            if not isinstance(assertions, list):
                continue
            assertion = assertions[int(projection["assertion_index"])]
            if not isinstance(assertion, dict):
                continue
            evidence = assertion.get("clause_evidence", [])
            if not isinstance(evidence, list):
                continue
            binding = evidence[int(projection["evidence_index"])]
            if not isinstance(binding, dict):
                continue
            binding["exact_source_fragment"] = projection["canonical_span"]
            repairs.append(
                {
                    "rule": "bind-typed-property-to-exact-source-cell-value",
                    "path": projection["path"],
                    "assertion_id": projection["assertion_id"],
                    "source_property_id": projection["source_property_id"],
                    "source_row_id": projection["source_row_id"],
                    "source_cell_locator": projection["source_cell_locator"],
                    "source_value": projection["source_value"],
                    "previous_value_sha256": projection[
                        "previous_value_sha256"
                    ],
                }
            )
        for projection in _necessary_control_missing_clause_evidence_projections(
            normalized,
            context,
        ):
            source_designs = normalized.get("source_designs", [])
            if not isinstance(source_designs, list):
                continue
            source_design = source_designs[int(projection["source_index"])]
            if not isinstance(source_design, dict):
                continue
            assertions = source_design.get("assertions", [])
            if not isinstance(assertions, list):
                continue
            assertion = assertions[int(projection["assertion_index"])]
            if not isinstance(assertion, dict):
                continue
            repairs.append(
                {
                    "rule": "bind-derived-necessary-control-to-full-source-rule",
                    "path": projection["path"],
                    "assertion_id": projection["assertion_id"],
                    "repaired_evidence_indices": projection[
                        "repaired_evidence_indices"
                    ],
                    "previous_value_sha256": canonical_payload_sha256(
                        {"clause_evidence": assertion.get("clause_evidence", [])}
                    ),
                }
            )
            assertion["clause_evidence"] = projection["canonical_evidence"]
    if context is not None and boundary is not None:
        for projection in _clarification_exclusion_oracle_projections(
            normalized,
            context,
            boundary,
        ):
            source_design = normalized["source_designs"][
                int(projection["source_index"])
            ]
            assertion = source_design["assertions"][
                int(projection["assertion_index"])
            ]
            oracle_index = int(projection["oracle_index"])
            evidence_index = int(projection["evidence_index"])
            previous = {
                "oracle": assertion["oracle_clauses"][oracle_index],
                "evidence": assertion["clause_evidence"][evidence_index],
            }
            assertion["oracle_clauses"][oracle_index] = projection[
                "canonical_oracle"
            ]
            assertion["clause_evidence"][evidence_index][
                "exact_source_fragment"
            ] = projection["canonical_evidence"]
            repairs.append(
                {
                    "rule": "bind-scope-exclusion-clarification-to-visible-source-oracle",
                    "path": (
                        f"$.source_designs[{projection['source_index']}].assertions"
                        f"[{projection['assertion_index']}].oracle_clauses"
                        f"[{oracle_index}]"
                    ),
                    "source_row_id": projection["source_row_id"],
                    "assertion_id": projection["assertion_id"],
                    "clarification_id": projection["clarification_id"],
                    "previous_value_sha256": canonical_payload_sha256(previous),
                }
            )
        for projection in _binary_optional_candidate_default_projections(
            normalized,
            context,
            boundary,
        ):
            source_design = normalized["source_designs"][
                int(projection["source_index"])
            ]
            assertion = source_design["assertions"][
                int(projection["assertion_index"])
            ]
            obligation = normalized["obligations"][
                int(projection["obligation_index"])
            ]
            oracle = normalized["requiredness_oracles"][
                int(projection["oracle_index"])
            ]
            repairs.append(
                {
                    "rule": (
                        "bind-optional-action-control-to-no-action-contract"
                        if projection.get("fallback_input_mode")
                        == "no-action-control"
                        else "bind-binary-optional-candidate-to-source-default"
                        if projection["restriction_type"] == "optionality"
                        else "bind-binary-requiredness-candidate-to-source-default"
                    ),
                    "path": projection["path"],
                    "source_row_id": projection["source_row_id"],
                    "assertion_id": projection["assertion_id"],
                    "scope_obligation_id": projection["scope_obligation_id"],
                    "previous_value_sha256": projection[
                        "previous_value_sha256"
                    ],
                }
            )
            assertion.update(projection["assertion_fields"])
            obligation.update(projection["obligation_fields"])
            oracle.update(projection["oracle_fields"])
        expected_requiredness_by_scope = {
            str(item["scope_obligation_id"]): item
            for item in semantic_source_signal_registry(context, boundary)[
                "requiredness"
            ]
        }
        for projection in _unsupported_executable_requiredness_candidate_projections(
            normalized,
            expected_signals_by_scope=expected_requiredness_by_scope,
        ):
            source_design = normalized["source_designs"][
                int(projection["source_index"])
            ]
            assertion = source_design["assertions"][
                int(projection["assertion_index"])
            ]
            obligation = normalized["obligations"][
                int(projection["obligation_index"])
            ]
            oracle = normalized["requiredness_oracles"][
                int(projection["oracle_index"])
            ]
            repairs.append(
                {
                    "rule": "downgrade-unobservable-requiredness-to-ui-calibration",
                    "path": projection["path"],
                    "scope_obligation_id": projection["scope_obligation_id"],
                    "source_requires_calibration": projection[
                        "source_requires_calibration"
                    ],
                    "previous_value_sha256": projection["previous_value_sha256"],
                }
            )
            assertion.update(projection["assertion_fields"])
            obligation.update(projection["obligation_fields"])
            oracle.update(projection["oracle_fields"])
        for projection in _candidate_fallback_clause_evidence_projections(
            normalized,
            context,
            boundary,
        ):
            source_designs = normalized.get("source_designs", [])
            if not isinstance(source_designs, list):
                continue
            source_design = source_designs[int(projection["source_index"])]
            if not isinstance(source_design, dict):
                continue
            assertions = source_design.get("assertions", [])
            if not isinstance(assertions, list):
                continue
            assertion = assertions[int(projection["assertion_index"])]
            if not isinstance(assertion, dict):
                continue
            repairs.append(
                {
                    "rule": "bind-candidate-fallback-clause-evidence-to-source-row",
                    "path": projection["path"],
                    "repaired_clause_keys": projection[
                        "repaired_clause_keys"
                    ],
                    "previous_value_sha256": canonical_payload_sha256(
                        {
                            "clause_evidence": assertion.get(
                                "clause_evidence", []
                            )
                        }
                    ),
                }
            )
            assertion["clause_evidence"] = projection["canonical_evidence"]
        for projection in _negative_candidate_clause_evidence_projections(
            normalized,
            context,
            boundary,
        ):
            source_design = normalized["source_designs"][
                int(projection["source_index"])
            ]
            assertion = source_design["assertions"][
                int(projection["assertion_index"])
            ]
            repairs.append(
                {
                    "rule": "bind-negative-candidate-clause-evidence-to-source-row",
                    "path": projection["path"],
                    "repaired_clause_keys": projection[
                        "repaired_clause_keys"
                    ],
                    "previous_value_sha256": canonical_payload_sha256(
                        {"clause_evidence": assertion.get("clause_evidence", [])}
                    ),
                }
            )
            assertion["clause_evidence"] = projection["canonical_evidence"]
        for projection in _executable_negative_signal_evidence_projections(
            normalized,
            context,
            boundary,
        ):
            source_design = normalized["source_designs"][
                int(projection["source_index"])
            ]
            assertion = source_design["assertions"][
                int(projection["assertion_index"])
            ]
            repairs.append(
                {
                    "rule": "expand-executable-negative-signal-clause-evidence",
                    "path": projection["path"],
                    "signal_id": projection["signal_id"],
                    "assertion_id": projection["assertion_id"],
                    "previous_value_sha256": canonical_payload_sha256(
                        {"clause_evidence": assertion.get("clause_evidence", [])}
                    ),
                }
            )
            assertion["clause_evidence"] = projection["canonical_evidence"]
    for projection in _candidate_oracle_source_alias_projections(normalized):
        collection = normalized.get(projection["collection_name"], [])
        if not isinstance(collection, list):
            continue
        item_index = int(projection["item_index"])
        item = collection[item_index]
        if not isinstance(item, dict):
            continue
        repairs.append(
            {
                "rule": "canonicalize-candidate-unknown-oracle-source",
                "path": projection["path"],
                "previous_value_sha256": hashlib.sha256(
                    str(item.get("oracle_source", "")).encode("utf-8")
                ).hexdigest(),
            }
        )
        item["oracle_source"] = projection["canonical_source"]
    if context is not None and boundary is not None:
        for projection in _candidate_signal_code_binding_projections(
            normalized,
            context,
            boundary,
        ):
            source_design = normalized["source_designs"][
                int(projection["source_index"])
            ]
            assertion = source_design["assertions"][
                int(projection["assertion_index"])
            ]
            repairs.append(
                {
                    "rule": "bind-candidate-signal-codes-to-owning-assertion",
                    "path": (
                        f"$.source_designs[{projection['source_index']}].assertions"
                        f"[{projection['assertion_index']}]"
                    ),
                    "signal_id": projection["signal_id"],
                    "missing_requirement_codes": projection[
                        "missing_requirement_codes"
                    ],
                    "previous_value_sha256": canonical_payload_sha256(
                        {
                            "requirement_codes": assertion.get(
                                "requirement_codes", []
                            ),
                            "requirement_code_evidence": assertion.get(
                                "requirement_code_evidence", []
                            ),
                        }
                    ),
                }
            )
            assertion["requirement_codes"] = projection[
                "canonical_requirement_codes"
            ]
            assertion["requirement_code_evidence"] = projection[
                "canonical_requirement_code_evidence"
            ]
    for projection in _external_dynamic_coverage_projections(normalized):
        obligation_index = int(projection["obligation_index"])
        obligations = normalized.get("obligations", [])
        if not isinstance(obligations, list):
            continue
        obligation = obligations[obligation_index]
        if not isinstance(obligation, dict):
            continue
        repairs.append(
            {
                "rule": "canonicalize-external-dynamic-dictionary-coverage",
                "path": f"$.obligations[{obligation_index}].dictionary_coverage",
                "previous_value_sha256": hashlib.sha256(
                    str(obligation.get("dictionary_coverage", "")).encode("utf-8")
                ).hexdigest(),
            }
        )
        obligation["dictionary_coverage"] = projection["dictionary_coverage"]
    for collection_name in ("negative_oracles", "requiredness_oracles"):
        collection = normalized.get(collection_name, [])
        if not isinstance(collection, list):
            continue
        for item_index, item in enumerate(collection):
            if not isinstance(item, dict) or item.get("decision") != "executable_tc":
                continue
            oracle_status = str(item.get("oracle_status", ""))
            canonical_status = ORACLE_STATUS_ALIASES.get(oracle_status)
            if canonical_status is None:
                continue
            repairs.append(
                {
                    "rule": "canonicalize-executable-oracle-status-alias",
                    "path": f"$.{collection_name}[{item_index}].oracle_status",
                    "previous_value_sha256": hashlib.sha256(
                        oracle_status.encode("utf-8")
                    ).hexdigest(),
                }
            )
            item["oracle_status"] = canonical_status
    if context is not None:
        rows_by_id = {
            str(item.get("source_row_id", "")): item
            for item in context.get("source_rows", [])
            if isinstance(item, Mapping)
        }
        expected_signal_registry = (
            semantic_source_signal_registry(context, boundary)
            if boundary is not None
            else None
        )
        expected_signals_by_collection = {
            collection_name: {
                str(item["signal_id"]): item
                for item in expected_signal_registry[registry_name]
            }
            for collection_name, registry_name in (
                ("negative_oracles", "negative"),
                ("requiredness_oracles", "requiredness"),
            )
        } if expected_signal_registry is not None else {}
        for collection_name in ("negative_oracles", "requiredness_oracles"):
            collection = normalized.get(collection_name, [])
            if not isinstance(collection, list):
                continue
            for item_index, item in enumerate(collection):
                if not isinstance(item, dict):
                    continue
                row = rows_by_id.get(str(item.get("source_row_id", "")))
                if row is None:
                    continue
                expected_signal = expected_signals_by_collection.get(
                    collection_name,
                    {},
                ).get(str(item.get("signal_id", "")))
                expected = {
                    "source_ref": str(
                        expected_signal.get("source_ref", "")
                        if expected_signal is not None
                        else row.get("source_ref", "")
                    ),
                    "field_or_block": str(
                        expected_signal.get("field_or_block", "")
                        if expected_signal is not None
                        else row.get("field_or_action", "")
                    ),
                }
                for field, expected_value in expected.items():
                    if item.get(field) == expected_value:
                        continue
                    repairs.append(
                        {
                            "rule": "bind-source-signal-row-identity",
                            "path": f"$.{collection_name}[{item_index}].{field}",
                            "previous_value_sha256": hashlib.sha256(
                                str(item.get(field, "")).encode("utf-8")
                            ).hexdigest(),
                        }
                    )
                    item[field] = expected_value
        if expected_signal_registry is not None:
            for collection_name, registry_name in (
                ("negative_oracles", "negative"),
                ("requiredness_oracles", "requiredness"),
            ):
                collection = normalized.get(collection_name, [])
                if not isinstance(collection, list):
                    continue
                expected_by_id = {
                    str(item["signal_id"]): item
                    for item in expected_signal_registry[registry_name]
                }
                for item_index, item in enumerate(collection):
                    if not isinstance(item, dict):
                        continue
                    expected_signal = expected_by_id.get(
                        str(item.get("signal_id", ""))
                    )
                    if expected_signal is None:
                        continue
                    expected_scope_id = str(
                        expected_signal["scope_obligation_id"]
                    )
                    if item.get("scope_obligation_id") == expected_scope_id:
                        pass
                    else:
                        repairs.append(
                            {
                                "rule": "bind-source-signal-canonical-scope-id",
                                "path": (
                                    f"$.{collection_name}[{item_index}]"
                                    ".scope_obligation_id"
                                ),
                                "previous_value_sha256": hashlib.sha256(
                                    str(item.get("scope_obligation_id", "")).encode(
                                        "utf-8"
                                    )
                                ).hexdigest(),
                            }
                        )
                        item["scope_obligation_id"] = expected_scope_id
                    if (
                        collection_name == "requiredness_oracles"
                        and expected_signal.get("source_binding")
                        == "typed-xhtml-cell"
                        and item.get("requiredness_source")
                        == "typed-xhtml-cell"
                    ):
                        repairs.append(
                            {
                                "rule": "bind-typed-requiredness-source-cell-value",
                                "path": (
                                    f"$.{collection_name}[{item_index}]"
                                    ".requiredness_source"
                                ),
                                "previous_value_sha256": hashlib.sha256(
                                    b"typed-xhtml-cell"
                                ).hexdigest(),
                                "source_cell_locator": str(
                                    expected_signal["source_cell_locator"]
                                ),
                            }
                        )
                        item["requiredness_source"] = str(
                            expected_signal["requiredness_source"]
                        )
                    if (
                        collection_name == "requiredness_oracles"
                        and expected_signal.get("source_binding")
                        == "typed-xhtml-cell"
                        and item.get("decision") == "candidate_tc_required"
                        and item.get("oracle_status")
                        == "ui-calibration-required"
                        and item.get("marker_oracle_found") == "yes"
                    ):
                        repairs.append(
                            {
                                "rule": "clear-unbacked-typed-candidate-marker-claim",
                                "path": (
                                    f"$.{collection_name}[{item_index}]"
                                    ".marker_oracle_found"
                                ),
                                "previous_value_sha256": hashlib.sha256(
                                    b"yes"
                                ).hexdigest(),
                            }
                        )
                        item["marker_oracle_found"] = "no"
    registry = normalized.get("obligations", [])
    if isinstance(registry, list):
        for projection in _oracle_scope_registry_projections(normalized):
            obligation_index = int(projection["obligation_index"])
            obligation = registry[obligation_index]
            if not isinstance(obligation, dict):
                continue
            repairs.append(
                {
                    "rule": "bind-obligation-canonical-oracle-scope-ids",
                    "path": (
                        f"$.obligations[{obligation_index}]"
                        ".scope_obligation_ids"
                    ),
                    "previous_value_sha256": canonical_payload_sha256(
                        {
                            "scope_obligation_ids": projection[
                                "previous_scope_obligation_ids"
                            ]
                        }
                    ),
                }
            )
            obligation["scope_obligation_ids"] = projection[
                "scope_obligation_ids"
            ]
    applicability = normalized.get("applicability", [])
    if isinstance(applicability, list):
        for projection in _applicability_registry_projections(normalized):
            row_index = int(projection["row_index"])
            row = applicability[row_index]
            if not isinstance(row, dict):
                continue
            repairs.append(
                {
                    "rule": "materialize-applicability-from-obligation-registry",
                    "path": f"$.applicability[{row_index}]",
                    "dimension": projection["dimension"],
                    "previous_value_sha256": canonical_payload_sha256(row),
                }
            )
            for field in ("applicable", "linked_atoms", "linked_test_cases"):
                row[field] = projection[field]
    receipt = {
        "version": 1,
        "status": "applied" if repairs else "not-needed",
        "repair_count": len(repairs),
        "repairs": repairs,
        "raw_sha256": canonical_payload_sha256(payload),
        "normalized_sha256": canonical_payload_sha256(normalized),
    }
    return normalized, receipt


def _array(items: Mapping[str, Any]) -> dict[str, Any]:
    return {"type": "array", "items": dict(items)}


def _sized_array(
    items: Mapping[str, Any],
    *,
    exact: int | None = None,
    minimum: int | None = None,
) -> dict[str, Any]:
    schema = _array(items)
    if exact is not None:
        schema.update({"minItems": exact, "maxItems": exact})
    elif minimum is not None:
        schema["minItems"] = minimum
    return schema


def _string_array() -> dict[str, Any]:
    return _array({"type": "string"})


def _object(properties: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(properties),
        "properties": {key: dict(value) for key, value in properties.items()},
    }


def _validate_schema_instance(
    value: Any,
    schema: Mapping[str, Any],
    *,
    path: str = "$",
) -> None:
    """Validate the closed semantic schema without relying on the model runner.

    The bridge is also called by deterministic materialization and library clients, so
    schema closure cannot be a runner-only guarantee.  This intentionally supports the
    small JSON-Schema subset emitted by :func:`semantic_design_output_schema`.
    """

    expected_type = schema.get("type")
    if expected_type == "object":
        if not isinstance(value, Mapping):
            raise SemanticDesignBridgeError(f"{path} must be an object")
        properties = schema.get("properties")
        required = schema.get("required")
        if not isinstance(properties, Mapping) or not isinstance(required, list):
            raise AssertionError("semantic schema object is malformed")
        actual = set(value)
        expected = set(map(str, required))
        unknown = sorted(actual - set(map(str, properties)))
        missing = sorted(expected - actual)
        if missing or unknown:
            raise SemanticDesignBridgeError(
                f"{path} fields mismatch: missing={missing or 'none'}, "
                f"unknown={unknown or 'none'}"
            )
        for key, child_schema in properties.items():
            _validate_schema_instance(
                value[key],
                child_schema,
                path=f"{path}.{key}",
            )
    elif expected_type == "array":
        if not isinstance(value, list):
            raise SemanticDesignBridgeError(f"{path} must be an array")
        item_schema = schema.get("items")
        if not isinstance(item_schema, Mapping):
            raise AssertionError("semantic schema array is malformed")
        for index, item in enumerate(value):
            _validate_schema_instance(item, item_schema, path=f"{path}[{index}]")
    elif expected_type == "string":
        if not isinstance(value, str):
            raise SemanticDesignBridgeError(f"{path} must be a string")
    elif expected_type == "integer":
        if type(value) is not int:
            raise SemanticDesignBridgeError(f"{path} must be an integer")
    elif expected_type == "boolean":
        if type(value) is not bool:
            raise SemanticDesignBridgeError(f"{path} must be a boolean")
    else:
        raise AssertionError(f"unsupported semantic schema type at {path}: {expected_type}")
    if "enum" in schema and value not in schema["enum"]:
        raise SemanticDesignBridgeError(f"{path} is outside the allowed enum")


def _validate_always_visibility_prestate_cardinality(
    assertion: Mapping[str, Any],
    requirement_evidence: Sequence[Mapping[str, Any]],
    source_row: Mapping[str, Any] | None = None,
) -> None:
    """Require two states only when the bounded row names both states."""

    is_always_visible = any(
        "видимость-всегда"
        in normalize_exact_source_text(
            str(binding.get("exact_source_fragment", ""))
        ).casefold()
        for binding in requirement_evidence
        if isinstance(binding, Mapping)
    )
    if not is_always_visible or assertion.get("semantic_disposition") != "testable":
        return
    if source_row is not None:
        source_text = str(source_row.get("bounded_source_text", ""))
        logical_pair = re.search(
            r"логическое\s+да\s*/\s*нет",
            source_text,
            re.IGNORECASE,
        )
        manual_pair = (
            re.search(r"при\s+ручном\s+заполнении", source_text, re.IGNORECASE)
            is not None
            and re.search(
                r"«ввести\s+вручную»\s*=\s*«нет»",
                source_text,
                re.IGNORECASE,
            )
            is not None
        )
        if logical_pair is None and not manual_pair:
            return
    for field in ("condition_clauses", "action_clauses", "oracle_clauses"):
        clauses = assertion.get(field)
        if not isinstance(clauses, list) or len(clauses) < 2:
            raise SemanticDesignBridgeError(
                f"{assertion.get('assertion_id')} Видимость-всегда requires "
                f"two distinct source-backed pre-state chains in {field}"
            )
        if field == "condition_clauses" and len(
            {
                normalize_exact_source_text(str(value)).casefold()
                for value in clauses
            }
        ) < 2:
            raise SemanticDesignBridgeError(
                f"{assertion.get('assertion_id')} Видимость-всегда requires "
                f"two distinct source-backed pre-state chains in {field}"
            )


def _required_necessary_condition_negative_controls(exact_source_fragment: str) -> int:
    """Return the minimum negative controls implied by a necessary-condition rule.

    A literal ``only if`` rule always needs at least one falsifying control. The FT
    also uses ``Видимость: Да, если A И если B`` for conjunctive visibility; each
    independently falsifiable conjunct needs its own negative control. A plain single
    ``Да, если A`` remains a positive implication and is not silently upgraded to iff.
    """

    normalized = normalize_exact_source_text(exact_source_fragment).casefold()
    repeated_if_conjuncts = len(re.findall(r"\bи\s+если\b", normalized))
    composite_visibility = (
        "видимость: да" in normalized
        and "если" in normalized
        and repeated_if_conjuncts > 0
    )
    explicit_only_if = "только если" in normalized or "только при" in normalized
    if composite_visibility:
        return 1 + repeated_if_conjuncts
    if explicit_only_if:
        return 1
    return 0


def _validate_necessary_condition_control_cardinality(
    row_id: str,
    row_assertions: Sequence[Mapping[str, Any]],
) -> None:
    """Reject positive-only coverage of explicit necessary-condition semantics."""

    required_by_code: dict[str, int] = {}
    for assertion in row_assertions:
        evidence = assertion.get("requirement_code_evidence", [])
        if not isinstance(evidence, list):
            continue
        for binding in evidence:
            if not isinstance(binding, Mapping):
                continue
            code = str(binding.get("requirement_code", ""))
            fragment = str(binding.get("exact_source_fragment", ""))
            required = _required_necessary_condition_negative_controls(fragment)
            if code and required:
                required_by_code[code] = max(required_by_code.get(code, 0), required)

    for code, required_negative_count in required_by_code.items():
        code_assertions = [
            assertion
            for assertion in row_assertions
            if assertion.get("semantic_disposition") == "testable"
            and code in set(map(str, assertion.get("requirement_codes", [])))
        ]
        positive_ids = {
            str(assertion.get("assertion_id", ""))
            for assertion in code_assertions
            if assertion.get("polarity") == "positive"
        }
        negative_ids = {
            str(assertion.get("assertion_id", ""))
            for assertion in code_assertions
            if assertion.get("polarity") == "negative"
        }
        if not positive_ids or len(negative_ids) < required_negative_count:
            raise SemanticDesignBridgeError(
                f"{row_id} {code} necessary-condition coverage requires one "
                f"positive assertion and {required_negative_count} distinct negative "
                f"control assertion(s); found positive={len(positive_ids)}, "
                f"negative={len(negative_ids)}"
            )
        branch_assertions = [
            assertion
            for assertion in code_assertions
            if assertion.get("polarity") in {"positive", "negative"}
        ]
        condition_signatures = [
            tuple(
                normalize_exact_source_text(str(clause)).casefold()
                for clause in assertion.get("condition_clauses", [])
            )
            for assertion in branch_assertions
        ]
        if (
            any(not signature for signature in condition_signatures)
            or len(set(condition_signatures)) != len(condition_signatures)
        ):
            raise SemanticDesignBridgeError(
                f"{row_id} {code} necessary-condition branches require distinct "
                "condition states aligned with each positive/negative action"
            )


def _validate_distinct_action_oracle_clauses(assertion: Mapping[str, Any]) -> None:
    """Reject a system result copied verbatim into the executable action."""

    if assertion.get("semantic_disposition") != "testable":
        return
    actions = assertion.get("action_clauses", [])
    oracles = assertion.get("oracle_clauses", [])
    if not isinstance(actions, list) or not isinstance(oracles, list):
        return
    normalized_actions = {
        normalize_exact_source_text(str(value)).casefold()
        for value in actions
        if str(value).strip()
    }
    normalized_oracles = {
        normalize_exact_source_text(str(value)).casefold()
        for value in oracles
        if str(value).strip()
    }
    duplicates = sorted(normalized_actions & normalized_oracles)
    if duplicates:
        raise SemanticDesignBridgeError(
            f"{assertion.get('assertion_id')} action must name a trigger and cannot "
            "duplicate the observable oracle"
        )


def semantic_design_output_schema(
    source_row_ids: Sequence[str],
    *,
    require_ready: bool = False,
    allow_canonical_clarification_binding: bool = True,
    expected_minimum_obligation_count: int | None = None,
    expected_dependency_count: int | None = None,
    expected_dictionary_count: int | None = None,
    expected_negative_signal_count: int | None = None,
    expected_requiredness_signal_count: int | None = None,
) -> dict[str, Any]:
    row_id = {"type": "string", "enum": list(source_row_ids)}
    requirement_binding = _object(
        {
            "requirement_code": {"type": "string"},
            "source_row_id": row_id,
            "provenance_role": {
                "type": "string",
                "enum": ["xhtml-row", "pdf-parity"],
            },
            "exact_source_fragment": {"type": "string"},
            "evidence_source_path": {"type": "string"},
            "evidence_locator": {"type": "string"},
        }
    )
    clause_binding = _object(
        {
            "clause_kind": {
                "type": "string",
                "enum": ["condition", "action", "oracle"],
            },
            "clause_index": {"type": "integer"},
            "source_row_id": row_id,
            "exact_source_fragment": {"type": "string"},
        }
    )
    supporting_binding = _object(
        {
            "source_row_id": row_id,
            "evidence_role": {
                "type": "string",
                "enum": [
                    "subject",
                    "property",
                    "applicability",
                    "constraint",
                    "cross-reference",
                    "definition",
                    "polarity",
                ],
            },
            "exact_source_fragment": {"type": "string"},
        }
    )
    clarification_binding = _object(
        {
            "clarification_id": {"type": "string"},
            "clause_kind": {
                "type": "string",
                "enum": [
                    "condition",
                    "action",
                    "oracle",
                    *(
                        ["canonical"]
                        if allow_canonical_clarification_binding
                        else []
                    ),
                ],
            },
            "clause_index": {"type": "integer"},
            "requirement_codes": _string_array(),
            "exact_answer_sha256": {"type": "string"},
            "binding_scope": {
                "type": "string",
                "enum": ["requirement-code", "source-context"],
            },
            "source_row_ids": _string_array(),
        }
    )
    assertion = _object(
        {
            "assertion_id": {"type": "string", "pattern": r".*\S.*"},
            "canonical_statement": {"type": "string"},
            "polarity": {
                "type": "string",
                "enum": ["positive", "negative", "neutral"],
            },
            "semantic_disposition": {
                "type": "string",
                "enum": ["testable", "ambiguous", "not-applicable"],
            },
            "execution_readiness": {
                "type": "string",
                "enum": ["ready", "dependency-blocked", "not-applicable"],
            },
            "execution_readiness_rationale": {"type": "string"},
            "risk": {
                "type": "string",
                "enum": ["low", "medium", "high", "critical"],
            },
            "condition_clauses": _string_array(),
            "action_clauses": _string_array(),
            "oracle_clauses": _string_array(),
            "requirement_codes": _string_array(),
            "requirement_code_evidence": _array(requirement_binding),
            "clause_evidence": _array(clause_binding),
            "supporting_source_bindings": _array(supporting_binding),
            "clarification_clause_bindings": _array(clarification_binding),
            "atom_id": {"type": "string", "pattern": r".*\S.*"},
            "obligation_ids": _string_array(),
            "disposition_rationale": {
                "type": "string",
                "pattern": r"^.{12,}$" if require_ready else r".*",
            },
            "source_property_id": {"type": "string", "pattern": r".*\S.*"},
            "field_or_block": {"type": "string"},
            "source_reference": {"type": "string"},
        }
    )
    source_design = _object(
        {
            "source_row_id": row_id,
            "boundary_disposition": {
                "type": "string",
                "enum": ["included", "context", "excluded"],
            },
            "requirement_codes": _string_array(),
            "assertions": _sized_array(
                assertion,
                minimum=1 if require_ready else None,
            ),
        }
    )
    obligation = _object(
        {
            "obligation_id": {"type": "string"},
            "package_id": {"type": "string"},
            "linked_atom_id": {"type": "string"},
            "source_property_id": {"type": "string", "pattern": r".*\S.*"},
            "property_type": {"type": "string"},
            "obligation_class": {"type": "string"},
            "required_behavior": {"type": "string"},
            "source_ref": {"type": "string"},
            "planned_tc_id": {"type": "string"},
            "review_notes": {"type": "string"},
            "design_dimension": {
                "type": "string",
                "enum": list(APPLICABILITY_DIMENSIONS),
            },
            "planned_check": {"type": "string"},
            "check_type": {
                "type": "string",
                "enum": [
                    "positive",
                    "negative",
                    "boundary",
                    "dependency",
                    "action-flow",
                    "scenario",
                ],
            },
            "coverage_class": {"type": "string"},
            "input_class": {"type": "string"},
            "single_expected_behavior": {"type": "string"},
            "oracle_source": {"type": "string"},
            "test_data": {"type": "string"},
            "dictionary_refs": _string_array(),
            "dictionary_coverage": {
                "type": "string",
                "enum": [
                    "none_required",
                    "reference-only",
                    "all-leaf-values",
                    "full-hierarchy",
                ],
            },
            "scope_obligation_ids": _string_array(),
        }
    )
    reset_lifecycle_binding = _object(
        {
            "obligation_id": {"type": "string"},
            "binding_kind": {
                "type": "string",
                "enum": ["reset", "readd-after-delete"],
            },
            "initial_condition_index": {"type": "integer"},
            "changed_state_setup": {"type": "string"},
            "pre_action_state_oracle": {"type": "string"},
            "state_relation": {
                "type": "string",
                "enum": ["different-from-captured-initial"],
            },
        }
    )
    dictionary = _object(
        {
            "dictionary_id": {"type": "string"},
            "dictionary_name": {"type": "string"},
            "source_row_ids": _string_array(),
            "source_file": {"type": "string"},
            "source_location": {"type": "string"},
            "extraction_status": {
                "type": "string",
                "enum": ["extracted", "partial", "missing", "ambiguous"],
            },
            "active_values": _string_array(),
            "archived_values": _string_array(),
            "gap_id": {"type": "string"},
            "notes": {"type": "string"},
        }
    )
    negative_oracle = _object(
        {
            "signal_id": {"type": "string"},
            "requirement_codes": _string_array(),
            "scope_obligation_id": {"type": "string"},
            "source_row_id": row_id,
            "source_ref": {"type": "string"},
            "field_or_block": {"type": "string"},
            "restriction_type": {"type": "string"},
            "negative_class": {"type": "string"},
            "source_statement": {"type": "string"},
            "representative_invalid_value": {"type": "string"},
            "observable_oracle_found": {
                "type": "string",
                "enum": ["yes", "no", "partial"],
            },
            "oracle_source": {"type": "string"},
            "oracle_status": {
                "type": "string",
                "enum": list(ORACLE_STATUS_VALUES),
            },
            "decision": {
                "type": "string",
                "enum": [
                    "executable_tc",
                    "candidate_tc_required",
                    "gap_required",
                    "clarification_required",
                    "not_applicable",
                ],
            },
            "planned_tc_or_gap": {"type": "string"},
            "gap_id": {"type": "string"},
            "analyst_question": {"type": "string"},
            "handoff_rule": {"type": "string"},
            "calibration_notes": {"type": "string"},
            "linked_atom_id": {"type": "string"},
            "linked_obligation_id": {"type": "string"},
        }
    )
    requiredness_oracle = _object(
        {
            "signal_id": {"type": "string"},
            "requirement_codes": _string_array(),
            "scope_obligation_id": {"type": "string"},
            "source_row_id": row_id,
            "source_ref": {"type": "string"},
            "field_or_block": {"type": "string"},
            "restriction_type": {"type": "string"},
            "requiredness_source": {"type": "string"},
            "requiredness_class": {"type": "string"},
            "required_when": {"type": "string"},
            "marker_oracle_found": {
                "type": "string",
                "enum": ["yes", "no", "not_applicable"],
            },
            "empty_value_oracle_found": {
                "type": "string",
                "enum": ["yes", "no", "partial"],
            },
            "oracle_source": {"type": "string"},
            "oracle_status": {
                "type": "string",
                "enum": list(ORACLE_STATUS_VALUES),
            },
            "decision": {
                "type": "string",
                "enum": [
                    "executable_tc",
                    "candidate_tc_required",
                    "gap_required",
                    "clarification_required",
                    "not_applicable",
                ],
            },
            "planned_tc_or_gap": {"type": "string"},
            "gap_id": {"type": "string"},
            "analyst_question": {"type": "string"},
            "handoff_rule": {"type": "string"},
            "calibration_notes": {"type": "string"},
            "linked_atom_id": {"type": "string"},
            "linked_obligation_id": {"type": "string"},
        }
    )
    dependency_binding = _object(
        {
            "dependency_id": {"type": "string"},
            "kind": {"type": "string"},
            "name": {"type": "string"},
            "source_row_ids": _string_array(),
            "resolution": {"type": "string"},
            "target_source_row_ids": _string_array(),
            "exact_source_fragments": _string_array(),
            "gap_ids": _string_array(),
            "blocking": {"type": "boolean"},
            "rationale": {"type": "string"},
            "semantic_disposition": {
                "type": "string",
                "enum": ["bound", "gap-bound", "not-applicable"],
            },
            "linked_assertion_ids": _string_array(),
            "linked_atom_ids": _string_array(),
            "linked_obligation_ids": _string_array(),
            "mapping_rationale": {"type": "string"},
        }
    )
    applicability = _object(
        {
            "dimension": {
                "type": "string",
                "enum": list(APPLICABILITY_DIMENSIONS),
            },
            "applicable": {"type": "string", "enum": ["yes", "no"]},
            "source_ref": {"type": "string"},
            "reason": {"type": "string"},
            "linked_atoms": _string_array(),
            "linked_test_cases": _string_array(),
        }
    )
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        **_object(
            {
                "version": {"type": "integer", "enum": [SEMANTIC_DESIGN_VERSION]},
                "contract": {"type": "string", "enum": [SEMANTIC_DESIGN_CONTRACT]},
                "status": {
                    "type": "string",
                    "enum": ["ready"] if require_ready else ["ready", "blocked"],
                },
                "blocking_reason": (
                    {"type": "string", "enum": ["none_required"]}
                    if require_ready
                    else {"type": "string"}
                ),
                "prepared_context_sha256": {"type": "string"},
                "scope_boundary_decision_sha256": {"type": "string"},
                "scope_summary": {"type": "string"},
                "included": _string_array(),
                "excluded": _string_array(),
                "mockup_locators": _string_array(),
                "source_designs": _sized_array(
                    source_design,
                    exact=len(source_row_ids) if require_ready else None,
                ),
                "obligations": _sized_array(
                    obligation,
                    minimum=(
                        expected_minimum_obligation_count if require_ready else None
                    ),
                ),
                "reset_lifecycle_bindings": _array(reset_lifecycle_binding),
                "dependency_bindings": _sized_array(
                    dependency_binding,
                    exact=expected_dependency_count if require_ready else None,
                ),
                "dictionaries": _sized_array(
                    dictionary,
                    exact=expected_dictionary_count if require_ready else None,
                ),
                "negative_oracles": _sized_array(
                    negative_oracle,
                    exact=expected_negative_signal_count if require_ready else None,
                ),
                "requiredness_oracles": _sized_array(
                    requiredness_oracle,
                    exact=expected_requiredness_signal_count if require_ready else None,
                ),
                "applicability": _sized_array(
                    applicability,
                    exact=len(APPLICABILITY_DIMENSIONS) if require_ready else None,
                ),
            }
        ),
    }


def semantic_design_allows_canonical_transport_binding(
    clarifications: Sequence[Mapping[str, Any]],
) -> bool:
    """Return whether a model transport schema needs the canonical slot.

    Requirement-code clarifications can bind only executable clauses. The
    canonical slot exists solely for typed source-context clarifications; when
    a bounded model shard has none, removing the enum value prevents an invalid
    cross-field combination before semantic validation.
    """

    return any(
        str(item.get("binding_scope", "requirement-code")) == "source-context"
        for item in clarifications
        if isinstance(item, Mapping)
    )


def _markdown_cell(value: str) -> str:
    result = value.strip()
    if len(result) >= 2 and result.startswith("`") and result.endswith("`"):
        result = result[1:-1].strip()
    return result


def _clarification_rows(text: str, *, source_path: str) -> list[dict[str, str]]:
    required = set(CLARIFICATION_COLUMNS)
    lines = text.splitlines()
    rows: list[dict[str, str]] = []
    for index in range(len(lines) - 1):
        header = lines[index].strip()
        separator = lines[index + 1].strip()
        if not (
            header.startswith("|")
            and separator.startswith("|")
            and "---" in separator
        ):
            continue
        columns = [_markdown_cell(item) for item in header.strip("|").split("|")]
        if not required.issubset(columns):
            continue
        cursor = index + 2
        while cursor < len(lines) and lines[cursor].strip().startswith("|"):
            cells = [
                _markdown_cell(item)
                for item in lines[cursor].strip().strip("|").split("|")
            ]
            if len(cells) != len(columns):
                raise SemanticDesignBridgeError(
                    f"invalid clarification row {source_path}:{cursor + 1}"
                )
            rows.append(dict(zip(columns, cells)))
            cursor += 1
        break
    if not rows:
        raise SemanticDesignBridgeError(
            f"approved clarification source has no canonical rows: {source_path}"
        )
    return rows


def _resolve_repo_file(repo_root: Path, raw_path: str) -> Path:
    root = repo_root.resolve()
    candidate = (root / Path(raw_path)).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise SemanticDesignBridgeError(
            f"registered path escapes repository: {raw_path}"
        ) from exc
    if not candidate.is_file():
        raise SemanticDesignBridgeError(f"registered file is missing: {raw_path}")
    return candidate


def _validate_dependency_alias_provenance(
    context: Mapping[str, Any],
    *,
    clarification_ids: set[str],
) -> None:
    aliases = context.get("dependency_aliases", {})
    if not isinstance(aliases, Mapping):
        raise SemanticDesignBridgeError("context.dependency_aliases must be an object")
    for alias, target in aliases.items():
        if (
            not isinstance(alias, str)
            or not alias.strip()
            or not isinstance(target, str)
            or not target.strip()
        ):
            raise SemanticDesignBridgeError(
                "context.dependency_aliases must map non-empty strings"
            )

    provenance = context.get("dependency_alias_provenance", {})
    if not isinstance(provenance, Mapping):
        raise SemanticDesignBridgeError(
            "context.dependency_alias_provenance must be an object"
        )
    if any(
        not isinstance(alias, str)
        or not alias.strip()
        or not isinstance(clarification_id, str)
        or not clarification_id.strip()
        for alias, clarification_id in provenance.items()
    ):
        raise SemanticDesignBridgeError(
            "context.dependency_alias_provenance must map non-empty aliases "
            "to clarification ids"
        )
    if set(provenance) != set(aliases):
        raise SemanticDesignBridgeError(
            "context.dependency_alias_provenance keys must exactly match "
            "context.dependency_aliases"
        )
    unknown_ids = sorted(set(map(str, provenance.values())) - clarification_ids)
    if unknown_ids:
        raise SemanticDesignBridgeError(
            "context.dependency_alias_provenance references unknown approved "
            "clarification ids: " + ", ".join(unknown_ids)
        )


def _normalize_approved_clarifications(
    context: Mapping[str, Any],
    records: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """Validate typed clarification records against the prepared context."""

    scope_slug = str(context.get("scope_slug", ""))
    rows = context.get("source_rows", [])
    if not isinstance(rows, list) or any(not isinstance(item, Mapping) for item in rows):
        raise SemanticDesignBridgeError("context.source_rows must be an object array")
    known_rows = {str(item.get("source_row_id", "")) for item in rows}
    known_codes: set[str] = set()
    for row in rows:
        codes = row.get("requirement_codes_hint", [])
        if not isinstance(codes, list):
            raise SemanticDesignBridgeError(
                "context requirement_codes_hint values must be arrays"
            )
        known_codes.update(map(str, codes))
    normalized: list[dict[str, Any]] = []
    for payload in records:
        try:
            record = ApprovedClarification.from_dict(payload)
        except (SourceAssertionContractError, KeyError, TypeError, ValueError) as exc:
            raise SemanticDesignBridgeError(
                f"invalid approved clarification: {exc}"
            ) from exc
        if record.scope_slug != scope_slug:
            raise SemanticDesignBridgeError(
                f"{record.clarification_id} scope_slug does not match prepared context"
            )
        if set(record.requirement_codes) - known_codes:
            raise SemanticDesignBridgeError(
                f"{record.clarification_id} references requirement codes outside context"
            )
        if set(record.source_row_ids) - known_rows:
            raise SemanticDesignBridgeError(
                f"{record.clarification_id} references source rows outside context"
            )
        normalized.append(record.to_dict())
    ids = [item["clarification_id"] for item in normalized]
    if len(ids) != len(set(ids)):
        raise SemanticDesignBridgeError("approved clarification ids must be unique")
    _validate_dependency_alias_provenance(
        context,
        clarification_ids=set(map(str, ids)),
    )
    return tuple(normalized)


def load_approved_clarifications(
    repo_root: Path,
    context: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    explicit = context.get("approved_clarifications")
    if explicit is not None:
        if not isinstance(explicit, list) or any(
            not isinstance(item, Mapping) for item in explicit
        ):
            raise SemanticDesignBridgeError(
                "context.approved_clarifications must be an object array"
            )
        normalized = _normalize_approved_clarifications(context, explicit)
        registered = {
            str(item.get("path")): item
            for item in context.get("sources", [])
            if isinstance(item, Mapping)
            and item.get("manifest_binding") == "approved-clarification"
        }
        for record in normalized:
            relative = str(record["evidence_source_path"])
            if relative not in registered:
                raise SemanticDesignBridgeError(
                    f"{record['clarification_id']} evidence source is not registered "
                    "as approved-clarification"
                )
            path = _resolve_repo_file(repo_root, relative)
            actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual_digest != record["evidence_source_sha256"]:
                raise SemanticDesignBridgeError(
                    f"{record['clarification_id']} evidence source digest mismatch"
                )
        return normalized

    result: list[dict[str, Any]] = []
    sources = context.get("sources", [])
    if not isinstance(sources, list):
        raise SemanticDesignBridgeError("context.sources must be an array")
    scope_slug = str(context.get("scope_slug", ""))
    for entry in sources:
        if not isinstance(entry, Mapping):
            raise SemanticDesignBridgeError("context.sources entries must be objects")
        if entry.get("manifest_binding") != "approved-clarification":
            continue
        relative = str(entry.get("path", ""))
        path = _resolve_repo_file(repo_root, relative)
        source_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows = _clarification_rows(
            path.read_text(encoding="utf-8"),
            source_path=relative,
        )
        for row in rows:
            if row["scope_slug"] != scope_slug or row["response_status"] != "answered":
                continue
            authority = row["authority"]
            if APPROVED_AUTHORITY_TYPES.get(authority) != row["response_type"]:
                continue
            codes = tuple(
                item.strip()
                for item in row["requirement_codes"].split(";")
                if item.strip() and item.strip() != "-"
            )
            if not codes:
                raise SemanticDesignBridgeError(
                    "source-context clarification requires explicit structured "
                    "context.approved_clarifications"
                )
            answer = row["user_response"]
            result.append(
                {
                    "clarification_id": row["clarification_id"],
                    "gap_id": row["gap_id"],
                    "scope_slug": row["scope_slug"],
                    "requirement_codes": list(codes),
                    "authority": authority,
                    "response_status": row["response_status"],
                    "response_type": row["response_type"],
                    "answered_at": row["updated_at"],
                    "exact_answer": answer,
                    "exact_answer_sha256": hashlib.sha256(
                        answer.encode("utf-8")
                    ).hexdigest(),
                    "evidence_source_path": relative.replace("\\", "/"),
                    "evidence_source_sha256": source_digest,
                    "binding_scope": "requirement-code",
                    "source_row_ids": [],
                }
            )
    return _normalize_approved_clarifications(context, result)


def validate_bridge_boundary(
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
) -> None:
    try:
        validate_boundary_decision_v2(context, boundary)
    except BoundedScopeBoundaryError as exc:
        raise SemanticDesignBridgeError(str(exc)) from exc

    if boundary["status"] != "ready" or boundary["blocking_reason"] != "none_required":
        raise SemanticDesignBridgeError(
            "semantic-design bridge requires a ready scope boundary decision"
        )
    if any(
        item.get("blocking") is True
        or item.get("downstream_handling") == "block-writer"
        for item in boundary["gaps"]
        if isinstance(item, Mapping)
    ):
        raise SemanticDesignBridgeError(
            "release semantic-design bridge cannot consume blocking scope gaps"
        )
    if any(
        item["blocking"] is True or item["resolution"] == "missing"
        for item in boundary["dependencies"]
    ):
        raise SemanticDesignBridgeError(
            "semantic-design bridge requires only resolved non-blocking dependencies"
        )
    package_id = context.get("package_id")
    if not isinstance(package_id, str) or re.fullmatch(r"WP-[0-9]{2,}", package_id) is None:
        raise SemanticDesignBridgeError(
            "semantic-design bridge requires one canonical context.package_id"
        )


_FIELD_PROPERTY_TYPES = ("requiredness", "editability")
_FIELD_PROPERTY_NORMALIZED_VALUES = {
    "requiredness": {"required", "optional"},
    "editability": {"editable", "read-only"},
}
_FIELD_PROPERTY_FIELDS = {
    "property_id",
    "table_id",
    "physical_column_index",
    "normalized_value",
    "source_value",
    "source_cell_locator",
    "header_source_row_id",
    "header_value",
    "header_cell_locator",
    "interpretation_source",
    "interpretation_source_fragment",
}


def _typed_field_property_registry(
    context: Mapping[str, Any],
    *,
    eligible_row_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    rows = context.get("source_rows")
    if not isinstance(rows, list):
        raise SemanticDesignBridgeError("context.source_rows must be an array")
    rows_by_id = {
        str(row.get("source_row_id", "")): row
        for row in rows
        if isinstance(row, Mapping)
    }
    if len(rows_by_id) != len(rows):
        raise SemanticDesignBridgeError(
            "context.source_rows must contain unique object source_row_id values"
        )
    registered_sources = {
        str(item.get("path"))
        for item in context.get("sources", [])
        if isinstance(item, Mapping)
    }
    declarations = context.get("source_table_column_semantics", [])
    if not isinstance(declarations, list):
        raise SemanticDesignBridgeError(
            "context.source_table_column_semantics must be an array"
        )
    declared: dict[tuple[str, str], dict[str, Any]] = {}
    for declaration_index, declaration in enumerate(declarations):
        label = f"source_table_column_semantics[{declaration_index}]"
        if not isinstance(declaration, Mapping):
            raise SemanticDesignBridgeError(f"{label} must be an object")
        if set(declaration) != {
            "table_id",
            "header_source_row_id",
            "target_source_row_ids",
            "columns",
        }:
            raise SemanticDesignBridgeError(f"{label} fields are invalid")
        table_id = declaration.get("table_id")
        header_row_id = declaration.get("header_source_row_id")
        target_row_ids = declaration.get("target_source_row_ids")
        columns = declaration.get("columns")
        if (
            not isinstance(table_id, str)
            or not table_id.strip()
            or not isinstance(header_row_id, str)
            or header_row_id not in rows_by_id
            or not isinstance(target_row_ids, list)
            or not target_row_ids
            or len(target_row_ids) != len(set(map(str, target_row_ids)))
            or any(str(row_id) not in rows_by_id for row_id in target_row_ids)
            or not isinstance(columns, list)
            or not columns
        ):
            raise SemanticDesignBridgeError(f"{label} row contract is invalid")
        for column_index, column in enumerate(columns):
            column_label = f"{label}.columns[{column_index}]"
            if not isinstance(column, Mapping) or set(column) != {
                "property",
                "physical_column_index",
                "expected_header",
                "value_mapping",
                "interpretation_source",
                "interpretation_source_fragment",
            }:
                raise SemanticDesignBridgeError(f"{column_label} fields are invalid")
            property_type = str(column.get("property", ""))
            physical_index = column.get("physical_column_index")
            mapping = column.get("value_mapping")
            if (
                property_type not in _FIELD_PROPERTY_TYPES
                or not isinstance(physical_index, int)
                or isinstance(physical_index, bool)
                or physical_index < 1
                or not isinstance(mapping, Mapping)
                or not mapping
            ):
                raise SemanticDesignBridgeError(f"{column_label} mapping is invalid")
            for row_id_value in target_row_ids:
                row_id = str(row_id_value)
                key = (row_id, property_type)
                if key in declared:
                    raise SemanticDesignBridgeError(
                        f"duplicate declared field property {row_id}/{property_type}"
                    )
                declared[key] = {
                    "table_id": table_id,
                    "header_source_row_id": header_row_id,
                    "physical_column_index": physical_index,
                    "header_value": column.get("expected_header"),
                    "value_mapping": dict(mapping),
                    "interpretation_source": column.get("interpretation_source"),
                    "interpretation_source_fragment": column.get(
                        "interpretation_source_fragment"
                    ),
                }

    registry: list[dict[str, Any]] = []
    actual_pairs: set[tuple[str, str]] = set()
    property_ids: set[str] = set()
    for row in rows:
        assert isinstance(row, Mapping)
        row_id = str(row["source_row_id"])
        properties = row.get("field_properties")
        if properties is None:
            if "physical_table_cells" in row:
                raise SemanticDesignBridgeError(
                    f"{row_id} has physical_table_cells without field properties"
                )
            continue
        if not isinstance(properties, Mapping) or not properties:
            raise SemanticDesignBridgeError(
                f"{row_id}.field_properties must be a non-empty object"
            )
        unknown_types = sorted(set(properties) - set(_FIELD_PROPERTY_TYPES))
        if unknown_types:
            raise SemanticDesignBridgeError(
                f"{row_id}.field_properties has unsupported properties: {unknown_types}"
            )
        physical_cells = row.get("physical_table_cells")
        if not isinstance(physical_cells, list) or not physical_cells:
            raise SemanticDesignBridgeError(
                f"{row_id}.physical_table_cells must be a non-empty array"
            )
        source_locator = row.get("source_locator")
        if not isinstance(source_locator, str) or not source_locator:
            raise SemanticDesignBridgeError(f"{row_id}.source_locator is required")
        cells_by_index: dict[int, Mapping[str, Any]] = {}
        for expected_index, cell in enumerate(physical_cells, start=1):
            if not isinstance(cell, Mapping) or set(cell) != {
                "physical_column_index",
                "source_cell_locator",
                "element_kind",
                "bounded_source_text",
            }:
                raise SemanticDesignBridgeError(
                    f"{row_id}.physical_table_cells[{expected_index - 1}] is invalid"
                )
            if (
                cell.get("physical_column_index") != expected_index
                or cell.get("source_cell_locator")
                != source_locator + f"/*[{expected_index}]"
                or cell.get("element_kind") not in {"td", "th"}
                or not isinstance(cell.get("bounded_source_text"), str)
            ):
                raise SemanticDesignBridgeError(
                    f"{row_id}.physical_table_cells[{expected_index - 1}] binding drifted"
                )
            cells_by_index[expected_index] = cell
        for property_type in _FIELD_PROPERTY_TYPES:
            if property_type not in properties:
                continue
            metadata = properties[property_type]
            label = f"{row_id}.field_properties.{property_type}"
            if not isinstance(metadata, Mapping) or set(metadata) != _FIELD_PROPERTY_FIELDS:
                raise SemanticDesignBridgeError(f"{label} fields are invalid")
            key = (row_id, property_type)
            actual_pairs.add(key)
            expected = declared.get(key)
            if expected is None:
                raise SemanticDesignBridgeError(
                    f"{label} has no source table semantics declaration"
                )
            property_id = metadata.get("property_id")
            normalized_value = metadata.get("normalized_value")
            expected_property_id = (
                f"FP-{row_id}-{property_type.upper()}-"
                f"{str(normalized_value).upper()}"
            )
            if (
                property_id != expected_property_id
                or property_id in property_ids
            ):
                raise SemanticDesignBridgeError(f"{label}.property_id is invalid")
            property_ids.add(str(property_id))
            for metadata_key in (
                "table_id",
                "header_source_row_id",
                "physical_column_index",
                "header_value",
                "interpretation_source",
                "interpretation_source_fragment",
            ):
                if metadata.get(metadata_key) != expected[metadata_key]:
                    raise SemanticDesignBridgeError(
                        f"{label}.{metadata_key} drifted from its declaration"
                    )
            source_value = metadata.get("source_value")
            if (
                not isinstance(source_value, str)
                or source_value not in expected["value_mapping"]
                or normalized_value
                != expected["value_mapping"][source_value]
                or normalized_value
                not in _FIELD_PROPERTY_NORMALIZED_VALUES[property_type]
            ):
                raise SemanticDesignBridgeError(f"{label} normalized value is invalid")
            source_cell_locator = metadata.get("source_cell_locator")
            header_row = rows_by_id[str(expected["header_source_row_id"])]
            header_cell_locator = metadata.get("header_cell_locator")
            expected_suffix = f"/*[{expected['physical_column_index']}]"
            if (
                not isinstance(source_locator, str)
                or source_cell_locator != source_locator + expected_suffix
                or header_cell_locator
                != str(header_row.get("source_locator", "")) + expected_suffix
            ):
                raise SemanticDesignBridgeError(f"{label} cell locator binding is invalid")
            property_cell = cells_by_index[int(expected["physical_column_index"])]
            if (
                property_cell.get("source_cell_locator") != source_cell_locator
                or property_cell.get("bounded_source_text") != source_value
            ):
                raise SemanticDesignBridgeError(
                    f"{label} does not match physical_table_cells evidence"
                )
            if metadata.get("interpretation_source") not in registered_sources:
                raise SemanticDesignBridgeError(
                    f"{label}.interpretation_source is not registered"
                )
            for text_key in (
                "source_value",
                "header_value",
                "interpretation_source_fragment",
            ):
                if not isinstance(metadata.get(text_key), str) or not str(
                    metadata[text_key]
                ).strip():
                    raise SemanticDesignBridgeError(f"{label}.{text_key} is empty")
            if eligible_row_ids is None or row_id in eligible_row_ids:
                registry.append(
                    {
                        "source_property_id": property_id,
                        "source_row_id": row_id,
                        "property_type": property_type,
                        "normalized_value": normalized_value,
                        "source_value": source_value,
                        "source_cell_locator": source_cell_locator,
                        "header_source_row_id": str(
                            metadata["header_source_row_id"]
                        ),
                        "header_value": metadata["header_value"],
                        "header_cell_locator": header_cell_locator,
                        "interpretation_source": metadata["interpretation_source"],
                        "interpretation_source_fragment": metadata[
                            "interpretation_source_fragment"
                        ],
                    }
                )
    if actual_pairs != set(declared):
        missing = sorted(set(declared) - actual_pairs)
        unexpected = sorted(actual_pairs - set(declared))
        raise SemanticDesignBridgeError(
            "prepared field-property coverage does not match declarations: "
            f"missing={missing or 'none'}, unexpected={unexpected or 'none'}"
        )
    return registry


def validate_semantic_input_preflight(
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
    clarifications: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Fail before model invocation when deterministic semantic inputs are incomplete."""

    validate_bridge_boundary(context, boundary)
    eligible_rows = _eligible_semantic_rows(context, boundary)
    eligible_row_ids = {
        str(row.get("source_row_id", ""))
        for row in eligible_rows
    }
    properties = _typed_field_property_registry(
        context,
        eligible_row_ids=eligible_row_ids,
    )
    counts = {
        "required": 0,
        "optional": 0,
        "editable": 0,
        "read-only": 0,
    }
    for item in properties:
        counts[str(item["normalized_value"])] += 1
    code_registry = {
        str(item["source_row_id"]): list(map(str, item["requirement_codes"]))
        for item in boundary["source_decisions"]
    }
    signals = _source_signal_registry(eligible_rows, code_registry)
    typed_requiredness_count = sum(
        item["property_type"] == "requiredness" for item in properties
    )
    typed_signal_count = sum(
        item.get("source_binding") == "typed-xhtml-cell"
        for item in signals["requiredness"]
    )
    if typed_requiredness_count != typed_signal_count:
        raise SemanticDesignBridgeError(
            "typed requiredness property/signal counts do not match"
        )
    rows_by_id = {
        str(row["source_row_id"]): row
        for row in context["source_rows"]
        if isinstance(row, Mapping)
    }
    requiredness_candidate_defaults: list[dict[str, Any]] = []
    for signal in signals["requiredness"]:
        if signal.get("source_binding") != "typed-xhtml-cell":
            continue
        signal_id = str(signal["signal_id"])
        scope_obligation_id = "SO-" + signal_id.removeprefix("SIG-")
        row_id = str(signal["source_row_id"])
        restriction_type = str(signal["restriction_type"])
        binary_default_value = (
            str(signal.get("default_value", ""))
            if signal.get("value_semantics") == "binary-logical-default"
            else ""
        )
        if binary_default_value:
            field = str(signal["field_or_block"])
            optional = restriction_type == "optionality"
            requiredness_label = "Необязательный" if optional else "Условно обязательный"
            fallback_action = (
                f"Не изменять значение по умолчанию «{binary_default_value}» "
                f"логического элемента «{field}»."
            )
            fallback_test_data = (
                f"Логическое значение по умолчанию «{binary_default_value}»"
            )
            expected_behavior = (
                f"{requiredness_label} логический элемент остаётся в заданном значении "
                f"по умолчанию «{binary_default_value}» без обязательной активации; "
                "точный UI-триггер и итоговый отклик требуют калибровки."
            )
            fallback_canonical_statement = (
                f"{requiredness_label} логический элемент «{field}» не требует отдельной "
                f"активации и остаётся в значении по умолчанию "
                f"«{binary_default_value}»; точный итоговый UI-отклик калибруется."
            )
            fallback_disposition_rationale = (
                "Типизированная ячейка О сохраняет requiredness/optionality, а источник "
                "задаёт бинарный control и его значение по умолчанию; "
                "третье пустое состояние не выводится."
            )
            analyst_question = (
                "Какое действие подтверждает форму и какой точный UI-отклик "
                f"отображается, если логический элемент «{field}» не изменять и "
                f"оставить в значении по умолчанию «{binary_default_value}»?"
            )
            fallback_input_mode = "binary-logical-default"
            fallback_required_when = (
                "no-user-selection-required"
                if optional
                else str(signal.get("requiredness_source", ""))
            )
        elif (
            restriction_type == "optionality"
            and signal.get("control_semantics") == "action-control"
        ):
            field = str(signal["field_or_block"])
            fallback_action = f"Не нажимать элемент «{field}»."
            fallback_test_data = f"Не нажимать элемент «{field}»"
            expected_behavior = (
                f"Взаимодействие с элементом «{field}» не является обязательным; "
                "точная точка подтверждения формы требует UI-калибровки."
            )
            fallback_canonical_statement = (
                f"Необязательность action control «{field}» означает отсутствие "
                "обязательного нажатия, а не пустое значение поля."
            )
            fallback_disposition_rationale = (
                "Типизированная ячейка О относится к action control, поэтому "
                "optionality проверяется отсутствием обязательного взаимодействия."
            )
            analyst_question = (
                f"В какой точке подтверждения формы проверяется, что элемент «{field}» "
                "не требуется нажимать?"
            )
            fallback_input_mode = "no-action-control"
            fallback_required_when = "never_required_by_typed_cell"
        else:
            fallback_action = f"Оставить поле из {row_id} пустым."
            fallback_test_data = "Пустое значение"
            expected_behavior = (
                "Пустое обязательное значение не подтверждается как валидное; "
                "точный UI-триггер и отклик требуют калибровки."
                if restriction_type == "requiredness"
                else
                "Пустое необязательное значение допускается; точный UI-триггер "
                "подтверждения требует калибровки."
            )
            fallback_canonical_statement = expected_behavior
            fallback_disposition_rationale = (
                "Типизированная requiredness/optionality ячейка сохраняется как "
                "калибровочный candidate без выдумывания UI-реакции."
            )
            analyst_question = (
                "Какое действие запускает проверку и какой точный UI-отклик "
                f"отображается для пустого поля из {row_id}?"
            )
            fallback_input_mode = "empty-value"
            fallback_required_when = (
                "never_required_by_typed_cell"
                if restriction_type == "optionality"
                else str(signal.get("requiredness_source", ""))
            )
        requiredness_candidate_defaults.append(
            {
                "signal_id": signal_id,
                "scope_obligation_id": scope_obligation_id,
                "source_row_id": row_id,
                "source_property_id": str(signal["source_property_id"]),
                "restriction_type": restriction_type,
                "fallback_input_mode": fallback_input_mode,
                "fallback_action": fallback_action,
                "fallback_test_data": fallback_test_data,
                "fallback_expected_behavior": expected_behavior,
                "fallback_canonical_statement": fallback_canonical_statement,
                "fallback_disposition_rationale": fallback_disposition_rationale,
                "fallback_required_when": fallback_required_when,
                "source_backed_default_value": binary_default_value,
                "oracle_source": "not_found",
                "oracle_status": "ui-calibration-required",
                "marker_oracle_found": "no",
                "empty_value_oracle_found": "no",
                "decision": "candidate_tc_required",
                "planned_tc_or_gap": f"candidate:{scope_obligation_id}",
                "gap_id": "none_required",
                "analyst_question": analyst_question,
                "handoff_rule": (
                    "Сохранить candidate TC и уточнить фактический UI-триггер и "
                    "отклик без блокировки остальных проверок."
                ),
                "calibration_notes": (
                    "candidate-ui-calibration: точный UI-триггер и реакция не "
                    "выдумываются."
                ),
            }
        )
    dictionary_registry: list[dict[str, Any]] = []
    external_dictionary_names = set(
        external_dynamic_dictionary_bindings(context)
    )
    for dictionary_index, reference in enumerate(
        [
            item
            for item in _dictionary_references(eligible_rows)
            if normalize_entity(str(item["dictionary_name"]))
            not in external_dictionary_names
        ],
        start=1,
    ):
        dictionary_name = str(reference["dictionary_name"])
        declared_values = _declared_dictionary_values(context, dictionary_name)
        source_kind = "prepared-inventory"
        if declared_values is None:
            inline_values = _closed_inline_dictionary_values(
                name=dictionary_name,
                row_ids=list(map(str, reference["source_row_ids"])),
                rows_by_id=rows_by_id,
            )
            if inline_values is None:
                raise SemanticDesignBridgeError(
                    f"semantic input lacks a complete dictionary value set for "
                    f"{dictionary_name}"
                )
            active_values, archived_values = inline_values, []
            source_kind = "bounded-xhtml-cells"
        else:
            active_values, archived_values = declared_values
        dictionary_registry.append(
            {
                "dictionary_id": f"DICT-{dictionary_index:03d}",
                "dictionary_name": dictionary_name,
                "source_row_ids": list(map(str, reference["source_row_ids"])),
                "source_kind": source_kind,
                "active_values": active_values,
                "archived_values": archived_values,
            }
        )
    state_change_source_row_ids = [
        str(row["source_row_id"])
        for row in eligible_rows
        if _row_requires_state_change(row)
    ]
    readd_lifecycle_clarification_ids = [
        str(item.get("clarification_id", ""))
        for item in clarifications
        if isinstance(item, Mapping)
        and _text_requires_readd_lifecycle(item.get("exact_answer", ""))
    ]
    semantic_slot_registry: list[dict[str, Any]] = []

    def add_slot(
        slot_id: str,
        slot_kind: str,
        source_row_ids: Sequence[Any],
        binding_id: str,
    ) -> None:
        semantic_slot_registry.append(
            {
                "slot_id": slot_id,
                "slot_kind": slot_kind,
                "source_row_ids": list(map(str, source_row_ids)),
                "binding_id": binding_id,
            }
        )

    for row in eligible_rows:
        row_id = str(row["source_row_id"])
        add_slot(f"SLOT-ROW-{row_id}", "source-row", [row_id], row_id)
    decision_by_row = {
        str(item.get("source_row_id", "")): item
        for item in boundary.get("source_decisions", [])
        if isinstance(item, Mapping)
    }
    for row in eligible_rows:
        row_id = str(row["source_row_id"])
        decision = decision_by_row.get(row_id, {})
        for requirement_code in map(str, decision.get("requirement_codes", [])):
            code_token = re.sub(
                r"[^A-ZА-ЯЁ0-9]+",
                "-",
                requirement_code.upper(),
            ).strip("-")
            add_slot(
                f"SLOT-REQ-{row_id}-{code_token}",
                "requirement-code",
                [row_id],
                f"{row_id}:{requirement_code}",
            )
    for item in properties:
        property_id = str(item["source_property_id"])
        add_slot(
            f"SLOT-{property_id}",
            "field-property",
            [item["source_row_id"]],
            property_id,
        )
    for signal_kind in ("negative", "requiredness"):
        for item in signals[signal_kind]:
            signal_id = str(item["signal_id"])
            add_slot(
                f"SLOT-{signal_id}",
                f"{signal_kind}-signal",
                [item["source_row_id"]],
                signal_id,
            )
    for item in dictionary_registry:
        dictionary_id = str(item["dictionary_id"])
        add_slot(
            f"SLOT-{dictionary_id}",
            "dictionary",
            item["source_row_ids"],
            dictionary_id,
        )
    for row_id in state_change_source_row_ids:
        add_slot(
            f"SLOT-STATE-{row_id}",
            "state-change",
            [row_id],
            row_id,
        )
    clarification_by_id = {
        str(item.get("clarification_id", "")): item
        for item in clarifications
        if isinstance(item, Mapping)
    }
    for clarification_id in readd_lifecycle_clarification_ids:
        clarification = clarification_by_id[clarification_id]
        lifecycle_source_rows = list(
            map(str, clarification.get("source_row_ids", []))
        )
        if not lifecycle_source_rows:
            lifecycle_codes = set(
                map(str, clarification.get("requirement_codes", []))
            )
            lifecycle_source_rows = [
                row_id
                for row_id, row_codes in code_registry.items()
                if lifecycle_codes & set(row_codes)
            ]
        add_slot(
            f"SLOT-LIFECYCLE-{clarification_id}",
            "readd-lifecycle",
            lifecycle_source_rows,
            clarification_id,
        )
    semantic_slot_counts = {
        slot_kind: sum(
            item["slot_kind"] == slot_kind for item in semantic_slot_registry
        )
        for slot_kind in (
            "source-row",
            "requirement-code",
            "field-property",
            "negative-signal",
            "requiredness-signal",
            "dictionary",
            "state-change",
            "readd-lifecycle",
        )
    }
    result = {
        "version": 1,
        "prepared_context_sha256": prepared_context_sha256(context),
        "scope_boundary_decision_sha256": canonical_payload_sha256(boundary),
        "eligible_source_row_count": len(eligible_rows),
        "field_property_count": len(properties),
        "field_property_counts": counts,
        "negative_signal_count": len(signals["negative"]),
        "requiredness_signal_count": len(signals["requiredness"]),
        "field_property_registry": properties,
        "dictionary_registry": dictionary_registry,
        "requiredness_candidate_defaults": requiredness_candidate_defaults,
        "semantic_slot_count": len(semantic_slot_registry),
        "semantic_slot_counts": semantic_slot_counts,
        "semantic_slot_registry": semantic_slot_registry,
        "state_change_source_row_ids": state_change_source_row_ids,
        "readd_lifecycle_clarification_ids": readd_lifecycle_clarification_ids,
    }
    result["semantic_input_sha256"] = canonical_payload_sha256(result)
    return result


def _fully_gapped_observation_rows(
    boundary: Mapping[str, Any],
) -> set[str]:
    """Return included rows whose complete coded behavior lacks an observer.

    A row is eligible only when one explicit non-blocking observation-interface
    gap carries every requirement code owned by that row in its literal evidence.
    This prevents a gap for one clause from turning unrelated visible behavior in
    the same row into N/A semantics.
    """

    codes_by_row = {
        str(item.get("source_row_id", "")): tuple(
            str(code) for code in item.get("requirement_codes", [])
        )
        for item in boundary.get("source_decisions", [])
        if isinstance(item, Mapping) and item.get("disposition") == "included"
    }
    result: set[str] = set()
    for gap in boundary.get("gaps", []):
        if (
            not isinstance(gap, Mapping)
            or gap.get("gap_type") != "missing-observation-interface"
            or gap.get("blocking") is not False
            or gap.get("downstream_handling") != "carry-to-source-model"
        ):
            continue
        literal_evidence = " ".join(
            str(fragment) for fragment in gap.get("exact_source_fragments", [])
        ).casefold()
        for row_id in map(str, gap.get("source_row_ids", [])):
            codes = codes_by_row.get(row_id, ())
            if codes and all(code.casefold() in literal_evidence for code in codes):
                result.add(row_id)
    return result


def _semantic_output_cardinality(
    preflight: Mapping[str, Any],
    boundary: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a compact, source-derived minimum-output checklist per row."""

    property_ids_by_row: dict[str, list[str]] = {}
    for item in preflight.get("field_property_registry", []):
        if not isinstance(item, Mapping):
            continue
        property_ids_by_row.setdefault(str(item.get("source_row_id", "")), []).append(
            str(item.get("source_property_id", ""))
        )
    negative_ids_by_row: dict[str, list[str]] = {}
    for item in preflight.get("semantic_slot_registry", []):
        if not isinstance(item, Mapping) or item.get("slot_kind") != "negative-signal":
            continue
        for row_id in map(str, item.get("source_row_ids", [])):
            negative_ids_by_row.setdefault(row_id, []).append(
                str(item.get("binding_id", ""))
            )

    fully_gapped_rows = _fully_gapped_observation_rows(boundary)
    scope_excluded_dependencies_by_row: dict[str, list[str]] = {}
    for dependency in boundary.get("dependencies", []):
        if not isinstance(dependency, Mapping) or dependency.get("resolution") != "scope-excluded":
            continue
        dependency_id = str(dependency.get("dependency_id", ""))
        for row_id in map(str, dependency.get("source_row_ids", [])):
            scope_excluded_dependencies_by_row.setdefault(row_id, []).append(dependency_id)
    rows: list[dict[str, Any]] = []
    for decision in boundary.get("source_decisions", []):
        if not isinstance(decision, Mapping):
            continue
        row_id = str(decision.get("source_row_id", ""))
        disposition = str(decision.get("disposition", ""))
        property_ids = property_ids_by_row.get(row_id, [])
        negative_ids = negative_ids_by_row.get(row_id, [])
        requirement_codes = list(map(str, decision.get("requirement_codes", [])))
        if disposition == "included" and row_id in fully_gapped_rows:
            minimum_testable = 0
            required_na = 1
        elif disposition == "included":
            behavior_minimum = max(
                1 if requirement_codes or not property_ids else 0,
                len(negative_ids),
            )
            minimum_testable = len(property_ids) + behavior_minimum
            required_na = len(scope_excluded_dependencies_by_row.get(row_id, ()))
        else:
            minimum_testable = 0
            required_na = 1
        rows.append(
            {
                "source_row_id": row_id,
                "boundary_disposition": disposition,
                "requirement_codes": requirement_codes,
                "required_source_property_ids": property_ids,
                "negative_signal_ids": negative_ids,
                "required_scope_excluded_dependency_ids": list(
                    scope_excluded_dependencies_by_row.get(row_id, ())
                ),
                "minimum_testable_assertion_count": minimum_testable,
                "required_not_applicable_assertion_count": required_na,
            }
        )
    return {
        "version": 1,
        "rows": rows,
        "minimum_testable_assertion_count": sum(
            int(item["minimum_testable_assertion_count"]) for item in rows
        ),
        "required_source_property_assertion_count": sum(
            len(item["required_source_property_ids"]) for item in rows
        ),
    }


def semantic_design_minimum_obligation_count(
    preflight: Mapping[str, Any],
    boundary: Mapping[str, Any],
) -> int:
    """Return the source-derived minimum executable obligation count."""

    return int(
        _semantic_output_cardinality(preflight, boundary)[
            "minimum_testable_assertion_count"
        ]
    )


def _validate_semantic_input_preflight_receipt(
    preflight: Mapping[str, Any],
    *,
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
) -> dict[str, Any]:
    result = dict(preflight)
    digest = result.pop("semantic_input_sha256", None)
    if digest != canonical_payload_sha256(result):
        raise SemanticDesignBridgeError("semantic-input preflight digest mismatch")
    if result.get("prepared_context_sha256") != prepared_context_sha256(context):
        raise SemanticDesignBridgeError("semantic-input preflight context drifted")
    if result.get("scope_boundary_decision_sha256") != canonical_payload_sha256(
        boundary
    ):
        raise SemanticDesignBridgeError("semantic-input preflight boundary drifted")
    result["semantic_input_sha256"] = digest
    return result


def semantic_design_prompt(
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
    clarifications: Sequence[Mapping[str, Any]],
    *,
    semantic_input_preflight: Mapping[str, Any] | None = None,
) -> str:
    validate_bridge_boundary(context, boundary)
    preflight = (
        _validate_semantic_input_preflight_receipt(
            semantic_input_preflight,
            context=context,
            boundary=boundary,
        )
        if semantic_input_preflight is not None
        else validate_semantic_input_preflight(
            context,
            boundary,
            clarifications,
        )
    )
    projection = dict(context)
    projection["authoritative_scope_boundary_v2"] = dict(boundary)
    projection["approved_clarifications"] = [dict(item) for item in clarifications]
    projection["semantic_clarification_binding_registry"] = [
        {
            "clarification_id": str(item.get("clarification_id", "")),
            "binding_scope": str(
                item.get("binding_scope", "requirement-code")
            ),
            "requirement_codes": list(
                map(str, item.get("requirement_codes", []))
            ),
            "source_row_ids": list(map(str, item.get("source_row_ids", []))),
            "allowed_clause_kinds": (
                ["condition", "action", "oracle"]
                if str(item.get("binding_scope", "requirement-code"))
                == "requirement-code"
                else ["condition", "action", "oracle", "canonical"]
            ),
        }
        for item in clarifications
        if isinstance(item, Mapping)
    ]
    projection["prepared_context_sha256"] = prepared_context_sha256(context)
    projection["scope_boundary_decision_sha256"] = canonical_payload_sha256(boundary)
    prompt_rows = _eligible_semantic_rows(context, boundary)
    code_registry = {
        str(item["source_row_id"]): list(map(str, item["requirement_codes"]))
        for item in boundary["source_decisions"]
    }
    projection["semantic_source_signal_registry"] = _source_signal_registry(
        prompt_rows,
        code_registry,
    )
    projection["semantic_field_property_registry"] = preflight[
        "field_property_registry"
    ]
    projection["semantic_dictionary_registry"] = preflight[
        "dictionary_registry"
    ]
    projection["semantic_requiredness_candidate_defaults"] = preflight[
        "requiredness_candidate_defaults"
    ]
    projection["semantic_slot_registry"] = preflight[
        "semantic_slot_registry"
    ]
    projection["semantic_output_cardinality"] = _semantic_output_cardinality(
        preflight,
        boundary,
    )
    projection["semantic_input_preflight"] = {
        key: value
        for key, value in preflight.items()
        if key not in {
            "field_property_registry",
            "dictionary_registry",
            "requiredness_candidate_defaults",
            "semantic_slot_registry",
        }
    }
    return """You are the semantic-design author for one already fixed FT scope.
Do not call tools, shell, web, MCP, or read workspace files. Return only strict JSON.

Authoritative boundary contract:
- The v2 boundary decision is immutable. Do not redo source discovery, scope selection,
  dependency resolution, gaps, dispositions, requirement-code routing, or mockup selection.
- The global scope summary and include/exclude arrays are routing metadata, not clause evidence.
  Author executable semantics only for the projected context.source_rows and their exact
  authoritative source decisions. If another requirement is named only in global metadata but
  its owning source row is absent, it belongs to another shard and must not be emitted here.
- Copy both supplied SHA-256 values, scope summary, include/exclude arrays, mockup locators,
  source row order, boundary dispositions and per-row requirement-code registry exactly.
- Split every independently testable property into a separate assertion. Assertion code sets
  may be subsets, but their union per source row must equal the exact row registry.
- Treat semantic_slot_registry as the compact source-derived completeness checklist. Satisfy
  each slot through its existing row/property/signal/dictionary/lifecycle contract; compatible
  slots may share one atomic chain only where the typed validators already require that binding.
- Treat semantic_output_cardinality as a hard pre-submit checklist. For every included row,
  emit at least minimum_testable_assertion_count testable assertions and make every listed
  required_source_property_id appear exactly once. One generic assertion per source row is an
  invalid compressed result. The minimum is not permission to merge independent BSR behaviors.
- Included rows normally need at least one testable assertion. When
  semantic_output_cardinality explicitly requires one N/A assertion and zero testable assertions,
  the whole coded row is covered by an authoritative non-blocking
  missing-observation-interface gap: preserve its requirement evidence in one N/A ASSERT/ATOM,
  create no OBL/TC, and do not turn it into executable behavior. Context/excluded rows also need
  explicit N/A assertions and no executable obligations. Never silently drop a row.

Quality contract:
- DOCX remains semantic source of truth; XHTML bounded rows provide exact text/locators;
  PDF is parity only; mockups refine visible locators only.
- Every testable assertion has one observable condition/action/oracle chain, exact literal
  evidence for every clause/code, one ATOM, and at least one independently executable OBL/TC.
- Every assertion, including N/A, uses a non-empty unique assertion_id and atom_id. Set
  execution_readiness_rationale to the literal none_required for both ready and N/A assertions;
  put explanations only in disposition_rationale, which must be substantive. Every condition,
  action and oracle clause has exactly one clause_evidence entry with an exact literal fragment.
  N/A assertions keep all clauses and obligation_ids empty.
- supporting_source_bindings is cross-row evidence only: never repeat the enclosing
  source_design.source_row_id there. The primary row is implicit. For an N/A assertion
  with no genuine cross-row support, return an empty supporting_source_bindings array.
- A non-excluded included row may be explicit cross-row support. A context-row support additionally
  requires the owner/context rows to share an authoritative boundary dependency, the same typed
  source-context clarification, or the exact source_property_id/header_source_row_id relation
  already declared by semantic_field_property_registry. No other table-header inference is allowed.
- Bind every requirement code to every independent atomic assertion governed by it; the union
  per source row must still equal the exact registry. When one coded statement contains multiple
  independently testable properties, repeating that code across their atomic sibling assertions
  is required and is not duplicate semantic coverage. For provenance_role=xhtml-row,
  exact_source_fragment must contain the literal bounded code token and both PDF evidence
  fields must equal none_required. For provenance_role=pdf-parity, use only the exact
  main_ft_pdf registered as structural-visual-parity, copy that code's exact context.parity
  page:N locator, and set exact_source_fragment=none_required. All fields remain strings;
  never emit JSON null for this evidence contract.
- Keep positive, negative, boundary, dependency and action-flow checks atomic. Do not merge
  independent results into one planned TC.
- A `только если` / `только при` / only-if rule states a necessary condition, not merely a
  positive example. Emit one positive ASSERT/ATOM/OBL for the satisfied condition and a
  separate negative control ASSERT/ATOM/OBL for each independently falsifiable conjunct. For
  `effect only if A and B`, prove A+B, not-A+B and A+not-B; each control oracle states that the
  effect is absent. Do not claim the full only-if rule from the positive state alone.
- Treat an explicit conjunctive visibility phrase such as `Видимость: Да, если A И если B`
  the same way: emit the positive branch plus one negative control for A and one for B. A plain
  single `Видимость: Да, если A` is not automatically upgraded to an iff rule.
- Every negative control's condition_clauses must describe its actual falsified pre-state and
  agree with its action. Never copy the unchanged positive A+B conditions into not-A+B or
  A+not-B; all branch condition states must be distinct.
- Turn source predicates into executable UI projections. For conditional visibility, the action
  sets the named trigger and the oracle observes the named field. For a positive input-format
  class, use one concrete representative value, enter it in the visible field and verify that
  the same value is present/accepted. For a negative format class, use one concrete invalid
  value and keep the exact unknown reaction as a candidate-ui-calibration oracle. For optionality,
  make field availability a precondition, leave it empty and use the full fallback oracle, not
  the raw cell token. For editability, enter one concrete allowed value and verify the same value
  is displayed. Never use requirement prose, table metadata (`Поле ввода`, `Текст`) or a raw
  `Да`/`Нет` property cell as the action or observable oracle.
- Action and oracle clauses must never be textually identical: the action names the user-visible
  trigger or input, while the oracle names the resulting observable product state. Copying a
  system result such as `address is decomposed` into the action is not an executable step.
- When the bounded source row of an explicit `Видимость-всегда` / always-visible
  rule itself names two states (for example logical `Да/Нет` or automatic/manual), emit one
  atomic assertion that proves the same visibility result in both states, with separate
  condition, action and oracle clauses. When that row names no state dimension, use one
  direct open-and-observe visibility check; never invent or borrow an unrelated toggle merely
  to manufacture a two-state proof.
- A statement about an internal model, persistence or integration field does not authorize
  inventing an API, database query or generic "observable artifact" action. Use only an
  observation interface registered in the bounded context. If none exists, do not return a
  ready executable assertion for that effect; preserve the missing interface as a coverage
  gap. When the same row also contains visible behavior, split it: the visible assertion owns
  the row's requirement code and executable OBL/TC, while a separate code-less N/A ASSERT/ATOM
  owns the exact gapped internal clause and has no OBL. Bind the affected dependency as
  gap-bound to that N/A chain. Only a row whose complete coded behavior is covered by the gap
  may be N/A-only.
- Copy every authoritative dependency into dependency_bindings in exact boundary order. A
  bound dependency maps a complete known testable ASSERT/ATOM/OBL chain. A resolved dependency
  whose entire projected source effect is covered by an authoritative non-blocking
  missing-observation-interface gap uses gap-bound and maps the N/A ASSERT/ATOM with no OBL.
  Every linked
  assertion must carry literal evidence containing an authoritative dependency fragment,
  and the linked assertion set must cover every fragment; for gap-bound, the authoritative gap
  evidence provides that literal coverage. Only a dependency resolved as scope-excluded may be
  explicit not-applicable, with no executable links.
- For a dependency sourced by context_relation_required rows, the linked assertion set must
  cover every authoritative target_source_row_id. The context row supplies evidence; each
  target row remains the owner (or explicit non-excluded support) of its executable assertion.
- Every obligation uses the one exact prepared context.package_id; do not invent work packages.
- Every obligation is owned by exactly one assertion whose atom_id equals linked_atom_id. Never
  add aggregate, registry-summary, padding, traceability-only or otherwise unowned obligations.
  Before returning, verify that the obligation_id set in the obligations registry equals the
  union of all assertion.obligation_ids exactly; no referenced OBL may be omitted.
- Requiredness is not covered by entering a valid value. Optionality is a distinct positive
  signal and needs its own ASSERT/ATOM/OBL/TC. For ordinary value fields it proves empty-value
  acceptance. For either requiredness or optionality on a source-typed binary logical
  switch/checkbox with a source-backed default, use the projected binary-default fallback:
  preserve that default and never invent a third empty state for a Да/Нет control. Do not classify
  a generic success message as negative feedback. When one explicit source sentence says that
  multiple named values must be entered, each named target in semantic_source_signal_registry
  requires its own negative or calibration ASSERT/ATOM/OBL/TC chain; a different validation
  branch in the same sentence and a positive fixture containing all values do not prove those
  independently required targets. The sentence that the values "must be entered" proves
  requiredness but is not itself an observed empty-value UI oracle. Unless the projected signal
  sentence also names a marker, message, save rejection or another visible reaction, return a
  ui-calibration candidate even if the surrounding source row contains feedback for a different
  field.
- Cover every semantic_field_property_registry entry with one distinct testable ASSERT/ATOM/OBL
  chain on its exact source row. Copy source_property_id exactly to the assertion and obligation,
  and copy property_type exactly to the obligation. The immutable source_property_id includes
  the expected normalized value (required/optional/editable/read-only); the chain's behavior,
  action and oracle must implement that value. Typed XHTML cells are structural table
  evidence and intentionally have no invented BSR assignment. Requiredness entries also bind
  their matching requiredness inventory signal; editability entries remain independent checks.
- A named verified fixture must project its exact request literal and exact expected suggestion
  into the owning condition/action/oracle chain. Vague phrases such as "corresponding value" or
  "value from the fixture" are not reproducible. A typed field-property chain must not own a
  requirement code whose literal statement defines a different property; emit a separate chain
  for that coded behavior (for example BSR visibility versus typed O-cell requiredness).
- An authoritative open missing-source-definition GAP bound to its own ambiguous/N/A assertion
  is a hard negative boundary. Do not add its undefined fragments to an executable sibling merely
  because both originate in one coded source row.
- Every typed-property assertion must preserve the exact source_value from its matching
  semantic_field_property_registry entry in at least one same-row clause_evidence literal.
  When the cell token alone does not describe the visible action/oracle, use one contiguous
  literal row span containing both that exact source_value and the clause's existing source
  anchor. Do not move primary-row typed evidence into supporting_source_bindings.
- For assertions that do not implement a semantic_field_property_registry entry, set
  source_property_id to the literal none_required on both the assertion and every owned
  obligation. Never return an empty source_property_id or invent a property identifier.
- semantic_requiredness_candidate_defaults are mandatory non-blocking fallbacks for typed XHTML
  requiredness/optionality when the source does not name the validation trigger or exact UI
  reaction. In that case copy the matching fallback identity and candidate fields, use its
  fallback_action as the source-derived user action, bind fallback_test_data to the typed cell,
  and copy marker_oracle_found/empty_value_oracle_found exactly; a typed requiredness cell is
  not proof that an executable UI marker or empty-value reaction was observed,
  and emit exactly one candidate ASSERT/ATOM/OBL/TC chain for that property. Do not require a
  second positive companion for the same typed property and do not return status=blocked merely
  because the trigger or reaction needs UI calibration. The fallback preserves the requirement
  while refusing to invent the missing reaction.
- Emit one negative inventory row per invalid input class. Unknown exact UI feedback remains a
  ui-calibration candidate, not an invented executable rejection oracle.
- For every non-typed negative ui-calibration candidate, preserve a separate positive
  allowed-class ASSERT/ATOM/OBL/TC for the same source_property_id. The positive companion must
  exercise a value inside the source-backed allowed class; it is not replaced by an editability,
  visibility, requiredness or dependency check that merely happens to use a valid-looking value.
  Keep source_property_id=none_required on both chains when the restriction comes from ordinary
  row text rather than semantic_field_property_registry.
- Copy the typed semantic_source_signal_registry exactly into negative/requiredness inventory
  identities. Keep each signal_id, row, requirement-code set and restriction_type distinct;
  source_statement must be one literal source segment containing that signal's literal_anchor.
  For a typed XHTML requiredness signal, copy requiredness_source from the registry exactly;
  it is the literal source-cell value, not the source_binding label "typed-xhtml-cell".
  Map every signal to its own compatible OBL/TC; never reuse one OBL for independent signals.
  executable_tc requires one exact backed oracle_status: source-backed,
  common-standard-backed, analyst-confirmed, or observed-ui-backed. Do not append decision
  labels such as "-executable" to these closed status values. When the restriction is
  source-backed but its exact UI reaction is unknown, retain a canonical calibration candidate:
  decision=candidate_tc_required, oracle_status=ui-calibration-required,
  planned_tc_or_gap=candidate:<scope_obligation_id>, a concrete invalid/empty input, a specific
  analyst question, a substantive handoff rule, and calibration_notes containing the explicit
  candidate-ui-calibration marker. Never invent the missing reaction oracle.
  For each OBL, scope_obligation_ids is exactly its linked SO-* scope_obligation_id in registry
  order; never put a SIG-* signal_id in that field.
- Copy every semantic_dictionary_registry dictionary_id, name, source-row set, active value and
  archived value exactly; do not invent or renumber ids and do not re-parse a flattened row
  across physical XHTML cell boundaries. Link
  dictionary obligations by
  DICT id only inside an ASSERT/ATOM/OBL evidence chain that reaches every dictionary source
  row, and use exhaustive coverage only when the source/context proves a complete list.
- An authoritative boundary dependency with resolution=external-dynamic is intentionally absent
  from semantic_dictionary_registry: it is a changing external directory, not a closed static
  inventory. Bind its ASSERT/ATOM/OBL chain through dependency_bindings, keep dictionary_refs=[],
  dictionary_coverage=none_required, and use only the supplied HTTPS/query contract as test-data
  context. The executable action must still use the owning product field through its normal UI
  path; a direct vendor API request alone does not test that product field. Use a value obtained
  from the registered dynamic contract as test-data setup, enter/search it in the owning UI
  field, select the matching offered value, and assert that the same value is offered and retained
  by the product. Never invent or enumerate a supposedly complete value set, and never claim
  backend provenance that the registered UI path cannot observe.
- Generic obligations never carry reset/lifecycle state fields. For every clear/reset or
  re-add-after-delete obligation, emit exactly one separate reset_lifecycle_bindings entry.
  Bind it by obligation_id, use initial_condition_index as the zero-based index of the owner's
  initial visible condition clause, and set state_relation=different-from-captured-initial.
  A non-reset/non-re-add obligation must not appear in reset_lifecycle_bindings.
- For clear/reset/delete-to-empty behavior, build a reset obligation with a condition clause
  capturing the initial visible state, changed-state setup and a pre-action inequality oracle.
  Every assertion carrying literal clear/reset evidence needs its own guarded reset obligation;
  supporting context-row reset evidence remains bound through that assertion's exact evidence.
  Re-add-after-delete is a separate repeatable-block-lifecycle obligation only when source or
  approved clarification explicitly states a filled prestate, deletion, subsequent new-block
  addition, and empty fields. Bind that clarification to the lifecycle condition/action/oracle;
  an unrelated clarification binding is not coverage.
- Approved clarification may affect ready semantics only through exact typed clause bindings.
  Each requirement-code binding may name only codes owned by its enclosing assertion; distribute
  the clarification's codes across assertions instead of copying the full list into each binding.
  Across those bindings, the union must copy the clarification's complete
  requirement_codes/source_row_ids exactly. CLR-EMP-002 owns a separate lifecycle
  ASSERT/ATOM/OBL/TC (not the reset chain)
  and binds its filled prestate, delete/re-add action and empty-new-block oracle clauses.
- Never copy an approved clarification answer into condition/action/oracle text or
  clause_evidence unless those exact bytes are also literal source-row text. When a
  requirement-code clarification excludes only an internal sibling effect and the boundary
  marks that dependency scope-excluded, keep the remaining visible `если ..., то ...` effect
  testable: use its literal system-effect phrase as both action and observable oracle, bind the
  clarification to that existing oracle clause. On the same included row create one separate
  code-less, clause-free and obligation-free N/A ASSERT/ATOM for each scope-excluded dependency:
  preserve the dependency's literal internal fragment in canonical_statement, set
  field_or_block to the exact dependency name, and explain the scope exclusion in
  disposition_rationale. Keep the row's requirement code only on the visible testable sibling.
  The visible testable sibling's field_or_block must name only the observable effect and must
  not mention the scope-excluded dependency.
  Map the excluded dependency as not-applicable with no executable links.
- Copy semantic_clarification_binding_registry exactly. A requirement-code clarification binds
  only an existing condition, action or oracle clause of a testable assertion. For that scope,
  clause_kind=canonical is forbidden even when clause_index=0; never use canonical as a generic
  binding to canonical_statement. The canonical slot is reserved exclusively for a typed
  source-context clarification on a not-applicable, clause-free, obligation-free assertion.
- A source-context clarification that makes rows explicitly out-of-project owns N/A semantics,
  not executable behavior. Keep every named boundary row excluded/not-applicable, create no
  obligation, and attach exactly one canonical clarification_clause_binding to that row's N/A
  assertion with only its own source_row_id. Never transfer the excluded rule to target fields.
- Produce exactly the 13 declared applicability dimensions. A yes row links known ATOM/TC ids
  whose obligation design_dimension equals that row; traceability is proved structurally by the
  compiled chain itself. A no row has empty links.
- If evidence lacks even the stable source anchor, input class or condition needed for an
  executable check or canonical calibration candidate, return status=blocked with a
  substantive reason and all eight semantic collections empty: source_designs,
  obligations, reset_lifecycle_bindings, dependency_bindings, dictionaries, negative_oracles,
  requiredness_oracles and applicability.
- A contradiction between two anchored FT statements is not missing input and must not mutate
  the immutable boundary gaps. Preserve both source anchors through the relevant assertion
  evidence and emit a canonical calibration candidate with gap_id=none_required for the exact
  disputed boundary/input class. The analyst question and handoff rule carry the unresolved
  choice. Do not choose one statement, invent precedence, or block the remaining scope. For
  BSR 281/BSR 282 specifically, equality at X is the disputed candidate; unambiguous below-X
  and above-X behavior remains independently designable.
  Do not manufacture or publish a runnable partial design.

Before returning JSON, compare the output to semantic_output_cardinality row by row. If any
minimum count, required N/A count or required_source_property_id is missing, continue authoring
instead of returning the compressed draft.

Inline immutable prepared projection:
""" + json.dumps(projection, ensure_ascii=False, indent=2)


def _literal_fragment(
    rows_by_id: Mapping[str, Mapping[str, Any]],
    row_id: str,
    fragment: Any,
    *,
    label: str,
) -> None:
    if row_id not in rows_by_id:
        raise SemanticDesignBridgeError(f"{label} references unknown row {row_id}")
    if not isinstance(fragment, str) or not fragment.strip():
        raise SemanticDesignBridgeError(f"{label} requires a literal fragment")
    if fragment not in str(rows_by_id[row_id].get("bounded_source_text", "")):
        raise SemanticDesignBridgeError(
            f"{label} fragment is absent from bounded row {row_id}"
        )


def _unique_nonempty(values: Sequence[Any], *, label: str) -> list[str]:
    result = [str(item) for item in values]
    if any(not item.strip() for item in result) or len(result) != len(set(result)):
        raise SemanticDesignBridgeError(f"{label} must be non-empty and unique")
    return result


def _state_change_class(obligation: Mapping[str, Any]) -> bool:
    values = " ".join(
        str(obligation.get(key, ""))
        for key in ("property_type", "obligation_class", "coverage_class")
    ).casefold()
    tokens = {item for item in re.split(r"[^a-zа-яё0-9]+", values) if item}
    return bool(tokens & {"reset", "clear", "cleanup", "очистка", "сброс"})


def _lifecycle_readd_class(obligation: Mapping[str, Any]) -> bool:
    """Return whether an obligation is the dedicated re-add-after-delete check."""

    values = " ".join(
        str(obligation.get(key, ""))
        for key in ("property_type", "obligation_class", "coverage_class")
    ).casefold()
    normalized = re.sub(r"[^a-zа-яё0-9]+", "-", values).strip("-")
    return any(
        marker in normalized
        for marker in (
            "repeatable-block-lifecycle",
            "readd-after-delete",
            "re-add-after-delete",
            "readd-after-delete-reset-or-gap",
            "повторное-добавление-после-удаления",
        )
    )


def _text_has_filled_prestate(value: Any) -> bool:
    return re.search(
        r"(?:(?<!не)(?<!не )заполн|непуст|не\s+пуст|"
        r"(?<!un)(?<!not )filled|non[- ]?empty|not\s+empty)",
        str(value).casefold(),
    ) is not None


def _text_has_delete_then_readd(value: Any) -> bool:
    text = str(value).casefold()
    delete = re.search(r"(?:удал|delete|remov)", text)
    add = re.search(
        r"(?:добав|\bre[- ]?add(?:ed|ing)?\b|\badd(?:ed|ing)?\b)",
        text,
    )
    return delete is not None and add is not None and delete.start() < add.start()


def _text_has_new_instance(value: Any) -> bool:
    return re.search(
        r"(?:(?<![а-яё])нов(?:ый|ого|ому|ым|ом|ая|ой|ую|ое|ые|ых|ыми)"
        r"(?![а-яё])|\bnew\b)",
        str(value).casefold(),
    ) is not None


def _text_has_empty_result(value: Any) -> bool:
    return re.search(
        r"(?:(?<!не)(?<!не )пуст|(?<!non)(?<!not )empty|"
        r"(?<!non)(?<!not )blank)",
        str(value).casefold(),
    ) is not None


def _text_requires_readd_lifecycle(value: Any) -> bool:
    """Recognize only a complete filled -> delete -> re-add -> empty rule."""

    return (
        _text_has_filled_prestate(value)
        and _text_has_delete_then_readd(value)
        and _text_has_new_instance(value)
        and _text_has_empty_result(value)
    )


def _assertion_has_readd_lifecycle(assertion: Mapping[str, Any]) -> bool:
    conditions = assertion.get("condition_clauses", [])
    actions = assertion.get("action_clauses", [])
    oracles = assertion.get("oracle_clauses", [])
    return (
        isinstance(conditions, list)
        and any(_text_has_filled_prestate(item) for item in conditions)
        and isinstance(actions, list)
        and _text_has_delete_then_readd(" ".join(map(str, actions)))
        and _text_has_new_instance(" ".join(map(str, actions)))
        and isinstance(oracles, list)
        and any(_text_has_empty_result(item) for item in oracles)
    )


def _row_requires_state_change(row: Mapping[str, Any]) -> bool:
    return _text_requires_state_change(row.get("bounded_source_text", ""))


def _text_requires_state_change(value: Any) -> bool:
    text = str(value).casefold()
    return bool(
        re.search(
            r"(?:очищ|очист|сброс|"
            r"(?<![a-z0-9])reset(?![a-z0-9])|"
            r"(?<![a-z0-9])clear(?![a-z0-9]))",
            text,
        )
    )


def _assertion_state_change_evidence_rows(
    assertion: Mapping[str, Any],
) -> set[str]:
    """Return rows whose exact assertion evidence explicitly states a state change."""

    result: set[str] = set()
    for collection_name in ("clause_evidence", "supporting_source_bindings"):
        bindings = assertion.get(collection_name, [])
        if not isinstance(bindings, list):
            continue
        for binding in bindings:
            if not isinstance(binding, Mapping) or not _text_requires_state_change(
                binding.get("exact_source_fragment", "")
            ):
                continue
            row_id = str(binding.get("source_row_id", ""))
            if row_id:
                result.add(row_id)
    return result


def _assertion_evidence_rows(
    assertion: Mapping[str, Any],
    *,
    primary_row_id: str,
) -> set[str]:
    """Return the explicit primary/supporting row chain for an assertion."""

    result = {primary_row_id}
    supporting = assertion.get("supporting_source_bindings", [])
    if isinstance(supporting, list):
        result.update(
            str(binding.get("source_row_id", ""))
            for binding in supporting
            if isinstance(binding, Mapping) and binding.get("source_row_id")
        )
    return result


def _assertion_literal_evidence(
    assertion: Mapping[str, Any],
) -> list[tuple[str, str]]:
    """Return typed literal evidence pairs without treating free text as provenance."""

    result: list[tuple[str, str]] = []
    for collection_name in (
        "requirement_code_evidence",
        "clause_evidence",
        "supporting_source_bindings",
    ):
        bindings = assertion.get(collection_name, [])
        if not isinstance(bindings, list):
            continue
        for binding in bindings:
            if not isinstance(binding, Mapping):
                continue
            fragment = binding.get("exact_source_fragment")
            row_id = str(binding.get("source_row_id", ""))
            if (
                isinstance(fragment, str)
                and fragment.strip()
                and fragment != "none_required"
                and row_id
            ):
                result.append((row_id, fragment))
    return result


def _assertion_lifecycle_evidence_rows(
    assertion: Mapping[str, Any],
) -> set[str]:
    fragments_by_row: dict[str, list[str]] = {}
    for row_id, fragment in _assertion_literal_evidence(assertion):
        fragments_by_row.setdefault(row_id, []).append(fragment)
    return {
        row_id
        for row_id, fragments in fragments_by_row.items()
        if _text_requires_readd_lifecycle(" ".join(fragments))
    }


def _dictionary_names(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    result: list[str] = []
    for row in rows:
        text = str(row.get("bounded_source_text", ""))
        names = re.findall(r"справочник[^«]{0,12}«([^\u00bb]+)»", text, flags=re.IGNORECASE)
        names.extend(
            match.strip()
            for match in re.findall(
                r"по\s+справочнику\s+([^:.;]+)\s*:",
                text,
                flags=re.IGNORECASE,
            )
        )
        for name in names:
            normalized = name.strip()
            if normalized and normalized.casefold() not in {
                item.casefold() for item in result
            }:
                result.append(normalized)
    return result


def _dictionary_references(
    rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    by_name: dict[str, dict[str, Any]] = {}
    for row in rows:
        row_id = str(row.get("source_row_id", ""))
        for name in _dictionary_names([row]):
            key = name.casefold()
            entry = by_name.get(key)
            if entry is None:
                entry = {"dictionary_name": name, "source_row_ids": []}
                by_name[key] = entry
                references.append(entry)
            if row_id not in entry["source_row_ids"]:
                entry["source_row_ids"].append(row_id)
    return references


def _declared_dictionary_values(
    context: Mapping[str, Any],
    name: str,
) -> tuple[list[str], list[str]] | None:
    raw = context.get("dictionary_inventory")
    if isinstance(raw, Mapping):
        for candidate, values in raw.items():
            if str(candidate).casefold() != name.casefold():
                continue
            if not isinstance(values, list) or any(
                not isinstance(value, str) or not value.strip() for value in values
            ):
                raise SemanticDesignBridgeError(
                    f"prepared dictionary inventory for {name} must be a non-empty string array"
                )
            if not values or len(values) != len(set(values)):
                raise SemanticDesignBridgeError(
                    f"prepared dictionary inventory for {name} must be non-empty and unique"
                )
            return list(values), []
    elif isinstance(raw, list):
        for item in raw:
            if not isinstance(item, Mapping):
                continue
            candidate = item.get("name") or item.get("dictionary_name")
            if not isinstance(candidate, str) or candidate.casefold() != name.casefold():
                continue
            active = item.get("active_values", item.get("values"))
            archived = item.get("archived_values", [])
            if (
                not isinstance(active, list)
                or not active
                or not isinstance(archived, list)
                or any(
                    not isinstance(value, str) or not value.strip()
                    for value in [*active, *archived]
                )
                or len(active) != len(set(active))
                or len(archived) != len(set(archived))
                or set(active) & set(archived)
            ):
                raise SemanticDesignBridgeError(
                    f"prepared dictionary inventory for {name} is invalid"
                )
            return list(active), list(archived)
    return None


def _closed_inline_dictionary_values(
    *,
    name: str,
    row_ids: Sequence[str],
    rows_by_id: Mapping[str, Mapping[str, Any]],
) -> list[str] | None:
    escaped = re.escape(name)
    patterns = (
        rf"справочник(?:а|у|ом|е)?\s+[«\"]{escaped}[»\"]\s*:\s*([^.!?\n]+)",
        rf"(?:по\s+)?справочнику\s+{escaped}\s*:\s*([^.!?\n]+)",
    )
    result: list[str] = []
    found = False
    for row_id in row_ids:
        row = rows_by_id[row_id]
        physical_cells = row.get("physical_table_cells")
        if isinstance(physical_cells, list) and physical_cells:
            bounded_segments = [
                str(cell.get("bounded_source_text", ""))
                for cell in physical_cells
                if isinstance(cell, Mapping)
            ]
        else:
            bounded_segments = [str(row.get("bounded_source_text", ""))]
        for text in bounded_segments:
            for pattern in patterns:
                match = re.search(pattern, text, flags=re.IGNORECASE)
                if match is None:
                    continue
                found = True
                captured = match.group(1)
                if re.search(r"(?:^|;)\s*[-–—]\s*", captured):
                    raw_values = re.split(
                        r"(?:^|;)\s*[-–—]\s*|\s+[-–—]\s+",
                        captured,
                    )
                else:
                    raw_values = re.split(r"[,;]", captured)
                values = [
                    item.strip(" \t\r\n-–—'\"«»;")
                    for item in raw_values
                ]
                values = [item for item in values if item]
                if len(values) < 2:
                    return None
                for value in values:
                    if value not in result:
                        result.append(value)
    return result if found and len(result) >= 2 else None


_NEGATIVE_SIGNAL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "format",
        re.compile(
            r"(?:формат(?:е|а)?|маск(?:а|е|и)|шаблон(?:у|а)?|"
            r"допустим(?:ые|ых)\s+символ(?:ы|ов)|регулярн(?:ое|ого)\s+выражени(?:е|я))",
            re.IGNORECASE,
        ),
    ),
    (
        "numeric",
        re.compile(
            r"(?:числов(?:ое|ого|ым)|"
            r"только\s+числов(?:ые|ых)\s+символ(?:ы|ов)|"
            r"цел(?:ое|ого)\s+числ(?:о|а)|"
            r"только\s+цифр(?:ы|ами)?|десятичн(?:ое|ого))",
            re.IGNORECASE,
        ),
    ),
    (
        "lower-bound",
        re.compile(
            r"(?:не\s+менее(?:\s+[-+]?\d+(?:[.,]\d+)?)?|"
            r"миним(?:ум|альное|альная|альный)(?:\s+значени[ея])?"
            r"(?:\s+[-+]?\d+(?:[.,]\d+)?)?|"
            r"(?:значение\s+)?от\s+[-+]?\d+(?:[.,]\d+)?)",
            re.IGNORECASE,
        ),
    ),
    (
        "upper-bound",
        re.compile(
            r"(?:не\s+более(?:\s+[-+]?\d+(?:[.,]\d+)?)?|"
            r"максим(?:ум|альное|альная|альный)(?:\s+значени[ея])?"
            r"(?:\s+[-+]?\d+(?:[.,]\d+)?)?|"
            r"до\s+[-+]?\d+(?:[.,]\d+)?|"
            r"при\s+попытке\s+ввести\s+сумм(?:у|а)\s+более\s+"
            r"(?:[-+]?\d+(?:[.,]\d+)?|[A-ZА-ЯЁ]))",
            re.IGNORECASE,
        ),
    ),
    (
        "feedback",
        re.compile(
            r"(?:ошибк(?:а|и|у|ой|е|ах)(?:\s+[^,.;]{0,80})?|"
            r"(?:сообщени(?:е|я)|уведомлени(?:е|я)|"
            r"подсказк(?:а|и|у|е))[^,.;]{0,80}"
            r"(?:ошиб|некоррект|недопуст|невалид|"
            r"обязательн|не\s+заполн|отклон|запрещ))",
            re.IGNORECASE,
        ),
    ),
)
_DEFAULT_TEMPLATE_STATE_PATTERN = re.compile(
    r"по\s+умолчанию\s+"
    r"(?:(?:в\s+поле\s+)?(?:стоит|"
    r"установлен(?:а|о|ы)?|задан(?:а|о|ы)?|указан(?:а|о|ы)?|"
    r"отображается|показывается|подставляется|содержится))\s+"
    r"шаблон(?:у|а|ом|е)?",
    re.IGNORECASE,
)
_BLOCK_HEADING_SOURCE_PATTERN = re.compile(
    r"^Блок\s+«(?P<title>[^»]+)»$",
    re.IGNORECASE,
)
_DOUBLE_WRAPPED_BLOCK_ORACLE_PATTERN = re.compile(
    r"^Отображается\s+заголовок\s+«Блок\s+«(?P<title>[^»]+)»»"
    r"(?P<punctuation>[.!?]?)$",
    re.IGNORECASE,
)
_REQUIREDNESS_SIGNAL_PATTERN = re.compile(
    r"(?:(?<![а-яё])обязательн(?:ое|ая|ый|ым|ого|а)?(?:\s+поле)?|"
    r"должн(?:о|а|ы)?\s+быть\s+заполнен(?:о|а|ы)?|"
    r"required\b|mandatory\b)",
    re.IGNORECASE,
)
_COMPOUND_REQUIREDNESS_PATTERN = re.compile(
    r"(?P<prefix>(?<![а-яё])обязательно\s+должн\s*ы\s+быть\s+"
    r"введен\s*ы\s+)(?P<targets>[^.;:]{3,160})(?=[.;:]|$)",
    re.IGNORECASE,
)
_COMPOUND_REQUIREDNESS_TARGET_SEPARATOR_PATTERN = re.compile(
    r"\s*,\s*|\s+и\s+",
    re.IGNORECASE,
)
_OPTIONALITY_SIGNAL_PATTERN = re.compile(
    r"(?:не\s*обязательн(?:ое|ая|ый|ым|ого|а)?|"
    r"не\s+является\s+обязательн(?:ым|ой|ыми)?|"
    r"опциональн(?:ое|ая|ый|ым|ого|а)?|optional\b|"
    r"может\s+оставаться\s+пуст(?:ым|ой|ыми)?)",
    re.IGNORECASE,
)
_BINARY_LOGICAL_DEFAULT_PATTERN = re.compile(
    r"значение\s+по\s+умолчанию\s+«(?P<value>Да|Нет)»",
    re.IGNORECASE,
)


def _binary_logical_default(
    row: Mapping[str, Any],
) -> dict[str, str] | None:
    cells = row.get("physical_table_cells", [])
    if not isinstance(cells, list):
        return None
    cell_texts = [
        str(cell.get("bounded_source_text", "")).strip()
        for cell in cells
        if isinstance(cell, Mapping)
    ]
    if not any(
        value.casefold() in {"переключатель", "флажок", "чек-бокс", "checkbox"}
        for value in cell_texts
    ) or not any(
        "логическое" in value.casefold()
        and "да/нет" in value.casefold().replace(" ", "")
        for value in cell_texts
    ):
        return None
    match = _BINARY_LOGICAL_DEFAULT_PATTERN.search(
        str(row.get("bounded_source_text", ""))
    )
    if match is None:
        return None
    return {
        "value_semantics": "binary-logical-default",
        "default_value": match.group("value"),
        "default_source_fragment": match.group(0),
    }


def _compound_requiredness_targets(
    text: str,
) -> list[tuple[int, int, str]]:
    """Return literal independently required targets from an explicit source list.

    The parser is intentionally narrow: it accepts only the source construction
    ``обязательно должны быть введены <A> и <B>`` (including whitespace split by
    DOCX/XHTML extraction) and requires a short list of at least two targets.
    """

    targets: list[tuple[int, int, str]] = []
    for compound in _COMPOUND_REQUIREDNESS_PATTERN.finditer(text):
        target_text = compound.group("targets")
        target_offset = compound.start("targets")
        separators = list(
            _COMPOUND_REQUIREDNESS_TARGET_SEPARATOR_PATTERN.finditer(target_text)
        )
        if not separators:
            continue
        spans: list[tuple[int, int]] = []
        start = 0
        for separator in separators:
            spans.append((start, separator.start()))
            start = separator.end()
        spans.append((start, len(target_text)))
        parsed: list[tuple[int, int, str]] = []
        for local_start, local_end in spans:
            raw_target = target_text[local_start:local_end]
            stripped = raw_target.strip()
            leading = len(raw_target) - len(raw_target.lstrip())
            absolute_start = target_offset + local_start + leading
            absolute_end = absolute_start + len(stripped)
            if (
                not stripped
                or len(stripped) > 80
                or len(re.findall(r"[0-9A-Za-zА-Яа-яЁё]+", stripped)) > 5
            ):
                parsed = []
                break
            parsed.append((absolute_start, absolute_end, stripped))
        if 2 <= len(parsed) <= 6:
            targets.extend(parsed)
    return targets


def _signal_codes(
    text: str,
    signal_start: int,
    codes: Sequence[str],
) -> list[str]:
    preceding: list[tuple[int, str]] = []
    for code in codes:
        for match in re.finditer(re.escape(str(code)), text, flags=re.IGNORECASE):
            if match.start() <= signal_start:
                preceding.append((match.start(), str(code)))
    if preceding:
        nearest = max(position for position, _code in preceding)
        return [
            code
            for position, code in preceding
            if position == nearest
        ]
    return list(map(str, codes)) if len(codes) <= 1 else []


def _is_default_template_state_signal(
    text: str,
    *,
    signal_start: int,
    signal_end: int,
) -> bool:
    """Return true when ``template`` describes initial UI state, not a restriction."""

    anchor = text[signal_start:signal_end]
    if re.fullmatch(r"шаблон(?:у|а|ом|е)?", anchor, flags=re.IGNORECASE) is None:
        return False
    return any(
        match.start() <= signal_start and signal_end <= match.end()
        for match in _DEFAULT_TEMPLATE_STATE_PATTERN.finditer(text)
    )


def _source_signal_registry(
    rows: Sequence[Mapping[str, Any]],
    code_registry: Mapping[str, Sequence[str]],
) -> dict[str, list[dict[str, Any]]]:
    negative: list[dict[str, Any]] = []
    requiredness: list[dict[str, Any]] = []
    for row in rows:
        row_id = str(row.get("source_row_id", ""))
        text = str(row.get("bounded_source_text", ""))
        row_codes = code_registry.get(row_id, ())
        matches: list[tuple[int, int, str, str]] = []
        for restriction_type, pattern in _NEGATIVE_SIGNAL_PATTERNS:
            for match in pattern.finditer(text):
                if restriction_type == "format" and _is_default_template_state_signal(
                    text,
                    signal_start=match.start(),
                    signal_end=match.end(),
                ):
                    continue
                matches.append(
                    (match.start(), match.end(), restriction_type, match.group(0))
                )
        matches.sort(key=lambda item: (item[0], item[1], item[2]))
        for _start, _end, restriction_type, anchor in matches:
            signal_id = f"SIG-NEG-{len(negative) + 1:03d}"
            negative.append(
                {
                    "signal_id": signal_id,
                    "scope_obligation_id": "SO-" + signal_id.removeprefix("SIG-"),
                    "source_row_id": row_id,
                    "source_ref": str(row.get("source_ref", "")),
                    "field_or_block": str(row.get("field_or_action", "")),
                    "requirement_codes": _signal_codes(text, _start, row_codes),
                    "restriction_type": restriction_type,
                    "literal_anchor": anchor,
                }
            )
        field_properties = row.get("field_properties")
        typed_requiredness = (
            field_properties.get("requiredness")
            if isinstance(field_properties, Mapping)
            else None
        )
        if isinstance(typed_requiredness, Mapping):
            normalized = typed_requiredness.get("normalized_value")
            if normalized not in {"required", "optional"}:
                raise SemanticDesignBridgeError(
                    f"{row_id} typed requiredness has invalid normalized_value"
                )
            signal_id = f"SIG-REQ-{len(requiredness) + 1:03d}"
            typed_signal = {
                    "signal_id": signal_id,
                    "scope_obligation_id": "SO-" + signal_id.removeprefix("SIG-"),
                    "source_row_id": row_id,
                    "source_ref": str(row.get("source_ref", "")),
                    "field_or_block": str(row.get("field_or_action", "")),
                    "requirement_codes": [],
                    "restriction_type": (
                        "requiredness" if normalized == "required" else "optionality"
                    ),
                    "literal_anchor": str(typed_requiredness.get("source_value", "")),
                    "requiredness_source": str(
                        typed_requiredness.get("source_value", "")
                    ),
                    "source_binding": "typed-xhtml-cell",
                    "source_property_id": str(
                        typed_requiredness.get("property_id", "")
                    ),
                    "source_cell_locator": str(
                        typed_requiredness.get("source_cell_locator", "")
                    ),
                }
            binary_default = _binary_logical_default(row)
            if binary_default is not None:
                typed_signal.update(binary_default)
            action_control_kind = _action_control_kind(row)
            if action_control_kind is not None:
                typed_signal.update(
                    {
                        "control_semantics": "action-control",
                        "action_control_kind": action_control_kind,
                    }
                )
            requiredness.append(typed_signal)
        compound_targets = _compound_requiredness_targets(text)
        compound_spans = [(start, end) for start, end, _target in compound_targets]
        for target_start, _target_end, target in compound_targets:
            if target.casefold() == str(row.get("field_or_action", "")).casefold():
                continue
            signal_id = f"SIG-REQ-{len(requiredness) + 1:03d}"
            requiredness.append(
                {
                    "signal_id": signal_id,
                    "scope_obligation_id": "SO-" + signal_id.removeprefix("SIG-"),
                    "source_row_id": row_id,
                    "source_ref": str(row.get("source_ref", "")),
                    "field_or_block": target,
                    "requirement_codes": _signal_codes(
                        text,
                        target_start,
                        row_codes,
                    ),
                    "restriction_type": "requiredness",
                    "literal_anchor": target,
                    "requiredness_source": text[
                        max(0, text.rfind(".", 0, target_start) + 1) :
                        next(
                            (
                                index + 1
                                for index in range(target_start, len(text))
                                if text[index] in ".;:"
                            ),
                            len(text),
                        )
                    ].strip(),
                    "source_binding": "compound-text-requirement",
                }
            )
        if isinstance(typed_requiredness, Mapping):
            continue
        optional_matches = list(_OPTIONALITY_SIGNAL_PATTERN.finditer(text))
        required_matches = [
            match
            for match in _REQUIREDNESS_SIGNAL_PATTERN.finditer(text)
            if not any(
                optional.start() <= match.start() < optional.end()
                for optional in optional_matches
            )
            and not any(
                start <= match.start() < end
                for start, end in compound_spans
            )
        ]
        requiredness_matches = [
            ("optionality", match) for match in optional_matches
        ] + [
            ("requiredness", match) for match in required_matches
        ]
        requiredness_matches.sort(
            key=lambda item: (item[1].start(), item[1].end(), item[0])
        )
        for restriction_type, match in requiredness_matches:
            signal_id = f"SIG-REQ-{len(requiredness) + 1:03d}"
            requiredness.append(
                {
                    "signal_id": signal_id,
                    "scope_obligation_id": "SO-" + signal_id.removeprefix("SIG-"),
                    "source_row_id": row_id,
                    "source_ref": str(row.get("source_ref", "")),
                    "field_or_block": str(row.get("field_or_action", "")),
                    "requirement_codes": _signal_codes(
                        text,
                        match.start(),
                        row_codes,
                    ),
                    "restriction_type": restriction_type,
                    "literal_anchor": match.group(0),
                }
            )
    return {"negative": negative, "requiredness": requiredness}


def semantic_source_signal_registry(
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Return source-anchored semantic signals for planning and safe shard merge."""

    validate_bridge_boundary(context, boundary)
    eligible_rows = _eligible_semantic_rows(context, boundary)
    code_registry = {
        str(item["source_row_id"]): list(map(str, item["requirement_codes"]))
        for item in boundary["source_decisions"]
    }
    return _source_signal_registry(eligible_rows, code_registry)


def _eligible_semantic_rows(
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
    source_designs: Sequence[Mapping[str, Any]] = (),
) -> list[Mapping[str, Any]]:
    disposition_by_row = {
        str(item.get("source_row_id")): item.get("disposition")
        for item in boundary.get("source_decisions", [])
        if isinstance(item, Mapping)
    }
    eligible_ids = {
        row_id
        for row_id, disposition in disposition_by_row.items()
        if disposition == "included"
    }
    for dependency in boundary.get("dependencies", []):
        if not isinstance(dependency, Mapping) or dependency.get("resolution") == "scope-excluded":
            continue
        for key in ("source_row_ids", "target_source_row_ids"):
            for row_id in dependency.get(key, []):
                row_id = str(row_id)
                if disposition_by_row.get(row_id) == "context":
                    eligible_ids.add(row_id)
    for source_design in source_designs:
        if not isinstance(source_design, Mapping):
            continue
        for assertion in source_design.get("assertions", []):
            if not isinstance(assertion, Mapping) or assertion.get(
                "semantic_disposition"
            ) != "testable":
                continue
            for binding in assertion.get("supporting_source_bindings", []):
                if not isinstance(binding, Mapping):
                    continue
                row_id = str(binding.get("source_row_id", ""))
                if disposition_by_row.get(row_id) == "excluded":
                    raise SemanticDesignBridgeError(
                        f"excluded row {row_id} cannot provide executable supporting coverage"
                    )
                if disposition_by_row.get(row_id) == "context":
                    eligible_ids.add(row_id)
    return [
        row
        for row in context.get("source_rows", [])
        if isinstance(row, Mapping) and str(row.get("source_row_id")) in eligible_ids
    ]


def validate_semantic_design_binding(
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
    design: Mapping[str, Any],
    *,
    clarifications: Sequence[Mapping[str, Any]] = (),
    require_ready: bool = False,
) -> dict[str, Any]:
    validate_bridge_boundary(context, boundary)
    row_ids = [
        str(item.get("source_row_id", ""))
        for item in context.get("source_rows", [])
        if isinstance(item, Mapping)
    ]
    _validate_schema_instance(
        design,
        semantic_design_output_schema(row_ids, require_ready=require_ready),
    )
    if design.get("version") != SEMANTIC_DESIGN_VERSION:
        raise SemanticDesignBridgeError(
            f"semantic design version must equal {SEMANTIC_DESIGN_VERSION}"
        )
    if design.get("contract") != SEMANTIC_DESIGN_CONTRACT:
        raise SemanticDesignBridgeError("semantic design contract identity mismatch")
    status = design.get("status")
    blocking_reason = design.get("blocking_reason")
    if status == "ready":
        if blocking_reason != "none_required":
            raise SemanticDesignBridgeError(
                "ready semantic design requires blocking_reason=none_required"
            )
    elif status == "blocked":
        if (
            not isinstance(blocking_reason, str)
            or len(blocking_reason.strip()) < 12
            or blocking_reason == "none_required"
        ):
            raise SemanticDesignBridgeError(
                "blocked semantic design requires a substantive blocking_reason"
            )
    else:
        raise SemanticDesignBridgeError("semantic design status must be ready or blocked")
    if design.get("prepared_context_sha256") != prepared_context_sha256(context):
        raise SemanticDesignBridgeError("semantic design context digest mismatch")
    if design.get("scope_boundary_decision_sha256") != canonical_payload_sha256(boundary):
        raise SemanticDesignBridgeError("semantic design boundary digest mismatch")
    if design.get("scope_summary") != boundary.get("scope_summary"):
        raise SemanticDesignBridgeError("semantic design scope_summary drifted from boundary")
    scope_boundary = boundary["scope_boundary"]
    if design.get("included") != scope_boundary.get("include"):
        raise SemanticDesignBridgeError("semantic design included scope drifted from boundary")
    if design.get("excluded") != scope_boundary.get("exclude"):
        raise SemanticDesignBridgeError("semantic design excluded scope drifted from boundary")
    if design.get("mockup_locators") != boundary.get("mockup_locators"):
        raise SemanticDesignBridgeError(
            "semantic design mockup locators drifted from boundary"
        )

    normalized_clarifications = _normalize_approved_clarifications(
        context,
        clarifications,
    )
    if status == "blocked":
        if require_ready:
            raise SemanticDesignBridgeError(
                "blocked semantic design cannot be materialized as runnable workflow"
            )
        semantic_collections = (
            "source_designs",
            "obligations",
            "reset_lifecycle_bindings",
            "dependency_bindings",
            "dictionaries",
            "negative_oracles",
            "requiredness_oracles",
            "applicability",
        )
        if any(design.get(name) != [] for name in semantic_collections):
            raise SemanticDesignBridgeError(
                "blocked semantic design must not publish a partial semantic payload"
            )
        return {
            "version": BRIDGE_CONTRACT_VERSION,
            "status": "blocked",
            "contract": BRIDGE_CONTRACT_NAME,
            "prepared_context_sha256": prepared_context_sha256(context),
            "scope_boundary_decision_sha256": canonical_payload_sha256(boundary),
            "semantic_design_decision_sha256": canonical_payload_sha256(design),
            "source_row_count": len(context["source_rows"]),
            "included_source_row_count": sum(
                item.get("disposition") == "included"
                for item in boundary["source_decisions"]
            ),
            "assertion_count": 0,
            "testable_assertion_count": 0,
            "obligation_count": 0,
            "dependency_binding_count": 0,
            "planned_test_case_count": 0,
            "dictionary_count": 0,
            "negative_oracle_count": 0,
            "requiredness_oracle_count": 0,
            "approved_clarification_count": len(normalized_clarifications),
            "state_change_obligation_count": 0,
            "reset_lifecycle_binding_count": 0,
        }

    rows = context["source_rows"]
    rows_by_id = {str(item["source_row_id"]): item for item in rows}
    boundary_decisions = boundary["source_decisions"]
    fully_gapped_observation_rows = _fully_gapped_observation_rows(boundary)
    boundary_disposition_by_row = {
        str(item.get("source_row_id", "")): item.get("disposition")
        for item in boundary_decisions
        if isinstance(item, Mapping)
    }
    source_designs = design.get("source_designs")
    if not isinstance(source_designs, list):
        raise SemanticDesignBridgeError("semantic design source_designs must be an array")
    design_ids = [
        str(item.get("source_row_id", ""))
        for item in source_designs
        if isinstance(item, Mapping)
    ]
    if design_ids != list(rows_by_id):
        raise SemanticDesignBridgeError(
            "semantic design must account for every source row in prepared order"
        )

    assertions: list[Mapping[str, Any]] = []
    assertion_by_id: dict[str, Mapping[str, Any]] = {}
    assertion_row_by_id: dict[str, str] = {}
    assertion_by_atom: dict[str, Mapping[str, Any]] = {}
    assertion_owner_by_obligation: dict[str, Mapping[str, Any]] = {}
    row_by_obligation: dict[str, str] = {}
    testable_assertion_count = 0
    clarification_binding_codes: dict[str, set[str]] = {}
    clarification_binding_rows: dict[str, set[str]] = {}
    clarification_binding_assertions: dict[str, set[str]] = {}
    clarification_binding_clause_kinds: dict[
        tuple[str, str], set[str]
    ] = {}
    assertion_support_rows: dict[str, set[str]] = {}
    assertion_source_context_clarifications: dict[str, set[str]] = {}
    clarification_by_id = {
        str(item["clarification_id"]): item for item in normalized_clarifications
    }
    for boundary_decision, source_design in zip(
        boundary_decisions,
        source_designs,
        strict=True,
    ):
        if not isinstance(boundary_decision, Mapping) or not isinstance(source_design, Mapping):
            raise SemanticDesignBridgeError("semantic design rows must be objects")
        row_id = str(boundary_decision["source_row_id"])
        boundary_disposition = boundary_decision.get("disposition")
        if source_design.get("boundary_disposition") != boundary_disposition:
            raise SemanticDesignBridgeError(
                f"{row_id} disposition drifted from authoritative boundary"
            )
        expected_codes = boundary_decision.get("requirement_codes")
        if source_design.get("requirement_codes") != expected_codes:
            raise SemanticDesignBridgeError(
                f"{row_id} requirement registry drifted from authoritative boundary"
            )
        row_assertions = source_design.get("assertions")
        if not isinstance(row_assertions, list) or not row_assertions:
            raise SemanticDesignBridgeError(f"{row_id} requires explicit assertions")
        row_testable = 0
        row_code_union: set[str] = set()
        for assertion in row_assertions:
            if not isinstance(assertion, Mapping):
                raise SemanticDesignBridgeError(f"{row_id} assertions must be objects")
            assertion_codes = assertion.get("requirement_codes")
            if not isinstance(assertion_codes, list) or len(assertion_codes) != len(
                set(map(str, assertion_codes))
            ):
                raise SemanticDesignBridgeError(
                    f"{row_id} assertion requirement_codes must be duplicate-free"
                )
            if set(map(str, assertion_codes)) - set(map(str, expected_codes)):
                raise SemanticDesignBridgeError(
                    f"{row_id} assertion uses requirement codes outside its row"
                )
            row_code_union.update(map(str, assertion_codes))
            disposition = assertion.get("semantic_disposition")
            readiness = assertion.get("execution_readiness")
            obligation_ids = assertion.get("obligation_ids")
            if not isinstance(obligation_ids, list) or len(obligation_ids) != len(
                set(map(str, obligation_ids))
            ):
                raise SemanticDesignBridgeError(
                    f"{row_id} assertion obligation_ids must be duplicate-free"
                )
            condition_clauses = assertion.get("condition_clauses")
            action_clauses = assertion.get("action_clauses")
            oracle_clauses = assertion.get("oracle_clauses")
            if not all(
                isinstance(value, list)
                for value in (condition_clauses, action_clauses, oracle_clauses)
            ):
                raise SemanticDesignBridgeError(f"{row_id} clauses must be arrays")
            if disposition == "testable":
                row_testable += 1
                testable_assertion_count += 1
                if readiness != "ready" or assertion.get(
                    "execution_readiness_rationale"
                ) != "none_required":
                    raise SemanticDesignBridgeError(
                        f"{row_id} testable assertion must be execution-ready"
                    )
                if not action_clauses or not oracle_clauses or not obligation_ids:
                    raise SemanticDesignBridgeError(
                        f"{row_id} testable assertion needs action, oracle and obligation"
                    )
                _validate_distinct_action_oracle_clauses(assertion)
            elif disposition == "not-applicable":
                if readiness != "not-applicable" or assertion.get(
                    "execution_readiness_rationale"
                ) != "none_required":
                    raise SemanticDesignBridgeError(
                        f"{row_id} N/A assertion readiness is invalid"
                    )
                if condition_clauses or action_clauses or oracle_clauses or obligation_ids:
                    raise SemanticDesignBridgeError(
                        f"{row_id} N/A assertion cannot own executable semantics"
                    )
                rationale = assertion.get("disposition_rationale")
                if not isinstance(rationale, str) or len(rationale.strip()) < 12:
                    raise SemanticDesignBridgeError(
                        f"{row_id} N/A assertion requires a substantive rationale"
                    )
            elif disposition == "ambiguous":
                rationale = assertion.get("execution_readiness_rationale")
                if (
                    readiness != "dependency-blocked"
                    or not isinstance(rationale, str)
                    or len(rationale.strip()) < 12
                    or rationale == "none_required"
                ):
                    raise SemanticDesignBridgeError(
                        f"{row_id} ambiguous assertion must be dependency-blocked "
                        "with a substantive readiness rationale"
                    )
                if condition_clauses or action_clauses or oracle_clauses or obligation_ids:
                    raise SemanticDesignBridgeError(
                        f"{row_id} ambiguous assertion cannot own executable semantics"
                    )
                disposition_rationale = assertion.get("disposition_rationale")
                if (
                    not isinstance(disposition_rationale, str)
                    or len(disposition_rationale.strip()) < 12
                ):
                    raise SemanticDesignBridgeError(
                        f"{row_id} ambiguous assertion requires a substantive rationale"
                    )
            else:
                raise SemanticDesignBridgeError(
                    f"{row_id} semantic_disposition is invalid"
                )
            if (
                boundary_disposition == "included"
                and disposition == "not-applicable"
                and len(row_assertions) == 1
                and row_id not in fully_gapped_observation_rows
            ):
                raise SemanticDesignBridgeError(
                    f"{row_id} included row cannot be N/A-only"
                )
            if boundary_disposition != "included" and disposition != "not-applicable":
                raise SemanticDesignBridgeError(
                    f"{row_id} context/excluded row cannot become testable or ambiguous"
                )

            requirement_evidence = assertion.get("requirement_code_evidence")
            if not isinstance(requirement_evidence, list):
                raise SemanticDesignBridgeError(
                    f"{row_id} requirement_code_evidence must be an array"
                )
            evidence_codes = [
                str(item.get("requirement_code", ""))
                for item in requirement_evidence
                if isinstance(item, Mapping)
            ]
            if (
                len(evidence_codes) != len(requirement_evidence)
                or len(evidence_codes) != len(set(evidence_codes))
                or set(evidence_codes) != set(map(str, assertion_codes))
            ):
                raise SemanticDesignBridgeError(
                    f"{row_id} requirement-code evidence must cover assertion codes exactly"
                )
            for binding in requirement_evidence:
                assert isinstance(binding, Mapping)
                binding_row = str(binding.get("source_row_id", ""))
                if binding_row != row_id:
                    raise SemanticDesignBridgeError(
                        f"{row_id} requirement-code evidence must bind its owning source row"
                    )
                requirement_code = str(binding.get("requirement_code", ""))
                provenance_role = binding.get("provenance_role")
                exact_source_fragment = binding.get("exact_source_fragment")
                evidence_source_path = binding.get("evidence_source_path")
                evidence_locator = binding.get("evidence_locator")
                if provenance_role == "xhtml-row":
                    if (
                        evidence_source_path != "none_required"
                        or evidence_locator != "none_required"
                    ):
                        raise SemanticDesignBridgeError(
                            f"{row_id} XHTML requirement evidence requires "
                            "none_required PDF evidence fields"
                        )
                    _literal_fragment(
                        rows_by_id,
                        binding_row,
                        exact_source_fragment,
                        label=f"{row_id} requirement evidence",
                    )
                    assert isinstance(exact_source_fragment, str)
                    if not contains_token_bounded_source_fragment(
                        normalize_exact_source_text(exact_source_fragment),
                        normalize_exact_source_text(requirement_code),
                    ):
                        raise SemanticDesignBridgeError(
                            f"{row_id} XHTML requirement evidence must contain its "
                            "literal requirement-code token"
                        )
                elif provenance_role == "pdf-parity":
                    if exact_source_fragment != "none_required":
                        raise SemanticDesignBridgeError(
                            f"{row_id} PDF parity requirement evidence requires "
                            "exact_source_fragment=none_required"
                        )
                    main_ft_pdf = context.get("main_ft_pdf")
                    if (
                        not isinstance(main_ft_pdf, str)
                        or not main_ft_pdf.strip()
                        or evidence_source_path != main_ft_pdf
                    ):
                        raise SemanticDesignBridgeError(
                            f"{row_id} PDF parity requirement evidence must bind "
                            "context.main_ft_pdf exactly"
                        )
                    if (
                        not isinstance(evidence_locator, str)
                        or re.fullmatch(r"page:[1-9][0-9]*", evidence_locator) is None
                    ):
                        raise SemanticDesignBridgeError(
                            f"{row_id} PDF parity requirement evidence locator must use page:N"
                        )
                    parity_rows = context.get("parity")
                    if not isinstance(parity_rows, list) or not any(
                        isinstance(item, Mapping)
                        and item.get("requirement_code") == requirement_code
                        and item.get("pdf_locator") == evidence_locator
                        for item in parity_rows
                    ):
                        raise SemanticDesignBridgeError(
                            f"{row_id} PDF parity requirement evidence must match the "
                            "exact context.parity code and locator"
                        )
                    sources = context.get("sources")
                    if not isinstance(sources, list) or not any(
                        isinstance(item, Mapping)
                        and item.get("path") == main_ft_pdf
                        and item.get("manifest_binding")
                        == "structural-visual-parity"
                        for item in sources
                    ):
                        raise SemanticDesignBridgeError(
                            f"{row_id} PDF parity requirement evidence source is not "
                            "registered as structural-visual-parity"
                        )
                else:
                    raise SemanticDesignBridgeError(
                        f"{row_id} requirement evidence provenance_role is invalid"
                    )

            _validate_always_visibility_prestate_cardinality(
                assertion,
                requirement_evidence,
                rows_by_id[row_id],
            )

            supporting = assertion.get("supporting_source_bindings")
            if not isinstance(supporting, list):
                raise SemanticDesignBridgeError(
                    f"{row_id} supporting_source_bindings must be an array"
                )
            supporting_row_ids: set[str] = set()
            for binding in supporting:
                if not isinstance(binding, Mapping):
                    raise SemanticDesignBridgeError(
                        f"{row_id} supporting binding must be an object"
                    )
                binding_row = str(binding.get("source_row_id", ""))
                if binding_row == row_id:
                    raise SemanticDesignBridgeError(
                        f"{row_id} primary-row evidence cannot be a supporting binding"
                    )
                if boundary_disposition_by_row.get(binding_row) == "excluded":
                    raise SemanticDesignBridgeError(
                        f"{row_id} cannot declare excluded row {binding_row} as support"
                    )
                _literal_fragment(
                    rows_by_id,
                    binding_row,
                    binding.get("exact_source_fragment"),
                    label=f"{row_id} supporting evidence",
                )
                supporting_row_ids.add(binding_row)

            clause_evidence = assertion.get("clause_evidence")
            if not isinstance(clause_evidence, list):
                raise SemanticDesignBridgeError(f"{row_id} clause_evidence must be an array")
            expected_clause_keys = {
                (kind, index)
                for kind, clauses in (
                    ("condition", condition_clauses),
                    ("action", action_clauses),
                    ("oracle", oracle_clauses),
                )
                for index in range(len(clauses))
            }
            actual_clause_keys: list[tuple[str, int]] = []
            for binding in clause_evidence:
                if not isinstance(binding, Mapping) or type(binding.get("clause_index")) is not int:
                    raise SemanticDesignBridgeError(
                        f"{row_id} clause evidence entries are invalid"
                    )
                key = (str(binding.get("clause_kind")), int(binding["clause_index"]))
                actual_clause_keys.append(key)
                binding_row = str(binding.get("source_row_id", ""))
                if binding_row != row_id and binding_row not in supporting_row_ids:
                    raise SemanticDesignBridgeError(
                        f"{row_id} clause evidence may bind only its own row or an "
                        "explicitly declared non-excluded supporting row"
                    )
                _literal_fragment(
                    rows_by_id,
                    binding_row,
                    binding.get("exact_source_fragment"),
                    label=f"{row_id} clause evidence",
                )
            if set(actual_clause_keys) != expected_clause_keys or len(actual_clause_keys) != len(
                set(actual_clause_keys)
            ):
                raise SemanticDesignBridgeError(
                    f"{row_id} clause evidence must bind every clause exactly once"
                )

            clarification_bindings = assertion.get("clarification_clause_bindings")
            if not isinstance(clarification_bindings, list):
                raise SemanticDesignBridgeError(
                    f"{row_id} clarification bindings must be an array"
                )
            clarification_binding_keys: set[tuple[str, str, int]] = set()
            for binding in clarification_bindings:
                if not isinstance(binding, Mapping):
                    raise SemanticDesignBridgeError(
                        f"{row_id} clarification binding must be an object"
                    )
                try:
                    typed_binding = ClarificationClauseBinding.from_dict(binding)
                except (SourceAssertionContractError, KeyError, TypeError, ValueError) as exc:
                    raise SemanticDesignBridgeError(
                        f"{row_id} clarification binding is invalid: {exc}"
                    ) from exc
                clarification_id = typed_binding.clarification_id
                record = clarification_by_id.get(clarification_id)
                if record is None:
                    raise SemanticDesignBridgeError(
                        f"{row_id} references unknown clarification {clarification_id}"
                    )
                if typed_binding.exact_answer_sha256 != record.get(
                    "exact_answer_sha256"
                ) or typed_binding.binding_scope != record.get("binding_scope"):
                    raise SemanticDesignBridgeError(
                        f"{row_id} clarification binding provenance mismatch"
                    )
                kind = typed_binding.clause_kind
                index = typed_binding.clause_index
                if kind == "canonical":
                    if disposition != "not-applicable" or index != 0:
                        raise SemanticDesignBridgeError(
                            f"{row_id} canonical clarification binding is invalid"
                        )
                elif (kind, index) not in expected_clause_keys:
                    raise SemanticDesignBridgeError(
                        f"{row_id} clarification binding references unknown clause"
                    )
                key = (clarification_id, kind, index)
                if key in clarification_binding_keys:
                    raise SemanticDesignBridgeError(
                        f"{row_id} clarification bindings contain duplicates"
                    )
                clarification_binding_keys.add(key)
                local_codes = set(typed_binding.requirement_codes)
                local_rows = set(typed_binding.source_row_ids)
                if typed_binding.binding_scope == "requirement-code":
                    if local_codes - set(map(str, record.get("requirement_codes", []))):
                        raise SemanticDesignBridgeError(
                            f"{row_id} clarification binding names undeclared codes"
                        )
                    if local_codes - set(map(str, assertion_codes)):
                        raise SemanticDesignBridgeError(
                            f"{row_id} clarification binding names codes outside assertion"
                        )
                else:
                    if local_rows - set(map(str, record.get("source_row_ids", []))):
                        raise SemanticDesignBridgeError(
                            f"{row_id} clarification binding names undeclared rows"
                        )
                    if local_rows != {row_id}:
                        raise SemanticDesignBridgeError(
                            f"{row_id} source-context clarification must bind only its own row"
                        )
                clarification_binding_codes.setdefault(clarification_id, set()).update(
                    local_codes
                )
                clarification_binding_rows.setdefault(clarification_id, set()).update(
                    local_rows
                )
                bound_assertion_id = str(assertion.get("assertion_id", ""))
                clarification_binding_assertions.setdefault(
                    clarification_id,
                    set(),
                ).add(bound_assertion_id)
                clarification_binding_clause_kinds.setdefault(
                    (clarification_id, bound_assertion_id),
                    set(),
                ).add(kind)
                if typed_binding.binding_scope == "source-context":
                    assertion_source_context_clarifications.setdefault(
                        bound_assertion_id,
                        set(),
                    ).add(clarification_id)

            atom_id = str(assertion.get("atom_id", ""))
            if not atom_id or atom_id in assertion_by_atom:
                raise SemanticDesignBridgeError(
                    "semantic design atom_id values must be non-empty and unique"
                )
            assertion_by_atom[atom_id] = assertion
            assertion_id = str(assertion.get("assertion_id", ""))
            if not assertion_id or assertion_id in assertion_by_id:
                raise SemanticDesignBridgeError(
                    "semantic design assertion_id values must be non-empty and unique"
                )
            assertion_by_id[assertion_id] = assertion
            assertion_row_by_id[assertion_id] = row_id
            assertion_support_rows[assertion_id] = set(supporting_row_ids)
            for obligation_id in map(str, obligation_ids):
                if obligation_id in assertion_owner_by_obligation:
                    raise SemanticDesignBridgeError(
                        f"duplicate assertion obligation binding: {obligation_id}"
                    )
                assertion_owner_by_obligation[obligation_id] = assertion
                row_by_obligation[obligation_id] = row_id
            assertions.append(assertion)
        if set(map(str, expected_codes)) != row_code_union:
            raise SemanticDesignBridgeError(
                f"{row_id} assertion code union does not equal row registry"
            )
        _validate_necessary_condition_control_cardinality(row_id, row_assertions)
        if (
            boundary_disposition == "included"
            and row_testable == 0
            and row_id not in fully_gapped_observation_rows
        ):
            raise SemanticDesignBridgeError(
                f"{row_id} included boundary row requires a testable assertion"
            )

    assertion_ids = _unique_nonempty(
        [item.get("assertion_id", "") for item in assertions],
        label="assertion_id values",
    )
    if len(assertion_ids) != len(assertions):
        raise AssertionError("unreachable")

    eligible_rows = _eligible_semantic_rows(context, boundary, source_designs)
    eligible_row_ids = {
        str(item.get("source_row_id", "")) for item in eligible_rows
    }

    definition_gap_codes: set[str] = set()
    boundary_codes_by_row = {
        str(item.get("source_row_id", "")): set(
            map(str, item.get("requirement_codes", []))
        )
        for item in boundary.get("source_decisions", [])
        if isinstance(item, Mapping)
    }
    for gap in boundary.get("gaps", []):
        if (
            not isinstance(gap, Mapping)
            or gap.get("gap_type") != "missing-source-definition"
            or gap.get("blocking") is not False
            or gap.get("downstream_handling") != "carry-to-source-model"
        ):
            continue
        fragments = " ".join(map(str, gap.get("exact_source_fragments", [])))
        for row_id in map(str, gap.get("source_row_ids", [])):
            definition_gap_codes.update(
                code
                for code in boundary_codes_by_row.get(row_id, set())
                if code.casefold() in fragments.casefold()
            )
    for clarification_id, record in clarification_by_id.items():
        expected_codes = set(map(str, record.get("requirement_codes", []))) - (
            definition_gap_codes
        )
        expected_rows = set(map(str, record.get("source_row_ids", [])))
        if clarification_binding_codes.get(clarification_id, set()) != expected_codes:
            raise SemanticDesignBridgeError(
                f"{clarification_id} requirement-code binding union is incomplete"
            )
        if clarification_binding_rows.get(clarification_id, set()) != expected_rows:
            raise SemanticDesignBridgeError(
                f"{clarification_id} source-row binding union is incomplete"
            )

    dependency_relation_rows = [
        {
            *map(str, dependency.get("source_row_ids", [])),
            *map(str, dependency.get("target_source_row_ids", [])),
        }
        for dependency in boundary.get("dependencies", [])
        if isinstance(dependency, Mapping)
        and dependency.get("resolution") != "scope-excluded"
    ]
    typed_property_header_relations = {
        str(item["source_property_id"]): (
            str(item["source_row_id"]),
            str(item["header_source_row_id"]),
        )
        for item in _typed_field_property_registry(
            context,
            eligible_row_ids=eligible_row_ids,
        )
    }
    for assertion_id, support_rows in assertion_support_rows.items():
        owner_row = assertion_row_by_id[assertion_id]
        assertion = assertion_by_id[assertion_id]
        property_relation = typed_property_header_relations.get(
            str(assertion.get("source_property_id", ""))
        )
        for support_row in support_rows:
            if boundary_disposition_by_row.get(support_row) != "context":
                continue
            dependency_related = any(
                {owner_row, support_row}.issubset(relation_rows)
                for relation_rows in dependency_relation_rows
            )
            clarification_related = any(
                owner_row
                in set(map(str, clarification_by_id[clarification_id].get(
                    "source_row_ids",
                    [],
                )))
                and support_row
                in set(map(str, clarification_by_id[clarification_id].get(
                    "source_row_ids",
                    [],
                )))
                and any(
                    assertion_row_by_id.get(bound_assertion_id) == support_row
                    for bound_assertion_id in clarification_binding_assertions.get(
                        clarification_id,
                        set(),
                    )
                )
                for clarification_id in assertion_source_context_clarifications.get(
                    assertion_id,
                    set(),
                )
            )
            typed_header_related = property_relation == (owner_row, support_row)
            if not (
                dependency_related
                or clarification_related
                or typed_header_related
            ):
                raise SemanticDesignBridgeError(
                    f"{assertion_id} supporting row {support_row} lacks an explicit "
                    "boundary dependency or typed source-context clarification relation"
                )

    lifecycle_clarification_ids = {
        clarification_id
        for clarification_id, record in clarification_by_id.items()
        if _text_requires_readd_lifecycle(record.get("exact_answer", ""))
    }
    lifecycle_clarification_assertions: set[str] = set()
    for clarification_id in lifecycle_clarification_ids:
        bound_assertion_ids = clarification_binding_assertions.get(
            clarification_id,
            set(),
        )
        if not bound_assertion_ids:
            raise SemanticDesignBridgeError(
                f"{clarification_id} lifecycle clarification is not bound to an assertion"
            )
        for assertion_id in bound_assertion_ids:
            assertion = assertion_by_id.get(assertion_id)
            if (
                assertion is None
                or assertion.get("semantic_disposition") != "testable"
                or not _assertion_has_readd_lifecycle(assertion)
            ):
                raise SemanticDesignBridgeError(
                    f"{clarification_id} is bound to unrelated assertion {assertion_id}; "
                    "the assertion must express filled -> delete -> re-add -> empty"
                )
            bound_kinds = clarification_binding_clause_kinds.get(
                (clarification_id, assertion_id),
                set(),
            )
            if not {"condition", "action", "oracle"}.issubset(bound_kinds):
                raise SemanticDesignBridgeError(
                    f"{clarification_id} lifecycle binding must cover condition, action "
                    "and oracle clauses"
                )
            lifecycle_clarification_assertions.add(assertion_id)

    obligations = design.get("obligations")
    if not isinstance(obligations, list):
        raise SemanticDesignBridgeError("semantic design obligations must be an array")
    obligation_ids = _unique_nonempty(
        [item.get("obligation_id", "") for item in obligations if isinstance(item, Mapping)],
        label="obligation_id values",
    )
    if len(obligation_ids) != len(obligations):
        raise SemanticDesignBridgeError("semantic design obligations must be objects")
    if set(obligation_ids) != set(assertion_owner_by_obligation):
        raise SemanticDesignBridgeError(
            "semantic design obligations must match assertion obligation bindings"
        )
    planned_tc_ids = _unique_nonempty(
        [item.get("planned_tc_id", "") for item in obligations],
        label="planned_tc_id values",
    )
    obligations_by_id = {
        str(item["obligation_id"]): item for item in obligations if isinstance(item, Mapping)
    }
    reset_lifecycle_bindings = design.get("reset_lifecycle_bindings")
    if not isinstance(reset_lifecycle_bindings, list):
        raise SemanticDesignBridgeError(
            "semantic design reset_lifecycle_bindings must be an array"
        )
    reset_lifecycle_obligation_ids = _unique_nonempty(
        [
            item.get("obligation_id", "")
            for item in reset_lifecycle_bindings
            if isinstance(item, Mapping)
        ],
        label="reset lifecycle obligation_id values",
    )
    if len(reset_lifecycle_obligation_ids) != len(reset_lifecycle_bindings):
        raise SemanticDesignBridgeError(
            "semantic design reset_lifecycle_bindings must be objects"
        )
    reset_lifecycle_by_obligation = {
        str(item["obligation_id"]): item
        for item in reset_lifecycle_bindings
        if isinstance(item, Mapping)
    }
    expected_reset_lifecycle_obligation_ids = {
        obligation_id
        for obligation_id, obligation in obligations_by_id.items()
        if _state_change_class(obligation) or _lifecycle_readd_class(obligation)
    }
    actual_reset_lifecycle_obligation_ids = set(reset_lifecycle_by_obligation)
    missing_reset_lifecycle_bindings = sorted(
        expected_reset_lifecycle_obligation_ids
        - actual_reset_lifecycle_obligation_ids
    )
    foreign_reset_lifecycle_bindings = sorted(
        actual_reset_lifecycle_obligation_ids
        - expected_reset_lifecycle_obligation_ids
    )
    if missing_reset_lifecycle_bindings or foreign_reset_lifecycle_bindings:
        raise SemanticDesignBridgeError(
            "reset_lifecycle_bindings must match reset/re-add obligations exactly; "
            f"missing={missing_reset_lifecycle_bindings}, "
            f"foreign={foreign_reset_lifecycle_bindings}"
        )
    context_package_id = context.get("package_id")
    if not isinstance(context_package_id, str) or not context_package_id.strip():
        raise SemanticDesignBridgeError(
            "ready semantic design requires a non-empty context.package_id"
        )
    state_change_rows: set[str] = set()
    state_change_assertion_ids: set[str] = set()
    lifecycle_rows: set[str] = set()
    lifecycle_obligation_assertion_ids: set[str] = set()
    for obligation_id, obligation in obligations_by_id.items():
        owner = assertion_owner_by_obligation[obligation_id]
        if obligation.get("linked_atom_id") != owner.get("atom_id"):
            raise SemanticDesignBridgeError(
                f"{obligation_id} linked_atom_id does not match its assertion"
            )
        if obligation.get("source_property_id") != owner.get("source_property_id"):
            raise SemanticDesignBridgeError(
                f"{obligation_id} source_property_id does not match its assertion"
            )
        package_id = obligation.get("package_id")
        if package_id != context_package_id:
            raise SemanticDesignBridgeError(
                f"{obligation_id} package_id must equal context.package_id exactly"
            )
        if obligation.get("design_dimension") not in APPLICABILITY_DIMENSIONS:
            raise SemanticDesignBridgeError(
                f"{obligation_id} design_dimension must use one canonical "
                "applicability dimension"
            )
        scope_obligation_ids = obligation.get("scope_obligation_ids")
        if not isinstance(scope_obligation_ids, list) or len(scope_obligation_ids) != len(
            set(map(str, scope_obligation_ids))
        ):
            raise SemanticDesignBridgeError(
                f"{obligation_id} scope_obligation_ids must be duplicate-free"
            )
        direct_calibration_candidate = (
            "candidate-ui-calibration"
            in str(obligation.get("review_notes", "")).casefold()
            and not scope_obligation_ids
        )
        if direct_calibration_candidate:
            normalized_oracle_source = re.sub(
                r"[^a-zа-яё0-9]+",
                "_",
                str(obligation.get("oracle_source", "")).casefold(),
            ).strip("_")
            oracle_text = " ".join(
                map(str, owner.get("oracle_clauses", []))
            ).casefold()
            if (
                obligation.get("check_type") not in {"negative", "boundary"}
                or normalized_oracle_source not in UNKNOWN_ORACLE_SOURCE_SENTINELS
                or not any(
                    marker in oracle_text
                    for marker in ("калибров", "calibration")
                )
            ):
                raise SemanticDesignBridgeError(
                    f"{obligation_id} direct calibration marker requires a boundary/"
                    "negative check, unknown oracle source and an explicit calibration "
                    "oracle clause"
                )
        is_reset = _state_change_class(obligation)
        is_lifecycle_readd = _lifecycle_readd_class(obligation)
        if is_reset or is_lifecycle_readd:
            lifecycle_binding = reset_lifecycle_by_obligation[obligation_id]
            expected_binding_kind = (
                "readd-after-delete" if is_lifecycle_readd else "reset"
            )
            if lifecycle_binding.get("binding_kind") != expected_binding_kind:
                raise SemanticDesignBridgeError(
                    f"{obligation_id} reset lifecycle binding_kind must equal "
                    f"{expected_binding_kind}"
                )
            owner_state_rows = _assertion_state_change_evidence_rows(owner)
            owner_lifecycle_rows = _assertion_lifecycle_evidence_rows(owner)
            owner_assertion_id = str(owner.get("assertion_id", ""))
            if is_reset and not is_lifecycle_readd and not owner_state_rows:
                raise SemanticDesignBridgeError(
                    f"{obligation_id} reset requires exact clear/reset assertion evidence"
                )
            condition_index = lifecycle_binding.get("initial_condition_index")
            if (
                not isinstance(condition_index, int)
                or isinstance(condition_index, bool)
                or condition_index < 0
            ):
                raise SemanticDesignBridgeError(
                    f"{obligation_id} reset requires a non-negative integer "
                    "initial_condition_index"
                )
            conditions = owner.get("condition_clauses", [])
            if condition_index >= len(conditions):
                raise SemanticDesignBridgeError(
                    f"{obligation_id} reset initial condition index is out of range"
                )
            if (
                lifecycle_binding.get("state_relation")
                != "different-from-captured-initial"
            ):
                raise SemanticDesignBridgeError(
                    f"{obligation_id} reset state relation is incomplete"
                )
            for key in ("changed_state_setup", "pre_action_state_oracle"):
                value = lifecycle_binding.get(key)
                if not isinstance(value, str) or len(value.strip()) < 12:
                    raise SemanticDesignBridgeError(
                        f"{obligation_id} reset requires substantive {key}"
                    )
            if is_lifecycle_readd:
                if (
                    owner_assertion_id not in lifecycle_clarification_assertions
                    and not owner_lifecycle_rows
                ):
                    raise SemanticDesignBridgeError(
                        f"{obligation_id} re-add lifecycle lacks exact source or typed "
                        "clarification evidence"
                    )
                if not _assertion_has_readd_lifecycle(owner):
                    raise SemanticDesignBridgeError(
                        f"{obligation_id} lifecycle assertion must express filled -> "
                        "delete -> re-add -> empty"
                    )
                if not _text_has_filled_prestate(conditions[condition_index]):
                    raise SemanticDesignBridgeError(
                        f"{obligation_id} lifecycle initial condition must capture a "
                        "filled prestate"
                    )
                if not _text_has_delete_then_readd(
                    lifecycle_binding.get("changed_state_setup", "")
                ) or not _text_has_new_instance(
                    lifecycle_binding.get("changed_state_setup", "")
                ):
                    raise SemanticDesignBridgeError(
                        f"{obligation_id} lifecycle setup must delete the filled block "
                        "and then add a new block"
                    )
                lifecycle_rows.update(owner_lifecycle_rows)
                lifecycle_obligation_assertion_ids.add(owner_assertion_id)
            if is_reset:
                state_change_rows.update(owner_state_rows)
                state_change_assertion_ids.add(owner_assertion_id)

    expected_field_properties = _typed_field_property_registry(
        context,
        eligible_row_ids=eligible_row_ids,
    )
    for expected_property in expected_field_properties:
        property_id = str(expected_property["source_property_id"])
        row_id = str(expected_property["source_row_id"])
        matching_assertions = [
            assertion
            for assertion in assertions
            if assertion.get("semantic_disposition") == "testable"
            and assertion.get("source_property_id") == property_id
            and assertion_row_by_id.get(str(assertion.get("assertion_id", "")))
            == row_id
        ]
        if len(matching_assertions) != 1:
            raise SemanticDesignBridgeError(
                f"{property_id} must map to one distinct testable assertion on {row_id}"
            )
        owner = matching_assertions[0]
        property_obligation_ids = list(map(str, owner.get("obligation_ids", [])))
        if len(property_obligation_ids) != 1:
            raise SemanticDesignBridgeError(
                f"{property_id} must map to one atomic ASSERT/ATOM/OBL/TC chain"
            )
        obligation = obligations_by_id[property_obligation_ids[0]]
        if (
            obligation.get("source_property_id") != property_id
            or obligation.get("property_type")
            != expected_property["property_type"]
        ):
            raise SemanticDesignBridgeError(
                f"{property_id} obligation property binding is invalid"
            )
        exact_anchor = str(expected_property["source_value"])
        if not any(
            evidence_row_id == row_id and exact_anchor in evidence_fragment
            for evidence_row_id, evidence_fragment in _assertion_literal_evidence(owner)
        ):
            raise SemanticDesignBridgeError(
                f"{property_id} assertion lacks its exact typed-cell source value"
            )
    missing_lifecycle_assertions = (
        lifecycle_clarification_assertions - lifecycle_obligation_assertion_ids
    )
    if missing_lifecycle_assertions:
        raise SemanticDesignBridgeError(
            "lifecycle clarification requires a separate guarded OBL/TC for assertions: "
            + ", ".join(sorted(missing_lifecycle_assertions))
        )
    for assertion in assertions:
        if (
            assertion.get("semantic_disposition") == "testable"
            and _assertion_state_change_evidence_rows(assertion)
            and str(assertion.get("assertion_id", ""))
            not in state_change_assertion_ids
        ):
            raise SemanticDesignBridgeError(
                f"{assertion.get('assertion_id')} state-change evidence requires its own "
                "changed-prestate obligation"
            )
    dependency_bindings = design.get("dependency_bindings")
    if not isinstance(dependency_bindings, list):
        raise SemanticDesignBridgeError("dependency_bindings must be an array")
    boundary_dependencies = boundary.get("dependencies")
    if not isinstance(boundary_dependencies, list):
        raise SemanticDesignBridgeError("authoritative dependencies must be an array")
    if len(dependency_bindings) != len(boundary_dependencies):
        raise SemanticDesignBridgeError(
            "dependency_bindings must cover authoritative dependencies exactly"
        )
    context_rows_by_id = {
        str(row.get("source_row_id", "")): row
        for row in context.get("source_rows", [])
        if isinstance(row, Mapping)
    }
    copied_dependency_fields = (
        "dependency_id",
        "kind",
        "name",
        "source_row_ids",
        "resolution",
        "target_source_row_ids",
        "exact_source_fragments",
        "gap_ids",
        "blocking",
        "rationale",
    )
    external_dynamic_obligation_ids: set[str] = set()
    observation_gaps = [
        item
        for item in boundary.get("gaps", [])
        if isinstance(item, Mapping)
        and item.get("gap_type") == "missing-observation-interface"
        and item.get("blocking") is False
        and item.get("downstream_handling") == "carry-to-source-model"
    ]
    for index, (authoritative, binding) in enumerate(
        zip(boundary_dependencies, dependency_bindings, strict=True)
    ):
        if not isinstance(authoritative, Mapping) or not isinstance(binding, Mapping):
            raise SemanticDesignBridgeError(
                f"dependency_bindings[{index}] must be an object"
            )
        dependency_id = str(authoritative.get("dependency_id", ""))
        for field in copied_dependency_fields:
            if binding.get(field) != authoritative.get(field):
                raise SemanticDesignBridgeError(
                    f"{dependency_id} {field} drifted from authoritative dependency"
                )
        linked_assertion_ids = binding.get("linked_assertion_ids")
        linked_atom_ids = binding.get("linked_atom_ids")
        linked_obligation_ids = binding.get("linked_obligation_ids")
        if not all(
            isinstance(value, list)
            for value in (
                linked_assertion_ids,
                linked_atom_ids,
                linked_obligation_ids,
            )
        ):
            raise SemanticDesignBridgeError(
                f"{dependency_id} semantic links must be arrays"
            )
        assert isinstance(linked_assertion_ids, list)
        assert isinstance(linked_atom_ids, list)
        assert isinstance(linked_obligation_ids, list)
        mapping_rationale = binding.get("mapping_rationale")
        if (
            not isinstance(mapping_rationale, str)
            or len(mapping_rationale.strip()) < 12
            or mapping_rationale == "none_required"
        ):
            raise SemanticDesignBridgeError(
                f"{dependency_id} requires a substantive mapping_rationale"
            )
        resolution = authoritative.get("resolution")
        if binding.get("semantic_disposition") == "not-applicable":
            if resolution != "scope-excluded" or any(
                (linked_assertion_ids, linked_atom_ids, linked_obligation_ids)
            ):
                raise SemanticDesignBridgeError(
                    f"{dependency_id} not-applicable mapping is allowed only for "
                    "scope-excluded dependency without executable links"
                )
            dependency_name = str(authoritative.get("name", "")).strip()
            exact_fragments = [
                str(fragment).strip()
                for fragment in authoritative.get("exact_source_fragments", [])
                if str(fragment).strip()
            ]
            for source_row_id in map(str, authoritative.get("source_row_ids", [])):
                if boundary_disposition_by_row.get(source_row_id) != "included":
                    continue
                sibling_candidates = [
                    assertion
                    for assertion_id, assertion in assertion_by_id.items()
                    if assertion_row_by_id.get(assertion_id) == source_row_id
                    and assertion.get("semantic_disposition") == "not-applicable"
                    and str(assertion.get("field_or_block", "")).strip().casefold()
                    == dependency_name.casefold()
                ]
                if len(sibling_candidates) != 1:
                    raise SemanticDesignBridgeError(
                        f"{dependency_id} partial scope exclusion on {source_row_id} "
                        "requires exactly one code-less N/A sibling whose field_or_block "
                        "equals the dependency name"
                    )
                sibling = sibling_candidates[0]
                canonical_statement = str(
                    sibling.get("canonical_statement", "")
                ).casefold()
                if sibling.get("requirement_codes") or not any(
                    fragment.casefold() in canonical_statement
                    for fragment in exact_fragments
                ):
                    raise SemanticDesignBridgeError(
                        f"{dependency_id} N/A sibling on {source_row_id} must be code-less "
                        "and preserve an exact dependency fragment in canonical_statement"
                    )
                contaminated_testable_labels = [
                    str(assertion.get("assertion_id", ""))
                    for assertion_id, assertion in assertion_by_id.items()
                    if assertion_row_by_id.get(assertion_id) == source_row_id
                    and assertion.get("semantic_disposition") == "testable"
                    and contains_token_bounded_source_fragment(
                        normalize_exact_source_text(
                            str(assertion.get("field_or_block", ""))
                        ),
                        normalize_exact_source_text(dependency_name),
                    )
                ]
                if contaminated_testable_labels:
                    raise SemanticDesignBridgeError(
                        f"{dependency_id} scope-excluded name leaked into testable "
                        "field_or_block: " + ", ".join(contaminated_testable_labels)
                    )
            continue
        if binding.get("semantic_disposition") == "gap-bound":
            if resolution == "scope-excluded" or linked_obligation_ids:
                raise SemanticDesignBridgeError(
                    f"{dependency_id} gap-bound mapping requires an in-scope "
                    "dependency and no executable obligations"
                )
            linked_assertion_ids = _unique_nonempty(
                linked_assertion_ids,
                label=f"{dependency_id} linked_assertion_ids",
            )
            linked_atom_ids = _unique_nonempty(
                linked_atom_ids,
                label=f"{dependency_id} linked_atom_ids",
            )
            if not linked_assertion_ids:
                raise SemanticDesignBridgeError(
                    f"{dependency_id} gap-bound dependency requires an N/A assertion chain"
                )
            dependency_source_rows = set(map(str, authoritative.get("source_row_ids", [])))
            linked_gap_ids = set(map(str, authoritative.get("gap_ids", [])))
            linked_observation_gaps = [
                gap
                for gap in observation_gaps
                if str(gap.get("gap_id", "")) in linked_gap_ids
            ]
            if (
                not dependency_source_rows
                or not linked_gap_ids
                or len(linked_observation_gaps) != len(linked_gap_ids)
            ):
                raise SemanticDesignBridgeError(
                    f"{dependency_id} gap-bound mapping lacks an authoritative "
                    "missing-observation-interface dependency gap"
                )
            linked_gap_assertions: list[Mapping[str, Any]] = []
            for assertion_id in linked_assertion_ids:
                assertion = assertion_by_id.get(assertion_id)
                if (
                    assertion is None
                    or assertion.get("semantic_disposition") != "not-applicable"
                    or assertion_row_by_id.get(assertion_id)
                    not in dependency_source_rows
                ):
                    raise SemanticDesignBridgeError(
                        f"{dependency_id} gap-bound mapping references an unknown, "
                        f"testable or unrelated assertion {assertion_id}"
                    )
                linked_gap_assertions.append(assertion)
            expected_atoms = [
                str(assertion.get("atom_id", ""))
                for assertion in linked_gap_assertions
            ]
            if linked_atom_ids != expected_atoms:
                raise SemanticDesignBridgeError(
                    f"{dependency_id} gap-bound mapping must preserve ASSERT->ATOM links"
                )
            gap_fragments = {
                str(fragment)
                for gap in linked_observation_gaps
                if dependency_source_rows.intersection(
                    map(str, gap.get("source_row_ids", []))
                )
                for fragment in gap.get("exact_source_fragments", [])
            }
            missing_fragments = [
                str(fragment)
                for fragment in authoritative.get("exact_source_fragments", [])
                if not any(
                    str(fragment) in gap_fragment
                    for gap_fragment in gap_fragments
                )
            ]
            if missing_fragments:
                raise SemanticDesignBridgeError(
                    f"{dependency_id} gap-bound evidence does not cover dependency "
                    f"fragments: {missing_fragments}"
                )
            continue
        if binding.get("semantic_disposition") != "bound" or resolution == "scope-excluded":
            raise SemanticDesignBridgeError(
                f"{dependency_id} resolved in-scope dependency must be bound"
            )
        linked_assertion_ids = _unique_nonempty(
            linked_assertion_ids,
            label=f"{dependency_id} linked_assertion_ids",
        )
        if not linked_assertion_ids:
            raise SemanticDesignBridgeError(
                f"{dependency_id} bound dependency requires a testable assertion chain"
            )
        linked_assertions: list[Mapping[str, Any]] = []
        dependency_source_rows = {
            *map(str, authoritative.get("source_row_ids", [])),
        }
        dependency_rows = {
            *dependency_source_rows,
            *map(str, authoritative.get("target_source_row_ids", [])),
        }
        dependency_fragments = list(
            map(str, authoritative.get("exact_source_fragments", []))
        )
        covered_dependency_fragments: set[str] = set()
        covered_dependency_rows: set[str] = set()
        for assertion_id in linked_assertion_ids:
            assertion = assertion_by_id.get(assertion_id)
            if assertion is None or assertion.get("semantic_disposition") != "testable":
                raise SemanticDesignBridgeError(
                    f"{dependency_id} references unknown or non-testable assertion "
                    f"{assertion_id}"
                )
            supporting_rows = {
                str(item.get("source_row_id", ""))
                for item in assertion.get("supporting_source_bindings", [])
                if isinstance(item, Mapping)
            }
            assertion_relation_rows = {
                assertion_row_by_id[assertion_id],
                *supporting_rows,
            }
            related_rows = dependency_rows.intersection(assertion_relation_rows)
            if not related_rows:
                raise SemanticDesignBridgeError(
                    f"{dependency_id} assertion {assertion_id} has no source relation "
                    "to the dependency"
                )
            covered_dependency_rows.update(related_rows)
            assertion_dependency_fragments = {
                dependency_fragment
                for evidence_row_id, evidence_fragment in _assertion_literal_evidence(
                    assertion
                )
                if evidence_row_id in dependency_source_rows
                for dependency_fragment in dependency_fragments
                if dependency_fragment in evidence_fragment
            }
            if not assertion_dependency_fragments:
                raise SemanticDesignBridgeError(
                    f"{dependency_id} assertion {assertion_id} has no exact dependency "
                    "fragment evidence"
                )
            covered_dependency_fragments.update(assertion_dependency_fragments)
            linked_assertions.append(assertion)
        if covered_dependency_fragments != set(dependency_fragments):
            missing_fragments = [
                fragment
                for fragment in dependency_fragments
                if fragment not in covered_dependency_fragments
            ]
            raise SemanticDesignBridgeError(
                f"{dependency_id} linked assertion evidence does not cover every exact "
                f"dependency fragment: {missing_fragments}"
            )
        relation_required = any(
            context_rows_by_id.get(row_id, {}).get("context_relation_required")
            is True
            for row_id in dependency_source_rows
        )
        required_target_rows = set(
            map(str, authoritative.get("target_source_row_ids", []))
        )
        if relation_required and not required_target_rows.issubset(
            covered_dependency_rows
        ):
            raise SemanticDesignBridgeError(
                f"{dependency_id} context relation does not cover target rows: "
                + ", ".join(
                    sorted(required_target_rows - covered_dependency_rows)
                )
            )
        expected_atoms = [str(item.get("atom_id", "")) for item in linked_assertions]
        expected_obligations = [
            str(obligation_id)
            for item in linked_assertions
            for obligation_id in item.get("obligation_ids", [])
        ]
        if linked_atom_ids != expected_atoms or linked_obligation_ids != expected_obligations:
            raise SemanticDesignBridgeError(
                f"{dependency_id} must preserve the full ASSERT->ATOM->OBL chain"
            )
        if any(obligation_id not in obligations_by_id for obligation_id in expected_obligations):
            raise SemanticDesignBridgeError(
                f"{dependency_id} references an unknown semantic obligation"
            )
        if resolution == "external-dynamic":
            external_dynamic_obligation_ids.update(expected_obligations)

    fully_gapped_rows = _fully_gapped_observation_rows(boundary)
    required_state_rows = {
        str(row["source_row_id"])
        for row in eligible_rows
        if _row_requires_state_change(row)
        and str(row["source_row_id"]) not in fully_gapped_rows
    }
    if not required_state_rows.issubset(state_change_rows):
        raise SemanticDesignBridgeError(
            "clear/reset source rows require an explicit changed-prestate obligation: "
            + ", ".join(sorted(required_state_rows - state_change_rows))
        )
    required_lifecycle_rows = {
        str(row["source_row_id"])
        for row in eligible_rows
        if _text_requires_readd_lifecycle(row.get("bounded_source_text", ""))
        and str(row["source_row_id"]) not in fully_gapped_rows
    }
    if not required_lifecycle_rows.issubset(lifecycle_rows):
        raise SemanticDesignBridgeError(
            "re-add lifecycle source rows require a separate guarded obligation: "
            + ", ".join(sorted(required_lifecycle_rows - lifecycle_rows))
        )

    dictionaries = design.get("dictionaries")
    if not isinstance(dictionaries, list):
        raise SemanticDesignBridgeError("semantic design dictionaries must be an array")
    dictionary_ids = _unique_nonempty(
        [item.get("dictionary_id", "") for item in dictionaries if isinstance(item, Mapping)],
        label="dictionary_id values",
    )
    if len(dictionary_ids) != len(dictionaries):
        raise SemanticDesignBridgeError("semantic design dictionaries must be objects")
    expected_ids = [f"DICT-{index:03d}" for index in range(1, len(dictionaries) + 1)]
    if dictionary_ids != expected_ids:
        raise SemanticDesignBridgeError(
            "dictionary ids must be sequential in first-source occurrence order"
        )
    external_dictionary_names = set(
        external_dynamic_dictionary_bindings(context)
    )
    required_dictionary_references = [
        item
        for item in _dictionary_references(eligible_rows)
        if normalize_entity(str(item["dictionary_name"]))
        not in external_dictionary_names
    ]
    required_dictionary_names = [
        str(item["dictionary_name"]) for item in required_dictionary_references
    ]
    actual_names = [str(item.get("dictionary_name", "")) for item in dictionaries]
    if len(actual_names) != len(required_dictionary_names) or {
        item.casefold() for item in actual_names
    } != {item.casefold() for item in required_dictionary_names}:
        raise SemanticDesignBridgeError(
            "semantic design dictionary set does not match bounded source references"
        )
    registered_paths = {
        str(item.get("path"))
        for item in context.get("sources", [])
        if isinstance(item, Mapping)
    }
    dictionary_source_rows_by_id: dict[str, set[str]] = {}
    for item, reference in zip(
        dictionaries,
        required_dictionary_references,
        strict=True,
    ):
        assert isinstance(item, Mapping)
        dictionary_id = str(item["dictionary_id"])
        if item.get("extraction_status") != "extracted":
            raise SemanticDesignBridgeError(
                f"{dictionary_id} must be fully extracted before release design"
            )
        active_values = item.get("active_values")
        if not isinstance(active_values, list) or not active_values:
            raise SemanticDesignBridgeError(f"{dictionary_id} active values are required")
        source_row_ids = item.get("source_row_ids")
        if not isinstance(source_row_ids, list) or not source_row_ids:
            raise SemanticDesignBridgeError(f"{dictionary_id} source rows are required")
        if source_row_ids != reference["source_row_ids"] or any(
            str(row_id) not in eligible_row_ids for row_id in source_row_ids
        ):
            raise SemanticDesignBridgeError(
                f"{dictionary_id} source rows must equal eligible bounded references"
            )
        dictionary_source_rows_by_id[dictionary_id] = set(map(str, source_row_ids))
        if item.get("source_file") not in registered_paths:
            raise SemanticDesignBridgeError(
                f"{dictionary_id} source_file is not registered in context.sources"
            )
        declared_values = _declared_dictionary_values(
            context,
            str(item.get("dictionary_name", "")),
        )
        archived_values = item.get("archived_values")
        if declared_values is not None:
            expected_active, expected_archived = declared_values
            if active_values != expected_active or archived_values != expected_archived:
                raise SemanticDesignBridgeError(
                    f"{dictionary_id} values drifted from prepared dictionary inventory"
                )
        else:
            inline_values = _closed_inline_dictionary_values(
                name=str(item.get("dictionary_name", "")),
                row_ids=list(map(str, source_row_ids)),
                rows_by_id=rows_by_id,
            )
            if inline_values is None:
                raise SemanticDesignBridgeError(
                    f"{dictionary_id} requires a prepared inventory or a closed inline list"
                )
            if active_values != inline_values or archived_values != []:
                raise SemanticDesignBridgeError(
                    f"{dictionary_id} must contain all and only closed inline values"
                )
    known_dictionary_ids = set(dictionary_ids)
    covered_dictionary_rows: dict[str, set[str]] = {
        dictionary_id: set() for dictionary_id in dictionary_ids
    }
    for obligation_id, obligation in obligations_by_id.items():
        refs = obligation.get("dictionary_refs")
        if (
            not isinstance(refs, list)
            or len(refs) != len(set(map(str, refs)))
            or set(map(str, refs)) - known_dictionary_ids
        ):
            raise SemanticDesignBridgeError(
                f"{obligation_id} dictionary refs contain unknown or duplicate ids"
            )
        if refs and obligation.get("dictionary_coverage") == "none_required":
            raise SemanticDesignBridgeError(
                f"{obligation_id} dictionary coverage must be explicit"
            )
        if not refs and obligation.get("dictionary_coverage") != "none_required":
            raise SemanticDesignBridgeError(
                f"{obligation_id} has dictionary coverage without dictionary refs"
            )
        if obligation_id in external_dynamic_obligation_ids and (
            refs != [] or obligation.get("dictionary_coverage") != "none_required"
        ):
            raise SemanticDesignBridgeError(
                f"{obligation_id} external dynamic dictionary must stay dependency-only"
            )
        owner = assertion_owner_by_obligation[obligation_id]
        assertion_rows = _assertion_evidence_rows(
            owner,
            primary_row_id=row_by_obligation[obligation_id],
        )
        for dictionary_id in map(str, refs):
            linked_rows = (
                dictionary_source_rows_by_id[dictionary_id] & assertion_rows
            )
            if not linked_rows:
                raise SemanticDesignBridgeError(
                    f"{obligation_id} dictionary {dictionary_id} is outside its "
                    "ASSERT->ATOM->OBL evidence chain"
                )
            covered_dictionary_rows[dictionary_id].update(linked_rows)
    referenced_dictionary_ids = {
        str(ref)
        for obligation in obligations_by_id.values()
        for ref in obligation.get("dictionary_refs", [])
    }
    if referenced_dictionary_ids != known_dictionary_ids:
        raise SemanticDesignBridgeError(
            "every extracted dictionary must be covered by at least one obligation"
        )
    for dictionary_id, source_rows in dictionary_source_rows_by_id.items():
        if covered_dictionary_rows[dictionary_id] != source_rows:
            raise SemanticDesignBridgeError(
                f"{dictionary_id} obligations do not cover every dictionary source row"
            )

    code_registry = {
        str(item.get("source_row_id", "")): list(
            map(str, item.get("requirement_codes", []))
        )
        for item in boundary_decisions
        if isinstance(item, Mapping)
    }
    expected_signal_registry = _source_signal_registry(eligible_rows, code_registry)
    oracle_scope_ids: set[str] = set()
    oracle_obligation_owner: dict[str, str] = {}
    executable_oracle_statuses = set(EXECUTABLE_ORACLE_STATUSES)
    expected_scope_ids_by_obligation: dict[str, list[str]] = {
        obligation_id: [] for obligation_id in obligations_by_id
    }
    for collection_name, registry_name, prefix, statement_field in (
        ("negative_oracles", "negative", "SO-NEG-", "source_statement"),
        (
            "requiredness_oracles",
            "requiredness",
            "SO-REQ-",
            "requiredness_source",
        ),
    ):
        collection = design.get(collection_name)
        if not isinstance(collection, list):
            raise SemanticDesignBridgeError(f"{collection_name} must be an array")
        expected_signals = expected_signal_registry[registry_name]
        if len(collection) != len(expected_signals):
            raise SemanticDesignBridgeError(
                f"{collection_name} must cover every eligible source signal exactly"
            )
        for item, expected_signal in zip(collection, expected_signals, strict=True):
            if not isinstance(item, Mapping):
                raise SemanticDesignBridgeError(f"{collection_name} entries must be objects")
            signal_id = str(item.get("signal_id", ""))
            for field in (
                "signal_id",
                "scope_obligation_id",
                "source_row_id",
                "source_ref",
                "field_or_block",
                "requirement_codes",
                "restriction_type",
            ):
                if item.get(field) != expected_signal[field]:
                    raise SemanticDesignBridgeError(
                        f"{signal_id or collection_name} {field} drifted from the "
                        "typed source-signal registry"
                    )
            signal_row_id = str(expected_signal["source_row_id"])
            source_statement = item.get(statement_field)
            _literal_fragment(
                rows_by_id,
                signal_row_id,
                source_statement,
                label=f"{signal_id} source_statement",
            )
            if str(expected_signal["literal_anchor"]) not in str(source_statement):
                raise SemanticDesignBridgeError(
                    f"{signal_id} source_statement does not contain its exact signal anchor"
                )
            if item.get("source_ref") != rows_by_id[signal_row_id].get("source_ref"):
                raise SemanticDesignBridgeError(
                    f"{signal_id} source_ref drifted from its bounded source row"
                )
            scope_id = str(item.get("scope_obligation_id", ""))
            expected_scope_id = "SO-" + signal_id.removeprefix("SIG-")
            if (
                scope_id != expected_scope_id
                or not scope_id.startswith(prefix)
                or scope_id in oracle_scope_ids
            ):
                raise SemanticDesignBridgeError(
                    f"{collection_name} scope obligation ids must preserve canonical "
                    "signal identity and order"
                )
            oracle_scope_ids.add(scope_id)
            obligation_id = str(item.get("linked_obligation_id", ""))
            obligation = obligations_by_id.get(obligation_id)
            if obligation is None or item.get("linked_atom_id") != obligation.get(
                "linked_atom_id"
            ):
                raise SemanticDesignBridgeError(
                    f"{scope_id} is not linked to one known ATOM/OBL chain"
                )
            previous_scope_id = oracle_obligation_owner.get(obligation_id)
            if previous_scope_id is not None:
                raise SemanticDesignBridgeError(
                    f"{scope_id} and {previous_scope_id} collapse independent oracle "
                    f"signals into {obligation_id}"
                )
            oracle_obligation_owner[obligation_id] = scope_id
            owner = assertion_owner_by_obligation[obligation_id]
            signal_codes = set(map(str, expected_signal["requirement_codes"]))
            owner_codes = set(map(str, owner.get("requirement_codes", [])))
            typed_cell_signal = (
                expected_signal.get("source_binding") == "typed-xhtml-cell"
            )
            if (
                not signal_codes
                and len(code_registry.get(signal_row_id, [])) > 1
                and not typed_cell_signal
            ):
                raise SemanticDesignBridgeError(
                    f"{scope_id} has an ambiguous requirement-code assignment on "
                    f"multi-code row {signal_row_id}"
                )
            if typed_cell_signal:
                expected_property_id = expected_signal.get("source_property_id")
                if (
                    owner.get("source_property_id") != expected_property_id
                    or obligation.get("source_property_id") != expected_property_id
                    or obligation.get("property_type") != "requiredness"
                ):
                    raise SemanticDesignBridgeError(
                        f"{scope_id} is not bound to its exact typed XHTML cell property"
                    )
            if signal_codes and not signal_codes.issubset(owner_codes):
                raise SemanticDesignBridgeError(
                    f"{scope_id} requirement codes are not owned by its linked assertion"
                )
            allowed_signal_rows = {
                row_by_obligation[obligation_id],
                *(
                    str(binding.get("source_row_id", ""))
                    for binding in owner.get("supporting_source_bindings", [])
                    if isinstance(binding, Mapping)
                ),
            }
            if signal_row_id not in allowed_signal_rows:
                raise SemanticDesignBridgeError(
                    f"{scope_id} source row is outside its ASSERT->ATOM->OBL evidence chain"
                )
            restriction_type = str(expected_signal["restriction_type"])
            binary_signal_default = (
                expected_signal.get("value_semantics")
                == "binary-logical-default"
                and bool(str(expected_signal.get("default_value", "")))
            )
            exact_anchor = str(expected_signal["literal_anchor"])
            if not any(
                evidence_row_id == signal_row_id
                and exact_anchor in evidence_fragment
                for evidence_row_id, evidence_fragment in _assertion_literal_evidence(
                    owner
                )
            ):
                raise SemanticDesignBridgeError(
                    f"{scope_id} requires exact signal evidence in its owning assertion"
                )
            if restriction_type == "optionality":
                if list(map(str, owner.get("obligation_ids", []))) != [obligation_id]:
                    raise SemanticDesignBridgeError(
                        f"{scope_id} optionality requires its own ASSERT/ATOM/OBL/TC"
                    )
            decision = item.get("decision")
            oracle_status = item.get("oracle_status")
            if decision == "executable_tc":
                if oracle_status not in executable_oracle_statuses:
                    raise SemanticDesignBridgeError(
                        f"{scope_id} executable oracle lacks explicit backed status"
                    )
                if registry_name == "negative":
                    if item.get("observable_oracle_found") != "yes":
                        raise SemanticDesignBridgeError(
                            f"{scope_id} executable negative check lacks an observable oracle"
                        )
                    allowed_check_types = {"negative", "boundary"}
                elif restriction_type == "requiredness":
                    if (
                        item.get("marker_oracle_found") != "yes"
                        and item.get("empty_value_oracle_found") != "yes"
                    ):
                        raise SemanticDesignBridgeError(
                            f"{scope_id} executable requiredness check lacks a marker or "
                            "empty-value oracle"
                        )
                    allowed_check_types = {"negative", "boundary"}
                    if _is_conditional_requiredness_signal(expected_signal):
                        allowed_check_types.add("dependency")
                else:
                    if (
                        not binary_signal_default
                        and item.get("empty_value_oracle_found") != "yes"
                    ):
                        raise SemanticDesignBridgeError(
                            f"{scope_id} executable optionality check must prove that an "
                            "empty value is accepted"
                        )
                    allowed_check_types = {"positive", "scenario", "boundary"}
                if obligation.get("check_type") not in allowed_check_types:
                    raise SemanticDesignBridgeError(
                        f"{scope_id} oracle is linked to incompatible obligation "
                        f"check_type={obligation.get('check_type')}"
                    )
                if item.get("planned_tc_or_gap") != obligation.get("planned_tc_id"):
                    raise SemanticDesignBridgeError(
                        f"{scope_id} executable mapping must use its planned TC"
                    )
            elif decision == "candidate_tc_required":
                if oracle_status != "ui-calibration-required":
                    raise SemanticDesignBridgeError(
                        f"{scope_id} calibration candidate requires explicit "
                        "oracle_status=ui-calibration-required"
                    )
                if item.get("planned_tc_or_gap") != f"candidate:{scope_id}":
                    raise SemanticDesignBridgeError(
                        f"{scope_id} calibration candidate marker is invalid"
                    )
                analyst_question = item.get("analyst_question")
                if (
                    not isinstance(analyst_question, str)
                    or len(analyst_question.strip()) < 12
                    or not analyst_question.rstrip().endswith("?")
                ):
                    raise SemanticDesignBridgeError(
                        f"{scope_id} calibration candidate requires a specific question"
                    )
                handoff_rule = item.get("handoff_rule")
                if (
                    not isinstance(handoff_rule, str)
                    or len(handoff_rule.strip()) < 12
                    or handoff_rule == "none_required"
                ):
                    raise SemanticDesignBridgeError(
                        f"{scope_id} calibration candidate requires a substantive "
                        "handoff rule"
                    )
                calibration_notes = item.get("calibration_notes")
                if (
                    not isinstance(calibration_notes, str)
                    or "candidate-ui-calibration"
                    not in calibration_notes.casefold()
                ):
                    raise SemanticDesignBridgeError(
                        f"{scope_id} calibration candidate lacks the explicit "
                        "candidate-ui-calibration marker"
                    )
                normalized_oracle_source = re.sub(
                    r"[^a-zа-яё0-9]+",
                    "_",
                    str(item.get("oracle_source", "")).casefold(),
                ).strip("_")
                if normalized_oracle_source not in {
                    "not_found",
                    "not_observed",
                    "none_found",
                    "unknown_ui_reaction",
                    "не_найден",
                    "не_наблюдался",
                }:
                    raise SemanticDesignBridgeError(
                        f"{scope_id} calibration candidate must not invent an oracle source"
                    )
                candidate_gap_id = str(item.get("gap_id", ""))
                known_boundary_gap = any(
                    isinstance(gap, Mapping)
                    and gap.get("gap_id") == candidate_gap_id
                    and signal_row_id
                    in set(map(str, gap.get("source_row_ids", [])))
                    for gap in boundary.get("gaps", [])
                )
                known_clarification_gap = any(
                    record.get("gap_id") == candidate_gap_id
                    and (
                        bool(
                            signal_codes
                            & set(map(str, record.get("requirement_codes", [])))
                        )
                        or signal_row_id
                        in set(map(str, record.get("source_row_ids", [])))
                    )
                    for record in clarification_by_id.values()
                )
                if (
                    candidate_gap_id != "none_required"
                    and not known_boundary_gap
                    and not known_clarification_gap
                ):
                    raise SemanticDesignBridgeError(
                        f"{scope_id} calibration candidate gap_id is not a known "
                        "parent GAP bound to this source signal"
                    )
                if registry_name == "negative":
                    invalid_value = item.get("representative_invalid_value")
                    if (
                        item.get("observable_oracle_found") not in {"no", "partial"}
                        or not isinstance(invalid_value, str)
                        or not invalid_value.strip()
                        or invalid_value.casefold()
                        in {"none_required", "not_derived", "unknown"}
                    ):
                        raise SemanticDesignBridgeError(
                            f"{scope_id} negative calibration candidate requires one "
                            "concrete invalid value and no invented observable reaction"
                        )
                    allowed_check_types = {"negative", "boundary"}
                elif restriction_type == "requiredness":
                    if (
                        item.get("marker_oracle_found")
                        not in {"no", "not_applicable"}
                        or item.get("empty_value_oracle_found") not in {"no", "partial"}
                    ):
                        raise SemanticDesignBridgeError(
                            f"{scope_id} requiredness candidate already has an executable "
                            "marker or empty-value oracle"
                        )
                    allowed_check_types = {"negative", "boundary"}
                    if _is_conditional_requiredness_signal(expected_signal):
                        allowed_check_types.add("dependency")
                else:
                    if (
                        item.get("marker_oracle_found")
                        not in {"no", "not_applicable"}
                        or item.get("empty_value_oracle_found") not in {"no", "partial"}
                    ):
                        raise SemanticDesignBridgeError(
                            f"{scope_id} optionality candidate already has an executable "
                            "empty-value oracle"
                        )
                    allowed_check_types = {"positive", "scenario", "boundary"}
                if obligation.get("check_type") not in allowed_check_types:
                    raise SemanticDesignBridgeError(
                        f"{scope_id} calibration candidate is linked to incompatible "
                        f"check_type={obligation.get('check_type')}"
                    )
                normalized_obligation_oracle_source = re.sub(
                    r"[^a-zа-яё0-9]+",
                    "_",
                    str(obligation.get("oracle_source", "")).casefold(),
                ).strip("_")
                if normalized_obligation_oracle_source not in {
                    "not_found",
                    "not_observed",
                    "none_found",
                    "unknown_ui_reaction",
                    "ui_calibration_required",
                    "не_найден",
                    "не_наблюдался",
                }:
                    raise SemanticDesignBridgeError(
                        f"{scope_id} candidate obligation must not claim a backed exact "
                        "oracle source"
                    )
                if registry_name == "requiredness":
                    if binary_signal_default:
                        default_value = str(expected_signal["default_value"])
                        if default_value not in str(obligation.get("test_data", "")):
                            raise SemanticDesignBridgeError(
                                f"{scope_id} binary requiredness/optionality candidate "
                                "must preserve "
                                "its source-backed default test value"
                            )
                    elif not (
                        _text_has_missing_required_value(
                            obligation.get("test_data", "")
                        )
                        or (
                            restriction_type == "optionality"
                            and expected_signal.get("control_semantics")
                            == "action-control"
                            and _text_has_no_action(
                                obligation.get("test_data", "")
                            )
                        )
                    ):
                        raise SemanticDesignBridgeError(
                            f"{scope_id} requiredness/optionality candidate requires an "
                            "explicit empty test value"
                        )
                if (
                    restriction_type != "optionality"
                    and not typed_cell_signal
                    and not any(
                    other_id != obligation_id
                    and other.get("source_property_id")
                    == obligation.get("source_property_id")
                    and other.get("check_type") == "positive"
                    for other_id, other in obligations_by_id.items()
                    )
                ):
                    raise SemanticDesignBridgeError(
                        f"{scope_id} calibration candidate must preserve a positive "
                        "allowed-class TC for the same source property"
                    )
            else:
                raise SemanticDesignBridgeError(
                    f"{scope_id} ready semantic design cannot publish a non-runnable "
                    f"oracle decision: {decision}"
                )
            expected_scope_ids_by_obligation[obligation_id].append(scope_id)
    for obligation_id, obligation in obligations_by_id.items():
        if obligation.get("scope_obligation_ids") != expected_scope_ids_by_obligation[
            obligation_id
        ]:
            raise SemanticDesignBridgeError(
                f"{obligation_id} scope_obligation_ids must equal linked oracle inventory "
                "ids in canonical order"
            )

    applicability = design.get("applicability")
    if not isinstance(applicability, list):
        raise SemanticDesignBridgeError("semantic design applicability must be an array")
    dimensions = [
        str(item.get("dimension", ""))
        for item in applicability
        if isinstance(item, Mapping)
    ]
    if dimensions != list(APPLICABILITY_DIMENSIONS):
        raise SemanticDesignBridgeError(
            "applicability must contain the exact 13 dimensions in canonical order"
        )
    testable_assertion_by_atom = {
        str(item.get("atom_id", "")): item
        for item in assertions
        if item.get("semantic_disposition") == "testable"
    }
    known_atoms = set(testable_assertion_by_atom)
    known_test_cases = set(planned_tc_ids)
    planned_tc_to_atom = {
        str(obligation.get("planned_tc_id", "")): str(
            obligation.get("linked_atom_id", "")
        )
        for obligation in obligations_by_id.values()
    }
    planned_tc_to_obligation = {
        str(obligation.get("planned_tc_id", "")): obligation
        for obligation in obligations_by_id.values()
    }
    for item in applicability:
        assert isinstance(item, Mapping)
        linked_atoms = item.get("linked_atoms")
        linked_tcs = item.get("linked_test_cases")
        if not isinstance(linked_atoms, list) or not isinstance(linked_tcs, list):
            raise SemanticDesignBridgeError("applicability links must be arrays")
        if (
            len(linked_atoms) != len(set(map(str, linked_atoms)))
            or len(linked_tcs) != len(set(map(str, linked_tcs)))
            or set(map(str, linked_atoms)) - known_atoms
            or set(map(str, linked_tcs)) - known_test_cases
        ):
            raise SemanticDesignBridgeError("applicability references unknown ATOM/TC")
        if item.get("applicable") == "yes" and (not linked_atoms or not linked_tcs):
            raise SemanticDesignBridgeError("applicable=yes requires ATOM and TC links")
        if item.get("applicable") == "no" and (linked_atoms or linked_tcs):
            raise SemanticDesignBridgeError("applicable=no cannot carry links")
        if item.get("applicable") == "yes":
            linked_atom_set = set(map(str, linked_atoms))
            linked_tc_atoms = {
                planned_tc_to_atom[str(test_case_id)]
                for test_case_id in linked_tcs
            }
            if not linked_tc_atoms.issubset(linked_atom_set) or not linked_atom_set.issubset(
                linked_tc_atoms
            ):
                raise SemanticDesignBridgeError(
                    "applicability ATOM and TC links must preserve their compiled chain"
                )
            dimension = str(item.get("dimension", ""))
            if dimension != "traceability":
                mismatched_test_cases = [
                    str(test_case_id)
                    for test_case_id in linked_tcs
                    if planned_tc_to_obligation[str(test_case_id)].get(
                        "design_dimension"
                    )
                    != dimension
                ]
                if mismatched_test_cases:
                    raise SemanticDesignBridgeError(
                        f"applicability dimension {dimension} is not exercised by linked "
                        f"test cases: {mismatched_test_cases}"
                    )

    applicability_by_dimension = {
        str(item["dimension"]): item for item in applicability
    }
    traceability_row = applicability_by_dimension["traceability"]
    if known_test_cases:
        if (
            traceability_row.get("applicable") != "yes"
            or set(map(str, traceability_row.get("linked_test_cases", [])))
            != known_test_cases
            or set(map(str, traceability_row.get("linked_atoms", [])))
            != set(planned_tc_to_atom.values())
        ):
            raise SemanticDesignBridgeError(
                "traceability applicability must cover every compiled ATOM/TC chain"
            )
    elif (
        known_atoms
        or planned_tc_to_atom
        or traceability_row.get("applicable") != "no"
        or traceability_row.get("linked_test_cases") != []
        or traceability_row.get("linked_atoms") != []
    ):
        raise SemanticDesignBridgeError(
            "empty semantic design requires traceability applicability=no without links"
        )
    for dimension in APPLICABILITY_DIMENSIONS:
        if dimension == "traceability":
            continue
        expected_test_cases = [
            str(obligation.get("planned_tc_id", ""))
            for obligation in obligations
            if isinstance(obligation, Mapping)
            and obligation.get("design_dimension") == dimension
        ]
        if not expected_test_cases:
            continue
        expected_atoms = {
            planned_tc_to_atom[test_case_id]
            for test_case_id in expected_test_cases
        }
        row = applicability_by_dimension[dimension]
        if (
            row.get("applicable") != "yes"
            or set(map(str, row.get("linked_test_cases", [])))
            != set(expected_test_cases)
            or set(map(str, row.get("linked_atoms", []))) != expected_atoms
        ):
            raise SemanticDesignBridgeError(
                f"applicability dimension {dimension} must cover every compiled "
                "ATOM/TC pair"
            )

    return {
        "version": BRIDGE_CONTRACT_VERSION,
        "status": "verified",
        "contract": BRIDGE_CONTRACT_NAME,
        "prepared_context_sha256": prepared_context_sha256(context),
        "scope_boundary_decision_sha256": canonical_payload_sha256(boundary),
        "semantic_design_decision_sha256": canonical_payload_sha256(design),
        "source_row_count": len(rows),
        "included_source_row_count": sum(
            item.get("disposition") == "included" for item in boundary_decisions
        ),
        "assertion_count": len(assertions),
        "testable_assertion_count": testable_assertion_count,
        "obligation_count": len(obligations),
        "dependency_binding_count": len(dependency_bindings),
        "planned_test_case_count": len(planned_tc_ids),
        "dictionary_count": len(dictionaries),
        "negative_oracle_count": len(design["negative_oracles"]),
        "requiredness_oracle_count": len(design["requiredness_oracles"]),
        "approved_clarification_count": len(normalized_clarifications),
        "state_change_obligation_count": sum(
            _state_change_class(item) for item in obligations_by_id.values()
        ),
        "reset_lifecycle_binding_count": len(reset_lifecycle_bindings),
    }


def legacy_v1_projection(
    design: Mapping[str, Any],
) -> dict[str, Any]:
    """Project bridge output into the legacy row/design shape for shared rendering only."""

    if design.get("version") != SEMANTIC_DESIGN_VERSION:
        raise SemanticDesignBridgeError(
            f"semantic bridge projection requires version {SEMANTIC_DESIGN_VERSION}"
        )
    reset_lifecycle_by_obligation = {
        str(item.get("obligation_id", "")): item
        for item in design.get("reset_lifecycle_bindings", [])
        if isinstance(item, Mapping)
    }
    projected_obligations: list[dict[str, Any]] = []
    for source_obligation in design["obligations"]:
        obligation = dict(source_obligation)
        lifecycle_binding = reset_lifecycle_by_obligation.get(
            str(obligation.get("obligation_id", ""))
        )
        if lifecycle_binding is None:
            obligation.update(
                {
                    "initial_state_capture": "none_required",
                    "changed_state_setup": "none_required",
                    "pre_action_state_oracle": "none_required",
                    "state_relation": "none_required",
                }
            )
        else:
            obligation.update(
                {
                    "initial_state_capture": (
                        "source-condition:"
                        f"{lifecycle_binding['initial_condition_index']}"
                    ),
                    "changed_state_setup": lifecycle_binding[
                        "changed_state_setup"
                    ],
                    "pre_action_state_oracle": lifecycle_binding[
                        "pre_action_state_oracle"
                    ],
                    "state_relation": lifecycle_binding["state_relation"],
                }
            )
        projected_obligations.append(obligation)
    return {
        "version": 1,
        "status": design["status"],
        "blocking_reason": design["blocking_reason"],
        "scope_summary": design["scope_summary"],
        "included": design["included"],
        "excluded": design["excluded"],
        "mockup_locators": design["mockup_locators"],
        "source_decisions": [
            {
                "source_row_id": item["source_row_id"],
                "scope_disposition": (
                    "yes"
                    if any(
                        assertion.get("semantic_disposition") == "testable"
                        for assertion in item["assertions"]
                    )
                    else (
                        "unclear"
                        if any(
                            assertion.get("semantic_disposition") == "ambiguous"
                            for assertion in item["assertions"]
                        )
                        else "no"
                    )
                ),
                "requirement_codes": item["requirement_codes"],
                "assertions": item["assertions"],
            }
            for item in design["source_designs"]
        ],
        "obligations": projected_obligations,
        "applicability": design["applicability"],
    }


__all__ = [
    "APPLICABILITY_DIMENSIONS",
    "BRIDGE_CONTRACT_NAME",
    "BRIDGE_CONTRACT_VERSION",
    "SEMANTIC_DESIGN_CONTRACT",
    "SEMANTIC_DESIGN_VERSION",
    "SemanticDesignBridgeError",
    "canonical_payload_sha256",
    "legacy_v1_projection",
    "load_approved_clarifications",
    "normalize_semantic_design_source_property_transport",
    "normalize_semantic_design_transport",
    "prepared_context_sha256",
    "semantic_design_allows_canonical_transport_binding",
    "semantic_design_completeness_diagnostics",
    "semantic_design_minimum_obligation_count",
    "semantic_design_transport_diagnostics",
    "semantic_design_output_schema",
    "semantic_design_prompt",
    "validate_bridge_boundary",
    "validate_semantic_input_preflight",
    "validate_semantic_design_binding",
    "semantic_source_signal_registry",
]
