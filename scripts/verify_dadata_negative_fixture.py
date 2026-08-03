from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ENDPOINT = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address"
TOKEN_ENV = "DADATA_API_KEY"
FIXTURE_ID_RE = re.compile(r"^FX-DADATA-[A-Z0-9_-]+$")


class DadataFixtureVerificationError(RuntimeError):
    pass


def _canonical_json_bytes(payload: Any) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _request_json_once(
    *,
    query: str,
    token: str,
    timeout_seconds: float,
    opener: Callable[..., Any],
    parameters: dict[str, Any] | None = None,
    endpoint: str = ENDPOINT,
) -> tuple[dict[str, Any], int]:
    request_parameters = {"query": query, **(parameters or {})}
    request_body = _canonical_json_bytes(request_parameters)
    request = Request(
        endpoint,
        data=request_body,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Token {token}",
        },
    )
    try:
        with opener(request, timeout=timeout_seconds) as response:
            status = int(getattr(response, "status", response.getcode()))
            raw_body = response.read()
    except HTTPError as exc:
        raise DadataFixtureVerificationError(
            f"DaData returned HTTP {exc.code}; no fixture was written"
        ) from exc
    except URLError as exc:
        raise DadataFixtureVerificationError(
            f"DaData request failed: {exc.reason}; no fixture was written"
        ) from exc

    if status != 200:
        raise DadataFixtureVerificationError(
            f"DaData returned HTTP {status}; expected 200; no fixture was written"
        )
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DadataFixtureVerificationError(
            "DaData response is not valid UTF-8 JSON; no fixture was written"
        ) from exc
    if not isinstance(payload, dict):
        raise DadataFixtureVerificationError(
            "DaData response must be a JSON object; no fixture was written"
        )
    return payload, status


def _request_once(
    *,
    query: str,
    token: str,
    timeout_seconds: float,
    opener: Callable[..., Any],
) -> tuple[dict[str, Any], int]:
    payload, status = _request_json_once(
        query=query,
        token=token,
        timeout_seconds=timeout_seconds,
        opener=opener,
    )
    if payload != {"suggestions": []}:
        raise DadataFixtureVerificationError(
            "DaData response is not exactly suggestions=[]; no fixture was written"
        )
    return payload, status


def verify_negative_fixture(
    *,
    query: str,
    fixture_id: str,
    output_dir: Path,
    token: str,
    attempts: int = 2,
    timeout_seconds: float = 30.0,
    opener: Callable[..., Any] = urlopen,
    clock: Callable[[], datetime] = _utc_now,
) -> dict[str, Any]:
    if not query.strip():
        raise DadataFixtureVerificationError("query must be non-empty")
    if FIXTURE_ID_RE.fullmatch(fixture_id) is None:
        raise DadataFixtureVerificationError("fixture_id has an invalid format")
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

    normalized_response = {"suggestions": []}
    response_bytes = _canonical_json_bytes(normalized_response)
    response_sha256 = hashlib.sha256(response_bytes).hexdigest()
    attempt_receipts: list[dict[str, Any]] = []
    for attempt_number in range(1, attempts + 1):
        payload, status = _request_once(
            query=query,
            token=token,
            timeout_seconds=timeout_seconds,
            opener=opener,
        )
        checked_at = clock().astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        attempt_receipts.append(
            {
                "attempt": attempt_number,
                "checked_at_utc": checked_at,
                "http_status": status,
                "response_sha256": hashlib.sha256(
                    _canonical_json_bytes(payload)
                ).hexdigest(),
                "exact_empty_suggestions": True,
            }
        )

    snapshot_name = f"{fixture_id}.response.json"
    verification_name = f"{fixture_id}.verification.json"
    receipt = {
        "schema_version": 1,
        "fixture_id": fixture_id,
        "provider": "DaData",
        "evidence_kind": "verified-live-negative-response",
        "status": "verified",
        "request": {
            "method": "POST",
            "endpoint": ENDPOINT,
            "parameters": {"query": query},
        },
        "verification": {
            "attempt_count": attempts,
            "all_http_200": True,
            "all_exact_empty_suggestions": True,
            "attempts": attempt_receipts,
        },
        "response_snapshot": snapshot_name,
        "response_sha256": response_sha256,
    }
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / snapshot_name).write_bytes(response_bytes)
    (output_dir / verification_name).write_bytes(_canonical_json_bytes(receipt))
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify a negative DaData address fixture twice and write immutable "
            "token-free evidence only when every response is exactly suggestions=[]."
        )
    )
    parser.add_argument("--query", required=True, help="Exact address query to verify.")
    parser.add_argument(
        "--fixture-id",
        default="FX-DADATA-ADDR-NEG-001",
        help="Stable FX-DADATA-* identifier.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="New immutable directory for response and verification JSON files.",
    )
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        receipt = verify_negative_fixture(
            query=args.query,
            fixture_id=args.fixture_id,
            output_dir=args.output_dir,
            token=os.environ.get(TOKEN_ENV, ""),
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
