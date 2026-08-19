from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    from scripts.runtime_io import configure_utf8_stdio
    from scripts.runtime_traceability import find_markdown_table
    from scripts.runtime_session_registry import find_package_root
    from scripts.validate_fixture_catalog import validate as validate_fixture_catalog
    from scripts.validate_runtime_matrix import REQUIRED_HEADERS
    from scripts.validate_runtime_scope import TEST_DATA_PLAN_HEADERS
except ModuleNotFoundError:  # Direct invocation
    from runtime_io import configure_utf8_stdio
    from runtime_traceability import find_markdown_table
    from runtime_session_registry import find_package_root
    from validate_fixture_catalog import validate as validate_fixture_catalog
    from validate_runtime_matrix import REQUIRED_HEADERS
    from validate_runtime_scope import TEST_DATA_PLAN_HEADERS


ROLE_RE = re.compile(r"(?<![A-Za-z0-9_.-])TD-[A-Z0-9.-]+(?![A-Za-z0-9_.-])")
RELATION_RE = re.compile(r"(?<![A-Za-z0-9_.-])REL-[A-Z0-9.-]+(?![A-Za-z0-9_.-])")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(
    r"(?:<[^>]+>|\[заполн|введите\s+значение|будет\s+подготовлен|требуется\s+получить|"
    r"валидн\w*\s+значени|несохран[её]нн\w*\s+значени|значени\w*\s+из\s+fixture)",
    re.IGNORECASE,
)
RUN_ID_RE = re.compile(r"\bRUN[-_ ]?ID\b|\{\{?\s*(?:timestamp|run[_-]?id)\s*\}?\}", re.IGNORECASE)
ALLOWED_SOURCE_TYPES = {"provider", "dictionary", "public", "synthetic", "environment", "primary", "approved-ba"}
SOURCE_COMPATIBILITY = {
    "provider": ("внешний сервис:", "сохранённый ответ", "сохраненный ответ"),
    "dictionary": ("проектный справочник",),
    "public": ("официальный публичный источник",),
    "synthetic": ("синтетический генератор",),
    "environment": ("стендовая подготовка",),
    "primary": ("первичный источник",),
    "approved-ba": ("утверждённый ответ ба", "утвержденный ответ ба"),
}


def scalar_values(value: Any) -> list[Any]:
    if isinstance(value, dict):
        return [item for child in value.values() for item in scalar_values(child)]
    if isinstance(value, list):
        return [item for child in value for item in scalar_values(child)]
    if value is None:
        return []
    return [value]


def matrix_data_usage(content: str) -> tuple[dict[str, set[str]], dict[str, set[str]], list[str]]:
    table = find_markdown_table(content, REQUIRED_HEADERS)
    if table is None or not table.rows:
        return {}, {}, ["materialization cannot be checked without executable matrix rows"]
    data_index = table.index("Тестовые данные и отношения")
    id_index = table.index("ID")
    decision_index = table.index("Решение")
    role_usage: dict[str, set[str]] = {}
    relation_usage: dict[str, set[str]] = {}
    for row in table.rows:
        if row[decision_index] != "TC":
            continue
        matrix_id = row[id_index].strip()
        for role in ROLE_RE.findall(row[data_index]):
            role_usage.setdefault(role, set()).add(matrix_id)
        for relation in RELATION_RE.findall(row[data_index]):
            relation_usage.setdefault(relation, set()).add(matrix_id)
    return role_usage, relation_usage, []


def plan_sources(content: str) -> tuple[dict[str, tuple[str, ...]], list[str]]:
    if re.search(r"(?m)^Данные не требуются\.\s*$", content) and "|" not in content:
        return {}, []
    table = find_markdown_table(content, TEST_DATA_PLAN_HEADERS)
    if table is None or not table.rows:
        return {}, ["test-data-plan has no logical data contract table"]
    role_index = table.index("Роли данных")
    source_index = table.index("Допустимый источник")
    result: dict[str, tuple[str, ...]] = {}
    errors: list[str] = []
    for row in table.rows:
        sources = tuple(part.strip().strip("`").casefold() for part in row[source_index].split(";") if part.strip())
        for role in ROLE_RE.findall(row[role_index]):
            if role in result:
                errors.append(f"test-data-plan declares {role} more than once")
            result[role] = sources
    return result, errors


def resolve_package_path(package_root: Path, value: str) -> Path | None:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (package_root / candidate).resolve()
    try:
        resolved.relative_to(package_root.resolve())
    except ValueError:
        return None
    return resolved


def operand_value(operand: str, bindings: dict[str, dict[str, Any]]) -> tuple[Any, str | None]:
    matching_roles = sorted(
        (role for role in bindings if operand.startswith(role + ".")),
        key=len,
        reverse=True,
    )
    if not matching_roles:
        return None, f"relation operand {operand!r} does not reference a materialized role field"
    role = matching_roles[0]
    field = operand[len(role) + 1 :]
    values = bindings[role].get("values")
    if not isinstance(values, dict) or field not in values:
        return None, f"relation operand {operand!r} is absent from binding values"
    return values[field], None


def validate(materialization_path: Path, matrix_path: Path, data_plan_path: Path) -> list[str]:
    errors: list[str] = []
    package_root = find_package_root(matrix_path)
    if package_root is None:
        return ["cannot locate FT package root for data materialization"]
    try:
        payload = json.loads(materialization_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"data materialization is not valid UTF-8 JSON: {exc}"]
    if not isinstance(payload, dict):
        return ["data materialization must be a JSON object"]

    matrix_content = matrix_path.read_text(encoding="utf-8")
    role_usage, relation_usage, usage_errors = matrix_data_usage(matrix_content)
    errors.extend(usage_errors)
    declared_sources, plan_errors = plan_sources(data_plan_path.read_text(encoding="utf-8"))
    errors.extend(plan_errors)

    scope = matrix_path.parent.name
    if payload.get("schema_version") != 1:
        errors.append("data materialization schema_version must be 1")
    if payload.get("scope") != scope:
        errors.append(f"data materialization scope must be {scope!r}")
    if payload.get("status") != "completed":
        errors.append("data materialization status must be 'completed'")
    try:
        expected_matrix = matrix_path.resolve().relative_to(package_root.resolve()).as_posix()
    except ValueError:
        return errors + ["matrix path escapes FT package"]
    if payload.get("matrix_path") != expected_matrix:
        errors.append(f"matrix_path must be {expected_matrix!r}")
    digest = payload.get("matrix_sha256")
    actual_digest = hashlib.sha256(matrix_path.read_bytes()).hexdigest()
    if not isinstance(digest, str) or not DIGEST_RE.fullmatch(digest) or digest.casefold() != actual_digest:
        errors.append("matrix_sha256 does not match the accepted matrix bytes")

    raw_bindings = payload.get("bindings")
    if not isinstance(raw_bindings, list):
        errors.append("bindings must be a list")
        raw_bindings = []
    bindings: dict[str, dict[str, Any]] = {}
    for index, binding in enumerate(raw_bindings, start=1):
        label = f"binding[{index}]"
        if not isinstance(binding, dict):
            errors.append(f"{label} must be an object")
            continue
        role = binding.get("role_id")
        if not isinstance(role, str) or ROLE_RE.fullmatch(role) is None:
            errors.append(f"{label}: invalid role_id")
            continue
        if role in bindings:
            errors.append(f"{label}: duplicate role_id {role}")
            continue
        bindings[role] = binding
        expected_used_by = sorted(role_usage.get(role, set()))
        if binding.get("used_by") != expected_used_by:
            errors.append(f"{role}: used_by must equal {expected_used_by}")
        source_type = binding.get("source_type")
        if source_type not in ALLOWED_SOURCE_TYPES:
            errors.append(f"{role}: unsupported source_type {source_type!r}")
        sources = declared_sources.get(role)
        if sources is None:
            errors.append(f"{role}: role is absent from test-data-plan")
        elif source_type in SOURCE_COMPATIBILITY and not any(
            source.startswith(prefix) for source in sources for prefix in SOURCE_COMPATIBILITY[source_type]
        ):
            errors.append(f"{role}: source_type {source_type!r} is incompatible with test-data-plan {sources}")
        if not isinstance(binding.get("source_name"), str) or not binding["source_name"].strip():
            errors.append(f"{role}: source_name is required")
        values = binding.get("values")
        if not isinstance(values, dict) or not values:
            errors.append(f"{role}: values must be a non-empty object")
            continue
        for field, value in values.items():
            if not isinstance(field, str) or not field.strip() or isinstance(value, (dict, list)) or value is None:
                errors.append(f"{role}: every materialized field must be a non-empty scalar")
                continue
            text = str(value)
            if not text.strip() or PLACEHOLDER_RE.search(text):
                errors.append(f"{role}.{field}: unresolved placeholder is forbidden")
            if source_type in {"provider", "dictionary"} and RUN_ID_RE.search(text):
                errors.append(f"{role}.{field}: RUN-ID/timestamp is forbidden for {source_type}-bound data")

    for role in sorted(set(role_usage) - set(bindings)):
        errors.append(f"matrix data role {role} has no materialized binding")
    for role in sorted(set(bindings) - set(role_usage)):
        errors.append(f"materialized binding {role} is not used by executable matrix rows")

    provider_bindings = [binding for binding in bindings.values() if binding.get("source_type") == "provider"]
    catalog: dict[str, Any] | None = None
    if provider_bindings:
        catalog_relative = payload.get("fixture_catalog")
        if not isinstance(catalog_relative, str):
            errors.append("fixture_catalog is required for provider bindings")
        else:
            catalog_path = resolve_package_path(package_root, catalog_relative)
            if catalog_path is None or not catalog_path.is_file():
                errors.append("fixture_catalog path is invalid or missing")
            else:
                errors.extend(validate_fixture_catalog(catalog_path))
                try:
                    loaded = json.loads(catalog_path.read_text(encoding="utf-8"))
                    if isinstance(loaded, dict):
                        catalog = loaded
                except (OSError, json.JSONDecodeError):
                    catalog = None
    catalog_by_id = {
        item.get("fixture_id"): item
        for item in (catalog or {}).get("fixtures", [])
        if isinstance(item, dict) and isinstance(item.get("fixture_id"), str)
    }
    for binding in provider_bindings:
        role = str(binding.get("role_id"))
        fixture_id = binding.get("fixture_id")
        fixture = catalog_by_id.get(fixture_id)
        if fixture is None:
            errors.append(f"{role}: provider binding requires an existing fixture_id")
            continue
        provider_values = {str(value) for value in scalar_values(fixture.get("runtime_data", {}))}
        missing = sorted(
            str(value)
            for value in (binding.get("values") or {}).values()
            if str(value) not in provider_values
        )
        if missing:
            errors.append(f"{role}: materialized values are absent from provider fixture: {missing}")

    raw_relations = payload.get("relations", [])
    if not isinstance(raw_relations, list):
        errors.append("relations must be a list")
        raw_relations = []
    relations: set[str] = set()
    for index, relation in enumerate(raw_relations, start=1):
        label = f"relation[{index}]"
        if not isinstance(relation, dict):
            errors.append(f"{label} must be an object")
            continue
        relation_id = relation.get("id")
        if not isinstance(relation_id, str) or RELATION_RE.fullmatch(relation_id) is None:
            errors.append(f"{label}: invalid relation id")
            continue
        if relation_id in relations:
            errors.append(f"{label}: duplicate relation {relation_id}")
            continue
        relations.add(relation_id)
        expected_used_by = sorted(relation_usage.get(relation_id, set()))
        if relation.get("used_by") != expected_used_by:
            errors.append(f"{relation_id}: used_by must equal {expected_used_by}")
        operator = relation.get("operator")
        if operator not in {"equal", "not-equal"}:
            errors.append(f"{relation_id}: operator must be equal or not-equal")
            continue
        left, left_error = operand_value(str(relation.get("left", "")), bindings)
        right, right_error = operand_value(str(relation.get("right", "")), bindings)
        if left_error:
            errors.append(f"{relation_id}: {left_error}")
        if right_error:
            errors.append(f"{relation_id}: {right_error}")
        if left_error or right_error:
            continue
        if operator == "equal" and left != right:
            errors.append(f"{relation_id}: equal relation is false")
        if operator == "not-equal" and left == right:
            errors.append(f"{relation_id}: not-equal relation is false")
    for relation in sorted(set(relation_usage) - relations):
        errors.append(f"matrix relation {relation} has no materialized relation")
    for relation in sorted(relations - set(relation_usage)):
        errors.append(f"materialized relation {relation} is not used by executable matrix rows")
    return errors


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Validate post-matrix runtime test-data materialization.")
    parser.add_argument("materialization", type=Path)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--data-plan", type=Path, required=True)
    args = parser.parse_args()
    errors = validate(args.materialization.resolve(), args.matrix.resolve(), args.data_plan.resolve())
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
