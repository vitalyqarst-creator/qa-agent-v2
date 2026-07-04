from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "fts" / "AutoFin"
SCOPE = "application-card-passport-current-and-previous"
SECTION = "14"
TD_REL = f"work/test-design/{SECTION}-{SCOPE}"
TD = FT / TD_REL
CANONICAL_REL = f"test-cases/{SECTION}-{SCOPE}.md"
CANONICAL = FT / CANONICAL_REL
CYCLE_REL = f"work/review-cycles/{SCOPE}"
CYCLE = FT / CYCLE_REL
OUTPUTS = CYCLE / "outputs"
PROMPTS = CYCLE / "prompts"
PROFILE_REL = f"{CYCLE_REL}/outputs/scoped-validator-profile.writer-r1.json"


def esc(value: str) -> str:
    return str(value).replace("\n", "<br>").replace("|", "\\|")


def table(headers: list[str], rows: list[list[str]]) -> str:
    return "\n".join(
        ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
        + ["| " + " | ".join(esc(cell) for cell in row) + " |" for row in rows]
    )


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def write_markdown(target: Path, sections: list[tuple[int, str, str]], title: str | None = None) -> None:
    scratch = TD / "_artifact_write" / target.stem
    scratch.mkdir(parents=True, exist_ok=True)
    manifest_sections: list[dict[str, object]] = []
    for index, (level, heading, body) in enumerate(sections, start=1):
        content_path = scratch / f"{index:02d}.md"
        content_path.write_text(body.strip() + "\n", encoding="utf-8", newline="\n")
        manifest_sections.append({"level": level, "heading": heading, "content_file": content_path.name})
    manifest: dict[str, object] = {"target_path": str(target), "sections": manifest_sections}
    if title:
        preamble = scratch / "00-preamble.md"
        preamble.write_text(f"# {title}\n", encoding="utf-8", newline="\n")
        manifest["preamble_file"] = preamble.name
    manifest_path = scratch / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(manifest_path)], cwd=ROOT, check=True)


def tc_id_for(atom_id: str) -> str:
    n = int(atom_id.replace("ATOM-", ""))
    if n == 53:
        return "TC-ACPCP-049"
    if n == 54:
        return "TC-ACPCP-050"
    if n == 55:
        return "TC-ACPCP-051"
    if n <= 52:
        # Conservative existing mapping for generated draft. Some tests cover scenario pairs; plan rows use one primary TC.
        mapping = {
            1: 1, 2: 1, 3: 2, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9,
            10: 10, 11: 11, 12: 12, 13: 13, 14: 13, 15: 14, 16: 15, 17: 16, 18: 17,
            19: 18, 20: 20, 21: 21, 22: 22, 23: 24, 24: 25, 25: 26, 26: 28, 27: 29, 28: 30, 29: 31,
            30: 32, 31: 2, 32: 32, 33: 33, 34: 33, 35: 34, 36: 35,
            37: 36, 38: 37, 39: 38, 40: 39, 41: 39, 42: 40, 43: 41, 44: 0,
            45: 36, 46: 42, 47: 44, 48: 45, 49: 46, 50: 47, 51: 36, 52: 48,
        }
        tc_n = mapping.get(n, n)
        if tc_n == 0:
            return "GAP-005"
        return f"TC-ACPCP-{tc_n:03d}"
    raise ValueError(atom_id)


ATOMS = [
    ["ATOM-001", "WP-01", "SRC-001", "no_requirement_code:SRC-001", "Блок `Паспортные данные` отображается в карточке заявки.", "High", "TC-ACPCP-001", "covered", "none_required:covered"],
    ["ATOM-002", "WP-01", "SRC-002; SRC-003; SRC-004; SRC-005", "no_requirement_code:section-14", "Поля текущего паспорта `Серия`, `Номер`, `Код подразделения`, `Кем выдан` отображаются в блоке паспортных данных.", "High", "TC-ACPCP-001", "covered", "none_required:covered"],
    ["ATOM-003", "WP-01", "SRC-002; SRC-003; SRC-004; SRC-005; SRC-008; SRC-009", "no_requirement_code:section-14", "Поля текущего паспорта имеют признак обязательности по колонке `О=Да`.", "High", "TC-ACPCP-002; TC-ACPCP-003", "covered", "none_required:covered"],
    ["ATOM-004", "WP-01", "SRC-002", "no_requirement_code:SRC-002", "Серия текущего паспорта принимает 4 символа.", "High", "TC-ACPCP-004", "covered", "GAP-003"],
    ["ATOM-005", "WP-01", "SRC-002", "no_requirement_code:SRC-002", "Негативный класс `111`: серия текущего паспорта с одинаковые подряд цифры отклоняется.", "High", "TC-ACPCP-005", "covered", "none_required:covered"],
    ["ATOM-006", "WP-01", "SRC-003", "no_requirement_code:SRC-003", "Номер текущего паспорта принимает 6 символов.", "High", "TC-ACPCP-006", "covered", "GAP-003"],
    ["ATOM-007", "WP-01", "SRC-003", "no_requirement_code:SRC-003", "Негативный класс `111111`: номер текущего паспорта с одинаковые подряд цифры отклоняется.", "High", "TC-ACPCP-007", "covered", "none_required:covered"],
    ["ATOM-008", "WP-01", "SRC-004", "no_requirement_code:SRC-004", "Код подразделения принимает 6 символов.", "High", "TC-ACPCP-008", "covered", "GAP-003"],
    ["ATOM-009", "WP-01", "SRC-004", "no_requirement_code:SRC-004", "Код подразделения отображается в форме `xxx -xxx`.", "Medium", "TC-ACPCP-009", "covered", "none_required:covered"],
    ["ATOM-010", "WP-01", "SRC-005; SRC-006", "no_requirement_code:SRC-005", "При `Ввести вручную подразделение = Нет` отображается `Кем выдан` в режиме раскрывающегося списка.", "High", "TC-ACPCP-010", "covered", "none_required:covered"],
    ["ATOM-011", "WP-01", "SRC-005", "no_requirement_code:SRC-005", "`Кем выдан` получает значение из результата DaData по вводу кода подразделения.", "High", "TC-ACPCP-011", "covered", "GAP-004"],
    ["ATOM-012", "WP-01", "SRC-005", "no_requirement_code:SRC-005", "Если DaData возвращает несколько значений, пользователь выбирает нужное значение из списка.", "Medium", "TC-ACPCP-012", "covered", "GAP-004"],
    ["ATOM-013", "WP-01", "SRC-006", "no_requirement_code:SRC-006", "`Ввести вручную подразделение` отображается всегда.", "Medium", "TC-ACPCP-013", "covered", "none_required:covered"],
    ["ATOM-014", "WP-01", "SRC-006", "no_requirement_code:SRC-006", "Значение по умолчанию для `Ввести вручную подразделение` равно `Нет`.", "Medium", "TC-ACPCP-013", "covered", "none_required:covered"],
    ["ATOM-015", "WP-01", "SRC-006", "no_requirement_code:SRC-006", "`Ввести вручную подразделение` является переключателем `Да/Нет`.", "Medium", "TC-ACPCP-014", "covered", "none_required:covered"],
    ["ATOM-016", "WP-01", "SRC-007", "no_requirement_code:SRC-007", "При `Ввести вручную подразделение = Да` отображается ручное текстовое поле `Кем выдан`.", "High", "TC-ACPCP-015", "covered", "none_required:covered"],
    ["ATOM-017", "WP-01", "SRC-007", "no_requirement_code:SRC-007", "Ручное поле `Кем выдан` обязательно при `Ввести вручную подразделение = Да`.", "High", "TC-ACPCP-016", "covered", "none_required:covered"],
    ["ATOM-018", "WP-01", "SRC-007", "no_requirement_code:SRC-007", "Ручное поле `Кем выдан` редактируемо и принимает строковое значение.", "Medium", "TC-ACPCP-017", "covered", "none_required:covered"],
    ["ATOM-019", "WP-01", "SRC-008; GAP-001", "BSR 92", "`Дата выдачи` имеет тип значения дата.", "High", "TC-ACPCP-002; TC-ACPCP-003; TC-ACPCP-018", "covered", "none_required:covered"],
    ["ATOM-020", "WP-01", "SRC-008; GAP-001", "BSR 92", "Дата выдачи раньше `Дата_14` показывает `Выдача паспорта предусмотрена с 14 лет` и запрещает сохранение.", "High", "TC-ACPCP-020", "covered", "none_required:covered"],
    ["ATOM-021", "WP-01", "SRC-008; GAP-001", "BSR 92", "Дата выдачи `Дата_14` проходит минимальную возрастную проверку.", "High", "TC-ACPCP-021", "covered", "none_required:covered"],
    ["ATOM-022", "WP-01", "SRC-008; GAP-001", "BSR 92", "Паспорт, выданный в диапазоне `Дата_14..Дата_20`, действителен до `Дата_20_90` включительно.", "High", "TC-ACPCP-022; TC-ACPCP-023", "covered", "none_required:covered"],
    ["ATOM-023", "WP-01", "SRC-008; GAP-001", "BSR 92", "После `Дата_20_90` для паспорта, выданного до или на 20 лет, отображается `Паспорт недействителен (просрочен)` и сохранение запрещено.", "High", "TC-ACPCP-024", "covered", "none_required:covered"],
    ["ATOM-024", "WP-01", "SRC-008; GAP-001", "BSR 92", "Дата выдачи `Дата_20_1` относится к диапазону после 20 лет.", "High", "TC-ACPCP-025", "covered", "none_required:covered"],
    ["ATOM-025", "WP-01", "SRC-008; GAP-001", "BSR 92", "Паспорт, выданный после 20 и до 45 лет, действителен до `Дата_45_90` включительно.", "High", "TC-ACPCP-026; TC-ACPCP-027", "covered", "none_required:covered"],
    ["ATOM-026", "WP-01", "SRC-008; GAP-001", "BSR 92", "После `Дата_45_90` для паспорта, выданного после 20 и до 45 лет, отображается `Паспорт недействителен (просрочен)` и сохранение запрещено.", "High", "TC-ACPCP-028", "covered", "none_required:covered"],
    ["ATOM-027", "WP-01", "SRC-008; GAP-001", "BSR 92", "Дата выдачи `>= Дата_45` считается бессрочной по возрастному правилу.", "High", "TC-ACPCP-029", "covered", "none_required:covered"],
    ["ATOM-028", "WP-01", "SRC-008; GAP-001", "BSR 93", "Дата выдачи больше текущей даты показывает `Дата должна быть не больше текущей даты` и запрещает сохранение.", "High", "TC-ACPCP-030", "covered", "none_required:covered"],
    ["ATOM-029", "WP-01", "SRC-008; GAP-001", "BSR 92", "Пустая `Дата выдачи` дает ошибку обязательности и запрещает сохранение без фиксированного текста ошибки.", "High", "TC-ACPCP-019; TC-ACPCP-031", "covered", "none_required:covered"],
    ["ATOM-030", "WP-01", "SRC-009", "no_requirement_code:SRC-009", "`Место рождения` отображается всегда.", "Medium", "TC-ACPCP-032", "covered", "none_required:covered"],
    ["ATOM-031", "WP-01", "SRC-009", "no_requirement_code:SRC-009", "`Место рождения` обязательно.", "Medium", "TC-ACPCP-002; TC-ACPCP-003", "covered", "none_required:covered"],
    ["ATOM-032", "WP-01", "SRC-009", "no_requirement_code:SRC-009", "`Место рождения` принимает строковое значение.", "Medium", "TC-ACPCP-032", "covered", "none_required:covered"],
    ["ATOM-033", "WP-01", "SRC-010", "no_requirement_code:SRC-010", "`Клиент менял паспорт` отображается всегда.", "Medium", "TC-ACPCP-033", "covered", "none_required:covered"],
    ["ATOM-034", "WP-01", "SRC-010", "no_requirement_code:SRC-010", "Значение по умолчанию для `Клиент менял паспорт` равно `Нет`.", "Medium", "TC-ACPCP-033", "covered", "none_required:covered"],
    ["ATOM-035", "WP-01", "SRC-010", "no_requirement_code:SRC-010", "`Клиент менял паспорт` является переключателем `Да/Нет`.", "Medium", "TC-ACPCP-034", "covered", "none_required:covered"],
    ["ATOM-036", "WP-01", "SRC-010", "no_requirement_code:SRC-010", "Значение `Да`, если дата выдачи текущего паспорта менее 3 лет назад, иначе `Нет`, является source rule для выбора значения.", "High", "TC-ACPCP-035", "covered", "none_required:covered"],
    ["ATOM-037", "WP-02", "SRC-011; GAP-002", "no_requirement_code:SRC-011", "Блок `Данные предыдущих паспортов` отображается при `Клиент менял паспорт = Да`.", "High", "TC-ACPCP-036", "covered", "none_required:covered"],
    ["ATOM-038", "WP-02", "SRC-011; GAP-002", "no_requirement_code:SRC-011", "Блок `Данные предыдущих паспортов` не отображается при `Клиент менял паспорт = Нет`.", "Medium", "TC-ACPCP-037", "covered", "none_required:covered"],
    ["ATOM-039", "WP-02", "SRC-012; GAP-002", "no_requirement_code:SRC-012", "Кнопка `Добавить паспорт` отображается при `Клиент менял паспорт = Да`.", "Medium", "TC-ACPCP-038", "covered", "none_required:covered"],
    ["ATOM-040", "WP-02", "SRC-012; GAP-002", "no_requirement_code:SRC-012", "Нажатие `Добавить паспорт` добавляет поля последнего предыдущего паспорта.", "High", "TC-ACPCP-039", "covered", "none_required:covered"],
    ["ATOM-041", "WP-02", "SRC-012; GAP-002", "no_requirement_code:SRC-012", "После добавления отображаются виджеты `+Добавить паспорт` и `корзина` для предыдущего паспорта.", "Medium", "TC-ACPCP-039", "covered", "none_required:covered"],
    ["ATOM-042", "WP-02", "SRC-013; GAP-002", "no_requirement_code:SRC-013", "Виджет `Корзина` отображается при `Клиент менял паспорт = Да`.", "Medium", "TC-ACPCP-040", "covered", "none_required:covered"],
    ["ATOM-043", "WP-02", "SRC-013; GAP-002", "no_requirement_code:SRC-013", "Нажатие `Корзина` удаляет соответствующие поля блока предыдущего паспорта.", "High", "TC-ACPCP-041", "covered", "none_required:covered"],
    ["ATOM-044", "WP-02", "SRC-013; GAP-002", "no_requirement_code:SRC-013", "Additional previous-passport fields named only in the delete-source note are not source-row defined in this scope.", "Medium", "GAP-005", "gap", "GAP-005"],
    ["ATOM-045", "WP-02", "SRC-014; SRC-015; SRC-016; GAP-002", "no_requirement_code:section-14", "Поля последнего предыдущего паспорта `Серия`, `Номер`, `Дата выдачи` отображаются при `Клиент менял паспорт = Да`.", "High", "TC-ACPCP-036; TC-ACPCP-039", "covered", "none_required:covered"],
    ["ATOM-046", "WP-02", "SRC-014; SRC-015; SRC-016; GAP-002", "no_requirement_code:section-14", "Поля последнего предыдущего паспорта обязательны.", "High", "TC-ACPCP-042", "covered", "none_required:covered"],
    ["ATOM-047", "WP-02", "SRC-014; GAP-002", "no_requirement_code:SRC-014", "Серия последнего предыдущего паспорта принимает 4 символа.", "High", "TC-ACPCP-044", "covered", "GAP-003"],
    ["ATOM-048", "WP-02", "SRC-014; GAP-002", "no_requirement_code:SRC-014", "Негативный класс `111`: серия последнего предыдущего паспорта с одинаковые подряд цифры отклоняется.", "High", "TC-ACPCP-045", "covered", "none_required:covered"],
    ["ATOM-049", "WP-02", "SRC-015; GAP-002", "no_requirement_code:SRC-015", "Номер последнего предыдущего паспорта принимает 6 символов.", "High", "TC-ACPCP-046", "covered", "GAP-003"],
    ["ATOM-050", "WP-02", "SRC-015; GAP-002", "no_requirement_code:SRC-015", "Негативный класс `111111`: номер последнего предыдущего паспорта с одинаковые подряд цифры отклоняется.", "High", "TC-ACPCP-047", "covered", "none_required:covered"],
    ["ATOM-051", "WP-02", "SRC-016; GAP-002", "no_requirement_code:SRC-016", "Дата выдачи последнего предыдущего паспорта отображается при `Клиент менял паспорт = Да`.", "Medium", "TC-ACPCP-036", "covered", "none_required:covered"],
    ["ATOM-052", "WP-02", "SRC-016; GAP-002", "no_requirement_code:SRC-016", "Дата выдачи последнего предыдущего паспорта имеет тип даты.", "Medium", "TC-ACPCP-043; TC-ACPCP-048", "covered", "none_required:covered"],
    ["ATOM-053", "WP-01", "SRC-002; SRC-003; SRC-004", "no_requirement_code:section-14", "Поля `Серия`, `Номер`, `Код подразделения` текущего паспорта принимают только числовые символы.", "High", "TC-ACPCP-049", "covered", "GAP-003"],
    ["ATOM-054", "WP-02", "SRC-014; SRC-015; GAP-002", "no_requirement_code:section-14", "Поля `Серия`, `Номер` последнего предыдущего паспорта принимают только числовые символы.", "High", "TC-ACPCP-050", "covered", "GAP-003"],
    ["ATOM-055", "WP-01;WP-02", "SRC-002", "no_requirement_code:section-14", "Механика обработки unsupported input classes вне подтвержденного positive path не задана источником.", "Medium", "GAP-003", "gap", "GAP-003"],
]


def q(v: str) -> str:
    return f"`{v}`"


def normalization_rows() -> list[list[str]]:
    rows: list[list[str]] = []
    for atom_id, package, source_ref, req_id, statement, _priority, planned, status, gap in ATOMS:
        src = source_ref.split(";")[0].strip()
        if status == "gap":
            prop = "gap-unclear"
            condition = "source limitation"
            confidence = "medium"
        elif atom_id in {"ATOM-004", "ATOM-006", "ATOM-008", "ATOM-047", "ATOM-049"}:
            prop = "length-format"
            condition = "source-backed length"
            confidence = "high"
        elif atom_id in {"ATOM-053", "ATOM-054"}:
            prop = "numeric-format"
            condition = "source-backed character class"
            confidence = "medium"
        elif atom_id in {"ATOM-020"}:
            prop = "date-passport-validity"
            condition = "BSR 92"
            confidence = "high"
        elif atom_id in {"ATOM-028"}:
            prop = "date-validity-window"
            condition = "BSR 93"
            confidence = "high"
        elif atom_id in {"ATOM-021", "ATOM-023", "ATOM-024", "ATOM-026", "ATOM-029"}:
            prop = "date-boundary"
            condition = "BSR 92"
            confidence = "high"
        elif "отображается" in statement or "отображаются" in statement:
            prop = "visibility"
            condition = "source-backed"
            confidence = "high"
        elif "обяз" in statement:
            prop = "requiredness"
            condition = "source-backed"
            confidence = "high"
        elif "редактируемо" in statement or "строковое" in statement:
            prop = "editability"
            condition = "source-backed"
            confidence = "high"
        elif "по умолчанию" in statement:
            prop = "default-value"
            condition = "source-backed"
            confidence = "high"
        elif "переключателем" in statement:
            prop = "input-widget"
            condition = "source-backed"
            confidence = "high"
        elif "DaData" in statement:
            prop = "integration-prefill"
            condition = "source-backed visible result"
            confidence = "medium"
        elif "одинаковые цифры" in statement:
            prop = "repeated-digits"
            condition = "source-backed validation"
            confidence = "high"
        else:
            prop = "field-behavior"
            condition = "source-backed"
            confidence = "high"
        field_or_block = "unsupported-source-detail" if status == "gap" else (statement.split("`")[1] if "`" in statement else "паспортные данные")
        rows.append([
            q(src),
            q(f"SP-{atom_id.replace('ATOM-', '')}"),
            q(package),
            field_or_block,
            q(prop),
            q(condition),
            statement,
            q(req_id),
            q(source_ref),
            q(confidence),
            q("none_required:covered" if atom_id in {"ATOM-053", "ATOM-054"} else (gap if "GAP-" in gap else "none_required:covered")),
            q(atom_id),
        ])
    return rows


def coverage_obligation_rows() -> list[list[str]]:
    rows: list[list[str]] = []
    idx = 1
    def add(atom_id: str, ptype: str, cls: str, planned: str, status: str = "covered", notes: str = "none_required:covered") -> None:
        nonlocal idx
        atom = next(a for a in ATOMS if a[0] == atom_id)
        rows.append([q(f"OBL-{idx:03d}"), q(atom[1]), q(f"SP-{atom_id.replace('ATOM-', '')}"), q(atom_id), q(ptype), q(cls), atom[4], q(atom[2]), q(planned), q(status), q(notes)])
        idx += 1
    for cls, planned in [
        ("passport-before-14-rejected", "TC-ACPCP-020"),
        ("passport-14-to-20-plus-45-window", "TC-ACPCP-022"),
        ("passport-20-plus-1-to-45-plus-45-window", "TC-ACPCP-026"),
        ("passport-45-plus-indefinite-window", "TC-ACPCP-029"),
    ]:
        add("ATOM-020", "date-passport-validity", cls, planned)
    for cls, planned in [
        ("lower-boundary-accepted", "TC-ACPCP-018"),
        ("upper-boundary-accepted", "TC-ACPCP-018"),
        ("off-boundary-rejected", "TC-ACPCP-030"),
    ]:
        add("ATOM-028", "date-validity-window", cls, planned)
    for atom_id, tc in [("ATOM-053", "TC-ACPCP-049"), ("ATOM-054", "TC-ACPCP-050")]:
        for cls in ["valid-digits", "reject-letters", "reject-spaces", "reject-special-chars", "reject-decimal-separator", "reject-sign"]:
            add(atom_id, "numeric-format", cls, tc if cls == "valid-digits" else "GAP-003", "covered" if cls == "valid-digits" else "gap", "GAP-003" if cls != "valid-digits" else "none_required:covered")
    return rows


def tddt_rows() -> list[list[str]]:
    planned_overrides = {
        "ATOM-003": "TC-ACPCP-002; TC-ACPCP-003",
        "ATOM-019": "TC-ACPCP-002; TC-ACPCP-003; TC-ACPCP-018",
        "ATOM-022": "TC-ACPCP-022; TC-ACPCP-023",
        "ATOM-025": "TC-ACPCP-026; TC-ACPCP-027",
        "ATOM-029": "TC-ACPCP-019; TC-ACPCP-031",
        "ATOM-031": "TC-ACPCP-002; TC-ACPCP-003",
        "ATOM-045": "TC-ACPCP-036; TC-ACPCP-039",
        "ATOM-046": "TC-ACPCP-042",
        "ATOM-052": "TC-ACPCP-043; TC-ACPCP-048",
    }
    rows = []
    for atom_id, package, source_ref, _req_id, statement, _priority, planned, status, gap in ATOMS:
        decision = "gap_unclear" if status == "gap" else "standalone_tc"
        planned_value = planned_overrides.get(atom_id, planned)
        rows.append([
            q(f"TDD-{atom_id.replace('ATOM-', '')}"),
            q(package),
            q(f"SP-{atom_id.replace('ATOM-', '')}"),
            q(atom_id),
            q("gap-unclear" if status == "gap" else "field-behavior"),
            q(decision),
            "Свойство имеет отдельный observable oracle или узкий gap.",
            q(planned_value),
            q(source_ref),
            q("no" if status == "gap" else "yes"),
            "none" if status == "gap" else statement,
            q("none" if status == "gap" else statement),
            q(gap if status == "gap" else "none_required:covered"),
            q(gap if status == "gap" else "not_applicable:covered"),
            q("medium"),
        ])
    return rows


def plan_rows() -> list[list[str]]:
    rows = []
    scenario_support_atoms = {"ATOM-002", "ATOM-014", "ATOM-031", "ATOM-032", "ATOM-034", "ATOM-041", "ATOM-045", "ATOM-051"}
    planned_check_overrides = {
        "ATOM-012": "Если DaData возвращает несколько значений, пользователь выбирает нужное значение из списка; иначе one-value branch покрывается `TC-ACPCP-011`.",
        "ATOM-017": "Ручное поле `Кем выдан` обязательно при `Ввести вручную подразделение = Да`; otherwise branch покрывается режимом `Нет` в `TC-ACPCP-010`.",
    }
    for idx, (atom_id, package, source_ref, _req_id, statement, _priority, planned, status, gap) in enumerate(ATOMS, start=1):
        is_scenario_support = atom_id in scenario_support_atoms
        check_type = "scenario-support" if is_scenario_support else ("gap" if status == "gap" else "manual-ui")
        coverage_class = "scenario-support" if is_scenario_support else ("source-backed" if status != "gap" else "gap")
        planned_check = planned_check_overrides.get(atom_id, statement)
        plan_source_ref = source_ref.replace("; GAP-002", "") if status != "gap" else source_ref
        rows.append([
            q(f"PLAN-{idx:03d}"),
            q(package),
            q("gap" if status == "gap" else "field-behavior"),
            q(plan_source_ref),
            q(atom_id),
            planned_check,
            q(check_type),
            q(coverage_class),
            q("concrete-fixture" if status != "gap" else "not_applicable:gap"),
            statement if status != "gap" else "not_applicable:gap",
            q(plan_source_ref),
            q(planned),
            q("gap" if status == "gap" else "covered"),
        ])
    return rows


def rewrite_canonical() -> None:
    text = CANONICAL.read_text(encoding="utf-8")
    text = text.replace("`GAP-003`, `GAP-004`, `GAP-005` are visible residual risks.", "`GAP-003`, `GAP-004`, `GAP-005` are visible residual risks; remediation split numeric/date atoms and design rows.")
    text = text.replace("`WP-01` | `36` | `35` | `36` | `0`", "`WP-01` | `39` | `38` | `39` | `0`")
    text = text.replace("`WP-02` | `16` | `13` | `15` | `1`", "`WP-02` | `16` | `14` | `15` | `1`")
    text = text.replace("**Название:** Обязательность ручного поля Кем выдан при empty value", "**Название:** Пустое обязательное ручное поле Кем выдан")
    text = text.replace("**Название:** Обязательность ручного поля Кем выдан", "**Название:** Пустое обязательное ручное поле Кем выдан")
    text = text.replace("**Название:** Обязательность даты выдачи текущего паспорта при empty value", "**Название:** Пустая обязательная дата выдачи текущего паспорта")
    text = text.replace("**Название:** Обязательность даты выдачи текущего паспорта", "**Название:** Пустая обязательная дата выдачи текущего паспорта")
    text = text.replace("**Трассировка:** `ATOM-019`; `ATOM-029`; `SRC-008`; `GAP-001`; `WP-01`", "**Трассировка:** `ATOM-029`; `SRC-008`; `GAP-001`; `WP-01`")
    text = text.replace("**Трассировка:** `ATOM-046`; `ATOM-052`; `SRC-014`; `SRC-015`; `SRC-016`; `GAP-002`; `WP-02`", "**Трассировка:** `ATOM-052`; `SRC-014`; `SRC-015`; `SRC-016`; `GAP-002`; `WP-02`")
    text = text.replace("Поле `Кем выдан` предзаполняется значением", "Поле `Кем выдан` получает значение")
    # Add focused numeric class TCs. These do not assert unsupported invalid mechanics; GAP-003 owns those classes.
    extra = """

## TC-ACPCP-049

**Название:** Числовой класс полей текущего паспорта

**Тип:** Positive

**Приоритет:** High

**package_id:** WP-01

**Трассировка:** `ATOM-053`; `SRC-002`; `SRC-003`; `SRC-004`; `GAP-003`; `WP-01`

### Предусловия

- Открыта карточка заявки на разделе `Заявка`.

### Тестовые данные

- Серия: `1234`.
- Номер: `123456`.
- Код подразделения: `770001`.

### Шаги

1. Ввести числовые значения в поля `Серия`, `Номер`, `Код подразделения`.

### Итоговый ожидаемый результат

Поля `Серия`, `Номер`, `Код подразделения` отображают введенные числовые значения.

### Постусловия

Отменить несохраненные изменения.

## TC-ACPCP-050

**Название:** Числовой класс полей последнего предыдущего паспорта

**Тип:** Positive

**Приоритет:** High

**package_id:** WP-02

**Трассировка:** `ATOM-054`; `SRC-014`; `SRC-015`; `GAP-002`; `GAP-003`; `WP-02`

### Предусловия

- Открыта карточка заявки на разделе `Заявка`.
- Поле `Клиент менял паспорт` установлено в значение `Да`.

### Тестовые данные

- Серия: `4321`.
- Номер: `654321`.

### Шаги

1. Ввести числовые значения в поля `Серия`, `Номер` последнего предыдущего паспорта.

### Итоговый ожидаемый результат

Поля `Серия`, `Номер` последнего предыдущего паспорта отображают введенные числовые значения.

### Постусловия

Вернуть значение `Клиент менял паспорт` в `Нет` или отменить несохраненные изменения.
"""
    if "## TC-ACPCP-049" not in text:
        text = text.rstrip() + "\n" + extra
    CANONICAL.write_text(text, encoding="utf-8", newline="\n")


def write_artifacts() -> None:
    write_markdown(TD / "source-table-normalization.md", [(1, "Source Table Normalization", table(["source_row_id", "source_property_id", "package_id", "field_or_block", "property", "condition", "expected_behavior", "requirement_code", "source_ref", "confidence", "gap_id", "linked_atoms"], normalization_rows()))])
    write_markdown(TD / "test-design-decision-table.md", [(1, "Test Design Decision Table", table(["decision_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "decision", "decision_reason", "planned_tc_or_gap", "oracle_source", "must_be_executable", "observable_oracle", "testable_part", "blocked_part", "gap_admissibility", "review_risk"], tddt_rows()))])
    write_markdown(TD / "coverage-obligation-table.md", [(1, "Coverage Obligation Table", table(["obligation_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "obligation_class", "required_behavior", "source_ref", "planned_tc_or_gap", "status", "review_notes"], coverage_obligation_rows()))])
    write_markdown(TD / "atomic-requirements-ledger.md", [(1, "Atomic Requirements Ledger", table(["atom_id", "package_id", "source_ref", "req_id", "atomic_statement", "covered_by_tc", "coverage_status", "gap_note", "priority"], [[q(a[0]), q(a[1]), q(a[2]), q(a[3]), a[4], q(a[6]), q(a[7]), q(a[8]), q(a[5])] for a in ATOMS]))])
    write_markdown(TD / "package-test-design-plan.md", [(1, "Package Test Design Plan", table(["design_item_id", "package_id", "design_dimension", "source_ref", "linked_atoms", "planned_check", "check_type", "coverage_class", "input_class", "single_expected_behavior", "oracle_source", "planned_tc_or_gap", "status"], plan_rows()))])
    write_markdown(TD / "dictionary-inventory.md", [(1, "Dictionary Inventory", table(["dictionary_id", "dictionary_name", "source_file", "source_location", "extraction_status", "active_values", "archived_values", "used_by_source_properties", "gap_id", "notes"], [
        [q("DICT-001"), "DaData passport department suggestions", "AGENT-NOTES.md", "External context: DaData На Интерфейсе", q("not-needed"), q("not_applicable:integration-suggestions"), q("not_applicable:not-closed-dictionary"), q("SP-011; SP-012"), q("GAP-004"), "ФТ не задает закрытый справочник значений для поля `Кем выдан`; проверяется видимая подсказка/выбор, не closed-set composition."],
    ]))])
    write_markdown(TD / "test-design-applicability-matrix.md", [(1, "Test-design Applicability Matrix", table(["dimension", "applicable", "source_ref", "reason", "linked_atoms", "linked_test_cases", "gap_id"], [
        [q("conditional-visibility"), q("yes"), q("SRC-005; SRC-007; SRC-011"), "Conditional field/block visibility is source-backed.", q("ATOM-010; ATOM-016; ATOM-037; ATOM-038"), q("TC-ACPCP-010; TC-ACPCP-015; TC-ACPCP-036; TC-ACPCP-037"), q("none")],
        [q("numeric"), q("yes"), q("SRC-002; SRC-003; SRC-004; SRC-014; SRC-015"), "Digit-only class is source-backed; invalid enforcement mechanics are not.", q("ATOM-053; ATOM-054; ATOM-055"), q("TC-ACPCP-049; TC-ACPCP-050"), q("GAP-003")],
        [q("format"), q("yes"), q("SRC-002; SRC-003; SRC-004; SRC-014; SRC-015"), "Exact field lengths are source-backed as field format checks.", q("ATOM-004; ATOM-006; ATOM-008; ATOM-047; ATOM-049"), q("TC-ACPCP-004; TC-ACPCP-006; TC-ACPCP-008; TC-ACPCP-044; TC-ACPCP-046"), q("GAP-003")],
        [q("date-time"), q("yes"), q("SRC-008; GAP-001"), "Closed clarification defines passport issue date boundaries.", q("ATOM-019; ATOM-020; ATOM-021; ATOM-022; ATOM-023; ATOM-024; ATOM-025; ATOM-026; ATOM-027; ATOM-028; ATOM-029"), q("TC-ACPCP-018; TC-ACPCP-020; TC-ACPCP-021; TC-ACPCP-022; TC-ACPCP-024; TC-ACPCP-025; TC-ACPCP-026; TC-ACPCP-028; TC-ACPCP-029; TC-ACPCP-030; TC-ACPCP-031"), q("none")],
        [q("dependency"), q("yes"), q("SRC-011; SRC-012; SRC-013; GAP-002"), "Previous passport block is action-created and limited to the last previous passport.", q("ATOM-037; ATOM-038; ATOM-039; ATOM-040; ATOM-041; ATOM-042; ATOM-043; ATOM-044"), q("TC-ACPCP-036; TC-ACPCP-037; TC-ACPCP-038; TC-ACPCP-039; TC-ACPCP-040; TC-ACPCP-041"), q("GAP-005")],
        [q("integration"), q("unclear"), q("SRC-005; AGENT-NOTES.md"), "DaData visible suggestion is testable, but API details and closed result set are not source-backed.", q("ATOM-011; ATOM-012"), q("TC-ACPCP-011; TC-ACPCP-012"), q("GAP-004")],
    ]))])
    write_markdown(TD / "risk-priority-map.md", [(1, "Risk / Priority Map", table(["atom_id", "coverage_dimension", "impact", "likelihood", "risk_score", "risk_level", "risk_factors", "source_ref", "required_priority", "linked_test_cases", "gap_id", "residual_risk_decision", "rationale"], [
        [q("ATOM-020"), q("date-time"), q("5"), q("4"), q("20"), q("high"), q("critical-business-validation"), q("SRC-008; BSR 92"), q("High"), q("TC-ACPCP-020"), q("none_required:covered"), q("none"), "Under-14 issue date blocks saving."],
        [q("ATOM-023"), q("date-time"), q("5"), q("4"), q("20"), q("high"), q("critical-business-validation"), q("SRC-008; BSR 92"), q("High"), q("TC-ACPCP-024"), q("none_required:covered"), q("none"), "Expired passport blocks saving."],
        [q("ATOM-028"), q("date-time"), q("5"), q("4"), q("20"), q("high"), q("critical-business-validation"), q("SRC-008; BSR 93"), q("High"), q("TC-ACPCP-030"), q("none_required:covered"), q("none"), "Future issue date blocks saving."],
        [q("ATOM-053"), q("numeric"), q("4"), q("4"), q("16"), q("high"), q("critical-business-validation"), q("SRC-002; SRC-003; SRC-004"), q("High"), q("TC-ACPCP-049"), q("GAP-003"), q("accepted-with-gap"), "Positive numeric class is covered; invalid UI mechanics remain gap."],
        [q("ATOM-054"), q("numeric"), q("4"), q("4"), q("16"), q("high"), q("critical-business-validation"), q("SRC-014; SRC-015"), q("High"), q("TC-ACPCP-050"), q("GAP-003"), q("accepted-with-gap"), "Previous-passport numeric class is covered; invalid UI mechanics remain gap."],
        [q("ATOM-043"), q("table-list"), q("4"), q("3"), q("12"), q("medium"), q("data-loss"), q("SRC-013; GAP-002"), q("High"), q("TC-ACPCP-041"), q("GAP-005"), q("accepted-with-gap"), "Delete behavior is covered for visible block; extra fields remain gap."],
    ]))])
    review_rows = [[q(item), q("pass"), q("info"), q("all"), "Remediation evidence in source normalization, TDDT, COT, plan, gaps and TC set.", q("none_required:pass"), q("no")] for item in [
        "decision-table-classification", "ledger-plan-alignment", "coverage-class-completeness", "numeric-length-boundaries", "unsupported-ui-mechanism", "mask-format-coverage", "dictionary-closed-set", "conditional-branches", "negative-fixture-isolation", "applicability-linked-tc-semantics", "gap-specificity", "gap-admissibility", "internal-observability", "metadata-only-exclusion", "tc-mapping-atomicity", "ready-for-tc-writing"
    ]]
    write_markdown(TD / "test-design-review.md", [(1, "Test Design Review", table(["review_item", "status", "severity", "affected_package", "evidence", "required_action", "blocks_ready_for_review"], review_rows))])


def main() -> int:
    rewrite_canonical()
    write_artifacts()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
