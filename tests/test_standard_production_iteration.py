from __future__ import annotations

import hashlib
import io
import json
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Sequence
from unittest.mock import patch

from scripts import run_standard_production_iteration
from test_case_agent.bounded_scope_boundary import recompute_bounded_context_sha256
from test_case_agent.review_cycle.source_assertions import (
    MANIFEST_VERSION,
    RegisteredArtifact,
    RegisteredSource,
    SourceAssertion,
    SourceAssertionManifest,
    SourceRow,
)
from test_case_agent.semantic_design_bridge import prepared_context_sha256


def _value(argv: Sequence[str], option: str) -> str:
    index = argv.index(option)
    return argv[index + 1]


def _source_manifest() -> SourceAssertionManifest:
    source_path = "source/main.xhtml"
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
        scope_slug="demo",
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


class StandardProductionIterationTests(unittest.TestCase):
    def test_source_review_lifecycle_counts_bounded_shards_as_attempts_not_retries(
        self,
    ) -> None:
        payload = {
            "status": "completed",
            "execution_route": "bounded-sharded",
            "attempt_count": 3,
            "retry_count": 0,
            "model_session_count": 3,
            "review_shard_count": 3,
        }
        self.assertEqual(
            (3, 0),
            run_standard_production_iteration._source_review_count_pair(payload),
        )
        payload["retry_count"] = 2
        self.assertIsNone(
            run_standard_production_iteration._source_review_count_pair(payload)
        )

    def _base(self, root: Path) -> dict[str, Path]:
        paths = {
            "context": root / "prepared-context.json",
            "runtime": root / "runtime",
            "handoff": root / "fts/Demo/work/stage-handoffs/01-scope",
            "cycle": root / "fts/Demo/work/review-cycles/01-scope",
            "final": root / "fts/Demo/test-cases/1-scope.md",
            "timer": root / "performance.json",
            "image": root / "mockup.png",
        }
        context_payload: dict[str, object] = {
            "package_id": "WP-07",
            "ft_slug": "Demo",
        }
        context_payload["source_cache"] = {
            "component_digests": {
                "bounded_context_sha256": recompute_bounded_context_sha256(
                    context_payload
                )
            }
        }
        paths["context"].write_text(json.dumps(context_payload), encoding="utf-8")
        paths["timer"].write_text(
            '{"status":"running","phases":[]}\n', encoding="utf-8"
        )
        paths["image"].write_bytes(b"mockup")
        return paths

    def _argv(self, root: Path, paths: dict[str, Path]) -> list[str]:
        return [
            "--repo-root", str(root),
            "--context", str(paths["context"]),
            "--runtime-dir", str(paths["runtime"]),
            "--handoff-dir", str(paths["handoff"]),
            "--cycle-dir", str(paths["cycle"]),
            "--final-artifact", str(paths["final"]),
            "--timer", str(paths["timer"]),
            "--image", str(paths["image"]),
            "--codex-command", "verified-codex",
            "--measurement-mode", "observational",
        ]

    @staticmethod
    def _record_downstream_timer(
        timer: Path,
        cycle: Path,
        *,
        writer_reviewer_status: str = "completed",
        include_reviewer: bool = True,
        compile_status: str = "completed",
        write_fresh_metrics: bool = True,
        explicit_reuse: bool = False,
        stage_round: int = 1,
        source_reuse: bool = False,
        source_review_path: Path | None = None,
    ) -> None:
        now_ms = time.time_ns() // 1_000_000
        stage_metrics = [
            {
                "stage_id": f"writer-r{stage_round}",
                "attempt_id": "attempt-001",
                "role": "writer",
            }
        ]
        if include_reviewer:
            stage_metrics.append(
                {
                    "stage_id": f"reviewer-r{stage_round}",
                    "attempt_id": "attempt-001",
                    "role": "reviewer",
                }
            )
        if compile_status == "completed" and write_fresh_metrics:
            for metric in stage_metrics:
                metric_path = (
                    cycle
                    / "attempts"
                    / str(metric["stage_id"])
                    / str(metric["attempt_id"])
                    / "metrics.json"
                )
                metric_path.parent.mkdir(parents=True, exist_ok=True)
                metric_path.write_text(json.dumps(metric), encoding="utf-8")
        if compile_status == "completed":
            stage_metrics = [
                json.loads(path.read_text(encoding="utf-8"))
                for path in sorted(cycle.glob("attempts/*/*/metrics.json"))
            ]
        source_summary_path = cycle / "source-review-summary.json"
        if source_reuse:
            source_review = source_review_path or cycle / "source-assertion-review.json"
            source_review.parent.mkdir(parents=True, exist_ok=True)
            if not source_review.exists():
                source_review.write_text("{}\n", encoding="utf-8")
            source_summary = {
                "version": 1,
                "status": "reused",
                "attempt_count": 0,
                "retry_count": 0,
                "reuse_evidence": {
                    "source_assertion_review": {
                        "path": str(source_review.resolve()),
                        "sha256": hashlib.sha256(source_review.read_bytes()).hexdigest(),
                    },
                    "persisted_summary": {
                        "path": str(source_summary_path.resolve()),
                        "sha256": (
                            hashlib.sha256(source_summary_path.read_bytes()).hexdigest()
                            if source_summary_path.is_file()
                            else None
                        ),
                    },
                },
            }
        else:
            source_summary = {"status": "completed", "attempt_count": 1}
            source_summary_path.parent.mkdir(parents=True, exist_ok=True)
            source_summary_path.write_text(json.dumps(source_summary), encoding="utf-8")
        phases: list[dict[str, object]] = [
            {
                "phase": "source-review",
                "status": "completed",
                "started_epoch_ms": now_ms,
                "metrics": {"summary": source_summary},
            },
            {
                "phase": "compile-preflight",
                "status": compile_status,
                "started_epoch_ms": now_ms,
                "metrics": {},
            },
        ]
        if compile_status == "completed":
            phases.append(
                {
                    "phase": "writer-reviewer",
                    "status": writer_reviewer_status,
                    "started_epoch_ms": now_ms,
                    "metrics": {
                        "stage_metrics": stage_metrics,
                        "performance": {"stage_metrics": stage_metrics},
                        **(
                            {
                                "model_attempt_evidence": {
                                    "status": "reused",
                                    "attempt_count": 0,
                                    "retry_count": 0,
                                }
                            }
                            if explicit_reuse
                            else {}
                        ),
                        **(
                            {"model_attempt_evidence_complete": True}
                            if writer_reviewer_status != "completed"
                            else {}
                        ),
                    },
                }
            )
        try:
            existing = json.loads(timer.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            existing = {}
        existing_phases = (
            list(existing.get("phases", []))
            if isinstance(existing, dict)
            and isinstance(existing.get("phases"), list)
            else []
        )
        timer.write_text(
            json.dumps({"phases": [*existing_phases, *phases]}), encoding="utf-8"
        )

    @staticmethod
    def _write_stage_metric(cycle: Path, metric: dict[str, object]) -> Path:
        path = (
            cycle
            / "attempts"
            / str(metric["stage_id"])
            / str(metric["attempt_id"])
            / "metrics.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(metric), encoding="utf-8")
        return path

    @staticmethod
    def _publish_bridge_outputs(
        argv: Sequence[str],
        *,
        package_id: str = "WP-07",
        write_summary: bool = True,
    ) -> None:
        handoff = Path(_value(argv, "--handoff-dir"))
        handoff.mkdir(parents=True)
        boundary_artifact = handoff / "scope-boundary-decision.json"
        boundary_artifact.write_text(
            json.dumps({"version": 2, "status": "ready"}),
            encoding="utf-8",
        )
        semantic_artifact = handoff / "semantic-design.json"
        semantic_artifact.write_text(
            json.dumps(
                {
                    "status": "ready",
                    "obligations": [
                        {"obligation_id": "OBL-001", "package_id": package_id}
                    ],
                }
            ),
            encoding="utf-8",
        )
        (handoff / "workflow-state.yaml").write_text(
            "ft_slug: Demo\n"
            "latest_artifacts:\n"
            "  source_assertion_review: work/stage-handoffs/01-scope/source-assertion-review.json\n",
            encoding="utf-8",
        )
        publication = {
            "status": "atomic-renamed",
            "final_handoff": "fts/Demo/work/stage-handoffs/01-scope",
        }
        manifest = _source_manifest()
        (handoff / "source-assertions.json").write_text(
            json.dumps(manifest.to_dict()), encoding="utf-8"
        )
        readiness = {
            "status": "passed",
            "canonical_preflight": "source-reviewer.prepare_evidence_set",
            "published_manifest_digest": manifest.digest,
        }
        owner_token = _value(argv, "--publication-owner-token")
        context_payload = json.loads(
            Path(_value(argv, "--context")).read_text(encoding="utf-8")
        )
        (handoff / "semantic-design-bridge-receipt.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "contract": "scope-v2-to-semantic-design-v1",
                    "status": "verified",
                    "materialization_status": "materialized",
                    "prepared_context_sha256": prepared_context_sha256(
                        context_payload
                    ),
                    "publication_ownership_contract_version": 1,
                    "publication_owner_token": owner_token,
                    "source_assertion_manifest_digest": manifest.digest,
                    "scope_boundary_artifact_sha256": hashlib.sha256(
                        boundary_artifact.read_bytes()
                    ).hexdigest(),
                    "semantic_design_artifact_sha256": hashlib.sha256(
                        semantic_artifact.read_bytes()
                    ).hexdigest(),
                    "publication": publication,
                    "downstream_evidence_readiness": readiness,
                }
            ),
            encoding="utf-8",
        )
        if write_summary:
            summary = Path(_value(argv, "--summary-output"))
            summary.parent.mkdir(parents=True, exist_ok=True)
            summary.write_text(
                json.dumps(
                    {
                        "status": "completed",
                        "return_code": 0,
                        "attempt_count": 2,
                        "retry_count": 0,
                        "publication_owner_token": owner_token,
                        "scope_materialization": {
                            "status": "completed",
                            "publication": publication,
                            "downstream_evidence_readiness": readiness,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )

    def test_success_calls_bridge_then_downstream_with_exact_derived_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._base(root)
            calls: list[tuple[str, list[str]]] = []

            def bridge(argv: Sequence[str] | None) -> int:
                self.assertIsNotNone(argv)
                actual = list(argv or [])
                calls.append(("bridge", actual))
                self._publish_bridge_outputs(actual)
                return 0

            def downstream(argv: Sequence[str] | None) -> int:
                self.assertIsNotNone(argv)
                actual = list(argv or [])
                calls.append(("downstream", actual))
                final_artifact = Path(_value(actual, "--final-artifact"))
                final_artifact.parent.mkdir(parents=True, exist_ok=True)
                final_artifact.write_text("# Signed off\n", encoding="utf-8")
                self._record_downstream_timer(paths["timer"], paths["cycle"])
                return 0

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = run_standard_production_iteration.main(
                    self._argv(root, paths),
                    bridge_runner=bridge,
                    downstream_runner=downstream,
                )

            self.assertEqual(0, code)
            self.assertEqual(["bridge", "downstream"], [name for name, _ in calls])
            bridge_args = calls[0][1]
            downstream_args = calls[1][1]
            self.assertEqual(str(root.resolve()), _value(bridge_args, "--repo-root"))
            self.assertEqual(str(paths["context"].resolve()), _value(bridge_args, "--context"))
            self.assertEqual(str(paths["runtime"].resolve()), _value(bridge_args, "--runtime-dir"))
            self.assertEqual(str(paths["handoff"].resolve()), _value(bridge_args, "--handoff-dir"))
            self.assertEqual("observational", _value(bridge_args, "--measurement-mode"))
            self.assertEqual(str(paths["timer"].resolve()), _value(bridge_args, "--timer"))
            self.assertEqual(str(paths["image"].resolve()), _value(bridge_args, "--image"))
            self.assertEqual("verified-codex", _value(bridge_args, "--codex-command"))

            self.assertEqual(str(root.resolve()), _value(downstream_args, "--repo-root"))
            self.assertEqual(
                str((paths["handoff"] / "workflow-state.yaml").resolve()),
                _value(downstream_args, "--workflow-state"),
            )
            self.assertEqual(str(paths["cycle"].resolve()), _value(downstream_args, "--cycle-dir"))
            self.assertEqual(str(paths["final"].resolve()), _value(downstream_args, "--final-artifact"))
            self.assertEqual("WP-07", _value(downstream_args, "--package-id"))
            self.assertEqual(str(paths["timer"].resolve()), _value(downstream_args, "--timer"))
            self.assertIn("--defer-timer-finish", downstream_args)
            self.assertEqual("verified-codex", _value(downstream_args, "--codex-command"))
            measurement_index = downstream_args.index("--measurement-mode")
            self.assertEqual("observational", downstream_args[measurement_index + 1])
            self.assertNotIn("--image", downstream_args)

            summary = json.loads(
                (
                    paths["runtime"]
                    / "standard-production-iteration-summary.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual("completed", summary["status"])
            self.assertEqual(5, summary["attempt_count"])
            self.assertEqual(0, summary["retry_count"])
            self.assertEqual(
                "bridge-and-downstream-components",
                summary["lifecycle_count_evidence"]["source"],
            )
            self.assertEqual(2, summary["bridge_attempt_count"])
            self.assertEqual(3, summary["downstream_attempt_count"])
            self.assertEqual(
                "recovered", summary["lifecycle_count_evidence"]["status"]
            )
            self.assertEqual(
                _value(bridge_args, "--publication-owner-token"),
                summary["publication_owner_token"],
            )
            self.assertEqual(0, summary["fallback_count"])
            self.assertEqual("WP-07", summary["package_id"])

    def test_bridge_failure_stops_before_downstream(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._base(root)
            downstream_calls: list[list[str]] = []

            def bridge(argv: Sequence[str] | None) -> int:
                actual = list(argv or [])
                summary = Path(_value(actual, "--summary-output"))
                summary.parent.mkdir(parents=True, exist_ok=True)
                summary.write_text(
                    json.dumps(
                        {
                            "status": "blocked-input",
                            "stopped_after": "scope-analysis",
                            "attempt_count": 2,
                            "retry_count": 1,
                            "publication_owner_token": _value(
                                actual, "--publication-owner-token"
                            ),
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
                return 3

            def downstream(argv: Sequence[str] | None) -> int:
                actual = list(argv or [])
                downstream_calls.append(actual)
                final_artifact = Path(_value(actual, "--final-artifact"))
                final_artifact.parent.mkdir(parents=True, exist_ok=True)
                final_artifact.write_text("# Signed off\n", encoding="utf-8")
                return 0

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = run_standard_production_iteration.main(
                    self._argv(root, paths),
                    bridge_runner=bridge,
                    downstream_runner=downstream,
                )

            self.assertEqual(3, code)
            self.assertEqual([], downstream_calls)
            summary = json.loads(
                (
                    paths["runtime"]
                    / "standard-production-iteration-summary.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual("blocked-input", summary["status"])
            self.assertEqual("not-run", summary["downstream"]["status"])
            self.assertEqual(2, summary["attempt_count"])
            self.assertEqual(1, summary["retry_count"])
            self.assertEqual(
                "owned-bridge-summary",
                summary["lifecycle_count_evidence"]["source"],
            )

    def test_corrupted_bridge_count_pair_makes_totals_unknown(self) -> None:
        for attempt_count, retry_count in ((1, 2), (0, 1)):
            with (
                self.subTest(
                    attempt_count=attempt_count,
                    retry_count=retry_count,
                ),
                tempfile.TemporaryDirectory() as raw,
            ):
                root = Path(raw)
                paths = self._base(root)

                def bridge(argv: Sequence[str] | None) -> int:
                    actual = list(argv or [])
                    self._publish_bridge_outputs(actual)
                    bridge_summary = Path(_value(actual, "--summary-output"))
                    payload = json.loads(bridge_summary.read_text(encoding="utf-8"))
                    payload["attempt_count"] = attempt_count
                    payload["retry_count"] = retry_count
                    bridge_summary.write_text(json.dumps(payload), encoding="utf-8")
                    return 0

                def downstream(argv: Sequence[str] | None) -> int:
                    actual = list(argv or [])
                    final_artifact = Path(_value(actual, "--final-artifact"))
                    final_artifact.parent.mkdir(parents=True, exist_ok=True)
                    final_artifact.write_text("# Signed off\n", encoding="utf-8")
                    self._record_downstream_timer(paths["timer"], paths["cycle"])
                    return 0

                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    code = run_standard_production_iteration.main(
                        self._argv(root, paths),
                        bridge_runner=bridge,
                        downstream_runner=downstream,
                    )

                self.assertEqual(0, code)
                summary = json.loads(
                    (
                        paths["runtime"]
                        / "standard-production-iteration-summary.json"
                    ).read_text(encoding="utf-8")
                )
                self.assertIsNone(summary["bridge_attempt_count"])
                self.assertIsNone(summary["bridge_retry_count"])
                self.assertIsNone(summary["attempt_count"])
                self.assertIsNone(summary["retry_count"])
                self.assertEqual(
                    "unknown",
                    summary["lifecycle_count_evidence"]["status"],
                )

    def test_downstream_compile_failure_aggregates_only_executed_model_stages(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._base(root)

            def bridge(argv: Sequence[str] | None) -> int:
                self._publish_bridge_outputs(list(argv or []))
                return 0

            def downstream(_argv: Sequence[str] | None) -> int:
                self._record_downstream_timer(
                    paths["timer"], paths["cycle"], compile_status="failed"
                )
                return 2

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = run_standard_production_iteration.main(
                    self._argv(root, paths),
                    bridge_runner=bridge,
                    downstream_runner=downstream,
                )

            self.assertEqual(2, code)
            summary = json.loads(
                (
                    paths["runtime"]
                    / "standard-production-iteration-summary.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual("terminal-failed", summary["status"])
            self.assertEqual(2, summary["bridge_attempt_count"])
            self.assertEqual(1, summary["downstream_attempt_count"])
            self.assertEqual(3, summary["attempt_count"])
            self.assertEqual(0, summary["retry_count"])

    def test_downstream_without_fresh_lifecycle_evidence_is_unknown_not_zero(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._base(root)

            def bridge(argv: Sequence[str] | None) -> int:
                self._publish_bridge_outputs(list(argv or []))
                return 0

            def downstream(argv: Sequence[str] | None) -> int:
                final_artifact = Path(_value(list(argv or []), "--final-artifact"))
                final_artifact.parent.mkdir(parents=True, exist_ok=True)
                final_artifact.write_text("# Signed off\n", encoding="utf-8")
                return 0

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = run_standard_production_iteration.main(
                    self._argv(root, paths),
                    bridge_runner=bridge,
                    downstream_runner=downstream,
                )

            self.assertEqual(0, code)
            summary = json.loads(
                (
                    paths["runtime"]
                    / "standard-production-iteration-summary.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(2, summary["bridge_attempt_count"])
            self.assertIsNone(summary["downstream_attempt_count"])
            self.assertIsNone(summary["attempt_count"])
            self.assertIsNone(summary["retry_count"])
            self.assertEqual(
                "unknown", summary["lifecycle_count_evidence"]["status"]
            )

    def test_preexisting_stage_metrics_are_ignored_when_fresh_attempts_exist(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._base(root)
            for metric in (
                {"stage_id": "writer-r1", "attempt_id": "attempt-001", "role": "writer"},
                {"stage_id": "reviewer-r1", "attempt_id": "attempt-001", "role": "reviewer"},
            ):
                self._write_stage_metric(paths["cycle"], metric)

            def bridge(argv: Sequence[str] | None) -> int:
                self._publish_bridge_outputs(list(argv or []))
                return 0

            def downstream(argv: Sequence[str] | None) -> int:
                self._record_downstream_timer(
                    paths["timer"], paths["cycle"], stage_round=2
                )
                final_artifact = Path(_value(list(argv or []), "--final-artifact"))
                final_artifact.parent.mkdir(parents=True, exist_ok=True)
                final_artifact.write_text("# Signed off\n", encoding="utf-8")
                return 0

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = run_standard_production_iteration.main(
                    self._argv(root, paths), bridge_runner=bridge, downstream_runner=downstream
                )

            self.assertEqual(0, code)
            summary = json.loads(
                (paths["runtime"] / "standard-production-iteration-summary.json").read_text(encoding="utf-8")
            )
            self.assertEqual(3, summary["downstream_attempt_count"])
            self.assertEqual(5, summary["attempt_count"])
            details = summary["downstream_lifecycle_count_evidence"]["stage_counts"]["writer-reviewer"]
            self.assertEqual(2, details["ignored_preexisting_identity_count"])

    def test_stale_only_stage_metrics_require_explicit_reuse_receipt(self) -> None:
        for explicit_reuse, expected_downstream, expected_total in (
            (False, None, None),
            (True, 1, 3),
        ):
            with self.subTest(explicit_reuse=explicit_reuse), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                paths = self._base(root)
                for metric in (
                    {"stage_id": "writer-r1", "attempt_id": "attempt-001", "role": "writer"},
                    {"stage_id": "reviewer-r1", "attempt_id": "attempt-001", "role": "reviewer"},
                ):
                    self._write_stage_metric(paths["cycle"], metric)

                def bridge(argv: Sequence[str] | None) -> int:
                    self._publish_bridge_outputs(list(argv or []))
                    return 0

                def downstream(argv: Sequence[str] | None) -> int:
                    self._record_downstream_timer(
                        paths["timer"],
                        paths["cycle"],
                        write_fresh_metrics=False,
                        explicit_reuse=explicit_reuse,
                    )
                    final_artifact = Path(_value(list(argv or []), "--final-artifact"))
                    final_artifact.parent.mkdir(parents=True, exist_ok=True)
                    final_artifact.write_text("# Signed off\n", encoding="utf-8")
                    return 0

                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    code = run_standard_production_iteration.main(
                        self._argv(root, paths), bridge_runner=bridge, downstream_runner=downstream
                    )
                self.assertEqual(0, code)
                summary = json.loads(
                    (paths["runtime"] / "standard-production-iteration-summary.json").read_text(encoding="utf-8")
                )
                self.assertEqual(expected_downstream, summary["downstream_attempt_count"])
                self.assertEqual(expected_total, summary["attempt_count"])

    def test_preexisting_future_timestamp_timer_phase_is_not_current(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._base(root)
            future = time.time_ns() // 1_000_000 + 60_000
            paths["timer"].write_text(
                json.dumps(
                    {
                        "status": "running",
                        "phases": [
                            {
                                "phase": "source-review",
                                "status": "completed",
                                "started_epoch_ms": future,
                                "metrics": {"summary": {"attempt_count": 99}},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            def bridge(argv: Sequence[str] | None) -> int:
                self._publish_bridge_outputs(list(argv or []))
                return 0

            def downstream(argv: Sequence[str] | None) -> int:
                self._record_downstream_timer(paths["timer"], paths["cycle"])
                final_artifact = Path(_value(list(argv or []), "--final-artifact"))
                final_artifact.parent.mkdir(parents=True, exist_ok=True)
                final_artifact.write_text("# Signed off\n", encoding="utf-8")
                return 0

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = run_standard_production_iteration.main(
                    self._argv(root, paths), bridge_runner=bridge, downstream_runner=downstream
                )
            self.assertEqual(0, code)
            summary = json.loads(
                (paths["runtime"] / "standard-production-iteration-summary.json").read_text(encoding="utf-8")
            )
            self.assertEqual(5, summary["attempt_count"])

    def test_overwritten_metric_identity_is_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._base(root)
            for metric in (
                {"stage_id": "writer-r1", "attempt_id": "attempt-001", "role": "writer", "outcome": "old"},
                {"stage_id": "reviewer-r1", "attempt_id": "attempt-001", "role": "reviewer", "outcome": "old"},
            ):
                self._write_stage_metric(paths["cycle"], metric)

            def bridge(argv: Sequence[str] | None) -> int:
                self._publish_bridge_outputs(list(argv or []))
                return 0

            def downstream(argv: Sequence[str] | None) -> int:
                self._record_downstream_timer(paths["timer"], paths["cycle"])
                final_artifact = Path(_value(list(argv or []), "--final-artifact"))
                final_artifact.parent.mkdir(parents=True, exist_ok=True)
                final_artifact.write_text("# Signed off\n", encoding="utf-8")
                return 0

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = run_standard_production_iteration.main(
                    self._argv(root, paths), bridge_runner=bridge, downstream_runner=downstream
                )
            self.assertEqual(0, code)
            summary = json.loads(
                (paths["runtime"] / "standard-production-iteration-summary.json").read_text(encoding="utf-8")
            )
            self.assertIsNone(summary["attempt_count"])

    def test_reuse_without_timer_metrics_cannot_hide_fresh_or_overwritten_metrics(self) -> None:
        for overwrite in (False, True):
            with self.subTest(overwrite=overwrite), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                paths = self._base(root)
                if overwrite:
                    for metric in (
                        {"stage_id": "writer-r1", "attempt_id": "attempt-001", "role": "writer", "outcome": "old"},
                        {"stage_id": "reviewer-r1", "attempt_id": "attempt-001", "role": "reviewer", "outcome": "old"},
                    ):
                        self._write_stage_metric(paths["cycle"], metric)

                def bridge(argv: Sequence[str] | None) -> int:
                    self._publish_bridge_outputs(list(argv or []))
                    return 0

                def downstream(argv: Sequence[str] | None) -> int:
                    for metric in (
                        {"stage_id": "writer-r1", "attempt_id": "attempt-001", "role": "writer", "outcome": "new"},
                        {"stage_id": "reviewer-r1", "attempt_id": "attempt-001", "role": "reviewer", "outcome": "new"},
                    ):
                        self._write_stage_metric(paths["cycle"], metric)
                    self._record_downstream_timer(
                        paths["timer"],
                        paths["cycle"],
                        write_fresh_metrics=False,
                        explicit_reuse=True,
                    )
                    timer_payload = json.loads(paths["timer"].read_text(encoding="utf-8"))
                    writer_metrics = timer_payload["phases"][-1]["metrics"]
                    writer_metrics.pop("stage_metrics", None)
                    writer_metrics.pop("performance", None)
                    paths["timer"].write_text(json.dumps(timer_payload), encoding="utf-8")
                    final_artifact = Path(_value(list(argv or []), "--final-artifact"))
                    final_artifact.parent.mkdir(parents=True, exist_ok=True)
                    final_artifact.write_text("# Signed off\n", encoding="utf-8")
                    return 0

                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    code = run_standard_production_iteration.main(
                        self._argv(root, paths), bridge_runner=bridge, downstream_runner=downstream
                    )
                self.assertEqual(0, code)
                summary = json.loads(
                    (paths["runtime"] / "standard-production-iteration-summary.json").read_text(encoding="utf-8")
                )
                self.assertIsNone(summary["downstream_attempt_count"])
                self.assertIsNone(summary["attempt_count"])

    def test_deleted_preexisting_metric_is_unknown_for_reuse_or_fresh_run(self) -> None:
        for explicit_reuse in (True, False):
            with self.subTest(explicit_reuse=explicit_reuse), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                paths = self._base(root)
                stale_paths = [
                    self._write_stage_metric(paths["cycle"], metric)
                    for metric in (
                        {"stage_id": "writer-r1", "attempt_id": "attempt-001", "role": "writer"},
                        {"stage_id": "reviewer-r1", "attempt_id": "attempt-001", "role": "reviewer"},
                    )
                ]

                def bridge(argv: Sequence[str] | None) -> int:
                    self._publish_bridge_outputs(list(argv or []))
                    return 0

                def downstream(argv: Sequence[str] | None) -> int:
                    stale_paths[0].unlink()
                    self._record_downstream_timer(
                        paths["timer"],
                        paths["cycle"],
                        write_fresh_metrics=not explicit_reuse,
                        explicit_reuse=explicit_reuse,
                        stage_round=2,
                    )
                    final_artifact = Path(_value(list(argv or []), "--final-artifact"))
                    final_artifact.parent.mkdir(parents=True, exist_ok=True)
                    final_artifact.write_text("# Signed off\n", encoding="utf-8")
                    return 0

                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    code = run_standard_production_iteration.main(
                        self._argv(root, paths), bridge_runner=bridge, downstream_runner=downstream
                    )
                self.assertEqual(0, code)
                summary = json.loads(
                    (paths["runtime"] / "standard-production-iteration-summary.json").read_text(encoding="utf-8")
                )
                self.assertIsNone(summary["downstream_attempt_count"])
                self.assertIsNone(summary["attempt_count"])

    def test_metric_payload_identity_must_match_attempt_path(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._base(root)

            def bridge(argv: Sequence[str] | None) -> int:
                self._publish_bridge_outputs(list(argv or []))
                return 0

            def downstream(argv: Sequence[str] | None) -> int:
                misplaced = (
                    paths["cycle"]
                    / "attempts/writer-r1/attempt-001/metrics.json"
                )
                misplaced.parent.mkdir(parents=True, exist_ok=True)
                misplaced.write_text(
                    json.dumps(
                        {"stage_id": "writer-r2", "attempt_id": "attempt-001", "role": "writer"}
                    ),
                    encoding="utf-8",
                )
                self._record_downstream_timer(
                    paths["timer"], paths["cycle"], write_fresh_metrics=False
                )
                final_artifact = Path(_value(list(argv or []), "--final-artifact"))
                final_artifact.parent.mkdir(parents=True, exist_ok=True)
                final_artifact.write_text("# Signed off\n", encoding="utf-8")
                return 0

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = run_standard_production_iteration.main(
                    self._argv(root, paths), bridge_runner=bridge, downstream_runner=downstream
                )
            self.assertEqual(0, code)
            summary = json.loads(
                (paths["runtime"] / "standard-production-iteration-summary.json").read_text(encoding="utf-8")
            )
            self.assertIsNone(summary["attempt_count"])

    def test_source_reuse_conflicts_with_fresh_summary(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._base(root)

            def bridge(argv: Sequence[str] | None) -> int:
                self._publish_bridge_outputs(list(argv or []))
                return 0

            def downstream(_argv: Sequence[str] | None) -> int:
                self._record_downstream_timer(
                    paths["timer"], paths["cycle"], compile_status="failed"
                )
                timer_payload = json.loads(paths["timer"].read_text(encoding="utf-8"))
                timer_payload["phases"][-2]["metrics"]["summary"] = {"status": "reused"}
                paths["timer"].write_text(json.dumps(timer_payload), encoding="utf-8")
                return 2

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = run_standard_production_iteration.main(
                    self._argv(root, paths), bridge_runner=bridge, downstream_runner=downstream
                )
            self.assertEqual(2, code)
            summary = json.loads(
                (paths["runtime"] / "standard-production-iteration-summary.json").read_text(encoding="utf-8")
            )
            self.assertIsNone(summary["downstream_attempt_count"])
            self.assertIsNone(summary["attempt_count"])

    def test_fresh_source_summary_counts_follow_phase_lifecycle(self) -> None:
        cases = (
            ("fresh-reused-zero", {"status": "reused", "attempt_count": 0, "retry_count": 0}, "completed", False, None, None),
            ("fresh-completed-zero", {"status": "completed", "attempt_count": 0}, "completed", False, None, None),
            ("fresh-completed-one", {"status": "completed", "attempt_count": 1}, "completed", False, 1, 3),
            ("completed-retry-gt-attempt", {"status": "completed", "attempt_count": 1, "retry_count": 2}, "completed", False, None, None),
            ("failed-zero-incomplete", {"status": "failed", "attempt_count": 0}, "failed", False, None, None),
            ("failed-zero-complete", {"status": "failed", "attempt_count": 0}, "failed", True, 0, 2),
            ("failed-zero-positive-retry", {"status": "failed", "attempt_count": 0, "retry_count": 1}, "failed", True, None, None),
        )
        for (
            name,
            source_summary,
            phase_status,
            completeness,
            expected_downstream,
            expected_total,
        ) in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                paths = self._base(root)

                def bridge(argv: Sequence[str] | None) -> int:
                    self._publish_bridge_outputs(list(argv or []))
                    return 0

                def downstream(_argv: Sequence[str] | None) -> int:
                    summary_path = paths["cycle"] / "source-review-summary.json"
                    summary_path.parent.mkdir(parents=True, exist_ok=True)
                    summary_path.write_text(json.dumps(source_summary), encoding="utf-8")
                    now_ms = time.time_ns() // 1_000_000
                    source_metrics: dict[str, object] = {"summary": source_summary}
                    if completeness:
                        source_metrics["model_attempt_evidence_complete"] = True
                    phases: list[dict[str, object]] = [
                        {
                            "phase": "source-review",
                            "status": phase_status,
                            "started_epoch_ms": now_ms,
                            "metrics": source_metrics,
                        }
                    ]
                    if phase_status == "completed":
                        phases.append(
                            {
                                "phase": "compile-preflight",
                                "status": "failed",
                                "started_epoch_ms": now_ms,
                                "metrics": {},
                            }
                        )
                    paths["timer"].write_text(json.dumps({"phases": phases}), encoding="utf-8")
                    return 2

                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    code = run_standard_production_iteration.main(
                        self._argv(root, paths), bridge_runner=bridge, downstream_runner=downstream
                    )
                self.assertEqual(2, code)
                summary = json.loads(
                    (paths["runtime"] / "standard-production-iteration-summary.json").read_text(encoding="utf-8")
                )
                self.assertEqual(expected_downstream, summary["downstream_attempt_count"])
                self.assertEqual(expected_total, summary["attempt_count"])

    def test_unchanged_source_summary_with_canonical_reuse_counts_zero(self) -> None:
        for contradictory in (False, True):
            with self.subTest(contradictory=contradictory), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                paths = self._base(root)
                persisted = paths["cycle"] / "source-review-summary.json"
                persisted.parent.mkdir(parents=True, exist_ok=True)
                persisted.write_text('{"status":"completed","attempt_count":1}\n', encoding="utf-8")
                original = persisted.read_bytes()
                expected_review = paths["handoff"] / "source-assertion-review.json"

                def bridge(argv: Sequence[str] | None) -> int:
                    self._publish_bridge_outputs(list(argv or []))
                    expected_review.write_text("{}\n", encoding="utf-8")
                    return 0

                def downstream(argv: Sequence[str] | None) -> int:
                    self._record_downstream_timer(
                        paths["timer"],
                        paths["cycle"],
                        source_reuse=True,
                        source_review_path=expected_review,
                    )
                    if contradictory:
                        timer_payload = json.loads(paths["timer"].read_text(encoding="utf-8"))
                        timer_payload["phases"][-3]["metrics"]["summary"]["attempt_count"] = 1
                        paths["timer"].write_text(json.dumps(timer_payload), encoding="utf-8")
                    final_artifact = Path(_value(list(argv or []), "--final-artifact"))
                    final_artifact.parent.mkdir(parents=True, exist_ok=True)
                    final_artifact.write_text("# Signed off\n", encoding="utf-8")
                    return 0

                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    code = run_standard_production_iteration.main(
                        self._argv(root, paths), bridge_runner=bridge, downstream_runner=downstream
                    )
                self.assertEqual(0, code)
                self.assertEqual(original, persisted.read_bytes())
                summary = json.loads(
                    (paths["runtime"] / "standard-production-iteration-summary.json").read_text(encoding="utf-8")
                )
                if contradictory:
                    self.assertIsNone(summary["attempt_count"])
                else:
                    self.assertEqual(2, summary["downstream_attempt_count"])
                    self.assertEqual(4, summary["attempt_count"])

    def test_source_reuse_requires_unchanged_expected_review_artifact(self) -> None:
        for mode in ("fresh", "overwritten", "deleted", "foreign"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                paths = self._base(root)
                persisted = paths["cycle"] / "source-review-summary.json"
                persisted.parent.mkdir(parents=True, exist_ok=True)
                persisted.write_text('{"status":"completed","attempt_count":1}\n', encoding="utf-8")
                expected_review = paths["handoff"] / "source-assertion-review.json"
                foreign_review = paths["cycle"] / "foreign-source-assertion-review.json"

                def bridge(argv: Sequence[str] | None) -> int:
                    self._publish_bridge_outputs(list(argv or []))
                    if mode != "fresh":
                        expected_review.write_text('{"decision":"old"}\n', encoding="utf-8")
                    return 0

                def downstream(argv: Sequence[str] | None) -> int:
                    receipt_path = expected_review
                    if mode == "overwritten":
                        expected_review.write_text('{"decision":"new"}\n', encoding="utf-8")
                    elif mode == "deleted":
                        expected_review.unlink()
                        receipt_path = foreign_review
                    elif mode == "foreign":
                        receipt_path = foreign_review
                    self._record_downstream_timer(
                        paths["timer"],
                        paths["cycle"],
                        source_reuse=True,
                        source_review_path=receipt_path,
                    )
                    final_artifact = Path(_value(list(argv or []), "--final-artifact"))
                    final_artifact.parent.mkdir(parents=True, exist_ok=True)
                    final_artifact.write_text("# Signed off\n", encoding="utf-8")
                    return 0


                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    code = run_standard_production_iteration.main(
                        self._argv(root, paths), bridge_runner=bridge, downstream_runner=downstream
                    )
                self.assertEqual(0, code)
                summary = json.loads(
                    (paths["runtime"] / "standard-production-iteration-summary.json").read_text(encoding="utf-8")
                )
                self.assertIsNone(summary["downstream_attempt_count"])
                self.assertIsNone(summary["attempt_count"])

    def test_rewritten_preexisting_timer_phase_is_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._base(root)
            paths["timer"].write_text(
                json.dumps(
                    {
                        "phases": [
                            {
                                "phase": "routing-preflight",
                                "status": "completed",
                                "started_epoch_ms": 1,
                                "metrics": {},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            def bridge(argv: Sequence[str] | None) -> int:
                self._publish_bridge_outputs(list(argv or []))
                return 0

            def downstream(argv: Sequence[str] | None) -> int:
                self._record_downstream_timer(paths["timer"], paths["cycle"])
                timer_payload = json.loads(paths["timer"].read_text(encoding="utf-8"))
                timer_payload["phases"][0]["status"] = "rewritten"
                paths["timer"].write_text(json.dumps(timer_payload), encoding="utf-8")
                final_artifact = Path(_value(list(argv or []), "--final-artifact"))
                final_artifact.parent.mkdir(parents=True, exist_ok=True)
                final_artifact.write_text("# Signed off\n", encoding="utf-8")
                return 0

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = run_standard_production_iteration.main(
                    self._argv(root, paths), bridge_runner=bridge, downstream_runner=downstream
                )
            self.assertEqual(0, code)
            summary = json.loads(
                (paths["runtime"] / "standard-production-iteration-summary.json").read_text(encoding="utf-8")
            )
            self.assertIsNone(summary["attempt_count"])

    def test_foreign_or_role_inconsistent_stage_metric_makes_counts_unknown(self) -> None:
        invalid_metrics = (
            {"stage_id": "observer-r1", "attempt_id": "attempt-001", "role": "observer"},
            {"stage_id": "reviewer-r1", "attempt_id": "attempt-001", "role": "writer"},
            {"stage_id": "writer-r1", "attempt_id": "attempt-000", "role": "writer"},
        )
        for invalid_metric in invalid_metrics:
            with self.subTest(metric=invalid_metric), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                paths = self._base(root)

                def bridge(argv: Sequence[str] | None) -> int:
                    self._publish_bridge_outputs(list(argv or []))
                    return 0

                def downstream(argv: Sequence[str] | None) -> int:
                    self._write_stage_metric(paths["cycle"], invalid_metric)
                    now_ms = time.time_ns() // 1_000_000
                    paths["timer"].write_text(
                        json.dumps(
                            {
                                "phases": [
                                    {
                                        "phase": "source-review",
                                        "status": "completed",
                                        "started_epoch_ms": now_ms,
                                        "metrics": {"summary": {"attempt_count": 1}},
                                    },
                                    {
                                        "phase": "compile-preflight",
                                        "status": "completed",
                                        "started_epoch_ms": now_ms,
                                        "metrics": {},
                                    },
                                    {
                                        "phase": "writer-reviewer",
                                        "status": "completed",
                                        "started_epoch_ms": now_ms,
                                        "metrics": {"stage_metrics": [invalid_metric]},
                                    },
                                ]
                            }
                        ),
                        encoding="utf-8",
                    )
                    final_artifact = Path(_value(list(argv or []), "--final-artifact"))
                    final_artifact.parent.mkdir(parents=True, exist_ok=True)
                    final_artifact.write_text("# Signed off\n", encoding="utf-8")
                    return 0

                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    code = run_standard_production_iteration.main(
                        self._argv(root, paths), bridge_runner=bridge, downstream_runner=downstream
                    )
                self.assertEqual(0, code)
                summary = json.loads(
                    (paths["runtime"] / "standard-production-iteration-summary.json").read_text(encoding="utf-8")
                )
                self.assertIsNone(summary["attempt_count"])
                self.assertEqual("unknown", summary["lifecycle_count_evidence"]["status"])

    def test_promotion_phase_without_writer_reviewer_evidence_is_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._base(root)

            def bridge(argv: Sequence[str] | None) -> int:
                self._publish_bridge_outputs(list(argv or []))
                return 0

            def downstream(_argv: Sequence[str] | None) -> int:
                now_ms = time.time_ns() // 1_000_000
                paths["timer"].write_text(
                    json.dumps(
                        {
                            "phases": [
                                {
                                    "phase": "source-review",
                                    "status": "completed",
                                    "started_epoch_ms": now_ms,
                                    "metrics": {"summary": {"attempt_count": 1}},
                                },
                                {
                                    "phase": "compile-preflight",
                                    "status": "completed",
                                    "started_epoch_ms": now_ms,
                                    "metrics": {},
                                },
                                {
                                    "phase": "promotion",
                                    "status": "failed",
                                    "started_epoch_ms": now_ms,
                                    "metrics": {},
                                },
                            ]
                        }
                    ),
                    encoding="utf-8",
                )
                return 2

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = run_standard_production_iteration.main(
                    self._argv(root, paths), bridge_runner=bridge, downstream_runner=downstream
                )
            self.assertEqual(2, code)
            summary = json.loads(
                (paths["runtime"] / "standard-production-iteration-summary.json").read_text(encoding="utf-8")
            )
            self.assertIsNone(summary["downstream_attempt_count"])
            self.assertIsNone(summary["attempt_count"])

    def test_preexisting_handoff_blocks_before_bridge_and_is_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._base(root)
            self._publish_bridge_outputs(
                [
                    "--handoff-dir",
                    str(paths["handoff"]),
                    "--context",
                    str(paths["context"]),
                    "--publication-owner-token",
                    "33333333-3333-4333-8333-333333333333",
                    "--summary-output",
                    str(
                        paths["runtime"]
                        / "standard-scope-bridge-summary.json"
                    ),
                ],
                write_summary=False,
            )
            marker = paths["handoff"] / "existing.txt"
            marker.write_text("keep", encoding="utf-8")
            bridge_calls: list[list[str]] = []

            def bridge(argv: Sequence[str] | None) -> int:
                bridge_calls.append(list(argv or []))
                return 2

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = run_standard_production_iteration.main(
                    self._argv(root, paths),
                    bridge_runner=bridge,
                    downstream_runner=lambda _argv: 0,
                )

            self.assertEqual(2, code)
            self.assertEqual([], bridge_calls)
            self.assertEqual("keep", marker.read_text(encoding="utf-8"))
            self.assertFalse(paths["runtime"].exists())

    def test_materialized_package_mismatch_stops_before_downstream(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._base(root)
            downstream_calls: list[list[str]] = []

            def bridge(argv: Sequence[str] | None) -> int:
                actual = list(argv or [])
                self._publish_bridge_outputs(actual, package_id="WP-08")
                return 0

            def downstream(argv: Sequence[str] | None) -> int:
                actual = list(argv or [])
                downstream_calls.append(actual)
                final_artifact = Path(_value(actual, "--final-artifact"))
                final_artifact.parent.mkdir(parents=True, exist_ok=True)
                final_artifact.write_text("# Signed off\n", encoding="utf-8")
                return 0

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = run_standard_production_iteration.main(
                    self._argv(root, paths),
                    bridge_runner=bridge,
                    downstream_runner=downstream,
                )

            self.assertEqual(2, code)
            self.assertEqual([], downstream_calls)
            summary = json.loads(
                (
                    paths["runtime"]
                    / "standard-production-iteration-summary.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual("terminal-failed", summary["status"])
            self.assertIn("package_id mismatch", summary["error"])

    def test_post_downstream_reporting_failure_does_not_invalidate_success(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._base(root)
            downstream_calls: list[list[str]] = []

            def bridge(argv: Sequence[str] | None) -> int:
                self._publish_bridge_outputs(list(argv or []))
                return 0

            def downstream(argv: Sequence[str] | None) -> int:
                actual = list(argv or [])
                downstream_calls.append(actual)
                final_artifact = Path(_value(actual, "--final-artifact"))
                final_artifact.parent.mkdir(parents=True, exist_ok=True)
                final_artifact.write_text("# Signed off\n", encoding="utf-8")
                return 0

            with (
                patch.object(
                    run_standard_production_iteration,
                    "_write_json_atomic",
                    side_effect=OSError("summary disk failure"),
                ),
                redirect_stdout(io.StringIO()),
                redirect_stderr(io.StringIO()),
            ):
                code = run_standard_production_iteration.main(
                    self._argv(root, paths),
                    bridge_runner=bridge,
                    downstream_runner=downstream,
                )

            self.assertEqual(0, code)
            self.assertEqual(1, len(downstream_calls))

    def test_downstream_success_without_final_artifact_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._base(root)

            def bridge(argv: Sequence[str] | None) -> int:
                self._publish_bridge_outputs(list(argv or []))
                return 0

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = run_standard_production_iteration.main(
                    self._argv(root, paths),
                    bridge_runner=bridge,
                    downstream_runner=lambda _argv: 0,
                )

            self.assertEqual(2, code)
            summary = json.loads(
                (
                    paths["runtime"]
                    / "standard-production-iteration-summary.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual("terminal-failed", summary["status"])
            self.assertIn("without the final artifact", summary["error"])

    def test_published_handoff_survives_missing_bridge_summary(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._base(root)

            def bridge(argv: Sequence[str] | None) -> int:
                self._publish_bridge_outputs(
                    list(argv or []), write_summary=False
                )
                return 0

            def downstream(argv: Sequence[str] | None) -> int:
                actual = list(argv or [])
                final_artifact = Path(_value(actual, "--final-artifact"))
                final_artifact.parent.mkdir(parents=True, exist_ok=True)
                final_artifact.write_text("# Signed off\n", encoding="utf-8")
                return 0

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = run_standard_production_iteration.main(
                    self._argv(root, paths),
                    bridge_runner=bridge,
                    downstream_runner=downstream,
                )

            self.assertEqual(0, code)
            summary = json.loads(
                (
                    paths["runtime"]
                    / "standard-production-iteration-summary.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual("completed", summary["status"])
            self.assertTrue(summary["reporting_errors"])
            self.assertIsNone(summary["attempt_count"])
            self.assertIsNone(summary["retry_count"])
            self.assertEqual(
                "unknown", summary["lifecycle_count_evidence"]["status"]
            )

    def test_published_handoff_survives_bridge_exception_after_commit(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._base(root)
            downstream_calls: list[list[str]] = []

            def bridge(argv: Sequence[str] | None) -> int:
                self._publish_bridge_outputs(
                    list(argv or []), write_summary=False
                )
                raise RuntimeError("summary reporting failed after publication")

            def downstream(argv: Sequence[str] | None) -> int:
                actual = list(argv or [])
                downstream_calls.append(actual)
                final_artifact = Path(_value(actual, "--final-artifact"))
                final_artifact.parent.mkdir(parents=True, exist_ok=True)
                final_artifact.write_text("# Signed off\n", encoding="utf-8")
                return 0

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = run_standard_production_iteration.main(
                    self._argv(root, paths),
                    bridge_runner=bridge,
                    downstream_runner=downstream,
                )

            self.assertEqual(0, code)
            self.assertEqual(1, len(downstream_calls))
            summary = json.loads(
                (
                    paths["runtime"]
                    / "standard-production-iteration-summary.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual("completed", summary["status"])
            self.assertIsNone(summary["attempt_count"])
            self.assertIsNone(summary["retry_count"])
            self.assertTrue(
                any(
                    item["error_type"] == "RuntimeError"
                    for item in summary["reporting_errors"]
                )
            )

    def test_damaged_bridge_summary_recovers_counts_from_phase_summaries(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._base(root)

            def bridge(argv: Sequence[str] | None) -> int:
                actual = list(argv or [])
                self._publish_bridge_outputs(actual, write_summary=False)
                runtime = Path(_value(actual, "--runtime-dir"))
                for phase in ("scope-analysis", "semantic-design"):
                    phase_summary = runtime / phase / "summary.json"
                    phase_summary.parent.mkdir(parents=True, exist_ok=True)
                    phase_summary.write_text(
                        json.dumps(
                            {
                                "model_invoked": True,
                                "lifecycle": {
                                    "runner_attempt_count": 1,
                                    "runner_retry_count": 0,
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                bridge_summary = Path(_value(actual, "--summary-output"))
                bridge_summary.write_text("{broken", encoding="utf-8")
                return 0

            def downstream(argv: Sequence[str] | None) -> int:
                actual = list(argv or [])
                final_artifact = Path(_value(actual, "--final-artifact"))
                final_artifact.parent.mkdir(parents=True, exist_ok=True)
                final_artifact.write_text("# Signed off\n", encoding="utf-8")
                self._record_downstream_timer(paths["timer"], paths["cycle"])
                return 0

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = run_standard_production_iteration.main(
                    self._argv(root, paths),
                    bridge_runner=bridge,
                    downstream_runner=downstream,
                )

            self.assertEqual(0, code)
            summary = json.loads(
                (
                    paths["runtime"]
                    / "standard-production-iteration-summary.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(5, summary["attempt_count"])
            self.assertEqual(0, summary["retry_count"])
            self.assertEqual(
                "recovered", summary["lifecycle_count_evidence"]["status"]
            )
            self.assertEqual(
                {
                    "scope-analysis": "phase-summary",
                    "semantic-design": "phase-summary",
                },
                summary["bridge_lifecycle_count_evidence"]["phase_sources"],
            )

    def test_missing_bridge_summary_recovers_counts_from_current_timer(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._base(root)

            def bridge(argv: Sequence[str] | None) -> int:
                actual = list(argv or [])
                self._publish_bridge_outputs(actual, write_summary=False)
                now_ms = time.time_ns() // 1_000_000
                phases = []
                for phase in ("scope-analysis", "semantic-design"):
                    phases.append(
                        {
                            "phase": phase,
                            "started_epoch_ms": now_ms,
                            "metrics": {
                                "lifecycle": {
                                    "runner_attempt_count": 1,
                                    "runner_retry_count": 0,
                                }
                            },
                        }
                    )
                Path(_value(actual, "--timer")).write_text(
                    json.dumps({"phases": phases}), encoding="utf-8"
                )
                return 0

            def downstream(argv: Sequence[str] | None) -> int:
                actual = list(argv or [])
                final_artifact = Path(_value(actual, "--final-artifact"))
                final_artifact.parent.mkdir(parents=True, exist_ok=True)
                final_artifact.write_text("# Signed off\n", encoding="utf-8")
                self._record_downstream_timer(paths["timer"], paths["cycle"])
                return 0

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = run_standard_production_iteration.main(
                    self._argv(root, paths),
                    bridge_runner=bridge,
                    downstream_runner=downstream,
                )

            self.assertEqual(0, code)
            summary = json.loads(
                (
                    paths["runtime"]
                    / "standard-production-iteration-summary.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(5, summary["attempt_count"])
            self.assertEqual(0, summary["retry_count"])
            self.assertEqual(
                {
                    "scope-analysis": "timer",
                    "semantic-design": "timer",
                },
                summary["bridge_lifecycle_count_evidence"]["phase_sources"],
            )

    def test_bridge_timer_recovery_rejects_stale_rewritten_or_duplicate_phases(self) -> None:
        for mode in ("stale-future", "rewritten-prefix", "duplicate-current"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                paths = self._base(root)
                future = time.time_ns() // 1_000_000 + 60_000
                if mode == "stale-future":
                    initial_phases = [
                        {
                            "phase": phase,
                            "started_epoch_ms": future,
                            "metrics": {
                                "lifecycle": {
                                    "runner_attempt_count": 1,
                                    "runner_retry_count": 0,
                                }
                            },
                        }
                        for phase in ("scope-analysis", "semantic-design")
                    ]
                elif mode == "rewritten-prefix":
                    initial_phases = [
                        {
                            "phase": "routing-preflight",
                            "status": "completed",
                            "started_epoch_ms": 1,
                            "metrics": {},
                        }
                    ]
                else:
                    initial_phases = []
                paths["timer"].write_text(
                    json.dumps({"status": "running", "phases": initial_phases}),
                    encoding="utf-8",
                )

                def bridge(argv: Sequence[str] | None) -> int:
                    self._publish_bridge_outputs(list(argv or []), write_summary=False)
                    if mode == "rewritten-prefix":
                        payload = json.loads(paths["timer"].read_text(encoding="utf-8"))
                        payload["phases"][0]["status"] = "rewritten"
                        paths["timer"].write_text(json.dumps(payload), encoding="utf-8")
                    elif mode == "duplicate-current":
                        now_ms = time.time_ns() // 1_000_000
                        phases = []
                        for phase in ("scope-analysis", "scope-analysis", "semantic-design"):
                            phases.append(
                                {
                                    "phase": phase,
                                    "started_epoch_ms": now_ms,
                                    "metrics": {
                                        "lifecycle": {
                                            "runner_attempt_count": 1,
                                            "runner_retry_count": 0,
                                        }
                                    },
                                }
                            )
                        paths["timer"].write_text(json.dumps({"phases": phases}), encoding="utf-8")
                    return 0

                def downstream(argv: Sequence[str] | None) -> int:
                    final_artifact = Path(_value(list(argv or []), "--final-artifact"))
                    final_artifact.parent.mkdir(parents=True, exist_ok=True)
                    final_artifact.write_text("# Signed off\n", encoding="utf-8")
                    return 0

                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    code = run_standard_production_iteration.main(
                        self._argv(root, paths), bridge_runner=bridge, downstream_runner=downstream
                    )
                self.assertEqual(0, code)
                summary = json.loads(
                    (paths["runtime"] / "standard-production-iteration-summary.json").read_text(encoding="utf-8")
                )
                self.assertIsNone(summary["bridge_attempt_count"])
                self.assertEqual("unknown", summary["bridge_lifecycle_count_evidence"]["status"])

    def test_published_receipt_must_match_current_prepared_context(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._base(root)
            downstream_calls: list[list[str]] = []

            def bridge(argv: Sequence[str] | None) -> int:
                actual = list(argv or [])
                self._publish_bridge_outputs(actual)
                receipt_path = (
                    Path(_value(actual, "--handoff-dir"))
                    / "semantic-design-bridge-receipt.json"
                )
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                receipt["prepared_context_sha256"] = "0" * 64
                receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
                return 0

            def downstream(argv: Sequence[str] | None) -> int:
                downstream_calls.append(list(argv or []))
                return 0

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = run_standard_production_iteration.main(
                    self._argv(root, paths),
                    bridge_runner=bridge,
                    downstream_runner=downstream,
                )

            self.assertEqual(2, code)
            self.assertEqual([], downstream_calls)

    def test_foreign_bridge_publication_is_not_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._base(root)
            downstream_calls: list[list[str]] = []

            def bridge(argv: Sequence[str] | None) -> int:
                actual = list(argv or [])
                self._publish_bridge_outputs(actual)
                receipt_path = (
                    Path(_value(actual, "--handoff-dir"))
                    / "semantic-design-bridge-receipt.json"
                )
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                receipt["publication_owner_token"] = (
                    "22222222-2222-4222-8222-222222222222"
                )
                receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
                return 2

            def downstream(argv: Sequence[str] | None) -> int:
                downstream_calls.append(list(argv or []))
                return 0

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = run_standard_production_iteration.main(
                    self._argv(root, paths),
                    bridge_runner=bridge,
                    downstream_runner=downstream,
                )

            self.assertEqual(2, code)
            self.assertEqual([], downstream_calls)
            summary = json.loads(
                (
                    paths["runtime"]
                    / "standard-production-iteration-summary.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual("terminal-failed", summary["status"])

    def test_invalid_ft_slug_creates_no_runtime_or_handoff_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._base(root)
            paths["context"].write_text(
                json.dumps({"package_id": "WP-07", "ft_slug": "C:"}),
                encoding="utf-8",
            )
            bridge_calls: list[list[str]] = []

            def bridge(argv: Sequence[str] | None) -> int:
                bridge_calls.append(list(argv or []))
                return 0

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = run_standard_production_iteration.main(
                    self._argv(root, paths),
                    bridge_runner=bridge,
                    downstream_runner=lambda _argv: 0,
                )

            self.assertEqual(2, code)
            self.assertEqual([], bridge_calls)
            self.assertFalse(paths["runtime"].exists())
            self.assertFalse(paths["handoff"].exists())

    def test_path_error_is_normalized_to_terminal_json(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paths = self._base(root)
            arguments = self._argv(root, paths)
            arguments[arguments.index("--context") + 1] = str(
                root.parent / "outside-context.json"
            )
            stderr = io.StringIO()

            with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
                code = run_standard_production_iteration.main(arguments)

            self.assertEqual(2, code)
            payload = json.loads(stderr.getvalue())
            self.assertEqual("terminal-failed", payload["status"])


if __name__ == "__main__":
    unittest.main()
