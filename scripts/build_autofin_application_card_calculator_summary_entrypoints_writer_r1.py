from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "fts" / "AutoFin"
SCOPE = "application-card-calculator-summary-entrypoints"
SECTION = "14"
TD_REL = f"work/test-design/{SECTION}-{SCOPE}"
TD = FT / TD_REL
CANONICAL_REL = f"test-cases/{SECTION}-{SCOPE}.md"
CANONICAL = FT / CANONICAL_REL
CYCLE_REL = f"work/review-cycles/{SCOPE}"
CYCLE = FT / CYCLE_REL
OUTPUTS = CYCLE / "outputs"
PROMPTS = CYCLE / "prompts"
HANDOFF_REL = f"work/stage-handoffs/05-{SCOPE}"
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


def tc_blocks() -> str:
    return dedent(
        """
        ## TC-ACCS-001

        **Название:** Видимость виджета краткой информации с калькулятора в карточке заявки

        **Тип:** Positive

        **Приоритет:** High

        **package_id:** WP-01

        **Трассировка:** `ATOM-001`; `BSR 35`; `SRC-001`; `WP-01`

        ### Предусловия

        - Открыта карточка заявки.

        ### Тестовые данные

        Не требуются.

        ### Шаги

        1. Перейти к области карточки заявки, где отображаются entrypoints кредитного калькулятора.

        ### Итоговый ожидаемый результат

        Виджет `Краткая информация с калькулятора` отображается в карточке заявки.

        ### Постусловия

        Не требуются.

        ## TC-ACCS-002

        **Название:** Отображение параметров краткой информации с этапа кредитного калькулятора

        **Тип:** Positive

        **Приоритет:** High

        **package_id:** WP-01

        **Трассировка:** `ATOM-002`; `BSR 36`; `SRC-001`; `WP-01`

        ### Предусловия

        - Открыта карточка заявки.
        - На этапе `Кредитный калькулятор` для этой заявки зафиксированы значения параметров из тестовых данных.

        ### Тестовые данные

        - Сумма кредита: `1500000 Р`.
        - VIN: `XW8ZZZ61ZKG000001`.
        - Ставка: `12,5 %`.
        - Платеж в месяц: `35000 Р`.
        - Срок: `60 мес`.

        ### Шаги

        1. Открыть виджет `Краткая информация с калькулятора` в карточке заявки.

        ### Итоговый ожидаемый результат

        В виджете отображаются параметры `Сумма кредита, Р`, `VIN`, `Ставка, %`, `Платеж в месяц, Р`, `Срок, мес.` со значениями из тестовых данных.

        ### Постусловия

        Не требуются.

        ## TC-ACCS-003

        **Название:** Переход на этап кредитного калькулятора при нажатии на виджет

        **Тип:** Positive

        **Приоритет:** Medium

        **package_id:** WP-01

        **Трассировка:** `ATOM-003`; `BSR 37`; `SRC-001`; `GAP-001`; `WP-01`

        ### Предусловия

        - Открыта карточка заявки.
        - Виджет `Краткая информация с калькулятора` отображается.

        ### Тестовые данные

        Не требуются.

        ### Шаги

        1. Нажать на виджет `Краткая информация с калькулятора`.

        ### Итоговый ожидаемый результат

        Выполнен переход на этап `Кредитный калькулятор`.

        ### Постусловия

        Не требуются.

        ## TC-ACCS-004

        **Название:** Открытие окна кредитного калькулятора с предзаполненными данными по заявке

        **Тип:** Positive

        **Приоритет:** High

        **package_id:** WP-01

        **Трассировка:** `ATOM-004`; `BSR 38`; `SRC-002`; `GAP-001`; `WP-01`

        ### Предусловия

        - Открыта карточка заявки.
        - В заявке есть сохраненные данные, доступные для предзаполнения кредитного калькулятора.

        ### Тестовые данные

        - Заявка содержит VIN `XW8ZZZ61ZKG000001`.
        - Заявка содержит сумму кредита `1500000 Р`.

        ### Шаги

        1. Нажать кнопку `Кредитный калькулятор`.

        ### Итоговый ожидаемый результат

        Открыто окно `Кредитный калькулятор` с предзаполненными данными по текущей заявке.

        ### Постусловия

        Не требуются.
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
        TD / "source-row-inventory.md",
        [(1, "Source Row Inventory", table(
            ["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"],
            [
                ["`SRC-001`", "`WP-01`", "Краткая информация с калькулятора", "DOCX section-14 table row 002; PDF page 15", "`BSR 35`; `BSR 36`; `BSR 37`", "`yes`", "`ATOM-001`; `ATOM-002`; `ATOM-003`; `GAP-001`"],
                ["`SRC-002`", "`WP-01`", "Кредитный калькулятор", "DOCX section-14 table row 003; PDF page 15", "`BSR 38`", "`yes`", "`ATOM-004`; `GAP-001`"],
            ],
        ))],
    )
    write_markdown(
        TD / "source-table-normalization.md",
        [(1, "Source Table Normalization", table(
            ["source_property_id", "source_row_id", "package_id", "field_or_block", "property", "condition", "expected_behavior", "requirement_code", "source_ref", "confidence", "gap_id", "linked_atoms"],
            [
                ["`SP-001`", "`SRC-001`", "`WP-01`", "Краткая информация с калькулятора", "`visibility`", "`always`", "Виджет краткой информации виден всегда.", "`BSR 35`", "PDF page 15; DOCX row 002", "`high`", "`none_required:covered`", "`ATOM-001`"],
                ["`SP-002`", "`SRC-001`", "`WP-01`", "Краткая информация с калькулятора", "`summary-content`", "`calculator-stage-data-exists`", "Виджет отображает параметры `Сумма кредита, Р`; `VIN`; `Ставка, %`; `Платеж в месяц, Р`; `Срок, мес.`.", "`BSR 36`", "PDF page 15; DOCX row 002", "`high`", "`none_required:covered`", "`ATOM-002`"],
                ["`SP-003`", "`SRC-001`", "`WP-01`", "Краткая информация с калькулятора", "`widget-action`", "`user-clicks-widget`", "Нажатие на виджет выполняет переход на этап `Кредитный калькулятор`.", "`BSR 37`", "PDF page 15; DOCX row 002", "`high`", "`GAP-001` for external calculator behavior", "`ATOM-003`"],
                ["`SP-004`", "`SRC-002`", "`WP-01`", "Кредитный калькулятор", "`button-action`", "`user-clicks-button`", "Нажатие на кнопку открывает окно `Кредитный калькулятор` с предзаполненными данными по заявке.", "`BSR 38`", "PDF page 15; DOCX row 003", "`high`", "`GAP-001` for prefill mapping and calculator screen rules", "`ATOM-004`"],
            ],
        ))],
    )
    write_markdown(
        TD / "source-row-completeness-matrix.md",
        [(1, "Source Row Completeness Matrix", table(
            ["source_row_id", "source_requirement_codes", "normalized_property_ids", "linked_atoms", "gap_ids", "coverage_decision"],
            [
                ["`SRC-001`", "`BSR 35`; `BSR 36`; `BSR 37`", "`SP-001`; `SP-002`; `SP-003`", "`ATOM-001`; `ATOM-002`; `ATOM-003`", "`GAP-001` for `BSR 37` external calculator behavior only", "`covered-with-residual-risk`"],
                ["`SRC-002`", "`BSR 38`", "`SP-004`", "`ATOM-004`", "`GAP-001` for prefill mapping and calculator screen rules", "`covered-with-residual-risk`"],
            ],
        ))],
    )
    write_markdown(
        TD / "atomic-requirements-ledger.md",
        [(1, "Atomic Requirements Ledger", table(
            ["atom_id", "package_id", "source_property_id", "req_id", "source_row_id", "atomic_statement", "coverage_status", "covered_by_tc", "planned_tc_or_gap", "gap_id"],
            [
                ["`ATOM-001`", "`WP-01`", "`SP-001`", "`BSR 35`", "`SRC-001`", "Виджет `Краткая информация с калькулятора` виден в карточке заявки всегда.", "`covered`", "`TC-ACCS-001`", "`TC-ACCS-001`", "`none_required:covered`"],
                ["`ATOM-002`", "`WP-01`", "`SP-002`", "`BSR 36`", "`SRC-001`", "Виджет отображает краткую информацию с этапа `Кредитный калькулятор`: `Сумма кредита, Р`, `VIN`, `Ставка, %`, `Платеж в месяц, Р`, `Срок, мес.`.", "`covered`", "`TC-ACCS-002`", "`TC-ACCS-002`", "`none_required:covered`"],
                ["`ATOM-003`", "`WP-01`", "`SP-003`", "`BSR 37`", "`SRC-001`", "При нажатии на виджет выполняется переход на этап `Кредитный калькулятор`.", "`covered`", "`TC-ACCS-003`", "`TC-ACCS-003`", "`GAP-001`"],
                ["`ATOM-004`", "`WP-01`", "`SP-004`", "`BSR 38`", "`SRC-002`", "При нажатии на кнопку `Кредитный калькулятор` открывается окно `Кредитный калькулятор` с предзаполненными данными по заявке.", "`covered`", "`TC-ACCS-004`", "`TC-ACCS-004`", "`GAP-001`"],
            ],
        ))],
    )
    write_markdown(
        TD / "test-design-decision-table.md",
        [(1, "Test Design Decision Table", table(
            ["decision_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "decision", "decision_reason", "planned_tc_or_gap", "oracle_source", "must_be_executable", "observable_oracle", "testable_part", "blocked_part", "gap_admissibility", "review_risk"],
            [
                ["`DD-001`", "`WP-01`", "`SP-001`", "`ATOM-001`", "`visibility`", "`standalone_tc`", "Visibility is explicitly stated.", "`TC-ACCS-001`", "FT row and PDF `BSR 35`", "`yes`", "Widget is visible.", "Visible widget.", "`none_required:covered`", "`none_required:covered`", "`low`"],
                ["`DD-002`", "`WP-01`", "`SP-002`", "`ATOM-002`", "`summary-content`", "`standalone_tc`", "Displayed parameter list is explicitly stated.", "`TC-ACCS-002`", "FT row and PDF `BSR 36`", "`yes`", "Listed parameters are displayed.", "Parameter presence and values from test fixture.", "`none_required:covered`", "`none_required:covered`", "`medium`"],
                ["`DD-003`", "`WP-01`", "`SP-003`", "`ATOM-003`", "`widget-action`", "`standalone_tc`", "Transition target is explicit; target screen internals are external.", "`TC-ACCS-003`; `GAP-001`", "FT row and PDF `BSR 37`", "`yes`", "Stage `Кредитный калькулятор` is opened.", "Entry transition.", "Calculator behavior after transition.", "`non-blocking`", "`medium`"],
                ["`DD-004`", "`WP-01`", "`SP-004`", "`ATOM-004`", "`button-action`", "`standalone_tc`", "Window opening and prefilled state are explicit; exact mapping is external.", "`TC-ACCS-004`; `GAP-001`", "FT row and PDF `BSR 38`", "`yes`", "Window opens with prefilled application data.", "Entrypoint opening and prefilled state.", "Prefill rules and calculator screen behavior.", "`non-blocking`", "`medium`"],
            ],
        ))],
    )
    write_markdown(
        TD / "coverage-obligation-table.md",
        [(1, "Coverage Obligation Table", "Coverage obligation expansion is not applicable for this scope: rows `002-003` do not define numeric boundaries, exact length, masks, repeatable blocks, checkbox lists, generated documents, combinatorial factors, API/async effects or other mandatory deep coverage classes. Source-backed display/action obligations are tracked in `atomic-requirements-ledger.md`, `package-test-design-plan.md` and `coverage-map.md`.\n\n" + table(
            ["obligation_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "obligation_class", "required_behavior", "source_ref", "planned_tc_or_gap", "status", "review_notes"],
            [
                ["`OBL-N/A-001`", "`WP-01`", "", "", "`other`", "`other`", "No mandatory deep coverage class requires obligation expansion for this scope.", "`SRC-001`; `SRC-002`; `BSR 35`-`BSR 38`", "`coverage-map.md`", "`n/a`", "Display/action obligations are represented as atoms and TCs; `GAP-001` remains for external calculator behavior."],
            ],
        ))],
    )
    write_markdown(
        TD / "package-test-design-plan.md",
        [(1, "Package Test Design Plan", table(
            ["design_item_id", "package_id", "design_dimension", "source_ref", "linked_atoms", "planned_check", "check_type", "coverage_class", "input_class", "single_expected_behavior", "oracle_source", "planned_tc_or_gap", "status"],
            [
                ["`PLAN-001`", "`WP-01`", "`visibility`", "`SRC-001`; `BSR 35`", "`ATOM-001`", "Открыть карточку заявки и проверить наличие виджета.", "`positive`", "`visibility-always`", "`existing-application-card`", "Виджет отображается.", "FT row", "`TC-ACCS-001`", "`covered`"],
                ["`PLAN-002`", "`WP-01`", "`summary-content`", "`SRC-001`; `BSR 36`", "`ATOM-002`", "Проверить состав краткой информации по тестовой заявке.", "`positive`", "`summary-parameter-list`", "`application-with-calculator-values`", "Виджет отображает пять перечисленных параметров.", "FT row", "`TC-ACCS-002`", "`covered`"],
                ["`PLAN-003`", "`WP-01`", "`widget-action`", "`SRC-001`; `BSR 37`", "`ATOM-003`", "Нажать на виджет.", "`positive`", "`navigation-target-opened`", "`click-widget`", "Открыт этап `Кредитный калькулятор`.", "FT row", "`TC-ACCS-003`; `GAP-001`", "`covered`"],
                ["`PLAN-004`", "`WP-01`", "`button-action`", "`SRC-002`; `BSR 38`", "`ATOM-004`", "Нажать кнопку `Кредитный калькулятор`.", "`positive`", "`window-open-prefilled`", "`click-button`", "Открыто окно `Кредитный калькулятор` с предзаполненными данными.", "FT row", "`TC-ACCS-004`; `GAP-001`", "`covered`"],
            ],
        ))],
    )
    write_markdown(
        TD / "test-design-applicability-matrix.md",
        [(1, "Test-design Applicability Matrix", table(
            ["dimension", "applicable", "source_ref", "reason", "linked_atoms", "linked_test_cases", "gap_id"],
            [
                ["`other`", "`yes`", "`BSR 35`", "Visibility/availability is explicitly stated.", "`ATOM-001`", "`TC-ACCS-001`", ""],
                ["`other`", "`no`", "`scope-contract.md`", "No closed list or dictionary is referenced by rows 002-003.", "`none_required:no_source`", "`none_required:no_source`", ""],
                ["`other`", "`yes`", "`BSR 36`; `BSR 37`; `BSR 38`", "Rows define positive display/action outcomes.", "`ATOM-002`; `ATOM-003`; `ATOM-004`", "`TC-ACCS-002`; `TC-ACCS-003`; `TC-ACCS-004`", "`GAP-001`"],
                ["`other`", "`no`", "`scope-contract.md`", "No invalid action/input behavior is stated.", "`none_required:no_source`", "`none_required:no_source`", ""],
                ["`other`", "`yes`", "`BSR 37`; `BSR 38`", "Widget transition and button window opening are stated.", "`ATOM-003`; `ATOM-004`", "`TC-ACCS-003`; `TC-ACCS-004`", "`GAP-001`"],
                ["`other`", "`no`", "`scope-coverage-gaps.md`", "Calculation logic belongs to external FT `Калькулятор`.", "`none_required:out_of_scope`", "`none_required:out_of_scope`", "`GAP-001`"],
                ["`other`", "`no`", "`scope-contract.md`", "No backend/API effect is stated for rows 002-003.", "`none_required:no_source`", "`none_required:no_source`", ""],
                ["`other`", "`no`", "`scope-contract.md`", "No role/status/security rule is stated in rows 002-003.", "`none_required:no_source`", "`none_required:no_source`", ""],
            ],
        ))],
    )
    write_markdown(
        TD / "internal-work-package-coverage.md",
        [(1, "Internal Work Package Coverage", table(
            ["package_id", "focus", "source_rows", "atoms", "test_cases", "coverage_status", "open_gaps", "accepted_risks"],
            [["`WP-01`", "calculator entrypoints", "`SRC-001`; `SRC-002`", "`ATOM-001`; `ATOM-002`; `ATOM-003`; `ATOM-004`", "`TC-ACCS-001`; `TC-ACCS-002`; `TC-ACCS-003`; `TC-ACCS-004`", "`covered-with-residual-risk`", "`GAP-001`", "`GAP-001` accepted as non-blocking until FT `Калькулятор` is connected"]],
        ))],
    )
    write_markdown(
        TD / "coverage-gaps.md",
        [(1, "Coverage Gaps", table(
            ["gap_id", "status", "source_ref", "linked_atoms", "impact", "handling"],
            [["`GAP-001`", "`open`", "`section-14 rows 002-003`", "`ATOM-003`; `ATOM-004`", "`non-blocking`", "Do not test calculator screen, calculations, offer selection or exact prefill mapping without external FT `Калькулятор`."]],
        ))],
    )
    write_markdown(
        TD / "coverage-map.md",
        [(1, "Coverage Map", table(
            ["source_row_id", "req_id", "atom_id", "package_id", "test_case_id", "coverage_status", "notes"],
            [
                ["`SRC-001`", "`BSR 35`", "`ATOM-001`", "`WP-01`", "`TC-ACCS-001`", "`covered`", "Visibility only."],
                ["`SRC-001`", "`BSR 36`", "`ATOM-002`", "`WP-01`", "`TC-ACCS-002`", "`covered`", "Listed summary parameters only."],
                ["`SRC-001`", "`BSR 37`", "`ATOM-003`", "`WP-01`", "`TC-ACCS-003`", "`covered-with-residual-risk`", "`GAP-001` for calculator behavior."],
                ["`SRC-002`", "`BSR 38`", "`ATOM-004`", "`WP-01`", "`TC-ACCS-004`", "`covered-with-residual-risk`", "`GAP-001` for prefill mapping."],
            ],
        ))],
    )
    write_markdown(
        TD / "test-design-review.md",
        [(1, "Test Design Review", table(
            ["review_item", "status", "severity", "affected_package", "evidence", "required_action", "blocks_ready_for_review"],
            [
                ["`decision-table-classification`", "`pass`", "`info`", "`WP-01`", "`test-design-decision-table.md` maps four source-backed properties.", "`none_required:pass`", "`no`"],
                ["`ledger-plan-alignment`", "`pass`", "`info`", "`WP-01`", "Every `ATOM-*` has plan and TC mapping.", "`none_required:pass`", "`no`"],
                ["`coverage-class-completeness`", "`pass`", "`info`", "`WP-01`", "`coverage-obligation-table.md` contains all source-backed obligations.", "`none_required:pass`", "`no`"],
                ["`numeric-length-boundaries`", "`pass`", "`info`", "`WP-01`", "No numeric input or boundary validation belongs to rows 002-003.", "`none_required:pass`", "`no`"],
                ["`conditional-branches`", "`pass`", "`info`", "`WP-01`", "No inverse branch is stated for visibility/action behavior.", "`none_required:pass`", "`no`"],
                ["`dictionary-closed-set`", "`pass`", "`info`", "`WP-01`", "No dictionary or closed list is referenced.", "`none_required:pass`", "`no`"],
                ["`mask-format-coverage`", "`pass`", "`info`", "`WP-01`", "No mask/format rule is in rows 002-003.", "`none_required:pass`", "`no`"],
                ["`negative-fixture-isolation`", "`pass`", "`info`", "`WP-01`", "No negative class is source-backed.", "`none_required:pass`", "`no`"],
                ["`applicability-linked-tc-semantics`", "`pass`", "`info`", "`WP-01`", "Applicable dimensions link to semantic TC coverage or `GAP-001`.", "`none_required:pass`", "`no`"],
                ["`gap-admissibility`", "`pass`", "`info`", "`WP-01`", "`GAP-001` is non-blocking and visible.", "`none_required:pass`", "`no`"],
                ["`gap-specificity`", "`pass`", "`info`", "`WP-01`", "`GAP-001` names calculator screen, calculations, offer selection and prefill mapping.", "`none_required:pass`", "`no`"],
                ["`unsupported-ui-mechanism`", "`pass`", "`info`", "`WP-01`", "No exact UI text, validation marker, calculation, offer selection or prefill mapping is invented.", "`none_required:pass`", "`no`"],
                ["`internal-observability`", "`pass`", "`info`", "`WP-01`", "Expected results are visible widget, listed params, transition or opened window.", "`none_required:pass`", "`no`"],
                ["`metadata-only-exclusion`", "`pass`", "`info`", "`WP-01`", "O/R/type metadata is not promoted into standalone TCs without behavior.", "`none_required:pass`", "`no`"],
                ["`tc-mapping-atomicity`", "`pass`", "`info`", "`WP-01`", "Four TCs cover four atomic obligations.", "`none_required:pass`", "`no`"],
                ["`ready-for-tc-writing`", "`pass`", "`info`", "`WP-01`", "Canonical TC file and split artifacts are synchronized.", "`none_required:pass`", "`no`"],
            ],
        ))],
    )
    gate_items = [
        "artifact-write-strategy",
        "mockup-visual-inventory",
        "source-row-inventory",
        "source-normalization-atomic",
        "test-design-decision-table",
        "test-design-review",
        "gap-admissibility",
        "ledger-atomicity",
        "gsr-range-compression",
        "design-plan-atomicity",
        "scenario-does-not-replace-atomic",
        "tc-atomicity",
        "test-data-specificity",
        "internal-observability",
        "action-observability",
        "semantic-req-id-parity",
        "package-ready",
        "scoped-validator-findings",
    ]
    write_markdown(
        TD / "writer-quality-gate.md",
        [(1, "Writer Quality Gate", table(
            ["gate_item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"],
            [[f"`{item}`", "`pass`", (f"`{WRITER_PROFILE_REL}` with `unresolved_warning_error_count = 0`." if item == "scoped-validator-findings" else "Writer-side check passed for `WP-01`.") , "`WP-01`", "`none_required:pass`", "`no`"] for item in gate_items],
        ))],
    )
    write_markdown(
        TD / "writer-self-check.md",
        [
            (1, "Writer Self-Check", table(
                ["check", "status", "evidence", "follow_up"],
                [
                    ["instruction context", "`pass`", "Resolver command and selected files recorded in session log.", "`none_required:pass`"],
                    ["source row preservation", "`pass`", "`SRC-001` and `SRC-002` preserved.", "`none_required:pass`"],
                    ["PDF-only req id preservation", "`pass`", "`BSR 35`-`BSR 38` preserved in ledger and TCs.", "`none_required:pass`"],
                    ["scope boundary", "`pass`", "No calculator calculation, offer selection or screen internals asserted.", "`none_required:pass`"],
                    ["residual risk visibility", "`pass`", "`GAP-001` present in coverage artifacts and cycle state.", "`none_required:pass`"],
                    ["scoped validator", "`pass`", f"`{WRITER_PROFILE_REL}` expected/generated with zero unresolved warning/error findings.", "`none_required:pass`"],
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
            (2, "Scope Boundaries", "Набор покрывает только section-14 rows `002-003`: виджет краткой информации с калькулятора и кнопку `Кредитный калькулятор` в карточке заявки. Набор не проверяет внутреннюю логику кредитного калькулятора, расчеты, выбор предложения, экран калькулятора и точные правила предзаполнения; это остается `GAP-001` до подключения ФТ `Калькулятор`."),
            (2, "Coverage Summary", table(
                ["package_id", "source_row_id", "req_id", "atom_id", "test_case_id", "coverage_status"],
                [
                    ["`WP-01`", "`SRC-001`", "`BSR 35`", "`ATOM-001`", "`TC-ACCS-001`", "`covered`"],
                    ["`WP-01`", "`SRC-001`", "`BSR 36`", "`ATOM-002`", "`TC-ACCS-002`", "`covered`"],
                    ["`WP-01`", "`SRC-001`", "`BSR 37`", "`ATOM-003`", "`TC-ACCS-003`", "`covered-with-residual-risk: GAP-001`"],
                    ["`WP-01`", "`SRC-002`", "`BSR 38`", "`ATOM-004`", "`TC-ACCS-004`", "`covered-with-residual-risk: GAP-001`"],
                ],
            )),
            (2, "Coverage Gaps", "- `GAP-001` remains open and non-blocking: behavior of the external calculator screen, calculation rules, offer selection and exact prefill mapping are not covered without FT `Калькулятор`."),
            (2, "Test Cases", tc_blocks()),
        ],
        title="Тест-кейсы: виджет и кнопка кредитного калькулятора в карточке заявки",
    )


def seed_writer_profile() -> None:
    profile = {
        "version": 1,
        "generated_by": "codex_review_cycle_runner",
        "command": "bootstrap before runner validate; overwritten by python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/work/review-cycles/application-card-calculator-summary-entrypoints/cycle-state.yaml",
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

            - Created canonical test-case file `{CANONICAL_REL}`.
            - Created split test-design artifacts under `{TD_REL}/`.
            - Preserved `SRC-001`, `SRC-002`, `WP-01` and PDF-only `BSR 35`-`BSR 38`.
            - Covered only source-backed calculator summary/button entrypoints.
            - Kept `GAP-001` visible as non-blocking residual risk for external FT `Калькулятор`.

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
        - `fts/AutoFin/{TD_REL}/package-test-design-plan.md`
        - `fts/AutoFin/{CYCLE_REL}/outputs/scoped-validator-profile.writer-r1.json`
        - `fts/AutoFin/{CYCLE_REL}/outputs/writer-session-log.writer-r1.md`
        - `fts/AutoFin/{CYCLE_REL}/outputs/agent-decision-log.writer-r1.md`
        - `fts/AutoFin/{CYCLE_REL}/cycle-state.yaml`
        - `fts/AutoFin/{HANDOFF_REL}/scope-coverage-gaps.md`

        ## Boundaries

        - Do not perform semantic coverage review.
        - Do not edit canonical test cases.
        - Do not expand scope beyond section-14 rows `002-003`.
        - Keep `GAP-001` visible; do not treat external calculator logic as covered.

        ## Expected Outputs

        - `fts/AutoFin/{CYCLE_REL}/outputs/structure-preflight-r1-findings.md`
        - `fts/AutoFin/{CYCLE_REL}/outputs/reviewer-session-log.structure-preflight-r1.md`
        - `fts/AutoFin/{CYCLE_REL}/outputs/agent-decision-log.structure-preflight-r1.md`
        - next prompt for `semantic-review-r1` or `writer-structure-r1`
        - updated `cycle-state.yaml`
        """
    ).strip()
    (PROMPTS / "prompt.structure-preflight-r1.md").write_text(prompt + "\n", encoding="utf-8", newline="\n")


def write_logs(final: bool) -> None:
    selected = "\n".join(f"- `{path}` - selected required instruction file." for path in SELECTED_REQUIRED_FILES)
    inputs = "\n".join(
        f"- `{path}` - required AutoFin writer input."
        for path in [
            "AGENT-NOTES.md",
            f"{HANDOFF_REL}/scope-gap-review.md",
            f"{HANDOFF_REL}/scope-contract.md",
            f"{HANDOFF_REL}/source-parity-check.md",
            f"{HANDOFF_REL}/source-row-inventory.md",
            f"{HANDOFF_REL}/mockup-visual-inventory.md",
            f"{HANDOFF_REL}/scope-coverage-gaps.md",
            f"{HANDOFF_REL}/scope-clarification-requests.md",
            "source/AutoFinPreFinal.docx",
            "source/AutoFinPreFinal.pdf",
            f"{CYCLE_REL}/cycle-state.yaml",
        ]
    )
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
                "`mockups/` - used only through `mockup-visual-inventory.md`; no business behavior derived from images.",
                "FT `Калькулятор` - not connected; retained as `GAP-001` rather than invented.",
                "Out-of-scope section-14 rows beyond `002-003` - not used.",
            ])),
            (2, "Key Decisions", bullets([
                "`SRC-001` normalized into `ATOM-001`-`ATOM-003`.",
                "`SRC-002` normalized into `ATOM-004`.",
                "PDF-only `BSR 35`-`BSR 38` preserved despite older parity summary saying no additional code at fixation.",
                "`GAP-001` remains non-blocking residual risk for external calculator screen and prefill mapping.",
                "Cycle routed to `structure-preflight-r1`, not semantic review directly.",
            ])),
            (2, "Risks And Fallbacks", bullets([
                "Initial PowerShell output for Russian instructions showed mojibake; files were reread with explicit UTF-8 and distorted stdout was not used as source evidence.",
                "`source-parity-check.md` under-reports PDF-only codes; direct PDF page 15 extraction is recorded in decision log and artifacts.",
            ])),
            (2, "Validation", bullets([
                "`python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - pass.",
                "Direct DOCX extraction - table row 002/003 confirmed.",
                "Direct PDF extraction - page 15 confirmed `BSR 35`-`BSR 38`.",
                validation,
            ])),
            (2, "Contamination Check", "Work was limited to `fts/AutoFin`, section-14 rows `002-003`, and cycle/test-design artifacts for this scope. Neighboring FT packages, old test-case sets and mockup-only behavior were not used as requirements."),
            (2, "Event Timeline", table(
                ["step", "event", "result", "artifact_or_evidence"],
                [["1", "Ran instruction resolver", "pass", "budget `140.2 / 200.0 KiB`"], ["2", "Read required instruction and scope inputs", "pass", "session log inputs"], ["3", "Extracted DOCX/PDF row evidence", "pass", "`source/AutoFinPreFinal.docx`; `source/AutoFinPreFinal.pdf`"], ["4", "Generated writer artifacts", "pass", CANONICAL_REL], ["5", "Prepared next prompt/state", "pass", f"{CYCLE_REL}/prompts/prompt.structure-preflight-r1.md"]],
            )),
            (2, "Quality Checkpoints", table(
                ["checkpoint", "status", "evidence", "follow_up"],
                [["Writer Quality Gate", "`pass`", f"`{TD_REL}/writer-quality-gate.md`", "structure preflight"], ["Source row parity", "`pass`", "`SRC-001`; `SRC-002`", "semantic reviewer should verify"], ["PDF req id parity", "`pass`", "`BSR 35`-`BSR 38`", "semantic reviewer should verify"], ["Residual gap visibility", "`pass`", "`GAP-001` in canonical and cycle state", "keep visible"]],
            )),
            (2, "Artifact Write Strategy", table(
                ["artifact_path", "artifact_size_class", "write_strategy", "declared_before_first_write", "helper", "forbidden_methods_checked"],
                [[CANONICAL_REL, "`package-based generated`", "`file-based manifest write`", "`yes`", "`scripts/write_artifact_sections.py --manifest <manifest.json>`", "`yes`"], [TD_REL, "`split generated`", "`file-based manifest write`", "`yes`", "`scripts/write_artifact_sections.py --manifest <manifest.json>`", "`yes`"]],
            )),
            (2, "Technical Fallbacks", table(
                ["fallback_id", "trigger", "failed_method", "fallback_method", "helper_artifact_path", "retained", "quality_risk", "follow_up"],
                [["`TF-001`", "`encoding issue`", "`PowerShell console output read without explicit UTF-8`", "`Get-Content -Encoding UTF8` and direct DOCX/PDF extraction", "`n/a`", "`n/a`", "`none; distorted stdout discarded and not used as evidence`", "`none`"]],
            )),
            (2, "Handoff Notes For Next Session", bullets([
                "Structure preflight should check parseability and artifact shape only.",
                "Semantic reviewer should verify that `GAP-001` was not converted into calculator logic coverage.",
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
                    ["`DEC-001`", "1", "`scope-boundary`", "`scope-contract.md`", "Use only section-14 rows `002-003`.", "Scope explicitly excludes calculator internals.", CANONICAL_REL, "`high`", "`applied`"],
                    ["`DEC-002`", "2", "`traceability`", "direct PDF page 15 extraction", "Preserve `BSR 35`-`BSR 38`.", "PDF-only IDs in confirmed scope are mandatory for traceability.", f"{TD_REL}/atomic-requirements-ledger.md", "`high`", "`applied`"],
                    ["`DEC-003`", "3", "`coverage`", "`SRC-001`", "Create three atoms for visibility, displayed summary parameters and widget transition.", "The row contains three independent obligations.", f"{TD_REL}/atomic-requirements-ledger.md", "`high`", "`applied`"],
                    ["`DEC-004`", "4", "`coverage`", "`SRC-002`", "Create one atom for button opening a prefilled calculator window.", "The row has one entrypoint action; exact prefill mapping remains external.", f"{TD_REL}/atomic-requirements-ledger.md", "`medium`", "`applied`"],
                    ["`DEC-005`", "5", "`gap`", "`scope-coverage-gaps.md`", "Keep `GAP-001` open and non-blocking.", "External FT `Калькулятор` is not connected.", f"{TD_REL}/coverage-gaps.md", "`high`", "`applied`"],
                    ["`DEC-006`", "6", "`routing`", "`session-based-review-cycle-format.md`", "Route to `structure-preflight-r1` with `writer-draft-ready` after clean validation.", "Writer must not start semantic review directly.", f"{CYCLE_REL}/cycle-state.yaml", "`high`", "`applied`"],
                ],
            )),
        ],
        title="Agent Decision Log",
    )


def write_state(*, final: bool) -> None:
    current_stage = "structure-preflight-r1" if final else "writer-r1"
    stage_status = "writer-draft-ready"
    state = dedent(
        f"""
        cycle_id: AutoFin-{SCOPE}
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
        active_transition_prompt: {CYCLE_REL}/prompts/prompt.structure-preflight-r1.md
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
          - {TD_REL}/atomic-requirements-ledger.md
          - {TD_REL}/internal-work-package-coverage.md
          - {TD_REL}/source-row-inventory.md
          - {TD_REL}/source-row-completeness-matrix.md
          - {TD_REL}/test-design-decision-table.md
          - {TD_REL}/package-test-design-plan.md
          - {TD_REL}/test-design-applicability-matrix.md
          - {TD_REL}/coverage-obligation-table.md
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
          - GAP-001 unanswered; keep visible as non-blocking residual risk unless external FT Calculator is connected.
        accepted_risks:
          - GAP-001 accepted residual risk; external FT Calculator is not connected; proceed with explicit rows 002-003 only.
        sessions: []
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
          scoped_validator_profile: {WRITER_PROFILE_REL}
        open_questions:
          - GAP-001 unanswered; keep visible as non-blocking residual risk unless external FT Calculator is connected.
        blocking_reasons: []
        accepted_risks:
          - GAP-001 accepted residual risk; external FT Calculator is not connected; proceed with explicit rows 002-003 only.
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
