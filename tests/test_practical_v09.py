from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_case_agent.practical_v09 import (
    MATRIX_CONTRACT_VERSION,
    ROUTE_VERSION,
    SOURCE_CONTRACT_VERSION,
    PracticalV09Error,
    build_review_manifest,
    build_validator_report,
    derived_execution_status,
    finding,
    load_workflow_state,
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


def approved_ba_decision_registry(decision_id: str = "BA-DEC-001") -> str:
    fields = {
        "decision_id": decision_id,
        "status": "approved",
        "authority": "business-analyst",
        "decision_type": "supersedes-ft",
        "applies_to": "Весь FT-пакет; только карточка партнёра.",
        "requirement_refs": "AS.34; таблица 6.",
        "decision": "Поля «Фактический адрес» в карточке партнёра не будет.",
    }
    yaml_body = "\n".join(
        f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in fields.items()
    )
    return f"# Утверждённые решения БА\n\n## {decision_id} — Фактический адрес\n\n```yaml\n{yaml_body}\n```\n"


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
            "approved_ba_decisions": [],
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
                "execution_setups": [
                    {
                        "id": "SETUP-ACTOR-001",
                        "kind": "actor",
                        "availability": "provided",
                        "evidence": "Пользователь с доступом к модулю подготовлен в тестовом контуре.",
                    }
                ],
                "obligations": [
                    {
                        "id": "OBL-001",
                        "source_anchor": "Раздел 9.1, строка «Партнеры»",
                        "statement": obligation_statement,
                        "risk_flags": [],
                        "execution_contexts": [
                            {
                                "id": "CTX-OPEN-MENU",
                                "label": "Открытие раздела из меню",
                                "required_setup_kinds": ["actor"],
                                "setup_ids": ["SETUP-ACTOR-001"],
                            }
                        ],
                    }
                ],
                "clarifications": [],
            },
        )
        self.matrix = self.scope_dir / "test-design-matrix.md"
        self.matrix.write_text(
            "# Матрица тест-дизайна\n\n"
            "| Проверка | Идентификатор сценария | Обязательство ФТ | Контекст исполнения | Проверяемое правило | Исходное состояние | Формирование состояния | Проверяемое действие | Ожидаемый результат | Нужные предпосылки | Тип | Приоритет | Статус исполнения | Планируемый TC-ID |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
            "| MTX-001 | SCN-001 | OBL-001 | CTX-OPEN-MENU — Открытие раздела из меню | Пункт меню «Партнеры» доступен пользователю. | Пользователь вошёл в систему. | Не требуется: состояние задано предусловием. | Открыть пункт меню «Партнеры». | Открывается раздел «Партнеры». | SETUP-ACTOR-001 — пользователь с доступом к модулю. | Positive | High | ready | TC-MENU-001 |\n",
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
            "**Контекст исполнения:** `CTX-OPEN-MENU` — открытие раздела из меню.\n"
            "**Трассировка:** `OBL-001`; `SCN-001`; Раздел 9.1.\n"
            "**Цель:** Проверить открытие раздела «Партнеры».\n"
            "**Предусловия:** Пользователь вошел в систему.\n"
            "**Тестовые данные:** Не требуются.\n"
            "**Шаги:**\n1. Открыть раздел «Партнеры».\n"
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
                "phase": "review",
                "next_action": "Провести независимое final TC review",
                "matrix_review_required": False,
                "contract_versions": {
                    "route": ROUTE_VERSION,
                    "source_package": SOURCE_CONTRACT_VERSION,
                    "matrix": MATRIX_CONTRACT_VERSION,
                },
                "artifacts": {
                    "source_package_manifest": "work/practical-v0.9/source-package-manifest.json",
                    "scope_obligations": "work/practical-v0.9/menu/scope-obligations.json",
                    "test_design_matrix": "work/practical-v0.9/menu/test-design-matrix.md",
                    "canonical_test_cases": "test-cases/9.1-menu.md",
                    "validator_report": "work/practical-v0.9/menu/validator-report.json",
                },
                "reviews": [],
                "matrix_revision_count": 0,
                "tc_revision_count": 0,
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
            self.assertEqual([], created["approved_ba_decisions"])

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

    def test_source_manifest_cli_binds_package_ba_decision_registry(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.source_manifest.unlink()
            registry = fixture.root / "support" / "package-approved-ba-decisions.md"
            registry.parent.mkdir()
            registry.write_text(approved_ba_decision_registry(), encoding="utf-8")

            rejected = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "create_practical_source_manifest.py"),
                    "--ft-package-root", str(fixture.root),
                    "--docx", str(fixture.root / "source" / "main.docx"),
                    "--xhtml", str(fixture.root / "source" / "main.xhtml"),
                    "--support", str(registry),
                    "--output", str(fixture.source_manifest),
                ],
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn("must be passed through --ba-decisions", rejected.stderr)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "create_practical_source_manifest.py"),
                    "--ft-package-root", str(fixture.root),
                    "--docx", str(fixture.root / "source" / "main.docx"),
                    "--xhtml", str(fixture.root / "source" / "main.xhtml"),
                    "--ba-decisions", str(registry),
                    "--output", str(fixture.source_manifest),
                ],
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            findings, created = validate_source_package_manifest(
                fixture.source_manifest, fixture.root
            )
            self.assertEqual([], [item.id for item in findings if item.blocking])
            self.assertEqual(
                "approved-ba-decision-registry",
                created["approved_ba_decisions"][0]["role"],
            )

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

    def test_unresolved_ft_conflict_always_requires_ba_question(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["clarifications"] = [
                {
                    "id": "GAP-001",
                    "gap_type": "ba-decision-required",
                    "source_anchor": "XHTML, AS.34",
                    "source_statement": "Заполняется фактический адрес.",
                    "description": "Ожидаемая практика отменяет поле, но решения БА нет.",
                    "impact": "blocking",
                    "affected_obligation_ids": ["OBL-001"],
                    "question_to_analyst": "Нужно ли исключить поле фактического адреса?",
                    "requires_business_answer": False,
                    "clarification_id": "CLR-001",
                    "temporary_handling": "Не проектировать проверку до решения БА.",
                    "status": "open",
                }
            ]
            write_json(fixture.obligations, obligations)

            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            finding_ids = [item.id for item in findings if item.blocking]
            self.assertIn("scope-ba-decision-request-flag", finding_ids)
            self.assertIn("scope-clarification-request-missing", finding_ids)

            obligations["clarifications"][0]["requires_business_answer"] = True
            write_json(fixture.obligations, obligations)
            (fixture.scope_dir / "scope-clarification-requests.md").write_text(
                clarification_card(), encoding="utf-8"
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            finding_ids = [item.id for item in findings]
            self.assertNotIn("scope-ba-decision-request-flag", finding_ids)
            self.assertNotIn("scope-clarification-request-missing", finding_ids)

    def test_package_ba_decision_supersedes_obligation_and_excludes_it_from_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            registry = fixture.root / "support" / "package-approved-ba-decisions.md"
            registry.parent.mkdir()
            registry.write_text(approved_ba_decision_registry(), encoding="utf-8")
            manifest = json.loads(fixture.source_manifest.read_text(encoding="utf-8"))
            manifest["approved_ba_decisions"] = [{
                "role": "approved-ba-decision-registry",
                "path": "support/package-approved-ba-decisions.md",
                "sha256": sha256_file(registry),
            }]
            write_json(fixture.source_manifest, manifest)

            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["source_manifest_sha256"] = sha256_file(fixture.source_manifest)
            obligations["obligations"][0]["disposition"] = "superseded-by-ba-decision"
            obligations["obligations"][0]["ba_decision_id"] = "BA-DEC-001"
            obligations["clarifications"] = [{
                "id": "GAP-001",
                "gap_type": "ba-decision-supersedes-ft",
                "source_anchor": "XHTML, AS.34",
                "source_statement": "Заполняется фактический адрес.",
                "description": "Утверждённое решение БА отменяет поле.",
                "impact": "non-blocking",
                "affected_obligation_ids": ["OBL-001"],
                "requires_business_answer": False,
                "temporary_handling": "Не проектировать отменённое поле.",
                "status": "resolved",
                "resolution": "approved-ba-decision:BA-DEC-001",
                "ba_decision_id": "BA-DEC-001",
            }]
            write_json(fixture.obligations, obligations)
            fixture.matrix.write_text(
                "# Матрица тест-дизайна\n\n"
                "| Проверка | Идентификатор сценария | Обязательство ФТ | Контекст исполнения | Проверяемое правило | Исходное состояние | Формирование состояния | Проверяемое действие | Ожидаемый результат | Нужные предпосылки | Тип | Приоритет | Статус исполнения | Планируемый TC-ID |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n",
                encoding="utf-8",
            )
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["phase"] = "matrix"
            state["artifacts"].pop("canonical_test_cases")
            write_json(fixture.state, state)

            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertEqual([], [item.id for item in findings if item.blocking])

            fixture.matrix.write_text(
                fixture.matrix.read_text(encoding="utf-8")
                + "| MTX-001 | SCN-001 | OBL-001 | CTX-OPEN-MENU | Проверка поля | Форма открыта. | Не требуется: состояние задано предусловием. | Проверить поле. | Поле доступно. | SETUP-ACTOR-001 | Positive | High | ready | TC-MENU-001 |\n",
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn(
                "matrix-obligation-superseded",
                [item.id for item in findings if item.blocking],
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
            self.assertEqual(0, state["matrix_revision_count"])
            self.assertEqual(0, state["tc_revision_count"])
            self.assertEqual(
                [{
                    "mode": "test-cases",
                    "verdict": "approved",
                    "manifest": "work/practical-v0.9/menu/test-cases-review-manifest.json",
                    "result": "work/practical-v0.9/menu/test-cases-review-result.json",
                }],
                state["reviews"],
            )

    def test_tc_changes_required_consumes_only_tc_revision_budget(self) -> None:
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
            self.assertEqual(0, state["matrix_revision_count"])
            self.assertEqual(1, state["tc_revision_count"])
            self.assertEqual("changes-required", state["final_verdict"])
            self.assertEqual("test-cases", state["phase"])

    def test_matrix_approval_during_contract_migration_requires_tc_sync(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["phase"] = "matrix"
            state["contract_migration"] = {
                "status": "matrix-ready",
                "from_matrix_contract": "practical-matrix-v1",
                "to_matrix_contract": MATRIX_CONTRACT_VERSION,
                "authorization": "explicit-user",
                "snapshot_manifest": "work/practical-v0.9/menu/migration-manifest.json",
                "canonical_tc_sync_required": True,
            }
            write_json(fixture.scope_dir / "migration-manifest.json", {"schema_version": 1})
            write_json(fixture.state, state)
            context, findings = validate_scope(
                package_root=fixture.root, workflow_state_path=fixture.state
            )
            write_json(
                fixture.scope_dir / "validator-report.json",
                build_validator_report(context, findings),
            )
            manifest = build_review_manifest(
                package_root=fixture.root,
                workflow_state_path=fixture.state,
                review_mode="matrix",
                controller_thread_id="019feebf-3cde-79d2-9f87-ba9c61ff7b13",
                code_branch="codex/test",
                code_commit="abc123",
                contract_digest="contract",
            )
            manifest_path = fixture.scope_dir / "matrix-review-manifest.json"
            write_json(manifest_path, manifest)
            result_path = fixture.scope_dir / "matrix-review-result.json"
            write_json(
                result_path,
                {
                    "review_manifest_sha256": sha256_file(manifest_path),
                    "scope_id": "01",
                    "scope_slug": "menu",
                    "review_mode": "matrix",
                    "execution_surface": "codex-thread",
                    "reviewer_thread_id": "019feebf-3cde-79d2-9f87-ba9c61ff7b14",
                    "independent_obligations": independently_derived_obligation(),
                    "verdict": "approved",
                    "findings": [],
                },
            )
            command = [
                sys.executable, str(REPO_ROOT / "scripts" / "finalize_practical_review.py"),
                "--ft-package-root", str(fixture.root),
                "--workflow-state", str(fixture.state),
                "--review-manifest", str(manifest_path),
                "--review-result", str(result_path),
            ]
            completed = subprocess.run(command, text=True, capture_output=True, encoding="utf-8", errors="replace")
            self.assertEqual(0, completed.returncode, completed.stderr)
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            self.assertEqual("matrix-accepted", state["contract_migration"]["status"])
            self.assertEqual("test-cases", state["phase"])
            self.assertIn("Синхронизировать канонические ТК", state["next_action"])

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
            self.assertEqual(0, state["matrix_revision_count"])
            self.assertEqual(0, state["tc_revision_count"])
            self.assertEqual("test-cases", state["phase"])
            self.assertIn("неблокирующие", state["next_action"])

    def test_legacy_matrix_revision_does_not_consume_tc_budget(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            legacy_state = json.loads(fixture.state.read_text(encoding="utf-8"))
            legacy_state.pop("matrix_revision_count")
            legacy_state.pop("tc_revision_count")
            legacy_state["revision_count"] = 1
            legacy_state["reviews"] = [{
                "mode": "matrix",
                "verdict": "changes-required",
                "manifest": "work/practical-v0.9/menu/matrix-review-manifest.json",
                "result": "work/practical-v0.9/menu/matrix-review-result.json",
            }]
            write_json(fixture.state, legacy_state)

            state = load_workflow_state(fixture.state, fixture.root)
            self.assertNotIn("revision_count", state)
            self.assertEqual(1, state["matrix_revision_count"])
            self.assertEqual(0, state["tc_revision_count"])

    def test_legacy_matrix_contract_requires_explicit_migration(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            legacy_matrix = (
                "# Матрица тест-дизайна\n\n"
                "| Проверка | Обязательство ФТ | Контекст исполнения | Проверяемое правило | Ожидаемый результат | Нужные предпосылки | Сценарий | Тип | Приоритет | Статус исполнения | Планируемый TC-ID |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
                "| MTX-001 | OBL-001 | CTX-OPEN-MENU — Открытие раздела из меню | Пункт меню доступен. | Раздел открыт. | SETUP-ACTOR-001. | Открыть раздел. | Positive | High | ready | TC-MENU-001 |\n"
            )
            fixture.matrix.write_text(legacy_matrix, encoding="utf-8")
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["contract_versions"].pop("matrix")
            write_json(fixture.state, state)

            _, findings = validate_scope(
                package_root=fixture.root, workflow_state_path=fixture.state
            )
            self.assertIn(
                "matrix-contract-migration-required",
                [item.id for item in findings if item.blocking],
            )
            self.assertNotIn(
                "matrix-scenario-id", [item.id for item in findings]
            )

    def test_v2_matrix_without_legacy_metadata_is_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["contract_versions"].pop("matrix")
            write_json(fixture.state, state)
            loaded = load_workflow_state(fixture.state, fixture.root)
            self.assertEqual(MATRIX_CONTRACT_VERSION, loaded["contract_versions"]["matrix"])
            _, findings = validate_scope(
                package_root=fixture.root, workflow_state_path=fixture.state
            )
            self.assertNotIn(
                "matrix-contract-migration-required", [item.id for item in findings]
            )

    def test_contract_migration_snapshots_legacy_inputs_without_resetting_budgets(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.matrix.write_text(
                "# Матрица тест-дизайна\n\n"
                "| Проверка | Обязательство ФТ | Контекст исполнения | Проверяемое правило | Ожидаемый результат | Нужные предпосылки | Сценарий | Тип | Приоритет | Статус исполнения | Планируемый TC-ID |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
                "| MTX-001 | OBL-001 | CTX-OPEN-MENU — Открытие раздела из меню | Пункт меню доступен. | Раздел открыт. | SETUP-ACTOR-001. | Открыть раздел. | Positive | High | ready | TC-MENU-001 |\n",
                encoding="utf-8",
            )
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["contract_versions"].pop("matrix")
            state["matrix_revision_count"] = 1
            state["tc_revision_count"] = 1
            write_json(fixture.state, state)
            original_matrix_hash = sha256_file(fixture.matrix)
            snapshot_dir = fixture.scope_dir / "contract-migration-v1-to-v2-snapshot"
            command = [
                sys.executable,
                str(REPO_ROOT / "scripts" / "migrate_practical_matrix_contract.py"),
                "--ft-package-root", str(fixture.root),
                "--workflow-state", str(fixture.state),
                "--action", "start",
                "--snapshot-dir", str(snapshot_dir),
            ]
            denied = subprocess.run(command, text=True, capture_output=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(0, denied.returncode)
            self.assertFalse(snapshot_dir.exists())

            completed = subprocess.run(
                [*command, "--explicit-user-authorization"],
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            migrated = json.loads(fixture.state.read_text(encoding="utf-8"))
            self.assertEqual("matrix-migration", migrated["phase"])
            self.assertEqual(MATRIX_CONTRACT_VERSION, migrated["contract_versions"]["matrix"])
            self.assertEqual("active", migrated["contract_migration"]["status"])
            self.assertEqual(1, migrated["matrix_revision_count"])
            self.assertEqual(1, migrated["tc_revision_count"])
            self.assertTrue((snapshot_dir / "migration-manifest.json").is_file())
            self.assertTrue((snapshot_dir / "test-design-matrix.md").is_file())
            self.assertEqual(original_matrix_hash, sha256_file(fixture.matrix))

            _, findings = validate_scope(
                package_root=fixture.root, workflow_state_path=fixture.state
            )
            self.assertIn("contract-migration-active", [item.id for item in findings if item.blocking])

    def test_contract_migration_marks_matrix_then_tc_sync_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.matrix.write_text(
                "# Матрица тест-дизайна\n\n"
                "| Проверка | Обязательство ФТ | Контекст исполнения | Проверяемое правило | Ожидаемый результат | Нужные предпосылки | Сценарий | Тип | Приоритет | Статус исполнения | Планируемый TC-ID |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
                "| MTX-001 | OBL-001 | CTX-OPEN-MENU — Открытие раздела из меню | Пункт меню доступен. | Раздел открыт. | SETUP-ACTOR-001. | Открыть раздел. | Positive | High | ready | TC-MENU-001 |\n",
                encoding="utf-8",
            )
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["contract_versions"].pop("matrix")
            write_json(fixture.state, state)
            migration_script = str(REPO_ROOT / "scripts" / "migrate_practical_matrix_contract.py")
            snapshot_dir = fixture.scope_dir / "contract-migration-v1-to-v2-snapshot"
            started = subprocess.run(
                [
                    sys.executable, migration_script,
                    "--ft-package-root", str(fixture.root),
                    "--workflow-state", str(fixture.state),
                    "--action", "start", "--snapshot-dir", str(snapshot_dir),
                    "--explicit-user-authorization",
                ],
                text=True, capture_output=True, encoding="utf-8", errors="replace",
            )
            self.assertEqual(0, started.returncode, started.stderr)
            # Restore a valid v2 table without touching the preserved TC.
            fixture.matrix.write_text(
                "# Матрица тест-дизайна\n\n"
                "| Проверка | Идентификатор сценария | Обязательство ФТ | Контекст исполнения | Проверяемое правило | Исходное состояние | Формирование состояния | Проверяемое действие | Ожидаемый результат | Нужные предпосылки | Тип | Приоритет | Статус исполнения | Планируемый TC-ID |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
                "| MTX-001 | SCN-001 | OBL-001 | CTX-OPEN-MENU — Открытие раздела из меню | Пункт меню доступен. | Пользователь вошёл. | Не требуется: состояние задано предусловием. | Открыть раздел. | Раздел открыт. | SETUP-ACTOR-001. | Positive | High | ready | TC-MENU-001 |\n",
                encoding="utf-8",
            )
            ready = subprocess.run(
                [
                    sys.executable, migration_script,
                    "--ft-package-root", str(fixture.root),
                    "--workflow-state", str(fixture.state),
                    "--action", "mark-matrix-ready",
                ],
                text=True, capture_output=True, encoding="utf-8", errors="replace",
            )
            self.assertEqual(0, ready.returncode, ready.stderr)
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            self.assertEqual("matrix-ready", state["contract_migration"]["status"])
            self.assertEqual("matrix", state["phase"])

            state["contract_migration"]["status"] = "matrix-accepted"
            state["phase"] = "test-cases"
            write_json(fixture.state, state)
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn("contract-migration-tc-sync-required", [item.id for item in findings if item.blocking])

            completed = subprocess.run(
                [
                    sys.executable, migration_script,
                    "--ft-package-root", str(fixture.root),
                    "--workflow-state", str(fixture.state),
                    "--action", "complete-tc-sync",
                ],
                text=True, capture_output=True, encoding="utf-8", errors="replace",
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            self.assertEqual("completed", state["contract_migration"]["status"])
            self.assertFalse(state["contract_migration"]["canonical_tc_sync_required"])
            self.assertEqual("review", state["phase"])
            self.assertEqual("not-finalized", state["final_verdict"])
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertNotIn(
                "contract-migration-tc-sync-required",
                [item.id for item in findings if item.blocking],
            )

            # A scope completed by the previous implementation can be repaired
            # by rerunning the same explicit transition, not by editing state.
            state["contract_migration"]["canonical_tc_sync_required"] = True
            write_json(fixture.state, state)
            repaired = subprocess.run(
                [
                    sys.executable, migration_script,
                    "--ft-package-root", str(fixture.root),
                    "--workflow-state", str(fixture.state),
                    "--action", "complete-tc-sync",
                ],
                text=True, capture_output=True, encoding="utf-8", errors="replace",
            )
            self.assertEqual(0, repaired.returncode, repaired.stderr)
            repaired_state = json.loads(fixture.state.read_text(encoding="utf-8"))
            self.assertFalse(repaired_state["contract_migration"]["canonical_tc_sync_required"])

    def test_second_tc_content_review_blocks_only_tc_phase(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["matrix_revision_count"] = 1
            write_json(fixture.state, state)
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
                    "findings": [{"id": "RV-001", "blocking": True, "remediation_owner": "writer"}],
                },
            )
            command = [
                sys.executable,
                str(REPO_ROOT / "scripts" / "finalize_practical_review.py"),
                "--ft-package-root", str(fixture.root),
                "--workflow-state", str(fixture.state),
                "--review-manifest", str(manifest_path),
                "--review-result", str(result_path),
            ]
            first = subprocess.run(command, text=True, capture_output=True, encoding="utf-8", errors="replace")
            self.assertEqual(0, first.returncode, first.stderr)
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            self.assertEqual(1, state["matrix_revision_count"])
            self.assertEqual(1, state["tc_revision_count"])
            self.assertEqual("test-cases", state["phase"])

            second = subprocess.run(command, text=True, capture_output=True, encoding="utf-8", errors="replace")
            self.assertEqual(0, second.returncode, second.stderr)
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            self.assertEqual("blocked", state["phase"])
            self.assertEqual(1, state["matrix_revision_count"])
            self.assertEqual(1, state["tc_revision_count"])

    def test_validator_rejects_test_data_that_restate_rule(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "**Тестовые данные:** Не требуются.",
                    "**Тестовые данные:** Данные, предусмотренные проверяемым правилом: раздел доступен.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn("test-case-test-data-tautology", [item.id for item in findings if item.blocking])

    def test_validator_requires_separate_first_file_upload_for_cardinality(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            broken = fixture.tc.read_text(encoding="utf-8")
            broken = broken.replace("Открытие раздела «Партнеры»", "В поле можно прикрепить не более одного файла")
            broken = broken.replace(
                "**Шаги:**\n1. Открыть раздел «Партнеры».",
                "**Шаги:**\n1. Открыть форму.\n2. Попытаться прикрепить второй допустимый файл.",
            )
            fixture.tc.write_text(broken, encoding="utf-8")
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn("test-case-upload-cardinality-trigger", [item.id for item in findings if item.blocking])

            fixed = broken.replace(
                "1. Открыть форму.\n2. Попытаться прикрепить второй допустимый файл.",
                "1. Открыть форму.\n2. Прикрепить первый допустимый файл.\n3. Попытаться прикрепить второй допустимый файл.",
            )
            fixture.tc.write_text(fixed, encoding="utf-8")
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertNotIn("test-case-upload-cardinality-trigger", [item.id for item in findings if item.blocking])

            without_ordinals = fixed.replace(
                "Прикрепить первый допустимый файл.",
                "Прикрепить файл `решение-1.pdf`.",
            ).replace(
                "Попытаться прикрепить второй допустимый файл.",
                "Попытаться прикрепить файл `решение-2.pdf`.",
            )
            fixture.tc.write_text(without_ordinals, encoding="utf-8")
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertNotIn("test-case-upload-cardinality-trigger", [item.id for item in findings if item.blocking])

    def test_matrix_allows_independent_boundary_scenarios_for_one_obligation_context(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.matrix.write_text(
                fixture.matrix.read_text(encoding="utf-8")
                + "| MTX-002 | SCN-002 | OBL-001 | CTX-OPEN-MENU — Открытие раздела из меню | Пункт меню «Партнеры» доступен пользователю. | Пользователь вошёл в систему. | Не требуется: состояние задано предусловием. | Открыть пункт меню «Партнеры» с граничным значением. | Открывается раздел «Партнеры» для граничного значения. | SETUP-ACTOR-001 — пользователь с доступом к модулю. | Positive | High | ready | TC-MENU-002 |\n",
                encoding="utf-8",
            )
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8")
                + "\n## TC-MENU-002\n"
                "**Название:** Открытие раздела «Партнеры» с граничным значением\n"
                "**Тип:** Positive\n"
                "**Приоритет:** High\n"
                "**Статус исполнения:** ready\n"
                "**Контекст исполнения:** `CTX-OPEN-MENU` — открытие раздела из меню.\n"
                "**Трассировка:** `OBL-001`; `SCN-002`; Раздел 9.1.\n"
                "**Цель:** Проверить открытие раздела с граничным значением.\n"
                "**Предусловия:** Пользователь вошел в систему.\n"
                "**Тестовые данные:** Граничное значение из предусловий.\n"
                "**Шаги:**\n1. Открыть раздел «Партнеры» с граничным значением.\n"
                "**Итоговый ожидаемый результат:** Открывается раздел «Партнеры» для граничного значения.\n",
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            finding_ids = [item.id for item in findings if item.blocking]
            self.assertNotIn("matrix-obligation-context-duplicated", finding_ids)
            self.assertNotIn("test-case-scenario-uncovered", finding_ids)
            self.assertNotIn("test-case-scenario-duplicated", finding_ids)

    def test_validator_requires_source_message_literal_in_matrix_and_tc(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(
                Path(raw),
                obligation_statement=(
                    "При ошибке система выводит текст «Документ не загружен: формат не поддерживается»."
                ),
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            finding_ids = [item.id for item in findings if item.blocking]
            self.assertIn("matrix-source-message-literal", finding_ids)
            self.assertIn("test-case-source-message-literal", finding_ids)

            literal = "Документ не загружен: формат не поддерживается"
            fixture.matrix.write_text(
                fixture.matrix.read_text(encoding="utf-8").replace(
                    "Открывается раздел «Партнеры».",
                    f"Отображается текст «{literal}».",
                ),
                encoding="utf-8",
            )
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "Открывается раздел «Партнеры».",
                    f"Отображается текст «{literal}».",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            finding_ids = [item.id for item in findings if item.blocking]
            self.assertNotIn("matrix-source-message-literal", finding_ids)
            self.assertNotIn("test-case-source-message-literal", finding_ids)

    def test_validator_requires_state_formation_and_follow_up_observation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(
                Path(raw),
                obligation_statement="При нажатии «Отменить» система не сохраняет данные.",
            )
            fixture.matrix.write_text(
                fixture.matrix.read_text(encoding="utf-8").replace(
                    "Не требуется: состояние задано предусловием.",
                    "Внести несохранённое изменение в поле «Наименование».",
                ).replace(
                    "Открыть пункт меню «Партнеры».",
                    "Нажать «Отменить».",
                ),
                encoding="utf-8",
            )
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "1. Открыть раздел «Партнеры».",
                    "1. Нажать «Отменить».",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            finding_ids = [item.id for item in findings if item.blocking]
            self.assertIn("test-case-state-formation-step", finding_ids)
            self.assertIn("test-case-no-save-observation", finding_ids)

            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "1. Нажать «Отменить».",
                    "1. Внести несохранённое изменение в поле «Наименование».\n"
                    "2. Нажать «Отменить».\n"
                    "3. Повторно открыть карточку и проверить отсутствие изменения.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            finding_ids = [item.id for item in findings if item.blocking]
            self.assertNotIn("test-case-state-formation-step", finding_ids)
            self.assertNotIn("test-case-no-save-observation", finding_ids)

    def test_validator_requires_search_and_duplicate_trigger_steps(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(
                Path(raw),
                obligation_statement=(
                    "При выборе организации из DaData система автоматически заполняет наименование."
                ),
            )
            fixture.matrix.write_text(
                fixture.matrix.read_text(encoding="utf-8").replace(
                    "Не требуется: состояние задано предусловием.",
                    "Ввести поисковый запрос для получения подсказки DaData.",
                ).replace(
                    "Открыть пункт меню «Партнеры».",
                    "Выбрать подсказку DaData.",
                ),
                encoding="utf-8",
            )
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "1. Открыть раздел «Партнеры».",
                    "1. Выбрать подсказку DaData.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn("test-case-autocomplete-trigger", [item.id for item in findings if item.blocking])

            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "1. Выбрать подсказку DaData.",
                    "1. Ввести поисковый запрос DaData.\n2. Выбрать подсказку DaData.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertNotIn("test-case-autocomplete-trigger", [item.id for item in findings if item.blocking])

            fixture = PracticalV09Fixture(
                Path(raw) / "duplicate",
                obligation_statement=(
                    "При сохранении система проверяет, что нет двух одинаковых названий партнеров."
                ),
            )
            fixture.matrix.write_text(
                fixture.matrix.read_text(encoding="utf-8").replace(
                    "Не требуется: состояние задано предусловием.",
                    "Ввести наименование существующего партнера.",
                ).replace(
                    "Открыть пункт меню «Партнеры».",
                    "Нажать «Сохранить».",
                ),
                encoding="utf-8",
            )
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "1. Открыть раздел «Партнеры».",
                    "1. Нажать «Сохранить».",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn("test-case-duplicate-trigger", [item.id for item in findings if item.blocking])

            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "1. Нажать «Сохранить».",
                    "1. Ввести наименование существующего партнера.\n2. Нажать «Сохранить».",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertNotIn("test-case-duplicate-trigger", [item.id for item in findings if item.blocking])

    def test_validator_requires_empty_value_before_required_field_validation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(
                Path(raw),
                obligation_statement="Поле «Наименование» обязательно для заполнения.",
            )
            fixture.matrix.write_text(
                fixture.matrix.read_text(encoding="utf-8").replace(
                    "Не требуется: состояние задано предусловием.",
                    "Оставить поле «Наименование» пустым.",
                ).replace(
                    "Открыть пункт меню «Партнеры».",
                    "Нажать «Сохранить».",
                ).replace(
                    "Открывается раздел «Партнеры».",
                    "Карточка не сохраняется, поле подсвечено ошибкой.",
                ),
                encoding="utf-8",
            )
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "1. Открыть раздел «Партнеры».",
                    "1. Нажать «Сохранить».",
                ).replace(
                    "Открывается раздел «Партнеры».",
                    "Карточка не сохраняется, поле подсвечено ошибкой.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn("test-case-required-empty-trigger", [item.id for item in findings if item.blocking])

            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "1. Нажать «Сохранить».",
                    "1. Оставить поле «Наименование» пустым.\n2. Нажать «Сохранить».",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertNotIn("test-case-required-empty-trigger", [item.id for item in findings if item.blocking])

    def test_validator_marks_source_only_internal_check_as_blocked_observability(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(
                Path(raw),
                obligation_statement="При нажатии «Сохранить» система проверяет соответствие внутреннему правилу.",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn("matrix-internal-oracle-status", [item.id for item in findings if item.blocking])

    def test_internal_unobservable_status_precedes_missing_setup_data(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(
                Path(raw),
                obligation_statement="При нажатии «Сохранить» система проверяет соответствие внутреннему правилу.",
            )
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["execution_setups"].append(
                {
                    "id": "SETUP-FIXTURE-001",
                    "kind": "fixture",
                    "availability": "needs-test-data",
                    "evidence": "Подходящий объект для проверки ещё не подготовлен.",
                }
            )
            context = obligations["obligations"][0]["execution_contexts"][0]
            context["required_setup_kinds"] = ["actor", "fixture"]
            context["setup_ids"] = ["SETUP-ACTOR-001", "SETUP-FIXTURE-001"]
            write_json(fixture.obligations, obligations)
            fixture.matrix.write_text(
                fixture.matrix.read_text(encoding="utf-8").replace(
                    "Открывается раздел «Партнеры». | SETUP-ACTOR-001 — пользователь с доступом к модулю. | Positive | High | ready",
                    "Источник не задаёт наблюдаемый результат внутренней проверки. | "
                    "SETUP-ACTOR-001 — пользователь с доступом к модулю; "
                    "SETUP-FIXTURE-001 — объект для проверки не подготовлен. | "
                    "Positive | High | blocked-observability",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            blocking_ids = [item.id for item in findings if item.blocking]
            self.assertNotIn("matrix-internal-oracle-status", blocking_ids)
            self.assertNotIn("matrix-internal-oracle-justification", blocking_ids)
            self.assertNotIn("matrix-execution-status-prerequisites", blocking_ids)

    def test_internal_unobservable_status_requires_explicit_matrix_justification(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(
                Path(raw),
                obligation_statement="При нажатии «Сохранить» система проверяет соответствие внутреннему правилу.",
            )
            fixture.matrix.write_text(
                fixture.matrix.read_text(encoding="utf-8").replace(
                    "| Positive | High | ready |",
                    "| Positive | High | blocked-observability |",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            blocking_ids = [item.id for item in findings if item.blocking]
            self.assertNotIn("matrix-internal-oracle-status", blocking_ids)
            self.assertIn("matrix-internal-oracle-justification", blocking_ids)

    def test_observable_check_with_missing_setup_data_stays_needs_test_data(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["execution_setups"].append(
                {
                    "id": "SETUP-FIXTURE-001",
                    "kind": "fixture",
                    "availability": "needs-test-data",
                    "evidence": "Подходящий объект для проверки ещё не подготовлен.",
                }
            )
            context = obligations["obligations"][0]["execution_contexts"][0]
            context["required_setup_kinds"] = ["actor", "fixture"]
            context["setup_ids"] = ["SETUP-ACTOR-001", "SETUP-FIXTURE-001"]
            write_json(fixture.obligations, obligations)
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            prerequisite_finding = next(
                item for item in findings if item.id == "matrix-execution-status-prerequisites"
            )
            self.assertIn("ожидается needs-test-data", prerequisite_finding.details)

    def test_validator_marks_test_case_writing_phase_stale_after_tc_exists(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["phase"] = "test-cases"
            state["next_action"] = "Написать тест-кейсы"
            write_json(fixture.state, state)
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn("workflow-phase-stale-after-tc-write", [item.id for item in findings])

    def test_legacy_matrix_verdict_is_not_projected_as_final_tc_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["final_verdict"] = "changes-required"
            state["reviews"] = [{
                "mode": "matrix",
                "verdict": "changes-required",
                "manifest": "work/practical-v0.9/menu/matrix-review-manifest.json",
                "result": "work/practical-v0.9/menu/matrix-review-result.json",
            }]
            write_json(fixture.state, state)
            normalized = load_workflow_state(fixture.state, fixture.root)
            self.assertEqual("not-finalized", normalized["final_verdict"])

    def test_matrix_approval_resets_final_tc_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["phase"] = "matrix"
            state["final_verdict"] = "changes-required"
            write_json(fixture.state, state)
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
                review_mode="matrix",
                controller_thread_id="019feebf-3cde-79d2-9f87-ba9c61ff7b13",
                code_branch="codex/test",
                code_commit="abc123",
                contract_digest="contract",
            )
            manifest_path = fixture.scope_dir / "matrix-review-manifest.json"
            write_json(manifest_path, manifest)
            result_path = fixture.scope_dir / "matrix-review-result.json"
            write_json(
                result_path,
                {
                    "review_manifest_sha256": sha256_file(manifest_path),
                    "scope_id": "01",
                    "scope_slug": "menu",
                    "review_mode": "matrix",
                    "execution_surface": "codex-thread",
                    "reviewer_thread_id": "019feebf-3cde-79d2-9f87-ba9c61ff7b14",
                    "independent_obligations": independently_derived_obligation(),
                    "verdict": "approved",
                    "findings": [],
                },
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "finalize_practical_review.py"),
                    "--ft-package-root", str(fixture.root),
                    "--workflow-state", str(fixture.state),
                    "--review-manifest", str(manifest_path),
                    "--review-result", str(result_path),
                ],
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            self.assertEqual("test-cases", state["phase"])
            self.assertEqual("not-finalized", state["final_verdict"])
            self.assertEqual("Написать тест-кейсы", state["next_action"])

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

    def test_matrix_requires_a_separate_row_for_each_execution_context(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["obligations"][0]["execution_contexts"].append(
                {
                    "id": "CTX-EDIT-MENU",
                    "label": "Повторное открытие после изменения прав",
                    "required_setup_kinds": ["actor"],
                    "setup_ids": ["SETUP-ACTOR-001"],
                }
            )
            write_json(fixture.obligations, obligations)
            _, findings = validate_scope(
                package_root=fixture.root,
                workflow_state_path=fixture.state,
            )
            self.assertIn(
                "matrix-obligation-context-unmapped",
                [item.id for item in findings if item.blocking],
            )

    def test_matrix_status_is_derived_from_context_prerequisites(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["execution_setups"][0]["availability"] = "needs-test-data"
            write_json(fixture.obligations, obligations)
            _, findings = validate_scope(
                package_root=fixture.root,
                workflow_state_path=fixture.state,
            )
            self.assertIn(
                "matrix-execution-status-prerequisites",
                [item.id for item in findings if item.blocking],
            )

    def test_execution_status_precedence_covers_every_pair_of_setup_availability(self) -> None:
        statuses = (
            "needs-future-clarification",
            "blocked-observability",
            "needs-test-data",
            "candidate-ui-calibration",
        )
        availability_values = ("provided", *statuses)
        for first in availability_values:
            for second in availability_values:
                with self.subTest(first=first, second=second):
                    setup_catalog = {
                        "SETUP-ACTOR-001": {"kind": "actor", "availability": first},
                        "SETUP-FIXTURE-001": {"kind": "fixture", "availability": second},
                    }
                    expected = next(
                        (status for status in statuses if status in {first, second}),
                        "ready",
                    )
                    self.assertEqual(
                        expected,
                        derived_execution_status(
                            {
                                "required_setup_kinds": ["actor", "fixture"],
                                "setup_ids": ["SETUP-ACTOR-001", "SETUP-FIXTURE-001"],
                            },
                            setup_catalog,
                        ),
                    )

    def test_matrix_status_does_not_mask_missing_data_with_ui_calibration(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["execution_setups"][0]["availability"] = "needs-test-data"
            obligations["execution_setups"].append(
                {
                    "id": "SETUP-NAVIGATION-001",
                    "kind": "navigation",
                    "availability": "candidate-ui-calibration",
                    "evidence": "Точный UI-контрол требует калибровки.",
                }
            )
            context = obligations["obligations"][0]["execution_contexts"][0]
            context["required_setup_kinds"] = ["actor", "navigation"]
            context["setup_ids"] = ["SETUP-ACTOR-001", "SETUP-NAVIGATION-001"]
            write_json(fixture.obligations, obligations)
            fixture.matrix.write_text(
                fixture.matrix.read_text(encoding="utf-8").replace(
                    "SETUP-ACTOR-001 — пользователь с доступом к модулю. | Открытие пункта меню | Positive | High | ready",
                    "SETUP-ACTOR-001 — пользователь с доступом к модулю; "
                    "SETUP-NAVIGATION-001 — UI-контрол требует калибровки | "
                    "Открытие пункта меню | Positive | High | candidate-ui-calibration",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(
                package_root=fixture.root,
                workflow_state_path=fixture.state,
            )
            self.assertIn(
                "matrix-execution-status-prerequisites",
                [item.id for item in findings if item.blocking],
            )

    def test_review_result_allows_legitimate_russian_source_anchor(self) -> None:
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
                    "independent_obligations": [
                        {
                            "source_anchor": "Таблица 8, столбец Р",
                            "statement": "Реквизит доступен для редактирования.",
                            "obligation_ids": ["OBL-001"],
                        }
                    ],
                    "verdict": "approved",
                    "findings": [],
                },
            )
            _, findings = verify_review_result(
                package_root=fixture.root,
                manifest_path=manifest_path,
                result_path=result_path,
            )
            self.assertNotIn("review-result-mojibake", [item.id for item in findings])
