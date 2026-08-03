from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from .source_assertions import SourceAssertionManifest


SOURCE_GATE_SCHEMA_VERSION = 1
SOURCE_GATE_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "started_at_utc",
        "finished_at_utc",
        "status",
        "validation_invocation_count",
        "manifest_digest",
        "source_row_count",
        "candidate_count",
        "assertion_count",
        "authenticated_testable_obligation_count",
        "checks",
    }
)
SOURCE_GATE_REQUIRED_CHECKS = frozenset(
    {
        "manifest-v4-shape-and-source-fragments",
        "coverage-gap-chain-binding",
        "source-selection-exact-registry",
        "source-row-baseline-bijection",
        "assertion-atom-obligation-chain",
    }
)


class SourceGateContractError(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def authenticated_testable_obligation_ids(
    manifest: SourceAssertionManifest,
) -> frozenset[str]:
    return frozenset(
        obligation_id
        for assertion in manifest.assertions
        if assertion.semantic_disposition == "testable"
        for obligation_id in assertion.obligation_ids
    )


def build_passed_source_gate_receipt(
    *,
    manifest: SourceAssertionManifest,
    started_at_utc: str,
    finished_at_utc: str,
    actual_source_row_count: int,
    actual_candidate_count: int,
    actual_assertion_count: int,
    actual_authenticated_testable_obligation_count: int,
) -> dict[str, Any]:
    expected_counts = {
        "source_row_count": len(manifest.source_rows),
        "candidate_count": manifest.source_row_candidate_count,
        "assertion_count": len(manifest.assertions),
        "authenticated_testable_obligation_count": len(
            authenticated_testable_obligation_ids(manifest)
        ),
    }
    actual_counts = {
        "source_row_count": actual_source_row_count,
        "candidate_count": actual_candidate_count,
        "assertion_count": actual_assertion_count,
        "authenticated_testable_obligation_count": (
            actual_authenticated_testable_obligation_count
        ),
    }
    if actual_counts != expected_counts:
        raise SourceGateContractError(
            "official source gate validation results do not match the manifest: "
            f"expected={expected_counts}, actual={actual_counts}"
        )
    if not started_at_utc or not finished_at_utc:
        raise SourceGateContractError("source gate timestamps must be non-empty")
    return {
        "schema_version": SOURCE_GATE_SCHEMA_VERSION,
        "started_at_utc": started_at_utc,
        "finished_at_utc": finished_at_utc,
        "status": "passed",
        "validation_invocation_count": 1,
        "manifest_digest": manifest.digest,
        **actual_counts,
        "checks": sorted(SOURCE_GATE_REQUIRED_CHECKS),
    }


def validate_passed_source_gate_receipt(
    payload: Mapping[str, Any],
    *,
    manifest: SourceAssertionManifest,
) -> None:
    actual_fields = set(payload)
    if actual_fields != SOURCE_GATE_REQUIRED_FIELDS:
        raise SourceGateContractError(
            "source gate receipt fields mismatch: "
            f"missing={sorted(SOURCE_GATE_REQUIRED_FIELDS - actual_fields) or 'none'}, "
            f"unknown={sorted(actual_fields - SOURCE_GATE_REQUIRED_FIELDS) or 'none'}"
        )
    if payload.get("schema_version") != SOURCE_GATE_SCHEMA_VERSION:
        raise SourceGateContractError(
            f"source gate schema_version must equal {SOURCE_GATE_SCHEMA_VERSION}"
        )
    if payload.get("status") != "passed":
        raise SourceGateContractError("source gate receipt is not passed")
    if payload.get("validation_invocation_count") != 1:
        raise SourceGateContractError(
            "source gate receipt must attest exactly one validation invocation"
        )
    for field in ("started_at_utc", "finished_at_utc"):
        if not isinstance(payload.get(field), str) or not payload[field].strip():
            raise SourceGateContractError(f"source gate {field} must be non-empty")
    if payload.get("manifest_digest") != manifest.digest:
        raise SourceGateContractError(
            "source gate receipt does not bind the current manifest digest"
        )
    expected_counts = {
        "source_row_count": len(manifest.source_rows),
        "candidate_count": manifest.source_row_candidate_count,
        "assertion_count": len(manifest.assertions),
        "authenticated_testable_obligation_count": len(
            authenticated_testable_obligation_ids(manifest)
        ),
    }
    for field, expected in expected_counts.items():
        if type(payload.get(field)) is not int or payload[field] != expected:
            raise SourceGateContractError(
                f"source gate {field} does not bind the current manifest"
            )
    checks = payload.get("checks")
    if not isinstance(checks, list) or any(not isinstance(item, str) for item in checks):
        raise SourceGateContractError("source gate checks must be a string array")
    if len(checks) != len(set(checks)) or set(checks) != SOURCE_GATE_REQUIRED_CHECKS:
        raise SourceGateContractError(
            "source gate check set mismatch: "
            f"missing={sorted(SOURCE_GATE_REQUIRED_CHECKS - set(checks)) or 'none'}, "
            f"extra={sorted(set(checks) - SOURCE_GATE_REQUIRED_CHECKS) or 'none'}"
        )
