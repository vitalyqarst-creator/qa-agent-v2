from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_case_agent.practical_v09 import (
    ROUTE_VERSION,
    PracticalV09Error,
    build_review_manifest,
    build_validator_report,
    matrix_review_required,
    sha256_file,
    validate_scope,
    verify_review_result,
    write_json,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


class PracticalV09Fixture:
    def __init__(self, root: Path, *, obligation_statement: str = "Пункт меню «Партнеры» доступен пользователю.") -> None:
        self.root = root
        (root / "source").mkdir(parents=True)
        (root / "work" / "practical-v0.9" / "menu").mkdir(parents=True)
        for name in ("main.docx", "main.xhtml", "main.pdf"):
            (root / "source" / name).write_text(name, encoding="utf-8")
        (root / "AGENT-NOTES.md").write_text("# Notes\n", encoding="utf-8")
        self.scope_dir = root / "work" / "practical-v0.9" / "menu"
        self.source_manifest = root / "work" / "practical-v0.9" / "source-package-manifest.json"
        source_payload = {
            "schema_version": 1,
            "route_version": ROUTE_VERSION,
            "source_contract_version": "source-package-v1",
            "documents": [
                {"role": "main-docx", "path": "source/main.docx", "sha256": sha256_file(root / "source" / "main.docx")},
                {"role": "main-xhtml", "path": "source/main.xhtml", "sha256": sha256_file(root / "source" / "main.xhtml")},
                {"role": "pdf-cross-check", "path": "source/main.pdf", "sha256": sha256_file(root / "source" / "main.pdf")},
            ],
            "agent_notes": {"path": "AGENT-NOTES.md", "sha256": sha256_file(root / "AGENT-NOTES.md")},
            "support_inputs": [],
        }
        write_json(self.source_manifest, source_payload)
        self.obligations = self.scope_dir / "scope-obligations.json"
        write_json(
            self.obligations,
            {
                "schema_version": 1,
                "route_version": ROUTE_VERSION,
                "source_manifest_sha256": sha256_file(self.source_manifest),
                "scope": {"id": "01", "slug": "menu", "title": "Меню"},
                "obligations": [
                    {
                        "id": "OBL-001",
                        "source_anchor": "Раздел 9.1, строка «Партнеры»",
                        "statement": obligation_statement,
                        "risk_flags": [],
                    }
                ],
                "clarifications": [],
            },
        )
        self.matrix = self.scope_dir / "test-design-matrix.md"
        self.matrix.write_text(
            "# Матрица тест-дизайна\n\n"
            "| Проверка | Обязательство ФТ | Сценарий | Тип | Приоритет | Статус исполнения | Планируемый TC-ID |\n"
            "| --- | --- | --- | --- | --- | --- | --- |\n"
            "| MTX-001 | OBL-001 | Открытие пункта меню | Positive | High | ready | TC-MENU-001 |\n",
            encoding="utf-8",
        )
        self.tc = root / "test-cases" / "9.1-menu.md"
        self.tc.parent.mkdir()
        self.tc.write_text(
            "## TC-MENU-001\n"
            "**Название:** Открытие раздела «Партнеры»\n"
            "**Тип:** Positive\n"
            "**Приоритет:** High\n"
            "**Статус исполнения:** ready\n"
            "**Трассировка:** `OBL-001`; Раздел 9.1.\n"
            "**Цель:** Проверить открытие раздела «Партнеры».\n"
            "**Предусловия:** Пользователь вошел в систему.\n"
            "**Тестовые данные:** Не требуются.\n"
            "**Шаги:** Открыть раздел «Партнеры».\n"
            "**Итоговый ожидаемый результат:** Открывается раздел «Партнеры».\n",
            encoding="utf-8",
        )
        self.state = self.scope_dir / "workflow-state.json"
        write_json(
            self.state,
            {
                "route_version": ROUTE_VERSION,
                "scope_id": "01",
                "scope_slug": "menu",
                "phase": "test-cases",
                "next_action": "Провести независимое review тест-кейсов",
                "matrix_review_required": False,
                "contract_versions": {
                    "route": ROUTE_VERSION,
                    "source_package": "source-package-v1",
                },
                "artifacts": {
                    "source_package_manifest": "work/practical-v0.9/source-package-manifest.json",
                    "scope_obligations": "work/practical-v0.9/menu/scope-obligations.json",
                    "test_design_matrix": "work/practical-v0.9/menu/test-design-matrix.md",
                    "canonical_test_cases": "test-cases/9.1-menu.md",
                    "validator_report": "work/practical-v0.9/menu/validator-report.json",
                },
                "reviews": [],
                "decision_notes": [],
            },
        )


class PracticalV09Tests(unittest.TestCase):
    def test_scope_validator_is_one_pass_and_ignores_sibling_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            sibling = fixture.root / "work" / "practical-v0.9" / "other"
            sibling.mkdir()
            (sibling / "broken.md").write_text("broken", encoding="utf-8")
            output = fixture.scope_dir / "validator-report.json"
            command = [
                sys.executable,
                str(REPO_ROOT / "scripts" / "validate_practical_scope.py"),
                "--ft-package-root",
                str(fixture.root),
                "--scope-manifest",
                str(fixture.state),
                "--output-profile",
                str(output),
                "--exclude-output",
                str(output),
                "--require-clean",
            ]
            completed = subprocess.run(
                command,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(report["summary"]["clean"])
            self.assertNotIn("validator_report", report["input_hashes"])
            self.assertEqual("menu", report["scope_slug"])
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            self.assertEqual(
                "work/practical-v0.9/menu/validator-report.json",
                state["artifacts"]["validator_report"],
            )
            rerun = subprocess.run(
                command,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(0, rerun.returncode, rerun.stderr)

    def test_scope_rejects_a_scope_local_source_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["artifacts"]["source_package_manifest"] = (
                "work/practical-v0.9/menu/source-package-manifest.json"
            )
            write_json(fixture.state, state)

            with self.assertRaises(PracticalV09Error):
                validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)

    def test_style_warning_is_visible_but_not_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw), obligation_statement="Проверить source-backed значение.")
            context, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            report = build_validator_report(context, findings)
            matching = [item for item in report["findings"] if item["id"] == "scope-obligation-process-language"]
            self.assertEqual(1, len(matching))
            self.assertFalse(matching[0]["blocking"])
            self.assertTrue(report["summary"]["clean"])

    def test_missing_primary_expected_result_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.tc.write_text(fixture.tc.read_text(encoding="utf-8").replace("**Итоговый ожидаемый результат:** Открывается раздел «Партнеры».\n", ""), encoding="utf-8")
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            matching = [item for item in findings if item.id == "test-case-required-field"]
            self.assertTrue(matching)
            self.assertTrue(all(item.blocking for item in matching))

    def test_execution_status_must_be_present_and_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "**Статус исполнения:** ready",
                    "**Статус исполнения:** unknown-status",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn(
                "test-case-execution-status",
                [item.id for item in findings if item.blocking],
            )

    def test_complex_scope_requires_matrix_review(self) -> None:
        payload = {
            "obligations": [
                {"id": f"OBL-{index:03d}", "risk_flags": []}
                for index in range(1, 9)
            ]
        }
        required, reasons = matrix_review_required(payload)
        self.assertTrue(required)
        self.assertIn("Количество обязательств", reasons[0])
        required, reasons = matrix_review_required(
            {"obligations": [{"id": "OBL-001", "risk_flags": ["authorization"]}]}
        )
        self.assertTrue(required)
        self.assertIn("authorization", reasons[0])

    def test_required_matrix_review_blocks_test_case_phase_until_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["obligations"][0]["risk_flags"] = ["authorization"]
            write_json(fixture.obligations, obligations)
            context, findings = validate_scope(
                package_root=fixture.root,
                workflow_state_path=fixture.state,
            )
            self.assertTrue(context["matrix_review_required"])
            self.assertIn(
                "matrix-review-required-before-test-cases",
                [item.id for item in findings if item.blocking],
            )
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["reviews"] = [{"mode": "matrix", "verdict": "approved"}]
            write_json(fixture.state, state)
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertNotIn(
                "matrix-review-required-before-test-cases",
                [item.id for item in findings],
            )

    def test_accepted_state_requires_final_tc_review(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["phase"] = "accepted"
            write_json(fixture.state, state)
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn(
                "test-cases-review-required-before-acceptance",
                [item.id for item in findings if item.blocking],
            )

    def test_review_result_requires_distinct_top_level_thread_and_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            manifest = build_review_manifest(
                package_root=fixture.root,
                workflow_state_path=fixture.state,
                review_mode="test-cases",
                controller_thread_id="019feebf-3cde-79d2-9f87-ba9c61ff7b13",
                code_branch="codex/test",
                code_commit="abc123",
                contract_digest="contract",
            )
            manifest_path = fixture.scope_dir / "test-cases-review-manifest.json"
            write_json(manifest_path, manifest)
            result_path = fixture.scope_dir / "test-cases-review-result.json"
            write_json(
                result_path,
                {
                    "review_manifest_sha256": sha256_file(manifest_path),
                    "scope_id": "01",
                    "scope_slug": "menu",
                    "review_mode": "test-cases",
                    "execution_surface": "codex-thread",
                    "reviewer_thread_id": "019feebf-3cde-79d2-9f87-ba9c61ff7b14",
                    "independent_obligations": ["OBL-001"],
                    "verdict": "approved",
                    "findings": [],
                },
            )
            _, findings = verify_review_result(
                package_root=fixture.root,
                manifest_path=manifest_path,
                result_path=result_path,
            )
            self.assertFalse([item for item in findings if item.blocking])
            fixture.tc.write_text(fixture.tc.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            _, findings = verify_review_result(
                package_root=fixture.root,
                manifest_path=manifest_path,
                result_path=result_path,
            )
            self.assertIn("review-result-snapshot-changed", [item.id for item in findings])

    def test_reviewer_must_reconstruct_the_full_obligation_set(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            manifest = build_review_manifest(
                package_root=fixture.root,
                workflow_state_path=fixture.state,
                review_mode="test-cases",
                controller_thread_id="019feebf-3cde-79d2-9f87-ba9c61ff7b13",
                code_branch="codex/test",
                code_commit="abc123",
                contract_digest="contract",
            )
            manifest_path = fixture.scope_dir / "test-cases-review-manifest.json"
            write_json(manifest_path, manifest)
            result_path = fixture.scope_dir / "test-cases-review-result.json"
            write_json(
                result_path,
                {
                    "review_manifest_sha256": sha256_file(manifest_path),
                    "scope_id": "01",
                    "scope_slug": "menu",
                    "review_mode": "test-cases",
                    "execution_surface": "codex-thread",
                    "reviewer_thread_id": "019feebf-3cde-79d2-9f87-ba9c61ff7b14",
                    "independent_obligations": ["OBL-OTHER"],
                    "verdict": "approved",
                    "findings": [],
                },
            )
            _, findings = verify_review_result(
                package_root=fixture.root,
                manifest_path=manifest_path,
                result_path=result_path,
            )
            self.assertIn(
                "review-result-independent-coverage",
                [item.id for item in findings if item.blocking],
            )

    def test_finalizer_records_review_and_allows_accepted_only_after_approval(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            manifest = build_review_manifest(
                package_root=fixture.root,
                workflow_state_path=fixture.state,
                review_mode="test-cases",
                controller_thread_id="019feebf-3cde-79d2-9f87-ba9c61ff7b13",
                code_branch="codex/test",
                code_commit="abc123",
                contract_digest="contract",
            )
            manifest_path = fixture.scope_dir / "test-cases-review-manifest.json"
            write_json(manifest_path, manifest)
            result_path = fixture.scope_dir / "test-cases-review-result.json"
            write_json(
                result_path,
                {
                    "review_manifest_sha256": sha256_file(manifest_path),
                    "scope_id": "01",
                    "scope_slug": "menu",
                    "review_mode": "test-cases",
                    "execution_surface": "codex-thread",
                    "reviewer_thread_id": "019feebf-3cde-79d2-9f87-ba9c61ff7b14",
                    "independent_obligations": ["OBL-001"],
                    "verdict": "approved",
                    "findings": [],
                },
            )
            command = [
                sys.executable,
                str(REPO_ROOT / "scripts" / "finalize_practical_review.py"),
                "--ft-package-root",
                str(fixture.root),
                "--scope-manifest",
                str(fixture.state),
                "--review-manifest",
                str(manifest_path),
                "--review-result",
                str(result_path),
            ]
            completed = subprocess.run(
                command,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            self.assertEqual("accepted", state["phase"])
            self.assertEqual(
                [{
                    "mode": "test-cases",
                    "verdict": "approved",
                    "manifest": "work/practical-v0.9/menu/test-cases-review-manifest.json",
                    "result": "work/practical-v0.9/menu/test-cases-review-result.json",
                }],
                state["reviews"],
            )

    def test_review_contract_rejects_non_durable_thread_identifiers(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            with self.assertRaises(PracticalV09Error):
                build_review_manifest(
                    package_root=fixture.root,
                    workflow_state_path=fixture.state,
                    review_mode="test-cases",
                    controller_thread_id="controller-task",
                    code_branch="codex/test",
                    code_commit="abc123",
                    contract_digest="contract",
                )
