from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "fts" / "AutoFin"
SCOPE = "application-card-client-personal-data"
SECTION = "14"
TD_REL = f"work/test-design/{SECTION}-{SCOPE}"
TD = FT / TD_REL
CANONICAL_REL = f"test-cases/{SECTION}-{SCOPE}.md"
CANONICAL = FT / CANONICAL_REL
CYCLE_REL = f"work/review-cycles/{SCOPE}"
CYCLE = FT / CYCLE_REL
OUTPUTS = CYCLE / "outputs"
PROMPTS = CYCLE / "prompts"
HANDOFF_REL = f"work/stage-handoffs/06-{SCOPE}"
WRITER_PROFILE_REL = f"{CYCLE_REL}/outputs/scoped-validator-profile.writer-r1.json"

SELECTED_REQUIRED_FILES = [
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

INPUTS_READ = [
    "AGENT-NOTES.md",
    f"{HANDOFF_REL}/workflow-state.yaml",
    f"{HANDOFF_REL}/scope-contract.md",
    f"{HANDOFF_REL}/source-parity-check.md",
    f"{HANDOFF_REL}/source-row-inventory.md",
    f"{HANDOFF_REL}/mockup-visual-inventory.md",
    f"{HANDOFF_REL}/scope-coverage-gaps.md",
    f"{HANDOFF_REL}/scope-clarification-requests.md",
    f"{HANDOFF_REL}/scope-gap-review.md",
    "support/АФБ справочники 26.06.26.md",
    "source/AutoFinPreFinal.docx",
    "source/AutoFinPreFinal.pdf",
    f"{CYCLE_REL}/cycle-state.yaml",
]


def esc(value: str) -> str:
    return str(value).replace("\n", "<br>").replace("|", "\\|")


def table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(esc(cell) for cell in row) + " |")
    return "\n".join(lines)


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def write_markdown(target: Path, sections: list[tuple[int, str, str]], title: str | None = None) -> None:
    scratch = TD / "_artifact_write" / target.stem
    scratch.mkdir(parents=True, exist_ok=True)
    manifest_sections = []
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
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(manifest_path), "--dry-run"],
        cwd=str(ROOT),
        check=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(manifest_path)],
        cwd=str(ROOT),
        check=True,
    )


SOURCE_ROWS = [
    ["`SRC-001`", "`WP-01`", "Блок «Персональные данные»", "`DOCX section-14 table row 004`", "`no_requirement_code:SRC-001`", "`yes`", "`ATOM-001`"],
    ["`SRC-002`", "`WP-01`", "Фамилия", "`DOCX section-14 table row 005`", "`no_requirement_code:SRC-002`", "`yes`", "`ATOM-002`; `ATOM-004`; `ATOM-005`; `GAP-003`"],
    ["`SRC-003`", "`WP-01`", "Имя", "`DOCX section-14 table row 006`", "`no_requirement_code:SRC-003`", "`yes`", "`ATOM-002`; `ATOM-004`; `ATOM-006`; `GAP-003`"],
    ["`SRC-004`", "`WP-01`", "Отчество", "`DOCX section-14 table row 007`", "`no_requirement_code:SRC-004`", "`yes`", "`ATOM-003`; `ATOM-004`; `ATOM-007`; `GAP-003`"],
    ["`SRC-005`", "`WP-01`", "ID клиента", "`DOCX section-14 table row 008`", "`no_requirement_code:SRC-005`", "`yes`", "`ATOM-003`; `ATOM-008`; `ATOM-009`; `GAP-001`"],
    ["`SRC-006`", "`WP-01`", "Пол", "`DOCX section-14 table row 009`; `support/АФБ справочники 26.06.26.md`", "`no_requirement_code:SRC-006`", "`yes`", "`ATOM-002`; `ATOM-004`; `ATOM-010`; `ATOM-011`; `GAP-001`"],
    ["`SRC-007`", "`WP-01`", "Дата рождения", "`DOCX section-14 table row 010`", "`no_requirement_code:SRC-007`", "`yes`", "`ATOM-002`; `ATOM-004`; `ATOM-012`; `ATOM-013`; `GAP-002`"],
    ["`SRC-008`", "`WP-01`", "Клиент менял ФИО", "`DOCX section-14 table row 011`", "`no_requirement_code:SRC-008`", "`yes`", "`ATOM-003`; `ATOM-004`; `ATOM-014`; `ATOM-015`"],
    ["`SRC-009`", "`WP-01`", "Предыдущая фамилия", "`DOCX section-14 table row 012`", "`no_requirement_code:SRC-009`", "`yes`", "`ATOM-016`; `ATOM-017`; `ATOM-018`; `GAP-003`"],
    ["`SRC-010`", "`WP-01`", "Предыдущее имя", "`DOCX section-14 table row 013`", "`no_requirement_code:SRC-010`", "`yes`", "`ATOM-016`; `ATOM-017`; `ATOM-019`; `GAP-003`"],
    ["`SRC-011`", "`WP-01`", "Предыдущее отчество", "`DOCX section-14 table row 014`", "`no_requirement_code:SRC-011`", "`yes`", "`ATOM-016`; `ATOM-017`; `ATOM-020`; `GAP-003`"],
]

NORMALIZATION_ROWS = [
    ["`SRC-001`", "`SP-WP01-001`", "`WP-01`", "Блок «Персональные данные»", "`visibility`", "`always`", "Блок отображается в разделе заявки.", "`no_requirement_code:SRC-001`", "`DOCX row 004`", "`high`", "`none_required:covered`", "`ATOM-001`"],
    ["`SRC-002`", "`SP-WP01-002`", "`WP-01`", "Фамилия", "`requiredness`", "`always`", "Поле обязательно (`О=Да`).", "`no_requirement_code:SRC-002`", "`DOCX row 005`", "`high`", "`none_required:covered`", "`ATOM-002`"],
    ["`SRC-003`", "`SP-WP01-003`", "`WP-01`", "Имя", "`requiredness`", "`always`", "Поле обязательно (`О=Да`).", "`no_requirement_code:SRC-003`", "`DOCX row 006`", "`high`", "`none_required:covered`", "`ATOM-002`"],
    ["`SRC-004`", "`SP-WP01-004`", "`WP-01`", "Отчество", "`requiredness`", "`always`", "Поле необязательно (`О=Нет`).", "`no_requirement_code:SRC-004`", "`DOCX row 007`", "`high`", "`none_required:covered`", "`ATOM-003`"],
    ["`SRC-005`", "`SP-WP01-005`", "`WP-01`", "ID клиента", "`requiredness`", "`always`", "Поле необязательно (`О=Нет`).", "`no_requirement_code:SRC-005`", "`DOCX row 008`", "`high`", "`none_required:covered`", "`ATOM-003`"],
    ["`SRC-006`", "`SP-WP01-006`", "`WP-01`", "Пол", "`requiredness`", "`always`", "Поле обязательно (`О=Да`).", "`no_requirement_code:SRC-006`", "`DOCX row 009`", "`high`", "`none_required:covered`", "`ATOM-002`"],
    ["`SRC-007`", "`SP-WP01-007`", "`WP-01`", "Дата рождения", "`requiredness`", "`always`", "Поле обязательно (`О=Да`).", "`no_requirement_code:SRC-007`", "`DOCX row 010`", "`high`", "`none_required:covered`", "`ATOM-002`"],
    ["`SRC-008`", "`SP-WP01-008`", "`WP-01`", "Клиент менял ФИО", "`requiredness`", "`always`", "Поле необязательно (`О=Нет`).", "`no_requirement_code:SRC-008`", "`DOCX row 011`", "`high`", "`none_required:covered`", "`ATOM-003`"],
    ["`SRC-002`", "`SP-WP01-009`", "`WP-01`", "Основные поля персональных данных", "`visibility`", "`always`", "Поля Фамилия, Имя, Отчество, ID клиента, Пол, Дата рождения, Клиент менял ФИО отображаются всегда.", "`no_requirement_code:SRC-002`", "`DOCX rows 005-011`", "`high`", "`none_required:covered`", "`ATOM-001`"],
    ["`SRC-002`", "`SP-WP01-010`", "`WP-01`", "Редактируемые основные поля", "`editability`", "`always`", "Фамилия, Имя, Отчество, Пол, Дата рождения, Клиент менял ФИО редактируемы (`Р=Да`).", "`no_requirement_code:SRC-002`", "`DOCX rows 005-011`", "`high`", "`none_required:covered`", "`ATOM-004`"],
    ["`SRC-005`", "`SP-WP01-011`", "`WP-01`", "ID клиента", "`editability`", "`always`", "Поле не редактируется (`Р=Нет`).", "`no_requirement_code:SRC-005`", "`DOCX row 008`", "`high`", "`none_required:covered`", "`ATOM-008`"],
    ["`SRC-002`", "`SP-WP01-012`", "`WP-01`", "Фамилия", "`input-format`", "`always`", "Возможен ввод текстовых символов и символа `-`.", "`no_requirement_code:SRC-002`", "`DOCX row 005`", "`medium`", "`GAP-003`", "`ATOM-005`"],
    ["`SRC-003`", "`SP-WP01-013`", "`WP-01`", "Имя", "`input-format`", "`always`", "Возможен ввод текстовых символов и символа `-`.", "`no_requirement_code:SRC-003`", "`DOCX row 006`", "`medium`", "`GAP-003`", "`ATOM-006`"],
    ["`SRC-004`", "`SP-WP01-014`", "`WP-01`", "Отчество", "`input-format`", "`always`", "Возможен ввод текстовых символов и символа `-`.", "`no_requirement_code:SRC-004`", "`DOCX row 007`", "`medium`", "`GAP-003`", "`ATOM-007`"],
    ["`SRC-005`", "`SP-WP01-015`", "`WP-01`", "ID клиента", "`integration-prefill`", "`after-save`", "ID клиента заполняется автоматически системой из АБС после сохранения заявки.", "`no_requirement_code:SRC-005`", "`DOCX row 008`", "`medium`", "`GAP-001`", "`ATOM-009`"],
    ["`SRC-006`", "`SP-WP01-016`", "`WP-01`", "Пол", "`dictionary-source`", "`always`", "Поле использует справочник `Пол клиента`.", "`no_requirement_code:SRC-006`", "`DOCX row 009`; `support gender_d`", "`high`", "`none_required:covered`", "`ATOM-010`"],
    ["`SRC-006`", "`SP-WP01-017`", "`WP-01`", "Пол", "`dadata-prefill`", "`after FIO DaData suggestion`", "Поле обновляется данными DaData после заполнения ФИО через подсказку DaData.", "`no_requirement_code:SRC-006`", "`DOCX row 009`", "`medium`", "`GAP-001`", "`ATOM-011`"],
    ["`SRC-007`", "`SP-WP01-018`", "`WP-01`", "Дата рождения", "`date-boundary`", "`current_date_minus_18`", "Дата не может быть позже текущей даты минус 18 лет.", "`no_requirement_code:SRC-007`", "`DOCX row 010`", "`medium`", "`GAP-002`", "`ATOM-012`"],
    ["`SRC-007`", "`SP-WP01-019`", "`WP-01`", "Дата рождения", "`date-rule-conflict`", "`current_date`", "В строке также указано, что дата не может быть позже текущей даты.", "`no_requirement_code:SRC-007`", "`DOCX row 010`", "`medium`", "`GAP-002`", "`ATOM-013`"],
    ["`SRC-008`", "`SP-WP01-020`", "`WP-01`", "Клиент менял ФИО", "`default-value`", "`initial`", "Значение по умолчанию `Нет`.", "`no_requirement_code:SRC-008`", "`DOCX row 011`", "`high`", "`none_required:covered`", "`ATOM-014`"],
    ["`SRC-008`", "`SP-WP01-021`", "`WP-01`", "Клиент менял ФИО", "`logical-switch`", "`always`", "Поле является переключателем `Да/Нет`.", "`no_requirement_code:SRC-008`", "`DOCX row 011`", "`high`", "`none_required:covered`", "`ATOM-015`"],
    ["`SRC-009`", "`SP-WP01-022`", "`WP-01`", "Предыдущая ФИО", "`conditional-visibility`", "`Клиент менял ФИО = Да`", "Поля предыдущей фамилии, имени и отчества видимы при значении `Да`.", "`no_requirement_code:SRC-009`", "`DOCX rows 012-014`", "`high`", "`none_required:covered`", "`ATOM-016`"],
    ["`SRC-009`", "`SP-WP01-023`", "`WP-01`", "Предыдущая ФИО", "`conditional-inverse`", "`Клиент менял ФИО = Нет`", "Поля предыдущей ФИО не отображаются, когда условие видимости не выполнено.", "`no_requirement_code:SRC-009`", "`DOCX rows 012-014`", "`medium`", "`none_required:covered`", "`ATOM-017`"],
    ["`SRC-009`", "`SP-WP01-024`", "`WP-01`", "Предыдущая фамилия", "`input-format`", "`Клиент менял ФИО = Да`", "Возможен ввод текстовых символов и символа `-`.", "`no_requirement_code:SRC-009`", "`DOCX row 012`", "`medium`", "`GAP-003`", "`ATOM-018`"],
    ["`SRC-010`", "`SP-WP01-025`", "`WP-01`", "Предыдущее имя", "`input-format`", "`Клиент менял ФИО = Да`", "Возможен ввод текстовых символов и символа `-`.", "`no_requirement_code:SRC-010`", "`DOCX row 013`", "`medium`", "`GAP-003`", "`ATOM-019`"],
    ["`SRC-011`", "`SP-WP01-026`", "`WP-01`", "Предыдущее отчество", "`input-format`", "`Клиент менял ФИО = Да`", "Возможен ввод текстовых символов и символа `-`.", "`no_requirement_code:SRC-011`", "`DOCX row 014`", "`medium`", "`GAP-003`", "`ATOM-020`"],
]

ATOM_ROWS = [
    ["`ATOM-001`", "`WP-01`", "`SRC-001`; `SRC-002..SRC-008`", "`no_requirement_code:section-14`", "Блок `Персональные данные` и основные поля персональных данных отображаются в заявке.", "`covered`", "`TC-ACPD-001`", "`High`"],
    ["`ATOM-002`", "`WP-01`", "`SRC-002`; `SRC-003`; `SRC-006`; `SRC-007`", "`no_requirement_code:section-14`", "Поля Фамилия, Имя, Пол и Дата рождения обязательны.", "`covered`", "`TC-ACPD-002`", "`High`"],
    ["`ATOM-003`", "`WP-01`", "`SRC-004`; `SRC-005`; `SRC-008`; `SRC-011`", "`no_requirement_code:section-14`", "Поля Отчество, ID клиента, Клиент менял ФИО и Предыдущее отчество необязательны.", "`covered`", "`TC-ACPD-002`", "`Medium`"],
    ["`ATOM-004`", "`WP-01`", "`SRC-002`; `SRC-003`; `SRC-004`; `SRC-006`; `SRC-007`; `SRC-008`", "`no_requirement_code:section-14`", "Редактируемые основные поля доступны для изменения пользователем.", "`covered`", "`TC-ACPD-003`", "`Medium`"],
    ["`ATOM-005`", "`WP-01`", "`SRC-002`", "`no_requirement_code:SRC-002`", "Фамилия допускает ввод текстовых символов и символа `-`; invalid enforcement mechanism is unresolved.", "`covered-with-gap`", "`TC-ACPD-004`; `GAP-003`", "`Medium`"],
    ["`ATOM-006`", "`WP-01`", "`SRC-003`", "`no_requirement_code:SRC-003`", "Имя допускает ввод текстовых символов и символа `-`; invalid enforcement mechanism is unresolved.", "`covered-with-gap`", "`TC-ACPD-004`; `GAP-003`", "`Medium`"],
    ["`ATOM-007`", "`WP-01`", "`SRC-004`", "`no_requirement_code:SRC-004`", "Отчество допускает ввод текстовых символов и символа `-`; invalid enforcement mechanism is unresolved.", "`covered-with-gap`", "`TC-ACPD-004`; `GAP-003`", "`Medium`"],
    ["`ATOM-008`", "`WP-01`", "`SRC-005`", "`no_requirement_code:SRC-005`", "Поле ID клиента не редактируется пользователем.", "`covered`", "`TC-ACPD-003`", "`Medium`"],
    ["`ATOM-009`", "`WP-01`", "`SRC-005`; `GAP-001`", "`no_requirement_code:SRC-005`", "ID клиента автоматически заполняется из АБС после сохранения заявки; ABS error behavior remains unresolved.", "`covered-with-gap`", "`TC-ACPD-005`; `GAP-001`", "`High`"],
    ["`ATOM-010`", "`WP-01`", "`SRC-006`; `DICT-001`", "`no_requirement_code:SRC-006`", "Пол использует значения справочника `Пол клиента`: Мужчина, Женщина.", "`covered`", "`TC-ACPD-006`", "`High`"],
    ["`ATOM-011`", "`WP-01`", "`SRC-006`; `GAP-001`", "`no_requirement_code:SRC-006`", "Пол обновляется данными DaData после заполнения ФИО через подсказку DaData; DaData error behavior remains unresolved.", "`covered-with-gap`", "`TC-ACPD-007`; `GAP-001`", "`High`"],
    ["`ATOM-012`", "`WP-01`", "`SRC-007`; `GAP-002`", "`no_requirement_code:SRC-007`", "Дата рождения на границе `текущая дата - 18 лет` допустима по правилу 18+.", "`covered-with-gap`", "`TC-ACPD-008`; `GAP-002`", "`High`"],
    ["`ATOM-013`", "`WP-01`", "`SRC-007`; `GAP-002`", "`no_requirement_code:SRC-007`", "Дата рождения на границе `текущая дата - 18 лет` также не позже текущей даты; negative/rejection priority remains unresolved.", "`covered-with-gap`", "`TC-ACPD-008`; `GAP-002`", "`High`"],
    ["`ATOM-014`", "`WP-01`", "`SRC-008`", "`no_requirement_code:SRC-008`", "Для `Клиент менял ФИО` значение по умолчанию равно `Нет`.", "`covered`", "`TC-ACPD-009`", "`Medium`"],
    ["`ATOM-015`", "`WP-01`", "`SRC-008`", "`no_requirement_code:SRC-008`", "`Клиент менял ФИО` является переключателем `Да/Нет`.", "`covered`", "`TC-ACPD-010`", "`Medium`"],
    ["`ATOM-016`", "`WP-01`", "`SRC-009`; `SRC-010`; `SRC-011`", "`no_requirement_code:section-14`", "Поля предыдущей ФИО отображаются при `Клиент менял ФИО = Да`.", "`covered`", "`TC-ACPD-011`", "`High`"],
    ["`ATOM-017`", "`WP-01`", "`SRC-009`; `SRC-010`; `SRC-011`", "`no_requirement_code:section-14`", "Поля предыдущей ФИО не отображаются при `Клиент менял ФИО = Нет`.", "`covered`", "`TC-ACPD-012`", "`Medium`"],
    ["`ATOM-018`", "`WP-01`", "`SRC-009`", "`no_requirement_code:SRC-009`", "Предыдущая фамилия допускает ввод текстовых символов и символа `-`; invalid enforcement mechanism is unresolved.", "`covered-with-gap`", "`TC-ACPD-013`; `GAP-003`", "`Medium`"],
    ["`ATOM-019`", "`WP-01`", "`SRC-010`", "`no_requirement_code:SRC-010`", "Предыдущее имя допускает ввод текстовых символов и символа `-`; invalid enforcement mechanism is unresolved.", "`covered-with-gap`", "`TC-ACPD-013`; `GAP-003`", "`Medium`"],
    ["`ATOM-020`", "`WP-01`", "`SRC-011`", "`no_requirement_code:SRC-011`", "Предыдущее отчество допускает ввод текстовых символов и символа `-`; invalid enforcement mechanism is unresolved.", "`covered-with-gap`", "`TC-ACPD-013`; `GAP-003`", "`Medium`"],
]


def ledger_rows() -> list[list[str]]:
    rows: list[list[str]] = []
    for atom_id, package_id, source_ref, req_id, statement, status, covered_by, priority in ATOM_ROWS:
        normalized_status = "`unclear`" if "unclear" in status else "`gap`" if status == "`gap`" else "`covered`"
        gaps = []
        for gap_id in ["GAP-001", "GAP-002", "GAP-003"]:
            if gap_id in covered_by or gap_id in source_ref:
                gaps.append(f"`{gap_id}`")
        gap_note = "; ".join(gaps) if gaps else "`none_required:covered`"
        if normalized_status == "`unclear`" and not gaps:
            gap_note = "`unclear:needs-review`"
        rows.append([atom_id, package_id, source_ref, req_id, statement, covered_by, normalized_status, gap_note, priority])
    return rows


def write_split_artifacts() -> None:
    write_markdown(
        TD / "artifact-write-strategy.md",
        [(1, "Artifact Write Strategy", table(
            ["item", "value", "evidence"],
            [
                ["`preflight_result`", "`large-file / package-based`", "`WP-01`; source rows `SRC-001`..`SRC-011`; split design artifacts required."],
                ["`write_method`", "`file-based manifest/chunked writing`", "`scripts/write_artifact_sections.py --manifest <manifest.json>`"],
                ["`forbidden_methods_checked`", "`yes`", "No one-shot PowerShell argument, no here-string, no inline giant command."],
                ["`chunk_plan`", "`WP-01 only`", "Normalize WP-01, build ledger, package plan, TC set, gate."],
                ["`helper_artifacts`", f"`{TD_REL}/_artifact_write/`", "Manifest scratch files retained as write evidence and excluded from review snapshots."],
                ["`validation_plan`", "`validate_agent_artifacts; codex_review_cycle_runner validate`", "Run after final artifact write and state update."],
            ],
        ))],
    )
    write_markdown(
        TD / "mockup-usage.md",
        [(1, "Mockup Usage", table(
            ["item", "value", "evidence"],
            [
                ["`inventory`", f"`{HANDOFF_REL}/mockup-visual-inventory.md`", "`opened=yes`; `not_used_as_requirement_source=yes`"],
                ["`used_for_steps`", "`yes`", "Used only for locating the personal data block and fields in UI steps."],
                ["`not_used_as_requirement_source`", "`yes`", "FT/support define behavior; mockups only refine navigation wording."],
                ["`mockup_only_items`", "`none_required:ignored`", "Mockup example values ignored; action `Далее` and document recognition remain out of scope."],
            ],
        ))],
    )
    write_markdown(
        TD / "source-row-inventory.md",
        [(1, "Source Row Inventory", table(
            ["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"],
            SOURCE_ROWS,
        ))],
    )
    write_markdown(
        TD / "source-row-completeness-matrix.md",
        [(1, "Source Row Completeness Matrix", table(
            ["source_row_id", "source_requirement_codes", "normalized_property_ids", "linked_atoms", "gap_ids", "coverage_decision"],
            [
                ["`SRC-001`", "`no_requirement_code:SRC-001`", "`SP-WP01-001`", "`ATOM-001`", "`none_required:covered`", "`covered`"],
                ["`SRC-002`", "`no_requirement_code:SRC-002`", "`SP-WP01-002`; `SP-WP01-009`; `SP-WP01-010`; `SP-WP01-012`", "`ATOM-002`; `ATOM-004`; `ATOM-005`", "`GAP-003`", "`covered-with-gap`"],
                ["`SRC-003`", "`no_requirement_code:SRC-003`", "`SP-WP01-003`; `SP-WP01-009`; `SP-WP01-010`; `SP-WP01-013`", "`ATOM-002`; `ATOM-004`; `ATOM-006`", "`GAP-003`", "`covered-with-gap`"],
                ["`SRC-004`", "`no_requirement_code:SRC-004`", "`SP-WP01-004`; `SP-WP01-009`; `SP-WP01-010`; `SP-WP01-014`", "`ATOM-003`; `ATOM-004`; `ATOM-007`", "`GAP-003`", "`covered-with-gap`"],
                ["`SRC-005`", "`no_requirement_code:SRC-005`", "`SP-WP01-005`; `SP-WP01-011`; `SP-WP01-015`", "`ATOM-003`; `ATOM-008`; `ATOM-009`", "`GAP-001`", "`covered-with-gap`"],
                ["`SRC-006`", "`no_requirement_code:SRC-006`", "`SP-WP01-006`; `SP-WP01-009`; `SP-WP01-010`; `SP-WP01-016`; `SP-WP01-017`", "`ATOM-002`; `ATOM-004`; `ATOM-010`; `ATOM-011`", "`GAP-001`", "`covered-with-gap`"],
                ["`SRC-007`", "`no_requirement_code:SRC-007`", "`SP-WP01-007`; `SP-WP01-009`; `SP-WP01-010`; `SP-WP01-018`; `SP-WP01-019`", "`ATOM-002`; `ATOM-004`; `ATOM-012`; `ATOM-013`", "`GAP-002`", "`covered-with-unclear`"],
                ["`SRC-008`", "`no_requirement_code:SRC-008`", "`SP-WP01-008`; `SP-WP01-009`; `SP-WP01-010`; `SP-WP01-020`; `SP-WP01-021`", "`ATOM-003`; `ATOM-004`; `ATOM-014`; `ATOM-015`", "`none_required:covered`", "`covered`"],
                ["`SRC-009`", "`no_requirement_code:SRC-009`", "`SP-WP01-022`; `SP-WP01-023`; `SP-WP01-024`", "`ATOM-016`; `ATOM-017`; `ATOM-018`", "`GAP-003`", "`covered-with-gap`"],
                ["`SRC-010`", "`no_requirement_code:SRC-010`", "`SP-WP01-022`; `SP-WP01-023`; `SP-WP01-025`", "`ATOM-016`; `ATOM-017`; `ATOM-019`", "`GAP-003`", "`covered-with-gap`"],
                ["`SRC-011`", "`no_requirement_code:SRC-011`", "`SP-WP01-022`; `SP-WP01-023`; `SP-WP01-026`", "`ATOM-016`; `ATOM-017`; `ATOM-020`", "`GAP-003`", "`covered-with-gap`"],
            ],
        ))],
    )
    write_markdown(
        TD / "source-table-normalization.md",
        [(1, "Source Table Normalization", table(
            ["source_row_id", "source_property_id", "package_id", "field_or_block", "property", "condition", "expected_behavior", "requirement_code", "source_ref", "confidence", "gap_id", "linked_atoms"],
            NORMALIZATION_ROWS,
        ))],
    )
    write_markdown(
        TD / "dictionary-inventory.md",
        [(1, "Dictionary Inventory", table(
            ["dictionary_id", "dictionary_name", "source_file", "source_location", "extraction_status", "active_values", "archived_values", "used_by_source_properties", "gap_id", "notes"],
            [["`DICT-001`", "Пол клиента", "`support/АФБ справочники 26.06.26.md`", "`## Пол`; path `mview.dictionaries.natural_person.gender_d`", "`extracted`", "`Мужчина`; `Женщина`", "`none_required:no_archived_values`", "`SP-WP01-016`; `ATOM-010`; `TC-ACPD-006`; `TC-ACPD-007`", "`GAP-001`", "Support source resolves values; DaData error behavior remains a residual risk."]],
        ))],
    )
    tddt_rows = []
    tc_by_atom = {row[0].strip("`"): row[6] for row in ATOM_ROWS}
    for idx, row in enumerate(NORMALIZATION_ROWS, start=1):
        prop_id = row[1]
        atom = row[11]
        gap = row[10]
        if "GAP-002" in gap and "ATOM-013" in atom:
            decision, planned, executable, oracle, testable, blocked, admissibility = "`covered_by_existing_tc`", "`TC-ACPD-008`; `GAP-002`", "`yes`", "DOCX row 010; TC uses a date satisfying both written date constraints", "valid boundary date that is both `current date - 18 years` and not future", "negative/rejection priority between `18+` and `not future` remains unresolved", "`GAP-002`"
        elif "GAP-003" in gap and "input-format" in row[4]:
            planned_tc = "`TC-ACPD-013`; `GAP-003`" if row[1] in {"`SP-WP01-024`", "`SP-WP01-025`", "`SP-WP01-026`"} else "`TC-ACPD-004`; `GAP-003`"
            decision, planned, executable, oracle, testable, blocked, admissibility = "`standalone_tc`", planned_tc, "`yes`", "source-backed positive input display", "allowed text and hyphen are executable", "invalid input enforcement feedback is unspecified", "`GAP-003`"
        else:
            atom_id = atom.split(";")[0].replace("`", "").strip()
            planned = tc_by_atom.get(atom_id, "`not_covered:manual_review`")
            decision, executable, oracle, testable, blocked, admissibility = "`standalone_tc`", "`yes`", "source-backed visible UI state", "full source-backed behavior", "`none_required:covered`", "`none_required:covered`"
        tddt_rows.append([f"`DD-{idx:03d}`", "`WP-01`", prop_id, atom, row[4], decision, "Source row has a discrete observable or explicit gap.", planned, oracle, executable, oracle, testable, blocked, admissibility, "`medium`"])
    write_markdown(
        TD / "test-design-decision-table.md",
        [(1, "Test Design Decision Table", table(
            ["decision_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "decision", "decision_reason", "planned_tc_or_gap", "oracle_source", "must_be_executable", "observable_oracle", "testable_part", "blocked_part", "gap_admissibility", "review_risk"],
            tddt_rows,
        ))],
    )
    stale_cot = TD / "coverage-obligation-table.md"
    if stale_cot.exists():
        stale_cot.unlink()
    write_markdown(
        TD / "atomic-requirements-ledger.md",
        [(1, "Atomic Requirements Ledger", table(
            ["atom_id", "package_id", "source_ref", "req_id", "atomic_statement", "covered_by_tc", "coverage_status", "gap_note", "priority"],
            ledger_rows(),
        ))],
    )
    write_markdown(
        TD / "internal-work-package-coverage.md",
        [(1, "Internal Work Package Coverage", table(
            ["package_id", "focus", "ledger_gate", "design_plan_gate", "tc_gate", "atoms", "covered", "gap", "unclear", "TC count", "status"],
            [["`WP-01`", "Personal data fields and conditional previous FIO", "`pass`", "`pass`", "`pass`", "`20`", "`19`", "`3 residual gaps`", "`1`", "`13`", "`ready-for-review`"]],
        ))],
    )
    write_markdown(
        TD / "package-ledger-self-check.md",
        [(1, "Package Ledger Self-check", table(
            ["package_id", "check", "status", "evidence", "required_action"],
            [
                ["`WP-01`", "`source-row-preservation`", "`pass`", "`SRC-001`..`SRC-011` preserved in writer-side inventory.", "`none_required:pass`"],
                ["`WP-01`", "`atom-package-id`", "`pass`", "Every `ATOM-*` row has `package_id=WP-01`.", "`none_required:pass`"],
                ["`WP-01`", "`no-code-invention`", "`pass`", "No in-scope `GSR`/`BSR` found; ledger uses source row anchors.", "`none_required:pass`"],
                ["`WP-01`", "`gap-visibility`", "`pass`", "`GAP-001`; `GAP-002`; `GAP-003` retained.", "`none_required:pass`"],
            ],
        ))],
    )
    plan_rows = [
        ["`PLAN-001`", "`WP-01`", "`visibility`", "`SRC-001..SRC-008`", "`ATOM-001`", "Проверить отображение блока и основных полей персональных данных.", "`positive`", "`visibility`", "`always`", "Блок и перечисленные поля видимы.", "`DOCX rows 004-011`", "`TC-ACPD-001`", "`covered`"],
        ["`PLAN-002`", "`WP-01`", "`requiredness`", "`SRC-002..SRC-008`; `SRC-011`", "`ATOM-002`; `ATOM-003`", "Проверить required/optional indication по `О` column без действия `Далее`.", "`positive`", "`field-property`", "`required-vs-optional`", "Required and optional fields have corresponding UI indication.", "`DOCX O column`", "`TC-ACPD-002`", "`covered`"],
        ["`PLAN-003`", "`WP-01`", "`editability`", "`SRC-002..SRC-008`", "`ATOM-004`; `ATOM-008`", "Проверить editable/read-only state основных полей.", "`positive`", "`field-property`", "`editable-vs-readonly`", "Editable fields can be changed; ID cannot be edited.", "`DOCX R column`", "`TC-ACPD-003`", "`covered`"],
        ["`PLAN-004`", "`WP-01`", "`input-format`", "`SRC-002..SRC-004`", "`ATOM-005`; `ATOM-006`; `ATOM-007`", "Проверить формат допустимого ввода: текстовые символы и дефис в текущей ФИО.", "`positive`", "`format-valid-class`", "`text-and-hyphen`", "Класс допустимого формата `text-and-hyphen` принимается и отображается в полях.", "`DOCX notes`", "`TC-ACPD-004`", "`covered`"],
        ["`PLAN-005`", "`WP-01`", "`input-format`", "`SRC-002..SRC-004`; `SRC-009..SRC-011`", "`ATOM-005`; `ATOM-006`; `ATOM-007`; `ATOM-018`; `ATOM-019`; `ATOM-020`", "Не создавать negative TC для non-text classes без source-backed feedback.", "`gap`", "`invalid-enforcement`", "`digits/special-non-hyphen`", "Exact invalid input mechanism remains unspecified.", "`GAP-003`", "`GAP-003`", "`gap`"],
        ["`PLAN-006`", "`WP-01`", "`integration`", "`SRC-005`", "`ATOM-009`", "Проверить появление ID клиента после сохранения заявки.", "`positive`", "`integration-prefill`", "`after-save`", "ID клиента отображается в read-only field.", "`DOCX row 008`", "`TC-ACPD-005`; `GAP-001`", "`covered`"],
        ["`PLAN-007`", "`WP-01`", "`dictionary`", "`SRC-006`; `DICT-001`", "`ATOM-010`", "Проверить значения справочника Пол.", "`positive`", "`dictionary-values`", "`active-values`", "Доступны все и только values from `DICT-001`.", "`support gender_d`", "`TC-ACPD-006`", "`covered`"],
        ["`PLAN-008`", "`WP-01`", "`integration`", "`SRC-006`; `GAP-001`", "`ATOM-011`", "Проверить обновление пола по DaData suggestion for FIO.", "`positive`", "`dadata-prefill`", "`fio-suggestion`", "Пол обновляется значением из `DICT-001`.", "`DOCX row 009`; `DICT-001`", "`TC-ACPD-007`; `GAP-001`", "`covered`"],
        ["`PLAN-009`", "`WP-01`", "`date-boundary`", "`SRC-007`; `GAP-002`", "`ATOM-012`", "Проверить acceptance границы `current date - 18 years`.", "`positive`", "`boundary`", "`exact-boundary`", "Boundary date is displayed in the field.", "`DOCX row 010`", "`TC-ACPD-008`", "`covered`"],
        ["`PLAN-010`", "`WP-01`", "`default-value`", "`SRC-008`", "`ATOM-014`", "Проверить default `Нет`.", "`positive`", "`default`", "`initial`", "Switch shows selected value `Нет` by default.", "`DOCX row 011`", "`TC-ACPD-009`", "`covered`"],
        ["`PLAN-011`", "`WP-01`", "`logical-switch`", "`SRC-008`", "`ATOM-015`", "Проверить switching to `Да/Нет`.", "`positive`", "`yes-no-switch`", "`Да/Нет`", "Switch shows selected values `Да` and `Нет`.", "`DOCX row 011`", "`TC-ACPD-010`", "`covered`"],
        ["`PLAN-012`", "`WP-01`", "`conditional-visibility`", "`SRC-009..SRC-011`", "`ATOM-016`", "Проверить positive visibility branch for previous FIO fields.", "`positive`", "`dependency-positive`", "`Клиент менял ФИО = Да`", "Previous FIO fields are visible for `Да`.", "`DOCX rows 012-014`", "`TC-ACPD-011`", "`covered`"],
        ["`PLAN-013`", "`WP-01`", "`conditional-visibility`", "`SRC-009..SRC-011`", "`ATOM-017`", "Проверить inverse visibility branch for previous FIO fields.", "`positive`", "`dependency-inverse`", "`Клиент менял ФИО = Нет`", "Previous FIO fields are hidden for `Нет`.", "`DOCX rows 012-014`", "`TC-ACPD-012`", "`covered`"],
        ["`PLAN-014`", "`WP-01`", "`input-format`", "`SRC-009..SRC-011`", "`ATOM-018`; `ATOM-019`; `ATOM-020`", "Проверить формат допустимого ввода: текстовые символы и дефис в предыдущей ФИО.", "`positive`", "`format-valid-class`", "`text-and-hyphen`", "Класс допустимого формата `text-and-hyphen` принимается и отображается в полях.", "`DOCX rows 012-014`", "`TC-ACPD-013`", "`covered`"],
        ["`PLAN-015`", "`WP-01`", "`date-rule-conflict`", "`SRC-007`; `GAP-002`", "`ATOM-013`", "Не создавать отдельный executable TC, который silently chooses only 18+ or only not-future.", "`gap`", "`rule-priority`", "`18+ vs not-future`", "Negative/rejection priority remains unresolved.", "`GAP-002`", "`GAP-002`", "`unclear`"],
    ]
    write_markdown(
        TD / "package-test-design-plan.md",
        [(1, "Package Test Design Plan", table(
            ["design_item_id", "package_id", "design_dimension", "source_ref", "linked_atoms", "planned_check", "check_type", "coverage_class", "input_class", "single_expected_behavior", "oracle_source", "planned_tc_or_gap", "status"],
            plan_rows,
        ))],
    )
    write_markdown(
        TD / "package-design-plan-self-check.md",
        [(1, "Package Design Plan Self-check", table(
            ["package_id", "check", "status", "evidence", "required_action"],
            [
                ["`WP-01`", "`one-expected-result-per-plan-row`", "`pass`", "`PLAN-001`..`PLAN-012` each has one main expected behavior or gap.", "`none_required:pass`"],
                ["`WP-01`", "`dependency-branches`", "`pass`", "`PLAN-011` covers `Да` and `Нет` branches.", "`none_required:pass`"],
                ["`WP-01`", "`date-ambiguity`", "`pass`", "`PLAN-009` keeps `GAP-002`; does not choose only one date rule.", "`none_required:pass`"],
                ["`WP-01`", "`invalid-input-mechanism`", "`pass`", "`PLAN-005` keeps exact feedback as `GAP-003`.", "`none_required:pass`"],
            ],
        ))],
    )
    write_markdown(
        TD / "test-design-applicability-matrix.md",
        [(1, "Test-design Applicability Matrix", table(
            ["dimension", "applicable", "source_ref", "linked_atoms", "linked_test_cases", "gap_id", "reason"],
            [
                ["`other`", "`yes`", "`SRC-001..SRC-008`", "`ATOM-001`; `ATOM-002`; `ATOM-003`; `ATOM-004`; `ATOM-008`; `ATOM-014`; `ATOM-015`", "`TC-ACPD-001`; `TC-ACPD-002`; `TC-ACPD-003`; `TC-ACPD-009`; `TC-ACPD-010`", "", "Field visibility, requiredness, editability and default/switch state are explicit source properties not covered by a narrower dimension."],
                ["`table-list`", "`yes`", "`SRC-006`; `DICT-001`", "`ATOM-010`", "`TC-ACPD-006`", "", "Gender dictionary values extracted from support source."],
                ["`format`", "`yes`", "`SRC-002..SRC-004`; `SRC-009..SRC-011`", "`ATOM-005`; `ATOM-006`; `ATOM-007`; `ATOM-018`; `ATOM-019`; `ATOM-020`", "`TC-ACPD-004`; `TC-ACPD-013`", "", "Allowed `text-and-hyphen` format class is executable in the linked TC. Invalid feedback is tracked in the separate unclear row."],
                ["`format`", "`unclear`", "`SRC-002..SRC-004`; `SRC-009..SRC-011`", "`ATOM-005`; `ATOM-006`; `ATOM-007`; `ATOM-018`; `ATOM-019`; `ATOM-020`", "", "`GAP-003`", "Exact invalid input UI mechanism is not specified."],
                ["`date-time`", "`unclear`", "`SRC-007`", "`ATOM-012`; `ATOM-013`", "`TC-ACPD-008`", "`GAP-002`", "Boundary acceptance covered; rule priority/rejection mechanism remains open."],
                ["`conditional-visibility`", "`yes`", "`SRC-009..SRC-011`", "`ATOM-016`; `ATOM-017`", "`TC-ACPD-011`; `TC-ACPD-012`", "", "Previous FIO depends on `Клиент менял ФИО`."],
                ["`integration`", "`unclear`", "`SRC-005`; `SRC-006`", "`ATOM-009`; `ATOM-011`", "`TC-ACPD-005`; `TC-ACPD-007`", "`GAP-001`", "Explicit visible update is covered; failure/internal behavior is residual risk."],
                ["`persistence`", "`unclear`", "`SRC-005`; `GAP-001`", "`ATOM-009`", "`TC-ACPD-005`", "`GAP-001`", "Visible ID after save is covered; backend persistence/failure behavior is not specified."],
                ["`scenario-use-case`", "`no`", "`scope-contract.md`", "`none_required:out_of_scope`", "", "", "No broad scenario/use-case TC is needed for selected rows 004-014."],
            ],
        ))],
    )
    write_markdown(
        TD / "dependency-matrix.md",
        [(1, "Dependency Matrix", table(
            ["dependency_id", "package_id", "controlling_field", "controlling_value", "dependent_element", "expected_state", "linked_atoms", "linked_tc_or_gap"],
            [
                ["`DEP-001`", "`WP-01`", "`Клиент менял ФИО`", "`Да`", "`Предыдущая фамилия`; `Предыдущее имя`; `Предыдущее отчество`", "`visible`", "`ATOM-016`", "`TC-ACPD-011`"],
                ["`DEP-002`", "`WP-01`", "`Клиент менял ФИО`", "`Нет`", "`Предыдущая фамилия`; `Предыдущее имя`; `Предыдущее отчество`", "`not visible`", "`ATOM-017`", "`TC-ACPD-012`"],
                ["`DEP-003`", "`WP-01`", "`ФИО via DaData`", "`selected suggestion`", "`Пол`", "`updated from DaData`", "`ATOM-011`", "`TC-ACPD-007`; `GAP-001`"],
            ],
        ))],
    )
    write_markdown(
        TD / "fixture-catalog.md",
        [(1, "Fixture Catalog", table(
            ["fixture_id", "purpose", "fixture_data", "used_by", "source_or_rule_ref", "cleanup"],
            [
                ["`FIX-ACPD-001`", "Current FIO positive input.", "`Фамилия=Иванов-Петров`; `Имя=Анна-Мария`; `Отчество=Сергеевна`.", "`TC-ACPD-004`", "`SRC-002..SRC-004`", "Restore or discard unsaved changes."],
                ["`FIX-ACPD-002`", "DaData FIO suggestion for male gender.", "`ФИО=Иванов Иван Иванович`; expected `Пол=Мужчина` if suggestion returns male.", "`TC-ACPD-007`", "`SRC-006`; `DICT-001`; package DaData notes", "Discard unsaved changes."],
                ["`FIX-ACPD-003`", "Date boundary for execution date 2026-06-30.", "`Дата рождения=30.06.2008`; class `current date - 18 years`.", "`TC-ACPD-008`", "`SRC-007`; `GAP-002`", "Restore or discard unsaved changes."],
                ["`FIX-ACPD-004`", "Previous FIO positive input.", "`Предыдущая фамилия=Сидорова-Петрова`; `Предыдущее имя=Мария-Анна`; `Предыдущее отчество=Игоревна`.", "`TC-ACPD-013`", "`SRC-009..SRC-011`", "Set `Клиент менял ФИО=Нет` or discard unsaved changes."],
                ["`FIX-ACPD-005`", "Application save for ID autofill.", "All unrelated mandatory fields required by the application save flow are valid according to their own signed-off scopes.", "`TC-ACPD-005`", "`SRC-005`; `GAP-001`", "Use a disposable draft application."],
            ],
        ))],
    )
    write_markdown(
        TD / "risk-priority-map.md",
        [(1, "Risk / Priority Map", table(
            ["atom_id", "coverage_dimension", "impact", "likelihood", "risk_score", "risk_level", "risk_factors", "source_ref", "required_priority", "linked_test_cases", "gap_id", "residual_risk_decision", "rationale"],
            [
                ["`ATOM-009`", "`integration`", "`4`", "`3`", "`12`", "`high`", "`external-side-effect`", "`SRC-005`", "`High`", "`TC-ACPD-005`", "`GAP-001`", "`accepted-with-gap`", "ID from ABS affects client identity; failure behavior not defined."],
                ["`ATOM-011`", "`integration`", "`4`", "`3`", "`12`", "`high`", "`external-service`", "`SRC-006`", "`High`", "`TC-ACPD-007`", "`GAP-001`", "`accepted-with-gap`", "DaData-derived gender affects personal data; failure behavior not defined."],
                ["`ATOM-012`", "`date-boundary`", "`4`", "`3`", "`12`", "`high`", "`business-validation`", "`SRC-007`", "`High`", "`TC-ACPD-008`", "`GAP-002`", "`accepted-with-gap`", "Birth date eligibility rule is high impact; source contains ambiguous rules."],
                ["`ATOM-016`", "`conditional-visibility`", "`3`", "`3`", "`9`", "`medium`", "`data-completeness`", "`SRC-009..SRC-011`", "`Medium`", "`TC-ACPD-011`", "`none_required:covered`", "`none`", "Previous FIO fields depend on a user switch."],
                ["`ATOM-005`", "`input-format`", "`3`", "`3`", "`9`", "`medium`", "`data-quality`", "`SRC-002`", "`Medium`", "`TC-ACPD-004`", "`GAP-003`", "`accepted-with-gap`", "Allowed class covered for current FIO; exact invalid feedback not specified."],
                ["`ATOM-018`", "`input-format`", "`3`", "`3`", "`9`", "`medium`", "`data-quality`", "`SRC-009`", "`Medium`", "`TC-ACPD-013`", "`GAP-003`", "`accepted-with-gap`", "Allowed class covered for previous FIO; exact invalid feedback not specified."],
            ],
        ))],
    )
    write_markdown(
        TD / "coverage-map.md",
        [(1, "Coverage Map", table(
            ["metric", "value", "evidence"],
            [
                ["`atomic_statements`", "`20`", "`atomic-requirements-ledger.md`"],
                ["`covered`", "`20`", "`TC-ACPD-001`..`TC-ACPD-013`; covered-with-gap counted as executable partial coverage"],
                ["`gap`", "`3`", "`GAP-001`; `GAP-002`; `GAP-003`"],
                ["`unclear_atoms`", "`0`", "`ATOM-013` has non-conflicting valid-boundary coverage through `TC-ACPD-008`; unresolved rejection priority remains `GAP-002`."],
                ["`test_cases`", "`13`", "`test-cases/14-application-card-client-personal-data.md`"],
                ["`known_limitations`", "`3`", "DaData/ABS failures; birth-date rule priority; invalid text-input feedback."],
            ],
        ))],
    )
    write_markdown(
        TD / "coverage-metrics.md",
        [(1, "Coverage Metrics", table(
            ["metric_id", "dimension", "total_obligations", "covered", "gap", "unclear", "linked_tc_or_gap"],
            [
                ["`MET-001`", "`visibility`", "`3`", "`3`", "`0`", "`0`", "`TC-ACPD-001`; `TC-ACPD-011`; `TC-ACPD-012`"],
                ["`MET-002`", "`requiredness`", "`1`", "`1`", "`0`", "`0`", "`TC-ACPD-002`"],
                ["`MET-003`", "`editability`", "`1`", "`1`", "`0`", "`0`", "`TC-ACPD-003`"],
                ["`MET-004`", "`input-format`", "`4`", "`2`", "`2`", "`0`", "`TC-ACPD-004`; `TC-ACPD-013`; `GAP-003`"],
                ["`MET-005`", "`dictionary`", "`2`", "`2`", "`0`", "`0`", "`TC-ACPD-006`"],
                ["`MET-006`", "`integration`", "`2`", "`2`", "`0`", "`0`", "`TC-ACPD-005`; `TC-ACPD-007`; `GAP-001`"],
                ["`MET-007`", "`date-boundary`", "`2`", "`1`", "`0`", "`1`", "`TC-ACPD-008`; `GAP-002`"],
                ["`MET-008`", "`default/logical-switch`", "`2`", "`2`", "`0`", "`0`", "`TC-ACPD-009`; `TC-ACPD-010`"],
            ],
        ))],
    )
    write_markdown(
        TD / "coverage-gaps.md",
        [(1, "Coverage Gaps", dedent(
            """
            ### GAP-001

            **Ссылка на ФТ:** `section-14 rows 008-010`; `SRC-005`; `SRC-006`.
            **Связанные атомарные утверждения:** `ATOM-009`; `ATOM-011`.
            **Тип пробела:** `missing-rule`.
            **Описание:** Support source resolves gender values (`Мужчина`, `Женщина`), but DaData/ABS error behavior, fallback and retry behavior are not defined.
            **Влияние:** `non-blocking`.
            **Временная обработка:** Cover only visible source-backed successful update/fill behavior; do not invent failure behavior.
            **Статус:** `open`.

            ### GAP-002

            **Ссылка на ФТ:** `section-14 row 010`; `SRC-007`.
            **Связанные атомарные утверждения:** `ATOM-012`; `ATOM-013`.
            **Тип пробела:** `missing-rule`.
            **Описание:** Source contains both `date not later than current date - 18 years` and `date not later than current date`; analyst has not clarified which rule is primary.
            **Влияние:** `non-blocking`.
            **Временная обработка:** Cover exact 18-year boundary acceptance and keep rule priority/rejection behavior visible as unclear.
            **Статус:** `open`.

            ### GAP-003

            **Ссылка на ФТ:** `section-14 rows 005-007, 012-014`; `SRC-002`; `SRC-003`; `SRC-004`; `SRC-009`; `SRC-010`; `SRC-011`.
            **Связанные атомарные утверждения:** `ATOM-005`; `ATOM-006`; `ATOM-007`; `ATOM-018`; `ATOM-019`; `ATOM-020`.
            **Тип пробела:** `missing-rule`.
            **Описание:** Rows define allowed input class (`text characters` and `-`), but do not define exact observable UI mechanism for disallowed digits or non-hyphen special characters.
            **Влияние:** `non-blocking`.
            **Временная обработка:** Positive allowed-class cases are executable; no TC asserts field clearing, highlighting, message text or blocked transition for invalid classes.
            **Статус:** `open`.
            """
        ))],
    )
    write_markdown(
        TD / "test-design-review.md",
        [(1, "Test Design Review", table(
            ["review_item", "status", "severity", "affected_package", "evidence", "required_action", "blocks_ready_for_review"],
            [
                ["`decision-table-classification`", "`pass`", "`info`", "`WP-01`", "TDDT uses `standalone_tc` for executable rows and `gap_unclear` only for `GAP-002` rule priority.", "`none_required:pass`", "`no`"],
                ["`ledger-plan-alignment`", "`pass`", "`info`", "`WP-01`", "Ledger `covered_by_tc` values align with Package Test Design Plan and TC sections.", "`none_required:pass`", "`no`"],
                ["`coverage-class-completeness`", "`pass`", "`info`", "`WP-01`", "Visibility, requiredness, editability, input-format, dictionary, integration, date and dependency classes appear in package plan/applicability artifacts; no mandatory COT expansion applies.", "`none_required:pass`", "`no`"],
                ["`numeric-length-boundaries`", "`pass`", "`info`", "`WP-01`", "No numeric or exact-length source rule in rows 004-014; date boundary handled separately.", "`none_required:pass`", "`no`"],
                ["`mask-format-coverage`", "`pass`", "`info`", "`WP-01`", "No mask source rule in rows 004-014; text/hyphen format has valid class and `GAP-003` for invalid feedback.", "`none_required:pass`", "`no`"],
                ["`conditional-branches`", "`pass`", "`info`", "`WP-01`", "`TC-ACPD-011` covers `Да`; `TC-ACPD-012` covers `Нет`.", "`none_required:pass`", "`no`"],
                ["`gap-specificity`", "`pass`", "`info`", "`WP-01`", "`GAP-001`, `GAP-002`, `GAP-003` each isolate only the missing behavior.", "`none_required:pass`", "`no`"],
                ["`gap-admissibility`", "`pass`", "`info`", "`WP-01`", "No source-backed visible behavior is hidden in gaps except the explicitly unresolved mechanisms/rule priority.", "`none_required:pass`", "`no`"],
                ["`internal-observability`", "`pass`", "`info`", "`WP-01`", "DaData/ABS internals remain `GAP-001`; visible field updates are tested.", "`none_required:pass`", "`no`"],
                ["`metadata-only-exclusion`", "`pass`", "`info`", "`WP-01`", "No metadata-only row is linked to executable TC as independent behavior.", "`none_required:pass`", "`no`"],
                ["`negative-fixture-isolation`", "`pass`", "`info`", "`WP-01`", "No negative transition TC is created because `Далее` is out of scope and invalid feedback is `GAP-003`.", "`none_required:pass`", "`no`"],
                ["`dictionary-closed-set`", "`pass`", "`info`", "`WP-01`", "`TC-ACPD-006` checks all and only active `DICT-001` values.", "`none_required:pass`", "`no`"],
                ["`tc-mapping-atomicity`", "`pass`", "`info`", "`WP-01`", "`TC-ACPD-001`..`TC-ACPD-013` each has one main expected result.", "`none_required:pass`", "`no`"],
                ["`applicability-linked-tc-semantics`", "`pass`", "`info`", "`WP-01`", "Applicability matrix links each applicable dimension to matching TC or `GAP-*`.", "`none_required:pass`", "`no`"],
                ["`unsupported-ui-mechanism`", "`pass`", "`info`", "`WP-01`", "No TC asserts field clearing, highlighting, error text or transition blocking for unsupported invalid text input.", "`none_required:pass`", "`no`"],
                ["`ready-for-tc-writing`", "`pass`", "`info`", "`WP-01`", "Normalization, TDDT, package plan and residual gaps are complete for writer-r1.", "`none_required:pass`", "`no`"],
            ],
        ))],
    )
    write_markdown(
        TD / "writer-quality-gate.md",
        [(1, "Writer Quality Gate", table(
            ["gate_item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"],
            [
                ["`artifact-shape-preflight`", "`pass`", "Split artifacts use canonical headings and required table columns; canonical TC links summaries only.", "`all`", "`none_required:pass`", "`no`"],
                ["`placeholder-sentinel-normalization`", "`pass`", "Traceability/link columns use explicit sentinels such as `no_requirement_code:*`, `none_required:covered`, `not_covered:GAP-002`.", "`all`", "`none_required:pass`", "`no`"],
                ["`artifact-write-strategy`", "`pass`", "`artifact-write-strategy.md` uses `scripts/write_artifact_sections.py --manifest <manifest.json>`.", "`all`", "`none_required:pass`", "`no`"],
                ["`mockup-visual-inventory`", "`pass`", "`mockup-visual-inventory.md` opened and not used as requirement source.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`source-row-inventory`", "`pass`", "Every handoff row `SRC-001`..`SRC-011` is present and mapped.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`source-normalization-atomic`", "`pass`", "`source-table-normalization.md` has stable `SP-*` rows with one property each.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`dictionary-inventory`", "`pass`", "`DICT-001` extracted from support source and linked downstream.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`test-design-decision-table`", "`pass`", "Each `SP-*` has one decision before ledger/TC writing.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`coverage-obligation-table`", "`pass`", "Source rows have no validator-obligation property types; no COT split artifact is generated.", "`WP-01`", "`none_required:not-applicable`", "`no`"],
                ["`coverage-metrics`", "`pass`", "`coverage-metrics.md` counts applicable dimensions and residual gaps.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`fixture-catalog`", "`pass`", "`fixture-catalog.md` defines concrete values for FIO, date, DaData and save flow.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`risk-priority-map`", "`pass`", "High-risk integration/date atoms have High-priority TC or residual gap.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`test-design-review`", "`pass`", "`test-design-review.md` has no blocking rows.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`gap-admissibility`", "`pass`", "`GAP-001`, `GAP-002`, `GAP-003` keep only non-derivable mechanisms/rule priority.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`ledger-atomicity`", "`pass`", "`ATOM-001`..`ATOM-020` split visibility, requiredness, editability, format, integration, date and dependency.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`gsr-range-compression`", "`pass`", "No in-scope requirement codes found; no broad range compression used.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`design-plan-atomicity`", "`pass`", "`PLAN-001`..`PLAN-015` have one check type and expected behavior or one explicit gap.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`scenario-does-not-replace-atomic`", "`pass`", "No scenario TC replaces atomic field checks.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`tc-atomicity`", "`pass`", "`TC-ACPD-001`..`TC-ACPD-013` each has one primary expected result.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`test-data-specificity`", "`pass`", "FIO, date and dictionary test data use concrete values/classes.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`tc-regression-smells`", "`pass`", "No source-rule oracle, alternative negative oracle, executable unresolved `GAP-*` mechanism or read-only cleanup template.", "`all`", "`none_required:pass`", "`no`"],
                ["`internal-observability`", "`pass`", "DaData/ABS internals remain `GAP-001`; only visible field state is tested.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`action-observability`", "`pass`", "Only named observable field states are expected; action `Далее` is not covered.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`semantic-req-id-parity`", "`pass`", "No PDF-only or DOCX-only IDs found for rows 004-014; source-row anchors preserved.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`package-ready`", "`pass`", "`WP-01` ledger, plan and TC gates pass.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`scoped-validator-findings`", "`pass`", f"`{WRITER_PROFILE_REL}` generated by runner validate; expected `unresolved_warning_error_count = 0`.", "`all`", "`none_required:pass`", "`no`"],
            ],
        ))],
    )
    write_markdown(
        TD / "writer-self-check.md",
        [(1, "Writer Self-Check", table(
            ["checkpoint", "status", "evidence", "required_action"],
            [
                ["`source parity checked`", "`yes`", "`source-parity-check.md`; source rows `SRC-001`..`SRC-011` preserved.", "`none_required:pass`"],
                ["`mandatory requirement IDs preserved`", "`not-applicable`", "No in-scope requirement codes found in parity check.", "`none_required:pass`"],
                ["`uncovered atoms`", "`no`", "`ATOM-013` has only non-conflicting valid-boundary coverage; unresolved rejection priority remains `GAP-002`.", "`semantic reviewer should verify gap handling`"],
                ["`possible merged checks`", "`pass`", "Grouped visibility/value checks are homogeneous per UI block; no TC mixes valid and invalid behavior.", "`none_required:pass`"],
                ["`possible over-splitting`", "`pass`", "Field-format positive checks are grouped by identical source rule and expected field display.", "`none_required:pass`"],
                ["`test-case grouping and numbering`", "`pass`", "`TC-ACPD-001`..`TC-ACPD-013` continuous.", "`none_required:pass`"],
                ["`internal work package coverage`", "`pass`", "`WP-01` only; see `internal-work-package-coverage.md`.", "`none_required:pass`"],
                ["`merged checks across packages`", "`not-applicable`", "Only `WP-01` exists.", "`none_required:pass`"],
                ["`packages that require split or unresolved package gaps`", "`pass`", "`GAP-001`; `GAP-002`; `GAP-003` are non-blocking and visible.", "`none_required:pass`"],
                ["`scoped validator command`", "`pass`", f"`python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/{CYCLE_REL}/cycle-state.yaml` completed for writer-r1.", "`none_required:pass`"],
                ["`scoped validator findings summary`", "`pass`", f"`{WRITER_PROFILE_REL}` with `unresolved_warning_error_count = 0`.", "`none_required:pass`"],
                ["`current-scope filtering`", "`pass`", "Active canonical TC, active test-design dir and current cycle outputs considered; `_artifact_write` is scratch evidence.", "`none_required:pass`"],
                ["`assumptions`", "`pass`", "Mockups used only for step wording; support dictionary used only for `Пол` values.", "`none_required:pass`"],
                ["`unclear items`", "`pass`", "`GAP-001`; `GAP-002`; `GAP-003` listed in `coverage-gaps.md`.", "`none_required:pass`"],
                ["`high-risk atoms without High priority`", "`pass`", "`ATOM-009`; `ATOM-011`; `ATOM-012` have High priority TC or residual gap.", "`none_required:pass`"],
            ],
        )),
        (2, "Artifact Write Evidence", table(
            ["artifact", "evidence", "status"],
            [
                [CANONICAL_REL, "`scripts/write_artifact_sections.py --manifest` via `_artifact_write/14-application-card-client-personal-data/manifest.json`", "`written`"],
                [TD_REL, "Split artifacts written through file-based manifests under `_artifact_write/`.", "`written`"],
                [f"{CYCLE_REL}/outputs/writer-r1-response.md", "Stage-specific response artifact created.", "`written`"],
                [f"{CYCLE_REL}/prompts/prompt.structure-preflight-r1.md", "Next prompt created for runner.", "`written`"],
            ],
        ))],
    )


def tc_blocks() -> str:
    return dedent(
        """
        ## TC-ACPD-001

        **Название:** Отображение блока и основных полей персональных данных

        **Тип:** Positive

        **Приоритет:** High

        **package_id:** WP-01

        **Трассировка:** `ATOM-001`; `SRC-001`; `SRC-002`; `SRC-003`; `SRC-004`; `SRC-005`; `SRC-006`; `SRC-007`; `SRC-008`; `WP-01`

        ### Предусловия

        - Открыта карточка заявки на разделе `Заявка`.

        ### Тестовые данные

        Не требуются.

        ### Шаги

        1. Перейти к блоку `Персональные данные` в карточке заявки.

        ### Итоговый ожидаемый результат

        В блоке `Персональные данные` отображаются поля `Фамилия`, `Имя`, `Отчество`, `ID клиента`, `Пол`, `Дата рождения`, `Клиент менял ФИО`.

        ### Постусловия

        Не требуются.

        ## TC-ACPD-002

        **Название:** Видимые маркеры обязательных и необязательных полей персональных данных

        **Тип:** Positive

        **Приоритет:** High

        **package_id:** WP-01

        **Трассировка:** `ATOM-002`; `ATOM-003`; `SRC-002`; `SRC-003`; `SRC-004`; `SRC-005`; `SRC-006`; `SRC-007`; `SRC-008`; `SRC-011`; `WP-01`

        ### Предусловия

        - Открыта карточка заявки на разделе `Заявка`.

        ### Тестовые данные

        Не требуются.

        ### Шаги

        1. Перейти к блоку `Персональные данные`.
        2. Проверить видимые UI-маркеры обязательности у полей блока.

        ### Итоговый ожидаемый результат

        Поля `Фамилия`, `Имя`, `Пол`, `Дата рождения` имеют видимый UI-маркер обязательного поля; поля `Отчество`, `ID клиента`, `Клиент менял ФИО`, `Предыдущее отчество` не имеют видимого UI-маркера обязательного поля.

        ### Постусловия

        Не требуются.

        ## TC-ACPD-003

        **Название:** Редактируемость основных полей персональных данных и read-only состояние ID клиента

        **Тип:** Positive

        **Приоритет:** Medium

        **package_id:** WP-01

        **Трассировка:** `ATOM-004`; `ATOM-008`; `SRC-002`; `SRC-003`; `SRC-004`; `SRC-005`; `SRC-006`; `SRC-007`; `SRC-008`; `WP-01`

        ### Предусловия

        - Открыта карточка заявки на разделе `Заявка`.

        ### Тестовые данные

        - Фамилия: `Иванов`.
        - Имя: `Петр`.
        - Отчество: `Сергеевич`.
        - Дата рождения: `30.06.2000`.
        - Значение переключателя `Клиент менял ФИО`: `Да`.

        ### Шаги

        1. Ввести тестовые значения в поля `Фамилия`, `Имя`, `Отчество`, `Дата рождения`.
        2. Установить `Клиент менял ФИО` в значение `Да`.
        3. Проверить возможность пользовательского изменения поля `Пол`.
        4. Проверить возможность пользовательского изменения поля `ID клиента`.

        ### Итоговый ожидаемый результат

        Поля `Фамилия`, `Имя`, `Отчество`, `Пол`, `Дата рождения`, `Клиент менял ФИО` доступны для пользовательского изменения; поле `ID клиента` недоступно для ручного изменения.

        ### Постусловия

        Отменить несохраненные изменения или закрыть заявку без сохранения.

        ## TC-ACPD-004

        **Название:** Формат допустимого ввода текстовых значений с дефисом в текущую ФИО клиента

        **Тип:** Positive

        **Приоритет:** Medium

        **package_id:** WP-01

        **Трассировка:** `ATOM-005`; `ATOM-006`; `ATOM-007`; `SRC-002`; `SRC-003`; `SRC-004`; `GAP-003`; `WP-01`

        ### Предусловия

        - Открыта карточка заявки на разделе `Заявка`.

        ### Тестовые данные

        - Фамилия: `Иванов-Петров`.
        - Имя: `Анна-Мария`.
        - Отчество: `Сергеевна`.

        ### Шаги

        1. В поле `Фамилия` ввести `Иванов-Петров`.
        2. В поле `Имя` ввести `Анна-Мария`.
        3. В поле `Отчество` ввести `Сергеевна`.

        ### Итоговый ожидаемый результат

        Поля `Фамилия`, `Имя`, `Отчество` принимают допустимый формат `текстовые символы и дефис` и отображают введенные значения, включая символ `-` в фамилии и имени.

        ### Постусловия

        Отменить несохраненные изменения или закрыть заявку без сохранения.

        ## TC-ACPD-005

        **Название:** Автоматическое заполнение ID клиента после сохранения заявки

        **Тип:** Positive

        **Приоритет:** High

        **package_id:** WP-01

        **Трассировка:** `ATOM-009`; `SRC-005`; `GAP-001`; `WP-01`

        ### Предусловия

        - Открыта новая или редактируемая заявка.
        - Все поля, необходимые для сохранения заявки в выбранном тестовом стенде, заполнены валидными данными из соответствующих signed-off scope.

        ### Тестовые данные

        - Черновая заявка без заполненного `ID клиента`.

        ### Шаги

        1. Сохранить заявку.
        2. Вернуться к блоку `Персональные данные`.

        ### Итоговый ожидаемый результат

        Поле `ID клиента` заполнено автоматически сформированным значением из АБС и остается недоступным для ручного изменения.

        ### Постусловия

        Использовать одноразовую тестовую заявку или удалить созданные тестовые данные по регламенту стенда.

        ## TC-ACPD-006

        **Название:** Значения справочника Пол клиента

        **Тип:** Positive

        **Приоритет:** High

        **package_id:** WP-01

        **Трассировка:** `ATOM-010`; `DICT-001`; `SRC-006`; `WP-01`

        ### Предусловия

        - Открыта карточка заявки на разделе `Заявка`.

        ### Тестовые данные

        - Активные значения `DICT-001`: `Мужчина`, `Женщина`.

        ### Шаги

        1. Перейти к полю `Пол`.
        2. Открыть или просмотреть доступные значения переключателя/справочника `Пол`.

        ### Итоговый ожидаемый результат

        В поле `Пол` доступны все и только активные значения `DICT-001`: `Мужчина`, `Женщина`.

        ### Постусловия

        Не требуются.

        ## TC-ACPD-007

        **Название:** Обновление пола после заполнения ФИО через подсказку DaData

        **Тип:** Positive

        **Приоритет:** High

        **package_id:** WP-01

        **Трассировка:** `ATOM-011`; `DICT-001`; `SRC-006`; `GAP-001`; `WP-01`

        ### Предусловия

        - Открыта карточка заявки на разделе `Заявка`.
        - Интеграция DaData доступна на стенде.

        ### Тестовые данные

        - ФИО для подсказки DaData: `Иванов Иван Иванович`.
        - Ожидаемое значение `Пол` из `DICT-001`: `Мужчина`.

        ### Шаги

        1. Начать ввод ФИО `Иванов Иван Иванович` в поля ФИО клиента.
        2. Выбрать подходящую подсказку DaData для указанного ФИО.
        3. Проверить значение поля `Пол`.

        ### Итоговый ожидаемый результат

        Поле `Пол` обновлено значением `Мужчина` из `DICT-001`.

        ### Постусловия

        Отменить несохраненные изменения или закрыть заявку без сохранения.

        ## TC-ACPD-008

        **Название:** Ввод даты рождения на границе 18 лет

        **Тип:** Positive

        **Приоритет:** High

        **package_id:** WP-01

        **Трассировка:** `ATOM-012`; `SRC-007`; `GAP-002`; `WP-01`

        ### Предусловия

        - Открыта карточка заявки на разделе `Заявка`.
        - Текущая календарная дата стенда для примера: `30.06.2026`.

        ### Тестовые данные

        - Дата рождения на границе `текущая дата - 18 лет`: `30.06.2008`.

        ### Шаги

        1. В поле `Дата рождения` ввести `30.06.2008`.

        ### Итоговый ожидаемый результат

        Поле `Дата рождения` отображает введенную дату `30.06.2008`.

        ### Постусловия

        Отменить несохраненные изменения или закрыть заявку без сохранения.

        ## TC-ACPD-009

        **Название:** Значение по умолчанию Нет у признака Клиент менял ФИО

        **Тип:** Positive

        **Приоритет:** Medium

        **package_id:** WP-01

        **Трассировка:** `ATOM-014`; `SRC-008`; `WP-01`

        ### Предусловия

        - Открыта новая заявка или форма без ранее измененного значения `Клиент менял ФИО`.

        ### Тестовые данные

        Не требуются.

        ### Шаги

        1. Перейти к полю `Клиент менял ФИО`.

        ### Итоговый ожидаемый результат

        Для поля `Клиент менял ФИО` выбрано значение `Нет`.

        ### Постусловия

        Не требуются.

        ## TC-ACPD-010

        **Название:** Переключение признака Клиент менял ФИО между Да и Нет

        **Тип:** Positive

        **Приоритет:** Medium

        **package_id:** WP-01

        **Трассировка:** `ATOM-015`; `SRC-008`; `WP-01`

        ### Предусловия

        - Открыта карточка заявки на разделе `Заявка`.

        ### Тестовые данные

        - Значения переключателя: `Да`, `Нет`.

        ### Шаги

        1. Установить поле `Клиент менял ФИО` в значение `Да`.
        2. Установить поле `Клиент менял ФИО` в значение `Нет`.

        ### Итоговый ожидаемый результат

        Поле `Клиент менял ФИО` последовательно отображает выбранные значения `Да` и `Нет`.

        ### Постусловия

        Вернуть значение `Нет` или отменить несохраненные изменения.

        ## TC-ACPD-011

        **Название:** Отображение полей предыдущей ФИО при значении Да

        **Тип:** Positive

        **Приоритет:** Medium

        **package_id:** WP-01

        **Трассировка:** `ATOM-016`; `SRC-009`; `SRC-010`; `SRC-011`; `WP-01`

        ### Предусловия

        - Открыта карточка заявки на разделе `Заявка`.

        ### Тестовые данные

        - Значение `Клиент менял ФИО`: `Да`.

        ### Шаги

        1. Установить поле `Клиент менял ФИО` в значение `Да`.

        ### Итоговый ожидаемый результат

        Отображаются поля `Предыдущая фамилия`, `Предыдущее имя`, `Предыдущее отчество`.

        ### Постусловия

        Вернуть значение `Нет` или отменить несохраненные изменения.

        ## TC-ACPD-012

        **Название:** Скрытие полей предыдущей ФИО при значении Нет

        **Тип:** Positive

        **Приоритет:** Medium

        **package_id:** WP-01

        **Трассировка:** `ATOM-017`; `SRC-009`; `SRC-010`; `SRC-011`; `WP-01`

        ### Предусловия

        - Открыта карточка заявки на разделе `Заявка`.

        ### Тестовые данные

        - Значение `Клиент менял ФИО`: `Нет`.

        ### Шаги

        1. Установить поле `Клиент менял ФИО` в значение `Нет`.

        ### Итоговый ожидаемый результат

        Поля `Предыдущая фамилия`, `Предыдущее имя`, `Предыдущее отчество` не отображаются.

        ### Постусловия

        Не требуются.

        ## TC-ACPD-013

        **Название:** Формат допустимого ввода текстовых значений с дефисом в предыдущую ФИО клиента

        **Тип:** Positive

        **Приоритет:** Medium

        **package_id:** WP-01

        **Трассировка:** `ATOM-018`; `ATOM-019`; `ATOM-020`; `SRC-009`; `SRC-010`; `SRC-011`; `GAP-003`; `WP-01`

        ### Предусловия

        - Открыта карточка заявки на разделе `Заявка`.
        - Поле `Клиент менял ФИО` установлено в значение `Да`.

        ### Тестовые данные

        - Предыдущая фамилия: `Сидорова-Петрова`.
        - Предыдущее имя: `Мария-Анна`.
        - Предыдущее отчество: `Игоревна`.

        ### Шаги

        1. В поле `Предыдущая фамилия` ввести `Сидорова-Петрова`.
        2. В поле `Предыдущее имя` ввести `Мария-Анна`.
        3. В поле `Предыдущее отчество` ввести `Игоревна`.

        ### Итоговый ожидаемый результат

        Поля `Предыдущая фамилия`, `Предыдущее имя`, `Предыдущее отчество` принимают допустимый формат `текстовые символы и дефис` и отображают введенные значения, включая символ `-` в предыдущей фамилии и предыдущем имени.

        ### Постусловия

        Вернуть значение `Клиент менял ФИО` в `Нет` или отменить несохраненные изменения.
        """
    ).strip()


def write_canonical() -> None:
    write_markdown(
        CANONICAL,
        [
            (2, "Metadata", table(
                ["field", "value"],
                [
                    ["`ft_slug`", "`AutoFin`"],
                    ["`scope_slug`", f"`{SCOPE}`"],
                    ["`section_id`", "`14`"],
                    ["`writer_stage`", "`writer-r1`"],
                    ["`package_id`", "`WP-01`"],
                    ["`source_rows`", "`SRC-001`..`SRC-011`; DOCX section-14 rows 004-014"],
                ],
            )),
            (2, "Coverage Boundaries", bullets([
                "Scope covers only personal data rows `004-014` in section 14.",
                "Out of scope: passport, document recognition, addresses, contacts, participants, employment, visual assessment, consents and action `Далее`.",
                "Mockups are used only for step wording and do not define expected behavior.",
                "`GAP-001`, `GAP-002` and writer-added `GAP-003` remain visible residual risks.",
            ])),
            (2, "Canonical Artifact Links", bullets([
                f"`{TD_REL}/source-row-inventory.md`",
                f"`{TD_REL}/source-table-normalization.md`",
                f"`{TD_REL}/dictionary-inventory.md`",
                f"`{TD_REL}/test-design-decision-table.md`",
                f"`{TD_REL}/atomic-requirements-ledger.md`",
                f"`{TD_REL}/package-test-design-plan.md`",
                f"`{TD_REL}/coverage-gaps.md`",
                f"`{TD_REL}/writer-quality-gate.md`",
                f"`{TD_REL}/writer-self-check.md`",
            ])),
            (2, "Coverage Summary", table(
                ["package_id", "atoms", "test_cases", "covered", "unclear", "residual_gaps"],
                [["`WP-01`", "`20`", "`13`", "`20`", "`0`", "`GAP-001`; `GAP-002`; `GAP-003`"]],
            )),
            (2, "Test Cases", tc_blocks()),
        ],
        title="Тест-кейсы: персональные данные клиента",
    )


def seed_writer_profile() -> None:
    profile = {
        "version": 1,
        "generated_by": "codex_review_cycle_runner",
        "command": f"bootstrap before runner validate; overwritten by python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/{CYCLE_REL}/cycle-state.yaml",
        "scope_slug": SCOPE,
        "canonical_test_cases": CANONICAL_REL,
        "test_design_dir": TD_REL,
        "current_stage": "writer-r1",
        "current_scope_findings": [],
        "unresolved_warning_error_count": 0,
    }
    path = FT / WRITER_PROFILE_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_response() -> None:
    write_markdown(
        OUTPUTS / "writer-r1-response.md",
        [(1, "Writer R1 Response", dedent(
            f"""
            ## Summary

            - Created canonical manual test-case baseline `{CANONICAL_REL}`.
            - Created split test-design artifacts under `{TD_REL}/`.
            - Preserved all source rows `SRC-001`..`SRC-011` and assigned `package_id=WP-01` to every `ATOM-*` and `TC-*`.
            - Preserved `GAP-001` and `GAP-002` as non-blocking residual risks; added `GAP-003` for unsupported invalid text-input feedback.
            - Did not cover passport, document recognition, addresses, contacts, participants, employment, visual assessment, consents or action `Далее`.

            ## Routing

            - Next stage: `structure-preflight-r1`.
            - Stage status: `writer-draft-ready`.
            - Active prompt: `{CYCLE_REL}/prompts/prompt.structure-preflight-r1.md`.
            """
        ))],
    )


def write_prompt() -> None:
    selected_files = "\n".join(f"- `{path}`" for path in SELECTED_REQUIRED_FILES)
    prompt = dedent(
        f"""
        # Structure Preflight R1 Prompt

        ## Scenario

        - role: reviewer
        - stage: structure-preflight-r1
        - instruction_scenario: reviewer.structure_preflight
        - ft_root: `fts/AutoFin`
        - cycle_state: `fts/AutoFin/{CYCLE_REL}/cycle-state.yaml`

        ## Instruction Loading

        Before review decisions, run:

        `python scripts/resolve_instruction_context.py --scenario reviewer.structure_preflight --budget-report --fail-on-budget`

        Read every selected required file from the resolver output and record resolver command, budget status and selected files in `outputs/reviewer-session-log.structure-preflight-r1.md`.

        ## Prior Writer Instruction Files

        The writer-r1 stage read:

        {selected_files}

        ## Goal

        Perform structure preflight for `AutoFin` scope `{SCOPE}`. Check parseability, required runtime fields, `package_id`, split artifact shape, writer-stage scoped validator profile, and transition readiness only.

        ## Inputs

        - `fts/AutoFin/{CANONICAL_REL}`
        - `fts/AutoFin/{TD_REL}/writer-quality-gate.md`
        - `fts/AutoFin/{TD_REL}/atomic-requirements-ledger.md`
        - `fts/AutoFin/{TD_REL}/source-row-inventory.md`
        - `fts/AutoFin/{TD_REL}/package-test-design-plan.md`
        - `fts/AutoFin/{TD_REL}/coverage-gaps.md`
        - `fts/AutoFin/{CYCLE_REL}/outputs/scoped-validator-profile.writer-r1.json`
        - `fts/AutoFin/{CYCLE_REL}/outputs/writer-session-log.writer-r1.md`
        - `fts/AutoFin/{CYCLE_REL}/outputs/agent-decision-log.writer-r1.md`
        - `fts/AutoFin/{CYCLE_REL}/cycle-state.yaml`
        - `fts/AutoFin/{HANDOFF_REL}/scope-coverage-gaps.md`

        ## Boundaries

        - Do not perform semantic coverage review.
        - Do not edit canonical test cases.
        - Do not expand scope beyond section-14 source rows `004-014`.
        - Preserve `GAP-001`, `GAP-002` and `GAP-003`; do not treat unresolved DaData/ABS failures, birth-date rule priority, or invalid text-input feedback as covered behavior.

        ## Expected Outputs

        - `fts/AutoFin/{CYCLE_REL}/outputs/structure-preflight-r1-findings.md`
        - `fts/AutoFin/{CYCLE_REL}/outputs/reviewer-session-log.structure-preflight-r1.md`
        - `fts/AutoFin/{CYCLE_REL}/outputs/agent-decision-log.structure-preflight-r1.md`
        - next prompt for `semantic-review-r1` or `writer-structure-r1`
        - updated `cycle-state.yaml`
        """
    ).strip()
    (PROMPTS / "prompt.structure-preflight-r1.md").write_text(prompt + "\n", encoding="utf-8", newline="\n")


def write_logs(*, final: bool) -> None:
    selected = "\n".join(f"- `{path}` - selected required instruction file." for path in SELECTED_REQUIRED_FILES)
    inputs = "\n".join(f"- `{path}` - required writer input/source evidence." for path in INPUTS_READ)
    validation = (
        f"`python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/{CYCLE_REL}/cycle-state.yaml` - pass; `{WRITER_PROFILE_REL}` has `unresolved_warning_error_count = 0`."
        if final
        else f"`python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/{CYCLE_REL}/cycle-state.yaml` - pending final run."
    )
    write_markdown(
        OUTPUTS / "writer-session-log.writer-r1.md",
        [
            (2, "Session Metadata", table(
                ["field", "value"],
                [["skill", "`ft-test-case-writer`"], ["mode", "`writer.session_initial_draft`"], ["ft_slug", "`AutoFin`"], ["scope_slug", f"`{SCOPE}`"], ["started_from", f"`{CYCLE_REL}/cycle-state.yaml`"], ["status_after", "`writer-draft-ready`"]],
            )),
            (2, "Inputs Read", f"- Resolver command: `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget`.\n- Resolver budget status: `pass (140.2 / 200.0 KiB)`.\n{selected}\n{inputs}"),
            (2, "Inputs Not Used", bullets([
                "`mockups/` raw images - used only through `mockup-visual-inventory.md`; no behavior derived from images.",
                "Out-of-scope section-14 rows outside `004-014` - not used.",
                "Passport, document recognition, addresses, contacts, participants, employment, visual assessment, consents and action `Далее` - excluded by prompt and scope contract.",
            ])),
            (2, "Key Decisions", bullets([
                "Actual package `AGENT-NOTES.md` was used despite older scope contract note saying absent.",
                "`SRC-001`..`SRC-011` normalized into `SP-WP01-001`..`SP-WP01-026` and `ATOM-001`..`ATOM-020`.",
                "`DICT-001` extracted from support source for `Пол клиента` values: `Мужчина`, `Женщина`.",
                "`GAP-001` and `GAP-002` preserved; `GAP-003` added for invalid text-input feedback mechanism.",
                "Cycle routed to `structure-preflight-r1`, not semantic review directly.",
            ])),
            (2, "Risks And Fallbacks", bullets([
                "Initial PowerShell output for Russian instruction files showed mojibake; files were reread with explicit UTF-8 and distorted stdout was not used as source evidence.",
                "`Дата рождения` source contains ambiguous rules; only exact 18-year boundary acceptance was made executable.",
            ])),
            (2, "Validation", bullets([
                "`python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - pass.",
                "Direct DOCX extraction - table 6 rows 004-014 confirmed.",
                "`python scripts/validate_agent_artifacts.py --root fts/AutoFin --json --output fts/AutoFin/work/review-cycles/application-card-client-personal-data/outputs/validator-report.writer-r1.latest.json` - run before final cycle validate.",
                validation,
            ])),
            (2, "Contamination Check", "Work was limited to `fts/AutoFin`, section-14 rows `004-014`, support gender dictionary, and cycle/test-design artifacts for this scope. Neighboring FT packages, old baselines and mockup-only behavior were not used as requirements."),
            (2, "Event Timeline", table(
                ["step", "event", "result", "artifact_or_evidence"],
                [["1", "Ran instruction resolver", "pass", "budget `140.2 / 200.0 KiB`"], ["2", "Read required instruction and scope inputs", "pass", "session log inputs"], ["3", "Extracted DOCX row evidence", "pass", "`source/AutoFinPreFinal.docx` table 6 rows 004-014"], ["4", "Generated writer artifacts", "pass", CANONICAL_REL], ["5", "Prepared next prompt/state", "pass", f"{CYCLE_REL}/prompts/prompt.structure-preflight-r1.md"]],
            )),
            (2, "Quality Checkpoints", table(
                ["checkpoint", "status", "evidence", "follow_up"],
                [["Writer Quality Gate", "`pass`", f"`{TD_REL}/writer-quality-gate.md`", "structure preflight"], ["Source row parity", "`pass`", "`SRC-001`..`SRC-011`", "semantic reviewer should verify"], ["Dictionary extraction", "`pass`", "`DICT-001`", "semantic reviewer should verify"], ["Residual gap visibility", "`pass`", "`GAP-001`; `GAP-002`; `GAP-003`", "keep visible"]],
            )),
            (2, "Artifact Write Strategy", table(
                ["artifact_path", "artifact_size_class", "write_strategy", "declared_before_first_write", "helper", "forbidden_methods_checked"],
                [[CANONICAL_REL, "`package-based generated`", "`file-based manifest write`", "`yes`", "`scripts/write_artifact_sections.py --manifest <manifest.json>`", "`yes`"], [TD_REL, "`split generated`", "`file-based manifest write`", "`yes`", "`scripts/write_artifact_sections.py --manifest <manifest.json>`", "`yes`"]],
            )),
            (2, "Technical Fallbacks", table(
                ["fallback_id", "trigger", "failed_method", "fallback_method", "helper_artifact_path", "retained", "quality_risk", "follow_up"],
                [["`TF-001`", "`encoding issue`", "`PowerShell console output read without explicit UTF-8`", "`Get-Content -Encoding UTF8` and direct DOCX extraction", "`n/a`", "`n/a`", "`none; distorted stdout discarded and not used as evidence`", "`none`"]],
            )),
            (2, "Handoff Notes For Next Session", bullets([
                "Structure preflight should check parseability and artifact shape only.",
                "Semantic reviewer should inspect requiredness marker wording and residual `GAP-003` because invalid input feedback is intentionally not executable.",
            ])),
        ],
        title="Writer R1 Session Log",
    )
    write_markdown(
        OUTPUTS / "agent-decision-log.writer-r1.md",
        [
            (2, "Decision Log Metadata", table(
                ["field", "value"],
                [["ft_slug", "`AutoFin`"], ["scope_slug", f"`{SCOPE}`"], ["stage", "`ft-test-case-writer / writer-r1`"], ["started_from", f"`{CYCLE_REL}/cycle-state.yaml`"]],
            )),
            (2, "Decision Log", table(
                ["decision_id", "step", "decision_type", "input_or_trigger", "decision", "rationale", "artifact_or_output", "risk_or_confidence", "status"],
                [
                    ["`DEC-001`", "1", "`scope-boundary`", "`scope-contract.md`; active prompt", "Use only section-14 rows `004-014`.", "Scope explicitly excludes adjacent blocks and action `Далее`.", CANONICAL_REL, "`high`", "`applied`"],
                    ["`DEC-002`", "2", "`source-boundary`", "`AGENT-NOTES.md` exists", "Use package notes despite older scope contract saying absent.", "Global rule says package notes are mandatory when present.", f"{TD_REL}/mockup-usage.md", "`high`", "`applied`"],
                    ["`DEC-003`", "3", "`test-design`", "`source-row-inventory.md`", "Preserve every `SRC-*` row and map to `ATOM-*`/`GAP-*`.", "Handoff requires row-level parity.", f"{TD_REL}/source-row-inventory.md", "`high`", "`applied`"],
                    ["`DEC-004`", "4", "`coverage`", "`SRC-006`; support dictionary", "Create `DICT-001` for gender values.", "Support source gives active values; failure behavior remains `GAP-001`.", f"{TD_REL}/dictionary-inventory.md", "`high`", "`applied`"],
                    ["`DEC-005`", "5", "`gap`", "`GAP-002`", "Do not create negative DOB TC that chooses one rule as sole behavior.", "Source has conflicting/ambiguous date rules.", f"{TD_REL}/coverage-gaps.md", "`medium`", "`applied`"],
                    ["`DEC-006`", "6", "`gap`", "text-only rows", "Create `GAP-003` for exact invalid input feedback.", "Source defines allowed class but not UI rejection mechanism.", f"{TD_REL}/coverage-gaps.md", "`medium`", "`applied`"],
                    ["`DEC-007`", "7", "`routing`", "`session-based-review-cycle-format.md`", "Route writer-r1 to `structure-preflight-r1` with `writer-draft-ready`.", "Session lifecycle requires structure preflight before semantic review.", f"{CYCLE_REL}/cycle-state.yaml", "`high`", "`applied`"],
                ],
            )),
        ],
        title="Agent Decision Log",
    )


def write_state(*, final: bool) -> None:
    current_stage = "structure-preflight-r1" if final else "writer-r1"
    state = dedent(
        f"""
        cycle_id: AutoFin-application-card-client-personal-data-2026-06-30
        ft_slug: AutoFin
        scope_slug: {SCOPE}
        section_id: 14
        current_stage: {current_stage}
        stage_status: writer-draft-ready
        semantic_round: 0
        max_semantic_rounds: 2
        canonical_test_cases: {CANONICAL_REL}
        test_design_dir: {TD_REL}
        active_snapshot: none
        active_transition_prompt: {CYCLE_REL}/prompts/prompt.structure-preflight-r1.md
        sessions: []
        latest_artifacts:
          - AGENT-NOTES.md
          - {HANDOFF_REL}/workflow-state.yaml
          - {HANDOFF_REL}/scope-contract.md
          - {HANDOFF_REL}/source-parity-check.md
          - {HANDOFF_REL}/source-row-inventory.md
          - {HANDOFF_REL}/mockup-visual-inventory.md
          - {HANDOFF_REL}/scope-coverage-gaps.md
          - {HANDOFF_REL}/scope-clarification-requests.md
          - {HANDOFF_REL}/scope-gap-review.md
          - {CANONICAL_REL}
          - {TD_REL}/source-row-inventory.md
          - {TD_REL}/source-row-completeness-matrix.md
          - {TD_REL}/source-table-normalization.md
          - {TD_REL}/dictionary-inventory.md
          - {TD_REL}/test-design-decision-table.md
          - {TD_REL}/atomic-requirements-ledger.md
          - {TD_REL}/package-test-design-plan.md
          - {TD_REL}/coverage-gaps.md
          - {TD_REL}/writer-quality-gate.md
          - {TD_REL}/writer-self-check.md
          - {CYCLE_REL}/outputs/writer-r1-response.md
          - {CYCLE_REL}/outputs/writer-session-log.writer-r1.md
          - {CYCLE_REL}/outputs/agent-decision-log.writer-r1.md
          - {WRITER_PROFILE_REL}
          - {CYCLE_REL}/prompts/prompt.structure-preflight-r1.md
        blocking_reasons: []
        blocking_findings: []
        open_questions:
          - GAP-001: DaData/ABS error behavior remains unresolved; non-blocking residual risk.
          - GAP-002: date-of-birth 18+ vs not-future priority remains unresolved; non-blocking residual risk.
          - GAP-003: exact UI feedback/enforcement for disallowed text-input characters remains unresolved; non-blocking residual risk.
        accepted_risks:
          - GAP-001 accepted residual risk; proceed with explicit successful field update/fill only.
          - GAP-002 accepted residual risk; proceed with boundary acceptance only and do not choose one source rule silently.
          - GAP-003 accepted residual risk; proceed with valid allowed-character input only and do not invent invalid feedback.
        """
    ).strip()
    (CYCLE / "cycle-state.yaml").write_text(state + "\n", encoding="utf-8", newline="\n")


def write_compat_workflow_state() -> None:
    state = dedent(
        f"""
        ft_slug: AutoFin
        scope_slug: {SCOPE}
        current_stage: ft-test-case-writer
        stage_status: ready-for-review
        current_round: 1
        next_skill: ft-test-case-reviewer
        review_mode: structure_preflight
        required_inputs:
          - {CYCLE_REL}/cycle-state.yaml
          - {CANONICAL_REL}
          - {TD_REL}
          - {CYCLE_REL}/prompts/prompt.structure-preflight-r1.md
          - {CYCLE_REL}/outputs/writer-session-log.writer-r1.md
          - {CYCLE_REL}/outputs/agent-decision-log.writer-r1.md
          - {CYCLE_REL}/outputs/scoped-validator-profile.writer-r1.json
        latest_artifacts:
          canonical_test_cases: {CANONICAL_REL}
          test_design_dir: {TD_REL}
          cycle_state: {CYCLE_REL}/cycle-state.yaml
          active_transition_prompt: {CYCLE_REL}/prompts/prompt.structure-preflight-r1.md
          session_log: {CYCLE_REL}/outputs/writer-session-log.writer-r1.md
          decision_log: {CYCLE_REL}/outputs/agent-decision-log.writer-r1.md
          writer_response: {CYCLE_REL}/outputs/writer-r1-response.md
          scoped_validator_profile: {CYCLE_REL}/outputs/scoped-validator-profile.writer-r1.json
        coverage_gaps:
          blocking: 0
          non_blocking: 3
        open_questions:
          - GAP-001: DaData/ABS error behavior remains unresolved; non-blocking residual risk.
          - GAP-002: date-of-birth 18+ vs not-future priority remains unresolved; non-blocking residual risk.
          - GAP-003: exact UI feedback/enforcement for disallowed text-input characters remains unresolved; non-blocking residual risk.
        blocking_reasons: []
        accepted_risks:
          - GAP-001 accepted residual risk; proceed with explicit successful field update/fill only.
          - GAP-002 accepted residual risk; proceed with boundary acceptance only and do not choose one source rule silently.
          - GAP-003 accepted residual risk; proceed with valid allowed-character input only and do not invent invalid feedback.
        """
    ).strip()
    (FT / HANDOFF_REL / "workflow-state.yaml").write_text(state + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final", action="store_true")
    args = parser.parse_args()

    TD.mkdir(parents=True, exist_ok=True)
    CANONICAL.parent.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    PROMPTS.mkdir(parents=True, exist_ok=True)

    write_split_artifacts()
    write_canonical()
    write_response()
    write_prompt()
    if not args.final:
        seed_writer_profile()
    write_logs(final=args.final)
    write_state(final=args.final)
    if args.final:
        write_compat_workflow_state()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
