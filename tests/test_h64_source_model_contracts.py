from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

from test_case_agent.review_cycle.source_assertions import (
    SourceAssertionContractError,
    load_source_assertion_manifest,
)
from tests.frozen_h64_h65_evidence import (
    frozen_h64_h65_package_note,
    frozen_h64_h65_support_dictionary,
)


ROOT = Path(__file__).resolve().parents[1]
HANDOFF_NAME = (
    "64-application-card-additional-income-postfinal-v2-"
    "source-provenance-terminal-state-remediation"
)
HANDOFF = ROOT / "fts/AutoFin/work/stage-handoffs" / HANDOFF_NAME


def _load_json(name: str) -> dict[str, object]:
    return json.loads((HANDOFF / name).read_text(encoding="utf-8"))


def _markdown_row(name: str, row_id: str) -> list[str]:
    prefix = f"| {row_id} |"
    matches = [
        line
        for line in (HANDOFF / name).read_text(encoding="utf-8").splitlines()
        if line.startswith(prefix)
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"expected one {row_id} row in {name}, found {len(matches)}"
        )
    return [cell.strip() for cell in matches[0].strip("|").split("|")]


class H64SourceModelContractsTests(unittest.TestCase):
    def test_not_applicable_generator_api_accepts_explicit_code_bindings(self) -> None:
        generator = HANDOFF / "build_remediation_scope_package.py"
        tree = ast.parse(generator.read_text(encoding="utf-8"))
        function = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "not_applicable"
        )
        self.assertIn(
            "code_bindings",
            [argument.arg for argument in function.args.kwonlyargs],
        )

    def test_assert_020_preserves_exact_out_of_scope_requirement_provenance(self) -> None:
        manifest_payload = _load_json("source-assertions.json")
        source_row = next(
            row
            for row in manifest_payload["source_rows"]
            if row["source_row_id"] == "SRC-014"
        )
        assertion = next(
            item
            for item in manifest_payload["assertions"]
            if item["assertion_id"] == "ASSERT-020"
        )

        self.assertEqual("no", source_row["scope_disposition"])
        self.assertEqual(["BSR 2", "BSR 3"], source_row["requirement_codes"])
        self.assertEqual(["BSR 2", "BSR 3"], assertion["requirement_codes"])
        self.assertEqual("not-applicable", assertion["semantic_disposition"])
        self.assertEqual("not-applicable", assertion["execution_readiness"])
        self.assertEqual([], assertion["obligation_ids"])
        self.assertEqual([], assertion["condition_clauses"])
        self.assertEqual([], assertion["action_clauses"])
        self.assertEqual([], assertion["oracle_clauses"])

        bindings = assertion["requirement_code_bindings"]
        self.assertEqual(["BSR 2", "BSR 3"], [row["requirement_code"] for row in bindings])
        for binding in bindings:
            self.assertEqual("SRC-014", binding["source_row_id"])
            self.assertEqual("xhtml-row", binding["provenance_role"])
            self.assertIsNone(binding["evidence_source_path"])
            self.assertIsNone(binding["evidence_locator"])
            fragment = binding["exact_source_fragment"]
            self.assertTrue(fragment.startswith(binding["requirement_code"] + "."))
            self.assertIn(fragment, assertion["exact_source_text"])

    def test_atom_020_and_descriptive_projection_keep_codes_without_tc(self) -> None:
        ledger = _markdown_row("atomic-requirements-ledger.md", "ATOM-020")
        self.assertEqual("BSR 2; BSR 3", ledger[4])
        self.assertEqual("SRC-014; BSR 2; BSR 3", ledger[5])
        self.assertEqual("not-applicable", ledger[7])
        self.assertEqual("none_required", ledger[8])

        projection = _markdown_row("coverage-obligation-table.md", "OBL-020")
        self.assertEqual("ATOM-020", projection[3])
        self.assertEqual("BSR 2; BSR 3", projection[5])
        self.assertEqual("not-applicable-context", projection[7])
        self.assertEqual("SRC-014; BSR 2; BSR 3", projection[9])
        self.assertEqual("not-applicable", projection[10])
        self.assertEqual("not-applicable", projection[11])

    def test_materialized_manifest_is_valid_and_keeps_h64_identifiers(self) -> None:
        with frozen_h64_h65_package_note(ROOT):
            manifest = load_source_assertion_manifest(
                HANDOFF / "source-assertions.json",
                ROOT,
            )
        self.assertEqual(20, len(manifest.assertions))
        self.assertEqual(14, len(manifest.source_rows))

        summary = _load_json("scope-package-generation-summary.json")
        self.assertEqual(11, summary["testable_assertion_count"])
        self.assertEqual(17, summary["testable_obligation_count"])
        self.assertEqual(14, summary["planned_tc_count"])

        artifact_manifest = _load_json("scope-artifact-manifest.json")
        self.assertIn(
            f"stage-handoffs/{HANDOFF_NAME}/build_remediation_scope_package.py",
            artifact_manifest["generator_path"],
        )
        for row in artifact_manifest["artifacts"]:
            self.assertIn(f"stage-handoffs/{HANDOFF_NAME}/", row["path"])

        execution_options = (HANDOFF / "scope-execution-options.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("run_h64_benchmark_once.py", execution_options)
        self.assertNotIn("run_h63_benchmark_once.py", execution_options)

        for name in (
            "build_remediation_scope_package.py",
            "build_scope_source_baseline.py",
            "build_source_reviewer_bounded_descriptors.py",
        ):
            generator_text = (HANDOFF / name).read_text(encoding="utf-8")
            self.assertNotIn("H63", generator_text)
            self.assertNotIn("h63", generator_text)
            self.assertNotIn(
                "63-application-card-additional-income-postfinal-v2-"
                "transport-remediation",
                generator_text,
            )

    def test_current_loader_rejects_historical_manifest_after_package_note_change(
        self,
    ) -> None:
        with frozen_h64_h65_support_dictionary(ROOT):
            with self.assertRaisesRegex(
                SourceAssertionContractError,
                "stale-evidence-source-sha256.*AGENT-NOTES.md",
            ):
                load_source_assertion_manifest(
                    HANDOFF / "source-assertions.json",
                    ROOT,
                )


if __name__ == "__main__":
    unittest.main()
