from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from test_case_agent.coverage_io import CoverageIoError, coverage_graph_from_dict
from test_case_agent.iteration_contract import (
    REVIEWER_FALSIFICATION_PROBES,
    has_complete_all_row_parity,
    reviewer_acceptance_contract,
    reviewer_prompt_instruction,
    reviewer_response_schema,
)
from test_case_agent.reviewer_evidence import (
    ReviewerEvidenceError,
    build_reviewer_evidence_pack,
    load_reviewer_evidence_basis_document,
)
from test_case_agent.review_cycle.runtime import sha256_path, write_json_atomic
from test_case_agent.stage_backend import (
    SUPPORTED_IMAGE_SUFFIXES,
    RegisteredImageInput,
    StageBackendError,
    verify_registered_image_inputs,
)
from test_case_agent.strict_output_schema import validate_openai_strict_output_instance
from test_case_agent.test_design import TestCaseDesign


ELIGIBILITY_SCHEMA_VERSION = 1
REVIEWER_BACKEND = "codex-exec-tool-free"
_HEX = frozenset("0123456789abcdef")


class PromotionAdapterBlocked(RuntimeError):
    """The immutable shadow does not prove production-promotion eligibility."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"promotion-adapter[{code}]: {message}")


@dataclass(frozen=True)
class PromotionAdapterResult:
    status: str
    basis_path: Path
    basis_sha256: str
    candidate_path: Path
    candidate_sha256: str
    production_test_case_hashes: Mapping[str, str]


@dataclass(frozen=True)
class _Snapshot:
    path: Path
    raw: bytes
    sha256: str

    @property
    def size_bytes(self) -> int:
        return len(self.raw)


def _blocked(code: str, message: str) -> PromotionAdapterBlocked:
    return PromotionAdapterBlocked(code, message)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _canonical_digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _is_digest(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in _HEX for char in value)
    )


def _resolve_inside(path: Path, parent: Path, label: str) -> Path:
    candidate = path if path.is_absolute() else parent / path
    resolved = candidate.resolve()
    try:
        resolved.relative_to(parent.resolve())
    except ValueError as exc:
        raise _blocked("unsafe-path", f"{label} must be inside {parent}: {resolved}") from exc
    return resolved


def _required_file(path: Path, *, parent: Path, label: str) -> Path:
    resolved = _resolve_inside(path, parent, label)
    if not resolved.is_file() or resolved.stat().st_size <= 0:
        raise _blocked("missing-artifact", f"required {label} is missing: {resolved}")
    return resolved


def _snapshot(path: Path, label: str) -> _Snapshot:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise _blocked("artifact-read", f"cannot read {label} {path}: {exc}") from exc
    if not raw:
        raise _blocked("missing-artifact", f"required {label} is empty: {path}")
    return _Snapshot(path=path, raw=raw, sha256=hashlib.sha256(raw).hexdigest())


def _json(snapshot: _Snapshot, label: str) -> Mapping[str, Any]:
    try:
        payload = json.loads(snapshot.raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise _blocked("invalid-json", f"cannot parse {label} {snapshot.path}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise _blocked("invalid-json", f"{label} must be a JSON object")
    return payload


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _binding(snapshot: _Snapshot, repo_root: Path) -> dict[str, Any]:
    return {
        "path": _relative(snapshot.path, repo_root),
        "sha256": snapshot.sha256,
        "size_bytes": snapshot.size_bytes,
    }


def _artifact(
    *, cycle_dir: Path, relative: str, label: str, snapshots: list[_Snapshot]
) -> _Snapshot:
    path = _required_file(Path(relative), parent=cycle_dir, label=label)
    item = _snapshot(path, label)
    snapshots.append(item)
    return item


def _accepted_summary(summary: Mapping[str, Any]) -> None:
    if (
        summary.get("status") == "accepted-with-calibration-pending"
        or summary.get("non_promotable_reason") == "calibration-pending"
    ):
        raise _blocked(
            "calibration-pending",
            "a suite with pending UI calibration is not promotion-eligible",
        )
    expected = {
        "schema_version": 1,
        "mode": "immutable-deterministic-first",
        "status": "accepted-shadow",
        "writer_model_calls": 0,
        "reviewer_model_calls": 1,
        "reviewer_decision": "accepted",
        "reviewer_accepted_zero_findings": True,
        "suite_gate_passed": True,
        "protected_inputs_unchanged": True,
        "canonical_publication": "not-performed",
        "promotion": "out-of-scope",
    }
    mismatches = {
        name: {"expected": expected_value, "actual": summary.get(name)}
        for name, expected_value in expected.items()
        if summary.get(name) != expected_value
    }
    if mismatches:
        raise _blocked(
            "iteration-not-eligible",
            f"immutable iteration terminal invariants mismatch: {mismatches}",
        )
    if (
        summary.get("qualification_only") is True
        or summary.get("promotion_eligible") is False
        or bool(summary.get("non_promotable_reason"))
    ):
        raise _blocked(
            "qualification-not-promotable",
            "qualification-only or explicitly non-promotable runs are ineligible",
        )


def _graph_case_bindings(
    graph: Mapping[str, Any],
) -> tuple[tuple[str, str, str, str], ...]:
    raw_cases = graph.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise _blocked("invalid-graph", "coverage graph must contain cases")
    bindings: list[tuple[str, str, str, str]] = []
    for index, raw in enumerate(raw_cases):
        if not isinstance(raw, Mapping):
            raise _blocked("invalid-graph", f"coverage graph cases[{index}] must be an object")
        case_key = raw.get("case_key")
        tc_id = raw.get("tc_id")
        obligation_ids = raw.get("obligation_ids")
        status = raw.get("status")
        if (
            not isinstance(case_key, str)
            or not case_key
            or not isinstance(tc_id, str)
            or not tc_id
            or not isinstance(obligation_ids, list)
            or len(obligation_ids) != 1
            or not isinstance(obligation_ids[0], str)
            or not obligation_ids[0]
            or status not in {"executable", "candidate-ui-calibration"}
        ):
            raise _blocked("invalid-graph", f"coverage graph cases[{index}] binding is invalid")
        bindings.append((case_key, tc_id, obligation_ids[0], status))
    if len(bindings) != len({item[0] for item in bindings}):
        raise _blocked("invalid-graph", "coverage graph case_key values must be unique")
    return tuple(bindings)


_TEST_CASE_DESIGN_FIELDS = {
    "case_key",
    "tc_id",
    "status",
    "title",
    "case_type",
    "priority",
    "package_id",
    "traceability",
    "preconditions",
    "test_data",
    "steps",
    "expected_result",
    "postconditions",
    "calibration_question",
}


def _test_case_designs(payload: Mapping[str, Any]) -> tuple[TestCaseDesign, ...]:
    if set(payload) != {"schema_version", "cases"} or payload.get("schema_version") != 1:
        raise _blocked(
            "test-designs-invalid",
            "test-case-designs.json differs from the closed runner contract",
        )
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise _blocked("test-designs-invalid", "test-case designs must be a non-empty array")

    def text_value(value: Any, path: str, *, allow_empty: bool = False) -> str:
        if (
            not isinstance(value, str)
            or (not allow_empty and not value.strip())
            or "\n" in value
            or "\r" in value
        ):
            raise _blocked("test-designs-invalid", f"{path} must be single-line text")
        return value

    def text_list(value: Any, path: str) -> tuple[str, ...]:
        if not isinstance(value, list):
            raise _blocked("test-designs-invalid", f"{path} must be a text array")
        return tuple(
            text_value(item, f"{path}[{index}]")
            for index, item in enumerate(value)
        )

    designs: list[TestCaseDesign] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_cases):
        path = f"test-case-designs.cases[{index}]"
        if not isinstance(raw, Mapping) or set(raw) != _TEST_CASE_DESIGN_FIELDS:
            raise _blocked("test-designs-invalid", f"{path} fields are invalid")
        case_key = text_value(raw["case_key"], f"{path}.case_key")
        if case_key in seen:
            raise _blocked("test-designs-invalid", f"duplicate case_key: {case_key}")
        seen.add(case_key)
        designs.append(
            TestCaseDesign(
                case_key=case_key,
                tc_id=text_value(raw["tc_id"], f"{path}.tc_id"),
                status=text_value(raw["status"], f"{path}.status"),
                title=text_value(raw["title"], f"{path}.title"),
                case_type=text_value(raw["case_type"], f"{path}.case_type"),
                priority=text_value(raw["priority"], f"{path}.priority"),
                package_id=text_value(raw["package_id"], f"{path}.package_id"),
                traceability=text_list(raw["traceability"], f"{path}.traceability"),
                preconditions=text_list(raw["preconditions"], f"{path}.preconditions"),
                test_data=text_list(raw["test_data"], f"{path}.test_data"),
                steps=text_list(raw["steps"], f"{path}.steps"),
                expected_result=text_value(
                    raw["expected_result"], f"{path}.expected_result"
                ),
                postconditions=text_list(
                    raw["postconditions"], f"{path}.postconditions"
                ),
                calibration_question=text_value(
                    raw["calibration_question"],
                    f"{path}.calibration_question",
                    allow_empty=True,
                ),
            )
        )
    return tuple(designs)


def _validate_reviewer_request(
    request: Mapping[str, Any],
    *,
    graph_digest: str,
    candidate_sha256: str,
    case_bindings: Sequence[tuple[str, str, str, str]],
) -> int:
    schema_version = request.get("schema_version")
    if schema_version != 2:
        raise _blocked(
            "reviewer-v2-required",
            "only ReviewerEvidencePack v2 iterations are promotion-eligible",
        )
    if (
        request.get("graph_digest") != graph_digest
        or request.get("draft_sha256") != candidate_sha256
    ):
        raise _blocked("review-request-mismatch", "reviewer request is not bound to graph and candidate")
    if schema_version == 2:
        expected_request_fields = {
            "schema_version",
            "graph_digest",
            "draft_sha256",
            "evidence_pack_sha256",
            "reviewer_evidence_pack",
            "acceptance",
        }
        if set(request) != expected_request_fields:
            raise _blocked(
                "review-request-mismatch",
                "reviewer v2 request fields differ from the closed production contract",
            )
        pack = request.get("reviewer_evidence_pack")
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
        if not isinstance(pack, Mapping) or set(pack) != expected_pack_fields:
            raise _blocked(
                "review-request-mismatch",
                "reviewer v2 evidence pack fields differ from the closed production contract",
            )
        identity = pack.get("identity")
        evidence_pack_sha256 = request.get("evidence_pack_sha256")
        if (
            pack.get("schema_version") != 2
            or not isinstance(identity, Mapping)
            or identity.get("contract") != "reviewer-evidence-pack-v2"
            or identity.get("graph_digest") != graph_digest
            or identity.get("coverage_graph_digest") != graph_digest
            or identity.get("draft_sha256") != candidate_sha256
            or not _is_digest(evidence_pack_sha256)
            or _canonical_digest(pack) != evidence_pack_sha256
        ):
            raise _blocked(
                "review-request-mismatch",
                "reviewer v2 evidence pack is not hash-bound to the graph and candidate",
            )
        acceptance = reviewer_acceptance_contract(schema_version=2)
        if request.get("acceptance") != acceptance or pack.get("acceptance") != acceptance:
            raise _blocked(
                "review-request-mismatch",
                "reviewer v2 acceptance contract is not production-safe",
            )
        normalized_projection = pack.get("normalized_projection")
        if not isinstance(normalized_projection, Mapping):
            raise _blocked("review-request-mismatch", "reviewer v2 normalized projection is invalid")
        if _canonical_digest(normalized_projection) != graph_digest:
            raise _blocked(
                "review-request-mismatch",
                "reviewer v2 normalized projection differs from the coverage graph",
            )
        if (
            identity.get("source_manifest_digest")
            != normalized_projection.get("source_manifest_digest")
            or identity.get("obligation_set_digest")
            != normalized_projection.get("obligation_set_digest")
        ):
            raise _blocked(
                "review-request-mismatch",
                "reviewer v2 qualified-source identity differs from the coverage graph",
            )

        test_cases = pack.get("test_cases")
        if not isinstance(test_cases, Mapping):
            raise _blocked("review-request-mismatch", "reviewer v2 test cases are invalid")
        draft_markdown = test_cases.get("draft_markdown")
        designs = test_cases.get("designs")
        if (
            not isinstance(draft_markdown, str)
            or hashlib.sha256(draft_markdown.encode("utf-8")).hexdigest()
            != candidate_sha256
            or not isinstance(designs, list)
        ):
            raise _blocked(
                "review-request-mismatch",
                "reviewer v2 full draft is not bound to the candidate",
            )
        expected_design_bindings = sorted(
            (case_key, tc_id, status)
            for case_key, tc_id, _obligation_id, status in case_bindings
        )
        design_bindings: list[tuple[str, str, str]] = []
        for index, raw in enumerate(designs):
            if not isinstance(raw, Mapping):
                raise _blocked(
                    "review-request-mismatch",
                    f"reviewer v2 test_cases.designs[{index}] is invalid",
                )
            case_key = raw.get("case_key")
            tc_id = raw.get("tc_id")
            status = raw.get("status")
            if (
                not isinstance(case_key, str)
                or not case_key
                or not isinstance(tc_id, str)
                or not tc_id
                or not isinstance(status, str)
                or not status
            ):
                raise _blocked(
                    "review-request-mismatch",
                    f"reviewer v2 test_cases.designs[{index}] binding is invalid",
                )
            design_bindings.append((case_key, tc_id, status))
        if sorted(design_bindings) != expected_design_bindings:
            raise _blocked(
                "review-request-mismatch",
                "reviewer v2 test-case designs differ from graph cases",
            )

        literal_rows = pack.get("literal_source_evidence")
        coverage_mapping = pack.get("coverage_mapping")
        supporting_mapping = pack.get("supporting_evidence_mapping")
        design_support_mapping = pack.get("design_support_mapping")
        if (
            not isinstance(literal_rows, list)
            or not isinstance(coverage_mapping, list)
            or not isinstance(supporting_mapping, list)
            or not isinstance(design_support_mapping, list)
        ):
            raise _blocked(
                "review-request-mismatch",
                "reviewer v2 literal rows and all coverage/support mappings must be arrays",
            )
        source_row_ids: list[str] = []
        for index, raw in enumerate(literal_rows):
            source_row_id = raw.get("source_row_id") if isinstance(raw, Mapping) else None
            source_text = raw.get("bounded_source_text") if isinstance(raw, Mapping) else None
            source_text_sha256 = (
                raw.get("bounded_source_text_sha256") if isinstance(raw, Mapping) else None
            )
            if (
                not isinstance(source_row_id, str)
                or not source_row_id
                or not isinstance(source_text, str)
                or not source_text
                or source_text_sha256
                != hashlib.sha256(source_text.encode("utf-8")).hexdigest()
            ):
                raise _blocked(
                    "review-request-mismatch",
                    f"reviewer v2 literal_source_evidence[{index}] is not literal-text bound",
                )
            source_row_ids.append(source_row_id)
        if not source_row_ids or len(source_row_ids) != len(set(source_row_ids)):
            raise _blocked(
                "review-request-mismatch",
                "reviewer v2 literal source rows must be non-empty and unique",
            )
        source_structure = pack.get("source_structure")
        scope_definition = (
            source_structure.get("scope_definition")
            if isinstance(source_structure, Mapping)
            else None
        )
        if (
            not isinstance(source_structure, Mapping)
            or not has_complete_all_row_parity(literal_rows, source_structure)
        ):
            raise _blocked(
                "review-request-mismatch",
                "reviewer v2 bounded DOCX/XHTML/PDF parity proof is incomplete",
            )
        mapping_fields = (
            "source_row_id",
            "assertion_id",
            "property_id",
            "obligation_id",
            "case_key",
            "tc_id",
        )
        mapped_rows: set[str] = set()
        mapped_cases: list[tuple[str, str, str]] = []
        for index, raw in enumerate(coverage_mapping):
            if not isinstance(raw, Mapping) or set(raw) != set(mapping_fields):
                raise _blocked(
                    "review-request-mismatch",
                    f"reviewer v2 coverage_mapping[{index}] is invalid",
                )
            values = tuple(raw[name] for name in mapping_fields)
            if any(not isinstance(value, str) for value in values) or not values[0]:
                raise _blocked(
                    "review-request-mismatch",
                    f"reviewer v2 coverage_mapping[{index}] bindings are invalid",
                )
            mapped_rows.add(values[0])
            first_empty = next(
                (binding_index for binding_index, value in enumerate(values) if not value),
                len(values),
            )
            if any(values[binding_index] for binding_index in range(first_empty, len(values))):
                raise _blocked(
                    "review-request-mismatch",
                    f"reviewer v2 coverage_mapping[{index}] skips a binding level",
                )
            if values[4]:
                mapped_cases.append((values[4], values[5], values[3]))
        if mapped_rows != set(source_row_ids):
            raise _blocked(
                "review-request-mismatch",
                "reviewer v2 coverage mapping does not include every literal source row",
            )
        expected_cases = sorted(
            (case_key, tc_id, obligation_id)
            for case_key, tc_id, obligation_id, _status in case_bindings
        )
        if sorted(mapped_cases) != expected_cases:
            raise _blocked(
                "review-request-mismatch",
                "reviewer v2 coverage mapping differs from graph case bindings",
            )

        supporting_fields = {
            "source_row_id",
            "source_path",
            "source_locator",
            "evidence_role",
            "exact_source_fragment",
            "exact_source_fragment_sha256",
            "primary_source_row_id",
            "assertion_id",
            "property_id",
            "obligation_id",
            "case_key",
            "tc_id",
        }
        supporting_keys: set[tuple[str, ...]] = set()
        for index, raw in enumerate(supporting_mapping):
            if not isinstance(raw, Mapping) or set(raw) != supporting_fields:
                raise _blocked(
                    "review-request-mismatch",
                    f"reviewer v2 supporting_evidence_mapping[{index}] is invalid",
                )
            fragment = raw.get("exact_source_fragment")
            binding = tuple(
                raw.get(name)
                for name in (
                    "source_row_id",
                    "evidence_role",
                    "exact_source_fragment",
                    "assertion_id",
                    "property_id",
                    "obligation_id",
                    "case_key",
                    "tc_id",
                )
            )
            if (
                any(not isinstance(value, str) for value in raw.values())
                or raw.get("source_row_id") not in set(source_row_ids)
                or raw.get("primary_source_row_id") not in set(source_row_ids)
                or not isinstance(fragment, str)
                or not fragment
                or raw.get("exact_source_fragment_sha256")
                != hashlib.sha256(fragment.encode("utf-8")).hexdigest()
                or binding in supporting_keys
            ):
                raise _blocked(
                    "review-request-mismatch",
                    f"reviewer v2 supporting_evidence_mapping[{index}] binding is invalid",
                )
            supporting_keys.add(binding)

        design_support_fields = {
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
        support_role_fields = {
            "setup": "preconditions",
            "action": "steps",
            "cleanup": "postconditions",
        }
        designs_by_case = {
            item.get("case_key"): item
            for item in designs
            if isinstance(item, Mapping)
        }
        properties_by_id = {
            item.get("property_id"): item
            for item in normalized_projection.get("properties", [])
            if isinstance(item, Mapping)
        }
        obligations_by_id = {
            item.get("obligation_id"): item
            for item in normalized_projection.get("obligations", [])
            if isinstance(item, Mapping)
        }
        primary_by_case = {
            case_key: (tc_id, obligation_id)
            for case_key, tc_id, obligation_id in expected_cases
        }
        design_support_keys: set[tuple[Any, ...]] = set()
        for index, raw in enumerate(design_support_mapping):
            if not isinstance(raw, Mapping) or set(raw) != design_support_fields:
                raise _blocked(
                    "review-request-mismatch",
                    f"reviewer v2 design_support_mapping[{index}] is invalid",
                )
            support_role = raw.get("support_role")
            field_name = raw.get("test_case_field")
            item_index = raw.get("item_index")
            materialized_text = raw.get("materialized_text")
            source_fragment = raw.get("source_action_fragment")
            case_key = raw.get("case_key")
            tc_id = raw.get("tc_id")
            obligation_id = raw.get("obligation_id")
            property_id = raw.get("property_id")
            design = designs_by_case.get(case_key)
            obligation = obligations_by_id.get(obligation_id)
            prop = properties_by_id.get(property_id)
            primary = primary_by_case.get(case_key)
            field_items = design.get(field_name) if isinstance(design, Mapping) else None
            source_actions = (
                obligation.get("validation_trigger"),
                obligation.get("cleanup_strategy"),
            ) if isinstance(obligation, Mapping) else ()
            binding_key = (
                support_role,
                field_name,
                item_index,
                raw.get("source_row_id"),
                raw.get("assertion_id"),
                property_id,
                obligation_id,
                case_key,
                tc_id,
            )
            if (
                any(
                    not isinstance(raw.get(name), str)
                    for name in design_support_fields - {"item_index"}
                )
                or support_role not in support_role_fields
                or field_name != support_role_fields.get(support_role)
                or type(item_index) is not int
                or item_index < 0
                or not isinstance(materialized_text, str)
                or not materialized_text
                or raw.get("materialized_text_sha256")
                != hashlib.sha256(materialized_text.encode("utf-8")).hexdigest()
                or not isinstance(source_fragment, str)
                or not source_fragment
                or source_fragment not in materialized_text
                or raw.get("source_row_id") not in set(source_row_ids)
                or primary is None
                or primary[0] != tc_id
                or primary[1] == obligation_id
                or not isinstance(design, Mapping)
                or obligation_id not in design.get("traceability", [])
                or not isinstance(field_items, list)
                or item_index >= len(field_items)
                or field_items[item_index] != materialized_text
                or not isinstance(obligation, Mapping)
                or obligation.get("property_id") != property_id
                or source_fragment not in source_actions
                or not isinstance(prop, Mapping)
                or prop.get("assertion_id") != raw.get("assertion_id")
                or prop.get("source_row_id") != raw.get("source_row_id")
                or binding_key in design_support_keys
            ):
                raise _blocked(
                    "review-request-mismatch",
                    f"reviewer v2 design_support_mapping[{index}] binding is invalid",
                )
            design_support_keys.add(binding_key)

        coverage_gaps = pack.get("coverage_gaps")
        expected_gap_fields = {
            "artifact",
            "registered_gap_ids",
            "materialized_gap_ids",
            "content",
            "content_sha256",
            "status",
        }
        expected_gap_ids = (
            scope_definition.get("gap_ids")
            if isinstance(scope_definition, Mapping)
            else None
        )
        if (
            not isinstance(coverage_gaps, Mapping)
            or set(coverage_gaps) != expected_gap_fields
            or not isinstance(expected_gap_ids, list)
            or coverage_gaps.get("registered_gap_ids") != sorted(expected_gap_ids)
            or coverage_gaps.get("materialized_gap_ids") != sorted(expected_gap_ids)
            or coverage_gaps.get("status")
            != "complete-literal-registered-artifact"
            or not isinstance(coverage_gaps.get("content"), str)
            or coverage_gaps.get("content_sha256")
            != hashlib.sha256(
                str(coverage_gaps.get("content", "")).encode("utf-8")
            ).hexdigest()
        ):
            raise _blocked(
                "review-request-mismatch",
                "reviewer v2 coverage-gap artifact is incomplete or differs from scope",
            )

        mockups = pack.get("mockup_attachments")
        if not isinstance(mockups, list):
            raise _blocked("review-request-mismatch", "reviewer v2 mockup attachments must be an array")
        mockup_paths: set[str] = set()
        expected_mockup_fields = {
            "path",
            "role",
            "scope_id",
            "sha256",
            "size_bytes",
            "screen_description",
            "locators",
        }
        for index, raw in enumerate(mockups):
            if not isinstance(raw, Mapping) or set(raw) != expected_mockup_fields:
                raise _blocked(
                    "review-request-mismatch",
                    f"reviewer v2 mockup_attachments[{index}] is invalid",
                )
            path = raw.get("path")
            digest = raw.get("sha256")
            size_bytes = raw.get("size_bytes")
            if (
                not isinstance(path, str)
                or not path
                or path in mockup_paths
                or not _is_digest(digest)
                or type(size_bytes) is not int
                or size_bytes <= 0
                or raw.get("role") != "scope-mockup"
                or raw.get("scope_id") != identity.get("scope_id")
                or not isinstance(raw.get("screen_description"), str)
                or not isinstance(raw.get("locators"), list)
            ):
                raise _blocked(
                    "review-request-mismatch",
                    f"reviewer v2 mockup_attachments[{index}] binding is invalid",
                )
            mockup_paths.add(path)
        return 2

    raw_cases = request.get("cases")
    if not isinstance(raw_cases, list):
        raise _blocked("review-request-mismatch", "reviewer request cases must be an array")
    projected: list[tuple[str, str, str, str]] = []
    for index, raw in enumerate(raw_cases):
        if not isinstance(raw, Mapping) or not isinstance(raw.get("obligation"), Mapping):
            raise _blocked("review-request-mismatch", f"reviewer request cases[{index}] is invalid")
        projected.append(
            (
                raw.get("case_key"),
                raw.get("tc_id"),
                raw["obligation"].get("obligation_id"),
                raw.get("status"),
            )
        )
    if tuple(projected) != tuple(case_bindings):
        raise _blocked("review-request-mismatch", "reviewer request case projection differs from graph")
    if request.get("acceptance") != reviewer_acceptance_contract():
        raise _blocked("review-request-mismatch", "reviewer acceptance contract is not production-safe")
    return 1


def _validate_reviewer_response(
    response: Mapping[str, Any],
    *,
    schema: Mapping[str, Any],
    graph_digest: str,
    candidate_sha256: str,
    case_bindings: Sequence[tuple[str, str, str, str]],
    request_payload: Mapping[str, Any],
) -> None:
    try:
        validate_openai_strict_output_instance(response, schema)
    except ValueError as exc:
        raise _blocked("review-response-invalid", str(exc)) from exc
    schema_version = request_payload.get("schema_version")
    finding_free = (
        response.get("findings") == []
        if schema_version == 1
        else response.get("source_projection_findings") == []
        and response.get("test_case_findings") == []
    )
    evidence_bound = (
        True
        if schema_version == 1
        else response.get("evidence_pack_sha256")
        == request_payload.get("evidence_pack_sha256")
    )
    if (
        response.get("schema_version") != schema_version
        or response.get("graph_digest") != graph_digest
        or response.get("draft_sha256") != candidate_sha256
        or not evidence_bound
        or response.get("decision") != "accepted"
        or not finding_free
    ):
        raise _blocked(
            "review-response-not-accepted",
            "reviewer response must be accepted, candidate-bound and finding-free",
        )
    expected = {
        case_key: (
            tc_id,
            obligation_id,
            "calibration-pending"
            if case_status == "candidate-ui-calibration"
            else "covered",
        )
        for case_key, tc_id, obligation_id, case_status in case_bindings
    }
    falsification_basis: dict[
        str,
        tuple[set[str], set[str], str, dict[str, set[str]]],
    ] = {}
    allowed_probe_bindings: dict[str, set[tuple[str, str, int]]] = {
        case_key: {("primary", binding[1], -1)}
        for case_key, binding in expected.items()
    }
    support_materialized_items: dict[
        tuple[str, str, str, int],
        set[str],
    ] = {}
    if schema_version == 2:
        pack = request_payload.get("reviewer_evidence_pack")
        test_cases = pack.get("test_cases") if isinstance(pack, Mapping) else None
        projection = (
            pack.get("normalized_projection") if isinstance(pack, Mapping) else None
        )
        raw_designs = (
            test_cases.get("designs") if isinstance(test_cases, Mapping) else None
        )
        raw_obligations = (
            projection.get("obligations")
            if isinstance(projection, Mapping)
            else None
        )
        raw_design_support = (
            pack.get("design_support_mapping") if isinstance(pack, Mapping) else None
        )
        if (
            not isinstance(raw_designs, list)
            or not isinstance(raw_obligations, list)
            or not isinstance(raw_design_support, list)
        ):
            raise _blocked(
                "review-response-not-accepted",
                "reviewer falsification basis is missing from the evidence pack",
            )
        obligations_by_id = {
            raw.get("obligation_id"): raw
            for raw in raw_obligations
            if isinstance(raw, Mapping)
            and isinstance(raw.get("obligation_id"), str)
        }
        for raw_design in raw_designs:
            if not isinstance(raw_design, Mapping):
                continue
            case_key = raw_design.get("case_key")
            binding = expected.get(case_key) if isinstance(case_key, str) else None
            design_context: set[str] = set()
            design_steps: set[str] = set()
            design_fields: dict[str, set[str]] = {}
            for field in ("preconditions", "test_data", "steps", "postconditions"):
                values = raw_design.get(field)
                if isinstance(values, (list, tuple)):
                    normalized = {
                        value for value in values if isinstance(value, str) and value
                    }
                    design_fields[field] = normalized
                    design_context.update(normalized)
                    if field == "steps":
                        design_steps = normalized
            expected_result = raw_design.get("expected_result")
            if (
                not isinstance(case_key, str)
                or binding is None
                or case_key in falsification_basis
                or not design_steps
                or not design_context
                or set(design_fields)
                != {"preconditions", "test_data", "steps", "postconditions"}
                or not isinstance(expected_result, str)
                or not expected_result
            ):
                raise _blocked(
                    "review-response-not-accepted",
                    "reviewer falsification basis is not bound to every graph case",
                )
            falsification_basis[case_key] = (
                design_steps,
                design_context,
                expected_result,
                design_fields,
            )
        if set(falsification_basis) != set(expected):
            raise _blocked(
                "review-response-not-accepted",
                "reviewer falsification basis is not bound to every graph case",
            )
        for raw in raw_design_support:
            if not isinstance(raw, Mapping):
                continue
            case_key = raw.get("case_key")
            obligation_id = raw.get("obligation_id")
            support_role = raw.get("support_role")
            item_index = raw.get("item_index")
            materialized_text = raw.get("materialized_text")
            if (
                isinstance(case_key, str)
                and case_key in expected
                and raw.get("tc_id") == expected[case_key][0]
                and isinstance(obligation_id, str)
                and obligation_id in obligations_by_id
                and support_role in {"setup", "action", "cleanup"}
                and type(item_index) is int
                and item_index >= 0
                and isinstance(materialized_text, str)
                and materialized_text
            ):
                binding_role = f"design-support-{support_role}"
                allowed_probe_bindings[case_key].add(
                    (binding_role, obligation_id, item_index)
                )
                support_materialized_items.setdefault(
                    (case_key, binding_role, obligation_id, item_index),
                    set(),
                ).add(materialized_text)
    raw_results = response.get("case_results")
    if not isinstance(raw_results, list):
        raise _blocked("review-response-not-accepted", "reviewer case_results must be an array")
    seen: set[str] = set()
    for raw in raw_results:
        if not isinstance(raw, Mapping):
            raise _blocked("review-response-not-accepted", "reviewer case result must be an object")
        case_key = raw.get("case_key")
        if (
            case_key not in expected
            or case_key in seen
            or (
                raw.get("tc_id"),
                raw.get("obligation_id"),
                raw.get("status"),
            )
            != expected[case_key]
        ):
            raise _blocked(
                "review-response-not-accepted",
                "reviewer must cover every graph case exactly once with its bound identifiers",
            )
        if schema_version == 2:
            falsification = raw.get("falsification")
            if (
                not isinstance(falsification, Mapping)
                or set(falsification) != set(REVIEWER_FALSIFICATION_PROBES)
            ):
                raise _blocked(
                    "review-response-not-accepted",
                    "reviewer must return all per-case falsification probes",
                )
            for probe in REVIEWER_FALSIFICATION_PROBES:
                probe_result = falsification.get(probe)
                values = (
                    tuple(
                        probe_result.get(name)
                        for name in (
                            "detail",
                            "binding_role",
                            "obligation_id",
                            "trigger_or_step",
                            "oracle",
                        )
                    )
                    if isinstance(probe_result, Mapping)
                    else ()
                )
                if (
                    not isinstance(probe_result, Mapping)
                    or set(probe_result)
                    != {
                        "outcome",
                        "detail",
                        "binding_role",
                        "obligation_id",
                        "binding_item_index",
                        "trigger_or_step",
                        "oracle",
                    }
                    or probe_result.get("outcome") != "passed"
                    or type(probe_result.get("binding_item_index")) is not int
                    or any(
                        not isinstance(value, str)
                        or not value.strip()
                        or "\n" in value
                        or "\r" in value
                        for value in values
                    )
                ):
                    raise _blocked(
                        "review-response-not-accepted",
                        "promotion requires a recorded passing result for every "
                        "falsification probe",
                    )
                binding_role = values[1]
                probe_obligation_id = values[2]
                binding_item_index = probe_result["binding_item_index"]
                trigger_or_step = values[3]
                oracle = values[4]
                if (
                    (binding_role, probe_obligation_id, binding_item_index)
                    not in allowed_probe_bindings[case_key]
                ):
                    raise _blocked(
                        "review-response-not-accepted",
                        "reviewer falsification result is not bound to an exact "
                        "registered evidence chain",
                    )
                (
                    tc_steps,
                    _tc_context,
                    expected_result,
                    design_fields,
                ) = falsification_basis[case_key]
                if binding_role != "primary":
                    allowed_triggers = support_materialized_items[
                        (
                            case_key,
                            binding_role,
                            probe_obligation_id,
                            binding_item_index,
                        )
                    ]
                elif probe == "failure_attribution":
                    allowed_triggers = set().union(
                        design_fields["preconditions"],
                        design_fields["test_data"],
                        design_fields["steps"],
                    )
                else:
                    allowed_triggers = tc_steps
                if trigger_or_step not in allowed_triggers or oracle != expected_result:
                    raise _blocked(
                        "review-response-not-accepted",
                        "reviewer falsification result is not bound to the reviewed "
                        "case and obligation",
                    )
        seen.add(case_key)
    if seen != set(expected):
        raise _blocked("review-response-not-accepted", "reviewer omitted graph cases")


def _registered_mockup_metrics(
    *,
    request_payload: Mapping[str, Any],
    repo_root: Path,
    snapshots: list[_Snapshot],
) -> Mapping[str, int]:
    if request_payload.get("schema_version") == 1:
        return {"count": 0, "bytes": 0}
    pack = request_payload.get("reviewer_evidence_pack")
    mockups = pack.get("mockup_attachments") if isinstance(pack, Mapping) else None
    if not isinstance(mockups, list):  # pragma: no cover - request validator invariant
        raise _blocked("review-request-mismatch", "reviewer v2 request omits mockups")
    total_bytes = 0
    registered_images: list[RegisteredImageInput] = []
    for index, raw in enumerate(mockups):
        path_text = raw["path"]
        path = _required_file(
            Path(path_text),
            parent=repo_root,
            label=f"registered reviewer mockup[{index}]",
        )
        if (
            _relative(path, repo_root) != path_text
            or path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES
        ):
            raise _blocked(
                "review-mockup-invalid",
                f"registered reviewer mockup path is not canonical or supported: {path_text}",
            )
        item = _snapshot(path, f"registered reviewer mockup[{index}]")
        snapshots.append(item)
        if item.sha256 != raw["sha256"] or item.size_bytes != raw["size_bytes"]:
            raise _blocked(
                "review-mockup-drift",
                f"registered reviewer mockup differs from its evidence binding: {path_text}",
            )
        total_bytes += item.size_bytes
        registered_images.append(
            RegisteredImageInput(
                path=path,
                sha256=item.sha256,
                size_bytes=item.size_bytes,
            )
        )
    try:
        verify_registered_image_inputs(tuple(registered_images))
    except StageBackendError as exc:
        raise _blocked(
            "review-mockup-invalid",
            f"registered reviewer mockup is not a decodable image: {exc}",
        ) from exc
    return {"count": len(mockups), "bytes": total_bytes}


def _validate_receipts(
    *,
    summary: Mapping[str, Any],
    receipt_document: Mapping[str, Any],
    reviewer_prompt: _Snapshot,
    reviewer_schema: _Snapshot,
    reviewer_response: _Snapshot,
    request_payload: Mapping[str, Any],
    expected_image_attachments: Mapping[str, int],
) -> Mapping[str, Any]:
    stages = receipt_document.get("stages")
    if receipt_document.get("schema_version") != 1 or not isinstance(stages, list):
        raise _blocked("review-receipt-invalid", "model stage receipt document is invalid")
    if summary.get("model_stages") != stages:
        raise _blocked("review-receipt-invalid", "summary and receipt document stage lists differ")
    by_stage: dict[str, Mapping[str, Any]] = {}
    for raw in stages:
        if not isinstance(raw, Mapping) or raw.get("stage") in by_stage:
            raise _blocked("review-receipt-invalid", "model stage receipts are invalid or duplicated")
        stage = raw.get("stage")
        if not isinstance(stage, str):
            raise _blocked("review-receipt-invalid", "model stage receipt omits stage")
        by_stage[stage] = raw
    if set(by_stage) != {"writer", "reviewer"}:
        raise _blocked("review-receipt-invalid", "exactly writer and reviewer receipts are required")
    writer = by_stage["writer"]
    if (
        writer.get("backend") != "deterministic-zero-call"
        or writer.get("attempts") != 0
        or writer.get("response_sha256") != "unavailable"
    ):
        raise _blocked("writer-receipt-invalid", "writer receipt must prove deterministic zero-call")
    reviewer = by_stage["reviewer"]
    expected = {
        "backend": REVIEWER_BACKEND,
        "attempts": 1,
        "timeout_seconds": None,
        "tool_event_count": 0,
        "request_sha256": _canonical_digest(request_payload),
        "prompt_sha256": reviewer_prompt.sha256,
        "schema_sha256": reviewer_schema.sha256,
        "response_sha256": reviewer_response.sha256,
    }
    mismatches = {
        name: {"expected": value, "actual": reviewer.get(name)}
        for name, value in expected.items()
        if reviewer.get(name) != value
    }
    if mismatches:
        raise _blocked("review-receipt-invalid", f"reviewer receipt mismatch: {mismatches}")
    schema_version = request_payload.get("schema_version")
    if schema_version == 2:
        if reviewer.get("image_attachments") != expected_image_attachments:
            raise _blocked(
                "review-receipt-invalid",
                "reviewer image receipt differs from registered mockup attachments",
            )
    elif (
        "image_attachments" in reviewer
        and reviewer.get("image_attachments") != {"count": 0, "bytes": 0}
    ):
        raise _blocked(
            "review-receipt-invalid",
            "legacy reviewer receipt cannot declare image attachments",
        )
    for name in ("request_sha256", "prompt_sha256", "schema_sha256", "response_sha256"):
        if not _is_digest(reviewer.get(name)):
            raise _blocked("review-receipt-invalid", f"reviewer receipt {name} is not SHA-256")
    return reviewer


def _protected_baseline(
    *,
    receipt: Mapping[str, Any],
    repo_root: Path,
    ft_root: Path,
    snapshots: list[_Snapshot],
) -> Mapping[str, str]:
    files = receipt.get("files")
    if receipt.get("schema_version") != 1 or not isinstance(files, list):
        raise _blocked("baseline-receipt-invalid", "protected input receipt is invalid")
    protected: dict[str, dict[str, str]] = {"source": {}, "canonical": {}}
    seen: set[str] = set()
    for index, raw in enumerate(files):
        if not isinstance(raw, Mapping) or raw.get("role") not in protected:
            raise _blocked("baseline-receipt-invalid", f"protected files[{index}] is invalid")
        role = raw["role"]
        path_text = raw.get("path")
        digest = raw.get("sha256")
        size_bytes = raw.get("size_bytes")
        if (
            not isinstance(path_text, str)
            or not path_text
            or not _is_digest(digest)
            or type(size_bytes) is not int
            or size_bytes < 0
            or path_text in seen
        ):
            raise _blocked("baseline-receipt-invalid", f"protected files[{index}] binding is invalid")
        path = _required_file(Path(path_text), parent=repo_root, label=f"protected {role} input")
        if _relative(path, repo_root) != path_text:
            raise _blocked("baseline-receipt-invalid", f"protected path is not canonical: {path_text}")
        item = _snapshot(path, f"protected {role} input")
        snapshots.append(item)
        if item.sha256 != digest or item.size_bytes != size_bytes:
            raise _blocked("protected-input-drift", f"protected {role} input changed: {path_text}")
        seen.add(path_text)
        protected[role][path_text] = digest
    if not protected["source"]:
        raise _blocked("baseline-receipt-invalid", "at least one protected source is required")

    production_root = ft_root / "test-cases"
    current_paths = tuple(sorted(production_root.rglob("*.md"))) if production_root.is_dir() else ()
    current: dict[str, str] = {}
    for path in current_paths:
        item = _snapshot(path, "current canonical test case")
        snapshots.append(item)
        current[_relative(path, repo_root)] = item.sha256
    if current != protected["canonical"]:
        raise _blocked(
            "incomplete-canonical-baseline",
            "protected receipt does not bind the full current canonical test-case set",
        )
    return {
        _relative(repo_root / path, ft_root): digest
        for path, digest in sorted(protected["canonical"].items())
    }


def _verify_unchanged(snapshots: Sequence[_Snapshot]) -> None:
    for item in snapshots:
        if not item.path.is_file():
            raise _blocked("artifact-drift", f"bound artifact disappeared: {item.path}")
        if item.path.stat().st_size != item.size_bytes or sha256_path(item.path) != item.sha256:
            raise _blocked("artifact-drift", f"bound artifact changed during eligibility check: {item.path}")


def prepare_immutable_iteration_promotion(
    *,
    repo_root: Path,
    ft_root: Path,
    iteration_output_dir: Path,
    scope_slug: str,
    basis_path: Path | None = None,
) -> PromotionAdapterResult:
    """Build a read-only eligibility basis for one accepted immutable shadow.

    The adapter never publishes a candidate. It proves only that the current
    immutable iteration has a hash-bound, authentic, finding-free reviewer result
    and that the complete canonical baseline has not changed.
    """

    repo_root = repo_root.resolve()
    if not repo_root.is_dir():
        raise _blocked("repo-root-missing", f"repo_root is missing: {repo_root}")
    ft_root = _resolve_inside(ft_root, repo_root, "ft_root")
    if not ft_root.is_dir():
        raise _blocked("ft-root-missing", f"ft_root is missing: {ft_root}")
    cycle_dir = _resolve_inside(iteration_output_dir, ft_root, "iteration output directory")
    if not cycle_dir.is_dir():
        raise _blocked("iteration-output-missing", f"iteration output is missing: {cycle_dir}")
    if not isinstance(scope_slug, str) or not scope_slug.strip():
        raise _blocked("scope-missing", "scope_slug must be non-empty text")
    scope_slug = scope_slug.strip()
    snapshots: list[_Snapshot] = []

    summary_snapshot = _artifact(
        cycle_dir=cycle_dir,
        relative="iteration-summary.json",
        label="iteration summary",
        snapshots=snapshots,
    )
    summary = _json(summary_snapshot, "iteration summary")
    _accepted_summary(summary)

    draft = summary.get("draft")
    if not isinstance(draft, str) or not draft:
        raise _blocked("candidate-missing", "accepted iteration does not name its draft")
    candidate_path = _required_file(Path(draft), parent=repo_root, label="shadow candidate")
    try:
        candidate_path.relative_to(cycle_dir)
    except ValueError as exc:
        raise _blocked("candidate-outside-iteration", "shadow candidate must be inside iteration output") from exc
    candidate = _snapshot(candidate_path, "shadow candidate")
    snapshots.append(candidate)

    graph_snapshot = _artifact(
        cycle_dir=cycle_dir,
        relative="coverage-graph.json",
        label="coverage graph",
        snapshots=snapshots,
    )
    graph = _json(graph_snapshot, "coverage graph")
    graph_digest = _canonical_digest(graph)
    if graph.get("scope_slug") != scope_slug or summary.get("graph_digest") != graph_digest:
        raise _blocked("graph-mismatch", "coverage graph scope or digest differs from iteration summary")
    case_bindings = _graph_case_bindings(graph)

    gate_snapshot = _artifact(
        cycle_dir=cycle_dir,
        relative="suite-gate.json",
        label="suite gate",
        snapshots=snapshots,
    )
    gate = _json(gate_snapshot, "suite gate")
    if (
        gate.get("passed") is not True
        or gate.get("findings") != []
        or gate.get("draft_sha256") != candidate.sha256
        or gate.get("graph_digest") != graph_digest
    ):
        raise _blocked("suite-gate-mismatch", "suite gate is not a zero-finding candidate-bound pass")

    request_snapshot = _artifact(
        cycle_dir=cycle_dir,
        relative="reviewer-request.json",
        label="reviewer request",
        snapshots=snapshots,
    )
    prompt_snapshot = _artifact(
        cycle_dir=cycle_dir,
        relative="model-stages/reviewer-prompt.txt",
        label="reviewer prompt",
        snapshots=snapshots,
    )
    schema_snapshot = _artifact(
        cycle_dir=cycle_dir,
        relative="model-stages/reviewer-output-schema.json",
        label="reviewer schema",
        snapshots=snapshots,
    )
    response_snapshot = _artifact(
        cycle_dir=cycle_dir,
        relative="model-stages/reviewer-response.json",
        label="reviewer response",
        snapshots=snapshots,
    )
    request = _json(request_snapshot, "reviewer request")
    schema = _json(schema_snapshot, "reviewer schema")
    response = _json(response_snapshot, "reviewer response")
    reviewer_schema_version = _validate_reviewer_request(
        request,
        graph_digest=graph_digest,
        candidate_sha256=candidate.sha256,
        case_bindings=case_bindings,
    )
    evidence_pack_snapshot: _Snapshot | None = None
    evidence_basis_snapshot: _Snapshot | None = None
    test_designs_snapshot: _Snapshot | None = None
    if reviewer_schema_version == 2:
        evidence_pack_snapshot = _artifact(
            cycle_dir=cycle_dir,
            relative="reviewer-evidence-pack.json",
            label="reviewer evidence pack",
            snapshots=snapshots,
        )
        evidence_pack_payload = _json(evidence_pack_snapshot, "reviewer evidence pack")
        if (
            evidence_pack_payload != request.get("reviewer_evidence_pack")
            or _canonical_digest(evidence_pack_payload)
            != request.get("evidence_pack_sha256")
        ):
            raise _blocked(
                "review-evidence-pack-mismatch",
                "reviewer-evidence-pack.json differs from the hash-bound reviewer request",
            )
        evidence_basis_snapshot = _artifact(
            cycle_dir=cycle_dir,
            relative="reviewer-evidence-basis.json",
            label="reviewer evidence basis",
            snapshots=snapshots,
        )
        test_designs_snapshot = _artifact(
            cycle_dir=cycle_dir,
            relative="test-case-designs.json",
            label="test-case designs",
            snapshots=snapshots,
        )
        evidence_basis_document = _json(
            evidence_basis_snapshot,
            "reviewer evidence basis",
        )
        test_designs_document = _json(
            test_designs_snapshot,
            "test-case designs",
        )
        try:
            typed_graph = coverage_graph_from_dict(graph)
            evidence_basis = load_reviewer_evidence_basis_document(
                repo_root,
                evidence_basis_document,
            )
            designs = _test_case_designs(test_designs_document)
            candidate_markdown = candidate.raw.decode("utf-8")
            rebuilt_pack = build_reviewer_evidence_pack(
                evidence_basis,
                typed_graph,
                designs,
                candidate_markdown,
                candidate.sha256,
                reviewer_acceptance_contract(schema_version=2),
            )
        except (CoverageIoError, ReviewerEvidenceError, UnicodeError) as exc:
            raise _blocked(
                "review-evidence-rebuild-failed",
                f"cannot independently rebuild reviewer evidence: {exc}",
            ) from exc
        rebuilt_payload = rebuilt_pack.to_dict()
        if (
            rebuilt_payload != evidence_pack_payload
            or rebuilt_pack.digest != request.get("evidence_pack_sha256")
        ):
            raise _blocked(
                "review-evidence-rebuild-mismatch",
                "reviewer evidence pack differs from independently requalified inputs",
            )
    expected_image_attachments = _registered_mockup_metrics(
        request_payload=request,
        repo_root=repo_root,
        snapshots=snapshots,
    )
    expected_prompt = (
        f"{reviewer_prompt_instruction(reviewer_schema_version)}\nREQUEST JSON:\n"
        f"{_canonical_bytes(request).decode('utf-8')}\n"
    ).encode("utf-8")
    if prompt_snapshot.raw != expected_prompt:
        raise _blocked("review-prompt-mismatch", "reviewer prompt is not the exact request projection")
    expected_schema = reviewer_response_schema(
        case_bindings,
        graph_digest=graph_digest,
        draft_sha256=candidate.sha256,
        reviewer_request=request if reviewer_schema_version == 2 else None,
    )
    if schema != expected_schema:
        raise _blocked("review-schema-mismatch", "reviewer schema differs from graph-bound schema")
    _validate_reviewer_response(
        response,
        schema=schema,
        graph_digest=graph_digest,
        candidate_sha256=candidate.sha256,
        case_bindings=case_bindings,
        request_payload=request,
    )

    receipts_snapshot = _artifact(
        cycle_dir=cycle_dir,
        relative="model-stage-receipts.json",
        label="model stage receipts",
        snapshots=snapshots,
    )
    receipts = _json(receipts_snapshot, "model stage receipts")
    reviewer_receipt = _validate_receipts(
        summary=summary,
        receipt_document=receipts,
        reviewer_prompt=prompt_snapshot,
        reviewer_schema=schema_snapshot,
        reviewer_response=response_snapshot,
        request_payload=request,
        expected_image_attachments=expected_image_attachments,
    )

    protected_snapshot = _artifact(
        cycle_dir=cycle_dir,
        relative="protected-inputs.receipt.json",
        label="protected input receipt",
        snapshots=snapshots,
    )
    protected_receipt = _json(protected_snapshot, "protected input receipt")
    production_hashes = _protected_baseline(
        receipt=protected_receipt,
        repo_root=repo_root,
        ft_root=ft_root,
        snapshots=snapshots,
    )

    basis = {
        "schema_version": ELIGIBILITY_SCHEMA_VERSION,
        "artifact_kind": "immutable-promotion-eligibility",
        "eligible": True,
        "scope_slug": scope_slug,
        "iteration_dir": _relative(cycle_dir, repo_root),
        "bindings": {
            "iteration_summary": _binding(summary_snapshot, repo_root),
            "candidate": _binding(candidate, repo_root),
            "coverage_graph": {
                **_binding(graph_snapshot, repo_root),
                "graph_digest": graph_digest,
            },
            "suite_gate": _binding(gate_snapshot, repo_root),
            "protected_inputs": _binding(protected_snapshot, repo_root),
            "model_stage_receipts": _binding(receipts_snapshot, repo_root),
            "reviewer_request": _binding(request_snapshot, repo_root),
            "reviewer_prompt": _binding(prompt_snapshot, repo_root),
            "reviewer_schema": _binding(schema_snapshot, repo_root),
            "reviewer_response": _binding(response_snapshot, repo_root),
        },
        "reviewer_receipt": {
            name: reviewer_receipt[name]
            for name in (
                "backend",
                "attempts",
                "timeout_seconds",
                "tool_event_count",
                "request_sha256",
                "prompt_sha256",
                "schema_sha256",
                "response_sha256",
            )
        },
        "production_test_case_hashes": dict(production_hashes),
        "publication": "not-performed",
    }
    if evidence_pack_snapshot is not None:
        basis["bindings"]["reviewer_evidence_pack"] = _binding(
            evidence_pack_snapshot,
            repo_root,
        )
        assert evidence_basis_snapshot is not None
        assert test_designs_snapshot is not None
        basis["bindings"]["reviewer_evidence_basis"] = _binding(
            evidence_basis_snapshot,
            repo_root,
        )
        basis["bindings"]["test_case_designs"] = _binding(
            test_designs_snapshot,
            repo_root,
        )
        basis["reviewer_receipt"]["image_attachments"] = reviewer_receipt[
            "image_attachments"
        ]
    _verify_unchanged(snapshots)
    basis_path = _resolve_inside(
        basis_path or cycle_dir / "promotion-eligibility-basis.json",
        cycle_dir,
        "promotion eligibility basis",
    )
    if basis_path.exists():
        existing = _json(_snapshot(basis_path, "existing eligibility basis"), "existing eligibility basis")
        if existing != basis:
            raise _blocked("basis-conflict", "existing eligibility basis differs from current projection")
        status = "eligible-reused"
    else:
        write_json_atomic(basis_path, basis)
        status = "eligible-built"
    return PromotionAdapterResult(
        status=status,
        basis_path=basis_path,
        basis_sha256=sha256_path(basis_path),
        candidate_path=candidate.path,
        candidate_sha256=candidate.sha256,
        production_test_case_hashes=production_hashes,
    )


__all__ = [
    "ELIGIBILITY_SCHEMA_VERSION",
    "PromotionAdapterBlocked",
    "PromotionAdapterResult",
    "prepare_immutable_iteration_promotion",
]
