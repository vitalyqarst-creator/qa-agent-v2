from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.create_new_tc_context_bundle import (  # noqa: E402
    DEFAULT_PACKAGE_ID,
    build_create_new_tc_context_bundle,
    write_create_new_tc_context_bundle,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a read-only create-new-TC context bundle for a manual update package."
    )
    parser.add_argument("--work-dir", required=True, type=Path, help="Directory containing pipeline artifacts.")
    parser.add_argument("--test-cases-dir", required=True, type=Path, help="Canonical test-cases directory.")
    parser.add_argument("--package-id", default=DEFAULT_PACKAGE_ID, help="Package id to bundle.")
    parser.add_argument("--old-version", default="autofin-prefinal", help="Old source version slug.")
    parser.add_argument("--new-version", default="autofin-final", help="New source version slug.")
    args = parser.parse_args()

    work_dir = args.work_dir
    pair = f"{args.old_version}-to-{args.new_version}"
    bundle = build_create_new_tc_context_bundle(
        package_id=args.package_id,
        manual_update_packages_path=work_dir / f"manual-update-packages.{pair}.json",
        writer_package_tasks_path=work_dir / f"writer-package-tasks.{pair}.json",
        update_plan_path=work_dir / f"test-case-update-plan.{pair}.json",
        impact_report_path=work_dir / f"impact-report.{pair}.json",
        requirements_diff_path=work_dir / f"requirements-diff.{pair}.json",
        old_registry_path=work_dir / f"requirements.{args.old_version}.jsonl",
        new_registry_path=work_dir / f"requirements.{args.new_version}.jsonl",
        old_source_manifest_path=work_dir / f"source-manifest.{args.old_version}.json",
        new_source_manifest_path=work_dir / f"source-manifest.{args.new_version}.json",
        test_cases_dir=args.test_cases_dir,
        created_by_tool="scripts/build_create_new_tc_context_bundle.py",
    )
    json_path, markdown_path = write_create_new_tc_context_bundle(bundle, work_dir)
    payload = {
        "bundle_path": str(json_path),
        "bundle_markdown_path": str(markdown_path),
        "bundle_status": bundle.bundle_status,
        "package_id": bundle.package_id,
        "package_type": bundle.package_type,
        "plan_item_count": len(bundle.plan_item_ids),
        "candidate_requirement_count": len(bundle.candidate_requirements),
        "candidate_group_count": len(bundle.candidate_groups),
        "duplicate_risk_count": len(bundle.duplicate_risks),
        "recommended_draft_target_count": len(bundle.recommended_draft_targets),
        "warnings_count": len(bundle.warnings),
        "blocking_reasons": bundle.blocking_reasons,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
