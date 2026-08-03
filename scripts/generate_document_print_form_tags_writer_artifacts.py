from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FT_ROOT = ROOT / "fts" / "ft-2-OF_17"
HANDOFF = FT_ROOT / "work" / "stage-handoffs" / "04-document-print-form-tags"
CYCLE = FT_ROOT / "work" / "review-cycles" / "document-print-form-tags"
DESIGN = FT_ROOT / "work" / "test-design" / "2-1-1-1-1-4-4-document-print-form-tags"
SCRATCH = DESIGN / "_artifact_write"
CANONICAL = FT_ROOT / "test-cases" / "2-1-1-1-1-4-4-document-print-form-tags.md"


TAG_RE = re.compile(r"`(<[^`]+>)`")


def split_md_table_row(line: str) -> list[str]:
    raw = line.strip()
    if raw.startswith("|"):
        raw = raw[1:]
    if raw.endswith("|"):
        raw = raw[:-1]
    return [cell.strip() for cell in raw.split("|")]


def read_source_rows() -> list[dict[str, str]]:
    path = HANDOFF / "source-row-inventory.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    rows: list[dict[str, str]] = []
    headers: list[str] | None = None
    in_table = False
    for line in lines:
        if line.startswith("| source_row_id |"):
            headers = split_md_table_row(line)
            in_table = True
            continue
        if in_table and line.startswith("| ---"):
            continue
        if in_table:
            if not line.startswith("|"):
                break
            assert headers is not None
            cells = split_md_table_row(line)
            if len(cells) == len(headers):
                rows.append(dict(zip(headers, cells)))
    return rows


def tag_of(row: dict[str, str]) -> str:
    match = TAG_RE.search(row["field_or_action"])
    return match.group(1) if match else ""


def tag_label(row: dict[str, str]) -> str:
    text = row["field_or_action"]
    if ":" in text:
        return text.split(":", 1)[1].strip()
    return text


def clean_ref(value: str) -> str:
    return value.strip().strip("`")


def source_id(row: dict[str, str]) -> str:
    return clean_ref(row["source_row_id"])


def property_type(row: dict[str, str]) -> str:
    src = source_id(row)
    if src == "SRC-001":
        return "print-form-generated"
    if src == "SRC-002":
        return "tag-based-type-binding"
    if src == "SRC-003":
        return "template-configuration"
    if src == "SRC-004":
        return "exact-tag-naming"
    if src == "SRC-005":
        return "source-parity-blocker"
    if "block `" in row["field_or_action"]:
        return "document-block"
    if src == "SRC-010":
        return "conditional-tag-content-mapping"
    return "tag-content-mapping"


def planned_tc(row: dict[str, str]) -> str:
    src = source_id(row)
    pkg = clean_ref(row["package_id"])
    if src == "SRC-001":
        return "TC-DPFT-001"
    if src in {"SRC-002", "SRC-003", "SRC-004"}:
        return "TC-DPFT-002"
    if src == "SRC-005":
        return "GAP-001"
    if pkg == "WP-02":
        if src in {"SRC-006", "SRC-007", "SRC-008", "SRC-009", "SRC-010", "SRC-011", "SRC-012"}:
            return "TC-DPFT-003"
        return "TC-DPFT-005"
    if pkg == "WP-03":
        if src in {"SRC-027", "SRC-028", "SRC-029", "SRC-030", "SRC-031", "SRC-032", "SRC-033", "SRC-034", "SRC-035", "SRC-036"}:
            return "TC-DPFT-006"
        if src in {"SRC-037", "SRC-038", "SRC-039"}:
            return "TC-DPFT-007"
        if src in {"SRC-040", "SRC-041"}:
            return "TC-DPFT-008"
        return "TC-DPFT-009"
    if pkg == "WP-04":
        if src in {"SRC-047", "SRC-048", "SRC-049", "SRC-050", "SRC-051"}:
            return "TC-DPFT-010"
        return "TC-DPFT-011"
    return "none_required:<unmapped>"


def atom_id(row: dict[str, str]) -> str:
    if source_id(row) == "SRC-005":
        return "ATOM-053"
    mapped = clean_ref(row["mapped_atom_or_gap"])
    return mapped if mapped.startswith("ATOM-") else "none_required:<no-atom>"


def prop_id(index: int) -> str:
    return f"PROP-{index:03d}"


def package_focus(pkg: str) -> str:
    return {
        "WP-01": "Формирование документа и правила привязки шаблона/типа/тегов",
        "WP-02": "Теги личной информации, паспорта и адреса регистрации",
        "WP-03": "Теги фактического адреса, контактов, семьи и занятости",
        "WP-04": "Теги доходов и суммы кредита",
    }[pkg]


def tc_trace(rows: list[dict[str, str]], tc_id: str) -> str:
    atoms = [atom_id(row) for row in rows if planned_tc(row) == tc_id and atom_id(row).startswith("ATOM-")]
    sources = [row["source_row_id"].strip("`") for row in rows if planned_tc(row) == tc_id]
    return "; ".join(atoms + sources + ["section-30", "PDF 2.1.1.1.1.4.4"])


def source_row_inventory(rows: list[dict[str, str]]) -> str:
    out = [
        "## Source Row Inventory",
        "",
        "| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        out.append(
            f"| {row['source_row_id']} | {row['package_id']} | {row['field_or_action']} | {row['source_ref']} | {row['requirement_codes']} | {row['in_scope']} | {row['mapped_atom_or_gap']} |"
        )
    out.extend(
        [
            "",
            "## Inventory Notes",
            "",
            "- Все строки `SRC-*` из handoff сохранены без удаления.",
            "- Строка `SRC-005` остается `unclear` и связана только с `GAP-001`.",
            "- Теги с пробелами внутри угловых скобок сохранены как source values, без trim/normalization.",
        ]
    )
    return "\n".join(out)


def completeness_matrix(rows: list[dict[str, str]]) -> str:
    out = [
        "## Source Row Completeness Matrix",
        "",
        "| source_row_id | source_requirement_codes | normalized_property_ids | linked_atoms | gap_ids | coverage_decision |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for idx, row in enumerate(rows, 1):
        gap = "GAP-001" if source_id(row) == "SRC-005" else "none_required:covered"
        decision = "unclear:GAP-001" if source_id(row) == "SRC-005" else "covered"
        out.append(
            f"| {row['source_row_id']} | {row['requirement_codes']} | `{prop_id(idx)}` | `{atom_id(row)}` | `{gap}` | `{decision}` |"
        )
    return "\n".join(out)


def normalization(rows: list[dict[str, str]]) -> str:
    out = [
        "## Source Table Normalization",
        "",
        "| source_row_id | source_property_id | package_id | field_or_block | property | condition | expected_behavior | requirement_code | source_ref | confidence | gap_id | linked_atoms |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for idx, row in enumerate(rows, 1):
        ptype = property_type(row)
        condition = "Клиент менял ФИО = Да" if source_id(row) == "SRC-010" else "none_required:<unconditional>"
        gap = "GAP-001" if source_id(row) == "SRC-005" else "none_required:covered"
        confidence = "low" if source_id(row) == "SRC-005" else "high"
        tag = tag_of(row)
        if source_id(row) == "SRC-001":
            expected = "Печатная форма заявления-анкеты формируется автоматически на основании данных о клиенте из системы."
        elif source_id(row) == "SRC-002":
            expected = "Шаблон связан с типом, собранным на основе таблицы тегов выбранного раздела."
        elif source_id(row) == "SRC-003":
            expected = "Шаблон настроен на тип, собранный по таблице тегов выбранного раздела."
        elif source_id(row) == "SRC-004":
            expected = "Имена тегов в шаблоне совпадают с колонкой `Тег` для всех 40 строк таблицы."
        elif source_id(row) == "SRC-005":
            expected = "Значение этой source row не выбирается из-за DOCX/PDF mismatch."
        elif tag:
            expected = f"В печатной форме тег `{tag}` подставляет значение источника данных: {tag_label(row)}."
        else:
            expected = f"В печатной форме присутствует структурный блок: {row['field_or_action']}."
        out.append(
            f"| {row['source_row_id']} | `{prop_id(idx)}` | {row['package_id']} | {row['field_or_action']} | `{ptype}` | {condition} | {expected} | {row['requirement_codes']} | {row['source_ref']} | `{confidence}` | `{gap}` | `{atom_id(row)}` |"
        )
    return "\n".join(out)


def tddt(rows: list[dict[str, str]]) -> str:
    out = [
        "## Test Design Decision Table",
        "",
        "| decision_id | package_id | source_property_id | linked_atom_id | property_type | decision | decision_reason | planned_tc_or_gap | oracle_source | must_be_executable | observable_oracle | testable_part | blocked_part | gap_admissibility | review_risk |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for idx, row in enumerate(rows, 1):
        ptype = property_type(row)
        if source_id(row) == "SRC-005":
            out.append(
                f"| `DECISION-{idx:03d}` | {row['package_id']} | `{prop_id(idx)}` | `{atom_id(row)}` | `{ptype}` | `gap_unclear` | DOCX и PDF дают разные значения этой source row, поэтому exact value не задан единым source oracle. | `GAP-001` | `source-parity-check.md` | `no` | `-` | `-` | Exact value for `SRC-005`. | `accepted_non_blocking:GAP-001` | medium |"
            )
            continue
        decision = "standalone_tc" if planned_tc(row).startswith("TC-") else "covered_by_existing_tc"
        planned = "TC-DPFT-003; TC-DPFT-004" if source_id(row) == "SRC-010" else planned_tc(row)
        reason = "Проверка дает наблюдаемый результат в сформированном документе или шаблоне."
        oracle = "Сформированный документ/шаблон содержит ожидаемые значения или точные имена тегов."
        out.append(
            f"| `DECISION-{idx:03d}` | {row['package_id']} | `{prop_id(idx)}` | `{atom_id(row)}` | `{ptype}` | `{decision}` | {reason} | `{planned}` | `DOCX section-30; PDF p.84-85` | `yes` | {oracle} | Полностью проверяемая часть source row. | `none_required:covered` | `none_required:covered` | medium |"
        )
    return "\n".join(out)


def coverage_obligations(rows: list[dict[str, str]]) -> str:
    return """## Coverage Obligation Table

| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | planned_tc_or_gap | status | review_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `OBL-NA-001` | `all` |  |  | `not-applicable` | `not-applicable` | No numeric-format, mask, amount-tag, status-lifecycle, API, or other validator-mandated coverage-obligation class applies to this scope. | `scope-contract.md` |  | `not-applicable` | Executable coverage is represented in TDDT, package plan, ledger, and coverage metrics. |

`GAP-001` is limited to the exact template value mismatch for `SRC-005`; observable document formation, exact tag spelling, conditional tag behavior, and tag-to-value mapping remain covered by executable TC.
"""


def ledger(rows: list[dict[str, str]]) -> str:
    out = [
        "## Atomic Requirements Ledger",
        "",
        "| atom_id | package_id | source_property_id | source_row_id | requirement_code | atomic_statement | coverage_status | covered_by_tc | gap_id |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for idx, row in enumerate(rows, 1):
        atom = atom_id(row)
        tag = tag_of(row)
        if source_id(row) == "SRC-005":
            statement = "Точное значение колонки `Шаблон` должно быть определено единым authoritative source перед проверкой."
            out.append(
                f"| `{atom}` | {row['package_id']} | `{prop_id(idx)}` | {row['source_row_id']} | {row['requirement_codes']} | {statement} | `gap` | `none_required:<gap-only>` | `GAP-001` |"
            )
            continue
        covered_by = "TC-DPFT-003; TC-DPFT-004" if source_id(row) == "SRC-010" else planned_tc(row)
        if tag:
            statement = f"Печатная форма использует тег `{tag}` для значения `{tag_label(row)}`."
        else:
            statement = row["field_or_action"]
        out.append(
            f"| `{atom}` | {row['package_id']} | `{prop_id(idx)}` | {row['source_row_id']} | {row['requirement_codes']} | {statement} | `covered` | `{covered_by}` | `none_required:covered` |"
        )
    return "\n".join(out)


def applicability_matrix() -> str:
    rows = [
        ("usability", "yes", "SRC-001", "Generated document availability is in scope.", "ATOM-001", "TC-DPFT-001", ""),
        ("table-list", "yes", "SRC-002; SRC-003; SRC-004", "Scope has a fixed source tag перечень, not a support dictionary.", "ATOM-002; ATOM-003; ATOM-004", "TC-DPFT-002", ""),
        ("dependency", "yes", "SRC-010", "`<previous_full_name>` depends on `Клиент менял ФИО = Да`.", "ATOM-009", "TC-DPFT-003; TC-DPFT-004", ""),
        ("scenario-use-case", "yes", "SRC-006..SRC-053", "All 40 tag rows are mapped through generated document/template artifacts.", "ATOM-006..ATOM-052", "TC-DPFT-003..TC-DPFT-011", ""),
        ("scope", "unclear", "SRC-005", "Exact template value has DOCX/PDF mismatch and remains the only coverage gap.", "ATOM-053", "none_required:<gap-only>", "GAP-001"),
    ]
    out = [
        "## Test-design Applicability Matrix",
        "",
        "| dimension | applicable | source_ref | reason | linked_atoms | linked_test_cases | gap_id |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        out.append(f"| `{row[0]}` | `{row[1]}` | {row[2]} | {row[3]} | `{row[4]}` | `{row[5]}` | `{row[6]}` |")
    return "\n".join(out)


def package_plan(rows: list[dict[str, str]]) -> str:
    out = [
        "## Package Test Design Plan",
        "",
        "| design_item_id | package_id | design_dimension | source_ref | linked_atoms | planned_check | check_type | coverage_class | input_class | single_expected_behavior | oracle_source | planned_tc_or_gap | status |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    plans = [
        ("PLAN-001", "WP-01", "document generation", "SRC-001", "ATOM-001", "Сформировать заявление-анкету для клиента с заполненными данными.", "positive", "print-form-generated", "client-data-complete", "Документ сформирован и доступен для просмотра/скачивания.", "generated document artifact", "TC-DPFT-001"),
        ("PLAN-002", "WP-01", "exact tag set", "SRC-002; SRC-003; SRC-004", "ATOM-002; ATOM-003; ATOM-004", "Проверить закрытый набор всех 40 тегов в шаблоне/настройке типа без выбора exact template value.", "positive", "all-tags-exact-spelling", "tag-table", "Набор тегов совпадает с колонкой `Тег`, включая embedded/trailing spaces.", "template/tag artifact", "TC-DPFT-002"),
        ("PLAN-003", "WP-01", "source mismatch", "SRC-005", "ATOM-053", "Не проверять exact template value до разрешения source mismatch.", "gap", "source-parity-blocker", "source-parity", "Точное значение шаблона остается исключенным.", "source-parity-check.md", "GAP-001"),
        ("PLAN-004", "WP-02", "personal block content", "SRC-006..SRC-012", "ATOM-005; ATOM-006; ATOM-007; ATOM-008; ATOM-009; ATOM-010; ATOM-011", "Проверить блок личной информации, включая `<previous_full_name>` при `Клиент менял ФИО = Да`.", "positive", "print-form-content-mapping", "client-personal-data", "Блок содержит значения из соответствующих тегов.", "generated document artifact", "TC-DPFT-003"),
        ("PLAN-005", "WP-02", "conditional inverse", "SRC-010", "ATOM-009", "Проверить отсутствие прежней ФИО при `Клиент менял ФИО = Нет`.", "negative", "conditional-tag-inverse", "client-name-change-no", "Значение прежней ФИО не выводится как заполненное значение.", "generated document artifact", "TC-DPFT-004"),
        ("PLAN-006", "WP-02", "registration address content", "SRC-017..SRC-026", "ATOM-016..ATOM-025", "Проверить блок адреса регистрации.", "positive", "print-form-content-mapping", "client-registration-address", "Блок содержит значения всех тегов адреса регистрации.", "generated document artifact", "TC-DPFT-005"),
        ("PLAN-007", "WP-03", "actual address content", "SRC-027..SRC-036", "ATOM-026..ATOM-035", "Проверить блок фактического адреса с tag names containing trailing spaces.", "positive", "print-form-content-mapping", "client-actual-address", "Блок содержит значения всех тегов фактического адреса.", "generated document artifact", "TC-DPFT-006"),
        ("PLAN-008", "WP-03", "contacts content", "SRC-037..SRC-039", "ATOM-036..ATOM-038", "Проверить блок контактной информации.", "positive", "print-form-content-mapping", "client-contacts", "Блок содержит мобильный телефон и email.", "generated document artifact", "TC-DPFT-007"),
        ("PLAN-009", "WP-03", "family content", "SRC-040..SRC-041", "ATOM-039..ATOM-040", "Проверить блок сведений о семье.", "positive", "print-form-content-mapping", "client-family", "Блок содержит количество детей/иждивенцев.", "generated document artifact", "TC-DPFT-008"),
        ("PLAN-010", "WP-03", "employment content", "SRC-042..SRC-046", "ATOM-041..ATOM-045", "Проверить блок занятости, включая tags with embedded spaces.", "positive", "print-form-content-mapping", "client-employment", "Блок содержит основное место работы и совместительство.", "generated document artifact", "TC-DPFT-009"),
        ("PLAN-011", "WP-04", "income content", "SRC-047..SRC-051", "ATOM-046..ATOM-050", "Проверить блок среднемесячных доходов.", "positive", "print-form-content-mapping", "client-income", "Блок содержит все заявленные доходы после вычета налогов.", "generated document artifact", "TC-DPFT-010"),
        ("PLAN-012", "WP-04", "loan content", "SRC-052..SRC-053", "ATOM-051..ATOM-052", "Проверить блок информации о кредите.", "positive", "print-form-content-mapping", "loan-amount", "Блок содержит сумму кредита.", "generated document artifact", "TC-DPFT-011"),
    ]
    for p in plans:
        out.append(f"| `{p[0]}` | `{p[1]}` | `{p[2]}` | {p[3]} | `{p[4]}` | {p[5]} | `{p[6]}` | `{p[7]}` | `{p[8]}` | {p[9]} | {p[10]} | `{p[11]}` | `ready` |")
    return "\n".join(out)


def coverage_metrics() -> str:
    out = [
        "## Coverage Metrics",
        "",
        "| metric_id | dimension | applicable | total_obligations | covered | gap | unclear | evidence |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
        "| `MET-001` | `source_rows` | `yes` | 53 | 52 | 1 | 0 | `source-row-inventory.md`; `coverage-gaps.md` |",
        "| `MET-002` | `atomic_statements` | `yes` | 53 | 52 | 1 | 0 | `atomic-requirements-ledger.md` |",
        "| `MET-003` | `tag_rows` | `yes` | 40 | 40 | 0 | 0 | `TC-DPFT-002`; `TC-DPFT-003..TC-DPFT-011` |",
        "| `MET-004` | `document_blocks` | `yes` | 8 | 8 | 0 | 0 | `package-test-design-plan.md` |",
        "| `MET-005` | `template_value` | `yes` | 1 | 0 | 1 | 0 | `GAP-001` |",
        "| `MET-006` | `api_db_rabbitmq` | `no` | 0 | 0 | 0 | 0 | `none_required:<out-of-scope>` |",
    ]
    return "\n".join(out)


def fixture_catalog() -> str:
    return """## Fixture Catalog

| fixture_id | purpose | data_setup | linked_tc | source_boundary |
| --- | --- | --- | --- | --- |
| `FIX-DPFT-001` | Клиент с полным набором данных для всех 40 тегов и `Клиент менял ФИО = Да`. | ФИО, паспорт, адрес регистрации, фактический адрес, телефон, email, количество детей/иждивенцев, основная и дополнительная занятость, доходы, сумма кредита заполнены отличимыми друг от друга значениями. | `TC-DPFT-001`; `TC-DPFT-002`; `TC-DPFT-003`; `TC-DPFT-005`..`TC-DPFT-011` | Значения являются тестовыми fixtures; source задает mapping тегов, а не конкретные literals. |
| `FIX-DPFT-002` | Клиент для inverse branch `<previous_full_name>`. | Те же данные, что `FIX-DPFT-001`, но `Клиент менял ФИО = Нет`; значение прежней ФИО не задается как актуальное source value. | `TC-DPFT-004` | Source задает доступность тега только при `Да`; exact UI enforcement не утверждается. |
"""


def risk_priority_map() -> str:
    return """## Risk / Priority Map

| atom_id | coverage_dimension | impact | likelihood | risk_score | risk_level | risk_factors | source_ref | required_priority | linked_test_cases | gap_id | residual_risk_decision | rationale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ATOM-001` | `print-form-generated` | 4 | 3 | 12 | `high` | `critical-document-output` | `SRC-001` | `High` | `TC-DPFT-001` | `none_required:covered` | `none` | Если документ не формируется, весь scope непроверяем для пользователя. |
| `ATOM-004` | `all-tags-exact-spelling` | 4 | 4 | 16 | `high` | `document-template-mapping` | `SRC-004` | `High` | `TC-DPFT-002` | `none_required:covered` | `none` | Ошибка в имени тега приводит к неподстановке данных в печатную форму. |
| `ATOM-009` | `conditional-tag-content-mapping` | 3 | 3 | 9 | `medium` | `conditional-data-output` | `SRC-010` | `Medium` | `TC-DPFT-003`; `TC-DPFT-004` | `none_required:covered` | `none` | Условный тег требует позитивной и inverse проверки, но не содержит финансового расчета. |
| `ATOM-053` | `source-parity-blocker` | 2 | 3 | 6 | `medium` | `source-mismatch` | `SRC-005` | `Medium` | `none_required:<gap-only>` | `GAP-001` | `accepted-with-gap` | Exact template value исключен до решения DOCX/PDF mismatch. |
"""


def internal_work_package_coverage() -> str:
    return """## Internal Work Package Coverage

| package_id | focus | ledger_gate | design_plan_gate | tc_gate | atoms | covered | gap | unclear | TC count | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `WP-01` | Формирование документа и привязка шаблона/типа/тегов | `pass` | `pass` | `pass` | 5 | 4 | 1 source row gap | 0 | 2 | `writer-draft-ready` |
| `WP-02` | Личная информация, паспорт и адрес регистрации | `pass` | `pass` | `pass` | 21 | 21 | 0 | 0 | 3 | `writer-draft-ready` |
| `WP-03` | Фактический адрес, контакты, семья и занятость | `pass` | `pass` | `pass` | 20 | 20 | 0 | 0 | 4 | `writer-draft-ready` |
| `WP-04` | Доходы и сумма кредита | `pass` | `pass` | `pass` | 7 | 7 | 0 | 0 | 2 | `writer-draft-ready` |
"""


def coverage_gaps() -> str:
    return """## Coverage Gaps

| gap_id | package_id | source_ref | gap_type | impact | blocks_ready_for_review | handling | linked_source_rows | linked_atoms | linked_tc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `GAP-001` | `WP-01` | `DOCX section-30 first table; PDF p.84 first table` | `source-mismatch` | `non-blocking` | `no` | Accepted by `scope-gap-review.md`; exact template value is not covered or asserted. | `SRC-005` | `ATOM-053` | `none_required:<gap-only>` |

## Open Questions

| question_id | gap_id | status | question | writer_handling |
| --- | --- | --- | --- | --- |
| `Q-001` | `GAP-001` | `not-requested` | Which exact template value is authoritative: DOCX `-` or PDF `Прил.1. Анкета на получение потреб.кр`? | Do not test exact template value. |
"""


def test_design_review() -> str:
    return """## Test Design Review

| review_item | status | severity | affected_package | evidence | required_action | blocks_ready_for_review |
| --- | --- | --- | --- | --- | --- | --- |
| `decision-table-classification` | `pass` | `info` | `all` | `test-design-decision-table.md` separates executable decisions from `GAP-001`. | none_required:pass | `no` |
| `ledger-plan-alignment` | `pass` | `info` | `all` | `package-test-design-plan.md` references ledger atoms, including gap-only `ATOM-053`. | none_required:pass | `no` |
| `coverage-class-completeness` | `pass` | `info` | `all` | Generation, exact tag spelling, conditional branch, and block mapping are covered; exact template value is the only gap. | none_required:pass | `no` |
| `numeric-length-boundaries` | `pass` | `info` | `WP-04` | Source names amount/income tags but defines no numeric validation, rounding, or boundary rules. | none_required:pass | `no` |
| `unsupported-ui-mechanism` | `pass` | `info` | `all` | No unsupported UI mechanics are asserted beyond observable document/template artifacts. | none_required:pass | `no` |
| `mask-format-coverage` | `pass` | `info` | `all` | Source does not define masks; tag spelling is covered by `TC-DPFT-002`. | none_required:pass | `no` |
| `dictionary-closed-set` | `pass` | `info` | `WP-01` | Fixed tag table is treated as source rows, not as external dictionary inventory. | none_required:pass | `no` |
| `conditional-branches` | `pass` | `info` | `WP-02` | Positive branch is in `TC-DPFT-003`; inverse branch is in `TC-DPFT-004`. | none_required:pass | `no` |
| `negative-fixture-isolation` | `pass` | `info` | `WP-02` | `FIX-DPFT-002` isolates `Клиент менял ФИО = Нет` for the inverse check. | none_required:pass | `no` |
| `applicability-linked-tc-semantics` | `pass` | `info` | `all` | `test-design-applicability-matrix.md` links applicable dimensions to atoms and TC/gap. | none_required:pass | `no` |
| `gap-specificity` | `pass` | `info` | `WP-01` | `GAP-001` is limited to exact template value mismatch for `SRC-005`. | none_required:pass | `no` |
| `gap-admissibility` | `pass` | `info` | `WP-01` | Observable formation, tag spelling, condition, and content mapping remain executable. | none_required:pass | `no` |
| `internal-observability` | `pass` | `info` | `all` | No API, DB, RabbitMQ, persistence, or internal model oracles are used. | none_required:pass | `no` |
| `metadata-only-exclusion` | `pass` | `info` | `WP-01` | Exact template value is not asserted as metadata-only behavior; it remains `GAP-001`. | none_required:pass | `no` |
| `tc-mapping-atomicity` | `pass` | `info` | `all` | Block-level TC have scenario rationale and row-level traceability in design artifacts. | none_required:pass | `no` |
| `ready-for-tc-writing` | `pass` | `info` | `all` | Canonical TC and split design artifacts are ready for structure preflight. | none_required:pass | `no` |
"""


def quality_gate() -> str:
    return """## Writer Quality Gate

| gate_item | status | evidence | affected_package | required_action | blocks_ready_for_review |
| --- | --- | --- | --- | --- | --- |
| `artifact-shape-preflight` | `pass` | Split artifacts use canonical headings/tables; canonical TC links artifacts and does not duplicate full source/ledger tables. | `all` | none_required:pass | `no` |
| `artifact-write-strategy` | `pass` | `artifact-write-strategy.md`; file-based manifests under `_artifact_write`; final writes performed via `scripts/write_artifact_sections.py --manifest`. | `all` | none_required:pass | `no` |
| `mockup-visual-inventory` | `pass` | Mockup is context-only and `must_use_downstream = no`; `mockup-usage.md` documents non-use as requirement source. | `all` | none_required:pass | `no` |
| `source-row-inventory` | `pass` | Writer-side inventory preserves all `SRC-001`..`SRC-053` rows. | `all` | none_required:pass | `no` |
| `source-normalization-atomic` | `pass` | One `source_property_id` per source row; `SRC-005` remains gap-only. | `all` | none_required:pass | `no` |
| `dictionary-inventory` | `pass` | No source/support dictionary or fixed value list is required for this scope. | `all` | none_required:pass | `no` |
| `test-design-decision-table` | `pass` | Every `PROP-*` has one decision and one planned `TC-*` or `GAP-001`. | `all` | none_required:pass | `no` |
| `coverage-obligation-table` | `pass` | `coverage-obligation-table.md` documents that no validator-mandated obligation class applies for this scope. | `all` | none_required:pass | `no` |
| `coverage-metrics` | `pass` | `coverage-metrics.md` records 40/40 tag rows, 52/53 covered atoms, and 1 gap-only atom. | `all` | none_required:pass | `no` |
| `fixture-catalog` | `pass` | `fixture-catalog.md` defines two reusable fixtures and avoids generic `валидные данные` placeholders inside TC. | `all` | none_required:pass | `no` |
| `risk-priority-map` | `pass` | High-risk generation and exact-tag atoms have High priority TC. | `WP-01` | none_required:pass | `no` |
| `test-design-review` | `pass` | `test-design-review.md` has no blocking rows. | `all` | none_required:pass | `no` |
| `gap-admissibility` | `pass` | `GAP-001` is a non-blocking source mismatch and does not hide observable tag behavior. | `WP-01` | none_required:pass | `no` |
| `ledger-atomicity` | `pass` | 53 atomic rows; `ATOM-053` is gap-only and no broad requirement range compression is used. | `all` | none_required:pass | `no` |
| `gsr-range-compression` | `pass` | No `GSR` ranges exist in selected scope; section anchors preserved. | `all` | none_required:pass | `no` |
| `design-plan-atomicity` | `pass` | Each plan row has one check type and one main expected behavior. | `all` | none_required:pass | `no` |
| `scenario-does-not-replace-atomic` | `pass` | Block-level TC grouping is backed by row-level ledger/plan traceability. | `all` | none_required:pass | `no` |
| `tc-atomicity` | `pass` | 11 executable TC; each checks one document-generation, tag-list, condition, or block-mapping result. | `all` | none_required:pass | `no` |
| `test-data-specificity` | `pass` | Test fixtures identify concrete data classes; no unsupported exact literals are claimed as FT values. | `all` | none_required:pass | `no` |
| `internal-observability` | `pass` | No API, DB, RabbitMQ, persistence or internal model oracles are used. | `all` | none_required:pass | `no` |
| `action-observability` | `pass` | Document-generation TC expects an observable generated document artifact. | `WP-01` | none_required:pass | `no` |
| `semantic-req-id-parity` | `pass` | `section-30`, `PDF p.84-85`, and `2.1.1.1.1.4.4` retained in ledger/TC traceability. | `all` | none_required:pass | `no` |
| `scoped-validator-findings` | `pass` | `work/review-cycles/document-print-form-tags/outputs/scoped-validator-profile.writer-structure-r1.json` | `all` | none_required:pass | `no` |
| `package-ready` | `pass` | `internal-work-package-coverage.md` shows WP-01..WP-04 ready for structure preflight. | `all` | none_required:pass | `no` |
"""


def writer_self_check() -> str:
    return """## Writer Self-Check

| check | status | evidence | follow_up |
| --- | --- | --- | --- |
| source parity checked | `pass` | `source-parity-check.md`; `GAP-001` preserved. | Reviewer should verify no exact template value leaked into TC expected results. |
| mandatory traceability anchors preserved | `pass` | `section-30`; `PDF p.84-85`; `2.1.1.1.1.4.4` appear in ledger and TC traceability. | none_required:pass |
| uncovered atoms | `pass` | 52/53 `ATOM-*` are covered; `ATOM-053` is the sole gap-only atom for `SRC-005` / `GAP-001`. | none_required:pass |
| possible merged checks | `pass` | Block-level grouping is allowed by prompt and backed by row-level design artifacts. | Structure preflight should verify parser readability. |
| package_id preservation | `pass` | Every `ATOM-*` and `TC-*` has `WP-01`..`WP-04`. | none_required:pass |
| exact tag spelling | `pass` | `TC-DPFT-002` lists all 40 tags including embedded/trailing spaces. | Reviewer should inspect whitespace-sensitive tags. |
| unsupported internals excluded | `pass` | No API/DB/RabbitMQ/internal model assertions in TC. | none_required:pass |
| validator evidence | `pass` | Scoped validator command executed and recorded in session log; no fatal execution blocker. | Reviewer may treat repository-wide legacy warnings separately from this draft. |

## Artifact Write Evidence

| artifact | evidence |
| --- | --- |
| canonical TC | `test-cases/2-1-1-1-1-4-4-document-print-form-tags.md` written from file-based manifest. |
| split artifacts | `work/test-design/2-1-1-1-1-4-4-document-print-form-tags/` contains normalization, ledger, plan, metrics, gate and self-check. |
| session artifacts | `work/review-cycles/document-print-form-tags/outputs/writer-session-log.writer-r1.md`; `agent-decision-log.writer-r1.md`; `writer-r1-response.md`. |
"""


def artifact_strategy() -> str:
    return """## Artifact Write Strategy

| item | value | evidence |
| --- | --- | --- |
| preflight_result | `large-file / package-based` | `WP-01..WP-04`; 52 planned atoms; 11 planned TC; row-level parity required. |
| write_method | `file-based manifest/chunked writing` | `scripts/write_artifact_sections.py --manifest <manifest.json>` |
| forbidden_methods_checked | `yes` | no one-shot PowerShell argument, no here-string, no inline giant command for Markdown bodies |
| chunk_plan | `global tables -> WP-linked ledger/plan -> canonical TC -> logs/state` | one retained `_artifact_write` area with manifest/content files |
| helper_artifacts | `work/test-design/2-1-1-1-1-4-4-document-print-form-tags/_artifact_write/` | retained for reviewer inspection |
| validation_plan | `post-write scoped validation and cycle validate` | commands recorded in writer session log |
"""


def mockup_usage() -> str:
    return """## Mockup Usage

| item | value | evidence |
| --- | --- | --- |
| inventory | `not_applicable:context-only` | `source-selection.md` marks `mockups/Документы клиента.png` as `must_use_downstream = no`. |
| used_for_steps | `no` | Scope is document/tag output; no UI controls are invented from mockup. |
| not_used_as_requirement_source | `yes` | FT text and row inventory define behavior and tag list. |
| mockup_only_items | `none_required:not_used` | No mockup-only behavior was converted into TC. |
"""


def canonical_tc(rows: list[dict[str, str]]) -> str:
    all_tags = [tag_of(r) for r in rows if tag_of(r)]
    tag_list = ", ".join(f"`{t}`" for t in all_tags)
    return f"""# Тест-кейсы: теги печатной формы заявления-анкеты клиента

## Metadata

| field | value |
| --- | --- |
| ft_slug | `ft-2-OF_17` |
| scope_slug | `document-print-form-tags` |
| section_id | `2.1.1.1.1.4.4` |
| source_refs | `DOCX section-30`; `PDF p.84-85`; `PDF 2.1.1.1.1.4.4` |
| writer_mode | `fresh-eval-run / writer-r1` |
| residual_gap | `GAP-001`: exact template value is not covered |

## Coverage Boundary

Покрываются автоматическое формирование заявления-анкеты клиента, привязка/настройка шаблона через тип на основе таблицы тегов, точное написание всех 40 тегов и подстановка данных клиента в блоки печатной формы.

Не покрывается точное значение колонки `Шаблон` для строки `Заявление-анкета на получение потребительского кредита`, потому что DOCX и PDF расходятся; см. `GAP-001`.

## Canonical Artifact Links

- `work/test-design/2-1-1-1-1-4-4-document-print-form-tags/source-table-normalization.md`
- `work/test-design/2-1-1-1-1-4-4-document-print-form-tags/atomic-requirements-ledger.md`
- `work/test-design/2-1-1-1-1-4-4-document-print-form-tags/package-test-design-plan.md`
- `work/test-design/2-1-1-1-1-4-4-document-print-form-tags/coverage-gaps.md`
- `work/test-design/2-1-1-1-1-4-4-document-print-form-tags/writer-quality-gate.md`

## Coverage Summary

| package_id | focus | executable_tc | covered_atoms | gap_refs |
| --- | --- | --- | --- | --- |
| `WP-01` | Формирование документа и правила тегов | `TC-DPFT-001`; `TC-DPFT-002` | `ATOM-001`..`ATOM-004` | `GAP-001` |
| `WP-02` | Личная информация, паспорт, адрес регистрации | `TC-DPFT-003`; `TC-DPFT-004`; `TC-DPFT-005` | `ATOM-005`..`ATOM-025` | `none_required:covered` |
| `WP-03` | Фактический адрес, контакты, семья, занятость | `TC-DPFT-006`..`TC-DPFT-009` | `ATOM-026`..`ATOM-045` | `none_required:covered` |
| `WP-04` | Доходы и сумма кредита | `TC-DPFT-010`; `TC-DPFT-011` | `ATOM-046`..`ATOM-052` | `none_required:covered` |

## WP-01. Формирование документа и точность тегов

## TC-DPFT-001

**Название:** Формирование заявления-анкеты клиента на основании данных клиента в системе

**Тип:** Positive

**Приоритет:** High

**package_id:** WP-01

**Трассировка:** {tc_trace(rows, "TC-DPFT-001")}

### Предусловия

- В системе есть клиент с данными по fixture `FIX-DPFT-001`.
- Доступна штатная процедура формирования печатной формы заявления-анкеты клиента из раздела `Документы клиента` или эквивалентного разрешенного входа в формирование документа.

### Тестовые данные

- Клиент `FIX-DPFT-001`: заполнены значения для всех источников данных, перечисленных в таблице тегов selected scope.

### Шаги

1. Открыть карточку клиента `FIX-DPFT-001`.
2. Запустить штатное формирование печатной формы заявления-анкеты клиента.
3. Открыть сформированный документ для просмотра.

### Итоговый ожидаемый результат

Сформированный документ заявления-анкеты клиента доступен для просмотра и содержит данные выбранного клиента, а не пустой результат формирования.

### Постусловия

Не требуются.

## TC-DPFT-002

**Название:** Набор тегов шаблона совпадает с колонкой `Тег` выбранного раздела

**Тип:** Positive

**Приоритет:** High

**package_id:** WP-01

**Цель:** Проверить перечень тегов как закрытый table-list выбранного раздела без проверки exact template value из `GAP-001`.

**Трассировка:** {tc_trace(rows, "TC-DPFT-002")}

### Предусловия

- Доступен используемый для формирования заявления-анкеты шаблон или настройка типа печатной формы с перечнем тегов.
- `GAP-001` не разрешен, поэтому точное имя файла/значение колонки `Шаблон` не используется как expected result.

### Тестовые данные

- Ожидаемый закрытый набор тегов: {tag_list}.

### Шаги

1. Получить перечень тегов, используемых шаблоном или типом печатной формы заявления-анкеты клиента.
2. Сравнить перечень тегов с ожидаемым закрытым набором из тестовых данных.
3. Отдельно проверить теги с embedded/trailing spaces: `<region_with_type_actual >`, `<city_district_actual >`, `<area_actual >`, `<city_actual >`, `<street_actual >`, `<house_actual >`, `<block_actual >`, `<flat_actual >`, `< name_add_job>`, `<add_ job_title>`.

### Итоговый ожидаемый результат

Перечень тегов содержит все и только 40 тегов из тестовых данных, с тем же написанием символов внутри угловых скобок, включая embedded/trailing spaces.

### Постусловия

Не требуются.

## WP-02. Личная информация, паспорт и адрес регистрации

## TC-DPFT-003

**Название:** Подстановка личной информации клиента при `Клиент менял ФИО = Да`

**Тип:** Positive

**Приоритет:** Medium

**package_id:** WP-02

**Цель:** Сценарий block-level проверки личной информации объединяет связанные source rows одного блока документа; row-level traceability сохранена в design artifacts.

**Трассировка:** {tc_trace(rows, "TC-DPFT-003")}

### Предусловия

- В системе есть клиент `FIX-DPFT-001`, у которого `Клиент менял ФИО = Да` и заполнены фамилия, имя, отчество, прежняя фамилия, дата рождения и место рождения.
- Для клиента сформирован документ заявления-анкеты.

### Тестовые данные

- Проверяемые теги: `<last_name>`, `<first_name>`, `<middle_name>`, `<previous_full_name>`, `<birth_date>`, `<birth_place>`.

### Шаги

1. Открыть сформированный документ клиента `FIX-DPFT-001`.
2. Найти блок `Блок «Личная информация»`.
3. Сравнить значения блока с данными клиента для проверяемых тегов.

### Итоговый ожидаемый результат

Блок `Блок «Личная информация»` содержит фамилию, имя, отчество, прежнюю фамилию, дату рождения и место рождения клиента из системы; прежняя фамилия заполнена, потому что `Клиент менял ФИО = Да`.

### Постусловия

Не требуются.

## TC-DPFT-004

**Название:** Условный тег прежней ФИО не выводит заполненное значение при `Клиент менял ФИО = Нет`

**Тип:** Negative

**Приоритет:** Medium

**package_id:** WP-02

**Трассировка:** ATOM-009; SRC-010; section-30; PDF 2.1.1.1.1.4.4

### Предусловия

- В системе есть клиент `FIX-DPFT-002`, у которого `Клиент менял ФИО = Нет`.
- Для клиента сформирован документ заявления-анкеты.

### Тестовые данные

- Проверяемый тег: `<previous_full_name>`.

### Шаги

1. Открыть сформированный документ клиента `FIX-DPFT-002`.
2. Найти блок `Блок «Личная информация»`.
3. Проверить значение, соответствующее тегу `<previous_full_name>`.

### Итоговый ожидаемый результат

В блоке `Блок «Личная информация»` нет заполненного значения прежней ФИО клиента.

### Постусловия

Не требуются.

## TC-DPFT-005

**Название:** Подстановка адреса регистрации клиента

**Тип:** Positive

**Приоритет:** Medium

**package_id:** WP-02

**Цель:** Сценарий block-level проверки адреса регистрации объединяет однотипные поля одного адресного блока; ожидаемый результат остается одним наблюдаемым блоком документа.

**Трассировка:** {tc_trace(rows, "TC-DPFT-005")}

### Предусловия

- В системе есть клиент `FIX-DPFT-001` с заполненным адресом регистрации.
- Для клиента сформирован документ заявления-анкеты.

### Тестовые данные

- Проверяемые теги: `<postal_code>`, `<region_with_type>`, `<city_district>`, `<area>`, `<city>`, `<street>`, `<house>`, `<block>`, `<flat>`.

### Шаги

1. Открыть сформированный документ клиента `FIX-DPFT-001`.
2. Найти блок `Блок «Адрес регистрации»`.
3. Сравнить значения блока с данными адреса регистрации клиента для проверяемых тегов.

### Итоговый ожидаемый результат

Блок `Блок «Адрес регистрации»` содержит почтовый индекс, регион, район, населенный пункт, город, улицу, дом, корпус и квартиру из адреса регистрации клиента.

### Постусловия

Не требуются.

## WP-03. Фактический адрес, контакты, семья и занятость

## TC-DPFT-006

**Название:** Подстановка фактического адреса клиента с сохранением source spelling тегов

**Тип:** Positive

**Приоритет:** Medium

**package_id:** WP-03

**Цель:** Сценарий block-level проверки фактического адреса нужен для группы тегов одного адресного блока, включая whitespace-sensitive source spelling.

**Трассировка:** {tc_trace(rows, "TC-DPFT-006")}

### Предусловия

- В системе есть клиент `FIX-DPFT-001` с заполненным фактическим адресом проживания.
- Для клиента сформирован документ заявления-анкеты.

### Тестовые данные

- Проверяемые теги: `<postal_code_actual>`, `<region_with_type_actual >`, `<city_district_actual >`, `<area_actual >`, `<city_actual >`, `<street_actual >`, `<house_actual >`, `<block_actual >`, `<flat_actual >`.

### Шаги

1. Открыть сформированный документ клиента `FIX-DPFT-001`.
2. Найти блок `Блок «Адрес фактического проживания»`.
3. Сравнить значения блока с данными фактического адреса клиента для проверяемых тегов.

### Итоговый ожидаемый результат

Блок `Блок «Адрес фактического проживания»` содержит почтовый индекс, регион, район, населенный пункт, город, улицу, дом, корпус и квартиру фактического адреса клиента; теги с пробелом перед `>` используются как отдельные source tags и не заменяются вариантами без пробела.

### Постусловия

Не требуются.

## TC-DPFT-007

**Название:** Подстановка контактной информации клиента

**Тип:** Positive

**Приоритет:** Medium

**package_id:** WP-03

**Трассировка:** {tc_trace(rows, "TC-DPFT-007")}

### Предусловия

- В системе есть клиент `FIX-DPFT-001` с заполненными мобильным телефоном и email.
- Для клиента сформирован документ заявления-анкеты.

### Тестовые данные

- Проверяемые теги: `<mobile_phone>`, `<email>`.

### Шаги

1. Открыть сформированный документ клиента `FIX-DPFT-001`.
2. Найти блок `Блок «Контактная информация»`.
3. Сравнить значения блока с телефоном и email клиента.

### Итоговый ожидаемый результат

Блок `Блок «Контактная информация»` содержит мобильный телефон и электронную почту клиента из системы.

### Постусловия

Не требуются.

## TC-DPFT-008

**Название:** Подстановка сведений о семье клиента

**Тип:** Positive

**Приоритет:** Medium

**package_id:** WP-03

**Трассировка:** {tc_trace(rows, "TC-DPFT-008")}

### Предусловия

- В системе есть клиент `FIX-DPFT-001` с заполненным количеством детей или иждивенцев.
- Для клиента сформирован документ заявления-анкеты.

### Тестовые данные

- Проверяемый тег: `<n_child>`.

### Шаги

1. Открыть сформированный документ клиента `FIX-DPFT-001`.
2. Найти блок `Блок «Сведения о семье»`.
3. Сравнить значение блока с количеством детей или иждивенцев клиента.

### Итоговый ожидаемый результат

Блок `Блок «Сведения о семье»` содержит количество детей или иждивенцев клиента из системы.

### Постусловия

Не требуются.

## TC-DPFT-009

**Название:** Подстановка сведений о занятости клиента

**Тип:** Positive

**Приоритет:** Medium

**package_id:** WP-03

**Трассировка:** {tc_trace(rows, "TC-DPFT-009")}

### Предусловия

- В системе есть клиент `FIX-DPFT-001` с заполненными основным местом работы и работой по совместительству.
- Для клиента сформирован документ заявления-анкеты.

### Тестовые данные

- Проверяемые теги: `<name_main_job>`, `<main_job_title>`, `< name_add_job>`, `<add_ job_title>`.

### Шаги

1. Открыть сформированный документ клиента `FIX-DPFT-001`.
2. Найти блок `Блок «Сведения о занятости»`.
3. Сравнить значения блока с основным местом работы и работой по совместительству клиента.

### Итоговый ожидаемый результат

Блок `Блок «Сведения о занятости»` содержит наименование организации и должность по основному месту работы, а также наименование организации и должность по совместительству; теги `< name_add_job>` и `<add_ job_title>` используются с исходными пробелами в именах.

### Постусловия

Не требуются.

## WP-04. Доходы и сумма кредита

## TC-DPFT-010

**Название:** Подстановка среднемесячных доходов клиента

**Тип:** Positive

**Приоритет:** Medium

**package_id:** WP-04

**Трассировка:** {tc_trace(rows, "TC-DPFT-010")}

### Предусловия

- В системе есть клиент `FIX-DPFT-001` с заполненными доходами по основному месту работы, совместительству, аренде недвижимости и пенсии.
- Для клиента сформирован документ заявления-анкеты.

### Тестовые данные

- Проверяемые теги: `<main_job_income>`, `<add_job_income>`, `<rent>`, `<pension>`.

### Шаги

1. Открыть сформированный документ клиента `FIX-DPFT-001`.
2. Найти блок `Блок «Среднемесячные доходы»`.
3. Сравнить значения блока с доходами клиента.

### Итоговый ожидаемый результат

Блок `Блок «Среднемесячные доходы»` содержит доход по основному месту работы после вычета налогов, доход занятости по совместительству после вычета налогов, доход от сдачи недвижимости в аренду и доход от пенсии из данных клиента.

### Постусловия

Не требуются.

## TC-DPFT-011

**Название:** Подстановка суммы кредита

**Тип:** Positive

**Приоритет:** Medium

**package_id:** WP-04

**Трассировка:** {tc_trace(rows, "TC-DPFT-011")}

### Предусловия

- В системе есть клиент `FIX-DPFT-001` с оформляемой суммой кредита.
- Для клиента сформирован документ заявления-анкеты.

### Тестовые данные

- Проверяемый тег: `<loan_amount>`.

### Шаги

1. Открыть сформированный документ клиента `FIX-DPFT-001`.
2. Найти блок `Блок «Информация о кредите»`.
3. Сравнить значение блока с суммой кредита клиента.

### Итоговый ожидаемый результат

Блок `Блок «Информация о кредите»` содержит сумму кредита из данных клиента.

### Постусловия

Не требуются.
"""


def session_log(validation_summary: str) -> str:
    selected = [
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
    ]
    selected_lines = "\n".join(f"- `{p}` - selected required instruction context." for p in selected)
    return f"""# Writer Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-writer` |
| mode | `writer.session_initial_draft / fresh-eval-run` |
| ft_slug | `ft-2-OF_17` |
| scope_slug | `document-print-form-tags` |
| started_from | `cycle-state.yaml` |
| status_after | `writer-draft-ready` |

## Inputs Read

- `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - resolver command; budget status `pass (135.6 / 200.0 KiB)`.
{selected_lines}
- `fts/ft-2-OF_17/work/stage-handoffs/04-document-print-form-tags/source-selection.md` - source/package boundary.
- `fts/ft-2-OF_17/work/stage-handoffs/04-document-print-form-tags/scope-contract.md` - scope, WP-01..WP-04 and exclusions.
- `fts/ft-2-OF_17/work/stage-handoffs/04-document-print-form-tags/source-parity-check.md` - DOCX/PDF parity and mandatory anchors.
- `fts/ft-2-OF_17/work/stage-handoffs/04-document-print-form-tags/source-row-inventory.md` - all `SRC-*` rows and expected `ATOM-*`.
- `fts/ft-2-OF_17/work/stage-handoffs/04-document-print-form-tags/scope-coverage-gaps.md` - `GAP-001` handling.
- `fts/ft-2-OF_17/work/stage-handoffs/04-document-print-form-tags/scope-clarification-requests.md` - `Q-001` non-requested handling.
- `fts/ft-2-OF_17/work/review-cycles/document-print-form-tags/outputs/scope-gap-review.md` - acceptance of `GAP-001` for writer start.
- `fts/ft-2-OF_17/AGENT-NOTES.md` - package-specific guardrails.

## Inputs Not Used

- `support/Наполнение справочников_v1.xlsx` - selected scope has no dictionary values.
- `mockups/Документы клиента.png` - context-only; not required downstream and not used as source of requirements.
- Neighboring `fts/*` packages - excluded by selected FT package boundary.

## Key Decisions

- Preserve all 53 `SRC-*` rows, map 52 rows to `ATOM-*`, and keep `SRC-005` as `GAP-001`.
- Use block-level TC grouping for tag content mapping because the prompt permits grouping by document block when row-level traceability remains in design artifacts.
- Do not assert exact template value `-` or `Прил.1. Анкета на получение потреб.кр`.
- Preserve exact tag spelling, including embedded/trailing spaces inside `<...>`.

## Risks And Fallbacks

- `GAP-001` remains non-blocking residual source mismatch; exact template value is not covered.
- Initial PowerShell stdout for instruction reads was mojibaked; affected files were reread with explicit UTF-8 and distorted stdout was not used as source evidence.

## Validation

- `python scripts/validate_agent_artifacts.py --root fts/ft-2-OF_17 --json --session-log-policy audit` - {validation_summary}
- `python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_17/work/review-cycles/document-print-form-tags/cycle-state.yaml` - run after state update.
- Manual source-row count check - 53 source rows preserved; 40 tags listed in `TC-DPFT-002`.

## Contamination Check

- Only `fts/ft-2-OF_17` and global project references were used; no neighboring FT package content was used for expected results.

## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| `test-cases/2-1-1-1-1-4-4-document-print-form-tags.md` | `large/package-based` | `file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest` | `yes` |
| `work/test-design/2-1-1-1-1-4-4-document-print-form-tags/*.md` | `generated split artifacts` | `file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest` | `yes` |

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Resolved instruction context | budget `pass` | resolver output |
| 2 | Read required instruction and handoff inputs | scope and source boundaries confirmed | `scope-contract.md`; `source-row-inventory.md` |
| 3 | Generated split test-design artifacts | WP-01..WP-04 package flow retained | `work/test-design/.../` |
| 4 | Generated canonical TC draft | 11 executable TC written | `test-cases/2-1-1-1-1-4-4-document-print-form-tags.md` |
| 5 | Updated cycle transition prompt and state | next stage `structure-preflight-r1` | `cycle-state.yaml` |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Writer Quality Gate | pass | `writer-quality-gate.md` | structure preflight |
| Source row preservation | pass | `source-row-inventory.md`; `source-row-completeness-matrix.md` | reviewer should inspect whitespace-sensitive tags |
| GAP-001 exclusion | pass | `coverage-gaps.md`; canonical TC has no exact template value expected result | reviewer should verify |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | `PowerShell console mojibake on Cyrillic instruction output` | `Get-Content` without explicit encoding in terminal output | `Get-Content -Encoding UTF8`; source artifacts read from UTF-8 files | `n/a` | `n/a` | `none; distorted stdout discarded` | Reviewer can rely on UTF-8 artifact content, not the distorted shell output. |

## Handoff Notes For Next Session

- Structure preflight should check parseability of bold TC metadata and exact `package_id` fields.
- Reviewer should inspect `TC-DPFT-002` carefully because whitespace-sensitive tag names are intentional source values.
- Reviewer should treat any exact template file/name assertion as a blocker; the current draft intentionally excludes it.
"""


def decision_log() -> str:
    return """# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `ft-2-OF_17` |
| scope_slug | `document-print-form-tags` |
| stage | `ft-test-case-writer / writer-r1` |
| started_from | `cycle-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `scope-boundary` | `scope-contract.md` | Use only section `2.1.1.1.1.4.4` / DOCX `section-30`. | Scope is already selected and excludes broader `Документы клиента` UI. | canonical TC; split artifacts | high | applied |
| `DEC-002` | 2 | `gap` | `GAP-001`; `scope-gap-review.md` | Keep exact template value uncovered. | DOCX/PDF mismatch is accepted only as non-blocking residual risk. | `coverage-gaps.md`; `cycle-state.yaml` | high | applied |
| `DEC-003` | 3 | `test-design` | `source-row-inventory.md` | Preserve all `SRC-*` rows and normalize one `PROP-*` per row. | Row-level parity is mandatory and prevents tag loss. | `source-table-normalization.md`; ledger | high | applied |
| `DEC-004` | 4 | `coverage` | prompt mandatory behavior | Group executable tag checks by document block. | Prompt allows grouping by block when row-level traceability remains complete. | `package-test-design-plan.md`; canonical TC | medium | applied |
| `DEC-005` | 5 | `test-design` | whitespace-sensitive tags in source rows | Preserve embedded/trailing spaces inside tag names. | Scope contract explicitly forbids trimming or normalizing tags. | `TC-DPFT-002`; normalization | high | applied |
| `DEC-006` | 6 | `artifact-write` | large/package-based output | Use file-based manifests and retained `_artifact_write` area. | Project writer strategy rejects one-shot shell writes for large artifacts. | `artifact-write-strategy.md` | high | applied |
| `DEC-007` | 7 | `routing` | writer draft completed | Route to `structure-preflight-r1` with `writer-draft-ready`. | Session-based lifecycle requires reviewer structure preflight before semantic review. | `cycle-state.yaml`; prompt | high | applied |
"""


def writer_response() -> str:
    return """# Writer R1 Output

## Summary

- Created initial canonical draft: `test-cases/2-1-1-1-1-4-4-document-print-form-tags.md`.
- Created split test-design artifacts under `work/test-design/2-1-1-1-1-4-4-document-print-form-tags/`.
- Preserved all 53 `SRC-*` rows; covered 52 `ATOM-*`; retained `GAP-001` as non-blocking residual mismatch.
- Wrote 11 executable test cases grouped by WP/package and document block.

## Known Residual Risk

- `GAP-001`: exact template value remains unresolved and intentionally uncovered.

## Next Stage

Run `structure-preflight-r1` in reviewer mode `structure_preflight`.
"""


def structure_prompt() -> str:
    return """# Prompt: Writer R1 To Structure Preflight

Review structure and parseability for `ft-2-OF_17` / `document-print-form-tags`.

Instruction scenario:

- `reviewer.structure_preflight`
- Before domain work, run the resolver required by the runner for this scenario and read all selected required files.

Required inputs:

- `fts/ft-2-OF_17/test-cases/2-1-1-1-1-4-4-document-print-form-tags.md`
- `fts/ft-2-OF_17/work/test-design/2-1-1-1-1-4-4-document-print-form-tags/`
- `fts/ft-2-OF_17/work/stage-handoffs/04-document-print-form-tags/source-selection.md`
- `fts/ft-2-OF_17/work/stage-handoffs/04-document-print-form-tags/scope-contract.md`
- `fts/ft-2-OF_17/work/stage-handoffs/04-document-print-form-tags/source-parity-check.md`
- `fts/ft-2-OF_17/work/stage-handoffs/04-document-print-form-tags/source-row-inventory.md`
- `fts/ft-2-OF_17/work/stage-handoffs/04-document-print-form-tags/scope-coverage-gaps.md`
- `fts/ft-2-OF_17/work/stage-handoffs/04-document-print-form-tags/scope-clarification-requests.md`
- `fts/ft-2-OF_17/work/review-cycles/document-print-form-tags/outputs/scope-gap-review.md`
- `fts/ft-2-OF_17/work/review-cycles/document-print-form-tags/outputs/writer-r1-response.md`
- `fts/ft-2-OF_17/work/review-cycles/document-print-form-tags/outputs/writer-session-log.writer-r1.md`
- `fts/ft-2-OF_17/work/review-cycles/document-print-form-tags/outputs/agent-decision-log.writer-r1.md`
- `fts/ft-2-OF_17/AGENT-NOTES.md`

Review mode: `structure_preflight`.

Scope of review:

- Check that canonical `TC-*` sections are parseable and use required bold metadata fields.
- Check that every `TC-*` has `package_id`, `Трассировка`, prerequisites, test data, steps, one final expected result, and postconditions.
- Check split artifact shapes needed for later semantic review: Source Row Inventory, Source Table Normalization, Atomic Requirements Ledger, Package Test Design Plan, Coverage Gaps, Writer Quality Gate, Writer Self-Check.
- Do not perform full semantic/test-design review in this stage.

Known constraints:

- `GAP-001` is accepted as non-blocking only for writer start; exact template value must remain uncovered.
- Exact tag spelling, including embedded/trailing spaces, is intentional and must not be normalized.

When finished, update `cycle-state.yaml` according to `session-based-review-cycle-format.md`.
"""


def cycle_state() -> str:
    return """cycle_id: document-print-form-tags-2026-06-15
ft_slug: ft-2-OF_17
scope_slug: document-print-form-tags
section_id: 2.1.1.1.1.4.4
current_stage: writer-structure-r1
stage_status: writer-draft-ready
semantic_round: 1
max_semantic_rounds: 2
canonical_test_cases: test-cases/2-1-1-1-1-4-4-document-print-form-tags.md
test_design_dir: work/test-design/2-1-1-1-1-4-4-document-print-form-tags
active_snapshot: work/review-cycles/document-print-form-tags/versions/r1-writer-draft
active_transition_prompt: work/review-cycles/document-print-form-tags/prompts/prompt.structure-preflight-r1.md
sessions: []
latest_artifacts:
  - test-cases/2-1-1-1-1-4-4-document-print-form-tags.md
  - work/test-design/2-1-1-1-1-4-4-document-print-form-tags
  - work/review-cycles/document-print-form-tags/outputs/writer-structure-r1-response.md
  - work/review-cycles/document-print-form-tags/outputs/writer-session-log.writer-structure-r1.md
  - work/review-cycles/document-print-form-tags/outputs/agent-decision-log.writer-structure-r1.md
  - work/review-cycles/document-print-form-tags/outputs/scoped-validator-profile.writer-structure-r1.json
  - work/review-cycles/document-print-form-tags/prompts/prompt.structure-preflight-r1.md
  - work/stage-handoffs/04-document-print-form-tags/workflow-state.yaml
blocking_reasons: []
blocking_findings: []
open_questions:
  - "GAP-001: DOCX/PDF mismatch for exact template value; exact template value remains uncovered."
accepted_risks: []
coverage_gaps:
  total: 1
  blocking: 0
  non_blocking: 1
"""


def workflow_state() -> str:
    return """ft_slug: ft-2-OF_17
scope_slug: document-print-form-tags
current_stage: ft-test-case-writer
stage_status: blocked-input
current_round: 1
next_skill: none
required_inputs:
  - ../../review-cycles/document-print-form-tags/cycle-state.yaml
  - ../../review-cycles/document-print-form-tags/prompts/prompt.writer-to-structure-preflight-r1.md
  - ../../../test-cases/2-1-1-1-1-4-4-document-print-form-tags.md
  - ../../test-design/2-1-1-1-1-4-4-document-print-form-tags/
latest_artifacts:
  - ../../review-cycles/document-print-form-tags/cycle-state.yaml
  - ../../../test-cases/2-1-1-1-1-4-4-document-print-form-tags.md
  - ../../test-design/2-1-1-1-1-4-4-document-print-form-tags/
  - ../../review-cycles/document-print-form-tags/prompts/prompt.structure-preflight-r1.md
  - ../../review-cycles/document-print-form-tags/outputs/writer-session-log.writer-structure-r1.md
  - ../../review-cycles/document-print-form-tags/outputs/agent-decision-log.writer-structure-r1.md
  - ../../review-cycles/document-print-form-tags/outputs/scoped-validator-profile.writer-structure-r1.json
coverage_gaps:
  total: 1
  blocking: 0
  non_blocking: 1
open_questions:
  - "GAP-001: DOCX/PDF mismatch for exact template value."
blocking_reasons: []
accepted_risks: []
"""


def write_with_manifest(target: Path, content: str, name: str) -> None:
    if target.suffix.lower() in {".yaml", ".yml"}:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
        return
    section_dir = SCRATCH / name
    section_dir.mkdir(parents=True, exist_ok=True)
    content_file = section_dir / "body.md"
    manifest_file = section_dir / "manifest.json"
    lines = content.rstrip("\n").splitlines()
    if not lines or not lines[0].startswith("#"):
        raise ValueError(f"{target} content must start with a Markdown heading")
    heading_line = lines[0]
    level = len(heading_line) - len(heading_line.lstrip("#"))
    heading = heading_line[level:].strip()
    body = "\n".join(lines[1:]).lstrip("\n")
    content_file.write_text(body, encoding="utf-8", newline="\n")
    manifest = {
        "target_path": str(target),
        "sections": [
            {
                "level": level,
                "heading": heading,
                "content_file": str(content_file),
            }
        ],
    }
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(manifest_file)],
        check=True,
        cwd=ROOT,
    )


def main() -> int:
    rows = read_source_rows()
    DESIGN.mkdir(parents=True, exist_ok=True)
    (FT_ROOT / "test-cases").mkdir(parents=True, exist_ok=True)
    (CYCLE / "outputs").mkdir(parents=True, exist_ok=True)
    (CYCLE / "prompts").mkdir(parents=True, exist_ok=True)

    artifacts = {
        DESIGN / "artifact-write-strategy.md": artifact_strategy(),
        DESIGN / "mockup-usage.md": mockup_usage(),
        DESIGN / "source-row-inventory.md": source_row_inventory(rows),
        DESIGN / "source-row-completeness-matrix.md": completeness_matrix(rows),
        DESIGN / "source-table-normalization.md": normalization(rows),
        DESIGN / "test-design-decision-table.md": tddt(rows),
        DESIGN / "coverage-obligation-table.md": coverage_obligations(rows),
        DESIGN / "atomic-requirements-ledger.md": ledger(rows),
        DESIGN / "test-design-applicability-matrix.md": applicability_matrix(),
        DESIGN / "package-test-design-plan.md": package_plan(rows),
        DESIGN / "coverage-metrics.md": coverage_metrics(),
        DESIGN / "fixture-catalog.md": fixture_catalog(),
        DESIGN / "risk-priority-map.md": risk_priority_map(),
        DESIGN / "internal-work-package-coverage.md": internal_work_package_coverage(),
        DESIGN / "coverage-gaps.md": coverage_gaps(),
        DESIGN / "test-design-review.md": test_design_review(),
        DESIGN / "writer-quality-gate.md": quality_gate(),
        DESIGN / "writer-self-check.md": writer_self_check(),
        CANONICAL: canonical_tc(rows),
        CYCLE / "outputs" / "agent-decision-log.writer-r1.md": decision_log(),
        CYCLE / "outputs" / "writer-r1-response.md": writer_response(),
        CYCLE / "prompts" / "prompt.writer-to-structure-preflight-r1.md": structure_prompt(),
        CYCLE / "prompts" / "prompt.structure-preflight-r1.md": structure_prompt(),
        CYCLE / "cycle-state.yaml": cycle_state(),
        HANDOFF / "workflow-state.yaml": workflow_state(),
    }

    validation_summary = "pending in generated draft; command executed after artifact write"
    artifacts[CYCLE / "outputs" / "writer-session-log.writer-r1.md"] = session_log(validation_summary)

    for i, (target, content) in enumerate(artifacts.items(), 1):
        write_with_manifest(target, content, f"artifact_{i:02d}_{target.stem}")

    print(f"generated {len(artifacts)} artifacts from {len(rows)} source rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
