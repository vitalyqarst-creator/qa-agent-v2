from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_case_agent import (
    ManualDecisionAnswerTemplate,
    build_manual_decision_answer_template,
    load_manual_decision_answer_template,
    load_manual_decision_answer_validation,
    validate_manual_decision_answers,
    write_manual_decision_answer_template,
    write_manual_decision_answer_validation,
    write_manual_decision_matrix,
)
from tests.test_manual_decision_matrix import build_matrix, setup_matrix_fixture


class ManualDecisionAnswerValidationTests(unittest.TestCase):
    def test_builds_answer_template_from_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, matrix_path = setup_answer_fixture(Path(temp_dir))

            template = build_template(matrix_path)

            self.assertEqual("pass-with-warnings", template.template_status)
            self.assertEqual("WPKG-000001", template.package_id)

    def test_template_has_one_row_per_reviewer_decision_row(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, matrix_path = setup_answer_fixture(Path(temp_dir))
            matrix = json.loads(matrix_path.read_text(encoding="utf-8"))

            template = build_template(matrix_path)

            self.assertEqual(len(matrix["reviewer_decision_rows"]), len(template.reviewer_rows))

    def test_template_does_not_preselect_options(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _root, matrix_path = setup_answer_fixture(Path(temp_dir))

            template = build_template(matrix_path)

            self.assertTrue(all(row.answer_placeholder.selected_option_id is None for row in template.reviewer_rows))

    def test_template_preserves_allowed_options_from_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            _root, matrix_path = setup_answer_fixture(Path(temp_dir))
            matrix = json.loads(matrix_path.read_text(encoding="utf-8"))

            template = build_template(matrix_path)

            matrix_options = {
                row["row_id"]: [option["option_id"] for option in row["decision_options"]]
                for row in matrix["reviewer_decision_rows"]
            }
            template_options = {
                row.row_id: [option["option_id"] for option in row.allowed_options]
                for row in template.reviewer_rows
            }
            self.assertEqual(matrix_options, template_options)

    def test_validation_awaits_reviewer_answers_when_answers_file_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, matrix_path = setup_answer_fixture(Path(temp_dir))

            validation = validate_answers(matrix_path, root / "work" / "missing.json")

            self.assertEqual("awaiting_reviewer_answers", validation.validation_status)
            self.assertEqual(validation.answer_rows_total, validation.answer_rows_missing)
            self.assertFalse(validation.stage_9e_gate.stage_9e_allowed)

    def test_validation_blocks_package_id_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, matrix_path = setup_answer_fixture(Path(temp_dir))
            answers_path = write_answers(root, matrix_path, package_id="WPKG-OTHER")

            validation = validate_answers(matrix_path, answers_path)

            self.assertEqual("blocked", validation.validation_status)
            self.assertTrue(any("package_id mismatch" in reason for reason in validation.blocking_reasons))

    def test_validation_rejects_unknown_row_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, matrix_path = setup_answer_fixture(Path(temp_dir))
            answers_path = write_answers(root, matrix_path)
            mutate_answers(answers_path, lambda answers: answers.append(valid_answer_for_unknown_row()))

            validation = validate_answers(matrix_path, answers_path)

            self.assertEqual("rejected", validation.validation_status)
            self.assertTrue(any(item.get("reason") == "unknown row_id" for item in validation.invalid_answers))

    def test_validation_rejects_duplicate_row_answers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, matrix_path = setup_answer_fixture(Path(temp_dir))
            answers_path = write_answers(root, matrix_path)
            mutate_answers(answers_path, lambda answers: answers.append(dict(answers[0])))

            validation = validate_answers(matrix_path, answers_path)

            self.assertEqual("rejected", validation.validation_status)
            self.assertTrue(any("duplicate" in str(item).casefold() for item in validation.invalid_answers))

    def test_validation_rejects_selected_option_not_allowed_for_row(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, matrix_path = setup_answer_fixture(Path(temp_dir))
            answers_path = write_answers(root, matrix_path)
            mutate_first_answer(answers_path, selected_option_id="OPT-NOT-ALLOWED")

            validation = validate_answers(matrix_path, answers_path)

            self.assertEqual("rejected", validation.validation_status)
            self.assertTrue(any("not allowed" in str(item).casefold() for item in validation.invalid_answers))

    def test_validation_rejects_missing_rationale(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, matrix_path = setup_answer_fixture(Path(temp_dir))
            answers_path = write_answers(root, matrix_path)
            mutate_first_answer(answers_path, reviewer_rationale="")

            validation = validate_answers(matrix_path, answers_path)

            self.assertEqual("rejected", validation.validation_status)
            self.assertTrue(any("rationale" in str(item).casefold() for item in validation.invalid_answers))

    def test_validation_rejects_missing_source_evidence_when_required(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, matrix_path = setup_answer_fixture(Path(temp_dir))
            answers_path = write_answers(root, matrix_path)
            mutate_first_source_required_answer(answers_path, matrix_path, source_evidence=[])

            validation = validate_answers(matrix_path, answers_path)

            self.assertEqual("rejected", validation.validation_status)
            self.assertTrue(any("source_evidence" in str(item) for item in validation.invalid_answers))

    def test_validation_rejects_missing_existing_tc_review_notes_when_required(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, matrix_path = setup_answer_fixture(Path(temp_dir))
            answers_path = write_answers(root, matrix_path)
            mutate_first_existing_required_answer(answers_path, matrix_path, existing_tc_review_notes=[])

            validation = validate_answers(matrix_path, answers_path)

            self.assertEqual("rejected", validation.validation_status)
            self.assertTrue(any("existing_tc_review_notes" in str(item) for item in validation.invalid_answers))

    def test_validation_rejects_direct_canonical_create_edit_intent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, matrix_path = setup_answer_fixture(Path(temp_dir))
            answers_path = write_answers(root, matrix_path)
            mutate_first_answer(answers_path, reviewer_rationale="Please create canonical TC directly with --apply.")

            validation = validate_answers(matrix_path, answers_path)

            self.assertEqual("rejected", validation.validation_status)
            self.assertGreater(len(validation.unsafe_answers), 0)

    def test_validation_rejects_existing_tc_used_as_business_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, matrix_path = setup_answer_fixture(Path(temp_dir))
            answers_path = write_answers(root, matrix_path)
            mutate_first_answer(answers_path, existing_tc_review_notes=["Use existing TC as business source for the rule."])

            validation = validate_answers(matrix_path, answers_path)

            self.assertEqual("rejected", validation.validation_status)
            self.assertGreater(len(validation.unsafe_answers), 0)

    def test_validation_keeps_canonical_write_allowed_false(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, matrix_path = setup_answer_fixture(Path(temp_dir))
            answers_path = write_answers(root, matrix_path)

            validation = validate_answers(matrix_path, answers_path)

            self.assertFalse(validation.canonical_write_allowed)

    def test_validation_keeps_manual_review_required_true(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, matrix_path = setup_answer_fixture(Path(temp_dir))
            answers_path = write_answers(root, matrix_path)

            validation = validate_answers(matrix_path, answers_path)

            self.assertTrue(validation.manual_review_required)

    def test_stage_9e_gate_false_without_complete_valid_answers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, matrix_path = setup_answer_fixture(Path(temp_dir))
            answers_path = write_answers(root, matrix_path)
            mutate_answers(answers_path, lambda answers: answers.pop())

            validation = validate_answers(matrix_path, answers_path)

            self.assertFalse(validation.stage_9e_gate.stage_9e_allowed)
            self.assertFalse(validation.readiness_after_answers.can_prepare_stage_9e_draft_only)

    def test_stage_9e_gate_can_be_true_only_for_complete_valid_draft_only_answers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, matrix_path = setup_answer_fixture(Path(temp_dir))
            answers_path = write_answers(root, matrix_path)

            validation = validate_answers(matrix_path, answers_path)

            self.assertEqual("pass", validation.validation_status)
            self.assertTrue(validation.stage_9e_gate.stage_9e_allowed)
            self.assertTrue(validation.stage_9e_gate.requires_draft_only_output)
            self.assertFalse(validation.stage_9e_gate.canonical_write_allowed)

    def test_writes_json_and_markdown_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, matrix_path = setup_answer_fixture(Path(temp_dir))
            template = build_template(matrix_path)
            answers_path = write_answers(root, matrix_path)
            validation = validate_answers(matrix_path, answers_path)

            template_json, template_md = write_manual_decision_answer_template(template, root / "work")
            validation_json, validation_md = write_manual_decision_answer_validation(validation, root / "work")
            loaded_template = load_manual_decision_answer_template(template_json)
            loaded_validation = load_manual_decision_answer_validation(validation_json)

            self.assertIsInstance(loaded_template, ManualDecisionAnswerTemplate)
            self.assertEqual("pass", loaded_validation.validation_status)
            self.assertIn("Answer Table", template_md.read_text(encoding="utf-8"))
            self.assertIn("Stage 9E Gate", validation_md.read_text(encoding="utf-8"))

    def test_does_not_modify_canonical_test_case_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, matrix_path = setup_answer_fixture(Path(temp_dir))
            tc_path = root / "fts" / "Demo" / "test-cases" / "scope.md"
            before = tc_path.read_text(encoding="utf-8")

            template = build_template(matrix_path)
            write_manual_decision_answer_template(template, root / "work")
            validation = validate_answers(matrix_path, root / "work" / "missing.json")
            write_manual_decision_answer_validation(validation, root / "work")

            self.assertEqual(before, tc_path.read_text(encoding="utf-8"))


def setup_answer_fixture(root: Path) -> tuple[Path, Path]:
    root, paths = setup_matrix_fixture(root)
    matrix = build_matrix(paths, root)
    matrix_path, _ = write_manual_decision_matrix(matrix, root / "work")
    return root, matrix_path


def build_template(matrix_path: Path):
    return build_manual_decision_answer_template(package_id="WPKG-000001", matrix_path=matrix_path)


def validate_answers(matrix_path: Path, answers_path: Path):
    return validate_manual_decision_answers(package_id="WPKG-000001", matrix_path=matrix_path, answers_path=answers_path)


def write_answers(root: Path, matrix_path: Path, package_id: str = "WPKG-000001") -> Path:
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    answers = [valid_answer_for_row(row) for row in matrix["reviewer_decision_rows"]]
    path = root / "work" / "manual-decision-reviewer-answers-WPKG-000001.json"
    path.write_text(
        json.dumps(
            {
                "package_id": package_id,
                "source_matrix_path": str(matrix_path),
                "answer_schema_version": "manual-decision-answers/v1",
                "answers": answers,
                "answered_by": "unit-test-reviewer",
                "answered_at_utc": "2026-07-06T00:00:00Z",
                "review_notes": ["synthetic complete answer set"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


def valid_answer_for_row(row: dict) -> dict:
    option = row["decision_options"][0]
    answer = {
        "row_id": row["row_id"],
        "cluster_id": row["cluster_id"],
        "selected_option_id": option["option_id"],
        "reviewer_rationale": "Reviewer selected this source-backed option for future draft-only handling.",
        "source_evidence": ["REQ-DEMO-001 / BSR 1 source artifact confirms the behavior."],
        "existing_tc_review_notes": ["Existing TC was used only as coverage evidence; no business rule was derived from it."],
        "business_clarification": "No additional clarification required for this synthetic answer.",
        "no_new_tc_rationale": "No-new-TC rationale supplied if this option is selected.",
        "defer_reason": "Defer reason supplied if this option is selected.",
        "split_guidance": "Split into source-backed atomic draft candidates if this option is selected.",
        "answered_by": "unit-test-reviewer",
        "answered_at_utc": "2026-07-06T00:00:00Z",
    }
    return answer


def valid_answer_for_unknown_row() -> dict:
    answer = valid_answer_for_row(
        {
            "row_id": "MDR-UNKNOWN",
            "cluster_id": "UNKNOWN",
            "decision_options": [
                {
                    "option_id": "OPT-DEFER",
                    "allowed_next_action": "defer",
                    "requires_source_evidence": False,
                    "requires_existing_tc_review": False,
                }
            ],
        }
    )
    return answer


def mutate_answers(path: Path, mutator) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutator(payload["answers"])
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def mutate_first_answer(path: Path, **updates) -> None:
    mutate_answers(path, lambda answers: answers[0].update(updates))


def mutate_first_source_required_answer(path: Path, matrix_path: Path, **updates) -> None:
    mutate_matching_answer(path, matrix_path, lambda option: option.get("requires_source_evidence"), updates)


def mutate_first_existing_required_answer(path: Path, matrix_path: Path, **updates) -> None:
    mutate_matching_answer(path, matrix_path, lambda option: option.get("requires_existing_tc_review"), updates)


def mutate_matching_answer(path: Path, matrix_path: Path, predicate, updates: dict) -> None:
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    wanted_row = None
    for row in matrix["reviewer_decision_rows"]:
        option = row["decision_options"][0]
        if predicate(option):
            wanted_row = row["row_id"]
            break
    if wanted_row is None:
        raise AssertionError("matching row not found")

    def mutator(answers):
        for answer in answers:
            if answer["row_id"] == wanted_row:
                answer.update(updates)
                return
        raise AssertionError("answer not found")

    mutate_answers(path, mutator)


if __name__ == "__main__":
    unittest.main()
