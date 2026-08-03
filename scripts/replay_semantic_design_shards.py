from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.semantic_design_bridge import (  # noqa: E402
    canonical_payload_sha256,
    load_approved_clarifications,
    normalize_semantic_design_transport,
)
from test_case_agent.semantic_design_sharding import (  # noqa: E402
    merge_semantic_shards,
    project_semantic_shard,
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON object expected: {path}")
    return payload


def _resolve(root: Path, path: Path) -> Path:
    resolved = (path if path.is_absolute() else root / path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes repository root: {resolved}") from exc
    return resolved


def replay_semantic_design_shards(
    *,
    repo_root: Path,
    context_path: Path,
    boundary_path: Path,
    plan_path: Path,
    shards_dir: Path,
    merged_output_path: Path | None = None,
) -> dict[str, Any]:
    root = repo_root.resolve()
    context_file = _resolve(root, context_path)
    boundary_file = _resolve(root, boundary_path)
    plan_file = _resolve(root, plan_path)
    shard_root = _resolve(root, shards_dir)
    context = _load(context_file)
    boundary = _load(boundary_file)
    plan = _load(plan_file)
    raw_shards = plan.get("shards")
    if not isinstance(raw_shards, list) or not raw_shards:
        raise ValueError("semantic shard plan has no shards")

    outputs: dict[str, dict[str, Any]] = {}
    shard_reports: list[dict[str, Any]] = []
    for item in raw_shards:
        if not isinstance(item, Mapping):
            raise ValueError("semantic shard plan contains a non-object shard")
        shard_id = str(item.get("shard_id", ""))
        if not shard_id:
            raise ValueError("semantic shard plan contains an empty shard_id")
        shard_dir = shard_root / shard_id
        raw_model_output = shard_dir / "semantic-design.model-output.json"
        materialized_output = shard_dir / "semantic-design.json"
        selected = raw_model_output if raw_model_output.is_file() else materialized_output
        if not selected.is_file():
            raise FileNotFoundError(f"semantic output is missing for {shard_id}")
        raw = _load(selected)
        shard_context, shard_boundary = project_semantic_shard(
            context,
            boundary,
            item,
        )
        normalized, receipt = normalize_semantic_design_transport(
            raw,
            context=shard_context,
            boundary=shard_boundary,
            repo_root=root,
            fixture_context=context,
        )
        outputs[shard_id] = normalized
        shard_reports.append(
            {
                "shard_id": shard_id,
                "input": selected.relative_to(root).as_posix(),
                "input_kind": (
                    "raw-model-output"
                    if selected == raw_model_output
                    else "materialized-output"
                ),
                "input_sha256": canonical_payload_sha256(raw),
                "normalized_sha256": canonical_payload_sha256(normalized),
                "repair_count": int(receipt.get("repair_count", 0)),
                "repairs": receipt.get("repairs", []),
            }
        )

    clarifications = load_approved_clarifications(root, context)
    merged, merge_receipt = merge_semantic_shards(
        context,
        boundary,
        clarifications,
        plan,
        outputs,
    )
    report = {
        "version": 1,
        "status": "verified",
        "inputs": {
            "context": context_file.relative_to(root).as_posix(),
            "scope_boundary_decision": boundary_file.relative_to(root).as_posix(),
            "semantic_shard_plan": plan_file.relative_to(root).as_posix(),
            "shards_dir": shard_root.relative_to(root).as_posix(),
        },
        "shard_count": len(shard_reports),
        "normalization_repair_count": sum(
            int(item["repair_count"]) for item in shard_reports
        ),
        "shards": shard_reports,
        "merge_receipt": merge_receipt,
        "merged_counts": {
            "source_designs": len(merged.get("source_designs", [])),
            "assertions": sum(
                len(item.get("assertions", []))
                for item in merged.get("source_designs", [])
                if isinstance(item, Mapping)
            ),
            "obligations": len(merged.get("obligations", [])),
            "negative_oracles": len(merged.get("negative_oracles", [])),
            "requiredness_oracles": len(merged.get("requiredness_oracles", [])),
        },
    }
    if merged_output_path is not None:
        merged_output = _resolve(root, merged_output_path)
        if merged_output.exists():
            raise FileExistsError(
                f"merged semantic output must be fresh: {merged_output}"
            )
        merged_output.parent.mkdir(parents=True, exist_ok=True)
        merged_output.write_text(
            json.dumps(merged, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        report["merged_output"] = {
            "path": merged_output.relative_to(root).as_posix(),
            "sha256": canonical_payload_sha256(merged),
        }
    return report


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Re-normalize saved semantic shard outputs and replay the strict full "
            "merge without model calls."
        )
    )
    result.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    result.add_argument("--context", type=Path, required=True)
    result.add_argument("--scope-boundary-decision", type=Path, required=True)
    result.add_argument("--semantic-shard-plan", type=Path, required=True)
    result.add_argument("--shards-dir", type=Path, required=True)
    result.add_argument("--merged-output", type=Path)
    result.add_argument("--output", type=Path)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.repo_root.resolve()
    try:
        report = replay_semantic_design_shards(
            repo_root=root,
            context_path=args.context,
            boundary_path=args.scope_boundary_decision,
            plan_path=args.semantic_shard_plan,
            shards_dir=args.shards_dir,
            merged_output_path=args.merged_output,
        )
    except Exception as exc:  # noqa: BLE001 - diagnostic terminal boundary.
        report = {
            "version": 1,
            "status": "blocked",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        output = _resolve(root, args.output)
        if output.exists():
            raise FileExistsError(f"replay output must be fresh: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "verified" else 2


if __name__ == "__main__":
    raise SystemExit(main())
