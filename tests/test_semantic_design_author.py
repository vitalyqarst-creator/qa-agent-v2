from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.codex_exec_bounded_scope_analyzer import (
    StreamingExecResult,
    main as analyzer_main,
)
from scripts.codex_exec_semantic_design_author import main as author_main
from test_case_agent.review_cycle.exec_backend import (
    MODEL_TOOL_ISOLATION_DISABLE_FEATURES,
    ExecCapability,
    ExecCapabilityResolution,
)
from test_case_agent.semantic_design_bridge import (
    APPLICABILITY_DIMENSIONS,
    SEMANTIC_DESIGN_CONTRACT,
    SEMANTIC_DESIGN_VERSION,
    canonical_payload_sha256,
)


class SemanticDesignAuthorTests(unittest.TestCase):
    @staticmethod
    def _bind_context(context: dict[str, object]) -> dict[str, object]:
        payload = copy.deepcopy(context)
        payload.pop("source_cache", None)
        payload.pop("source_row_baseline", None)
        digest = hashlib.sha256(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        context["source_cache"] = {
            "component_digests": {"bounded_context_sha256": digest}
        }
        return context

    @classmethod
    def _context(cls) -> dict[str, object]:
        return cls._bind_context(
            {
                "version": 1,
                "package_id": "WP-01",
                "scope_slug": "open-window",
                "scope_boundary": {
                    "target": "Verify the Open action from BSR 1.",
                    "include": ["Opening the target window."],
                    "exclude": ["All behavior inside the target window."],
                },
                "mockup_locators": [],
                "source_rows": [
                    {
                        "source_row_id": "SRC-001",
                        "field_or_action": "Open action",
                        "source_ref": "BSR 1",
                        "bounded_source_text": (
                            "BSR 1. When the user selects Open, the target window opens."
                        ),
                        "requirement_codes_hint": ["BSR 1"],
                        "in_scope_hint": "yes; target behavior",
                    }
                ],
                "sources": [],
                "scope_execution_facts": {
                    "version": 1,
                    "bounded_scope_kind": "single-section",
                    "expected_testable_assertion_count": 1,
                    "expected_tc_count": 1,
                    "internal_package_count": 1,
                    "has_heterogeneous_integrations": False,
                    "has_large_dictionary": False,
                    "mockups_ready": True,
                },
            }
        )

    @classmethod
    def _boundary(cls, context: dict[str, object]) -> dict[str, object]:
        return {
            "version": 2,
            "status": "ready",
            "blocking_reason": "none_required",
            "scope_summary": "Verify the observable window opening required by BSR 1.",
            "scope_boundary": copy.deepcopy(context["scope_boundary"]),
            "source_decisions": [
                {
                    "source_row_id": "SRC-001",
                    "disposition": "included",
                    "requirement_codes": ["BSR 1"],
                    "rationale": "The row contains the selected action and its observable result.",
                }
            ],
            "dependencies": [],
            "gaps": [],
            "mockup_locators": [],
        }

    @classmethod
    def _design(
        cls,
        context: dict[str, object],
        boundary: dict[str, object],
    ) -> dict[str, object]:
        source_text = str(context["source_rows"][0]["bounded_source_text"])
        assertion = {
            "assertion_id": "ASSERT-001",
            "canonical_statement": "Selecting Open causes the target window to open.",
            "polarity": "positive",
            "semantic_disposition": "testable",
            "execution_readiness": "ready",
            "execution_readiness_rationale": "none_required",
            "risk": "medium",
            "condition_clauses": [],
            "action_clauses": ["Select Open."],
            "oracle_clauses": ["The target window opens."],
            "requirement_codes": ["BSR 1"],
            "requirement_code_evidence": [
                {
                    "requirement_code": "BSR 1",
                    "source_row_id": "SRC-001",
                    "provenance_role": "xhtml-row",
                    "exact_source_fragment": source_text,
                    "evidence_source_path": "none_required",
                    "evidence_locator": "none_required",
                }
            ],
            "clause_evidence": [
                {
                    "clause_kind": "action",
                    "clause_index": 0,
                    "source_row_id": "SRC-001",
                    "exact_source_fragment": source_text,
                },
                {
                    "clause_kind": "oracle",
                    "clause_index": 0,
                    "source_row_id": "SRC-001",
                    "exact_source_fragment": source_text,
                },
            ],
            "supporting_source_bindings": [],
            "clarification_clause_bindings": [],
            "atom_id": "ATOM-001",
            "obligation_ids": ["OBL-001"],
            "disposition_rationale": "The selected behavior is directly observable.",
            "source_property_id": "PROP-001",
            "field_or_block": "Open action",
            "source_reference": "BSR 1",
        }
        obligation = {
            "obligation_id": "OBL-001",
            "package_id": "WP-01",
            "linked_atom_id": "ATOM-001",
            "source_property_id": "PROP-001",
            "property_type": "observable-behavior",
            "obligation_class": "positive-action",
            "required_behavior": "The target window opens after selecting Open.",
            "source_ref": "BSR 1",
            "planned_tc_id": "TC-001",
            "review_notes": "none_required",
            "design_dimension": "scenario-use-case",
            "planned_check": "Select Open and observe the target window.",
            "check_type": "action-flow",
            "coverage_class": "positive",
            "input_class": "valid-user-action",
            "single_expected_behavior": "The target window is open.",
            "oracle_source": "BSR 1",
            "test_data": "none_required",
            "dictionary_refs": [],
            "dictionary_coverage": "none_required",
            "scope_obligation_ids": [],
        }
        applicability = []
        for dimension in APPLICABILITY_DIMENSIONS:
            applicable = dimension in {"scenario-use-case", "traceability"}
            applicability.append(
                {
                    "dimension": dimension,
                    "applicable": "yes" if applicable else "no",
                    "source_ref": "BSR 1" if applicable else "none_required",
                    "reason": (
                        "The requirement and planned check have an explicit link."
                        if applicable
                        else "No source evidence makes this dimension applicable."
                    ),
                    "linked_atoms": ["ATOM-001"] if applicable else [],
                    "linked_test_cases": ["TC-001"] if applicable else [],
                }
            )
        return {
            "version": SEMANTIC_DESIGN_VERSION,
            "contract": SEMANTIC_DESIGN_CONTRACT,
            "status": "ready",
            "blocking_reason": "none_required",
            "prepared_context_sha256": context["source_cache"][
                "component_digests"
            ]["bounded_context_sha256"],
            "scope_boundary_decision_sha256": canonical_payload_sha256(boundary),
            "scope_summary": boundary["scope_summary"],
            "included": copy.deepcopy(context["scope_boundary"]["include"]),
            "excluded": copy.deepcopy(context["scope_boundary"]["exclude"]),
            "mockup_locators": [],
            "source_designs": [
                {
                    "source_row_id": "SRC-001",
                    "boundary_disposition": "included",
                    "requirement_codes": ["BSR 1"],
                    "assertions": [assertion],
                }
            ],
            "obligations": [obligation],
            "reset_lifecycle_bindings": [],
            "dependency_bindings": [],
            "dictionaries": [],
            "negative_oracles": [],
            "requiredness_oracles": [],
            "applicability": applicability,
        }

    @staticmethod
    def _resolution(root: Path) -> ExecCapabilityResolution:
        capability = ExecCapability(
            command="mock-codex",
            available=True,
            verified=True,
            returncode=0,
            duration_ms=1,
            missing_flags=(),
            version="codex-cli test",
            resolved_command=str((root / "mock-codex.exe").resolve()),
        )
        return ExecCapabilityResolution(
            requested_command="mock-codex",
            probes=(capability,),
            selected=capability,
            disable_features=MODEL_TOOL_ISOLATION_DISABLE_FEATURES,
        )

    @staticmethod
    def _execution() -> StreamingExecResult:
        return StreamingExecResult(
            return_code=0,
            timed_out=False,
            tool_event_count=0,
            event_line_count=4,
            usage={"input_tokens": 120, "output_tokens": 80},
            process_spawn_ms=1,
            process_spawn_count=1,
            process_exit_ms=6,
            thread_started_ms=2,
            thread_started_count=1,
            turn_started_ms=3,
            turn_started_count=1,
            model_result_received_ms=4,
            model_result_count=1,
            turn_completed_ms=5,
            turn_completed_count=1,
        )

    @staticmethod
    def _arguments(root: Path) -> list[str]:
        return [
            "--context",
            str(root / "context.json"),
            "--scope-boundary-decision",
            str(root / "boundary.json"),
            "--decision-output",
            str(root / "design.json"),
            "--events-output",
            str(root / "events.ndjson"),
            "--stderr-output",
            str(root / "stderr.txt"),
            "--summary-output",
            str(root / "summary.json"),
            "--schema-output",
            str(root / "schema.json"),
            "--contract-version",
            "1",
            "--scope-execution-profile",
            "standard-production",
            "--codex-command",
            "mock-codex",
        ]

    def _write_inputs(
        self,
        root: Path,
    ) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        context = self._context()
        boundary = self._boundary(context)
        design = self._design(context, boundary)
        (root / "context.json").write_text(
            json.dumps(context, ensure_ascii=False), encoding="utf-8"
        )
        (root / "boundary.json").write_text(
            json.dumps(boundary, ensure_ascii=False), encoding="utf-8"
        )
        return context, boundary, design

    def test_standard_bridge_runs_exactly_one_model_attempt_without_retry(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _context, _boundary, design = self._write_inputs(root)
            captured: dict[str, object] = {}

            def execute(*_args, **kwargs):
                captured["prompt"] = kwargs["prompt"]
                (root / "design.json").write_text(
                    json.dumps(design, ensure_ascii=False), encoding="utf-8"
                )
                return self._execution()

            with (
                patch(
                    "scripts.codex_exec_bounded_scope_analyzer."
                    "resolve_verified_exec_capability",
                    return_value=self._resolution(root),
                ),
                patch(
                    "scripts.codex_exec_bounded_scope_analyzer.run_exec_streaming",
                    side_effect=execute,
                ) as run_model,
            ):
                code = analyzer_main(self._arguments(root))
            summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
            schema = json.loads((root / "schema.json").read_text(encoding="utf-8"))

        self.assertEqual(0, code)
        run_model.assert_called_once()
        self.assertIn("authoritative_scope_boundary_v2", str(captured["prompt"]))
        self.assertEqual("standard-semantic-design-author", summary["execution_route"])
        self.assertEqual("verified", summary["semantic_design_bridge"]["status"])
        self.assertEqual(1, summary["assertion_count"])
        self.assertEqual(1, summary["obligation_count"])
        self.assertEqual(1, summary["lifecycle"]["runner_attempt_count"])
        self.assertEqual(0, summary["lifecycle"]["runner_retry_count"])
        self.assertIn("source_designs", schema["properties"])
        self.assertNotIn("source_decisions", schema["properties"])
        requirement_binding = schema["properties"]["source_designs"]["items"][
            "properties"
        ]["assertions"]["items"]["properties"]["requirement_code_evidence"][
            "items"
        ]
        self.assertEqual("string", requirement_binding["properties"]["provenance_role"]["type"])
        self.assertEqual(
            ["xhtml-row", "pdf-parity"],
            requirement_binding["properties"]["provenance_role"]["enum"],
        )
        self.assertEqual("string", requirement_binding["properties"]["evidence_source_path"]["type"])
        self.assertEqual("string", requirement_binding["properties"]["evidence_locator"]["type"])
        self.assertIn("provenance_role=pdf-parity", str(captured["prompt"]))
        self.assertIn("never emit JSON null", str(captured["prompt"]))

    def test_bad_authoritative_boundary_fails_before_model(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _context, boundary, _design = self._write_inputs(root)
            boundary["source_decisions"][0]["requirement_codes"] = []
            (root / "boundary.json").write_text(
                json.dumps(boundary, ensure_ascii=False), encoding="utf-8"
            )
            with patch(
                "scripts.codex_exec_bounded_scope_analyzer.run_exec_streaming"
            ) as run_model:
                code = analyzer_main(self._arguments(root))
            summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))

        self.assertEqual(2, code)
        run_model.assert_not_called()
        self.assertEqual("scope-boundary-binding", summary["error_stage"])
        self.assertEqual("input-contract", summary["error_category"])
        self.assertFalse(summary["model_invoked"])
        self.assertEqual(0, summary["lifecycle"]["runner_attempt_count"])

    def test_semantic_input_defect_fails_before_backend_and_model(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            context, _boundary, _design = self._write_inputs(root)
            context["source_table_column_semantics"] = [
                {
                    "table_id": "INCOMPLETE-TABLE",
                    "header_source_row_id": "SRC-001",
                    "target_source_row_ids": ["SRC-001"],
                    "columns": [
                        {
                            "property": "requiredness",
                            "physical_column_index": 2,
                            "expected_header": "O",
                            "value_mapping": {"yes": "required"},
                            "interpretation_source": "source/notes.md",
                            "interpretation_source_fragment": "O means required",
                        }
                    ],
                }
            ]
            self._bind_context(context)
            (root / "context.json").write_text(
                json.dumps(context, ensure_ascii=False), encoding="utf-8"
            )
            arguments = [
                *self._arguments(root),
                "--preflight-output",
                str(root / "preflight.json"),
            ]
            with (
                patch(
                    "scripts.codex_exec_bounded_scope_analyzer."
                    "resolve_verified_exec_capability"
                ) as resolve_backend,
                patch(
                    "scripts.codex_exec_bounded_scope_analyzer.run_exec_streaming"
                ) as run_model,
            ):
                code = analyzer_main(arguments)
            summary = json.loads(
                (root / "summary.json").read_text(encoding="utf-8")
            )
            preflight = json.loads(
                (root / "preflight.json").read_text(encoding="utf-8")
            )

        self.assertEqual(2, code)
        resolve_backend.assert_not_called()
        run_model.assert_not_called()
        self.assertEqual("semantic-input-preflight", summary["error_stage"])
        self.assertEqual("input-contract", summary["error_category"])
        self.assertFalse(summary["model_invoked"])
        self.assertEqual(0, summary["lifecycle"]["runner_attempt_count"])
        self.assertEqual("failed", preflight["semantic_input"]["status"])
        self.assertIn(
            "prepared field-property coverage",
            preflight["semantic_input"]["error"],
        )

    def test_unknown_bridge_fields_are_terminal_without_retry(self) -> None:
        for location in ("root", "nested"):
            with self.subTest(location=location), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                _context, _boundary, design = self._write_inputs(root)
                if location == "root":
                    design["unexpected_root"] = "reject"
                else:
                    design["source_designs"][0]["assertions"][0][
                        "unexpected_nested"
                    ] = "reject"

                def execute(*_args, **_kwargs):
                    (root / "design.json").write_text(
                        json.dumps(design, ensure_ascii=False), encoding="utf-8"
                    )
                    return self._execution()

                with (
                    patch(
                        "scripts.codex_exec_bounded_scope_analyzer."
                        "resolve_verified_exec_capability",
                        return_value=self._resolution(root),
                    ),
                    patch(
                        "scripts.codex_exec_bounded_scope_analyzer.run_exec_streaming",
                        side_effect=execute,
                    ) as run_model,
                ):
                    code = analyzer_main(self._arguments(root))
                summary = json.loads(
                    (root / "summary.json").read_text(encoding="utf-8")
                )

                self.assertEqual(2, code)
                run_model.assert_called_once()
                self.assertEqual("result-contract", summary["error_category"])
                self.assertEqual("result-validate", summary["error_stage"])
                self.assertEqual(1, summary["lifecycle"]["runner_attempt_count"])
                self.assertEqual(0, summary["lifecycle"]["runner_retry_count"])

    def test_thin_author_cli_forces_stable_standard_bridge_route(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            arguments = [
                "--repo-root",
                str(root),
                "--context",
                str(root / "context.json"),
                "--scope-boundary-decision",
                str(root / "boundary.json"),
                "--decision-output",
                str(root / "design.json"),
                "--events-output",
                str(root / "events.ndjson"),
                "--stderr-output",
                str(root / "stderr.txt"),
                "--summary-output",
                str(root / "summary.json"),
                "--schema-output",
                str(root / "schema.json"),
                "--preflight-output",
                str(root / "preflight.json"),
                "--terminal-receipt-output",
                str(root / "terminal.json"),
                "--scope-execution-profile-output",
                str(root / "profile.json"),
                "--backend-selection-output",
                str(root / "backend.json"),
                "--measurement-mode",
                "observational",
                "--no-timeout",
            ]
            with patch(
                "scripts.codex_exec_semantic_design_author.run_scope_analyzer",
                return_value=0,
            ) as run_analyzer:
                code = author_main(arguments)

        self.assertEqual(0, code)
        run_analyzer.assert_called_once()
        forwarded = run_analyzer.call_args.args[0]
        self.assertEqual("1", forwarded[forwarded.index("--contract-version") + 1])
        self.assertEqual(
            "standard-production",
            forwarded[forwarded.index("--scope-execution-profile") + 1],
        )
        self.assertIn("--scope-boundary-decision", forwarded)
        self.assertEqual(str(root), forwarded[forwarded.index("--repo-root") + 1])
        self.assertIn("--no-timeout", forwarded)


if __name__ == "__main__":
    unittest.main()
