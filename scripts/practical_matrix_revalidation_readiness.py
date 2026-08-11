"""Check whether a preserved practical TC suite is fit for matrix revalidation.

Matrix revalidation after canonical test cases exist is intentionally narrow: it
may restore a stale matrix binding, but it cannot repair an older writer
package.  Running a separate reviewer before detecting durable TC-package
defects wastes a reviewer session and obscures the real blocker.  This
controller-only check therefore runs *before* a new matrix reviewer is
dispatched.  It is read-only and reports only durable canonical-suite defects;
ordinary transitional matrix-revalidation findings are deliberately excluded.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import practical_review_preflight as review_preflight  # noqa: E402


# These workflow findings are emitted only after the writer has produced a
# canonical suite and express prerequisites that a matrix reviewer cannot fix.
CANONICAL_SUITE_WORKFLOW_FINDINGS = {
    "workflow-state-ready-for-review-missing-handoff-source-rows",
    "workflow-state-ready-for-review-without-passing-writer-quality-gate",
}


def _path_belongs_to_scope(path_value: str, descriptor: review_preflight.ScopeDescriptor) -> bool:
    normalized = path_value.replace("\\", "/").casefold()
    return descriptor.handoff_dir.as_posix().casefold() in normalized or any(
        candidate.casefold() in normalized for candidate in descriptor.canonical_test_case_paths
    )


def canonical_suite_blockers(
    report: dict[str, Any],
    descriptors: list[review_preflight.ScopeDescriptor],
) -> list[dict[str, str]]:
    """Project validator findings down to durable saved-suite prerequisites."""

    blockers: list[dict[str, str]] = []
    for finding in report.get("findings", []):
        if not isinstance(finding, dict) or finding.get("severity") != "error":
            continue
        finding_id = str(finding.get("id") or "")
        if finding_id not in CANONICAL_SUITE_WORKFLOW_FINDINGS:
            continue
        path_value = str(finding.get("path") or "")
        matching_scope = next(
            (item for item in descriptors if _path_belongs_to_scope(path_value, item)),
            None,
        )
        if matching_scope is None:
            continue
        blockers.append(
            {
                "scope_id": matching_scope.scope_id,
                "id": finding_id,
                "path": path_value,
                "details": str(finding.get("details") or ""),
                "recommended_action": str(finding.get("recommended_action") or ""),
            }
        )
    return blockers


def build_readiness(
    *, ft_package_root: Path, scope_ids: list[str]
) -> dict[str, Any]:
    ft_package_root = ft_package_root.resolve()
    descriptors, descriptor_issues = review_preflight.scope_descriptors(
        ft_package_root, scope_ids
    )
    blockers: list[dict[str, str]] = [
        {
            "scope_id": "",
            "id": "matrix-revalidation-scope-descriptor-invalid",
            "path": "",
            "details": issue,
            "recommended_action": "Исправить handoff области до повторного review матрицы.",
        }
        for issue in descriptor_issues
    ]
    state_issues: list[dict[str, str]] = []
    expected = {
        "current_stage": "ft-test-case-writer",
        "stage_status": "ready-for-review",
        "next_skill": "ft-test-case-reviewer",
        "review_mode": "matrix_review",
        "matrix_review_status": "invalidated",
        "matrix_revalidation_reason": "reviewed-matrix-hash-mismatch",
    }
    for descriptor in descriptors:
        try:
            state = review_preflight.artifact_validator.parse_workflow_state(
                descriptor.workflow_path
            )
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            state_issues.append(
                {
                    "scope_id": descriptor.scope_id,
                    "id": "matrix-revalidation-workflow-unreadable",
                    "path": descriptor.workflow_path.as_posix(),
                    "details": str(exc),
                    "recommended_action": "Восстановить читаемый workflow-state.yaml.",
                }
            )
            continue
        for key, value in expected.items():
            if str(state.get(key) or "").strip() != value:
                state_issues.append(
                    {
                        "scope_id": descriptor.scope_id,
                        "id": "matrix-revalidation-state-mismatch",
                        "path": descriptor.workflow_path.as_posix(),
                        "details": f"{key}={state.get(key)!r}; expected {value!r}",
                        "recommended_action": "Не запускать matrix review: восстановить каноническое состояние revalidation.",
                    }
                )
        if str(state.get("current_round") or "").strip() != "2":
            state_issues.append(
                {
                    "scope_id": descriptor.scope_id,
                    "id": "matrix-revalidation-round-invalid",
                    "path": descriptor.workflow_path.as_posix(),
                    "details": f"current_round={state.get('current_round')!r}; expected 2",
                    "recommended_action": "Не запускать matrix review: восстановить current_round=2.",
                }
            )
    blockers.extend(state_issues)
    if not blockers:
        report = review_preflight.artifact_validator.validate(ft_package_root)
        blockers.extend(canonical_suite_blockers(report, descriptors))

    return {
        "schema_version": 1,
        "status": "ready-for-matrix-revalidation" if not blockers else "blocked",
        "allowed": not blockers,
        "ft_package_root": ft_package_root.as_posix(),
        "scope_ids": scope_ids,
        "checks": [
            {
                "id": "matrix-revalidation-canonical-suite-readiness",
                "status": "pass" if not blockers else "fail",
                "details": f"blocking_reasons={len(blockers)}",
            }
        ],
        "blocking_reasons": blockers,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check saved canonical test-case readiness before matrix revalidation."
    )
    parser.add_argument("--ft-package-root", type=Path, required=True)
    parser.add_argument("--scope-id", action="append", required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_readiness(
        ft_package_root=args.ft_package_root,
        scope_ids=list(dict.fromkeys(args.scope_id)),
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        output = args.output if args.output.is_absolute() else Path.cwd() / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["allowed"] else 2


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
