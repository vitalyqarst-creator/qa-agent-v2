from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ENDPOINT = "https://api.randomdatatools.ru/"
FIXTURE_ID_RE = re.compile(r"^FX-SYNTH-[A-Z0-9_-]+$")
SELECTION_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
PATH_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")
MAX_RESPONSE_BYTES = 512 * 1024


class SyntheticFixtureError(RuntimeError):
    """The synthetic fixture was not created and no partial output is allowed."""


def _canonical_json_bytes(payload: Any) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_name_value(value: str, *, label: str) -> tuple[str, str]:
    name, separator, remainder = value.partition("=")
    if not separator or not name.strip() or not remainder.strip():
        raise argparse.ArgumentTypeError(f"{label} must use non-empty name=value syntax")
    if SELECTION_NAME_RE.fullmatch(name.strip()) is None:
        raise argparse.ArgumentTypeError(f"{label} name has an invalid format")
    return name.strip(), remainder.strip()


def _selection(value: str) -> tuple[str, str]:
    name, path = _parse_name_value(value, label="selection")
    if PATH_RE.fullmatch(path) is None:
        raise argparse.ArgumentTypeError("selection path has an invalid format")
    return name, path


def _pattern(value: str) -> tuple[str, str]:
    name, pattern = _parse_name_value(value, label="pattern")
    try:
        re.compile(pattern)
    except re.error as exc:
        raise argparse.ArgumentTypeError(f"pattern is invalid: {exc}") from exc
    return name, pattern


def _value_at_path(payload: Mapping[str, Any], path: str) -> Any:
    current: Any = payload
    for segment in path.split("."):
        if not isinstance(current, Mapping) or segment not in current:
            raise SyntheticFixtureError(
                f"response has no non-empty value at selected path {path!r}; no fixture was written"
            )
        current = current[segment]
    if current is None or (isinstance(current, str) and not current.strip()):
        raise SyntheticFixtureError(
            f"response has no non-empty value at selected path {path!r}; no fixture was written"
        )
    return current


def _scalar_value(payload: Mapping[str, Any], path: str) -> str | int | float | bool:
    value = _value_at_path(payload, path)
    if isinstance(value, bool | int | float | str):
        return value
    raise SyntheticFixtureError(
        f"selected path {path!r} must resolve to a scalar value; no fixture was written"
    )


def _request_profile(
    *,
    timeout_seconds: float,
    opener: Callable[..., Any],
) -> tuple[dict[str, Any], int]:
    if timeout_seconds <= 0:
        raise SyntheticFixtureError("timeout_seconds must be positive")
    request = Request(
        ENDPOINT,
        method="GET",
        headers={"Accept": "application/json", "User-Agent": "FT-Test-Case-Agent/1.0"},
    )
    try:
        with opener(request, timeout=timeout_seconds) as response:
            status_value = getattr(response, "status", None)
            status = int(status_value if status_value is not None else response.getcode())
            raw_body = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        raise SyntheticFixtureError(
            f"RandomDataTools returned HTTP {exc.code}; no fixture was written"
        ) from exc
    except URLError as exc:
        raise SyntheticFixtureError(
            f"RandomDataTools request failed: {exc.reason}; no fixture was written"
        ) from exc

    if status != 200:
        raise SyntheticFixtureError(
            f"RandomDataTools returned HTTP {status}; expected 200; no fixture was written"
        )
    if len(raw_body) > MAX_RESPONSE_BYTES:
        raise SyntheticFixtureError("RandomDataTools response exceeds the size limit; no fixture was written")
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SyntheticFixtureError(
            "RandomDataTools response is not valid UTF-8 JSON; no fixture was written"
        ) from exc
    if not isinstance(payload, dict):
        raise SyntheticFixtureError(
            "RandomDataTools response must be a JSON object; no fixture was written"
        )
    return payload, status


def create_synthetic_fixture(
    *,
    fixture_id: str,
    purpose: str,
    selected_paths: Mapping[str, str],
    output_dir: Path,
    required_paths: Sequence[str] = (),
    patterns_by_name: Mapping[str, str] | None = None,
    timeout_seconds: float = 30.0,
    opener: Callable[..., Any] = urlopen,
    clock: Callable[[], datetime] = _utc_now,
) -> dict[str, Any]:
    """Create one immutable, token-free synthetic fixture from a single API call."""

    if FIXTURE_ID_RE.fullmatch(fixture_id) is None:
        raise SyntheticFixtureError("fixture_id must use the FX-SYNTH-* format")
    if not purpose.strip():
        raise SyntheticFixtureError("purpose must be non-empty")
    if not selected_paths:
        raise SyntheticFixtureError("at least one selected path is required")
    if output_dir.exists():
        raise SyntheticFixtureError("output_dir must be a new immutable directory")
    if any(
        SELECTION_NAME_RE.fullmatch(name) is None or PATH_RE.fullmatch(path) is None
        for name, path in selected_paths.items()
    ):
        raise SyntheticFixtureError("selected_paths contains an invalid name or path")
    if any(PATH_RE.fullmatch(path) is None for path in required_paths):
        raise SyntheticFixtureError("required_paths contains an invalid path")

    patterns = dict(patterns_by_name or {})
    unknown_pattern_names = sorted(set(patterns) - set(selected_paths))
    if unknown_pattern_names:
        raise SyntheticFixtureError(
            "patterns reference unknown selected values: " + ", ".join(unknown_pattern_names)
        )
    try:
        compiled_patterns = {name: re.compile(pattern) for name, pattern in patterns.items()}
    except re.error as exc:
        raise SyntheticFixtureError(f"pattern is invalid: {exc}") from exc

    payload, status = _request_profile(timeout_seconds=timeout_seconds, opener=opener)
    for path in required_paths:
        _value_at_path(payload, path)
    selected_values = {
        name: _scalar_value(payload, path) for name, path in selected_paths.items()
    }
    for name, pattern in compiled_patterns.items():
        if pattern.fullmatch(str(selected_values[name])) is None:
            raise SyntheticFixtureError(
                f"selected value {name!r} does not satisfy its required pattern; no fixture was written"
            )

    response_bytes = _canonical_json_bytes(payload)
    response_sha256 = hashlib.sha256(response_bytes).hexdigest()
    snapshot_name = f"{fixture_id}.response.json"
    receipt_name = f"{fixture_id}.fixture.json"
    generated_at = clock().astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    receipt = {
        "schema_version": 1,
        "fixture_id": fixture_id,
        "provider": "RandomDataTools",
        "evidence_kind": "generated-synthetic-fixture",
        "status": "generated",
        "purpose": purpose.strip(),
        "generation": {
            "method": "GET",
            "endpoint": ENDPOINT,
            "generated_at_utc": generated_at,
            "http_status": status,
            "request_count": 1,
        },
        "selection": {
            "selected_paths": dict(selected_paths),
            "selected_values": selected_values,
            "required_paths": list(required_paths),
            "patterns_by_name": patterns,
        },
        "response_snapshot": snapshot_name,
        "response_sha256": response_sha256,
        "lifecycle": {
            "policy": "snapshot-only / regenerate-by-explicit-request",
            "runtime_live_calls_allowed": False,
        },
        "limitations": [
            "Синтетические значения не подтверждают существование организации, адреса или реквизита во внешних системах.",
            "Fixture нельзя использовать как доказательство бизнес-валидности ИНН, ОГРН, КПП, БИК, расчетного счета или интеграционного сценария.",
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / snapshot_name).write_bytes(response_bytes)
    (output_dir / receipt_name).write_bytes(_canonical_json_bytes(receipt))
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create one immutable FX-SYNTH fixture from a single RandomDataTools API "
            "response. The produced snapshot must be used instead of live calls during tests."
        )
    )
    parser.add_argument("--fixture-id", required=True, help="Stable FX-SYNTH-* identifier.")
    parser.add_argument("--purpose", required=True, help="Concrete test-data purpose.")
    parser.add_argument(
        "--select",
        action="append",
        type=_selection,
        required=True,
        metavar="NAME=JSON_PATH",
        help="Select a non-empty scalar response field into the fixture.",
    )
    parser.add_argument(
        "--require-path",
        action="append",
        default=[],
        metavar="JSON_PATH",
        help="Require another non-empty response field without adding it to test data.",
    )
    parser.add_argument(
        "--pattern",
        action="append",
        type=_pattern,
        default=[],
        metavar="NAME=REGEX",
        help="Require the full value of a selected field to match REGEX.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="New immutable directory for response and fixture JSON files.",
    )
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    selected_paths = dict(args.select)
    if len(selected_paths) != len(args.select):
        raise SystemExit("error: selected field names must be unique")
    patterns = dict(args.pattern)
    if len(patterns) != len(args.pattern):
        raise SystemExit("error: pattern names must be unique")
    try:
        receipt = create_synthetic_fixture(
            fixture_id=args.fixture_id,
            purpose=args.purpose,
            selected_paths=selected_paths,
            required_paths=args.require_path,
            patterns_by_name=patterns,
            output_dir=args.output_dir,
            timeout_seconds=args.timeout_seconds,
        )
    except SyntheticFixtureError as exc:
        raise SystemExit(f"error: {exc}") from exc
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "fixture_id": receipt["fixture_id"],
                "response_sha256": receipt["response_sha256"],
                "request_count": receipt["generation"]["request_count"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
