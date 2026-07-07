from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT_DIR / "scripts" / "collect_clean_run_evidence.py"


class CollectCleanRunEvidenceTests(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def write_inventory(self, path: Path, rows: list[tuple[str, str]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        table_rows = [
            "# Source Row Inventory",
            "",
            "| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for source_row_id, in_scope in rows:
            table_rows.append(f"| {source_row_id} | WP-01 | Field {source_row_id} | PDF p.1 | GSR 1 | {in_scope} | ATOM-001 |")
        path.write_text("\n".join(table_rows), encoding="utf-8")

    def write_test_case_file(self, path: Path, writer_source_rows: list[str]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = [
            "## Source Row Inventory",
            "",
            "| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for source_row_id in writer_source_rows:
            rows.append(f"| {source_row_id} | WP-01 | Field {source_row_id} | PDF p.1 | GSR 1 | yes | ATOM-001 |")
        path.write_text(
            "\n".join(
                [
                    "# Sample",
                    "",
                    *rows,
                    "",
                    "## Atomic Requirements Ledger",
                    "",
                    "| atom_id | package_id | requirement | coverage_status | covered_by_tc | gap_note |",
                    "| --- | --- | --- | --- | --- | --- |",
                    "| ATOM-001 | WP-01 | Requirement | covered | TC-SAMPLE-001 | - |",
                    "",
                    "## TC-SAMPLE-001",
                    "**Title:** Sample",
                    "**Expected Result:** Result.",
                    "**FT Reference:** `GSR 1`",
                ]
            ),
            encoding="utf-8",
        )

    def append_safe_artifact_write_strategy(self, path: Path) -> None:
        path.write_text(
            path.read_text(encoding="utf-8")
            + "\n\n"
            + "\n".join(
                [
                    "## Artifact Write Strategy",
                    "",
                    "| item | value | evidence |",
                    "| --- | --- | --- |",
                    "| preflight_result | `small-fixture` | `test fixture` |",
                    "| write_method | `file-based chunked writing` | `scripts/write_artifact_sections.py --manifest artifact-sections.json` |",
                    "| forbidden_methods_checked | `yes` | no one-shot PowerShell command, no here-string |",
                    "| chunk_plan | `WP-01` | one fixture package |",
                    "| helper_artifacts | `none` | no ad-hoc tmp generator |",
                    "| validation_plan | `final` | validator after write |",
                ]
            ),
            encoding="utf-8",
        )

    def append_passing_writer_quality_gate(self, path: Path) -> None:
        profile_path = path.parent / "scoped-validator-profile.writer-r1.json"
        profile_path.write_text(
            json.dumps(
                {
                    "command": "python scripts/validate_agent_artifacts.py --root test-cases/sample.md --json",
                    "generated_by": "codex_review_cycle_runner",
                    "scope_slug": "ui-main-info",
                    "canonical_test_cases": path.name,
                    "test_design_dir": "test-cases",
                    "current_scope_findings": [],
                    "unresolved_warning_error_count": 0,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        path.write_text(
            path.read_text(encoding="utf-8")
            + "\n\n"
            + "\n".join(
                [
                    "## Writer Quality Gate",
                    "",
                    "| gate_item | status | evidence | affected_package | required_action | blocks_ready_for_review |",
                    "| --- | --- | --- | --- | --- | --- |",
                    "| `artifact-write-strategy` | `pass` | Проверено | `WP-01` | - | `no` |",
                    "| `mockup-visual-inventory` | `pass` | Для fixture не применимо | `WP-01` | - | `no` |",
                    "| `source-row-inventory` | `pass` | В fixture нет handoff inventory | `WP-01` | - | `no` |",
                    "| `source-normalization-atomic` | `pass` | Проверено | `WP-01` | - | `no` |",
                    "| `test-design-decision-table` | `pass` | Проверено | `WP-01` | - | `no` |",
                    "| `test-design-review` | `pass` | Проверено | `WP-01` | - | `no` |",
                    "| `gap-admissibility` | `pass` | Проверено | `WP-01` | - | `no` |",
                    "| `ledger-atomicity` | `pass` | Проверено | `WP-01` | - | `no` |",
                    "| `gsr-range-compression` | `pass` | Проверено | `WP-01` | - | `no` |",
                    "| `design-plan-atomicity` | `pass` | Проверено | `WP-01` | - | `no` |",
                    "| `scenario-does-not-replace-atomic` | `pass` | Проверено | `WP-01` | - | `no` |",
                    "| `tc-atomicity` | `pass` | Проверено | `WP-01` | - | `no` |",
                    "| `test-data-specificity` | `pass` | Проверено | `WP-01` | - | `no` |",
                    "| `internal-observability` | `pass` | Проверено | `WP-01` | - | `no` |",
                    "| `action-observability` | `pass` | Проверено | `WP-01` | - | `no` |",
                    "| `semantic-req-id-parity` | `pass` | Проверено | `WP-01` | - | `no` |",
                    "| `scoped-validator-findings` | `pass` | `scoped-validator-profile.writer-r1.json`: unresolved_warning_error_count=0 | `WP-01` | none_required:pass | `no` |",
                    "| `package-ready` | `pass` | Проверено | `WP-01` | - | `no` |",
                ]
            ),
            encoding="utf-8",
        )
        content = path.read_text(encoding="utf-8")
        path.write_text(
            content.replace(" | - | `no` |", " | none_required:pass | `no` |"),
            encoding="utf-8",
        )

    def append_passing_test_design_review(self, path: Path) -> None:
        path.write_text(
            path.read_text(encoding="utf-8")
            + "\n\n"
            + "\n".join(
                [
                    "## Test Design Review",
                    "",
                    "| review_item | status | severity | affected_package | evidence | required_action | blocks_ready_for_review |",
                    "| --- | --- | --- | --- | --- | --- | --- |",
                    "| `decision-table-classification` | `pass` | `info` | `WP-01` | Проверено | - | `no` |",
                    "| `ledger-plan-alignment` | `pass` | `info` | `WP-01` | Проверено | - | `no` |",
                    "| `coverage-class-completeness` | `pass` | `info` | `WP-01` | Проверено | - | `no` |",
                    "| `numeric-length-boundaries` | `pass` | `info` | `WP-01` | Проверено | - | `no` |",
                    "| `unsupported-ui-mechanism` | `pass` | `info` | `WP-01` | Проверено | - | `no` |",
                    "| `mask-format-coverage` | `pass` | `info` | `WP-01` | Проверено | - | `no` |",
                    "| `dictionary-closed-set` | `pass` | `info` | `WP-01` | Проверено | - | `no` |",
                    "| `conditional-branches` | `pass` | `info` | `WP-01` | Проверено | - | `no` |",
                    "| `negative-fixture-isolation` | `pass` | `info` | `WP-01` | Проверено | - | `no` |",
                    "| `applicability-linked-tc-semantics` | `pass` | `info` | `WP-01` | Проверено | - | `no` |",
                    "| `gap-specificity` | `pass` | `info` | `WP-01` | Проверено | - | `no` |",
                    "| `gap-admissibility` | `pass` | `info` | `WP-01` | Проверено | - | `no` |",
                    "| `internal-observability` | `pass` | `info` | `WP-01` | Проверено | - | `no` |",
                    "| `metadata-only-exclusion` | `pass` | `info` | `WP-01` | Проверено | - | `no` |",
                    "| `tc-mapping-atomicity` | `pass` | `info` | `WP-01` | Проверено | - | `no` |",
                    "| `coverage-depth-profile-selection` | `pass` | `info` | `WP-01` | Проверено | - | `no` |",
                    "| `artifact-mode-appropriateness` | `pass` | `info` | `WP-01` | Проверено | - | `no` |",
                    "| `over-testing-risk` | `pass` | `info` | `WP-01` | Проверено | - | `no` |",
                    "| `excessive-tc-fragmentation` | `pass` | `info` | `WP-01` | Проверено | - | `no` |",
                    "| `duplicate-tc-risk` | `pass` | `info` | `WP-01` | Проверено | - | `no` |",
                    "| `manual-execution-cost` | `pass` | `info` | `WP-01` | Проверено | - | `no` |",
                    "| `core-vs-deep-coverage-separation` | `pass` | `info` | `WP-01` | Проверено | - | `no` |",
                    "| `ready-for-tc-writing` | `pass` | `info` | `WP-01` | Проверено | - | `no` |",
                ]
            ),
            encoding="utf-8",
        )
        content = path.read_text(encoding="utf-8")
        path.write_text(
            content.replace(" | - | `no` |", " | none_required:pass | `no` |"),
            encoding="utf-8",
        )

    def write_writer_pass_artifacts(self, fixture_root: Path, *, ft_slug: str = "ft-2-OF_11") -> None:
        handoff_dir = fixture_root / "work" / "stage-handoffs" / "01-ui-main-info"
        test_case_path = fixture_root / "test-cases" / "sample.md"
        test_case_path.parent.mkdir(parents=True, exist_ok=True)
        test_case_path.write_text(
            "\n".join(
                [
                    "# Sample",
                    "",
                    "## Source Row Inventory",
                    "",
                    "| source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap |",
                    "| --- | --- | --- | --- | --- | --- | --- |",
                    "| SRC-001 | WP-01 | Field SRC-001 | PDF p.1 | GSR 1 | yes | ATOM-001 |",
                    "",
                    "## Atomic Requirements Ledger",
                    "",
                    "| atom_id | package_id | requirement | coverage_status | covered_by_tc | gap_note |",
                    "| --- | --- | --- | --- | --- | --- |",
                    "| ATOM-001 | WP-01 | Numeric value is accepted. | covered | TC-SAMPLE-001 | not_applicable:covered |",
                    "",
                    "## Package Test Design Plan",
                    "",
                    "| design_item_id | package_id | design_dimension | source_ref | linked_atoms | planned_check | check_type | coverage_class | input_class | single_expected_behavior | oracle_source | planned_tc_or_gap | status |",
                    "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                    "| PD-001 | WP-01 | format | GSR 1 | ATOM-001 | Enter numeric value | positive | equivalence | numeric | Numeric value is accepted | FT 1 | TC-SAMPLE-001 | planned |",
                    "",
                    "## TC-SAMPLE-001",
                    "**package_id:** `WP-01`",
                    "**Title:** Numeric value is accepted",
                    "**Priority:** High",
                    "**Type:** Positive",
                    "**Goal:** Verify `ATOM-001`.",
                    "**Preconditions:**",
                    "- Form is open.",
                    "**Test Data:**",
                    "- `123`.",
                    "**Steps:**",
                    "1. Enter `123` into the field.",
                    "**Expected Result:** Numeric value is accepted.",
                    "**Postconditions:**",
                    "- Clear the field.",
                    "**FT Reference:** `GSR 1`",
                    "**Requirement Source:**",
                    "- `FT 1`",
                    "**Requirement Source Quote:** Numeric value is accepted.",
                ]
            ),
            encoding="utf-8",
        )
        self.append_safe_artifact_write_strategy(test_case_path)
        self.append_passing_test_design_review(test_case_path)
        self.append_passing_writer_quality_gate(test_case_path)
        self.write_valid_session_log(
            handoff_dir / "writer-session-log.md",
            skill="ft-test-case-writer",
            ft_slug=ft_slug,
            status_after="ready-for-review",
        )
        self.write_valid_decision_log(handoff_dir / "agent-decision-log.md", ft_slug=ft_slug, stage="ft-test-case-writer")
        (handoff_dir / "prompt.writer-to-reviewer.round-1.md").write_text(
            "\n".join(
                [
                    "# Writer To Reviewer",
                    "",
                    "## Goal",
                    "",
                    "Review the canonical test cases.",
                    "",
                    "## Inputs",
                    "",
                    "- `test-cases/sample.md`",
                    "",
                    "## Guardrails",
                    "",
                    "- Do not infer expected behavior outside FT sources.",
                ]
            ),
            encoding="utf-8",
        )
        (handoff_dir / "workflow-state.yaml").write_text(
            "\n".join(
                [
                    f"ft_slug: {ft_slug}",
                    "scope_slug: ui-main-info",
                    "current_stage: ft-test-case-writer",
                    "stage_status: ready-for-review",
                    "current_round: 1",
                    "next_skill: ft-test-case-reviewer",
                    "required_inputs:",
                    "  - ../../../test-cases/sample.md",
                    "  - prompt.writer-to-reviewer.round-1.md",
                    "  - agent-decision-log.md",
                    "latest_artifacts:",
                    "  test_cases: ../../../test-cases/sample.md",
                    "  prompt_writer_to_reviewer: prompt.writer-to-reviewer.round-1.md",
                    "  session_log: writer-session-log.md",
                    "  decision_log: agent-decision-log.md",
                    "coverage_gaps:",
                    "  total: 0",
                    "  blocking: 0",
                    "open_questions: []",
                    "blocking_reasons: []",
                    "accepted_risks: []",
                ]
            ),
            encoding="utf-8",
        )

    def write_workflow_state(
        self,
        path: Path,
        *,
        current_stage: str,
        stage_status: str,
        next_skill: str,
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(
                [
                    f"current_stage: {current_stage}",
                    f"stage_status: {stage_status}",
                    f"next_skill: {next_skill}",
                ]
            ),
            encoding="utf-8",
        )

    def write_minimal_file(self, path: Path, content: str = "placeholder\n") -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def write_valid_source_selection(self, path: Path, *, ft_slug: str = "ft-2-OF_11") -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        handoff_root = path.parent
        while handoff_root.name != "work" and handoff_root != handoff_root.parent:
            handoff_root = handoff_root.parent
        source_dir = (handoff_root.parent if handoff_root.name == "work" else path.parent) / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        (source_dir / "main.xhtml").write_text("<html><body>Main FT</body></html>\n", encoding="utf-8")
        path.write_text(
            "\n".join(
                [
                    "# Source Selection",
                    "",
                    "## Context",
                    "",
                    "- request_summary: Clean-run source locator fixture.",
                    f"- selected_ft_slug: {ft_slug}",
                    "- selection_status: `selected`",
                    "- created_at: 2026-05-28",
                    "- created_by: test",
                    "",
                    "## Main FT Documents",
                    "",
                    "| path | role | selection_reason | version_or_date | source_quality_notes |",
                    "| --- | --- | --- | --- | --- |",
                    "| `source/main.docx` | main-ft-docx | DOCX remains source of truth | v1 | parseable |",
                    "| `source/main.xhtml` | main-ft-xhtml | Mandatory machine-readable extraction source | v1 | primary extraction |",
                    "",
                    "## Machine-Readable XHTML Source",
                    "",
                    "- xhtml_available: `yes`",
                    "- xhtml_path: `source/main.xhtml`",
                    "- xhtml_matches_main_ft: `yes`",
                    "- xhtml_extraction_priority: `primary`",
                    "- xhtml_required_for_downstream: `yes`",
                    "- limitation: none",
                    "- blocking_reason: none",
                    "",
                    "## Structural Cross-Check PDF",
                    "",
                    "- pdf_available: `no`",
                    "- pdf_path: `-`",
                    "- pdf_matches_main_ft: `not-checked`",
                    "- limitation: No PDF in fixture.",
                    "",
                    "## Support Files And Mockups",
                    "",
                    "| path | role | why_relevant | must_use_downstream | limitations |",
                    "| --- | --- | --- | --- | --- |",
                    "| `AGENT-NOTES.md` | package-context | Fixture package notes | yes | none |",
                    "",
                    "## Source Quality",
                    "",
                    "- active source documents: `source/main.docx`",
                    "- parseability: `ok`",
                    "- section-id confidence: `high`",
                    "- oversized blocks: `none`",
                    "- strict warnings: `0`",
                    "",
                    "## Ambiguity And Decision Log",
                    "",
                    "| candidate | issue | required_decision |",
                    "| --- | --- | --- |",
                    "| `source/main.docx` | none | selected |",
                    "",
                    "## Handoff",
                    "",
                    "- next_skill: `ft-scope-analyzer`",
                    "- required_inputs: `source-selection.md`",
                    "- latest_artifacts: `source-selection.md`",
                    "- blocked_reasons: `none`",
                ]
            ),
            encoding="utf-8",
        )

    def write_valid_session_log(
        self,
        path: Path,
        *,
        skill: str,
        ft_slug: str = "ft-2-OF_11",
        status_after: str = "ready-for-next-stage",
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        clean_boundary_note = (
            f"`fts/{ft_slug}` is the selected package; neighboring `fts/ft-2-OF*` "
            "baseline packages were not opened and not used."
        )
        path.write_text(
            "\n".join(
                [
                    "# Stage Session Log",
                    "",
                    "## Session Metadata",
                    "",
                    "| field | value |",
                    "| --- | --- |",
                    f"| skill | `{skill}` |",
                    "| mode | `test` |",
                    f"| ft_slug | `{ft_slug}` |",
                    "| scope_slug | `sample-scope` |",
                    "| started_from | `workflow-state.yaml` |",
                    f"| status_after | `{status_after}` |",
                    "",
                    "## Inputs Read",
                    "",
                    "- `workflow-state.yaml` - stage state.",
                    "",
                    "## Inputs Not Used",
                    "",
                    f"- {clean_boundary_note}",
                    "",
                    "## Key Decisions",
                    "",
                    "- Used current package artifacts only.",
                    "",
                    "## Risks And Fallbacks",
                    "",
                    "- `none` - no fallback.",
                    "",
                    "## Validation",
                    "",
                    "- `validator` - passed.",
                    "",
                    "## Contamination Check",
                    "",
                    f"- {clean_boundary_note}",
                    "",
                    "## Event Timeline",
                    "",
                    "| step | event | result | artifact_or_evidence |",
                    "| --- | --- | --- | --- |",
                    "| 1 | Created session log before stage work | Log exists | `session log` |",
                    "| 2 | Ran validation | Passed | `validator` |",
                    "",
                    "## Quality Checkpoints",
                    "",
                    "| checkpoint | status | evidence | follow_up |",
                    "| --- | --- | --- | --- |",
                    "| Stage boundary | pass | current-stage artifacts only | none |",
                    "",
                    "## Technical Fallbacks",
                    "",
                    "| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |",
                    "| --- | --- | --- | --- | --- | --- | --- | --- |",
                    "| `none` | `none` | `none` | `none` | `n/a` | `n/a` | `none` | `none` |",
                    "",
                    "## Handoff Notes For Next Session",
                    "",
                    "- `none` - no open doubts in this fixture.",
                ]
            ),
            encoding="utf-8",
        )

    def write_valid_decision_log(
        self,
        path: Path,
        *,
        ft_slug: str = "ft-2-OF_11",
        stage: str = "ft-test-case-writer",
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(
                [
                    "# Agent Decision Log",
                    "",
                    "## Decision Log Metadata",
                    "",
                    "| field | value |",
                    "| --- | --- |",
                    f"| ft_slug | `{ft_slug}` |",
                    "| scope_slug | `sample-scope` |",
                    f"| stage | `{stage}` |",
                    "| started_from | `workflow-state.yaml` |",
                    "",
                    "## Decision Log",
                    "",
                    "| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |",
                    "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                    "| `DEC-001` | 1 | `scope-boundary` | `workflow-state.yaml` | Use current fixture scope | Clean-run evidence must not depend on chat | `workflow-state.yaml` | high | applied |",
                ]
            ),
            encoding="utf-8",
        )

    def write_source_locator_workflow_state(self, path: Path, *, ft_slug: str = "ft-2-OF_11") -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(
                [
                    f"ft_slug: {ft_slug}",
                    "scope_slug: 00-scope-selection",
                    "current_stage: ft-source-locator",
                    "stage_status: ready-for-next-stage",
                    "current_round: 0",
                    "next_skill: ft-scope-analyzer",
                    "required_inputs:",
                    "  - source-selection.md",
                    "  - agent-decision-log.md",
                    "latest_artifacts:",
                    "  source_selection: source-selection.md",
                    "  session_log: source-locator-session-log.md",
                    "  decision_log: agent-decision-log.md",
                    "open_questions: []",
                    "blocking_reasons: []",
                ]
            ),
            encoding="utf-8",
        )

    def write_agent_proposed_scope_artifacts(self, handoff_dir: Path, *, ft_slug: str = "ft-2-OF_11") -> None:
        self.write_valid_source_selection(handoff_dir / "source-selection.md", ft_slug=ft_slug)
        self.write_valid_session_log(
            handoff_dir / "scope-analyzer-session-log.md",
            skill="ft-scope-analyzer",
            ft_slug=ft_slug,
            status_after="blocked-input",
        )
        self.write_valid_decision_log(handoff_dir / "agent-decision-log.md", ft_slug=ft_slug, stage="ft-scope-analyzer")
        (handoff_dir / "scope-options.md").write_text(
            "\n".join(
                [
                    f"# Scope Options For `{ft_slug}`",
                    "",
                    "## Context",
                    "",
                    f"- FT package: `fts/{ft_slug}`",
                    "- Main source: `source/main.docx`",
                    "- Mode: `agent-proposed-scope`",
                    "",
                    "## Candidate Scope",
                    "",
                    "### SCOPE-OPTION-001",
                    "**Scope Order:** `01`",
                    "**Scope Slug:** `ui-main-info`",
                    "**Stage Handoff Dir:** `01-ui-main-info`",
                    "**Title:** Main information UI fields",
                    "**Source Path:** `2.3`",
                    "",
                    "**What is included:** Field properties.",
                    "**What is excluded:** Other UI sections.",
                    "**Why separate:** UI field-property scope.",
                    "**Approximate complexity:** `medium`",
                    "**Risks / Coverage Gaps:** none.",
                    "**Recommended next step:** choose this scope.",
                    "",
                    "## Recommendation",
                    "",
                    "- Start with `ui-main-info`.",
                    "",
                    "## What User Must Do Next",
                    "",
                    "- Choose one candidate scope.",
                ]
            ),
            encoding="utf-8",
        )
        (handoff_dir / "scope-selection-prompts.md").write_text(
            "\n".join(
                [
                    f"# Scope Selection Prompts For `{ft_slug}`",
                    "",
                    "## How To Use",
                    "",
                    "- Choose one candidate scope from `scope-options.md`.",
                    "- Use the matching prompt below.",
                    "",
                    "## Prompt Templates",
                    "",
                    "### SCOPE-OPTION-001",
                    "**Scope Order:** `01`",
                    "**Scope Slug:** `ui-main-info`",
                    "**Stage Handoff Dir:** `01-ui-main-info`",
                    "",
                    "```md",
                    f"Continue workflow for `fts/{ft_slug}`.",
                    "Run only `ft-scope-analyzer` in manual-scope mode.",
                    "Scope: `ui-main-info`.",
                    "Do not write test cases.",
                    "```",
                ]
            ),
            encoding="utf-8",
        )
        (handoff_dir / "workflow-state.yaml").write_text(
            "\n".join(
                [
                    f"ft_slug: {ft_slug}",
                    "scope_slug: scope-selection",
                    "current_stage: ft-scope-analyzer",
                    "stage_status: blocked-input",
                    "current_round: 0",
                    "next_skill: ft-scope-analyzer",
                    "required_inputs:",
                    "  - source-selection.md",
                    "  - scope-options.md",
                    "  - scope-selection-prompts.md",
                    "  - agent-decision-log.md",
                    "latest_artifacts:",
                    "  source_selection: source-selection.md",
                    "  scope_options: scope-options.md",
                    "  scope_selection_prompts: scope-selection-prompts.md",
                    "  session_log: scope-analyzer-session-log.md",
                    "  decision_log: agent-decision-log.md",
                    "open_questions:",
                    "  - Choose one candidate scope.",
                    "blocking_reasons:",
                    "  - SCOPE-SELECTION-REQUIRED: choose one candidate scope before downstream work.",
                ]
            ),
            encoding="utf-8",
        )

    def write_confirmed_scope_artifacts(self, handoff_dir: Path, *, ft_slug: str = "ft-2-OF_11") -> None:
        self.write_valid_source_selection(handoff_dir / "source-selection.md", ft_slug=ft_slug)
        self.write_valid_session_log(
            handoff_dir / "scope-analyzer-session-log.md",
            skill="ft-scope-analyzer",
            ft_slug=ft_slug,
            status_after="ready-for-next-stage",
        )
        self.write_valid_decision_log(handoff_dir / "agent-decision-log.md", ft_slug=ft_slug, stage="ft-scope-analyzer")
        (handoff_dir / "scope-contract.md").write_text(
            "\n".join(
                [
                    "# Scope Contract",
                    "",
                    "## Scope Identity",
                    "",
                    f"- ft_slug: `{ft_slug}`",
                    "- scope_slug: `ui-main-info`",
                    "- scope_mode: `manual-scope`",
                    "",
                    "## In Scope",
                    "",
                    "- Field properties for the main information UI section.",
                    "",
                    "## Out Of Scope",
                    "",
                    "- Other UI sections.",
                    "- Reviewer and writer artifacts.",
                ]
            ),
            encoding="utf-8",
        )
        (handoff_dir / "scope-coverage-gaps.md").write_text(
            "\n".join(
                [
                    "# Scope Coverage Gaps",
                    "",
                    "- Gaps: `0`",
                    "- Blocking gaps: `no`",
                ]
            ),
            encoding="utf-8",
        )
        (handoff_dir / "prompt.scope-to-iteration.md").write_text(
            "\n".join(
                [
                    "# Prompt",
                    "",
                    "## Goal",
                    "",
                    "Run the iteration stage for the confirmed scope.",
                    "",
                    "## Inputs",
                    "",
                    "- `source-selection.md`",
                    "- `scope-contract.md`",
                    "- `scope-coverage-gaps.md`",
                    "",
                    "## Guardrails",
                    "",
                    "- Do not expand scope.",
                    "- Do not use neighboring packages.",
                ]
            ),
            encoding="utf-8",
        )
        (handoff_dir / "workflow-state.yaml").write_text(
            "\n".join(
                [
                    f"ft_slug: {ft_slug}",
                    "scope_slug: ui-main-info",
                    "current_stage: ft-scope-analyzer",
                    "stage_status: ready-for-next-stage",
                    "current_round: 0",
                    "next_skill: ft-test-case-iteration",
                    "required_inputs:",
                    "  - source-selection.md",
                    "  - scope-contract.md",
                    "  - scope-coverage-gaps.md",
                    "  - prompt.scope-to-iteration.md",
                    "  - agent-decision-log.md",
                    "latest_artifacts:",
                    "  source_selection: source-selection.md",
                    "  scope_contract: scope-contract.md",
                    "  scope_coverage_gaps: scope-coverage-gaps.md",
                    "  prompt_scope_to_iteration: prompt.scope-to-iteration.md",
                    "  session_log: scope-analyzer-session-log.md",
                    "  decision_log: agent-decision-log.md",
                    "open_questions: []",
                    "blocking_reasons: []",
                ]
            ),
            encoding="utf-8",
        )

    def test_empty_package_assessment_is_not_started(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = self.run_script("--root", tmp_dir, "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assessment = payload["clean_run_assessment"]
        self.assertEqual("not-started", assessment["stage"])
        self.assertEqual("pending", assessment["status"])
        self.assertEqual("Prompt 1: Source Locator", assessment["next_expected_prompt"])
        self.assertIn("ft-source-locator", assessment["next_prompt_text"])
        self.assertIn("fts\\ft-2-OF_11", assessment["next_prompt_text"])

    def test_source_locator_assessment_passes_for_valid_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            fixture_root = Path(tmp_dir)
            handoff_dir = fixture_root / "work" / "stage-handoffs" / "00-scope-selection"
            self.write_valid_source_selection(handoff_dir / "source-selection.md")
            self.write_valid_session_log(
                handoff_dir / "source-locator-session-log.md",
                skill="ft-source-locator",
            )
            self.write_valid_decision_log(handoff_dir / "agent-decision-log.md", stage="ft-source-locator")
            self.write_source_locator_workflow_state(handoff_dir / "workflow-state.yaml")

            result = self.run_script(
                "--root",
                str(fixture_root),
                "--json",
                "--expect-stage",
                "source-locator",
                "--expect-status",
                "pass",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assessment = payload["clean_run_assessment"]
        self.assertEqual("source-locator", assessment["stage"])
        self.assertEqual("pass", assessment["status"])
        self.assertEqual([], assessment["reasons"])
        self.assertEqual("Prompt 2: Scope Selection", assessment["next_expected_prompt"])

    def test_agent_proposed_scope_assessment_passes_for_valid_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            fixture_root = Path(tmp_dir)
            handoff_dir = fixture_root / "work" / "stage-handoffs" / "00-scope-selection"
            self.write_agent_proposed_scope_artifacts(handoff_dir)

            result = self.run_script(
                "--root",
                str(fixture_root),
                "--json",
                "--expect-stage",
                "agent-proposed-scope",
                "--expect-status",
                "pass",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assessment = payload["clean_run_assessment"]
        self.assertEqual("agent-proposed-scope", assessment["stage"])
        self.assertEqual("pass", assessment["status"])
        self.assertEqual([], assessment["reasons"])
        self.assertEqual("Prompt 3: Confirm ui-main-info", assessment["next_expected_prompt"])

    def test_confirmed_scope_assessment_passes_for_valid_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            fixture_root = Path(tmp_dir)
            handoff_dir = fixture_root / "work" / "stage-handoffs" / "01-ui-main-info"
            self.write_confirmed_scope_artifacts(handoff_dir)

            result = self.run_script(
                "--root",
                str(fixture_root),
                "--json",
                "--expect-stage",
                "confirmed-scope",
                "--expect-status",
                "pass",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assessment = payload["clean_run_assessment"]
        self.assertEqual("confirmed-scope", assessment["stage"])
        self.assertEqual("pass", assessment["status"])
        self.assertEqual([], assessment["reasons"])
        self.assertEqual("Prompt 4: Writer Pass", assessment["next_expected_prompt"])

    def test_writer_pass_assessment_passes_for_valid_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            fixture_root = Path(tmp_dir)
            self.write_writer_pass_artifacts(fixture_root)

            result = self.run_script(
                "--root",
                str(fixture_root),
                "--json",
                "--expect-stage",
                "writer-pass",
                "--expect-status",
                "pass",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assessment = payload["clean_run_assessment"]
        self.assertEqual("writer-pass", assessment["stage"])
        self.assertEqual("pass", assessment["status"])
        self.assertEqual([], assessment["reasons"])
        self.assertEqual("Independent full review", assessment["next_expected_prompt"])

    def test_source_locator_assessment_fails_on_premature_scope_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            fixture_root = Path(tmp_dir)
            handoff_dir = fixture_root / "work" / "stage-handoffs" / "00-scope-selection"
            self.write_workflow_state(
                handoff_dir / "workflow-state.yaml",
                current_stage="ft-source-locator",
                stage_status="ready-for-next-stage",
                next_skill="ft-scope-analyzer",
            )
            self.write_minimal_file(handoff_dir / "source-selection.md")
            self.write_minimal_file(handoff_dir / "source-locator-session-log.md")
            self.write_minimal_file(handoff_dir / "scope-contract.md")

            result = self.run_script("--root", str(fixture_root), "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assessment = payload["clean_run_assessment"]
        self.assertEqual("source-locator", assessment["stage"])
        self.assertEqual("fail", assessment["status"])
        self.assertIn("work/stage-handoffs/00-scope-selection/scope-contract.md", assessment["forbidden_present"])

    def test_collects_missing_handoff_source_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            fixture_root = Path(tmp_dir)
            self.write_inventory(
                fixture_root / "work" / "stage-handoffs" / "01-ui-main-info" / "source-row-inventory.md",
                [("SRC-001", "yes"), ("SRC-002", "yes"), ("SRC-003", "no")],
            )
            self.write_test_case_file(fixture_root / "test-cases" / "sample.md", ["SRC-001"])

            result = self.run_script("--root", str(fixture_root), "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(["SRC-002"], payload["source_row_inventory"]["missing_handoff_source_rows_in_writer"])
        self.assertEqual(2, payload["source_row_inventory"]["handoff_required_row_count"])
        self.assertEqual(1, payload["source_row_inventory"]["writer_row_count"])
        self.assertEqual(1, payload["test_case_metrics"]["tc_count"])
        self.assertEqual(1, payload["test_case_metrics"]["atom_count"])

    def test_writer_assessment_fails_on_missing_handoff_source_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            fixture_root = Path(tmp_dir)
            handoff_dir = fixture_root / "work" / "stage-handoffs" / "01-ui-main-info"
            self.write_workflow_state(
                handoff_dir / "workflow-state.yaml",
                current_stage="ft-test-case-writer",
                stage_status="ready-for-review",
                next_skill="ft-test-case-reviewer",
            )
            self.write_inventory(
                handoff_dir / "source-row-inventory.md",
                [("SRC-001", "yes"), ("SRC-002", "yes")],
            )
            self.write_minimal_file(handoff_dir / "writer-session-log.md")
            self.write_minimal_file(handoff_dir / "prompt.writer-to-reviewer.round-1.md")
            self.write_test_case_file(fixture_root / "test-cases" / "sample.md", ["SRC-001"])

            result = self.run_script("--root", str(fixture_root), "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assessment = payload["clean_run_assessment"]
        self.assertEqual("writer-pass", assessment["stage"])
        self.assertEqual("fail", assessment["status"])
        self.assertTrue(
            any("SRC-002" in reason for reason in assessment["reasons"]),
            assessment["reasons"],
        )

    def test_markdown_report_includes_inventory_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            fixture_root = Path(tmp_dir)
            self.write_inventory(
                fixture_root / "work" / "stage-handoffs" / "01-ui-main-info" / "source-row-inventory.md",
                [("SRC-001", "yes"), ("SRC-002", "unclear")],
            )
            self.write_test_case_file(fixture_root / "test-cases" / "sample.md", ["SRC-001", "SRC-002"])

            result = self.run_script("--root", str(fixture_root), "--markdown")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("handoff_required_row_count: `2`", result.stdout)
        self.assertIn("writer_row_count: `2`", result.stdout)
        self.assertIn("missing_handoff_source_rows_in_writer: `none`", result.stdout)
        self.assertIn("## Next Prompt", result.stdout)

    def test_next_prompt_output_prints_only_prompt_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = self.run_script("--root", tmp_dir, "--next-prompt")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ft-source-locator", result.stdout)
        self.assertIn("fts\\ft-2-OF_11", result.stdout)
        self.assertNotIn("# Clean Run Evidence", result.stdout)

    def test_expect_stage_and_status_passes_when_assessment_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = self.run_script(
                "--root",
                tmp_dir,
                "--json",
                "--expect-stage",
                "not-started",
                "--expect-status",
                "pending",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("not-started", payload["clean_run_assessment"]["stage"])

    def test_expect_stage_and_status_fail_when_assessment_differs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = self.run_script(
                "--root",
                tmp_dir,
                "--json",
                "--expect-stage",
                "writer-pass",
                "--expect-status",
                "pass",
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("Expected clean_run stage `writer-pass`", result.stderr)
        self.assertIn("Expected clean_run status `pass`", result.stderr)

    def test_run_report_template_includes_current_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = self.run_script("--root", tmp_dir, "--run-report-template")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Eval Run Report: ft2-of11-clean-run-regression", result.stdout)
        self.assertIn("- reviewed_skill: `ft-source-locator`, `ft-scope-analyzer`, `ft-test-case-writer`", result.stdout)
        self.assertIn("- source_instructions: `AGENTS.md`, `skills/*/SKILL.md`, `references/agent/*`, `references/qa/*`", result.stdout)
        self.assertIn("clean_run_assessment.stage: `not-started`", result.stdout)
        self.assertIn("clean_run_assessment.status: `pending`", result.stdout)
        self.assertIn("clean_run_assessment.next_prompt_text: `Перейди в", result.stdout)
        self.assertIn("## Next Prompt Snapshot", result.stdout)
        self.assertIn("Выполни только стадию `ft-source-locator`", result.stdout)
        self.assertIn("validator_finding_ids: `workflow-state-not-found`", result.stdout)
        self.assertIn("## Stage Results", result.stdout)


if __name__ == "__main__":
    unittest.main()
