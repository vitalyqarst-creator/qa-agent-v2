from __future__ import annotations

import hashlib
import json
import unittest
import copy
from dataclasses import replace
from pathlib import Path
from typing import Any

from PIL import Image

from test_case_agent.coverage_graph import build_coverage_graph
from test_case_agent.coverage_io import load_property_derivations
from test_case_agent.immutable_iteration import run_immutable_iteration
from test_case_agent.iteration_contract import (
    REVIEWER_PROMPT_INSTRUCTION,
    reviewer_acceptance_contract,
    reviewer_prompt_instruction,
    reviewer_response_schema,
)
from test_case_agent.promotion_adapter import (
    PromotionAdapterBlocked,
    _validate_reviewer_request,
    _validate_reviewer_response as _validate_promotion_reviewer_response,
    prepare_immutable_iteration_promotion,
)
from test_case_agent.review_cycle.runtime import sha256_path
from test_case_agent.review_cycle.source_assertions import (
    RegisteredMockup,
    parse_embedded_source_assertion_contract,
)
from test_case_agent.reviewer_evidence import prepare_reviewer_evidence_basis
from test_case_agent.scope_compiler import compile_scope_source
from test_case_agent.scope_registry import load_and_resolve_scope_registry
from tests.test_immutable_iteration import FixtureBackend
from tests import test_source_qualified_run as source_qualified_fixture


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _canonical_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _canonical_digest(payload: Any) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


class PromotionAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        fixture = source_qualified_fixture.SourceQualifiedRunTests(
            methodName="test_offline_run_is_source_qualified_and_preserves_canonical"
        )
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        self.repo = fixture.repo.resolve()
        self.ft = fixture.ft.resolve()
        self.source = fixture.xhtml
        self.canonical = fixture.canonical
        self.canonical_before = self.canonical.read_bytes()

        registry = load_and_resolve_scope_registry(
            fixture.registry,
            fixture.ft,
            scope_id="sample-scope",
        )
        compiled = compile_scope_source(
            registry,
            scope_id="sample-scope",
            repo_root=self.repo,
        )
        contract = parse_embedded_source_assertion_contract(
            fixture.source_evidence.read_text(encoding="utf-8"),
            self.repo,
            expected_scope_slug="sample-scope",
            expected_obligation_ids=("OBL-001",),
        )
        self.mockup = self.ft / "source" / "mockups" / "contact-form.png"
        self.mockup.parent.mkdir(parents=True)
        Image.new("RGB", (3, 2), color=(31, 97, 173)).save(self.mockup)
        compiled = replace(
            compiled,
            definition=replace(
                compiled.definition,
                reference_paths=tuple(
                    sorted(
                        (
                            *compiled.definition.reference_paths,
                            "source/mockups/contact-form.png",
                        )
                    )
                ),
            ),
        )
        manifest = replace(
            contract.manifest,
            mockups=(
                RegisteredMockup(
                    path=self._rel(self.mockup),
                    sha256=sha256_path(self.mockup),
                    screen_name="Форма клиента",
                    locators=("Контактная форма",),
                ),
            ),
        )
        receipt = replace(contract.review_receipt, manifest_digest=manifest.digest)
        derivations = load_property_derivations(
            fixture.derivations,
            expected_source_manifest_digest=contract.manifest.digest,
            expected_obligation_set_digest=fixture.prepared_obligations.digest,
        )
        graph = build_coverage_graph(
            ft_slug="sample",
            tc_prefix="SMP",
            source_manifest=manifest,
            obligation_set=fixture.prepared_obligations,
            derivations=tuple(
                replace(item, source_manifest_digest=manifest.digest)
                for item in derivations.derivations
            ),
        )
        evidence_basis = prepare_reviewer_evidence_basis(
            self.repo,
            compiled,
            manifest,
            receipt,
            fixture.prepared_obligations,
        )
        self.cycle = self.ft / "work" / "immutable" / "promotion-v2"
        self.cycle.parent.mkdir(parents=True, exist_ok=True)
        result = run_immutable_iteration(
            repo_root=self.repo,
            graph=graph,
            context=fixture.context,
            output_dir=self.cycle,
            protected_source_paths=tuple(
                item.path for item in evidence_basis.registered_files
            ),
            protected_canonical_paths=(self.canonical,),
            backend=FixtureBackend(),
            reviewer_evidence_basis=evidence_basis,
        )
        self.assertEqual("accepted-shadow", result.status)
        assert result.draft_path is not None
        self.candidate = result.draft_path
        self.candidate_before = self.candidate.read_text(encoding="utf-8")
        self.graph = graph.to_dict()
        self.graph_digest = graph.digest
        self.request = json.loads(
            (self.cycle / "reviewer-request.json").read_text(encoding="utf-8")
        )
        self.response = json.loads(
            (self.cycle / "model-stages" / "reviewer-response.json").read_text(
                encoding="utf-8"
            )
        )
        receipts = json.loads(
            (self.cycle / "model-stage-receipts.json").read_text(encoding="utf-8")
        )["stages"]
        self.writer_receipt = next(item for item in receipts if item["stage"] == "writer")
        self.reviewer_receipt = next(
            item for item in receipts if item["stage"] == "reviewer"
        )
        self.reviewer_receipt["backend"] = "codex-exec-tool-free"
        self._write_receipts()

    def _rel(self, path: Path) -> str:
        return path.relative_to(self.repo).as_posix()

    def _protected(self, role: str, path: Path) -> dict[str, Any]:
        return {
            "role": role,
            "path": self._rel(path),
            "sha256": sha256_path(path),
            "size_bytes": path.stat().st_size,
        }

    def _reviewer_receipt(self) -> dict[str, Any]:
        model_dir = self.cycle / "model-stages"
        receipt = {
            "stage": "reviewer",
            "backend": "codex-exec-tool-free",
            "attempts": 1,
            "timeout_seconds": None,
            "tool_event_count": 0,
            "request_sha256": _canonical_digest(self.request),
            "prompt_sha256": sha256_path(model_dir / "reviewer-prompt.txt"),
            "schema_sha256": sha256_path(model_dir / "reviewer-output-schema.json"),
            "response_sha256": sha256_path(model_dir / "reviewer-response.json"),
        }
        if self.request.get("schema_version") == 2:
            mockups = self.request["reviewer_evidence_pack"]["mockup_attachments"]
            receipt["image_attachments"] = {
                "count": len(mockups),
                "bytes": sum(item["size_bytes"] for item in mockups),
            }
        return receipt

    def _write_receipts(self, **summary_overrides: Any) -> None:
        stages = [self.writer_receipt, self.reviewer_receipt]
        _write_json(
            self.cycle / "model-stage-receipts.json",
            {"schema_version": 1, "stages": stages},
        )
        summary = {
            "schema_version": 1,
            "mode": "immutable-deterministic-first",
            "status": "accepted-shadow",
            "graph_digest": self.graph_digest,
            "draft": self._rel(self.candidate),
            "writer_model_calls": 0,
            "reviewer_model_calls": 1,
            "reviewer_decision": "accepted",
            "reviewer_accepted_zero_findings": True,
            "suite_gate_passed": True,
            "protected_inputs_unchanged": True,
            "canonical_publication": "not-performed",
            "promotion": "out-of-scope",
            "model_stages": stages,
        }
        summary.update(summary_overrides)
        _write_json(self.cycle / "iteration-summary.json", summary)

    def _rewrite_response(self) -> None:
        _write_json(self.cycle / "model-stages" / "reviewer-response.json", self.response)
        self.reviewer_receipt = self._reviewer_receipt()
        self._write_receipts()

    def _rewrite_v2_contract(self) -> None:
        model_dir = self.cycle / "model-stages"
        _write_json(self.cycle / "reviewer-request.json", self.request)
        (model_dir / "reviewer-prompt.txt").write_text(
            reviewer_prompt_instruction(2)
            + "\nREQUEST JSON:\n"
            + _canonical_bytes(self.request).decode("utf-8")
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        bindings = tuple(
            (
                item["case_key"],
                item["tc_id"],
                item["obligation_ids"][0],
                item["status"],
            )
            for item in self.graph["cases"]
        )
        self.schema = reviewer_response_schema(
            bindings,
            graph_digest=self.graph_digest,
            draft_sha256=sha256_path(self.candidate),
            reviewer_request=self.request,
        )
        _write_json(model_dir / "reviewer-output-schema.json", self.schema)
        _write_json(model_dir / "reviewer-response.json", self.response)
        self.reviewer_receipt = self._reviewer_receipt()
        self._write_receipts()

    def _upgrade_to_v2(self) -> tuple[dict[str, Any], Path]:
        pack = json.loads(
            (self.cycle / "reviewer-evidence-pack.json").read_text(encoding="utf-8")
        )
        return pack, self.mockup

        # Kept unreachable only as historical fixture shape below; production
        # tests use the independently built source-qualified v2 package above.
        mockup = self.ft / "source" / "mockups" / "contact-form.png"
        mockup.parent.mkdir(parents=True)
        Image.new("RGB", (3, 2), color=(31, 97, 173)).save(mockup)
        pack = {
            "schema_version": 2,
            "identity": {
                "contract": "reviewer-evidence-pack-v2",
                "graph_digest": self.graph_digest,
                "coverage_graph_digest": self.graph_digest,
                "draft_sha256": sha256_path(self.candidate),
                "scope_id": "demo-scope",
                "source_manifest_digest": self.graph["source_manifest_digest"],
                "obligation_set_digest": self.graph["obligation_set_digest"],
            },
            "literal_source_evidence": [
                {
                    "source_row_id": "SRC-001",
                    "candidate_id": "SRC-CAND-111111111111111111111111",
                    "bounded_source_text": "Поле принимает только цифровые символы.",
                    "bounded_source_text_sha256": hashlib.sha256(
                        "Поле принимает только цифровые символы.".encode("utf-8")
                    ).hexdigest(),
                }
            ],
            "source_structure": {
                "scope_definition": {
                    "gap_ids": [],
                    "source_set": {"pdf": None},
                },
                "docx_xhtml_pdf_parity": {
                    "contract": "bounded-source-parity-v1",
                    "status": "verified",
                    "docx_xhtml": {
                        "status": "verified",
                        "literal_candidate_count": 1,
                        "matched_literal_candidate_count": 1,
                        "row_matches": [
                            {
                                "candidate_id": "SRC-CAND-111111111111111111111111",
                                "source_row_id": "SRC-001",
                            }
                        ],
                    },
                    "pdf_requirement_codes": {"status": "not-registered"},
                },
            },
            "dictionaries": [],
            "coverage_gaps": {
                "artifact": {
                    "role": "scope-coverage-gaps",
                    "path": "work/coverage-gaps.md",
                    "sha256": hashlib.sha256(b"# Coverage gaps\n\nNo gaps.\n").hexdigest(),
                    "size_bytes": len(b"# Coverage gaps\n\nNo gaps.\n"),
                },
                "registered_gap_ids": [],
                "materialized_gap_ids": [],
                "content": "# Coverage gaps\n\nNo gaps.\n",
                "content_sha256": hashlib.sha256(
                    b"# Coverage gaps\n\nNo gaps.\n"
                ).hexdigest(),
                "status": "complete-literal-registered-artifact",
            },
            "mockup_attachments": [
                {
                    "path": self._rel(mockup),
                    "role": "scope-mockup",
                    "scope_id": "demo-scope",
                    "sha256": sha256_path(mockup),
                    "size_bytes": mockup.stat().st_size,
                    "screen_description": "Форма",
                    "locators": [],
                }
            ],
            "normalized_projection": self.graph,
            "test_cases": {
                "draft_markdown": self.candidate.read_bytes().decode("utf-8"),
                "designs": [
                    {
                        "case_key": "CASE-001",
                        "tc_id": "TC-001",
                        "status": "executable",
                    }
                ],
            },
            "coverage_mapping": [
                {
                    "source_row_id": "SRC-001",
                    "assertion_id": "AST-001",
                    "property_id": "PROP-001",
                    "obligation_id": "OBL-001",
                    "case_key": "CASE-001",
                    "tc_id": "TC-001",
                }
            ],
            "supporting_evidence_mapping": [],
            "design_support_mapping": [],
            "acceptance": reviewer_acceptance_contract(schema_version=2),
        }
        self.request = {
            "schema_version": 2,
            "graph_digest": self.graph_digest,
            "draft_sha256": sha256_path(self.candidate),
            "evidence_pack_sha256": _canonical_digest(pack),
            "reviewer_evidence_pack": pack,
            "acceptance": reviewer_acceptance_contract(schema_version=2),
        }
        _write_json(self.cycle / "reviewer-evidence-pack.json", pack)
        _write_json(self.cycle / "reviewer-request.json", self.request)
        prompt = (
            reviewer_prompt_instruction(2)
            + "\nREQUEST JSON:\n"
            + _canonical_bytes(self.request).decode("utf-8")
            + "\n"
        )
        model_dir = self.cycle / "model-stages"
        (model_dir / "reviewer-prompt.txt").write_text(
            prompt,
            encoding="utf-8",
            newline="\n",
        )
        self.schema = reviewer_response_schema(
            (("CASE-001", "TC-001", "OBL-001", "executable"),),
            graph_digest=self.graph_digest,
            draft_sha256=sha256_path(self.candidate),
            reviewer_request=self.request,
        )
        _write_json(model_dir / "reviewer-output-schema.json", self.schema)
        self.response = {
            "schema_version": 2,
            "graph_digest": self.graph_digest,
            "draft_sha256": sha256_path(self.candidate),
            "evidence_pack_sha256": self.request["evidence_pack_sha256"],
            "decision": "accepted",
            "case_results": [
                {
                    "case_key": "CASE-001",
                    "tc_id": "TC-001",
                    "obligation_id": "OBL-001",
                    "status": "covered",
                    "comment": "Покрытие проверено по буквальному источнику.",
                }
            ],
            "source_projection_findings": [],
            "test_case_findings": [],
            "summary": "Набор принят.",
        }
        _write_json(model_dir / "reviewer-response.json", self.response)
        self.reviewer_receipt = self._reviewer_receipt()
        self._write_receipts()
        return pack, mockup

    def prepare(self):
        return prepare_immutable_iteration_promotion(
            repo_root=self.repo,
            ft_root=self.ft,
            iteration_output_dir=self.cycle,
            scope_slug="sample-scope",
        )

    def test_builds_and_reuses_minimal_eligibility_basis_without_publication(self) -> None:
        result = self.prepare()

        self.assertEqual("eligible-built", result.status)
        self.assertEqual(self.canonical_before, self.canonical.read_bytes())
        self.assertEqual(sha256_path(result.basis_path), result.basis_sha256)
        self.assertEqual(sha256_path(self.candidate), result.candidate_sha256)
        self.assertEqual(
            {"test-cases/1-existing.md": sha256_path(self.canonical)},
            result.production_test_case_hashes,
        )
        basis = json.loads(result.basis_path.read_text(encoding="utf-8"))
        self.assertTrue(basis["eligible"])
        self.assertEqual("not-performed", basis["publication"])
        self.assertEqual(
            sha256_path(self.cycle / "model-stages" / "reviewer-response.json"),
            basis["reviewer_receipt"]["response_sha256"],
        )
        self.assertEqual(
            sha256_path(self.cycle / "reviewer-evidence-basis.json"),
            basis["bindings"]["reviewer_evidence_basis"]["sha256"],
        )
        self.assertEqual(
            sha256_path(self.cycle / "test-case-designs.json"),
            basis["bindings"]["test_case_designs"]["sha256"],
        )
        self.assertNotIn("cycle_state", json.dumps(basis))
        self.assertNotIn("traceability_matrix", json.dumps(basis))

        reused = self.prepare()
        self.assertEqual("eligible-reused", reused.status)
        self.assertEqual(result.basis_sha256, reused.basis_sha256)
        self.assertEqual(self.canonical_before, self.canonical.read_bytes())

    def test_schema_v1_iteration_is_explicitly_non_promotable(self) -> None:
        _write_json(
            self.cycle / "reviewer-request.json",
            {
                "schema_version": 1,
                "graph_digest": self.graph_digest,
                "draft_sha256": sha256_path(self.candidate),
                "cases": [],
                "acceptance": reviewer_acceptance_contract(),
            },
        )

        with self.assertRaisesRegex(PromotionAdapterBlocked, "reviewer-v2-required"):
            self.prepare()

    def test_v2_rejects_coherently_rehashed_previous_reviewer_policy(self) -> None:
        request = copy.deepcopy(self.request)
        case_bindings = tuple(
            (
                item["case_key"],
                item["tc_id"],
                item["obligation_ids"][0],
                item["status"],
            )
            for item in self.graph["cases"]
        )
        self.assertEqual(
            2,
            _validate_reviewer_request(
                request,
                graph_digest=self.graph_digest,
                candidate_sha256=sha256_path(self.candidate),
                case_bindings=case_bindings,
            ),
        )

        previous_policy_only_missing = (
            "reviewer_policy_version",
            "adversarial_false_pass_check",
            "adversarial_false_fail_check",
            "failure_attribution_check",
            "trigger_fidelity_check",
            "probe_findings_require_concrete_witness",
            "probe_findings_require_exact_probe_binding",
            "per_probe_evidence_chain_binding_required",
            "per_probe_evidence_item_binding_required",
            "artifact_proven_findings_do_not_require_hypothetical_witness",
            "per_case_falsification_receipt_required",
            "live_falsification_receipt_allows_not_recorded",
        )
        pack = request["reviewer_evidence_pack"]
        for acceptance in (request["acceptance"], pack["acceptance"]):
            for field in previous_policy_only_missing:
                self.assertIn(field, acceptance)
                acceptance.pop(field)
        self.assertEqual(request["acceptance"], pack["acceptance"])
        request["evidence_pack_sha256"] = _canonical_digest(pack)

        with self.assertRaisesRegex(
            PromotionAdapterBlocked,
            "review-request-mismatch",
        ):
            _validate_reviewer_request(
                request,
                graph_digest=self.graph_digest,
                candidate_sha256=sha256_path(self.candidate),
                case_bindings=case_bindings,
            )

    def test_v2_binds_evidence_pack_separate_findings_and_registered_image_receipt(self) -> None:
        pack, mockup = self._upgrade_to_v2()

        result = self.prepare()

        self.assertEqual("eligible-built", result.status)
        basis = json.loads(result.basis_path.read_text(encoding="utf-8"))
        self.assertEqual(
            sha256_path(self.cycle / "reviewer-evidence-pack.json"),
            basis["bindings"]["reviewer_evidence_pack"]["sha256"],
        )
        self.assertEqual(
            {"count": 1, "bytes": mockup.stat().st_size},
            basis["reviewer_receipt"]["image_attachments"],
        )
        self.assertEqual(
            _canonical_digest(pack),
            self.response["evidence_pack_sha256"],
        )

    def test_v2_rejects_evidence_artifact_or_digest_drift(self) -> None:
        pack, _mockup = self._upgrade_to_v2()
        changed = dict(pack)
        changed["source_structure"] = {"forged": True}
        _write_json(self.cycle / "reviewer-evidence-pack.json", changed)
        with self.assertRaisesRegex(PromotionAdapterBlocked, "review-evidence-pack-mismatch"):
            self.prepare()

        _write_json(self.cycle / "reviewer-evidence-pack.json", pack)
        self.request["evidence_pack_sha256"] = "0" * 64
        _write_json(self.cycle / "reviewer-request.json", self.request)
        with self.assertRaisesRegex(PromotionAdapterBlocked, "review-request-mismatch"):
            self.prepare()

    def test_coherently_rehashed_fabricated_pack_fails_independent_rebuild(self) -> None:
        pack, _mockup = self._upgrade_to_v2()
        pack = copy.deepcopy(pack)
        pack["dictionaries"] = [{"fabricated": True}]
        digest = _canonical_digest(pack)
        self.request["reviewer_evidence_pack"] = pack
        self.request["evidence_pack_sha256"] = digest
        self.response["evidence_pack_sha256"] = digest
        _write_json(self.cycle / "reviewer-evidence-pack.json", pack)
        self._rewrite_v2_contract()

        with self.assertRaisesRegex(
            PromotionAdapterBlocked,
            "review-evidence-rebuild-mismatch",
        ):
            self.prepare()

    def test_v2_rejects_findings_in_either_closed_category(self) -> None:
        pack, _mockup = self._upgrade_to_v2()
        chain = next(item for item in pack["coverage_mapping"] if item["case_key"])
        source_finding = {
            "severity": "warning",
            "finding_type": "source-element-omitted",
            **{
                name: chain[name]
                for name in (
                    "source_row_id",
                    "assertion_id",
                    "property_id",
                    "obligation_id",
                    "case_key",
                    "tc_id",
                )
            },
            "message": "Потеряно буквальное условие.",
        }
        test_finding = {
            "severity": "warning",
            "finding_type": "traceability-incorrect",
            "binding_role": "primary",
            "falsification_probe": "",
            **{
                name: chain[name]
                for name in (
                    "source_row_id",
                    "assertion_id",
                    "property_id",
                    "obligation_id",
                    "case_key",
                    "tc_id",
                )
            },
            "message": "Некорректная трассировка.",
        }
        for field, finding in (
            ("source_projection_findings", source_finding),
            ("test_case_findings", test_finding),
        ):
            with self.subTest(field=field):
                self.response[field] = [finding]
                self._rewrite_response()
                with self.assertRaisesRegex(
                    PromotionAdapterBlocked,
                    "review-response-not-accepted",
                ):
                    self.prepare()
                self.response[field] = []
                self._rewrite_response()

    def test_v2_promotion_rejects_unrecorded_falsification_receipt(self) -> None:
        for case_result in self.response["case_results"]:
            for probe_result in case_result["falsification"].values():
                probe_result["outcome"] = "not-recorded"
                probe_result["detail"] = "Legacy review did not record this probe."
        self._rewrite_v2_contract()

        with self.assertRaisesRegex(
            PromotionAdapterBlocked,
            "review-response-invalid",
        ):
            self.prepare()

    def test_v2_promotion_rejects_fabricated_falsification_basis(self) -> None:
        self.response["case_results"][0]["falsification"]["false_pass"][
            "trigger_or_step"
        ] = "Fabricated step absent from the reviewed design."
        self._rewrite_response()

        with self.assertRaisesRegex(
            PromotionAdapterBlocked,
            "review-response-not-accepted",
        ):
            self.prepare()

    def test_v2_promotion_rejects_source_only_trigger_as_passed_basis(self) -> None:
        request = copy.deepcopy(self.request)
        response = copy.deepcopy(self.response)
        pack = request["reviewer_evidence_pack"]
        design = pack["test_cases"]["designs"][0]
        source_trigger = design["steps"][0]
        tc_only_step = "Inspect the already-open current screen."
        design["steps"] = [tc_only_step]
        request["evidence_pack_sha256"] = _canonical_digest(pack)
        response["evidence_pack_sha256"] = request["evidence_pack_sha256"]
        for probe, probe_result in response["case_results"][0][
            "falsification"
        ].items():
            probe_result["trigger_or_step"] = (
                source_trigger if probe == "trigger_fidelity" else tc_only_step
            )
        bindings = tuple(
            (
                item["case_key"],
                item["tc_id"],
                item["obligation_ids"][0],
                item["status"],
            )
            for item in self.graph["cases"]
        )
        schema = reviewer_response_schema(
            bindings,
            graph_digest=self.graph_digest,
            draft_sha256=sha256_path(self.candidate),
            reviewer_request=request,
        )

        with self.assertRaisesRegex(
            PromotionAdapterBlocked,
            "review-response-not-accepted",
        ):
            _validate_promotion_reviewer_response(
                response,
                schema=schema,
                graph_digest=self.graph_digest,
                candidate_sha256=sha256_path(self.candidate),
                case_bindings=bindings,
                request_payload=request,
            )

    def test_v2_promotion_requires_all_docx_rows_and_nonregistered_pdf_semantics(
        self,
    ) -> None:
        case_bindings = tuple(
            (
                item["case_key"],
                item["tc_id"],
                item["obligation_ids"][0],
                item["status"],
            )
            for item in self.graph["cases"]
        )
        base = copy.deepcopy(self.request)

        missing_docx_row = copy.deepcopy(base)
        pack = missing_docx_row["reviewer_evidence_pack"]
        target = pack["literal_source_evidence"][-1]
        match_field = (
            "row_matches"
            if target["candidate_id"] is not None
            else "auxiliary_row_matches"
        )
        matches = pack["source_structure"]["docx_xhtml_pdf_parity"][
            "docx_xhtml"
        ][match_field]
        matches[:] = [
            item
            for item in matches
            if item["source_row_id"] != target["source_row_id"]
        ]
        missing_docx_row["evidence_pack_sha256"] = _canonical_digest(pack)

        missing_pdf_semantics = copy.deepcopy(base)
        pack = missing_pdf_semantics["reviewer_evidence_pack"]
        pack["source_structure"]["docx_xhtml_pdf_parity"][
            "pdf_requirement_codes"
        ].pop("semantic_literal_rows")
        missing_pdf_semantics["evidence_pack_sha256"] = _canonical_digest(pack)

        wrong_total = copy.deepcopy(base)
        pack = wrong_total["reviewer_evidence_pack"]
        docx_parity = pack["source_structure"]["docx_xhtml_pdf_parity"][
            "docx_xhtml"
        ]
        docx_parity["matched_literal_xhtml_row_count"] -= 1
        wrong_total["evidence_pack_sha256"] = _canonical_digest(pack)

        for request in (missing_docx_row, missing_pdf_semantics, wrong_total):
            with self.subTest(request=request):
                with self.assertRaisesRegex(
                    PromotionAdapterBlocked,
                    "bounded DOCX/XHTML/PDF parity proof is incomplete",
                ):
                    _validate_reviewer_request(
                        request,
                        graph_digest=self.graph_digest,
                        candidate_sha256=sha256_path(self.candidate),
                        case_bindings=case_bindings,
                    )

    def test_v2_promotion_registered_pdf_requires_exact_literal_row_set(self) -> None:
        request = copy.deepcopy(self.request)
        pack = request["reviewer_evidence_pack"]
        literal_row_ids = [
            item["source_row_id"] for item in pack["literal_source_evidence"]
        ]
        pack["source_structure"]["scope_definition"]["source_set"]["pdf"] = {
            "path": "source/main.pdf"
        }
        pack["source_structure"]["docx_xhtml_pdf_parity"][
            "pdf_requirement_codes"
        ] = {
            "status": "verified",
            "semantic_literal_rows": {
                "status": "verified",
                "literal_xhtml_row_count": len(literal_row_ids),
                "matched_literal_xhtml_row_count": len(literal_row_ids),
                "row_matches": [
                    {"source_row_id": source_row_id}
                    for source_row_id in literal_row_ids
                ],
            },
        }
        request["evidence_pack_sha256"] = _canonical_digest(pack)
        case_bindings = tuple(
            (
                item["case_key"],
                item["tc_id"],
                item["obligation_ids"][0],
                item["status"],
            )
            for item in self.graph["cases"]
        )

        _validate_reviewer_request(
            request,
            graph_digest=self.graph_digest,
            candidate_sha256=sha256_path(self.candidate),
            case_bindings=case_bindings,
        )

        semantic = pack["source_structure"]["docx_xhtml_pdf_parity"][
            "pdf_requirement_codes"
        ]["semantic_literal_rows"]
        semantic["row_matches"][-1]["source_row_id"] = literal_row_ids[0]
        request["evidence_pack_sha256"] = _canonical_digest(pack)
        with self.assertRaisesRegex(
            PromotionAdapterBlocked,
            "bounded DOCX/XHTML/PDF parity proof is incomplete",
        ):
            _validate_reviewer_request(
                request,
                graph_digest=self.graph_digest,
                candidate_sha256=sha256_path(self.candidate),
                case_bindings=case_bindings,
            )

    def test_v2_promotion_shape_rejects_primary_chain_as_design_support(self) -> None:
        request = copy.deepcopy(self.request)
        pack = request["reviewer_evidence_pack"]
        primary = next(item for item in pack["coverage_mapping"] if item["case_key"])
        design = next(
            item
            for item in pack["test_cases"]["designs"]
            if item["case_key"] == primary["case_key"]
        )
        obligation = next(
            item
            for item in pack["normalized_projection"]["obligations"]
            if item["obligation_id"] == primary["obligation_id"]
        )
        fragment = obligation["validation_trigger"]
        item_index = next(
            index for index, item in enumerate(design["steps"]) if fragment in item
        )
        materialized_text = design["steps"][item_index]
        pack["design_support_mapping"] = [
            {
                "support_role": "action",
                "test_case_field": "steps",
                "item_index": item_index,
                "materialized_text": materialized_text,
                "materialized_text_sha256": hashlib.sha256(
                    materialized_text.encode("utf-8")
                ).hexdigest(),
                "source_action_fragment": fragment,
                **primary,
            }
        ]
        request["evidence_pack_sha256"] = _canonical_digest(pack)
        case_bindings = tuple(
            (
                item["case_key"],
                item["tc_id"],
                item["obligation_ids"][0],
                item["status"],
            )
            for item in self.graph["cases"]
        )

        with self.assertRaisesRegex(
            PromotionAdapterBlocked,
            r"design_support_mapping\[0\] binding is invalid",
        ):
            _validate_reviewer_request(
                request,
                graph_digest=self.graph_digest,
                candidate_sha256=sha256_path(self.candidate),
                case_bindings=case_bindings,
            )

    def test_v2_requires_schema_specific_prompt_and_exact_image_metrics(self) -> None:
        self._upgrade_to_v2()
        model_dir = self.cycle / "model-stages"
        legacy_prompt = (
            REVIEWER_PROMPT_INSTRUCTION
            + "\nREQUEST JSON:\n"
            + _canonical_bytes(self.request).decode("utf-8")
            + "\n"
        )
        (model_dir / "reviewer-prompt.txt").write_text(
            legacy_prompt,
            encoding="utf-8",
            newline="\n",
        )
        with self.assertRaisesRegex(PromotionAdapterBlocked, "review-prompt-mismatch"):
            self.prepare()

        prompt = (
            reviewer_prompt_instruction(2)
            + "\nREQUEST JSON:\n"
            + _canonical_bytes(self.request).decode("utf-8")
            + "\n"
        )
        (model_dir / "reviewer-prompt.txt").write_text(
            prompt,
            encoding="utf-8",
            newline="\n",
        )
        self.reviewer_receipt = self._reviewer_receipt()
        self.reviewer_receipt["image_attachments"]["bytes"] += 1
        self._write_receipts()
        with self.assertRaisesRegex(PromotionAdapterBlocked, "review-receipt-invalid"):
            self.prepare()

    def test_v2_rejects_registered_mockup_drift(self) -> None:
        _pack, mockup = self._upgrade_to_v2()
        Image.new("RGB", (3, 2), color=(173, 31, 97)).save(mockup)

        with self.assertRaisesRegex(
            PromotionAdapterBlocked,
            "review-evidence-rebuild-failed|review-mockup-drift",
        ):
            self.prepare()

    def test_requires_zero_writer_and_one_reviewer_call(self) -> None:
        for field, value in (("writer_model_calls", 1), ("reviewer_model_calls", 0)):
            with self.subTest(field=field):
                self._write_receipts(**{field: value})
                with self.assertRaisesRegex(PromotionAdapterBlocked, "iteration-not-eligible"):
                    self.prepare()
                self._write_receipts()

    def test_rejects_qualification_only_and_non_promotable_runs(self) -> None:
        for overrides in (
            {"qualification_only": True},
            {"promotion_eligible": False},
            {"non_promotable_reason": "fixture-test-hook"},
        ):
            with self.subTest(overrides=overrides):
                self._write_receipts(**overrides)
                with self.assertRaisesRegex(
                    PromotionAdapterBlocked, "qualification-not-promotable"
                ):
                    self.prepare()
                self._write_receipts()

    def test_rejects_accepted_suite_with_calibration_pending(self) -> None:
        self._write_receipts(
            status="accepted-with-calibration-pending",
            calibration_pending_count=1,
            promotion_eligible=False,
            non_promotable_reason="calibration-pending",
        )

        with self.assertRaisesRegex(PromotionAdapterBlocked, "calibration-pending"):
            self.prepare()

    def test_requires_authentic_tool_free_reviewer_receipt(self) -> None:
        invalid = {
            "backend": "fixture",
            "attempts": 0,
            "timeout_seconds": 30,
            "tool_event_count": 1,
        }
        for field, value in invalid.items():
            with self.subTest(field=field):
                original = self.reviewer_receipt[field]
                self.reviewer_receipt[field] = value
                self._write_receipts()
                with self.assertRaisesRegex(PromotionAdapterBlocked, "review-receipt-invalid"):
                    self.prepare()
                self.reviewer_receipt[field] = original
                self._write_receipts()

    def test_rejects_each_broken_reviewer_hash_binding(self) -> None:
        for field in (
            "request_sha256",
            "prompt_sha256",
            "schema_sha256",
            "response_sha256",
        ):
            with self.subTest(field=field):
                original = self.reviewer_receipt[field]
                self.reviewer_receipt[field] = "0" * 64
                self._write_receipts()
                with self.assertRaisesRegex(PromotionAdapterBlocked, "review-receipt-invalid"):
                    self.prepare()
                self.reviewer_receipt[field] = original
                self._write_receipts()

    def test_rejects_not_covered_or_finding_bearing_response_even_when_rehashed(self) -> None:
        self.response["case_results"][0]["status"] = "not-covered"
        self._rewrite_response()
        with self.assertRaisesRegex(PromotionAdapterBlocked, "review-response-not-accepted"):
            self.prepare()

        self.response["case_results"][0]["status"] = "covered"
        pack = self.request["reviewer_evidence_pack"]
        chain = next(item for item in pack["coverage_mapping"] if item["case_key"])
        self.response["test_case_findings"] = [
            {
                "severity": "warning",
                "finding_type": "test-case-defect",
                "binding_role": "primary",
                "falsification_probe": "",
                **{
                    name: chain[name]
                    for name in (
                        "source_row_id",
                        "assertion_id",
                        "property_id",
                        "obligation_id",
                        "case_key",
                        "tc_id",
                    )
                },
                "message": "Найдено замечание.",
            }
        ]
        self._rewrite_response()
        with self.assertRaisesRegex(PromotionAdapterBlocked, "review-response-not-accepted"):
            self.prepare()

    def test_rejects_candidate_graph_and_suite_drift(self) -> None:
        self.candidate.write_text("# Changed shadow\n", encoding="utf-8")
        with self.assertRaisesRegex(PromotionAdapterBlocked, "suite-gate-mismatch"):
            self.prepare()

        self.candidate.write_text(self.candidate_before, encoding="utf-8")
        self.graph["ft_slug"] = "changed"
        _write_json(self.cycle / "coverage-graph.json", self.graph)
        with self.assertRaisesRegex(PromotionAdapterBlocked, "graph-mismatch"):
            self.prepare()

    def test_rejects_incomplete_or_changed_canonical_baseline(self) -> None:
        unprotected = self.ft / "test-cases" / "4.2-unprotected.md"
        unprotected.write_text("# Unprotected\n", encoding="utf-8")
        with self.assertRaisesRegex(
            PromotionAdapterBlocked, "incomplete-canonical-baseline"
        ):
            self.prepare()
        unprotected.unlink()

        self.canonical.write_text("# Changed canonical\n", encoding="utf-8")
        with self.assertRaisesRegex(PromotionAdapterBlocked, "protected-input-drift"):
            self.prepare()

    def test_conflicting_existing_basis_fails_closed(self) -> None:
        basis = self.cycle / "promotion-eligibility-basis.json"
        _write_json(basis, {"forged": True})

        with self.assertRaisesRegex(PromotionAdapterBlocked, "basis-conflict"):
            self.prepare()
        self.assertEqual(self.canonical_before, self.canonical.read_bytes())


if __name__ == "__main__":
    unittest.main()
