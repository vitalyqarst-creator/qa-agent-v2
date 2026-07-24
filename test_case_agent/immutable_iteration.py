from __future__ import annotations

import copy
import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence

from test_case_agent.strict_output_schema import (
    validate_openai_strict_output_instance,
    validate_openai_strict_output_schema,
)
from test_case_agent.coverage_graph import CoverageGraph, validate_coverage_graph
from test_case_agent.iteration_contract import (
    REVIEWER_FALSIFICATION_PROBES,
    IterationContractError,
    SuiteGateReport,
    build_reviewer_request,
    build_writer_request,
    request_sha256,
    reviewer_acceptance_contract,
    reviewer_prompt_instruction,
    reviewer_response_schema,
    validate_reviewer_response,
    validate_suite,
    validate_writer_response,
    writer_response_schema,
)
from test_case_agent.reviewer_evidence import (
    ReviewerEvidenceBasis,
    ReviewerEvidenceError,
    build_reviewer_evidence_pack,
)
from test_case_agent.stage_backend import (
    CodexExecStageBackend,
    RegisteredImageInput,
    StageBackendError,
    StageResult,
    verify_registered_image_inputs,
)
from test_case_agent.review_cycle.runtime import sha256_path, write_json_atomic
from test_case_agent.test_design import (
    DesignContext,
    DesignError,
    TestCaseDesign,
    build_test_design_plan,
    render_test_cases,
)


MAX_WRITER_PROMPT_BYTES = 128 * 1024
MAX_REVIEWER_PROMPT_BYTES = 384 * 1024


class ImmutableIterationError(ValueError):
    """The deterministic-first attempt cannot continue without guessing."""


class ReviewerContextTooLarge(ImmutableIterationError):
    """The complete reviewer evidence cannot fit without forbidden truncation."""


class StageBackend(Protocol):
    def run_stage(
        self,
        *,
        stage: str,
        prompt: str,
        schema: Mapping[str, Any],
        artifact_dir: Path,
        images: tuple[RegisteredImageInput, ...] = (),
    ) -> StageResult: ...


ResponseInput = Mapping[str, Any] | Path


@dataclass(frozen=True)
class ImmutableIterationResult:
    status: str
    output_dir: Path
    draft_path: Path | None
    summary_path: Path
    test_case_count: int
    writer_model_calls: int
    reviewer_model_calls: int


@dataclass(frozen=True)
class _ProtectedFile:
    role: str
    path: Path
    relative_path: str
    sha256: str
    size_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "path": self.relative_path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }


class _PhaseTimer:
    def __init__(self) -> None:
        self.started_ns = time.perf_counter_ns()
        self.phases_ns: dict[str, int] = {}

    def phase(self, name: str):
        timer = self

        class _Context:
            def __enter__(self) -> None:
                self.started_ns = time.perf_counter_ns()

            def __exit__(self, *_: object) -> None:
                timer.phases_ns[name] = timer.phases_ns.get(name, 0) + (
                    time.perf_counter_ns() - self.started_ns
                )

        return _Context()

    def report(self) -> dict[str, Any]:
        total_ns = time.perf_counter_ns() - self.started_ns
        phase_sum_ns = sum(self.phases_ns.values())
        interphase_ns = max(0, total_ns - phase_sum_ns)
        return {
            "total_wall_ms": total_ns // 1_000_000,
            "phase_sum_ms": phase_sum_ns // 1_000_000,
            "unattributed_interphase_ms": interphase_ns // 1_000_000,
            "total_wall_ns": total_ns,
            "phase_sum_ns": phase_sum_ns,
            "unattributed_interphase_ns": interphase_ns,
            "phases_ms": {
                name: value // 1_000_000 for name, value in self.phases_ns.items()
            },
            "phases_ns": dict(self.phases_ns),
            "reconciliation": (
                "total_wall_ns = phase_sum_ns + unattributed_interphase_ns"
            ),
            "measurement_boundary": (
                "after final reconciliation and before iteration-summary serialization"
            ),
        }


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    write_json_atomic(path, value)


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def _resolve_inside_repo(path: Path, repo_root: Path, label: str) -> Path:
    candidate = path if path.is_absolute() else repo_root / path
    resolved = candidate.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise ImmutableIterationError(f"{label} is outside repo_root: {resolved}") from exc
    return resolved


def _prepare_output_dir(path: Path, repo_root: Path) -> Path:
    output_dir = _resolve_inside_repo(path, repo_root, "output_dir")
    if output_dir == repo_root:
        raise ImmutableIterationError("output_dir cannot be the repository root")
    if output_dir.exists():
        raise ImmutableIterationError(
            f"output_dir must not exist; every attempt is immutable: {output_dir}"
        )
    output_dir.mkdir(parents=True)
    return output_dir


def _snapshot_files(
    *,
    repo_root: Path,
    source_paths: Sequence[Path],
    canonical_paths: Sequence[Path],
) -> tuple[_ProtectedFile, ...]:
    if not source_paths:
        raise ImmutableIterationError(
            "protected_source_paths must register at least one source file"
        )
    snapshots: list[_ProtectedFile] = []
    seen: set[Path] = set()
    for role, paths in (("source", source_paths), ("canonical", canonical_paths)):
        for index, raw_path in enumerate(paths):
            if not isinstance(raw_path, Path):
                raise ImmutableIterationError(
                    f"protected_{role}_paths[{index}] must be a Path"
                )
            path = _resolve_inside_repo(raw_path, repo_root, f"protected {role} path")
            if path in seen:
                raise ImmutableIterationError(
                    f"protected file is registered more than once: {path}"
                )
            if not path.is_file():
                raise ImmutableIterationError(
                    f"protected {role} path is missing or not a file: {path}"
                )
            seen.add(path)
            snapshots.append(
                _ProtectedFile(
                    role=role,
                    path=path,
                    relative_path=path.relative_to(repo_root).as_posix(),
                    sha256=sha256_path(path),
                    size_bytes=path.stat().st_size,
                )
            )
    return tuple(snapshots)


def _input_drift(snapshots: Sequence[_ProtectedFile]) -> tuple[dict[str, Any], ...]:
    drift: list[dict[str, Any]] = []
    for item in snapshots:
        if not item.path.is_file():
            drift.append(
                {
                    "role": item.role,
                    "path": item.relative_path,
                    "expected_sha256": item.sha256,
                    "actual_sha256": "missing",
                }
            )
            continue
        actual = sha256_path(item.path)
        if actual != item.sha256:
            drift.append(
                {
                    "role": item.role,
                    "path": item.relative_path,
                    "expected_sha256": item.sha256,
                    "actual_sha256": actual,
                }
            )
    return tuple(drift)


def _context_payload(context: DesignContext) -> dict[str, Any]:
    return {
        "package_id": context.package_id,
        "scope_title": context.scope_title,
        "base_preconditions": list(context.base_preconditions),
        "subject_labels": dict(sorted(context.subject_labels.items())),
        "condition_preconditions": dict(
            sorted(context.condition_preconditions.items())
        ),
        "priorities": dict(sorted((context.priorities or {}).items())),
    }


def _stage_prompt(stage: str, request: Mapping[str, Any]) -> str:
    if stage == "writer":
        instruction = (
            "Return JSON only. For every card, return only its registered subject, "
            "expected-result, fixture, data, and ordered action identifiers. Do not "
            "author case prose or add identifiers that are absent from the card."
        )
    elif stage == "reviewer":
        raw_version = request.get("schema_version")
        if type(raw_version) is not int:
            raise ImmutableIterationError(
                "reviewer request schema_version must be an integer"
            )
        instruction = reviewer_prompt_instruction(raw_version)
    else:  # pragma: no cover - the runner owns its two-stage call graph
        raise ImmutableIterationError(f"unsupported model stage: {stage}")
    return f"{instruction}\nREQUEST JSON:\n{_json_bytes(request).decode('utf-8')}\n"


def _load_precomputed_response(
    response: ResponseInput,
    *,
    repo_root: Path,
) -> dict[str, Any]:
    if isinstance(response, Mapping):
        payload: Any = dict(response)
    elif isinstance(response, Path):
        path = _resolve_inside_repo(response, repo_root, "precomputed response")
        if not path.is_file():
            raise ImmutableIterationError(
                f"precomputed response is missing or not a file: {path}"
            )
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        raise ImmutableIterationError(
            "precomputed response must be a JSON object or repository Path"
        )
    if not isinstance(payload, dict):
        raise ImmutableIterationError("precomputed response root must be a JSON object")
    return payload


def _upgrade_precomputed_reviewer_response(
    payload: Mapping[str, Any],
    *,
    request: Mapping[str, Any],
) -> tuple[dict[str, Any], bool]:
    """Adapt a clean recorded v1 response for an offline v2 replay only."""

    if request.get("schema_version") != 2 or payload.get("schema_version") != 1:
        return dict(payload), False
    expected_fields = {
        "schema_version",
        "graph_digest",
        "draft_sha256",
        "decision",
        "case_results",
        "findings",
        "summary",
    }
    if set(payload) != expected_fields:
        raise ImmutableIterationError(
            "legacy reviewer response cannot be adapted because its fields differ"
        )
    findings = payload.get("findings")
    if not isinstance(findings, list):
        raise ImmutableIterationError(
            "legacy reviewer findings must be an array"
        )
    case_results = payload.get("case_results")
    if not isinstance(case_results, list) or any(
        not isinstance(item, Mapping) for item in case_results
    ):
        raise ImmutableIterationError(
            "legacy reviewer case_results must be an array of objects"
        )
    legacy_case_result_fields = {
        "case_key",
        "tc_id",
        "obligation_id",
        "status",
        "comment",
    }
    for index, item in enumerate(case_results):
        if (
            set(item) != legacy_case_result_fields
            or any(
                not isinstance(item.get(name), str) or not item[name].strip()
                for name in ("case_key", "tc_id", "obligation_id", "status")
            )
            or not isinstance(item.get("comment"), str)
        ):
            raise ImmutableIterationError(
                f"legacy reviewer case result {index} fields are invalid"
            )
    if (
        payload.get("graph_digest") != request.get("graph_digest")
        or payload.get("draft_sha256") != request.get("draft_sha256")
    ):
        raise ImmutableIterationError(
            "legacy reviewer response is not bound to the v2 graph and draft"
        )
    evidence_pack_sha256 = request.get("evidence_pack_sha256")
    if not isinstance(evidence_pack_sha256, str) or not evidence_pack_sha256:
        raise ImmutableIterationError("v2 reviewer request omits evidence pack digest")
    pack = request.get("reviewer_evidence_pack")
    mapping = pack.get("coverage_mapping") if isinstance(pack, Mapping) else None
    if not isinstance(mapping, list):
        raise ImmutableIterationError("v2 reviewer request omits coverage mapping")
    test_cases = pack.get("test_cases") if isinstance(pack, Mapping) else None
    raw_designs = test_cases.get("designs") if isinstance(test_cases, Mapping) else None
    if not isinstance(raw_designs, list):
        raise ImmutableIterationError("v2 reviewer request omits test-case designs")
    designs_by_case: dict[str, tuple[str, str]] = {}
    for index, raw_design in enumerate(raw_designs):
        steps = raw_design.get("steps") if isinstance(raw_design, Mapping) else None
        expected_result = (
            raw_design.get("expected_result")
            if isinstance(raw_design, Mapping)
            else None
        )
        case_key = raw_design.get("case_key") if isinstance(raw_design, Mapping) else None
        if (
            not isinstance(case_key, str)
            or not case_key
            or case_key in designs_by_case
            or not isinstance(steps, list)
            or not steps
            or any(not isinstance(step, str) or not step.strip() for step in steps)
            or not isinstance(expected_result, str)
            or not expected_result.strip()
        ):
            raise ImmutableIterationError(
                f"v2 reviewer test-case design {index} cannot bind legacy probes"
            )
        designs_by_case[case_key] = (steps[-1], expected_result)
    upgraded_findings: list[dict[str, Any]] = []
    legacy_fields = {
        "severity",
        "case_key",
        "tc_id",
        "obligation_id",
        "message",
    }
    for index, raw in enumerate(findings):
        if not isinstance(raw, Mapping) or set(raw) != legacy_fields:
            raise ImmutableIterationError(
                f"legacy reviewer finding {index} cannot be classified safely"
            )
        matches = [
            item
            for item in mapping
            if isinstance(item, Mapping)
            and item.get("case_key") == raw.get("case_key")
            and item.get("tc_id") == raw.get("tc_id")
            and item.get("obligation_id") == raw.get("obligation_id")
        ]
        chains = {
            tuple(
                item.get(name)
                for name in (
                    "source_row_id",
                    "assertion_id",
                    "property_id",
                    "obligation_id",
                    "case_key",
                    "tc_id",
                )
            )
            for item in matches
        }
        if len(chains) != 1:
            raise ImmutableIterationError(
                f"legacy reviewer finding {index} has no unique v2 evidence chain"
            )
        chain = next(iter(chains))
        if any(not isinstance(value, str) or not value for value in chain):
            raise ImmutableIterationError(
                f"legacy reviewer finding {index} has an incomplete v2 evidence chain"
            )
        upgraded_findings.append(
            {
                "severity": raw["severity"],
                "finding_type": "test-case-defect",
                "binding_role": "primary",
                "falsification_probe": "",
                "source_row_id": chain[0],
                "assertion_id": chain[1],
                "property_id": chain[2],
                "obligation_id": chain[3],
                "case_key": chain[4],
                "tc_id": chain[5],
                "message": raw["message"],
            }
        )
    upgraded_case_results: list[dict[str, Any]] = []
    for index, item in enumerate(case_results):
        case_key = item.get("case_key")
        basis = designs_by_case.get(case_key) if isinstance(case_key, str) else None
        if basis is None:
            raise ImmutableIterationError(
                f"legacy reviewer case result {index} has no bound v2 design"
            )
        trigger_or_step, oracle = basis
        upgraded_case_results.append(
            {
                **item,
                "falsification": {
                    probe: {
                        "outcome": "not-recorded",
                        "detail": (
                            "Legacy v1 response did not record this "
                            "falsification probe."
                        ),
                        "binding_role": "primary",
                        "obligation_id": item["obligation_id"],
                        "binding_item_index": -1,
                        "trigger_or_step": trigger_or_step,
                        "oracle": oracle,
                    }
                    for probe in REVIEWER_FALSIFICATION_PROBES
                },
            }
        )
    return (
        {
            "schema_version": 2,
            "graph_digest": payload["graph_digest"],
            "draft_sha256": payload["draft_sha256"],
            "evidence_pack_sha256": evidence_pack_sha256,
            "decision": payload["decision"],
            "case_results": upgraded_case_results,
            "source_projection_findings": [],
            "test_case_findings": upgraded_findings,
            "summary": payload["summary"],
        },
        True,
    )


def _normalize_stage_receipt(
    *,
    stage: str,
    raw: Mapping[str, Any],
    expected_attempts: int,
    stage_wall_ms: int,
    prompt_path: Path,
    schema_path: Path,
    response_path: Path,
    request: Mapping[str, Any],
    images: tuple[RegisteredImageInput, ...],
) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise ImmutableIterationError(f"{stage} backend receipt must be an object")
    if raw.get("stage") != stage:
        raise ImmutableIterationError(
            f"{stage} backend receipt is bound to a different stage"
        )
    attempts = raw.get("attempts", expected_attempts)
    if type(attempts) is not int or attempts != expected_attempts:
        raise ImmutableIterationError(
            f"{stage} backend receipt must attest exactly {expected_attempts} attempt(s)"
        )
    if "timeout_seconds" not in raw or raw.get("timeout_seconds") is not None:
        raise ImmutableIterationError(f"{stage} model stage used a forbidden hard timeout")
    duration_ms = raw.get("duration_ms", stage_wall_ms)
    if type(duration_ms) is not int or duration_ms < 0:
        raise ImmutableIterationError(f"{stage} receipt duration_ms is invalid")
    output_artifacts = raw.get("output_artifacts")
    if not isinstance(output_artifacts, Mapping):
        output_artifacts = {"count": 1, "bytes": response_path.stat().st_size}
    output_count = output_artifacts.get("count", 1)
    output_bytes = output_artifacts.get("bytes", response_path.stat().st_size)
    if (
        type(output_count) is not int
        or output_count < 1
        or type(output_bytes) is not int
        or output_bytes < response_path.stat().st_size
    ):
        raise ImmutableIterationError(f"{stage} output artifact receipt is invalid")
    tool_event_count = raw.get("tool_event_count", 0)
    if type(tool_event_count) is not int or tool_event_count != 0:
        raise ImmutableIterationError(
            f"{stage} receipt reports forbidden model tool events"
        )
    expected_image_count = len(images)
    expected_image_bytes = sum(item.size_bytes for item in images)
    raw_images = raw.get("image_attachments")
    if raw_images is None:
        if expected_image_count:
            raise ImmutableIterationError(
                f"{stage} receipt omits transported image attachments"
            )
        raw_images = {"count": 0, "bytes": 0}
    if (
        not isinstance(raw_images, Mapping)
        or raw_images.get("count") != expected_image_count
        or raw_images.get("bytes") != expected_image_bytes
    ):
        raise ImmutableIterationError(
            f"{stage} image attachment receipt differs from verified inputs"
        )
    tokens = raw.get("tokens", "unavailable")
    if tokens == "unavailable":
        normalized_tokens: Mapping[str, Any] | str = "unavailable"
    elif isinstance(tokens, Mapping):
        if not tokens:
            raise ImmutableIterationError(
                f"{stage} token usage must be unavailable or a non-empty usage object"
            )
        normalized: dict[str, int] = {}
        for name, value in tokens.items():
            if not isinstance(name, str) or not name.strip():
                raise ImmutableIterationError(
                    f"{stage} token usage contains an invalid metric name"
                )
            if type(value) is not int or value < 0:
                raise ImmutableIterationError(
                    f"{stage} token metric {name!r} must be a nonnegative integer"
                )
            normalized[name] = value
        normalized_tokens = normalized
    else:
        raise ImmutableIterationError(
            f"{stage} tokens must be a non-empty usage object or unavailable"
        )
    token_usage = {
        name: (
            normalized_tokens.get(name, "unavailable")
            if isinstance(normalized_tokens, Mapping)
            else "unavailable"
        )
        for name in ("input_tokens", "output_tokens", "reasoning_tokens")
    }
    result = {
        "stage": stage,
        "backend": str(raw.get("backend", "unknown")),
        "attempts": attempts,
        "duration_ms": duration_ms,
        "stage_wall_ms": stage_wall_ms,
        "tokens": normalized_tokens,
        "token_usage": token_usage,
        "tool_event_count": tool_event_count,
        "timeout_seconds": None,
        "request_sha256": request_sha256(request),
        "prompt_sha256": sha256_path(prompt_path),
        "schema_sha256": sha256_path(schema_path),
        "response_sha256": sha256_path(response_path),
        "input_artifacts": {
            "count": 2 + expected_image_count,
            "bytes": (
                prompt_path.stat().st_size
                + schema_path.stat().st_size
                + expected_image_bytes
            ),
            "prompt_bytes": prompt_path.stat().st_size,
            "schema_bytes": schema_path.stat().st_size,
            "request_bytes": len(_json_bytes(request)),
        },
        "image_attachments": {
            "count": expected_image_count,
            "bytes": expected_image_bytes,
        },
        "output_artifacts": {
            "count": output_count,
            "bytes": output_bytes,
            "response_bytes": response_path.stat().st_size,
        },
    }
    for name in (
        "capability_probe_ms",
        "codex_version",
        "precomputed_schema_upgrade",
    ):
        if name in raw:
            result[name] = raw[name]
    return result


def _zero_writer_receipt(request: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "stage": "writer",
        "backend": "deterministic-zero-call",
        "attempts": 0,
        "duration_ms": 0,
        "stage_wall_ms": 0,
        "tokens": "unavailable",
        "token_usage": {
            "input_tokens": "unavailable",
            "output_tokens": "unavailable",
            "reasoning_tokens": "unavailable",
        },
        "tool_event_count": 0,
        "timeout_seconds": None,
        "request_sha256": request_sha256(request),
        "response_sha256": "unavailable",
        "input_artifacts": {"count": 0, "bytes": 0, "request_bytes": 0},
        "image_attachments": {"count": 0, "bytes": 0},
        "output_artifacts": {"count": 0, "bytes": 0, "response_bytes": 0},
    }


def _run_stage(
    *,
    stage: str,
    request: Mapping[str, Any],
    schema: Mapping[str, Any],
    output_dir: Path,
    repo_root: Path,
    backend: StageBackend,
    precomputed: ResponseInput | None,
    on_model_call: Callable[[], None],
    images: tuple[RegisteredImageInput, ...] = (),
) -> tuple[dict[str, Any], dict[str, Any], bool]:
    try:
        validate_openai_strict_output_schema(schema)
    except ValueError as exc:
        raise ImmutableIterationError(f"{stage} schema is invalid: {exc}") from exc
    prompt = _stage_prompt(stage, request)
    limit = MAX_WRITER_PROMPT_BYTES if stage == "writer" else MAX_REVIEWER_PROMPT_BYTES
    prompt_size = len(prompt.encode("utf-8"))
    if prompt_size > limit:
        message = f"{stage} prompt exceeds compact limit: {prompt_size} > {limit} bytes"
        if stage == "reviewer":
            raise ReviewerContextTooLarge(message)
        raise ImmutableIterationError(message)
    model_dir = output_dir / "model-stages"
    prompt_path = model_dir / f"{stage}-prompt.txt"
    schema_path = model_dir / f"{stage}-output-schema.json"
    response_path = model_dir / f"{stage}-response.json"
    _write_text(prompt_path, prompt)
    _write_json(schema_path, dict(schema))
    started_ns = time.perf_counter_ns()
    precomputed_schema_upgrade = False
    if precomputed is not None:
        payload = _load_precomputed_response(precomputed, repo_root=repo_root)
        if stage == "reviewer":
            payload, precomputed_schema_upgrade = (
                _upgrade_precomputed_reviewer_response(payload, request=request)
            )
        raw_receipt: Mapping[str, Any] = {
            "stage": stage,
            "backend": "precomputed-response",
            "attempts": 0,
            "duration_ms": (time.perf_counter_ns() - started_ns) // 1_000_000,
            "tokens": "unavailable",
            "tool_event_count": 0,
            "timeout_seconds": None,
            "image_attachments": {"count": 0, "bytes": 0},
        }
        if precomputed_schema_upgrade:
            raw_receipt = {
                **raw_receipt,
                "precomputed_schema_upgrade": (
                    "reviewer-v1-to-v2-bound-findings-and-unrecorded-falsification"
                ),
            }
        called_model = False
        expected_attempts = 0
        transported_images: tuple[RegisteredImageInput, ...] = ()
    else:
        if getattr(backend, "timeout_seconds", None) is not None:
            raise ImmutableIterationError(
                f"{stage} backend declares a forbidden hard model timeout"
            )
        on_model_call()
        stage_kwargs: dict[str, Any] = {
            "stage": stage,
            "prompt": prompt,
            "schema": schema,
            "artifact_dir": model_dir,
        }
        if images:
            stage_kwargs["images"] = images
        result = backend.run_stage(**stage_kwargs)
        if not isinstance(result, StageResult):
            raise ImmutableIterationError(f"{stage} backend returned an invalid StageResult")
        payload = result.payload
        raw_receipt = result.receipt
        called_model = True
        expected_attempts = 1
        transported_images = images
    stage_wall_ms = (time.perf_counter_ns() - started_ns) // 1_000_000
    instance_schema = schema
    if precomputed_schema_upgrade:
        instance_schema = copy.deepcopy(schema)
        try:
            probe_schemas = instance_schema["properties"]["case_results"][
                "items"
            ]["properties"]["falsification"]["properties"]
            for probe in REVIEWER_FALSIFICATION_PROBES:
                outcomes = probe_schemas[probe]["properties"]["outcome"]["enum"]
                if "not-recorded" not in outcomes:
                    outcomes.append("not-recorded")
        except (KeyError, TypeError, AttributeError) as exc:  # pragma: no cover
            raise ImmutableIterationError(
                "legacy reviewer adapter cannot extend the v2 falsification schema"
            ) from exc
        try:
            validate_openai_strict_output_schema(instance_schema)
        except ValueError as exc:  # pragma: no cover - live schema already validated
            raise ImmutableIterationError(
                f"legacy reviewer adapter produced an invalid schema: {exc}"
            ) from exc
        _write_json(schema_path, dict(instance_schema))
    try:
        validate_openai_strict_output_instance(payload, instance_schema)
    except ValueError as exc:
        raise ImmutableIterationError(
            f"{stage} response failed strict schema validation: {exc}"
        ) from exc
    if called_model and response_path.is_file():
        try:
            persisted_payload = json.loads(response_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ImmutableIterationError(
                f"{stage} backend response artifact is not valid JSON: {exc}"
            ) from exc
        if persisted_payload != payload:
            raise ImmutableIterationError(
                f"{stage} backend response artifact differs from StageResult.payload"
            )
    else:
        _write_json(response_path, payload)
    receipt = _normalize_stage_receipt(
        stage=stage,
        raw=raw_receipt,
        expected_attempts=expected_attempts,
        stage_wall_ms=stage_wall_ms,
        prompt_path=prompt_path,
        schema_path=schema_path,
        response_path=response_path,
        request=request,
        images=transported_images,
    )
    return payload, receipt, called_model


def _artifact_inventory(output_dir: Path) -> list[str]:
    values = [
        path.relative_to(output_dir).as_posix()
        for path in output_dir.rglob("*")
        if path.is_file() and ".tmp" not in path.name
    ]
    if "iteration-summary.json" not in values:
        values.append("iteration-summary.json")
    return sorted(values)


def run_immutable_iteration(
    *,
    repo_root: Path,
    graph: CoverageGraph,
    context: DesignContext,
    output_dir: Path,
    protected_source_paths: Sequence[Path],
    protected_canonical_paths: Sequence[Path] = (),
    writer_response: ResponseInput | None = None,
    reviewer_response: ResponseInput | None = None,
    reviewer_evidence_basis: ReviewerEvidenceBasis | None = None,
    backend: StageBackend | None = None,
) -> ImmutableIterationResult:
    """Run one immutable deterministic-first shadow iteration.

    The runner has no retry loop and no promotion path. It calls writer at most once
    for non-deterministic cards and reviewer at most once after a green suite gate.
    """

    repo_root = repo_root.resolve()
    if not repo_root.is_dir():
        raise ImmutableIterationError(f"repo_root is missing: {repo_root}")
    output_dir = _prepare_output_dir(output_dir, repo_root)
    timer = _PhaseTimer()
    active_backend = backend or CodexExecStageBackend(timeout_seconds=None)
    protected: tuple[_ProtectedFile, ...] = ()
    model_receipts: list[dict[str, Any]] = []
    draft_path: Path | None = None
    gate: SuiteGateReport | None = None
    writer_model_calls = 0
    reviewer_model_calls = 0
    reviewer_decision = "not-run"
    reviewer_accepted = False
    test_case_count = 0
    protected_inputs_unchanged = True
    writer_request: Mapping[str, Any] | None = None
    reviewer_request: Mapping[str, Any] | None = None
    reviewer_images: tuple[RegisteredImageInput, ...] = ()
    reviewer_evidence_pack_sha256 = ""
    reviewer_source_row_count = 0
    reviewer_dictionary_count = 0
    reviewer_registered_image_count = 0
    reviewer_registered_image_bytes = 0
    calibration_pending_count = sum(
        item.status == "candidate-ui-calibration" for item in graph.cases
    )

    def record_writer_call() -> None:
        nonlocal writer_model_calls
        writer_model_calls += 1
        if writer_model_calls > 1:
            raise ImmutableIterationError("writer call cap exceeded")

    def record_reviewer_call() -> None:
        nonlocal reviewer_model_calls
        reviewer_model_calls += 1
        if reviewer_model_calls > 1:
            raise ImmutableIterationError("reviewer call cap exceeded")

    def record_unreceipted_attempts() -> None:
        receipted = {
            item.get("stage")
            for item in model_receipts
            if item.get("attempts") == 1
        }
        for stage, calls, request in (
            ("writer", writer_model_calls, writer_request),
            ("reviewer", reviewer_model_calls, reviewer_request),
        ):
            if calls != 1 or stage in receipted or request is None:
                continue
            model_dir = output_dir / "model-stages"
            prompt_path = model_dir / f"{stage}-prompt.txt"
            schema_path = model_dir / f"{stage}-output-schema.json"
            output_paths = tuple(
                path
                for suffix in ("response.json", "events.jsonl", "stderr.txt")
                if (path := model_dir / f"{stage}-{suffix}").is_file()
            )
            input_paths = tuple(
                path for path in (prompt_path, schema_path) if path.is_file()
            )
            stage_images = reviewer_images if stage == "reviewer" else ()
            response_path = model_dir / f"{stage}-response.json"
            model_receipts.append(
                {
                    "stage": stage,
                    "backend": "attempt-ended-without-stage-receipt",
                    "attempts": 1,
                    "duration_ms": timer.phases_ns.get(stage, 0) // 1_000_000,
                    "stage_wall_ms": timer.phases_ns.get(stage, 0) // 1_000_000,
                    "tokens": "unavailable",
                    "token_usage": {
                        "input_tokens": "unavailable",
                        "output_tokens": "unavailable",
                        "reasoning_tokens": "unavailable",
                    },
                    "tool_event_count": "unavailable",
                    "timeout_seconds": None,
                    "request_sha256": request_sha256(request),
                    "response_sha256": (
                        sha256_path(response_path)
                        if response_path.is_file()
                        else "unavailable"
                    ),
                    "input_artifacts": {
                        "count": len(input_paths) + len(stage_images),
                        "bytes": (
                            sum(path.stat().st_size for path in input_paths)
                            + sum(item.size_bytes for item in stage_images)
                        ),
                    },
                    "image_attachments": {
                        "count": len(stage_images),
                        "bytes": sum(item.size_bytes for item in stage_images),
                    },
                    "output_artifacts": {
                        "count": len(output_paths),
                        "bytes": sum(path.stat().st_size for path in output_paths),
                    },
                }
            )

    def finish(status: str, *, error: str = "") -> ImmutableIterationResult:
        nonlocal protected_inputs_unchanged, reviewer_accepted
        with timer.phase("final-reconciliation"):
            record_unreceipted_attempts()
            _write_json(
                output_dir / "model-stage-receipts.json",
                {"schema_version": 1, "stages": model_receipts},
            )
            drift = _input_drift(protected)
            protected_inputs_unchanged = not bool(drift)
            if drift:
                status = "blocked-input-drift"
                error = "protected source or canonical input changed during the attempt"
                reviewer_accepted = False
                _write_json(
                    output_dir / "input-drift.json",
                    {"schema_version": 1, "drift": list(drift)},
                )
            if status in {
                "accepted-shadow",
                "accepted-with-calibration-pending",
            } and (
                gate is None or not gate.passed or not reviewer_accepted
            ):
                status = "blocked-contract"
                error = "accepted terminal invariant failed"
            if (
                status == "accepted-shadow" and calibration_pending_count
            ) or (
                status == "accepted-with-calibration-pending"
                and not calibration_pending_count
            ):
                status = "blocked-contract"
                error = "accepted calibration status invariant failed"
        timing = timer.report()
        summary = {
            "schema_version": 1,
            "mode": "immutable-deterministic-first",
            "status": status,
            "error": error,
            "graph_digest": graph.digest,
            "test_case_count": test_case_count,
            "draft": (
                draft_path.relative_to(repo_root).as_posix()
                if draft_path is not None
                else None
            ),
            "writer_model_calls": writer_model_calls,
            "reviewer_model_calls": reviewer_model_calls,
            "reviewer_decision": reviewer_decision,
            "reviewer_accepted_zero_findings": reviewer_accepted,
            "reviewer_evidence_pack_sha256": (
                reviewer_evidence_pack_sha256 or None
            ),
            "reviewer_source_row_count": reviewer_source_row_count,
            "reviewer_dictionary_count": reviewer_dictionary_count,
            "reviewer_registered_image_count": reviewer_registered_image_count,
            "reviewer_registered_image_bytes": reviewer_registered_image_bytes,
            "calibration_pending_count": calibration_pending_count,
            "suite_gate_passed": bool(gate and gate.passed),
            "protected_inputs_unchanged": protected_inputs_unchanged,
            "canonical_publication": "not-performed",
            "promotion": "out-of-scope",
            "root_agent_token_usage": {
                "availability": "unavailable",
                "input_tokens": "unavailable",
                "output_tokens": "unavailable",
                "reasoning_tokens": "unavailable",
            },
            "orchestration_token_usage": {
                "availability": "unavailable",
                "input_tokens": "unavailable",
                "output_tokens": "unavailable",
                "reasoning_tokens": "unavailable",
            },
            "model_stages": model_receipts,
            "timing": timing,
            "artifacts": _artifact_inventory(output_dir),
        }
        if status == "accepted-with-calibration-pending":
            summary.update(
                {
                    "promotion_eligible": False,
                    "non_promotable_reason": "calibration-pending",
                }
            )
        summary_path = output_dir / "iteration-summary.json"
        _write_json(summary_path, summary)
        return ImmutableIterationResult(
            status=status,
            output_dir=output_dir,
            draft_path=draft_path,
            summary_path=summary_path,
            test_case_count=test_case_count,
            writer_model_calls=writer_model_calls,
            reviewer_model_calls=reviewer_model_calls,
        )

    try:
        with timer.phase("request-validation"):
            if not isinstance(graph, CoverageGraph):
                raise ImmutableIterationError("graph must be a CoverageGraph")
            if reviewer_evidence_basis is not None and not isinstance(
                reviewer_evidence_basis, ReviewerEvidenceBasis
            ):
                raise ImmutableIterationError(
                    "reviewer_evidence_basis must be a ReviewerEvidenceBasis"
                )
            graph_findings = validate_coverage_graph(graph)
            graph_errors = [item for item in graph_findings if item.severity == "error"]
            if graph_errors:
                raise ImmutableIterationError(
                    "coverage graph is invalid: "
                    + "; ".join(item.finding_id for item in graph_errors)
                )
            context.validate()
            protected = _snapshot_files(
                repo_root=repo_root,
                source_paths=protected_source_paths,
                canonical_paths=protected_canonical_paths,
            )
            _write_json(output_dir / "coverage-graph.json", graph.to_dict())
            _write_json(output_dir / "design-context.json", _context_payload(context))
            _write_json(
                output_dir / "protected-inputs.receipt.json",
                {
                    "schema_version": 1,
                    "files": [item.to_dict() for item in protected],
                },
            )

        with timer.phase("deterministic-design"):
            plan = build_test_design_plan(graph, context=context)
            _write_json(output_dir / "test-design-plan.json", plan.to_dict())
            evidence_access = {
                "schema_version": 1,
                "graph_digest": graph.digest,
                "registered_context_only": True,
                "protected_sources": [
                    item.to_dict() for item in protected if item.role == "source"
                ],
                "protected_canonical": [
                    item.to_dict() for item in protected if item.role == "canonical"
                ],
                "source_file_content_in_model_context": (
                    reviewer_evidence_basis is not None
                ),
                "source_file_content_mode": (
                    "bounded-literal-scope-elements"
                    if reviewer_evidence_basis is not None
                    else "not-provided"
                ),
                "canonical_file_content_in_model_context": False,
                "old_test_cases_in_model_context": False,
                "benchmark_context_in_model_context": False,
                "review_history_in_model_context": False,
                "writer_context": "typed writer cards only",
                "reviewer_context": (
                    "complete ReviewerEvidencePack v2 literal scope evidence"
                    if reviewer_evidence_basis is not None
                    else "compact source/obligation/case projection only"
                ),
                "runner_owned_fields": [
                    "tc_id",
                    "traceability",
                    "priority",
                    "preconditions",
                    "expected_result",
                    "postconditions",
                    "calibration_status",
                ],
                "model_tool_access": False,
                "command_budget": 0,
                "writer_cards": len(plan.writer_cards),
                "blocked_cards": len(plan.blocked_cards),
                "writer_precomputed": writer_response is not None,
                "reviewer_precomputed": reviewer_response is not None,
            }
            _write_json(output_dir / "evidence-access-report.json", evidence_access)
            if plan.blocked_cards:
                _write_json(
                    output_dir / "blocked-cards.json",
                    {
                        "schema_version": 1,
                        "cards": [item.to_dict() for item in plan.blocked_cards],
                    },
                )
        if plan.blocked_cards:
            return finish(
                "blocked-design",
                error="typed design contains blocked cards; model stages were not run",
            )
        if _input_drift(protected):
            return finish(
                "blocked-input-drift",
                error="protected inputs changed before model execution",
            )

        writer_request = build_writer_request(graph, plan)
        _write_json(output_dir / "writer-request.json", writer_request)
        writer_cases: tuple[TestCaseDesign, ...] = ()
        if plan.writer_cards:
            with timer.phase("writer"):
                schema = writer_response_schema(plan.writer_cards, graph.digest)
                payload, receipt, called_model = _run_stage(
                    stage="writer",
                    request=writer_request,
                    schema=schema,
                    output_dir=output_dir,
                    repo_root=repo_root,
                    backend=active_backend,
                    precomputed=writer_response,
                    on_model_call=record_writer_call,
                )
                if called_model != (writer_response is None):  # pragma: no cover
                    raise ImmutableIterationError("writer call accounting mismatch")
                model_receipts.append(receipt)
                writer_cases, unresolved = validate_writer_response(
                    payload,
                    graph=graph,
                    plan=plan,
                    context=context,
                )
                if unresolved:
                    _write_json(
                        output_dir / "writer-unresolved.json",
                        {"schema_version": 1, "cards": list(unresolved)},
                    )
            if _input_drift(protected):
                return finish("blocked-input-drift")
            if unresolved:
                return finish(
                    "blocked-writer-unresolved",
                    error="writer returned unresolved cards; no reviewer was run",
                )
        else:
            if writer_response is not None:
                raise ImmutableIterationError(
                    "writer_response was provided but deterministic design requires zero writer calls"
                )
            model_receipts.append(_zero_writer_receipt(writer_request))

        with timer.phase("render-and-gate"):
            cases = tuple(
                sorted(
                    (*plan.deterministic_cases, *writer_cases),
                    key=lambda item: item.case_key,
                )
            )
            markdown = render_test_cases(cases, scope_title=context.scope_title)
            draft_path = output_dir / "shadow-test-cases.md"
            _write_text(draft_path, markdown)
            _write_json(
                output_dir / "test-case-designs.json",
                {
                    "schema_version": 1,
                    "cases": [item.to_dict() for item in cases],
                },
            )
            gate = validate_suite(
                graph=graph,
                cases=cases,
                markdown=markdown,
                checked_path=str(draft_path),
            )
            _write_json(output_dir / "suite-gate.json", gate.to_dict())
            test_case_count = gate.actual_case_count
        if not gate.passed:
            return finish(
                "blocked-suite-gate",
                error="runner-owned suite gate rejected the shadow draft",
            )
        if _input_drift(protected):
            return finish(
                "blocked-input-drift",
                error="protected inputs changed before reviewer execution",
            )

        if reviewer_evidence_basis is not None:
            _write_json(
                output_dir / "reviewer-evidence-basis.json",
                reviewer_evidence_basis.to_document(),
            )
            evidence_pack = build_reviewer_evidence_pack(
                reviewer_evidence_basis,
                graph,
                cases,
                markdown,
                gate.draft_sha256,
                reviewer_acceptance_contract(schema_version=2),
            )
            evidence_payload = evidence_pack.to_dict()
            _write_json(output_dir / "reviewer-evidence-pack.json", evidence_payload)
            reviewer_request = build_reviewer_request(
                graph=graph,
                cases=cases,
                gate=gate,
                evidence_pack=evidence_pack,
            )
            reviewer_evidence_pack_sha256 = evidence_pack.digest
            reviewer_source_row_count = len(
                evidence_payload["literal_source_evidence"]
            )
            reviewer_dictionary_count = len(evidence_payload["dictionaries"])
            mockup_attachments = evidence_payload["mockup_attachments"]
            image_paths = evidence_pack.image_paths
            if len(image_paths) != len(mockup_attachments):  # pragma: no cover
                raise ImmutableIterationError(
                    "reviewer evidence mockup paths differ from attachment metadata"
                )
            reviewer_images = verify_registered_image_inputs(
                tuple(
                    RegisteredImageInput(
                        path=path,
                        sha256=attachment["sha256"],
                        size_bytes=attachment["size_bytes"],
                    )
                    for path, attachment in zip(
                        image_paths,
                        mockup_attachments,
                        strict=True,
                    )
                )
            )
            reviewer_registered_image_count = len(reviewer_images)
            reviewer_registered_image_bytes = sum(
                item.size_bytes for item in reviewer_images
            )
            evidence_access.update(
                {
                    "reviewer_evidence_schema_version": 2,
                    "reviewer_evidence_pack_sha256": (
                        reviewer_evidence_pack_sha256
                    ),
                    "reviewer_source_row_count": reviewer_source_row_count,
                    "reviewer_dictionary_count": reviewer_dictionary_count,
                    "reviewer_registered_image_count": (
                        reviewer_registered_image_count
                    ),
                    "reviewer_registered_image_bytes": (
                        reviewer_registered_image_bytes
                    ),
                }
            )
            _write_json(output_dir / "evidence-access-report.json", evidence_access)
        else:
            reviewer_request = build_reviewer_request(
                graph=graph,
                cases=cases,
                gate=gate,
            )
        _write_json(output_dir / "reviewer-request.json", reviewer_request)
        case_bindings = [
            (item.case_key, item.tc_id, item.obligation_ids[0], item.status)
            for item in graph.cases
        ]
        with timer.phase("reviewer"):
            schema = reviewer_response_schema(
                case_bindings,
                graph_digest=graph.digest,
                draft_sha256=gate.draft_sha256,
                reviewer_request=reviewer_request,
            )
            payload, receipt, called_model = _run_stage(
                stage="reviewer",
                request=reviewer_request,
                schema=schema,
                output_dir=output_dir,
                repo_root=repo_root,
                backend=active_backend,
                precomputed=reviewer_response,
                on_model_call=record_reviewer_call,
                images=reviewer_images,
            )
            if called_model != (reviewer_response is None):  # pragma: no cover
                raise ImmutableIterationError("reviewer call accounting mismatch")
            model_receipts.append(receipt)
            reviewer_accepted, reviewer_decision = validate_reviewer_response(
                payload,
                graph=graph,
                draft_sha256=gate.draft_sha256,
                reviewer_request=reviewer_request,
                allow_legacy_unrecorded_falsification=(
                    receipt.get("precomputed_schema_upgrade")
                    == "reviewer-v1-to-v2-bound-findings-and-unrecorded-falsification"
                ),
            )
        if _input_drift(protected):
            return finish("blocked-input-drift")
        if not reviewer_accepted:
            return finish(
                f"review-{reviewer_decision}",
                error="reviewer did not accept the gate-passed shadow draft",
            )
        return finish(
            "accepted-with-calibration-pending"
            if calibration_pending_count
            else "accepted-shadow"
        )
    except ReviewerContextTooLarge as exc:
        _write_json(
            output_dir / "failure-diagnostic.json",
            {
                "schema_version": 1,
                "status": "blocked-reviewer-context-too-large",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "safe_recovery": "decompose the external scope and start a new output directory",
            },
        )
        return finish("blocked-reviewer-context-too-large", error=str(exc))
    except (
        DesignError,
        ImmutableIterationError,
        IterationContractError,
        ReviewerEvidenceError,
        json.JSONDecodeError,
    ) as exc:
        _write_json(
            output_dir / "failure-diagnostic.json",
            {
                "schema_version": 1,
                "status": "blocked-contract",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "safe_recovery": "fix the named contract and start a new output directory",
            },
        )
        return finish("blocked-contract", error=str(exc))
    except (StageBackendError, OSError) as exc:
        _write_json(
            output_dir / "failure-diagnostic.json",
            {
                "schema_version": 1,
                "status": "failed-infrastructure",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "safe_recovery": "start a new immutable attempt after backend recovery",
            },
        )
        return finish("failed-infrastructure", error=str(exc))
