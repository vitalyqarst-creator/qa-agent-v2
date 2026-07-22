from __future__ import annotations

import copy
import hashlib
import json
import unittest
from dataclasses import dataclass, replace
from typing import Any

from test_case_agent.coverage_graph import (
    CoverageGraphError,
    PropertyDerivation,
    build_coverage_graph,
    validate_coverage_graph,
)
from test_case_agent.review_cycle.prepared_package import (
    PreparedObligation,
    PreparedObligationSet,
)


@dataclass(frozen=True)
class FakeAssertion:
    assertion_id: str
    source_row_id: str
    requirement_codes: tuple[str, ...]
    obligation_ids: tuple[str, ...]
    semantic_disposition: str = "testable"
    source_path: str = "fts/sample/source.xhtml"
    locator: str = "/*/*[2]/*[1]"
    exact_source_text: str = "Поле."
    canonical_statement: str = "Поле имеет проверяемое свойство."
    primary_gap_id: str | None = None

    @property
    def atom_id(self) -> str:
        return self.assertion_id.replace("ASSERT-", "ATOM-", 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "assertion_id": self.assertion_id,
            "source_row_id": self.source_row_id,
            "requirement_codes": list(self.requirement_codes),
            "obligation_ids": list(self.obligation_ids),
            "semantic_disposition": self.semantic_disposition,
            "source_path": self.source_path,
            "locator": self.locator,
            "exact_source_text": self.exact_source_text,
            "canonical_statement": self.canonical_statement,
            "primary_gap_id": self.primary_gap_id,
        }


@dataclass(frozen=True)
class FakeManifest:
    scope_slug: str
    assertions: tuple[FakeAssertion, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 4,
            "scope_slug": self.scope_slug,
            "assertions": [item.to_dict() for item in self.assertions],
        }


def obligation(
    obligation_id: str,
    atom_id: str,
    *source_refs: str,
    calibration: bool = False,
) -> PreparedObligation:
    return PreparedObligation(
        obligation_id=obligation_id,
        source_refs=tuple(source_refs),
        atomic_statement=f"Atomic statement for {obligation_id}",
        observable_oracle=f"Observable result for {obligation_id}",
        test_intent=f"Test intent for {obligation_id}",
        coverage_status="testable",
        gap_id="",
        dictionary_refs=(),
        notes="",
        atom_id=atom_id,
        calibration_status=("ui-calibration-required" if calibration else "none"),
    )


def obligation_set(*items: PreparedObligation) -> PreparedObligationSet:
    return PreparedObligationSet.create(
        package_id="WP-SAMPLE",
        obligations=items,
        coverage_gaps=(),
    )


def derivation(
    manifest: FakeManifest,
    prepared: PreparedObligationSet,
    assertion_id: str,
    property_key: str,
    property_kind: str,
    variants: dict[str, str],
    **overrides: Any,
) -> PropertyDerivation:
    assertion = next(
        item for item in manifest.assertions if item.assertion_id == assertion_id
    )
    manifest_digest = hashlib.sha256(
        json.dumps(
            manifest.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    values: dict[str, Any] = {
        "source_manifest_digest": manifest_digest,
        "obligation_set_digest": prepared.digest,
        "assertion_id": assertion_id,
        "source_row_id": assertion.source_row_id,
        "atom_id": assertion.atom_id,
        "source_text_sha256": hashlib.sha256(
            assertion.exact_source_text.encode("utf-8")
        ).hexdigest(),
        "property_key": property_key,
        "subject_key": "customer.phone",
        "property_kind": property_kind,
        "obligation_variants": variants,
    }
    values.update(overrides)
    return PropertyDerivation(**values)


class CoverageGraphTests(unittest.TestCase):
    def test_build_is_canonical_and_deterministic(self) -> None:
        manifest = FakeManifest(
            "sample-scope",
            (FakeAssertion("ASSERT-001", "SRC-001", ("BSR 100",), ("OBL-001",)),),
        )
        prepared = obligation_set(obligation("OBL-001", "ATOM-001", "BSR 100"))
        typed = [
            derivation(
                manifest,
                prepared,
                "ASSERT-001",
                "phone.visibility",
                "visibility",
                {"OBL-001": "visible"},
            )
        ]
        first = build_coverage_graph(
            ft_slug="Sample",
            tc_prefix="SMP",
            source_manifest=manifest,  # type: ignore[arg-type]
            obligation_set=prepared,
            derivations=typed,
        )
        second = build_coverage_graph(
            ft_slug="Sample",
            tc_prefix="SMP",
            source_manifest=copy.deepcopy(manifest),  # type: ignore[arg-type]
            obligation_set=copy.deepcopy(prepared),
            derivations=copy.deepcopy(typed),
        )
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.digest, second.digest)

    def test_same_row_sibling_properties_are_retained(self) -> None:
        manifest = FakeManifest(
            "sample-scope",
            (
                FakeAssertion("ASSERT-001", "SRC-001", (), ("OBL-001",)),
                FakeAssertion("ASSERT-002", "SRC-001", (), ("OBL-002",)),
            ),
        )
        prepared = obligation_set(
            obligation("OBL-001", "ATOM-001", "SRC-001"),
            obligation("OBL-002", "ATOM-002", "SRC-001"),
        )
        graph = build_coverage_graph(
            ft_slug="Sample",
            tc_prefix="SMP",
            source_manifest=manifest,  # type: ignore[arg-type]
            obligation_set=prepared,
            derivations=(
                derivation(
                    manifest,
                    prepared,
                    "ASSERT-001",
                    "phone.required",
                    "requiredness",
                    {"OBL-001": "empty"},
                ),
                derivation(
                    manifest,
                    prepared,
                    "ASSERT-002",
                    "phone.editable",
                    "editability",
                    {"OBL-002": "replace"},
                ),
            ),
        )
        self.assertEqual(2, len(graph.properties))
        self.assertEqual({"requiredness", "editability"}, {item.property_kind for item in graph.properties})
        self.assertEqual(2, len(graph.cases))

    def test_foreign_row_wide_requirement_code_is_rejected(self) -> None:
        manifest = FakeManifest(
            "sample-scope",
            (FakeAssertion("ASSERT-001", "SRC-001", ("BSR 100",), ("OBL-001",)),),
        )
        prepared = obligation_set(
            obligation("OBL-001", "ATOM-001", "BSR 100", "BSR 101")
        )
        with self.assertRaisesRegex(CoverageGraphError, "foreign requirement codes"):
            build_coverage_graph(
                ft_slug="Sample",
                tc_prefix="SMP",
                source_manifest=manifest,  # type: ignore[arg-type]
                obligation_set=prepared,
                derivations=(
                    derivation(
                        manifest,
                        prepared,
                        "ASSERT-001",
                        "phone.length",
                        "exact-length",
                        {"OBL-001": "n"},
                    ),
                ),
            )

    def test_every_property_has_one_explicit_disposition(self) -> None:
        manifest = FakeManifest(
            "sample-scope",
            (
                FakeAssertion("ASSERT-001", "SRC-001", (), ("OBL-001",)),
                FakeAssertion(
                    "ASSERT-002",
                    "SRC-002",
                    (),
                    (),
                    semantic_disposition="ambiguous",
                    primary_gap_id="GAP-001",
                ),
                FakeAssertion(
                    "ASSERT-003",
                    "SRC-003",
                    (),
                    (),
                    semantic_disposition="not-applicable",
                ),
            ),
        )
        prepared = obligation_set(obligation("OBL-001", "ATOM-001", "SRC-001"))
        graph = build_coverage_graph(
            ft_slug="Sample",
            tc_prefix="SMP",
            source_manifest=manifest,  # type: ignore[arg-type]
            obligation_set=prepared,
            derivations=(
                derivation(
                    manifest,
                    prepared,
                    "ASSERT-001",
                    "phone.visible",
                    "visibility",
                    {"OBL-001": "visible"},
                ),
            ),
        )
        self.assertEqual({"tc", "gap", "not-applicable"}, {item.disposition for item in graph.properties})
        self.assertEqual(("GAP-001",), tuple(item.gap_id for item in graph.gaps))

    def test_missing_and_orphan_obligations_fail_closed(self) -> None:
        manifest = FakeManifest(
            "sample-scope",
            (FakeAssertion("ASSERT-001", "SRC-001", (), ("OBL-001",)),),
        )
        prepared = obligation_set(obligation("OBL-002", "ATOM-002", "SRC-002"))
        with self.assertRaisesRegex(CoverageGraphError, "missing OBL-001"):
            build_coverage_graph(
                ft_slug="Sample",
                tc_prefix="SMP",
                source_manifest=manifest,  # type: ignore[arg-type]
                obligation_set=prepared,
                derivations=(
                    derivation(
                        manifest,
                        prepared,
                        "ASSERT-001",
                        "phone.visible",
                        "visibility",
                        {"OBL-001": "visible"},
                    ),
                ),
            )

    def test_explicit_non_testable_context_obligation_is_not_a_fake_case(self) -> None:
        manifest = FakeManifest(
            "sample-scope",
            (
                FakeAssertion("ASSERT-001", "SRC-001", (), ("OBL-001",)),
                FakeAssertion(
                    "ASSERT-CONTEXT-001",
                    "SRC-CONTEXT-001",
                    (),
                    (),
                    semantic_disposition="not-applicable",
                ),
            ),
        )
        context = PreparedObligation(
            obligation_id="OBL-CONTEXT-001",
            source_refs=("SRC-CONTEXT-001",),
            atomic_statement="Контекстная строка не задаёт отдельного поведения.",
            observable_oracle="",
            test_intent="Сохранить только как контекст.",
            coverage_status="not-applicable",
            gap_id="",
            dictionary_refs=(),
            notes="",
            atom_id="ATOM-CONTEXT-001",
        )
        prepared = obligation_set(
            obligation("OBL-001", "ATOM-001", "SRC-001"),
            context,
        )
        graph = build_coverage_graph(
            ft_slug="Sample",
            tc_prefix="SMP",
            source_manifest=manifest,  # type: ignore[arg-type]
            obligation_set=prepared,
            derivations=(
                derivation(
                    manifest,
                    prepared,
                    "ASSERT-001",
                    "phone.visible",
                    "visibility",
                    {"OBL-001": "visible"},
                ),
            ),
        )

        self.assertEqual(1, len(graph.cases))
        self.assertEqual(1, len(graph.obligations))

    def test_candidate_requires_so_trigger_fixture_and_question(self) -> None:
        manifest = FakeManifest(
            "sample-scope",
            (FakeAssertion("ASSERT-001", "SRC-001", (), ("OBL-001",)),),
        )
        prepared = obligation_set(
            obligation("OBL-001", "ATOM-001", "SRC-001", calibration=True)
        )
        typed = derivation(
            manifest,
            prepared,
            "ASSERT-001",
            "phone.invalid-letters",
            "numeric-format",
            {"OBL-001": "letters"},
        )
        with self.assertRaisesRegex(CoverageGraphError, "CG-CALIBRATION-CONTRACT-INCOMPLETE"):
            build_coverage_graph(
                ft_slug="Sample",
                tc_prefix="SMP",
                source_manifest=manifest,  # type: ignore[arg-type]
                obligation_set=prepared,
                derivations=(typed,),
            )

    def test_state_change_requires_cleanup(self) -> None:
        manifest = FakeManifest(
            "sample-scope",
            (FakeAssertion("ASSERT-001", "SRC-001", (), ("OBL-001",)),),
        )
        prepared = obligation_set(obligation("OBL-001", "ATOM-001", "SRC-001"))
        with self.assertRaisesRegex(CoverageGraphError, "CG-STATE-CHANGE-WITHOUT-CLEANUP"):
            build_coverage_graph(
                ft_slug="Sample",
                tc_prefix="SMP",
                source_manifest=manifest,  # type: ignore[arg-type]
                obligation_set=prepared,
                derivations=(
                    derivation(
                        manifest,
                        prepared,
                        "ASSERT-001",
                        "repeater.delete",
                        "repeater-delete",
                        {"OBL-001": "second-row"},
                    ),
                ),
            )

    def test_complete_candidate_contract_passes(self) -> None:
        manifest = FakeManifest(
            "sample-scope",
            (FakeAssertion("ASSERT-001", "SRC-001", (), ("OBL-001",)),),
        )
        prepared = obligation_set(
            obligation("OBL-001", "ATOM-001", "SRC-001", calibration=True)
        )
        graph = build_coverage_graph(
            ft_slug="Sample",
            tc_prefix="SMP",
            source_manifest=manifest,  # type: ignore[arg-type]
            obligation_set=prepared,
            derivations=(
                derivation(
                    manifest,
                    prepared,
                    "ASSERT-001",
                    "phone.invalid-letters",
                    "numeric-format",
                    {"OBL-001": "letters"},
                    validation_trigger="leave-field",
                    source_oracle_ids={"OBL-001": "SO-NEG-001"},
                    fixture_values={"OBL-001": ("A",)},
                    calibration_questions={"OBL-001": "Как интерфейс отклоняет букву?"},
                ),
            ),
        )
        self.assertEqual((), validate_coverage_graph(graph))

    def test_derivation_is_hash_bound_to_manifest_obligations_and_source_text(self) -> None:
        manifest = FakeManifest(
            "sample-scope",
            (FakeAssertion("ASSERT-001", "SRC-001", (), ("OBL-001",)),),
        )
        prepared = obligation_set(obligation("OBL-001", "ATOM-001", "SRC-001"))
        typed = derivation(
            manifest,
            prepared,
            "ASSERT-001",
            "phone.visible",
            "visibility",
            {"OBL-001": "visible"},
        )
        mutations = (
            (
                "stale for this source manifest",
                replace(typed, source_manifest_digest="0" * 64),
            ),
            (
                "stale for this obligation set",
                replace(typed, obligation_set_digest="1" * 64),
            ),
            (
                "exact source hash mismatch",
                replace(typed, source_text_sha256="2" * 64),
            ),
        )
        for message, mutation in mutations:
            with self.subTest(message=message), self.assertRaisesRegex(
                CoverageGraphError, message
            ):
                build_coverage_graph(
                    ft_slug="Sample",
                    tc_prefix="SMP",
                    source_manifest=manifest,  # type: ignore[arg-type]
                    obligation_set=prepared,
                    derivations=(mutation,),
                )

    def test_authoritative_validator_covers_io_integrity_rules(self) -> None:
        manifest = FakeManifest(
            "sample-scope",
            (FakeAssertion("ASSERT-001", "SRC-001", (), ("OBL-001",)),),
        )
        prepared = obligation_set(obligation("OBL-001", "ATOM-001", "SRC-001"))
        graph = build_coverage_graph(
            ft_slug="Sample",
            tc_prefix="SMP",
            source_manifest=manifest,  # type: ignore[arg-type]
            obligation_set=prepared,
            derivations=(
                derivation(
                    manifest,
                    prepared,
                    "ASSERT-001",
                    "phone.visible",
                    "visibility",
                    {"OBL-001": "visible"},
                ),
            ),
        )
        invalid = replace(
            graph,
            obligations=(
                replace(
                    graph.obligations[0],
                    coverage_status="mystery",
                    gap_id="GAP-404",
                ),
            ),
        )

        finding_ids = {item.finding_id for item in validate_coverage_graph(invalid)}

        self.assertIn("CG-INVALID-COVERAGE-STATUS", finding_ids)


if __name__ == "__main__":
    unittest.main()
