from __future__ import annotations

import hashlib
import importlib
import json
import sys
import tempfile
import unittest
from contextlib import ExitStack, contextmanager
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
H64 = (
    ROOT
    / "fts"
    / "AutoFin"
    / "work"
    / "stage-handoffs"
    / "64-application-card-additional-income-postfinal-v2-source-provenance-terminal-state-remediation"
)


@contextmanager
def patched(module: ModuleType, **values: object):
    with ExitStack() as stack:
        for name, value in values.items():
            stack.enter_context(patch.object(module, name, value))
        yield


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class H64TerminalContractsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # H64 scripts use sibling imports because they are executable artifacts.
        # Load exactly that sibling set, never a same-named module from H61-H63.
        cls._saved_modules: dict[str, ModuleType] = {}
        cls._local_names = {path.stem for path in H64.glob("*.py")}
        local_names = cls._local_names
        for name in local_names:
            existing = sys.modules.pop(name, None)
            if existing is not None:
                cls._saved_modules[name] = existing
        sys.path.insert(0, str(H64))
        try:
            cls.update = importlib.import_module("update_workflow_state")
            cls.finalizer = importlib.import_module("finalize_h64_terminal")
            cls.orchestrator = importlib.import_module("run_h64_benchmark_once")
        finally:
            sys.path.remove(str(H64))
        for module in (cls.update, cls.finalizer, cls.orchestrator):
            cls.assert_h64_module(module)

    @classmethod
    def tearDownClass(cls) -> None:
        for name in cls._local_names:
            sys.modules.pop(name, None)
        sys.modules.update(cls._saved_modules)

    @staticmethod
    def assert_h64_module(module: ModuleType) -> None:
        path = Path(module.__file__).resolve()
        if path.parent != H64.resolve():
            raise AssertionError(f"loaded a non-H64 module: {path}")

    def update_paths(self, root: Path) -> dict[str, object]:
        ft_root = root / "fts" / "AutoFin"
        handoff = ft_root / "work" / "stage-handoffs" / "h64-test"
        handoff.mkdir(parents=True)
        return {
            "ROOT": root,
            "FT_ROOT": ft_root,
            "HANDOFF": handoff,
            "HANDOFF_NAME": handoff.name,
            "PREFIX": f"work/stage-handoffs/{handoff.name}",
            "WORKFLOW": handoff / "workflow-state.yaml",
            "MANIFEST": handoff / "source-assertions.json",
            "GATE": handoff / "source-gate-validation.json",
            "RECEIPT": handoff / "source-assertion-review.json",
            "REVIEW_SUMMARY": handoff / "source-reviewer-exec-summary.json",
            "REVIEW_CONTEXT": handoff / "source-review-context-report.json",
            "REVIEW_SCHEMA": handoff / "source-review-output-schema.json",
            "REVIEW_EVENTS": handoff / "source-reviewer-exec-events.ndjson",
            "REVIEW_STDERR": handoff / "source-reviewer-exec-stderr.log",
            "CANARY_BINDING": handoff / "source-review-canary-binding.json",
            "CANARY_POSTCHECK": handoff / "source-review-canary-postcheck.json",
            "CANDIDATE": handoff / "architecture-candidate-manifest.json",
            "PREFLIGHT": handoff / "remediation-preflight.json",
        }

    def finalizer_paths(self, root: Path) -> dict[str, object]:
        handoff = root / "handoff"
        handoff.mkdir(parents=True)
        return {
            "ROOT": root,
            "HANDOFF": handoff,
            "SCRIPT": handoff / "finalize_h64_terminal.py",
            "CANARY_DIR": root / "canary",
            "CYCLE": root / "cycle",
            "PRODUCTION": root / "production.md",
            "PREQUALIFICATION": handoff / "prequalification-manifest.json",
            "RUN_RESERVATION": handoff / "run-reservation.json",
            "FINALIZER_RESERVATION": handoff / "terminal-finalizer.reserved.json",
            "ORCHESTRATION_EVENTS": handoff / "h64-orchestration-events.ndjson",
            "WORKFLOW": handoff / "workflow-state.yaml",
            "QUALIFICATION_PERFORMANCE": handoff / "qualification-performance.json",
            "TERMINAL_FINDINGS": handoff / "terminal-findings.md",
            "TERMINAL_RECEIPT": handoff / "terminal-run-receipt.json",
        }

    def prepare_reservations(self, paths: dict[str, object]) -> None:
        prequalification = paths["PREQUALIFICATION"]
        run_reservation = paths["RUN_RESERVATION"]
        finalizer_reservation = paths["FINALIZER_RESERVATION"]
        assert isinstance(prequalification, Path)
        assert isinstance(run_reservation, Path)
        assert isinstance(finalizer_reservation, Path)
        write_json(prequalification, {"status": "passed"})
        digest = sha256(prequalification)
        write_json(
            run_reservation,
            {
                "status": "reserved",
                "qualification_id": self.finalizer.QUALIFICATION_ID,
                "prequalification_sha256": digest,
                "max_attempts": 1,
            },
        )
        write_json(
            finalizer_reservation,
            {
                "status": "reserved",
                "qualification_id": self.finalizer.QUALIFICATION_ID,
                "prequalification_sha256": digest,
                "max_attempts": 1,
            },
        )

    def test_reservations_precede_first_event_and_do_not_start_a_process(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            handoff = root / "handoff"
            handoff.mkdir()
            prequalification = handoff / "prequalification-manifest.json"
            write_json(prequalification, {"status": "passed"})
            event_log = handoff / "events.ndjson"
            run_reservation = handoff / "run-reservation.json"
            finalizer_reservation = handoff / "terminal-finalizer.reserved.json"
            finalizer_source = handoff / "finalize_remediation_metrics.py"
            finalizer_source.write_text("# frozen\n", encoding="utf-8")
            blocked_subprocess = Mock(
                side_effect=AssertionError("offline reservation preflight started a process")
            )
            operations: list[Path] = []
            original_open = Path.open

            def tracking_open(path: Path, *args: object, **kwargs: object):
                mode = str(args[0]) if args else str(kwargs.get("mode", "r"))
                if path in {event_log, run_reservation, finalizer_reservation} and any(
                    marker in mode for marker in ("w", "a", "x", "+")
                ):
                    operations.append(path)
                return original_open(path, *args, **kwargs)

            values = {
                "ROOT": root,
                "HANDOFF": handoff,
                "HANDOFF_REPO": "handoff",
                "CYCLE": root / "cycle",
                "PRODUCTION": root / "production.md",
                "PYTHON": Path(sys.executable),
                "EVENT_LOG": event_log,
                "FINAL_METRICS": handoff / "full-chain-performance.json",
                "TERMINAL_FINDINGS": handoff / "benchmark-terminal-findings.md",
                "BENCHMARK_EVENTS": handoff / "benchmark-events.ndjson",
                "FINALIZER_RESERVATION": finalizer_reservation,
                "RUN_RESERVATION": run_reservation,
                "FINALIZER_SOURCE": finalizer_source,
                "PRELOADED_FINALIZER_SHA256": sha256(finalizer_source),
                "PREQUALIFICATION_MANIFEST": prequalification,
                "CANARY_DIR": root / "canary",
                "CANARY_RESERVATION": root / "canary-reservation.json",
                "SOURCE_REVIEW_OUTPUTS": (),
                "QUALIFICATION_PERFORMANCE": handoff / "qualification-performance.json",
                "UNIVERSAL_TERMINAL_FINDINGS": handoff / "terminal-findings.md",
                "TERMINAL_RECEIPT": handoff / "terminal-run-receipt.json",
            }
            with patched(self.orchestrator, **values), patch.object(
                self.orchestrator, "validate_irreversible_preconditions", return_value={}
            ), patch.object(
                self.orchestrator, "validate_scope_artifact_manifest", return_value={}
            ), patch.object(
                self.orchestrator, "validate_current_descriptors", return_value={}
            ), patch.object(
                self.orchestrator, "validate_prior_attempt_snapshot", return_value={}
            ), patch.object(
                self.orchestrator,
                "validate_prequalification_manifest",
                return_value={"status": "passed"},
            ), patch.object(
                self.orchestrator.subprocess, "run", blocked_subprocess
            ), patch.object(Path, "open", tracking_open):
                self.orchestrator.require_clean_start()

            self.assertEqual(
                [finalizer_reservation, run_reservation, event_log], operations
            )
            blocked_subprocess.assert_not_called()
            finalizer_payload = json.loads(finalizer_reservation.read_text(encoding="utf-8"))
            run_payload = json.loads(run_reservation.read_text(encoding="utf-8"))
            for payload in (finalizer_payload, run_payload):
                self.assertEqual("reserved", payload["status"])
                self.assertEqual(self.finalizer.QUALIFICATION_ID, payload["qualification_id"])
                self.assertEqual(sha256(prequalification), payload["prequalification_sha256"])
                self.assertEqual(1, payload["max_attempts"])
            events = [
                json.loads(line)
                for line in event_log.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(["run-reserved", "orchestration-started"], [row["event"] for row in events])
            self.assertEqual(sha256(run_reservation), events[0]["run_reservation_sha256"])
            self.assertEqual(
                sha256(finalizer_reservation),
                events[0]["finalizer_reservation_sha256"],
            )

    def test_failure_workflow_is_blocked_with_reasons_and_artifact_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            values = self.update_paths(root)
            gate = values["GATE"]
            receipt = values["RECEIPT"]
            summary = values["REVIEW_SUMMARY"]
            workflow = values["WORKFLOW"]
            assert isinstance(gate, Path)
            assert isinstance(receipt, Path)
            assert isinstance(summary, Path)
            assert isinstance(workflow, Path)
            write_json(gate, {"status": "passed"})
            write_json(
                receipt,
                {
                    "version": 6,
                    "decision": "changes-required",
                    "assertion_reviews": [
                        {"assertion_id": "ASSERT-020", "verdict": "incorrect"}
                    ],
                },
            )
            write_json(summary, {"status": "completed"})

            with patched(self.update, **values):
                result = self.update.write_terminal_blocked_state(
                    trigger="source-reviewer",
                    return_code=1,
                    outcome_class="semantic-quality-stop",
                    error_type="ReviewRejected",
                    error="requirement-code provenance mismatch",
                )
                state = self.update.load_workflow_state(workflow)

            self.assertEqual("blocked-input", state["stage_status"])
            self.assertEqual("none", state["next_skill"])
            self.assertEqual("ft-scope-analyzer", state["current_stage"])
            self.assertTrue(state["blocking_reasons"])
            joined_reasons = "\n".join(state["blocking_reasons"])
            self.assertIn("semantic-quality-stop:source-reviewer:return-code-1", joined_reasons)
            self.assertIn("ASSERT-020", joined_reasons)
            review_state = state["source_assertion_review_state"]
            self.assertEqual(sha256(gate), review_state["source_gate_sha256"])
            self.assertEqual(sha256(receipt), review_state["receipt_sha256"])
            self.assertEqual(sha256(summary), review_state["review_summary_sha256"])
            self.assertEqual("ASSERT-020", review_state["incorrect_assertion_ids"])
            self.assertEqual(sha256(workflow), result["sha256"])

    def test_terminal_receipt_is_last_evidence_and_forbids_repeat(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            paths = self.finalizer_paths(root)
            self.prepare_reservations(paths)
            write_order: list[Path] = []

            def exclusive_json(path: Path, payload: dict[str, object]) -> None:
                write_order.append(path)
                with path.open("x", encoding="utf-8", newline="\n") as stream:
                    json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
                    stream.write("\n")

            def exclusive_text(path: Path, text: str) -> None:
                write_order.append(path)
                with path.open("x", encoding="utf-8", newline="\n") as stream:
                    stream.write(text)

            workflow_result = {
                "status": "blocked-input",
                "path": "handoff/workflow-state.yaml",
                "sha256": "a" * 64,
                "blocking_reasons": ["deterministic-gate-failure:source-gate:return-code-1"],
            }
            with patched(self.finalizer, **paths), patch.object(
                self.finalizer, "prequalification_binding", return_value=None
            ), patch.object(
                self.finalizer,
                "validate_prior_attempt_snapshot",
                return_value={
                    "subject_count": 7,
                    "file_count": 100,
                    "total_bytes": 1000,
                    "subject_set_sha256": "b" * 64,
                },
            ), patch.object(
                self.finalizer,
                "write_terminal_blocked_state",
                return_value=workflow_result,
            ), patch.object(
                self.finalizer, "write_json_exclusive", side_effect=exclusive_json
            ), patch.object(
                self.finalizer, "write_text_exclusive", side_effect=exclusive_text
            ), patch("builtins.print"):
                return_code = self.finalizer.finalize_terminal(
                    trigger="source-gate",
                    return_code=1,
                    benchmark_started=True,
                )
                receipt_path = paths["TERMINAL_RECEIPT"]
                performance_path = paths["QUALIFICATION_PERFORMANCE"]
                findings_path = paths["TERMINAL_FINDINGS"]
                assert isinstance(receipt_path, Path)
                assert isinstance(performance_path, Path)
                assert isinstance(findings_path, Path)
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                frozen = receipt_path.read_bytes()
                with self.assertRaisesRegex(
                    self.finalizer.TerminalReceiptError, "retry is forbidden"
                ):
                    self.finalizer.finalize_terminal(
                        trigger="source-gate",
                        return_code=1,
                        benchmark_started=True,
                    )

            self.assertEqual(1, return_code)
            self.assertEqual(
                [performance_path, findings_path, receipt_path], write_order
            )
            self.assertTrue(receipt["receipt_written_last"])
            evidence = {row["path"] for row in receipt["evidence"]}
            self.assertIn("handoff/qualification-performance.json", evidence)
            self.assertIn("handoff/terminal-findings.md", evidence)
            self.assertNotIn("handoff/terminal-run-receipt.json", evidence)
            self.assertEqual(frozen, receipt_path.read_bytes())

    def test_success_validates_signed_off_workflow_without_rewriting_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            paths = self.finalizer_paths(root)
            self.prepare_reservations(paths)
            production = paths["PRODUCTION"]
            workflow = paths["WORKFLOW"]
            receipt_path = paths["TERMINAL_RECEIPT"]
            assert isinstance(production, Path)
            assert isinstance(workflow, Path)
            assert isinstance(receipt_path, Path)
            production.write_text("signed off production\n", encoding="utf-8")
            original_workflow = b"signed-off immutable workflow\n"
            workflow.write_bytes(original_workflow)
            blocked_writer = Mock(
                side_effect=AssertionError("success must not write a blocked workflow")
            )
            signed_off = {
                "current_stage": "ft-test-case-iteration",
                "stage_status": "signed-off",
                "next_skill": "ft-ui-automation-prep",
            }

            with patched(self.finalizer, **paths), patch.object(
                self.finalizer, "prequalification_binding", return_value=None
            ), patch.object(
                self.finalizer,
                "validate_prior_attempt_snapshot",
                return_value={
                    "subject_count": 7,
                    "file_count": 100,
                    "total_bytes": 1000,
                    "subject_set_sha256": "b" * 64,
                },
            ), patch.object(
                self.finalizer, "load_workflow_state", return_value=signed_off
            ) as workflow_loader, patch.object(
                self.finalizer, "write_terminal_blocked_state", blocked_writer
            ), patch("builtins.print"):
                return_code = self.finalizer.finalize_terminal(
                    trigger="controlled-promotion",
                    return_code=0,
                    benchmark_started=True,
                )

            self.assertEqual(0, return_code)
            workflow_loader.assert_called_once_with(workflow)
            blocked_writer.assert_not_called()
            self.assertEqual(original_workflow, workflow.read_bytes())
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual("success-promoted", receipt["status"])
            self.assertEqual("success-promoted", receipt["outcome_class"])
            self.assertEqual("signed-off", receipt["workflow_terminalization"]["status"])
            self.assertEqual(sha256(workflow), receipt["workflow_terminalization"]["sha256"])


if __name__ == "__main__":
    unittest.main()
