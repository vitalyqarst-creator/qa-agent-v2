from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SHORT_TEXT_LIMIT = 180
TOP_GROUPS_LIMIT = 20
SHORT_MARKER_TEXTS = {
    "\u041e",
    "O",
    "\u0420",
    "P",
    "\u0414\u0430",
    "\u041d\u0435\u0442",
    "true",
    "false",
    "0",
    "1",
}
DIFF_ELIGIBLE_STATUSES = {"active", "gap", "unclear"}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect duplicate req_uid groups in a requirements registry JSONL artifact."
    )
    parser.add_argument("--registry", required=True, type=Path, help="requirements.<version>.jsonl")
    parser.add_argument("--out-json", required=True, type=Path, help="Output duplicate diagnostics JSON.")
    parser.add_argument("--out-md", required=True, type=Path, help="Output duplicate diagnostics Markdown.")
    parser.add_argument("--out-diff-eligible-json", type=Path, help="Output diff-eligible duplicate diagnostics JSON.")
    parser.add_argument("--out-diff-eligible-md", type=Path, help="Output diff-eligible duplicate diagnostics Markdown.")
    parser.add_argument(
        "--top",
        type=int,
        default=TOP_GROUPS_LIMIT,
        help=f"Number of top duplicate groups to include. Default: {TOP_GROUPS_LIMIT}.",
    )
    args = parser.parse_args()

    report = inspect_registry_duplicates(args.registry, top_limit=args.top)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    args.out_md.write_text(render_markdown(report), encoding="utf-8", newline="\n")
    diff_eligible_report = diff_eligible_only_report(report)
    out_diff_json = args.out_diff_eligible_json or _default_diff_eligible_path(args.out_json)
    out_diff_md = args.out_diff_eligible_md or _default_diff_eligible_path(args.out_md)
    out_diff_json.write_text(
        json.dumps(diff_eligible_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    out_diff_md.write_text(render_markdown(diff_eligible_report), encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "registry": str(args.registry),
                "out_json": str(args.out_json),
                "out_md": str(args.out_md),
                "out_diff_eligible_json": str(out_diff_json),
                "out_diff_eligible_md": str(out_diff_md),
                "duplicate_groups_total": report["statistics"]["duplicate_groups_total"],
                "duplicate_entries_total": report["statistics"]["duplicate_entries_total"],
                "duplicate_entry_uid_count": report["statistics"]["duplicate_entry_uid_count"],
                "diff_eligible_duplicate_groups_total": report["statistics"]["diff_eligible_duplicate_groups_total"],
                "remaining_duplicate_groups_excluding_source_only": report["recommendations"][
                    "remaining_duplicate_groups_excluding_source_only"
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def inspect_registry_duplicates(registry_path: Path, *, top_limit: int = TOP_GROUPS_LIMIT) -> dict[str, Any]:
    entries = _load_jsonl(registry_path)
    groups = _groups_by(entries, "req_uid")
    duplicate_groups = _duplicate_groups(groups)
    source_only_duplicate_groups = _duplicate_groups(_groups_by([entry for entry in entries if not _is_diff_eligible(entry)], "req_uid"))
    diff_eligible_duplicate_groups = _duplicate_groups(_groups_by([entry for entry in entries if _is_diff_eligible(entry)], "req_uid"))
    active_gap_unclear_duplicate_groups = _duplicate_groups(_groups_by([entry for entry in entries if entry.get("status") in DIFF_ELIGIBLE_STATUSES], "req_uid"))
    duplicate_entry_uid_groups = _duplicate_groups(_groups_by(entries, "entry_uid"))
    duplicate_entries = [entry for group in duplicate_groups.values() for entry in group]
    top_groups = [
        _group_summary(req_uid, group)
        for req_uid, group in sorted(
            duplicate_groups.items(),
            key=lambda item: (-len(item[1]), item[0]),
        )[:top_limit]
    ]

    statistics = {
        "registry_path": str(registry_path),
        "source_version": _source_version(entries, registry_path),
        "entries_total": len(entries),
        "unique_req_uid_count": len(groups),
        "duplicate_req_uid_count": len(duplicate_groups),
        "duplicate_entries_total": len(duplicate_entries),
        "duplicate_groups_total": len(duplicate_groups),
        "source_only_duplicate_groups_total": len(source_only_duplicate_groups),
        "source_only_duplicate_entries_total": sum(len(group) for group in source_only_duplicate_groups.values()),
        "diff_eligible_duplicate_groups_total": len(diff_eligible_duplicate_groups),
        "diff_eligible_duplicate_entries_total": sum(len(group) for group in diff_eligible_duplicate_groups.values()),
        "active_gap_unclear_duplicate_groups_total": len(active_gap_unclear_duplicate_groups),
        "active_gap_unclear_duplicate_entries_total": sum(len(group) for group in active_gap_unclear_duplicate_groups.values()),
        "duplicate_entry_uid_count": len(duplicate_entry_uid_groups),
        "duplicate_entry_uids": sorted(duplicate_entry_uid_groups),
    }
    categories = _category_counts(duplicate_groups)
    remaining = _remaining_duplicate_counts(entries)
    recommendations = _recommendations(statistics, categories, remaining)
    return {
        "statistics": statistics,
        "breakdown": _breakdown(duplicate_groups),
        "categories": categories,
        "top_duplicate_groups": top_groups,
        "top_diff_eligible_duplicate_groups": [
            _group_summary(req_uid, group)
            for req_uid, group in sorted(
                diff_eligible_duplicate_groups.items(),
                key=lambda item: (-len(item[1]), item[0]),
            )[:top_limit]
        ],
        "top_duplicate_entry_uid_groups": [
            _entry_uid_group_summary(entry_uid, group)
            for entry_uid, group in sorted(
                duplicate_entry_uid_groups.items(),
                key=lambda item: (-len(item[1]), item[0]),
            )[:top_limit]
        ],
        "recommendations": recommendations,
    }


def diff_eligible_only_report(report: dict[str, Any]) -> dict[str, Any]:
    statistics = dict(report["statistics"])
    statistics["duplicate_req_uid_count"] = statistics["diff_eligible_duplicate_groups_total"]
    statistics["duplicate_groups_total"] = statistics["diff_eligible_duplicate_groups_total"]
    statistics["duplicate_entries_total"] = statistics["diff_eligible_duplicate_entries_total"]
    return {
        "statistics": statistics,
        "breakdown": report["breakdown"].get("diff_eligible", {}),
        "categories": {
            "diff_eligible_duplicate_groups_total": statistics["diff_eligible_duplicate_groups_total"],
            "active_gap_unclear_duplicate_groups_total": statistics["active_gap_unclear_duplicate_groups_total"],
        },
        "top_duplicate_groups": report["top_diff_eligible_duplicate_groups"],
        "top_diff_eligible_duplicate_groups": report["top_diff_eligible_duplicate_groups"],
        "top_duplicate_entry_uid_groups": report["top_duplicate_entry_uid_groups"],
        "recommendations": report["recommendations"],
    }


def render_markdown(report: dict[str, Any]) -> str:
    stats = report["statistics"]
    categories = report["categories"]
    recommendations = report["recommendations"]
    lines = [
        "# Requirements Duplicate Diagnostics",
        "",
        "## Summary",
        "",
        f"- Registry: `{stats['registry_path']}`",
        f"- Source version: `{stats['source_version']}`",
        f"- Entries total: `{stats['entries_total']}`",
        f"- Unique req_uid count: `{stats['unique_req_uid_count']}`",
        f"- Duplicate req_uid count: `{stats['duplicate_req_uid_count']}`",
        f"- Duplicate entries total: `{stats['duplicate_entries_total']}`",
        f"- Duplicate groups total: `{stats['duplicate_groups_total']}`",
        f"- Diff-eligible duplicate groups total: `{stats.get('diff_eligible_duplicate_groups_total', 0)}`",
        f"- Duplicate entry_uid count: `{stats.get('duplicate_entry_uid_count', 0)}`",
        "",
        "## Duplicate Group Categories",
        "",
    ]
    for key, value in categories.items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Recommendations", ""])
    for key, value in recommendations.items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Top Duplicate Groups", ""])
    for group in report["top_duplicate_groups"]:
        lines.append(f"### {group['req_uid']}")
        lines.append("")
        lines.append(f"- Count: `{group['count']}`")
        lines.append(f"- Statuses: `{', '.join(group['statuses'])}`")
        lines.append(f"- Requirement types: `{', '.join(group['requirement_types'])}`")
        lines.append(f"- Source req IDs: `{', '.join(group['source_req_ids']) or 'none'}`")
        lines.append(f"- Normalized text sample: {group['normalized_text_sample']}")
        lines.append(f"- Source text sample: {group['source_text_sample']}")
        lines.append(f"- Context sources: `{', '.join(group.get('context_sources', [])) or 'none'}`")
        lines.append(f"- Object samples: `{', '.join(group.get('object_samples', [])) or 'none'}`")
        lines.append(f"- Context text samples: `{'; '.join(group.get('context_text_samples', [])) or 'none'}`")
        lines.append(f"- Likely cause: `{group.get('likely_cause', 'unknown')}`")
        lines.append(f"- Duplicate group category: `{group.get('duplicate_group_category', 'unknown')}`")
        lines.append("")
        lines.append("| part | xpath | node_id | value_type | flags | aggregate_kind |")
        lines.append("|---|---|---|---|---|---|")
        for anchor in group["first_10_anchors"]:
            lines.append(
                "| "
                + " | ".join(
                    _md_cell(str(anchor.get(column) or ""))
                    for column in ["part", "xpath", "node_id", "value_type", "flags", "aggregate_kind"]
                )
                + " |"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"JSONL line {line_number} is not an object: {path}")
            entries.append(payload)
    return entries


def _groups_by(entries: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        value = str(entry.get(key) or "")
        if value:
            groups[value].append(entry)
    return groups


def _duplicate_groups(groups: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    return {key: group for key, group in groups.items() if len(group) > 1}


def _is_diff_eligible(entry: dict[str, Any]) -> bool:
    if "diff_eligible" in entry:
        return bool(entry["diff_eligible"])
    return entry.get("status") != "source_only"


def _source_version(entries: list[dict[str, Any]], registry_path: Path) -> str:
    if entries:
        return str(entries[0].get("source_version") or "unknown")
    stem = registry_path.stem
    prefix = "requirements."
    return stem[len(prefix):] if stem.startswith(prefix) else "unknown"


def _breakdown(duplicate_groups: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    status_values: Counter[str] = Counter()
    status_combinations: Counter[str] = Counter()
    requirement_type_values: Counter[str] = Counter()
    requirement_type_combinations: Counter[str] = Counter()
    part_values: Counter[str] = Counter()
    value_type_values: Counter[str] = Counter()
    flag_values: Counter[str] = Counter()
    flag_combinations: Counter[str] = Counter()
    has_source_req_id: Counter[str] = Counter()
    source_req_id_values: Counter[str] = Counter()

    for group in duplicate_groups.values():
        statuses = _entry_values(group, "status")
        requirement_types = _entry_values(group, "requirement_type")
        source_req_ids = _entry_values(group, "source_req_id", drop_empty=True)
        anchor_values = _anchor_value_sets(group)

        status_values.update(statuses)
        status_combinations[_combo(statuses)] += 1
        requirement_type_values.update(requirement_types)
        requirement_type_combinations[_combo(requirement_types)] += 1
        part_values.update(anchor_values["parts"])
        value_type_values.update(anchor_values["value_types"])
        flag_values.update(anchor_values["flags"])
        flag_combinations[_combo(anchor_values["flags"])] += 1
        has_source_req_id[str(bool(source_req_ids)).lower()] += 1
        source_req_id_values.update(source_req_ids)

    all_breakdown = {
        "by_status": dict(status_values),
        "by_status_combination": dict(status_combinations),
        "by_requirement_type": dict(requirement_type_values),
        "by_requirement_type_combination": dict(requirement_type_combinations),
        "by_part": dict(part_values),
        "by_value_type": dict(value_type_values),
        "by_flags": dict(flag_values),
        "by_flags_combination": dict(flag_combinations),
        "by_has_source_req_id": dict(has_source_req_id),
        "by_source_req_id": dict(source_req_id_values),
    }
    diff_eligible_groups = {
        req_uid: group
        for req_uid, group in duplicate_groups.items()
        if all(_is_diff_eligible(entry) for entry in group)
    }
    if diff_eligible_groups == duplicate_groups:
        return all_breakdown
    return {
        **all_breakdown,
        "diff_eligible": _breakdown(diff_eligible_groups),
    }


def _category_counts(duplicate_groups: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    counts = {
        "source_only_only_groups": 0,
        "groups_with_at_least_one_active": 0,
        "active_gap_unclear_only_groups": 0,
        "same_normalized_text_groups": 0,
        "same_source_req_id_groups": 0,
        "groups_with_different_source_anchors": 0,
        "normalized_text_length_lte_3_groups": 0,
        "short_marker_text_groups": 0,
        "canonicalizable_same_context_groups": 0,
        "unresolved_different_context_groups": 0,
        "unresolved_different_behavior_groups": 0,
        "unresolved_different_status_groups": 0,
        "unresolved_different_type_groups": 0,
        "unknown_duplicate_groups": 0,
    }
    for group in duplicate_groups.values():
        statuses = set(_entry_values(group, "status"))
        normalized_texts = set(_entry_values(group, "normalized_text"))
        source_req_ids = set(_entry_values(group, "source_req_id", drop_empty=True))
        anchor_keys = _anchor_keys(group)

        if statuses == {"source_only"}:
            counts["source_only_only_groups"] += 1
        if "active" in statuses:
            counts["groups_with_at_least_one_active"] += 1
        if statuses and statuses.issubset(DIFF_ELIGIBLE_STATUSES):
            counts["active_gap_unclear_only_groups"] += 1
        if len(normalized_texts) == 1:
            counts["same_normalized_text_groups"] += 1
        if len(source_req_ids) == 1 and all(entry.get("source_req_id") for entry in group):
            counts["same_source_req_id_groups"] += 1
        if len(anchor_keys) > 1:
            counts["groups_with_different_source_anchors"] += 1
        if normalized_texts and all(len(text) <= 3 for text in normalized_texts):
            counts["normalized_text_length_lte_3_groups"] += 1
        if normalized_texts and all(text in SHORT_MARKER_TEXTS for text in normalized_texts):
            counts["short_marker_text_groups"] += 1
        category = _duplicate_group_category(group)
        if category == "canonicalizable_same_context":
            counts["canonicalizable_same_context_groups"] += 1
        elif category == "unresolved_different_context":
            counts["unresolved_different_context_groups"] += 1
        elif category == "unresolved_different_behavior":
            counts["unresolved_different_behavior_groups"] += 1
        elif category == "unresolved_different_status":
            counts["unresolved_different_status_groups"] += 1
        elif category == "unresolved_different_type":
            counts["unresolved_different_type_groups"] += 1
        else:
            counts["unknown_duplicate_groups"] += 1
    return counts


def _remaining_duplicate_counts(entries: list[dict[str, Any]]) -> dict[str, int]:
    non_source_only = [entry for entry in entries if entry.get("status") != "source_only"]
    eligible = [entry for entry in entries if _is_diff_eligible(entry)]
    active = [entry for entry in entries if entry.get("status") == "active"]
    return {
        "remaining_duplicate_groups_excluding_source_only": _duplicate_group_count(non_source_only),
        "remaining_duplicate_entries_excluding_source_only": _duplicate_entry_count(non_source_only),
        "remaining_duplicate_groups_active_gap_unclear": _duplicate_group_count(eligible),
        "remaining_duplicate_entries_active_gap_unclear": _duplicate_entry_count(eligible),
        "remaining_duplicate_groups_active_only": _duplicate_group_count(active),
        "remaining_duplicate_entries_active_only": _duplicate_entry_count(active),
    }


def _recommendations(
    statistics: dict[str, Any],
    categories: dict[str, int],
    remaining: dict[str, int],
) -> dict[str, Any]:
    duplicate_groups = int(statistics["duplicate_groups_total"])
    remaining_without_source_only = remaining["remaining_duplicate_groups_excluding_source_only"]
    active_remaining = remaining["remaining_duplicate_groups_active_gap_unclear"]
    source_only_only = categories["source_only_only_groups"]
    return {
        "can_ignore_source_only_duplicates_in_diff": (
            source_only_only > 0 and remaining_without_source_only < duplicate_groups
        ),
        "source_only_ignore_is_sufficient": remaining_without_source_only == 0,
        "remaining_duplicate_groups_excluding_source_only": remaining_without_source_only,
        "remaining_duplicate_entries_excluding_source_only": remaining[
            "remaining_duplicate_entries_excluding_source_only"
        ],
        "remaining_duplicate_groups_active_gap_unclear": active_remaining,
        "remaining_duplicate_entries_active_gap_unclear": remaining[
            "remaining_duplicate_entries_active_gap_unclear"
        ],
        "remaining_duplicate_groups_active_only": remaining["remaining_duplicate_groups_active_only"],
        "remaining_duplicate_entries_active_only": remaining["remaining_duplicate_entries_active_only"],
        "needs_entry_uid": duplicate_groups > 0,
        "needs_req_uid_generation_improvement": remaining_without_source_only > 0,
        "needs_diff_eligibility_filter": source_only_only > 0,
        "recommended_next_step": (
            "Add a diff eligibility filter for source_only entries and introduce a stable entry_uid; "
            "then improve req_uid generation for remaining active/gap/unclear duplicates."
            if active_remaining > 0
            else "Add a diff eligibility filter for source_only entries and a stable entry_uid before rerunning diff."
        ),
    }


def _group_summary(req_uid: str, group: list[dict[str, Any]]) -> dict[str, Any]:
    anchors = _first_anchors(group, limit=10)
    return {
        "req_uid": req_uid,
        "count": len(group),
        "statuses": _entry_values(group, "status"),
        "requirement_types": _entry_values(group, "requirement_type"),
        "source_req_ids": _entry_values(group, "source_req_id", drop_empty=True),
        "normalized_text_sample": _short(_first_value(group, "normalized_text")),
        "source_text_sample": _short(_first_value(group, "source_text")),
        "context_text_samples": _short_values(group, "context_text", limit=5),
        "context_sources": _entry_values(group, "context_source", drop_empty=True),
        "object_samples": _short_values(group, "object", limit=5),
        "likely_cause": _likely_cause(group),
        "duplicate_group_category": _duplicate_group_category(group),
        "first_10_anchors": anchors,
    }


def _entry_uid_group_summary(entry_uid: str, group: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "entry_uid": entry_uid,
        "count": len(group),
        "req_uids": _entry_values(group, "req_uid"),
        "statuses": _entry_values(group, "status"),
        "requirement_types": _entry_values(group, "requirement_type"),
        "normalized_text_sample": _short(_first_value(group, "normalized_text")),
        "first_10_anchors": _first_anchors(group, limit=10),
    }


def _entry_values(group: list[dict[str, Any]], key: str, *, drop_empty: bool = False) -> list[str]:
    values = sorted(
        {
            str(entry.get(key))
            for entry in group
            if entry.get(key) is not None and (not drop_empty or str(entry.get(key)).strip())
        }
    )
    return values


def _short_values(group: list[dict[str, Any]], key: str, *, limit: int) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for entry in group:
        value = entry.get(key)
        if value is None or not str(value).strip():
            continue
        short_value = _short(str(value))
        if short_value in seen:
            continue
        seen.add(short_value)
        values.append(short_value)
        if len(values) >= limit:
            break
    return values


def _likely_cause(group: list[dict[str, Any]]) -> str:
    normalized_texts = set(_entry_values(group, "normalized_text"))
    context_texts = set(_entry_values(group, "context_text", drop_empty=True))
    source_req_ids = set(_entry_values(group, "source_req_id", drop_empty=True))
    if any(not entry.get("context_text") for entry in group):
        return "missing_context"
    if len(context_texts) == 1:
        return "same_context_repeated"
    if normalized_texts and all(len(text) <= 3 or text in SHORT_MARKER_TEXTS for text in normalized_texts):
        return "short_marker"
    if len(source_req_ids) == 1 and all(entry.get("source_req_id") for entry in group):
        return "same_source_req_id"
    return "unknown"


def _duplicate_group_category(group: list[dict[str, Any]]) -> str:
    if _same_values(group, CANONICALIZABLE_FIELDS):
        return "canonicalizable_same_context"
    if not _same_values(group, ["status"]):
        return "unresolved_different_status"
    if not _same_values(group, ["requirement_type"]):
        return "unresolved_different_type"
    if not _same_values(group, ["normalized_text", "semantic_fingerprint", "expected_behavior"]):
        return "unresolved_different_behavior"
    if not _same_values(group, ["context_hash", "context_text", "object", "condition"]):
        return "unresolved_different_context"
    return "unknown"


CANONICALIZABLE_FIELDS = [
    "req_uid",
    "normalized_text",
    "requirement_type",
    "status",
    "source_req_id",
    "semantic_fingerprint",
    "context_hash",
    "context_text",
    "object",
    "condition",
    "expected_behavior",
]


def _same_values(group: list[dict[str, Any]], keys: list[str]) -> bool:
    for key in keys:
        values = {entry.get(key) for entry in group}
        if len(values) > 1:
            return False
    return True


def _first_value(group: list[dict[str, Any]], key: str) -> str:
    for entry in group:
        value = entry.get(key)
        if value is not None:
            return str(value)
    return ""


def _anchor_value_sets(group: list[dict[str, Any]]) -> dict[str, list[str]]:
    parts: set[str] = set()
    value_types: set[str] = set()
    flags: set[str] = set()
    for entry in group:
        for anchor in entry.get("source_anchors") or []:
            if not isinstance(anchor, dict):
                continue
            if anchor.get("part"):
                parts.add(str(anchor["part"]))
            if anchor.get("value_type"):
                value_types.add(str(anchor["value_type"]))
            for flag in anchor.get("flags") or []:
                flags.add(str(flag))
    return {
        "parts": sorted(parts),
        "value_types": sorted(value_types),
        "flags": sorted(flags),
    }


def _anchor_keys(group: list[dict[str, Any]]) -> set[tuple[str, str, str, str]]:
    keys: set[tuple[str, str, str, str]] = set()
    for entry in group:
        for anchor in entry.get("source_anchors") or []:
            if not isinstance(anchor, dict):
                continue
            keys.add(
                (
                    str(anchor.get("part") or ""),
                    str(anchor.get("xpath") or ""),
                    str(anchor.get("node_id") or ""),
                    str(anchor.get("value_type") or ""),
                )
            )
    return keys


def _first_anchors(group: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    anchors: list[dict[str, Any]] = []
    for entry in group:
        for anchor in entry.get("source_anchors") or []:
            if not isinstance(anchor, dict):
                continue
            anchors.append(
                {
                    "part": anchor.get("part"),
                    "xpath": anchor.get("xpath"),
                    "node_id": anchor.get("node_id"),
                    "value_type": anchor.get("value_type"),
                    "flags": ",".join(str(flag) for flag in anchor.get("flags") or []),
                    "aggregate_kind": anchor.get("aggregate_kind"),
                }
            )
            if len(anchors) >= limit:
                return anchors
    return anchors


def _duplicate_group_count(entries: list[dict[str, Any]]) -> int:
    counts = Counter(str(entry.get("req_uid") or "") for entry in entries)
    return sum(1 for req_uid, count in counts.items() if req_uid and count > 1)


def _duplicate_entry_count(entries: list[dict[str, Any]]) -> int:
    counts = Counter(str(entry.get("req_uid") or "") for entry in entries)
    duplicate_uids = {req_uid for req_uid, count in counts.items() if req_uid and count > 1}
    return sum(1 for entry in entries if str(entry.get("req_uid") or "") in duplicate_uids)


def _combo(values: list[str]) -> str:
    return " + ".join(values) if values else "none"


def _short(text: str) -> str:
    text = " ".join(str(text).split())
    if len(text) <= SHORT_TEXT_LIMIT:
        return text
    return text[: SHORT_TEXT_LIMIT - 3] + "..."


def _md_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _default_diff_eligible_path(path: Path) -> Path:
    name = path.name
    if name.startswith("requirements-duplicates."):
        return path.with_name(name.replace("requirements-duplicates.", "requirements-diff-eligible-duplicates.", 1))
    return path.with_name(f"requirements-diff-eligible-duplicates.{path.name}")


if __name__ == "__main__":
    raise SystemExit(main())
