from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.review_cycle.source_model_adequacy import (  # noqa: E402
    evaluate_pre_review_source_model_adequacy,
)


def _resolve(root: Path, value: Path, *, label: str) -> Path:
    path = (value if value.is_absolute() else root / value).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} must stay under repo root: {path}") from exc
    return path


def _write_fresh_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run deterministic source-model checks before model review."
    )
    parser.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--coverage-obligation-table", type=Path, required=True)
    parser.add_argument("--package-test-design-plan", type=Path, required=True)
    parser.add_argument("--dictionary-inventory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.repo_root.resolve()
    try:
        report = evaluate_pre_review_source_model_adequacy(
            _resolve(root, args.manifest, label="manifest"),
            coverage_obligation_table=_resolve(
                root,
                args.coverage_obligation_table,
                label="coverage_obligation_table",
            ),
            package_test_design_plan=_resolve(
                root,
                args.package_test_design_plan,
                label="package_test_design_plan",
            ),
            dictionary_inventory=(
                _resolve(
                    root,
                    args.dictionary_inventory,
                    label="dictionary_inventory",
                )
                if args.dictionary_inventory is not None
                else None
            ),
        )
        output = _resolve(root, args.output, label="output")
        _write_fresh_json(output, report)
    except Exception as exc:  # noqa: BLE001 - one terminal CLI diagnostic.
        print(
            json.dumps(
                {"status": "failed", "error_type": type(exc).__name__, "error": str(exc)},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
