from __future__ import annotations

import copy
import hashlib
import json
import re
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence

from test_case_agent.strict_output_schema import (
    validate_openai_strict_output_instance,
    validate_openai_strict_output_schema,
)
from test_case_agent.coverage_graph import (
    CoverageCase,
    CoverageGraph,
    validate_coverage_graph,
)
from test_case_agent.iteration_contract import (
    REVIEWER_FALSIFICATION_PROBES,
    IterationContractError,
    SuiteGateReport,
    build_reviewer_request,
    build_runtime_writer_request,
    build_writer_request,
    request_sha256,
    reviewer_deferred_test_case_findings,
    reviewer_acceptance_contract,
    reviewer_prompt_instruction_for_request,
    reviewer_response_schema,
    runtime_writer_response_schema,
    validate_runtime_writer_response,
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
    TestDesignPlan,
    build_test_design_plan,
    render_test_cases,
)


MAX_WRITER_PROMPT_BYTES = 192 * 1024
MAX_REVISION_WRITER_PROMPT_TARGET_BYTES = 110 * 1024
MAX_REVIEWER_PROMPT_BYTES = 512 * 1024


class ImmutableIterationError(ValueError):
    """The deterministic-first attempt cannot continue without guessing."""


class ReviewerContextTooLarge(ImmutableIterationError):
    """The complete reviewer evidence cannot fit without forbidden truncation."""


class RevisionContextTooLarge(ImmutableIterationError):
    """The bounded revision writer context exceeds the hard compact limit."""

    def __init__(self, message: str, *, breakdown: Mapping[str, Any]) -> None:
        self.breakdown = dict(breakdown)
        super().__init__(message)


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


def _json_size(value: Any) -> int:
    return len(_json_bytes(value))


def _compact_reviewer_request_for_model(
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a live-reviewer view without dropping audited request evidence.

    ``reviewer-request.json`` remains the full contract payload used for
    validation, promotion, and receipt binding.  The model prompt does not need
    repeated deterministic hashes/locators when the same objects remain bound by
    stable IDs and a full-request digest.  This compact view is therefore used
    only for model transport.
    """

    if request.get("schema_version") != 2:
        return dict(request)
    pack = request.get("reviewer_evidence_pack")
    if not isinstance(pack, Mapping):
        return dict(request)
    source_structure = pack.get("source_structure")
    if not isinstance(source_structure, Mapping):
        return dict(request)

    compact_request = copy.deepcopy(dict(request))
    compact_pack = compact_request.get("reviewer_evidence_pack")
    if not isinstance(compact_pack, dict):  # pragma: no cover - guarded above
        return compact_request
    compact_source_structure = compact_pack.get("source_structure")
    if not isinstance(compact_source_structure, dict):  # pragma: no cover
        return compact_request

    omitted_fields: list[str] = []

    parity = compact_source_structure.get("docx_xhtml_pdf_parity")
    if isinstance(parity, Mapping):
        compact_source_structure["docx_xhtml_pdf_parity"] = {
            "compact_omitted_from_model_prompt": True,
            "full_payload_sha256": hashlib.sha256(_json_bytes(parity)).hexdigest(),
            "full_payload_bytes": _json_size(parity),
            "status": parity.get("status", "unavailable"),
            "top_level_keys": sorted(str(key) for key in parity),
            "rationale": (
                "Detailed parity proof is preserved in reviewer-request.json; "
                "the live prompt uses this digest-bound summary because the "
                "accepted source review and literal row evidence remain present."
            ),
        }
        omitted_fields.append(
            "reviewer_evidence_pack.source_structure.docx_xhtml_pdf_parity"
        )

    for item in compact_pack.get("supporting_evidence_mapping", []):
        if isinstance(item, dict):
            for field in (
                "source_path",
                "source_locator",
                "exact_source_fragment_sha256",
            ):
                if field in item:
                    item.pop(field)
                    omitted_fields.append(
                        f"reviewer_evidence_pack.supporting_evidence_mapping[].{field}"
                    )

    for item in compact_pack.get("design_support_mapping", []):
        if isinstance(item, dict) and "materialized_text_sha256" in item:
            item.pop("materialized_text_sha256")
            omitted_fields.append(
                "reviewer_evidence_pack.design_support_mapping[].materialized_text_sha256"
            )

    normalized_projection = compact_pack.get("normalized_projection")
    if isinstance(normalized_projection, dict):
        for item in normalized_projection.get("properties", []):
            if isinstance(item, dict):
                for field in ("source_path", "source_locator", "source_text_sha256"):
                    if field in item:
                        item.pop(field)
                        omitted_fields.append(
                            f"reviewer_evidence_pack.normalized_projection.properties[].{field}"
                        )

    compact_request["model_context"] = {
        "context_contract": "reviewer-model-request-compact-v1",
        "full_request_sha256": request_sha256(request),
        "full_request_bytes": _json_size(request),
        "model_request_bytes": 0,
        "omitted_field_kinds": sorted(set(omitted_fields)),
        "review_contract": (
            "Validate the draft semantically against this compact view; the "
            "runner validates the response against the full reviewer-request.json."
        ),
    }
    previous_size = -1
    while True:
        current_size = _json_size(compact_request)
        if current_size == previous_size:
            break
        compact_request["model_context"]["model_request_bytes"] = current_size
        previous_size = current_size
    return compact_request


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
        if request.get("writer_mode") == "model-runtime-prose":
            instruction = (
                "Return JSON only. This is the model-runtime-prose route, not the "
                "legacy registered-card projection route. Do not choose or return "
                "`subject_id`, `expected_result_id`, `fixture_ids`, `data_ids`, or "
                "`step_ids`. Return `route_contract_ack` exactly as "
                "`runtime-prose-one-case-per-seed`. Return exactly one item in "
                "`cases` for every input seed case. Copy each `case_key` and `tc_id` "
                "without changes. The runner owns identity, traceability, priority, "
                "package, status, and lifecycle fields. Author only human-executable "
                "runtime prose: `title`, `preconditions`, `test_data`, `steps`, "
                "`expected_result`, `postconditions`, and `calibration_question`. "
                "Use the provided `seed_runtime` as the starting draft and improve "
                "human wording only when needed. Never copy non-executable "
                "sentinel placeholders such as `source-backed fixture only`, "
                "`source-backed value only`, or "
                "`requires UI calibration for exact response` into title, "
                "preconditions, test data, steps, expected result, postconditions, "
                "or calibration question. If a seed contains such a placeholder "
                "and no concrete source-prepared value is available, return that "
                "individual case in `unresolved` with a specific reason. "
                "If `seed_runtime.test_data` "
                "contains source-prepared `Допустимое ...: `...``` or "
                "`Недопустимое ...: `...``` items, every exact backticked "
                "prepared value from those items must appear in `steps` as a "
                "concrete input/check action. Do not replace prepared values "
                "with aggregate wording such as `поочередно вводить каждое "
                "значение`. Every item listed in "
                "`protected_runtime_fragments.source_prepared_test_data` is "
                "mandatory exact-copy test data: copy it into `test_data` "
                "unchanged, including fixture id, query literal, suggestion "
                "literal, punctuation and backticks. Do not summarize, "
                "translate, move it to steps, or replace it with runtime lookup "
                "instructions. `preconditions` must contain only the "
                "exact sentinel `Не требуются.` or user/tester setup "
                "actions that reproduce the required state, such as `Открыть "
                "карточку ...`, `Перейти в блок ...`, or `Нажать ...`. Do not "
                "use passive state-only preconditions such as `Открыта карточка "
                "...`, `Поле доступно ...`, or `Блок отображается ...`. Each setup "
                "action must name one exact source-backed UI control/action path. "
                "Do not remove or reorder seed_runtime preconditions that open "
                "the parent card/form and then navigate to the scope block; a "
                "block-level navigation step is not a replacement for opening "
                "the containing card/form when both are present in the seed. "
                "For positive allowed-value or boundary checks, do not use "
                "negated rejection/blocking wording such as `не отклоняется` "
                "or `не блокируется` as the oracle. "
                "State the concrete observable positive artifact instead, for "
                "example that the exact entered value is displayed in the field. "
                "For always-visible or invariant seeds that verify only concrete "
                "source-backed states such as before and after one transition, "
                "keep the title and expected result bounded to those states. Do "
                "not use unbounded wording such as `всегда`, `постоянно`, "
                "`always`, or `permanent` unless the seed explicitly enumerates "
                "all source-defined states. "
                "Do not list alternative controls/actions joined by `или` or `/`, "
                "for example `Дважды нажать виджет + или кнопку Добавить контактное "
                "лицо`. If several controls are present in source/mockup context, "
                "choose the canonical source-backed control/action instead of "
                "listing alternatives. Repeated setup must be either separate "
                "numbered actions or one exact repeated action with one exact "
                "control, for example `Нажать кнопку «Добавить контактное лицо» "
                "два раза`. If a "
                "source-bound setup hint cannot be written as a user action, "
                "return that concrete case in `unresolved` with a specific reason. "
                "Do not put internal IDs such as `subject:*`, `OBL-*`, `ATOM-*`, "
                "`ASSERT-*`, `SRC-*`, or `BSR ...` in runtime prose. Use "
                "`unresolved` only for a concrete individual case with a specific "
                "source blocker; do not mark all valid seed cases unresolved "
                "because of schema or route confusion."
            )
            if "revision_context" in request:
                instruction += (
                    " This is a bounded revision attempt. The request contains only "
                    "TCs affected by reviewer findings plus their previous draft "
                    "blocks. Revise only those affected cases. Cases absent from "
                    "the request are preserved by the runner byte-identical from "
                    "the previous shadow draft. Do not rewrite unaffected TCs. "
                    "For affected executable cases, repair only source-backed "
                    "defects described in `findings_by_case`. If a finding requires "
                    "an unknown UI observable, validation/commit trigger, concrete "
                    "test fixture, or representative disallowed transition class "
                    "that is not source-bound, keep the case as calibration-pending "
                    "by returning the provided `calibration_question`; do not invent "
                    "UI messages, markers, buttons, statuses, fixtures, or validation "
                    "responses. If a "
                    "source-bound commit/validation action is explicit in the seed "
                    "or source evidence, write it as an action-oriented step. "
                    "Runner-owned identity and traceability remain immutable."
                )
        else:
            instruction = (
                "Return JSON only. For every card, return only its registered subject, "
                "expected-result, fixture, data, and ordered action identifiers. Do not "
                "author case prose or add identifiers that are absent from the card."
            )
    elif stage == "reviewer":
        try:
            instruction = reviewer_prompt_instruction_for_request(request)
        except IterationContractError as exc:
            raise ImmutableIterationError(str(exc)) from exc
        if "revision_review_scope" in request:
            instruction += (
                " This is a bounded revision review. Full-review only the "
                "changed case_keys listed in revision_review_scope.changed_case_keys "
                "and the directly affected reviewer findings for those cases. "
                "For unchanged byte-identical cases, check only regression, identity "
                "drift, and binding drift. Do not escalate unchanged calibration-"
                "pending baseline issues into blocking errors for this revision; "
                "record unrelated unchanged issues only as non-blocking baseline "
                "backlog/deferred findings. Any blocking finding must bind to a "
                "changed case or to a concrete regression caused by this revision. "
                "Falsification trigger_or_step and oracle values must be copied "
                "exactly from the reviewed case/evidence allowed set; if exact "
                "binding is unavailable, do not emit a blocking case finding."
            )
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
    model_request: Mapping[str, Any],
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
        "model_request_sha256": request_sha256(model_request),
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
            "model_request_bytes": len(_json_bytes(model_request)),
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


def _revision_prompt_size_breakdown(
    request: Mapping[str, Any],
    *,
    prompt_size: int,
) -> dict[str, Any]:
    revision_context = request.get("revision_context")
    if not isinstance(revision_context, Mapping):
        revision_context = {}
    top_level = {
        key: _json_size(value)
        for key, value in sorted(request.items())
        if key != "revision_context"
    }
    context_parts = {
        key: _json_size(value)
        for key, value in sorted(revision_context.items())
    }
    affected_keys = revision_context.get("affected_case_keys")
    unaffected_manifest = revision_context.get("unaffected_cases_manifest")
    return {
        "prompt_bytes": prompt_size,
        "target_bytes": MAX_REVISION_WRITER_PROMPT_TARGET_BYTES,
        "hard_cap_bytes": MAX_WRITER_PROMPT_BYTES,
        "top_level_request_bytes": top_level,
        "revision_context_bytes": context_parts,
        "case_count": len(request.get("cases", []))
        if isinstance(request.get("cases"), list)
        else None,
        "affected_case_count": len(affected_keys)
        if isinstance(affected_keys, list)
        else None,
        "unaffected_manifest_count": len(unaffected_manifest)
        if isinstance(unaffected_manifest, list)
        else None,
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
    model_request: Mapping[str, Any]
    if stage == "reviewer":
        model_request = _compact_reviewer_request_for_model(request)
    else:
        model_request = request
    prompt = _stage_prompt(stage, model_request)
    limit = MAX_WRITER_PROMPT_BYTES if stage == "writer" else MAX_REVIEWER_PROMPT_BYTES
    prompt_size = len(prompt.encode("utf-8"))
    if prompt_size > limit:
        message = f"{stage} prompt exceeds compact limit: {prompt_size} > {limit} bytes"
        if stage == "writer" and "revision_context" in request:
            raise RevisionContextTooLarge(
                message,
                breakdown=_revision_prompt_size_breakdown(
                    request,
                    prompt_size=prompt_size,
                ),
            )
        if stage == "reviewer":
            raise ReviewerContextTooLarge(message)
        raise ImmutableIterationError(message)
    model_dir = output_dir / "model-stages"
    prompt_path = model_dir / f"{stage}-prompt.txt"
    model_request_path = model_dir / f"{stage}-model-request.json"
    schema_path = model_dir / f"{stage}-output-schema.json"
    response_path = model_dir / f"{stage}-response.json"
    _write_text(prompt_path, prompt)
    if model_request != request:
        _write_json(model_request_path, dict(model_request))
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
        model_request=model_request,
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


_REVISION_CALIBRATION_FINDING_TYPES = {
    "commit-action-missing",
    "execution-status-incorrect",
    "expected-result-unsupported",
    "test-data-nonconcrete",
}
_REVISION_SOURCE_BOUND_REPAIR_HINT = (
    "Masked rendering belongs to ASSERT-019/OBL-BSR-183-PHONE-DEFAULT-MASK"
)


@dataclass(frozen=True)
class _RevisionContext:
    payload: Mapping[str, Any]
    previous_cases: tuple[TestCaseDesign, ...]
    affected_case_keys: tuple[str, ...]
    findings_by_case: Mapping[str, tuple[Mapping[str, Any], ...]]
    previous_blocks_by_tc_id: Mapping[str, str]
    source_attempt_dir: Path


@dataclass(frozen=True)
class _RevisionSplitPlan:
    graph: CoverageGraph
    active_cases: tuple[TestCaseDesign, ...]
    affected_case_keys: tuple[str, ...]
    findings_by_case: Mapping[str, tuple[Mapping[str, Any], ...]]
    child_cases_by_parent_key: Mapping[str, tuple[TestCaseDesign, ...]]


_REVISION_EXPECTED_CLAUSE_RE = re.compile(
    r"(?<=[.!?])\s+(?=(?:Для|Ожидаемая реакция|Проверить|После)\s+|$)"
)
_REVISION_BACKTICK_VALUE_RE = re.compile(r"`([^`]+)`")
_REVISION_CALIBRATION_RE = re.compile(
    r"(?:UI[- ]?калибровк|калибровк|требует\s+UI|calibration)",
    re.IGNORECASE,
)
_REVISION_NEGATIVE_OUTCOME_RE = re.compile(
    r"(?:очища\w*|обязательн\w*\s+к\s+заполн|ошибк\w*|invalid|required|"
    r"не\s+принима\w*|не\s+сохраня\w*|отклон\w*)",
    re.IGNORECASE,
)
_REVISION_POSITIVE_OUTCOME_RE = re.compile(
    r"(?:состояни\w*\s+`?valid`?|валидн\w*|valid|отобража\w*|"
    r"нормализ\w*|игнорир\w*|отброш\w*|фильтру\w*|сообщени\w*[^.;]*отсутств\w*)",
    re.IGNORECASE,
)


def _revision_expected_clauses(expected_result: str) -> tuple[str, ...]:
    clauses = tuple(
        item.strip()
        for item in _REVISION_EXPECTED_CLAUSE_RE.split(expected_result.strip())
        if item.strip()
    )
    return clauses or (expected_result.strip(),)


def _revision_clause_polarity(clause: str) -> str:
    if _REVISION_CALIBRATION_RE.search(clause) is not None:
        return "calibration"
    if _REVISION_NEGATIVE_OUTCOME_RE.search(clause) is not None:
        return "negative"
    if _REVISION_POSITIVE_OUTCOME_RE.search(clause) is not None:
        return "positive"
    return "neutral"


def _revision_values_in_text(value: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(_REVISION_BACKTICK_VALUE_RE.findall(value)))


def _revision_case_key_variant(case_key: str, polarity: str) -> str | None:
    parts = case_key.split("|")
    if len(parts) != 5:
        return None
    property_kind = parts[2]
    variant = parts[3]
    mapping = {
        ("source-format", "allowed-class", "positive"): "allowed-class-valid",
        ("source-format", "allowed-class", "negative"): "allowed-class-invalid",
        ("source-format", "allowed-class", "calibration"): "allowed-class-calibration",
        (
            "source-requiredness",
            "required-empty",
            "positive",
        ): "required-empty-positive-outcome",
        (
            "source-requiredness",
            "required-empty",
            "negative",
        ): "required-empty-negative-outcome",
        (
            "source-requiredness",
            "required-empty",
            "calibration",
        ): "required-empty-calibration-outcome",
    }
    child_variant = mapping.get((property_kind, variant, polarity))
    if child_variant is None:
        return None
    return "|".join((*parts[:3], child_variant, parts[4]))


def _revision_child_tc_id(parent_tc_id: str, polarity: str, *, first: bool) -> str:
    if first:
        return parent_tc_id
    suffix = {
        "positive": "POS",
        "negative": "NEG",
        "calibration": "OBS",
    }[polarity]
    return f"{parent_tc_id}-{suffix}"


def _revision_child_title(parent_title: str, polarity: str) -> str:
    suffix = {
        "positive": "допустимые значения",
        "negative": "недопустимые значения",
        "calibration": "значения со специальными символами",
    }[polarity]
    return f"{parent_title} - {suffix}"


def _revision_filtered_runtime_items(
    items: Sequence[str],
    values: Sequence[str],
) -> tuple[str, ...]:
    if not values:
        return tuple(items)
    selected: list[str] = []
    for item in items:
        item_values = set(_revision_values_in_text(item))
        if not item_values or item_values.intersection(values):
            selected.append(item)
    return tuple(selected) or tuple(items)


def _revision_input_values_for_child(
    *,
    case: TestCaseDesign,
    expected_result: str,
    polarity: str,
    findings: Sequence[Mapping[str, Any]],
) -> tuple[str, ...]:
    parent_input_values = tuple(
        dict.fromkeys(
            value
            for item in case.test_data
            for value in _revision_values_in_text(item)
            if value
        )
    )
    expected_values = set(_revision_values_in_text(expected_result))
    selected = [value for value in parent_input_values if value in expected_values]
    if polarity == "positive":
        for finding in findings:
            message = str(finding.get("message") or "")
            if "valid" not in message.casefold() and "допуст" not in message.casefold():
                continue
            for value in _revision_values_in_text(message):
                if value not in selected:
                    selected.append(value)
    return tuple(selected)


def _revision_child_test_data(
    *,
    case: TestCaseDesign,
    values: Sequence[str],
) -> tuple[str, ...]:
    if not values:
        return case.test_data
    return (
        "Проверяемые значения: "
        + ", ".join(f"`{value}`" for value in values)
        + ".",
    )


def _revision_child_steps(
    *,
    case: TestCaseDesign,
    values: Sequence[str],
) -> tuple[str, ...]:
    steps = _revision_filtered_runtime_items(case.steps, values)
    if not values:
        return steps
    steps_text = "\n".join(steps)
    missing = tuple(
        value for value in values if value not in _revision_values_in_text(steps_text)
    )
    if not missing:
        return steps
    value_steps = tuple(
        f"Ввести `{value}` и снять фокус с поля."
        for value in missing
    )
    return (*steps, *value_steps)


def _revision_split_case_by_outcome(
    case: TestCaseDesign,
    findings: Sequence[Mapping[str, Any]],
) -> tuple[TestCaseDesign, ...]:
    grouped: dict[str, list[str]] = {"positive": [], "negative": [], "calibration": []}
    neutral: list[str] = []
    for clause in _revision_expected_clauses(case.expected_result):
        polarity = _revision_clause_polarity(clause)
        if polarity in grouped:
            grouped[polarity].append(clause)
        else:
            neutral.append(clause)
    present = tuple(polarity for polarity, clauses in grouped.items() if clauses)
    if len(present) < 2:
        return (case,)
    children: list[TestCaseDesign] = []
    for polarity in present:
        child_key = _revision_case_key_variant(case.case_key, polarity)
        if child_key is None:
            return (case,)
        clauses = [*neutral, *grouped[polarity]]
        expected_result = " ".join(clauses).strip()
        values = _revision_values_in_text(expected_result)
        status = (
            "candidate-ui-calibration"
            if polarity == "calibration"
            else "executable"
        )
        child_case_type = "позитивный" if polarity == "positive" else "негативный"
        values = _revision_input_values_for_child(
            case=case,
            expected_result=expected_result,
            polarity=polarity,
            findings=findings,
        )
        children.append(
            replace(
                case,
                case_key=child_key,
                tc_id=_revision_child_tc_id(
                    case.tc_id,
                    polarity,
                    first=not children,
                ),
                status=status,
                case_type=child_case_type,
                title=_revision_child_title(case.title, polarity),
                test_data=_revision_child_test_data(case=case, values=values),
                steps=_revision_child_steps(case=case, values=values),
                expected_result=expected_result,
                calibration_question=(
                    case.calibration_question
                    if status == "candidate-ui-calibration"
                    else ""
                ),
            )
        )
    return tuple(children)


def _revision_findings_for_child(
    *,
    child: TestCaseDesign,
    parent_findings: Sequence[Mapping[str, Any]],
    parent_tc_id: str,
) -> tuple[Mapping[str, Any], ...]:
    child_values = set(_revision_values_in_text(child.expected_result))
    matched: list[Mapping[str, Any]] = []
    for raw in parent_findings:
        message = str(raw.get("message") or "")
        message_values = set(_revision_values_in_text(message))
        if message_values and child_values and message_values.isdisjoint(child_values):
            continue
        finding = dict(raw)
        finding["case_key"] = child.case_key
        finding["tc_id"] = child.tc_id
        if child.tc_id != parent_tc_id:
            finding["split_parent_tc_id"] = parent_tc_id
        matched.append(finding)
    if matched:
        return tuple(matched)
    return tuple(
        {
            **dict(raw),
            "case_key": child.case_key,
            "tc_id": child.tc_id,
            **({"split_parent_tc_id": parent_tc_id} if child.tc_id != parent_tc_id else {}),
        }
        for raw in parent_findings
    )


def _prepare_revision_split_plan(
    *,
    graph: CoverageGraph,
    revision_context: _RevisionContext,
) -> _RevisionSplitPlan:
    graph_cases_by_key = {case.case_key: case for case in graph.cases}
    previous_cases_by_key = {
        case.case_key: case for case in revision_context.previous_cases
    }
    active_graph_cases = list(graph.cases)
    active_seed_cases: list[TestCaseDesign] = []
    active_findings: dict[str, tuple[Mapping[str, Any], ...]] = {}
    replacements: dict[str, tuple[TestCaseDesign, ...]] = {}
    for case_key in revision_context.affected_case_keys:
        parent_seed = _revision_seed_case(
            previous_cases_by_key[case_key],
            revision_context.findings_by_case[case_key],
        )
        children = _revision_split_case_by_outcome(
            parent_seed,
            revision_context.findings_by_case[case_key],
        )
        if len(children) == 1 and children[0].case_key == case_key:
            active_seed_cases.append(parent_seed)
            active_findings[case_key] = revision_context.findings_by_case[case_key]
            continue
        parent_graph_case = graph_cases_by_key[case_key]
        replacements[case_key] = children
        active_graph_cases = [
            item for item in active_graph_cases if item.case_key != case_key
        ]
        active_graph_cases.extend(
            CoverageCase(
                case_key=child.case_key,
                tc_id=child.tc_id,
                obligation_ids=parent_graph_case.obligation_ids,
                status=(
                    parent_graph_case.status
                    if child.status == "candidate-ui-calibration"
                    else child.status
                ),
            )
            for child in children
        )
        active_seed_cases.extend(children)
        for child in children:
            active_findings[child.case_key] = _revision_findings_for_child(
                child=child,
                parent_findings=revision_context.findings_by_case[case_key],
                parent_tc_id=parent_seed.tc_id,
            )
    active_graph = replace(
        graph,
        cases=tuple(sorted(active_graph_cases, key=lambda item: item.case_key)),
    )
    return _RevisionSplitPlan(
        graph=active_graph,
        active_cases=tuple(sorted(active_seed_cases, key=lambda item: item.case_key)),
        affected_case_keys=tuple(sorted(active_findings)),
        findings_by_case=active_findings,
        child_cases_by_parent_key=replacements,
    )


def _text_field(raw: Mapping[str, Any], field: str, label: str) -> str:
    value = raw.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ImmutableIterationError(f"{label}.{field} must be non-empty text")
    return value


def _string_tuple(raw: Mapping[str, Any], field: str, label: str) -> tuple[str, ...]:
    value = raw.get(field)
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise ImmutableIterationError(
            f"{label}.{field} must be a non-empty string array"
        )
    return tuple(value)


def _design_from_document(raw: Mapping[str, Any], label: str) -> TestCaseDesign:
    return TestCaseDesign(
        case_key=_text_field(raw, "case_key", label),
        tc_id=_text_field(raw, "tc_id", label),
        status=_text_field(raw, "status", label),
        title=_text_field(raw, "title", label),
        case_type=_text_field(raw, "case_type", label),
        priority=_text_field(raw, "priority", label),
        package_id=_text_field(raw, "package_id", label),
        traceability=_string_tuple(raw, "traceability", label),
        preconditions=_string_tuple(raw, "preconditions", label),
        test_data=_string_tuple(raw, "test_data", label),
        steps=_string_tuple(raw, "steps", label),
        expected_result=_text_field(raw, "expected_result", label),
        postconditions=_string_tuple(raw, "postconditions", label),
        calibration_question=(
            raw.get("calibration_question")
            if isinstance(raw.get("calibration_question"), str)
            else ""
        ),
    )


def _case_blocks_by_tc_id(markdown: str) -> dict[str, str]:
    starts: list[tuple[str, int]] = []
    offset = 0
    for line in markdown.splitlines(keepends=True):
        if line.startswith("## "):
            tc_id = line[3:].strip()
            if tc_id:
                starts.append((tc_id, offset))
        offset += len(line)
    blocks: dict[str, str] = {}
    for index, (tc_id, start) in enumerate(starts):
        end = starts[index + 1][1] if index + 1 < len(starts) else len(markdown)
        blocks[tc_id] = markdown[start:end]
    return blocks


def _revision_unaffected_manifest(
    *,
    previous_cases: Sequence[TestCaseDesign],
    affected_case_keys: Sequence[str],
    previous_blocks_by_tc_id: Mapping[str, str],
) -> tuple[dict[str, Any], ...]:
    affected = set(affected_case_keys)
    manifest: list[dict[str, Any]] = []
    for case in previous_cases:
        if case.case_key in affected:
            continue
        block = previous_blocks_by_tc_id.get(case.tc_id, "")
        manifest.append(
            {
                "case_key": case.case_key,
                "tc_id": case.tc_id,
                "title": case.title,
                "block_sha256": hashlib.sha256(block.encode("utf-8")).hexdigest(),
            }
        )
    return tuple(manifest)


def _previous_reviewer_disposition_by_case(
    revision_input: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    response = revision_input.get("reviewer_response")
    if not isinstance(response, Mapping):
        return {}
    disposition: dict[str, dict[str, Any]] = {}
    results = response.get("case_results")
    if isinstance(results, list):
        for raw in results:
            if not isinstance(raw, Mapping):
                continue
            case_key = raw.get("case_key")
            if isinstance(case_key, str) and case_key:
                disposition.setdefault(case_key, {})["previous_result_status"] = raw.get(
                    "status"
                )
    findings = response.get("test_case_findings")
    if isinstance(findings, list):
        for raw in findings:
            if not isinstance(raw, Mapping):
                continue
            case_key = raw.get("case_key")
            if not isinstance(case_key, str) or not case_key:
                continue
            entry = disposition.setdefault(case_key, {})
            entry.setdefault("previous_findings", []).append(
                {
                    "severity": raw.get("severity"),
                    "finding_type": raw.get("finding_type"),
                    "tc_id": raw.get("tc_id"),
                }
            )
    return disposition


def _revision_reviewer_scope(
    *,
    revision_context: _RevisionContext,
    previous_cases_by_key: Mapping[str, TestCaseDesign],
    changed_tc_ids: Sequence[str],
    unchanged_hashes: Mapping[str, str],
    changed_cases: Sequence[TestCaseDesign] = (),
) -> dict[str, Any]:
    changed_tc_id_set = set(changed_tc_ids)
    changed_case_keys = tuple(
        sorted(
            {
                *(
                    case.case_key
                    for case in revision_context.previous_cases
                    if case.tc_id in changed_tc_id_set
                ),
                *(
                    case.case_key
                    for case in changed_cases
                    if case.tc_id in changed_tc_id_set
                ),
            }
        )
    )
    previous_disposition = _previous_reviewer_disposition_by_case(
        revision_context.payload
    )
    unchanged_cases: list[dict[str, Any]] = []
    for case in revision_context.previous_cases:
        block_sha256 = unchanged_hashes.get(case.tc_id)
        if block_sha256 is None:
            continue
        item = {
            "case_key": case.case_key,
            "tc_id": case.tc_id,
            "title": case.title,
            "status": case.status,
            "block_sha256": block_sha256,
        }
        disposition = previous_disposition.get(case.case_key)
        if disposition:
            item["previous_reviewer_disposition"] = disposition
        unchanged_cases.append(item)
    return {
        "schema_version": 1,
        "mode": "revision-review-changed-cases-primary",
        "changed_case_keys": list(changed_case_keys),
        "changed_tc_ids": list(changed_tc_ids),
        "affected_case_keys": list(revision_context.affected_case_keys),
        "affected_tc_ids": sorted(
            previous_cases_by_key[key].tc_id
            for key in revision_context.affected_case_keys
            if key in previous_cases_by_key
        ),
        "unchanged_byte_identical_cases": unchanged_cases,
        "policy": {
            "changed_cases": "full-review changed cases and directly affected findings",
            "unchanged_cases": (
                "check only regression, identity drift, and binding drift; unrelated "
                "unchanged issues are non-blocking baseline backlog/deferred"
            ),
            "calibration_pending_baseline": (
                "do not escalate unchanged calibration-pending baseline cases from "
                "previous warning/accepted disposition into current blocking errors"
            ),
            "falsification_binding": (
                "copy trigger_or_step and oracle exactly from the reviewed case or "
                "evidence allowed set; do not paraphrase blocking falsification basis"
            ),
        },
    }


def _revision_findings_by_case(
    revision_input: Mapping[str, Any],
) -> dict[str, tuple[Mapping[str, Any], ...]]:
    response = revision_input.get("reviewer_response")
    if not isinstance(response, Mapping):
        raise ImmutableIterationError("revision_input.reviewer_response must be an object")
    raw_findings = response.get("test_case_findings")
    if not isinstance(raw_findings, list):
        raise ImmutableIterationError(
            "revision_input.reviewer_response.test_case_findings must be an array"
        )
    by_case: dict[str, list[Mapping[str, Any]]] = {}
    for index, raw in enumerate(raw_findings):
        if not isinstance(raw, Mapping):
            raise ImmutableIterationError(
                f"revision test_case_findings[{index}] must be an object"
            )
        case_key = raw.get("case_key")
        tc_id = raw.get("tc_id")
        finding_type = raw.get("finding_type")
        if (
            not isinstance(case_key, str)
            or not case_key
            or not isinstance(tc_id, str)
            or not tc_id
            or not isinstance(finding_type, str)
            or not finding_type
        ):
            raise ImmutableIterationError(
                f"revision test_case_findings[{index}] is missing case binding"
            )
        by_case.setdefault(case_key, []).append(dict(raw))
    return {key: tuple(value) for key, value in by_case.items()}


def _revision_requires_calibration(findings: Sequence[Mapping[str, Any]]) -> bool:
    for finding in findings:
        finding_type = str(finding.get("finding_type") or "")
        message = str(finding.get("message") or "")
        if finding_type not in _REVISION_CALIBRATION_FINDING_TYPES:
            continue
        if _REVISION_SOURCE_BOUND_REPAIR_HINT in message:
            continue
        return True
    return False


def _revision_calibration_question(findings: Sequence[Mapping[str, Any]]) -> str:
    tc_id = str(findings[0].get("tc_id") or "affected case")
    finding_types = ", ".join(
        sorted({str(item.get("finding_type") or "unknown") for item in findings})
    )
    return (
        f"Какой точный source-backed UI trigger/observable нужно проверить "
        f"для {tc_id} перед executable publication по reviewer findings "
        f"{finding_types}?"
    )


def _load_revision_context(
    *,
    revision_input: Mapping[str, Any],
    repo_root: Path,
    graph: CoverageGraph,
    writer_mode: str,
) -> _RevisionContext:
    if revision_input.get("schema_version") != 1:
        raise ImmutableIterationError("revision_input.schema_version must be 1")
    if revision_input.get("graph_digest") != graph.digest:
        raise ImmutableIterationError("revision_input graph_digest differs")
    if revision_input.get("writer_mode") != writer_mode:
        raise ImmutableIterationError("revision_input writer_mode differs")
    if revision_input.get("reviewer_decision") != "changes-required":
        raise ImmutableIterationError(
            "revision_input must come from reviewer changes-required"
        )
    source_attempt = revision_input.get("source_attempt_dir")
    if not isinstance(source_attempt, str) or not source_attempt.strip():
        raise ImmutableIterationError("revision_input.source_attempt_dir is missing")
    source_attempt_dir = _resolve_inside_repo(
        Path(source_attempt),
        repo_root,
        "revision source attempt",
    )
    designs_path = source_attempt_dir / "test-case-designs.json"
    draft_path = source_attempt_dir / "shadow-test-cases.md"
    if not designs_path.is_file() or not draft_path.is_file():
        raise ImmutableIterationError(
            "revision_input source attempt is missing draft/design artifacts"
        )
    designs_payload = json.loads(designs_path.read_text(encoding="utf-8"))
    if not isinstance(designs_payload, Mapping) or not isinstance(
        designs_payload.get("cases"), list
    ):
        raise ImmutableIterationError("previous test-case-designs.json is invalid")
    previous_cases = tuple(
        _design_from_document(raw, f"previous.cases[{index}]")
        for index, raw in enumerate(designs_payload["cases"])
        if isinstance(raw, Mapping)
    )
    if len(previous_cases) != len(designs_payload["cases"]):
        raise ImmutableIterationError("previous test-case-designs contains non-objects")
    previous_keys = {case.case_key for case in previous_cases}
    graph_keys = {case.case_key for case in graph.cases}
    if previous_keys != graph_keys:
        raise ImmutableIterationError("revision previous cases differ from graph cases")
    previous_draft = draft_path.read_text(encoding="utf-8")
    expected_draft_sha = revision_input.get("draft_sha256")
    if isinstance(expected_draft_sha, str) and expected_draft_sha:
        actual_draft_sha = hashlib.sha256(previous_draft.encode("utf-8")).hexdigest()
        if actual_draft_sha != expected_draft_sha:
            raise ImmutableIterationError("revision_input draft_sha256 differs")
    findings_by_case = _revision_findings_by_case(revision_input)
    affected_case_keys = tuple(
        key for key in sorted(findings_by_case) if key in previous_keys
    )
    if not affected_case_keys:
        raise ImmutableIterationError("revision_input has no bound affected cases")
    unknown = set(findings_by_case) - previous_keys
    if unknown:
        raise ImmutableIterationError(
            "revision_input references unknown cases: " + ", ".join(sorted(unknown))
        )
    return _RevisionContext(
        payload=revision_input,
        previous_cases=previous_cases,
        affected_case_keys=affected_case_keys,
        findings_by_case=findings_by_case,
        previous_blocks_by_tc_id=_case_blocks_by_tc_id(previous_draft),
        source_attempt_dir=source_attempt_dir,
    )


def _revision_seed_case(
    case: TestCaseDesign,
    findings: Sequence[Mapping[str, Any]],
) -> TestCaseDesign:
    if not _revision_requires_calibration(findings):
        return case
    return replace(
        case,
        status="candidate-ui-calibration",
        calibration_question=_revision_calibration_question(findings),
    )


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
    writer_mode: str = "deterministic-first",
    mockup_label_aliases: Sequence[Mapping[str, str]] = (),
    revision_findings: Mapping[str, Any] | None = None,
    revision_input: Mapping[str, Any] | None = None,
) -> ImmutableIterationResult:
    """Run one immutable shadow iteration.

    The runner has no retry loop and no promotion path. It calls writer at most once
    and reviewer at most once after a green suite gate.
    """

    repo_root = repo_root.resolve()
    if not repo_root.is_dir():
        raise ImmutableIterationError(f"repo_root is missing: {repo_root}")
    if writer_mode not in {"deterministic-first", "model-runtime-prose"}:
        raise ImmutableIterationError(
            "writer_mode must be `deterministic-first` or `model-runtime-prose`"
        )
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
    revision_context: _RevisionContext | None = None
    revision_changed_tc_ids: tuple[str, ...] = ()
    revision_unaffected_byte_identical = False
    revision_reviewer_scope: Mapping[str, Any] | None = None
    reviewer_deferred_findings_count = 0

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
            "mode": (
                "immutable-model-runtime-prose"
                if writer_mode == "model-runtime-prose"
                else "immutable-deterministic-first"
            ),
            "writer_mode": writer_mode,
            "revision_input_supplied": revision_input is not None,
            "revision_source_attempt_dir": (
                revision_context.source_attempt_dir.relative_to(repo_root).as_posix()
                if revision_context is not None
                else None
            ),
            "revision_affected_case_count": (
                len(revision_context.affected_case_keys)
                if revision_context is not None
                else 0
            ),
            "revision_changed_tc_ids": list(revision_changed_tc_ids),
            "revision_unaffected_byte_identical": (
                revision_unaffected_byte_identical
                if revision_context is not None
                else None
            ),
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
            "reviewer_deferred_findings_count": reviewer_deferred_findings_count,
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
            source_graph = graph
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
            if revision_input is not None and writer_mode != "model-runtime-prose":
                raise ImmutableIterationError(
                    "revision_input requires writer_mode model-runtime-prose"
                )
            context.validate()
            protected = _snapshot_files(
                repo_root=repo_root,
                source_paths=protected_source_paths,
                canonical_paths=protected_canonical_paths,
            )
            if revision_input is not None:
                revision_context = _load_revision_context(
                    revision_input=revision_input,
                    repo_root=repo_root,
                    graph=graph,
                    writer_mode=writer_mode,
                )
                if writer_mode == "model-runtime-prose":
                    revision_split_plan = _prepare_revision_split_plan(
                        graph=graph,
                        revision_context=revision_context,
                    )
                    graph = revision_split_plan.graph
                    graph_findings = validate_coverage_graph(graph)
                    graph_errors = [
                        item for item in graph_findings if item.severity == "error"
                    ]
                    if graph_errors:
                        raise ImmutableIterationError(
                            "revision split coverage graph is invalid: "
                            + "; ".join(item.finding_id for item in graph_errors)
                        )
                else:  # pragma: no cover - guarded above
                    revision_split_plan = None
            else:
                revision_split_plan = None
            _write_json(output_dir / "coverage-graph.json", graph.to_dict())
            if revision_split_plan is not None:
                _write_json(
                    output_dir / "revision-split-plan.json",
                    {
                        "schema_version": 1,
                        "source_graph_digest": source_graph.digest,
                        "active_graph_digest": graph.digest,
                        "affected_case_keys": list(
                            revision_context.affected_case_keys
                        ),
                        "active_affected_case_keys": list(
                            revision_split_plan.affected_case_keys
                        ),
                        "replacements": {
                            key: [case.to_dict() for case in cases]
                            for key, cases in revision_split_plan.child_cases_by_parent_key.items()
                        },
                    },
                )
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
                "writer_mode": writer_mode,
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

        active_plan = plan
        previous_cases_by_key: dict[str, TestCaseDesign] = {}
        if writer_mode == "model-runtime-prose" and revision_context is not None:
            previous_cases_by_key = {
                item.case_key: item for item in revision_context.previous_cases
            }
            if revision_split_plan is not None:
                affected_cases = revision_split_plan.active_cases
                active_findings_by_case = revision_split_plan.findings_by_case
                active_affected_case_keys = revision_split_plan.affected_case_keys
            else:  # pragma: no cover - revision split is always prepared above
                affected_cases = tuple(
                    _revision_seed_case(
                        previous_cases_by_key[case_key],
                        revision_context.findings_by_case[case_key],
                    )
                    for case_key in revision_context.affected_case_keys
                )
                active_findings_by_case = revision_context.findings_by_case
                active_affected_case_keys = revision_context.affected_case_keys
            active_plan = TestDesignPlan(
                schema_version=plan.schema_version,
                graph_digest=graph.digest,
                deterministic_cases=affected_cases,
                writer_cards=(),
                blocked_cards=(),
            )
        if writer_mode == "model-runtime-prose":
            writer_request = build_runtime_writer_request(
                graph,
                active_plan,
                mockup_label_aliases=mockup_label_aliases,
                revision_findings=(
                    None if revision_context is not None else revision_findings
                ),
            )
            if revision_context is not None:
                writer_request = dict(writer_request)
                writer_request.pop("revision_findings", None)
                previous_blocks = {
                    case_key: revision_context.previous_blocks_by_tc_id[parent.tc_id]
                    for parent_key, child_cases in (
                        revision_split_plan.child_cases_by_parent_key.items()
                        if revision_split_plan is not None
                        else ()
                    )
                    for parent in (previous_cases_by_key[parent_key],)
                    for case_key in [case.case_key for case in child_cases]
                    if parent.tc_id in revision_context.previous_blocks_by_tc_id
                }
                previous_blocks.update(
                    {
                        case_key: revision_context.previous_blocks_by_tc_id[
                            previous_cases_by_key[case_key].tc_id
                        ]
                        for case_key in revision_context.affected_case_keys
                        if case_key in previous_cases_by_key
                        and case_key not in previous_blocks
                        and previous_cases_by_key[case_key].tc_id
                        in revision_context.previous_blocks_by_tc_id
                    }
                )
                unaffected_manifest = _revision_unaffected_manifest(
                    previous_cases=revision_context.previous_cases,
                    affected_case_keys=revision_context.affected_case_keys,
                    previous_blocks_by_tc_id=revision_context.previous_blocks_by_tc_id,
                )
                writer_request = {
                    **writer_request,
                    "revision_context": {
                        "mode": "affected-cases-only",
                        "source_attempt_dir": (
                            revision_context.source_attempt_dir.relative_to(
                                repo_root
                            ).as_posix()
                        ),
                        "affected_case_keys": list(active_affected_case_keys),
                        "findings_by_case": {
                            key: list(value)
                            for key, value in active_findings_by_case.items()
                            if key in active_affected_case_keys
                        },
                        "split_parent_case_keys": list(
                            (
                                revision_split_plan.child_cases_by_parent_key.keys()
                                if revision_split_plan is not None
                                else ()
                            )
                        ),
                        "previous_draft_blocks_by_case": previous_blocks,
                        "unaffected_cases_manifest": list(unaffected_manifest),
                        "unaffected_cases_policy": (
                            "The runner will preserve cases absent from this "
                            "request byte-identical from the previous shadow draft. "
                            "Do not emit or rewrite unaffected cases."
                        ),
                    },
                }
            evidence_access.update(
                {
                    "writer_context": (
                        "model-runtime-prose revision affected cases"
                        if revision_context is not None
                        else "model-runtime-prose source-bound cases"
                    ),
                    "writer_model_authors_runtime_prose": True,
                    "mockup_label_alias_count": len(mockup_label_aliases),
                    "revision_findings_supplied": revision_findings is not None,
                    "revision_input_supplied": revision_context is not None,
                }
            )
            _write_json(output_dir / "evidence-access-report.json", evidence_access)
        else:
            writer_request = build_writer_request(graph, plan)
        _write_json(output_dir / "writer-request.json", writer_request)
        if revision_context is not None:
            _write_json(
                output_dir / "revision-context.json",
                {
                    "schema_version": 1,
                    "source_attempt_dir": revision_context.source_attempt_dir.relative_to(
                        repo_root
                    ).as_posix(),
                    "affected_case_keys": list(revision_context.affected_case_keys),
                    "active_affected_case_keys": (
                        list(revision_split_plan.affected_case_keys)
                        if revision_split_plan is not None
                        else list(revision_context.affected_case_keys)
                    ),
                    "finding_count": sum(
                        len(items)
                        for items in revision_context.findings_by_case.values()
                    ),
                    "previous_case_count": len(revision_context.previous_cases),
                    "split_replacement_count": (
                        len(revision_split_plan.child_cases_by_parent_key)
                        if revision_split_plan is not None
                        else 0
                    ),
                },
            )
        writer_cases: tuple[TestCaseDesign, ...] = ()
        if writer_mode == "model-runtime-prose":
            with timer.phase("writer"):
                schema = runtime_writer_response_schema(
                    [item.case_key for item in active_plan.deterministic_cases],
                    graph.digest,
                )
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
                writer_cases, unresolved = validate_runtime_writer_response(
                    payload,
                    graph=graph,
                    plan=active_plan,
                    context=context,
                    mockup_label_aliases=mockup_label_aliases,
                    revision_findings_by_case=(
                        active_findings_by_case
                        if revision_context is not None
                        else None
                    ),
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
                    error="runtime writer returned unresolved cases; no reviewer was run",
                )
        elif plan.writer_cards:
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
            nonlocal_cases: tuple[TestCaseDesign, ...]
            if writer_mode == "model-runtime-prose" and revision_context is not None:
                revised_by_key = {item.case_key: item for item in writer_cases}
                merged_cases: list[TestCaseDesign] = []
                for item in revision_context.previous_cases:
                    child_cases = (
                        revision_split_plan.child_cases_by_parent_key.get(item.case_key)
                        if revision_split_plan is not None
                        else None
                    )
                    if child_cases:
                        merged_cases.extend(
                            revised_by_key.get(child.case_key, child)
                            for child in child_cases
                        )
                    else:
                        merged_cases.append(revised_by_key.get(item.case_key, item))
                nonlocal_cases = tuple(merged_cases)
            elif writer_mode == "model-runtime-prose":
                nonlocal_cases = writer_cases
            else:
                nonlocal_cases = (*plan.deterministic_cases, *writer_cases)
            calibration_pending_count = sum(
                item.status == "candidate-ui-calibration"
                for item in nonlocal_cases
            )
            cases = tuple(
                sorted(
                    nonlocal_cases,
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
                context=context,
                case_status_overrides=(
                    {
                        item.case_key: item.status
                        for item in cases
                        if item.status == "candidate-ui-calibration"
                    }
                    if revision_context is not None
                    else None
                ),
            )
            _write_json(output_dir / "suite-gate.json", gate.to_dict())
            test_case_count = gate.actual_case_count
            if revision_context is not None:
                new_blocks = _case_blocks_by_tc_id(markdown)
                affected_tc_ids = {
                    previous_cases_by_key[key].tc_id
                    for key in revision_context.affected_case_keys
                }
                added_tc_ids = tuple(
                    sorted(
                        tc_id
                        for tc_id in new_blocks
                        if tc_id not in revision_context.previous_blocks_by_tc_id
                    )
                )
                changed_tc_ids = tuple(
                    sorted(
                        {
                            *(
                                tc_id
                                for tc_id, old_block in revision_context.previous_blocks_by_tc_id.items()
                                if new_blocks.get(tc_id) != old_block
                            ),
                            *added_tc_ids,
                        }
                    )
                )
                revision_changed_tc_ids = changed_tc_ids
                revision_unaffected_byte_identical = all(
                    new_blocks.get(tc_id) == old_block
                    for tc_id, old_block in revision_context.previous_blocks_by_tc_id.items()
                    if tc_id not in affected_tc_ids
                )
                unchanged_hashes = {
                    tc_id: hashlib.sha256(old_block.encode("utf-8")).hexdigest()
                    for tc_id, old_block in revision_context.previous_blocks_by_tc_id.items()
                    if new_blocks.get(tc_id) == old_block
                }
                revision_reviewer_scope = _revision_reviewer_scope(
                    revision_context=revision_context,
                    previous_cases_by_key=previous_cases_by_key,
                    changed_tc_ids=changed_tc_ids,
                    unchanged_hashes=unchanged_hashes,
                    changed_cases=tuple(
                        case for case in cases if case.tc_id in changed_tc_ids
                    ),
                )
                _write_json(
                    output_dir / "revision-diff.json",
                    {
                        "schema_version": 1,
                        "source_attempt_dir": revision_context.source_attempt_dir.relative_to(
                            repo_root
                        ).as_posix(),
                        "affected_case_keys": list(
                            revision_context.affected_case_keys
                        ),
                        "affected_tc_ids": sorted(affected_tc_ids),
                        "added_tc_ids": list(added_tc_ids),
                        "changed_tc_ids": list(changed_tc_ids),
                        "changed_tc_count": len(changed_tc_ids),
                        "unchanged_tc_count": len(unchanged_hashes),
                        "unchanged_tc_hashes": unchanged_hashes,
                        "unaffected_byte_identical": (
                            revision_unaffected_byte_identical
                        ),
                    },
                )
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
                case_status_overrides=(
                    {
                        item.case_key: item.status
                        for item in cases
                        if item.status == "candidate-ui-calibration"
                    }
                    if revision_context is not None
                    else None
                ),
            )
            evidence_payload = evidence_pack.to_dict()
            _write_json(output_dir / "reviewer-evidence-pack.json", evidence_payload)
            reviewer_request = build_reviewer_request(
                graph=graph,
                cases=cases,
                gate=gate,
                evidence_pack=evidence_pack,
                revision_review_scope=revision_reviewer_scope,
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
            (
                item.case_key,
                item.tc_id,
                obligation_id,
                item.status,
            )
            for item in cases
            for graph_case in graph.cases
            if graph_case.case_key == item.case_key
            for obligation_id in graph_case.obligation_ids
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
            deferred_findings = reviewer_deferred_test_case_findings(
                payload,
                reviewer_request,
            )
            reviewer_deferred_findings_count = len(deferred_findings)
            if deferred_findings:
                _write_json(
                    output_dir / "reviewer-deferred-findings.json",
                    {
                        "schema_version": 1,
                        "mode": "revision-unchanged-byte-identical-backlog",
                        "deferred_count": reviewer_deferred_findings_count,
                        "findings": list(deferred_findings),
                    },
                )
        if _input_drift(protected):
            return finish("blocked-input-drift")
        if not reviewer_accepted:
            _write_json(
                output_dir / "revision-input.json",
                {
                    "schema_version": 1,
                    "graph_digest": graph.digest,
                    "draft_sha256": gate.draft_sha256,
                    "writer_mode": writer_mode,
                    "source_attempt_dir": output_dir.relative_to(repo_root).as_posix(),
                    "reviewer_decision": reviewer_decision,
                    "reviewer_response": payload,
                    "next_attempt_policy": "start-new-immutable-attempt",
                    "old_test_cases_available": False,
                    "required_next_input": "revision_findings",
                },
            )
            return finish(
                f"review-{reviewer_decision}",
                error="reviewer did not accept the gate-passed shadow draft",
            )
        return finish(
            "accepted-with-calibration-pending"
            if calibration_pending_count
            else "accepted-shadow"
        )
    except RevisionContextTooLarge as exc:
        _write_json(
            output_dir / "failure-diagnostic.json",
            {
                "schema_version": 1,
                "status": "blocked-revision-context-too-large",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "breakdown": exc.breakdown,
                "safe_recovery": "compact revision context further and start a new output directory",
            },
        )
        return finish("blocked-revision-context-too-large", error=str(exc))
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
