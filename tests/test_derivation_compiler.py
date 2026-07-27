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
    compile_source_first_property_derivations,
    extract_optional_semantic_compiler_projection,
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
from test_case_agent.test_design import DesignContext, build_test_design_plan


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

    def test_source_first_default_fixture_uses_oracle_value_not_block_label(self) -> None:
        assertion = replace(
            self._assertion(),
            assertion_id="ASSERT-PASS-CUR-028",
            atom_id="ATOM-028",
            obligation_ids=("OBL-PASS-CUR-028",),
            exact_source_text=(
                "Блок «Паспортные данные». BSR 104. "
                "Переключатель «Клиент менял паспорт» по умолчанию имеет значение «Нет»."
            ),
            canonical_statement=(
                "Переключатель «Клиент менял паспорт» по умолчанию имеет значение «Нет»."
            ),
            action_clauses=(
                "Не взаимодействуя с переключателем «Клиент менял паспорт», проверить его первоначальное значение.",
            ),
            oracle_clauses=(
                "Переключатель «Клиент менял паспорт» имеет значение «Нет».",
            ),
            requirement_codes=("BSR 104",),
        )
        obligations = PreparedObligationSet.create(
            package_id="WP-01",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-PASS-CUR-028",
                    source_refs=("SRC-001", "BSR 104"),
                    atomic_statement=assertion.canonical_statement,
                    observable_oracle=assertion.oracle_clauses[0],
                    test_intent=(
                        "Action contract: Не взаимодействуя с переключателем "
                        "«Клиент менял паспорт», проверить его первоначальное значение.; "
                        "Test data: Блок «Паспортные данные»."
                    ),
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    atom_id="ATOM-028",
                ),
            ),
            coverage_gaps=(),
        )

        compiled = compile_source_first_property_derivations(
            repo_root=self.root,
            ft_slug="sample",
            source_manifest=_Manifest("4-3-current-passport-data", (assertion,)),  # type: ignore[arg-type]
            obligation_set=obligations,
        )
        derivation = compiled.document.derivations[0]

        self.assertEqual("default", derivation.property_kind)
        self.assertEqual(
            ("Нет",),
            derivation.fixture_values["OBL-PASS-CUR-028"],  # type: ignore[index]
        )

    def test_source_first_allows_exact_split_oracle_clauses_across_obligations(self) -> None:
        assertion = replace(
            self._assertion(),
            assertion_id="ASSERT-SPLIT",
            atom_id="ATOM-SPLIT",
            exact_source_text="AS 6. The widget displays primary and secondary values.",
            canonical_statement="The widget displays primary and secondary values.",
            action_clauses=("Open the widget.",),
            oracle_clauses=("Primary value is displayed.", "Secondary value is displayed."),
            requirement_codes=("AS 6",),
            obligation_ids=("OBL-PRIMARY", "OBL-SECONDARY"),
        )
        obligations = PreparedObligationSet.create(
            package_id="WP-01",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-PRIMARY",
                    source_refs=("SRC-001", "AS 6"),
                    atomic_statement="The widget displays primary value.",
                    observable_oracle=assertion.oracle_clauses[0],
                    test_intent="Open the widget and check the primary value.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    atom_id="ATOM-SPLIT",
                ),
                PreparedObligation(
                    obligation_id="OBL-SECONDARY",
                    source_refs=("SRC-001", "AS 6"),
                    atomic_statement="The widget displays secondary value.",
                    observable_oracle=assertion.oracle_clauses[1],
                    test_intent="Open the widget and check the secondary value.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    atom_id="ATOM-SPLIT",
                ),
            ),
            coverage_gaps=(),
        )

        compiled = compile_source_first_property_derivations(
            repo_root=self.root,
            ft_slug="sample",
            source_manifest=_Manifest("sample-scope", (assertion,)),  # type: ignore[arg-type]
            obligation_set=obligations,
        )

        derivation = compiled.document.derivations[0]
        self.assertEqual(
            {"OBL-PRIMARY", "OBL-SECONDARY"},
            set(derivation.obligation_variants),
        )

    def test_source_first_rejects_split_oracle_when_clause_is_lost(self) -> None:
        assertion = replace(
            self._assertion(),
            assertion_id="ASSERT-SPLIT",
            atom_id="ATOM-SPLIT",
            exact_source_text="AS 6. The widget displays primary and secondary values.",
            canonical_statement="The widget displays primary and secondary values.",
            action_clauses=("Open the widget.",),
            oracle_clauses=("Primary value is displayed.", "Secondary value is displayed."),
            requirement_codes=("AS 6",),
            obligation_ids=("OBL-PRIMARY", "OBL-SECONDARY"),
        )
        obligations = PreparedObligationSet.create(
            package_id="WP-01",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-PRIMARY",
                    source_refs=("SRC-001", "AS 6"),
                    atomic_statement="The widget displays primary value.",
                    observable_oracle=assertion.oracle_clauses[0],
                    test_intent="Open the widget and check the primary value.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    atom_id="ATOM-SPLIT",
                ),
                PreparedObligation(
                    obligation_id="OBL-SECONDARY",
                    source_refs=("SRC-001", "AS 6"),
                    atomic_statement="The widget displays secondary value.",
                    observable_oracle=assertion.oracle_clauses[0],
                    test_intent="Open the widget and check the secondary value.",
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    atom_id="ATOM-SPLIT",
                ),
            ),
            coverage_gaps=(),
        )

        with self.assertRaisesRegex(
            DerivationCompilationError,
            "accepted oracle clauses are not covered",
        ):
            compile_source_first_property_derivations(
                repo_root=self.root,
                ft_slug="sample",
                source_manifest=_Manifest("sample-scope", (assertion,)),  # type: ignore[arg-type]
                obligation_set=obligations,
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
        self.assertTrue(
            derivation_compiler_module._needs_validation_trigger_calibration(
                polarity="positive",
                oracle=(
                    "Просроченный паспорт блокирует сохранение с подсказкой "
                    "«Паспорт недействителен (просрочен)»."
                ),
                action="Инициировать проверку срока действия паспорта.",
            )
        )
        self.assertFalse(
            derivation_compiler_module._needs_validation_trigger_calibration(
                polarity="positive",
                oracle=(
                    "Просроченный паспорт блокирует сохранение с подсказкой "
                    "«Паспорт недействителен (просрочен)»."
                ),
                action=(
                    "Ввести дату выдачи паспорта; "
                    "Инициировать проверку срока действия паспорта."
                ),
            )
        )
        self.assertFalse(
            derivation_compiler_module._needs_validation_trigger_calibration(
                polarity="positive",
                oracle=(
                    "Просроченный паспорт блокирует сохранение с подсказкой "
                    "«Паспорт недействителен (просрочен)»."
                ),
                action=(
                    "Ввести дату выдачи паспорта; Попытаться сохранить карточку."
                ),
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
        self.assertIsNone(
            extract_optional_semantic_compiler_projection(
                "# Accepted source evidence without bridge\n"
            )
        )

    def test_source_first_compiles_without_semantic_projection(self) -> None:
        manifest, obligations, _projection, _ = self._fixture()

        compiled = compile_source_first_property_derivations(
            repo_root=self.root,
            ft_slug="sample",
            source_manifest=manifest,  # type: ignore[arg-type]
            obligation_set=obligations,
        )

        self.assertEqual((), compiled.registered_artifacts)
        self.assertEqual((), compiled.registered_artifact_snapshots)
        derivation = compiled.document.derivations[0]
        self.assertEqual("visibility", derivation.property_kind)
        self.assertEqual({"OBL-001": "visible"}, derivation.obligation_variants)
        self.assertEqual("OBL-001", next(iter(derivation.fixture_values)))
        self.assertNotEqual("always", derivation.condition_key)
        self.assertEqual(
            tuple(compiled.condition_preconditions.values()),
            (manifest.assertions[0].condition_clauses[0],),
        )

    def test_source_first_case_identity_keeps_subject_and_branch_distinct(self) -> None:
        base = self._assertion()
        assertions = (
            replace(
                base,
                assertion_id="ASSERT-PASS-CUR-017",
                source_row_id="SRC-PASS-CUR-006",
                atom_id="ATOM-017",
                obligation_ids=("OBL-PASS-CUR-017",),
                exact_source_text=(
                    "Ввести вручную подразделение Нет Да Переключатель "
                    "Логическое Да/Нет BSR 96. Видимость-всегда."
                ),
                canonical_statement=(
                    "Переключатель «Ввести вручную подразделение» отображается."
                ),
                condition_clauses=("Открыт блок «Паспортные данные».",),
                action_clauses=("Открыть блок «Паспортные данные».",),
                oracle_clauses=(
                    "Переключатель «Ввести вручную подразделение» отображается.",
                ),
                requirement_codes=("BSR 96",),
            ),
            replace(
                base,
                assertion_id="ASSERT-PASS-CUR-027",
                source_row_id="SRC-PASS-CUR-010",
                atom_id="ATOM-027",
                obligation_ids=("OBL-PASS-CUR-027",),
                exact_source_text=(
                    "Клиент менял паспорт Да, если дата выдачи текущего паспорта "
                    "менее 3х лет назад. BSR 103. Видимость-всегда."
                ),
                canonical_statement=(
                    "Переключатель «Клиент менял паспорт» отображается."
                ),
                condition_clauses=("Открыт блок «Паспортные данные».",),
                action_clauses=("Открыть блок «Паспортные данные».",),
                oracle_clauses=(
                    "Переключатель «Клиент менял паспорт» отображается.",
                ),
                requirement_codes=("BSR 103",),
            ),
            replace(
                base,
                assertion_id="ASSERT-PASS-CUR-018",
                source_row_id="SRC-PASS-CUR-006",
                atom_id="ATOM-018",
                obligation_ids=("OBL-PASS-CUR-018",),
                exact_source_text=(
                    "Ввести вручную подразделение Нет Да Переключатель "
                    "Логическое Да/Нет BSR 97. Значение по умолчанию «Нет»."
                ),
                canonical_statement=(
                    "Значение по умолчанию для «Ввести вручную подразделение» "
                    "равно «Нет»."
                ),
                condition_clauses=(
                    "Открыт блок «Паспортные данные» без изменения признака.",
                ),
                action_clauses=("Открыть блок «Паспортные данные».",),
                oracle_clauses=("Переключатель имеет значение «Нет».",),
                requirement_codes=("BSR 97",),
            ),
            replace(
                base,
                assertion_id="ASSERT-PASS-CUR-028",
                source_row_id="SRC-PASS-CUR-010",
                atom_id="ATOM-028",
                obligation_ids=("OBL-PASS-CUR-028",),
                exact_source_text=(
                    "Клиент менял паспорт Да Переключатель Логическое Да/Нет "
                    "BSR 104. Значение по умолчанию «Нет»."
                ),
                canonical_statement=(
                    "Значение по умолчанию для «Клиент менял паспорт» равно «Нет»."
                ),
                condition_clauses=(
                    "Открыт блок «Паспортные данные» без изменения признака.",
                ),
                action_clauses=("Открыть блок «Паспортные данные».",),
                oracle_clauses=("Переключатель имеет значение «Нет».",),
                requirement_codes=("BSR 104",),
            ),
            replace(
                base,
                assertion_id="ASSERT-PASS-CUR-032",
                source_row_id="SRC-PASS-CUR-005",
                atom_id="ATOM-032",
                obligation_ids=("OBL-PASS-CUR-032",),
                exact_source_text=(
                    "Кем выдан Да, если признак «Ввести вручную подразделение» = "
                    "«Нет». BSR 93. Видимость: да, если признак = «Нет»."
                ),
                canonical_statement=(
                    "Поле «Кем выдан» обязательно при автозаполнении подразделения."
                ),
                condition_clauses=(
                    "Открыт блок «Паспортные данные»; поле является обязательным.",
                ),
                action_clauses=(
                    "Оставить поле «Кем выдан» пустым при "
                    "«Ввести вручную подразделение» = «Нет» и инициировать проверку.",
                ),
                oracle_clauses=(
                    "Поле подсвечено красным; под полем отображается текст "
                    "«Выберите значение».",
                ),
                requirement_codes=(),
            ),
            replace(
                base,
                assertion_id="ASSERT-PASS-CUR-033",
                source_row_id="SRC-PASS-CUR-007",
                atom_id="ATOM-033",
                obligation_ids=("OBL-PASS-CUR-033",),
                exact_source_text=(
                    "Кем выдан Если активирован признак «Ввести вручную "
                    "подразделение» = «Да». BSR 98. Видимость: Да, если признак = «Да»."
                ),
                canonical_statement=(
                    "Ручное поле «Кем выдан» обязательно при ручном вводе подразделения."
                ),
                condition_clauses=(
                    "Открыт блок «Паспортные данные»; поле является обязательным.",
                ),
                action_clauses=(
                    "Оставить ручное поле «Кем выдан» пустым при "
                    "«Ввести вручную подразделение» = «Да» и инициировать проверку.",
                ),
                oracle_clauses=(
                    "Поле подсвечено красным; под полем отображается текст "
                    "«Выберите значение».",
                ),
                requirement_codes=(),
            ),
        )
        manifest = _Manifest("4-3-current-passport-data", assertions)
        obligations = PreparedObligationSet.create(
            package_id="WP-01",
            obligations=tuple(
                PreparedObligation(
                    obligation_id=assertion.obligation_ids[0],
                    source_refs=(assertion.source_row_id, *assertion.requirement_codes),
                    atomic_statement=assertion.canonical_statement,
                    observable_oracle=assertion.oracle_clauses[0],
                    test_intent=(
                        f"Action contract: {assertion.action_clauses[0]}; "
                        "Test data: exact source-bound value"
                    ),
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    atom_id=assertion.atom_id,
                )
                for assertion in assertions
            ),
            coverage_gaps=(),
        )

        compiled = compile_source_first_property_derivations(
            repo_root=self.root,
            ft_slug="sample",
            source_manifest=manifest,  # type: ignore[arg-type]
            obligation_set=obligations,
        )
        derivations = {
            item.assertion_id: item for item in compiled.document.derivations
        }
        self.assertNotEqual(
            derivations["ASSERT-PASS-CUR-017"].subject_key,
            derivations["ASSERT-PASS-CUR-027"].subject_key,
        )
        self.assertEqual(
            "Ввести вручную подразделение",
            compiled.subject_labels[derivations["ASSERT-PASS-CUR-018"].subject_key],
        )
        self.assertEqual(
            "Клиент менял паспорт",
            compiled.subject_labels[derivations["ASSERT-PASS-CUR-028"].subject_key],
        )
        self.assertNotEqual(
            derivations["ASSERT-PASS-CUR-018"].subject_key,
            derivations["ASSERT-PASS-CUR-028"].subject_key,
        )
        self.assertEqual(
            "source-requiredness",
            derivations["ASSERT-PASS-CUR-032"].property_kind,
        )
        self.assertEqual(
            "source-requiredness",
            derivations["ASSERT-PASS-CUR-033"].property_kind,
        )
        self.assertEqual(
            "Кем выдан",
            compiled.subject_labels[derivations["ASSERT-PASS-CUR-032"].subject_key],
        )
        self.assertEqual(
            "Кем выдан",
            compiled.subject_labels[derivations["ASSERT-PASS-CUR-033"].subject_key],
        )
        self.assertNotEqual(
            derivations["ASSERT-PASS-CUR-032"].condition_key,
            derivations["ASSERT-PASS-CUR-033"].condition_key,
        )

        graph = build_coverage_graph(
            ft_slug="sample",
            tc_prefix="PASSCUR",
            source_manifest=manifest,  # type: ignore[arg-type]
            obligation_set=obligations,
            derivations=compiled.document.derivations,
        )
        self.assertEqual(6, len(graph.cases))
        self.assertEqual(6, len({item.case_key for item in graph.cases}))

    def test_source_first_format_representatives_do_not_use_action_phrases(self) -> None:
        base = self._assertion()
        assertions = (
            replace(
                base,
                assertion_id="ASSERT-PASS-CUR-005",
                atom_id="ATOM-005",
                obligation_ids=("OBL-PASS-CUR-005",),
                canonical_statement=(
                    "Поле «Серия» не допускает три одинаковые цифры подряд."
                ),
                action_clauses=("Ввести серию с тремя одинаковыми цифрами подряд.",),
                oracle_clauses=(
                    "Поле подсвечивается красным; отображается сообщение "
                    "«Не должно быть трех одинаковых цифр подряд».",
                ),
            ),
            replace(
                base,
                assertion_id="ASSERT-PASS-CUR-013",
                atom_id="ATOM-013",
                obligation_ids=("OBL-PASS-CUR-013",),
                canonical_statement=(
                    "Поле «Код подразделения» отображает формат заполнения xxx-xxx."
                ),
                action_clauses=("Ввести шесть цифр кода подразделения.",),
                oracle_clauses=("Значение отображается в форме `xxx-xxx`.",),
            ),
            replace(
                base,
                assertion_id="ASSERT-PASS-CUR-021",
                atom_id="ATOM-021",
                obligation_ids=("OBL-PASS-CUR-021",),
                canonical_statement=(
                    "Дата выдачи раньше 14-летия клиента недопустима."
                ),
                action_clauses=(
                    "Ввести дату выдачи раньше 14-летия клиента и инициировать "
                    "проверку сохранения.",
                ),
                oracle_clauses=(
                    "Сохранение блокируется с подсказкой "
                    "«Выдача паспорта предусмотрена с 14 лет».",
                ),
            ),
        )
        obligations = PreparedObligationSet.create(
            package_id="WP-01",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-PASS-CUR-005",
                    source_refs=("SRC-001",),
                    atomic_statement=assertions[0].canonical_statement,
                    observable_oracle=assertions[0].oracle_clauses[0],
                    test_intent=(
                        "Action contract: Ввести серию с тремя одинаковыми цифрами "
                        "подряд.; Test data: Ввести серию с тремя одинаковыми "
                        "цифрами подряд."
                    ),
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    atom_id="ATOM-005",
                ),
                PreparedObligation(
                    obligation_id="OBL-PASS-CUR-013",
                    source_refs=("SRC-001",),
                    atomic_statement=assertions[1].canonical_statement,
                    observable_oracle=assertions[1].oracle_clauses[0],
                    test_intent=(
                        "Action contract: Ввести шесть цифр кода подразделения.; "
                        "Test data: Ввести шесть цифр кода подразделения."
                    ),
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    atom_id="ATOM-013",
                ),
                PreparedObligation(
                    obligation_id="OBL-PASS-CUR-021",
                    source_refs=("SRC-001",),
                    atomic_statement=assertions[2].canonical_statement,
                    observable_oracle=assertions[2].oracle_clauses[0],
                    test_intent=(
                        "Action contract: Ввести дату выдачи раньше 14-летия "
                        "клиента и инициировать проверку сохранения.; Test data: "
                        "Ввести дату выдачи раньше 14-летия клиента и инициировать "
                        "проверку сохранения."
                    ),
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    atom_id="ATOM-021",
                ),
            ),
            coverage_gaps=(),
        )

        compiled = compile_source_first_property_derivations(
            repo_root=self.root,
            ft_slug="sample",
            source_manifest=_Manifest("4-3-current-passport-data", assertions),  # type: ignore[arg-type]
            obligation_set=obligations,
        )
        by_id = {item.assertion_id: item for item in compiled.document.derivations}

        self.assertEqual(
            "repeated-digits",
            by_id["ASSERT-PASS-CUR-005"].obligation_variants["OBL-PASS-CUR-005"],
        )
        self.assertEqual(
            ("111",),
            by_id["ASSERT-PASS-CUR-005"].fixture_values["OBL-PASS-CUR-005"],  # type: ignore[index]
        )
        self.assertEqual(
            ("123456",),
            by_id["ASSERT-PASS-CUR-013"].fixture_values["OBL-PASS-CUR-013"],  # type: ignore[index]
        )
        self.assertEqual(
            "date-window",
            by_id["ASSERT-PASS-CUR-021"].obligation_variants["OBL-PASS-CUR-021"],
        )
        self.assertEqual(
            ("дата 14-летия", "дата 14-летия - 1 день"),
            by_id["ASSERT-PASS-CUR-021"].fixture_values["OBL-PASS-CUR-021"],  # type: ignore[index]
        )

    def test_source_first_exact_length_uses_exact_source_boundaries(self) -> None:
        assertion = replace(
            self._assertion(),
            assertion_id="ASSERT-PASS-CUR-003",
            atom_id="ATOM-003",
            obligation_ids=("OBL-PASS-CUR-003",),
            exact_source_text=(
                "Серия Да Да Поле ввода Текст Строка BSR 85. "
                "Ограничение на формат: только 4 числовых символа."
            ),
            canonical_statement=(
                "Поле «Серия» не принимает более 4 числовых символов."
            ),
            polarity="negative",
            action_clauses=("Попытаться ввести значение `12345`.",),
            oracle_clauses=(
                "Пятый символ не вводится; в поле остается ограниченное "
                "значение длиной не более 4 символов.",
            ),
            requirement_codes=("BSR 85",),
        )
        obligations = PreparedObligationSet.create(
            package_id="WP-01",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-PASS-CUR-003",
                    source_refs=("SRC-001", "BSR 85"),
                    atomic_statement=assertion.canonical_statement,
                    observable_oracle=assertion.oracle_clauses[0],
                    test_intent=(
                        "Action contract: Попытаться ввести значение `12345`.; "
                        "Test data: Попытаться ввести значение `12345`."
                    ),
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    atom_id="ATOM-003",
                ),
            ),
            coverage_gaps=(),
        )

        compiled = compile_source_first_property_derivations(
            repo_root=self.root,
            ft_slug="sample",
            source_manifest=_Manifest("4-3-current-passport-data", (assertion,)),  # type: ignore[arg-type]
            obligation_set=obligations,
        )
        derivation = compiled.document.derivations[0]

        self.assertEqual(
            ("1234", "123", "12345"),
            derivation.fixture_values["OBL-PASS-CUR-003"],  # type: ignore[index]
        )

    def test_source_first_digits_only_does_not_inherit_exact_length_boundaries(self) -> None:
        assertion = replace(
            self._assertion(),
            assertion_id="ASSERT-PASS-CUR-004",
            atom_id="ATOM-004",
            obligation_ids=("OBL-PASS-CUR-004",),
            exact_source_text=(
                "Номер Да Да Поле ввода Текст Строка BSR 88. "
                "Ограничение на формат: только 6 числовых символов."
            ),
            canonical_statement=(
                "Field `Number` rejects a non-numeric symbol."
            ),
            polarity="negative",
            action_clauses=("Try to enter non-numeric symbol `A`.",),
            oracle_clauses=("Symbol `A` is not entered into the field.",),
            requirement_codes=("BSR 88",),
        )
        obligations = PreparedObligationSet.create(
            package_id="WP-01",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-PASS-CUR-004",
                    source_refs=("SRC-001", "BSR 88"),
                    atomic_statement=assertion.canonical_statement,
                    observable_oracle=assertion.oracle_clauses[0],
                    test_intent=(
                        "Action contract: Try to enter non-numeric symbol `A`.; "
                        "Test data: Try to enter non-numeric symbol `A`."
                    ),
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    atom_id="ATOM-004",
                ),
            ),
            coverage_gaps=(),
        )

        compiled = compile_source_first_property_derivations(
            repo_root=self.root,
            ft_slug="sample",
            source_manifest=_Manifest("4-3-current-passport-data", (assertion,)),  # type: ignore[arg-type]
            obligation_set=obligations,
        )
        derivation = compiled.document.derivations[0]

        self.assertEqual(
            "digits-only",
            derivation.obligation_variants["OBL-PASS-CUR-004"],
        )
        self.assertEqual(
            ("123A56", "123 56", "123@56", "123.56", "123-56"),
            derivation.fixture_values["OBL-PASS-CUR-004"],  # type: ignore[index]
        )

    def test_source_first_date_window_splits_positive_boundary_calibration(self) -> None:
        assertion = replace(
            self._assertion(),
            assertion_id="ASSERT-PASS-CUR-023",
            source_row_id="SRC-PASS-CUR-008",
            atom_id="ATOM-023",
            obligation_ids=("OBL-PASS-CUR-023",),
            exact_source_text=(
                "Дата выдачи Да Дата BSR 100. Паспорт, выданный после "
                "20-летия и до 45-летия, действителен до 45-летия + 90 "
                "календарных дней включительно."
            ),
            canonical_statement=(
                "Паспорт, выданный после 20-летия и до 45-летия, "
                "действителен до 45-летия + 90 календарных дней включительно."
            ),
            polarity="positive",
            condition_clauses=(
                "Дата выдачи паспорта после 20-летия и до 45-летия клиента; "
                "текущая дата позже 45-летия + 90 календарных дней.",
            ),
            action_clauses=("Инициировать проверку срока действия паспорта.",),
            oracle_clauses=(
                "Просроченный паспорт блокирует сохранение с подсказкой "
                "«Паспорт недействителен (просрочен)».",
            ),
            requirement_codes=("BSR 100",),
        )
        manifest = _Manifest("4-3-current-passport-data", (assertion,))
        obligations = PreparedObligationSet.create(
            package_id="WP-01",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-PASS-CUR-023",
                    source_refs=("SRC-PASS-CUR-008", "BSR 100"),
                    atomic_statement=assertion.canonical_statement,
                    observable_oracle=assertion.oracle_clauses[0],
                    test_intent=(
                        "Action contract: Инициировать проверку срока действия "
                        "паспорта.; Test data: Инициировать проверку срока "
                        "действия паспорта."
                    ),
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    atom_id="ATOM-023",
                ),
            ),
            coverage_gaps=(),
        )

        compiled = compile_source_first_property_derivations(
            repo_root=self.root,
            ft_slug="sample",
            source_manifest=manifest,  # type: ignore[arg-type]
            obligation_set=obligations,
        )
        derivation = compiled.document.derivations[0]

        self.assertEqual("source-date-boundary", derivation.property_kind)
        self.assertEqual(
            {"OBL-PASS-CUR-023": "date-window"},
            derivation.obligation_variants,
        )
        self.assertEqual(
            (
                "дата выдачи = дата 45-летия - 1 день; "
                "текущая дата = дата 45-летия + 90 дней",
                "дата выдачи = дата 45-летия - 1 день; "
                "текущая дата = дата 45-летия + 91 день",
            ),
            derivation.fixture_values["OBL-PASS-CUR-023"],  # type: ignore[index]
        )
        self.assertRegex(
            derivation.source_oracle_ids["OBL-PASS-CUR-023"],  # type: ignore[index]
            r"^SO-CAL-",
        )
        self.assertIn(
            "наблюдаемый UI-артефакт",
            derivation.calibration_questions["OBL-PASS-CUR-023"],  # type: ignore[index]
        )

        graph = build_coverage_graph(
            ft_slug="sample",
            tc_prefix="PASSCUR",
            source_manifest=manifest,  # type: ignore[arg-type]
            obligation_set=obligations,
            derivations=compiled.document.derivations,
        )
        by_variant = {
            case.case_key.split("|")[3]: case.status for case in graph.cases
        }
        self.assertEqual(
            "candidate-ui-calibration",
            by_variant["date-window-valid-boundary"],
        )
        self.assertEqual("executable", by_variant["date-window-invalid-boundary"])
        self.assertEqual(
            assertion.oracle_clauses[0],
            graph.obligations[0].observable_oracle,
        )

    def test_source_first_projects_entrypoint_and_dadata_fixture_literals(self) -> None:
        source_dir = self.root / "fts" / "sample" / "source"
        source_dir.mkdir(parents=True)
        (source_dir / "main.xhtml").write_text(
            "<html><body><h1>4.3. Карточка «Заявка»</h1></body></html>\n",
            encoding="utf-8",
        )
        fixture_dir = (
            self.root
            / "fts"
            / "sample"
            / "work"
            / "vendor-references"
            / "dadata-fixtures"
            / "FX-DADATA-FMS-POS-001"
        )
        fixture_dir.mkdir(parents=True)
        (fixture_dir / "FX-DADATA-FMS-POS-001.verification.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "fixture_id": "FX-DADATA-FMS-POS-001",
                    "status": "verified",
                    "request": {
                        "parameters": {
                            "query": "772-053",
                        },
                    },
                    "expected_response": {
                        "exact_suggestion": "ОВД ЗЮЗИНО Г. МОСКВЫ",
                        "exact_components": {
                            "code": "772-053",
                            "name": "ОВД ЗЮЗИНО Г. МОСКВЫ",
                            "region_code": "77",
                            "type": "2",
                        },
                    },
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        assertion = replace(
            self._assertion(),
            assertion_id="ASSERT-PASS-CUR-015",
            source_path="fts/sample/source/main.xhtml",
            source_row_id="SRC-PASS-CUR-005",
            atom_id="ATOM-015",
            obligation_ids=("OBL-PASS-CUR-015",),
            exact_source_text=(
                "Блок «Паспортные данные». Кем выдан BSR 94. "
                "Предзаполняется по вводу кода подразделения."
            ),
            canonical_statement=(
                "Поле «Кем выдан» предзаполняется по вводу кода подразделения."
            ),
            condition_clauses=(
                "Открыт блок «Паспортные данные»; "
                "Признак ручного ввода подразделения имеет значение «Нет»; "
                "fixture `FX-DADATA-FMS-POS-001` подтверждает FMS response "
                "for query `772-053`.",
            ),
            action_clauses=("Ввести код подразделения `772-053`.",),
            oracle_clauses=(
                "Поле «Кем выдан» получает значение из подсказок DaData; "
                "exact dropdown order/count is not asserted.",
            ),
            requirement_codes=("BSR 94",),
        )
        manifest = _Manifest("4-3-current-passport-data", (assertion,))
        obligations = PreparedObligationSet.create(
            package_id="WP-01",
            obligations=(
                PreparedObligation(
                    obligation_id="OBL-PASS-CUR-015",
                    source_refs=("SRC-PASS-CUR-005", "BSR 94"),
                    atomic_statement=assertion.canonical_statement,
                    observable_oracle=assertion.oracle_clauses[0],
                    test_intent=(
                        "Condition contract: fixture `FX-DADATA-FMS-POS-001` "
                        "подтверждает FMS response for query `772-053`.; "
                        "Action contract: Ввести код подразделения `772-053`.; "
                        "Test data: Ввести код подразделения `772-053`."
                    ),
                    coverage_status="testable",
                    gap_id="",
                    dictionary_refs=(),
                    notes="",
                    atom_id="ATOM-015",
                ),
            ),
            coverage_gaps=(),
        )

        compiled = compile_source_first_property_derivations(
            repo_root=self.root,
            ft_slug="sample",
            source_manifest=manifest,  # type: ignore[arg-type]
            obligation_set=obligations,
        )

        derivation = compiled.document.derivations[0]
        self.assertEqual(
            "Карточка «Заявка» / Блок «Паспортные данные»",
            compiled.scope_title,
        )
        self.assertEqual(
            (
                "FX-DADATA-FMS-POS-001",
                "772-053",
                "ОВД ЗЮЗИНО Г. МОСКВЫ",
                "77",
                "2",
            ),
            derivation.fixture_values["OBL-PASS-CUR-015"],  # type: ignore[index]
        )

        graph = build_coverage_graph(
            ft_slug="sample",
            tc_prefix="PASSCUR",
            source_manifest=manifest,  # type: ignore[arg-type]
            obligation_set=obligations,
            derivations=compiled.document.derivations,
        )
        context = DesignContext(
            package_id=obligations.package_id,
            scope_title=compiled.scope_title,
            base_preconditions=compiled.base_preconditions,
            subject_labels=compiled.subject_labels,
            condition_preconditions=compiled.condition_preconditions,
        )
        plan = build_test_design_plan(
            graph,
            context=context,
            expected_package_id=obligations.package_id,
        )
        case = plan.deterministic_cases[0]
        self.assertEqual(
            (
                "Открыть карточку `Заявка`.",
                "Перейти к блоку `Паспортные данные`.",
            ),
            case.preconditions,
        )
        self.assertIn("Fixture DaData: `FX-DADATA-FMS-POS-001`.", case.test_data)
        self.assertIn("Запрос: `772-053`.", case.test_data)
        self.assertIn("Точное предложение: `ОВД ЗЮЗИНО Г. МОСКВЫ`.", case.test_data)

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
