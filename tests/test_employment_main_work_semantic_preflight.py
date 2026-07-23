from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent.semantic_design_bridge import (
    _source_signal_registry,
    load_approved_clarifications,
    semantic_design_prompt,
    validate_semantic_input_preflight,
)
from test_case_agent.source_preparation import prepare_bounded_scope_context


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = Path(
    "evals/full-production-benchmark/configs/"
    "postfinal-v2-employment-main-work/bounded-context-template.json"
)


class EmploymentMainWorkSemanticPreflightTests(unittest.TestCase):
    @staticmethod
    def _boundary(context: dict[str, object]) -> dict[str, object]:
        source_decisions = []
        for row in context["source_rows"]:
            assert isinstance(row, dict)
            hint = str(row["in_scope_hint"])
            if hint.startswith("yes;"):
                disposition = "included"
            elif row.get("context_relation_required") is True:
                disposition = "context"
            else:
                disposition = "excluded"
            source_decisions.append(
                {
                    "source_row_id": row["source_row_id"],
                    "disposition": disposition,
                    "requirement_codes": copy.deepcopy(
                        row.get("requirement_codes_hint", [])
                    ),
                    "rationale": (
                        "Строка классифицирована по зафиксированной границе "
                        "интеграционного replay-теста."
                    ),
                }
            )
        dependencies = []
        for index, item in enumerate(context["expected_dependencies"], start=1):
            assert isinstance(item, dict)
            dependencies.append(
                {
                    "dependency_id": f"DEP-{index:03d}",
                    **copy.deepcopy(item),
                    "gap_ids": [],
                    "blocking": False,
                    "rationale": (
                        "Зависимость полностью разрешена подготовленным "
                        "source-only контрактом."
                    ),
                }
            )
        return {
            "version": 2,
            "status": "ready",
            "blocking_reason": "none_required",
            "scope_summary": (
                "Проверяется подблок «Основная работа» блока «Сведения о занятости»."
            ),
            "scope_boundary": copy.deepcopy(context["scope_boundary"]),
            "source_decisions": source_decisions,
            "dependencies": dependencies,
            "gaps": [],
            "mockup_locators": copy.deepcopy(context["mockup_locators"]),
        }

    def test_real_30_row_replay_is_structurally_ready_before_model(self) -> None:
        temp_root = ROOT / ".codex-temp"
        temp_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="employment-preflight-test-",
            dir=temp_root,
        ) as raw:
            work = Path(raw)
            relative = work.relative_to(ROOT)
            first = prepare_bounded_scope_context(
                repo_root=ROOT,
                context_template=TEMPLATE,
                cache_dir=relative / "cache",
                output_context=relative / "context-cold.json",
                output_baseline=relative / "baseline-cold.json",
            )
            second = prepare_bounded_scope_context(
                repo_root=ROOT,
                context_template=TEMPLATE,
                cache_dir=relative / "cache",
                output_context=relative / "context-warm.json",
                output_baseline=relative / "baseline-warm.json",
            )
            context = json.loads(
                (work / "context-warm.json").read_text(encoding="utf-8")
            )

            self.assertFalse(first.cache_hit)
            self.assertTrue(second.cache_hit)
            self.assertEqual(first.cache_key, second.cache_key)
            self.assertEqual(30, first.candidate_count)
            self.assertEqual(
                (work / "context-cold.json").read_text(encoding="utf-8").replace(
                    "baseline-cold.json", "baseline-warm.json"
                ),
                (work / "context-warm.json").read_text(encoding="utf-8"),
            )

            rows = {row["source_row_id"]: row for row in context["source_rows"]}
            date_dependency = next(
                item
                for item in context["expected_dependencies"]
                if item["name"] == "Ограничение типа Дата"
            )
            self.assertEqual(
                ["SRC-027"],
                date_dependency["target_source_row_ids"],
                "Локальный BSR 278 задаёт для SRC-028 отдельный формат ММ.ГГГГ.",
            )
            target_ids = [f"SRC-{index:03d}" for index in range(20, 30)]
            self.assertEqual(
                target_ids,
                [
                    row_id
                    for row_id, row in rows.items()
                    if "field_properties" in row
                ],
            )
            normalized = [
                rows[row_id]["field_properties"]["requiredness"][
                    "normalized_value"
                ]
                for row_id in target_ids
            ]
            self.assertEqual(9, normalized.count("required"))
            self.assertEqual(["SRC-023"], [
                row_id
                for row_id in target_ids
                if rows[row_id]["field_properties"]["requiredness"][
                    "normalized_value"
                ] == "optional"
            ])
            self.assertTrue(all(
                rows[row_id]["field_properties"]["editability"][
                    "normalized_value"
                ] == "editable"
                for row_id in target_ids
            ))
            self.assertTrue(all(
                rows[row_id]["field_properties"][property_type][
                    "source_cell_locator"
                ]
                == rows[row_id]["source_locator"]
                + ("/*[2]" if property_type == "requiredness" else "/*[3]")
                for row_id in target_ids
                for property_type in ("requiredness", "editability")
            ))
            for row_id in ("SRC-018", "SRC-019", "SRC-030"):
                self.assertNotIn("field_properties", rows[row_id])

            boundary = self._boundary(context)
            clarifications = load_approved_clarifications(ROOT, context)
            preflight = validate_semantic_input_preflight(
                context,
                boundary,
                clarifications,
            )
            self.assertEqual(
                {
                    "required": 9,
                    "optional": 1,
                    "editable": 10,
                    "read-only": 0,
                },
                preflight["field_property_counts"],
            )
            self.assertEqual(20, preflight["field_property_count"])
            self.assertEqual(10, preflight["requiredness_signal_count"])
            self.assertEqual(18, preflight["negative_signal_count"])
            self.assertEqual(3, len(preflight["dictionary_registry"]))
            defaults = preflight["requiredness_candidate_defaults"]
            self.assertEqual(10, len(defaults))
            self.assertEqual(
                [f"SIG-REQ-{index:03d}" for index in range(1, 11)],
                [item["signal_id"] for item in defaults],
            )
            self.assertTrue(all(
                item["decision"] == "candidate_tc_required"
                and item["oracle_status"] == "ui-calibration-required"
                and item["fallback_test_data"] == "Пустое значение"
                and item["planned_tc_or_gap"]
                == f"candidate:{item['scope_obligation_id']}"
                for item in defaults
            ))
            prompt = semantic_design_prompt(
                context,
                boundary,
                clarifications,
                semantic_input_preflight=preflight,
            )
            self.assertIn("semantic_requiredness_candidate_defaults", prompt)
            self.assertIn(
                "do not return status=blocked merely",
                prompt,
            )
            dictionaries = {
                item["dictionary_name"]: item
                for item in preflight["dictionary_registry"]
            }
            self.assertEqual(
                ["DICT-001", "DICT-002", "DICT-003"],
                [
                    item["dictionary_id"]
                    for item in preflight["dictionary_registry"]
                ],
            )
            social = dictionaries["Социальный статус"]["active_values"]
            self.assertEqual(
                [
                    "собственник бизнеса",
                    "ИП",
                    "работа по найму",
                    "пенсионер (не работает)",
                    "самозанятый",
                    "военнослужащий",
                ],
                social,
            )
            self.assertFalse(any("BSR" in value for value in social))
            opf = dictionaries["ОПФ"]["active_values"]
            self.assertEqual(32, len(opf))
            self.assertEqual("ИП", opf[0])
            self.assertEqual("ПИФ О", opf[-1])
            self.assertEqual(
                5,
                len(dictionaries["Типы должности"]["active_values"]),
            )
            self.assertEqual(["SRC-030"], preflight["state_change_source_row_ids"])
            self.assertEqual(
                ["CLR-EMP-002"],
                preflight["readd_lifecycle_clarification_ids"],
            )

            eligible_ids = {
                item["source_row_id"]
                for item in boundary["source_decisions"]
                if item["disposition"] in {"included", "context"}
            }
            eligible_rows = [
                row for row in context["source_rows"]
                if row["source_row_id"] in eligible_ids
            ]
            code_registry = {
                item["source_row_id"]: item["requirement_codes"]
                for item in boundary["source_decisions"]
            }
            negative = _source_signal_registry(
                eligible_rows,
                code_registry,
            )["negative"]
            bsr_272_classes = [
                signal["negative_class"]
                for signal in negative
                if "BSR 272" in signal["requirement_codes"]
            ]
            self.assertEqual(
                [
                    "length-n-minus-one",
                    "length-n-plus-one",
                    "letters",
                    "spaces",
                    "special-characters",
                    "decimal-separator",
                    "sign",
                ],
                bsr_272_classes,
            )
            codes = {
                code
                for signal in negative
                for code in signal["requirement_codes"]
            }
            self.assertIn("BSR 272", codes)
            self.assertIn("BSR 280", codes)
            self.assertIn("BSR 283", codes)
            self.assertNotIn("BSR 273", codes)


if __name__ == "__main__":
    unittest.main()
