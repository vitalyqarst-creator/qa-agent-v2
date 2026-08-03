from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from test_case_agent.source_qualified_run import (
    SourceQualifiedRunError,
    classify_source_qualified_status,
    run_source_qualified_scope,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXIT_WORKFLOW_FAILED = 1
EXIT_CONTRACT_ERROR = 2
EXIT_INFRASTRUCTURE_ERROR = 3
EXIT_INTERNAL_ERROR = 70


def _run(args: argparse.Namespace) -> int:
    result = run_source_qualified_scope(
        repo_root=args.repo_root.resolve(),
        config_path=args.config,
        output_dir=args.output_dir,
    )
    summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
    print(json.dumps(summary, ensure_ascii=False))
    category = classify_source_qualified_status(result.status)
    return {
        "success": 0,
        "workflow": EXIT_WORKFLOW_FAILED,
        "contract": EXIT_CONTRACT_ERROR,
        "infrastructure": EXIT_INFRASTRUCTURE_ERROR,
        "internal": EXIT_INTERNAL_ERROR,
    }[category]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ft-agent",
        description="Source-first deterministic test-case production command.",
    )
    parser.add_argument("--repo-root", type=Path, default=PROJECT_ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser(
        "run",
        help="Run one registry- and source-qualified immutable shadow iteration.",
    )
    run.add_argument("--config", type=Path, required=True)
    run.add_argument("--output-dir", type=Path, required=True)
    run.set_defaults(handler=_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except SourceQualifiedRunError as exc:
        print(f"contract-error [{type(exc).__name__}]: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR
    except OSError as exc:
        print(f"infrastructure-error [{type(exc).__name__}]: {exc}", file=sys.stderr)
        return EXIT_INFRASTRUCTURE_ERROR
    except Exception as exc:
        print(
            f"internal-error: unexpected {type(exc).__name__}; "
            "see developer diagnostics",
            file=sys.stderr,
        )
        return EXIT_INTERNAL_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
