from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.requirements_registry import (  # noqa: E402
    build_requirements_registry,
    write_requirements_registry,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a requirements registry JSONL for one FT source version."
    )
    parser.add_argument(
        "--source-manifest",
        required=True,
        type=Path,
        help="Path to source-manifest.<version>.json.",
    )
    parser.add_argument(
        "--out-dir",
        required=True,
        type=Path,
        help="Output directory for requirements JSONL and summary JSON.",
    )
    args = parser.parse_args()

    registry = build_requirements_registry(
        args.source_manifest,
        created_by_tool="scripts/build_requirements_registry.py",
    )
    registry_path, summary_path = write_requirements_registry(registry, args.out_dir)
    payload = {
        "registry_path": str(registry_path),
        "summary_path": str(summary_path),
        "registry_status": registry.extraction_summary["registry_status"],
        "entries_total": registry.extraction_summary["entries_total"],
        "active": registry.extraction_summary["active"],
        "gap": registry.extraction_summary["gap"],
        "unclear": registry.extraction_summary["unclear"],
        "source_only": registry.extraction_summary["source_only"],
        "warnings_count": len(registry.warnings),
        "blocking_reasons_count": len(registry.blocking_reasons),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
