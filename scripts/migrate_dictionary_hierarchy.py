from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.review_cycle.prepared_compiler import markdown_tables  # noqa: E402
from test_case_agent.review_cycle.runtime import StageRuntimeError  # noqa: E402


COLUMNS = (
    "dictionary_id",
    "dictionary_name",
    "source_file",
    "source_location",
    "extraction_status",
    "active_values",
    "archived_values",
    "used_by_source_properties",
    "gap_id",
    "notes",
)


def _decode_codepoints(value: str) -> str:
    try:
        return "".join(chr(int(item, 16)) for item in value.split(","))
    except (ValueError, OverflowError) as exc:
        raise StageRuntimeError("parent name codepoints must be comma-separated hex values") from exc


def _render(rows: Sequence[dict[str, str]]) -> str:
    header = "| " + " | ".join(COLUMNS) + " |"
    separator = "| " + " | ".join("---" for _ in COLUMNS) + " |"
    body = [
        "| " + " | ".join(row[column] for column in COLUMNS) + " |"
        for row in rows
    ]
    return "# Dictionary Inventory\n\n" + "\n".join((header, separator, *body)) + "\n"


def _replace_all(value: str, replacements: dict[str, str]) -> str:
    for old_id, new_id in replacements.items():
        value = value.replace(old_id, new_id)
    return value


def migrate(
    *,
    inventory: Path,
    dictionary_id: str,
    parent_name: str,
    write: bool,
) -> dict[str, object]:
    inventory = inventory.resolve()
    if not inventory.is_file():
        raise StageRuntimeError(f"dictionary inventory is missing: {inventory}")
    tables = markdown_tables(inventory)
    table = next(
        (rows for rows in tables if rows and set(COLUMNS) <= set(rows[0])),
        None,
    )
    if table is None:
        raise StageRuntimeError("canonical dictionary inventory table is missing")
    identifier_match = re.fullmatch(r"DICT-(\d{3,})", dictionary_id)
    if identifier_match is None:
        raise StageRuntimeError("dictionary id must use canonical numeric DICT-NNN format")
    child_base = int(identifier_match.group(1)) * 100
    legacy_child_ids = [
        row["dictionary_id"]
        for row in table
        if row["dictionary_id"].startswith(
            (f"{dictionary_id}.CAT-", f"{dictionary_id}-CAT-")
        )
    ]
    legacy_replacements = {
        old_id: f"DICT-{child_base + index:03d}"
        for index, old_id in enumerate(legacy_child_ids, 1)
    }
    normalized_rows = [
        {
            key: _replace_all(value, legacy_replacements)
            for key, value in row.items()
        }
        for row in table
    ]
    formatting_changed = normalized_rows != table
    table = normalized_rows
    duplicates = [row for row in table if row["dictionary_id"] == dictionary_id]
    if len(duplicates) < 2:
        if write and formatting_changed:
            temporary = inventory.with_name(f".{inventory.name}.dictionary-hierarchy.tmp")
            if temporary.exists():
                raise StageRuntimeError(f"migration temporary file already exists: {temporary}")
            temporary.write_text(_render(table), encoding="utf-8")
            os.replace(temporary, inventory)
        return {
            "status": "normalized-child-ids" if formatting_changed else "already-current",
            "dictionary_id": dictionary_id,
            "duplicate_rows": len(duplicates),
            "write": write,
        }
    child_ids = [f"DICT-{child_base + index:03d}" for index in range(1, len(duplicates) + 1)]
    first = duplicates[0]
    parent = {
        "dictionary_id": dictionary_id,
        "dictionary_name": parent_name,
        "source_file": first["source_file"],
        "source_location": first["source_location"],
        "extraction_status": "extracted",
        "active_values": "; ".join(f"`{item}`" for item in child_ids),
        "archived_values": first["archived_values"],
        "used_by_source_properties": first["used_by_source_properties"],
        "gap_id": "none_required:covered",
        "notes": "Parent inventory row; child category rows preserve the complete source values.",
    }
    migrated: list[dict[str, str]] = []
    inserted_parent = False
    duplicate_index = 0
    for row in table:
        if row["dictionary_id"] != dictionary_id:
            migrated.append(dict(row))
            continue
        if not inserted_parent:
            migrated.append(parent)
            inserted_parent = True
        child = dict(row)
        child["dictionary_id"] = child_ids[duplicate_index]
        child["notes"] = (
            child["notes"].rstrip(".")
            + f". Child category of `{dictionary_id}`."
        )
        migrated.append(child)
        duplicate_index += 1
    rendered = _render(migrated)
    if write:
        temporary = inventory.with_name(f".{inventory.name}.dictionary-hierarchy.tmp")
        if temporary.exists():
            raise StageRuntimeError(f"migration temporary file already exists: {temporary}")
        temporary.write_text(rendered, encoding="utf-8")
        os.replace(temporary, inventory)
    return {
        "status": "migrated",
        "dictionary_id": dictionary_id,
        "child_ids": child_ids,
        "write": write,
        "rows": len(migrated),
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Split duplicate dictionary rows into a parent/child hierarchy")
    result.add_argument("--inventory", required=True)
    result.add_argument("--dictionary-id", required=True)
    result.add_argument("--parent-name-codepoints", required=True)
    result.add_argument("--write", action="store_true")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result = migrate(
            inventory=Path(args.inventory),
            dictionary_id=args.dictionary_id,
            parent_name=_decode_codepoints(args.parent_name_codepoints),
            write=args.write,
        )
    except (OSError, StageRuntimeError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
