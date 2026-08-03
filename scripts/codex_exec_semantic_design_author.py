from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.codex_exec_bounded_scope_analyzer import main as run_scope_analyzer


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Run one isolated standard-production semantic-design author call "
            "against an authoritative ready v2 scope boundary."
        )
    )
    result.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    result.add_argument("--context", type=Path, required=True)
    result.add_argument(
        "--fixture-context",
        type=Path,
        help=(
            "full prepared context for deterministic verified-fixture "
            "normalization; not exposed to the model prompt"
        ),
    )
    result.add_argument("--scope-boundary-decision", type=Path, required=True)
    result.add_argument("--decision-output", type=Path, required=True)
    result.add_argument("--events-output", type=Path, required=True)
    result.add_argument("--stderr-output", type=Path, required=True)
    result.add_argument("--summary-output", type=Path, required=True)
    result.add_argument("--schema-output", type=Path, required=True)
    result.add_argument("--preflight-output", type=Path)
    result.add_argument("--terminal-receipt-output", type=Path)
    result.add_argument("--scope-execution-profile-output", type=Path)
    result.add_argument("--backend-selection-output", type=Path)
    result.add_argument("--image", action="append", type=Path, default=[])
    result.add_argument("--codex-command")
    result.add_argument(
        "--measurement-mode",
        choices=("production", "observational"),
        default="production",
    )
    timeout = result.add_mutually_exclusive_group()
    timeout.add_argument("--timeout-seconds", type=int)
    timeout.add_argument("--no-timeout", action="store_true")
    return result


def _append_path(arguments: list[str], name: str, value: Path | None) -> None:
    if value is not None:
        arguments.extend((name, str(value)))


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    forwarded = [
        "--repo-root",
        str(args.repo_root),
        "--context",
        str(args.context),
        "--scope-boundary-decision",
        str(args.scope_boundary_decision),
        "--decision-output",
        str(args.decision_output),
        "--events-output",
        str(args.events_output),
        "--stderr-output",
        str(args.stderr_output),
        "--summary-output",
        str(args.summary_output),
        "--schema-output",
        str(args.schema_output),
        "--contract-version",
        "1",
        "--scope-execution-profile",
        "standard-production",
        "--measurement-mode",
        args.measurement_mode,
    ]
    _append_path(forwarded, "--fixture-context", args.fixture_context)
    for option, value in (
        ("--preflight-output", args.preflight_output),
        ("--terminal-receipt-output", args.terminal_receipt_output),
        ("--scope-execution-profile-output", args.scope_execution_profile_output),
        ("--backend-selection-output", args.backend_selection_output),
    ):
        _append_path(forwarded, option, value)
    for image in args.image:
        forwarded.extend(("--image", str(image)))
    if args.codex_command is not None:
        forwarded.extend(("--codex-command", args.codex_command))
    if args.timeout_seconds is not None:
        forwarded.extend(("--timeout-seconds", str(args.timeout_seconds)))
    elif args.no_timeout:
        forwarded.append("--no-timeout")
    return run_scope_analyzer(forwarded)


if __name__ == "__main__":
    raise SystemExit(main())
