from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.request import urlopen


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.verify_dadata_negative_fixture import (
    ENDPOINT,
    FIXTURE_ID_RE,
    TOKEN_ENV,
    DadataFixtureVerificationError,
    _canonical_json_bytes,
    _request_json_once,
    _utc_now,
)


FMS_UNIT_ENDPOINT = (
    "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/fms_unit"
)
PARTY_ENDPOINT = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/party"
ALLOWED_ENDPOINTS = frozenset({ENDPOINT, FMS_UNIT_ENDPOINT, PARTY_ENDPOINT})
SUGGESTION_TYPE_ENDPOINTS = {
    "address": ENDPOINT,
    "fms_unit": FMS_UNIT_ENDPOINT,
    "party": PARTY_ENDPOINT,
}


def _component(value: str) -> tuple[str, str]:
    key, separator, expected = value.partition("=")
    if not separator or not key.strip() or not expected.strip():
        raise argparse.ArgumentTypeError(
            "expected component must use non-empty key=value syntax"
        )
    return key.strip(), expected.strip()


def _component_value(data: Mapping[str, Any], path: str) -> Any:
    current: Any = data
    for segment in path.split("."):
        if not isinstance(current, Mapping):
            return None
        current = current.get(segment)
    return current


def _matched_suggestion(
    payload: Mapping[str, Any],
    *,
    expected_suggestion: str,
    expected_components: Mapping[str, str],
    minimum_suggestion_count: int,
) -> Mapping[str, Any]:
    suggestions = payload.get("suggestions")
    if not isinstance(suggestions, list):
        raise DadataFixtureVerificationError(
            "DaData response misses suggestions array; no fixture was written"
        )
    if len(suggestions) < minimum_suggestion_count:
        raise DadataFixtureVerificationError(
            "DaData response contains fewer suggestions than required by the fixture "
            f"contract: required={minimum_suggestion_count} actual={len(suggestions)}"
        )
    matches = [
        item
        for item in suggestions
        if isinstance(item, Mapping) and item.get("value") == expected_suggestion
    ]
    if len(matches) != 1:
        actual_values = [
            item.get("value")
            for item in suggestions
            if isinstance(item, Mapping) and isinstance(item.get("value"), str)
        ]
        raise DadataFixtureVerificationError(
            "DaData response must contain the exact expected suggestion once; "
            "actual suggestion values="
            + json.dumps(actual_values, ensure_ascii=False)
            + "; no fixture was written"
        )
    match = matches[0]
    data = match.get("data")
    if not isinstance(data, Mapping):
        raise DadataFixtureVerificationError(
            "matched DaData suggestion misses data object; no fixture was written"
        )
    mismatches = {
        key: {"expected": expected, "actual": _component_value(data, key)}
        for key, expected in expected_components.items()
        if _component_value(data, key) != expected
    }
    if mismatches:
        raise DadataFixtureVerificationError(
            "DaData suggestion components differ from the fixture contract: "
            + json.dumps(mismatches, ensure_ascii=False, sort_keys=True)
        )
    return match


def verify_positive_fixture(
    *,
    query: str,
    fixture_id: str,
    expected_suggestion: str,
    expected_components: Mapping[str, str],
    output_dir: Path,
    token: str,
    request_parameters: Mapping[str, Any] | None = None,
    endpoint: str = ENDPOINT,
    minimum_suggestion_count: int = 1,
    attempts: int = 2,
    timeout_seconds: float = 30.0,
    opener: Callable[..., Any] = urlopen,
    clock: Callable[[], datetime] = _utc_now,
) -> dict[str, Any]:
    if not query.strip():
        raise DadataFixtureVerificationError("query must be non-empty")
    if FIXTURE_ID_RE.fullmatch(fixture_id) is None:
        raise DadataFixtureVerificationError("fixture_id has an invalid format")
    if not expected_suggestion.strip():
        raise DadataFixtureVerificationError("expected_suggestion must be non-empty")
    if not expected_components:
        raise DadataFixtureVerificationError(
            "expected_components must contain at least one exact component"
        )
    if endpoint not in ALLOWED_ENDPOINTS:
        raise DadataFixtureVerificationError(
            "endpoint is not an allowlisted DaData suggestions endpoint"
        )
    if minimum_suggestion_count < 1:
        raise DadataFixtureVerificationError(
            "minimum_suggestion_count must be positive"
        )
    if any(not key.strip() or not value.strip() for key, value in expected_components.items()):
        raise DadataFixtureVerificationError(
            "expected component keys and values must be non-empty"
        )
    if not token:
        raise DadataFixtureVerificationError(
            f"{TOKEN_ENV} is unavailable; no live request was attempted"
        )
    if attempts < 2 or attempts > 5:
        raise DadataFixtureVerificationError("attempts must be between 2 and 5")
    if timeout_seconds <= 0:
        raise DadataFixtureVerificationError("timeout_seconds must be positive")
    if output_dir.exists():
        raise DadataFixtureVerificationError(
            "output_dir must be a new immutable directory"
        )

    parameters = dict(request_parameters or {})
    if "query" in parameters:
        raise DadataFixtureVerificationError(
            "request_parameters must not redefine query"
        )
    attempt_receipts: list[dict[str, Any]] = []
    response_payload: dict[str, Any] | None = None
    response_sha256: str | None = None
    for attempt_number in range(1, attempts + 1):
        payload, status = _request_json_once(
            query=query,
            token=token,
            timeout_seconds=timeout_seconds,
            opener=opener,
            parameters=parameters,
            endpoint=endpoint,
        )
        _matched_suggestion(
            payload,
            expected_suggestion=expected_suggestion,
            expected_components=expected_components,
            minimum_suggestion_count=minimum_suggestion_count,
        )
        current_sha256 = hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()
        if response_sha256 is not None and current_sha256 != response_sha256:
            raise DadataFixtureVerificationError(
                "DaData responses changed between verification attempts; "
                "no fixture was written"
            )
        response_payload = payload
        response_sha256 = current_sha256
        checked_at = clock().astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        attempt_receipts.append(
            {
                "attempt": attempt_number,
                "checked_at_utc": checked_at,
                "http_status": status,
                "response_sha256": current_sha256,
                "exact_suggestion_matched": True,
                "exact_components_matched": True,
                "minimum_suggestion_count_matched": True,
            }
        )

    assert response_payload is not None and response_sha256 is not None
    snapshot_name = f"{fixture_id}.response.json"
    verification_name = f"{fixture_id}.verification.json"
    request = {"query": query, **parameters}
    receipt = {
        "schema_version": 1,
        "fixture_id": fixture_id,
        "provider": "DaData",
        "evidence_kind": "verified-live-positive-response",
        "status": "verified",
        "request": {
            "method": "POST",
            "endpoint": endpoint,
            "parameters": request,
        },
        "expected_response": {
            "outcome": "suggestions-found",
            "exact_suggestion": expected_suggestion,
            "exact_components": dict(expected_components),
            "minimum_suggestion_count": minimum_suggestion_count,
        },
        "verification": {
            "attempt_count": attempts,
            "all_http_200": True,
            "all_responses_identical": True,
            "all_exact_suggestion_matched": True,
            "all_exact_components_matched": True,
            "all_minimum_suggestion_count_matched": True,
            "attempts": attempt_receipts,
        },
        "response_snapshot": snapshot_name,
        "response_sha256": response_sha256,
    }
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / snapshot_name).write_bytes(_canonical_json_bytes(response_payload))
    (output_dir / verification_name).write_bytes(_canonical_json_bytes(receipt))
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify one positive DaData suggestions fixture with repeated identical "
            "responses and write immutable token-free evidence."
        )
    )
    parser.add_argument("--query", required=True)
    parser.add_argument("--fixture-id", required=True)
    parser.add_argument("--expected-suggestion", required=True)
    parser.add_argument(
        "--expected-component",
        action="append",
        type=_component,
        default=[],
        metavar="KEY=VALUE",
    )
    parser.add_argument("--from-bound")
    parser.add_argument("--to-bound")
    parser.add_argument(
        "--suggestion-type",
        choices=sorted(SUGGESTION_TYPE_ENDPOINTS),
        default="address",
    )
    parser.add_argument("--minimum-suggestion-count", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    components = dict(args.expected_component)
    if len(components) != len(args.expected_component):
        raise SystemExit("error: expected component keys must be unique")
    request_parameters: dict[str, Any] = {}
    if args.from_bound:
        request_parameters["from_bound"] = {"value": args.from_bound}
    if args.to_bound:
        request_parameters["to_bound"] = {"value": args.to_bound}
    try:
        receipt = verify_positive_fixture(
            query=args.query,
            fixture_id=args.fixture_id,
            expected_suggestion=args.expected_suggestion,
            expected_components=components,
            output_dir=args.output_dir,
            token=os.environ.get(TOKEN_ENV, ""),
            request_parameters=request_parameters,
            endpoint=SUGGESTION_TYPE_ENDPOINTS[args.suggestion_type],
            minimum_suggestion_count=args.minimum_suggestion_count,
            attempts=args.attempts,
            timeout_seconds=args.timeout_seconds,
        )
    except DadataFixtureVerificationError as exc:
        raise SystemExit(f"error: {exc}") from exc
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "fixture_id": receipt["fixture_id"],
                "attempt_count": receipt["verification"]["attempt_count"],
                "response_sha256": receipt["response_sha256"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
