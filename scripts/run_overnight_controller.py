from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from test_case_agent.overnight_controller import (  # noqa: E402
    ControllerError,
    OvernightController,
    initialize_run,
    load_state,
    render_summary,
)


def _read_object(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ControllerError(f"JSON object expected: {path}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create, resume and inspect a durable sequential overnight work queue."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    initialize = subparsers.add_parser("init")
    initialize.add_argument("--plan", type=Path, required=True)
    initialize.add_argument("--run-dir", type=Path, required=True)
    initialize.add_argument("--run-id", required=True)
    initialize.add_argument("--repo-root", type=Path, default=ROOT)

    run = subparsers.add_parser("run")
    run.add_argument("--state", type=Path, required=True)
    run.add_argument("--only-job")
    run.add_argument("--max-jobs", type=int)
    run.add_argument("--max-idle-seconds", type=int, default=0)

    retry = subparsers.add_parser("retry")
    retry.add_argument("--state", type=Path, required=True)
    retry.add_argument("--job", required=True)

    status = subparsers.add_parser("status")
    status.add_argument("--state", type=Path, required=True)
    status.add_argument("--json", action="store_true")

    summary = subparsers.add_parser("summary")
    summary.add_argument("--state", type=Path, required=True)
    summary.add_argument("--output", type=Path)

    args = parser.parse_args()
    try:
        if args.command == "init":
            plan = _read_object(args.plan.resolve())
            jobs = plan.get("jobs")
            if not isinstance(jobs, list) or not all(isinstance(item, dict) for item in jobs):
                raise ControllerError("overnight plan jobs must be an object array")
            goal = plan.get("goal")
            if not isinstance(goal, str):
                raise ControllerError("overnight plan goal must be text")
            source_guard = plan.get("source_guard", [])
            if not isinstance(source_guard, list) or not all(isinstance(item, str) for item in source_guard):
                raise ControllerError("overnight plan source_guard must be a string array")
            state_path = initialize_run(
                run_dir=args.run_dir,
                run_id=args.run_id,
                goal=goal,
                jobs=jobs,
                repo_root=args.repo_root.resolve(),
                source_guard_paths=(
                    (args.repo_root / item).resolve() if not Path(item).is_absolute() else Path(item).resolve()
                    for item in source_guard
                ),
            )
            print(json.dumps({"status": "initialized", "state": str(state_path)}, ensure_ascii=False))
            return 0
        if args.command == "run":
            payload = OvernightController(args.state).run(
                only_job=args.only_job,
                max_jobs=args.max_jobs,
                max_idle_seconds=args.max_idle_seconds,
            )
            print(
                json.dumps(
                    {
                        "status": payload["overall_status"],
                        "state": str(args.state.resolve()),
                        "completed_work": payload["completed_work"],
                        "deferred_transient": payload["deferred_transient"],
                        "scope_blockers": payload["scope_blockers"],
                        "failed_infrastructure": payload["failed_infrastructure"],
                        "global_blocker": payload["global_blocker"],
                    },
                    ensure_ascii=False,
                )
            )
            return 3 if payload.get("global_blocker") else 0
        if args.command == "retry":
            controller = OvernightController(args.state)
            controller.retry(args.job)
            print(json.dumps({"status": "requeued", "job_id": args.job}, ensure_ascii=False))
            return 0
        if args.command == "status":
            payload = load_state(args.state.resolve())
            print(
                json.dumps(payload, ensure_ascii=False, indent=2)
                if args.json
                else render_summary(payload)
            )
            return 0
        if args.command == "summary":
            payload = load_state(args.state.resolve())
            text = render_summary(payload)
            output = args.output or args.state.resolve().with_name("overnight-summary.md")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(text, encoding="utf-8", newline="\n")
            print(json.dumps({"status": "written", "output": str(output.resolve())}, ensure_ascii=False))
            return 0
    except (ControllerError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"overnight controller error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
