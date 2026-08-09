from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "validate_agent_artifacts_practical_handoff_quality",
        ROOT_DIR / "scripts" / "validate_agent_artifacts.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PracticalHandoffQualityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = load_validator_module()

    def write_scope_brief(
        self,
        path: Path,
        *,
        dependency_status: str = "needs-test-data",
        include_ready_dependency: bool = False,
    ) -> None:
        dependency_rows = [
            "| Ключ подготовки | Подготовка | Затронутые проверки | Статус исполнения |",
            "| --- | --- | --- | --- |",
            f"| `SETUP-ACCESS-001` | Подготовить учетную запись с заданными правами. | `ATOM-002` | `{dependency_status}` |",
        ]
        if include_ready_dependency:
            dependency_rows.append(
                "| `SETUP-OBJECT-001` | Подготовить объект. | `ATOM-001` | `needs-test-data` |"
            )
        path.write_text(
            "\n".join(
                [
                    "# Краткое описание области",
                    "",
                    "## Планируемые проверки",
                    "",
                    "| Идентификатор | Проверяемое утверждение | Статус исполнения |",
                    "| --- | --- | --- |",
                    "| `ATOM-001` | Действие выполняется для подготовленного объекта. | `ready` |",
                    "| `ATOM-002` | Действие доступно пользователю с заданными правами. | `needs-test-data` |",
                    "",
                    "## Предпосылки исполнения",
                    "",
                    "| Затронутые проверки | Исполнитель | Объект и исходное состояние | Ключ подготовки | Подтверждение подготовки | Статус исполнения |",
                    "| --- | --- | --- | --- | --- | --- |",
                    "| `ATOM-001` | Пользователь с доступом. | Подготовленный объект. | `SETUP-OBJECT-001` | Шаги подготовки: создать объект по AS.10; данные: проверенные значения. | `ready` |",
                    "| `ATOM-002` | Пользователь с заданными правами. | Подготовленный объект. | `SETUP-ACCESS-001` | Отсутствует: учетная запись с заданными правами. | `needs-test-data` |",
                    "",
                    "## Зависимости от тестовых данных",
                    "",
                    *dependency_rows,
                ]
            ),
            encoding="utf-8",
        )

    def test_scope_brief_rejects_dependency_rows_that_leave_affected_check_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief, include_ready_dependency=True)

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-data-dependency-status-mismatch", finding_ids)

    def test_scope_brief_accepts_structured_preparation_and_setup_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)

            findings, checks = self.validator.validate_practical_scope_brief(brief, root)

        self.assertEqual([], findings)
        self.assertTrue(all(check.status == "pass" for check in checks))

    def test_scope_brief_requires_prerequisites_for_every_planned_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "| `ATOM-002` | Пользователь с заданными правами. | Подготовленный объект. | `SETUP-ACCESS-001` | Отсутствует: учетная запись с заданными правами. | `needs-test-data` |\n",
                    "",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-execution-prerequisites-incomplete", finding_ids)

    def test_scope_brief_requires_actor_and_initial_state_for_missing_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "| `ATOM-002` | Пользователь с заданными правами. | Подготовленный объект. | `SETUP-ACCESS-001` | Отсутствует: учетная запись с заданными правами. | `needs-test-data` |",
                    "| `ATOM-002` | Не требуется. | Не требуется. | `SETUP-ACCESS-001` | Отсутствует: учетная запись с заданными правами. | `needs-test-data` |",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-execution-prerequisites-incomplete", finding_ids)

    def test_scope_brief_rejects_ready_existing_state_without_reproducible_preparation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "Шаги подготовки: создать объект по AS.10; данные: проверенные значения.",
                    "Подготовленный объект уже существует.",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-execution-prerequisites-incomplete", finding_ids)

    def test_scope_brief_rejects_generic_actor_for_ready_access_prerequisite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "| `ATOM-001` | Пользователь с доступом. | Подготовленный объект. | `SETUP-OBJECT-001` | Шаги подготовки: создать объект по AS.10; данные: проверенные значения. | `ready` |",
                    "| `ATOM-001` | Тестировщик | Объект доступен только администратору. | `SETUP-OBJECT-001` | Шаги подготовки: создать объект по AS.10; данные: проверенные значения. | `ready` |",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-execution-prerequisites-incomplete", finding_ids)

    def test_scope_brief_requires_fixture_for_ready_role_and_status_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "| `ATOM-001` | Пользователь с доступом. | Подготовленный объект. | `SETUP-OBJECT-001` | Шаги подготовки: создать объект по AS.10; данные: проверенные значения. | `ready` |",
                    "| `ATOM-001` | Администратор | Объект в статусе «Подтвержден». | `SETUP-ADMIN-001` | Шаги подготовки: создать объект по AS.10; данные: проверенные значения. | `ready` |",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-execution-prerequisites-incomplete", finding_ids)

    def test_scope_brief_rejects_free_text_as_ready_preparation_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "Шаги подготовки: создать объект по AS.10; данные: проверенные значения.",
                    "Исходные данные: создать или выбрать объект.",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-execution-prerequisites-incomplete", finding_ids)

    def test_scope_brief_propagates_missing_setup_to_every_dependent_atom(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "| `ATOM-001` | Пользователь с доступом. | Подготовленный объект. | `SETUP-OBJECT-001` | Шаги подготовки: создать объект по AS.10; данные: проверенные значения. | `ready` |",
                    "| `ATOM-001` | Пользователь с доступом. | Подготовленный объект. | `SETUP-ACCESS-001` | Шаги подготовки: создать объект по AS.10; данные: проверенные значения. | `ready` |",
                ).replace(
                    "| `SETUP-ACCESS-001` | Подготовить учетную запись с заданными правами. | `ATOM-002` | `needs-test-data` |",
                    "| `SETUP-ACCESS-001` | Подготовить учетную запись с заданными правами. | `ATOM-001`; `ATOM-002` | `needs-test-data` |",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-scope-brief-data-dependency-status-mismatch", finding_ids)

    def test_scope_brief_rejects_english_visible_handoff_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8").replace(
                    "# Краткое описание области",
                    "# Scope Brief",
                ),
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-handoff-non-russian-visible-text", finding_ids)

    def test_scope_brief_rejects_single_english_process_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "scope-brief.md"
            self.write_scope_brief(brief)
            brief.write_text(
                brief.read_text(encoding="utf-8") + "\n| Version gate | `passed` |\n",
                encoding="utf-8",
            )

            findings, _ = self.validator.validate_practical_scope_brief(brief, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-handoff-non-russian-visible-text", finding_ids)

    def test_practical_workflow_rejects_stale_code_version_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = root / "workflow-state.yaml"
            workflow.write_text("route_profile: practical_v0_8\n", encoding="utf-8")
            state = {
                "route_profile": "practical_v0_8",
                "root_consistency": {"code_root": str(root)},
                "code_version_gate": {"code_commit": "0" * 40},
            }
            original = self.validator.current_git_commit_for_code_root
            self.validator.current_git_commit_for_code_root = lambda _: "a" * 40
            try:
                findings, _ = self.validator.validate_practical_workflow_version_gate(
                    state,
                    workflow,
                    root,
                )
            finally:
                self.validator.current_git_commit_for_code_root = original

        finding_ids = {finding.id for finding in findings}
        self.assertIn("workflow-state-practical-code-version-stale", finding_ids)

    def test_practical_writer_prompt_rejects_copied_permanent_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = root / "handoff"
            handoff.mkdir()
            prompt = handoff / "prompt.scope-to-writer.md"
            prompt.write_text(
                "\n".join(
                    [
                        "## Цель этапа",
                        "Подготовить матрицу тест-дизайна.",
                        "## Входные артефакты",
                        "- `scope-brief.md`",
                        "## Обязательные действия",
                        "- Создать матрицу.",
                        "## Не делать",
                        "- Не создавать benchmark.",
                        "## Ожидаемые выходы",
                        "- `test-design-matrix.md`.",
                        "## Gate завершения",
                        "Матрица готова.",
                    ]
                ),
                encoding="utf-8",
            )
            workflow = handoff / "workflow-state.yaml"
            workflow.write_text("route_profile: practical_v0_8\n", encoding="utf-8")

            findings, _ = self.validator.validate_active_transition_prompt(prompt, workflow, root, root)

        finding_ids = {finding.id for finding in findings}
        self.assertIn("practical-prompt-copies-permanent-guardrails", finding_ids)


if __name__ == "__main__":
    unittest.main()
