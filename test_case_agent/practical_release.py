from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


TEST_CASE_HEADING_RE = re.compile(r"^##\s+(TC-[A-Za-z0-9-]+)\s*$", re.MULTILINE)
SECTION_HEADING_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
FIELD_RE_TEMPLATE = r"(?im)^\*\*{field}:\*\*\s*(.+?)\s*$"

REQUIREMENT_REF_RE = re.compile(
    r"\b(?:AS\.\d+|BSR\s+\d+|GSR\s+\d+|REQ-[A-Za-z0-9_.-]+|"
    r"ATOM-[A-Za-z0-9_.-]+|SRC-[A-Za-z0-9_.-]+|DICT-[A-Za-z0-9_.-]+|"
    r"FX-[A-Za-z0-9_.-]+|Table\s+\d+|PDF\s+page\s+\d+)\b",
    flags=re.IGNORECASE,
)

SCENARIO_RATIONALE_RE = re.compile(
    r"(?im)^\*\*(?:Сценарное\s+обоснование|Scenario\s+rationale):\*\*"
)
FUTURE_FT_PLACEHOLDER_RE = re.compile(
    r"(?i)(?:конкретн\w+\s+[^.\n]{0,80})?буд(?:ет|ут)\s+определ[её]н|"
    r"буд(?:ет|ут)\s+уточнен|"
    r"will\s+be\s+defined\s+in\s+ft|"
    r"ft\s+\d+\s+буд(?:ет|ут)\s+определ",
)
INTERNAL_PROCESS_MARKER_RE = re.compile(
    r"(?i)\b(?:runtime receipt|manifest digest|hash-bound|"
    r"writer|reviewer|runner|benchmark|bridge|sharding)\b"
)

ALLOWED_TEST_CASE_STATUSES = {
    "confirmed",
    "needs-ui-calibration",
    "candidate-ui-calibration",
    "needs-test-data",
    "blocked-observability",
    "blocked-ui-unavailable",
    "blocked-access",
    "needs-future-clarification",
    "mismatch-ft-ui",
    "not-automatable-manual-only",
}

REQUIRED_FIELDS = (
    "Название",
    "Тип",
    "Приоритет",
    "package_id",
    "Трассировка",
    "Статус тест-кейса",
    "Предусловия",
    "Тестовые данные",
    "Шаги",
    "Итоговый ожидаемый результат",
    "Постусловия",
)


class PracticalReleaseError(RuntimeError):
    pass


@dataclass(frozen=True)
class TestCaseRecord:
    seq_id: str
    test_case_id: str
    source_file: str
    section_title: str
    title: str
    case_type: str
    priority: str
    package_id: str
    statuses: tuple[str, ...]
    traceability: str
    requirement_refs: tuple[str, ...]
    body: str


@dataclass(frozen=True)
class ReleaseFinding:
    severity: str
    finding_id: str
    source_file: str
    test_case_id: str
    details: str


@dataclass(frozen=True)
class ReleaseBuildResult:
    ft_root: str
    output_dir: str
    combined_file: str
    coverage_matrix: str
    quality_report_md: str
    quality_report_json: str
    test_case_count: int
    source_files: tuple[str, ...]
    status_counts: dict[str, int]
    finding_counts: dict[str, int]
    status: str


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _field_value(block: str, field: str) -> str:
    pattern = re.compile(FIELD_RE_TEMPLATE.format(field=re.escape(field)))
    match = pattern.search(block)
    return match.group(1).strip() if match else ""


def _extract_section_title(text: str, fallback: str) -> str:
    match = SECTION_HEADING_RE.search(text)
    return match.group(1).strip() if match else fallback


def _normalize_statuses(raw_status: str) -> tuple[str, ...]:
    if not raw_status:
        return tuple()
    cleaned = raw_status.replace("`", "").strip()
    parts = [part.strip().lower() for part in re.split(r"[;,]", cleaned) if part.strip()]
    return tuple(parts)


def _extract_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(TEST_CASE_HEADING_RE.finditer(text))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((match.group(1), text[start:end].strip()))
    return blocks


def discover_test_case_files(ft_root: Path) -> list[Path]:
    tc_dir = ft_root / "test-cases"
    if not tc_dir.is_dir():
        raise PracticalReleaseError(f"test-cases directory not found: {tc_dir}")
    files = [
        path
        for path in tc_dir.glob("*.md")
        if path.is_file()
        and not path.name.lower().endswith("summary.md")
        and "summary" not in path.stem.lower()
    ]
    return sorted(files, key=_natural_sort_key)


def _natural_sort_key(path: Path) -> tuple[object, ...]:
    parts: list[object] = []
    for part in re.split(r"(\d+)", path.name):
        parts.append(int(part) if part.isdigit() else part.lower())
    return tuple(parts)


def parse_test_cases(ft_root: Path, files: Sequence[Path] | None = None) -> tuple[list[TestCaseRecord], list[ReleaseFinding]]:
    selected_files = list(files) if files is not None else discover_test_case_files(ft_root)
    records: list[TestCaseRecord] = []
    findings: list[ReleaseFinding] = []
    seen_ids: dict[str, str] = {}

    for file_path in selected_files:
        text = _read_text(file_path)
        rel_file = file_path.relative_to(ft_root).as_posix()
        section_title = _extract_section_title(text, file_path.stem)
        blocks = _extract_blocks(text)
        if not blocks:
            findings.append(
                ReleaseFinding("error", "release-file-has-no-test-cases", rel_file, "-", "No `## TC-*` sections found.")
            )
            continue
        for tc_id, block in blocks:
            missing_fields = [field for field in REQUIRED_FIELDS if not _field_value(block, field)]
            if missing_fields:
                findings.append(
                    ReleaseFinding(
                        "error",
                        "release-test-case-missing-required-fields",
                        rel_file,
                        tc_id,
                        "Missing fields: " + ", ".join(missing_fields),
                    )
                )
            if tc_id in seen_ids:
                findings.append(
                    ReleaseFinding(
                        "error",
                        "release-duplicate-test-case-id",
                        rel_file,
                        tc_id,
                        f"Duplicate of {seen_ids[tc_id]}.",
                    )
                )
            else:
                seen_ids[tc_id] = rel_file

            status_values = _normalize_statuses(_field_value(block, "Статус тест-кейса"))
            unknown_statuses = [status for status in status_values if status not in ALLOWED_TEST_CASE_STATUSES]
            if unknown_statuses:
                findings.append(
                    ReleaseFinding(
                        "error",
                        "release-test-case-invalid-status",
                        rel_file,
                        tc_id,
                        "Unknown statuses: " + ", ".join(unknown_statuses),
                    )
                )

            if SCENARIO_RATIONALE_RE.search(block):
                findings.append(
                    ReleaseFinding(
                        "error",
                        "release-agent-rationale-leak",
                        rel_file,
                        tc_id,
                        "`Сценарное обоснование` / `Scenario rationale` is an internal design marker.",
                    )
                )
            if FUTURE_FT_PLACEHOLDER_RE.search(block):
                findings.append(
                    ReleaseFinding(
                        "error",
                        "release-future-ft-runtime-placeholder",
                        rel_file,
                        tc_id,
                        "Runtime TC contains a future-FT placeholder instead of an executable setup/data marker.",
                    )
                )
            if INTERNAL_PROCESS_MARKER_RE.search(block):
                findings.append(
                    ReleaseFinding(
                        "warning",
                        "release-internal-process-marker",
                        rel_file,
                        tc_id,
                        "Runtime TC contains an agent/process marker; keep diagnostics in work artifacts.",
                    )
                )

            traceability = _field_value(block, "Трассировка")
            refs = tuple(dict.fromkeys(match.group(0) for match in REQUIREMENT_REF_RE.finditer(traceability)))
            if not refs:
                findings.append(
                    ReleaseFinding(
                        "error",
                        "release-test-case-unparseable-traceability",
                        rel_file,
                        tc_id,
                        "Traceability has no parseable AS/BSR/GSR/REQ/ATOM/SRC/DICT/FX/Table/PDF reference.",
                    )
                )

            records.append(
                TestCaseRecord(
                    seq_id=f"TC-{len(records) + 1:03d}",
                    test_case_id=tc_id,
                    source_file=rel_file,
                    section_title=section_title,
                    title=_field_value(block, "Название"),
                    case_type=_field_value(block, "Тип"),
                    priority=_field_value(block, "Приоритет"),
                    package_id=_field_value(block, "package_id").replace("`", "").strip(),
                    statuses=status_values,
                    traceability=traceability,
                    requirement_refs=refs,
                    body=block,
                )
            )

    if not records:
        raise PracticalReleaseError("No test cases parsed.")
    return records, findings


def _status_counts(records: Iterable[TestCaseRecord]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        for status in record.statuses or ("<missing>",):
            counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def _finding_counts(findings: Iterable[ReleaseFinding]) -> dict[str, int]:
    counts = {"error": 0, "warning": 0, "info": 0}
    for finding in findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1
    return counts


def _markdown_table_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def render_combined(records: Sequence[TestCaseRecord]) -> str:
    source_ranges: list[tuple[str, str, int, int, int]] = []
    current_key: tuple[str, str] | None = None
    start_index = 1
    count = 0
    for index, record in enumerate(records, start=1):
        key = (record.source_file, record.section_title)
        if current_key is None:
            current_key = key
            start_index = index
            count = 1
        elif key == current_key:
            count += 1
        else:
            assert current_key is not None
            source_ranges.append((current_key[0], current_key[1], start_index, index - 1, count))
            current_key = key
            start_index = index
            count = 1
    if current_key is not None:
        source_ranges.append((current_key[0], current_key[1], start_index, len(records), count))

    lines = [
        "# Единый файл тест-кейсов",
        "",
        "Правила сборки:",
        "",
        "- исходные `TC-*` сохранены как стабильные идентификаторы;",
        "- добавлена сквозная нумерация `TC-001` ... по порядку разделов;",
        "- исходные per-scope файлы не изменяются этим экспортом;",
        "- summary-файлы не включаются как тест-кейсы.",
        "",
        "## Состав",
        "",
        "| Сквозной диапазон | Раздел | Исходный файл | Количество TC |",
        "| --- | --- | --- | ---: |",
    ]
    for source_file, section_title, start, end, item_count in source_ranges:
        lines.append(
            f"| `TC-{start:03d}`–`TC-{end:03d}` | {_markdown_table_escape(section_title)} | `{source_file}` | {item_count} |"
        )
    lines.append("")

    last_section: tuple[str, str] | None = None
    for record in records:
        key = (record.source_file, record.section_title)
        if key != last_section:
            lines.append(f"## {record.section_title}")
            lines.append("")
            last_section = key
        body_without_heading = TEST_CASE_HEADING_RE.sub("", record.body, count=1).strip()
        lines.append(f"### {record.seq_id} — {record.test_case_id}")
        lines.append(f"**Сквозной номер:** `{record.seq_id}`")
        lines.append(f"**Исходный TC-ID:** `{record.test_case_id}`")
        lines.append("")
        lines.append(body_without_heading)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_coverage_matrix(records: Sequence[TestCaseRecord]) -> str:
    lines = [
        "# Practical Release Coverage Matrix",
        "",
        "| seq_id | test_case_id | source_file | section | title | type | priority | status | requirement_refs | traceability |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for record in records:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{record.seq_id}`",
                    f"`{record.test_case_id}`",
                    f"`{record.source_file}`",
                    _markdown_table_escape(record.section_title),
                    _markdown_table_escape(record.title),
                    _markdown_table_escape(record.case_type),
                    _markdown_table_escape(record.priority),
                    _markdown_table_escape(", ".join(record.statuses) if record.statuses else "<missing>"),
                    _markdown_table_escape(", ".join(record.requirement_refs)),
                    _markdown_table_escape(record.traceability),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def render_quality_report(result: ReleaseBuildResult, findings: Sequence[ReleaseFinding]) -> str:
    lines = [
        "# Practical Release Quality Report",
        "",
        f"- Status: `{result.status}`",
        f"- Test cases: `{result.test_case_count}`",
        f"- Combined file: `{result.combined_file}`",
        f"- Coverage matrix: `{result.coverage_matrix}`",
        "",
        "## Status counts",
        "",
        "| status | count |",
        "| --- | ---: |",
    ]
    for status, count in result.status_counts.items():
        lines.append(f"| `{status}` | {count} |")
    lines.extend(
        [
            "",
            "## Finding counts",
            "",
            "| severity | count |",
            "| --- | ---: |",
        ]
    )
    for severity, count in result.finding_counts.items():
        lines.append(f"| `{severity}` | {count} |")
    lines.extend(
        [
            "",
            "## Findings",
            "",
            "| severity | id | file | TC | details |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    if findings:
        for finding in findings:
            lines.append(
                f"| `{finding.severity}` | `{finding.finding_id}` | `{finding.source_file}` | "
                f"`{finding.test_case_id}` | {_markdown_table_escape(finding.details)} |"
            )
    else:
        lines.append("| `info` | `release-quality-pass` | `-` | `-` | No blocking release smells found. |")
    return "\n".join(lines) + "\n"


def build_practical_release(
    ft_root: Path,
    *,
    output_dir: Path | None = None,
    release_name: str = "all-test-cases",
    source_files: Sequence[Path] | None = None,
) -> tuple[ReleaseBuildResult, list[ReleaseFinding]]:
    ft_root = ft_root.resolve()
    output_dir = (output_dir or (ft_root / "work" / "exports")).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    files = (
        [path if path.is_absolute() else ft_root / path for path in source_files]
        if source_files is not None
        else discover_test_case_files(ft_root)
    )
    missing_files = [str(path) for path in files if not path.is_file()]
    if missing_files:
        raise PracticalReleaseError("Missing release source files: " + ", ".join(missing_files))
    records, findings = parse_test_cases(ft_root, files)

    combined_path = output_dir / f"{release_name}.md"
    matrix_path = output_dir / f"{release_name}.coverage-matrix.md"
    quality_md_path = output_dir / f"{release_name}.quality-report.md"
    quality_json_path = output_dir / f"{release_name}.quality-report.json"

    finding_counts = _finding_counts(findings)
    status = "failed" if finding_counts.get("error", 0) else "passed-with-warnings" if finding_counts.get("warning", 0) else "passed"
    result = ReleaseBuildResult(
        ft_root=str(ft_root),
        output_dir=str(output_dir),
        combined_file=str(combined_path),
        coverage_matrix=str(matrix_path),
        quality_report_md=str(quality_md_path),
        quality_report_json=str(quality_json_path),
        test_case_count=len(records),
        source_files=tuple(path.relative_to(ft_root).as_posix() for path in files),
        status_counts=_status_counts(records),
        finding_counts=finding_counts,
        status=status,
    )

    combined_path.write_text(render_combined(records), encoding="utf-8", newline="\n")
    matrix_path.write_text(render_coverage_matrix(records), encoding="utf-8", newline="\n")
    quality_md_path.write_text(render_quality_report(result, findings), encoding="utf-8", newline="\n")
    quality_json_path.write_text(
        json.dumps(
            {
                "result": asdict(result),
                "findings": [asdict(finding) for finding in findings],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return result, findings
