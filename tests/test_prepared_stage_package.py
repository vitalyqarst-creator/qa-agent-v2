from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from test_case_agent.review_cycle.prepared_package import (
    EvidenceInput,
    PreparedGap,
    PreparedObligation,
    PreparedObligationSet,
    PreparedPackageBuilder,
    StageInstructionConfig,
    load_prepared_package,
)
from test_case_agent.review_cycle.runtime import StageRuntimeError


class PreparedStagePackageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "source").mkdir()
        (self.root / "work").mkdir()
        self.docx = self.root / "source" / "requirements.docx"
        self.xhtml = self.root / "source" / "requirements.xhtml"
        self.docx.write_bytes(b"docx-source")
        self.xhtml.write_text("<html>full source</html>", encoding="utf-8")
        self.evidence = self.root / "work" / "scope.md"
        self.evidence.write_text(
            "# Evidence\n\nSRC-1: поле допускает одно значение.\nSRC-2: внутренний NULL не наблюдаем.\n",
            encoding="utf-8",
        )

    def _obligations(self) -> PreparedObligationSet:
        return PreparedObligationSet.create(
            package_id="pkg-001",
            obligations=(
                PreparedObligation(
                    obligation_id="ATOM-001",
                    source_refs=("SRC-1",),
                    atomic_statement="Поле допускает выбор одного значения.",
                    observable_oracle="В поле остается одно выбранное значение.",
                    test_intent="Проверить одиночный выбор.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                ),
                PreparedObligation(
                    obligation_id="ATOM-002",
                    source_refs=("SRC-2",),
                    atomic_statement="Пустое значение хранится как NULL.",
                    observable_oracle="",
                    test_intent="Не создавать исполнимый кейс без наблюдаемого oracle.",
                    coverage_status="gap",
                    gap_id="GAP-001",
                    dictionary_refs=(),
                    notes="Требуется API или DB evidence.",
                ),
            ),
            coverage_gaps=(
                PreparedGap(
                    gap_id="GAP-001",
                    source_refs=("SRC-2",),
                    problem="Нет наблюдаемого способа проверить внутренний NULL.",
                    handling="Зафиксировать открытый вопрос.",
                    blocking=False,
                ),
            ),
        )

    def _build(self, *, max_package_bytes: int = 512000, output_name: str = "prepared"):
        return PreparedPackageBuilder(
            self.root, max_package_bytes=max_package_bytes
        ).build(
            output_root=self.root / "work" / output_name,
            package_id="pkg-001",
            ft_slug="demo-ft",
            scope_slug="field-selection",
            section_id="4.3",
            source_registry=(
                (self.docx, "source-of-truth", "section 4.3"),
                (self.xhtml, "machine-readable", "SRC-1..SRC-2"),
            ),
            evidence_inputs=(EvidenceInput(self.evidence, "Confirmed scope"),),
            obligations=self._obligations(),
            instructions=StageInstructionConfig(
                role="writer",
                scenario="writer.session_prepared_initial_draft",
                output_path="work/output.md",
                attempt_root="work/attempt-001",
                sandbox_policy="workspace_write",
                timeout_seconds=180,
                idle_timeout_seconds=60,
                command_budget=12,
            ),
            forbidden_evidence_roots=("fts/demo-ft/test-cases", "work/previous-cycle"),
        )

    def test_builds_compact_immutable_package_and_round_trips(self) -> None:
        package = self._build()
        package_root = self.root / "work" / "prepared"
        loaded = load_prepared_package(package_root / "stage-package.json", self.root)

        self.assertEqual(package.package_digest, loaded.package_digest)
        self.assertEqual(
            {path.name for path in package_root.iterdir()},
            {
                "stage-package.json",
                "source-evidence.md",
                "atomic-obligations.json",
                "stage-instructions.md",
            },
        )
        self.assertFalse((package_root / self.docx.name).exists())
        self.assertTrue(all(item.path.startswith("work/prepared/") for item in loaded.package_artifacts))
        instructions = (package_root / "stage-instructions.md").read_text(encoding="utf-8")
        self.assertIn("Do not rerun source locator", instructions)
        self.assertIn("targeted_source_fallback", instructions)
        with self.assertRaisesRegex(StageRuntimeError, "immutable"):
            self._build()

    def test_detects_registered_source_and_package_tampering(self) -> None:
        self._build()
        manifest = self.root / "work" / "prepared" / "stage-package.json"
        self.docx.write_bytes(b"changed")
        with self.assertRaisesRegex(StageRuntimeError, "full source hash mismatch"):
            load_prepared_package(manifest, self.root)

        self.docx.write_bytes(b"docx-source")
        (manifest.parent / "source-evidence.md").write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(StageRuntimeError, "artifact hash mismatch"):
            load_prepared_package(manifest, self.root)

    def test_rejects_missing_evidence_reference(self) -> None:
        self.evidence.write_text("# no anchors\n", encoding="utf-8")
        with self.assertRaisesRegex(StageRuntimeError, "does not name"):
            self._build()
        self.assertFalse((self.root / "work" / "prepared").exists())

    def test_rejects_testable_obligation_without_oracle(self) -> None:
        invalid = PreparedObligation(
            obligation_id="ATOM-003",
            source_refs=("SRC-1",),
            atomic_statement="Утверждение.",
            observable_oracle="",
            test_intent="Проверить.",
            coverage_status="testable",
            gap_id="",
            dictionary_refs=(),
            notes="",
        )
        with self.assertRaisesRegex(StageRuntimeError, "observable_oracle"):
            PreparedObligationSet.create(
                package_id="pkg-001", obligations=(invalid,), coverage_gaps=()
            )

    def test_rejects_unknown_gap_and_package_budget_overflow(self) -> None:
        unknown = PreparedObligation(
            obligation_id="ATOM-004",
            source_refs=("SRC-2",),
            atomic_statement="Неясное утверждение.",
            observable_oracle="",
            test_intent="Зафиксировать gap.",
            coverage_status="unclear",
            gap_id="GAP-404",
            dictionary_refs=(),
            notes="",
        )
        with self.assertRaisesRegex(StageRuntimeError, "unknown gap"):
            PreparedObligationSet.create(
                package_id="pkg-001", obligations=(unknown,), coverage_gaps=()
            )

        with self.assertRaisesRegex(StageRuntimeError, "blocked-package-budget"):
            self._build(max_package_bytes=32, output_name="too-large")
        self.assertFalse((self.root / "work" / "too-large").exists())


if __name__ == "__main__":
    unittest.main()
