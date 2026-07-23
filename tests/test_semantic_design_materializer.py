from __future__ import annotations

import copy
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.materialize_semantic_design_bridge import parser
from test_case_agent.bounded_scope_materializer import (
    BoundedScopeMaterializationError,
    _assertion_payload,
    _cell,
    _is_explicit_direct_calibration_candidate,
    _portable_fixture_contract_lines,
    _render_clarification_requests,
    _render_coverage_gaps,
    _resolved_scope_exclusion_gap_links,
    materialize_semantic_design_bridge,
)


ROOT = Path(__file__).resolve().parents[1]
OWNER_TOKEN = "11111111-1111-4111-8111-111111111111"


class SemanticDesignMaterializerTests(unittest.TestCase):
    def test_direct_calibration_candidate_is_typed_not_notes_driven(self) -> None:
        candidate = {
            "obligation_class": "candidate-ui-calibration",
            "oracle_source": "not_found",
            "scope_obligation_ids": [],
            "planned_tc_id": "candidate:FIELD-INVALID",
            "single_expected_behavior": "Точный UI-отклик требует калибровки.",
            "test_data": "Иванов1",
            "review_notes": "no marker required",
        }
        self.assertTrue(_is_explicit_direct_calibration_candidate(candidate))

        notes_only = dict(candidate)
        notes_only["obligation_class"] = "format-check"
        notes_only["review_notes"] = "candidate-ui-calibration"
        self.assertFalse(_is_explicit_direct_calibration_candidate(notes_only))

    def test_verified_fixture_is_rendered_as_portable_inline_contract(self) -> None:
        fixture_path = (
            ROOT
            / "fts/AutoFin/work/vendor-references/dadata-fixtures"
            / "FX-DADATA-FMS-POS-001"
            / "FX-DADATA-FMS-POS-001.verification.json"
        )
        relative = fixture_path.relative_to(ROOT).as_posix()
        lines = _portable_fixture_contract_lines(
            repo_root=ROOT,
            source_entries=[{"path": relative}],
            obligations=[
                {
                    "obligation_id": "OBL-001",
                    "test_data": "query=772-053; FX-DADATA-FMS-POS-001",
                }
            ],
        )
        self.assertEqual(1, len(lines))
        self.assertIn('request_parameters=`{"query":"772-053"}`', lines[0])
        self.assertIn('"exact_suggestion":"ОВД ЗЮЗИНО Г. МОСКВЫ"', lines[0])
        self.assertIn("runtime_api_call=`prohibited`", lines[0])

    def test_referenced_named_fixture_requires_registered_verification(self) -> None:
        with self.assertRaisesRegex(
            BoundedScopeMaterializationError,
            "named fixture lacks a registered verified portable contract",
        ):
            _portable_fixture_contract_lines(
                repo_root=ROOT,
                source_entries=[],
                obligations=[{"test_data": "FX-MISSING-001"}],
            )

    def test_party_fixture_contract_includes_hash_bound_address_component(self) -> None:
        fixture_dir = (
            ROOT
            / "fts/AutoFin/work/vendor-references/dadata-fixtures"
            / "FX-DADATA-PARTY-ACTIVE-001"
        )
        verification = fixture_dir / "FX-DADATA-PARTY-ACTIVE-001.verification.json"
        response = fixture_dir / "FX-DADATA-PARTY-ACTIVE-001.response.json"
        lines = _portable_fixture_contract_lines(
            repo_root=ROOT,
            source_entries=[
                {"path": verification.relative_to(ROOT).as_posix()},
                {"path": response.relative_to(ROOT).as_posix()},
            ],
            obligations=[
                {
                    "obligation_id": "OBL-ADDRESS",
                    "test_data": "FX-DADATA-PARTY-ACTIVE-001",
                }
            ],
        )

        self.assertEqual(1, len(lines))
        self.assertIn(
            '"address.value":"г Москва, ул Вавилова, д 19"',
            lines[0],
        )

    def test_resolved_partial_scope_exclusion_routes_to_na_sibling(self) -> None:
        links = _resolved_scope_exclusion_gap_links(
            clarifications=[
                {
                    "clarification_id": "CLR-001",
                    "gap_id": "GAP-001",
                    "requirement_codes": ["BSR 324"],
                }
            ],
            dependencies=[
                {
                    "dependency_id": "DEP-001",
                    "name": "kladr",
                    "resolution": "scope-excluded",
                    "source_row_ids": ["SRC-001"],
                }
            ],
            requirement_codes_by_row={"SRC-001": ("BSR 324",)},
            decisions_by_row={
                "SRC-001": {
                    "assertions": [
                        {
                            "assertion_id": "ASSERT-VISIBLE-001",
                            "atom_id": "ATOM-VISIBLE-001",
                            "semantic_disposition": "testable",
                            "field_or_block": "Адрес",
                        },
                        {
                            "assertion_id": "ASSERT-NA-001",
                            "atom_id": "ATOM-NA-001",
                            "semantic_disposition": "not-applicable",
                            "field_or_block": "kladr",
                        },
                    ]
                }
            },
        )
        self.assertEqual(
            {
                "assertion_ids": ("ASSERT-NA-001",),
                "atom_ids": ("ATOM-NA-001",),
            },
            links["GAP-001"],
        )

        rendered = _render_coverage_gaps(
            scope_slug="client-addresses",
            clarifications=[
                {"clarification_id": "CLR-001", "gap_id": "GAP-001"}
            ],
            boundary_gaps=[],
            requirement_codes_by_row={},
            gap_links=links,
        )
        self.assertIn("| status | resolved |", rendered)
        self.assertIn("| affected_assertion_id | ASSERT-NA-001 |", rendered)
        self.assertIn("| affected_atom_id | ATOM-NA-001 |", rendered)
        self.assertIn("| execution_obligation_ids |  |", rendered)

        empty_rendered = _render_coverage_gaps(
            scope_slug="client-addresses",
            clarifications=[
                {"clarification_id": "CLR-002", "gap_id": "GAP-002"}
            ],
            boundary_gaps=[],
            requirement_codes_by_row={},
            gap_links={},
        )
        self.assertIn("| affected_assertion_id |  |", empty_rendered)
        self.assertIn("| affected_atom_id |  |", empty_rendered)

    def test_markdown_table_cell_preserves_significant_path_spaces(self) -> None:
        self.assertEqual(
            "`mockups/Figure 3  Main state.jpg`",
            _cell("`mockups/Figure 3  Main state.jpg`"),
        )

    @staticmethod
    def _h68_design() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        context = json.loads(
            (ROOT / "evals/lean-production-benchmark/h68/bounded-scope-context.json").read_text(
                encoding="utf-8"
            )
        )
        legacy = json.loads(
            (ROOT / "evals/lean-production-benchmark/h68/golden-scope-decision.json").read_text(
                encoding="utf-8"
            )
        )
        boundary = {
            "version": 2,
            "status": "ready",
            "blocking_reason": "none_required",
            "scope_summary": legacy["scope_summary"],
            "scope_boundary": copy.deepcopy(context["scope_boundary"]),
            "source_decisions": [],
            "dependencies": [],
            "gaps": [],
            "mockup_locators": legacy["mockup_locators"],
        }
        source_designs = []
        for source_decision in legacy["source_decisions"]:
            projected = copy.deepcopy(source_decision)
            for assertion in projected["assertions"]:
                assertion["supporting_source_bindings"] = []
                assertion["clarification_clause_bindings"] = []
            disposition = "included" if projected["scope_disposition"] == "yes" else "context"
            source_designs.append(
                {
                    "source_row_id": projected["source_row_id"],
                    "boundary_disposition": disposition,
                    "requirement_codes": projected["requirement_codes"],
                    "assertions": projected["assertions"],
                }
            )
            boundary["source_decisions"].append(
                {
                    "source_row_id": projected["source_row_id"],
                    "disposition": disposition,
                    "requirement_codes": projected["requirement_codes"],
                    "rationale": "offline fixture",
                }
            )
        obligations = copy.deepcopy(legacy["obligations"])
        for obligation in obligations:
            obligation.update(
                {
                    "package_id": "WP-01",
                    "test_data": "none_required:action-only",
                    "dictionary_refs": [],
                    "dictionary_coverage": "none_required",
                    "scope_obligation_ids": [],
                }
            )
        design = {
            "version": 4,
            "contract": "semantic-design-bridge-v2",
            "status": "ready",
            "blocking_reason": "none_required",
            "prepared_context_sha256": "0" * 64,
            "scope_boundary_decision_sha256": "1" * 64,
            "scope_summary": legacy["scope_summary"],
            "included": copy.deepcopy(context["scope_boundary"]["include"]),
            "excluded": copy.deepcopy(context["scope_boundary"]["exclude"]),
            "mockup_locators": legacy["mockup_locators"],
            "source_designs": source_designs,
            "obligations": obligations,
            "reset_lifecycle_bindings": [],
            "dependency_bindings": [],
            "dictionaries": [],
            "negative_oracles": [],
            "requiredness_oracles": [],
            "applicability": copy.deepcopy(legacy["applicability"]),
        }
        return context, boundary, design

    def test_assertion_projection_preserves_support_and_clarification_bindings(self) -> None:
        row = {
            "source_row_id": "SRC-001",
            "source_path": "fts/F/source.xhtml",
            "source_context_class": "scope-local",
            "source_locator": "row:1",
            "bounded_source_text": "BSR 1. text",
        }
        assertion = {
            "assertion_id": "ASSERT-001",
            "canonical_statement": "statement",
            "polarity": "positive",
            "semantic_disposition": "testable",
            "execution_readiness": "ready",
            "execution_readiness_rationale": "none_required",
            "risk": "low",
            "condition_clauses": [],
            "action_clauses": ["action"],
            "oracle_clauses": ["oracle"],
            "requirement_codes": ["BSR 1"],
            "requirement_code_evidence": [
                {
                    "requirement_code": "BSR 1",
                    "source_row_id": "SRC-001",
                    "provenance_role": "pdf-parity",
                    "exact_source_fragment": "none_required",
                    "evidence_source_path": "fts/F/source.pdf",
                    "evidence_locator": "page:3",
                },
                {
                    "requirement_code": "BSR 1",
                    "source_row_id": "SRC-001",
                    "provenance_role": "xhtml-row",
                    "exact_source_fragment": "BSR 1",
                    "evidence_source_path": "none_required",
                    "evidence_locator": "none_required",
                },
            ],
            "clause_evidence": [],
            "atom_id": "ATOM-001",
            "obligation_ids": ["OBL-001"],
            "disposition_rationale": "none_required",
            "supporting_source_bindings": [
                {
                    "source_row_id": "SRC-002",
                    "evidence_role": "definition",
                    "exact_source_fragment": "definition",
                }
            ],
            "clarification_clause_bindings": [
                {
                    "clarification_id": "CLR-001",
                    "clause_kind": "oracle",
                    "clause_index": 0,
                    "requirement_codes": ["BSR 1"],
                    "exact_answer_sha256": "a" * 64,
                    "binding_scope": "requirement-code",
                    "source_row_ids": [],
                }
            ],
        }

        payload = _assertion_payload(row, assertion)

        self.assertEqual(payload["supporting_source_bindings"], assertion["supporting_source_bindings"])
        self.assertEqual(
            payload["clarification_clause_bindings"],
            assertion["clarification_clause_bindings"],
        )
        self.assertEqual(
            payload["requirement_code_bindings"][0]["provenance_role"],
            "pdf-parity",
        )
        self.assertEqual(
            payload["requirement_code_bindings"][0]["evidence_locator"], "page:3"
        )
        self.assertIsNone(
            payload["requirement_code_bindings"][0]["exact_source_fragment"]
        )
        self.assertIsNone(
            payload["requirement_code_bindings"][1]["evidence_source_path"]
        )
        self.assertIsNone(payload["requirement_code_bindings"][1]["evidence_locator"])

        ambiguous_payload = _assertion_payload(
            row,
            {
                **assertion,
                "semantic_disposition": "ambiguous",
                "execution_readiness": "dependency-blocked",
                "execution_readiness_rationale": (
                    "Требуется определить поведение до создания проверки."
                ),
                "obligation_ids": [],
            },
            primary_gap_id="GAP-001",
        )
        self.assertEqual("GAP-001", ambiguous_payload["primary_gap_id"])
        self.assertEqual(
            "dependency-blocked", ambiguous_payload["execution_readiness"]
        )

    def test_real_projection_publishes_only_final_handoff(self) -> None:
        context, boundary, design = self._h68_design()
        obligation = design["obligations"][0]
        obligation.update(
            {
                "property_type": "reset-action",
                "coverage_class": "reset-action",
                "dictionary_refs": ["DICT-001"],
                "dictionary_coverage": "reference-only",
                "scope_obligation_ids": ["SO-REQ-001"],
                "test_data": "DICT-001; fixture `Value A`",
            }
        )
        design["reset_lifecycle_bindings"].append(
            {
                "obligation_id": obligation["obligation_id"],
                "binding_kind": "reset",
                "initial_condition_index": 0,
                "changed_state_setup": (
                    "Prepare a visibly changed state before the action."
                ),
                "pre_action_state_oracle": (
                    "The visible state differs from the captured initial state."
                ),
                "state_relation": "different-from-captured-initial",
            }
        )
        executable_obligation = copy.deepcopy(obligation)
        executable_obligation.update(
            {
                "obligation_id": "OBL-EXEC-001",
                "planned_tc_id": "TC-AUTOFIN-APPLICATIONS-EXEC-001",
                "scope_obligation_ids": ["SO-NEG-001"],
            }
        )
        design["obligations"].append(executable_obligation)
        executable_binding = copy.deepcopy(
            design["reset_lifecycle_bindings"][0]
        )
        executable_binding["obligation_id"] = executable_obligation[
            "obligation_id"
        ]
        design["reset_lifecycle_bindings"].append(executable_binding)
        for source_design in design["source_designs"]:
            for assertion in source_design["assertions"]:
                if obligation["obligation_id"] in assertion["obligation_ids"]:
                    assertion["obligation_ids"].append(
                        executable_obligation["obligation_id"]
                    )
        source_row = next(
            item for item in context["source_rows"] if item["source_row_id"] == "SRC-006"
        )
        boundary["gaps"] = [
            {
                "gap_id": "GAP-UI-001",
                "gap_type": "ambiguity",
                "source_row_ids": ["SRC-006"],
                "source_refs": [source_row["source_ref"]],
                "exact_source_fragments": ["BSR 38"],
                "blocking": False,
                "clarification_question": "Какой точный UI-отклик отображается?",
                "downstream_handling": "carry-to-source-model",
            }
        ]
        design["dictionaries"] = [
            {
                "dictionary_id": "DICT-001",
                "dictionary_name": "Fixture values",
                "source_row_ids": ["SRC-006"],
                "source_file": context["main_ft_xhtml"],
                "source_location": "BSR 38",
                "extraction_status": "extracted",
                "active_values": ["Value A", "Value B"],
                "archived_values": [],
                "gap_id": "none_required:covered",
                "notes": "Offline projection fixture.",
            }
        ]
        oracle_common = {
            "signal_id": "SIG-NEG-001",
            "requirement_codes": ["BSR 38"],
            "scope_obligation_id": "SO-NEG-001",
            "source_row_id": "SRC-006",
            "source_ref": "BSR 38",
            "field_or_block": "Create action",
            "restriction_type": "other",
            "negative_class": "invalid-action",
            "source_statement": "Fixture restriction.",
            "representative_invalid_value": "not_derived",
            "observable_oracle_found": "yes",
            "oracle_source": "FT",
            "oracle_status": "source-backed",
            "decision": "executable_tc",
            "planned_tc_or_gap": executable_obligation["planned_tc_id"],
            "gap_id": "none_required:covered",
            "analyst_question": "none_required",
            "handoff_rule": "Preserve the linked obligation.",
            "calibration_notes": "not_applicable",
            "linked_atom_id": obligation["linked_atom_id"],
            "linked_obligation_id": executable_obligation["obligation_id"],
        }
        design["negative_oracles"] = [oracle_common]
        design["requiredness_oracles"] = [
            {
                "signal_id": "SIG-REQ-001",
                "requirement_codes": ["BSR 38"],
                "scope_obligation_id": "SO-REQ-001",
                "source_row_id": "SRC-006",
                "source_ref": "BSR 38",
                "field_or_block": "Create action",
                "restriction_type": "requiredness",
                "requiredness_source": "Fixture source.",
                "requiredness_class": "marker-only",
                "required_when": "always",
                "marker_oracle_found": "no",
                "empty_value_oracle_found": "no",
                "oracle_source": "not_found",
                "oracle_status": "ui-calibration-required",
                "decision": "candidate_tc_required",
                "planned_tc_or_gap": "candidate:SO-REQ-001",
                "gap_id": "GAP-UI-001",
                "analyst_question": "Какой точный UI-отклик отображается?",
                "handoff_rule": "Calibrate in UI without inventing the reaction.",
                "calibration_notes": "Статус тест-кейса: candidate-ui-calibration.",
                "linked_atom_id": obligation["linked_atom_id"],
                "linked_obligation_id": obligation["obligation_id"],
            }
        ]
        stage_root = ROOT / "fts/AutoFin/work/stage-handoffs"
        with tempfile.TemporaryDirectory(prefix="semantic-materializer-test-", dir=stage_root) as raw:
            final_dir = Path(raw) / "final"
            receipt = {
                "version": 1,
                "status": "verified",
                "contract": "scope-v2-to-semantic-design-v1",
            }
            with (
                patch(
                    "test_case_agent.bounded_scope_materializer.validate_bridge_boundary"
                ),
                patch(
                    "test_case_agent.bounded_scope_materializer.validate_semantic_design_binding",
                    return_value=receipt,
                ),
            ):
                result = materialize_semantic_design_bridge(
                    repo_root=ROOT,
                    context=context,
                    scope_boundary_decision=boundary,
                    semantic_design=design,
                    approved_clarifications=(),
                    publication_owner_token=OWNER_TOKEN,
                    handoff_dir=final_dir,
                )

            self.assertTrue(final_dir.is_dir())
            self.assertFalse(list(final_dir.parent.glob(".final.semantic-stage-*")))
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["materialization_status"], "materialized")
            self.assertEqual(result["publication"]["status"], "atomic-renamed")
            self.assertEqual(result["semantic_design_bridge"]["status"], "verified")
            self.assertTrue((final_dir / "scope-boundary-decision.json").is_file())
            self.assertTrue((final_dir / "semantic-design.json").is_file())
            self.assertTrue((final_dir / "semantic-design-bridge-receipt.json").is_file())
            published_receipt = json.loads(
                (final_dir / "semantic-design-bridge-receipt.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                "atomic-renamed", published_receipt["publication"]["status"]
            )
            self.assertEqual(
                "source-reviewer.prepare_evidence_set",
                published_receipt["downstream_evidence_readiness"][
                    "canonical_preflight"
                ],
            )
            self.assertEqual(
                published_receipt["source_assertion_manifest_digest"],
                published_receipt["downstream_evidence_readiness"][
                    "published_manifest_digest"
                ],
            )
            self.assertEqual(
                1, published_receipt["publication_ownership_contract_version"]
            )
            self.assertEqual(
                OWNER_TOKEN, published_receipt["publication_owner_token"]
            )
            self.assertEqual(
                hashlib.sha256(
                    (final_dir / "scope-boundary-decision.json").read_bytes()
                ).hexdigest(),
                published_receipt["scope_boundary_artifact_sha256"],
            )
            self.assertEqual(
                hashlib.sha256(
                    (final_dir / "semantic-design.json").read_bytes()
                ).hexdigest(),
                published_receipt["semantic_design_artifact_sha256"],
            )
            workflow = (final_dir / "workflow-state.yaml").read_text(encoding="utf-8")
            self.assertIn("current_stage: ft-scope-analyzer", workflow)
            self.assertIn("stage_status: ready-for-next-stage", workflow)
            self.assertIn("next_skill: ft-test-case-reviewer", workflow)
            self.assertIn("required_inputs:", workflow)
            self.assertIn("  non_blocking: 1", workflow)
            self.assertIn("scope_clarification_requests:", workflow)
            self.assertIn(
                "scope-clarification-requests.md", workflow
            )
            self.assertIn(
                '  - "GAP-UI-001 | Какой точный UI-отклик',
                workflow,
            )
            self.assertEqual(1, result["non_blocking_gap_count"])
            self.assertIn(
                "active_transition_prompt: "
                + final_dir.relative_to(ROOT / "fts/AutoFin").as_posix()
                + "/prompt.scope-assertions-to-reviewer.md",
                workflow,
            )
            plan = (final_dir / "package-test-design-plan.md").read_text(encoding="utf-8")
            self.assertIn("initial_state_capture", plan)
            self.assertIn("different-from-captured-initial", plan)
            self.assertIn("Prepare a visibly changed state", plan)
            obligations = (final_dir / "coverage-obligation-table.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("dictionary_coverage", obligations)
            self.assertIn("calibration_status", obligations)
            self.assertIn("DICT-001", obligations)
            candidate_line = next(
                line for line in obligations.splitlines() if "`OBL-001`" in line
            )
            executable_line = next(
                line
                for line in obligations.splitlines()
                if "`OBL-EXEC-001`" in line
            )
            self.assertIn("`ui-calibration-required`", candidate_line)
            self.assertIn("`none`", executable_line)
            ledger = (final_dir / "atomic-requirements-ledger.md").read_text(
                encoding="utf-8"
            )
            atom_line = next(
                line for line in ledger.splitlines() if "`ATOM-001`" in line
            )
            self.assertIn("`covered_with_ui_calibration`", atom_line)
            self.assertIn("`GAP-UI-001`", atom_line)
            gaps = (final_dir / "scope-coverage-gaps.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("### GAP-UI-001", gaps)
            self.assertIn("| impact | non-blocking |", gaps)
            self.assertIn("| source_row_ids | SRC-006 |", gaps)
            self.assertIn("| requirement_codes | BSR 38 |", gaps)
            self.assertIn("Какой точный UI-отклик", gaps)
            clarifications = (
                final_dir / "scope-clarification-requests.md"
            ).read_text(encoding="utf-8")
            self.assertIn("CLR-PENDING-001", clarifications)
            self.assertIn("GAP-UI-001", clarifications)
            self.assertIn("unanswered", clarifications)
            self.assertIn("not-provided", clarifications)
            manifest = json.loads(
                (final_dir / "source-assertions.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                hashlib.sha256(
                    (final_dir / "scope-coverage-gaps.md").read_bytes()
                ).hexdigest(),
                manifest["coverage_gaps_artifact"]["sha256"],
            )
            self.assertTrue((final_dir / "dictionary-inventory.md").is_file())
            self.assertTrue((final_dir / "negative-oracle-inventory.md").is_file())
            self.assertTrue((final_dir / "requiredness-oracle-inventory.md").is_file())

    def test_candidate_without_parent_gap_keeps_calibration_without_constraint(self) -> None:
        context, boundary, design = self._h68_design()
        obligation = design["obligations"][0]
        obligation["scope_obligation_ids"] = ["SO-REQ-001"]
        design["requiredness_oracles"] = [
            {
                "signal_id": "SIG-REQ-001",
                "requirement_codes": ["BSR 38"],
                "scope_obligation_id": "SO-REQ-001",
                "source_row_id": "SRC-006",
                "source_ref": "BSR 38",
                "field_or_block": "Create action",
                "restriction_type": "requiredness",
                "requiredness_source": "Fixture source.",
                "requiredness_class": "marker-only",
                "required_when": "always",
                "marker_oracle_found": "no",
                "empty_value_oracle_found": "no",
                "oracle_source": "not_found",
                "oracle_status": "ui-calibration-required",
                "decision": "candidate_tc_required",
                "planned_tc_or_gap": "candidate:SO-REQ-001",
                "gap_id": "none_required",
                "analyst_question": "Какой точный UI-отклик отображается?",
                "handoff_rule": "Calibrate in UI without inventing the reaction.",
                "calibration_notes": "Статус тест-кейса: candidate-ui-calibration.",
                "linked_atom_id": obligation["linked_atom_id"],
                "linked_obligation_id": obligation["obligation_id"],
            }
        ]
        stage_root = ROOT / "fts/AutoFin/work/stage-handoffs"
        with tempfile.TemporaryDirectory(
            prefix="semantic-candidate-no-gap-", dir=stage_root
        ) as raw:
            final_dir = Path(raw) / "final"
            with (
                patch(
                    "test_case_agent.bounded_scope_materializer.validate_bridge_boundary"
                ),
                patch(
                    "test_case_agent.bounded_scope_materializer.validate_semantic_design_binding",
                    return_value={
                        "version": 1,
                        "status": "verified",
                        "contract": "scope-v2-to-semantic-design-v1",
                    },
                ),
            ):
                result = materialize_semantic_design_bridge(
                    repo_root=ROOT,
                    context=context,
                    scope_boundary_decision=boundary,
                    semantic_design=design,
                    approved_clarifications=(),
                    publication_owner_token=OWNER_TOKEN,
                    handoff_dir=final_dir,
                )

            obligations = (final_dir / "coverage-obligation-table.md").read_text(
                encoding="utf-8"
            )
            candidate_line = next(
                line for line in obligations.splitlines() if "`OBL-001`" in line
            )
            self.assertIn("`ui-calibration-required`", candidate_line)
            ledger = (final_dir / "atomic-requirements-ledger.md").read_text(
                encoding="utf-8"
            )
            atom_line = next(
                line for line in ledger.splitlines() if "`ATOM-001`" in line
            )
            self.assertIn("`covered_with_ui_calibration`", atom_line)
            self.assertIn("`none_required`", atom_line)
            self.assertNotIn("GAP-", atom_line)
            self.assertEqual(0, result["non_blocking_gap_count"])
            self.assertFalse(
                (final_dir / "scope-clarification-requests.md").exists()
            )
            self.assertIn(
                "open_questions: []",
                (final_dir / "workflow-state.yaml").read_text(encoding="utf-8"),
            )

    def test_context_only_boundary_gap_is_preserved_without_fake_test_case(self) -> None:
        context, boundary, design = self._h68_design()
        context_row = next(
            item for item in context["source_rows"] if item["source_row_id"] == "SRC-001"
        )
        boundary["gaps"] = [
            {
                "gap_id": "GAP-CONTEXT-001",
                "gap_type": "ambiguity",
                "source_row_ids": ["SRC-001"],
                "source_refs": [context_row["source_ref"]],
                "exact_source_fragments": ["1."],
                "blocking": False,
                "clarification_question": (
                    "Как трактовать контекстное ограничение для последующего анализа?"
                ),
                "downstream_handling": "carry-to-source-model",
            }
        ]
        stage_root = ROOT / "fts/AutoFin/work/stage-handoffs"
        with tempfile.TemporaryDirectory(
            prefix="semantic-context-gap-", dir=stage_root
        ) as raw:
            final_dir = Path(raw) / "final"
            with (
                patch(
                    "test_case_agent.bounded_scope_materializer.validate_bridge_boundary"
                ),
                patch(
                    "test_case_agent.bounded_scope_materializer.validate_semantic_design_binding",
                    return_value={
                        "version": 1,
                        "status": "verified",
                        "contract": "scope-v2-to-semantic-design-v1",
                    },
                ),
            ):
                result = materialize_semantic_design_bridge(
                    repo_root=ROOT,
                    context=context,
                    scope_boundary_decision=boundary,
                    semantic_design=design,
                    approved_clarifications=(),
                    publication_owner_token=OWNER_TOKEN,
                    handoff_dir=final_dir,
                )

            gaps = (final_dir / "scope-coverage-gaps.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("### GAP-CONTEXT-001", gaps)
            self.assertIn("| affected_assertion_id | ASSERT-CONTEXT-001 |", gaps)
            self.assertIn("| affected_atom_id | ATOM-CONTEXT-001 |", gaps)
            self.assertIn("| execution_atom_ids |  |", gaps)
            self.assertIn("| status | open |", gaps)
            self.assertIn("| resolution | unresolved |", gaps)
            self.assertNotIn("| resolution | none_required |", gaps)
            coverable_section = gaps.split(
                "## Что Можно Покрывать Несмотря На Gaps", 1
            )[1].split("## Что Нельзя Домысливать", 1)[0]
            self.assertIn("не зависящие от открытых GAP", coverable_section)
            self.assertNotIn("Весь scope с учётом", coverable_section)
            clarification_section = gaps.split("## Требуемые Уточнения", 1)[1]
            self.assertIn("`GAP-CONTEXT-001`", clarification_section)
            self.assertIn("scope-clarification-requests.md", clarification_section)
            self.assertNotIn("- none_required", clarification_section)

            ledger = (final_dir / "atomic-requirements-ledger.md").read_text(
                encoding="utf-8"
            )
            context_atom_line = next(
                line
                for line in ledger.splitlines()
                if "`ATOM-CONTEXT-001`" in line
            )
            testable_atom_line = next(
                line for line in ledger.splitlines() if "`ATOM-001`" in line
            )
            self.assertIn("`not-applicable`", context_atom_line)
            self.assertNotIn("GAP-CONTEXT-001", context_atom_line)
            self.assertNotIn("GAP-CONTEXT-001", testable_atom_line)

            obligations = (final_dir / "coverage-obligation-table.md").read_text(
                encoding="utf-8"
            )
            context_obligation_line = next(
                line
                for line in obligations.splitlines()
                if "`OBL-CONTEXT-001`" in line
            )
            self.assertIn("`not-applicable`", context_obligation_line)
            self.assertNotIn("TC-", context_obligation_line)

            plan = (final_dir / "package-test-design-plan.md").read_text(
                encoding="utf-8"
            )
            context_plan_line = next(
                line
                for line in plan.splitlines()
                if "`PD-CONTEXT-001`" in line
            )
            self.assertIn("none_required:not-applicable", context_plan_line)
            self.assertNotIn("TC-", context_plan_line)
            self.assertEqual(1, result["non_blocking_gap_count"])

            clarifications = (
                final_dir / "scope-clarification-requests.md"
            ).read_text(encoding="utf-8")
            self.assertIn("CLR-PENDING-001", clarifications)
            self.assertIn("GAP-CONTEXT-001", clarifications)
            workflow = (final_dir / "workflow-state.yaml").read_text(
                encoding="utf-8"
            )
            self.assertIn("scope_clarification_requests:", workflow)
            self.assertIn("GAP-CONTEXT-001 |", workflow)

    def test_mixed_row_gap_routes_constraint_only_to_testable_atom(self) -> None:
        context, boundary, design = self._h68_design()
        target_design = next(
            item
            for item in design["source_designs"]
            if item["source_row_id"] == "SRC-006"
        )
        context_assertion = copy.deepcopy(target_design["assertions"][0])
        context_assertion.update(
            {
                "assertion_id": "ASSERT-CONTEXT-MIXED-001",
                "canonical_statement": (
                    "Строка содержит дополнительный контекст без отдельного поведения."
                ),
                "polarity": "neutral",
                "semantic_disposition": "not-applicable",
                "execution_readiness": "not-applicable",
                "execution_readiness_rationale": "none_required",
                "condition_clauses": [],
                "action_clauses": [],
                "oracle_clauses": [],
                "requirement_codes": [],
                "requirement_code_evidence": [],
                "clause_evidence": [],
                "atom_id": "ATOM-CONTEXT-MIXED-001",
                "obligation_ids": [],
                "disposition_rationale": (
                    "Контекстное утверждение не формулирует исполнимый результат."
                ),
                "source_property_id": "SRC-006.CONTEXT",
                "field_or_block": "Контекст строки",
                "source_reference": "SRC-006",
            }
        )
        target_design["assertions"].append(context_assertion)
        target_row = next(
            item for item in context["source_rows"] if item["source_row_id"] == "SRC-006"
        )
        boundary["gaps"] = [
            {
                "gap_id": "GAP-MIXED-001",
                "gap_type": "ambiguity",
                "source_row_ids": ["SRC-006"],
                "source_refs": [target_row["source_ref"]],
                "exact_source_fragments": ["BSR 38"],
                "blocking": False,
                "clarification_question": (
                    "Как трактовать общий контекст без расширения testable поведения?"
                ),
                "downstream_handling": "carry-to-source-model",
            }
        ]
        stage_root = ROOT / "fts/AutoFin/work/stage-handoffs"
        with tempfile.TemporaryDirectory(
            prefix="semantic-mixed-gap-", dir=stage_root
        ) as raw:
            final_dir = Path(raw) / "final"
            with (
                patch(
                    "test_case_agent.bounded_scope_materializer.validate_bridge_boundary"
                ),
                patch(
                    "test_case_agent.bounded_scope_materializer.validate_semantic_design_binding",
                    return_value={
                        "version": 1,
                        "status": "verified",
                        "contract": "scope-v2-to-semantic-design-v1",
                    },
                ),
            ):
                result = materialize_semantic_design_bridge(
                    repo_root=ROOT,
                    context=context,
                    scope_boundary_decision=boundary,
                    semantic_design=design,
                    approved_clarifications=(),
                    publication_owner_token=OWNER_TOKEN,
                    handoff_dir=final_dir,
                )

            gaps = (final_dir / "scope-coverage-gaps.md").read_text(
                encoding="utf-8"
            )
            self.assertIn(
                "| affected_assertion_id | ASSERT-001; ASSERT-CONTEXT-MIXED-001 |",
                gaps,
            )
            self.assertIn(
                "| affected_atom_id | ATOM-001; ATOM-CONTEXT-MIXED-001 |",
                gaps,
            )
            ledger = (final_dir / "atomic-requirements-ledger.md").read_text(
                encoding="utf-8"
            )
            testable_line = next(
                line for line in ledger.splitlines() if "`ATOM-001`" in line
            )
            context_line = next(
                line
                for line in ledger.splitlines()
                if "`ATOM-CONTEXT-MIXED-001`" in line
            )
            self.assertIn("`GAP-MIXED-001`", testable_line)
            self.assertNotIn("GAP-MIXED-001", context_line)
            self.assertIn("`not-applicable`", context_line)
            obligations = (final_dir / "coverage-obligation-table.md").read_text(
                encoding="utf-8"
            )
            context_obligation_line = next(
                line
                for line in obligations.splitlines()
                if "ATOM-CONTEXT-MIXED-001" in line
            )
            self.assertNotIn("TC-", context_obligation_line)
            self.assertEqual(1, result["testable_obligation_count"])

    def test_render_failure_removes_staging_and_leaves_no_final(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            final_dir = root / "fts/F/work/stage-handoffs/01-scope"
            context = {"ft_slug": "F"}
            boundary: dict[str, object] = {}
            design = {
                "version": 4,
                "contract": "semantic-design-bridge-v2",
                "status": "ready",
                "blocking_reason": "none_required",
                "scope_summary": "scope",
                "included": [],
                "excluded": [],
                "mockup_locators": [],
                "source_designs": [],
                "obligations": [],
                "applicability": [],
            }

            def fail_after_partial_write(**kwargs):
                (kwargs["handoff_dir"] / "partial.txt").write_text("partial", encoding="utf-8")
                raise RuntimeError("render failed")

            with (
                patch("test_case_agent.bounded_scope_materializer.validate_bridge_boundary"),
                patch(
                    "test_case_agent.bounded_scope_materializer.validate_semantic_design_binding",
                    return_value={"status": "verified"},
                ),
                patch(
                    "test_case_agent.bounded_scope_materializer.materialize_bounded_scope",
                    side_effect=fail_after_partial_write,
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "render failed"):
                    materialize_semantic_design_bridge(
                        repo_root=root,
                        context=context,
                        scope_boundary_decision=boundary,
                        semantic_design=design,
                        approved_clarifications=(),
                        publication_owner_token=OWNER_TOKEN,
                        handoff_dir=final_dir,
                    )

            self.assertFalse(final_dir.exists())
            self.assertFalse(list(final_dir.parent.glob(".01-scope.semantic-stage-*")))

    def test_invalid_ft_slug_is_rejected_before_staging(self) -> None:
        for invalid_slug in ("C:", "../F", "CON", "Demo."):
            with self.subTest(ft_slug=invalid_slug), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                final_dir = root / "fts/F/work/stage-handoffs/01-scope"
                with (
                    patch(
                        "test_case_agent.bounded_scope_materializer.validate_bridge_boundary"
                    ),
                    patch(
                        "test_case_agent.bounded_scope_materializer.validate_semantic_design_binding",
                        return_value={"status": "verified"},
                    ),
                ):
                    with self.assertRaises(BoundedScopeMaterializationError):
                        materialize_semantic_design_bridge(
                            repo_root=root,
                            context={"ft_slug": invalid_slug},
                            scope_boundary_decision={},
                            semantic_design={"version": 3},
                            approved_clarifications=(),
                            publication_owner_token=OWNER_TOKEN,
                            handoff_dir=final_dir,
                        )

                self.assertFalse(final_dir.exists())
                self.assertFalse((root / "fts").exists())

    def test_invalid_publication_owner_token_is_rejected_before_staging(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            final_dir = root / "fts/F/work/stage-handoffs/01-scope"
            with self.assertRaisesRegex(
                BoundedScopeMaterializationError, "UUIDv4"
            ):
                materialize_semantic_design_bridge(
                    repo_root=root,
                    context={"ft_slug": "F"},
                    scope_boundary_decision={},
                    semantic_design={"version": 3},
                    approved_clarifications=(),
                    publication_owner_token="not-a-token",
                    handoff_dir=final_dir,
                )

            self.assertFalse((root / "fts").exists())

    def test_downstream_evidence_preflight_failure_publishes_nothing(self) -> None:
        context, boundary, design = self._h68_design()
        stage_root = ROOT / "fts/AutoFin/work/stage-handoffs"
        with tempfile.TemporaryDirectory(prefix="semantic-preflight-fail-", dir=stage_root) as raw:
            final_dir = Path(raw) / "final"
            with (
                patch(
                    "test_case_agent.bounded_scope_materializer.validate_bridge_boundary"
                ),
                patch(
                    "test_case_agent.bounded_scope_materializer.validate_semantic_design_binding",
                    return_value={"status": "verified"},
                ),
                patch(
                    "scripts.codex_exec_source_assertion_reviewer.prepare_evidence_set",
                    side_effect=RuntimeError("canonical evidence preflight failed"),
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "canonical evidence preflight"):
                    materialize_semantic_design_bridge(
                        repo_root=ROOT,
                        context=context,
                        scope_boundary_decision=boundary,
                        semantic_design=design,
                        approved_clarifications=(),
                        publication_owner_token=OWNER_TOKEN,
                        handoff_dir=final_dir,
                    )

            self.assertFalse(final_dir.exists())
            self.assertFalse(list(final_dir.parent.glob(".final.semantic-stage-*")))

    def test_summary_reporting_failure_preserves_published_handoff(self) -> None:
        context, boundary, design = self._h68_design()
        stage_root = ROOT / "fts/AutoFin/work/stage-handoffs"
        with tempfile.TemporaryDirectory(
            prefix="semantic-summary-fail-", dir=stage_root
        ) as raw:
            root = Path(raw)
            final_dir = root / "final"
            summary = root / "summary.json"
            with (
                patch(
                    "test_case_agent.bounded_scope_materializer.validate_bridge_boundary"
                ),
                patch(
                    "test_case_agent.bounded_scope_materializer.validate_semantic_design_binding",
                    return_value={"status": "verified"},
                ),
                patch(
                    "test_case_agent.bounded_scope_materializer.write_json_fresh",
                    side_effect=RuntimeError("summary write failed"),
                ),
            ):
                result = materialize_semantic_design_bridge(
                    repo_root=ROOT,
                    context=context,
                    scope_boundary_decision=boundary,
                    semantic_design=design,
                    approved_clarifications=(),
                    publication_owner_token=OWNER_TOKEN,
                    handoff_dir=final_dir,
                    success_summary_path=summary,
                )

            self.assertEqual("completed", result["status"])
            self.assertTrue(final_dir.is_dir())
            self.assertFalse(summary.exists())
            self.assertEqual(
                "RuntimeError", result["reporting_error"]["error_type"]
            )
            self.assertFalse(list(root.glob(".final.semantic-stage-*")))

    def test_final_rename_failure_publishes_no_completed_summary(self) -> None:
        context, boundary, design = self._h68_design()
        stage_root = ROOT / "fts/AutoFin/work/stage-handoffs"
        with tempfile.TemporaryDirectory(
            prefix="semantic-rename-fail-", dir=stage_root
        ) as raw:
            root = Path(raw)
            final_dir = root / "final"
            summary = root / "summary.json"
            with (
                patch(
                    "test_case_agent.bounded_scope_materializer.validate_bridge_boundary"
                ),
                patch(
                    "test_case_agent.bounded_scope_materializer.validate_semantic_design_binding",
                    return_value={"status": "verified"},
                ),
                patch(
                    "test_case_agent.bounded_scope_materializer.os.rename",
                    side_effect=RuntimeError("rename failed"),
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "rename failed"):
                    materialize_semantic_design_bridge(
                        repo_root=ROOT,
                        context=context,
                        scope_boundary_decision=boundary,
                        semantic_design=design,
                        approved_clarifications=(),
                        publication_owner_token=OWNER_TOKEN,
                        handoff_dir=final_dir,
                        success_summary_path=summary,
                    )

            self.assertFalse(final_dir.exists())
            self.assertFalse(summary.exists())
            self.assertFalse(list(root.glob(".final.semantic-stage-*")))

    def test_existing_final_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            final_dir = root / "fts/F/work/stage-handoffs/01-scope"
            final_dir.mkdir(parents=True)
            marker = final_dir / "user.txt"
            marker.write_text("keep", encoding="utf-8")
            with (
                patch("test_case_agent.bounded_scope_materializer.validate_bridge_boundary"),
                patch(
                    "test_case_agent.bounded_scope_materializer.validate_semantic_design_binding",
                    return_value={"status": "verified"},
                ),
            ):
                with self.assertRaisesRegex(
                    BoundedScopeMaterializationError, "must not already exist"
                ):
                    materialize_semantic_design_bridge(
                        repo_root=root,
                        context={"ft_slug": "F"},
                        scope_boundary_decision={},
                        semantic_design={"version": 4},
                        approved_clarifications=(),
                        publication_owner_token=OWNER_TOKEN,
                        handoff_dir=final_dir,
                    )
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_cli_exposes_stable_bridge_flags(self) -> None:
        option_strings = {
            option
            for action in parser()._actions
            for option in action.option_strings
        }
        self.assertTrue(
            {
                "--repo-root",
                "--context",
                "--scope-boundary-decision",
                "--semantic-design",
                "--handoff-dir",
                "--publication-owner-token",
                "--summary-output",
            }.issubset(option_strings)
        )

    def test_cli_requires_explicit_publication_owner_token(self) -> None:
        with patch("sys.stderr", io.StringIO()), self.assertRaises(
            SystemExit
        ) as raised:
            parser().parse_args(
                [
                    "--repo-root",
                    ".",
                    "--context",
                    "context.json",
                    "--scope-boundary-decision",
                    "boundary.json",
                    "--semantic-design",
                    "semantic.json",
                    "--handoff-dir",
                    "handoff",
                ]
            )

        self.assertEqual(2, raised.exception.code)

    def test_multiple_clarification_sources_have_one_canonical_companion(self) -> None:
        records = [
            SimpleNamespace(
                clarification_id=f"CLR-00{index}",
                gap_id=f"GAP-00{index}",
                scope_slug="scope",
                requirement_codes=(f"BSR {index}",),
                source_row_ids=(),
                evidence_source_path=f"fts/F/clarification-{index}.md",
                authority="user",
                exact_answer=f"answer {index}",
                response_status="answered",
                response_type="user-confirmed",
                answered_at="2026-07-17",
            )
            for index in (1, 2)
        ]

        content = _render_clarification_requests(
            scope_slug="scope", records=records
        )

        self.assertIn("## Clarification Requests", content)
        self.assertIn("CLR-001", content)
        self.assertIn("CLR-002", content)
        self.assertIn("### CLR-001", content)
        self.assertIn("**Текст из ФТ:**", content)
        self.assertIn("#### Ответ БА (`user_response`)", content)
        self.assertIn("response_status: answered", content)


if __name__ == "__main__":
    unittest.main()
