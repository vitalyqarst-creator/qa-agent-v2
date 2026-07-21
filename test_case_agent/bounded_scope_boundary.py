from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


CANONICAL_GAP_TYPES = (
    "ambiguity",
    "missing-rule",
    "cross-ft-dependency",
    "missing-constraint",
    "missing-source-definition",
    "missing-observation-interface",
    "unconfirmed-shared-behavior",
    "undeclared-field-reference",
    "missing-dictionary-values",
)

BOUNDARY_ROOT_FIELDS = {
    "version",
    "status",
    "blocking_reason",
    "scope_summary",
    "scope_boundary",
    "source_decisions",
    "dependencies",
    "gaps",
    "mockup_locators",
}
SCOPE_BOUNDARY_FIELDS = {"target", "include", "exclude"}
SOURCE_DECISION_FIELDS = {
    "source_row_id",
    "disposition",
    "requirement_codes",
    "rationale",
}
DEPENDENCY_FIELDS = {
    "dependency_id",
    "kind",
    "name",
    "source_row_ids",
    "resolution",
    "target_source_row_ids",
    "exact_source_fragments",
    "gap_ids",
    "blocking",
    "rationale",
}
GAP_FIELDS = {
    "gap_id",
    "gap_type",
    "source_row_ids",
    "source_refs",
    "exact_source_fragments",
    "blocking",
    "clarification_question",
    "downstream_handling",
}
DEPENDENCY_KINDS = {
    "field",
    "dictionary",
    "external-requirement",
    "integration",
    "other",
}
DEPENDENCY_RESOLUTIONS = {
    "declared",
    "approved-alias",
    "source-provided",
    "external-dynamic",
    "scope-excluded",
    "missing",
}
EXTERNAL_DICTIONARY_BINDING_FIELDS = {
    "dictionary_name",
    "binding_type",
    "provider",
    "reference_path",
    "reference_url",
    "source_row_ids",
    "query_parameters",
    "authority",
    "authority_ref",
}
EXPECTED_DEPENDENCY_FIELDS = {
    "kind",
    "name",
    "source_row_ids",
    "resolution",
    "target_source_row_ids",
    "exact_source_fragments",
}
GAP_HANDLING = {"block-writer", "carry-to-source-model", "none-required"}


class BoundedScopeBoundaryError(ValueError):
    """A fail-closed v2 boundary/context contract violation."""


_WINDOWS_RESERVED_SEGMENTS = {
    "aux",
    "con",
    "nul",
    "prn",
    *(f"com{index}" for index in range(1, 10)),
    *(f"lpt{index}" for index in range(1, 10)),
}


def is_global_type_definition_row(row: Mapping[str, Any]) -> bool:
    """Return whether a row is a document-global data-type definition.

    These rows use generic examples such as ``field \"Date\"`` to describe
    type-wide behavior.  The example is not a reference to a concrete UI field
    that must be declared in the selected scope.
    """

    return (
        str(row.get("source_context_class", "")).strip()
        == "document-global-constraints"
        and str(row.get("field_or_action", ""))
        .strip()
        .casefold()
        .startswith("ограничение типа ")
    )


def _exact_fields(
    payload: Mapping[str, Any],
    expected: set[str],
    *,
    label: str,
) -> None:
    if not isinstance(payload, Mapping):
        raise BoundedScopeBoundaryError(f"{label} must be an object")
    actual = set(payload)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing or unknown:
        raise BoundedScopeBoundaryError(
            f"{label} fields mismatch: missing={missing or 'none'}, "
            f"unknown={unknown or 'none'}"
        )


def _nonempty_text(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BoundedScopeBoundaryError(f"{label} must be non-empty text")
    return value


def validate_stable_path_segment(value: Any, *, label: str) -> str:
    """Return one exact cross-platform-safe path segment or fail closed."""

    segment = _nonempty_text(value, label=label)
    if segment != segment.strip():
        raise BoundedScopeBoundaryError(
            f"{label} must not have leading or trailing whitespace"
        )
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", segment) is None:
        raise BoundedScopeBoundaryError(
            f"{label} must be one stable ASCII slug segment"
        )
    if segment.endswith((".", " ")) or any(ord(character) < 32 for character in segment):
        raise BoundedScopeBoundaryError(
            f"{label} contains an unstable path character"
        )
    if segment.split(".", 1)[0].casefold() in _WINDOWS_RESERVED_SEGMENTS:
        raise BoundedScopeBoundaryError(
            f"{label} is a platform-reserved path segment"
        )
    return segment


def validate_publication_owner_token(value: Any, *, label: str) -> str:
    """Return one exact per-invocation ownership token or fail closed."""

    token = _nonempty_text(value, label=label)
    if token != token.strip() or re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        token,
    ) is None:
        raise BoundedScopeBoundaryError(
            f"{label} must be an exact lowercase UUIDv4 token"
        )
    return token


def _string_array(
    value: Any,
    *,
    label: str,
    nonempty: bool = False,
    unique: bool = False,
) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise BoundedScopeBoundaryError(f"{label} must be a string array")
    if nonempty and not value:
        raise BoundedScopeBoundaryError(f"{label} must be non-empty")
    if any(not item.strip() for item in value):
        raise BoundedScopeBoundaryError(f"{label} values must be non-empty text")
    if unique and len(value) != len(set(value)):
        raise BoundedScopeBoundaryError(f"{label} values must be unique")
    return value


def _in_scope_membership(value: str, *, label: str) -> str:
    hint = value.strip().casefold()
    match = re.match(r"^(yes|no)(?:$|\s*;)", hint)
    if match is None:
        raise BoundedScopeBoundaryError(
            f"{label} must authoritatively start with the yes/no token"
        )
    return match.group(1)


def normalize_entity(value: str) -> str:
    value = value.casefold().replace("ё", "е")
    value = re.sub(r"[^0-9a-zа-я]+", " ", value)
    return " ".join(value.split())


def declared_dictionary_values(context: Mapping[str, Any]) -> set[str]:
    declared: set[str] = set()
    raw = context.get("dictionary_inventory")
    if isinstance(raw, Mapping):
        for name, values in raw.items():
            if (
                isinstance(name, str)
                and isinstance(values, Sequence)
                and not isinstance(values, str)
                and values
            ):
                declared.add(normalize_entity(name))
    elif isinstance(raw, list):
        for item in raw:
            if not isinstance(item, Mapping):
                continue
            name = item.get("name") or item.get("dictionary_name")
            values = item.get("values")
            if isinstance(name, str) and isinstance(values, list) and values:
                declared.add(normalize_entity(name))
    return declared


def external_dynamic_dictionary_bindings(
    context: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Return validated hash-bound external dynamic dictionary bindings.

    The binding is deliberately separate from ``dictionary_inventory``: it
    proves where live values come from without pretending that a changing
    external directory is a closed inline value set.
    """

    raw = context.get("external_dictionary_bindings", [])
    if not isinstance(raw, list):
        raise BoundedScopeBoundaryError(
            "context.external_dictionary_bindings must be an array"
        )
    known_rows = {
        str(item.get("source_row_id", ""))
        for item in context.get("source_rows", [])
        if isinstance(item, Mapping)
    }
    registered_references = {
        str(item.get("path", ""))
        for item in context.get("sources", [])
        if isinstance(item, Mapping)
        and item.get("role") == "external-vendor-reference"
        and item.get("manifest_binding") == "supporting-material"
    }
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(raw):
        label = f"context.external_dictionary_bindings[{index}]"
        if not isinstance(item, Mapping):
            raise BoundedScopeBoundaryError(f"{label} must be an object")
        _exact_fields(item, EXTERNAL_DICTIONARY_BINDING_FIELDS, label=label)
        name = _nonempty_text(
            item.get("dictionary_name"), label=f"{label}.dictionary_name"
        )
        normalized_name = normalize_entity(name)
        if normalized_name in result:
            raise BoundedScopeBoundaryError(
                "external dynamic dictionary names must be unique"
            )
        if item.get("binding_type") != "external-dynamic-dictionary":
            raise BoundedScopeBoundaryError(
                f"{label}.binding_type must equal external-dynamic-dictionary"
            )
        _nonempty_text(item.get("provider"), label=f"{label}.provider")
        reference_path = _nonempty_text(
            item.get("reference_path"), label=f"{label}.reference_path"
        )
        if reference_path not in registered_references:
            raise BoundedScopeBoundaryError(
                f"{label}.reference_path must be a registered external-vendor-reference"
            )
        reference_url = _nonempty_text(
            item.get("reference_url"), label=f"{label}.reference_url"
        )
        if re.fullmatch(r"https://[^\s]+", reference_url) is None:
            raise BoundedScopeBoundaryError(
                f"{label}.reference_url must be an HTTPS URL"
            )
        source_row_ids = _string_array(
            item.get("source_row_ids"),
            label=f"{label}.source_row_ids",
            nonempty=True,
            unique=True,
        )
        if set(source_row_ids) - known_rows:
            raise BoundedScopeBoundaryError(
                f"{label}.source_row_ids reference unknown rows"
            )
        parameters = item.get("query_parameters")
        if not isinstance(parameters, Mapping) or not parameters:
            raise BoundedScopeBoundaryError(
                f"{label}.query_parameters must be a non-empty object"
            )
        if any(
            not isinstance(key, str)
            or not key.strip()
            or not isinstance(value, str)
            or not value.strip()
            for key, value in parameters.items()
        ):
            raise BoundedScopeBoundaryError(
                f"{label}.query_parameters must map non-empty strings"
            )
        if item.get("authority") != "user-confirmed":
            raise BoundedScopeBoundaryError(
                f"{label}.authority must equal user-confirmed"
            )
        authority_ref = _nonempty_text(
            item.get("authority_ref"), label=f"{label}.authority_ref"
        )
        if re.fullmatch(r"CLR-[A-Z0-9-]+", authority_ref) is None:
            raise BoundedScopeBoundaryError(
                f"{label}.authority_ref must be a stable CLR-* identifier"
            )
        result[normalized_name] = copy.deepcopy(dict(item))
    return result


def dictionary_has_inline_values(name: str, source_texts: Sequence[str]) -> bool:
    escaped = re.escape(name)
    patterns = (
        rf"справочник(?:а|у|ом|е)?\s+[«\"]{escaped}[»\"]\s*:\s*(.+?)(?=\bBSR\s+\d+|$)",
        rf"(?:по\s+)?справочнику\s+{escaped}\s*:\s*(.+?)(?=\bBSR\s+\d+|$)",
    )
    for text in source_texts:
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match and len(match.group(1).strip(" -;,.")) >= 2:
                return True
    return False


def recompute_bounded_context_sha256(context: Mapping[str, Any]) -> str:
    payload = copy.deepcopy(dict(context))
    payload.pop("source_cache", None)
    payload.pop("source_row_baseline", None)
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def validate_source_cache_binding(
    context: Mapping[str, Any],
    *,
    required: bool = True,
) -> None:
    source_cache = context.get("source_cache")
    if source_cache is None:
        if required:
            raise BoundedScopeBoundaryError(
                "context.source_cache is required for a production prepared context"
            )
        return
    if not isinstance(source_cache, Mapping):
        raise BoundedScopeBoundaryError("context.source_cache must be an object")
    components = source_cache.get("component_digests")
    if not isinstance(components, Mapping):
        raise BoundedScopeBoundaryError(
            "context.source_cache.component_digests must be an object"
        )
    expected = components.get("bounded_context_sha256")
    if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
        raise BoundedScopeBoundaryError(
            "bounded_context_sha256 must be a lowercase SHA-256 in source_cache"
        )
    if recompute_bounded_context_sha256(context) != expected:
        raise BoundedScopeBoundaryError(
            "prepared context bounded_context_sha256 mismatch"
        )


def expected_dependency_inventory(
    context: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows = [
        item for item in context.get("source_rows", []) if isinstance(item, Mapping)
    ]
    inventory: dict[tuple[str, str], dict[str, Any]] = {}

    def register(*, kind: str, name: str, row_id: str, fragment: str) -> None:
        key = (kind, normalize_entity(name))
        entry = inventory.setdefault(
            key,
            {
                "kind": kind,
                "name": name,
                "source_row_ids": [],
                "exact_source_fragments": [],
            },
        )
        if row_id not in entry["source_row_ids"]:
            entry["source_row_ids"].append(row_id)
        if fragment not in entry["exact_source_fragments"]:
            entry["exact_source_fragments"].append(fragment)

    patterns = (
        (
            "field",
            re.compile(r"\bпол(?:е|я|ем)\s+[«\"]([^»\"]+)[»\"]", re.IGNORECASE),
            lambda match: match.group(1).strip(),
        ),
        (
            "dictionary",
            re.compile(
                r"справочник(?:а|у|ом|е)?\s+[«\"]([^»\"]+)[»\"]",
                re.IGNORECASE,
            ),
            lambda match: match.group(1).strip(),
        ),
        (
            "external-requirement",
            re.compile(r"\bФТ\s+[«\"]([^»\"]+)[»\"]", re.IGNORECASE),
            lambda match: match.group(0).strip(),
        ),
    )
    for row in rows:
        row_id = str(row.get("source_row_id", ""))
        text = str(row.get("bounded_source_text", ""))
        skip_generic_type_field = is_global_type_definition_row(row)
        for kind, pattern, name_from_match in patterns:
            if kind == "field" and skip_generic_type_field:
                continue
            for match in pattern.finditer(text):
                register(
                    kind=kind,
                    name=name_from_match(match),
                    row_id=row_id,
                    fragment=match.group(0),
                )

    explicit = context.get("expected_dependencies", [])
    if not isinstance(explicit, list):
        raise BoundedScopeBoundaryError(
            "context.expected_dependencies must be an array"
        )
    known_rows = {str(item.get("source_row_id")) for item in rows}
    for index, item in enumerate(explicit):
        if not isinstance(item, Mapping):
            raise BoundedScopeBoundaryError(
                f"context.expected_dependencies[{index}] must be an object"
            )
        _exact_fields(
            item,
            EXPECTED_DEPENDENCY_FIELDS,
            label=f"context.expected_dependencies[{index}]",
        )
        kind = item.get("kind")
        name = item.get("name")
        linked = item.get("source_row_ids")
        resolution = item.get("resolution")
        targets = item.get("target_source_row_ids")
        fragments = item.get("exact_source_fragments")
        if kind not in DEPENDENCY_KINDS:
            raise BoundedScopeBoundaryError(
                f"invalid expected dependency kind at index {index}"
            )
        _nonempty_text(name, label=f"expected dependency {index}.name")
        if resolution not in DEPENDENCY_RESOLUTIONS:
            raise BoundedScopeBoundaryError(
                f"invalid expected dependency resolution at index {index}"
            )
        if (
            not isinstance(linked, list)
            or not linked
            or any(not isinstance(row_id, str) for row_id in linked)
            or set(linked) - known_rows
        ):
            raise BoundedScopeBoundaryError(
                f"expected dependency {index} links unknown rows"
            )
        if (
            not isinstance(fragments, list)
            or not fragments
            or any(not isinstance(fragment, str) for fragment in fragments)
        ):
            raise BoundedScopeBoundaryError(
                f"expected dependency {index} needs source fragments"
            )
        if (
            not isinstance(targets, list)
            or any(not isinstance(row_id, str) for row_id in targets)
            or len(targets) != len(set(targets))
            or set(targets) - known_rows
        ):
            raise BoundedScopeBoundaryError(
                f"expected dependency {index} has invalid target rows"
            )
        for row_id in linked:
            row_text = next(
                str(row.get("bounded_source_text", ""))
                for row in rows
                if str(row.get("source_row_id")) == row_id
            )
            for fragment in fragments:
                if not fragment or fragment not in row_text:
                    raise BoundedScopeBoundaryError(
                        f"expected dependency {index} fragment is not literal row text"
                    )
                register(
                    kind=str(kind),
                    name=str(name).strip(),
                    row_id=row_id,
                    fragment=fragment,
                )
        key = (str(kind), normalize_entity(str(name)))
        entry = inventory[key]
        expected_resolution = entry.get("resolution")
        expected_targets = entry.get("target_source_row_ids")
        if expected_resolution is not None and expected_resolution != resolution:
            raise BoundedScopeBoundaryError(
                f"expected dependency {index} conflicts with an earlier resolution"
            )
        if expected_targets is not None and expected_targets != list(targets):
            raise BoundedScopeBoundaryError(
                f"expected dependency {index} conflicts with earlier target rows"
            )
        entry["resolution"] = resolution
        entry["target_source_row_ids"] = list(targets)
    return list(inventory.values())


def validate_bounded_scope_context(
    context: Mapping[str, Any],
    *,
    require_source_cache: bool = True,
) -> None:
    if not isinstance(context, Mapping):
        raise BoundedScopeBoundaryError("context must be an object")
    if "ft_slug" in context:
        validate_stable_path_segment(context.get("ft_slug"), label="context.ft_slug")
    rows = context.get("source_rows")
    if not isinstance(rows, list) or not rows:
        raise BoundedScopeBoundaryError(
            "context.source_rows must be a non-empty array"
        )
    row_ids: list[str] = []
    for index, item in enumerate(rows):
        if not isinstance(item, Mapping):
            raise BoundedScopeBoundaryError(
                f"context.source_rows[{index}] must be an object"
            )
        row_id = _nonempty_text(
            item.get("source_row_id"),
            label=f"context.source_rows[{index}].source_row_id",
        )
        row_ids.append(row_id)
        for key in ("source_ref", "bounded_source_text", "in_scope_hint"):
            _nonempty_text(item.get(key), label=f"{row_id}.{key}")
        _in_scope_membership(
            str(item["in_scope_hint"]),
            label=f"{row_id}.in_scope_hint",
        )
        _string_array(
            item.get("requirement_codes_hint", []),
            label=f"{row_id}.requirement_codes_hint",
            unique=True,
        )
        if "context_relation_required" in item and type(
            item.get("context_relation_required")
        ) is not bool:
            raise BoundedScopeBoundaryError(
                f"{row_id}.context_relation_required must be boolean"
            )
    if len(row_ids) != len(set(row_ids)):
        raise BoundedScopeBoundaryError(
            "context source_row_id values must be unique"
        )

    boundary = context.get("scope_boundary")
    if not isinstance(boundary, Mapping):
        raise BoundedScopeBoundaryError("context.scope_boundary must be an object")
    _exact_fields(boundary, SCOPE_BOUNDARY_FIELDS, label="context.scope_boundary")
    _nonempty_text(
        boundary.get("target"),
        label="context.scope_boundary.target",
    )
    for key in ("include", "exclude"):
        _string_array(
            boundary.get(key),
            label=f"context.scope_boundary.{key}",
        )
    _string_array(
        context.get("mockup_locators", []),
        label="context.mockup_locators",
        unique=True,
    )
    validate_source_cache_binding(context, required=require_source_cache)
    dependency_inventory = expected_dependency_inventory(context)
    external_bindings = external_dynamic_dictionary_bindings(context)
    external_dependencies = {
        normalize_entity(str(item["name"])): item
        for item in dependency_inventory
        if item.get("kind") == "dictionary"
        and item.get("resolution") == "external-dynamic"
    }
    if set(external_bindings) != set(external_dependencies):
        raise BoundedScopeBoundaryError(
            "external_dictionary_bindings must match external-dynamic "
            "dictionary dependencies exactly"
        )
    for name, binding in external_bindings.items():
        dependency = external_dependencies[name]
        if binding["source_row_ids"] != dependency["source_row_ids"]:
            raise BoundedScopeBoundaryError(
                "external dynamic dictionary source_row_ids must match its dependency"
            )
    required_relation_rows = {
        str(item["source_row_id"])
        for item in rows
        if item.get("context_relation_required") is True
    }
    bound_relation_rows = {
        str(row_id)
        for dependency in dependency_inventory
        if dependency.get("resolution") != "scope-excluded"
        and dependency.get("target_source_row_ids")
        for row_id in dependency.get("source_row_ids", [])
    }
    if not required_relation_rows.issubset(bound_relation_rows):
        raise BoundedScopeBoundaryError(
            "context_relation_required rows need explicit non-excluded "
            "dependencies with target_source_row_ids: "
            + ", ".join(sorted(required_relation_rows - bound_relation_rows))
        )


def validate_boundary_decision_v2(
    context: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> None:
    """Validate one boundary-v2 decision against its immutable prepared context."""

    validate_bounded_scope_context(context, require_source_cache=True)
    _exact_fields(payload, BOUNDARY_ROOT_FIELDS, label="scope boundary decision")
    if type(payload.get("version")) is not int or payload.get("version") != 2:
        raise BoundedScopeBoundaryError(
            "scope-only decision.version must equal 2"
        )

    raw_rows = context["source_rows"]
    source_rows = {str(item["source_row_id"]): item for item in raw_rows}
    expected_boundary = context["scope_boundary"]
    returned_boundary = payload.get("scope_boundary")
    if not isinstance(returned_boundary, Mapping):
        raise BoundedScopeBoundaryError("scope_boundary must be an object")
    _exact_fields(
        returned_boundary,
        SCOPE_BOUNDARY_FIELDS,
        label="scope boundary decision.scope_boundary",
    )
    if returned_boundary != expected_boundary:
        raise BoundedScopeBoundaryError(
            "scope_boundary must match bounded context exactly"
        )
    _nonempty_text(payload.get("scope_summary"), label="scope_summary")

    decisions = payload.get("source_decisions")
    if not isinstance(decisions, list):
        raise BoundedScopeBoundaryError("source_decisions must be an array")
    decision_ids: list[str] = []
    for index, decision in enumerate(decisions):
        if not isinstance(decision, Mapping):
            raise BoundedScopeBoundaryError(
                f"source_decisions[{index}] must be an object"
            )
        _exact_fields(
            decision,
            SOURCE_DECISION_FIELDS,
            label=f"source_decisions[{index}]",
        )
        decision_ids.append(
            _nonempty_text(
                decision.get("source_row_id"),
                label=f"source_decisions[{index}].source_row_id",
            )
        )
    if decision_ids != list(source_rows):
        raise BoundedScopeBoundaryError(
            "source_decisions must account for every source row exactly once in input order"
        )
    for index, decision in enumerate(decisions):
        assert isinstance(decision, Mapping)
        row_id = str(decision["source_row_id"])
        disposition = decision.get("disposition")
        if disposition not in {"included", "context", "excluded"}:
            raise BoundedScopeBoundaryError(f"invalid disposition for {row_id}")
        membership = _in_scope_membership(
            str(source_rows[row_id]["in_scope_hint"]),
            label=f"{row_id}.in_scope_hint",
        )
        if membership == "yes" and disposition != "included":
            raise BoundedScopeBoundaryError(
                f"{row_id} with yes in_scope_hint must be included"
            )
        if membership == "no" and disposition == "included":
            raise BoundedScopeBoundaryError(
                f"{row_id} with no in_scope_hint cannot be included"
            )
        if (
            source_rows[row_id].get("context_relation_required") is True
            and disposition != "context"
        ):
            raise BoundedScopeBoundaryError(
                f"{row_id} with context_relation_required must be context"
            )
        _nonempty_text(decision.get("rationale"), label=f"{row_id}.rationale")
        expected_codes = source_rows[row_id].get("requirement_codes_hint", [])
        if decision.get("requirement_codes") != expected_codes:
            raise BoundedScopeBoundaryError(
                f"{row_id} requirement_codes must match requirement_codes_hint exactly"
            )

    dependencies = payload.get("dependencies")
    if not isinstance(dependencies, list):
        raise BoundedScopeBoundaryError("dependencies must be an array")
    dependency_ids: list[str] = []
    for index, item in enumerate(dependencies):
        if not isinstance(item, Mapping):
            raise BoundedScopeBoundaryError("dependencies entries must be objects")
        _exact_fields(item, DEPENDENCY_FIELDS, label=f"dependencies[{index}]")
        dependency_ids.append(
            _nonempty_text(
                item.get("dependency_id"),
                label=f"dependencies[{index}].dependency_id",
            )
        )
    if len(dependency_ids) != len(set(dependency_ids)):
        raise BoundedScopeBoundaryError(
            "dependency_id values must be non-empty and unique"
        )

    expected_dependencies = {
        (str(item["kind"]), normalize_entity(str(item["name"]))): item
        for item in expected_dependency_inventory(context)
    }
    seen_dependency_keys: set[tuple[str, str]] = set()
    declared_fields_by_name: dict[str, set[str]] = {}
    for row_id, row in source_rows.items():
        name = normalize_entity(str(row.get("field_or_action", "")))
        if name:
            declared_fields_by_name.setdefault(name, set()).add(row_id)
    aliases = context.get("dependency_aliases", {})
    if not isinstance(aliases, Mapping):
        raise BoundedScopeBoundaryError(
            "context.dependency_aliases must be an object"
        )
    normalized_aliases: dict[str, str] = {}
    for name, target in aliases.items():
        if (
            not isinstance(name, str)
            or not name.strip()
            or not isinstance(target, str)
            or not target.strip()
        ):
            raise BoundedScopeBoundaryError(
                "context.dependency_aliases must map non-empty strings"
            )
        normalized_aliases[normalize_entity(name)] = normalize_entity(target)
    declared_dictionaries = declared_dictionary_values(context)
    external_dictionaries = external_dynamic_dictionary_bindings(context)
    exclusions = [
        normalize_entity(value) for value in expected_boundary["exclude"]
    ]
    dependency_gap_ids: set[str] = set()
    resolved_dependency_gap_ids: dict[str, set[str]] = {}
    missing_blocking_dependency = False
    for index, item in enumerate(dependencies):
        assert isinstance(item, Mapping)
        kind = item.get("kind")
        if kind not in DEPENDENCY_KINDS:
            raise BoundedScopeBoundaryError(
                f"dependencies[{index}].kind is invalid"
            )
        name = _nonempty_text(
            item.get("name"), label=f"dependencies[{index}].name"
        )
        _nonempty_text(
            item.get("rationale"), label=f"dependencies[{index}].rationale"
        )
        dependency_key = (str(kind), normalize_entity(name))
        if dependency_key in seen_dependency_keys:
            raise BoundedScopeBoundaryError("semantic dependencies must be unique")
        seen_dependency_keys.add(dependency_key)
        expected_dependency = expected_dependencies.get(dependency_key)
        if expected_dependency is None:
            raise BoundedScopeBoundaryError(
                "decision contains an undeclared dependency"
            )

        linked = _string_array(
            item.get("source_row_ids"),
            label=f"dependencies[{index}].source_row_ids",
            nonempty=True,
            unique=True,
        )
        targets = _string_array(
            item.get("target_source_row_ids"),
            label=f"dependencies[{index}].target_source_row_ids",
            unique=True,
        )
        fragments = _string_array(
            item.get("exact_source_fragments"),
            label=f"dependencies[{index}].exact_source_fragments",
            nonempty=True,
            unique=True,
        )
        linked_gaps = _string_array(
            item.get("gap_ids"),
            label=f"dependencies[{index}].gap_ids",
            unique=True,
        )
        if set(linked) - set(source_rows):
            raise BoundedScopeBoundaryError(
                "dependency source_row_ids must link known rows"
            )
        if set(linked) != set(expected_dependency["source_row_ids"]):
            raise BoundedScopeBoundaryError(
                "dependency source_row_ids must match expected inventory"
            )
        if set(targets) - set(source_rows):
            raise BoundedScopeBoundaryError(
                "dependency target_source_row_ids must link known rows"
            )
        linked_texts = [
            str(source_rows[row_id].get("bounded_source_text", ""))
            for row_id in linked
        ]
        if any(
            not any(fragment in source_text for source_text in linked_texts)
            for fragment in fragments
        ):
            raise BoundedScopeBoundaryError(
                "dependency evidence must be literal linked-row text"
            )
        if any(
            not any(str(expected) in returned for returned in fragments)
            for expected in expected_dependency["exact_source_fragments"]
        ):
            raise BoundedScopeBoundaryError(
                "dependency evidence must cover expected inventory fragments"
            )
        dependency_gap_ids.update(linked_gaps)
        resolution = item.get("resolution")
        if resolution not in DEPENDENCY_RESOLUTIONS:
            raise BoundedScopeBoundaryError("dependency resolution is invalid")
        expected_resolution = expected_dependency.get("resolution")
        if expected_resolution is not None and resolution != expected_resolution:
            raise BoundedScopeBoundaryError(
                f"{item['dependency_id']} resolution must match expected inventory"
            )
        expected_targets = expected_dependency.get("target_source_row_ids")
        if expected_targets is not None and targets != expected_targets:
            raise BoundedScopeBoundaryError(
                f"{item['dependency_id']} target_source_row_ids must match "
                "expected inventory"
            )
        if type(item.get("blocking")) is not bool:
            raise BoundedScopeBoundaryError("dependency blocking must be boolean")
        is_missing = resolution == "missing"
        if is_missing != (item.get("blocking") is True):
            raise BoundedScopeBoundaryError(
                "only missing dependencies may be blocking"
            )
        if is_missing and not linked_gaps:
            raise BoundedScopeBoundaryError(
                "missing dependency must link a blocking gap"
            )
        if not is_missing and linked_gaps:
            resolved_dependency_gap_ids[str(item["dependency_id"])] = set(
                linked_gaps
            )

        normalized_name = dependency_key[1]
        target_ids = set(targets)
        if resolution == "declared":
            if not target_ids or not target_ids.issubset(
                declared_fields_by_name.get(normalized_name, set())
            ):
                raise BoundedScopeBoundaryError(
                    f"{item['dependency_id']} declared dependency {name!r} must "
                    f"target matching source rows; targets={targets}"
                )
        elif resolution == "approved-alias":
            alias_target = normalized_aliases.get(normalized_name)
            if not alias_target or not target_ids or not target_ids.issubset(
                declared_fields_by_name.get(alias_target, set())
            ):
                raise BoundedScopeBoundaryError(
                    "approved-alias dependency lacks an approved target"
                )
        elif resolution == "source-provided":
            if kind == "field":
                raise BoundedScopeBoundaryError(
                    f"{item['dependency_id']} field dependency cannot use "
                    "source-provided resolution"
                )
            dictionary_is_bound = (
                kind == "dictionary"
                and (
                    normalized_name in declared_dictionaries
                    or dictionary_has_inline_values(name, linked_texts)
                )
            )
            if kind == "dictionary" and not dictionary_is_bound:
                raise BoundedScopeBoundaryError(
                    "source-provided dictionary dependency lacks bound values"
                )
            if kind != "dictionary" and not target_ids:
                raise BoundedScopeBoundaryError(
                    "source-provided dependency lacks bound source evidence"
                )
        elif resolution == "external-dynamic":
            if kind != "dictionary":
                raise BoundedScopeBoundaryError(
                    "external-dynamic resolution is valid only for dictionaries"
                )
            binding = external_dictionaries.get(normalized_name)
            if binding is None:
                raise BoundedScopeBoundaryError(
                    "external-dynamic dictionary lacks an authoritative binding"
                )
            if target_ids:
                raise BoundedScopeBoundaryError(
                    "external-dynamic dictionary must not use source-row targets as values"
                )
            if linked != binding["source_row_ids"]:
                raise BoundedScopeBoundaryError(
                    "external-dynamic dictionary rows drifted from its binding"
                )
        elif resolution == "scope-excluded":
            if target_ids or not any(
                normalized_name in value for value in exclusions
            ):
                raise BoundedScopeBoundaryError(
                    "scope-excluded dependency is not present in exclusions"
                )
        missing_blocking_dependency |= is_missing
    if seen_dependency_keys != set(expected_dependencies):
        raise BoundedScopeBoundaryError(
            "dependencies must cover expected_dependency_inventory exactly"
        )

    gaps = payload.get("gaps")
    if not isinstance(gaps, list):
        raise BoundedScopeBoundaryError("gaps must be an array")
    gap_ids: list[str] = []
    for index, item in enumerate(gaps):
        if not isinstance(item, Mapping):
            raise BoundedScopeBoundaryError("gaps entries must be objects")
        _exact_fields(item, GAP_FIELDS, label=f"gaps[{index}]")
        gap_ids.append(
            _nonempty_text(item.get("gap_id"), label=f"gaps[{index}].gap_id")
        )
    if len(gap_ids) != len(set(gap_ids)):
        raise BoundedScopeBoundaryError(
            "gap_id values must be non-empty and unique"
        )
    if dependency_gap_ids - set(gap_ids):
        raise BoundedScopeBoundaryError(
            "dependency gap_ids must link known gaps"
        )

    blocking_gap = False
    blocking_gap_ids: set[str] = set()
    for index, item in enumerate(gaps):
        assert isinstance(item, Mapping)
        if item.get("gap_type") not in CANONICAL_GAP_TYPES:
            raise BoundedScopeBoundaryError(
                "gap_type must use the canonical vocabulary"
            )
        linked = _string_array(
            item.get("source_row_ids"),
            label=f"gaps[{index}].source_row_ids",
            nonempty=True,
            unique=True,
        )
        source_refs = _string_array(
            item.get("source_refs"),
            label=f"gaps[{index}].source_refs",
            nonempty=True,
            unique=True,
        )
        fragments = _string_array(
            item.get("exact_source_fragments"),
            label=f"gaps[{index}].exact_source_fragments",
            nonempty=True,
            unique=True,
        )
        if set(linked) - set(source_rows):
            raise BoundedScopeBoundaryError(
                "gap source_row_ids must link known rows"
            )
        allowed_refs = {
            str(source_rows[row_id].get("source_ref", "")) for row_id in linked
        }
        if set(source_refs) - allowed_refs:
            raise BoundedScopeBoundaryError(
                "gap source_refs must match linked context rows"
            )
        linked_texts = [
            str(source_rows[row_id].get("bounded_source_text", ""))
            for row_id in linked
        ]
        if any(
            not any(fragment in source_text for source_text in linked_texts)
            for fragment in fragments
        ):
            raise BoundedScopeBoundaryError(
                "gap evidence must be literal linked-row text"
            )
        if type(item.get("blocking")) is not bool:
            raise BoundedScopeBoundaryError("gap blocking must be boolean")
        handling = item.get("downstream_handling")
        if handling not in GAP_HANDLING:
            raise BoundedScopeBoundaryError("gap downstream_handling is invalid")
        question = item.get("clarification_question")
        if not isinstance(question, str) or not question.strip():
            raise BoundedScopeBoundaryError(
                "gap clarification_question must be non-empty text"
            )
        if item.get("blocking") is True:
            blocking_gap = True
            blocking_gap_ids.add(str(item["gap_id"]))
            if handling != "block-writer":
                raise BoundedScopeBoundaryError(
                    "blocking gap must use block-writer handling"
                )
            if question == "none_required":
                raise BoundedScopeBoundaryError(
                    "blocking gap requires a clarification question"
                )
        elif handling == "block-writer":
            raise BoundedScopeBoundaryError(
                "non-blocking gap cannot use block-writer handling"
            )
    for item in dependencies:
        assert isinstance(item, Mapping)
        if item.get("resolution") == "missing" and (
            set(item["gap_ids"]) - blocking_gap_ids
        ):
            raise BoundedScopeBoundaryError(
                "missing dependency must link only blocking gaps"
            )
    gaps_by_id = {
        str(item["gap_id"]): item
        for item in gaps
        if isinstance(item, Mapping)
    }
    dependencies_by_id = {
        str(item["dependency_id"]): item
        for item in dependencies
        if isinstance(item, Mapping)
    }
    for dependency_id, linked_gap_ids in resolved_dependency_gap_ids.items():
        dependency = dependencies_by_id[dependency_id]
        dependency_rows = set(map(str, dependency["source_row_ids"]))
        for gap_id in linked_gap_ids:
            gap = gaps_by_id[gap_id]
            gap_rows = set(map(str, gap["source_row_ids"]))
            if (
                gap.get("gap_type") != "missing-observation-interface"
                or gap.get("blocking") is not False
                or gap.get("downstream_handling") != "carry-to-source-model"
                or not gap_rows
                or not gap_rows.issubset(dependency_rows)
            ):
                raise BoundedScopeBoundaryError(
                    "resolved dependency may link only a non-blocking "
                    "missing-observation-interface gap on its source rows"
                )

    status = payload.get("status")
    reason = payload.get("blocking_reason")
    has_blocker = blocking_gap or missing_blocking_dependency
    if status == "ready":
        if has_blocker or reason != "none_required":
            raise BoundedScopeBoundaryError(
                "ready status requires no blocker and blocking_reason=none_required"
            )
    elif status == "blocked":
        if not has_blocker:
            raise BoundedScopeBoundaryError(
                "blocked status requires a blocking gap or missing dependency"
            )
        if (
            not isinstance(reason, str)
            or not reason.strip()
            or reason == "none_required"
        ):
            raise BoundedScopeBoundaryError(
                "blocked status requires a substantive blocking_reason"
            )
    else:
        raise BoundedScopeBoundaryError("status must be ready or blocked")

    returned_locators = payload.get("mockup_locators")
    if returned_locators != context.get("mockup_locators", []):
        raise BoundedScopeBoundaryError(
            "mockup_locators must match declared bounded context exactly"
        )


__all__ = [
    "BoundedScopeBoundaryError",
    "CANONICAL_GAP_TYPES",
    "declared_dictionary_values",
    "dictionary_has_inline_values",
    "expected_dependency_inventory",
    "external_dynamic_dictionary_bindings",
    "is_global_type_definition_row",
    "normalize_entity",
    "recompute_bounded_context_sha256",
    "validate_bounded_scope_context",
    "validate_boundary_decision_v2",
    "validate_source_cache_binding",
    "validate_publication_owner_token",
    "validate_stable_path_segment",
]
