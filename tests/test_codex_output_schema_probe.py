from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT_DIR / "scripts" / "probe_codex_output_schema.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "probe_codex_output_schema_under_test", SCRIPT_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


probe = load_module()


class CodexOutputSchemaProbeTests(unittest.TestCase):
    def test_probe_uses_runner_schema_and_persists_evidence(self) -> None:
        payload = {
            "contract_version": 4,
            "decision": "accepted",
            "reviewed_draft_sha256": "0" * 64,
            "reviewed_source_basis_sha256": hashlib.sha256(
                (
                    "SRC-PROBE-001: deterministic reviewer schema transport probe."
                    + os.linesep
                ).encode("utf-8")
            ).hexdigest(),
            "reviewed_obligation_set_sha256": hashlib.sha256(
                ('{"probe":true}' + os.linesep).encode("utf-8")
            ).hexdigest(),
            "obligation_reviews": [
                {
                    "obligation_id": "OBL-PROBE-001",
                    "verdict": "covered",
                }
            ],
            "dimension_reviews": [
                {
                    "dimension": "scope-boundary",
                    "verdict": "verified",
                    "source_refs": ["SRC-PROBE-001"],
                    "note": "Transport probe only.",
                }
            ],
            "findings": [],
            "summary": "Reviewer schema transport probe passed.",
        }
        events = (
            json.dumps({"type": "thread.started", "thread_id": "probe-session"})
            + "\n"
            + json.dumps(
                {
                    "type": "item.completed",
                    "item": {
                        "type": "agent_message",
                        "text": json.dumps(payload),
                    },
                }
            )
            + "\n"
        )
        responses = [
            subprocess.CompletedProcess([], 0, stdout="codex-test 1.0\n", stderr=""),
            subprocess.CompletedProcess([], 0, stdout=events, stderr=""),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary) / "probe"
            with mock.patch.object(probe.subprocess, "run", side_effect=responses):
                result = probe.run_probe(
                    codex_command="codex-test",
                    output_dir=output_dir,
                    timeout_seconds=5,
                )

            self.assertEqual("passed", result["status"], result)
            schema = (output_dir / "review-contract.schema.json").read_text(
                encoding="utf-8"
            )
            self.assertNotIn("uniqueItems", schema)
            self.assertTrue((output_dir / "stdout.ndjson").is_file())
            self.assertTrue((output_dir / "result.json").is_file())


if __name__ == "__main__":
    unittest.main()
