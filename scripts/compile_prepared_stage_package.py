from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.review_cycle.prepared_compiler import (  # noqa: E402
    DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE,
    RELEASE_OUTPUT_MODE,
    PreparedCompilerDiagnostic,
    compile_workflow_package,
)
from test_case_agent.review_cycle.runtime import StageRuntimeError  # noqa: E402


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Compile an immutable prepared package from workflow-state canonical artifacts"
    )
    result.add_argument("--workflow-state", required=True)
    result.add_argument("--output-root", required=True)
    result.add_argument("--package-id", required=True)
    result.add_argument("--attempt-root", required=True)
    result.add_argument("--expected-ft-slug", required=True)
    result.add_argument("--section-id")
    result.add_argument("--repo-root", default=".")
    result.add_argument("--reuse-if-current", action="store_true")
    result.add_argument(
        "--output-mode",
        choices=(RELEASE_OUTPUT_MODE, DRAFT_WITH_BLOCKING_GAPS_OUTPUT_MODE),
        default=RELEASE_OUTPUT_MODE,
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    try:
        compiled = compile_workflow_package(
            workflow_state=(repo_root / args.workflow_state),
            repo_root=repo_root,
            output_root=(repo_root / args.output_root),
            package_id=args.package_id,
            attempt_root=(repo_root / args.attempt_root),
            expected_ft_slug=args.expected_ft_slug,
            section_id=args.section_id,
            reuse_if_current=args.reuse_if_current,
            output_mode=args.output_mode,
        )
    except (OSError, StageRuntimeError, ValueError) as exc:
        payload: dict[str, object] = {
            "status": "blocked",
            "reason": str(exc),
            "output_mode": args.output_mode,
        }
        if isinstance(exc, PreparedCompilerDiagnostic):
            payload["error_code"] = exc.code
            payload["details"] = list(exc.details)
        print(json.dumps(payload, ensure_ascii=False))
        return 2
    print(
        json.dumps(
            {
                "status": "reused" if compiled.cache_reused else "built",
                "stage_package": compiled.stage_package.relative_to(repo_root).as_posix(),
                "obligations": compiled.obligation_count,
                "coverage_gaps": compiled.gap_count,
                "dictionary_refs": compiled.dictionary_ref_count,
                "section_id": compiled.section_id,
                "execution_profile": compiled.execution_profile,
                "unsupported_dimensions": list(compiled.unsupported_dimensions),
                "fast_path_eligible": not compiled.unsupported_dimensions,
                "output_mode": compiled.output_mode,
                "release_eligible": compiled.release_eligible,
                "blocking_gap_ids": list(compiled.blocking_gap_ids),
                "release_blocking_finding_codes": list(
                    compiled.release_blocking_finding_codes
                ),
                "execution_dependency_count": compiled.execution_dependency_count,
                "excluded_execution_obligation_ids": list(
                    compiled.excluded_execution_obligation_ids
                ),
                "cache_reused": compiled.cache_reused,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
