from __future__ import annotations

import re
from typing import Any, Mapping


SCHEMA_CANARY_SUMMARY_VERSION = 2
SCHEMA_CANARY_LATENCY_CLASSES = frozenset({"slow", "within-target"})

_QUALIFICATION_ID_PATTERN = re.compile(r"[A-Za-z0-9._-]+")
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_MISSING = object()


class SchemaCanarySummaryContractError(ValueError):
    """Raised when a successful schema-canary summary violates the v2 contract."""


def _type_label(expected_type: type[Any]) -> str:
    if expected_type is bool:
        return "boolean"
    if expected_type is int:
        return "integer"
    if expected_type is str:
        return "string"
    return expected_type.__name__


def _record_exact_mismatch(
    mismatches: list[str],
    summary: Mapping[str, Any],
    field_name: str,
    expected: Any,
    expected_type: type[Any],
) -> None:
    actual = summary.get(field_name, _MISSING)
    expected_label = _type_label(expected_type)
    if actual is _MISSING:
        mismatches.append(
            f"{field_name} missing; expected {expected_label} {expected!r}"
        )
        return
    if type(actual) is not expected_type:
        mismatches.append(
            f"{field_name} type mismatch; expected {expected_label}, "
            f"got {type(actual).__name__} {actual!r}"
        )
        return
    if actual != expected:
        mismatches.append(
            f"{field_name} mismatch; expected {expected!r}, got {actual!r}"
        )


def _validate_expected_bindings(
    *,
    expected_qualification_id: str,
    expected_manifest_digest: str,
    expected_manifest_sha256: str,
    expected_schema_sha256: str,
) -> None:
    if (
        type(expected_qualification_id) is not str
        or _QUALIFICATION_ID_PATTERN.fullmatch(expected_qualification_id) is None
    ):
        raise SchemaCanarySummaryContractError(
            "expected_qualification_id must be a non-empty schema-canary identifier"
        )
    for field_name, value in (
        ("expected_manifest_digest", expected_manifest_digest),
        ("expected_manifest_sha256", expected_manifest_sha256),
        ("expected_schema_sha256", expected_schema_sha256),
    ):
        if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
            raise SchemaCanarySummaryContractError(
                f"{field_name} must be a lowercase SHA-256 hex digest"
            )


def validate_schema_canary_summary(
    summary: Mapping[str, Any],
    *,
    expected_qualification_id: str,
    expected_manifest_digest: str,
    expected_manifest_sha256: str,
    expected_schema_sha256: str,
) -> None:
    """Validate the shared success invariants of a schema-canary summary v2.

    The producer has additional diagnostic fields that are intentionally outside
    this shared consumer contract. This validator accepts them while checking the
    exact success, single-attempt, non-semantic, and artifact-binding invariants.
    """

    if not isinstance(summary, Mapping):
        raise SchemaCanarySummaryContractError(
            "schema-canary summary must be a JSON object; "
            f"got {type(summary).__name__}"
        )
    _validate_expected_bindings(
        expected_qualification_id=expected_qualification_id,
        expected_manifest_digest=expected_manifest_digest,
        expected_manifest_sha256=expected_manifest_sha256,
        expected_schema_sha256=expected_schema_sha256,
    )

    mismatches: list[str] = []
    for field_name, expected, expected_type in (
        ("version", SCHEMA_CANARY_SUMMARY_VERSION, int),
        ("status", "passed", str),
        ("qualification_passed", True, bool),
        ("attempt_count", 1, int),
        ("max_attempts", 1, int),
        ("model_session_count", 1, int),
        ("model_call_invocation_count", 1, int),
        ("retry_count", 0, int),
        ("retry_performed", False, bool),
        ("semantic_review_performed", False, bool),
        ("admissible_as_source_review", False, bool),
        ("qualification_id", expected_qualification_id, str),
        ("manifest_digest", expected_manifest_digest, str),
        ("manifest_sha256", expected_manifest_sha256, str),
        ("schema_sha256", expected_schema_sha256, str),
    ):
        _record_exact_mismatch(
            mismatches,
            summary,
            field_name,
            expected,
            expected_type,
        )

    latency_class = summary.get("latency_class", _MISSING)
    if latency_class is not _MISSING:
        if type(latency_class) is not str:
            mismatches.append(
                "latency_class type mismatch; expected string, "
                f"got {type(latency_class).__name__} {latency_class!r}"
            )
        elif latency_class not in SCHEMA_CANARY_LATENCY_CLASSES:
            mismatches.append(
                "latency_class mismatch; expected one of "
                f"{sorted(SCHEMA_CANARY_LATENCY_CLASSES)!r}, got {latency_class!r}"
            )

    if mismatches:
        raise SchemaCanarySummaryContractError(
            "schema-canary summary v2 mismatch: " + "; ".join(mismatches)
        )


__all__ = [
    "SCHEMA_CANARY_LATENCY_CLASSES",
    "SCHEMA_CANARY_SUMMARY_VERSION",
    "SchemaCanarySummaryContractError",
    "validate_schema_canary_summary",
]
