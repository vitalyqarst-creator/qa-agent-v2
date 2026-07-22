from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from test_case_agent.iteration_contract import (
    REVIEWER_PROMPT_INSTRUCTION,
    reviewer_acceptance_contract,
    reviewer_response_schema,
)
from test_case_agent.review_cycle.runtime import sha256_path, write_json_atomic
from test_case_agent.strict_output_schema import validate_openai_strict_output_instance


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


def _validate_reviewer_request(
    request: Mapping[str, Any],
    *,
    graph_digest: str,
    candidate_sha256: str,
    case_bindings: Sequence[tuple[str, str, str, str]],
) -> None:
    if (
        request.get("schema_version") != 1
        or request.get("graph_digest") != graph_digest
        or request.get("draft_sha256") != candidate_sha256
    ):
        raise _blocked("review-request-mismatch", "reviewer request is not bound to graph and candidate")
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


def _validate_reviewer_response(
    response: Mapping[str, Any],
    *,
    schema: Mapping[str, Any],
    graph_digest: str,
    candidate_sha256: str,
    case_bindings: Sequence[tuple[str, str, str, str]],
) -> None:
    try:
        validate_openai_strict_output_instance(response, schema)
    except ValueError as exc:
        raise _blocked("review-response-invalid", str(exc)) from exc
    if (
        response.get("schema_version") != 1
        or response.get("graph_digest") != graph_digest
        or response.get("draft_sha256") != candidate_sha256
        or response.get("decision") != "accepted"
        or response.get("findings") != []
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
        seen.add(case_key)
    if seen != set(expected):
        raise _blocked("review-response-not-accepted", "reviewer omitted graph cases")


def _validate_receipts(
    *,
    summary: Mapping[str, Any],
    receipt_document: Mapping[str, Any],
    reviewer_prompt: _Snapshot,
    reviewer_schema: _Snapshot,
    reviewer_response: _Snapshot,
    request_payload: Mapping[str, Any],
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
    _validate_reviewer_request(
        request,
        graph_digest=graph_digest,
        candidate_sha256=candidate.sha256,
        case_bindings=case_bindings,
    )
    expected_prompt = (
        f"{REVIEWER_PROMPT_INSTRUCTION}\nREQUEST JSON:\n"
        f"{_canonical_bytes(request).decode('utf-8')}\n"
    ).encode("utf-8")
    if prompt_snapshot.raw != expected_prompt:
        raise _blocked("review-prompt-mismatch", "reviewer prompt is not the exact request projection")
    expected_schema = reviewer_response_schema(
        case_bindings,
        graph_digest=graph_digest,
        draft_sha256=candidate.sha256,
    )
    if schema != expected_schema:
        raise _blocked("review-schema-mismatch", "reviewer schema differs from graph-bound schema")
    _validate_reviewer_response(
        response,
        schema=schema,
        graph_digest=graph_digest,
        candidate_sha256=candidate.sha256,
        case_bindings=case_bindings,
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
