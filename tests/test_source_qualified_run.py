from __future__ import annotations

import hashlib
import io
import inspect
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import test_case_agent.source_qualified_run as source_run_module
from test_case_agent.cli import build_parser, main
from test_case_agent.coverage_graph import PropertyDerivation, build_coverage_graph
from test_case_agent.coverage_io import (
    PropertyDerivationDocument,
    write_property_derivations,
)
from test_case_agent.derivation_compiler import compile_property_derivations
from test_case_agent.iteration_contract import validate_suite
from test_case_agent.immutable_iteration import (
    ImmutableIterationResult,
    run_immutable_iteration as immutable_runner,
)
from test_case_agent.review_cycle.prepared_package import (
    PreparedObligation,
    PreparedObligationSet,
)
from test_case_agent.review_cycle.runtime import write_json_atomic
from test_case_agent.review_cycle.source_assertions import (
    NO_REQUIRED_CHANGE,
    REVIEW_RECEIPT_VERSION,
    SOURCE_REVIEW_DIMENSIONS,
    ClauseEvidenceBinding,
    RequirementCodeBinding,
    ScopeBoundaryExclusion,
    ScopeBoundaryManifestContext,
    ScopeBoundaryReview,
    SourceAssertion,
    SourceAssertionReview,
    SourceAssertionReviewReceipt,
    SourceInventoryReview,
    SourceRow,
    build_source_assertion_manifest,
    render_embedded_source_assertion_contract,
    scope_boundary_source_locator,
)
from test_case_agent.scope_compiler import compile_scope_source
from test_case_agent.scope_registry import (
    load_scope_registry,
    resolve_scope_registry,
)
from test_case_agent.source_qualified_run import (
    SourceQualifiedRunError,
    classify_source_qualified_status,
    load_source_qualified_run_config,
    run_source_qualified_scope,
    run_source_qualified_scope_with_fixture_responses,
)
from test_case_agent.test_design import (
    DesignContext,
    build_test_design_plan,
    render_test_cases,
)
from tests.test_immutable_iteration import FixtureBackend, _accepted_review


class SourceQualifiedRunTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name)
        self.ft = self.repo / "fts" / "sample"
        (self.ft / "source").mkdir(parents=True)
        (self.ft / "support").mkdir()
        (self.ft / "work" / "prepared").mkdir(parents=True)
        self.docx = self.ft / "source" / "requirements.docx"
        self.docx.write_bytes(b"PK\x03\x04source-of-truth")
        self.xhtml = self.ft / "source" / "requirements.xhtml"
        self.xhtml.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><body>
<p>Global constraints reviewed outside the selected rows.</p>
<table>
<tr><td>Client data: open the client card.</td></tr>
<tr><td>BSR 1. Open the client card and verify the client name field is visible.</td></tr>
</table>
<p>Cross-reference context reviewed for this scope.</p>
</body></html>
""",
            encoding="utf-8",
        )
        self.support = self.ft / "support" / "scope-notes.md"
        self.support.write_text("# Approved scope support\n", encoding="utf-8")
        self.registry = self.ft / "scope-registry.json"
        self._write_json(self.registry, self._registry_payload())
        self.canonical = self.ft / "test-cases" / "1-existing.md"
        self.canonical.parent.mkdir()
        self.canonical.write_text("# Existing canonical\n", encoding="utf-8")
        self.coverage_gaps = self.ft / "work" / "prepared" / "coverage-gaps.md"
        self.coverage_gaps.write_text("# Coverage Gaps\n\nNo gaps.\n", encoding="utf-8")

        registry = load_scope_registry(self.registry)
        resolved = resolve_scope_registry(
            registry,
            self.ft,
            scope_id="sample-scope",
        )
        compiled = compile_scope_source(
            resolved,
            scope_id="sample-scope",
            repo_root=self.repo,
        )
        candidates = compiled.baseline.candidates
        self.assertEqual(3, len(candidates))
        xhtml_relative = self._relative(self.xhtml)
        rows = tuple(
            SourceRow(
                source_row_id=f"SRC-{index:03d}",
                source_path=xhtml_relative,
                source_locator=candidate.canonical_xpath,
                bounded_source_text=candidate.bounded_source_text,
                source_context_class=candidate.source_context_class,
                candidate_id=candidate.candidate_id,
                scope_disposition="yes" if index == 2 else "no",
                requirement_codes=("BSR 1",) if index == 2 else (),
            )
            for index, candidate in enumerate(candidates, 1)
        )
        testable = rows[1]
        testable_assertion = SourceAssertion(
            assertion_id="ASSERT-001",
            source_path=testable.source_path,
            source_context_class=testable.source_context_class,
            locator=testable.source_locator,
            exact_source_text=testable.bounded_source_text,
            canonical_statement="Verify that the client name field is visible.",
            polarity="positive",
            semantic_disposition="testable",
            execution_readiness="ready",
            execution_readiness_rationale=NO_REQUIRED_CHANGE,
            risk="high",
            condition_clauses=("Open the client data block.",),
            action_clauses=("Open the client data block.",),
            oracle_clauses=("The client name field is visible.",),
            requirement_codes=("BSR 1",),
            requirement_code_bindings=(
                RequirementCodeBinding(
                    "BSR 1",
                    testable.source_row_id,
                    "xhtml-row",
                    "BSR 1",
                ),
            ),
            clause_evidence_bindings=tuple(
                ClauseEvidenceBinding(
                    clause_kind=kind,
                    clause_index=0,
                    source_row_id=testable.source_row_id,
                    evidence_role=kind,
                    exact_source_fragment=testable.bounded_source_text,
                )
                for kind in ("condition", "action", "oracle")
            ),
            source_row_id=testable.source_row_id,
            atom_id="ATOM-001",
            obligation_ids=("OBL-001",),
            execution_dependency_gap_ids=(),
            primary_gap_id=None,
        )
        context_assertions = tuple(
            SourceAssertion(
                assertion_id=f"ASSERT-CONTEXT-{index:03d}",
                source_path=row.source_path,
                source_context_class=row.source_context_class,
                locator=row.source_locator,
                exact_source_text=row.bounded_source_text,
                canonical_statement=row.bounded_source_text,
                polarity="neutral",
                semantic_disposition="not-applicable",
                execution_readiness="not-applicable",
                execution_readiness_rationale=NO_REQUIRED_CHANGE,
                risk="low",
                condition_clauses=(),
                action_clauses=(),
                oracle_clauses=(),
                requirement_codes=(),
                requirement_code_bindings=(),
                clause_evidence_bindings=(),
                source_row_id=row.source_row_id,
                atom_id=f"ATOM-CONTEXT-{index:03d}",
                obligation_ids=(),
                execution_dependency_gap_ids=(),
                primary_gap_id=None,
                disposition_rationale=(
                    "This row is boundary context and has no independently "
                    "testable product behavior."
                ),
            )
            for index, row in enumerate((rows[0], rows[2]), 1)
        )
        assertions = (context_assertions[0], testable_assertion, context_assertions[1])
        manifest = build_source_assertion_manifest(
            self.repo,
            scope_slug="sample-scope",
            coverage_gaps_path=self._relative(self.coverage_gaps),
            source_paths=(xhtml_relative,),
            assertions=assertions,
            source_row_extraction_spec_digest=compiled.extraction_spec.digest,
            source_row_baseline_digest=compiled.baseline.digest,
            source_row_candidate_count=compiled.baseline.candidate_count,
            source_rows=rows,
            evidence_sources=(
                (self._relative(self.docx), "semantic-source-of-truth"),
                (self._relative(self.support), "supporting-material"),
            ),
            expected_source_rows=rows,
        )
        self.accepted_manifest = manifest
        self.testable_assertion = testable_assertion
        receipt = SourceAssertionReviewReceipt(
            version=REVIEW_RECEIPT_VERSION,
            manifest_digest=manifest.digest,
            decision="accepted",
            source_inventory_review=SourceInventoryReview(
                extraction_spec_digest=manifest.source_row_extraction_spec_digest,
                baseline_digest=manifest.source_row_baseline_digest,
                candidate_count=manifest.source_row_candidate_count,
                mapped_source_row_count=len(rows),
                verdict="verified",
                required_change=NO_REQUIRED_CHANGE,
                note="The complete compiled source inventory was reviewed.",
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
                    note="Verified against the exact compiled source row.",
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
                        context_class=rows[0].source_context_class,
                        source_row_id=rows[0].source_row_id,
                    ),
                    ScopeBoundaryManifestContext(
                        context_class=rows[2].source_context_class,
                        source_row_id=rows[2].source_row_id,
                    ),
                ),
                excluded_contexts=(
                    ScopeBoundaryExclusion(
                        context_class="document-global-constraints",
                        source_path=xhtml_relative,
                        source_sha256=hashlib.sha256(
                            self.xhtml.read_bytes()
                        ).hexdigest(),
                        source_locator=scope_boundary_source_locator(
                            xhtml_relative,
                            "Global constraints reviewed outside the selected rows.",
                        ),
                        exact_source_text=(
                            "Global constraints reviewed outside the selected rows."
                        ),
                        reason="Reviewed global context is outside the selected rows.",
                    ),
                ),
                required_change=NO_REQUIRED_CHANGE,
                note="All mandatory boundary context classes were reviewed.",
            ),
        )
        self.source_evidence = self.ft / "work" / "prepared" / "source-evidence.md"
        self.source_evidence.write_text(
            "# Accepted source evidence\n\n"
            + render_embedded_source_assertion_contract(manifest, receipt)
            + "\n",
            encoding="utf-8",
        )
        obligations = PreparedObligationSet.create(
            package_id="WP-01",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    source_refs=("SRC-002", "BSR 1"),
                    atomic_statement="Verify that the client name field is visible.",
                    observable_oracle="The client name field is visible.",
                    test_intent="Open the client data block.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                ),
            ),
            coverage_gaps=(),
            evidence_text=self.source_evidence.read_text(encoding="utf-8"),
        )
        self.prepared_obligations = obligations
        self.obligations = self.ft / "work" / "prepared" / "obligations.json"
        write_json_atomic(self.obligations, obligations.to_dict())
        derivation = PropertyDerivation(
            source_manifest_digest=manifest.digest,
            obligation_set_digest=obligations.digest,
            assertion_id=testable_assertion.assertion_id,
            source_row_id=testable_assertion.source_row_id,
            atom_id=testable_assertion.atom_id,
            source_text_sha256=hashlib.sha256(
                testable_assertion.exact_source_text.encode("utf-8")
            ).hexdigest(),
            property_key="client.name.visibility",
            subject_key="client.name",
            property_kind="visibility",
            obligation_variants={"OBL-001": "visible"},
            condition_key="always",
            validation_trigger="Open the client data block.",
            cleanup_strategy="",
            source_oracle_ids=None,
            fixture_values={"OBL-001": ("Иван",)},
            calibration_questions=None,
        )
        derivation_document = PropertyDerivationDocument(
            schema_version=1,
            ft_slug="sample",
            scope_slug="sample-scope",
            source_manifest_digest=manifest.digest,
            obligation_set_digest=obligations.digest,
            derivations=(derivation,),
        )
        self.derivations = self.ft / "work" / "prepared" / "derivations.json"
        write_property_derivations(self.derivations, derivation_document)
        self.context = DesignContext(
            package_id="WP-01",
            scope_title="Client data",
            base_preconditions=("Open the client data block.",),
            subject_labels={"client.name": "the client name field"},
            condition_preconditions={},
        )
        self.design_context = self.ft / "work" / "prepared" / "design-context.json"
        self._write_json(
            self.design_context,
            {
                "package_id": self.context.package_id,
                "scope_title": self.context.scope_title,
                "base_preconditions": list(self.context.base_preconditions),
                "subject_labels": dict(self.context.subject_labels),
                "condition_preconditions": {},
                "priorities": {},
            },
        )
        graph = build_coverage_graph(
            ft_slug=derivation_document.ft_slug,
            tc_prefix="SMP",
            source_manifest=manifest,
            obligation_set=obligations,
            derivations=derivation_document.derivations,
        )
        plan = build_test_design_plan(graph, context=self.context)
        draft = render_test_cases(
            plan.deterministic_cases,
            scope_title=self.context.scope_title,
        )
        gate = validate_suite(
            graph=graph,
            cases=plan.deterministic_cases,
            markdown=draft,
            checked_path="shadow-test-cases.md",
        )
        self.assertTrue(gate.passed, gate.production_gate)
        self.reviewer_response = self.ft / "work" / "prepared" / "reviewer.json"
        self._write_json(
            self.reviewer_response,
            _accepted_review(graph, gate.draft_sha256),
        )
        self.config = self.ft / "work" / "run-config.json"
        self._write_json(self.config, self._run_config())

    def _registry_payload(self) -> dict[str, object]:
        selected = {
            "scope_id": "sample-scope",
            "tc_prefix": "SMP",
            "source_set": {
                "docx": "source/requirements.docx",
                "xhtml": "source/requirements.xhtml",
            },
            "boundary": {
                "container_xpath": "/*/*[1]/*[2]",
                "row_ranges": [
                    {"role": "context", "start": 1, "end": 1},
                    {"role": "testable", "start": 2, "end": 2},
                ],
                "cross_references": [
                    {
                        "reference_id": "scope-context",
                        "xpath": "/*/*[1]/*[3]",
                    }
                ],
            },
            "requirement_guard": {
                "allowed_ranges": [{"prefix": "BSR", "start": 1, "end": 1}],
                "excluded_codes": [],
            },
            "reference_paths": ["support/scope-notes.md"],
            "fixture_ids": [],
            "gap_ids": [],
            "execution_profile": "lean-production",
        }
        broken_other_scope = {
            **selected,
            "scope_id": "unrelated-scope",
            "source_set": {
                "docx": "source/missing-other.docx",
                "xhtml": "source/missing-other.xhtml",
            },
            "boundary": {
                "container_xpath": "/*/*[1]/*[1]",
                "row_ranges": [{"role": "testable", "start": 1, "end": 1}],
                "cross_references": [],
            },
            "reference_paths": [],
        }
        return {"version": 1, "scopes": [selected, broken_other_scope]}

    def _run_config(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "registry": self._relative(self.registry),
            "ft_root": self._relative(self.ft),
            "scope": "sample-scope",
            "source_evidence": self._relative(self.source_evidence),
            "obligations": self._relative(self.obligations),
            "derivations": self._relative(self.derivations),
            "design_context": self._relative(self.design_context),
        }

    def _relative(self, path: Path) -> str:
        return path.relative_to(self.repo).as_posix()

    @staticmethod
    def _write_json(path: Path, payload: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _run(self, output: Path) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch(
            "test_case_agent.cli.run_source_qualified_scope",
            side_effect=lambda **kwargs: run_source_qualified_scope_with_fixture_responses(
                **kwargs,
                reviewer_response=self.reviewer_response,
            ),
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(
                [
                    "--repo-root",
                    str(self.repo),
                    "run",
                    "--config",
                    str(self.config),
                    "--output-dir",
                    str(output),
                ]
            )
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def _enable_v2_generated_derivations(self) -> Path:
        assertion = self.testable_assertion
        semantic_obligation = {
            "obligation_id": "OBL-001",
            "package_id": "WP-01",
            "linked_atom_id": "ATOM-001",
            "property_type": "visibility",
            "obligation_class": "visible",
            "coverage_class": "visible",
            "oracle_source": "BSR 1",
            "scope_obligation_ids": [],
            "planned_tc_id": "TC-001",
            "single_expected_behavior": assertion.oracle_clauses[0],
            "test_data": "none_required",
        }
        semantic_assertions = []
        for accepted in self.accepted_manifest.assertions:
            semantic_assertions.append(
                {
                    "assertion_id": accepted.assertion_id,
                    "canonical_statement": accepted.canonical_statement,
                    "polarity": accepted.polarity,
                    "semantic_disposition": accepted.semantic_disposition,
                    "execution_readiness": accepted.execution_readiness,
                    "risk": accepted.risk,
                    "condition_clauses": list(accepted.condition_clauses),
                    "action_clauses": list(accepted.action_clauses),
                    "oracle_clauses": list(accepted.oracle_clauses),
                    "requirement_codes": list(accepted.requirement_codes),
                    "atom_id": accepted.atom_id,
                    "obligation_ids": list(accepted.obligation_ids),
                    "field_or_block": (
                        "the client name field"
                        if accepted.assertion_id == assertion.assertion_id
                        else accepted.canonical_statement
                    ),
                }
            )
        semantic = {
            "version": 4,
            "contract": "semantic-design-bridge-v2",
            "status": "ready",
            "source_designs": [{"assertions": semantic_assertions}],
            "obligations": [semantic_obligation],
        }
        semantic_path = self.ft / "work" / "prepared" / "semantic-design.json"
        self._write_json(semantic_path, semantic)
        boundary_path = self.ft / "work" / "prepared" / "scope-boundary.json"
        self._write_json(boundary_path, {})
        semantic_sha = hashlib.sha256(semantic_path.read_bytes()).hexdigest()
        decision_sha = "a" * 64
        receipt = {
            "status": "verified",
            "source_assertion_manifest_digest": self.accepted_manifest.digest,
            "semantic_design_artifact_sha256": semantic_sha,
            "semantic_design_decision_sha256": decision_sha,
        }
        receipt_path = self.ft / "work" / "prepared" / "semantic-receipt.json"
        self._write_json(receipt_path, receipt)

        def artifact(path: Path, **extra: str) -> dict[str, str]:
            return {
                "path": self._relative(path),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                **extra,
            }

        projection = {
            "contract": "semantic-design-compiler-projection-v1",
            "semantic_design_artifact": artifact(
                semantic_path, decision_sha256=decision_sha
            ),
            "scope_boundary_artifact": artifact(
                boundary_path, decision_sha256="b" * 64
            ),
            "bridge_receipt_artifact": artifact(receipt_path),
            "bridge_receipt": receipt,
            "boundary_gaps": [],
            "obligations": [semantic_obligation],
            "dependency_bindings": [],
            "negative_oracles": [],
            "requiredness_oracles": [],
            "oracle_inventories": [],
        }
        self.source_evidence.write_text(
            self.source_evidence.read_text(encoding="utf-8")
            + "\n## Immutable semantic-design bridge projection\n\n```json\n"
            + json.dumps(projection, ensure_ascii=False, separators=(",", ":"))
            + "\n```\n",
            encoding="utf-8",
        )
        compiled = compile_property_derivations(
            repo_root=self.repo,
            ft_slug="sample",
            source_manifest=self.accepted_manifest,
            obligation_set=self.prepared_obligations,
            semantic_projection=projection,
        )
        context = DesignContext(
            package_id="WP-01",
            scope_title=compiled.scope_title,
            base_preconditions=compiled.base_preconditions,
            subject_labels=compiled.subject_labels,
            condition_preconditions=compiled.condition_preconditions,
        )
        graph = build_coverage_graph(
            ft_slug="sample",
            tc_prefix="SMP",
            source_manifest=self.accepted_manifest,
            obligation_set=self.prepared_obligations,
            derivations=compiled.document.derivations,
        )
        plan = build_test_design_plan(graph, context=context)
        draft = render_test_cases(
            plan.deterministic_cases, scope_title=compiled.scope_title
        )
        gate = validate_suite(
            graph=graph,
            cases=plan.deterministic_cases,
            markdown=draft,
            checked_path="shadow-test-cases.md",
        )
        self._write_json(
            self.reviewer_response,
            _accepted_review(graph, gate.draft_sha256),
        )
        self._write_json(
            self.design_context,
            {
                "scope_title": context.scope_title,
                "base_preconditions": list(context.base_preconditions),
            },
        )
        self._write_json(
            self.config,
            {
                "schema_version": 2,
                "registry": self._relative(self.registry),
                "ft_root": self._relative(self.ft),
                "scope": "sample-scope",
                "source_evidence": self._relative(self.source_evidence),
                "obligations": self._relative(self.obligations),
            },
        )
        return semantic_path

    def test_offline_run_is_source_qualified_and_preserves_canonical(self) -> None:
        output = self.ft / "work" / "source-qualified-runs" / "run-001"
        canonical_before = self.canonical.read_bytes()

        exit_code, stdout, stderr = self._run(output)

        terminal = json.loads(
            (output / "terminal-summary.json").read_text(encoding="utf-8")
        )
        self.assertEqual(0, exit_code, f"{stderr}\n{terminal}")
        self.assertEqual("", stderr)
        self.assertEqual("accepted-shadow", terminal["status"])
        self.assertEqual("source-qualified-immutable", terminal["mode"])
        self.assertEqual(0, terminal["writer_model_calls"])
        self.assertEqual(0, terminal["reviewer_model_calls"])
        self.assertEqual("not-performed", terminal["canonical_publication"])
        self.assertTrue(terminal["qualification_only"])
        self.assertFalse(terminal["promotion_eligible"])
        iteration_summary = json.loads(
            (output / "iteration" / "iteration-summary.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(iteration_summary["qualification_only"])
        self.assertFalse(iteration_summary["promotion_eligible"])
        self.assertIsNone(terminal["diagnostic"])
        self.assertEqual(terminal, json.loads(stdout))
        self.assertEqual(canonical_before, self.canonical.read_bytes())
        self.assertFalse((output / "diagnostic.json").exists())
        for relative in (
            "scope-compilation/compiled-scope.json",
            "bindings/accepted-coverage-contract.json",
            "graph/coverage-graph.json",
            "context/design-context.json",
            "iteration/iteration-summary.json",
            "run-input-receipt.json",
        ):
            self.assertTrue((output / relative).is_file(), relative)
        protected = json.loads(
            (output / "iteration" / "protected-inputs.receipt.json").read_text(
                encoding="utf-8"
            )
        )
        protected_paths = {item["path"] for item in protected["files"]}
        self.assertIn(self._relative(self.docx), protected_paths)
        self.assertIn(self._relative(self.xhtml), protected_paths)
        self.assertIn(self._relative(self.support), protected_paths)
        self.assertIn(self._relative(self.coverage_gaps), protected_paths)
        self.assertIn(self._relative(self.canonical), protected_paths)

    def test_v2_generates_derivations_from_authenticated_semantic_projection(self) -> None:
        semantic_path = self._enable_v2_generated_derivations()
        output = self.ft / "work" / "source-qualified-runs" / "run-v2"

        exit_code, _, stderr = self._run(output)

        terminal = json.loads(
            (output / "terminal-summary.json").read_text(encoding="utf-8")
        )
        receipt = json.loads(
            (output / "run-input-receipt.json").read_text(encoding="utf-8")
        )
        gate_path = output / "iteration" / "suite-gate.json"
        gate = (
            json.loads(gate_path.read_text(encoding="utf-8"))
            if gate_path.is_file()
            else {}
        )
        self.assertEqual(0, exit_code, f"{stderr}\n{terminal}\n{gate}")
        self.assertEqual("accepted-shadow", terminal["status"])
        self.assertEqual(
            "generated-from-semantic-projection", terminal["derivation_mode"]
        )
        self.assertTrue(
            (output / "bindings" / "generated-property-derivations.json").is_file()
        )
        self.assertNotIn("derivations", {item["role"] for item in receipt["inputs"]})
        self.assertIn(
            self._relative(semantic_path),
            terminal["protected_semantic_artifact_paths"],
        )

    def test_calibration_pending_terminal_is_success_and_remains_non_promotable(
        self,
    ) -> None:
        self._enable_v2_generated_derivations()
        output = self.ft / "work" / "source-qualified-runs" / "run-pending"

        def pending_iteration(**kwargs):  # type: ignore[no-untyped-def]
            iteration_dir = kwargs["output_dir"]
            iteration_dir.mkdir(parents=True)
            draft = iteration_dir / "shadow-test-cases.md"
            draft.write_text("# Pending calibration suite\n", encoding="utf-8")
            summary_path = iteration_dir / "iteration-summary.json"
            self._write_json(
                summary_path,
                {
                    "schema_version": 1,
                    "mode": "immutable-deterministic-first",
                    "status": "accepted-with-calibration-pending",
                    "error": "",
                    "draft": draft.resolve().relative_to(
                        self.repo.resolve()
                    ).as_posix(),
                    "calibration_pending_count": 1,
                    "promotion_eligible": False,
                    "non_promotable_reason": "calibration-pending",
                },
            )
            return ImmutableIterationResult(
                status="accepted-with-calibration-pending",
                output_dir=iteration_dir,
                draft_path=draft,
                summary_path=summary_path,
                test_case_count=2,
                writer_model_calls=0,
                reviewer_model_calls=1,
            )

        with patch(
            "test_case_agent.source_qualified_run.run_immutable_iteration",
            side_effect=pending_iteration,
        ):
            result = run_source_qualified_scope(
                repo_root=self.repo,
                config_path=self.config,
                output_dir=output,
            )

        terminal = json.loads(result.summary_path.read_text(encoding="utf-8"))
        self.assertEqual("success", classify_source_qualified_status(result.status))
        self.assertEqual("accepted-with-calibration-pending", terminal["status"])
        self.assertEqual(1, terminal["calibration_pending_count"])
        self.assertFalse(terminal["promotion_eligible"])
        self.assertEqual(
            "calibration-pending", terminal["non_promotable_reason"]
        )
        self.assertIsNone(terminal["diagnostic"])
        self.assertFalse((output / "diagnostic.json").exists())

    def test_registry_source_absent_from_manifest_is_rejected_with_diagnostic(self) -> None:
        unrelated = self.ft / "source" / "unrelated.xhtml"
        unrelated.write_text("unrelated", encoding="utf-8")
        registry = json.loads(self.registry.read_text(encoding="utf-8"))
        selected = next(
            item for item in registry["scopes"] if item["scope_id"] == "sample-scope"
        )
        selected["reference_paths"].append("source/unrelated.xhtml")
        self._write_json(self.registry, registry)
        output = self.ft / "work" / "source-qualified-runs" / "run-002"
        canonical_before = self.canonical.read_bytes()

        exit_code, _, stderr = self._run(output)

        self.assertEqual(2, exit_code)
        self.assertIn("contract-error", stderr)
        terminal = json.loads(
            (output / "terminal-summary.json").read_text(encoding="utf-8")
        )
        diagnostic = json.loads(
            (output / "diagnostic.json").read_text(encoding="utf-8")
        )
        self.assertEqual("blocked-contract", terminal["status"])
        self.assertEqual("source-contract-binding", terminal["failed_stage"])
        self.assertIn("source set", diagnostic["message"])
        self.assertFalse((output / "iteration").exists())
        self.assertEqual(canonical_before, self.canonical.read_bytes())

    def test_full_canonical_baseline_is_derived_without_config_surface(self) -> None:
        second = self.ft / "test-cases" / "2-new.md"
        second.write_text("# New canonical\n", encoding="utf-8")
        output = self.ft / "work" / "source-qualified-runs" / "run-003"

        exit_code, _, stderr = self._run(output)

        terminal = json.loads(
            (output / "terminal-summary.json").read_text(encoding="utf-8")
        )
        self.assertEqual(0, exit_code, f"{stderr}\n{terminal}")
        protected = json.loads(
            (output / "iteration" / "protected-inputs.receipt.json").read_text(
                encoding="utf-8"
            )
        )
        canonical_paths = {
            item["path"] for item in protected["files"] if item["role"] == "canonical"
        }
        self.assertEqual(
            {self._relative(self.canonical), self._relative(second)},
            canonical_paths,
        )

    def test_run_config_rejects_unknown_fields_without_creating_output(self) -> None:
        config = self._run_config()
        config["protected_source_paths"] = [self._relative(self.xhtml)]
        self._write_json(self.config, config)
        output = self.ft / "work" / "source-qualified-runs" / "run-004"

        exit_code, _, stderr = self._run(output)

        self.assertEqual(2, exit_code)
        self.assertIn("run-config-fields", stderr)
        self.assertFalse(output.exists())

    def test_public_config_rejects_legacy_v1_and_behavioral_context_knobs(self) -> None:
        with self.assertRaisesRegex(SourceQualifiedRunError, "run-config-version"):
            load_source_qualified_run_config(self.config)

        self._enable_v2_generated_derivations()
        payload = json.loads(self.config.read_text(encoding="utf-8"))
        payload["design_context"] = self._relative(self.design_context)
        payload["ft_slug"] = "forged-ft"
        self._write_json(self.config, payload)
        with self.assertRaisesRegex(SourceQualifiedRunError, "run-config-fields"):
            load_source_qualified_run_config(self.config)

    def test_wrong_design_context_package_is_rejected_before_iteration(self) -> None:
        payload = json.loads(self.design_context.read_text(encoding="utf-8"))
        payload["package_id"] = "WP-FORGED"
        self._write_json(self.design_context, payload)
        output = self.ft / "work" / "source-qualified-runs" / "run-wrong-package"

        exit_code, _, stderr = self._run(output)

        terminal = json.loads(
            (output / "terminal-summary.json").read_text(encoding="utf-8")
        )
        diagnostic = json.loads(
            (output / "diagnostic.json").read_text(encoding="utf-8")
        )
        self.assertEqual(2, exit_code, stderr)
        self.assertEqual("blocked-contract", terminal["status"])
        self.assertEqual("design-context", terminal["failed_stage"])
        self.assertIn("package_id", diagnostic["message"])
        self.assertFalse((output / "iteration").exists())

    def test_nonaccepted_iteration_has_separate_terminal_diagnostic(self) -> None:
        review = json.loads(self.reviewer_response.read_text(encoding="utf-8"))
        review["decision"] = "changes-required"
        for item in review["case_results"]:
            item["status"] = "incorrect"
            item["comment"] = "The case requires a correction."
        review["findings"] = [
            {
                "severity": "error",
                "case_key": review["case_results"][0]["case_key"],
                "tc_id": review["case_results"][0]["tc_id"],
                "obligation_id": review["case_results"][0]["obligation_id"],
                "message": "The case requires a correction.",
            }
        ]
        review["summary"] = "Changes are required."
        self._write_json(self.reviewer_response, review)
        output = self.ft / "work" / "source-qualified-runs" / "run-005"
        canonical_before = self.canonical.read_bytes()

        exit_code, _, stderr = self._run(output)

        self.assertEqual(1, exit_code, stderr)
        terminal = json.loads(
            (output / "terminal-summary.json").read_text(encoding="utf-8")
        )
        diagnostic = json.loads(
            (output / "diagnostic.json").read_text(encoding="utf-8")
        )
        self.assertEqual("review-changes-required", terminal["status"])
        self.assertEqual("workflow", diagnostic["category"])
        self.assertEqual("immutable-iteration", diagnostic["failed_stage"])
        self.assertEqual(canonical_before, self.canonical.read_bytes())

    def test_contract_terminal_status_uses_contract_exit_code(self) -> None:
        review = json.loads(self.reviewer_response.read_text(encoding="utf-8"))
        del review["summary"]
        self._write_json(self.reviewer_response, review)
        output = self.ft / "work" / "source-qualified-runs" / "run-006"

        exit_code, _, stderr = self._run(output)

        terminal = json.loads(
            (output / "terminal-summary.json").read_text(encoding="utf-8")
        )
        diagnostic = json.loads(
            (output / "diagnostic.json").read_text(encoding="utf-8")
        )
        self.assertEqual(2, exit_code, stderr)
        self.assertEqual("blocked-contract", terminal["status"])
        self.assertEqual("contract", diagnostic["category"])

    def test_coverage_gaps_mutation_is_blocked_as_input_drift(self) -> None:
        output = self.ft / "work" / "source-qualified-runs" / "run-007"
        backend = FixtureBackend(
            mutate_on_stage=("reviewer", self.coverage_gaps),
        )

        result = run_source_qualified_scope_with_fixture_responses(
            repo_root=self.repo,
            config_path=self.config,
            output_dir=output,
            backend=backend,
        )

        terminal = json.loads(result.summary_path.read_text(encoding="utf-8"))
        diagnostic = json.loads(
            (output / "diagnostic.json").read_text(encoding="utf-8")
        )
        self.assertEqual("blocked-input-drift", result.status)
        self.assertEqual("contract", diagnostic["category"])
        self.assertEqual("blocked-input-drift", terminal["status"])
        self.assertEqual(["reviewer"], backend.calls)

    def test_presnapshot_canonical_mutation_cannot_rebase_protection(self) -> None:
        output = self.ft / "work" / "source-qualified-runs" / "run-008"
        canonical_before = self.canonical.read_bytes()

        def mutate_then_run(**kwargs):
            self.canonical.write_text("# Mutated canonical\n", encoding="utf-8")
            return immutable_runner(**kwargs)

        with patch(
            "test_case_agent.source_qualified_run.run_immutable_iteration",
            side_effect=mutate_then_run,
        ):
            exit_code, _, stderr = self._run(output)

        terminal = json.loads(
            (output / "terminal-summary.json").read_text(encoding="utf-8")
        )
        diagnostic = json.loads(
            (output / "diagnostic.json").read_text(encoding="utf-8")
        )
        self.assertEqual(2, exit_code, stderr)
        self.assertEqual("blocked-contract", terminal["status"])
        self.assertEqual("final-reconciliation", terminal["failed_stage"])
        self.assertIn("run-input-drift", diagnostic["message"])
        self.assertNotEqual(canonical_before, self.canonical.read_bytes())

    def test_canonical_mutation_during_scope_compile_cannot_rebase_snapshot(self) -> None:
        output = self.ft / "work" / "source-qualified-runs" / "run-compile-drift"
        original = source_run_module.compile_scope_source

        def mutate_then_compile(*args, **kwargs):
            self.canonical.write_text("# Mutated during compile\n", encoding="utf-8")
            return original(*args, **kwargs)

        with patch(
            "test_case_agent.source_qualified_run.compile_scope_source",
            side_effect=mutate_then_compile,
        ):
            exit_code, _, stderr = self._run(output)

        terminal = json.loads(
            (output / "terminal-summary.json").read_text(encoding="utf-8")
        )
        diagnostic = json.loads(
            (output / "diagnostic.json").read_text(encoding="utf-8")
        )
        self.assertEqual(2, exit_code, stderr)
        self.assertEqual("pre-dispatch-verification", terminal["failed_stage"])
        self.assertIn("run-input-drift", diagnostic["message"])
        self.assertFalse((output / "iteration").exists())

    def test_config_mutation_after_parse_cannot_become_trusted_binding(self) -> None:
        output = self.ft / "work" / "source-qualified-runs" / "run-config-drift"
        original = source_run_module._source_qualified_run_config_from_bytes

        def parse_then_mutate(raw, **kwargs):
            parsed = original(raw, **kwargs)
            self.config.write_bytes(self.config.read_bytes() + b" ")
            return parsed

        with patch(
            "test_case_agent.source_qualified_run._source_qualified_run_config_from_bytes",
            side_effect=parse_then_mutate,
        ):
            exit_code, _, stderr = self._run(output)

        terminal = json.loads(
            (output / "terminal-summary.json").read_text(encoding="utf-8")
        )
        diagnostic = json.loads(
            (output / "diagnostic.json").read_text(encoding="utf-8")
        )
        self.assertEqual(2, exit_code, stderr)
        self.assertEqual("pre-dispatch-verification", terminal["failed_stage"])
        self.assertIn("run-input-drift", diagnostic["message"])
        receipt = json.loads(
            (output / "run-input-receipt.json").read_text(encoding="utf-8")
        )
        bound = next(item for item in receipt["inputs"] if item["role"] == "run-config")
        self.assertNotEqual(
            bound["sha256"], hashlib.sha256(self.config.read_bytes()).hexdigest()
        )

    def test_invalid_utf8_source_evidence_is_a_contract_failure(self) -> None:
        self.source_evidence.write_bytes(b"\xff\xfe")
        output = self.ft / "work" / "source-qualified-runs" / "run-009"

        exit_code, _, stderr = self._run(output)

        terminal = json.loads(
            (output / "terminal-summary.json").read_text(encoding="utf-8")
        )
        diagnostic = json.loads(
            (output / "diagnostic.json").read_text(encoding="utf-8")
        )
        self.assertEqual(2, exit_code, stderr)
        self.assertEqual("blocked-contract", terminal["status"])
        self.assertEqual("source-contract-binding", terminal["failed_stage"])
        self.assertIn("invalid-utf8", diagnostic["message"])

    def test_public_production_parser_exposes_only_run(self) -> None:
        self.assertNotIn(
            "backend",
            inspect.signature(source_run_module.run_source_qualified_scope).parameters,
        )
        help_text = build_parser().format_help()

        self.assertIn("{run}", help_text)
        for legacy in (
            "scope-compile",
            "graph-build",
            "context-build",
            "iterate",
            "quality-proof",
        ):
            self.assertNotIn(legacy, help_text)
        run_parser = build_parser()
        with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()):
            run_parser.parse_args(
                [
                    "run",
                    "--config",
                    "config.json",
                    "--output-dir",
                    "run-001",
                    "--reviewer-response",
                    "offline.json",
                ]
            )


if __name__ == "__main__":
    unittest.main()
