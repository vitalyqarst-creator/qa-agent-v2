from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from test_case_agent.coverage_graph import (
    CoverageCase,
    CoverageGraph,
    CoverageObligation,
    CoverageProperty,
    PropertyDerivation,
)
from test_case_agent.coverage_io import (
    DesignContextDocument,
    PropertyDerivationDocument,
    CoverageIoError,
    load_coverage_graph,
    load_design_context,
    load_property_derivations,
    payload_sha256,
    write_coverage_graph,
    write_design_context,
    write_property_derivations,
)
from test_case_agent.test_design import DesignContext


def _derivation_document() -> PropertyDerivationDocument:
    return PropertyDerivationDocument(
        schema_version=1,
        ft_slug="sample-ft",
        scope_slug="sample-scope",
        source_manifest_digest="a" * 64,
        obligation_set_digest="b" * 64,
        derivations=(
            PropertyDerivation(
                source_manifest_digest="a" * 64,
                obligation_set_digest="b" * 64,
                assertion_id="ASSERT-001",
                source_row_id="SRC-001",
                atom_id="ATOM-001",
                source_text_sha256="c" * 64,
                property_key="customer.phone.visibility",
                subject_key="customer.phone",
                property_kind="visibility",
                obligation_variants={"OBL-001": "visible"},
                condition_key="always",
                validation_trigger="",
                cleanup_strategy="",
                source_oracle_ids=None,
                fixture_values={"OBL-001": ("+79991234567",)},
                calibration_questions=None,
            ),
        ),
    )


def _graph() -> CoverageGraph:
    return CoverageGraph(
        schema_version=1,
        ft_slug="sample-ft",
        scope_slug="sample-scope",
        source_manifest_digest="a" * 64,
        obligation_set_digest="b" * 64,
        properties=(
            CoverageProperty(
                property_id="PROP-001",
                assertion_id="ASSERT-001",
                property_key="customer.phone.visibility",
                subject_key="customer.phone",
                property_kind="visibility",
                source_row_id="SRC-001",
                source_path="fts/sample/source/requirements.xhtml",
                source_locator="//*[@id='phone']",
                source_text_sha256="c" * 64,
                canonical_statement="Поле «Телефон» отображается.",
                requirement_codes=("BSR 1",),
                disposition="tc",
            ),
            CoverageProperty(
                property_id="PROP-CONTEXT",
                assertion_id="ASSERT-CONTEXT",
                property_key="customer-card.open",
                subject_key="customer-card",
                property_kind="context",
                source_row_id="SRC-CONTEXT",
                source_path="fts/sample/source/requirements.xhtml",
                source_locator="//*[@id='customer-card']",
                source_text_sha256="d" * 64,
                canonical_statement="Открыть карточку клиента.",
                requirement_codes=(),
                disposition="not-applicable",
            ),
            CoverageProperty(
                property_id="PROP-SCOPE-TITLE",
                assertion_id="ASSERT-SCOPE-TITLE",
                property_key="customer-card.title",
                subject_key="customer-card",
                property_kind="context",
                source_row_id="SRC-SCOPE-TITLE",
                source_path="fts/sample/source/requirements.xhtml",
                source_locator="//*[@id='customer-card-title']",
                source_text_sha256="e" * 64,
                canonical_statement="Контактные данные",
                requirement_codes=(),
                disposition="not-applicable",
            ),
        ),
        obligations=(
            CoverageObligation(
                obligation_id="OBL-001",
                property_id="PROP-001",
                atom_id="ATOM-001",
                coverage_variant="visible",
                condition_key="always",
                atomic_statement="Проверить отображение поля «Телефон».",
                observable_oracle="Поле «Телефон» отображается.",
                coverage_status="testable",
                requirement_codes=("BSR 1",),
                gap_id="",
                calibration_status="none",
                validation_trigger="",
                cleanup_strategy="",
                source_oracle_id="",
                fixture_values=("+79991234567",),
                calibration_question="",
            ),
        ),
        cases=(
            CoverageCase(
                case_key="sample-scope|customer.phone|visibility|visible|always",
                tc_id="TC-SMP-001",
                obligation_ids=("OBL-001",),
                status="executable",
            ),
        ),
        gaps=(),
    )


def _design_document(graph: CoverageGraph) -> DesignContextDocument:
    return DesignContextDocument(
        schema_version=1,
        ft_slug=graph.ft_slug,
        scope_slug=graph.scope_slug,
        coverage_graph_digest=graph.digest,
        context=DesignContext(
            package_id="WP-01",
            scope_title="Контактные данные",
            base_preconditions=("Открыть карточку клиента.",),
            subject_labels={"customer.phone": "поле «Телефон»"},
            condition_preconditions={},
            priorities={graph.cases[0].case_key: "высокий"},
        ),
    )


def _rewrite_envelope(path: Path, mutate) -> None:  # type: ignore[no-untyped-def]
    root = json.loads(path.read_text(encoding="utf-8"))
    mutate(root)
    root["payload_sha256"] = payload_sha256(root["payload"])
    path.write_text(
        json.dumps(root, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )


class CoverageIoTests(unittest.TestCase):
    def test_derivation_round_trip_is_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "derivations.json"
            second = Path(directory) / "derivations-copy.json"
            source = _derivation_document()

            digest = write_property_derivations(first, source)
            loaded = load_property_derivations(
                first,
                expected_source_manifest_digest="a" * 64,
                expected_obligation_set_digest="b" * 64,
            )
            second_digest = write_property_derivations(second, loaded)

            self.assertEqual(source, loaded)
            self.assertEqual(source.digest, digest)
            self.assertEqual(digest, second_digest)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_duplicate_nested_json_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "derivations.json"
            write_property_derivations(path, _derivation_document())
            source = path.read_text(encoding="utf-8")
            source = source.replace(
                '"property_kind":"visibility"',
                '"property_kind":"visibility","property_kind":"requiredness"',
                1,
            )
            path.write_text(source, encoding="utf-8")

            with self.assertRaisesRegex(CoverageIoError, "duplicate-json-key"):
                load_property_derivations(path)

    def test_tampered_payload_is_rejected_before_use(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "derivations.json"
            write_property_derivations(path, _derivation_document())
            source = path.read_text(encoding="utf-8").replace(
                '"property_kind":"visibility"',
                '"property_kind":"editability"',
                1,
            )
            path.write_text(source, encoding="utf-8")

            with self.assertRaisesRegex(CoverageIoError, "payload-digest-mismatch"):
                load_property_derivations(path)

    def test_missing_semantic_field_is_not_inferred_from_prose(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "derivations.json"
            write_property_derivations(path, _derivation_document())

            def remove_kind(root):  # type: ignore[no-untyped-def]
                del root["payload"]["derivations"][0]["property_kind"]

            _rewrite_envelope(path, remove_kind)
            with self.assertRaisesRegex(CoverageIoError, "schema-fields"):
                load_property_derivations(path)

    def test_derivation_evidence_binding_fields_are_all_mandatory(self) -> None:
        mandatory = (
            "source_manifest_digest",
            "obligation_set_digest",
            "source_row_id",
            "atom_id",
            "source_text_sha256",
        )
        with tempfile.TemporaryDirectory() as directory:
            for field in mandatory:
                with self.subTest(field=field):
                    path = Path(directory) / f"missing-{field}.json"
                    write_property_derivations(path, _derivation_document())

                    def remove_field(root, field=field):  # type: ignore[no-untyped-def]
                        del root["payload"]["derivations"][0][field]

                    _rewrite_envelope(path, remove_field)
                    with self.assertRaisesRegex(CoverageIoError, "schema-fields"):
                        load_property_derivations(path)

    def test_derivation_must_repeat_document_digests_exactly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "derivations.json"
            write_property_derivations(path, _derivation_document())

            def rebind_one_derivation(root):  # type: ignore[no-untyped-def]
                root["payload"]["derivations"][0]["source_manifest_digest"] = "f" * 64

            _rewrite_envelope(path, rebind_one_derivation)
            with self.assertRaisesRegex(CoverageIoError, "artifact-binding"):
                load_property_derivations(path)

    def test_unknown_nested_field_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "derivations.json"
            write_property_derivations(path, _derivation_document())

            def add_prose_hint(root):  # type: ignore[no-untyped-def]
                root["payload"]["derivations"][0]["prose_hint"] = "Поле обязательно"

            _rewrite_envelope(path, add_prose_hint)
            with self.assertRaisesRegex(CoverageIoError, "schema-fields"):
                load_property_derivations(path)

    def test_non_finite_json_number_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.json"
            path.write_text(
                '{"schema_version":NaN,"artifact_kind":"coverage-graph",'
                '"payload_sha256":"' + "0" * 64 + '","payload":{}}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(CoverageIoError, "non-finite-json-number"):
                load_coverage_graph(path)

    def test_graph_round_trip_is_byte_deterministic_and_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "coverage-graph.json"
            second = Path(directory) / "coverage-graph-copy.json"
            graph = _graph()

            digest = write_coverage_graph(first, graph)
            loaded = load_coverage_graph(
                first,
                expected_source_manifest_digest="a" * 64,
                expected_obligation_set_digest="b" * 64,
            )
            second_digest = write_coverage_graph(second, loaded)

            self.assertEqual(graph, loaded)
            self.assertEqual(graph.digest, digest)
            self.assertEqual(digest, second_digest)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_graph_load_runs_referential_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "coverage-graph.json"
            write_coverage_graph(path, _graph())

            def make_dangling(root):  # type: ignore[no-untyped-def]
                root["payload"]["cases"][0]["obligation_ids"] = ["OBL-404"]

            _rewrite_envelope(path, make_dangling)
            with self.assertRaisesRegex(
                CoverageIoError, "CG-CASE-UNKNOWN-OBLIGATION"
            ):
                load_coverage_graph(path)

    def test_duplicate_graph_identity_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "coverage-graph.json"
            write_coverage_graph(path, _graph())

            def duplicate_property(root):  # type: ignore[no-untyped-def]
                root["payload"]["properties"].append(
                    dict(root["payload"]["properties"][0])
                )

            _rewrite_envelope(path, duplicate_property)
            with self.assertRaisesRegex(CoverageIoError, "CG-DUPLICATE-PROPERTY"):
                load_coverage_graph(path)

    def test_design_context_round_trip_checks_graph_binding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "design-context.json"
            second = Path(directory) / "design-context-copy.json"
            graph = _graph()
            document = _design_document(graph)

            digest = write_design_context(first, document, graph=graph)
            loaded = load_design_context(first, graph=graph)
            second_digest = write_design_context(second, loaded, graph=graph)

            self.assertEqual(document, loaded)
            self.assertEqual(document.digest, digest)
            self.assertEqual(digest, second_digest)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_design_context_missing_subject_fails_closed(self) -> None:
        graph = _graph()
        document = _design_document(graph)
        document = replace(
            document,
            context=replace(document.context, subject_labels={}),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "design-context.json"
            with self.assertRaisesRegex(CoverageIoError, "subject_labels"):
                write_design_context(path, document, graph=graph)

    def test_design_context_for_another_graph_is_rejected(self) -> None:
        graph = _graph()
        document = _design_document(graph)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "design-context.json"
            write_design_context(path, document)
            changed = replace(graph, obligation_set_digest="d" * 64)

            with self.assertRaisesRegex(CoverageIoError, "digest does not match"):
                load_design_context(path, graph=changed)

    def test_expected_digest_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "derivations.json"
            write_property_derivations(path, _derivation_document())
            with self.assertRaisesRegex(CoverageIoError, "artifact-binding"):
                load_property_derivations(
                    path, expected_source_manifest_digest="f" * 64
                )


if __name__ == "__main__":
    unittest.main()
