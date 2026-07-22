from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any
from unittest.mock import patch

import test_case_agent.derivation_compiler as derivation_compiler_module
from test_case_agent.coverage_graph import build_coverage_graph
from test_case_agent.coverage_io import (
    load_property_derivations,
    write_property_derivations,
)
from test_case_agent.derivation_compiler import (
    DerivationCompilationError,
    compile_property_derivations,
    extract_semantic_compiler_projection,
)
from test_case_agent.review_cycle.prepared_package import (
    PreparedObligation,
    PreparedObligationSet,
)
from test_case_agent.review_cycle.source_assertions import (
    NO_REQUIRED_CHANGE,
    SourceAssertion,
)


def _canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class _Manifest:
    scope_slug: str
    assertions: tuple[SourceAssertion, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 4,
            "scope_slug": self.scope_slug,
            "assertions": [item.to_dict() for item in self.assertions],
        }

    @property
    def digest(self) -> str:
        return _canonical_sha(self.to_dict())


class DerivationCompilerTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.work = self.root / "fts" / "sample" / "work" / "handoff"
        self.work.mkdir(parents=True)

    def test_default_discards_interaction_trigger_from_initial_state_contract(self) -> None:
        self.assertEqual(
            "",
            derivation_compiler_module._effective_validation_trigger(
                property_kind="default",
                action_contract="Перевести фокус в поле «Телефон».",
            ),
        )
        self.assertEqual(
            "Нажать «Добавить».",
            derivation_compiler_module._effective_validation_trigger(
                property_kind="visibility",
                action_contract="Нажать «Добавить».",
            ),
        )

    def test_positive_and_negative_persistence_require_commit_trigger(self) -> None:
        for polarity, oracle in (
            ("positive", "Поле сохраняет текущую дату."),
            ("negative", "Поле не сохраняет будущую дату."),
            ("positive", "В поле сохранено значение «отец/мать»."),
        ):
            with self.subTest(polarity=polarity):
                mutation = (
                    "Выбрать «отец/мать»."
                    if "отец/мать" in oracle
                    else "Ввести тестовое значение."
                )
                self.assertTrue(
                    derivation_compiler_module._needs_validation_trigger_calibration(
                        polarity=polarity,
                        oracle=oracle,
                        action=mutation,
                    )
                )
                self.assertFalse(
                    derivation_compiler_module._needs_validation_trigger_calibration(
                        polarity=polarity,
                        oracle=oracle,
                        action=f"{mutation}; Сохранить карточку.",
                    )
                )
        for action in (
            "Сохранить карточку; Ввести X.",
            "Reopen the card.",
            "Enter X; Close the tooltip.",
            "Enter X; Confirm that the hint is absent.",
            "Enter X; Confirm.",
            "Enter X; Continue editing another field.",
            "Enter X; Refresh the tooltip.",
            "Enter X; Verify that the archive button is visible.",
            "Enter X; Open storage; Check storage page title.",
            "Ввести X; Отправить SMS.",
            "Ввести X; Проверить кнопку «Сохранить».",
        ):
            with self.subTest(action=action):
                self.assertTrue(
                    derivation_compiler_module._needs_validation_trigger_calibration(
                        polarity="positive",
                        oracle="The value is saved.",
                        action=action,
                    )
                )
        self.assertFalse(
            derivation_compiler_module._needs_validation_trigger_calibration(
                polarity="positive",
                oracle="The value is saved.",
                action="Enter X and save the card.",
            )
        )
        self.assertFalse(
            derivation_compiler_module._needs_validation_trigger_calibration(
                polarity="positive",
                oracle="The selected option is retained after selection.",
                action="Select X.",
            )
        )
        self.assertFalse(
            derivation_compiler_module._needs_validation_trigger_calibration(
                polarity="positive",
                oracle=(
                    "Поле отображает Петров-Сидоров; символ '-' сохранен."
                ),
                action="Ввести Петров-Сидоров.",
            )
        )
        self.assertTrue(
            derivation_compiler_module._needs_validation_trigger_calibration(
                polarity="positive",
                oracle=(
                    "После повторного открытия карточки поле содержит X."
                ),
                action="Выбрать X.",
            )
        )
        self.assertFalse(
            derivation_compiler_module._needs_validation_trigger_calibration(
                polarity="positive",
                oracle="Значение сохранено.",
                action=(
                    "Ввести X; Сохранить карточку; "
                    "Проверить кнопку «Добавить»."
                ),
            )
        )
        for decision in ("Да", "Нет"):
            with self.subTest(decision=decision):
                self.assertFalse(
                    derivation_compiler_module._needs_validation_trigger_calibration(
                        polarity="positive",
                        oracle=(
                            "При повторном открытии раздела поле отображает "
                            "сохраненное значение."
                        ),
                        action=(
                            "Изменить значение; Нажать `Назад`; "
                            f"В уведомлении выбрать `{decision}`; "
                            "Вернуться в раздел."
                        ),
                    )
                )
        self.assertTrue(
            derivation_compiler_module._needs_validation_trigger_calibration(
                polarity="negative",
                oracle="Сохранение блокируется.",
                action="Ввести будущую дату.",
            )
        )
        self.assertFalse(
            derivation_compiler_module._needs_validation_trigger_calibration(
                polarity="negative",
                oracle="Сохранение блокируется.",
                action="Ввести будущую дату; Сохранить карточку.",
            )
        )
        for action in (
            "Ввести будущую дату; Попытаться сохранить карточку.",
            "Ввести будущую дату; Выполнить подтверждение формы.",
        ):
            with self.subTest(action=action):
                self.assertFalse(
                    derivation_compiler_module._needs_validation_trigger_calibration(
                        polarity="negative",
                        oracle="Сохранение формы запрещено.",
                        action=action,
                    )
                )
        self.assertFalse(
            derivation_compiler_module._needs_validation_trigger_calibration(
                polarity="positive",
                oracle="Документ сохранен в электронном архиве.",
                action=(
                    "Добавить файл; Проверить запись о сохранении документа "
                    "в электронном архиве."
                ),
            )
        )
        self.assertTrue(
            derivation_compiler_module._needs_validation_trigger_calibration(
                polarity="positive",
                oracle="The value is retained after reopening.",
                action="Navigate to the block; Enter X.",
            )
        )
        self.assertFalse(
            derivation_compiler_module._needs_validation_trigger_calibration(
                polarity="positive",
                oracle="The value is retained after reopening.",
                action="Enter X; Reopen the card.",
            )
        )
        self.assertFalse(
            derivation_compiler_module._needs_validation_trigger_calibration(
                polarity="positive",
                oracle="Кнопка «Сохранить» отображается.",
                action="Открыть форму.",
            )
        )
        self.assertEqual(
            "его принятие",
            derivation_compiler_module._calibration_outcome("positive"),
        )
        self.assertEqual(
            "его отклонение",
            derivation_compiler_module._calibration_outcome("negative"),
        )

    @staticmethod
    def _assertion(*, calibration: bool = False) -> SourceAssertion:
        oracle = (
            "Точная UI-реакция требует калибровки."
            if calibration
            else "Поле «Имя» отображается."
        )
        return SourceAssertion(
            assertion_id="ASSERT-001",
            source_path="fts/sample/source/main.xhtml",
            source_context_class="scope-local",
            locator="/*/*[1]",
            exact_source_text="BSR 1. Поле «Имя» отображается.",
            canonical_statement="Поле «Имя» отображается.",
            polarity="negative" if calibration else "positive",
            semantic_disposition="testable",
            execution_readiness="ready",
            execution_readiness_rationale=NO_REQUIRED_CHANGE,
            risk="medium",
            condition_clauses=("Открыта анкета.",),
            action_clauses=(
                "Ввести значение «1» в поле «Имя»."
                if calibration
                else "Проверить поле «Имя»."
            ,),
            oracle_clauses=(oracle,),
            requirement_codes=("BSR 1",),
            requirement_code_bindings=(),
            clause_evidence_bindings=(),
            source_row_id="SRC-001",
            atom_id="ATOM-001",
            obligation_ids=("OBL-001",),
            execution_dependency_gap_ids=(),
            primary_gap_id=None,
        )

    def _fixture(self, *, calibration: bool = False):
        assertion = self._assertion(calibration=calibration)
        manifest = _Manifest("sample-scope", (assertion,))
        oracle = assertion.oracle_clauses[0]
        obligation = PreparedObligation(
            obligation_id="OBL-001",
            source_refs=("SRC-001", "BSR 1"),
            atomic_statement=(
                "Значение «1» требует проверки."
                if calibration
                else "Поле «Имя» отображается."
            ),
            observable_oracle=oracle,
            test_intent=(
                "Action contract: Ввести значение «1»; Test data: 1"
                if calibration
                else "Проверить поле «Имя»; Test data: Иван"
            ),
            coverage_status="testable",
            gap_id="",
            dictionary_refs=(),
            notes="",
            atom_id="ATOM-001",
            calibration_status=(
                "ui-calibration-required" if calibration else "none"
            ),
        )
        obligations = PreparedObligationSet.create(
            package_id="WP-01",
            obligations=(obligation,),
            coverage_gaps=(),
        )
        semantic_obligation = {
            "obligation_id": "OBL-001",
            "package_id": "WP-01",
            "linked_atom_id": "ATOM-001",
            "property_type": "format" if calibration else "visibility",
            "obligation_class": (
                "candidate-ui-calibration" if calibration else "visible"
            ),
            "coverage_class": "invalid-class" if calibration else "visible",
            "oracle_source": "not_found" if calibration else "BSR 1",
            "scope_obligation_ids": [],
            "planned_tc_id": "candidate:NAME-DIGIT" if calibration else "TC-001",
            "single_expected_behavior": oracle,
            "test_data": "1" if calibration else "Иван",
        }
        semantic_assertion = {
            "assertion_id": assertion.assertion_id,
            "canonical_statement": assertion.canonical_statement,
            "polarity": assertion.polarity,
            "semantic_disposition": assertion.semantic_disposition,
            "execution_readiness": assertion.execution_readiness,
            "risk": assertion.risk,
            "condition_clauses": list(assertion.condition_clauses),
            "action_clauses": list(assertion.action_clauses),
            "oracle_clauses": list(assertion.oracle_clauses),
            "requirement_codes": list(assertion.requirement_codes),
            "atom_id": assertion.atom_id,
            "obligation_ids": list(assertion.obligation_ids),
            "field_or_block": "Имя",
        }
        semantic = {
            "version": 4,
            "contract": "semantic-design-bridge-v2",
            "status": "ready",
            "source_designs": [{"assertions": [semantic_assertion]}],
            "obligations": [semantic_obligation],
        }
        semantic_path = self.work / "semantic-design.json"
        semantic_path.write_text(
            json.dumps(semantic, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        boundary_path = self.work / "scope-boundary.json"
        boundary_path.write_text("{}\n", encoding="utf-8")
        decision_sha = "a" * 64
        semantic_sha = hashlib.sha256(semantic_path.read_bytes()).hexdigest()
        receipt = {
            "status": "verified",
            "source_assertion_manifest_digest": manifest.digest,
            "semantic_design_artifact_sha256": semantic_sha,
            "semantic_design_decision_sha256": decision_sha,
        }
        receipt_path = self.work / "bridge-receipt.json"
        receipt_path.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        def artifact(path: Path, **extra: str) -> dict[str, str]:
            return {
                "path": path.relative_to(self.root).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                **extra,
            }

        projection = {
            "contract": "semantic-design-compiler-projection-v1",
            "semantic_design_artifact": artifact(
                semantic_path, decision_sha256=decision_sha
            ),
            "scope_boundary_artifact": artifact(
                boundary_path, decision_sha256="b" * 64
            ),
            "bridge_receipt_artifact": artifact(receipt_path),
            "bridge_receipt": receipt,
            "boundary_gaps": [],
            "obligations": [semantic_obligation],
            "dependency_bindings": [],
            "negative_oracles": [],
            "requiredness_oracles": [],
            "oracle_inventories": [],
        }
        return manifest, obligations, projection, semantic_path

    def test_projection_extraction_is_bounded_and_duplicate_rejecting(self) -> None:
        _, _, projection, _ = self._fixture()
        evidence = (
            "# Evidence\n\n"
            "## Immutable semantic-design bridge projection\n\n```json\n"
            + json.dumps(projection, ensure_ascii=False)
            + "\n```\n"
        )
        self.assertEqual(
            "semantic-design-compiler-projection-v1",
            extract_semantic_compiler_projection(evidence)["contract"],
        )
        with self.assertRaisesRegex(
            DerivationCompilationError, "semantic-projection-count"
        ):
            extract_semantic_compiler_projection(evidence + evidence)

    def test_compiles_and_round_trips_without_manual_derivation(self) -> None:
        manifest, obligations, projection, _ = self._fixture()
        compiled = compile_property_derivations(
            repo_root=self.root,
            ft_slug="sample",
            source_manifest=manifest,  # type: ignore[arg-type]
            obligation_set=obligations,
            semantic_projection=projection,
        )
        path = self.work / "derivations.json"
        write_property_derivations(path, compiled.document)
        loaded = load_property_derivations(
            path,
            expected_source_manifest_digest=manifest.digest,
            expected_obligation_set_digest=obligations.digest,
        )

        self.assertEqual("visibility", loaded.derivations[0].property_kind)
        self.assertEqual(("Иван",), loaded.derivations[0].fixture_values["OBL-001"])
        self.assertEqual(3, len(compiled.registered_artifacts))
        self.assertNotEqual("always", loaded.derivations[0].condition_key)
        self.assertEqual(("Имя",), tuple(compiled.subject_labels.values()))
        self.assertEqual(
            ("Открыта анкета.",),
            tuple(compiled.condition_preconditions.values()),
        )

    def test_subject_label_can_bind_to_exact_source_row_context(self) -> None:
        assertion = replace(
            self._assertion(),
            canonical_statement="Текущее значение допускается.",
            oracle_clauses=("Текущее значение допускается.",),
        )
        semantic = {
            "canonical_statement": assertion.canonical_statement,
            "polarity": assertion.polarity,
            "semantic_disposition": assertion.semantic_disposition,
            "execution_readiness": assertion.execution_readiness,
            "risk": assertion.risk,
            "condition_clauses": list(assertion.condition_clauses),
            "action_clauses": list(assertion.action_clauses),
            "oracle_clauses": list(assertion.oracle_clauses),
            "requirement_codes": list(assertion.requirement_codes),
            "atom_id": assertion.atom_id,
            "obligation_ids": list(assertion.obligation_ids),
            "field_or_block": "Имя",
        }

        self.assertEqual(
            "Имя",
            derivation_compiler_module._validate_assertion_projection(
                assertion,
                semantic,
                require_bound_subject=True,
            ),
        )

    def test_negative_save_oracle_without_trigger_is_downgraded_to_calibration(self) -> None:
        manifest, obligations, projection, semantic_path = self._fixture()
        assertion = replace(
            manifest.assertions[0],
            polarity="negative",
            canonical_statement="Недопустимое значение не допускается.",
            action_clauses=("Ввести недопустимое значение.",),
            oracle_clauses=("Поле не сохраняет недопустимое значение.",),
        )
        manifest = _Manifest(manifest.scope_slug, (assertion,))
        obligation = replace(
            obligations.obligations[0],
            atomic_statement=assertion.canonical_statement,
            observable_oracle=assertion.oracle_clauses[0],
        )
        obligations = PreparedObligationSet.create(
            package_id=obligations.package_id,
            obligations=(obligation,),
            coverage_gaps=(),
        )
        semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
        semantic_assertion = semantic["source_designs"][0]["assertions"][0]
        semantic_assertion.update(
            {
                "canonical_statement": assertion.canonical_statement,
                "polarity": assertion.polarity,
                "action_clauses": list(assertion.action_clauses),
                "oracle_clauses": list(assertion.oracle_clauses),
            }
        )
        semantic_path.write_text(
            json.dumps(semantic, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        semantic_sha = hashlib.sha256(semantic_path.read_bytes()).hexdigest()
        projection["semantic_design_artifact"]["sha256"] = semantic_sha
        receipt_path = self.work / "bridge-receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt.update(
            {
                "source_assertion_manifest_digest": manifest.digest,
                "semantic_design_artifact_sha256": semantic_sha,
            }
        )
        receipt_path.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        projection["bridge_receipt"] = receipt
        projection["bridge_receipt_artifact"]["sha256"] = hashlib.sha256(
            receipt_path.read_bytes()
        ).hexdigest()
        projection["negative_oracles"] = [
            {
                "linked_obligation_id": "OBL-001",
                "scope_obligation_id": "SO-NEG-001",
                "analyst_question": "",
            }
        ]

        compiled = compile_property_derivations(
            repo_root=self.root,
            ft_slug="sample",
            source_manifest=manifest,  # type: ignore[arg-type]
            obligation_set=obligations,
            semantic_projection=projection,
        )
        derivation = compiled.document.derivations[0]
        self.assertEqual(
            "SO-NEG-001",
            derivation.source_oracle_ids["OBL-001"],
        )
        self.assertIn("OBL-001", derivation.calibration_questions)
        self.assertIn("Имя", derivation.calibration_questions["OBL-001"])
        self.assertIn("Иван", derivation.calibration_questions["OBL-001"])
        self.assertIn("отклонение", derivation.calibration_questions["OBL-001"])
        graph = build_coverage_graph(
            ft_slug="sample",
            tc_prefix="SMP",
            source_manifest=manifest,  # type: ignore[arg-type]
            obligation_set=obligations,
            derivations=compiled.document.derivations,
        )
        self.assertEqual("candidate-ui-calibration", graph.cases[0].status)
        self.assertEqual(
            "Недопустимое значение не допускается.",
            graph.obligations[0].observable_oracle,
        )
        self.assertNotIn("не сохраня", graph.obligations[0].observable_oracle)
        self.assertEqual(
            "ui-calibration-required",
            graph.obligations[0].calibration_status,
        )

    def test_direct_candidate_gets_typed_calibration_owner_and_graph_case(self) -> None:
        manifest, obligations, projection, _ = self._fixture(calibration=True)
        compiled = compile_property_derivations(
            repo_root=self.root,
            ft_slug="sample",
            source_manifest=manifest,  # type: ignore[arg-type]
            obligation_set=obligations,
            semantic_projection=projection,
        )
        derivation = compiled.document.derivations[0]
        self.assertRegex(derivation.source_oracle_ids["OBL-001"], r"^SO-CAL-")
        graph = build_coverage_graph(
            ft_slug="sample",
            tc_prefix="SMP",
            source_manifest=manifest,  # type: ignore[arg-type]
            obligation_set=obligations,
            derivations=compiled.document.derivations,
        )
        self.assertEqual("candidate-ui-calibration", graph.cases[0].status)

    def test_block_structure_supplies_human_scope_title_and_base_precondition(self) -> None:
        manifest, obligations, projection, semantic_path = self._fixture()
        semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
        semantic["obligations"][0]["property_type"] = "block-structure"
        semantic["source_designs"][0]["assertions"][0]["field_or_block"] = (
            "Блок «Контактные лица»"
        )
        semantic_path.write_text(
            json.dumps(semantic, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        semantic_sha = hashlib.sha256(semantic_path.read_bytes()).hexdigest()
        projection["obligations"][0]["property_type"] = "block-structure"
        projection["semantic_design_artifact"]["sha256"] = semantic_sha
        receipt_path = self.work / "bridge-receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["semantic_design_artifact_sha256"] = semantic_sha
        receipt_path.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        projection["bridge_receipt"] = receipt
        projection["bridge_receipt_artifact"]["sha256"] = hashlib.sha256(
            receipt_path.read_bytes()
        ).hexdigest()

        compiled = compile_property_derivations(
            repo_root=self.root,
            ft_slug="sample",
            source_manifest=manifest,  # type: ignore[arg-type]
            obligation_set=obligations,
            semantic_projection=projection,
        )

        self.assertEqual("Блок «Контактные лица»", compiled.scope_title)
        self.assertEqual(("Открыта анкета.",), compiled.base_preconditions)

    def test_artifact_drift_fails_closed(self) -> None:
        manifest, obligations, projection, semantic_path = self._fixture()
        semantic_path.write_text("{}\n", encoding="utf-8")
        with self.assertRaisesRegex(
            DerivationCompilationError, "artifact-hash-mismatch"
        ):
            compile_property_derivations(
                repo_root=self.root,
                ft_slug="sample",
                source_manifest=manifest,  # type: ignore[arg-type]
                obligation_set=obligations,
                semantic_projection=projection,
            )

    def test_mutation_between_hash_and_parse_cannot_rebase_semantics(self) -> None:
        manifest, obligations, projection, semantic_path = self._fixture()
        original = derivation_compiler_module._read_json_object_bytes

        def mutate_before_parse(raw: bytes, label: str):
            if label == "semantic design":
                semantic_path.write_text("{}\n", encoding="utf-8")
            return original(raw, label)

        with patch(
            "test_case_agent.derivation_compiler._read_json_object_bytes",
            side_effect=mutate_before_parse,
        ), self.assertRaisesRegex(DerivationCompilationError, "artifact-drift"):
            compile_property_derivations(
                repo_root=self.root,
                ft_slug="sample",
                source_manifest=manifest,  # type: ignore[arg-type]
                obligation_set=obligations,
                semantic_projection=projection,
            )


if __name__ == "__main__":
    unittest.main()
