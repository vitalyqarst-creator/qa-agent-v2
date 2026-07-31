from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from test_case_agent.practical_release import (  # noqa: E402
    PracticalReleaseError,
    build_practical_release,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build a practical FT test-case release: one combined Markdown file, "
            "a lightweight coverage matrix, and a release quality report."
        )
    )
    parser.add_argument("--root", type=Path, required=True, help="FT package root, for example fts/Partners/Partners-v1.")
    parser.add_argument("--output-dir", type=Path, help="Output directory. Defaults to <root>/work/exports.")
    parser.add_argument("--release-name", default="all-test-cases", help="Base filename without extension.")
    parser.add_argument(
        "--files",
        type=Path,
        nargs="+",
        help=(
            "Optional explicit test-case files in FT/PDF order. Paths may be "
            "absolute or relative to --root."
        ),
    )
    parser.add_argument("--json", action="store_true", help="Print JSON summary instead of a short text summary.")
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Return exit code 1 when the release has warnings. Errors always return 1.",
    )
    args = parser.parse_args(argv)

    try:
        result, findings = build_practical_release(
            args.root,
            output_dir=args.output_dir,
            release_name=args.release_name,
            source_files=args.files,
        )
    except (OSError, PracticalReleaseError) as error:
        print(str(error), file=sys.stderr)
        return 2

    if args.json:
        print(
            json.dumps(
                {
                    "result": result.__dict__,
                    "findings_count": len(findings),
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(f"status={result.status}")
        print(f"test_case_count={result.test_case_count}")
        print(f"combined_file={result.combined_file}")
        print(f"coverage_matrix={result.coverage_matrix}")
        print(f"quality_report={result.quality_report_md}")

    if result.finding_counts.get("error", 0):
        return 1
    if args.fail_on_warning and result.finding_counts.get("warning", 0):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
