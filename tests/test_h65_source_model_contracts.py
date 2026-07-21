from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

from test_case_agent.review_cycle.source_assertions import (
    load_source_assertion_manifest,
)
from tests.frozen_h64_h65_evidence import frozen_h64_h65_package_note


ROOT = Path(__file__).resolve().parents[1]
H64_HANDOFF_NAME = (
    "64-application-card-additional-income-postfinal-v2-"
    "source-provenance-terminal-state-remediation"
)
H65_HANDOFF_NAME = (
    "65-application-card-additional-income-postfinal-v2-"
    "canary-contract-remediation"
)
HANDOFF_ROOT = ROOT / "fts/AutoFin/work/stage-handoffs"
H64_HANDOFF = HANDOFF_ROOT / H64_HANDOFF_NAME
H65_HANDOFF = HANDOFF_ROOT / H65_HANDOFF_NAME
EXPECTED_MANIFEST_DIGEST = (
    "699fcea64b2585dcfbf77a4e92bb7d70a43abef8e47be9b9acf5cc1c1e1ae235"
)
EXPECTED_BENCHMARK_ID = (
    "application-card-additional-income-postfinal-v2-h65-benchmark-20260716"
)
EXPECTED_QUALIFICATION_ID = "h65-source-review-schema-v6-20260716"
EXPECTED_CANARY_REPO = (
    "evals/schema-canary/20260716-h65-source-assertion-review-v6"
)


def _load_json(name: str) -> dict[str, object]:
    return json.loads((H65_HANDOFF / name).read_text(encoding="utf-8"))


def _markdown_row(name: str, row_id: str) -> list[str]:
    prefix = f"| {row_id} |"
    matches = [
        line
        for line in (H65_HANDOFF / name).read_text(encoding="utf-8").splitlines()
        if line.startswith(prefix)
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"expected one {row_id} row in {name}, found {len(matches)}"
        )
    return [cell.strip() for cell in matches[0].strip("|").split("|")]


def _literal_assignments(source: str) -> dict[str, object]:
    result: dict[str, object] = {}
    for node in ast.parse(source).body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            try:
                result[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass
    return result


class H65SourceModelContractsTests(unittest.TestCase):
    def test_h65_identities_are_exact_and_source_carryforward_is_explicit(self) -> None:
        generator = H65_HANDOFF / "build_remediation_scope_package.py"
        source = generator.read_text(encoding="utf-8")
        assignments = _literal_assignments(source)

        self.assertEqual(H65_HANDOFF_NAME, assignments["HANDOFF_NAME"])
        self.assertEqual(H64_HANDOFF_NAME, assignments["FROZEN_SOURCE_HANDOFF_NAME"])
        self.assertEqual(EXPECTED_BENCHMARK_ID, assignments["BENCHMARK_ID"])
        self.assertEqual(EXPECTED_QUALIFICATION_ID, assignments["QUALIFICATION_ID"])
        self.assertEqual(EXPECTED_CANARY_REPO, assignments["CANARY_REPO"])
        self.assertIn(
            'CYCLE_REPO = f"fts/AutoFin/work/review-cycles/{BENCHMARK_ID}"',
            source,
        )
        self.assertIn("run_h65_benchmark_once.py", source)
        self.assertNotIn("run_h64_benchmark_once.py", source)

        descriptor_source = (
            H65_HANDOFF / "build_source_reviewer_bounded_descriptors.py"
        ).read_text(encoding="utf-8")
        self.assertIn("H65 source-verified", descriptor_source)
        self.assertNotIn("H64 source-verified", descriptor_source)

    def test_manifest_is_byte_identical_to_h64_and_keeps_required_digest(self) -> None:
        h64_manifest_path = H64_HANDOFF / "source-assertions.json"
        h65_manifest_path = H65_HANDOFF / "source-assertions.json"
        self.assertEqual(h64_manifest_path.read_bytes(), h65_manifest_path.read_bytes())

        with frozen_h64_h65_package_note(ROOT):
            manifest = load_source_assertion_manifest(h65_manifest_path, ROOT)
        self.assertEqual(EXPECTED_MANIFEST_DIGEST, manifest.digest)
        self.assertEqual(14, len(manifest.source_rows))
        self.assertEqual(20, len(manifest.assertions))

        payload = _load_json("source-assertions.json")
        self.assertIn(H64_HANDOFF_NAME, payload["coverage_gaps_artifact"]["path"])
        clarification = payload["clarifications"][0]
        self.assertIn(H64_HANDOFF_NAME, clarification["evidence_source_path"])

    def test_assert_020_keeps_exact_codes_without_executable_tc(self) -> None:
        payload = _load_json("source-assertions.json")
        source_row = next(
            row
            for row in payload["source_rows"]
            if row["source_row_id"] == "SRC-014"
        )
        assertion = next(
            item
            for item in payload["assertions"]
            if item["assertion_id"] == "ASSERT-020"
        )

        self.assertEqual("no", source_row["scope_disposition"])
        self.assertEqual(["BSR 2", "BSR 3"], source_row["requirement_codes"])
        self.assertEqual(["BSR 2", "BSR 3"], assertion["requirement_codes"])
        self.assertEqual("not-applicable", assertion["semantic_disposition"])
        self.assertEqual("not-applicable", assertion["execution_readiness"])
        self.assertEqual([], assertion["obligation_ids"])

        bindings = assertion["requirement_code_bindings"]
        self.assertEqual(["BSR 2", "BSR 3"], [row["requirement_code"] for row in bindings])
        for binding in bindings:
            self.assertEqual("SRC-014", binding["source_row_id"])
            self.assertEqual("xhtml-row", binding["provenance_role"])
            fragment = binding["exact_source_fragment"]
            self.assertTrue(fragment.startswith(binding["requirement_code"] + "."))
            self.assertIn(fragment, assertion["exact_source_text"])

        ledger = _markdown_row("atomic-requirements-ledger.md", "ATOM-020")
        self.assertEqual("BSR 2; BSR 3", ledger[4])
        self.assertEqual("SRC-014; BSR 2; BSR 3", ledger[5])
        self.assertEqual("not-applicable", ledger[7])
        self.assertEqual("none_required", ledger[8])

        projection = _markdown_row("coverage-obligation-table.md", "OBL-020")
        self.assertEqual("not-applicable-context", projection[7])
        self.assertEqual("SRC-014; BSR 2; BSR 3", projection[9])
        self.assertEqual("not-applicable", projection[10])
        self.assertEqual("not-applicable", projection[11])

    def test_generated_source_artifacts_have_exact_counts_and_h65_paths(self) -> None:
        summary = _load_json("scope-package-generation-summary.json")
        self.assertEqual(EXPECTED_MANIFEST_DIGEST, summary["manifest_digest"])
        self.assertEqual(14, summary["source_row_count"])
        self.assertEqual(20, summary["assertion_count"])
        self.assertEqual(11, summary["testable_assertion_count"])
        self.assertEqual(17, summary["testable_obligation_count"])
        self.assertEqual(14, summary["planned_tc_count"])

        artifact_manifest = _load_json("scope-artifact-manifest.json")
        self.assertEqual(28, len(artifact_manifest["artifacts"]))
        self.assertIn(
            f"stage-handoffs/{H65_HANDOFF_NAME}/build_remediation_scope_package.py",
            artifact_manifest["generator_path"],
        )
        for row in artifact_manifest["artifacts"]:
            self.assertIn(f"stage-handoffs/{H65_HANDOFF_NAME}/", row["path"])

        execution_options = (H65_HANDOFF / "scope-execution-options.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("run_h65_benchmark_once.py", execution_options)
        self.assertNotIn("run_h64_benchmark_once.py", execution_options)


if __name__ == "__main__":
    unittest.main()
