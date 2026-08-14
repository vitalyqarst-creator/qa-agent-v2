from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from test_case_agent.test_data_sources import validate_plan_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Проверить план источников тестовых данных")
    parser.add_argument("plan", type=Path)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args()
    errors = validate_plan_file(args.plan, repo_root=args.repo_root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("OK: план источников тестовых данных корректен")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
