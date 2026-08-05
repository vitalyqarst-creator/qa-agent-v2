from __future__ import annotations

import importlib.util
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

    def make_package(self, review_independence: str | None, tc_content: str = TC_CONTENT) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name) / "fts" / "Sample"
        (root / "test-cases").mkdir(parents=True)
        (root / "test-cases" / "sample-scope.md").write_text(tc_content, encoding="utf-8")
        practical = root / "work" / "practical" / "sample-scope"
        practical.mkdir(parents=True)
        if review_independence is not None:
            (practical / "review-independence.md").write_text(review_independence, encoding="utf-8")
        return root

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

    def test_released_practical_suite_rejects_noncanonical_english_summary_heading(self) -> None:
        ids = self.finding_ids(
            self.make_package(
                review_independence=VALID_REVIEW_INDEPENDENCE,
                tc_content=TC_CONTENT_WITH_NONCANONICAL_HEADING,
            )
        )

        self.assertIn("test-case-forbidden-formulation-smell", ids)


if __name__ == "__main__":
    unittest.main()
