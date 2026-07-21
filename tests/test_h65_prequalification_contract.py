from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

from test_case_agent.review_cycle.source_assertions import SourceAssertionContractError


ROOT = Path(__file__).resolve().parents[1]
H65 = (
    ROOT
    / "fts"
    / "AutoFin"
    / "work"
    / "stage-handoffs"
    / "65-application-card-additional-income-postfinal-v2-canary-contract-remediation"
)
REPORT = H65 / "offline-qualification-report.json"


def load_unique(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


class H65PrequalificationContractTests(unittest.TestCase):
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
            cls.prequal = load_unique(
                "_h65_prequalification_contract",
                H65 / "build_prequalification_manifest.py",
            )
        finally:
            sys.path.remove(str(H65))
        if Path(cls.prequal.__file__).resolve().parent != H65.resolve():
            raise AssertionError(f"loaded a non-H65 module: {cls.prequal.__file__}")
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls) -> None:
        sys.modules.pop("_h65_prequalification_contract", None)
        for name in cls._local_names:
            sys.modules.pop(name, None)
        sys.modules.update(cls._saved_modules)

    def validate_mutation(
        self,
        payload: dict[str, object],
        *,
        expected_evidence: dict[str, object] | None = None,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "offline-qualification-report.json"
            write_json(report, payload)
            patches = [
                patch.object(self.prequal, "OFFLINE_QUALIFICATION_REPORT", report)
            ]
            if expected_evidence is not None:
                patches.append(
                    patch.object(
                        self.prequal,
                        "expected_offline_evidence",
                        return_value=expected_evidence,
                    )
                )
            with patches[0]:
                if len(patches) == 1:
                    self.prequal.offline_qualification()
                else:
                    with patches[1]:
                        self.prequal.offline_qualification()

    def test_historical_report_passes_against_captured_evidence(self) -> None:
        with patch.object(
            self.prequal,
            "expected_offline_evidence",
            return_value=copy.deepcopy(self.report["evidence"]),
        ):
            qualification = self.prequal.offline_qualification()
        self.assertEqual("passed", qualification["status"])
        self.assertEqual(set(self.prequal.OFFLINE_CHECKS), set(qualification["checks"]))

    def test_current_report_rejects_changed_mutable_package_note(self) -> None:
        with self.assertRaisesRegex(
            SourceAssertionContractError,
            "stale-evidence-source-sha256.*AGENT-NOTES.md",
        ):
            self.prequal.offline_qualification()

    def test_bool_integer_confusion_is_rejected(self) -> None:
        payload = copy.deepcopy(self.report)
        payload["external_calls_made"] = 0
        with self.assertRaisesRegex(
            self.prequal.PrequalificationError,
            "external_calls_made has type int; expected bool",
        ):
            self.validate_mutation(
                payload,
                expected_evidence=copy.deepcopy(self.report["evidence"]),
            )

    def test_unknown_root_field_is_rejected(self) -> None:
        payload = copy.deepcopy(self.report)
        payload["unbound_claim"] = "passed"
        with self.assertRaisesRegex(
            self.prequal.PrequalificationError,
            "invalid root shape",
        ):
            self.validate_mutation(payload)

    def test_mislabeled_source_digest_is_rejected(self) -> None:
        payload = copy.deepcopy(self.report)
        scope = payload["evidence"]["scope_package_validation"]
        digest = scope.pop("source_assertion_manifest_digest")
        scope["source_artifact_manifest_sha256"] = digest
        with self.assertRaisesRegex(
            self.prequal.PrequalificationError,
            "invalid fields",
        ):
            self.validate_mutation(
                payload,
                expected_evidence=copy.deepcopy(self.report["evidence"]),
            )


if __name__ == "__main__":
    unittest.main()
