from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.agent_driven_create_new_goal_report import (  # noqa: E402
    DEFAULT_PACKAGE_ID,
    build_agent_driven_create_new_goal_report,
    write_agent_driven_create_new_goal_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build final agent-driven create-new goal report.")
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--test-cases-dir", required=True, type=Path)
    parser.add_argument("--package-id", default=DEFAULT_PACKAGE_ID)
    parser.add_argument("--test-result", action="append", default=[], help="Recorded test result: command => result")
    args = parser.parse_args()

    tests_run = [_parse_test_result(item) for item in args.test_result]
    report = build_agent_driven_create_new_goal_report(
        package_id=args.package_id,
        work_dir=args.work_dir,
        git_status_test_cases=_git_status(args.test_cases_dir),
        tests_run=tests_run,
        created_by_tool="scripts/build_agent_driven_create_new_goal_report.py",
    )
    json_path, md_path = write_agent_driven_create_new_goal_report(report, args.work_dir)
    print(
        json.dumps(
            {
                "goal_report_path": str(json_path),
                "goal_report_markdown_path": str(md_path),
                "goal_status": report.goal_status,
                "executed_stages": report.executed_stages,
                "skipped_stages": report.skipped_stages,
                "recommended_next_action": report.recommended_next_action,
                "blocking_reasons": report.blocking_reasons,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _parse_test_result(value: str) -> dict[str, str]:
    if "=>" in value:
        command, result = value.split("=>", 1)
        return {"command": command.strip(), "result": result.strip()}
    return {"command": value.strip(), "result": "recorded"}


def _git_status(path: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short", "--", str(path)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        return [result.stderr.strip() or "git status failed"]
    return [line for line in result.stdout.splitlines() if line.strip()]


if __name__ == "__main__":
    raise SystemExit(main())
