from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.source_manifest import (  # noqa: E402
    build_source_manifest,
    write_source_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a source manifest for an FT source version.")
    parser.add_argument("--ft-slug", required=True, help="FT package slug, for example AutoFin.")
    parser.add_argument("--source-version", required=True, help="Stable source version id.")
    parser.add_argument("--docx", required=True, type=Path, help="Primary DOCX source path.")
    parser.add_argument("--pdf", type=Path, help="Primary PDF source path.")
    parser.add_argument("--xhtml", type=Path, help="Primary XHTML source path.")
    parser.add_argument("--support", action="append", type=Path, default=[], help="Support file path. Repeatable.")
    parser.add_argument("--mockup", action="append", type=Path, default=[], help="Mockup file path. Repeatable.")
    parser.add_argument("--other", action="append", type=Path, default=[], help="Other source file path. Repeatable.")
    parser.add_argument("--out-dir", required=True, type=Path, help="Output directory for manifest and coverage audit JSON.")
    parser.add_argument(
        "--tolerant",
        action="store_true",
        help="Explicitly allow tolerant OOXML parser mode. Strict mode is the default.",
    )
    args = parser.parse_args()

    manifest = build_source_manifest(
        ft_slug=args.ft_slug,
        source_version=args.source_version,
        docx=args.docx,
        pdf=args.pdf,
        xhtml=args.xhtml,
        support_files=args.support,
        mockup_files=args.mockup,
        other_files=args.other,
        out_dir=args.out_dir,
        created_by_tool="scripts/build_source_manifest.py",
        parser_mode="tolerant" if args.tolerant else "strict",
        allow_tolerant=args.tolerant,
    )
    manifest_path = write_source_manifest(manifest, args.out_dir)

    payload = {
        "manifest_path": str(manifest_path),
        "coverage_audit_path": manifest.ooxml_coverage_audit_path,
        "ingestion_status": manifest.ingestion_status,
        "source_file_hashes": {
            entry.path: entry.sha256 for entry in manifest.source_files if entry.sha256
        },
        "warnings_count": len(manifest.warnings),
        "blocking_reasons_count": len(manifest.blocking_reasons),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
