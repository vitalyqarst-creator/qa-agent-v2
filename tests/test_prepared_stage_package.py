from __future__ import annotations

import tempfile
import hashlib
import json
import unittest
from pathlib import Path

from test_case_agent.review_cycle.prepared_package import (
    EvidenceInput,
    PreparedGap,
    PreparedObligation,
    PreparedObligationSet,
    PreparedPackageBuilder,
    PreparedStateChange,
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

    def _build(
        self,
        *,
        max_package_bytes: int = 512000,
        output_name: str = "prepared",
        reuse_if_current: bool = False,
    ):
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
            evidence_inputs=(
                EvidenceInput(self.evidence, "Confirmed scope", selectors=("SRC-1", "SRC-2")),
            ),
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
            execution_profile="simple-field-property",
            unsupported_dimensions=(),
            forbidden_evidence_roots=("fts/demo-ft/test-cases", "work/previous-cycle"),
            reuse_if_current=reuse_if_current,
        )

    def test_builds_compact_immutable_package_and_round_trips(self) -> None:
        package = self._build()
        package_root = self.root / "work" / "prepared"
        loaded = load_prepared_package(package_root / "stage-package.json", self.root)

        self.assertEqual(package.package_digest, loaded.package_digest)
        self.assertEqual(64, len(loaded.input_fingerprint))
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
        self.assertLess(sum(path.stat().st_size for path in package_root.iterdir()), 16 * 1024)
        self.assertTrue(all(item.path.startswith("work/prepared/") for item in loaded.package_artifacts))
        obligation_payload = json.loads(
            (package_root / "atomic-obligations.json").read_text(encoding="utf-8")
        )
        self.assertEqual("ATOM-001", obligation_payload["obligations"][0]["atom_id"])
        instructions = (package_root / "stage-instructions.md").read_text(encoding="utf-8")
        self.assertIn("Do not rerun source locator", instructions)
        self.assertIn("targeted_source_fallback", instructions)
        with self.assertRaisesRegex(StageRuntimeError, "immutable"):
            self._build()

    def test_reuses_only_identical_current_package_input(self) -> None:
        original = self._build()

        reused = self._build(reuse_if_current=True)

        self.assertEqual(original.package_digest, reused.package_digest)
        self.assertEqual(original.created_at, reused.created_at)
        self.assertEqual(original.input_fingerprint, reused.input_fingerprint)

        self.evidence.write_text(
            self.evidence.read_text(encoding="utf-8") + "\nSRC-1: changed context.\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(StageRuntimeError, "stale prepared package cache"):
            self._build(reuse_if_current=True)

    def test_v6_obligation_payload_without_planned_tc_round_trips_unchanged(self) -> None:
        original = self._obligations()
        payload = original.to_dict()

        self.assertNotIn("planned_test_case_id", payload["obligations"][0])
        restored = PreparedObligationSet.from_dict(payload)

        self.assertEqual(original.digest, restored.digest)
        self.assertEqual(payload, restored.to_dict())

    def test_legacy_v6_obligation_payload_remains_readable(self) -> None:
        payload = self._obligations().to_dict()
        payload["package_version"] = 6
        for obligation in payload["obligations"]:
            obligation.pop("dictionary_requirements")
            obligation.pop("calibration_status")
        without_digest = {
            key: value for key, value in payload.items() if key != "digest"
        }
        payload["digest"] = hashlib.sha256(
            json.dumps(
                without_digest,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        restored = PreparedObligationSet.from_dict(payload)

        self.assertEqual(6, restored.package_version)
        self.assertEqual((), restored.obligations[0].dictionary_requirements)
        self.assertEqual("none", restored.obligations[0].calibration_status)

    def test_v6_obligation_payload_with_planned_tc_round_trips(self) -> None:
        original = PreparedObligationSet.create(
            package_id="pkg-grouped",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-001",
                    atom_id="ATOM-001",
                    source_refs=("SRC-1",),
                    atomic_statement="Поле редактируемо.",
                    observable_oracle="Значение отображается.",
                    test_intent="Ввести значение.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    planned_test_case_id="TC-GROUP-001",
                ),
            ),
            coverage_gaps=(),
        )
        payload = original.to_dict()

        restored = PreparedObligationSet.from_dict(payload)

        self.assertEqual("TC-GROUP-001", restored.obligations[0].planned_test_case_id)
        self.assertEqual(original.digest, restored.digest)

    def test_v6_obligation_payload_still_rejects_unknown_extra_field(self) -> None:
        payload = self._obligations().to_dict()
        payload["obligations"][0]["unexpected_field"] = "unexpected"

        with self.assertRaisesRegex(StageRuntimeError, "unknown=.*unexpected_field"):
            PreparedObligationSet.from_dict(payload)

    def test_v6_reset_obligation_preserves_changed_prestate_contract(self) -> None:
        obligation = PreparedObligation(
            obligation_id="OBL-RESET-001",
            atom_id="ATOM-RESET-001",
            source_refs=("SRC-1",),
            atomic_statement="Clear restores the captured initial state.",
            observable_oracle="After Clear the state matches the captured initial state.",
            test_intent="Change the state, prove the change, then click Clear.",
            coverage_status="testable",
            gap_id="",
            dictionary_refs=(),
            notes="",
            planned_test_case_id="TC-RESET-001",
            execution_semantics="reset-to-captured-initial",
            state_change=PreparedStateChange(
                initial_state_capture="Capture the visible initial state.",
                changed_state_setup="Choose a visible state different from the captured initial state.",
                pre_action_state_oracle="Before Clear the visible state differs from the captured initial state.",
            ),
        )

        original = PreparedObligationSet.create(
            package_id="pkg-reset", obligations=(obligation,), coverage_gaps=()
        )
        restored = PreparedObligationSet.from_dict(original.to_dict())

        self.assertEqual(
            "reset-to-captured-initial",
            restored.obligations[0].execution_semantics,
        )
        self.assertEqual(
            "different-from-captured-initial",
            restored.obligations[0].state_change.relation,
        )

    def test_v6_reset_obligation_requires_changed_prestate_contract(self) -> None:
        obligation = PreparedObligation(
            obligation_id="OBL-RESET-001",
            atom_id="ATOM-RESET-001",
            source_refs=("SRC-1",),
            atomic_statement="Clear restores the captured initial state.",
            observable_oracle="After Clear the state matches the captured initial state.",
            test_intent="Click Clear.",
            coverage_status="testable",
            gap_id="",
            dictionary_refs=(),
            notes="",
            execution_semantics="reset-to-captured-initial",
        )

        with self.assertRaisesRegex(StageRuntimeError, "require state_change"):
            PreparedObligationSet.create(
                package_id="pkg-reset", obligations=(obligation,), coverage_gaps=()
            )

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
        with self.assertRaisesRegex(StageRuntimeError, "selector not found|does not name"):
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

    def test_rejects_dictionary_backed_testable_obligation_without_inventory_ref(self) -> None:
        invalid = PreparedObligation(
            obligation_id="ATOM-003",
            source_refs=("SRC-1",),
            atomic_statement="Значения берутся из справочника и допускают одиночный выбор.",
            observable_oracle="В поле остается одно выбранное значение.",
            test_intent="Проверить одиночный выбор.",
            coverage_status="testable",
            gap_id="",
            dictionary_refs=(),
            notes="",
        )

        with self.assertRaisesRegex(StageRuntimeError, "dictionary-backed.*dictionary_refs"):
            PreparedObligationSet.create(
                package_id="pkg-001", obligations=(invalid,), coverage_gaps=()
            )

    def test_dictionary_word_in_limiting_test_intent_does_not_change_claim_class(self) -> None:
        obligation = PreparedObligation(
            obligation_id="ATOM-003",
            source_refs=("SRC-1",),
            atomic_statement="Поле допускает одиночный выбор.",
            observable_oracle="В поле остается одно выбранное значение.",
            test_intent="Проверить кратность без предположений о конкретном справочнике.",
            coverage_status="testable",
            gap_id="",
            dictionary_refs=(),
            notes="",
        )

        value = PreparedObligationSet.create(
            package_id="pkg-001", obligations=(obligation,), coverage_gaps=()
        )
        self.assertEqual("ATOM-003", value.obligations[0].obligation_id)

    def test_dictionary_ref_must_be_present_as_exact_evidence_anchor(self) -> None:
        obligation = PreparedObligation(
            obligation_id="ATOM-003",
            source_refs=("SRC-1",),
            atomic_statement="Значения берутся из справочника.",
            observable_oracle="Отображается подтвержденный закрытый набор значений.",
            test_intent="Сравнить значения с инвентарем.",
            coverage_status="testable",
            gap_id="",
            dictionary_refs=("DICT-001",),
            notes="",
        )
        obligations = PreparedObligationSet.create(
            package_id="pkg-001", obligations=(obligation,), coverage_gaps=()
        )

        with self.assertRaisesRegex(StageRuntimeError, "DICT-001"):
            obligations.validate(evidence_text="SRC-1 and DICT-0010 are not the requested anchor.")

    def test_rejects_orphan_and_fast_path_blocking_gaps(self) -> None:
        orphan = PreparedGap(
            gap_id="GAP-002",
            source_refs=("SRC-2",),
            problem="Unlinked gap.",
            handling="Link it to an obligation.",
            blocking=False,
        )
        with self.assertRaisesRegex(StageRuntimeError, "coverage gaps must be linked"):
            PreparedObligationSet.create(
                package_id="pkg-001",
                obligations=(self._obligations().obligations[0],),
                coverage_gaps=(orphan,),
            )

        blocking = PreparedGap(
            gap_id="GAP-001",
            source_refs=("SRC-2",),
            problem="Required fixture is unavailable.",
            handling="Block the fast path.",
            blocking=True,
        )
        obligations = PreparedObligationSet.create(
            package_id="pkg-001",
            obligations=(self._obligations().obligations[0], self._obligations().obligations[1]),
            coverage_gaps=(blocking,),
        )
        with self.assertRaisesRegex(StageRuntimeError, "blocking coverage gaps"):
            PreparedPackageBuilder(self.root).build(
                output_root=self.root / "work" / "blocking-gap",
                package_id="pkg-001",
                ft_slug="demo-ft",
                scope_slug="field-selection",
                section_id="4.3",
                source_registry=((self.docx, "source-of-truth", "section 4.3"),),
                evidence_inputs=(
                    EvidenceInput(self.evidence, "Confirmed scope", selectors=("SRC-1", "SRC-2")),
                ),
                obligations=obligations,
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
                execution_profile="simple-field-property",
                unsupported_dimensions=(),
                forbidden_evidence_roots=("fts/demo-ft/test-cases",),
            )

    def test_reference_selector_does_not_match_longer_anchor(self) -> None:
        self.evidence.write_text("# Evidence\n\nSRC-10: different row.\n", encoding="utf-8")
        with self.assertRaisesRegex(StageRuntimeError, "selector not found"):
            self._build()

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

    def test_fast_profile_rejects_unsupported_dimensions(self) -> None:
        builder = PreparedPackageBuilder(self.root)
        with self.assertRaisesRegex(StageRuntimeError, "cannot declare unsupported"):
            builder.build(
                output_root=self.root / "work" / "ineligible",
                package_id="pkg-001",
                ft_slug="demo-ft",
                scope_slug="field-selection",
                section_id="4.3",
                source_registry=((self.docx, "source-of-truth", "section 4.3"),),
                evidence_inputs=(
                    EvidenceInput(self.evidence, "Confirmed scope", selectors=("SRC-1",)),
                ),
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
                execution_profile="simple-field-property",
                unsupported_dimensions=("integration-persistence",),
                forbidden_evidence_roots=("fts/demo-ft/test-cases",),
            )

    def test_fast_profile_requires_docx_and_xhtml_source_roles(self) -> None:
        common = {
            "package_id": "pkg-001",
            "ft_slug": "demo-ft",
            "scope_slug": "field-selection",
            "section_id": "4.3",
            "evidence_inputs": (
                EvidenceInput(self.evidence, "Confirmed scope", selectors=("SRC-1", "SRC-2")),
            ),
            "obligations": self._obligations(),
            "instructions": StageInstructionConfig(
                role="writer",
                scenario="writer.session_prepared_initial_draft",
                output_path="work/output.md",
                attempt_root="work/attempt-001",
                sandbox_policy="workspace_write",
                timeout_seconds=180,
                idle_timeout_seconds=60,
                command_budget=12,
            ),
            "execution_profile": "simple-field-property",
            "unsupported_dimensions": (),
            "forbidden_evidence_roots": ("fts/demo-ft/test-cases",),
        }

        with self.assertRaisesRegex(StageRuntimeError, "DOCX.*XHTML"):
            PreparedPackageBuilder(self.root).build(
                output_root=self.root / "work" / "missing-xhtml",
                source_registry=((self.docx, "source-of-truth", "section 4.3"),),
                **common,
            )
        with self.assertRaisesRegex(StageRuntimeError, "DOCX.*XHTML"):
            PreparedPackageBuilder(self.root).build(
                output_root=self.root / "work" / "missing-docx",
                source_registry=((self.xhtml, "machine-readable", "SRC-1..SRC-2"),),
                **common,
            )

    def test_version_one_package_remains_readable_but_is_unclassified(self) -> None:
        self._build()
        manifest = self.root / "work" / "prepared" / "stage-package.json"
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        payload["package_version"] = 1
        payload.pop("execution_profile")
        payload.pop("unsupported_dimensions")
        payload.pop("input_fingerprint")
        without_digest = {key: value for key, value in payload.items() if key != "package_digest"}
        payload["package_digest"] = hashlib.sha256(
            json.dumps(
                without_digest,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        loaded = load_prepared_package(manifest, self.root)
        self.assertEqual("legacy-unclassified", loaded.execution_profile)
        self.assertEqual(("legacy-unclassified",), loaded.unsupported_dimensions)

    def test_version_two_obligations_remain_readable_but_cannot_build_fast_path(self) -> None:
        dictionary_claim = PreparedObligation(
            obligation_id="ATOM-LEGACY-001",
            source_refs=("SRC-1",),
            atomic_statement="Значения берутся из справочника и допускают одиночный выбор.",
            observable_oracle="В поле остается одно выбранное значение.",
            test_intent="Проверить одиночный выбор.",
            coverage_status="testable",
            gap_id="",
            dictionary_refs=(),
            notes="Historical v2 evidence.",
        )
        payload = {
            "package_version": 2,
            "package_id": "pkg-001",
            "obligations": [dictionary_claim.to_dict()],
            "coverage_gaps": [],
        }
        payload["digest"] = hashlib.sha256(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        legacy = PreparedObligationSet.from_dict(payload)

        self.assertEqual(2, legacy.package_version)
        with self.assertRaisesRegex(StageRuntimeError, "requires package version 7"):
            PreparedPackageBuilder(self.root).build(
                output_root=self.root / "work" / "legacy-fast",
                package_id="pkg-001",
                ft_slug="demo-ft",
                scope_slug="field-selection",
                section_id="4.3",
                source_registry=((self.docx, "source-of-truth", "section 4.3"),),
                evidence_inputs=(
                    EvidenceInput(self.evidence, "Confirmed scope", selectors=("SRC-1",)),
                ),
                obligations=legacy,
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
                execution_profile="simple-field-property",
                unsupported_dimensions=(),
                forbidden_evidence_roots=("fts/demo-ft/test-cases",),
            )

    def test_version_five_obligations_remain_readable_without_state_change_fields(self) -> None:
        current = self._obligations()
        payload = {
            "package_version": 5,
            "package_id": current.package_id,
            "obligations": [
                item.to_dict(include_constraints=True, include_atom_id=True)
                for item in current.obligations
            ],
            "coverage_gaps": [item.to_dict() for item in current.coverage_gaps],
        }
        payload["digest"] = hashlib.sha256(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        legacy = PreparedObligationSet.from_dict(payload)

        self.assertEqual(5, legacy.package_version)
        self.assertEqual("direct", legacy.obligations[0].execution_semantics)
        self.assertIsNone(legacy.obligations[0].state_change)
        self.assertEqual(payload, legacy.to_dict())

    def test_version_four_obligations_remain_readable_without_explicit_atom_field(self) -> None:
        current = self._obligations()
        payload = {
            "package_version": 4,
            "package_id": current.package_id,
            "obligations": [
                item.to_dict(include_constraints=True) for item in current.obligations
            ],
            "coverage_gaps": [item.to_dict() for item in current.coverage_gaps],
        }
        payload["digest"] = hashlib.sha256(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        legacy = PreparedObligationSet.from_dict(payload)

        self.assertEqual(4, legacy.package_version)
        self.assertEqual("ATOM-001", legacy.obligations[0].traceability_atom_id)

    def test_scope_local_selector_excludes_unrelated_markdown_sections(self) -> None:
        self.evidence.write_text(
            "# Scope\n\n## Selected\nSRC-1: required evidence.\n\n"
            "## Unrelated\nSECRET-UNRELATED-CONTENT\nSRC-2: second evidence.\n",
            encoding="utf-8",
        )
        package = PreparedPackageBuilder(self.root).build(
            output_root=self.root / "work" / "sliced",
            package_id="pkg-001",
            ft_slug="demo-ft",
            scope_slug="field-selection",
            section_id="4.3",
            source_registry=(
                (self.docx, "source-of-truth", "section 4.3"),
                (self.xhtml, "machine-readable", "SRC-1"),
            ),
            evidence_inputs=(
                EvidenceInput(self.evidence, "Selected evidence", selectors=("SRC-1",)),
            ),
            obligations=PreparedObligationSet.create(
                package_id="pkg-001",
                obligations=(self._obligations().obligations[0],),
                coverage_gaps=(),
            ),
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
            execution_profile="simple-field-property",
            unsupported_dimensions=(),
            forbidden_evidence_roots=("fts/demo-ft/test-cases",),
        )
        evidence_path = next(
            item.path for item in package.package_artifacts if item.kind == "source-evidence"
        )
        text = (self.root / evidence_path).read_text(encoding="utf-8")
        self.assertIn("required evidence", text)
        self.assertNotIn("SECRET-UNRELATED-CONTENT", text)

    def test_missing_evidence_selector_blocks_package(self) -> None:
        with self.assertRaisesRegex(StageRuntimeError, "selector not found"):
            PreparedPackageBuilder(self.root).build(
                output_root=self.root / "work" / "missing-selector",
                package_id="pkg-001",
                ft_slug="demo-ft",
                scope_slug="field-selection",
                section_id="4.3",
                source_registry=((self.docx, "source-of-truth", "section 4.3"),),
                evidence_inputs=(
                    EvidenceInput(self.evidence, "Evidence", selectors=("SRC-404",)),
                ),
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
                execution_profile="simple-field-property",
                unsupported_dimensions=(),
                forbidden_evidence_roots=("fts/demo-ft/test-cases",),
            )


if __name__ == "__main__":
    unittest.main()
