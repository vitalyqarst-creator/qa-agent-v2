"""Small, deterministic contracts for the compact practical v0.9 route.

The v0.8 practical route accumulated controller artefacts that repeated the
same state in several mutable files.  This module deliberately keeps the
v0.9 control plane narrow: a source manifest, source obligations, one matrix,
canonical test cases, a validator report, review manifests/results and one
workflow state.  It has no dependency on the legacy package-wide validator.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping


ROUTE_VERSION = "practical-v0.9"
ROUTE_TOOL_VERSION = "practical-v0.9.32"
WORKFLOW_STATE_SCHEMA_VERSION = 1
SOURCE_CONTRACT_VERSION = "source-package-v4"
MATRIX_CONTRACT_VERSION = "practical-matrix-v3"
PREVIOUS_MATRIX_CONTRACT_VERSION = "practical-matrix-v2"
LEGACY_MATRIX_CONTRACT_VERSION = "practical-matrix-v1"
MIGRATABLE_MATRIX_CONTRACT_VERSIONS = {
    LEGACY_MATRIX_CONTRACT_VERSION,
    PREVIOUS_MATRIX_CONTRACT_VERSION,
}
SCENARIO_CONSOLIDATION_CONTRACT_VERSION = "scenario-consolidation-v2"
LEGACY_SCENARIO_CONSOLIDATION_CONTRACT_VERSION = "scenario-consolidation-v1"
CONTROLLER_TRIAGE_CONTRACT_VERSION = "controller-triage-v1"
CLARIFICATION_OUTCOME_CONTRACT_VERSION = "clarification-outcome-v1"
EXECUTION_CONTEXT_CONTRACT_VERSION = "execution-context-v1"
SOURCE_PARITY_CONTRACT_VERSION = "source-parity-v1"
EXCEPTION_SNAPSHOT_CONTRACT_VERSION = "exception-snapshot-v1"
REVIEW_MANIFEST_VERSION = "practical-review-manifest-v4"
REVIEW_SESSION_ATTESTATION_VERSION = "review-session-attestation-v2"
VALIDATOR_REPORT_VERSION = "practical-scope-validator-v2"
SOURCE_MANIFEST_RELATIVE_PATH = "work/practical-v0.9/source-package-manifest.json"
CLARIFICATION_REQUESTS_FILENAME = "scope-clarification-requests.md"
MATRIX_CONSOLIDATION_SECTION_HEADING = "## Решения о консолидации сценариев"
NO_BUSINESS_QUESTIONS_MARKER = "Вопросов, требующих ответа БА, не выявлено."
CLARIFICATION_REQUEST_SECTION_HEADINGS = (
    "Контекст",
    "Заполнение ответа",
    "Запросы на уточнение",
    "Пробелы без запросов",
    "Правила использования ответов",
)

REQUIRED_SOURCE_ROLES = {"main-docx", "main-xhtml"}
ALLOWED_SUPPORT_ROLES = {"support"}
ALLOWED_VISUAL_ROLES = {"visual-only"}
ALLOWED_APPROVED_BA_DECISION_ROLES = {"approved-ba-decision-registry"}
VISUAL_ONLY_PATH_PREFIXES = ("mockups/", "support/figma/")
ALLOWED_GAP_TYPES = {
    "ba-business-ambiguity",
    "missing-source-definition",
    "source-terminology-discrepancy",
    "ui-calibration",
    "external-scope-boundary",
    "test-data-setup",
    "ba-decision-required",
    "ba-decision-supersedes-ft",
    # Compatibility with artifacts written by practical-v0.9.2.
    "ambiguity",
}
ALLOWED_GAP_STATUSES = {"open", "resolved"}
ALLOWED_VISUAL_EVIDENCE_OUTCOMES = {
    "no-visual-source",
    "insufficient",
    "conflict",
    "runtime-only",
}
REQUIRED_TC_FIELDS = (
    "Номер в разделе",
    "Название",
    "Тип",
    "Приоритет",
    "package_id",
    "Статус исполнения",
    "Контекст исполнения",
    "Трассировка",
    "Цель",
    "Предусловия",
    "Тестовые данные",
    "Шаги",
    "Итоговый ожидаемый результат",
    "Постусловия",
)
BLOCKING_CATEGORIES = {
    "source-integrity",
    "unresolved-requirement",
    "semantic-completeness",
    "traceability",
    "execution-readiness",
    "review-integrity",
    "artifact-tampering",
}
MATRIX_REVIEW_RISK_FLAGS = {
    "status-transition",
    "cross-field-rule",
    "closed-dictionary",
    "integration",
    "authorization",
    "exception-over-general-rule",
    "mapping-table",
    "temporal-rule",
    "high-fan-out",
    "high-risk",
}
COMPACT_REVIEWER_RECEIPT_OBLIGATION_THRESHOLD = 8
COMPACT_REVIEWER_RECEIPT_FORMAT = "compact-obligation-vector-v2"
COMPACT_REVIEWER_RECEIPT_MAX_BYTES = 64 * 1024
ALLOWED_EXECUTION_STATUSES = {
    "ready",
    "needs-test-data",
    "candidate-ui-calibration",
    "blocked-observability",
    "needs-future-clarification",
}
ALLOWED_EXECUTION_SETUP_KINDS = {
    "actor",
    "fixture",
    "integration",
    "initial-state",
    "environment",
    "navigation",
}
ALLOWED_EXECUTION_SETUP_AVAILABILITY = {"provided", *ALLOWED_EXECUTION_STATUSES}
ALLOWED_EXECUTION_SETUP_AVAILABILITY_SCOPES = {
    "business-test-data",
    "environment-access",
}
ALLOWED_EXECUTION_FLOW_KINDS = {
    "create",
    "edit",
    "view",
    "delete",
    "search",
    "other",
}
ALLOWED_PARAMETERIZATION_BASES = {
    "значения одного закрытого справочника",
    "эквивалентные значения одного класса",
    "границы одного правила",
    "поля одного составного результата",
}
COMPOSITE_RESULT_PARAMETERIZATION_BASIS = "поля одного составного результата"
COMPOSITE_RESULT_SHARED_COLUMNS = (
    "Домен проверки",
    "Способ взаимодействия",
    "Тип",
    "Статус исполнения",
    "Исходное состояние",
    "Формирование состояния",
    "Проверяемое действие",
)
EXECUTION_STATUS_PRECEDENCE = (
    "needs-future-clarification",
    "blocked-observability",
    "needs-test-data",
    "candidate-ui-calibration",
)
MATRIX_REQUIRED_COLUMNS = (
    "Проверка",
    "Идентификатор сценария",
    "Обязательство ФТ",
    "Контекст исполнения",
    "Проверяемый элемент",
    "Домен проверки",
    "Способ взаимодействия",
    "Проверяемое правило",
    "Исходное состояние",
    "Формирование состояния",
    "Проверяемое действие",
    "Ожидаемый результат",
    "Нужные предпосылки",
    "Тип",
    "Приоритет",
    "Статус исполнения",
    "Планируемый TC-ID",
)
PREVIOUS_MATRIX_REQUIRED_COLUMNS = (
    "Проверка",
    "Идентификатор сценария",
    "Обязательство ФТ",
    "Контекст исполнения",
    "Проверяемое правило",
    "Исходное состояние",
    "Формирование состояния",
    "Проверяемое действие",
    "Ожидаемый результат",
    "Нужные предпосылки",
    "Тип",
    "Приоритет",
    "Статус исполнения",
    "Планируемый TC-ID",
)
LEGACY_MATRIX_REQUIRED_COLUMNS = (
    "Проверка",
    "Обязательство ФТ",
    "Контекст исполнения",
    "Проверяемое правило",
    "Ожидаемый результат",
    "Нужные предпосылки",
    "Сценарий",
    "Тип",
    "Приоритет",
    "Статус исполнения",
    "Планируемый TC-ID",
)
ALLOWED_FINAL_VERDICTS = {"not-finalized", "approved", "changes-required", "blocked-input"}
ALLOWED_TRIAGE_DISPOSITIONS = {"accepted", "rejected"}
ALLOWED_TRIAGE_REJECTION_BASES = {
    "execution-status-precedence",
    "duplicate-finding",
}


def build_initial_workflow_state(
    *,
    scope_id: str,
    scope_slug: str,
    source_package_manifest: str,
    scope_obligations: str,
    scope_clarification_requests: str,
    source_parity_check: str | None = None,
    dictionary_inventory: str | None = None,
) -> dict[str, Any]:
    """Build the only current schema for a newly initialized v0.9 scope.

    Initializer, generated documentation example and contract tests use this
    builder. No current contract version or default field is duplicated in a
    Markdown example.
    """
    return {
        "schema_version": WORKFLOW_STATE_SCHEMA_VERSION,
        "route_version": ROUTE_VERSION,
        "scope_id": scope_id,
        "scope_slug": scope_slug,
        "phase": "scope",
        "next_action": "Создать матрицу тест-дизайна",
        "matrix_review_required": None,
        "contract_versions": {
            "route": ROUTE_VERSION,
            "source_package": SOURCE_CONTRACT_VERSION,
            "matrix": MATRIX_CONTRACT_VERSION,
            "controller_triage": CONTROLLER_TRIAGE_CONTRACT_VERSION,
            "clarification_outcome": CLARIFICATION_OUTCOME_CONTRACT_VERSION,
            "execution_context": EXECUTION_CONTEXT_CONTRACT_VERSION,
            "source_parity": SOURCE_PARITY_CONTRACT_VERSION,
            "exception_snapshot": EXCEPTION_SNAPSHOT_CONTRACT_VERSION,
        },
        "artifacts": {
            "source_package_manifest": source_package_manifest,
            "scope_obligations": scope_obligations,
            "scope_clarification_requests": scope_clarification_requests,
            "source_parity_check": source_parity_check or "not-created",
            "test_design_matrix": "not-created",
            "canonical_test_cases": "not-created",
            "validator_report": "not-created",
            **({"dictionary_inventory": dictionary_inventory} if dictionary_inventory else {}),
        },
        "reviews": [],
        "matrix_revision_count": 0,
        "tc_revision_count": 0,
        "final_verdict": "not-finalized",
        "decision_notes": [],
        "review_triage": [],
    }
REVIEW_FINDING_REQUIRED_FIELDS = (
    "id",
    "title",
    "details",
    "source_anchor",
    "artifact_anchor",
    "category",
    "severity",
    "blocking",
    "remediation_owner",
)
STATUS_CHANGE_CLAIM_RE = re.compile(
    r"\b(?:измен\w*|установ\w*|замен\w*)\s+(?:\S+\s+){0,4}статус\w*"
    r"|\bстатус\w*(?:\s+\S+){0,7}\s+(?:измен\w*|установ\w*|замен\w*)"
    r"|\bошибочно\s+(?:указан|имеет)\s+статус\w*",
    re.IGNORECASE,
)
TEST_DATA_TAUTOLOGY_PATTERNS = (
    re.compile(r"\bданные,?\s+предусмотренные\s+проверяемым\s+правилом\b", re.IGNORECASE),
    re.compile(r"\bвалидные\s+данные\b", re.IGNORECASE),
    re.compile(r"\bзначение\s+из\s+тестовых\s+данных\b", re.IGNORECASE),
    re.compile(r"\bподготовлена?\s+строка\s+запроса\b", re.IGNORECASE),
    re.compile(r"\bпараметр\w*\s*,?\s+указанн\w*\s+в\s+тестовых\s+данных\b", re.IGNORECASE),
    re.compile(r"\bподготовить\s+данные\s+для\s+проверяемого\s+правила\b", re.IGNORECASE),
)
TEST_DATA_GENERIC_COMPLETION_PATTERNS = (
    re.compile(
        r"\bостальн\w*\s+обязательн\w*\s+пол\w*\b[^.\n]{0,80}"
        r"\b(?:допустим\w*|валидн\w*)\s+значен\w*\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:допустим\w*|валидн\w*)\s+значен\w*\b[^.\n]{0,80}"
        r"\bостальн\w*\s+обязательн\w*\s+пол\w*\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bуникальн\w*\s+набор\w*\b[^.\n]{0,80}"
        r"\bобязательн\w*\s+значен\w*\b",
        re.IGNORECASE,
    ),
)
TEST_DATA_RUNTIME_PLACEHOLDER_PATTERNS = (
    re.compile(r"\bнесохран[её]нн\w*\s+значени\w*\b", re.IGNORECASE),
)
TEST_DATA_ACTION_LEAK_RE = re.compile(
    r"(?im)^\s*[-*]\s*(?:заполнить|открыть|выбрать|изменить|перейти|"
    r"нажать|прикрепить|загрузить)\w*\b",
    re.IGNORECASE,
)
TEST_DATA_PREPARATION_RE = re.compile(r"\bспособ\s+подготовк\w*\s*:", re.IGNORECASE)
TEST_DATA_BOUNDARY_RE = re.compile(
    r"\b(?:строк\w*|текст\w*)\b[^.\n]{0,48}"
    r"\b(?:длин\w*|из)\s*\d{3,}\s+символ\w*\b",
    re.IGNORECASE,
)
TEST_DATA_FILE_PREPARATION_RE = re.compile(
    r"\bподготовить\w*\b[^.\n]{0,120}\bфайл\w*\b",
    re.IGNORECASE,
)
MATRIX_META_STATE_PATTERNS = (
    re.compile(r"\bдоступны\s+указанные\s+предпосылки\b", re.IGNORECASE),
    re.compile(r"\bподготовлена?\s+строка\s+запроса\b", re.IGNORECASE),
    re.compile(r"\bподготовить\s+данные\s+для\s+проверяемого\s+правила\b", re.IGNORECASE),
    re.compile(r"\bвнести\s+только\s+изменение\s*,?\s+требуем\w*\s+проверяемым\s+правилом\b", re.IGNORECASE),
)
META_STATE_STEP_PATTERNS = (
    re.compile(r"\bсформировать\s+исходное\s+состояние\b", re.IGNORECASE),
    re.compile(r"\bвыполнить\s+подготовку\s+состояния\b", re.IGNORECASE),
    re.compile(r"\bподготовить\s+данные\s+для\s+проверяемого\s+правила\b", re.IGNORECASE),
    re.compile(r"\bвнести\s+только\s+изменение\s*,?\s+требуем\w*\s+проверяемым\s+правилом\b", re.IGNORECASE),
)
CONTEXT_LABEL_AS_ACTION_RE = re.compile(
    r"\b(?:откр|перейт)\w*\b[^.\n]{0,120}\bв\s+контекст\w*\b",
    re.IGNORECASE,
)
DADATA_GENERIC_DATA_PATTERNS = (
    re.compile(
        r"\b(?:подготовить|использовать|ввести)\w*\b[^.\n]{0,80}"
        r"\bорганизац\w*\s+с\s+(?:известн\w*|доступн\w*)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:нужн\w*|требу\w*)\b[^.\n]{0,48}"
        r"\bорганизац\w*\s+с\s+(?:устойчив\w*|доступн\w*|известн\w*)",
        re.IGNORECASE,
    ),
)
DADATA_FIXTURE_ID_RE = re.compile(r"\bFX-DADATA-[A-Z0-9-]+\b", re.IGNORECASE)
DADATA_PREPARATION_RE = re.compile(r"\bспособ\s+подготовк\w*\s*:", re.IGNORECASE)
DADATA_PROPERTY_RE = re.compile(
    r"\b(?:наименован\w*|инн|кпп|огрн|юр\.?\s*адрес\w*|адрес\w*)\b",
    re.IGNORECASE,
)
FROZEN_PROFILE_PROCESS_LANGUAGE_RE = re.compile(r"\bfrozen\s+profile\b", re.IGNORECASE)
RUNTIME_PROCESS_TC_MARKER_RE = re.compile(
    r"\b(?:edit|create|writer|reviewer)\s+TC\b",
    re.IGNORECASE,
)
MIXED_CREATE_EDIT_TITLE_RE = re.compile(
    r"\bсоздани\w*\b[^.]{0,48}\b(?:и|или)\b[^.]{0,48}\bредактир\w*\b",
    re.IGNORECASE,
)
SCENARIO_ID_RE = re.compile(r"^SCN-[A-Z0-9-]+$")
MATRIX_STATE_NOT_ACTIONABLE_RE = re.compile(
    r"\b(?:не\s+требуется|зада[её]тс[яь]\s+предуслов)\b", re.IGNORECASE
)
STATE_FORMATION_VERB_RE = re.compile(
    r"\b(?:ввест|указ|выбр|заполн|остав|очист|измен|прикреп|загруз|созда|откр|найт|перейт)\w*\b",
    re.IGNORECASE,
)
SAVE_OR_CLOSE_ACTION_RE = re.compile(
    r"\b(?:сохран|отмен|закр|крестик)\w*\b", re.IGNORECASE
)
NO_SAVE_SOURCE_RE = re.compile(r"\b(?:не\s+сохран\w*|без\s+сохран\w*)\b", re.IGNORECASE)
NO_SAVE_ACTION_RE = re.compile(r"\b(?:отмен|закры|крестик)\w*\b", re.IGNORECASE)
NO_SAVE_PERSISTENCE_ORACLE_RE = re.compile(
    r"\b(?:не\s+(?:создан\w*|сохран\w*|добавлен\w*)|"
    r"(?:создани\w*|сохранени\w*)\s+не\s+выполн\w*)\b",
    re.IGNORECASE,
)
SECTION_NUMBER_RE = re.compile(
    r"(?m)^\*\*Номер в разделе:\*\*\s*(\d+)\s+из\s+(\d+)\s*$"
)
SUCCESSFUL_CREATE_EXPECTED_RE = re.compile(
    r"\b(?:создан\w*|сохран\w*)\b", re.IGNORECASE
)
SUCCESSFUL_CREATE_NEGATION_RE = re.compile(
    r"\b(?:не\s+(?:создан\w*|сохран\w*)|"
    r"(?:создани\w*|сохранени\w*)\s+не\s+выполн\w*)\b",
    re.IGNORECASE,
)
CREATE_OBJECT_KEY_PATTERNS = (
    re.compile(r"(?im)^\s*[-*]\s*Ключ создаваемого объекта\s*:\s*(\S.+)$"),
    re.compile(r"(?im)^\s*[-*]\s*Идентификатор создаваемого объекта\s*:\s*(\S.+)$"),
    re.compile(r"(?im)^\s*[-*]\s*Уникальный ключ объекта\s*:\s*(\S.+)$"),
)
CREATE_OBJECT_ABSENCE_PATTERNS = (
    re.compile(
        r"(?im)^\s*[-*]\s*(?:Исходное состояние|Состояние)"
        r"(?: создаваемого)? объекта(?: в системе)?\s*:\s*"
        r"(?:отсутствует|не создан\w*)\b"
    ),
    re.compile(
        r"(?im)^\s*[-*]\s*До начала проверки объект с (?:указанным )?ключом\s*"
        r"(?:отсутствует|не создан\w*)\b"
    ),
    re.compile(
        r"(?im)^\s*[-*]\s*В системе нет объекта с (?:указанным )?ключом\b"
    ),
)
SUCCESSFUL_CREATE_CLEANUP_PATTERNS = (
    re.compile(
        r"\b(?:удал\w*[^.\n]{0,100}\bсоздан\w*|"
        r"восстанов\w*[^.\n]{0,100}\bисходн\w*\s+состо\w*|"
        r"изолированн\w*\s+прогон\w*|одноразов\w*\s+fixture)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bпосле проверки\s+удал\w*\s+объект\b", re.IGNORECASE),
    re.compile(
        r"\bпосле проверки\s+верн\w*\s+систем\w*\s+в\s+исходн\w*\s+состо\w*",
        re.IGNORECASE,
    ),
)
FOLLOW_UP_OBSERVATION_RE = re.compile(
    r"\b(?:повторн|откр|найт|провер|убед|поиск)\w*\b", re.IGNORECASE
)
EMPTY_STATE_RE = re.compile(
    r"\b(?:не\s+заполня\w*|остав\w*[^.\n]{0,80}\bпуст\w*|очист\w*)\b", re.IGNORECASE
)
INPUT_OR_SELECTION_RE = re.compile(
    r"\b(?:ввест|указ|наб[оа]р|заполн|выбр)\w*\b", re.IGNORECASE
)
NAME_FIELD_RE = re.compile(r"\b(?:наименован|назван)\w*\b", re.IGNORECASE)
SOURCE_MESSAGE_CUE_RE = re.compile(
    r"\b(?:вывод|отображ|показыв|сообщени|текст|уведомлен|ошибк)\w*\b",
    re.IGNORECASE,
)
REQUIREMENT_CODE_RE = re.compile(
    r"\b(?P<prefix>AS|BSR|GSR|DIT)\s*\.?\s*(?P<number>\d+)\b",
    re.IGNORECASE,
)
INTERNAL_UNOBSERVABILITY_JUSTIFICATION_RE = re.compile(
    r"(?:\b(?:источник|фт|требовани\w*)\b.{0,120}"
    r"\b(?:не\s+(?:зада\w*|содерж\w*|определ\w*)|отсутств\w*)\b.{0,120}"
    r"\b(?:наблюдаем\w*|признак\w*|результат\w*)\b|"
    r"\b(?:нет|отсутств\w*)\b.{0,120}\b(?:наблюдаем\w*|признак\w*|результат\w*)\b"
    r".{0,120}\b(?:источник|фт|требовани\w*)\b)",
    re.IGNORECASE,
)
CODEX_THREAD_ID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    flags=re.IGNORECASE,
)
CLARIFICATION_CARD_HEADER_RE = re.compile(
    r"(?m)^###\s+(?P<clarification_id>CLR-[A-Z0-9-]+)\s+[—-]\s+(?P<gap_id>GAP-[A-Z0-9-]+)\s*$"
)
CLARIFICATION_REQUEST_REQUIRED_FIELDS = (
    "clarification_id",
    "gap_id",
    "request_kind",
    "scope_slug",
    "requirement_codes",
    "related_ft_reference",
    "related_obligation_ids",
    "source_quote",
    "question",
    "needed_for",
    "blocking",
    "requested_from",
    "authority",
    "user_response",
    "response_status",
    "response_type",
    "updated_at",
)
CLARIFICATION_REQUEST_ENUMS = {
    "request_kind": {"ba-business-ambiguity"},
    "blocking": {"yes", "no"},
    "requested_from": {"user", "analyst", "product-owner", "developer", "unknown"},
    "authority": {"user", "analyst", "product-owner"},
    "response_status": {"unanswered", "answered", "superseded", "rejected"},
    "response_type": {
        "not-provided",
        "working-assumption",
        "user-confirmed",
        "analyst-confirmed",
        "product-confirmed",
        "rejected",
    },
}
AUTOFILL_MULTI_TARGET_RE = re.compile(
    r"автоматическ\w*\s+заполн\w*[^.]{0,400}[,;]",
    flags=re.IGNORECASE,
)
AUTOFILL_MANUAL_INPUT_RE = re.compile(
    r"(?:автоматическ\w*\s+заполн\w*[^.]{0,400}ручн\w*\s+(?:ввод\w*|заполн\w*|редактир\w*)|"
    r"ручн\w*\s+(?:ввод\w*|заполн\w*|редактир\w*)[^.]{0,400}автоматическ\w*\s+заполн\w*)",
    flags=re.IGNORECASE,
)
# A syntactically valid UTF-8 JSON file can still contain text that was
# previously decoded through a wrong single-byte codec.  These markers cover
# the two common forms of Russian UTF-8 mojibake without treating ordinary
# Russian prose as invalid.
MOJIBAKE_RE = re.compile(
    # Latin-1 fragments are the usual UTF-8-as-single-byte form.  The second
    # alternative requires two malformed Cyrillic-pair fragments: a single
    # ordinary Russian word such as "Реквизит" must never be treated as damage.
    r"(?:[ÐÑÃÂ][\x80-\xBF]|(?:[РС][\u0400-\u045f]){2,})"
)
EXECUTION_CONTEXT_ID_RE = re.compile(r"^CTX-[A-Z0-9-]+$")
EXECUTION_SETUP_ID_RE = re.compile(r"^SETUP-[A-Z0-9-]+$")
VOLATILE_ENVIRONMENT_CONFIGURATION_RE = re.compile(
    r"https?://|\b(?:url|uri|login|username|password|token|cookie)\b|"
    r"\b(?:логин|парол[ья]|токен|куки)\b|"
    r"(?:уч[её]тн\w*\s+запис\w*|account)\s*(?::|=|`|«)",
    flags=re.IGNORECASE,
)
APPROVED_CLARIFICATION_FILENAME_RE = re.compile(
    r"(?:^|/)[^/]+-approved-clarifications\.md$", flags=re.IGNORECASE
)
APPROVED_BA_DECISIONS_FILENAME_RE = re.compile(
    r"(?:^|/)[^/]+-approved-ba-decisions\.md$", flags=re.IGNORECASE
)
APPROVED_BA_DECISION_CARD_HEADER_RE = re.compile(
    r"(?m)^##\s+(?P<decision_id>BA-DEC-[A-Z0-9-]+)\b.*$"
)
APPROVED_BA_DECISION_REQUIRED_FIELDS = (
    "decision_id",
    "status",
    "authority",
    "decision_type",
    "applies_to",
    "requirement_refs",
    "decision",
)
APPROVED_BA_DECISION_ENUMS = {
    "status": {"approved"},
    "authority": {"business-analyst", "product-owner"},
    "decision_type": {"clarifies-ft", "supersedes-ft"},
}
OBLIGATION_DISPOSITIONS = {"active", "superseded-by-ba-decision"}
AGENT_NOTES_VERSION_METADATA_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:исходн\w*|agent(?:[- ]layer)?|агент\w*|код\w*)\s*"
    r"(?:commit|коммит|version|версия)\s*[:=]"
)


@dataclass(frozen=True)
class ScopeFinding:
    id: str
    category: str
    severity: str
    blocking: bool
    blocking_reason: str | None
    remediation_owner: str
    title: str
    details: str
    artifact: str
    evidence: list[str]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class PracticalV09Error(ValueError):
    """Raised when a v0.9 contract input is unreadable or unsafe."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def is_durable_codex_thread_id(value: object) -> bool:
    return isinstance(value, str) and bool(CODEX_THREAD_ID_RE.fullmatch(value))


def requirement_codes(value: object) -> dict[str, str]:
    """Return normalized FT requirement codes and their canonical display form.

    ``source_anchor`` and a TC trace may use a dot or whitespace between a
    prefix and a number.  The comparison therefore normalizes only that
    separator; the numeric part is preserved exactly so that, for example,
    ``DIT 007`` is not silently rewritten to a different code.
    """
    codes: dict[str, str] = {}
    for match in REQUIREMENT_CODE_RE.finditer(str(value or "")):
        prefix = match.group("prefix").upper()
        number = match.group("number")
        key = f"{prefix}:{number}"
        separator = "." if prefix == "AS" else " "
        codes.setdefault(key, f"{prefix}{separator}{number}")
    return codes


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PracticalV09Error(f"Cannot read JSON {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PracticalV09Error(f"JSON object expected in {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(rendered, encoding="utf-8")


def has_suspicious_mojibake(value: object) -> bool:
    """Return whether a JSON value contains likely corrupted UTF-8 prose."""
    if isinstance(value, str):
        return bool(MOJIBAKE_RE.search(value))
    if isinstance(value, list):
        return any(has_suspicious_mojibake(item) for item in value)
    if isinstance(value, dict):
        return any(
            has_suspicious_mojibake(key) or has_suspicious_mojibake(item)
            for key, item in value.items()
        )
    return False


def package_relative_path(package_root: Path, raw: object, *, artifact: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise PracticalV09Error(f"{artifact}: expected a non-empty package-relative path")
    candidate = (package_root / raw).resolve()
    try:
        candidate.relative_to(package_root.resolve())
    except ValueError as exc:
        raise PracticalV09Error(f"{artifact}: path escapes FT package: {raw}") from exc
    return candidate


def relative_to_package(package_root: Path, path: Path) -> str:
    return path.resolve().relative_to(package_root.resolve()).as_posix()


def clarification_requests_path(obligations_path: Path) -> Path:
    """Return the single user-facing clarification companion for one scope."""
    return obligations_path.with_name(CLARIFICATION_REQUESTS_FILENAME)


def business_clarification_entries(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return gaps that need a concrete question to the business analyst."""
    clarifications = payload.get("clarifications", [])
    if not isinstance(clarifications, list):
        return []
    result: list[dict[str, Any]] = []
    for entry in clarifications:
        if not isinstance(entry, dict):
            continue
        is_open_ba_conflict = (
            entry.get("gap_type") == "ba-decision-required"
            and entry.get("status") == "open"
        )
        if clarification_requires_business_request(entry) or is_open_ba_conflict:
            result.append(entry)
    return result


def render_scope_clarification_requests(payload: Mapping[str, Any]) -> str:
    """Build the initial BA-question outcome for one practical scope.

    The renderer only creates an initial draft.  It is intentionally not used
    to overwrite a file containing a BA response on a later iteration.
    """
    scope = payload.get("scope")
    if not isinstance(scope, dict) or not str(scope.get("slug") or "").strip():
        raise PracticalV09Error(
            "scope-obligations.json: scope.slug is required to create BA questions"
        )
    scope_slug = str(scope["slug"]).strip()
    cards: list[str] = []
    for entry in business_clarification_entries(payload):
        gap_id = str(entry.get("id") or "").strip()
        clarification_id = str(entry.get("clarification_id") or "").strip()
        question = str(entry.get("question_to_analyst") or "").strip()
        affected = entry.get("affected_obligation_ids")
        if not re.fullmatch(r"GAP-[A-Z0-9-]+", gap_id):
            raise PracticalV09Error(
                "scope-obligations.json: вопрос БА требует GAP-* id"
            )
        if not re.fullmatch(r"CLR-[A-Z0-9-]+", clarification_id):
            raise PracticalV09Error(
                f"{gap_id}: вопрос БА требует clarification_id формата CLR-*"
            )
        if not question:
            raise PracticalV09Error(
                f"{gap_id}: вопрос БА требует точный question_to_analyst"
            )
        if (
            not isinstance(affected, list)
            or not affected
            or not all(isinstance(item, str) and item.strip() for item in affected)
        ):
            raise PracticalV09Error(
                f"{gap_id}: вопрос БА требует непустой affected_obligation_ids"
            )
        source_anchor = str(entry.get("source_anchor") or "").strip()
        source_statement = str(entry.get("source_statement") or "").strip()
        description = str(entry.get("description") or "").strip()
        if not source_anchor or not source_statement or not description:
            raise PracticalV09Error(
                f"{gap_id}: вопрос БА требует source_anchor, source_statement и description"
            )
        codes = requirement_codes(f"{source_anchor} {source_statement}")
        fields = {
            "clarification_id": clarification_id,
            "gap_id": gap_id,
            "request_kind": "ba-business-ambiguity",
            "scope_slug": scope_slug,
            "requirement_codes": "; ".join(codes.values()) or "-",
            "related_ft_reference": source_anchor,
            "related_obligation_ids": "; ".join(affected),
            "source_quote": source_statement,
            "question": question,
            "needed_for": description,
            "blocking": "yes" if entry.get("impact") == "blocking" else "no",
            "requested_from": "analyst",
            "authority": "analyst",
            "user_response": "-",
            "response_status": "unanswered",
            "response_type": "not-provided",
            "updated_at": "-",
        }
        yaml_body = "\n".join(
            f"{key}: {json.dumps(value, ensure_ascii=False)}"
            for key, value in fields.items()
        )
        cards.append(
            f"### {clarification_id} — {gap_id}\n\n```yaml\n{yaml_body}\n```"
        )
    questions_section = "\n\n".join(cards) if cards else f"- {NO_BUSINESS_QUESTIONS_MARKER}"
    no_request_section = (
        "- Отсутствуют."
        if cards
        else "- Нет открытых GAP-*, которые требуют продуктового ответа БА."
    )
    return (
        "# Вопросы к бизнес-аналитику\n\n"
        "## Контекст\n\n"
        f"- `scope_slug`: `{scope_slug}`\n"
        "- Основание: `scope-obligations.json`.\n\n"
        "## Заполнение ответа\n\n"
        "- Для каждой карточки заполните поле «Ответ БА» (`user_response`), затем обновите статус ответа.\n"
        "- Не меняйте `CLR-*`, `GAP-*`, source-привязки и формулировку вопроса.\n\n"
        "## Запросы на уточнение\n\n"
        f"{questions_section}\n\n"
        "## Пробелы без запросов\n\n"
        f"{no_request_section}\n\n"
        "## Правила использования ответов\n\n"
        "- Подтверждённый ответ связывается с соответствующим `GAP-*`; он не заменяет основной ФТ без явного решения БА.\n"
    )


def missing_clarification_request_sections(text: str) -> list[str]:
    """Return required Russian user-facing headings absent from a BA request file."""
    headings = {
        match.group("heading").strip()
        for match in re.finditer(r"(?m)^##\s+(?P<heading>.+?)\s*$", text)
    }
    return [heading for heading in CLARIFICATION_REQUEST_SECTION_HEADINGS if heading not in headings]


def finding(
    finding_id: str,
    category: str,
    title: str,
    details: str,
    artifact: str,
    *,
    evidence: Iterable[str] = (),
    severity: str = "error",
    remediation_owner: str = "writer",
    blocking: bool | None = None,
    blocking_reason: str | None = None,
) -> ScopeFinding:
    if blocking is None:
        blocking = category in BLOCKING_CATEGORIES
    if blocking and not blocking_reason:
        blocking_reason = f"Блокирующая категория: {category}."
    if not blocking:
        blocking_reason = None
    return ScopeFinding(
        id=finding_id,
        category=category,
        severity=severity,
        blocking=bool(blocking),
        blocking_reason=blocking_reason,
        remediation_owner=remediation_owner,
        title=title,
        details=details,
        artifact=artifact,
        evidence=list(evidence),
    )


def workflow_artifact_path(
    state: dict[str, Any], package_root: Path, key: str, *, required: bool = False
) -> Path | None:
    artifacts = state.get("artifacts")
    if not isinstance(artifacts, dict):
        if required:
            raise PracticalV09Error("workflow-state.json: object artifacts is required")
        return None
    raw = artifacts.get(key)
    if raw in (None, "", "not-created", "not-applicable"):
        if required:
            raise PracticalV09Error(f"workflow-state.json: artifacts.{key} is required")
        return None
    return package_relative_path(package_root, raw, artifact=f"workflow artifacts.{key}")


def load_workflow_state(path: Path, package_root: Path) -> dict[str, Any]:
    state = read_json(path)
    if state.get("schema_version") != WORKFLOW_STATE_SCHEMA_VERSION:
        raise PracticalV09Error(
            "workflow-state.json: schema_version must be "
            f"{WORKFLOW_STATE_SCHEMA_VERSION!r}"
        )
    if state.get("route_version") != ROUTE_VERSION:
        raise PracticalV09Error(
            f"workflow-state.json: route_version must be {ROUTE_VERSION!r}"
        )
    for key in ("scope_id", "scope_slug", "phase", "artifacts"):
        if not state.get(key):
            raise PracticalV09Error(f"workflow-state.json: missing {key}")
    if not isinstance(state.get("artifacts"), dict):
        raise PracticalV09Error("workflow-state.json: artifacts must be an object")
    contract_versions = state.get("contract_versions")
    if not isinstance(contract_versions, dict):
        raise PracticalV09Error("workflow-state.json: contract_versions must be an object")
    if contract_versions.get("route") != ROUTE_VERSION:
        raise PracticalV09Error(
            f"workflow-state.json: contract_versions.route must be {ROUTE_VERSION!r}"
        )
    if contract_versions.get("source_package") != SOURCE_CONTRACT_VERSION:
        raise PracticalV09Error(
            "workflow-state.json: contract_versions.source_package must be "
            f"{SOURCE_CONTRACT_VERSION!r}"
        )
    reviews = state.get("reviews", [])
    if not isinstance(reviews, list):
        raise PracticalV09Error("workflow-state.json: reviews must be an array")
    normalize_revision_budgets(state)
    normalize_final_verdict(state)
    if state.get("final_verdict") not in ALLOWED_FINAL_VERDICTS:
        raise PracticalV09Error(
            "workflow-state.json: final_verdict has unsupported value"
        )
    source_manifest = workflow_artifact_path(
        state, package_root, "source_package_manifest", required=True
    )
    assert source_manifest is not None
    if relative_to_package(package_root, source_manifest) != SOURCE_MANIFEST_RELATIVE_PATH:
        raise PracticalV09Error(
            "workflow-state.json: source_package_manifest must be the shared "
            f"{SOURCE_MANIFEST_RELATIVE_PATH}"
        )
    workflow_artifact_path(state, package_root, "scope_obligations", required=True)
    # The first v2 tool release predates the explicit matrix-version field.
    # A scope whose actual table already has the v2 header is compatible; add
    # the missing metadata in-memory, without touching budgets or content.
    if contract_versions.get("matrix") is None:
        matrix_path = workflow_artifact_path(state, package_root, "test_design_matrix")
        if matrix_path is not None and matrix_path.is_file():
            if matrix_contract_version_from_path(matrix_path) == MATRIX_CONTRACT_VERSION:
                contract_versions["matrix"] = MATRIX_CONTRACT_VERSION
    workflow_matrix_contract_version(state)
    workflow_scenario_consolidation_enabled(state)
    workflow_controller_triage_enabled(state)
    workflow_clarification_outcome_enabled(state)
    workflow_execution_context_enabled(state)
    migration = workflow_contract_migration(state)
    if migration is not None and workflow_matrix_contract_version(state) != MATRIX_CONTRACT_VERSION:
        raise PracticalV09Error(
            "workflow-state.json: active contract migration must declare the current matrix contract"
        )
    return state


def normalize_revision_budgets(state: dict[str, Any]) -> None:
    """Normalize the v0.9 revision budget without breaking existing scopes.

    Early v0.9 artifacts had one ``revision_count`` shared by matrix and TC
    reviews.  A consumed matrix revision must not make the first final TC
    finding unrepairable.  Legacy states are deterministically migrated in
    memory and are persisted in the new form on the next finalization.
    """
    matrix_count = state.get("matrix_revision_count")
    tc_count = state.get("tc_revision_count")
    if matrix_count is None and tc_count is None:
        legacy_count = state.pop("revision_count", None)
        if not isinstance(legacy_count, int) or not 0 <= legacy_count <= 1:
            raise PracticalV09Error(
                "workflow-state.json: revision_count must be 0 or 1 for a legacy state"
            )
        reviews = state.get("reviews", [])
        has_matrix_changes = any(
            isinstance(entry, dict)
            and entry.get("mode") == "matrix"
            and entry.get("verdict") == "changes-required"
            for entry in reviews
        )
        state["matrix_revision_count"] = legacy_count if has_matrix_changes else 0
        state["tc_revision_count"] = 0 if has_matrix_changes else legacy_count
        return
    if matrix_count is None or tc_count is None:
        raise PracticalV09Error(
            "workflow-state.json: matrix_revision_count and tc_revision_count must be specified together"
        )
    if not isinstance(matrix_count, int) or not 0 <= matrix_count <= 1:
        raise PracticalV09Error("workflow-state.json: matrix_revision_count must be 0 or 1")
    if not isinstance(tc_count, int) or not 0 <= tc_count <= 1:
        raise PracticalV09Error("workflow-state.json: tc_revision_count must be 0 or 1")
    state.pop("revision_count", None)


def normalize_final_verdict(state: dict[str, Any]) -> None:
    """Keep final_verdict reserved for the final TC review.

    Matrix review history is already retained in ``reviews``.  Older state
    files projected a matrix ``changes-required`` result as the final verdict,
    which made the route appear unfinished even after a matrix re-review was
    approved.
    """
    test_case_review_exists = any(
        isinstance(entry, dict) and entry.get("mode") == "test-cases"
        for entry in state.get("reviews", [])
    )
    if not test_case_review_exists and state.get("final_verdict") == "changes-required":
        state["final_verdict"] = "not-finalized"


def workflow_matrix_contract_version(state: Mapping[str, Any]) -> str:
    """Return the declared matrix contract without silently persisting a migration.

    Workflows created before ``practical-matrix-v2`` did not record a matrix
    contract. They remain readable as v1. A controller must explicitly run
    the contract-migration command before it can use the current matrix rules.
    """
    versions = state.get("contract_versions")
    if not isinstance(versions, Mapping):
        raise PracticalV09Error("workflow-state.json: contract_versions must be an object")
    declared = versions.get("matrix")
    if declared is None:
        return LEGACY_MATRIX_CONTRACT_VERSION
    if declared not in {
        LEGACY_MATRIX_CONTRACT_VERSION,
        PREVIOUS_MATRIX_CONTRACT_VERSION,
        MATRIX_CONTRACT_VERSION,
    }:
        raise PracticalV09Error(
            "workflow-state.json: contract_versions.matrix has unsupported value"
        )
    return str(declared)


def workflow_scenario_consolidation_enabled(state: Mapping[str, Any]) -> bool:
    """Return whether a scope uses the explicit consolidation contract.

    This is a compatibility reader for scopes created before decisions moved
    into ``test-design-matrix.md``.  New scopes do not declare this workflow
    contract: every shared planned TC is instead a deliberate, reviewable
    ``CON-*`` decision in the matrix.
    """
    versions = state.get("contract_versions")
    if not isinstance(versions, Mapping):
        raise PracticalV09Error("workflow-state.json: contract_versions must be an object")
    declared = versions.get("scenario_consolidation")
    if declared is None:
        return False
    if declared not in {
        LEGACY_SCENARIO_CONSOLIDATION_CONTRACT_VERSION,
        SCENARIO_CONSOLIDATION_CONTRACT_VERSION,
    }:
        raise PracticalV09Error(
            "workflow-state.json: contract_versions.scenario_consolidation has unsupported value"
        )
    if not isinstance(state.get("scenario_consolidation"), list):
        raise PracticalV09Error(
            "workflow-state.json: scenario_consolidation must be an array for the declared scenario consolidation contract"
        )
    return True


def workflow_controller_triage_enabled(state: Mapping[str, Any]) -> bool:
    """Return whether changes-required results require controller triage.

    The triage contract is intentionally opt-in for existing scopes.  New
    scopes must record a decision for every content blocker before a reviewer
    result can consume a revision budget or move the workflow forward.
    """
    versions = state.get("contract_versions")
    if not isinstance(versions, Mapping):
        raise PracticalV09Error("workflow-state.json: contract_versions must be an object")
    declared = versions.get("controller_triage")
    if declared is None:
        return False
    if declared != CONTROLLER_TRIAGE_CONTRACT_VERSION:
        raise PracticalV09Error(
            "workflow-state.json: contract_versions.controller_triage has unsupported value"
        )
    if not isinstance(state.get("review_triage"), list):
        raise PracticalV09Error(
            "workflow-state.json: review_triage must be an array for controller-triage-v1"
        )
    return True


def workflow_clarification_outcome_enabled(state: Mapping[str, Any]) -> bool:
    """Return whether the scope must retain one explicit BA-question outcome."""
    versions = state.get("contract_versions")
    if not isinstance(versions, Mapping):
        raise PracticalV09Error("workflow-state.json: contract_versions must be an object")
    declared = versions.get("clarification_outcome")
    if declared is None:
        return False
    if declared != CLARIFICATION_OUTCOME_CONTRACT_VERSION:
        raise PracticalV09Error(
            "workflow-state.json: contract_versions.clarification_outcome "
            "has unsupported value"
        )
    artifacts = state.get("artifacts")
    raw_path = artifacts.get("scope_clarification_requests") if isinstance(artifacts, Mapping) else None
    if not isinstance(raw_path, str) or raw_path.strip() in {
        "",
        "not-created",
        "not-applicable",
    }:
        raise PracticalV09Error(
            "workflow-state.json: scope_clarification_requests is required "
            "for clarification-outcome-v1"
        )
    return True


def workflow_execution_context_enabled(state: Mapping[str, Any]) -> bool:
    """Validate the explicit execution-context schema for newly initialized scopes.

    The schema is opt-in only to keep historical scope artifacts readable.
    Every current initializer declares it; its presence therefore fails closed
    when an incompatible controller or a stale document writes another value.
    """
    versions = state.get("contract_versions")
    if not isinstance(versions, Mapping):
        raise PracticalV09Error("workflow-state.json: contract_versions must be an object")
    declared = versions.get("execution_context")
    if declared is None:
        return False
    if declared != EXECUTION_CONTEXT_CONTRACT_VERSION:
        raise PracticalV09Error(
            "workflow-state.json: contract_versions.execution_context "
            "has unsupported value"
        )
    return True


def workflow_source_parity_enabled(state: Mapping[str, Any]) -> bool:
    """Return whether a scope must retain DOCX/PDF parity evidence when PDF exists.

    The contract is opt-in for scopes created before v0.9.29.  New scopes
    declare it from initialization, so an available PDF is not merely bound to
    a reviewer manifest but is explicitly cross-checked before matrix/TC work.
    """
    versions = state.get("contract_versions")
    if not isinstance(versions, Mapping):
        raise PracticalV09Error("workflow-state.json: contract_versions must be an object")
    declared = versions.get("source_parity")
    if declared is None:
        return False
    if declared != SOURCE_PARITY_CONTRACT_VERSION:
        raise PracticalV09Error(
            "workflow-state.json: contract_versions.source_parity has unsupported value"
        )
    return True


def workflow_exception_snapshot_enabled(state: Mapping[str, Any]) -> bool:
    """Return whether exceptions must bind an immutable pre-change snapshot."""
    versions = state.get("contract_versions")
    if not isinstance(versions, Mapping):
        raise PracticalV09Error("workflow-state.json: contract_versions must be an object")
    declared = versions.get("exception_snapshot")
    if declared is None:
        return False
    if declared != EXCEPTION_SNAPSHOT_CONTRACT_VERSION:
        raise PracticalV09Error(
            "workflow-state.json: contract_versions.exception_snapshot has unsupported value"
        )
    return True


def review_content_findings(result: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return blocking reviewer findings that can trigger a writer revision."""
    raw_findings = result.get("findings")
    if not isinstance(raw_findings, list):
        return []
    return [
        item
        for item in raw_findings
        if isinstance(item, dict)
        and item.get("blocking") is True
        and item.get("remediation_owner") not in {"controller", "validator"}
    ]


def triage_record_for_review(
    state: Mapping[str, Any],
    *,
    review_mode: str,
    review_result_path: Path,
) -> dict[str, Any] | None:
    """Return the one controller decision bound to an immutable review result."""
    if not workflow_controller_triage_enabled(state):
        return None
    review_triage = state.get("review_triage")
    assert isinstance(review_triage, list)
    expected_hash = sha256_file(review_result_path)
    matches = [
        item
        for item in review_triage
        if isinstance(item, dict)
        and item.get("review_mode") == review_mode
        and item.get("review_result_sha256") == expected_hash
    ]
    if len(matches) != 1:
        raise PracticalV09Error(
            "workflow-state.json: changes-required result requires exactly one "
            "controller triage bound to its raw review SHA-256"
        )
    return matches[0]


def workflow_contract_migration(state: Mapping[str, Any]) -> dict[str, Any] | None:
    """Validate and return an explicit active-scope contract migration record."""
    raw = state.get("contract_migration")
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise PracticalV09Error("workflow-state.json: contract_migration must be an object")
    status = raw.get("status")
    if status not in {"active", "matrix-ready", "matrix-accepted", "completed"}:
        raise PracticalV09Error("workflow-state.json: contract_migration.status has unsupported value")
    if raw.get("from_matrix_contract") not in MIGRATABLE_MATRIX_CONTRACT_VERSIONS:
        raise PracticalV09Error(
            "workflow-state.json: contract_migration.from_matrix_contract must be a supported legacy matrix contract"
        )
    if raw.get("to_matrix_contract") != MATRIX_CONTRACT_VERSION:
        raise PracticalV09Error(
            "workflow-state.json: contract_migration.to_matrix_contract must be practical-matrix-v3"
        )
    if raw.get("authorization") != "explicit-user":
        raise PracticalV09Error("workflow-state.json: contract migration requires explicit-user authorization")
    if not isinstance(raw.get("snapshot_manifest"), str) or not raw["snapshot_manifest"]:
        raise PracticalV09Error("workflow-state.json: contract_migration.snapshot_manifest is required")
    if not isinstance(raw.get("canonical_tc_sync_required"), bool):
        raise PracticalV09Error("workflow-state.json: contract_migration.canonical_tc_sync_required must be boolean")
    return raw


def is_visual_only_path(raw_path: str) -> bool:
    normalized = raw_path.replace("\\", "/").lstrip("/").casefold()
    return normalized.startswith(VISUAL_ONLY_PATH_PREFIXES)


def validate_manifest_bound_inputs(
    manifest: dict[str, Any],
    package_root: Path,
    artifact: str,
    *,
    field: str,
    allowed_roles: set[str],
    input_label: str,
    seen_paths: set[str],
    reject_visual_paths: bool,
    reject_package_ba_decision_registries: bool = True,
) -> list[ScopeFinding]:
    entries = manifest.get(field)
    if not isinstance(entries, list):
        return [finding(
            f"source-manifest-{field}-format",
            "source-integrity",
            f"Некорректен перечень {input_label}",
            f"Поле {field} должно быть массивом hash-bound файлов.",
            artifact,
            remediation_owner="controller",
        )]

    findings: list[ScopeFinding] = []
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            findings.append(finding(
                f"source-manifest-{field}-invalid",
                "source-integrity",
                f"Строка {input_label} имеет неверный формат",
                f"{field}[{index}] должен быть объектом.",
                artifact,
                remediation_owner="controller",
            ))
            continue

        role = str(entry.get("role") or "")
        raw_path = entry.get("path")
        if role not in allowed_roles:
            findings.append(finding(
                f"source-manifest-{field}-role",
                "source-integrity",
                f"У {input_label} неизвестная роль",
                f"{field}[{index}].role={role!r}; допустимы: "
                + ", ".join(sorted(allowed_roles))
                + ".",
                artifact,
                remediation_owner="controller",
            ))
        if not isinstance(raw_path, str) or not raw_path.strip():
            findings.append(finding(
                f"source-manifest-{field}-path",
                "source-integrity",
                f"У {input_label} не указан путь",
                f"{field}[{index}].path должен быть непустой строкой.",
                artifact,
                remediation_owner="controller",
            ))
            continue

        if reject_visual_paths and is_visual_only_path(raw_path):
            findings.append(finding(
                "source-manifest-visual-input-misclassified",
                "source-integrity",
                "Визуальный материал ошибочно зарегистрирован как support",
                "Макеты и Figma-index должны находиться только в visual_inputs с ролью visual-only; "
                "они не являются источником бизнес-правил.",
                artifact,
                evidence=[raw_path],
                remediation_owner="controller",
            ))
        if APPROVED_CLARIFICATION_FILENAME_RE.search(raw_path.replace("\\", "/")):
            findings.append(finding(
                "source-manifest-scope-clarification",
                "source-integrity",
                "Утверждённый ответ БА ошибочно добавлен в общий source manifest",
                "Scope-local approved clarification должен быть связан только через GAP-* "
                "в scope-obligations.json и не должен делать stale другие scope.",
                artifact,
                remediation_owner="controller",
            ))
        if (
            reject_package_ba_decision_registries
            and APPROVED_BA_DECISIONS_FILENAME_RE.search(raw_path.replace("\\", "/"))
        ):
            findings.append(finding(
                "source-manifest-ba-decision-registry-misclassified",
                "source-integrity",
                "Пакетный реестр решений БА добавлен не в специальное поле",
                "Файл *-approved-ba-decisions.md должен находиться только в approved_ba_decisions "
                "с ролью approved-ba-decision-registry.",
                artifact,
                remediation_owner="controller",
            ))
        if raw_path in seen_paths:
            findings.append(finding(
                "source-manifest-input-path-duplicate",
                "traceability",
                "Материал повторяется в source manifest",
                f"Повторяется {raw_path}.",
                artifact,
                remediation_owner="controller",
            ))
        seen_paths.add(raw_path)

        try:
            input_path = package_relative_path(package_root, raw_path, artifact=artifact)
        except PracticalV09Error as exc:
            findings.append(finding(
                f"source-manifest-{field}-path",
                "source-integrity",
                f"Некорректен путь {input_label}",
                str(exc),
                artifact,
                remediation_owner="controller",
            ))
            continue
        if not input_path.is_file():
            findings.append(finding(
                f"source-manifest-{field}-missing",
                "source-integrity",
                f"{input_label.capitalize()} отсутствует",
                f"Не найден {raw_path} для роли {role}.",
                artifact,
                evidence=[raw_path],
                remediation_owner="controller",
            ))
            continue
        expected_hash = str(entry.get("sha256") or "")
        actual_hash = sha256_file(input_path)
        if expected_hash != actual_hash:
            findings.append(finding(
                f"source-manifest-{field}-hash",
                "source-integrity",
                f"Контрольная сумма {input_label} не совпадает",
                f"Файл {raw_path} изменён после создания манифеста.",
                artifact,
                evidence=[f"expected={expected_hash}", f"actual={actual_hash}"],
                remediation_owner="controller",
            ))
    return findings


def validate_source_package_manifest(
    manifest_path: Path, package_root: Path
) -> tuple[list[ScopeFinding], dict[str, Any]]:
    artifact = relative_to_package(package_root, manifest_path)
    try:
        manifest = read_json(manifest_path)
    except PracticalV09Error as exc:
        return [finding("source-manifest-unreadable", "source-integrity", "Недоступен манифест исходных материалов", str(exc), artifact, remediation_owner="controller")], {}

    findings: list[ScopeFinding] = []
    if manifest.get("route_version") != ROUTE_VERSION:
        findings.append(finding("source-manifest-route-version", "source-integrity", "У манифеста исходных материалов неверная версия маршрута", f"Ожидается {ROUTE_VERSION}.", artifact, remediation_owner="controller"))
    if manifest.get("tool_version") not in {None, ROUTE_TOOL_VERSION}:
        findings.append(finding("source-manifest-tool-version", "transport", "Манифест исходных материалов создан другой версией инструмента", f"Текущая версия: {ROUTE_TOOL_VERSION}; указанная: {manifest.get('tool_version')}.", artifact, remediation_owner="controller", severity="warning"))
    if manifest.get("source_contract_version") != SOURCE_CONTRACT_VERSION:
        findings.append(finding("source-manifest-contract-version", "source-integrity", "У манифеста исходных материалов неверная версия контракта", f"Ожидается {SOURCE_CONTRACT_VERSION}.", artifact, remediation_owner="controller"))
    documents = manifest.get("documents")
    if not isinstance(documents, list):
        findings.append(finding("source-manifest-documents-missing", "source-integrity", "В манифесте не указан перечень исходных файлов", "Поле documents должно быть массивом DOCX и XHTML; PDF включается при наличии для structural/visual cross-check.", artifact, remediation_owner="controller"))
        return findings, manifest

    seen_roles: set[str] = set()
    for index, entry in enumerate(documents, start=1):
        if not isinstance(entry, dict):
            findings.append(finding("source-manifest-document-invalid", "source-integrity", "Строка исходных материалов имеет неверный формат", f"documents[{index}] должен быть объектом.", artifact, remediation_owner="controller"))
            continue
        role = str(entry.get("role") or "")
        seen_roles.add(role)
        raw_path = entry.get("path")
        try:
            document_path = package_relative_path(package_root, raw_path, artifact=artifact)
        except PracticalV09Error as exc:
            findings.append(finding("source-manifest-document-path", "source-integrity", "Некорректен путь исходного материала", str(exc), artifact, remediation_owner="controller"))
            continue
        if not document_path.is_file():
            findings.append(finding("source-manifest-document-missing", "source-integrity", "Исходный материал отсутствует", f"Не найден {raw_path} для роли {role}.", artifact, evidence=[str(raw_path)], remediation_owner="controller"))
            continue
        expected_hash = str(entry.get("sha256") or "")
        actual_hash = sha256_file(document_path)
        if expected_hash != actual_hash:
            findings.append(finding("source-manifest-document-hash", "source-integrity", "Контрольная сумма исходного материала не совпадает", f"Файл {raw_path} изменён после создания манифеста.", artifact, evidence=[f"expected={expected_hash}", f"actual={actual_hash}"], remediation_owner="controller"))

    missing_roles = sorted(REQUIRED_SOURCE_ROLES - seen_roles)
    if missing_roles:
        findings.append(finding("source-manifest-required-roles", "source-integrity", "Манифест исходных материалов неполон", "Отсутствуют обязательные роли: " + ", ".join(missing_roles) + ".", artifact, remediation_owner="controller"))

    seen_manifest_paths = {
        entry["path"]
        for entry in documents
        if isinstance(entry, dict) and isinstance(entry.get("path"), str)
    }
    findings.extend(validate_manifest_bound_inputs(
        manifest,
        package_root,
        artifact,
        field="support_inputs",
        allowed_roles=ALLOWED_SUPPORT_ROLES,
        input_label="support-материалов",
        seen_paths=seen_manifest_paths,
        reject_visual_paths=True,
    ))
    findings.extend(validate_manifest_bound_inputs(
        manifest,
        package_root,
        artifact,
        field="visual_inputs",
        allowed_roles=ALLOWED_VISUAL_ROLES,
        input_label="визуальных материалов",
        seen_paths=seen_manifest_paths,
        reject_visual_paths=False,
    ))
    findings.extend(validate_manifest_bound_inputs(
        manifest,
        package_root,
        artifact,
        field="approved_ba_decisions",
        allowed_roles=ALLOWED_APPROVED_BA_DECISION_ROLES,
        input_label="утверждённых решений БА",
        seen_paths=seen_manifest_paths,
        reject_visual_paths=False,
        reject_package_ba_decision_registries=False,
    ))

    approved_entries = manifest.get("approved_ba_decisions", [])
    if isinstance(approved_entries, list) and len(approved_entries) > 1:
        findings.append(finding(
            "source-manifest-ba-decision-registry-count",
            "source-integrity",
            "В манифесте указано несколько реестров решений БА",
            "Для одного FT-пакета допускается ровно один пакетный реестр утверждённых решений БА.",
            artifact,
            remediation_owner="controller",
        ))
    for entry in approved_entries if isinstance(approved_entries, list) else []:
        if isinstance(entry, dict) and not APPROVED_BA_DECISIONS_FILENAME_RE.search(
            str(entry.get("path") or "").replace("\\", "/")
        ):
            findings.append(finding(
                "source-manifest-ba-decision-registry-name",
                "source-integrity",
                "Реестр решений БА имеет некорректное имя",
                "Пакетный реестр должен называться *-approved-ba-decisions.md.",
                artifact,
                remediation_owner="controller",
            ))
    _, decision_findings = load_approved_ba_decisions(manifest, package_root, artifact)
    findings.extend(decision_findings)

    notes = manifest.get("agent_notes")
    notes_path = package_root / "AGENT-NOTES.md"
    if notes_path.is_file():
        if not isinstance(notes, dict) or notes.get("path") != "AGENT-NOTES.md":
            findings.append(finding("source-manifest-agent-notes-unbound", "source-integrity", "Не учтён обязательный контекст AGENT-NOTES.md", "Файл существует в корне FT-пакета и должен быть связан в source-package-manifest.json.", artifact, remediation_owner="controller"))
        elif str(notes.get("sha256") or "") != sha256_file(notes_path):
            findings.append(finding("source-manifest-agent-notes-hash", "source-integrity", "Контрольная сумма AGENT-NOTES.md не совпадает", "Контекст пакета изменился после создания манифеста.", artifact, remediation_owner="controller"))
        try:
            notes_text = notes_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            findings.append(finding(
                "source-manifest-agent-notes-unreadable",
                "source-integrity",
                "Не удалось прочитать AGENT-NOTES.md как UTF-8",
                str(exc),
                artifact,
                remediation_owner="controller",
            ))
        else:
            if AGENT_NOTES_VERSION_METADATA_RE.search(notes_text):
                findings.append(finding(
                    "source-manifest-agent-notes-version-metadata",
                    "transport",
                    "В AGENT-NOTES.md записана версия agent-layer",
                    "Версия и commit агента фиксируются в review manifest только для аудита; "
                    "удалите их из package context, чтобы обновление агента не делало scope stale.",
                    artifact,
                    remediation_owner="controller",
                    severity="warning",
                ))
    elif notes not in (None, "", "not-applicable"):
        findings.append(finding("source-manifest-agent-notes-stale", "source-integrity", "Манифест ссылается на отсутствующий AGENT-NOTES.md", "Удалите устаревшую ссылку или восстановите файл.", artifact, remediation_owner="controller"))
    return findings, manifest


def validate_practical_stage_workspace_hygiene(package_root: Path) -> list[ScopeFinding]:
    """Reject temporary package files left at a practical stage boundary.

    ``tmp/`` and ``work/debug/`` are deliberately not source or handoff
    locations. The check reports rather than removes files: a pre-existing
    user artifact must be resolved by the controller, never deleted by a
    workflow helper.
    """
    findings: list[ScopeFinding] = []
    for relative_root in (Path("tmp"), Path("work") / "debug"):
        root = package_root / relative_root
        if not root.is_dir():
            continue
        files = sorted(
            path for path in root.rglob("*")
            if path.is_file() and path.name != ".gitkeep"
        )
        if not files:
            continue
        paths = [relative_to_package(package_root, path) for path in files]
        findings.append(finding(
            "practical-stage-temporary-artifacts",
            "workspace-hygiene",
            "В пакете остались временные артефакты этапа",
            "Перед завершением этапа удалите созданные агентом временные файлы или перенесите "
            "нужное доказательство в именованный work-артефакт. Не удаляйте уже существовавшие "
            "пользовательские файлы без отдельного решения.",
            relative_root.as_posix(),
            evidence=paths,
            remediation_owner="controller",
            blocking=True,
        ))
    return findings


def clarification_requires_business_request(entry: dict[str, Any]) -> bool:
    """Keep only business ambiguities in the BA-facing companion file."""
    if entry.get("requires_business_answer") is True:
        return True
    # Compatibility with v0.9.2: a concrete analyst question was its only
    # marker that the gap required a BA answer.
    return bool(str(entry.get("question_to_analyst") or "").strip())


def parse_clarification_request_cards(
    content: str,
) -> tuple[dict[tuple[str, str], dict[str, str]], list[str]]:
    """Parse the deliberately narrow YAML profile used in CLR cards.

    Full YAML parsing would introduce a runtime dependency for one small,
    flat, user-facing record.  The canonical profile instead requires a flat
    map whose values are double-quoted YAML/JSON scalars.  This is valid YAML,
    handles punctuation in Russian prose, and is deterministic to validate
    with the standard library.
    """
    headers = list(CLARIFICATION_CARD_HEADER_RE.finditer(content))
    cards: dict[tuple[str, str], dict[str, str]] = {}
    errors: list[str] = []
    for index, header in enumerate(headers, start=1):
        card_end = headers[index].start() if index < len(headers) else len(content)
        body = content[header.end() : card_end]
        clarification_id = header.group("clarification_id")
        gap_id = header.group("gap_id")
        card_key = (clarification_id, gap_id)
        if card_key in cards:
            errors.append(f"повторяется карточка «{clarification_id} — {gap_id}»")
            continue
        fence = re.search(r"(?ms)^```yaml\s*\n(?P<payload>.*?)^```\s*$", body)
        if fence is None:
            errors.append(f"карточка «{clarification_id} — {gap_id}» не содержит YAML-блок")
            continue
        data: dict[str, str] = {}
        card_errors: list[str] = []
        for line_number, raw_line in enumerate(fence.group("payload").splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            match = re.fullmatch(r"(?P<key>[a-z_]+):\s*(?P<value>\"(?:\\\\.|[^\"\\\\])*\")", line)
            if match is None:
                card_errors.append(
                    f"строка {line_number}: ожидается ключ и значение в двойных кавычках"
                )
                continue
            key = match.group("key")
            if key in data:
                card_errors.append(f"повторяется поле {key}")
                continue
            try:
                data[key] = str(json.loads(match.group("value")))
            except json.JSONDecodeError:
                card_errors.append(f"некорректная строка YAML для {key}")
        if card_errors:
            details = "; ".join(card_errors[:3])
            suffix = "; …" if len(card_errors) > 3 else ""
            errors.append(f"карточка «{clarification_id} — {gap_id}»: {details}{suffix}")
        else:
            cards[card_key] = data
    return cards, errors


def parse_approved_ba_decision_cards(
    content: str,
) -> tuple[dict[str, dict[str, str]], list[str]]:
    """Parse the compact, package-level registry of approved BA decisions."""
    headers = list(APPROVED_BA_DECISION_CARD_HEADER_RE.finditer(content))
    cards: dict[str, dict[str, str]] = {}
    errors: list[str] = []
    for index, header in enumerate(headers, start=1):
        card_end = headers[index].start() if index < len(headers) else len(content)
        body = content[header.end() : card_end]
        decision_id = header.group("decision_id")
        if decision_id in cards:
            errors.append(f"повторяется карточка решения «{decision_id}»")
            continue
        fence = re.search(r"(?ms)^```yaml\s*\n(?P<payload>.*?)^```\s*$", body)
        if fence is None:
            errors.append(f"карточка решения «{decision_id}» не содержит YAML-блок")
            continue
        data: dict[str, str] = {}
        card_errors: list[str] = []
        for line_number, raw_line in enumerate(fence.group("payload").splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            match = re.fullmatch(r"(?P<key>[a-z_]+):\s*(?P<value>\"(?:\\\\.|[^\"\\\\])*\")", line)
            if match is None:
                card_errors.append(
                    f"строка {line_number}: ожидается ключ и значение в двойных кавычках"
                )
                continue
            key = match.group("key")
            if key in data:
                card_errors.append(f"повторяется поле {key}")
                continue
            try:
                data[key] = str(json.loads(match.group("value")))
            except json.JSONDecodeError:
                card_errors.append(f"некорректная строка YAML для {key}")
        if card_errors:
            details = "; ".join(card_errors[:3])
            suffix = "; …" if len(card_errors) > 3 else ""
            errors.append(f"карточка решения «{decision_id}»: {details}{suffix}")
            continue
        if data.get("decision_id") != decision_id:
            errors.append(
                f"карточка решения «{decision_id}»: decision_id={data.get('decision_id')!r} "
                "не совпадает с заголовком"
            )
            continue
        cards[decision_id] = data
    return cards, errors


def approved_ba_decision_registry_path(
    manifest: dict[str, Any], package_root: Path, artifact: str
) -> Path | None:
    entries = manifest.get("approved_ba_decisions", [])
    if not isinstance(entries, list) or len(entries) != 1 or not isinstance(entries[0], dict):
        return None
    try:
        return package_relative_path(package_root, entries[0].get("path"), artifact=artifact)
    except PracticalV09Error:
        return None


def load_approved_ba_decisions(
    manifest: dict[str, Any], package_root: Path, artifact: str
) -> tuple[dict[str, dict[str, str]], list[ScopeFinding]]:
    """Read decision cards after their manifest binding has been checked."""
    registry_path = approved_ba_decision_registry_path(manifest, package_root, artifact)
    if registry_path is None:
        return {}, []
    registry_artifact = relative_to_package(package_root, registry_path)
    if not registry_path.is_file():
        return {}, []
    try:
        content = registry_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return {}, [finding(
            "source-manifest-ba-decision-registry-unreadable",
            "source-integrity",
            "Не удалось прочитать реестр утверждённых решений БА",
            str(exc),
            registry_artifact,
            remediation_owner="controller",
        )]
    cards, errors = parse_approved_ba_decision_cards(content)
    findings: list[ScopeFinding] = []
    if not cards:
        findings.append(finding(
            "source-manifest-ba-decision-registry-empty",
            "source-integrity",
            "В реестре решений БА нет машиночитаемых утверждённых решений",
            "Нужна хотя бы одна карточка ## BA-DEC-* с YAML-профилем.",
            registry_artifact,
            remediation_owner="controller",
        ))
    for error in errors:
        findings.append(finding(
            "source-manifest-ba-decision-registry-format",
            "source-integrity",
            "Карточка решения БА не соответствует машиночитаемому профилю",
            error,
            registry_artifact,
            remediation_owner="controller",
        ))
    for decision_id, card in cards.items():
        missing = [field for field in APPROVED_BA_DECISION_REQUIRED_FIELDS if not card.get(field, "").strip()]
        if missing:
            findings.append(finding(
                "source-manifest-ba-decision-registry-fields",
                "semantic-completeness",
                "В карточке решения БА отсутствуют обязательные поля",
                f"{decision_id}: " + ", ".join(missing) + ".",
                registry_artifact,
                remediation_owner="controller",
            ))
        for field, allowed_values in APPROVED_BA_DECISION_ENUMS.items():
            value = card.get(field, "")
            if value and value not in allowed_values:
                findings.append(finding(
                    "source-manifest-ba-decision-registry-enum",
                    "semantic-completeness",
                    "У карточки решения БА некорректное значение поля",
                    f"{decision_id}: {field}={value!r}; допустимы: {', '.join(sorted(allowed_values))}.",
                    registry_artifact,
                    remediation_owner="controller",
                ))
    return cards, findings


def obligation_disposition(obligation: dict[str, Any]) -> str:
    return str(obligation.get("disposition") or "active")


def active_obligations(obligations: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in obligations.get("obligations", [])
        if isinstance(item, dict) and obligation_disposition(item) == "active"
    ]


def active_obligation_ids(obligations: dict[str, Any]) -> set[str]:
    return {str(item.get("id")) for item in active_obligations(obligations)}


def obligation_ids_sha256(obligation_ids: Iterable[str]) -> str:
    """Return a stable digest for the complete independently recovered OBL set."""
    payload = "\n".join(sorted(set(obligation_ids))).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def execution_setups(obligations: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return declared reusable execution prerequisites keyed by SETUP-* id."""
    entries = obligations.get("execution_setups", [])
    if not isinstance(entries, list):
        return {}
    return {
        str(item.get("id")): item
        for item in entries
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def provided_setup_artifacts(
    obligations: dict[str, Any],
    package_root: Path,
) -> list[tuple[str, Path]]:
    """Resolve immutable files cited by ``provided`` execution setups.

    A fixture may be created after the package-level source manifest.  It is
    still evidence for literals in a matrix/TC and must therefore be bound in
    the independent-review manifest.  The setup's ``artifacts`` field is
    deliberately explicit: prose in ``evidence`` is not a stable file
    reference and must not be parsed heuristically.
    """
    bound: list[tuple[str, Path]] = []
    seen_paths: set[str] = set()
    for setup in execution_setups(obligations).values():
        if str(setup.get("availability") or "") != "provided":
            continue
        setup_id = str(setup.get("id") or "")
        artifacts = setup.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            continue
        for index, raw_path in enumerate(artifacts, start=1):
            if not isinstance(raw_path, str) or not raw_path.strip():
                raise PracticalV09Error(
                    f"{setup_id}: provided setup artifacts must contain non-empty paths"
                )
            path = package_relative_path(
                package_root, raw_path, artifact=f"{setup_id}.artifacts"
            )
            if not path.is_file():
                raise PracticalV09Error(
                    f"{setup_id}: provided setup artifact is missing: "
                    + relative_to_package(package_root, path)
                )
            relative = relative_to_package(package_root, path)
            if relative in seen_paths:
                continue
            seen_paths.add(relative)
            bound.append((f"provided-setup-{setup_id}-{index}", path))
    return bound


def execution_contexts(obligation: dict[str, Any]) -> list[dict[str, Any]]:
    """Return explicitly declared user-execution contexts for one OBL."""
    entries = obligation.get("execution_contexts", [])
    return [item for item in entries if isinstance(item, dict)] if isinstance(entries, list) else []


def execution_context_flow_kind(context: Mapping[str, Any] | None) -> str | None:
    """Return the structured lifecycle kind for one execution context.

    Context IDs are traceability anchors, not a lifecycle API.  Rules that
    depend on creation or editing must use this explicit field instead of
    guessing from a free-form ``CTX-*`` identifier.
    """
    if not isinstance(context, Mapping):
        return None
    value = context.get("flow_kind")
    return value if isinstance(value, str) and value in ALLOWED_EXECUTION_FLOW_KINDS else None


def execution_setup_availability_scope(setup: dict[str, Any]) -> str:
    """Return the status scope of one SETUP entry.

    ``environment-access`` is intentionally limited to volatile delivery
    details such as a test-contour URL or a rotating account.  Those details
    are supplied outside canonical test cases and must not turn a
    source-complete scenario into ``needs-test-data``.  All existing entries
    default to ``business-test-data`` for backward compatibility.
    """
    return str(setup.get("availability_scope") or "business-test-data")


def setup_affects_execution_status(setup: dict[str, Any]) -> bool:
    """Return whether an unavailable setup is a material TC-data limitation."""
    return execution_setup_availability_scope(setup) != "environment-access"


def derived_execution_status(
    context: dict[str, Any],
    setup_catalog: dict[str, dict[str, Any]],
) -> str:
    """Derive the honest execution status from every prerequisite of a context."""
    setup_ids = context.get("setup_ids", [])
    required_kinds = context.get("required_setup_kinds", [])
    if not isinstance(setup_ids, list) or not isinstance(required_kinds, list):
        return "needs-test-data"
    selected = [setup_catalog.get(str(setup_id)) for setup_id in setup_ids]
    if any(item is None for item in selected):
        return "needs-test-data"
    kinds = {
        str(item.get("kind"))
        for item in selected
        if isinstance(item, dict)
    }
    if not set(required_kinds).issubset(kinds):
        return "needs-test-data"
    availability = {
        str(item.get("availability"))
        for item in selected
        if isinstance(item, dict) and setup_affects_execution_status(item)
    }
    for status in EXECUTION_STATUS_PRECEDENCE:
        if status in availability:
            return status
    return "ready"


def secondary_execution_limitations(
    context: dict[str, Any],
    setup_catalog: dict[str, dict[str, Any]],
) -> list[tuple[str, str]]:
    """Return unavailable prerequisites that are material but not primary.

    A test case has exactly one primary ``Статус исполнения``.  This helper
    preserves the other unavailable prerequisite types so that, for example,
    missing data does not hide a separate unresolved UI interaction.
    """
    primary_status = derived_execution_status(context, setup_catalog)
    setup_ids = context.get("setup_ids", [])
    if not isinstance(setup_ids, list):
        return []
    limitations: list[tuple[str, str]] = []
    for setup_id in setup_ids:
        setup = setup_catalog.get(str(setup_id))
        if not isinstance(setup, dict):
            continue
        if not setup_affects_execution_status(setup):
            continue
        availability = str(setup.get("availability") or "")
        if (
            availability in ALLOWED_EXECUTION_STATUSES
            and availability != primary_status
        ):
            limitations.append((str(setup_id), availability))
    return limitations


def has_russian_prose(value: str) -> bool:
    """Return whether a user-facing limitation contains an explanation."""
    return bool(re.search(r"[А-Яа-яЁё]{3,}", value))


def context_id_from_cell(value: object) -> str:
    """Extract exactly one CTX-* token from a human-readable matrix/TC field."""
    matches = re.findall(r"\bCTX-[A-Z0-9-]+\b", str(value or ""))
    return matches[0] if len(matches) == 1 else ""


def validate_scope_clarifications(
    *,
    payload: dict[str, Any],
    obligations_path: Path,
    package_root: Path,
    obligation_ids: set[str],
    obligation_ba_decisions: dict[str, str],
    approved_ba_decisions: dict[str, dict[str, str]],
) -> list[ScopeFinding]:
    """Validate the compact gap register and its conditional BA companion."""
    artifact = relative_to_package(package_root, obligations_path)
    clarifications = payload.get("clarifications", [])
    if not isinstance(clarifications, list):
        return [finding(
            "scope-clarifications-format",
            "source-integrity",
            "Некорректен формат gaps scope",
            "Поле clarifications должно быть массивом GAP-*.",
            artifact,
            remediation_owner="scope-analyzer",
        )]

    findings: list[ScopeFinding] = []
    seen_gap_ids: set[str] = set()
    requests_path = clarification_requests_path(obligations_path)
    request_cards: dict[tuple[str, str], dict[str, str]] | None = None
    requests_text: str | None = None
    business_entries = business_clarification_entries(payload)

    if requests_path.is_file():
        try:
            requests_text = requests_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            findings.append(finding(
                "scope-clarification-request-unreadable",
                "source-integrity",
                "Не удалось прочитать файл вопросов к БА",
                str(exc),
                relative_to_package(package_root, requests_path),
                remediation_owner="scope-analyzer",
            ))
            request_cards = {}
        else:
            missing_sections = missing_clarification_request_sections(requests_text)
            if missing_sections:
                findings.append(finding(
                    "scope-clarification-request-sections",
                    "semantic-completeness",
                    "Файл вопросов к БА не содержит обязательные русскоязычные разделы",
                    "Отсутствуют разделы: " + ", ".join(f"«{section}»" for section in missing_sections) + ".",
                    relative_to_package(package_root, requests_path),
                    remediation_owner="scope-analyzer",
                ))
            request_cards, parse_errors = parse_clarification_request_cards(requests_text)
            for error in parse_errors:
                findings.append(finding(
                    "scope-clarification-request-yaml",
                    "source-integrity",
                    "Карточка вопроса БА не соответствует машиночитаемому YAML-профилю",
                    error,
                    relative_to_package(package_root, requests_path),
                    remediation_owner="scope-analyzer",
                ))
            if not business_entries and NO_BUSINESS_QUESTIONS_MARKER not in requests_text:
                findings.append(finding(
                    "scope-clarification-outcome-none",
                    "semantic-completeness",
                    "Файл вопросов к БА не фиксирует отсутствие вопросов",
                    f"При отсутствии вопросов добавьте точный итог: «{NO_BUSINESS_QUESTIONS_MARKER}».",
                    relative_to_package(package_root, requests_path),
                    remediation_owner="scope-analyzer",
                ))

    for index, entry in enumerate(clarifications, start=1):
        if not isinstance(entry, dict):
            findings.append(finding(
                "scope-clarification-invalid",
                "source-integrity",
                "Строка gaps scope имеет неверный формат",
                f"clarifications[{index}] должен быть объектом.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
            continue
        gap_id = str(entry.get("id") or "")
        if not re.fullmatch(r"GAP-[A-Z0-9-]+", gap_id):
            findings.append(finding(
                "scope-clarification-id",
                "traceability",
                "У gap некорректный идентификатор",
                f"clarifications[{index}].id={gap_id!r}; ожидается GAP-*.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
        elif gap_id in seen_gap_ids:
            findings.append(finding(
                "scope-clarification-duplicate",
                "traceability",
                "В scope повторяется GAP-ID",
                f"Повторяется {gap_id}.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
        seen_gap_ids.add(gap_id)

        for field in ("source_anchor", "source_statement", "description", "temporary_handling"):
            if not str(entry.get(field) or "").strip():
                findings.append(finding(
                    "scope-clarification-incomplete",
                    "unresolved-requirement",
                    "Gap не содержит обязательный контекст",
                    f"{gap_id or f'строка {index}'}: отсутствует «{field}».",
                    artifact,
                    remediation_owner="scope-analyzer",
                ))
        gap_type = str(entry.get("gap_type") or "")
        if gap_type not in ALLOWED_GAP_TYPES:
            findings.append(finding(
                "scope-clarification-type",
                "semantic-completeness",
                "У gap указан неизвестный тип",
                f"{gap_id or f'строка {index}'}: «{gap_type}» не входит в допустимый перечень.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
        impact = str(entry.get("impact") or "")
        if impact not in {"blocking", "non-blocking"}:
            findings.append(finding(
                "scope-clarification-impact",
                "semantic-completeness",
                "У gap не указан корректный impact",
                f"{gap_id or f'строка {index}'}: ожидается blocking или non-blocking.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
        status = str(entry.get("status") or "")
        if status not in ALLOWED_GAP_STATUSES:
            findings.append(finding(
                "scope-clarification-status",
                "semantic-completeness",
                "У gap не указан корректный статус",
                f"{gap_id or f'строка {index}'}: ожидается open или resolved.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
        if gap_type == "ui-calibration":
            visual_check = entry.get("visual_evidence_check")
            if not isinstance(visual_check, dict):
                findings.append(finding(
                    "scope-ui-calibration-visual-check",
                    "semantic-completeness",
                    "Перед UI-калибровкой не зафиксирована проверка визуальных источников",
                    f"{gap_id or f'строка {index}'}: добавьте visual_evidence_check с проверенными "
                    "изображениями ФТ/макетами и остаточной runtime-неопределённостью.",
                    artifact,
                    remediation_owner="scope-analyzer",
                ))
            else:
                outcome = str(visual_check.get("outcome") or "")
                checked_sources = visual_check.get("checked_sources")
                remaining_uncertainty = str(
                    visual_check.get("remaining_uncertainty") or ""
                ).strip()
                if outcome not in ALLOWED_VISUAL_EVIDENCE_OUTCOMES:
                    findings.append(finding(
                        "scope-ui-calibration-visual-outcome",
                        "semantic-completeness",
                        "У проверки визуальных источников неизвестный результат",
                        f"{gap_id}: outcome={outcome!r}; допустимы: "
                        + ", ".join(sorted(ALLOWED_VISUAL_EVIDENCE_OUTCOMES)) + ".",
                        artifact,
                        remediation_owner="scope-analyzer",
                    ))
                if (
                    not isinstance(checked_sources, list)
                    or not checked_sources
                    or not all(isinstance(source, str) and source.strip() for source in checked_sources)
                ):
                    findings.append(finding(
                        "scope-ui-calibration-visual-sources",
                        "semantic-completeness",
                        "Проверка UI-калибровки не перечисляет проверенные визуальные источники",
                        f"{gap_id}: checked_sources должен быть непустым списком изображений ФТ, "
                        "макетов либо явной фиксации отсутствия такого изображения.",
                        artifact,
                        remediation_owner="scope-analyzer",
                    ))
                if not remaining_uncertainty:
                    findings.append(finding(
                        "scope-ui-calibration-visual-residual",
                        "semantic-completeness",
                        "Для UI-калибровки не указана остаточная runtime-неопределённость",
                        f"{gap_id}: опишите только то, что нельзя установить по проверенным "
                        "визуальным материалам.",
                        artifact,
                        remediation_owner="scope-analyzer",
                    ))
        affected = entry.get("affected_obligation_ids", [])
        if not isinstance(affected, list) or not affected or not all(isinstance(item, str) for item in affected):
            findings.append(finding(
                "scope-clarification-obligations-format",
                "traceability",
                "У gap нет корректной связи с обязательствами",
                f"{gap_id or f'строка {index}'}: affected_obligation_ids должен быть непустым массивом OBL-*.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
        else:
            unknown_obligations = sorted(set(affected) - obligation_ids)
            if unknown_obligations:
                findings.append(finding(
                    "scope-clarification-unknown-obligation",
                    "traceability",
                    "Gap ссылается на отсутствующее обязательство",
                    f"{gap_id}: " + ", ".join(unknown_obligations) + ".",
                    artifact,
                    remediation_owner="scope-analyzer",
                ))

        requires_request = clarification_requires_business_request(entry)
        if gap_type == "ba-decision-required" and status == "open":
            if entry.get("requires_business_answer") is not True:
                findings.append(finding(
                    "scope-ba-decision-request-flag",
                    "unresolved-requirement",
                    "Неразрешённое противоречие ФТ не помечено как вопрос к БА",
                    f"{gap_id}: для открытого ba-decision-required требуется requires_business_answer=true.",
                    artifact,
                    remediation_owner="scope-analyzer",
                ))
            requires_request = True
        clarification_id = str(entry.get("clarification_id") or "")
        if requires_request:
            if not re.fullmatch(r"CLR-[A-Z0-9-]+", clarification_id):
                findings.append(finding(
                    "scope-clarification-request-id",
                    "traceability",
                    "Вопросу к БА не присвоен CLR-ID",
                    f"{gap_id}: требуется clarification_id формата CLR-*.",
                    artifact,
                    remediation_owner="scope-analyzer",
                ))
            if not requests_path.is_file():
                findings.append(finding(
                    "scope-clarification-request-missing",
                    "unresolved-requirement",
                    "Не создан файл вопросов к БА",
                    f"Для {gap_id} нужен {relative_to_package(package_root, requests_path)}.",
                    artifact,
                    remediation_owner="scope-analyzer",
                ))
            else:
                card = (request_cards or {}).get((clarification_id, gap_id))
                header_exists = bool(
                    clarification_id
                    and requests_text
                    and re.search(
                        rf"(?m)^###\s+{re.escape(clarification_id)}\s+[—-]\s+{re.escape(gap_id)}\b",
                        requests_text,
                    )
                )
                if clarification_id and card is None and not header_exists:
                    findings.append(finding(
                        "scope-clarification-request-link",
                        "traceability",
                        "Файл вопросов к БА не связан с GAP",
                        f"Не найдена карточка «{clarification_id} — {gap_id}».",
                        relative_to_package(package_root, requests_path),
                        remediation_owner="scope-analyzer",
                    ))
                elif card is not None:
                    missing_fields = [
                        field for field in CLARIFICATION_REQUEST_REQUIRED_FIELDS
                        if not card.get(field, "").strip()
                    ]
                    if missing_fields:
                        findings.append(finding(
                            "scope-clarification-request-fields",
                            "semantic-completeness",
                            "В карточке вопроса БА отсутствуют обязательные поля",
                            f"{clarification_id} — {gap_id}: " + ", ".join(missing_fields) + ".",
                            relative_to_package(package_root, requests_path),
                            remediation_owner="scope-analyzer",
                        ))
                    expected_scope_slug = str((payload.get("scope") or {}).get("slug") or "")
                    mismatches: list[str] = []
                    for field, expected in (
                        ("clarification_id", clarification_id),
                        ("gap_id", gap_id),
                        ("request_kind", "ba-business-ambiguity"),
                        ("scope_slug", expected_scope_slug),
                    ):
                        if expected and card.get(field) != expected:
                            mismatches.append(f"{field}={card.get(field)!r}, ожидается {expected!r}")
                    related_obligation_ids = {
                        value.strip()
                        for value in card.get("related_obligation_ids", "").split(";")
                        if value.strip()
                    }
                    missing_related = sorted(set(affected) - related_obligation_ids)
                    if missing_related:
                        mismatches.append(
                            "related_obligation_ids не содержит " + ", ".join(missing_related)
                        )
                    for field, allowed_values in CLARIFICATION_REQUEST_ENUMS.items():
                        value = card.get(field, "")
                        if value and value not in allowed_values:
                            mismatches.append(
                                f"{field}={value!r} не входит в допустимый перечень"
                            )
                    if mismatches:
                        findings.append(finding(
                            "scope-clarification-request-binding",
                            "traceability",
                            "Карточка вопроса БА не согласована с реестром gaps",
                            f"{clarification_id} — {gap_id}: " + "; ".join(mismatches) + ".",
                            relative_to_package(package_root, requests_path),
                            remediation_owner="scope-analyzer",
                        ))

        if status == "resolved":
            resolution = str(entry.get("resolution") or "")
            if resolution.startswith("approved-ba-decision:"):
                decision_id = resolution.partition(":")[2]
                decision = approved_ba_decisions.get(decision_id)
                if decision is None:
                    findings.append(finding(
                        "scope-ba-decision-missing",
                        "source-integrity",
                        "Закрытый gap ссылается на отсутствующее утверждённое решение БА",
                        f"{gap_id}: не найдено решение {decision_id or '<без ID>'} в package-level реестре.",
                        artifact,
                        remediation_owner="scope-analyzer",
                    ))
                elif decision.get("decision_type") != "supersedes-ft":
                    findings.append(finding(
                        "scope-ba-decision-resolution-type",
                        "traceability",
                        "Закрытый gap ссылается на уточнение БА вместо изменения требования",
                        f"{gap_id}: {decision_id} имеет decision_type={decision.get('decision_type')!r}; "
                        "для resolution=approved-ba-decision требуется supersedes-ft.",
                        artifact,
                        remediation_owner="scope-analyzer",
                    ))
                declared_decision = str(entry.get("ba_decision_id") or "")
                if declared_decision != decision_id:
                    findings.append(finding(
                        "scope-ba-decision-gap-link",
                        "traceability",
                        "Закрытый gap не связан с решением БА явным полем",
                        f"{gap_id}: ba_decision_id должен совпадать с {decision_id!r}.",
                        artifact,
                        remediation_owner="scope-analyzer",
                    ))
                for obligation_id in affected if isinstance(affected, list) else []:
                    if obligation_ba_decisions.get(obligation_id) != decision_id:
                        findings.append(finding(
                            "scope-ba-decision-obligation-link",
                            "traceability",
                            "Решение БА не применено к связанному обязательству",
                            f"{gap_id}: {obligation_id} должен иметь disposition=superseded-by-ba-decision "
                            f"и ba_decision_id={decision_id}.",
                            artifact,
                            remediation_owner="scope-analyzer",
                        ))
                continue
            expected_resolution = f"approved-clarification:{clarification_id}" if clarification_id else ""
            approved_path = str(entry.get("approved_clarification_path") or "")
            approved_hash = str(entry.get("approved_clarification_sha256") or "")
            if not expected_resolution or resolution != expected_resolution:
                findings.append(finding(
                    "scope-clarification-resolution",
                    "traceability",
                    "Закрытый gap не связан с подтверждённым ответом",
                    f"{gap_id}: ожидается resolution={expected_resolution or 'approved-clarification:CLR-*'}.",
                    artifact,
                    remediation_owner="scope-analyzer",
                ))
            try:
                approved_file = package_relative_path(
                    package_root,
                    approved_path,
                    artifact=artifact,
                )
            except PracticalV09Error as exc:
                findings.append(finding(
                    "scope-clarification-approved-path",
                    "source-integrity",
                    "Некорректен путь к подтверждённому ответу БА",
                    f"{gap_id}: {exc}",
                    artifact,
                    remediation_owner="scope-analyzer",
                ))
            else:
                if not approved_file.is_file():
                    findings.append(finding(
                        "scope-clarification-approved-missing",
                        "source-integrity",
                        "Подтверждённый ответ БА отсутствует",
                        f"{gap_id}: не найден {approved_path}.",
                        artifact,
                        remediation_owner="scope-analyzer",
                    ))
                elif not approved_hash or approved_hash != sha256_file(approved_file):
                    findings.append(finding(
                        "scope-clarification-approved-hash",
                        "source-integrity",
                        "Контрольная сумма подтверждённого ответа БА не совпадает",
                        f"{gap_id}: approved_clarification_sha256 должен совпадать с {approved_path}.",
                        artifact,
                        remediation_owner="scope-analyzer",
                    ))
    return findings


def validate_scope_obligations(
    obligations_path: Path,
    package_root: Path,
    source_manifest_path: Path,
) -> tuple[list[ScopeFinding], dict[str, Any]]:
    artifact = relative_to_package(package_root, obligations_path)
    try:
        payload = read_json(obligations_path)
    except PracticalV09Error as exc:
        return [finding("scope-obligations-unreadable", "source-integrity", "Недоступен реестр обязательств scope", str(exc), artifact, remediation_owner="controller")], {}
    findings: list[ScopeFinding] = []
    if payload.get("route_version") != ROUTE_VERSION:
        findings.append(finding("scope-obligations-route-version", "source-integrity", "У реестра обязательств неверная версия маршрута", f"Ожидается {ROUTE_VERSION}.", artifact, remediation_owner="controller"))
    if str(payload.get("source_manifest_sha256") or "") != sha256_file(source_manifest_path):
        findings.append(finding("scope-obligations-source-manifest-stale", "source-integrity", "Реестр обязательств не связан с текущим манифестом источников", "Пересоберите scope-obligations.json от неизменённого source-package-manifest.json.", artifact, remediation_owner="controller"))
    try:
        source_manifest = read_json(source_manifest_path)
    except PracticalV09Error:
        source_manifest = {}
    approved_ba_decisions, _ = load_approved_ba_decisions(
        source_manifest,
        package_root,
        relative_to_package(package_root, source_manifest_path),
    )
    obligations = payload.get("obligations")
    if not isinstance(obligations, list) or not obligations:
        findings.append(finding("scope-obligations-empty", "unresolved-requirement", "В scope не зафиксированы проверяемые обязательства", "Нужен хотя бы один OBL-* с source_anchor и формулировкой требования.", artifact, remediation_owner="scope-analyzer"))
        return findings, payload
    seen: set[str] = set()
    obligation_ba_decisions: dict[str, str] = {}
    raw_setups = payload.get("execution_setups")
    if not isinstance(raw_setups, list):
        findings.append(finding(
            "scope-execution-setups-format",
            "execution-readiness",
            "В scope не задан корректный каталог предпосылок исполнения",
            "execution_setups должен быть массивом SETUP-*; он описывает акторов, fixture, интеграции и исходные состояния.",
            artifact,
            remediation_owner="scope-analyzer",
        ))
        raw_setups = []
    seen_setup_ids: set[str] = set()
    for index, setup in enumerate(raw_setups, start=1):
        if not isinstance(setup, dict):
            findings.append(finding(
                "scope-execution-setup-invalid",
                "execution-readiness",
                "Строка каталога предпосылок имеет неверный формат",
                f"execution_setups[{index}] должен быть объектом.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
            continue
        setup_id = str(setup.get("id") or "")
        kind = str(setup.get("kind") or "")
        availability = str(setup.get("availability") or "")
        availability_scope = execution_setup_availability_scope(setup)
        evidence = str(setup.get("evidence") or "").strip()
        setup_artifacts = setup.get("artifacts")
        if not EXECUTION_SETUP_ID_RE.fullmatch(setup_id):
            findings.append(finding(
                "scope-execution-setup-id",
                "traceability",
                "У предпосылки исполнения некорректный идентификатор",
                f"execution_setups[{index}].id={setup_id!r}; ожидается SETUP-*.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
        elif setup_id in seen_setup_ids:
            findings.append(finding(
                "scope-execution-setup-duplicate",
                "traceability",
                "В каталоге повторяется предпосылка исполнения",
                f"Повторяется {setup_id}.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
        seen_setup_ids.add(setup_id)
        if kind not in ALLOWED_EXECUTION_SETUP_KINDS:
            findings.append(finding(
                "scope-execution-setup-kind",
                "execution-readiness",
                "У предпосылки указан неизвестный вид",
                f"{setup_id or f'строка {index}'}: kind={kind!r}; допустимы: "
                + ", ".join(sorted(ALLOWED_EXECUTION_SETUP_KINDS)) + ".",
                artifact,
                remediation_owner="scope-analyzer",
            ))
        if availability not in ALLOWED_EXECUTION_SETUP_AVAILABILITY:
            findings.append(finding(
                "scope-execution-setup-availability",
                "execution-readiness",
                "У предпосылки указан неизвестный статус доступности",
                f"{setup_id or f'строка {index}'}: availability={availability!r}.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
        if availability_scope not in ALLOWED_EXECUTION_SETUP_AVAILABILITY_SCOPES:
            findings.append(finding(
                "scope-execution-setup-availability-scope",
                "execution-readiness",
                "У предпосылки указан неизвестный контур доступности",
                f"{setup_id or f'строка {index}'}: availability_scope={availability_scope!r}; допустимы: "
                + ", ".join(sorted(ALLOWED_EXECUTION_SETUP_AVAILABILITY_SCOPES)) + ".",
                artifact,
                remediation_owner="scope-analyzer",
            ))
        if availability_scope == "environment-access" and setup_artifacts:
            findings.append(finding(
                "scope-execution-environment-access-artifacts",
                "execution-readiness",
                "Волатильная среда не должна храниться в артефактах FT-пакета",
                f"{setup_id or f'строка {index}'}: удалите artifacts; URL, логины и иные параметры среды передаются исполнителю вне FT-пакета.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
        if availability_scope == "environment-access" and availability != "provided":
            findings.append(finding(
                "scope-execution-environment-access-availability",
                "execution-readiness",
                "Волатильный доступ к среде ошибочно указан как тестовые данные",
                f"{setup_id or f'строка {index}'}: для availability_scope=environment-access укажите availability=provided; "
                "конкретные URL и учётная запись передаются исполнителю отдельно и не являются зависимостью TC.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
        if (
            availability_scope == "environment-access"
            and VOLATILE_ENVIRONMENT_CONFIGURATION_RE.search(evidence)
        ):
            findings.append(finding(
                "scope-execution-environment-access-secret",
                "security",
                "Волатильная предпосылка раскрывает параметры среды",
                f"{setup_id or f'строка {index}'}: не записывайте URL, логин, пароль, токен или cookie в FT-пакет; укажите только нейтральное подтверждение доступа.",
                artifact,
                remediation_owner="scope-analyzer",
                blocking=True,
                blocking_reason="В FT-пакете нельзя хранить параметры доступа к тестовой среде.",
            ))
        if not evidence:
            findings.append(finding(
                "scope-execution-setup-evidence",
                "execution-readiness",
                "Для предпосылки не указано подтверждение подготовки",
                f"{setup_id or f'строка {index}'}: укажите воспроизводимый способ подготовки или источник доступности.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
        if setup_artifacts is not None and (
            not isinstance(setup_artifacts, list)
            or not setup_artifacts
            or not all(isinstance(item, str) and item.strip() for item in setup_artifacts)
        ):
            findings.append(finding(
                "scope-execution-setup-artifacts",
                "execution-readiness",
                "У предпосылки некорректно указан набор файлов-доказательств",
                f"{setup_id or f'строка {index}'}: artifacts должен быть непустым массивом путей к файлам.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
        elif isinstance(setup_artifacts, list):
            for raw_path in setup_artifacts:
                try:
                    artifact_path = package_relative_path(
                        package_root, raw_path, artifact=f"{setup_id}.artifacts"
                    )
                except PracticalV09Error as exc:
                    findings.append(finding(
                        "scope-execution-setup-artifact-path",
                        "execution-readiness",
                        "Файл-доказательство предпосылки находится вне FT-пакета",
                        str(exc),
                        artifact,
                        remediation_owner="scope-analyzer",
                    ))
                    continue
                if not artifact_path.is_file():
                    findings.append(finding(
                        "scope-execution-setup-artifact-missing",
                        "execution-readiness",
                        "Файл-доказательство предпосылки отсутствует",
                        f"{setup_id}: не найден {relative_to_package(package_root, artifact_path)}.",
                        artifact,
                        remediation_owner="scope-analyzer",
                    ))
        if availability == "provided" and kind == "fixture" and not setup_artifacts:
            findings.append(finding(
                "scope-execution-provided-fixture-artifacts",
                "execution-readiness",
                "Для предоставленного fixture не зафиксированы неизменяемые файлы",
                f"{setup_id or f'строка {index}'}: добавьте artifacts со snapshot/verification/catalog файлами, используемыми в matrix и TC.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
    setup_catalog = execution_setups(payload)
    for index, obligation in enumerate(obligations, start=1):
        if not isinstance(obligation, dict):
            findings.append(finding("scope-obligation-invalid", "source-integrity", "Строка реестра обязательств имеет неверный формат", f"obligations[{index}] должен быть объектом.", artifact, remediation_owner="scope-analyzer"))
            continue
        obligation_id = str(obligation.get("id") or "")
        statement = str(obligation.get("statement") or "")
        source_anchor = str(obligation.get("source_anchor") or "")
        if not re.fullmatch(r"OBL-[A-Z0-9-]+", obligation_id):
            findings.append(finding("scope-obligation-id", "traceability", "У обязательства некорректный идентификатор", f"obligations[{index}].id={obligation_id!r}; ожидается OBL-*.", artifact, remediation_owner="scope-analyzer"))
        elif obligation_id in seen:
            findings.append(finding("scope-obligation-duplicate", "traceability", "В реестре повторяется идентификатор обязательства", f"Повторяется {obligation_id}.", artifact, remediation_owner="scope-analyzer"))
        seen.add(obligation_id)
        if not statement or not source_anchor:
            findings.append(finding("scope-obligation-incomplete", "unresolved-requirement", "Обязательство не содержит формулировку или привязку к ФТ", f"{obligation_id or f'строка {index}'} требует statement и source_anchor.", artifact, remediation_owner="scope-analyzer"))
        visual_binding = obligation.get("visual_binding")
        if visual_binding is not None:
            if not isinstance(visual_binding, dict):
                findings.append(finding(
                    "scope-obligation-visual-binding-format",
                    "semantic-completeness",
                    "Визуальная привязка обязательства имеет неверный формат",
                    f"{obligation_id}: visual_binding должен содержать source_anchor, element и location.",
                    artifact,
                    remediation_owner="scope-analyzer",
                ))
            else:
                missing_binding_fields = [
                    field
                    for field in ("source_anchor", "element", "location")
                    if not str(visual_binding.get(field) or "").strip()
                ]
                if missing_binding_fields:
                    findings.append(finding(
                        "scope-obligation-visual-binding-incomplete",
                        "semantic-completeness",
                        "Визуальная привязка обязательства неполна",
                        f"{obligation_id}: отсутствуют " + ", ".join(missing_binding_fields) + ".",
                        artifact,
                        remediation_owner="scope-analyzer",
                    ))
        disposition = obligation_disposition(obligation)
        if disposition not in OBLIGATION_DISPOSITIONS:
            findings.append(finding(
                "scope-obligation-disposition",
                "semantic-completeness",
                "У обязательства указан неизвестный disposition",
                f"{obligation_id or f'строка {index}'}: «{disposition}» не входит в допустимый перечень.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
        if disposition == "superseded-by-ba-decision":
            decision_id = str(obligation.get("ba_decision_id") or "")
            obligation_ba_decisions[obligation_id] = decision_id
            decision = approved_ba_decisions.get(decision_id)
            if decision is None:
                findings.append(finding(
                    "scope-obligation-ba-decision",
                    "traceability",
                    "Исключённое обязательство не связано с утверждённым решением БА",
                    f"{obligation_id}: ba_decision_id={decision_id or '<не указан>'} не найден в package-level реестре.",
                    artifact,
                    remediation_owner="scope-analyzer",
                ))
            elif decision.get("decision_type") != "supersedes-ft":
                findings.append(finding(
                    "scope-obligation-ba-decision-type",
                    "traceability",
                    "Исключённое обязательство связано с уточнением БА вместо изменения требования",
                    f"{obligation_id}: {decision_id} имеет decision_type={decision.get('decision_type')!r}; "
                    "disposition=superseded-by-ba-decision требует supersedes-ft.",
                    artifact,
                    remediation_owner="scope-analyzer",
                ))
        elif str(obligation.get("ba_decision_id") or ""):
            findings.append(finding(
                "scope-obligation-ba-decision-active",
                "traceability",
                "Активное обязательство не должно содержать решение, отменяющее требование",
                f"{obligation_id}: ba_decision_id допустим только при disposition=superseded-by-ba-decision.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
        findings.extend(validate_visual_label_mappings(
            obligation_id=obligation_id,
            obligation=obligation,
            artifact=artifact,
        ))
        if disposition == "active":
            common_result_for = obligation.get("common_result_for_obligation_ids")
            if common_result_for is not None:
                if (
                    not isinstance(common_result_for, list)
                    or len(common_result_for) < 2
                    or len(set(common_result_for)) != len(common_result_for)
                    or not all(
                        isinstance(item, str)
                        and re.fullmatch(r"OBL-[A-Z0-9-]+", item)
                        for item in common_result_for
                    )
                    or obligation_id in common_result_for
                ):
                    findings.append(finding(
                        "scope-obligation-common-result-format",
                        "semantic-completeness",
                        "Общий результат отказа связан с классами невалидного ввода некорректно",
                        f"{obligation_id}: common_result_for_obligation_ids должен содержать два и более разных OBL-* без самого обязательства.",
                        artifact,
                        remediation_owner="scope-analyzer",
                    ))
                else:
                    unknown_common_result_ids = sorted(
                        set(common_result_for) - set(
                            str(item.get("id") or "")
                            for item in obligations
                            if isinstance(item, dict)
                        )
                    )
                    if unknown_common_result_ids:
                        findings.append(finding(
                            "scope-obligation-common-result-target-unknown",
                            "traceability",
                            "Общий результат отказа ссылается на отсутствующий класс невалидного ввода",
                            f"{obligation_id}: не найдены " + ", ".join(unknown_common_result_ids) + ".",
                            artifact,
                            remediation_owner="scope-analyzer",
                        ))
                    if not required_message_literals(statement):
                        findings.append(finding(
                            "scope-obligation-common-result-message",
                            "semantic-completeness",
                            "Общий результат отказа не содержит точного результата из ФТ",
                            f"{obligation_id}: common_result_for_obligation_ids допустим только для обязательства с точным текстом сообщения или иным дословным общим результатом.",
                            artifact,
                            remediation_owner="scope-analyzer",
                        ))
            raw_contexts = obligation.get("execution_contexts")
            if not isinstance(raw_contexts, list) or not raw_contexts:
                findings.append(finding(
                    "scope-obligation-execution-contexts",
                    "execution-readiness",
                    "У активного обязательства не указаны контексты исполнения",
                    f"{obligation_id or f'строка {index}'} требует непустой execution_contexts с CTX-*.",
                    artifact,
                    remediation_owner="scope-analyzer",
                ))
            else:
                seen_context_ids: set[str] = set()
                for context_index, context in enumerate(raw_contexts, start=1):
                    if not isinstance(context, dict):
                        findings.append(finding(
                            "scope-obligation-execution-context-invalid",
                            "execution-readiness",
                            "Контекст исполнения имеет неверный формат",
                            f"{obligation_id}: execution_contexts[{context_index}] должен быть объектом.",
                            artifact,
                            remediation_owner="scope-analyzer",
                        ))
                        continue
                    context_id = str(context.get("id") or "")
                    label = str(context.get("label") or "").strip()
                    flow_kind = execution_context_flow_kind(context)
                    required_kinds = context.get("required_setup_kinds")
                    setup_ids = context.get("setup_ids")
                    if not EXECUTION_CONTEXT_ID_RE.fullmatch(context_id):
                        findings.append(finding(
                            "scope-obligation-execution-context-id",
                            "traceability",
                            "У контекста исполнения некорректный идентификатор",
                            f"{obligation_id}: execution_contexts[{context_index}].id={context_id!r}; ожидается CTX-*.",
                            artifact,
                            remediation_owner="scope-analyzer",
                        ))
                    elif context_id in seen_context_ids:
                        findings.append(finding(
                            "scope-obligation-execution-context-duplicate",
                            "traceability",
                            "У обязательства повторяется контекст исполнения",
                            f"{obligation_id}: повторяется {context_id}.",
                            artifact,
                            remediation_owner="scope-analyzer",
                        ))
                    seen_context_ids.add(context_id)
                    if not label:
                        findings.append(finding(
                            "scope-obligation-execution-context-label",
                            "execution-readiness",
                            "У контекста исполнения нет понятного названия",
                            f"{obligation_id}: {context_id or f'строка {context_index}'} требует русскоязычный label.",
                            artifact,
                            remediation_owner="scope-analyzer",
                        ))
                    if flow_kind is None:
                        findings.append(finding(
                            "scope-obligation-execution-context-flow-kind",
                            "execution-readiness",
                            "У контекста исполнения не указан тип пользовательского потока",
                            f"{obligation_id}: {context_id or f'строка {context_index}'} требует flow_kind: "
                            + ", ".join(sorted(ALLOWED_EXECUTION_FLOW_KINDS)) + ".",
                            artifact,
                            remediation_owner="scope-analyzer",
                        ))
                    if (
                        not isinstance(required_kinds, list)
                        or not all(isinstance(kind, str) for kind in required_kinds)
                        or "actor" not in required_kinds
                    ):
                        findings.append(finding(
                            "scope-obligation-execution-context-required-kinds",
                            "execution-readiness",
                            "Контекст не фиксирует полный набор предпосылок",
                            f"{obligation_id}: {context_id or f'строка {context_index}'} требует required_setup_kinds, включая actor.",
                            artifact,
                            remediation_owner="scope-analyzer",
                        ))
                        required_kinds = []
                    else:
                        unknown_kinds = sorted(set(required_kinds) - ALLOWED_EXECUTION_SETUP_KINDS)
                        if unknown_kinds:
                            findings.append(finding(
                                "scope-obligation-execution-context-required-kinds-unknown",
                                "execution-readiness",
                                "Контекст содержит неизвестный вид предпосылки",
                                f"{obligation_id}: {context_id}: " + ", ".join(unknown_kinds) + ".",
                                artifact,
                                remediation_owner="scope-analyzer",
                            ))
                    if (
                        not isinstance(setup_ids, list)
                        or not setup_ids
                        or not all(isinstance(item, str) and EXECUTION_SETUP_ID_RE.fullmatch(item) for item in setup_ids)
                    ):
                        findings.append(finding(
                            "scope-obligation-execution-context-setups",
                            "execution-readiness",
                            "Контекст не связан с предпосылками исполнения",
                            f"{obligation_id}: {context_id or f'строка {context_index}'} требует непустой setup_ids с SETUP-*.",
                            artifact,
                            remediation_owner="scope-analyzer",
                        ))
                    else:
                        missing_setup_ids = sorted(set(setup_ids) - set(setup_catalog))
                        if missing_setup_ids:
                            findings.append(finding(
                                "scope-obligation-execution-context-setup-missing",
                                "execution-readiness",
                                "Контекст ссылается на отсутствующую предпосылку",
                                f"{obligation_id}: {context_id}: " + ", ".join(missing_setup_ids) + ".",
                                artifact,
                                remediation_owner="scope-analyzer",
                            ))
                        selected_kinds = {
                            str(setup_catalog[setup_id].get("kind"))
                            for setup_id in setup_ids
                            if setup_id in setup_catalog
                        }
                        missing_kinds = sorted(set(required_kinds) - selected_kinds)
                        if missing_kinds:
                            findings.append(finding(
                                "scope-obligation-execution-context-required-setup-missing",
                                "execution-readiness",
                                "Контекст не связан со всеми обязательными видами предпосылок",
                                f"{obligation_id}: {context_id}: " + ", ".join(missing_kinds) + ".",
                                artifact,
                                remediation_owner="scope-analyzer",
                            ))
        risk_flags = obligation.get("risk_flags", [])
        if not isinstance(risk_flags, list) or not all(isinstance(flag, str) for flag in risk_flags):
            findings.append(finding("scope-obligation-risk-flags-format", "semantic-completeness", "У обязательства некорректный формат risk_flags", f"{obligation_id or f'строка {index}'} требует массив известных строковых risk_flags.", artifact, remediation_owner="scope-analyzer"))
        else:
            unknown_flags = sorted(set(risk_flags) - MATRIX_REVIEW_RISK_FLAGS)
            if unknown_flags:
                findings.append(finding("scope-obligation-risk-flags-unknown", "semantic-completeness", "У обязательства указан неизвестный риск matrix review", f"{obligation_id or f'строка {index}'}: " + ", ".join(unknown_flags) + ".", artifact, remediation_owner="scope-analyzer"))
        if re.search(r"\b(source-backed|residual|blocked-observability|fixture)\b", statement, flags=re.IGNORECASE):
            findings.append(finding("scope-obligation-process-language", "style", "В формулировке обязательства остался служебный английский текст", f"Проверьте statement для {obligation_id}.", artifact, remediation_owner="scope-analyzer", severity="warning"))
        if AUTOFILL_MULTI_TARGET_RE.search(statement):
            findings.append(finding(
                "scope-obligation-autofill-aggregated",
                "semantic-completeness",
                "Одно обязательство объединяет автозаполнение нескольких полей",
                f"{obligation_id}: разделите автозаполнение на отдельный OBL-* для каждого целевого поля.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
        if AUTOFILL_MANUAL_INPUT_RE.search(statement):
            findings.append(finding(
                "scope-obligation-autofill-manual-mixed",
                "semantic-completeness",
                "Одно обязательство смешивает автозаполнение и ручной ввод",
                f"{obligation_id}: создайте отдельные OBL-* для автозаполнения и ручного ввода/редактирования.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
    findings.extend(
        validate_scope_clarifications(
            payload=payload,
            obligations_path=obligations_path,
            package_root=package_root,
            obligation_ids=seen,
            obligation_ba_decisions=obligation_ba_decisions,
            approved_ba_decisions=approved_ba_decisions,
        )
    )
    return findings, payload


def matrix_header(path: Path) -> list[str] | None:
    """Read the sole human-readable matrix header without interpreting rows."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise PracticalV09Error(f"Cannot read matrix {path}: {exc}") from exc
    for raw_line in lines:
        line = raw_line.strip()
        if not line.startswith("|") or line.count("|") < 3:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if "Проверка" in cells and "Обязательство ФТ" in cells:
            return cells
    return None


def matrix_contract_version_from_path(path: Path) -> str | None:
    """Classify a matrix by its declared table schema, never by prose content."""
    header = matrix_header(path)
    if header is None:
        return None
    if all(column in header for column in MATRIX_REQUIRED_COLUMNS):
        return MATRIX_CONTRACT_VERSION
    if all(column in header for column in PREVIOUS_MATRIX_REQUIRED_COLUMNS):
        return PREVIOUS_MATRIX_CONTRACT_VERSION
    if all(column in header for column in LEGACY_MATRIX_REQUIRED_COLUMNS):
        return LEGACY_MATRIX_CONTRACT_VERSION
    return None


def parse_matrix_consolidation_decisions(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read current ``CON-*`` decisions from their immutable matrix section.

    The current matrix contract keeps the structured decision list directly
    beside the SCN rows it governs. This makes the matrix, rather than mutable
    workflow state, the single owner of test-design reasoning.
    """
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise PracticalV09Error(f"Cannot read matrix {path}: {exc}") from exc
    if MATRIX_CONSOLIDATION_SECTION_HEADING not in source:
        return [], [
            "в матрице отсутствует раздел «Решения о консолидации сценариев»"
        ]
    section = source.split(MATRIX_CONSOLIDATION_SECTION_HEADING, 1)[1]
    match = re.search(r"(?ms)^```json\s*\n(.*?)^```\s*$", section)
    if match is None:
        return [], [
            "в разделе решений о консолидации требуется один JSON-массив в блоке ```json"
        ]
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        return [], [f"JSON решений о консолидации не читается: {exc.msg}"]
    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        return [], ["JSON решений о консолидации должен быть массивом объектов CON-*"]
    return payload, []


def matrix_consolidation_enabled(
    *, state: Mapping[str, Any] | None, matrix_path: Path | None
) -> bool:
    """Return current matrix ownership or explicit compatibility with legacy state."""
    if matrix_path is not None and matrix_path.is_file():
        try:
            if MATRIX_CONSOLIDATION_SECTION_HEADING in matrix_path.read_text(encoding="utf-8"):
                return True
        except (OSError, UnicodeDecodeError):
            pass
    return state is not None and workflow_scenario_consolidation_enabled(state)


def parse_matrix_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise PracticalV09Error(f"Cannot read matrix {path}: {exc}") from exc
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    header: list[str] | None = None
    for raw_line in lines:
        line = raw_line.strip()
        if not line.startswith("|") or line.count("|") < 3:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells):
            continue
        if header is None and "Проверка" in cells and "Обязательство ФТ" in cells:
            header = cells
            missing = [column for column in MATRIX_REQUIRED_COLUMNS if column not in header]
            if missing:
                errors.append("в таблице матрицы отсутствуют колонки: " + ", ".join(f"«{column}»" for column in missing))
            continue
        if header is not None:
            if len(cells) != len(header):
                errors.append(f"строка матрицы имеет {len(cells)} ячеек вместо {len(header)}")
                continue
            rows.append(dict(zip(header, cells)))
    if header is None:
        errors.append("не найдена таблица с колонками «Проверка» и «Обязательство ФТ»")
    return rows, errors


def normalized_matrix_phrase(value: str) -> str:
    """Normalize human wording only for a conservative duplicate candidate key."""
    return " ".join(re.findall(r"[\w-]+", value.casefold()))


def normalized_field_label(value: str) -> str:
    """Normalize a UI-field label for a composite-result table comparison."""
    normalized = normalized_matrix_phrase(value)
    normalized = re.sub(r"^поле\s+", "", normalized)
    return normalized.strip(" «»\"'`.,:;")


def markdown_table_rows(value: str) -> list[list[list[str]]]:
    """Return simple Markdown tables, excluding separator rows."""
    tables: list[list[list[str]]] = []
    current: list[list[str]] = []
    for line in value.splitlines():
        if line.lstrip().startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                continue
            current.append(cells)
            continue
        if current:
            tables.append(current)
            current = []
    if current:
        tables.append(current)
    return tables


def has_composite_result_table(body: str, field_inventory: Iterable[str]) -> bool:
    """Check that one visible result table covers every fan-out field."""
    expected_fields = {normalized_field_label(field) for field in field_inventory}
    if not expected_fields:
        return False
    for table in markdown_table_rows(body):
        if len(table) < 2 or len(table[0]) < 2:
            continue
        header = [normalized_matrix_phrase(cell) for cell in table[0]]
        if not any("поле" in cell for cell in header):
            continue
        if not any("ожидаем" in cell or "значен" in cell or "результат" in cell for cell in header):
            continue
        listed_fields = {
            normalized_field_label(row[0])
            for row in table[1:]
            if row and row[0].strip()
        }
        if expected_fields <= listed_fields:
            return True
    return False


def matrix_exact_duplicate_signatures(
    row: Mapping[str, str],
) -> list[tuple[str, ...]]:
    """Return only exact duplicate matrix candidates.

    Natural-language similarity is not evidence that two source assertions
    are one test.  In particular, editability and manual input of the same
    field are independent properties.  Broader consolidation remains an
    explicit writer/reviewer decision in the matrix-owned ``CON-*`` section.
    """
    context_id = context_id_from_cell(row.get("Контекст исполнения", ""))
    required = (
        "Проверяемое правило",
        "Исходное состояние",
        "Формирование состояния",
        "Проверяемое действие",
        "Ожидаемый результат",
        "Нужные предпосылки",
        "Тип",
        "Статус исполнения",
    )
    if not context_id or any(not row.get(column, "").strip() for column in required):
        return []
    exact = (
        "exact",
        context_id,
        *(normalized_matrix_phrase(row[column]) for column in required),
    )
    return [exact]


def matrix_exact_duplicate_groups(
    rows: Iterable[dict[str, str]],
) -> list[tuple[tuple[str, ...], list[dict[str, str]]]]:
    """Group only exact duplicate rows from different source assertions."""
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = {}
    for row in rows:
        for signature in matrix_exact_duplicate_signatures(row):
            grouped.setdefault(signature, []).append(row)
    candidates: list[tuple[tuple[str, ...], list[dict[str, str]], frozenset[str]]] = []
    for signature, group in grouped.items():
        scenario_ids = frozenset(
            row.get("Идентификатор сценария", "")
            for row in group
            if SCENARIO_ID_RE.fullmatch(row.get("Идентификатор сценария", ""))
        )
        obligation_ids = {
            row.get("Обязательство ФТ", "")
            for row in group
            if re.fullmatch(r"OBL-[A-Z0-9-]+", row.get("Обязательство ФТ", ""))
        }
        if len(scenario_ids) < 2 or len(obligation_ids) < 2:
            continue
        candidates.append((signature, group, scenario_ids))
    result: list[tuple[tuple[str, ...], list[dict[str, str]]]] = []
    covered_scenarios: set[str] = set()
    for signature, group, scenario_ids in sorted(
        candidates, key=lambda item: (-len(item[2]), item[0])
    ):
        if covered_scenarios & scenario_ids:
            continue
        covered_scenarios.update(scenario_ids)
        result.append((signature, group))
    return result


def scenario_consolidation_contract(
    *,
    state: Mapping[str, Any] | None,
    rows_by_scenario: Mapping[str, dict[str, str]],
    artifact: str,
    matrix_path: Path | None = None,
) -> tuple[list[ScopeFinding], dict[str, Any]]:
    """Validate explicit, bounded decisions to merge or retain scenarios.

    The contract deliberately records decisions only for candidate groups. It
    does not create a second coverage artefact and never auto-merges prose
    that merely looks similar.
    """
    current_matrix = matrix_consolidation_enabled(state=None, matrix_path=matrix_path)
    enabled = current_matrix or (
        state is not None and workflow_scenario_consolidation_enabled(state)
    )
    result: dict[str, Any] = {
        "enabled": enabled,
        "decisions": [],
        "shared_scenarios_by_tc": {},
        "consolidation_by_tc": {},
        "covered_internal_scenarios": {},
    }
    if not enabled:
        return [], result

    findings: list[ScopeFinding] = []
    if current_matrix:
        raw_decisions, parsing_errors = parse_matrix_consolidation_decisions(matrix_path)
        for parsing_error in parsing_errors:
            findings.append(finding(
                "scenario-consolidation-matrix-section",
                "traceability",
                "Матрица не содержит читаемое решение о консолидации сценариев",
                parsing_error + ".",
                artifact,
                remediation_owner="writer",
                blocking=True,
            ))
        if parsing_errors:
            return findings, result
    else:
        raw_decisions = state.get("scenario_consolidation", []) if state is not None else []
    declared_versions = state.get("contract_versions") if state is not None else None
    declared_version = (
        declared_versions.get("scenario_consolidation")
        if isinstance(declared_versions, Mapping)
        else None
    )
    if not current_matrix and declared_version != SCENARIO_CONSOLIDATION_CONTRACT_VERSION:
        findings.append(finding(
            "scenario-consolidation-contract-migration-required",
            "transport",
            "Активный scope использует устаревший контракт консолидации сценариев",
            "Перед matrix review обновите matrix до practical-matrix-v3 и "
            "scenario_consolidation до scenario-consolidation-v2. Новый контракт "
            "требует совпадения элемента, домена проверки и способа взаимодействия "
            "для параметризованного объединения.",
            artifact,
            remediation_owner="controller",
            blocking=True,
            blocking_reason="scenario-consolidation-contract-migration-required",
        ))
        return findings, result
    seen_ids: set[str] = set()
    scenario_to_decision: dict[str, str] = {}
    allowed = {"merge-parameterized", "covered-by-observable-result", "separate"}
    for index, raw in enumerate(raw_decisions, start=1):
        label = f"scenario_consolidation[{index}]"
        if not isinstance(raw, dict):
            findings.append(finding(
                "scenario-consolidation-format",
                "traceability",
                "Решение о консолидации сценариев имеет неверный формат",
                f"{label} должен быть объектом.",
                artifact,
                remediation_owner="writer",
                blocking=True,
            ))
            continue
        decision_id = str(raw.get("id") or "")
        decision = str(raw.get("decision") or "")
        raw_scenarios = raw.get("scenario_ids")
        source_anchor = str(raw.get("source_anchor") or "").strip()
        rationale = str(raw.get("rationale") or "").strip()
        valid = True
        if not re.fullmatch(r"CON-[A-Z0-9-]+", decision_id) or decision_id in seen_ids:
            findings.append(finding(
                "scenario-consolidation-id",
                "traceability",
                "У решения о консолидации нет уникального идентификатора CON-*",
                f"{label}: id={decision_id!r}.",
                artifact,
                remediation_owner="writer",
                blocking=True,
            ))
            valid = False
        seen_ids.add(decision_id)
        if decision not in allowed:
            findings.append(finding(
                "scenario-consolidation-decision",
                "semantic-completeness",
                "У решения о консолидации указан неизвестный вид",
                f"{label}: допустимы merge-parameterized, covered-by-observable-result, separate.",
                artifact,
                remediation_owner="writer",
                blocking=True,
            ))
            valid = False
        scenario_ids = [item for item in raw_scenarios if isinstance(item, str)] if isinstance(raw_scenarios, list) else []
        if len(scenario_ids) < 2 or len(set(scenario_ids)) != len(scenario_ids) or not all(
            SCENARIO_ID_RE.fullmatch(item) for item in scenario_ids
        ):
            findings.append(finding(
                "scenario-consolidation-scenarios",
                "traceability",
                "Решение о консолидации должно содержать два и более разных SCN-*",
                f"{label}: scenario_ids={raw_scenarios!r}.",
                artifact,
                remediation_owner="writer",
                blocking=True,
            ))
            valid = False
        missing = [item for item in scenario_ids if item not in rows_by_scenario]
        if missing:
            findings.append(finding(
                "scenario-consolidation-scenario-unknown",
                "traceability",
                "Решение о консолидации ссылается на отсутствующий сценарий матрицы",
                f"{label}: не найдены {', '.join(missing)}.",
                artifact,
                remediation_owner="writer",
                blocking=True,
            ))
            valid = False
        if not source_anchor or not rationale:
            findings.append(finding(
                "scenario-consolidation-rationale",
                "semantic-completeness",
                "Решение о консолидации не обосновано источником",
                f"{label}: заполните source_anchor и русскоязычное rationale.",
                artifact,
                remediation_owner="writer",
            ))
            valid = False
        known_rows = [rows_by_scenario[item] for item in scenario_ids if item in rows_by_scenario]
        contexts = {
            context_id_from_cell(row.get("Контекст исполнения", ""))
            for row in known_rows
        }
        if known_rows and (len(contexts) != 1 or "" in contexts):
            findings.append(finding(
                "scenario-consolidation-context",
                "test-design",
                "Консолидируемые сценарии относятся к разным контекстам исполнения",
                f"{label}: объединять можно только сценарии одного CTX-*.",
                artifact,
                remediation_owner="writer",
            ))
            valid = False
        if decision == "merge-parameterized" and known_rows:
            parameterization_basis = str(raw.get("parameterization_basis") or "").strip()
            if parameterization_basis not in ALLOWED_PARAMETERIZATION_BASES:
                findings.append(finding(
                    "scenario-consolidation-parameterization-basis",
                    "test-design",
                    "Не указан допустимый тип параметризации сценариев",
                    f"{label}: parameterization_basis должен быть одним из: "
                    + ", ".join(sorted(ALLOWED_PARAMETERIZATION_BASES)) + ".",
                    artifact,
                    remediation_owner="writer",
                    blocking=True,
                ))
                valid = False
            if parameterization_basis == COMPOSITE_RESULT_PARAMETERIZATION_BASIS:
                field_inventory = raw.get("field_inventory")
                composite_result = str(raw.get("composite_result") or "").strip()
                expected_inventory = {
                    normalized_field_label(row.get("Проверяемый элемент", ""))
                    for row in known_rows
                }
                declared_inventory = (
                    {normalized_field_label(str(item)) for item in field_inventory}
                    if isinstance(field_inventory, list)
                    and all(isinstance(item, str) and item.strip() for item in field_inventory)
                    else set()
                )
                if not composite_result or not declared_inventory or declared_inventory != expected_inventory:
                    findings.append(finding(
                        "scenario-consolidation-composite-result-contract",
                        "test-design",
                        "Для объединения полей не зафиксирован полный составной результат",
                        f"{label}: укажите непустой composite_result и field_inventory, "
                        "точно совпадающий с «Проверяемым элементом» всех связанных SCN-*.",
                        artifact,
                        remediation_owner="writer",
                        blocking=True,
                    ))
                    valid = False
                required_columns = COMPOSITE_RESULT_SHARED_COLUMNS
            else:
                required_columns = (
                    "Проверяемый элемент",
                    "Домен проверки",
                    "Способ взаимодействия",
                    "Тип",
                    "Статус исполнения",
                )
            for column in required_columns:
                finding_id = {
                    "Проверяемый элемент": "scenario-consolidation-element",
                    "Домен проверки": "scenario-consolidation-domain",
                    "Способ взаимодействия": "scenario-consolidation-interaction",
                    "Тип": "scenario-consolidation-type",
                    "Статус исполнения": "scenario-consolidation-status",
                }.get(column, "scenario-consolidation-composite-mismatch")
                title = {
                    "Проверяемый элемент": "Параметризованное объединение смешивает разные проверяемые элементы",
                    "Домен проверки": "Параметризованное объединение смешивает разные домены проверки",
                    "Способ взаимодействия": "Параметризованное объединение смешивает разные способы взаимодействия",
                    "Тип": "Параметризованное объединение смешивает позитивную и негативную проверку",
                    "Статус исполнения": "Параметризованное объединение смешивает разные статусы исполнения",
                }.get(column, "Параметризованное объединение не описывает один общий составной результат")
                values = {row.get(column, "").strip() for row in known_rows}
                if len(values) != 1 or "" in values:
                    findings.append(finding(
                        finding_id,
                        "test-design",
                        title,
                        f"{label}: для merge-parameterized все SCN-* должны иметь "
                        f"одно значение в колонке «{column}»; получено: "
                        + ", ".join(sorted(value or "<пусто>" for value in values)) + ".",
                        artifact,
                        remediation_owner="writer",
                        blocking=True,
                    ))
                    valid = False
        overlap = [item for item in scenario_ids if item in scenario_to_decision]
        if overlap:
            findings.append(finding(
                "scenario-consolidation-overlap",
                "traceability",
                "Сценарий включён в несколько решений о консолидации",
                f"{label}: {', '.join(overlap)} уже относится к {scenario_to_decision[overlap[0]]}.",
                artifact,
                remediation_owner="writer",
            ))
            valid = False
        for item in scenario_ids:
            scenario_to_decision[item] = decision_id

        planned_tc_id = str(raw.get("planned_tc_id") or "")
        observable_scenario_id = str(raw.get("observable_scenario_id") or "")
        if decision in {"merge-parameterized", "covered-by-observable-result"}:
            if not re.fullmatch(r"TC-[A-Z0-9-]+", planned_tc_id):
                findings.append(finding(
                    "scenario-consolidation-planned-tc",
                    "traceability",
                    "Для объединения сценариев не указан общий planned TC-ID",
                    f"{label}: planned_tc_id должен иметь вид TC-*.",
                    artifact,
                    remediation_owner="writer",
                ))
                valid = False
            matrix_tc_ids = {row.get("Планируемый TC-ID", "") for row in known_rows}
            if planned_tc_id and matrix_tc_ids != {planned_tc_id}:
                findings.append(finding(
                    "scenario-consolidation-plan-mismatch",
                    "traceability",
                    "Общий planned TC-ID не совпадает со строками матрицы",
                    f"{label}: в решении {planned_tc_id}, в matrix {', '.join(sorted(matrix_tc_ids))}.",
                    artifact,
                    remediation_owner="writer",
                ))
                valid = False
        if decision == "covered-by-observable-result":
            if observable_scenario_id not in scenario_ids:
                findings.append(finding(
                    "scenario-consolidation-observable-scenario",
                    "semantic-completeness",
                    "Для ненаблюдаемого внутреннего действия не указан сценарий наблюдаемого результата",
                    f"{label}: observable_scenario_id должен входить в scenario_ids.",
                    artifact,
                    remediation_owner="writer",
                ))
                valid = False
        if decision == "separate":
            matrix_tc_ids = {row.get("Планируемый TC-ID", "") for row in known_rows}
            if len(matrix_tc_ids) != len(known_rows):
                findings.append(finding(
                    "scenario-consolidation-separate-plan",
                    "test-design",
                    "Решение оставить сценарии раздельными противоречит общему planned TC-ID",
                    f"{label}: у всех связанных строк должны быть разные planned TC-ID.",
                    artifact,
                    remediation_owner="writer",
                ))
                valid = False
        if not valid:
            continue
        normalized = {
            "id": decision_id,
            "decision": decision,
            "scenario_ids": tuple(scenario_ids),
            "planned_tc_id": planned_tc_id,
            "observable_scenario_id": observable_scenario_id,
            "parameterization_basis": str(raw.get("parameterization_basis") or "").strip(),
            "field_inventory": tuple(
                str(item) for item in raw.get("field_inventory", []) if isinstance(item, str)
            ),
            "composite_result": str(raw.get("composite_result") or "").strip(),
        }
        result["decisions"].append(normalized)
        if decision in {"merge-parameterized", "covered-by-observable-result"}:
            result["shared_scenarios_by_tc"][planned_tc_id] = frozenset(scenario_ids)
            result["consolidation_by_tc"][planned_tc_id] = normalized
        if decision == "covered-by-observable-result":
            for scenario_id in scenario_ids:
                result["covered_internal_scenarios"][scenario_id] = normalized

    shared_by_matrix_tc: dict[str, set[str]] = {}
    for scenario_id, row in rows_by_scenario.items():
        planned_tc_id = row.get("Планируемый TC-ID", "").strip()
        if re.fullmatch(r"TC-[A-Z0-9-]+", planned_tc_id):
            shared_by_matrix_tc.setdefault(planned_tc_id, set()).add(scenario_id)
    for planned_tc_id, scenario_ids in sorted(shared_by_matrix_tc.items()):
        if len(scenario_ids) < 2:
            continue
        authorized = result["shared_scenarios_by_tc"].get(planned_tc_id)
        if authorized != frozenset(scenario_ids):
            findings.append(finding(
                "scenario-consolidation-shared-tc-without-decision",
                "test-design",
                "Несколько сценариев назначены одному TC без подтверждённого решения о консолидации",
                f"{planned_tc_id}: {', '.join(sorted(scenario_ids))}. Добавьте одно решение CON-* в разделе консолидации matrix с общим source_anchor и rationale либо разнесите planned TC-ID.",
                artifact,
                remediation_owner="writer",
                blocking=True,
            ))
    return findings, result


def required_message_literals(statement: str) -> list[str]:
    """Return source-prescribed message text, not ordinary quoted labels.

    A literal is mandatory only when the source frames it as a visible message,
    text, notification or error.  Quoted field names, dictionary values and
    button labels must not become an accidental exact-text oracle.
    """
    literals: list[str] = []
    for match in re.finditer(r"«([^»\n]{4,})»", statement):
        prefix = statement[max(0, match.start() - 180) : match.start()]
        literal = match.group(1).strip()
        if literal and SOURCE_MESSAGE_CUE_RE.search(prefix):
            literals.append(literal)
    return list(dict.fromkeys(literals))


def common_result_literals_by_obligation(
    obligations: Mapping[str, Any],
) -> dict[str, set[str]]:
    """Map each invalid-input OBL to source-prescribed common result text.

    The source analyzer declares this relationship explicitly on the OBL that
    owns the common result.  It is intentionally not guessed from similar
    prose: a validator may enforce only a source-backed grouping.
    """
    result: dict[str, set[str]] = {}
    for obligation in active_obligations(dict(obligations)):
        target_ids = obligation.get("common_result_for_obligation_ids")
        if not isinstance(target_ids, list):
            continue
        literals = required_message_literals(str(obligation.get("statement") or ""))
        for target_id in target_ids:
            if isinstance(target_id, str):
                result.setdefault(target_id, set()).update(literals)
    return result


def is_internal_unobservable_statement(statement: str) -> bool:
    """Identify a source assertion that describes only an internal check.

    This deliberately remains narrow: visible result words exempt the
    statement, because their observability must be designed rather than
    presumed absent.
    """
    text = statement.casefold()
    internal_check = re.search(r"\bсистем\w*\s+провер\w*\b", text)
    if internal_check is None:
        return False
    # An action before the assertion (for example, «При нажатии Сохранить»)
    # is not an observable result.  Only a result described after the internal
    # check can make the source assertion executable.
    result_clause = text[internal_check.end() :]
    return not re.search(
        r"\b(?:сообщени|текст|ошибк|отображ|показыв|доступ|сохран|закры|откры|переход)\w*\b",
        result_clause,
    )


def has_internal_unobservability_justification(expected_result: str) -> bool:
    """Compatibility check for pre-consolidation scopes only."""
    return bool(INTERNAL_UNOBSERVABILITY_JUSTIFICATION_RE.search(expected_result))


def validate_matrix(
    matrix_path: Path,
    package_root: Path,
    obligations: dict[str, Any],
    workflow_state: Mapping[str, Any] | None = None,
) -> tuple[
    list[ScopeFinding],
    dict[str, dict[str, str]],
    dict[tuple[str, str], list[dict[str, str]]],
]:
    artifact = relative_to_package(package_root, matrix_path)
    findings: list[ScopeFinding] = []
    try:
        rows, errors = parse_matrix_rows(matrix_path)
    except PracticalV09Error as exc:
        return [finding("matrix-unreadable", "source-integrity", "Недоступна матрица тест-дизайна", str(exc), artifact, remediation_owner="writer")], {}, {}
    for error in errors:
        findings.append(finding("matrix-format", "format", "Матрица тест-дизайна не соответствует компактному шаблону", error, artifact, remediation_owner="writer", severity="warning"))
    by_obligation_context: dict[tuple[str, str], list[dict[str, str]]] = {}
    by_scenario: dict[str, dict[str, str]] = {}
    seen_matrix_ids: set[str] = set()
    active_ids = active_obligation_ids(obligations)
    active_entries = {str(item.get("id")): item for item in active_obligations(obligations)}
    setup_catalog = execution_setups(obligations)
    shared_result_literals = common_result_literals_by_obligation(obligations)
    consolidation_enabled = matrix_consolidation_enabled(
        state=workflow_state, matrix_path=matrix_path
    )
    all_ids = {
        str(item.get("id"))
        for item in obligations.get("obligations", [])
        if isinstance(item, dict)
    }
    for row in rows:
        matrix_id = row.get("Проверка", "")
        scenario_id = row.get("Идентификатор сценария", "")
        obligation_id = row.get("Обязательство ФТ", "")
        context_id = context_id_from_cell(row.get("Контекст исполнения", ""))
        tc_id = row.get("Планируемый TC-ID", "")
        if not re.fullmatch(r"MTX-[A-Z0-9-]+", matrix_id):
            findings.append(finding("matrix-id", "traceability", "У строки матрицы некорректный идентификатор", f"Проверка={matrix_id!r}; ожидается MTX-*.", artifact, remediation_owner="writer"))
        elif matrix_id in seen_matrix_ids:
            findings.append(finding("matrix-duplicate-id", "traceability", "В матрице повторяется идентификатор проверки", f"Повторяется {matrix_id}.", artifact, remediation_owner="writer"))
        seen_matrix_ids.add(matrix_id)
        if not SCENARIO_ID_RE.fullmatch(scenario_id):
            findings.append(finding(
                "matrix-scenario-id",
                "traceability",
                "У строки матрицы нет идентификатора атомарного сценария",
                f"Проверка {matrix_id or '<без ID>'}: «Идентификатор сценария» должен содержать SCN-*.",
                artifact,
                remediation_owner="writer",
            ))
        elif scenario_id in by_scenario:
            findings.append(finding(
                "matrix-scenario-duplicate",
                "traceability",
                "Идентификатор сценария повторяется в матрице",
                f"Повторяется {scenario_id}.",
                artifact,
                remediation_owner="writer",
            ))
        else:
            by_scenario[scenario_id] = row
        if not re.fullmatch(r"TC-[A-Z0-9-]+", tc_id):
            findings.append(finding("matrix-tc-id", "traceability", "У строки матрицы нет планируемого TC-ID", f"Проверка {matrix_id or '<без ID>'} должна иметь TC-*.", artifact, remediation_owner="writer"))
        if not re.fullmatch(r"OBL-[A-Z0-9-]+", obligation_id):
            findings.append(finding("matrix-obligation-id", "traceability", "У строки матрицы нет одного обязательства ФТ", f"Проверка {matrix_id or '<без ID>'} должна ссылаться ровно на один OBL-*.", artifact, remediation_owner="writer"))
        else:
            if not context_id:
                findings.append(finding(
                    "matrix-execution-context",
                    "execution-readiness",
                    "В строке матрицы нет одного контекста исполнения",
                    f"Проверка {matrix_id or '<без ID>'}: «Контекст исполнения» должен содержать ровно один CTX-*.",
                    artifact,
                    remediation_owner="writer",
                ))
            else:
                by_obligation_context.setdefault((obligation_id, context_id), []).append(row)
            if obligation_id in all_ids and obligation_id not in active_ids:
                findings.append(finding(
                    "matrix-obligation-superseded",
                    "traceability",
                    "Матрица включает обязательство, отменённое утверждённым решением БА",
                    f"Проверка {matrix_id or '<без ID>'} не должна ссылаться на {obligation_id}.",
                    artifact,
                    remediation_owner="writer",
                ))
        for required_column in (
            "Проверяемый элемент",
            "Домен проверки",
            "Способ взаимодействия",
            "Проверяемое правило",
            "Исходное состояние",
            "Формирование состояния",
            "Проверяемое действие",
            "Ожидаемый результат",
            "Нужные предпосылки",
            "Тип",
            "Приоритет",
            "Статус исполнения",
        ):
            if not row.get(required_column, "").strip():
                findings.append(finding("matrix-required-cell", "semantic-completeness", "В строке матрицы не заполнено обязательное поле", f"Проверка {matrix_id or '<без ID>'}: отсутствует «{required_column}».", artifact, remediation_owner="writer"))
        for column in ("Исходное состояние", "Формирование состояния", "Проверяемое действие"):
            value = row.get(column, "")
            if any(pattern.search(value) for pattern in MATRIX_META_STATE_PATTERNS):
                findings.append(finding(
                    "matrix-meta-state-description",
                    "execution-readiness",
                    "Матрица содержит служебное описание состояния вместо исполнимого действия или данных",
                    f"Проверка {matrix_id or '<без ID>'}: в колонке «{column}» укажите конкретное действие пользователя, поле и значение либо точный fixture и способ подготовки.",
                    artifact,
                    remediation_owner="writer",
                ))
            if CONTEXT_LABEL_AS_ACTION_RE.search(value):
                findings.append(finding(
                    "matrix-context-label-as-action",
                    "execution-readiness",
                    "Матрица подменяет действие пользователя названием контекста",
                    f"Проверка {matrix_id or '<без ID>'}: в колонке «{column}» "
                    "укажите конкретный вход на экран или перенесите уже открытый "
                    "экран в предусловие; CTX-* служит только для трассировки потока.",
                    artifact,
                    remediation_owner="writer",
                ))
        execution_status = row.get("Статус исполнения", "").strip()
        if execution_status and execution_status not in ALLOWED_EXECUTION_STATUSES:
            findings.append(finding(
                "matrix-execution-status",
                "semantic-completeness",
                "В матрице указан неизвестный статус исполнения",
                f"Проверка {matrix_id or '<без ID>'}: «{execution_status}» не входит в допустимый перечень.",
                artifact,
                remediation_owner="writer",
            ))
        obligation = active_entries.get(obligation_id)
        if obligation is not None and context_id:
            row_visible_text = normalized_matrix_phrase(matrix_row_text(row))
            for source_label, ui_label in visual_label_mappings(obligation, context_id):
                if normalized_matrix_phrase(ui_label) not in row_visible_text:
                    findings.append(finding(
                        "matrix-visual-label-binding",
                        "semantic-completeness",
                        "Матрица не использует подтверждённую подпись UI",
                        f"Проверка {matrix_id or '<без ID>'}: для термина ФТ «{source_label}» "
                        f"в visual_binding зафиксирована подпись UI «{ui_label}». Укажите её в "
                        "проверяемом элементе, действии, правиле или ожидаемом результате; термин ФТ "
                        "сохраняйте в трассировке и формулировке требования.",
                        artifact,
                        remediation_owner="writer",
                    ))
            contexts = {
                str(item.get("id")): item
                for item in execution_contexts(obligation)
            }
            context = contexts.get(context_id)
            if context is None:
                findings.append(finding(
                    "matrix-execution-context-unknown",
                    "traceability",
                    "Матрица ссылается на неописанный контекст исполнения",
                    f"Проверка {matrix_id or '<без ID>'}: {context_id} не принадлежит {obligation_id}.",
                    artifact,
                    remediation_owner="writer",
                ))
            required_literals = list(dict.fromkeys(
                [
                    *required_message_literals(str(obligation.get("statement") or "")),
                    *sorted(shared_result_literals.get(obligation_id, set())),
                ]
            ))
            expected_result = row.get("Ожидаемый результат", "")
            for literal in required_literals:
                if literal not in expected_result:
                    findings.append(finding(
                        "matrix-source-message-literal",
                        "semantic-completeness",
                        "Матрица потеряла дословное сообщение из ФТ",
                        f"Проверка {matrix_id or '<без ID>'}: ожидаемый результат должен содержать «{literal}».",
                        artifact,
                        remediation_owner="writer",
                    ))
            source_requires_blocked_observability = is_internal_unobservable_statement(
                str(obligation.get("statement") or "")
            )
            if source_requires_blocked_observability and not consolidation_enabled:
                if execution_status != "blocked-observability":
                    findings.append(finding(
                        "matrix-internal-oracle-status",
                        "execution-readiness",
                        "Ненаблюдаемое внутреннее действие не помечено как blocked-observability",
                        f"Проверка {matrix_id or '<без ID>'}: для внутреннего действия без source-backed oracle требуется blocked-observability.",
                        artifact,
                        remediation_owner="writer",
                    ))
                elif not has_internal_unobservability_justification(expected_result):
                    findings.append(finding(
                        "matrix-internal-oracle-justification",
                        "execution-readiness",
                        "Ненаблюдаемость внутреннего действия не обоснована в матрице",
                        f"Проверка {matrix_id or '<без ID>'}: ожидаемый результат должен явно объяснять, что источник не задаёт наблюдаемый признак или результат.",
                        artifact,
                        remediation_owner="writer",
                    ))
            if context is not None:
                expected_status = (
                    "blocked-observability"
                    if source_requires_blocked_observability and not consolidation_enabled
                    else derived_execution_status(context, setup_catalog)
                )
                if execution_status and execution_status != expected_status:
                    findings.append(finding(
                        "matrix-execution-status-prerequisites",
                        "execution-readiness",
                        "Статус исполнения не соответствует полной цепочке предпосылок",
                        f"Проверка {matrix_id or '<без ID>'}: указан {execution_status}, ожидается {expected_status} по {context_id}.",
                        artifact,
                        remediation_owner="writer",
                    ))
                prerequisite_cell = row.get("Нужные предпосылки", "")
                missing_setup_ids = [
                    setup_id for setup_id in context.get("setup_ids", [])
                    if setup_id not in prerequisite_cell
                ]
                if missing_setup_ids:
                    findings.append(finding(
                        "matrix-execution-prerequisites-incomplete",
                        "execution-readiness",
                        "Матрица не показывает все необходимые предпосылки",
                        f"Проверка {matrix_id or '<без ID>'}: «Нужные предпосылки» не содержит " + ", ".join(missing_setup_ids) + ".",
                        artifact,
                        remediation_owner="writer",
                    ))
                secondary_limitations = secondary_execution_limitations(
                    context, setup_catalog
                )
                if secondary_limitations:
                    limitation_cell = row.get("Ограничения исполнения", "").strip()
                    missing_limitations = [
                        setup_id
                        for setup_id, _availability in secondary_limitations
                        if setup_id not in limitation_cell
                    ]
                    if not limitation_cell or missing_limitations or not has_russian_prose(limitation_cell):
                        details = (
                            f"Проверка {matrix_id or '<без ID>'}: добавьте отдельную колонку «Ограничения исполнения» "
                            "с русским пояснением и ссылками на "
                            + ", ".join(setup_id for setup_id, _ in secondary_limitations)
                            + ". Первичный статус исполнения не меняйте."
                        )
                        findings.append(finding(
                            "matrix-execution-limitations-incomplete",
                            "execution-readiness",
                            "Матрица потеряла существенное вторичное ограничение исполнения",
                            details,
                            artifact,
                            remediation_owner="writer",
                        ))
    consolidation_findings, consolidation = scenario_consolidation_contract(
        state=workflow_state,
        rows_by_scenario=by_scenario,
        artifact=artifact,
        matrix_path=matrix_path,
    )
    findings.extend(consolidation_findings)
    if consolidation["enabled"]:
        declared_groups = {
            frozenset(decision["scenario_ids"])
            for decision in consolidation["decisions"]
        }
        for _signature, group in matrix_exact_duplicate_groups(rows):
            scenario_ids = frozenset(
                row.get("Идентификатор сценария", "") for row in group
            )
            if scenario_ids not in declared_groups:
                findings.append(finding(
                    "scenario-consolidation-exact-candidate-undecided",
                    "test-design",
                    "Для точного кандидата на дублирование не принято решение о консолидации",
                    "Сценарии " + ", ".join(sorted(scenario_ids))
                    + " имеют один контекст, действие и результат. В разделе решений о "
                    "консолидации matrix зафиксируйте merge-parameterized или separate "
                    "с source_anchor и rationale.",
                    artifact,
                    remediation_owner="writer",
                    blocking=True,
                ))
        for scenario_id, row in by_scenario.items():
            obligation = active_entries.get(row.get("Обязательство ФТ", ""))
            if obligation is None or not is_internal_unobservable_statement(
                str(obligation.get("statement") or "")
            ):
                continue
            decision = consolidation["covered_internal_scenarios"].get(scenario_id)
            if decision is None or decision.get("decision") != "covered-by-observable-result":
                findings.append(finding(
                    "matrix-internal-oracle-needs-observable-coverage",
                    "test-design",
                    "Внутреннее действие ФТ без наблюдаемого oracle запланировано как самостоятельная проверка",
                    f"{scenario_id}: свяжите его с наблюдаемым результатом отдельным решением CON-* "
                    "или зафиксируйте source contradiction; standalone TC не создавайте.",
                    artifact,
                    remediation_owner="writer",
                    blocking=True,
                ))
                continue
            observable_scenario_id = str(decision.get("observable_scenario_id") or "")
            observable_row = by_scenario.get(observable_scenario_id)
            observable_obligation = active_entries.get(
                observable_row.get("Обязательство ФТ", "") if observable_row else ""
            )
            if observable_row is None or observable_obligation is None or is_internal_unobservable_statement(
                str(observable_obligation.get("statement") or "")
            ):
                findings.append(finding(
                    "matrix-internal-oracle-observable-target",
                    "test-design",
                    "Для внутреннего действия не указан самостоятельный наблюдаемый результат",
                    f"{scenario_id}: observable_scenario_id={observable_scenario_id or '<пусто>'} должен ссылаться на SCN с source-backed результатом.",
                    artifact,
                    remediation_owner="writer",
                    blocking=True,
                ))
    else:
        # New v0.9 scopes do not keep decisions in workflow-state.  If their
        # matrix has an exact duplicate, the writer must add a matrix-owned
        # CON-* section instead of relying on the old warning-only detector.
        is_current_scope = (
            workflow_state is not None
            and workflow_matrix_contract_version(workflow_state)
            == MATRIX_CONTRACT_VERSION
        )
        for group_index, (_signature, group) in enumerate(
            matrix_exact_duplicate_groups(rows), start=1
        ):
            group_key = f"exact-duplicate-{group_index}"
            for row in group:
                row["_shared_test_case_group"] = group_key
            planned_tc_ids = {row.get("Планируемый TC-ID", "").strip() for row in group}
            if is_current_scope:
                matrix_ids = ", ".join(row.get("Проверка", "<без ID>") for row in group)
                scenario_ids = ", ".join(row.get("Идентификатор сценария", "<без SCN>") for row in group)
                findings.append(finding(
                    "matrix-exact-duplicate-consolidation-missing",
                    "test-design",
                    "Для точного кандидата на дублирование не принято решение в матрице",
                    f"{matrix_ids}: совпадают контекст, действие и основной результат ({scenario_ids}). "
                    "Добавьте раздел «Решения о консолидации сценариев» с решением CON-* "
                    "либо разнесите сценарии по действительно разным проверкам.",
                    artifact,
                    remediation_owner="writer",
                    blocking=True,
                    evidence=["duplicate_group=" + group_key],
                ))
            elif len(planned_tc_ids) != 1:
                matrix_ids = ", ".join(row.get("Проверка", "<без ID>") for row in group)
                scenario_ids = ", ".join(row.get("Идентификатор сценария", "<без SCN>") for row in group)
                findings.append(finding(
                    "matrix-probable-semantic-duplicate",
                    "test-design",
                    "Строки матрицы вероятно дублируют одну исполнимую проверку",
                    f"{matrix_ids}: совпадают контекст, действие и основной результат ({scenario_ids}). "
                    "Независимый reviewer должен подтвердить раздельность или назначить общий planned TC-ID.",
                    artifact,
                    remediation_owner="reviewer",
                    severity="warning",
                    evidence=["duplicate_group=" + group_key],
                ))
    expected_pairs = {
        (str(obligation.get("id")), str(context.get("id")))
        for obligation in active_entries.values()
        for context in execution_contexts(obligation)
        if EXECUTION_CONTEXT_ID_RE.fullmatch(str(context.get("id") or ""))
    }
    for obligation_id, context_id in sorted(expected_pairs):
        mapped = by_obligation_context.get((obligation_id, context_id), [])
        if not mapped:
            findings.append(finding(
                "matrix-obligation-context-unmapped",
                "semantic-completeness",
                "Контекст обязательства ФТ не покрыт матрицей",
                f"Для {obligation_id} в контексте {context_id} нет строки матрицы.",
                artifact,
                remediation_owner="writer",
            ))
    return findings, by_scenario, {
        key: value
        for key, value in by_obligation_context.items()
        if key in expected_pairs
    }


def parse_test_case_blocks(path: Path) -> list[dict[str, str]]:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise PracticalV09Error(f"Cannot read test cases {path}: {exc}") from exc
    headings = list(re.finditer(r"(?m)^#{2,3}\s+(TC-[A-Z0-9-]+)\b.*$", content))
    blocks: list[dict[str, str]] = []
    for position, heading in enumerate(headings):
        end = headings[position + 1].start() if position + 1 < len(headings) else len(content)
        blocks.append({"id": heading.group(1), "body": content[heading.start() : end]})
    return blocks


def test_case_field(body: str, field: str) -> str:
    """Return a Markdown TC field value, including a multi-line value."""
    match = re.search(
        rf"(?ms)^\*\*{re.escape(field)}:\*\*\s*(.*?)(?=^\*\*[^\n]+:\*\*|\Z)",
        body,
    )
    return match.group(1).strip() if match else ""


def backtick_literals(value: str) -> set[str]:
    """Return explicitly marked literals for advisory test-data review.

    The helper deliberately does not infer that equivalent scenarios need
    distinct real-world values. It only detects likely copied profile fields.
    """
    return {
        literal.strip()
        for literal in re.findall(r"`([^`]+)`", value)
        if len(literal.strip()) >= 2
    }


def has_test_data_completion_action(steps: str) -> bool:
    """Whether the TC can need a full profile to complete a save flow."""
    return bool(re.search(
        r"\b(?:заполн\w*\s+(?:остальн\w*|все|обязательн\w*)|сохран\w*)\b",
        steps,
        re.IGNORECASE,
    ))


def numbered_steps(value: str) -> list[str]:
    return [
        match.group(1).strip()
        for match in re.finditer(r"(?m)^\s*\d+\.\s+(.+?)\s*$", value)
    ]


def opens_new_card(step: str) -> bool:
    """Detect the narrow, unambiguous create-flow phrase inside an edit TC.

    This is intentionally not a general natural-language classifier.  It only
    blocks an explicit instruction to open/create a *new* or empty card, which
    cannot exercise a matrix row whose declared context is editing an existing
    object.  Any less explicit navigation remains reviewer territory.
    """
    return bool(re.search(
        r"\b(?:открыть|создать|добавить)\w*\b[^.\n]{0,100}"
        r"\b(?:нов\w*|пуст\w*)\b[^.\n]{0,100}\bкарточк\w*\b",
        step,
        re.IGNORECASE,
    ))


def matrix_field_labels(value: str) -> set[str]:
    """Return explicit UI labels from a matrix element cell.

    Only quoted labels are suitable for an automatic TC binding gate.  Generic
    elements such as ``Карточка партнёра`` deliberately remain a reviewer
    concern, while ``Поле «Дата аккредитации»`` has a stable literal that must
    be preserved by writer templates and revisions.
    """
    return {
        normalized_matrix_phrase(label)
        for label in re.findall(r"[«\"]([^»\"]+)[»\"]", value)
        if normalized_matrix_phrase(label)
    }


def visual_label_mappings(
    obligation: Mapping[str, Any] | None,
    context_id: str | None = None,
) -> list[tuple[str, str]]:
    """Return declared FT-term to visible-UI-label mappings for an obligation.

    The validator never guesses that two similar labels identify the same
    control.  A mapping exists only when the scope analyst explicitly records
    a visual binding and says that its source term and UI label differ.
    """
    binding = (obligation or {}).get("visual_binding")
    if not isinstance(binding, Mapping):
        return []
    mappings = binding.get("label_mappings")
    if not isinstance(mappings, list):
        return []
    result: list[tuple[str, str]] = []
    for item in mappings:
        if not isinstance(item, Mapping):
            continue
        context_ids = item.get("context_ids")
        if (
            context_id is not None
            and isinstance(context_ids, list)
            and context_id not in context_ids
        ):
            continue
        source_label = str(item.get("source_label") or "").strip()
        ui_label = str(item.get("ui_label") or "").strip()
        if source_label and ui_label:
            result.append((source_label, ui_label))
    return result


def validate_visual_label_mappings(
    *,
    obligation_id: str,
    obligation: Mapping[str, Any],
    artifact: str,
) -> list[ScopeFinding]:
    """Validate explicit FT-term to UI-label mappings without guessing them."""
    binding = obligation.get("visual_binding")
    if not isinstance(binding, Mapping):
        return []
    mappings = binding.get("label_mappings")
    if mappings is None:
        return []
    if not isinstance(mappings, list) or not mappings:
        return [finding(
            "scope-obligation-visual-label-mappings-format",
            "semantic-completeness",
            "Сопоставление терминов ФТ и подписей UI имеет неверный формат",
            f"{obligation_id}: visual_binding.label_mappings должен быть непустым списком объектов source_label/ui_label.",
            artifact,
            remediation_owner="scope-analyzer",
        )]
    known_context_ids = {
        str(context.get("id") or "")
        for context in execution_contexts(obligation)
        if isinstance(context, Mapping)
    }
    seen: set[tuple[str, str]] = set()
    findings: list[ScopeFinding] = []
    for mapping_index, item in enumerate(mappings, start=1):
        if not isinstance(item, Mapping):
            findings.append(finding(
                "scope-obligation-visual-label-mapping-format",
                "semantic-completeness",
                "Строка сопоставления терминов ФТ и подписей UI имеет неверный формат",
                f"{obligation_id}: label_mappings[{mapping_index}] должен быть объектом source_label/ui_label.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
            continue
        source_label = str(item.get("source_label") or "").strip()
        ui_label = str(item.get("ui_label") or "").strip()
        if not source_label or not ui_label:
            findings.append(finding(
                "scope-obligation-visual-label-mapping-incomplete",
                "semantic-completeness",
                "Сопоставление терминов ФТ и подписей UI неполно",
                f"{obligation_id}: label_mappings[{mapping_index}] требует source_label и ui_label.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
            continue
        mapping = (
            normalized_matrix_phrase(source_label),
            normalized_matrix_phrase(ui_label),
        )
        if mapping[0] == mapping[1]:
            findings.append(finding(
                "scope-obligation-visual-label-mapping-same",
                "semantic-completeness",
                "Сопоставление терминов ФТ и подписей UI не описывает различие",
                f"{obligation_id}: source_label и ui_label в label_mappings[{mapping_index}] совпадают; сопоставление нужно только для различающихся подписей.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
        if mapping in seen:
            findings.append(finding(
                "scope-obligation-visual-label-mapping-duplicate",
                "semantic-completeness",
                "Сопоставление терминов ФТ и подписей UI повторяется",
                f"{obligation_id}: повторяется label_mappings[{mapping_index}].",
                artifact,
                remediation_owner="scope-analyzer",
            ))
        seen.add(mapping)
        context_ids = item.get("context_ids")
        if context_ids is not None and (
            not isinstance(context_ids, list)
            or not context_ids
            or not all(
                isinstance(value, str) and value in known_context_ids
                for value in context_ids
            )
        ):
            findings.append(finding(
                "scope-obligation-visual-label-mapping-contexts",
                "semantic-completeness",
                "Сопоставление подписей UI ссылается на неизвестный контекст",
                f"{obligation_id}: context_ids в label_mappings[{mapping_index}] должен содержать один или несколько CTX-* этого обязательства.",
                artifact,
                remediation_owner="scope-analyzer",
            ))
    return findings


def matrix_row_text(row: Mapping[str, str]) -> str:
    """Return the visible design fields of one matrix row as normalized text."""
    return " ".join(
        str(row.get(column) or "")
        for column in (
            "Проверяемый элемент",
            "Проверяемое правило",
            "Проверяемое действие",
            "Ожидаемый результат",
        )
    )


def tc_explicit_ui_labels(body: str) -> set[str]:
    """Return only literal field/control labels that the TC declares explicitly."""
    return {
        normalized_matrix_phrase(label)
        for label in re.findall(r"[«\"]([^»\"]+)[»\"]", body)
        if normalized_matrix_phrase(label)
    }


def conflicts_with_matrix_field(*, expected_label: str, declared_labels: set[str]) -> bool:
    """Detect a declared replacement of a matrix field, not mere omission.

    An executable TC may legitimately refer to a field through its purpose or
    an upload action without restating a long label. A static gate may not
    invent that label. It can, however, reject an explicit *different* field
    from the same field family, such as ``Дата начала сотрудничества`` instead
    of matrix field ``Дата аккредитации``.
    """
    expected = expected_label.replace("ё", "е")
    actual = {label.replace("ё", "е") for label in declared_labels}
    if expected in actual:
        return False
    expected_words = expected.split()
    if not expected_words:
        return False
    primary_word = expected_words[0]
    return any(label.split()[:1] == [primary_word] for label in actual)


def attachment_identity(step: str) -> str | None:
    """Return a stable attached-file identity when the step declares one."""
    quoted = re.findall(r"`([^`]+)`", step)
    if quoted:
        return quoted[-1].casefold()
    numbered = re.search(r"\b(\d+)\s*(?:-?й|[- ]?й)?\s+файл", step, re.IGNORECASE)
    if numbered:
        return numbered.group(1)
    if re.search(r"\bперв\w*\s+файл", step, re.IGNORECASE):
        return "first"
    if re.search(r"\bвтор\w*\s+файл", step, re.IGNORECASE):
        return "second"
    return None


def has_complete_single_file_trigger(steps: list[str]) -> bool:
    """Check the minimal observable setup for a one-file upload limit.

    The check is intentionally narrow.  It applies only when a TC explicitly
    talks about a second file or a one-file limit, and requires separate file
    actions before and during the attempted overflow.
    """
    file_actions = [
        step for step in steps
        if re.search(r"\b(?:прикрепить|загрузить)\w*\b", step, re.IGNORECASE)
        and re.search(r"\bфайл\w*\b", step, re.IGNORECASE)
    ]
    for index, initial_action in enumerate(file_actions):
        if re.search(r"\bпопыт\w*\b", initial_action, re.IGNORECASE):
            continue
        initial_identity = attachment_identity(initial_action)
        for attempted_action in file_actions[index + 1 :]:
            if not re.search(r"\bпопыт\w*\b", attempted_action, re.IGNORECASE):
                continue
            attempted_identity = attachment_identity(attempted_action)
            if initial_identity and attempted_identity and initial_identity == attempted_identity:
                continue
            return True
    return False


def has_nontrivial_state_formation(row: dict[str, str]) -> bool:
    formation = row.get("Формирование состояния", "").strip()
    return bool(formation) and not MATRIX_STATE_NOT_ACTIONABLE_RE.search(formation)


def has_explicit_follow_up_observation(steps: list[str]) -> bool:
    action_indexes = [
        index for index, step in enumerate(steps) if SAVE_OR_CLOSE_ACTION_RE.search(step)
    ]
    return any(
        FOLLOW_UP_OBSERVATION_RE.search(step)
        for index in action_indexes
        for step in steps[index + 1 :]
    )


def validate_state_formation_contract(
    *,
    tc_id: str,
    body: str,
    row: dict[str, str],
    obligation: dict[str, Any] | None,
    artifact: str,
) -> list[ScopeFinding]:
    """Validate deterministic parts of state → action → observation design.

    The validator deliberately checks only repeatable structural signals.  It
    does not claim to infer product semantics from prose; that remains the job
    of the independent reviewer.
    """
    findings: list[ScopeFinding] = []
    steps = numbered_steps(test_case_field(body, "Шаги"))
    if not steps:
        findings.append(finding(
            "test-case-numbered-steps",
            "execution-readiness",
            "Шаги тест-кейса должны быть отдельными нумерованными действиями",
            f"{tc_id}: поле «Шаги» не содержит нумерованного действия.",
            artifact,
            remediation_owner="writer",
        ))
        return findings
    if has_nontrivial_state_formation(row):
        if len(steps) < 2 or not any(STATE_FORMATION_VERB_RE.search(step) for step in steps[:-1]):
            findings.append(finding(
                "test-case-state-formation-step",
                "execution-readiness",
                "Состояние для проверки не сформировано отдельным шагом",
                f"{tc_id}: сначала отразите «Формирование состояния» из matrix, затем отдельным шагом выполните проверяемое действие.",
                artifact,
                remediation_owner="writer",
            ))
    statement = str((obligation or {}).get("statement") or "")
    expected_result = test_case_field(body, "Итоговый ожидаемый результат")
    source_literal_required = required_message_literals(statement)
    for literal in source_literal_required:
        if literal not in expected_result:
            findings.append(finding(
                "test-case-source-message-literal",
                "semantic-completeness",
                "Тест-кейс потерял дословное сообщение из ФТ",
                f"{tc_id}: ожидаемый результат должен содержать «{literal}».",
                artifact,
                remediation_owner="writer",
            ))
    lowered_statement = statement.casefold()
    preconditions = test_case_field(body, "Предусловия")
    if (
        "dadata" in lowered_statement
        and re.search(r"\bполучен\w*\s+список\s+dadata\b", preconditions, re.IGNORECASE)
        and any(INPUT_OR_SELECTION_RE.search(step) for step in steps)
    ):
        findings.append(finding(
            "test-case-dadata-precondition-duplicates-trigger",
            "execution-readiness",
            "Предусловие DaData повторяет состояние, формируемое шагами теста",
            f"{tc_id}: не указывайте полученный список DaData в предусловиях, "
            "если тест сам вводит запрос или выбирает подсказку. Оставьте в "
            "предусловиях открытый экран и подготовленный набор данных.",
            artifact,
            remediation_owner="writer",
        ))
    # The FT may require an effect directly after input (for example,
    # displaying suggestions or autofilling fields), or only after choosing a
    # suggestion. Require a selection step only when the source-backed matrix
    # action itself says that the user selects a suggestion.
    matrix_action = row.get("Проверяемое действие", "")
    requires_dadata_selection = bool(
        "dadata" in lowered_statement
        and re.search(r"\bвыбр\w*\b", matrix_action, re.IGNORECASE)
    )
    if requires_dadata_selection:
        selection_indexes = [
            index for index, step in enumerate(steps)
            if re.search(r"\bвыбр\w*\b", step, re.IGNORECASE)
        ]
        if not selection_indexes:
            findings.append(finding(
                "test-case-autocomplete-trigger",
                "execution-readiness",
                "В тест-кейсе отсутствует выбор подсказки DaData",
                f"{tc_id}: после ввода поискового значения отдельным шагом выберите подсказку DaData.",
                artifact,
                remediation_owner="writer",
            ))
        elif not any(
            INPUT_OR_SELECTION_RE.search(step) and re.search(r"\b(?:ввест|указ|наб[оа]р)\w*\b", step, re.IGNORECASE)
            for index in selection_indexes
            for step in steps[:index]
        ):
            findings.append(finding(
                "test-case-autocomplete-trigger",
                "execution-readiness",
                "Перед выбором подсказки не сформирован поисковый запрос",
                f"{tc_id}: добавьте отдельный шаг ввода поискового значения до выбора подсказки.",
                artifact,
                remediation_owner="writer",
            ))
    # A duplicate may be detected before saving (for example, a hint while the
    # user enters a name) or during the save flow.  The source-backed matrix
    # action, rather than a generic word such as "существующий" in the
    # obligation, determines whether a save trigger is required.
    duplicate_save_flow = (
        re.search(r"\b(?:одинаков|существующ).*\b(?:наименован|назван)|такой\s+партнер", lowered_statement)
        and re.search(r"\bсохран\w*\b", matrix_action, re.IGNORECASE)
    )
    if duplicate_save_flow:
        save_indexes = [index for index, step in enumerate(steps) if re.search(r"\bсохран\w*\b", step, re.IGNORECASE)]
        if not save_indexes or not any(
            INPUT_OR_SELECTION_RE.search(step) and NAME_FIELD_RE.search(step)
            for index in save_indexes
            for step in steps[:index]
        ):
            findings.append(finding(
                "test-case-duplicate-trigger",
                "execution-readiness",
                "Перед сохранением не сформировано состояние дубля",
                f"{tc_id}: отдельным шагом укажите существующее наименование до нажатия «Сохранить».",
                artifact,
                remediation_owner="writer",
            ))
    if "обязательн" in lowered_statement and re.search(r"\b(?:не\s+сохран|ошибк|подсвеч|валидац)\w*", expected_result, re.IGNORECASE):
        save_indexes = [index for index, step in enumerate(steps) if re.search(r"\bсохран\w*\b", step, re.IGNORECASE)]
        if save_indexes and not any(
            EMPTY_STATE_RE.search(step)
            for index in save_indexes
            for step in steps[:index]
        ):
            findings.append(finding(
                "test-case-required-empty-trigger",
                "execution-readiness",
                "Перед проверкой обязательности не задано пустое значение поля",
                f"{tc_id}: отдельным шагом оставьте проверяемое поле пустым до нажатия «Сохранить».",
                artifact,
                remediation_owner="writer",
            ))
    no_save_source = NO_SAVE_SOURCE_RE.search(statement) is not None
    has_close_or_cancel = any(NO_SAVE_ACTION_RE.search(step) for step in steps)
    if no_save_source and has_close_or_cancel and NO_SAVE_PERSISTENCE_ORACLE_RE.search(expected_result) is None:
        findings.append(finding(
            "test-case-no-save-persistence-oracle",
            "semantic-completeness",
            "Закрытие без сохранения не подтверждает отсутствие созданного или сохранённого объекта",
            f"{tc_id}: если источник задаёт закрытие без сохранения, итоговый ожидаемый результат должен явно подтвердить, что объект не создан или изменения не сохранены.",
            artifact,
            remediation_owner="writer",
        ))
    if no_save_source and not has_explicit_follow_up_observation(steps):
        findings.append(finding(
            "test-case-no-save-observation",
            "execution-readiness",
            "Отсутствие сохранения не подтверждено повторным наблюдением",
            f"{tc_id}: после сохранения, отмены или закрытия добавьте отдельный шаг проверки отсутствия нового объекта или изменений.",
            artifact,
            remediation_owner="writer",
        ))
    return findings


def is_dadata_obligation(obligation: Mapping[str, Any] | None) -> bool:
    """Whether an obligation requires an actual DaData-backed interaction."""
    return "dadata" in str((obligation or {}).get("statement") or "").casefold()


def verified_dadata_fixture_literals(
    *, fixture_root: Path, fixture_id: str
) -> tuple[set[str], str | None]:
    """Load exact literals only from an immutable verified DaData receipt."""
    fixture_dir = fixture_root / fixture_id
    receipt_path = fixture_dir / f"{fixture_id}.verification.json"
    try:
        receipt = read_json(receipt_path)
    except PracticalV09Error:
        return set(), "не найден verification receipt"
    snapshot_name = str(receipt.get("response_snapshot") or "")
    snapshot_path = fixture_dir / snapshot_name
    if (
        receipt.get("fixture_id") != fixture_id
        or receipt.get("provider") != "DaData"
        or receipt.get("status") != "verified"
        or not snapshot_name
        or not snapshot_path.is_file()
        or str(receipt.get("response_sha256") or "") != sha256_file(snapshot_path)
    ):
        return set(), "verification receipt или snapshot не прошли проверку целостности"
    request = receipt.get("request")
    expected_response = receipt.get("expected_response")
    if not isinstance(request, dict) or not isinstance(expected_response, dict):
        return set(), "verification receipt не содержит request/expected_response"
    try:
        response_payload = read_json(snapshot_path)
    except PracticalV09Error:
        return set(), "response snapshot не читается как JSON"
    suggestions = response_payload.get("suggestions")
    exact_suggestion = str(expected_response.get("exact_suggestion") or "")
    components = expected_response.get("exact_components")
    if not isinstance(suggestions, list) or not isinstance(components, dict):
        return set(), "response snapshot или receipt не содержит данных для сверки"
    matching_suggestions = [
        item for item in suggestions
        if isinstance(item, dict) and item.get("value") == exact_suggestion
    ]
    if len(matching_suggestions) != 1:
        return set(), "response snapshot не содержит единственную ожидаемую подсказку"
    response_data = matching_suggestions[0].get("data")
    if not isinstance(response_data, dict):
        return set(), "ожидаемая подсказка не содержит data"
    for dotted_key, expected_value in components.items():
        value: Any = response_data
        for part in str(dotted_key).split("."):
            value = value.get(part) if isinstance(value, dict) else None
        if value != expected_value:
            return set(), f"response snapshot не подтверждает компонент {dotted_key}"
    literals = {
        str(request.get("parameters", {}).get("query") or "").strip(),
        exact_suggestion.strip(),
    }
    literals.update(str(value).strip() for value in components.values())
    return {literal for literal in literals if literal and literal != "not_applicable"}, None


def validate_dadata_test_data_contract(
    *,
    tc_id: str,
    test_data: str,
    artifact: str,
    execution_status: str,
    fixture_root: Path,
) -> list[ScopeFinding]:
    """Reject circular DaData inputs while allowing an explicitly missing fixture.

    A stable integration fixture is the preferred way to make a case executable.
    When it is genuinely unavailable, a ``needs-test-data`` case may instead
    specify the required profile and a reproducible preparation method.  The
    validator intentionally does not infer whether a live DaData response is
    stable; the separate reviewer must still examine the selected profile.
    """
    findings: list[ScopeFinding] = []
    if any(pattern.search(test_data) for pattern in DADATA_GENERIC_DATA_PATTERNS):
        findings.append(finding(
            "test-case-dadata-generic-data",
            "execution-readiness",
            "DaData-данные описаны круговой общей формулировкой",
            f"{tc_id}: не используйте «организация с известными реквизитами» "
            "или «подготовить организацию» как тестовые данные. Укажите "
            "сохранённый FX-DADATA fixture с literals либо свойства реально "
            "недостающего набора и строку «Способ подготовки: ...».",
            artifact,
            remediation_owner="writer",
        ))
        return findings
    fixture_ids = set(DADATA_FIXTURE_ID_RE.findall(test_data))
    concrete_literals = backtick_literals(test_data) - fixture_ids
    if fixture_ids:
        allowed_literals: set[str] = set()
        unavailable: list[str] = []
        for fixture_id in sorted(fixture_ids):
            values, error = verified_dadata_fixture_literals(
                fixture_root=fixture_root,
                fixture_id=fixture_id,
            )
            if error is not None:
                unavailable.append(f"{fixture_id}: {error}")
            allowed_literals.update(values)
        if unavailable:
            if execution_status != "needs-test-data":
                findings.append(finding(
                    "test-case-dadata-unverified-fixture-status",
                    "execution-readiness",
                    "DaData-fixture не подтверждён, но тест-кейс отмечен как исполнимый",
                    f"{tc_id}: " + "; ".join(unavailable) + ". До появления verified fixture используйте primary статус needs-test-data.",
                    artifact,
                    remediation_owner="writer",
                ))
            if concrete_literals:
                findings.append(finding(
                    "test-case-dadata-unverified-literal",
                    "execution-readiness",
                    "В DaData-тесте использованы значения без подтверждённого fixture",
                    f"{tc_id}: удалите непроверенные literals «{', '.join(sorted(concrete_literals))}» и укажите свойства требуемого профиля и способ подготовки либо добавьте verified fixture.",
                    artifact,
                    remediation_owner="writer",
                ))
            if not (
                DADATA_PREPARATION_RE.search(test_data)
                and DADATA_PROPERTY_RE.search(test_data)
            ):
                findings.append(finding(
                    "test-case-dadata-test-data-contract",
                    "execution-readiness",
                    "Для DaData-сценария без verified fixture не определены требуемые свойства профиля",
                    f"{tc_id}: укажите точные свойства отсутствующего ответа и строку «Способ подготовки: ...».",
                    artifact,
                    remediation_owner="writer",
                ))
            return findings
        unknown_literals = concrete_literals - allowed_literals
        if unknown_literals:
            findings.append(finding(
                "test-case-dadata-fixture-literal-mismatch",
                "execution-readiness",
                "В DaData-тесте указан literal, которого нет в подтверждённом fixture",
                f"{tc_id}: значения «{', '.join(sorted(unknown_literals))}» не подтверждены указанным FX-DADATA fixture.",
                artifact,
                remediation_owner="writer",
            ))
        if not concrete_literals:
            findings.append(finding(
                "test-case-dadata-fixture-literals",
                "execution-readiness",
                "DaData-fixture указан без конкретного значения для выполнения сценария",
                f"{tc_id}: рядом с FX-DADATA fixture укажите хотя бы один literal, который используется в шаге или основном ожидаемом результате.",
                artifact,
                remediation_owner="writer",
            ))
        return findings
    if concrete_literals:
        findings.append(finding(
            "test-case-dadata-unverified-literal",
            "execution-readiness",
            "В DaData-тесте использованы значения без подтверждённого fixture",
            f"{tc_id}: literals «{', '.join(sorted(concrete_literals))}» допустимы только из сохранённого verified FX-DADATA fixture.",
            artifact,
            remediation_owner="writer",
        ))
        return findings
    if execution_status != "needs-test-data":
        findings.append(finding(
            "test-case-dadata-missing-fixture-status",
            "execution-readiness",
            "DaData-тест без сохранённого fixture не помечен как needs-test-data",
            f"{tc_id}: до появления verified FX-DADATA fixture primary статус должен быть needs-test-data.",
            artifact,
            remediation_owner="writer",
        ))
    if not (
        DADATA_PREPARATION_RE.search(test_data)
        and DADATA_PROPERTY_RE.search(test_data)
    ):
        findings.append(finding(
            "test-case-dadata-test-data-contract",
            "execution-readiness",
            "Для DaData-сценария не определены воспроизводимые тестовые данные",
            f"{tc_id}: укажите сохранённый FX-DADATA fixture с literals либо "
            "точные требуемые свойства отсутствующего профиля и строку "
            "«Способ подготовки: ...».",
            artifact,
            remediation_owner="writer",
        ))
    return findings


def validate_test_data_executability(
    *,
    tc_id: str,
    test_data: str,
    artifact: str,
) -> list[ScopeFinding]:
    """Reject test-data placeholders that cannot be reproduced by a tester.

    This is deliberately narrower than a semantic review: it catches the
    recurring forms of circular completion data and setup actions disguised as
    test data.  A reviewer still decides whether a particular literal is fit
    for a requirement.
    """
    findings: list[ScopeFinding] = []
    if any(pattern.search(test_data) for pattern in TEST_DATA_GENERIC_COMPLETION_PATTERNS):
        findings.append(finding(
            "test-case-test-data-generic-completion",
            "execution-readiness",
            "Тестовые данные не определяют значения для сохранения или перехода",
            f"{tc_id}: не заменяйте значения формулировкой «остальные обязательные "
            "поля заполнить допустимо» или «уникальный набор обязательных "
            "значений». Укажите literals либо точные свойства каждого нужного "
            "значения и способ подготовки.",
            artifact,
            remediation_owner="writer",
        ))
    for pattern in TEST_DATA_RUNTIME_PLACEHOLDER_PATTERNS:
        match = pattern.search(test_data)
        if match is None:
            continue
        findings.append(finding(
            "test-case-test-data-runtime-placeholder",
            "execution-readiness",
            "В тестовых данных использован служебный placeholder вместо воспроизводимого значения",
            f"{tc_id}: «{match.group(0)}» не является значением для ввода или проверки. Укажите конкретное значение с подтверждённым происхождением либо, для DaData, FX-DADATA fixture и выбранную подсказку.",
            artifact,
            remediation_owner="writer",
        ))
    if TEST_DATA_ACTION_LEAK_RE.search(test_data):
        findings.append(finding(
            "test-case-test-data-action-leak",
            "execution-readiness",
            "В разделе «Тестовые данные» записано действие вместо входного значения",
            f"{tc_id}: перенесите пользовательское действие в «Шаги», а в "
            "«Тестовые данные» оставьте конкретное значение, файл или точные "
            "свойства с воспроизводимым способом подготовки.",
            artifact,
            remediation_owner="writer",
        ))
    requires_preparation = (
        TEST_DATA_BOUNDARY_RE.search(test_data) is not None
        or TEST_DATA_FILE_PREPARATION_RE.search(test_data) is not None
    )
    if requires_preparation and TEST_DATA_PREPARATION_RE.search(test_data) is None:
        findings.append(finding(
            "test-case-test-data-preparation-missing",
            "execution-readiness",
            "Тестовые данные требуют подготовки, но её способ не указан",
            f"{tc_id}: для граничной строки или подготовленного файла укажите "
            "точные свойства и строку «Способ подготовки: ...», достаточную для "
            "повторного ручного и автоматизированного прогона.",
            artifact,
            remediation_owner="writer",
        ))
    return findings


def validate_section_numbering(
    *,
    blocks: list[dict[str, str]],
    artifact: str,
) -> list[ScopeFinding]:
    """Ensure that a canonical scope file exposes an executable local sequence.

    ``TC-*`` identifiers are traceability identifiers and may contain a source
    code.  They are not a usable answer to "which case and how many are in
    this section?".  The explicit number is therefore validated separately.
    """
    findings: list[ScopeFinding] = []
    total = len(blocks)
    seen_numbers: dict[int, str] = {}
    for expected_number, block in enumerate(blocks, start=1):
        tc_id = block["id"]
        match = SECTION_NUMBER_RE.search(block["body"])
        if match is None:
            findings.append(finding(
                "test-case-section-numbering-missing",
                "execution-readiness",
                "В тест-кейсе отсутствует сквозной номер внутри раздела",
                f"{tc_id}: добавьте поле «Номер в разделе» в формате «{expected_number} из {total}».",
                artifact,
                remediation_owner="writer",
            ))
            continue
        number, declared_total = (int(match.group(1)), int(match.group(2)))
        if declared_total != total:
            findings.append(finding(
                "test-case-section-numbering-total",
                "traceability",
                "В тест-кейсе указан неверный общий счётчик раздела",
                f"{tc_id}: указано «{number} из {declared_total}», в canonical file {total} TC.",
                artifact,
                remediation_owner="writer",
            ))
        previous_tc_id = seen_numbers.get(number)
        if previous_tc_id is not None:
            findings.append(finding(
                "test-case-section-numbering-duplicate",
                "traceability",
                "Сквозной номер раздела повторяется",
                f"{tc_id}: номер {number} уже использован в {previous_tc_id}.",
                artifact,
                remediation_owner="writer",
            ))
        else:
            seen_numbers[number] = tc_id
        if number != expected_number:
            findings.append(finding(
                "test-case-section-numbering-order",
                "traceability",
                "Сквозная нумерация раздела содержит пропуск или нарушенный порядок",
                f"{tc_id}: на позиции {expected_number} ожидается «{expected_number} из {total}», указано «{number} из {declared_total}».",
                artifact,
                remediation_owner="writer",
            ))
    return findings


def successful_create_case(
    *,
    flow_kind: str | None,
    steps: str,
    expected_result: str,
) -> bool:
    """Whether a TC claims a successful persistence of a newly created object."""
    return bool(
        flow_kind == "create"
        and re.search(r"\bсохран\w*\b", steps, re.IGNORECASE)
        and SUCCESSFUL_CREATE_EXPECTED_RE.search(expected_result)
        and SUCCESSFUL_CREATE_NEGATION_RE.search(expected_result) is None
    )


def successful_create_object_key(test_data: str) -> str | None:
    """Extract a concrete object key from one approved lifecycle label."""
    for pattern in CREATE_OBJECT_KEY_PATTERNS:
        match = pattern.search(test_data)
        if match is not None:
            return match.group(1)
    return None


def successful_create_has_initial_absence(test_data: str) -> bool:
    """Accept only approved, equivalent declarations of initial absence."""
    return any(pattern.search(test_data) is not None for pattern in CREATE_OBJECT_ABSENCE_PATTERNS)


def successful_create_has_cleanup(postconditions: str) -> bool:
    """Accept only approved, equivalent cleanup/isolation declarations."""
    return any(pattern.search(postconditions) is not None for pattern in SUCCESSFUL_CREATE_CLEANUP_PATTERNS)


def validate_test_cases(
    tc_path: Path,
    package_root: Path,
    obligations: dict[str, Any],
    matrix_by_scenario: dict[str, dict[str, str]],
    workflow_state: Mapping[str, Any] | None = None,
    matrix_path: Path | None = None,
    fixture_root: Path | None = None,
) -> list[ScopeFinding]:
    artifact = relative_to_package(package_root, tc_path)
    try:
        blocks = parse_test_case_blocks(tc_path)
    except PracticalV09Error as exc:
        return [finding("test-cases-unreadable", "source-integrity", "Недоступен файл тест-кейсов", str(exc), artifact, remediation_owner="writer")]
    findings: list[ScopeFinding] = []
    if not blocks:
        return [finding("test-cases-empty", "semantic-completeness", "В файле нет тест-кейсов компактного формата", "Ожидается заголовок уровня ## или ### с TC-*.", artifact, remediation_owner="writer")]
    findings.extend(validate_section_numbering(blocks=blocks, artifact=artifact))
    seen_ids: set[str] = set()
    covered_scenarios: dict[str, list[str]] = {}
    covered_obligation_contexts: dict[tuple[str, str], list[str]] = {}
    successful_creates: dict[str, list[tuple[str, bool]]] = {}
    active_entries = {
        str(item.get("id")): item
        for item in active_obligations(obligations)
    }
    context_flow_kinds = {
        str(context.get("id")): execution_context_flow_kind(context)
        for obligation in active_entries.values()
        for context in execution_contexts(obligation)
    }
    setup_catalog = execution_setups(obligations)
    shared_result_literals = common_result_literals_by_obligation(obligations)
    fixture_root = fixture_root or Path("__missing_dadata_fixture_root__")
    consolidation_enabled = matrix_consolidation_enabled(
        state=workflow_state, matrix_path=matrix_path
    )
    shared_scenarios_by_tc: dict[str, frozenset[str]] = {}
    consolidation_by_tc: dict[str, dict[str, Any]] = {}
    if consolidation_enabled:
        _consolidation_findings, consolidation = scenario_consolidation_contract(
            state=workflow_state,
            rows_by_scenario=matrix_by_scenario,
            artifact=relative_to_package(package_root, matrix_path)
            if matrix_path is not None
            else "workflow-state.json",
            matrix_path=matrix_path,
        )
        shared_scenarios_by_tc = consolidation["shared_scenarios_by_tc"]
        consolidation_by_tc = consolidation["consolidation_by_tc"]
    for block in blocks:
        tc_id = block["id"]
        body = block["body"]
        if tc_id in seen_ids:
            findings.append(finding("test-case-duplicate-id", "traceability", "Повторяется TC-ID", f"Повторяется {tc_id}.", artifact, remediation_owner="writer"))
        seen_ids.add(tc_id)
        for field in REQUIRED_TC_FIELDS:
            if not re.search(rf"(?m)^\*\*{re.escape(field)}:\*\*\s*\S", body):
                findings.append(finding("test-case-required-field", "execution-readiness", "В тест-кейсе отсутствует обязательное поле", f"{tc_id}: отсутствует «{field}».", artifact, remediation_owner="writer"))
        if (
            re.search(r"\bSETUP-[A-Z0-9-]+\b", body)
            or VOLATILE_ENVIRONMENT_CONFIGURATION_RE.search(body)
        ):
            findings.append(finding(
                "test-case-volatile-environment-reference",
                "execution-readiness",
                "Тест-кейс содержит волатильные параметры среды",
                f"{tc_id}: не указывайте SETUP-идентификаторы, URL, логин, пароль, токен или cookie. "
                "Оставьте нейтральное предусловие о доступе к модулю; конкретная среда и учётная запись предоставляются исполнителю вне тест-кейса.",
                artifact,
                remediation_owner="writer",
            ))
        package_id = test_case_field(body, "package_id")
        if package_id and not re.fullmatch(r"WP-\d{2,}", package_id):
            findings.append(finding(
                "test-case-package-id",
                "traceability",
                "В тест-кейсе указан недопустимый package_id",
                f"{tc_id}: package_id должен иметь вид WP-01.",
                artifact,
                remediation_owner="writer",
            ))
        test_data = test_case_field(body, "Тестовые данные")
        if any(pattern.search(test_data) for pattern in TEST_DATA_TAUTOLOGY_PATTERNS):
            findings.append(finding(
                "test-case-test-data-tautology",
                "execution-readiness",
                "Тестовые данные пересказывают проверяемое правило",
                f"{tc_id}: укажите конкретные значения либо точные свойства и способ подготовки набора данных.",
                artifact,
                remediation_owner="writer",
            ))
        findings.extend(validate_test_data_executability(
            tc_id=tc_id,
            test_data=test_data,
            artifact=artifact,
        ))
        steps_value = test_case_field(body, "Шаги")
        declared_literals = backtick_literals(test_data)
        runtime_literals = backtick_literals(
            "\n".join((steps_value, test_case_field(body, "Итоговый ожидаемый результат")))
        )
        unused_literals = sorted(declared_literals - runtime_literals)
        if (
            len(declared_literals) >= 4
            and len(unused_literals) >= 3
            and not has_test_data_completion_action(steps_value)
        ):
            findings.append(finding(
                "test-case-test-data-profile-overfull",
                "style",
                "Тестовые данные содержат вероятно неиспользуемую часть профиля",
                f"{tc_id}: повторно проверьте literals «{', '.join(unused_literals)}». "
                "Оставьте только значения, нужные для шагов, ожидаемого результата или "
                "сохранения/перехода. Повторное использование одного проверенного профиля "
                "само по себе допустимо.",
                artifact,
                remediation_owner="writer",
                severity="warning",
            ))
        for step in numbered_steps(steps_value):
            if any(pattern.search(step) for pattern in META_STATE_STEP_PATTERNS):
                findings.append(finding(
                    "test-case-meta-state-step",
                    "execution-readiness",
                    "Шаг тест-кейса описывает служебную подготовку вместо действия пользователя",
                    f"{tc_id}: замените «{step}» конкретным действием с экраном, полем и значением либо перенесите недоступный fixture в предпосылки.",
                    artifact,
                    remediation_owner="writer",
                ))
            if CONTEXT_LABEL_AS_ACTION_RE.search(step):
                findings.append(finding(
                    "test-case-context-label-as-action",
                    "execution-readiness",
                    "Шаг тест-кейса подменяет действие пользователя названием контекста",
                    f"{tc_id}: замените «{step}» конкретным действием входа на экран "
                    "либо укажите уже открытый экран в предусловиях. CTX-* не является "
                    "пользовательским действием.",
                    artifact,
                    remediation_owner="writer",
                ))
        single_file_limit = re.search(
            r"\b(?:не\s+более\s+одн\w*\s+файл\w*|втор\w*\s+файл\w*)\b",
            body,
            re.IGNORECASE,
        )
        if single_file_limit and not has_complete_single_file_trigger(numbered_steps(steps_value)):
            findings.append(finding(
                "test-case-upload-cardinality-trigger",
                "execution-readiness",
                "Для проверки ограничения числа файлов не создано исходное состояние",
                f"{tc_id}: отдельно прикрепите первый допустимый файл, затем отдельным шагом попытайтесь прикрепить второй.",
                artifact,
                remediation_owner="writer",
            ))
        status_match = re.search(r"(?m)^\*\*Статус исполнения:\*\*\s*(\S+)", body)
        if status_match and status_match.group(1) not in ALLOWED_EXECUTION_STATUSES:
            findings.append(finding(
                "test-case-execution-status",
                "execution-readiness",
                "В тест-кейсе указан неизвестный статус исполнения",
                f"{tc_id}: «{status_match.group(1)}» не входит в допустимый перечень.",
                artifact,
                remediation_owner="writer",
            ))
        context_match = re.search(r"(?m)^\*\*Контекст исполнения:\*\*\s*(.+)$", body)
        context_id = context_id_from_cell(context_match.group(1) if context_match else "")
        if not context_id:
            findings.append(finding(
                "test-case-execution-context",
                "execution-readiness",
                "Тест-кейс не связан ровно с одним контекстом исполнения",
                f"{tc_id}: поле «Контекст исполнения» должно содержать один CTX-*.",
                artifact,
                remediation_owner="writer",
            ))
        elif context_flow_kinds.get(context_id) == "edit":
            create_steps = [step for step in numbered_steps(steps_value) if opens_new_card(step)]
            if create_steps:
                findings.append(finding(
                    "test-case-edit-context-new-card",
                    "execution-readiness",
                    "Тест-кейс редактирования открывает новую или пустую карточку",
                    f"{tc_id}: контекст {context_id} требует работу с сохранённым объектом; "
                    f"создание новой карточки в шаге «{create_steps[0]}» подменяет edit-поток.",
                    artifact,
                    remediation_owner="writer",
                ))
        postconditions = test_case_field(body, "Постусловия")
        expected_result = test_case_field(body, "Итоговый ожидаемый результат")
        if successful_create_case(
            flow_kind=context_flow_kinds.get(context_id),
            steps=steps_value,
            expected_result=expected_result,
        ):
            object_key_value = successful_create_object_key(test_data)
            if object_key_value is None:
                findings.append(finding(
                    "test-case-successful-create-key-missing",
                    "execution-readiness",
                    "Успешное создание не содержит конкретный ключ создаваемого объекта",
                    f"{tc_id}: в «Тестовые данные» добавьте строку «Ключ создаваемого объекта: ...» с конкретными значениями, определяющими уникальность объекта в системе.",
                    artifact,
                    remediation_owner="writer",
                ))
            if not successful_create_has_initial_absence(test_data):
                findings.append(finding(
                    "test-case-successful-create-initial-state-missing",
                    "execution-readiness",
                    "Успешное создание не подтверждает отсутствие объекта до начала теста",
                    f"{tc_id}: в «Тестовые данные» добавьте «Исходное состояние объекта: отсутствует»; происхождение данных от DaData не доказывает отсутствие объекта в системе.",
                    artifact,
                    remediation_owner="writer",
                ))
            has_cleanup = successful_create_has_cleanup(postconditions)
            if not has_cleanup:
                findings.append(finding(
                    "test-case-successful-create-cleanup-missing",
                    "execution-readiness",
                    "Успешное создание не изолировано от повторного прогона",
                    f"{tc_id}: в «Постусловия» укажите конкретное удаление созданного объекта, восстановление исходного состояния или изолированный прогон. Иначе следующий TC может столкнуться с дублем.",
                    artifact,
                    remediation_owner="writer",
                ))
            if object_key_value is not None:
                object_key = " ".join(object_key_value.casefold().split())
                successful_creates.setdefault(object_key, []).append((tc_id, has_cleanup))
        title = test_case_field(body, "Название").casefold()
        if context_flow_kinds.get(context_id) == "create" and MIXED_CREATE_EDIT_TITLE_RE.search(title):
            findings.append(finding(
                "test-case-title-context-mismatch",
                "semantic-completeness",
                "Название тест-кейса смешивает создание и редактирование",
                f"{tc_id}: контекст {context_id} относится к созданию; уберите из названия редактирование и вынесите его в отдельный TC контекста CTX-EDIT.",
                artifact,
                remediation_owner="writer",
            ))
        if context_flow_kinds.get(context_id) == "edit" and MIXED_CREATE_EDIT_TITLE_RE.search(title):
            findings.append(finding(
                "test-case-title-context-mismatch",
                "semantic-completeness",
                "Название тест-кейса смешивает создание и редактирование",
                f"{tc_id}: контекст {context_id} относится к редактированию; уберите из названия создание и вынесите его в отдельный TC контекста CTX-CREATE.",
                artifact,
                remediation_owner="writer",
            ))
        expected_result_count = len(re.findall(r"(?m)^\*\*Итоговый ожидаемый результат:\*\*", body))
        if expected_result_count != 1:
            findings.append(finding("test-case-primary-oracle", "semantic-completeness", "У тест-кейса должен быть один основной ожидаемый результат", f"{tc_id}: найдено полей ожидаемого результата: {expected_result_count}.", artifact, remediation_owner="writer"))
        trace_match = re.search(r"(?m)^\*\*Трассировка:\*\*\s*(.+)$", body)
        trace = trace_match.group(1) if trace_match else ""
        raw_obligation_ids = re.findall(r"\bOBL-[A-Z0-9-]+\b", trace)
        raw_scenario_ids = re.findall(r"\bSCN-[A-Z0-9-]+\b", trace)
        obligation_ids = list(dict.fromkeys(raw_obligation_ids))
        scenario_ids = list(dict.fromkeys(raw_scenario_ids))
        if len(raw_obligation_ids) != len(obligation_ids):
            findings.append(finding(
                "test-case-obligation-trace-duplicate",
                "traceability",
                "В трассировке тест-кейса повторяется обязательство ФТ",
                f"{tc_id}: OBL должен быть указан один раз.",
                artifact,
                remediation_owner="writer",
            ))
        if len(raw_scenario_ids) != len(scenario_ids):
            findings.append(finding(
                "test-case-scenario-trace-duplicate",
                "traceability",
                "В трассировке тест-кейса повторяется сценарий матрицы",
                f"{tc_id}: SCN должен быть указан один раз.",
                artifact,
                remediation_owner="writer",
            ))
        if not obligation_ids:
            findings.append(finding(
                "test-case-obligation-trace",
                "traceability",
                "Тест-кейс не связан с обязательством ФТ",
                f"{tc_id}: в «Трассировка» не найден OBL-*.",
                artifact,
                remediation_owner="writer",
            ))
        if not scenario_ids:
            findings.append(finding(
                "test-case-scenario-trace",
                "traceability",
                "Тест-кейс не связан со сценарием матрицы",
                f"{tc_id}: в «Трассировка» не найден SCN-*.",
                artifact,
                remediation_owner="writer",
            ))
        authorized_shared = (
            consolidation_enabled
            and shared_scenarios_by_tc.get(tc_id) == frozenset(scenario_ids)
        )
        consolidation_decision = consolidation_by_tc.get(tc_id, {})
        if (
            consolidation_decision.get("parameterization_basis")
            == COMPOSITE_RESULT_PARAMETERIZATION_BASIS
            and not has_composite_result_table(
                body,
                consolidation_decision.get("field_inventory", ()),
            )
        ):
            findings.append(finding(
                "test-case-composite-result-table",
                "test-design",
                "Составной результат по нескольким полям не раскрыт таблицей",
                f"{tc_id}: для объединения «поля одного составного результата» "
                "добавьте таблицу «Поле | Ожидаемое значение/результат» со всеми "
                "полями из field_inventory.",
                artifact,
                remediation_owner="writer",
                blocking=True,
            ))
        if (
            obligation_ids
            and scenario_ids
            and len(obligation_ids) != len(scenario_ids)
            and not authorized_shared
        ):
            findings.append(finding(
                "test-case-obligation-scenario-count",
                "traceability",
                "Число обязательств и сценариев в общей трассировке не совпадает",
                f"{tc_id}: OBL={len(obligation_ids)}, SCN={len(scenario_ids)}. "
                "Общий TC допустим только для попарно связанных строк одной группы вероятного дублирования.",
                artifact,
                remediation_owner="writer",
            ))
        trace_codes = requirement_codes(trace)
        for obligation_id in obligation_ids:
            pair = (obligation_id, context_id)
            covered_obligation_contexts.setdefault(pair, []).append(tc_id)
            if obligation_id not in active_obligation_ids(obligations):
                findings.append(finding(
                    "test-case-obligation-superseded",
                    "traceability",
                    "Тест-кейс ссылается на обязательство, отменённое решением БА",
                    f"{tc_id}: {obligation_id} не должно попадать в test cases.",
                    artifact,
                    remediation_owner="writer",
                ))
            obligation = active_entries.get(obligation_id)
            if obligation is not None:
                source_anchor = str(obligation.get("source_anchor") or "")
                source_codes = requirement_codes(source_anchor)
                missing_source_codes = [
                    source_codes[key]
                    for key in sorted(source_codes)
                    if key not in trace_codes
                ]
                if missing_source_codes:
                    findings.append(finding(
                        "test-case-source-code-trace",
                        "traceability",
                        "В трассировке тест-кейса потерян код требования ФТ",
                        f"{tc_id}: для {obligation_id} добавьте в «Трассировка» коды из source_anchor: "
                        + ", ".join(missing_source_codes) + ".",
                        artifact,
                        evidence=[
                            f"source_anchor={source_anchor}",
                            f"trace={trace}",
                        ],
                        remediation_owner="writer",
                    ))
        if any(is_dadata_obligation(active_entries.get(obligation_id)) for obligation_id in obligation_ids):
            findings.extend(validate_dadata_test_data_contract(
                tc_id=tc_id,
                test_data=test_data,
                artifact=artifact,
                execution_status=status_match.group(1) if status_match else "",
                fixture_root=fixture_root,
            ))
        mapped_rows: list[tuple[str, dict[str, str]]] = []
        for scenario_id in scenario_ids:
            covered_scenarios.setdefault(scenario_id, []).append(tc_id)
            mapped_row = matrix_by_scenario.get(scenario_id)
            if mapped_row is None:
                findings.append(finding(
                    "test-case-scenario-unknown",
                    "traceability",
                    "Тест-кейс ссылается на отсутствующий сценарий матрицы",
                    f"{tc_id}: {scenario_id} не найден в test-design-matrix.md.",
                    artifact,
                    remediation_owner="writer",
                ))
                continue
            mapped_rows.append((scenario_id, mapped_row))
        mapped_obligation_ids = {
            row.get("Обязательство ФТ", "") for _, row in mapped_rows
        }
        if mapped_rows and set(obligation_ids) != mapped_obligation_ids:
            findings.append(finding(
                "test-case-scenario-obligation-mismatch",
                "traceability",
                "Сценарии матрицы и обязательства тест-кейса не образуют одну связь",
                f"{tc_id}: OBL в TC — {', '.join(obligation_ids)}; OBL в SCN — "
                + ", ".join(sorted(mapped_obligation_ids)) + ".",
                artifact,
                remediation_owner="writer",
            ))
        if len(scenario_ids) > 1 and consolidation_enabled:
            if not authorized_shared:
                findings.append(finding(
                    "test-case-shared-scenario-not-authorized",
                    "traceability",
                    "Один тест-кейс объединяет сценарии без решения о консолидации",
                    f"{tc_id}: решение CON-* в разделе консолидации matrix должно в точности содержать {', '.join(sorted(scenario_ids))} и этот planned TC-ID.",
                    artifact,
                    remediation_owner="writer",
                ))
        elif len(scenario_ids) > 1:
            group_keys = {
                str(row.get("_shared_test_case_group") or "")
                for _, row in mapped_rows
            }
            if (
                len(mapped_rows) != len(scenario_ids)
                or len(group_keys) != 1
                or not all(group_keys)
            ):
                findings.append(finding(
                    "test-case-shared-scenario-not-allowed",
                    "traceability",
                    "Один тест-кейс объединяет несопоставимые сценарии матрицы",
                    f"{tc_id}: несколько SCN допустимы только для одной группы вероятно дублирующих "
                    "сценариев с единым контекстом, действием и основным ожидаемым результатом.",
                    artifact,
                    remediation_owner="writer",
                ))
        checked_matrix_field_labels: set[str] = set()
        tc_labels = tc_explicit_ui_labels(body)
        for scenario_id, mapped_row in mapped_rows:
            mapped_pair = (
                mapped_row.get("Обязательство ФТ", ""),
                context_id_from_cell(mapped_row.get("Контекст исполнения", "")),
            )
            if mapped_pair[1] != context_id:
                findings.append(finding(
                    "test-case-scenario-context-mismatch",
                    "traceability",
                    "Сценарий тест-кейса относится к другому контексту исполнения",
                    f"{tc_id}: {scenario_id} связан с {mapped_pair[0]} / "
                    f"{mapped_pair[1] or '<без CTX>'}, а TC — с {context_id or '<без CTX>'}.",
                    artifact,
                    remediation_owner="writer",
                ))
            if tc_id != mapped_row.get("Планируемый TC-ID", ""):
                findings.append(finding(
                    "test-case-scenario-tc-id-mismatch",
                    "traceability",
                    "Фактический TC-ID не совпадает с планом сценария",
                    f"{tc_id}: {scenario_id} планирует {mapped_row.get('Планируемый TC-ID', '<без TC-ID>')}.",
                    artifact,
                    remediation_owner="writer",
                ))
            for field_label in sorted(
                matrix_field_labels(mapped_row.get("Проверяемый элемент", ""))
                - checked_matrix_field_labels
            ):
                checked_matrix_field_labels.add(field_label)
                if conflicts_with_matrix_field(
                    expected_label=field_label,
                    declared_labels=tc_labels,
                ):
                    findings.append(finding(
                        "test-case-matrix-element-binding",
                        "traceability",
                        "Тест-кейс подменяет проверяемый элемент из матрицы",
                        f"{tc_id}: {scenario_id} требует элемент «{field_label}», "
                        "но TC явно называет другое поле того же типа. Проверьте, что writer "
                        "не подменил поле шаблонным или однотипным полем.",
                        artifact,
                        remediation_owner="writer",
                    ))
            if status_match and status_match.group(1) != mapped_row.get("Статус исполнения"):
                findings.append(finding(
                    "test-case-execution-status-matrix",
                    "execution-readiness",
                    "Статус исполнения тест-кейса отличается от статуса в матрице",
                    f"{tc_id}: указан {status_match.group(1)}, в матрице {mapped_row.get('Статус исполнения')}.",
                    artifact,
                    remediation_owner="writer",
                ))
            mapped_obligation = active_entries.get(mapped_pair[0])
            for source_label, ui_label in visual_label_mappings(mapped_obligation, mapped_pair[1]):
                normalized_ui_label = normalized_matrix_phrase(ui_label)
                if normalized_ui_label not in tc_labels:
                    findings.append(finding(
                        "test-case-visual-label-binding",
                        "execution-readiness",
                        "Тест-кейс не использует подтверждённую подпись UI",
                        f"{tc_id}: для термина ФТ «{source_label}» в visual_binding зафиксирована "
                        f"подпись UI «{ui_label}». Назовите её явно в шаге или в ожидаемом "
                        "наблюдаемом результате; не подменяйте подпись UI термином ФТ.",
                        artifact,
                        remediation_owner="writer",
                    ))
            for literal in sorted(shared_result_literals.get(mapped_pair[0], set())):
                if literal not in test_case_field(body, "Итоговый ожидаемый результат"):
                    findings.append(finding(
                        "test-case-common-result-literal",
                        "semantic-completeness",
                        "Тест-кейс потерял общий результат отказа для самостоятельного класса невалидного ввода",
                        f"{tc_id}: для {mapped_pair[0]} ожидаемый результат должен содержать «{literal}».",
                        artifact,
                        remediation_owner="writer",
                    ))
            mapped_contexts = {
                str(context.get("id")): context
                for context in execution_contexts(mapped_obligation or {})
            }
            mapped_context = mapped_contexts.get(mapped_pair[1])
            if mapped_context is not None:
                secondary_limitations = secondary_execution_limitations(
                    mapped_context, setup_catalog
                )
                if secondary_limitations:
                    limitation_text = test_case_field(body, "Ограничения исполнения")
                    missing_limitations = [
                        setup_id
                        for setup_id, _availability in secondary_limitations
                        if setup_id not in limitation_text
                    ]
                    if (
                        not limitation_text
                        or missing_limitations
                        or not has_russian_prose(limitation_text)
                    ):
                        findings.append(finding(
                            "test-case-execution-limitations-incomplete",
                            "execution-readiness",
                            "Тест-кейс потерял существенное вторичное ограничение исполнения",
                            f"{tc_id}: добавьте поле «Ограничения исполнения» с русским пояснением и ссылками на "
                            + ", ".join(setup_id for setup_id, _ in secondary_limitations)
                            + ". Первичный статус исполнения не меняйте.",
                            artifact,
                            remediation_owner="writer",
                        ))
            findings.extend(validate_state_formation_contract(
                tc_id=tc_id,
                body=body,
                row=mapped_row,
                obligation=active_entries.get(mapped_pair[0]),
                artifact=artifact,
            ))
        body_without_metadata = re.sub(r"(?m)^\*\*(Тип|Приоритет|Статус исполнения):\*\*.*$", "", body)
        if FROZEN_PROFILE_PROCESS_LANGUAGE_RE.search(body_without_metadata):
            findings.append(finding(
                "test-case-process-language-frozen-profile",
                "style",
                "В пользовательском поле тест-кейса остался английский служебный термин",
                f"{tc_id}: замените «frozen profile» русской формулировкой "
                "«зафиксированный профиль» или «сохранённый профиль». ",
                artifact,
                remediation_owner="writer",
                blocking=True,
            ))
        process_match = RUNTIME_PROCESS_TC_MARKER_RE.search(body_without_metadata)
        if process_match is not None:
            findings.append(finding(
                "test-case-process-language-tc-marker",
                "style",
                "В пользовательском поле тест-кейса остался служебный маркер процесса",
                f"{tc_id}: «{process_match.group(0)}» замените описанием объекта, поля, действия или конкретного значения продукта.",
                artifact,
                remediation_owner="writer",
                blocking=True,
            ))
        if re.search(r"\b(source-backed|residual|fixture|blocked-observability)\b", body_without_metadata, flags=re.IGNORECASE):
            findings.append(finding("test-case-process-language", "style", "В тест-кейсе остался служебный английский текст", f"Проверьте пользовательские поля {tc_id}.", artifact, remediation_owner="writer", severity="warning"))
    for object_key, entries in sorted(successful_creates.items()):
        if len(entries) < 2 or all(has_cleanup for _tc_id, has_cleanup in entries):
            continue
        related_tcs = ", ".join(tc_id for tc_id, _has_cleanup in entries)
        for tc_id, has_cleanup in entries:
            if has_cleanup:
                continue
            findings.append(finding(
                "test-case-successful-create-key-reused",
                "execution-readiness",
                "Несколько успешных созданий используют один ключ без изоляции прогона",
                f"{tc_id}: ключ «{object_key}» повторяется в {related_tcs}. Выделите разные конкретные данные либо задайте cleanup/изолированный прогон для каждого создания.",
                artifact,
                remediation_owner="writer",
            ))
    for scenario_id, row in sorted(matrix_by_scenario.items()):
        mapped_tcs = covered_scenarios.get(scenario_id, [])
        if not mapped_tcs:
            findings.append(finding(
                "test-case-scenario-uncovered",
                "semantic-completeness",
                "Сценарий матрицы не покрыт тест-кейсом",
                f"Для {scenario_id} нет TC.",
                artifact,
                remediation_owner="writer",
            ))
        elif len(mapped_tcs) > 1:
            findings.append(finding(
                "test-case-scenario-duplicated",
                "traceability",
                "Сценарий матрицы покрыт несколькими тест-кейсами",
                f"{scenario_id}: {', '.join(mapped_tcs)}. Один SCN-* должен иметь ровно один TC.",
                artifact,
                remediation_owner="writer",
            ))
    expected_obligations = active_obligation_ids(obligations)
    unknown = sorted({obligation_id for obligation_id, _ in covered_obligation_contexts} - expected_obligations)
    if unknown:
        findings.append(finding("test-case-unknown-obligation", "traceability", "Тест-кейс ссылается на отсутствующее обязательство", ", ".join(unknown), artifact, remediation_owner="writer"))
    return findings


def matrix_review_required(obligations: dict[str, Any]) -> tuple[bool, list[str]]:
    entries = active_obligations(obligations)
    reasons: list[str] = [
        "Независимое matrix review обязательно для каждого нового scope до написания тест-кейсов."
    ]
    flags = {
        str(flag)
        for item in entries
        for flag in (item.get("risk_flags") if isinstance(item.get("risk_flags"), list) else [])
    }
    matched = sorted(flags & MATRIX_REVIEW_RISK_FLAGS)
    if matched:
        reasons.append("Риски scope: " + ", ".join(matched) + ".")
    return True, reasons


def validate_workflow_artifact_links(state: dict[str, Any], package_root: Path) -> list[ScopeFinding]:
    findings: list[ScopeFinding] = []
    artifact = "workflow-state.json"
    phase = str(state.get("phase") or "")
    required_by_phase = {
        "scope": ("source_package_manifest", "scope_obligations"),
        "matrix": ("source_package_manifest", "scope_obligations", "test_design_matrix"),
        "matrix-migration": ("source_package_manifest", "scope_obligations", "test_design_matrix"),
        "test-cases": ("source_package_manifest", "scope_obligations", "test_design_matrix"),
        "review": ("source_package_manifest", "scope_obligations", "test_design_matrix", "canonical_test_cases"),
        "accepted": ("source_package_manifest", "scope_obligations", "test_design_matrix", "canonical_test_cases"),
        "blocked": ("source_package_manifest", "scope_obligations"),
    }
    if phase not in required_by_phase:
        findings.append(finding("workflow-phase", "transport", "В workflow указан неизвестный этап", f"phase={phase!r}.", artifact, remediation_owner="controller", severity="warning"))
        return findings
    required_keys = list(required_by_phase[phase])
    if workflow_clarification_outcome_enabled(state):
        required_keys.append("scope_clarification_requests")
    try:
        obligations_path = workflow_artifact_path(
            state, package_root, "scope_obligations", required=True
        )
        assert obligations_path is not None
        obligations = read_json(obligations_path)
    except PracticalV09Error:
        obligations = {}
    if dictionary_inventory_required(obligations):
        required_keys.append("dictionary_inventory")
    if workflow_source_parity_enabled(state):
        try:
            manifest_path = workflow_artifact_path(
                state, package_root, "source_package_manifest", required=True
            )
            assert manifest_path is not None
            manifest = read_json(manifest_path)
        except PracticalV09Error:
            manifest = {}
        documents = manifest.get("documents") if isinstance(manifest, Mapping) else []
        has_pdf = isinstance(documents, list) and any(
            isinstance(item, Mapping) and item.get("role") == "pdf-cross-check"
            for item in documents
        )
        if has_pdf and phase in {"matrix", "matrix-migration", "test-cases", "review", "accepted", "blocked"}:
            required_keys.append("source_parity_check")
    for key in required_keys:
        try:
            path = workflow_artifact_path(state, package_root, key, required=True)
        except PracticalV09Error as exc:
            findings.append(finding("workflow-artifact-reference", "source-integrity", "В workflow отсутствует обязательная ссылка на артефакт", str(exc), artifact, remediation_owner="controller"))
            continue
        if path is not None and not path.is_file():
            findings.append(finding("workflow-artifact-missing", "source-integrity", "Workflow ссылается на отсутствующий артефакт", f"artifacts.{key}={relative_to_package(package_root, path)}.", artifact, remediation_owner="controller"))
    if dictionary_inventory_required(obligations):
        inventory_path = workflow_artifact_path(
            state, package_root, "dictionary_inventory", required=False
        )
        if inventory_path is not None and inventory_path.is_file():
            inventory_text = inventory_path.read_text(encoding="utf-8")
            if not inventory_text.strip():
                findings.append(finding(
                    "dictionary-inventory-empty",
                    "semantic-completeness",
                    "Inventory закрытого справочника пуст",
                    "Добавьте извлечённый DICT-* и полный состав значений или зафиксируйте source gap.",
                    relative_to_package(package_root, inventory_path),
                    remediation_owner="scope-analyzer",
                ))
    if "source_parity_check" in required_keys:
        parity_path = workflow_artifact_path(
            state, package_root, "source_parity_check", required=False
        )
        if parity_path is not None and parity_path.is_file():
            parity_text = parity_path.read_text(encoding="utf-8")
            if (
                "Сверка источников" not in parity_text
                or not parity_text.strip()
                or ("## Решение" not in parity_text and "## Decision" not in parity_text)
            ):
                findings.append(finding(
                    "source-parity-check-invalid",
                    "source-integrity",
                    "Сверка источников не содержит проверяемого результата",
                    "Файл source-parity-check.md должен содержать заголовок «Сверка источников» и раздел «Решение» с результатом сверки DOCX/PDF.",
                    relative_to_package(package_root, parity_path),
                    remediation_owner="scope-analyzer",
                ))
    findings.extend(validate_exception_snapshot_links(state, package_root))
    return findings


def validate_exception_snapshot_links(
    state: dict[str, Any], package_root: Path
) -> list[ScopeFinding]:
    """Validate snapshot evidence for every active narrow exception.

    A snapshot cannot retrospectively prove when a historical edit happened.
    It does, however, gives every new exception a fixed baseline for the
    reviewer, controller and later diff.  This guard deliberately applies only
    to new workflows that declare ``exception-snapshot-v1``.
    """
    if not workflow_exception_snapshot_enabled(state):
        return []

    findings: list[ScopeFinding] = []
    artifact = "workflow-state.json"
    artifacts = state.get("artifacts")
    if not isinstance(artifacts, Mapping):
        return findings
    for key, raw_path in artifacts.items():
        if not key.endswith("_exception") or raw_path in (None, "", "not-created", "not-applicable"):
            continue
        try:
            exception_path = package_relative_path(
                package_root, raw_path, artifact=f"artifacts.{key}"
            )
            payload = read_json(exception_path)
        except PracticalV09Error as exc:
            findings.append(finding(
                "exception-snapshot-reference-invalid",
                "review-integrity",
                "Исключение не связано с читаемым контрактом",
                str(exc), artifact, remediation_owner="controller",
            ))
            continue
        snapshot = payload.get("pre_change_snapshot") if isinstance(payload, Mapping) else None
        allowed = payload.get("allowed_artifacts") if isinstance(payload, Mapping) else None
        if not isinstance(snapshot, Mapping) or not isinstance(allowed, list) or not allowed:
            findings.append(finding(
                "exception-pre-change-snapshot-missing",
                "review-integrity",
                "Исключение не содержит immutable снимок до изменения",
                f"{relative_to_package(package_root, exception_path)} должен содержать pre_change_snapshot и непустой allowed_artifacts.",
                artifact, remediation_owner="controller",
            ))
            continue
        raw_snapshot_path = snapshot.get("path")
        expected_manifest_hash = snapshot.get("manifest_sha256")
        if not isinstance(raw_snapshot_path, str) or not isinstance(expected_manifest_hash, str):
            findings.append(finding(
                "exception-pre-change-snapshot-format",
                "review-integrity",
                "У snapshot исключения отсутствует путь или контрольная сумма",
                f"{relative_to_package(package_root, exception_path)}: нужны pre_change_snapshot.path и manifest_sha256.",
                artifact, remediation_owner="controller",
            ))
            continue
        try:
            snapshot_dir = package_relative_path(
                package_root, raw_snapshot_path, artifact=f"{key}.pre_change_snapshot"
            )
            manifest_path = snapshot_dir / "snapshot-manifest.yaml"
            snapshot_manifest = read_json(manifest_path)
        except PracticalV09Error as exc:
            findings.append(finding(
                "exception-pre-change-snapshot-invalid",
                "review-integrity",
                "Immutable снимок исключения отсутствует или повреждён",
                str(exc), artifact, remediation_owner="controller",
            ))
            continue
        if sha256_file(manifest_path) != expected_manifest_hash or snapshot_manifest.get("snapshot_role") != "pre_write_baseline":
            findings.append(finding(
                "exception-pre-change-snapshot-invalid",
                "review-integrity",
                "Immutable снимок исключения не подтверждает исходную версию",
                f"{relative_to_package(package_root, manifest_path)} должен иметь корректный SHA-256 и snapshot_role=pre_write_baseline.",
                artifact, remediation_owner="controller",
            ))
            continue
        records = [
            item
            for item in snapshot_manifest.get("source_files", [])
            if isinstance(item, Mapping)
        ]
        recorded = {item.get("source_path") for item in records if isinstance(item.get("source_path"), str)}
        invalid_allowed = [
            item for item in allowed
            if not isinstance(item, str) or item not in recorded
        ]
        if invalid_allowed:
            findings.append(finding(
                "exception-pre-change-snapshot-coverage",
                "review-integrity",
                "Immutable снимок исключения не покрывает разрешённые изменения",
                "В snapshot отсутствуют исходные версии: " + ", ".join(map(str, invalid_allowed)),
                artifact, remediation_owner="controller",
            ))
        for record in records:
            source_path = record.get("source_path")
            snapshot_path = record.get("snapshot_path")
            source_hash = record.get("source_sha256_before_write")
            snapshot_hash = record.get("snapshot_sha256")
            if not all(isinstance(value, str) and value for value in (source_path, snapshot_path, source_hash, snapshot_hash)):
                findings.append(finding(
                    "exception-pre-change-snapshot-invalid",
                    "review-integrity",
                    "Immutable снимок исключения содержит неполную запись файла",
                    f"{relative_to_package(package_root, manifest_path)}: у source_files отсутствуют путь или SHA-256.",
                    artifact, remediation_owner="controller",
                ))
                continue
            copied_path = (snapshot_dir / snapshot_path).resolve()
            if (
                not copied_path.is_file()
                or sha256_file(copied_path) != source_hash
                or sha256_file(copied_path) != snapshot_hash
            ):
                findings.append(finding(
                    "exception-pre-change-snapshot-invalid",
                    "review-integrity",
                    "Immutable снимок исключения не совпадает с зафиксированной исходной версией",
                    f"{relative_to_package(package_root, manifest_path)}: повреждён или отсутствует snapshot файла {source_path}.",
                    artifact, remediation_owner="controller",
                ))
    return findings


def dictionary_inventory_required(obligations: Mapping[str, Any]) -> bool:
    """Return whether active scope obligations require a closed-list inventory.

    A support-backed closed dictionary cannot be safely reviewed through an
    arbitrary pair of examples.  The inventory is a human-readable immutable
    input to the matrix and the independent reviewer, not a second source of
    requirements.
    """
    return any(
        "closed-dictionary" in (
            item.get("risk_flags") if isinstance(item.get("risk_flags"), list) else []
        )
        for item in active_obligations(obligations)
    )


def validate_review_history_integrity(
    state: dict[str, Any], package_root: Path
) -> list[ScopeFinding]:
    """Verify hashes recorded for immutable reviewer submissions.

    Older v0.9 review entries predate ``result_sha256`` and remain readable.
    Every newly finalized review records it, so a later edit or replacement of
    the preserved raw reviewer JSON becomes a scoped integrity blocker.
    """
    findings: list[ScopeFinding] = []
    reviews = state.get("reviews", [])
    if not isinstance(reviews, list):
        return findings
    for index, entry in enumerate(reviews, start=1):
        if not isinstance(entry, dict):
            continue
        expected_hash = entry.get("result_sha256")
        if expected_hash is None:
            continue
        artifact = "workflow-state.json"
        if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
            findings.append(finding(
                "workflow-review-result-hash-format",
                "review-integrity",
                "У записи независимого review неверный формат контрольной суммы",
                f"reviews[{index}].result_sha256 должен быть SHA-256 сохранённого raw JSON reviewer-а.",
                artifact,
                remediation_owner="controller",
            ))
            continue
        try:
            result_path = package_relative_path(
                package_root,
                entry.get("result"),
                artifact=artifact,
            )
        except PracticalV09Error as exc:
            findings.append(finding(
                "workflow-review-result-reference",
                "review-integrity",
                "Запись независимого review не содержит корректной ссылки на raw результат",
                str(exc),
                artifact,
                remediation_owner="controller",
            ))
            continue
        if not result_path.is_file():
            findings.append(finding(
                "workflow-review-result-missing",
                "review-integrity",
                "Сохранённый raw результат независимого review отсутствует",
                f"reviews[{index}].result={relative_to_package(package_root, result_path)}.",
                artifact,
                remediation_owner="controller",
            ))
            continue
        if sha256_file(result_path) != expected_hash:
            findings.append(finding(
                "workflow-review-result-drift",
                "artifact-tampering",
                "Сохранённый raw результат независимого review был изменён после финализации",
                f"reviews[{index}].result_sha256 не совпадает с {relative_to_package(package_root, result_path)}.",
                artifact,
                remediation_owner="controller",
            ))
            continue
        try:
            manifest_path = package_relative_path(
                package_root, entry.get("manifest"), artifact=artifact
            )
            manifest = read_json(manifest_path)
        except PracticalV09Error:
            continue
        requires_attestation = isinstance(
            manifest.get("review_session_attestation_required"), Mapping
        )
        attestation_ref = entry.get("session_attestation")
        attestation_hash = entry.get("session_attestation_sha256")
        if not requires_attestation and attestation_ref is None and attestation_hash is None:
            continue
        if (
            not isinstance(attestation_ref, str)
            or not attestation_ref.strip()
            or not isinstance(attestation_hash, str)
            or not re.fullmatch(r"[0-9a-f]{64}", attestation_hash)
        ):
            findings.append(finding(
                "workflow-review-session-attestation-reference",
                "review-integrity",
                "В history review отсутствует ссылка на подтверждение отдельной reviewer-сессии",
                f"reviews[{index}] должен хранить session_attestation и session_attestation_sha256.",
                artifact,
                remediation_owner="controller",
            ))
            continue
        try:
            attestation_path = package_relative_path(
                package_root, attestation_ref, artifact=artifact
            )
        except PracticalV09Error as exc:
            findings.append(finding(
                "workflow-review-session-attestation-reference",
                "review-integrity",
                "History review содержит некорректную ссылку на подтверждение reviewer-сессии",
                str(exc),
                artifact,
                remediation_owner="controller",
            ))
            continue
        if not attestation_path.is_file() or sha256_file(attestation_path) != attestation_hash:
            findings.append(finding(
                "workflow-review-session-attestation-drift",
                "artifact-tampering",
                "Сохранённое подтверждение отдельной reviewer-сессии отсутствует или изменено",
                f"reviews[{index}].session_attestation не совпадает с сохранённым SHA-256.",
                artifact,
                remediation_owner="controller",
            ))
            continue
        attestation = read_json(attestation_path)
        if (
            attestation.get("review_manifest_sha256") != sha256_file(manifest_path)
            or attestation.get("reviewer_thread_id") != read_json(result_path).get("reviewer_thread_id")
            or read_json(result_path).get("review_session_attestation_sha256")
            != attestation_hash
        ):
            findings.append(finding(
                "workflow-review-session-attestation-binding",
                "review-integrity",
                "History review не подтверждает связь manifest, reviewer-сессии и raw результата",
                f"reviews[{index}] должен связывать один immutable manifest, attestation и reviewer result.",
                artifact,
                remediation_owner="controller",
            ))
    return findings


def validate_review_triage_integrity(
    state: dict[str, Any], package_root: Path
) -> list[ScopeFinding]:
    """Validate controller decisions without changing immutable reviewer JSON."""
    if not workflow_controller_triage_enabled(state):
        return []
    findings: list[ScopeFinding] = []
    raw_triage = state.get("review_triage")
    assert isinstance(raw_triage, list)
    seen: set[tuple[str, str]] = set()
    valid_records: dict[tuple[str, str], dict[str, Any]] = {}
    for index, record in enumerate(raw_triage, start=1):
        artifact = "workflow-state.json"
        if not isinstance(record, dict):
            findings.append(finding(
                "workflow-review-triage-format",
                "review-integrity",
                "Запись controller triage имеет неверный формат",
                f"review_triage[{index}] должен быть объектом.",
                artifact,
                remediation_owner="controller",
            ))
            continue
        review_mode = record.get("review_mode")
        result_hash = record.get("review_result_sha256")
        raw_result_path = record.get("review_result")
        key = (str(review_mode), str(result_hash))
        if (
            review_mode not in {"matrix", "test-cases"}
            or not isinstance(result_hash, str)
            or not re.fullmatch(r"[0-9a-f]{64}", result_hash)
            or not isinstance(raw_result_path, str)
            or not raw_result_path
            or key in seen
        ):
            findings.append(finding(
                "workflow-review-triage-reference",
                "review-integrity",
                "Запись controller triage не связана однозначно с raw результатом review",
                f"review_triage[{index}] требует уникальные review_mode, review_result и review_result_sha256.",
                artifact,
                remediation_owner="controller",
            ))
            continue
        seen.add(key)
        try:
            result_path = package_relative_path(
                package_root, raw_result_path, artifact=artifact
            )
        except PracticalV09Error as exc:
            findings.append(finding(
                "workflow-review-triage-reference",
                "review-integrity",
                "У controller triage указан некорректный путь raw результата review",
                str(exc),
                artifact,
                remediation_owner="controller",
            ))
            continue
        if not result_path.is_file() or sha256_file(result_path) != result_hash:
            findings.append(finding(
                "workflow-review-triage-result-drift",
                "artifact-tampering",
                "Controller triage не связан с неизменённым raw результатом review",
                f"Не совпадает SHA-256 {raw_result_path}.",
                artifact,
                remediation_owner="controller",
            ))
            continue
        result = read_json(result_path)
        if result.get("review_mode") != review_mode or result.get("verdict") != "changes-required":
            findings.append(finding(
                "workflow-review-triage-result-mode",
                "review-integrity",
                "Controller triage допустим только для changes-required соответствующего режима review",
                f"review_triage[{index}] не соответствует raw результату.",
                artifact,
                remediation_owner="controller",
            ))
            continue
        content = review_content_findings(result)
        expected_ids = {str(item.get("id")) for item in content}
        findings_by_id = {str(item.get("id")): item for item in content}
        decisions = record.get("decisions")
        if not isinstance(decisions, list):
            findings.append(finding(
                "workflow-review-triage-decisions",
                "review-integrity",
                "Controller triage не содержит решений по blocking findings",
                f"review_triage[{index}].decisions должен быть массивом.",
                artifact,
                remediation_owner="controller",
            ))
            continue
        decision_by_id: dict[str, dict[str, Any]] = {}
        for decision in decisions:
            if not isinstance(decision, dict):
                continue
            identifier = decision.get("finding_id")
            if isinstance(identifier, str) and identifier not in decision_by_id:
                decision_by_id[identifier] = decision
        if set(decision_by_id) != expected_ids or len(decision_by_id) != len(decisions):
            findings.append(finding(
                "workflow-review-triage-coverage",
                "review-integrity",
                "Controller triage должен разобрать каждый и только каждый content blocking finding",
                f"Ожидались: {', '.join(sorted(expected_ids)) or 'нет'}; получены: {', '.join(sorted(decision_by_id)) or 'нет'}.",
                artifact,
                remediation_owner="controller",
            ))
            continue
        invalid = False
        for finding_id, decision in decision_by_id.items():
            anchors = decision.get("checked_anchors")
            if (
                decision.get("disposition") not in ALLOWED_TRIAGE_DISPOSITIONS
                or not isinstance(decision.get("rationale"), str)
                or len(decision["rationale"].strip()) < 16
                or not isinstance(anchors, list)
                or not anchors
                or not all(isinstance(anchor, str) and anchor.strip() for anchor in anchors)
            ):
                invalid = True
                break
            if decision["disposition"] == "rejected":
                rejection = decision.get("rejection")
                if (
                    not isinstance(rejection, dict)
                    or rejection.get("basis") not in ALLOWED_TRIAGE_REJECTION_BASES
                ):
                    invalid = True
                    break
                basis = rejection["basis"]
                if basis == "source-not-supported":
                    evidence = rejection.get("counter_evidence")
                    if (
                        not isinstance(evidence, list)
                        or not evidence
                        or not all(isinstance(item, str) and item.strip() for item in evidence)
                    ):
                        invalid = True
                        break
                elif basis == "duplicate-finding":
                    duplicate_of = rejection.get("duplicate_of")
                    if not isinstance(duplicate_of, str) or not duplicate_of.strip():
                        invalid = True
                        break
                else:
                    assertion = findings_by_id[finding_id].get("status_assertion")
                    if (
                        not isinstance(assertion, dict)
                        or assertion.get("required_status") not in ALLOWED_EXECUTION_STATUSES
                        or not isinstance(assertion.get("scenario_ids"), list)
                        or not assertion["scenario_ids"]
                    ):
                        invalid = True
                        break
        if invalid:
            findings.append(finding(
                "workflow-review-triage-decision",
                "review-integrity",
                "Решение controller triage неполно",
                "Каждое решение требует disposition, развёрнутый rationale и checked_anchors; отклонение также требует допустимый rejection.basis.",
                artifact,
                remediation_owner="controller",
            ))
            continue
        valid_records[key] = record

    for review in state.get("reviews", []):
        if not isinstance(review, dict) or review.get("effective_verdict") is None:
            continue
        if review.get("verdict") != "changes-required" or review.get("effective_verdict") != "approved":
            findings.append(finding(
                "workflow-review-triage-effective-verdict",
                "review-integrity",
                "Effective verdict controller triage указан недопустимо",
                "Только changes-required может получить effective_verdict=approved после отклонения всех content blocking findings.",
                "workflow-state.json",
                remediation_owner="controller",
            ))
            continue
        key = (str(review.get("mode")), str(review.get("result_sha256")))
        record = valid_records.get(key)
        if record is None or any(
            decision.get("disposition") != "rejected"
            for decision in record.get("decisions", [])
            if isinstance(decision, dict)
        ):
            findings.append(finding(
                "workflow-review-triage-effective-verdict",
                "review-integrity",
                "Effective verdict не подтверждён controller triage",
                "Для перехода по effective_verdict=approved все content blocking findings должны быть документированно отклонены.",
                "workflow-state.json",
                remediation_owner="controller",
            ))
    return findings


def validate_pending_triage_finalization(
    state: dict[str, Any], package_root: Path
) -> list[ScopeFinding]:
    """Block a writer revision that races ahead of raw-review finalization.

    A controller triage is a decision about one immutable review result, not a
    permission to change the reviewed matrix or TC. The raw verdict must be
    recorded in ``reviews`` before its accepted finding consumes a revision
    budget. Review history itself may legitimately describe an older snapshot
    after the permitted writer revision, so only unfinished triage is checked.
    """
    if not workflow_controller_triage_enabled(state):
        return []
    finalized = {
        (str(item.get("mode")), str(item.get("result_sha256")))
        for item in state.get("reviews", [])
        if isinstance(item, dict)
    }
    findings: list[ScopeFinding] = []
    raw_triage = state.get("review_triage")
    assert isinstance(raw_triage, list)
    for index, record in enumerate(raw_triage, start=1):
        if not isinstance(record, dict):
            continue
        key = (str(record.get("review_mode")), str(record.get("review_result_sha256")))
        if key in finalized:
            continue
        artifact = "workflow-state.json"
        manifest_ref = record.get("review_manifest")
        if not isinstance(manifest_ref, str) or not manifest_ref.strip():
            findings.append(finding(
                "workflow-triage-finalization-reference",
                "review-integrity",
                "После triage отсутствует ссылка на immutable manifest до финализации review",
                f"review_triage[{index}] не содержит review_manifest; нельзя доказать неизменность review-входов до расходования revision budget.",
                artifact,
                remediation_owner="controller",
                blocking=True,
                blocking_reason="triage-finalization-reference-missing",
            ))
            continue
        try:
            manifest_path = package_relative_path(
                package_root, manifest_ref, artifact=artifact
            )
        except PracticalV09Error as exc:
            findings.append(finding(
                "workflow-triage-finalization-reference",
                "review-integrity",
                "После triage указана некорректная ссылка на immutable manifest",
                str(exc),
                artifact,
                remediation_owner="controller",
                blocking=True,
                blocking_reason="triage-finalization-reference-invalid",
            ))
            continue
        if (
            not manifest_path.is_file()
            or sha256_file(manifest_path) != record.get("review_manifest_sha256")
        ):
            findings.append(finding(
                "workflow-triage-finalization-manifest-drift",
                "artifact-tampering",
                "Immutable manifest triage был изменён или отсутствует до финализации review",
                f"review_triage[{index}].review_manifest не совпадает с review_manifest_sha256.",
                artifact,
                remediation_owner="controller",
                blocking=True,
                blocking_reason="triage-finalization-manifest-drift",
            ))
            continue
        manifest = read_json(manifest_path)
        changed: list[str] = []
        for entry in manifest.get("inputs", []):
            if not isinstance(entry, dict):
                continue
            try:
                path = package_relative_path(
                    package_root, entry.get("path"), artifact=manifest_ref
                )
            except PracticalV09Error:
                changed.append(str(entry.get("path") or "<некорректный путь>"))
                continue
            if not path.is_file() or sha256_file(path) != entry.get("sha256"):
                changed.append(str(entry.get("path") or "<неизвестный вход>"))
        if changed:
            findings.append(finding(
                "workflow-triage-finalization-required",
                "review-integrity",
                "После controller triage изменены входы review до его финализации",
                "Сначала финализируйте raw verdict неизменённого review через finalize_practical_review.py; "
                "writer revision допускается только после записи verdict и расходования принятого budget. "
                f"Изменены входы: {', '.join(changed)}.",
                artifact,
                remediation_owner="controller",
                blocking=True,
                blocking_reason="triage-finalization-required",
            ))
    return findings


def approved_review_exists(state: dict[str, Any], review_mode: str) -> bool:
    """Return whether the state records raw or triaged acceptance for a mode."""
    return any(
        isinstance(entry, dict)
        and entry.get("mode") == review_mode
        and (
            entry.get("verdict") == "approved"
            or (
                entry.get("verdict") == "changes-required"
                and entry.get("effective_verdict") == "approved"
            )
        )
        for entry in state.get("reviews", [])
    )


def validate_scope(
    *, package_root: Path, workflow_state_path: Path, include_test_cases: bool | None = None
) -> tuple[dict[str, Any], list[ScopeFinding]]:
    package_root = package_root.resolve()
    state = load_workflow_state(workflow_state_path, package_root)
    findings = validate_workflow_artifact_links(state, package_root)
    findings.extend(validate_review_history_integrity(state, package_root))
    findings.extend(validate_review_triage_integrity(state, package_root))
    findings.extend(validate_pending_triage_finalization(state, package_root))
    source_path = workflow_artifact_path(state, package_root, "source_package_manifest", required=True)
    obligations_path = workflow_artifact_path(state, package_root, "scope_obligations", required=True)
    assert source_path is not None and obligations_path is not None
    source_findings, _ = validate_source_package_manifest(source_path, package_root)
    findings.extend(source_findings)
    obligation_findings, obligations = validate_scope_obligations(
        obligations_path,
        package_root,
        source_path,
    )
    findings.extend(obligation_findings)
    if dictionary_inventory_required(obligations):
        dictionary_path = workflow_artifact_path(
            state, package_root, "dictionary_inventory", required=False
        )
        if dictionary_path is None:
            findings.append(finding(
                "dictionary-inventory-reference-missing",
                "source-integrity",
                "Для закрытого справочника не указан inventory",
                "Активные OBL-* с risk_flags=closed-dictionary требуют artifacts.dictionary_inventory.",
                "workflow-state.json",
                remediation_owner="scope-analyzer",
            ))
        elif not dictionary_path.is_file():
            findings.append(finding(
                "dictionary-inventory-missing",
                "source-integrity",
                "Для закрытого справочника отсутствует inventory",
                relative_to_package(package_root, dictionary_path),
                "workflow-state.json",
                remediation_owner="scope-analyzer",
            ))
    try:
        provided_fixture_inputs = provided_setup_artifacts(obligations, package_root)
    except PracticalV09Error as exc:
        findings.append(finding(
            "scope-provided-fixture-artifacts-unavailable",
            "execution-readiness",
            "Не удалось получить неизменяемые файлы предоставленного fixture",
            str(exc),
            relative_to_package(package_root, obligations_path),
            remediation_owner="scope-analyzer",
        ))
        provided_fixture_inputs = []

    migration = workflow_contract_migration(state)
    migration_status = str(migration.get("status")) if migration else ""
    migration_active = migration_status == "active"
    migration_tc_sync_required = bool(
        migration
        and migration.get("canonical_tc_sync_required")
        and migration_status in {"matrix-accepted", "completed"}
    )
    if migration_active:
        findings.append(finding(
            "contract-migration-active",
            "transport",
            "Scope ожидает завершения явной миграции контракта матрицы",
            f"До создания матрицы в новом контракте {MATRIX_CONTRACT_VERSION} нельзя валидировать или ревьюить прежние matrix/TC. "
            "Бюджеты matrix_revision_count и tc_revision_count при миграции не сбрасываются.",
            "workflow-state.json",
            remediation_owner="controller",
            blocking=True,
            blocking_reason="contract-migration-active",
        ))

    matrix_path = workflow_artifact_path(state, package_root, "test_design_matrix")
    matrix_by_scenario: dict[str, dict[str, str]] = {}
    if matrix_path is not None:
        if migration_active:
            pass
        elif matrix_path.is_file():
            expected_matrix_contract = workflow_matrix_contract_version(state)
            actual_matrix_contract = matrix_contract_version_from_path(matrix_path)
            if actual_matrix_contract != expected_matrix_contract:
                findings.append(finding(
                    "matrix-contract-schema-mismatch",
                    "transport",
                    "Схема матрицы не соответствует версии контракта workflow",
                    f"Workflow ожидает {expected_matrix_contract}, а таблица имеет "
                    f"{actual_matrix_contract or 'неизвестную'} схему. Требуется явная миграция контракта, а не частичная правка.",
                    relative_to_package(package_root, matrix_path),
                    remediation_owner="controller",
                    blocking=True,
                    blocking_reason="matrix-contract-schema-mismatch",
                ))
            elif expected_matrix_contract != MATRIX_CONTRACT_VERSION:
                findings.append(finding(
                    "matrix-contract-migration-required",
                    "transport",
                    "Активный scope использует устаревший контракт матрицы",
                    "Для перехода к текущему practical route выполните явную миграцию контракта со snapshot и явным разрешением пользователя.",
                    "workflow-state.json",
                    remediation_owner="controller",
                    blocking=True,
                    blocking_reason="matrix-contract-migration-required",
                ))
            else:
                matrix_findings, matrix_by_scenario, _matrix_by_obligation_context = validate_matrix(
                    matrix_path, package_root, obligations, state
                )
                findings.extend(matrix_findings)
        else:
            findings.append(finding("matrix-missing", "source-integrity", "Матрица тест-дизайна отсутствует", relative_to_package(package_root, matrix_path), "workflow-state.json", remediation_owner="writer"))

    tc_path = workflow_artifact_path(state, package_root, "canonical_test_cases")
    phase_requires_tc = str(state.get("phase") or "") in {"review", "accepted"}
    need_tc = include_test_cases if include_test_cases is not None else (phase_requires_tc or tc_path is not None)
    if migration_tc_sync_required:
        findings.append(finding(
            "contract-migration-tc-sync-required",
            "transport",
            "Канонические ТК требуют синхронизации с матрицей после миграции",
            "Матрица уже принята после миграции, но прежние TC нельзя использовать до отдельной проверяемой синхронизации с новым SCN-контрактом.",
            "workflow-state.json",
            remediation_owner="writer",
            blocking=True,
            blocking_reason="contract-migration-tc-sync-required",
        ))
    elif migration is not None and migration_status in {"active", "matrix-ready", "matrix-accepted"}:
        # Old TC are snapshot-preserved during a matrix-contract migration.  A
        # structural matrix review must not accidentally treat them as current
        # proof before the explicit synchronization transition.
        pass
    elif need_tc:
        if tc_path is None:
            findings.append(finding("test-cases-reference-missing", "traceability", "В workflow не указан файл тест-кейсов", "Для этапа тест-кейсов нужна artifacts.canonical_test_cases.", "workflow-state.json", remediation_owner="writer"))
        elif tc_path.is_file():
            findings.extend(validate_test_cases(
                tc_path,
                package_root,
                obligations,
                matrix_by_scenario,
                state,
                matrix_path,
                obligations_path.parent / "fixtures",
            ))
        else:
            findings.append(finding("test-cases-missing", "source-integrity", "Файл тест-кейсов отсутствует", relative_to_package(package_root, tc_path), "workflow-state.json", remediation_owner="writer"))

    matrix_required, matrix_reasons = matrix_review_required(obligations)
    consolidation_decisions: list[dict[str, Any]] = []
    if matrix_consolidation_enabled(state=state, matrix_path=matrix_path):
        if matrix_consolidation_enabled(state=None, matrix_path=matrix_path):
            consolidation_decisions, _consolidation_errors = (
                parse_matrix_consolidation_decisions(matrix_path)
            )
        else:
            consolidation_decisions = state.get("scenario_consolidation", [])
    if consolidation_decisions:
        matrix_required = True
        matrix_reasons = [
            *matrix_reasons,
            "в matrix есть решение CON-*, требующее независимой проверки",
        ]
    declared = state.get("matrix_review_required")
    if declared is not None and bool(declared) != matrix_required:
        findings.append(finding("matrix-review-decision-stale", "transport", "Workflow содержит устаревшее решение о matrix review", "; ".join(matrix_reasons) or "Scope не достигает порога обязательного matrix review.", "workflow-state.json", remediation_owner="controller", severity="warning"))

    phase = str(state.get("phase") or "")
    if not migration_active and matrix_required and phase in {"test-cases", "review", "accepted"} and not approved_review_exists(state, "matrix"):
        findings.append(finding(
            "matrix-review-required-before-test-cases",
            "review-integrity",
            "Перед написанием тест-кейсов не подтверждено обязательное review матрицы",
            "Для данного scope matrix review обязательно по complexity rule; в workflow-state.json нет approved результата независимого matrix review.",
            "workflow-state.json",
            remediation_owner="controller",
        ))
    if phase == "accepted" and not approved_review_exists(state, "test-cases"):
        findings.append(finding(
            "test-cases-review-required-before-acceptance",
            "review-integrity",
            "Scope принят без обязательного независимого review тест-кейсов",
            "В workflow-state.json отсутствует approved результат final TC review из отдельной Codex-сессии.",
            "workflow-state.json",
            remediation_owner="controller",
        ))
    if phase == "test-cases" and tc_path is not None and tc_path.is_file():
        findings.append(finding(
            "workflow-phase-stale-after-tc-write",
            "transport",
            "Workflow не переведён к финальному review после записи тест-кейсов",
            "После создания canonical test cases установите phase=review и следующим действием укажите независимое final TC review.",
            "workflow-state.json",
            remediation_owner="controller",
            severity="warning",
        ))
    if phase == "review" and state.get("final_verdict") != "not-finalized":
        findings.append(finding(
            "workflow-final-verdict-stale",
            "transport",
            "До final TC review указан устаревший финальный вердикт",
            "В phase=review поле final_verdict должно быть not-finalized; результат matrix review хранится в reviews.",
            "workflow-state.json",
            remediation_owner="controller",
            severity="warning",
        ))

    content_input_keys = [
        "source_package_manifest",
        "scope_obligations",
        "test_design_matrix",
        "canonical_test_cases",
    ]
    if workflow_clarification_outcome_enabled(state):
        content_input_keys.append("scope_clarification_requests")
    if dictionary_inventory_required(obligations):
        content_input_keys.append("dictionary_inventory")
    content_input_hashes = {
        key: sha256_file(path)
        for key in content_input_keys
        for path in [workflow_artifact_path(state, package_root, key)]
        if path is not None and path.is_file()
    }
    content_input_hashes.update(
        {
            "provided_setup_artifact:" + relative_to_package(package_root, path): sha256_file(path)
            for _role, path in provided_fixture_inputs
        }
    )
    report_context = {
        "route_version": ROUTE_VERSION,
        "tool_version": ROUTE_TOOL_VERSION,
        "scope_id": state["scope_id"],
        "scope_slug": state["scope_slug"],
        "phase": state["phase"],
        "matrix_contract_version": workflow_matrix_contract_version(state),
        "contract_migration_status": migration_status or "not-required",
        "matrix_review_required": matrix_required,
        "matrix_review_reasons": matrix_reasons,
        "content_input_hashes": content_input_hashes,
        "input_hashes": {
            "workflow_state": sha256_file(workflow_state_path),
            **content_input_hashes,
        },
    }
    return report_context, findings


def build_validator_report(context: dict[str, Any], findings: Iterable[ScopeFinding]) -> dict[str, Any]:
    rendered_findings = [item.as_dict() for item in findings]
    blocking_count = sum(1 for item in rendered_findings if item["blocking"])
    return {
        "schema_version": 1,
        "validator_contract_version": VALIDATOR_REPORT_VERSION,
        **context,
        "summary": {
            "findings_count": len(rendered_findings),
            "blocking_count": blocking_count,
            "warnings_count": sum(1 for item in rendered_findings if item["severity"] == "warning"),
            "clean": blocking_count == 0,
        },
        "findings": rendered_findings,
    }


def review_subject_paths(state: dict[str, Any], package_root: Path, review_mode: str) -> dict[str, Path]:
    if review_mode not in {"matrix", "test-cases"}:
        raise PracticalV09Error("review_mode must be matrix or test-cases")
    keys = ["source_package_manifest", "scope_obligations", "test_design_matrix"]
    if workflow_clarification_outcome_enabled(state):
        keys.append("scope_clarification_requests")
    if workflow_source_parity_enabled(state):
        manifest_path = workflow_artifact_path(
            state, package_root, "source_package_manifest", required=True
        )
        assert manifest_path is not None
        manifest = read_json(manifest_path)
        documents = manifest.get("documents") if isinstance(manifest, Mapping) else []
        if isinstance(documents, list) and any(
            isinstance(item, Mapping) and item.get("role") == "pdf-cross-check"
            for item in documents
        ):
            keys.append("source_parity_check")
    if workflow_exception_snapshot_enabled(state):
        artifacts = state.get("artifacts")
        if isinstance(artifacts, Mapping):
            keys.extend(
                key
                for key, value in artifacts.items()
                if key.endswith("_exception") and value not in (None, "", "not-created", "not-applicable")
            )
    obligations_path = workflow_artifact_path(
        state, package_root, "scope_obligations", required=True
    )
    assert obligations_path is not None
    if dictionary_inventory_required(read_json(obligations_path)):
        keys.append("dictionary_inventory")
    if review_mode == "test-cases":
        keys.append("canonical_test_cases")
    paths: dict[str, Path] = {}
    for key in keys:
        path = workflow_artifact_path(state, package_root, key, required=True)
        assert path is not None
        if not path.is_file():
            raise PracticalV09Error(f"Review input is missing: {relative_to_package(package_root, path)}")
        paths[key] = path
    return paths


def exception_snapshot_review_inputs(
    state: dict[str, Any], package_root: Path
) -> list[tuple[str, Path]]:
    """Return exception evidence a reviewer needs to verify a bounded edit.

    Binding only the exception JSON would force the reviewer to trust its
    ``pre_change_snapshot`` claim.  The manifest and copied pre-change bytes
    are therefore explicit immutable review inputs.  Validation has already
    checked their hashes before this helper is called.
    """
    if not workflow_exception_snapshot_enabled(state):
        return []
    artifacts = state.get("artifacts")
    if not isinstance(artifacts, Mapping):
        return []
    bound: list[tuple[str, Path]] = []
    for key, raw_path in artifacts.items():
        if not key.endswith("_exception") or raw_path in (None, "", "not-created", "not-applicable"):
            continue
        exception_path = package_relative_path(
            package_root, raw_path, artifact=f"artifacts.{key}"
        )
        payload = read_json(exception_path)
        snapshot = payload.get("pre_change_snapshot") if isinstance(payload, Mapping) else None
        if not isinstance(snapshot, Mapping):
            continue
        snapshot_dir = package_relative_path(
            package_root,
            snapshot.get("path"),
            artifact=f"{key}.pre_change_snapshot",
        )
        snapshot_manifest = snapshot_dir / "snapshot-manifest.yaml"
        if not snapshot_manifest.is_file():
            continue
        bound.append((f"{key}-snapshot-manifest", snapshot_manifest))
        manifest = read_json(snapshot_manifest)
        for index, record in enumerate(manifest.get("source_files", []), start=1):
            if not isinstance(record, Mapping):
                continue
            raw_snapshot_path = record.get("snapshot_path")
            if not isinstance(raw_snapshot_path, str) or not raw_snapshot_path:
                continue
            copied = (snapshot_dir / raw_snapshot_path).resolve()
            if copied.is_file() and copied.is_relative_to(snapshot_dir.resolve()):
                bound.append((f"{key}-snapshot-file-{index}", copied))
    return bound


def source_bound_review_inputs(
    *, source_manifest_path: Path, package_root: Path
) -> list[tuple[str, Path]]:
    """Return all source-package inputs required for a source-qualified review.

    The source-package manifest is itself an audit record, not a substitute for
    its DOCX/XHTML/PDF, support and visual inputs.  A separate reviewer must
    receive those files in the immutable snapshot to reconstruct obligations
    independently.  The source manifest has already passed validation before
    this function is called; the defensive path checks below make an invalid
    transport fail closed rather than producing a partial review snapshot.
    """
    manifest = read_json(source_manifest_path)
    bound: list[tuple[str, Path]] = []
    seen_paths: set[str] = set()

    def add(role: str, raw_path: object) -> None:
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise PracticalV09Error(
                f"source-package manifest review input {role} has no path"
            )
        path = package_relative_path(
            package_root, raw_path, artifact="source-package manifest"
        )
        if not path.is_file():
            raise PracticalV09Error(
                "Source-qualified review input is missing: "
                + relative_to_package(package_root, path)
            )
        relative = relative_to_package(package_root, path)
        if relative in seen_paths:
            return
        seen_paths.add(relative)
        bound.append((role, path))

    documents = manifest.get("documents")
    if not isinstance(documents, list):
        raise PracticalV09Error("source-package manifest documents must be an array")
    for index, entry in enumerate(documents, start=1):
        if not isinstance(entry, dict):
            raise PracticalV09Error(
                f"source-package manifest documents[{index}] must be an object"
            )
        add(f"source-document-{entry.get('role') or index}", entry.get("path"))

    for field, role_prefix in (
        ("support_inputs", "source-support"),
        ("visual_inputs", "source-visual"),
        ("approved_ba_decisions", "source-ba-decision"),
    ):
        entries = manifest.get(field, [])
        if not isinstance(entries, list):
            raise PracticalV09Error(
                f"source-package manifest {field} must be an array"
            )
        for index, entry in enumerate(entries, start=1):
            if not isinstance(entry, dict):
                raise PracticalV09Error(
                    f"source-package manifest {field}[{index}] must be an object"
                )
            add(f"{role_prefix}-{entry.get('role') or index}", entry.get("path"))

    notes = manifest.get("agent_notes")
    if isinstance(notes, dict):
        add("source-agent-notes", notes.get("path"))
    return bound


def require_current_validator_report(
    *,
    state: dict[str, Any],
    package_root: Path,
    context: dict[str, Any],
) -> tuple[Path, dict[str, Any]]:
    """Load the persisted scoped validation for exactly the frozen review inputs.

    `build_review_manifest` performs a defensive in-memory validation as well,
    but that is not a replacement for the canonical `validator-report.json`.
    Requiring the persisted report prevents a revision from being reviewed with
    an old report whose hashes describe an earlier matrix or obligations set.
    """
    report_path = workflow_artifact_path(
        state, package_root, "validator_report", required=True
    )
    assert report_path is not None
    if not report_path.is_file():
        raise PracticalV09Error(
            "Current scoped validator report is required before independent review: "
            + relative_to_package(package_root, report_path)
        )
    report = read_json(report_path)
    if report.get("route_version") != ROUTE_VERSION:
        raise PracticalV09Error("validator-report.json belongs to another route version")
    if report.get("tool_version") != ROUTE_TOOL_VERSION:
        raise PracticalV09Error("validator-report.json was created by another tool version")
    if report.get("validator_contract_version") != VALIDATOR_REPORT_VERSION:
        raise PracticalV09Error("validator-report.json has an unsupported validator contract")
    if report.get("scope_id") != state["scope_id"] or report.get("scope_slug") != state["scope_slug"]:
        raise PracticalV09Error("validator-report.json belongs to another scope")
    if report.get("phase") != state["phase"]:
        raise PracticalV09Error("validator-report.json does not describe the current workflow phase")
    if report.get("content_input_hashes") != context["content_input_hashes"]:
        raise PracticalV09Error(
            "validator-report.json is stale for the current scope inputs; "
            "run validate_practical_scope.py again before independent review"
        )
    summary = report.get("summary")
    if not isinstance(summary, dict) or summary.get("clean") is not True:
        raise PracticalV09Error("validator-report.json is not clean for independent review")
    return report_path, report


def build_review_manifest(
    *,
    package_root: Path,
    workflow_state_path: Path,
    review_mode: str,
    controller_thread_id: str,
    code_branch: str,
    code_commit: str,
    contract_digest: str,
    ft_package_path: str = ".",
    repo_root_path: str | None = None,
    require_session_attestation: bool = False,
) -> dict[str, Any]:
    state = load_workflow_state(workflow_state_path, package_root)
    if not is_durable_codex_thread_id(controller_thread_id):
        raise PracticalV09Error("controller_thread_id must be a durable Codex thread UUID")
    normalized_repo_root = Path(repo_root_path).resolve() if repo_root_path else package_root.resolve()
    normalized_package_root = package_root.resolve()
    try:
        derived_package_path = normalized_package_root.relative_to(normalized_repo_root).as_posix()
    except ValueError as exc:
        raise PracticalV09Error("package_root must be inside repo_root_path") from exc
    normalized_package_path = Path(ft_package_path)
    if normalized_package_path.is_absolute() or ".." in normalized_package_path.parts:
        raise PracticalV09Error("ft_package_path must be a relative path inside the code repository")
    if normalized_package_path.as_posix() != derived_package_path:
        raise PracticalV09Error(
            "ft_package_path must exactly match the normalized package path relative to repo_root_path"
        )
    if require_session_attestation and repo_root_path is None:
        raise PracticalV09Error(
            "repo_root_path is required when an independent reviewer-session attestation is required"
        )
    context, findings = validate_scope(package_root=package_root, workflow_state_path=workflow_state_path)
    blocking = [item for item in findings if item.blocking]
    if blocking:
        raise PracticalV09Error("Cannot create review manifest while scope has blocking findings: " + ", ".join(item.id for item in blocking))
    validator_report_path, validator_report = require_current_validator_report(
        state=state,
        package_root=package_root,
        context=context,
    )
    paths = review_subject_paths(state, package_root, review_mode)
    source_inputs = source_bound_review_inputs(
        source_manifest_path=paths["source_package_manifest"],
        package_root=package_root,
    )
    provided_inputs = provided_setup_artifacts(
        read_json(paths["scope_obligations"]), package_root
    )
    exception_inputs = exception_snapshot_review_inputs(state, package_root)
    manifest_inputs: list[dict[str, str]] = []
    bound_paths: set[str] = set()

    def bind(role: str, path: Path) -> None:
        relative = relative_to_package(package_root, path)
        if relative in bound_paths:
            return
        bound_paths.add(relative)
        manifest_inputs.append(
            {"role": role, "path": relative, "sha256": sha256_file(path)}
        )

    for key, path in paths.items():
        bind(key, path)
    for role, path in source_inputs:
        bind(role, path)
    for role, path in provided_inputs:
        bind(role, path)
    for role, path in exception_inputs:
        bind(role, path)
    manifest = {
        "schema_version": 1,
        "manifest_version": REVIEW_MANIFEST_VERSION,
        "route_version": ROUTE_VERSION,
        "tool_version": ROUTE_TOOL_VERSION,
        "scope_id": state["scope_id"],
        "scope_slug": state["scope_slug"],
        "review_mode": review_mode,
        "controller_thread_id": controller_thread_id,
        "execution_surface_required": "codex-thread",
        "repo_root": str(normalized_repo_root),
        "ft_package_root": str(normalized_package_root),
        "ft_package_path": derived_package_path,
        "code_branch": code_branch,
        "code_commit": code_commit,
        "contract_digest": contract_digest,
        "validator_report_sha256": sha256_file(validator_report_path),
        "validator_report_digest": sha256_json(validator_report),
        "inputs": manifest_inputs,
        "reviewer_order": [
            "Самостоятельно восстановить обязательства из исходных материалов.",
            "Сопоставить обязательства с матрицей тест-дизайна.",
            "Проверить тест-кейсы, если review_mode=test-cases.",
        ],
    }
    if require_session_attestation:
        manifest["review_session_attestation_required"] = {
            "version": REVIEW_SESSION_ATTESTATION_VERSION,
            "owner": "controller",
            "execution_surface": "codex-thread",
        }
    matrix_path = paths.get("test_design_matrix")
    if review_mode == "matrix" and matrix_consolidation_enabled(
        state=state, matrix_path=matrix_path
    ):
        matrix_owns_consolidation = matrix_consolidation_enabled(
            state=None, matrix_path=matrix_path
        )
        if matrix_owns_consolidation:
            consolidation_decisions, consolidation_errors = (
                parse_matrix_consolidation_decisions(matrix_path)
            )
            if consolidation_errors:
                raise PracticalV09Error(
                    "Cannot create matrix review manifest: "
                    + "; ".join(consolidation_errors)
                )
        else:
            consolidation_decisions = state.get("scenario_consolidation", [])
        if consolidation_decisions:
            manifest["scenario_consolidation_contract"] = {
                "version": SCENARIO_CONSOLIDATION_CONTRACT_VERSION,
                "decisions": consolidation_decisions,
                "owner": "test-design-matrix" if matrix_owns_consolidation else "legacy-workflow-state",
            }
            manifest["reviewer_order"].append(
                "Самостоятельно проверить решения CON-* в matrix и неучтённые кандидаты на объединение."
            )
    if workflow_controller_triage_enabled(state):
        manifest["controller_triage_contract"] = {
            "version": CONTROLLER_TRIAGE_CONTRACT_VERSION,
            "finding_schema": "practical-review-finding-v1",
            "required_for": "changes-required-with-content-blockers",
        }
    obligations_path = paths["scope_obligations"]
    active_ids = active_obligation_ids(read_json(obligations_path))
    if len(active_ids) > COMPACT_REVIEWER_RECEIPT_OBLIGATION_THRESHOLD:
        manifest["reviewer_receipt_contract"] = {
            "format": COMPACT_REVIEWER_RECEIPT_FORMAT,
            "max_bytes": COMPACT_REVIEWER_RECEIPT_MAX_BYTES,
            "scope_obligations_sha256": sha256_file(obligations_path),
            "active_obligation_count": len(active_ids),
            "active_obligation_ids_sha256": obligation_ids_sha256(active_ids),
            "obligation_ids": sorted(active_ids),
        }
    return manifest


def build_review_session_attestation(
    *,
    package_root: Path,
    manifest_path: Path,
    reviewer_thread_id: str,
) -> dict[str, Any]:
    """Build the controller-owned binding for an already created reviewer task.

    The desktop task API is the source of the reviewer thread ID.  A local
    validator cannot create or cryptographically attest that task itself, so
    it fails closed unless the controller records the returned ID in this
    immutable, manifest-bound artifact before reviewer finalization.
    """
    manifest = read_json(manifest_path)
    required = manifest.get("review_session_attestation_required")
    if not isinstance(required, Mapping) or required.get("version") != REVIEW_SESSION_ATTESTATION_VERSION:
        raise PracticalV09Error("review manifest does not require a current controller session attestation")
    controller_thread_id = str(manifest.get("controller_thread_id") or "")
    if (
        not is_durable_codex_thread_id(reviewer_thread_id)
        or not is_durable_codex_thread_id(controller_thread_id)
        or reviewer_thread_id == controller_thread_id
    ):
        raise PracticalV09Error("reviewer_thread_id must be a distinct durable Codex thread UUID")
    try:
        repo_root = Path(str(manifest.get("repo_root") or "")).resolve()
        manifest_package_root = Path(str(manifest.get("ft_package_root") or "")).resolve()
        expected_relative = manifest_package_root.relative_to(repo_root).as_posix()
    except (TypeError, ValueError) as exc:
        raise PracticalV09Error("review manifest has invalid normalized repository roots") from exc
    if (
        manifest_package_root != package_root.resolve()
        or manifest.get("ft_package_path") != expected_relative
    ):
        raise PracticalV09Error(
            "review manifest roots do not match the current FT package root"
        )
    return {
        "schema_version": 1,
        "attestation_version": REVIEW_SESSION_ATTESTATION_VERSION,
        "recorded_by": "controller",
        "execution_surface": "codex-thread",
        "review_manifest": relative_to_package(package_root, manifest_path),
        "review_manifest_sha256": sha256_file(manifest_path),
        "controller_thread_id": controller_thread_id,
        "reviewer_thread_id": reviewer_thread_id,
        "code_commit": manifest.get("code_commit"),
        "repo_root": manifest.get("repo_root"),
        "ft_package_root": manifest.get("ft_package_root"),
        "ft_package_path": manifest.get("ft_package_path"),
    }


def verify_review_result(
    *, package_root: Path,
    manifest_path: Path,
    result_path: Path,
    review_session_attestation_path: Path | None = None,
) -> tuple[dict[str, Any], list[ScopeFinding]]:
    manifest = read_json(manifest_path)
    result = read_json(result_path)
    artifact = relative_to_package(package_root, result_path)
    findings: list[ScopeFinding] = []
    try:
        manifest_repo_root = Path(str(manifest.get("repo_root") or "")).resolve()
        manifest_package_root = Path(str(manifest.get("ft_package_root") or "")).resolve()
        expected_package_path = manifest_package_root.relative_to(manifest_repo_root).as_posix()
        manifest_roots_valid = (
            manifest_package_root == package_root.resolve()
            and manifest.get("ft_package_path") == expected_package_path
        )
    except (TypeError, ValueError):
        manifest_roots_valid = False
    if not manifest_roots_valid:
        findings.append(finding(
            "review-manifest-roots",
            "review-integrity",
            "Manifest review не содержит корректные нормализованные roots репозитория и FT-пакета",
            "repo_root и ft_package_root должны быть абсолютными нормализованными путями; ft_package_path должен быть их корректным относительным путём.",
            artifact,
            remediation_owner="controller",
        ))
    if has_suspicious_mojibake(result):
        findings.append(finding(
            "review-result-mojibake",
            "review-integrity",
            "В результате review обнаружен повреждённый текст",
            "JSON должен содержать читаемый UTF-8 текст; исправьте кодировку без изменения review snapshot.",
            artifact,
            remediation_owner="reviewer",
        ))
    if manifest.get("manifest_version") != REVIEW_MANIFEST_VERSION:
        findings.append(finding("review-manifest-version", "review-integrity", "У manifest review неверная версия контракта", f"Ожидается {REVIEW_MANIFEST_VERSION}.", artifact, remediation_owner="controller"))
    if manifest.get("route_version") != ROUTE_VERSION:
        findings.append(finding("review-manifest-route", "review-integrity", "Manifest review относится к другому маршруту", f"Ожидается {ROUTE_VERSION}.", artifact, remediation_owner="controller"))
    if manifest.get("tool_version") != ROUTE_TOOL_VERSION:
        findings.append(finding("review-manifest-tool-version", "review-integrity", "Manifest review создан несовместимой версией инструмента", f"Ожидается {ROUTE_TOOL_VERSION}.", artifact, remediation_owner="controller"))
    if result.get("review_manifest_sha256") != sha256_file(manifest_path):
        findings.append(finding("review-result-manifest-hash", "review-integrity", "Результат review не связан с переданным manifest", "review_manifest_sha256 не совпадает с контрольной суммой review-manifest.json.", artifact, remediation_owner="controller"))
    if result.get("execution_surface") != "codex-thread":
        findings.append(finding("review-result-execution-surface", "review-integrity", "Независимое review выполнено не в отдельной Codex-сессии", "execution_surface должен быть codex-thread.", artifact, remediation_owner="controller"))
    reviewer_thread_id = str(result.get("reviewer_thread_id") or "")
    if (
        not is_durable_codex_thread_id(reviewer_thread_id)
        or reviewer_thread_id == str(manifest.get("controller_thread_id") or "")
    ):
        findings.append(finding("review-result-thread-independence", "review-integrity", "Не доказана отдельность reviewer-сессии", "reviewer_thread_id должен быть durable Codex thread UUID и отличаться от controller_thread_id.", artifact, remediation_owner="controller"))
    attestation_contract = manifest.get("review_session_attestation_required")
    if attestation_contract is not None:
        if (
            not isinstance(attestation_contract, Mapping)
            or attestation_contract.get("version") != REVIEW_SESSION_ATTESTATION_VERSION
            or attestation_contract.get("owner") != "controller"
            or attestation_contract.get("execution_surface") != "codex-thread"
        ):
            findings.append(finding(
                "review-manifest-session-attestation-contract",
                "review-integrity",
                "Manifest review содержит неверный контракт подтверждения отдельной сессии",
                f"Ожидается controller-owned {REVIEW_SESSION_ATTESTATION_VERSION} для codex-thread.",
                artifact,
                remediation_owner="controller",
            ))
        elif review_session_attestation_path is None:
            findings.append(finding(
                "review-result-session-attestation-missing",
                "review-integrity",
                "Не передано подтверждение controller-а о создании отдельной reviewer-сессии",
                "Перед финализацией controller обязан записать attestation с фактическим reviewer_thread_id и передать его в verify/finalize.",
                artifact,
                remediation_owner="controller",
            ))
        else:
            try:
                attestation_path = package_relative_path(
                    package_root,
                    relative_to_package(package_root, review_session_attestation_path),
                    artifact=artifact,
                )
                attestation = read_json(attestation_path)
            except (PracticalV09Error, OSError, json.JSONDecodeError) as exc:
                findings.append(finding(
                    "review-result-session-attestation-unreadable",
                    "review-integrity",
                    "Подтверждение controller-а о reviewer-сессии недоступно",
                    str(exc),
                    artifact,
                    remediation_owner="controller",
                ))
            else:
                expected_attestation = {
                    "schema_version": 1,
                    "attestation_version": REVIEW_SESSION_ATTESTATION_VERSION,
                    "recorded_by": "controller",
                    "execution_surface": "codex-thread",
                    "review_manifest": relative_to_package(package_root, manifest_path),
                    "review_manifest_sha256": sha256_file(manifest_path),
                    "controller_thread_id": manifest.get("controller_thread_id"),
                    "reviewer_thread_id": reviewer_thread_id,
                    "code_commit": manifest.get("code_commit"),
                    "repo_root": manifest.get("repo_root"),
                    "ft_package_root": manifest.get("ft_package_root"),
                    "ft_package_path": manifest.get("ft_package_path"),
                }
                if any(attestation.get(key) != value for key, value in expected_attestation.items()):
                    findings.append(finding(
                        "review-result-session-attestation-mismatch",
                        "review-integrity",
                        "Подтверждение controller-а не связано с текущим review manifest и reviewer-сессией",
                        "Attestation должен в точности связывать manifest hash, controller/reviewer thread ID, code commit и нормализованные roots репозитория/FT-пакета.",
                        artifact,
                        remediation_owner="controller",
                    ))
                elif result.get("review_session_attestation_sha256") != sha256_file(attestation_path):
                    findings.append(finding(
                        "review-result-session-attestation-hash",
                        "review-integrity",
                        "Reviewer result не связан с controller-owned подтверждением сессии",
                        "review_session_attestation_sha256 должен совпадать с SHA-256 attestation.",
                        artifact,
                        remediation_owner="reviewer",
                    ))
    receipt_contract = manifest.get("reviewer_receipt_contract")
    compact_receipt_required = isinstance(receipt_contract, dict) and receipt_contract.get("format") == COMPACT_REVIEWER_RECEIPT_FORMAT
    if receipt_contract is not None and not compact_receipt_required:
        findings.append(finding(
            "review-manifest-receipt-contract",
            "review-integrity",
            "Manifest review содержит неподдерживаемый контракт компактного результата",
            f"reviewer_receipt_contract должен быть объектом format={COMPACT_REVIEWER_RECEIPT_FORMAT}.",
            artifact,
            remediation_owner="controller",
        ))
    independent = result.get("independent_obligations")
    if not compact_receipt_required and (not isinstance(independent, list) or not independent):
        findings.append(finding("review-result-independent-obligations", "review-integrity", "Reviewer не зафиксировал самостоятельный список обязательств", "До сравнения с matrix/TC reviewer обязан перечислить independently derived obligations.", artifact, remediation_owner="reviewer"))
    if result.get("review_mode") != manifest.get("review_mode"):
        findings.append(finding("review-result-mode", "review-integrity", "Режим результата review не совпадает с manifest", "review_mode результата должен совпадать с review_mode manifest.", artifact, remediation_owner="reviewer"))
    for key in ("scope_id", "scope_slug"):
        if result.get(key) != manifest.get(key):
            findings.append(finding("review-result-scope", "review-integrity", "Результат review относится к другому scope", f"Поле {key} должно совпадать с review-manifest.json.", artifact, remediation_owner="reviewer"))
    if result.get("verdict") not in {"approved", "changes-required", "blocked-input"}:
        findings.append(finding("review-result-verdict", "review-integrity", "У результата review неизвестный verdict", "Допустимы approved, changes-required или blocked-input.", artifact, remediation_owner="reviewer"))
    consolidation_contract = manifest.get("scenario_consolidation_contract")
    if consolidation_contract is not None:
        if (
            not isinstance(consolidation_contract, dict)
            or consolidation_contract.get("version")
            != SCENARIO_CONSOLIDATION_CONTRACT_VERSION
        ):
            findings.append(finding(
                "review-manifest-scenario-consolidation-contract",
                "review-integrity",
                "Manifest matrix review содержит неверный контракт консолидации сценариев",
                f"Ожидается version={SCENARIO_CONSOLIDATION_CONTRACT_VERSION}.",
                artifact,
                remediation_owner="controller",
            ))
        else:
            raw_review = result.get("scenario_consolidation_review")
            expected_ids = [
                str(item.get("id"))
                for item in consolidation_contract.get("decisions", [])
                if isinstance(item, dict)
            ]
            if not isinstance(raw_review, dict):
                findings.append(finding(
                    "review-result-scenario-consolidation",
                    "review-integrity",
                    "Reviewer не подтвердил проверку решений о консолидации сценариев",
                    "Matrix review должен содержать scenario_consolidation_review из immutable manifest.",
                    artifact,
                    remediation_owner="reviewer",
                ))
            else:
                actual_ids = raw_review.get("decision_ids")
                candidate_count = raw_review.get("uncategorized_candidate_count")
                if (
                    raw_review.get("checked") is not True
                    or not isinstance(actual_ids, list)
                    or actual_ids != expected_ids
                    or not isinstance(candidate_count, int)
                    or candidate_count < 0
                    or not isinstance(raw_review.get("method"), str)
                    or not raw_review["method"].strip()
                ):
                    findings.append(finding(
                        "review-result-scenario-consolidation-format",
                        "review-integrity",
                        "Подтверждение reviewer-а о консолидации сценариев неполно",
                        "Нужны checked=true, decision_ids из manifest, неотрицательный uncategorized_candidate_count и непустой method.",
                        artifact,
                        remediation_owner="reviewer",
                    ))
                elif result.get("verdict") == "approved" and candidate_count != 0:
                    findings.append(finding(
                        "review-result-scenario-consolidation-approved-with-gaps",
                        "review-integrity",
                        "Reviewer одобрил матрицу с неучтёнными кандидатами на консолидацию",
                        "При approved значение uncategorized_candidate_count должно быть равно нулю.",
                        artifact,
                        remediation_owner="reviewer",
                    ))
    raw_review_findings = result.get("findings")
    if not isinstance(raw_review_findings, list):
        findings.append(finding(
            "review-result-findings-format",
            "review-integrity",
            "У результата review неверный формат findings",
            "Поле findings должно быть массивом формальных findings, включая пустой массив при approved verdict.",
            artifact,
            remediation_owner="reviewer",
        ))
    triage_contract = manifest.get("controller_triage_contract")
    if triage_contract is not None:
        if (
            not isinstance(triage_contract, dict)
            or triage_contract.get("version") != CONTROLLER_TRIAGE_CONTRACT_VERSION
            or triage_contract.get("finding_schema") != "practical-review-finding-v1"
            or triage_contract.get("required_for")
            != "changes-required-with-content-blockers"
        ):
            findings.append(finding(
                "review-manifest-controller-triage-contract",
                "review-integrity",
                "Manifest review содержит неверный контракт controller triage",
                "Нужен controller-triage-v1 с форматом practical-review-finding-v1.",
                artifact,
                remediation_owner="controller",
            ))
        elif isinstance(raw_review_findings, list):
            finding_ids: set[str] = set()
            for index, review_finding in enumerate(raw_review_findings, start=1):
                if not isinstance(review_finding, dict):
                    findings.append(finding(
                        "review-result-finding-schema",
                        "review-integrity",
                        "Finding reviewer-а имеет неверный формат",
                        f"findings[{index}] должен быть объектом practical-review-finding-v1.",
                        artifact,
                        remediation_owner="reviewer",
                    ))
                    continue
                missing = [
                    key for key in REVIEW_FINDING_REQUIRED_FIELDS
                    if key not in review_finding
                    or (isinstance(review_finding.get(key), str) and not review_finding[key].strip())
                ]
                identifier = review_finding.get("id")
                if (
                    missing
                    or not isinstance(identifier, str)
                    or identifier in finding_ids
                    or not isinstance(review_finding.get("blocking"), bool)
                    or not isinstance(review_finding.get("remediation_owner"), str)
                ):
                    findings.append(finding(
                        "review-result-finding-schema",
                        "review-integrity",
                        "Finding reviewer-а неполон или не имеет уникального идентификатора",
                        f"findings[{index}] требует поля: {', '.join(REVIEW_FINDING_REQUIRED_FIELDS)}.",
                        artifact,
                        remediation_owner="reviewer",
                    ))
                    continue
                finding_ids.add(identifier)
                if review_finding["blocking"] is True and not str(
                    review_finding.get("blocking_reason") or ""
                ).strip():
                    findings.append(finding(
                        "review-result-finding-blocking-reason",
                        "review-integrity",
                        "Для блокирующего finding reviewer-а не указана причина блокировки",
                        f"findings[{index}].blocking_reason обязателен при blocking=true.",
                        artifact,
                        remediation_owner="reviewer",
                    ))
                status_change_claimed = bool(STATUS_CHANGE_CLAIM_RE.search(
                    " ".join(
                        str(review_finding.get(key) or "")
                        for key in ("title", "details", "blocking_reason")
                    )
                ))
                assertion = review_finding.get("status_assertion")
                if status_change_claimed or assertion is not None:
                    if (
                        not isinstance(assertion, dict)
                        or assertion.get("required_status") not in ALLOWED_EXECUTION_STATUSES
                        or not isinstance(assertion.get("scenario_ids"), list)
                        or not assertion["scenario_ids"]
                        or not all(
                            isinstance(item, str) and item.startswith("SCN-")
                            for item in assertion["scenario_ids"]
                        )
                    ):
                        findings.append(finding(
                            "review-result-status-assertion",
                            "review-integrity",
                            "Статусное замечание reviewer-а не имеет проверяемой декларации",
                            f"findings[{index}] запрашивает изменение статуса исполнения; "
                            "укажите status_assertion с required_status и затронутыми SCN-*.",
                            artifact,
                            remediation_owner="reviewer",
                        ))
    for entry in manifest.get("inputs", []):
        if not isinstance(entry, dict):
            continue
        path = package_relative_path(package_root, entry.get("path"), artifact=artifact)
        if not path.is_file() or sha256_file(path) != entry.get("sha256"):
            findings.append(finding("review-result-snapshot-changed", "artifact-tampering", "Изменён входной snapshot независимого review", f"Изменился {entry.get('path')} после создания manifest.", artifact, remediation_owner="controller"))
    obligations_entry = next(
        (entry for entry in manifest.get("inputs", []) if isinstance(entry, dict) and entry.get("role") == "scope_obligations"),
        None,
    )
    if compact_receipt_required and obligations_entry:
        max_bytes = receipt_contract.get("max_bytes")
        if not isinstance(max_bytes, int) or max_bytes <= 0 or max_bytes > COMPACT_REVIEWER_RECEIPT_MAX_BYTES:
            findings.append(finding(
                "review-manifest-receipt-size-limit",
                "review-integrity",
                "Manifest review содержит недопустимый лимит compact receipt",
                f"max_bytes должен быть целым числом от 1 до {COMPACT_REVIEWER_RECEIPT_MAX_BYTES}.",
                artifact,
                remediation_owner="controller",
            ))
        elif result_path.stat().st_size > max_bytes:
            findings.append(finding(
                "review-result-compact-size",
                "review-integrity",
                "Raw результат reviewer-а превышает лимит compact receipt",
                f"Размер {result_path.stat().st_size} байт превышает max_bytes={max_bytes} из immutable manifest.",
                artifact,
                remediation_owner="reviewer",
            ))
        compact_receipt = result.get("independent_obligation_vector")
        if not isinstance(compact_receipt, list):
            findings.append(finding(
                "review-result-compact-obligation-vector",
                "review-integrity",
                "Для большого scope отсутствует компактный вектор обязательств",
                "Reviewer должен вернуть independent_obligation_vector из первого raw JSON submission.",
                artifact,
                remediation_owner="reviewer",
            ))
        else:
            received_ids: set[str] = set()
            vector_invalid = False
            vector_verdicts: list[str] = []
            for index, entry in enumerate(compact_receipt, start=1):
                if not isinstance(entry, dict):
                    vector_invalid = True
                    continue
                obligation_id = entry.get("obligation_id")
                verdict = entry.get("verdict")
                if (
                    not isinstance(obligation_id, str)
                    or not obligation_id.startswith("OBL-")
                    or obligation_id in received_ids
                    or verdict not in {"covered", "gap", "blocked"}
                    or not str(entry.get("source_anchor") or "").strip()
                    or not str(entry.get("statement") or "").strip()
                ):
                    vector_invalid = True
                    continue
                received_ids.add(obligation_id)
                vector_verdicts.append(str(verdict))
            if vector_invalid or received_ids != set(receipt_contract.get("obligation_ids", [])):
                findings.append(finding(
                    "review-result-compact-obligation-vector-coverage",
                    "review-integrity",
                    "Компактный вектор reviewer-а неполон или имеет неверный формат",
                    "Каждый активный OBL-* из immutable manifest должен иметь один verdict, source_anchor и statement.",
                    artifact,
                    remediation_owner="reviewer",
                ))
            compact_digest = result.get("independent_obligation_vector_digest")
            if compact_digest != receipt_contract.get("active_obligation_ids_sha256"):
                findings.append(finding(
                    "review-result-compact-obligation-vector-digest",
                    "review-integrity",
                    "Компактный вектор reviewer-а не связан с immutable набором обязательств",
                    "independent_obligation_vector_digest должен совпадать с active_obligation_ids_sha256 из reviewer_receipt_contract.",
                    artifact,
                    remediation_owner="reviewer",
                ))
            if result.get("verdict") == "approved" and any(item != "covered" for item in vector_verdicts):
                findings.append(finding(
                    "review-result-compact-obligation-vector-approved-with-gaps",
                    "review-integrity",
                    "Reviewer одобрил scope с незакрытым обязательством",
                    "При verdict=approved каждый OBL-* в independent_obligation_vector должен иметь verdict=covered.",
                    artifact,
                    remediation_owner="reviewer",
                ))
    elif isinstance(independent, list) and obligations_entry:
        obligations_path = package_relative_path(package_root, obligations_entry.get("path"), artifact=artifact)
        if obligations_path.is_file():
            expected = active_obligation_ids(read_json(obligations_path))
            actual: set[str] = set()
            for index, entry in enumerate(independent, start=1):
                if not isinstance(entry, dict):
                    findings.append(finding(
                        "review-result-independent-obligation-format",
                        "review-integrity",
                        "Самостоятельно восстановленное обязательство имеет неверный формат",
                        f"independent_obligations[{index}] должен содержать source_anchor, statement и obligation_ids.",
                        artifact,
                        remediation_owner="reviewer",
                    ))
                    continue
                source_anchor = str(entry.get("source_anchor") or "").strip()
                statement = str(entry.get("statement") or "").strip()
                obligation_ids = entry.get("obligation_ids")
                if (
                    not source_anchor
                    or not statement
                    or not isinstance(obligation_ids, list)
                    or not obligation_ids
                    or not all(isinstance(item, str) and item.startswith("OBL-") for item in obligation_ids)
                ):
                    findings.append(finding(
                        "review-result-independent-obligation-format",
                        "review-integrity",
                        "Самостоятельно восстановленное обязательство неполно",
                        f"independent_obligations[{index}] требует непустые source_anchor, statement и obligation_ids с OBL-*.",
                        artifact,
                        remediation_owner="reviewer",
                    ))
                    continue
                actual.update(obligation_ids)
            if actual != expected:
                findings.append(finding(
                    "review-result-independent-coverage",
                    "review-integrity",
                    "Reviewer восстановил неполный или иной набор обязательств",
                    "obligation_ids в independently derived obligations должны в сумме содержать в точности все активные OBL-* из зафиксированного scope-obligations.json.",
                    artifact,
                    remediation_owner="reviewer",
                    evidence=["expected=" + ",".join(sorted(expected)), "actual=" + ",".join(sorted(actual))],
                ))
    return result, findings
