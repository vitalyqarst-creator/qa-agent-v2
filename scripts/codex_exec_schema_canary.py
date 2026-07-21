from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.codex_exec_source_assertion_reviewer import receipt_schema, run_exec  # noqa: E402
from scripts.openai_strict_output_schema import (  # noqa: E402
    openai_strict_output_schema_shape_sha256,
    validate_openai_strict_output_instance,
    validate_openai_strict_output_schema,
)
from test_case_agent.review_cycle.exec_backend import (  # noqa: E402
    MODEL_TOOL_ISOLATION_DISABLE_FEATURES,
    probe_exec_capability,
    resolve_exec_command,
    resolve_verified_exec_capability,
)
from test_case_agent.review_cycle.exec_events import (  # noqa: E402
    TOOL_EVENT_ITEM_TYPES,
)
from test_case_agent.review_cycle.schema_canary_contract import (  # noqa: E402
    SCHEMA_CANARY_SUMMARY_VERSION,
    validate_schema_canary_summary,
)
from test_case_agent.review_cycle.source_assertions import (  # noqa: E402
    SourceAssertionContractError,
    SourceAssertionReviewReceipt,
    load_source_assertion_manifest,
)


# Backward-compatible public alias for handoff-local consumers.  The value is
# canonical only in schema_canary_contract.py.
CANARY_VERSION = SCHEMA_CANARY_SUMMARY_VERSION
CANARY_RUNTIME_PROFILE = "codex-exec-deterministic-exact-echo-pinned-v3"
KNOWN_SCHEMA_KEYWORDS = frozenset(
    {
        "$schema",
        "additionalProperties",
        "allOf",
        "anyOf",
        "const",
        "dependentRequired",
        "dependentSchemas",
        "else",
        "enum",
        "format",
        "if",
        "items",
        "maxItems",
        "maxLength",
        "minItems",
        "minLength",
        "not",
        "pattern",
        "properties",
        "required",
        "then",
        "type",
        "uniqueItems",
    }
)


class SchemaCanaryError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_under(root: Path, value: Path, *, label: str) -> Path:
    candidate = value.resolve() if value.is_absolute() else (root / value).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise SchemaCanaryError(f"{label} must resolve under repo root: {candidate}") from exc
    return candidate


def schema_keyword_inventory(value: Any) -> dict[str, int]:
    counts: dict[str, int] = {}

    def visit(item: Any) -> None:
        if isinstance(item, Mapping):
            for key, nested in item.items():
                if key in KNOWN_SCHEMA_KEYWORDS:
                    counts[key] = counts.get(key, 0) + 1
                visit(nested)
        elif isinstance(item, list):
            for nested in item:
                visit(nested)

    visit(value)
    return dict(sorted(counts.items()))


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def deterministic_transport_instance(schema: Mapping[str, Any]) -> Any:
    """Build the smallest deterministic instance needed for a transport-only canary."""

    enum = schema.get("enum")
    if isinstance(enum, list) and enum:
        return enum[0]
    if "const" in schema:
        return schema["const"]
    for combinator in ("oneOf", "anyOf"):
        options = schema.get(combinator)
        if isinstance(options, list) and options and isinstance(options[0], Mapping):
            return deterministic_transport_instance(options[0])

    schema_type = schema.get("type")
    if schema_type == "object":
        properties = schema.get("properties")
        required = schema.get("required")
        if not isinstance(properties, Mapping) or not isinstance(required, list):
            raise SchemaCanaryError("transport fixture requires strict object properties")
        result: dict[str, Any] = {}
        for name in required:
            property_schema = properties.get(name)
            if not isinstance(name, str) or not isinstance(property_schema, Mapping):
                raise SchemaCanaryError(
                    f"transport fixture cannot resolve required property: {name!r}"
                )
            result[name] = deterministic_transport_instance(property_schema)
        return result
    if schema_type == "array":
        item_schema = schema.get("items")
        if not isinstance(item_schema, Mapping):
            raise SchemaCanaryError("transport fixture requires one object items schema")
        minimum = schema.get("minItems", 0)
        maximum = schema.get("maxItems")
        if type(minimum) is not int or minimum < 0:
            raise SchemaCanaryError("transport fixture minItems must be a non-negative integer")
        if maximum is not None and (type(maximum) is not int or maximum < minimum):
            raise SchemaCanaryError("transport fixture maxItems is inconsistent")
        return [deterministic_transport_instance(item_schema) for _ in range(minimum)]
    if schema_type == "string":
        pattern = schema.get("pattern")
        if pattern == "^[0-9a-f]{64}$":
            return "0" * 64
        if pattern is not None:
            raise SchemaCanaryError(
                f"transport fixture does not support string pattern: {pattern}"
            )
        minimum = schema.get("minLength", 0)
        if type(minimum) is not int or minimum < 0:
            raise SchemaCanaryError("transport fixture minLength must be non-negative")
        return "transport-canary" if minimum <= len("transport-canary") else "x" * minimum
    if schema_type == "integer":
        return 0
    if schema_type == "number":
        return 0.0
    if schema_type == "boolean":
        return False
    if schema_type == "null":
        return None
    raise SchemaCanaryError(f"transport fixture does not support schema type: {schema_type!r}")


def transport_prompt(instance: Mapping[str, Any]) -> str:
    expected = canonical_json_bytes(instance).decode("utf-8")
    return (
        "Schema transport canary only. Do not call tools. This is not a source "
        "review and contains no source evidence. Return exactly the JSON object "
        "between BEGIN_EXPECTED_JSON and END_EXPECTED_JSON. Preserve every value; "
        "do not add commentary or Markdown.\n"
        "BEGIN_EXPECTED_JSON\n"
        f"{expected}\n"
        "END_EXPECTED_JSON\n"
    )


def semantic_receipt_is_rejected(instance: Mapping[str, Any], manifest: Any) -> bool:
    try:
        receipt = SourceAssertionReviewReceipt.from_dict(instance)
        receipt.validate(manifest)
    except (SourceAssertionContractError, TypeError, ValueError):
        return True
    return False


def optional_sha256(path: Path) -> str | None:
    return sha256_file(path) if path.is_file() else None


def optional_canonical_json_sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return sha256_bytes(canonical_json_bytes(value))


def event_type_sequence(path: Path) -> list[str]:
    if not path.is_file():
        return []
    event_types: list[str] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SchemaCanaryError(
                f"invalid canary event JSON at line {line_number}: {exc}"
            ) from exc
        event_type = event.get("type") if isinstance(event, Mapping) else None
        if not isinstance(event_type, str) or not event_type:
            raise SchemaCanaryError(
                f"canary event at line {line_number} has no string type"
            )
        event_types.append(event_type)
    return event_types


def event_type_counts(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event_type in event_type_sequence(path):
        counts[event_type] = counts.get(event_type, 0) + 1
    return dict(sorted(counts.items()))


def write_json_exclusive(path: Path, payload: Mapping[str, Any]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def codex_version(command: str) -> str:
    completed = subprocess.run(
        [command, "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        check=False,
    )
    if completed.returncode != 0:
        raise SchemaCanaryError(
            "cannot identify codex runtime: "
            + (completed.stderr or completed.stdout).strip()[-1000:]
        )
    version = completed.stdout.strip()
    if not version:
        raise SchemaCanaryError("codex --version returned no version text")
    return version


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run one non-semantic codex exec transport canary for the exact generated "
            "source-review output schema."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--qualification-id", required=True)
    parser.add_argument(
        "--qualification-registry",
        type=Path,
        default=Path("evals/schema-canary/qualification-registry"),
    )
    parser.add_argument("--codex-command")
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--latency-target-seconds", type=int, default=300)
    parser.add_argument("--expected-instance", type=Path)
    parser.add_argument("--prompt-file", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    started = time.monotonic()
    started_at = utc_now()
    root = args.repo_root.resolve()
    if args.timeout_seconds <= 0 or args.latency_target_seconds <= 0:
        raise SchemaCanaryError("canary timeout and latency target must be positive")
    output_dir = resolve_under(root, args.output_dir, label="output_dir")
    if output_dir.exists():
        raise SchemaCanaryError(
            "schema canary output directory already exists; retries and overwrites are "
            f"forbidden: {output_dir}"
        )
    if re.fullmatch(r"[A-Za-z0-9._-]+", args.qualification_id) is None:
        raise SchemaCanaryError(
            "qualification_id must contain only ASCII letters, digits, dot, underscore "
            "or hyphen"
        )
    qualification_registry = resolve_under(
        root,
        args.qualification_registry,
        label="qualification_registry",
    )
    reservation_path = qualification_registry / f"{args.qualification_id}.reserved.json"
    if reservation_path.exists():
        raise SchemaCanaryError(
            "schema canary qualification was already attempted; a new output directory "
            f"must not be used as a retry: {args.qualification_id}"
        )

    # Complete every deterministic gate before consuming the exclusive qualification.
    manifest_path = resolve_under(root, args.manifest, label="manifest")
    manifest_input_sha256 = sha256_file(manifest_path)
    manifest = load_source_assertion_manifest(manifest_path, root)
    schema = receipt_schema(manifest)
    validate_openai_strict_output_schema(schema)
    schema_shape_sha256 = openai_strict_output_schema_shape_sha256(schema)
    schema_bytes = json.dumps(schema, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    schema_sha256 = sha256_bytes(schema_bytes)

    generated_instance = deterministic_transport_instance(schema)
    if not isinstance(generated_instance, dict):
        raise SchemaCanaryError("generated transport fixture root must be an object")
    expected_instance = generated_instance
    expected_input_path: Path | None = None
    if args.expected_instance is not None:
        expected_input_path = resolve_under(
            root,
            args.expected_instance,
            label="expected_instance",
        )
        try:
            loaded_expected = json.loads(expected_input_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise SchemaCanaryError(f"cannot load expected transport fixture: {exc}") from exc
        if loaded_expected != generated_instance:
            raise SchemaCanaryError(
                "provided expected transport fixture differs from deterministic schema fixture"
            )
        expected_instance = loaded_expected
    try:
        validate_openai_strict_output_instance(expected_instance, schema)
    except ValueError as exc:
        raise SchemaCanaryError(
            f"deterministic transport fixture does not satisfy exact schema: {exc}"
        ) from exc
    if not semantic_receipt_is_rejected(expected_instance, manifest):
        raise SchemaCanaryError(
            "transport fixture unexpectedly passes the semantic source-review validator"
        )
    expected_canonical_sha256 = sha256_bytes(canonical_json_bytes(expected_instance))
    prompt = transport_prompt(expected_instance)
    prompt_input_path: Path | None = None
    if args.prompt_file is not None:
        prompt_input_path = resolve_under(root, args.prompt_file, label="prompt_file")
        try:
            supplied_prompt = prompt_input_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise SchemaCanaryError(f"cannot load transport prompt: {exc}") from exc
        if supplied_prompt != prompt:
            raise SchemaCanaryError(
                "provided transport prompt differs from deterministic expected prompt"
            )

    architecture_paths = (
        Path("scripts/openai_strict_output_schema.py"),
        Path("scripts/codex_exec_source_assertion_reviewer.py"),
        Path("scripts/codex_exec_schema_canary.py"),
        Path("scripts/review_cycle_backend_dispatcher.py"),
        Path("test_case_agent/review_cycle/exec_backend.py"),
        Path("test_case_agent/review_cycle/exec_events.py"),
        Path("test_case_agent/review_cycle/schema_canary_contract.py"),
        Path("test_case_agent/review_cycle/source_assertions.py"),
    )
    architecture_bindings = {
        path.as_posix(): sha256_file(root / path) for path in architecture_paths
    }
    requested_codex = (
        resolve_exec_command(args.codex_command) if args.codex_command else None
    )
    resolution = resolve_verified_exec_capability(
        requested_codex,
        additional_required_flags=("--ephemeral", "--ignore-user-config", "--color"),
        required_disable_features=MODEL_TOOL_ISOLATION_DISABLE_FEATURES,
        probe=probe_exec_capability,
    )
    capability = resolution.selection_capability()
    if not resolution.verified:
        raise SchemaCanaryError(
            "codex exec capability is unavailable or incomplete: "
            + (capability.error or ", ".join(capability.missing_flags))
        )
    codex = (
        resolution.selected_executable
        or requested_codex
        or capability.resolved_command
        or capability.command
    )
    codex_path = Path(codex).resolve()
    if not codex_path.is_file():
        raise SchemaCanaryError(
            "schema canary requires one resolved codex executable file: "
            f"{codex_path}"
        )
    codex_executable_sha256 = sha256_file(codex_path)
    version = capability.version or codex_version(codex)
    backend_capability = {
        "selected_executable": resolution.selected_executable,
        "selected_version": version,
        "capability_probe_total_ms": resolution.total_duration_ms,
        "disable_features": list(resolution.disable_features),
        "probes": [asdict(item) for item in resolution.probes],
    }
    qualification_registry.mkdir(parents=True, exist_ok=True)
    try:
        write_json_exclusive(
            reservation_path,
            {
                "version": SCHEMA_CANARY_SUMMARY_VERSION,
                "status": "reserved",
                "qualification_id": args.qualification_id,
                "reserved_at_utc": started_at,
                "output_dir": output_dir.relative_to(root).as_posix(),
            },
        )
    except FileExistsError as exc:
        raise SchemaCanaryError(
            "schema canary qualification was already attempted; a new output directory "
            f"must not be used as a retry: {args.qualification_id}"
        ) from exc
    output_dir.mkdir(parents=True, exist_ok=False)
    summary_path = output_dir / "canary-summary.json"
    terminal_path = output_dir / "qualification-terminal.json"
    schema_path = output_dir / "output-schema.json"
    expected_path = output_dir / "expected-transport-instance.json"
    prompt_path = output_dir / "prompt.txt"
    events_path = output_dir / "events.ndjson"
    stderr_path = output_dir / "stderr.log"
    model_output_path = output_dir / "untrusted-transport-instance.json"
    model_call_started = False
    runtime_metadata: dict[str, Any] = {}
    try:
        with schema_path.open("xb") as stream:
            stream.write(schema_bytes)
        expected_bytes = (
            json.dumps(expected_instance, ensure_ascii=False, indent=2).encode("utf-8")
            + b"\n"
        )
        with expected_path.open("xb") as stream:
            stream.write(expected_bytes)
        with prompt_path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(prompt)
        command = [
            codex,
            "exec",
            *resolution.disable_args,
            "--ephemeral",
            "--ignore-user-config",
            "--sandbox",
            "read-only",
            "--cd",
            str(root),
            "--json",
            "--output-last-message",
            str(model_output_path),
            "--output-schema",
            str(schema_path),
            "--color",
            "never",
            "-",
        ]
        model_call_started = True
        return_code, usage, forbidden = run_exec(
            command,
            prompt=prompt,
            cwd=root,
            events_path=events_path,
            stderr_path=stderr_path,
            timeout_seconds=args.timeout_seconds,
            runtime_metadata=runtime_metadata,
        )
        event_types = event_type_sequence(events_path)
        event_counts: dict[str, int] = {}
        for event_type in event_types:
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        event_counts = dict(sorted(event_counts.items()))
        if forbidden in TOOL_EVENT_ITEM_TYPES:
            raise SchemaCanaryError(
                f"schema canary attempted forbidden tool event: {forbidden}"
            )
        if return_code != 0:
            raise SchemaCanaryError(f"codex exec schema canary exited with code {return_code}")
        expected_lifecycle = {
            "thread.started": 1,
            "turn.started": 1,
            "turn.completed": 1,
        }
        lifecycle_mismatches = {
            name: {"actual": event_counts.get(name, 0), "expected": expected}
            for name, expected in expected_lifecycle.items()
            if event_counts.get(name, 0) != expected
        }
        if lifecycle_mismatches:
            raise SchemaCanaryError(
                "schema canary did not complete exactly one lifecycle: "
                + json.dumps(lifecycle_mismatches, sort_keys=True)
            )
        if (
            not event_types
            or event_types[0] != "thread.started"
            or event_types.index("thread.started")
            >= event_types.index("turn.started")
            or event_types[-1] != "turn.completed"
        ):
            raise SchemaCanaryError(
                "schema canary lifecycle order/boundary is invalid: "
                + json.dumps(event_types, ensure_ascii=False)
            )
        if sha256_bytes(schema_path.read_bytes()) != schema_sha256:
            raise SchemaCanaryError("schema canary output schema changed during model call")
        if sha256_file(manifest_path) != manifest_input_sha256:
            raise SchemaCanaryError("schema canary input manifest changed during model call")
        if sha256_file(expected_path) != sha256_bytes(expected_bytes):
            raise SchemaCanaryError("schema canary expected instance changed during model call")
        if sha256_file(prompt_path) != sha256_bytes(prompt.encode("utf-8")):
            raise SchemaCanaryError("schema canary prompt changed during model call")
        current_architecture = {
            path.as_posix(): sha256_file(root / path) for path in architecture_paths
        }
        if current_architecture != architecture_bindings:
            raise SchemaCanaryError("schema canary architecture changed during model call")
        if expected_input_path is not None and (
            sha256_file(expected_input_path)
            != sha256_file(expected_path)
        ):
            raise SchemaCanaryError("prequalified expected instance changed during model call")
        if prompt_input_path is not None and (
            sha256_file(prompt_input_path)
            != sha256_file(prompt_path)
        ):
            raise SchemaCanaryError("prequalified prompt changed during model call")
        if not model_output_path.is_file():
            raise SchemaCanaryError("codex exec did not publish canary model output")
        try:
            parsed_output = json.loads(model_output_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise SchemaCanaryError(f"canary model output is not valid JSON: {exc}") from exc
        if not isinstance(parsed_output, dict):
            raise SchemaCanaryError("canary model output root must be a JSON object")
        try:
            validate_openai_strict_output_instance(parsed_output, schema)
        except ValueError as exc:
            raise SchemaCanaryError(
                f"canary model output does not satisfy exact output schema: {exc}"
            ) from exc
        if parsed_output != expected_instance:
            raise SchemaCanaryError(
                "canary model output is schema-valid but differs from expected transport fixture"
            )

        duration_ms = int((time.monotonic() - started) * 1000)
        latency_slo_breach = duration_ms > args.latency_target_seconds * 1000

        summary = {
            "version": SCHEMA_CANARY_SUMMARY_VERSION,
            "status": "passed",
            "qualification_passed": True,
            "started_at_utc": started_at,
            "finished_at_utc": utc_now(),
            "duration_ms": duration_ms,
            "attempt_count": 1,
            "max_attempts": 1,
            "retry_count": 0,
            "retry_performed": False,
            "model_call_invocation_count": 1,
            "model_session_count": 1,
            "semantic_review_performed": False,
            "admissible_as_source_review": False,
            "qualification_id": args.qualification_id,
            "manifest_path": manifest_path.relative_to(root).as_posix(),
            "manifest_digest": manifest.digest,
            "manifest_sha256": manifest_input_sha256,
            "schema_sha256": schema_sha256,
            "schema_shape_sha256": schema_shape_sha256,
            "schema_size_bytes": len(schema_bytes),
            "schema_keyword_inventory": schema_keyword_inventory(schema),
            "architecture_bindings": architecture_bindings,
            "runtime_profile": CANARY_RUNTIME_PROFILE,
            "codex_executable": str(codex_path),
            "codex_executable_sha256": codex_executable_sha256,
            "codex_version": version,
            "tool_event_count": 0,
            "transport_instance_schema_validated": True,
            "transport_instance_exact_match": True,
            "transport_instance_semantic_validator_rejected": True,
            "expected_transport_instance_path": expected_path.relative_to(root).as_posix(),
            "expected_transport_instance_sha256": sha256_file(expected_path),
            "expected_transport_instance_canonical_sha256": expected_canonical_sha256,
            "expected_transport_instance_size_bytes": expected_path.stat().st_size,
            "untrusted_transport_instance_sha256": sha256_file(model_output_path),
            "untrusted_transport_instance_canonical_sha256": sha256_bytes(
                canonical_json_bytes(parsed_output)
            ),
            "untrusted_transport_instance_size_bytes": model_output_path.stat().st_size,
            "prompt_path": prompt_path.relative_to(root).as_posix(),
            "prompt_sha256": sha256_file(prompt_path),
            "prompt_size_bytes": prompt_path.stat().st_size,
            "timeout_seconds": args.timeout_seconds,
            "latency_target_seconds": args.latency_target_seconds,
            "latency_class": "slow" if latency_slo_breach else "within-target",
            "latency_slo_breach": latency_slo_breach,
            "input_integrity_revalidated": True,
            "events_sha256": sha256_file(events_path),
            "stderr_sha256": sha256_file(stderr_path),
            "event_type_counts": event_counts,
            "usage": usage,
            "runtime_metadata": runtime_metadata,
            "backend_capability": backend_capability,
        }
        validate_schema_canary_summary(
            summary,
            expected_qualification_id=args.qualification_id,
            expected_manifest_digest=manifest.digest,
            expected_manifest_sha256=manifest_input_sha256,
            expected_schema_sha256=schema_sha256,
        )
        write_json_exclusive(summary_path, summary)
        write_json_exclusive(
            terminal_path,
            {
                "version": 1,
                "status": "qualified",
                "qualification_passed": True,
                "qualification_id": args.qualification_id,
                "summary_path": summary_path.relative_to(root).as_posix(),
                "summary_sha256": sha256_file(summary_path),
                "event_type_counts": event_counts,
                "latency_class": summary["latency_class"],
                "latency_slo_breach": latency_slo_breach,
                "model_call_invocation_count": 1,
                "model_session_count": 1,
                "attempt_count": 1,
                "max_attempts": 1,
                "retry_count": 0,
                "retry_performed": False,
            },
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:  # noqa: BLE001 - preserve the single terminal canary result.
        try:
            failure_event_counts = event_type_counts(events_path)
        except Exception:  # noqa: BLE001 - retain the primary terminal failure.
            failure_event_counts = {}
        failure = {
            "version": SCHEMA_CANARY_SUMMARY_VERSION,
            "status": "failed",
            "qualification_passed": False,
            "started_at_utc": started_at,
            "finished_at_utc": utc_now(),
            "duration_ms": int((time.monotonic() - started) * 1000),
            "attempt_count": 1,
            "max_attempts": 1,
            "retry_count": 0,
            "retry_performed": False,
            "model_call_invocation_count": 1 if model_call_started else 0,
            "model_session_count": failure_event_counts.get("thread.started", 0),
            "semantic_review_performed": False,
            "admissible_as_source_review": False,
            "qualification_id": args.qualification_id,
            "manifest_path": manifest_path.relative_to(root).as_posix(),
            "manifest_digest": manifest.digest,
            "manifest_sha256": manifest_input_sha256,
            "schema_sha256": schema_sha256,
            "schema_shape_sha256": schema_shape_sha256,
            "schema_size_bytes": len(schema_bytes),
            "schema_keyword_inventory": schema_keyword_inventory(schema),
            "expected_transport_instance_sha256": optional_sha256(expected_path),
            "expected_transport_instance_canonical_sha256": expected_canonical_sha256,
            "expected_transport_instance_size_bytes": (
                expected_path.stat().st_size if expected_path.is_file() else None
            ),
            "untrusted_transport_instance_sha256": optional_sha256(model_output_path),
            "untrusted_transport_instance_canonical_sha256": (
                optional_canonical_json_sha256(model_output_path)
            ),
            "untrusted_transport_instance_size_bytes": (
                model_output_path.stat().st_size if model_output_path.is_file() else None
            ),
            "prompt_sha256": optional_sha256(prompt_path),
            "prompt_size_bytes": prompt_path.stat().st_size if prompt_path.is_file() else None,
            "timeout_seconds": args.timeout_seconds,
            "latency_target_seconds": args.latency_target_seconds,
            "event_type_counts": failure_event_counts,
            "events_sha256": optional_sha256(events_path),
            "stderr_sha256": optional_sha256(stderr_path),
            "runtime_profile": CANARY_RUNTIME_PROFILE,
            "codex_executable": str(codex_path),
            "codex_executable_sha256": codex_executable_sha256,
            "codex_version": version,
            "architecture_bindings": architecture_bindings,
            "runtime_metadata": runtime_metadata,
            "backend_capability": backend_capability,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        if not summary_path.exists():
            write_json_exclusive(summary_path, failure)
        if not terminal_path.exists():
            write_json_exclusive(
                terminal_path,
                {
                    "version": 1,
                    "status": "failed",
                    "qualification_passed": False,
                    "qualification_id": args.qualification_id,
                    "summary_path": summary_path.relative_to(root).as_posix(),
                    "summary_sha256": sha256_file(summary_path),
                    "event_type_counts": failure_event_counts,
                    "model_call_invocation_count": 1 if model_call_started else 0,
                    "model_session_count": failure_event_counts.get("thread.started", 0),
                    "attempt_count": 1,
                    "max_attempts": 1,
                    "retry_count": 0,
                    "retry_performed": False,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "runtime_metadata": runtime_metadata,
                },
            )
        print(json.dumps(failure, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SchemaCanaryError as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
