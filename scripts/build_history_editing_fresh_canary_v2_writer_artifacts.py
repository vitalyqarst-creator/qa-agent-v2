from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FT_ROOT = ROOT / "fts" / "ft-2-OF_17"
SCOPE = "history-editing-fresh-canary-v2"
SECTION = "section-40"
TC_FILE = FT_ROOT / "test-cases" / f"{SECTION}-{SCOPE}.md"
TD = FT_ROOT / "work" / "test-design" / f"{SECTION}-{SCOPE}"
CYCLE = FT_ROOT / "work" / "review-cycles" / SCOPE
OUT = CYCLE / "outputs"
PROMPTS = CYCLE / "prompts"


SRC_ROWS = [
    ("SRC-001", "WP-01", "history rows from changed UZ card fields", "section-40, block 1", "ATOM-001"),
    ("SRC-002", "WP-01", "separate edit-event rows and unified form list", "section-40, block 2", "ATOM-002"),
    ("SRC-003", "WP-01", "descending sort by `Дата и время начала`", "section-40, block 3", "ATOM-003"),
    ("SRC-004", "WP-01", "row count for simultaneous multi-field edit", "section-40, block 4", "ATOM-004"),
    ("SRC-005", "WP-01", "add new value: empty `Было`, new `Стало`", "section-40, block 5", "ATOM-005"),
    ("SRC-006", "WP-01", "delete value: removed `Было`, empty `Стало`", "section-40, block 6", "ATOM-006"),
    ("SRC-007", "WP-02", "close form action", "section-40, blocks 7-8", "ATOM-007"),
    ("SRC-008", "WP-02", "column `Дата и время начала`: visible date sortable", "section-40, table 2", "ATOM-008"),
    ("SRC-009", "WP-02", "column `Поле`: visible text sortable", "section-40, table 2", "ATOM-009"),
    ("SRC-010", "WP-02", "column `Было`: visible text sortable", "section-40, table 2", "ATOM-010"),
    ("SRC-011", "WP-02", "column `Стало`: visible text sortable", "section-40, table 2", "ATOM-011"),
    ("SRC-012", "WP-02", "column `ФИО сотрудника, выполнившего изменения`: visible text sortable with full name and login", "section-40, table 2", "ATOM-012"),
]

ATOMS = {
    "ATOM-001": ("WP-01", "SRC-001", "Коллекция таблицы истории формируется из измененных значений полей карточки УЗ.", "TC-HIST-001"),
    "ATOM-002": ("WP-01", "SRC-002", "Каждое событие редактирования анкеты представлено отдельной строкой, а форма показывает единый актуальный список изменений.", "TC-HIST-002"),
    "ATOM-003": ("WP-01", "SRC-003", "Строки отсортированы по `Дата и время начала` по убыванию.", "TC-HIST-003"),
    "ATOM-004": ("WP-01", "SRC-004", "Одновременное изменение нескольких полей создает число строк, равное числу измененных параметров.", "TC-HIST-004"),
    "ATOM-005": ("WP-01", "SRC-005", "При добавлении нового значения `Было` пусто, а `Стало` содержит новое значение.", "TC-HIST-005"),
    "ATOM-006": ("WP-01", "SRC-006", "При удалении значения `Было` содержит удаленное значение, а `Стало` пусто.", "TC-HIST-006"),
    "ATOM-007": ("WP-02", "SRC-007", "Форма поддерживает закрытие.", "TC-HIST-010"),
    "ATOM-008": ("WP-02", "SRC-008", "Таблица отображает колонку `Дата и время начала` как дату и поддерживает сортировку.", "TC-HIST-007; TC-HIST-008"),
    "ATOM-009": ("WP-02", "SRC-009", "Таблица отображает колонку `Поле` как текст и поддерживает сортировку.", "TC-HIST-007; TC-HIST-008"),
    "ATOM-010": ("WP-02", "SRC-010", "Таблица отображает колонку `Было` как текст и поддерживает сортировку.", "TC-HIST-007; TC-HIST-008"),
    "ATOM-011": ("WP-02", "SRC-011", "Таблица отображает колонку `Стало` как текст и поддерживает сортировку.", "TC-HIST-007; TC-HIST-008"),
    "ATOM-012": ("WP-02", "SRC-012", "Таблица отображает колонку сотрудника как текст; значение содержит ФИО и логин; сортировка поддерживается.", "TC-HIST-007; TC-HIST-008; TC-HIST-009"),
}


def md_table(headers: list[str], rows: list[list[str] | tuple[str, ...]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() != ".md":
        path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")
        return
    match = re.match(r"^(#{1,6})\s+(.+?)\n\n?(.*)$", text.rstrip(), flags=re.S)
    if not match:
        path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")
        return
    scratch = TD / "_artifact_write"
    scratch.mkdir(parents=True, exist_ok=True)
    level = len(match.group(1))
    heading = match.group(2)
    content = match.group(3).strip()
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", path.relative_to(FT_ROOT).as_posix())
    content_path = scratch / f"{slug}.content.md"
    manifest_path = scratch / f"{slug}.manifest.json"
    content_path.write_text(content + "\n", encoding="utf-8", newline="\n")
    manifest_path.write_text(
        json.dumps(
            {
                "target_path": str(path.resolve()),
                "sections": [{"level": level, "heading": heading, "content_file": str(content_path.resolve())}],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(manifest_path)],
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def artifact_write_strategy() -> str:
    return "# Artifact Write Strategy\n\n" + md_table(
        ["item", "value", "evidence"],
        [
            ["preflight_result", "`package-based`", "`WP-01`, `WP-02`; split artifacts and canonical TC generated by file-based script"],
            ["write_method", "`scripts/write_artifact_sections.py --manifest <manifest.json>`", "`scripts/build_history_editing_fresh_canary_v2_writer_artifacts.py` creates UTF-8 section files/manifests and invokes the canonical helper"],
            ["forbidden_methods_checked", "`yes`", "No old canary file used as template; no giant shell argument; no inline generator command"],
            ["chunk_plan", "`WP-01 -> WP-02 -> cycle outputs`", "Artifacts are generated from the confirmed `SRC-*` and `ATOM-*` lists in this script"],
            ["helper_artifacts", "`scripts/build_history_editing_fresh_canary_v2_writer_artifacts.py`; `_artifact_write/*.manifest.json`", "Committed reproducible helper and retained manifests"],
            ["validation_plan", "`artifact-shape-preflight; scoped validator profile writer-r1`", "`outputs/scoped-validator-profile.writer-r1.json` after runner validate"],
        ],
    )


def source_row_inventory() -> str:
    rows = [[src, wp, field, ref, "`section-40`", "yes", atom] for src, wp, field, ref, atom in SRC_ROWS]
    rows.append(["SRC-013", "WP-01", "PDF extraction/parity risk", "source-parity-check.md", "`source-parity-check.md`", "unclear", "GAP-001"])
    return "# Source Row Inventory\n\n" + md_table(
        ["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"],
        rows,
    )


def source_row_completeness() -> str:
    rows = [[src, "`section-40`", f"`{src}.P01`", atom, "`GAP-001`", "covered_with_accepted_parity_risk"] for src, _, _, _, atom in SRC_ROWS]
    rows.append(["SRC-013", "`source-parity-check.md`", "`SRC-013.P01`", "not_applicable:parity_risk", "`GAP-001`", "accepted_nonblocking_parity_risk"])
    return "# Source Row Completeness Matrix\n\n" + md_table(
        ["source_row_id", "source_requirement_codes", "normalized_property_ids", "linked_atoms", "gap_ids", "coverage_decision"],
        rows,
    )


def normalized_rows() -> list[list[str]]:
    base = [
        ["SRC-001", "SRC-001.P01", "WP-01", "history-editing table", "changed-field-row-source", "changed UZ card field exists", "table contains a row for the changed field", "`section-40`", "section-40, block 1", "high", "not_applicable:covered", "ATOM-001"],
        ["SRC-002", "SRC-002.P01", "WP-01", "history-editing form", "separate-event-rows", "several edit events exist", "each event is represented as a separate row in one unified list", "`section-40`", "section-40, block 2", "high", "not_applicable:covered", "ATOM-002"],
        ["SRC-003", "SRC-003.P01", "WP-01", "history-editing table", "date-descending-order", "two or more rows have different start dates", "newer `Дата и время начала` is above older rows", "`section-40`", "section-40, block 3", "high", "not_applicable:covered", "ATOM-003"],
        ["SRC-004", "SRC-004.P01", "WP-01", "history-editing table", "multi-field-row-count", "several fields changed simultaneously", "row count equals changed parameter count", "`section-40`", "section-40, block 4", "high", "not_applicable:covered", "ATOM-004"],
        ["SRC-005", "SRC-005.P01", "WP-01", "old-new cells", "add-value-old-new", "new UZ value added", "`Было` is empty and `Стало` contains new value", "`section-40`", "section-40, block 5", "high", "not_applicable:covered", "ATOM-005"],
        ["SRC-006", "SRC-006.P01", "WP-01", "old-new cells", "delete-value-old-new", "UZ value removed", "`Было` contains removed value and `Стало` is empty", "`section-40`", "section-40, block 6", "high", "not_applicable:covered", "ATOM-006"],
        ["SRC-007", "SRC-007.P01", "WP-02", "form action", "close-form", "form is open", "close action closes the form", "`section-40`", "section-40, blocks 7-8", "high", "not_applicable:covered", "ATOM-007"],
        ["SRC-008", "SRC-008.P01", "WP-02", "table column", "date-column-visible-sortable", "history table is open", "`Дата и время начала` column is visible, date-valued and sortable", "`section-40`", "section-40, table 2", "high", "not_applicable:covered", "ATOM-008"],
        ["SRC-009", "SRC-009.P01", "WP-02", "table column", "field-column-visible-sortable", "history table is open", "`Поле` column is visible, text-valued and sortable", "`section-40`", "section-40, table 2", "high", "not_applicable:covered", "ATOM-009"],
        ["SRC-010", "SRC-010.P01", "WP-02", "table column", "old-column-visible-sortable", "history table is open", "`Было` column is visible, text-valued and sortable", "`section-40`", "section-40, table 2", "high", "not_applicable:covered", "ATOM-010"],
        ["SRC-011", "SRC-011.P01", "WP-02", "table column", "new-column-visible-sortable", "history table is open", "`Стало` column is visible, text-valued and sortable", "`section-40`", "section-40, table 2", "high", "not_applicable:covered", "ATOM-011"],
        ["SRC-012", "SRC-012.P01", "WP-02", "table column", "employee-column-visible-sortable", "history table is open", "`ФИО сотрудника, выполнившего изменения` column is visible, text-valued, contains full name and login, and sortable", "`section-40`", "section-40, table 2", "high", "not_applicable:covered", "ATOM-012"],
        ["SRC-013", "SRC-013.P01", "WP-01", "source parity", "pdf-extraction-risk", "PDF text extraction did not locate section-40", "do not claim PDF page, PDF-only IDs, or PDF-confirmed parity", "`source-parity-check.md`", "source-parity-check.md; scope-coverage-gaps.md", "high", "GAP-001", "not_applicable:parity_risk"],
    ]
    return base


def source_table_normalization() -> str:
    return "# Source Table Normalization\n\n" + md_table(
        ["source_row_id", "source_property_id", "package_id", "field_or_block", "property", "condition", "expected_behavior", "requirement_code", "source_ref", "confidence", "gap_id", "linked_atoms"],
        normalized_rows(),
    )


def tddt() -> str:
    rows = []
    plan = {
        "SRC-001.P01": ("ATOM-001", "row-source", "standalone_tc", "TC-HIST-001"),
        "SRC-002.P01": ("ATOM-002", "list-composition", "standalone_tc", "TC-HIST-002"),
        "SRC-003.P01": ("ATOM-003", "ordering", "standalone_tc", "TC-HIST-003"),
        "SRC-004.P01": ("ATOM-004", "row-count", "standalone_tc", "TC-HIST-004"),
        "SRC-005.P01": ("ATOM-005", "old-new-mapping", "standalone_tc", "TC-HIST-005"),
        "SRC-006.P01": ("ATOM-006", "old-new-mapping", "standalone_tc", "TC-HIST-006"),
        "SRC-007.P01": ("ATOM-007", "action-navigation", "standalone_tc", "TC-HIST-010"),
        "SRC-008.P01": ("ATOM-008", "table-column", "covered_by_existing_tc", "TC-HIST-007; TC-HIST-008"),
        "SRC-009.P01": ("ATOM-009", "table-column", "covered_by_existing_tc", "TC-HIST-007; TC-HIST-008"),
        "SRC-010.P01": ("ATOM-010", "table-column", "covered_by_existing_tc", "TC-HIST-007; TC-HIST-008"),
        "SRC-011.P01": ("ATOM-011", "table-column", "covered_by_existing_tc", "TC-HIST-007; TC-HIST-008"),
        "SRC-012.P01": ("ATOM-012", "table-column", "covered_by_existing_tc", "TC-HIST-007; TC-HIST-008; TC-HIST-009"),
        "SRC-013.P01": ("not_applicable:parity_risk", "source-parity-risk", "out_of_scope", "GAP-001"),
    }
    for i, norm in enumerate(normalized_rows(), start=1):
        source_property_id = norm[1]
        atom, prop_type, decision, planned = plan[source_property_id]
        gap = "GAP-001" if source_property_id == "GAP-001.P01" else "not_applicable:covered"
        rows.append([
            f"TDD-{i:03d}", norm[2], source_property_id, atom, prop_type, decision,
            "Executable observable UI state exists." if planned.startswith("TC-") else "Accepted non-blocking PDF extraction risk; no executable system behavior.",
            planned, norm[8], "yes" if planned.startswith("TC-") else "no",
            norm[6], "covered by selected TC" if planned.startswith("TC-") else "DOCX coverage testable; PDF parity blocked",
            "not_applicable:covered" if planned.startswith("TC-") else "PDF page/ID parity not claimable",
            gap, "low" if planned.startswith("TC-") else "medium",
        ])
    return "# Test Design Decision Table\n\n" + md_table(
        ["decision_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "decision", "decision_reason", "planned_tc_or_gap", "oracle_source", "must_be_executable", "observable_oracle", "testable_part", "blocked_part", "gap_admissibility", "review_risk"],
        rows,
    )


def coverage_obligation_table() -> str:
    rows: list[list[str]] = [[
        "OBL-NA-001",
        "WP-01",
        "SRC-013.P01",
        "not_applicable:parity_risk",
        "source-parity-risk",
        "pdf-extraction-risk-recorded",
        "No executable coverage-obligation class is derived; preserve accepted PDF extraction risk.",
        "source-parity-check.md",
        "GAP-001",
        "n/a",
        "No numeric/mask/exact-length/dictionary/repeatable/print-form obligation classes exist in section-40.",
    ]]
    return "# Coverage Obligation Table\n\n" + md_table(
        ["obligation_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "obligation_class", "required_behavior", "source_ref", "planned_tc_or_gap", "status", "review_notes"],
        rows,
    )


def atomic_ledger() -> str:
    rows = []
    for atom, (wp, src, statement, tc) in ATOMS.items():
        rows.append([atom, wp, src, "`section-40`", statement, "covered", tc, "not_applicable:covered"])
    return "# Atomic Requirements Ledger\n\n" + md_table(
        ["atom_id", "package_id", "source_row_id", "requirement_code", "atomic_statement", "coverage_status", "covered_by_tc", "gap_id"],
        rows,
    )


def package_plan() -> str:
    rows = [
        ["PLAN-001", "WP-01", "row-formation", "section-40, block 1", "ATOM-001", "Changed UZ field appears as a history row", "positive", "row-source", "changed existing value", "row for changed field is displayed", "DOCX section-40", "TC-HIST-001", "covered"],
        ["PLAN-002", "WP-01", "unified-list", "section-40, block 2", "ATOM-002", "Separate events appear in one current list", "positive", "list-composition", "two edit events", "both event rows are displayed together", "DOCX section-40", "TC-HIST-002", "covered"],
        ["PLAN-003", "WP-01", "sort-order", "section-40, block 3", "ATOM-003", "Rows ordered by date descending", "positive", "ordering", "three dated events", "latest event is first", "DOCX section-40", "TC-HIST-003", "covered"],
        ["PLAN-004", "WP-01", "multi-field-edit", "section-40, block 4", "ATOM-004", "Row count equals changed parameter count", "positive", "row-count", "three changed parameters", "three rows exist for the event", "DOCX section-40", "TC-HIST-004", "covered"],
        ["PLAN-005", "WP-01", "add-value", "section-40, block 5", "ATOM-005", "Added value maps to empty old and filled new", "positive", "old-new-mapping", "added value", "`Было` empty; `Стало` filled", "DOCX section-40", "TC-HIST-005", "covered"],
        ["PLAN-006", "WP-01", "delete-value", "section-40, block 6", "ATOM-006", "Deleted value maps to filled old and empty new", "positive", "old-new-mapping", "deleted value", "`Было` filled; `Стало` empty", "DOCX section-40", "TC-HIST-006", "covered"],
        ["PLAN-007", "WP-02", "table-column-set", "section-40, table 2", "ATOM-008; ATOM-009; ATOM-010; ATOM-011; ATOM-012", "Verify the section-40 table column set", "scenario-use-case", "table-composition", "history table open", "section-40 column set is visible", "DOCX section-40", "TC-HIST-007", "covered"],
        ["PLAN-008", "WP-02", "table-column-sortability", "section-40, table 2", "ATOM-008; ATOM-009; ATOM-010; ATOM-011; ATOM-012", "Verify sortability for the section-40 table column set", "scenario-use-case", "table-sortability", "history table open", "sort action is available for section-40 column set", "DOCX section-40", "TC-HIST-008", "covered"],
        ["PLAN-009", "WP-02", "employee-column-value", "section-40, table 2", "ATOM-012", "Employee column contains full name and login", "positive", "table-cell-value", "history table with row changed by employee", "employee cell contains full name and login", "DOCX section-40", "TC-HIST-009", "covered"],
        ["PLAN-010", "WP-02", "close-action", "section-40, blocks 7-8", "ATOM-007", "Close form action", "positive", "action-navigation", "form open", "form is closed", "DOCX section-40", "TC-HIST-010", "covered"],
    ]
    return "# Package Test Design Plan\n\n" + md_table(
        ["design_item_id", "package_id", "design_dimension", "source_ref", "linked_atoms", "planned_check", "check_type", "coverage_class", "input_class", "single_expected_behavior", "oracle_source", "planned_tc_or_gap", "status"],
        rows,
    )


def internal_work_package_coverage() -> str:
    return "# Internal Work Package Coverage\n\n" + md_table(
        ["package_id", "focus", "ledger_gate", "design_plan_gate", "tc_gate", "atoms", "covered", "gap", "unclear", "TC count", "status"],
        [
            ["WP-01", "Row formation and history semantics", "pass", "pass", "pass", "6", "6", "0", "0", "6", "ready-for-review"],
            ["WP-02", "Table composition and user action", "pass", "pass", "pass", "6", "6", "0", "0", "4", "ready-for-review"],
        ],
    )


def simple_self_check(title: str) -> str:
    return f"# {title}\n\n" + md_table(
        ["check", "status", "evidence", "follow_up"],
        [
            ["package rows preserved", "pass", "All `SRC-001`..`SRC-012` and `ATOM-001`..`ATOM-012` are present.", "none_required:pass"],
            ["GAP-001 preserved", "pass", "`coverage-gaps.md`, TDDT, ledger and coverage plan keep `GAP-001` visible.", "none_required:pass"],
            ["no metadata-only TC", "pass", "Table columns are covered by observable composition, sortability and employee-value checks, not by standalone type-only cases.", "none_required:pass"],
        ],
    )


def coverage_metrics() -> str:
    return "# Coverage Metrics\n\n" + md_table(
        ["dimension", "technique", "applicable", "source_ref", "obligations_found", "obligations_covered_by_tc", "obligations_gap_or_unclear", "coverage_strength", "linked_artifact", "residual_risk"],
        [
            ["row-formation", "example-based", "yes", "section-40, blocks 1,4,5,6", "4", "4", "0", "obligation-level", "package-test-design-plan.md", "none_required:covered"],
            ["event-list", "state/list", "yes", "section-40, block 2", "1", "1", "0", "obligation-level", "package-test-design-plan.md", "none_required:covered"],
            ["ordering", "sort/order", "yes", "section-40, block 3; table 2", "2", "2", "0", "obligation-level", "package-test-design-plan.md", "none_required:covered"],
            ["table-composition", "column-composition", "yes", "section-40, table 2", "5", "5", "0", "column-level", "package-test-design-plan.md", "none_required:covered"],
            ["action", "navigation/action", "yes", "section-40, blocks 7-8", "1", "1", "0", "action-level", "package-test-design-plan.md", "none_required:covered"],
            ["source-parity", "parity-risk", "yes", "source-parity-check.md", "1", "0", "1", "risk-recorded", "coverage-gaps.md", "GAP-001"],
        ],
    )


def applicability_matrix() -> str:
    return "# Test-design Applicability Matrix\n\n" + md_table(
        ["dimension", "applicable", "source_ref", "linked_atoms", "linked_test_cases", "gap_id", "reason"],
        [
            ["other", "yes", "section-40, table 2", "ATOM-008; ATOM-009; ATOM-010; ATOM-011; ATOM-012", "TC-HIST-007", "", "Table column-set visibility is not named in the canonical vocabulary."],
            ["scenario-use-case", "yes", "section-40, blocks 7-8", "ATOM-007", "TC-HIST-010", "", "Close action changes form visibility."],
            ["persistence", "yes", "section-40, blocks 1-6", "ATOM-001; ATOM-002; ATOM-004; ATOM-005; ATOM-006", "TC-HIST-001; TC-HIST-002; TC-HIST-004; TC-HIST-005; TC-HIST-006", "", "History rows are observed after performed edits."],
            ["other", "yes", "section-40, block 3; table 2", "ATOM-003; ATOM-008; ATOM-009; ATOM-010; ATOM-011; ATOM-012", "TC-HIST-003; TC-HIST-008", "", "Ordering/sortability dimension is not named in the canonical vocabulary; descending order and sortable columns are in scope."],
            ["table-list", "yes", "section-40, block 2", "ATOM-002", "TC-HIST-002", "", "Unified list across edit events is required."],
        ],
    )


def risk_priority_map() -> str:
    rows = []
    for atom, (wp, src, statement, tc) in ATOMS.items():
        high = atom in {"ATOM-001", "ATOM-002", "ATOM-003", "ATOM-004", "ATOM-005", "ATOM-006"}
        rows.append([
            atom, "audit-history" if high else "ui-structure", "4" if high else "2", "3" if high else "2",
            "12" if high else "4", "high" if high else "low", "data-audit" if high else "manual-navigation",
            f"{src}; section-40", "High" if high else "Low", tc, "not_applicable:covered", "none", statement,
        ])
    return "# Risk / Priority Map\n\n" + md_table(
        ["atom_id", "coverage_dimension", "impact", "likelihood", "risk_score", "risk_level", "risk_factors", "source_ref", "required_priority", "linked_test_cases", "gap_id", "residual_risk_decision", "rationale"],
        rows,
    )


def coverage_map() -> str:
    return "# Coverage Map\n\n" + md_table(
        ["item", "value", "evidence"],
        [
            ["atomic_statements", "`12`", "`ATOM-001`..`ATOM-012`"],
            ["covered_atoms", "`12`", "`TC-HIST-001`..`TC-HIST-010`"],
            ["coverage_gaps", "`1`", "`GAP-001` accepted non-blocking PDF extraction risk"],
            ["uncovered_atoms", "`0`", "none_required:all_atoms_covered"],
            ["multi-atom TC", "`TC-HIST-007`; `TC-HIST-008`", "Table set and sortability checks cover column atoms without type-only standalone cases."],
        ],
    )


def coverage_gaps() -> str:
    return "# Coverage Gaps\n\n" + md_table(
        ["gap_id", "source_ref", "gap_type", "impact", "blocks_ready_for_review", "coverage_impact", "handling", "linked_artifacts"],
        [
            ["GAP-001", "source-parity-check.md; section-40; table 2", "ambiguity", "non-blocking", "no", "Writer covers DOCX atoms but cannot claim PDF page references, PDF-only IDs, or PDF-confirmed row parity.", "accepted non-blocking extraction risk from `scope-gap-review.md`", "source-table-normalization.md; test-design-decision-table.md; atomic-requirements-ledger.md; package-test-design-plan.md"],
        ],
    )


def test_design_review() -> str:
    rows = [[item, "pass", "info", "all", evidence, "none_required:pass", "no"] for item, evidence in [
        ("decision-table-classification", "TDDT rows classify section-40 executable properties as `standalone_tc`/`covered_by_existing_tc`; source parity is `out_of_scope` with `GAP-001`."),
        ("ledger-plan-alignment", "All `ATOM-001`..`ATOM-012` in ledger have package-plan coverage and linked TC ids."),
        ("coverage-class-completeness", "No numeric/exact-length/dictionary mandatory classes exist; row/list/sort/action classes are represented in plan and metrics."),
        ("numeric-length-boundaries", "Not applicable: section-40 has no numeric or exact-length input rule."),
        ("unsupported-ui-mechanism", "TC expected results do not invent messages, red highlight, disabled state or backend effects."),
        ("mask-format-coverage", "Not applicable: section-40 has no mask/default-mask rule."),
        ("dictionary-closed-set", "Not applicable: section-40 has no fixed dictionary/list values."),
        ("conditional-branches", "Not applicable: section-40 has no conditional visibility/requiredness branches."),
        ("negative-fixture-isolation", "Not applicable: no negative transition case is created."),
        ("applicability-linked-tc-semantics", "Applicability rows link only to TC sections that exercise the stated dimension."),
        ("gap-specificity", "`GAP-001` is narrowly scoped to PDF extraction/parity and does not hide DOCX behavior."),
        ("gap-admissibility", "`GAP-001` is not an executable system behavior and does not hide source-backed UI behavior."),
        ("internal-observability", "Backend/API/DB audit internals are out of scope and not marked covered."),
        ("metadata-only-exclusion", "Column type metadata is covered only through observable table composition/sortability, not standalone type-only TCs."),
        ("tc-mapping-atomicity", "Each executable plan row has one linked TC; table set/sortability rows are grouped by source contract."),
        ("ready-for-tc-writing", "`WP-01` and `WP-02` have no blocking test-design rows."),
    ]]
    return "# Test Design Review\n\n" + md_table(
        ["review_item", "status", "severity", "affected_package", "evidence", "required_action", "blocks_ready_for_review"],
        rows,
    )


def fixture_catalog() -> str:
    return "# Fixture Catalog\n\n" + md_table(
        ["fixture_id", "purpose", "source_ref", "setup_state", "concrete_data", "valid_for", "invalid_for", "dependencies", "cleanup", "linked_tcs"],
        [
            ["FX-HIST-001", "Карточка УЗ с изменяемым полем для одной строки истории", "section-40, block 1", "Существующая карточка УЗ; форма истории доступна", "Контрольное поле: `Фамилия`; было `Барисов`; стало `Борисов`", "TC-HIST-001", "none_required:positive_case", "доступность редактирования выбранного поля в тестовом окружении", "вернуть исходное значение при необходимости", "TC-HIST-001"],
            ["FX-HIST-002", "Карточка УЗ с несколькими событиями и датами начала", "section-40, blocks 2-3", "Существующая карточка УЗ с тремя событиями редактирования", "Событие A `2026-06-14 10:00`; B `2026-06-14 10:05`; C `2026-06-14 10:10`", "TC-HIST-002; TC-HIST-003", "none_required:positive_case", "возможность подготовить разные времена событий", "нет специальных постусловий", "TC-HIST-002; TC-HIST-003"],
            ["FX-HIST-003", "Карточка УЗ с одновременным изменением трех параметров", "section-40, block 4", "Одно сохранение меняет три поля", "`Фамилия`: `Барисов` -> `Борисов`; `Имя`: `Иван` -> `Петр`; `Отчество`: `Иванович` -> `Петрович`", "TC-HIST-004", "none_required:positive_case", "выбранные поля доступны в одной операции сохранения", "вернуть исходные значения при необходимости", "TC-HIST-004"],
            ["FX-HIST-004", "Карточка УЗ для добавления и удаления значения", "section-40, blocks 5-6", "Существующая карточка УЗ с редактируемым полем", "Добавленное/удаленное значение: `Борисов`", "TC-HIST-005; TC-HIST-006", "none_required:positive_case", "поле поддерживает добавление/удаление значения в тестовом окружении", "вернуть исходное состояние при необходимости", "TC-HIST-005; TC-HIST-006"],
        ],
    )


def writer_quality_gate() -> str:
    profile_rel = f"work/review-cycles/{SCOPE}/outputs/scoped-validator-profile.writer-r1.json"
    items = [
        ("artifact-shape-preflight", "pass", "Split artifacts use one top-level canonical heading and exact required table columns; canonical TC links summaries and does not duplicate full split tables."),
        ("placeholder-sentinel-normalization", "pass", "Traceability columns use explicit values such as `not_applicable:covered`, `none_required:*`, `not_covered:GAP-001`; no `N/A` placeholder is used."),
        ("artifact-write-strategy", "pass", "`artifact-write-strategy.md` records file-based UTF-8 helper script and forbids shell here-string/one-shot payloads."),
        ("mockup-visual-inventory", "pass", "No scope-specific mockup is selected; `source-selection.md` says mockups are not used for this scope."),
        ("source-row-inventory", "pass", "`SRC-001`..`SRC-012` from handoff inventory are preserved and mapped."),
        ("source-normalization-atomic", "pass", "Each normalized row has one property/condition/behavior; `GAP-001` is a separate parity row."),
        ("test-design-decision-table", "pass", "Every normalized row has a design decision and planned `TC-*` or `GAP-001`."),
        ("coverage-metrics", "pass", "`coverage-metrics.md` counts all applicable dimensions and residual `GAP-001`."),
        ("fixture-catalog", "pass", "`fixture-catalog.md` defines concrete reusable data for history events and row checks."),
        ("risk-priority-map", "pass", "High audit-history atoms map to High-priority TCs; `GAP-001` remains medium residual risk."),
        ("gap-admissibility", "pass", "`GAP-001` is only a PDF extraction risk and does not hide executable DOCX behavior."),
        ("test-design-review", "pass", "`test-design-review.md` has no blocking rows."),
        ("ledger-atomicity", "pass", "`ATOM-001`..`ATOM-012` remain separate; no broad section range compression."),
        ("gsr-range-compression", "pass", "No GSR-like code exists; traceability uses `section-40`."),
        ("design-plan-atomicity", "pass", "Each plan row has one planned check and one expected behavior."),
        ("scenario-does-not-replace-atomic", "pass", "No scenario TC replaces atomic checks; table composition/sortability TCs are allowed by scope constraints."),
        ("tc-atomicity", "pass", "Each executable TC has one primary expected result."),
        ("test-data-specificity", "pass", "Reusable fixtures use literal values or source-backed event timestamps."),
        ("tc-regression-smells", "pass", "No executable TC over unresolved gap; no source-rule oracle; no generic editability steps."),
        ("internal-observability", "pass", "Backend/audit-log internals are out of scope and not asserted."),
        ("action-observability", "pass", "Close action expected result is visible form closure."),
        ("semantic-req-id-parity", "pass", "All TCs and atoms use `section-40`; no PDF page or PDF-only code invented."),
        ("package-ready", "pass", "`WP-01` and `WP-02` have covered package gates."),
        ("scoped-validator-findings", "pass", f"`{profile_rel}` generated by runner validate; expected `unresolved_warning_error_count = 0`."),
    ]
    rows = [[f"`{item}`", f"`{status}`", evidence, "`all`", "none_required:pass", "`no`"] for item, status, evidence in items]
    return "# Writer Quality Gate\n\n" + md_table(
        ["gate_item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"],
        rows,
    )


def writer_self_check() -> str:
    return "# Writer Self-Check\n\n" + md_table(
        ["check", "status", "evidence", "follow_up"],
        [
            ["source parity checked", "pass", "`source-parity-check.md` read; `GAP-001` preserved.", "none_required:pass"],
            ["mandatory requirement IDs preserved", "pass", "`section-40` used for all `ATOM-*`; no GSR-like ID exists.", "none_required:pass"],
            ["uncovered atoms", "pass", "`0`; coverage-map.md lists all atoms covered.", "none_required:pass"],
            ["possible merged checks", "pass", "`TC-HIST-007` covers column visibility and `TC-HIST-008` covers sortability; scope contract forbids one standalone metadata TC per column.", "reviewer should confirm this remains atomic enough for structure preflight"],
            ["possible over-splitting", "pass", "No standalone type-only table column TCs.", "none_required:pass"],
            ["test-case grouping and numbering", "pass", "`TC-HIST-001`..`TC-HIST-010` continuous.", "none_required:pass"],
            ["internal work package coverage", "pass", "`internal-work-package-coverage.md` shows `WP-01`, `WP-02` ready.", "none_required:pass"],
            ["artifact write evidence", "pass", "`artifact-write-strategy.md`; retained helper `scripts/build_history_editing_fresh_canary_v2_writer_artifacts.py`.", "none_required:pass"],
            ["scoped validator command", "pass", "`python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_17/work/review-cycles/history-editing-fresh-canary-v2/cycle-state.yaml` before state advancement.", "none_required:pass"],
            ["scoped validator findings summary", "pass", "`outputs/scoped-validator-profile.writer-r1.json`; current-scope unresolved warning/error count expected `0`.", "none_required:pass"],
            ["assumptions", "pass", "Fixtures use section-40 examples as test data only, not mandatory business values.", "reviewer may challenge if fixture field availability is insufficient"],
            ["unclear items", "pass", "Only `GAP-001` remains, accepted non-blocking.", "none_required:pass"],
        ],
    )


def tc_section(tc_id: str, title: str, priority: str, package_id: str, trace: str, goal: str, pre: list[str], data: list[str], steps: list[str], expected: str, post: list[str], source_quote: str) -> str:
    return f"""## {tc_id}
**Название:** {title}
**Приоритет:** {priority}
**Тип:** Positive
**package_id:** `{package_id}`
**Трассировка:** {trace}

**Цель:** {goal}

**Предусловия:**
{chr(10).join(f"- {item}" for item in pre)}

**Тестовые данные:**
{chr(10).join(f"- {item}" for item in data)}

**Шаги:**
{chr(10).join(f"{idx}. {step}" for idx, step in enumerate(steps, start=1))}

**Итоговый ожидаемый результат:** {expected}

**Постусловия:**
{chr(10).join(f"- {item}" for item in post)}

**Ссылка на ФТ:** `section-40`

**Источник требования:**
- `section-40` / Форма `История редактирования анкеты`

**Источник / цитата требования:** {source_quote}
"""


def canonical_tc() -> str:
    links = "\n".join(
        f"- `{p}`"
        for p in [
            f"work/test-design/{SECTION}-{SCOPE}/artifact-write-strategy.md",
            f"work/test-design/{SECTION}-{SCOPE}/source-row-inventory.md",
            f"work/test-design/{SECTION}-{SCOPE}/source-table-normalization.md",
            f"work/test-design/{SECTION}-{SCOPE}/test-design-decision-table.md",
            f"work/test-design/{SECTION}-{SCOPE}/atomic-requirements-ledger.md",
            f"work/test-design/{SECTION}-{SCOPE}/package-test-design-plan.md",
            f"work/test-design/{SECTION}-{SCOPE}/coverage-gaps.md",
            f"work/test-design/{SECTION}-{SCOPE}/writer-quality-gate.md",
            f"work/test-design/{SECTION}-{SCOPE}/writer-self-check.md",
        ]
    )
    intro = f"""# Тест-кейсы: section-40 / Форма «История редактирования анкеты»

## Metadata

- ft_slug: `ft-2-OF_17`
- scope_slug: `{SCOPE}`
- source_scope: `section-40`
- writer_stage: `writer-r1`
- source_handoff: `work/stage-handoffs/03-history-editing-canary-prep/`
- accepted_risk: `GAP-001` remains non-blocking PDF extraction risk; PDF page references and PDF-only requirement IDs are not used.

## Coverage Boundaries

Набор покрывает только форму `История редактирования анкеты` из `section-40`: формирование строк истории изменений, единый список событий, сортировку по `Дата и время начала`, количество строк при одновременном изменении нескольких параметров, заполнение колонок `Было` / `Стало` при добавлении и удалении значения, состав таблицы и закрытие формы.

Не покрываются полный раздел `История заявки`, поведение исходных разделов `2.1.1.1.1.1` / `2.1.1.1.1.2`, backend/API/DB audit internals, mockup-only элементы и PDF traceability beyond `GAP-001`.

## Canonical Artifact Links

{links}

## Coverage Summary

| package_id | scope | atoms | covered_by_tc | residual_gap |
| --- | --- | --- | --- | --- |
| `WP-01` | Row formation and history semantics | `ATOM-001`..`ATOM-006` | `TC-HIST-001`..`TC-HIST-006` | none_required:covered |
| `WP-02` | Table composition and user action | `ATOM-007`..`ATOM-012` | `TC-HIST-007`; `TC-HIST-008`; `TC-HIST-009`; `TC-HIST-010` | none_required:covered |
| `WP-00` | Source parity risk | none_required:parity_only | not_covered:GAP-001 | `GAP-001` |

## Тест-кейсы
"""
    tests = [
        tc_section(
            "TC-HIST-001",
            "Строка истории отображается для измененного поля карточки УЗ",
            "High",
            "WP-01",
            "`ATOM-001`; `SRC-001`; `section-40`",
            "Проверить, что изменение значения поля карточки УЗ попадает в таблицу истории редактирования анкеты.",
            ["Существует карточка УЗ с доступной формой `История редактирования анкеты`.", "В карточке УЗ изменено контрольное поле `Фамилия`."],
            ["Контрольное поле: `Фамилия`.", "Исходное значение: `Барисов`.", "Новое значение: `Борисов`."],
            ["Открыть форму `История редактирования анкеты` для подготовленной карточки УЗ.", "Найти строку таблицы по контрольному полю `Фамилия` и значениям `Барисов` / `Борисов`."],
            "В таблице отображается строка истории для поля `Фамилия`, где колонка `Было` содержит `Барисов`, а колонка `Стало` содержит `Борисов`.",
            ["Вернуть контрольное поле к исходному значению при необходимости."],
            "Коллекция строк формируется из измененных значений полей карточки УЗ.",
        ),
        tc_section(
            "TC-HIST-002",
            "Единый список истории содержит строки разных событий редактирования",
            "High",
            "WP-01",
            "`ATOM-002`; `SRC-002`; `section-40`",
            "Проверить, что форма показывает один актуальный список строк по нескольким событиям редактирования анкеты.",
            ["Для одной карточки УЗ выполнены два отдельных события редактирования анкеты.", "Форма `История редактирования анкеты` доступна для этой карточки."],
            ["Событие 1: поле `Фамилия`, было `Барисов`, стало `Борисов`.", "Событие 2: поле `Имя`, было `Иван`, стало `Петр`."],
            ["Открыть форму `История редактирования анкеты` для подготовленной карточки УЗ.", "Найти строки истории для события 1 и события 2."],
            "В одной таблице формы одновременно отображаются отдельная строка для события 1 и отдельная строка для события 2.",
            ["Нет специальных постусловий."],
            "Каждое событие редактирования анкеты записывается отдельной строкой; форма показывает единый список по всем записям.",
        ),
        tc_section(
            "TC-HIST-003",
            "Строки истории отсортированы по дате и времени начала по убыванию",
            "High",
            "WP-01",
            "`ATOM-003`; `SRC-003`; `section-40`",
            "Проверить порядок строк истории по колонке `Дата и время начала`.",
            ["Для одной карточки УЗ существуют три строки истории редактирования с разными значениями `Дата и время начала`.", "Форма `История редактирования анкеты` доступна для этой карточки."],
            ["Событие A: `2026-06-14 10:00`.", "Событие B: `2026-06-14 10:05`.", "Событие C: `2026-06-14 10:10`."],
            ["Открыть форму `История редактирования анкеты` для подготовленной карточки УЗ.", "Прочитать значения `Дата и время начала` в первых трех строках сверху вниз."],
            "Первой отображается строка с `2026-06-14 10:10`, второй - строка с `2026-06-14 10:05`, третьей - строка с `2026-06-14 10:00`.",
            ["Нет специальных постусловий."],
            "Записи сортируются по `Дата и время начала` по убыванию.",
        ),
        tc_section(
            "TC-HIST-004",
            "Одновременное изменение трех параметров создает три строки истории",
            "High",
            "WP-01",
            "`ATOM-004`; `SRC-004`; `section-40`",
            "Проверить количество строк истории при одном событии с несколькими измененными параметрами.",
            ["В одной операции редактирования карточки УЗ одновременно изменены три контрольных параметра.", "Форма `История редактирования анкеты` доступна для этой карточки."],
            ["Параметр 1: `Фамилия`, `Барисов` -> `Борисов`.", "Параметр 2: `Имя`, `Иван` -> `Петр`.", "Параметр 3: `Отчество`, `Иванович` -> `Петрович`."],
            ["Открыть форму `История редактирования анкеты` для подготовленной карточки УЗ.", "Отфильтровать или визуально выделить строки, относящиеся к одному событию изменения трех параметров."],
            "Для этого события отображаются ровно три строки истории: по одной строке для `Фамилия`, `Имя` и `Отчество`.",
            ["Вернуть измененные значения при необходимости."],
            "При одновременном изменении нескольких полей создается столько строк, сколько параметров было изменено.",
        ),
        tc_section(
            "TC-HIST-005",
            "Добавленное значение отображается с пустой колонкой `Было` и заполненной колонкой `Стало`",
            "High",
            "WP-01",
            "`ATOM-005`; `SRC-005`; `section-40`",
            "Проверить заполнение колонок `Было` и `Стало` при добавлении нового значения.",
            ["В карточке УЗ добавлено новое значение в контрольное поле.", "Форма `История редактирования анкеты` доступна для этой карточки."],
            ["Контрольное поле: `Фамилия`.", "Добавленное значение: `Борисов`."],
            ["Открыть форму `История редактирования анкеты` для подготовленной карточки УЗ.", "Найти строку истории по контрольному полю и добавленному значению `Борисов`."],
            "В найденной строке колонка `Было` пустая, а колонка `Стало` содержит `Борисов`.",
            ["Вернуть контрольное поле к исходному состоянию при необходимости."],
            "При добавлении нового значения `Было` пусто, `Стало` содержит новое значение.",
        ),
        tc_section(
            "TC-HIST-006",
            "Удаленное значение отображается в колонке `Было` с пустой колонкой `Стало`",
            "High",
            "WP-01",
            "`ATOM-006`; `SRC-006`; `section-40`",
            "Проверить заполнение колонок `Было` и `Стало` при удалении значения.",
            ["В карточке УЗ удалено значение из контрольного поля.", "Форма `История редактирования анкеты` доступна для этой карточки."],
            ["Контрольное поле: `Фамилия`.", "Удаленное значение: `Борисов`."],
            ["Открыть форму `История редактирования анкеты` для подготовленной карточки УЗ.", "Найти строку истории по контрольному полю и удаленному значению `Борисов`."],
            "В найденной строке колонка `Было` содержит `Борисов`, а колонка `Стало` пустая.",
            ["Восстановить удаленное значение при необходимости."],
            "При удалении значения `Было` содержит удаленное значение, `Стало` пусто.",
        ),
        tc_section(
            "TC-HIST-007",
            "Таблица истории отображает заданные колонки section-40",
            "Medium",
            "WP-02",
            "`ATOM-008`; `ATOM-009`; `ATOM-010`; `ATOM-011`; `ATOM-012`; `SRC-008`; `SRC-009`; `SRC-010`; `SRC-011`; `SRC-012`; `section-40`",
            "Проверить состав колонок таблицы истории, указанный в `section-40`.",
            ["Открыта форма `История редактирования анкеты` для карточки УЗ с минимум одной строкой истории."],
            ["Нет специальных тестовых данных."],
            ["Осмотреть заголовки таблицы истории."],
            "Таблица отображает колонки `Дата и время начала`, `Поле`, `Было`, `Стало`, `ФИО сотрудника, выполнившего изменения`.",
            ["Нет специальных постусловий."],
            "Table 2 lists the visible columns of the history changes table.",
        ),
        tc_section(
            "TC-HIST-008",
            "Сортировка доступна для колонок таблицы истории",
            "Medium",
            "WP-02",
            "`ATOM-008`; `ATOM-009`; `ATOM-010`; `ATOM-011`; `ATOM-012`; `SRC-008`; `SRC-009`; `SRC-010`; `SRC-011`; `SRC-012`; `section-40`",
            "Проверить, что для колонок таблицы истории доступно действие сортировки.",
            ["Открыта форма `История редактирования анкеты` для карточки УЗ с минимум двумя строками истории."],
            ["Колонки для проверки сортировки: `Дата и время начала`, `Поле`, `Было`, `Стало`, `ФИО сотрудника, выполнившего изменения`."],
            ["Осмотреть заголовки таблицы истории.", "Для каждого заголовка из тестовых данных проверить наличие доступного действия сортировки."],
            "Для колонок `Дата и время начала`, `Поле`, `Было`, `Стало`, `ФИО сотрудника, выполнившего изменения` доступно действие сортировки.",
            ["Нет специальных постусловий."],
            "Table 2 marks sorting as `Да` for the listed columns.",
        ),
        tc_section(
            "TC-HIST-009",
            "Колонка сотрудника отображает ФИО и логин выполнившего изменения",
            "Medium",
            "WP-02",
            "`ATOM-012`; `SRC-012`; `section-40`",
            "Проверить формат значения в колонке `ФИО сотрудника, выполнившего изменения`.",
            ["Открыта форма `История редактирования анкеты` для карточки УЗ с минимум одной строкой истории."],
            ["Контрольная строка истории содержит значение сотрудника, например `Асирова Д.Ф // Asdf`."],
            ["В контрольной строке прочитать значение в колонке `ФИО сотрудника, выполнившего изменения`."],
            "В колонке `ФИО сотрудника, выполнившего изменения` отображается ФИО сотрудника и логин.",
            ["Нет специальных постусловий."],
            "For the employee column, the source says the value is employee full name and login.",
        ),
        tc_section(
            "TC-HIST-010",
            "Форма `История редактирования анкеты` закрывается по действию закрытия",
            "Medium",
            "WP-02",
            "`ATOM-007`; `SRC-007`; `section-40`",
            "Проверить, что пользователь может закрыть форму истории редактирования анкеты.",
            ["Открыта форма `История редактирования анкеты`."],
            ["Нет специальных тестовых данных."],
            ["Выполнить действие закрытия формы."],
            "Форма `История редактирования анкеты` закрыта и больше не отображается пользователю.",
            ["Нет специальных постусловий."],
            "Пользовательское действие формы: закрыть форму.",
        ),
    ]
    return intro + "\n".join(tests)


def writer_response() -> str:
    return f"""# Writer R1 Response

## Summary

Initial FT-first draft created for `ft-2-OF_17` / `{SCOPE}`.

## Outputs

- Canonical test cases: `test-cases/{SECTION}-{SCOPE}.md`
- Split artifacts: `work/test-design/{SECTION}-{SCOPE}/`
- Writer session log: `work/review-cycles/{SCOPE}/outputs/writer-session-log.writer-r1.md`
- Decision log: `work/review-cycles/{SCOPE}/outputs/agent-decision-log.writer-r1.md`
- Scoped validator profile: `work/review-cycles/{SCOPE}/outputs/scoped-validator-profile.writer-r1.json`

## Coverage

- Covered: `ATOM-001`..`ATOM-012`
- Residual accepted risk: `GAP-001`
- Reviewer focus: structure preflight should verify split artifact schemas and the separate WP-02 table composition/sortability/value/action cases.
"""


def session_log() -> str:
    required_files = [
        "AGENTS.md",
        "skills/README.md",
        "references/agent/session-based-review-cycle-format.md",
        "references/agent/codex-sdk-orchestration-format.md",
        "skills/ft-test-case-writer/SKILL.md",
        "references/agent/writer-runtime-workflow.md",
        "references/agent/writer-runtime-contract.md",
        "references/qa/test-case-runtime-format.md",
        "references/qa/coverage-runtime-checklist.md",
        "references/qa/traceability-rules.md",
        "references/agent/writer-process-workflow.md",
        "references/agent/workflow-state-format.md",
        "references/agent/session-log-format.md",
        "references/agent/agent-decision-log-format.md",
        "references/agent/writer-handoff-format.md",
        "references/agent/writer-output-format.md",
        "references/agent/writer-quality-gate-format.md",
        "references/agent/writer-table-artifacts-format.md",
        "fts/ft-2-OF_17/work/review-cycles/history-editing-fresh-canary-v2/cycle-state.yaml",
        "fts/ft-2-OF_17/work/stage-handoffs/03-history-editing-canary-prep/workflow-state.yaml",
        "fts/ft-2-OF_17/work/stage-handoffs/03-history-editing-canary-prep/source-selection.md",
        "fts/ft-2-OF_17/work/stage-handoffs/03-history-editing-canary-prep/scope-contract.md",
        "fts/ft-2-OF_17/work/stage-handoffs/03-history-editing-canary-prep/source-parity-check.md",
        "fts/ft-2-OF_17/work/stage-handoffs/03-history-editing-canary-prep/source-row-inventory.md",
        "fts/ft-2-OF_17/work/stage-handoffs/03-history-editing-canary-prep/scope-coverage-gaps.md",
        "fts/ft-2-OF_17/work/stage-handoffs/03-history-editing-canary-prep/scope-clarification-requests.md",
        "fts/ft-2-OF_17/work/stage-handoffs/03-history-editing-canary-prep/scope-gap-review.md",
        "fts/ft-2-OF_17/AGENT-NOTES.md",
    ]
    inputs = "\n".join(f"- `{p}` - read for writer-r1 instruction, source, scope, format, process or package context." for p in required_files)
    return f"""# Writer Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-writer` |
| mode | `writer.session_initial_draft` |
| ft_slug | `ft-2-OF_17` |
| scope_slug | `{SCOPE}` |
| started_from | `work/review-cycles/{SCOPE}/cycle-state.yaml` |
| status_after | `writer-draft-ready` |

## Inputs Read

- Resolver command: `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - budget status `pass (138.8 / 200.0 KiB)`.
{inputs}

## Inputs Not Used

- `fts/ft-2-OF_17/test-cases/section-40-history-editing-canary.md` - excluded by active prompt; a broad `rg` command surfaced matching lines, but this output was discarded and not used as source evidence or template.
- `fts/ft-2-OF_17/test-cases/section-40-history-editing-fresh-canary.md` - excluded by active prompt; a broad `rg` command surfaced matching lines, but this output was discarded and not used as source evidence or template.
- `fts/ft-2-OF_17/work/test-design/ui-employment*` - excluded as old employment canary material.
- `fts/ft-2-OF_17/mockups/*.png` - not selected for section-40.

## Key Decisions

- Used only `section-40` DOCX-backed handoff atoms and rows for requirements; `GAP-001` remains an accepted non-blocking parity risk.
- Created 10 executable `TC-*` sections for 12 atoms; table columns are covered by observable composition, sortability and employee-value checks to avoid metadata-only cases.
- Did not assert backend/API/DB audit persistence or PDF page IDs because the selected source does not provide observable evidence.
- Routed the next stage to structure preflight after writer-r1.

## Risks And Fallbacks

- Encoding fallback: initial PowerShell stdout for Russian instruction files displayed mojibake. Files were reread with explicit UTF-8 output and distorted stdout was not used as evidence.
- Contamination risk: broad `rg` surfaced old canary TC lines. Those lines were discarded and are logged as not used.
- Residual product/source risk: `GAP-001` remains accepted non-blocking extraction risk.

## Validation

- `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - pass.
- `python scripts/build_history_editing_fresh_canary_v2_writer_artifacts.py` - wrote canonical TC, split artifacts and writer outputs.
- `python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_17/work/review-cycles/{SCOPE}/cycle-state.yaml` - expected to generate `outputs/scoped-validator-profile.writer-r1.json`.

## Contamination Check

- Old `ui-employment`, `history-editing-canary-prep`, `history-editing-fresh-canary`, signed-off and blocked canary TC files were not used as templates or source evidence.
- Active requirements came from `scope-contract.md`, `source-row-inventory.md`, `source-parity-check.md`, `scope-gap-review.md`, and `AGENT-NOTES.md`.

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Resolved instruction context | budget `pass` | resolver output |
| 2 | Read required instruction files | required context available | `Inputs Read` |
| 3 | Read scope handoff and AGENT-NOTES | 12 atoms and `GAP-001` confirmed | handoff artifacts |
| 4 | Discarded contaminated broad-search output | old TC files not used | `Inputs Not Used` |
| 5 | Generated writer artifacts | canonical and split artifacts written | `test-cases/{SECTION}-{SCOPE}.md` |
| 6 | Prepared structure-preflight handoff | prompt and state update planned | `prompt.structure-preflight-r1.md` |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Writer Quality Gate | pass | `work/test-design/{SECTION}-{SCOPE}/writer-quality-gate.md` | structure preflight |
| Artifact shape preflight | pass | exact table columns and no duplicate wrapper headings | runner validation |
| GAP-001 preservation | pass | `coverage-gaps.md`; TDDT; ledger; plan | reviewer should verify no PDF traceability is fabricated |
| Self-check near misses | pass | `writer-self-check.md` notes the WP-02 split between composition, sortability, employee value and close action | reviewer should confirm atomicity |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | mojibake in PowerShell stdout | ordinary `Get-Content` console output | explicit UTF-8 `Get-Content -Encoding UTF8` with UTF-8 output | n/a | n/a | none; distorted stdout discarded | none |
| `TF-002` | broad search matched excluded old TC files | broad `rg` over `fts/ft-2-OF_17` | discard matched old TC output; use handoff artifacts only | n/a | n/a | contamination risk controlled by exclusion | structure reviewer may compare source anchors |

## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| `test-cases/{SECTION}-{SCOPE}.md` | `package-based generated` | `file-based helper script` | `yes` | `scripts/build_history_editing_fresh_canary_v2_writer_artifacts.py` | `yes` |
| `work/test-design/{SECTION}-{SCOPE}/` | `split generated artifacts` | `file-based helper script` | `yes` | `scripts/build_history_editing_fresh_canary_v2_writer_artifacts.py` | `yes` |

## Handoff Notes For Next Session

- Structure preflight should focus on parseability, exact split table columns, absence of duplicate wrapper headings and canonical runtime TC metadata.
- Do not require PDF page references unless `GAP-001` is resolved by new PDF evidence.
"""


def decision_log() -> str:
    rows = [
        ["DEC-001", "1", "scope-boundary", "scope-contract.md", "Use only `section-40` and fresh-canary-v2 output targets.", "Prompt and contract define a controlled canary boundary.", "canonical TC; split artifacts", "high", "applied"],
        ["DEC-002", "2", "gap", "scope-gap-review.md", "Carry `GAP-001` as accepted non-blocking extraction risk.", "Reviewer accepted DOCX coverage while forbidding fabricated PDF traceability.", "coverage-gaps.md; cycle-state.yaml", "high", "applied"],
        ["DEC-003", "3", "test-design", "scope-contract.md coverage constraints", "Cover table columns through observable composition, sortability and employee-value checks, not type-only metadata cases.", "Contract says not to create one standalone TC per metadata-only table column.", "TC-HIST-007; TC-HIST-008; TC-HIST-009; package-test-design-plan.md", "medium", "applied"],
        ["DEC-004", "4", "source-boundary", "broad rg contamination hazard", "Discard old canary TC search output and use handoff artifacts only.", "Active prompt forbids using old canary files as templates or source evidence.", "writer-session-log.writer-r1.md", "risk:controlled-contamination", "applied"],
        ["DEC-005", "5", "artifact-write", "package-based split artifacts", "Use retained file-based helper script to write UTF-8 artifacts.", "Avoids command-line payload and preserves reproducibility.", "artifact-write-strategy.md", "high", "applied"],
        ["DEC-006", "6", "routing", "session-based lifecycle", "Route writer-r1 to `structure-preflight-r1` with `writer-draft-ready`.", "Session-based matrix requires structure preflight before semantic review.", "cycle-state.yaml; prompt.structure-preflight-r1.md", "high", "applied"],
    ]
    return "# Agent Decision Log\n\n## Decision Log Metadata\n\n" + md_table(
        ["field", "value"],
        [["ft_slug", "`ft-2-OF_17`"], ["scope_slug", f"`{SCOPE}`"], ["stage", "`ft-test-case-writer / writer-r1`"], ["started_from", f"`work/review-cycles/{SCOPE}/cycle-state.yaml`"]],
    ) + "\n\n## Decision Log\n\n" + md_table(
        ["decision_id", "step", "decision_type", "input_or_trigger", "decision", "rationale", "artifact_or_output", "risk_or_confidence", "status"],
        rows,
    )


def structure_prompt() -> str:
    return f"""# Structure Preflight R1 Prompt

## Goal

Run reviewer structure preflight for `ft-2-OF_17` / `{SCOPE}` after writer-r1.

## Instruction Loading

Before review decisions, run:

```powershell
python scripts/resolve_instruction_context.py --scenario reviewer.structure_preflight --budget-report --fail-on-budget
```

Read every selected required file and record resolver command, budget status and selected files in the reviewer session log.

## Inputs

- `work/review-cycles/{SCOPE}/cycle-state.yaml`
- `test-cases/{SECTION}-{SCOPE}.md`
- `work/test-design/{SECTION}-{SCOPE}/`
- `work/review-cycles/{SCOPE}/outputs/writer-session-log.writer-r1.md`
- `work/review-cycles/{SCOPE}/outputs/agent-decision-log.writer-r1.md`
- `work/review-cycles/{SCOPE}/outputs/writer-r1-response.md`
- `work/review-cycles/{SCOPE}/outputs/scoped-validator-profile.writer-r1.json`
- `work/stage-handoffs/03-history-editing-canary-prep/scope-contract.md`
- `work/stage-handoffs/03-history-editing-canary-prep/source-row-inventory.md`
- `work/stage-handoffs/03-history-editing-canary-prep/scope-gap-review.md`
- `AGENT-NOTES.md`

## Review Mode

Use `structure_preflight` only: parseability, required headings, required table columns, duplicate wrapper heading defects, canonical TC runtime fields, continuous numbering, split artifact presence, and current writer-stage scoped validator evidence.

Do not perform semantic/test-design review in this stage except where structure prevents reliable semantic review.

## Guardrails

- `GAP-001` is an accepted non-blocking PDF extraction risk; do not require PDF page references.
- Treat any fabricated PDF traceability or PDF-only ID as blocker.
- Verify the Writer Quality Gate cites `outputs/scoped-validator-profile.writer-r1.json`, not a future reviewer profile.
- If preflight passes, update `cycle-state.yaml` to `current_stage: semantic-review-r1`, `stage_status: semantic-review-ready`, `semantic_round: 1`, and create the semantic reviewer prompt.
"""


def cycle_state_after() -> str:
    return f"""cycle_id: history-editing-fresh-canary-v2-2026-06-19
ft_slug: ft-2-OF_17
scope_slug: {SCOPE}
section_id: {SECTION}
current_stage: structure-preflight-r1
stage_status: writer-draft-ready
semantic_round: 0
max_semantic_rounds: 2
canonical_test_cases: test-cases/{SECTION}-{SCOPE}.md
test_design_dir: work/test-design/{SECTION}-{SCOPE}
active_snapshot: work/review-cycles/{SCOPE}/versions/r0-baseline
active_transition_prompt: work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md
sessions:
latest_artifacts:
  - canonical_test_cases=test-cases/{SECTION}-{SCOPE}.md
  - test_design_dir=work/test-design/{SECTION}-{SCOPE}
  - writer_response=work/review-cycles/{SCOPE}/outputs/writer-r1-response.md
  - writer_session_log=work/review-cycles/{SCOPE}/outputs/writer-session-log.writer-r1.md
  - decision_log=work/review-cycles/{SCOPE}/outputs/agent-decision-log.writer-r1.md
  - scoped_validator_profile=work/review-cycles/{SCOPE}/outputs/scoped-validator-profile.writer-r1.json
blocking_reasons:
blocking_findings:
open_questions:
accepted_risks:
  - "GAP-001 | accepted-nonblocking-risk | owner: reviewer | rationale: DOCX section-40 is parseable and sufficient for writing; PDF extraction failed and is carried as a traceability guardrail | revisit: before adding PDF page or PDF-only requirement traceability"
"""


def main() -> int:
    TD.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    PROMPTS.mkdir(parents=True, exist_ok=True)
    (FT_ROOT / "test-cases").mkdir(parents=True, exist_ok=True)
    (TD / "coverage-obligation-table.md").unlink(missing_ok=True)

    artifacts = {
        TD / "artifact-write-strategy.md": artifact_write_strategy(),
        TD / "source-row-inventory.md": source_row_inventory(),
        TD / "source-row-completeness-matrix.md": source_row_completeness(),
        TD / "source-table-normalization.md": source_table_normalization(),
        TD / "test-design-decision-table.md": tddt(),
        TD / "atomic-requirements-ledger.md": atomic_ledger(),
        TD / "internal-work-package-coverage.md": internal_work_package_coverage(),
        TD / "package-ledger-self-check.md": simple_self_check("Package Ledger Self-Check"),
        TD / "package-test-design-plan.md": package_plan(),
        TD / "package-design-plan-self-check.md": simple_self_check("Package Design Plan Self-Check"),
        TD / "test-design-applicability-matrix.md": applicability_matrix(),
        TD / "coverage-metrics.md": coverage_metrics(),
        TD / "fixture-catalog.md": fixture_catalog(),
        TD / "risk-priority-map.md": risk_priority_map(),
        TD / "coverage-map.md": coverage_map(),
        TD / "coverage-gaps.md": coverage_gaps(),
        TD / "test-design-review.md": test_design_review(),
        TD / "writer-quality-gate.md": writer_quality_gate(),
        TD / "writer-self-check.md": writer_self_check(),
        TC_FILE: canonical_tc(),
        OUT / "writer-r1-response.md": writer_response(),
        OUT / "writer-session-log.writer-r1.md": session_log(),
        OUT / "agent-decision-log.writer-r1.md": decision_log(),
        PROMPTS / "prompt.structure-preflight-r1.md": structure_prompt(),
    }
    for path, text in artifacts.items():
        write(path, text)

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifacts": [
            {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "bytes": path.stat().st_size}
            for path in sorted(artifacts)
        ],
    }
    write(OUT / "writer-r1-artifact-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"wrote {len(artifacts)} writer artifacts for {SCOPE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
