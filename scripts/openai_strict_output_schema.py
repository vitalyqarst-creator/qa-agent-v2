from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


OPENAI_STRICT_OUTPUT_SCHEMA_ALLOWED_KEYWORDS = frozenset(
    {
        "additionalProperties",
        "enum",
        "items",
        "maxItems",
        "minItems",
        "pattern",
        "properties",
        "required",
        "type",
    }
)
OPENAI_STRICT_OUTPUT_SCHEMA_ALLOWED_TYPES = frozenset(
    {"array", "boolean", "integer", "number", "object", "string"}
)
OPENAI_STRICT_OUTPUT_SCHEMA_MAX_PROPERTIES = 5_000
OPENAI_STRICT_OUTPUT_SCHEMA_MAX_DEPTH = 10
OPENAI_STRICT_OUTPUT_SCHEMA_MAX_STRING_CHARACTERS = 120_000
OPENAI_STRICT_OUTPUT_SCHEMA_MAX_ENUM_VALUES = 1_000
OPENAI_STRICT_OUTPUT_SCHEMA_LARGE_ENUM_THRESHOLD = 250
OPENAI_STRICT_OUTPUT_SCHEMA_MAX_LARGE_ENUM_CHARACTERS = 15_000


class OpenAIStrictOutputSchemaError(ValueError):
    pass


class OpenAIStrictOutputInstanceError(ValueError):
    pass


@dataclass
class _SchemaStats:
    property_count: int = 0
    enum_value_count: int = 0
    string_characters: int = 0


def _fail(path: str, message: str) -> None:
    raise OpenAIStrictOutputSchemaError(
        f"OpenAI strict output schema invalid at {path}: {message}"
    )


def _instance_fail(path: str, message: str) -> None:
    raise OpenAIStrictOutputInstanceError(
        f"OpenAI strict output instance invalid at {path}: {message}"
    )


def _matches_type(value: Any, schema_type: str) -> bool:
    if schema_type == "string":
        return isinstance(value, str)
    if schema_type == "integer":
        return type(value) is int
    if schema_type == "number":
        return type(value) in {int, float}
    if schema_type == "boolean":
        return type(value) is bool
    if schema_type == "array":
        return isinstance(value, list)
    if schema_type == "object":
        return isinstance(value, Mapping)
    return False


def _validate_schema_node(
    schema: Mapping[str, Any],
    *,
    path: str,
    root: bool,
    depth: int,
    stats: _SchemaStats,
) -> None:
    if depth > OPENAI_STRICT_OUTPUT_SCHEMA_MAX_DEPTH:
        _fail(
            path,
            f"nesting depth exceeds {OPENAI_STRICT_OUTPUT_SCHEMA_MAX_DEPTH}",
        )
    unknown = sorted(
        repr(key)
        for key in schema
        if not isinstance(key, str)
        or key not in OPENAI_STRICT_OUTPUT_SCHEMA_ALLOWED_KEYWORDS
    )
    if unknown:
        _fail(path, f"unsupported JSON Schema keyword(s): {unknown}")

    schema_type = schema.get("type")
    if (
        not isinstance(schema_type, str)
        or schema_type not in OPENAI_STRICT_OUTPUT_SCHEMA_ALLOWED_TYPES
    ):
        _fail(
            path,
            "type must be one conservative supported scalar/object/array type",
        )
    if root and schema_type != "object":
        _fail(path, "root schema must have type=object")

    enum_values = schema.get("enum")
    if enum_values is not None:
        if not isinstance(enum_values, list) or not enum_values:
            _fail(path, "enum must be a non-empty JSON array")
        try:
            fingerprints = [
                json.dumps(value, ensure_ascii=False, sort_keys=True)
                for value in enum_values
            ]
        except (TypeError, ValueError) as exc:
            _fail(path, f"enum values must be JSON-serializable: {exc}")
        if len(fingerprints) != len(set(fingerprints)):
            _fail(path, "enum values must not contain duplicates")
        if any(not _matches_type(value, schema_type) for value in enum_values):
            _fail(path, f"enum values must match type={schema_type}")
        stats.enum_value_count += len(enum_values)
        if stats.enum_value_count > OPENAI_STRICT_OUTPUT_SCHEMA_MAX_ENUM_VALUES:
            _fail(
                path,
                "total enum values exceed "
                f"{OPENAI_STRICT_OUTPUT_SCHEMA_MAX_ENUM_VALUES}",
            )
        enum_string_characters = sum(
            len(value) for value in enum_values if isinstance(value, str)
        )
        if (
            schema_type == "string"
            and len(enum_values) > OPENAI_STRICT_OUTPUT_SCHEMA_LARGE_ENUM_THRESHOLD
            and enum_string_characters
            > OPENAI_STRICT_OUTPUT_SCHEMA_MAX_LARGE_ENUM_CHARACTERS
        ):
            _fail(
                path,
                "one string enum with more than "
                f"{OPENAI_STRICT_OUTPUT_SCHEMA_LARGE_ENUM_THRESHOLD} values exceeds "
                f"{OPENAI_STRICT_OUTPUT_SCHEMA_MAX_LARGE_ENUM_CHARACTERS} characters",
            )
        stats.string_characters += enum_string_characters
        if (
            stats.string_characters
            > OPENAI_STRICT_OUTPUT_SCHEMA_MAX_STRING_CHARACTERS
        ):
            _fail(
                path,
                "total property-name and string-enum characters exceed "
                f"{OPENAI_STRICT_OUTPUT_SCHEMA_MAX_STRING_CHARACTERS}",
            )

    object_keywords = {"properties", "required", "additionalProperties"}
    present_object_keywords = object_keywords & set(schema)
    if schema_type == "object":
        if present_object_keywords != object_keywords:
            _fail(
                path,
                "object schemas require properties, required and "
                "additionalProperties=false",
            )
        properties = schema["properties"]
        required = schema["required"]
        if not isinstance(properties, Mapping):
            _fail(path, "properties must be a JSON object")
        if (
            not isinstance(required, list)
            or any(not isinstance(item, str) or not item for item in required)
            or len(required) != len(set(required))
        ):
            _fail(path, "required must be a duplicate-free string array")
        property_names = list(properties)
        if any(not isinstance(name, str) or not name for name in property_names):
            _fail(path, "property names must be non-empty strings")
        if set(required) != set(property_names):
            _fail(path, "every object property must be required exactly once")
        if schema["additionalProperties"] is not False:
            _fail(path, "additionalProperties must be false")
        stats.property_count += len(property_names)
        if stats.property_count > OPENAI_STRICT_OUTPUT_SCHEMA_MAX_PROPERTIES:
            _fail(
                path,
                f"total object properties exceed "
                f"{OPENAI_STRICT_OUTPUT_SCHEMA_MAX_PROPERTIES}",
            )
        stats.string_characters += sum(len(name) for name in property_names)
        if (
            stats.string_characters
            > OPENAI_STRICT_OUTPUT_SCHEMA_MAX_STRING_CHARACTERS
        ):
            _fail(
                path,
                "total property-name and string-enum characters exceed "
                f"{OPENAI_STRICT_OUTPUT_SCHEMA_MAX_STRING_CHARACTERS}",
            )
        for name, child in properties.items():
            if not isinstance(child, Mapping):
                _fail(f"{path}.properties.{name}", "property schema must be an object")
            _validate_schema_node(
                child,
                path=f"{path}.properties.{name}",
                root=False,
                depth=depth + 1,
                stats=stats,
            )
    elif present_object_keywords:
        _fail(path, f"{sorted(present_object_keywords)} require type=object")

    array_keywords = {"items", "minItems", "maxItems"}
    present_array_keywords = array_keywords & set(schema)
    if schema_type == "array":
        if "items" not in schema:
            _fail(path, "array schemas require items")
        items = schema["items"]
        if not isinstance(items, Mapping):
            _fail(f"{path}.items", "items must be a schema object")
        for keyword in ("minItems", "maxItems"):
            if keyword in schema and (
                type(schema[keyword]) is not int or schema[keyword] < 0
            ):
                _fail(path, f"{keyword} must be a non-negative integer")
        if (
            "minItems" in schema
            and "maxItems" in schema
            and schema["minItems"] > schema["maxItems"]
        ):
            _fail(path, "minItems must not exceed maxItems")
        _validate_schema_node(
            items,
            path=f"{path}.items",
            root=False,
            depth=depth + 1,
            stats=stats,
        )
    elif present_array_keywords:
        _fail(path, f"{sorted(present_array_keywords)} require type=array")

    if "pattern" in schema:
        if schema_type != "string" or not isinstance(schema["pattern"], str):
            _fail(path, "pattern requires type=string and a string expression")
        try:
            re.compile(schema["pattern"])
        except re.error as exc:
            _fail(path, f"pattern is not a valid regular expression: {exc}")


def validate_openai_strict_output_schema(schema: Mapping[str, Any]) -> None:
    """Validate the project-qualified Codex default-runtime strict subset.

    ``pattern`` and array cardinality keywords require a live exact-schema canary for
    the same unpinned ``codex exec --ignore-user-config`` runtime. They are not a
    portable claim about fine-tuned models or a different runtime profile.
    """

    if not isinstance(schema, Mapping):
        _fail("$", "schema must be a JSON object")
    _validate_schema_node(
        schema,
        path="$",
        root=True,
        depth=1,
        stats=_SchemaStats(),
    )


def _validate_instance_node(
    instance: Any,
    schema: Mapping[str, Any],
    *,
    path: str,
) -> None:
    schema_type = schema["type"]
    if not _matches_type(instance, schema_type):
        _instance_fail(path, f"value must match type={schema_type}")
    if schema_type == "number" and not math.isfinite(instance):
        _instance_fail(path, "number must be finite JSON data")

    if "enum" in schema:
        instance_fingerprint = json.dumps(
            instance,
            ensure_ascii=False,
            sort_keys=True,
        )
        enum_fingerprints = {
            json.dumps(value, ensure_ascii=False, sort_keys=True)
            for value in schema["enum"]
        }
        if instance_fingerprint not in enum_fingerprints:
            _instance_fail(path, "value is absent from enum")

    if schema_type == "object":
        properties = schema["properties"]
        instance_keys = set(instance)
        property_keys = set(properties)
        missing = sorted(property_keys - instance_keys)
        unknown = sorted(instance_keys - property_keys)
        if missing or unknown:
            _instance_fail(
                path,
                f"object fields mismatch: missing={missing or 'none'}, "
                f"unknown={unknown or 'none'}",
            )
        for name, child_schema in properties.items():
            _validate_instance_node(
                instance[name],
                child_schema,
                path=f"{path}.{name}",
            )
    elif schema_type == "array":
        if "minItems" in schema and len(instance) < schema["minItems"]:
            _instance_fail(
                path,
                f"array has fewer than minItems={schema['minItems']}",
            )
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            _instance_fail(
                path,
                f"array has more than maxItems={schema['maxItems']}",
            )
        for index, item in enumerate(instance):
            _validate_instance_node(
                item,
                schema["items"],
                path=f"{path}[{index}]",
            )
    elif schema_type == "string" and "pattern" in schema:
        if re.search(schema["pattern"], instance) is None:
            _instance_fail(path, "string does not match pattern")


def validate_openai_strict_output_instance(
    instance: Any,
    schema: Mapping[str, Any],
) -> None:
    """Validate one parsed JSON value against the conservative strict subset."""

    validate_openai_strict_output_schema(schema)
    _validate_instance_node(instance, schema, path="$")


def _json_shape_type(value: Any) -> str:
    if value is None:
        return "null"
    if type(value) is bool:
        return "boolean"
    if type(value) is int:
        return "integer"
    if type(value) is float:
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, Mapping):
        return "object"
    raise AssertionError(f"validated enum contains unsupported value: {value!r}")


def _normalized_schema_shape(schema: Mapping[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for keyword, value in schema.items():
        if keyword == "enum":
            normalized[keyword] = {
                "count": len(value),
                "json_types": sorted({_json_shape_type(item) for item in value}),
            }
        elif keyword == "properties":
            normalized[keyword] = {
                name: _normalized_schema_shape(child)
                for name, child in value.items()
            }
        elif keyword == "items":
            normalized[keyword] = _normalized_schema_shape(value)
        elif keyword == "required":
            normalized[keyword] = sorted(value)
        else:
            normalized[keyword] = value
    return normalized


def openai_strict_output_schema_shape_sha256(
    schema: Mapping[str, Any],
) -> str:
    """Hash transport topology without binding semantic enum payload values."""

    validate_openai_strict_output_schema(schema)
    canonical = json.dumps(
        _normalized_schema_shape(schema),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
