from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from test_case_agent.case_identity import CaseIdentityError
from test_case_agent.coverage_contract import (
    CoverageContractError,
    bind_accepted_source_contract,
)
from test_case_agent.coverage_graph import CoverageGraphError, build_coverage_graph
from test_case_agent.coverage_io import (
    CoverageIoError,
    DesignContextDocument,
    load_design_context,
    load_property_derivations,
    write_coverage_graph,
    write_design_context,
    write_property_derivations,
)
from test_case_agent.derivation_compiler import (
    DerivationCompilationError,
    compile_property_derivations,
    extract_semantic_compiler_projection,
)
from test_case_agent.immutable_iteration import (
    ImmutableIterationError,
    ImmutableIterationResult,
    StageBackend,
    run_immutable_iteration,
)
from test_case_agent.iteration_contract import IterationContractError
from test_case_agent.review_cycle.prepared_package import load_obligations
from test_case_agent.review_cycle.runtime import (
    StageRuntimeError,
    sha256_path,
    write_json_atomic,
)
from test_case_agent.reviewer_evidence import (
    ReviewerEvidenceError,
    prepare_reviewer_evidence_basis,
)
from test_case_agent.review_cycle.source_assertions import (
    EmbeddedSourceAssertionContract,
    SourceAssertionContractError,
    SourceAssertionManifest,
    parse_embedded_source_assertion_contract,
)
from test_case_agent.review_cycle.source_row_baseline import (
    SourceRowBaselineValidationError,
    write_source_row_baseline,
)
from test_case_agent.scope_compiler import (
    ScopeCompilationError,
    compile_scope_source,
    validate_manifest_scope_binding,
)
from test_case_agent.scope_registry import (
    ResolvedScopeRegistry,
    ScopeRegistryError,
    load_and_resolve_scope_registry,
)
from test_case_agent.test_design import (
    DesignContext,
    DesignError,
    validate_design_context_for_graph,
)


RUN_CONFIG_SCHEMA_VERSION = 2
SUPPORTED_RUN_CONFIG_SCHEMA_VERSIONS = frozenset({RUN_CONFIG_SCHEMA_VERSION})
_INTERNAL_RUN_CONFIG_SCHEMA_VERSIONS = frozenset({1, RUN_CONFIG_SCHEMA_VERSION})
RUN_SUMMARY_SCHEMA_VERSION = 1
RUN_MODE = "source-qualified-immutable"
_SCOPE_ID = re.compile(r"[a-z0-9][a-z0-9-]*")
_FT_SLUG = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
_RUN_CONFIG_FIELDS_V1 = {
    "schema_version",
    "registry",
    "ft_root",
    "scope",
    "source_evidence",
    "obligations",
    "derivations",
    "design_context",
}
_RUN_CONFIG_FIELDS_V2 = (
    _RUN_CONFIG_FIELDS_V1 - {"derivations", "design_context"}
)
_RUN_CONFIG_OPTIONAL_FIELDS = {
    "writer_mode",
    "mockup_label_aliases",
    "revision_findings",
    "revision_input",
}
_WRITER_MODES = {"deterministic-first", "model-runtime-prose"}
_DESIGN_CONTEXT_FIELDS_V1 = {
    "package_id",
    "scope_title",
    "base_preconditions",
    "subject_labels",
    "condition_preconditions",
    "priorities",
}
_ITERATION_STATUS_CATEGORIES = {
    "accepted-shadow": "success",
    "accepted-with-calibration-pending": "success",
    "blocked-contract": "contract",
    "blocked-input-drift": "contract",
    "blocked-design": "workflow",
    "blocked-writer-unresolved": "workflow",
    "blocked-suite-gate": "workflow",
    "blocked-reviewer-context-too-large": "workflow",
    "review-changes-required": "workflow",
    "review-blocked": "workflow",
    "failed-infrastructure": "infrastructure",
}
_SUCCESSFUL_ITERATION_STATUSES = frozenset(
    {"accepted-shadow", "accepted-with-calibration-pending"}
)


class SourceQualifiedRunError(ValueError):
    """A source-qualified run cannot safely enter or complete its next stage."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        stage: str = "run-config",
        output_dir: Path | None = None,
    ):
        self.code = code
        self.stage = stage
        self.output_dir = output_dir
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class SourceQualifiedRunConfig:
    schema_version: int
    registry: str
    ft_root: str
    scope: str
    source_evidence: str
    obligations: str
    derivations: str | None
    design_context: str | None
    ft_slug: str | None = None
    writer_mode: str = "deterministic-first"
    mockup_label_aliases: tuple[Mapping[str, str], ...] = ()
    revision_findings: Mapping[str, Any] | None = None
    revision_input: str | None = None


@dataclass(frozen=True)
class SourceQualifiedRunResult:
    status: str
    output_dir: Path
    summary_path: Path
    iteration: ImmutableIterationResult


_PIPELINE_CONTRACT_ERRORS = (
    SourceQualifiedRunError,
    CaseIdentityError,
    CoverageContractError,
    CoverageGraphError,
    CoverageIoError,
    ImmutableIterationError,
    IterationContractError,
    ScopeCompilationError,
    ScopeRegistryError,
    SourceAssertionContractError,
    SourceRowBaselineValidationError,
    StageRuntimeError,
    DesignError,
    DerivationCompilationError,
    ReviewerEvidenceError,
)


def _fail(code: str, message: str, *, stage: str = "run-config") -> None:
    raise SourceQualifiedRunError(code, message, stage=stage)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("duplicate-json-key", f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _json_object(path: Path, *, label: str) -> Mapping[str, Any]:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
        )
    except SourceQualifiedRunError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        _fail("invalid-json", f"cannot read {label} {path}: {exc}")
    if not isinstance(payload, Mapping):
        _fail("invalid-json-object", f"{label} must be a JSON object")
    return payload


def _json_object_bytes(raw: bytes, *, label: str) -> Mapping[str, Any]:
    try:
        text = raw.decode("utf-8")
        payload = json.loads(text, object_pairs_hook=_unique_object)
    except SourceQualifiedRunError:
        raise
    except (UnicodeError, json.JSONDecodeError) as exc:
        _fail("invalid-json", f"cannot decode {label}: {exc}")
    if not isinstance(payload, Mapping):
        _fail("invalid-json-object", f"{label} must be a JSON object")
    return payload


def _utf8_text(path: Path, *, label: str, stage: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeError as exc:
        _fail(
            "invalid-utf8",
            f"{label} is not valid UTF-8: {path}: {exc}",
            stage=stage,
        )


def _text(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or "\n" in value
        or "\r" in value
    ):
        _fail("invalid-text", f"{label} must be non-empty trimmed single-line text")
    return value


def _relative_path(value: Any, label: str) -> str:
    text = _text(value, label)
    if "\\" in text or text.startswith("/") or re.match(r"^[A-Za-z]:", text):
        _fail("invalid-path", f"{label} must be a repo-relative POSIX path")
    path = PurePosixPath(text)
    if path.as_posix() != text or any(part in {"", ".", ".."} for part in path.parts):
        _fail("invalid-path", f"{label} must be normalized without traversal")
    return text


def _writer_mode(value: Any) -> str:
    text = _text(value, "writer_mode")
    if text not in _WRITER_MODES:
        _fail(
            "invalid-writer-mode",
            "writer_mode must be one of " + ", ".join(sorted(_WRITER_MODES)),
        )
    return text


def _mockup_label_aliases(value: Any) -> tuple[Mapping[str, str], ...]:
    if not isinstance(value, list):
        _fail("invalid-mockup-label-aliases", "mockup_label_aliases must be an array")
    aliases: list[Mapping[str, str]] = []
    for index, raw in enumerate(value):
        if not isinstance(raw, Mapping):
            _fail(
                "invalid-mockup-label-aliases",
                f"mockup_label_aliases[{index}] must be an object",
            )
        if set(raw) != {"canonical_ft_name", "label_from_mockup"}:
            _fail(
                "invalid-mockup-label-aliases",
                f"mockup_label_aliases[{index}] fields differ",
            )
        aliases.append(
            {
                "canonical_ft_name": _text(
                    raw["canonical_ft_name"],
                    f"mockup_label_aliases[{index}].canonical_ft_name",
                ),
                "label_from_mockup": _text(
                    raw["label_from_mockup"],
                    f"mockup_label_aliases[{index}].label_from_mockup",
                ),
            }
        )
    return tuple(aliases)


def _revision_findings(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail("invalid-revision-findings", "revision_findings must be an object")
    return dict(value)


def _source_qualified_run_config_from_bytes(
    raw: bytes, *, allow_legacy_v1: bool = False
) -> SourceQualifiedRunConfig:
    payload = _json_object_bytes(raw, label="source-qualified run config")
    version = payload.get("schema_version")
    supported = (
        _INTERNAL_RUN_CONFIG_SCHEMA_VERSIONS
        if allow_legacy_v1
        else SUPPORTED_RUN_CONFIG_SCHEMA_VERSIONS
    )
    if type(version) is not int or version not in supported:
        _fail(
            "run-config-version",
            "schema_version must be one of "
            + ", ".join(map(str, sorted(supported))),
        )
    expected_fields = (
        _RUN_CONFIG_FIELDS_V1 if version == 1 else _RUN_CONFIG_FIELDS_V2
    )
    allowed_fields = expected_fields | _RUN_CONFIG_OPTIONAL_FIELDS
    if not expected_fields.issubset(payload) or set(payload) - allowed_fields:
        _fail(
            "run-config-fields",
            "run config fields differ: "
            f"missing={sorted(expected_fields - set(payload)) or 'none'}, "
            f"unknown={sorted(set(payload) - allowed_fields) or 'none'}",
        )
    scope = _text(payload["scope"], "scope")
    if _SCOPE_ID.fullmatch(scope) is None:
        _fail("invalid-scope", "scope must be a lowercase slug")
    return SourceQualifiedRunConfig(
        schema_version=version,
        registry=_relative_path(payload["registry"], "registry"),
        ft_root=_relative_path(payload["ft_root"], "ft_root"),
        scope=scope,
        source_evidence=_relative_path(payload["source_evidence"], "source_evidence"),
        obligations=_relative_path(payload["obligations"], "obligations"),
        derivations=(
            _relative_path(payload["derivations"], "derivations")
            if version == 1
            else None
        ),
        design_context=(
            _relative_path(payload["design_context"], "design_context")
            if version == 1
            else None
        ),
        ft_slug=None,
        writer_mode=(
            _writer_mode(payload["writer_mode"])
            if "writer_mode" in payload
            else "deterministic-first"
        ),
        mockup_label_aliases=(
            _mockup_label_aliases(payload["mockup_label_aliases"])
            if "mockup_label_aliases" in payload
            else ()
        ),
        revision_findings=(
            _revision_findings(payload["revision_findings"])
            if "revision_findings" in payload
            else None
        ),
        revision_input=(
            _relative_path(payload["revision_input"], "revision_input")
            if "revision_input" in payload
            else None
        ),
    )


def load_source_qualified_run_config(path: Path) -> SourceQualifiedRunConfig:
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        _fail("invalid-json", f"cannot read source-qualified run config {path}: {exc}")
    return _source_qualified_run_config_from_bytes(raw)


def classify_source_qualified_status(status: str) -> str:
    """Map every known immutable terminal state to one recovery category."""

    return _ITERATION_STATUS_CATEGORIES.get(status, "internal")


def _inside(path: Path, root: Path, label: str) -> Path:
    candidate = path if path.is_absolute() else root / path
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise SourceQualifiedRunError(
            "unsafe-path", f"{label} is outside {root}: {resolved}"
        ) from exc
    return resolved


def _repo_path(relative: str, repo_root: Path, label: str) -> Path:
    path = _inside(repo_root.joinpath(*PurePosixPath(relative).parts), repo_root, label)
    if not path.is_file():
        _fail("missing-input", f"{label} is missing or not a file: {path}")
    return path


def _relative(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _manifest_registered_paths(manifest: SourceAssertionManifest) -> tuple[str, ...]:
    paths = [item.path for item in manifest.sources]
    paths.extend(item.path for item in manifest.evidence_sources)
    paths.extend(item.path for item in manifest.mockups)
    paths.extend(item.evidence_source_path for item in manifest.clarifications)
    paths.append(manifest.coverage_gaps_artifact.path)
    return tuple(sorted(set(paths)))


def _canonical_baseline(ft_root: Path, repo_root: Path) -> tuple[str, ...]:
    test_cases = ft_root / "test-cases"
    files = sorted(test_cases.rglob("*.md")) if test_cases.is_dir() else []
    return tuple(
        _relative(_inside(path, test_cases, "canonical baseline"), repo_root)
        for path in files
    )


def _canonical_snapshot(
    ft_root: Path, repo_root: Path
) -> tuple[dict[str, Any], ...]:
    """Capture canonical path, size and hash before any compilation work."""

    test_cases = ft_root / "test-cases"
    files = sorted(test_cases.rglob("*.md")) if test_cases.is_dir() else []
    result: list[dict[str, Any]] = []
    for candidate in files:
        path = _inside(candidate, test_cases, "canonical baseline")
        try:
            raw = path.read_bytes()
        except OSError as exc:
            _fail(
                "canonical-baseline-read",
                f"cannot snapshot canonical test case {path}: {exc}",
                stage="input-resolution",
            )
        result.append(
            {
                "role": "canonical",
                "path": _relative(path, repo_root),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "size_bytes": len(raw),
            }
        )
    return tuple(result)


def _verify_canonical_snapshot(
    snapshot: Sequence[Mapping[str, Any]],
    *,
    ft_root: Path,
    repo_root: Path,
    stage: str,
) -> None:
    expected_paths = tuple(str(item["path"]) for item in snapshot)
    actual_paths = _canonical_baseline(ft_root, repo_root)
    if actual_paths != expected_paths:
        _fail(
            "canonical-baseline-drift",
            "the full production test-case path set changed during execution",
            stage=stage,
        )
    _verify_input_bindings(snapshot, repo_root, stage=stage)


def _design_context_v1(payload: Mapping[str, Any]) -> DesignContext:
    if set(payload) != _DESIGN_CONTEXT_FIELDS_V1:
        _fail(
            "design-context-fields",
            "design context fields differ: "
            f"missing={sorted(_DESIGN_CONTEXT_FIELDS_V1 - set(payload)) or 'none'}, "
            f"unknown={sorted(set(payload) - _DESIGN_CONTEXT_FIELDS_V1) or 'none'}",
            stage="design-context",
        )
    base = payload["base_preconditions"]
    if not isinstance(base, list) or any(not isinstance(item, str) for item in base):
        _fail(
            "invalid-design-context",
            "base_preconditions must be a string array",
            stage="design-context",
        )
    mappings: dict[str, dict[str, str]] = {}
    for name in ("subject_labels", "condition_preconditions", "priorities"):
        value = payload[name]
        if not isinstance(value, Mapping) or any(
            not isinstance(key, str) or not isinstance(item, str)
            for key, item in value.items()
        ):
            _fail(
                "invalid-design-context",
                f"{name} must be a string-to-string object",
                stage="design-context",
            )
        mappings[name] = dict(value)
    context = DesignContext(
        package_id=_text(payload["package_id"], "design_context.package_id"),
        scope_title=_text(payload["scope_title"], "design_context.scope_title"),
        base_preconditions=tuple(base),
        subject_labels=mappings["subject_labels"],
        condition_preconditions=mappings["condition_preconditions"],
        priorities=mappings["priorities"] or None,
    )
    context.validate()
    return context


def _design_context_v2(
    *,
    package_id: str,
    subject_labels: Mapping[str, str],
    condition_preconditions: Mapping[str, str],
    scope_title: str,
    base_preconditions: Sequence[str],
) -> DesignContext:
    """Build production context only from the accepted compiler projection."""

    context = DesignContext(
        package_id=package_id,
        scope_title=scope_title,
        base_preconditions=tuple(base_preconditions),
        subject_labels=dict(subject_labels),
        condition_preconditions=dict(condition_preconditions),
        priorities=None,
    )
    context.validate()
    return context


def _binding(path: Path, repo_root: Path, *, role: str) -> dict[str, Any]:
    return {
        "role": role,
        "path": _relative(path, repo_root),
        "sha256": sha256_path(path),
        "size_bytes": path.stat().st_size,
    }


def _input_bindings(
    inputs: Sequence[tuple[str, Path]], repo_root: Path
) -> tuple[dict[str, Any], ...]:
    return tuple(_binding(path, repo_root, role=role) for role, path in inputs)


def _verify_input_bindings(
    bindings: Sequence[Mapping[str, Any]],
    repo_root: Path,
    *,
    stage: str,
) -> None:
    for item in bindings:
        path = _repo_path(str(item["path"]), repo_root, str(item["role"]))
        if (
            sha256_path(path) != item["sha256"]
            or path.stat().st_size != item["size_bytes"]
        ):
            _fail(
                "run-input-drift",
                f"material run input changed during execution: {item['path']}",
                stage=stage,
            )


def _write_terminal_failure(
    *,
    repo_root: Path,
    output_dir: Path,
    status: str,
    stage: str,
    category: str,
    error_type: str,
    message: str,
    started_ns: int,
    stage_timings_ms: Mapping[str, int],
    qualification_only: bool = False,
) -> None:
    diagnostic_path = output_dir / "diagnostic.json"
    write_json_atomic(
        diagnostic_path,
        {
            "schema_version": 1,
            "category": category,
            "failed_stage": stage,
            "error_type": error_type,
            "message": message,
        },
    )
    terminal = {
        "schema_version": RUN_SUMMARY_SCHEMA_VERSION,
        "mode": RUN_MODE,
        "status": status,
        "failed_stage": stage,
        "diagnostic": _relative(diagnostic_path, repo_root),
        "canonical_publication": "not-performed",
        "promotion": "out-of-scope",
        "stage_timings_ms": dict(stage_timings_ms),
        "total_duration_ms": (time.perf_counter_ns() - started_ns) // 1_000_000,
    }
    if qualification_only:
        terminal.update(
            {
                "qualification_only": True,
                "promotion_eligible": False,
                "non_promotable_reason": "fixture-test-hook",
            }
        )
    write_json_atomic(output_dir / "terminal-summary.json", terminal)


def _run_source_qualified_scope(
    *,
    repo_root: Path,
    config_path: Path,
    output_dir: Path,
    writer_response: Path | None = None,
    reviewer_response: Path | None = None,
    backend: StageBackend | None = None,
    allow_legacy_v1: bool = False,
    qualification_only: bool = False,
) -> SourceQualifiedRunResult:
    """Shared engine; precomputed responses are reserved for library tests."""

    started_ns = time.perf_counter_ns()
    repo_root = Path(repo_root).resolve()
    if not repo_root.is_dir():
        _fail("missing-repo-root", f"repo_root is missing: {repo_root}")
    config_path = _inside(Path(config_path), repo_root, "run config")
    if not config_path.is_file():
        _fail("missing-run-config", f"run config is missing: {config_path}")
    try:
        config_raw = config_path.read_bytes()
    except OSError as exc:
        _fail("invalid-json", f"cannot read source-qualified run config: {exc}")
    config = _source_qualified_run_config_from_bytes(
        config_raw, allow_legacy_v1=allow_legacy_v1
    )
    if config.revision_findings is not None and config.revision_input is not None:
        _fail(
            "ambiguous-revision-input",
            "run config must not define both revision_findings and revision_input",
        )
    config_binding = {
        "role": "run-config",
        "path": _relative(config_path, repo_root),
        "sha256": hashlib.sha256(config_raw).hexdigest(),
        "size_bytes": len(config_raw),
    }
    ft_root = _inside(
        repo_root.joinpath(*PurePosixPath(config.ft_root).parts),
        repo_root,
        "FT root",
    )
    if not ft_root.is_dir():
        _fail("missing-ft-root", f"FT root is missing: {ft_root}")
    derived_ft_slug = ft_root.name
    if _FT_SLUG.fullmatch(derived_ft_slug) is None:
        _fail(
            "invalid-ft-slug",
            "authenticated ft_root basename is not a stable FT identifier",
        )
    output_dir = _inside(Path(output_dir), repo_root, "run output")
    work_root = (ft_root / "work").resolve()
    try:
        output_dir.relative_to(work_root)
    except ValueError as exc:
        raise SourceQualifiedRunError(
            "unsafe-output",
            f"run output must be below {work_root}",
        ) from exc
    if output_dir == work_root or output_dir.exists():
        _fail("nonfresh-output", f"run output must be a fresh child path: {output_dir}")
    early_canonical_bindings = _canonical_snapshot(ft_root, repo_root)
    output_dir.mkdir(parents=True)

    stage = "input-resolution"
    stage_started_ns = time.perf_counter_ns()
    stage_timings_ms: dict[str, int] = {}

    def finish_stage() -> None:
        stage_timings_ms[stage] = (
            time.perf_counter_ns() - stage_started_ns
        ) // 1_000_000

    try:
        registry_path = _repo_path(config.registry, repo_root, "scope registry")
        source_evidence_path = _repo_path(
            config.source_evidence, repo_root, "source evidence"
        )
        obligations_path = _repo_path(config.obligations, repo_root, "obligations")
        derivations_path = (
            _repo_path(config.derivations, repo_root, "derivations")
            if config.derivations is not None
            else None
        )
        design_context_path = (
            _repo_path(config.design_context, repo_root, "design context")
            if config.design_context is not None
            else None
        )
        revision_input_path = (
            _repo_path(config.revision_input, repo_root, "revision input")
            if config.revision_input is not None
            else None
        )
        revision_input_payload = (
            _json_object(revision_input_path, label="revision input")
            if revision_input_path is not None
            else None
        )
        material_paths = [
            registry_path,
            source_evidence_path,
            obligations_path,
        ]
        if design_context_path is not None:
            material_paths.append(design_context_path)
        if derivations_path is not None:
            material_paths.append(derivations_path)
        for path in material_paths:
            _inside(path, ft_root, "FT run input")
        writer_path = (
            _inside(Path(writer_response), repo_root, "writer response")
            if writer_response is not None
            else None
        )
        reviewer_path = (
            _inside(Path(reviewer_response), repo_root, "reviewer response")
            if reviewer_response is not None
            else None
        )
        for label, path in (
            ("writer response", writer_path),
            ("reviewer response", reviewer_path),
        ):
            if path is not None and not path.is_file():
                _fail("missing-input", f"{label} is missing: {path}")
        input_paths: list[tuple[str, Path]] = [
            ("scope-registry", registry_path),
            ("source-evidence", source_evidence_path),
            ("obligations", obligations_path),
        ]
        if design_context_path is not None:
            input_paths.append(("design-context", design_context_path))
        if derivations_path is not None:
            input_paths.append(("derivations", derivations_path))
        if revision_input_path is not None:
            input_paths.append(("revision-input", revision_input_path))
        if writer_path is not None:
            input_paths.append(("precomputed-writer-response", writer_path))
        if reviewer_path is not None:
            input_paths.append(("precomputed-reviewer-response", reviewer_path))
        run_input_bindings = (
            config_binding,
            *_input_bindings(input_paths, repo_root),
        )
        finish_stage()

        stage = "scope-compilation"
        stage_started_ns = time.perf_counter_ns()
        registry: ResolvedScopeRegistry = load_and_resolve_scope_registry(
            registry_path,
            ft_root,
            scope_id=config.scope,
        )
        compiled = compile_scope_source(
            registry,
            scope_id=config.scope,
            repo_root=repo_root,
        )
        compilation_dir = output_dir / "scope-compilation"
        compilation_dir.mkdir()
        write_json_atomic(
            compilation_dir / "source-row-extraction-spec.json",
            compiled.extraction_spec.to_dict(),
        )
        write_source_row_baseline(
            compilation_dir / "source-row-baseline.json",
            compiled.baseline,
        )
        write_json_atomic(
            compilation_dir / "compiled-scope.json",
            compiled.to_dict(),
        )
        finish_stage()

        stage = "source-contract-binding"
        stage_started_ns = time.perf_counter_ns()
        evidence_text = _utf8_text(
            source_evidence_path,
            label="source evidence",
            stage=stage,
        )
        obligations = load_obligations(
            obligations_path,
            evidence_text=evidence_text,
        )
        expected_obligation_ids = tuple(
            item.obligation_id
            for item in obligations.obligations
            if item.coverage_status == "testable"
        )
        contract = parse_embedded_source_assertion_contract(
            evidence_text,
            repo_root,
            expected_scope_slug=config.scope,
            expected_obligation_ids=expected_obligation_ids,
        )
        if not isinstance(contract, EmbeddedSourceAssertionContract):
            _fail(
                "missing-accepted-source-contract",
                "source evidence has no accepted current source-assertion contract",
                stage=stage,
            )
        validate_manifest_scope_binding(
            contract.manifest,
            compiled=compiled,
            repo_root=repo_root,
            package_root=ft_root,
        )
        bindings_dir = output_dir / "bindings"
        bindings_dir.mkdir()
        generated_derivation_path: Path | None = None
        derived_semantic_artifact_paths: tuple[str, ...] = ()
        derived_semantic_snapshots: tuple[tuple[Path, str, int], ...] = ()
        generated_subject_labels: Mapping[str, str] = {}
        generated_condition_preconditions: Mapping[str, str] = {}
        generated_scope_title = ""
        generated_base_preconditions: tuple[str, ...] = ()
        if derivations_path is not None:
            derivations = load_property_derivations(
                derivations_path,
                expected_obligation_set_digest=obligations.digest,
            )
        else:
            compiled_derivations = compile_property_derivations(
                repo_root=repo_root,
                ft_slug=derived_ft_slug,
                source_manifest=contract.manifest,
                obligation_set=obligations,
                semantic_projection=extract_semantic_compiler_projection(
                    evidence_text
                ),
            )
            generated_derivation_path = (
                bindings_dir / "generated-property-derivations.json"
            )
            write_property_derivations(
                generated_derivation_path,
                compiled_derivations.document,
            )
            derivations = load_property_derivations(
                generated_derivation_path,
                expected_source_manifest_digest=contract.manifest.digest,
                expected_obligation_set_digest=obligations.digest,
            )
            derived_semantic_artifact_paths = tuple(
                _relative(path, repo_root)
                for path in compiled_derivations.registered_artifacts
            )
            derived_semantic_snapshots = (
                compiled_derivations.registered_artifact_snapshots
            )
            generated_subject_labels = compiled_derivations.subject_labels
            generated_condition_preconditions = (
                compiled_derivations.condition_preconditions
            )
            generated_scope_title = compiled_derivations.scope_title
            generated_base_preconditions = (
                compiled_derivations.base_preconditions
            )
        derived_sources = _manifest_registered_paths(contract.manifest)
        derived_canonical_bindings = early_canonical_bindings
        derived_canonical = tuple(
            str(item["path"]) for item in derived_canonical_bindings
        )
        derived_source_bindings = _input_bindings(
            tuple(
                (
                    "accepted-source",
                    _repo_path(path, repo_root, "derived protected source"),
                )
                for path in derived_sources
            ),
            repo_root,
        )
        derived_semantic_bindings = tuple(
            {
                "role": "semantic-derivation-source",
                "path": _relative(path, repo_root),
                "sha256": expected_hash,
                "size_bytes": expected_size,
            }
            for path, expected_hash, expected_size in derived_semantic_snapshots
        )
        if derivations.scope_slug != config.scope:
            _fail(
                "derivation-scope-mismatch",
                "derivation document scope differs from the selected registry scope",
                stage=stage,
            )
        binding = bind_accepted_source_contract(
            contract=contract,
            obligation_set=obligations,
            expected_scope_slug=config.scope,
            expected_manifest_digest=derivations.source_manifest_digest,
            expected_package_id=obligations.package_id,
            expected_obligation_set_digest=derivations.obligation_set_digest,
            repo_root=repo_root,
        )
        reviewer_evidence_basis = prepare_reviewer_evidence_basis(
            repo_root,
            compiled,
            contract.manifest,
            contract.review_receipt,
            obligations,
        )
        write_json_atomic(
            bindings_dir / "accepted-coverage-contract.json",
            binding.to_dict(),
        )
        write_json_atomic(
            output_dir / "run-input-receipt.json",
            {
                "schema_version": 1,
                "inputs": list(run_input_bindings),
                "derived_protected_source_paths": list(derived_sources),
                "derived_protected_canonical_paths": list(derived_canonical),
                "derived_protected_source_bindings": list(
                    derived_source_bindings
                ),
                "derived_protected_canonical_bindings": list(
                    derived_canonical_bindings
                ),
                "derived_semantic_artifact_paths": list(
                    derived_semantic_artifact_paths
                ),
                "derived_semantic_artifact_bindings": list(
                    derived_semantic_bindings
                ),
                "registry_digest": registry.digest,
                "extraction_spec_digest": compiled.extraction_spec.digest,
                "source_row_baseline_digest": compiled.baseline.digest,
                "accepted_coverage_binding_digest": binding.digest,
                "derivation_document_digest": derivations.digest,
                "derivation_mode": (
                    "generated-from-semantic-projection"
                    if generated_derivation_path is not None
                    else "legacy-explicit-input"
                ),
                "generated_derivation_path": (
                    _relative(generated_derivation_path, repo_root)
                    if generated_derivation_path is not None
                    else None
                ),
            },
        )
        finish_stage()

        stage = "coverage-graph"
        stage_started_ns = time.perf_counter_ns()
        graph = build_coverage_graph(
            ft_slug=derivations.ft_slug,
            tc_prefix=compiled.definition.tc_prefix,
            source_manifest=contract.manifest,
            obligation_set=obligations,
            derivations=derivations.derivations,
        )
        graph_dir = output_dir / "graph"
        graph_dir.mkdir()
        graph_path = graph_dir / "coverage-graph.json"
        write_coverage_graph(graph_path, graph)
        finish_stage()

        stage = "design-context"
        stage_started_ns = time.perf_counter_ns()
        if config.schema_version == 1:
            assert design_context_path is not None
            context = _design_context_v1(
                _json_object(design_context_path, label="design context")
            )
        else:
            context = _design_context_v2(
                package_id=binding.package_id,
                subject_labels=generated_subject_labels,
                condition_preconditions=generated_condition_preconditions,
                scope_title=generated_scope_title,
                base_preconditions=generated_base_preconditions,
            )
        validate_design_context_for_graph(
            graph,
            context,
            expected_package_id=binding.package_id,
        )
        context_document = DesignContextDocument(
            schema_version=1,
            ft_slug=graph.ft_slug,
            scope_slug=graph.scope_slug,
            coverage_graph_digest=graph.digest,
            context=context,
        )
        context_dir = output_dir / "context"
        context_dir.mkdir()
        bound_context_path = context_dir / "design-context.json"
        write_design_context(bound_context_path, context_document, graph=graph)
        bound_context = load_design_context(bound_context_path, graph=graph)
        finish_stage()

        stage = "pre-dispatch-verification"
        stage_started_ns = time.perf_counter_ns()
        _verify_input_bindings(run_input_bindings, repo_root, stage=stage)
        _verify_input_bindings(derived_source_bindings, repo_root, stage=stage)
        _verify_canonical_snapshot(
            derived_canonical_bindings,
            ft_root=ft_root,
            repo_root=repo_root,
            stage=stage,
        )
        _verify_input_bindings(derived_semantic_bindings, repo_root, stage=stage)
        finish_stage()

        stage = "immutable-iteration"
        stage_started_ns = time.perf_counter_ns()
        protected_sources = tuple(
            dict.fromkeys(
                _repo_path(path, repo_root, "derived protected source")
                for path in (*derived_sources, *derived_semantic_artifact_paths)
            )
        )
        protected_canonical = tuple(
            _repo_path(path, repo_root, "derived protected canonical")
            for path in derived_canonical
        )
        iteration = run_immutable_iteration(
            repo_root=repo_root,
            graph=graph,
            context=bound_context.context,
            output_dir=output_dir / "iteration",
            protected_source_paths=protected_sources,
            protected_canonical_paths=protected_canonical,
            writer_response=writer_path,
            reviewer_response=reviewer_path,
            backend=backend,
            reviewer_evidence_basis=reviewer_evidence_basis,
            writer_mode=config.writer_mode,
            mockup_label_aliases=config.mockup_label_aliases,
            revision_findings=config.revision_findings,
            revision_input=revision_input_payload,
        )
        finish_stage()

        stage = "final-reconciliation"
        stage_started_ns = time.perf_counter_ns()
        _verify_input_bindings(run_input_bindings, repo_root, stage=stage)
        if iteration.status != "blocked-input-drift":
            _verify_input_bindings(derived_source_bindings, repo_root, stage=stage)
            _verify_input_bindings(
                derived_semantic_bindings,
                repo_root,
                stage=stage,
            )
            _verify_canonical_snapshot(
                derived_canonical_bindings,
                ft_root=ft_root,
                repo_root=repo_root,
                stage=stage,
            )
        iteration_summary = json.loads(
            iteration.summary_path.read_text(encoding="utf-8")
        )
        if qualification_only:
            iteration_summary["qualification_only"] = True
            iteration_summary.setdefault("promotion_eligible", False)
            iteration_summary.setdefault(
                "non_promotable_reason", "fixture-test-hook"
            )
            write_json_atomic(iteration.summary_path, iteration_summary)
        diagnostic_relative: str | None = None
        if iteration.status not in _SUCCESSFUL_ITERATION_STATUSES:
            diagnostic_path = output_dir / "diagnostic.json"
            write_json_atomic(
                diagnostic_path,
                {
                    "schema_version": 1,
                    "category": classify_source_qualified_status(
                        iteration.status
                    ),
                    "failed_stage": "immutable-iteration",
                    "error_type": "ImmutableIterationTerminalStatus",
                    "message": iteration_summary.get("error") or iteration.status,
                    "iteration_status": iteration.status,
                    "iteration_summary": _relative(
                        iteration.summary_path,
                        repo_root,
                    ),
                },
            )
            diagnostic_relative = _relative(diagnostic_path, repo_root)
        summary = {
            "schema_version": RUN_SUMMARY_SCHEMA_VERSION,
            "mode": RUN_MODE,
            "status": iteration.status,
            "ft_root": _relative(ft_root, repo_root),
            "scope": config.scope,
            "writer_mode": config.writer_mode,
            "mockup_label_alias_count": len(config.mockup_label_aliases),
            "revision_findings_supplied": config.revision_findings is not None,
            "revision_input_supplied": config.revision_input is not None,
            "registry_digest": registry.digest,
            "source_manifest_digest": contract.manifest.digest,
            "source_review_receipt_digest": binding.source_review_receipt_digest,
            "obligation_set_digest": obligations.digest,
            "derivation_document_digest": derivations.digest,
            "derivation_mode": (
                "generated-from-semantic-projection"
                if generated_derivation_path is not None
                else "legacy-explicit-input"
            ),
            "coverage_graph_digest": graph.digest,
            "accepted_coverage_binding_digest": binding.digest,
            "test_case_count": iteration.test_case_count,
            "writer_model_calls": iteration.writer_model_calls,
            "reviewer_model_calls": iteration.reviewer_model_calls,
            "calibration_pending_count": iteration_summary.get(
                "calibration_pending_count", 0
            ),
            "iteration_summary": _relative(iteration.summary_path, repo_root),
            "draft": iteration_summary.get("draft"),
            "protected_source_paths": list(derived_sources),
            "protected_semantic_artifact_paths": list(
                derived_semantic_artifact_paths
            ),
            "protected_canonical_paths": list(derived_canonical),
            "canonical_publication": "not-performed",
            "promotion": "out-of-scope",
            "diagnostic": diagnostic_relative,
            "stage_timings_ms": stage_timings_ms,
            "total_duration_ms": 0,
        }
        for name in ("promotion_eligible", "non_promotable_reason"):
            if name in iteration_summary:
                summary[name] = iteration_summary[name]
        if qualification_only:
            summary["qualification_only"] = True
            summary.setdefault("promotion_eligible", False)
            summary.setdefault("non_promotable_reason", "fixture-test-hook")
        finish_stage()
        summary["stage_timings_ms"] = stage_timings_ms
        summary["total_duration_ms"] = (
            time.perf_counter_ns() - started_ns
        ) // 1_000_000
        summary_path = output_dir / "terminal-summary.json"
        write_json_atomic(summary_path, summary)
        return SourceQualifiedRunResult(
            status=iteration.status,
            output_dir=output_dir,
            summary_path=summary_path,
            iteration=iteration,
        )
    except _PIPELINE_CONTRACT_ERRORS as exc:
        finish_stage()
        message = str(exc)
        failure_stage = (
            exc.stage
            if isinstance(exc, SourceQualifiedRunError)
            and exc.stage != "run-config"
            else stage
        )
        _write_terminal_failure(
            repo_root=repo_root,
            output_dir=output_dir,
            status="blocked-contract",
            stage=failure_stage,
            category="contract",
            error_type=type(exc).__name__,
            message=message,
            started_ns=started_ns,
            stage_timings_ms=stage_timings_ms,
            qualification_only=qualification_only,
        )
        raise SourceQualifiedRunError(
            "pipeline-blocked",
            message,
            stage=failure_stage,
            output_dir=output_dir,
        ) from exc
    except OSError as exc:
        finish_stage()
        _write_terminal_failure(
            repo_root=repo_root,
            output_dir=output_dir,
            status="failed-infrastructure",
            stage=stage,
            category="infrastructure",
            error_type=type(exc).__name__,
            message=str(exc),
            started_ns=started_ns,
            stage_timings_ms=stage_timings_ms,
            qualification_only=qualification_only,
        )
        raise
    except Exception as exc:
        finish_stage()
        _write_terminal_failure(
            repo_root=repo_root,
            output_dir=output_dir,
            status="failed-internal",
            stage=stage,
            category="internal",
            error_type=type(exc).__name__,
            message="unexpected internal failure; inspect developer logs",
            started_ns=started_ns,
            stage_timings_ms=stage_timings_ms,
            qualification_only=qualification_only,
        )
        raise


def run_source_qualified_scope(
    *,
    repo_root: Path,
    config_path: Path,
    output_dir: Path,
) -> SourceQualifiedRunResult:
    """Run production admission with the built-in Codex backend only."""

    return _run_source_qualified_scope(
        repo_root=repo_root,
        config_path=config_path,
        output_dir=output_dir,
    )


def run_source_qualified_scope_with_fixture_responses(
    *,
    repo_root: Path,
    config_path: Path,
    output_dir: Path,
    writer_response: Path | None = None,
    reviewer_response: Path | None = None,
    backend: StageBackend | None = None,
) -> SourceQualifiedRunResult:
    """Offline library test hook; its zero-call result is never promotable."""

    return _run_source_qualified_scope(
        repo_root=repo_root,
        config_path=config_path,
        output_dir=output_dir,
        writer_response=writer_response,
        reviewer_response=reviewer_response,
        backend=backend,
        allow_legacy_v1=True,
        qualification_only=True,
    )


__all__ = [
    "RUN_CONFIG_SCHEMA_VERSION",
    "RUN_MODE",
    "SourceQualifiedRunConfig",
    "SourceQualifiedRunError",
    "SourceQualifiedRunResult",
    "classify_source_qualified_status",
    "load_source_qualified_run_config",
    "run_source_qualified_scope",
]
