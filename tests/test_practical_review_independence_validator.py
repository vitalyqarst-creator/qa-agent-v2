from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "validate_agent_artifacts",
        ROOT_DIR / "scripts" / "validate_agent_artifacts.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


TC_CONTENT = """# Sample scope

**Suite Readiness:** `released-ft-first`

## TC-001

**Название:** Проверка открытия раздела
**Тип:** Positive
**Приоритет:** High
**package_id:** `WP-01`
**Трассировка:** `SRC-001`

### Предусловия

1. Открыть систему.

### Тестовые данные

Не требуются.

### Шаги

1. Открыть раздел.

### Итоговый ожидаемый результат

Раздел открыт.

### Постусловия

Не требуются.
"""


TC_CONTENT_WITH_NONCANONICAL_HEADING = TC_CONTENT.replace(
    "## TC-001",
    "## Summary\n\n| Метрика | Значение |\n| --- | --- |\n| Тест-кейсов | `1` |\n\n## TC-001",
)


VALID_REVIEW_INDEPENDENCE = """# Review Independence

| field | value |
| --- | --- |
| reviewer_task_or_session | `019fc5cf-8bfe-7693-bf2f-c3c55cca4824` |
| reviewer_execution_surface | `codex-task` |
| reviewer_thread_url_or_id | `019fc5cf-8bfe-7693-bf2f-c3c55cca4824` |
| reviewer_was_separate_session | `yes` |
| reviewer_input_excluded_writer_transcript | `yes` |
| reviewer_input_excluded_writer_private_reasoning | `yes` |
| reviewer_modified_test_cases | `no` |
| independent_signoff_claim_allowed | `yes` |
| review_mode | `tc_review` |
| review_round | `3` |
"""


MATRIX_ONLY_REVIEW_INDEPENDENCE = VALID_REVIEW_INDEPENDENCE.replace(
    "| review_mode | `tc_review` |",
    "| review_mode | `matrix_review` |",
).replace(
    "| review_round | `3` |",
    "| review_round | `2` |",
)


TC_REVIEW_FINDINGS_SAME_SESSION = """# TC Review Findings

## Review Metadata

| field | value |
| --- | --- |
| review_mode | `tc_review` |
| review_round | `3` |
| reviewer_task_or_session | `current Codex task` |
| reviewer_execution_surface | `same-session` |

## Verdict

`tc-changes-required`
"""


TC_REVIEW_FINDINGS_SEPARATE_SESSION = TC_REVIEW_FINDINGS_SAME_SESSION.replace(
    "`current Codex task`",
    "`019fc5cf-8bfe-7693-bf2f-c3c55cca4824`",
)


TC_REVIEW_FINDING_WITH_ENGLISH_PROSE = """# TC Review Findings

### FINDING-001
**Review Mode:** tc_review
**Severity:** error
**Category:** test-design
**Coverage Dimension:** boundary
**Test Case ID:** TC-SAMPLE-001
**Title:** Missing lower boundary coverage for the numeric field
**Problem:** The test case checks only the maximum value and omits the minimum accepted value.
**Evidence:** `TC-SAMPLE-001`
**Required Change:** Add one atomic test case for the lower boundary acceptance.
**Source Reference:** `Table 1`
**Status:** open
"""


TC_REVIEW_FINDING_WITH_MIXED_PROSE = TC_REVIEW_FINDING_WITH_ENGLISH_PROSE.replace(
    "**Title:** Missing lower boundary coverage for the numeric field",
    "**Title:** Для поля не хватает проверки lower boundary",
).replace(
    "**Problem:** The test case checks only the maximum value and omits the minimum accepted value.",
    "**Problem:** TC проверяет `Наименование поля`, но misses lower boundary acceptance.",
).replace(
    "**Required Change:** Add one atomic test case for the lower boundary acceptance.",
    "**Required Change:** Добавить отдельный TC для lower boundary acceptance.",
)


TC_REVIEW_FINDING_WITH_RUSSIAN_VISIBLE_LABELS = """# Результаты ревью тест-кейсов

### FINDING-001
**Режим ревью:** test-design
**Критичность:** error
**Категория:** test-design
**Измерение покрытия:** boundary
**Идентификатор тест-кейса:** TC-SAMPLE-001
**Заголовок:** Не хватает проверки нижней границы числового поля
**Проблема:** В тест-кейсе проверено только максимальное значение, а минимальное допустимое значение не проверяется.
**Доказательства:** `TC-SAMPLE-001`
**Требуемое изменение:** Добавить отдельный атомарный тест-кейс для допустимого значения на нижней границе.
**Ссылка на источник:** `Таблица 1`
**Статус:** open
"""


INVALID_REVIEW_INDEPENDENCE = """# Review Independence

| field | value |
| --- | --- |
| reviewer_task_or_session | `not-available` |
| reviewer_execution_surface | `same-session` |
| reviewer_thread_url_or_id | `not-available` |
| reviewer_was_separate_session | `no` |
| reviewer_input_excluded_writer_transcript | `no` |
| reviewer_input_excluded_writer_private_reasoning | `yes` |
| reviewer_modified_test_cases | `no` |
| independent_signoff_claim_allowed | `no` |
"""


PSEUDO_ALIAS_REVIEW_INDEPENDENCE = """# Review Independence

| field | value |
| --- | --- |
| reviewer_task_or_session | `019fc5c2-tc-review-round-2` |
| reviewer_execution_surface | `codex-task` |
| reviewer_thread_url_or_id | `019fc5c2-tc-review-round-2` |
| reviewer_was_separate_session | `yes` |
| reviewer_input_excluded_writer_transcript | `yes` |
| reviewer_input_excluded_writer_private_reasoning | `yes` |
| reviewer_modified_test_cases | `no` |
| independent_signoff_claim_allowed | `yes` |
"""


SUB_AGENT_REVIEW_INDEPENDENCE = """# Review Independence

| field | value |
| --- | --- |
| reviewer_task_or_session | `019fc5cf-8bfe-7693-bf2f-c3c55cca4824` |
| reviewer_execution_surface | `sub-agent` |
| reviewer_thread_url_or_id | `019fc5cf-8bfe-7693-bf2f-c3c55cca4824` |
| reviewer_was_separate_session | `yes` |
| reviewer_input_excluded_writer_transcript | `yes` |
| reviewer_input_excluded_writer_private_reasoning | `yes` |
| reviewer_modified_test_cases | `no` |
| independent_signoff_claim_allowed | `yes` |
"""


class PracticalReviewIndependenceValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = load_validator_module()

    def make_package(
        self,
        review_independence: str | None,
        tc_content: str = TC_CONTENT,
        review_findings: str | None = None,
        review_findings_name: str = "review-findings.md",
    ) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name) / "fts" / "Sample"
        (root / "test-cases").mkdir(parents=True)
        (root / "test-cases" / "sample-scope.md").write_text(tc_content, encoding="utf-8")
        practical = root / "work" / "practical" / "sample-scope"
        practical.mkdir(parents=True)
        if review_independence is not None:
            (practical / "review-independence.md").write_text(review_independence, encoding="utf-8")
        if review_findings is not None:
            (practical / review_findings_name).write_text(review_findings, encoding="utf-8")
        return root

    def write_ready_for_writer_revision_workflow(
        self,
        root: Path,
        *,
        controller_authorized_advisory_revision: bool = False,
    ) -> None:
        handoff = root / "work" / "stage-handoffs" / "01-sample"
        handoff.mkdir(parents=True)
        auth_line = (
            "controller_authorized_advisory_revision: yes\n"
            if controller_authorized_advisory_revision
            else ""
        )
        (handoff / "workflow-state.yaml").write_text(
            "\n".join(
                [
                    "ft_slug: Sample",
                    "scope_slug: sample-scope",
                    "current_stage: ft-test-case-writer",
                    "stage_status: ready-for-writer-revision",
                    "current_round: 3",
                    "next_skill: ft-test-case-writer",
                    "review_mode: tc_review",
                    auth_line.rstrip(),
                    "required_inputs:",
                    "- work/practical/sample-scope/review-independence.md",
                    "latest_artifacts:",
                    "  review_independence: work/practical/sample-scope/review-independence.md",
                    "open_questions: []",
                    "blocking_reasons: []",
                    "",
                ]
            ).replace("\n\n", "\n"),
            encoding="utf-8",
        )

    def finding_ids(self, root: Path) -> set[str]:
        report = self.validator.validate(root)
        return {finding["id"] for finding in report["findings"]}

    def test_released_practical_suite_requires_review_independence_file(self) -> None:
        ids = self.finding_ids(self.make_package(review_independence=None))

        self.assertIn("practical-release-missing-review-independence", ids)

    def test_released_practical_suite_rejects_non_independent_review(self) -> None:
        ids = self.finding_ids(self.make_package(review_independence=INVALID_REVIEW_INDEPENDENCE))

        self.assertIn("practical-release-invalid-review-independence", ids)

    def test_released_practical_suite_rejects_pseudo_session_alias(self) -> None:
        ids = self.finding_ids(self.make_package(review_independence=PSEUDO_ALIAS_REVIEW_INDEPENDENCE))

        self.assertIn("practical-release-invalid-review-independence", ids)

    def test_released_practical_suite_rejects_sub_agent_review_surface(self) -> None:
        ids = self.finding_ids(self.make_package(review_independence=SUB_AGENT_REVIEW_INDEPENDENCE))

        self.assertIn("practical-release-invalid-review-independence", ids)

    def test_released_practical_suite_accepts_independent_review_evidence(self) -> None:
        ids = self.finding_ids(self.make_package(review_independence=VALID_REVIEW_INDEPENDENCE))

        self.assertNotIn("practical-release-missing-review-independence", ids)
        self.assertNotIn("practical-release-invalid-review-independence", ids)

    def test_v082_release_requires_a_valid_reviewer_launch_preflight_receipt(self) -> None:
        root = self.make_package(review_independence=VALID_REVIEW_INDEPENDENCE)
        (root / "work" / "practical-stage-summary.md").write_text(
            "\n".join(
                [
                    "# Practical Stage Summary",
                    "",
                    "| field | value |",
                    "| --- | --- |",
                    "| route_profile | `practical route v0.8.2` |",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        ids = self.finding_ids(root)

        self.assertIn("practical-release-invalid-review-independence", ids)

    def test_v083_release_still_requires_a_valid_reviewer_launch_preflight_receipt(self) -> None:
        root = self.make_package(review_independence=VALID_REVIEW_INDEPENDENCE)
        (root / "work" / "practical-stage-summary.md").write_text(
            "\n".join(
                [
                    "# Practical Stage Summary",
                    "",
                    "| field | value |",
                    "| --- | --- |",
                    "| route_profile | `practical route v0.8.3` |",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        ids = self.finding_ids(root)

        self.assertIn("practical-release-invalid-review-independence", ids)

    def test_v082_release_accepts_matching_reviewer_launch_preflight_receipt(self) -> None:
        root = self.make_package(
            review_independence=VALID_REVIEW_INDEPENDENCE.replace(
                "| review_round | `3` |",
                "\n".join(
                    [
                        "| review_round | `3` |",
                        "| review_launch_preflight | `review-launch-preflight.json` |",
                        "| review_launch_preflight_status | `allowed` |",
                        "| reviewer_dispatch_receipt | `review-dispatch.json` |",
                    ]
                ),
            )
        )
        (root / "work" / "practical-stage-summary.md").write_text(
            "\n".join(
                [
                    "# Practical Stage Summary",
                    "",
                    "| field | value |",
                    "| --- | --- |",
                    "| route_profile | `practical route v0.8.2` |",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (root / "work" / "practical" / "sample-scope" / "review-launch-preflight.json").write_text(
            json.dumps(
                {
                    "status": "allowed",
                    "allowed": True,
                    "review_mode": "tc_review",
                    "scope_ids": ["01"],
                    "code_branch": "codex/test",
                    "code_commit": "a" * 40,
                    "summary_sha256": "b" * 64,
                }
            ),
            encoding="utf-8",
        )
        (root / "work" / "practical" / "sample-scope" / "review-dispatch.json").write_text(
            json.dumps(
                {
                    "status": "dispatched",
                    "allowed": True,
                    "reviewer_task_or_session": "019fc5cf-8bfe-7693-bf2f-c3c55cca4824",
                    "reviewer_execution_surface": "codex-task",
                    "reviewer_thread_url_or_id": "019fc5cf-8bfe-7693-bf2f-c3c55cca4824",
                }
            ),
            encoding="utf-8",
        )

        ids = self.finding_ids(root)

        self.assertNotIn("practical-release-invalid-review-independence", ids)

    def test_tc_review_requires_matching_review_independence_mode_and_round(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                review_independence=MATRIX_ONLY_REVIEW_INDEPENDENCE,
                review_findings=TC_REVIEW_FINDINGS_SEPARATE_SESSION,
            )
        )

        self.assertIn("practical-release-invalid-review-independence", ids)

    def test_tc_review_rejects_current_codex_task_as_reviewer_session(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                review_independence=VALID_REVIEW_INDEPENDENCE,
                review_findings=TC_REVIEW_FINDINGS_SAME_SESSION,
            )
        )

        self.assertIn("practical-release-invalid-review-independence", ids)

    def test_non_independent_review_must_not_be_named_release_grade_review_findings(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                review_independence=INVALID_REVIEW_INDEPENDENCE,
                review_findings=TC_REVIEW_FINDINGS_SAME_SESSION,
            )
        )

        self.assertIn("practical-advisory-review-findings-misnamed", ids)

    def test_advisory_review_findings_filename_does_not_claim_release_grade_review(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                review_independence=INVALID_REVIEW_INDEPENDENCE,
                review_findings=TC_REVIEW_FINDINGS_SAME_SESSION,
                review_findings_name="advisory-review-findings.md",
            )
        )

        self.assertNotIn("practical-advisory-review-findings-misnamed", ids)

    def test_workflow_rejects_advisory_review_routed_to_writer_without_controller_authority(self) -> None:
        root = self.make_package(
            review_independence=INVALID_REVIEW_INDEPENDENCE,
            review_findings=TC_REVIEW_FINDINGS_SAME_SESSION,
            review_findings_name="advisory-review-findings.md",
        )
        self.write_ready_for_writer_revision_workflow(root)

        ids = self.finding_ids(root)

        self.assertIn("workflow-state-advisory-review-routed-to-writer", ids)

    def test_workflow_allows_controller_authorized_advisory_writer_revision(self) -> None:
        root = self.make_package(
            review_independence=INVALID_REVIEW_INDEPENDENCE,
            review_findings=TC_REVIEW_FINDINGS_SAME_SESSION,
            review_findings_name="advisory-review-findings.md",
        )
        self.write_ready_for_writer_revision_workflow(
            root,
            controller_authorized_advisory_revision=True,
        )

        ids = self.finding_ids(root)

        self.assertNotIn("workflow-state-advisory-review-routed-to-writer", ids)

    def test_released_practical_suite_rejects_noncanonical_english_summary_heading(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                review_independence=VALID_REVIEW_INDEPENDENCE,
                tc_content=TC_CONTENT_WITH_NONCANONICAL_HEADING,
            )
        )

        self.assertIn("test-case-forbidden-formulation-smell", ids)

    def test_review_findings_reject_english_only_human_prose(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                review_independence=VALID_REVIEW_INDEPENDENCE,
                review_findings=TC_REVIEW_FINDING_WITH_ENGLISH_PROSE,
            )
        )

        self.assertIn("review-findings-nonrussian-human-field", ids)

    def test_review_findings_reject_mixed_english_prose_hidden_by_russian_literal(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                review_independence=VALID_REVIEW_INDEPENDENCE,
                review_findings=TC_REVIEW_FINDING_WITH_MIXED_PROSE,
            )
        )

        self.assertIn("review-findings-nonrussian-human-field", ids)

    def test_review_findings_accept_russian_visible_field_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "review-findings.md"
            path.write_text(TC_REVIEW_FINDING_WITH_RUSSIAN_VISIBLE_LABELS, encoding="utf-8")

            findings, _ = self.validator.validate_review_findings(path, root)

        ids = {finding.id for finding in findings}
        self.assertNotIn("review-findings-missing-required-fields", ids)
        self.assertNotIn("review-findings-nonrussian-human-field", ids)

    def test_workflow_rejects_stale_generic_aliases_after_tc_review(self) -> None:
        root = self.make_package(
            review_independence=VALID_REVIEW_INDEPENDENCE,
            review_findings=TC_REVIEW_FINDINGS_SEPARATE_SESSION,
        )
        self.write_ready_for_writer_revision_workflow(root)
        practical = root / "work" / "practical" / "sample-scope"
        for name in ("old-session.md", "current-session.md", "old-decision.md", "current-decision.md"):
            (practical / name).write_text("# Artifact\n", encoding="utf-8")
        workflow = root / "work" / "stage-handoffs" / "01-sample" / "workflow-state.yaml"
        workflow.write_text(
            workflow.read_text(encoding="utf-8").replace(
                "  review_independence: work/practical/sample-scope/review-independence.md",
                "\n".join(
                    [
                        "  review_independence: work/practical/sample-scope/review-independence.md",
                        "  tc_review_independence: work/practical/sample-scope/current-independence.md",
                        "  session_log: work/practical/sample-scope/old-session.md",
                        "  reviewer_tc_session_log: work/practical/sample-scope/current-session.md",
                        "  decision_log: work/practical/sample-scope/old-decision.md",
                        "  reviewer_tc_decision_log: work/practical/sample-scope/current-decision.md",
                    ]
                ),
            ),
            encoding="utf-8",
        )
        (practical / "current-independence.md").write_text(VALID_REVIEW_INDEPENDENCE, encoding="utf-8")

        ids = self.finding_ids(root)

        self.assertIn("workflow-state-stale-current-tc-review-alias", ids)


if __name__ == "__main__":
    unittest.main()
