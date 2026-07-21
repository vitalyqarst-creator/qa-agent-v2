from __future__ import annotations

import json
import hashlib
import unittest
from dataclasses import replace

from test_case_agent.review_cycle.prepared_package import (
    PreparedObligation,
    PreparedObligationSet,
)
from test_case_agent.review_cycle.source_assertions import (
    ApprovedClarification,
    ClarificationClauseBinding,
    MANIFEST_VERSION,
    NO_REQUIRED_CHANGE,
    REVIEW_RECEIPT_VERSION,
    SOURCE_REVIEW_DIMENSIONS,
    ClauseEvidenceBinding,
    EmbeddedSourceAssertionContract,
    RegisteredEvidenceSource,
    RegisteredSource,
    RegisteredArtifact,
    RequirementCodeBinding,
    ScopeBoundaryReview,
    SourceAssertion,
    SourceAssertionManifest,
    SourceAssertionReview,
    SourceAssertionReviewReceipt,
    SourceInventoryReview,
    SourceRow,
)
from test_case_agent.review_cycle.source_projection import (
    SourceProjectionError,
    build_compact_source_projection,
    render_reviewer_obligation_semantic_projection,
    select_draft_testable_obligation_ids,
    source_contract_digest_summary,
)


class SourceProjectionTests(unittest.TestCase):
    def fixture(
        self,
    ) -> tuple[EmbeddedSourceAssertionContract, PreparedObligationSet]:
        source_row = SourceRow(
            source_row_id="SRC-1",
            source_path="fts/demo/source/main.xhtml",
            source_locator="body/row-1",
            bounded_source_text="BSR 1. Source requirement.",
            source_context_class="document-global-constraints",
            candidate_id="SRC-CAND-" + "1" * 24,
            scope_disposition="yes",
            requirement_codes=("BSR 1",),
        )
        assertions = tuple(
            SourceAssertion(
                assertion_id=f"ASSERT-{index:03d}",
                source_path=source_row.source_path,
                source_context_class=source_row.source_context_class,
                locator=source_row.source_locator,
                exact_source_text="BSR 1. Source requirement.",
                canonical_statement=f"Observable property {index} is required.",
                polarity="positive",
                semantic_disposition="testable",
                execution_readiness="ready",
                execution_readiness_rationale=NO_REQUIRED_CHANGE,
                risk="high",
                condition_clauses=("The form is open.",),
                action_clauses=(f"Perform action {index}.",),
                oracle_clauses=(f"Visible result {index} is present.",),
                requirement_codes=("BSR 1",),
                requirement_code_bindings=(
                    RequirementCodeBinding(
                        "BSR 1", "SRC-1", "xhtml-row", "BSR 1"
                    ),
                ),
                clause_evidence_bindings=tuple(
                    ClauseEvidenceBinding(
                        clause_kind=kind,
                        clause_index=0,
                        source_row_id="SRC-1",
                        evidence_role=kind,
                        exact_source_fragment="BSR 1. Source requirement.",
                    )
                    for kind in ("condition", "action", "oracle")
                ),
                source_row_id="SRC-1",
                atom_id=f"ATOM-{index:03d}",
                obligation_ids=(f"OBL-{index:03d}",),
                execution_dependency_gap_ids=(),
                primary_gap_id=None,
            )
            for index in (1, 2)
        )
        manifest = SourceAssertionManifest(
            version=MANIFEST_VERSION,
            scope_slug="demo-scope",
            source_row_extraction_spec_digest="1" * 64,
            source_row_baseline_digest="2" * 64,
            source_row_candidate_count=1,
            coverage_gaps_artifact=RegisteredArtifact(
                "fts/demo/work/coverage-gaps.md", "4" * 64
            ),
            sources=(RegisteredSource(source_row.source_path, "3" * 64),),
            source_rows=(source_row,),
            assertions=assertions,
        )
        receipt = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=manifest.digest,
            decision="accepted",
            assertion_reviews=tuple(
                SourceAssertionReview(
                    assertion_id=assertion.assertion_id,
                    approved_polarity=assertion.polarity,
                    approved_semantic_disposition=assertion.semantic_disposition,
                    approved_execution_readiness=assertion.execution_readiness,
                    approved_risk=assertion.risk,
                    dimension_verdicts={
                        dimension: "verified"
                        for dimension in SOURCE_REVIEW_DIMENSIONS
                    },
                    verdict="verified",
                    required_change=NO_REQUIRED_CHANGE,
                    note="Reviewed independently against the exact source row.",
                )
                for assertion in assertions
            ),
            source_inventory_review=SourceInventoryReview(
                extraction_spec_digest=manifest.source_row_extraction_spec_digest,
                baseline_digest=manifest.source_row_baseline_digest,
                candidate_count=1,
                mapped_source_row_count=1,
                verdict="verified",
                required_change=NO_REQUIRED_CHANGE,
                note="The complete candidate inventory was independently reviewed.",
            ),
            scope_boundary_review=ScopeBoundaryReview(
                verdict="verified",
                checked_context_classes=(),
                reviewed_manifest_contexts=(),
                excluded_contexts=(),
                required_change=NO_REQUIRED_CHANGE,
                note="The bounded scope was independently reviewed in full.",
            ),
        )
        obligations = PreparedObligationSet.create(
            package_id="projection-unit",
            obligations=tuple(
                PreparedObligation(
                    obligation_id=f"OBL-{index:03d}",
                    atom_id=f"ATOM-{index:03d}",
                    source_refs=("SRC-1",),
                    atomic_statement=f"Observable property {index} is required.",
                    observable_oracle=f"Visible result {index} is present.",
                    test_intent=f"Perform action {index}.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    planned_test_case_id=f"TC-DEMO-{index:03d}",
                )
                for index in (1, 2)
            ),
            coverage_gaps=(),
        )
        return EmbeddedSourceAssertionContract(manifest, receipt), obligations

    def clarification_fixture(
        self,
    ) -> tuple[EmbeddedSourceAssertionContract, PreparedObligationSet]:
        contract, obligations = self.fixture()
        exact_answer = "The visible result is confirmed by the user."
        answer_digest = hashlib.sha256(exact_answer.encode("utf-8")).hexdigest()
        clarification = ApprovedClarification(
            clarification_id="CLR-DEMO-001",
            gap_id="GAP-DEMO-001",
            scope_slug=contract.manifest.scope_slug,
            requirement_codes=("BSR 1",),
            authority="user",
            response_status="answered",
            response_type="user-confirmed",
            answered_at="2026-07-15",
            exact_answer=exact_answer,
            exact_answer_sha256=answer_digest,
            evidence_source_path="fts/demo/work/scope-clarification-requests.md",
            evidence_source_sha256="6" * 64,
        )
        first, second = contract.manifest.assertions
        second = replace(
            second,
            clarification_clause_bindings=(
                ClarificationClauseBinding(
                    clarification_id=clarification.clarification_id,
                    clause_kind="oracle",
                    clause_index=0,
                    requirement_codes=("BSR 1",),
                    exact_answer_sha256=answer_digest,
                ),
            ),
        )
        manifest = replace(
            contract.manifest,
            assertions=(first, second),
            clarifications=(clarification,),
            evidence_sources=(
                RegisteredEvidenceSource(
                    clarification.evidence_source_path,
                    clarification.evidence_source_sha256,
                    "approved-clarification",
                ),
            ),
        )
        receipt = replace(
            contract.review_receipt,
            manifest_digest=manifest.digest,
        )
        return EmbeddedSourceAssertionContract(manifest, receipt), obligations

    def test_compact_projection_is_deterministic_and_exact_for_selection(self) -> None:
        contract, obligations = self.fixture()
        kwargs = {
            "role": "writer",
            "contract": contract,
            "obligations": obligations,
            "selected_obligation_ids": ("OBL-002",),
            "source_evidence_path": "prepared/source-evidence.md",
            "source_evidence_sha256": "4" * 64,
            "source_evidence_bytes": 64 * 1024,
            "atomic_obligations_path": "prepared/atomic-obligations.json",
            "atomic_obligations_sha256": "5" * 64,
        }

        first = build_compact_source_projection(**kwargs)
        second = build_compact_source_projection(**kwargs)
        payload = json.loads(first.rendered)

        self.assertEqual(first.rendered, second.rendered)
        self.assertEqual(("ASSERT-002",), first.selected_assertion_ids)
        self.assertEqual(["OBL-002"], payload["selection"]["obligation_ids"])
        self.assertEqual(
            "Observable property 2 is required.",
            payload["assertions"][0]["canonical_statement"],
        )
        self.assertNotIn("Reviewed independently", first.rendered)
        self.assertNotIn("Source requirement", first.rendered)
        self.assertTrue(first.report["passed"])
        self.assertLess(
            first.report["projected_bytes"], first.report["limit_bytes"]
        )

    def test_writer_repair_can_include_verified_same_row_context(self) -> None:
        contract, obligations = self.fixture()

        projection = build_compact_source_projection(
            role="writer",
            contract=contract,
            obligations=obligations,
            selected_obligation_ids=("OBL-002",),
            source_evidence_path="prepared/source-evidence.md",
            source_evidence_sha256="4" * 64,
            source_evidence_bytes=64 * 1024,
            atomic_obligations_path="prepared/atomic-obligations.json",
            atomic_obligations_sha256="5" * 64,
            include_source_row_siblings=True,
        )
        payload = json.loads(projection.rendered)

        self.assertEqual(("ASSERT-001", "ASSERT-002"), projection.selected_assertion_ids)
        self.assertEqual(["OBL-002"], payload["selection"]["obligation_ids"])
        self.assertEqual(2, len(payload["assertions"]))
        self.assertEqual([], payload["assertions"][0]["obligation_bindings"])

    def test_h59_cardinality_projection_fits_role_budget_without_semantic_truncation(self) -> None:
        source_row = SourceRow(
            source_row_id="SRC-H59-001",
            source_path="fts/demo/source/main.xhtml",
            source_locator="body/row-1",
            bounded_source_text="BSR 1. H59 source requirement.",
            source_context_class="document-global-constraints",
            candidate_id="SRC-CAND-" + "9" * 24,
            scope_disposition="yes",
            requirement_codes=("BSR 1",),
        )
        assertion_count = 182
        extra_binding_count = 123
        assertions = []
        obligations = []
        for index in range(1, assertion_count + 1):
            obligation_ids = [f"OBL-{index:03d}"]
            if index <= extra_binding_count:
                obligation_ids.append(f"OBL-{assertion_count + index:03d}")
            statement = f"Observable H59 property {index} is required."
            oracle = f"Visible H59 result {index} is present."
            action = f"Perform H59 action {index}."
            assertions.append(
                SourceAssertion(
                    assertion_id=f"ASSERT-H59-{index:03d}",
                    source_path=source_row.source_path,
                    source_context_class=source_row.source_context_class,
                    locator=source_row.source_locator,
                    exact_source_text=source_row.bounded_source_text,
                    canonical_statement=statement,
                    polarity="positive",
                    semantic_disposition="testable",
                    execution_readiness="ready",
                    execution_readiness_rationale=NO_REQUIRED_CHANGE,
                    risk="high",
                    condition_clauses=("The H59 form is open.",),
                    action_clauses=(action,),
                    oracle_clauses=(oracle,),
                    requirement_codes=("BSR 1",),
                    requirement_code_bindings=(
                        RequirementCodeBinding(
                            "BSR 1", source_row.source_row_id, "xhtml-row", "BSR 1"
                        ),
                    ),
                    clause_evidence_bindings=tuple(
                        ClauseEvidenceBinding(
                            clause_kind=kind,
                            clause_index=0,
                            source_row_id=source_row.source_row_id,
                            evidence_role=kind,
                            exact_source_fragment=source_row.bounded_source_text,
                        )
                        for kind in ("condition", "action", "oracle")
                    ),
                    source_row_id=source_row.source_row_id,
                    atom_id=f"ATOM-H59-{index:03d}",
                    obligation_ids=tuple(obligation_ids),
                    execution_dependency_gap_ids=(),
                    primary_gap_id=None,
                )
            )
            obligations.extend(
                PreparedObligation(
                    obligation_id=obligation_id,
                    atom_id=f"ATOM-H59-{index:03d}",
                    source_refs=("BSR 1", source_row.source_row_id),
                    atomic_statement=statement,
                    observable_oracle=oracle,
                    test_intent=action,
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    planned_test_case_id=f"TC-H59-{index:03d}",
                )
                for obligation_id in obligation_ids
            )
        manifest = SourceAssertionManifest(
            version=MANIFEST_VERSION,
            scope_slug="h59-scope",
            source_row_extraction_spec_digest="1" * 64,
            source_row_baseline_digest="2" * 64,
            source_row_candidate_count=1,
            coverage_gaps_artifact=RegisteredArtifact(
                "fts/demo/work/coverage-gaps.md", "4" * 64
            ),
            sources=(RegisteredSource(source_row.source_path, "3" * 64),),
            source_rows=(source_row,),
            assertions=tuple(assertions),
        )
        receipt = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=manifest.digest,
            decision="accepted",
            assertion_reviews=tuple(
                SourceAssertionReview(
                    assertion_id=assertion.assertion_id,
                    approved_polarity=assertion.polarity,
                    approved_semantic_disposition=assertion.semantic_disposition,
                    approved_execution_readiness=assertion.execution_readiness,
                    approved_risk=assertion.risk,
                    dimension_verdicts={
                        dimension: "verified"
                        for dimension in SOURCE_REVIEW_DIMENSIONS
                    },
                    verdict="verified",
                    required_change=NO_REQUIRED_CHANGE,
                    note="Reviewed independently against the exact H59 source row.",
                )
                for assertion in assertions
            ),
            source_inventory_review=SourceInventoryReview(
                extraction_spec_digest=manifest.source_row_extraction_spec_digest,
                baseline_digest=manifest.source_row_baseline_digest,
                candidate_count=1,
                mapped_source_row_count=1,
                verdict="verified",
                required_change=NO_REQUIRED_CHANGE,
                note="The complete H59 candidate inventory was independently reviewed.",
            ),
            scope_boundary_review=ScopeBoundaryReview(
                verdict="verified",
                checked_context_classes=(),
                reviewed_manifest_contexts=(),
                excluded_contexts=(),
                required_change=NO_REQUIRED_CHANGE,
                note="The bounded H59 scope was independently reviewed in full.",
            ),
        )
        obligation_set = PreparedObligationSet.create(
            package_id="h59-projection",
            obligations=tuple(obligations),
            coverage_gaps=(),
        )
        selected_ids = tuple(item.obligation_id for item in obligations)

        writer = build_compact_source_projection(
            role="writer",
            contract=EmbeddedSourceAssertionContract(manifest, receipt),
            obligations=obligation_set,
            selected_obligation_ids=selected_ids,
            source_evidence_path="prepared/source-evidence.md",
            source_evidence_sha256="5" * 64,
            source_evidence_bytes=1200 * 1024,
            atomic_obligations_path="prepared/atomic-obligations.json",
            atomic_obligations_sha256="6" * 64,
        )
        reviewer = build_compact_source_projection(
            role="reviewer",
            contract=EmbeddedSourceAssertionContract(manifest, receipt),
            obligations=obligation_set,
            selected_obligation_ids=selected_ids,
            source_evidence_path="prepared/source-evidence.md",
            source_evidence_sha256="5" * 64,
            source_evidence_bytes=1200 * 1024,
            atomic_obligations_path="prepared/atomic-obligations.json",
            atomic_obligations_sha256="6" * 64,
        )

        self.assertEqual(305, writer.report["selected_obligation_count"])
        self.assertEqual(182, writer.report["selected_assertion_count"])
        self.assertTrue(writer.report["passed"], writer.report)
        self.assertTrue(reviewer.report["passed"], reviewer.report)
        self.assertEqual(182, len(json.loads(writer.rendered)["assertions"]))
        self.assertLess(
            reviewer.report["projected_bytes"],
            writer.report["projected_bytes"],
        )
        reviewer_assertion = json.loads(reviewer.rendered)["assertions"][0]
        self.assertIn("canonical_statement", reviewer_assertion)
        self.assertIn("oracle_clauses", reviewer_assertion)
        self.assertNotIn("execution_readiness_rationale", reviewer_assertion)
        self.assertNotIn("dictionary_requirements", reviewer_assertion["obligation_bindings"][0])

    def test_writer_and_reviewer_projection_carry_exact_clarification_provenance(self) -> None:
        contract, obligations = self.clarification_fixture()
        rendered_by_role = {}
        for role in ("writer", "reviewer"):
            projection = build_compact_source_projection(
                role=role,
                contract=contract,
                obligations=obligations,
                selected_obligation_ids=("OBL-002",),
                source_evidence_path="prepared/source-evidence.md",
                source_evidence_sha256="4" * 64,
                source_evidence_bytes=10000,
                atomic_obligations_path="prepared/atomic-obligations.json",
                atomic_obligations_sha256="5" * 64,
            )
            payload = json.loads(projection.rendered)
            rendered_by_role[role] = payload["approved_clarifications"]
            clarification = payload["approved_clarifications"][0]
            self.assertEqual("CLR-DEMO-001", clarification["clarification_id"])
            self.assertEqual("user", clarification["authority"])
            self.assertEqual("user-confirmed", clarification["response_type"])
            self.assertEqual(
                "The visible result is confirmed by the user.",
                clarification["exact_answer"],
            )
            self.assertEqual(
                contract.manifest.clarifications[0].exact_answer_sha256,
                clarification["exact_answer_sha256"],
            )
            self.assertEqual(
                ["BSR 1"],
                payload["assertions"][0]["clarification_clause_bindings"][0][
                    "requirement_codes"
                ],
            )
            self.assertEqual(1, projection.report["selected_clarification_count"])
        self.assertEqual(rendered_by_role["writer"], rendered_by_role["reviewer"])

    def test_projection_rejects_omitted_clarification_registry(self) -> None:
        contract, obligations = self.clarification_fixture()
        incomplete_manifest = replace(contract.manifest, clarifications=())
        incomplete_contract = EmbeddedSourceAssertionContract(
            incomplete_manifest,
            replace(
                contract.review_receipt,
                manifest_digest=incomplete_manifest.digest,
            ),
        )

        with self.assertRaisesRegex(
            SourceProjectionError,
            "missing registered approved clarifications: CLR-DEMO-001",
        ):
            build_compact_source_projection(
                role="writer",
                contract=incomplete_contract,
                obligations=obligations,
                selected_obligation_ids=("OBL-002",),
                source_evidence_path="prepared/source-evidence.md",
                source_evidence_sha256="4" * 64,
                source_evidence_bytes=10000,
                atomic_obligations_path="prepared/atomic-obligations.json",
                atomic_obligations_sha256="5" * 64,
            )

    def test_draft_selection_uses_actual_trace_and_rejects_unknown_id(self) -> None:
        contract, obligations = self.fixture()
        selected = select_draft_testable_obligation_ids(
            draft_text=(
                "## TC-DEMO-002\n"
                "**Трассировка:** OBL-002; ATOM-002; SRC-1\n"
            ),
            obligations=obligations,
            manifest=contract.manifest,
        )
        self.assertEqual(("OBL-002",), selected)

        with self.assertRaisesRegex(SourceProjectionError, "unknown draft trace IDs"):
            select_draft_testable_obligation_ids(
                draft_text=(
                    "## TC-DEMO-002\n"
                    "**Трассировка:** OBL-002; ATOM-999; SRC-1\n"
                ),
                obligations=obligations,
                manifest=contract.manifest,
            )

    def test_draft_selection_requires_trace_and_testable_obl_in_every_tc(self) -> None:
        contract, obligations = self.fixture()
        with self.assertRaisesRegex(
            SourceProjectionError,
            "TC TC-DEMO-001 has no traceability field",
        ):
            select_draft_testable_obligation_ids(
                draft_text=(
                    "## TC-DEMO-001\n### Шаги\n1. Action.\n"
                    "## TC-DEMO-002\n"
                    "**Трассировка:** OBL-002; ATOM-002; SRC-1\n"
                ),
                obligations=obligations,
                manifest=contract.manifest,
            )

        with self.assertRaisesRegex(
            SourceProjectionError,
            "TC TC-DEMO-001 has no known testable OBL trace ID",
        ):
            select_draft_testable_obligation_ids(
                draft_text=(
                    "## TC-DEMO-001\n"
                    "**Трассировка:** ATOM-001; SRC-1\n"
                    "## TC-DEMO-002\n"
                    "**Трассировка:** OBL-002; ATOM-002; SRC-1\n"
                ),
                obligations=obligations,
                manifest=contract.manifest,
            )

    def test_draft_selection_rejects_unknown_requirement_code(self) -> None:
        contract, obligations = self.fixture()
        with self.assertRaisesRegex(
            SourceProjectionError,
            "unknown requirement codes: BSR 999",
        ):
            select_draft_testable_obligation_ids(
                draft_text=(
                    "## TC-DEMO-001\n"
                    "**Трассировка:** "
                    "OBL-001; ATOM-001; SRC-1; BSR 999\n"
                ),
                obligations=obligations,
                manifest=contract.manifest,
            )

    def test_projection_rejects_missing_assertion_binding(self) -> None:
        contract, obligations = self.fixture()
        incomplete_manifest = replace(
            contract.manifest,
            assertions=contract.manifest.assertions[:1],
        )
        rebound_contract = EmbeddedSourceAssertionContract(
            incomplete_manifest,
            replace(
                contract.review_receipt,
                manifest_digest=incomplete_manifest.digest,
            ),
        )

        with self.assertRaisesRegex(
            SourceProjectionError,
            "missing accepted source assertions for: OBL-002",
        ):
            build_compact_source_projection(
                role="writer",
                contract=rebound_contract,
                obligations=obligations,
                selected_obligation_ids=("OBL-002",),
                source_evidence_path="prepared/source-evidence.md",
                source_evidence_sha256="4" * 64,
                source_evidence_bytes=10000,
                atomic_obligations_path="prepared/atomic-obligations.json",
                atomic_obligations_sha256="5" * 64,
            )

    def test_reviewer_semantic_projection_preserves_compiled_fields(self) -> None:
        contract, obligations = self.fixture()
        rendered = render_reviewer_obligation_semantic_projection(
            obligations=obligations,
            artifact_path="prepared/atomic-obligations.json",
            artifact_sha256="5" * 64,
            source_contract_summary=source_contract_digest_summary(contract),
            draft_referenced_testable_obligation_ids=("OBL-002",),
            dictionary_evidence=(),
        )
        payload = json.loads(rendered)
        second = payload["obligations"][1]
        immutable = obligations.obligations[1]

        self.assertEqual(["OBL-002"], payload["draft_referenced_testable_obligation_ids"])
        self.assertEqual(immutable.atomic_statement, second["atomic_statement"])
        self.assertEqual(immutable.observable_oracle, second["observable_oracle"])
        self.assertEqual(immutable.test_intent, second["test_intent"])
        self.assertEqual(list(immutable.source_refs), second["source_refs"])


if __name__ == "__main__":
    unittest.main()
