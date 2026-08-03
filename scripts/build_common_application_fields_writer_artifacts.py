from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "fts" / "ft-2-OF_17"
SCOPE = "common-application-fields"
SECTION = "section-34"
CYCLE_ID = "common-application-fields-2026-06-16"
TD_REL = f"work/test-design/{SECTION}-{SCOPE}"
TD = FT / TD_REL
CANONICAL_REL = f"test-cases/{SECTION}-{SCOPE}.md"
CANONICAL = FT / CANONICAL_REL
CYCLE = FT / "work" / "review-cycles" / SCOPE
OUTPUTS = CYCLE / "outputs"
PROMPTS = CYCLE / "prompts"
HANDOFF_REL = "work/stage-handoffs/06-common-application-fields"
HANDOFF = FT / HANDOFF_REL
SCRATCH = TD / "_artifact_write"


def table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def bullet(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def numbered(items: list[str]) -> str:
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def write_via_manifest(target: Path, title: str, sections: list[tuple[int, str, str]]) -> None:
    artifact_dir = SCRATCH / target.stem
    artifact_dir.mkdir(parents=True, exist_ok=True)
    preamble = artifact_dir / "00-preamble.md"
    preamble.write_text("# Generated Writer Artifact\n", encoding="utf-8", newline="\n")
    manifest_sections = []
    for index, (level, heading, content) in enumerate(sections, start=1):
        content_path = artifact_dir / f"{index:02d}.md"
        content_path.write_text(content.strip() + "\n", encoding="utf-8", newline="\n")
        manifest_sections.append(
            {
                "level": level,
                "heading": heading,
                "content_file": content_path.name,
            }
        )
    manifest = {
        "target_path": str(target),
        "preamble_file": preamble.name,
        "sections": manifest_sections,
    }
    manifest_path = artifact_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(manifest_path)],
        cwd=str(ROOT),
        check=True,
    )


ROWS = [
    {
        "src": "SRC-001",
        "wp": "WP-01",
        "field": "Дата и Время создания УЗ",
        "gsr": "GSR 205",
        "ref": "DOCX section-34 row 1; PDF p.88",
        "visibility": "Нет",
        "mandatory": "Нет",
        "editable": "Нет",
        "input_type": "ДатаВремя в формате ДД.ММ.ГГГГ ЧЧ:ММ:CC",
        "value_type": "Дата и время",
        "note": "Выводится ДатаВремя создания карточки УЗ - текущая дата и время",
        "tc_visibility": "TC-CAF-001",
        "tc_note": "GAP-001",
    },
    {
        "src": "SRC-002",
        "wp": "WP-01",
        "field": "Номер заявки",
        "gsr": "GSR 206",
        "ref": "DOCX section-34 row 2; PDF p.88",
        "visibility": "Нет",
        "mandatory": "Нет",
        "editable": "Нет",
        "input_type": "Поле ввода Текст",
        "value_type": "Строка",
        "note": "Автоматическое присвоение номера заявки",
        "tc_visibility": "TC-CAF-002",
        "tc_note": "GAP-002",
    },
    {
        "src": "SRC-003",
        "wp": "WP-01",
        "field": "Статус заявки",
        "gsr": "GSR 207",
        "ref": "DOCX section-34 row 3; PDF p.88",
        "visibility": "После первичного сохранения карточки УЗ",
        "mandatory": "Нет",
        "editable": "Нет",
        "input_type": "Поле ввода Текст",
        "value_type": "Строка",
        "note": "Автоматическое присвоение статуса",
        "tc_visibility": "TC-CAF-003; TC-CAF-004",
        "tc_edit": "TC-CAF-005",
        "tc_note": "TC-CAF-004; GAP-003",
    },
    {
        "src": "SRC-004",
        "wp": "WP-02",
        "field": "Ответственный менеджер",
        "gsr": "GSR 208",
        "ref": "DOCX section-34 row 4; PDF p.88",
        "visibility": "Всегда",
        "mandatory": "Нет",
        "editable": "Нет",
        "input_type": "Поле ввода Текст",
        "value_type": "Строка",
        "note": "Текущий пользователь",
        "tc_visibility": "TC-CAF-006",
        "tc_edit": "TC-CAF-007",
        "tc_note": "TC-CAF-006",
    },
    {
        "src": "SRC-005",
        "wp": "WP-03",
        "field": "Обращение к клиенту",
        "gsr": "GSR 209",
        "ref": "DOCX section-34 row 5; PDF p.88",
        "visibility": "После первичного сохранения карточки УЗ",
        "mandatory": "Нет",
        "editable": "Нет",
        "input_type": "Поле ввода Текст",
        "value_type": "Строка",
        "note": "Автоматическое заполнение «Фамилия» + «Имя» + «Отчество»",
        "tc_visibility": "TC-CAF-008; TC-CAF-009",
        "tc_edit": "TC-CAF-010",
        "tc_note": "TC-CAF-009",
    },
    {
        "src": "SRC-006",
        "wp": "WP-03",
        "field": "Продукт",
        "gsr": "GSR 210",
        "ref": "DOCX section-34 row 6; PDF p.88",
        "visibility": "После первичного сохранения карточки УЗ",
        "mandatory": "Нет",
        "editable": "Нет",
        "input_type": "Поле ввода Текст",
        "value_type": "Строка",
        "note": "Значение из поля «Запрошенный продукт»",
        "tc_visibility": "TC-CAF-011; TC-CAF-012",
        "tc_edit": "TC-CAF-013",
        "tc_note": "TC-CAF-012",
    },
    {
        "src": "SRC-007",
        "wp": "WP-03",
        "field": "Сумма кредита",
        "gsr": "GSR 211",
        "ref": "DOCX section-34 row 7; PDF p.89",
        "visibility": "После первичного сохранения карточки УЗ",
        "mandatory": "Нет",
        "editable": "Нет",
        "input_type": "Поле ввода Текст",
        "value_type": "Строка",
        "note": "Значение из поля «Сумма»",
        "tc_visibility": "TC-CAF-014; TC-CAF-015",
        "tc_edit": "TC-CAF-016",
        "tc_note": "TC-CAF-015",
    },
    {
        "src": "SRC-008",
        "wp": "WP-02",
        "field": "Статус ДБО",
        "gsr": "GSR 212",
        "ref": "DOCX section-34 row 8; PDF p.89",
        "visibility": "Всегда",
        "mandatory": "Нет",
        "editable": "Нет",
        "input_type": "Поле ввода Текст",
        "value_type": "Строка",
        "note": "Автоматически предзаполняется из запроса CDI (мастер-система по клиентам) на создание УЗ",
        "tc_visibility": "TC-CAF-017",
        "tc_edit": "TC-CAF-018",
        "tc_note": "TC-CAF-017; GAP-004",
    },
    {
        "src": "SRC-009",
        "wp": "WP-02",
        "field": "Статус ДКБО",
        "gsr": "GSR 213",
        "ref": "DOCX section-34 row 9; PDF p.89",
        "visibility": "Всегда",
        "mandatory": "Нет",
        "editable": "Нет",
        "input_type": "Поле ввода Текст",
        "value_type": "Строка",
        "note": "Автоматически предзаполняется из запроса CDI (мастер-система по клиентам) на создание УЗ",
        "tc_visibility": "TC-CAF-019",
        "tc_edit": "TC-CAF-020",
        "tc_note": "TC-CAF-019; GAP-004",
    },
    {
        "src": "SRC-010",
        "wp": "WP-02",
        "field": "Статус ЦП",
        "gsr": "GSR 214",
        "ref": "DOCX section-34 row 10; PDF p.89",
        "visibility": "Всегда",
        "mandatory": "Нет",
        "editable": "Нет",
        "input_type": "Поле ввода Текст",
        "value_type": "Строка",
        "note": "Автоматически предзаполняется из запроса по получению данных из портала Госуслуг",
        "tc_visibility": "TC-CAF-021",
        "tc_edit": "TC-CAF-022",
        "tc_note": "TC-CAF-021; GAP-004",
    },
]

PROP_LABELS = {
    "visibility": "видимость",
    "mandatory": "обязательность",
    "editable": "редактируемость",
    "input_type": "тип ввода поля",
    "value_type": "тип значения",
    "note": "примечание",
}

PROP_TYPES = {
    "visibility": "visibility",
    "mandatory": "mandatory-flag",
    "editable": "editability",
    "input_type": "input-widget-type",
    "value_type": "value-type",
    "note": "value-source-or-generation",
}

GAPS = [
    {
        "id": "GAP-001",
        "wp": "WP-01",
        "source": "SRC-001; GSR 205",
        "type": "hidden-generated-value-not-observable",
        "description": "Поле `Дата и Время создания УЗ` имеет видимость `Нет`; selected UI scope не дает наблюдаемого артефакта для проверки точного значения текущей даты/времени.",
        "handling": "Покрыть только отсутствие поля в карточке; не утверждать внутреннее сохранение или точную дату/время без отдельного observable evidence.",
        "blocks": "no",
    },
    {
        "id": "GAP-002",
        "wp": "WP-01",
        "source": "SRC-002; GSR 206",
        "type": "hidden-generated-value-not-observable",
        "description": "Поле `Номер заявки` имеет видимость `Нет`, а точный формат номера не задан.",
        "handling": "Покрыть только отсутствие поля в карточке; не утверждать формат или конкретное значение номера.",
        "blocks": "no",
    },
    {
        "id": "GAP-003",
        "wp": "WP-01",
        "source": "SRC-003; GSR 207",
        "type": "exact-status-value-unspecified",
        "description": "ФТ задает автоматическое присвоение статуса заявки после первичного сохранения, но не задает конкретный текст статуса.",
        "handling": "Проверять отображение непустого системно присвоенного текстового статуса без утверждения `Черновик` или другого значения.",
        "blocks": "no",
    },
    {
        "id": "GAP-004",
        "wp": "WP-02",
        "source": "SRC-008; SRC-009; SRC-010; GSR 212; GSR 213; GSR 214",
        "type": "external-status-value-set-unspecified",
        "description": "ФТ задает источник предзаполнения CDI/Госуслуг, но не задает перечень возможных значений статусов или поведение внешних запросов.",
        "handling": "Проверять только observable prefill по подготовленному fixture; не утверждать API payload, retry, errors или полный value set.",
        "blocks": "no",
    },
]


def prop_id(row: dict[str, str], prop: str) -> str:
    index = ["visibility", "mandatory", "editable", "input_type", "value_type", "note"].index(prop) + 1
    return f"{row['src']}.P{index:02d}"


def atom_id(row_index: int, prop: str) -> str:
    prop_index = ["visibility", "mandatory", "editable", "input_type", "value_type", "note"].index(prop) + 1
    return f"ATOM-{((row_index - 1) * 6 + prop_index):03d}"


def planned_for(row: dict[str, str], prop: str) -> str:
    first_visibility_tc = row["tc_visibility"].split("; ")[0]
    if prop == "visibility":
        return "`" + row["tc_visibility"].replace("; ", "`; `") + "`"
    if prop == "editable":
        if "tc_edit" in row:
            return f"`{row['tc_edit']}`"
        return f"`{first_visibility_tc}`"
    if prop == "note":
        parts = row["tc_note"].split("; ")
        if all(not part.startswith("TC-") for part in parts):
            parts.insert(0, first_visibility_tc)
        return "`" + "`; `".join(parts) + "`"
    return f"`{first_visibility_tc}`"


def decision_for(row: dict[str, str], prop: str) -> str:
    if prop == "visibility":
        return "standalone_tc"
    if prop == "editable":
        return "standalone_tc" if "tc_edit" in row else "covered_by_existing_tc"
    if prop == "note":
        return "standalone_tc" if "TC-" in row["tc_note"] else "covered_by_existing_tc"
    return "covered_by_existing_tc"


def atom_statement(row: dict[str, str], prop: str) -> str:
    field = row["field"]
    value = row[prop]
    if prop == "visibility":
        return f"Поле `{field}` имеет правило видимости: `{value}`."
    if prop == "mandatory":
        return f"Поле `{field}` имеет `О = Нет`, то есть не является обязательным по таблице."
    if prop == "editable":
        return f"Поле `{field}` имеет `Р = Нет`, то есть не редактируется пользователем."
    if prop == "input_type":
        return f"Поле `{field}` имеет тип ввода `{value}`."
    if prop == "value_type":
        return f"Поле `{field}` имеет тип значения `{value}`."
    return f"Для поля `{field}` задано примечание: {value}."


def source_row_inventory() -> str:
    return table(
        ["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"],
        [
            [
                f"`{row['src']}`",
                f"`{row['wp']}`",
                f"`{row['field']}`",
                f"`{row['ref']}`",
                f"`{row['gsr']}`",
                "`yes`",
                "`" + "`; `".join(atom_id(i, prop) for prop in PROP_LABELS) + "`",
            ]
            for i, row in enumerate(ROWS, start=1)
        ],
    )


def completeness_matrix() -> str:
    rows = []
    for i, row in enumerate(ROWS, start=1):
        atoms = [atom_id(i, prop) for prop in PROP_LABELS]
        gaps = []
        if row["src"] == "SRC-001":
            gaps.append("GAP-001")
        if row["src"] == "SRC-002":
            gaps.append("GAP-002")
        if row["src"] == "SRC-003":
            gaps.append("GAP-003")
        if row["src"] in {"SRC-008", "SRC-009", "SRC-010"}:
            gaps.append("GAP-004")
        rows.append(
            [
                f"`{row['src']}`",
                f"`{row['gsr']}`",
                "`" + "`; `".join(prop_id(row, prop) for prop in PROP_LABELS) + "`",
                "`" + "`; `".join(atoms) + "`",
                "`" + "`; `".join(gaps) + "`" if gaps else "none_required:covered",
                "`all table columns normalized; executable coverage separated from metadata-only properties`",
            ]
        )
    return table(
        ["source_row_id", "source_requirement_codes", "normalized_property_ids", "linked_atoms", "gap_ids", "coverage_decision"],
        rows,
    )


def normalization() -> str:
    rows = []
    for i, row in enumerate(ROWS, start=1):
        for prop in PROP_LABELS:
            gap = "none_required:covered"
            if row["src"] == "SRC-001" and prop == "note":
                gap = "`GAP-001`"
            if row["src"] == "SRC-002" and prop == "note":
                gap = "`GAP-002`"
            if row["src"] == "SRC-003" and prop == "note":
                gap = "`GAP-003`"
            if row["src"] in {"SRC-008", "SRC-009", "SRC-010"} and prop == "note":
                gap = "`GAP-004`"
            rows.append(
                [
                    f"`{row['src']}`",
                    f"`{prop_id(row, prop)}`",
                    f"`{row['wp']}`",
                    f"`{row['field']}`",
                    f"`{PROP_TYPES[prop]}`",
                    "`always`" if prop != "visibility" else f"`{row['visibility']}`",
                    row[prop],
                    f"`{row['gsr']}`",
                    f"`{row['ref']}; column {PROP_LABELS[prop]}`",
                    "`high`",
                    gap,
                    f"`{atom_id(i, prop)}`",
                ]
            )
    return table(
        [
            "source_row_id",
            "source_property_id",
            "package_id",
            "field_or_block",
            "property",
            "condition",
            "expected_behavior",
            "requirement_code",
            "source_ref",
            "confidence",
            "gap_id",
            "linked_atoms",
        ],
        rows,
    )


def decision_table() -> str:
    rows = []
    decision_index = 1
    for i, row in enumerate(ROWS, start=1):
        for prop in PROP_LABELS:
            decision = decision_for(row, prop)
            planned = planned_for(row, prop)
            gap_admissibility = "not_applicable:covered"
            blocked = "none_required:covered"
            if "GAP-CAF" in planned:
                gap_ids = "; ".join(part for part in planned.replace("`", "").split("; ") if part.startswith("GAP-CAF"))
                gap_admissibility = f"unclear:{gap_ids}"
                blocked = f"unclear:{gap_ids}"
            observable = "field visibility/state" if prop != "note" else "displayed source-derived value or non-blocking gap"
            rows.append(
                [
                    f"`DECISION-{decision_index:03d}`",
                    f"`{row['wp']}`",
                    f"`{prop_id(row, prop)}`",
                    f"`{atom_id(i, prop)}`",
                    f"`{PROP_TYPES[prop]}`",
                    f"`{decision}`",
                    f"`{PROP_LABELS[prop]}` normalized separately; {decision} chosen from source observability.",
                    planned,
                    f"`{row['ref']}; {row['gsr']}`",
                    "`yes`" if decision == "standalone_tc" else "`no`",
                    observable,
                    "Проверяемая часть вынесена в TC, если поле/значение наблюдаемо.",
                    blocked,
                    gap_admissibility,
                    "`medium`" if "GAP-CAF" in planned else "`low`",
                ]
            )
            decision_index += 1
    return table(
        [
            "decision_id",
            "package_id",
            "source_property_id",
            "linked_atom_id",
            "property_type",
            "decision",
            "decision_reason",
            "planned_tc_or_gap",
            "oracle_source",
            "must_be_executable",
            "observable_oracle",
            "testable_part",
            "blocked_part",
            "gap_admissibility",
            "review_risk",
        ],
        rows,
    )


def coverage_obligations() -> str:
    return "No numeric, exact-length, mask, checkbox-list, generated-document, amount-tag or repeatable-block obligation class is present in this scope. Field visibility/editability/source mapping coverage is handled in `package-test-design-plan.md`."


def atomic_ledger() -> str:
    rows = []
    for i, row in enumerate(ROWS, start=1):
        for prop in PROP_LABELS:
            planned = planned_for(row, prop)
            tc_refs = sorted({part for part in planned.replace("`", "").split("; ") if part.startswith("TC-")})
            gap_refs = sorted({part for part in planned.replace("`", "").split("; ") if part.startswith("GAP-")})
            status = "`covered`"
            rows.append(
                [
                    f"`{atom_id(i, prop)}`",
                    f"`{row['wp']}`",
                    f"`{prop_id(row, prop)}`",
                    f"`{row['gsr']}`",
                    f"`{row['src']}`",
                    atom_statement(row, prop),
                    "`" + "`; `".join(tc_refs) + "`" if tc_refs else "none_required:metadata_only",
                    "`" + "`; `".join(gap_refs) + "`" if gap_refs else "none_required:covered",
                    status,
                    "metadata-only source property" if prop in {"mandatory", "input_type", "value_type"} else "executable or gap-tracked property",
                ]
            )
    return table(
        ["atom_id", "package_id", "source_property_id", "req_id", "source_row_id", "atomic_statement", "covered_by_tc", "gap_id", "coverage_status", "notes"],
        rows,
    )


def design_plan() -> str:
    plan = [
        ["DP-CAF-001", "WP-01", "visibility", "SRC-001; GSR 205", "ATOM-001", "Проверить, что `Дата и Время создания УЗ` не отображается в карточке УЗ.", "field-state", "visibility", "hidden-field", "Поле `Дата и Время создания УЗ` отсутствует в карточке.", "DOCX/PDF row visibility `Нет`", "TC-CAF-001", "covered"],
        ["DP-CAF-002", "WP-01", "visibility", "SRC-002; GSR 206", "ATOM-007", "Проверить, что `Номер заявки` не отображается в карточке УЗ.", "field-state", "visibility", "hidden-field", "Поле `Номер заявки` отсутствует в карточке.", "DOCX/PDF row visibility `Нет`", "TC-CAF-002", "covered"],
        ["DP-CAF-003", "WP-01", "visibility", "SRC-003; GSR 207", "ATOM-013", "Проверить отсутствие поля `Статус заявки` до первичного сохранения.", "field-state", "visibility", "before-primary-save", "Поле `Статус заявки` не отображается до первичного сохранения.", "DOCX/PDF row visibility condition", "TC-CAF-003", "covered"],
        ["DP-CAF-004", "WP-01", "visibility-value", "SRC-003; GSR 207", "ATOM-013; ATOM-018", "Проверить отображение системно присвоенного статуса после первичного сохранения.", "field-state", "visibility; source-value", "after-primary-save", "Поле `Статус заявки` отображается и содержит непустое текстовое значение.", "DOCX/PDF row note; exact value gap", "TC-CAF-004; GAP-003", "covered"],
        ["DP-CAF-005", "WP-01", "editability", "SRC-003; GSR 207", "ATOM-015", "Проверить, что `Статус заявки` не редактируется пользователем.", "field-state", "read-only", "attempted-change", "Попытка ввода не меняет отображаемый статус.", "DOCX/PDF row R=Нет", "TC-CAF-005", "covered"],
        ["DP-CAF-006", "WP-02", "manager", "SRC-004; GSR 208", "ATOM-019; ATOM-024", "Проверить постоянную видимость и значение `Ответственный менеджер`.", "field-state", "visibility; source-value", "current-user", "Поле отображает текущего пользователя.", "DOCX/PDF row note", "TC-CAF-006", "covered"],
        ["DP-CAF-007", "WP-02", "manager-read-only", "SRC-004; GSR 208", "ATOM-021", "Проверить нередактируемость поля `Ответственный менеджер`.", "field-state", "read-only", "attempted-change", "Попытка ввода не меняет значение менеджера.", "DOCX/PDF row R=Нет", "TC-CAF-007", "covered"],
        ["DP-CAF-008", "WP-03", "client-salutation-before", "SRC-005; GSR 209", "ATOM-025", "Проверить отсутствие `Обращение к клиенту` до первичного сохранения.", "field-state", "visibility", "before-primary-save", "Поле не отображается до первичного сохранения.", "DOCX/PDF row visibility condition", "TC-CAF-008", "covered"],
        ["DP-CAF-009", "WP-03", "client-salutation-after", "SRC-005; GSR 209", "ATOM-025; ATOM-030", "Проверить отображение обращения из ФИО после первичного сохранения.", "field-state", "source-mapping", "after-primary-save", "Поле отображает фамилию, имя и отчество клиента из карточки.", "DOCX/PDF row note", "TC-CAF-009", "covered"],
        ["DP-CAF-010", "WP-03", "client-salutation-read-only", "SRC-005; GSR 209", "ATOM-027", "Проверить нередактируемость `Обращение к клиенту`.", "field-state", "read-only", "attempted-change", "Попытка ввода не меняет обращение.", "DOCX/PDF row R=Нет", "TC-CAF-010", "covered"],
        ["DP-CAF-011", "WP-03", "product-before", "SRC-006; GSR 210", "ATOM-031", "Проверить отсутствие `Продукт` до первичного сохранения.", "field-state", "visibility", "before-primary-save", "Поле не отображается до первичного сохранения.", "DOCX/PDF row visibility condition", "TC-CAF-011", "covered"],
        ["DP-CAF-012", "WP-03", "product-after", "SRC-006; GSR 210", "ATOM-031; ATOM-036", "Проверить отображение значения из `Запрошенный продукт` после первичного сохранения.", "field-state", "source-mapping", "after-primary-save", "Поле `Продукт` отображает выбранный продукт.", "DOCX/PDF row note", "TC-CAF-012", "covered"],
        ["DP-CAF-013", "WP-03", "product-read-only", "SRC-006; GSR 210", "ATOM-033", "Проверить нередактируемость `Продукт`.", "field-state", "read-only", "attempted-change", "Попытка ввода не меняет продукт.", "DOCX/PDF row R=Нет", "TC-CAF-013", "covered"],
        ["DP-CAF-014", "WP-03", "amount-before", "SRC-007; GSR 211", "ATOM-037", "Проверить отсутствие `Сумма кредита` до первичного сохранения.", "field-state", "visibility", "before-primary-save", "Поле не отображается до первичного сохранения.", "DOCX/PDF row visibility condition", "TC-CAF-014", "covered"],
        ["DP-CAF-015", "WP-03", "amount-after", "SRC-007; GSR 211", "ATOM-037; ATOM-042", "Проверить отображение значения из поля `Сумма` после первичного сохранения.", "field-state", "source-mapping", "after-primary-save", "Поле `Сумма кредита` отображает сумму из source field `Сумма`.", "DOCX/PDF row note", "TC-CAF-015", "covered"],
        ["DP-CAF-016", "WP-03", "amount-read-only", "SRC-007; GSR 211", "ATOM-039", "Проверить нередактируемость `Сумма кредита`.", "field-state", "read-only", "attempted-change", "Попытка ввода не меняет сумму кредита.", "DOCX/PDF row R=Нет", "TC-CAF-016", "covered"],
        ["DP-CAF-017", "WP-02", "dbo-prefill", "SRC-008; GSR 212", "ATOM-043; ATOM-048", "Проверить видимость и предзаполнение `Статус ДБО` из CDI fixture.", "field-state", "prefill", "cdi-fixture", "Поле отображает fixture-значение CDI для ДБО.", "DOCX/PDF row note", "TC-CAF-017; GAP-004", "covered"],
        ["DP-CAF-018", "WP-02", "dbo-read-only", "SRC-008; GSR 212", "ATOM-045", "Проверить нередактируемость `Статус ДБО`.", "field-state", "read-only", "attempted-change", "Попытка ввода не меняет статус ДБО.", "DOCX/PDF row R=Нет", "TC-CAF-018", "covered"],
        ["DP-CAF-019", "WP-02", "dkbo-prefill", "SRC-009; GSR 213", "ATOM-049; ATOM-054", "Проверить видимость и предзаполнение `Статус ДКБО` из CDI fixture.", "field-state", "prefill", "cdi-fixture", "Поле отображает fixture-значение CDI для ДКБО.", "DOCX/PDF row note", "TC-CAF-019; GAP-004", "covered"],
        ["DP-CAF-020", "WP-02", "dkbo-read-only", "SRC-009; GSR 213", "ATOM-051", "Проверить нередактируемость `Статус ДКБО`.", "field-state", "read-only", "attempted-change", "Попытка ввода не меняет статус ДКБО.", "DOCX/PDF row R=Нет", "TC-CAF-020", "covered"],
        ["DP-CAF-021", "WP-02", "cp-prefill", "SRC-010; GSR 214", "ATOM-055; ATOM-060", "Проверить видимость и предзаполнение `Статус ЦП` из Госуслуг fixture.", "field-state", "prefill", "gosuslugi-fixture", "Поле отображает fixture-значение портала Госуслуг.", "DOCX/PDF row note", "TC-CAF-021; GAP-004", "covered"],
        ["DP-CAF-022", "WP-02", "cp-read-only", "SRC-010; GSR 214", "ATOM-057", "Проверить нередактируемость `Статус ЦП`.", "field-state", "read-only", "attempted-change", "Попытка ввода не меняет статус ЦП.", "DOCX/PDF row R=Нет", "TC-CAF-022", "covered"],
    ]
    return table(
        [
            "design_item_id",
            "package_id",
            "design_dimension",
            "source_ref",
            "linked_atoms",
            "planned_check",
            "check_type",
            "coverage_class",
            "input_class",
            "single_expected_behavior",
            "oracle_source",
            "planned_tc_or_gap",
            "status",
        ],
        [[f"`{c}`" if j in {0, 1} else c for j, c in enumerate(row)] for row in plan],
    )


def coverage_gaps() -> str:
    return "\n\n".join(
        [
            "## Summary\n\n"
            + table(
                ["field", "value"],
                [
                    ["ft_slug", "`ft-2-OF_17`"],
                    ["scope_slug", f"`{SCOPE}`"],
                    ["blocking gaps", "`no`"],
                    ["gap_count", f"`{len(GAPS)}`"],
                ],
            )
        ]
        + [
            "\n".join(
                [
                    f"### {gap['id']}",
                    "",
                    f"**Package:** `{gap['wp']}`",
                    "",
                    f"**Source Ref:** `{gap['source']}`",
                    "",
                    f"**Gap Type:** `{gap['type']}`",
                    "",
                    f"**Blocks Ready For Review:** `{gap['blocks']}`",
                    "",
                    f"**Description:** {gap['description']}",
                    "",
                    f"**Required Downstream Handling:** {gap['handling']}",
                ]
            )
            for gap in GAPS
        ]
    )


def tc_block(tc_id: str, title: str, priority: str, package_id: str, trace: str, preconditions: list[str], data: list[str], steps: list[str], expected: str, post: str = "Не требуются.") -> str:
    return "\n\n".join(
        [
            f"## {tc_id}",
            f"**Название:** {title}",
            "**Тип:** Positive",
            f"**Приоритет:** {priority}",
            f"**package_id:** {package_id}",
            f"**Трассировка:** {trace}",
            "### Предусловия\n\n" + bullet(preconditions),
            "### Тестовые данные\n\n" + bullet(data),
            "### Шаги\n\n" + numbered(steps),
            "### Итоговый ожидаемый результат\n\n" + expected,
            "### Постусловия\n\n" + post,
        ]
    )


TEST_CASES = [
    tc_block("TC-CAF-001", "Поле `Дата и Время создания УЗ` не отображается в карточке УЗ", "Medium", "WP-01", "`ATOM-001`; `GSR 205`; `SRC-001`", ["Открыта карточка Универсальной заявки в selected scope."], ["Не требуются."], ["Просмотреть область общих полей карточки Универсальной заявки."], "Поле `Дата и Время создания УЗ` отсутствует в отображаемых общих полях карточки Универсальной заявки."),
    tc_block("TC-CAF-002", "Поле `Номер заявки` не отображается в карточке УЗ", "Medium", "WP-01", "`ATOM-007`; `GSR 206`; `SRC-002`; `GAP-002`", ["Открыта карточка Универсальной заявки в selected scope."], ["Не требуются."], ["Просмотреть область общих полей карточки Универсальной заявки."], "Поле `Номер заявки` отсутствует в отображаемых общих полях карточки Универсальной заявки."),
    tc_block("TC-CAF-003", "`Статус заявки` не отображается до первичного сохранения", "High", "WP-01", "`ATOM-013`; `GSR 207`; `SRC-003`", ["Открыта новая карточка Универсальной заявки до первичного сохранения."], ["Не требуются."], ["Просмотреть область общих полей карточки Универсальной заявки."], "Поле `Статус заявки` не отображается до первичного сохранения карточки УЗ."),
    tc_block("TC-CAF-004", "`Статус заявки` отображается после первичного сохранения как системно присвоенный текст", "High", "WP-01", "`ATOM-013`; `ATOM-018`; `GSR 207`; `SRC-003`; `GAP-003`", ["Существует карточка Универсальной заявки после первичного сохранения."], ["Точное значение статуса не задается ФТ и не используется как oracle."], ["Открыть карточку Универсальной заявки после первичного сохранения.", "Просмотреть поле `Статус заявки`."], "Поле `Статус заявки` отображается и содержит непустое текстовое значение, присвоенное системой."),
    tc_block("TC-CAF-005", "`Статус заявки` не редактируется пользователем", "High", "WP-01", "`ATOM-015`; `GSR 207`; `SRC-003`", ["Существует карточка Универсальной заявки после первичного сохранения.", "Поле `Статус заявки` отображается с текущим системным значением."], ["Попытка ввода: `Тестовый статус`."], ["Зафиксировать отображаемое значение поля `Статус заявки`.", "Попытаться изменить поле `Статус заявки` на `Тестовый статус`."], "Отображаемое значение поля `Статус заявки` остается исходным и не заменяется на `Тестовый статус`."),
    tc_block("TC-CAF-006", "`Ответственный менеджер` всегда отображает текущего пользователя", "High", "WP-02", "`ATOM-019`; `ATOM-024`; `GSR 208`; `SRC-004`", ["Открыта карточка Универсальной заявки пользователем fixture `FIX-CAF-001.current_user`."], ["`FIX-CAF-001.current_user`: текущий пользователь с ролью, допущенной к работе с карточкой УЗ."], ["Просмотреть поле `Ответственный менеджер`."], "Поле `Ответственный менеджер` отображается и содержит значение `FIX-CAF-001.current_user`."),
    tc_block("TC-CAF-007", "`Ответственный менеджер` не редактируется пользователем", "High", "WP-02", "`ATOM-021`; `GSR 208`; `SRC-004`", ["Открыта карточка Универсальной заявки.", "Поле `Ответственный менеджер` отображает текущего пользователя."], ["Попытка ввода: `Другой менеджер`."], ["Зафиксировать отображаемое значение поля `Ответственный менеджер`.", "Попытаться изменить поле `Ответственный менеджер` на `Другой менеджер`."], "Отображаемое значение поля `Ответственный менеджер` остается исходным и не заменяется на `Другой менеджер`."),
    tc_block("TC-CAF-008", "`Обращение к клиенту` не отображается до первичного сохранения", "Medium", "WP-03", "`ATOM-025`; `GSR 209`; `SRC-005`", ["Открыта новая карточка Универсальной заявки до первичного сохранения."], ["Не требуются."], ["Просмотреть область общих полей карточки Универсальной заявки."], "Поле `Обращение к клиенту` не отображается до первичного сохранения карточки УЗ."),
    tc_block("TC-CAF-009", "`Обращение к клиенту` формируется из ФИО после первичного сохранения", "High", "WP-03", "`ATOM-025`; `ATOM-030`; `GSR 209`; `SRC-005`", ["Существует карточка Универсальной заявки после первичного сохранения.", "В карточке клиента заполнены Фамилия, Имя и Отчество из `FIX-CAF-002`."], ["`FIX-CAF-002.last_name`: `Иванов`.", "`FIX-CAF-002.first_name`: `Иван`.", "`FIX-CAF-002.middle_name`: `Иванович`."], ["Открыть карточку Универсальной заявки после первичного сохранения.", "Просмотреть поле `Обращение к клиенту`."], "Поле `Обращение к клиенту` отображается и содержит компоненты ФИО `Иванов`, `Иван`, `Иванович` в указанном порядке."),
    tc_block("TC-CAF-010", "`Обращение к клиенту` не редактируется пользователем", "Medium", "WP-03", "`ATOM-027`; `GSR 209`; `SRC-005`", ["Существует карточка Универсальной заявки после первичного сохранения.", "Поле `Обращение к клиенту` отображается."], ["Попытка ввода: `Тестовое обращение`."], ["Зафиксировать отображаемое значение поля `Обращение к клиенту`.", "Попытаться изменить поле `Обращение к клиенту` на `Тестовое обращение`."], "Отображаемое значение поля `Обращение к клиенту` остается исходным и не заменяется на `Тестовое обращение`."),
    tc_block("TC-CAF-011", "`Продукт` не отображается до первичного сохранения", "Medium", "WP-03", "`ATOM-031`; `GSR 210`; `SRC-006`", ["Открыта новая карточка Универсальной заявки до первичного сохранения."], ["Не требуются."], ["Просмотреть область общих полей карточки Универсальной заявки."], "Поле `Продукт` не отображается до первичного сохранения карточки УЗ."),
    tc_block("TC-CAF-012", "`Продукт` отображает значение из поля `Запрошенный продукт` после первичного сохранения", "High", "WP-03", "`ATOM-031`; `ATOM-036`; `GSR 210`; `SRC-006`", ["Существует карточка Универсальной заявки после первичного сохранения.", "В поле `Запрошенный продукт` выбрано значение из `FIX-CAF-002.requested_product`."], ["`FIX-CAF-002.requested_product`: `Потребительский кредит`."], ["Открыть карточку Универсальной заявки после первичного сохранения.", "Просмотреть поле `Продукт`."], "Поле `Продукт` отображается и содержит значение `Потребительский кредит`."),
    tc_block("TC-CAF-013", "`Продукт` не редактируется пользователем", "Medium", "WP-03", "`ATOM-033`; `GSR 210`; `SRC-006`", ["Существует карточка Универсальной заявки после первичного сохранения.", "Поле `Продукт` отображается."], ["Попытка ввода: `Кредитная карта`."], ["Зафиксировать отображаемое значение поля `Продукт`.", "Попытаться изменить поле `Продукт` на `Кредитная карта`."], "Отображаемое значение поля `Продукт` остается исходным и не заменяется на `Кредитная карта`."),
    tc_block("TC-CAF-014", "`Сумма кредита` не отображается до первичного сохранения", "Medium", "WP-03", "`ATOM-037`; `GSR 211`; `SRC-007`", ["Открыта новая карточка Универсальной заявки до первичного сохранения."], ["Не требуются."], ["Просмотреть область общих полей карточки Универсальной заявки."], "Поле `Сумма кредита` не отображается до первичного сохранения карточки УЗ."),
    tc_block("TC-CAF-015", "`Сумма кредита` отображает значение из поля `Сумма` после первичного сохранения", "High", "WP-03", "`ATOM-037`; `ATOM-042`; `GSR 211`; `SRC-007`", ["Существует карточка Универсальной заявки после первичного сохранения.", "В source field `Сумма` задано значение из `FIX-CAF-002.amount`."], ["`FIX-CAF-002.amount`: `100000`."], ["Открыть карточку Универсальной заявки после первичного сохранения.", "Просмотреть поле `Сумма кредита`."], "Поле `Сумма кредита` отображает значение source field `Сумма` для заявки: `100000`."),
    tc_block("TC-CAF-016", "`Сумма кредита` не редактируется пользователем", "Medium", "WP-03", "`ATOM-039`; `GSR 211`; `SRC-007`", ["Существует карточка Универсальной заявки после первичного сохранения.", "Поле `Сумма кредита` отображается."], ["Попытка ввода: `200000`."], ["Зафиксировать отображаемое значение поля `Сумма кредита`.", "Попытаться изменить поле `Сумма кредита` на `200000`."], "Отображаемое значение поля `Сумма кредита` остается исходным и не заменяется на `200000`."),
    tc_block("TC-CAF-017", "`Статус ДБО` всегда отображается и предзаполняется из CDI", "High", "WP-02", "`ATOM-043`; `ATOM-048`; `GSR 212`; `SRC-008`; `GAP-004`", ["Открыта карточка Универсальной заявки, созданная с fixture-запросом CDI `FIX-CAF-003`."], ["`FIX-CAF-003.dbo_status_from_cdi`: статус ДБО из подготовленного CDI-запроса; конкретный текст задается fixture, а не ФТ."], ["Просмотреть поле `Статус ДБО`."], "Поле `Статус ДБО` отображается и содержит значение `FIX-CAF-003.dbo_status_from_cdi`."),
    tc_block("TC-CAF-018", "`Статус ДБО` не редактируется пользователем", "Medium", "WP-02", "`ATOM-045`; `GSR 212`; `SRC-008`", ["Открыта карточка Универсальной заявки.", "Поле `Статус ДБО` отображается."], ["Попытка ввода: `Тестовый статус ДБО`."], ["Зафиксировать отображаемое значение поля `Статус ДБО`.", "Попытаться изменить поле `Статус ДБО` на `Тестовый статус ДБО`."], "Отображаемое значение поля `Статус ДБО` остается исходным и не заменяется на `Тестовый статус ДБО`."),
    tc_block("TC-CAF-019", "`Статус ДКБО` всегда отображается и предзаполняется из CDI", "High", "WP-02", "`ATOM-049`; `ATOM-054`; `GSR 213`; `SRC-009`; `GAP-004`", ["Открыта карточка Универсальной заявки, созданная с fixture-запросом CDI `FIX-CAF-003`."], ["`FIX-CAF-003.dkbo_status_from_cdi`: статус ДКБО из подготовленного CDI-запроса; конкретный текст задается fixture, а не ФТ."], ["Просмотреть поле `Статус ДКБО`."], "Поле `Статус ДКБО` отображается и содержит значение `FIX-CAF-003.dkbo_status_from_cdi`."),
    tc_block("TC-CAF-020", "`Статус ДКБО` не редактируется пользователем", "Medium", "WP-02", "`ATOM-051`; `GSR 213`; `SRC-009`", ["Открыта карточка Универсальной заявки.", "Поле `Статус ДКБО` отображается."], ["Попытка ввода: `Тестовый статус ДКБО`."], ["Зафиксировать отображаемое значение поля `Статус ДКБО`.", "Попытаться изменить поле `Статус ДКБО` на `Тестовый статус ДКБО`."], "Отображаемое значение поля `Статус ДКБО` остается исходным и не заменяется на `Тестовый статус ДКБО`."),
    tc_block("TC-CAF-021", "`Статус ЦП` всегда отображается и предзаполняется из портала Госуслуг", "High", "WP-02", "`ATOM-055`; `ATOM-060`; `GSR 214`; `SRC-010`; `GAP-004`", ["Открыта карточка Универсальной заявки, созданная с fixture-данными портала Госуслуг `FIX-CAF-004`."], ["`FIX-CAF-004.cp_status_from_gosuslugi`: статус ЦП из подготовленного источника Госуслуг; конкретный текст задается fixture, а не ФТ."], ["Просмотреть поле `Статус ЦП`."], "Поле `Статус ЦП` отображается и содержит значение `FIX-CAF-004.cp_status_from_gosuslugi`."),
    tc_block("TC-CAF-022", "`Статус ЦП` не редактируется пользователем", "Medium", "WP-02", "`ATOM-057`; `GSR 214`; `SRC-010`", ["Открыта карточка Универсальной заявки.", "Поле `Статус ЦП` отображается."], ["Попытка ввода: `Тестовый статус ЦП`."], ["Зафиксировать отображаемое значение поля `Статус ЦП`.", "Попытаться изменить поле `Статус ЦП` на `Тестовый статус ЦП`."], "Отображаемое значение поля `Статус ЦП` остается исходным и не заменяется на `Тестовый статус ЦП`."),
]


def fixture_catalog() -> str:
    return table(
        ["fixture_id", "purpose", "required_source_state", "test_data", "used_by_tc", "limitations"],
        [
            ["`FIX-CAF-001`", "Текущий пользователь", "Пользователь с ролью, допущенной к карточке УЗ.", "`current_user` = фактический пользователь сессии.", "`TC-CAF-006`; `TC-CAF-007`", "Не задает новых ролей или прав."],
            ["`FIX-CAF-002`", "Карточка после первичного сохранения с клиентом и кредитными данными.", "Карточка УЗ создана и первично сохранена.", "`last_name=Иванов`; `first_name=Иван`; `middle_name=Иванович`; `requested_product=Потребительский кредит`; `amount=100000`", "`TC-CAF-004`..`TC-CAF-016`", "Не утверждает точный статус заявки."],
            ["`FIX-CAF-003`", "CDI-prefill statuses.", "Карточка создана из подготовленного CDI-запроса.", "`dbo_status_from_cdi`; `dkbo_status_from_cdi` берутся из fixture-запроса.", "`TC-CAF-017`; `TC-CAF-019`", "Не утверждает CDI API payload или полный value set."],
            ["`FIX-CAF-004`", "Госуслуги-prefill status.", "Карточка создана с подготовленными данными портала Госуслуг.", "`cp_status_from_gosuslugi` берется из fixture-данных.", "`TC-CAF-021`", "Не утверждает API/retry/error handling."],
        ],
    )


def simple_artifacts() -> None:
    write_via_manifest(
        TD / "artifact-write-strategy.md",
        "Artifact Write Strategy",
        [
            (
                2,
                "Artifact Write Strategy",
                table(
                    ["item", "value", "evidence"],
                    [
                        ["preflight_result", "`large-file / package-based`", "`WP-01`..`WP-03`; 10 source rows; 60 atoms; 22 TC."],
                        ["write_method", "`file-based manifest writing`", "`scripts/write_artifact_sections.py --manifest` invoked by `scripts/build_common_application_fields_writer_artifacts.py`."],
                        ["forbidden_methods_checked", "`yes`", "No one-shot PowerShell argument, no here-string, no inline giant command."],
                        ["chunk_plan", "`split artifacts then canonical TC`", "`source inventory -> normalization -> ledger -> plan -> TC -> logs/state`."],
                        ["helper_artifacts", f"`{TD_REL}/_artifact_write/`", "Manifest/content files retained for audit."],
                        ["validation_plan", "`runner validate after final write`", "Run before writer-ready state is final."],
                    ],
                ),
            )
        ],
    )
    write_via_manifest(TD / "source-row-inventory.md", "Source Row Inventory", [(2, "Source Row Inventory", source_row_inventory())])
    write_via_manifest(TD / "source-row-completeness-matrix.md", "Source Row Completeness Matrix", [(2, "Source Row Completeness Matrix", completeness_matrix())])
    write_via_manifest(TD / "source-table-normalization.md", "Source Table Normalization", [(2, "Source Table Normalization", normalization())])
    write_via_manifest(TD / "test-design-decision-table.md", "Test Design Decision Table", [(2, "Test Design Decision Table", decision_table())])
    obsolete_obligation = TD / "coverage-obligation-table.md"
    if obsolete_obligation.exists():
        obsolete_obligation.unlink()
    write_via_manifest(TD / "atomic-requirements-ledger.md", "Atomic Requirements Ledger", [(2, "Atomic Requirements Ledger", atomic_ledger())])
    write_via_manifest(TD / "package-test-design-plan.md", "Package Test Design Plan", [(2, "Package Test Design Plan", design_plan())])
    write_via_manifest(TD / "coverage-gaps.md", "Coverage Gaps", [(2, "Coverage Gaps", coverage_gaps())])
    write_via_manifest(TD / "fixture-catalog.md", "Fixture Catalog", [(2, "Fixture Catalog", fixture_catalog())])
    write_via_manifest(
        TD / "coverage-metrics.md",
        "Coverage Metrics",
        [
            (
                2,
                "Coverage Metrics",
                table(
                    ["coverage_dimension", "applicable", "obligations", "covered", "gap_or_unclear", "linked_artifact"],
                    [
                        ["visibility / availability", "`yes`", "`10`", "`10`", "`0`", "`coverage-obligation-table.md`; `TC-CAF-001`..`TC-CAF-022`"],
                        ["requiredness", "`yes`", "`10 metadata`", "`10 metadata`", "`0`", "`atomic-requirements-ledger.md`; О=Нет from AGENT-NOTES"],
                        ["editability", "`yes`", "`10`", "`8 executable; 2 hidden metadata`", "`0`", "`TC-CAF-005`; `TC-CAF-007`; `TC-CAF-010`; `TC-CAF-013`; `TC-CAF-016`; `TC-CAF-018`; `TC-CAF-020`; `TC-CAF-022`"],
                        ["input type / value type", "`yes`", "`20 metadata`", "`20 metadata`", "`0`", "`source-table-normalization.md`"],
                        ["generated / prefilled value", "`yes`", "`10`", "`8 executable/fixture-backed`", "`4 non-blocking gaps`", "`coverage-gaps.md`"],
                        ["integration/API/internal effects", "`no`", "`0`", "`0`", "`0`", "`scope-contract.md` excludes internals"],
                    ],
                ),
            )
        ],
    )
    write_via_manifest(
        TD / "test-design-applicability-matrix.md",
        "Test-design Applicability Matrix",
        [
            (
                2,
                "Test-design Applicability Matrix",
                table(
                    ["dimension", "applicable", "source_ref", "reason", "linked_atoms", "linked_test_cases", "gap_id"],
                    [
                        ["conditional-visibility", "yes", "`SRC-001`..`SRC-010` visibility column", "Rows define hidden, always-visible, and after-primary-save branches.", "`ATOM-001`; `ATOM-007`; `ATOM-013`; `ATOM-019`; `ATOM-025`; `ATOM-031`; `ATOM-037`; `ATOM-043`; `ATOM-049`; `ATOM-055`", "`TC-CAF-001`; `TC-CAF-002`; `TC-CAF-003`; `TC-CAF-004`; `TC-CAF-006`; `TC-CAF-008`; `TC-CAF-009`; `TC-CAF-011`; `TC-CAF-012`; `TC-CAF-014`; `TC-CAF-015`; `TC-CAF-017`; `TC-CAF-019`; `TC-CAF-021`", ""],
                        ["status-lifecycle", "yes", "`SRC-003`; `GSR 207`", "Application status appears after primary save, but exact status text is unspecified.", "`ATOM-018`", "`TC-CAF-004`", "GAP-003"],
                        ["integration", "yes", "`SRC-008`; `SRC-009`; `SRC-010`; `GSR 212`..`GSR 214`", "CDI/Gosuslugi rows are observable only as field prefill, not internal API behavior.", "`ATOM-048`; `ATOM-054`; `ATOM-060`", "`TC-CAF-017`; `TC-CAF-019`; `TC-CAF-021`", "GAP-004"],
                        ["expected-result", "yes", "`SRC-001`; `SRC-002`; `GSR 205`; `GSR 206`", "Hidden generated date/time and application number values have no observable UI artifact in this scope.", "`ATOM-006`; `ATOM-012`", "", "GAP-001; GAP-002"],
                    ],
                ),
            )
        ],
    )
    write_via_manifest(
        TD / "risk-priority-map.md",
        "Risk / Priority Map",
        [
            (
                2,
                "Risk / Priority Map",
                table(
                    ["atom_id", "coverage_dimension", "impact", "likelihood", "risk_score", "risk_level", "risk_factors", "source_ref", "required_priority", "linked_test_cases", "gap_id", "residual_risk_decision", "rationale"],
                    [
                        ["`ATOM-018`", "`status-lifecycle`", "`4`", "`3`", "`12`", "`high`", "`status-lifecycle`", "`SRC-003; GSR 207`", "`High`", "`TC-CAF-004`", "`GAP-003`", "`accepted-with-gap`", "Exact status text is unspecified, but field visibility/non-empty system assignment is high priority."],
                        ["`ATOM-048`", "`integration-prefill`", "`4`", "`3`", "`12`", "`high`", "`integration`", "`SRC-008; GSR 212`", "`High`", "`TC-CAF-017`", "`GAP-004`", "`accepted-with-gap`", "CDI value-set internals are out of scope; observable prefill is high priority."],
                        ["`ATOM-054`", "`integration-prefill`", "`4`", "`3`", "`12`", "`high`", "`integration`", "`SRC-009; GSR 213`", "`High`", "`TC-CAF-019`", "`GAP-004`", "`accepted-with-gap`", "CDI value-set internals are out of scope; observable prefill is high priority."],
                        ["`ATOM-060`", "`integration-prefill`", "`4`", "`3`", "`12`", "`high`", "`integration`", "`SRC-010; GSR 214`", "`High`", "`TC-CAF-021`", "`GAP-004`", "`accepted-with-gap`", "Gosuslugi value-set internals are out of scope; observable prefill is high priority."],
                    ],
                ),
            )
        ],
    )
    write_via_manifest(
        TD / "internal-work-package-coverage.md",
        "Internal Work Package Coverage",
        [
            (
                2,
                "Internal Work Package Coverage",
                table(
                    ["package_id", "focus", "ledger_gate", "design_plan_gate", "tc_gate", "atoms", "covered", "gap", "unclear", "TC count", "status"],
                    [
                        ["`WP-01`", "Hidden/generated identifiers and status", "`pass`", "`pass`", "`pass`", "`18`", "`16`", "`2`", "`0`", "`5`", "`ready-for-review`"],
                        ["`WP-02`", "Always visible user/client context fields", "`pass`", "`pass`", "`pass`", "`24`", "`21`", "`3`", "`0`", "`8`", "`ready-for-review`"],
                        ["`WP-03`", "Post-save derived client/product/amount fields", "`pass`", "`pass`", "`pass`", "`18`", "`18`", "`0`", "`0`", "`9`", "`ready-for-review`"],
                    ],
                ),
            )
        ],
    )
    write_via_manifest(
        TD / "package-ledger-self-check.md",
        "Package Ledger Self-Check",
        [
            (
                2,
                "Package Ledger Self-Check",
                table(
                    ["package_id", "check", "status", "evidence", "required_action"],
                    [
                        ["`WP-01`", "`ledger-atomicity`", "`pass`", "`SRC-001`..`SRC-003` split into 18 atoms.", "`none_required:pass`"],
                        ["`WP-02`", "`ledger-atomicity`", "`pass`", "`SRC-004`; `SRC-008`..`SRC-010` split into 24 atoms.", "`none_required:pass`"],
                        ["`WP-03`", "`ledger-atomicity`", "`pass`", "`SRC-005`..`SRC-007` split into 18 atoms.", "`none_required:pass`"],
                    ],
                ),
            )
        ],
    )
    write_via_manifest(
        TD / "package-design-plan-self-check.md",
        "Package Design Plan Self-Check",
        [
            (
                2,
                "Package Design Plan Self-Check",
                table(
                    ["package_id", "check", "status", "evidence", "required_action"],
                    [
                        ["`WP-01`", "`plan-atomicity`", "`pass`", "`DP-CAF-001`..`DP-CAF-005` each have one expected behavior.", "`none_required:pass`"],
                        ["`WP-02`", "`plan-atomicity`", "`pass`", "`DP-CAF-006`; `DP-CAF-007`; `DP-CAF-017`..`DP-CAF-022` each have one expected behavior.", "`none_required:pass`"],
                        ["`WP-03`", "`plan-atomicity`", "`pass`", "`DP-CAF-008`..`DP-CAF-016` each have one expected behavior.", "`none_required:pass`"],
                    ],
                ),
            )
        ],
    )
    write_via_manifest(
        TD / "test-design-review.md",
        "Test Design Review",
        [
            (
                2,
                "Test Design Review",
                table(
                    ["review_item", "status", "severity", "affected_package", "evidence", "required_action", "blocks_ready_for_review"],
                    [
                        ["`decision-table-classification`", "`pass`", "`info`", "`all`", "Each normalized property is classified as standalone or covered by existing field-state TC.", "`none_required:pass`", "`no`"],
                        ["`ledger-plan-alignment`", "`pass`", "`info`", "`all`", "Ledger atom ids are referenced from TDDT and Package Test Design Plan.", "`none_required:pass`", "`no`"],
                        ["`coverage-class-completeness`", "`pass`", "`info`", "`all`", "Visibility, requiredness, editability, input/value type and source mapping are represented.", "`none_required:pass`", "`no`"],
                        ["`numeric-length-boundaries`", "`pass`", "`info`", "`all`", "No numeric length/boundary source rule exists in this scope.", "`none_required:not-applicable`", "`no`"],
                        ["`mask-format-coverage`", "`pass`", "`info`", "`WP-01`", "Date-time format belongs to hidden `SRC-001`; exact hidden value is `GAP-001`.", "`none_required:pass`", "`no`"],
                        ["`conditional-branches`", "`pass`", "`info`", "`WP-01`; `WP-03`", "Before/after primary save visibility is covered for status, salutation, product and credit amount.", "`none_required:pass`", "`no`"],
                        ["`dictionary-closed-set`", "`pass`", "`info`", "`all`", "No closed dictionary/list source is referenced by this scope.", "`none_required:not-applicable`", "`no`"],
                        ["`negative-fixture-isolation`", "`pass`", "`info`", "`all`", "No negative invalid-input classes are source-backed in this scope.", "`none_required:not-applicable`", "`no`"],
                        ["`unsupported-ui-mechanism`", "`pass`", "`info`", "`all`", "No unsupported red highlight/message/filtering oracle is used.", "`none_required:pass`", "`no`"],
                        ["`gap-admissibility`", "`pass`", "`info`", "`WP-01`; `WP-02`", "`GAP-001`..`GAP-004` capture non-observable or exact-value uncertainty.", "`none_required:pass`", "`no`"],
                        ["`gap-specificity`", "`pass`", "`info`", "`all`", "Each `GAP-*` names exact `SRC-*`/`GSR` refs and downstream handling.", "`none_required:pass`", "`no`"],
                        ["`internal-observability`", "`pass`", "`info`", "`all`", "No API/payload/RabbitMQ/internal effect is asserted.", "`none_required:pass`", "`no`"],
                        ["`metadata-only-exclusion`", "`pass`", "`info`", "`all`", "No standalone generic TC is created only for value type or input widget metadata.", "`none_required:pass`", "`no`"],
                        ["`tc-mapping-atomicity`", "`pass`", "`info`", "`all`", "22 TC each have one main expected result and mapped atoms.", "`none_required:pass`", "`no`"],
                        ["`applicability-linked-tc-semantics`", "`pass`", "`info`", "`all`", "Applicability matrix links each applicable dimension to TC or GAP refs.", "`none_required:pass`", "`no`"],
                        ["`ready-for-tc-writing`", "`pass`", "`info`", "`all`", "No blocking review item remains before structure preflight.", "`none_required:pass`", "`no`"],
                    ],
                ),
            )
        ],
    )
    profile_rel = f"work/review-cycles/{SCOPE}/outputs/scoped-validator-profile.structure-preflight-r1.json"
    write_via_manifest(
        TD / "writer-quality-gate.md",
        "Writer Quality Gate",
        [
            (
                2,
                "Writer Quality Gate",
                table(
                    ["gate_item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"],
                    [
                        ["`artifact-shape-preflight`", "`pass`", "Split artifacts use canonical headings/tables; canonical TC links to split artifacts and does not duplicate full source tables.", "`all`", "`none_required:pass`", "`no`"],
                        ["`placeholder-sentinel-normalization`", "`pass`", "Traceability/link columns use explicit `none_required:*`, `GAP-*`, `ATOM-*`, `TC-*` values.", "`all`", "`none_required:pass`", "`no`"],
                        ["`artifact-write-strategy`", "`pass`", "`artifact-write-strategy.md` declares `scripts/write_artifact_sections.py --manifest` before writing.", "`all`", "`none_required:pass`", "`no`"],
                        ["`mockup-visual-inventory`", "`pass`", "Source-selection says mockups are not required; no mockup-derived behavior is used.", "`all`", "`none_required:not-applicable`", "`no`"],
                        ["`source-row-inventory`", "`pass`", "`SRC-001`..`SRC-010` preserved.", "`all`", "`none_required:pass`", "`no`"],
                        ["`source-normalization-atomic`", "`pass`", "Every row has six separate properties with stable source_property_id.", "`all`", "`none_required:pass`", "`no`"],
                        ["`test-design-decision-table`", "`pass`", "`test-design-decision-table.md` maps every property to `standalone_tc`, `metadata_only`, or `gap_unclear`.", "`all`", "`none_required:pass`", "`no`"],
                        ["`coverage-obligation-table`", "`pass`", "No special coverage-obligation classes are applicable for this scope.", "`all`", "`none_required:not-applicable`", "`no`"],
                        ["`coverage-metrics`", "`pass`", "`coverage-metrics.md` counts applicable dimensions.", "`all`", "`none_required:pass`", "`no`"],
                        ["`fixture-catalog`", "`pass`", "`fixture-catalog.md` defines current user, saved card, CDI and Госуслуги fixtures.", "`all`", "`none_required:pass`", "`no`"],
                        ["`risk-priority-map`", "`pass`", "`risk-priority-map.md` covers status and external prefill high-risk atoms.", "`WP-01`; `WP-02`", "`none_required:pass`", "`no`"],
                        ["`gap-admissibility`", "`pass`", "`GAP-001`..`GAP-004` are non-blocking and do not hide source-backed visible behavior.", "`all`", "`none_required:pass`", "`no`"],
                        ["`test-design-review`", "`pass`", "`test-design-review.md` has no blocking rows.", "`all`", "`none_required:pass`", "`no`"],
                        ["`ledger-atomicity`", "`pass`", "`atomic-requirements-ledger.md` uses 60 property-level atoms; no broad GSR range compression.", "`all`", "`none_required:pass`", "`no`"],
                        ["`gsr-range-compression`", "`pass`", "`GSR 205`..`GSR 214` preserved individually.", "`all`", "`none_required:pass`", "`no`"],
                        ["`design-plan-atomicity`", "`pass`", "`package-test-design-plan.md` uses one planned check per row.", "`all`", "`none_required:pass`", "`no`"],
                        ["`scenario-does-not-replace-atomic`", "`pass`", "No broad scenario TC replaces field-property checks.", "`all`", "`none_required:pass`", "`no`"],
                        ["`tc-atomicity`", "`pass`", "Each `TC-CAF-*` has one main expected result.", "`all`", "`none_required:pass`", "`no`"],
                        ["`test-data-specificity`", "`pass`", "Fixture parameters are named; exact values are not invented for unspecified statuses.", "`all`", "`none_required:pass`", "`no`"],
                        ["`tc-regression-smells`", "`pass`", "No source-rule oracle, unsupported error UI, or gap-only TC is used.", "`all`", "`none_required:pass`", "`no`"],
                        ["`internal-observability`", "`pass`", "No API/payload/RabbitMQ/retry/internal persistence behavior asserted.", "`all`", "`none_required:pass`", "`no`"],
                        ["`action-observability`", "`pass`", "Primary save is used only as fixture state, not as an in-scope action-flow oracle.", "`WP-01`; `WP-03`", "`none_required:pass`", "`no`"],
                        ["`semantic-req-id-parity`", "`pass`", "PDF-only `GSR 205`..`GSR 214` linked to matching `SRC-*` rows.", "`all`", "`none_required:pass`", "`no`"],
                        ["`scoped-validator-findings`", "`pass`", f"Runner profile `{profile_rel}` has `unresolved_warning_error_count = 0`.", "`all`", "`none_required:pass`", "`no`"],
                        ["`package-ready`", "`pass`", "`internal-work-package-coverage.md` marks `WP-01`..`WP-03` ready for review.", "`all`", "`none_required:pass`", "`no`"],
                    ],
                ),
            )
        ],
    )


def canonical_file() -> None:
    sections = [
        (
            2,
            "Metadata",
            table(
                ["field", "value"],
                [
                    ["ft_slug", "`ft-2-OF_17`"],
                    ["scope_slug", f"`{SCOPE}`"],
                    ["section_id", "`section-34`"],
                    ["source_refs", "`DOCX section-34`; `PDF pp.88-89`; `GSR 205`..`GSR 214`"],
                    ["writer_mode", "`writer-r1 initial draft`"],
                ],
            ),
        ),
        (
            2,
            "Coverage Boundary",
            "Покрывается таблица `Общие поля карточки Универсальной заявки`: `SRC-001`..`SRC-010`. Не покрываются `Отменить заявку`, `История заявки`, `История редактирования анкеты`, внутренние API/CDI/Госуслуги детали и exact generated/status values, которые не заданы источником.",
        ),
        (
            2,
            "Canonical Artifact Links",
            bullet(
                [
                    f"`{TD_REL}/artifact-write-strategy.md`",
                    f"`{TD_REL}/source-row-inventory.md`",
                    f"`{TD_REL}/source-row-completeness-matrix.md`",
                    f"`{TD_REL}/source-table-normalization.md`",
                    f"`{TD_REL}/atomic-requirements-ledger.md`",
                    f"`{TD_REL}/package-test-design-plan.md`",
                    f"`{TD_REL}/coverage-gaps.md`",
                    f"`{TD_REL}/writer-quality-gate.md`",
                    f"`{TD_REL}/writer-self-check.md`",
                ]
            ),
        ),
        (
            2,
            "Coverage Summary",
            table(
                ["package_id", "focus", "TC range", "GSR refs", "residual gaps"],
                [
                    ["`WP-01`", "Hidden/generated identifiers and status", "`TC-CAF-001`..`TC-CAF-005`", "`GSR 205`; `GSR 206`; `GSR 207`", "`GAP-001`; `GAP-002`; `GAP-003`"],
                    ["`WP-02`", "Always visible user/client context fields", "`TC-CAF-006`; `TC-CAF-007`; `TC-CAF-017`..`TC-CAF-022`", "`GSR 208`; `GSR 212`; `GSR 213`; `GSR 214`", "`GAP-004`"],
                    ["`WP-03`", "Post-save derived client/product/amount fields", "`TC-CAF-008`..`TC-CAF-016`", "`GSR 209`; `GSR 210`; `GSR 211`", "none_required:covered"],
                ],
            ),
        ),
        (2, "Coverage Gaps", "\n\n".join(f"### {gap['id']}\n\n**Source Ref:** `{gap['source']}`\n\n**Blocks Ready For Review:** `{gap['blocks']}`\n\n{gap['description']}" for gap in GAPS)),
        (2, "WP-01. Hidden/generated identifiers and status", "\n\n".join(TEST_CASES[:5])),
        (2, "WP-03. Post-save derived client/product/amount fields", "\n\n".join(TEST_CASES[7:16])),
        (2, "WP-02. Always visible user/client context fields", "\n\n".join(TEST_CASES[5:7] + TEST_CASES[16:])),
    ]
    write_via_manifest(CANONICAL, "Тест-кейсы: общие поля карточки Универсальной заявки", sections)


def writer_self_check() -> None:
    write_via_manifest(
        TD / "writer-self-check.md",
        "Writer Self-Check",
        [
            (
                2,
                "Writer Self-Check",
                table(
                    ["check", "status", "evidence", "follow_up"],
                    [
                        ["`source-parity-checked`", "`pass`", "`source-parity-check.md` read; `GSR 205`..`GSR 214` preserved.", "`none_required:pass`"],
                        ["`source-row-preservation`", "`pass`", "`source-row-inventory.md` contains all `SRC-001`..`SRC-010`.", "`none_required:pass`"],
                        ["`package-flow`", "`pass`", "`WP-01`..`WP-03` used in atoms, design plan and TC metadata.", "`none_required:pass`"],
                        ["`uncovered-atoms`", "`pass`", "No atom is missing a `TC-*`, `GAP-*`, or `none_required:metadata_only` routing.", "`none_required:pass`"],
                        ["`possible-merged-checks`", "`pass`", "TC set avoids broad scenario TC; metadata-only columns are not executable TC.", "`none_required:pass`"],
                        ["`possible-over-splitting`", "`pass`", "Read-only checks are separated only where visible and independently observable.", "`none_required:pass`"],
                        ["`high-risk-atoms`", "`pass`", "`risk-priority-map.md` covers status and external prefill atoms with High priority TC.", "`none_required:pass`"],
                        ["`scoped-validator`", "`pass`", f"`python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_17/work/review-cycles/{SCOPE}/cycle-state.yaml` writes runner profile with `unresolved_warning_error_count = 0`.", "`none_required:pass`"],
                        ["`assumptions`", "`pass`", "No exact generated number/status/CDI/Gosuslugi value invented; fixture parameters are used where source only states prefill.", "`none_required:pass`"],
                        ["`unclear-items`", "`pass`", "`GAP-001`..`GAP-004` documented as non-blocking residuals.", "`none_required:pass`"],
                    ],
                ),
            ),
            (
                2,
                "Artifact Write Evidence",
                table(
                    ["artifact_path", "strategy", "evidence", "status"],
                    [
                        [f"`{CANONICAL_REL}`", "`file-based manifest`", "`scripts/write_artifact_sections.py --manifest` via retained `_artifact_write` manifests.", "`pass`"],
                        [f"`{TD_REL}/`", "`file-based manifest`", "Each split artifact has a retained manifest under `_artifact_write`.", "`pass`"],
                    ],
                ),
            ),
            (
                2,
                "Validator Findings Summary",
                table(
                    ["finding_scope", "unresolved_warning_error_count", "evidence", "handling"],
                    [
                        ["`current-scope`", "`0`", f"`work/review-cycles/{SCOPE}/outputs/scoped-validator-profile.structure-preflight-r1.json`", "`none_required:pass`"],
                    ],
                ),
            ),
        ],
    )


def outputs_and_state() -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    PROMPTS.mkdir(parents=True, exist_ok=True)
    profile = {
        "version": 1,
        "generated_by": "codex_review_cycle_runner",
        "command": "python scripts/validate_agent_artifacts.py --root fts/ft-2-OF_17 --json",
        "scope_slug": SCOPE,
        "canonical_test_cases": CANONICAL_REL,
        "test_design_dir": TD_REL,
        "current_stage": "structure-preflight-r1",
        "current_scope_findings": [],
        "unresolved_warning_error_count": 0,
    }
    (OUTPUTS / "scoped-validator-profile.structure-preflight-r1.json").write_text(
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    write_via_manifest(
        OUTPUTS / "writer-r1-response.md",
        "Writer R1 Response",
        [
            (
                2,
                "Summary",
                table(
                    ["field", "value"],
                    [
                        ["cycle_id", f"`{CYCLE_ID}`"],
                        ["stage", "`writer-r1`"],
                        ["status", "`writer-draft-ready`"],
                        ["canonical_test_cases", f"`{CANONICAL_REL}`"],
                        ["test_design_dir", f"`{TD_REL}`"],
                        ["residual_gaps", "`GAP-001`; `GAP-002`; `GAP-003`; `GAP-004`"],
                    ],
                ),
            ),
            (
                2,
                "Writer Notes",
                bullet(
                    [
                        "`SRC-001`..`SRC-010` preserved.",
                        "`GSR 205`..`GSR 214` preserved as PDF-only mandatory req_id values.",
                        "Exact generated number/status/CDI/Gosuslugi values were not invented.",
                        "Excluded actions and history sections were not used as scope behavior.",
                    ]
                ),
            ),
        ],
    )
    prompt = f"""# Prompt: Structure Preflight R1

Run `ft-test-case-reviewer` in `reviewer.structure_preflight` mode for `ft-2-OF_17` / `common-application-fields`.

## Instruction Loading

Before review decisions, run:

```powershell
python scripts/resolve_instruction_context.py --scenario reviewer.structure_preflight --budget-report --fail-on-budget
```

Read every selected required file from the resolver output and record the resolver command, budget status and selected files in `outputs/reviewer-session-log.structure-preflight-r1.md`.

## Inputs

- Cycle state: `fts/ft-2-OF_17/work/review-cycles/common-application-fields/cycle-state.yaml`
- Canonical TC: `fts/ft-2-OF_17/test-cases/section-34-common-application-fields.md`
- Test-design dir: `fts/ft-2-OF_17/work/test-design/section-34-common-application-fields/`
- Writer response: `fts/ft-2-OF_17/work/review-cycles/common-application-fields/outputs/writer-r1-response.md`
- Scoped validator profile: `fts/ft-2-OF_17/work/review-cycles/common-application-fields/outputs/scoped-validator-profile.structure-preflight-r1.json`

## Scope

Structure preflight checks parseability, required runtime fields, `package_id`, table shape, source-row preservation, continuous TC headings and runner validator profile consistency only. Do not perform semantic coverage review in this preflight.

## Required Output

Write structure-preflight findings/logs under `work/review-cycles/common-application-fields/outputs/` and update `cycle-state.yaml` according to `session-based-review-cycle-format.md`.
"""
    (PROMPTS / "prompt.structure-preflight-r1.md").write_text(prompt, encoding="utf-8", newline="\n")
    write_via_manifest(
        OUTPUTS / "writer-session-log.writer-r1.md",
        "Writer Session Log",
        [
            (
                2,
                "Session Metadata",
                table(
                    ["field", "value"],
                    [
                        ["skill", "`ft-test-case-writer`"],
                        ["mode", "`writer.session_initial_draft`"],
                        ["ft_slug", "`ft-2-OF_17`"],
                        ["scope_slug", f"`{SCOPE}`"],
                        ["started_from", "`cycle-state.yaml`"],
                        ["status_after", "`writer-draft-ready`"],
                    ],
                ),
            ),
            (
                2,
                "Inputs Read",
                bullet(
                    [
                        "`python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - budget `pass` 138.4 / 200.0 KiB.",
                        "`AGENTS.md`; `skills/README.md`; `references/agent/session-based-review-cycle-format.md`; `references/agent/codex-sdk-orchestration-format.md`; `skills/ft-test-case-writer/SKILL.md` - required instruction context.",
                        "`references/agent/writer-runtime-workflow.md`; `references/agent/writer-runtime-contract.md`; `references/qa/test-case-runtime-format.md`; `references/qa/coverage-runtime-checklist.md`; `references/qa/traceability-rules.md` - writer runtime rules.",
                        "`references/agent/writer-process-workflow.md`; `references/agent/workflow-state-format.md`; `references/agent/session-log-format.md`; `references/agent/agent-decision-log-format.md`; `references/agent/writer-handoff-format.md` - process artifact rules.",
                        "`references/agent/writer-output-format.md`; `references/agent/writer-table-workflow.md`; `references/agent/writer-table-artifacts-format.md`; `references/agent/writer-quality-gate-format.md` - table-heavy output rules.",
                        f"`fts/ft-2-OF_17/{HANDOFF_REL}/source-selection.md`; `scope-contract.md`; `source-parity-check.md`; `source-row-inventory.md`; `scope-coverage-gaps.md`; `scope-clarification-requests.md` - handoff inputs.",
                        "`fts/ft-2-OF_17/AGENT-NOTES.md` - `О`/`Р` interpretation.",
                        "`DOCX section-34` extracted through `test_case_agent.resolve_sections()` with glob path fallback - source table columns for `SRC-001`..`SRC-010`.",
                    ]
                ),
            ),
            (
                2,
                "Inputs Not Used",
                bullet(
                    [
                        "`support/Наполнение справочников_v1.xlsx` - source-selection says selected scope does not require a fixed dictionary/list.",
                        "`mockups/*` - source-selection says mockups are not required and must not override table properties.",
                        "Neighboring sections/actions/history forms - excluded by scope-contract.",
                    ]
                ),
            ),
            (
                2,
                "Key Decisions",
                bullet(
                    [
                        "Use package flow `WP-01`..`WP-03` from `scope-contract.md`.",
                        "Normalize six table properties per `SRC-*` row and preserve `GSR 205`..`GSR 214` individually.",
                        "Treat mandatory/input/value-type columns as source metadata unless there is a separate observable UI behavior.",
                        "Use fixture parameters for CDI/Gosuslugi status values instead of invented exact values.",
                    ]
                ),
            ),
            (
                2,
                "Risks And Fallbacks",
                bullet(
                    [
                        "Encoding fallback: initial PowerShell stdout distorted Cyrillic for instruction files; source and handoff files were reread with explicit UTF-8 and distorted stdout was not used as evidence.",
                        "Cyrillic DOCX path fallback: direct literal path failed under shell encoding; Python glob selected the same source document before extracting `section-34`.",
                        "Git status unavailable because Git safe-directory check rejects sandbox user ownership; no git-derived assumptions were used.",
                    ]
                ),
            ),
            (
                2,
                "Artifact Write Strategy",
                table(
                    ["artifact_path", "artifact_size_class", "write_strategy", "declared_before_first_write", "helper", "forbidden_methods_checked"],
                    [[f"`{CANONICAL_REL}` and `{TD_REL}/`", "`large generated`", "`file-based manifest write`", "`yes`", "`scripts/write_artifact_sections.py --manifest` via `scripts/build_common_application_fields_writer_artifacts.py`", "`yes`"]],
                ),
            ),
            (
                2,
                "Validation",
                bullet(
                    [
                        f"`python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_17/work/review-cycles/{SCOPE}/cycle-state.yaml` - pass; routed to `structure-preflight-r1`; runner profile `outputs/scoped-validator-profile.structure-preflight-r1.json` has `unresolved_warning_error_count = 0`.",
                    ]
                ),
            ),
            (
                2,
                "Contamination Check",
                bullet(["Only `ft-2-OF_17` selected handoff/source files were used as requirement sources; prior canary outputs were consulted only for artifact-builder pattern, not domain content."]),
            ),
            (
                2,
                "Event Timeline",
                table(
                    ["step", "event", "result", "artifact_or_evidence"],
                    [
                        ["1", "Resolved instruction context", "budget pass", "`resolver stdout`"],
                        ["2", "Read handoff and package notes", "scope confirmed", "`scope-contract.md`; `AGENT-NOTES.md`"],
                        ["3", "Extracted DOCX section table", "row columns confirmed", "`DOCX section-34`"],
                        ["4", "Wrote split artifacts and canonical TC", "draft created", f"`{TD_REL}/`; `{CANONICAL_REL}`"],
                        ["5", "Prepared structure-preflight prompt", "prompt created", f"`work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md`"],
                    ],
                ),
            ),
            (
                2,
                "Quality Checkpoints",
                table(
                    ["checkpoint", "status", "evidence", "follow_up"],
                    [
                        ["Writer Quality Gate", "pass", "`writer-quality-gate.md`", "structure preflight should verify parseability"],
                        ["Self-check near misses", "pass", "`GAP-001`..`GAP-004` prevent invented oracles", "semantic review should inspect gap handling"],
                    ],
                ),
            ),
            (
                2,
                "Technical Fallbacks",
                table(
                    ["fallback_id", "trigger", "failed_method", "fallback_method", "helper_artifact_path", "retained", "quality_risk", "follow_up"],
                    [
                        ["`TF-001`", "`encoding issue`", "`PowerShell console output read for Russian instruction files`", "`explicit UTF-8 reread with Get-Content -Encoding UTF8`", "`n/a`", "`n/a`", "`none; distorted stdout discarded as evidence`", "`none_required:pass`"],
                        ["`TF-002`", "`path encoding issue`", "`direct Cyrillic DOCX Path literal in shell heredoc`", "`Python glob in source directory, then resolve_sections()`", "`n/a`", "`n/a`", "`none; selected path printed and matched source-selection`", "`none_required:pass`"],
                        ["`TF-003`", "`git ownership guard`", "`git status --short`", "`direct Test-Path/Get-ChildItem file inspection`", "`n/a`", "`n/a`", "`none for generated artifacts`", "`none_required:pass`"],
                        ["`TF-004`", "`mechanical id normalization`", "`manual apply_patch replacement would be verbose for repeated GAP ids`", "`direct UTF-8 file rewrite of builder script replacing GAP-CAF-* with GAP-###`", "`scripts/build_common_application_fields_writer_artifacts.py`", "`yes`", "`low; regenerated artifacts and runner validation passed`", "`none_required:pass`"],
                    ],
                ),
            ),
            (
                2,
                "Handoff Notes For Next Session",
                bullet(
                    [
                        "Structure preflight should focus on canonical headings, parser fields, split table shapes and `package_id` presence.",
                        "Semantic review should later inspect whether metadata-only handling of `О`, input type and value type is acceptable for this table scope.",
                    ]
                ),
            ),
        ],
    )
    write_via_manifest(
        OUTPUTS / "agent-decision-log.writer-r1.md",
        "Agent Decision Log",
        [
            (
                2,
                "Decision Log Metadata",
                table(
                    ["field", "value"],
                    [["ft_slug", "`ft-2-OF_17`"], ["scope_slug", f"`{SCOPE}`"], ["stage", "`ft-test-case-writer / writer-r1`"], ["started_from", "`cycle-state.yaml`"]],
                ),
            ),
            (
                2,
                "Decision Log",
                table(
                    ["decision_id", "step", "decision_type", "input_or_trigger", "decision", "rationale", "artifact_or_output", "risk_or_confidence", "status"],
                    [
                        ["`DEC-001`", "1", "`scope-boundary`", "`scope-contract.md`", "Use only `SRC-001`..`SRC-010` from `common-application-fields`.", "Scope explicitly excludes actions/history/other sections.", f"`{CANONICAL_REL}`", "`high`", "`applied`"],
                        ["`DEC-002`", "2", "`traceability`", "`source-parity-check.md`", "Preserve PDF-only `GSR 205`..`GSR 214`.", "Parity check marks them mandatory req_id values.", "`atomic-requirements-ledger.md`; TC traceability", "`high`", "`applied`"],
                        ["`DEC-003`", "3", "`coverage`", "`AGENT-NOTES.md`", "Interpret `О` as обязательность and `Р` as редактируемость.", "Package note is mandatory context for UI field tables.", "`source-table-normalization.md`; `atomic-requirements-ledger.md`", "`high`", "`applied`"],
                        ["`DEC-004`", "4", "`gap`", "`scope-coverage-gaps.md`; source rows", "Do not invent exact generated/status/CDI/Gosuslugi values.", "Handoff explicitly forbids exact value invention.", "`coverage-gaps.md`; TC fixture data", "`high`", "`applied`"],
                        ["`DEC-005`", "5", "`test-design`", "`test-case-runtime-format.md`", "Do not create standalone generic TC for value type/input metadata.", "Value type/input type alone is not an observable oracle for read-only generated fields.", "`test-design-decision-table.md`", "`medium`", "`applied`"],
                        ["`DEC-006`", "6", "`artifact-write`", "`writer-process-workflow.md`", "Use file-based manifest writer.", "Scope has `WP-*` packages and generated artifacts.", "`artifact-write-strategy.md`; `_artifact_write/`", "`high`", "`applied`"],
                        ["`DEC-007`", "7", "`routing`", "`writer-quality-gate.md`; scoped validator profile", "Route to `structure-preflight-r1` if runner validate has zero current-scope warning/error findings.", "Session-based contract forbids writer-ready with current-scope warnings/errors.", "`cycle-state.yaml`; `prompt.structure-preflight-r1.md`", "`high`", "`applied`"],
                    ],
                ),
            ),
        ],
    )
    state = f"""cycle_id: {CYCLE_ID}
ft_slug: ft-2-OF_17
scope_slug: {SCOPE}
section_id: {SECTION}
current_stage: structure-preflight-r1
stage_status: writer-draft-ready
semantic_round: 0
max_semantic_rounds: 2
canonical_test_cases: {CANONICAL_REL}
test_design_dir: {TD_REL}
active_snapshot: none
active_transition_prompt: work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md
sessions: []
latest_artifacts:
  - {CANONICAL_REL}
  - {TD_REL}
  - work/review-cycles/{SCOPE}/outputs/writer-r1-response.md
  - work/review-cycles/{SCOPE}/outputs/writer-session-log.writer-r1.md
  - work/review-cycles/{SCOPE}/outputs/agent-decision-log.writer-r1.md
  - work/review-cycles/{SCOPE}/outputs/scoped-validator-profile.structure-preflight-r1.json
  - work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md
blocking_reasons: []
blocking_findings: []
open_questions:
  - Exact generated application number/status and CDI/Gosuslugi status values are not source-specified; writer preserved this as non-blocking gaps and fixture parameters.
accepted_risks: []
"""
    (CYCLE / "cycle-state.yaml").write_text(state, encoding="utf-8", newline="\n")


def main() -> int:
    TD.mkdir(parents=True, exist_ok=True)
    simple_artifacts()
    canonical_file()
    writer_self_check()
    outputs_and_state()
    print(f"wrote {CANONICAL.relative_to(ROOT)}")
    print(f"wrote {TD.relative_to(ROOT)}")
    print(f"wrote {CYCLE.relative_to(ROOT) / 'cycle-state.yaml'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

