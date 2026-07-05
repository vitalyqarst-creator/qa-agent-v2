from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.writer_package_tasks import (  # noqa: E402
    build_writer_package_tasks,
    write_writer_package_tasks,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build writer task artifacts from manual update work packages."
    )
    parser.add_argument(
        "--packages",
        required=True,
        type=Path,
        help="manual-update-packages.<old>-to-<new>.json",
    )
    parser.add_argument(
        "--out-dir",
        required=True,
        type=Path,
        help="Output directory for writer task artifacts.",
    )
    args = parser.parse_args()

    report = build_writer_package_tasks(
        manual_update_packages_path=args.packages,
        created_by_tool="scripts/build_writer_package_tasks.py",
    )
    report_path, summary_path, task_paths = write_writer_package_tasks(report, args.out_dir)
    payload = {
        "writer_package_tasks_path": str(report_path),
        "writer_package_tasks_summary_path": str(summary_path),
        "writer_package_task_paths": [str(path) for path in task_paths],
        "task_status": report.summary["task_status"],
        "tasks_total": report.summary["tasks_total"],
        "file_bound_tasks": report.summary["file_bound_tasks"],
        "unlinked_tasks": report.summary["unlinked_tasks"],
        "create_new_candidate_tasks": report.summary["create_new_candidate_tasks"],
        "large_package_tasks": report.summary["large_package_tasks"],
        "largest_task_plan_items_count": report.summary["largest_task_plan_items_count"],
        "warnings_count": len(report.warnings),
        "blocking_reasons_count": len(report.blocking_reasons),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
