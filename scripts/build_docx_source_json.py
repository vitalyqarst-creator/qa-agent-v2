from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from test_case_agent.source_json_projection import write_docx_source_json


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a deterministic machine-readable JSON projection from DOCX."
    )
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--docx", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    write_docx_source_json(
        args.docx,
        repo_root=args.repo_root,
        output_path=args.output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
