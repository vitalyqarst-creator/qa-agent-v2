from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from test_case_agent.incremental_update import (  # noqa: E402
    IncrementalUpdateError,
    run_incremental_update,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the conditional ft-test-case-iteration incremental-update mode."
    )
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run_incremental_update(
            repo_root=args.repo_root.resolve(),
            config_path=args.config.resolve(),
        )
    except (IncrementalUpdateError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"incremental update error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "status": result.status,
                "run_dir": str(result.run_dir),
                "shadow_suite": str(result.shadow_suite) if result.shadow_suite else None,
                "release_manifest": str(result.release_manifest),
                "writer_invocation_count": result.writer_invocation_count,
                "change_count": result.change_count,
                "reused_case_count": result.reused_case_count,
                "modified_case_count": result.modified_case_count,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if result.status in {"signed-off", "shadow-accepted"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
