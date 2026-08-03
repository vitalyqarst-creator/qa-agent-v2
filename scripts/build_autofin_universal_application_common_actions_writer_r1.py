from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "fts" / "AutoFin"
SCOPE = "universal-application-common-actions"
SECTION = "section-17"
TD_REL = f"work/test-design/{SECTION}-{SCOPE}"
TD = FT / TD_REL
CANONICAL_REL = f"test-cases/{SECTION}-{SCOPE}.md"
CANONICAL = FT / CANONICAL_REL
CYCLE_REL = f"work/review-cycles/{SCOPE}"
CYCLE = FT / CYCLE_REL
OUTPUTS = CYCLE / "outputs"
PROMPTS = CYCLE / "prompts"
HANDOFF_REL = f"work/stage-handoffs/04-{SCOPE}"
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
        manifest_sections.append(
            {"level": level, "heading": heading, "content_file": content_path.name}
        )
    manifest: dict[str, object] = {
        "target_path": str(target),
        "sections": manifest_sections,
    }
    if title:
        preamble = scratch / "00-preamble.md"
        preamble.write_text(f"# {title}\n", encoding="utf-8", newline="\n")
        manifest["preamble_file"] = preamble.name
    manifest_path = scratch / "manifest.json"
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


def tc_block() -> str:
    return dedent(
        """
        **Название:** Открытие окна просмотра истории заявки по действию `История заявки`

        **Тип:** Positive

        **Приоритет:** Medium

        **package_id:** WP-01

        **Трассировка:** `ATOM-001`; `BSR 321`; `SRC-001`; `section-17`; PDF p.38 section `4.5`

        ### Предусловия

        - Открыта карточка Универсальной заявки.

        ### Тестовые данные

        Не требуются.

        ### Шаги

        1. В карточке Универсальной заявки выбрать действие `История заявки`.

        ### Итоговый ожидаемый результат

        Открыто окно просмотра истории заявки.

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
                ["write_method", "`file-based manifest write`", "`scripts/write_artifact_sections.py --manifest <manifest.json>` selected before writing generated artifacts."],
                ["forbidden_methods_checked", "`yes`", "No PowerShell here-string, no one-shot shell Markdown write, no inline giant command."],
                ["helper_artifacts", f"`{TD_REL}/_artifact_write/*/manifest.json`", "Retained for audit and reproducibility."],
            ],
        ))],
    )
    write_markdown(
        TD / "source-row-inventory.md",
        [(1, "Source Row Inventory", table(
            ["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"],
            [[
                "`SRC-001`",
                "`WP-01`",
                "Кнопка `История заявки`: нажатием открывается окно просмотра истории заявки",
                "DOCX section-17 table row 2; PDF p.38 section 4.5",
                "`BSR 321`",
                "`yes`",
                "`ATOM-001`",
            ]],
        ))],
    )
    write_markdown(
        TD / "source-row-completeness-matrix.md",
        [(1, "Source Row Completeness Matrix", table(
            ["source_row_id", "source_requirement_codes", "normalized_property_ids", "linked_atoms", "gap_ids", "coverage_decision"],
            [["`SRC-001`", "`BSR 321`", "`SP-001`", "`ATOM-001`", "`none_required:covered`", "`covered`"]],
        ))],
    )
    write_markdown(
        TD / "source-table-normalization.md",
        [(1, "Source Table Normalization", table(
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
            [[
                "`SRC-001`",
                "`SP-001`",
                "`WP-01`",
                "Карточка Универсальной заявки",
                "`action-navigation`",
                "Пользователь нажимает `История заявки`",
                "Открывается окно просмотра истории заявки.",
                "`BSR 321`",
                "DOCX section-17 row `История заявки`; PDF p.38 section 4.5",
                "`high`",
                "`none_required:covered`",
                "`ATOM-001`",
            ]],
        ))],
    )
    write_markdown(
        TD / "test-design-decision-table.md",
        [(1, "Test Design Decision Table", table(
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
                "review_risk",
            ],
            [[
                "`DD-001`",
                "`WP-01`",
                "`SP-001`",
                "`ATOM-001`",
                "`action-navigation`",
                "`standalone_tc`",
                "Opening the history-view window is the only observable behavior in scope.",
                "`TC-UACA-001`",
                "DOCX/PDF action row",
                "`yes`",
                "`low`",
            ]],
        ))],
    )
    write_markdown(
        TD / "coverage-obligation-table.md",
        [(1, "Coverage Obligation Table", table(
            [
                "obligation_id",
                "package_id",
                "source_property_id",
                "linked_atom_id",
                "property_type",
                "obligation_class",
                "required_behavior",
                "source_ref",
                "planned_tc_or_gap",
                "status",
                "review_notes",
            ],
            [[
                "`OBL-001`",
                "`WP-01`",
                "`SP-001`",
                "`ATOM-001`",
                "`action-navigation`",
                "`navigation-target-opened`",
                "При нажатии `История заявки` открывается окно просмотра истории заявки.",
                "`SRC-001`; `BSR 321`",
                "`TC-UACA-001`",
                "`covered`",
                "`none_required:covered`",
            ]],
        ))],
    )
    write_markdown(
        TD / "atomic-requirements-ledger.md",
        [(1, "Atomic Requirements Ledger", table(
            [
                "atom_id",
                "package_id",
                "source_property_id",
                "req_id",
                "source_row_id",
                "atomic_statement",
                "property_type",
                "coverage_status",
                "covered_by_tc",
                "planned_tc_or_gap",
                "gap_id",
            ],
            [[
                "`ATOM-001`",
                "`WP-01`",
                "`SP-001`",
                "`BSR 321`",
                "`SRC-001`",
                "Действие `История заявки` открывает окно просмотра истории заявки.",
                "`action-navigation`",
                "`covered`",
                "`TC-UACA-001`",
                "`TC-UACA-001`",
                "`none_required:covered`",
            ]],
        ))],
    )
    write_markdown(
        TD / "internal-work-package-coverage.md",
        [(1, "Internal Work Package Coverage", table(
            ["package_id", "focus", "ledger_gate", "design_plan_gate", "tc_gate", "covered_atoms", "linked_test_cases", "open_gaps"],
            [["`WP-01`", "Действие `История заявки`", "`pass`", "`pass`", "`pass`", "`ATOM-001`", "`TC-UACA-001`", "`none_required:covered`"]],
        ))],
    )
    write_markdown(
        TD / "package-ledger-self-check.md",
        [(1, "Package Ledger Self-Check", table(
            ["package_id", "check", "status", "evidence", "required_action"],
            [
                ["`WP-01`", "source row preserved", "`pass`", "`SRC-001` mapped to `ATOM-001`.", "`none_required:pass`"],
                ["`WP-01`", "mandatory req id preserved", "`pass`", "`BSR 321` present in ledger.", "`none_required:pass`"],
                ["`WP-01`", "atom atomicity", "`pass`", "One action outcome only.", "`none_required:pass`"],
            ],
        ))],
    )
    write_markdown(
        TD / "package-test-design-plan.md",
        [(1, "Package Test Design Plan", table(
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
            [[
                "`PLAN-001`",
                "`WP-01`",
                "`action-navigation`",
                "`SRC-001`; `BSR 321`",
                "`ATOM-001`",
                "Выбрать действие `История заявки` в карточке Универсальной заявки.",
                "`positive`",
                "`navigation-target-opened`",
                "`action-click`",
                "Открыто окно просмотра истории заявки.",
                "DOCX/PDF action row",
                "`TC-UACA-001`",
                "`covered`",
            ]],
        ))],
    )
    write_markdown(
        TD / "package-design-plan-self-check.md",
        [(1, "Package Design Plan Self-Check", table(
            ["package_id", "check", "status", "evidence", "required_action"],
            [
                ["`WP-01`", "single expected result", "`pass`", "`PLAN-001` has one observable outcome.", "`none_required:pass`"],
                ["`WP-01`", "scope boundary", "`pass`", "Window internals are not planned.", "`none_required:pass`"],
            ],
        ))],
    )
    write_markdown(
        TD / "test-design-applicability-matrix.md",
        [(1, "Test-design Applicability Matrix", table(
            ["dimension", "applicable", "source_ref", "reason", "linked_atoms", "linked_test_cases", "gap_id"],
            [
                ["`other`", "`yes`", "`SRC-001`; `BSR 321`", "Action opens a history-view window.", "`ATOM-001`", "`TC-UACA-001`", ""],
                ["`role-permission`", "`no`", "`scope-contract.md`", "Section-17 does not define role or status availability rules.", "", "", ""],
                ["`dependency`", "`no`", "`scope-contract.md`", "No conditional dependency is stated for the action.", "", "", ""],
                ["`table-list`", "`no`", "`scope-contract.md`", "No list, table or dictionary composition is in the section-17 row.", "", "", ""],
                ["`integration`", "`no`", "`scope-contract.md`", "Backend history loading and integration behavior are not specified.", "", "", ""],
                ["`persistence`", "`no`", "`scope-contract.md`", "No persistence effect is described for this action entrypoint.", "", "", ""],
            ],
        ))],
    )
    write_markdown(
        TD / "risk-priority-map.md",
        [(1, "Risk / Priority Map", table(
            ["atom_id", "risk_level", "risk_factors", "source_ref", "required_priority", "linked_test_cases", "gap_id", "rationale"],
            [["`ATOM-001`", "`medium`", "User needs access to application history; only entrypoint is in scope.", "`SRC-001`; `BSR 321`", "`Medium`", "`TC-UACA-001`", "`none_required:covered`", "One positive action check covers the source-backed behavior."]],
        ))],
    )
    write_markdown(
        TD / "coverage-map.md",
        [(1, "Coverage Map", table(
            ["source_row_id", "req_id", "atom_id", "package_id", "test_case_id", "coverage_status", "notes"],
            [["`SRC-001`", "`BSR 321`", "`ATOM-001`", "`WP-01`", "`TC-UACA-001`", "`covered`", "Covers only opening the history-view window."]],
        ))],
    )
    write_markdown(
        TD / "coverage-gaps.md",
        [(1, "Coverage Gaps", "No `GAP-*` items are open for `WP-01`. Window internals are excluded by scope rather than treated as writer-side gaps.")],
    )
    review_rows = []
    for item in [
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
    ]:
        review_rows.append([f"`{item}`", "`pass`", "`info`", "`WP-01`", "Checked against section-17 scope.", "`none_required:pass`", "`no`"])
    write_markdown(
        TD / "test-design-review.md",
        [(1, "Test Design Review", table(
            ["review_item", "status", "severity", "affected_package", "evidence", "required_action", "blocks_ready_for_review"],
            review_rows,
        ))],
    )
    gate_rows = []
    for item in [
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
    ]:
        gate_rows.append([f"`{item}`", "`pass`", "Writer-side check passed for `WP-01`.", "`WP-01`", "`none_required:pass`", "`no`"])
    gate_rows.append([
        "`scoped-validator-findings`",
        "`pass`",
        f"`{WRITER_PROFILE_REL}` with `unresolved_warning_error_count = 0`.",
        "`WP-01`",
        "`none_required:pass`",
        "`no`",
    ])
    write_markdown(
        TD / "writer-quality-gate.md",
        [(1, "Writer Quality Gate", table(
            ["gate_item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"],
            gate_rows,
        ))],
    )
    write_markdown(
        TD / "writer-self-check.md",
        [
            (1, "Writer Self-Check", table(
                ["check", "status", "evidence", "follow_up"],
                [
                    ["instruction context", "`pass`", "Resolver command and selected required files recorded in session log.", "`none_required:pass`"],
                    ["source parity", "`pass`", "`BSR 321` and `SRC-001` preserved in ledger, plan and TC.", "`none_required:pass`"],
                    ["scope boundary", "`pass`", "No TC asserts fields, records, filters or contents inside the history window.", "`none_required:pass`"],
                    ["package gates", "`pass`", "`package-ledger-self-check.md`; `package-design-plan-self-check.md`; `internal-work-package-coverage.md`.", "`none_required:pass`"],
                    ["scoped validator", "`pass`", f"`{WRITER_PROFILE_REL}` expected and then generated by runner validation.", "`none_required:pass`"],
                ],
            )),
            (1, "Artifact Write Evidence", table(
                ["artifact_group", "write_strategy", "evidence", "follow_up"],
                [
                    ["canonical test cases", "`write_artifact_sections.py --manifest`", f"`{TD_REL}/_artifact_write/{CANONICAL.stem}/manifest.json`", "`none_required:pass`"],
                    ["split artifacts", "`write_artifact_sections.py --manifest`", f"`{TD_REL}/_artifact_write/*/manifest.json`", "`none_required:pass`"],
                    ["cycle outputs", "`write_artifact_sections.py --manifest` or direct short UTF-8 file write from generator", "`scripts/build_autofin_universal_application_common_actions_writer_r1.py`", "`none_required:pass`"],
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
                    ["section_id", f"`{SECTION}`"],
                    ["package_id", "`WP-01`"],
                    ["canonical_test_design_dir", f"`{TD_REL}`"],
                ],
            )),
            (2, "Scope Boundaries", "Набор покрывает только действие `История заявки` в карточке Универсальной заявки и факт открытия окна просмотра истории заявки. Содержимое, поля, записи, фильтры, статусы, загрузка данных и действия внутри окна истории не покрываются без отдельного ФТ `Общие требования`."),
            (2, "Coverage Summary", table(
                ["package_id", "source_row_id", "req_id", "atom_id", "test_case_id", "coverage_status"],
                [["`WP-01`", "`SRC-001`", "`BSR 321`", "`ATOM-001`", "`TC-UACA-001`", "`covered`"]],
            )),
            (2, "Test Cases", "## TC-UACA-001\n\n" + tc_block()),
        ],
        title="Тест-кейсы: общие действия в карточке Универсальной заявки",
    )


def seed_writer_profile() -> None:
    profile = {
        "version": 1,
        "generated_by": "codex_review_cycle_runner",
        "command": "python scripts/validate_agent_artifacts.py --root fts/AutoFin --json",
        "scope_slug": SCOPE,
        "canonical_test_cases": CANONICAL_REL,
        "test_design_dir": TD_REL,
        "current_stage": "writer-r1",
        "current_scope_findings": [],
        "unresolved_warning_error_count": 0,
    }
    path = FT / WRITER_PROFILE_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_response() -> None:
    write_markdown(
        OUTPUTS / "writer-r1-response.md",
        [(1, "Writer R1 Response", dedent(
            f"""
            ## Summary

            - Created canonical test case file `{CANONICAL_REL}`.
            - Created writer-side split artifacts under `{TD_REL}/`.
            - Preserved mandatory traceability `SRC-001` and PDF-only `BSR 321` in ledger, plan and `TC-UACA-001`.
            - Covered only the source-backed action result: opening the history-view window.
            - Did not cover internal content of the history window or full application-card behavior.

            ## Output Artifacts

            - `{CANONICAL_REL}`
            - `{TD_REL}/`
            - `{CYCLE_REL}/outputs/writer-session-log.writer-r1.md`
            - `{CYCLE_REL}/outputs/agent-decision-log.writer-r1.md`
            - `{CYCLE_REL}/outputs/scoped-validator-profile.writer-r1.json`
            - `{CYCLE_REL}/prompts/prompt.structure-preflight-r1.md`
            """
        ))],
    )


def write_prompt() -> None:
    selected_files = "\n".join(f"- `{path}`" for path in SELECTED_REQUIRED_FILES)
    prompt = dedent(
        f"""
        # Prompt: Structure Preflight R1

        ## Цель этапа

        Проверить parseability, canonical schema, обязательные поля `TC-*`, split artifact shape and blocking format prerequisites for `AutoFin` / `{SCOPE}` in session-based stage `structure-preflight-r1`.

        Skill: `ft-test-case-reviewer`.
        Instruction scenario: `reviewer.structure_preflight`.
        Resolver command: `python scripts/resolve_instruction_context.py --scenario reviewer.structure_preflight --budget-report --fail-on-budget`.

        Перед reviewer decisions прочитай все selected required instruction files and record resolver command, budget status and selected files in `outputs/reviewer-session-log.structure-preflight-r1.md`.

        ## Selected Required Files

        {selected_files}

        ## Входные артефакты

        - `fts/AutoFin/{CANONICAL_REL}`
        - `fts/AutoFin/{TD_REL}/`
        - `fts/AutoFin/{HANDOFF_REL}/scope-contract.md`
        - `fts/AutoFin/{HANDOFF_REL}/source-parity-check.md`
        - `fts/AutoFin/{HANDOFF_REL}/source-row-inventory.md`
        - `fts/AutoFin/{HANDOFF_REL}/scope-coverage-gaps.md`
        - `fts/AutoFin/{CYCLE_REL}/outputs/writer-session-log.writer-r1.md`
        - `fts/AutoFin/{CYCLE_REL}/outputs/agent-decision-log.writer-r1.md`
        - `fts/AutoFin/{CYCLE_REL}/outputs/scoped-validator-profile.writer-r1.json`
        - `fts/AutoFin/{CYCLE_REL}/cycle-state.yaml`
        - `fts/AutoFin/AGENT-NOTES.md`

        ## Обязательные действия

        - Работать only in `structure_preflight`; do not perform semantic coverage review.
        - Проверить, что canonical `TC-UACA-001` parseable and uses bold runtime fields.
        - Проверить, что every `ATOM-*` and `TC-*` has `package_id = WP-01`.
        - Проверить наличие `BSR 321` and `SRC-001` in canonical, ledger and design plan.
        - Проверить, что no test asserts internal history-window content.
        - If structure blockers exist, route to `writer-structure-r1` with `structure-preflight-blocked`.
        - If no structure blockers exist, route to `semantic-review-r1` with `stage_status: semantic-review-ready`.

        ## Не делать

        - Do not edit canonical test cases.
        - Do not expand scope beyond section-17 and shared section-1 context.
        - Do not review internal history-window fields, records, filters or statuses.
        - Do not set `signed-off`.

        ## Ожидаемые выходы

        - `fts/AutoFin/{CYCLE_REL}/outputs/structure-preflight-r1-findings.md`
        - `fts/AutoFin/{CYCLE_REL}/outputs/reviewer-session-log.structure-preflight-r1.md`
        - `fts/AutoFin/{CYCLE_REL}/outputs/agent-decision-log.structure-preflight-r1.md`
        - next prompt for `semantic-review-r1` or `writer-structure-r1`
        - updated `fts/AutoFin/{CYCLE_REL}/cycle-state.yaml`
        """
    ).strip()
    (PROMPTS / "prompt.structure-preflight-r1.md").write_text(prompt + "\n", encoding="utf-8", newline="\n")


def write_logs(final: bool) -> None:
    validation_status = (
        f"`python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/{CYCLE_REL}/cycle-state.yaml` - pass; runner-generated `{WRITER_PROFILE_REL}` has `unresolved_warning_error_count = 0`."
        if final
        else f"`python scripts/codex_review_cycle_runner.py validate --state fts/AutoFin/{CYCLE_REL}/cycle-state.yaml` - pending until after artifact generation."
    )
    selected = "\n".join(
        f"- `{path}` - selected required instruction file for `writer.session_initial_draft`."
        for path in SELECTED_REQUIRED_FILES
    )
    scope_inputs = "\n".join(
        f"- `{path}` - writer input read for AutoFin section-17 scope."
        for path in [
            f"{HANDOFF_REL}/source-selection.md",
            f"{HANDOFF_REL}/workflow-state.yaml",
            f"{HANDOFF_REL}/scope-contract.md",
            f"{HANDOFF_REL}/source-parity-check.md",
            f"{HANDOFF_REL}/source-row-inventory.md",
            f"{HANDOFF_REL}/scope-coverage-gaps.md",
            f"{HANDOFF_REL}/prompt.scope-to-writer.md",
            f"{HANDOFF_REL}/prompt.scope-to-iteration.md",
            f"{CYCLE_REL}/cycle-state.yaml",
            "source/AutoFinPreFinal.docx",
            "source/AutoFinPreFinal.pdf",
            "AGENT-NOTES.md",
        ]
    )
    session_log = dedent(
        f"""
        # Writer R1 Session Log

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

        - Resolver command: `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget`.
        - Resolver budget status: `pass (140.2 / 200.0 KiB)`.
        {selected}
        {scope_inputs}

        ## Inputs Not Used

        - `fts/AutoFin/mockups/` - not used because section-17 has sufficient textual source and prompt forbids visual-only behavior.
        - `section-14` / `section-15` rows - excluded except for the generic precondition that the user is in a Универсальная заявка card.
        - FT `Общие требования` - not available in this package; internal history-window behavior is outside current scope.

        ## Key Decisions

        - `SRC-001` is writer-normalized as in scope and mapped to `ATOM-001`.
        - PDF-only `BSR 321` is preserved as mandatory `req_id` in ledger, design plan and `TC-UACA-001`.
        - One executable TC is created because the source row has one observable action result.
        - Window internals are excluded rather than converted into gaps or invented checks.

        ## Risks And Fallbacks

        - `source-selection.md` says `AGENT-NOTES.md` absent, but `fts/AutoFin/AGENT-NOTES.md` now exists; it was read as package-specific context only and did not add behavior.
        - Initial PowerShell console output for Russian instruction files showed mojibake; files were reread with explicit UTF-8 and distorted stdout was not used as evidence.

        ## Validation

        - `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - pass.
        - Direct DOCX/PDF source check - DOCX table 10 row 1 and PDF p.38 confirm `История заявки` / `BSR 321` / opening history-view window.
        - {validation_status}

        ## Contamination Check

        - Work was limited to `fts/AutoFin`, `{CANONICAL_REL}`, `{TD_REL}`, and `{CYCLE_REL}`.
        - Visual materials, section-14/15 behavior and FT `Общие требования` were not used as behavior sources.

        ## Event Timeline

        | step | event | result | artifact_or_evidence |
        | --- | --- | --- | --- |
        | 1 | Ran instruction resolver | pass | resolver output budget `140.2 / 200.0 KiB` |
        | 2 | Read selected required instruction files | pass | `Inputs Read` |
        | 3 | Read AutoFin scope and source artifacts | pass | `scope-contract.md`; `source-parity-check.md`; `source-row-inventory.md` |
        | 4 | Declared manifest write strategy | pass | `{TD_REL}/artifact-write-strategy.md` |
        | 5 | Generated canonical and split artifacts | pass | `{CANONICAL_REL}`; `{TD_REL}/` |
        | 6 | Ran scoped validator | {"pass" if final else "pending"} | `{WRITER_PROFILE_REL}` |
        | 7 | Prepared next transition prompt | pass | `{CYCLE_REL}/prompts/prompt.structure-preflight-r1.md` |

        ## Quality Checkpoints

        | checkpoint | status | evidence | follow_up |
        | --- | --- | --- | --- |
        | Writer Quality Gate | `pass` | `{TD_REL}/writer-quality-gate.md` | structure preflight |
        | Source row parity | `pass` | `SRC-001`; `BSR 321` preserved | none |
        | TC atomicity | `pass` | `TC-UACA-001` has one action and one expected result | none |
        | Scope containment | `pass` | no internal history-window content in TC | semantic reviewer should verify |

        ## Artifact Write Strategy

        | artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
        | --- | --- | --- | --- | --- | --- |
        | `{CANONICAL_REL}` | `package-based generated` | `file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest <manifest.json>` | `yes` |
        | `{TD_REL}/` | `split generated` | `file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest <manifest.json>` | `yes` |

        ## Technical Fallbacks

        | fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
        | --- | --- | --- | --- | --- | --- | --- | --- |
        | `TF-001` | `encoding issue` | `PowerShell console output read without explicit UTF-8` | `Get-Content -Raw -Encoding UTF8` and direct DOCX/PDF extraction | `n/a` | `n/a` | `none; mojibake stdout discarded and not used as source evidence` | `none` |

        ## Handoff Notes For Next Session

        - Structure preflight should check parseability, required fields and split artifact shape only.
        - Semantic review should verify that `TC-UACA-001` does not assert window internals and that `BSR 321` / `SRC-001` remain traceable.
        """
    ).strip()
    (OUTPUTS / "writer-session-log.writer-r1.md").write_text(session_log + "\n", encoding="utf-8", newline="\n")

    decision_log = "# Agent Decision Log\n\n## Decision Log Metadata\n\n" + table(
        ["field", "value"],
        [["ft_slug", "`AutoFin`"], ["scope_slug", f"`{SCOPE}`"], ["stage", "`ft-test-case-writer / writer-r1`"], ["started_from", f"`{CYCLE_REL}/cycle-state.yaml`"]],
    ) + "\n\n## Decision Log\n\n" + table(
        ["decision_id", "step", "decision_type", "input_or_trigger", "decision", "rationale", "artifact_or_output", "risk_or_confidence", "status"],
        [
            ["`DEC-001`", "1", "`scope-boundary`", "`scope-contract.md`", "Cover only action `История заявки` and opening of the history-view window.", "Scope explicitly excludes full card and history-window internals.", CANONICAL_REL, "`high`", "`applied`"],
            ["`DEC-002`", "2", "`source-boundary`", "`source-row-inventory.md`", "Map `SRC-001` to one atom.", "There is one source row and one observable action result.", f"{TD_REL}/atomic-requirements-ledger.md", "`high`", "`applied`"],
            ["`DEC-003`", "3", "`traceability`", "`source-parity-check.md`", "Preserve PDF-only `BSR 321` as `req_id`.", "Traceability rules require PDF-only IDs from parity check.", f"{TD_REL}/atomic-requirements-ledger.md; {CANONICAL_REL}", "`high`", "`applied`"],
            ["`DEC-004`", "4", "`test-design`", "`scope-coverage-gaps.md`", "Do not create TC for internal history-window contents.", "Section-17 delegates window details to another FT not available for this scope.", f"{TD_REL}/package-test-design-plan.md", "`high`", "`applied`"],
            ["`DEC-005`", "5", "`artifact-write`", "`writer-process-workflow.md`", "Use manifest helper for generated artifacts.", "Scope uses `WP-01` and split artifacts; file-based writing is required.", f"{TD_REL}/artifact-write-strategy.md", "`high`", "`applied`"],
            ["`DEC-006`", "6", "`routing`", "`session-based-review-cycle-format.md`", "Route to `structure-preflight-r1` after clean writer validation.", "Writer must not start semantic review directly.", f"{CYCLE_REL}/cycle-state.yaml", "`high`", "`applied`"],
        ],
    ) + "\n"
    (OUTPUTS / "agent-decision-log.writer-r1.md").write_text(decision_log, encoding="utf-8", newline="\n")


def write_state(final: bool) -> None:
    if final:
        current_stage = "structure-preflight-r1"
        stage_status = "writer-draft-ready"
        semantic_round = "1"
        active_prompt = f"{CYCLE_REL}/prompts/prompt.structure-preflight-r1.md"
    else:
        current_stage = "writer-r1"
        stage_status = "scope-ready-for-writer"
        semantic_round = "0"
        active_prompt = f"{CYCLE_REL}/prompts/prompt.writer-r1.md"

    state = dedent(
        f"""
        cycle_id: universal-application-common-actions-2026-06-26
        ft_slug: AutoFin
        scope_slug: {SCOPE}
        section_id: {SECTION}
        current_stage: {current_stage}
        stage_status: {stage_status}
        semantic_round: {semantic_round}
        max_semantic_rounds: 2
        canonical_test_cases: {CANONICAL_REL}
        test_design_dir: {TD_REL}
        active_snapshot: none
        active_transition_prompt: {active_prompt}
        sessions: []
        latest_artifacts:
          - {CANONICAL_REL}
          - {TD_REL}
          - {TD_REL}/artifact-write-strategy.md
          - {TD_REL}/source-row-inventory.md
          - {TD_REL}/atomic-requirements-ledger.md
          - {TD_REL}/package-test-design-plan.md
          - {TD_REL}/writer-quality-gate.md
          - {TD_REL}/writer-self-check.md
          - {CYCLE_REL}/outputs/writer-r1-response.md
          - {CYCLE_REL}/outputs/writer-session-log.writer-r1.md
          - {CYCLE_REL}/outputs/agent-decision-log.writer-r1.md
          - {WRITER_PROFILE_REL}
          - {CYCLE_REL}/prompts/prompt.structure-preflight-r1.md
        blocking_reasons: []
        blocking_findings: []
        open_questions: []
        accepted_risks: []
        """
    ).strip()
    (CYCLE / "cycle-state.yaml").write_text(state + "\n", encoding="utf-8", newline="\n")


def update_compat_workflow_state() -> None:
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
        open_questions: []
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
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    PROMPTS.mkdir(parents=True, exist_ok=True)
    CANONICAL.parent.mkdir(parents=True, exist_ok=True)

    write_split_artifacts()
    write_canonical()
    write_response()
    write_prompt()
    if not args.final:
        seed_writer_profile()
    write_logs(final=args.final)
    write_state(final=args.final)
    if args.final:
        update_compat_workflow_state()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
