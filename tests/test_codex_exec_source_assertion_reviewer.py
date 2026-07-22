from __future__ import annotations

import json
import hashlib
import os
import sys
import tempfile
import unittest
import zipfile
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from scripts.codex_exec_source_assertion_reviewer import (
    DEFAULT_MAX_ASSERTIONS_PER_SHARD,
    DEFAULT_MAX_PROMPT_BYTES,
    DEFAULT_SHARD_TARGET_PROMPT_BYTES,
    OutputReservations,
    PreparedEvidenceSet,
    SourceReviewerRunnerError,
    _normalize_pdf_literal_text,
    assert_output_isolation,
    event_item_type,
    event_usage,
    main,
    merge_review_shard_payloads,
    plan_review_prompt_shards,
    prepare_evidence_set,
    receipt_schema,
    render_prompt,
    reserve_fresh_outputs,
    run_exec,
    verify_source_gate,
    write_json,
)
from scripts.build_bounded_source_evidence_extract import (
    write_validated_descriptor,
)
from scripts.review_cycle_backend_dispatcher import ExecCapability
from test_case_agent.review_cycle.exec_backend import (
    MODEL_TOOL_ISOLATION_DISABLE_FEATURES,
)
from scripts.openai_strict_output_schema import (
    OPENAI_STRICT_OUTPUT_SCHEMA_LARGE_ENUM_THRESHOLD,
    OPENAI_STRICT_OUTPUT_SCHEMA_MAX_DEPTH,
    OPENAI_STRICT_OUTPUT_SCHEMA_MAX_ENUM_VALUES,
    OPENAI_STRICT_OUTPUT_SCHEMA_MAX_LARGE_ENUM_CHARACTERS,
    OPENAI_STRICT_OUTPUT_SCHEMA_MAX_PROPERTIES,
    OPENAI_STRICT_OUTPUT_SCHEMA_MAX_STRING_CHARACTERS,
    OpenAIStrictOutputInstanceError,
    OpenAIStrictOutputSchemaError,
    openai_strict_output_schema_shape_sha256,
    validate_openai_strict_output_instance,
    validate_openai_strict_output_schema,
)
from test_case_agent.review_cycle.source_assertions import (
    MANIFEST_VERSION,
    SCOPE_BOUNDARY_CONTEXT_CLASSES,
    SOURCE_REVIEW_DIMENSIONS,
    RegisteredArtifact,
    RegisteredEvidenceSource,
    RegisteredMockup,
    RegisteredSource,
    SourceAssertion,
    SourceAssertionManifest,
    SourceRow,
)
from test_case_agent.review_cycle.source_gate import (
    build_passed_source_gate_receipt,
)


class CodexExecSourceAssertionReviewerTests(unittest.TestCase):
    def test_pdf_literal_normalizer_ignores_only_layout_punctuation_spaces(self) -> None:
        extracted = (
            "BSR 324. Если адрес клиента (регистрации / места жительства ) "
            "заполнен посредством запроса DaData, то он раскладывается по полям."
        )
        descriptor = (
            "BSR 324. Если адрес клиента (регистрации / места жительства) "
            "заполнен посредством запроса DaData"
        )

        self.assertIn(
            _normalize_pdf_literal_text(descriptor),
            _normalize_pdf_literal_text(extracted),
        )
        self.assertNotIn(
            _normalize_pdf_literal_text("BSR 324. Адрес удаляется"),
            _normalize_pdf_literal_text(extracted),
        )

    def test_pdf_literal_normalizer_handles_extracted_hyphen_and_period_spaces(self) -> None:
        self.assertEqual(
            _normalize_pdf_literal_text("BSR 115. Видимость-всегда."),
            _normalize_pdf_literal_text("BSR 115. Видимость -всегда ."),
        )

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def manifest(self) -> SourceAssertionManifest:
        source_path = "source/main.xhtml"
        source_sha = "a" * 64
        rows = []
        assertions = []
        classes = (
            "document-global-constraints",
            "ancestor-and-section-preamble",
            "cross-referenced-constraints",
        )
        for index, context_class in enumerate(classes, start=1):
            row_id = f"SRC-{index:03d}"
            text = f"Bound source text {index}"
            rows.append(
                SourceRow(
                    source_row_id=row_id,
                    source_path=source_path,
                    source_locator=f"/*/*[{index}]",
                    bounded_source_text=text,
                    source_context_class=context_class,
                    candidate_id=f"SRC-CAND-{'1' * 22}{index:02d}",
                )
            )
            assertions.append(
                SourceAssertion(
                    assertion_id=f"ASSERT-{index:03d}",
                    source_path=source_path,
                    source_context_class=context_class,
                    locator=f"/*/*[{index}]",
                    exact_source_text=text,
                    canonical_statement=f"Context statement {index} is not executable.",
                    polarity="neutral",
                    semantic_disposition="not-applicable",
                    execution_readiness="not-applicable",
                    execution_readiness_rationale="none_required",
                    risk="low",
                    condition_clauses=(),
                    action_clauses=(),
                    oracle_clauses=(),
                    requirement_codes=(),
                    requirement_code_bindings=(),
                    clause_evidence_bindings=(),
                    source_row_id=row_id,
                    atom_id=f"ATOM-{index:03d}",
                    obligation_ids=(),
                    execution_dependency_gap_ids=(),
                    primary_gap_id=None,
                    disposition_rationale="Structural context does not define product behavior.",
                )
            )
        return SourceAssertionManifest(
            version=MANIFEST_VERSION,
            scope_slug="demo-scope",
            source_row_extraction_spec_digest="1" * 64,
            source_row_baseline_digest="2" * 64,
            source_row_candidate_count=3,
            coverage_gaps_artifact=RegisteredArtifact(
                path="coverage-gaps.md", sha256="3" * 64
            ),
            sources=(RegisteredSource(path=source_path, sha256=source_sha),),
            source_rows=tuple(rows),
            assertions=tuple(assertions),
        )

    def accepted_review_payload(
        self,
        manifest: SourceAssertionManifest,
        assertion_ids: tuple[str, ...],
    ) -> dict[str, object]:
        assertions_by_id = {
            item.assertion_id: item for item in manifest.assertions
        }
        return {
            "version": 6,
            "manifest_digest": manifest.digest,
            "decision": "accepted",
            "assertion_reviews": [
                {
                    "assertion_id": assertion_id,
                    "approved_polarity": assertions_by_id[assertion_id].polarity,
                    "approved_semantic_disposition": assertions_by_id[
                        assertion_id
                    ].semantic_disposition,
                    "approved_execution_readiness": assertions_by_id[
                        assertion_id
                    ].execution_readiness,
                    "approved_risk": assertions_by_id[assertion_id].risk,
                    "dimension_verdicts": {
                        dimension: "verified"
                        for dimension in SOURCE_REVIEW_DIMENSIONS
                    },
                    "verdict": "verified",
                    "required_change": "none_required",
                    "note": "Verified against the bound source evidence.",
                }
                for assertion_id in assertion_ids
            ],
            "source_inventory_review": {
                "extraction_spec_digest": manifest.source_row_extraction_spec_digest,
                "baseline_digest": manifest.source_row_baseline_digest,
                "candidate_count": manifest.source_row_candidate_count,
                "mapped_source_row_count": manifest.source_row_candidate_count,
                "verdict": "verified",
                "required_change": "none_required",
                "note": "Verified against the complete candidate baseline.",
            },
            "scope_boundary_review": {
                "verdict": "verified",
                "checked_context_classes": sorted(SCOPE_BOUNDARY_CONTEXT_CLASSES),
                "reviewed_manifest_contexts": [
                    {
                        "context_class": row.source_context_class,
                        "source_row_id": row.source_row_id,
                    }
                    for row in manifest.source_rows
                ],
                "excluded_contexts": [],
                "required_change": "none_required",
                "note": "Verified against all registered boundary contexts.",
            },
        }

    def test_receipt_schema_is_strict_and_digest_bound(self) -> None:
        manifest = self.manifest()
        schema = receipt_schema(manifest)

        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            [manifest.digest],
            schema["properties"]["manifest_digest"]["enum"],
        )
        reviews = schema["properties"]["assertion_reviews"]
        self.assertEqual(3, reviews["minItems"])
        self.assertEqual(3, reviews["maxItems"])
        self.assertFalse(reviews["items"]["additionalProperties"])
        dimensions = reviews["items"]["properties"]["dimension_verdicts"]
        self.assertEqual(13, len(dimensions["required"]))
        boundary = schema["properties"]["scope_boundary_review"]
        self.assertEqual(3, boundary["properties"]["reviewed_manifest_contexts"]["minItems"])
        validate_openai_strict_output_schema(schema)
        serialized = json.dumps(schema, sort_keys=True)
        for unsupported in ("$schema", "const", "minLength", "uniqueItems"):
            self.assertNotIn(f'"{unsupported}"', serialized)

    def test_strict_output_schema_lint_rejects_unsupported_keywords(self) -> None:
        valid = {
            "type": "object",
            "properties": {
                "values": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 1,
                }
            },
            "required": ["values"],
            "additionalProperties": False,
        }
        validate_openai_strict_output_schema(valid)

        mutations = {
            "uniqueItems": lambda schema: schema["properties"]["values"].update(
                {"uniqueItems": True}
            ),
            "minLength": lambda schema: schema["properties"]["values"][
                "items"
            ].update({"minLength": 1}),
            "const": lambda schema: schema["properties"]["values"]["items"].update(
                {"const": "value"}
            ),
            "$schema": lambda schema: schema.update(
                {"$schema": "https://json-schema.org/draft/2020-12/schema"}
            ),
            "not": lambda schema: schema.update({"not": {"type": "object"}}),
        }
        for keyword, mutate in mutations.items():
            with self.subTest(keyword=keyword):
                candidate = deepcopy(valid)
                mutate(candidate)
                with self.assertRaisesRegex(
                    OpenAIStrictOutputSchemaError,
                    keyword.replace("$", r"\$"),
                ):
                    validate_openai_strict_output_schema(candidate)

    def test_strict_output_schema_lint_enforces_documented_caps(self) -> None:
        def object_schema(properties):
            return {
                "type": "object",
                "properties": properties,
                "required": list(properties),
                "additionalProperties": False,
            }

        def nested_schema(depth: int):
            result = {"type": "string"}
            for index in reversed(range(depth - 1)):
                result = object_schema({f"level_{index}": result})
            return result

        validate_openai_strict_output_schema(
            nested_schema(OPENAI_STRICT_OUTPUT_SCHEMA_MAX_DEPTH)
        )
        with self.assertRaisesRegex(OpenAIStrictOutputSchemaError, "nesting depth"):
            validate_openai_strict_output_schema(
                nested_schema(OPENAI_STRICT_OUTPUT_SCHEMA_MAX_DEPTH + 1)
            )

        maximum_properties = {
            f"property_{index}": {"type": "string"}
            for index in range(OPENAI_STRICT_OUTPUT_SCHEMA_MAX_PROPERTIES)
        }
        validate_openai_strict_output_schema(object_schema(maximum_properties))
        over_properties = dict(maximum_properties)
        over_properties["one_property_too_many"] = {"type": "string"}
        with self.assertRaisesRegex(OpenAIStrictOutputSchemaError, "properties exceed"):
            validate_openai_strict_output_schema(object_schema(over_properties))

        maximum_enum = [
            f"value_{index}"
            for index in range(OPENAI_STRICT_OUTPUT_SCHEMA_MAX_ENUM_VALUES)
        ]
        validate_openai_strict_output_schema(
            object_schema(
                {"value": {"type": "string", "enum": maximum_enum}}
            )
        )
        with self.assertRaisesRegex(OpenAIStrictOutputSchemaError, "enum values exceed"):
            validate_openai_strict_output_schema(
                object_schema(
                    {
                        "value": {
                            "type": "string",
                            "enum": [*maximum_enum, "one_value_too_many"],
                        }
                    }
                )
        )

        threshold = OPENAI_STRICT_OUTPUT_SCHEMA_LARGE_ENUM_THRESHOLD
        large_enum_count = threshold + 1
        longer_value_count = (
            OPENAI_STRICT_OUTPUT_SCHEMA_MAX_LARGE_ENUM_CHARACTERS
            - large_enum_count * 59
        )
        large_enum = [
            f"{index:03d}"
            + "x"
            * (
                57
                if index < longer_value_count
                else 56
            )
            for index in range(large_enum_count)
        ]
        self.assertEqual(
            OPENAI_STRICT_OUTPUT_SCHEMA_MAX_LARGE_ENUM_CHARACTERS,
            sum(len(value) for value in large_enum),
        )
        validate_openai_strict_output_schema(
            object_schema(
                {"value": {"type": "string", "enum": large_enum}}
            )
        )
        over_large_enum = list(large_enum)
        over_large_enum[0] += "x"
        with self.assertRaisesRegex(
            OpenAIStrictOutputSchemaError,
            "string enum.*characters",
        ):
            validate_openai_strict_output_schema(
                object_schema(
                    {"value": {"type": "string", "enum": over_large_enum}}
                )
            )

        maximum_name = "p" * OPENAI_STRICT_OUTPUT_SCHEMA_MAX_STRING_CHARACTERS
        validate_openai_strict_output_schema(
            object_schema({maximum_name: {"type": "string"}})
        )
        with self.assertRaisesRegex(
            OpenAIStrictOutputSchemaError,
            "characters exceed",
        ):
            validate_openai_strict_output_schema(
                object_schema({maximum_name + "x": {"type": "string"}})
            )

    def test_strict_output_instance_validator_enforces_transport_shape(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "digest": {
                    "type": "string",
                    "pattern": "^[0-9a-f]{64}$",
                },
                "decisions": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["accepted", "rejected"],
                    },
                    "minItems": 2,
                    "maxItems": 2,
                },
            },
            "required": ["digest", "decisions"],
            "additionalProperties": False,
        }
        valid = {
            "digest": "a" * 64,
            "decisions": ["accepted", "rejected"],
        }
        validate_openai_strict_output_instance(valid, schema)

        invalid_instances = (
            {},
            {**valid, "extra": True},
            {**valid, "digest": "not-a-sha256"},
            {**valid, "decisions": ["accepted"]},
            {**valid, "decisions": ["accepted", "unknown"]},
            {**valid, "decisions": "accepted"},
        )
        for candidate in invalid_instances:
            with self.subTest(candidate=candidate):
                with self.assertRaises(OpenAIStrictOutputInstanceError):
                    validate_openai_strict_output_instance(candidate, schema)

    def test_strict_output_schema_shape_sha_is_semantic_value_independent(self) -> None:
        first = {
            "type": "object",
            "properties": {
                "decision": {
                    "type": "string",
                    "enum": ["accepted", "rejected"],
                }
            },
            "required": ["decision"],
            "additionalProperties": False,
        }
        same_shape = deepcopy(first)
        same_shape["properties"]["decision"]["enum"] = ["yes", "no"]
        changed_shape = deepcopy(first)
        changed_shape["properties"]["decision"]["enum"].append("blocked")

        first_digest = openai_strict_output_schema_shape_sha256(first)
        self.assertEqual(64, len(first_digest))
        self.assertEqual(
            first_digest,
            openai_strict_output_schema_shape_sha256(same_shape),
        )
        self.assertNotEqual(
            first_digest,
            openai_strict_output_schema_shape_sha256(changed_shape),
        )

    def test_source_gate_must_be_single_and_digest_bound(self) -> None:
        manifest = self.manifest()
        path = self.root / "gate.json"
        path.write_text(
            json.dumps(
                {
                    "status": "passed",
                    "validation_invocation_count": 1,
                    "manifest_digest": manifest.digest,
                    "candidate_count": 3,
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(RuntimeError, "fields mismatch"):
            verify_source_gate(path, manifest=manifest)

        payload = build_passed_source_gate_receipt(
            manifest=manifest,
            started_at_utc="2026-07-16T00:00:00Z",
            finished_at_utc="2026-07-16T00:00:01Z",
            actual_source_row_count=3,
            actual_candidate_count=3,
            actual_assertion_count=3,
            actual_authenticated_testable_obligation_count=0,
        )
        path.write_text(
            json.dumps(payload),
            encoding="utf-8",
        )
        gate = verify_source_gate(path, manifest=manifest)
        self.assertEqual("passed", gate["status"])

        payload["validation_invocation_count"] = 2
        path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "exactly one"):
            verify_source_gate(path, manifest=manifest)

    def test_prompt_contains_only_inline_bound_basis(self) -> None:
        manifest = self.manifest()
        evidence = PreparedEvidenceSet(
            inline_files=(
                ("evidence.json", '{"direct":"fragment"}'),
                ("source-row-baseline.json", '{"duplicate_body":"omitted"}'),
            ),
            image_paths=(),
            bindings=(
                {
                    "subject_kind": "manifest-evidence-source",
                    "subject_path": "evidence.json",
                    "subject_sha256": "4" * 64,
                    "role": "supporting-material",
                    "representation_mode": "direct-utf8",
                    "representation_path": "evidence.json",
                    "representation_sha256": "4" * 64,
                },
            ),
            snapshot_sha256={"evidence.json": "4" * 64},
            digest="5" * 64,
        )
        prompt = render_prompt(
            manifest=manifest,
            gate={"status": "passed", "manifest_digest": manifest.digest},
            instruction_files=(("runtime.md", "No tools."),),
            review_prompt="Review the exact basis.",
            evidence=evidence,
        )
        self.assertIn(manifest.digest, prompt)
        self.assertIn(evidence.digest, prompt)
        self.assertIn("No tools.", prompt)
        self.assertIn("evidence.json", prompt)
        self.assertIn("do not call tools", prompt.casefold())
        self.assertIn("source-assertion-reviewer-transport-v2", prompt)
        self.assertIn('"transport_legend"', prompt)
        self.assertIn('"clause_evidence"', prompt)
        self.assertIn("Mixed-observability semantics", prompt)
        self.assertIn("missing-observation-interface gap", prompt)
        self.assertIn("Binary optionality semantics", prompt)
        self.assertIn("third empty state", prompt)
        self.assertIn("Do not require duplicate requirement-code ownership", prompt)
        self.assertIn("affected_assertion_id and affected_atom_id", prompt)
        self.assertIn("manifest-v4 contract", prompt)
        self.assertIn("Gate-verified evidence identity: source-row-baseline.json", prompt)
        self.assertNotIn("duplicate_body", prompt)

    def test_v13_sized_prompt_uses_soft_shard_target_below_hard_cap(self) -> None:
        manifest = self.manifest()
        evidence = PreparedEvidenceSet(
            inline_files=(),
            image_paths=(),
            bindings=(),
            snapshot_sha256={},
            digest="5" * 64,
        )
        gate = {"status": "passed", "manifest_digest": manifest.digest}
        base = render_prompt(
            manifest=manifest,
            gate=gate,
            instruction_files=(),
            review_prompt="",
            evidence=evidence,
        )
        target_bytes = 283_009
        padding = target_bytes - len(base.encode("utf-8"))
        self.assertGreater(padding, 0)

        plan = plan_review_prompt_shards(
            manifest=manifest,
            gate=gate,
            instruction_files=(),
            review_prompt="x" * padding,
            evidence=evidence,
        )

        self.assertEqual(320 * 1024, DEFAULT_MAX_PROMPT_BYTES)
        self.assertGreater(len(plan), 1)
        self.assertTrue(
            all(item.prompt_bytes <= DEFAULT_MAX_PROMPT_BYTES for item in plan)
        )
        self.assertTrue(
            all(item.prompt_bytes <= DEFAULT_MAX_PROMPT_BYTES for item in plan)
        )
        self.assertTrue(
            any(item.prompt_bytes > DEFAULT_SHARD_TARGET_PROMPT_BYTES for item in plan)
        )

    def test_v16_scale_129_assertions_is_soft_sharded_and_fully_owned(self) -> None:
        base = self.manifest()
        row_template = base.source_rows[0]
        assertion_template = base.assertions[0]
        rows = tuple(
            replace(
                row_template,
                source_row_id=f"SRC-{index:03d}",
                source_locator=f"/*/*[{index}]",
                bounded_source_text=f"Bound source text {index}",
                candidate_id=f"SRC-CAND-{'1' * 20}{index:04d}",
            )
            for index in range(1, 130)
        )
        assertions = tuple(
            replace(
                assertion_template,
                assertion_id=f"ASSERT-{index:03d}",
                source_row_id=f"SRC-{index:03d}",
                locator=f"/*/*[{index}]",
                exact_source_text=f"Bound source text {index}",
                canonical_statement=f"Testable statement {index}.",
                atom_id=f"ATOM-{index:03d}",
            )
            for index in range(1, 130)
        )
        manifest = replace(
            base,
            source_rows=rows,
            assertions=assertions,
            source_row_candidate_count=129,
        )
        evidence = PreparedEvidenceSet(
            inline_files=(),
            image_paths=(),
            bindings=(),
            snapshot_sha256={},
            digest="8" * 64,
        )
        plan = plan_review_prompt_shards(
            manifest=manifest,
            gate={"status": "passed", "manifest_digest": manifest.digest},
            instruction_files=(),
            review_prompt="Review every assertion.",
            evidence=evidence,
        )

        owned = [assertion_id for shard in plan for assertion_id in shard.assertion_ids]
        self.assertGreater(len(plan), 1)
        self.assertEqual([item.assertion_id for item in assertions], owned)
        self.assertEqual(len(owned), len(set(owned)))
        self.assertTrue(
            all(len(shard.assertion_ids) <= DEFAULT_MAX_ASSERTIONS_PER_SHARD for shard in plan)
        )

    def test_soft_target_overflow_repacks_under_hard_cap(self) -> None:
        base = self.manifest()
        row_template = base.source_rows[0]
        assertion_template = base.assertions[0]
        rows = tuple(
            replace(
                row_template,
                source_row_id=f"SRC-{index:03d}",
                source_locator=f"/*/*[{index}]",
                bounded_source_text=f"Bound source text {index}",
                candidate_id=f"SRC-CAND-{'2' * 20}{index:04d}",
            )
            for index in range(1, 31)
        )
        assertions = tuple(
            replace(
                assertion_template,
                assertion_id=f"ASSERT-{index:03d}",
                source_row_id=f"SRC-{index:03d}",
                locator=f"/*/*[{index}]",
                exact_source_text=f"Bound source text {index}",
                canonical_statement=f"Testable statement {index}.",
                atom_id=f"ATOM-{index:03d}",
            )
            for index in range(1, 31)
        )
        manifest = replace(
            base,
            source_rows=rows,
            assertions=assertions,
            source_row_candidate_count=30,
        )
        evidence = PreparedEvidenceSet(
            inline_files=(("shared.md", "x" * 60_000),),
            image_paths=(),
            bindings=(),
            snapshot_sha256={},
            digest="9" * 64,
        )
        gate = {"status": "passed", "manifest_digest": manifest.digest}
        one_id = (assertions[0].assertion_id,)
        two_ids = (assertions[0].assertion_id, assertions[1].assertion_id)
        one_bytes = len(
            render_prompt(
                manifest=manifest,
                gate=gate,
                instruction_files=(),
                review_prompt="Review.",
                evidence=evidence,
                assertion_ids=one_id,
                shard_id="source-review-shard-999",
                shard_count=8,
            ).encode("utf-8")
        )
        two_bytes = len(
            render_prompt(
                manifest=manifest,
                gate=gate,
                instruction_files=(),
                review_prompt="Review.",
                evidence=evidence,
                assertion_ids=two_ids,
                shard_id="source-review-shard-999",
                shard_count=8,
            ).encode("utf-8")
        )
        self.assertGreater(two_bytes, one_bytes)

        plan = plan_review_prompt_shards(
            manifest=manifest,
            gate=gate,
            instruction_files=(),
            review_prompt="Review.",
            evidence=evidence,
            max_prompt_bytes=two_bytes + 20_000,
            max_shards=8,
            shard_target_prompt_bytes=one_bytes,
            max_assertions_per_shard=64,
        )

        self.assertLessEqual(len(plan), 8)
        self.assertEqual(
            [item.assertion_id for item in assertions],
            [assertion_id for shard in plan for assertion_id in shard.assertion_ids],
        )
        self.assertTrue(
            all(shard.prompt_bytes <= two_bytes + 20_000 for shard in plan)
        )

    def test_oversized_prompt_is_sharded_without_splitting_source_row_siblings(
        self,
    ) -> None:
        manifest = self.manifest()
        assertions = tuple(
            replace(
                assertion,
                canonical_statement=(
                    assertion.canonical_statement + " " + "x" * 120_000
                ),
            )
            for assertion in manifest.assertions
        )
        manifest = replace(manifest, assertions=assertions)
        evidence = PreparedEvidenceSet(
            inline_files=(),
            image_paths=(),
            bindings=(),
            snapshot_sha256={},
            digest="6" * 64,
        )
        gate = {"status": "passed", "manifest_digest": manifest.digest}

        plan = plan_review_prompt_shards(
            manifest=manifest,
            gate=gate,
            instruction_files=(),
            review_prompt="Review every assertion.",
            evidence=evidence,
        )

        self.assertGreater(len(plan), 1)
        self.assertLessEqual(len(plan), 8)
        self.assertTrue(
            all(item.prompt_bytes <= DEFAULT_MAX_PROMPT_BYTES for item in plan)
        )
        owned = [assertion_id for item in plan for assertion_id in item.assertion_ids]
        self.assertEqual(
            [assertion.assertion_id for assertion in manifest.assertions],
            owned,
        )
        shard_by_assertion = {
            assertion_id: shard.shard_id
            for shard in plan
            for assertion_id in shard.assertion_ids
        }
        for source_row_id in {item.source_row_id for item in manifest.assertions}:
            sibling_shards = {
                shard_by_assertion[item.assertion_id]
                for item in manifest.assertions
                if item.source_row_id == source_row_id
            }
            self.assertEqual(1, len(sibling_shards))

        merged = merge_review_shard_payloads(
            [
                self.accepted_review_payload(manifest, shard.assertion_ids)
                for shard in plan
            ],
            manifest=manifest,
            shards=plan,
        )
        self.assertEqual("accepted", merged["decision"])
        self.assertEqual(len(manifest.assertions), len(merged["assertion_reviews"]))

    def test_main_runs_fresh_shards_and_publishes_one_valid_merged_receipt(
        self,
    ) -> None:
        manifest = self.manifest()
        manifest = replace(
            manifest,
            assertions=tuple(
                replace(
                    assertion,
                    canonical_statement=(
                        assertion.canonical_statement + " " + "x" * 120_000
                    ),
                )
                for assertion in manifest.assertions
            ),
        )
        inputs = {}
        for name in ("manifest", "gate", "prompt", "inventory", "spec", "baseline"):
            path = self.root / f"sharded-{name}.json"
            path.write_text("{}\n", encoding="utf-8")
            inputs[name] = path
        outputs = {
            name: self.root / f"sharded-{name}.output"
            for name in ("receipt", "events", "stderr", "summary", "schema", "context")
        }
        outputs["session"] = self.root / "reviewer-session-log.source-assertion.md"
        outputs["decision"] = self.root / "agent-decision-log.source-assertion-review.md"
        evidence = PreparedEvidenceSet(
            inline_files=(),
            image_paths=(),
            bindings=(),
            snapshot_sha256={},
            digest="7" * 64,
        )
        gate = {"status": "passed", "manifest_digest": manifest.digest}
        expected_plan = plan_review_prompt_shards(
            manifest=manifest,
            gate=gate,
            instruction_files=(),
            review_prompt="{}\n",
            evidence=evidence,
        )
        self.assertGreater(len(expected_plan), 1)
        capability = ExecCapability(
            command="codex",
            available=True,
            verified=True,
            returncode=0,
            duration_ms=1,
            missing_flags=(),
            version="codex-cli test",
            resolved_command=str((self.root / "codex.exe").resolve()),
        )
        calls = []

        def completed_exec(command, **kwargs):
            shard = expected_plan[len(calls)]
            calls.append(shard.shard_id)
            model_receipt = Path(
                command[command.index("--output-last-message") + 1]
            )
            model_receipt.write_text(
                json.dumps(
                    self.accepted_review_payload(manifest, shard.assertion_ids)
                ),
                encoding="utf-8",
            )
            kwargs["events_path"].write_text("", encoding="utf-8")
            kwargs["stderr_path"].write_text("", encoding="utf-8")
            return 0, {"input_tokens": 10, "output_tokens": 2}, None

        argv = [
            "--repo-root", str(self.root),
            "--manifest", str(inputs["manifest"]),
            "--source-gate-receipt", str(inputs["gate"]),
            "--review-prompt", str(inputs["prompt"]),
            "--source-row-inventory", str(inputs["inventory"]),
            "--source-row-extraction-spec", str(inputs["spec"]),
            "--source-row-baseline", str(inputs["baseline"]),
            "--receipt-output", str(outputs["receipt"]),
            "--events-output", str(outputs["events"]),
            "--stderr-output", str(outputs["stderr"]),
            "--summary-output", str(outputs["summary"]),
            "--schema-output", str(outputs["schema"]),
            "--context-output", str(outputs["context"]),
            "--session-log-output", str(outputs["session"]),
            "--decision-log-output", str(outputs["decision"]),
            "--audit-ft-slug", "Demo",
        ]
        with (
            patch.object(SourceAssertionManifest, "from_dict", return_value=manifest),
            patch.object(SourceAssertionManifest, "validate", return_value=None),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.validate_passed_source_gate_receipt"
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.instruction_context",
                return_value=({"budget": {"status": "pass"}}, ()),
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.prepare_evidence_set",
                return_value=evidence,
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.probe_exec_capability",
                return_value=capability,
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.run_exec",
                side_effect=completed_exec,
            ),
        ):
            self.assertEqual(0, main(argv))

        summary = json.loads(outputs["summary"].read_text(encoding="utf-8"))
        receipt = json.loads(outputs["receipt"].read_text(encoding="utf-8"))
        self.assertEqual("bounded-sharded", summary["execution_route"])
        self.assertEqual(len(expected_plan), summary["attempt_count"])
        self.assertEqual(0, summary["retry_count"])
        self.assertEqual(len(expected_plan) * 10, summary["usage"]["input_tokens"])
        self.assertEqual(len(manifest.assertions), len(receipt["assertion_reviews"]))
        self.assertEqual([item.shard_id for item in expected_plan], calls)
        self.assertFalse(any(self.root.glob("*.model-output.tmp*")))
        session_log = outputs["session"].read_text(encoding="utf-8")
        decision_log = outputs["decision"].read_text(encoding="utf-8")
        self.assertIn("| skill | `ft-test-case-reviewer` |", session_log)
        self.assertIn("| ft_slug | `Demo` |", session_log)
        self.assertIn("## Event Timeline", session_log)
        self.assertIn("## Artifact Write Strategy", session_log)
        self.assertIn("| stage | `ft-test-case-reviewer` |", decision_log)
        self.assertIn("`accepted`", decision_log)

    def _write_docx(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        document = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/'
            'wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>'
            + text
            + "</w:t></w:r></w:p></w:body></w:document>"
        )
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("word/document.xml", document)

    def _evidence_fixture(self) -> tuple[SourceAssertionManifest, dict[str, Path]]:
        source = self.root / "source" / "main.xhtml"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(
            "<html>Bound source text 1 2 3 External boundary fragment</html>",
            encoding="utf-8",
        )
        gaps = self.root / "coverage-gaps.md"
        gaps.write_text("# Coverage gaps\n\nNo blocking gaps.\n", encoding="utf-8")
        support = self.root / "support.md"
        support.write_text("Registered supporting evidence.\n", encoding="utf-8")
        docx = self.root / "source" / "truth.docx"
        self._write_docx(docx, "Canonical direct source fragment")
        mockup = self.root / "mockup.jpg"
        mockup.write_bytes(b"registered-image-bytes")
        inventory = self.root / "source-row-inventory.md"
        extraction_spec = self.root / "source-row-extraction-spec.json"
        baseline = self.root / "source-row-baseline.json"
        inventory.write_text("typed inventory placeholder\n", encoding="utf-8")
        extraction_spec.write_text("{}\n", encoding="utf-8")
        baseline.write_text("{}\n", encoding="utf-8")
        manifest = replace(
            self.manifest(),
            coverage_gaps_artifact=RegisteredArtifact(
                path="coverage-gaps.md",
                sha256=hashlib.sha256(gaps.read_bytes()).hexdigest(),
            ),
            sources=(
                RegisteredSource(
                    path="source/main.xhtml",
                    sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                ),
            ),
            evidence_sources=(
                RegisteredEvidenceSource(
                    path="support.md",
                    sha256=hashlib.sha256(support.read_bytes()).hexdigest(),
                    role="supporting-material",
                ),
                RegisteredEvidenceSource(
                    path="source/truth.docx",
                    sha256=hashlib.sha256(docx.read_bytes()).hexdigest(),
                    role="semantic-source-of-truth",
                ),
            ),
            mockups=(
                RegisteredMockup(
                    path="mockup.jpg",
                    sha256=hashlib.sha256(mockup.read_bytes()).hexdigest(),
                    screen_name="Registered screen",
                    locators=("Income block",),
                ),
            ),
        )
        return manifest, {
            "inventory": inventory,
            "spec": extraction_spec,
            "baseline": baseline,
            "docx": docx,
        }

    def _write_bounded_extract(
        self,
        path: Path,
        *,
        source_path: str,
        source_file: Path,
        text: str = "Canonical direct source fragment",
    ) -> None:
        path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "source_path": source_path,
                    "source_sha256": hashlib.sha256(source_file.read_bytes()).hexdigest(),
                    "extraction_method": "docx-xml-literal-fragments-v1",
                    "fragments": [
                        {
                            "source_locator": "document",
                            "exact_source_text": text,
                            "exact_source_text_sha256": hashlib.sha256(
                                text.encode("utf-8")
                            ).hexdigest(),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    def test_evidence_set_requires_exact_registered_coverage(self) -> None:
        manifest, paths = self._evidence_fixture()
        with patch(
            "scripts.codex_exec_source_assertion_reviewer.verify_scope_artifacts"
        ):
            with self.assertRaisesRegex(RuntimeError, "requires one source-verified"):
                prepare_evidence_set(
                    root=self.root,
                    manifest=manifest,
                    inventory_path=paths["inventory"],
                    extraction_spec_path=paths["spec"],
                    baseline_path=paths["baseline"],
                    bounded_extract_paths=(),
                    max_direct_file_bytes=65_536,
                )

    def test_evidence_set_accepts_verified_bounded_extract_and_direct_images(self) -> None:
        manifest, paths = self._evidence_fixture()
        descriptor = self.root / "truth.extract.json"
        self._write_bounded_extract(
            descriptor,
            source_path="source/truth.docx",
            source_file=paths["docx"],
        )
        with patch(
            "scripts.codex_exec_source_assertion_reviewer.verify_scope_artifacts"
        ):
            evidence = prepare_evidence_set(
                root=self.root,
                manifest=manifest,
                inventory_path=paths["inventory"],
                extraction_spec_path=paths["spec"],
                baseline_path=paths["baseline"],
                bounded_extract_paths=(descriptor,),
                max_direct_file_bytes=65_536,
            )
        represented = {
            item["subject_path"]
            for item in evidence.bindings
            if item["subject_kind"].startswith("manifest-")
        }
        self.assertEqual(
            {"source/main.xhtml", "support.md", "source/truth.docx", "mockup.jpg"},
            represented,
        )
        self.assertEqual((self.root.resolve() / "mockup.jpg",), evidence.image_paths)
        self.assertTrue(
            any(
                item["representation_mode"] == "source-verified-bounded-extract"
                for item in evidence.bindings
            )
        )

    def test_evidence_set_accepts_redundant_source_extract_only_when_rows_cover_it(
        self,
    ) -> None:
        manifest, paths = self._evidence_fixture()
        docx_descriptor = self.root / "truth.extract.json"
        self._write_bounded_extract(
            docx_descriptor,
            source_path="source/truth.docx",
            source_file=paths["docx"],
        )
        source_file = self.root / "source" / "main.xhtml"
        fragment = manifest.source_rows[0].bounded_source_text
        source_descriptor = self.root / "source-covered.extract.json"
        source_descriptor.write_text(
            json.dumps(
                {
                    "version": 1,
                    "source_path": "source/main.xhtml",
                    "source_sha256": hashlib.sha256(
                        source_file.read_bytes()
                    ).hexdigest(),
                    "extraction_method": "utf8-literal-fragments-v1",
                    "fragments": [
                        {
                            "source_locator": "document",
                            "exact_source_text": fragment,
                            "exact_source_text_sha256": hashlib.sha256(
                                fragment.encode("utf-8")
                            ).hexdigest(),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        with patch(
            "scripts.codex_exec_source_assertion_reviewer.verify_scope_artifacts"
        ):
            evidence = prepare_evidence_set(
                root=self.root,
                manifest=manifest,
                inventory_path=paths["inventory"],
                extraction_spec_path=paths["spec"],
                baseline_path=paths["baseline"],
                bounded_extract_paths=(docx_descriptor, source_descriptor),
                max_direct_file_bytes=65_536,
            )

        source_binding = next(
            item
            for item in evidence.bindings
            if item["subject_kind"] == "manifest-source"
        )
        self.assertEqual(
            "redundant-covered-by-manifest-rows",
            source_binding["bounded_extract_disposition"],
        )
        self.assertEqual(0, source_binding["boundary_exclusion_candidate_count"])

    def test_evidence_set_keeps_explicit_sibling_boundary_candidate(self) -> None:
        manifest, paths = self._evidence_fixture()
        docx_descriptor = self.root / "truth.extract.json"
        self._write_bounded_extract(
            docx_descriptor,
            source_path="source/truth.docx",
            source_file=paths["docx"],
        )
        source_file = self.root / "source" / "main.xhtml"
        fragment = "External boundary fragment"
        source_descriptor = self.root / "source-boundary.extract.json"
        source_descriptor.write_text(
            json.dumps(
                {
                    "version": 1,
                    "source_path": "source/main.xhtml",
                    "source_sha256": hashlib.sha256(
                        source_file.read_bytes()
                    ).hexdigest(),
                    "extraction_method": "utf8-literal-fragments-v1",
                    "fragments": [
                        {
                            "source_locator": "document",
                            "exact_source_text": fragment,
                            "exact_source_text_sha256": hashlib.sha256(
                                fragment.encode("utf-8")
                            ).hexdigest(),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        with patch(
            "scripts.codex_exec_source_assertion_reviewer.verify_scope_artifacts"
        ):
            evidence = prepare_evidence_set(
                root=self.root,
                manifest=manifest,
                inventory_path=paths["inventory"],
                extraction_spec_path=paths["spec"],
                baseline_path=paths["baseline"],
                bounded_extract_paths=(docx_descriptor, source_descriptor),
                max_direct_file_bytes=65_536,
            )

        source_binding = next(
            item
            for item in evidence.bindings
            if item["subject_kind"] == "manifest-source"
        )
        self.assertEqual(
            "boundary-exclusion-candidates",
            source_binding["bounded_extract_disposition"],
        )
        self.assertEqual(1, source_binding["boundary_exclusion_candidate_count"])

    def test_evidence_set_rejects_duplicate_bounded_descriptor(self) -> None:
        manifest, paths = self._evidence_fixture()
        descriptor = self.root / "truth.extract.json"
        self._write_bounded_extract(
            descriptor,
            source_path="source/truth.docx",
            source_file=paths["docx"],
        )
        with patch(
            "scripts.codex_exec_source_assertion_reviewer.verify_scope_artifacts"
        ):
            with self.assertRaisesRegex(RuntimeError, "must not contain duplicates"):
                prepare_evidence_set(
                    root=self.root,
                    manifest=manifest,
                    inventory_path=paths["inventory"],
                    extraction_spec_path=paths["spec"],
                    baseline_path=paths["baseline"],
                    bounded_extract_paths=(descriptor, descriptor),
                    max_direct_file_bytes=65_536,
                )

    def test_bounded_extract_rejects_fragment_absent_from_source(self) -> None:
        manifest, paths = self._evidence_fixture()
        descriptor = self.root / "truth.extract.json"
        self._write_bounded_extract(
            descriptor,
            source_path="source/truth.docx",
            source_file=paths["docx"],
            text="Invented fragment not present in source",
        )
        with patch(
            "scripts.codex_exec_source_assertion_reviewer.verify_scope_artifacts"
        ):
            with self.assertRaisesRegex(RuntimeError, "absent from registered"):
                prepare_evidence_set(
                    root=self.root,
                    manifest=manifest,
                    inventory_path=paths["inventory"],
                    extraction_spec_path=paths["spec"],
                    baseline_path=paths["baseline"],
                    bounded_extract_paths=(descriptor,),
                    max_direct_file_bytes=65_536,
                )

    def test_empty_boundary_class_requires_source_verified_exclusion_candidate(self) -> None:
        manifest, paths = self._evidence_fixture()
        manifest = replace(
            manifest,
            source_rows=manifest.source_rows[:2],
            assertions=manifest.assertions[:2],
            source_row_candidate_count=2,
        )
        docx_descriptor = self.root / "truth.extract.json"
        self._write_bounded_extract(
            docx_descriptor,
            source_path="source/truth.docx",
            source_file=paths["docx"],
        )
        with patch(
            "scripts.codex_exec_source_assertion_reviewer.verify_scope_artifacts"
        ):
            with self.assertRaisesRegex(RuntimeError, "zero manifest rows"):
                prepare_evidence_set(
                    root=self.root,
                    manifest=manifest,
                    inventory_path=paths["inventory"],
                    extraction_spec_path=paths["spec"],
                    baseline_path=paths["baseline"],
                    bounded_extract_paths=(docx_descriptor,),
                    max_direct_file_bytes=65_536,
                )

        source_descriptor = self.root / "source-boundary.extract.json"
        source_file = self.root / "source" / "main.xhtml"
        text = "External boundary fragment"
        source_descriptor.write_text(
            json.dumps(
                {
                    "version": 1,
                    "source_path": "source/main.xhtml",
                    "source_sha256": hashlib.sha256(source_file.read_bytes()).hexdigest(),
                    "extraction_method": "utf8-literal-fragments-v1",
                    "fragments": [
                        {
                            "source_locator": "document",
                            "exact_source_text": text,
                            "exact_source_text_sha256": hashlib.sha256(
                                text.encode("utf-8")
                            ).hexdigest(),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        with patch(
            "scripts.codex_exec_source_assertion_reviewer.verify_scope_artifacts"
        ):
            evidence = prepare_evidence_set(
                root=self.root,
                manifest=manifest,
                inventory_path=paths["inventory"],
                extraction_spec_path=paths["spec"],
                baseline_path=paths["baseline"],
                bounded_extract_paths=(docx_descriptor, source_descriptor),
                max_direct_file_bytes=65_536,
            )
        rendered = "\n".join(content for _path, content in evidence.inline_files)
        self.assertIn("canonical_exclusion_locator", rendered)
        self.assertIn("#text-sha256=", rendered)

        overlap_descriptor = self.root / "source-boundary-overlap.extract.json"
        overlap_text = "Bound source text 1"
        overlap_descriptor.write_text(
            json.dumps(
                {
                    "version": 1,
                    "source_path": "source/main.xhtml",
                    "source_sha256": hashlib.sha256(source_file.read_bytes()).hexdigest(),
                    "extraction_method": "utf8-literal-fragments-v1",
                    "fragments": [
                        {
                            "source_locator": "document",
                            "exact_source_text": overlap_text,
                            "exact_source_text_sha256": hashlib.sha256(
                                overlap_text.encode("utf-8")
                            ).hexdigest(),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        with patch(
            "scripts.codex_exec_source_assertion_reviewer.verify_scope_artifacts"
        ):
            with self.assertRaisesRegex(RuntimeError, "overlaps a manifest"):
                prepare_evidence_set(
                    root=self.root,
                    manifest=manifest,
                    inventory_path=paths["inventory"],
                    extraction_spec_path=paths["spec"],
                    baseline_path=paths["baseline"],
                    bounded_extract_paths=(docx_descriptor, overlap_descriptor),
                    max_direct_file_bytes=65_536,
                )

    def test_output_paths_must_be_distinct_and_not_alias_inputs(self) -> None:
        first = self.root / "first.json"
        second = self.root / "second.json"
        with self.assertRaisesRegex(RuntimeError, "distinct"):
            assert_output_isolation((first, first), inputs=())
        with self.assertRaisesRegex(RuntimeError, "must not alias"):
            assert_output_isolation((first, second), inputs=(second,))

    def test_overlapping_output_reservations_fail_and_release_only_their_locks(
        self,
    ) -> None:
        first_outputs = tuple(
            self.root / f"10-first-{index}.json" for index in range(6)
        )
        first = reserve_fresh_outputs(
            first_outputs,
            receipt_output=first_outputs[0],
        )
        first_locks = tuple(
            path.with_name(f".{path.name}.source-review.lock")
            for path in first_outputs
        )
        self.assertTrue(all(path.exists() for path in first_locks))

        second_only = self.root / "00-second-only.json"
        second_outputs = (
            second_only,
            first_outputs[2],
            *(self.root / f"20-second-{index}.json" for index in range(4)),
        )
        with self.assertRaisesRegex(RuntimeError, "already reserved"):
            reserve_fresh_outputs(
                second_outputs,
                receipt_output=second_only,
            )

        second_only_lock = second_only.with_name(
            f".{second_only.name}.source-review.lock"
        )
        self.assertFalse(second_only_lock.exists())
        self.assertTrue(all(path.exists() for path in first_locks))
        first.release()
        self.assertFalse(any(path.exists() for path in first_locks))

    def test_reservation_release_does_not_delete_foreign_sidecar(self) -> None:
        owner_file = self.root / "owner-lock-inode"
        owner_descriptor = os.open(
            owner_file,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
        foreign_sidecar = self.root / ".output.source-review.lock"
        foreign_sidecar.write_text("foreign-owner\n", encoding="utf-8")
        reservation = OutputReservations(
            owner_token="owner",
            lock_handles=((foreign_sidecar, owner_descriptor),),
            model_receipt_path=self.root / ".model-output.tmp",
            delete_locks_on_close=False,
        )

        reservation.release()

        self.assertEqual(
            "foreign-owner\n",
            foreign_sidecar.read_text(encoding="utf-8"),
        )

    def test_atomic_json_publish_does_not_clobber_concurrent_owner(self) -> None:
        output = self.root / "runner-output.json"

        def concurrent_create(_source: Path, destination: Path) -> None:
            Path(destination).write_text("concurrent-owner\n", encoding="utf-8")
            raise FileExistsError(destination)

        with patch(
            "scripts.codex_exec_source_assertion_reviewer.os.link",
            side_effect=concurrent_create,
        ):
            with self.assertRaisesRegex(RuntimeError, "refusing to overwrite"):
                write_json(output, {"owned": False})

        self.assertEqual("concurrent-owner\n", output.read_text(encoding="utf-8"))
        self.assertFalse(
            any(self.root.glob(f".{output.name}.source-review.*.tmp"))
        )

    def test_descriptor_atomic_create_does_not_clobber_concurrent_output(self) -> None:
        _manifest, paths = self._evidence_fixture()
        descriptor = self.root / "truth.extract.json"
        payload = {
            "version": 1,
            "source_path": "source/truth.docx",
            "source_sha256": hashlib.sha256(paths["docx"].read_bytes()).hexdigest(),
            "extraction_method": "docx-xml-literal-fragments-v1",
            "fragments": [
                {
                    "source_locator": "document",
                    "exact_source_text": "Canonical direct source fragment",
                    "exact_source_text_sha256": hashlib.sha256(
                        b"Canonical direct source fragment"
                    ).hexdigest(),
                }
            ],
        }

        def concurrent_create(_source: Path, destination: Path) -> None:
            Path(destination).write_text("concurrent-owner\n", encoding="utf-8")
            raise FileExistsError(destination)

        with patch(
            "scripts.build_bounded_source_evidence_extract.os.link",
            side_effect=concurrent_create,
        ):
            with self.assertRaisesRegex(RuntimeError, "appeared concurrently"):
                write_validated_descriptor(
                    root=self.root,
                    output_path=descriptor,
                    payload=payload,
                )
        self.assertEqual("concurrent-owner\n", descriptor.read_text(encoding="utf-8"))

    def test_missing_image_capability_writes_no_runner_outputs(self) -> None:
        manifest = self.manifest()
        inputs = {}
        for name in ("manifest", "gate", "prompt", "inventory", "spec", "baseline"):
            path = self.root / f"{name}.json"
            path.write_text("{}\n", encoding="utf-8")
            inputs[name] = path
        outputs = {
            name: self.root / f"{name}.output"
            for name in ("receipt", "events", "stderr", "summary", "schema", "context")
        }
        evidence = PreparedEvidenceSet(
            inline_files=(),
            image_paths=(self.root / "registered.jpg",),
            bindings=(),
            snapshot_sha256={},
            digest="6" * 64,
        )
        capability = ExecCapability(
            command="codex",
            available=True,
            verified=False,
            returncode=0,
            duration_ms=1,
            missing_flags=("--image",),
        )
        argv = [
            "--repo-root", str(self.root),
            "--manifest", str(inputs["manifest"]),
            "--source-gate-receipt", str(inputs["gate"]),
            "--review-prompt", str(inputs["prompt"]),
            "--source-row-inventory", str(inputs["inventory"]),
            "--source-row-extraction-spec", str(inputs["spec"]),
            "--source-row-baseline", str(inputs["baseline"]),
            "--receipt-output", str(outputs["receipt"]),
            "--events-output", str(outputs["events"]),
            "--stderr-output", str(outputs["stderr"]),
            "--summary-output", str(outputs["summary"]),
            "--schema-output", str(outputs["schema"]),
            "--context-output", str(outputs["context"]),
        ]
        with (
            patch.object(SourceAssertionManifest, "from_dict", return_value=manifest),
            patch.object(SourceAssertionManifest, "validate", return_value=None),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.validate_passed_source_gate_receipt"
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.instruction_context",
                return_value=({"budget": {"status": "pass"}}, ()),
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.prepare_evidence_set",
                return_value=evidence,
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.probe_exec_capability",
                return_value=capability,
            ) as probe,
        ):
            self.assertEqual(2, main(argv))
        self.assertGreaterEqual(probe.call_count, 1)
        for call in probe.call_args_list:
            self.assertIsNotNone(call.kwargs.get("timeout_seconds"))
            flags = call.kwargs["additional_required_flags"]
            self.assertIn("--image", flags)
            self.assertIn("--disable", flags)
        self.assertFalse(any(path.exists() for path in outputs.values()))

        verified = replace(
            capability,
            verified=True,
            missing_flags=(),
            version="codex-cli test",
            resolved_command=str((self.root / "codex.exe").resolve()),
        )

        def mutate_prompt_during_probe(*_args, **_kwargs):
            inputs["prompt"].write_text('{"changed":true}\n', encoding="utf-8")
            return verified

        with (
            patch.object(SourceAssertionManifest, "from_dict", return_value=manifest),
            patch.object(SourceAssertionManifest, "validate", return_value=None),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.validate_passed_source_gate_receipt"
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.instruction_context",
                return_value=({"budget": {"status": "pass"}}, ()),
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.prepare_evidence_set",
                return_value=evidence,
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.probe_exec_capability",
                side_effect=mutate_prompt_during_probe,
            ),
        ):
            self.assertEqual(2, main(argv))
        self.assertFalse(any(path.exists() for path in outputs.values()))

    def test_timeout_cleans_private_receipt_without_deleting_foreign_final(
        self,
    ) -> None:
        manifest = self.manifest()
        inputs = {}
        for name in ("manifest", "gate", "prompt", "inventory", "spec", "baseline"):
            path = self.root / f"timeout-{name}.json"
            path.write_text("{}\n", encoding="utf-8")
            inputs[name] = path
        outputs = {
            name: self.root / f"timeout-{name}.output"
            for name in ("receipt", "events", "stderr", "summary", "schema", "context")
        }
        evidence = PreparedEvidenceSet(
            inline_files=(),
            image_paths=(),
            bindings=(),
            snapshot_sha256={},
            digest="7" * 64,
        )
        capability = ExecCapability(
            command="codex",
            available=True,
            verified=True,
            returncode=0,
            duration_ms=1,
            missing_flags=(),
            version="codex-cli test",
            resolved_command=str((self.root / "codex.exe").resolve()),
        )
        argv = [
            "--repo-root", str(self.root),
            "--manifest", str(inputs["manifest"]),
            "--source-gate-receipt", str(inputs["gate"]),
            "--review-prompt", str(inputs["prompt"]),
            "--source-row-inventory", str(inputs["inventory"]),
            "--source-row-extraction-spec", str(inputs["spec"]),
            "--source-row-baseline", str(inputs["baseline"]),
            "--receipt-output", str(outputs["receipt"]),
            "--events-output", str(outputs["events"]),
            "--stderr-output", str(outputs["stderr"]),
            "--summary-output", str(outputs["summary"]),
            "--schema-output", str(outputs["schema"]),
            "--context-output", str(outputs["context"]),
        ]
        model_receipt_paths: list[Path] = []

        def timed_out(command, **kwargs):
            model_receipt = Path(
                command[command.index("--output-last-message") + 1]
            )
            model_receipt_paths.append(model_receipt)
            self.assertNotEqual(outputs["receipt"], model_receipt)
            model_receipt.write_text(
                '{"decision":"accepted","forged":true}\n',
                encoding="utf-8",
            )
            with kwargs["events_path"].open(
                "x", encoding="utf-8", newline="\n"
            ) as stream:
                stream.write('{"type":"turn.started"}\n')
            with kwargs["stderr_path"].open(
                "x", encoding="utf-8", newline="\n"
            ) as stream:
                stream.write("timed out\n")
            outputs["receipt"].write_text("foreign-owner\n", encoding="utf-8")
            raise SourceReviewerRunnerError("source reviewer timed out after 1s")

        with (
            patch.object(SourceAssertionManifest, "from_dict", return_value=manifest),
            patch.object(SourceAssertionManifest, "validate", return_value=None),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.validate_passed_source_gate_receipt"
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.instruction_context",
                return_value=({"budget": {"status": "pass"}}, ()),
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.prepare_evidence_set",
                return_value=evidence,
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.probe_exec_capability",
                return_value=capability,
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.run_exec",
                side_effect=timed_out,
            ),
        ):
            self.assertEqual(2, main(argv))

        self.assertEqual(1, len(model_receipt_paths))
        self.assertFalse(model_receipt_paths[0].exists())
        self.assertEqual(
            "foreign-owner\n",
            outputs["receipt"].read_text(encoding="utf-8"),
        )
        for name in ("events", "stderr", "schema", "context", "summary"):
            self.assertTrue(outputs[name].exists(), name)
        failed_summary = json.loads(outputs["summary"].read_text(encoding="utf-8"))
        self.assertEqual("failed", failed_summary["status"])
        self.assertEqual(1, failed_summary["attempt_count"])
        self.assertEqual(1, failed_summary["model_session_count"])
        self.assertIn("timed out", failed_summary["error"])
        self.assertFalse(any(self.root.glob(".*.source-review.lock")))
        self.assertFalse(any(self.root.glob(".*.model-output.tmp")))

    def test_failure_after_output_reservation_does_not_count_model_attempt(
        self,
    ) -> None:
        manifest = self.manifest()
        inputs = {}
        for name in ("manifest", "gate", "prompt", "inventory", "spec", "baseline"):
            path = self.root / f"pre-model-{name}.json"
            path.write_text("{}\n", encoding="utf-8")
            inputs[name] = path
        outputs = {
            name: self.root / f"pre-model-{name}.output"
            for name in ("receipt", "events", "stderr", "summary", "schema", "context")
        }
        evidence = PreparedEvidenceSet(
            inline_files=(),
            image_paths=(),
            bindings=(),
            snapshot_sha256={},
            digest="9" * 64,
        )
        capability = ExecCapability(
            command="codex",
            available=True,
            verified=True,
            returncode=0,
            duration_ms=1,
            missing_flags=(),
            version="codex-cli test",
            resolved_command=str((self.root / "codex.exe").resolve()),
        )
        argv = [
            "--repo-root", str(self.root),
            "--manifest", str(inputs["manifest"]),
            "--source-gate-receipt", str(inputs["gate"]),
            "--review-prompt", str(inputs["prompt"]),
            "--source-row-inventory", str(inputs["inventory"]),
            "--source-row-extraction-spec", str(inputs["spec"]),
            "--source-row-baseline", str(inputs["baseline"]),
            "--receipt-output", str(outputs["receipt"]),
            "--events-output", str(outputs["events"]),
            "--stderr-output", str(outputs["stderr"]),
            "--summary-output", str(outputs["summary"]),
            "--schema-output", str(outputs["schema"]),
            "--context-output", str(outputs["context"]),
        ]
        original_write_json = write_json

        def fail_context_publish(path: Path, payload) -> None:
            if path.resolve() == outputs["context"].resolve():
                raise SourceReviewerRunnerError(
                    "deterministic context publication failure"
                )
            original_write_json(path, payload)

        with (
            patch.object(SourceAssertionManifest, "from_dict", return_value=manifest),
            patch.object(SourceAssertionManifest, "validate", return_value=None),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.validate_passed_source_gate_receipt"
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.instruction_context",
                return_value=({"budget": {"status": "pass"}}, ()),
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.prepare_evidence_set",
                return_value=evidence,
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.probe_exec_capability",
                return_value=capability,
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.write_json",
                side_effect=fail_context_publish,
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.run_exec",
            ) as run_exec_mock,
        ):
            self.assertEqual(2, main(argv))

        run_exec_mock.assert_not_called()
        failed_summary = json.loads(outputs["summary"].read_text(encoding="utf-8"))
        self.assertEqual("failed", failed_summary["status"])
        self.assertEqual(0, failed_summary["attempt_count"])
        self.assertEqual(0, failed_summary["model_session_count"])
        self.assertIn("context publication failure", failed_summary["error"])
        self.assertTrue(outputs["schema"].exists())
        self.assertFalse(outputs["context"].exists())
        self.assertFalse(outputs["receipt"].exists())
        self.assertFalse(any(self.root.glob(".*.source-review.lock")))
        self.assertFalse(any(self.root.glob(".*.model-output.tmp")))

    def test_summary_publish_race_rolls_back_owned_final_receipt(self) -> None:
        manifest = self.manifest()
        inputs = {}
        for name in ("manifest", "gate", "prompt", "inventory", "spec", "baseline"):
            path = self.root / f"race-{name}.json"
            path.write_text("{}\n", encoding="utf-8")
            inputs[name] = path
        outputs = {
            name: self.root / f"race-{name}.output"
            for name in ("receipt", "events", "stderr", "summary", "schema", "context")
        }
        evidence = PreparedEvidenceSet(
            inline_files=(),
            image_paths=(),
            bindings=(),
            snapshot_sha256={},
            digest="8" * 64,
        )
        capability = ExecCapability(
            command="codex",
            available=True,
            verified=True,
            returncode=0,
            duration_ms=1,
            missing_flags=(),
            version="codex-cli test",
            resolved_command=str((self.root / "codex.exe").resolve()),
        )
        argv = [
            "--repo-root", str(self.root),
            "--manifest", str(inputs["manifest"]),
            "--source-gate-receipt", str(inputs["gate"]),
            "--review-prompt", str(inputs["prompt"]),
            "--source-row-inventory", str(inputs["inventory"]),
            "--source-row-extraction-spec", str(inputs["spec"]),
            "--source-row-baseline", str(inputs["baseline"]),
            "--receipt-output", str(outputs["receipt"]),
            "--events-output", str(outputs["events"]),
            "--stderr-output", str(outputs["stderr"]),
            "--summary-output", str(outputs["summary"]),
            "--schema-output", str(outputs["schema"]),
            "--context-output", str(outputs["context"]),
        ]
        model_receipt_paths: list[Path] = []

        def completed_exec(command, **kwargs):
            self.assertEqual(
                len(MODEL_TOOL_ISOLATION_DISABLE_FEATURES),
                command.count("--disable"),
            )
            self.assertIn("remote_plugin", command)
            self.assertIn("plugins", command)
            self.assertIn("apps", command)
            self.assertIn("shell_tool", command)
            self.assertIn("browser_use", command)
            model_receipt = Path(
                command[command.index("--output-last-message") + 1]
            )
            model_receipt_paths.append(model_receipt)
            model_receipt.write_text("{}\n", encoding="utf-8")
            kwargs["events_path"].write_text("", encoding="utf-8")
            kwargs["stderr_path"].write_text("", encoding="utf-8")
            return 0, {}, None

        class AcceptedReceipt:
            decision = "accepted"
            assertion_reviews = ()

        original_write_json = write_json

        def race_summary_publish(path: Path, payload) -> None:
            if path.resolve() == outputs["summary"].resolve():
                if not path.exists():
                    self.assertTrue(outputs["receipt"].exists())
                    path.write_text("concurrent-summary-owner\n", encoding="utf-8")
                raise SourceReviewerRunnerError(
                    "source reviewer summary appeared concurrently"
                )
            original_write_json(path, payload)

        with (
            patch.object(SourceAssertionManifest, "from_dict", return_value=manifest),
            patch.object(SourceAssertionManifest, "validate", return_value=None),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.validate_passed_source_gate_receipt"
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.instruction_context",
                return_value=({"budget": {"status": "pass"}}, ()),
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.prepare_evidence_set",
                return_value=evidence,
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.probe_exec_capability",
                return_value=capability,
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.run_exec",
                side_effect=completed_exec,
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.load_source_assertion_review_receipt",
                return_value=AcceptedReceipt(),
            ),
            patch(
                "scripts.codex_exec_source_assertion_reviewer.write_json",
                side_effect=race_summary_publish,
            ),
        ):
            self.assertEqual(2, main(argv))

        self.assertFalse(outputs["receipt"].exists())
        self.assertEqual(
            "concurrent-summary-owner\n",
            outputs["summary"].read_text(encoding="utf-8"),
        )
        self.assertEqual(1, len(model_receipt_paths))
        self.assertFalse(model_receipt_paths[0].exists())
        self.assertFalse(any(self.root.glob(".*.source-review.lock")))

    def test_event_parser_detects_tools_and_usage(self) -> None:
        event = json.dumps(
            {
                "type": "item.started",
                "item": {"type": "mcp_tool_call"},
            }
        )
        self.assertEqual("mcp_tool_call", event_item_type(event))
        usage = event_usage(
            json.dumps(
                {
                    "type": "turn.completed",
                    "usage": {"input_tokens": 10, "output_tokens": 4},
                }
            )
        )
        self.assertEqual({"input_tokens": 10, "output_tokens": 4}, usage)

    def test_run_exec_terminates_on_first_tool_event(self) -> None:
        events = self.root / "events.ndjson"
        stderr = self.root / "stderr.log"
        emitted = json.dumps(
            {
                "type": "item.started",
                "item": {"type": "command_execution"},
            }
        )
        code = (
            "import sys,time; "
            f"print({emitted!r}, flush=True); "
            "sys.stdin.read(); time.sleep(5)"
        )
        return_code, usage, forbidden = run_exec(
            (sys.executable, "-c", code),
            prompt="bounded prompt",
            cwd=self.root,
            events_path=events,
            stderr_path=stderr,
            timeout_seconds=10,
        )
        self.assertNotEqual(0, return_code)
        self.assertEqual({}, usage)
        self.assertEqual("command_execution", forbidden)
        self.assertEqual(1, len(events.read_text(encoding="utf-8").splitlines()))

    def test_run_exec_terminates_on_image_generation_event(self) -> None:
        events = self.root / "image-events.ndjson"
        stderr = self.root / "image-stderr.log"
        emitted = json.dumps(
            {
                "type": "item.started",
                "item": {"type": "image_generation"},
            }
        )
        code = (
            "import sys,time; "
            f"print({emitted!r}, flush=True); "
            "sys.stdin.read(); time.sleep(5)"
        )
        return_code, usage, forbidden = run_exec(
            (sys.executable, "-c", code),
            prompt="bounded prompt",
            cwd=self.root,
            events_path=events,
            stderr_path=stderr,
            timeout_seconds=10,
        )
        self.assertNotEqual(0, return_code)
        self.assertEqual({}, usage)
        self.assertEqual("image_generation", forbidden)
        self.assertEqual(1, len(events.read_text(encoding="utf-8").splitlines()))


if __name__ == "__main__":
    unittest.main()
