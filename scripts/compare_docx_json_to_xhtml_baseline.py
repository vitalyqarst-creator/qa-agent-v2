from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from test_case_agent.review_cycle.source_row_baseline import (
    SourceRowExtractionSpec,
    build_source_row_baseline,
    normalize_bounded_source_text,
)
from test_case_agent.source_json_projection import load_docx_source_json


REQUIREMENT_CODE_RE = re.compile(r"\bBSR\s+\d+\b")
DOCX_JSON_TABLE_DELIMITER_RE = re.compile(r"\s*\|\s*")


def _repo_relative(path: Path, repo_root: Path) -> str:
    resolved = path.resolve()
    root = repo_root.resolve()
    return PurePosixPath(*resolved.relative_to(root).parts).as_posix()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _comparison_text(value: str) -> str:
    """Normalize source text for cross-transport comparison.

    XHTML row text is flattened by the source-row baseline extractor, while the
    DOCX JSON projection intentionally preserves table cell boundaries with
    ``|`` delimiters.  For parity diagnostics those delimiters are transport
    syntax, not requirement text, so compare with them collapsed to spaces.
    """

    return normalize_bounded_source_text(
        DOCX_JSON_TABLE_DELIMITER_RE.sub(" ", value)
    ).casefold()


def _load_spec(
    path: Path,
    *,
    repo_root: Path,
    selected_xhtml: Path | None,
) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("source-row extraction spec must be a JSON object")
    if selected_xhtml is not None:
        payload = dict(payload)
        payload["selected_xhtml"] = {
            "relative_path": _repo_relative(selected_xhtml, repo_root),
            "sha256": _sha256(selected_xhtml),
        }
    return payload


def _match_candidate(candidate_text: str, blocks: list[dict[str, Any]]) -> dict[str, Any]:
    target = normalize_bounded_source_text(candidate_text).casefold()
    target_for_comparison = _comparison_text(candidate_text)
    target_codes = tuple(REQUIREMENT_CODE_RE.findall(candidate_text))
    exact: list[dict[str, Any]] = []
    contains: list[dict[str, Any]] = []
    normalized_exact: list[dict[str, Any]] = []
    normalized_contains: list[dict[str, Any]] = []
    code_exact: list[dict[str, Any]] = []
    code_contains: list[dict[str, Any]] = []
    for block in blocks:
        raw_text = str(block.get("text", ""))
        text = normalize_bounded_source_text(raw_text).casefold()
        text_for_comparison = _comparison_text(raw_text)
        if not text:
            continue
        if text == target:
            exact.append(block)
        elif target in text or text in target:
            contains.append(block)
        elif text_for_comparison == target_for_comparison:
            normalized_exact.append(block)
        elif (
            target_for_comparison in text_for_comparison
            or text_for_comparison in target_for_comparison
        ):
            normalized_contains.append(block)
        if target_codes:
            block_codes = tuple(REQUIREMENT_CODE_RE.findall(raw_text))
            if set(block_codes) == set(target_codes):
                code_exact.append(block)
            elif set(target_codes).issubset(set(block_codes)):
                code_contains.append(block)
    matches = (
        exact
        or contains
        or normalized_exact
        or normalized_contains
        or code_exact
        or code_contains
    )
    if not matches:
        return {"match_type": "missing", "matches": []}
    if exact:
        match_type = "exact"
    elif contains:
        match_type = "contains"
    elif normalized_exact:
        match_type = "normalized-exact"
    elif normalized_contains:
        match_type = "normalized-contains"
    elif code_exact:
        match_type = "requirement-code-exact"
    else:
        match_type = "requirement-code-contains"
    if len(matches) > 1:
        match_type = f"ambiguous-{match_type}"
    return {
        "match_type": match_type,
        "requirement_codes": list(target_codes),
        "matches": [
            {
                "block_id": item.get("block_id"),
                "block_index": item.get("block_index"),
                "kind": item.get("kind"),
                "locator": item.get("locator"),
                "section_path": item.get("section_path"),
                "text": item.get("text"),
            }
            for item in matches[:5]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compare DOCX JSON projection coverage against an XHTML source-row "
            "baseline built from an extraction spec."
        )
    )
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--docx-json", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--selected-xhtml", type=Path)
    args = parser.parse_args()

    spec_payload = _load_spec(
        args.spec,
        repo_root=args.repo_root,
        selected_xhtml=args.selected_xhtml,
    )
    spec = SourceRowExtractionSpec.from_dict(spec_payload)
    baseline = build_source_row_baseline(repo_root=args.repo_root, spec=spec)
    projection = load_docx_source_json(args.docx_json)
    blocks = projection["blocks"]

    candidate_results = []
    last_block_index = 0
    order_violations = 0
    for candidate in baseline.candidates:
        match = _match_candidate(candidate.bounded_source_text, blocks)
        first_match_index = (
            int(match["matches"][0]["block_index"])
            if match["matches"]
            and isinstance(match["matches"][0].get("block_index"), int)
            else None
        )
        if first_match_index is not None:
            if first_match_index < last_block_index:
                order_violations += 1
            last_block_index = max(last_block_index, first_match_index)
        candidate_results.append(
            {
                "candidate_id": candidate.candidate_id,
                "region_id": candidate.region_id,
                "element_kind": candidate.element_kind,
                "xhtml_locator": candidate.canonical_xpath,
                "bounded_source_text": candidate.bounded_source_text,
                **match,
            }
        )

    counts: dict[str, int] = {}
    for item in candidate_results:
        counts[item["match_type"]] = counts.get(item["match_type"], 0) + 1
    matched = sum(
        count for kind, count in counts.items() if kind != "missing"
    )
    report = {
        "schema_version": 1,
        "scope_slug": spec.scope_slug,
        "xhtml_candidate_count": baseline.candidate_count,
        "docx_json_block_count": projection["block_count"],
        "match_counts": counts,
        "matched_candidate_count": matched,
        "missing_candidate_count": counts.get("missing", 0),
        "order_violations": order_violations,
        "order_preserved": order_violations == 0,
        "selected_xhtml": spec.selected_xhtml.to_dict(),
        "docx_json_projection": {
            "source_path": projection["source_path"],
            "source_sha256": projection["source_sha256"],
            "projection_sha256": projection["projection_sha256"],
        },
        "candidate_results": candidate_results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({k: report[k] for k in (
        "scope_slug",
        "xhtml_candidate_count",
        "docx_json_block_count",
        "match_counts",
        "missing_candidate_count",
        "order_preserved",
    )}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
