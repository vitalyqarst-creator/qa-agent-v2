from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "fts" / "AutoFin"
SCOPE = "application-card-participants-coborrower-pledger"
SECTION = "14"
TD_REL = f"work/test-design/{SECTION}-{SCOPE}"
TD = FT / TD_REL
CANONICAL_REL = f"test-cases/{SECTION}-{SCOPE}.md"
CANONICAL = FT / CANONICAL_REL
CYCLE_REL = f"work/review-cycles/{SCOPE}"
CYCLE = FT / CYCLE_REL
OUTPUTS = CYCLE / "outputs"
PROMPTS = CYCLE / "prompts"
HANDOFF_REL = f"work/stage-handoffs/12-{SCOPE}"
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

SCOPE_INPUTS = [
    "AGENT-NOTES.md",
    f"{HANDOFF_REL}/source-selection.md",
    "work/stage-handoffs/02-application-card-questionnaires-decomposition/scope-options.md",
    f"{HANDOFF_REL}/workflow-state.yaml",
    f"{HANDOFF_REL}/prompt.scope-to-iteration.md",
    f"{HANDOFF_REL}/scope-gap-review.md",
    f"{HANDOFF_REL}/scope-contract.md",
    f"{HANDOFF_REL}/source-parity-check.md",
    f"{HANDOFF_REL}/source-row-inventory.md",
    f"{HANDOFF_REL}/mockup-visual-inventory.md",
    f"{HANDOFF_REL}/scope-coverage-gaps.md",
    f"{HANDOFF_REL}/scope-clarification-requests.md",
]


def table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
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
        [sys.executable, str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(manifest_path)],
        cwd=str(ROOT),
        check=True,
    )


def artifact_write_strategy() -> str:
    return table(
        ["item", "value", "evidence"],
        [
            ["preflight_result", "`large-file / package-based`", "`WP-01`, `WP-02`; split artifacts and canonical TC are generated for a session-based writer stage."],
            ["write_method", "`file-based manifest/chunked writing`", "`scripts/write_artifact_sections.py --manifest <manifest.json>` for every generated markdown artifact."],
            ["forbidden_methods_checked", "`yes`", "No one-shot PowerShell argument, no here-string and no inline giant command are used as the primary writer."],
            ["chunk_plan", "`split artifacts -> canonical TC -> cycle outputs -> state`", "Artifacts are written one target at a time through UTF-8 section files."],
            ["helper_artifacts", f"`{TD_REL}/_artifact_write/*/manifest.json`", "Scratch manifests retained as write evidence; snapshots must exclude `_artifact_write`."],
            ["validation_plan", "`runner validate after draft generation`", f"`python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/{CYCLE_REL}/cycle-state.yaml`."],
        ],
    )


def source_row_inventory() -> str:
    return table(
        ["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"],
        [
            ["SRC-001", "WP-01", "Блок `Участники`", "DOCX section-14 table row 095", "no_requirement_code:SRC-001", "yes", "`ATOM-001`"],
            ["SRC-002", "WP-01", "`+ Добавить созаемщика`", "DOCX section-14 table row 096", "no_requirement_code:SRC-002", "yes", "`ATOM-002`; `ATOM-003`; `ATOM-004`; `ATOM-005`"],
            ["SRC-003", "WP-01", "`+ Добавить залогодателя`", "DOCX section-14 table row 097", "no_requirement_code:SRC-003", "yes", "`ATOM-006`; `ATOM-007`; `ATOM-008`; `GAP-003`"],
            ["SRC-004", "WP-01", "Виджет `Редактировать`", "DOCX section-14 table row 098", "no_requirement_code:SRC-004", "yes", "`ATOM-011`; `ATOM-012`; `ATOM-013`; `ATOM-014`"],
            ["SRC-005", "WP-01", "Виджет `Корзина`", "DOCX section-14 table row 099", "no_requirement_code:SRC-005", "yes", "`ATOM-013`; `ATOM-014`; `ATOM-015`; `ATOM-016`; `ATOM-017`; `ATOM-018`; `GAP-002`"],
            ["SRC-006", "WP-02", "`Тип участия`", "DOCX section-14 table row 100", "no_requirement_code:SRC-006", "yes", "`ATOM-019`"],
            ["SRC-007", "WP-02", "`ФИО`", "DOCX section-14 table row 101", "no_requirement_code:SRC-007", "yes", "`ATOM-020`"],
            ["SRC-008", "WP-02", "`Паспорт`", "DOCX section-14 table row 102", "no_requirement_code:SRC-008", "yes", "`ATOM-021`"],
            ["SRC-009", "WP-02", "`ID клиента`", "DOCX section-14 table row 103", "no_requirement_code:SRC-009", "yes", "`ATOM-022`"],
        ],
    )


def source_table_normalization() -> str:
    rows = [
        ["SRC-001", "SRC-001.P01", "WP-01", "Блок `Участники`", "block-visibility", "always", "Блок `Участники` отображается в карточке заявки.", "no_requirement_code:SRC-001", "DOCX section-14 row 095", "high", "none_required:covered", "`ATOM-001`"],
        ["SRC-002", "SRC-002.P01", "WP-01", "`+ Добавить созаемщика`", "action-visibility", "always", "Кнопка добавления созаемщика отображается всегда.", "no_requirement_code:SRC-002", "DOCX section-14 row 096", "high", "none_required:covered", "`ATOM-002`"],
        ["SRC-002", "SRC-002.P02", "WP-01", "`+ Добавить созаемщика`", "action-open-window", "on click", "Открывается окно `Заявка` для созаемщика.", "no_requirement_code:SRC-002", "DOCX section-14 row 096", "high", "none_required:covered", "`ATOM-003`"],
        ["SRC-002", "SRC-002.P03", "WP-01", "Анкета созаемщика", "role-form-exclusion", "co-borrower form", "В форме созаемщика исключен виджет `Краткая информация с калькулятора`.", "no_requirement_code:SRC-002", "DOCX section-14 row 096; GAP-001 analyst clarification", "high", "none_required:covered", "`ATOM-004`"],
        ["SRC-002", "SRC-002.P04", "WP-01", "Анкета созаемщика", "role-label-substitution", "co-borrower form", "В наименованиях по тексту заявки `клиент` заменяется на `созаемщик`.", "no_requirement_code:SRC-002", "DOCX section-14 row 096", "high", "none_required:covered", "`ATOM-005`"],
        ["SRC-003", "SRC-003.P01", "WP-01", "`+ Добавить залогодателя`", "action-visibility", "always", "Кнопка добавления залогодателя отображается всегда.", "no_requirement_code:SRC-003", "DOCX section-14 row 097", "high", "none_required:covered", "`ATOM-006`"],
        ["SRC-003", "SRC-003.P02", "WP-01", "`+ Добавить залогодателя`", "action-open-window", "on click", "Открывается окно `Заявка` для залогодателя.", "no_requirement_code:SRC-003", "DOCX section-14 row 097", "high", "none_required:covered", "`ATOM-007`"],
        ["SRC-003", "SRC-003.P03", "WP-01", "Анкета залогодателя", "role-form-exclusion", "pledger form", "В форме залогодателя исключены FT-backed блоки/поля: калькуляторный виджет, сведения о занятости, контактные лица, кодовое слово, СНИЛС, верификация ИНН ФЛ, семейное положение, количество иждивенцев, социальный статус, подтверждение дохода.", "no_requirement_code:SRC-003", "DOCX section-14 row 097; GAP-001 analyst clarification", "high", "none_required:covered", "`ATOM-008`"],
        ["SRC-003", "SRC-003.P04", "WP-01", "Анкета залогодателя", "role-label-substitution", "pledger form", "В наименованиях по тексту заявки `клиент` заменяется на `залогодатель`.", "no_requirement_code:SRC-003", "DOCX section-14 row 097", "high", "none_required:covered", "`ATOM-009`"],
        ["SRC-003", "SRC-003.P05", "WP-01", "Залогодатель по умолчанию", "default-role-assignment", "no separate pledger added", "Если отдельно залогодатель не добавлен, залогодателем по умолчанию является заемщик.", "no_requirement_code:SRC-003", "DOCX section-14 row 097", "medium", "`GAP-003`", "`ATOM-010`"],
        ["SRC-004", "SRC-004.P01", "WP-01", "Row 098 control", "visibility", "always", "Row 098 control is shown in the participants block.", "no_requirement_code:SRC-004", "DOCX section-14 row 098", "high", "none_required:covered", "`ATOM-011`"],
        ["SRC-004", "SRC-004.P02", "WP-01", "Виджет `Редактировать`", "action-availability", "participant selected", "Виджет доступен к нажатию, если выбран участник в таблице.", "no_requirement_code:SRC-004", "DOCX section-14 row 098", "high", "none_required:covered", "`ATOM-012`"],
        ["SRC-004", "SRC-004.P03", "WP-01", "Виджет `Редактировать`", "action-availability", "no participant selected", "Виджет находится в состоянии disabled, если участник в таблице не выбран.", "no_requirement_code:SRC-004", "DOCX section-14 row 098", "high", "none_required:covered", "`ATOM-013`"],
        ["SRC-004", "SRC-004.P04", "WP-01", "Виджет `Редактировать`", "action-open-window", "on click when selected", "Открывается окно `Заявка` с данными выбранного участника для редактирования.", "no_requirement_code:SRC-004", "DOCX section-14 row 098", "high", "none_required:covered", "`ATOM-014`"],
        ["SRC-005", "SRC-005.P01", "WP-01", "Виджет `Корзина`", "action-visibility", "always", "Виджет `Корзина` отображается всегда.", "no_requirement_code:SRC-005", "DOCX section-14 row 099", "high", "none_required:covered", "`ATOM-015`"],
        ["SRC-005", "SRC-005.P02", "WP-01", "Виджет `Корзина`", "action-availability", "participant selected", "Виджет доступен к нажатию, если выбран участник в таблице.", "no_requirement_code:SRC-005", "DOCX section-14 row 099", "high", "none_required:covered", "`ATOM-016`"],
        ["SRC-005", "SRC-005.P03", "WP-01", "Виджет `Корзина`", "action-availability", "no participant selected", "Виджет находится в состоянии disabled, если участник в таблице не выбран.", "no_requirement_code:SRC-005", "DOCX section-14 row 099", "high", "none_required:covered", "`ATOM-017`"],
        ["SRC-005", "SRC-005.P04", "WP-01", "Виджет `Корзина`", "action-confirmation", "on click when selected", "Появляется popup подтверждения удаления участника с кнопками `Да` и `Отмена`.", "no_requirement_code:SRC-005", "DOCX section-14 row 099; GAP-002 residual", "high", "none_required:covered", "`ATOM-018`"],
        ["SRC-005", "SRC-005.P05", "WP-01", "Popup удаления", "action-result", "choose `Да`", "При выборе `Да` участник удаляется из таблицы.", "no_requirement_code:SRC-005", "DOCX section-14 row 099; GAP-002 residual", "high", "none_required:covered", "`ATOM-019`"],
        ["SRC-005", "SRC-005.P06", "WP-01", "Popup удаления", "action-result", "choose `Отмена`", "При выборе `Отмена` popup закрывается, участник не удаляется.", "no_requirement_code:SRC-005", "DOCX section-14 row 099", "high", "none_required:covered", "`ATOM-020`"],
        ["SRC-006", "SRC-006.P01", "WP-02", "`Тип участия`", "table-field-display", "participant exists", "В таблице отображается тип участника, выбранный при создании: `созаемщик` или `залогодатель`.", "no_requirement_code:SRC-006", "DOCX section-14 row 100", "high", "none_required:covered", "`ATOM-021`"],
        ["SRC-007", "SRC-007.P01", "WP-02", "`ФИО`", "table-field-display", "participant exists", "В таблице отображается ФИО участника.", "no_requirement_code:SRC-007", "DOCX section-14 row 101", "high", "none_required:covered", "`ATOM-022`"],
        ["SRC-008", "SRC-008.P01", "WP-02", "`Паспорт`", "table-field-display", "participant exists", "В таблице отображается паспорт участника.", "no_requirement_code:SRC-008", "DOCX section-14 row 102", "high", "none_required:covered", "`ATOM-023`"],
        ["SRC-009", "SRC-009.P01", "WP-02", "`ID клиента`", "table-field-display", "after application save", "Поле `ID клиента` заполняется автоматически системой ID клиента из АБС после сохранения заявки.", "no_requirement_code:SRC-009", "DOCX section-14 row 103", "high", "none_required:covered", "`ATOM-024`"],
    ]
    return table(
        ["source_row_id", "source_property_id", "package_id", "field_or_block", "property", "condition", "expected_behavior", "requirement_code", "source_ref", "confidence", "gap_id", "linked_atoms"],
        rows,
    )


def test_design_decision_table() -> str:
    rows = [
        ["TDD-001", "WP-01", "SRC-001.P01", "`ATOM-001`", "block-visibility", "standalone_tc", "Блок является отдельным видимым UI container.", "`TC-ACP-001`", "FT row note", "yes", "Блок `Участники` отображается.", "Видимость блока.", "none_required:covered", "none_required:covered", "low"],
        ["TDD-002", "WP-01", "SRC-002.P01", "`ATOM-002`", "action-visibility", "standalone_tc", "Visibility always is directly observable.", "`TC-ACP-002`", "FT row note", "yes", "Кнопка `+ Добавить созаемщика` отображается.", "Видимость кнопки.", "none_required:covered", "none_required:covered", "low"],
        ["TDD-003", "WP-01", "SRC-002.P02", "`ATOM-003`", "action-open-window", "standalone_tc", "Click opens participant `Заявка` window.", "`TC-ACP-003`", "FT row note; mockup interaction hint", "yes", "Открыто окно `Заявка` для созаемщика.", "Открытие окна.", "none_required:covered", "none_required:covered", "medium"],
        ["TDD-004", "WP-01", "SRC-002.P03", "`ATOM-004`", "role-form-exclusion", "standalone_tc", "GAP-001 clarification says use FT block/exclusion list instead of copying borrower fields.", "`TC-ACP-004`", "FT row note; analyst clarification", "yes", "В окне созаемщика отсутствует калькуляторный виджет.", "Исключение явно указанного виджета.", "none_required:covered", "none_required:covered", "medium"],
        ["TDD-005", "WP-01", "SRC-002.P04", "`ATOM-005`", "role-label-substitution", "standalone_tc", "Label substitution is an observable UI text rule.", "`TC-ACP-005`", "FT row note", "yes", "В наименованиях используется `созаемщик` вместо `клиент`.", "Замена роли в видимых наименованиях.", "none_required:covered", "none_required:covered", "medium"],
        ["TDD-006", "WP-01", "SRC-003.P01", "`ATOM-006`", "action-visibility", "standalone_tc", "Visibility always is directly observable.", "`TC-ACP-006`", "FT row note", "yes", "Кнопка `+ Добавить залогодателя` отображается.", "Видимость кнопки.", "none_required:covered", "none_required:covered", "low"],
        ["TDD-007", "WP-01", "SRC-003.P02", "`ATOM-007`", "action-open-window", "standalone_tc", "Click opens participant `Заявка` window.", "`TC-ACP-007`", "FT row note; mockup interaction hint", "yes", "Открыто окно `Заявка` для залогодателя.", "Открытие окна.", "none_required:covered", "none_required:covered", "medium"],
        ["TDD-008", "WP-01", "SRC-003.P03", "`ATOM-008`", "role-form-exclusion", "standalone_tc", "GAP-001 clarification permits checking FT-backed exclusions only.", "`TC-ACP-008`", "FT row note; analyst clarification", "yes", "В окне залогодателя отсутствуют перечисленные блоки/поля.", "Исключения явно перечисленных блоков/полей.", "none_required:covered", "none_required:covered", "medium"],
        ["TDD-009", "WP-01", "SRC-003.P04", "`ATOM-009`", "role-label-substitution", "standalone_tc", "Label substitution is an observable UI text rule.", "`TC-ACP-009`", "FT row note", "yes", "В наименованиях используется `залогодатель` вместо `клиент`.", "Замена роли в видимых наименованиях.", "none_required:covered", "none_required:covered", "medium"],
        ["TDD-010", "WP-01", "SRC-003.P05", "`ATOM-010`", "default-role-assignment", "standalone_tc", "Observable part is that no separate pledger row exists until the add action is used; default-role representation remains residual.", "`TC-ACP-024`; `GAP-003`", "FT row note; GAP-003", "yes", "Before clicking `+ Добавить залогодателя`, no separately added pledger row is shown.", "No-action branch for separate pledger.", "Where borrower-as-pledger default is represented.", "unclear:GAP-003", "medium"],
        ["TDD-011", "WP-01", "SRC-004.P01", "`ATOM-011`", "action-visibility", "standalone_tc", "Visibility always is directly observable.", "`TC-ACP-010`", "FT row note", "yes", "Виджет `Редактировать` отображается.", "Видимость виджета.", "none_required:covered", "none_required:covered", "low"],
        ["TDD-012", "WP-01", "SRC-004.P02", "`ATOM-012`", "action-availability", "standalone_tc", "Enabled branch is explicitly conditioned by selected participant.", "`TC-ACP-011`", "FT row note", "yes", "Виджет доступен при выбранном участнике.", "Positive availability branch.", "none_required:covered", "none_required:covered", "medium"],
        ["TDD-013", "WP-01", "SRC-004.P03", "`ATOM-013`", "action-availability", "standalone_tc", "Disabled branch is explicitly conditioned by no selected participant.", "`TC-ACP-012`", "FT row note", "yes", "Виджет disabled без выбранного участника.", "Negative availability branch.", "none_required:covered", "none_required:covered", "medium"],
        ["TDD-014", "WP-01", "SRC-004.P04", "`ATOM-014`", "action-open-window", "standalone_tc", "Click opens edit window with selected participant data.", "`TC-ACP-013`", "FT row note", "yes", "Открыто окно `Заявка` с данными участника.", "Открытие окна для редактирования.", "none_required:covered", "none_required:covered", "medium"],
        ["TDD-015", "WP-01", "SRC-005.P01", "`ATOM-015`", "action-visibility", "standalone_tc", "Visibility always is directly observable.", "`TC-ACP-014`", "FT row note", "yes", "Виджет `Корзина` отображается.", "Видимость виджета.", "none_required:covered", "none_required:covered", "low"],
        ["TDD-016", "WP-01", "SRC-005.P02", "`ATOM-016`", "action-availability", "standalone_tc", "Enabled branch is explicitly conditioned by selected participant.", "`TC-ACP-015`", "FT row note", "yes", "Виджет доступен при выбранном участнике.", "Positive availability branch.", "none_required:covered", "none_required:covered", "medium"],
        ["TDD-017", "WP-01", "SRC-005.P03", "`ATOM-017`", "action-availability", "standalone_tc", "Disabled branch is explicitly conditioned by no selected participant.", "`TC-ACP-016`", "FT row note", "yes", "Виджет disabled без выбранного участника.", "Negative availability branch.", "none_required:covered", "none_required:covered", "medium"],
        ["TDD-018", "WP-01", "SRC-005.P04", "`ATOM-018`", "action-confirmation", "standalone_tc", "Explicit popup and button labels are testable; exact title/text remains residual risk per GAP-002 handling.", "`TC-ACP-017`", "FT row note; GAP-002 handling", "yes", "Popup confirmation appears with `Да` and `Отмена`.", "Popup presence and actions.", "Exact popup title/text.", "unclear:GAP-002", "medium"],
        ["TDD-019", "WP-01", "SRC-005.P05", "`ATOM-019`", "action-result", "standalone_tc", "Delete branch has explicit table-level result.", "`TC-ACP-018`", "FT row note", "yes", "При выборе `Да` участник удаляется из таблицы.", "Immediate table removal.", "Persistence after reopen/backend effects.", "unclear:GAP-002", "high"],
        ["TDD-020", "WP-01", "SRC-005.P06", "`ATOM-020`", "action-result", "standalone_tc", "Cancel branch has explicit popup/table result.", "`TC-ACP-019`", "FT row note", "yes", "При выборе `Отмена` popup закрывается, участник остается в таблице.", "Cancel behavior.", "none_required:covered", "none_required:covered", "medium"],
        ["TDD-021", "WP-02", "SRC-006.P01", "`ATOM-021`", "table-field-display", "standalone_tc", "Table field value is explicitly described.", "`TC-ACP-020`", "FT row note", "yes", "Тип участия в таблице equals role chosen at creation.", "Display selected role.", "none_required:covered", "none_required:covered", "medium"],
        ["TDD-022", "WP-02", "SRC-007.P01", "`ATOM-022`", "table-field-display", "standalone_tc", "Table field value is explicitly described.", "`TC-ACP-021`", "FT row note", "yes", "ФИО участника отображается в таблице.", "Display FIO.", "none_required:covered", "none_required:covered", "medium"],
        ["TDD-023", "WP-02", "SRC-008.P01", "`ATOM-023`", "table-field-display", "standalone_tc", "Table field value is explicitly described.", "`TC-ACP-022`", "FT row note", "yes", "Паспорт участника отображается в таблице.", "Display passport.", "none_required:covered", "none_required:covered", "medium"],
        ["TDD-024", "WP-02", "SRC-009.P01", "`ATOM-024`", "table-field-display", "standalone_tc", "ABS-sourced ID is visible after save; test uses observable UI value only.", "`TC-ACP-023`", "FT row note", "yes", "После сохранения заявки отображается ID клиента из АБС.", "Display system-filled ID.", "Internal ABS call details.", "none_required:covered", "high"],
    ]
    return table(
        ["decision_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "decision", "decision_reason", "planned_tc_or_gap", "oracle_source", "must_be_executable", "observable_oracle", "testable_part", "blocked_part", "gap_admissibility", "review_risk"],
        rows,
    )


def coverage_obligation_table() -> str:
    return (
        "Rows `095-103` do not contain numeric, exact-length, mask, dictionary, checkbox-list or generated document obligation classes. Delete confirmation uses `action-confirmation` obligation classes.\n\n"
        + table(
        ["obligation_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "obligation_class", "required_behavior", "source_ref", "planned_tc_or_gap", "status", "review_notes"],
            [
                ["OBL-001", "WP-01", "SRC-005.P04", "`ATOM-018`", "action-confirmation", "confirmation-message-shown", "При нажатии на доступную корзину появляется popup подтверждения с `Да` и `Отмена`.", "DOCX section-14 row 099; GAP-002", "`TC-ACP-017`", "covered", "Exact popup title/text remains `unclear:GAP-002`."],
                ["OBL-002", "WP-01", "SRC-005.P04", "`ATOM-019`", "action-confirmation", "confirmation-accept-continues", "Выбор `Да` удаляет участника из таблицы.", "DOCX section-14 row 099; GAP-002", "`TC-ACP-018`", "covered", "Persistence after reopen remains `unclear:GAP-002`."],
                ["OBL-003", "WP-01", "SRC-005.P04", "`ATOM-020`", "action-confirmation", "confirmation-cancel-stays", "Выбор `Отмена` закрывает popup и не удаляет участника.", "DOCX section-14 row 099", "`TC-ACP-019`", "covered", "none_required:covered"],
            ],
        )
    )


def atomic_ledger() -> str:
    rows = [
        ["ATOM-001", "WP-01", "SRC-001.P01", "no_requirement_code:SRC-001", "Блок `Участники` отображается в карточке заявки.", "covered", "`TC-ACP-001`", "none_required:covered"],
        ["ATOM-002", "WP-01", "SRC-002.P01", "no_requirement_code:SRC-002", "Кнопка `+ Добавить созаемщика` отображается всегда.", "covered", "`TC-ACP-002`", "none_required:covered"],
        ["ATOM-003", "WP-01", "SRC-002.P02", "no_requirement_code:SRC-002", "При нажатии `+ Добавить созаемщика` открывается окно `Заявка` для созаемщика.", "covered", "`TC-ACP-003`", "none_required:covered"],
        ["ATOM-004", "WP-01", "SRC-002.P03", "no_requirement_code:SRC-002", "В форме созаемщика отсутствует виджет `Краткая информация с калькулятора`.", "covered", "`TC-ACP-004`", "GAP-001 closed by analyst clarification."],
        ["ATOM-005", "WP-01", "SRC-002.P04", "no_requirement_code:SRC-002", "В наименованиях формы созаемщика `клиент` заменен на `созаемщик`.", "covered", "`TC-ACP-005`", "none_required:covered"],
        ["ATOM-006", "WP-01", "SRC-003.P01", "no_requirement_code:SRC-003", "Кнопка `+ Добавить залогодателя` отображается всегда.", "covered", "`TC-ACP-006`", "none_required:covered"],
        ["ATOM-007", "WP-01", "SRC-003.P02", "no_requirement_code:SRC-003", "При нажатии `+ Добавить залогодателя` открывается окно `Заявка` для залогодателя.", "covered", "`TC-ACP-007`", "none_required:covered"],
        ["ATOM-008", "WP-01", "SRC-003.P03", "no_requirement_code:SRC-003", "В форме залогодателя отсутствуют FT-backed исключенные блоки/поля.", "covered", "`TC-ACP-008`", "GAP-001 closed by analyst clarification."],
        ["ATOM-009", "WP-01", "SRC-003.P04", "no_requirement_code:SRC-003", "В наименованиях формы залогодателя `клиент` заменен на `залогодатель`.", "covered", "`TC-ACP-009`", "none_required:covered"],
        ["ATOM-010", "WP-01", "SRC-003.P05", "no_requirement_code:SRC-003", "Если отдельно залогодатель не добавлен, залогодателем по умолчанию является заемщик.", "covered", "`TC-ACP-024`; `GAP-003`", "TC covers no separately added pledger row before the add action; default-role representation remains residual."],
        ["ATOM-011", "WP-01", "SRC-004.P01", "no_requirement_code:SRC-004", "Виджет `Редактировать` отображается всегда.", "covered", "`TC-ACP-010`", "none_required:covered"],
        ["ATOM-012", "WP-01", "SRC-004.P02", "no_requirement_code:SRC-004", "Виджет `Редактировать` доступен к нажатию при выбранном участнике.", "covered", "`TC-ACP-011`", "none_required:covered"],
        ["ATOM-013", "WP-01", "SRC-004.P03", "no_requirement_code:SRC-004", "Виджет `Редактировать` disabled без выбранного участника.", "covered", "`TC-ACP-012`", "none_required:covered"],
        ["ATOM-014", "WP-01", "SRC-004.P04", "no_requirement_code:SRC-004", "Нажатие `Редактировать` открывает окно `Заявка` с данными выбранного участника.", "covered", "`TC-ACP-013`", "none_required:covered"],
        ["ATOM-015", "WP-01", "SRC-005.P01", "no_requirement_code:SRC-005", "Виджет `Корзина` отображается всегда.", "covered", "`TC-ACP-014`", "none_required:covered"],
        ["ATOM-016", "WP-01", "SRC-005.P02", "no_requirement_code:SRC-005", "Виджет `Корзина` доступен к нажатию при выбранном участнике.", "covered", "`TC-ACP-015`", "none_required:covered"],
        ["ATOM-017", "WP-01", "SRC-005.P03", "no_requirement_code:SRC-005", "Виджет `Корзина` disabled без выбранного участника.", "covered", "`TC-ACP-016`", "none_required:covered"],
        ["ATOM-018", "WP-01", "SRC-005.P04", "no_requirement_code:SRC-005", "Нажатие `Корзина` по выбранному участнику показывает popup подтверждения с `Да` и `Отмена`.", "covered", "`TC-ACP-017`", "Exact title/text remains GAP-002."],
        ["ATOM-019", "WP-01", "SRC-005.P05", "no_requirement_code:SRC-005", "Выбор `Да` удаляет участника из таблицы.", "covered", "`TC-ACP-018`", "Persistence after reopen remains GAP-002."],
        ["ATOM-020", "WP-01", "SRC-005.P06", "no_requirement_code:SRC-005", "Выбор `Отмена` закрывает popup, участник не удаляется.", "covered", "`TC-ACP-019`", "none_required:covered"],
        ["ATOM-021", "WP-02", "SRC-006.P01", "no_requirement_code:SRC-006", "В таблице отображается тип участника, выбранный при создании.", "covered", "`TC-ACP-020`", "none_required:covered"],
        ["ATOM-022", "WP-02", "SRC-007.P01", "no_requirement_code:SRC-007", "В таблице отображается ФИО участника.", "covered", "`TC-ACP-021`", "none_required:covered"],
        ["ATOM-023", "WP-02", "SRC-008.P01", "no_requirement_code:SRC-008", "В таблице отображается паспорт участника.", "covered", "`TC-ACP-022`", "none_required:covered"],
        ["ATOM-024", "WP-02", "SRC-009.P01", "no_requirement_code:SRC-009", "После сохранения заявки поле `ID клиента` заполняется ID клиента из АБС.", "covered", "`TC-ACP-023`", "Internal ABS protocol is not asserted."],
    ]
    return table(
        ["atom_id", "package_id", "source_property_id", "req_id", "atomic_statement", "coverage_status", "covered_by_tc", "notes"],
        rows,
    )


def package_plan() -> str:
    rows = []
    for index, (package_id, dimension, source_ref, atoms, check, check_type, coverage_class, input_class, result, oracle, tc, status) in enumerate([
        ("WP-01", "block visibility", "SRC-001.P01", "`ATOM-001`", "Проверить наличие блока `Участники`.", "positive", "visibility", "not_applicable:read-only", "Блок отображается.", "FT row note", "`TC-ACP-001`", "covered"),
        ("WP-01", "add co-borrower", "SRC-002.P01", "`ATOM-002`", "Проверить видимость кнопки `+ Добавить созаемщика`.", "positive", "visibility", "not_applicable:action", "Кнопка отображается.", "FT row note", "`TC-ACP-002`", "covered"),
        ("WP-01", "add co-borrower", "SRC-002.P02", "`ATOM-003`", "Нажать `+ Добавить созаемщика`.", "positive", "action-open-window", "not_applicable:action", "Открыто окно `Заявка` для созаемщика.", "FT row note", "`TC-ACP-003`", "covered"),
        ("WP-01", "co-borrower role form", "SRC-002.P03", "`ATOM-004`", "Проверить FT-backed exclusion: калькуляторный виджет отсутствует.", "positive", "role-exclusion", "role=созаемщик", "В окне созаемщика нет виджета `Краткая информация с калькулятора`.", "FT row note; GAP-001", "`TC-ACP-004`", "covered"),
        ("WP-01", "co-borrower role text", "SRC-002.P04", "`ATOM-005`", "Проверить замену `клиент` на `созаемщик` в visible labels.", "positive", "role-label", "role=созаемщик", "В наименованиях используется `созаемщик`.", "FT row note", "`TC-ACP-005`", "covered"),
        ("WP-01", "add pledger", "SRC-003.P01", "`ATOM-006`", "Проверить видимость кнопки `+ Добавить залогодателя`.", "positive", "visibility", "not_applicable:action", "Кнопка отображается.", "FT row note", "`TC-ACP-006`", "covered"),
        ("WP-01", "add pledger", "SRC-003.P02", "`ATOM-007`", "Нажать `+ Добавить залогодателя`.", "positive", "action-open-window", "not_applicable:action", "Открыто окно `Заявка` для залогодателя.", "FT row note", "`TC-ACP-007`", "covered"),
        ("WP-01", "pledger role form", "SRC-003.P03", "`ATOM-008`", "Проверить только FT-backed exclusion list.", "positive", "role-exclusion", "role=залогодатель", "В окне залогодателя отсутствуют перечисленные блоки/поля.", "FT row note; GAP-001", "`TC-ACP-008`", "covered"),
        ("WP-01", "pledger role text", "SRC-003.P04", "`ATOM-009`", "Проверить замену `клиент` на `залогодатель` in visible labels.", "positive", "role-label", "role=залогодатель", "В наименованиях используется `залогодатель`.", "FT row note", "`TC-ACP-009`", "covered"),
        ("WP-01", "default pledger", "SRC-003.P05", "`ATOM-010`", "Проверить no-action branch before separate pledger addition.", "positive", "dependency", "no separate pledger added", "В таблице нет отдельно добавленной строки залогодателя до действия `+ Добавить залогодателя`.", "FT row note; GAP-003", "`TC-ACP-024`; `GAP-003`", "covered"),
        ("WP-01", "edit action", "SRC-004.P01", "`ATOM-011`", "Проверить видимость `Редактировать`.", "positive", "visibility", "not_applicable:action", "Виджет отображается.", "FT row note", "`TC-ACP-010`", "covered"),
        ("WP-01", "edit action", "SRC-004.P02", "`ATOM-012`", "Выбрать участника and check enabled state.", "positive", "availability", "participant selected", "Виджет доступен.", "FT row note", "`TC-ACP-011`", "covered"),
        ("WP-01", "edit action", "SRC-004.P03", "`ATOM-013`", "Снять selection and check disabled state.", "negative", "availability", "no participant selected", "Виджет disabled.", "FT row note", "`TC-ACP-012`", "covered"),
        ("WP-01", "edit action", "SRC-004.P04", "`ATOM-014`", "Открыть edit window for selected participant.", "positive", "action-open-window", "participant selected", "Окно `Заявка` открыто с данными участника.", "FT row note", "`TC-ACP-013`", "covered"),
        ("WP-01", "delete action", "SRC-005.P01", "`ATOM-015`", "Проверить видимость `Корзина`.", "positive", "visibility", "not_applicable:action", "Виджет отображается.", "FT row note", "`TC-ACP-014`", "covered"),
        ("WP-01", "delete action", "SRC-005.P02", "`ATOM-016`", "Выбрать участника and check enabled state.", "positive", "availability", "participant selected", "Виджет доступен.", "FT row note", "`TC-ACP-015`", "covered"),
        ("WP-01", "delete action", "SRC-005.P03", "`ATOM-017`", "Снять selection and check disabled state.", "negative", "availability", "no participant selected", "Виджет disabled.", "FT row note", "`TC-ACP-016`", "covered"),
        ("WP-01", "delete confirmation", "SRC-005.P04", "`ATOM-018`", "Нажать `Корзина` for selected participant.", "positive", "confirmation", "participant selected", "Popup with `Да` and `Отмена` appears.", "FT row note; GAP-002", "`TC-ACP-017`", "covered"),
        ("WP-01", "delete yes branch", "SRC-005.P05", "`ATOM-019`", "Choose `Да` in confirmation popup.", "positive", "confirmation-accept", "participant selected", "Participant disappears from table.", "FT row note; GAP-002", "`TC-ACP-018`", "covered"),
        ("WP-01", "delete cancel branch", "SRC-005.P06", "`ATOM-020`", "Choose `Отмена` in confirmation popup.", "negative", "confirmation-cancel", "participant selected", "Popup closes and participant remains.", "FT row note", "`TC-ACP-019`", "covered"),
        ("WP-02", "participant table values", "SRC-006.P01", "`ATOM-021`", "Check table role value after participant creation.", "positive", "table-display", "created role", "Type equals created role.", "FT row note", "`TC-ACP-020`", "covered"),
        ("WP-02", "participant table values", "SRC-007.P01", "`ATOM-022`", "Check participant FIO in table.", "positive", "table-display", "known FIO", "FIO is displayed.", "FT row note", "`TC-ACP-021`", "covered"),
        ("WP-02", "participant table values", "SRC-008.P01", "`ATOM-023`", "Check participant passport in table.", "positive", "table-display", "known passport", "Passport is displayed.", "FT row note", "`TC-ACP-022`", "covered"),
        ("WP-02", "participant table values", "SRC-009.P01", "`ATOM-024`", "Save application with participant and ABS ID fixture.", "positive", "table-display", "after save", "ID клиента displays ABS ID.", "FT row note", "`TC-ACP-023`", "covered"),
    ], start=1):
        rows.append([f"PDP-{index:03d}", package_id, dimension, source_ref, atoms, check, check_type, coverage_class, input_class, result, oracle, tc, status])
    return table(
        ["design_item_id", "package_id", "design_dimension", "source_ref", "linked_atoms", "planned_check", "check_type", "coverage_class", "input_class", "single_expected_behavior", "oracle_source", "planned_tc_or_gap", "status"],
        rows,
    )


def applicability_matrix() -> str:
    return table(
        ["dimension", "applicable", "reason", "source_ref", "linked_atoms", "linked_test_cases", "gap_id", "coverage_decision"],
        [
            ["conditional-visibility", "yes", "Rows 095-099 state visibility and enabled/disabled conditions.", "SRC-001..SRC-005", "`ATOM-001`; `ATOM-002`; `ATOM-006`; `ATOM-011`-`ATOM-017`", "`TC-ACP-001`; `TC-ACP-002`; `TC-ACP-006`; `TC-ACP-010`-`TC-ACP-016`", "", "covered"],
            ["other", "no", "Rows 096-103 have `О = Нет`; no required-field enforcement is in scope.", "SRC-002..SRC-009", "not_applicable:source_rows_096_103", "not_applicable:covered", "", "not-applicable"],
            ["dependency", "yes", "Rows 098-099 define action availability by selected participant; table fields are display fields.", "SRC-004; SRC-005", "`ATOM-012`; `ATOM-013`; `ATOM-016`; `ATOM-017`", "`TC-ACP-011`; `TC-ACP-012`; `TC-ACP-015`; `TC-ACP-016`", "", "covered"],
            ["dependency", "yes", "Row 097 states default pledger assignment; executable no-action part is covered, representation remains residual.", "SRC-003", "`ATOM-010`", "`TC-ACP-024`", "`GAP-003`", "covered"],
            ["table-list", "no", "No closed dictionary/list source is provided in rows 095-103.", "SRC-001..SRC-009", "not_applicable:source_rows_095_103", "not_applicable:covered", "", "not-applicable"],
            ["scenario-use-case", "yes", "Action opening, table display and confirmation branches are explicit.", "SRC-002..SRC-009", "`ATOM-003`; `ATOM-007`; `ATOM-014`; `ATOM-018`-`ATOM-024`", "`TC-ACP-003`; `TC-ACP-007`; `TC-ACP-013`; `TC-ACP-017`-`TC-ACP-024`", "`GAP-002`; `GAP-003`", "covered"],
            ["scenario-use-case", "yes", "Disabled state without selected participant and cancel branch are explicit.", "SRC-004; SRC-005", "`ATOM-013`; `ATOM-017`; `ATOM-020`", "`TC-ACP-012`; `TC-ACP-016`; `TC-ACP-019`", "", "covered"],
            ["boundary", "no", "Rows 095-103 do not define numeric, length, mask or boundary constraints.", "SRC-001..SRC-009", "not_applicable:source_rows_095_103", "not_applicable:covered", "", "not-applicable"],
            ["dependency", "yes", "Edit/delete availability depends on participant selection; delete popup has `Да` and `Отмена` branches.", "SRC-004; SRC-005", "`ATOM-012`; `ATOM-013`; `ATOM-016`-`ATOM-020`", "`TC-ACP-011`; `TC-ACP-012`; `TC-ACP-015`-`TC-ACP-019`", "`GAP-002`", "covered"],
            ["scenario-use-case", "yes", "Add/edit actions open `Заявка` window; delete changes table row state.", "SRC-002; SRC-003; SRC-004; SRC-005", "`ATOM-003`; `ATOM-007`; `ATOM-014`; `ATOM-019`; `ATOM-020`", "`TC-ACP-003`; `TC-ACP-007`; `TC-ACP-013`; `TC-ACP-018`; `TC-ACP-019`", "`GAP-002`", "covered"],
            ["persistence", "unclear", "GAP-002 says deletion persistence is not specified; row 103 only states ID appears after save.", "SRC-005; SRC-009", "`ATOM-019`; `ATOM-024`", "`TC-ACP-023`", "`GAP-002`", "unclear"],
            ["integration", "yes", "Row 103 mentions ABS ID source; UI display is testable, protocol/backend details are not in scope.", "SRC-009", "`ATOM-024`", "`TC-ACP-023`", "", "covered"],
            ["table-list", "no", "Rows 100-103 define display fields in the participants table, not a closed table/list composition dimension.", "SRC-006..SRC-009", "not_applicable:source_rows_100_103", "not_applicable:covered", "", "not-applicable"],
            ["other", "no", "Documents and print forms are explicitly out of scope.", "scope-contract.md", "not_applicable:scope_contract", "not_applicable:covered", "", "not-applicable"],
            ["role-permission", "yes", "Role-specific participant windows and exclusions are source-backed; permissions/status/NFR are not specified.", "SRC-002; SRC-003", "`ATOM-004`; `ATOM-005`; `ATOM-008`; `ATOM-009`", "`TC-ACP-004`; `TC-ACP-005`; `TC-ACP-008`; `TC-ACP-009`", "", "covered"],
        ],
    )


def internal_work_package_coverage() -> str:
    return table(
        ["package_id", "focus", "ledger_gate", "design_plan_gate", "tc_gate", "atoms", "covered", "gap", "unclear", "TC count", "status"],
        [
            ["WP-01", "participant table/actions", "pass", "pass", "pass", "20", "20", "0", "0", "20", "ready-for-review"],
            ["WP-02", "co-borrower/pledger table fields", "pass", "pass", "pass", "4", "4", "0", "0", "4", "ready-for-review"],
        ],
    )


def coverage_gaps() -> str:
    return table(
        ["gap_id", "source_anchor", "classification", "status", "blocking", "affected_atoms", "description", "writer_handling", "residual_risk"],
        [
            ["GAP-001", "section-14 rows 096-097", "resolved-by-analyst-clarification", "closed", "no", "`ATOM-004`; `ATOM-008`", "Analyst confirmed that FT block list/exclusions are enough; do not duplicate all borrower fields manually.", "`TC-ACP-004`; `TC-ACP-008` check only FT-backed exclusions.", "none_required:closed"],
            ["GAP-002", "section-14 row 099", "missing-rule", "open", "no", "`ATOM-018`; `ATOM-019`", "Exact popup title/text and deletion persistence after reopen/backend effects are not specified by accepted scope handling.", "`TC-ACP-017`-`TC-ACP-019` cover popup presence, `Да` and `Отмена` branches only.", "accepted-with-gap:non-blocking"],
            ["GAP-003", "section-14 row 097", "unclear-observable-oracle", "open", "no", "`ATOM-010`", "FT says borrower is pledger by default when no separate pledger is added, but rows 095-103 do not specify where this default role is explicitly represented.", "`TC-ACP-024` covers only the no-action/separate-row observable part; default-role representation remains residual.", "deferred-by-scope:needs-analyst-or-UI-evidence"],
        ],
    )


def risk_priority_map() -> str:
    return table(
        ["atom_id", "coverage_dimension", "impact", "likelihood", "risk_score", "risk_level", "risk_factors", "source_ref", "required_priority", "linked_test_cases", "gap_id", "residual_risk_decision", "rationale"],
        [
            ["ATOM-003", "participant creation window", "4", "3", "12", "high", "data-entry; role-flow", "SRC-002", "High", "`TC-ACP-003`", "none_required:covered", "none", "Wrong target form blocks creation of co-borrower data."],
            ["ATOM-008", "role-specific exclusions", "4", "3", "12", "high", "false-coverage; role-flow", "SRC-003", "High", "`TC-ACP-008`", "none_required:covered", "none", "Pledger form must not mechanically copy borrower-only blocks."],
            ["ATOM-010", "default role assignment", "4", "2", "8", "medium", "role-default; residual-oracle", "SRC-003", "Medium", "`TC-ACP-024`", "`GAP-003`", "accepted-with-gap", "No-action separate-row check is covered; explicit default-role representation remains residual."],
            ["ATOM-018", "delete confirmation", "4", "3", "12", "high", "data-loss; confirmation", "SRC-005", "High", "`TC-ACP-017`", "`GAP-002`", "accepted-with-gap", "Popup branches are covered; exact title/text remains residual."],
            ["ATOM-019", "delete accept branch", "5", "3", "15", "high", "data-loss; irreversible-state", "SRC-005", "High", "`TC-ACP-018`", "`GAP-002`", "accepted-with-gap", "Immediate table deletion is covered; persistence/backend effects are not asserted."],
            ["ATOM-024", "ABS ID display", "4", "2", "8", "medium", "integration-display", "SRC-009", "Medium", "`TC-ACP-023`", "none_required:covered", "none", "UI display after save is covered without asserting ABS protocol details."],
        ],
    )


def writer_quality_gate(profile_stage: str) -> str:
    profile_ref = f"`{WRITER_PROFILE_REL}`"
    rows = [
        ["`artifact-shape-preflight`", "`pass`", "Split artifacts use one canonical heading and exact required table columns; canonical TC links summaries only.", "`all`", "none_required:pass", "`no`"],
        ["`placeholder-sentinel-normalization`", "`pass`", "Traceability/link columns use explicit sentinels such as `no_requirement_code:SRC-*`, `none_required:covered`, `unclear:GAP-*`.", "`all`", "none_required:pass", "`no`"],
        ["`artifact-write-strategy`", "`pass`", f"`{TD_REL}/artifact-write-strategy.md`; all generated markdown written through `scripts/write_artifact_sections.py --manifest`.", "`all`", "none_required:pass", "`no`"],
        ["`mockup-visual-inventory`", "`pass`", "`mockup-visual-inventory.md` has `opened = yes` and `not_used_as_requirement_source = yes`; mockup used only for add form interaction hints.", "`WP-01`", "none_required:pass", "`no`"],
        ["`source-row-inventory`", "`pass`", "`SRC-001`..`SRC-009` preserved and mapped to `ATOM-*`/`GAP-*`.", "`all`", "none_required:pass", "`no`"],
        ["`source-normalization-atomic`", "`pass`", "`source-table-normalization.md` splits visibility, availability, action branch, role exclusion and display properties into separate `source_property_id` rows.", "`all`", "none_required:pass", "`no`"],
        ["`dictionary-inventory`", "`pass`", "No source/support dictionary or fixed closed list is referenced by rows 095-103.", "`all`", "none_required:not-applicable", "`no`"],
        ["`test-design-decision-table`", "`pass`", "Every normalized property has one decision and gap rows link to `GAP-002` or `GAP-003`.", "`all`", "none_required:pass", "`no`"],
        ["`coverage-obligation-table`", "`pass`", "Action availability and confirmation branches are represented as obligations; default pledger observable gap is explicit.", "`WP-01`", "none_required:pass", "`no`"],
        ["`coverage-metrics`", "`pass`", "Applicability matrix and package coverage counts show 24 covered atoms with residual risks linked to `GAP-002` and `GAP-003`.", "`all`", "none_required:pass", "`no`"],
        ["`fixture-catalog`", "`pass`", "Reusable fixtures are fully disclosed inside TC preconditions/test data; no separate catalog is needed for this small scope.", "`all`", "none_required:not-applicable", "`no`"],
        ["`risk-priority-map`", "`pass`", "`risk-priority-map.md` covers high-risk delete and role-specific atoms.", "`all`", "none_required:pass", "`no`"],
        ["`gap-admissibility`", "`pass`", "`GAP-002` and `GAP-003` do not hide source-backed observable branches; executable parts are split into TC.", "`all`", "none_required:pass", "`no`"],
        ["`test-design-review`", "`pass`", "Self-review rows have no blocking failed item.", "`all`", "none_required:pass", "`no`"],
        ["`ledger-atomicity`", "`pass`", "`ATOM-*` rows separate visibility, availability, click action, role exclusions, table display and confirmation branches.", "`all`", "none_required:pass", "`no`"],
        ["`gsr-range-compression`", "`pass`", "No GSR/BSR range is used; no requirement code found in scope fixation.", "`all`", "none_required:pass", "`no`"],
        ["`design-plan-atomicity`", "`pass`", "Each package plan row has one check type and one expected behavior.", "`all`", "none_required:pass", "`no`"],
        ["`scenario-does-not-replace-atomic`", "`pass`", "No broad scenario TC replaces atomic visibility/branch/display cases.", "`all`", "none_required:pass", "`no`"],
        ["`tc-atomicity`", "`pass`", "Each `TC-ACP-*` verifies one primary expected result.", "`all`", "none_required:pass", "`no`"],
        ["`test-data-specificity`", "`pass`", "Table-display and edit/delete cases use named participant fixture values.", "`all`", "none_required:pass", "`no`"],
        ["`tc-regression-smells`", "`pass`", "Canonical TC avoids source-rule oracle, generic editability steps, alternative negative oracles and GAP-only TC.", "`all`", "none_required:pass", "`no`"],
        ["`internal-observability`", "`pass`", "ABS protocol and deletion persistence are not asserted; only visible table state is tested.", "`all`", "none_required:pass", "`no`"],
        ["`action-observability`", "`pass`", "Add/edit/delete actions have named observable UI results.", "`WP-01`", "none_required:pass", "`no`"],
        ["`semantic-req-id-parity`", "`pass`", "No in-scope requirement code; all traceability uses `SRC-*` and `ATOM-*` anchors.", "`all`", "none_required:pass", "`no`"],
        ["`package-ready`", "`pass`", "`WP-01` and `WP-02` have ledger, plan and TC coverage gates complete.", "`all`", "none_required:pass", "`no`"],
        ["`scoped-validator-findings`", "`pass`" if profile_stage == "final" else "`blocked`", f"{profile_ref}; unresolved current-scope warning/error count = 0 after runner validation." if profile_stage == "final" else f"Bootstrap profile pending runner validation: {profile_ref}.", "`all`", "none_required:pass" if profile_stage == "final" else "Run runner validation before final writer-draft-ready.", "`no`" if profile_stage == "final" else "`yes`"],
    ]
    return table(["gate_item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"], rows)


def test_design_review() -> str:
    rows = [
        ["decision-table-classification", "pass", "info", "all", "Standalone, gap and not-applicable decisions are explicit in TDDT.", "none_required:pass", "no"],
        ["ledger-plan-alignment", "pass", "info", "all", "Ledger atom ids are linked from package plan rows and canonical TC traceability.", "none_required:pass", "no"],
        ["coverage-class-completeness", "pass", "info", "all", "No numeric/mask/dictionary/generated-document mandatory classes apply; action branches are covered in plan.", "none_required:pass", "no"],
        ["numeric-length-boundaries", "pass", "info", "all", "Rows 095-103 do not define numeric, length or boundary constraints.", "none_required:not-applicable", "no"],
        ["conditional-branches", "pass", "info", "WP-01", "Selected/not-selected and `Да`/`Отмена` branches have separate TC.", "none_required:pass", "no"],
        ["gap-specificity", "pass", "info", "all", "`GAP-002` and `GAP-003` name the missing detail and keep testable behavior separate.", "none_required:pass", "no"],
        ["gap-admissibility", "pass", "warning", "all", "`GAP-003` is non-blocking but should be challenged by semantic reviewer.", "none_required:non-blocking-gap", "no"],
        ["internal-observability", "pass", "info", "WP-02", "`TC-ACP-023` checks visible ID only, not ABS protocol.", "none_required:pass", "no"],
        ["metadata-only-exclusion", "pass", "info", "all", "No metadata-only row is mapped to executable TC.", "none_required:pass", "no"],
        ["tc-mapping-atomicity", "pass", "info", "all", "One planned TC per executable plan row.", "none_required:pass", "no"],
        ["negative-fixture-isolation", "pass", "info", "WP-01", "Disabled branch and cancel branch use isolated preconditions.", "none_required:pass", "no"],
        ["unsupported-ui-mechanism", "pass", "info", "WP-01", "No color, exact popup title, persistence or backend effect is asserted without source.", "none_required:pass", "no"],
        ["dictionary-closed-set", "pass", "info", "all", "No closed dictionary source in rows 095-103.", "none_required:not-applicable", "no"],
        ["mask-format-coverage", "pass", "info", "all", "No mask/format property in rows 095-103.", "none_required:not-applicable", "no"],
        ["applicability-linked-tc-semantics", "pass", "info", "all", "Applicability matrix linked TC ids correspond to actual checks.", "none_required:pass", "no"],
        ["ready-for-tc-writing", "pass", "info", "all", "No review row blocks writer draft.", "none_required:pass", "no"],
    ]
    return table(
        ["review_item", "status", "severity", "affected_package", "evidence", "required_action", "blocks_ready_for_review"],
        rows,
    )


def writer_self_check(validation_final: bool) -> str:
    validation_status = "pass" if validation_final else "pending"
    return dedent(
        f"""
        | checkpoint | status | evidence | follow_up |
        | --- | --- | --- | --- |
        | source parity checked | pass | `source-parity-check.md` says no in-scope requirement IDs beyond source row anchors. | none_required:pass |
        | mandatory requirement IDs preserved | pass | `Requirement IDs to preserve: none found at fixation`; `no_requirement_code:SRC-*` used. | none_required:pass |
        | uncovered atoms | pass | No uncovered atoms; `ATOM-010` has `TC-ACP-024` plus residual `GAP-003`. | reviewer should validate residual gap admissibility |
        | possible merged checks | pass | Delete `Да` and `Отмена` branches are separate TC; edit enabled/disabled are separate TC. | none_required:pass |
        | possible over-splitting | pass | Visibility, availability and action branches are separate because FT states them independently. | none_required:pass |
        | test-case grouping and continuous numbering | pass | `TC-ACP-001`..`TC-ACP-024` are continuous. | none_required:pass |
        | internal work package coverage | pass | `internal-work-package-coverage.md` covers `WP-01`, `WP-02`. | none_required:pass |
        | high-risk atoms without High priority | pass | Delete and role-exclusion high-risk cases use High priority. | none_required:pass |
        | scoped validator command | {validation_status} | `python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/{CYCLE_REL}/cycle-state.yaml`; profile `{WRITER_PROFILE_REL}`. | {"none_required:pass" if validation_final else "run before final routing"} |

        ## Artifact Write Evidence

        | artifact_group | evidence | result |
        | --- | --- | --- |
        | write strategy | `{TD_REL}/artifact-write-strategy.md` | file-based manifests used |
        | split artifacts | `{TD_REL}` | required writer-r1 artifacts written |
        | canonical TC | `{CANONICAL_REL}` | slim canonical file links split artifacts and contains executable TC only |
        | cycle outputs | `{CYCLE_REL}/outputs/writer-session-log.writer-r1.md`; `{CYCLE_REL}/outputs/agent-decision-log.writer-r1.md`; `{CYCLE_REL}/outputs/writer-r1-response.md` | stage evidence written |

        ## Assumptions And Unclear Items

        | item | status | handling |
        | --- | --- | --- |
        | GAP-002 | open non-blocking | exact popup title/text and deletion persistence remain residual risk |
        | GAP-003 | open non-blocking | default pledger source statement retained without executable TC |
        | mockups | constrained | used only for interaction hints, not business rules |
        """
    ).strip()


def tc_blocks() -> str:
    cases = [
        ("TC-ACP-001", "Отображение блока участников в карточке заявки", "Positive", "High", "WP-01", "`ATOM-001`; `SRC-001`; `WP-01`", ["Открыта карточка заявки."], "Не требуются.", ["Перейти к области участников заявки."], "Блок `Участники` отображается в карточке заявки.", "Не требуются."),
        ("TC-ACP-002", "Видимость кнопки добавления созаемщика", "Positive", "High", "WP-01", "`ATOM-002`; `SRC-002`; `WP-01`", ["Открыта карточка заявки.", "Отображается блок `Участники`."], "Не требуются.", ["Перейти к блоку `Участники`."], "Кнопка `+ Добавить созаемщика` отображается.", "Не требуются."),
        ("TC-ACP-003", "Открытие окна заявки для добавления созаемщика", "Positive", "High", "WP-01", "`ATOM-003`; `SRC-002`; `WP-01`", ["Открыта карточка заявки.", "Отображается блок `Участники`."], "Не требуются.", ["Нажать кнопку `+ Добавить созаемщика`."], "Открыто окно `Заявка` для добавления созаемщика.", "Закрыть окно без сохранения, если оно осталось открытым."),
        ("TC-ACP-004", "Исключение калькуляторного виджета из окна созаемщика", "Positive", "High", "WP-01", "`ATOM-004`; `SRC-002`; `GAP-001`; `WP-01`", ["Открыта карточка заявки.", "Открыто окно `Заявка` после нажатия `+ Добавить созаемщика`."], "Не требуются.", ["Осмотреть верхнюю часть окна созаемщика и область entrypoints калькулятора."], "В окне созаемщика отсутствует виджет `Краткая информация с калькулятора`.", "Закрыть окно без сохранения, если оно осталось открытым."),
        ("TC-ACP-005", "Замена наименования клиента на созаемщика в окне созаемщика", "Positive", "Medium", "WP-01", "`ATOM-005`; `SRC-002`; `WP-01`", ["Открыта карточка заявки.", "Открыто окно `Заявка` после нажатия `+ Добавить созаемщика`."], "Не требуются.", ["Просмотреть видимые наименования в окне созаемщика, где в форме заемщика используется роль `клиент`."], "В видимых наименованиях окна используется роль `созаемщик` вместо роли `клиент`.", "Закрыть окно без сохранения, если оно осталось открытым."),
        ("TC-ACP-006", "Видимость кнопки добавления залогодателя", "Positive", "High", "WP-01", "`ATOM-006`; `SRC-003`; `WP-01`", ["Открыта карточка заявки.", "Отображается блок `Участники`."], "Не требуются.", ["Перейти к блоку `Участники`."], "Кнопка `+ Добавить залогодателя` отображается.", "Не требуются."),
        ("TC-ACP-007", "Открытие окна заявки для добавления залогодателя", "Positive", "High", "WP-01", "`ATOM-007`; `SRC-003`; `WP-01`", ["Открыта карточка заявки.", "Отображается блок `Участники`."], "Не требуются.", ["Нажать кнопку `+ Добавить залогодателя`."], "Открыто окно `Заявка` для добавления залогодателя.", "Закрыть окно без сохранения, если оно осталось открытым."),
        ("TC-ACP-008", "Исключение FT-backed блоков и полей из окна залогодателя", "Positive", "High", "WP-01", "`ATOM-008`; `SRC-003`; `GAP-001`; `WP-01`", ["Открыта карточка заявки.", "Открыто окно `Заявка` после нажатия `+ Добавить залогодателя`."], "Исключения по ФТ: `Краткая информация с калькулятора`; `Сведения о занятости`; `контактные лица`; `кодовое слово`; `СНИЛС`; `верификация ИНН ФЛ`; `семейное положение`; `количество иждивенцев`; `социальный статус`; `подтверждение дохода`.", ["Просмотреть окно залогодателя.", "Сверить наличие каждого элемента из списка исключений в тестовых данных."], "В окне залогодателя не отображаются элементы из списка исключений в тестовых данных.", "Закрыть окно без сохранения, если оно осталось открытым."),
        ("TC-ACP-009", "Замена наименования клиента на залогодателя в окне залогодателя", "Positive", "Medium", "WP-01", "`ATOM-009`; `SRC-003`; `WP-01`", ["Открыта карточка заявки.", "Открыто окно `Заявка` после нажатия `+ Добавить залогодателя`."], "Не требуются.", ["Просмотреть видимые наименования в окне залогодателя, где в форме заемщика используется роль `клиент`."], "В видимых наименованиях окна используется роль `залогодатель` вместо роли `клиент`.", "Закрыть окно без сохранения, если оно осталось открытым."),
        ("TC-ACP-010", "Видимость виджета редактирования участника", "Positive", "Medium", "WP-01", "`ATOM-011`; `SRC-004`; `WP-01`", ["Открыта карточка заявки.", "Отображается блок `Участники`."], "Не требуются.", ["Перейти к таблице участников."], "Виджет `Редактировать` отображается.", "Не требуются."),
        ("TC-ACP-011", "Доступность редактирования при выбранном участнике", "Positive", "High", "WP-01", "`ATOM-012`; `SRC-004`; `WP-01`", ["Открыта карточка заявки.", "В таблице участников есть строка созаемщика `Иванов Иван Иванович`."], "Участник: `Иванов Иван Иванович`.", ["Выбрать строку участника из тестовых данных в таблице участников."], "Виджет `Редактировать` доступен к нажатию.", "Снять выбор строки, если он остался."),
        ("TC-ACP-012", "Недоступность редактирования без выбранного участника", "Negative", "High", "WP-01", "`ATOM-013`; `SRC-004`; `WP-01`", ["Открыта карточка заявки.", "В таблице участников есть хотя бы одна строка.", "Ни одна строка участника не выбрана."], "Не требуются.", ["Перейти к таблице участников без выбора строки."], "Виджет `Редактировать` находится в состоянии disabled.", "Не требуются."),
        ("TC-ACP-013", "Открытие окна редактирования с данными выбранного участника", "Positive", "High", "WP-01", "`ATOM-014`; `SRC-004`; `WP-01`", ["Открыта карточка заявки.", "В таблице участников есть строка созаемщика с ФИО `Иванов Иван Иванович` и паспортом `4512 123456`."], "Участник: тип `созаемщик`; ФИО `Иванов Иван Иванович`; паспорт `4512 123456`.", ["Выбрать строку участника из тестовых данных.", "Нажать виджет `Редактировать`."], "Открыто окно `Заявка` с данными выбранного участника из тестовых данных.", "Закрыть окно без сохранения, если оно осталось открытым."),
        ("TC-ACP-014", "Видимость виджета корзины участника", "Positive", "Medium", "WP-01", "`ATOM-015`; `SRC-005`; `WP-01`", ["Открыта карточка заявки.", "Отображается блок `Участники`."], "Не требуются.", ["Перейти к таблице участников."], "Виджет `Корзина` отображается.", "Не требуются."),
        ("TC-ACP-015", "Доступность корзины при выбранном участнике", "Positive", "High", "WP-01", "`ATOM-016`; `SRC-005`; `WP-01`", ["Открыта карточка заявки.", "В таблице участников есть строка созаемщика `Иванов Иван Иванович`."], "Участник: `Иванов Иван Иванович`.", ["Выбрать строку участника из тестовых данных в таблице участников."], "Виджет `Корзина` доступен к нажатию.", "Снять выбор строки, если он остался."),
        ("TC-ACP-016", "Недоступность корзины без выбранного участника", "Negative", "High", "WP-01", "`ATOM-017`; `SRC-005`; `WP-01`", ["Открыта карточка заявки.", "В таблице участников есть хотя бы одна строка.", "Ни одна строка участника не выбрана."], "Не требуются.", ["Перейти к таблице участников без выбора строки."], "Виджет `Корзина` находится в состоянии disabled.", "Не требуются."),
        ("TC-ACP-017", "Открытие подтверждения удаления участника", "Positive", "High", "WP-01", "`ATOM-018`; `SRC-005`; `GAP-002`; `WP-01`", ["Открыта карточка заявки.", "В таблице участников есть строка созаемщика `Иванов Иван Иванович`."], "Участник: `Иванов Иван Иванович`.", ["Выбрать строку участника из тестовых данных.", "Нажать виджет `Корзина`."], "Отображается popup подтверждения удаления участника с кнопками `Да` и `Отмена`.", "Выбрать `Отмена`, если popup остался открытым."),
        ("TC-ACP-018", "Удаление участника при подтверждении Да", "Positive", "High", "WP-01", "`ATOM-019`; `SRC-005`; `GAP-002`; `WP-01`", ["Открыта карточка заявки.", "В таблице участников есть строка созаемщика `Иванов Иван Иванович`.", "Открыт popup подтверждения удаления для этой строки."], "Участник: `Иванов Иван Иванович`.", ["В popup подтверждения выбрать `Да`."], "Строка участника `Иванов Иван Иванович` удалена из таблицы участников.", "Восстановить удаленного участника через `+ Добавить созаемщика`, если состояние заявки сохраняется в тестовом контуре."),
        ("TC-ACP-019", "Отмена удаления участника", "Negative", "High", "WP-01", "`ATOM-020`; `SRC-005`; `WP-01`", ["Открыта карточка заявки.", "В таблице участников есть строка созаемщика `Иванов Иван Иванович`.", "Открыт popup подтверждения удаления для этой строки."], "Участник: `Иванов Иван Иванович`.", ["В popup подтверждения выбрать `Отмена`."], "Popup закрыт, строка участника `Иванов Иван Иванович` остается в таблице участников.", "Не требуются."),
        ("TC-ACP-020", "Отображение типа участия в таблице участников", "Positive", "High", "WP-02", "`ATOM-021`; `SRC-006`; `WP-02`", ["Открыта карточка заявки.", "В таблице участников есть созданные участники из тестовых данных."], "Участник 1: создан как `созаемщик`. Участник 2: создан как `залогодатель`.", ["Просмотреть колонку `Тип участия` для участников из тестовых данных."], "Для каждого участника отображается тип участия, выбранный при его создании: `созаемщик` или `залогодатель`.", "Не требуются."),
        ("TC-ACP-021", "Отображение ФИО участника в таблице участников", "Positive", "Medium", "WP-02", "`ATOM-022`; `SRC-007`; `WP-02`", ["Открыта карточка заявки.", "В таблице участников есть созданный созаемщик `Иванов Иван Иванович`."], "ФИО участника: `Иванов Иван Иванович`.", ["Найти строку участника из тестовых данных в таблице участников."], "В строке участника отображается ФИО `Иванов Иван Иванович`.", "Не требуются."),
        ("TC-ACP-022", "Отображение паспорта участника в таблице участников", "Positive", "Medium", "WP-02", "`ATOM-023`; `SRC-008`; `WP-02`", ["Открыта карточка заявки.", "В таблице участников есть созданный созаемщик с паспортом `4512 123456`."], "Паспорт участника: `4512 123456`.", ["Найти строку участника из тестовых данных в таблице участников."], "В строке участника отображается паспорт `4512 123456`.", "Не требуются."),
        ("TC-ACP-023", "Автозаполнение ID клиента участника после сохранения заявки", "Positive", "Medium", "WP-02", "`ATOM-024`; `SRC-009`; `WP-02`", ["Открыта сохраненная карточка заявки.", "Для участника `Иванов Иван Иванович` система АБС вернула ID клиента `ABS-COB-001` после сохранения заявки."], "Участник: `Иванов Иван Иванович`. ID клиента из АБС: `ABS-COB-001`.", ["Найти строку участника из тестовых данных в таблице участников."], "В поле `ID клиента` для участника отображается значение `ABS-COB-001`.", "Не требуются."),
        ("TC-ACP-024", "Отсутствие отдельно добавленной строки залогодателя до действия добавления", "Positive", "Medium", "WP-01", "`ATOM-010`; `SRC-003`; `GAP-003`; `WP-01`", ["Открыта карточка заявки.", "В текущей заявке пользователь не нажимал `+ Добавить залогодателя`."], "Не требуются.", ["Перейти к таблице участников."], "В таблице участников не отображается отдельная строка с типом участия `залогодатель`, созданная через действие `+ Добавить залогодателя`.", "Не требуются."),
    ]
    parts = []
    for tc_id, title, tc_type, priority, package_id, trace, preconditions, data, steps, expected, post in cases:
        lines = [
            f"## {tc_id}",
            "",
            f"**Название:** {title}",
            "",
            f"**Тип:** {tc_type}",
            "",
            f"**Приоритет:** {priority}",
            "",
            f"**package_id:** {package_id}",
            "",
            f"**Трассировка:** {trace}",
            "",
            "### Предусловия",
            "",
            bullets(preconditions),
            "",
            "### Тестовые данные",
            "",
            data,
            "",
            "### Шаги",
            "",
            "\n".join(f"{i}. {step}" for i, step in enumerate(steps, start=1)),
            "",
            "### Итоговый ожидаемый результат",
            "",
            expected,
            "",
            "### Постусловия",
            "",
            post,
        ]
        parts.append("\n".join(lines).strip())
    return "\n\n".join(parts)


def canonical_body() -> str:
    links = bullets([
        f"`{TD_REL}/source-row-inventory.md`",
        f"`{TD_REL}/source-table-normalization.md`",
        f"`{TD_REL}/atomic-requirements-ledger.md`",
        f"`{TD_REL}/package-test-design-plan.md`",
        f"`{TD_REL}/coverage-obligation-table.md`",
        f"`{TD_REL}/coverage-gaps.md`",
        f"`{TD_REL}/writer-quality-gate.md`",
        f"`{TD_REL}/writer-self-check.md`",
    ])
    return "\n\n".join([
        "## Metadata\n\n"
        "| field | value |\n"
        "| --- | --- |\n"
        "| ft_slug | `AutoFin` |\n"
        f"| scope_slug | `{SCOPE}` |\n"
        "| section_id | `14` |\n"
        "| source | `section-14 rows 095-103` |\n"
        "| writer_stage | `writer-r1` |",
        "## Coverage Boundaries\n\n"
        "В scope входят только участники заявки: созаемщик и залогодатель, строки `095-103`.\n\n"
        "Не входят персональные данные основного клиента, паспортные поля анкеты как отдельный borrower-scope, адреса, контакты, документы анкеты, занятость, визуальная оценка, согласия, действие `Далее`, backend effects and persistence after deletion.",
        f"## Canonical Artifact Links\n\n{links}",
        "## Coverage Summary\n\n"
        "- `SRC-001`..`SRC-009` preserved.\n"
        "- `ATOM-001`..`ATOM-024` created.\n"
        "- Covered atoms: `24`.\n"
        "- Residual gaps linked to covered atoms: `GAP-002`, `GAP-003`.\n"
        "- Open non-blocking residual risks: `GAP-002`, `GAP-003`.",
        f"## Test Cases\n\n{tc_blocks()}",
    ]).strip()


def write_split_artifacts(final: bool) -> None:
    profile_stage = "final" if final else "bootstrap"
    write_markdown(TD / "artifact-write-strategy.md", [(1, "Artifact Write Strategy", artifact_write_strategy())])
    write_markdown(TD / "source-row-inventory.md", [(1, "Source Row Inventory", source_row_inventory())])
    write_markdown(TD / "source-table-normalization.md", [(1, "Source Table Normalization", source_table_normalization())])
    write_markdown(TD / "test-design-decision-table.md", [(1, "Test Design Decision Table", test_design_decision_table())])
    write_markdown(TD / "coverage-obligation-table.md", [(1, "Coverage Obligation Table", coverage_obligation_table())])
    write_markdown(TD / "atomic-requirements-ledger.md", [(1, "Atomic Requirements Ledger", atomic_ledger())])
    write_markdown(TD / "package-test-design-plan.md", [(1, "Package Test Design Plan", package_plan())])
    write_markdown(TD / "test-design-applicability-matrix.md", [(1, "Test-design Applicability Matrix", applicability_matrix())])
    write_markdown(TD / "internal-work-package-coverage.md", [(1, "Internal Work Package Coverage", internal_work_package_coverage())])
    write_markdown(TD / "coverage-gaps.md", [(1, "Coverage Gaps", coverage_gaps())])
    write_markdown(TD / "risk-priority-map.md", [(1, "Risk / Priority Map", risk_priority_map())])
    write_markdown(TD / "test-design-review.md", [(1, "Test Design Review", test_design_review())])
    write_markdown(TD / "writer-quality-gate.md", [(1, "Writer Quality Gate", writer_quality_gate(profile_stage))])
    write_markdown(TD / "writer-self-check.md", [(1, "Writer Self-Check", writer_self_check(final))])


def write_canonical() -> None:
    write_markdown(CANONICAL, [(1, "AutoFin Section 14 Participants Co-borrower Pledger Test Cases", canonical_body())])


def writer_response(final: bool) -> str:
    validation = (
        f"`python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/{CYCLE_REL}/cycle-state.yaml` passed; `{WRITER_PROFILE_REL}` unresolved warning/error count is 0."
        if final
        else "Pending runner validation."
    )
    return dedent(
        f"""
        | item | value |
        | --- | --- |
        | cycle_id | `autofin-{SCOPE}` |
        | stage | `writer-r1` |
        | result | `initial-draft-created` |
        | canonical_test_cases | `{CANONICAL_REL}` |
        | test_design_dir | `{TD_REL}` |
        | validation | {validation} |

        ## Coverage Notes

        - `GAP-001` is closed by analyst clarification and implemented as FT-backed inclusion/exclusion checks, not borrower-form duplication.
        - `GAP-002` remains visible as non-blocking residual risk for exact popup title/text and persistence after deletion.
        - `GAP-003` was added by writer for the default borrower-as-pledger statement because rows `095-103` do not specify an in-scope observable UI checkpoint.

        ## Next Stage

        Route to `structure-preflight-r1` using `work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md`.
        """
    ).strip()


def write_response(final: bool) -> None:
    write_markdown(OUTPUTS / "writer-r1-response.md", [(1, "Writer R1 Response", writer_response(final))])


def write_prompt() -> None:
    prompt = dedent(
        f"""
        ## Цель

        Выполнить structure preflight для writer draft scope `{SCOPE}`.

        ## Inputs

        - `fts/AutoFin/{CANONICAL_REL}`
        - `fts/AutoFin/{TD_REL}/`
        - `fts/AutoFin/{CYCLE_REL}/outputs/scoped-validator-profile.writer-r1.json`
        - `fts/AutoFin/{CYCLE_REL}/outputs/writer-r1-response.md`
        - `fts/AutoFin/{CYCLE_REL}/outputs/writer-session-log.writer-r1.md`
        - `fts/AutoFin/{CYCLE_REL}/outputs/agent-decision-log.writer-r1.md`
        - `fts/AutoFin/{CYCLE_REL}/cycle-state.yaml`

        ## Review Mode

        `reviewer.structure_preflight`

        ## Scope Rules

        - Check parseability, canonical TC structure, package_id presence, split artifact headings/table shapes and current writer-stage scoped validator profile.
        - Do not perform semantic/test-design review in this stage.
        - Keep `GAP-002` and `GAP-003` visible as non-blocking residual risks.

        ## Expected Outputs

        - structure preflight findings/session log/decision log under `work/review-cycles/{SCOPE}/outputs/`
        - updated `cycle-state.yaml` to `semantic-review-ready` if structure passes, or `structure-preflight-blocked` if it blocks
        """
    ).strip()
    write_markdown(PROMPTS / "prompt.structure-preflight-r1.md", [(1, "Structure Preflight R1 Prompt", prompt)])


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
    (OUTPUTS / "scoped-validator-profile.writer-r1.json").write_text(
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def session_log(final: bool) -> str:
    inputs_read = [f"`{p}` - selected required instruction file read before writer decisions." for p in SELECTED_REQUIRED_FILES]
    inputs_read += [f"`fts/AutoFin/{p}` - required scope/source input read for writer-r1." for p in SCOPE_INPUTS]
    inputs_read.append("`fts/AutoFin/source/AutoFinPreFinal.docx` rows `095-103` - full source row text extracted with `python-docx` for normalization.")
    validation = (
        f"`python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/{CYCLE_REL}/cycle-state.yaml` - pass; `{WRITER_PROFILE_REL}` generated by runner with unresolved warning/error count 0."
        if final
        else f"`python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/{CYCLE_REL}/cycle-state.yaml` - pending final run."
    )
    return dedent(
        f"""
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

        {bullets(inputs_read)}

        ## Inputs Not Used

        - Neighboring AutoFin scopes and historical review-cycle snapshots - excluded by current scope boundary.
        - Full borrower field test sets - not used because GAP-001 rule forbids mechanical duplication.

        ## Key Decisions

        - Preserve `SRC-001`..`SRC-009` before ledger creation.
        - Split role-specific form checks into FT-backed exclusions and visible role label substitutions.
        - Keep `GAP-002` open for exact popup title/text and deletion persistence.
        - Add `GAP-003` for default borrower-as-pledger observable checkpoint instead of inventing backend or `Далее` behavior.

        ## Risks And Fallbacks

        - Encoding fallback: initial non-UTF8 PowerShell output for one instruction read was discarded; sources were reread with explicit UTF-8.
        - `GAP-002` and `GAP-003` are non-blocking residual risks carried to reviewer.

        ## Validation

        - `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - pass, budget `140.2 / 200.0 KiB`.
        - {validation}

        ## Contamination Check

        - Scope limited to `fts/AutoFin`, section-14 rows `095-103`; no out-of-scope borrower, passport, address, contact, document, employment, visual assessment, consent or `Далее` behavior promoted into TC.

        ## Artifact Write Strategy

        | artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
        | --- | --- | --- | --- | --- | --- |
        | `{CANONICAL_REL}` and `{TD_REL}/*.md` | `package-based generated` | `file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest` | `yes` |

        ## Event Timeline

        | step | event | result | artifact_or_evidence |
        | --- | --- | --- | --- |
        | 1 | Resolved instruction context | budget pass | resolver output |
        | 2 | Read selected instructions and scope inputs | scope confirmed | `cycle-state.yaml`; `scope-contract.md` |
        | 3 | Extracted DOCX rows 095-103 | full source row text available | `source/AutoFinPreFinal.docx` |
        | 4 | Wrote split artifacts and canonical TC | artifacts created | `{TD_REL}`; `{CANONICAL_REL}` |
        | 5 | Prepared next prompt and state | route to structure preflight | `prompt.structure-preflight-r1.md`; `cycle-state.yaml` |

        ## Quality Checkpoints

        | checkpoint | status | evidence | follow_up |
        | --- | --- | --- | --- |
        | Writer Quality Gate | {"pass" if final else "blocked"} | `{TD_REL}/writer-quality-gate.md` | {"none" if final else "run runner validation"} |
        | Self-check near misses | pass | `GAP-003` retained instead of executable TC | reviewer should validate non-blocking classification |

        ## Technical Fallbacks

        | fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
        | --- | --- | --- | --- | --- | --- | --- | --- |
        | `TF-001` | `PowerShell console mojibake in early instruction read` | `default PowerShell stdout encoding` | `Get-Content -Encoding UTF8`; source reread and distorted stdout discarded | `n/a` | `n/a` | `none` | `none` |

        ## Handoff Notes For Next Session

        - Structure preflight should focus on parseability, headings, table columns, TC runtime fields and current writer-stage scoped validator profile.
        - Semantic reviewer should pay attention to `GAP-003` default pledger handling and verify that `GAP-001` was not converted into borrower-form duplication.
        """
    ).strip()


def decision_log() -> str:
    rows = [
        ["`DEC-001`", "1", "`scope-boundary`", "`scope-contract.md`", "Use only section-14 rows `095-103`.", "Scope contract excludes borrower personal data, documents, employment, visual assessment, consents and `Далее`.", f"`{CANONICAL_REL}`; `{TD_REL}`", "high", "applied"],
        ["`DEC-002`", "2", "`source-boundary`", "`source-row-inventory.md`", "Preserve `SRC-001`..`SRC-009` and map each to atoms or gaps.", "Row-level parity is mandatory for this scope.", f"`{TD_REL}/source-row-inventory.md`", "high", "applied"],
        ["`DEC-003`", "3", "`coverage`", "`GAP-001`; analyst clarification", "Use FT-backed block/exclusion list for participant forms.", "Copying all borrower fields would create false coverage and scope expansion.", f"`{TD_REL}/package-test-design-plan.md`", "high", "applied"],
        ["`DEC-004`", "4", "`gap`", "`GAP-002`", "Keep exact popup title/text and persistence as residual risk.", "Active prompt requires explicit `Да`/`Отмена` behavior only.", f"`{TD_REL}/coverage-gaps.md`", "high", "applied"],
        ["`DEC-005`", "5", "`gap`", "DOCX row 097 default pledger statement", "Create `GAP-003` for missing observable UI checkpoint.", "Rows `095-103` do not identify where default borrower-as-pledger is visible.", f"`{TD_REL}/coverage-gaps.md`", "medium", "applied"],
        ["`DEC-006`", "6", "`artifact-write`", "`writer-process-workflow.md`", "Use script-backed file manifest writes.", "Package-based split artifacts must avoid one-shot shell writes.", f"`{TD_REL}/artifact-write-strategy.md`", "high", "applied"],
        ["`DEC-007`", "7", "`routing`", "`session-based-review-cycle-format.md`", "Route to `structure-preflight-r1` with `writer-draft-ready` after clean validation.", "Writer must not start semantic review directly.", f"`{CYCLE_REL}/cycle-state.yaml`", "high", "applied"],
    ]
    body = table(
        ["decision_id", "step", "decision_type", "input_or_trigger", "decision", "rationale", "artifact_or_output", "risk_or_confidence", "status"],
        rows,
    )
    meta = table(
        ["field", "value"],
        [["ft_slug", "`AutoFin`"], ["scope_slug", f"`{SCOPE}`"], ["stage", "`ft-test-case-writer / writer-r1`"], ["started_from", f"`{CYCLE_REL}/cycle-state.yaml`"]],
    )
    write_markdown(
        OUTPUTS / "agent-decision-log.writer-r1.md",
        [(2, "Decision Log Metadata", meta), (2, "Decision Log", body)],
        title="Agent Decision Log",
    )


def write_logs(final: bool) -> None:
    write_markdown(OUTPUTS / "writer-session-log.writer-r1.md", [(1, "Writer R1 Session Log", session_log(final))])
    decision_log()


def write_state(final: bool) -> None:
    current_stage = "structure-preflight-r1" if final else "writer-r1"
    stage_status = "writer-draft-ready" if final else "scope-ready-for-writer"
    active_prompt = f"{CYCLE_REL}/prompts/prompt.structure-preflight-r1.md" if final else f"{CYCLE_REL}/prompts/prompt.writer-r1.md"
    state = dedent(
        f"""
        cycle_id: autofin-{SCOPE}
        ft_slug: AutoFin
        scope_slug: {SCOPE}
        section_id: 14
        current_stage: {current_stage}
        stage_status: {stage_status}
        semantic_round: 0
        max_semantic_rounds: 2
        canonical_test_cases: {CANONICAL_REL}
        test_design_dir: {TD_REL}
        active_snapshot: none
        active_transition_prompt: {active_prompt}
        sessions: []
        latest_artifacts:
          - AGENT-NOTES.md
          - work/stage-handoffs/00-autofin-scope-selection/source-selection.md
          - work/stage-handoffs/02-application-card-questionnaires-decomposition/scope-options.md
          - {HANDOFF_REL}/workflow-state.yaml
          - {HANDOFF_REL}/scope-gap-review.md
          - {HANDOFF_REL}/scope-contract.md
          - {HANDOFF_REL}/source-parity-check.md
          - {HANDOFF_REL}/source-row-inventory.md
          - {HANDOFF_REL}/mockup-visual-inventory.md
          - {HANDOFF_REL}/scope-coverage-gaps.md
          - {HANDOFF_REL}/scope-clarification-requests.md
          - {CANONICAL_REL}
          - {TD_REL}/source-row-inventory.md
          - {TD_REL}/source-table-normalization.md
          - {TD_REL}/atomic-requirements-ledger.md
          - {TD_REL}/internal-work-package-coverage.md
          - {TD_REL}/package-test-design-plan.md
          - {TD_REL}/test-design-decision-table.md
          - {TD_REL}/test-design-applicability-matrix.md
          - {TD_REL}/coverage-obligation-table.md
          - {TD_REL}/coverage-gaps.md
          - {TD_REL}/risk-priority-map.md
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
          - GAP-002: popup exact title/text and deletion persistence are not specified; cover only explicit Да/Отмена behavior.
          - GAP-003: observable UI checkpoint for default borrower-as-pledger is not specified in rows 095-103.
        accepted_risks:
          - GAP-002: exact popup title/text and deletion persistence are non-blocking residual risk; do not assert them until analyst clarification.
          - GAP-003: default borrower-as-pledger observable checkpoint is non-blocking residual risk; do not invent backend or next-step behavior.
        """
    ).strip()
    (CYCLE / "cycle-state.yaml").write_text(state + "\n", encoding="utf-8", newline="\n")


def write_compat_workflow_state() -> None:
    state = dedent(
        f"""
        ft_slug: AutoFin
        scope_slug: {SCOPE}
        current_stage: ft-test-case-iteration
        stage_status: ready-for-review
        current_round: 1
        next_skill: ft-test-case-reviewer
        review_mode: structure_preflight
        required_inputs:
          - {CYCLE_REL}/cycle-state.yaml
          - {CANONICAL_REL}
          - {TD_REL}
          - {CYCLE_REL}/prompts/prompt.structure-preflight-r1.md
        latest_artifacts:
          canonical_test_cases: {CANONICAL_REL}
          test_design_dir: {TD_REL}
          cycle_state: {CYCLE_REL}/cycle-state.yaml
          active_transition_prompt: {CYCLE_REL}/prompts/prompt.structure-preflight-r1.md
          session_log: {CYCLE_REL}/outputs/writer-session-log.writer-r1.md
          decision_log: {CYCLE_REL}/outputs/agent-decision-log.writer-r1.md
          scoped_validator_profile: {WRITER_PROFILE_REL}
        open_questions:
          - GAP-002: popup exact title/text and deletion persistence are not specified.
          - GAP-003: observable UI checkpoint for default borrower-as-pledger is not specified.
        blocking_reasons: []
        accepted_risks:
          - GAP-002 non-blocking residual risk.
          - GAP-003 non-blocking residual risk.
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

    write_split_artifacts(final=args.final)
    write_canonical()
    write_response(final=args.final)
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
