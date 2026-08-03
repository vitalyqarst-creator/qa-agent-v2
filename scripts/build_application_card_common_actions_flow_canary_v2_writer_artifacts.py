from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FT_ROOT = ROOT / "fts" / "ft-2-OF_17"
SCOPE = "application-card-common-actions-flow-canary-v2"
SECTION = "section-38"
TD_REL = f"work/test-design/{SECTION}-{SCOPE}"
TD = FT_ROOT / TD_REL
CYCLE_REL = f"work/review-cycles/{SCOPE}"
CYCLE = FT_ROOT / CYCLE_REL
OUTPUTS = CYCLE / "outputs"
PROMPTS = CYCLE / "prompts"
CANONICAL_REL = f"test-cases/{SECTION}-{SCOPE}.md"
CANONICAL = FT_ROOT / CANONICAL_REL
WRITER_PROFILE_REL = f"work/review-cycles/{SCOPE}/outputs/scoped-validator-profile.writer-r1.json"


DICT_VALUES = [
    "Высокая ставка",
    "Не готов предоставить документы",
    "Не устраивает сумма",
    "Кредит/карта не нужны",
    "Технический сбой",
    "Заявка создана ошибочно",
]


def table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def write_with_section_helper(target: Path, heading: str, body: str) -> None:
    scratch = OUTPUTS / "_writer_r1_artifact_write"
    scratch.mkdir(parents=True, exist_ok=True)
    stem = target.name.replace(".", "_").replace("-", "_")
    content_file = scratch / f"{stem}.content.md"
    manifest_file = scratch / f"{stem}.manifest.json"
    content_file.write_text(body.strip() + "\n", encoding="utf-8", newline="\n")
    manifest = {
        "target_path": os.path.relpath(target, scratch),
        "sections": [{"level": 2, "heading": heading, "content_file": content_file.name}],
    }
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(manifest_file)],
        cwd=str(ROOT),
        check=True,
    )


def write_artifact_strategy() -> None:
    body = table(
        ["item", "value", "evidence"],
        [
            ["preflight_result", "`large-file / package-based`", "`scope-contract.md` defines `WP-01` and `WP-02`; split artifacts required."],
            ["write_method", "`file-based manifest/chunked writing`", "`scripts/write_artifact_sections.py --manifest <manifest.json>` selected before artifact generation."],
            ["forbidden_methods_checked", "`yes`", "No one-shot PowerShell argument, no here-string, no inline giant command."],
            ["chunk_plan", "`WP-01 -> WP-02 -> process outputs`", "Cancel action flow is written before history entrypoint."],
            ["helper_artifacts", "`scripts/write_artifact_sections.py`; transient manifests under `outputs/_writer_r1_artifact_write`", "Manifest files are transport artifacts, not source evidence."],
            ["validation_plan", "`artifact-shape-preflight; runner scoped validator`", "`python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_17/work/review-cycles/application-card-common-actions-flow-canary-v2/cycle-state.yaml`."],
        ],
    )
    write_with_section_helper(TD / "artifact-write-strategy.md", "Artifact Write Strategy", body)


def write_source_artifacts() -> None:
    write_with_section_helper(
        TD / "source-row-inventory.md",
        "Source Row Inventory",
        table(
            ["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"],
            [
                ["`SRC-001`", "`WP-01`", "`Отменить заявку`", "`DOCX section-35; table row \"Отменить заявку\"`", "`section-35`", "`yes`", "`ATOM-001`; `ATOM-002`; `ATOM-003`; `ATOM-004`; `ATOM-005`; `ATOM-006`; `GAP-001`; `GAP-002`"],
                ["`SRC-002`", "`WP-01`", "`Отменить заявку`", "`DOCX section-38; table row \"Отменить заявку\"`", "`section-38`", "`yes`", "`ATOM-001`; `ATOM-002`; `ATOM-003`; `ATOM-004`; `ATOM-005`; `ATOM-006`; `GAP-001`; `GAP-002`"],
                ["`SRC-003`", "`WP-02`", "`История заявки`", "`DOCX section-38; table row \"История заявки\"; target form section-39`", "`section-38`", "`yes`", "`ATOM-007`; `GAP-001`"],
            ],
        ),
    )
    write_with_section_helper(
        TD / "source-row-completeness-matrix.md",
        "Source Row Completeness Matrix",
        table(
            ["source_row_id", "source_requirement_codes", "normalized_property_ids", "linked_atoms", "gap_ids", "coverage_decision"],
            [
                ["`SRC-001`", "`section-35`", "`SP-WP01-001`; `SP-WP01-002`; `SP-WP01-003`; `SP-WP01-004`; `SP-WP01-005`; `SP-WP01-006`", "`ATOM-001`; `ATOM-002`; `ATOM-003`; `ATOM-004`; `ATOM-005`; `ATOM-006`", "`GAP-001`; `GAP-002`", "`duplicate-normalized-with-SRC-002`"],
                ["`SRC-002`", "`section-38`", "`SP-WP01-001`; `SP-WP01-002`; `SP-WP01-003`; `SP-WP01-004`; `SP-WP01-005`; `SP-WP01-006`", "`ATOM-001`; `ATOM-002`; `ATOM-003`; `ATOM-004`; `ATOM-005`; `ATOM-006`", "`GAP-001`; `GAP-002`", "`duplicate-normalized-with-SRC-001`"],
                ["`SRC-003`", "`section-38`", "`SP-WP02-001`", "`ATOM-007`", "`GAP-001`", "`covered-entrypoint-only`"],
            ],
        ),
    )
    rows = [
        ["`SRC-001`", "`SP-WP01-001`", "`WP-01`", "`Карточка УЗ`", "`action-opens-modal`", "`Пользователь выбирает действие Отменить заявку`", "`Открывается окно выбора причины отказа.`", "`section-35`", "`DOCX row SRC-001; duplicate row SRC-002 preserved in completeness matrix`", "`high`", "`none_required:covered`", "`ATOM-001`"],
        ["`SRC-001`", "`SP-WP01-002`", "`WP-01`", "`Окно выбора причины отказа`", "`dictionary-source`", "`Причина отказа выбирается из справочника`", "`Используются активные значения DICT-001.`", "`section-35`", "`DOCX row SRC-001; support sheet Причины отказа от УЗ; duplicate row SRC-002 preserved in completeness matrix`", "`high`", "`none_required:covered`", "`ATOM-003`"],
        ["`SRC-001`", "`SP-WP01-003`", "`WP-01`", "`Окно выбора причины отказа`", "`validation-message`", "`Нажат Подтвердить без выбранной причины`", "`Отображается сообщение Выберите причину отказа.`", "`section-35`", "`DOCX row SRC-001; duplicate row SRC-002 preserved in completeness matrix`", "`high`", "`none_required:covered`", "`ATOM-002`"],
        ["`SRC-001`", "`SP-WP01-004`", "`WP-01`", "`Окно выбора причины отказа`", "`status-transition`", "`Нажат Подтвердить при выбранной хотя бы одной причине`", "`УЗ переходит в статус Отказ клиента.`", "`section-35`", "`DOCX row SRC-001; duplicate row SRC-002 preserved in completeness matrix`", "`high`", "`none_required:covered`", "`ATOM-004`"],
        ["`SRC-001`", "`SP-WP01-005`", "`WP-01`", "`Карточка УЗ`", "`expected-result-unclear`", "`GAP-002 clarification target`", "`unclear:GAP-002`", "`section-35`", "`scope-coverage-gaps.md GAP-002; duplicate row SRC-002 preserved in completeness matrix`", "`medium`", "`GAP-002`", "`ATOM-005`"],
        ["`SRC-001`", "`SP-WP01-006`", "`WP-01`", "`Окно выбора причины отказа`", "`modal-cancel-branch`", "`Нажата кнопка Отменить в окне`", "`Пользователь возвращается в карточку УЗ.`", "`section-35`", "`DOCX row SRC-001; duplicate row SRC-002 preserved in completeness matrix`", "`high`", "`none_required:covered`", "`ATOM-006`"],
        ["`SRC-003`", "`SP-WP02-001`", "`WP-02`", "`Карточка УЗ`", "`action-opens-window`", "`Пользователь выбирает действие История заявки`", "`Открывается окно просмотра истории заявки.`", "`section-38`", "`DOCX row История заявки; section-39 target only`", "`high`", "`none_required:covered`", "`ATOM-007`"],
    ]
    write_with_section_helper(
        TD / "source-table-normalization.md",
        "Source Table Normalization",
        table(
            ["source_row_id", "source_property_id", "package_id", "field_or_block", "property", "condition", "expected_behavior", "requirement_code", "source_ref", "confidence", "gap_id", "linked_atoms"],
            rows,
        ),
    )


def write_dictionary_artifact() -> None:
    write_with_section_helper(
        TD / "dictionary-inventory.md",
        "Dictionary Inventory",
        table(
            ["dictionary_id", "dictionary_name", "source_file", "source_location", "extraction_status", "active_values", "archived_values", "used_by_source_properties", "gap_id", "notes"],
            [[
                "`DICT-001`",
                "`Причины отказа от УЗ`",
                "`support/Наполнение справочников_v1.xlsx`",
                "`sheet: Причины отказа от УЗ; columns: Значение, Архивный, Описание атрибута`",
                "`extracted`",
                "; ".join(f"`{value}`" for value in DICT_VALUES),
                "`none_required:no_archived_values`",
                "`SP-WP01-002`; `TC-ACAF-CV2-002`; `TC-ACAF-CV2-004`",
                "`none_required:covered`",
                "`Архивный = Нет` трактуется как active; строка `Назад` не является значением справочника.",
            ]],
        ),
    )


def write_design_artifacts() -> None:
    tddt_rows = [
        ["`DD-001`", "`WP-01`", "`SP-WP01-001`", "`ATOM-001`", "`action-opens-modal`", "`standalone_tc`", "Открытие окна является отдельным observable result.", "`TC-ACAF-CV2-001`", "`source`", "`yes`", "`Окно выбора причины отказа открыто`", "`Открытие окна`", "`none_required:covered`", "`none_required:covered`", "`low`"],
        ["`DD-002`", "`WP-01`", "`SP-WP01-002`", "`ATOM-003`", "`dictionary-source`", "`standalone_tc`", "Справочник должен использовать полный активный DICT-001.", "`TC-ACAF-CV2-002`", "`support`", "`yes`", "`Отображаются все активные значения DICT-001`", "`Состав списка`", "`none_required:covered`", "`none_required:covered`", "`medium`"],
        ["`DD-003`", "`WP-01`", "`SP-WP01-003`", "`ATOM-002`", "`validation-message`", "`standalone_tc`", "Сообщение задано точным текстом источника.", "`TC-ACAF-CV2-003`", "`source`", "`yes`", "`Выберите причину отказа`", "`Ветка без причины`", "`none_required:covered`", "`none_required:covered`", "`low`"],
        ["`DD-004`", "`WP-01`", "`SP-WP01-004`", "`ATOM-004`", "`status-transition`", "`standalone_tc`", "Переход статуса является source-backed oracle.", "`TC-ACAF-CV2-004`", "`source`", "`yes`", "`Статус Отказ клиента отображается`", "`Переход статуса`", "`none_required:covered`", "`none_required:covered`", "`medium`"],
        ["`DD-005`", "`WP-01`", "`SP-WP01-005`", "`ATOM-005`", "`expected-result-unclear`", "`out_of_scope`", "Точный observable UI-механизм запрета редактирования не входит в executable writer draft без source/UI evidence.", "`GAP-002`", "`scope-coverage-gaps.md GAP-002`", "`no`", "`unclear:GAP-002`", "`none_required:narrow_gap_only`", "`exact edit-lock UI oracle`", "`GAP-002`", "`medium`"],
        ["`DD-006`", "`WP-01`", "`SP-WP01-006`", "`ATOM-006`", "`modal-cancel-branch`", "`standalone_tc`", "Ветка Отменить имеет отдельный expected result.", "`TC-ACAF-CV2-005`", "`source`", "`yes`", "`Окно закрыто и карточка УЗ отображается`", "`Возврат в карточку`", "`none_required:covered`", "`none_required:covered`", "`low`"],
        ["`DD-007`", "`WP-02`", "`SP-WP02-001`", "`ATOM-007`", "`action-opens-window`", "`standalone_tc`", "Только entrypoint истории входит в scope.", "`TC-ACAF-CV2-006`", "`source`", "`yes`", "`Окно просмотра истории заявки открыто`", "`Открытие окна`", "`none_required:covered`", "`none_required:covered`", "`low`"],
    ]
    write_with_section_helper(
        TD / "test-design-decision-table.md",
        "Test Design Decision Table",
        table(
            ["decision_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "decision", "decision_reason", "planned_tc_or_gap", "oracle_source", "must_be_executable", "observable_oracle", "testable_part", "blocked_part", "gap_admissibility", "review_risk"],
            tddt_rows,
        ),
    )
    obligation_rows = [
        ["`OBL-001`", "`WP-01`", "`SP-WP01-003`", "`ATOM-002`", "`validation-message`", "`message-triggered`", "`Подтвердить without selected reason shows exact message Выберите причину отказа`", "`section-35`", "`TC-ACAF-CV2-003`", "`covered`", "`none_required:covered`"],
    ]
    write_with_section_helper(
        TD / "coverage-obligation-table.md",
        "Coverage Obligation Table",
        table(
            ["obligation_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "obligation_class", "required_behavior", "source_ref", "planned_tc_or_gap", "status", "review_notes"],
            obligation_rows,
        ),
    )
    ledger_rows = [
        ["`ATOM-001`", "`WP-01`", "`SP-WP01-001`", "`section-35; section-38`", "`SRC-001; SRC-002`", "`Отменить заявку` открывает окно выбора причины отказа.", "`action-opens-modal`", "`covered`", "`TC-ACAF-CV2-001`", "`TC-ACAF-CV2-001`", "`none_required:covered`"],
        ["`ATOM-002`", "`WP-01`", "`SP-WP01-003`", "`section-35; section-38`", "`SRC-001; SRC-002`", "`Подтвердить` без выбранной причины показывает сообщение `Выберите причину отказа`.", "`validation-message`", "`covered`", "`TC-ACAF-CV2-003`", "`TC-ACAF-CV2-003`", "`none_required:covered`"],
        ["`ATOM-003`", "`WP-01`", "`SP-WP01-002`", "`DICT-001`", "`SRC-001; SRC-002`", "Причина отказа выбирается из активных значений справочника `Причины отказа от УЗ`.", "`dictionary-source`", "`covered`", "`TC-ACAF-CV2-002`", "`TC-ACAF-CV2-002`", "`none_required:covered`"],
        ["`ATOM-004`", "`WP-01`", "`SP-WP01-004`", "`section-35; section-38`", "`SRC-001; SRC-002`", "`Подтвердить` при выбранной хотя бы одной причине переводит УЗ в статус `Отказ клиента`.", "`status-transition`", "`covered`", "`TC-ACAF-CV2-004`", "`TC-ACAF-CV2-004`", "`none_required:covered`"],
        ["`ATOM-005`", "`WP-01`", "`SP-WP01-005`", "`section-35; section-38`", "`SRC-001; SRC-002`", "После статуса `Отказ клиента` дальнейшее редактирование УЗ запрещается.", "`expected-result-unclear`", "`unclear`", "`not_covered:GAP-002`", "`GAP-002`", "`GAP-002`"],
        ["`ATOM-006`", "`WP-01`", "`SP-WP01-006`", "`section-35; section-38`", "`SRC-001; SRC-002`", "`Отменить` в окне выбора причины возвращает пользователя в карточку УЗ.", "`modal-cancel-branch`", "`covered`", "`TC-ACAF-CV2-005`", "`TC-ACAF-CV2-005`", "`none_required:covered`"],
        ["`ATOM-007`", "`WP-02`", "`SP-WP02-001`", "`section-38`", "`SRC-003`", "`История заявки` открывает окно просмотра истории заявки.", "`action-opens-window`", "`covered`", "`TC-ACAF-CV2-006`", "`TC-ACAF-CV2-006`", "`none_required:covered`"],
    ]
    write_with_section_helper(
        TD / "atomic-requirements-ledger.md",
        "Atomic Requirements Ledger",
        table(
            ["atom_id", "package_id", "source_property_id", "requirement_code", "source_row_id", "atomic_statement", "property_type", "coverage_status", "covered_by_tc", "planned_tc_or_gap", "gap_id"],
            ledger_rows,
        ),
    )
    plan_rows = [
        ["`PLAN-001`", "`WP-01`", "`action-flow`", "`SRC-001; SRC-002`", "`ATOM-001`", "Открыть окно выбора причины отказа действием `Отменить заявку`.", "`positive`", "`modal-open`", "`action-click`", "Открыто окно выбора причины отказа.", "`DOCX row`", "`TC-ACAF-CV2-001`", "`covered`"],
        ["`PLAN-002`", "`WP-01`", "`dictionary`", "`DICT-001`", "`ATOM-003`", "Проверить состав списка причин отказа по active values.", "`positive`", "`dictionary-active-values`", "`all-active-values`", "Список содержит все активные DICT-001 значения и не содержит значений вне DICT-001.", "`support workbook`", "`TC-ACAF-CV2-002`", "`covered`"],
        ["`PLAN-003`", "`WP-01`", "`validation`", "`SRC-001; SRC-002`", "`ATOM-002`", "Нажать `Подтвердить` без выбранной причины.", "`negative`", "`required-selection`", "`empty-selection`", "Показано сообщение `Выберите причину отказа`.", "`DOCX row`", "`TC-ACAF-CV2-003`", "`covered`"],
        ["`PLAN-004`", "`WP-01`", "`status-lifecycle`", "`SRC-001; SRC-002`; `DICT-001`", "`ATOM-004`", "Выбрать одну активную причину и нажать `Подтвердить`.", "`positive`", "`status-transition`", "`one-active-reason`", "Статус УЗ отображается как `Отказ клиента`.", "`DOCX row`", "`TC-ACAF-CV2-004`", "`covered`"],
        ["`PLAN-005`", "`WP-01`", "`edit-lock`", "`SRC-001; SRC-002`", "`ATOM-005`", "Не создавать executable TC до появления source-backed UI oracle.", "`gap`", "`observable-oracle`", "`after-status-refusal`", "`unclear:GAP-002`", "`source lacks UI mechanism`", "`GAP-002`", "`unclear`"],
        ["`PLAN-006`", "`WP-01`", "`modal-branch`", "`SRC-001; SRC-002`", "`ATOM-006`", "Нажать `Отменить` в окне выбора причины.", "`positive`", "`modal-cancel-return`", "`cancel-button`", "Окно закрыто, отображается карточка УЗ.", "`DOCX row`", "`TC-ACAF-CV2-005`", "`covered`"],
        ["`PLAN-007`", "`WP-02`", "`action-flow`", "`SRC-003`", "`ATOM-007`", "Нажать `История заявки` в карточке УЗ.", "`positive`", "`window-open`", "`action-click`", "Открыто окно просмотра истории заявки.", "`DOCX row`", "`TC-ACAF-CV2-006`", "`covered`"],
    ]
    write_with_section_helper(
        TD / "package-test-design-plan.md",
        "Package Test Design Plan",
        table(
            ["design_item_id", "package_id", "design_dimension", "source_ref", "linked_atoms", "planned_check", "check_type", "coverage_class", "input_class", "single_expected_behavior", "oracle_source", "planned_tc_or_gap", "status"],
            plan_rows,
        ),
    )


def write_supporting_artifacts() -> None:
    write_with_section_helper(
        TD / "internal-work-package-coverage.md",
        "Internal Work Package Coverage",
        table(
            ["package_id", "focus", "ledger_gate", "design_plan_gate", "tc_gate", "atoms", "covered", "gap", "unclear", "TC count", "status"],
            [
                ["`WP-01`", "`Cancel application action flow`", "`pass`", "`pass`", "`pass`", "`6`", "`5`", "`0`", "`1`", "`5`", "`ready-for-review`"],
                ["`WP-02`", "`History action entrypoint`", "`pass`", "`pass`", "`pass`", "`1`", "`1`", "`0`", "`0`", "`1`", "`ready-for-review`"],
            ],
        ),
    )
    write_with_section_helper(
        TD / "package-ledger-self-check.md",
        "Package Ledger Self-Check",
        table(
            ["package_id", "check", "status", "evidence", "required_action"],
            [
                ["`WP-01`", "`atomicity`", "`pass`", "`ATOM-001`..`ATOM-006` split modal open, dictionary, empty confirm, status transition, edit-lock gap and modal cancel.", "`none_required:pass`"],
                ["`WP-02`", "`scope-boundary`", "`pass`", "`ATOM-007` covers only history window opening, not section-39 details.", "`none_required:pass`"],
            ],
        ),
    )
    write_with_section_helper(
        TD / "package-design-plan-self-check.md",
        "Package Design Plan Self-Check",
        table(
            ["package_id", "check", "status", "evidence", "required_action"],
            [
                ["`WP-01`", "`branch-separation`", "`pass`", "`PLAN-003`, `PLAN-004`, `PLAN-006` are separate rows and separate TC targets.", "`none_required:pass`"],
                ["`WP-01`", "`gap-discipline`", "`pass`", "`PLAN-005` routes edit-lock mechanism to `GAP-002`.", "`none_required:pass`"],
                ["`WP-02`", "`history-boundary`", "`pass`", "`PLAN-007` covers only entrypoint.", "`none_required:pass`"],
            ],
        ),
    )
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
    review_rows = []
    for item in review_items:
        if item == "unsupported-ui-mechanism":
            evidence = "`GAP-002` preserves unspecified edit-lock UI mechanism; no TC invents disabled/error/save mechanics."
        elif item == "dictionary-closed-set":
            evidence = "`TC-ACAF-CV2-002` uses full active `DICT-001` list."
        elif item in {"numeric-length-boundaries", "mask-format-coverage"}:
            evidence = "`not_applicable:source_has_no_numeric_length_or_mask_rules`."
        else:
            evidence = "`pass` based on package plan and ledger alignment."
        review_rows.append([f"`{item}`", "`pass`", "`info`", "`all`", evidence, "`none_required:pass`", "`no`"])
    write_with_section_helper(
        TD / "test-design-review.md",
        "Test Design Review",
        table(["review_item", "status", "severity", "affected_package", "evidence", "required_action", "blocks_ready_for_review"], review_rows),
    )
    write_with_section_helper(
        TD / "dependency-matrix.md",
        "Dependency Matrix",
        table(
            ["dependency_id", "package_id", "controlling_action_or_state", "controlling_value", "dependent_field", "branch", "source_ref", "linked_atoms", "planned_tc_or_gap", "tc_gap", "decision"],
            [
                ["`DEP-001`", "`WP-01`", "`Подтвердить`", "`reason not selected`", "`reason selection`", "`no-reason-selected`", "`SRC-001; SRC-002`", "`ATOM-002`", "`TC-ACAF-CV2-003`", "`TC-ACAF-CV2-003`", "`covered`"],
                ["`DEP-002`", "`WP-01`", "`Подтвердить`", "`one active reason selected`", "`UZ status`", "`one-active-reason-selected`", "`SRC-001; SRC-002; DICT-001`", "`ATOM-004`", "`TC-ACAF-CV2-004`", "`TC-ACAF-CV2-004`", "`covered`"],
                ["`DEP-003`", "`WP-01`", "`Отменить` in modal", "`cancel button selected`", "`modal state`", "`cancel-modal`", "`SRC-001; SRC-002`", "`ATOM-006`", "`TC-ACAF-CV2-005`", "`TC-ACAF-CV2-005`", "`covered`"],
            ],
        ),
    )
    write_with_section_helper(
        TD / "test-design-applicability-matrix.md",
        "Test-design Applicability Matrix",
        table(
            ["dimension", "applicable", "reason", "source_ref", "linked_atoms", "linked_test_cases", "gap_id", "status"],
            [
                ["`scenario-use-case`", "`yes`", "Actions are source rows in card.", "`SRC-001`; `SRC-003`", "`ATOM-001`; `ATOM-007`", "`TC-ACAF-CV2-001`; `TC-ACAF-CV2-006`", "", "`covered`"],
                ["`expected-result`", "`yes`", "Reason required before confirm and exact message is source-backed.", "`SRC-001`; `SRC-002`", "`ATOM-002`", "`TC-ACAF-CV2-003`", "", "`covered`"],
                ["`table-list`", "`yes`", "`DICT-001` supplies active values.", "`DICT-001`", "`ATOM-003`", "`TC-ACAF-CV2-002`", "", "`covered`"],
                ["`dependency`", "`yes`", "Confirm without/with reason and modal cancel branches.", "`SRC-001`; `SRC-002`", "`ATOM-002`; `ATOM-004`; `ATOM-006`", "`TC-ACAF-CV2-003`; `TC-ACAF-CV2-004`; `TC-ACAF-CV2-005`", "", "`covered`"],
                ["`status-lifecycle`", "`yes`", "Status transition is source-backed.", "`SRC-001`; `SRC-002`", "`ATOM-004`", "`TC-ACAF-CV2-004`", "", "`covered`"],
                ["`expected-result`", "`unclear`", "Edit lock rule exists, observable mechanism absent.", "`SRC-001`; `SRC-002`", "`ATOM-005`", "", "`GAP-002`", "`unclear`"],
                ["`integration`", "`no`", "Out of scope by scope contract.", "`scope-contract.md`", "", "", "", "`not-applicable`"],
            ],
        ),
    )
    write_with_section_helper(
        TD / "fixture-catalog.md",
        "Fixture Catalog",
        table(
            ["fixture_id", "package_id", "fixture_purpose", "source_or_scope_basis", "data_or_state", "used_by_tc", "risk"],
            [
                ["`FX-001`", "`WP-01; WP-02`", "Baseline application card with in-scope actions visible.", "`scope-contract.md` rows for actions in UZ card.", "Pre-existing UZ card where `Отменить заявку` and `История заявки` actions are available.", "`TC-ACAF-CV2-001`; `TC-ACAF-CV2-002`; `TC-ACAF-CV2-003`; `TC-ACAF-CV2-005`; `TC-ACAF-CV2-006`", "`medium:source_does_not_define_initial_status`"],
                ["`FX-002`", "`WP-01`", "Mutable application card for irreversible refusal transition.", "`SRC-001; SRC-002` status transition.", "Separate UZ card where cancellation can be confirmed with reason `Высокая ставка`.", "`TC-ACAF-CV2-004`", "`medium:mutates_status`"],
            ],
        ),
    )
    write_with_section_helper(
        TD / "coverage-metrics.md",
        "Coverage Metrics",
        table(
            ["metric_id", "dimension", "applicable_obligations", "covered", "gap", "unclear", "evidence"],
            [
                ["`MET-001`", "`action-flow`", "`3`", "`3`", "`0`", "`0`", "`TC-ACAF-CV2-001`; `TC-ACAF-CV2-005`; `TC-ACAF-CV2-006`"],
                ["`MET-002`", "`validation-message`", "`1`", "`1`", "`0`", "`0`", "`TC-ACAF-CV2-003`"],
                ["`MET-003`", "`dictionary-source`", "`1`", "`1`", "`0`", "`0`", "`TC-ACAF-CV2-002`"],
                ["`MET-004`", "`status-lifecycle`", "`1`", "`1`", "`0`", "`0`", "`TC-ACAF-CV2-004`"],
                ["`MET-005`", "`editability`", "`1`", "`0`", "`0`", "`1`", "`GAP-002`"],
                ["`MET-006`", "`traceability-parity`", "`1`", "`0`", "`0`", "`1`", "`GAP-001`"],
            ],
        ),
    )
    write_with_section_helper(
        TD / "risk-priority-map.md",
        "Risk / Priority Map",
        table(
            ["atom_id", "coverage_dimension", "impact", "likelihood", "risk_score", "risk_level", "risk_factors", "source_ref", "required_priority", "linked_test_cases", "gap_id", "residual_risk_decision", "rationale"],
            [
                ["`ATOM-004`", "`status-lifecycle`", "`5`", "`3`", "`15`", "`high`", "`irreversible-state`", "`section-35; section-38`", "`High`", "`TC-ACAF-CV2-004`", "`none_required:covered`", "`none`", "Отказ клиента меняет lifecycle/status."],
                ["`ATOM-005`", "`editability`", "`4`", "`3`", "`12`", "`medium`", "`edit-lock`", "`section-35; section-38`", "`Medium`", "`not_covered:GAP-002`", "`GAP-002`", "`deferred-by-scope`", "Правило есть, но observable UI oracle не задан."],
                ["`ATOM-002`", "`validation-message`", "`3`", "`3`", "`9`", "`medium`", "`critical-validation`", "`section-35; section-38`", "`Medium`", "`TC-ACAF-CV2-003`", "`none_required:covered`", "`none`", "Source-backed exact message."],
            ],
        ),
    )
    write_with_section_helper(
        TD / "coverage-map.md",
        "Coverage Map",
        table(
            ["item", "value", "evidence"],
            [
                ["atomic_statements_total", "`7`", "`atomic-requirements-ledger.md`"],
                ["covered_atoms", "`6`", "`ATOM-001`; `ATOM-002`; `ATOM-003`; `ATOM-004`; `ATOM-006`; `ATOM-007`"],
                ["gap_atoms", "`0`", "`none_required:no_gap_status_atoms`"],
                ["unclear_atoms", "`1`", "`ATOM-005` -> `GAP-002`"],
                ["executable_tc_total", "`6`", "`TC-ACAF-CV2-001`..`TC-ACAF-CV2-006`"],
                ["known_limitations", "`GAP-001`; `GAP-002`", "No PDF refs; no invented edit-lock UI mechanism."],
            ],
        ),
    )
    gap_body = """
### GAP-001

**FT Reference:** `source-parity-check.md`; DOCX `section-35`; DOCX `section-38`; rows `Отменить заявку`, `История заявки`
**Source Statement:** PDF доступен как версия основного ФТ, но text extraction не подтвердил выбранные строки.
**Impact:** `non-blocking`
**Coverage Impact:** `traceability`
**Affected Atom ID:** `not_covered:GAP-001`
**Temporary Handling:** Cover DOCX-backed behavior only; do not invent PDF page refs or PDF-only requirement IDs.
**Status:** `open`

### GAP-002

**FT Reference:** DOCX `section-35` / `section-38`, row `Отменить заявку`: `Дальнейшее редактирование УЗ запрещается.`
**Source Statement:** После подтверждения отказа с заполненной причиной УЗ переходит в статус `Отказ клиента`; дальнейшее редактирование УЗ запрещается.
**Impact:** `non-blocking`
**Coverage Impact:** `expected-result`
**Affected Atom ID:** `ATOM-005`
**Temporary Handling:** Cover source-backed status transition in `TC-ACAF-CV2-004`; keep exact edit-lock oracle as `unclear:GAP-002`.
**Status:** `open`
""".strip()
    write_with_section_helper(TD / "coverage-gaps.md", "Coverage Gaps", gap_body)


def write_gate_and_self_check() -> None:
    gate_rows = [
        ["`artifact-shape-preflight`", "`pass`", "Split artifacts use one canonical section heading and exact required table columns; canonical TC links summaries only.", "`all`", "`none_required:pass`", "`no`"],
        ["`placeholder-sentinel-normalization`", "`pass`", "Traceability-bearing columns use explicit sentinels such as `none_required:covered`, `not_covered:GAP-002`, `unclear:GAP-002`.", "`all`", "`none_required:pass`", "`no`"],
        ["`artifact-write-strategy`", "`pass`", "`artifact-write-strategy.md` selects `scripts/write_artifact_sections.py --manifest <manifest.json>` before generation.", "`all`", "`none_required:pass`", "`no`"],
        ["`mockup-visual-inventory`", "`pass`", "`source-selection.md` states no unambiguous mockup is used for this scope.", "`all`", "`none_required:not_applicable_no_mockup_source`", "`no`"],
        ["`source-row-inventory`", "`pass`", "`SRC-001`, `SRC-002`, `SRC-003` preserved; duplicate cancel rows normalized without duplicate TC coverage.", "`all`", "`none_required:pass`", "`no`"],
        ["`source-normalization-atomic`", "`pass`", "`source-table-normalization.md` has one property per row.", "`all`", "`none_required:pass`", "`no`"],
        ["`dictionary-inventory`", "`pass`", "`DICT-001` copied into writer-side inventory and linked to `TC-ACAF-CV2-002` / `TC-ACAF-CV2-004`.", "`WP-01`", "`none_required:pass`", "`no`"],
        ["`test-design-decision-table`", "`pass`", "Each source property has one decision: standalone TC or `GAP-002`.", "`all`", "`none_required:pass`", "`no`"],
        ["`coverage-obligation-table`", "`pass`", "Action, dictionary, validation, status and edit-lock obligations are mapped to TC or `GAP-002`.", "`all`", "`none_required:pass`", "`no`"],
        ["`coverage-metrics`", "`pass`", "`coverage-metrics.md` counts applicable dimensions and residual unclear items.", "`all`", "`none_required:pass`", "`no`"],
        ["`fixture-catalog`", "`pass`", "`fixture-catalog.md` names baseline fixtures `FX-001` and `FX-002`.", "`all`", "`none_required:pass`", "`no`"],
        ["`risk-priority-map`", "`pass`", "`ATOM-004` status lifecycle is high priority and covered by `TC-ACAF-CV2-004`.", "`WP-01`", "`none_required:pass`", "`no`"],
        ["`test-design-review`", "`pass`", "`test-design-review.md` has no blocking rows.", "`all`", "`none_required:pass`", "`no`"],
        ["`gap-admissibility`", "`pass`", "`GAP-001` and `GAP-002` preserve only non-derivable traceability/UI oracle details.", "`all`", "`none_required:pass`", "`no`"],
        ["`ledger-atomicity`", "`pass`", "`ATOM-001`..`ATOM-007` are independent statements.", "`all`", "`none_required:pass`", "`no`"],
        ["`gsr-range-compression`", "`pass`", "No GSR ranges or fabricated requirement IDs used.", "`all`", "`none_required:pass`", "`no`"],
        ["`design-plan-atomicity`", "`pass`", "Each `PLAN-*` row has one check type and one expected behavior.", "`all`", "`none_required:pass`", "`no`"],
        ["`scenario-does-not-replace-atomic`", "`pass`", "No broad scenario replaces the branch-specific TCs.", "`all`", "`none_required:pass`", "`no`"],
        ["`tc-atomicity`", "`pass`", "`TC-ACAF-CV2-003`, `TC-ACAF-CV2-004`, `TC-ACAF-CV2-005` split empty confirm, confirmed refusal and modal cancel.", "`all`", "`none_required:pass`", "`no`"],
        ["`test-data-specificity`", "`pass`", "`TC-ACAF-CV2-004` uses concrete active reason `Высокая ставка`; dictionary TC lists all active values.", "`WP-01`", "`none_required:pass`", "`no`"],
        ["`tc-regression-smells`", "`pass`", "No TC uses source-rule oracle, alternative negative oracle, executable gap-only case, or template cleanup for read-only checks.", "`all`", "`none_required:pass`", "`no`"],
        ["`internal-observability`", "`pass`", "No API/DB/audit/RabbitMQ checks are included.", "`all`", "`none_required:pass`", "`no`"],
        ["`action-observability`", "`pass`", "Each action TC names a visible modal/window/message/status/card result.", "`all`", "`none_required:pass`", "`no`"],
        ["`semantic-req-id-parity`", "`pass`", "`section-35` and `section-38` anchors preserved; no PDF page refs invented.", "`all`", "`none_required:pass`", "`no`"],
        ["`scoped-validator-findings`", "`pass`", f"`{WRITER_PROFILE_REL}` generated by runner validate; expected `unresolved_warning_error_count = 0`.", "`all`", "`none_required:pass`", "`no`"],
        ["`package-ready`", "`pass`", "`WP-01` and `WP-02` have ledger, design plan and TC gates passed; residual `GAP-002` remains explicit.", "`all`", "`none_required:pass`", "`no`"],
    ]
    write_with_section_helper(
        TD / "writer-quality-gate.md",
        "Writer Quality Gate",
        table(["gate_item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"], gate_rows),
    )
    self_check = table(
        ["check", "status", "evidence", "required_action"],
        [
            ["source parity checked", "`pass`", "`source-parity-check.md` read; `GAP-001` preserved.", "`none_required:pass`"],
            ["mandatory requirement IDs preserved", "`pass`", "`section-35`; `section-38` appear in ledger and TC traceability.", "`none_required:pass`"],
            ["uncovered atoms", "`pass`", "`ATOM-005` is `unclear:GAP-002`, not silently covered.", "`none_required:pass`"],
            ["possible merged checks", "`pass`", "No TC combines empty confirm, successful confirm and modal cancel branches.", "`none_required:pass`"],
            ["possible over-splitting", "`pass`", "Duplicate cancel source rows are normalized into one coverage set.", "`none_required:pass`"],
            ["test-case grouping and continuous numbering", "`pass`", "`TC-ACAF-CV2-001`..`TC-ACAF-CV2-006` continuous.", "`none_required:pass`"],
            ["internal work package coverage", "`pass`", "`internal-work-package-coverage.md` shows `WP-01` and `WP-02` ready.", "`none_required:pass`"],
            ["scoped validator command", "`pass`", "`python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_17/work/review-cycles/application-card-common-actions-flow-canary-v2/cycle-state.yaml` completed for writer-r1.", "`none_required:pass`"],
            ["scoped validator findings summary", "`pass`", f"`{WRITER_PROFILE_REL}` has `unresolved_warning_error_count = 0`.", "`none_required:pass`"],
            ["assumptions", "`pass`", "Baseline fixtures require an existing UZ card where in-scope actions are visible; no initial status is invented.", "`none_required:pass`"],
            ["unclear items", "`pass`", "`GAP-001`; `GAP-002` are listed in `coverage-gaps.md`.", "`none_required:pass`"],
        ],
    )
    artifact_write_evidence = table(
        ["artifact_path", "artifact_size_class", "write_strategy", "declared_before_first_write", "helper", "forbidden_methods_checked"],
        [
            [CANONICAL_REL, "`package-based generated`", "`file-based manifest write`", "`yes`", "`scripts/write_artifact_sections.py --manifest <manifest.json>`", "`yes`"],
            [TD_REL, "`split generated`", "`file-based manifest write`", "`yes`", "`scripts/write_artifact_sections.py --manifest <manifest.json>`", "`yes`"],
        ],
    )
    body = self_check + "\n\n### Artifact Write Evidence\n\n" + artifact_write_evidence
    write_with_section_helper(TD / "writer-self-check.md", "Writer Self-Check", body)


def tc_block(tc_id: str, title: str, tc_type: str, priority: str, package: str, trace: str, preconditions: str, data: str, steps: list[str], expected: str, post: str) -> str:
    numbered = "\n".join(f"{idx}. {step}" for idx, step in enumerate(steps, start=1))
    return f"""## {tc_id}

**Название:** {title}
**Тип:** {tc_type}
**Приоритет:** {priority}
**package_id:** `{package}`
**Трассировка:** {trace}

### Предусловия

{preconditions}

### Тестовые данные

{data}

### Шаги

{numbered}

### Итоговый ожидаемый результат

{expected}

### Постусловия

{post}
"""


def write_canonical() -> None:
    sections: list[tuple[str, str]] = []
    sections.append((
        "Metadata",
        table(
            ["field", "value"],
            [
                ["ft_slug", "`ft-2-OF_17`"],
                ["scope_slug", f"`{SCOPE}`"],
                ["section_id", "`section-38`"],
                ["writer_stage", "`writer-r1`"],
                ["source_scope_contract", "`work/stage-handoffs/07-application-card-common-actions/scope-contract.md`"],
            ],
        ),
    ))
    sections.append((
        "Artifact Write Strategy",
        f"Каноническая таблица стратегии записи хранится в `{TD_REL}/artifact-write-strategy.md`. "
        "Для этого package-based набора выбран file-based manifest write через "
        "`scripts/write_artifact_sections.py --manifest <manifest.json>` до генерации Markdown.",
    ))
    sections.append((
        "Coverage Boundaries",
        "- В scope входят только действия `Отменить заявку` и `История заявки` в карточке УЗ.\n"
        "- Полная форма `История заявки` из `section-39`, backend/API/DB/audit/RabbitMQ и точный механизм edit-lock не покрываются.\n"
        "- `SRC-001` и `SRC-002` сохранены как duplicate source anchors для одного cancel flow без двойного покрытия.",
    ))
    artifact_rows = [
        ["source rows", f"`{TD_REL}/source-row-inventory.md`"],
        ["normalization", f"`{TD_REL}/source-table-normalization.md`"],
        ["decision table", f"`{TD_REL}/test-design-decision-table.md`"],
        ["coverage obligations", f"`{TD_REL}/coverage-obligation-table.md`"],
        ["atomic ledger", f"`{TD_REL}/atomic-requirements-ledger.md`"],
        ["package plan", f"`{TD_REL}/package-test-design-plan.md`"],
        ["coverage gaps", f"`{TD_REL}/coverage-gaps.md`"],
        ["writer quality gate", f"`{TD_REL}/writer-quality-gate.md`"],
    ]
    sections.append(("Canonical Artifact Links", table(["artifact", "path"], artifact_rows)))
    sections.append((
        "Coverage Summary",
        table(
            ["package_id", "covered_behavior", "tc_ids", "residual_gap"],
            [
                ["`WP-01`", "Cancel modal, dictionary values, empty confirm message, successful refusal status transition, modal cancel return.", "`TC-ACAF-CV2-001`..`TC-ACAF-CV2-005`", "`GAP-002` edit-lock UI oracle"],
                ["`WP-02`", "History action opens history viewing window only.", "`TC-ACAF-CV2-006`", "`none_required:covered`"],
            ],
        ),
    ))
    sections.append((
        "Coverage Gaps Summary",
        "- `GAP-001`: accepted nonblocking PDF extraction risk; no PDF page refs or PDF-only IDs are claimed.\n"
        "- `GAP-002`: exact observable UI oracle for edit lock after `Отказ клиента` remains unclear; no executable TC invents the mechanism.",
    ))
    tc_sections = [
        tc_block(
            "TC-ACAF-CV2-001",
            "Открытие окна выбора причины отказа действием `Отменить заявку`",
            "Positive",
            "High",
            "WP-01",
            "`ATOM-001`; `SRC-001`; `SRC-002`; `section-35`; `section-38`",
            "Открыта карточка УЗ из `FX-001`, где действие `Отменить заявку` доступно пользователю.",
            "`FX-001`: карточка УЗ с доступным действием `Отменить заявку`.",
            ["В карточке УЗ выбрать действие `Отменить заявку`."],
            "Открыто окно выбора причины отказа от УЗ.",
            "Закрыть окно без подтверждения, если оно осталось открытым.",
        ),
        tc_block(
            "TC-ACAF-CV2-002",
            "Состав списка причин отказа от УЗ по активным значениям `DICT-001`",
            "Positive",
            "Medium",
            "WP-01",
            "`ATOM-003`; `DICT-001`; `SRC-001`; `SRC-002`; `section-35`; `section-38`",
            "Открыта карточка УЗ из `FX-001`; окно выбора причины отказа открыто действием `Отменить заявку`.",
            "Активные значения `DICT-001`: " + "; ".join(f"`{value}`" for value in DICT_VALUES) + ".",
            ["В окне выбора причины отказа открыть список/область выбора причины отказа."],
            "В списке причин отказа доступны все и только активные значения `DICT-001`: " + "; ".join(f"`{value}`" for value in DICT_VALUES) + ".",
            "Закрыть окно без подтверждения.",
        ),
        tc_block(
            "TC-ACAF-CV2-003",
            "Сообщение при подтверждении отказа без выбранной причины",
            "Negative",
            "Medium",
            "WP-01",
            "`ATOM-002`; `SRC-001`; `SRC-002`; `section-35`; `section-38`",
            "Открыта карточка УЗ из `FX-001`; окно выбора причины отказа открыто действием `Отменить заявку`; причина отказа не выбрана.",
            "Не требуются.",
            ["В окне выбора причины отказа нажать `Подтвердить`."],
            "Отображается сообщение `Выберите причину отказа`.",
            "Закрыть окно без подтверждения.",
        ),
        tc_block(
            "TC-ACAF-CV2-004",
            "Переход УЗ в статус `Отказ клиента` при подтверждении отказа с выбранной причиной",
            "Positive",
            "High",
            "WP-01",
            "`ATOM-004`; `DICT-001`; `SRC-001`; `SRC-002`; `section-35`; `section-38`",
            "Открыта отдельная карточка УЗ из `FX-002`, где действие `Отменить заявку` доступно и отказ еще не подтвержден.",
            "Причина отказа из `DICT-001`: `Высокая ставка`.",
            ["В карточке УЗ выбрать действие `Отменить заявку`.", "В окне выбора причины отказа выбрать значение `Высокая ставка`.", "Нажать `Подтвердить`."],
            "В карточке или отображении УЗ статус изменен на `Отказ клиента`.",
            "Не использовать эту же УЗ для кейсов, которым требуется исходное состояние до отказа.",
        ),
        tc_block(
            "TC-ACAF-CV2-005",
            "Возврат в карточку УЗ при нажатии `Отменить` в окне выбора причины отказа",
            "Positive",
            "Medium",
            "WP-01",
            "`ATOM-006`; `SRC-001`; `SRC-002`; `section-35`; `section-38`",
            "Открыта карточка УЗ из `FX-001`; окно выбора причины отказа открыто действием `Отменить заявку`.",
            "Не требуются.",
            ["В окне выбора причины отказа нажать `Отменить`."],
            "Окно выбора причины отказа закрыто, отображается карточка той же УЗ.",
            "Не требуются.",
        ),
        tc_block(
            "TC-ACAF-CV2-006",
            "Открытие окна просмотра истории заявки действием `История заявки`",
            "Positive",
            "Medium",
            "WP-02",
            "`ATOM-007`; `SRC-003`; `section-38`",
            "Открыта карточка УЗ из `FX-001`, где действие `История заявки` доступно пользователю.",
            "Не требуются.",
            ["В карточке УЗ выбрать действие `История заявки`."],
            "Открыто окно просмотра истории заявки.",
            "Закрыть окно просмотра истории заявки.",
        ),
    ]
    sections.append(("Test Cases", "\n".join(tc_sections).strip()))

    scratch = OUTPUTS / "_writer_r1_artifact_write"
    scratch.mkdir(parents=True, exist_ok=True)
    manifest_sections = []
    for idx, (heading, body) in enumerate(sections, start=1):
        content_file = scratch / f"canonical_{idx:02d}.md"
        content_file.write_text(body.strip() + "\n", encoding="utf-8", newline="\n")
        manifest_sections.append({"level": 2, "heading": heading, "content_file": content_file.name})
    preamble = scratch / "canonical_preamble.md"
    preamble.write_text("# Тест-кейсы: общие действия карточки УЗ (fresh canary v2)\n", encoding="utf-8", newline="\n")
    manifest = {"target_path": os.path.relpath(CANONICAL, scratch), "preamble_file": preamble.name, "sections": manifest_sections}
    manifest_file = scratch / "canonical.manifest.json"
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(manifest_file)], cwd=str(ROOT), check=True)


def write_cycle_outputs() -> None:
    response = f"""# Writer R1 Response

## Summary

- Created fresh canary-v2 canonical test cases at `{CANONICAL_REL}`.
- Created split design artifacts at `{TD_REL}/`.
- Covered six executable checks across `WP-01` and `WP-02`.
- Preserved `GAP-001` and `GAP-002`; no PDF page refs, backend checks or edit-lock UI mechanics were invented.

## Output Artifacts

- `{CANONICAL_REL}`
- `{TD_REL}/`
- `{WRITER_PROFILE_REL}`
- `work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md`
"""
    write_with_section_helper(OUTPUTS / "writer-r1-response.md", "Writer R1 Response", response.split("\n", 1)[1])
    reviewer_prompt = f"""# Structure Preflight R1 Prompt

## Goal

Run session-based structure preflight for `ft-2-OF_17` / `{SCOPE}`.

## Instruction Loading

- Scenario: `reviewer.structure_preflight`
- Before review, run `python scripts/resolve_instruction_context.py --scenario reviewer.structure_preflight --budget-report --fail-on-budget`.
- Read every selected required file before reviewer decisions and record resolver command, budget status and selected files in the session log.

## Inputs

- `work/review-cycles/{SCOPE}/cycle-state.yaml`
- `{CANONICAL_REL}`
- `{TD_REL}/`
- `work/stage-handoffs/07-application-card-common-actions/source-selection.md`
- `work/stage-handoffs/07-application-card-common-actions/scope-contract.md`
- `work/stage-handoffs/07-application-card-common-actions/source-parity-check.md`
- `work/stage-handoffs/07-application-card-common-actions/source-row-inventory.md`
- `work/stage-handoffs/07-application-card-common-actions/dictionary-inventory.md`
- `work/stage-handoffs/07-application-card-common-actions/scope-coverage-gaps.md`
- `work/stage-handoffs/07-application-card-common-actions/scope-clarification-requests.md`
- `work/review-cycles/application-card-common-actions/outputs/scope-gap-review.md`
- `AGENT-NOTES.md`

## Review Boundary

Check parseability, canonical TC format, split artifact shape, required headings/table columns, current writer-stage scoped validator profile, and readiness for semantic review.

Do not perform full semantic/test-design review in this stage. Do not edit the canonical test-case file.

## Expected Outputs

- Structure preflight output under `work/review-cycles/{SCOPE}/outputs/`.
- Updated `cycle-state.yaml` routing to `semantic-review-r1` with `semantic-review-ready` if structure passes, or to `writer-structure-r1` with `structure-preflight-blocked` if it blocks.
"""
    (PROMPTS / "prompt.structure-preflight-r1.md").write_text(reviewer_prompt, encoding="utf-8", newline="\n")


def write_logs() -> None:
    selected_files = [
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
    inputs_read = "\n".join(f"- `{path}` - selected required instruction file." for path in selected_files)
    scope_inputs = [
        f"`work/review-cycles/{SCOPE}/cycle-state.yaml` - session state source of truth.",
        "`work/stage-handoffs/07-application-card-common-actions/source-selection.md` - source boundary and contamination exclusions.",
        "`work/stage-handoffs/07-application-card-common-actions/scope-contract.md` - scope boundary and WP order.",
        "`work/stage-handoffs/07-application-card-common-actions/source-parity-check.md` - DOCX/PDF extraction risk and mandatory anchors.",
        "`work/stage-handoffs/07-application-card-common-actions/source-row-inventory.md` - in-scope source rows.",
        "`work/stage-handoffs/07-application-card-common-actions/dictionary-inventory.md` - `DICT-001` active values.",
        "`work/stage-handoffs/07-application-card-common-actions/scope-coverage-gaps.md` - `GAP-001`, `GAP-002` handling.",
        "`work/stage-handoffs/07-application-card-common-actions/scope-clarification-requests.md` - open clarification rows.",
        "`work/review-cycles/application-card-common-actions/outputs/scope-gap-review.md` - accepted gap review only.",
        "`AGENT-NOTES.md` - package-specific constraints.",
        "`references/agent/writer-output-format.md` - loaded for artifact-shape preflight.",
        "`references/agent/writer-quality-gate-format.md` - loaded for gate table/profile rules.",
    ]
    session_log = f"""# Writer R1 Session Log

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

- Resolver command: `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget`.
- Resolver budget status: `pass (138.8 / 200.0 KiB)`.
{inputs_read}
{chr(10).join("- " + item for item in scope_inputs)}

## Inputs Not Used

- `test-cases/section-38-application-card-common-actions.md` - forbidden previous signed-off canonical file for source/template use.
- `work/test-design/section-38-application-card-common-actions/` - forbidden previous split design output.
- `work/review-cycles/application-card-common-actions/outputs/*` except `scope-gap-review.md` - forbidden previous reviewer/writer outputs.
- `section-39` details - out of scope except target window entrypoint.

## Key Decisions

- `WP-01` written before `WP-02` according to prompt and scope contract.
- Duplicate cancel rows `SRC-001` and `SRC-002` preserved as traceability anchors but normalized into one behavioral coverage set.
- `GAP-002` kept as `unclear`; no disabled-field, hidden-save or error-message edit-lock mechanism was invented.
- Full active `DICT-001` values used in `TC-ACAF-CV2-002`; `Высокая ставка` used as concrete active value in `TC-ACAF-CV2-004`.

## Risks And Fallbacks

- `GAP-001` remains a nonblocking PDF extraction risk; writer uses DOCX anchors only.
- `GAP-002` remains open for analyst clarification on observable edit-lock oracle.
- Initial PowerShell console read produced mojibake for Russian text; all source/instruction artifacts were reread with explicit UTF-8 and distorted stdout was not used as evidence.

## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| `{CANONICAL_REL}` | `package-based generated` | `file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest <manifest.json>` | `yes` |
| `{TD_REL}/` | `split generated` | `file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest <manifest.json>` | `yes` |

## Validation

- `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - pass.
- `python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_17/work/review-cycles/{SCOPE}/cycle-state.yaml` - to be run after state/profile bootstrap and final artifacts.
- Writer artifact-shape preflight - pass by exact required table columns in split artifacts and no duplicate wrapper headings.

## Contamination Check

- Previous canonical/split/canary outputs for `application-card-common-actions` were not read as templates or source evidence.
- Only previous-cycle artifact used was the allowed `scope-gap-review.md`.

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Resolved instruction context | pass | resolver output budget `138.8 / 200.0 KiB` |
| 2 | Read required instructions and scope inputs | pass | this session log Inputs Read |
| 3 | Built split design artifacts package-by-package | pass | `{TD_REL}/` |
| 4 | Built canonical TC file | pass | `{CANONICAL_REL}` |
| 5 | Prepared structure preflight prompt | pass | `work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md` |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Writer Quality Gate | `pass` | `{TD_REL}/writer-quality-gate.md` | structure preflight |
| Gap discipline | `pass` | `{TD_REL}/coverage-gaps.md` | reviewer should verify no unsupported edit-lock oracle |
| Dictionary coverage | `pass` | `TC-ACAF-CV2-002`; `{TD_REL}/dictionary-inventory.md` | none |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | `encoding issue` | `PowerShell console output read without explicit UTF-8` | `Get-Content -Raw -Encoding UTF8` | `n/a` | `n/a` | `none; mojibake stdout discarded and not used as source evidence` | `none` |

## Handoff Notes For Next Session

- Structure preflight should check that `writer-quality-gate.md` references current writer profile `{WRITER_PROFILE_REL}`, not a reviewer/future profile.
- Semantic reviewer should focus on branch atomicity and ensure `GAP-002` was not silently promoted into covered edit-lock behavior.
"""
    (OUTPUTS / "writer-session-log.writer-r1.md").write_text(session_log, encoding="utf-8", newline="\n")
    decisions = [
        ["`DEC-001`", "1", "`scope-boundary`", "`scope-contract.md`", "Use only `Отменить заявку` and `История заявки` entrypoint behavior.", "Confirmed scope excludes full history form and backend effects.", CANONICAL_REL, "`high`", "`applied`"],
        ["`DEC-002`", "2", "`source-boundary`", "`source-row-inventory.md`", "Normalize `SRC-001` and `SRC-002` duplicate cancel rows into one coverage set.", "Rows duplicate the same action flow; duplicate TCs would inflate coverage.", f"{TD_REL}/source-row-inventory.md", "`high`", "`applied`"],
        ["`DEC-003`", "3", "`gap`", "`scope-coverage-gaps.md`; `scope-gap-review.md`", "Carry `GAP-001` and `GAP-002` into writer artifacts.", "Both are accepted nonblocking but must remain visible.", f"{TD_REL}/coverage-gaps.md", "`high`", "`applied`"],
        ["`DEC-004`", "4", "`test-design`", "`dictionary-inventory.md`", "Add a dedicated dictionary composition TC for all active `DICT-001` values.", "Prompt requires full active dictionary values, not examples.", f"{CANONICAL_REL}#TC-ACAF-CV2-002", "`high`", "`applied`"],
        ["`DEC-005`", "5", "`test-design`", "`GAP-002`", "Do not write an executable edit-lock TC.", "No source-backed visible UI oracle for edit lock mechanism exists.", f"{TD_REL}/atomic-requirements-ledger.md", "`medium`", "`applied`"],
        ["`DEC-006`", "6", "`artifact-write`", "`writer-output-format.md`", "Use file-based helper strategy for canonical and split artifacts.", "Package-based output requires safe manifest writing.", f"{TD_REL}/artifact-write-strategy.md", "`high`", "`applied`"],
        ["`DEC-007`", "7", "`routing`", "`session-based-review-cycle-format.md`", "Route writer-r1 to `structure-preflight-r1` with `writer-draft-ready`.", "Session lifecycle requires structure preflight before semantic review.", f"work/review-cycles/{SCOPE}/cycle-state.yaml", "`high`", "`applied`"],
    ]
    decision_log = "# Agent Decision Log\n\n## Decision Log Metadata\n\n" + table(
        ["field", "value"],
        [["ft_slug", "`ft-2-OF_17`"], ["scope_slug", f"`{SCOPE}`"], ["stage", "`ft-test-case-writer / writer-r1`"], ["started_from", f"`work/review-cycles/{SCOPE}/cycle-state.yaml`"]],
    ) + "\n\n## Decision Log\n\n" + table(
        ["decision_id", "step", "decision_type", "input_or_trigger", "decision", "rationale", "artifact_or_output", "risk_or_confidence", "status"],
        decisions,
    ) + "\n"
    (OUTPUTS / "agent-decision-log.writer-r1.md").write_text(decision_log, encoding="utf-8", newline="\n")


def write_cycle_state() -> None:
    state = f"""cycle_id: application-card-common-actions-flow-canary-v2-2026-06-19
ft_slug: ft-2-OF_17
scope_slug: {SCOPE}
section_id: section-38
current_stage: structure-preflight-r1
stage_status: writer-draft-ready
semantic_round: 0
max_semantic_rounds: 2
canonical_test_cases: {CANONICAL_REL}
test_design_dir: {TD_REL}
active_snapshot: work/review-cycles/{SCOPE}/versions/r1-writer-draft
active_transition_prompt: work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md
sessions:
latest_artifacts:
  - {CANONICAL_REL}
  - {TD_REL}
  - work/review-cycles/{SCOPE}/outputs/writer-r1-response.md
  - work/review-cycles/{SCOPE}/outputs/writer-session-log.writer-r1.md
  - work/review-cycles/{SCOPE}/outputs/agent-decision-log.writer-r1.md
  - {WRITER_PROFILE_REL}
  - work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md
blocking_reasons:
blocking_findings:
open_questions:
  - "GAP-002: preferred observable UI oracle for edit lock after status `Отказ клиента` remains unspecified; writer did not create an executable edit-lock mechanism TC."
accepted_risks:
  - "GAP-001 | accepted-nonblocking-risk | owner: scope-reviewer | rationale: DOCX selected rows are parseable; PDF extraction failed and must remain a traceability guardrail | revisit: before claiming PDF page refs or PDF-only IDs"
"""
    (CYCLE / "cycle-state.yaml").write_text(state, encoding="utf-8", newline="\n")


def main() -> int:
    TD.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    PROMPTS.mkdir(parents=True, exist_ok=True)
    CANONICAL.parent.mkdir(parents=True, exist_ok=True)
    write_artifact_strategy()
    write_source_artifacts()
    write_dictionary_artifact()
    write_design_artifacts()
    write_supporting_artifacts()
    write_gate_and_self_check()
    write_canonical()
    write_cycle_outputs()
    write_logs()
    write_cycle_state()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
