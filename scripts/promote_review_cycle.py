from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.review_cycle.promotion import (  # noqa: E402
    HARD_SLO_MS,
    TARGET_SLO_MS,
    PromotionBlocked,
    build_full_promotion_basis,
    build_validate_promote_review_cycle,
    promote_review_cycle,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build, validate and promote one accepted prepared exec review cycle "
            "without model/UI calls or manually prepared promotion-inputs."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    parser.add_argument("--cycle-dir", type=Path, required=True)
    parser.add_argument("--promotion-basis", type=Path)
    parser.add_argument("--promotion-seed", type=Path)
    parser.add_argument("--cycle-state-replacement", type=Path)
    parser.add_argument("--workflow-state-replacement", type=Path)
    parser.add_argument(
        "--use-existing-basis",
        action="store_true",
        help="Skip seed builder and promote only an already materialized basis.",
    )
    parser.add_argument(
        "--build-only",
        action="store_true",
        help="Build/reuse promotion-basis.json but do not validate or promote.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--validate-only", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-overwrite", action="store_true")
    parser.add_argument("--target-slo-ms", type=int, default=TARGET_SLO_MS)
    parser.add_argument("--hard-slo-ms", type=int, default=HARD_SLO_MS)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    cycle_dir = (
        args.cycle_dir.resolve()
        if args.cycle_dir.is_absolute()
        else (repo_root / args.cycle_dir).resolve()
    )
    def resolved(value: Path | None) -> Path | None:
        if value is None:
            return None
        return value.resolve() if value.is_absolute() else (repo_root / value).resolve()

    basis_path = resolved(args.promotion_basis)
    seed_path = resolved(args.promotion_seed)
    cycle_replacement = resolved(args.cycle_state_replacement)
    workflow_replacement = resolved(args.workflow_state_replacement)
    default_seed = cycle_dir / "promotion-basis.seed.json"
    use_builder = not args.use_existing_basis and (
        args.build_only or seed_path is not None or default_seed.is_file()
    )
    if args.build_only and (args.validate_only or args.dry_run):
        print(
            json.dumps(
                {
                    "status": "blocked-input",
                    "code": "PROMO-INVALID-OPTIONS",
                    "message": "--build-only cannot be combined with validation modes",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2
    if args.build_only and args.use_existing_basis:
        print(
            json.dumps(
                {
                    "status": "blocked-input",
                    "code": "PROMO-INVALID-OPTIONS",
                    "message": "--build-only cannot be combined with --use-existing-basis",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2
    if not use_builder and not args.use_existing_basis:
        print(
            json.dumps(
                {
                    "status": "blocked-input",
                    "code": "PROMO-MISSING-SEED",
                    "message": (
                        "default one-command promotion requires promotion-basis.seed.json; "
                        "use --use-existing-basis only for an explicitly audited schema-v3 basis"
                    ),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2
    try:
        if args.build_only:
            build = build_full_promotion_basis(
                repo_root=repo_root,
                cycle_dir=cycle_dir,
                seed_path=seed_path,
                basis_path=basis_path,
                cycle_state_replacement_path=cycle_replacement,
                workflow_state_replacement_path=workflow_replacement,
            )
            print(json.dumps(build.as_dict(), ensure_ascii=False, indent=2))
            return 0
        if use_builder:
            result = build_validate_promote_review_cycle(
                repo_root=repo_root,
                cycle_dir=cycle_dir,
                seed_path=seed_path,
                basis_path=basis_path,
                cycle_state_replacement_path=cycle_replacement,
                workflow_state_replacement_path=workflow_replacement,
                validate_only=args.validate_only,
                dry_run=args.dry_run,
                allow_overwrite=args.allow_overwrite,
                target_slo_ms=args.target_slo_ms,
                hard_slo_ms=args.hard_slo_ms,
            )
        else:
            result = promote_review_cycle(
                repo_root=repo_root,
                cycle_dir=cycle_dir,
                basis_path=basis_path,
                validate_only=args.validate_only,
                dry_run=args.dry_run,
                allow_overwrite=args.allow_overwrite,
                target_slo_ms=args.target_slo_ms,
                hard_slo_ms=args.hard_slo_ms,
            )
    except PromotionBlocked as exc:
        print(
            json.dumps(
                {"status": "blocked-input", "code": exc.code, "message": exc.message},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        print(
            json.dumps(
                {"status": "failed", "error": f"{type(exc).__name__}: {exc}"},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1
    print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
