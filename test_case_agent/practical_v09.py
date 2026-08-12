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
from typing import Any, Iterable


ROUTE_VERSION = "practical-v0.9"
ROUTE_TOOL_VERSION = "practical-v0.9.9"
WORKFLOW_STATE_SCHEMA_VERSION = 1
SOURCE_CONTRACT_VERSION = "source-package-v3"
REVIEW_MANIFEST_VERSION = "practical-review-manifest-v2"
VALIDATOR_REPORT_VERSION = "practical-scope-validator-v2"
SOURCE_MANIFEST_RELATIVE_PATH = "work/practical-v0.9/source-package-manifest.json"
CLARIFICATION_REQUESTS_FILENAME = "scope-clarification-requests.md"
CLARIFICATION_REQUEST_SECTION_HEADINGS = (
    "Контекст",
    "Как Заполнять",
    "Запросы на уточнение",
    "Пробелы без запросов",
    "Правила Использования Ответов",
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
REQUIRED_TC_FIELDS = (
    "Название",
    "Тип",
    "Приоритет",
    "Статус исполнения",
    "Контекст исполнения",
    "Трассировка",
    "Цель",
    "Предусловия",
    "Тестовые данные",
    "Шаги",
    "Итоговый ожидаемый результат",
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
MATRIX_REVIEW_OBLIGATION_THRESHOLD = 8
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
EXECUTION_STATUS_PRECEDENCE = (
    "needs-future-clarification",
    "blocked-observability",
    "needs-test-data",
    "candidate-ui-calibration",
)
MATRIX_REQUIRED_COLUMNS = (
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
    "decision_type": {"supersedes-ft"},
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
    revision_count = state.get("revision_count")
    if not isinstance(revision_count, int) or not 0 <= revision_count <= 1:
        raise PracticalV09Error("workflow-state.json: revision_count must be 0 or 1")
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
    return state


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


def execution_contexts(obligation: dict[str, Any]) -> list[dict[str, Any]]:
    """Return explicitly declared user-execution contexts for one OBL."""
    entries = obligation.get("execution_contexts", [])
    return [item for item in entries if isinstance(item, dict)] if isinstance(entries, list) else []


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
        if isinstance(item, dict)
    }
    for status in EXECUTION_STATUS_PRECEDENCE:
        if status in availability:
            return status
    return "ready"


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
    approved_ba_decision_ids: set[str],
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
                if decision_id not in approved_ba_decision_ids:
                    findings.append(finding(
                        "scope-ba-decision-missing",
                        "source-integrity",
                        "Закрытый gap ссылается на отсутствующее утверждённое решение БА",
                        f"{gap_id}: не найдено решение {decision_id or '<без ID>'} в package-level реестре.",
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
        evidence = str(setup.get("evidence") or "").strip()
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
        if not evidence:
            findings.append(finding(
                "scope-execution-setup-evidence",
                "execution-readiness",
                "Для предпосылки не указано подтверждение подготовки",
                f"{setup_id or f'строка {index}'}: укажите воспроизводимый способ подготовки или источник доступности.",
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
            if decision_id not in approved_ba_decisions:
                findings.append(finding(
                    "scope-obligation-ba-decision",
                    "traceability",
                    "Исключённое обязательство не связано с утверждённым решением БА",
                    f"{obligation_id}: ba_decision_id={decision_id or '<не указан>'} не найден в package-level реестре.",
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
        if disposition == "active":
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
            approved_ba_decision_ids=set(approved_ba_decisions),
        )
    )
    return findings, payload


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


def validate_matrix(
    matrix_path: Path, package_root: Path, obligations: dict[str, Any]
) -> tuple[list[ScopeFinding], dict[tuple[str, str], list[dict[str, str]]]]:
    artifact = relative_to_package(package_root, matrix_path)
    findings: list[ScopeFinding] = []
    try:
        rows, errors = parse_matrix_rows(matrix_path)
    except PracticalV09Error as exc:
        return [finding("matrix-unreadable", "source-integrity", "Недоступна матрица тест-дизайна", str(exc), artifact, remediation_owner="writer")], {}
    for error in errors:
        findings.append(finding("matrix-format", "format", "Матрица тест-дизайна не соответствует компактному шаблону", error, artifact, remediation_owner="writer", severity="warning"))
    by_obligation_context: dict[tuple[str, str], list[dict[str, str]]] = {}
    seen_matrix_ids: set[str] = set()
    active_ids = active_obligation_ids(obligations)
    active_entries = {str(item.get("id")): item for item in active_obligations(obligations)}
    setup_catalog = execution_setups(obligations)
    all_ids = {
        str(item.get("id"))
        for item in obligations.get("obligations", [])
        if isinstance(item, dict)
    }
    for row in rows:
        matrix_id = row.get("Проверка", "")
        obligation_id = row.get("Обязательство ФТ", "")
        context_id = context_id_from_cell(row.get("Контекст исполнения", ""))
        tc_id = row.get("Планируемый TC-ID", "")
        if not re.fullmatch(r"MTX-[A-Z0-9-]+", matrix_id):
            findings.append(finding("matrix-id", "traceability", "У строки матрицы некорректный идентификатор", f"Проверка={matrix_id!r}; ожидается MTX-*.", artifact, remediation_owner="writer"))
        elif matrix_id in seen_matrix_ids:
            findings.append(finding("matrix-duplicate-id", "traceability", "В матрице повторяется идентификатор проверки", f"Повторяется {matrix_id}.", artifact, remediation_owner="writer"))
        seen_matrix_ids.add(matrix_id)
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
            "Проверяемое правило",
            "Ожидаемый результат",
            "Нужные предпосылки",
            "Сценарий",
            "Тип",
            "Приоритет",
            "Статус исполнения",
        ):
            if not row.get(required_column, "").strip():
                findings.append(finding("matrix-required-cell", "semantic-completeness", "В строке матрицы не заполнено обязательное поле", f"Проверка {matrix_id or '<без ID>'}: отсутствует «{required_column}».", artifact, remediation_owner="writer"))
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
            else:
                expected_status = derived_execution_status(context, setup_catalog)
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
        elif len(mapped) > 1:
            findings.append(finding(
                "matrix-obligation-context-duplicated",
                "traceability",
                "Контекст обязательства повторно спроектирован в матрице",
                f"{obligation_id} / {context_id} связан со строками: " + ", ".join(row.get("Проверка", "<без ID>") for row in mapped) + ".",
                artifact,
                remediation_owner="writer",
            ))
    return findings, {
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


def validate_test_cases(
    tc_path: Path,
    package_root: Path,
    obligations: dict[str, Any],
    matrix_mapping: dict[tuple[str, str], list[dict[str, str]]],
) -> list[ScopeFinding]:
    artifact = relative_to_package(package_root, tc_path)
    try:
        blocks = parse_test_case_blocks(tc_path)
    except PracticalV09Error as exc:
        return [finding("test-cases-unreadable", "source-integrity", "Недоступен файл тест-кейсов", str(exc), artifact, remediation_owner="writer")]
    findings: list[ScopeFinding] = []
    if not blocks:
        return [finding("test-cases-empty", "semantic-completeness", "В файле нет тест-кейсов компактного формата", "Ожидается заголовок уровня ## или ### с TC-*.", artifact, remediation_owner="writer")]
    seen_ids: set[str] = set()
    covered_contexts: dict[tuple[str, str], list[str]] = {}
    for block in blocks:
        tc_id = block["id"]
        body = block["body"]
        if tc_id in seen_ids:
            findings.append(finding("test-case-duplicate-id", "traceability", "Повторяется TC-ID", f"Повторяется {tc_id}.", artifact, remediation_owner="writer"))
        seen_ids.add(tc_id)
        for field in REQUIRED_TC_FIELDS:
            if not re.search(rf"(?m)^\*\*{re.escape(field)}:\*\*\s*\S", body):
                findings.append(finding("test-case-required-field", "execution-readiness", "В тест-кейсе отсутствует обязательное поле", f"{tc_id}: отсутствует «{field}».", artifact, remediation_owner="writer"))
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
        expected_result_count = len(re.findall(r"(?m)^\*\*Итоговый ожидаемый результат:\*\*", body))
        if expected_result_count != 1:
            findings.append(finding("test-case-primary-oracle", "semantic-completeness", "У тест-кейса должен быть один основной ожидаемый результат", f"{tc_id}: найдено полей ожидаемого результата: {expected_result_count}.", artifact, remediation_owner="writer"))
        trace_match = re.search(r"(?m)^\*\*Трассировка:\*\*\s*(.+)$", body)
        trace = trace_match.group(1) if trace_match else ""
        obligation_ids = re.findall(r"\bOBL-[A-Z0-9-]+\b", trace)
        if len(obligation_ids) != 1:
            findings.append(finding("test-case-obligation-trace", "traceability", "Тест-кейс должен ссылаться ровно на одно обязательство ФТ", f"{tc_id}: в трассировке найдено OBL: {', '.join(obligation_ids) or 'нет'}.", artifact, remediation_owner="writer"))
        else:
            pair = (obligation_ids[0], context_id)
            covered_contexts.setdefault(pair, []).append(tc_id)
            if obligation_ids[0] not in active_obligation_ids(obligations):
                findings.append(finding(
                    "test-case-obligation-superseded",
                    "traceability",
                    "Тест-кейс ссылается на обязательство, отменённое решением БА",
                    f"{tc_id}: {obligation_ids[0]} не должно попадать в test cases.",
                    artifact,
                    remediation_owner="writer",
                ))
            mapped_rows = matrix_mapping.get(pair, [])
            if len(mapped_rows) != 1:
                findings.append(finding(
                    "test-case-matrix-context-trace",
                    "traceability",
                    "Тест-кейс не связан с одной строкой матрицы в том же контексте",
                    f"{tc_id}: не найдена единственная matrix row для {obligation_ids[0]} / {context_id or '<без CTX>'}.",
                    artifact,
                    remediation_owner="writer",
                ))
            elif status_match and status_match.group(1) != mapped_rows[0].get("Статус исполнения"):
                findings.append(finding(
                    "test-case-execution-status-matrix",
                    "execution-readiness",
                    "Статус исполнения тест-кейса отличается от статуса в матрице",
                    f"{tc_id}: указан {status_match.group(1)}, в матрице {mapped_rows[0].get('Статус исполнения')}.",
                    artifact,
                    remediation_owner="writer",
                ))
        body_without_metadata = re.sub(r"(?m)^\*\*(Тип|Приоритет|Статус исполнения):\*\*.*$", "", body)
        if re.search(r"\b(source-backed|residual|fixture|blocked-observability)\b", body_without_metadata, flags=re.IGNORECASE):
            findings.append(finding("test-case-process-language", "style", "В тест-кейсе остался служебный английский текст", f"Проверьте пользовательские поля {tc_id}.", artifact, remediation_owner="writer", severity="warning"))
    for obligation_id, context_id in sorted(matrix_mapping):
        mapped_tcs = covered_contexts.get((obligation_id, context_id), [])
        if not mapped_tcs:
            findings.append(finding(
                "test-case-obligation-context-uncovered",
                "semantic-completeness",
                "Контекст обязательства матрицы не покрыт тест-кейсом",
                f"Для {obligation_id} в контексте {context_id} нет TC.",
                artifact,
                remediation_owner="writer",
            ))
        elif len(mapped_tcs) > 1:
            findings.append(finding(
                "test-case-obligation-context-duplicated",
                "traceability",
                "Контекст обязательства покрыт несколькими тест-кейсами",
                f"{obligation_id} / {context_id}: {', '.join(mapped_tcs)}. Для v0.9 это допустимо только после явного разбиения на самостоятельные OBL/CTX.",
                artifact,
                remediation_owner="writer",
            ))
    expected_obligations = active_obligation_ids(obligations)
    unknown = sorted({obligation_id for obligation_id, _ in covered_contexts} - expected_obligations)
    if unknown:
        findings.append(finding("test-case-unknown-obligation", "traceability", "Тест-кейс ссылается на отсутствующее обязательство", ", ".join(unknown), artifact, remediation_owner="writer"))
    return findings


def matrix_review_required(obligations: dict[str, Any]) -> tuple[bool, list[str]]:
    entries = active_obligations(obligations)
    reasons: list[str] = []
    if len(entries) >= MATRIX_REVIEW_OBLIGATION_THRESHOLD:
        reasons.append(f"Количество обязательств: {len(entries)} (порог {MATRIX_REVIEW_OBLIGATION_THRESHOLD}).")
    flags = {
        str(flag)
        for item in entries
        for flag in (item.get("risk_flags") if isinstance(item.get("risk_flags"), list) else [])
    }
    matched = sorted(flags & MATRIX_REVIEW_RISK_FLAGS)
    if matched:
        reasons.append("Риски scope: " + ", ".join(matched) + ".")
    return bool(reasons), reasons


def validate_workflow_artifact_links(state: dict[str, Any], package_root: Path) -> list[ScopeFinding]:
    findings: list[ScopeFinding] = []
    artifact = "workflow-state.json"
    phase = str(state.get("phase") or "")
    required_by_phase = {
        "scope": ("source_package_manifest", "scope_obligations"),
        "matrix": ("source_package_manifest", "scope_obligations", "test_design_matrix"),
        "test-cases": ("source_package_manifest", "scope_obligations", "test_design_matrix", "canonical_test_cases"),
        "review": ("source_package_manifest", "scope_obligations", "test_design_matrix", "canonical_test_cases"),
        "accepted": ("source_package_manifest", "scope_obligations", "test_design_matrix", "canonical_test_cases"),
        "blocked": ("source_package_manifest", "scope_obligations"),
    }
    if phase not in required_by_phase:
        findings.append(finding("workflow-phase", "transport", "В workflow указан неизвестный этап", f"phase={phase!r}.", artifact, remediation_owner="controller", severity="warning"))
        return findings
    for key in required_by_phase[phase]:
        try:
            path = workflow_artifact_path(state, package_root, key, required=True)
        except PracticalV09Error as exc:
            findings.append(finding("workflow-artifact-reference", "source-integrity", "В workflow отсутствует обязательная ссылка на артефакт", str(exc), artifact, remediation_owner="controller"))
            continue
        if path is not None and not path.is_file():
            findings.append(finding("workflow-artifact-missing", "source-integrity", "Workflow ссылается на отсутствующий артефакт", f"artifacts.{key}={relative_to_package(package_root, path)}.", artifact, remediation_owner="controller"))
    return findings


def approved_review_exists(state: dict[str, Any], review_mode: str) -> bool:
    """Return whether the single workflow state records a valid accepted review mode."""
    return any(
        isinstance(entry, dict)
        and entry.get("mode") == review_mode
        and entry.get("verdict") == "approved"
        for entry in state.get("reviews", [])
    )


def validate_scope(
    *, package_root: Path, workflow_state_path: Path, include_test_cases: bool | None = None
) -> tuple[dict[str, Any], list[ScopeFinding]]:
    package_root = package_root.resolve()
    state = load_workflow_state(workflow_state_path, package_root)
    findings = validate_workflow_artifact_links(state, package_root)
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

    matrix_path = workflow_artifact_path(state, package_root, "test_design_matrix")
    matrix_mapping: dict[tuple[str, str], list[dict[str, str]]] = {}
    if matrix_path is not None:
        if matrix_path.is_file():
            matrix_findings, matrix_mapping = validate_matrix(matrix_path, package_root, obligations)
            findings.extend(matrix_findings)
        else:
            findings.append(finding("matrix-missing", "source-integrity", "Матрица тест-дизайна отсутствует", relative_to_package(package_root, matrix_path), "workflow-state.json", remediation_owner="writer"))

    tc_path = workflow_artifact_path(state, package_root, "canonical_test_cases")
    need_tc = include_test_cases if include_test_cases is not None else tc_path is not None
    if need_tc:
        if tc_path is None:
            findings.append(finding("test-cases-reference-missing", "traceability", "В workflow не указан файл тест-кейсов", "Для этапа тест-кейсов нужна artifacts.canonical_test_cases.", "workflow-state.json", remediation_owner="writer"))
        elif tc_path.is_file():
            findings.extend(validate_test_cases(tc_path, package_root, obligations, matrix_mapping))
        else:
            findings.append(finding("test-cases-missing", "source-integrity", "Файл тест-кейсов отсутствует", relative_to_package(package_root, tc_path), "workflow-state.json", remediation_owner="writer"))

    matrix_required, matrix_reasons = matrix_review_required(obligations)
    declared = state.get("matrix_review_required")
    if declared is not None and bool(declared) != matrix_required:
        findings.append(finding("matrix-review-decision-stale", "transport", "Workflow содержит устаревшее решение о matrix review", "; ".join(matrix_reasons) or "Scope не достигает порога обязательного matrix review.", "workflow-state.json", remediation_owner="controller", severity="warning"))

    phase = str(state.get("phase") or "")
    if matrix_required and phase in {"test-cases", "review", "accepted"} and not approved_review_exists(state, "matrix"):
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

    content_input_hashes = {
        key: sha256_file(path)
        for key in ("source_package_manifest", "scope_obligations", "test_design_matrix", "canonical_test_cases")
        for path in [workflow_artifact_path(state, package_root, key)]
        if path is not None and path.is_file()
    }
    report_context = {
        "route_version": ROUTE_VERSION,
        "tool_version": ROUTE_TOOL_VERSION,
        "scope_id": state["scope_id"],
        "scope_slug": state["scope_slug"],
        "phase": state["phase"],
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
) -> dict[str, Any]:
    state = load_workflow_state(workflow_state_path, package_root)
    if not is_durable_codex_thread_id(controller_thread_id):
        raise PracticalV09Error("controller_thread_id must be a durable Codex thread UUID")
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
    return {
        "schema_version": 1,
        "manifest_version": REVIEW_MANIFEST_VERSION,
        "route_version": ROUTE_VERSION,
        "tool_version": ROUTE_TOOL_VERSION,
        "scope_id": state["scope_id"],
        "scope_slug": state["scope_slug"],
        "review_mode": review_mode,
        "controller_thread_id": controller_thread_id,
        "execution_surface_required": "codex-thread",
        "code_branch": code_branch,
        "code_commit": code_commit,
        "contract_digest": contract_digest,
        "validator_report_sha256": sha256_file(validator_report_path),
        "validator_report_digest": sha256_json(validator_report),
        "inputs": [
            {"role": key, "path": relative_to_package(package_root, path), "sha256": sha256_file(path)}
            for key, path in paths.items()
        ],
        "reviewer_order": [
            "Самостоятельно восстановить обязательства из исходных материалов.",
            "Сопоставить обязательства с матрицей тест-дизайна.",
            "Проверить тест-кейсы, если review_mode=test-cases.",
        ],
    }


def verify_review_result(
    *, package_root: Path,
    manifest_path: Path,
    result_path: Path,
) -> tuple[dict[str, Any], list[ScopeFinding]]:
    manifest = read_json(manifest_path)
    result = read_json(result_path)
    artifact = relative_to_package(package_root, result_path)
    findings: list[ScopeFinding] = []
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
    independent = result.get("independent_obligations")
    if not isinstance(independent, list) or not independent:
        findings.append(finding("review-result-independent-obligations", "review-integrity", "Reviewer не зафиксировал самостоятельный список обязательств", "До сравнения с matrix/TC reviewer обязан перечислить independently derived obligations.", artifact, remediation_owner="reviewer"))
    if result.get("review_mode") != manifest.get("review_mode"):
        findings.append(finding("review-result-mode", "review-integrity", "Режим результата review не совпадает с manifest", "review_mode результата должен совпадать с review_mode manifest.", artifact, remediation_owner="reviewer"))
    for key in ("scope_id", "scope_slug"):
        if result.get(key) != manifest.get(key):
            findings.append(finding("review-result-scope", "review-integrity", "Результат review относится к другому scope", f"Поле {key} должно совпадать с review-manifest.json.", artifact, remediation_owner="reviewer"))
    if result.get("verdict") not in {"approved", "changes-required", "blocked-input"}:
        findings.append(finding("review-result-verdict", "review-integrity", "У результата review неизвестный verdict", "Допустимы approved, changes-required или blocked-input.", artifact, remediation_owner="reviewer"))
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
    if isinstance(independent, list) and obligations_entry:
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
