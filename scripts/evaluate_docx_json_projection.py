from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.compare_docx_json_to_xhtml_baseline import (
    compare_docx_json_to_xhtml_baseline,
)
from test_case_agent.source_json_projection import write_docx_source_json


def _repo_relative(path: Path, repo_root: Path) -> str:
    resolved = path.resolve()
    root = repo_root.resolve()
    return PurePosixPath(*resolved.relative_to(root).parts).as_posix()


def _collect_specs(
    *,
    repo_root: Path,
    specs: list[Path],
    spec_roots: list[Path],
) -> list[Path]:
    result: list[Path] = []
    for spec in specs:
        result.append(spec)
    for root in spec_roots:
        result.extend(sorted(root.rglob("source-row-extraction-spec.json")))
    unique: dict[Path, Path] = {}
    for item in result:
        resolved = item.resolve()
        try:
            resolved.relative_to(repo_root.resolve())
        except ValueError as exc:
            raise ValueError(f"spec path must be under repo root: {item}") from exc
        unique[resolved] = item
    return [unique[key] for key in sorted(unique)]


def _count_match_prefixes(scope_results: list[dict[str, Any]], prefix: str) -> int:
    total = 0
    for item in scope_results:
        if item.get("status") != "evaluated":
            continue
        for match_type, count in item["match_counts"].items():
            if str(match_type).startswith(prefix):
                total += int(count)
    return total


def _aggregate_verdict(scope_results: list[dict[str, Any]]) -> dict[str, Any]:
    evaluated = [item for item in scope_results if item.get("status") == "evaluated"]
    errored = [item for item in scope_results if item.get("status") == "error"]
    missing = sum(int(item["missing_candidate_count"]) for item in evaluated)
    weak = sum(int(item["weak_match_count"]) for item in evaluated)
    order_violations = sum(int(item["order_violations"]) for item in evaluated)
    ambiguous = _count_match_prefixes(evaluated, "ambiguous-")
    code_only = _count_match_prefixes(evaluated, "requirement-code")
    candidate_count = sum(int(item["xhtml_candidate_count"]) for item in evaluated)

    blockers: list[str] = []
    if errored:
        blockers.append("scope-evaluation-errors")
    if len(evaluated) < 3:
        blockers.append("less-than-three-real-scopes")
    if missing:
        blockers.append("missing-xhtml-candidates")
    if order_violations:
        blockers.append("order-violations")
    if ambiguous:
        blockers.append("ambiguous-docx-json-matches")
    if code_only:
        blockers.append("requirement-code-only-matches")

    if blockers:
        verdict = "not-ready-for-production-replacement"
    else:
        verdict = "candidate-for-controlled-production-switch"

    return {
        "verdict": verdict,
        "production_switch_criteria_met": not blockers,
        "blockers": blockers,
        "evaluated_scope_count": len(evaluated),
        "error_scope_count": len(errored),
        "xhtml_candidate_count": candidate_count,
        "missing_candidate_count": missing,
        "weak_match_count": weak,
        "ambiguous_match_count": ambiguous,
        "requirement_code_only_match_count": code_only,
        "order_violations": order_violations,
    }


def _write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# DOCX JSON Projection Evaluation",
        "",
        f"- verdict: `{report['summary']['verdict']}`",
        "- production_switch_criteria_met: "
        f"`{str(report['summary']['production_switch_criteria_met']).lower()}`",
        f"- evaluated_scope_count: `{report['summary']['evaluated_scope_count']}`",
        f"- error_scope_count: `{report['summary']['error_scope_count']}`",
        f"- xhtml_candidate_count: `{report['summary']['xhtml_candidate_count']}`",
        f"- missing_candidate_count: `{report['summary']['missing_candidate_count']}`",
        f"- weak_match_count: `{report['summary']['weak_match_count']}`",
        f"- ambiguous_match_count: `{report['summary']['ambiguous_match_count']}`",
        "- requirement_code_only_match_count: "
        f"`{report['summary']['requirement_code_only_match_count']}`",
        f"- order_violations: `{report['summary']['order_violations']}`",
        "",
        "## Blockers",
        "",
    ]
    if report["summary"]["blockers"]:
        lines.extend(f"- `{item}`" for item in report["summary"]["blockers"])
    else:
        lines.append("- none")
    lines.extend(["", "## Scope Results", ""])
    lines.append(
        "| Scope | Status | Candidates | Missing | Weak | Order preserved | Diagnostics | Match counts |"
    )
    lines.append("| --- | --- | ---: | ---: | ---: | --- | --- | --- |")
    for item in report["scope_results"]:
        if item.get("status") == "error":
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{item['scope_slug']}`",
                        "`error`",
                        "-",
                        "-",
                        "-",
                        "-",
                        "-",
                        f"`{item['error_type']}: {item['error']}`",
                    ]
                )
                + " |"
            )
            continue
        match_counts = ", ".join(
            f"{key}={value}" for key, value in sorted(item["match_counts"].items())
        )
        diagnostics = item.get("diagnostics", {})
        diagnostic_counts = (
            f"missing={len(diagnostics.get('missing_candidates', []))}, "
            f"weak={len(diagnostics.get('weak_matches', []))}, "
            f"order={len(diagnostics.get('order_violations', []))}"
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{item['scope_slug']}`",
                    "`evaluated`",
                    str(item["xhtml_candidate_count"]),
                    str(item["missing_candidate_count"]),
                    str(item["weak_match_count"]),
                    f"`{str(item['order_preserved']).lower()}`",
                    f"`{diagnostic_counts}`",
                    f"`{match_counts}`",
                ]
            )
            + " |"
        )
    lines.extend(["", "## Diagnostic Notes", ""])
    notes: list[str] = []
    for item in report["scope_results"]:
        if item.get("status") != "evaluated":
            continue
        diagnostics = item.get("diagnostics", {})
        for key, label in (
            ("missing_candidates", "missing"),
            ("weak_matches", "weak"),
            ("order_violations", "order"),
        ):
            values = diagnostics.get(key, [])
            if values:
                first = values[0]
                matched_ids = first.get("matched_block_ids", [])
                note_id = first.get("candidate_id") or (
                    matched_ids[0] if matched_ids else "unknown"
                )
                notes.append(
                    f"- `{item['scope_slug']}` {label}: "
                    f"`{note_id}`"
                )
    lines.extend(notes[:20] if notes else ["- none"])
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This diagnostic compares the DOCX-derived JSON projection with the "
            "current XHTML row baseline. A passing diagnostic does not by itself "
            "replace XHTML in production; it only proves that JSON is safe enough "
            "for a controlled switch candidate on the evaluated scopes.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate whether DOCX JSON projection is ready to replace XHTML "
            "as the machine-readable extraction source across multiple scopes."
        )
    )
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--docx", required=True, type=Path)
    parser.add_argument("--selected-xhtml", type=Path)
    parser.add_argument("--spec", action="append", default=[], type=Path)
    parser.add_argument("--spec-root", action="append", default=[], type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--docx-json-output", type=Path)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    output_json = args.output_json
    docx_json_output = args.docx_json_output or output_json.with_suffix(
        ".source.json"
    )
    write_docx_source_json(
        args.docx,
        repo_root=repo_root,
        output_path=docx_json_output,
    )
    spec_paths = _collect_specs(
        repo_root=repo_root,
        specs=args.spec,
        spec_roots=args.spec_root,
    )
    if not spec_paths:
        raise SystemExit("no source-row-extraction-spec.json files were selected")

    scope_results: list[dict[str, Any]] = []
    for spec_path in spec_paths:
        scope_slug = spec_path.parent.name
        try:
            scope_report = compare_docx_json_to_xhtml_baseline(
                repo_root=repo_root,
                spec_path=spec_path,
                docx_json_path=docx_json_output,
                selected_xhtml=args.selected_xhtml,
            )
        except Exception as exc:  # noqa: BLE001 - diagnostic must continue all scopes
            scope_results.append(
                {
                    "status": "error",
                    "scope_slug": scope_slug,
                    "spec_path": _repo_relative(spec_path, repo_root),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
            continue
        scope_results.append({"status": "evaluated", **scope_report})

    report = {
        "schema_version": 1,
        "docx": _repo_relative(args.docx, repo_root),
        "selected_xhtml_override": (
            _repo_relative(args.selected_xhtml, repo_root)
            if args.selected_xhtml is not None
            else None
        ),
        "docx_json": _repo_relative(docx_json_output, repo_root),
        "summary": _aggregate_verdict(scope_results),
        "scope_results": scope_results,
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if args.output_md is not None:
        _write_markdown(report, args.output_md)
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
