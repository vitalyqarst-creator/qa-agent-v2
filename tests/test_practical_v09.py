from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_case_agent.practical_v09 import (
    ROUTE_VERSION,
    SOURCE_CONTRACT_VERSION,
    PracticalV09Error,
    build_review_manifest,
    build_validator_report,
    finding,
    matrix_review_required,
    sha256_file,
    validate_source_package_manifest,
    validate_scope,
    verify_review_result,
    write_json,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def independently_derived_obligation(obligation_id: str = "OBL-001") -> list[dict[str, object]]:
    return [
        {
            "source_anchor": "Раздел 9.1, строка «Партнеры»",
            "statement": "Пункт меню «Партнеры» доступен пользователю.",
            "obligation_ids": [obligation_id],
        }
    ]


def clarification_card(
    *,
    clarification_id: str = "CLR-001",
    gap_id: str = "GAP-001",
    scope_slug: str = "menu",
    related_obligation_ids: str = "OBL-001",
) -> str:
    fields = {
        "clarification_id": clarification_id,
        "gap_id": gap_id,
        "request_kind": "ba-business-ambiguity",
        "scope_slug": scope_slug,
        "requirement_codes": "-",
        "related_ft_reference": "Раздел 9.1, строка «Партнеры»",
        "related_obligation_ids": related_obligation_ids,
        "source_quote": "Пункт доступен пользователю.",
        "question": "Какое условие доступности применяется?",
        "needed_for": "Полное покрытие требования.",
        "blocking": "no",
        "requested_from": "analyst",
        "authority": "analyst",
        "user_response": "-",
        "response_status": "unanswered",
        "response_type": "not-provided",
        "updated_at": "-",
    }
    yaml_body = "\n".join(
        f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in fields.items()
    )
    return (
        "## Контекст\n\n"
        f"- `scope_slug`: `{scope_slug}`\n\n"
        "## Как Заполнять\n\n"
        "- Заполните только поле `user_response`.\n\n"
        "## Запросы на уточнение\n\n"
        f"### {clarification_id} — {gap_id}\n\n"
        f"```yaml\n{yaml_body}\n```\n\n"
        "## Пробелы без запросов\n\n"
        "- Отсутствуют.\n\n"
        "## Правила Использования Ответов\n\n"
        "- Ответ не заменяет основной ФТ.\n"
    )


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
            "source_contract_version": SOURCE_CONTRACT_VERSION,
            "documents": [
                {"role": "main-docx", "path": "source/main.docx", "sha256": sha256_file(root / "source" / "main.docx")},
                {"role": "main-xhtml", "path": "source/main.xhtml", "sha256": sha256_file(root / "source" / "main.xhtml")},
                {"role": "pdf-cross-check", "path": "source/main.pdf", "sha256": sha256_file(root / "source" / "main.pdf")},
            ],
            "agent_notes": {"path": "AGENT-NOTES.md", "sha256": sha256_file(root / "AGENT-NOTES.md")},
            "support_inputs": [],
            "visual_inputs": [],
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
                "schema_version": 1,
                "route_version": ROUTE_VERSION,
                "scope_id": "01",
                "scope_slug": "menu",
                "phase": "test-cases",
                "next_action": "Провести независимое review тест-кейсов",
                "matrix_review_required": False,
                "contract_versions": {
                    "route": ROUTE_VERSION,
                    "source_package": SOURCE_CONTRACT_VERSION,
                },
                "artifacts": {
                    "source_package_manifest": "work/practical-v0.9/source-package-manifest.json",
                    "scope_obligations": "work/practical-v0.9/menu/scope-obligations.json",
                    "test_design_matrix": "work/practical-v0.9/menu/test-design-matrix.md",
                    "canonical_test_cases": "test-cases/9.1-menu.md",
                    "validator_report": "work/practical-v0.9/menu/validator-report.json",
                },
                "reviews": [],
                "revision_count": 0,
                "final_verdict": "not-finalized",
                "decision_notes": [],
            },
        )
        context, findings = validate_scope(
            package_root=self.root,
            workflow_state_path=self.state,
        )
        write_json(
            self.scope_dir / "validator-report.json",
            build_validator_report(context, findings),
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
                "--workflow-state",
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
            self.assertNotIn("workflow_state", report["content_input_hashes"])
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

    def test_pdf_is_optional_but_bound_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            manifest = json.loads(fixture.source_manifest.read_text(encoding="utf-8"))
            manifest["documents"] = [
                item for item in manifest["documents"] if item["role"] != "pdf-cross-check"
            ]
            write_json(fixture.source_manifest, manifest)
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["source_manifest_sha256"] = sha256_file(fixture.source_manifest)
            write_json(fixture.obligations, obligations)

            _, findings = validate_scope(
                package_root=fixture.root,
                workflow_state_path=fixture.state,
            )
            self.assertNotIn(
                "source-manifest-required-roles",
                [item.id for item in findings if item.blocking],
            )

    def test_source_manifest_cli_creates_a_valid_package_without_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.source_manifest.unlink()
            command = [
                sys.executable,
                str(REPO_ROOT / "scripts" / "create_practical_source_manifest.py"),
                "--ft-package-root",
                str(fixture.root),
                "--docx",
                str(fixture.root / "source" / "main.docx"),
                "--xhtml",
                str(fixture.root / "source" / "main.xhtml"),
                "--output",
                str(fixture.source_manifest),
            ]
            completed = subprocess.run(
                command,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            created = json.loads(fixture.source_manifest.read_text(encoding="utf-8"))
            self.assertEqual(
                {"main-docx", "main-xhtml"},
                {item["role"] for item in created["documents"]},
            )
            self.assertIn("tool_version", created)
            self.assertEqual([], created["visual_inputs"])

    def test_source_manifest_cli_separates_visual_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.source_manifest.unlink()
            support = fixture.root / "support" / "dictionary.md"
            visual = fixture.root / "mockups" / "partner-card.png"
            support.parent.mkdir()
            visual.parent.mkdir()
            support.write_text("dictionary", encoding="utf-8")
            visual.write_bytes(b"png")
            rejected = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "create_practical_source_manifest.py"),
                    "--ft-package-root", str(fixture.root),
                    "--docx", str(fixture.root / "source" / "main.docx"),
                    "--xhtml", str(fixture.root / "source" / "main.xhtml"),
                    "--support", str(visual),
                    "--output", str(fixture.source_manifest),
                ],
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn("must be passed through --visual", rejected.stderr)
            command = [
                sys.executable,
                str(REPO_ROOT / "scripts" / "create_practical_source_manifest.py"),
                "--ft-package-root", str(fixture.root),
                "--docx", str(fixture.root / "source" / "main.docx"),
                "--xhtml", str(fixture.root / "source" / "main.xhtml"),
                "--support", str(support),
                "--visual", str(visual),
                "--output", str(fixture.source_manifest),
            ]
            completed = subprocess.run(
                command, text=True, capture_output=True, encoding="utf-8", errors="replace"
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            created = json.loads(fixture.source_manifest.read_text(encoding="utf-8"))
            self.assertEqual("support", created["support_inputs"][0]["role"])
            self.assertEqual("visual-only", created["visual_inputs"][0]["role"])

    def test_validator_rejects_visual_path_inside_support_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            visual = fixture.root / "mockups" / "partner-card.png"
            visual.parent.mkdir()
            visual.write_bytes(b"png")
            manifest = json.loads(fixture.source_manifest.read_text(encoding="utf-8"))
            manifest["support_inputs"] = [{
                "role": "support",
                "path": "mockups/partner-card.png",
                "sha256": sha256_file(visual),
            }]
            write_json(fixture.source_manifest, manifest)
            findings, _ = validate_source_package_manifest(fixture.source_manifest, fixture.root)
            self.assertIn(
                "source-manifest-visual-input-misclassified",
                [item.id for item in findings],
            )

    def test_scope_source_inspector_uses_title_fallback_without_writing_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "main.xhtml"
            source.write_text(
                "<html><body><h2>Карточка партнера</h2><p>Требование</p></body></html>",
                encoding="utf-8",
            )
            command = [
                sys.executable,
                str(REPO_ROOT / "scripts" / "inspect_practical_scope_sources.py"),
                "--section", "9.3.2",
                "--xhtml", str(source),
                "--fallback-title", "Карточка партнера",
            ]
            completed = subprocess.run(
                command, text=True, capture_output=True, encoding="utf-8", errors="replace"
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            inspected = json.loads(completed.stdout)
            self.assertEqual("xhtml", inspected["sources"][0]["kind"])
            self.assertEqual(1, len(inspected["sources"][0]["matches"]))
            self.assertFalse((root / "work").exists())

    def test_business_gap_requires_linked_clarification_request(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["clarifications"] = [
                {
                    "id": "GAP-001",
                    "gap_type": "ba-business-ambiguity",
                    "source_anchor": "XHTML, раздел 9.1, строка «Партнеры»",
                    "source_statement": "Пункт доступен пользователю.",
                    "description": "Не определено условие доступности.",
                    "impact": "non-blocking",
                    "affected_obligation_ids": ["OBL-001"],
                    "question_to_analyst": "Какое условие доступности применяется?",
                    "requires_business_answer": True,
                    "clarification_id": "CLR-001",
                    "temporary_handling": "Не задавать условие доступа до ответа.",
                    "status": "open",
                }
            ]
            write_json(fixture.obligations, obligations)

            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn(
                "scope-clarification-request-missing",
                [item.id for item in findings if item.blocking],
            )

            (fixture.scope_dir / "scope-clarification-requests.md").write_text(
                clarification_card(),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertNotIn(
                "scope-clarification-request-missing",
                [item.id for item in findings],
            )
            self.assertNotIn(
                "scope-clarification-request-link",
                [item.id for item in findings],
            )

    def test_clarification_card_requires_strict_yaml_and_all_fields(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["clarifications"] = [
                {
                    "id": "GAP-001",
                    "gap_type": "ba-business-ambiguity",
                    "source_anchor": "XHTML, раздел 9.1, строка «Партнеры»",
                    "source_statement": "Пункт доступен пользователю.",
                    "description": "Не определено условие доступности.",
                    "impact": "non-blocking",
                    "affected_obligation_ids": ["OBL-001"],
                    "question_to_analyst": "Какое условие доступности применяется?",
                    "requires_business_answer": True,
                    "clarification_id": "CLR-001",
                    "temporary_handling": "Не задавать условие доступа до ответа.",
                    "status": "open",
                }
            ]
            write_json(fixture.obligations, obligations)
            card_path = fixture.scope_dir / "scope-clarification-requests.md"
            card_path.write_text(clarification_card(), encoding="utf-8")

            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertNotIn("scope-clarification-request-yaml", [item.id for item in findings])
            self.assertNotIn("scope-clarification-request-fields", [item.id for item in findings])

            card_path.write_text(
                clarification_card().replace('requirement_codes: "-"', "requirement_codes: -"),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn(
                "scope-clarification-request-yaml",
                [item.id for item in findings if item.blocking],
            )

            card_path.write_text(
                clarification_card().replace('user_response: "-"\n', ""),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn(
                "scope-clarification-request-fields",
                [item.id for item in findings if item.blocking],
            )

            card_path.write_text(
                clarification_card().replace(
                    "## Запросы на уточнение", "## Clarification Requests"
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn(
                "scope-clarification-request-sections",
                [item.id for item in findings if item.blocking],
            )

    def test_scope_obligation_rejects_known_autofill_aggregation_patterns(self) -> None:
        cases = (
            (
                "Система автоматически заполняет наименование, ИНН и ОГРН.",
                "scope-obligation-autofill-aggregated",
            ),
            (
                "Поле поддерживает автоматическое заполнение и ручной ввод.",
                "scope-obligation-autofill-manual-mixed",
            ),
        )
        for statement, finding_id in cases:
            with self.subTest(statement=statement), tempfile.TemporaryDirectory() as raw:
                fixture = PracticalV09Fixture(Path(raw), obligation_statement=statement)
                _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
                self.assertIn(finding_id, [item.id for item in findings if item.blocking])

    def test_resolved_gap_requires_hash_bound_approved_clarification(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            approved = fixture.root / "support" / "menu-approved-clarifications.md"
            approved.parent.mkdir()
            approved.write_text("# Подтвержденное уточнение\n", encoding="utf-8")
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["clarifications"] = [
                {
                    "id": "GAP-001",
                    "gap_type": "ba-business-ambiguity",
                    "source_anchor": "XHTML, раздел 9.1, строка «Партнеры»",
                    "source_statement": "Пункт доступен пользователю.",
                    "description": "Не определено условие доступности.",
                    "impact": "non-blocking",
                    "affected_obligation_ids": ["OBL-001"],
                    "question_to_analyst": "Какое условие доступности применяется?",
                    "requires_business_answer": True,
                    "clarification_id": "CLR-001",
                    "temporary_handling": "Использовать подтвержденный ответ.",
                    "status": "resolved",
                    "resolution": "approved-clarification:CLR-001",
                    "approved_clarification_path": "support/menu-approved-clarifications.md",
                    "approved_clarification_sha256": sha256_file(approved),
                }
            ]
            write_json(fixture.obligations, obligations)
            (fixture.scope_dir / "scope-clarification-requests.md").write_text(
                clarification_card(),
                encoding="utf-8",
            )

            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertNotIn(
                "scope-clarification-approved-hash",
                [item.id for item in findings],
            )
            self.assertNotIn(
                "scope-clarification-resolution",
                [item.id for item in findings],
            )
            approved.write_text("# Измененный ответ БА\n", encoding="utf-8")
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn(
                "scope-clarification-approved-hash",
                [item.id for item in findings if item.blocking],
            )

    def test_scope_local_approved_clarification_is_not_allowed_in_shared_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            approved = fixture.root / "support" / "menu-approved-clarifications.md"
            approved.parent.mkdir()
            approved.write_text("# Утвержденный ответ БА\n", encoding="utf-8")
            manifest = json.loads(fixture.source_manifest.read_text(encoding="utf-8"))
            manifest["support_inputs"] = [{
                "role": "support",
                "path": "support/menu-approved-clarifications.md",
                "sha256": sha256_file(approved),
            }]
            write_json(fixture.source_manifest, manifest)
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["source_manifest_sha256"] = sha256_file(fixture.source_manifest)
            write_json(fixture.obligations, obligations)
            _, findings = validate_scope(
                package_root=fixture.root,
                workflow_state_path=fixture.state,
            )
            self.assertIn(
                "source-manifest-scope-clarification",
                [item.id for item in findings if item.blocking],
            )

    def test_agent_notes_warn_about_agent_layer_version_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            notes = fixture.root / "AGENT-NOTES.md"
            notes.write_text("# Notes\n\n- Исходный commit: deadbeef\n", encoding="utf-8")
            manifest = json.loads(fixture.source_manifest.read_text(encoding="utf-8"))
            manifest["agent_notes"]["sha256"] = sha256_file(notes)
            write_json(fixture.source_manifest, manifest)
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["source_manifest_sha256"] = sha256_file(fixture.source_manifest)
            write_json(fixture.obligations, obligations)
            _, findings = validate_scope(
                package_root=fixture.root,
                workflow_state_path=fixture.state,
            )
            matching = [
                item for item in findings
                if item.id == "source-manifest-agent-notes-version-metadata"
            ]
            self.assertEqual(1, len(matching))
            self.assertFalse(matching[0].blocking)

    def test_pre_matrix_check_is_not_scoped_route_validation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.state.unlink()
            command = [
                sys.executable,
                str(REPO_ROOT / "scripts" / "validate_practical_obligations.py"),
                "--ft-package-root",
                str(fixture.root),
                "--source-package-manifest",
                str(fixture.source_manifest),
                "--scope-obligations",
                str(fixture.obligations),
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
            payload = json.loads(completed.stdout)
            self.assertEqual("scope-obligations-structure", payload["check_type"])
            self.assertIn("ещё не запускалась", payload["note"])

    def test_v09_scope_contract_requires_ba_and_terminology_handling(self) -> None:
        route = (REPO_ROOT / "references" / "agent" / "practical-test-case-route-v0.9.md").read_text(
            encoding="utf-8"
        )
        scope_format = (REPO_ROOT / "references" / "agent" / "practical-v0.9-scope-obligations-format.md").read_text(
            encoding="utf-8"
        )
        analyzer = (REPO_ROOT / "skills" / "ft-scope-analyzer" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        for content in (route, scope_format, analyzer):
            self.assertIn("scope-clarification-requests.md", content)
            self.assertIn("source-terminology-discrepancy", content)
            self.assertIn("validate_practical_obligations.py", content)
        self.assertIn("practical route v0.9", analyzer)
        self.assertIn("v0.8 instructions below are legacy-only", analyzer)
        self.assertIn("автозаполняет несколько полей", scope_format)
        self.assertIn("Не создавай `CLR-*` только из-за различия заголовка", scope_format)

    def test_style_warning_is_visible_but_not_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw), obligation_statement="Проверить source-backed значение.")
            context, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            report = build_validator_report(context, findings)
            matching = [item for item in report["findings"] if item["id"] == "scope-obligation-process-language"]
            self.assertEqual(1, len(matching))
            self.assertFalse(matching[0]["blocking"])
            self.assertIsNone(matching[0]["blocking_reason"])
            self.assertTrue(report["summary"]["clean"])

    def test_blocking_reason_is_independent_from_severity_and_category(self) -> None:
        default_blocker = finding(
            "source-missing",
            "source-integrity",
            "Источник недоступен",
            "Не найден обязательный источник.",
            "source-package-manifest.json",
        )
        self.assertTrue(default_blocker.blocking)
        self.assertTrue(default_blocker.blocking_reason)

        escalated_warning = finding(
            "format-escalated",
            "format",
            "Нарушен обязательный формат",
            "Локальный контракт требует точный формат.",
            "test-cases.md",
            severity="warning",
            blocking=True,
            blocking_reason="Локальный контракт делает формат блокирующим.",
        )
        self.assertTrue(escalated_warning.blocking)
        self.assertEqual("warning", escalated_warning.severity)
        self.assertEqual(
            "Локальный контракт делает формат блокирующим.",
            escalated_warning.blocking_reason,
        )

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
        required, reasons = matrix_review_required(
            {"obligations": [{"id": "OBL-001", "risk_flags": ["temporal-rule"]}]}
        )
        self.assertTrue(required)
        self.assertIn("temporal-rule", reasons[0])

    def test_unknown_matrix_review_risk_is_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["obligations"][0]["risk_flags"] = ["unrecognized-risk"]
            write_json(fixture.obligations, obligations)
            _, findings = validate_scope(
                package_root=fixture.root,
                workflow_state_path=fixture.state,
            )
            self.assertIn(
                "scope-obligation-risk-flags-unknown",
                [item.id for item in findings if item.blocking],
            )

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
                    "independent_obligations": independently_derived_obligation(),
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

    def test_review_manifest_requires_a_fresh_persisted_validator_report(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.matrix.write_text(
                fixture.matrix.read_text(encoding="utf-8") + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PracticalV09Error, "validator-report.json is stale"):
                build_review_manifest(
                    package_root=fixture.root,
                    workflow_state_path=fixture.state,
                    review_mode="test-cases",
                    controller_thread_id="019feebf-3cde-79d2-9f87-ba9c61ff7b13",
                    code_branch="codex/test",
                    code_commit="abc123",
                    contract_digest="contract",
                )
            context, findings = validate_scope(
                package_root=fixture.root,
                workflow_state_path=fixture.state,
            )
            write_json(
                fixture.scope_dir / "validator-report.json",
                build_validator_report(context, findings),
            )
            manifest = build_review_manifest(
                package_root=fixture.root,
                workflow_state_path=fixture.state,
                review_mode="test-cases",
                controller_thread_id="019feebf-3cde-79d2-9f87-ba9c61ff7b13",
                code_branch="codex/test",
                code_commit="abc123",
                contract_digest="contract",
            )
            self.assertIn("validator_report_sha256", manifest)

    def test_review_result_rejects_readable_json_with_mojibake(self) -> None:
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
                    "independent_obligations": independently_derived_obligation(),
                    "verdict": "approved",
                    "findings": [{"description": "РџСЂРѕРІРµСЂРєР°"}],
                },
            )
            _, findings = verify_review_result(
                package_root=fixture.root,
                manifest_path=manifest_path,
                result_path=result_path,
            )
            self.assertIn("review-result-mojibake", [item.id for item in findings if item.blocking])

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
                    "independent_obligations": independently_derived_obligation("OBL-OTHER"),
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

    def test_reviewer_must_record_source_backed_independent_obligations(self) -> None:
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
            self.assertIn(
                "review-result-independent-obligation-format",
                [item.id for item in findings if item.blocking],
            )

    def test_review_manifest_rejects_changed_tool_contract(self) -> None:
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
            manifest["tool_version"] = "practical-v0.9.0"
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
                    "independent_obligations": independently_derived_obligation(),
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
                "review-manifest-tool-version",
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
                    "independent_obligations": independently_derived_obligation(),
                    "verdict": "approved",
                    "findings": [],
                },
            )
            command = [
                sys.executable,
                str(REPO_ROOT / "scripts" / "finalize_practical_review.py"),
                "--ft-package-root",
                str(fixture.root),
                "--workflow-state",
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
            self.assertEqual("approved", state["final_verdict"])
            self.assertEqual(0, state["revision_count"])
            self.assertEqual(
                [{
                    "mode": "test-cases",
                    "verdict": "approved",
                    "manifest": "work/practical-v0.9/menu/test-cases-review-manifest.json",
                    "result": "work/practical-v0.9/menu/test-cases-review-result.json",
                }],
                state["reviews"],
            )

    def test_changes_required_consumes_the_single_content_revision(self) -> None:
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
                    "independent_obligations": independently_derived_obligation(),
                    "verdict": "changes-required",
                    "findings": [
                        {
                            "id": "RV-001",
                            "blocking": True,
                            "remediation_owner": "writer",
                        }
                    ],
                },
            )
            command = [
                sys.executable,
                str(REPO_ROOT / "scripts" / "finalize_practical_review.py"),
                "--ft-package-root",
                str(fixture.root),
                "--workflow-state",
                str(fixture.state),
                "--review-manifest",
                str(manifest_path),
                "--review-result",
                str(result_path),
            ]
            first = subprocess.run(
                command,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(0, first.returncode, first.stderr)
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            self.assertEqual(1, state["revision_count"])
            self.assertEqual("changes-required", state["final_verdict"])
            self.assertEqual("test-cases", state["phase"])

    def test_nonblocking_execution_status_correction_does_not_consume_revision(self) -> None:
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
                    "independent_obligations": independently_derived_obligation(),
                    "verdict": "changes-required",
                    "findings": [
                        {
                            "id": "RV-STATUS-001",
                            "blocking": False,
                            "remediation_owner": "writer",
                            "description": "Нужно использовать blocked-observability.",
                        }
                    ],
                },
            )
            command = [
                sys.executable,
                str(REPO_ROOT / "scripts" / "finalize_practical_review.py"),
                "--ft-package-root",
                str(fixture.root),
                "--workflow-state",
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
            self.assertEqual(0, state["revision_count"])
            self.assertEqual("test-cases", state["phase"])
            self.assertIn("неблокирующие", state["next_action"])

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
