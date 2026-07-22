from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from test_case_agent.coverage_contract import (
    CoverageContractError,
    bind_accepted_source_contract,
)
from test_case_agent.review_cycle.prepared_package import (
    PreparedObligation,
    PreparedObligationSet,
)
from test_case_agent.review_cycle.source_assertions import (
    MANIFEST_VERSION,
    NO_REQUIRED_CHANGE,
    REVIEW_RECEIPT_VERSION,
    SOURCE_REVIEW_DIMENSIONS,
    ClauseEvidenceBinding,
    EmbeddedSourceAssertionContract,
    RegisteredArtifact,
    RegisteredSource,
    RequirementCodeBinding,
    ScopeBoundaryExclusion,
    ScopeBoundaryManifestContext,
    ScopeBoundaryReview,
    SourceAssertion,
    SourceAssertionManifest,
    SourceAssertionReview,
    SourceAssertionReviewReceipt,
    SourceInventoryReview,
    SourceRow,
    scope_boundary_source_locator,
)


def _fixture() -> tuple[EmbeddedSourceAssertionContract, PreparedObligationSet]:
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
    ancestor_text = "Ancestor preamble was reviewed outside the selected rows."
    cross_reference_text = "Cross references were reviewed outside the selected rows."
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
        _validated_source_texts={
            source_row.source_path: " ".join(
                (
                    source_row.bounded_source_text,
                    ancestor_text,
                    cross_reference_text,
                )
            )
        },
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
                    dimension: "verified" for dimension in SOURCE_REVIEW_DIMENSIONS
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
            checked_context_classes=(
                "document-global-constraints",
                "ancestor-and-section-preamble",
                "cross-referenced-constraints",
            ),
            reviewed_manifest_contexts=(
                ScopeBoundaryManifestContext(
                    context_class="document-global-constraints",
                    source_row_id=source_row.source_row_id,
                ),
            ),
            excluded_contexts=tuple(
                ScopeBoundaryExclusion(
                    context_class=context_class,
                    source_path=source_row.source_path,
                    source_sha256="3" * 64,
                    source_locator=scope_boundary_source_locator(
                        source_row.source_path, exact_text
                    ),
                    exact_source_text=exact_text,
                    reason="This reviewed boundary evidence is outside manifest rows.",
                )
                for context_class, exact_text in (
                    ("ancestor-and-section-preamble", ancestor_text),
                    ("cross-referenced-constraints", cross_reference_text),
                )
            ),
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
                source_refs=("SRC-1", "BSR 1"),
                atomic_statement=f"Observable property {index} is required.",
                observable_oracle=f"Visible result {index} is present.",
                test_intent=f"Perform action {index}.",
                coverage_status="testable",
                gap_id="",
                dictionary_refs=(),
                notes="",
            )
            for index in (1, 2)
        ),
        coverage_gaps=(),
    )
    return EmbeddedSourceAssertionContract(manifest, receipt), obligations


class CoverageContractTests(unittest.TestCase):
    def _with_closed_context(
        self,
        contract: EmbeddedSourceAssertionContract,
        obligations: PreparedObligationSet,
    ) -> tuple[
        EmbeddedSourceAssertionContract,
        PreparedObligationSet,
        PreparedObligation,
    ]:
        source = contract.manifest.assertions[0]
        context_assertion = replace(
            source,
            assertion_id="ASSERT-CONTEXT-001",
            canonical_statement="The table header supplies column context only.",
            polarity="neutral",
            semantic_disposition="not-applicable",
            execution_readiness="not-applicable",
            risk="low",
            condition_clauses=(),
            action_clauses=(),
            oracle_clauses=(),
            requirement_codes=(),
            requirement_code_bindings=(),
            clause_evidence_bindings=(),
            atom_id="ATOM-CONTEXT-001",
            obligation_ids=(),
            disposition_rationale="Context row has no independent product behavior.",
        )
        manifest = replace(
            contract.manifest,
            assertions=(context_assertion, *contract.manifest.assertions),
        )
        context_review = SourceAssertionReview(
            assertion_id=context_assertion.assertion_id,
            approved_polarity=context_assertion.polarity,
            approved_semantic_disposition=context_assertion.semantic_disposition,
            approved_execution_readiness=context_assertion.execution_readiness,
            approved_risk=context_assertion.risk,
            dimension_verdicts={
                dimension: "verified" for dimension in SOURCE_REVIEW_DIMENSIONS
            },
            verdict="verified",
            required_change=NO_REQUIRED_CHANGE,
            note="Reviewed as closed structural context.",
        )
        receipt = replace(
            contract.review_receipt,
            manifest_digest=manifest.digest,
            assertion_reviews=(
                context_review,
                *contract.review_receipt.assertion_reviews,
            ),
        )
        context_obligation = PreparedObligation(
            obligation_id="OBL-CONTEXT-001",
            atom_id=context_assertion.atom_id,
            source_refs=(context_assertion.source_row_id,),
            atomic_statement=context_assertion.canonical_statement,
            observable_oracle="",
            test_intent="Use the row only to interpret the table columns.",
            coverage_status="not-applicable",
            gap_id="",
            dictionary_refs=(),
            notes="Closed context projection.",
        )
        obligation_set = PreparedObligationSet.create(
            package_id=obligations.package_id,
            obligations=(context_obligation, *obligations.obligations),
            coverage_gaps=(),
        )
        return (
            EmbeddedSourceAssertionContract(manifest, receipt),
            obligation_set,
            context_obligation,
        )

    def test_accepted_contract_produces_deterministic_binding(self) -> None:
        contract, obligations = _fixture()

        first = bind_accepted_source_contract(
            contract=contract,
            obligation_set=obligations,
            expected_scope_slug="demo-scope",
        )
        second = bind_accepted_source_contract(
            contract=contract,
            obligation_set=obligations,
            expected_scope_slug="demo-scope",
        )

        self.assertEqual(first, second)
        self.assertEqual(first.digest, second.digest)
        self.assertEqual(contract.manifest.digest, first.source_manifest_digest)
        self.assertEqual(obligations.digest, first.obligation_set_digest)
        self.assertEqual(("OBL-001", "OBL-002"), first.obligation_ids)
        self.assertEqual(
            (("fts/demo/source/main.xhtml", "3" * 64),), first.source_hashes
        )

    def test_allows_only_closed_not_applicable_context_obligations(self) -> None:
        contract, obligations = _fixture()
        contract, obligations, context_obligation = self._with_closed_context(
            contract, obligations
        )

        binding = bind_accepted_source_contract(
            contract=contract,
            obligation_set=obligations,
            expected_scope_slug="demo-scope",
        )

        self.assertEqual(("OBL-001", "OBL-002"), binding.obligation_ids)

        unsafe = PreparedObligationSet.create(
            package_id=obligations.package_id,
            obligations=(
                replace(context_obligation, source_refs=("SRC-OTHER",)),
                *obligations.obligations[1:],
            ),
            coverage_gaps=(),
        )
        with self.assertRaisesRegex(
            CoverageContractError, "unexpected=\\['OBL-CONTEXT-001'\\]"
        ):
            bind_accepted_source_contract(
                contract=contract,
                obligation_set=unsafe,
                expected_scope_slug="demo-scope",
            )

    def test_rejects_nonaccepted_and_stale_review_receipts(self) -> None:
        contract, obligations = _fixture()
        candidates = (
            (
                replace(
                    contract,
                    review_receipt=replace(
                        contract.review_receipt, decision="changes-required"
                    ),
                ),
                "decision=accepted",
            ),
            (
                replace(
                    contract,
                    review_receipt=replace(
                        contract.review_receipt, manifest_digest="0" * 64
                    ),
                ),
                "not valid for the manifest",
            ),
        )
        for candidate, message in candidates:
            with self.subTest(message=message):
                with self.assertRaisesRegex(CoverageContractError, message):
                    bind_accepted_source_contract(
                        contract=candidate,
                        obligation_set=obligations,
                        expected_scope_slug="demo-scope",
                    )

    def test_rejects_scope_and_explicit_digest_mismatches(self) -> None:
        contract, obligations = _fixture()
        calls = (
            ({"expected_scope_slug": "other-scope"}, "requested scope"),
            (
                {
                    "expected_scope_slug": "demo-scope",
                    "expected_manifest_digest": "0" * 64,
                },
                "expected manifest digest",
            ),
            (
                {
                    "expected_scope_slug": "demo-scope",
                    "expected_review_receipt_digest": "0" * 64,
                },
                "receipt digest",
            ),
            (
                {
                    "expected_scope_slug": "demo-scope",
                    "expected_package_id": "other-package",
                },
                "package_id",
            ),
            (
                {
                    "expected_scope_slug": "demo-scope",
                    "expected_obligation_set_digest": "0" * 64,
                },
                "expected digest",
            ),
        )
        for kwargs, message in calls:
            with self.subTest(message=message):
                with self.assertRaisesRegex(CoverageContractError, message):
                    bind_accepted_source_contract(
                        contract=contract,
                        obligation_set=obligations,
                        **kwargs,
                    )

    def test_rejects_missing_extra_and_wrong_atom_obligations(self) -> None:
        contract, obligations = _fixture()
        missing = PreparedObligationSet.create(
            package_id=obligations.package_id,
            obligations=(obligations.obligations[0],),
            coverage_gaps=(),
        )
        extra = PreparedObligationSet.create(
            package_id=obligations.package_id,
            obligations=(
                *obligations.obligations,
                replace(
                    obligations.obligations[0],
                    obligation_id="OBL-999",
                    atom_id="ATOM-999",
                ),
            ),
            coverage_gaps=(),
        )
        wrong_atom = PreparedObligationSet.create(
            package_id=obligations.package_id,
            obligations=(
                replace(obligations.obligations[0], atom_id="ATOM-999"),
                obligations.obligations[1],
            ),
            coverage_gaps=(),
        )
        for candidate, message in (
            (missing, "missing=\\['OBL-002'\\]"),
            (extra, "unexpected=\\['OBL-999'\\]"),
            (wrong_atom, "source ATOM owners"),
        ):
            with self.subTest(message=message):
                with self.assertRaisesRegex(CoverageContractError, message):
                    bind_accepted_source_contract(
                        contract=contract,
                        obligation_set=candidate,
                        expected_scope_slug="demo-scope",
                    )

    def test_rejects_forged_obligation_semantic_fields(self) -> None:
        contract, obligations = _fixture()
        first = obligations.obligations[0]
        mutations = (
            (
                replace(first, atomic_statement="Forged atomic behavior."),
                "atomic_statement",
            ),
            (
                replace(first, observable_oracle="Forged visible result."),
                "observable_oracle",
            ),
            (
                replace(first, test_intent="Perform a forged administrator action."),
                "test_intent",
            ),
        )

        for forged, message in mutations:
            with self.subTest(field=message):
                candidate = PreparedObligationSet.create(
                    package_id=obligations.package_id,
                    obligations=(forged, obligations.obligations[1]),
                    coverage_gaps=(),
                )
                with self.assertRaisesRegex(CoverageContractError, message):
                    bind_accepted_source_contract(
                        contract=contract,
                        obligation_set=candidate,
                        expected_scope_slug="demo-scope",
                    )

    def test_rejects_invalid_package_digest_before_binding(self) -> None:
        contract, obligations = _fixture()
        corrupted = replace(obligations, digest="0" * 64)

        with self.assertRaisesRegex(CoverageContractError, "package is invalid"):
            bind_accepted_source_contract(
                contract=contract,
                obligation_set=corrupted,
                expected_scope_slug="demo-scope",
            )

    def test_expected_source_hash_registry_must_match_exactly(self) -> None:
        contract, obligations = _fixture()
        valid = {"fts/demo/source/main.xhtml": "3" * 64}
        binding = bind_accepted_source_contract(
            contract=contract,
            obligation_set=obligations,
            expected_scope_slug="demo-scope",
            expected_source_hashes=valid,
        )
        self.assertEqual(tuple(valid.items()), binding.source_hashes)

        candidates = (
            ({}, "missing"),
            ({"fts/demo/source/main.xhtml": "5" * 64}, "changed"),
            (
                {
                    **valid,
                    "fts/demo/source/foreign.xhtml": "6" * 64,
                },
                "unexpected",
            ),
        )
        for expected, message in candidates:
            with self.subTest(message=message):
                with self.assertRaisesRegex(CoverageContractError, message):
                    bind_accepted_source_contract(
                        contract=contract,
                        obligation_set=obligations,
                        expected_scope_slug="demo-scope",
                        expected_source_hashes=expected,
                    )

    def test_repo_root_uses_existing_manifest_file_validator(self) -> None:
        contract, obligations = _fixture()
        repo_root = Path("C:/verified-repository")

        with patch.object(
            SourceAssertionManifest, "validate", autospec=True
        ) as validate:
            bind_accepted_source_contract(
                contract=contract,
                obligation_set=obligations,
                expected_scope_slug="demo-scope",
                repo_root=repo_root,
            )

        validate.assert_called_once()
        validated_manifest, validated_root = validate.call_args.args
        self.assertEqual(contract.manifest.digest, validated_manifest.digest)
        self.assertEqual(repo_root, validated_root)


if __name__ == "__main__":
    unittest.main()
