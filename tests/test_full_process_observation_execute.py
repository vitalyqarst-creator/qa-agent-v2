from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import run_standard_production_iteration, start_full_process_observation
from test_case_agent.lean_production import (
    finish_phase,
    load_run,
    start_phase,
    start_run,
)
from test_case_agent.review_cycle.source_assertions import (
    MANIFEST_VERSION,
    RegisteredArtifact,
    RegisteredSource,
    SourceAssertion,
    SourceAssertionManifest,
    SourceRow,
)
from test_case_agent.review_cycle.source_row_baseline import (
    SourceRowExtractionSpec,
    build_source_row_baseline,
)
from test_case_agent.semantic_design_bridge import (
    load_approved_clarifications,
    prepared_context_sha256,
)
from test_case_agent.source_preparation import prepare_bounded_scope_context


XHTML_OPEN = '<html xmlns="http://www.w3.org/1999/xhtml"><body>'
XHTML_CLOSE = "</body></html>"


def _seam_source_manifest() -> SourceAssertionManifest:
    source_path = "fts/Demo/source/v1/main.xhtml"
    source_text = "Bound source context"
    row = SourceRow(
        source_row_id="SRC-001",
        source_path=source_path,
        source_locator="/*/*[1]",
        bounded_source_text=source_text,
        source_context_class="ancestor-and-section-preamble",
        candidate_id=f"SRC-CAND-{'1' * 24}",
    )
    assertion = SourceAssertion(
        assertion_id="ASSERT-001",
        source_path=source_path,
        source_context_class="ancestor-and-section-preamble",
        locator="/*/*[1]",
        exact_source_text=source_text,
        canonical_statement="Structural context is not executable.",
        polarity="neutral",
        semantic_disposition="not-applicable",
        execution_readiness="not-applicable",
        execution_readiness_rationale="none_required",
        risk="low",
        condition_clauses=(),
        action_clauses=(),
        oracle_clauses=(),
        requirement_codes=(),
        requirement_code_bindings=(),
        clause_evidence_bindings=(),
        source_row_id="SRC-001",
        atom_id="ATOM-001",
        obligation_ids=(),
        execution_dependency_gap_ids=(),
        primary_gap_id=None,
        disposition_rationale="Structural context only.",
    )
    return SourceAssertionManifest(
        version=MANIFEST_VERSION,
        scope_slug="demo-scope",
        source_row_extraction_spec_digest="1" * 64,
        source_row_baseline_digest="2" * 64,
        source_row_candidate_count=1,
        coverage_gaps_artifact=RegisteredArtifact(
            path="coverage-gaps.md", sha256="3" * 64
        ),
        sources=(RegisteredSource(path=source_path, sha256="4" * 64),),
        source_rows=(row,),
        assertions=(assertion,),
    )


class FullProcessObservationExecuteTests(unittest.TestCase):
    @staticmethod
    def _sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @classmethod
    def _fixture(
        cls,
        root: Path,
        *,
        schema_version: int = 2,
        blocking_dependency: bool = False,
    ) -> Path:
        ft_root = root / "fts" / "Demo"
        source_root = ft_root / "source" / "v1"
        source_root.mkdir(parents=True)
        docx = source_root / "main.docx"
        xhtml = source_root / "main.xhtml"
        pdf = source_root / "main.pdf"
        docx.write_bytes(b"docx")
        pdf.write_bytes(b"pdf")
        target_requirement = (
            "BSR 7. Система использует поле «Внешнее поле»."
            if blocking_dependency
            else "BSR 7. Система открывает форму."
        )
        xhtml.write_text(
            XHTML_OPEN
            + f"<section><p>Контекст</p><p>{target_requirement}</p></section>"
            + XHTML_CLOSE,
            encoding="utf-8",
        )
        notes = ft_root / "AGENT-NOTES.md"
        notes.parent.mkdir(parents=True, exist_ok=True)
        notes.write_text("package notes\n", encoding="utf-8")
        mockup = ft_root / "mockups" / "v1" / "screen.png"
        mockup.parent.mkdir(parents=True)
        mockup.write_bytes(b"image")

        profile_root = root / "evals" / "configs" / "demo-scope"
        profile_root.mkdir(parents=True)
        spec_path = profile_root / "source-row-extraction-spec.json"
        spec_payload = {
            "version": 1,
            "scope_slug": "demo-scope",
            "selected_xhtml": {
                "relative_path": "fts/Demo/source/v1/main.xhtml",
                "sha256": cls._sha256(xhtml),
            },
            "namespaces": {"xhtml": "http://www.w3.org/1999/xhtml"},
            "regions": [
                {
                    "region_id": "REG-SCOPE",
                    "source_context_class": "scope-local",
                    "selector": {
                        "kind": "container",
                        "container_xpath": "/xhtml:html/xhtml:body/xhtml:section[1]",
                    },
                }
            ],
        }
        spec_path.write_text(
            json.dumps(spec_payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        baseline = build_source_row_baseline(
            repo_root=root, spec=SourceRowExtractionSpec.from_dict(spec_payload)
        )
        target = baseline.candidates[-1]
        rows = []
        for index, candidate in enumerate(baseline.candidates, start=1):
            is_target = candidate == target
            rows.append(
                {
                    "source_row_id": f"SRC-{index:03d}",
                    "field_or_action": "Открытие формы" if is_target else "Контекст",
                    "source_ref": "BSR 7" if is_target else "section",
                    "source_path": "fts/Demo/source/v1/main.xhtml",
                    "source_locator": candidate.canonical_xpath,
                    "bounded_source_text": candidate.bounded_source_text,
                    "source_context_class": candidate.source_context_class,
                    "candidate_id": candidate.candidate_id,
                    "requirement_codes_hint": ["BSR 7"] if is_target else [],
                    "in_scope_hint": "yes; target" if is_target else "no; context",
                }
            )
        context = {
            "version": 1,
            "ft_slug": "Demo",
            "scope_slug": "demo-scope",
            "section_id": "1",
            "package_id": "WP-01",
            "request_summary": "Source-only configured scope.",
            "canonical_test_cases": "test-cases/1-demo-scope.md",
            "main_ft_docx": "fts/Demo/source/v1/main.docx",
            "main_ft_xhtml": "fts/Demo/source/v1/main.xhtml",
            "main_ft_pdf": "fts/Demo/source/v1/main.pdf",
            "package_notes": "fts/Demo/AGENT-NOTES.md",
            "source_row_extraction_spec": (
                "evals/configs/demo-scope/source-row-extraction-spec.json"
            ),
            "sources": [
                {
                    "path": "fts/Demo/source/v1/main.docx",
                    "role": "main-ft-docx",
                    "manifest_binding": "semantic-source-of-truth",
                },
                {
                    "path": "fts/Demo/source/v1/main.xhtml",
                    "role": "main-ft-xhtml",
                    "manifest_binding": "assertion-source",
                },
                {
                    "path": "fts/Demo/source/v1/main.pdf",
                    "role": "main-ft-pdf",
                    "manifest_binding": "structural-visual-parity",
                },
                {
                    "path": "fts/Demo/AGENT-NOTES.md",
                    "role": "mandatory-package-context",
                    "manifest_binding": "supporting-material",
                },
            ],
            "mockups": [
                {
                    "path": "fts/Demo/mockups/v1/screen.png",
                    "role": "mockup",
                    "manifest_binding": "mockup",
                }
            ],
            "mockup_locators": ["Figure 1: form"],
            "scope_boundary": {
                "target": "Открытие формы",
                "include": ["BSR 7"],
                "exclude": ["Другие разделы"],
            },
            "dependency_gap_gate": True,
            "dependency_aliases": {},
            "scope_execution_facts": {
                "version": 1,
                "bounded_scope_kind": "contiguous-bounded-fragment",
                "expected_testable_assertion_count": None,
                "expected_tc_count": None,
                "internal_package_count": 1,
                "has_heterogeneous_integrations": False,
                "has_large_dictionary": False,
                "mockups_ready": True,
                "standard_profile_reasons": ["configured standard test route"],
            },
            "source_rows": rows,
            "parity": [
                {
                    "requirement_code": "BSR 7",
                    "docx_locator": "table:1/row:1",
                    "xhtml_locator": target.canonical_xpath,
                    "pdf_locator": "page:1",
                    "status": "matched",
                }
            ],
        }
        template = profile_root / "bounded-context-template.json"
        template.write_text(
            json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        scripts = root / "scripts"
        scripts.mkdir()
        (scripts / "workflow_wall_clock.py").write_text("# recorder\n", encoding="utf-8")
        (scripts / "run_standard_production_iteration.py").write_text(
            "# wrapper\n", encoding="utf-8"
        )
        config = root / "evals" / "configs" / "demo.json"
        payload = {
            "schema_version": schema_version,
            "benchmark_id": "demo-scope",
            "ft_root": "fts/Demo",
            "ft_slug": "Demo",
            "scope_slug": "demo-scope",
            "source_files": [
                "source/v1/main.docx",
                "source/v1/main.xhtml",
                "source/v1/main.pdf",
            ],
            "scope_inputs": [
                {
                    "path": "AGENT-NOTES.md",
                    "role": "mandatory-package-context",
                    "manifest_binding": "supporting-material",
                },
                {
                    "path": "mockups/v1/screen.png",
                    "role": "mockup",
                    "manifest_binding": "mockup",
                },
            ],
            "observation_root": "work/full-process-observation",
            "recorder_entrypoint": "scripts/workflow_wall_clock.py",
            "production_wrapper": "scripts/run_standard_production_iteration.py",
            "measurement_mode": "observational",
        }
        if schema_version == 2:
            expected_sha256 = {
                path.resolve().relative_to(root.resolve()).as_posix(): cls._sha256(path)
                for path in (docx, xhtml, pdf, notes, mockup, template, spec_path)
            }
            payload.update(
                {
                    "expected_sha256": expected_sha256,
                    "source_preparation": {
                        "context_template": (
                            "evals/configs/demo-scope/bounded-context-template.json"
                        ),
                        "cache_dir": ".codex-temp/source-preparation-cache",
                    },
                    "outputs": {
                        "handoff_dir": "work/stage-handoffs/01-demo-scope",
                        "cycle_dir": "work/review-cycles/demo-scope-run",
                        "final_artifact": "test-cases/1-demo-scope.md",
                    },
                }
            )
        config.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return config

    @staticmethod
    def _starter(mutate_after_receipt=None):
        def start(plan):
            def recorder(command, **_):
                start_run(
                    Path(command[command.index("--output") + 1]),
                    ft_slug=plan.ft_slug,
                    scope_slug=plan.scope_slug,
                    profile="current-full-process-observation",
                    request_started_epoch_ms=plan.request_started_epoch_ms,
                    measurement_mode="observational",
                    request_start_source="codex-request-metadata",
                    request_start_precision_ms=1,
                    codex_turn_id=plan.codex_turn_id,
                    end_anchor="pre-final-response",
                    initial_phase="routing-preflight",
                )
                return subprocess.CompletedProcess(command, 0, "{}", "")

            with patch(
                "scripts.start_full_process_observation.subprocess.run",
                side_effect=recorder,
            ):
                receipt = start_full_process_observation.start_observation(plan)
            if mutate_after_receipt is not None:
                mutate_after_receipt(plan)
            return receipt

        return start

    @staticmethod
    def _argument(arguments, option):
        return Path(arguments[arguments.index(option) + 1])

    def test_execute_uses_real_preparation_and_invokes_wrapper_once(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = self._fixture(root)
            plan = start_full_process_observation.resolve_plan(
                repo_root=root,
                config_path=config,
                request_started_epoch_ms=1,
                codex_turn_id="turn-success",
            )
            calls = []

            def production(arguments):
                calls.append(list(arguments))
                context = self._argument(arguments, "--context")
                self.assertTrue(context.is_file())
                prepared = json.loads(context.read_text(encoding="utf-8"))
                self.assertIn("source_cache", prepared)
                images = [
                    Path(arguments[index + 1]).resolve()
                    for index, value in enumerate(arguments)
                    if value == "--image"
                ]
                self.assertEqual(
                    [item.path for item in plan.scope_inputs if item.role == "mockup"],
                    images,
                )
                plan.handoff_dir.mkdir(parents=True)
                plan.cycle_dir.mkdir(parents=True)
                plan.final_artifact.parent.mkdir(parents=True, exist_ok=True)
                plan.final_artifact.write_text(
                    "# Cases\n\n## TC-DEMO-001\n\n## TC-DEMO-002\n",
                    encoding="utf-8",
                )
                plan.runtime_dir.mkdir(parents=True, exist_ok=True)
                (plan.runtime_dir / "standard-production-iteration-summary.json").write_text(
                    json.dumps({"status": "completed", "return_code": 0}),
                    encoding="utf-8",
                )
                return 0

            result = start_full_process_observation.execute_observation(
                plan,
                observation_starter=self._starter(),
                production_runner=production,
            )

            self.assertEqual("signed-off", result["status"], result)
            self.assertEqual(2, result["test_case_count"])
            self.assertEqual(1, len(calls))
            self.assertEqual(1, result["production"]["invocation_count"])
            self.assertEqual("pending", result["post_turn_reconciliation"]["status"])
            timer = load_run(plan.timer)
            self.assertEqual("signed-off", timer["status"])
            self.assertEqual(
                [
                    "routing-preflight",
                    "source-selection",
                    "source-preparation",
                    "final-reporting",
                ],
                [item["phase"] for item in timer["phases"]],
            )
            self.assertEqual(
                "production.checked_in_observation",
                timer["phases"][0]["metrics"]["route_id"],
            )
            breakdown = timer["phases"][0]["metrics"][
                "routing_preflight_breakdown"
            ]
            self.assertEqual(10, len(breakdown))
            self.assertIn(
                "command-preparation",
                {item["component"] for item in breakdown},
            )
            other = next(
                item
                for item in breakdown
                if item["component"] == "other-orchestration"
            )
            self.assertEqual("unavailable", other["duration_ms"])
            self.assertEqual("pending-residual", other["status"])
            self.assertTrue(plan.execution_summary.is_file())
            timing_report = json.loads(
                (plan.run_dir / "workflow-timing-report.json").read_text(
                    encoding="utf-8"
                )
            )
            reconciled_routing = timing_report["phases"][0][
                "routing_preflight_breakdown"
            ]
            self.assertTrue(reconciled_routing["reconciled"])
            reconciled_other = next(
                item
                for item in reconciled_routing["components"]
                if item["component"] == "other-orchestration"
            )
            self.assertEqual("residual-measured", reconciled_other["status"])
            self.assertTrue(
                (plan.run_dir / "workflow-timing-report.md").is_file()
            )

    def test_execute_seam_uses_real_standard_wrapper_and_caller_timer(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            plan = start_full_process_observation.resolve_plan(
                repo_root=root,
                config_path=self._fixture(root),
                request_started_epoch_ms=1,
                codex_turn_id="turn-real-wrapper-seam",
            )
            calls = []

            def value(arguments, option):
                return arguments[arguments.index(option) + 1]

            def complete_phase(timer, phase, metrics=None):
                start_phase(timer, phase=phase)
                finish_phase(
                    timer,
                    phase=phase,
                    status="completed",
                    metrics=metrics or {},
                )

            def bridge(arguments):
                actual = list(arguments or [])
                calls.append(("bridge", actual))
                timer = Path(value(actual, "--timer"))
                for phase in ("scope-analysis", "semantic-design"):
                    complete_phase(
                        timer,
                        phase,
                        {
                            "stage_summary": {
                                "status": "completed",
                                "decision": "ready",
                                "lifecycle": {
                                    "runner_attempt_count": 1,
                                    "runner_retry_count": 0,
                                },
                            }
                        },
                    )
                complete_phase(timer, "scope-materialization")

                handoff = Path(value(actual, "--handoff-dir"))
                handoff.mkdir(parents=True)
                boundary = handoff / "scope-boundary-decision.json"
                boundary.write_text(
                    json.dumps({"version": 2, "status": "ready"}),
                    encoding="utf-8",
                )
                semantic = handoff / "semantic-design.json"
                semantic.write_text(
                    json.dumps(
                        {
                            "status": "ready",
                            "obligations": [
                                {"obligation_id": "OBL-001", "package_id": "WP-01"}
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                (handoff / "workflow-state.yaml").write_text(
                    "ft_slug: Demo\n"
                    "latest_artifacts:\n"
                    "  source_assertion_review: work/stage-handoffs/01-demo-scope/source-assertion-review.json\n",
                    encoding="utf-8",
                )
                manifest = _seam_source_manifest()
                (handoff / "source-assertions.json").write_text(
                    json.dumps(manifest.to_dict()), encoding="utf-8"
                )
                context = json.loads(
                    Path(value(actual, "--context")).read_text(encoding="utf-8")
                )
                publication = {
                    "status": "atomic-renamed",
                    "final_handoff": "fts/Demo/work/stage-handoffs/01-demo-scope",
                }
                readiness = {
                    "status": "passed",
                    "canonical_preflight": "source-reviewer.prepare_evidence_set",
                    "published_manifest_digest": manifest.digest,
                }
                owner = value(actual, "--publication-owner-token")
                (handoff / "semantic-design-bridge-receipt.json").write_text(
                    json.dumps(
                        {
                            "version": 1,
                            "contract": "scope-v2-to-semantic-design-v1",
                            "status": "verified",
                            "materialization_status": "materialized",
                            "prepared_context_sha256": prepared_context_sha256(context),
                            "publication_ownership_contract_version": 1,
                            "publication_owner_token": owner,
                            "source_assertion_manifest_digest": manifest.digest,
                            "scope_boundary_artifact_sha256": self._sha256(boundary),
                            "semantic_design_artifact_sha256": self._sha256(semantic),
                            "publication": publication,
                            "downstream_evidence_readiness": readiness,
                        }
                    ),
                    encoding="utf-8",
                )
                summary = Path(value(actual, "--summary-output"))
                summary.parent.mkdir(parents=True, exist_ok=True)
                summary.write_text(
                    json.dumps(
                        {
                            "status": "completed",
                            "return_code": 0,
                            "attempt_count": 2,
                            "retry_count": 0,
                            "publication_owner_token": owner,
                            "scope_materialization": {
                                "status": "completed",
                                "publication": publication,
                                "downstream_evidence_readiness": readiness,
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                return 0

            def downstream(arguments):
                actual = list(arguments or [])
                calls.append(("downstream", actual))
                timer = Path(value(actual, "--timer"))
                cycle = Path(value(actual, "--cycle-dir"))
                cycle.mkdir(parents=True)
                source_summary = {"status": "completed", "attempt_count": 1}
                (cycle / "source-review-summary.json").write_text(
                    json.dumps(source_summary), encoding="utf-8"
                )
                workflow_state = Path(value(actual, "--workflow-state"))
                (workflow_state.parent / "source-assertion-review.json").write_text(
                    json.dumps({"status": "passed"}), encoding="utf-8"
                )
                stage_metrics = [
                    {
                        "stage_id": "writer-r1",
                        "attempt_id": "attempt-001",
                        "role": "writer",
                    },
                    {
                        "stage_id": "reviewer-r1",
                        "attempt_id": "attempt-001",
                        "role": "reviewer",
                    },
                ]
                for metric in stage_metrics:
                    path = (
                        cycle
                        / "attempts"
                        / metric["stage_id"]
                        / metric["attempt_id"]
                        / "metrics.json"
                    )
                    path.parent.mkdir(parents=True)
                    path.write_text(json.dumps(metric), encoding="utf-8")
                complete_phase(timer, "source-review", {"summary": source_summary})
                complete_phase(timer, "compile-preflight")
                complete_phase(
                    timer,
                    "writer-reviewer",
                    {"stage_metrics": stage_metrics},
                )
                complete_phase(timer, "promotion")
                final = Path(value(actual, "--final-artifact"))
                final.parent.mkdir(parents=True, exist_ok=True)
                final.write_text("# Cases\n\n## TC-DEMO-001\n", encoding="utf-8")
                return 0

            wrapper_calls = []
            wrapper_summaries = []
            bridge_errors = []

            def bridge_capture(arguments):
                try:
                    return bridge(arguments)
                except Exception as exc:
                    bridge_errors.append(repr(exc))
                    raise

            def production(arguments):
                wrapper_calls.append(list(arguments))
                with patch.object(
                    run_standard_production_iteration, "_print_best_effort"
                ):
                    code = run_standard_production_iteration.main(
                        arguments,
                        bridge_runner=bridge_capture,
                        downstream_runner=downstream,
                    )
                wrapper_summaries.append(
                    json.loads(
                        (
                            plan.runtime_dir
                            / "standard-production-iteration-summary.json"
                        ).read_text(encoding="utf-8")
                    )
                )
                return code

            result = start_full_process_observation.execute_observation(
                plan,
                observation_starter=self._starter(),
                production_runner=production,
            )

            self.assertEqual(
                "signed-off",
                result["status"],
                (result, wrapper_summaries, bridge_errors),
            )
            self.assertEqual(1, len(wrapper_calls))
            self.assertEqual(["bridge", "downstream"], [item[0] for item in calls])
            bridge_args = calls[0][1]
            downstream_args = calls[1][1]
            self.assertIn("--image", bridge_args)
            self.assertNotIn("--image", downstream_args)
            self.assertIn("--defer-timer-finish", downstream_args)
            self.assertEqual(str(plan.timer), value(downstream_args, "--timer"))
            wrapper_summary = json.loads(
                (
                    plan.runtime_dir / "standard-production-iteration-summary.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual("completed", wrapper_summary["status"])
            self.assertEqual(5, wrapper_summary["attempt_count"])
            self.assertEqual(0, wrapper_summary["retry_count"])
            timer = load_run(plan.timer)
            self.assertEqual("signed-off", timer["status"])
            self.assertEqual(
                [
                    "routing-preflight",
                    "source-selection",
                    "source-preparation",
                    "scope-analysis",
                    "semantic-design",
                    "scope-materialization",
                    "source-review",
                    "compile-preflight",
                    "writer-reviewer",
                    "promotion",
                    "final-reporting",
                ],
                [item["phase"] for item in timer["phases"]],
            )
            self.assertFalse(
                any(item["status"] == "running" for item in timer["phases"])
            )

    def test_blocking_dependency_stops_before_production(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            plan = start_full_process_observation.resolve_plan(
                repo_root=root,
                config_path=self._fixture(root),
                request_started_epoch_ms=1,
                codex_turn_id="turn-blocked",
            )
            calls = []

            result = start_full_process_observation.execute_observation(
                plan,
                observation_starter=self._starter(),
                dependency_analyzer=lambda _: {
                    "version": 1,
                    "status": "blocked-input",
                    "gaps": [{"gap_id": "GAP-1"}],
                    "blocking_gap_count": 1,
                },
                production_runner=lambda arguments: calls.append(arguments) or 0,
            )

            self.assertEqual("blocked-input", result["status"])
            self.assertEqual(0, len(calls))
            self.assertEqual(0, result["production"]["invocation_count"])
            self.assertEqual("blocked-input", load_run(plan.timer)["status"])

    def test_malformed_clarification_stops_before_production(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            plan = start_full_process_observation.resolve_plan(
                repo_root=root,
                config_path=self._fixture(root),
                request_started_epoch_ms=1,
                codex_turn_id="turn-clarification",
            )
            calls = []

            def malformed(*_):
                raise ValueError("malformed clarification")

            result = start_full_process_observation.execute_observation(
                plan,
                observation_starter=self._starter(),
                clarification_loader=malformed,
                production_runner=lambda arguments: calls.append(arguments) or 0,
            )

            self.assertEqual("terminal-failed", result["status"])
            self.assertEqual(0, len(calls))
            self.assertIn("malformed clarification", result["error"])

    def test_tamper_after_receipt_is_rejected_before_preparation_and_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            plan = start_full_process_observation.resolve_plan(
                repo_root=root,
                config_path=self._fixture(root),
                request_started_epoch_ms=1,
                codex_turn_id="turn-tamper",
            )
            preparation_calls = []
            production_calls = []

            def mutate(_):
                plan.source_files[1].write_text("tampered", encoding="utf-8")

            result = start_full_process_observation.execute_observation(
                plan,
                observation_starter=self._starter(mutate),
                source_preparer=lambda **kwargs: preparation_calls.append(kwargs),
                production_runner=lambda arguments: production_calls.append(arguments) or 0,
            )

            self.assertEqual("terminal-failed", result["status"])
            self.assertEqual([], preparation_calls)
            self.assertEqual([], production_calls)
            self.assertIn("changed after the bootstrap receipt", result["error"])

    def test_tamper_during_preparation_is_rejected_before_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            plan = start_full_process_observation.resolve_plan(
                repo_root=root,
                config_path=self._fixture(root),
                request_started_epoch_ms=1,
                codex_turn_id="turn-tamper-during-preparation",
            )
            production_calls = []

            def mutating_preparer(**kwargs):
                result = prepare_bounded_scope_context(**kwargs)
                plan.source_files[1].write_text("tampered", encoding="utf-8")
                return result

            result = start_full_process_observation.execute_observation(
                plan,
                observation_starter=self._starter(),
                source_preparer=mutating_preparer,
                production_runner=lambda arguments: production_calls.append(arguments) or 0,
            )

            self.assertEqual("terminal-failed", result["status"])
            self.assertEqual([], production_calls)
            self.assertEqual(0, result["production"]["invocation_count"])
            self.assertIn("changed after the bootstrap receipt", result["error"])
            self.assertNotEqual("running", load_run(plan.timer)["status"])

    def test_production_terminal_result_is_not_retried(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            plan = start_full_process_observation.resolve_plan(
                repo_root=root,
                config_path=self._fixture(root),
                request_started_epoch_ms=1,
                codex_turn_id="turn-no-retry",
            )
            calls = []

            def production(arguments):
                calls.append(arguments)
                plan.runtime_dir.mkdir(parents=True, exist_ok=True)
                (plan.runtime_dir / "standard-production-iteration-summary.json").write_text(
                    json.dumps({"status": "terminal-failed", "return_code": 2}),
                    encoding="utf-8",
                )
                return 2

            result = start_full_process_observation.execute_observation(
                plan,
                observation_starter=self._starter(),
                production_runner=production,
            )

            self.assertEqual("terminal-failed", result["status"])
            self.assertEqual(1, len(calls))
            self.assertEqual(1, result["production"]["invocation_count"])

    def test_starter_failure_after_timer_creation_terminalizes_timer(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            plan = start_full_process_observation.resolve_plan(
                repo_root=root,
                config_path=self._fixture(root),
                request_started_epoch_ms=1,
                codex_turn_id="turn-starter-failure",
            )

            def failing_starter(value):
                self._starter()(value)
                raise RuntimeError("starter failed after timer creation")

            result = start_full_process_observation.execute_observation(
                plan,
                observation_starter=failing_starter,
                production_runner=lambda _: self.fail("wrapper must not run"),
            )

            self.assertEqual("terminal-failed", result["status"])
            self.assertIn("starter failed after timer creation", result["error"])
            self.assertEqual("terminal-failed", load_run(plan.timer)["status"])

    def test_default_dependency_import_failure_terminalizes_started_timer(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            plan = start_full_process_observation.resolve_plan(
                repo_root=root,
                config_path=self._fixture(root),
                request_started_epoch_ms=1,
                codex_turn_id="turn-dependency-import-failure",
            )
            production_calls = []

            with patch(
                "scripts.start_full_process_observation._load_preparation_dependencies",
                side_effect=ModuleNotFoundError("injected stage dependency failure"),
            ):
                result = start_full_process_observation.execute_observation(
                    plan,
                    observation_starter=self._starter(),
                    production_runner=lambda arguments: production_calls.append(arguments)
                    or 0,
                )

            self.assertEqual("terminal-failed", result["status"])
            self.assertEqual("ModuleNotFoundError", result["error_type"])
            self.assertIn("injected stage dependency failure", result["error"])
            self.assertEqual([], production_calls)
            self.assertEqual(0, result["production"]["invocation_count"])
            timer = load_run(plan.timer)
            self.assertEqual("terminal-failed", timer["status"])
            self.assertEqual(
                "ModuleNotFoundError", timer["terminal"]["error_type"]
            )

    def test_direct_file_cli_execute_starts_and_terminalizes_before_wrapper(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        entrypoint = repo_root / "scripts" / "start_full_process_observation.py"
        recorder_source = repo_root / "scripts" / "workflow_wall_clock.py"
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = self._fixture(root, blocking_dependency=True)
            recorder = root / "scripts" / "workflow_wall_clock.py"
            recorder.write_text(
                "from __future__ import annotations\n"
                "import runpy\n"
                f"runpy.run_path({str(recorder_source)!r}, run_name='__main__')\n",
                encoding="utf-8",
            )
            turn_id = "turn-direct-file-cli"
            environment = os.environ.copy()
            shadow_root = root / "shadow-pythonpath"
            shadow_scripts = shadow_root / "scripts"
            shadow_scripts.mkdir(parents=True)
            (shadow_scripts / "codex_exec_bounded_scope_analyzer.py").write_text(
                "raise RuntimeError('shadow scripts package was imported')\n",
                encoding="utf-8",
            )
            dependency_paths = [
                entry
                for entry in sys.path
                if entry and "site-packages" in entry.casefold()
            ]
            # Keep the real repository later in PYTHONPATH to prove that the
            # entrypoint moves its own ROOT_DIR to deterministic index 0.  The
            # leading namespace-package shadow would otherwise intercept the
            # analyzer import.
            environment["PYTHONPATH"] = os.pathsep.join(
                (str(shadow_root), str(repo_root), str(repo_root), *dependency_paths)
            )
            isolated_home = root / "isolated-home"
            isolated_home.mkdir()
            isolated_appdata = isolated_home / "AppData" / "Roaming"
            isolated_local_appdata = isolated_home / "AppData" / "Local"
            isolated_appdata.mkdir(parents=True)
            isolated_local_appdata.mkdir(parents=True)
            unavailable_codex = root / "unavailable-codex.exe"
            environment.update(
                {
                    "HOME": str(isolated_home),
                    "USERPROFILE": str(isolated_home),
                    "CODEX_HOME": str(isolated_home / ".codex"),
                    "APPDATA": str(isolated_appdata),
                    "LOCALAPPDATA": str(isolated_local_appdata),
                    "CODEX_EXEC_COMMAND": str(unavailable_codex),
                    # The child commands use the absolute sys.executable path.
                    # Restrict discovery to the Python runtime directory so a
                    # dependency-gate regression cannot discover a real Codex.
                    "PATH": str(Path(sys.executable).resolve().parent),
                }
            )
            self.assertFalse(unavailable_codex.exists())
            self.assertIsNone(shutil.which("codex", path=environment["PATH"]))
            completed = subprocess.run(
                [
                    sys.executable,
                    str(entrypoint),
                    "--repo-root",
                    str(root),
                    "--config",
                    str(config),
                    "--request-started-epoch-ms",
                    "1",
                    "--codex-turn-id",
                    turn_id,
                    "--execute",
                ],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                check=False,
            )

            self.assertEqual(3, completed.returncode, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual("blocked-input", payload["status"])
            self.assertEqual(0, payload["production"]["invocation_count"])
            self.assertEqual("not-run", payload["production"]["status"])
            self.assertGreater(payload["preflight"]["blocking_gap_count"], 0)
            timer = (
                root
                / "fts"
                / "Demo"
                / "work"
                / "full-process-observation"
                / turn_id
                / "workflow-performance.json"
            )
            self.assertTrue(timer.is_file())
            self.assertEqual("blocked-input", load_run(timer)["status"])
            self.assertFalse((root / "fts" / "Demo" / "test-cases").exists())

    def test_execution_summary_write_failure_does_not_block_finish(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            plan = start_full_process_observation.resolve_plan(
                repo_root=root,
                config_path=self._fixture(root),
                request_started_epoch_ms=1,
                codex_turn_id="turn-summary-failure",
            )

            def production(_):
                plan.handoff_dir.mkdir(parents=True)
                plan.cycle_dir.mkdir(parents=True)
                plan.final_artifact.parent.mkdir(parents=True, exist_ok=True)
                plan.final_artifact.write_text(
                    "# Cases\n\n## TC-DEMO-001\n", encoding="utf-8"
                )
                plan.runtime_dir.mkdir(parents=True, exist_ok=True)
                (plan.runtime_dir / "standard-production-iteration-summary.json").write_text(
                    json.dumps({"status": "completed", "return_code": 0}),
                    encoding="utf-8",
                )
                return 0

            real_write = start_full_process_observation._write_json_atomic

            def fail_only_execution_summary(path, payload):
                if Path(path).resolve() == plan.execution_summary.resolve():
                    raise OSError("execution summary unavailable")
                return real_write(path, payload)

            with patch(
                "scripts.start_full_process_observation._write_json_atomic",
                side_effect=fail_only_execution_summary,
            ):
                result = start_full_process_observation.execute_observation(
                    plan,
                    observation_starter=self._starter(),
                    production_runner=production,
                )

            self.assertEqual("signed-off", result["status"])
            self.assertEqual(2, result["return_code"])
            self.assertEqual("failed", result["reporting"]["status"])
            self.assertEqual(
                "write-execution-summary",
                result["reporting"]["errors"][0]["operation"],
            )
            self.assertFalse(plan.execution_summary.exists())
            self.assertEqual("signed-off", load_run(plan.timer)["status"])

    def test_fresh_target_and_schema_v1_fail_before_recorder(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            plan = start_full_process_observation.resolve_plan(
                repo_root=root,
                config_path=self._fixture(root),
                request_started_epoch_ms=1,
                codex_turn_id="turn-existing",
            )
            plan.handoff_dir.mkdir(parents=True)
            calls = []
            with self.assertRaisesRegex(
                start_full_process_observation.BootstrapError,
                "fresh execution target already exists",
            ):
                start_full_process_observation.execute_observation(
                    plan, observation_starter=lambda value: calls.append(value) or {}
                )
            self.assertEqual([], calls)

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            plan = start_full_process_observation.resolve_plan(
                repo_root=root,
                config_path=self._fixture(root, schema_version=1),
                request_started_epoch_ms=1,
                codex_turn_id="turn-v1",
            )
            calls = []
            with self.assertRaisesRegex(
                start_full_process_observation.BootstrapError,
                "schema_version 2",
            ):
                start_full_process_observation.execute_observation(
                    plan, observation_starter=lambda value: calls.append(value) or {}
                )
            self.assertEqual([], calls)

    def test_registry_mismatch_is_rejected_before_recorder(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = self._fixture(root)
            payload = json.loads(config.read_text(encoding="utf-8"))
            template = root / payload["source_preparation"]["context_template"]
            context = json.loads(template.read_text(encoding="utf-8"))
            context["sources"][1]["manifest_binding"] = "supporting-material"
            template.write_text(
                json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            with self.assertRaisesRegex(
                start_full_process_observation.BootstrapError,
                "sources registry does not exactly match",
            ):
                start_full_process_observation.resolve_plan(
                    repo_root=root,
                    config_path=config,
                    request_started_epoch_ms=1,
                    codex_turn_id="turn-registry",
                )
            self.assertFalse(
                (
                    root
                    / "fts"
                    / "Demo"
                    / "work"
                    / "full-process-observation"
                    / "turn-registry"
                ).exists()
            )

    def test_schema_v2_hash_inventory_and_drift_fail_before_recorder(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = self._fixture(root)
            payload = json.loads(config.read_text(encoding="utf-8"))
            removed = next(iter(payload["expected_sha256"]))
            del payload["expected_sha256"][removed]
            config.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(
                start_full_process_observation.BootstrapError,
                "expected_sha256 inventory mismatch",
            ):
                start_full_process_observation.resolve_plan(
                    repo_root=root,
                    config_path=config,
                    request_started_epoch_ms=1,
                    codex_turn_id="turn-missing-pin",
                )

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = self._fixture(root)
            payload = json.loads(config.read_text(encoding="utf-8"))
            target_relative = next(iter(payload["expected_sha256"]))
            target = root / target_relative
            target.write_bytes(target.read_bytes() + b"drift")
            with self.assertRaisesRegex(
                start_full_process_observation.BootstrapError,
                "checked-in SHA-256 mismatch",
            ):
                start_full_process_observation.resolve_plan(
                    repo_root=root,
                    config_path=config,
                    request_started_epoch_ms=1,
                    codex_turn_id="turn-hash-drift",
                )
            self.assertFalse(
                (root / "fts" / "Demo" / "work" / "full-process-observation").exists()
            )

    def test_every_pinned_input_class_is_checked_before_recorder(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = self._fixture(root)
            payload = json.loads(config.read_text(encoding="utf-8"))
            for index, relative in enumerate(payload["expected_sha256"]):
                with self.subTest(relative=relative):
                    target = root / relative
                    original = target.read_bytes()
                    target.write_bytes(original + b"\n")
                    with self.assertRaisesRegex(
                        start_full_process_observation.BootstrapError,
                        "checked-in SHA-256 mismatch",
                    ):
                        start_full_process_observation.resolve_plan(
                            repo_root=root,
                            config_path=config,
                            request_started_epoch_ms=1,
                            codex_turn_id=f"turn-pin-{index}",
                        )
                    target.write_bytes(original)

    def test_schema_v2_rejects_noncanonical_cache_and_unknown_config_field(self) -> None:
        for mutation, message in (
            (
                lambda payload: payload["source_preparation"].update(
                    {"cache_dir": "fts/Demo/work/source-cache"}
                ),
                "must equal canonical protected cache path",
            ),
            (
                lambda payload: payload.update({"unexpected": True}),
                "schema-v2 bootstrap config fields mismatch",
            ),
        ):
            with self.subTest(message=message), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                config = self._fixture(root)
                payload = json.loads(config.read_text(encoding="utf-8"))
                mutation(payload)
                config.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaisesRegex(
                    start_full_process_observation.BootstrapError, message
                ):
                    start_full_process_observation.resolve_plan(
                        repo_root=root,
                        config_path=config,
                        request_started_epoch_ms=1,
                        codex_turn_id="turn-config-guard",
                    )

    def test_schema_v2_supports_package_without_agent_notes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = self._fixture(root)
            payload = json.loads(config.read_text(encoding="utf-8"))
            notes = root / "fts" / "Demo" / "AGENT-NOTES.md"
            notes.unlink()
            payload["scope_inputs"] = [
                item
                for item in payload["scope_inputs"]
                if item["role"] != "mandatory-package-context"
            ]
            notes_relative = notes.relative_to(root).as_posix()
            del payload["expected_sha256"][notes_relative]

            template_relative = payload["source_preparation"]["context_template"]
            template = root / template_relative
            context = json.loads(template.read_text(encoding="utf-8"))
            context.pop("package_notes")
            context["sources"] = [
                item
                for item in context["sources"]
                if item["role"] != "mandatory-package-context"
            ]
            template.write_text(
                json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            payload["expected_sha256"][template_relative] = self._sha256(template)
            config.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            plan = start_full_process_observation.resolve_plan(
                repo_root=root,
                config_path=config,
                request_started_epoch_ms=1,
                codex_turn_id="turn-no-package-notes",
            )
            self.assertFalse(
                any(
                    item.role == "mandatory-package-context"
                    for item in plan.scope_inputs
                )
            )
            result = prepare_bounded_scope_context(
                repo_root=root,
                context_template=plan.context_template,
                cache_dir=plan.source_preparation_cache,
                output_context=plan.prepared_context,
                output_baseline=plan.source_row_baseline,
            )
            prepared = json.loads(result.output_context.read_text(encoding="utf-8"))
            self.assertNotIn("package_notes", prepared)

    def test_config_tamper_after_resolve_is_rejected_before_starter(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = self._fixture(root)
            plan = start_full_process_observation.resolve_plan(
                repo_root=root,
                config_path=config,
                request_started_epoch_ms=1,
                codex_turn_id="turn-config-tamper",
            )
            config.write_text(
                config.read_text(encoding="utf-8") + "\n", encoding="utf-8"
            )
            starter_calls = []

            with self.assertRaisesRegex(
                start_full_process_observation.BootstrapError,
                "bootstrap config SHA-256 changed after resolve",
            ):
                start_full_process_observation.execute_observation(
                    plan,
                    observation_starter=lambda value: starter_calls.append(value) or {},
                )
            self.assertEqual([], starter_calls)
            self.assertFalse(plan.run_dir.exists())
            self.assertFalse(plan.timer.exists())
            with patch(
                "scripts.start_full_process_observation.subprocess.run"
            ) as recorder:
                with self.assertRaisesRegex(
                    start_full_process_observation.BootstrapError,
                    "bootstrap config SHA-256 changed after resolve",
                ):
                    start_full_process_observation.start_observation(plan)
            recorder.assert_not_called()

    def test_source_only_profile_rejects_prior_result_fields_and_paths(self) -> None:
        mutations = (
            ("reviewer-output", lambda context: context.update({"reviewer_output": {}})),
            (
                "inline-evidence",
                lambda context: context.update({"bounded_evidence_inline": {}}),
            ),
            (
                "handoff-path",
                lambda context: context.update(
                    {"prior_input": "fts/Demo/work/stage-handoffs/00-old/scope.md"}
                ),
            ),
            (
                "prior-count",
                lambda context: context["scope_execution_facts"].update(
                    {"expected_tc_count": 12}
                ),
            ),
        )
        for name, mutation in mutations:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                config = self._fixture(root)
                payload = json.loads(config.read_text(encoding="utf-8"))
                template = root / payload["source_preparation"]["context_template"]
                context = json.loads(template.read_text(encoding="utf-8"))
                mutation(context)
                template.write_text(
                    json.dumps(context, ensure_ascii=False), encoding="utf-8"
                )
                with self.assertRaisesRegex(
                    start_full_process_observation.BootstrapError,
                    "not source-only|cannot pin prior-result-derived|top-level fields mismatch",
                ):
                    start_full_process_observation.resolve_plan(
                        repo_root=root,
                        config_path=config,
                        request_started_epoch_ms=1,
                        codex_turn_id=f"turn-source-only-{name}",
                    )

    def test_unknown_inline_field_is_rejected_even_after_template_repin(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = self._fixture(root)
            payload = json.loads(config.read_text(encoding="utf-8"))
            template_relative = payload["source_preparation"]["context_template"]
            template = root / template_relative
            context = json.loads(template.read_text(encoding="utf-8"))
            context["draft_test_cases"] = "# Prior test cases"
            template.write_text(
                json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            payload["expected_sha256"][template_relative] = self._sha256(template)
            config.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            with self.assertRaisesRegex(
                start_full_process_observation.BootstrapError,
                r"top-level fields mismatch:.*draft_test_cases",
            ):
                start_full_process_observation.resolve_plan(
                    repo_root=root,
                    config_path=config,
                    request_started_epoch_ms=1,
                    codex_turn_id="turn-inline-repin",
                )
            self.assertFalse(
                (
                    root
                    / "fts"
                    / "Demo"
                    / "work"
                    / "full-process-observation"
                    / "turn-inline-repin"
                ).exists()
            )

    def test_checked_in_profile_is_source_only_and_prepares_without_gaps(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        profile = (
            repo_root
            / "evals"
            / "full-production-benchmark"
            / "configs"
            / "postfinal-v2-employment-main-work"
            / "bounded-context-template.json"
        )
        context = json.loads(profile.read_text(encoding="utf-8"))
        facts = context["scope_execution_facts"]
        self.assertIsNone(facts["expected_testable_assertion_count"])
        self.assertIsNone(facts["expected_tc_count"])
        self.assertNotIn("source_cache", context)
        self.assertNotIn("source_row_baseline", context)
        self.assertEqual(
            {"Тип занятости": "CLR-EMP-001"},
            context["dependency_alias_provenance"],
        )
        dictionary = context["dictionary_inventory"][0]
        self.assertEqual(5, len(dictionary["entries"]))
        self.assertEqual(
            ["staff", "sole_proprietor", "mid_manager", "top_manager", "expert"],
            [item["internal_code"] for item in dictionary["entries"]],
        )
        self.assertTrue(all(item["archived"] is False for item in dictionary["entries"]))
        registered_paths = [item["path"] for item in context["sources"]]
        self.assertFalse(
            any(
                marker in path.replace("\\", "/")
                for path in registered_paths
                for marker in (
                    "/test-cases/",
                    "/work/stage-handoffs/",
                    "/work/review-cycles/",
                    "/work/full-process-observation/",
                )
            )
        )

        temp_parent = repo_root / ".codex-temp"
        temp_parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_parent) as raw:
            output = Path(raw)
            result = prepare_bounded_scope_context(
                repo_root=repo_root,
                context_template=profile,
                cache_dir=output / "cache",
                output_context=output / "out" / "context.json",
                output_baseline=output / "out" / "baseline.json",
            )
            prepared = json.loads(result.output_context.read_text(encoding="utf-8"))
            clarifications = load_approved_clarifications(repo_root, prepared)
            from scripts.codex_exec_bounded_scope_analyzer import analyze_dependency_gaps

            dependency = analyze_dependency_gaps(prepared)
            self.assertEqual(2, len(clarifications))
            self.assertEqual("pass", dependency["status"])
            self.assertEqual(0, dependency["blocking_gap_count"])


if __name__ == "__main__":
    unittest.main()
