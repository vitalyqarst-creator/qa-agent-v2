from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.semantic_design_bridge import (  # noqa: E402
    canonical_payload_sha256,
    load_approved_clarifications,
    normalize_semantic_design_transport,
    semantic_design_minimum_obligation_count,
    semantic_design_output_schema,
    validate_semantic_design_binding,
    validate_semantic_input_preflight,
)
from test_case_agent.semantic_design_sharding import (  # noqa: E402
    build_semantic_shard_plan,
    merge_semantic_shards,
    project_semantic_shard,
    rebind_semantic_shard_plan_ownership,
)


class QualificationShardMergeError(RuntimeError):
    """Raised when immutable development shard evidence cannot be merged."""


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise QualificationShardMergeError(f"JSON object expected: {path}")
    return payload


def _under(root: Path, value: Path, *, label: str) -> Path:
    path = (value if value.is_absolute() else root / value).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise QualificationShardMergeError(
            f"{label} escapes repository root: {path}"
        ) from exc
    return path


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _parse_shard_inputs(
    root: Path,
    values: Sequence[str],
) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values:
        shard_id, separator, raw_path = value.partition("=")
        if not separator or not shard_id.strip() or not raw_path.strip():
            raise QualificationShardMergeError(
                "--shard-input must use SHARD_ID=PATH"
            )
        shard_id = shard_id.strip()
        if shard_id in result:
            raise QualificationShardMergeError(
                f"duplicate --shard-input for {shard_id}"
            )
        path = _under(root, Path(raw_path.strip()), label=f"{shard_id} input")
        if not path.is_file():
            raise FileNotFoundError(f"shard input is not a file: {path}")
        result[shard_id] = path
    return result


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Revalidate immutable semantic shard outputs under the current deterministic "
            "contract and merge them as development qualification evidence. The result "
            "is explicitly ineligible for a clean benchmark."
        )
    )
    result.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    result.add_argument("--context", type=Path, required=True)
    result.add_argument("--scope-boundary-decision", type=Path, required=True)
    result.add_argument("--runtime-dir", type=Path, required=True)
    result.add_argument(
        "--shard-input",
        action="append",
        default=[],
        help="One immutable SHARD_ID=PATH binding; repeat for every planned shard.",
    )
    result.add_argument("--semantic-shard-max-included-rows", type=int, default=10)
    result.add_argument("--semantic-shard-max-source-rows", type=int, default=16)
    result.add_argument("--semantic-shard-max-shards", type=int, default=10)
    result.add_argument("--semantic-shard-max-weight", type=int, default=24)
    result.add_argument(
        "--preferred-plan",
        type=Path,
        help=(
            "Optional prior digest-bound plan whose safe row ownership is preserved "
            "while current weights and limits are revalidated."
        ),
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    started = time.perf_counter_ns()
    root = args.repo_root.resolve()
    context_path = _under(root, args.context, label="context")
    boundary_path = _under(
        root,
        args.scope_boundary_decision,
        label="scope-boundary-decision",
    )
    runtime_dir = _under(root, args.runtime_dir, label="runtime-dir")
    if runtime_dir.exists():
        raise FileExistsError(
            f"qualification runtime-dir must be a fresh immutable path: {runtime_dir}"
        )
    if args.semantic_shard_max_weight <= 0:
        raise ValueError("semantic-shard-max-weight must be positive")
    for label, path in (("context", context_path), ("boundary", boundary_path)):
        if not path.is_file():
            raise FileNotFoundError(f"{label} is not a file: {path}")

    context = _load(context_path)
    boundary = _load(boundary_path)
    if args.preferred_plan is None:
        plan = build_semantic_shard_plan(
            context,
            boundary,
            mode="on",
            max_included_rows=args.semantic_shard_max_included_rows,
            max_source_rows=args.semantic_shard_max_source_rows,
            max_shards=args.semantic_shard_max_shards,
            max_semantic_weight=args.semantic_shard_max_weight,
        )
    else:
        preferred_plan_path = _under(
            root,
            args.preferred_plan,
            label="preferred-plan",
        )
        if not preferred_plan_path.is_file():
            raise FileNotFoundError(
                f"preferred-plan is not a file: {preferred_plan_path}"
            )
        plan = rebind_semantic_shard_plan_ownership(
            context,
            boundary,
            _load(preferred_plan_path),
            max_included_rows=args.semantic_shard_max_included_rows,
            max_source_rows=args.semantic_shard_max_source_rows,
            max_shards=args.semantic_shard_max_shards,
            max_semantic_weight=args.semantic_shard_max_weight,
        )
    expected_ids = [str(item["shard_id"]) for item in plan["shards"]]
    source_paths = _parse_shard_inputs(root, args.shard_input)
    if set(source_paths) != set(expected_ids):
        missing = sorted(set(expected_ids) - set(source_paths))
        extra = sorted(set(source_paths) - set(expected_ids))
        raise QualificationShardMergeError(
            f"shard input set mismatch: missing={missing}, extra={extra}"
        )

    semantic_root = runtime_dir / "semantic-design"
    _write_json(semantic_root / "semantic-shard-plan.json", plan)
    normalized_outputs: dict[str, dict[str, Any]] = {}
    evidence_rows: list[dict[str, Any]] = []
    for shard in plan["shards"]:
        shard_id = str(shard["shard_id"])
        shard_context, shard_boundary = project_semantic_shard(
            context,
            boundary,
            shard,
        )
        raw_path = source_paths[shard_id]
        raw = _load(raw_path)
        normalized, normalization_receipt = normalize_semantic_design_transport(
            raw,
            context=shard_context,
            boundary=shard_boundary,
        )
        shard_clarifications = tuple(
            item
            for item in shard_context.get("approved_clarifications", [])
            if isinstance(item, Mapping)
        )
        validation = validate_semantic_design_binding(
            shard_context,
            shard_boundary,
            normalized,
            clarifications=shard_clarifications,
            require_ready=True,
        )
        normalized_outputs[shard_id] = normalized
        shard_root = semantic_root / "shards" / shard_id
        _write_json(shard_root / "prepared-bounded-context.json", shard_context)
        _write_json(shard_root / "scope-boundary-decision.json", shard_boundary)
        _write_json(shard_root / "semantic-design.json", normalized)
        _write_json(
            shard_root / "normalization-receipt.json",
            normalization_receipt,
        )
        source_bytes = raw_path.read_bytes()
        evidence_rows.append(
            {
                "shard_id": shard_id,
                "execution_mode": shard["execution_mode"],
                "source_path": raw_path.relative_to(root).as_posix(),
                "source_bytes": len(source_bytes),
                "source_file_sha256": hashlib.sha256(source_bytes).hexdigest(),
                "source_payload_sha256": canonical_payload_sha256(raw),
                "normalized_payload_sha256": canonical_payload_sha256(normalized),
                "normalization_repair_count": len(
                    normalization_receipt.get("repairs", [])
                ),
                "validation": validation,
            }
        )

    clarifications = load_approved_clarifications(root, context)
    merged, merge_receipt = merge_semantic_shards(
        context,
        boundary,
        clarifications,
        plan,
        normalized_outputs,
    )
    preflight = validate_semantic_input_preflight(
        context,
        boundary,
        clarifications,
    )
    output_schema = semantic_design_output_schema(
        [str(item["source_row_id"]) for item in context["source_rows"]],
        require_ready=True,
        expected_minimum_obligation_count=semantic_design_minimum_obligation_count(
            preflight,
            boundary,
        ),
        expected_dependency_count=len(boundary["dependencies"]),
        expected_dictionary_count=len(preflight["dictionary_registry"]),
        expected_negative_signal_count=preflight["negative_signal_count"],
        expected_requiredness_signal_count=preflight["requiredness_signal_count"],
    )
    _write_json(semantic_root / "semantic-design.json", merged)
    _write_json(
        semantic_root / "semantic-shard-merge-receipt.json",
        merge_receipt,
    )
    _write_json(semantic_root / "preflight.json", preflight)
    _write_json(semantic_root / "output-schema.json", output_schema)
    qualification_manifest = {
        "version": 1,
        "status": "verified",
        "purpose": "development-shard-revalidation-and-merge",
        "benchmark_eligible": False,
        "benchmark_ineligibility_reason": (
            "The merged result reuses immutable outputs from prior development "
            "attempts and is not a fresh request-to-final execution."
        ),
        "context": context_path.relative_to(root).as_posix(),
        "scope_boundary_decision": boundary_path.relative_to(root).as_posix(),
        "plan_sha256": plan["plan_sha256"],
        "shards": evidence_rows,
        "merged_semantic_design_sha256": canonical_payload_sha256(merged),
        "merge_receipt": "semantic-shard-merge-receipt.json",
    }
    _write_json(
        semantic_root / "qualification-reuse-manifest.json",
        qualification_manifest,
    )
    summary = {
        "version": 1,
        "status": "completed",
        "decision": "ready",
        "development_evidence_only": True,
        "benchmark_eligible": False,
        "duration_ms": (time.perf_counter_ns() - started) // 1_000_000,
        "source_row_count": len(context["source_rows"]),
        "assertion_count": merge_receipt["validation"]["assertion_count"],
        "obligation_count": merge_receipt["validation"]["obligation_count"],
        "planned_test_case_count": merge_receipt["validation"][
            "planned_test_case_count"
        ],
        "requiredness_oracle_count": merge_receipt["validation"][
            "requiredness_oracle_count"
        ],
        "shard_count": len(expected_ids),
        "revalidated_shard_count": len(evidence_rows),
        "model_invoked": False,
        "qualification_reuse_manifest": "qualification-reuse-manifest.json",
    }
    _write_json(semantic_root / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
