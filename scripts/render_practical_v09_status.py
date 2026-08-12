"""Render a human-readable v0.9 status from canonical state and validation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from test_case_agent.practical_v09 import PracticalV09Error, load_workflow_state, read_json, workflow_artifact_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render, but do not persist, practical v0.9 status.")
    parser.add_argument("--ft-package-root", type=Path, required=True)
    parser.add_argument("--workflow-state", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    package_root = args.ft_package_root.resolve()
    state = load_workflow_state(args.workflow_state.resolve(), package_root)
    report_path = workflow_artifact_path(state, package_root, "validator_report")
    report = read_json(report_path) if report_path is not None and report_path.is_file() else None
    print(f"# Статус scope {state['scope_id']} — {state['scope_slug']}")
    print()
    print(f"- Этап: `{state['phase']}`")
    print(f"- Следующее действие: {state['next_action']}")
    print(f"- Доработки матрицы: {state['matrix_revision_count']} из 1")
    print(f"- Доработки тест-кейсов: {state['tc_revision_count']} из 1")
    print(f"- Финальный вердикт: `{state['final_verdict']}`")
    print(f"- Matrix review обязателен: {'да' if state.get('matrix_review_required') else 'нет'}")
    if report is None:
        print("- Scoped validator: ещё не запускался.")
    else:
        summary = report.get("summary", {})
        print(
            "- Scoped validator: "
            f"blocking={summary.get('blocking_count', '?')}; "
            f"warnings={summary.get('warnings_count', '?')}; "
            f"clean={'да' if summary.get('clean') else 'нет'}."
        )
    reviews = state.get("reviews", [])
    if isinstance(reviews, list) and reviews and isinstance(reviews[-1], dict):
        latest = reviews[-1]
        print(
            f"- \u041f\u043e\u0441\u043b\u0435\u0434\u043d\u0435\u0435 review: "
            f"`{latest.get('mode')}` / `{latest.get('verdict')}`."
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PracticalV09Error as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
