from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_case_agent.practical_v09 import (
    COMPACT_REVIEWER_RECEIPT_FORMAT,
    COMPACT_REVIEWER_RECEIPT_MAX_BYTES,
    CLARIFICATION_OUTCOME_CONTRACT_VERSION,
    CONTROLLER_TRIAGE_CONTRACT_VERSION,
    EXECUTION_CONTEXT_CONTRACT_VERSION,
    EXCEPTION_SNAPSHOT_CONTRACT_VERSION,
    MATRIX_CONTRACT_VERSION,
    LEGACY_SCENARIO_CONSOLIDATION_CONTRACT_VERSION,
    LEGACY_CONTROLLER_TRIAGE_CONTRACT_VERSION,
    PREVIOUS_MATRIX_CONTRACT_VERSION,
    ROUTE_VERSION,
    SCENARIO_CONSOLIDATION_CONTRACT_VERSION,
    SOURCE_PARITY_CONTRACT_VERSION,
    SOURCE_CONTRACT_VERSION,
    PracticalV09Error,
    build_review_manifest,
    build_review_session_attestation,
    build_initial_workflow_state,
    build_validator_report,
    composite_field_mentions,
    derived_execution_status,
    dictionary_inventory_required,
    finding,
    load_workflow_state,
    has_composite_result_table,
    matrix_review_required,
    matrix_exact_duplicate_groups,
    matrix_semantic_consolidation_groups,
    parse_test_case_blocks,
    parse_matrix_consolidation_decisions,
    parse_matrix_rows,
    scenario_consolidation_contract,
    successful_create_has_cleanup,
    successful_create_has_initial_absence,
    successful_create_object_key,
    obligation_ids_sha256,
    requirement_codes,
    relative_to_package,
    review_content_findings,
    render_scope_clarification_requests,
    sha256_file,
    validate_source_package_manifest,
    validate_scope_obligations,
    validate_matrix_file_state_contract,
    validate_matrix_state_and_primary_oracle_contract,
    validate_scope,
    verify_review_result,
    write_json,
)
from test_case_agent.practical_review_input_snapshot import create_snapshot
from scripts.practical_snapshot_preflight import create_snapshot as create_pre_write_snapshot


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
        "## Заполнение ответа\n\n"
        "- Заполните поле «Ответ БА» (`user_response`).\n\n"
        "## Запросы на уточнение\n\n"
        f"### {clarification_id} — {gap_id}\n\n"
        f"```yaml\n{yaml_body}\n```\n\n"
        "## Пробелы без запросов\n\n"
        "- Отсутствуют.\n\n"
        "## Правила использования ответов\n\n"
        "- Ответ не заменяет основной ФТ.\n"
    )


def approved_ba_decision_registry(
    decision_id: str = "BA-DEC-001", *, decision_type: str = "supersedes-ft"
) -> str:
    fields = {
        "decision_id": decision_id,
        "status": "approved",
        "authority": "business-analyst",
        "decision_type": decision_type,
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
                                "flow_kind": "view",
                                "required_setup_kinds": ["actor"],
                                "setup_ids": ["SETUP-ACTOR-001"],
                            }
                        ],
                    }
                ],
                "clarifications": [],
            },
        )
        (self.scope_dir / "scope-clarification-requests.md").write_text(
            render_scope_clarification_requests(
                json.loads(self.obligations.read_text(encoding="utf-8"))
            ),
            encoding="utf-8",
        )
        self.matrix = self.scope_dir / "test-design-matrix.md"
        self.matrix.write_text(
            "# Матрица тест-дизайна\n\n"
            "| Проверка | Идентификатор сценария | Обязательство ФТ | Контекст исполнения | Проверяемый элемент | Домен проверки | Способ взаимодействия | Проверяемое правило | Исходное состояние | Формирование состояния | Проверяемое действие | Ожидаемый результат | Нужные предпосылки | Тип | Приоритет | Статус исполнения | Планируемый TC-ID |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
            "| MTX-001 | SCN-001 | OBL-001 | CTX-OPEN-MENU — Открытие раздела из меню | Пункт меню «Партнеры» | Доступность пункта меню | Нажатие пункта меню | Пункт меню «Партнеры» доступен пользователю. | Пользователь вошёл в систему. | Не требуется: состояние задано предусловием. | Открыть пункт меню «Партнеры». | Открывается раздел «Партнеры». | SETUP-ACTOR-001 — пользователь с доступом к модулю. | Positive | High | ready | TC-MENU-001 |\n",
            encoding="utf-8",
        )
        self.tc = root / "test-cases" / "9.1-menu.md"
        self.tc.parent.mkdir()
        self.tc.write_text(
            "## TC-MENU-001\n"
            "**Номер в разделе:** 1 из 1\n"
            "**Название:** Открытие раздела «Партнеры»\n"
            "**Тип:** Positive\n"
            "**Приоритет:** High\n"
            "**package_id:** WP-01\n"
            "**Статус исполнения:** ready\n"
            "**Контекст исполнения:** `CTX-OPEN-MENU` — открытие раздела из меню.\n"
            "**Трассировка:** `OBL-001`; `SCN-001`; Раздел 9.1.\n"
            "**Цель:** Проверить открытие раздела «Партнеры».\n"
            "**Предусловия:** Пользователь вошел в систему.\n"
            "**Тестовые данные:** Не требуются.\n"
            "**Шаги:**\n1. Открыть раздел «Партнеры».\n"
            "**Итоговый ожидаемый результат:** Открывается раздел «Партнеры».\n"
            "**Постусловия:** Не требуются.\n",
            encoding="utf-8",
        )
        self.state = self.scope_dir / "workflow-state.json"
        self.source_parity = self.scope_dir / "source-parity-check.md"
        self.source_parity.write_text(
            "## Сверка источников\n\n- DOCX/PDF: совпадает.\n\n## Решение\n\n- Расхождений нет.\n",
            encoding="utf-8",
        )
        write_json(
            self.state,
            {
                "schema_version": 1,
                "route_version": ROUTE_VERSION,
                "scope_id": "01",
                "scope_slug": "menu",
                "phase": "review",
                "next_action": "Провести независимое final TC review",
                "matrix_review_required": True,
                "contract_versions": {
                    "route": ROUTE_VERSION,
                    "source_package": SOURCE_CONTRACT_VERSION,
                    "matrix": MATRIX_CONTRACT_VERSION,
                    "source_parity": SOURCE_PARITY_CONTRACT_VERSION,
                    "exception_snapshot": EXCEPTION_SNAPSHOT_CONTRACT_VERSION,
                },
                "artifacts": {
                    "source_package_manifest": "work/practical-v0.9/source-package-manifest.json",
                    "scope_obligations": "work/practical-v0.9/menu/scope-obligations.json",
                    "test_design_matrix": "work/practical-v0.9/menu/test-design-matrix.md",
                    "canonical_test_cases": "test-cases/9.1-menu.md",
                    "validator_report": "work/practical-v0.9/menu/validator-report.json",
                    "source_parity_check": "work/practical-v0.9/menu/source-parity-check.md",
                },
                "reviews": [{"mode": "matrix", "verdict": "approved"}],
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

    def write_verified_dadata_fixture(self, fixture_id: str = "FX-DADATA-PARTNER-001") -> None:
        fixture_dir = self.scope_dir / "fixtures" / fixture_id
        fixture_dir.mkdir(parents=True)
        snapshot = {
            "suggestions": [
                {
                    "value": "ПАО СБЕРБАНК",
                    "data": {
                        "inn": "7707083893",
                        "kpp": "773601001",
                    },
                }
            ]
        }
        snapshot_path = fixture_dir / f"{fixture_id}.response.json"
        write_json(snapshot_path, snapshot)
        write_json(
            fixture_dir / f"{fixture_id}.verification.json",
            {
                "fixture_id": fixture_id,
                "provider": "DaData",
                "status": "verified",
                "request": {"parameters": {"query": "7707083893"}},
                "expected_response": {
                    "exact_suggestion": "ПАО СБЕРБАНК",
                    "exact_components": {
                        "inn": "7707083893",
                        "kpp": "773601001",
                    },
                },
                "response_snapshot": snapshot_path.name,
                "response_sha256": sha256_file(snapshot_path),
            },
        )


class PracticalV09Tests(unittest.TestCase):
    def test_writer_skill_routes_new_practical_work_to_v09(self) -> None:
        writer = (REPO_ROOT / "skills" / "ft-test-case-writer" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("# FT Test Case Writer", writer)
        self.assertIn("[ft-practical-route]", writer)
        self.assertIn("`workflow-state.json`", writer)
        self.assertIn("source-to-matrix scan", writer)
        self.assertNotIn("practical_v0_8", writer)

    def test_reviewer_skill_requires_bounded_review_pass(self) -> None:
        reviewer = (REPO_ROOT / "skills" / "ft-test-case-reviewer" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("одним проходом", reviewer)
        self.assertIn("raw JSON verdict", reviewer)
        self.assertIn("remediation_closure", reviewer)

    def test_runtime_format_allows_grouped_cases_with_global_numbering(self) -> None:
        runtime_format = (
            REPO_ROOT / "references" / "qa" / "test-case-runtime-format.md"
        ).read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "cases.md"
            path.write_text(
                "## Интеграция\n\n"
                "### TC-TEST-001\n**Номер в разделе:** 1 из 2\n\n"
                "## Сохранение\n\n"
                "### TC-TEST-002\n**Номер в разделе:** 2 из 2\n",
                encoding="utf-8",
            )
            blocks = parse_test_case_blocks(path)

        self.assertEqual(["TC-TEST-001", "TC-TEST-002"], [item["id"] for item in blocks])
        self.assertIn("### TC-*", runtime_format)
        self.assertIn("Сквозной номер", runtime_format)

    def test_composite_wording_rejects_a_partial_field_list(self) -> None:
        fields = ["Поле «Юридический адрес»", "Поле «ИНН»", "Поле «ОГРН»"]
        self.assertEqual(
            {"юридический адрес"},
            composite_field_mentions(
                "Выбор подсказки автоматически заполняет юридический адрес.",
                fields,
            ),
        )
        self.assertEqual(
            set(),
            composite_field_mentions(
                "Выбор подсказки заполняет сведения организации.", fields
            ),
        )

    def test_matrix_requires_negative_candidate_for_typed_date_input(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(
                Path(raw),
                obligation_statement="Поле «Дата аккредитации» доступно для ввода даты.",
            )
            fixture.matrix.write_text(
                "# Матрица тест-дизайна\n\n"
                "| Проверка | Идентификатор сценария | Обязательство ФТ | Контекст исполнения | Проверяемый элемент | Домен проверки | Способ взаимодействия | Проверяемое правило | Исходное состояние | Формирование состояния | Проверяемое действие | Ожидаемый результат | Нужные предпосылки | Тип | Приоритет | Статус исполнения | Планируемый TC-ID |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
                "| MTX-001 | SCN-001 | OBL-001 | CTX-OPEN-MENU — Открытие раздела из меню | Поле «Дата аккредитации» | Дата | Ввод | Поле доступно для ввода даты. | Открыта карточка. | Не требуется: состояние задано предусловием. | Ввести дату. | В поле отображается введённая дата. | SETUP-ACTOR-001 — пользователь с доступом к модулю. | Positive | High | ready | TC-MENU-001 |\n",
                encoding="utf-8",
            )
            _, findings = validate_scope(
                package_root=fixture.root,
                workflow_state_path=fixture.state,
            )

        self.assertIn(
            "matrix-date-negative-candidate-missing",
            [item.id for item in findings if item.blocking],
        )

    def test_matrix_requires_source_defined_date_format_and_day_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(
                Path(raw),
                obligation_statement=(
                    "Поле «Дата аккредитации» имеет формат дд.мм.гггг; "
                    "день 01–31 и невозможные календарные даты не принимаются."
                ),
            )
            fixture.matrix.write_text(
                "# Матрица тест-дизайна\n\n"
                "| Проверка | Идентификатор сценария | Обязательство ФТ | Контекст исполнения | Проверяемый элемент | Домен проверки | Способ взаимодействия | Проверяемое правило | Исходное состояние | Формирование состояния | Проверяемое действие | Ожидаемый результат | Нужные предпосылки | Тип | Приоритет | Статус исполнения | Планируемый TC-ID |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
                "| MTX-001 | SCN-001 | OBL-001 | CTX-OPEN-MENU — Открытие раздела из меню | Поле «Дата аккредитации» | Дата | Ввод | Допустимая дата. | Открыта карточка. | Не требуется: состояние задано предусловием. | Ввести `01.01.2026`. | Значение отображается. | SETUP-ACTOR-001 — пользователь. | Positive | High | ready | TC-DATE-001 |\n"
                "| MTX-002 | SCN-002 | OBL-001 | CTX-OPEN-MENU — Открытие раздела из меню | Поле «Дата аккредитации» | Дата | Ввод | Невозможная дата. | Открыта карточка. | Не требуется: состояние задано предусловием. | Ввести `31.02.2026`. | Значение не принимается. | SETUP-ACTOR-001 — пользователь. | Negative | High | candidate-ui-calibration | TC-DATE-002 |\n",
                encoding="utf-8",
            )
            _, findings = validate_scope(
                package_root=fixture.root,
                workflow_state_path=fixture.state,
            )

        finding_ids = {item.id for item in findings if item.blocking}
        self.assertIn("matrix-date-format-negative-class-missing", finding_ids)
        self.assertIn("matrix-date-day-boundary-classes-missing", finding_ids)

    def test_file_matrix_gate_requires_container_state_and_isolated_format_iterations(self) -> None:
        findings = validate_matrix_file_state_contract(
            rows=[
                {
                    "Проверка": "MTX-FILE-001",
                    "Идентификатор сценария": "SCN-FILE-001",
                    "Проверяемый элемент": "Информационное письмо",
                    "Домен проверки": "Допустимый файл",
                    "Способ взаимодействия": "Выбор файла",
                    "Проверяемое правило": "Принимаются jpg, png и pdf.",
                    "Исходное состояние": "Открыта карточка реквизита.",
                    "Формирование состояния": "Выбрать jpg, png и pdf по очереди.",
                    "Проверяемое действие": "Прикрепить файл.",
                    "Ожидаемый результат": "Файл добавлен.",
                }
            ],
            artifact="test-design-matrix.md",
        )
        finding_ids = {item.id for item in findings if item.blocking}
        self.assertIn("matrix-file-container-initial-state", finding_ids)
        self.assertIn("matrix-file-format-iteration-isolation", finding_ids)

    def test_matrix_gate_rejects_duplicated_trigger_and_mixed_create_edit_oracle(self) -> None:
        findings = validate_matrix_state_and_primary_oracle_contract(
            row={
                "Проверка": "MTX-CREATE-001",
                "Идентификатор сценария": "SCN-CREATE-001",
                "Исходное состояние": "Новая карточка уже заполнена обязательными полями.",
                "Формирование состояния": "Заполнить обязательные поля и ввести значение.",
                "Проверяемое действие": "Нажать «Сохранить».",
                "Ожидаемый результат": "Карточка не создаётся или не изменяется.",
            },
            flow_kind="create",
            artifact="test-design-matrix.md",
        )
        finding_ids = {item.id for item in findings if item.blocking}
        self.assertIn("matrix-state-formation-duplicates-trigger", finding_ids)
        self.assertIn("matrix-context-primary-oracle-ambiguous", finding_ids)

    def test_semantic_consolidation_candidates_are_detected_beyond_exact_duplicates(self) -> None:
        rows = [
            {
                "Идентификатор сценария": "SCN-001",
                "Обязательство ФТ": "OBL-001",
                "Контекст исполнения": "CTX-CREATE — Создание",
                "Проверяемый элемент": "Поле «БИК»",
                "Домен проверки": "Автозаполнение",
                "Способ взаимодействия": "Выбор подсказки",
                "Проверяемое правило": "Подсказка заполняет БИК.",
                "Исходное состояние": "Банковские поля пусты.",
                "Формирование состояния": "Открыть список подсказок.",
                "Проверяемое действие": "Выбрать подсказку.",
                "Ожидаемый результат": "В поле отображается БИК из подсказки.",
                "Тип": "Positive",
                "Статус исполнения": "ready",
            },
            {
                "Идентификатор сценария": "SCN-002",
                "Обязательство ФТ": "OBL-002",
                "Контекст исполнения": "CTX-CREATE — Создание",
                "Проверяемый элемент": "Поле «БИК»",
                "Домен проверки": "Автозаполнение",
                "Способ взаимодействия": "Выбор подсказки",
                "Проверяемое правило": "БИК заполнен после выбора подсказки.",
                "Исходное состояние": "Банковские поля пусты.",
                "Формирование состояния": "Открыть список подсказок.",
                "Проверяемое действие": "Выбрать подсказку.",
                "Ожидаемый результат": "В поле отображается БИК из подсказки.",
                "Тип": "Positive",
                "Статус исполнения": "ready",
            },
        ]
        groups = matrix_semantic_consolidation_groups(rows)
        self.assertEqual(1, len(groups))
        self.assertEqual(
            {"SCN-001", "SCN-002"},
            {row["Идентификатор сценария"] for row in groups[0][1]},
        )

    def test_validator_requires_con_decision_for_semantic_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            context = obligations["obligations"][0]["execution_contexts"][0]
            obligations["obligations"] = [
                {
                    "id": "OBL-001",
                    "source_anchor": "Таблица 8, поле «БИК».",
                    "statement": "После выбора подсказки БИК заполнен.",
                    "risk_flags": [],
                    "execution_contexts": [context],
                },
                {
                    "id": "OBL-002",
                    "source_anchor": "Таблица 8, поле «БИК», О=Да.",
                    "statement": "После выбора подсказки обязательное поле БИК заполнено.",
                    "risk_flags": [],
                    "execution_contexts": [context],
                },
            ]
            write_json(fixture.obligations, obligations)
            fixture.matrix.write_text(
                "# Матрица тест-дизайна\n\n"
                "| Проверка | Идентификатор сценария | Обязательство ФТ | Контекст исполнения | Проверяемый элемент | Домен проверки | Способ взаимодействия | Проверяемое правило | Исходное состояние | Формирование состояния | Проверяемое действие | Ожидаемый результат | Нужные предпосылки | Тип | Приоритет | Статус исполнения | Планируемый TC-ID |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
                "| MTX-001 | SCN-001 | OBL-001 | CTX-OPEN-MENU — Открытие раздела из меню | Поле «БИК» | Автозаполнение | Выбор подсказки | Подсказка заполняет БИК. | Банковские поля пусты. | Открыть список подсказок. | Выбрать подсказку. | В поле отображается БИК из подсказки. | SETUP-ACTOR-001 — пользователь. | Positive | High | ready | TC-BIK-001 |\n"
                "| MTX-002 | SCN-002 | OBL-002 | CTX-OPEN-MENU — Открытие раздела из меню | Поле «БИК» | Автозаполнение | Выбор подсказки | БИК заполнен после выбора. | Банковские поля пусты. | Открыть список подсказок. | Выбрать подсказку. | В поле отображается БИК из подсказки. | SETUP-ACTOR-001 — пользователь. | Positive | High | ready | TC-BIK-002 |\n\n"
                "## Решения о консолидации сценариев\n\n```json\n[]\n```\n",
                encoding="utf-8",
            )
            _, findings = validate_scope(
                package_root=fixture.root,
                workflow_state_path=fixture.state,
            )

        self.assertIn(
            "scenario-consolidation-semantic-candidate-undecided",
            [item.id for item in findings if item.blocking],
        )

    def test_writer_runtime_requires_full_remediation_closure(self) -> None:
        workflow = (REPO_ROOT / "references" / "agent" / "writer-runtime-workflow.md").read_text(
            encoding="utf-8"
        )
        review_format = (
            REPO_ROOT / "references" / "agent" / "practical-v0.9-review-result-format.md"
        ).read_text(encoding="utf-8")

        self.assertIn("remediation_closure", workflow)
        self.assertIn("весь ограниченный класс", workflow)
        self.assertIn("remediation_closure", review_format)

    def test_v09_route_requires_final_review_transition_after_writer_revision(self) -> None:
        route = (REPO_ROOT / "skills" / "ft-practical-route" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("обязательный independent matrix review", route)
        self.assertIn("independent final TC review", route)
        self.assertIn("одна содержательная writer-доработка", route)
        self.assertIn("единый законченный пакет", route)
        canonical_route = (
            REPO_ROOT / "references" / "agent" / "practical-test-case-route-v0.9.md"
        ).read_text(encoding="utf-8")
        self.assertIn("source-to-matrix scan", canonical_route)

    def test_initializer_enables_controller_triage_for_new_scope(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            output = fixture.scope_dir / "fresh-workflow-state.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "init_practical_v09_workflow.py"),
                    "--ft-package-root", str(fixture.root),
                    "--scope-id", "01",
                    "--scope-slug", "menu",
                    "--source-package-manifest", str(fixture.source_manifest),
                    "--scope-obligations", str(fixture.obligations),
                    "--output", str(output),
                ],
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            state = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                CONTROLLER_TRIAGE_CONTRACT_VERSION,
                state["contract_versions"]["controller_triage"],
            )
            self.assertEqual([], state["review_triage"])
            self.assertEqual(
                CLARIFICATION_OUTCOME_CONTRACT_VERSION,
                state["contract_versions"]["clarification_outcome"],
            )
            self.assertEqual(
                EXECUTION_CONTEXT_CONTRACT_VERSION,
                state["contract_versions"]["execution_context"],
            )
            self.assertTrue(state["matrix_review_required"] is None)
            clarification_path = fixture.scope_dir / "scope-clarification-requests.md"
            self.assertEqual(
                str(clarification_path.relative_to(fixture.root)).replace("\\", "/"),
                state["artifacts"]["scope_clarification_requests"],
            )
            self.assertIn(
                "Вопросов, требующих ответа БА, не выявлено.",
                clarification_path.read_text(encoding="utf-8"),
            )

    def test_initializer_binds_required_parity_and_dictionary_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["obligations"][0]["risk_flags"] = ["closed-dictionary"]
            write_json(fixture.obligations, obligations)
            inventory = fixture.scope_dir / "dictionary-inventory.md"
            inventory.write_text("# Состав справочника\n\nЗначения извлечены.\n", encoding="utf-8")
            output = fixture.scope_dir / "fresh-workflow-state.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "init_practical_v09_workflow.py"),
                    "--ft-package-root", str(fixture.root),
                    "--scope-id", "01",
                    "--scope-slug", "menu",
                    "--source-package-manifest", str(fixture.source_manifest),
                    "--scope-obligations", str(fixture.obligations),
                    "--output", str(output),
                ],
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            artifacts = json.loads(output.read_text(encoding="utf-8"))["artifacts"]
            self.assertEqual(
                "work/practical-v0.9/menu/source-parity-check.md",
                artifacts["source_parity_check"],
            )
            self.assertEqual(
                "work/practical-v0.9/menu/dictionary-inventory.md",
                artifacts["dictionary_inventory"],
            )

    def test_initializer_rejects_missing_required_dictionary_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["obligations"][0]["risk_flags"] = ["closed-dictionary"]
            write_json(fixture.obligations, obligations)
            output = fixture.scope_dir / "fresh-workflow-state.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "init_practical_v09_workflow.py"),
                    "--ft-package-root", str(fixture.root),
                    "--scope-id", "01",
                    "--scope-slug", "menu",
                    "--source-package-manifest", str(fixture.source_manifest),
                    "--scope-obligations", str(fixture.obligations),
                    "--output", str(output),
                ],
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertNotEqual(0, completed.returncode)
            self.assertIn("dictionary-inventory.md", completed.stderr)

    def test_current_v09_contract_versions_are_documented_and_initialized(self) -> None:
        workflow_format = (
            REPO_ROOT / "references" / "agent" / "practical-v0.9-workflow-state-format.md"
        ).read_text(encoding="utf-8")
        example_path = (
            REPO_ROOT / "references" / "agent" / "examples"
            / "practical-v0.9-workflow-state.json"
        )
        self.assertIn("генерируется тем же runtime builder-ом", workflow_format)
        self.assertIn("practical-v0.9-workflow-state.json", workflow_format)
        self.assertEqual(
            build_initial_workflow_state(
                scope_id="01",
                scope_slug="example-scope",
                source_package_manifest="work/practical-v0.9/source-package-manifest.json",
                scope_obligations="work/practical-v0.9/example-scope/scope-obligations.json",
                scope_clarification_requests=(
                    "work/practical-v0.9/example-scope/scope-clarification-requests.md"
                ),
            ),
            json.loads(example_path.read_text(encoding="utf-8")),
        )

    def test_workflow_example_renderer_matches_checked_in_example(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "workflow-state.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "render_practical_v09_workflow_example.py"),
                    "--output",
                    str(output),
                ],
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            example_path = (
                REPO_ROOT / "references" / "agent" / "examples"
                / "practical-v0.9-workflow-state.json"
            )
            self.assertEqual(
                json.loads(example_path.read_text(encoding="utf-8")),
                json.loads(output.read_text(encoding="utf-8")),
            )

    def test_invalid_execution_context_contract_or_flow_kind_blocks_current_scope(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["contract_versions"]["execution_context"] = "unexpected-v1"
            write_json(fixture.state, state)
            with self.assertRaisesRegex(PracticalV09Error, "execution_context"):
                load_workflow_state(fixture.state, fixture.root)

            state["contract_versions"]["execution_context"] = (
                EXECUTION_CONTEXT_CONTRACT_VERSION
            )
            write_json(fixture.state, state)
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["obligations"][0]["execution_contexts"][0]["flow_kind"] = "archive"
            write_json(fixture.obligations, obligations)
            _, findings = validate_scope(
                package_root=fixture.root, workflow_state_path=fixture.state
            )
            self.assertIn(
                "scope-obligation-execution-context-flow-kind",
                [item.id for item in findings if item.blocking],
            )

    def test_successful_create_lifecycle_metadata_accepts_equivalent_russian_forms(self) -> None:
        key_cases = {
            "- Ключ создаваемого объекта: ИНН `7707083893`.": "ИНН `7707083893`.",
            "- Идентификатор создаваемого объекта: `PARTNER-001`.": "`PARTNER-001`.",
            "- Уникальный ключ объекта: ИНН `7707083893`, тип `СК`.": "ИНН `7707083893`, тип `СК`.",
        }
        for source, expected in key_cases.items():
            with self.subTest(source=source):
                self.assertEqual(expected, successful_create_object_key(source))
        for source in (
            "- Исходное состояние объекта: отсутствует.",
            "- До начала проверки объект с указанным ключом отсутствует.",
            "- В системе нет объекта с ключом.",
        ):
            with self.subTest(initial_state=source):
                self.assertTrue(successful_create_has_initial_absence(source))
        for source in (
            "После проверки удалить созданный объект.",
            "После проверки вернуть систему в исходное состояние.",
            "Выполнить изолированный прогон.",
        ):
            with self.subTest(cleanup=source):
                self.assertTrue(successful_create_has_cleanup(source))
        self.assertIsNone(successful_create_object_key("- Наименование: Партнер."))
        self.assertFalse(successful_create_has_initial_absence("- Открыта новая карточка."))
        self.assertFalse(successful_create_has_cleanup("Закрыть карточку."))

    def test_current_consolidation_decisions_are_owned_by_matrix_not_workflow_state(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            matrix_text = fixture.matrix.read_text(encoding="utf-8")
            matrix_text += (
                "\n## Решения о консолидации сценариев\n\n```json\n"
                "[{\n"
                "  \"id\": \"CON-001\",\n"
                "  \"decision\": \"merge-parameterized\",\n"
                "  \"scenario_ids\": [\"SCN-001\", \"SCN-002\"],\n"
                "  \"planned_tc_id\": \"TC-MENU-001\",\n"
                "  \"source_anchor\": \"Раздел 9.1\",\n"
                "  \"rationale\": \"Один элемент и одна реакция.\",\n"
                "  \"parameterization_basis\": \"эквивалентные значения одного класса\"\n"
                "}]\n```\n"
            )
            fixture.matrix.write_text(matrix_text, encoding="utf-8")
            raw_decisions, errors = parse_matrix_consolidation_decisions(fixture.matrix)
            self.assertEqual([], errors)
            self.assertEqual("CON-001", raw_decisions[0]["id"])
            rows = {
                "SCN-001": {
                    "Идентификатор сценария": "SCN-001",
                    "Контекст исполнения": "CTX-OPEN-MENU — Открытие раздела из меню",
                    "Проверяемый элемент": "Пункт меню «Партнеры»",
                    "Домен проверки": "Доступность",
                    "Способ взаимодействия": "Нажатие",
                    "Тип": "Positive",
                    "Статус исполнения": "ready",
                    "Планируемый TC-ID": "TC-MENU-001",
                },
                "SCN-002": {
                    "Идентификатор сценария": "SCN-002",
                    "Контекст исполнения": "CTX-OPEN-MENU — Открытие раздела из меню",
                    "Проверяемый элемент": "Пункт меню «Партнеры»",
                    "Домен проверки": "Доступность",
                    "Способ взаимодействия": "Нажатие",
                    "Тип": "Positive",
                    "Статус исполнения": "ready",
                    "Планируемый TC-ID": "TC-MENU-001",
                },
            }
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            self.assertNotIn("scenario_consolidation", state)
            findings, consolidation = scenario_consolidation_contract(
                state=state,
                rows_by_scenario=rows,
                artifact="test-design-matrix.md",
                matrix_path=fixture.matrix,
            )
            self.assertEqual([], [item.id for item in findings if item.blocking])
            self.assertTrue(consolidation["enabled"])
            self.assertEqual("CON-001", consolidation["decisions"][0]["id"])

    def test_initializer_creates_ba_cards_and_binds_outcome_to_review_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["clarifications"] = [{
                "id": "GAP-001",
                "gap_type": "ba-business-ambiguity",
                "source_anchor": "XHTML, раздел 9.1, AS.1",
                "source_statement": "Пункт доступен пользователю.",
                "description": "Не определено условие доступности.",
                "impact": "non-blocking",
                "affected_obligation_ids": ["OBL-001"],
                "question_to_analyst": "Какое условие доступности применяется?",
                "requires_business_answer": True,
                "clarification_id": "CLR-001",
                "temporary_handling": "Не задавать условие доступа до ответа.",
                "status": "open",
            }]
            write_json(fixture.obligations, obligations)
            clarification_path = fixture.scope_dir / "scope-clarification-requests.md"
            clarification_path.unlink()
            output = fixture.scope_dir / "fresh-workflow-state.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "init_practical_v09_workflow.py"),
                    "--ft-package-root", str(fixture.root),
                    "--scope-id", "01",
                    "--scope-slug", "menu",
                    "--source-package-manifest", str(fixture.source_manifest),
                    "--scope-obligations", str(fixture.obligations),
                    "--output", str(output),
                ],
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            rendered = clarification_path.read_text(encoding="utf-8")
            self.assertIn("### CLR-001 — GAP-001", rendered)
            self.assertIn("AS.1", rendered)
            state = json.loads(output.read_text(encoding="utf-8"))
            state["phase"] = "matrix"
            state["artifacts"]["test_design_matrix"] = relative_to_package(
                fixture.root, fixture.matrix
            )
            state["artifacts"]["source_parity_check"] = relative_to_package(
                fixture.root, fixture.source_parity
            )
            write_json(output, state)
            context, findings = validate_scope(
                package_root=fixture.root, workflow_state_path=output
            )
            self.assertFalse([item for item in findings if item.blocking])
            report_path = fixture.scope_dir / "fresh-validator-report.json"
            write_json(report_path, build_validator_report(context, findings))
            state = json.loads(output.read_text(encoding="utf-8"))
            state["artifacts"]["validator_report"] = relative_to_package(
                fixture.root, report_path
            )
            write_json(output, state)
            manifest = build_review_manifest(
                package_root=fixture.root,
                workflow_state_path=output,
                review_mode="matrix",
                controller_thread_id="019feebf-3cde-79d2-9f87-ba9c61ff7b13",
                code_branch="codex/test",
                code_commit="abc123",
                contract_digest="contract",
            )
            self.assertIn(
                "scope_clarification_requests",
                [item["role"] for item in manifest["inputs"]],
            )

    def test_clarification_outcome_contract_blocks_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["contract_versions"]["clarification_outcome"] = (
                CLARIFICATION_OUTCOME_CONTRACT_VERSION
            )
            state["artifacts"]["scope_clarification_requests"] = relative_to_package(
                fixture.root, fixture.scope_dir / "scope-clarification-requests.md"
            )
            write_json(fixture.state, state)
            (fixture.scope_dir / "scope-clarification-requests.md").unlink()
            _, findings = validate_scope(
                package_root=fixture.root, workflow_state_path=fixture.state
            )
            self.assertIn(
                "workflow-artifact-missing",
                [item.id for item in findings if item.blocking],
            )

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

    def test_scope_validator_rejects_an_input_artifact_as_output(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            command = [
                sys.executable,
                str(REPO_ROOT / "scripts" / "validate_practical_scope.py"),
                "--ft-package-root",
                str(fixture.root),
                "--workflow-state",
                str(fixture.state),
                "--output-profile",
                str(fixture.obligations),
                "--exclude-output",
                str(fixture.obligations),
            ]
            completed = subprocess.run(
                command,
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(2, completed.returncode, completed.stderr)
            self.assertIn("not an input artifact", completed.stderr)

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

    def test_source_manifest_cli_auto_discovers_package_mockups(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.source_manifest.unlink()
            visual = fixture.root / "mockups" / "partner-card.png"
            visual.parent.mkdir()
            visual.write_bytes(b"png")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "create_practical_source_manifest.py"),
                    "--ft-package-root", str(fixture.root),
                    "--docx", str(fixture.root / "source" / "main.docx"),
                    "--xhtml", str(fixture.root / "source" / "main.xhtml"),
                    "--output", str(fixture.source_manifest),
                ],
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            created = json.loads(fixture.source_manifest.read_text(encoding="utf-8"))
            self.assertEqual(
                ["mockups/partner-card.png"],
                [item["path"] for item in created["visual_inputs"]],
            )

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
            (fixture.scope_dir / "scope-clarification-requests.md").unlink()

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

    def test_ui_calibration_requires_visual_evidence_check(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["clarifications"] = [{
                "id": "GAP-UI-001",
                "gap_type": "ui-calibration",
                "source_anchor": "XHTML, раздел 9.1, строка «Партнеры»",
                "source_statement": "Пункт доступен пользователю.",
                "description": "Неизвестна фактическая реакция UI.",
                "impact": "non-blocking",
                "affected_obligation_ids": ["OBL-001"],
                "temporary_handling": "Проверить реакцию на стенде.",
                "status": "open",
            }]
            write_json(fixture.obligations, obligations)

            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            finding_ids = [item.id for item in findings if item.blocking]
            self.assertIn("scope-ui-calibration-visual-check", finding_ids)

            obligations["clarifications"][0]["visual_evidence_check"] = {
                "outcome": "runtime-only",
                "checked_sources": [
                    "DOCX/XHTML/PDF: рисунок экрана не определяет фактическую реакцию UI."
                ],
                "remaining_uncertainty": "Реакция UI после нажатия требует прогона.",
            }
            obligations["obligations"][0]["visual_binding"] = {
                "source_anchor": "Рисунок экрана, правый верхний угол",
                "element": "кнопка закрытия",
                "location": "правый верхний угол окна",
            }
            write_json(fixture.obligations, obligations)

            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            finding_ids = [item.id for item in findings if item.blocking]
            self.assertNotIn("scope-ui-calibration-visual-check", finding_ids)
            self.assertNotIn("scope-ui-calibration-visual-sources", finding_ids)
            self.assertNotIn("scope-ui-calibration-visual-residual", finding_ids)
            self.assertNotIn("scope-obligation-visual-binding-incomplete", finding_ids)

    def test_ui_calibration_rejects_incomplete_visual_evidence_or_binding(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["clarifications"] = [{
                "id": "GAP-UI-001",
                "gap_type": "ui-calibration",
                "source_anchor": "XHTML, раздел 9.1, строка «Партнеры»",
                "source_statement": "Пункт доступен пользователю.",
                "description": "Неизвестна фактическая реакция UI.",
                "impact": "non-blocking",
                "affected_obligation_ids": ["OBL-001"],
                "temporary_handling": "Проверить реакцию на стенде.",
                "status": "open",
                "visual_evidence_check": {
                    "outcome": "resolved",
                    "checked_sources": [],
                    "remaining_uncertainty": "",
                },
            }]
            obligations["obligations"][0]["visual_binding"] = {
                "source_anchor": "Рисунок экрана",
                "element": "",
            }
            write_json(fixture.obligations, obligations)

            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            finding_ids = [item.id for item in findings if item.blocking]
            self.assertIn("scope-ui-calibration-visual-outcome", finding_ids)
            self.assertIn("scope-ui-calibration-visual-sources", finding_ids)
            self.assertIn("scope-ui-calibration-visual-residual", finding_ids)
            self.assertIn("scope-obligation-visual-binding-incomplete", finding_ids)

    def test_visual_label_mapping_requires_actual_ui_label_in_matrix_and_test_case(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["obligations"][0]["visual_binding"] = {
                "source_anchor": "Рисунок экрана, верхняя навигация",
                "element": "пункт меню «Группы компаний»",
                "location": "верхняя часть экрана",
                "label_mappings": [{
                    "source_label": "Группы компаний (ГК)",
                    "ui_label": "Группы компаний",
                }],
            }
            write_json(fixture.obligations, obligations)

            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            finding_ids = [item.id for item in findings if item.blocking]
            self.assertIn("matrix-visual-label-binding", finding_ids)
            self.assertIn("test-case-visual-label-binding", finding_ids)

            fixture.matrix.write_text(
                fixture.matrix.read_text(encoding="utf-8").replace(
                    "Пункт меню «Партнеры»",
                    "Пункт меню «Группы компаний»",
                ),
                encoding="utf-8",
            )
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "«Партнеры»",
                    "«Группы компаний»",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            finding_ids = [item.id for item in findings if item.blocking]
            self.assertNotIn("matrix-visual-label-binding", finding_ids)
            self.assertNotIn("test-case-visual-label-binding", finding_ids)

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
            (fixture.scope_dir / "scope-clarification-requests.md").unlink()

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
                "| Проверка | Идентификатор сценария | Обязательство ФТ | Контекст исполнения | Проверяемый элемент | Домен проверки | Способ взаимодействия | Проверяемое правило | Исходное состояние | Формирование состояния | Проверяемое действие | Ожидаемый результат | Нужные предпосылки | Тип | Приоритет | Статус исполнения | Планируемый TC-ID |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n",
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
                + "| MTX-001 | SCN-001 | OBL-001 | CTX-OPEN-MENU | Поле карточки | Доступность поля | Проверка отображения | Проверка поля | Форма открыта. | Не требуется: состояние задано предусловием. | Проверить поле. | Поле доступно. | SETUP-ACTOR-001 | Positive | High | ready | TC-MENU-001 |\n",
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn(
                "matrix-obligation-superseded",
                [item.id for item in findings if item.blocking],
            )

    def test_validator_accepts_approved_ba_clarification_type(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            registry = fixture.root / "support" / "package-approved-ba-decisions.md"
            registry.parent.mkdir()
            registry.write_text(
                approved_ba_decision_registry(decision_type="clarifies-ft"),
                encoding="utf-8",
            )
            manifest = json.loads(fixture.source_manifest.read_text(encoding="utf-8"))
            manifest["approved_ba_decisions"] = [{
                "role": "approved-ba-decision-registry",
                "path": "support/package-approved-ba-decisions.md",
                "sha256": sha256_file(registry),
            }]
            write_json(fixture.source_manifest, manifest)
            findings, _ = validate_source_package_manifest(fixture.source_manifest, fixture.root)
            self.assertNotIn(
                "source-manifest-ba-decision-registry-enum",
                [item.id for item in findings if item.blocking],
            )

    def test_clarifying_ba_decision_cannot_supersede_obligation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            registry = fixture.root / "support" / "package-approved-ba-decisions.md"
            registry.parent.mkdir()
            registry.write_text(
                approved_ba_decision_registry(decision_type="clarifies-ft"),
                encoding="utf-8",
            )
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
            write_json(fixture.obligations, obligations)
            findings, _ = validate_scope_obligations(
                fixture.obligations, fixture.root, fixture.source_manifest
            )
            self.assertIn(
                "scope-obligation-ba-decision-type",
                [item.id for item in findings if item.blocking],
            )

    def test_obligation_cli_blocks_temporary_package_artifacts_and_reports_details(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            temporary = fixture.root / "tmp" / "pdfs" / "derived-screen.png"
            temporary.parent.mkdir(parents=True)
            temporary.write_bytes(b"png")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "validate_practical_obligations.py"),
                    "--ft-package-root", str(fixture.root),
                    "--source-package-manifest", str(fixture.source_manifest),
                    "--scope-obligations", str(fixture.obligations),
                    "--require-clean",
                ],
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(1, completed.returncode, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertIn(
                "practical-stage-temporary-artifacts",
                [item["id"] for item in payload["findings"]],
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
        review_format = (REPO_ROOT / "references" / "agent" / "practical-v0.9-review-result-format.md").read_text(
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
        self.assertIn("practical v0.9", analyzer)
        self.assertNotIn("v0.8", analyzer)
        self.assertIn("автозаполняет несколько полей", scope_format)
        self.assertIn("Не создавай `CLR-*` только из-за различия заголовка", scope_format)
        self.assertIn("visual_evidence_check", route)
        self.assertIn("visual_binding", scope_format)
        self.assertIn("visual_evidence_check", analyzer)
        self.assertIn("visual_binding", review_format)

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

    def test_every_new_scope_requires_matrix_review(self) -> None:
        payload = {
            "obligations": [
                {"id": f"OBL-{index:03d}", "risk_flags": []}
                for index in range(1, 9)
            ]
        }
        required, reasons = matrix_review_required(payload)
        self.assertTrue(required)
        self.assertIn("обязательно", reasons[0])
        required, reasons = matrix_review_required(
            {"obligations": [{"id": "OBL-001", "risk_flags": ["authorization"]}]}
        )
        self.assertTrue(required)
        self.assertIn("authorization", reasons[-1])
        required, reasons = matrix_review_required(
            {"obligations": [{"id": "OBL-001", "risk_flags": ["temporal-rule"]}]}
        )
        self.assertTrue(required)
        self.assertIn("temporal-rule", reasons[-1])

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
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["reviews"] = []
            write_json(fixture.state, state)
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

    def test_reviewer_status_change_requires_structured_status_assertion(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["contract_versions"]["controller_triage"] = (
                CONTROLLER_TRIAGE_CONTRACT_VERSION
            )
            state["review_triage"] = []
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
            result_path = fixture.scope_dir / "test-cases-review-result.json"
            write_json(manifest_path, manifest)
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
                    "findings": [{
                        "id": "RV-STATUS-001",
                        "title": "Ошибочно указан статус исполнения",
                        "details": "Требуется изменить статус исполнения сценария.",
                        "source_anchor": "Раздел 9.1, строка «Партнеры».",
                        "artifact_anchor": "test-cases/9.1-menu.md, TC-MENU-001",
                        "category": "execution-readiness",
                        "severity": "High",
                        "blocking": True,
                        "blocking_reason": "Без смены статуса результат нельзя считать исполнимым.",
                        "remediation_owner": "writer",
                    }],
                },
            )
            _, findings = verify_review_result(
                package_root=fixture.root,
                manifest_path=manifest_path,
                result_path=result_path,
            )
            self.assertIn(
                "review-result-status-assertion",
                [item.id for item in findings if item.blocking],
            )
            self.assertIn(
                "review-result-finding-remediation-closure",
                [item.id for item in findings if item.blocking],
            )

    def test_review_manifest_binds_all_source_package_inputs(self) -> None:
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
            bound = {(entry["role"], entry["path"]) for entry in manifest["inputs"]}
            self.assertTrue({
                ("source-document-main-docx", "source/main.docx"),
                ("source-document-main-xhtml", "source/main.xhtml"),
                ("source-document-pdf-cross-check", "source/main.pdf"),
                ("source-agent-notes", "AGENT-NOTES.md"),
            }.issubset(bound))
            snapshot_path = fixture.scope_dir / "test-cases-review-input-snapshot"
            snapshot = create_snapshot(
                manifest_path=manifest_path,
                package_root=fixture.root,
                destination=snapshot_path,
            )
            self.assertTrue(snapshot["allowed"])

    def test_provided_fixture_files_are_required_and_bound_to_review_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.write_verified_dadata_fixture()
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            fixture_root = "work/practical-v0.9/menu/fixtures/FX-DADATA-PARTNER-001"
            obligations["execution_setups"].append(
                {
                    "id": "SETUP-FIXTURE-001",
                    "kind": "fixture",
                    "availability": "provided",
                    "evidence": "Сохранен проверенный профиль DaData.",
                    "artifacts": [
                        f"{fixture_root}/FX-DADATA-PARTNER-001.response.json",
                        f"{fixture_root}/FX-DADATA-PARTNER-001.verification.json",
                    ],
                }
            )
            write_json(fixture.obligations, obligations)
            context, findings = validate_scope(
                package_root=fixture.root, workflow_state_path=fixture.state
            )
            self.assertFalse([item for item in findings if item.blocking])
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
            bound = {(entry["role"], entry["path"]) for entry in manifest["inputs"]}
            self.assertTrue(
                {
                    (
                        "provided-setup-SETUP-FIXTURE-001-1",
                        f"{fixture_root}/FX-DADATA-PARTNER-001.response.json",
                    ),
                    (
                        "provided-setup-SETUP-FIXTURE-001-2",
                        f"{fixture_root}/FX-DADATA-PARTNER-001.verification.json",
                    ),
                }.issubset(bound)
            )

    def test_provided_fixture_without_artifacts_blocks_scope(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["execution_setups"].append(
                {
                    "id": "SETUP-FIXTURE-001",
                    "kind": "fixture",
                    "availability": "provided",
                    "evidence": "Сохранен проверенный профиль DaData.",
                }
            )
            write_json(fixture.obligations, obligations)
            _, findings = validate_scope(
                package_root=fixture.root, workflow_state_path=fixture.state
            )
            self.assertIn(
                "scope-execution-provided-fixture-artifacts",
                [item.id for item in findings if item.blocking],
            )

    def test_closed_dictionary_requires_bound_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["obligations"][0]["risk_flags"] = ["closed-dictionary"]
            write_json(fixture.obligations, obligations)
            self.assertTrue(dictionary_inventory_required(obligations))
            _, findings = validate_scope(
                package_root=fixture.root, workflow_state_path=fixture.state
            )
            self.assertIn(
                "dictionary-inventory-reference-missing",
                [item.id for item in findings if item.blocking],
            )

    def test_closed_dictionary_inventory_is_bound_to_review_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["obligations"][0]["risk_flags"] = ["closed-dictionary"]
            write_json(fixture.obligations, obligations)
            inventory = fixture.scope_dir / "dictionary-inventory.md"
            inventory.write_text(
                "# Состав справочника\n\n"
                "| Идентификатор | Значения |\n| --- | --- |\n"
                "| `DICT-001` | `Первое`; `Второе` |\n",
                encoding="utf-8",
            )
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["artifacts"]["dictionary_inventory"] = (
                "work/practical-v0.9/menu/dictionary-inventory.md"
            )
            state["phase"] = "matrix"
            write_json(fixture.state, state)
            context, findings = validate_scope(
                package_root=fixture.root, workflow_state_path=fixture.state
            )
            self.assertFalse([item for item in findings if item.blocking])
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
            self.assertIn(
                ("dictionary_inventory", "work/practical-v0.9/menu/dictionary-inventory.md"),
                {(entry["role"], entry["path"]) for entry in manifest["inputs"]},
            )

    def test_closed_dictionary_rejects_empty_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["obligations"][0]["risk_flags"] = ["closed-dictionary"]
            write_json(fixture.obligations, obligations)
            inventory = fixture.scope_dir / "dictionary-inventory.md"
            inventory.write_text("\n", encoding="utf-8")
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["artifacts"]["dictionary_inventory"] = (
                "work/practical-v0.9/menu/dictionary-inventory.md"
            )
            write_json(fixture.state, state)
            _, findings = validate_scope(
                package_root=fixture.root, workflow_state_path=fixture.state
            )
            self.assertIn(
                "dictionary-inventory-empty",
                [item.id for item in findings if item.blocking],
            )

    def test_review_result_rejects_unsupported_verdict_enum(self) -> None:
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
            result_path = fixture.scope_dir / "test-cases-review-result.json"
            write_json(manifest_path, manifest)
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
                    "verdict": "rejected",
                    "findings": [],
                },
            )
            _, findings = verify_review_result(
                package_root=fixture.root,
                manifest_path=manifest_path,
                result_path=result_path,
            )
            self.assertIn(
                "review-result-verdict",
                [item.id for item in findings if item.blocking],
            )

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

    def test_compact_reviewer_receipt_binds_large_scope_to_per_obligation_vector(self) -> None:
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
            manifest["reviewer_receipt_contract"] = {
                "format": COMPACT_REVIEWER_RECEIPT_FORMAT,
                "max_bytes": COMPACT_REVIEWER_RECEIPT_MAX_BYTES,
                "scope_obligations_sha256": sha256_file(fixture.obligations),
                "active_obligation_count": 1,
                "active_obligation_ids_sha256": obligation_ids_sha256({"OBL-001"}),
                "obligation_ids": ["OBL-001"],
            }
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
                    "independent_obligation_vector": [
                        {
                            "obligation_id": "OBL-001",
                            "verdict": "covered",
                            "source_anchor": "Раздел 9.1, строка «Партнеры»",
                            "statement": "Проверено обязательство immutable snapshot.",
                        }
                    ],
                    "independent_obligation_vector_digest": manifest[
                        "reviewer_receipt_contract"
                    ]["active_obligation_ids_sha256"],
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

            result = json.loads(result_path.read_text(encoding="utf-8"))
            result["independent_obligation_vector_digest"] = "0" * 64
            write_json(result_path, result)
            _, findings = verify_review_result(
                package_root=fixture.root,
                manifest_path=manifest_path,
                result_path=result_path,
            )
            self.assertIn(
                "review-result-compact-obligation-vector-digest",
                [item.id for item in findings if item.blocking],
            )

    def test_session_attestation_is_required_when_manifest_declares_it(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            repo_root = fixture.root.parent
            manifest = build_review_manifest(
                package_root=fixture.root,
                workflow_state_path=fixture.state,
                review_mode="matrix",
                controller_thread_id="019feebf-3cde-79d2-9f87-ba9c61ff7b13",
                code_branch="codex/test",
                code_commit="abc123",
                contract_digest="contract",
                ft_package_path=fixture.root.name,
                repo_root_path=str(repo_root),
                require_session_attestation=True,
            )
            manifest_path = fixture.scope_dir / "matrix-review-manifest.json"
            write_json(manifest_path, manifest)
            self.assertEqual(str(repo_root.resolve()), manifest["repo_root"])
            self.assertEqual(str(fixture.root.resolve()), manifest["ft_package_root"])
            self.assertEqual(fixture.root.name, manifest["ft_package_path"])
            attestation_path = fixture.scope_dir / "matrix-review-session.json"
            write_json(
                attestation_path,
                build_review_session_attestation(
                    package_root=fixture.root,
                    manifest_path=manifest_path,
                    reviewer_thread_id="019feebf-3cde-79d2-9f87-ba9c61ff7b14",
                ),
            )
            attestation = json.loads(attestation_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["repo_root"], attestation["repo_root"])
            self.assertEqual(manifest["ft_package_root"], attestation["ft_package_root"])
            result_path = fixture.scope_dir / "matrix-review-result.json"
            write_json(
                result_path,
                {
                    "review_manifest_sha256": sha256_file(manifest_path),
                    "review_session_attestation_sha256": sha256_file(attestation_path),
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
            _, missing = verify_review_result(
                package_root=fixture.root,
                manifest_path=manifest_path,
                result_path=result_path,
            )
            self.assertIn(
                "review-result-session-attestation-missing",
                [item.id for item in missing if item.blocking],
            )
            _, findings = verify_review_result(
                package_root=fixture.root,
                manifest_path=manifest_path,
                result_path=result_path,
                review_session_attestation_path=attestation_path,
            )
            self.assertFalse([item for item in findings if item.blocking])
            attestation["repo_root"] = str((fixture.root / "other-root").resolve())
            write_json(attestation_path, attestation)
            result = json.loads(result_path.read_text(encoding="utf-8"))
            result["review_session_attestation_sha256"] = sha256_file(attestation_path)
            write_json(result_path, result)
            _, findings = verify_review_result(
                package_root=fixture.root,
                manifest_path=manifest_path,
                result_path=result_path,
                review_session_attestation_path=attestation_path,
            )
            self.assertIn(
                "review-result-session-attestation-mismatch",
                [item.id for item in findings if item.blocking],
            )

    def test_finalizer_preserves_required_session_attestation_in_review_history(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            manifest = build_review_manifest(
                package_root=fixture.root,
                workflow_state_path=fixture.state,
                review_mode="matrix",
                controller_thread_id="019feebf-3cde-79d2-9f87-ba9c61ff7b13",
                code_branch="codex/test",
                code_commit="abc123",
                contract_digest="contract",
                ft_package_path=".",
                repo_root_path=str(fixture.root),
                require_session_attestation=True,
            )
            manifest_path = fixture.scope_dir / "matrix-review-manifest.json"
            write_json(manifest_path, manifest)
            attestation_path = fixture.scope_dir / "matrix-review-session.json"
            write_json(
                attestation_path,
                build_review_session_attestation(
                    package_root=fixture.root,
                    manifest_path=manifest_path,
                    reviewer_thread_id="019feebf-3cde-79d2-9f87-ba9c61ff7b14",
                ),
            )
            result_path = fixture.scope_dir / "matrix-review-result.json"
            write_json(
                result_path,
                {
                    "review_manifest_sha256": sha256_file(manifest_path),
                    "review_session_attestation_sha256": sha256_file(attestation_path),
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
                    "--review-session-attestation", str(attestation_path),
                ],
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            review = state["reviews"][-1]
            self.assertEqual(
                "work/practical-v0.9/menu/matrix-review-session.json",
                review["session_attestation"],
            )
            self.assertEqual(
                sha256_file(attestation_path), review["session_attestation_sha256"]
            )
            _, findings = validate_scope(
                package_root=fixture.root, workflow_state_path=fixture.state
            )
            self.assertNotIn(
                "workflow-review-session-attestation-binding",
                [item.id for item in findings if item.blocking],
            )

    def test_matrix_reviewer_does_not_require_consolidation_receipt_without_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            manifest = build_review_manifest(
                package_root=fixture.root,
                workflow_state_path=fixture.state,
                review_mode="matrix",
                controller_thread_id="019feebf-3cde-79d2-9f87-ba9c61ff7b13",
                code_branch="codex/test",
                code_commit="abc123",
                contract_digest="contract",
            )
            self.assertNotIn("scenario_consolidation_contract", manifest)

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
                [{"mode": "matrix", "verdict": "approved"}, {
                    "mode": "test-cases",
                    "verdict": "approved",
                    "manifest": "work/practical-v0.9/menu/test-cases-review-manifest.json",
                    "result": "work/practical-v0.9/menu/test-cases-review-result.json",
                    "result_sha256": sha256_file(result_path),
                }],
                state["reviews"],
            )

            result_path.write_text(result_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn(
                "workflow-review-result-drift",
                [item.id for item in findings if item.blocking],
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

    def test_controller_triage_is_required_before_new_scope_spends_revision_budget(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["contract_versions"]["controller_triage"] = (
                CONTROLLER_TRIAGE_CONTRACT_VERSION
            )
            state["review_triage"] = []
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
            self.assertIn("controller_triage_contract", manifest)
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
                    "findings": [{
                        "id": "RV-001",
                        "title": "Не хватает сценария",
                        "details": "Матрица и ТК не покрывают отдельный наблюдаемый результат.",
                        "source_anchor": "Раздел 9.1, строка «Партнеры».",
                        "artifact_anchor": "test-cases/9.1-menu.md",
                        "category": "semantic-completeness",
                        "severity": "High",
                        "blocking": True,
                        "blocking_reason": "Без исправления нет source-backed покрытия.",
                        "remediation_owner": "writer",
                        "remediation_closure": {
                            "basis": "Отсутствующее source-backed покрытие в том же пользовательском потоке.",
                            "scenario_ids": ["SCN-001"],
                            "obligation_ids": ["OBL-001"],
                        },
                    }],
                },
            )
            finalize = [
                sys.executable, str(REPO_ROOT / "scripts" / "finalize_practical_review.py"),
                "--ft-package-root", str(fixture.root),
                "--workflow-state", str(fixture.state),
                "--review-manifest", str(manifest_path),
                "--review-result", str(result_path),
            ]
            blocked = subprocess.run(
                finalize, text=True, capture_output=True, encoding="utf-8", errors="replace"
            )
            self.assertNotEqual(0, blocked.returncode)
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            self.assertEqual(0, state["tc_revision_count"])
            self.assertEqual(
                [{"mode": "matrix", "verdict": "approved"}], state["reviews"]
            )

            decisions_path = fixture.scope_dir / "controller-triage-input.json"
            write_json(
                decisions_path,
                {
                    "review_result_sha256": sha256_file(result_path),
                    "decisions": [{
                        "finding_id": "RV-001",
                        "disposition": "accepted",
                        "rationale": "Проверены ФТ и тестовый артефакт: отдельная проверка действительно отсутствует.",
                        "checked_anchors": [
                            "Раздел 9.1, строка «Партнеры».",
                            "test-cases/9.1-menu.md",
                        ],
                    }],
                },
            )
            triaged = subprocess.run(
                [
                    sys.executable, str(REPO_ROOT / "scripts" / "triage_practical_review.py"),
                    "--ft-package-root", str(fixture.root),
                    "--workflow-state", str(fixture.state),
                    "--review-manifest", str(manifest_path),
                    "--review-result", str(result_path),
                    "--decisions-file", str(decisions_path),
                ],
                text=True, capture_output=True, encoding="utf-8", errors="replace",
            )
            self.assertEqual(0, triaged.returncode, triaged.stderr)
            completed = subprocess.run(
                finalize, text=True, capture_output=True, encoding="utf-8", errors="replace"
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            self.assertEqual(1, state["tc_revision_count"])
            self.assertEqual("test-cases", state["phase"])

    def test_content_finding_cannot_be_misclassified_as_controller_only(self) -> None:
        findings = review_content_findings(
            {
                "findings": [
                    {
                        "id": "RV-001",
                        "category": "coverage",
                        "blocking": True,
                        "remediation_owner": "controller",
                    },
                    {
                        "id": "RV-002",
                        "category": "review-integrity",
                        "blocking": True,
                        "remediation_owner": "controller",
                    },
                ]
            }
        )
        self.assertEqual(["RV-001"], [item["id"] for item in findings])

    def test_legacy_triage_keeps_historical_owner_classification(self) -> None:
        findings = review_content_findings(
            {
                "findings": [
                    {
                        "id": "RV-001",
                        "category": "coverage",
                        "blocking": True,
                        "remediation_owner": "controller",
                    }
                ]
            },
            triage_contract_version=LEGACY_CONTROLLER_TRIAGE_CONTRACT_VERSION,
        )
        self.assertEqual([], findings)

    def test_validator_blocks_review_input_change_between_triage_and_finalization(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["contract_versions"]["controller_triage"] = (
                CONTROLLER_TRIAGE_CONTRACT_VERSION
            )
            state["review_triage"] = []
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
            result_path = fixture.scope_dir / "test-cases-review-result.json"
            write_json(manifest_path, manifest)
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
                    "findings": [{
                        "id": "RV-001",
                        "title": "Не хватает сценария",
                        "details": "Матрица и ТК не покрывают отдельный наблюдаемый результат.",
                        "source_anchor": "Раздел 9.1, строка «Партнеры».",
                        "artifact_anchor": "test-cases/9.1-menu.md",
                        "category": "semantic-completeness",
                        "severity": "High",
                        "blocking": True,
                        "blocking_reason": "Без исправления нет source-backed покрытия.",
                        "remediation_owner": "writer",
                        "remediation_closure": {
                            "basis": "Отсутствующее source-backed покрытие в том же пользовательском потоке.",
                            "scenario_ids": ["SCN-001"],
                            "obligation_ids": ["OBL-001"],
                        },
                    }],
                },
            )
            decisions_path = fixture.scope_dir / "controller-triage-input.json"
            write_json(
                decisions_path,
                {
                    "review_result_sha256": sha256_file(result_path),
                    "decisions": [{
                        "finding_id": "RV-001",
                        "disposition": "accepted",
                        "rationale": "Проверены ФТ и тестовый артефакт: отдельная проверка действительно отсутствует.",
                        "checked_anchors": [
                            "Раздел 9.1, строка «Партнеры».",
                            "test-cases/9.1-menu.md",
                        ],
                    }],
                },
            )
            triaged = subprocess.run(
                [
                    sys.executable, str(REPO_ROOT / "scripts" / "triage_practical_review.py"),
                    "--ft-package-root", str(fixture.root),
                    "--workflow-state", str(fixture.state),
                    "--review-manifest", str(manifest_path),
                    "--review-result", str(result_path),
                    "--decisions-file", str(decisions_path),
                ],
                text=True, capture_output=True, encoding="utf-8", errors="replace",
            )
            self.assertEqual(0, triaged.returncode, triaged.stderr)
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8") + "\n", encoding="utf-8"
            )
            _, findings = validate_scope(
                package_root=fixture.root, workflow_state_path=fixture.state
            )
            self.assertIn(
                "workflow-triage-finalization-required",
                [item.id for item in findings if item.blocking],
            )

    def test_explicit_recovery_finalizes_verified_pretriage_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["contract_versions"]["controller_triage"] = (
                CONTROLLER_TRIAGE_CONTRACT_VERSION
            )
            state["review_triage"] = []
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
            result_path = fixture.scope_dir / "test-cases-review-result.json"
            write_json(manifest_path, manifest)
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
                    "findings": [{
                        "id": "RV-001",
                        "title": "Не хватает сценария",
                        "details": "Матрица и ТК не покрывают отдельный наблюдаемый результат.",
                        "source_anchor": "Раздел 9.1, строка «Партнеры».",
                        "artifact_anchor": "test-cases/9.1-menu.md",
                        "category": "semantic-completeness",
                        "severity": "High",
                        "blocking": True,
                        "blocking_reason": "Без исправления нет source-backed покрытия.",
                        "remediation_owner": "writer",
                        "remediation_closure": {
                            "basis": "Отсутствующее source-backed покрытие в том же пользовательском потоке.",
                            "scenario_ids": ["SCN-001"],
                            "obligation_ids": ["OBL-001"],
                        },
                    }],
                },
            )
            decisions_path = fixture.scope_dir / "controller-triage-input.json"
            write_json(
                decisions_path,
                {
                    "review_result_sha256": sha256_file(result_path),
                    "decisions": [{
                        "finding_id": "RV-001",
                        "disposition": "accepted",
                        "rationale": "Проверены ФТ и тестовый артефакт: отдельная проверка действительно отсутствует.",
                        "checked_anchors": [
                            "Раздел 9.1, строка «Партнеры».",
                            "test-cases/9.1-menu.md",
                        ],
                    }],
                },
            )
            triaged = subprocess.run(
                [
                    sys.executable, str(REPO_ROOT / "scripts" / "triage_practical_review.py"),
                    "--ft-package-root", str(fixture.root),
                    "--workflow-state", str(fixture.state),
                    "--review-manifest", str(manifest_path),
                    "--review-result", str(result_path),
                    "--decisions-file", str(decisions_path),
                ],
                text=True, capture_output=True, encoding="utf-8", errors="replace",
            )
            self.assertEqual(0, triaged.returncode, triaged.stderr)
            snapshot_path = fixture.scope_dir / "test-cases-review-input-snapshot"
            snapshot = create_snapshot(
                manifest_path=manifest_path,
                package_root=fixture.root,
                destination=snapshot_path,
            )
            self.assertTrue(snapshot["allowed"])
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8") + "\n", encoding="utf-8"
            )
            recovered = subprocess.run(
                [
                    sys.executable, str(REPO_ROOT / "scripts" / "finalize_practical_review.py"),
                    "--ft-package-root", str(fixture.root),
                    "--workflow-state", str(fixture.state),
                    "--review-manifest", str(manifest_path),
                    "--review-result", str(result_path),
                    "--allow-post-triage-recovery",
                    "--review-input-snapshot", str(snapshot_path),
                    "--recovery-reason", "Явно одобренное восстановление после ошибки порядка triage и finalization.",
                ],
                text=True, capture_output=True, encoding="utf-8", errors="replace",
            )
            self.assertEqual(0, recovered.returncode, recovered.stderr)
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            self.assertEqual(1, state["tc_revision_count"])
            self.assertEqual(2, len(state["reviews"]))
            self.assertEqual(
                "Провести повторное независимое review тест-кейсов после уже выполненной целевой доработки",
                state["next_action"],
            )
            self.assertTrue(any("восстановление finalization" in item for item in state["decision_notes"]))

    def test_controller_triage_rejects_wrong_status_finding_without_spending_budget(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["execution_setups"][0]["availability"] = "needs-test-data"
            write_json(fixture.obligations, obligations)
            fixture.matrix.write_text(
                fixture.matrix.read_text(encoding="utf-8").replace(
                    "| Positive | High | ready |",
                    "| Positive | High | needs-test-data |",
                ),
                encoding="utf-8",
            )
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["phase"] = "matrix"
            state["artifacts"]["canonical_test_cases"] = "not-created"
            state["contract_versions"]["controller_triage"] = (
                CONTROLLER_TRIAGE_CONTRACT_VERSION
            )
            state["review_triage"] = []
            write_json(fixture.state, state)
            context, validation_findings = validate_scope(
                package_root=fixture.root, workflow_state_path=fixture.state
            )
            write_json(
                fixture.scope_dir / "validator-report.json",
                build_validator_report(context, validation_findings),
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
                    "verdict": "changes-required",
                    "findings": [{
                        "id": "RV-STATUS-001",
                        "title": "Неверный статус",
                        "details": "Для проверки требуется UI-калибровка.",
                        "source_anchor": "Раздел 9.1, строка «Партнеры».",
                        "artifact_anchor": "test-design-matrix.md, SCN-001",
                        "category": "execution-readiness",
                        "severity": "Medium",
                        "blocking": True,
                        "blocking_reason": "Статус необходимо изменить.",
                        "remediation_owner": "writer",
                        "remediation_closure": {
                            "basis": "Тот же сценарий с неполной цепочкой предпосылок исполнения.",
                            "scenario_ids": ["SCN-001"],
                            "obligation_ids": ["OBL-001"],
                        },
                        "status_assertion": {
                            "scenario_ids": ["SCN-001"],
                            "required_status": "candidate-ui-calibration",
                        },
                    }],
                },
            )
            decisions_path = fixture.scope_dir / "controller-triage-input.json"
            write_json(
                decisions_path,
                {
                    "review_result_sha256": sha256_file(result_path),
                    "decisions": [{
                        "finding_id": "RV-STATUS-001",
                        "disposition": "accepted",
                        "rationale": "Статус считается скорректированным без проверки полной цепочки предпосылок.",
                        "checked_anchors": [
                            "SCN-001; SETUP-ACTOR-001.",
                        ],
                    }],
                },
            )
            wrongly_accepted = subprocess.run(
                [
                    sys.executable, str(REPO_ROOT / "scripts" / "triage_practical_review.py"),
                    "--ft-package-root", str(fixture.root),
                    "--workflow-state", str(fixture.state),
                    "--review-manifest", str(manifest_path),
                    "--review-result", str(result_path),
                    "--decisions-file", str(decisions_path),
                ],
                text=True, capture_output=True, encoding="utf-8", errors="replace",
            )
            self.assertNotEqual(0, wrongly_accepted.returncode)
            write_json(
                decisions_path,
                {
                    "review_result_sha256": sha256_file(result_path),
                    "decisions": [{
                        "finding_id": "RV-STATUS-001",
                        "disposition": "rejected",
                        "rationale": "Полная цепочка SETUP содержит отсутствующего актора, поэтому приоритет имеет needs-test-data.",
                        "checked_anchors": [
                            "practical route: порядок статусов исполнения.",
                            "SCN-001; SETUP-ACTOR-001.",
                        ],
                        "rejection": {
                            "basis": "execution-status-precedence",
                        },
                    }],
                },
            )
            triaged = subprocess.run(
                [
                    sys.executable, str(REPO_ROOT / "scripts" / "triage_practical_review.py"),
                    "--ft-package-root", str(fixture.root),
                    "--workflow-state", str(fixture.state),
                    "--review-manifest", str(manifest_path),
                    "--review-result", str(result_path),
                    "--decisions-file", str(decisions_path),
                ],
                text=True, capture_output=True, encoding="utf-8", errors="replace",
            )
            self.assertEqual(0, triaged.returncode, triaged.stderr)
            completed = subprocess.run(
                [
                    sys.executable, str(REPO_ROOT / "scripts" / "finalize_practical_review.py"),
                    "--ft-package-root", str(fixture.root),
                    "--workflow-state", str(fixture.state),
                    "--review-manifest", str(manifest_path),
                    "--review-result", str(result_path),
                ],
                text=True, capture_output=True, encoding="utf-8", errors="replace",
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            self.assertEqual(0, state["matrix_revision_count"])
            self.assertEqual("test-cases", state["phase"])
            self.assertEqual(
                "approved", state["reviews"][-1]["effective_verdict"]
            )

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

    def test_contract_migration_accepts_v2_matrix_as_legacy_input(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.matrix.write_text(
                "# Матрица тест-дизайна\n\n"
                "| Проверка | Идентификатор сценария | Обязательство ФТ | Контекст исполнения | Проверяемое правило | Исходное состояние | Формирование состояния | Проверяемое действие | Ожидаемый результат | Нужные предпосылки | Тип | Приоритет | Статус исполнения | Планируемый TC-ID |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
                "| MTX-001 | SCN-001 | OBL-001 | CTX-OPEN-MENU — Открытие раздела из меню | Пункт меню доступен. | Пользователь вошёл. | Не требуется: состояние задано предусловием. | Открыть раздел. | Раздел открыт. | SETUP-ACTOR-001. | Positive | High | ready | TC-MENU-001 |\n",
                encoding="utf-8",
            )
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["contract_versions"]["matrix"] = PREVIOUS_MATRIX_CONTRACT_VERSION
            state["contract_versions"]["scenario_consolidation"] = (
                LEGACY_SCENARIO_CONSOLIDATION_CONTRACT_VERSION
            )
            state["scenario_consolidation"] = []
            write_json(fixture.state, state)
            snapshot_dir = fixture.scope_dir / "contract-migration-v2-to-v3-snapshot"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "migrate_practical_matrix_contract.py"),
                    "--ft-package-root", str(fixture.root),
                    "--workflow-state", str(fixture.state),
                    "--action", "start", "--snapshot-dir", str(snapshot_dir),
                    "--explicit-user-authorization",
                ],
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            migrated = json.loads(fixture.state.read_text(encoding="utf-8"))
            self.assertEqual(MATRIX_CONTRACT_VERSION, migrated["contract_versions"]["matrix"])
            self.assertEqual(
                PREVIOUS_MATRIX_CONTRACT_VERSION,
                migrated["contract_migration"]["from_matrix_contract"],
            )
            self.assertEqual(
                SCENARIO_CONSOLIDATION_CONTRACT_VERSION,
                migrated["contract_versions"]["scenario_consolidation"],
            )

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
                "| Проверка | Идентификатор сценария | Обязательство ФТ | Контекст исполнения | Проверяемый элемент | Домен проверки | Способ взаимодействия | Проверяемое правило | Исходное состояние | Формирование состояния | Проверяемое действие | Ожидаемый результат | Нужные предпосылки | Тип | Приоритет | Статус исполнения | Планируемый TC-ID |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
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

    def test_validator_rejects_generic_completion_data_and_actions(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "**Тестовые данные:** Не требуются.",
                    "**Тестовые данные:**\n"
                    "- Остальные обязательные поля заполнить допустимыми значениями.\n"
                    "- Уникальный набор обязательных значений.\n"
                    "- Заполнить карточку партнёра.\n"
                    "- Подготовить файл формата PDF размером 1 МБ.\n"
                    "- Строка длиной 2000 символов.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            finding_ids = {item.id for item in findings if item.blocking}
            self.assertIn("test-case-test-data-generic-completion", finding_ids)
            self.assertIn("test-case-test-data-action-leak", finding_ids)
            self.assertIn("test-case-test-data-preparation-missing", finding_ids)

    def test_validator_allows_prepared_boundary_or_file_data(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "**Тестовые данные:** Не требуются.",
                    "**Тестовые данные:**\n"
                    "- Строка длиной 2000 символов `А`.\n"
                    "- Файл `document.pdf`, формат PDF, размер 1 МБ.\n"
                    "- Способ подготовки: локально создать строку повторением `А` "
                    "2000 раз и файл `document.pdf` фиксированного размера 1 МБ.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            finding_ids = {item.id for item in findings if item.blocking}
            self.assertNotIn("test-case-test-data-preparation-missing", finding_ids)
            self.assertNotIn("test-case-test-data-action-leak", finding_ids)

    def test_validator_warns_about_unused_copied_test_data_profile(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8")
                .replace(
                    "**Тестовые данные:** Не требуются.",
                    "**Тестовые данные:** Запрос `АЛЬФА`; подсказка `ООО АЛЬФА`; "
                    "ИНН `7700000000`; КПП `770001001`; ОГРН `1027700000000`; "
                    "адрес `г Москва, ул Тестовая, д 1`.",
                )
                .replace(
                    "1. Открыть раздел «Партнеры».",
                    "1. Ввести в поле поиска `АЛЬФА`.",
                )
                .replace(
                    "Открывается раздел «Партнеры».",
                    "Отображается подсказка `ООО АЛЬФА`.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            matching = [
                item for item in findings
                if item.id == "test-case-test-data-profile-overfull"
            ]
            self.assertEqual(1, len(matching))
            self.assertFalse(matching[0].blocking)

    def test_validator_allows_reused_profile_when_literals_are_used_for_save(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8")
                .replace(
                    "**Тестовые данные:** Не требуются.",
                    "**Тестовые данные:** Наименование `ООО АЛЬФА`; ИНН `7700000000`; "
                    "КПП `770001001`; адрес `г Москва, ул Тестовая, д 1`.",
                )
                .replace(
                    "1. Открыть раздел «Партнеры».",
                    "1. Заполнить обязательные поля указанными значениями и сохранить карточку.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertNotIn(
                "test-case-test-data-profile-overfull",
                [item.id for item in findings],
            )

    def test_validator_rejects_circular_data_and_meta_state_steps(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.matrix.write_text(
                fixture.matrix.read_text(encoding="utf-8")
                .replace(
                    "Не требуется: состояние задано предусловием.",
                    "Доступны указанные предпосылки; подготовлена строка запроса.",
                )
                .replace(
                    "Открыть пункт меню «Партнеры».",
                    "Открыть пункт меню «Партнеры» и подготовить данные для проверяемого правила.",
                ),
                encoding="utf-8",
            )
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8")
                .replace(
                    "**Тестовые данные:** Не требуются.",
                    "**Тестовые данные:** Подготовлена строка запроса; параметры, указанные в тестовых данных.",
                )
                .replace(
                    "1. Открыть раздел «Партнеры».",
                    "1. Сформировать исходное состояние.\n2. Открыть раздел «Партнеры».",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            finding_ids = [item.id for item in findings if item.blocking]
            self.assertIn("matrix-meta-state-description", finding_ids)
            self.assertIn("test-case-test-data-tautology", finding_ids)
            self.assertIn("test-case-meta-state-step", finding_ids)

    def test_validator_rejects_context_label_substituted_for_navigation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.matrix.write_text(
                fixture.matrix.read_text(encoding="utf-8").replace(
                    "Открыть пункт меню «Партнеры».",
                    "Открыть раздел «Партнеры» в контексте «Открытие раздела из меню».",
                ),
                encoding="utf-8",
            )
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "1. Открыть раздел «Партнеры».",
                    "1. Открыть раздел «Партнеры» в контексте «Открытие раздела из меню».",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            finding_ids = [item.id for item in findings if item.blocking]
            self.assertIn("matrix-context-label-as-action", finding_ids)
            self.assertIn("test-case-context-label-as-action", finding_ids)

    def test_validator_rejects_generic_dadata_test_data(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(
                Path(raw),
                obligation_statement="По введённому наименованию система показывает подходящие организации DaData.",
            )
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8")
                .replace(
                    "**Тестовые данные:** Не требуются.",
                    "**Тестовые данные:** Подготовить организацию с известным наименованием и доступной подсказкой DaData.",
                )
                .replace(
                    "1. Открыть раздел «Партнеры».",
                    "1. Ввести фрагмент наименования в поле «Наименование партнёра».\n"
                    "2. Выбрать организацию из подсказки DaData.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn(
                "test-case-dadata-generic-data",
                [item.id for item in findings if item.blocking],
            )

    def test_validator_allows_explicit_missing_dadata_fixture_contract(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(
                Path(raw),
                obligation_statement="По введённому наименованию система показывает подходящие организации DaData.",
            )
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8")
                .replace(
                    "**Тестовые данные:** Не требуются.",
                    "**Тестовые данные:** Требуемый профиль: юридическое лицо с заполненными "
                    "наименованием и ИНН в ответе DaData. Способ подготовки: включить "
                    "интеграцию DaData в тестовом контуре и сохранить выбранную подсказку "
                    "как fixture прогона.",
                )
                .replace(
                    "1. Открыть раздел «Партнеры».",
                    "1. Ввести фрагмент наименования в поле «Наименование партнёра».\n"
                    "2. Выбрать организацию из подсказки DaData.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertNotIn(
                "test-case-dadata-test-data-contract",
                [item.id for item in findings],
            )

    def test_validator_allows_dadata_fixture_with_used_literal(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(
                Path(raw),
                obligation_statement="По введённому наименованию система показывает подходящие организации DaData.",
            )
            fixture.write_verified_dadata_fixture()
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8")
                .replace(
                    "**Тестовые данные:** Не требуются.",
                    "**Тестовые данные:** `FX-DADATA-PARTNER-001`; запрос и ожидаемая "
                    "подсказка `ПАО СБЕРБАНК`.",
                )
                .replace(
                    "1. Открыть раздел «Партнеры».",
                    "1. Ввести `ПАО СБЕРБАНК` в поле «Наименование партнёра».\n"
                    "2. Выбрать организацию из подсказки DaData.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertNotIn(
                "test-case-dadata-test-data-contract",
                [item.id for item in findings],
            )
            self.assertNotIn(
                "test-case-dadata-fixture-literals",
                [item.id for item in findings],
            )

    def test_validator_requires_literal_alongside_dadata_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(
                Path(raw),
                obligation_statement="По введённому наименованию система показывает подходящие организации DaData.",
            )
            fixture.write_verified_dadata_fixture()
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8")
                .replace(
                    "**Тестовые данные:** Не требуются.",
                    "**Тестовые данные:** Сохранённый fixture `FX-DADATA-PARTNER-001`.",
                )
                .replace(
                    "1. Открыть раздел «Партнеры».",
                    "1. Ввести фрагмент наименования в поле «Наименование партнёра».\n"
                    "2. Выбрать организацию из подсказки DaData.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn(
                "test-case-dadata-fixture-literals",
                [item.id for item in findings if item.blocking],
            )

    def test_validator_rejects_invented_literal_for_verified_dadata_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(
                Path(raw),
                obligation_statement="По введённому наименованию система показывает подходящие организации DaData.",
            )
            fixture.write_verified_dadata_fixture()
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8")
                .replace(
                    "**Тестовые данные:** Не требуются.",
                    "**Тестовые данные:** `FX-DADATA-PARTNER-001`; запрос `ООО «Тестовый партнёр»`.",
                )
                .replace(
                    "1. Открыть раздел «Партнеры».",
                    "1. Ввести `ООО «Тестовый партнёр»` в поле «Наименование партнёра».\n"
                    "2. Выбрать организацию из подсказки DaData.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn(
                "test-case-dadata-fixture-literal-mismatch",
                [item.id for item in findings if item.blocking],
            )

    def test_validator_allows_missing_dadata_fixture_without_invented_literal(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(
                Path(raw),
                obligation_statement="По введённому наименованию система показывает подходящие организации DaData.",
            )
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8")
                .replace("**Статус исполнения:** ready", "**Статус исполнения:** needs-test-data")
                .replace(
                    "**Тестовые данные:** Не требуются.",
                    "**Тестовые данные:** `FX-DADATA-PARTNER-001` не предоставлен. "
                    "Требуемый профиль: юридическое лицо с заполненными наименованием и ИНН в ответе DaData. "
                    "Способ подготовки: включить интеграцию DaData в тестовом контуре и сохранить ответ как fixture прогона.",
                )
                .replace(
                    "1. Открыть раздел «Партнеры».",
                    "1. Ввести поисковую строку из подготовленного профиля в поле «Наименование партнёра».\n"
                    "2. Выбрать организацию из подсказки DaData.",
                ),
                encoding="utf-8",
            )
            fixture.matrix.write_text(
                fixture.matrix.read_text(encoding="utf-8").replace(
                    "| Positive | High | ready |", "| Positive | High | needs-test-data |"
                ),
                encoding="utf-8",
            )
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["execution_setups"][0]["availability"] = "needs-test-data"
            write_json(fixture.obligations, obligations)
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            blocking_ids = [item.id for item in findings if item.blocking]
            self.assertNotIn("test-case-dadata-unverified-literal", blocking_ids)
            self.assertNotIn("test-case-dadata-test-data-contract", blocking_ids)

    def test_validator_rejects_dadata_precondition_that_repeats_trigger(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(
                Path(raw),
                obligation_statement="После выбора подсказки DaData система автоматически заполняет наименование.",
            )
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8")
                .replace(
                    "**Предусловия:** Пользователь вошел в систему.",
                    "**Предусловия:** Пользователь вошел в систему; получен список DaData по наименованию.",
                )
                .replace(
                    "**Тестовые данные:** Не требуются.",
                    "**Тестовые данные:** Требуемый профиль: юридическое лицо с заполненными "
                    "наименованием и ИНН в ответе DaData. Способ подготовки: включить "
                    "интеграцию DaData в тестовом контуре и сохранить выбранную подсказку.",
                )
                .replace(
                    "1. Открыть раздел «Партнеры».",
                    "1. Ввести поисковый запрос в поле «Наименование партнёра».\n"
                    "2. Выбрать подсказку DaData.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn(
                "test-case-dadata-precondition-duplicates-trigger",
                [item.id for item in findings if item.blocking],
            )

    def test_validator_rejects_frozen_profile_process_language(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "**Тестовые данные:** Не требуются.",
                    "**Тестовые данные:** frozen profile подготовлен до прогона.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn(
                "test-case-process-language-frozen-profile",
                [item.id for item in findings if item.blocking],
            )

    def test_validator_requires_section_number_and_total(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "**Номер в разделе:** 1 из 1\n", ""
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(
                package_root=fixture.root, workflow_state_path=fixture.state
            )
            self.assertIn(
                "test-case-section-numbering-missing",
                [item.id for item in findings if item.blocking],
            )

    def test_validator_rejects_unsaved_value_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "**Тестовые данные:** Не требуются.",
                    "**Тестовые данные:** Несохранённое значение: `Несохранённое значение`.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(
                package_root=fixture.root, workflow_state_path=fixture.state
            )
            self.assertIn(
                "test-case-test-data-runtime-placeholder",
                [item.id for item in findings if item.blocking],
            )

    def test_validator_rejects_edit_tc_process_marker(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "**Тестовые данные:** Не требуются.",
                    "**Тестовые данные:** Исходное значение для edit TC: `Москва`.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(
                package_root=fixture.root, workflow_state_path=fixture.state
            )
            self.assertIn(
                "test-case-process-language-tc-marker",
                [item.id for item in findings if item.blocking],
            )

    def test_validator_requires_no_save_persistence_oracle(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["obligations"][0]["statement"] = (
                "При нажатии «Отменить» карточка закрывается без сохранения."
            )
            write_json(fixture.obligations, obligations)
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8")
                .replace(
                    "1. Открыть раздел «Партнеры».",
                    "1. Нажать «Отменить».\n2. Повторно открыть карточку добавления.",
                )
                .replace(
                    "Открывается раздел «Партнеры».", "Карточка закрыта."
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(
                package_root=fixture.root, workflow_state_path=fixture.state
            )
            self.assertIn(
                "test-case-no-save-persistence-oracle",
                [item.id for item in findings if item.blocking],
            )

    def test_validator_requires_system_lifecycle_for_successful_create(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["obligations"][0]["execution_contexts"][0]["id"] = "CTX-CARD-SAVE"
            obligations["obligations"][0]["execution_contexts"][0]["flow_kind"] = "create"
            write_json(fixture.obligations, obligations)
            fixture.matrix.write_text(
                fixture.matrix.read_text(encoding="utf-8").replace(
                    "CTX-OPEN-MENU", "CTX-CARD-SAVE"
                ),
                encoding="utf-8",
            )
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8")
                .replace("CTX-OPEN-MENU", "CTX-CARD-SAVE")
                .replace(
                    "1. Открыть раздел «Партнеры».", "1. Нажать «Сохранить»."
                )
                .replace("Открывается раздел «Партнеры».", "Партнер создан."),
                encoding="utf-8",
            )
            _, findings = validate_scope(
                package_root=fixture.root, workflow_state_path=fixture.state
            )
            finding_ids = [item.id for item in findings if item.blocking]
            self.assertIn("test-case-successful-create-key-missing", finding_ids)
            self.assertIn("test-case-successful-create-initial-state-missing", finding_ids)
            self.assertIn("test-case-successful-create-cleanup-missing", finding_ids)

    def test_validator_requires_valid_package_id(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "**package_id:** WP-01", "**package_id:** package-menu"
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn("test-case-package-id", [item.id for item in findings if item.blocking])

    def test_validator_requires_package_id(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "**package_id:** WP-01\n", ""
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn("test-case-required-field", [item.id for item in findings if item.blocking])

    def test_validator_rejects_only_mixed_create_edit_title(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["obligations"][0]["execution_contexts"][0]["id"] = "CTX-CREATE"
            obligations["obligations"][0]["execution_contexts"][0]["flow_kind"] = "create"
            write_json(fixture.obligations, obligations)
            fixture.matrix.write_text(
                fixture.matrix.read_text(encoding="utf-8").replace("CTX-OPEN-MENU", "CTX-CREATE"),
                encoding="utf-8",
            )
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace("CTX-OPEN-MENU", "CTX-CREATE").replace(
                    "**Название:** Открытие раздела «Партнеры»",
                    "**Название:** При создании и редактировании открывается раздел «Партнеры».",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn("test-case-title-context-mismatch", [item.id for item in findings if item.blocking])

            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "**Название:** При создании и редактировании открывается раздел «Партнеры».",
                    "**Название:** При создании поле доступно для редактирования.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertNotIn("test-case-title-context-mismatch", [item.id for item in findings if item.blocking])

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
                + "| MTX-002 | SCN-002 | OBL-001 | CTX-OPEN-MENU — Открытие раздела из меню | Пункт меню «Партнеры» | Доступность пункта меню | Нажатие пункта меню | Пункт меню «Партнеры» доступен пользователю. | Пользователь вошёл в систему. | Не требуется: состояние задано предусловием. | Открыть пункт меню «Партнеры» с граничным значением. | Открывается раздел «Партнеры» для граничного значения. | SETUP-ACTOR-001 — пользователь с доступом к модулю. | Positive | High | ready | TC-MENU-002 |\n",
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

    def test_validator_requires_explicit_scenario_consolidation_for_shared_tc(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            shared_context = {
                "id": "CTX-CREATE",
                "label": "Создание карточки партнера",
                "flow_kind": "create",
                "required_setup_kinds": ["actor"],
                "setup_ids": ["SETUP-ACTOR-001"],
            }
            obligations["obligations"] = [
                {
                    "id": "OBL-001",
                    "source_anchor": "Таблица 6, строка «КПП».",
                    "statement": "Поле «КПП» доступно для редактирования.",
                    "risk_flags": [],
                    "execution_contexts": [shared_context],
                },
                {
                    "id": "OBL-002",
                    "source_anchor": "Таблица 6, строка «КПП», тип значения.",
                    "statement": "Поле «КПП» допускает ручной ввод.",
                    "risk_flags": [],
                    "execution_contexts": [shared_context],
                },
            ]
            write_json(fixture.obligations, obligations)
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["contract_versions"]["scenario_consolidation"] = (
                SCENARIO_CONSOLIDATION_CONTRACT_VERSION
            )
            state["scenario_consolidation"] = []
            write_json(fixture.state, state)
            header = (
                "# Матрица тест-дизайна\n\n"
                "| Проверка | Идентификатор сценария | Обязательство ФТ | Контекст исполнения | Проверяемый элемент | Домен проверки | Способ взаимодействия | Проверяемое правило | Исходное состояние | Формирование состояния | Проверяемое действие | Ожидаемый результат | Нужные предпосылки | Тип | Приоритет | Статус исполнения | Планируемый TC-ID |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
            )
            rows = (
                "| MTX-001 | SCN-001 | OBL-001 | CTX-CREATE — Создание карточки партнера | Поле «КПП» | Редактируемость | Текстовый ввод | Поле «КПП» доступно для редактирования. | Открыта новая карточка партнера. | Не требуется: карточка открыта в предусловии. | Ввести значение в поле «КПП», затем заменить его. | Поле «КПП» принимает измененное значение. | SETUP-ACTOR-001 — пользователь с доступом. | Positive | Medium | ready | TC-CARD-001 |\n"
                "| MTX-002 | SCN-002 | OBL-002 | CTX-CREATE — Создание карточки партнера | Поле «КПП» | Ручной ввод | Текстовый ввод | Поле «КПП» допускает ручной ввод. | Открыта новая карточка партнера. | Не требуется: карточка открыта в предусловии. | Вручную ввести значение в поле «КПП». | Поле «КПП» принимает значение, введенное вручную. | SETUP-ACTOR-001 — пользователь с доступом. | Positive | Medium | ready | TC-CARD-002 |\n"
            )
            fixture.matrix.write_text(header + rows, encoding="utf-8")
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertNotIn(
                "scenario-consolidation-exact-candidate-undecided",
                [item.id for item in findings],
            )

            exact_rows = (header + rows).replace(
                "Поле «КПП» допускает ручной ввод.",
                "Поле «КПП» доступно для редактирования.",
            ).replace(
                "Вручную ввести значение в поле «КПП».",
                "Ввести значение в поле «КПП», затем заменить его.",
            ).replace(
                "Поле «КПП» принимает значение, введенное вручную.",
                "Поле «КПП» принимает измененное значение.",
            )
            fixture.matrix.write_text(exact_rows, encoding="utf-8")
            parsed_rows, parsed_errors = parse_matrix_rows(fixture.matrix)
            self.assertFalse(parsed_errors)
            self.assertEqual(1, len(matrix_exact_duplicate_groups(parsed_rows)))
            loaded_state = load_workflow_state(fixture.state, fixture.root)
            direct_findings, direct_consolidation = scenario_consolidation_contract(
                state=loaded_state,
                rows_by_scenario={row["Идентификатор сценария"]: row for row in parsed_rows},
                artifact="workflow-state.json",
            )
            self.assertTrue(direct_consolidation["enabled"])
            self.assertFalse(direct_findings)
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn(
                "scenario-consolidation-exact-candidate-undecided",
                [item.id for item in findings if item.blocking],
            )

            current_state = json.loads(fixture.state.read_text(encoding="utf-8"))
            current_state["contract_versions"].pop("scenario_consolidation")
            current_state.pop("scenario_consolidation")
            write_json(fixture.state, current_state)
            _, findings = validate_scope(
                package_root=fixture.root, workflow_state_path=fixture.state
            )
            self.assertIn(
                "matrix-exact-duplicate-consolidation-missing",
                [item.id for item in findings if item.blocking],
            )

            merged_rows = exact_rows.replace("TC-CARD-002", "TC-CARD-001")
            fixture.matrix.write_text(merged_rows, encoding="utf-8")
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["contract_versions"]["scenario_consolidation"] = (
                SCENARIO_CONSOLIDATION_CONTRACT_VERSION
            )
            state["scenario_consolidation"] = [{
                "id": "CON-001",
                "decision": "merge-parameterized",
                "scenario_ids": ["SCN-001", "SCN-002"],
                "planned_tc_id": "TC-CARD-001",
                "source_anchor": "Таблица 6, строка «КПП».",
                "rationale": "Обе строки описывают одно и то же действие и результат.",
                "parameterization_basis": "эквивалентные значения одного класса",
            }]
            write_json(fixture.state, state)
            fixture.tc.write_text(
                "## TC-CARD-001\n"
                "**Название:** Изменение КПП при создании карточки партнера\n"
                "**Тип:** Positive\n"
                "**Приоритет:** Medium\n"
                "**package_id:** WP-01\n"
                "**Статус исполнения:** ready\n"
                "**Контекст исполнения:** `CTX-CREATE` — создание карточки партнера.\n"
                "**Трассировка:** `OBL-001`; `OBL-002`; `SCN-001`; `SCN-002`; Таблица 6.\n"
                "**Цель:** Проверить изменение КПП.\n"
                "**Предусловия:** Открыта новая карточка партнера.\n"
                "**Тестовые данные:** Первое значение КПП: `773601001`; новое значение КПП: `773601002`.\n"
                "**Шаги:**\n"
                "1. Ввести в поле «КПП» `773601001`.\n"
                "2. Заменить значение поля «КПП» на `773601002`.\n"
                "**Итоговый ожидаемый результат:** В поле «КПП» отображается `773601002`.\n",
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            finding_ids = [item.id for item in findings if item.blocking]
            self.assertIn("scenario-consolidation-domain", finding_ids)

    def test_parameterized_consolidation_requires_one_element_domain_and_interaction(self) -> None:
        def state_for(scenario_ids: list[str]) -> dict[str, object]:
            return {
                "contract_versions": {
                    "scenario_consolidation": SCENARIO_CONSOLIDATION_CONTRACT_VERSION,
                },
                "scenario_consolidation": [{
                    "id": "CON-001",
                    "decision": "merge-parameterized",
                    "scenario_ids": scenario_ids,
                    "planned_tc_id": "TC-CARD-001",
                    "source_anchor": "Таблица 6, строка «КПП».",
                    "rationale": "Параметры относятся к одной проверке.",
                    "parameterization_basis": "границы одного правила",
                }],
            }

        common = {
            "Контекст исполнения": "CTX-CREATE — Создание карточки партнера",
            "Проверяемый элемент": "Поле «КПП»",
            "Домен проверки": "Границы длины",
            "Способ взаимодействия": "Текстовый ввод",
            "Тип": "Negative",
            "Статус исполнения": "ready",
            "Планируемый TC-ID": "TC-CARD-001",
        }
        same_rule_rows = {
            "SCN-001": {**common, "Идентификатор сценария": "SCN-001"},
            "SCN-002": {**common, "Идентификатор сценария": "SCN-002"},
        }
        findings, _ = scenario_consolidation_contract(
            state=state_for(["SCN-001", "SCN-002"]),
            rows_by_scenario=same_rule_rows,
            artifact="workflow-state.json",
        )
        self.assertEqual([], [item.id for item in findings])

        different_field_rows = {
            **same_rule_rows,
            "SCN-002": {
                **same_rule_rows["SCN-002"],
                "Проверяемый элемент": "Поле «ИНН»",
            },
        }
        findings, _ = scenario_consolidation_contract(
            state=state_for(["SCN-001", "SCN-002"]),
            rows_by_scenario=different_field_rows,
            artifact="workflow-state.json",
        )
        self.assertIn("scenario-consolidation-element", [item.id for item in findings])

        different_domain_rows = {
            **same_rule_rows,
            "SCN-002": {
                **same_rule_rows["SCN-002"],
                "Домен проверки": "Размер файла",
                "Способ взаимодействия": "Выбор файла",
            },
        }
        findings, _ = scenario_consolidation_contract(
            state=state_for(["SCN-001", "SCN-002"]),
            rows_by_scenario=different_domain_rows,
            artifact="workflow-state.json",
        )
        finding_ids = [item.id for item in findings]
        self.assertIn("scenario-consolidation-domain", finding_ids)
        self.assertIn("scenario-consolidation-interaction", finding_ids)

    def test_composite_result_consolidation_allows_fields_of_one_autofill(self) -> None:
        rows = {
            "SCN-001": {
                "Идентификатор сценария": "SCN-001",
                "Контекст исполнения": "CTX-CREATE — Создание карточки партнера",
                "Проверяемый элемент": "Поле «Наименование партнера»",
                "Домен проверки": "Автозаполнение после выбора подсказки",
                "Способ взаимодействия": "Выбор подсказки DaData",
                "Исходное состояние": "Открыта новая карточка партнера.",
                "Формирование состояния": "Ввести запрос `СБЕРБАНК`.",
                "Проверяемое действие": "Выбрать подсказку `ПАО СБЕРБАНК`.",
                "Тип": "Positive",
                "Статус исполнения": "needs-test-data",
                "Планируемый TC-ID": "TC-CARD-AUTOFILL-001",
            },
            "SCN-002": {
                "Идентификатор сценария": "SCN-002",
                "Контекст исполнения": "CTX-CREATE — Создание карточки партнера",
                "Проверяемый элемент": "Поле «ИНН»",
                "Домен проверки": "Автозаполнение после выбора подсказки",
                "Способ взаимодействия": "Выбор подсказки DaData",
                "Исходное состояние": "Открыта новая карточка партнера.",
                "Формирование состояния": "Ввести запрос `СБЕРБАНК`.",
                "Проверяемое действие": "Выбрать подсказку `ПАО СБЕРБАНК`.",
                "Тип": "Positive",
                "Статус исполнения": "needs-test-data",
                "Планируемый TC-ID": "TC-CARD-AUTOFILL-001",
            },
        }
        state = {
            "contract_versions": {
                "scenario_consolidation": SCENARIO_CONSOLIDATION_CONTRACT_VERSION,
            },
            "scenario_consolidation": [{
                "id": "CON-AUTOFILL-001",
                "decision": "merge-parameterized",
                "scenario_ids": ["SCN-001", "SCN-002"],
                "planned_tc_id": "TC-CARD-AUTOFILL-001",
                "source_anchor": "Таблица 6, автозаполнение карточки партнера.",
                "rationale": "Одно действие выбора подсказки создаёт один составной результат автозаполнения карточки.",
                "parameterization_basis": "поля одного составного результата",
                "composite_result": "Карточка заполнена данными выбранной организации.",
                "field_inventory": ["Поле «Наименование партнера»", "Поле «ИНН»"],
            }],
        }
        findings, consolidation = scenario_consolidation_contract(
            state=state,
            rows_by_scenario=rows,
            artifact="workflow-state.json",
        )
        self.assertEqual([], [item.id for item in findings])
        self.assertEqual(
            "поля одного составного результата",
            consolidation["consolidation_by_tc"]["TC-CARD-AUTOFILL-001"]["parameterization_basis"],
        )
        tc_body = (
            "**Итоговый ожидаемый результат:** Карточка заполнена данными выбранной организации.\n\n"
            "| Поле | Ожидаемое значение |\n"
            "| --- | --- |\n"
            "| Наименование партнера | `ПАО СБЕРБАНК` |\n"
            "| ИНН | `7707083893` |"
        )
        self.assertTrue(has_composite_result_table(
            tc_body,
            consolidation["consolidation_by_tc"]["TC-CARD-AUTOFILL-001"]["field_inventory"],
        ))

    def test_composite_result_consolidation_requires_full_field_inventory_and_table(self) -> None:
        rows = {
            "SCN-001": {
                "Идентификатор сценария": "SCN-001",
                "Контекст исполнения": "CTX-CREATE — Создание карточки партнера",
                "Проверяемый элемент": "Поле «Наименование партнера»",
                "Домен проверки": "Автозаполнение после выбора подсказки",
                "Способ взаимодействия": "Выбор подсказки DaData",
                "Исходное состояние": "Открыта новая карточка партнера.",
                "Формирование состояния": "Ввести запрос `СБЕРБАНК`.",
                "Проверяемое действие": "Выбрать подсказку `ПАО СБЕРБАНК`.",
                "Тип": "Positive",
                "Статус исполнения": "needs-test-data",
                "Планируемый TC-ID": "TC-CARD-AUTOFILL-001",
            },
            "SCN-002": {
                "Идентификатор сценария": "SCN-002",
                "Контекст исполнения": "CTX-CREATE — Создание карточки партнера",
                "Проверяемый элемент": "Поле «ИНН»",
                "Домен проверки": "Автозаполнение после выбора подсказки",
                "Способ взаимодействия": "Выбор подсказки DaData",
                "Исходное состояние": "Открыта новая карточка партнера.",
                "Формирование состояния": "Ввести запрос `СБЕРБАНК`.",
                "Проверяемое действие": "Выбрать подсказку `ПАО СБЕРБАНК`.",
                "Тип": "Positive",
                "Статус исполнения": "needs-test-data",
                "Планируемый TC-ID": "TC-CARD-AUTOFILL-001",
            },
        }
        state = {
            "contract_versions": {
                "scenario_consolidation": SCENARIO_CONSOLIDATION_CONTRACT_VERSION,
            },
            "scenario_consolidation": [{
                "id": "CON-AUTOFILL-001",
                "decision": "merge-parameterized",
                "scenario_ids": ["SCN-001", "SCN-002"],
                "planned_tc_id": "TC-CARD-AUTOFILL-001",
                "source_anchor": "Таблица 6, автозаполнение карточки партнера.",
                "rationale": "Одно действие выбора подсказки создаёт один составной результат автозаполнения карточки.",
                "parameterization_basis": "поля одного составного результата",
                "composite_result": "Карточка заполнена данными выбранной организации.",
                "field_inventory": ["Поле «Наименование партнера»"],
            }],
        }
        findings, _ = scenario_consolidation_contract(
            state=state,
            rows_by_scenario=rows,
            artifact="workflow-state.json",
        )
        self.assertIn(
            "scenario-consolidation-composite-result-contract",
            [item.id for item in findings if item.blocking],
        )
        self.assertFalse(has_composite_result_table(
            "| Поле | Ожидаемое значение |\n| --- | --- |\n| Наименование партнера | `ПАО СБЕРБАНК` |",
            ["Поле «Наименование партнера»", "Поле «ИНН»"],
        ))

    def test_validator_maps_internal_check_to_observable_result(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            shared_context = obligations["obligations"][0]["execution_contexts"][0]
            obligations["obligations"] = [
                {
                    "id": "OBL-001",
                    "source_anchor": "Таблица 7, AS.36.",
                    "statement": "При сохранении система проверяет уникальность партнера.",
                    "risk_flags": [],
                    "execution_contexts": [shared_context],
                },
                {
                    "id": "OBL-002",
                    "source_anchor": "Таблица 7, AS.37.",
                    "statement": "При неуспешной проверке система выводит сообщение «Ошибка уникальности».",
                    "risk_flags": [],
                    "execution_contexts": [shared_context],
                },
            ]
            write_json(fixture.obligations, obligations)
            header = (
                "# Матрица тест-дизайна\n\n"
                "| Проверка | Идентификатор сценария | Обязательство ФТ | Контекст исполнения | Проверяемый элемент | Домен проверки | Способ взаимодействия | Проверяемое правило | Исходное состояние | Формирование состояния | Проверяемое действие | Ожидаемый результат | Нужные предпосылки | Тип | Приоритет | Статус исполнения | Планируемый TC-ID |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
            )
            rows = (
                "| MTX-001 | SCN-001 | OBL-001 | CTX-OPEN-MENU — Открытие раздела из меню | Карточка партнера | Проверка уникальности | Нажатие «Сохранить» | Перед сохранением проверяется уникальность. | Открыта новая карточка с дублирующими данными. | Ввести дублирующее наименование. | Нажать «Сохранить». | Внутренняя проверка не имеет самостоятельного наблюдаемого результата. | SETUP-ACTOR-001 — пользователь с доступом к модулю. | Negative | High | ready | TC-MENU-001 |\n"
                "| MTX-002 | SCN-002 | OBL-002 | CTX-OPEN-MENU — Открытие раздела из меню | Карточка партнера | Проверка уникальности | Нажатие «Сохранить» | При неуспешной проверке выводится сообщение. | Открыта новая карточка с дублирующими данными. | Ввести дублирующее наименование. | Нажать «Сохранить». | Отображается сообщение «Ошибка уникальности». | SETUP-ACTOR-001 — пользователь с доступом к модулю. | Negative | High | ready | TC-MENU-001 |\n"
            )
            fixture.matrix.write_text(header + rows, encoding="utf-8")
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["contract_versions"]["scenario_consolidation"] = (
                SCENARIO_CONSOLIDATION_CONTRACT_VERSION
            )
            state["scenario_consolidation"] = []
            write_json(fixture.state, state)
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            finding_ids = [item.id for item in findings if item.blocking]
            self.assertIn("matrix-internal-oracle-needs-observable-coverage", finding_ids)
            self.assertIn("scenario-consolidation-shared-tc-without-decision", finding_ids)

            state["scenario_consolidation"] = [{
                "id": "CON-001",
                "decision": "covered-by-observable-result",
                "scenario_ids": ["SCN-001", "SCN-002"],
                "planned_tc_id": "TC-MENU-001",
                "observable_scenario_id": "SCN-002",
                "source_anchor": "Таблица 7, AS.36–AS.37.",
                "rationale": "Внутренняя проверка подтверждается наблюдаемым сообщением об ошибке.",
            }]
            state["reviews"] = []
            write_json(fixture.state, state)
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            finding_ids = [item.id for item in findings if item.blocking]
            self.assertNotIn("matrix-internal-oracle-needs-observable-coverage", finding_ids)
            self.assertNotIn("scenario-consolidation-shared-tc-without-decision", finding_ids)
            self.assertIn(
                "matrix-review-required-before-test-cases",
                finding_ids,
            )

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

    def test_validator_requires_all_requirement_codes_from_obligation_in_tc_trace(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["obligations"][0]["source_anchor"] = (
                "XHTML, Таблица 7, AS.36; раздел 9.3, AS.5."
            )
            write_json(fixture.obligations, obligations)

            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            finding_ids = [item.id for item in findings if item.blocking]
            self.assertIn("test-case-source-code-trace", finding_ids)

            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "`OBL-001`; `SCN-001`; Раздел 9.1.",
                    "`OBL-001`; `SCN-001`; AS 36; Раздел 9.1.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            source_code_findings = [
                item for item in findings if item.id == "test-case-source-code-trace"
            ]
            self.assertEqual(1, len(source_code_findings))
            self.assertIn("AS.5", source_code_findings[0].details)

            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "AS 36; Раздел 9.1.", "AS 36; AS.5; Раздел 9.1."
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertNotIn(
                "test-case-source-code-trace",
                [item.id for item in findings if item.blocking],
            )

    def test_validator_allows_trace_without_requirement_code_when_anchor_has_none(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertNotIn(
                "test-case-source-code-trace",
                [item.id for item in findings if item.blocking],
            )

    def test_requirement_code_parser_supports_known_ft_code_forms(self) -> None:
        self.assertEqual(
            {
                "AS:36": "AS.36",
                "BSR:128": "BSR 128",
                "GSR:22": "GSR 22",
                "DIT:007": "DIT 007",
            },
            requirement_codes("AS.36; BSR 128; GSR.22; DIT 007"),
        )

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

    def test_validator_requires_search_and_duplicate_save_trigger_steps(self) -> None:
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

            input_autofill = PracticalV09Fixture(
                Path(raw) / "input-autofill",
                obligation_statement=(
                    "При вводе ИНН система автоматически заполняет наименование данными DaData."
                ),
            )
            input_autofill.matrix.write_text(
                input_autofill.matrix.read_text(encoding="utf-8").replace(
                    "Не требуется: состояние задано предусловием.",
                    "Очистить поле «ИНН».",
                ).replace(
                    "Открыть пункт меню «Партнеры».",
                    "Ввести ИНН из сохранённого ответа DaData.",
                ),
                encoding="utf-8",
            )
            input_autofill.tc.write_text(
                input_autofill.tc.read_text(encoding="utf-8").replace(
                    "1. Открыть раздел «Партнеры».",
                    "1. Очистить поле «ИНН».\n"
                    "2. Ввести ИНН из сохранённого ответа DaData.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(
                package_root=input_autofill.root,
                workflow_state_path=input_autofill.state,
            )
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

            pre_save_hint = PracticalV09Fixture(
                Path(raw) / "duplicate-hint",
                obligation_statement=(
                    "При создании нового партнёра с уже существующим названием "
                    "система выдаёт подсказку о существовании партнёра с таким названием."
                ),
            )
            pre_save_hint.matrix.write_text(
                pre_save_hint.matrix.read_text(encoding="utf-8").replace(
                    "Не требуется: состояние задано предусловием.",
                    "Создать новую карточку партнёра.",
                ).replace(
                    "Открыть пункт меню «Партнеры».",
                    "Ввести название уже существующего партнёра.",
                ),
                encoding="utf-8",
            )
            pre_save_hint.tc.write_text(
                pre_save_hint.tc.read_text(encoding="utf-8").replace(
                    "1. Открыть раздел «Партнеры».",
                    "1. Создать новую карточку партнёра.\n"
                    "2. Ввести в поле «Наименование» название уже существующего партнёра.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(
                package_root=pre_save_hint.root,
                workflow_state_path=pre_save_hint.state,
            )
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
                    "flow_kind": "view",
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

    def test_environment_access_does_not_make_source_complete_case_needs_test_data(self) -> None:
        self.assertEqual(
            "ready",
            derived_execution_status(
                {
                    "required_setup_kinds": ["actor"],
                    "setup_ids": ["SETUP-ACTOR-001"],
                },
                {
                    "SETUP-ACTOR-001": {
                        "kind": "actor",
                        "availability": "provided",
                        "availability_scope": "environment-access",
                    }
                },
            ),
        )

    def test_environment_access_cannot_store_volatile_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["execution_setups"][0]["availability_scope"] = "environment-access"
            obligations["execution_setups"][0]["evidence"] = "URL: https://test.example; логин: qa-user"
            write_json(fixture.obligations, obligations)
            _, findings = validate_scope(
                package_root=fixture.root,
                workflow_state_path=fixture.state,
            )
            self.assertIn(
                "scope-execution-environment-access-secret",
                [item.id for item in findings if item.blocking],
            )

    def test_environment_access_must_be_provided_not_test_data(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["execution_setups"][0]["availability_scope"] = "environment-access"
            obligations["execution_setups"][0]["availability"] = "needs-test-data"
            write_json(fixture.obligations, obligations)
            _, findings = validate_scope(
                package_root=fixture.root,
                workflow_state_path=fixture.state,
            )
            self.assertIn(
                "scope-execution-environment-access-availability",
                [item.id for item in findings if item.blocking],
            )

    def test_canonical_test_case_rejects_setup_and_environment_configuration(self) -> None:
        for volatile_value in (
            "**Предусловия:** Выполнить SETUP-NAV-001.",
            "**Предусловия:** Открыть https://test.example под логином qa-user.",
        ):
            with self.subTest(volatile_value=volatile_value), tempfile.TemporaryDirectory() as raw:
                fixture = PracticalV09Fixture(Path(raw))
                fixture.tc.write_text(
                    fixture.tc.read_text(encoding="utf-8").replace(
                        "**Предусловия:** Пользователь вошел в систему.",
                        volatile_value,
                    ),
                    encoding="utf-8",
                )
                _, findings = validate_scope(
                    package_root=fixture.root,
                    workflow_state_path=fixture.state,
                )
                self.assertIn(
                    "test-case-volatile-environment-reference",
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

    def test_validator_requires_secondary_execution_limitation_in_matrix_and_tc(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["execution_setups"][0]["availability"] = "needs-test-data"
            obligations["execution_setups"].append(
                {
                    "id": "SETUP-NAVIGATION-001",
                    "kind": "navigation",
                    "availability": "candidate-ui-calibration",
                    "evidence": "Точное название элемента входа требует UI-калибровки.",
                }
            )
            context = obligations["obligations"][0]["execution_contexts"][0]
            context["required_setup_kinds"] = ["actor", "navigation"]
            context["setup_ids"] = ["SETUP-ACTOR-001", "SETUP-NAVIGATION-001"]
            write_json(fixture.obligations, obligations)
            fixture.matrix.write_text(
                fixture.matrix.read_text(encoding="utf-8").replace(
                    "| Positive | High | ready |", "| Positive | High | needs-test-data |"
                ),
                encoding="utf-8",
            )
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "**Статус исполнения:** ready", "**Статус исполнения:** needs-test-data"
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            blocking_ids = [item.id for item in findings if item.blocking]
            self.assertIn("matrix-execution-limitations-incomplete", blocking_ids)
            self.assertIn("test-case-execution-limitations-incomplete", blocking_ids)

    def test_validator_blocks_new_card_inside_edit_context(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["obligations"][0]["execution_contexts"][0]["id"] = "CTX-CARD-EDIT"
            obligations["obligations"][0]["execution_contexts"][0]["flow_kind"] = "edit"
            write_json(fixture.obligations, obligations)
            fixture.matrix.write_text(
                fixture.matrix.read_text(encoding="utf-8").replace(
                    "CTX-OPEN-MENU — Открытие раздела из меню",
                    "CTX-CARD-EDIT — Редактирование сохранённой карточки",
                ),
                encoding="utf-8",
            )
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "CTX-OPEN-MENU` — открытие раздела из меню.",
                    "CTX-CARD-EDIT` — редактирование сохранённой карточки.",
                ).replace(
                    "1. Открыть раздел «Партнеры».",
                    "1. Открыть новую карточку партнёра.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn(
                "test-case-edit-context-new-card",
                [item.id for item in findings if item.blocking],
            )

    def test_validator_blocks_explicit_matrix_field_substitution(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.matrix.write_text(
                fixture.matrix.read_text(encoding="utf-8").replace(
                    "Пункт меню «Партнеры» | Доступность пункта меню",
                    "Поле «Дата аккредитации» | Формат даты",
                ),
                encoding="utf-8",
            )
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "1. Открыть раздел «Партнеры».",
                    "1. Ввести дату в поле «Дата начала сотрудничества».",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertIn(
                "test-case-matrix-element-binding",
                [item.id for item in findings if item.blocking],
            )

    def test_validator_accepts_explicit_matrix_field_label_in_tc(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            fixture.matrix.write_text(
                fixture.matrix.read_text(encoding="utf-8").replace(
                    "Пункт меню «Партнеры» | Доступность пункта меню",
                    "Поле «Дата аккредитации» | Формат даты",
                ),
                encoding="utf-8",
            )
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "1. Открыть раздел «Партнеры».",
                    "1. Ввести дату в поле «Дата аккредитации».",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            self.assertNotIn(
                "test-case-matrix-element-binding",
                [item.id for item in findings if item.blocking],
            )

    def test_validator_requires_source_parity_when_pdf_is_bound(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["artifacts"]["source_parity_check"] = "not-created"
            write_json(fixture.state, state)

            _, findings = validate_scope(
                package_root=fixture.root, workflow_state_path=fixture.state
            )
            self.assertIn(
                "workflow-artifact-reference",
                [item.id for item in findings if item.blocking],
            )

    def test_exception_requires_immutable_pre_change_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            exception = fixture.scope_dir / "EXC-001.json"
            write_json(
                exception,
                {
                    "exception_id": "EXC-001",
                    "scope_slug": "menu",
                    "allowed_artifacts": ["test-cases/9.1-menu.md"],
                },
            )
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["artifacts"]["tc_exception"] = relative_to_package(
                fixture.root, exception
            )
            write_json(fixture.state, state)

            _, findings = validate_scope(
                package_root=fixture.root, workflow_state_path=fixture.state
            )
            self.assertIn(
                "exception-pre-change-snapshot-missing",
                [item.id for item in findings if item.blocking],
            )

    def test_exception_snapshot_is_bound_to_review_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            snapshot = create_pre_write_snapshot(
                ft_package_root=fixture.root,
                scope_slug="menu",
                snapshot_id="before-exception",
                sources=[fixture.tc],
                reason="Проверка контракта исключения до целевой доработки.",
            )
            snapshot_dir = Path(str(snapshot["snapshot_dir"]))
            snapshot_manifest = snapshot_dir / "snapshot-manifest.yaml"
            exception = fixture.scope_dir / "EXC-001.json"
            write_json(
                exception,
                {
                    "exception_id": "EXC-001",
                    "scope_slug": "menu",
                    "allowed_artifacts": ["test-cases/9.1-menu.md"],
                    "pre_change_snapshot": {
                        "path": relative_to_package(fixture.root, snapshot_dir),
                        "manifest_sha256": sha256_file(snapshot_manifest),
                    },
                },
            )
            state = json.loads(fixture.state.read_text(encoding="utf-8"))
            state["artifacts"]["tc_exception"] = relative_to_package(
                fixture.root, exception
            )
            write_json(fixture.state, state)
            context, findings = validate_scope(
                package_root=fixture.root, workflow_state_path=fixture.state
            )
            self.assertFalse(
                [item for item in findings if item.id.startswith("exception-pre-change-snapshot")]
            )
            write_json(fixture.scope_dir / "validator-report.json", build_validator_report(context, findings))
            manifest = build_review_manifest(
                package_root=fixture.root,
                workflow_state_path=fixture.state,
                review_mode="test-cases",
                controller_thread_id="019feebf-3cde-79d2-9f87-ba9c61ff7b13",
                code_branch="codex/test",
                code_commit="abc123",
                contract_digest="contract",
            )
            input_paths = {item["path"] for item in manifest["inputs"]}
            self.assertIn(relative_to_package(fixture.root, fixture.source_parity), input_paths)
            self.assertIn(relative_to_package(fixture.root, exception), input_paths)
            self.assertIn(relative_to_package(fixture.root, snapshot_manifest), input_paths)
            self.assertTrue(
                any(path.endswith("files/test-cases/9.1-menu.md") for path in input_paths)
            )

    def test_validator_accepts_secondary_execution_limitation_without_second_status(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            obligations["execution_setups"][0]["availability"] = "needs-test-data"
            obligations["execution_setups"].append(
                {
                    "id": "SETUP-NAVIGATION-001",
                    "kind": "navigation",
                    "availability": "candidate-ui-calibration",
                    "evidence": "Точное название элемента входа требует UI-калибровки.",
                }
            )
            context = obligations["obligations"][0]["execution_contexts"][0]
            context["required_setup_kinds"] = ["actor", "navigation"]
            context["setup_ids"] = ["SETUP-ACTOR-001", "SETUP-NAVIGATION-001"]
            write_json(fixture.obligations, obligations)
            fixture.matrix.write_text(
                fixture.matrix.read_text(encoding="utf-8")
                .replace(
                    "| Нужные предпосылки | Тип |",
                    "| Нужные предпосылки | Ограничения исполнения | Тип |",
                )
                .replace(
                    "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                    "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                )
                .replace(
                    "| SETUP-ACTOR-001 — пользователь с доступом к модулю. | Positive | High | ready |",
                    "| SETUP-ACTOR-001 — пользователь с доступом к модулю; SETUP-NAVIGATION-001 — точный элемент входа. | "
                    "Требуется UI-калибровка элемента входа: SETUP-NAVIGATION-001. | Positive | High | needs-test-data |",
                ),
                encoding="utf-8",
            )
            fixture.tc.write_text(
                fixture.tc.read_text(encoding="utf-8").replace(
                    "**Статус исполнения:** ready",
                    "**Статус исполнения:** needs-test-data\n"
                    "**Ограничения исполнения:** Требуется UI-калибровка элемента входа: SETUP-NAVIGATION-001.",
                ),
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            blocking_ids = [item.id for item in findings if item.blocking]
            self.assertNotIn("matrix-execution-limitations-incomplete", blocking_ids)
            self.assertNotIn("test-case-execution-limitations-incomplete", blocking_ids)

    def test_validator_requires_common_rejection_result_for_every_invalid_class(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = PracticalV09Fixture(Path(raw))
            obligations = json.loads(fixture.obligations.read_text(encoding="utf-8"))
            shared_context = obligations["obligations"][0]["execution_contexts"]
            obligations["obligations"] = [
                {
                    "id": "OBL-FILE-ERROR",
                    "source_anchor": "AS.35, требование к документу",
                    "statement": "Для документа, не соответствующего требованиям, система выводит сообщение «Документ не соответствует требованиям». ",
                    "common_result_for_obligation_ids": ["OBL-FILE-FORMAT", "OBL-FILE-SIZE"],
                    "risk_flags": [],
                    "execution_contexts": shared_context,
                },
                {
                    "id": "OBL-FILE-FORMAT",
                    "source_anchor": "AS.35, допустимый формат",
                    "statement": "Система не принимает документ недопустимого формата.",
                    "risk_flags": [],
                    "execution_contexts": shared_context,
                },
                {
                    "id": "OBL-FILE-SIZE",
                    "source_anchor": "AS.35, размер файла",
                    "statement": "Система не принимает документ размером более 40 МБ.",
                    "risk_flags": [],
                    "execution_contexts": shared_context,
                },
            ]
            write_json(fixture.obligations, obligations)
            fixture.matrix.write_text(
                "# Матрица тест-дизайна\n\n"
                "| Проверка | Идентификатор сценария | Обязательство ФТ | Контекст исполнения | Проверяемый элемент | Домен проверки | Способ взаимодействия | Проверяемое правило | Исходное состояние | Формирование состояния | Проверяемое действие | Ожидаемый результат | Нужные предпосылки | Тип | Приоритет | Статус исполнения | Планируемый TC-ID |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
                "| MTX-ERROR | SCN-ERROR | OBL-FILE-ERROR | CTX-OPEN-MENU — Открытие раздела из меню | Документ | Ошибка | Загрузка | Общий результат отказа | Экран открыт. | Выбрать неподходящий файл. | Прикрепить файл. | Выводится «Документ не соответствует требованиям». | SETUP-ACTOR-001 — пользователь. | Negative | High | ready | TC-FILE-ERROR |\n"
                "| MTX-FORMAT | SCN-FORMAT | OBL-FILE-FORMAT | CTX-OPEN-MENU — Открытие раздела из меню | Документ | Формат | Загрузка | Недопустимый формат | Экран открыт. | Выбрать файл `.docx`. | Прикрепить файл. | Файл не прикрепляется. | SETUP-ACTOR-001 — пользователь. | Negative | High | ready | TC-FILE-FORMAT |\n"
                "| MTX-SIZE | SCN-SIZE | OBL-FILE-SIZE | CTX-OPEN-MENU — Открытие раздела из меню | Документ | Размер | Загрузка | Размер более 40 МБ | Экран открыт. | Выбрать файл размером `41 МБ`. | Прикрепить файл. | Файл не прикрепляется. | SETUP-ACTOR-001 — пользователь. | Negative | High | ready | TC-FILE-SIZE |\n",
                encoding="utf-8",
            )
            fixture.tc.write_text(
                "## TC-FILE-ERROR\n"
                "**Название:** Общий результат отказа\n**Тип:** Negative\n**Приоритет:** High\n**package_id:** WP-01\n"
                "**Статус исполнения:** ready\n**Контекст исполнения:** `CTX-OPEN-MENU` — открытие.\n"
                "**Трассировка:** `OBL-FILE-ERROR`; `SCN-ERROR`; `AS.35`.\n**Цель:** Проверить сообщение.\n"
                "**Предусловия:** Экран открыт.\n**Тестовые данные:** Файл `.docx`.\n"
                "**Шаги:**\n1. Прикрепить файл `.docx`.\n"
                "**Итоговый ожидаемый результат:** Выводится «Документ не соответствует требованиям».\n\n"
                "## TC-FILE-FORMAT\n"
                "**Название:** Отказ для недопустимого формата\n**Тип:** Negative\n**Приоритет:** High\n**package_id:** WP-01\n"
                "**Статус исполнения:** ready\n**Контекст исполнения:** `CTX-OPEN-MENU` — открытие.\n"
                "**Трассировка:** `OBL-FILE-FORMAT`; `SCN-FORMAT`; `AS.35`.\n**Цель:** Проверить формат.\n"
                "**Предусловия:** Экран открыт.\n**Тестовые данные:** Файл `.docx`.\n"
                "**Шаги:**\n1. Прикрепить файл `.docx`.\n"
                "**Итоговый ожидаемый результат:** Файл не прикрепляется.\n\n"
                "## TC-FILE-SIZE\n"
                "**Название:** Отказ для файла больше лимита\n**Тип:** Negative\n**Приоритет:** High\n**package_id:** WP-01\n"
                "**Статус исполнения:** ready\n**Контекст исполнения:** `CTX-OPEN-MENU` — открытие.\n"
                "**Трассировка:** `OBL-FILE-SIZE`; `SCN-SIZE`; `AS.35`.\n**Цель:** Проверить размер.\n"
                "**Предусловия:** Экран открыт.\n**Тестовые данные:** Файл размером `41 МБ`.\n"
                "**Шаги:**\n1. Прикрепить файл размером `41 МБ`.\n"
                "**Итоговый ожидаемый результат:** Файл не прикрепляется.\n",
                encoding="utf-8",
            )
            _, findings = validate_scope(package_root=fixture.root, workflow_state_path=fixture.state)
            common_matrix = [
                item.details for item in findings
                if item.id == "matrix-source-message-literal"
            ]
            common_tc = [
                item.details for item in findings
                if item.id == "test-case-common-result-literal"
            ]
            self.assertTrue(any("MTX-FORMAT" in details for details in common_matrix))
            self.assertTrue(any("MTX-SIZE" in details for details in common_matrix))
            self.assertTrue(any("TC-FILE-FORMAT" in details for details in common_tc))
            self.assertTrue(any("TC-FILE-SIZE" in details for details in common_tc))

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
