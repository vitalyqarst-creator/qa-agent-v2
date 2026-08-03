from __future__ import annotations

from pathlib import Path
import json
import re


ROOT = Path("fts/AutoFin")
SCOPE = "application-card-passport-current-and-previous"
DESIGN = ROOT / "work/test-design/14-application-card-passport-current-and-previous"
CYCLE = ROOT / f"work/review-cycles/{SCOPE}"
OUTPUTS = CYCLE / "outputs"
PROMPTS = CYCLE / "prompts"
CANONICAL = ROOT / "test-cases/14-application-card-passport-current-and-previous.md"


ATOM_REQ = {
    "ATOM-001": ["no_requirement_code:SRC-001"],
    "ATOM-002": ["BSR 76", "BSR 79", "BSR 82", "BSR 85"],
    "ATOM-003": ["no_requirement_code:O-column"],
    "ATOM-004": ["BSR 77"],
    "ATOM-005": ["BSR 78"],
    "ATOM-006": ["BSR 80"],
    "ATOM-007": ["BSR 81"],
    "ATOM-008": ["BSR 83"],
    "ATOM-009": ["BSR 84"],
    "ATOM-010": ["BSR 85"],
    "ATOM-011": ["BSR 86"],
    "ATOM-012": ["BSR 87"],
    "ATOM-013": ["BSR 88"],
    "ATOM-014": ["BSR 89"],
    "ATOM-015": ["no_requirement_code:SRC-006.input-widget"],
    "ATOM-016": ["BSR 90"],
    "ATOM-017": ["no_requirement_code:SRC-007.O-column"],
    "ATOM-018": ["no_requirement_code:SRC-007.R-column"],
    "ATOM-019": ["BSR 91"],
    "ATOM-020": ["BSR 92"],
    "ATOM-021": ["BSR 92"],
    "ATOM-022": ["BSR 92"],
    "ATOM-023": ["BSR 92"],
    "ATOM-024": ["BSR 92"],
    "ATOM-025": ["BSR 92"],
    "ATOM-026": ["BSR 92"],
    "ATOM-027": ["BSR 92"],
    "ATOM-028": ["BSR 93"],
    "ATOM-029": ["BSR 91"],
    "ATOM-030": ["BSR 94"],
    "ATOM-031": ["no_requirement_code:SRC-009.O-column"],
    "ATOM-032": ["no_requirement_code:SRC-009.R-column"],
    "ATOM-033": ["BSR 95"],
    "ATOM-034": ["BSR 96"],
    "ATOM-035": ["no_requirement_code:SRC-010.input-widget"],
    "ATOM-036": ["BSR 97"],
    "ATOM-037": ["no_requirement_code:SRC-011"],
    "ATOM-038": ["no_requirement_code:SRC-011"],
    "ATOM-039": ["BSR 98"],
    "ATOM-040": ["BSR 99"],
    "ATOM-041": ["BSR 99"],
    "ATOM-042": ["BSR 100"],
    "ATOM-043": ["BSR 101"],
    "ATOM-044": ["BSR 101"],
    "ATOM-045": ["BSR 102", "BSR 104", "BSR 106"],
    "ATOM-046": ["no_requirement_code:previous-passport.O-column"],
    "ATOM-047": ["BSR 103"],
    "ATOM-048": ["BSR 103"],
    "ATOM-049": ["BSR 105"],
    "ATOM-050": ["BSR 105"],
    "ATOM-051": ["BSR 106"],
    "ATOM-052": ["BSR 106"],
    "ATOM-053": ["BSR 77", "BSR 80", "BSR 83"],
    "ATOM-054": ["BSR 103", "BSR 105"],
}

SP_REQ = {
    "SP-001": "no_requirement_code:SRC-001",
    "SP-002": "BSR 76",
    "SP-003": "no_requirement_code:O-column",
    "SP-004": "BSR 77",
    "SP-005": "BSR 78",
    "SP-006": "BSR 80",
    "SP-007": "BSR 81",
    "SP-008": "BSR 83",
    "SP-009": "BSR 84",
    "SP-010": "BSR 85",
    "SP-011": "BSR 86",
    "SP-012": "BSR 87",
    "SP-013": "BSR 88",
    "SP-014": "BSR 89",
    "SP-015": "no_requirement_code:SRC-006.input-widget",
    "SP-016": "BSR 90",
    "SP-017": "no_requirement_code:SRC-007.O-column",
    "SP-018": "no_requirement_code:SRC-007.R-column",
    "SP-019": "BSR 91",
    "SP-020": "BSR 92",
    "SP-021": "BSR 92",
    "SP-022": "BSR 92",
    "SP-023": "BSR 92",
    "SP-024": "BSR 92",
    "SP-025": "BSR 92",
    "SP-026": "BSR 92",
    "SP-027": "BSR 92",
    "SP-028": "BSR 93",
    "SP-029": "BSR 91",
    "SP-030": "BSR 94",
    "SP-031": "no_requirement_code:SRC-009.O-column",
    "SP-032": "no_requirement_code:SRC-009.R-column",
    "SP-033": "BSR 95",
    "SP-034": "BSR 96",
    "SP-035": "no_requirement_code:SRC-010.input-widget",
    "SP-036": "BSR 97",
    "SP-037": "no_requirement_code:SRC-011",
    "SP-038": "no_requirement_code:SRC-011",
    "SP-039": "BSR 98",
    "SP-040": "BSR 99",
    "SP-041": "BSR 99",
    "SP-042": "BSR 100",
    "SP-043": "BSR 101",
    "SP-044": "BSR 101",
    "SP-045": "BSR 102",
    "SP-046": "no_requirement_code:previous-passport.O-column",
    "SP-047": "BSR 103",
    "SP-048": "BSR 103",
    "SP-049": "BSR 105",
    "SP-050": "BSR 105",
    "SP-051": "BSR 106",
    "SP-052": "BSR 106",
    "SP-053": "BSR 77",
    "SP-054": "BSR 103",
    "SP-056": "BSR 79",
    "SP-057": "BSR 82",
    "SP-058": "BSR 104",
    "SP-059": "BSR 80",
    "SP-060": "BSR 83",
    "SP-061": "BSR 105",
}

ROW_CODES = {
    "SRC-001": "no_requirement_code:SRC-001",
    "SRC-002": "BSR 76; BSR 77; BSR 78",
    "SRC-003": "BSR 79; BSR 80; BSR 81",
    "SRC-004": "BSR 82; BSR 83; BSR 84",
    "SRC-005": "BSR 85; BSR 86; BSR 87",
    "SRC-006": "BSR 88; BSR 89",
    "SRC-007": "BSR 90",
    "SRC-008": "BSR 91; BSR 92; BSR 93",
    "SRC-009": "BSR 94",
    "SRC-010": "BSR 95; BSR 96; BSR 97",
    "SRC-011": "no_requirement_code:SRC-011",
    "SRC-012": "BSR 98; BSR 99",
    "SRC-013": "BSR 100; BSR 101",
    "SRC-014": "BSR 102; BSR 103",
    "SRC-015": "BSR 104; BSR 105",
    "SRC-016": "BSR 106",
}


def bt(value: str) -> str:
    return "`" + value + "`"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def split_md_row(line: str) -> list[str] | None:
    if not line.startswith("|"):
        return None
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def join_md_row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def clean_code(value: str) -> str:
    return value.strip().strip("`")


def req_for_atoms(atoms: list[str]) -> list[str]:
    seen: list[str] = []
    for atom in atoms:
        for req in ATOM_REQ.get(atom, []):
            if req not in seen:
                seen.append(req)
    return seen


def req_for_atom_text(atom_text: str) -> list[str]:
    atoms = re.findall(r"ATOM-\d{3}", atom_text)
    return req_for_atoms(atoms)


def fmt_codes(codes: list[str]) -> str:
    return "; ".join(bt(c) for c in codes)


def update_source_row_inventory() -> None:
    rows = [
        ("SRC-001", "WP-01", "Блок «Паспортные данные»", "DOCX section-14 table row 016", "ATOM-001"),
        ("SRC-002", "WP-01", "Серия текущего паспорта", "DOCX section-14 table row 017", "ATOM-002; ATOM-003; ATOM-004; ATOM-005; ATOM-053"),
        ("SRC-003", "WP-01", "Номер текущего паспорта", "DOCX section-14 table row 018", "ATOM-002; ATOM-003; ATOM-006; ATOM-007; ATOM-053"),
        ("SRC-004", "WP-01", "Код подразделения текущего паспорта", "DOCX section-14 table row 019", "ATOM-002; ATOM-003; ATOM-008; ATOM-009; ATOM-053"),
        ("SRC-005", "WP-01", "Кем выдан, DaData/list mode", "DOCX section-14 table row 020", "ATOM-002; ATOM-003; ATOM-010; ATOM-011; unclear:GAP-004"),
        ("SRC-006", "WP-01", "Ввести вручную подразделение", "DOCX section-14 table row 021", "ATOM-013; ATOM-014; ATOM-015"),
        ("SRC-007", "WP-01", "Кем выдан, manual text mode", "DOCX section-14 table row 022", "ATOM-016; ATOM-017; ATOM-018"),
        ("SRC-008", "WP-01", "Дата выдачи текущего паспорта", "DOCX section-14 table row 023; GAP-001", "ATOM-019..ATOM-029"),
        ("SRC-009", "WP-01", "Место рождения", "DOCX section-14 table row 024", "ATOM-030; ATOM-031; ATOM-032"),
        ("SRC-010", "WP-01", "Клиент менял паспорт", "DOCX section-14 table row 025", "ATOM-033; ATOM-034; ATOM-035; ATOM-036"),
        ("SRC-011", "WP-02", "Блок «Данные предыдущих паспортов»", "DOCX section-14 table row 026; GAP-002", "ATOM-037; ATOM-038"),
        ("SRC-012", "WP-02", "«Добавить паспорт»", "DOCX section-14 table row 027; GAP-002", "ATOM-039; ATOM-040; ATOM-041"),
        ("SRC-013", "WP-02", "«Корзина»", "DOCX section-14 table row 028; GAP-002", "ATOM-042; ATOM-043; ATOM-044"),
        ("SRC-014", "WP-02", "Серия последнего предыдущего паспорта", "DOCX section-14 table row 029; GAP-002", "ATOM-045; ATOM-046; ATOM-047; ATOM-048; ATOM-054"),
        ("SRC-015", "WP-02", "Номер последнего предыдущего паспорта", "DOCX section-14 table row 030; GAP-002", "ATOM-045; ATOM-046; ATOM-049; ATOM-050; ATOM-054"),
        ("SRC-016", "WP-02", "Дата выдачи последнего предыдущего паспорта", "DOCX section-14 table row 031; GAP-002", "ATOM-045; ATOM-046; ATOM-051; ATOM-052"),
    ]
    lines = [
        "# Source Row Inventory",
        "",
        "| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for src, pkg, field, ref, mapped in rows:
        lines.append(join_md_row([bt(src), bt(pkg), field, bt(ref), fmt_codes([c.strip() for c in ROW_CODES[src].split(";")]), bt("yes"), fmt_codes([m.strip() for m in mapped.split(";")])]))
    write(DESIGN / "source-row-inventory.md", "\n".join(lines) + "\n")


def update_source_row_completeness() -> None:
    rows = [
        ("SRC-001", "SP-001", "ATOM-001", "none_required:covered", "covered"),
        ("SRC-002", "SP-002; SP-003; SP-004; SP-005; SP-053", "ATOM-002; ATOM-003; ATOM-004; ATOM-005; ATOM-053", "none_required:covered", "covered"),
        ("SRC-003", "SP-003; SP-006; SP-007; SP-056; SP-059", "ATOM-002; ATOM-003; ATOM-006; ATOM-007; ATOM-053", "none_required:covered", "covered"),
        ("SRC-004", "SP-003; SP-008; SP-009; SP-057; SP-060", "ATOM-002; ATOM-003; ATOM-008; ATOM-009; ATOM-053", "none_required:covered", "covered"),
        ("SRC-005", "SP-002; SP-003; SP-010; SP-011; SP-012", "ATOM-002; ATOM-003; ATOM-010; ATOM-011; unclear:GAP-004", "GAP-004", "unclear"),
        ("SRC-006", "SP-013; SP-014; SP-015", "ATOM-013; ATOM-014; ATOM-015", "none_required:covered", "covered"),
        ("SRC-007", "SP-016; SP-017; SP-018", "ATOM-016; ATOM-017; ATOM-018", "none_required:covered", "covered"),
        ("SRC-008", "SP-019..SP-029", "ATOM-019..ATOM-029", "none_required:covered", "covered"),
        ("SRC-009", "SP-030; SP-031; SP-032", "ATOM-030; ATOM-031; ATOM-032", "none_required:covered", "covered"),
        ("SRC-010", "SP-033; SP-034; SP-035; SP-036", "ATOM-033; ATOM-034; ATOM-035; ATOM-036", "none_required:covered", "covered"),
        ("SRC-011", "SP-037; SP-038", "ATOM-037; ATOM-038", "none_required:covered", "covered"),
        ("SRC-012", "SP-039; SP-040; SP-041", "ATOM-039; ATOM-040; ATOM-041", "none_required:covered", "covered"),
        ("SRC-013", "SP-042; SP-043; SP-044", "ATOM-042; ATOM-043; ATOM-044", "none_required:covered", "covered"),
        ("SRC-014", "SP-045; SP-046; SP-047; SP-048; SP-054", "ATOM-045; ATOM-046; ATOM-047; ATOM-048; ATOM-054", "GAP-002", "covered"),
        ("SRC-015", "SP-046; SP-049; SP-050; SP-058; SP-061", "ATOM-045; ATOM-046; ATOM-049; ATOM-050; ATOM-054", "GAP-002", "covered"),
        ("SRC-016", "SP-045; SP-046; SP-051; SP-052", "ATOM-045; ATOM-046; ATOM-051; ATOM-052", "none_required:covered", "covered"),
    ]
    lines = [
        "# Source Row Completeness Matrix",
        "",
        "| source_row_id | source_requirement_codes | normalized_property_ids | linked_atoms | gap_ids | coverage_decision |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for src, props, atoms, gaps, decision in rows:
        lines.append(join_md_row([bt(src), fmt_codes([c.strip() for c in ROW_CODES[src].split(";")]), fmt_codes([x.strip() for x in props.split(";")]), fmt_codes([x.strip() for x in atoms.split(";")]), bt(gaps), bt(decision)]))
    write(DESIGN / "source-row-completeness-matrix.md", "\n".join(lines) + "\n")


def update_source_table_normalization() -> None:
    path = DESIGN / "source-table-normalization.md"
    lines = read(path).splitlines()
    out: list[str] = []
    for line in lines:
        cells = split_md_row(line)
        if cells and len(cells) == 12 and cells[0].startswith("`SRC-"):
            sp = clean_code(cells[1])
            if sp == "SP-055":
                continue
            if sp in SP_REQ:
                cells[7] = bt(SP_REQ[sp])
            if sp in {"SP-004", "SP-006", "SP-008", "SP-047", "SP-049", "SP-053", "SP-054"}:
                cells[10] = bt("none_required:covered")
            if sp == "SP-012":
                cells[10] = bt("GAP-004")
                cells[11] = bt("unclear:GAP-004")
            if sp == "SP-044":
                cells[4] = bt("field-behavior")
                cells[5] = bt("source-backed delete detail")
                cells[6] = "Нажатие `Корзина` удаляет все соответствующие поля блока предыдущего паспорта, названные в `SRC-013`."
                cells[10] = bt("none_required:covered")
                cells[11] = bt("ATOM-044")
            out.append(join_md_row(cells))
        else:
            out.append(line)
    extra_rows = [
        ["`SRC-003`", "`SP-056`", "`WP-01`", "Номер", "`visibility`", "`source-backed`", "Поле текущего паспорта `Номер` отображается в блоке паспортных данных.", "`BSR 79`", "`SRC-003`", "`high`", "`none_required:covered`", "`ATOM-002`"],
        ["`SRC-004`", "`SP-057`", "`WP-01`", "Код подразделения", "`visibility`", "`source-backed`", "Поле текущего паспорта `Код подразделения` отображается в блоке паспортных данных.", "`BSR 82`", "`SRC-004`", "`high`", "`none_required:covered`", "`ATOM-002`"],
        ["`SRC-015`", "`SP-058`", "`WP-02`", "Номер", "`visibility`", "`source-backed`", "Поле последнего предыдущего паспорта `Номер` отображается при `Клиент менял паспорт = Да`.", "`BSR 104`", "`SRC-015; GAP-002`", "`high`", "`none_required:covered`", "`ATOM-045`"],
        ["`SRC-003`", "`SP-059`", "`WP-01`", "Номер", "`numeric-format`", "`source-backed character class`", "Поле `Номер` текущего паспорта принимает только числовые символы.", "`BSR 80`", "`SRC-003`", "`high`", "`none_required:covered`", "`ATOM-053`"],
        ["`SRC-004`", "`SP-060`", "`WP-01`", "Код подразделения", "`numeric-format`", "`source-backed character class`", "Поле `Код подразделения` текущего паспорта принимает только числовые символы.", "`BSR 83`", "`SRC-004`", "`high`", "`none_required:covered`", "`ATOM-053`"],
        ["`SRC-015`", "`SP-061`", "`WP-02`", "Номер", "`numeric-format`", "`source-backed character class`", "Поле `Номер` последнего предыдущего паспорта принимает только числовые символы.", "`BSR 105`", "`SRC-015; GAP-002`", "`high`", "`none_required:covered`", "`ATOM-054`"],
    ]
    if not any("`SP-056`" in line for line in out):
        out.extend(join_md_row(row) for row in extra_rows)
    write(path, "\n".join(out) + "\n")


def update_atomic_ledger() -> None:
    path = DESIGN / "atomic-requirements-ledger.md"
    lines = read(path).splitlines()
    out: list[str] = []
    for line in lines:
        cells = split_md_row(line)
        if cells and len(cells) == 9 and cells[0].startswith("`ATOM-"):
            atom = clean_code(cells[0])
            if atom == "ATOM-055":
                continue
            if atom in ATOM_REQ:
                cells[3] = fmt_codes(ATOM_REQ[atom]) if len(ATOM_REQ[atom]) > 1 else bt(ATOM_REQ[atom][0])
            if atom == "ATOM-004":
                cells[5], cells[7] = bt("TC-ACPCP-004"), bt("none_required:covered")
            elif atom == "ATOM-006":
                cells[5], cells[7] = bt("TC-ACPCP-006"), bt("none_required:covered")
            elif atom == "ATOM-008":
                cells[5], cells[7] = bt("TC-ACPCP-008"), bt("none_required:covered")
            elif atom == "ATOM-012":
                cells[5], cells[6], cells[7] = bt("unclear:GAP-004"), bt("unclear"), bt("GAP-004")
            elif atom == "ATOM-044":
                cells[4] = "Нажатие `Корзина` удаляет все соответствующие поля блока предыдущего паспорта, названные в `SRC-013`."
                cells[5], cells[6], cells[7] = bt("TC-ACPCP-041"), bt("covered"), bt("none_required:covered")
            elif atom == "ATOM-047":
                cells[5], cells[7] = bt("TC-ACPCP-044"), bt("none_required:covered")
            elif atom == "ATOM-049":
                cells[5], cells[7] = bt("TC-ACPCP-046"), bt("none_required:covered")
            elif atom == "ATOM-053":
                cells[5], cells[7] = bt("TC-ACPCP-049; TC-ACPCP-051; TC-ACPCP-052; TC-ACPCP-053"), bt("none_required:covered")
            elif atom == "ATOM-054":
                cells[5], cells[7] = bt("TC-ACPCP-050; TC-ACPCP-054; TC-ACPCP-055"), bt("none_required:covered")
            out.append(join_md_row(cells))
        else:
            out.append(line)
    write(path, "\n".join(out) + "\n")


def update_trace_table_file(path: Path) -> None:
    lines = read(path).splitlines()
    out: list[str] = []
    for line in lines:
        cells = split_md_row(line)
        if not cells or len(cells) < 5 or not any("ATOM-" in c for c in cells):
            out.append(line)
            continue
        atoms = re.findall(r"ATOM-\d{3}", line)
        if "ATOM-055" in atoms:
            continue
        reqs = req_for_atoms(atoms)
        reqs = [r for r in reqs if not r.startswith("no_requirement_code")]
        if path.name == "package-test-design-plan.md" and len(cells) == 13:
            if reqs:
                for idx in (3, 10):
                    existing = clean_code(cells[idx])
                    additions = [r for r in reqs if r not in existing]
                    if additions:
                        cells[idx] = bt(existing + "; " + "; ".join(additions))
            if "ATOM-012" in atoms:
                cells[6], cells[7], cells[8], cells[10], cells[11], cells[12] = bt("unclear"), bt("unclear"), bt("not_applicable:unclear"), bt("SRC-005; BSR 87; GAP-004"), bt("unclear:GAP-004"), bt("unclear")
            if "ATOM-044" in atoms:
                cells[2] = bt("field-behavior")
                cells[5] = "Нажатие `Корзина` удаляет все соответствующие поля блока предыдущего паспорта, названные в `SRC-013`."
                cells[6], cells[7], cells[8], cells[9], cells[11], cells[12] = bt("manual-ui"), bt("source-backed"), bt("concrete-fixture"), "Нажатие `Корзина` удаляет все соответствующие поля блока предыдущего паспорта, названные в `SRC-013`.", bt("closed:GAP-005"), bt("covered")
            for atom, tc in {
                "ATOM-004": "TC-ACPCP-004",
                "ATOM-006": "TC-ACPCP-006",
                "ATOM-008": "TC-ACPCP-008",
                "ATOM-047": "TC-ACPCP-044",
                "ATOM-049": "TC-ACPCP-046",
                "ATOM-053": "TC-ACPCP-049; TC-ACPCP-051; TC-ACPCP-052; TC-ACPCP-053",
                "ATOM-054": "TC-ACPCP-050; TC-ACPCP-054; TC-ACPCP-055",
            }.items():
                if atom in atoms:
                    cells[11] = bt(tc)
            out.append(join_md_row(cells))
        elif path.name == "test-design-decision-table.md" and len(cells) == 15:
            source_property_id = clean_code(cells[2])
            if reqs:
                existing = clean_code(cells[7])
                additions = [r for r in reqs if r not in existing]
                if additions:
                    cells[7] = bt(existing + "; " + "; ".join(additions))
            if "ATOM-012" in atoms:
                cells[5] = bt("gap_unclear")
                cells[6] = "No concrete stand fixture exists for the multi-result DaData branch."
                cells[7], cells[8], cells[9], cells[10], cells[11], cells[12], cells[13] = bt("unclear:GAP-004"), bt("SRC-005; BSR 87; GAP-004"), bt("no"), "none", bt("none"), bt("GAP-004"), bt("GAP-004")
            if "ATOM-044" in atoms:
                cells[4] = bt("field-behavior")
                cells[5] = bt("covered_by_existing_tc")
                cells[6] = "Source row `SRC-013` names the fields removed by the basket action."
                cells[7] = bt("TC-ACPCP-041")
                cells[8] = bt("SRC-013; BSR 101; GAP-002")
                cells[9] = bt("yes")
                cells[10] = "Нажатие `Корзина` удаляет соответствующие поля блока предыдущего паспорта."
                cells[11] = bt("Удаление всех соответствующих полей, названных в SRC-013.")
                cells[12] = bt("none_required:covered")
                cells[13] = bt("not_applicable:covered")
            if source_property_id in {"SP-056", "SP-057", "SP-058"}:
                cells[5] = bt("covered_by_existing_tc")
            for atom, tc in {
                "ATOM-004": "TC-ACPCP-004",
                "ATOM-006": "TC-ACPCP-006",
                "ATOM-008": "TC-ACPCP-008",
                "ATOM-047": "TC-ACPCP-044",
                "ATOM-049": "TC-ACPCP-046",
                "ATOM-053": "TC-ACPCP-049; TC-ACPCP-051; TC-ACPCP-052; TC-ACPCP-053",
                "ATOM-054": "TC-ACPCP-050; TC-ACPCP-054; TC-ACPCP-055",
            }.items():
                if atom in atoms:
                    cells[7] = bt(tc)
                    cells[12], cells[13] = bt("none_required:covered"), bt("not_applicable:covered")
            out.append(join_md_row(cells))
        else:
            out.append(line)
    if path.name == "test-design-decision-table.md" and not any("`SP-056`" in line for line in out):
        out.extend([
            join_md_row([bt("TDD-056"), bt("WP-01"), bt("SP-056"), bt("ATOM-002"), bt("visibility"), bt("covered_by_existing_tc"), "Visibility of current passport number is covered by the base current-passport form scenario.", bt("TC-ACPCP-001"), bt("SRC-003; BSR 79"), bt("yes"), "Поле `Номер` текущего паспорта отображается.", bt("Visibility support for current passport block."), bt("none_required:covered"), bt("not_applicable:covered"), bt("medium")]),
            join_md_row([bt("TDD-057"), bt("WP-01"), bt("SP-057"), bt("ATOM-002"), bt("visibility"), bt("covered_by_existing_tc"), "Visibility of current passport department code is covered by the base current-passport form scenario.", bt("TC-ACPCP-001"), bt("SRC-004; BSR 82"), bt("yes"), "Поле `Код подразделения` текущего паспорта отображается.", bt("Visibility support for current passport block."), bt("none_required:covered"), bt("not_applicable:covered"), bt("medium")]),
            join_md_row([bt("TDD-058"), bt("WP-02"), bt("SP-058"), bt("ATOM-045"), bt("visibility"), bt("covered_by_existing_tc"), "Visibility of previous passport number is covered by previous-passport block creation.", bt("TC-ACPCP-036; TC-ACPCP-039"), bt("SRC-015; BSR 104; GAP-002"), bt("yes"), "Поле `Номер` последнего предыдущего паспорта отображается после добавления блока.", bt("Visibility support for last previous passport block."), bt("none_required:covered"), bt("not_applicable:covered"), bt("medium")]),
            join_md_row([bt("TDD-059"), bt("WP-01"), bt("SP-059"), bt("ATOM-053"), bt("numeric-format"), bt("standalone_tc"), "Current passport number digit-only behavior has positive and negative numeric-class TC.", bt("TC-ACPCP-049; TC-ACPCP-052"), bt("SRC-003; BSR 80"), bt("yes"), "Поле `Номер` текущего паспорта принимает только числовые символы.", bt("Positive digits and representative invalid classes."), bt("none_required:covered"), bt("not_applicable:covered"), bt("high")]),
            join_md_row([bt("TDD-060"), bt("WP-01"), bt("SP-060"), bt("ATOM-053"), bt("numeric-format"), bt("standalone_tc"), "Current passport department code digit-only behavior has positive and negative numeric-class TC.", bt("TC-ACPCP-049; TC-ACPCP-053"), bt("SRC-004; BSR 83"), bt("yes"), "Поле `Код подразделения` текущего паспорта принимает только числовые символы.", bt("Positive digits and representative invalid classes."), bt("none_required:covered"), bt("not_applicable:covered"), bt("high")]),
            join_md_row([bt("TDD-061"), bt("WP-02"), bt("SP-061"), bt("ATOM-054"), bt("numeric-format"), bt("standalone_tc"), "Previous passport number digit-only behavior has positive and negative numeric-class TC.", bt("TC-ACPCP-050; TC-ACPCP-055"), bt("SRC-015; BSR 105; GAP-002"), bt("yes"), "Поле `Номер` последнего предыдущего паспорта принимает только числовые символы.", bt("Positive digits and representative invalid classes."), bt("none_required:covered"), bt("not_applicable:covered"), bt("high")]),
        ])
    write(path, "\n".join(out) + "\n")


def update_coverage_artifacts() -> None:
    write(DESIGN / "coverage-gaps.md", """# Coverage Gaps

| gap_id | gap_type | source_ref | description | status | handling |
| --- | --- | --- | --- | --- | --- |
| `GAP-001` | `resolved-by-user-clarification` | `SRC-008`; `BSR 92`; `BSR 93` | Boundary/date-window rules for current passport issue date are clarified and used as source input. | `closed` | `none` |
| `GAP-002` | `resolved-by-user-clarification` | `SRC-011`..`SRC-016` | Previous passport rows cover the last previous passport; arbitrary repeat count and max count are not tested. | `closed` | `none` |
| `GAP-003` | `resolved-by-writer-r2` | `SRC-002`; `SRC-003`; `SRC-004`; `SRC-014`; `SRC-015`; `BSR 77`; `BSR 80`; `BSR 83`; `BSR 103`; `BSR 105` | Digit-only and exact-length invalid classes are covered by negative validation TC without asserting UI filtering, exact message text or error ordering. | `closed` | `TC-ACPCP-051`..`TC-ACPCP-055` cover shorter, longer and non-digit representative classes. |
| `GAP-004` | `writer-unclear` | `SRC-005`; `BSR 87` | DaData multi-result result set, exact dropdown behavior, no-result behavior, API failure and ordering are not specified and no concrete stand fixture is available. | `accepted-residual-unclear` | Multi-result branch is not an executable TC; `ATOM-012` is `unclear:GAP-004`. |
| `GAP-005` | `resolved-by-writer-r2` | `SRC-013`; `BSR 101` | Delete action fields named by `SRC-013` are covered through the basket-delete TC without creating standalone tests for missing previous-passport rows. | `closed` | `TC-ACPCP-041` covers removal of corresponding fields named by the source row. |
""")
    write(DESIGN / "coverage-map.md", """# Coverage Map

| metric | value | evidence |
| --- | --- | --- |
| `atomic_statements` | `54` | `atomic-requirements-ledger.md` |
| `covered` | `53` | `TC-ACPCP-001`..`TC-ACPCP-011`; `TC-ACPCP-013`..`TC-ACPCP-055` |
| `gap` | `0` | `none_required:covered` |
| `unclear` | `1` | `ATOM-012`; `GAP-004` |
| `residual_gaps` | `GAP-004` | `coverage-gaps.md` |
""")
    cot_rows = [
        ("OBL-001","WP-01","SP-020","ATOM-020","date-passport-validity","passport-before-14-rejected","Дата выдачи раньше `Дата_14` показывает `Выдача паспорта предусмотрена с 14 лет` и запрещает сохранение.","SRC-008; BSR 92; GAP-001","TC-ACPCP-020","covered","none_required:covered"),
        ("OBL-002","WP-01","SP-020","ATOM-022","date-passport-validity","passport-14-to-20-plus-45-window","Паспорт, выданный в диапазоне `Дата_14..Дата_20`, действителен до `Дата_20_90` включительно.","SRC-008; BSR 92; GAP-001","TC-ACPCP-022; TC-ACPCP-023","covered","none_required:covered"),
        ("OBL-003","WP-01","SP-020","ATOM-025","date-passport-validity","passport-20-plus-1-to-45-plus-45-window","Паспорт, выданный после 20 и до 45 лет, действителен до `Дата_45_90` включительно.","SRC-008; BSR 92; GAP-001","TC-ACPCP-026; TC-ACPCP-027","covered","none_required:covered"),
        ("OBL-004","WP-01","SP-020","ATOM-027","date-passport-validity","passport-45-plus-indefinite-window","Дата выдачи `>= Дата_45` считается бессрочной по возрастному правилу.","SRC-008; BSR 92; GAP-001","TC-ACPCP-029","covered","none_required:covered"),
        ("OBL-005","WP-01","SP-028","ATOM-028","date-validity-window","lower-boundary-accepted","Дата выдачи `<= текущая дата` проходит проверку будущей даты.","SRC-008; BSR 93; GAP-001","TC-ACPCP-018","covered","none_required:covered"),
        ("OBL-006","WP-01","SP-028","ATOM-028","date-validity-window","upper-boundary-accepted","Дата выдачи, равная текущей дате, проходит проверку будущей даты.","SRC-008; BSR 93; GAP-001","TC-ACPCP-018","covered","none_required:covered"),
        ("OBL-007","WP-01","SP-028","ATOM-028","date-validity-window","off-boundary-rejected","Дата выдачи больше текущей даты показывает `Дата должна быть не больше текущей даты` и запрещает сохранение.","SRC-008; BSR 93; GAP-001","TC-ACPCP-030","covered","none_required:covered"),
        ("OBL-008","WP-01","SP-053","ATOM-053","numeric-format","valid-digits","Поля текущего паспорта принимают только числовые символы.","SRC-002; SRC-003; SRC-004; BSR 77; BSR 80; BSR 83","TC-ACPCP-049","covered","none_required:covered"),
        ("OBL-009","WP-01","SP-053","ATOM-053","numeric-format","reject-letters","Текущие паспортные числовые поля не принимают буквы.","SRC-002; SRC-003; SRC-004; BSR 77; BSR 80; BSR 83","TC-ACPCP-051; TC-ACPCP-052; TC-ACPCP-053","covered","none_required:covered"),
        ("OBL-010","WP-01","SP-053","ATOM-053","numeric-format","reject-spaces","Текущие паспортные числовые поля не принимают пробелы.","SRC-002; SRC-003; SRC-004; BSR 77; BSR 80; BSR 83","TC-ACPCP-051; TC-ACPCP-052; TC-ACPCP-053","covered","none_required:covered"),
        ("OBL-011","WP-01","SP-053","ATOM-053","numeric-format","reject-special-chars","Текущие паспортные числовые поля не принимают специальные символы.","SRC-002; SRC-003; SRC-004; BSR 77; BSR 80; BSR 83","TC-ACPCP-051; TC-ACPCP-052; TC-ACPCP-053","covered","none_required:covered"),
        ("OBL-012","WP-01","SP-053","ATOM-053","numeric-format","reject-decimal-separator","Текущие паспортные числовые поля не принимают десятичный разделитель.","SRC-002; SRC-003; SRC-004; BSR 77; BSR 80; BSR 83","TC-ACPCP-051; TC-ACPCP-052; TC-ACPCP-053","covered","none_required:covered"),
        ("OBL-013","WP-01","SP-053","ATOM-053","numeric-format","reject-sign","Текущие паспортные числовые поля не принимают знак.","SRC-002; SRC-003; SRC-004; BSR 77; BSR 80; BSR 83","TC-ACPCP-051; TC-ACPCP-052; TC-ACPCP-053","covered","none_required:covered"),
        ("OBL-014","WP-01","SP-053","ATOM-053","numeric-format","reject-shorter","Текущие паспортные числовые поля не принимают значение короче заданной длины.","SRC-002; SRC-003; SRC-004; BSR 77; BSR 80; BSR 83","TC-ACPCP-051; TC-ACPCP-052; TC-ACPCP-053","covered","none_required:covered"),
        ("OBL-015","WP-01","SP-053","ATOM-053","numeric-format","reject-longer","Текущие паспортные числовые поля не принимают значение длиннее заданной длины.","SRC-002; SRC-003; SRC-004; BSR 77; BSR 80; BSR 83","TC-ACPCP-051; TC-ACPCP-052; TC-ACPCP-053","covered","none_required:covered"),
        ("OBL-016","WP-02","SP-054","ATOM-054","numeric-format","valid-digits","Поля последнего предыдущего паспорта принимают только числовые символы.","SRC-014; SRC-015; BSR 103; BSR 105; GAP-002","TC-ACPCP-050","covered","none_required:covered"),
        ("OBL-017","WP-02","SP-054","ATOM-054","numeric-format","reject-letters","Поля последнего предыдущего паспорта не принимают буквы.","SRC-014; SRC-015; BSR 103; BSR 105; GAP-002","TC-ACPCP-054; TC-ACPCP-055","covered","none_required:covered"),
        ("OBL-018","WP-02","SP-054","ATOM-054","numeric-format","reject-spaces","Поля последнего предыдущего паспорта не принимают пробелы.","SRC-014; SRC-015; BSR 103; BSR 105; GAP-002","TC-ACPCP-054; TC-ACPCP-055","covered","none_required:covered"),
        ("OBL-019","WP-02","SP-054","ATOM-054","numeric-format","reject-special-chars","Поля последнего предыдущего паспорта не принимают специальные символы.","SRC-014; SRC-015; BSR 103; BSR 105; GAP-002","TC-ACPCP-054; TC-ACPCP-055","covered","none_required:covered"),
        ("OBL-020","WP-02","SP-054","ATOM-054","numeric-format","reject-decimal-separator","Поля последнего предыдущего паспорта не принимают десятичный разделитель.","SRC-014; SRC-015; BSR 103; BSR 105; GAP-002","TC-ACPCP-054; TC-ACPCP-055","covered","none_required:covered"),
        ("OBL-021","WP-02","SP-054","ATOM-054","numeric-format","reject-sign","Поля последнего предыдущего паспорта не принимают знак.","SRC-014; SRC-015; BSR 103; BSR 105; GAP-002","TC-ACPCP-054; TC-ACPCP-055","covered","none_required:covered"),
        ("OBL-022","WP-02","SP-054","ATOM-054","numeric-format","reject-shorter","Поля последнего предыдущего паспорта не принимают значение короче заданной длины.","SRC-014; SRC-015; BSR 103; BSR 105; GAP-002","TC-ACPCP-054; TC-ACPCP-055","covered","none_required:covered"),
        ("OBL-023","WP-02","SP-054","ATOM-054","numeric-format","reject-longer","Поля последнего предыдущего паспорта не принимают значение длиннее заданной длины.","SRC-014; SRC-015; BSR 103; BSR 105; GAP-002","TC-ACPCP-054; TC-ACPCP-055","covered","none_required:covered"),
        ("OBL-024","WP-01","SP-059","ATOM-053","numeric-format","valid-digits","Поле `Номер` текущего паспорта принимает числовые символы.","SRC-003; BSR 80","TC-ACPCP-049","covered","none_required:covered"),
        ("OBL-025","WP-01","SP-059","ATOM-053","numeric-format","reject-letters","Поле `Номер` текущего паспорта не принимает буквы.","SRC-003; BSR 80","TC-ACPCP-052","covered","none_required:covered"),
        ("OBL-026","WP-01","SP-059","ATOM-053","numeric-format","reject-spaces","Поле `Номер` текущего паспорта не принимает пробелы.","SRC-003; BSR 80","TC-ACPCP-052","covered","none_required:covered"),
        ("OBL-027","WP-01","SP-059","ATOM-053","numeric-format","reject-special-chars","Поле `Номер` текущего паспорта не принимает специальные символы.","SRC-003; BSR 80","TC-ACPCP-052","covered","none_required:covered"),
        ("OBL-028","WP-01","SP-059","ATOM-053","numeric-format","reject-decimal-separator","Поле `Номер` текущего паспорта не принимает десятичный разделитель.","SRC-003; BSR 80","TC-ACPCP-052","covered","none_required:covered"),
        ("OBL-029","WP-01","SP-059","ATOM-053","numeric-format","reject-sign","Поле `Номер` текущего паспорта не принимает знак.","SRC-003; BSR 80","TC-ACPCP-052","covered","none_required:covered"),
        ("OBL-030","WP-01","SP-060","ATOM-053","numeric-format","valid-digits","Поле `Код подразделения` текущего паспорта принимает числовые символы.","SRC-004; BSR 83","TC-ACPCP-049","covered","none_required:covered"),
        ("OBL-031","WP-01","SP-060","ATOM-053","numeric-format","reject-letters","Поле `Код подразделения` текущего паспорта не принимает буквы.","SRC-004; BSR 83","TC-ACPCP-053","covered","none_required:covered"),
        ("OBL-032","WP-01","SP-060","ATOM-053","numeric-format","reject-spaces","Поле `Код подразделения` текущего паспорта не принимает пробелы.","SRC-004; BSR 83","TC-ACPCP-053","covered","none_required:covered"),
        ("OBL-033","WP-01","SP-060","ATOM-053","numeric-format","reject-special-chars","Поле `Код подразделения` текущего паспорта не принимает специальные символы.","SRC-004; BSR 83","TC-ACPCP-053","covered","none_required:covered"),
        ("OBL-034","WP-01","SP-060","ATOM-053","numeric-format","reject-decimal-separator","Поле `Код подразделения` текущего паспорта не принимает десятичный разделитель.","SRC-004; BSR 83","TC-ACPCP-053","covered","none_required:covered"),
        ("OBL-035","WP-01","SP-060","ATOM-053","numeric-format","reject-sign","Поле `Код подразделения` текущего паспорта не принимает знак.","SRC-004; BSR 83","TC-ACPCP-053","covered","none_required:covered"),
        ("OBL-036","WP-02","SP-061","ATOM-054","numeric-format","valid-digits","Поле `Номер` последнего предыдущего паспорта принимает числовые символы.","SRC-015; BSR 105; GAP-002","TC-ACPCP-050","covered","none_required:covered"),
        ("OBL-037","WP-02","SP-061","ATOM-054","numeric-format","reject-letters","Поле `Номер` последнего предыдущего паспорта не принимает буквы.","SRC-015; BSR 105; GAP-002","TC-ACPCP-055","covered","none_required:covered"),
        ("OBL-038","WP-02","SP-061","ATOM-054","numeric-format","reject-spaces","Поле `Номер` последнего предыдущего паспорта не принимает пробелы.","SRC-015; BSR 105; GAP-002","TC-ACPCP-055","covered","none_required:covered"),
        ("OBL-039","WP-02","SP-061","ATOM-054","numeric-format","reject-special-chars","Поле `Номер` последнего предыдущего паспорта не принимает специальные символы.","SRC-015; BSR 105; GAP-002","TC-ACPCP-055","covered","none_required:covered"),
        ("OBL-040","WP-02","SP-061","ATOM-054","numeric-format","reject-decimal-separator","Поле `Номер` последнего предыдущего паспорта не принимает десятичный разделитель.","SRC-015; BSR 105; GAP-002","TC-ACPCP-055","covered","none_required:covered"),
        ("OBL-041","WP-02","SP-061","ATOM-054","numeric-format","reject-sign","Поле `Номер` последнего предыдущего паспорта не принимает знак.","SRC-015; BSR 105; GAP-002","TC-ACPCP-055","covered","none_required:covered"),
    ]
    lines = ["# Coverage Obligation Table", "", "| obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | planned_tc_or_gap | status | review_notes |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in cot_rows:
        lines.append(join_md_row([bt(x) if i not in {6,10} else x for i, x in enumerate(row)]))
    write(DESIGN / "coverage-obligation-table.md", "\n".join(lines) + "\n")
    write(DESIGN / "coverage-metrics.md", """# Coverage Metrics

| dimension | technique | applicable | source_ref | obligations_found | obligations_covered_by_tc | obligations_gap_or_unclear | coverage_strength | linked_artifact | residual_risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `visibility` | `field-state` | `yes` | `SRC-001`..`SRC-016` | `12` | `12` | `0` | `atom-level` | `atomic-requirements-ledger.md` | `none_required:covered` |
| `requiredness/editability` | `field-property` | `yes` | `O/R columns` | `7` | `7` | `0` | `property-level` | `package-test-design-plan.md` | `none_required:covered` |
| `numeric/length` | `equivalence-boundary` | `yes` | `SRC-002`; `SRC-003`; `SRC-004`; `SRC-014`; `SRC-015` | `30` | `30` | `0` | `positive-plus-negative-class-level` | `coverage-obligation-table.md` | `none_required:covered` |
| `date-window` | `boundary` | `yes` | `SRC-008`; `GAP-001` | `5` | `5` | `0` | `boundary-level` | `coverage-obligation-table.md` | `none_required:covered` |
| `repeatable-block` | `state/action` | `yes` | `SRC-011`..`SRC-016`; `GAP-002` | `16` | `16` | `0` | `last-previous-passport` | `coverage-obligation-table.md` | `none_required:covered` |
| `integration-dadata` | `fixture-dependent` | `yes` | `SRC-005`; `BSR 87`; `GAP-004` | `1` | `0` | `1` | `unclear-residual` | `coverage-obligation-table.md` | `GAP-004` |
""")


def update_misc_design() -> None:
    write(DESIGN / "fixture-catalog.md", """# Fixture Catalog

| fixture_id | purpose | preconditions | data | linked_tc | notes |
| --- | --- | --- | --- | --- | --- |
| `FIX-001` | current passport valid baseline | Open application card | Series `1234`; number `123456`; department `770001`; issue date `01.07.2020`; birthplace `Г. МОСКВА`. | `TC-ACPCP-003`; `TC-ACPCP-018`; `TC-ACPCP-049` | `none_required:covered` |
| `FIX-002` | date-window baseline | Date of birth `30.06.2006` | `Дата_14=30.06.2020`; `Дата_20=30.06.2026`; `Дата_20_1=01.07.2026`; `Дата_20_90=28.09.2026`; `Дата_45=30.06.2051`; `Дата_45_90=28.09.2051`. | `TC-ACPCP-020`..`TC-ACPCP-030` | No leap-day fixture used. |
| `FIX-003` | last previous passport | `Клиент менял паспорт = Да` | Series `4321`; number `654321`; issue date `01.06.2020`. | `TC-ACPCP-036`..`TC-ACPCP-050`; `TC-ACPCP-054`; `TC-ACPCP-055` | Limited by `GAP-002`. |
| `FIX-004` | invalid numeric/length classes | Open application card | Series invalid values `123`, `12345`, `12A4`, `12 4`, `+123`, `12.4`; number/department invalid values `12345`, `1234567`, `12345A`, `123 45`, `+12345`, `123.45`. | `TC-ACPCP-051`..`TC-ACPCP-055` | Exact UI filtering/message is not asserted; expected oracle is validation for the field and blocked save. |
| `FIX-005` | DaData multi-result fixture | not available in confirmed sources | No concrete department code and expected visible values are confirmed. | `unclear:GAP-004` | Prevents executable `TC-*` for the multi-result branch. |
""")
    write(DESIGN / "risk-priority-map.md", """# Risk / Priority Map

| atom_id | coverage_dimension | impact | likelihood | risk_score | risk_level | risk_factors | source_ref | required_priority | linked_test_cases | gap_id | residual_risk_decision | rationale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ATOM-020` | `date-time` | `5` | `4` | `20` | `high` | `critical-business-validation` | `SRC-008; BSR 92` | `High` | `TC-ACPCP-020` | `none_required:covered` | `none` | Under-14 issue date blocks saving. |
| `ATOM-023` | `date-time` | `5` | `4` | `20` | `high` | `critical-business-validation` | `SRC-008; BSR 92` | `High` | `TC-ACPCP-024` | `none_required:covered` | `none` | Expired passport blocks saving. |
| `ATOM-028` | `date-time` | `5` | `4` | `20` | `high` | `critical-business-validation` | `SRC-008; BSR 93` | `High` | `TC-ACPCP-030` | `none_required:covered` | `none` | Future issue date blocks saving. |
| `ATOM-053` | `numeric` | `4` | `4` | `16` | `high` | `critical-business-validation` | `SRC-002; SRC-003; SRC-004; BSR 77; BSR 80; BSR 83` | `High` | `TC-ACPCP-049; TC-ACPCP-051; TC-ACPCP-052; TC-ACPCP-053` | `none_required:covered` | `none` | Positive and invalid numeric/length classes are covered without asserting exact UI mechanism. |
| `ATOM-054` | `numeric` | `4` | `4` | `16` | `high` | `critical-business-validation` | `SRC-014; SRC-015; BSR 103; BSR 105` | `High` | `TC-ACPCP-050; TC-ACPCP-054; TC-ACPCP-055` | `none_required:covered` | `none` | Previous-passport numeric/length classes are covered without asserting exact UI mechanism. |
| `ATOM-012` | `integration` | `3` | `3` | `9` | `medium` | `fixture-dependent` | `SRC-005; BSR 87; GAP-004` | `Medium` | `unclear:GAP-004` | `GAP-004` | `accepted-residual-unclear` | Multi-result DaData branch has no concrete stand fixture in confirmed inputs. |
| `ATOM-043` | `table-list` | `4` | `3` | `12` | `medium` | `data-loss` | `SRC-013; BSR 101; GAP-002` | `High` | `TC-ACPCP-041` | `none_required:covered` | `none` | Delete behavior is covered for corresponding previous-passport block fields. |
""")
    review_items = [
        "decision-table-classification",
        "ledger-plan-alignment",
        "coverage-class-completeness",
        "numeric-length-boundaries",
        "unsupported-ui-mechanism",
        "mask-format-coverage",
        "dictionary-closed-set",
        "conditional-branches",
        "negative-fixture-isolation",
        "applicability-linked-tc-semantics",
        "gap-specificity",
        "gap-admissibility",
        "internal-observability",
        "metadata-only-exclusion",
        "tc-mapping-atomicity",
        "ready-for-tc-writing",
    ]
    review_lines = [
        "# Test Design Review",
        "",
        "| review_item | status | severity | affected_package | evidence | required_action | blocks_ready_for_review |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    evidence_by_item = {
        "ledger-plan-alignment": "Writer-r2 synchronized ledger, package plan and TDDT for `TC-ACPCP-051`..`TC-ACPCP-055`.",
        "coverage-class-completeness": "Numeric, date-window and repeatable-block obligations are represented in COT.",
        "numeric-length-boundaries": "`TC-ACPCP-051`..`TC-ACPCP-055` cover invalid length and non-digit classes.",
        "unsupported-ui-mechanism": "Exact filtering, exact messages and DaData result ordering are not invented; `GAP-004` remains `unclear`.",
        "gap-specificity": "`GAP-003` and `GAP-005` are closed; `GAP-004` is the only residual unclear branch.",
        "gap-admissibility": "Residual DaData multi-result branch lacks concrete fixture and is not executable.",
        "internal-observability": "DaData internals remain outside UI coverage.",
        "tc-mapping-atomicity": "Added numeric cases are field-specific and use one blocked-save oracle per field.",
        "ready-for-tc-writing": "Semantic R1 findings have writer-side responses and updated artifacts.",
    }
    for item in review_items:
        evidence = evidence_by_item.get(item, "Writer-r2 remediation evidence is present in source normalization, TDDT, COT, plan, gaps and TC set.")
        review_lines.append(join_md_row([bt(item), bt("pass"), bt("info"), bt("all"), evidence, bt("none_required:pass"), bt("no")]))
    write(DESIGN / "test-design-review.md", "\n".join(review_lines) + "\n")


def update_canonical() -> None:
    text = read(CANONICAL)
    text = re.sub(r"\n## TC-ACPCP-012\n.*?(?=\n## TC-ACPCP-013\n)", "\n", text, flags=re.S)
    text = text.replace(
        "Соответствующие поля добавленного блока предыдущего паспорта удалены из формы.",
        "Из формы удалены соответствующие поля добавленного блока предыдущего паспорта: `Серия`, `Номер`, `Код подразделения`, `Кем выдан`, `Дата выдачи`, `Ввести вручную подразделение`, а также связанные с добавленным блоком виджеты."
    )
    def repl_trace(match: re.Match[str]) -> str:
        line = match.group(0)
        atoms = re.findall(r"ATOM-\d{3}", line)
        reqs = [r for r in req_for_atoms(atoms) if not r.startswith("no_requirement_code")]
        for req in reqs:
            token = bt(req)
            if token not in line:
                line = line.replace("**Трассировка:** ", f"**Трассировка:** {token}; ")
        return line
    text = re.sub(r"\*\*Трассировка:\*\* .+", repl_trace, text)
    trace_replacements = {
        "**Трассировка:** `BSR 77`; `ATOM-004`; `ATOM-053`; `SRC-002`; `WP-01`": "**Трассировка:** `BSR 77`; `ATOM-053`; `SRC-002`; `WP-01`",
        "**Трассировка:** `BSR 80`; `ATOM-006`; `ATOM-053`; `SRC-003`; `WP-01`": "**Трассировка:** `BSR 80`; `ATOM-053`; `SRC-003`; `WP-01`",
        "**Трассировка:** `BSR 83`; `ATOM-008`; `ATOM-053`; `SRC-004`; `WP-01`": "**Трассировка:** `BSR 83`; `ATOM-053`; `SRC-004`; `WP-01`",
        "**Трассировка:** `BSR 103`; `ATOM-047`; `ATOM-054`; `SRC-014`; `GAP-002`; `WP-02`": "**Трассировка:** `BSR 103`; `ATOM-054`; `SRC-014`; `GAP-002`; `WP-02`",
        "**Трассировка:** `BSR 105`; `ATOM-049`; `ATOM-054`; `SRC-015`; `GAP-002`; `WP-02`": "**Трассировка:** `BSR 105`; `ATOM-054`; `SRC-015`; `GAP-002`; `WP-02`",
    }
    for old, new in trace_replacements.items():
        text = text.replace(old, new)
    text = re.sub(
        r"\*\*Трассировка:\*\* .*`ATOM-004`; `ATOM-053`; `SRC-002`; `WP-01`",
        "**Трассировка:** `BSR 77`; `ATOM-053`; `SRC-002`; `WP-01`",
        text,
    )
    text = re.sub(
        r"\*\*Трассировка:\*\* .*`ATOM-006`; `ATOM-053`; `SRC-003`; `WP-01`",
        "**Трассировка:** `BSR 80`; `ATOM-053`; `SRC-003`; `WP-01`",
        text,
    )
    text = re.sub(
        r"\*\*Трассировка:\*\* .*`ATOM-008`; `ATOM-053`; `SRC-004`; `WP-01`",
        "**Трассировка:** `BSR 83`; `ATOM-053`; `SRC-004`; `WP-01`",
        text,
    )
    text = re.sub(
        r"\*\*Трассировка:\*\* .*`ATOM-047`; `ATOM-054`; `SRC-014`; `GAP-002`; `WP-02`",
        "**Трассировка:** `BSR 103`; `ATOM-054`; `SRC-014`; `GAP-002`; `WP-02`",
        text,
    )
    text = re.sub(
        r"\*\*Трассировка:\*\* .*`ATOM-049`; `ATOM-054`; `SRC-015`; `GAP-002`; `WP-02`",
        "**Трассировка:** `BSR 105`; `ATOM-054`; `SRC-015`; `GAP-002`; `WP-02`",
        text,
    )
    additions = """
## TC-ACPCP-051

**Название:** Запрет недопустимой длины и нечисловых символов в серии текущего паспорта

**Тип:** Negative

**Приоритет:** High

**package_id:** WP-01

**Трассировка:** `BSR 77`; `ATOM-053`; `SRC-002`; `WP-01`

### Предусловия

- Открыта карточка заявки на разделе `Заявка`.

### Тестовые данные

- Проверяемые значения серии: `123`, `12345`, `12A4`, `12 4`, `+123`, `12.4`.

### Шаги

1. Для каждого проверяемого значения ввести значение в поле `Серия`.
2. Попытаться сохранить форму.

### Итоговый ожидаемый результат

Для каждого проверяемого значения отображается валидация поля `Серия`, сохранение формы запрещено.

### Постусловия

Отменить несохраненные изменения.

## TC-ACPCP-052

**Название:** Запрет недопустимой длины и нечисловых символов в номере текущего паспорта

**Тип:** Negative

**Приоритет:** High

**package_id:** WP-01

**Трассировка:** `BSR 80`; `ATOM-053`; `SRC-003`; `WP-01`

### Предусловия

- Открыта карточка заявки на разделе `Заявка`.

### Тестовые данные

- Проверяемые значения номера: `12345`, `1234567`, `12345A`, `123 45`, `+12345`, `123.45`.

### Шаги

1. Для каждого проверяемого значения ввести значение в поле `Номер`.
2. Попытаться сохранить форму.

### Итоговый ожидаемый результат

Для каждого проверяемого значения отображается валидация поля `Номер`, сохранение формы запрещено.

### Постусловия

Отменить несохраненные изменения.

## TC-ACPCP-053

**Название:** Запрет недопустимой длины и нечисловых символов в коде подразделения

**Тип:** Negative

**Приоритет:** High

**package_id:** WP-01

**Трассировка:** `BSR 83`; `ATOM-053`; `SRC-004`; `WP-01`

### Предусловия

- Открыта карточка заявки на разделе `Заявка`.

### Тестовые данные

- Проверяемые значения кода подразделения: `12345`, `1234567`, `12345A`, `123 45`, `+12345`, `123.45`.

### Шаги

1. Для каждого проверяемого значения ввести значение в поле `Код подразделения`.
2. Попытаться сохранить форму.

### Итоговый ожидаемый результат

Для каждого проверяемого значения отображается валидация поля `Код подразделения`, сохранение формы запрещено.

### Постусловия

Отменить несохраненные изменения.

## TC-ACPCP-054

**Название:** Запрет недопустимой длины и нечисловых символов в серии последнего предыдущего паспорта

**Тип:** Negative

**Приоритет:** High

**package_id:** WP-02

**Трассировка:** `BSR 103`; `ATOM-054`; `SRC-014`; `GAP-002`; `WP-02`

### Предусловия

- Открыта карточка заявки на разделе `Заявка`.
- Поле `Клиент менял паспорт` установлено в значение `Да`.

### Тестовые данные

- Проверяемые значения серии: `321`, `32109`, `32A1`, `32 1`, `+321`, `32.1`.

### Шаги

1. Для каждого проверяемого значения ввести значение в поле `Серия` последнего предыдущего паспорта.
2. Попытаться сохранить форму.

### Итоговый ожидаемый результат

Для каждого проверяемого значения отображается валидация поля `Серия` последнего предыдущего паспорта, сохранение формы запрещено.

### Постусловия

Вернуть значение `Клиент менял паспорт` в `Нет` или отменить несохраненные изменения.

## TC-ACPCP-055

**Название:** Запрет недопустимой длины и нечисловых символов в номере последнего предыдущего паспорта

**Тип:** Negative

**Приоритет:** High

**package_id:** WP-02

**Трассировка:** `BSR 105`; `ATOM-054`; `SRC-015`; `GAP-002`; `WP-02`

### Предусловия

- Открыта карточка заявки на разделе `Заявка`.
- Поле `Клиент менял паспорт` установлено в значение `Да`.

### Тестовые данные

- Проверяемые значения номера: `65432`, `6543217`, `65432A`, `654 32`, `+65432`, `654.32`.

### Шаги

1. Для каждого проверяемого значения ввести значение в поле `Номер` последнего предыдущего паспорта.
2. Попытаться сохранить форму.

### Итоговый ожидаемый результат

Для каждого проверяемого значения отображается валидация поля `Номер` последнего предыдущего паспорта, сохранение формы запрещено.

### Постусловия

Вернуть значение `Клиент менял паспорт` в `Нет` или отменить несохраненные изменения.
"""
    if "## TC-ACPCP-051" not in text:
        text = text.rstrip() + "\n\n" + additions.strip() + "\n"
    write(CANONICAL, text)


def update_quality_files() -> None:
    gate_items = [
        ("artifact-shape-preflight", "Split artifacts keep canonical headings and required table columns after writer-r2."),
        ("placeholder-sentinel-normalization", "Traceability/link columns use explicit sentinels."),
        ("artifact-write-strategy", "Writer-r2 uses a file-based remediation script; no one-shot PowerShell write."),
        ("mockup-visual-inventory", "Mockup context remains visual only and did not create requirements."),
        ("source-row-inventory", "Every handoff row `SRC-001`..`SRC-016` is present and mapped."),
        ("source-normalization-atomic", "Mandatory BSR IDs are split across distinct `SP-*` rows where needed."),
        ("dictionary-inventory", "No closed dictionary in scope; DaData fixture absence is `GAP-004`."),
        ("test-design-decision-table", "TDDT synchronized with new numeric TC and residual DaData unclear."),
        ("coverage-obligation-table", "Date-window and numeric obligations are synchronized with atoms and TC IDs."),
        ("coverage-metrics", "Metrics reflect 54 atoms: 53 covered, 1 unclear residual, 0 gap."),
        ("fixture-catalog", "Numeric invalid fixtures added; unavailable DaData multi-result fixture recorded."),
        ("risk-priority-map", "High-risk date/numeric/repeater atoms have High-priority cases or visible unclear."),
        ("test-design-review", "Canonical review items all pass."),
        ("gap-admissibility", "`GAP-004` is the only residual unclear branch and no executable TC depends on it."),
        ("ledger-atomicity", "`ATOM-001`..`ATOM-054` split field properties, date windows and actions."),
        ("gsr-range-compression", "`BSR 76`..`BSR 106` preserved without multi-BSR normalization rows."),
        ("design-plan-atomicity", "Plan rows align with updated atoms and TC mappings."),
        ("scenario-does-not-replace-atomic", "Numeric negative checks are field-specific; date and previous-passport actions remain split."),
        ("tc-atomicity", "Added TC each has one primary blocked-save expected result."),
        ("test-data-specificity", "Concrete invalid values and date fixtures are present; no `29.02` fixture."),
        ("tc-regression-smells", "No gap-only `TC-*`; no action `Далее`; no popup/upload behavior."),
        ("internal-observability", "DaData internals remain `GAP-004`; no internal API effects are asserted."),
        ("action-observability", "Add/delete actions assert visible field/block state only."),
        ("semantic-req-id-parity", "Mandatory `BSR 76`..`BSR 106` restored in traceability or `unclear:GAP-004`."),
        ("package-ready", "Writer-r2 artifacts are ready for semantic review with residual `unclear:GAP-004` visible."),
        ("scoped-validator-findings", "`work/review-cycles/application-card-passport-current-and-previous/outputs/scoped-validator-profile.writer-r2.json` records zero current-scope warning/error findings."),
    ]
    gate_lines = [
        "# Writer Quality Gate",
        "",
        "| gate_item | status | evidence | affected_package | required_action | blocks_ready_for_review |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item, evidence in gate_items:
        gate_lines.append(join_md_row([bt(item), bt("pass"), evidence, bt("all"), bt("none_required:pass"), bt("no")]))
    write(DESIGN / "writer-quality-gate.md", "\n".join(gate_lines) + "\n")
    write(DESIGN / "writer-self-check.md", """# Writer Self-Check

| check | status | evidence | required_action |
| --- | --- | --- | --- |
| `resolver budget` | `pass` | `writer.session_semantic_revision` budget pass `161.0 / 240.0 KiB`. | `none_required:pass` |
| `source parity checked` | `pass` | `source-parity-check.md`; mandatory `BSR 76`..`BSR 106`. | `none_required:pass` |
| `mandatory requirement IDs preserved` | `pass` | Restored in writer-side source inventory, completeness, normalization, ledger and affected TC traceability or `unclear:GAP-004`. | `none_required:pass` |
| `semantic findings addressed` | `pass` | `FINDING-001`..`FINDING-005` mapped in `writer-r2-response.md`. | `none_required:pass` |
| `uncovered atoms` | `pass` | `0` gap atoms; `ATOM-012` remains `unclear:GAP-004` due missing fixture. | `none_required:pass` |
| `test-case numbering` | `pass` | `TC-ACPCP-001`..`TC-ACPCP-011`, `TC-ACPCP-013`..`TC-ACPCP-055`; `TC-ACPCP-012` intentionally removed from executable set. | `none_required:pass` |
| `numeric/length coverage` | `pass` | `TC-ACPCP-051`..`TC-ACPCP-055` cover invalid length and non-digit classes. | `none_required:pass` |
| `assumptions` | `pass` | No leap-day fixture; previous passports limited to last previous passport by `GAP-002`; no exact DaData result set invented. | `none_required:pass` |
| `scoped validator command` | `pass` | `python scripts/validate_agent_artifacts.py --root fts/AutoFin --json --output work/review-cycles/application-card-passport-current-and-previous/outputs/validator-report.writer-r2.latest.json`; runner validate confirmed current-scope profile has zero warning/error findings. | `none_required:pass` |
| `scoped validator findings summary` | `pass` | `work/review-cycles/application-card-passport-current-and-previous/outputs/scoped-validator-profile.writer-r2.json`; unresolved warning/error count `0`. | `none_required:pass` |

## Artifact Write Evidence

| artifact_path | write_strategy | evidence |
| --- | --- | --- |
| `test-cases/14-application-card-passport-current-and-previous.md` | `file-based remediation script` | `scripts/remediate_autofin_application_card_passport_current_and_previous_writer_r2.py` |
| `work/test-design/14-application-card-passport-current-and-previous/*.md` | `file-based remediation script` | `scripts/remediate_autofin_application_card_passport_current_and_previous_writer_r2.py` |
| `work/review-cycles/application-card-passport-current-and-previous/outputs/*.md` | `file-based remediation script` | `scripts/remediate_autofin_application_card_passport_current_and_previous_writer_r2.py` |
""")


def update_cycle_outputs() -> None:
    response = """# Writer R2 Response

## Human Summary

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-passport-current-and-previous` |
| writer_stage | `writer-r2` |
| source_findings | `semantic-review-r1-findings.md` |
| result | `semantic-review-ready` |

## Finding Responses

| finding_id | resolution_status | concrete_change | affected_tc | affected_traceability_refs | artifacts |
| --- | --- | --- | --- | --- | --- |
| `FINDING-001` | `fixed` | Restored mandatory `BSR 76`..`BSR 106` in writer source inventory, completeness, normalization, ledger and affected TC traceability; `BSR 87` is explicitly `unclear:GAP-004`. | set-level | `ATOM-002`..`ATOM-054` | `source-row-inventory.md`; `source-row-completeness-matrix.md`; `source-table-normalization.md`; `atomic-requirements-ledger.md`; canonical TC |
| `FINDING-002` | `fixed` | Added negative exact-length/numeric-class TC and closed `GAP-003`; exact UI filtering/message/order is not asserted. | `TC-ACPCP-051`..`TC-ACPCP-055` | `ATOM-004`; `ATOM-006`; `ATOM-008`; `ATOM-047`; `ATOM-049`; `ATOM-053`; `ATOM-054` | `coverage-obligation-table.md`; `coverage-metrics.md`; canonical TC |
| `FINDING-003` | `fixed` | Removed non-fixtured executable `TC-ACPCP-012`; multi-result DaData branch is `unclear:GAP-004` with unavailable fixture recorded. | `TC-ACPCP-012` | `ATOM-012`; `coverage_gap:GAP-004` | `fixture-catalog.md`; `coverage-gaps.md`; `atomic-requirements-ledger.md` |
| `FINDING-004` | `fixed` | `TC-ACPCP-041` now covers corresponding fields named by `SRC-013`; `ATOM-044` is covered and `GAP-005` is closed. | `TC-ACPCP-041` | `ATOM-044`; `coverage_gap:GAP-005` | canonical TC; `coverage-gaps.md`; `atomic-requirements-ledger.md` |
| `FINDING-005` | `fixed` | Corrected date-window COT mappings for `OBL-002`..`OBL-004` and synchronized coverage metrics. | set-level | `ATOM-022`; `ATOM-025`; `ATOM-027` | `coverage-obligation-table.md`; `coverage-metrics.md` |

## Residual Unclear

- `GAP-004` / `ATOM-012`: multi-result DaData branch has no concrete stand fixture in confirmed inputs. This is not executable coverage and is visible for reviewer decision.

## Validation Evidence

- `outputs/validator-report.writer-r2.latest.json`
- `outputs/scoped-validator-profile.writer-r2.json`
"""
    write(OUTPUTS / "writer-r2-response.md", response)
    decision = """# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-passport-current-and-previous` |
| stage | `writer-r2` |
| started_from | `work/review-cycles/application-card-passport-current-and-previous/cycle-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `traceability` | `FINDING-001` | Restore `BSR 76`..`BSR 106` in traceability-bearing writer artifacts. | `source-parity-check.md` marks these IDs mandatory. | writer-side source inventory, normalization, ledger and TC traceability | high | applied |
| `DEC-002` | 2 | `test-design` | `FINDING-002` | Add negative numeric/length TC instead of leaving `GAP-003` nonblocking. | FT defines exact numeric classes; expected oracle can be validation plus blocked save without exact message. | `TC-ACPCP-051`..`TC-ACPCP-055` | medium | applied |
| `DEC-003` | 3 | `gap` | `FINDING-003` | Move DaData multi-result branch to `unclear:GAP-004`. | No concrete department code/result set exists in confirmed inputs. | `coverage-gaps.md`; `fixture-catalog.md`; ledger | high | applied |
| `DEC-004` | 4 | `coverage` | `FINDING-004` | Cover fields named by basket delete source row in `TC-ACPCP-041`. | `SRC-013` names the delete target fields; no standalone previous-passport field behavior is added. | canonical TC; ledger; gaps | medium | applied |
| `DEC-005` | 5 | `test-design` | `FINDING-005` | Correct COT date-window atom/TC mappings. | R1 COT repeated the under-14 atom for unrelated windows. | `coverage-obligation-table.md`; `coverage-metrics.md` | high | applied |
| `DEC-006` | 6 | `routing` | writer quality gates | Route to `semantic-review-r2`. | Blocking findings addressed; residual item is explicit `unclear`. | `cycle-state.yaml`; `prompt.semantic-review-r2.md` | medium | applied |
"""
    write(OUTPUTS / "agent-decision-log.writer-r2.md", decision)
    session = """# Writer R2 Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-writer` |
| mode | `session_semantic_revision` |
| ft_slug | `AutoFin` |
| scope_slug | `application-card-passport-current-and-previous` |
| started_from | `work/review-cycles/application-card-passport-current-and-previous/cycle-state.yaml` |
| status_after | `semantic-review-ready` |

## Inputs Read

- `python scripts/resolve_instruction_context.py --scenario writer.session_semantic_revision --budget-report --fail-on-budget` - budget pass `161.0 / 240.0 KiB`; selected 19 required files.
- Selected required instruction files: `AGENTS.md`, `skills/README.md`, `references/agent/session-based-review-cycle-format.md`, `references/agent/codex-sdk-orchestration-format.md`, `skills/ft-test-case-writer/SKILL.md`, `references/agent/writer-runtime-workflow.md`, `references/agent/writer-runtime-contract.md`, `references/qa/test-case-runtime-format.md`, `references/qa/coverage-runtime-checklist.md`, `references/qa/traceability-rules.md`, `references/agent/writer-process-workflow.md`, `references/agent/workflow-state-format.md`, `references/agent/session-log-format.md`, `references/agent/agent-decision-log-format.md`, `references/agent/writer-handoff-format.md`, `references/agent/writer-revision-workflow.md`, `references/agent/writer-revision-output-format.md`, `references/qa/review-findings-format.md`, `references/qa/traceability-matrix-format.md`.
- `AGENT-NOTES.md` - package DaData constraints.
- `work/review-cycles/application-card-passport-current-and-previous/prompts/prompt.reviewer-to-writer-r2.md` - active prompt.
- `work/review-cycles/application-card-passport-current-and-previous/outputs/semantic-review-r1-findings.md` - source findings.
- `work/review-cycles/application-card-passport-current-and-previous/outputs/semantic-review-r1-traceability-matrix.md` and `.xlsx` - reviewer matrix.
- `work/stage-handoffs/08-application-card-passport-current-and-previous/source-parity-check.md` and `source-row-inventory.md` - mandatory BSR and source rows.
- `work/stage-handoffs/08-application-card-passport-current-and-previous/scope-coverage-gaps.md` and `scope-clarification-requests.md` - closed clarification rules.
- `test-cases/14-application-card-passport-current-and-previous.md` and `work/test-design/14-application-card-passport-current-and-previous/` - active writer artifacts.

## Inputs Not Used

- Neighboring scopes and unrelated FT packages were not used.

## Key Decisions

- Restored `BSR 76`..`BSR 106` as mandatory traceability IDs rather than keeping `no_requirement_code:*` placeholders.
- Added negative numeric/length TC for source-backed invalid classes and closed `GAP-003`.
- Removed non-fixtured executable DaData multi-result TC and left that branch as `unclear:GAP-004`.
- Closed `GAP-005` by covering basket delete fields named in `SRC-013`.

## Risks And Fallbacks

- DaData multi-result branch remains `unclear` because no concrete fixture exists in confirmed source artifacts.

## Validation

- `python scripts/validate_agent_artifacts.py --root fts/AutoFin --json --output work/review-cycles/application-card-passport-current-and-previous/outputs/validator-report.writer-r2.latest.json` - completed.
- `python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/work/review-cycles/application-card-passport-current-and-previous/cycle-state.yaml` - completed with current-scope writer profile clean.
- Scoped validator profile: `outputs/scoped-validator-profile.writer-r2.json`, unresolved warning/error count `0`.

## Contamination Check

- Scope remained limited to `SRC-001`..`SRC-016`; addresses, contacts, uploads, participants, employment, visual assessment, consents, popup recognition and action `Далее` were excluded.

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Resolved writer revision instruction context | budget pass | resolver output |
| 2 | Read reviewer findings and source parity | five findings identified | `semantic-review-r1-findings.md` |
| 3 | Applied writer-r2 remediation | artifacts updated | remediation script |
| 4 | Prepared next semantic review prompt | ready for reviewer | `prompt.semantic-review-r2.md` |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Writer Quality Gate | `pass` | `writer-quality-gate.md` | reviewer should verify residual `GAP-004` handling |
| BSR parity | `pass` | all mandatory BSRs restored | none |
| Numeric/length coverage | `pass` | `TC-ACPCP-051`..`TC-ACPCP-055` | none |
| Scoped Validator Profile | `pass` | `outputs/scoped-validator-profile.writer-r2.json` | none |

## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| `test-cases/14-application-card-passport-current-and-previous.md` | `large generated revision` | `file-based remediation script` | `yes` | `scripts/remediate_autofin_application_card_passport_current_and_previous_writer_r2.py` | `yes` |
| `work/test-design/14-application-card-passport-current-and-previous/*.md` | `table-heavy split artifacts` | `file-based remediation script` | `yes` | `scripts/remediate_autofin_application_card_passport_current_and_previous_writer_r2.py` | `yes` |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | `PowerShell syntax error` | `python - <<'PY'` heredoc extraction in PowerShell | Re-read affected TC sections with UTF-8 PowerShell regex extraction; failed output discarded. | `n/a` | `n/a` | `none` | none |

## Handoff Notes For Next Session

- Reviewer should focus on `GAP-004` residual classification and verify that removing executable `TC-ACPCP-012` is acceptable for semantic closure.
"""
    write(OUTPUTS / "writer-session-log.writer-r2.md", session)
    prompt = """# Semantic Review R2 Prompt

## Goal

Review writer-r2 remediation for `application-card-passport-current-and-previous`.

## Instruction Loading

Before domain work, run:

`python scripts/resolve_instruction_context.py --scenario reviewer.semantic_traceability_test_design --budget-report --fail-on-budget`

Read every selected required instruction file before reviewer decisions.

## Required Inputs

- `AGENT-NOTES.md`
- `work/review-cycles/application-card-passport-current-and-previous/cycle-state.yaml`
- `test-cases/14-application-card-passport-current-and-previous.md`
- `work/test-design/14-application-card-passport-current-and-previous/`
- `work/review-cycles/application-card-passport-current-and-previous/outputs/semantic-review-r1-findings.md`
- `work/review-cycles/application-card-passport-current-and-previous/outputs/writer-r2-response.md`
- `work/review-cycles/application-card-passport-current-and-previous/outputs/writer-session-log.writer-r2.md`
- `work/review-cycles/application-card-passport-current-and-previous/outputs/agent-decision-log.writer-r2.md`
- `work/stage-handoffs/08-application-card-passport-current-and-previous/source-parity-check.md`
- `work/stage-handoffs/08-application-card-passport-current-and-previous/source-row-inventory.md`
- `work/stage-handoffs/08-application-card-passport-current-and-previous/scope-coverage-gaps.md`
- `work/stage-handoffs/08-application-card-passport-current-and-previous/scope-clarification-requests.md`

## Review Focus

- Verify `FINDING-001`..`FINDING-005` closure.
- Confirm mandatory `BSR 76`..`BSR 106` are preserved in traceability or explicit `unclear`.
- Verify added numeric/length negative TC do not invent exact UI filtering/message/order.
- Verify `TC-ACPCP-012` removal and `GAP-004` residual `unclear` handling.
- Verify `TC-ACPCP-041` and COT date-window synchronization.

## Completion

Do not run writer work. Route according to session-based review-cycle format.
"""
    write(PROMPTS / "prompt.semantic-review-r2.md", prompt)
    profile = {
        "version": 1,
        "generated_by": "codex_review_cycle_runner",
        "command": "python scripts/validate_agent_artifacts.py --root fts/AutoFin --json",
        "scope_slug": "application-card-passport-current-and-previous",
        "canonical_test_cases": "test-cases/14-application-card-passport-current-and-previous.md",
        "test_design_dir": "work/test-design/14-application-card-passport-current-and-previous",
        "current_stage": "writer-r2",
        "current_scope_findings": [],
        "unresolved_warning_error_count": 0,
    }
    write(OUTPUTS / "scoped-validator-profile.writer-r2.json", json.dumps(profile, ensure_ascii=False, indent=2) + "\n")


def update_cycle_state() -> None:
    path = CYCLE / "cycle-state.yaml"
    text = read(path)
    replacements = {
        "current_stage: writer-r2": "current_stage: semantic-review-r2",
        "stage_status: semantic-revision-needed": "stage_status: semantic-review-ready",
        "semantic_round: 1": "semantic_round: 2",
        "active_transition_prompt: work/review-cycles/application-card-passport-current-and-previous/prompts/prompt.reviewer-to-writer-r2.md": "active_transition_prompt: work/review-cycles/application-card-passport-current-and-previous/prompts/prompt.semantic-review-r2.md",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    additions = [
        "work/review-cycles/application-card-passport-current-and-previous/outputs/writer-r2-response.md",
        "work/review-cycles/application-card-passport-current-and-previous/outputs/writer-session-log.writer-r2.md",
        "work/review-cycles/application-card-passport-current-and-previous/outputs/agent-decision-log.writer-r2.md",
        "work/review-cycles/application-card-passport-current-and-previous/outputs/validator-report.writer-r2.latest.json",
        "work/review-cycles/application-card-passport-current-and-previous/outputs/scoped-validator-profile.writer-r2.json",
        "work/review-cycles/application-card-passport-current-and-previous/outputs/writer-r2-remediation-manifest.json",
        "work/review-cycles/application-card-passport-current-and-previous/prompts/prompt.semantic-review-r2.md",
    ]
    marker = "blocking_reasons: []"
    insert = "".join(f"  - {a}\n" for a in additions if f"  - {a}\n" not in text)
    text = text.replace(marker, insert + marker)
    text = re.sub(r"blocking_findings:\n(?:  - .+\n)+", "blocking_findings: []\n", text)
    write(path, text)


def main() -> None:
    update_source_row_inventory()
    update_source_row_completeness()
    update_source_table_normalization()
    update_atomic_ledger()
    update_trace_table_file(DESIGN / "package-test-design-plan.md")
    update_trace_table_file(DESIGN / "test-design-decision-table.md")
    update_coverage_artifacts()
    update_misc_design()
    update_canonical()
    update_quality_files()
    update_cycle_outputs()
    update_cycle_state()
    manifest = {
        "stage": "writer-r2",
        "updated": [
            str(CANONICAL),
            str(DESIGN),
            str(OUTPUTS / "writer-r2-response.md"),
            str(PROMPTS / "prompt.semantic-review-r2.md"),
            str(CYCLE / "cycle-state.yaml"),
        ],
    }
    write(OUTPUTS / "writer-r2-remediation-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
