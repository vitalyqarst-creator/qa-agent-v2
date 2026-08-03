from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT_DIR / "references" / "agent" / "instruction-loading-manifest.md"

MANIFEST_RE = re.compile(
    r"<!--\s*instruction-loading-manifest:v1\s*-->\s*```json\s*(.*?)\s*```",
    re.DOTALL,
)
DEFAULT_MIN_HEADROOM_KIB = 15.0
SCENARIO_MIN_HEADROOM_KIB = {
    "iteration.full_loop": 30.0,
    "writer.initial_draft.table": 30.0,
    "writer.remediation.style": 30.0,
    "writer.remediation.validator_failure": 30.0,
}


@dataclass(frozen=True)
class FileStat:
    path: str
    bytes: int
    kib: float
    lines: int
    group: str
    category: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve the instruction files for an agent pipeline scenario."
    )
    parser.add_argument("--root", type=Path, default=ROOT_DIR)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--scenario", help="Scenario id from instruction-loading-manifest.md.")
    parser.add_argument("--phase", help="Pipeline phase, e.g. writer, scope, iteration.")
    parser.add_argument("--mode", help="Scenario mode, e.g. initial_draft or full_loop.")
    parser.add_argument(
        "--scope-profile",
        default="any",
        help="Scope profile, e.g. simple, table, ui, any.",
    )
    parser.add_argument("--json", action="store_true", dest="json_only")
    parser.add_argument(
        "--budget-report",
        action="store_true",
        help="Include budget status in text output. JSON always includes it.",
    )
    parser.add_argument(
        "--fail-on-budget",
        action="store_true",
        help="Return a non-zero exit code when the selected scenario exceeds its budget.",
    )
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="List available scenario ids and exit.",
    )
    return parser.parse_args()


def manifest_path(root: Path, explicit: Path | None = None) -> Path:
    if explicit is not None:
        return explicit if explicit.is_absolute() else root / explicit
    return root / "references" / "agent" / "instruction-loading-manifest.md"


def load_manifest(root: Path = ROOT_DIR, explicit: Path | None = None) -> dict[str, Any]:
    path = manifest_path(root, explicit)
    content = path.read_text(encoding="utf-8")
    match = MANIFEST_RE.search(content)
    if not match:
        raise ValueError(f"Manifest JSON block not found in {path}")
    payload = json.loads(match.group(1))
    if payload.get("version") != 1:
        raise ValueError(f"Unsupported manifest version in {path}: {payload.get('version')}")
    return payload


def scenario_matches(
    scenario: dict[str, Any],
    *,
    phase: str | None,
    mode: str | None,
    scope_profile: str,
) -> bool:
    if phase and scenario.get("phase") != phase:
        return False
    if mode and scenario.get("mode") != mode:
        return False
    expected_profile = scenario.get("scope_profile", "any")
    return expected_profile == "any" or expected_profile == scope_profile


def find_scenario(
    manifest: dict[str, Any],
    *,
    scenario_id: str | None = None,
    phase: str | None = None,
    mode: str | None = None,
    scope_profile: str = "any",
) -> dict[str, Any]:
    scenarios = manifest.get("scenarios", [])
    if scenario_id:
        matches = [item for item in scenarios if item.get("id") == scenario_id]
    else:
        matches = [
            item
            for item in scenarios
            if scenario_matches(
                item,
                phase=phase,
                mode=mode,
                scope_profile=scope_profile,
            )
        ]
    if not matches:
        raise ValueError("No matching instruction-loading scenario found.")
    if len(matches) > 1:
        ids = ", ".join(item["id"] for item in matches)
        raise ValueError(f"Instruction-loading scenario is ambiguous: {ids}")
    return matches[0]


def group_paths(manifest: dict[str, Any], group_name: str) -> list[str]:
    groups = manifest.get("groups", {})
    group = groups.get(group_name)
    if group is None:
        raise ValueError(f"Unknown instruction group: {group_name}")
    paths = group.get("paths", [])
    if not isinstance(paths, list):
        raise ValueError(f"Instruction group {group_name} has invalid paths.")
    return paths


def collect_paths(
    manifest: dict[str, Any],
    scenario: dict[str, Any],
    category_key: str,
    category: str,
) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for group_name in scenario.get(category_key, []):
        for path in group_paths(manifest, group_name):
            rows.append((path, group_name, category))
    return rows


def path_stats(root: Path, path: str, group: str, category: str) -> FileStat:
    target = root / path
    data = target.read_bytes()
    text = data.decode("utf-8")
    line_count = text.count("\n") + (0 if text.endswith("\n") or text == "" else 1)
    return FileStat(
        path=path,
        bytes=len(data),
        kib=round(len(data) / 1024, 1),
        lines=line_count,
        group=group,
        category=category,
    )


def min_headroom_for_scenario(scenario_id: str) -> float:
    return SCENARIO_MIN_HEADROOM_KIB.get(scenario_id, DEFAULT_MIN_HEADROOM_KIB)


def budget_status(total_kib: float, limit_kib: float, min_headroom_kib: float) -> str:
    if total_kib > limit_kib:
        return "fail"
    if round(limit_kib - total_kib, 1) < min_headroom_kib:
        return "near_limit"
    return "pass"


def group_budget_summary(files: list[FileStat]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for item in files:
        row = groups.setdefault(
            item.group,
            {"group": item.group, "category": item.category, "files_count": 0, "bytes": 0, "lines": 0},
        )
        row["files_count"] += 1
        row["bytes"] += item.bytes
        row["lines"] += item.lines
    result = []
    for row in groups.values():
        result.append(
            {
                "group": row["group"],
                "category": row["category"],
                "files_count": row["files_count"],
                "bytes": row["bytes"],
                "kib": round(row["bytes"] / 1024, 1),
                "lines": row["lines"],
            }
        )
    return sorted(result, key=lambda item: (-item["bytes"], item["group"]))


def resolve_instruction_context(
    *,
    root: Path = ROOT_DIR,
    manifest: dict[str, Any] | None = None,
    scenario_id: str | None = None,
    phase: str | None = None,
    mode: str | None = None,
    scope_profile: str = "any",
) -> dict[str, Any]:
    root = root.resolve()
    manifest = manifest or load_manifest(root)
    scenario = find_scenario(
        manifest,
        scenario_id=scenario_id,
        phase=phase,
        mode=mode,
        scope_profile=scope_profile,
    )

    selected_rows = collect_paths(manifest, scenario, "required_groups", "required")
    conditional_rows = collect_paths(manifest, scenario, "conditional_groups", "conditional_skipped")
    audit_only_rows = collect_paths(manifest, scenario, "audit_only_groups", "audit_only_skipped")

    seen: set[str] = set()
    selected_stats: list[FileStat] = []
    duplicates: list[str] = []
    missing: list[str] = []
    for path, group, category in selected_rows:
        if path in seen:
            duplicates.append(path)
            continue
        seen.add(path)
        if not (root / path).exists():
            missing.append(path)
            continue
        selected_stats.append(path_stats(root, path, group, category))

    skipped = []
    for path, group, category in conditional_rows + audit_only_rows:
        skipped.append({"path": path, "group": group, "category": category})

    total_bytes = sum(item.bytes for item in selected_stats)
    total_kib = round(total_bytes / 1024, 1)
    total_lines = sum(item.lines for item in selected_stats)
    budget_limit = float(scenario["budget_limit_kib"])
    min_headroom_kib = min_headroom_for_scenario(scenario["id"])
    headroom_kib = round(budget_limit - total_kib, 1)
    headroom_percent = round((headroom_kib / budget_limit) * 100, 1) if budget_limit else 0.0
    status = budget_status(total_kib, budget_limit, min_headroom_kib)
    top_files = sorted(selected_stats, key=lambda item: item.bytes, reverse=True)[:10]

    return {
        "scenario": scenario["id"],
        "phase": scenario.get("phase"),
        "mode": scenario.get("mode"),
        "scope_profile": scenario.get("scope_profile"),
        "rationale": scenario.get("rationale", ""),
        "budget": {
            "total_bytes": total_bytes,
            "total_kib": total_kib,
            "total_lines": total_lines,
            "limit_kib": budget_limit,
            "headroom_kib": headroom_kib,
            "headroom_percent": headroom_percent,
            "min_headroom_kib": min_headroom_kib,
            "status": status,
            "baseline": manifest.get("baseline", {}),
        },
        "groups": group_budget_summary(selected_stats),
        "top_files": [item.__dict__ for item in top_files],
        "files": [item.__dict__ for item in selected_stats],
        "skipped": skipped,
        "duplicates": duplicates,
        "missing": missing,
    }


def list_scenarios(manifest: dict[str, Any]) -> str:
    lines = ["Instruction-loading scenarios:"]
    for scenario in manifest.get("scenarios", []):
        lines.append(
            f"- {scenario['id']} "
            f"(phase={scenario.get('phase')}, mode={scenario.get('mode')}, "
            f"profile={scenario.get('scope_profile')}, limit={scenario.get('budget_limit_kib')} KiB)"
        )
    return "\n".join(lines)


def text_report(result: dict[str, Any], *, include_budget: bool = False) -> str:
    budget = result["budget"]
    lines = [
        f"Instruction context: {result['scenario']}",
        f"- phase: {result['phase']}",
        f"- mode: {result['mode']}",
        f"- scope_profile: {result['scope_profile']}",
        f"- files: {len(result['files'])}",
        f"- total: {budget['total_kib']} KiB ({budget['total_bytes']} bytes), lines: {budget['total_lines']}",
    ]
    if include_budget:
        lines.append(
            f"- budget: {budget['status']} ({budget['total_kib']} / {budget['limit_kib']} KiB, "
            f"headroom {budget['headroom_kib']} KiB / min {budget['min_headroom_kib']} KiB, "
            f"{budget['headroom_percent']}%)"
        )
        lines.append("- groups:")
        for item in result["groups"]:
            lines.append(
                f"  - {item['group']}: {item['kib']} KiB, {item['files_count']} files"
            )
        lines.append("- top files:")
        for item in result["top_files"][:5]:
            lines.append(
                f"  - {item['path']} ({item['kib']} KiB, group={item['group']})"
            )
    if result["missing"]:
        lines.append(f"- missing: {', '.join(result['missing'])}")
    if result["duplicates"]:
        lines.append(f"- duplicates skipped: {', '.join(result['duplicates'])}")
    lines.append("- selected files:")
    for item in result["files"]:
        lines.append(
            f"  - [{item['category']}] {item['path']} "
            f"({item['kib']} KiB, group={item['group']})"
        )
    skipped_count = len(result["skipped"])
    if skipped_count:
        lines.append(f"- skipped conditional/audit-only files: {skipped_count}")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    manifest = load_manifest(root, args.manifest)
    if args.list_scenarios:
        print(list_scenarios(manifest))
        return 0

    try:
        result = resolve_instruction_context(
            root=root,
            manifest=manifest,
            scenario_id=args.scenario,
            phase=args.phase,
            mode=args.mode,
            scope_profile=args.scope_profile,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.json_only:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(text_report(result, include_budget=args.budget_report))

    if result["missing"]:
        return 2
    if args.fail_on_budget and result["budget"]["status"] != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
