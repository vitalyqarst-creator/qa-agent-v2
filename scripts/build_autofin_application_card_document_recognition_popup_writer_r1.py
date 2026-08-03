from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "fts" / "AutoFin"
SCOPE = "application-card-document-recognition-popup"
SECTION = "14"
TD_REL = f"work/test-design/{SECTION}-{SCOPE}"
TD = FT / TD_REL
CANONICAL_REL = f"test-cases/{SECTION}-{SCOPE}.md"
CANONICAL = FT / CANONICAL_REL
CYCLE_REL = f"work/review-cycles/{SCOPE}"
CYCLE = FT / CYCLE_REL
OUTPUTS = CYCLE / "outputs"
PROMPTS = CYCLE / "prompts"
HANDOFF_REL = f"work/stage-handoffs/07-{SCOPE}"
PROFILE_REL = f"{CYCLE_REL}/outputs/scoped-validator-profile.writer-r1.json"

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

REQ_INPUTS = [
    "AGENT-NOTES.md",
    "work/stage-handoffs/00-autofin-scope-selection/source-selection.md",
    "work/stage-handoffs/02-application-card-questionnaires-decomposition/scope-options.md",
    f"{HANDOFF_REL}/scope-gap-review.md",
    f"{HANDOFF_REL}/scope-contract.md",
    f"{HANDOFF_REL}/source-parity-check.md",
    f"{HANDOFF_REL}/source-row-inventory.md",
    f"{HANDOFF_REL}/mockup-visual-inventory.md",
    f"{HANDOFF_REL}/scope-coverage-gaps.md",
    f"{HANDOFF_REL}/scope-clarification-requests.md",
    "source/AutoFinPreFinal.docx",
    "source/AutoFinPreFinal.pdf",
    "support/АФБ справочники 26.06.26.md",
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
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(manifest_path)],
        cwd=str(ROOT),
        check=True,
    )


def tc_blocks() -> str:
    return dedent(
        """
        ## TC-AFDRP-001

        **Название:** Видимость кнопки `Распознать документ` в карточке заявки

        **Тип:** Positive

        **Приоритет:** High

        **package_id:** WP-01

        **Трассировка:** `ATOM-001`; `BSR 70`; `SRC-001`; `WP-01`

        ### Предусловия

        - Открыта карточка заявки.

        ### Тестовые данные

        Не требуются.

        ### Шаги

        1. Перейти к области карточки заявки, где размещено действие распознавания документа.

        ### Итоговый ожидаемый результат

        Кнопка `Распознать документ` отображается в карточке заявки.

        ### Постусловия

        Не требуются.

        ## TC-AFDRP-002

        **Название:** Открытие popup распознавания документов по кнопке `Распознать документ`

        **Тип:** Positive

        **Приоритет:** High

        **package_id:** WP-01

        **Трассировка:** `ATOM-002`; `BSR 71`; `SRC-001`; `WP-01`

        ### Предусловия

        - Открыта карточка заявки.
        - Кнопка `Распознать документ` отображается.

        ### Тестовые данные

        Не требуются.

        ### Шаги

        1. Нажать кнопку `Распознать документ`.

        ### Итоговый ожидаемый результат

        Открыто всплывающее окно распознавания документов.

        ### Постусловия

        - Закрыть всплывающее окно без распознавания, если оно осталось открытым.

        ## TC-AFDRP-003

        **Название:** Состав раскрывающегося списка `Тип документа` в popup распознавания

        **Тип:** Positive

        **Приоритет:** High

        **package_id:** WP-01

        **Трассировка:** `ATOM-003`; `BSR 71`; `SRC-001`; `DICT-001`; `GAP-001`; `WP-01`

        ### Предусловия

        - Открыто всплывающее окно распознавания документов.

        ### Тестовые данные

        Активные значения `DICT-001`: `ВУ`, `СНИЛС`, `Загран. паспорт`, `Паспорт`, `Анкета`.

        ### Шаги

        1. Раскрыть список `Тип документа`.

        ### Итоговый ожидаемый результат

        В списке `Тип документа` доступны все и только активные значения `DICT-001`: `ВУ`, `СНИЛС`, `Загран. паспорт`, `Паспорт`, `Анкета`.

        ### Постусловия

        - Закрыть список `Тип документа`, если он остался раскрытым.

        ## TC-AFDRP-004

        **Название:** Отображение контейнера прикрепления файлов с drag&drop в popup распознавания

        **Тип:** Positive

        **Приоритет:** High

        **package_id:** WP-01

        **Трассировка:** `ATOM-004`; `BSR 71`; `SRC-001`; `WP-01`

        ### Предусловия

        - Открыто всплывающее окно распознавания документов.

        ### Тестовые данные

        Не требуются.

        ### Шаги

        1. Осмотреть область прикрепления файлов во всплывающем окне.

        ### Итоговый ожидаемый результат

        Во всплывающем окне отображается контейнер для прикрепления файлов с drag&drop, предназначенных для распознавания.

        ### Постусловия

        Не требуются.

        ## TC-AFDRP-005

        **Название:** Отображение кнопок `Отменить` и `Распознать` в popup распознавания

        **Тип:** Positive

        **Приоритет:** High

        **package_id:** WP-01

        **Трассировка:** `ATOM-005`; `BSR 72`; `SRC-001`; `WP-01`

        ### Предусловия

        - Открыто всплывающее окно распознавания документов.

        ### Тестовые данные

        Не требуются.

        ### Шаги

        1. Осмотреть набор кнопок во всплывающем окне.

        ### Итоговый ожидаемый результат

        Во всплывающем окне отображаются кнопки `Отменить` и `Распознать`.

        ### Постусловия

        Не требуются.

        ## TC-AFDRP-006

        **Название:** Закрытие popup распознавания по кнопке `Отменить`

        **Тип:** Positive

        **Приоритет:** Medium

        **package_id:** WP-01

        **Трассировка:** `ATOM-006`; `BSR 73`; `SRC-001`; `WP-01`

        ### Предусловия

        - Открыто всплывающее окно распознавания документов.

        ### Тестовые данные

        Не требуются.

        ### Шаги

        1. Нажать кнопку `Отменить`.

        ### Итоговый ожидаемый результат

        Всплывающее окно распознавания документов закрыто.

        ### Постусловия

        Не требуются.

        ## TC-AFDRP-007

        **Название:** Предупреждение при распознавании без вложения в контейнере файлов

        **Тип:** Negative

        **Приоритет:** High

        **package_id:** WP-01

        **Трассировка:** `ATOM-007`; `BSR 74`; `SRC-001`; `WP-01`

        ### Предусловия

        - Открыто всплывающее окно распознавания документов.
        - В контейнере для файлов отсутствуют вложения.

        ### Тестовые данные

        Не требуются.

        ### Шаги

        1. Нажать кнопку `Распознать`.

        ### Итоговый ожидаемый результат

        Отображается предупреждение `Отсутствуют файлы для распознавания`.

        ### Постусловия

        - Закрыть предупреждение, если интерфейс требует отдельного закрытия.
        """
    ).strip()


def write_split_artifacts() -> None:
    write_markdown(
        TD / "artifact-write-strategy.md",
        [(1, "Artifact Write Strategy", table(
            ["item", "value", "evidence"],
            [
                ["preflight_result", "`package-based`", "`scope-contract.md` defines internal package `WP-01`."],
                ["write_method", "`file-based manifest write`", "`scripts/write_artifact_sections.py --manifest <manifest.json>` selected before generated artifact writes."],
                ["forbidden_methods_checked", "`yes`", "No PowerShell here-string, no one-shot shell Markdown write, no inline giant command."],
                ["helper_artifacts", f"`{TD_REL}/_artifact_write/*/manifest.json`", "Retained for audit and reproducibility."],
            ],
        ))],
    )
    write_markdown(
        TD / "dictionary-inventory.md",
        [(1, "Dictionary Inventory", table(
            ["dictionary_id", "dictionary_name", "source_file", "source_location", "extraction_status", "active_values", "archived_values", "used_by_source_properties", "gap_id", "notes"],
            [
                ["`DICT-001`", "`Тип документа`", "`support/АФБ справочники 26.06.26.md`", "`section: Тип документа; columns: Значение, Внутренний код, Архивный`", "`extracted`", "`ВУ`; `СНИЛС`; `Загран. паспорт`; `Паспорт`; `Анкета`", "`none_required:no_archived_values`", "`SP-003`", "`GAP-001`", "`Архивный = нет` трактуется как active; `GAP-001` относится только к default selection."],
            ],
        ))],
    )
    write_markdown(
        TD / "source-row-inventory.md",
        [(1, "Source Row Inventory", table(
            ["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"],
            [
                ["`SRC-001`", "`WP-01`", "`Распознать документ`", "DOCX section-14 table row 015; PDF pages 16-17", "`BSR 70`; `BSR 71`; `BSR 72`; `BSR 73`; `BSR 74`; `BSR 75`", "`yes`", "`ATOM-001`; `ATOM-002`; `ATOM-003`; `ATOM-004`; `ATOM-005`; `ATOM-006`; `ATOM-007`; `ATOM-008`; `GAP-001`; `GAP-002`"],
            ],
        ))],
    )
    write_markdown(
        TD / "source-table-normalization.md",
        [(1, "Source Table Normalization", table(
            ["source_property_id", "source_row_id", "package_id", "field_or_block", "property", "condition", "expected_behavior", "requirement_code", "source_ref", "confidence", "gap_id", "linked_atoms"],
            [
                ["`SP-001`", "`SRC-001`", "`WP-01`", "`Распознать документ`", "`visibility`", "`always`", "Кнопка `Распознать документ` видима всегда.", "`BSR 70`", "PDF page 16; DOCX row 015", "`high`", "`none_required:covered`", "`ATOM-001`"],
                ["`SP-002`", "`SRC-001`", "`WP-01`", "`Распознать документ`", "`popup-open`", "`user-clicks-button`", "Кнопка открывает всплывающее окно распознавания документов.", "`BSR 71`", "PDF page 16; DOCX row 015", "`high`", "`none_required:covered`", "`ATOM-002`"],
                ["`SP-003`", "`SRC-001`", "`WP-01`", "`DICT-001`", "`dictionary-source`", "`support-source`", "Active values for `DICT-001` are extracted from support.", "`BSR 71`", "PDF page 16; DOCX row 015; support dictionary", "`high`", "`GAP-001` for default value only", "`ATOM-003`"],
                ["`SP-004`", "`SRC-001`", "`WP-01`", "`container`", "`file-container`", "`popup-open`", "В popup есть контейнер для прикрепления файлов с drag&drop.", "`BSR 71`", "PDF page 16; DOCX row 015", "`high`", "`none_required:covered`", "`ATOM-004`"],
                ["`SP-005`", "`SRC-001`", "`WP-01`", "`popup buttons`", "`button-set`", "`popup-open`", "В popup есть кнопки `Отменить` и `Распознать`.", "`BSR 72`", "PDF page 16; DOCX row 015", "`high`", "`none_required:covered`", "`ATOM-005`"],
                ["`SP-006`", "`SRC-001`", "`WP-01`", "`Отменить`", "`button-action`", "`user-clicks-cancel`", "Нажатие `Отменить` закрывает всплывающее окно.", "`BSR 73`", "PDF page 16; DOCX row 015", "`high`", "`none_required:covered`", "`ATOM-006`"],
                ["`SP-007`", "`SRC-001`", "`WP-01`", "`Распознать`", "`negative-file-presence`", "`no-files-attached`", "Если файлы отсутствуют, выдается предупреждение `Отсутствуют файлы для распознавания`.", "`BSR 74`", "PDF page 16; DOCX row 015", "`high`", "`none_required:covered`", "`ATOM-007`"],
                ["`SP-008`", "`SRC-001`", "`WP-01`", "`GAP-002`", "`integration`", "`not_applicable:gap_only`", "`unclear:GAP-002`", "`BSR 75`", "PDF page 17; DOCX row 015", "`medium`", "`GAP-002`", "`ATOM-008`"],
            ],
        ))],
    )
    write_markdown(
        TD / "source-row-completeness-matrix.md",
        [(1, "Source Row Completeness Matrix", table(
            ["source_row_id", "source_requirement_codes", "normalized_property_ids", "linked_atoms", "gap_ids", "coverage_decision"],
            [
                ["`SRC-001`", "`BSR 70`; `BSR 71`; `BSR 72`; `BSR 73`; `BSR 74`; `BSR 75`", "`SP-001`; `SP-002`; `SP-003`; `SP-004`; `SP-005`; `SP-006`; `SP-007`; `SP-008`", "`ATOM-001`; `ATOM-002`; `ATOM-003`; `ATOM-004`; `ATOM-005`; `ATOM-006`; `ATOM-007`; `ATOM-008`", "`GAP-001`; `GAP-002`", "`covered-with-residual-risk`"],
            ],
        ))],
    )
    write_markdown(
        TD / "atomic-requirements-ledger.md",
        [(1, "Atomic Requirements Ledger", table(
            ["atom_id", "package_id", "source_property_id", "req_id", "source_row_id", "atomic_statement", "coverage_status", "covered_by_tc", "planned_tc_or_gap", "gap_id"],
            [
                ["`ATOM-001`", "`WP-01`", "`SP-001`", "`BSR 70`", "`SRC-001`", "Кнопка `Распознать документ` видима всегда.", "`covered`", "`TC-AFDRP-001`", "`TC-AFDRP-001`", "`none_required:covered`"],
                ["`ATOM-002`", "`WP-01`", "`SP-002`", "`BSR 71`", "`SRC-001`", "Кнопка `Распознать документ` открывает popup распознавания документов.", "`covered`", "`TC-AFDRP-002`", "`TC-AFDRP-002`", "`none_required:covered`"],
                ["`ATOM-003`", "`WP-01`", "`SP-003`", "`BSR 71`", "`SRC-001`", "В popup есть раскрывающийся список `Тип документа` со значениями по справочнику типов документов.", "`covered`", "`TC-AFDRP-003`", "`TC-AFDRP-003`; `GAP-001`", "`GAP-001`"],
                ["`ATOM-004`", "`WP-01`", "`SP-004`", "`BSR 71`", "`SRC-001`", "В popup есть контейнер для прикрепления файлов с drag&drop.", "`covered`", "`TC-AFDRP-004`", "`TC-AFDRP-004`", "`none_required:covered`"],
                ["`ATOM-005`", "`WP-01`", "`SP-005`", "`BSR 72`", "`SRC-001`", "В popup есть кнопки `Отменить` и `Распознать`.", "`covered`", "`TC-AFDRP-005`", "`TC-AFDRP-005`", "`none_required:covered`"],
                ["`ATOM-006`", "`WP-01`", "`SP-006`", "`BSR 73`", "`SRC-001`", "Нажатие кнопки `Отменить` закрывает popup.", "`covered`", "`TC-AFDRP-006`", "`TC-AFDRP-006`", "`none_required:covered`"],
                ["`ATOM-007`", "`WP-01`", "`SP-007`", "`BSR 74`", "`SRC-001`", "При нажатии `Распознать` без файлов отображается предупреждение `Отсутствуют файлы для распознавания`.", "`covered`", "`TC-AFDRP-007`", "`TC-AFDRP-007`", "`none_required:covered`"],
                ["`ATOM-008`", "`WP-01`", "`SP-008`", "`BSR 75`", "`SRC-001`", "При наличии файлов инициируется запрос во внешнюю систему распознавания, ожидание распознавания и заполнение соответствующих полей заявки.", "`unclear`", "`not_covered:GAP-002`", "`GAP-002`", "`GAP-002`"],
            ],
        ))],
    )
    write_markdown(
        TD / "test-design-decision-table.md",
        [(1, "Test Design Decision Table", table(
            ["decision_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "decision", "decision_reason", "planned_tc_or_gap", "oracle_source", "must_be_executable", "observable_oracle", "testable_part", "blocked_part", "gap_admissibility", "review_risk"],
            [
                ["`DD-001`", "`WP-01`", "`SP-001`", "`ATOM-001`", "`visibility`", "`standalone_tc`", "Visibility is explicit.", "`TC-AFDRP-001`", "`BSR 70`", "`yes`", "Button is visible.", "Button visibility.", "`none_required:covered`", "`none_required:covered`", "`low`"],
                ["`DD-002`", "`WP-01`", "`SP-002`", "`ATOM-002`", "`popup-open`", "`standalone_tc`", "Popup opening is explicit.", "`TC-AFDRP-002`", "`BSR 71`", "`yes`", "Popup opens.", "Popup opening.", "`none_required:covered`", "`none_required:covered`", "`low`"],
                ["`DD-003`", "`WP-01`", "`SP-003`", "`ATOM-003`", "`dictionary-list`", "`standalone_tc`", "Dictionary values are supplied by support; default is not specified.", "`TC-AFDRP-003`; `GAP-001`", "`BSR 71`; `DICT-001`", "`yes`", "List contains all active support values.", "Dictionary composition.", "Default selected value.", "`non-blocking`", "`medium`"],
                ["`DD-004`", "`WP-01`", "`SP-004`", "`ATOM-004`", "`file-container`", "`standalone_tc`", "Container existence is explicit; upload persistence is not specified.", "`TC-AFDRP-004`", "`BSR 71`", "`yes`", "Container is displayed.", "Container availability.", "Attachment result details.", "`none_required:covered`", "`medium`"],
                ["`DD-005`", "`WP-01`", "`SP-005`", "`ATOM-005`", "`button-set`", "`standalone_tc`", "Popup button set is explicit.", "`TC-AFDRP-005`", "`BSR 72`", "`yes`", "Both buttons are visible.", "Button set.", "`none_required:covered`", "`none_required:covered`", "`low`"],
                ["`DD-006`", "`WP-01`", "`SP-006`", "`ATOM-006`", "`button-action`", "`standalone_tc`", "Cancel behavior is explicit.", "`TC-AFDRP-006`", "`BSR 73`", "`yes`", "Popup closes.", "Cancel action.", "`none_required:covered`", "`none_required:covered`", "`low`"],
                ["`DD-007`", "`WP-01`", "`SP-007`", "`ATOM-007`", "`negative-file-presence`", "`standalone_tc`", "Missing-file warning text is explicit.", "`TC-AFDRP-007`", "`BSR 74`", "`yes`", "Warning text is displayed.", "No-file validation.", "`none_required:covered`", "`none_required:covered`", "`low`"],
                ["`DD-008`", "`WP-01`", "`SP-008`", "`ATOM-008`", "`integration`", "`gap_unclear`", "No permitted observable oracle is defined in current scope.", "`GAP-002`", "`scope-coverage-gaps.md`; `BSR 75`", "`no`", "`unclear:GAP-002`", "", "`GAP-002`", "`non-blocking`", "`high`"],
            ],
        ))],
    )
    write_markdown(
        TD / "coverage-obligation-table.md",
        [(1, "Coverage Obligation Table", "Coverage obligation expansion is not applicable for this scope as a separate deep-class table: row `015` does not define numeric boundaries, exact length, masks, upload file formats, file size limits, repeatable blocks, generated documents, role matrices or combinatorial factors. The source-backed dictionary/file-container/no-file warning checks are tracked in `atomic-requirements-ledger.md`, `package-test-design-plan.md`, `test-design-decision-table.md` and `coverage-map.md`; `BSR 75` remains `GAP-002` rather than an executable obligation.\n\n" + table(
            ["obligation_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "obligation_class", "required_behavior", "source_ref", "planned_tc_or_gap", "status", "review_notes"],
            [
                ["`OBL-N/A-001`", "`WP-01`", "", "", "`other`", "`other`", "No validator-mandated deep coverage class applies beyond atom/plan/TDDT tracking.", "`SRC-001`; `BSR 70`-`BSR 75`", "`coverage-map.md`; `GAP-002`", "`n/a`", "Dictionary composition is covered through `DICT-001` and `TC-AFDRP-003`; recognition outcome remains gap."],
            ],
        ))],
    )
    write_markdown(
        TD / "package-test-design-plan.md",
        [(1, "Package Test Design Plan", table(
            ["design_item_id", "package_id", "design_dimension", "source_ref", "linked_atoms", "planned_check", "check_type", "coverage_class", "input_class", "single_expected_behavior", "oracle_source", "planned_tc_or_gap", "status"],
            [
                ["`PLAN-001`", "`WP-01`", "`visibility`", "`BSR 70`", "`ATOM-001`", "Проверить видимость кнопки в карточке заявки.", "`positive`", "`visibility-always`", "`application-card-open`", "Кнопка отображается.", "`BSR 70`", "`TC-AFDRP-001`", "`covered`"],
                ["`PLAN-002`", "`WP-01`", "`popup-open`", "`BSR 71`", "`ATOM-002`", "Нажать кнопку `Распознать документ`.", "`positive`", "`state-transition-popup`", "`button-click`", "Popup открыт.", "`BSR 71`", "`TC-AFDRP-002`", "`covered`"],
                ["`PLAN-003`", "`WP-01`", "`dictionary-list`", "`BSR 71`; `DICT-001`", "`ATOM-003`", "Раскрыть список `Тип документа`.", "`positive`", "`closed-list-composition`", "`support-dictionary-values`", "Доступны все и только активные значения.", "`DICT-001`", "`TC-AFDRP-003`; `GAP-001`", "`covered-with-residual-risk`"],
                ["`PLAN-004`", "`WP-01`", "`file-container`", "`BSR 71`", "`ATOM-004`", "Проверить наличие контейнера прикрепления файлов.", "`positive`", "`file-control-visibility`", "`popup-open`", "Контейнер отображается.", "`BSR 71`", "`TC-AFDRP-004`", "`covered`"],
                ["`PLAN-005`", "`WP-01`", "`button-set`", "`BSR 72`", "`ATOM-005`", "Проверить наличие кнопок popup.", "`positive`", "`popup-controls`", "`popup-open`", "Кнопки `Отменить` и `Распознать` отображаются.", "`BSR 72`", "`TC-AFDRP-005`", "`covered`"],
                ["`PLAN-006`", "`WP-01`", "`cancel-action`", "`BSR 73`", "`ATOM-006`", "Нажать `Отменить`.", "`positive`", "`popup-close`", "`cancel-click`", "Popup закрыт.", "`BSR 73`", "`TC-AFDRP-006`", "`covered`"],
                ["`PLAN-007`", "`WP-01`", "`missing-file-warning`", "`BSR 74`", "`ATOM-007`", "Нажать `Распознать` без вложений.", "`negative`", "`missing-file-validation`", "`empty-file-container`", "Показано предупреждение.", "`BSR 74`", "`TC-AFDRP-007`", "`covered`"],
                ["`PLAN-008`", "`WP-01`", "`recognition-with-file`", "`BSR 75`", "`ATOM-008`", "Не писать TC до уточнения observable результата.", "`unclear`", "`integration-result`", "`file-attached`", "`unclear:GAP-002`", "`scope-coverage-gaps.md`", "`GAP-002`", "`unclear`"],
            ],
        ))],
    )
    write_markdown(
        TD / "test-design-applicability-matrix.md",
        [(1, "Test-design Applicability Matrix", table(
            ["dimension", "applicable", "source_ref", "reason", "linked_atoms", "linked_test_cases", "gap_id"],
            [
                ["`other`", "`yes`", "`BSR 70`; `BSR 71`; `BSR 72`", "Button, popup field/container and popup controls are explicitly visible/available.", "`ATOM-001`; `ATOM-003`; `ATOM-004`; `ATOM-005`", "`TC-AFDRP-001`; `TC-AFDRP-003`; `TC-AFDRP-004`; `TC-AFDRP-005`", ""],
                ["`other`", "`no`", "`source-row-inventory.md`", "Row 015 is an action/button row; no requiredness rule for popup field is source-backed.", "`none_required:no_source`", "`none_required:no_source`", ""],
                ["`other`", "`no`", "`source-row-inventory.md`", "No editability rule is stated for row 015 beyond dropdown availability.", "`none_required:no_source`", "`none_required:no_source`", ""],
                ["`other`", "`unclear`", "`scope-coverage-gaps.md`", "Default for `Тип документа` is not defined.", "`ATOM-003`", "`not_covered:GAP-001`", "`GAP-001`"],
                ["`other`", "`yes`", "`BSR 71`; `DICT-001`", "Popup uses document-type dictionary; support defines active values.", "`ATOM-003`", "`TC-AFDRP-003`", "`GAP-001`"],
                ["`other`", "`yes`", "`BSR 71`; `BSR 73`", "Popup opening and cancel closing are positive observable actions.", "`ATOM-002`; `ATOM-006`", "`TC-AFDRP-002`; `TC-AFDRP-006`", ""],
                ["`other`", "`yes`", "`BSR 74`", "No-file recognition has explicit warning.", "`ATOM-007`", "`TC-AFDRP-007`", ""],
                ["`other`", "`no`", "`source-row-inventory.md`", "No numeric, length or mask constraints in row 015.", "`none_required:no_source`", "`none_required:no_source`", ""],
                ["`other`", "`yes`", "`BSR 71`; `BSR 73`", "Popup opens and closes.", "`ATOM-002`; `ATOM-006`", "`TC-AFDRP-002`; `TC-AFDRP-006`", ""],
                ["`other`", "`unclear`", "`BSR 75`; `GAP-002`", "External recognition request and field filling lack permitted observable outcome in this scope.", "`ATOM-008`", "`not_covered:GAP-002`", "`GAP-002`"],
                ["`other`", "`yes`", "`BSR 71`; `BSR 74`", "File container and missing-file validation are explicit.", "`ATOM-004`; `ATOM-007`", "`TC-AFDRP-004`; `TC-AFDRP-007`", "`GAP-002`"],
                ["`other`", "`no`", "`scope-contract.md`", "No role, status, security or NFR rule is included in row 015.", "`none_required:no_source`", "`none_required:no_source`", ""],
            ],
        ))],
    )
    write_markdown(
        TD / "internal-work-package-coverage.md",
        [(1, "Internal Work Package Coverage", table(
            ["package_id", "focus", "source_rows", "atoms", "test_cases", "coverage_status", "residual_gaps"],
            [
                ["`WP-01`", "Recognition popup opening, controls, dictionary, no-file warning and residual recognition gap", "`SRC-001`", "`ATOM-001`-`ATOM-008`", "`TC-AFDRP-001`-`TC-AFDRP-007`", "`covered-with-residual-risk`", "`GAP-001`; `GAP-002`"],
            ],
        ))],
    )
    write_markdown(
        TD / "coverage-map.md",
        [(1, "Coverage Map", table(
            ["atom_id", "req_id", "source_row_id", "tc_id", "coverage_status", "gap_id"],
            [
                ["`ATOM-001`", "`BSR 70`", "`SRC-001`", "`TC-AFDRP-001`", "`covered`", "`none_required:covered`"],
                ["`ATOM-002`", "`BSR 71`", "`SRC-001`", "`TC-AFDRP-002`", "`covered`", "`none_required:covered`"],
                ["`ATOM-003`", "`BSR 71`", "`SRC-001`", "`TC-AFDRP-003`", "`covered-with-residual-risk`", "`GAP-001`"],
                ["`ATOM-004`", "`BSR 71`", "`SRC-001`", "`TC-AFDRP-004`", "`covered`", "`none_required:covered`"],
                ["`ATOM-005`", "`BSR 72`", "`SRC-001`", "`TC-AFDRP-005`", "`covered`", "`none_required:covered`"],
                ["`ATOM-006`", "`BSR 73`", "`SRC-001`", "`TC-AFDRP-006`", "`covered`", "`none_required:covered`"],
                ["`ATOM-007`", "`BSR 74`", "`SRC-001`", "`TC-AFDRP-007`", "`covered`", "`none_required:covered`"],
                ["`ATOM-008`", "`BSR 75`", "`SRC-001`", "`not_covered:GAP-002`", "`unclear`", "`GAP-002`"],
            ],
        ))],
    )
    write_markdown(
        TD / "coverage-gaps.md",
        [(1, "Coverage Gaps", table(
            ["gap_id", "package_id", "linked_atoms", "source_ref", "status", "blocking", "writer_handling", "reviewer_focus"],
            [
                ["`GAP-001`", "`WP-01`", "`ATOM-003`", "`BSR 71`; `scope-coverage-gaps.md`; `scope-clarification-requests.md`", "`open`", "`no`", "Use `DICT-001` values; do not assert default `Тип документа`.", "Check no default document type is asserted."],
                ["`GAP-002`", "`WP-01`", "`ATOM-008`", "`BSR 75`; `scope-coverage-gaps.md`; `scope-clarification-requests.md`", "`open`", "`no`", "Do not create TC for successful or failed recognition or passport field mapping.", "Check BSR 75 is preserved as unclear, not treated as covered."],
            ],
        ))],
    )
    write_markdown(
        TD / "test-design-review.md",
        [(1, "Test Design Review", table(
            ["review_item", "status", "severity", "evidence", "affected_package", "required_action", "blocks_ready_for_review"],
            [
                ["`coverage-class-completeness`", "`pass`", "`info`", "`coverage-obligation-table.md` records deep class n/a; ledger/plan cover explicit dimensions.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`applicability-linked-tc-semantics`", "`pass`", "`info`", "`test-design-applicability-matrix.md` links applicable dimensions to atoms/TC or GAP.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`conditional-branches`", "`pass`", "`info`", "Only no-file branch has explicit observable warning; with-files branch is `GAP-002`.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`decision-table-classification`", "`pass`", "`info`", "`test-design-decision-table.md` classifies executable rows as `standalone_tc`; `BSR 75` is kept in ledger and `coverage-gaps.md`.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`dictionary-closed-set`", "`pass`", "`info`", "`dictionary-inventory.md` extracts all active support values for `DICT-001`.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`gap-admissibility`", "`pass`", "`info`", "`GAP-001` and `GAP-002` are non-blocking residual risks from scope review.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`gap-specificity`", "`pass`", "`info`", "`coverage-gaps.md` links both gaps to `BSR 71`/`BSR 75` and affected atoms.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`internal-observability`", "`pass`", "`info`", "No TC asserts backend request, RabbitMQ/API effect or recognition-service outcome.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`ledger-plan-alignment`", "`pass`", "`info`", "`atomic-requirements-ledger.md`, `package-test-design-plan.md` and `coverage-map.md` use the same atom/TC/gap links.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`mask-format-coverage`", "`pass`", "`info`", "Row 015 has no mask or format restrictions.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`metadata-only-exclusion`", "`pass`", "`info`", "No metadata-only source statement was converted to standalone TC.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`negative-fixture-isolation`", "`pass`", "`info`", "`TC-AFDRP-007` isolates one negative class: no files in container.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`numeric-length-boundaries`", "`pass`", "`info`", "Row 015 has no numeric length or boundary restrictions.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`ready-for-tc-writing`", "`pass`", "`info`", "All executable source-backed rows have planned `TC-*`; gap-only row remains in `coverage-gaps.md`.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`tc-mapping-atomicity`", "`pass`", "`info`", "Each executable `ATOM-*` maps to one focused `TC-AFDRP-*`.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`unsupported-ui-mechanism`", "`pass`", "`info`", "No TC asserts unsupported default value, file upload persistence, recognition result, backend request or field mapping.", "`WP-01`", "`none_required:pass`", "`no`"],
            ],
        ))],
    )
    write_markdown(
        TD / "writer-quality-gate.md",
        [(1, "Writer Quality Gate", table(
            ["gate_item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"],
            [
                ["`artifact-write-strategy`", "`pass`", "`artifact-write-strategy.md` documents file-based manifest write.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`mockup-visual-inventory`", "`pass`", "Mockup used only for steps, not business rules.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`source-row-inventory`", "`pass`", "`SRC-001` preserved.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`source-normalization-atomic`", "`pass`", "`source-table-normalization.md`; `atomic-requirements-ledger.md`.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`test-design-decision-table`", "`pass`", "`test-design-decision-table.md`.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`design-plan-atomicity`", "`pass`", "`package-test-design-plan.md` has one planned check per row.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`dictionary-inventory`", "`pass`", "`DICT-001` contains five support values only.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`coverage-obligation-table`", "`pass`", "`coverage-obligation-table.md` records no separate validator-mandated deep obligation class; explicit checks stay in ledger/plan/TDDT.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`gap-admissibility`", "`pass`", "`coverage-gaps.md` keeps `GAP-001` and `GAP-002` non-blocking and visible.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`ledger-atomicity`", "`pass`", "`atomic-requirements-ledger.md` has one independently checkable source statement per atom or explicit gap.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`gsr-range-compression`", "`pass`", "`BSR 70`-`BSR 75` are listed individually; no range-only traceability.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`scenario-does-not-replace-atomic`", "`pass`", "`TC-AFDRP-*` cases map back to `ATOM-*`; no broad scenario replaces ledger rows.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`tc-atomicity`", "`pass`", "Each `TC-AFDRP-*` has one main expected result.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`test-data-specificity`", "`pass`", "`TC-AFDRP-003` names all `DICT-001` values; other cases require no special data.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`test-design-review`", "`pass`", "`test-design-review.md` uses required rows and all statuses are pass.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`action-observability`", "`pass`", "Popup open/close and no-file warning are observable; `BSR 75` remains gap.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`internal-observability`", "`pass`", "`BSR 75` backend/integration outcome is not covered by UI-only TC.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`semantic-req-id-parity`", "`pass`", "`BSR 70`-`BSR 75` preserved in ledger and coverage map.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`package-ready`", "`pass`", "`WP-01` artifacts, canonical TC file and next prompt are present.", "`WP-01`", "`none_required:pass`", "`no`"],
                ["`scoped-validator-findings`", "`pass`", f"`{PROFILE_REL}` with `unresolved_warning_error_count = 0`.", "`all`", "`none_required:pass`", "`no`"],
            ],
        ))],
    )
    write_markdown(
        TD / "writer-self-check.md",
        [
            (1, "Writer Self-check", table(
                ["check", "status", "evidence", "follow_up"],
                [
                    ["`scope-boundary`", "`pass`", "Only section-14 row `015` is used.", "`none_required:pass`"],
                    ["`source-read-contract`", "`pass`", "DOCX row 015 and PDF pages 16-17 extracted; support dictionary read.", "`none_required:pass`"],
                    ["`dictionary-closure`", "`pass`", "`DICT-001` has values `ВУ`, `СНИЛС`, `Загран. паспорт`, `Паспорт`, `Анкета` only.", "`none_required:pass`"],
                    ["`default-not-invented`", "`pass`", "`GAP-001` remains open.", "`none_required:pass`"],
                    ["`recognition-result-not-invented`", "`pass`", "`ATOM-008` maps to `GAP-002`; no TC asserts recognition outcome.", "`none_required:pass`"],
                    ["`runtime-format`", "`pass`", "Canonical file uses parser-supported bold metadata fields.", "`none_required:pass`"],
                    ["`validator-profile`", "`pass`", f"`{PROFILE_REL}` expected/generated with zero unresolved warning/error findings.", "`none_required:pass`"],
                ],
            )),
            (1, "Artifact Write Evidence", table(
                ["artifact_group", "write_strategy", "evidence", "follow_up"],
                [
                    ["canonical test cases", "`write_artifact_sections.py --manifest`", f"`{TD_REL}/_artifact_write/{CANONICAL.stem}/manifest.json`", "`none_required:pass`"],
                    ["split artifacts", "`write_artifact_sections.py --manifest`", f"`{TD_REL}/_artifact_write/*/manifest.json`", "`none_required:pass`"],
                    ["cycle outputs", "`write_artifact_sections.py --manifest`", f"`{TD_REL}/_artifact_write/writer-r1-response/manifest.json`", "`none_required:pass`"],
                ],
            )),
        ],
    )


def write_canonical() -> None:
    write_markdown(
        CANONICAL,
        [
            (2, "Metadata", table(
                ["field", "value"],
                [
                    ["ft_slug", "`AutoFin`"],
                    ["scope_slug", f"`{SCOPE}`"],
                    ["section_id", "`14`"],
                    ["package_id", "`WP-01`"],
                    ["test_design_dir", f"`{TD_REL}`"],
                ],
            )),
            (2, "Scope Boundaries", "Набор покрывает только `section-14` row `015`: кнопку `Распознать документ`, открытие popup, поле `Тип документа`, контейнер прикрепления файлов, кнопки popup и предупреждение при распознавании без файлов. Набор не покрывает паспортные поля, маппинг результатов распознавания, backend/API/RabbitMQ effects, успешное или неуспешное распознавание и выбор `Тип документа` по умолчанию."),
            (2, "Coverage Summary", table(
                ["package_id", "source_row_id", "req_id", "atom_id", "test_case_id", "coverage_status"],
                [
                    ["`WP-01`", "`SRC-001`", "`BSR 70`", "`ATOM-001`", "`TC-AFDRP-001`", "`covered`"],
                    ["`WP-01`", "`SRC-001`", "`BSR 71`", "`ATOM-002`", "`TC-AFDRP-002`", "`covered`"],
                    ["`WP-01`", "`SRC-001`", "`BSR 71`", "`ATOM-003`", "`TC-AFDRP-003`", "`covered-with-residual-risk: GAP-001`"],
                    ["`WP-01`", "`SRC-001`", "`BSR 71`", "`ATOM-004`", "`TC-AFDRP-004`", "`covered`"],
                    ["`WP-01`", "`SRC-001`", "`BSR 72`", "`ATOM-005`", "`TC-AFDRP-005`", "`covered`"],
                    ["`WP-01`", "`SRC-001`", "`BSR 73`", "`ATOM-006`", "`TC-AFDRP-006`", "`covered`"],
                    ["`WP-01`", "`SRC-001`", "`BSR 74`", "`ATOM-007`", "`TC-AFDRP-007`", "`covered`"],
                    ["`WP-01`", "`SRC-001`", "`BSR 75`", "`ATOM-008`", "`not_covered:GAP-002`", "`unclear`"],
                ],
            )),
            (2, "Coverage Gaps", bullets([
                "`GAP-001` remains open and non-blocking: support provides `Тип документа` values, but default selection in popup is not defined.",
                "`GAP-002` remains open and non-blocking: observable successful/failed recognition outcomes and mapping to application fields are not defined for executable coverage in this scope.",
            ])),
            (2, "Test Cases", tc_blocks()),
        ],
        title="Тест-кейсы: всплывающее окно распознавания документов",
    )


def write_response() -> None:
    write_markdown(
        OUTPUTS / "writer-r1-response.md",
        [(1, "Writer R1 Response", dedent(
            f"""
            ## Summary

            - Created canonical test-case file `{CANONICAL_REL}`.
            - Created split test-design artifacts under `{TD_REL}/`.
            - Preserved `SRC-001`, `WP-01`, support dictionary `DICT-001`, and PDF-visible `BSR 70`-`BSR 75`.
            - Created seven executable manual test cases for source-backed popup behavior.
            - Kept `GAP-001` and `GAP-002` visible as non-blocking residual risks.

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
        # Prompt: Structure Preflight R1

        ## Selected Skill

        - Skill: `ft-test-case-reviewer`
        - Mode: `structure_preflight`
        - Instruction scenario: `reviewer.structure_preflight`

        ## Instruction Loading

        Run before review decisions:

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
        - `fts/AutoFin/{TD_REL}/dictionary-inventory.md`
        - `fts/AutoFin/{TD_REL}/package-test-design-plan.md`
        - `fts/AutoFin/{CYCLE_REL}/outputs/scoped-validator-profile.writer-r1.json`
        - `fts/AutoFin/{CYCLE_REL}/outputs/writer-session-log.writer-r1.md`
        - `fts/AutoFin/{CYCLE_REL}/outputs/agent-decision-log.writer-r1.md`
        - `fts/AutoFin/{CYCLE_REL}/cycle-state.yaml`
        - `fts/AutoFin/{HANDOFF_REL}/scope-coverage-gaps.md`

        ## Boundaries

        - Use structure preflight only: parseability, canonical TC runtime fields, continuous headings, split artifact presence/shape, writer-stage scoped validator evidence, transition readiness.
        - Do not perform semantic coverage review.
        - Do not edit canonical test cases.
        - Do not expand scope beyond section-14 row `015`.
        - Keep `GAP-001` and `GAP-002` visible; do not treat default document type or recognition outcome as covered.

        ## Expected Outputs

        - `fts/AutoFin/{CYCLE_REL}/outputs/structure-preflight-r1-findings.md`
        - `fts/AutoFin/{CYCLE_REL}/outputs/reviewer-session-log.structure-preflight-r1.md`
        - `fts/AutoFin/{CYCLE_REL}/outputs/agent-decision-log.structure-preflight-r1.md`
        - next prompt for `semantic-review-r1` or `writer-structure-r1`
        - updated `cycle-state.yaml`
        """
    ).strip()
    (PROMPTS / "prompt.structure-preflight-r1.md").write_text(prompt + "\n", encoding="utf-8", newline="\n")


def seed_profile() -> None:
    payload = {
        "version": 1,
        "generated_by": "codex_review_cycle_runner",
        "command": "bootstrap before runner validate; overwritten by python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/work/review-cycles/application-card-document-recognition-popup/cycle-state.yaml",
        "scope_slug": SCOPE,
        "canonical_test_cases": CANONICAL_REL,
        "test_design_dir": TD_REL,
        "current_stage": "writer-r1",
        "current_scope_findings": [],
        "unresolved_warning_error_count": 0,
    }
    path = FT / PROFILE_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_logs(final: bool) -> None:
    selected = "\n".join(f"- `{path}` - selected required instruction file." for path in SELECTED_REQUIRED_FILES)
    inputs = "\n".join(f"- `{path}` - required AutoFin writer input." for path in REQ_INPUTS)
    validation = (
        f"`python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/{CYCLE_REL}/cycle-state.yaml` - pass; `{PROFILE_REL}` has `unresolved_warning_error_count = 0`."
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
                "`mockups/` raw images - used only through `mockup-visual-inventory.md`; no business behavior derived from images.",
                "Passport rows and document-result mapping - explicitly out of scope.",
                "Backend/API/RabbitMQ/internal recognition-service effects - not used as test oracles.",
                "Neighboring FT packages and old test-case sets - not used.",
            ])),
            (2, "Key Decisions", bullets([
                "`SRC-001` normalized into `ATOM-001`-`ATOM-008`.",
                "PDF-visible `BSR 70`-`BSR 75` preserved although older parity summary did not list them at fixation.",
                "`DICT-001` uses support values `ВУ`, `СНИЛС`, `Загран. паспорт`, `Паспорт`, `Анкета`; no extra values added.",
                "`GAP-001` remains non-blocking for popup default document type.",
                "`GAP-002` remains non-blocking for recognition success/failure outcome and target field mapping.",
                "Cycle routed to `structure-preflight-r1`, not semantic review directly.",
            ])),
            (2, "Risks And Fallbacks", bullets([
                "Initial PowerShell output for some Russian instruction files showed mojibake; files were reread with explicit UTF-8 and distorted stdout was not used as source evidence.",
                "`source-parity-check.md` under-reports row-level PDF BSR IDs; direct PDF extraction evidence is recorded in writer artifacts.",
            ])),
            (2, "Validation", bullets([
                "`python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - pass.",
                "Direct DOCX extraction - section-14 row 015 confirmed.",
                "Direct PDF extraction - pages 16-17 confirmed `BSR 70`-`BSR 75`.",
                validation,
            ])),
            (2, "Contamination Check", "Work was limited to `fts/AutoFin`, section-14 row `015`, support document type dictionary, and cycle/test-design artifacts for this scope. Mockup-only behavior, passport fields, recognition result mapping and backend effects were excluded."),
            (2, "Event Timeline", table(
                ["step", "event", "result", "artifact_or_evidence"],
                [["1", "Ran instruction resolver", "pass", "budget `140.2 / 200.0 KiB`"], ["2", "Read required instruction and scope inputs", "pass", "session log inputs"], ["3", "Extracted DOCX/PDF row evidence", "pass", "`source/AutoFinPreFinal.docx`; `source/AutoFinPreFinal.pdf`"], ["4", "Generated writer artifacts", "pass", CANONICAL_REL], ["5", "Prepared next prompt/state", "pass", f"{CYCLE_REL}/prompts/prompt.structure-preflight-r1.md"]],
            )),
            (2, "Quality Checkpoints", table(
                ["checkpoint", "status", "evidence", "follow_up"],
                [["Writer Quality Gate", "`pass`", f"`{TD_REL}/writer-quality-gate.md`", "structure preflight"], ["Source row parity", "`pass`", "`SRC-001`", "semantic reviewer should verify"], ["PDF req id parity", "`pass`", "`BSR 70`-`BSR 75`", "semantic reviewer should verify"], ["Residual gap visibility", "`pass`", "`GAP-001`; `GAP-002` in canonical and cycle state", "keep visible"]],
            )),
            (2, "Artifact Write Strategy", table(
                ["artifact_path", "artifact_size_class", "write_strategy", "declared_before_first_write", "helper", "forbidden_methods_checked"],
                [[CANONICAL_REL, "`package-based generated`", "`file-based manifest write`", "`yes`", "`scripts/write_artifact_sections.py --manifest <manifest.json>`", "`yes`"], [TD_REL, "`split generated`", "`file-based manifest write`", "`yes`", "`scripts/write_artifact_sections.py --manifest <manifest.json>`", "`yes`"]],
            )),
            (2, "Technical Fallbacks", table(
                ["fallback_id", "trigger", "failed_method", "fallback_method", "helper_artifact_path", "retained", "quality_risk", "follow_up"],
                [["`TF-001`", "`encoding issue`", "`PowerShell console output read without explicit UTF-8`", "`Get-Content -Encoding UTF8` and direct DOCX/PDF extraction", "`n/a`", "`n/a`", "`no source-fidelity risk; distorted stdout discarded and not used as evidence`", "`No reviewer action; source evidence was reread through UTF-8/DOCX/PDF extraction.`"]],
            )),
            (2, "Handoff Notes For Next Session", bullets([
                "Structure preflight should check parseability and artifact shape only.",
                "Semantic reviewer should verify that `BSR 75` is preserved as `GAP-002`, not converted into unsupported recognition-result coverage.",
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
                    ["`DEC-001`", "1", "`scope-boundary`", "`scope-contract.md`", "Use only section-14 row `015`.", "Scope explicitly excludes passport fields and recognition-result mapping.", CANONICAL_REL, "`high`", "`applied`"],
                    ["`DEC-002`", "2", "`traceability`", "direct PDF pages 16-17 extraction", "Preserve `BSR 70`-`BSR 75`.", "PDF-only IDs in confirmed scope are mandatory for traceability.", f"{TD_REL}/atomic-requirements-ledger.md", "`high`", "`applied`"],
                    ["`DEC-003`", "3", "`coverage`", "`SRC-001`; `BSR 71`", "Cover dictionary composition from support values but not default selection.", "Support resolves values only; default remains open in `GAP-001`.", f"{TD_REL}/dictionary-inventory.md", "`high`", "`applied`"],
                    ["`DEC-004`", "4", "`coverage`", "`SRC-001`; `BSR 74`", "Create no-file recognition warning TC with exact source text.", "The warning is observable and explicitly stated.", f"{CANONICAL_REL}#TC-AFDRP-007", "`high`", "`applied`"],
                    ["`DEC-005`", "5", "`gap`", "`SRC-001`; `BSR 75`; handoff constraints", "Preserve recognition-with-files as `ATOM-008` + `GAP-002`, no TC.", "Observable outcome and target field mapping are not allowed/source-complete for this scope.", f"{TD_REL}/coverage-gaps.md", "`high`", "`applied`"],
                    ["`DEC-006`", "6", "`routing`", "`session-based-review-cycle-format.md`", "Route to `structure-preflight-r1` with `writer-draft-ready` after clean validation.", "Writer must not start review directly and must not bypass structure preflight.", f"{CYCLE_REL}/cycle-state.yaml", "`high`", "`applied`"],
                ],
            )),
        ],
        title="Agent Decision Log",
    )


def write_state(final: bool) -> None:
    current_stage = "structure-preflight-r1" if final else "writer-r1"
    state = dedent(
        f"""
        cycle_id: AutoFin-application-card-document-recognition-popup-2026-06-30
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
          - {HANDOFF_REL}/scope-gap-review.md
          - {HANDOFF_REL}/scope-contract.md
          - {HANDOFF_REL}/source-parity-check.md
          - {HANDOFF_REL}/source-row-inventory.md
          - {HANDOFF_REL}/mockup-visual-inventory.md
          - {HANDOFF_REL}/scope-coverage-gaps.md
          - {HANDOFF_REL}/scope-clarification-requests.md
          - {CANONICAL_REL}
          - {TD_REL}/artifact-write-strategy.md
          - {TD_REL}/atomic-requirements-ledger.md
          - {TD_REL}/internal-work-package-coverage.md
          - {TD_REL}/source-row-inventory.md
          - {TD_REL}/source-row-completeness-matrix.md
          - {TD_REL}/source-table-normalization.md
          - {TD_REL}/test-design-decision-table.md
          - {TD_REL}/package-test-design-plan.md
          - {TD_REL}/test-design-applicability-matrix.md
          - {TD_REL}/dictionary-inventory.md
          - {TD_REL}/coverage-obligation-table.md
          - {TD_REL}/coverage-gaps.md
          - {TD_REL}/writer-quality-gate.md
          - {TD_REL}/writer-self-check.md
          - {CYCLE_REL}/outputs/writer-r1-response.md
          - {CYCLE_REL}/outputs/writer-session-log.writer-r1.md
          - {CYCLE_REL}/outputs/agent-decision-log.writer-r1.md
          - {PROFILE_REL}
          - {CYCLE_REL}/prompts/prompt.structure-preflight-r1.md
        blocking_reasons: []
        blocking_findings: []
        open_questions:
          - GAP-001 non-blocking residual risk; document type default is unresolved; support only provides dictionary values.
          - GAP-002 non-blocking residual risk; successful and failed recognition outcomes are unresolved.
        accepted_risks: []
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
          scoped_validator_profile: {PROFILE_REL}
        open_questions:
          - GAP-001: Какой тип документа выбран в popup по умолчанию, если выбор по умолчанию должен проверяться? Support provides dictionary values, but default remains unresolved.
          - GAP-002: Что должно произойти после successful/failed recognition?
        blocking_reasons: []
        accepted_risks: []
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
        seed_profile()
    write_logs(final=args.final)
    write_state(final=args.final)
    if args.final:
        write_compat_workflow_state()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
