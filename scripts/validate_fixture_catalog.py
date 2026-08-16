from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ALLOWED_SOURCE_TYPES = {"local", "provider", "public_reference", "synthetic"}
SECRET_KEYS = {"token", "api_key", "apikey", "secret", "password", "authorization"}


def has_secret(value: Any) -> bool:
    if isinstance(value, dict):
        return any(str(key).lower() in SECRET_KEYS or has_secret(item) for key, item in value.items())
    if isinstance(value, list):
        return any(has_secret(item) for item in value)
    return False


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"catalog-read-error: {exc}"]

    fixtures = payload.get("fixtures") if isinstance(payload, dict) else payload
    if not isinstance(fixtures, list) or not fixtures:
        return ["fixtures must be a non-empty JSON list or an object with non-empty fixtures"]

    seen_ids: set[str] = set()
    for index, fixture in enumerate(fixtures, start=1):
        label = f"fixture[{index}]"
        if not isinstance(fixture, dict):
            errors.append(f"{label}: must be an object")
            continue
        fixture_id = fixture.get("fixture_id")
        if not isinstance(fixture_id, str) or not fixture_id.strip():
            errors.append(f"{label}: fixture_id is required")
        elif fixture_id in seen_ids:
            errors.append(f"{label}: duplicate fixture_id {fixture_id}")
        else:
            seen_ids.add(fixture_id)

        source_type = fixture.get("source_type")
        if source_type not in ALLOWED_SOURCE_TYPES:
            errors.append(f"{label}: unsupported source_type {source_type!r}")
        if not isinstance(fixture.get("purpose"), str) or not fixture["purpose"].strip():
            errors.append(f"{label}: purpose is required")
        if not isinstance(fixture.get("runtime_data"), dict) or not fixture["runtime_data"]:
            errors.append(f"{label}: runtime_data must be a non-empty object")
        if has_secret(fixture):
            errors.append(f"{label}: catalog must not contain credentials or secrets")

        if source_type == "provider":
            if not isinstance(fixture.get("provider"), str) or not fixture["provider"].strip():
                errors.append(f"{label}: provider is required for provider fixture")
            if not isinstance(fixture.get("request"), dict) or not fixture["request"]:
                errors.append(f"{label}: request is required for provider fixture")
            snapshot_path = fixture.get("snapshot_path")
            digest = fixture.get("snapshot_sha256")
            if not isinstance(snapshot_path, str) or not snapshot_path:
                errors.append(f"{label}: snapshot_path is required for provider fixture")
            if not isinstance(digest, str) or len(digest) != 64:
                errors.append(f"{label}: snapshot_sha256 must be a 64-character SHA-256")
            elif isinstance(snapshot_path, str) and snapshot_path:
                snapshot = path.parent / snapshot_path
                if not snapshot.is_file():
                    errors.append(f"{label}: snapshot does not exist: {snapshot_path}")
                else:
                    snapshot_bytes = snapshot.read_bytes()
                    if hashlib.sha256(snapshot_bytes).hexdigest() != digest:
                        errors.append(f"{label}: snapshot SHA-256 mismatch")
                    try:
                        snapshot_payload = json.loads(snapshot_bytes.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        errors.append(f"{label}: snapshot must be UTF-8 JSON")
                    else:
                        if has_secret(snapshot_payload):
                            errors.append(f"{label}: snapshot must not contain credentials or secrets")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a runtime fixture catalog without calling providers.")
    parser.add_argument("catalog", type=Path)
    args = parser.parse_args()
    errors = validate(args.catalog)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
