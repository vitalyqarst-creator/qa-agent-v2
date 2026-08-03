from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.codex_exec_semantic_design_author import main as semantic_main  # noqa: E402
from scripts.run_standard_scope_bridge import (  # noqa: E402
    StandardScopeBridgeError,
    _model_args,
    _run_sharded_semantic_design,
    _runtime_paths,
    _validate_one_attempt_summary,
    _write_json_atomic,
)
from test_case_agent.semantic_design_sharding import (  # noqa: E402
    MODEL_EXECUTION_MODE,
    build_semantic_shard_plan,
    project_semantic_shard,
    rebind_semantic_shard_plan_ownership,
)


def _under(root: Path, value: Path, *, label: str) -> Path:
    path = (value if value.is_absolute() else root / value).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise StandardScopeBridgeError(
            f"{label} escapes repository root: {path}"
        ) from exc
    return path


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Run only the standard sharded semantic-design phase against an existing "
            "immutable context/boundary pair. The fresh output is development evidence, "
            "not a production handoff or benchmark continuation."
        )
    )
    result.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    result.add_argument("--context", type=Path, required=True)
    result.add_argument("--scope-boundary-decision", type=Path, required=True)
    result.add_argument("--runtime-dir", type=Path, required=True)
    result.add_argument("--image", type=Path, action="append", default=[])
    result.add_argument("--codex-command")
    result.add_argument(
        "--measurement-mode",
        choices=("production", "observational"),
        default="observational",
    )
    result.add_argument(
        "--semantic-sharding",
        choices=("auto", "on"),
        default="on",
    )
    result.add_argument("--semantic-shard-max-included-rows", type=int, default=10)
    result.add_argument("--semantic-shard-max-source-rows", type=int, default=16)
    result.add_argument("--semantic-shard-max-shards", type=int, default=10)
    result.add_argument("--semantic-shard-max-weight", type=int, default=24)
    result.add_argument(
        "--semantic-timeout-seconds",
        type=int,
        help=(
            "Optional per-model-shard timeout for a qualification attempt; "
            "the default preserves the production runner budget."
        ),
    )
    result.add_argument(
        "--target-shard-id",
        help=(
            "Development-only: run one projected model shard in a fresh immutable "
            "runtime. This does not qualify the full semantic design or perform merge."
        ),
    )
    result.add_argument(
        "--preferred-plan",
        type=Path,
        help=(
            "Development-only digest-valid prior plan whose row ownership is "
            "revalidated for the fresh context before a targeted shard call."
        ),
    )
    return result


def _run_targeted_shard(
    *,
    root: Path,
    context_path: Path,
    boundary_path: Path,
    runtime_dir: Path,
    images: tuple[Path, ...],
    args: argparse.Namespace,
) -> tuple[int, dict[str, object]]:
    context = json.loads(context_path.read_text(encoding="utf-8"))
    boundary = json.loads(boundary_path.read_text(encoding="utf-8"))
    if args.preferred_plan is None:
        plan = build_semantic_shard_plan(
            context,
            boundary,
            mode=args.semantic_sharding,
            max_included_rows=args.semantic_shard_max_included_rows,
            max_source_rows=args.semantic_shard_max_source_rows,
            max_shards=args.semantic_shard_max_shards,
            max_semantic_weight=args.semantic_shard_max_weight,
        )
    else:
        preferred_plan = json.loads(args.preferred_plan.read_text(encoding="utf-8"))
        plan = rebind_semantic_shard_plan_ownership(
            context,
            boundary,
            preferred_plan,
            max_included_rows=args.semantic_shard_max_included_rows,
            max_source_rows=args.semantic_shard_max_source_rows,
            max_shards=args.semantic_shard_max_shards,
            max_semantic_weight=args.semantic_shard_max_weight,
        )
    shard = next(
        (
            item
            for item in plan["shards"]
            if item.get("shard_id") == args.target_shard_id
        ),
        None,
    )
    if shard is None:
        raise StandardScopeBridgeError(
            f"target shard is absent from deterministic plan: {args.target_shard_id}"
        )
    if shard.get("execution_mode") != MODEL_EXECUTION_MODE:
        raise StandardScopeBridgeError(
            f"target shard is not model-owned: {args.target_shard_id}"
        )
    semantic_root = runtime_dir / "semantic-design"
    _write_json_atomic(semantic_root / "semantic-shard-plan.json", plan)
    projected_context, projected_boundary = project_semantic_shard(
        context,
        boundary,
        shard,
    )
    paths = _runtime_paths(
        semantic_root / "shards",
        str(args.target_shard_id),
        "semantic-design.json",
    )
    projected_context_path = paths["root"] / "prepared-bounded-context.json"
    projected_boundary_path = paths["root"] / "scope-boundary-decision.json"
    _write_json_atomic(projected_context_path, projected_context)
    _write_json_atomic(projected_boundary_path, projected_boundary)
    model_args = _model_args(
        paths=paths,
        repo_root=root,
        context=projected_context_path,
        images=images,
        codex_command=args.codex_command,
        measurement_mode=args.measurement_mode,
        timeout_seconds=args.semantic_timeout_seconds,
    )
    model_args.extend(
        ("--scope-boundary-decision", str(projected_boundary_path))
    )
    code = semantic_main(model_args)
    summary = (
        json.loads(paths["summary"].read_text(encoding="utf-8"))
        if paths["summary"].is_file()
        else {}
    )
    if code == 0 and summary.get("decision") == "ready":
        _validate_one_attempt_summary(summary, label=str(args.target_shard_id))
    result = dict(summary)
    result["targeted_qualification"] = {
        "status": "development-evidence-only",
        "shard_id": args.target_shard_id,
        "full_design_qualified": False,
        "merge_performed": False,
        "plan": "semantic-shard-plan.json",
    }
    _write_json_atomic(paths["summary"], result)
    return code, result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.repo_root.resolve()
    context = _under(root, args.context, label="context")
    boundary = _under(
        root,
        args.scope_boundary_decision,
        label="scope-boundary-decision",
    )
    runtime_dir = _under(root, args.runtime_dir, label="runtime-dir")
    images = tuple(_under(root, item, label="image") for item in args.image)
    if args.preferred_plan is not None:
        args.preferred_plan = _under(
            root,
            args.preferred_plan,
            label="preferred-plan",
        )
    for label, path in (
        ("context", context),
        ("scope-boundary-decision", boundary),
        *(("image", item) for item in images),
        *(
            (("preferred-plan", args.preferred_plan),)
            if args.preferred_plan is not None
            else ()
        ),
    ):
        if not path.is_file():
            raise FileNotFoundError(f"{label} is not a file: {path}")
    if runtime_dir.exists():
        raise FileExistsError(
            f"qualification runtime-dir must be a fresh immutable path: {runtime_dir}"
        )
    if args.semantic_shard_max_weight <= 0:
        raise ValueError("semantic-shard-max-weight must be positive")
    if args.semantic_timeout_seconds is not None and args.semantic_timeout_seconds <= 0:
        raise ValueError("semantic-timeout-seconds must be positive")
    if args.preferred_plan is not None and not args.target_shard_id:
        raise StandardScopeBridgeError(
            "--preferred-plan currently requires --target-shard-id"
        )

    if args.target_shard_id:
        code, summary = _run_targeted_shard(
            root=root,
            context_path=context,
            boundary_path=boundary,
            runtime_dir=runtime_dir,
            images=images,
            args=args,
        )
    else:
        semantic_paths = _runtime_paths(
            runtime_dir,
            "semantic-design",
            "semantic-design.json",
        )
        code, summary = _run_sharded_semantic_design(
            repo_root=root,
            context_path=context,
            boundary_path=boundary,
            semantic_paths=semantic_paths,
            images=images,
            codex_command=args.codex_command,
            measurement_mode=args.measurement_mode,
            semantic_runner=semantic_main,
            mode=args.semantic_sharding,
            max_included_rows=args.semantic_shard_max_included_rows,
            max_source_rows=args.semantic_shard_max_source_rows,
            max_shards=args.semantic_shard_max_shards,
            max_semantic_weight=args.semantic_shard_max_weight,
            timeout_seconds=args.semantic_timeout_seconds,
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
