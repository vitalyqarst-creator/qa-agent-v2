from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts import run_standard_scope_bridge

from test_case_agent.bounded_scope_boundary import recompute_bounded_context_sha256
from test_case_agent.semantic_design_bridge import (
    APPLICABILITY_DIMENSIONS,
    SEMANTIC_DESIGN_CONTRACT,
    SEMANTIC_DESIGN_VERSION,
    canonical_payload_sha256,
    legacy_v1_projection,
    prepared_context_sha256,
    validate_semantic_design_binding,
)
from test_case_agent.semantic_design_sharding import (
    DETERMINISTIC_NON_TESTABLE_EXECUTION_MODE,
    MODEL_EXECUTION_MODE,
    SemanticDesignShardingError,
    build_semantic_shard_plan,
    materialize_non_testable_semantic_shard,
    merge_semantic_shards,
    project_semantic_shard,
    rebind_semantic_shard_plan_ownership,
    _order_oracles_by_signal_registry,
    _remap_oracle_planned_route,
    semantic_complexity_profile,
)


def _bind(context: dict[str, object]) -> dict[str, object]:
    context.pop("source_cache", None)
    context["source_cache"] = {
        "component_digests": {
            "bounded_context_sha256": recompute_bounded_context_sha256(context)
        }
    }
    return context


def _context(row_count: int = 2) -> dict[str, object]:
    rows = []
    for index in range(1, row_count + 1):
        rows.append(
            {
                "source_row_id": f"SRC-{index:03d}",
                "field_or_action": f"Action {index}",
                "source_ref": f"BSR {index}",
                "source_locator": f"/*/*[{index}]",
                "bounded_source_text": (
                    f"BSR {index}. When action {index} is selected, result {index} is visible."
                ),
                "requirement_codes_hint": [f"BSR {index}"],
                "in_scope_hint": "yes; target behavior",
            }
        )
    return _bind(
        {
            "version": 1,
            "package_id": "WP-01",
            "scope_slug": "two-actions",
            "scope_boundary": {
                "target": "Two independent actions.",
                "include": ["Both observable actions."],
                "exclude": ["Unrelated behavior."],
            },
            "mockup_locators": [],
            "source_rows": rows,
            "sources": [],
            "approved_clarifications": [],
            "source_table_column_semantics": [],
            "expected_dependencies": [],
            "dependency_aliases": {},
            "dependency_alias_provenance": {},
            "scope_execution_facts": {
                "version": 1,
                "bounded_scope_kind": "single-section",
                "expected_testable_assertion_count": row_count,
                "expected_tc_count": row_count,
                "internal_package_count": 1,
                "has_heterogeneous_integrations": False,
                "has_large_dictionary": False,
                "mockups_ready": True,
            },
        }
    )


def _boundary(context: dict[str, object]) -> dict[str, object]:
    return {
        "version": 2,
        "status": "ready",
        "blocking_reason": "none_required",
        "scope_summary": "Verify both independently observable actions.",
        "scope_boundary": copy.deepcopy(context["scope_boundary"]),
        "source_decisions": [
            {
                "source_row_id": row["source_row_id"],
                "disposition": "included",
                "requirement_codes": copy.deepcopy(row["requirement_codes_hint"]),
                "rationale": "The selected action has a directly observable result.",
            }
            for row in context["source_rows"]
        ],
        "dependencies": [],
        "gaps": [],
        "mockup_locators": copy.deepcopy(context["mockup_locators"]),
    }


def _design(
    context: dict[str, object], boundary: dict[str, object]
) -> dict[str, object]:
    source_designs = []
    obligations = []
    atoms: list[str] = []
    test_cases: list[str] = []
    included_decisions = {
        item["source_row_id"]: item for item in boundary["source_decisions"]
    }
    for index, row in enumerate(context["source_rows"], start=1):
        row_id = str(row["source_row_id"])
        text = str(row["bounded_source_text"])
        decision = included_decisions[row_id]
        disposition = str(decision["disposition"])
        codes = list(map(str, decision["requirement_codes"]))
        assertion_id = f"ASSERT-{index:03d}"
        atom_id = f"ATOM-{index:03d}"
        if disposition != "included":
            source_designs.append(
                {
                    "source_row_id": row_id,
                    "boundary_disposition": disposition,
                    "requirement_codes": codes,
                    "assertions": [
                        {
                            "assertion_id": assertion_id,
                            "canonical_statement": (
                                "The row is non-testable context for this projected scope."
                            ),
                            "polarity": "neutral",
                            "semantic_disposition": "not-applicable",
                            "execution_readiness": "not-applicable",
                            "execution_readiness_rationale": "none_required",
                            "risk": "low",
                            "condition_clauses": [],
                            "action_clauses": [],
                            "oracle_clauses": [],
                            "requirement_codes": codes,
                            "requirement_code_evidence": [
                                {
                                    "requirement_code": code,
                                    "source_row_id": row_id,
                                    "provenance_role": "xhtml-row",
                                    "exact_source_fragment": code,
                                    "evidence_source_path": "none_required",
                                    "evidence_locator": "none_required",
                                }
                                for code in codes
                            ],
                            "clause_evidence": [],
                            "supporting_source_bindings": [],
                            "clarification_clause_bindings": [],
                            "atom_id": atom_id,
                            "obligation_ids": [],
                            "disposition_rationale": (
                                "The authoritative boundary excludes executable behavior."
                            ),
                            "source_property_id": "none_required",
                            "field_or_block": str(row["field_or_action"]),
                            "source_reference": str(row["source_ref"]),
                        }
                    ],
                }
            )
            continue
        code = codes[0]
        obligation_id = f"OBL-{index:03d}"
        tc_id = f"TC-{index:03d}"
        atoms.append(atom_id)
        test_cases.append(tc_id)
        assertion = {
            "assertion_id": assertion_id,
            "canonical_statement": f"Action {index} makes result {index} visible.",
            "polarity": "positive",
            "semantic_disposition": "testable",
            "execution_readiness": "ready",
            "execution_readiness_rationale": "none_required",
            "risk": "medium",
            "condition_clauses": [],
            "action_clauses": [f"Select action {index}."],
            "oracle_clauses": [f"Result {index} is visible."],
            "requirement_codes": [code],
            "requirement_code_evidence": [
                {
                    "requirement_code": code,
                    "source_row_id": row_id,
                    "provenance_role": "xhtml-row",
                    "exact_source_fragment": text,
                    "evidence_source_path": "none_required",
                    "evidence_locator": "none_required",
                }
            ],
            "clause_evidence": [
                {
                    "clause_kind": "action",
                    "clause_index": 0,
                    "source_row_id": row_id,
                    "exact_source_fragment": text,
                },
                {
                    "clause_kind": "oracle",
                    "clause_index": 0,
                    "source_row_id": row_id,
                    "exact_source_fragment": text,
                },
            ],
            "supporting_source_bindings": [],
            "clarification_clause_bindings": [],
            "atom_id": atom_id,
            "obligation_ids": [obligation_id],
            "disposition_rationale": "The behavior is directly observable in the scope.",
            "source_property_id": f"PROP-{row_id}",
            "field_or_block": str(row["field_or_action"]),
            "source_reference": code,
        }
        source_designs.append(
            {
                "source_row_id": row_id,
                "boundary_disposition": disposition,
                "requirement_codes": codes,
                "assertions": [assertion],
            }
        )
        obligations.append(
            {
                "obligation_id": obligation_id,
                "package_id": "WP-01",
                "linked_atom_id": atom_id,
                "source_property_id": f"PROP-{row_id}",
                "property_type": "observable-behavior",
                "obligation_class": "positive-action",
                "required_behavior": f"Result {index} becomes visible.",
                "source_ref": code,
                "planned_tc_id": tc_id,
                "review_notes": "none_required",
                "design_dimension": "scenario-use-case",
                "planned_check": f"Select action {index} and observe result {index}.",
                "check_type": "action-flow",
                "coverage_class": "positive",
                "input_class": "valid-user-action",
                "single_expected_behavior": f"Result {index} is visible.",
                "oracle_source": code,
                "test_data": "none_required",
                "dictionary_refs": [],
                "dictionary_coverage": "none_required",
                "scope_obligation_ids": [],
            }
        )
    applicability = []
    for dimension in APPLICABILITY_DIMENSIONS:
        applicable = bool(test_cases) and dimension in {
            "scenario-use-case",
            "traceability",
        }
        applicability.append(
            {
                "dimension": dimension,
                "applicable": "yes" if applicable else "no",
                "source_ref": "scope rows" if applicable else "none_required",
                "reason": (
                    "Every local action is linked to its planned test."
                    if applicable
                    else "No source evidence makes this dimension applicable."
                ),
                "linked_atoms": atoms if applicable else [],
                "linked_test_cases": test_cases if applicable else [],
            }
        )
    return {
        "version": SEMANTIC_DESIGN_VERSION,
        "contract": SEMANTIC_DESIGN_CONTRACT,
        "status": "ready",
        "blocking_reason": "none_required",
        "prepared_context_sha256": prepared_context_sha256(context),
        "scope_boundary_decision_sha256": canonical_payload_sha256(boundary),
        "scope_summary": boundary["scope_summary"],
        "included": copy.deepcopy(boundary["scope_boundary"]["include"]),
        "excluded": copy.deepcopy(boundary["scope_boundary"]["exclude"]),
        "mockup_locators": copy.deepcopy(boundary["mockup_locators"]),
        "source_designs": source_designs,
        "obligations": obligations,
        "reset_lifecycle_bindings": [],
        "dependency_bindings": [],
        "dictionaries": [],
        "negative_oracles": [],
        "requiredness_oracles": [],
        "applicability": applicability,
    }


class SemanticDesignShardingTests(unittest.TestCase):
    def test_oracles_restore_full_registry_order_after_shard_merge(self) -> None:
        registry = [
            {"signal_id": "SIG-REQ-001"},
            {"signal_id": "SIG-REQ-002"},
            {"signal_id": "SIG-REQ-012"},
        ]
        shard_order = [
            {"signal_id": "SIG-REQ-001", "marker": "first shard"},
            {"signal_id": "SIG-REQ-012", "marker": "dependency component"},
            {"signal_id": "SIG-REQ-002", "marker": "second shard"},
        ]

        ordered = _order_oracles_by_signal_registry(
            shard_order,
            registry,
            kind="requiredness",
        )

        self.assertEqual(
            ["SIG-REQ-001", "SIG-REQ-002", "SIG-REQ-012"],
            [item["signal_id"] for item in ordered],
        )

    def test_oracle_ordering_rejects_duplicate_or_missing_signals(self) -> None:
        registry = [
            {"signal_id": "SIG-REQ-001"},
            {"signal_id": "SIG-REQ-002"},
        ]
        with self.assertRaisesRegex(
            SemanticDesignShardingError,
            "do not exactly cover",
        ):
            _order_oracles_by_signal_registry(
                [
                    {"signal_id": "SIG-REQ-001"},
                    {"signal_id": "SIG-REQ-001"},
                ],
                registry,
                kind="requiredness",
            )

    def test_oracle_route_markers_follow_remapped_scope_and_tc_ids(self) -> None:
        obligation_by_key = {
            ("semantic-shard-002", "OBL-LOCAL-001"): {
                "planned_tc_id": "TC-LOCAL-001"
            }
        }
        tc_map = {
            ("semantic-shard-002", "TC-LOCAL-001"): "TC-017"
        }
        executable = {
            "decision": "executable_tc",
            "planned_tc_or_gap": "TC-LOCAL-001",
        }
        candidate = {
            "decision": "candidate_tc_required",
            "planned_tc_or_gap": "candidate:SO-NEG-001",
        }

        _remap_oracle_planned_route(
            executable,
            shard_id="semantic-shard-002",
            new_scope_obligation_id="SO-NEG-009",
            old_linked_obligation_id="OBL-LOCAL-001",
            obligation_by_key=obligation_by_key,
            tc_map=tc_map,
        )
        _remap_oracle_planned_route(
            candidate,
            shard_id="semantic-shard-002",
            new_scope_obligation_id="SO-NEG-009",
            old_linked_obligation_id="OBL-LOCAL-001",
            obligation_by_key=obligation_by_key,
            tc_map=tc_map,
        )

        self.assertEqual("TC-017", executable["planned_tc_or_gap"])
        self.assertEqual(
            "candidate:SO-NEG-009",
            candidate["planned_tc_or_gap"],
        )

    def test_exact_client_address_capacity_shape_marks_zero_shard_deterministic(
        self,
    ) -> None:
        context = _context(44)
        boundary = _boundary(context)
        for index, decision in enumerate(boundary["source_decisions"], start=1):
            if index <= 16 or index == 30:
                decision["disposition"] = "context"
                decision["requirement_codes"] = []
                context["source_rows"][index - 1]["in_scope_hint"] = (
                    "no; context-only regression fixture"
                )
                context["source_rows"][index - 1]["requirement_codes_hint"] = []
        context["source_rows"][29]["field_or_action"] = "Action 17"
        dependency = {
            "kind": "field",
            "name": "Action 17",
            "source_row_ids": ["SRC-017"],
            "resolution": "declared",
            "target_source_row_ids": ["SRC-030"],
            "exact_source_fragments": ["action 17"],
        }
        context["expected_dependencies"] = [copy.deepcopy(dependency)]
        _bind(context)
        boundary["dependencies"] = [
            {
                "dependency_id": "DEP-001",
                **copy.deepcopy(dependency),
                "gap_ids": [],
                "blocking": False,
                "rationale": "The target field is declared in the linked context row.",
            }
        ]

        plan = build_semantic_shard_plan(
            context,
            boundary,
            mode="on",
            max_included_rows=10,
            max_source_rows=16,
            max_shards=8,
        )

        self.assertEqual(
            [(16, 0), (11, 10), (10, 10), (7, 7)],
            [
                (item["owned_source_row_count"], item["owned_included_row_count"])
                for item in plan["shards"]
            ],
        )
        self.assertEqual(
            DETERMINISTIC_NON_TESTABLE_EXECUTION_MODE,
            plan["shards"][0]["execution_mode"],
        )
        self.assertTrue(
            all(
                item["execution_mode"] == MODEL_EXECUTION_MODE
                for item in plan["shards"][1:]
            )
        )

    def test_non_testable_materialization_is_stable_and_strict(self) -> None:
        context = _context(2)
        boundary = _boundary(context)
        for decision in boundary["source_decisions"]:
            decision["disposition"] = "context"
            decision["requirement_codes"] = []
            decision["rationale"] = (
                "The row is retained only as non-executable scope context."
            )
        for row in context["source_rows"]:
            row["in_scope_hint"] = "no; context-only regression fixture"
            row["requirement_codes_hint"] = []
        _bind(context)

        first, first_receipt = materialize_non_testable_semantic_shard(
            context,
            boundary,
        )
        second, second_receipt = materialize_non_testable_semantic_shard(
            context,
            boundary,
        )

        self.assertEqual(first, second)
        self.assertEqual(
            first_receipt["semantic_design_sha256"],
            second_receipt["semantic_design_sha256"],
        )
        self.assertEqual(2, first_receipt["validation"]["assertion_count"])
        self.assertEqual(0, first_receipt["validation"]["obligation_count"])

    def test_non_testable_materialization_rejects_requirement_code_clarification(
        self,
    ) -> None:
        context = _context(1)
        boundary = _boundary(context)
        boundary["source_decisions"][0]["disposition"] = "context"
        boundary["source_decisions"][0]["rationale"] = (
            "The row is retained only as non-executable scope context."
        )
        context["source_rows"][0]["in_scope_hint"] = (
            "no; context-only regression fixture"
        )
        context["approved_clarifications"] = [
            {
                "clarification_id": "CLR-ADDR-001",
                "binding_scope": "requirement-code",
                "requirement_codes": ["BSR 1"],
                "source_row_ids": [],
                "exact_answer_sha256": "a" * 64,
            }
        ]
        _bind(context)

        with self.assertRaisesRegex(
            SemanticDesignShardingError,
            "requirement-code clarification cannot bind",
        ):
            materialize_non_testable_semantic_shard(context, boundary)

    def test_auto_preserves_single_session_below_capacity(self) -> None:
        context = _context(2)
        boundary = _boundary(context)
        plan = build_semantic_shard_plan(
            context, boundary, mode="auto", max_included_rows=2, max_source_rows=2
        )
        self.assertEqual("single", plan["mode"])
        self.assertEqual("within-capacity", plan["trigger"])

    def test_source_derived_weight_triggers_sharding_below_row_limits(self) -> None:
        context = _context(5)
        boundary = _boundary(context)

        profile = semantic_complexity_profile(context, boundary)
        plan = build_semantic_shard_plan(
            context,
            boundary,
            mode="auto",
            max_included_rows=10,
            max_source_rows=10,
            max_semantic_weight=2,
        )

        self.assertEqual(10, profile["semantic_slot_count"])
        self.assertEqual(10, profile["model_semantic_weight"])
        self.assertEqual(5, profile["semantic_slot_counts"]["requirement-code"])
        self.assertEqual("complexity-exceeded", plan["trigger"])
        self.assertEqual(
            [2, 2, 2, 2, 2],
            [item["owned_semantic_weight"] for item in plan["shards"]],
        )

    def test_capacity_plan_is_complete_disjoint_and_projects_valid_scopes(self) -> None:
        context = _context(5)
        boundary = _boundary(context)
        plan = build_semantic_shard_plan(
            context, boundary, mode="auto", max_included_rows=2, max_source_rows=2
        )
        self.assertEqual("sharded", plan["mode"])
        self.assertEqual([2, 2, 1], [item["owned_source_row_count"] for item in plan["shards"]])
        owned = [row for shard in plan["shards"] for row in shard["owned_source_row_ids"]]
        self.assertEqual([f"SRC-{index:03d}" for index in range(1, 6)], owned)
        self.assertEqual(len(owned), len(set(owned)))
        for shard in plan["shards"]:
            project_semantic_shard(context, boundary, shard)

    def test_projection_keeps_only_dependency_fragments_literal_in_every_source_row(self) -> None:
        context = _context(3)
        context["source_rows"][0]["bounded_source_text"] = (
            "BSR 1. поле «Флаг» управляет первой веткой."
        )
        context["source_rows"][1]["bounded_source_text"] = (
            "BSR 2. признак «Флаг» управляет второй веткой."
        )
        context["source_rows"][2]["field_or_action"] = "Флаг"
        dependency = {
            "kind": "field",
            "name": "Флаг",
            "source_row_ids": ["SRC-001", "SRC-002"],
            "resolution": "declared",
            "target_source_row_ids": ["SRC-003"],
            "exact_source_fragments": ["«Флаг»"],
        }
        context["expected_dependencies"] = [copy.deepcopy(dependency)]
        _bind(context)
        boundary = _boundary(context)
        boundary["dependencies"] = [
            {
                "dependency_id": "DEP-001",
                **copy.deepcopy(dependency),
                "exact_source_fragments": ["поле «Флаг»", "«Флаг»"],
                "gap_ids": [],
                "blocking": False,
                "rationale": "Both references resolve to the declared field.",
            }
        ]
        shard = {
            "shard_id": "semantic-shard-001",
            "owned_source_row_ids": ["SRC-001", "SRC-002", "SRC-003"],
        }

        projected, projected_boundary = project_semantic_shard(
            context,
            boundary,
            shard,
        )

        self.assertEqual(
            ["«Флаг»"],
            projected["expected_dependencies"][0]["exact_source_fragments"],
        )
        self.assertEqual(
            ["поле «Флаг»", "«Флаг»"],
            projected_boundary["dependencies"][0]["exact_source_fragments"],
        )

    def test_projected_inline_evidence_does_not_leak_between_shards(self) -> None:
        context = _context(2)
        context["bounded_evidence_inline"] = {
            "docx": {
                "version": 1,
                "fragments": [
                    {
                        "source_locator": "paragraph:1",
                        "exact_source_text": context["source_rows"][0][
                            "bounded_source_text"
                        ],
                    },
                    {
                        "source_locator": "paragraph:2",
                        "exact_source_text": context["source_rows"][1][
                            "bounded_source_text"
                        ],
                    },
                ],
            }
        }
        _bind(context)
        boundary = _boundary(context)
        plan = build_semantic_shard_plan(
            context,
            boundary,
            mode="on",
            max_included_rows=1,
            max_source_rows=1,
        )

        projected = [
            project_semantic_shard(context, boundary, shard)[0]
            for shard in plan["shards"]
        ]

        self.assertEqual(
            [["paragraph:1"], ["paragraph:2"]],
            [
                [
                    item["source_locator"]
                    for item in shard["bounded_evidence_inline"]["docx"][
                        "fragments"
                    ]
                ]
                for shard in projected
            ],
        )

    def test_external_dynamic_dictionary_binding_is_projected_with_owned_rows(self) -> None:
        context = _context(3)
        for index in (1, 2):
            context["source_rows"][index]["bounded_source_text"] += (
                " По справочнику регионов"
            )
        context["sources"] = [
            {
                "path": "fts/demo/work/vendor-references/dadata-reference.md",
                "role": "external-vendor-reference",
                "manifest_binding": "supporting-material",
            }
        ]
        context["external_dictionary_bindings"] = [
            {
                "dictionary_name": "регионы",
                "binding_type": "external-dynamic-dictionary",
                "provider": "DaData",
                "reference_path": (
                    "fts/demo/work/vendor-references/dadata-reference.md"
                ),
                "reference_url": "https://example.test/dadata/regions",
                "source_row_ids": ["SRC-002", "SRC-003"],
                "query_parameters": {
                    "from_bound": "region",
                    "to_bound": "region",
                },
                "authority": "user-confirmed",
                "authority_ref": "CLR-DEMO-001",
            }
        ]
        dependency = {
            "kind": "dictionary",
            "name": "регионы",
            "source_row_ids": ["SRC-002", "SRC-003"],
            "resolution": "external-dynamic",
            "target_source_row_ids": [],
            "exact_source_fragments": ["По справочнику регионов"],
        }
        context["expected_dependencies"] = [copy.deepcopy(dependency)]
        _bind(context)
        boundary = _boundary(context)
        boundary["dependencies"] = [
            {
                "dependency_id": "DEP-001",
                **copy.deepcopy(dependency),
                "gap_ids": [],
                "blocking": False,
                "rationale": "Values come from a user-confirmed dynamic API.",
            }
        ]
        plan = build_semantic_shard_plan(
            context,
            boundary,
            mode="on",
            max_included_rows=1,
            max_source_rows=1,
        )

        projections = [
            project_semantic_shard(context, boundary, shard)
            for shard in plan["shards"]
        ]

        self.assertEqual([], projections[0][0]["external_dictionary_bindings"])
        self.assertEqual(
            [["SRC-002"], ["SRC-003"]],
            [
                projected[0]["external_dictionary_bindings"][0]["source_row_ids"]
                for projected in projections[1:]
            ],
        )
        self.assertEqual(
            [["SRC-002"], ["SRC-003"]],
            [
                projected[1]["dependencies"][0]["source_row_ids"]
                for projected in projections[1:]
            ],
        )

        outputs: dict[str, dict[str, object]] = {}
        for shard, (shard_context, shard_boundary) in zip(
            plan["shards"],
            projections,
            strict=True,
        ):
            design = _design(shard_context, shard_boundary)
            dependencies = shard_boundary["dependencies"]
            if dependencies:
                projected_dependency = dependencies[0]
                owned_row_id = projected_dependency["source_row_ids"][0]
                source_design = next(
                    item
                    for item in design["source_designs"]
                    if item["source_row_id"] == owned_row_id
                )
                assertion = source_design["assertions"][0]
                assertion["condition_clauses"].append(
                    "По справочнику регионов"
                )
                assertion["clause_evidence"].append(
                    {
                        "clause_kind": "condition",
                        "clause_index": 0,
                        "source_row_id": owned_row_id,
                        "exact_source_fragment": "По справочнику регионов",
                    }
                )
                design["dependency_bindings"] = [
                    {
                        **copy.deepcopy(projected_dependency),
                        "semantic_disposition": "bound",
                        "linked_assertion_ids": [assertion["assertion_id"]],
                        "linked_atom_ids": [assertion["atom_id"]],
                        "linked_obligation_ids": assertion["obligation_ids"],
                        "mapping_rationale": (
                            "DaData remains a dynamic dependency of the owned row."
                        ),
                    }
                ]
            validate_semantic_design_binding(
                shard_context,
                shard_boundary,
                design,
                require_ready=True,
            )
            outputs[str(shard["shard_id"])] = design

        merged, receipt = merge_semantic_shards(
            context,
            boundary,
            (),
            plan,
            outputs,
        )
        self.assertEqual("verified", receipt["status"])
        self.assertEqual([], merged["dictionaries"])
        self.assertEqual(1, len(merged["dependency_bindings"]))
        merged_dependency = merged["dependency_bindings"][0]
        self.assertEqual("external-dynamic", merged_dependency["resolution"])
        self.assertEqual(
            ["SRC-002", "SRC-003"],
            merged_dependency["source_row_ids"],
        )
        self.assertEqual(2, len(merged_dependency["linked_obligation_ids"]))

    def test_atomic_field_dependency_fails_closed_when_capacity_is_too_small(self) -> None:
        context = _context(2)
        context["expected_dependencies"] = [
            {
                "kind": "field",
                "name": "Action 2",
                "source_row_ids": ["SRC-001"],
                "resolution": "declared",
                "target_source_row_ids": ["SRC-002"],
                "exact_source_fragments": ["action 1"],
            }
        ]
        context["source_rows"][1]["field_or_action"] = "Action 2"
        _bind(context)
        boundary = _boundary(context)
        boundary["dependencies"] = [
            {
                "dependency_id": "DEP-001",
                "kind": "field",
                "name": "Action 2",
                "source_row_ids": ["SRC-001"],
                "resolution": "declared",
                "target_source_row_ids": ["SRC-002"],
                "exact_source_fragments": ["action 1"],
                "gap_ids": [],
                "blocking": False,
                "rationale": "The target field is declared in SRC-002.",
            }
        ]
        with self.assertRaisesRegex(
            SemanticDesignShardingError, "atomic semantic component exceeds"
        ):
            build_semantic_shard_plan(
                context, boundary, mode="on", max_included_rows=1, max_source_rows=1
            )

    def test_merge_remaps_colliding_local_ids_and_passes_full_validator(self) -> None:
        context = _context(2)
        boundary = _boundary(context)
        plan = build_semantic_shard_plan(
            context, boundary, mode="on", max_included_rows=1, max_source_rows=1
        )
        outputs: dict[str, dict[str, object]] = {}
        for shard in plan["shards"]:
            shard_context, shard_boundary = project_semantic_shard(context, boundary, shard)
            design = _design(shard_context, shard_boundary)
            validate_semantic_design_binding(
                shard_context, shard_boundary, design, require_ready=True
            )
            outputs[str(shard["shard_id"])] = design
        merged, receipt = merge_semantic_shards(
            context, boundary, (), plan, outputs
        )
        self.assertEqual("verified", receipt["status"])
        self.assertEqual(["ATOM-001", "ATOM-002"], [
            item["assertions"][0]["atom_id"] for item in merged["source_designs"]
        ])
        self.assertEqual(["OBL-001", "OBL-002"], [
            item["obligation_id"] for item in merged["obligations"]
        ])

    def test_rebind_preserves_digest_bound_safe_ownership(self) -> None:
        context = _context(3)
        boundary = _boundary(context)
        preferred = build_semantic_shard_plan(
            context,
            boundary,
            mode="on",
            max_included_rows=1,
            max_source_rows=1,
            max_shards=3,
            max_semantic_weight=8,
        )

        rebound = rebind_semantic_shard_plan_ownership(
            context,
            boundary,
            preferred,
            max_included_rows=1,
            max_source_rows=1,
            max_shards=3,
            max_semantic_weight=9,
        )

        self.assertEqual("preferred-ownership-rebound", rebound["trigger"])
        self.assertEqual(preferred["plan_sha256"], rebound["preferred_plan_sha256"])
        self.assertEqual(
            [item["owned_source_row_ids"] for item in preferred["shards"]],
            [item["owned_source_row_ids"] for item in rebound["shards"]],
        )
        self.assertEqual(9, rebound["limits"]["max_semantic_weight"])

    def test_rebind_accepts_fresh_context_with_same_safe_row_ownership(self) -> None:
        old_context = _context(3)
        old_boundary = _boundary(old_context)
        preferred = build_semantic_shard_plan(
            old_context,
            old_boundary,
            mode="on",
            max_included_rows=1,
            max_source_rows=1,
            max_shards=3,
            max_semantic_weight=8,
        )
        current_context = copy.deepcopy(old_context)
        current_context["request_summary"] = "fresh clarification-bound context"
        _bind(current_context)
        current_boundary = _boundary(current_context)

        rebound = rebind_semantic_shard_plan_ownership(
            current_context,
            current_boundary,
            preferred,
            max_included_rows=1,
            max_source_rows=1,
            max_shards=3,
            max_semantic_weight=9,
        )

        self.assertNotEqual(
            preferred["prepared_context_sha256"],
            rebound["prepared_context_sha256"],
        )
        self.assertEqual(
            [item["owned_source_row_ids"] for item in preferred["shards"]],
            [item["owned_source_row_ids"] for item in rebound["shards"]],
        )

    def test_reset_binding_survives_shard_merge_and_legacy_projection(self) -> None:
        context = _context(2)
        context["source_rows"][0]["bounded_source_text"] = (
            "BSR 1. Field has a changed value. When Clear is selected, "
            "the field becomes empty."
        )
        _bind(context)
        boundary = _boundary(context)
        plan = build_semantic_shard_plan(
            context,
            boundary,
            mode="on",
            max_included_rows=1,
            max_source_rows=1,
        )
        outputs: dict[str, dict[str, object]] = {}
        for shard in plan["shards"]:
            shard_context, shard_boundary = project_semantic_shard(
                context, boundary, shard
            )
            design = _design(shard_context, shard_boundary)
            if shard["owned_source_row_ids"] == ["SRC-001"]:
                assertion = design["source_designs"][0]["assertions"][0]
                source_text = shard_context["source_rows"][0][
                    "bounded_source_text"
                ]
                assertion["condition_clauses"] = [
                    "Field has a changed value."
                ]
                assertion["action_clauses"] = ["Select Clear."]
                assertion["oracle_clauses"] = ["The field becomes empty."]
                assertion["clause_evidence"] = [
                    {
                        "clause_kind": kind,
                        "clause_index": 0,
                        "source_row_id": "SRC-001",
                        "exact_source_fragment": source_text,
                    }
                    for kind in ("condition", "action", "oracle")
                ]
                obligation = design["obligations"][0]
                obligation.update(
                    property_type="reset",
                    obligation_class="clear",
                    coverage_class="reset",
                )
                design["reset_lifecycle_bindings"] = [
                    {
                        "obligation_id": obligation["obligation_id"],
                        "binding_kind": "reset",
                        "initial_condition_index": 0,
                        "changed_state_setup": (
                            "Prepare a visible value different from the initial one."
                        ),
                        "pre_action_state_oracle": (
                            "Observe the changed visible value before selecting Clear."
                        ),
                        "state_relation": "different-from-captured-initial",
                    }
                ]
            validate_semantic_design_binding(
                shard_context,
                shard_boundary,
                design,
                require_ready=True,
            )
            outputs[str(shard["shard_id"])] = design

        merged, _receipt = merge_semantic_shards(
            context, boundary, (), plan, outputs
        )
        projected = legacy_v1_projection(merged)

        self.assertEqual(
            ["OBL-001"],
            [item["obligation_id"] for item in merged["reset_lifecycle_bindings"]],
        )
        self.assertEqual(
            "source-condition:0",
            projected["obligations"][0]["initial_state_capture"],
        )
        self.assertEqual(
            "none_required",
            projected["obligations"][1]["initial_state_capture"],
        )

    def test_merge_rejects_missing_shard_output(self) -> None:
        context = _context(2)
        boundary = _boundary(context)
        plan = build_semantic_shard_plan(
            context, boundary, mode="on", max_included_rows=1, max_source_rows=1
        )
        with self.assertRaisesRegex(SemanticDesignShardingError, "output set mismatch"):
            merge_semantic_shards(context, boundary, (), plan, {})

    def test_sharded_runner_records_each_fresh_attempt_and_merge_time(self) -> None:
        context = _context(2)
        context["mockup_locators"] = [
            "Figure 1: both observable action controls"
        ]
        _bind(context)
        boundary = _boundary(context)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            image = root / "mockup.jpg"
            image.write_bytes(b"bounded-mockup-fixture")
            context_path = root / "context.json"
            boundary_path = root / "boundary.json"
            context_path.write_text(json.dumps(context), encoding="utf-8")
            boundary_path.write_text(json.dumps(boundary), encoding="utf-8")
            paths = run_standard_scope_bridge._runtime_paths(
                root / "runtime", "semantic-design", "semantic-design.json"
            )
            calls: list[str] = []
            shard_image_flags: list[bool] = []

            def runner(arguments) -> int:
                args = list(arguments)
                option = lambda name: Path(args[args.index(name) + 1])
                shard_context = json.loads(option("--context").read_text(encoding="utf-8"))
                shard_boundary = json.loads(
                    option("--scope-boundary-decision").read_text(encoding="utf-8")
                )
                calls.append(option("--context").parent.name)
                shard_image_flags.append("--image" in args)
                decision = _design(shard_context, shard_boundary)
                option("--decision-output").write_text(
                    json.dumps(decision), encoding="utf-8"
                )
                option("--summary-output").write_text(
                    json.dumps(
                        {
                            "status": "completed",
                            "decision": "ready",
                            "model_invoked": True,
                            "usage": {
                                "input_tokens": 100,
                                "output_tokens": 25,
                                "reasoning_tokens": 5,
                            },
                            "lifecycle": {
                                "runner_attempt_count": 1,
                                "runner_retry_count": 0,
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                return 0

            code, summary = run_standard_scope_bridge._run_sharded_semantic_design(
                repo_root=root,
                context_path=context_path,
                boundary_path=boundary_path,
                semantic_paths=paths,
                images=(image,),
                codex_command=None,
                measurement_mode="observational",
                semantic_runner=runner,
                mode="on",
                max_included_rows=1,
                max_source_rows=1,
                max_shards=4,
            )
            merged = json.loads(paths["decision"].read_text(encoding="utf-8"))

        self.assertEqual(0, code)
        self.assertEqual(2, len(calls))
        self.assertEqual([False, False], shard_image_flags)
        self.assertEqual(2, summary["lifecycle"]["runner_attempt_count"])
        self.assertEqual(200, summary["usage"]["input_tokens"])
        self.assertEqual(50, summary["usage"]["output_tokens"])
        self.assertEqual(10, summary["usage"]["reasoning_tokens"])
        self.assertEqual("sequential-fresh-sessions", summary["sharding"]["execution"])
        self.assertEqual(
            "scope-boundary-locator-projection",
            summary["sharding"]["mockup_transport"]["mode"],
        )
        self.assertEqual(
            0,
            summary["sharding"]["mockup_transport"][
                "attached_image_count_per_model_shard"
            ],
        )
        self.assertIn("preparation_ms", summary["sharding"])
        self.assertIn("merge_ms", summary["sharding"])
        self.assertEqual(2, len(merged["obligations"]))

    def test_runner_skips_zero_included_shard_and_merges_remaining_model_output(
        self,
    ) -> None:
        context = _context(4)
        boundary = _boundary(context)
        for index, decision in enumerate(boundary["source_decisions"][:2]):
            decision["disposition"] = "context"
            decision["requirement_codes"] = []
            decision["rationale"] = (
                "The row is retained only as non-executable scope context."
            )
            context["source_rows"][index]["in_scope_hint"] = (
                "no; context-only regression fixture"
            )
            context["source_rows"][index]["requirement_codes_hint"] = []
        _bind(context)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            image = root / "unprojected-mockup.jpg"
            image.write_bytes(b"unprojected-mockup-fixture")
            context_path = root / "context.json"
            boundary_path = root / "boundary.json"
            context_path.write_text(json.dumps(context), encoding="utf-8")
            boundary_path.write_text(json.dumps(boundary), encoding="utf-8")
            paths = run_standard_scope_bridge._runtime_paths(
                root / "runtime", "semantic-design", "semantic-design.json"
            )
            calls: list[str] = []
            shard_image_flags: list[bool] = []

            def runner(arguments) -> int:
                args = list(arguments)
                option = lambda name: Path(args[args.index(name) + 1])
                shard_context = json.loads(option("--context").read_text(encoding="utf-8"))
                shard_boundary = json.loads(
                    option("--scope-boundary-decision").read_text(encoding="utf-8")
                )
                calls.append(option("--context").parent.name)
                shard_image_flags.append("--image" in args)
                decision = _design(shard_context, shard_boundary)
                option("--decision-output").write_text(
                    json.dumps(decision), encoding="utf-8"
                )
                option("--summary-output").write_text(
                    json.dumps(
                        {
                            "status": "completed",
                            "decision": "ready",
                            "model_invoked": True,
                            "usage": {
                                "input_tokens": 100,
                                "output_tokens": 25,
                                "reasoning_tokens": 5,
                            },
                            "lifecycle": {
                                "runner_attempt_count": 1,
                                "runner_retry_count": 0,
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                return 0

            code, summary = run_standard_scope_bridge._run_sharded_semantic_design(
                repo_root=root,
                context_path=context_path,
                boundary_path=boundary_path,
                semantic_paths=paths,
                images=(image,),
                codex_command=None,
                measurement_mode="observational",
                semantic_runner=runner,
                mode="on",
                max_included_rows=2,
                max_source_rows=2,
                max_shards=4,
            )
            merged = json.loads(paths["decision"].read_text(encoding="utf-8"))

        self.assertEqual(0, code)
        self.assertEqual(["semantic-shard-002"], calls)
        self.assertEqual([True], shard_image_flags)
        self.assertEqual(
            "direct-image-attachment",
            summary["sharding"]["mockup_transport"]["mode"],
        )
        self.assertEqual(1, summary["lifecycle"]["runner_attempt_count"])
        self.assertEqual(1, summary["sharding"]["model_shard_count"])
        self.assertEqual(1, summary["sharding"]["deterministic_shard_count"])
        self.assertEqual(4, len(merged["source_designs"]))
        self.assertEqual(2, len(merged["obligations"]))


if __name__ == "__main__":
    unittest.main()
