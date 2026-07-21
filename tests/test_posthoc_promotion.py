from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Any
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]

import test_case_agent.review_cycle.promotion as promotion_module
from test_case_agent.review_cycle.production_tc_gate import (
    validate_production_tc_draft,
)
from test_case_agent.review_cycle.prepared_package import (
    PACKAGE_VERSION,
    PackageArtifact,
    PreparedGap,
    PreparedObligation,
    PreparedObligationSet,
    PreparedReleaseStatus,
    PreparedStagePackage,
    SourceRegistryEntry,
)
from test_case_agent.review_cycle.promotion import (
    PromotionBlocked,
    build_full_promotion_basis,
    build_normalized_review_result,
    build_promotion_basis_seed,
    build_validate_promote_review_cycle,
    promote_review_cycle,
)
from test_case_agent.review_cycle.dimension_bindings import (
    ReviewerDimensionSourceBindings,
    render_reviewer_dimension_source_bindings,
)
from test_case_agent.review_cycle.source_assertions import (
    NO_REQUIRED_CHANGE,
    REVIEW_RECEIPT_VERSION,
    SOURCE_REVIEW_DIMENSIONS,
    ClauseEvidenceBinding,
    RequirementCodeBinding,
    ScopeBoundaryManifestContext,
    ScopeBoundaryExclusion,
    ScopeBoundaryReview,
    SourceAssertion,
    SourceAssertionReview,
    SourceAssertionReviewReceipt,
    SourceInventoryReview,
    build_source_assertion_manifest,
    render_embedded_source_assertion_contract,
    scope_boundary_source_locator,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_xlsx_table(
    path: Path,
    header: tuple[str, ...],
    rows: tuple[tuple[str, ...], ...],
) -> None:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Traceability"
    sheet.append(header)
    for row in rows:
        sheet.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)
    workbook.close()


class PosthocPromotionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.ft = self.repo / "fts" / "demo"
        self.cycle = self.ft / "work" / "review-cycles" / "demo-scope"
        self.handoff = self.ft / "work" / "stage-handoffs" / "01-demo-scope"
        self.cycle.mkdir(parents=True)
        self.handoff.mkdir(parents=True)

        self.candidate = self.cycle / "attempts" / "writer" / "attempt-001" / "stage-output" / "draft.md"
        self.candidate.parent.mkdir(parents=True)
        self.candidate_bytes = """# Demo test cases

## TC-DEMO-001

**Название:** Поиск заявки по точному номеру
**Тип:** позитивный
**Приоритет:** высокий
**package_id:** demo-scope
**Трассировка:** OBL-001; ATOM-001; BSR 1

### Предусловия

1. Открыть основную форму «Заявки в Системе».

### Тестовые данные

- Номер заявки: `APP-001`.

### Шаги

1. Ввести `APP-001` в поле «Номер заявки».
2. Нажать «Найти».

### Итоговый ожидаемый результат

В таблице отображается одна строка с номером заявки `APP-001`.

### Постусловия

- Нажать «Очистить», чтобы вернуть форму к исходному состоянию.
""".encode("utf-8")
        self.candidate.write_bytes(self.candidate_bytes)

        self.source_truth = self.ft / "source" / "main.xhtml"
        self.source_truth.parent.mkdir(parents=True)
        self.source_truth.write_text(
            '<html xmlns="http://www.w3.org/1999/xhtml"><body>'
            "<p>BSR 1: Search by application number.</p>"
            "<p>BSR 2: The fallback behavior is not specified.</p>"
            "<p>External ancestor context.</p>"
            "<p>External cross-reference context.</p>"
            "</body></html>\n",
            encoding="utf-8",
        )
        self.semantic_truth = self.ft / "source" / "main.docx"
        self.semantic_truth.write_bytes(b"PK\x03\x04semantic-source-v1")
        self.coverage_gaps = self.ft / "work" / "prepared" / "coverage-gaps.md"
        self.coverage_gaps.parent.mkdir(parents=True)
        self.coverage_gaps.write_text(
            "# Coverage Gaps\n\n## GAP-001\n\n"
            "**Impact:** `non-blocking`\n\n"
            "| field | value |\n"
            "| --- | --- |\n"
            "| gap_id | GAP-001 |\n"
            "| affected_assertion_id | ASSERT-DEMO-002 |\n"
            "| affected_atom_id | ATOM-002 |\n"
            "| status | open |\n\n"
            "Fallback behavior is not specified.\n",
            encoding="utf-8",
        )
        self.source = self.ft / "work" / "prepared" / "source-evidence.md"
        self.source.parent.mkdir(parents=True, exist_ok=True)
        self.source.write_text(self.render_source_basis(), encoding="utf-8")
        self.obligations = self.ft / "work" / "prepared" / "atomic-obligations.json"
        obligation_set = PreparedObligationSet.create(
            package_id="demo-scope",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    source_refs=("BSR 1",),
                    atomic_statement="Search supports an exact application number.",
                    observable_oracle="Only APP-001 is present in the result table.",
                    test_intent="Verify search by application number.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    planned_test_case_id="TC-DEMO-001",
                ),
                PreparedObligation(
                    obligation_id="OBL-002",
                    atom_id="ATOM-002",
                    source_refs=("BSR 2",),
                    atomic_statement="Fallback behavior is not specified.",
                    observable_oracle="",
                    test_intent="Preserve the unresolved fallback behavior.",
                    coverage_status="gap",
                    gap_id="GAP-DEMO-001",
                    dictionary_refs=(),
                    notes="Await clarification.",
                ),
            ),
            coverage_gaps=(
                PreparedGap(
                    gap_id="GAP-DEMO-001",
                    source_refs=("BSR 2",),
                    problem="The fallback behavior is not specified.",
                    handling="Preserve the gap until the source is clarified.",
                    blocking=False,
                ),
            ),
            evidence_text=self.source.read_text(encoding="utf-8"),
        )
        self.obligation_set = obligation_set
        write_json(self.obligations, obligation_set.to_dict())
        self.prepared_package = self.ft / "work" / "prepared" / "stage-package.json"
        self.prepared_instructions = (
            self.ft / "work" / "prepared" / "stage-instructions.md"
        )
        self.prepared_instructions.write_text(
            "# Prepared instructions\n", encoding="utf-8"
        )
        self.refresh_prepared_package()

        candidate_sha = sha256(self.candidate)
        self.review_result = self.cycle / "review-result.json"
        write_json(
            self.review_result,
            {
                "schema_version": 2,
                "contract_version": 4,
                "decision": "accepted",
                "reviewed_draft_path": self.rel(self.candidate),
                "reviewed_draft_sha256": candidate_sha,
                "reviewed_source_basis_sha256": sha256(self.source),
                "reviewed_obligation_set_sha256": sha256(self.obligations),
                "obligation_reviews": [
                    {
                        "obligation_id": "OBL-001",
                        "verdict": "covered",
                    },
                    {
                        "obligation_id": "OBL-002",
                        "verdict": "gap-preserved",
                    },
                ],
                "dimension_reviews": [],
                "findings": [],
                "summary": "Accepted without error findings.",
            },
        )

        self.gate = self.cycle / "attempts" / "writer" / "attempt-001" / "runner-output" / "quality-gate-bundle.json"
        write_json(
            self.gate,
            {
                "passed": True,
                "validator": "prepared-quality-gate-bundle-v1",
                "draft_sha256": candidate_sha,
                "findings": [],
            },
        )

        outputs = self.cycle / "outputs"
        self.findings = outputs / "final-findings.md"
        self.matrix = outputs / "final-traceability-matrix.md"
        self.matrix_xlsx = outputs / "final-traceability-matrix.xlsx"
        self.prompt = self.handoff / "prompt.reviewer-to-ui-prep.md"
        for path, content in (
            (self.findings, "# Final findings\n\nNo blocking findings.\n"),
            (
                self.matrix,
                "# Final traceability matrix\n\n"
                "| obligation_id | covered_by_tc | coverage_status |\n"
                "| --- | --- | --- |\n"
                "| `OBL-001` | `TC-DEMO-001` | `covered` |\n",
            ),
            (self.prompt, "# UI prep handoff\n\nUse the signed-off baseline.\n"),
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        write_xlsx_table(
            self.matrix_xlsx,
            ("obligation_id", "covered_by_tc", "coverage_status"),
            (("OBL-001", "TC-DEMO-001", "covered"),),
        )

        self.cycle_state = self.cycle / "cycle-state.yaml"
        self.cycle_state.write_text(
            f"""cycle_id: demo-scope
workflow_status: accepted-promotion-ready-not-promoted
stage_status: accepted-promotion-ready-not-promoted
current_stage: reviewer
reviewer_stage_status: accepted
writer_draft_sha256: {candidate_sha}
accepted_terminal_state: true
final_promoted: false
draft_or_unsigned: true
promotion_status: ready-not-promoted
canonical_test_cases: test-cases/1-demo.md
blocking_reasons:
  - promotion is disabled; review the promotion-ready candidate before a controlled production write
""",
            encoding="utf-8",
        )
        self.workflow_state = self.handoff / "workflow-state.yaml"
        self.workflow_state.write_text(
            """ft_slug: demo
scope_slug: demo-scope
current_stage: ft-test-case-iteration
stage_status: ready-for-review
next_skill: ft-test-case-reviewer
latest_artifacts:
  active_transition_prompt: work/review-cycles/demo-scope/prompts/prompt.writer-to-reviewer.round-1.md
blocking_reasons: []
""",
            encoding="utf-8",
        )

        self.canonical = self.ft / "test-cases" / "1-demo.md"
        transaction_id = f"{candidate_sha[:16]}-{sha256(self.review_result)[:8]}"
        self.transaction_id = transaction_id
        snapshot_rel = "work/review-cycles/demo-scope/versions/signed-off"
        promotion_inputs = self.cycle / "promotion-inputs"
        promotion_inputs.mkdir()
        self.cycle_after = promotion_inputs / "cycle-state.signed-off.yaml"
        self.cycle_after.write_text(
            f"""cycle_id: demo-scope
workflow_status: signed-off
stage_status: signed-off
current_stage: reviewer
reviewer_stage_status: accepted
writer_draft_sha256: {candidate_sha}
accepted_terminal_state: true
final_promoted: true
draft_or_unsigned: false
promotion_status: completed
final_sha256: {candidate_sha}
canonical_test_cases: test-cases/1-demo.md
blocking_reasons:
""",
            encoding="utf-8",
        )
        self.workflow_after = promotion_inputs / "workflow-state.signed-off.yaml"
        self.workflow_after.write_text(
            f"""ft_slug: demo
scope_slug: demo-scope
current_stage: ft-test-case-iteration
stage_status: signed-off
current_round: 1
next_skill: ft-ui-automation-prep
required_inputs:
  - work/review-cycles/demo-scope/cycle-state.yaml
  - {snapshot_rel}
  - work/stage-handoffs/01-demo-scope/prompt.reviewer-to-ui-prep.md
latest_artifacts:
  canonical_test_cases: test-cases/1-demo.md
  cycle_state: work/review-cycles/demo-scope/cycle-state.yaml
  final_findings: work/review-cycles/demo-scope/outputs/final-findings.md
  final_traceability_matrix: work/review-cycles/demo-scope/outputs/final-traceability-matrix.md
  final_traceability_matrix_xlsx: work/review-cycles/demo-scope/outputs/final-traceability-matrix.xlsx
  final_writer_response: none
  signed_off_snapshot: {snapshot_rel}
  prompt_reviewer_to_ui_prep: work/stage-handoffs/01-demo-scope/prompt.reviewer-to-ui-prep.md
  active_transition_prompt: work/stage-handoffs/01-demo-scope/prompt.reviewer-to-ui-prep.md
coverage_gaps:
  blocking: 0
  non_blocking: 0
open_questions: []
blocking_reasons: []
accepted_risks: []
""",
            encoding="utf-8",
        )

        self.basis = self.cycle / "promotion-basis.json"
        write_json(
            self.basis,
            {
                "schema_version": 3,
                "ft_root": self.rel(self.ft),
                "cycle_dir": self.rel(self.cycle),
                "scope_slug": "demo-scope",
                "candidate": self.binding(self.candidate),
                "writer": self.binding(self.candidate),
                "source_basis": self.binding(self.source),
                "obligation_set": self.binding(self.obligations),
                "prepared_package": self.binding(self.prepared_package),
                "reviewer": self.binding(self.review_result),
                "publication": {
                    "canonical_path": self.rel(self.canonical),
                    "expected_prior_sha256": None,
                },
                "gate_reports": [
                    {
                        **self.binding(self.gate),
                        "validator": "prepared-quality-gate-bundle-v1",
                    }
                ],
                "state_updates": [
                    {
                        "role": "cycle-state",
                        "path": self.rel(self.cycle_state),
                        "before_sha256": sha256(self.cycle_state),
                        "after_path": self.rel(self.cycle_after),
                        "after_sha256": sha256(self.cycle_after),
                        "schema": "codex-exec-cycle-state-v1",
                    },
                    {
                        "role": "workflow-state",
                        "path": self.rel(self.workflow_state),
                        "before_sha256": sha256(self.workflow_state),
                        "after_path": self.rel(self.workflow_after),
                        "after_sha256": sha256(self.workflow_after),
                        "schema": "workflow-state-final-aliases-v1",
                    },
                ],
                "final_aliases": {
                    "final_findings": self.binding(self.findings),
                    "final_traceability_matrix": self.binding(self.matrix),
                    "final_traceability_matrix_xlsx": self.binding(self.matrix_xlsx),
                    "final_writer_response": None,
                    "handoff_prompt": self.binding(self.prompt),
                },
            },
        )

        self.seed = self.cycle / "promotion-basis.seed.json"
        write_json(
            self.seed,
            build_promotion_basis_seed(
                ft_root=self.rel(self.ft),
                cycle_dir=self.rel(self.cycle),
                scope_slug="demo-scope",
                candidate=self.binding(self.candidate),
                writer=self.binding(self.candidate),
                source_basis=self.binding(self.source),
                obligation_set=self.binding(self.obligations),
                prepared_package=self.binding(self.prepared_package),
                reviewer=self.binding(self.review_result),
                gate_reports=(
                    {
                        **self.binding(self.gate),
                        "validator": "prepared-quality-gate-bundle-v1",
                    },
                ),
                canonical_path=self.rel(self.canonical),
                canonical_prior_sha256=None,
                production_test_case_hashes={},
                available_builder_inputs={
                    "final_findings": self.binding(self.findings),
                    "final_traceability_matrix": self.binding(self.matrix),
                    "final_traceability_matrix_xlsx": self.binding(self.matrix_xlsx),
                    "handoff_prompt": self.binding(self.prompt),
                },
            ),
        )

    def render_source_basis(
        self,
        *,
        scope_slug: str = "demo-scope",
        testable_obligation_ids: tuple[str, ...] = ("OBL-001",),
        gap_disposition: str = "ambiguous",
        dimension_bindings: dict[str, tuple[str, ...]] | None = None,
    ) -> str:
        source_path = self.rel(self.source_truth)
        assertions = (
            SourceAssertion(
                assertion_id="ASSERT-DEMO-001",
                source_path=source_path,
                source_context_class="document-global-constraints",
                locator="/*/*[1]/*[1]",
                exact_source_text="BSR 1: Search by application number.",
                canonical_statement="Search supports an exact application number.",
                polarity="positive",
                semantic_disposition="testable",
                execution_readiness="ready",
                execution_readiness_rationale=NO_REQUIRED_CHANGE,
                risk="high",
                condition_clauses=("An exact application number is available.",),
                action_clauses=("Search by the exact application number.",),
                oracle_clauses=("Only APP-001 is present in the result table.",),
                requirement_codes=("BSR 1",),
                requirement_code_bindings=(
                    RequirementCodeBinding("BSR 1", "SRC-DEMO-001", "xhtml-row", "BSR 1"),
                ),
                clause_evidence_bindings=tuple(
                    ClauseEvidenceBinding(
                        clause_kind=kind,
                        clause_index=0,
                        source_row_id="SRC-DEMO-001",
                        evidence_role=kind,
                        exact_source_fragment="BSR 1: Search by application number.",
                    )
                    for kind in ("condition", "action", "oracle")
                ),
                source_row_id="SRC-DEMO-001",
                atom_id="ATOM-001",
                obligation_ids=testable_obligation_ids,
                execution_dependency_gap_ids=(),
                primary_gap_id=None,
            ),
            SourceAssertion(
                assertion_id="ASSERT-DEMO-002",
                source_path=source_path,
                source_context_class="scope-local",
                locator="/*/*[1]/*[2]",
                exact_source_text="BSR 2: The fallback behavior is not specified.",
                canonical_statement="Fallback behavior is not specified.",
                polarity="neutral",
                semantic_disposition=gap_disposition,
                execution_readiness=(
                    "dependency-blocked"
                    if gap_disposition == "ambiguous"
                    else "not-applicable"
                ),
                execution_readiness_rationale=(
                    "Fallback behavior must be clarified before execution."
                    if gap_disposition == "ambiguous"
                    else NO_REQUIRED_CHANGE
                ),
                risk="medium",
                condition_clauses=(),
                action_clauses=(),
                oracle_clauses=(),
                requirement_codes=("BSR 2",),
                requirement_code_bindings=(
                    RequirementCodeBinding("BSR 2", "SRC-DEMO-002", "xhtml-row", "BSR 2"),
                ),
                clause_evidence_bindings=(),
                source_row_id="SRC-DEMO-002",
                atom_id="ATOM-002",
                obligation_ids=(),
                execution_dependency_gap_ids=(),
                primary_gap_id=(
                    "GAP-001" if gap_disposition == "ambiguous" else None
                ),
                disposition_rationale=(
                    "The registered BSR 2 statement is treated as excluded for this "
                    "negative promotion fixture."
                    if gap_disposition == "not-applicable"
                    else (
                        "The registered BSR 2 statement explicitly leaves fallback "
                        "behavior undefined and requires GAP-001."
                    )
                ),
            ),
        )
        if gap_disposition == "ambiguous":
            self.coverage_gaps.write_text(
                "# Coverage Gaps\n\n"
                "## GAP-001\n\n"
                "**Impact:** `non-blocking`\n\n"
                "| field | value |\n"
                "| --- | --- |\n"
                "| gap_id | GAP-001 |\n"
                "| affected_assertion_id | ASSERT-DEMO-002 |\n"
                "| affected_atom_id | ATOM-002 |\n"
                "| status | open |\n\n"
                "Fallback behavior is not specified.\n",
                encoding="utf-8",
            )
        else:
            self.coverage_gaps.write_text(
                "# Coverage Gaps\n\nNo gaps.\n",
                encoding="utf-8",
            )
        manifest = build_source_assertion_manifest(
            self.repo,
            scope_slug=scope_slug,
            coverage_gaps_path=self.rel(self.coverage_gaps),
            source_paths=(source_path,),
            assertions=assertions,
            source_row_extraction_spec_digest="1" * 64,
            source_row_baseline_digest="2" * 64,
            source_row_candidate_count=2,
            source_row_candidate_ids={
                "SRC-DEMO-001": "SRC-CAND-" + "1" * 24,
                "SRC-DEMO-002": "SRC-CAND-" + "2" * 24,
            },
            evidence_sources=(
                (
                    self.rel(self.semantic_truth),
                    "semantic-source-of-truth",
                ),
            ),
            expected_source_row_ids=("SRC-DEMO-001", "SRC-DEMO-002"),
        )
        receipt = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=manifest.digest,
            decision="accepted",
            source_inventory_review=SourceInventoryReview(
                extraction_spec_digest=manifest.source_row_extraction_spec_digest,
                baseline_digest=manifest.source_row_baseline_digest,
                candidate_count=manifest.source_row_candidate_count,
                mapped_source_row_count=2,
                verdict="verified",
                required_change=NO_REQUIRED_CHANGE,
                note="Candidate baseline and source-row mapping were reviewed.",
            ),
            assertion_reviews=tuple(
                SourceAssertionReview(
                    assertion_id=item.assertion_id,
                    approved_polarity=item.polarity,
                    approved_semantic_disposition=item.semantic_disposition,
                    approved_execution_readiness=item.execution_readiness,
                    approved_risk=item.risk,
                    dimension_verdicts={
                        dimension: "verified"
                        for dimension in SOURCE_REVIEW_DIMENSIONS
                    },
                    verdict="verified",
                    required_change=NO_REQUIRED_CHANGE,
                    note="Verified against the registered source.",
                )
                for item in assertions
            ),
            scope_boundary_review=ScopeBoundaryReview(
                verdict="verified",
                checked_context_classes=(
                    "document-global-constraints",
                    "ancestor-and-section-preamble",
                    "cross-referenced-constraints",
                ),
                reviewed_manifest_contexts=(
                    ScopeBoundaryManifestContext(
                        context_class="document-global-constraints",
                        source_row_id=assertions[0].source_row_id,
                    ),
                ),
                excluded_contexts=tuple(
                    ScopeBoundaryExclusion(
                        context_class=context_class,
                        source_path=manifest.sources[0].path,
                        source_sha256=manifest.sources[0].sha256,
                        source_locator=scope_boundary_source_locator(
                            manifest.sources[0].path,
                            exact_text,
                        ),
                        exact_source_text=exact_text,
                        reason="Verified context is outside the manifest row registry.",
                    )
                    for context_class, exact_text in (
                        (
                            "ancestor-and-section-preamble",
                            "External ancestor context.",
                        ),
                        (
                            "cross-referenced-constraints",
                            "External cross-reference context.",
                        ),
                    )
                ),
                required_change=NO_REQUIRED_CHANGE,
                note="Scope boundaries were checked against the full document.",
            ),
        )
        bindings = ReviewerDimensionSourceBindings.create(
            dimension_bindings or {}
        )
        return (
            "# Verified source\n\n"
            + render_embedded_source_assertion_contract(manifest, receipt)
            + "\n## Reviewer dimension source bindings\n\n"
            + render_reviewer_dimension_source_bindings(bindings)
            + "\n"
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_cycle_state_admission_accepts_exact_reviewer_rebind_terminal(self) -> None:
        candidate_sha = sha256(self.candidate)
        state = f"""cycle_id: demo-scope-rebind
workflow_status: accepted-not-promoted
stage_status: accepted-not-promoted
current_stage: reviewer-r1
writer_stage_status: skipped-reviewer-rebind
reviewer_stage_status: accepted
writer_draft_sha256: {candidate_sha}
accepted_terminal_state: true
final_promoted: false
draft_or_unsigned: true
promotion_status: pending
reviewer_rebind_report: work/review-cycles/demo-scope-rebind/reviewer-rebind.json
blocking_reasons:
  - promotion is disabled; review the promotion-ready candidate before a controlled production write
"""

        promotion_module._validate_cycle_state_before(state, candidate_sha)

    def test_cycle_state_admission_accepts_exact_ordinary_writer_review_terminal(self) -> None:
        candidate_sha = sha256(self.candidate)
        state = f"""cycle_id: demo-scope
workflow_status: accepted-not-promoted
stage_status: accepted-not-promoted
current_stage: reviewer-r1
writer_stage_status: completed
reviewer_stage_status: accepted
writer_draft_sha256: {candidate_sha}
accepted_terminal_state: true
final_promoted: false
draft_or_unsigned: true
promotion_status: pending
blocking_reasons:
  - promotion is disabled; review the promotion-ready candidate before a controlled production write
"""

        promotion_module._validate_cycle_state_before(state, candidate_sha)

    def rel(self, path: Path) -> str:
        return path.relative_to(self.repo).as_posix()

    def binding(self, path: Path) -> dict[str, str]:
        return {"path": self.rel(path), "sha256": sha256(path)}

    def target_lock_path(self, target: Path) -> Path:
        normalized = os.path.normcase(os.path.normpath(str(target.resolve())))
        lock_key = hashlib.sha256((normalized + "\n").encode("utf-8")).hexdigest()
        return self.repo / ".qa-agent-promotion-locks" / f"{lock_key}.lock"

    def assert_concurrent_target_overlap_is_blocked(
        self,
        *,
        second_cycle: Path,
        second_basis: Path,
    ) -> None:
        entered = threading.Event()
        release = threading.Event()
        failures: list[BaseException] = []

        def pause(phase: str) -> None:
            if phase == "after-publication":
                entered.set()
                if not release.wait(10):
                    raise RuntimeError("target-lock test timed out")

        def first_promotion() -> None:
            try:
                self.promote(fault_injector=pause)
            except BaseException as exc:  # pragma: no cover - surfaced below
                failures.append(exc)

        thread = threading.Thread(target=first_promotion)
        thread.start()
        try:
            self.assertTrue(entered.wait(10))
            with self.assertRaises(PromotionBlocked) as raised:
                promote_review_cycle(
                    repo_root=self.repo,
                    cycle_dir=second_cycle,
                    basis_path=second_basis,
                )
            self.assertEqual("PROMO-TARGET-LOCKED", raised.exception.code)
        finally:
            release.set()
            thread.join(10)
        self.assertFalse(thread.is_alive())
        self.assertEqual([], failures)
        self.assertEqual(self.candidate_bytes, self.canonical.read_bytes())
        self.assertEqual(self.cycle_after.read_bytes(), self.cycle_state.read_bytes())
        self.assertEqual(
            self.workflow_after.read_bytes(),
            self.workflow_state.read_bytes(),
        )
        self.assertFalse((self.repo / ".qa-agent-promotion-locks").exists())

    def refresh_prepared_package(self) -> None:
        obligation_set = PreparedObligationSet.from_dict(
            json.loads(self.obligations.read_text(encoding="utf-8")),
            evidence_text=self.source.read_text(encoding="utf-8"),
        )
        blocking_gap_ids = tuple(
            sorted(
                item.gap_id
                for item in obligation_set.coverage_gaps
                if item.blocking
            )
        )
        release_status = (
            PreparedReleaseStatus(
                contract="prepared-package-release-status-v1",
                output_mode="draft-with-blocking-gaps",
                release_eligible=False,
                blocking_gap_ids=blocking_gap_ids,
                execution_dependency_registry=(),
                excluded_execution_obligation_ids=(),
                unsigned_status="blocked-source-gaps",
                release_blocking_finding_codes=(
                    "blocking-source-first-gap",
                ),
            )
            if blocking_gap_ids
            else PreparedReleaseStatus.release_default()
        )
        artifacts = tuple(
            PackageArtifact(
                path=self.rel(path),
                sha256=sha256(path),
                kind=kind,
                bytes=path.stat().st_size,
            )
            for path, kind in (
                (self.source, "source-evidence"),
                (self.obligations, "atomic-obligations"),
                (self.prepared_instructions, "stage-instructions"),
            )
        )
        package = PreparedStagePackage(
            package_version=PACKAGE_VERSION,
            package_id=obligation_set.package_id,
            ft_slug="demo",
            scope_slug="demo-scope",
            section_id="1",
            created_at="2026-07-15T00:00:00+00:00",
            input_fingerprint="a" * 64,
            source_registry=(
                SourceRegistryEntry(
                    path=self.rel(self.semantic_truth),
                    sha256=sha256(self.semantic_truth),
                    role="source-of-truth",
                    locator="main FT",
                ),
                SourceRegistryEntry(
                    path=self.rel(self.source_truth),
                    sha256=sha256(self.source_truth),
                    role="machine-readable",
                    locator="scope rows",
                ),
            ),
            package_artifacts=artifacts,
            execution_profile="simple-field-property",
            unsupported_dimensions=(),
            release_status=release_status,
            forbidden_evidence_roots=("fts/demo/test-cases",),
            fallback_policy="targeted-only",
            package_digest="",
        )
        digest = hashlib.sha256(
            json.dumps(
                package._without_digest(),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        package = replace(package, package_digest=digest)
        package.validate()
        write_json(self.prepared_package, package.to_dict())
        if hasattr(self, "basis") and self.basis.is_file():
            basis = json.loads(self.basis.read_text(encoding="utf-8"))
            basis["prepared_package"] = self.binding(self.prepared_package)
            write_json(self.basis, basis)

    def replace_review_result(self, payload: dict[str, Any]) -> None:
        write_json(self.review_result, payload)
        basis = json.loads(self.basis.read_text(encoding="utf-8"))
        basis["reviewer"] = self.binding(self.review_result)
        write_json(self.basis, basis)

    def replace_source_basis(self, text: str) -> None:
        self.source.write_text(text, encoding="utf-8")
        review = json.loads(self.review_result.read_text(encoding="utf-8"))
        review["reviewed_source_basis_sha256"] = sha256(self.source)
        self.replace_review_result(review)
        basis = json.loads(self.basis.read_text(encoding="utf-8"))
        basis["source_basis"] = self.binding(self.source)
        write_json(self.basis, basis)
        self.refresh_prepared_package()

    def replace_obligation_set(self, obligation_set: PreparedObligationSet) -> None:
        write_json(self.obligations, obligation_set.to_dict())
        review = json.loads(self.review_result.read_text(encoding="utf-8"))
        review["reviewed_obligation_set_sha256"] = sha256(self.obligations)
        self.replace_review_result(review)
        basis = json.loads(self.basis.read_text(encoding="utf-8"))
        basis["obligation_set"] = self.binding(self.obligations)
        write_json(self.basis, basis)
        self.refresh_prepared_package()

    def promote(self, **kwargs: Any):
        return promote_review_cycle(
            repo_root=self.repo,
            cycle_dir=self.cycle,
            basis_path=self.basis,
            **kwargs,
        )

    def build_basis(self, *, reset: bool = True, **kwargs: Any):
        if reset:
            self.basis.unlink(missing_ok=True)
        return build_full_promotion_basis(
            repo_root=self.repo,
            cycle_dir=self.cycle,
            seed_path=self.seed,
            basis_path=self.basis,
            **kwargs,
        )

    def build_and_promote(self, **kwargs: Any):
        return build_validate_promote_review_cycle(
            repo_root=self.repo,
            cycle_dir=self.cycle,
            seed_path=self.seed,
            basis_path=self.basis,
            **kwargs,
        )

    def run_abrupt_promotion(self, phase: str) -> subprocess.CompletedProcess[str]:
        self.build_basis()
        return subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "tests" / "fixtures" / "abrupt_promotion_child.py"),
                "--repo-root",
                str(self.repo),
                "--cycle-dir",
                str(self.cycle),
                "--basis-path",
                str(self.basis),
                "--phase",
                phase,
            ],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
        )

    def assert_abrupt_exit_recovers(self, phase: str, *, expected_retry: str) -> None:
        killed = self.run_abrupt_promotion(phase)
        self.assertEqual(97, killed.returncode, killed.stderr + killed.stdout)
        self.assertTrue((self.cycle / "promotion.lock").is_file())
        self.assertTrue((self.repo / ".qa-agent-promotion-locks").is_dir())

        recovered = self.build_and_promote()

        self.assertEqual(expected_retry, recovered.status)
        self.assertEqual(self.candidate_bytes, self.canonical.read_bytes())
        self.assertEqual(self.cycle_after.read_bytes(), self.cycle_state.read_bytes())
        self.assertEqual(self.workflow_after.read_bytes(), self.workflow_state.read_bytes())
        self.assertFalse((self.cycle / "promotion.lock").exists())
        self.assertFalse((self.repo / ".qa-agent-promotion-locks").exists())
        self.assertEqual([], list((self.cycle / "promotion").glob(".*.journal")))
        self.assertEqual([], list((self.cycle / "promotion").glob(".*.rolled-back")))

        replay = self.build_and_promote()
        self.assertEqual("already-promoted", replay.status)
        self.assertEqual(recovered.receipt_path, replay.receipt_path)

    def test_happy_path_runs_production_gate_once_and_publishes_byte_identically(self) -> None:
        calls = 0

        def counting_gate(**kwargs: Any):
            nonlocal calls
            calls += 1
            return validate_production_tc_draft(**kwargs)

        result = self.promote(production_gate=counting_gate)

        self.assertEqual("promoted", result.status)
        self.assertEqual(1, calls)
        self.assertEqual(self.candidate_bytes, self.canonical.read_bytes())
        self.assertTrue(result.byte_identical)
        self.assertEqual(self.cycle_after.read_bytes(), self.cycle_state.read_bytes())
        self.assertEqual(self.workflow_after.read_bytes(), self.workflow_state.read_bytes())
        self.assertTrue(result.receipt_path.is_file())
        self.assertTrue(result.metrics_path.is_file())
        receipt = json.loads(result.receipt_path.read_text(encoding="utf-8"))
        self.assertTrue(receipt["publication"]["byte_identical"])
        self.assertEqual(sha256(self.candidate), receipt["publication"]["sha256"])
        self.assertNotIn("phase_timings_ms", receipt)
        self.assertNotIn("generated_at", receipt)
        snapshot = self.cycle / "versions" / "signed-off" / "snapshot-manifest.yaml"
        self.assertTrue(snapshot.is_file())
        snapshot_manifest = json.loads(
            (snapshot.parent / "snapshot-manifest.json").read_text(encoding="utf-8")
        )
        canonical_entries = [
            item
            for item in snapshot_manifest["files"]
            if item["path"] == "test-cases/1-demo.md"
        ]
        self.assertEqual(1, len(canonical_entries))
        self.assertEqual(sha256(self.candidate), canonical_entries[0]["sha256"])
        self.assertTrue(
            (result.receipt_path.parent / "before" / "snapshot-manifest.json").is_file()
        )
        self.assertFalse((self.cycle / "promotion.lock").exists())

    def test_abrupt_exit_after_journal_prepared_rolls_back_and_retries(self) -> None:
        self.assert_abrupt_exit_recovers(
            "after-journal-prepared",
            expected_retry="promoted",
        )

    def test_abrupt_exit_after_locks_acquired_recovers_stale_locks(self) -> None:
        self.assert_abrupt_exit_recovers(
            "after-locks-acquired",
            expected_retry="promoted",
        )

    def test_abrupt_exit_after_publication_rolls_back_and_retries(self) -> None:
        self.assert_abrupt_exit_recovers(
            "after-publication",
            expected_retry="promoted",
        )

    def test_abrupt_exit_after_cycle_state_update_rolls_back_and_retries(self) -> None:
        self.assert_abrupt_exit_recovers(
            "after-cycle-state-update",
            expected_retry="promoted",
        )

    def test_abrupt_exit_after_workflow_state_update_rolls_back_and_retries(self) -> None:
        self.assert_abrupt_exit_recovers(
            "after-workflow-state-update",
            expected_retry="promoted",
        )

    def test_abrupt_exit_after_state_updates_rolls_back_and_retries(self) -> None:
        self.assert_abrupt_exit_recovers(
            "after-state-updates",
            expected_retry="promoted",
        )

    def test_abrupt_exit_after_metrics_rolls_back_and_retries(self) -> None:
        self.assert_abrupt_exit_recovers(
            "after-metrics",
            expected_retry="promoted",
        )

    def test_abrupt_exit_after_transaction_commit_rolls_forward_idempotently(self) -> None:
        self.assert_abrupt_exit_recovers(
            "after-transaction-commit",
            expected_retry="already-promoted",
        )

    def test_abrupt_exit_after_snapshot_commit_rolls_forward_idempotently(self) -> None:
        self.assert_abrupt_exit_recovers(
            "after-snapshot-commit",
            expected_retry="already-promoted",
        )

    def test_abrupt_exit_recovery_blocks_on_unknown_external_target_bytes(self) -> None:
        killed = self.run_abrupt_promotion("after-publication")
        self.assertEqual(97, killed.returncode, killed.stderr + killed.stdout)
        external = self.workflow_state.read_bytes() + b"# external mutation\n"
        self.workflow_state.write_bytes(external)

        with self.assertRaises(PromotionBlocked) as raised:
            self.build_and_promote()

        self.assertEqual("PROMO-RECOVERY-AMBIGUOUS", raised.exception.code)
        self.assertEqual(self.candidate_bytes, self.canonical.read_bytes())
        self.assertEqual(external, self.workflow_state.read_bytes())
        self.assertTrue((self.cycle / "promotion.lock").exists())
        self.assertTrue((self.repo / ".qa-agent-promotion-locks").exists())

    def test_full_basis_builder_binds_real_terminal_inputs_deterministically(self) -> None:
        result = self.build_basis()

        self.assertEqual("built", result.status)
        self.assertFalse(result.reused)
        self.assertEqual(sha256(self.basis), result.basis_sha256)
        payload = json.loads(self.basis.read_text(encoding="utf-8"))
        self.assertEqual(3, payload["schema_version"])
        self.assertEqual(self.binding(self.findings), payload["final_aliases"]["final_findings"])
        self.assertEqual(self.binding(self.matrix), payload["final_aliases"]["final_traceability_matrix"])
        self.assertEqual(self.binding(self.prompt), payload["final_aliases"]["handoff_prompt"])

        reused = self.build_basis(reset=False)

        self.assertEqual("reused", reused.status)
        self.assertTrue(reused.reused)
        self.assertEqual(result.basis_sha256, reused.basis_sha256)

    def test_builder_prefers_current_seed_matrix_over_prior_workflow_aliases(self) -> None:
        prior_outputs = self.ft / "work" / "review-cycles" / "prior" / "outputs"
        prior_outputs.mkdir(parents=True)
        prior_md = prior_outputs / "final-traceability-matrix.md"
        prior_xlsx = prior_outputs / "final-traceability-matrix.xlsx"
        prior_md.write_bytes(self.matrix.read_bytes())
        prior_xlsx.write_bytes(self.matrix_xlsx.read_bytes())
        workflow = self.workflow_state.read_text(encoding="utf-8")
        workflow = workflow.replace(
            "  active_transition_prompt: work/review-cycles/demo-scope/prompts/"
            "prompt.writer-to-reviewer.round-1.md\n",
            "  active_transition_prompt: work/review-cycles/demo-scope/prompts/"
            "prompt.writer-to-reviewer.round-1.md\n"
            "  final_traceability_matrix: work/review-cycles/prior/outputs/"
            "final-traceability-matrix.md\n"
            "  final_traceability_matrix_xlsx: work/review-cycles/prior/outputs/"
            "final-traceability-matrix.xlsx\n",
        )
        self.workflow_state.write_text(workflow, encoding="utf-8")

        result = self.build_basis()
        payload = json.loads(result.basis_path.read_text(encoding="utf-8"))

        self.assertEqual(
            self.binding(self.matrix),
            payload["final_aliases"]["final_traceability_matrix"],
        )

    def test_builder_rejects_terminal_artifact_mutated_after_runner_seed(self) -> None:
        self.prompt.write_text(
            "# Mutated handoff\n",
            encoding="utf-8",
        )

        with self.assertRaises(PromotionBlocked) as raised:
            self.build_basis()

        self.assertEqual("PROMO-BUILDER-BINDING-MISMATCH", raised.exception.code)

    def test_builder_requires_runner_seed_binding_for_each_terminal_artifact(self) -> None:
        seed = json.loads(self.seed.read_text(encoding="utf-8"))
        seed["available_builder_inputs"].pop("handoff_prompt")
        seed["missing_builder_inputs"].append(
            "reviewer-to-ui-prep-handoff-prompt"
        )
        write_json(self.seed, seed)

        with self.assertRaises(PromotionBlocked) as raised:
            self.build_basis()

        self.assertEqual("PROMO-MISSING-BUILDER-INPUT", raised.exception.code)

    def test_one_command_build_validate_promote_creates_complete_transaction(self) -> None:
        self.basis.unlink()

        result = self.build_and_promote()

        self.assertEqual("promoted", result.status)
        self.assertEqual(self.candidate_bytes, self.canonical.read_bytes())
        self.assertTrue(result.receipt_path.is_file())
        self.assertTrue(result.metrics_path.is_file())
        self.assertIn("basis_build", result.phase_timings_ms)
        self.assertLessEqual(result.phase_timings_ms["total"], 300_000)
        receipt = json.loads(result.receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(
            sha256(self.prepared_package),
            receipt["hash_chain"]["prepared_package_sha256"],
        )
        self.assertTrue((self.cycle / "versions" / "signed-off" / "snapshot-manifest.yaml").is_file())
        self.assertEqual(self.workflow_after.read_bytes(), self.workflow_state.read_bytes())

    def test_one_command_hard_slo_blocks_before_publication(self) -> None:
        self.basis.unlink()
        now = 0

        def deterministic_clock() -> int:
            nonlocal now
            now += 10_000_000
            return now

        with self.assertRaises(PromotionBlocked) as raised:
            self.build_and_promote(
                target_slo_ms=20,
                hard_slo_ms=30,
                monotonic_ns=deterministic_clock,
            )

        self.assertEqual("PROMO-HARD-SLO-EXCEEDED", raised.exception.code)
        self.assertFalse(self.canonical.exists())
        self.assertNotEqual(self.cycle_after.read_bytes(), self.cycle_state.read_bytes())
        self.assertNotEqual(self.workflow_after.read_bytes(), self.workflow_state.read_bytes())
        self.assertFalse((self.cycle / "promotion").exists())

    def test_cli_default_runs_build_validate_promote_from_seed(self) -> None:
        self.basis.unlink()
        shutil.rmtree(self.cycle / "promotion-inputs")
        command = [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "promote_review_cycle.py"),
            "--repo-root",
            str(self.repo),
            "--cycle-dir",
            self.rel(self.cycle),
        ]

        first = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
        )
        second = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
        )

        self.assertEqual(0, first.returncode, first.stderr + first.stdout)
        self.assertEqual("promoted", json.loads(first.stdout)["status"])
        self.assertEqual(0, second.returncode, second.stderr + second.stdout)
        self.assertEqual("already-promoted", json.loads(second.stdout)["status"])
        self.assertEqual(self.candidate_bytes, self.canonical.read_bytes())
        self.assertTrue(self.cycle_after.is_file())
        self.assertTrue(self.workflow_after.is_file())

    def test_cli_default_does_not_silently_fall_back_to_unseeded_existing_basis(self) -> None:
        self.seed.unlink()
        command = [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "promote_review_cycle.py"),
            "--repo-root",
            str(self.repo),
            "--cycle-dir",
            self.rel(self.cycle),
        ]

        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
        )

        self.assertEqual(2, completed.returncode)
        self.assertEqual("PROMO-MISSING-SEED", json.loads(completed.stdout)["code"])
        self.assertFalse(self.canonical.exists())

    def test_generated_workflow_required_inputs_cannot_be_satisfied_by_other_list(self) -> None:
        self.basis.unlink()
        workflow = self.workflow_after.read_text(encoding="utf-8")
        required_block = """required_inputs:
  - work/review-cycles/demo-scope/cycle-state.yaml
  - work/review-cycles/demo-scope/versions/signed-off
  - work/stage-handoffs/01-demo-scope/prompt.reviewer-to-ui-prep.md
"""
        workflow = workflow.replace(required_block, "required_inputs: []\n")
        workflow += """unrelated_paths:
  - work/review-cycles/demo-scope/cycle-state.yaml
  - work/review-cycles/demo-scope/versions/signed-off
  - work/stage-handoffs/01-demo-scope/prompt.reviewer-to-ui-prep.md
"""
        self.workflow_after.write_text(workflow, encoding="utf-8")

        with self.assertRaises(PromotionBlocked) as raised:
            self.build_and_promote()

        self.assertEqual("PROMO-INVALID-WORKFLOW-STATE", raised.exception.code)
        self.assertFalse(self.canonical.exists())

    def test_duplicate_workflow_yaml_key_is_rejected_fail_closed(self) -> None:
        self.basis.unlink()
        with self.workflow_after.open("a", encoding="utf-8") as handle:
            handle.write("scope_slug: demo-scope\n")

        with self.assertRaises(PromotionBlocked) as raised:
            self.build_and_promote()

        self.assertEqual("PROMO-INVALID-YAML", raised.exception.code)
        self.assertFalse(self.canonical.exists())

    def test_builder_missing_matrix_blocks_before_basis_or_canonical_write(self) -> None:
        self.basis.unlink()
        self.matrix.unlink()

        with self.assertRaises(PromotionBlocked) as raised:
            self.build_and_promote()

        self.assertEqual("PROMO-MISSING-BUILDER-INPUT", raised.exception.code)
        self.assertFalse(self.basis.exists())
        self.assertFalse(self.canonical.exists())
        self.assertNotEqual(self.cycle_after.read_bytes(), self.cycle_state.read_bytes())

    def test_builder_rejects_pk_prefixed_non_ooxml_matrix(self) -> None:
        self.basis.unlink()
        self.matrix_xlsx.write_bytes(b"PK\x03\x04not-a-real-workbook")

        with self.assertRaises(PromotionBlocked) as raised:
            self.build_and_promote()

        self.assertEqual("PROMO-TRACEABILITY-XLSX-INVALID", raised.exception.code)
        self.assertFalse(self.basis.exists())
        self.assertFalse(self.canonical.exists())

    def test_builder_rejects_markdown_xlsx_semantic_drift(self) -> None:
        self.basis.unlink()
        write_xlsx_table(
            self.matrix_xlsx,
            ("obligation_id", "covered_by_tc", "coverage_status"),
            (("OBL-001", "TC-DEMO-999", "covered"),),
        )

        with self.assertRaises(PromotionBlocked) as raised:
            self.build_and_promote()

        self.assertEqual(
            "PROMO-TRACEABILITY-PARITY-MISMATCH",
            raised.exception.code,
        )
        self.assertFalse(self.basis.exists())
        self.assertFalse(self.canonical.exists())

    def test_generated_replacements_reject_blocked_foreign_workflow_state(self) -> None:
        self.basis.unlink()
        shutil.rmtree(self.cycle / "promotion-inputs")
        blocked_workflow = b"""ft_slug: demo
scope_slug: demo-scope
current_stage: ft-scope-analyzer
stage_status: blocked-input
next_skill: ft-scope-analyzer
blocking_reasons:
  - mandatory XHTML source is missing
"""
        self.workflow_state.write_bytes(blocked_workflow)

        with self.assertRaises(PromotionBlocked) as raised:
            self.build_and_promote()

        self.assertEqual("PROMO-INVALID-WORKFLOW-STATE", raised.exception.code)
        self.assertEqual(blocked_workflow, self.workflow_state.read_bytes())
        self.assertFalse((self.cycle / "promotion-inputs").exists())
        self.assertFalse(self.basis.exists())
        self.assertFalse(self.canonical.exists())

    def test_generated_replacements_reject_blocked_foreign_cycle_state(self) -> None:
        self.basis.unlink()
        shutil.rmtree(self.cycle / "promotion-inputs")
        blocked_cycle = f"""cycle_id: demo-scope
workflow_status: accepted-promotion-ready-not-promoted
stage_status: blocked-input
current_stage: ft-scope-analyzer
reviewer_stage_status: accepted
writer_draft_sha256: {sha256(self.candidate)}
accepted_terminal_state: true
final_promoted: false
draft_or_unsigned: true
promotion_status: ready-not-promoted
canonical_test_cases: test-cases/1-demo.md
blocking_reasons:
  - source selection is blocked
""".encode("utf-8")
        self.cycle_state.write_bytes(blocked_cycle)

        with self.assertRaises(PromotionBlocked) as raised:
            self.build_and_promote()

        self.assertEqual("PROMO-NOT-ACCEPTED", raised.exception.code)
        self.assertEqual(blocked_cycle, self.cycle_state.read_bytes())
        self.assertFalse((self.cycle / "promotion-inputs").exists())
        self.assertFalse(self.basis.exists())
        self.assertFalse(self.canonical.exists())

    def test_explicit_replacements_cannot_bypass_blocked_workflow_state(self) -> None:
        self.basis.unlink()
        blocked_workflow = b"""ft_slug: demo
scope_slug: demo-scope
current_stage: ft-scope-analyzer
stage_status: blocked-input
next_skill: ft-scope-analyzer
blocking_reasons:
  - source selection is blocked
"""
        self.workflow_state.write_bytes(blocked_workflow)

        with self.assertRaises(PromotionBlocked) as raised:
            self.build_basis(
                reset=False,
                cycle_state_replacement_path=self.cycle_after,
                workflow_state_replacement_path=self.workflow_after,
            )

        self.assertEqual("PROMO-INVALID-WORKFLOW-STATE", raised.exception.code)
        self.assertEqual(blocked_workflow, self.workflow_state.read_bytes())
        self.assertFalse(self.basis.exists())
        self.assertFalse(self.canonical.exists())

    def test_signed_off_workflow_replacement_cannot_preserve_blockers(self) -> None:
        self.basis.unlink()
        workflow_after = self.workflow_after.read_text(encoding="utf-8").replace(
            "blocking_reasons: []",
            "blocking_reasons:\n  - unresolved terminal blocker",
        )
        self.workflow_after.write_text(workflow_after, encoding="utf-8")

        with self.assertRaises(PromotionBlocked) as raised:
            self.build_basis(reset=False)

        self.assertEqual("PROMO-INVALID-WORKFLOW-STATE", raised.exception.code)
        self.assertFalse(self.basis.exists())
        self.assertFalse(self.canonical.exists())

    def test_generator_does_not_fabricate_missing_semantic_matrix_or_state_inputs(self) -> None:
        self.basis.unlink()
        shutil.rmtree(self.cycle / "promotion-inputs")
        self.matrix.unlink()

        with self.assertRaises(PromotionBlocked) as raised:
            self.build_and_promote()

        self.assertEqual("PROMO-MISSING-BUILDER-INPUT", raised.exception.code)
        self.assertFalse(self.matrix.exists())
        self.assertFalse((self.cycle / "promotion-inputs").exists())
        self.assertFalse(self.basis.exists())
        self.assertFalse(self.canonical.exists())

    def test_generator_ignores_historical_signed_off_handoff_for_same_scope(self) -> None:
        self.basis.unlink()
        shutil.rmtree(self.cycle / "promotion-inputs")
        historical = self.ft / "work" / "stage-handoffs" / "00-demo-scope-old"
        historical.mkdir(parents=True)
        (historical / "prompt.reviewer-to-ui-prep.md").write_text(
            "# Historical handoff\n",
            encoding="utf-8",
        )
        (historical / "workflow-state.yaml").write_text(
            """ft_slug: demo
scope_slug: demo-scope
current_stage: ft-test-case-iteration
stage_status: signed-off
next_skill: ft-ui-automation-prep
""",
            encoding="utf-8",
        )

        result = self.build_and_promote()

        self.assertEqual("promoted", result.status)
        basis = json.loads(self.basis.read_text(encoding="utf-8"))
        self.assertEqual(self.binding(self.prompt), basis["final_aliases"]["handoff_prompt"])

    def test_generator_ignores_malformed_handoff_for_foreign_scope(self) -> None:
        self.basis.unlink()
        shutil.rmtree(self.cycle / "promotion-inputs")
        foreign = self.ft / "work" / "stage-handoffs" / "99-foreign-scope"
        foreign.mkdir(parents=True)
        (foreign / "prompt.reviewer-to-ui-prep.md").write_text(
            "# Foreign handoff\n",
            encoding="utf-8",
        )
        (foreign / "workflow-state.yaml").write_text(
            """ft_slug: demo
scope_slug: foreign-scope
current_stage: ft-test-case-iteration
stage_status: blocked-input
next_skill: none
latest_artifacts:
  nested:
    unsupported: shape
""",
            encoding="utf-8",
        )

        result = self.build_and_promote()

        self.assertEqual("promoted", result.status)

    def test_builder_rejects_fabricated_findings_alias_not_bound_by_seed(self) -> None:
        self.basis.unlink()
        fabricated = self.cycle / "outputs" / "fabricated-findings.md"
        fabricated.write_text("# Fabricated findings\n", encoding="utf-8")
        self.workflow_after.write_text(
            self.workflow_after.read_text(encoding="utf-8").replace(
                "final_findings: work/review-cycles/demo-scope/outputs/final-findings.md",
                "final_findings: work/review-cycles/demo-scope/outputs/fabricated-findings.md",
            ),
            encoding="utf-8",
        )

        with self.assertRaises(PromotionBlocked) as raised:
            self.build_and_promote()

        self.assertEqual("PROMO-BUILDER-BINDING-MISMATCH", raised.exception.code)
        self.assertFalse(self.basis.exists())
        self.assertFalse(self.canonical.exists())

    def test_builder_conflict_is_not_overwritten(self) -> None:
        built = self.build_basis()
        payload = json.loads(self.basis.read_text(encoding="utf-8"))
        payload["scope_slug"] = "other-scope"
        write_json(self.basis, payload)
        conflicting_bytes = self.basis.read_bytes()

        with self.assertRaises(PromotionBlocked) as raised:
            self.build_basis(reset=False)

        self.assertEqual("PROMO-BASIS-CONFLICT", raised.exception.code)
        self.assertEqual(conflicting_bytes, self.basis.read_bytes())
        self.assertNotEqual(built.basis_sha256, sha256(self.basis))
        self.assertFalse(self.canonical.exists())

    def test_one_command_failure_rolls_back_and_exact_retry_succeeds(self) -> None:
        self.basis.unlink()
        cycle_before = self.cycle_state.read_bytes()
        workflow_before = self.workflow_state.read_bytes()

        def fail(phase: str) -> None:
            if phase == "after-state-updates":
                raise RuntimeError("injected one-command failure")

        with self.assertRaisesRegex(RuntimeError, "injected one-command failure"):
            self.build_and_promote(fault_injector=fail)

        self.assertTrue(self.basis.is_file())
        self.assertFalse(self.canonical.exists())
        self.assertEqual(cycle_before, self.cycle_state.read_bytes())
        self.assertEqual(workflow_before, self.workflow_state.read_bytes())
        self.assertFalse((self.cycle / "versions" / "signed-off").exists())

        retried = self.build_and_promote()

        self.assertEqual("promoted", retried.status)
        self.assertEqual(self.candidate_bytes, self.canonical.read_bytes())

    def test_one_command_replay_is_verified_idempotent_without_gate_rerun(self) -> None:
        self.basis.unlink()
        calls = 0

        def counting_gate(**kwargs: Any):
            nonlocal calls
            calls += 1
            return validate_production_tc_draft(**kwargs)

        first = self.build_and_promote(production_gate=counting_gate)
        receipt_before = first.receipt_path.read_bytes()
        canonical_before = self.canonical.read_bytes()
        second = self.build_and_promote(production_gate=counting_gate)

        self.assertEqual("promoted", first.status)
        self.assertEqual("already-promoted", second.status)
        self.assertEqual(1, calls)
        self.assertEqual(receipt_before, second.receipt_path.read_bytes())
        self.assertEqual(canonical_before, self.canonical.read_bytes())
        self.assertIn("idempotency_check", second.phase_timings_ms)
        self.assertFalse((self.repo / ".qa-agent-promotion-locks").exists())

    def test_idempotent_replay_rejects_mutated_snapshot(self) -> None:
        self.basis.unlink()
        first = self.build_and_promote()
        snapshot_candidate = (
            self.cycle
            / "versions"
            / "signed-off"
            / "test-cases"
            / "1-demo.md"
        )
        snapshot_candidate.write_bytes(snapshot_candidate.read_bytes() + b"tampered")

        with self.assertRaises(PromotionBlocked) as raised:
            self.build_and_promote()

        self.assertEqual("PROMO-IDEMPOTENCY-CONFLICT", raised.exception.code)
        self.assertEqual(self.candidate_bytes, self.canonical.read_bytes())
        self.assertTrue(first.receipt_path.is_file())

    def test_idempotent_replay_rejects_self_consistent_but_unbound_alias_snapshot(self) -> None:
        self.basis.unlink()
        self.build_and_promote()
        snapshot_root = self.cycle / "versions" / "signed-off"
        alias_relative = (
            "work/review-cycles/demo-scope/outputs/final-traceability-matrix.md"
        )
        snapshot_alias = snapshot_root / Path(alias_relative)
        mutated = snapshot_alias.read_bytes() + b"tampered"
        snapshot_alias.write_bytes(mutated)
        manifest_path = snapshot_root / "snapshot-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for item in manifest["files"]:
            if item["path"] == alias_relative:
                item["sha256"] = hashlib.sha256(mutated).hexdigest()
                item["size_bytes"] = len(mutated)
        write_json(manifest_path, manifest)

        with self.assertRaises(PromotionBlocked) as raised:
            self.build_and_promote()

        self.assertEqual("PROMO-IDEMPOTENCY-CONFLICT", raised.exception.code)
        self.assertEqual(self.candidate_bytes, self.canonical.read_bytes())

    def test_idempotent_replay_rejects_mutated_snapshot_yaml_manifest(self) -> None:
        self.basis.unlink()
        self.build_and_promote()
        yaml_manifest = (
            self.cycle
            / "versions"
            / "signed-off"
            / "snapshot-manifest.yaml"
        )
        yaml_manifest.write_bytes(yaml_manifest.read_bytes() + b"# tampered\n")

        with self.assertRaises(PromotionBlocked) as raised:
            self.build_and_promote()

        self.assertEqual("PROMO-IDEMPOTENCY-CONFLICT", raised.exception.code)

    def test_promotion_denies_structured_execution_dependencies(self) -> None:
        payload = json.loads(self.prepared_package.read_text(encoding="utf-8"))
        payload["release_status"] = {
            "contract": "prepared-package-release-status-v1",
            "output_mode": "draft-with-blocking-gaps",
            "release_eligible": False,
            "blocking_gap_ids": ["GAP-EXECUTION-001"],
            "execution_dependency_registry": [
                {
                    "assertion_id": "ASSERT-BLOCKED-001",
                    "source_row_id": "SRC-BLOCKED-001",
                    "atom_id": "ATOM-BLOCKED-001",
                    "obligation_ids": ["OBL-BLOCKED-001"],
                    "gap_ids": ["GAP-EXECUTION-001"],
                    "risk": "high",
                    "rationale": "A reproducible execution fixture is not registered.",
                    "route": "excluded-from-ready-subset",
                }
            ],
            "excluded_execution_obligation_ids": ["OBL-BLOCKED-001"],
            "unsigned_status": "blocked-execution-dependencies",
            "release_blocking_finding_codes": [
                "blocking-source-first-gap",
                "source-execution-dependency-blocked",
            ],
        }
        without_digest = {
            key: value for key, value in payload.items() if key != "package_digest"
        }
        payload["package_digest"] = hashlib.sha256(
            json.dumps(
                without_digest,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        write_json(self.prepared_package, payload)
        basis = json.loads(self.basis.read_text(encoding="utf-8"))
        basis["prepared_package"] = self.binding(self.prepared_package)
        write_json(self.basis, basis)

        with self.assertRaises(PromotionBlocked) as caught:
            self.promote(validate_only=True)

        self.assertEqual(
            "PROMO-BLOCKED-EXECUTION-DEPENDENCIES",
            caught.exception.code,
        )

    def test_promotion_basis_artifacts_must_match_prepared_package(self) -> None:
        alternate = self.ft / "work" / "prepared" / "alternate-source.md"
        alternate.write_bytes(self.source.read_bytes())
        basis = json.loads(self.basis.read_text(encoding="utf-8"))
        basis["source_basis"] = self.binding(alternate)
        write_json(self.basis, basis)

        with self.assertRaises(PromotionBlocked) as caught:
            self.promote(validate_only=True)

        self.assertEqual("PROMO-PACKAGE-BINDING-MISMATCH", caught.exception.code)

    def test_tampered_candidate_hash_is_blocked_before_publication(self) -> None:
        self.candidate.write_bytes(self.candidate_bytes + b"tampered")

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote()

        self.assertEqual("PROMO-HASH-MISMATCH", raised.exception.code)
        self.assertFalse(self.canonical.exists())

    def test_basis_parse_and_receipt_hash_use_one_rechecked_byte_snapshot(self) -> None:
        original_snapshot = promotion_module._read_basis_snapshot
        reads = 0

        def mutate_after_locked_read(path: Path):
            nonlocal reads
            snapshot = original_snapshot(path)
            reads += 1
            if reads == 2:
                payload = json.loads(path.read_text(encoding="utf-8"))
                payload["scope_slug"] = "tampered-after-parse"
                write_json(path, payload)
            return snapshot

        with patch.object(
            promotion_module,
            "_read_basis_snapshot",
            side_effect=mutate_after_locked_read,
        ):
            with self.assertRaises(PromotionBlocked) as raised:
                self.promote()

        self.assertEqual(2, reads)
        self.assertEqual("PROMO-HASH-MISMATCH", raised.exception.code)
        self.assertFalse(self.canonical.exists())
        self.assertNotEqual(self.cycle_after.read_bytes(), self.cycle_state.read_bytes())
        self.assertNotEqual(self.workflow_after.read_bytes(), self.workflow_state.read_bytes())
        self.assertFalse((self.cycle / "promotion").exists())

    def test_direct_promotion_cannot_rewrite_blocked_workflow_state(self) -> None:
        blocked_workflow = b"""ft_slug: demo
scope_slug: demo-scope
current_stage: ft-scope-analyzer
stage_status: blocked-input
next_skill: ft-scope-analyzer
blocking_reasons:
  - unresolved source contract
"""
        self.workflow_state.write_bytes(blocked_workflow)
        basis = json.loads(self.basis.read_text(encoding="utf-8"))
        workflow_update = next(
            item
            for item in basis["state_updates"]
            if item["role"] == "workflow-state"
        )
        workflow_update["before_sha256"] = sha256(self.workflow_state)
        write_json(self.basis, basis)

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote()

        self.assertEqual("PROMO-INVALID-WORKFLOW-STATE", raised.exception.code)
        self.assertEqual(blocked_workflow, self.workflow_state.read_bytes())
        self.assertFalse(self.canonical.exists())
        self.assertFalse((self.cycle / "promotion").exists())

    def test_existing_target_is_denied_by_default(self) -> None:
        self.canonical.parent.mkdir(parents=True)
        self.canonical.write_bytes(b"existing canonical")

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote()

        self.assertEqual("PROMO-TARGET-EXISTS", raised.exception.code)
        self.assertEqual(b"existing canonical", self.canonical.read_bytes())

    def test_failure_after_state_updates_rolls_back_publication_and_state(self) -> None:
        cycle_before = self.cycle_state.read_bytes()
        workflow_before = self.workflow_state.read_bytes()

        def fail(phase: str) -> None:
            if phase == "after-state-updates":
                raise RuntimeError("injected state failure")

        with self.assertRaisesRegex(RuntimeError, "injected state failure"):
            self.promote(fault_injector=fail)

        self.assertFalse(self.canonical.exists())
        self.assertEqual(cycle_before, self.cycle_state.read_bytes())
        self.assertEqual(workflow_before, self.workflow_state.read_bytes())
        self.assertFalse((self.cycle / "promotion").exists())
        self.assertFalse((self.cycle / "versions" / "signed-off").exists())
        self.assertFalse((self.cycle / "promotion.lock").exists())
        self.assertFalse((self.repo / ".qa-agent-promotion-locks").exists())

    def test_failed_explicit_overwrite_restores_prior_canonical_bytes(self) -> None:
        self.canonical.parent.mkdir(parents=True)
        prior = b"prior signed-off bytes\r\n"
        self.canonical.write_bytes(prior)
        basis = json.loads(self.basis.read_text(encoding="utf-8"))
        basis["publication"]["expected_prior_sha256"] = sha256(self.canonical)
        write_json(self.basis, basis)

        def fail(phase: str) -> None:
            if phase == "after-state-updates":
                raise RuntimeError("injected overwrite failure")

        with self.assertRaisesRegex(RuntimeError, "injected overwrite failure"):
            self.promote(allow_overwrite=True, fault_injector=fail)

        self.assertEqual(prior, self.canonical.read_bytes())
        self.assertFalse((self.cycle / "versions" / "signed-off").exists())

    def test_existing_lock_blocks_without_removing_foreign_lock(self) -> None:
        lock = self.cycle / "promotion.lock"
        lock.write_text("pid=999\n", encoding="ascii")

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote()

        self.assertEqual("PROMO-LOCKED", raised.exception.code)
        self.assertTrue(lock.exists())
        self.assertFalse(self.canonical.exists())

    def test_target_lock_blocks_a_second_cycle_for_same_publication_targets(self) -> None:
        second_cycle = self.ft / "work" / "review-cycles" / "demo-scope-second"
        second_cycle.mkdir(parents=True)
        second_basis = second_cycle / "promotion-basis.json"
        payload = json.loads(self.basis.read_text(encoding="utf-8"))
        payload["cycle_dir"] = self.rel(second_cycle)
        write_json(second_basis, payload)
        self.assert_concurrent_target_overlap_is_blocked(
            second_cycle=second_cycle,
            second_basis=second_basis,
        )

    def test_target_lock_blocks_same_canonical_with_different_workflow_state(self) -> None:
        second_cycle = self.ft / "work" / "review-cycles" / "demo-scope-second"
        second_cycle.mkdir(parents=True)
        second_handoff = self.ft / "work" / "stage-handoffs" / "02-demo-scope"
        second_handoff.mkdir(parents=True)
        second_workflow = second_handoff / "workflow-state.yaml"
        second_workflow.write_bytes(self.workflow_state.read_bytes())
        second_basis = second_cycle / "promotion-basis.json"
        payload = json.loads(self.basis.read_text(encoding="utf-8"))
        payload["cycle_dir"] = self.rel(second_cycle)
        workflow_update = next(
            item
            for item in payload["state_updates"]
            if item["role"] == "workflow-state"
        )
        workflow_update["path"] = self.rel(second_workflow)
        workflow_update["before_sha256"] = sha256(second_workflow)
        write_json(second_basis, payload)

        self.assert_concurrent_target_overlap_is_blocked(
            second_cycle=second_cycle,
            second_basis=second_basis,
        )

    def test_target_lock_blocks_same_workflow_state_with_different_canonical(self) -> None:
        second_cycle = self.ft / "work" / "review-cycles" / "demo-scope-second"
        second_cycle.mkdir(parents=True)
        second_canonical = self.ft / "test-cases" / "2-demo.md"
        second_basis = second_cycle / "promotion-basis.json"
        payload = json.loads(self.basis.read_text(encoding="utf-8"))
        payload["cycle_dir"] = self.rel(second_cycle)
        payload["publication"]["canonical_path"] = self.rel(second_canonical)
        write_json(second_basis, payload)

        self.assert_concurrent_target_overlap_is_blocked(
            second_cycle=second_cycle,
            second_basis=second_basis,
        )
        self.assertFalse(second_canonical.exists())

    def test_target_lock_partial_acquisition_preserves_foreign_lock(self) -> None:
        lock_paths = sorted(
            (
                self.target_lock_path(self.canonical),
                self.target_lock_path(self.workflow_state),
            ),
            key=lambda item: item.name,
        )
        acquired_first, foreign_lock = lock_paths
        foreign_lock.parent.mkdir(parents=True)
        foreign_lock.write_text("pid=999\n", encoding="ascii")

        try:
            with self.assertRaises(PromotionBlocked) as raised:
                self.promote()

            self.assertEqual("PROMO-TARGET-LOCKED", raised.exception.code)
            self.assertFalse(acquired_first.exists())
            self.assertTrue(foreign_lock.exists())
            self.assertFalse(self.canonical.exists())
        finally:
            foreign_lock.unlink(missing_ok=True)
            foreign_lock.parent.rmdir()

    def test_candidate_mutation_after_publication_is_detected_and_rolled_back(self) -> None:
        cycle_before = self.cycle_state.read_bytes()
        workflow_before = self.workflow_state.read_bytes()

        def mutate(phase: str) -> None:
            if phase == "after-publication":
                self.candidate.write_bytes(self.candidate_bytes + b"mutated")

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote(fault_injector=mutate)

        self.assertEqual("PROMO-HASH-MISMATCH", raised.exception.code)
        self.assertFalse(self.canonical.exists())
        self.assertEqual(cycle_before, self.cycle_state.read_bytes())
        self.assertEqual(workflow_before, self.workflow_state.read_bytes())
        self.assertFalse((self.cycle / "promotion").exists())
        self.assertFalse((self.cycle / "versions" / "signed-off").exists())

    def test_final_alias_mutation_after_publication_is_detected_and_rolled_back(self) -> None:
        matrix_before = self.matrix.read_bytes()

        def mutate(phase: str) -> None:
            if phase == "after-publication":
                self.matrix.write_bytes(matrix_before + b"mutated")

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote(fault_injector=mutate)

        self.assertEqual("PROMO-HASH-MISMATCH", raised.exception.code)
        self.assertFalse(self.canonical.exists())
        self.assertFalse((self.cycle / "promotion").exists())
        self.assertFalse((self.cycle / "versions" / "signed-off").exists())

    def test_source_chain_mutation_after_publication_is_detected_and_rolled_back(self) -> None:
        source_before = self.source.read_bytes()

        def mutate(phase: str) -> None:
            if phase == "after-publication":
                self.source.write_bytes(source_before + b"mutated")

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote(fault_injector=mutate)

        self.assertEqual("PROMO-HASH-MISMATCH", raised.exception.code)
        self.assertFalse(self.canonical.exists())
        self.assertFalse((self.cycle / "promotion").exists())
        self.assertFalse((self.cycle / "versions" / "signed-off").exists())

    def test_external_state_change_is_not_clobbered_when_cas_blocks_commit(self) -> None:
        external_state = self.workflow_state.read_bytes() + b"# external change\n"

        def mutate(phase: str) -> None:
            if phase == "after-snapshot-commit":
                self.workflow_state.write_bytes(external_state)

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote(fault_injector=mutate)

        self.assertEqual("PROMO-HASH-MISMATCH", raised.exception.code)
        self.assertEqual(external_state, self.workflow_state.read_bytes())
        self.assertFalse(self.canonical.exists())
        self.assertFalse((self.cycle / "promotion").exists())
        self.assertFalse((self.cycle / "versions" / "signed-off").exists())

    def test_validate_only_and_dry_run_do_not_mutate_canonical_or_states(self) -> None:
        cycle_before = self.cycle_state.read_bytes()
        workflow_before = self.workflow_state.read_bytes()

        validated = self.promote(validate_only=True)
        dry_run = self.promote(dry_run=True)

        self.assertEqual("validated", validated.status)
        self.assertEqual("dry-run-passed", dry_run.status)
        self.assertFalse(self.canonical.exists())
        self.assertEqual(cycle_before, self.cycle_state.read_bytes())
        self.assertEqual(workflow_before, self.workflow_state.read_bytes())
        self.assertFalse((self.cycle / "promotion").exists())

    def test_blocking_source_gap_rejects_every_promotion_mode_before_writes(self) -> None:
        changed = PreparedObligationSet.create(
            package_id=self.obligation_set.package_id,
            obligations=self.obligation_set.obligations,
            coverage_gaps=(
                replace(self.obligation_set.coverage_gaps[0], blocking=True),
            ),
            evidence_text=self.source.read_text(encoding="utf-8"),
        )
        self.replace_obligation_set(changed)
        cycle_before = self.cycle_state.read_bytes()
        workflow_before = self.workflow_state.read_bytes()

        for options in ({"validate_only": True}, {"dry_run": True}, {}):
            with self.subTest(options=options):
                with self.assertRaises(PromotionBlocked) as raised:
                    self.promote(**options)
                self.assertEqual(
                    "PROMO-BLOCKING-SOURCE-GAPS", raised.exception.code
                )
                self.assertFalse(self.canonical.exists())
                self.assertEqual(cycle_before, self.cycle_state.read_bytes())
                self.assertEqual(workflow_before, self.workflow_state.read_bytes())
                self.assertFalse((self.cycle / "promotion").exists())
                self.assertFalse((self.cycle / "versions" / "signed-off").exists())

    def test_missing_normalized_review_result_reports_exact_blocked_input(self) -> None:
        self.review_result.unlink()

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote()

        self.assertEqual("PROMO-MISSING-REVIEW-RESULT", raised.exception.code)
        self.assertIn("review-result", str(raised.exception))

    def test_normalized_review_builder_emits_v4_compact_receipt(self) -> None:
        payload = build_normalized_review_result(
            reviewed_draft_path=self.rel(self.candidate),
            reviewed_draft_sha256=sha256(self.candidate),
            reviewed_source_basis_sha256=sha256(self.source),
            reviewed_obligation_set_sha256=sha256(self.obligations),
            obligation_reviews=(
                {"obligation_id": "OBL-001", "verdict": "covered"},
                {"obligation_id": "OBL-002", "verdict": "gap-preserved"},
            ),
            dimension_reviews=(),
            findings=(),
            summary="Accepted without error findings.",
        )

        self.assertEqual(2, payload["schema_version"])
        self.assertEqual(4, payload["contract_version"])
        self.assertEqual(
            [
                {"obligation_id": "OBL-001", "verdict": "covered"},
                {"obligation_id": "OBL-002", "verdict": "gap-preserved"},
            ],
            payload["obligation_reviews"],
        )
        self.assertEqual([], payload["dimension_reviews"])

    def test_obligation_receipt_must_match_bound_obligation_set_exactly(self) -> None:
        review = json.loads(self.review_result.read_text(encoding="utf-8"))
        review["obligation_reviews"] = review["obligation_reviews"][:1]
        self.replace_review_result(review)

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote()

        self.assertEqual("PROMO-INVALID-REVIEW-RESULT", raised.exception.code)
        self.assertIn("does not match", str(raised.exception))

    def test_testable_obligation_requires_covered_verdict(self) -> None:
        review = json.loads(self.review_result.read_text(encoding="utf-8"))
        review["obligation_reviews"][0]["verdict"] = "gap-preserved"
        self.replace_review_result(review)

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote()

        self.assertEqual("PROMO-INVALID-REVIEW-RESULT", raised.exception.code)
        self.assertIn("OBL-001", str(raised.exception))

    def test_non_testable_obligation_requires_gap_preserved_verdict(self) -> None:
        review = json.loads(self.review_result.read_text(encoding="utf-8"))
        review["obligation_reviews"][1]["verdict"] = "covered"
        self.replace_review_result(review)

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote()

        self.assertEqual("PROMO-INVALID-REVIEW-RESULT", raised.exception.code)
        self.assertIn("OBL-002", str(raised.exception))

    def test_duplicate_obligation_receipt_id_is_rejected(self) -> None:
        review = json.loads(self.review_result.read_text(encoding="utf-8"))
        review["obligation_reviews"][1]["obligation_id"] = "OBL-001"
        self.replace_review_result(review)

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote()

        self.assertEqual("PROMO-INVALID-REVIEW-RESULT", raised.exception.code)
        self.assertIn("duplicate", str(raised.exception))

    def test_obligation_receipt_item_must_have_only_compact_fields(self) -> None:
        review = json.loads(self.review_result.read_text(encoding="utf-8"))
        review["obligation_reviews"][0]["note"] = "Not part of the compact receipt."
        self.replace_review_result(review)

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote()

        self.assertEqual("PROMO-INVALID-REVIEW-RESULT", raised.exception.code)
        self.assertIn("invalid fields", str(raised.exception))

    def test_obsolete_v3_review_result_is_rejected(self) -> None:
        review = json.loads(self.review_result.read_text(encoding="utf-8"))
        review["schema_version"] = 1
        review["contract_version"] = 3
        self.replace_review_result(review)

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote()

        self.assertEqual("PROMO-INVALID-REVIEW-RESULT", raised.exception.code)
        self.assertIn("schema v2", str(raised.exception))

    def test_non_verified_dimension_is_rejected_but_empty_dimensions_are_allowed(self) -> None:
        validated = self.promote(validate_only=True)
        self.assertEqual("validated", validated.status)

        review = json.loads(self.review_result.read_text(encoding="utf-8"))
        review["dimension_reviews"] = [
            {
                "dimension": "test-design",
                "verdict": "failed",
                "source_refs": ["BSR 1"],
                "note": "The design is incomplete.",
            }
        ]
        self.replace_review_result(review)

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote(validate_only=True)

        self.assertEqual("PROMO-INVALID-REVIEW-RESULT", raised.exception.code)
        self.assertIn("dimension", str(raised.exception))

    def test_source_first_v4_rejects_fabricated_plain_markdown_binding(self) -> None:
        self.replace_source_basis(
            "# Fabricated plain evidence\n\n"
            "BSR 1: Search by application number.\n\n"
            "BSR 2: The fallback behavior is not specified.\n\n"
            "## Reviewer dimension source bindings\n\n"
            + render_reviewer_dimension_source_bindings(
                ReviewerDimensionSourceBindings.create({})
            )
            + "\n"
        )

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote(validate_only=True)

        self.assertEqual("PROMO-INVALID-SOURCE-BASIS", raised.exception.code)
        self.assertIn("legacy plain Markdown", str(raised.exception))

    def test_source_assertion_contract_scope_must_match_bound_scope(self) -> None:
        self.replace_source_basis(
            self.render_source_basis(scope_slug="different-scope")
        )

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote(validate_only=True)

        self.assertEqual("PROMO-INVALID-SOURCE-BASIS", raised.exception.code)
        self.assertIn("scope", str(raised.exception))

    def test_source_assertion_contract_rejects_changed_binary_source_of_truth(self) -> None:
        self.semantic_truth.write_bytes(b"PK\x03\x04semantic-source-v2")

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote(validate_only=True)

        self.assertEqual("PROMO-PREPARED-PACKAGE-INVALID", raised.exception.code)
        self.assertIn("registered full source hash mismatch", str(raised.exception))

    def test_bound_scope_must_match_signed_off_workflow_replacement(self) -> None:
        self.replace_source_basis(
            self.render_source_basis(scope_slug="different-scope")
        )
        basis = json.loads(self.basis.read_text(encoding="utf-8"))
        basis["scope_slug"] = "different-scope"
        write_json(self.basis, basis)

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote(validate_only=True)

        self.assertEqual("PROMO-SCOPE-MISMATCH", raised.exception.code)
        self.assertIn("scope_slug", str(raised.exception))

    def test_source_assertion_contract_requires_review_receipt(self) -> None:
        authenticated = self.render_source_basis()
        basis_only = authenticated.split(
            "### Independent source review receipt", 1
        )[0]
        dimension_tail = authenticated.split(
            "## Reviewer dimension source bindings", 1
        )[1]
        self.replace_source_basis(
            basis_only
            + "## Reviewer dimension source bindings"
            + dimension_tail
        )

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote(validate_only=True)

        self.assertEqual("PROMO-INVALID-SOURCE-BASIS", raised.exception.code)
        self.assertIn("complete source-first block", str(raised.exception))

    def test_source_assertion_contract_rejects_changed_review_receipt(self) -> None:
        changed_receipt = self.render_source_basis().replace(
            '"decision":"accepted"',
            '"decision":"changes-required"',
            1,
        )
        self.replace_source_basis(changed_receipt)

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote(validate_only=True)

        self.assertEqual("PROMO-INVALID-SOURCE-BASIS", raised.exception.code)
        self.assertIn("review", str(raised.exception))

    def test_source_assertion_obligation_set_must_match_exactly(self) -> None:
        self.replace_source_basis(
            self.render_source_basis(testable_obligation_ids=("OBL-999",))
        )

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote(validate_only=True)

        self.assertEqual("PROMO-INVALID-SOURCE-BASIS", raised.exception.code)
        self.assertIn("obligations mismatch", str(raised.exception))

    def test_gap_obligation_must_preserve_authenticated_disposition(self) -> None:
        self.replace_source_basis(
            self.render_source_basis(gap_disposition="not-applicable")
        )

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote(validate_only=True)

        self.assertEqual("PROMO-INVALID-SOURCE-BASIS", raised.exception.code)
        self.assertIn("semantic disposition", str(raised.exception))

    def test_obligation_source_refs_must_include_authenticated_canonical_refs(self) -> None:
        changed = PreparedObligationSet.create(
            package_id=self.obligation_set.package_id,
            obligations=(
                self.obligation_set.obligations[0],
                replace(
                    self.obligation_set.obligations[1],
                    source_refs=("SRC-DEMO-002",),
                ),
            ),
            coverage_gaps=self.obligation_set.coverage_gaps,
            evidence_text=self.source.read_text(encoding="utf-8"),
        )
        self.replace_obligation_set(changed)

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote(validate_only=True)

        self.assertEqual("PROMO-INVALID-SOURCE-BASIS", raised.exception.code)
        self.assertIn("source_refs omit", str(raised.exception))

    def test_dimension_cannot_cite_ref_bound_only_to_another_dimension(self) -> None:
        self.replace_source_basis(
            self.render_source_basis(
                dimension_bindings={
                    "input-boundaries": ("BSR 2",),
                    "state-reset": ("BSR 1",),
                }
            )
        )
        review = json.loads(self.review_result.read_text(encoding="utf-8"))
        review["dimension_reviews"] = [
            {
                "dimension": "input-boundaries",
                "verdict": "verified",
                "source_refs": ["BSR 2"],
                "note": "Boundary checked.",
            },
            {
                "dimension": "state-reset",
                "verdict": "verified",
                "source_refs": ["BSR 2"],
                "note": "Incorrect cross-dimension citation.",
            },
        ]
        self.replace_review_result(review)

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote(validate_only=True)

        self.assertEqual("PROMO-INVALID-REVIEW-RESULT", raised.exception.code)
        self.assertIn("exact canonical", str(raised.exception))

    def test_dimension_receipt_cannot_omit_a_bound_source_ref(self) -> None:
        self.replace_source_basis(
            self.render_source_basis(
                dimension_bindings={
                    "state-reset": ("BSR 1", "SRC-RESET-DETAIL")
                }
            )
        )
        review = json.loads(self.review_result.read_text(encoding="utf-8"))
        review["dimension_reviews"] = [
            {
                "dimension": "state-reset",
                "verdict": "verified",
                "source_refs": ["BSR 1"],
                "note": "The second bound source was omitted.",
            }
        ]
        self.replace_review_result(review)

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote(validate_only=True)

        self.assertEqual("PROMO-INVALID-REVIEW-RESULT", raised.exception.code)
        self.assertIn("exact canonical", str(raised.exception))

    def test_source_first_promotion_rejects_missing_dimension_binding_block(self) -> None:
        authenticated = self.render_source_basis()
        self.replace_source_basis(
            authenticated.split("## Reviewer dimension source bindings", 1)[0]
        )

        with self.assertRaises(PromotionBlocked) as raised:
            self.promote(validate_only=True)

        self.assertEqual("PROMO-INVALID-REVIEW-RESULT", raised.exception.code)
        self.assertIn("exactly one reviewer dimension binding block", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
