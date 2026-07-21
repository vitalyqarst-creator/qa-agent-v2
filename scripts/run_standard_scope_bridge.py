from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
import uuid
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.codex_exec_bounded_scope_analyzer import main as boundary_main  # noqa: E402
from scripts.codex_exec_semantic_design_author import main as semantic_main  # noqa: E402
from scripts.materialize_semantic_design_bridge import main as materialize_main  # noqa: E402
from test_case_agent.bounded_scope_boundary import (  # noqa: E402
    BoundedScopeBoundaryError,
    validate_publication_owner_token,
    validate_stable_path_segment,
)
from test_case_agent.lean_production import (  # noqa: E402
    LeanProductionError,
    artifact_inventory,
    finish_phase,
    load_run,
    start_phase,
)
from test_case_agent.semantic_design_bridge import (  # noqa: E402
    semantic_design_output_schema,
    semantic_design_minimum_obligation_count,
    load_approved_clarifications,
    prepared_context_sha256,
    validate_semantic_input_preflight,
)
from test_case_agent.semantic_design_sharding import (  # noqa: E402
    DETERMINISTIC_NON_TESTABLE_EXECUTION_MODE,
    MODEL_EXECUTION_MODE,
    SemanticDesignShardingError,
    build_semantic_shard_plan,
    materialize_non_testable_semantic_shard,
    merge_semantic_shards,
    project_semantic_shard,
)
from test_case_agent.review_cycle.source_assertions import (  # noqa: E402
    SourceAssertionContractError,
    SourceAssertionManifest,
)


class StandardScopeBridgeError(ValueError):
    pass


class _ModelLifecycleContractError(StandardScopeBridgeError):
    def __init__(
        self,
        message: str,
        *,
        phase: str,
        summary: Mapping[str, Any],
    ) -> None:
        super().__init__(message)
        self.phase = phase
        self.summary = dict(summary)


class _ModelPhaseExecutionError(StandardScopeBridgeError):
    def __init__(
        self,
        original: Exception,
        *,
        phase: str,
        summary: Mapping[str, Any],
    ) -> None:
        super().__init__(str(original))
        self.original = original
        self.phase = phase
        self.summary = dict(summary)


def _under(root: Path, value: Path, *, label: str) -> Path:
    path = (value if value.is_absolute() else root / value).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise StandardScopeBridgeError(f"{label} escapes repository root: {path}") from exc
    return path


def _load_json(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StandardScopeBridgeError(f"cannot read {label}: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise StandardScopeBridgeError(f"{label} must be a JSON object: {path}")
    return payload


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(raw_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _print_best_effort(payload: Mapping[str, Any], *, error: bool = False) -> None:
    try:
        print(
            json.dumps(payload, ensure_ascii=False, indent=2),
            file=sys.stderr if error else sys.stdout,
        )
    except Exception:
        # Console/reporting availability must not change an already established
        # terminal result.
        pass


def _phase_is_running(timer: Path, phase: str) -> bool:
    running = [
        item
        for item in load_run(timer).get("phases", [])
        if item.get("status") == "running"
    ]
    if not running:
        return False
    if len(running) == 1 and running[0].get("phase") == phase:
        return True
    raise LeanProductionError(
        f"timer already has another running phase: {running[0].get('phase')}"
    )


def _invoke_phase(
    *,
    timer: Path | None,
    phase: str,
    action: Callable[[], int],
    summary_path: Path,
    input_roots: Sequence[Path],
    output_roots: Sequence[Path],
    require_single_model_attempt: bool = False,
) -> tuple[int, dict[str, Any]]:
    if timer is not None and not _phase_is_running(timer, phase):
        start_phase(timer, phase=phase, input_artifact_roots=input_roots)
    started = time.perf_counter_ns()
    try:
        return_code = action()
        summary = (
            _load_json(summary_path, label=f"{phase} summary")
            if summary_path.is_file()
            else {}
        )
        if require_single_model_attempt:
            lifecycle = summary.get("lifecycle")
            if not isinstance(lifecycle, Mapping):
                raise _ModelLifecycleContractError(
                    f"{phase} result misses model lifecycle evidence",
                    phase=phase,
                    summary=summary,
                )
            attempt_count = lifecycle.get("runner_attempt_count")
            retry_count = lifecycle.get("runner_retry_count")
            model_invoked = summary.get("model_invoked")
            lifecycle_valid = (
                model_invoked is True
                and type(attempt_count) is int
                and attempt_count == 1
                and type(retry_count) is int
                and retry_count == 0
            ) or (
                model_invoked is False
                and type(attempt_count) is int
                and attempt_count == 0
                and type(retry_count) is int
                and retry_count == 0
            )
            if not lifecycle_valid:
                raise _ModelLifecycleContractError(
                    f"{phase} violated the one-attempt/no-retry route contract",
                    phase=phase,
                    summary=summary,
                )
        metrics = {
            "wall_ms": (time.perf_counter_ns() - started) // 1_000_000,
            "return_code": return_code,
            "usage": summary.get("usage"),
            "model_invoked": summary.get("model_invoked"),
            "lifecycle": summary.get("lifecycle"),
            "stage_summary": summary,
        }
        phase_status = (
            "completed"
            if return_code == 0 and summary.get("decision") != "blocked"
            else "blocked"
            if return_code == 3 or summary.get("decision") == "blocked"
            else "terminal-failed"
        )
        if timer is not None:
            finish_phase(
                timer,
                phase=phase,
                status=phase_status,
                metrics=metrics,
                input_artifact_roots=input_roots,
                output_artifact_roots=output_roots,
            )
        return return_code, summary
    except Exception as exc:
        failure_summary: dict[str, Any] = {}
        if summary_path.is_file():
            try:
                failure_summary = _load_json(
                    summary_path, label=f"{phase} failure summary"
                )
            except StandardScopeBridgeError:
                # Preserve the action failure.  Invalid/missing lifecycle evidence
                # is represented as unknown by the terminal aggregate.
                failure_summary = {}
        timer_failure: Exception | None = None
        if timer is not None:
            try:
                finish_phase(
                    timer,
                    phase=phase,
                    status="terminal-failed",
                    metrics={
                        "wall_ms": (time.perf_counter_ns() - started) // 1_000_000,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                        "usage": failure_summary.get("usage"),
                        "model_invoked": failure_summary.get("model_invoked"),
                        "lifecycle": failure_summary.get("lifecycle"),
                        "stage_summary": failure_summary,
                    },
                    input_artifact_roots=input_roots,
                    output_artifact_roots=output_roots,
                )
            except Exception as reporting_exc:  # noqa: BLE001 - retain model evidence.
                timer_failure = reporting_exc
        if require_single_model_attempt:
            if isinstance(exc, _ModelLifecycleContractError):
                raise
            raise _ModelPhaseExecutionError(
                exc,
                phase=phase,
                summary=failure_summary,
            ) from exc
        if timer_failure is not None:
            raise timer_failure from exc
        raise


def _runtime_paths(runtime_dir: Path, stage: str, decision_name: str) -> dict[str, Path]:
    root = runtime_dir / stage
    return {
        "root": root,
        "decision": root / decision_name,
        "events": root / "events.ndjson",
        "stderr": root / "stderr.txt",
        "summary": root / "summary.json",
        "schema": root / "output-schema.json",
        "preflight": root / "preflight.json",
        "terminal_receipt": root / "terminal-receipt.json",
        "profile": root / "scope-execution-profile.json",
        "backend": root / "backend-selection.json",
    }


def _relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _file_sha256(path: Path, *, label: str) -> str:
    if not path.is_file():
        raise StandardScopeBridgeError(
            f"published handoff misses {label}: {path}"
        )
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise StandardScopeBridgeError(
            f"cannot hash published {label}: {path}: {exc}"
        ) from exc
    return digest.hexdigest()


def load_published_handoff_receipt(
    repo_root: Path,
    handoff_dir: Path,
    *,
    expected_prepared_context_sha256: str,
    expected_publication_owner_token: str,
) -> dict[str, Any]:
    """Validate the authoritative commit receipt inside an atomic handoff."""

    try:
        expected_publication_owner_token = validate_publication_owner_token(
            expected_publication_owner_token,
            label="expected_publication_owner_token",
        )
    except BoundedScopeBoundaryError as exc:
        raise StandardScopeBridgeError(str(exc)) from exc

    # Keep the already-normalized lexical paths supplied by the wrapper.  On
    # Windows, resolving again after the directory appears can expand an 8.3
    # parent alias for only one operand and make two identical paths fail
    # ``relative_to``.
    repo_root = repo_root if repo_root.is_absolute() else repo_root.absolute()
    handoff_dir = (
        handoff_dir if handoff_dir.is_absolute() else handoff_dir.absolute()
    )
    if not handoff_dir.is_dir():
        raise StandardScopeBridgeError(
            "materializer did not publish the requested handoff directory"
        )
    receipt = _load_json(
        handoff_dir / "semantic-design-bridge-receipt.json",
        label="semantic design bridge receipt",
    )
    required_receipt_fields = {
        "version": 1,
        "contract": "scope-v2-to-semantic-design-v1",
        "status": "verified",
        "materialization_status": "materialized",
    }
    if any(receipt.get(key) != value for key, value in required_receipt_fields.items()):
        raise StandardScopeBridgeError(
            "published handoff has an invalid semantic bridge receipt identity"
        )
    if receipt.get("prepared_context_sha256") != expected_prepared_context_sha256:
        raise StandardScopeBridgeError(
            "published handoff is not bound to the current prepared context digest"
        )
    if (
        receipt.get("publication_ownership_contract_version") != 1
        or receipt.get("publication_owner_token")
        != expected_publication_owner_token
    ):
        raise StandardScopeBridgeError(
            "published handoff has no valid current-invocation ownership binding"
        )
    artifact_bindings = (
        (
            "scope_boundary_artifact_sha256",
            handoff_dir / "scope-boundary-decision.json",
            "scope boundary artifact",
        ),
        (
            "semantic_design_artifact_sha256",
            handoff_dir / "semantic-design.json",
            "semantic design artifact",
        ),
    )
    for receipt_field, artifact, label in artifact_bindings:
        expected_artifact_digest = receipt.get(receipt_field)
        if (
            not isinstance(expected_artifact_digest, str)
            or _file_sha256(artifact, label=label) != expected_artifact_digest
        ):
            raise StandardScopeBridgeError(
                f"published {label} does not match receipt.{receipt_field}"
            )
    publication = receipt.get("publication")
    if not isinstance(publication, Mapping):
        raise StandardScopeBridgeError(
            "published handoff misses atomic publication evidence"
        )
    declared_handoff = publication.get("final_handoff")
    if not isinstance(declared_handoff, str) or not declared_handoff.strip():
        raise StandardScopeBridgeError(
            "published handoff misses its repository-relative final path"
        )
    declared_relative = PurePosixPath(declared_handoff)
    if declared_relative.is_absolute() or any(
        part in {"", ".", ".."} for part in declared_relative.parts
    ):
        raise StandardScopeBridgeError(
            "published handoff final path must be normalized and repository-relative"
        )
    declared_path = repo_root.joinpath(*declared_relative.parts)
    try:
        same_handoff = os.path.samefile(declared_path, handoff_dir)
    except OSError:
        same_handoff = False
    if publication.get("status") != "atomic-renamed" or not same_handoff:
        raise StandardScopeBridgeError(
            "published handoff does not attest the requested atomic rename"
        )
    readiness = receipt.get("downstream_evidence_readiness")
    if not isinstance(readiness, Mapping) or (
        readiness.get("status") != "passed"
        or readiness.get("canonical_preflight")
        != "source-reviewer.prepare_evidence_set"
    ):
        raise StandardScopeBridgeError(
            "published handoff misses canonical downstream evidence preflight"
        )
    manifest_digest = receipt.get("source_assertion_manifest_digest")
    if (
        not isinstance(manifest_digest, str)
        or not manifest_digest
        or readiness.get("published_manifest_digest") != manifest_digest
    ):
        raise StandardScopeBridgeError(
            "published handoff evidence readiness is not bound to the receipt "
            "source assertion manifest digest"
        )
    manifest_payload = _load_json(
        handoff_dir / "source-assertions.json",
        label="published source assertion manifest",
    )
    try:
        actual_manifest_digest = SourceAssertionManifest.from_dict(
            manifest_payload
        ).digest
    except SourceAssertionContractError as exc:
        raise StandardScopeBridgeError(
            f"published source assertion manifest is invalid: {exc}"
        ) from exc
    if actual_manifest_digest != manifest_digest:
        raise StandardScopeBridgeError(
            "published source assertion manifest canonical digest does not match "
            "the receipt"
        )
    return receipt


def _materialization_summary_from_receipt(
    reported: Mapping[str, Any],
    *,
    receipt: Mapping[str, Any],
    reporting_error: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    publication = dict(receipt["publication"])
    readiness = dict(receipt["downstream_evidence_readiness"])
    if reported.get("status") == "completed":
        reported_publication = reported.get("publication")
        reported_readiness = reported.get("downstream_evidence_readiness")
        publication_valid = isinstance(reported_publication, Mapping) and (
            reported_publication.get("status") == "atomic-renamed"
            and reported_publication.get("final_handoff")
            == publication["final_handoff"]
        )
        readiness_valid = isinstance(reported_readiness, Mapping) and (
            reported_readiness.get("status") == "passed"
            and reported_readiness.get("canonical_preflight")
            == "source-reviewer.prepare_evidence_set"
        )
        if publication_valid and readiness_valid:
            return dict(reported)
        reporting_error = {
            "error_type": "StandardScopeBridgeError",
            "error": (
                "completed materializer summary omitted required commit evidence; "
                "recovered from authoritative handoff receipt"
            ),
        }
    recovered = {
        "status": "completed",
        "publication": publication,
        "downstream_evidence_readiness": readiness,
        "summary_recovered_from_published_handoff": True,
    }
    if reported:
        recovered["reported_summary"] = dict(reported)
    if reporting_error is not None:
        recovered["reporting_error"] = dict(reporting_error)
    return recovered


def _unique_paths(paths: Sequence[Path]) -> tuple[Path, ...]:
    return tuple(dict.fromkeys(path.resolve() for path in paths))


def _registered_source_inputs(
    repo_root: Path,
    context: Mapping[str, Any],
    *,
    manifest_binding: str | None = None,
) -> tuple[Path, ...]:
    raw_sources = context.get("sources", [])
    if not isinstance(raw_sources, list):
        raise StandardScopeBridgeError("prepared context.sources must be an array")
    result: list[Path] = []
    for index, item in enumerate(raw_sources):
        if not isinstance(item, Mapping):
            raise StandardScopeBridgeError(
                f"prepared context.sources[{index}] must be an object"
            )
        if manifest_binding is not None and item.get("manifest_binding") != manifest_binding:
            continue
        value = item.get("path")
        if not isinstance(value, str) or not value.strip():
            raise StandardScopeBridgeError(
                f"prepared context.sources[{index}].path is required"
            )
        result.append(_under(repo_root, Path(value), label="registered source"))
    return _unique_paths(result)


def _materialization_source_inputs(
    repo_root: Path,
    context: Mapping[str, Any],
) -> tuple[Path, ...]:
    result = list(_registered_source_inputs(repo_root, context))
    for key in ("source_row_extraction_spec", "source_row_baseline"):
        value = context.get(key)
        if value is not None:
            if not isinstance(value, str) or not value.strip():
                raise StandardScopeBridgeError(f"prepared context.{key} must be a path")
            result.append(_under(repo_root, Path(value), label=f"context.{key}"))
    bounded_evidence = context.get("bounded_evidence", {})
    if not isinstance(bounded_evidence, Mapping):
        raise StandardScopeBridgeError("prepared context.bounded_evidence must be an object")
    for key, value in bounded_evidence.items():
        if not isinstance(value, str) or not value.strip():
            raise StandardScopeBridgeError(
                f"prepared context.bounded_evidence.{key} must be a path"
            )
        result.append(
            _under(repo_root, Path(value), label=f"context.bounded_evidence.{key}")
        )
    return _unique_paths(result)


def _record_model_summary(
    terminal: dict[str, Any],
    summary: Mapping[str, Any],
) -> None:
    lifecycle = summary.get("lifecycle")
    attempt_count = (
        lifecycle.get("runner_attempt_count")
        if isinstance(lifecycle, Mapping)
        else None
    )
    retry_count = (
        lifecycle.get("runner_retry_count")
        if isinstance(lifecycle, Mapping)
        else None
    )
    if not (
        type(attempt_count) is int
        and attempt_count >= 0
        and type(retry_count) is int
        and retry_count >= 0
        and type(terminal.get("attempt_count")) is int
        and type(terminal.get("retry_count")) is int
    ):
        terminal["attempt_count"] = None
        terminal["retry_count"] = None
    else:
        terminal["attempt_count"] = int(terminal["attempt_count"]) + attempt_count
        terminal["retry_count"] = int(terminal["retry_count"]) + retry_count
    if summary.get("model_invoked") is True:
        terminal["model_stage_count"] = int(terminal["model_stage_count"]) + 1


def _model_args(
    *,
    paths: Mapping[str, Path],
    repo_root: Path,
    context: Path,
    images: Sequence[Path],
    codex_command: str | None,
    measurement_mode: str,
    timeout_seconds: int | None = None,
) -> list[str]:
    result = [
        "--repo-root", str(repo_root),
        "--context", str(context),
        "--decision-output", str(paths["decision"]),
        "--events-output", str(paths["events"]),
        "--stderr-output", str(paths["stderr"]),
        "--summary-output", str(paths["summary"]),
        "--schema-output", str(paths["schema"]),
        "--preflight-output", str(paths["preflight"]),
        "--terminal-receipt-output", str(paths["terminal_receipt"]),
        "--scope-execution-profile-output", str(paths["profile"]),
        "--backend-selection-output", str(paths["backend"]),
        "--measurement-mode", measurement_mode,
    ]
    if codex_command:
        result.extend(("--codex-command", codex_command))
    if timeout_seconds is not None:
        result.extend(("--timeout-seconds", str(timeout_seconds)))
    for image in images:
        result.extend(("--image", str(image)))
    return result


def _aggregate_usage(summaries: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    keys = {
        key
        for summary in summaries
        for key in (
            summary.get("usage", {}).keys()
            if isinstance(summary.get("usage"), Mapping)
            else ()
        )
    }
    result: dict[str, Any] = {}
    for key in sorted(keys):
        values = [
            summary.get("usage", {}).get(key)
            for summary in summaries
            if isinstance(summary.get("usage"), Mapping)
        ]
        result[key] = (
            sum(value for value in values if type(value) is int)
            if values and all(type(value) is int for value in values)
            else "unavailable"
        )
    return result


def _validate_one_attempt_summary(
    summary: Mapping[str, Any], *, label: str
) -> None:
    lifecycle = summary.get("lifecycle")
    if not isinstance(lifecycle, Mapping):
        raise StandardScopeBridgeError(f"{label} misses model lifecycle evidence")
    if not (
        summary.get("model_invoked") is True
        and lifecycle.get("runner_attempt_count") == 1
        and lifecycle.get("runner_retry_count") == 0
    ):
        raise StandardScopeBridgeError(
            f"{label} violated the one-attempt/no-retry shard contract"
        )


def _materialize_non_testable_shard_result(
    *,
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
    paths: Mapping[str, Path],
) -> dict[str, Any]:
    started = time.perf_counter_ns()
    design, receipt = materialize_non_testable_semantic_shard(context, boundary)
    preflight = validate_semantic_input_preflight(
        context,
        boundary,
        tuple(
            dict(item)
            for item in context.get("approved_clarifications", [])
            if isinstance(item, Mapping)
        ),
    )
    _write_json_atomic(paths["decision"], design)
    _write_json_atomic(paths["preflight"], preflight)
    _write_json_atomic(
        paths["schema"],
        semantic_design_output_schema(
            [str(item["source_row_id"]) for item in context["source_rows"]],
            require_ready=True,
            expected_minimum_obligation_count=0,
            expected_dependency_count=len(boundary["dependencies"]),
            expected_dictionary_count=0,
            expected_negative_signal_count=0,
            expected_requiredness_signal_count=0,
        ),
    )
    receipt_path = paths["root"] / "deterministic-materialization-receipt.json"
    _write_json_atomic(receipt_path, receipt)
    summary = {
        "status": "completed",
        "decision": "ready",
        "return_code": 0,
        "execution_route": DETERMINISTIC_NON_TESTABLE_EXECUTION_MODE,
        "model_invoked": False,
        "duration_ms": (time.perf_counter_ns() - started) // 1_000_000,
        "prompt_bytes": 0,
        "schema_bytes": paths["schema"].stat().st_size,
        "usage": {
            "input_tokens": 0,
            "cached_input_tokens": 0,
            "cache_write_input_tokens": 0,
            "output_tokens": 0,
            "reasoning_output_tokens": 0,
        },
        "lifecycle": {
            "runner_attempt_count": 0,
            "runner_retry_count": 0,
            "process_spawn_count": 0,
        },
        "source_row_count": receipt["source_row_count"],
        "assertion_count": receipt["validation"]["assertion_count"],
        "obligation_count": 0,
        "deterministic_receipt": receipt_path.name,
    }
    _write_json_atomic(paths["summary"], summary)
    return summary


def _run_sharded_semantic_design(
    *,
    repo_root: Path,
    context_path: Path,
    boundary_path: Path,
    semantic_paths: Mapping[str, Path],
    images: Sequence[Path],
    codex_command: str | None,
    measurement_mode: str,
    semantic_runner: Callable[[Sequence[str] | None], int],
    mode: str,
    max_included_rows: int,
    max_source_rows: int,
    max_shards: int,
    max_semantic_weight: int | None = None,
    timeout_seconds: int | None = None,
) -> tuple[int, dict[str, Any]]:
    started = time.perf_counter_ns()
    context = _load_json(context_path, label="prepared context")
    boundary = _load_json(boundary_path, label="scope boundary decision")
    preparation_started = time.perf_counter_ns()
    plan = build_semantic_shard_plan(
        context,
        boundary,
        mode=mode,
        max_included_rows=max_included_rows,
        max_source_rows=max_source_rows,
        max_shards=max_shards,
        max_semantic_weight=max_semantic_weight,
    )
    semantic_root = semantic_paths["root"]
    _write_json_atomic(semantic_root / "semantic-shard-plan.json", plan)
    preparation_ms = (time.perf_counter_ns() - preparation_started) // 1_000_000
    if plan["mode"] == "single":
        shard = plan["shards"][0]
        if shard["execution_mode"] == DETERMINISTIC_NON_TESTABLE_EXECUTION_MODE:
            summary = _materialize_non_testable_shard_result(
                context=context,
                boundary=boundary,
                paths=semantic_paths,
            )
            summary["sharding"] = {
                "mode": "single",
                "trigger": plan["trigger"],
                "plan": "semantic-shard-plan.json",
                "preparation_ms": preparation_ms,
                "merge_ms": 0,
                "model_shard_count": 0,
                "deterministic_shard_count": 1,
                "complexity": plan["complexity"],
            }
            _write_json_atomic(semantic_paths["summary"], summary)
            return 0, summary
        arguments = _model_args(
            paths=semantic_paths,
            repo_root=repo_root,
            context=context_path,
            images=images,
            codex_command=codex_command,
            measurement_mode=measurement_mode,
            timeout_seconds=timeout_seconds,
        )
        arguments.extend(("--scope-boundary-decision", str(boundary_path)))
        return_code = semantic_runner(arguments)
        summary = (
            _load_json(semantic_paths["summary"], label="semantic-design summary")
            if semantic_paths["summary"].is_file()
            else {}
        )
        summary["sharding"] = {
            "mode": "single",
            "trigger": plan["trigger"],
            "plan": "semantic-shard-plan.json",
            "preparation_ms": preparation_ms,
            "merge_ms": 0,
            "model_shard_count": 1,
            "deterministic_shard_count": 0,
            "complexity": plan["complexity"],
        }
        _write_json_atomic(semantic_paths["summary"], summary)
        return return_code, summary

    context_mockup_locators = context.get("mockup_locators")
    boundary_mockup_locators = boundary.get("mockup_locators")
    reuse_boundary_mockup_projection = (
        bool(images)
        and isinstance(context_mockup_locators, list)
        and bool(context_mockup_locators)
        and boundary_mockup_locators == context_mockup_locators
    )
    semantic_model_images: Sequence[Path] = (
        () if reuse_boundary_mockup_projection else images
    )
    mockup_transport = {
        "mode": (
            "scope-boundary-locator-projection"
            if reuse_boundary_mockup_projection
            else "direct-image-attachment"
            if images
            else "none"
        ),
        "source_image_count": len(images),
        "attached_image_count_per_model_shard": len(semantic_model_images),
        "mockup_locator_count": (
            len(boundary_mockup_locators)
            if isinstance(boundary_mockup_locators, list)
            else 0
        ),
    }
    shard_summaries: list[dict[str, Any]] = []
    shard_outputs: dict[str, dict[str, Any]] = {}
    for shard in plan["shards"]:
        shard_id = str(shard["shard_id"])
        shard_root = semantic_root / "shards" / shard_id
        shard_context, shard_boundary = project_semantic_shard(context, boundary, shard)
        shard_context_path = shard_root / "prepared-bounded-context.json"
        shard_boundary_path = shard_root / "scope-boundary-decision.json"
        _write_json_atomic(shard_context_path, shard_context)
        _write_json_atomic(shard_boundary_path, shard_boundary)
        paths = _runtime_paths(semantic_root / "shards", shard_id, "semantic-design.json")
        shard_started = time.perf_counter_ns()
        execution_mode = str(shard.get("execution_mode", ""))
        projected_included_count = sum(
            item.get("disposition") == "included"
            for item in shard_boundary["source_decisions"]
        )
        if projected_included_count != shard["owned_included_row_count"]:
            raise StandardScopeBridgeError(
                f"{shard_id} projected included-row count drifted from its plan"
            )
        if execution_mode == DETERMINISTIC_NON_TESTABLE_EXECUTION_MODE:
            summary = _materialize_non_testable_shard_result(
                context=shard_context,
                boundary=shard_boundary,
                paths=paths,
            )
            return_code = 0
        elif execution_mode == MODEL_EXECUTION_MODE:
            arguments = _model_args(
                paths=paths,
                repo_root=repo_root,
                context=shard_context_path,
                images=semantic_model_images,
                codex_command=codex_command,
                measurement_mode=measurement_mode,
                timeout_seconds=timeout_seconds,
            )
            arguments.extend(("--scope-boundary-decision", str(shard_boundary_path)))
            return_code = semantic_runner(arguments)
            summary = (
                _load_json(paths["summary"], label=f"{shard_id} summary")
                if paths["summary"].is_file()
                else {}
            )
        else:
            raise StandardScopeBridgeError(
                f"{shard_id} has unsupported execution_mode={execution_mode}"
            )
        summary = dict(summary)
        summary["shard_id"] = shard_id
        summary["execution_mode"] = execution_mode
        summary["owned_source_row_count"] = shard["owned_source_row_count"]
        summary["owned_included_row_count"] = shard["owned_included_row_count"]
        summary["owned_semantic_weight"] = shard["owned_semantic_weight"]
        summary["mockup_transport"] = dict(mockup_transport)
        summary["orchestrator_wall_ms"] = (
            time.perf_counter_ns() - shard_started
        ) // 1_000_000
        shard_input_paths = _unique_paths(
            (
                shard_context_path,
                shard_boundary_path,
                *_registered_source_inputs(
                    repo_root,
                    shard_context,
                    manifest_binding="approved-clarification",
                ),
                *(
                    semantic_model_images
                    if execution_mode == MODEL_EXECUTION_MODE
                    else ()
                ),
            )
        )
        shard_output_paths = _unique_paths(
            tuple(path for path in paths.values() if path != paths["root"] and path.is_file())
        )
        summary["input_artifacts"] = {
            "file_count": len(shard_input_paths),
            "bytes": sum(path.stat().st_size for path in shard_input_paths),
        }
        summary["output_artifacts"] = {
            "file_count": len(shard_output_paths),
            "bytes": sum(path.stat().st_size for path in shard_output_paths),
        }
        shard_summaries.append(summary)
        if return_code != 0 or summary.get("decision") != "ready":
            aggregate = {
                "status": "blocked" if return_code == 3 else "terminal-failed",
                "decision": summary.get("decision", "failed"),
                "return_code": return_code or 3,
                "model_invoked": any(item.get("model_invoked") is True for item in shard_summaries),
                "duration_ms": (time.perf_counter_ns() - started) // 1_000_000,
                "usage": _aggregate_usage(shard_summaries),
                "lifecycle": {
                    "runner_attempt_count": sum(
                        int(item.get("lifecycle", {}).get("runner_attempt_count", 0))
                        for item in shard_summaries
                        if isinstance(item.get("lifecycle"), Mapping)
                    ),
                    "runner_retry_count": sum(
                        int(item.get("lifecycle", {}).get("runner_retry_count", 0))
                        for item in shard_summaries
                        if isinstance(item.get("lifecycle"), Mapping)
                    ),
                },
                "sharding": {
                    "mode": "sharded",
                    "plan": "semantic-shard-plan.json",
                    "preparation_ms": preparation_ms,
                    "merge_ms": 0,
                    "failed_shard": shard_id,
                    "completed_shard_count": len(shard_outputs),
                    "model_shard_count": sum(
                        item.get("execution_mode") == MODEL_EXECUTION_MODE
                        for item in shard_summaries
                    ),
                    "deterministic_shard_count": sum(
                        item.get("execution_mode")
                        == DETERMINISTIC_NON_TESTABLE_EXECUTION_MODE
                        for item in shard_summaries
                    ),
                    "complexity": plan["complexity"],
                    "mockup_transport": mockup_transport,
                    "shards": shard_summaries,
                },
            }
            _write_json_atomic(semantic_paths["summary"], aggregate)
            return int(aggregate["return_code"]), aggregate
        if execution_mode == MODEL_EXECUTION_MODE:
            _validate_one_attempt_summary(summary, label=shard_id)
        shard_outputs[shard_id] = _load_json(paths["decision"], label=f"{shard_id} design")

    merge_started = time.perf_counter_ns()
    clarifications = load_approved_clarifications(repo_root, context)
    merged, merge_receipt = merge_semantic_shards(
        context, boundary, clarifications, plan, shard_outputs
    )
    merge_ms = (time.perf_counter_ns() - merge_started) // 1_000_000
    _write_json_atomic(semantic_paths["decision"], merged)
    _write_json_atomic(semantic_root / "semantic-shard-merge-receipt.json", merge_receipt)
    full_preflight = validate_semantic_input_preflight(
        context, boundary, clarifications
    )
    _write_json_atomic(semantic_paths["preflight"], full_preflight)
    _write_json_atomic(
        semantic_paths["schema"],
        semantic_design_output_schema(
            [str(item["source_row_id"]) for item in context["source_rows"]],
            require_ready=True,
            expected_minimum_obligation_count=semantic_design_minimum_obligation_count(
                full_preflight,
                boundary,
            ),
            expected_dependency_count=len(boundary["dependencies"]),
            expected_dictionary_count=len(full_preflight["dictionary_registry"]),
            expected_negative_signal_count=full_preflight["negative_signal_count"],
            expected_requiredness_signal_count=full_preflight["requiredness_signal_count"],
        ),
    )
    aggregate = {
        "status": "completed",
        "decision": "ready",
        "model_invoked": any(
            item.get("model_invoked") is True for item in shard_summaries
        ),
        "duration_ms": (time.perf_counter_ns() - started) // 1_000_000,
        "usage": _aggregate_usage(shard_summaries),
        "prompt_bytes": sum(
            int(item.get("prompt_bytes", 0))
            for item in shard_summaries
            if type(item.get("prompt_bytes", 0)) is int
        ),
        "schema_bytes": sum(
            int(item.get("schema_bytes", 0))
            for item in shard_summaries
            if type(item.get("schema_bytes", 0)) is int
        ),
        "input_artifacts": {
            "file_count": sum(
                int(item.get("input_artifacts", {}).get("file_count", 0))
                for item in shard_summaries
            ),
            "bytes": sum(
                int(item.get("input_artifacts", {}).get("bytes", 0))
                for item in shard_summaries
            ),
        },
        "output_artifacts": {
            "file_count": sum(
                int(item.get("output_artifacts", {}).get("file_count", 0))
                for item in shard_summaries
            ),
            "bytes": sum(
                int(item.get("output_artifacts", {}).get("bytes", 0))
                for item in shard_summaries
            ),
        },
        "lifecycle": {
            "runner_attempt_count": sum(
                int(item.get("lifecycle", {}).get("runner_attempt_count", 0))
                for item in shard_summaries
                if isinstance(item.get("lifecycle"), Mapping)
            ),
            "runner_retry_count": sum(
                int(item.get("lifecycle", {}).get("runner_retry_count", 0))
                for item in shard_summaries
                if isinstance(item.get("lifecycle"), Mapping)
            ),
        },
        "source_row_count": len(context["source_rows"]),
        "assertion_count": merge_receipt["validation"]["assertion_count"],
        "obligation_count": merge_receipt["validation"]["obligation_count"],
        "sharding": {
            "mode": "sharded",
            "plan": "semantic-shard-plan.json",
            "merge_receipt": "semantic-shard-merge-receipt.json",
            "preparation_ms": preparation_ms,
            "merge_ms": merge_ms,
            "shard_count": len(shard_summaries),
            "model_shard_count": sum(
                item.get("execution_mode") == MODEL_EXECUTION_MODE
                for item in shard_summaries
            ),
            "deterministic_shard_count": sum(
                item.get("execution_mode")
                == DETERMINISTIC_NON_TESTABLE_EXECUTION_MODE
                for item in shard_summaries
            ),
            "execution": "sequential-fresh-sessions",
            "complexity": plan["complexity"],
            "mockup_transport": mockup_transport,
            "shards": shard_summaries,
        },
    }
    _write_json_atomic(semantic_paths["summary"], aggregate)
    return 0, aggregate


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Run the standard-production boundary-v2, semantic-design and atomic "
            "materialization route once, with separate phase metrics."
        )
    )
    result.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    result.add_argument("--context", type=Path, required=True)
    result.add_argument("--runtime-dir", type=Path, required=True)
    result.add_argument("--handoff-dir", type=Path, required=True)
    result.add_argument("--timer", type=Path)
    result.add_argument("--summary-output", type=Path)
    result.add_argument("--publication-owner-token")
    result.add_argument("--image", action="append", type=Path, default=[])
    result.add_argument("--codex-command")
    result.add_argument(
        "--measurement-mode",
        choices=("production", "observational"),
        default="observational",
        help=(
            "Observational is the no-deadline baseline mode requested for the next "
            "timing run; production keeps each model runner's normal deadline."
        ),
    )
    result.add_argument(
        "--semantic-sharding",
        choices=("off", "auto", "on"),
        default="off",
    )
    result.add_argument("--semantic-shard-max-included-rows", type=int, default=12)
    result.add_argument("--semantic-shard-max-source-rows", type=int, default=18)
    result.add_argument("--semantic-shard-max-shards", type=int, default=8)
    result.add_argument(
        "--semantic-shard-max-weight",
        type=int,
        default=0,
        help="Zero disables source-derived semantic-weight capacity.",
    )
    return result


def main(
    argv: Sequence[str] | None = None,
    *,
    boundary_runner: Callable[[Sequence[str] | None], int] = boundary_main,
    semantic_runner: Callable[[Sequence[str] | None], int] = semantic_main,
    materializer_runner: Callable[[Sequence[str] | None], int] = materialize_main,
) -> int:
    args = parser().parse_args(argv)
    started = time.perf_counter_ns()
    terminal: dict[str, Any] = {
        "version": 1,
        "route": "standard-production-semantic-design-bridge",
        "status": "running",
        "measurement_mode": args.measurement_mode,
        "attempt_count": 0,
        "retry_count": 0,
        "fallback_count": 0,
        "model_stage_count": 0,
    }
    summary_output: Path | None = None
    summary_safe_for_reporting = False
    handoff_dir: Path | None = None
    handoff_committed = False
    handoff_absent_before_run = False

    def add_reporting_error(stage: str, exc: BaseException) -> None:
        errors = terminal.setdefault("reporting_errors", [])
        assert isinstance(errors, list)
        errors.append(
            {
                "stage": stage,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )

    def emit(return_code: int, *, error: bool) -> int:
        if summary_output is not None and summary_safe_for_reporting:
            try:
                _write_json_atomic(summary_output, terminal)
            except Exception as exc:  # noqa: BLE001 - terminal reporting boundary.
                add_reporting_error("terminal-summary", exc)
        _print_best_effort(terminal, error=error)
        return return_code

    try:
        repo_root = args.repo_root.resolve()
        runtime_dir = _under(repo_root, args.runtime_dir, label="runtime-dir")
        summary_output = _under(
            repo_root,
            args.summary_output
            or runtime_dir / "standard-scope-bridge-summary.json",
            label="summary-output",
        )
        context = _under(repo_root, args.context, label="context")
        handoff_dir = _under(repo_root, args.handoff_dir, label="handoff-dir")
        timer = _under(repo_root, args.timer, label="timer") if args.timer else None
        images: tuple[Path, ...] = ()
        clarification_inputs: tuple[Path, ...] = ()
        materialization_source_inputs: tuple[Path, ...] = ()
        if not context.is_file():
            raise StandardScopeBridgeError(f"context is missing: {context}")
        context_payload = _load_json(context, label="prepared context")
        try:
            publication_owner_token = validate_publication_owner_token(
                args.publication_owner_token or str(uuid.uuid4()),
                label="publication-owner-token",
            )
        except BoundedScopeBoundaryError as exc:
            raise StandardScopeBridgeError(str(exc)) from exc
        terminal["publication_owner_token"] = publication_owner_token
        try:
            ft_slug = validate_stable_path_segment(
                context_payload.get("ft_slug"), label="prepared context.ft_slug"
            )
        except BoundedScopeBoundaryError as exc:
            raise StandardScopeBridgeError(str(exc)) from exc
        expected_context_digest = prepared_context_sha256(context_payload)
        clarification_inputs = _registered_source_inputs(
            repo_root,
            context_payload,
            manifest_binding="approved-clarification",
        )
        materialization_source_inputs = _materialization_source_inputs(
            repo_root,
            context_payload,
        )
        expected_ft_root = (repo_root / "fts" / ft_slug).resolve()
        if not _relative_to(handoff_dir, expected_ft_root):
            raise StandardScopeBridgeError(
                "handoff-dir must stay inside the FT package named by context.ft_slug"
            )
        declared_mockups = context_payload.get("mockups", [])
        if not isinstance(declared_mockups, list) or any(
            not isinstance(item, Mapping)
            or not isinstance(item.get("path"), str)
            or not str(item["path"]).strip()
            for item in declared_mockups
        ):
            raise StandardScopeBridgeError(
                "prepared context.mockups must be an object array with paths"
            )
        declared_images = tuple(
            _under(repo_root, Path(str(item["path"])), label="context mockup")
            for item in declared_mockups
        )
        explicit_images = tuple(
            _under(repo_root, item, label="image") for item in args.image
        )
        if explicit_images and (
            len(explicit_images) != len(set(explicit_images))
            or set(explicit_images) != set(declared_images)
        ):
            raise StandardScopeBridgeError(
                "explicit image attachments must equal the prepared context mockup set"
            )
        images = explicit_images or declared_images
        missing_inputs = [
            str(path)
            for path in _unique_paths(
                (*images, *clarification_inputs, *materialization_source_inputs)
            )
            if not path.is_file()
        ]
        if missing_inputs:
            raise StandardScopeBridgeError(
                "registered input is missing: " + ", ".join(missing_inputs)
            )
        if _relative_to(runtime_dir, handoff_dir) or _relative_to(
            handoff_dir, runtime_dir
        ):
            raise StandardScopeBridgeError(
                "runtime-dir and handoff-dir must not overlap"
            )
        if not _relative_to(summary_output, runtime_dir):
            raise StandardScopeBridgeError(
                "summary-output must stay inside runtime-dir so it cannot pre-create "
                "the atomic handoff target"
            )
        protected_inputs = _unique_paths(
            (
                context,
                *images,
                *clarification_inputs,
                *materialization_source_inputs,
                *((timer,) if timer else ()),
            )
        )
        if any(_relative_to(path, runtime_dir) for path in protected_inputs):
            raise StandardScopeBridgeError(
                "runtime-dir must not contain a protected input artifact"
            )
        if any(_relative_to(path, handoff_dir) for path in protected_inputs):
            raise StandardScopeBridgeError(
                "handoff-dir must not contain a protected input artifact"
            )
        if runtime_dir.exists() and any(runtime_dir.iterdir()):
            raise StandardScopeBridgeError(
                f"runtime-dir must be new or empty: {runtime_dir}"
            )
        if handoff_dir.exists():
            raise StandardScopeBridgeError(
                f"handoff-dir must not exist before atomic publication: {handoff_dir}"
            )
        handoff_absent_before_run = True
        summary_safe_for_reporting = True
        runtime_dir.mkdir(parents=True, exist_ok=True)

        boundary = _runtime_paths(runtime_dir, "scope-analysis", "scope-boundary-decision.json")
        boundary_args = _model_args(
            paths=boundary,
            repo_root=repo_root,
            context=context,
            images=images,
            codex_command=args.codex_command,
            measurement_mode=args.measurement_mode,
        )
        boundary_args.extend(("--contract-version", "2", "--scope-execution-profile", "standard-production"))
        boundary_code, boundary_summary = _invoke_phase(
            timer=timer,
            phase="scope-analysis",
            action=lambda: boundary_runner(boundary_args),
            summary_path=boundary["summary"],
            input_roots=(context, *images),
            output_roots=(boundary["root"],),
            require_single_model_attempt=True,
        )
        _record_model_summary(terminal, boundary_summary)
        terminal["scope_analysis"] = boundary_summary
        if boundary_code != 0 or boundary_summary.get("decision") != "ready":
            terminal.update(
                {
                    "status": (
                        "blocked-input"
                        if boundary_code == 3 or boundary_summary.get("decision") == "blocked"
                        else "terminal-failed"
                    ),
                    "stopped_after": "scope-analysis",
                    "return_code": boundary_code or 3,
                    "duration_ms": (time.perf_counter_ns() - started) // 1_000_000,
                }
            )
            return emit(int(terminal["return_code"]), error=False)
        if not boundary["decision"].is_file():
            raise StandardScopeBridgeError(
                "scope analyzer returned ready without a boundary decision artifact"
            )

        semantic = _runtime_paths(runtime_dir, "semantic-design", "semantic-design.json")
        semantic_args = _model_args(
            paths=semantic,
            repo_root=repo_root,
            context=context,
            images=images,
            codex_command=args.codex_command,
            measurement_mode=args.measurement_mode,
        )
        semantic_args.extend(
            ("--scope-boundary-decision", str(boundary["decision"]))
        )
        semantic_code, semantic_summary = _invoke_phase(
            timer=timer,
            phase="semantic-design",
            action=(
                (lambda: semantic_runner(semantic_args))
                if args.semantic_sharding == "off"
                else (
                    lambda: _run_sharded_semantic_design(
                        repo_root=repo_root,
                        context_path=context,
                        boundary_path=boundary["decision"],
                        semantic_paths=semantic,
                        images=images,
                        codex_command=args.codex_command,
                        measurement_mode=args.measurement_mode,
                        semantic_runner=semantic_runner,
                        mode=args.semantic_sharding,
                        max_included_rows=args.semantic_shard_max_included_rows,
                        max_source_rows=args.semantic_shard_max_source_rows,
                        max_shards=args.semantic_shard_max_shards,
                        max_semantic_weight=(
                            args.semantic_shard_max_weight or None
                        ),
                    )[0]
                )
            ),
            summary_path=semantic["summary"],
            input_roots=(
                context,
                boundary["decision"],
                *clarification_inputs,
                *images,
            ),
            output_roots=(semantic["root"],),
            require_single_model_attempt=args.semantic_sharding == "off",
        )
        _record_model_summary(terminal, semantic_summary)
        terminal["semantic_design"] = semantic_summary
        if semantic_code != 0 or semantic_summary.get("decision") != "ready":
            terminal.update(
                {
                    "status": (
                        "blocked-input"
                        if semantic_code == 3 or semantic_summary.get("decision") == "blocked"
                        else "terminal-failed"
                    ),
                    "stopped_after": "semantic-design",
                    "return_code": semantic_code or 3,
                    "duration_ms": (time.perf_counter_ns() - started) // 1_000_000,
                }
            )
            return emit(int(terminal["return_code"]), error=False)
        if not semantic["decision"].is_file():
            raise StandardScopeBridgeError(
                "semantic author returned ready without a semantic-design artifact"
            )

        materialize_summary = runtime_dir / "scope-materialization-summary.json"
        materialize_args = [
            "--repo-root", str(repo_root),
            "--context", str(context),
            "--scope-boundary-decision", str(boundary["decision"]),
            "--semantic-design", str(semantic["decision"]),
            "--handoff-dir", str(handoff_dir),
            "--publication-owner-token", publication_owner_token,
            "--summary-output", str(materialize_summary),
        ]
        materialization_summary: dict[str, Any] = {}
        materialize_code = 2
        materialize_reporting_error: dict[str, Any] | None = None
        try:
            materialize_code, materialization_summary = _invoke_phase(
                timer=timer,
                phase="scope-materialization",
                action=lambda: materializer_runner(materialize_args),
                summary_path=materialize_summary,
                input_roots=(
                    context,
                    boundary["decision"],
                    semantic["decision"],
                    *materialization_source_inputs,
                    *images,
                ),
                output_roots=(handoff_dir, materialize_summary),
            )
        except Exception as phase_exc:  # noqa: BLE001 - recover committed handoff.
            try:
                if not handoff_absent_before_run or not handoff_dir.is_dir():
                    raise StandardScopeBridgeError(
                        "scope handoff was not published during this invocation"
                    )
                handoff_receipt = load_published_handoff_receipt(
                    repo_root,
                    handoff_dir,
                    expected_prepared_context_sha256=expected_context_digest,
                    expected_publication_owner_token=publication_owner_token,
                )
            except Exception:
                raise phase_exc
            materialize_reporting_error = {
                "error_type": type(phase_exc).__name__,
                "error": str(phase_exc),
                "stage": "scope-materialization-reporting",
            }
        else:
            if materialize_code != 0:
                try:
                    if not handoff_absent_before_run or not handoff_dir.is_dir():
                        raise StandardScopeBridgeError(
                            "scope handoff was not published during this invocation"
                        )
                    handoff_receipt = load_published_handoff_receipt(
                        repo_root,
                        handoff_dir,
                        expected_prepared_context_sha256=expected_context_digest,
                        expected_publication_owner_token=publication_owner_token,
                    )
                except Exception:
                    terminal["scope_materialization"] = materialization_summary
                    terminal.update(
                        {
                            "status": "terminal-failed",
                            "stopped_after": "scope-materialization",
                            "return_code": materialize_code,
                            "duration_ms": (
                                time.perf_counter_ns() - started
                            ) // 1_000_000,
                        }
                    )
                    return emit(materialize_code, error=True)
                materialize_reporting_error = {
                    "error_type": "MaterializerReportingError",
                    "error": (
                        "materializer returned a non-zero code after publishing an "
                        "authoritative handoff"
                    ),
                    "reported_return_code": materialize_code,
                    "stage": "scope-materialization-reporting",
                }
            else:
                if not handoff_absent_before_run or not handoff_dir.is_dir():
                    raise StandardScopeBridgeError(
                        "scope handoff was not published during this invocation"
                    )
                handoff_receipt = load_published_handoff_receipt(
                    repo_root,
                    handoff_dir,
                    expected_prepared_context_sha256=expected_context_digest,
                    expected_publication_owner_token=publication_owner_token,
                )
        materialization_summary = _materialization_summary_from_receipt(
            materialization_summary,
            receipt=handoff_receipt,
            reporting_error=materialize_reporting_error,
        )
        handoff_committed = True
        terminal["scope_materialization"] = materialization_summary

        terminal.update(
            {
                "status": "completed",
                "stopped_after": "scope-materialization",
                "return_code": 0,
                "duration_ms": (time.perf_counter_ns() - started) // 1_000_000,
                "input_artifacts": artifact_inventory(
                    _unique_paths(
                        (
                            context,
                            *images,
                            *clarification_inputs,
                            *materialization_source_inputs,
                        )
                    )
                ),
                "output_artifacts": artifact_inventory((runtime_dir, handoff_dir)),
                "handoff_dir": str(handoff_dir),
            }
        )
        return emit(0, error=False)
    except Exception as exc:  # noqa: BLE001 - terminal orchestration boundary.
        if isinstance(
            exc, (_ModelLifecycleContractError, _ModelPhaseExecutionError)
        ):
            _record_model_summary(terminal, exc.summary)
            terminal[
                "scope_analysis"
                if exc.phase == "scope-analysis"
                else "semantic_design"
            ] = exc.summary
        if handoff_committed:
            add_reporting_error("post-commit-orchestration", exc)
            terminal.update(
                {
                    "status": "completed",
                    "stopped_after": "scope-materialization",
                    "return_code": 0,
                    "duration_ms": (
                        time.perf_counter_ns() - started
                    ) // 1_000_000,
                    **(
                        {"handoff_dir": str(handoff_dir)}
                        if handoff_dir is not None
                        else {}
                    ),
                }
            )
            return emit(0, error=False)
        reported_exc = (
            exc.original if isinstance(exc, _ModelPhaseExecutionError) else exc
        )
        terminal.update(
            {
                "status": "terminal-failed",
                "error_type": type(reported_exc).__name__,
                "error": str(reported_exc),
                "duration_ms": (time.perf_counter_ns() - started) // 1_000_000,
                "return_code": 2,
            }
        )
        return emit(2, error=True)


if __name__ == "__main__":
    raise SystemExit(main())
