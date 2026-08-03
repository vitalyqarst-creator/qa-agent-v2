from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.start_full_process_observation import (  # noqa: E402
    BootstrapError,
    execute_observation,
    resolve_plan,
)


def _runtime_diagnostics(run_dir: Path) -> str:
    runtime = run_dir / "runtime"
    if not runtime.is_dir():
        return ""
    chunks: list[str] = []
    paths = sorted(runtime.rglob("stderr.txt")) + sorted(runtime.rglob("summary.json"))
    for path in paths:
        try:
            data = path.read_bytes()
        except OSError:
            continue
        chunks.append(data[-262_144:].decode("utf-8", errors="replace"))
    return "\n".join(chunks)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a schema-v2 observation from an honest local-controller anchor."
    )
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--observation-id", required=True)
    parser.add_argument("--attempt-dir", type=Path, required=True)
    args = parser.parse_args()
    attempt_result = args.attempt_dir.resolve() / "attempt-result.json"
    try:
        plan = resolve_plan(
            repo_root=args.repo_root.resolve(),
            config_path=args.config,
            request_started_epoch_ms=int(time.time() * 1000),
            codex_turn_id=args.observation_id,
            request_start_source="controller-job-start",
        )
        payload = execute_observation(plan)
        status = str(payload.get("status") or "terminal-failed")
        error = str(payload.get("error") or "")
        diagnostic_text = (
            json.dumps(payload, ensure_ascii=False) + "\n" + _runtime_diagnostics(plan.run_dir)
        ).casefold()
        if status == "signed-off":
            classification = "completed"
        elif status == "blocked-input":
            classification = "scope-blocker"
        elif any(
            marker in diagnostic_text
            for marker in (
                "capacity",
                "network",
                "backend unavailable",
                "no verified codex",
                "rate limit",
                "temporarily unavailable",
                "stream disconnected",
                "retrying sampling request",
            )
        ):
            classification = "transient"
        else:
            classification = "infrastructure"
        attempt_result.write_text(
            json.dumps(
                {
                    "classification": classification,
                    "reason": (
                        error
                        or (
                            f"{status}; transient backend evidence is present in runtime logs"
                            if classification == "transient"
                            else status
                        )
                    ),
                    "benchmark_status": status,
                    "result_links": [
                        plan.run_dir.relative_to(plan.repo_root).as_posix(),
                        plan.execution_summary.relative_to(plan.repo_root).as_posix(),
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0 if classification == "completed" else 3
    except (BootstrapError, OSError, ValueError, json.JSONDecodeError) as exc:
        attempt_result.write_text(
            json.dumps(
                {
                    "classification": "infrastructure",
                    "reason": str(exc),
                    "result_links": [],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(f"local observation error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
