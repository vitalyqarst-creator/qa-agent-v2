from __future__ import annotations

import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_CASES_DIR = ROOT / "fts" / "AutoFin" / "test-cases"
OUTPUT_PATH = TEST_CASES_DIR / "fixture-catalog.md"

EXCLUDED_FILES = {
    "14-application-card.md",  # Aggregate file; including it duplicates scope fixtures.
    "fixture-catalog.md",
}

FIXTURE_RE = re.compile(r"\b(?:FIX|FX)-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")
TC_HEADING_RE = re.compile(r"^(#{2,4})\s+(TC-[A-Z0-9-]+)\b")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def clean_title(raw: str) -> str:
    value = raw.strip()
    value = re.sub(r"^\*\*Название:\*\*\s*", "", value)
    value = re.sub(r"^\*\*.*?Name.*?:\*\*\s*", "", value, flags=re.I)
    return value.strip()


def collect_tc_blocks(lines: list[str]) -> list[dict[str, int | str]]:
    blocks: list[dict[str, int | str]] = []
    current: dict[str, int | str] | None = None
    for index, line in enumerate(lines):
        match = TC_HEADING_RE.match(line)
        if not match:
            continue
        if current is not None:
            current["end"] = index
            blocks.append(current)
        current = {
            "tc_id": match.group(2),
            "start": index,
            "end": len(lines),
        }
    if current is not None:
        blocks.append(current)
    return blocks


def extract_title(block_lines: list[str]) -> str:
    for line in block_lines[1:12]:
        if "Название" in line or "Name" in line:
            return clean_title(line)
    return ""


def extract_test_data_sections(block_lines: list[str]) -> list[str]:
    sections: list[str] = []
    index = 0
    while index < len(block_lines):
        heading_match = HEADING_RE.match(block_lines[index])
        if not heading_match:
            index += 1
            continue

        heading_text = heading_match.group(2).strip().lower()
        if heading_text not in {"тестовые данные", "test data"}:
            index += 1
            continue

        section_level = len(heading_match.group(1))
        start = index + 1
        end = start
        while end < len(block_lines):
            next_heading = HEADING_RE.match(block_lines[end])
            if next_heading and len(next_heading.group(1)) <= section_level:
                break
            end += 1

        content = "\n".join(block_lines[start:end]).strip()
        if content:
            sections.append(content)
        index = end
    return sections


def is_meaningful_test_data(content: str) -> bool:
    normalized = re.sub(r"\s+", " ", content).strip().lower()
    return normalized not in {
        "не требуются.",
        "не требуется.",
        "не требуются",
        "не требуется",
        "n/a",
        "-",
    }


def build_catalog() -> tuple[int, int, int]:
    source_files = [
        path
        for path in sorted(TEST_CASES_DIR.glob("*.md"), key=lambda item: item.name.lower())
        if path.name not in EXCLUDED_FILES
    ]

    records: list[dict[str, object]] = []
    fixture_index: dict[str, list[str]] = {}
    file_stats: list[tuple[str, int, int]] = []

    for path in source_files:
        text = read_text(path)
        lines = text.splitlines()
        tc_blocks = collect_tc_blocks(lines)
        file_record_count = 0

        for block in tc_blocks:
            start = int(block["start"])
            end = int(block["end"])
            tc_id = str(block["tc_id"])
            block_lines = lines[start:end]
            fixture_ids = sorted(set(FIXTURE_RE.findall("\n".join(block_lines))))
            test_data = [
                section
                for section in extract_test_data_sections(block_lines)
                if is_meaningful_test_data(section)
            ]

            if not fixture_ids and not test_data:
                continue

            records.append(
                {
                    "file": path.name,
                    "tc_id": tc_id,
                    "title": extract_title(block_lines),
                    "fixture_ids": fixture_ids,
                    "test_data": test_data,
                }
            )
            file_record_count += 1
            for fixture_id in fixture_ids:
                fixture_index.setdefault(fixture_id, []).append(f"{tc_id} ({path.name})")

        file_stats.append((path.name, len(tc_blocks), file_record_count))

    output_lines: list[str] = [
        "# AutoFin Fixture Catalog",
        "",
        "## Metadata",
        "",
        "| field | value |",
        "| --- | --- |",
        "| ft_slug | `AutoFin` |",
        f"| generated_on | `{date.today().isoformat()}` |",
        "| source_dir | `fts/AutoFin/test-cases` |",
        "| excluded | `14-application-card.md` aggregate file to avoid duplicate fixture rows |",
        "",
        "## Summary",
        "",
        f"- Source files scanned: `{len(source_files)}`",
        f"- Test cases with fixture IDs or explicit test data: `{len(records)}`",
        f"- Distinct fixture IDs: `{len(fixture_index)}`",
        "",
        "## Source File Coverage",
        "",
        "| source_file | total_tc_headings | tc_with_fixture_or_test_data |",
        "| --- | ---: | ---: |",
    ]

    for file_name, total, with_data in file_stats:
        output_lines.append(f"| `{file_name}` | {total} | {with_data} |")

    output_lines.extend(["", "## Fixture ID Index", ""])
    if fixture_index:
        output_lines.extend(["| fixture_id | used_by |", "| --- | --- |"])
        for fixture_id in sorted(fixture_index):
            used_by = "<br>".join(f"`{usage}`" for usage in fixture_index[fixture_id])
            output_lines.append(f"| `{fixture_id}` | {used_by} |")
    else:
        output_lines.append("No explicit `FIX-*` or `FX-*` fixture IDs found.")

    output_lines.extend(["", "## Test Data By Source File", ""])
    current_file = None
    for record in records:
        file_name = str(record["file"])
        if file_name != current_file:
            current_file = file_name
            output_lines.extend([f"### `{current_file}`", ""])

        heading = f"#### `{record['tc_id']}`"
        title = str(record["title"])
        if title:
            heading += f" - {title}"
        output_lines.extend([heading, ""])

        fixture_ids = list(record["fixture_ids"])
        if fixture_ids:
            output_lines.append(
                "- Fixture IDs: " + ", ".join(f"`{fixture_id}`" for fixture_id in fixture_ids)
            )
        else:
            output_lines.append("- Fixture IDs: none explicit")

        test_data = list(record["test_data"])
        if test_data:
            output_lines.extend(["", "Test data:"])
            for section_index, content in enumerate(test_data, 1):
                if len(test_data) > 1:
                    output_lines.extend(["", f"Block {section_index}:"])
                output_lines.extend(["", "```markdown", str(content), "```"])
        output_lines.append("")

    OUTPUT_PATH.write_text("\n".join(output_lines).rstrip() + "\n", encoding="utf-8")
    return len(source_files), len(records), len(fixture_index)


if __name__ == "__main__":
    source_count, record_count, fixture_count = build_catalog()
    print(f"Wrote {OUTPUT_PATH}")
    print(f"Source files: {source_count}")
    print(f"Records: {record_count}")
    print(f"Distinct fixture IDs: {fixture_count}")
