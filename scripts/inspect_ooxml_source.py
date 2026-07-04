from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_case_agent.ooxml_loader import (  # noqa: E402
    PARSER_MODE_STRICT,
    PARSER_MODE_TOLERANT,
    SourceNode,
    load_ooxml_source,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect DOCX OOXML source coverage.")
    parser.add_argument("source", type=Path, help="Path to a .docx file.")
    parser.add_argument("--json", action="store_true", help="Print coverage audit as JSON.")
    parser.add_argument("--summary", action="store_true", help="Print summary counts.")
    parser.add_argument("--find-markers", action="store_true", help="Find marker strings in source nodes.")
    parser.add_argument(
        "--marker-regex",
        default=r"\bLXML_[A-Z0-9_]+__[A-F0-9]{8}\b",
        help="Regex used by --find-markers.",
    )
    parser.add_argument(
        "--tolerant",
        action="store_true",
        help="Use explicit tolerant XML parser mode with recover=True and an audit warning.",
    )
    args = parser.parse_args()

    parser_mode = PARSER_MODE_TOLERANT if args.tolerant else PARSER_MODE_STRICT
    source = load_ooxml_source(args.source, parser_mode=parser_mode)
    markers = find_markers(source.nodes, args.marker_regex) if args.find_markers else []
    payload = {
        "coverage_audit": source.coverage.to_dict(),
        "summary_counts": summary_counts(source.nodes, source.coverage.to_dict()),
        "markers": markers,
        "files_read": [str(args.source)],
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.summary or not args.find_markers:
        print("Summary counts:")
        for key, value in payload["summary_counts"].items():
            print(f"- {key}: {value}")

    if args.find_markers:
        print("Markers:")
        for marker in markers:
            print(f"- {marker['marker']} | {marker['part']} | {marker['node_id']}")
        if not markers:
            print("- none")

    print("Files read:")
    for file_read in payload["files_read"]:
        print(f"- {file_read}")
    return 0


def find_markers(nodes: list[SourceNode], marker_regex: str) -> list[dict[str, Any]]:
    pattern = re.compile(marker_regex)
    markers: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for node in nodes:
        for match in pattern.finditer(node.value):
            key = (match.group(0), node.part, node.node_id)
            if key in seen:
                continue
            seen.add(key)
            markers.append(
                {
                    "marker": match.group(0),
                    "node_id": node.node_id,
                    "part": node.part,
                    "xpath": node.xpath,
                    "value_type": node.value_type,
                    "flags": list(node.flags),
                    "target_part": node.target_part,
                    "target_url": node.target_url,
                }
            )
    return markers


def summary_counts(nodes: list[SourceNode], audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_nodes": len(nodes),
        "zip_entries_seen": len(audit["zip_entries_seen"]),
        "xml_parts_extracted": len(audit["xml_parts_extracted"]),
        "rels_parts_extracted": len(audit["rels_parts_extracted"]),
        "binary_parts_seen": len(audit["binary_parts_seen"]),
        "extraction_warnings": len(audit["extraction_warnings"]),
        "comments_count": audit["comments_count"],
        "footnotes_count": audit["footnotes_count"],
        "endnotes_count": audit["endnotes_count"],
        "headers_count": audit["headers_count"],
        "footers_count": audit["footers_count"],
        "hyperlinks_count": audit["hyperlinks_count"],
        "images_count": audit["images_count"],
        "hidden_text_count": audit["hidden_text_count"],
        "tracked_insert_count": audit["tracked_insert_count"],
        "tracked_delete_count": audit["tracked_delete_count"],
        "textboxes_count": audit["textboxes_count"],
        "custom_xml_parts_count": audit["custom_xml_parts_count"],
    }


if __name__ == "__main__":
    raise SystemExit(main())
