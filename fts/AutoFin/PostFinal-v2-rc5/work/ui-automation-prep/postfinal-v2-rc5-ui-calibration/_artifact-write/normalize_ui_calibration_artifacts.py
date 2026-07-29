from __future__ import annotations

from pathlib import Path


BASE = Path(__file__).resolve().parents[1]
REPORT = BASE / "ui-validation-report.md"
INDEX = BASE / "ui-evidence-index.md"


BLOCKED_STATUS = {
    "TC-PASSCUR-003": "blocked-observability",
    "TC-PASSCUR-005": "blocked-observability",
    "TC-PASSCUR-018": "blocked-observability",
    "TC-DOC-019": "not-automatable-manual-only",
    "TC-DOC-020": "not-automatable-manual-only",
    "TC-DOC-025": "not-automatable-manual-only",
    "TC-DOC-026": "not-automatable-manual-only",
    "TC-DOC-031": "not-automatable-manual-only",
    "TC-DOC-040": "blocked-observability",
}


def split_table_row(line: str) -> list[str]:
    return [part.strip() for part in line.strip().strip("|").split("|")]


def artifact_type_for(path: str) -> str:
    lower = path.lower()
    if lower.endswith(".png"):
        return "screenshot"
    if lower.endswith(".zip"):
        return "trace"
    if lower.endswith(".md"):
        return "log"
    return "log"


def normalize_report() -> None:
    lines = REPORT.read_text(encoding="utf-8-sig").splitlines()
    out: list[str] = []
    table_context: str | None = None

    for line in lines:
        if line.startswith("| TC-ID | Фактическое поведение UI |"):
            table_context = "mismatch"
            out.append("| TC-ID | UI Verification Status | Фактическое поведение UI | Требуемая корректировка |")
            continue
        if line.startswith("| TC-ID | Причина блокировки |"):
            table_context = "blocked"
            out.append("| TC-ID | UI Verification Status | Причина блокировки |")
            continue
        if table_context == "mismatch" and line.startswith("| --- | --- | --- |"):
            out.append("| --- | --- | --- | --- |")
            continue
        if table_context == "blocked" and line.startswith("| --- | --- |"):
            out.append("| --- | --- | --- |")
            continue
        if table_context in {"mismatch", "blocked"} and line.startswith("| `TC-"):
            cells = split_table_row(line)
            tc_id = cells[0].strip("`")
            if table_context == "mismatch" and len(cells) >= 3:
                out.append(f"| {cells[0]} | `mismatch-ft-ui` | {cells[1]} | {cells[2]} |")
                continue
            if table_context == "blocked" and len(cells) >= 2:
                status = BLOCKED_STATUS.get(tc_id, "blocked-observability")
                out.append(f"| {cells[0]} | `{status}` | {cells[1]} |")
                continue
        if not line.startswith("|") and line.strip():
            table_context = None
        out.append(line)

    REPORT.write_text("\n".join(out) + "\n", encoding="utf-8")


def normalize_index() -> None:
    lines = INDEX.read_text(encoding="utf-8-sig").splitlines()
    canonical_rows: list[tuple[str, str, str, str]] = []
    rewritten: list[str] = []
    artifact_table_inserted = False

    for line in lines:
        if line.startswith("- Screenshots:") and not artifact_table_inserted:
            rewritten.append(line)
            rewritten.append("")
            rewritten.append("## Canonical Evidence Artifact Table")
            rewritten.append("")
            rewritten.append("| test_case_id | artifact_type | path | note |")
            rewritten.append("| --- | --- | --- | --- |")
            artifact_table_inserted = True
            continue

        if line.startswith("| TC-ID | Что проверялось |"):
            rewritten.append(line.replace("| TC-ID |", "| Case |", 1))
            continue

        if line.startswith("| `TC-"):
            cells = split_table_row(line)
            if len(cells) >= 7:
                tc_id = cells[0].strip("`")
                check_summary = cells[1].replace("|", "/")
                status = cells[5].strip("`")
                path = cells[6].strip("`")
                note = f"{status}; {check_summary}".replace("|", "/")
                canonical_rows.append((tc_id, artifact_type_for(path), path, note))
                cells[0] = f"Case {cells[0]}"
                rewritten.append("| " + " | ".join(cells) + " |")
                continue

        rewritten.append(line)

    if artifact_table_inserted:
        insertion_index = rewritten.index("| --- | --- | --- | --- |") + 1
        artifact_lines = [
            f"| {tc_id} | {artifact_type} | {path} | {note} |"
            for tc_id, artifact_type, path, note in canonical_rows
        ]
        rewritten[insertion_index:insertion_index] = artifact_lines

    INDEX.write_text("\n".join(rewritten) + "\n", encoding="utf-8")


def main() -> None:
    normalize_report()
    normalize_index()


if __name__ == "__main__":
    main()
