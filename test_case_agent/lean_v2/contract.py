from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence


class LeanV2ContractError(ValueError):
    """Raised when a lean-v2 source packet is incomplete or inconsistent."""


TEMPLATE_KINDS = {
    "visibility",
    "default",
    "editability",
    "dictionary",
    "positive-input",
    "requiredness",
    "calibration-negative",
    "behavior",
    "complex",
}
SOURCE_ROLES = {"docx", "xhtml", "pdf", "support", "mockup", "package-notes"}
FORBIDDEN_SOURCE_PATH_PARTS = {"test-cases", "review-cycles", "review-loops", "evals"}
HEX_SHA256_RE = re.compile(r"[0-9a-f]{64}")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def packet_sha256(packet: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_json_bytes(packet))


def _mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise LeanV2ContractError(f"{path} must be an object")
    return value


def _list(value: Any, path: str, *, allow_empty: bool = True) -> list[Any]:
    if not isinstance(value, list):
        raise LeanV2ContractError(f"{path} must be an array")
    if not allow_empty and not value:
        raise LeanV2ContractError(f"{path} must not be empty")
    return value


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LeanV2ContractError(f"{path} must be a non-empty string")
    return value.strip()


def _single_line(value: Any, path: str) -> str:
    result = _text(value, path)
    if "\n" in result or "\r" in result:
        raise LeanV2ContractError(f"{path} must be a single-line string")
    return result


def _string_list(value: Any, path: str, *, allow_empty: bool = True) -> list[str]:
    values = _list(value, path, allow_empty=allow_empty)
    result: list[str] = []
    for index, item in enumerate(values):
        result.append(_single_line(item, f"{path}[{index}]"))
    return result


def _resolve_registered_path(repo_root: Path, value: str, path: str) -> Path:
    candidate = Path(value)
    resolved = (candidate if candidate.is_absolute() else repo_root / candidate).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise LeanV2ContractError(f"{path} escapes repo_root: {value}") from exc
    return resolved


def validate_source_files(
    packet: Mapping[str, Any],
    *,
    repo_root: Path,
) -> tuple[dict[str, Any], ...]:
    source_files = _list(packet.get("source_files"), "$.source_files", allow_empty=False)
    normalized: list[dict[str, Any]] = []
    roles: set[str] = set()
    paths: set[str] = set()
    for index, raw in enumerate(source_files):
        item = _mapping(raw, f"$.source_files[{index}]")
        role = _single_line(item.get("role"), f"$.source_files[{index}].role").casefold()
        if role not in SOURCE_ROLES:
            raise LeanV2ContractError(f"unsupported source role: {role}")
        relative_path = _single_line(item.get("path"), f"$.source_files[{index}].path")
        expected_sha = _single_line(
            item.get("sha256"), f"$.source_files[{index}].sha256"
        ).casefold()
        if HEX_SHA256_RE.fullmatch(expected_sha) is None:
            raise LeanV2ContractError(
                f"$.source_files[{index}].sha256 must be a lowercase SHA-256"
            )
        resolved = _resolve_registered_path(
            repo_root,
            relative_path,
            f"$.source_files[{index}].path",
        )
        if not resolved.is_file():
            raise LeanV2ContractError(f"registered source file does not exist: {resolved}")
        path_parts = {part.casefold() for part in resolved.parts}
        forbidden_parts = path_parts & FORBIDDEN_SOURCE_PATH_PARTS
        if forbidden_parts:
            raise LeanV2ContractError(
                "source registry cannot read test-case/history paths: "
                + ", ".join(sorted(forbidden_parts))
            )
        if role == "docx" and resolved.suffix.casefold() != ".docx":
            raise LeanV2ContractError(f"docx role requires a .docx file: {relative_path}")
        if role == "xhtml" and resolved.suffix.casefold() not in {".xhtml", ".html"}:
            raise LeanV2ContractError(f"xhtml role requires a .xhtml/.html file: {relative_path}")
        actual_sha = sha256_file(resolved)
        if actual_sha != expected_sha:
            raise LeanV2ContractError(
                f"registered source hash mismatch for {relative_path}: "
                f"expected {expected_sha}, got {actual_sha}"
            )
        normalized_key = str(resolved).casefold()
        if normalized_key in paths:
            raise LeanV2ContractError(f"duplicate registered source path: {relative_path}")
        paths.add(normalized_key)
        roles.add(role)
        normalized.append(
            {
                "role": role,
                "path": relative_path,
                "resolved_path": str(resolved),
                "sha256": actual_sha,
                "bytes": resolved.stat().st_size,
            }
        )
    missing = {"docx", "xhtml"} - roles
    if missing:
        raise LeanV2ContractError(
            "lean-v2 requires registered DOCX and XHTML sources; missing roles: "
            + ", ".join(sorted(missing))
        )
    for main_role in ("docx", "xhtml"):
        count = sum(1 for item in normalized if item["role"] == main_role)
        if count != 1:
            raise LeanV2ContractError(
                f"lean-v2 requires exactly one {main_role} source; got {count}"
            )
    return tuple(normalized)


def load_source_packet(path: Path, *, repo_root: Path) -> tuple[dict[str, Any], tuple[dict[str, Any], ...]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LeanV2ContractError(f"cannot read lean-v2 source packet {path}: {exc}") from exc
    packet = dict(_mapping(payload, "$"))
    if packet.get("schema_version") != 1:
        raise LeanV2ContractError("$.schema_version must equal 1")
    for key in ("ft_slug", "scope_slug", "section_id", "package_id", "tc_prefix"):
        _single_line(packet.get(key), f"$.{key}")
    if re.fullmatch(r"[A-Z0-9][A-Z0-9-]{1,30}", str(packet["tc_prefix"])) is None:
        raise LeanV2ContractError("$.tc_prefix must match [A-Z0-9][A-Z0-9-]{1,30}")
    _string_list(packet.get("base_preconditions"), "$.base_preconditions", allow_empty=False)
    dictionaries = _list(packet.get("dictionaries", []), "$.dictionaries")
    dictionary_ids: set[str] = set()
    for index, raw in enumerate(dictionaries):
        item = _mapping(raw, f"$.dictionaries[{index}]")
        dictionary_id = _single_line(
            item.get("dictionary_id"), f"$.dictionaries[{index}].dictionary_id"
        )
        if dictionary_id in dictionary_ids:
            raise LeanV2ContractError(f"duplicate dictionary_id: {dictionary_id}")
        dictionary_ids.add(dictionary_id)
        _string_list(item.get("values"), f"$.dictionaries[{index}].values", allow_empty=False)
        if item.get("closed") is not True:
            raise LeanV2ContractError(
                f"$.dictionaries[{index}].closed must be true for deterministic use"
            )
    rows = _list(packet.get("source_rows"), "$.source_rows", allow_empty=False)
    row_ids: set[str] = set()
    obligation_ids: set[str] = set()
    atom_ids: set[str] = set()
    for row_index, raw_row in enumerate(rows):
        row = _mapping(raw_row, f"$.source_rows[{row_index}]")
        row_id = _single_line(
            row.get("source_row_id"), f"$.source_rows[{row_index}].source_row_id"
        )
        if row_id in row_ids:
            raise LeanV2ContractError(f"duplicate source_row_id: {row_id}")
        row_ids.add(row_id)
        for key in ("field_or_action", "source_ref", "source_locator"):
            _single_line(row.get(key), f"$.source_rows[{row_index}].{key}")
        _text(row.get("bounded_source_text"), f"$.source_rows[{row_index}].bounded_source_text")
        _string_list(row.get("requirement_codes", []), f"$.source_rows[{row_index}].requirement_codes")
        obligations = _list(
            row.get("obligations"),
            f"$.source_rows[{row_index}].obligations",
            allow_empty=False,
        )
        for obligation_index, raw_obligation in enumerate(obligations):
            base = f"$.source_rows[{row_index}].obligations[{obligation_index}]"
            obligation = _mapping(raw_obligation, base)
            obligation_id = _single_line(
                obligation.get("obligation_id"), f"{base}.obligation_id"
            )
            atom_id = _single_line(obligation.get("atom_id"), f"{base}.atom_id")
            if obligation_id in obligation_ids:
                raise LeanV2ContractError(f"duplicate obligation_id: {obligation_id}")
            if atom_id in atom_ids:
                raise LeanV2ContractError(f"duplicate atom_id: {atom_id}")
            obligation_ids.add(obligation_id)
            atom_ids.add(atom_id)
            template = _single_line(obligation.get("template"), f"{base}.template")
            if template not in TEMPLATE_KINDS:
                raise LeanV2ContractError(f"unsupported {base}.template: {template}")
            priority = _single_line(
                obligation.get("priority", "средний"), f"{base}.priority"
            )
            if priority.casefold() not in {"низкий", "средний", "высокий"}:
                raise LeanV2ContractError(f"unsupported {base}.priority: {priority}")
            inputs = _mapping(obligation.get("inputs", {}), f"{base}.inputs")
            if template == "dictionary":
                dictionary_id = _single_line(
                    inputs.get("dictionary_id"), f"{base}.inputs.dictionary_id"
                )
                if dictionary_id not in dictionary_ids:
                    raise LeanV2ContractError(
                        f"{base} references unknown dictionary_id {dictionary_id}"
                    )
            if template == "complex":
                _text(inputs.get("writer_context"), f"{base}.inputs.writer_context")
    source_files = validate_source_files(packet, repo_root=repo_root)
    return packet, source_files


def compile_evidence_cards(packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    counter = 1
    for row in packet["source_rows"]:
        for obligation in row["obligations"]:
            cards.append(
                {
                    "schema_version": 1,
                    "card_id": f"CARD-{counter:03d}",
                    "source_row_id": row["source_row_id"],
                    "field_or_action": row["field_or_action"],
                    "source_ref": row["source_ref"],
                    "source_locator": row["source_locator"],
                    "bounded_source_text": row["bounded_source_text"],
                    "requirement_codes": list(row.get("requirement_codes", [])),
                    "obligation_id": obligation["obligation_id"],
                    "atom_id": obligation["atom_id"],
                    "template": obligation["template"],
                    "priority": obligation.get("priority", "средний").casefold(),
                    "inputs": json.loads(json.dumps(obligation.get("inputs", {}), ensure_ascii=False)),
                }
            )
            counter += 1
    return cards


def assert_sources_unchanged(source_files: Sequence[Mapping[str, Any]]) -> None:
    for item in source_files:
        path = Path(str(item["resolved_path"]))
        actual = sha256_file(path)
        if actual != item["sha256"]:
            raise LeanV2ContractError(f"registered source changed during run: {path}")
