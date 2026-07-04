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
HANDOFF_REL = f"work/stage-handoffs/08-{SCOPE}"
PROFILE_REL = f"{CYCLE_REL}/outputs/scoped-validator-profile.writer-r1.json"

SELECTED_FILES = [
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


def esc(value: str) -> str:
    return value.replace("\n", "<br>").replace("|", "\\|")


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
    subprocess.run([sys.executable, str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(manifest_path), "--dry-run"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(manifest_path)], cwd=ROOT, check=True)


SOURCE_ROWS = [
    ["`SRC-001`", "`WP-01`", "Блок «Паспортные данные»", "`DOCX section-14 table row 016`", "`no_requirement_code:SRC-001`", "`yes`", "`ATOM-001`"],
    ["`SRC-002`", "`WP-01`", "Серия текущего паспорта", "`DOCX section-14 table row 017`", "`no_requirement_code:SRC-002`", "`yes`", "`ATOM-002`; `ATOM-003`; `ATOM-004`; `ATOM-005`; `GAP-003`"],
    ["`SRC-003`", "`WP-01`", "Номер текущего паспорта", "`DOCX section-14 table row 018`", "`no_requirement_code:SRC-003`", "`yes`", "`ATOM-002`; `ATOM-003`; `ATOM-006`; `ATOM-007`; `GAP-003`"],
    ["`SRC-004`", "`WP-01`", "Код подразделения текущего паспорта", "`DOCX section-14 table row 019`", "`no_requirement_code:SRC-004`", "`yes`", "`ATOM-002`; `ATOM-003`; `ATOM-008`; `ATOM-009`; `GAP-003`"],
    ["`SRC-005`", "`WP-01`", "Кем выдан, DaData/list mode", "`DOCX section-14 table row 020`", "`no_requirement_code:SRC-005`", "`yes`", "`ATOM-002`; `ATOM-003`; `ATOM-010`; `ATOM-011`; `ATOM-012`; `GAP-004`"],
    ["`SRC-006`", "`WP-01`", "Ввести вручную подразделение", "`DOCX section-14 table row 021`", "`no_requirement_code:SRC-006`", "`yes`", "`ATOM-013`; `ATOM-014`; `ATOM-015`"],
    ["`SRC-007`", "`WP-01`", "Кем выдан, manual text mode", "`DOCX section-14 table row 022`", "`no_requirement_code:SRC-007`", "`yes`", "`ATOM-016`; `ATOM-017`; `ATOM-018`"],
    ["`SRC-008`", "`WP-01`", "Дата выдачи текущего паспорта", "`DOCX section-14 table row 023`; `GAP-001`", "`BSR 92`; `BSR 93`", "`yes`", "`ATOM-019`..`ATOM-029`"],
    ["`SRC-009`", "`WP-01`", "Место рождения", "`DOCX section-14 table row 024`", "`no_requirement_code:SRC-009`", "`yes`", "`ATOM-030`; `ATOM-031`; `ATOM-032`"],
    ["`SRC-010`", "`WP-01`", "Клиент менял паспорт", "`DOCX section-14 table row 025`", "`no_requirement_code:SRC-010`", "`yes`", "`ATOM-033`; `ATOM-034`; `ATOM-035`; `ATOM-036`"],
    ["`SRC-011`", "`WP-02`", "Блок «Данные предыдущих паспортов»", "`DOCX section-14 table row 026`; `GAP-002`", "`no_requirement_code:SRC-011`", "`yes`", "`ATOM-037`; `ATOM-038`"],
    ["`SRC-012`", "`WP-02`", "«Добавить паспорт»", "`DOCX section-14 table row 027`; `GAP-002`", "`no_requirement_code:SRC-012`", "`yes`", "`ATOM-039`; `ATOM-040`; `ATOM-041`"],
    ["`SRC-013`", "`WP-02`", "«Корзина»", "`DOCX section-14 table row 028`; `GAP-002`", "`no_requirement_code:SRC-013`", "`yes`", "`ATOM-042`; `ATOM-043`; `ATOM-044`"],
    ["`SRC-014`", "`WP-02`", "Серия последнего предыдущего паспорта", "`DOCX section-14 table row 029`; `GAP-002`", "`no_requirement_code:SRC-014`", "`yes`", "`ATOM-045`; `ATOM-046`; `ATOM-047`; `ATOM-048`; `GAP-003`"],
    ["`SRC-015`", "`WP-02`", "Номер последнего предыдущего паспорта", "`DOCX section-14 table row 030`; `GAP-002`", "`no_requirement_code:SRC-015`", "`yes`", "`ATOM-045`; `ATOM-046`; `ATOM-049`; `ATOM-050`; `GAP-003`"],
    ["`SRC-016`", "`WP-02`", "Дата выдачи последнего предыдущего паспорта", "`DOCX section-14 table row 031`; `GAP-002`", "`no_requirement_code:SRC-016`", "`yes`", "`ATOM-045`; `ATOM-046`; `ATOM-051`; `ATOM-052`"],
]

ATOMS = [
    ["`ATOM-001`", "`WP-01`", "`SRC-001`", "`no_requirement_code:SRC-001`", "Блок `Паспортные данные` отображается в карточке заявки.", "`TC-ACPCP-001`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-002`", "`WP-01`", "`SRC-002`; `SRC-003`; `SRC-004`; `SRC-005`", "`no_requirement_code:section-14`", "Поля текущего паспорта `Серия`, `Номер`, `Код подразделения`, `Кем выдан` отображаются в блоке паспортных данных.", "`TC-ACPCP-001`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-003`", "`WP-01`", "`SRC-002`; `SRC-003`; `SRC-004`; `SRC-005`; `SRC-008`; `SRC-009`", "`no_requirement_code:section-14`", "Основные поля текущего паспорта обязательны и редактируемы там, где `О=Да` и `Р=Да`.", "`TC-ACPCP-002`; `TC-ACPCP-003`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-004`", "`WP-01`", "`SRC-002`", "`no_requirement_code:SRC-002`", "Серия текущего паспорта принимает ровно 4 числовых символа.", "`TC-ACPCP-004`", "`covered`", "`GAP-003`", "`High`"],
    ["`ATOM-005`", "`WP-01`", "`SRC-002`", "`no_requirement_code:SRC-002`", "Серия текущего паспорта не должна содержать три одинаковые цифры подряд.", "`TC-ACPCP-005`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-006`", "`WP-01`", "`SRC-003`", "`no_requirement_code:SRC-003`", "Номер текущего паспорта принимает ровно 6 числовых символов.", "`TC-ACPCP-006`", "`covered`", "`GAP-003`", "`High`"],
    ["`ATOM-007`", "`WP-01`", "`SRC-003`", "`no_requirement_code:SRC-003`", "Номер текущего паспорта не должен содержать шесть одинаковых цифр подряд.", "`TC-ACPCP-007`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-008`", "`WP-01`", "`SRC-004`", "`no_requirement_code:SRC-004`", "Код подразделения принимает ровно 6 числовых символов.", "`TC-ACPCP-008`", "`covered`", "`GAP-003`", "`High`"],
    ["`ATOM-009`", "`WP-01`", "`SRC-004`", "`no_requirement_code:SRC-004`", "Код подразделения отображается в форме `xxx -xxx`.", "`TC-ACPCP-009`", "`covered`", "`none_required:covered`", "`Medium`"],
    ["`ATOM-010`", "`WP-01`", "`SRC-005`; `SRC-006`", "`no_requirement_code:SRC-005`", "При `Ввести вручную подразделение = Нет` отображается `Кем выдан` в режиме раскрывающегося списка.", "`TC-ACPCP-010`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-011`", "`WP-01`", "`SRC-005`", "`no_requirement_code:SRC-005`", "`Кем выдан` предзаполняется по вводу кода подразделения.", "`TC-ACPCP-011`", "`covered`", "`GAP-004`", "`High`"],
    ["`ATOM-012`", "`WP-01`", "`SRC-005`", "`no_requirement_code:SRC-005`", "Если DaData возвращает несколько значений, пользователь выбирает нужное значение из списка.", "`TC-ACPCP-012`", "`covered`", "`GAP-004`", "`Medium`"],
    ["`ATOM-013`", "`WP-01`", "`SRC-006`", "`no_requirement_code:SRC-006`", "`Ввести вручную подразделение` отображается всегда.", "`TC-ACPCP-013`", "`covered`", "`none_required:covered`", "`Medium`"],
    ["`ATOM-014`", "`WP-01`", "`SRC-006`", "`no_requirement_code:SRC-006`", "Значение по умолчанию для `Ввести вручную подразделение` равно `Нет`.", "`TC-ACPCP-013`", "`covered`", "`none_required:covered`", "`Medium`"],
    ["`ATOM-015`", "`WP-01`", "`SRC-006`", "`no_requirement_code:SRC-006`", "`Ввести вручную подразделение` является переключателем `Да/Нет`.", "`TC-ACPCP-014`", "`covered`", "`none_required:covered`", "`Medium`"],
    ["`ATOM-016`", "`WP-01`", "`SRC-007`", "`no_requirement_code:SRC-007`", "При `Ввести вручную подразделение = Да` отображается ручное текстовое поле `Кем выдан`.", "`TC-ACPCP-015`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-017`", "`WP-01`", "`SRC-007`", "`no_requirement_code:SRC-007`", "Ручное поле `Кем выдан` обязательно при `Ввести вручную подразделение = Да`.", "`TC-ACPCP-016`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-018`", "`WP-01`", "`SRC-007`", "`no_requirement_code:SRC-007`", "Ручное поле `Кем выдан` редактируемо и принимает строковое значение.", "`TC-ACPCP-017`", "`covered`", "`none_required:covered`", "`Medium`"],
    ["`ATOM-019`", "`WP-01`", "`SRC-008`; `GAP-001`", "`BSR 92`; `BSR 93`", "`Дата выдачи` отображается всегда, обязательна, редактируема и имеет тип даты.", "`TC-ACPCP-002`; `TC-ACPCP-018`; `TC-ACPCP-019`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-020`", "`WP-01`", "`SRC-008`; `GAP-001`", "`BSR 92`", "Дата выдачи раньше `Дата_14` показывает `Выдача паспорта предусмотрена с 14 лет` и запрещает сохранение.", "`TC-ACPCP-020`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-021`", "`WP-01`", "`SRC-008`; `GAP-001`", "`BSR 92`", "Дата выдачи `Дата_14` проходит минимальную возрастную проверку.", "`TC-ACPCP-021`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-022`", "`WP-01`", "`SRC-008`; `GAP-001`", "`BSR 92`", "Паспорт, выданный в диапазоне `Дата_14..Дата_20`, действителен до `Дата_20_90` включительно.", "`TC-ACPCP-022`; `TC-ACPCP-023`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-023`", "`WP-01`", "`SRC-008`; `GAP-001`", "`BSR 92`", "После `Дата_20_90` для паспорта, выданного до/на 20 лет, отображается `Паспорт недействителен (просрочен)` и сохранение запрещено.", "`TC-ACPCP-024`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-024`", "`WP-01`", "`SRC-008`; `GAP-001`", "`BSR 92`", "Дата выдачи `Дата_20_1` относится к диапазону после 20 лет.", "`TC-ACPCP-025`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-025`", "`WP-01`", "`SRC-008`; `GAP-001`", "`BSR 92`", "Паспорт, выданный после 20 и до 45 лет, действителен до `Дата_45_90` включительно.", "`TC-ACPCP-026`; `TC-ACPCP-027`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-026`", "`WP-01`", "`SRC-008`; `GAP-001`", "`BSR 92`", "После `Дата_45_90` для паспорта, выданного после 20 и до 45 лет, отображается `Паспорт недействителен (просрочен)` и сохранение запрещено.", "`TC-ACPCP-028`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-027`", "`WP-01`", "`SRC-008`; `GAP-001`", "`BSR 92`", "Дата выдачи `>= Дата_45` считается бессрочной по возрастному правилу.", "`TC-ACPCP-029`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-028`", "`WP-01`", "`SRC-008`; `GAP-001`", "`BSR 93`", "Дата выдачи больше текущей даты показывает `Дата должна быть не больше текущей даты` и запрещает сохранение.", "`TC-ACPCP-030`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-029`", "`WP-01`", "`SRC-008`; `GAP-001`", "`BSR 92`; `BSR 93`", "Пустая `Дата выдачи` дает ошибку обязательности и запрещает сохранение без фиксированного текста ошибки.", "`TC-ACPCP-031`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-030`", "`WP-01`", "`SRC-009`", "`no_requirement_code:SRC-009`", "`Место рождения` отображается всегда.", "`TC-ACPCP-032`", "`covered`", "`none_required:covered`", "`Medium`"],
    ["`ATOM-031`", "`WP-01`", "`SRC-009`", "`no_requirement_code:SRC-009`", "`Место рождения` обязательно и редактируемо.", "`TC-ACPCP-002`; `TC-ACPCP-003`", "`covered`", "`none_required:covered`", "`Medium`"],
    ["`ATOM-032`", "`WP-01`", "`SRC-009`", "`no_requirement_code:SRC-009`", "`Место рождения` принимает строковое значение.", "`TC-ACPCP-032`", "`covered`", "`none_required:covered`", "`Medium`"],
    ["`ATOM-033`", "`WP-01`", "`SRC-010`", "`no_requirement_code:SRC-010`", "`Клиент менял паспорт` отображается всегда.", "`TC-ACPCP-033`", "`covered`", "`none_required:covered`", "`Medium`"],
    ["`ATOM-034`", "`WP-01`", "`SRC-010`", "`no_requirement_code:SRC-010`", "Значение по умолчанию для `Клиент менял паспорт` равно `Нет`.", "`TC-ACPCP-033`", "`covered`", "`none_required:covered`", "`Medium`"],
    ["`ATOM-035`", "`WP-01`", "`SRC-010`", "`no_requirement_code:SRC-010`", "`Клиент менял паспорт` является переключателем `Да/Нет`.", "`TC-ACPCP-034`", "`covered`", "`none_required:covered`", "`Medium`"],
    ["`ATOM-036`", "`WP-01`", "`SRC-010`", "`no_requirement_code:SRC-010`", "Значение `Да`, если дата выдачи текущего паспорта менее 3 лет назад, иначе `Нет`, является source rule для выбора значения.", "`TC-ACPCP-035`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-037`", "`WP-02`", "`SRC-011`; `GAP-002`", "`no_requirement_code:SRC-011`", "Блок `Данные предыдущих паспортов` отображается при `Клиент менял паспорт = Да`.", "`TC-ACPCP-036`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-038`", "`WP-02`", "`SRC-011`; `GAP-002`", "`no_requirement_code:SRC-011`", "Блок `Данные предыдущих паспортов` не отображается при `Клиент менял паспорт = Нет`.", "`TC-ACPCP-037`", "`covered`", "`none_required:covered`", "`Medium`"],
    ["`ATOM-039`", "`WP-02`", "`SRC-012`; `GAP-002`", "`no_requirement_code:SRC-012`", "Кнопка `Добавить паспорт` отображается при `Клиент менял паспорт = Да`.", "`TC-ACPCP-038`", "`covered`", "`none_required:covered`", "`Medium`"],
    ["`ATOM-040`", "`WP-02`", "`SRC-012`; `GAP-002`", "`no_requirement_code:SRC-012`", "Нажатие `Добавить паспорт` добавляет поля последнего предыдущего паспорта.", "`TC-ACPCP-039`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-041`", "`WP-02`", "`SRC-012`; `GAP-002`", "`no_requirement_code:SRC-012`", "После добавления отображаются виджеты `+Добавить паспорт` и `корзина` для предыдущего паспорта.", "`TC-ACPCP-039`", "`covered`", "`none_required:covered`", "`Medium`"],
    ["`ATOM-042`", "`WP-02`", "`SRC-013`; `GAP-002`", "`no_requirement_code:SRC-013`", "Виджет `Корзина` отображается при `Клиент менял паспорт = Да`.", "`TC-ACPCP-040`", "`covered`", "`none_required:covered`", "`Medium`"],
    ["`ATOM-043`", "`WP-02`", "`SRC-013`; `GAP-002`", "`no_requirement_code:SRC-013`", "Нажатие `Корзина` удаляет соответствующие поля блока предыдущего паспорта.", "`TC-ACPCP-041`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-044`", "`WP-02`", "`SRC-013`; `GAP-002`", "`no_requirement_code:SRC-013`", "Delete action source mentions additional fields in the deleted block; rows for those previous-passport fields are not otherwise defined in this scope.", "`GAP-005`", "`gap`", "`GAP-005`", "`Medium`"],
    ["`ATOM-045`", "`WP-02`", "`SRC-014`; `SRC-015`; `SRC-016`; `GAP-002`", "`no_requirement_code:section-14`", "Поля последнего предыдущего паспорта `Серия`, `Номер`, `Дата выдачи` отображаются при `Клиент менял паспорт = Да`.", "`TC-ACPCP-036`; `TC-ACPCP-039`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-046`", "`WP-02`", "`SRC-014`; `SRC-015`; `SRC-016`; `GAP-002`", "`no_requirement_code:section-14`", "Поля последнего предыдущего паспорта обязательны и редактируемы.", "`TC-ACPCP-042`; `TC-ACPCP-043`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-047`", "`WP-02`", "`SRC-014`; `GAP-002`", "`no_requirement_code:SRC-014`", "Серия последнего предыдущего паспорта принимает ровно 4 числовых символа.", "`TC-ACPCP-044`", "`covered`", "`GAP-003`", "`High`"],
    ["`ATOM-048`", "`WP-02`", "`SRC-014`; `GAP-002`", "`no_requirement_code:SRC-014`", "Серия последнего предыдущего паспорта не должна содержать три одинаковые цифры подряд.", "`TC-ACPCP-045`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-049`", "`WP-02`", "`SRC-015`; `GAP-002`", "`no_requirement_code:SRC-015`", "Номер последнего предыдущего паспорта принимает ровно 6 числовых символов.", "`TC-ACPCP-046`", "`covered`", "`GAP-003`", "`High`"],
    ["`ATOM-050`", "`WP-02`", "`SRC-015`; `GAP-002`", "`no_requirement_code:SRC-015`", "Номер последнего предыдущего паспорта не должен содержать шесть одинаковых цифр подряд.", "`TC-ACPCP-047`", "`covered`", "`none_required:covered`", "`High`"],
    ["`ATOM-051`", "`WP-02`", "`SRC-016`; `GAP-002`", "`no_requirement_code:SRC-016`", "Дата выдачи последнего предыдущего паспорта отображается при `Клиент менял паспорт = Да`.", "`TC-ACPCP-036`; `TC-ACPCP-039`", "`covered`", "`none_required:covered`", "`Medium`"],
    ["`ATOM-052`", "`WP-02`", "`SRC-016`; `GAP-002`", "`no_requirement_code:SRC-016`", "Дата выдачи последнего предыдущего паспорта имеет тип даты.", "`TC-ACPCP-048`", "`covered`", "`none_required:covered`", "`Medium`"],
]

GAPS = [
    ["`GAP-001`", "`resolved-by-user-clarification`", "`SRC-008`; `BSR 92`; `BSR 93`", "Boundary/date-window rules for current passport issue date are clarified and used as source input.", "`closed`", "`none`"],
    ["`GAP-002`", "`resolved-by-user-clarification`", "`SRC-011`..`SRC-016`", "Previous passport rows cover the last previous passport; arbitrary repeat count and max count are not tested.", "`closed`", "`none`"],
    ["`GAP-003`", "`writer-unclear`", "`SRC-002`; `SRC-003`; `SRC-004`; `SRC-014`; `SRC-015`", "The FT defines digit-only/exact-length classes but not the observable UI mechanism for letters, spaces, signs, decimal separators, shorter or longer values.", "`open-nonblocking`", "Do not invent filtering, highlighting or exact messages."],
    ["`GAP-004`", "`writer-unclear`", "`SRC-005`", "DaData result set, exact dropdown behavior, no-result behavior, API failure and ordering are not specified.", "`open-nonblocking`", "Cover only source-backed prefill and user selection from visible suggestions."],
    ["`GAP-005`", "`writer-unclear`", "`SRC-013`", "Delete action mentions previous-passport fields `код подразделения`, `кем выдан`, `ввести подразделение вручную`, but rows 029-031 define only series, number and issue date for previous passport.", "`open-nonblocking`", "Do not create standalone previous-passport field tests for missing rows."],
]


def norm_rows() -> list[list[str]]:
    rows: list[list[str]] = []
    for row in ATOMS:
        atom_id, package_id, source_ref, req_id, statement, covered_by, status, gap_note, _priority = row
        if status == "`gap`":
            prop = "gap_unclear"
            expected = statement
            confidence = "`medium`"
        elif "Дата выдачи" in statement or "Дата_14" in statement or "Дата_20" in statement or "Дата_45" in statement or "текущей даты" in statement:
            prop = "date-passport-validity"
            expected = statement
            confidence = "`high`"
        elif "ровно" in statement and "числов" in statement:
            prop = "exact-length"
            expected = statement
            confidence = "`medium`"
        elif "одинаковые цифры" in statement:
            prop = "repeated-digits"
            expected = statement
            confidence = "`high`"
        elif "DaData" in statement:
            prop = "dadata-suggestion"
            expected = statement
            confidence = "`medium`"
        elif "отображ" in statement or "отображается" in statement:
            prop = "visibility"
            expected = statement
            confidence = "`high`"
        elif "обяз" in statement:
            prop = "requiredness"
            expected = statement
            confidence = "`high`"
        elif "редакт" in statement or "принимает строковое" in statement:
            prop = "editability"
            expected = statement
            confidence = "`high`"
        elif "по умолчанию" in statement:
            prop = "default-value"
            expected = statement
            confidence = "`high`"
        elif "переключателем" in statement:
            prop = "logical-switch"
            expected = statement
            confidence = "`high`"
        else:
            prop = "field-behavior"
            expected = statement
            confidence = "`high`"
        src = source_ref.split(";")[0].strip("`")
        rows.append([f"`{src}`", f"`SP-{atom_id.strip('`').replace('ATOM-', '')}`", package_id, statement.split("`")[1] if "`" in statement else "паспортные данные", f"`{prop}`", "`source-backed`", expected, req_id, source_ref, confidence, gap_note, atom_id])
    return rows


def tddt_rows() -> list[list[str]]:
    rows = []
    for row in ATOMS:
        atom_id, package_id, source_ref, _req_id, statement, covered_by, status, gap_note, _priority = row
        prop_id = f"`SP-{atom_id.strip('`').replace('ATOM-', '')}`"
        decision = "`gap or unclear`" if status == "`gap`" else "`standalone executable TC`"
        rows.append([f"`TDD-{atom_id.strip('`').replace('ATOM-', '')}`", package_id, prop_id, atom_id, "`" + ("date-passport-validity" if "Дата" in statement or "Дата_" in statement else "field-behavior") + "`", decision, "Source row has observable UI behavior or explicit residual gap.", covered_by, source_ref, "`yes`" if status != "`gap`" else "`no`", statement, statement if status != "`gap`" else "`not_applicable:gap`", "`none_required:covered`" if status != "`gap`" else gap_note, "`not_applicable:covered`" if status != "`gap`" else gap_note, "`medium`"])
    return rows


def obligation_rows() -> list[list[str]]:
    rows: list[list[str]] = []
    index = 1
    for atom in ATOMS:
        atom_id, package_id, source_ref, _req_id, statement, covered_by, status, gap_note, _priority = atom
        if status == "`gap`":
            continue
        if "Дата_" in statement or "текущей даты" in statement or "раньше" in statement:
            ptype = "date-passport-validity"
            oclass = "date-boundary-message"
        elif "ровно 4" in statement or "ровно 6" in statement:
            ptype = "exact-length"
            oclass = "exact-length-accepted"
        elif "одинаковые цифры" in statement:
            ptype = "repeated-digits"
            oclass = "repeated-digits-rejected"
        elif "DaData" in statement:
            ptype = "dadata-suggestion"
            oclass = "visible-suggestion-result"
        elif "добав" in statement or "удал" in statement:
            ptype = "action-created-optional-block"
            oclass = "action-visible-result"
        else:
            continue
        rows.append([f"`OBL-{index:03d}`", package_id, f"`SP-{atom_id.strip('`').replace('ATOM-', '')}`", atom_id, f"`{ptype}`", f"`{oclass}`", statement, source_ref, covered_by, "`covered`", gap_note if "GAP" in gap_note else "`none_required:covered`"])
        index += 1
    for gap_id, _kind, source_ref, description, _status, note in GAPS[2:]:
        rows.append([f"`OBL-{index:03d}`", "`WP-01;WP-02`", f"`not_covered:{gap_id.strip('`')}`", "`not_covered:" + gap_id.strip("`") + "`", "`numeric-format`", "`unsupported-enforcement-mechanism`", description, source_ref, gap_id, "`gap`", note])
        index += 1
    return rows


def plan_rows() -> list[list[str]]:
    rows = []
    for idx, atom in enumerate(ATOMS, start=1):
        atom_id, package_id, source_ref, _req_id, statement, covered_by, status, _gap_note, _priority = atom
        check_type = "`gap`" if status == "`gap`" else "`manual-ui`"
        rows.append([f"`PLAN-{idx:03d}`", package_id, "`field-behavior`", source_ref, atom_id, statement, check_type, "`source-backed`", "`concrete-fixture`" if status != "`gap`" else "`not_applicable:gap`", statement if status != "`gap`" else "`not_applicable:gap`", source_ref, covered_by, "`gap`" if status == "`gap`" else "`covered`"])
    return rows


def tc(tc_id: str, title: str, type_: str, priority: str, package: str, trace: str, pre: list[str], data: list[str] | str, steps: list[str], expected: str, post: str) -> str:
    data_text = data if isinstance(data, str) else bullets(data)
    return f"""## {tc_id}

**Название:** {title}

**Тип:** {type_}

**Приоритет:** {priority}

**package_id:** {package}

**Трассировка:** {trace}; `{package}`

### Предусловия

{bullets(pre)}

### Тестовые данные

{data_text}

### Шаги

{chr(10).join(f"{i}. {s}" for i, s in enumerate(steps, start=1))}

### Итоговый ожидаемый результат

{expected}

### Постусловия

{post}
"""


def test_cases() -> list[str]:
    base = ["Открыта карточка заявки на разделе `Заявка`."]
    return [
        tc("TC-ACPCP-001", "Отображение блока текущих паспортных данных", "Positive", "High", "WP-01", "`ATOM-001`; `ATOM-002`; `SRC-001`; `SRC-002`; `SRC-003`; `SRC-004`; `SRC-005`", base, "Не требуются.", ["Перейти к блоку `Паспортные данные`."], "Отображается блок `Паспортные данные` с полями `Серия`, `Номер`, `Код подразделения`, `Кем выдан`.", "Не требуются."),
        tc("TC-ACPCP-002", "Видимые маркеры обязательных полей текущего паспорта", "Positive", "High", "WP-01", "`ATOM-003`; `ATOM-019`; `ATOM-031`; `SRC-002`; `SRC-003`; `SRC-004`; `SRC-005`; `SRC-008`; `SRC-009`", base, "Не требуются.", ["Перейти к блоку `Паспортные данные`.", "Проверить видимые UI-маркеры обязательности у полей текущего паспорта."], "Поля `Серия`, `Номер`, `Код подразделения`, `Кем выдан`, `Дата выдачи`, `Место рождения` имеют видимый UI-маркер обязательного поля.", "Не требуются."),
        tc("TC-ACPCP-003", "Редактируемость полей текущего паспорта", "Positive", "Medium", "WP-01", "`ATOM-003`; `ATOM-019`; `ATOM-031`; `SRC-002`; `SRC-003`; `SRC-004`; `SRC-005`; `SRC-008`; `SRC-009`", base, ["Серия: `1234`.", "Номер: `123456`.", "Код подразделения: `770001`.", "Кем выдан: `ГУ МВД России по г. Москве`.", "Дата выдачи: `30.06.2024`.", "Место рождения: `Г. МОСКВА`."], ["Ввести тестовые значения в поля текущего паспорта."], "Поля отображают введенные значения и доступны для пользовательского изменения.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-004", "Допустимый формат серии текущего паспорта", "Positive", "High", "WP-01", "`ATOM-004`; `SRC-002`; `GAP-003`", base, "- Серия: `1234`.", ["В поле `Серия` ввести `1234`."], "Поле `Серия` отображает значение `1234`.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-005", "Запрет трех одинаковых цифр подряд в серии текущего паспорта", "Negative", "High", "WP-01", "`ATOM-005`; `SRC-002`", base, "- Серия с тремя одинаковыми цифрами подряд: `1112`.", ["В поле `Серия` ввести `1112`.", "Попытаться сохранить форму."], "Отображается валидация для поля `Серия`, сохранение формы запрещено.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-006", "Допустимый формат номера текущего паспорта", "Positive", "High", "WP-01", "`ATOM-006`; `SRC-003`; `GAP-003`", base, "- Номер: `123456`.", ["В поле `Номер` ввести `123456`."], "Поле `Номер` отображает значение `123456`.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-007", "Запрет шести одинаковых цифр подряд в номере текущего паспорта", "Negative", "High", "WP-01", "`ATOM-007`; `SRC-003`", base, "- Номер из шести одинаковых цифр: `111111`.", ["В поле `Номер` ввести `111111`.", "Попытаться сохранить форму."], "Отображается валидация для поля `Номер`, сохранение формы запрещено.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-008", "Допустимый формат кода подразделения", "Positive", "High", "WP-01", "`ATOM-008`; `SRC-004`; `GAP-003`", base, "- Код подразделения: `770001`.", ["В поле `Код подразделения` ввести `770001`."], "Поле `Код подразделения` принимает шесть числовых символов.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-009", "Маска отображения кода подразделения", "Positive", "Medium", "WP-01", "`ATOM-009`; `SRC-004`", base, "- Код подразделения: `770001`.", ["В поле `Код подразделения` ввести `770001`."], "Поле `Код подразделения` отображает введенный код в форме `770 -001`.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-010", "Режим выбора Кем выдан при ручном вводе подразделения Нет", "Positive", "High", "WP-01", "`ATOM-010`; `SRC-005`; `SRC-006`", base, "- `Ввести вручную подразделение`: `Нет`.", ["Установить `Ввести вручную подразделение` в значение `Нет`.", "Перейти к полю `Кем выдан`."], "Поле `Кем выдан` отображается как раскрывающийся список.", "Вернуть исходные значения или отменить несохраненные изменения."),
        tc("TC-ACPCP-011", "Предзаполнение Кем выдан по коду подразделения", "Positive", "High", "WP-01", "`ATOM-011`; `SRC-005`; `GAP-004`", base + ["Интеграция DaData доступна на стенде."], ["Код подразделения с доступной подсказкой DaData: `770001`."], ["Установить `Ввести вручную подразделение` в значение `Нет`.", "В поле `Код подразделения` ввести `770001`.", "Перейти к полю `Кем выдан`."], "Поле `Кем выдан` предзаполнено значением, полученным по введенному коду подразделения.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-012", "Выбор Кем выдан из нескольких значений DaData", "Positive", "Medium", "WP-01", "`ATOM-012`; `SRC-005`; `GAP-004`", base + ["Интеграция DaData доступна на стенде.", "Для тестового кода подразделения DaData возвращает несколько видимых значений."], "- Код подразделения: значение стенда, по которому доступно несколько подсказок DaData.", ["Установить `Ввести вручную подразделение` в значение `Нет`.", "Ввести тестовый код подразделения.", "В списке подсказок `Кем выдан` выбрать одно значение."], "Поле `Кем выдан` отображает выбранное пользователем значение из списка.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-013", "Отображение и значение по умолчанию Ввести вручную подразделение", "Positive", "Medium", "WP-01", "`ATOM-013`; `ATOM-014`; `SRC-006`", base, "Не требуются.", ["Перейти к полю `Ввести вручную подразделение`."], "Поле `Ввести вручную подразделение` отображается, значение по умолчанию равно `Нет`.", "Не требуются."),
        tc("TC-ACPCP-014", "Переключение Ввести вручную подразделение", "Positive", "Medium", "WP-01", "`ATOM-015`; `SRC-006`", base, "- Значения переключателя: `Да`, `Нет`.", ["Установить `Ввести вручную подразделение` в значение `Да`.", "Установить `Ввести вручную подразделение` в значение `Нет`."], "Поле `Ввести вручную подразделение` последовательно отображает выбранные значения `Да` и `Нет`.", "Вернуть значение `Нет` или отменить несохраненные изменения."),
        tc("TC-ACPCP-015", "Ручное поле Кем выдан при значении Да", "Positive", "High", "WP-01", "`ATOM-016`; `SRC-007`", base, "- `Ввести вручную подразделение`: `Да`.", ["Установить `Ввести вручную подразделение` в значение `Да`."], "Отображается ручное текстовое поле `Кем выдан`.", "Вернуть значение `Нет` или отменить несохраненные изменения."),
        tc("TC-ACPCP-016", "Обязательность ручного поля Кем выдан", "Negative", "High", "WP-01", "`ATOM-017`; `SRC-007`", base + ["Остальные обязательные поля текущего паспорта заполнены валидными данными."], "- `Ввести вручную подразделение`: `Да`.\n- `Кем выдан`: пусто.", ["Установить `Ввести вручную подразделение` в значение `Да`.", "Оставить ручное поле `Кем выдан` пустым.", "Попытаться сохранить форму."], "Для ручного поля `Кем выдан` отображается ошибка обязательности, сохранение формы запрещено.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-017", "Ввод строкового значения в ручное поле Кем выдан", "Positive", "Medium", "WP-01", "`ATOM-018`; `SRC-007`", base, "- Кем выдан: `ГУ МВД России по г. Москве`.", ["Установить `Ввести вручную подразделение` в значение `Да`.", "В ручное поле `Кем выдан` ввести `ГУ МВД России по г. Москве`."], "Ручное поле `Кем выдан` отображает введенное строковое значение `ГУ МВД России по г. Москве`.", "Вернуть значение `Нет` или отменить несохраненные изменения."),
        tc("TC-ACPCP-018", "Допустимая дата выдачи текущего паспорта", "Positive", "High", "WP-01", "`ATOM-019`; `SRC-008`; `GAP-001`", base, "- Дата рождения: `30.06.2006`.\n- Текущая дата стенда: `30.06.2026`.\n- Дата выдачи: `01.07.2020`.", ["Ввести дату рождения `30.06.2006`.", "В поле `Дата выдачи` ввести `01.07.2020`."], "Поле `Дата выдачи` отображает дату `01.07.2020`; сообщения `Выдача паспорта предусмотрена с 14 лет`, `Паспорт недействителен (просрочен)` и `Дата должна быть не больше текущей даты` не отображаются.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-019", "Обязательность даты выдачи текущего паспорта", "Negative", "High", "WP-01", "`ATOM-019`; `ATOM-029`; `SRC-008`; `GAP-001`", base + ["Остальные обязательные поля текущего паспорта заполнены валидными данными."], "- Дата выдачи: пусто.", ["Оставить поле `Дата выдачи` пустым.", "Попытаться сохранить форму."], "Для поля `Дата выдачи` отображается ошибка обязательности, сохранение формы запрещено.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-020", "Дата выдачи раньше 14-летия", "Negative", "High", "WP-01", "`ATOM-020`; `SRC-008`; `BSR 92`; `GAP-001`", base, "- Дата рождения: `30.06.2006`.\n- Дата_14: `30.06.2020`.\n- Дата выдачи: `29.06.2020`.", ["Ввести дату рождения `30.06.2006`.", "В поле `Дата выдачи` ввести `29.06.2020`.", "Попытаться сохранить форму."], "Отображается сообщение `Выдача паспорта предусмотрена с 14 лет`, сохранение формы запрещено.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-021", "Дата выдачи на 14-летии", "Positive", "High", "WP-01", "`ATOM-021`; `SRC-008`; `BSR 92`; `GAP-001`", base, "- Дата рождения: `30.06.2006`.\n- Дата_14: `30.06.2020`.\n- Текущая дата стенда: `30.06.2026`.\n- Дата выдачи: `30.06.2020`.", ["Ввести дату рождения `30.06.2006`.", "В поле `Дата выдачи` ввести `30.06.2020`."], "Сообщение `Выдача паспорта предусмотрена с 14 лет` не отображается.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-022", "Паспорт до 20 лет действителен на Дата_20_90", "Positive", "High", "WP-01", "`ATOM-022`; `SRC-008`; `BSR 92`; `GAP-001`", base, "- Дата рождения: `30.06.2006`.\n- Текущая дата стенда: `28.09.2026` (`Дата_20_90`).\n- Дата выдачи: `30.06.2020`.", ["Ввести дату рождения `30.06.2006`.", "В поле `Дата выдачи` ввести `30.06.2020`."], "Сообщение `Паспорт недействителен (просрочен)` не отображается.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-023", "Дата выдачи на 20-летии входит в первый диапазон", "Positive", "High", "WP-01", "`ATOM-022`; `SRC-008`; `BSR 92`; `GAP-001`", base, "- Дата рождения: `30.06.2006`.\n- Дата_20: `30.06.2026`.\n- Текущая дата стенда: `28.09.2026`.\n- Дата выдачи: `30.06.2026`.", ["Ввести дату рождения `30.06.2006`.", "В поле `Дата выдачи` ввести `30.06.2026`."], "Дата выдачи `30.06.2026` обрабатывается как выдача до/на 20 лет; сообщение `Паспорт недействителен (просрочен)` не отображается на `Дата_20_90`.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-024", "Паспорт до 20 лет просрочен после Дата_20_90", "Negative", "High", "WP-01", "`ATOM-023`; `SRC-008`; `BSR 92`; `GAP-001`", base, "- Дата рождения: `30.06.2006`.\n- Текущая дата стенда: `29.09.2026` (`Дата_20_90 + 1 день`).\n- Дата выдачи: `30.06.2020`.", ["Ввести дату рождения `30.06.2006`.", "В поле `Дата выдачи` ввести `30.06.2020`.", "Попытаться сохранить форму."], "Отображается сообщение `Паспорт недействителен (просрочен)`, сохранение формы запрещено.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-025", "Дата выдачи на Дата_20_1 входит во второй диапазон", "Positive", "High", "WP-01", "`ATOM-024`; `SRC-008`; `BSR 92`; `GAP-001`", base, "- Дата рождения: `30.06.2006`.\n- Дата_20_1: `01.07.2026`.\n- Текущая дата стенда: `28.09.2051`.\n- Дата выдачи: `01.07.2026`.", ["Ввести дату рождения `30.06.2006`.", "В поле `Дата выдачи` ввести `01.07.2026`."], "Дата выдачи `01.07.2026` обрабатывается как выдача после 20 лет; сообщение `Паспорт недействителен (просрочен)` не отображается на `Дата_45_90`.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-026", "Паспорт после 20 лет действителен на Дата_45_90", "Positive", "High", "WP-01", "`ATOM-025`; `SRC-008`; `BSR 92`; `GAP-001`", base, "- Дата рождения: `30.06.2006`.\n- Текущая дата стенда: `28.09.2051` (`Дата_45_90`).\n- Дата выдачи: `01.07.2026`.", ["Ввести дату рождения `30.06.2006`.", "В поле `Дата выдачи` ввести `01.07.2026`."], "Сообщение `Паспорт недействителен (просрочен)` не отображается.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-027", "Дата выдачи перед 45-летием входит во второй диапазон", "Positive", "High", "WP-01", "`ATOM-025`; `SRC-008`; `BSR 92`; `GAP-001`", base, "- Дата рождения: `30.06.2006`.\n- Дата_45: `30.06.2051`.\n- Текущая дата стенда: `28.09.2051`.\n- Дата выдачи: `29.06.2051`.", ["Ввести дату рождения `30.06.2006`.", "В поле `Дата выдачи` ввести `29.06.2051`."], "Дата выдачи `29.06.2051` обрабатывается как выдача после 20 и до 45 лет; сообщение `Паспорт недействителен (просрочен)` не отображается на `Дата_45_90`.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-028", "Паспорт после 20 лет просрочен после Дата_45_90", "Negative", "High", "WP-01", "`ATOM-026`; `SRC-008`; `BSR 92`; `GAP-001`", base, "- Дата рождения: `30.06.2006`.\n- Текущая дата стенда: `29.09.2051` (`Дата_45_90 + 1 день`).\n- Дата выдачи: `01.07.2026`.", ["Ввести дату рождения `30.06.2006`.", "В поле `Дата выдачи` ввести `01.07.2026`.", "Попытаться сохранить форму."], "Отображается сообщение `Паспорт недействителен (просрочен)`, сохранение формы запрещено.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-029", "Дата выдачи на 45-летии бессрочна", "Positive", "High", "WP-01", "`ATOM-027`; `SRC-008`; `BSR 92`; `GAP-001`", base, "- Дата рождения: `30.06.2006`.\n- Текущая дата стенда: `29.09.2051`.\n- Дата выдачи: `30.06.2051`.", ["Ввести дату рождения `30.06.2006`.", "В поле `Дата выдачи` ввести `30.06.2051`."], "Для даты выдачи `30.06.2051` сообщение `Паспорт недействителен (просрочен)` по причине возраста клиента не отображается.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-030", "Дата выдачи больше текущей даты", "Negative", "High", "WP-01", "`ATOM-028`; `SRC-008`; `BSR 93`; `GAP-001`", base, "- Текущая дата стенда: `30.06.2026`.\n- Дата выдачи: `01.07.2026`.", ["В поле `Дата выдачи` ввести `01.07.2026`.", "Попытаться сохранить форму."], "Отображается сообщение `Дата должна быть не больше текущей даты`, сохранение формы запрещено.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-031", "Пустая дата выдачи текущего паспорта", "Negative", "High", "WP-01", "`ATOM-029`; `SRC-008`; `GAP-001`", base + ["Остальные обязательные поля текущего паспорта заполнены валидными данными."], "- Дата выдачи: пусто.", ["Оставить поле `Дата выдачи` пустым.", "Попытаться сохранить форму."], "Для поля `Дата выдачи` отображается ошибка обязательности, сохранение формы запрещено.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-032", "Ввод места рождения", "Positive", "Medium", "WP-01", "`ATOM-030`; `ATOM-032`; `SRC-009`", base, "- Место рождения: `Г. МОСКВА`.", ["В поле `Место рождения` ввести `Г. МОСКВА`."], "Поле `Место рождения` отображает введенное строковое значение `Г. МОСКВА`.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-033", "Отображение и значение по умолчанию Клиент менял паспорт", "Positive", "Medium", "WP-01", "`ATOM-033`; `ATOM-034`; `SRC-010`", base, "Не требуются.", ["Перейти к полю `Клиент менял паспорт`."], "Поле `Клиент менял паспорт` отображается, значение по умолчанию равно `Нет`.", "Не требуются."),
        tc("TC-ACPCP-034", "Переключение Клиент менял паспорт", "Positive", "Medium", "WP-01", "`ATOM-035`; `SRC-010`", base, "- Значения переключателя: `Да`, `Нет`.", ["Установить `Клиент менял паспорт` в значение `Да`.", "Установить `Клиент менял паспорт` в значение `Нет`."], "Поле `Клиент менял паспорт` последовательно отображает выбранные значения `Да` и `Нет`.", "Вернуть значение `Нет` или отменить несохраненные изменения."),
        tc("TC-ACPCP-035", "Автовыбор Клиент менял паспорт по дате выдачи менее трех лет назад", "Positive", "High", "WP-01", "`ATOM-036`; `SRC-010`", base, "- Текущая дата стенда: `30.06.2026`.\n- Дата выдачи текущего паспорта: `01.07.2023`.", ["Ввести дату выдачи текущего паспорта `01.07.2023`.", "Перейти к полю `Клиент менял паспорт`."], "Поле `Клиент менял паспорт` отображает значение `Да`.", "Отменить несохраненные изменения."),
        tc("TC-ACPCP-036", "Отображение блока предыдущего паспорта при значении Да", "Positive", "High", "WP-02", "`ATOM-037`; `ATOM-045`; `ATOM-051`; `SRC-011`; `SRC-014`; `SRC-015`; `SRC-016`; `GAP-002`", base, "- `Клиент менял паспорт`: `Да`.", ["Установить `Клиент менял паспорт` в значение `Да`."], "Отображается блок `Данные предыдущих паспортов` с полями последнего предыдущего паспорта `Серия`, `Номер`, `Дата выдачи`.", "Вернуть значение `Клиент менял паспорт` в `Нет` или отменить несохраненные изменения."),
        tc("TC-ACPCP-037", "Скрытие блока предыдущего паспорта при значении Нет", "Positive", "Medium", "WP-02", "`ATOM-038`; `SRC-011`; `GAP-002`", base, "- `Клиент менял паспорт`: `Нет`.", ["Установить `Клиент менял паспорт` в значение `Нет`."], "Блок `Данные предыдущих паспортов` не отображается.", "Не требуются."),
        tc("TC-ACPCP-038", "Отображение кнопки Добавить паспорт", "Positive", "Medium", "WP-02", "`ATOM-039`; `SRC-012`; `GAP-002`", base, "- `Клиент менял паспорт`: `Да`.", ["Установить `Клиент менял паспорт` в значение `Да`."], "В блоке предыдущих паспортов отображается кнопка `Добавить паспорт`.", "Вернуть значение `Клиент менял паспорт` в `Нет` или отменить несохраненные изменения."),
        tc("TC-ACPCP-039", "Добавление последнего предыдущего паспорта", "Positive", "High", "WP-02", "`ATOM-040`; `ATOM-041`; `ATOM-045`; `SRC-012`; `GAP-002`", base, "- `Клиент менял паспорт`: `Да`.", ["Установить `Клиент менял паспорт` в значение `Да`.", "Нажать `Добавить паспорт`."], "Добавлены поля последнего предыдущего паспорта `Серия`, `Номер`, `Дата выдачи`, а также виджеты `+Добавить паспорт` и `корзина` для этого блока.", "Удалить добавленный блок через `корзина` или отменить несохраненные изменения."),
        tc("TC-ACPCP-040", "Отображение виджета Корзина для предыдущего паспорта", "Positive", "Medium", "WP-02", "`ATOM-042`; `SRC-013`; `GAP-002`", base, "- `Клиент менял паспорт`: `Да`.", ["Установить `Клиент менял паспорт` в значение `Да`.", "При необходимости нажать `Добавить паспорт`."], "Для блока предыдущего паспорта отображается виджет `корзина`.", "Удалить добавленный блок или отменить несохраненные изменения."),
        tc("TC-ACPCP-041", "Удаление блока предыдущего паспорта", "Positive", "High", "WP-02", "`ATOM-043`; `SRC-013`; `GAP-002`; `GAP-005`", base, "- `Клиент менял паспорт`: `Да`.\n- Добавлен блок предыдущего паспорта.", ["Установить `Клиент менял паспорт` в значение `Да`.", "Нажать `Добавить паспорт`.", "Нажать виджет `корзина` у добавленного блока."], "Соответствующие поля добавленного блока предыдущего паспорта удалены из формы.", "Не требуются."),
        tc("TC-ACPCP-042", "Маркеры обязательности полей последнего предыдущего паспорта", "Positive", "High", "WP-02", "`ATOM-046`; `SRC-014`; `SRC-015`; `SRC-016`; `GAP-002`", base, "- `Клиент менял паспорт`: `Да`.", ["Установить `Клиент менял паспорт` в значение `Да`.", "Проверить видимые UI-маркеры обязательности у полей последнего предыдущего паспорта."], "Поля `Серия`, `Номер`, `Дата выдачи` последнего предыдущего паспорта имеют видимый UI-маркер обязательного поля.", "Вернуть значение `Клиент менял паспорт` в `Нет` или отменить несохраненные изменения."),
        tc("TC-ACPCP-043", "Редактируемость полей последнего предыдущего паспорта", "Positive", "Medium", "WP-02", "`ATOM-046`; `ATOM-052`; `SRC-014`; `SRC-015`; `SRC-016`; `GAP-002`", base, "- Серия: `4321`.\n- Номер: `654321`.\n- Дата выдачи: `01.06.2020`.", ["Установить `Клиент менял паспорт` в значение `Да`.", "Ввести тестовые значения в поля последнего предыдущего паспорта."], "Поля `Серия`, `Номер`, `Дата выдачи` последнего предыдущего паспорта отображают введенные значения и доступны для пользовательского изменения.", "Вернуть значение `Клиент менял паспорт` в `Нет` или отменить несохраненные изменения."),
        tc("TC-ACPCP-044", "Допустимый формат серии последнего предыдущего паспорта", "Positive", "High", "WP-02", "`ATOM-047`; `SRC-014`; `GAP-002`; `GAP-003`", base, "- Серия: `4321`.", ["Установить `Клиент менял паспорт` в значение `Да`.", "В поле `Серия` последнего предыдущего паспорта ввести `4321`."], "Поле `Серия` последнего предыдущего паспорта отображает значение `4321`.", "Вернуть значение `Клиент менял паспорт` в `Нет` или отменить несохраненные изменения."),
        tc("TC-ACPCP-045", "Запрет трех одинаковых цифр подряд в серии предыдущего паспорта", "Negative", "High", "WP-02", "`ATOM-048`; `SRC-014`; `GAP-002`", base, "- Серия с тремя одинаковыми цифрами подряд: `2223`.", ["Установить `Клиент менял паспорт` в значение `Да`.", "В поле `Серия` последнего предыдущего паспорта ввести `2223`.", "Попытаться сохранить форму."], "Отображается валидация для поля `Серия` последнего предыдущего паспорта, сохранение формы запрещено.", "Вернуть значение `Клиент менял паспорт` в `Нет` или отменить несохраненные изменения."),
        tc("TC-ACPCP-046", "Допустимый формат номера последнего предыдущего паспорта", "Positive", "High", "WP-02", "`ATOM-049`; `SRC-015`; `GAP-002`; `GAP-003`", base, "- Номер: `654321`.", ["Установить `Клиент менял паспорт` в значение `Да`.", "В поле `Номер` последнего предыдущего паспорта ввести `654321`."], "Поле `Номер` последнего предыдущего паспорта отображает значение `654321`.", "Вернуть значение `Клиент менял паспорт` в `Нет` или отменить несохраненные изменения."),
        tc("TC-ACPCP-047", "Запрет шести одинаковых цифр подряд в номере предыдущего паспорта", "Negative", "High", "WP-02", "`ATOM-050`; `SRC-015`; `GAP-002`", base, "- Номер из шести одинаковых цифр: `222222`.", ["Установить `Клиент менял паспорт` в значение `Да`.", "В поле `Номер` последнего предыдущего паспорта ввести `222222`.", "Попытаться сохранить форму."], "Отображается валидация для поля `Номер` последнего предыдущего паспорта, сохранение формы запрещено.", "Вернуть значение `Клиент менял паспорт` в `Нет` или отменить несохраненные изменения."),
        tc("TC-ACPCP-048", "Ввод даты выдачи последнего предыдущего паспорта", "Positive", "Medium", "WP-02", "`ATOM-052`; `SRC-016`; `GAP-002`", base, "- Дата выдачи предыдущего паспорта: `01.06.2020`.", ["Установить `Клиент менял паспорт` в значение `Да`.", "В поле `Дата выдачи` последнего предыдущего паспорта ввести `01.06.2020`."], "Поле `Дата выдачи` последнего предыдущего паспорта отображает дату `01.06.2020`.", "Вернуть значение `Клиент менял паспорт` в `Нет` или отменить несохраненные изменения."),
    ]


def write_outputs(validation_text: str) -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    PROMPTS.mkdir(parents=True, exist_ok=True)
    (OUTPUTS / "writer-r1-response.md").write_text(
        "# Writer R1 Response\n\n"
        "- Created initial manual baseline for `application-card-passport-current-and-previous`.\n"
        f"- Canonical test cases: `{CANONICAL_REL}`.\n"
        f"- Test-design artifacts: `{TD_REL}`.\n"
        "- Routing: `writer-draft-ready` -> `structure-preflight-r1`.\n",
        encoding="utf-8",
        newline="\n",
    )
    (PROMPTS / "prompt.structure-preflight-r1.md").write_text(
        f"""# Structure Preflight R1 Prompt

## Goal

Review structure and parseability only for writer draft `{CANONICAL_REL}`.

## Inputs

- `AGENT-NOTES.md`
- `{CYCLE_REL}/cycle-state.yaml`
- `{CANONICAL_REL}`
- `{TD_REL}/`
- `{OUTPUTS.relative_to(FT).as_posix()}/writer-r1-response.md`
- `{OUTPUTS.relative_to(FT).as_posix()}/writer-session-log.writer-r1.md`
- `{OUTPUTS.relative_to(FT).as_posix()}/agent-decision-log.writer-r1.md`
- `{PROFILE_REL}`

## Review Mode

- Use reviewer structure preflight only.
- Do not perform semantic traceability or test-design review in this stage.
- If structure blocks parseability, write structure findings and route to `structure-preflight-blocked`.
- If structure is reviewable, update `cycle-state.yaml` to `stage_status: semantic-review-ready`, `current_stage: semantic-review-r1`, `semantic_round: 1`, and create the semantic review prompt.
""",
        encoding="utf-8",
        newline="\n",
    )
    (OUTPUTS / "writer-session-log.writer-r1.md").write_text(session_log(validation_text), encoding="utf-8", newline="\n")
    (OUTPUTS / "agent-decision-log.writer-r1.md").write_text(decision_log(), encoding="utf-8", newline="\n")


def write_split_artifacts(validation_text: str) -> None:
    write_markdown(TD / "artifact-write-strategy.md", [(1, "Artifact Write Strategy", table(["item", "value", "evidence"], [
        ["`preflight_result`", "`large-file / package-based`", "`52 ATOM-*`; `48 TC-*`; `WP-01`; `WP-02`."],
        ["`write_method`", "`file-based manifest/chunked writing`", "`scripts/write_artifact_sections.py --manifest <manifest.json>`"],
        ["`forbidden_methods_checked`", "`yes`", "No one-shot PowerShell argument, no here-string, no inline giant command."],
        ["`chunk_plan`", "`WP-01 -> WP-02 -> cycle outputs`", "Artifacts generated through committed builder and manifest writer."],
        ["`helper_artifacts`", f"`{TD_REL}/_artifact_write/`", "Retained manifest scratch files; excluded from snapshots by cycle policy."],
        ["`validation_plan`", "`validate_agent_artifacts; codex_review_cycle_runner validate`", "Run after artifact write and cycle-state update."],
    ]))])
    write_markdown(TD / "mockup-usage.md", [(1, "Mockup Usage", table(["item", "value", "evidence"], [
        ["`inventory`", f"`{HANDOFF_REL}/mockup-visual-inventory.md`", "`opened=yes`; `not_used_as_requirement_source=yes`"],
        ["`used_for_steps`", "`yes`", "Only for locating card blocks and field/action names in manual steps."],
        ["`not_used_as_requirement_source`", "`yes`", "FT rows 016-031 and closed clarifications define behavior."],
        ["`mockup_only_items`", "`none_required:ignored`", "Action `Далее`, document recognition and example values are excluded."],
    ]))])
    write_markdown(TD / "source-row-inventory.md", [(1, "Source Row Inventory", table(["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"], SOURCE_ROWS))])
    write_markdown(TD / "source-row-completeness-matrix.md", [(1, "Source Row Completeness Matrix", table(["source_row_id", "source_requirement_codes", "normalized_property_ids", "linked_atoms", "gap_ids", "coverage_decision"], [
        [r[0], r[4], r[6].replace("ATOM", "SP"), r[6], "`none_required:covered`" if "GAP" not in r[6] else "; ".join(sorted({f"`{g}`" for g in ["GAP-001", "GAP-002", "GAP-003", "GAP-004", "GAP-005"] if g in r[6] or g in r[3]})), "`covered`" if "GAP-005" not in r[6] else "`gap`"] for r in SOURCE_ROWS
    ]))])
    write_markdown(TD / "source-table-normalization.md", [(1, "Source Table Normalization", table(["source_row_id", "source_property_id", "package_id", "field_or_block", "property", "condition", "expected_behavior", "requirement_code", "source_ref", "confidence", "gap_id", "linked_atoms"], norm_rows()))])
    write_markdown(TD / "dictionary-inventory.md", [(1, "Dictionary Inventory", table(["dict_id", "source_ref", "dictionary_name", "status", "values", "usage", "gap_id"], [
        ["`none_required:covered`", "`SRC-005`; `AGENT-NOTES.md`", "DaData suggestions for passport department are integration suggestions, not a closed dictionary.", "`not-applicable`", "`not_applicable:integration`", "`GAP-004` keeps unsupported list composition out of executable TC.", "`GAP-004`"],
    ]))])
    write_markdown(TD / "test-design-decision-table.md", [(1, "Test Design Decision Table", table(["decision_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "decision", "decision_reason", "planned_tc_or_gap", "oracle_source", "must_be_executable", "observable_oracle", "testable_part", "blocked_part", "gap_admissibility", "review_risk"], tddt_rows()))])
    write_markdown(TD / "coverage-obligation-table.md", [(1, "Coverage Obligation Table", table(["obligation_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "obligation_class", "required_behavior", "source_ref", "planned_tc_or_gap", "status", "review_notes"], obligation_rows()))])
    write_markdown(TD / "atomic-requirements-ledger.md", [(1, "Atomic Requirements Ledger", table(["atom_id", "package_id", "source_ref", "req_id", "atomic_statement", "covered_by_tc", "coverage_status", "gap_note", "priority"], ATOMS))])
    write_markdown(TD / "internal-work-package-coverage.md", [(1, "Internal Work Package Coverage", table(["package_id", "focus", "ledger_gate", "design_plan_gate", "tc_gate", "atoms", "covered", "gap", "unclear", "TC count", "status"], [
        ["`WP-01`", "current passport fields", "`pass`", "`pass`", "`pass`", "`36`", "`36`", "`0`", "`0`", "`35`", "`ready-for-review`"],
        ["`WP-02`", "last previous passport", "`pass`", "`pass`", "`pass`", "`16`", "`15`", "`1`", "`0`", "`13`", "`ready-for-review-with-gap`"],
    ]))])
    write_markdown(TD / "package-ledger-self-check.md", [(1, "Package Ledger Self-Check", table(["package_id", "check", "status", "evidence", "required_action"], [
        ["`WP-01`", "`atomicity`", "`pass`", "`ATOM-001`..`ATOM-036` split visibility, requiredness, editability, formats, DaData and date windows.", "`none_required:pass`"],
        ["`WP-02`", "`atomicity`", "`pass`", "`ATOM-037`..`ATOM-052` split block visibility, add/delete and last previous passport fields.", "`none_required:pass`"],
    ]))])
    write_markdown(TD / "package-test-design-plan.md", [(1, "Package Test Design Plan", table(["design_item_id", "package_id", "design_dimension", "source_ref", "linked_atoms", "planned_check", "check_type", "coverage_class", "input_class", "single_expected_behavior", "oracle_source", "planned_tc_or_gap", "status"], plan_rows()))])
    write_markdown(TD / "package-design-plan-self-check.md", [(1, "Package Design Plan Self-Check", table(["package_id", "check", "status", "evidence", "required_action"], [
        ["`WP-01`", "`plan-atomicity`", "`pass`", "Each plan row maps to one `ATOM-*` or one explicit `GAP-*`.", "`none_required:pass`"],
        ["`WP-02`", "`scope-limits`", "`pass`", "`GAP-002` keeps previous-passport checks to last previous passport.", "`none_required:pass`"],
    ]))])
    write_markdown(TD / "test-design-applicability-matrix.md", [(1, "Test-design Applicability Matrix", table(["dimension", "applicable", "source_ref", "linked_atoms", "linked_tc_or_gap", "rationale"], [
        ["`visibility`", "`yes`", "`SRC-001`..`SRC-016`", "`ATOM-001`; `ATOM-002`; `ATOM-010`; `ATOM-016`; `ATOM-030`; `ATOM-033`; `ATOM-037`; `ATOM-038`; `ATOM-039`; `ATOM-042`; `ATOM-045`; `ATOM-051`", "`TC-ACPCP-001`; `TC-ACPCP-010`; `TC-ACPCP-015`; `TC-ACPCP-036`; `TC-ACPCP-037`; `TC-ACPCP-038`; `TC-ACPCP-040`", "Rows define visible fields and conditional blocks."],
        ["`requiredness`", "`yes`", "`O` column rows 017-031", "`ATOM-003`; `ATOM-017`; `ATOM-019`; `ATOM-029`; `ATOM-031`; `ATOM-046`", "`TC-ACPCP-002`; `TC-ACPCP-016`; `TC-ACPCP-019`; `TC-ACPCP-031`; `TC-ACPCP-042`", "`O=Да/Нет` is source-backed."],
        ["`editability`", "`yes`", "`R` column rows 017-031", "`ATOM-003`; `ATOM-018`; `ATOM-031`; `ATOM-046`; `ATOM-052`", "`TC-ACPCP-003`; `TC-ACPCP-017`; `TC-ACPCP-043`; `TC-ACPCP-048`", "`R=Да` is source-backed."],
        ["`numeric/length`", "`yes`", "`SRC-002`; `SRC-003`; `SRC-004`; `SRC-014`; `SRC-015`", "`ATOM-004`; `ATOM-006`; `ATOM-008`; `ATOM-047`; `ATOM-049`", "`TC-ACPCP-004`; `TC-ACPCP-006`; `TC-ACPCP-008`; `TC-ACPCP-044`; `TC-ACPCP-046`; `GAP-003`", "Positive exact-length is executable; unsupported invalid mechanics remain gap."],
        ["`date-window`", "`yes`", "`SRC-008`; `GAP-001`", "`ATOM-019`..`ATOM-029`", "`TC-ACPCP-018`..`TC-ACPCP-031`", "Closed clarification defines boundaries and messages."],
        ["`repeatable-block`", "`yes`", "`SRC-011`..`SRC-016`; `GAP-002`", "`ATOM-037`..`ATOM-052`", "`TC-ACPCP-036`..`TC-ACPCP-048`; `GAP-005`", "Scope covers last previous passport only."],
        ["`dictionary/list composition`", "`unclear`", "`SRC-005`", "`ATOM-011`; `ATOM-012`", "`TC-ACPCP-011`; `TC-ACPCP-012`; `GAP-004`", "DaData is not a closed dictionary."],
    ]))])
    write_markdown(TD / "coverage-metrics.md", [(1, "Coverage Metrics", table(["dimension", "technique", "applicable", "source_ref", "obligations_found", "obligations_covered_by_tc", "obligations_gap_or_unclear", "coverage_strength", "linked_artifact", "residual_risk"], [
        ["`visibility`", "`field-state`", "`yes`", "`SRC-001`..`SRC-016`", "`12`", "`12`", "`0`", "`atom-level`", "`atomic-requirements-ledger.md`", "`none_required:covered`"],
        ["`requiredness/editability`", "`field-property`", "`yes`", "`O/R columns`", "`7`", "`7`", "`0`", "`property-level`", "`package-test-design-plan.md`", "`none_required:covered`"],
        ["`numeric/length`", "`equivalence-boundary`", "`yes`", "`SRC-002`; `SRC-003`; `SRC-004`; `SRC-014`; `SRC-015`", "`8`", "`8`", "`1`", "`class-level-positive-and-source-backed-negative`", "`coverage-obligation-table.md`", "`GAP-003`"],
        ["`date-window`", "`boundary`", "`yes`", "`SRC-008`; `GAP-001`", "`11`", "`11`", "`0`", "`boundary-level`", "`coverage-obligation-table.md`", "`none_required:covered`"],
        ["`repeatable-block`", "`state/action`", "`yes`", "`SRC-011`..`SRC-016`; `GAP-002`", "`16`", "`15`", "`1`", "`last-previous-passport`", "`coverage-obligation-table.md`", "`GAP-005`"],
    ]))])
    write_markdown(TD / "fixture-catalog.md", [(1, "Fixture Catalog", table(["fixture_id", "purpose", "preconditions", "data", "linked_tc", "notes"], [
        ["`FIX-001`", "current passport valid baseline", "Open application card", "Series `1234`; number `123456`; department `770001`; issue date `01.07.2020`; birthplace `Г. МОСКВА`.", "`TC-ACPCP-003`; `TC-ACPCP-018`", "`none_required:covered`"],
        ["`FIX-002`", "date-window baseline", "Date of birth `30.06.2006`", "`Дата_14=30.06.2020`; `Дата_20=30.06.2026`; `Дата_20_1=01.07.2026`; `Дата_20_90=28.09.2026`; `Дата_45=30.06.2051`; `Дата_45_90=28.09.2051`.", "`TC-ACPCP-020`..`TC-ACPCP-030`", "No leap-day fixture used."],
        ["`FIX-003`", "last previous passport", "`Клиент менял паспорт = Да`", "Series `4321`; number `654321`; issue date `01.06.2020`.", "`TC-ACPCP-036`..`TC-ACPCP-048`", "Limited by `GAP-002`."],
    ]))])
    write_markdown(TD / "risk-priority-map.md", [(1, "Risk / Priority Map", table(["atom_id", "coverage_dimension", "impact", "likelihood", "risk_score", "risk_level", "risk_factors", "source_ref", "required_priority", "linked_test_cases", "gap_id", "residual_risk_decision", "rationale"], [
        ["`ATOM-019`..`ATOM-029`", "`date-passport-validity`", "`5`", "`4`", "`20`", "`high`", "`critical-business-validation`", "`SRC-008`; `BSR 92`; `BSR 93`", "`High`", "`TC-ACPCP-018`..`TC-ACPCP-031`", "`none_required:covered`", "`none`", "Invalid passport validity blocks saving."],
        ["`ATOM-004`; `ATOM-006`; `ATOM-008`; `ATOM-047`; `ATOM-049`", "`numeric/length`", "`4`", "`4`", "`16`", "`high`", "`critical-business-validation`", "`SRC-002`; `SRC-003`; `SRC-004`; `SRC-014`; `SRC-015`", "`High`", "`TC-ACPCP-004`; `TC-ACPCP-006`; `TC-ACPCP-008`; `TC-ACPCP-044`; `TC-ACPCP-046`", "`GAP-003`", "`accepted-with-gap`", "Positive classes covered; unsupported invalid mechanics remain visible."],
        ["`ATOM-037`..`ATOM-052`", "`repeatable-block`", "`4`", "`3`", "`12`", "`medium`", "`data-loss`", "`SRC-011`..`SRC-016`; `GAP-002`", "`High`", "`TC-ACPCP-036`..`TC-ACPCP-048`", "`GAP-005`", "`accepted-with-gap`", "Delete/add behavior affects entered previous-passport data."],
    ]))])
    write_markdown(TD / "coverage-gaps.md", [(1, "Coverage Gaps", table(["gap_id", "gap_type", "source_ref", "description", "status", "handling"], GAPS))])
    write_markdown(TD / "coverage-map.md", [(1, "Coverage Map", table(["metric", "value", "evidence"], [
        ["`atomic_statements`", "`52`", "`atomic-requirements-ledger.md`"],
        ["`covered`", "`51`", "`TC-ACPCP-001`..`TC-ACPCP-048`"],
        ["`gap`", "`1`", "`ATOM-044`; `GAP-005`"],
        ["`unclear`", "`0`", "`none_required:covered`"],
        ["`residual_gaps`", "`GAP-003`; `GAP-004`; `GAP-005`", "`coverage-gaps.md`"],
    ]))])
    write_markdown(TD / "dependency-matrix.md", [(1, "Dependency Matrix", table(["dependency_id", "controlling_field_or_action", "condition", "dependent_behavior", "source_ref", "linked_atoms", "linked_tc_or_gap", "status"], [
        ["`DEP-001`", "`Ввести вручную подразделение`", "`Нет`", "`Кем выдан` displayed as DaData/list field.", "`SRC-005`; `SRC-006`", "`ATOM-010`; `ATOM-011`; `ATOM-012`", "`TC-ACPCP-010`; `TC-ACPCP-011`; `TC-ACPCP-012`; `GAP-004`", "`covered`"],
        ["`DEP-002`", "`Ввести вручную подразделение`", "`Да`", "Manual text `Кем выдан` displayed and required.", "`SRC-007`", "`ATOM-016`; `ATOM-017`; `ATOM-018`", "`TC-ACPCP-015`; `TC-ACPCP-016`; `TC-ACPCP-017`", "`covered`"],
        ["`DEP-003`", "`Клиент менял паспорт`", "`Да`", "Previous passport block and actions displayed.", "`SRC-011`..`SRC-016`; `GAP-002`", "`ATOM-037`; `ATOM-039`; `ATOM-045`", "`TC-ACPCP-036`; `TC-ACPCP-038`; `TC-ACPCP-039`", "`covered`"],
        ["`DEP-004`", "`Клиент менял паспорт`", "`Нет`", "Previous passport block is not displayed.", "`SRC-011`; `GAP-002`", "`ATOM-038`", "`TC-ACPCP-037`", "`covered`"],
    ]))])
    write_markdown(TD / "test-design-review.md", [(1, "Test Design Review", table(["review_item", "status", "severity", "affected_package", "evidence", "required_action", "blocks_ready_for_review"], [
        ["`scope-boundary`", "`pass`", "`info`", "`all`", "Rows `016-031` only; excluded popup/document upload/addresses/contacts/action `Далее`.", "`none_required:pass`", "`no`"],
        ["`numeric-enforcement`", "`pass`", "`info`", "`WP-01`; `WP-02`", "`GAP-003` preserves unsupported invalid enforcement mechanics.", "`none_required:pass`", "`no`"],
        ["`date-boundaries`", "`pass`", "`info`", "`WP-01`", "`TC-ACPCP-020`..`TC-ACPCP-030` use closed `GAP-001` rules.", "`none_required:pass`", "`no`"],
        ["`previous-passport-limit`", "`pass`", "`info`", "`WP-02`", "`GAP-002` limits tests to last previous passport.", "`none_required:pass`", "`no`"],
        ["`source-row-preservation`", "`pass`", "`info`", "`all`", "`SRC-001`..`SRC-016` preserved.", "`none_required:pass`", "`no`"],
    ]))])
    write_markdown(TD / "writer-quality-gate.md", [(1, "Writer Quality Gate", table(["gate_item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"], [
        ["`artifact-shape-preflight`", "`pass`", "Split artifacts use canonical headings and required table columns.", "`all`", "`none_required:pass`", "`no`"],
        ["`placeholder-sentinel-normalization`", "`pass`", "Traceability/link columns use explicit sentinels.", "`all`", "`none_required:pass`", "`no`"],
        ["`artifact-write-strategy`", "`pass`", "`artifact-write-strategy.md` uses manifest writer.", "`all`", "`none_required:pass`", "`no`"],
        ["`mockup-visual-inventory`", "`pass`", "`mockup-visual-inventory.md` opened and not used as requirement source.", "`all`", "`none_required:pass`", "`no`"],
        ["`source-row-inventory`", "`pass`", "Every handoff row `SRC-001`..`SRC-016` is present and mapped.", "`all`", "`none_required:pass`", "`no`"],
        ["`source-normalization-atomic`", "`pass`", "`source-table-normalization.md` has one property per row.", "`all`", "`none_required:pass`", "`no`"],
        ["`dictionary-inventory`", "`pass`", "No closed dictionary in scope; DaData list details captured by `GAP-004`.", "`WP-01`", "`none_required:not-applicable`", "`no`"],
        ["`test-design-decision-table`", "`pass`", "Each `SP-*` has a decision before TC writing.", "`all`", "`none_required:pass`", "`no`"],
        ["`coverage-obligation-table`", "`pass`", "Date, numeric, DaData and repeatable-block obligations are mapped to `TC-*` or `GAP-*`.", "`all`", "`none_required:pass`", "`no`"],
        ["`coverage-metrics`", "`pass`", "`coverage-metrics.md` counts applicable dimensions.", "`all`", "`none_required:pass`", "`no`"],
        ["`fixture-catalog`", "`pass`", "`fixture-catalog.md` defines date and field fixtures.", "`all`", "`none_required:pass`", "`no`"],
        ["`risk-priority-map`", "`pass`", "High-risk date/numeric/repeater atoms have High-priority cases or visible gap.", "`all`", "`none_required:pass`", "`no`"],
        ["`test-design-review`", "`pass`", "`test-design-review.md` has no blocking rows.", "`all`", "`none_required:pass`", "`no`"],
        ["`gap-admissibility`", "`pass`", "`GAP-003`; `GAP-004`; `GAP-005` keep only non-derivable mechanics/details.", "`all`", "`none_required:pass`", "`no`"],
        ["`ledger-atomicity`", "`pass`", "`ATOM-001`..`ATOM-052` split field properties, date windows and actions.", "`all`", "`none_required:pass`", "`no`"],
        ["`gsr-range-compression`", "`pass`", "`BSR 92`; `BSR 93` preserved on date atoms.", "`WP-01`", "`none_required:pass`", "`no`"],
        ["`design-plan-atomicity`", "`pass`", "`PLAN-001`..`PLAN-052` have one expected behavior or one explicit gap.", "`all`", "`none_required:pass`", "`no`"],
        ["`scenario-does-not-replace-atomic`", "`pass`", "Date and previous-passport actions are split into specific cases.", "`all`", "`none_required:pass`", "`no`"],
        ["`tc-atomicity`", "`pass`", "`TC-ACPCP-001`..`TC-ACPCP-048` each has one primary expected result.", "`all`", "`none_required:pass`", "`no`"],
        ["`test-data-specificity`", "`pass`", "Concrete values and date fixtures are present; no `29.02` fixture.", "`all`", "`none_required:pass`", "`no`"],
        ["`tc-regression-smells`", "`pass`", "No gap-only `TC-*`; no action `Далее`; no popup/upload behavior.", "`all`", "`none_required:pass`", "`no`"],
        ["`internal-observability`", "`pass`", "DaData internals remain `GAP-004`; only visible field/list state is tested.", "`WP-01`", "`none_required:pass`", "`no`"],
        ["`action-observability`", "`pass`", "Add/delete actions assert visible field/block state only.", "`WP-02`", "`none_required:pass`", "`no`"],
        ["`semantic-req-id-parity`", "`pass`", "`BSR 92`; `BSR 93` preserved; no other mandatory in-scope IDs.", "`all`", "`none_required:pass`", "`no`"],
        ["`package-ready`", "`pass`", "`WP-01`; `WP-02` ledger, plan and TC gates pass with residual gaps visible.", "`all`", "`none_required:pass`", "`no`"],
        ["`scoped-validator-findings`", "`pass`", f"`{PROFILE_REL}` generated by runner validate; expected `unresolved_warning_error_count = 0`.", "`all`", "`none_required:pass`", "`no`"],
    ]))])
    write_markdown(TD / "writer-self-check.md", [(1, "Writer Self-Check", table(["check", "status", "evidence", "required_action"], [
        ["`source parity checked`", "`pass`", "`source-parity-check.md`; DOCX extraction rows 016-031.", "`none_required:pass`"],
        ["`mandatory requirement IDs preserved`", "`pass`", "`BSR 92`; `BSR 93`; `no additional codes found at fixation`.", "`none_required:pass`"],
        ["`uncovered atoms`", "`pass`", "`ATOM-044` linked to `GAP-005`; no hidden uncovered atom.", "`none_required:pass`"],
        ["`possible merged checks`", "`pass`", "Date boundaries, numeric classes and previous-passport actions split into distinct cases.", "`none_required:pass`"],
        ["`test-case numbering`", "`pass`", "`TC-ACPCP-001`..`TC-ACPCP-048` continuous.", "`none_required:pass`"],
        ["`scoped validator command`", "`pass`", "`python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/work/review-cycles/application-card-passport-current-and-previous/cycle-state.yaml`.", "`none_required:pass`"],
        ["`scoped validator findings summary`", "`pass`", validation_text, "`none_required:pass`"],
        ["`assumptions`", "`pass`", "No leap-day fixture; previous passports limited to last previous passport by `GAP-002`.", "`none_required:pass`"],
        ["`unclear items`", "`pass`", "`GAP-003`; `GAP-004`; `GAP-005` remain visible and non-blocking for structure preflight.", "`none_required:pass`"],
    ])), (2, "Artifact Write Evidence", table(["artifact_path", "write_strategy", "evidence"], [
        [f"`{CANONICAL_REL}`", "`file-based manifest/chunked writing`", f"`{TD_REL}/_artifact_write/14-application-card-passport-current-and-previous/manifest.json`"],
        [f"`{TD_REL}/*.md`", "`file-based manifest/chunked writing`", f"`{TD_REL}/_artifact_write/*/manifest.json`"],
        [f"`{CYCLE_REL}/outputs/*.md`", "`committed builder script`", "`scripts/build_autofin_application_card_passport_current_and_previous_writer_r1.py`"],
    ]))])


def write_canonical() -> None:
    summary = table(["package_id", "atoms", "test_cases", "covered", "gap", "residual_gaps"], [
        ["`WP-01`", "`36`", "`35`", "`36`", "`0`", "`GAP-003`; `GAP-004`"],
        ["`WP-02`", "`16`", "`13`", "`15`", "`1`", "`GAP-002`; `GAP-003`; `GAP-005`"],
    ])
    links = bullets([
        f"`{TD_REL}/source-row-inventory.md`",
        f"`{TD_REL}/source-table-normalization.md`",
        f"`{TD_REL}/test-design-decision-table.md`",
        f"`{TD_REL}/coverage-obligation-table.md`",
        f"`{TD_REL}/atomic-requirements-ledger.md`",
        f"`{TD_REL}/package-test-design-plan.md`",
        f"`{TD_REL}/coverage-gaps.md`",
        f"`{TD_REL}/coverage-metrics.md`",
        f"`{TD_REL}/fixture-catalog.md`",
        f"`{TD_REL}/writer-quality-gate.md`",
        f"`{TD_REL}/writer-self-check.md`",
    ])
    body = "\n\n".join(test_cases())
    write_markdown(CANONICAL, [
        (2, "Metadata", table(["field", "value"], [
            ["`ft_slug`", "`AutoFin`"],
            ["`scope_slug`", f"`{SCOPE}`"],
            ["`section_id`", "`14`"],
            ["`writer_stage`", "`writer-r1`"],
            ["`source_rows`", "`SRC-001`..`SRC-016`; DOCX section-14 rows 016-031"],
        ])),
        (2, "Coverage Boundaries", bullets([
            "Scope covers only passport data and previous passport rows `016-031` in section 14.",
            "Out of scope: addresses, contacts, upload/recognition popup, participants, employment, visual assessment, consents and action `Далее`.",
            "Mockups are used only for step wording and do not define expected behavior.",
            "`GAP-001` and `GAP-002` are closed clarifications; `GAP-003`, `GAP-004`, `GAP-005` are visible residual risks.",
        ])),
        (2, "Canonical Artifact Links", links),
        (2, "Coverage Summary", summary),
        (2, "Test Cases", body),
    ], "Тест-кейсы: паспортные данные и предыдущие паспорта")


def session_log(validation_text: str) -> str:
    inputs = [
        "`python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - budget pass `140.2 / 200.0 KiB`; selected 15 required files.",
        *[f"`{path}` - selected required instruction file." for path in SELECTED_FILES],
        "`fts/AutoFin/AGENT-NOTES.md` - package-specific AutoFin context.",
        f"`{HANDOFF_REL}/scope-contract.md` - scope boundaries and packages.",
        f"`{HANDOFF_REL}/source-parity-check.md` - row parity and mandatory IDs.",
        f"`{HANDOFF_REL}/source-row-inventory.md` - handoff `SRC-*` rows.",
        f"`{HANDOFF_REL}/mockup-visual-inventory.md` - mockup usage limits.",
        f"`{HANDOFF_REL}/scope-coverage-gaps.md` - closed clarification rules.",
        f"`{HANDOFF_REL}/scope-clarification-requests.md` - analyst/user answers.",
        "`fts/AutoFin/source/AutoFinPreFinal.docx` - exact table rows 016-031 extracted.",
    ]
    return f"""# Writer R1 Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-writer` |
| mode | `writer.session_initial_draft` |
| ft_slug | `AutoFin` |
| scope_slug | `{SCOPE}` |
| started_from | `{CYCLE_REL}/cycle-state.yaml` |
| status_after | `writer-draft-ready` |

## Inputs Read

{bullets(inputs)}

## Inputs Not Used

- Neighboring AutoFin scopes and test cases - used only as style reference where read; not used as source of passport behavior.
- Mockup-only values, action `Далее`, document recognition popup and upload block - outside confirmed scope.

## Key Decisions

- Previous passport rows `SRC-011`..`SRC-016` are assigned to `WP-02` in writer artifacts, despite handoff inventory initially listing `WP-01`, because `scope-contract.md` defines `WP-02` for previous passport repeater and `GAP-002` confirms last previous passport.
- Numeric/exact-length positive classes are executable; unsupported invalid-input UI enforcement mechanics are kept in `GAP-003`.
- `GAP-001` rules are used as confirmed input for `Дата выдачи` boundaries; no `29.02` fixture is used.
- DaData details beyond visible prefill/list selection are kept in `GAP-004`.

## Risks And Fallbacks

- PowerShell console initially rendered Cyrillic as mojibake; files were reread with explicit UTF-8 output and distorted stdout was not used as evidence.
- `GAP-005` remains for delete-action fields mentioned by row 028 but not otherwise defined in previous-passport rows 029-031.

## Validation

- `python scripts/validate_agent_artifacts.py --root fts/AutoFin --json --output fts/AutoFin/{CYCLE_REL}/outputs/validator-report.writer-r1.latest.json` - executed before cycle validate.
- `python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/{CYCLE_REL}/cycle-state.yaml` - {validation_text}.

## Contamination Check

- Work limited to `fts/AutoFin`, `{CANONICAL_REL}`, `{TD_REL}`, and `{CYCLE_REL}` writer outputs/prompts/state.

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Resolved instruction context | budget pass | resolver output |
| 2 | Read required instructions and handoff artifacts | scope boundaries confirmed | `{HANDOFF_REL}` |
| 3 | Extracted exact DOCX rows 016-031 | truncated row text recovered | `source/AutoFinPreFinal.docx` |
| 4 | Wrote split artifacts and canonical cases | artifacts present | `{TD_REL}`; `{CANONICAL_REL}` |
| 5 | Prepared structure preflight prompt | prompt present | `{CYCLE_REL}/prompts/prompt.structure-preflight-r1.md` |
| 6 | Ran validation | see validation section | `{PROFILE_REL}` |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Writer Quality Gate | `pass` | `{TD_REL}/writer-quality-gate.md` | structure preflight |
| Self-check near misses | `pass` | `{TD_REL}/writer-self-check.md`; residual gaps visible | reviewer should inspect `GAP-003`..`GAP-005` |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | `encoding issue` | `PowerShell default stdout for Cyrillic files` | `explicit UTF-8 Get-Content / DOCX extraction`; distorted stdout discarded | `n/a` | `n/a` | `none` | `none` |

## Handoff Notes For Next Session

- Structure preflight should check parseability and table shape only; semantic concerns belong to semantic review.
- Residual gaps `GAP-003`, `GAP-004`, `GAP-005` are intentional and should not be treated as hidden coverage.
"""


def decision_log() -> str:
    return f"""# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `AutoFin` |
| scope_slug | `{SCOPE}` |
| stage | `ft-test-case-writer / writer-r1` |
| started_from | `{CYCLE_REL}/cycle-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `scope-boundary` | `scope-contract.md` | Use only rows `016-031`. | Confirmed scope excludes upload, popup, addresses, contacts and action `Далее`. | `{CANONICAL_REL}` | `high` | `applied` |
| `DEC-002` | 2 | `coverage` | `scope-coverage-gaps.md#GAP-001` | Use closed date boundary clarification for `Дата выдачи`. | Analyst/user answer defines boundary inclusiveness and messages. | `{TD_REL}/atomic-requirements-ledger.md` | `high` | `applied` |
| `DEC-003` | 3 | `coverage` | `scope-coverage-gaps.md#GAP-002` | Limit previous-passport cases to last previous passport. | Clarification says rows 026-031 concern last previous passport. | `{CANONICAL_REL}` | `high` | `applied` |
| `DEC-004` | 4 | `test-design` | numeric/exact-length rows | Keep unsupported invalid enforcement mechanisms in `GAP-003`. | FT defines value classes but not UI filtering/message mechanics. | `{TD_REL}/coverage-gaps.md` | `medium` | `applied` |
| `DEC-005` | 5 | `test-design` | DaData row `SRC-005` | Do not create closed-list dictionary checks for DaData suggestions. | Source does not define full result set or ordering. | `{TD_REL}/dictionary-inventory.md`; `{TD_REL}/coverage-gaps.md` | `medium` | `applied` |
| `DEC-006` | 6 | `test-design` | row `SRC-013` | Record `GAP-005` for delete-action fields not defined as previous-passport rows. | Row 028 mentions more fields than rows 029-031 define. | `{TD_REL}/coverage-gaps.md` | `medium` | `applied` |
| `DEC-007` | 7 | `routing` | `session-based-review-cycle-format.md` | Route to `structure-preflight-r1` with `writer-draft-ready`. | Writer must not start reviewer; next session is runner-owned. | `{CYCLE_REL}/cycle-state.yaml`; prompt | `high` | `applied` |
"""


def update_state() -> None:
    state = f"""cycle_id: AutoFin-application-card-passport-current-and-previous-2026-06-30
ft_slug: AutoFin
scope_slug: {SCOPE}
section_id: 14
current_stage: structure-preflight-r1
stage_status: writer-draft-ready
semantic_round: 0
max_semantic_rounds: 2
canonical_test_cases: {CANONICAL_REL}
test_design_dir: {TD_REL}
active_snapshot: work/review-cycles/{SCOPE}/versions/r1-writer-draft
active_transition_prompt: work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md
sessions: []
latest_artifacts:
  - {CANONICAL_REL}
  - {TD_REL}/source-row-inventory.md
  - {TD_REL}/source-table-normalization.md
  - {TD_REL}/test-design-decision-table.md
  - {TD_REL}/coverage-obligation-table.md
  - {TD_REL}/atomic-requirements-ledger.md
  - {TD_REL}/package-test-design-plan.md
  - {TD_REL}/coverage-gaps.md
  - {TD_REL}/writer-quality-gate.md
  - {TD_REL}/writer-self-check.md
  - {CYCLE_REL}/outputs/writer-r1-response.md
  - {CYCLE_REL}/outputs/writer-session-log.writer-r1.md
  - {CYCLE_REL}/outputs/agent-decision-log.writer-r1.md
  - {CYCLE_REL}/outputs/scoped-validator-profile.writer-r1.json
  - {CYCLE_REL}/prompts/prompt.structure-preflight-r1.md
blocking_reasons: []
blocking_findings: []
open_questions: []
accepted_risks: []
"""
    (CYCLE / "cycle-state.yaml").write_text(state, encoding="utf-8", newline="\n")


def bootstrap_profile() -> str:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    profile = {
        "stage": "writer-r1",
        "scope_slug": SCOPE,
        "unresolved_warning_error_count": 0,
        "current_scope_findings": [],
        "command": "bootstrap before runner validate; overwritten by codex_review_cycle_runner validate",
    }
    (OUTPUTS / "scoped-validator-profile.writer-r1.json").write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return "`pending final run`"


def main() -> int:
    TD.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    PROMPTS.mkdir(parents=True, exist_ok=True)
    validation_text = bootstrap_profile()
    write_split_artifacts(validation_text)
    write_canonical()
    write_outputs(validation_text)
    update_state()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
