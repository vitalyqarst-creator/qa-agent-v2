from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.review_cycle.source_assertions import (  # noqa: E402
    SourceAssertionContractError,
    SourceAssertionManifest,
    migrate_source_assertion_manifest_v3_payload,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Deterministically migrate a source assertion manifest v3 with zero "
            "approved clarifications to the fail-closed v4 schema."
        )
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    parser.add_argument(
        "--assert-no-approved-clarifications",
        action="store_true",
        help=(
            "Required acknowledgement that no user/analyst/product clarification "
            "influenced the v3 semantics."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    input_path = args.input.resolve()
    output_path = args.output.resolve()
    try:
        raw = json.loads(input_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise SourceAssertionContractError(
                "invalid-object",
                "source assertion manifest root must be a JSON object",
            )
        migrated = migrate_source_assertion_manifest_v3_payload(
            raw,
            confirm_no_approved_clarifications=(
                args.assert_no_approved_clarifications
            ),
        )
        manifest = SourceAssertionManifest.from_dict(migrated)
        manifest.validate(repo_root)
        content = json.dumps(
            manifest.to_dict(),
            ensure_ascii=False,
            indent=2,
        ) + "\n"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    except (OSError, UnicodeError, json.JSONDecodeError, SourceAssertionContractError) as exc:
        print(
            json.dumps(
                {"status": "blocked-input", "message": str(exc)},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2
    print(
        json.dumps(
            {
                "status": "migrated",
                "input": str(input_path),
                "output": str(output_path),
                "manifest_digest": manifest.digest,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
