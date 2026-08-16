from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


TOKEN_ENV = "DADATA_API_KEY"
FIXTURE_ID = re.compile(r"^FX-[A-Z0-9_-]+$")
ENDPOINTS = {
    "party": "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/party",
    "address": "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address",
}


class CaptureError(RuntimeError):
    pass


def canonical_json(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def request_suggestions(*, endpoint: str, query: str, token: str, timeout_seconds: float) -> list[dict[str, Any]]:
    request = Request(
        endpoint,
        data=canonical_json({"query": query}),
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Token {token}",
        },
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            status = int(getattr(response, "status", response.getcode()))
            body = response.read()
    except HTTPError as exc:
        raise CaptureError(f"DaData returned HTTP {exc.code}; fixture was not created") from exc
    except URLError as exc:
        raise CaptureError(f"DaData request failed: {exc.reason}; fixture was not created") from exc
    if status != 200:
        raise CaptureError(f"DaData returned HTTP {status}; fixture was not created")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CaptureError("DaData response is not UTF-8 JSON; fixture was not created") from exc
    suggestions = payload.get("suggestions") if isinstance(payload, dict) else None
    if not isinstance(suggestions, list) or not all(isinstance(item, dict) for item in suggestions):
        raise CaptureError("DaData response has no valid suggestions list; fixture was not created")
    return suggestions


def capture_fixture(
    *,
    kind: str,
    query: str,
    fixture_id: str,
    purpose: str,
    fixture_root: Path,
    selection_index: int = 0,
    attempts: int = 2,
    timeout_seconds: float = 30.0,
    token: str | None = None,
) -> dict[str, Any]:
    if kind not in ENDPOINTS:
        raise CaptureError(f"unsupported suggestion kind: {kind}")
    if not query.strip() or not purpose.strip():
        raise CaptureError("query and purpose must be non-empty")
    if FIXTURE_ID.fullmatch(fixture_id) is None:
        raise CaptureError("fixture_id must use FX-<UPPERCASE_ID> format")
    if attempts < 2 or attempts > 5:
        raise CaptureError("attempts must be between 2 and 5")
    if selection_index < 0 or timeout_seconds <= 0:
        raise CaptureError("selection_index and timeout_seconds are invalid")
    actual_token = token if token is not None else os.environ.get(TOKEN_ENV, "")
    if not actual_token:
        raise CaptureError(f"{TOKEN_ENV} is unavailable; no live request was made")

    fixture_dir = fixture_root / fixture_id
    if fixture_dir.exists():
        raise CaptureError(f"fixture directory already exists: {fixture_dir}")
    selected: dict[str, Any] | None = None
    for attempt in range(attempts):
        suggestions = request_suggestions(
            endpoint=ENDPOINTS[kind], query=query, token=actual_token, timeout_seconds=timeout_seconds
        )
        if selection_index >= len(suggestions):
            raise CaptureError(
                f"DaData returned {len(suggestions)} suggestions; index {selection_index} is unavailable"
            )
        current = suggestions[selection_index]
        if not isinstance(current.get("value"), str) or not current["value"].strip():
            raise CaptureError("selected suggestion has no display value")
        if selected is not None and canonical_json(current) != canonical_json(selected):
            raise CaptureError(
                "selected suggestion changed between requests; choose a more stable query or do not create a fixture"
            )
        selected = current

    assert selected is not None
    snapshot = {
        "provider": "DaData",
        "suggestion_kind": kind,
        "endpoint": ENDPOINTS[kind],
        "request": {"query": query, "selection_index": selection_index},
        "suggestion": selected,
    }
    snapshot_bytes = canonical_json(snapshot)
    digest = hashlib.sha256(snapshot_bytes).hexdigest()
    fixture_dir.mkdir(parents=True, exist_ok=False)
    (fixture_dir / "response.json").write_bytes(snapshot_bytes)

    catalog_path = fixture_root / "fixture-catalog.json"
    if catalog_path.exists():
        try:
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CaptureError("existing fixture catalog is not valid JSON") from exc
        fixtures = catalog.get("fixtures") if isinstance(catalog, dict) else None
        if not isinstance(fixtures, list):
            raise CaptureError("existing fixture catalog has no fixtures list")
    else:
        catalog = {"schema_version": 1, "fixtures": []}
        fixtures = catalog["fixtures"]
    if any(isinstance(item, dict) and item.get("fixture_id") == fixture_id for item in fixtures):
        raise CaptureError(f"fixture_id already exists in catalog: {fixture_id}")

    entry = {
        "fixture_id": fixture_id,
        "purpose": purpose,
        "source_type": "provider",
        "provider": "DaData",
        "request": {"suggestion_kind": kind, "query": query, "selection_index": selection_index},
        "runtime_data": {"suggestion": selected.get("value"), "data": selected.get("data", {})},
        "snapshot_path": f"{fixture_id}/response.json",
        "snapshot_sha256": digest,
    }
    fixtures.append(entry)
    fixtures.sort(key=lambda item: str(item.get("fixture_id", "")))
    catalog_path.write_bytes(canonical_json(catalog))
    return entry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture one stable DaData suggestion as a token-free runtime fixture."
    )
    parser.add_argument("--kind", choices=sorted(ENDPOINTS), default="party")
    parser.add_argument("--query", required=True)
    parser.add_argument("--fixture-id", required=True)
    parser.add_argument("--purpose", required=True)
    parser.add_argument("--fixture-root", type=Path, required=True)
    parser.add_argument("--selection-index", type=int, default=0)
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        entry = capture_fixture(
            kind=args.kind,
            query=args.query,
            fixture_id=args.fixture_id,
            purpose=args.purpose,
            fixture_root=args.fixture_root,
            selection_index=args.selection_index,
            attempts=args.attempts,
            timeout_seconds=args.timeout_seconds,
        )
    except CaptureError as exc:
        print(f"error: {exc}", file=os.sys.stderr)
        return 1
    print(json.dumps(entry, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
