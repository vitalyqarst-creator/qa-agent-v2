from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import ExitStack, contextmanager
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock, patch

from test_case_agent.review_cycle.stage_failure_contract import read_stage_failure
from tests.frozen_h64_h65_evidence import frozen_h64_h65_package_note


ROOT = Path(__file__).resolve().parents[1]
H64 = (
    ROOT
    / "fts"
    / "AutoFin"
    / "work"
    / "stage-handoffs"
    / "64-application-card-additional-income-postfinal-v2-source-provenance-terminal-state-remediation"
)
H65 = (
    ROOT
    / "fts"
    / "AutoFin"
    / "work"
    / "stage-handoffs"
    / "65-application-card-additional-income-postfinal-v2-canary-contract-remediation"
)
H64_MANIFEST = H64 / "source-assertions.json"
H64_RECEIPT = H64 / "source-assertion-review.json"
H65_MANIFEST = H65 / "source-assertions.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def load_unique(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@contextmanager
def patched_constants(module: ModuleType, values: dict[str, object]):
    with ExitStack() as stack:
        for name, value in values.items():
            stack.enter_context(patch.object(module, name, value))
        yield


class H65CompileReadyContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._local_names = {path.stem for path in H65.glob("*.py")}
        cls._saved_modules: dict[str, ModuleType] = {}
        for name in cls._local_names:
            existing = sys.modules.pop(name, None)
            if existing is not None:
                cls._saved_modules[name] = existing
        sys.path.insert(0, str(H65))
        try:
            cls.update = load_unique(
                "_h65_update_workflow_state_compile_ready_contract",
                H65 / "update_workflow_state.py",
            )
            cls.metrics = load_unique(
                "_h65_finalize_remediation_metrics_compile_ready_contract",
                H65 / "finalize_remediation_metrics.py",
            )
        finally:
            sys.path.remove(str(H65))
        for module in (cls.update, cls.metrics):
            if Path(module.__file__).resolve().parent != H65.resolve():
                raise AssertionError(f"loaded a non-H65 module: {module.__file__}")
        with frozen_h64_h65_package_note(ROOT):
            cls.manifest = cls.update.load_source_assertion_manifest(H65_MANIFEST, ROOT)

    @classmethod
    def tearDownClass(cls) -> None:
        sys.modules.pop("_h65_update_workflow_state_compile_ready_contract", None)
        sys.modules.pop("_h65_finalize_remediation_metrics_compile_ready_contract", None)
        for name in cls._local_names:
            sys.modules.pop(name, None)
        sys.modules.update(cls._saved_modules)

    def build_chain(
        self,
        directory: str,
        *,
        canary_summary_version: int,
    ) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        root = Path(directory).resolve()
        handoff = root / "handoff"
        canary_root = root / "canary"
        handoff.mkdir()
        canary_root.mkdir()

        paths = {
            "gate": handoff / "source-gate-validation.json",
            "receipt": handoff / "source-assertion-review.json",
            "summary": handoff / "source-reviewer-exec-summary.json",
            "context": handoff / "source-review-context-report.json",
            "review_schema": handoff / "source-review-output-schema.json",
            "events": handoff / "source-reviewer-exec-events.ndjson",
            "stderr": handoff / "source-reviewer-exec-stderr.log",
            "binding": handoff / "source-review-canary-binding.json",
            "postcheck": handoff / "source-review-canary-postcheck.json",
            "candidate": handoff / "architecture-candidate-manifest.json",
            "preflight": handoff / "remediation-preflight.json",
            "canary_summary": canary_root / "canary-summary.json",
            "canary_schema": canary_root / "output-schema.json",
            "review_session_log": handoff / "reviewer-session-log.source-assertion.md",
            "review_decision_log": handoff / "agent-decision-log.source-assertion-review.md",
        }
        typed_paths = {name: Path(path) for name, path in paths.items()}

        self.assertEqual(H64_MANIFEST.read_bytes(), H65_MANIFEST.read_bytes())
        typed_paths["receipt"].write_bytes(H64_RECEIPT.read_bytes())
        schema_bytes = b'{"additionalProperties":false,"type":"object"}\n'
        typed_paths["canary_schema"].write_bytes(schema_bytes)
        typed_paths["review_schema"].write_bytes(schema_bytes)
        typed_paths["events"].write_text("", encoding="utf-8")
        typed_paths["stderr"].write_text("", encoding="utf-8")
        typed_paths["review_session_log"].write_text(
            "# synthetic accepted reviewer session\n", encoding="utf-8"
        )
        typed_paths["review_decision_log"].write_text(
            "# synthetic accepted reviewer decision\n", encoding="utf-8"
        )

        manifest_digest = self.manifest.digest
        manifest_sha256 = sha256(H65_MANIFEST)
        schema_sha256 = sha256(typed_paths["canary_schema"])
        architecture_set_sha256 = "a" * 64
        schema_shape_sha256 = "b" * 64
        codex_executable_sha256 = "c" * 64
        candidate = {
            "schema_version": 2,
            "benchmark_id": self.update.BENCHMARK_ID,
            "architecture_set_sha256": architecture_set_sha256,
        }
        write_json(typed_paths["candidate"], candidate)
        write_json(
            typed_paths["preflight"],
            {
                "schema_version": 4,
                "benchmark_id": self.update.BENCHMARK_ID,
                "status": "passed",
                "validation_invocation_count": 1,
            },
        )
        write_json(
            typed_paths["gate"],
            {
                "schema_version": 1,
                "status": "passed",
                "validation_invocation_count": 1,
                "manifest_digest": manifest_digest,
            },
        )
        write_json(
            typed_paths["summary"],
            {
                "version": 1,
                "status": "completed",
                "attempt_count": 1,
                "model_session_count": 1,
                "tool_event_count": 0,
                "receipt_validation_count": 1,
                "manifest_digest": manifest_digest,
                "decision": "accepted",
            },
        )
        relative_manifest = H65_MANIFEST.relative_to(ROOT).as_posix()
        write_json(
            typed_paths["context"],
            {
                "runner_input_snapshot_sha256": {
                    relative_manifest: manifest_sha256,
                }
            },
        )
        canary_summary = {
            "version": canary_summary_version,
            "status": "passed",
            "qualification_passed": True,
            "qualification_id": self.update.QUALIFICATION_ID,
            "attempt_count": 1,
            "max_attempts": 1,
            "model_call_invocation_count": 1,
            "model_session_count": 1,
            "retry_count": 0,
            "retry_performed": False,
            "semantic_review_performed": False,
            "admissible_as_source_review": False,
            "manifest_digest": manifest_digest,
            "manifest_sha256": manifest_sha256,
            "schema_sha256": schema_sha256,
            "schema_shape_sha256": schema_shape_sha256,
            "codex_executable": "C:/synthetic/codex.exe",
            "codex_executable_sha256": codex_executable_sha256,
            "codex_version": "codex-cli synthetic-offline",
            "runtime_profile": "codex-exec-deterministic-exact-echo-unpinned-v2",
            "latency_class": "within-target",
        }
        write_json(typed_paths["canary_summary"], canary_summary)
        binding = {
            "version": 1,
            "status": "passed",
            "benchmark_id": self.update.BENCHMARK_ID,
            "qualification_id": self.update.QUALIFICATION_ID,
            "candidate_manifest_sha256": sha256(typed_paths["candidate"]),
            "architecture_set_sha256": architecture_set_sha256,
            "canary_summary_sha256": sha256(typed_paths["canary_summary"]),
            "preflight_sha256": sha256(typed_paths["preflight"]),
            "preflight_status": "passed",
            "manifest_digest": manifest_digest,
            "manifest_sha256": manifest_sha256,
            "schema_sha256": schema_sha256,
            "schema_shape_sha256": schema_shape_sha256,
            "codex_executable": canary_summary["codex_executable"],
            "codex_executable_sha256": codex_executable_sha256,
            "codex_version": canary_summary["codex_version"],
            "runtime_profile": canary_summary["runtime_profile"],
        }
        write_json(typed_paths["binding"], binding)
        postcheck = {
            "version": 1,
            "status": "passed",
            "benchmark_id": self.update.BENCHMARK_ID,
            "qualification_id": self.update.QUALIFICATION_ID,
            "binding_sha256": sha256(typed_paths["binding"]),
            "receipt_sha256": sha256(typed_paths["receipt"]),
            "summary_sha256": sha256(typed_paths["summary"]),
            "context_sha256": sha256(typed_paths["context"]),
            "schema_sha256": sha256(typed_paths["review_schema"]),
            "events_sha256": sha256(typed_paths["events"]),
            "stderr_sha256": sha256(typed_paths["stderr"]),
            "manifest_digest": manifest_digest,
            "decision": "accepted",
            "model_session_count": 1,
            "receipt_validation_count": 1,
            "tool_event_count": 0,
        }
        postcheck["chain_sha256"] = hashlib.sha256(
            json.dumps(
                postcheck,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        write_json(typed_paths["postcheck"], postcheck)

        constants: dict[str, object] = {
            "HANDOFF": handoff,
            "HANDOFF_NAME": handoff.name,
            "PREFIX": f"work/stage-handoffs/{handoff.name}",
            "WORKFLOW": handoff / "workflow-state.yaml",
            "MANIFEST": H65_MANIFEST,
            "GATE": typed_paths["gate"],
            "RECEIPT": typed_paths["receipt"],
            "REVIEW_SUMMARY": typed_paths["summary"],
            "REVIEW_CONTEXT": typed_paths["context"],
            "REVIEW_SCHEMA": typed_paths["review_schema"],
            "REVIEW_EVENTS": typed_paths["events"],
            "REVIEW_STDERR": typed_paths["stderr"],
            "CANARY_BINDING": typed_paths["binding"],
            "CANARY_POSTCHECK": typed_paths["postcheck"],
            "CANDIDATE": typed_paths["candidate"],
            "PREFLIGHT": typed_paths["preflight"],
            "CANARY_ROOT": canary_root,
            "CANARY_SUMMARY": typed_paths["canary_summary"],
            "CANARY_SCHEMA": typed_paths["canary_schema"],
            "REVIEW_SESSION_LOG": typed_paths["review_session_log"],
            "REVIEW_DECISION_LOG": typed_paths["review_decision_log"],
            "STAGE_FAILURE": handoff / "stage-failure.json",
        }
        current_canary = {"schema_sha256": schema_sha256}
        return constants, candidate, current_canary

    def test_accepted_v2_chain_renders_compile_ready_without_process_calls(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            constants, candidate, current_canary = self.build_chain(
                directory,
                canary_summary_version=2,
            )
            candidate_validator = Mock(return_value=candidate)
            canary_validator = Mock(return_value=current_canary)
            scope_validator = Mock(return_value={})
            input_validator = Mock(return_value=None)
            blocked_process = Mock(
                side_effect=AssertionError("offline compile-ready test started a process")
            )
            with patched_constants(self.update, constants), patch.object(
                self.update, "validate_candidate", candidate_validator
            ), patch.object(
                self.update, "validate_canary", canary_validator
            ), patch.object(
                self.update, "validate_scope_artifact_manifest", scope_validator
            ), patch.object(
                self.update, "require_files", input_validator
            ), patch.object(
                self.update, "load_manifest", return_value=self.manifest
            ), patch.object(subprocess, "run", blocked_process):
                rendered = self.update.compile_ready_state(
                    template=False,
                    write_supporting_logs=False,
                )
                state_path = Path(directory) / "rendered-workflow-state.yaml"
                state_path.write_text(rendered, encoding="utf-8", newline="\n")
                state = self.update.load_workflow_state(state_path)

            self.assertEqual("ready-for-next-stage", state["stage_status"])
            self.assertEqual("ft-test-case-reviewer", state["current_stage"])
            self.assertEqual("ft-test-case-iteration", state["next_skill"])
            self.assertEqual("accepted", state["source_assertion_review_state"]["status"])
            self.assertEqual(
                sha256(Path(constants["REVIEW_SUMMARY"])),
                state["source_assertion_review_state"]["review_summary_sha256"],
            )
            candidate_validator.assert_called_once_with()
            canary_validator.assert_called_once_with(candidate)
            scope_validator.assert_called_once_with()
            input_validator.assert_called_once()
            blocked_process.assert_not_called()

    def test_canary_summary_v1_is_rejected_with_expected_v2_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            constants, candidate, current_canary = self.build_chain(
                directory,
                canary_summary_version=1,
            )
            blocked_process = Mock(
                side_effect=AssertionError("negative compile-ready test started a process")
            )
            with patched_constants(self.update, constants), patch.object(
                self.update, "validate_candidate", return_value=candidate
            ), patch.object(
                self.update, "validate_canary", return_value=current_canary
            ), patch.object(
                self.update, "validate_scope_artifact_manifest", return_value={}
            ), patch.object(
                self.update, "require_files", return_value=None
            ), patch.object(
                self.update, "load_manifest", return_value=self.manifest
            ), patch.object(subprocess, "run", blocked_process):
                with self.assertRaises(self.update.WorkflowUpdateError) as raised:
                    self.update.compile_ready_state(
                        template=False,
                        write_supporting_logs=False,
                    )

            diagnostic = str(raised.exception)
            self.assertIn("version mismatch", diagnostic)
            self.assertIn("expected 2", diagnostic)
            self.assertIn("got 1", diagnostic)
            blocked_process.assert_not_called()

    def test_compile_ready_failure_is_never_classified_as_compiler(self) -> None:
        classification = self.metrics.classify_terminal(
            preflight_passed=True,
            source_gate_passed=True,
            source_review_accepted=True,
            compiler_ready=False,
            writer_started=False,
            writer_completed=False,
            reviewer_started=False,
            reviewer_accepted=False,
            promotion_present=False,
            promotion_valid=False,
            failed_orchestration_stage="compile-ready",
        )

        self.assertEqual(
            ("quality-stop-compile-ready", "stage-2b-workflow-compile-ready"),
            classification,
        )
        self.assertNotEqual("quality-stop-compiler", classification[0])
        self.assertNotEqual("stage-3-prepared-compiler", classification[1])

    def test_compile_ready_cli_failure_is_published_exactly_once(self) -> None:
        exact_message = "  Ошибка перехода compile-ready: поле «Доход»\nне связано  "
        with tempfile.TemporaryDirectory() as directory:
            stage_failure = Path(directory) / "stage-failure.json"
            blocked_process = Mock(
                side_effect=AssertionError("failure publisher started a process")
            )
            with patch.object(
                self.update, "STAGE_FAILURE", stage_failure
            ), patch.object(
                self.update.sys,
                "argv",
                [str(self.update.__file__), "--phase", "compile-ready"],
            ), patch.object(subprocess, "run", blocked_process):
                publication_error = self.update._publish_cli_failure(
                    self.update.WorkflowUpdateError(exact_message)
                )
                original = stage_failure.read_bytes()
                repeated_error = self.update._publish_cli_failure(
                    self.update.WorkflowUpdateError("replacement must not win")
                )

            self.assertIsNone(publication_error)
            failure = read_stage_failure(stage_failure)
            self.assertEqual("compile-ready", failure.stage)
            self.assertEqual(2, failure.return_code)
            self.assertEqual("WorkflowUpdateError", failure.error_type)
            self.assertEqual(exact_message, failure.error)
            self.assertEqual(
                Path(self.update.__file__).relative_to(ROOT).as_posix(),
                failure.source,
            )
            self.assertIsNotNone(repeated_error)
            assert repeated_error is not None
            self.assertIn("StageFailureAlreadyExistsError", repeated_error)
            self.assertIn("already exists", repeated_error)
            self.assertEqual(original, stage_failure.read_bytes())
            self.assertEqual([stage_failure], list(Path(directory).iterdir()))
            blocked_process.assert_not_called()


if __name__ == "__main__":
    unittest.main()
