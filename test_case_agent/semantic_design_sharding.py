from __future__ import annotations

import copy
import hashlib
import json
from collections import defaultdict
from typing import Any, Mapping, Sequence

from test_case_agent.bounded_scope_boundary import normalize_entity
from test_case_agent.semantic_design_bridge import (
    APPLICABILITY_DIMENSIONS,
    SEMANTIC_DESIGN_CONTRACT,
    SEMANTIC_DESIGN_VERSION,
    canonical_payload_sha256,
    prepared_context_sha256,
    semantic_source_signal_registry,
    validate_bridge_boundary,
    validate_semantic_design_binding,
    validate_semantic_input_preflight,
)
from test_case_agent.review_cycle.source_assertions import (
    contains_token_bounded_source_fragment,
    normalize_exact_source_text,
)


class SemanticDesignShardingError(ValueError):
    pass


SEMANTIC_SHARD_PLAN_VERSION = 4
SEMANTIC_SHARD_PLAN_CONTRACT = "semantic-design-shard-plan-v4"
MODEL_EXECUTION_MODE = "model"
DETERMINISTIC_NON_TESTABLE_EXECUTION_MODE = "deterministic-non-testable"


def _context_digest_payload(context: Mapping[str, Any]) -> str:
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


def _bind_projected_context(context: dict[str, Any]) -> dict[str, Any]:
    context.pop("source_cache", None)
    context.pop("source_row_baseline", None)
    context["source_cache"] = {
        "component_digests": {
            "bounded_context_sha256": _context_digest_payload(context),
        }
    }
    return context


class _DisjointSet:
    def __init__(self, values: Sequence[str]) -> None:
        self.parent = {value: value for value in values}

    def find(self, value: str) -> str:
        root = value
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[value] != value:
            parent = self.parent[value]
            self.parent[value] = root
            value = parent
        return root

    def union(self, values: Sequence[str]) -> None:
        present = [value for value in values if value in self.parent]
        if len(present) < 2:
            return
        root = self.find(present[0])
        for value in present[1:]:
            other = self.find(value)
            if other != root:
                self.parent[other] = root


def _require_positive_int(value: int, *, label: str) -> None:
    if type(value) is not int or value < 1:
        raise SemanticDesignShardingError(f"{label} must be a positive integer")


def _execution_mode(included_count: int) -> str:
    return (
        MODEL_EXECUTION_MODE
        if included_count
        else DETERMINISTIC_NON_TESTABLE_EXECUTION_MODE
    )


def semantic_complexity_profile(
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
) -> dict[str, Any]:
    """Measure source-derived semantic work without guessing model output size."""

    clarifications = tuple(
        item
        for item in context.get("approved_clarifications", [])
        if isinstance(item, Mapping)
    )
    preflight = validate_semantic_input_preflight(
        context,
        boundary,
        clarifications,
    )
    row_ids = [
        str(row.get("source_row_id", ""))
        for row in context.get("source_rows", [])
        if isinstance(row, Mapping)
    ]
    included = {
        str(item.get("source_row_id", ""))
        for item in boundary.get("source_decisions", [])
        if isinstance(item, Mapping) and item.get("disposition") == "included"
    }
    slot_counts_by_row = {row_id: 0 for row_id in row_ids}
    model_weight_by_row = {row_id: 0 for row_id in row_ids}
    unbound_slot_ids: list[str] = []
    for slot in preflight.get("semantic_slot_registry", []):
        if not isinstance(slot, Mapping):
            continue
        slot_rows = [
            row_id
            for row_id in map(str, slot.get("source_row_ids", []))
            if row_id in slot_counts_by_row
        ]
        if not slot_rows:
            unbound_slot_ids.append(str(slot.get("slot_id", "")))
            continue
        for row_id in slot_rows:
            slot_counts_by_row[row_id] += 1
            if row_id in included:
                model_weight_by_row[row_id] += 1
    return {
        "version": 1,
        "contract": "semantic-complexity-profile-v1",
        "semantic_input_sha256": preflight["semantic_input_sha256"],
        "semantic_slot_count": preflight["semantic_slot_count"],
        "semantic_slot_counts": copy.deepcopy(preflight["semantic_slot_counts"]),
        "model_semantic_weight": sum(model_weight_by_row.values()),
        "slot_counts_by_source_row": slot_counts_by_row,
        "model_semantic_weight_by_source_row": model_weight_by_row,
        "unbound_slot_ids": unbound_slot_ids,
    }


def build_semantic_shard_plan(
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
    *,
    mode: str = "auto",
    max_included_rows: int = 12,
    max_source_rows: int = 18,
    max_shards: int = 8,
    max_semantic_weight: int | None = None,
) -> dict[str, Any]:
    """Build immutable, complete and disjoint semantic row ownership.

    Field/alias dependencies, source-context clarifications and gap evidence stay
    atomic. Broad integration and dictionary dependencies may be projected into
    several independently validated mini-scopes and are restored during merge.
    """

    if mode not in {"off", "auto", "on"}:
        raise SemanticDesignShardingError("semantic sharding mode is invalid")
    _require_positive_int(max_included_rows, label="max_included_rows")
    _require_positive_int(max_source_rows, label="max_source_rows")
    _require_positive_int(max_shards, label="max_shards")
    if max_semantic_weight is not None:
        _require_positive_int(
            max_semantic_weight,
            label="max_semantic_weight",
        )
    validate_bridge_boundary(context, boundary)
    rows = context.get("source_rows")
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise SemanticDesignShardingError("context.source_rows must be an object array")
    row_ids = [str(row.get("source_row_id", "")) for row in rows]
    if not row_ids or len(row_ids) != len(set(row_ids)):
        raise SemanticDesignShardingError("source row ids must be non-empty and unique")
    decisions = {
        str(item.get("source_row_id", "")): item
        for item in boundary.get("source_decisions", [])
        if isinstance(item, Mapping)
    }
    if list(decisions) != row_ids:
        raise SemanticDesignShardingError("boundary row order drifted from context")
    included = {
        row_id
        for row_id, decision in decisions.items()
        if decision.get("disposition") == "included"
    }
    complexity = semantic_complexity_profile(context, boundary)
    model_weight_by_row = complexity["model_semantic_weight_by_source_row"]
    total_semantic_weight = int(complexity["model_semantic_weight"])
    capacity_exceeded = (
        len(included) > max_included_rows
        or len(row_ids) > max_source_rows
        or (
            max_semantic_weight is not None
            and total_semantic_weight > max_semantic_weight
        )
    )
    if mode == "off" or (mode == "auto" and not capacity_exceeded):
        plan = {
            "version": SEMANTIC_SHARD_PLAN_VERSION,
            "contract": SEMANTIC_SHARD_PLAN_CONTRACT,
            "mode": "single",
            "trigger": "disabled" if mode == "off" else "within-capacity",
            "prepared_context_sha256": prepared_context_sha256(context),
            "scope_boundary_decision_sha256": canonical_payload_sha256(boundary),
            "limits": {
                "max_included_rows": max_included_rows,
                "max_source_rows": max_source_rows,
                "max_shards": max_shards,
                "max_semantic_weight": max_semantic_weight,
            },
            "complexity": complexity,
            "shards": [
                {
                    "shard_id": "semantic-shard-001",
                    "owned_source_row_ids": row_ids,
                    "owned_included_row_count": len(included),
                    "owned_source_row_count": len(row_ids),
                    "owned_semantic_weight": total_semantic_weight,
                    "execution_mode": _execution_mode(len(included)),
                }
            ],
        }
        plan["plan_sha256"] = canonical_payload_sha256(plan)
        return plan

    dsu = _DisjointSet(row_ids)
    for dependency in boundary.get("dependencies", []):
        if not isinstance(dependency, Mapping):
            continue
        if dependency.get("kind") == "field" or dependency.get("resolution") == "approved-alias":
            dsu.union(
                [
                    *map(str, dependency.get("source_row_ids", [])),
                    *map(str, dependency.get("target_source_row_ids", [])),
                ]
            )
    for clarification in context.get("approved_clarifications", []):
        if (
            isinstance(clarification, Mapping)
            and clarification.get("binding_scope", "requirement-code")
            == "source-context"
        ):
            dsu.union(list(map(str, clarification.get("source_row_ids", []))))
    for gap in boundary.get("gaps", []):
        if isinstance(gap, Mapping):
            dsu.union(list(map(str, gap.get("source_row_ids", []))))

    components: dict[str, list[str]] = defaultdict(list)
    for row_id in row_ids:
        components[dsu.find(row_id)].append(row_id)
    order = {row_id: index for index, row_id in enumerate(row_ids)}
    ordered_components = sorted(
        components.values(), key=lambda values: min(order[value] for value in values)
    )
    for component in ordered_components:
        included_count = len(set(component) & included)
        component_semantic_weight = sum(
            int(model_weight_by_row[row_id]) for row_id in component
        )
        if (
            included_count > max_included_rows
            or len(component) > max_source_rows
            or (
                max_semantic_weight is not None
                and component_semantic_weight > max_semantic_weight
            )
        ):
            raise SemanticDesignShardingError(
                "an atomic semantic component exceeds shard capacity: "
                + ", ".join(component)
            )

    bins: list[list[str]] = []
    current: list[str] = []
    current_included = 0
    current_semantic_weight = 0
    for component in ordered_components:
        component_included = len(set(component) & included)
        component_semantic_weight = sum(
            int(model_weight_by_row[row_id]) for row_id in component
        )
        if current and (
            current_included + component_included > max_included_rows
            or len(current) + len(component) > max_source_rows
            or (
                max_semantic_weight is not None
                and current_semantic_weight + component_semantic_weight
                > max_semantic_weight
            )
        ):
            bins.append(sorted(current, key=order.__getitem__))
            current = []
            current_included = 0
            current_semantic_weight = 0
        current.extend(component)
        current_included += component_included
        current_semantic_weight += component_semantic_weight
    if current:
        bins.append(sorted(current, key=order.__getitem__))
    if len(bins) < 2:
        raise SemanticDesignShardingError(
            "capacity trigger requested sharding but no safe split was produced"
        )
    if len(bins) > max_shards:
        raise SemanticDesignShardingError(
            f"semantic shard count {len(bins)} exceeds max_shards={max_shards}"
        )

    shards = []
    for index, values in enumerate(bins, start=1):
        included_count = len(set(values) & included)
        shards.append(
            {
                "shard_id": f"semantic-shard-{index:03d}",
                "owned_source_row_ids": values,
                "owned_included_row_count": included_count,
                "owned_source_row_count": len(values),
                "owned_semantic_weight": sum(
                    int(model_weight_by_row[row_id]) for row_id in values
                ),
                "execution_mode": _execution_mode(included_count),
            }
        )
    owned = [row_id for shard in shards for row_id in shard["owned_source_row_ids"]]
    if sorted(owned, key=order.__getitem__) != row_ids or len(owned) != len(set(owned)):
        raise SemanticDesignShardingError("semantic shard ownership is not complete/disjoint")
    plan = {
        "version": SEMANTIC_SHARD_PLAN_VERSION,
        "contract": SEMANTIC_SHARD_PLAN_CONTRACT,
        "mode": "sharded",
        "trigger": (
            "complexity-exceeded"
            if mode == "auto"
            and max_semantic_weight is not None
            and total_semantic_weight > max_semantic_weight
            and len(included) <= max_included_rows
            and len(row_ids) <= max_source_rows
            else "capacity-exceeded" if mode == "auto" else "forced"
        ),
        "prepared_context_sha256": prepared_context_sha256(context),
        "scope_boundary_decision_sha256": canonical_payload_sha256(boundary),
        "limits": {
            "max_included_rows": max_included_rows,
            "max_source_rows": max_source_rows,
            "max_shards": max_shards,
            "max_semantic_weight": max_semantic_weight,
        },
        "complexity": complexity,
        "shards": shards,
    }
    plan["plan_sha256"] = canonical_payload_sha256(plan)
    return plan


def rebind_semantic_shard_plan_ownership(
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
    preferred_plan: Mapping[str, Any],
    *,
    max_included_rows: int,
    max_source_rows: int,
    max_shards: int,
    max_semantic_weight: int | None = None,
) -> dict[str, Any]:
    """Preserve a prior safe partition while rebinding current semantic weights.

    Reuse is allowed only when the prior plan is internally digest-valid and its
    ownership is complete, disjoint and capacity-safe for the current row registry.
    The old context/boundary digests are intentionally not reused: this helper exists
    for a fresh context whose row identities are stable but whose clarification or
    deterministic weights changed. The result is suitable for development
    qualification, not proof of a fresh benchmark execution.
    """

    _require_positive_int(max_included_rows, label="max_included_rows")
    _require_positive_int(max_source_rows, label="max_source_rows")
    _require_positive_int(max_shards, label="max_shards")
    if max_semantic_weight is not None:
        _require_positive_int(max_semantic_weight, label="max_semantic_weight")
    _validate_plan_digest(preferred_plan)
    if preferred_plan.get("mode") != "sharded":
        raise SemanticDesignShardingError(
            "preferred semantic shard ownership requires a sharded plan"
        )
    rows = context.get("source_rows")
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise SemanticDesignShardingError("context.source_rows must be an object array")
    row_ids = [str(row.get("source_row_id", "")) for row in rows]
    decisions = {
        str(item.get("source_row_id", "")): item
        for item in boundary.get("source_decisions", [])
        if isinstance(item, Mapping)
    }
    if list(decisions) != row_ids:
        raise SemanticDesignShardingError("boundary row order drifted from context")
    included = {
        row_id
        for row_id, decision in decisions.items()
        if decision.get("disposition") == "included"
    }
    complexity = semantic_complexity_profile(context, boundary)
    weight_by_row = complexity["model_semantic_weight_by_source_row"]
    preferred_shards = preferred_plan.get("shards")
    if not isinstance(preferred_shards, list) or len(preferred_shards) < 2:
        raise SemanticDesignShardingError(
            "preferred semantic shard plan has no sharded ownership"
        )
    if len(preferred_shards) > max_shards:
        raise SemanticDesignShardingError(
            f"preferred semantic shard count {len(preferred_shards)} "
            f"exceeds max_shards={max_shards}"
        )
    order = {row_id: index for index, row_id in enumerate(row_ids)}
    rebound_shards: list[dict[str, Any]] = []
    owned_rows: list[str] = []
    shard_ids: set[str] = set()
    for raw_shard in preferred_shards:
        if not isinstance(raw_shard, Mapping):
            raise SemanticDesignShardingError("preferred shard entries must be objects")
        shard_id = str(raw_shard.get("shard_id", ""))
        values = list(map(str, raw_shard.get("owned_source_row_ids", [])))
        if not shard_id or shard_id in shard_ids or not values:
            raise SemanticDesignShardingError(
                "preferred shard ids and ownership must be non-empty and unique"
            )
        shard_ids.add(shard_id)
        if any(value not in order for value in values) or values != sorted(
            values,
            key=order.__getitem__,
        ):
            raise SemanticDesignShardingError(
                f"preferred shard ownership is invalid for {shard_id}"
            )
        included_count = len(set(values) & included)
        semantic_weight = sum(int(weight_by_row[value]) for value in values)
        if (
            included_count > max_included_rows
            or len(values) > max_source_rows
            or (
                max_semantic_weight is not None
                and semantic_weight > max_semantic_weight
            )
        ):
            raise SemanticDesignShardingError(
                f"preferred shard {shard_id} exceeds current capacity"
            )
        rebound_shards.append(
            {
                "shard_id": shard_id,
                "owned_source_row_ids": values,
                "owned_included_row_count": included_count,
                "owned_source_row_count": len(values),
                "owned_semantic_weight": semantic_weight,
                "execution_mode": _execution_mode(included_count),
            }
        )
        owned_rows.extend(values)
    if (
        sorted(owned_rows, key=order.get) != row_ids
        or len(owned_rows) != len(set(owned_rows))
    ):
        raise SemanticDesignShardingError(
            "preferred semantic shard ownership is not complete/disjoint"
        )
    plan = {
        "version": SEMANTIC_SHARD_PLAN_VERSION,
        "contract": SEMANTIC_SHARD_PLAN_CONTRACT,
        "mode": "sharded",
        "trigger": "preferred-ownership-rebound",
        "prepared_context_sha256": prepared_context_sha256(context),
        "scope_boundary_decision_sha256": canonical_payload_sha256(boundary),
        "preferred_plan_sha256": str(preferred_plan["plan_sha256"]),
        "limits": {
            "max_included_rows": max_included_rows,
            "max_source_rows": max_source_rows,
            "max_shards": max_shards,
            "max_semantic_weight": max_semantic_weight,
        },
        "complexity": complexity,
        "shards": rebound_shards,
    }
    plan["plan_sha256"] = canonical_payload_sha256(plan)
    return plan


def _project_clarifications(
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
    owned: set[str],
) -> list[dict[str, Any]]:
    codes = {
        str(code)
        for decision in boundary.get("source_decisions", [])
        if isinstance(decision, Mapping)
        and str(decision.get("source_row_id")) in owned
        for code in decision.get("requirement_codes", [])
    }
    result: list[dict[str, Any]] = []
    for raw in context.get("approved_clarifications", []):
        if not isinstance(raw, Mapping):
            continue
        item = copy.deepcopy(dict(raw))
        binding_scope = item.get("binding_scope", "requirement-code")
        if binding_scope == "source-context":
            selected = [row_id for row_id in map(str, item.get("source_row_ids", [])) if row_id in owned]
            if not selected:
                continue
            item["source_row_ids"] = selected
        else:
            selected_codes = [code for code in map(str, item.get("requirement_codes", [])) if code in codes]
            if not selected_codes:
                continue
            item["requirement_codes"] = selected_codes
        result.append(item)
    return result


def _project_dependency(
    dependency: Mapping[str, Any],
    owned: set[str],
    rows_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any] | None:
    sources = [row_id for row_id in map(str, dependency.get("source_row_ids", [])) if row_id in owned]
    targets = [row_id for row_id in map(str, dependency.get("target_source_row_ids", [])) if row_id in owned]
    if not sources:
        return None
    fragments = [
        fragment
        for fragment in map(str, dependency.get("exact_source_fragments", []))
        if any(fragment in str(rows_by_id[row_id].get("bounded_source_text", "")) for row_id in sources)
    ]
    if not fragments:
        raise SemanticDesignShardingError(
            f"{dependency.get('dependency_id')} has no literal evidence in projected rows"
        )
    if dependency.get("kind") == "field" and (
        sources != list(map(str, dependency.get("source_row_ids", [])))
        or targets != list(map(str, dependency.get("target_source_row_ids", [])))
    ):
        raise SemanticDesignShardingError(
            f"field dependency {dependency.get('dependency_id')} was split"
        )
    if dependency.get("resolution") == "source-provided" and dependency.get("kind") != "dictionary" and not targets:
        raise SemanticDesignShardingError(
            f"{dependency.get('dependency_id')} cannot be projected without a target"
        )
    item = copy.deepcopy(dict(dependency))
    item["source_row_ids"] = sources
    item["target_source_row_ids"] = targets
    item["exact_source_fragments"] = fragments
    return item


def _project_bounded_evidence_inline(
    context: Mapping[str, Any],
    projected_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any] | None:
    """Keep only literal source extracts represented by this shard's rows."""

    inline = context.get("bounded_evidence_inline")
    if not isinstance(inline, Mapping):
        return None
    row_texts = [
        normalize_exact_source_text(str(row.get("bounded_source_text", "")))
        for row in projected_rows
        if str(row.get("bounded_source_text", "")).strip()
    ]
    result: dict[str, Any] = {}
    for source_kind, raw_section in inline.items():
        if not isinstance(raw_section, Mapping):
            result[str(source_kind)] = copy.deepcopy(raw_section)
            continue
        section = copy.deepcopy(dict(raw_section))
        fragments = raw_section.get("fragments")
        if isinstance(fragments, list):
            section["fragments"] = [
                copy.deepcopy(fragment)
                for fragment in fragments
                if isinstance(fragment, Mapping)
                and (
                    normalized_fragment := normalize_exact_source_text(
                        str(fragment.get("exact_source_text", ""))
                    )
                )
                and any(
                    normalized_fragment in row_text
                    or row_text in normalized_fragment
                    for row_text in row_texts
                )
            ]
        result[str(source_kind)] = section
    return result


def project_semantic_shard(
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
    shard: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_bridge_boundary(context, boundary)
    owned_order = list(map(str, shard.get("owned_source_row_ids", [])))
    owned = set(owned_order)
    if not owned_order or len(owned_order) != len(owned):
        raise SemanticDesignShardingError("shard ownership must be non-empty and unique")
    rows_by_id = {
        str(row.get("source_row_id", "")): row
        for row in context.get("source_rows", [])
        if isinstance(row, Mapping)
    }
    unknown = sorted(owned - set(rows_by_id))
    if unknown:
        raise SemanticDesignShardingError("shard owns unknown rows: " + ", ".join(unknown))

    semantics: list[dict[str, Any]] = []
    support_ids: list[str] = []
    for raw in context.get("source_table_column_semantics", []):
        if not isinstance(raw, Mapping):
            continue
        targets = [row_id for row_id in map(str, raw.get("target_source_row_ids", [])) if row_id in owned]
        if not targets:
            continue
        header = str(raw.get("header_source_row_id", ""))
        if header not in owned:
            original = next(
                (
                    item
                    for item in boundary.get("source_decisions", [])
                    if isinstance(item, Mapping) and item.get("source_row_id") == header
                ),
                None,
            )
            if not isinstance(original, Mapping) or original.get("disposition") != "context":
                raise SemanticDesignShardingError(
                    f"typed field header {header} cannot be shared as read-only context"
                )
            support_ids.append(header)
        item = copy.deepcopy(dict(raw))
        item["target_source_row_ids"] = targets
        semantics.append(item)
    projection_ids = [
        row_id
        for row_id in rows_by_id
        if row_id in owned or row_id in set(support_ids)
    ]
    projected = copy.deepcopy(dict(context))
    projected_rows = [copy.deepcopy(rows_by_id[row_id]) for row_id in projection_ids]
    projected["source_rows"] = projected_rows
    projected["source_table_column_semantics"] = semantics
    projected["approved_clarifications"] = _project_clarifications(context, boundary, owned)
    projected_inline = _project_bounded_evidence_inline(context, projected_rows)
    if projected_inline is not None:
        projected["bounded_evidence_inline"] = projected_inline

    projected_dependencies: list[dict[str, Any]] = []
    projected_expected: list[dict[str, Any]] = []
    for dependency in boundary.get("dependencies", []):
        if not isinstance(dependency, Mapping):
            continue
        item = _project_dependency(dependency, owned, rows_by_id)
        if item is None:
            continue
        projected_dependencies.append(item)
        projected_expected.append(
            {
                key: copy.deepcopy(item[key])
                for key in (
                    "kind",
                    "name",
                    "source_row_ids",
                    "resolution",
                    "target_source_row_ids",
                    "exact_source_fragments",
                )
            }
        )
    projected["expected_dependencies"] = projected_expected
    external_bindings = {
        normalize_entity(str(item.get("dictionary_name", ""))): item
        for item in context.get("external_dictionary_bindings", [])
        if isinstance(item, Mapping)
    }
    projected_external_bindings: list[dict[str, Any]] = []
    for dependency in projected_dependencies:
        if dependency.get("resolution") != "external-dynamic":
            continue
        normalized_name = normalize_entity(str(dependency.get("name", "")))
        binding = external_bindings.get(normalized_name)
        if binding is None:
            raise SemanticDesignShardingError(
                f"external dynamic dependency {dependency.get('dependency_id')} "
                "has no context binding"
            )
        item = copy.deepcopy(dict(binding))
        item["source_row_ids"] = copy.deepcopy(dependency["source_row_ids"])
        projected_external_bindings.append(item)
    projected["external_dictionary_bindings"] = projected_external_bindings
    alias_names = {
        str(item["name"])
        for item in projected_dependencies
        if item.get("resolution") == "approved-alias"
    }
    aliases = context.get("dependency_aliases", {})
    provenance = context.get("dependency_alias_provenance", {})
    projected["dependency_aliases"] = {
        key: copy.deepcopy(value)
        for key, value in aliases.items()
        if key in alias_names
    } if isinstance(aliases, Mapping) else {}
    projected["dependency_alias_provenance"] = {
        key: copy.deepcopy(value)
        for key, value in provenance.items()
        if key in alias_names
    } if isinstance(provenance, Mapping) else {}
    owned_codes = {
        str(code)
        for decision in boundary.get("source_decisions", [])
        if isinstance(decision, Mapping)
        and str(decision.get("source_row_id")) in owned
        for code in decision.get("requirement_codes", [])
    }
    if isinstance(context.get("parity"), list):
        projected["parity"] = [
            copy.deepcopy(item)
            for item in context["parity"]
            if isinstance(item, Mapping) and str(item.get("requirement_code")) in owned_codes
        ]
    projected = _bind_projected_context(projected)

    projected_decisions: list[dict[str, Any]] = []
    original_decisions = {
        str(item.get("source_row_id", "")): item
        for item in boundary.get("source_decisions", [])
        if isinstance(item, Mapping)
    }
    for row_id in projection_ids:
        item = copy.deepcopy(dict(original_decisions[row_id]))
        if row_id not in owned:
            item["disposition"] = "context"
            item["requirement_codes"] = []
            item["rationale"] = "Shared typed-column header; read-only shard context."
        projected_decisions.append(item)
    projected_gaps = [
        copy.deepcopy(item)
        for item in boundary.get("gaps", [])
        if isinstance(item, Mapping)
        and set(map(str, item.get("source_row_ids", []))).issubset(owned)
    ]
    projected_boundary = copy.deepcopy(dict(boundary))
    projected_boundary["source_decisions"] = projected_decisions
    projected_boundary["dependencies"] = projected_dependencies
    projected_boundary["gaps"] = projected_gaps
    validate_bridge_boundary(projected, projected_boundary)
    return projected, projected_boundary


def _validate_plan_binding(
    context: Mapping[str, Any], boundary: Mapping[str, Any], plan: Mapping[str, Any]
) -> None:
    _validate_plan_digest(plan)
    if plan.get("prepared_context_sha256") != prepared_context_sha256(context):
        raise SemanticDesignShardingError("semantic shard plan context drifted")
    if plan.get("scope_boundary_decision_sha256") != canonical_payload_sha256(boundary):
        raise SemanticDesignShardingError("semantic shard plan boundary drifted")


def _validate_plan_digest(plan: Mapping[str, Any]) -> None:
    payload = dict(plan)
    digest = payload.pop("plan_sha256", None)
    if digest != canonical_payload_sha256(payload):
        raise SemanticDesignShardingError("semantic shard plan digest mismatch")
    if plan.get("version") != SEMANTIC_SHARD_PLAN_VERSION:
        raise SemanticDesignShardingError("semantic shard plan version mismatch")
    if plan.get("contract") != SEMANTIC_SHARD_PLAN_CONTRACT:
        raise SemanticDesignShardingError("semantic shard plan contract mismatch")


def _ordered_unique(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _na_requirement_code_evidence(
    context: Mapping[str, Any],
    row: Mapping[str, Any],
    requirement_codes: Sequence[str],
) -> list[dict[str, Any]]:
    row_id = str(row.get("source_row_id", ""))
    source_text = normalize_exact_source_text(
        str(row.get("bounded_source_text", ""))
    )
    parity = context.get("parity", [])
    main_ft_pdf = str(context.get("main_ft_pdf", ""))
    result: list[dict[str, Any]] = []
    for requirement_code in requirement_codes:
        normalized_code = normalize_exact_source_text(requirement_code)
        if contains_token_bounded_source_fragment(source_text, normalized_code):
            result.append(
                {
                    "requirement_code": requirement_code,
                    "source_row_id": row_id,
                    "provenance_role": "xhtml-row",
                    "exact_source_fragment": requirement_code,
                    "evidence_source_path": "none_required",
                    "evidence_locator": "none_required",
                }
            )
            continue
        parity_match = next(
            (
                item
                for item in parity
                if isinstance(item, Mapping)
                and item.get("requirement_code") == requirement_code
                and isinstance(item.get("pdf_locator"), str)
            ),
            None,
        )
        if not isinstance(parity_match, Mapping) or not main_ft_pdf:
            raise SemanticDesignShardingError(
                f"{row_id} cannot deterministically bind requirement code "
                f"{requirement_code}"
            )
        result.append(
            {
                "requirement_code": requirement_code,
                "source_row_id": row_id,
                "provenance_role": "pdf-parity",
                "exact_source_fragment": "none_required",
                "evidence_source_path": main_ft_pdf,
                "evidence_locator": str(parity_match["pdf_locator"]),
            }
        )
    return result


def _na_clarification_bindings(
    context: Mapping[str, Any],
    *,
    row_id: str,
    requirement_codes: Sequence[str],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    row_code_set = set(requirement_codes)
    for raw in context.get("approved_clarifications", []):
        if not isinstance(raw, Mapping):
            continue
        binding_scope = str(raw.get("binding_scope", "requirement-code"))
        if binding_scope == "source-context":
            if row_id not in set(map(str, raw.get("source_row_ids", []))):
                continue
            local_codes: list[str] = []
            local_rows = [row_id]
        elif binding_scope == "requirement-code":
            local_codes = [
                code
                for code in map(str, raw.get("requirement_codes", []))
                if code in row_code_set
            ]
            if not local_codes:
                continue
            raise SemanticDesignShardingError(
                f"{row_id} requirement-code clarification cannot bind a "
                "non-testable canonical assertion"
            )
        else:
            raise SemanticDesignShardingError(
                f"unsupported clarification binding_scope={binding_scope}"
            )
        result.append(
            {
                "clarification_id": str(raw.get("clarification_id", "")),
                "clause_kind": "canonical",
                "clause_index": 0,
                "requirement_codes": local_codes,
                "exact_answer_sha256": str(raw.get("exact_answer_sha256", "")),
                "binding_scope": binding_scope,
                "source_row_ids": local_rows,
            }
        )
    return result


def materialize_non_testable_semantic_shard(
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Materialize a context/excluded-only shard without a model call.

    This route is intentionally narrow. It fails closed if the projection owns
    an included row, an executable source signal, a dictionary, or a resolved
    in-scope dependency.
    """

    validate_bridge_boundary(context, boundary)
    decisions = boundary.get("source_decisions", [])
    if not isinstance(decisions, list) or any(
        not isinstance(item, Mapping) for item in decisions
    ):
        raise SemanticDesignShardingError(
            "non-testable shard requires authoritative source decisions"
        )
    included = [
        str(item.get("source_row_id", ""))
        for item in decisions
        if item.get("disposition") == "included"
    ]
    if included:
        raise SemanticDesignShardingError(
            "deterministic non-testable shard owns included rows: "
            + ", ".join(included)
        )
    clarifications = tuple(
        copy.deepcopy(dict(item))
        for item in context.get("approved_clarifications", [])
        if isinstance(item, Mapping)
    )
    preflight = validate_semantic_input_preflight(
        context,
        boundary,
        clarifications,
    )
    if (
        preflight.get("eligible_source_row_count") != 0
        or preflight.get("negative_signal_count") != 0
        or preflight.get("requiredness_signal_count") != 0
        or preflight.get("dictionary_registry") != []
    ):
        raise SemanticDesignShardingError(
            "non-testable shard contains executable semantic signals"
        )

    rows = context.get("source_rows", [])
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise SemanticDesignShardingError(
            "non-testable shard context.source_rows must be an object array"
        )
    decision_by_row = {
        str(item.get("source_row_id", "")): item for item in decisions
    }
    source_designs: list[dict[str, Any]] = []
    for row in rows:
        row_id = str(row.get("source_row_id", ""))
        decision = decision_by_row.get(row_id)
        if not isinstance(decision, Mapping):
            raise SemanticDesignShardingError(
                f"non-testable shard misses source decision for {row_id}"
            )
        requirement_codes = list(map(str, decision.get("requirement_codes", [])))
        rationale = str(decision.get("rationale", "")).strip()
        if len(rationale) < 12:
            raise SemanticDesignShardingError(
                f"{row_id} requires a substantive boundary rationale"
            )
        field_or_block = str(row.get("field_or_action", ""))
        source_reference = str(row.get("source_ref", ""))
        assertion = {
            "assertion_id": f"ASSERT-{row_id}-NA",
            "canonical_statement": (
                f"{rationale} Самостоятельное исполняемое обязательство отсутствует."
            ),
            "polarity": "neutral",
            "semantic_disposition": "not-applicable",
            "execution_readiness": "not-applicable",
            "execution_readiness_rationale": "none_required",
            "risk": "low",
            "condition_clauses": [],
            "action_clauses": [],
            "oracle_clauses": [],
            "requirement_codes": requirement_codes,
            "requirement_code_evidence": _na_requirement_code_evidence(
                context,
                row,
                requirement_codes,
            ),
            "clause_evidence": [],
            "supporting_source_bindings": [],
            "clarification_clause_bindings": _na_clarification_bindings(
                context,
                row_id=row_id,
                requirement_codes=requirement_codes,
            ),
            "atom_id": f"ATOM-{row_id}-NA",
            "obligation_ids": [],
            "disposition_rationale": rationale,
            "source_property_id": "none_required",
            "field_or_block": field_or_block,
            "source_reference": source_reference,
        }
        source_designs.append(
            {
                "source_row_id": row_id,
                "boundary_disposition": str(decision.get("disposition", "")),
                "requirement_codes": requirement_codes,
                "assertions": [assertion],
            }
        )

    dependency_bindings: list[dict[str, Any]] = []
    dependency_fields = (
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
    )
    for dependency in boundary.get("dependencies", []):
        if not isinstance(dependency, Mapping):
            raise SemanticDesignShardingError(
                "non-testable shard dependency must be an object"
            )
        if dependency.get("resolution") != "scope-excluded":
            raise SemanticDesignShardingError(
                f"{dependency.get('dependency_id')} requires a model-owned testable chain"
            )
        dependency_bindings.append(
            {
                **{key: copy.deepcopy(dependency.get(key)) for key in dependency_fields},
                "semantic_disposition": "not-applicable",
                "linked_assertion_ids": [],
                "linked_atom_ids": [],
                "linked_obligation_ids": [],
                "mapping_rationale": str(dependency.get("rationale", "")),
            }
        )

    applicability = [
        {
            "dimension": dimension,
            "applicable": "no",
            "source_ref": "none_required",
            "reason": (
                "Проекция содержит только контекстные или исключённые строки и "
                "не создаёт исполняемых ATOM/TC-цепочек."
            ),
            "linked_atoms": [],
            "linked_test_cases": [],
        }
        for dimension in APPLICABILITY_DIMENSIONS
    ]
    design = {
        "version": SEMANTIC_DESIGN_VERSION,
        "contract": SEMANTIC_DESIGN_CONTRACT,
        "status": "ready",
        "blocking_reason": "none_required",
        "prepared_context_sha256": prepared_context_sha256(context),
        "scope_boundary_decision_sha256": canonical_payload_sha256(boundary),
        "scope_summary": boundary["scope_summary"],
        "included": copy.deepcopy(boundary["scope_boundary"]["include"]),
        "excluded": copy.deepcopy(boundary["scope_boundary"]["exclude"]),
        "mockup_locators": copy.deepcopy(boundary["mockup_locators"]),
        "source_designs": source_designs,
        "obligations": [],
        "reset_lifecycle_bindings": [],
        "dependency_bindings": dependency_bindings,
        "dictionaries": [],
        "negative_oracles": [],
        "requiredness_oracles": [],
        "applicability": applicability,
    }
    validation = validate_semantic_design_binding(
        context,
        boundary,
        design,
        clarifications=clarifications,
        require_ready=True,
    )
    return design, {
        "version": 1,
        "contract": "deterministic-non-testable-semantic-shard-v1",
        "status": "verified",
        "semantic_design_sha256": canonical_payload_sha256(design),
        "source_row_count": len(source_designs),
        "model_invoked": False,
        "validation": validation,
    }


def _signal_mapping(
    full_registry: Mapping[str, Sequence[Mapping[str, Any]]],
    shard_registry: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    kind: str,
) -> dict[str, str]:
    if kind not in {"negative", "requiredness"}:
        raise SemanticDesignShardingError("unsupported semantic signal kind")

    def key(item: Mapping[str, Any]) -> tuple[Any, ...]:
        return (
            str(item.get("source_row_id", "")),
            tuple(map(str, item.get("requirement_codes", []))),
            str(item.get("restriction_type", "")),
            str(item.get("literal_anchor", "")),
            str(item.get("source_property_id", "")),
            str(item.get("source_cell_locator", "")),
        )

    full_by_key: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    for item in full_registry.get(kind, []):
        if isinstance(item, Mapping):
            full_by_key[key(item)].append(str(item.get("signal_id", "")))
    used: dict[tuple[Any, ...], int] = defaultdict(int)
    result: dict[str, str] = {}
    for item in shard_registry.get(kind, []):
        if not isinstance(item, Mapping):
            continue
        item_key = key(item)
        index = used[item_key]
        candidates = full_by_key.get(item_key, [])
        if index >= len(candidates):
            raise SemanticDesignShardingError(
                f"cannot bind projected {kind} signal to the full registry"
            )
        result[str(item.get("signal_id", ""))] = candidates[index]
        used[item_key] += 1
    return result


def _order_oracles_by_signal_registry(
    oracles: Sequence[Mapping[str, Any]],
    registry: Sequence[Mapping[str, Any]],
    *,
    kind: str,
) -> list[dict[str, Any]]:
    """Restore canonical full-registry order after dependency-aware sharding."""

    expected_ids = [str(item.get("signal_id", "")) for item in registry]
    actual_ids = [str(item.get("signal_id", "")) for item in oracles]
    if (
        not all(expected_ids)
        or len(expected_ids) != len(set(expected_ids))
        or len(actual_ids) != len(set(actual_ids))
        or set(actual_ids) != set(expected_ids)
    ):
        raise SemanticDesignShardingError(
            f"merged {kind} oracle signals do not exactly cover the full registry"
        )
    order = {signal_id: index for index, signal_id in enumerate(expected_ids)}
    return sorted(
        (copy.deepcopy(dict(item)) for item in oracles),
        key=lambda item: order[str(item["signal_id"])],
    )


def _remap_oracle_planned_route(
    item: dict[str, Any],
    *,
    shard_id: str,
    new_scope_obligation_id: str,
    old_linked_obligation_id: str,
    obligation_by_key: Mapping[tuple[str, str], Mapping[str, Any]],
    tc_map: Mapping[tuple[str, str], str],
) -> None:
    """Keep oracle route markers aligned with remapped OBL/TC/scope identifiers."""

    decision = item.get("decision")
    if decision == "candidate_tc_required":
        item["planned_tc_or_gap"] = f"candidate:{new_scope_obligation_id}"
        return
    if decision != "executable_tc":
        return
    obligation = obligation_by_key.get((shard_id, old_linked_obligation_id))
    if not isinstance(obligation, Mapping):
        raise SemanticDesignShardingError(
            "oracle references an unknown projected obligation"
        )
    old_planned_tc_id = str(obligation.get("planned_tc_id", ""))
    new_planned_tc_id = tc_map.get((shard_id, old_planned_tc_id))
    if new_planned_tc_id is None:
        raise SemanticDesignShardingError(
            "oracle projected TC is absent from the merge map"
        )
    item["planned_tc_or_gap"] = new_planned_tc_id


def merge_semantic_shards(
    context: Mapping[str, Any],
    boundary: Mapping[str, Any],
    clarifications: Sequence[Mapping[str, Any]],
    plan: Mapping[str, Any],
    shard_outputs: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Merge independently strict shard designs and validate the full contract."""

    _validate_plan_binding(context, boundary, plan)
    if plan.get("mode") != "sharded":
        raise SemanticDesignShardingError("merge requires a sharded plan")
    shards = plan.get("shards")
    if not isinstance(shards, list) or not shards:
        raise SemanticDesignShardingError("semantic shard plan has no shards")
    expected_ids = [str(item.get("shard_id", "")) for item in shards if isinstance(item, Mapping)]
    if set(shard_outputs) != set(expected_ids):
        missing = sorted(set(expected_ids) - set(shard_outputs))
        extra = sorted(set(shard_outputs) - set(expected_ids))
        raise SemanticDesignShardingError(
            f"semantic shard output set mismatch: missing={missing}, extra={extra}"
        )

    projected: dict[str, tuple[dict[str, Any], dict[str, Any], tuple[dict[str, Any], ...]]] = {}
    full_clarifications = tuple(copy.deepcopy(dict(item)) for item in clarifications)
    for shard in shards:
        assert isinstance(shard, Mapping)
        shard_id = str(shard["shard_id"])
        shard_context, shard_boundary = project_semantic_shard(context, boundary, shard)
        shard_clarifications = tuple(
            copy.deepcopy(dict(item))
            for item in shard_context.get("approved_clarifications", [])
            if isinstance(item, Mapping)
        )
        validate_semantic_design_binding(
            shard_context,
            shard_boundary,
            shard_outputs[shard_id],
            clarifications=shard_clarifications,
            require_ready=True,
        )
        projected[shard_id] = (shard_context, shard_boundary, shard_clarifications)

    global_rows = [str(row.get("source_row_id", "")) for row in context.get("source_rows", []) if isinstance(row, Mapping)]
    owned_by_shard = {
        str(shard["shard_id"]): set(map(str, shard["owned_source_row_ids"]))
        for shard in shards
        if isinstance(shard, Mapping)
    }
    source_design_by_row: dict[str, tuple[str, dict[str, Any]]] = {}
    for shard_id in expected_ids:
        owned = owned_by_shard[shard_id]
        for source_design in shard_outputs[shard_id].get("source_designs", []):
            if not isinstance(source_design, Mapping):
                continue
            row_id = str(source_design.get("source_row_id", ""))
            if row_id in owned:
                if row_id in source_design_by_row:
                    raise SemanticDesignShardingError(f"duplicate owned source design {row_id}")
                source_design_by_row[row_id] = (shard_id, copy.deepcopy(dict(source_design)))
    if set(source_design_by_row) != set(global_rows):
        missing = [row_id for row_id in global_rows if row_id not in source_design_by_row]
        raise SemanticDesignShardingError("merged source designs are incomplete: " + ", ".join(missing))

    assertion_map: dict[tuple[str, str], str] = {}
    atom_map: dict[tuple[str, str], str] = {}
    assertion_index = 0
    source_designs: list[dict[str, Any]] = []
    for row_id in global_rows:
        shard_id, source_design = source_design_by_row[row_id]
        for assertion in source_design.get("assertions", []):
            assertion_index += 1
            old_assertion = str(assertion["assertion_id"])
            old_atom = str(assertion["atom_id"])
            assertion_map[(shard_id, old_assertion)] = f"ASSERT-{assertion_index:03d}"
            atom_map[(shard_id, old_atom)] = f"ATOM-{assertion_index:03d}"
            assertion["assertion_id"] = assertion_map[(shard_id, old_assertion)]
            assertion["atom_id"] = atom_map[(shard_id, old_atom)]
        source_designs.append(source_design)

    obligation_map: dict[tuple[str, str], str] = {}
    tc_map: dict[tuple[str, str], str] = {}
    selected_obligations: list[tuple[str, dict[str, Any]]] = []
    obligation_by_key = {
        (shard_id, str(raw.get("obligation_id", ""))): raw
        for shard_id in expected_ids
        for raw in shard_outputs[shard_id].get("obligations", [])
        if isinstance(raw, Mapping)
    }
    ordered_obligation_keys: list[tuple[str, str]] = []
    for row_id in global_rows:
        shard_id = source_design_by_row[row_id][0]
        source_design = next(
            item for item in source_designs if item["source_row_id"] == row_id
        )
        for assertion in source_design.get("assertions", []):
            ordered_obligation_keys.extend(
                (shard_id, str(value))
                for value in assertion.get("obligation_ids", [])
            )
    if len(ordered_obligation_keys) != len(set(ordered_obligation_keys)):
        raise SemanticDesignShardingError("owned assertions reference duplicate obligations")
    for shard_id, old_obligation in ordered_obligation_keys:
        raw = obligation_by_key.get((shard_id, old_obligation))
        if not isinstance(raw, Mapping):
            raise SemanticDesignShardingError(
                f"owned assertion references missing obligation {old_obligation}"
            )
        obligation = copy.deepcopy(dict(raw))
        old_tc = str(obligation["planned_tc_id"])
        index = len(selected_obligations) + 1
        obligation_map[(shard_id, old_obligation)] = f"OBL-{index:03d}"
        tc_map[(shard_id, old_tc)] = f"TC-{index:03d}"
        selected_obligations.append((shard_id, obligation))

    full_preflight = validate_semantic_input_preflight(context, boundary, full_clarifications)
    full_signal_registry = semantic_source_signal_registry(context, boundary)
    shard_signal_maps: dict[str, dict[str, dict[str, str]]] = {}
    dictionary_map: dict[tuple[str, str], str] = {}
    full_dictionary_by_name = {
        str(item["dictionary_name"]): item
        for item in full_preflight.get("dictionary_registry", [])
        if isinstance(item, Mapping)
    }
    for shard_id in expected_ids:
        shard_context, shard_boundary, shard_clarifications = projected[shard_id]
        shard_preflight = validate_semantic_input_preflight(
            shard_context, shard_boundary, shard_clarifications
        )
        shard_registry = semantic_source_signal_registry(shard_context, shard_boundary)
        shard_signal_maps[shard_id] = {
            kind: _signal_mapping(full_signal_registry, shard_registry, kind=kind)
            for kind in ("negative", "requiredness")
        }
        local_registry = {
            str(item["dictionary_id"]): item
            for item in shard_preflight.get("dictionary_registry", [])
            if isinstance(item, Mapping)
        }
        for local_id, item in local_registry.items():
            name = str(item["dictionary_name"])
            if name not in full_dictionary_by_name:
                raise SemanticDesignShardingError(f"unknown projected dictionary {name}")
            dictionary_map[(shard_id, local_id)] = str(full_dictionary_by_name[name]["dictionary_id"])

    shard_reset_lifecycle_by_obligation = {
        (shard_id, str(item.get("obligation_id", ""))): item
        for shard_id in expected_ids
        for item in shard_outputs[shard_id].get("reset_lifecycle_bindings", [])
        if isinstance(item, Mapping)
    }
    obligations: list[dict[str, Any]] = []
    reset_lifecycle_bindings: list[dict[str, Any]] = []
    for shard_id, obligation in selected_obligations:
        old_obligation = str(obligation["obligation_id"])
        old_atom = str(obligation["linked_atom_id"])
        old_tc = str(obligation["planned_tc_id"])
        obligation["obligation_id"] = obligation_map[(shard_id, old_obligation)]
        obligation["linked_atom_id"] = atom_map[(shard_id, old_atom)]
        obligation["planned_tc_id"] = tc_map[(shard_id, old_tc)]
        obligation["dictionary_refs"] = [
            dictionary_map[(shard_id, str(value))]
            for value in obligation.get("dictionary_refs", [])
        ]
        scope_map = {
            "SO-" + old.removeprefix("SIG-"): "SO-" + new.removeprefix("SIG-")
            for kind_map in shard_signal_maps[shard_id].values()
            for old, new in kind_map.items()
        }
        obligation["scope_obligation_ids"] = [
            scope_map.get(str(value), str(value))
            for value in obligation.get("scope_obligation_ids", [])
        ]
        obligations.append(obligation)
        reset_lifecycle_binding = shard_reset_lifecycle_by_obligation.get(
            (shard_id, old_obligation)
        )
        if reset_lifecycle_binding is not None:
            remapped_binding = copy.deepcopy(dict(reset_lifecycle_binding))
            remapped_binding["obligation_id"] = obligation_map[
                (shard_id, old_obligation)
            ]
            reset_lifecycle_bindings.append(remapped_binding)
    for source_design in source_designs:
        row_id = str(source_design["source_row_id"])
        shard_id = source_design_by_row[row_id][0]
        for assertion in source_design.get("assertions", []):
            assertion["obligation_ids"] = [
                obligation_map[(shard_id, str(value))]
                for value in assertion.get("obligation_ids", [])
            ]

    dependency_parts: dict[str, list[tuple[str, Mapping[str, Any]]]] = defaultdict(list)
    for shard_id in expected_ids:
        for binding in shard_outputs[shard_id].get("dependency_bindings", []):
            if isinstance(binding, Mapping):
                dependency_parts[str(binding.get("dependency_id"))].append((shard_id, binding))
    dependency_bindings: list[dict[str, Any]] = []
    for dependency in boundary.get("dependencies", []):
        if not isinstance(dependency, Mapping):
            continue
        dependency_id = str(dependency["dependency_id"])
        parts = dependency_parts.get(dependency_id, [])
        if not parts:
            raise SemanticDesignShardingError(f"missing dependency binding {dependency_id}")
        dispositions = {str(part.get("semantic_disposition")) for _sid, part in parts}
        if dispositions.issubset({"bound", "gap-bound"}) and "bound" in dispositions:
            merged_disposition = "bound"
            executable_parts = [
                (sid, part)
                for sid, part in parts
                if part.get("semantic_disposition") == "bound"
            ]
        elif len(dispositions) == 1:
            merged_disposition = next(iter(dispositions))
            executable_parts = parts
        else:
            raise SemanticDesignShardingError(f"inconsistent dependency disposition {dependency_id}")
        dependency_bindings.append(
            {
                **copy.deepcopy(dict(dependency)),
                "semantic_disposition": merged_disposition,
                "linked_assertion_ids": _ordered_unique(
                    [assertion_map[(sid, str(value))] for sid, part in executable_parts for value in part.get("linked_assertion_ids", []) if (sid, str(value)) in assertion_map]
                ),
                "linked_atom_ids": _ordered_unique(
                    [atom_map[(sid, str(value))] for sid, part in executable_parts for value in part.get("linked_atom_ids", []) if (sid, str(value)) in atom_map]
                ),
                "linked_obligation_ids": _ordered_unique(
                    [obligation_map[(sid, str(value))] for sid, part in executable_parts for value in part.get("linked_obligation_ids", []) if (sid, str(value)) in obligation_map]
                ),
                "mapping_rationale": " | ".join(
                    _ordered_unique([str(part.get("mapping_rationale", "")) for _sid, part in parts])
                ),
            }
        )

    dictionaries: list[dict[str, Any]] = []
    for full_dictionary in full_preflight.get("dictionary_registry", []):
        if not isinstance(full_dictionary, Mapping):
            continue
        name = str(full_dictionary["dictionary_name"])
        candidates = [
            copy.deepcopy(dict(item))
            for shard_id in expected_ids
            for item in shard_outputs[shard_id].get("dictionaries", [])
            if isinstance(item, Mapping)
            and dictionary_map.get((shard_id, str(item.get("dictionary_id"))))
            == full_dictionary["dictionary_id"]
        ]
        if not candidates:
            raise SemanticDesignShardingError(f"missing merged dictionary {name}")
        if any(
            item.get("active_values") != full_dictionary.get("active_values")
            or item.get("archived_values") != full_dictionary.get("archived_values")
            for item in candidates
        ):
            raise SemanticDesignShardingError(f"dictionary values drifted across shards: {name}")
        item = candidates[0]
        item["dictionary_id"] = full_dictionary["dictionary_id"]
        item["dictionary_name"] = name
        item["source_row_ids"] = copy.deepcopy(full_dictionary["source_row_ids"])
        item["active_values"] = copy.deepcopy(full_dictionary["active_values"])
        item["archived_values"] = copy.deepcopy(full_dictionary["archived_values"])
        dictionaries.append(item)

    negative_oracles: list[dict[str, Any]] = []
    for shard_id in expected_ids:
        signal_map = shard_signal_maps[shard_id]["negative"]
        for raw in shard_outputs[shard_id].get("negative_oracles", []):
            if not isinstance(raw, Mapping):
                continue
            item = copy.deepcopy(dict(raw))
            old_signal = str(item["signal_id"])
            if old_signal not in signal_map:
                raise SemanticDesignShardingError("unknown projected negative signal")
            new_signal = signal_map[old_signal]
            item["signal_id"] = new_signal
            item["scope_obligation_id"] = "SO-" + new_signal.removeprefix("SIG-")
            old_linked_obligation_id = str(item["linked_obligation_id"])
            _remap_oracle_planned_route(
                item,
                shard_id=shard_id,
                new_scope_obligation_id=str(item["scope_obligation_id"]),
                old_linked_obligation_id=old_linked_obligation_id,
                obligation_by_key=obligation_by_key,
                tc_map=tc_map,
            )
            item["linked_atom_id"] = atom_map[(shard_id, str(item["linked_atom_id"]))]
            item["linked_obligation_id"] = obligation_map[
                (shard_id, old_linked_obligation_id)
            ]
            negative_oracles.append(item)
    requiredness_oracles: list[dict[str, Any]] = []
    for shard_id in expected_ids:
        signal_map = shard_signal_maps[shard_id]["requiredness"]
        for raw in shard_outputs[shard_id].get("requiredness_oracles", []):
            if not isinstance(raw, Mapping):
                continue
            item = copy.deepcopy(dict(raw))
            old_signal = str(item["signal_id"])
            if old_signal not in signal_map:
                raise SemanticDesignShardingError("unknown projected requiredness signal")
            new_signal = signal_map[old_signal]
            item["signal_id"] = new_signal
            item["scope_obligation_id"] = "SO-" + new_signal.removeprefix("SIG-")
            old_linked_obligation_id = str(item["linked_obligation_id"])
            _remap_oracle_planned_route(
                item,
                shard_id=shard_id,
                new_scope_obligation_id=str(item["scope_obligation_id"]),
                old_linked_obligation_id=old_linked_obligation_id,
                obligation_by_key=obligation_by_key,
                tc_map=tc_map,
            )
            item["linked_atom_id"] = atom_map[(shard_id, str(item["linked_atom_id"]))]
            item["linked_obligation_id"] = obligation_map[
                (shard_id, old_linked_obligation_id)
            ]
            requiredness_oracles.append(item)
    negative_oracles = _order_oracles_by_signal_registry(
        negative_oracles,
        full_signal_registry["negative"],
        kind="negative",
    )
    requiredness_oracles = _order_oracles_by_signal_registry(
        requiredness_oracles,
        full_signal_registry["requiredness"],
        kind="requiredness",
    )

    applicability: list[dict[str, Any]] = []
    for dimension in APPLICABILITY_DIMENSIONS:
        parts = [
            (shard_id, item)
            for shard_id in expected_ids
            for item in shard_outputs[shard_id].get("applicability", [])
            if isinstance(item, Mapping) and item.get("dimension") == dimension
        ]
        atoms = _ordered_unique([
            atom_map[(shard_id, str(value))]
            for shard_id, item in parts
            for value in item.get("linked_atoms", [])
            if (shard_id, str(value)) in atom_map
        ])
        test_cases = _ordered_unique([
            tc_map[(shard_id, str(value))]
            for shard_id, item in parts
            for value in item.get("linked_test_cases", [])
            if (shard_id, str(value)) in tc_map
        ])
        yes_parts = [item for _sid, item in parts if item.get("applicable") == "yes"]
        applicability.append(
            {
                "dimension": dimension,
                "applicable": "yes" if yes_parts else "no",
                "source_ref": " | ".join(_ordered_unique([str(item.get("source_ref", "")) for item in yes_parts])) if yes_parts else "none_required",
                "reason": " | ".join(_ordered_unique([str(item.get("reason", "")) for item in (yes_parts or [item for _sid, item in parts])])),
                "linked_atoms": atoms,
                "linked_test_cases": test_cases,
            }
        )

    merged = {
        "version": SEMANTIC_DESIGN_VERSION,
        "contract": SEMANTIC_DESIGN_CONTRACT,
        "status": "ready",
        "blocking_reason": "none_required",
        "prepared_context_sha256": prepared_context_sha256(context),
        "scope_boundary_decision_sha256": canonical_payload_sha256(boundary),
        "scope_summary": boundary["scope_summary"],
        "included": copy.deepcopy(boundary["scope_boundary"]["include"]),
        "excluded": copy.deepcopy(boundary["scope_boundary"]["exclude"]),
        "mockup_locators": copy.deepcopy(boundary["mockup_locators"]),
        "source_designs": source_designs,
        "obligations": obligations,
        "reset_lifecycle_bindings": reset_lifecycle_bindings,
        "dependency_bindings": dependency_bindings,
        "dictionaries": dictionaries,
        "negative_oracles": negative_oracles,
        "requiredness_oracles": requiredness_oracles,
        "applicability": applicability,
    }
    receipt = validate_semantic_design_binding(
        context,
        boundary,
        merged,
        clarifications=full_clarifications,
        require_ready=True,
    )
    return merged, {
        "version": 1,
        "contract": "semantic-design-shard-merge-receipt-v1",
        "status": "verified",
        "plan_sha256": plan["plan_sha256"],
        "semantic_design_sha256": canonical_payload_sha256(merged),
        "shard_count": len(expected_ids),
        "validation": receipt,
    }


__all__ = [
    "DETERMINISTIC_NON_TESTABLE_EXECUTION_MODE",
    "MODEL_EXECUTION_MODE",
    "SemanticDesignShardingError",
    "build_semantic_shard_plan",
    "materialize_non_testable_semantic_shard",
    "merge_semantic_shards",
    "project_semantic_shard",
    "rebind_semantic_shard_plan_ownership",
    "semantic_complexity_profile",
]
