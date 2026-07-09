from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import warnings
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

warnings.filterwarnings("ignore", message="ARC4 has been moved", category=Warning)

from test_case_agent import analyze_sections, classify_source_quality_issue, load_sections
from test_case_agent.chunking import split_section

ALLOWED_CURRENT_STAGES = {
    "ft-source-locator",
    "ft-scope-analyzer",
    "ft-test-case-writer",
    "ft-test-case-reviewer",
    "ft-test-case-iteration",
    "ft-ui-automation-prep",
}
ALLOWED_STAGE_STATUSES = {
    "ready-for-next-stage",
    "ready-for-gap-review",
    "ready-for-review",
    "ready-for-writer-revision",
    "signed-off",
    "round-cap-reached",
    "blocked-input",
}
ALLOWED_NEXT_SKILLS = ALLOWED_CURRENT_STAGES | {"none", None}
SESSION_BASED_REVIEW_CYCLE_STATUSES = {
    "scope-ready-for-gap-review",
    "scope-gap-review-passed",
    "scope-ready-for-writer",
    "writer-draft-ready",
    "structure-preflight-blocked",
    "semantic-review-ready",
    "semantic-revision-needed",
    "semantic-review-passed",
    "format-review-ready",
    "format-revision-needed",
    "final-regression-ready",
    "signed-off",
    "round-cap-reached",
    "blocked-input",
}
ALLOWED_UI_STATUSES = {
    "confirmed",
    "mismatch-ft-ui",
    "blocked-ui-unavailable",
    "blocked-access",
    "blocked-observability",
    "not-automatable-manual-only",
}
ALLOWED_ARTIFACT_EXPORT_POLICIES = {
    "repo-tracked",
    "alias-copy",
    "local-output-index-only",
    "external",
    "not-collected",
}
REPO_TRACKED_ARTIFACT_POLICIES = {"repo-tracked", "alias-copy"}
SOURCE_SUPPORT_EXTENSIONS = {
    ".docx",
    ".pdf",
    ".xlsx",
    ".xlsb",
    ".vsdx",
    ".png",
    ".json",
    ".txt",
    ".wsdl",
}
REQUIRED_WORKFLOW_FIELDS = {
    "ft_slug",
    "scope_slug",
    "current_stage",
    "stage_status",
    "current_round",
    "next_skill",
    "required_inputs",
    "latest_artifacts",
    "open_questions",
    "blocking_reasons",
}
REQUIRED_SOURCE_SELECTION_SECTIONS = {
    "Context",
    "Main FT Documents",
    "Machine-Readable XHTML Source",
    "Structural Cross-Check PDF",
    "Support Files And Mockups",
    "Source Quality",
    "Ambiguity And Decision Log",
    "Handoff",
}
REQUIRED_SOURCE_SELECTION_CONTEXT_FIELDS = {
    "selected_ft_slug",
    "selection_status",
}
ALLOWED_SOURCE_SELECTION_STATUSES = {"selected", "ambiguous", "blocked-input"}
REQUIRED_FINAL_ARTIFACT_ALIASES = {
    "final_findings",
    "final_traceability_matrix",
    "final_traceability_matrix_xlsx",
    "loop_summary",
}
ALLOWED_REVIEW_MODES = {"traceability", "structure", "test-design", "scope_gap_review"}
ALLOWED_FINDING_SEVERITIES = {"error", "warning", "info"}
ALLOWED_FINDING_CATEGORIES = {
    "coverage",
    "atomarity",
    "traceability",
    "expected-result",
    "scope",
    "duplication",
    "format",
    "structure",
    "test-design",
}
ALLOWED_FINDING_STATUSES = {"open", "closed", "partially-closed"}
REQUIRED_FINDING_FIELDS = {
    "review_mode",
    "severity",
    "category",
    "title",
    "problem",
    "evidence",
    "required_change",
    "source_reference",
    "status",
}
REQUIRED_REVIEWER_SIGNOFF_FIELDS = {
    "traceability_checked",
    "structure_checked",
    "test_case_grouping_checked",
    "test_case_numbering_checked",
    "test_design_checked",
    "applicability_dimensions_checked",
    "validator_checked",
    "blocking_findings_absent",
    "traceability_gaps_absent",
    "known_unclear_items",
    "sign_off_rationale",
}
REQUIRED_RESIDUAL_RISK_FIELDS = {
    "remaining_blocking_findings",
    "remaining_traceability_gaps",
    "remaining_coverage_gaps",
    "remaining_unclear_items",
    "decision_rationale",
    "next_action",
}
REVIEWER_SIGNOFF_YES_FIELDS = {
    "structure_checked",
    "test_case_grouping_checked",
    "test_case_numbering_checked",
    "test_design_checked",
    "applicability_dimensions_checked",
    "validator_checked",
    "blocking_findings_absent",
}
REVIEWER_SIGNOFF_YES_OR_NA_FIELDS = {
    "source_parity_checked",
    "traceability_checked",
    "traceability_gaps_absent",
}
ALLOWED_RESOLUTION_STATUSES = {"fixed", "not-fixed-scope", "needs-clarification"}
REQUIRED_WRITER_RESPONSE_FIELDS = {
    "resolution_status",
    "change_summary",
    "affected_test_case_ids",
}
MIN_TEST_CASE_FIELD_COUNT = 8
RUNTIME_METADATA_FIELD_ALIASES = (
    ("Название", "Title"),
    ("Тип", "Type"),
    ("Приоритет", "Priority"),
    ("package_id",),
    ("Трассировка", "Traceability"),
)
RUNTIME_SECTION_FIELD_ALIASES = (
    ("Предусловия", "Preconditions"),
    ("Тестовые данные", "Test Data", "Test data"),
    ("Итоговый ожидаемый результат", "Ожидаемый результат", "Expected Result"),
    ("Постусловия", "Postconditions"),
)
TEST_CASE_ID_RE = re.compile(r"\bTC-[A-Za-z0-9_-]+\b")
ATOM_ID_RE = re.compile(r"\bATOM-\d{3,}\b")
SCOPED_ATOM_ID_RE = re.compile(r"[A-Z0-9-]+-ATOM-\d{3,}")
ANY_ATOM_ID_RE = re.compile(r"\b(?:[A-Z0-9-]+-)?ATOM-\d{3,}\b")
GAP_ID_RE = re.compile(r"\b(?:GAP-\d{3,}|coverage_gap:[a-z0-9][a-z0-9_-]*)\b")
DICT_ID_RE = re.compile(r"\bDICT-\d{3,}\b")
FINDING_ID_RE = re.compile(r"\b(?:USER-)?FINDING(?:-[A-Z]+)?-\d{3,}\b")
TEST_CASE_TRACEABILITY_TOKEN_RE = re.compile(
    r"\b(ATOM-\d{3,}|GSR\s+\d+|BSR\s+\d+|REQ[-\s]?\d+)\b|PDF",
    flags=re.IGNORECASE,
)
SOURCE_BACKED_TEST_CASE_REF_RE = re.compile(
    r"\b(?:[A-Z0-9-]+-)?ATOM-\d{3,}\b|\b(?:GSR|BSR)\s+\d+\b|\bREQ[-\s]?\d+\b",
    flags=re.IGNORECASE,
)
REQUIREMENT_CODE_RANGE_RE = re.compile(
    r"\b([A-ZА-Я]{2,10})\s*[-:]?\s*(\d+)\b\s*`?\s*(?:-|–|—)\s*`?\s*(?:\1\s*[-:]?\s*)?(\d+)\b",
    flags=re.IGNORECASE,
)
REQUIREMENT_CODE_TOKEN_RE = re.compile(r"\b([A-ZА-Я]{2,10})\s*[-:]?\s*(\d+)\b", flags=re.IGNORECASE)
NON_REQUIREMENT_CODE_PREFIXES = {
    "ATOM",
    "GAP",
    "SRC",
    "TC",
    "WP",
    "PDF",
    "PAGE",
    "P",
}
ALLOWED_COVERAGE_STATUSES = {"covered", "gap", "unclear"}
ALLOWED_COVERAGE_DIMENSIONS = {
    "role-permission",
    "status-lifecycle",
    "decision-table",
    "pairwise",
    "boundary",
    "equivalence",
    "dependency",
    "conditional-visibility",
    "api-server-validation",
    "integration",
    "security",
    "async",
    "persistence",
    "table-list",
    "file-upload",
    "calculation",
    "numeric",
    "date-time",
    "length",
    "scenario-use-case",
    "performance",
    "reliability",
    "compatibility",
    "usability",
    "accessibility-ui",
    "traceability",
    "expected-result",
    "atomarity",
    "format",
    "scope",
    "other",
}
APPLICABILITY_MATRIX_REQUIRED_COLUMNS = {
    "dimension",
    "applicable",
    "source_ref",
    "reason",
    "linked_atoms",
    "linked_test_cases",
    "gap_id",
}
RISK_PRIORITY_MAP_REQUIRED_COLUMNS = {
    "atom_id",
    "risk_level",
    "risk_factors",
    "source_ref",
    "required_priority",
    "linked_test_cases",
    "gap_id",
    "rationale",
}
SOURCE_ROW_INVENTORY_REQUIRED_COLUMNS = {
    "source_row_id",
    "package_id",
    "field_or_action",
    "source_ref",
    "requirement_codes",
    "in_scope",
    "mapped_atom_or_gap",
}
SOURCE_ROW_COMPLETENESS_MATRIX_REQUIRED_COLUMNS = {
    "source_row_id",
    "source_requirement_codes",
    "normalized_property_ids",
    "linked_atoms",
    "gap_ids",
    "coverage_decision",
}
SOURCE_NORMALIZATION_DIAGNOSTIC_COMPLETENESS_MATRIX_REQUIRED_COLUMNS = (
    SOURCE_ROW_COMPLETENESS_MATRIX_REQUIRED_COLUMNS | {"diagnostic_atom_status"}
)
SOURCE_NORMALIZATION_DIAGNOSTIC_NORMALIZATION_REQUIRED_COLUMNS = {
    "source_column",
    "source_text_fragment",
}
SOURCE_NORMALIZATION_DIAGNOSTIC_REQUIRED_SECTIONS = {
    "Source Row Completeness Matrix",
    "Source Table Normalization",
    "Self-check",
}
TEST_DESIGN_DECISION_TABLE_REQUIRED_COLUMNS = {
    "decision_id",
    "package_id",
    "source_property_id",
    "linked_atom_id",
    "property_type",
    "decision",
    "decision_reason",
    "planned_tc_or_gap",
    "oracle_source",
    "must_be_executable",
    "review_risk",
}
COVERAGE_OBLIGATION_TABLE_REQUIRED_COLUMNS = {
    "obligation_id",
    "package_id",
    "source_property_id",
    "linked_atom_id",
    "property_type",
    "obligation_class",
    "required_behavior",
    "source_ref",
    "planned_tc_or_gap",
    "status",
    "review_notes",
}
DICTIONARY_INVENTORY_REQUIRED_COLUMNS = {
    "dictionary_id",
    "dictionary_name",
    "source_file",
    "source_location",
    "extraction_status",
    "active_values",
    "archived_values",
    "used_by_source_properties",
    "gap_id",
}
COVERAGE_OBLIGATION_REQUIRED_CLASSES_BY_PROPERTY_TYPE = {
    "numeric-format": (
        "valid-digits",
        "reject-letters",
        "reject-spaces",
        "reject-special-chars",
        "reject-decimal-separator",
        "reject-sign",
    ),
    "text-symbol-restriction": (
        "valid-letters",
        "valid-letters-hyphen",
        "reject-digits",
        "reject-special-chars-other-than-hyphen",
    ),
    "text-format": (
        "valid-letters",
        "valid-letters-hyphen",
        "reject-digits",
        "reject-special-chars-other-than-hyphen",
    ),
    "allowed-symbols": (
        "valid-letters",
        "valid-letters-hyphen",
        "reject-digits",
        "reject-special-chars-other-than-hyphen",
    ),
    "amount-tags": (
        "dictionary-values-shown",
        "tag-selection-fills-field",
    ),
    "format-mask": (
        "mask-pattern-applied",
    ),
    "mask-format": (
        "mask-pattern-applied",
    ),
    "default-mask": (
        "default-mask-visible",
    ),
    "маска-формата": (
        "mask-pattern-applied",
    ),
    "формат-маска": (
        "mask-pattern-applied",
    ),
    "маска-по-умолчанию": (
        "default-mask-visible",
    ),
    "date-passport-validity": (
        "passport-before-14-rejected",
        "passport-14-to-20-plus-45-window",
        "passport-20-plus-1-to-45-plus-45-window",
        "passport-45-plus-indefinite-window",
    ),
    "date-validity-window": (
        "lower-boundary-accepted",
        "upper-boundary-accepted",
        "off-boundary-rejected",
    ),
    "hint-behavior": (
        "hint-triggered",
        "hint-cleared",
    ),
    "validation-message": (
        "message-triggered",
    ),
    "red-highlight": (
        "highlight-triggered",
    ),
    "action-confirmation": (
        "confirmation-message-shown",
        "confirmation-accept-continues",
        "confirmation-cancel-stays",
    ),
    "action-navigation": (
        "navigation-target-opened",
    ),
    "address-required-components": (
        "region-and-house-required",
        "missing-apartment-or-private-house-hint",
    ),
}
COVERAGE_OBLIGATION_ALLOWED_STATUSES = {
    "covered",
    "gap",
    "unclear",
    "blocked",
    "not-applicable",
    "n/a",
}
ALLOWED_TEST_DESIGN_DECISIONS = {
    "standalone_tc",
    "covered_by_existing_tc",
    "gap_unclear",
    "metadata_only",
    "scenario_only",
    "out_of_scope",
}
ARTIFICIAL_NUMERIC_PROPERTY_TYPES = {
    "non-digit-rejection",
    "numeric-format-invalid",
    "numeric-negative",
}
DASH_PLACEHOLDER_VALUES = {"-", "—", "n/a", "na", "not applicable", "not-applicable"}
TRACEABILITY_PLACEHOLDER_COLUMNS_BY_SECTION = {
    "Atomic Requirements Ledger": {
        "req_id",
        "covered_by_tc",
        "gap_id",
        "gap_note",
    },
    "Test Design Decision Table": {
        "planned_tc_or_gap",
        "blocked_part",
        "gap_admissibility",
    },
    "Coverage Obligation Table": {
        "planned_tc_or_gap",
        "review_notes",
    },
    "Package Test Design Plan": {
        "planned_tc_or_gap",
        "oracle_source",
    },
    "Test-design Applicability Matrix": {
        "linked_test_cases",
        "gap_id",
    },
    "Dependency Matrix": {
        "tc_gap",
        "gap_id",
    },
    "Source Row Inventory": {
        "requirement_codes",
        "mapped_atom_or_gap",
    },
    "Source Row Completeness Matrix": {
        "gap_ids",
    },
    "Source Table Normalization": {
        "requirement_code",
        "gap_id",
        "linked_atoms",
    },
    "Risk / Priority Map": {
        "linked_test_cases",
        "gap_id",
    },
    "Writer Quality Gate": {
        "required_action",
    },
    "Test Design Review": {
        "required_action",
    },
}
TRACEABILITY_MATRIX_PLACEHOLDER_COLUMNS = {
    "req_id",
    "covered_by_tc",
    "gap_note",
}
SPLIT_TEST_DESIGN_SECTION_FILES = {
    "Artifact Write Strategy": "artifact-write-strategy.md",
    "Mockup Usage": "mockup-usage.md",
    "Source Row Inventory": "source-row-inventory.md",
    "Source Row Completeness Matrix": "source-row-completeness-matrix.md",
    "Source Table Normalization": "source-table-normalization.md",
    "Test Design Decision Table": "test-design-decision-table.md",
    "Coverage Obligation Table": "coverage-obligation-table.md",
    "Dictionary Inventory": "dictionary-inventory.md",
    "Atomic Requirements Ledger": "atomic-requirements-ledger.md",
    "Internal Work Package Coverage": "internal-work-package-coverage.md",
    "Package Ledger Self-Check": "package-ledger-self-check.md",
    "Package Test Design Plan": "package-test-design-plan.md",
    "Package Design Plan Self-Check": "package-design-plan-self-check.md",
    "Test Design Review": "test-design-review.md",
    "Dependency Matrix": "dependency-matrix.md",
    "Test-design Applicability Matrix": "test-design-applicability-matrix.md",
    "Risk / Priority Map": "risk-priority-map.md",
    "Combinatorial Coverage Table": "combinatorial-coverage-table.md",
    "Coverage Map": "coverage-map.md",
    "Coverage Gaps": "coverage-gaps.md",
    "Writer Quality Gate": "writer-quality-gate.md",
    "Writer Self-Check": "writer-self-check.md",
}
SPLIT_TEST_DESIGN_SECTIONS = frozenset(SPLIT_TEST_DESIGN_SECTION_FILES)
REQUIRED_TEST_CASE_TEMPLATE_FIELDS = {
    "source link": ["Traceability", "Трассировка", "FT Reference", "Ссылка на ФТ"],
}
TRACEABILITY_REMAP_TEST_CASE_TYPES = {"traceability-remap"}
TRACEABILITY_REMAP_TEXT_RE = re.compile(
    r"traceability[-\s]?remap|compatibility\s+(?:anchor|section)|"
    r"not\s+(?:a\s+)?standalone\s+(?:executable\s+)?(?:check|coverage|tc)|"
    r"does\s+not\s+create\s+(?:a\s+)?separate\s+standalone|"
    r"covered\s+within|remapped\s+to|canonical\s+coverage\s+is|"
    r"не\s+созда[её]т\s+.*самостоятельн|не\s+является\s+.*самостоятельн",
    flags=re.IGNORECASE,
)
SOURCE_PROPERTY_ID_RE = re.compile(r"\bSRC-[A-Za-z0-9_-]+\.P\d+\b", flags=re.IGNORECASE)
DIAGNOSTIC_PLACEHOLDER_GAP_RE = re.compile(r"\bGAP-900\b", flags=re.IGNORECASE)
GSR_ONLY_EXPECTED_BEHAVIOR_RE = re.compile(
    r"\b(?:follows|per|according\s+to|as\s+described\s+in)\s+GSR\b|"
    r"\b(?:по|согласно)\s+GSR\b|"
    r"\bGSR\s+\d+\b\s*(?:rule|requirement|требовани[ея])",
    flags=re.IGNORECASE,
)
INTEGRATION_OR_INTERNAL_PROPERTY_RE = re.compile(
    r"\b(?:integration|api|backend|internal|model|database|db|rabbitmq|async|persistence|kladr|dadata)\b",
    flags=re.IGNORECASE,
)
OBSERVABLE_BEHAVIOR_RE = re.compile(
    r"\b(?:displayed|shown|visible|hint|message|screen|form|button|opened|click|"
    r"decomposed|manual\s+input\s+block|fills?\s+[^|]{0,80}fields?)\b|"
    r"(?:отображ|видим|подсказ|сообщен|экран|форма|кнопк|открыва|расклад|заполня)",
    flags=re.IGNORECASE,
)
GAP_ADMISSIBILITY_VISIBLE_RESULT_RE = re.compile(
    r"\b(?:displayed|shown|visible|hint|message|notification|toast|modal|screen|"
    r"button|opened|closed|red|highlighted|required|mandatory|validation|"
    r"error|warning|tooltip|mask|tag|dictionary|confirmation|confirm|cancel|"
    r"navigate|navigation)\b|"
    r"(?:отображ|показыва|видим|скрыва|подсказ|сообщен|уведомлен|ошибк|"
    r"предупрежден|подсвеч|красн|обязател|валидац|маск|шаблон|"
    r"справочн|подтверждени|отмен|переход|открыва|закрыва)|\bтег[а-я]*\b",
    flags=re.IGNORECASE,
)
GAP_ADMISSIBILITY_EXECUTABLE_PROPERTY_RE = re.compile(
    r"hint[-_ ]?behavior|validation[-_ ]?message|red[-_ ]?highlight|"
    r"action[-_ ]?(?:confirmation|exit)|conditional[-_ ]?visibility|"
    r"format[-_ ]?mask|default[-_ ]?mask|amount[-_ ]?tags|dictionary[-_ ]?(?:closed[-_ ]?set|source|values)|"
    r"date[-_ ]?(?:passport[-_ ]?)?validity[-_ ]?window|date[-_ ]?passport[-_ ]?validity|"
    r"address[-_ ]?required[-_ ]?components|visible[-_ ]?result|"
    r"подсказ|сообщен|подсвет|маск|справочник|\bтег[а-я]*\b|"
    r"дата[^|]{0,40}паспорт|паспорт[^|]{0,40}дат|"
    r"обязательн[^|]{0,40}адрес|компонент[^|]{0,40}адрес|"
    r"действи[^|]{0,40}(?:подтверждени|выход)|условн[^|]{0,40}видим",
    flags=re.IGNORECASE,
)
GAP_ADMISSIBILITY_BLOCKER_RE = re.compile(
    r"\b(?:catalog|fixture|support\s+workbook|source\s+missing|not\s+available|"
    r"not\s+defined|unknown|backend|api|rabbitmq|model|database|db|kladr|dadata|"
    r"integration|internal|status|dictionary)\b|"
    r"(?:отсутств|не\s+найден|не\s+задан|не\s+указан|недоступ|нет\s+данных|"
    r"справочник|каталог|фикстур|статус|бэкенд|модель|интеграц|внутренн|клада?р|дадата)",
    flags=re.IGNORECASE,
)
PASSPORT_VALIDITY_WINDOW_RE = re.compile(
    r"(?:паспорт|passport).{0,160}(?:14|20|45|просроч|недействител)|"
    r"(?:14|20|45).{0,160}(?:паспорт|passport|просроч|недействител)|"
    r"date[-_ ]?passport[-_ ]?validity",
    flags=re.IGNORECASE | re.DOTALL,
)
HIGH_RISK_DIMENSION_CANDIDATES = {
    "role-permission",
    "status-lifecycle",
    "api-server-validation",
    "integration",
    "security",
    "file-upload",
    "calculation",
}
SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}
SOURCE_QUALITY_MAX_CHARS = 12000
PROMPT_REQUIRED_SECTION_GROUPS = {"goal", "inputs", "guardrails"}
PROMPT_SECTION_ALIASES = {
    "goal": {
        "цель этапа",
        "цель следующего этапа",
        "goal",
    },
    "inputs": {
        "входные артефакты",
        "входы",
        "inputs",
    },
    "actions": {
        "обязательные действия",
        "required actions",
        "required changes",
    },
    "guardrails": {
        "не делать",
        "ограничения",
        "guardrails",
        "constraints",
    },
    "outputs": {
        "ожидаемые выходы",
        "outputs",
    },
    "gate": {
        "gate завершения",
        "gate",
    },
}


@dataclass(frozen=True)
class Finding:
    id: str
    severity: str
    category: str
    title: str
    details: str
    path: str
    evidence: list[str]
    recommended_action: str


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    details: str
    path: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only validator for QA agent workflow artifacts."
    )
    parser.add_argument("--root", type=Path, default=ROOT_DIR)
    parser.add_argument("--json", action="store_true", dest="json_only")
    parser.add_argument("--text", action="store_true", dest="text_only")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fail-on", choices=("error", "warning"))
    parser.add_argument(
        "--source-quality-policy",
        choices=("compatible", "strict"),
        default="compatible",
        help=(
            "Select source quality severity policy. "
            "compatible keeps structural extraction risks as info; "
            "strict reports analyzer severities as warnings."
        ),
    )
    parser.add_argument(
        "--findings-policy",
        choices=("compatible", "strict"),
        default="compatible",
        help=(
            "Select reviewer findings severity policy. "
            "compatible records legacy traceability_ref gaps as info; "
            "strict reports them as warnings."
        ),
    )
    parser.add_argument(
        "--writer-response-policy",
        choices=("compatible", "strict"),
        default="compatible",
        help=(
            "Select writer response severity policy. "
            "compatible records legacy/noncanonical response gaps as info; "
            "strict reports them as warnings."
        ),
    )
    parser.add_argument(
        "--test-case-policy",
        choices=("compatible", "strict"),
        default="compatible",
        help=(
            "Select test-case artifact severity policy. "
            "compatible records structural test-case gaps and missing applicability matrices as info; "
            "strict reports them as warnings."
        ),
    )
    parser.add_argument(
        "--input-restriction-gap-policy",
        choices=("compatible", "diagnostic", "strict-canary", "writer-final", "production"),
        default="compatible",
        help=(
            "Select severity for source-backed input restrictions routed as gap-only. "
            "compatible/diagnostic keep legacy audit artifacts as warnings; "
            "strict-canary, writer-final and production report them as errors."
        ),
    )
    parser.add_argument(
        "--rolling-date-boundary-policy",
        choices=("compatible", "diagnostic", "strict-canary", "writer-final", "production"),
        default="compatible",
        help=(
            "Select severity for rolling/current-date boundary TC that uses static calendar dates. "
            "compatible/diagnostic keep legacy audit artifacts as warnings; "
            "strict-canary, writer-final and production report them as errors."
        ),
    )
    parser.add_argument(
        "--atomicity-coverage-policy",
        choices=("compatible", "diagnostic", "strict-canary", "writer-final", "production"),
        default="compatible",
        help=(
            "Select severity for TC atomicity and representative/pairwise coverage strategy gates. "
            "compatible/diagnostic keep legacy audit artifacts as warnings; "
            "strict-canary, writer-final and production report them as errors."
        ),
    )
    parser.add_argument(
        "--reviewer-signoff-policy",
        choices=("compatible", "strict"),
        default="compatible",
        help=(
            "Select reviewer sign-off self-check severity policy. "
            "compatible records missing or invalid self-checks as info; "
            "strict reports them as warnings."
        ),
    )
    parser.add_argument(
        "--final-alias-policy",
        choices=("compatible", "strict"),
        default="compatible",
        help=(
            "Select completed reviewer-loop final artifact alias policy. "
            "compatible records missing final_* aliases as info; "
            "strict reports them as warnings."
        ),
    )
    parser.add_argument(
        "--session-log-policy",
        choices=("compatible", "strict", "audit"),
        default="compatible",
        help=(
            "Select session log severity policy. "
            "compatible records missing session logs as info; "
            "strict reports missing or malformed base session logs as warnings; "
            "audit also requires timeline, quality checkpoints and handoff notes."
        ),
    )
    parser.add_argument(
        "--decision-log-policy",
        choices=("compatible", "strict"),
        default="compatible",
        help=(
            "Select intermediate decision log policy. "
            "compatible validates decision logs when present; "
            "strict reports missing or malformed linked agent-decision-log.md artifacts as warnings."
        ),
    )
    return parser.parse_args()


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_scalar(value: str) -> Any:
    value = strip_quotes(value.strip())
    lowered = value.lower()
    if lowered in {"null", "none", "~"}:
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def parse_workflow_state(path: Path) -> dict[str, Any]:
    state: dict[str, Any] = {}
    current_key: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        raw_line = raw_line.lstrip("\ufeff")
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        top_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):(?:\s*(.*))?$", raw_line)
        if top_match:
            key, raw_value = top_match.groups()
            current_key = key
            if raw_value:
                state[key] = parse_scalar(raw_value)
            else:
                state[key] = []
            continue

        if current_key is None or not raw_line.startswith(" "):
            continue

        stripped = raw_line.strip()
        current_value = state.get(current_key)

        if stripped.startswith("- "):
            if not isinstance(current_value, list):
                current_value = []
                state[current_key] = current_value
            current_value.append(parse_scalar(stripped[2:]))
            continue

        nested_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):(?:\s*(.*))?$", stripped)
        if nested_match:
            if not isinstance(current_value, dict):
                current_value = {}
                state[current_key] = current_value
            nested_key, raw_value = nested_match.groups()
            current_value[nested_key] = parse_scalar(raw_value) if raw_value else {}

    return state


def iter_workflow_states(root: Path) -> list[Path]:
    if root.is_file() and root.name == "workflow-state.yaml":
        return [root]
    if (root / "fts").is_dir():
        return sorted((root / "fts").rglob("workflow-state.yaml"))
    return sorted(root.rglob("workflow-state.yaml"))


def iter_session_cycle_states(root: Path) -> list[Path]:
    if root.is_file() and root.name == "cycle-state.yaml":
        return [root]
    if (root / "cycle-state.yaml").is_file():
        return [root / "cycle-state.yaml"]
    scope = validation_scope(root)
    return sorted(
        path
        for path in scope.rglob("work/review-cycles/*/cycle-state.yaml")
        if "versions" not in path.parts
    )


def find_authoritative_session_cycle_state(
    workflow_state: dict[str, Any],
    workflow_path: Path,
    root: Path,
    ft_root: Path,
) -> tuple[Path, dict[str, Any]] | None:
    scope_slug = workflow_state.get("scope_slug")
    if not isinstance(scope_slug, str) or not scope_slug:
        return None

    candidate_values = [
        value
        for value in flatten_string_values(workflow_state.get("latest_artifacts"))
        if Path(strip_quotes(value)).name == "cycle-state.yaml"
    ]
    candidates = [
        resolved
        for value in candidate_values
        for resolved in [resolve_artifact_path(value, workflow_path, root, ft_root)]
        if resolved is not None
    ]
    candidates.append(ft_root / "work" / "review-cycles" / scope_slug / "cycle-state.yaml")

    try:
        workflow_mtime = workflow_path.stat().st_mtime
    except OSError:
        workflow_mtime = 0.0

    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen or not candidate.exists() or candidate == workflow_path:
            continue
        seen.add(candidate)
        try:
            if candidate.stat().st_mtime < workflow_mtime:
                continue
            cycle_state = parse_workflow_state(candidate)
        except (OSError, UnicodeDecodeError):
            continue
        if cycle_state.get("scope_slug") != scope_slug:
            continue
        workflow_ft_slug = workflow_state.get("ft_slug")
        if isinstance(workflow_ft_slug, str) and cycle_state.get("ft_slug") != workflow_ft_slug:
            continue
        if cycle_state.get("stage_status") not in SESSION_BASED_REVIEW_CYCLE_STATUSES:
            continue
        return candidate, cycle_state

    return None


def validate_session_cycle_state_artifacts(
    path: Path,
    root: Path,
) -> tuple[list[Finding], list[Check]]:
    display_path = rel(path, root)
    findings: list[Finding] = []
    checks: list[Check] = []
    try:
        state = parse_workflow_state(path)
    except UnicodeDecodeError as exc:
        findings.append(
            Finding(
                id="session-cycle-state-unreadable",
                severity="error",
                category="workflow-state",
                title="cycle-state.yaml is not readable as UTF-8",
                details=str(exc),
                path=display_path,
                evidence=[],
                recommended_action="Save cycle-state.yaml as UTF-8.",
            )
        )
        checks.append(Check("session-cycle-state-artifacts", "fail", "cycle-state.yaml is unreadable.", display_path))
        return findings, checks

    stage_status = str(state.get("stage_status") or "")
    canonical_ref = strip_quotes(str(state.get("canonical_test_cases") or ""))
    draft_ref = strip_quotes(str(state.get("draft_test_cases") or ""))
    ft_root = path.parents[3] if len(path.parents) > 3 else root
    canonical = resolve_artifact_path(canonical_ref, path, root, ft_root) if canonical_ref else None
    draft = resolve_artifact_path(draft_ref, path, root, ft_root) if draft_ref else None
    canonical_exists = canonical is not None and canonical.exists()
    draft_exists = draft is not None and draft.exists()
    explicitly_draft = str(state.get("draft_or_unsigned") or "").lower() in {"true", "yes", "1"}
    signed_off = stage_status == "signed-off"

    if canonical_exists and not signed_off and not draft_exists and not explicitly_draft:
        severity = "warning"
        check_status = "warn"
        finding_id = "unsigned-draft-in-production-test-cases"
        title = "Unsigned writer draft is present under production test-cases"
        details = (
            "Session cycle is not signed off, but canonical_test_cases resolves under fts/**/test-cases/*.md "
            "without draft_test_cases or an explicit draft marker. This can make an unsigned writer draft look final."
        )
        if stage_status == "blocked-input":
            finding_id = "blocked-cycle-must-not-commit-final-artifact"
            title = "Blocked cycle exposes canonical test-case file as active artifact"
            details = (
                "A blocked-input cycle must not make a production test-case path look like an accepted final artifact. "
                "Move the unsigned draft into work/review-cycles/<cycle>/outputs/ and set draft_test_cases, "
                "or complete reviewer sign-off before keeping the production file."
            )
        findings.append(
            Finding(
                id=finding_id,
                severity=severity,
                category="workflow-state",
                title=title,
                details=details,
                path=display_path,
                evidence=[
                    f"stage_status={stage_status}",
                    f"canonical_test_cases={canonical_ref}",
                    f"draft_test_cases={draft_ref or '<missing>'}",
                ],
                recommended_action=(
                    "Move unsigned drafts to the cycle work outputs and set draft_test_cases, or promote to "
                    "canonical test-cases only after reviewer sign-off."
                ),
            )
        )
        checks.append(Check("session-cycle-unsigned-production-draft", check_status, title, display_path))
    else:
        checks.append(
            Check(
                "session-cycle-unsigned-production-draft",
                "pass",
                "No unsigned production test-case draft is exposed by this cycle.",
                display_path,
            )
        )

    return findings, checks


def validation_scope(root: Path) -> Path:
    if root.is_file():
        return root.parent
    if (root / "fts").is_dir():
        return root / "fts"
    return root


ROOT_LEVEL_HANDOFF_ARTIFACT_NAMES = {
    "workflow-state.yaml",
    "source-selection.md",
    "scope-options.md",
    "scope-selection-prompts.md",
    "source-locator-session-log.md",
    "scope-analyzer-session-log.md",
}


def iter_ft_package_roots(root: Path) -> list[Path]:
    if root.is_file():
        return []
    if root.parent.name == "fts" and ((root / "source").is_dir() or (root / "AGENT-NOTES.md").exists()):
        return [root]
    fts_root = root / "fts"
    if fts_root.is_dir():
        return sorted(
            package_root
            for package_root in fts_root.iterdir()
            if package_root.is_dir()
            and ((package_root / "source").is_dir() or (package_root / "AGENT-NOTES.md").exists())
        )
    return []


def validate_ft_package_handoff_layout(root: Path) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    package_roots = iter_ft_package_roots(root)
    if not package_roots:
        return findings, checks

    for package_root in package_roots:
        root_level_artifacts = sorted(
            artifact_name
            for artifact_name in ROOT_LEVEL_HANDOFF_ARTIFACT_NAMES
            if (package_root / artifact_name).exists()
        )
        root_level_handoff_artifacts = [
            artifact_name for artifact_name in root_level_artifacts if artifact_name != "workflow-state.yaml"
        ]
        display_path = rel(package_root, root)
        if root_level_handoff_artifacts:
            findings.append(
                Finding(
                    id="ft-package-root-level-handoff-artifacts",
                    severity="warning",
                    category="stage-transition",
                    title="FT package has root-level workflow handoff artifacts",
                    details=(
                        "Clean FT package workflow artifacts must live under "
                        "`work/stage-handoffs/NN-<scope-or-container>/`. Root-level handoff files can be missed by "
                        "downstream prompts, create competing workflow-state files, and contaminate clean eval runs."
                    ),
                    path=display_path,
                    evidence=[f"{display_path}/{artifact_name}" for artifact_name in root_level_artifacts],
                    recommended_action=(
                        "Move or recreate these files in `work/stage-handoffs/00-source-selection/` for source/scope "
                        "selection, or in the numbered scope handoff folder for confirmed scope work. Remove root-level copies."
                    ),
                )
            )
            checks.append(
                Check(
                    "ft-package-handoff-layout",
                    "warn",
                    "Root-level handoff artifacts found.",
                    display_path,
                )
            )
        else:
            checks.append(
                Check(
                    "ft-package-handoff-layout",
                    "pass",
                    "No root-level handoff artifacts found.",
                    display_path,
                )
            )
    return findings, checks


def iter_named_markdown(root: Path, name: str) -> list[Path]:
    if root.is_file() and root.name == name:
        return [root]
    return sorted(validation_scope(root).rglob(name))


def iter_traceability_matrices(root: Path) -> list[Path]:
    if root.is_file() and root.name.endswith("traceability-matrix.md"):
        return [root]
    return sorted(validation_scope(root).rglob("*traceability-matrix.md"))


def iter_review_findings(root: Path) -> list[Path]:
    if root.is_file() and re.fullmatch(r"round-\d+-findings\.md", root.name):
        return [root]
    return sorted(validation_scope(root).rglob("round-*-findings.md"))


def iter_writer_responses(root: Path) -> list[Path]:
    if root.is_file() and re.fullmatch(r"round-\d+-writer-response\.md", root.name):
        return [root]
    return sorted(validation_scope(root).rglob("round-*-writer-response.md"))


def iter_test_case_files(root: Path) -> list[Path]:
    if root.is_file() and root.suffix == ".md" and root.parent.name == "test-cases" and root.name != "README.md":
        return [root]
    if root.is_file() and root.suffix == ".md" and root.name.endswith("-draft.md"):
        return [root]
    scope = validation_scope(root)
    return sorted(
        {
            *(
                path
                for path in scope.rglob("test-cases/*.md")
                if path.name != "README.md"
            ),
            *(
                path
                for path in scope.rglob("work/review-cycles/*/outputs/*-draft.md")
                if "versions" not in path.parts
            ),
        }
    )


def iter_source_normalization_diagnostics(root: Path) -> list[Path]:
    return iter_named_markdown(root, "source-normalization-diagnostic.md")


def iter_writer_process_diagnostics(root: Path) -> list[Path]:
    if root.is_file() and root.suffix == ".md" and root.name.startswith("writer-process-diagnostic"):
        return [root]
    return sorted(validation_scope(root).rglob("writer-process-diagnostic*.md"))


def iter_writer_self_checks(root: Path) -> list[Path]:
    return iter_named_markdown(root, "writer-self-check.md")


def iter_session_logs(root: Path) -> list[Path]:
    if root.is_file() and root.suffix == ".md" and "session-log" in root.name.lower():
        return [root]
    return sorted(
        path
        for path in validation_scope(root).rglob("*session-log*.md")
        if path.is_file()
    )


def is_historical_or_scratch_artifact(path: Path) -> bool:
    return "versions" in path.parts or "_artifact_write" in path.parts


def is_active_text_artifact(path: Path, root: Path) -> bool:
    if path.suffix.lower() != ".md" or is_historical_or_scratch_artifact(path):
        return False

    relative_parts = rel(path, root).split("/")
    relative_text = "/".join(relative_parts)
    if "/work/review-cycles/" in f"/{relative_text}" and "/outputs/" in f"/{relative_text}/":
        return True
    if "/work/test-design/" in f"/{relative_text}/":
        return True
    if "/test-cases/" in f"/{relative_text}/" and path.parent.name == "test-cases":
        return path.name != "README.md"
    if "session-log" in path.name.lower():
        return True
    return False


def iter_active_text_artifacts(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if is_active_text_artifact(root, root.parent) else []
    return sorted(
        path
        for path in validation_scope(root).rglob("*.md")
        if path.is_file() and is_active_text_artifact(path, root)
    )


def is_canary_run_markdown(path: Path, root: Path) -> bool:
    if path.suffix.lower() != ".md" or is_historical_or_scratch_artifact(path):
        return False
    relative_text = f"/{rel(path, root)}/"
    return "/work/canary-runs/" in relative_text or "canary-runs" in path.parts


def iter_generated_source_basis_artifacts(root: Path) -> list[Path]:
    if root.is_file() and root.suffix.lower() == ".md":
        return [root]
    return sorted(
        path
        for path in validation_scope(root).rglob("*.md")
        if path.is_file() and is_canary_run_markdown(path, root)
    )


def iter_decision_logs(root: Path) -> list[Path]:
    if root.is_file() and root.suffix == ".md" and "decision-log" in root.name.lower():
        return [root]
    return sorted(
        path
        for path in validation_scope(root).rglob("*decision-log*.md")
        if path.is_file()
    )


ENCODING_DAMAGE_QUESTION_MARK_RE = re.compile(r"\?{4,}")
ENCODING_DAMAGE_DIAGNOSTIC_TERMS = {
    "encoding",
    "utf-8",
    "utf8",
    "mojibake",
    "question-mark",
    "question mark",
    "replacement character",
    "replacement-character",
    "кодиров",
}


def is_encoding_diagnostic_line(line: str) -> bool:
    lowered = line.lower()
    return any(term in lowered for term in ENCODING_DAMAGE_DIAGNOSTIC_TERMS)


def encoding_damage_markers(line: str) -> list[str]:
    markers: list[str] = []
    if "\ufffd" in line:
        markers.append("unicode-replacement-character")
    if ENCODING_DAMAGE_QUESTION_MARK_RE.search(line):
        markers.append("question-mark-run")
    return markers


def validate_text_encoding_damage(path: Path, root: Path) -> tuple[list[Finding], list[Check]]:
    display_path = rel(path, root)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as exc:
        return (
            [
                Finding(
                    id="active-text-artifact-not-utf8",
                    severity="warning",
                    category="source-quality",
                    title="Active text artifact is not valid UTF-8",
                    details=str(exc),
                    path=display_path,
                    evidence=[],
                    recommended_action="Rewrite the active artifact as UTF-8 Markdown before continuing the review cycle.",
                )
            ],
            [Check("active-text-encoding-damage", "warn", "Active text artifact is not valid UTF-8.", display_path)],
        )

    evidence: list[str] = []
    for line_number, line in enumerate(lines, start=1):
        markers = encoding_damage_markers(line)
        if not markers or is_encoding_diagnostic_line(line):
            continue
        evidence.append(f"line {line_number}: {', '.join(markers)}: {line[:160]}")
        if len(evidence) >= 5:
            break

    if evidence:
        return (
            [
                Finding(
                    id="active-text-artifact-encoding-damage",
                    severity="warning",
                    category="source-quality",
                    title="Active text artifact contains encoding damage markers",
                    details=(
                        "The active artifact contains replacement characters or long question-mark runs, "
                        "which usually means Russian source text was lost during stdout/file encoding."
                    ),
                    path=display_path,
                    evidence=evidence,
                    recommended_action=(
                        "Regenerate or repair the artifact from the original UTF-8/source document; do not use "
                        "the damaged text as requirement evidence, traceability, expected results or sign-off basis."
                    ),
                )
            ],
            [Check("active-text-encoding-damage", "warn", "Active text artifact contains encoding damage markers.", display_path)],
        )

    return [], [Check("active-text-encoding-damage", "pass", "Active text artifact has no encoding damage markers.", display_path)]


def iter_mockup_visual_inventories(root: Path) -> list[Path]:
    return iter_named_markdown(root, MOCKUP_VISUAL_INVENTORY_NAME)


def iter_dictionary_inventories(root: Path) -> list[Path]:
    return iter_named_markdown(root, DICTIONARY_INVENTORY_NAME)


def iter_source_table_normalizations(root: Path) -> list[Path]:
    if root.is_file() and root.name == "source-table-normalization.md":
        return [root]
    return []


def repository_root(root: Path) -> Path:
    base = root.parent if root.is_file() else root
    if base.name == "fts":
        return base.parent
    return base


def dedupe_paths(paths: list[Path]) -> list[Path]:
    deduped: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = path.resolve().as_posix()
        if key in seen:
            continue
        deduped.append(path)
        seen.add(key)
    return deduped


def iter_artifact_manifests(root: Path) -> list[Path]:
    if root.is_file() and root.name == "artifact-manifest.json":
        return [root]

    scope = validation_scope(root)
    base = repository_root(root)
    candidates = [base / "artifact-manifest.json", scope / "artifact-manifest.json"]
    candidates.extend(scope.rglob("artifact-manifest.json"))
    return sorted(path for path in dedupe_paths(candidates) if path.is_file())


def manifest_path_candidates(raw_path: str, root: Path, manifest_path: Path | None = None) -> list[Path]:
    value = strip_quotes(raw_path)
    if not value or value.startswith(("http://", "https://")):
        return []

    candidate = Path(value)
    if candidate.is_absolute():
        return [candidate]

    parents: list[Path] = [repository_root(root), validation_scope(root)]
    if manifest_path is not None:
        parents.append(manifest_path.parent)
    return dedupe_paths([parent / value for parent in parents])


def resolve_manifest_path(raw_path: str, root: Path, manifest_path: Path | None = None) -> Path | None:
    candidates = manifest_path_candidates(raw_path, root, manifest_path)
    if not candidates:
        return None
    return next((candidate for candidate in candidates if candidate.exists()), candidates[0])


def normalized_path(path: Path) -> str:
    return path.resolve().as_posix()


def ft_scope_key(path: Path, root: Path) -> str:
    base = repository_root(root).resolve()
    try:
        relative_parts = path.resolve().relative_to(base).parts
    except ValueError:
        relative_parts = path.resolve().parts

    if "fts" in relative_parts:
        index = relative_parts.index("fts")
        if index + 1 < len(relative_parts):
            return (base / Path(*relative_parts[: index + 2])).resolve().as_posix()
    return base.as_posix()


def extract_test_case_ids_from_text(value: str) -> list[str]:
    return sorted(set(TEST_CASE_ID_RE.findall(value)))


def extract_atom_ids_from_text(value: str) -> list[str]:
    return sorted(set(ATOM_ID_RE.findall(value)))


def extract_any_atom_ids_from_text(value: str) -> list[str]:
    return sorted(set(ANY_ATOM_ID_RE.findall(value)))


def extract_source_backed_test_case_refs(value: str) -> list[str]:
    return sorted(
        {
            re.sub(r"\s+", " ", match.group(0).strip().upper())
            for match in SOURCE_BACKED_TEST_CASE_REF_RE.finditer(value)
        }
    )


def extract_gap_ids_from_text(value: str) -> list[str]:
    return sorted(set(GAP_ID_RE.findall(value)))


def extract_finding_ids_from_text(value: str) -> list[str]:
    return sorted(set(FINDING_ID_RE.findall(value)))


def build_test_case_id_index(test_case_files: list[Path], root: Path) -> dict[str, set[str]]:
    index: dict[str, set[str]] = {}
    for path in test_case_files:
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        ids = {test_case_id for test_case_id, _ in extract_test_case_blocks(content)}
        if not ids:
            continue
        index.setdefault(ft_scope_key(path, root), set()).update(ids)
    return index


def ft_root_for_test_case_path(path: Path) -> Path | None:
    parts = path.parts
    if "test-cases" not in parts:
        return None

    test_cases_index = len(parts) - 1 - list(reversed(parts)).index("test-cases")
    if test_cases_index < 1:
        return None

    ft_root = Path(*parts[:test_cases_index])
    return ft_root


def split_test_design_dir_for_test_case(path: Path) -> Path | None:
    ft_root = ft_root_for_test_case_path(path)
    if ft_root is None:
        return None
    return ft_root / "work" / "test-design" / path.stem


def normalize_cycle_state_path(value: str) -> str:
    normalized = value.strip().strip("`'\"")
    normalized = normalized.replace("\\", "/").lstrip("./")
    return normalized.rstrip("/")


def cycle_state_values(path: Path, key: str) -> list[str]:
    values: list[str] = []
    collecting_list = False
    key_pattern = re.compile(rf"^{re.escape(key)}:\s*(.*)$")
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return values

    for line in lines:
        match = key_pattern.match(line)
        if match:
            collecting_list = False
            raw_value = match.group(1).strip()
            if not raw_value:
                collecting_list = True
                continue
            if raw_value == "[]":
                return []
            if raw_value.startswith("[") and raw_value.endswith("]"):
                return [
                    item.strip().strip("`'\"")
                    for item in raw_value.strip("[]").split(",")
                    if item.strip()
                ]
            return [raw_value.strip().strip("`'\"")]

        if collecting_list:
            if line.startswith("  - "):
                values.append(line[4:].strip().strip("`'\""))
                continue
            if line and not line.startswith(" "):
                break

    return values


@lru_cache(maxsize=None)
def cycle_state_test_design_dir_map(ft_root: Path) -> dict[str, tuple[Path, ...]]:
    review_cycles_dir = ft_root / "work" / "review-cycles"
    if not review_cycles_dir.is_dir():
        return {}

    mapped: dict[str, list[Path]] = defaultdict(list)
    for state_path in sorted(review_cycles_dir.glob("*/cycle-state.yaml")):
        canonical_paths = [
            normalize_cycle_state_path(value)
            for value in cycle_state_values(state_path, "canonical_test_cases")
        ]
        test_design_dirs = [
            normalize_cycle_state_path(value)
            for value in cycle_state_values(state_path, "test_design_dir")
        ]
        for canonical_path in canonical_paths:
            for test_design_dir in test_design_dirs:
                directory = ft_root / test_design_dir
                if directory not in mapped[canonical_path]:
                    mapped[canonical_path].append(directory)

    return {canonical_path: tuple(paths) for canonical_path, paths in mapped.items()}


def split_test_design_dirs_for_test_case(path: Path) -> list[Path]:
    ft_root = ft_root_for_test_case_path(path)
    candidates: list[Path] = []
    if ft_root is not None:
        try:
            canonical_rel = normalize_cycle_state_path(str(path.relative_to(ft_root)))
        except ValueError:
            canonical_rel = ""
        if canonical_rel:
            candidates.extend(cycle_state_test_design_dir_map(ft_root).get(canonical_rel, ()))

    stem_dir = split_test_design_dir_for_test_case(path)
    if stem_dir is not None:
        candidates.append(stem_dir)

    unique_candidates: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        unique_candidates.append(candidate)
    return unique_candidates


def split_test_design_artifact_paths(path: Path) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for directory in split_test_design_dirs_for_test_case(path):
        if not directory.is_dir():
            continue
        for section_title, file_name in SPLIT_TEST_DESIGN_SECTION_FILES.items():
            if section_title in paths:
                continue
            candidate = directory / file_name
            if candidate.is_file():
                paths[section_title] = candidate
    return paths


def collapse_redundant_section_heading(content: str, section_title: str) -> str:
    pattern = re.compile(
        rf"(^|\n)#\s+{re.escape(section_title)}\s*\n(?:[ \t]*\n)*"
        rf"##\s+{re.escape(section_title)}\s*(?=\n)",
        flags=re.IGNORECASE,
    )
    return pattern.sub(lambda match: f"{match.group(1)}## {section_title}", content)


def has_redundant_section_heading(content: str, section_title: str) -> bool:
    pattern = re.compile(
        rf"(^|\n)#\s+{re.escape(section_title)}\s*\n(?:[ \t]*\n)*"
        rf"##\s+{re.escape(section_title)}\s*(?=\n)",
        flags=re.IGNORECASE,
    )
    return pattern.search(content) is not None


def has_canonical_split_artifact_heading(content: str, section_title: str) -> bool:
    pattern = re.compile(
        rf"(?im)^#{{1,2}}\s+{re.escape(section_title)}\s*$",
    )
    return pattern.search(content) is not None


def validate_split_artifact_heading_shape(
    section_title: str,
    artifact_path: Path,
    root: Path,
) -> tuple[list[Finding], list[Check]]:
    display_path = rel(artifact_path, root)
    try:
        content = artifact_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return (
            [
                Finding(
                    id="split-artifact-not-utf8",
                    severity="warning",
                    category="test-case-format",
                    title="Split artifact is not valid UTF-8",
                    details=str(exc),
                    path=display_path,
                    evidence=[],
                    recommended_action="Save the split artifact as UTF-8 Markdown.",
                )
            ],
            [Check("split-artifact-heading-shape", "warn", "Split artifact is not UTF-8.", display_path)],
        )

    if has_redundant_section_heading(content, section_title):
        return (
            [
                Finding(
                    id="split-artifact-redundant-section-heading",
                    severity="warning",
                    category="test-case-format",
                    title="Split artifact has redundant duplicate section headings",
                    details=(
                        "A split artifact must expose exactly one canonical section heading. Adjacent `# Section` and "
                        "`## Section` wrappers create ambiguous section extraction and should be normalized at write time."
                    ),
                    path=display_path,
                    evidence=[f"# {section_title} + ## {section_title}"],
                    recommended_action=(
                        f"Keep only one canonical heading, `# {section_title}` or `## {section_title}`, "
                        "before the table/body."
                    ),
                )
            ],
            [Check("split-artifact-heading-shape", "warn", "Split artifact has redundant headings.", display_path)],
        )

    if has_canonical_split_artifact_heading(content, section_title):
        return (
            [],
            [Check("split-artifact-heading-shape", "pass", "Split artifact heading shape passed.", display_path)],
        )

    return (
        [
            Finding(
                id="split-artifact-canonical-heading-missing",
                severity="warning",
                category="test-case-format",
                title="Split artifact misses canonical section heading",
                details=(
                    "A split artifact must expose exactly one canonical section heading using `# Section` or "
                    "`## Section`. Other heading text or a bare table makes split artifact shape ambiguous."
                ),
                path=display_path,
                evidence=[f"expected `# {section_title}` or `## {section_title}`"],
                recommended_action=f"Add one canonical heading, `# {section_title}` or `## {section_title}`, before the table/body.",
            )
        ],
        [Check("split-artifact-heading-shape", "warn", "Split artifact misses canonical heading.", display_path)],
    )


def normalize_split_test_design_section(section_title: str, content: str) -> str:
    content = collapse_redundant_section_heading(content, section_title)
    if extract_markdown_section(content, section_title) is not None:
        return content.strip()

    h1_pattern = re.compile(
        rf"^#\s+{re.escape(section_title)}\s*$",
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if h1_pattern.search(content):
        return h1_pattern.sub(f"## {section_title}", content, count=1).strip()

    return f"## {section_title}\n\n{content.strip()}".strip()


def test_case_validation_content(path: Path, root: Path) -> str:
    content = path.read_text(encoding="utf-8")
    split_sections: list[str] = []
    for section_title, artifact_path in split_test_design_artifact_paths(path).items():
        if extract_markdown_section(content, section_title) is not None:
            continue
        artifact_content = artifact_path.read_text(encoding="utf-8")
        split_sections.append(normalize_split_test_design_section(section_title, artifact_content))

    if not split_sections:
        return content

    return (
        content.rstrip()
        + "\n\n"
        + "<!-- Split canonical test-design artifacts appended for validation context. -->"
        + "\n\n"
        + "\n\n".join(split_sections)
        + "\n"
    )


def duplicate_split_sections_in_test_case(content: str, path: Path) -> list[str]:
    if not split_test_design_artifact_paths(path):
        return []

    duplicated: list[str] = []
    for section_title in SPLIT_TEST_DESIGN_SECTIONS:
        section = extract_markdown_section(content, section_title)
        if section is None:
            continue
        if markdown_table_rows_from_text(section):
            duplicated.append(section_title)
    return sorted(duplicated)


def known_test_case_ids_for_artifact(
    path: Path,
    root: Path,
    test_case_id_index: dict[str, set[str]],
) -> set[str]:
    if not test_case_id_index:
        return set()

    scoped_ids = test_case_id_index.get(ft_scope_key(path, root), set())
    if scoped_ids:
        return scoped_ids
    if len(test_case_id_index) == 1:
        return set(next(iter(test_case_id_index.values())))
    return set()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_manifest_file_metadata(
    artifact_id: str,
    path: Path,
    artifact: dict[str, Any],
    display_path: str,
) -> list[Finding]:
    findings: list[Finding] = []

    expected_size = artifact.get("size_bytes")
    if expected_size is not None:
        if not isinstance(expected_size, int):
            findings.append(
                Finding(
                    id="artifact-manifest-invalid-size",
                    severity="error",
                    category="artifact-manifest",
                    title="Artifact manifest size_bytes is not an integer",
                    details=f"Artifact {artifact_id!r} has non-integer size_bytes.",
                    path=display_path,
                    evidence=[str(expected_size)],
                    recommended_action="Set size_bytes to the file size in bytes or remove the field.",
                )
            )
        elif path.stat().st_size != expected_size:
            findings.append(
                Finding(
                    id="artifact-manifest-size-mismatch",
                    severity="error",
                    category="artifact-manifest",
                    title="Artifact manifest size does not match the file",
                    details=f"Artifact {artifact_id!r} points to a file with a different size.",
                    path=display_path,
                    evidence=[f"expected={expected_size}", f"actual={path.stat().st_size}", path.as_posix()],
                    recommended_action="Update the manifest metadata or replace the stale artifact.",
                )
            )

    expected_hash = artifact.get("sha256")
    if expected_hash is not None:
        if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_hash):
            findings.append(
                Finding(
                    id="artifact-manifest-invalid-sha256",
                    severity="error",
                    category="artifact-manifest",
                    title="Artifact manifest sha256 is invalid",
                    details=f"Artifact {artifact_id!r} has an invalid sha256 value.",
                    path=display_path,
                    evidence=[str(expected_hash)],
                    recommended_action="Use a 64-character hexadecimal SHA-256 digest or remove the field.",
                )
            )
        else:
            actual_hash = sha256_file(path)
            if actual_hash.lower() != expected_hash.lower():
                findings.append(
                    Finding(
                        id="artifact-manifest-sha256-mismatch",
                        severity="error",
                        category="artifact-manifest",
                        title="Artifact manifest checksum does not match the file",
                        details=f"Artifact {artifact_id!r} points to a file with a different SHA-256 digest.",
                        path=display_path,
                        evidence=[f"expected={expected_hash.lower()}", f"actual={actual_hash}", path.as_posix()],
                        recommended_action="Update the manifest metadata or replace the stale artifact.",
                    )
                )

    return findings


def validate_artifact_manifest(path: Path, root: Path) -> tuple[list[Finding], list[Check], set[str]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    declared_paths: set[str] = set()
    display_path = rel(path, root)

    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        findings.append(
            Finding(
                id="artifact-manifest-unreadable",
                severity="error",
                category="artifact-manifest",
                title="artifact-manifest.json is not readable JSON",
                details=str(exc),
                path=display_path,
                evidence=[],
                recommended_action="Save artifact-manifest.json as UTF-8 JSON.",
            )
        )
        checks.append(Check("artifact-manifest", "fail", "Manifest is not readable JSON.", display_path))
        return findings, checks, declared_paths

    if not isinstance(manifest, dict):
        findings.append(
            Finding(
                id="artifact-manifest-invalid-root",
                severity="error",
                category="artifact-manifest",
                title="Artifact manifest root must be an object",
                details="The manifest must contain top-level metadata and an artifacts array.",
                path=display_path,
                evidence=[],
                recommended_action="Use the schema from references/agent/artifact-manifest-format.md.",
            )
        )
        checks.append(Check("artifact-manifest", "fail", "Manifest root is invalid.", display_path))
        return findings, checks, declared_paths

    if manifest.get("manifest_version") != 1:
        findings.append(
            Finding(
                id="artifact-manifest-invalid-version",
                severity="error",
                category="artifact-manifest",
                title="Artifact manifest version is unsupported",
                details="Only manifest_version 1 is supported.",
                path=display_path,
                evidence=[str(manifest.get("manifest_version"))],
                recommended_action="Set manifest_version to 1 or update the validator before using a new schema.",
            )
        )

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        findings.append(
            Finding(
                id="artifact-manifest-missing-artifacts",
                severity="error",
                category="artifact-manifest",
                title="Artifact manifest does not contain an artifacts list",
                details="The manifest cannot declare canonical artifacts or aliases without an artifacts array.",
                path=display_path,
                evidence=[],
                recommended_action="Add an artifacts array.",
            )
        )
        checks.append(Check("artifact-manifest", "fail", "Manifest artifacts list is missing.", display_path))
        return findings, checks, declared_paths

    seen_ids: set[str] = set()
    for index, artifact in enumerate(artifacts):
        artifact_label = f"artifacts[{index}]"
        if not isinstance(artifact, dict):
            findings.append(
                Finding(
                    id="artifact-manifest-invalid-artifact",
                    severity="error",
                    category="artifact-manifest",
                    title="Artifact manifest entry must be an object",
                    details=f"{artifact_label} is not an object.",
                    path=display_path,
                    evidence=[str(artifact)],
                    recommended_action="Represent each artifact as an object with id, role, export_policy, and path fields.",
                )
            )
            continue

        artifact_id = artifact.get("id")
        artifact_id_text = artifact_id if isinstance(artifact_id, str) and artifact_id else artifact_label
        if not isinstance(artifact_id, str) or not artifact_id:
            findings.append(
                Finding(
                    id="artifact-manifest-missing-id",
                    severity="error",
                    category="artifact-manifest",
                    title="Artifact manifest entry has no id",
                    details=f"{artifact_label} must have a stable id.",
                    path=display_path,
                    evidence=[],
                    recommended_action="Add a stable artifact id.",
                )
            )
        elif artifact_id in seen_ids:
            findings.append(
                Finding(
                    id="artifact-manifest-duplicate-id",
                    severity="error",
                    category="artifact-manifest",
                    title="Artifact manifest contains duplicate ids",
                    details=f"Artifact id {artifact_id!r} is declared more than once.",
                    path=display_path,
                    evidence=[artifact_id],
                    recommended_action="Use unique artifact ids.",
                )
            )
        else:
            seen_ids.add(artifact_id)

        role = artifact.get("role")
        if not isinstance(role, str) or not role:
            findings.append(
                Finding(
                    id="artifact-manifest-missing-role",
                    severity="error",
                    category="artifact-manifest",
                    title="Artifact manifest entry has no role",
                    details=f"Artifact {artifact_id_text!r} must declare its role.",
                    path=display_path,
                    evidence=[],
                    recommended_action="Add a short role such as main-ft-docx, support-docx, or ui-evidence-output.",
                )
            )

        policy = artifact.get("export_policy")
        if policy not in ALLOWED_ARTIFACT_EXPORT_POLICIES:
            findings.append(
                Finding(
                    id="artifact-manifest-invalid-export-policy",
                    severity="error",
                    category="artifact-manifest",
                    title="Artifact manifest has an unsupported export_policy",
                    details=f"Artifact {artifact_id_text!r} uses unsupported export_policy {policy!r}.",
                    path=display_path,
                    evidence=[str(policy)],
                    recommended_action="Use one of the canonical export_policy values.",
                )
            )

        canonical_raw = artifact.get("canonical_path")
        canonical_path: Path | None = None
        if isinstance(canonical_raw, str) and canonical_raw:
            canonical_path = resolve_manifest_path(canonical_raw, root, path)
            if canonical_path is not None:
                declared_paths.add(normalized_path(canonical_path))
        elif policy != "not-collected":
            findings.append(
                Finding(
                    id="artifact-manifest-missing-canonical-path",
                    severity="error",
                    category="artifact-manifest",
                    title="Artifact manifest entry has no canonical_path",
                    details=f"Artifact {artifact_id_text!r} needs a canonical_path unless it is not-collected.",
                    path=display_path,
                    evidence=[],
                    recommended_action="Add canonical_path or use export_policy not-collected.",
                )
            )

        if policy in REPO_TRACKED_ARTIFACT_POLICIES:
            if canonical_path is None or not canonical_path.exists():
                findings.append(
                    Finding(
                        id="artifact-manifest-canonical-path-missing",
                        severity="error",
                        category="artifact-manifest",
                        title="Artifact manifest canonical_path is missing",
                        details=f"Artifact {artifact_id_text!r} points to a missing repo-tracked artifact.",
                        path=display_path,
                        evidence=[str(canonical_raw)],
                        recommended_action="Restore the artifact or update the manifest path.",
                    )
                )
            elif not canonical_path.is_file():
                findings.append(
                    Finding(
                        id="artifact-manifest-canonical-path-not-file",
                        severity="error",
                        category="artifact-manifest",
                        title="Artifact manifest canonical_path is not a file",
                        details=f"Artifact {artifact_id_text!r} uses a file policy for a non-file path.",
                        path=display_path,
                        evidence=[canonical_path.as_posix()],
                        recommended_action="Use a file path or change export_policy for directory/local evidence.",
                    )
                )
            else:
                findings.extend(validate_manifest_file_metadata(artifact_id_text, canonical_path, artifact, display_path))

        aliases = artifact.get("aliases", [])
        if aliases is None:
            aliases = []
        if not isinstance(aliases, list):
            findings.append(
                Finding(
                    id="artifact-manifest-invalid-aliases",
                    severity="error",
                    category="artifact-manifest",
                    title="Artifact manifest aliases must be a list",
                    details=f"Artifact {artifact_id_text!r} has non-list aliases.",
                    path=display_path,
                    evidence=[str(aliases)],
                    recommended_action="Use an aliases array or remove the field.",
                )
            )
            continue

        canonical_hash = sha256_file(canonical_path) if canonical_path and canonical_path.is_file() else None
        for alias_raw in aliases:
            if not isinstance(alias_raw, str) or not alias_raw:
                findings.append(
                    Finding(
                        id="artifact-manifest-invalid-alias-path",
                        severity="error",
                        category="artifact-manifest",
                        title="Artifact manifest alias path is invalid",
                        details=f"Artifact {artifact_id_text!r} contains an invalid alias path.",
                        path=display_path,
                        evidence=[str(alias_raw)],
                        recommended_action="Use non-empty string paths in aliases.",
                    )
                )
                continue

            alias_path = resolve_manifest_path(alias_raw, root, path)
            if alias_path is not None:
                declared_paths.add(normalized_path(alias_path))

            if policy in REPO_TRACKED_ARTIFACT_POLICIES:
                if alias_path is None or not alias_path.exists():
                    findings.append(
                        Finding(
                            id="artifact-manifest-alias-path-missing",
                            severity="error",
                            category="artifact-manifest",
                            title="Artifact manifest alias path is missing",
                            details=f"Artifact {artifact_id_text!r} declares a missing alias.",
                            path=display_path,
                            evidence=[alias_raw],
                            recommended_action="Restore the alias copy or remove the stale alias.",
                        )
                    )
                elif not alias_path.is_file():
                    findings.append(
                        Finding(
                            id="artifact-manifest-alias-path-not-file",
                            severity="error",
                            category="artifact-manifest",
                            title="Artifact manifest alias path is not a file",
                            details=f"Artifact {artifact_id_text!r} declares a non-file alias.",
                            path=display_path,
                            evidence=[alias_path.as_posix()],
                            recommended_action="Use file aliases only for repo-tracked artifacts.",
                        )
                    )
                elif canonical_hash is not None and sha256_file(alias_path) != canonical_hash:
                    findings.append(
                        Finding(
                            id="artifact-manifest-alias-sha256-mismatch",
                            severity="error",
                            category="artifact-manifest",
                            title="Artifact manifest alias content differs from canonical artifact",
                            details=f"Artifact {artifact_id_text!r} declares an alias with different bytes.",
                            path=display_path,
                            evidence=[alias_path.as_posix()],
                            recommended_action="Replace the alias copy or split it into a separate artifact entry.",
                        )
                    )

    manifest_errors = [finding for finding in findings if finding.severity == "error"]
    manifest_warnings = [finding for finding in findings if finding.severity == "warning"]
    checks.append(
        Check(
            "artifact-manifest",
            "fail" if manifest_errors else "warn" if manifest_warnings else "pass",
            "Manifest validation failed."
            if manifest_errors
            else "Manifest validation has warnings."
            if manifest_warnings
            else "Manifest metadata and declared aliases are valid.",
            display_path,
        )
    )
    return findings, checks, declared_paths


def iter_source_support_files(root: Path) -> list[Path]:
    scope = validation_scope(root)
    candidates = [root] if root.is_file() else scope.rglob("*")
    files: list[Path] = []
    for path in candidates:
        if not path.is_file() or path.suffix.lower() not in SOURCE_SUPPORT_EXTENSIONS:
            continue
        if path.name.startswith("~$"):
            continue
        if {"source", "support"}.isdisjoint({part.lower() for part in path.parts}):
            continue
        files.append(path)
    return sorted(files)


def validate_source_support_duplicates(root: Path, declared_paths: set[str]) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    files = iter_source_support_files(root)
    display_path = rel(validation_scope(root), root)

    by_hash: dict[str, list[Path]] = {}
    for path in files:
        try:
            digest = sha256_file(path)
        except OSError as exc:
            findings.append(
                Finding(
                    id="artifact-manifest-source-support-unreadable",
                    severity="warning",
                    category="artifact-manifest",
                    title="Source/support artifact could not be hashed",
                    details=str(exc),
                    path=rel(path, root),
                    evidence=[],
                    recommended_action="Check file permissions or remove the stale artifact.",
                )
            )
            continue
        by_hash.setdefault(digest, []).append(path)

    duplicate_groups = {
        digest: paths
        for digest, paths in by_hash.items()
        if len(paths) > 1
    }
    for digest, paths in sorted(duplicate_groups.items()):
        untracked = [
            path
            for path in paths
            if normalized_path(path) not in declared_paths
        ]
        if untracked:
            findings.append(
                Finding(
                    id="artifact-manifest-duplicate-untracked",
                    severity="warning",
                    category="artifact-manifest",
                    title="Duplicate source/support files are not declared in artifact manifest",
                    details=(
                        "The same bytes appear in multiple source/support paths. "
                        "Without a manifest, future changes can update one alias but not the other."
                    ),
                    path=display_path,
                    evidence=[f"sha256={digest}", *[rel(path, repository_root(root)) for path in paths]],
                    recommended_action="Declare the canonical artifact and aliases in fts/artifact-manifest.json.",
                )
            )

    checks.append(
        Check(
            "source-support-duplicate-manifest",
            "warn" if findings else "pass",
            "Some duplicate source/support files are not manifest-declared."
            if findings
            else "Duplicate source/support files are covered by artifact manifest or absent.",
            display_path,
        )
    )
    return findings, checks


def find_ft_root(path: Path, root: Path, state: dict[str, Any]) -> Path:
    ft_slug = state.get("ft_slug")
    if isinstance(ft_slug, str):
        candidate = root / "fts" / ft_slug
        if candidate.is_dir():
            return candidate

    parts = path.parts
    if "fts" in parts:
        index = parts.index("fts")
        if index + 1 < len(parts):
            return Path(*parts[: index + 2])

    return path.parent


def flatten_string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        values: list[str] = []
        for item in value:
            values.extend(flatten_string_values(item))
        return values
    if isinstance(value, dict):
        values = []
        for item in value.values():
            values.extend(flatten_string_values(item))
        return values
    return []


def candidate_artifact_paths(
    raw_path: str,
    workflow_path: Path,
    root: Path,
    ft_root: Path,
) -> list[Path]:
    value = strip_quotes(raw_path)
    if not value or value.startswith(("http://", "https://")):
        return []

    candidate = Path(value)
    if candidate.is_absolute():
        return [candidate]

    validation_root = root.parent if root.is_file() else root
    candidates = [validation_root / value, ft_root / value, workflow_path.parent / value]
    deduped: list[Path] = []
    for item in candidates:
        if item not in deduped:
            deduped.append(item)
    return deduped


def artifact_exists(raw_path: str, workflow_path: Path, root: Path, ft_root: Path) -> bool:
    candidates = candidate_artifact_paths(raw_path, workflow_path, root, ft_root)
    return bool(candidates) and any(candidate.exists() for candidate in candidates)


def resolve_artifact_path(
    raw_path: str,
    workflow_path: Path,
    root: Path,
    ft_root: Path,
) -> Path | None:
    return next(
        (candidate for candidate in candidate_artifact_paths(raw_path, workflow_path, root, ft_root) if candidate.exists()),
        None,
    )


def resolving_artifact_by_name(
    expected_name: str,
    values: list[str],
    workflow_path: Path,
    root: Path,
    ft_root: Path,
) -> Path | None:
    return next(
        (
            resolved
            for value in values
            if Path(strip_quotes(value)).name == expected_name
            for resolved in [resolve_artifact_path(value, workflow_path, root, ft_root)]
            if resolved is not None
        ),
        None,
    )


def resolve_workflow_test_case_artifacts(
    state: dict[str, Any],
    workflow_path: Path,
    root: Path,
    ft_root: Path,
) -> list[Path]:
    values = [
        *flatten_string_values(state.get("required_inputs")),
        *flatten_string_values(state.get("latest_artifacts")),
    ]
    resolved_paths: list[Path] = []
    for value in values:
        candidate_name = Path(strip_quotes(value)).name
        if not candidate_name.endswith(".md") or candidate_name == "README.md":
            continue
        resolved = resolve_artifact_path(value, workflow_path, root, ft_root)
        if resolved is None:
            continue
        if resolved.parent.name == "test-cases" or "test-cases" in resolved.parts:
            resolved_paths.append(resolved)
    return dedupe_paths(resolved_paths)


def blocked_writer_gate_failure_reasons_present(blocking_reasons: Any) -> bool:
    if not isinstance(blocking_reasons, list):
        return False
    reason_text = " ".join(str(reason).lower() for reason in blocking_reasons)
    return any(
        marker in reason_text
        for marker in (
            "writer quality gate",
            "quality gate",
            "test design review",
            "test-design-review",
            "blocking gate",
            "blocking row",
            "validator finding",
            "validator blocker",
        )
    )


def blocked_writer_gate_suppression_test_case_paths(
    workflow_states: list[Path],
    root: Path,
) -> set[Path]:
    suppress_paths: set[Path] = set()
    for workflow_path in workflow_states:
        try:
            state = parse_workflow_state(workflow_path)
        except UnicodeDecodeError:
            continue
        if state.get("current_stage") != "ft-test-case-writer":
            continue
        if state.get("stage_status") != "blocked-input":
            continue
        if not blocked_writer_gate_failure_reasons_present(state.get("blocking_reasons")):
            continue
        ft_root = find_ft_root(workflow_path, root, state)
        suppress_paths.update(resolve_workflow_test_case_artifacts(state, workflow_path, root, ft_root))
    return {path.resolve() for path in suppress_paths}


def resolve_workflow_artifacts_by_name(
    state: dict[str, Any],
    workflow_path: Path,
    root: Path,
    ft_root: Path,
    expected_name: str,
) -> list[Path]:
    values = [
        *flatten_string_values(state.get("required_inputs")),
        *flatten_string_values(state.get("latest_artifacts")),
    ]
    resolved_paths: list[Path] = []
    for value in values:
        if Path(strip_quotes(value)).name != expected_name:
            continue
        resolved = resolve_artifact_path(value, workflow_path, root, ft_root)
        if resolved is not None:
            resolved_paths.append(resolved)
    default_candidate = workflow_path.parent / expected_name
    if default_candidate.exists():
        resolved_paths.append(default_candidate)
    return dedupe_paths(resolved_paths)


def workflow_scope_contract_paths(
    state: dict[str, Any],
    workflow_path: Path,
    root: Path,
    ft_root: Path,
) -> list[Path]:
    return resolve_workflow_artifacts_by_name(state, workflow_path, root, ft_root, "scope-contract.md")


def workflow_requires_mockup_visual_inventory(
    state: dict[str, Any],
    workflow_path: Path,
    root: Path,
    ft_root: Path,
) -> bool:
    for scope_contract in workflow_scope_contract_paths(state, workflow_path, root, ft_root):
        try:
            content = scope_contract.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if MOCKUP_SOURCE_RE.search(content):
            return True
    return False


def workflow_mockup_visual_inventory_paths(
    state: dict[str, Any],
    workflow_path: Path,
    root: Path,
    ft_root: Path,
) -> list[Path]:
    return resolve_workflow_artifacts_by_name(
        state,
        workflow_path,
        root,
        ft_root,
        MOCKUP_VISUAL_INVENTORY_NAME,
    )


def workflow_artifact_paths_by_name(
    state: dict[str, Any],
    workflow_path: Path,
    root: Path,
    ft_root: Path,
    expected_name: str,
) -> list[Path]:
    return resolve_workflow_artifacts_by_name(state, workflow_path, root, ft_root, expected_name)


def scope_oracle_signal_evidence(
    state: dict[str, Any],
    workflow_path: Path,
    root: Path,
    ft_root: Path,
    pattern: re.Pattern[str],
) -> list[str]:
    evidence: list[str] = []
    source_paths = [
        *workflow_scope_contract_paths(state, workflow_path, root, ft_root),
        *workflow_artifact_paths_by_name(state, workflow_path, root, ft_root, "source-row-inventory.md"),
    ]
    for source_path in dedupe_paths(source_paths):
        try:
            content = source_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        display_path = rel(source_path, root)
        for line_number, line in enumerate(content.splitlines(), start=1):
            if pattern.search(line):
                evidence.append(f"{display_path}:{line_number}:{line.strip()[:180]}")
                if len(evidence) >= 20:
                    return evidence
    return evidence


def oracle_inventory_summary(path: Path) -> dict[str, Any]:
    content = path.read_text(encoding="utf-8")
    rows = markdown_table_rows_from_text(content)
    if not rows:
        return {
            "has_table": False,
            "missing_columns": [],
            "gap_rows_without_gap": [],
            "invalid_rows": [],
            "candidate_rows": [],
            "row_count": 0,
            "decisions": [],
        }

    header = normalize_table_header(rows[0])
    required_columns = {
        "scope_obligation_id",
        "source_ref",
        "field_or_block",
        "restriction_type",
        "oracle_source",
        "oracle_status",
        "decision",
        "planned_tc_or_gap",
        "gap_id",
        "analyst_question",
        "handoff_rule",
        "calibration_notes",
    }
    if path.name == REQUIREDNESS_ORACLE_INVENTORY_NAME:
        required_columns.update({"requiredness_class", "marker_oracle_found", "empty_value_oracle_found"})
    else:
        required_columns.add("observable_oracle_found")
        if "negative_class" not in header and "invalid_class" not in header:
            required_columns.add("negative_class")
    missing_columns = sorted(required_columns - set(header))

    parsed_rows: list[dict[str, str]] = []
    for row in rows[1:]:
        parsed_rows.append(
            {
                column_name: row[index].strip().strip("`") if index < len(row) else ""
                for index, column_name in enumerate(header)
            }
        )

    gap_rows_without_gap: list[str] = []
    invalid_rows: list[str] = []
    candidate_rows: list[str] = []
    decisions: list[str] = []
    for index, row in enumerate(parsed_rows, start=2):
        decision = row.get("decision", "").strip().strip("`").lower()
        oracle_status = row.get("oracle_status", "").strip().strip("`").lower()
        gap_id = row.get("gap_id", "").strip()
        scope_obligation_id = row.get("scope_obligation_id", "").strip() or f"row-{index}"
        if decision:
            decisions.append(decision)
        if decision and decision not in ALLOWED_ORACLE_INVENTORY_DECISIONS:
            invalid_rows.append(f"{scope_obligation_id}:invalid decision={decision}")
        if oracle_status and oracle_status not in ALLOWED_ORACLE_STATUSES:
            invalid_rows.append(f"{scope_obligation_id}:invalid oracle_status={oracle_status}")
        if decision == "candidate_tc_required":
            candidate_rows.append(scope_obligation_id)
            if oracle_status != "ui-calibration-required":
                invalid_rows.append(
                    f"{scope_obligation_id}:candidate_tc_required requires oracle_status=ui-calibration-required"
                )
            if not row.get("planned_tc_or_gap", "").strip():
                invalid_rows.append(f"{scope_obligation_id}:candidate_tc_required missing planned_tc_or_gap")
            if not row.get("calibration_notes", "").strip():
                invalid_rows.append(f"{scope_obligation_id}:candidate_tc_required missing calibration_notes")
        if decision in {"gap_required", "clarification_required"} and not real_gap_ids(gap_id):
            gap_rows_without_gap.append(f"{scope_obligation_id}:decision={decision};gap_id={gap_id or '-'}")

    return {
        "has_table": True,
        "missing_columns": missing_columns,
        "gap_rows_without_gap": gap_rows_without_gap,
        "invalid_rows": invalid_rows,
        "candidate_rows": candidate_rows,
        "row_count": len(parsed_rows),
        "decisions": decisions,
    }


def oracle_inventory_candidate_obligations(path: Path, root: Path) -> list[dict[str, str]]:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    rows = markdown_table_rows_from_text(content)
    if not rows:
        return []
    header = normalize_table_header(rows[0])
    obligations: list[dict[str, str]] = []
    for index, raw_row in enumerate(rows[1:], start=2):
        row = {
            column_name: raw_row[column_index].strip().strip("`") if column_index < len(raw_row) else ""
            for column_index, column_name in enumerate(header)
        }
        if row.get("decision", "").strip().lower() != "candidate_tc_required":
            continue
        scope_obligation_id = row.get("scope_obligation_id", "").strip()
        if not scope_obligation_id:
            scope_obligation_id = f"row-{index}"
        obligations.append(
            {
                "scope_obligation_id": scope_obligation_id,
                "gap_id": row.get("gap_id", "").strip(),
                "source_ref": row.get("source_ref", "").strip(),
                "path": rel(path, root),
            }
        )
    return obligations


def validate_candidate_oracle_obligation_coverage(
    root: Path,
    inventory_paths: list[Path],
    test_case_files: list[Path],
) -> tuple[list[Finding], list[Check]]:
    obligations: list[dict[str, str]] = []
    for inventory_path in inventory_paths:
        obligations.extend(oracle_inventory_candidate_obligations(inventory_path, root))
    if not obligations:
        return [], [
            Check(
                "oracle-candidate-obligation-coverage",
                "pass",
                "No candidate_tc_required oracle obligations found.",
                rel(root, root),
            )
        ]

    searchable_outputs: list[tuple[str, str]] = []
    for test_case_file in test_case_files:
        try:
            searchable_outputs.append((rel(test_case_file, root), test_case_file.read_text(encoding="utf-8")))
        except UnicodeDecodeError:
            continue

    missing: list[str] = []
    for obligation in obligations:
        obligation_id = obligation["scope_obligation_id"]
        gap_ids = real_gap_ids(obligation.get("gap_id", ""))
        tokens = [obligation_id, *gap_ids]
        if not any(
            any(token and token in content for token in tokens)
            for _, content in searchable_outputs
        ):
            missing.append(
                f"{obligation['path']}:{obligation_id}; gap_id={obligation.get('gap_id') or '-'}; source={obligation.get('source_ref') or '-'}"
            )

    if not missing:
        return [], [
            Check(
                "oracle-candidate-obligation-coverage",
                "pass",
                "All candidate_tc_required obligations are linked from writer output.",
                rel(root, root),
            )
        ]

    return [
        Finding(
            id="oracle-candidate-obligation-without-test-case",
            severity="warning",
            category="coverage",
            title="Candidate oracle obligations are not covered by candidate test cases",
            details=(
                "Rows with `decision = candidate_tc_required` must be carried into writer output as "
                "candidate TC traceability by matching `scope_obligation_id` or related GAP-*."
            ),
            path=rel(root, root),
            evidence=missing[:20],
            recommended_action=(
                "Create candidate TC sections for these obligations and include the stable "
                "`scope_obligation_id` in `Трассировка` or the TC body."
            ),
        )
    ], [
        Check(
            "oracle-candidate-obligation-coverage",
            "warn",
            "Some candidate_tc_required obligations are missing candidate TC coverage.",
            rel(root, root),
        )
    ]


SESSION_LOG_REQUIRED_STAGES = {
    "ft-source-locator",
    "ft-scope-analyzer",
    "ft-test-case-writer",
    "ft-test-case-reviewer",
    "ft-test-case-iteration",
}

SESSION_LOG_STAGE_FILE_HINTS = {
    "ft-source-locator": ("source-locator-session-log.md",),
    "ft-scope-analyzer": ("scope-analyzer-session-log.md",),
    "ft-test-case-writer": ("writer-session-log.md",),
    "ft-test-case-reviewer": ("reviewer-session-log",),
    "ft-test-case-iteration": ("iteration-session-log.md",),
}

SESSION_LOG_REQUIRED_SECTIONS = {
    "Session Metadata",
    "Inputs Read",
    "Inputs Not Used",
    "Key Decisions",
    "Risks And Fallbacks",
    "Validation",
    "Contamination Check",
}

SESSION_LOG_AUDIT_SECTIONS = {
    "Event Timeline",
    "Quality Checkpoints",
    "Technical Fallbacks",
    "Handoff Notes For Next Session",
}

SESSION_LOG_TECHNICAL_FALLBACK_REQUIRED_COLUMNS = {
    "fallback_id",
    "trigger",
    "failed_method",
    "fallback_method",
    "helper_artifact_path",
    "retained",
    "quality_risk",
    "follow_up",
}

SESSION_LOG_ARTIFACT_WRITE_STRATEGY_REQUIRED_COLUMNS = {
    "artifact_path",
    "artifact_size_class",
    "write_strategy",
    "declared_before_first_write",
    "helper",
    "forbidden_methods_checked",
}

SESSION_LOG_ARTIFACT_WRITE_STRATEGY_HINT_RE = re.compile(
    r"("
    r"source-row-inventory\.md|"
    r"source-normalization-diagnostic\.md|"
    r"mockup-visual-inventory\.md|"
    r"test-cases[\\/][^\s`|]+\.md|"
    r"canonical\s+(?:test[-\s]?case\s+)?file|"
    r"round-\d+-traceability-matrix\.(?:md|xlsx)|"
    r"large\s+artifact|package[-\s]?based|"
    r"generated\s+artifact|artifact\s+write|"
    r"write_artifact_sections\.py"
    r")",
    re.IGNORECASE,
)

SESSION_LOG_LARGE_ARTIFACT_SIZE_RE = re.compile(
    r"large|package[-\s]?based|table[-\s]?heavy|generated|chunked|multi[-\s]?section|diagnostic",
    re.IGNORECASE,
)

SESSION_LOG_ARTIFACT_WRITER_HELPER_RE = re.compile(
    r"scripts[\\/]write_artifact_sections\.py|write_artifact_sections\.py",
    re.IGNORECASE,
)

SESSION_LOG_DECLARED_BEFORE_WRITE_RE = re.compile(r"^(yes|true|pass|passed)$", re.IGNORECASE)

SESSION_LOG_TECHNICAL_FALLBACK_HINT_RE = re.compile(
    r"("
    r"command\s+length|windows\s+command|"
    r"длин[ауы]\s+команд|лимит\s+windows|"
    r"failed\s+patch|patch\s+limit|context\s+limit|"
    r"chunked\s+(artifact\s+)?writing|"
    r"helper\s+script|local\s+generator|generate_[\w-]+|"
    r"temporary\s+file|temp\s+content\s+file|"
    r"encoding\s+issue|utf-?8\s+console|mojibake|"
    r"кодировк\w*\s+искаж|искаж\w*\s+.*кирилл|бит\w*\s+кодиров|"
    r"technical\s+fallback|"
    r"коротк\w*\s+локальн\w*\s+генератор|"
    r"техническ\w*\s+fallback|"
    r"ограничени\w*\s+.*командн\w*\s+строк"
    r")",
    re.IGNORECASE,
)

SESSION_LOG_FORBIDDEN_INITIAL_WRITE_RE = re.compile(
    r"("
    r"command\s+length|"
    r"command[-\s]?line\s+limit|"
    r"windows\s+command[-\s]?line\s+limit|"
    r"one[-\s]?shot|"
    r"here[-\s]?string|"
    r"inline\s+(?:giant\s+)?command|"
    r"giant\s+command|"
    r"long\s+(?:shell\s+)?command|"
    r"command[-\s]?line\s+transport|"
    r"PowerShell\s+(?:argument|markdown\s+write|write|here[-\s]?string)|"
    r"длинн\w*\s+команд|"
    r"одн\w+\s+команд|"
    r"командн\w*\s+строк"
    r")",
    re.IGNORECASE,
)

SESSION_LOG_ENCODING_FALLBACK_RE = re.compile(
    r"encoding|utf-?8|mojibake|кирилл|кодиров|кракозябр|искаж\w*\s+вывод|бит\w*\s+текст",
    re.IGNORECASE,
)

SESSION_LOG_ENCODING_UTF8_REREAD_RE = re.compile(
    r"("
    r"explicit\s+utf-?8|utf-?8\s+(?:file\s+)?read|read_text\([^)]*encoding\s*=\s*[\"']utf-?8|"
    r"Get-Content[^\n|]*-Encoding\s+UTF8|PYTHONIOENCODING|PYTHONUTF8|"
    r"перечит\w*[^\n|]*utf-?8|явн\w*[^\n|]*utf-?8|utf-?8[^\n|]*(?:файл|источник)"
    r")",
    re.IGNORECASE,
)

SESSION_LOG_ENCODING_STDOUT_NOT_USED_RE = re.compile(
    r"("
    r"(?:stdout|console|terminal|output|вывод|консол\w*)[^\n|;,.]*"
    r"(?:not\s+used|discard\w*|ignored|не\s+использ|не\s+опира|отброш)|"
    r"(?:not\s+used|discard\w*|ignored|не\s+использ|не\s+опира|отброш)[^\n|;,.]*"
    r"(?:stdout|console|terminal|output|вывод|консол\w*)|"
    r"distorted\s+stdout\s+not\s+used\s+as\s+evidence|"
    r"испорчен\w*\s+вывод[^\n|;,.]*(?:не\s+использ|не\s+опира|отброш)|"
    r"mojibake[^\n|;,.]*(?:not\s+used|discard\w*|ignored)"
    r")",
    re.IGNORECASE,
)

SESSION_LOG_NONE_VALUES = {
    "",
    "-",
    "n/a",
    "na",
    "none",
    "no",
    "no fallback",
    "not applicable",
    "not-applicable",
    "нет",
    "не применимо",
}

DECISION_LOG_REQUIRED_STAGES = SESSION_LOG_REQUIRED_STAGES

DECISION_LOG_REQUIRED_COLUMNS = {
    "decision_id",
    "step",
    "decision_type",
    "input_or_trigger",
    "decision",
    "rationale",
    "artifact_or_output",
    "risk_or_confidence",
}

DECISION_LOG_ID_RE = re.compile(r"^(?:DEC|DL)-\d{3,}$", re.IGNORECASE)

WRITER_PROCESS_DIAGNOSTIC_REQUIRED_FIELDS = {
    "diagnostic_scope",
    "diagnostic_target",
    "active_for_current_workflow",
    "verdict",
    "process_readiness",
    "validator_gap_suspected",
}

WRITER_PROCESS_DIAGNOSTIC_FAIL_VALUES = {"fail", "failed", "not-pass", "not passed"}
WRITER_PROCESS_DIAGNOSTIC_CONTAMINATED_VALUES = {
    "contaminated",
    "technical-contaminated",
    "technically-contaminated",
    "not-clean",
    "dirty",
}
WRITER_PROCESS_DIAGNOSTIC_YES_VALUES = {"yes", "true", "y", "1"}
WRITER_PROCESS_DIAGNOSTIC_NO_VALUES = {"no", "false", "n", "0"}


def is_session_log_reference(value: str) -> bool:
    name = Path(strip_quotes(value)).name.lower()
    return name.endswith(".md") and "session-log" in name


def is_decision_log_reference(value: str) -> bool:
    name = Path(strip_quotes(value)).name.lower()
    return name.endswith(".md") and "decision-log" in name


def resolve_workflow_session_logs(
    state: dict[str, Any],
    workflow_path: Path,
    root: Path,
    ft_root: Path,
) -> list[Path]:
    values = [
        *flatten_string_values(state.get("required_inputs")),
        *flatten_string_values(state.get("latest_artifacts")),
    ]
    resolved_paths: list[Path] = []
    for value in values:
        if not is_session_log_reference(value):
            continue
        resolved = resolve_artifact_path(value, workflow_path, root, ft_root)
        if resolved is not None:
            resolved_paths.append(resolved)
    return dedupe_paths(resolved_paths)


def resolve_workflow_decision_logs(
    state: dict[str, Any],
    workflow_path: Path,
    root: Path,
    ft_root: Path,
) -> list[Path]:
    values = [
        *flatten_string_values(state.get("required_inputs")),
        *flatten_string_values(state.get("latest_artifacts")),
    ]
    resolved_paths: list[Path] = []
    for value in values:
        if not is_decision_log_reference(value):
            continue
        resolved = resolve_artifact_path(value, workflow_path, root, ft_root)
        if resolved is not None:
            resolved_paths.append(resolved)
    return dedupe_paths(resolved_paths)


def session_log_declared_skill(path: Path) -> str:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""
    metadata_section = extract_markdown_section(content, "Session Metadata") or ""
    skill_match = re.search(r"\|\s*skill\s*\|\s*`?([^`|\s]+)`?\s*\|", metadata_section)
    return skill_match.group(1).strip() if skill_match else ""


def session_log_matches_stage(path: Path, stage: str) -> bool:
    declared_skill = session_log_declared_skill(path)
    if declared_skill == stage:
        return True
    file_name = path.name.lower()
    return any(hint in file_name for hint in SESSION_LOG_STAGE_FILE_HINTS.get(stage, ()))


def prompt_ref_candidates(
    raw_path: str,
    workflow_path: Path,
    root: Path,
    ft_root: Path,
) -> list[Path]:
    candidates = candidate_artifact_paths(raw_path, workflow_path, root, ft_root)
    value = strip_quotes(raw_path).replace("\\", "/")

    for marker in ("/test-cases/", "/work/", "/source/", "/support/"):
        if marker in value:
            suffix = value.split(marker, 1)[1]
            candidates.append(ft_root / marker.strip("/") / suffix)

    if value.endswith("/AGENT-NOTES.md"):
        candidates.append(ft_root / "AGENT-NOTES.md")

    return dedupe_paths(candidates)


def prompt_ref_exists(raw_path: str, workflow_path: Path, root: Path, ft_root: Path) -> bool:
    return any(candidate.exists() for candidate in prompt_ref_candidates(raw_path, workflow_path, root, ft_root))


def prompt_section_key(heading: str) -> str | None:
    normalized = re.sub(r"\s+", " ", heading.strip().lower().rstrip(":"))
    for key, aliases in PROMPT_SECTION_ALIASES.items():
        if normalized in aliases:
            return key
    return None


def split_prompt_sections(content: str) -> list[tuple[str | None, str, str]]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", content, flags=re.MULTILINE))
    sections: list[tuple[str | None, str, str]] = []
    for index, match in enumerate(matches):
        body_start = match.end()
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        heading = match.group(1).strip()
        sections.append((prompt_section_key(heading), heading, content[body_start:body_end]))
    return sections


def extract_prompt_refs(content: str) -> list[str]:
    refs: list[str] = []
    for match in re.finditer(r"`([^`\n]+)`", content):
        value = match.group(1).strip()
        if "/" in value or "\\" in value or Path(value).suffix:
            refs.append(value)
    return refs


def validate_active_transition_prompt(
    prompt_path: Path,
    workflow_path: Path,
    root: Path,
    ft_root: Path,
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(prompt_path, root)

    try:
        content = prompt_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        findings.append(
            Finding(
                id="prompt-format-unreadable",
                severity="error",
                category="prompt-format",
                title="Active transition prompt is not readable as UTF-8",
                details=str(exc),
                path=display_path,
                evidence=[],
                recommended_action="Save the active handoff prompt as UTF-8.",
            )
        )
        checks.append(Check("active-transition-prompt-format", "fail", "Active prompt is not UTF-8.", display_path))
        return findings, checks

    sections = split_prompt_sections(content)
    present_groups = {key for key, _, _ in sections if key is not None}
    missing_required_groups = sorted(PROMPT_REQUIRED_SECTION_GROUPS - present_groups)
    if missing_required_groups:
        findings.append(
            Finding(
                id="prompt-format-missing-required-sections",
                severity="error",
                category="prompt-format",
                title="Active transition prompt misses required sections",
                details="The active handoff prompt must state the stage goal, resolving inputs, and guardrails.",
                path=display_path,
                evidence=missing_required_groups,
                recommended_action="Add canonical or accepted alias sections for goal, inputs, and guardrails.",
            )
        )

    input_refs = [
        ref
        for key, _, body in sections
        if key == "inputs"
        for ref in extract_prompt_refs(body)
    ]
    resolving_input_refs = [
        ref
        for ref in input_refs
        if prompt_ref_exists(ref, workflow_path, root, ft_root)
    ]
    if not input_refs:
        findings.append(
            Finding(
                id="prompt-format-missing-input-artifact-refs",
                severity="error",
                category="prompt-format",
                title="Active transition prompt has no input artifact references",
                details="The next skill should not have to infer its inputs from chat history.",
                path=display_path,
                evidence=[],
                recommended_action="List concrete input artifact paths in the input section.",
            )
        )
    elif not resolving_input_refs:
        findings.append(
            Finding(
                id="prompt-format-no-resolving-input-artifacts",
                severity="error",
                category="prompt-format",
                title="Active transition prompt input artifacts do not resolve",
                details="The input section lists artifact references, but none can be found in the current checkout.",
                path=display_path,
                evidence=input_refs[:10],
                recommended_action="Replace stale prompt references with existing artifact paths.",
            )
        )

    if prompt_path.name in {
        "prompt.scope-to-writer.md",
        "prompt.scope-to-iteration.md",
        "prompt.scope-gaps-to-reviewer.md",
    }:
        state = parse_workflow_state(workflow_path)
        workflow_artifact_values = [
            *flatten_string_values(state.get("required_inputs")),
            *flatten_string_values(state.get("latest_artifacts")),
        ]
        required_scope_input_names = {
            "source-selection.md",
            "scope-contract.md",
            "scope-coverage-gaps.md",
        }
        if prompt_path.name == "prompt.scope-gaps-to-reviewer.md":
            required_scope_input_names.add("workflow-state.yaml")
        for conditional_name in (
            "source-parity-check.md",
            "mockup-visual-inventory.md",
            NEGATIVE_ORACLE_INVENTORY_NAME,
            REQUIREDNESS_ORACLE_INVENTORY_NAME,
        ):
            if resolving_artifact_by_name(conditional_name, workflow_artifact_values, workflow_path, root, ft_root) is not None:
                required_scope_input_names.add(conditional_name)

        source_parity_path = resolving_artifact_by_name(
            "source-parity-check.md",
            workflow_artifact_values,
            workflow_path,
            root,
            ft_root,
        )
        if (
            resolving_artifact_by_name("source-row-inventory.md", workflow_artifact_values, workflow_path, root, ft_root)
            is not None
            or (source_parity_path is not None and source_parity_requires_source_row_inventory(source_parity_path))
        ):
            required_scope_input_names.add("source-row-inventory.md")

        scope_gaps_path = resolving_artifact_by_name(
            "scope-coverage-gaps.md",
            workflow_artifact_values,
            workflow_path,
            root,
            ft_root,
        )
        if scope_gaps_path is not None:
            try:
                scope_gap_total = get_int(extract_scope_coverage_metrics(scope_gaps_path).get("total")) or 0
            except UnicodeDecodeError:
                scope_gap_total = 0
            if scope_gap_total > 0:
                required_scope_input_names.add("scope-clarification-requests.md")
        if prompt_path.name == "prompt.scope-gaps-to-reviewer.md":
            required_scope_input_names.add("scope-clarification-requests.md")
        if (
            prompt_path.name == "prompt.scope-to-writer.md"
            and resolving_artifact_by_name("scope-gap-review.md", workflow_artifact_values, workflow_path, root, ft_root) is not None
        ):
            required_scope_input_names.add("scope-gap-review.md")

        missing_scope_prompt_inputs = [
            name
            for name in sorted(required_scope_input_names)
            if not any(
                Path(strip_quotes(ref)).name == name and prompt_ref_exists(ref, workflow_path, root, ft_root)
                for ref in input_refs
            )
        ]
        if missing_scope_prompt_inputs:
            findings.append(
                Finding(
                    id="prompt-format-missing-required-scope-inputs",
                    severity="error",
                    category="prompt-format",
                    title="Scope transition prompt misses required input artifacts",
                    details=(
                        "Scope transition prompts must list the concrete source/scope handoff artifacts that "
                        "the next skill must read."
                    ),
                    path=display_path,
                    evidence=missing_scope_prompt_inputs,
                    recommended_action=(
                        "Add resolving references to the missing artifacts in the prompt input section, or keep the "
                        "workflow blocked instead of routing to writer/iteration."
                    ),
                )
            )

    has_errors = any(finding.severity == "error" for finding in findings)
    checks.append(
        Check(
            "active-transition-prompt-format",
            "fail" if has_errors else "pass",
            "Active prompt format contract failed." if has_errors else "Active prompt format contract passed.",
            display_path,
        )
    )
    return findings, checks


def collect_active_source_documents(workflow_path: Path, root: Path) -> list[Path]:
    state = parse_workflow_state(workflow_path)
    ft_root = find_ft_root(workflow_path, root, state)
    artifact_values = [
        *flatten_string_values(state.get("required_inputs")),
        *flatten_string_values(state.get("latest_artifacts")),
    ]

    def is_source_docx_ref(value: str) -> bool:
        normalized = strip_quotes(value).replace("\\", "/")
        return Path(normalized).suffix.lower() == ".docx" and (
            normalized.startswith("source/") or "/source/" in normalized
        )

    raw_source_refs = [
        value
        for value in artifact_values
        if is_source_docx_ref(value)
    ]

    source_selection_values = [
        value
        for value in artifact_values
        if Path(strip_quotes(value)).name == "source-selection.md" and artifact_exists(value, workflow_path, root, ft_root)
    ]
    for source_selection_value in source_selection_values:
        source_selection_path = resolve_artifact_path(source_selection_value, workflow_path, root, ft_root)
        if source_selection_path is None:
            continue
        refs = extract_prompt_refs(source_selection_path.read_text(encoding="utf-8"))
        raw_source_refs.extend(
            ref
            for ref in refs
            if is_source_docx_ref(ref)
        )

    source_paths: list[Path] = []
    for ref in raw_source_refs:
        resolved = next(
            (candidate for candidate in prompt_ref_candidates(ref, workflow_path, root, ft_root) if candidate.exists()),
            None,
        )
        if resolved is not None and resolved.suffix.lower() == ".docx":
            source_paths.append(resolved)

    return dedupe_paths(source_paths)


def validate_active_source_document(
    path: Path,
    root: Path,
    *,
    source_quality_policy: str = "compatible",
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)

    try:
        sections = load_sections(path)
    except Exception as exc:
        findings.append(
            Finding(
                id="source-quality-unreadable-active-source",
                severity="error",
                category="source-quality",
                title="Active source document cannot be parsed",
                details=f"{type(exc).__name__}: {exc}",
                path=display_path,
                evidence=[],
                recommended_action="Replace the active source path with a readable DOCX or remove it from active handoff inputs.",
            )
        )
        checks.append(Check("active-source-quality", "fail", "Active source document cannot be parsed.", display_path))
        return findings, checks

    oversized_chunks = [
        f"{chunk.chunk_id}:{len(chunk.text)}"
        for section in sections
        if section.section_id != "preface"
        for chunk in split_section(section, max_chars=SOURCE_QUALITY_MAX_CHARS)
        if len(chunk.text) > SOURCE_QUALITY_MAX_CHARS
    ]
    if oversized_chunks:
        findings.append(
            Finding(
                id="source-quality-chunk-limit-breached",
                severity="error",
                category="source-quality",
                title="Active source chunk exceeds max_chars after splitting",
                details="The chunker must not pass oversized source chunks to downstream agents.",
                path=display_path,
                evidence=oversized_chunks[:10],
                recommended_action="Fix source block splitting before using this document for test-case generation.",
            )
        )

    for issue in analyze_sections(sections, max_chars=SOURCE_QUALITY_MAX_CHARS):
        severity = classify_source_quality_issue(issue, policy=source_quality_policy)  # type: ignore[arg-type]
        findings.append(
            Finding(
                id=issue.issue_id,
                severity=severity,
                category="source-quality",
                title="Active source extraction has quality risk",
                details=issue.details,
                path=display_path,
                evidence=issue.evidence,
                recommended_action="Inspect source extraction before relying on downstream test cases.",
            )
        )

    blocking = any(finding.severity in {"error", "warning"} for finding in findings)
    checks.append(
        Check(
            "active-source-quality",
            "fail" if blocking else "pass",
            "Active source quality gate failed." if blocking else "Active source quality gate passed.",
            display_path,
        )
    )
    return findings, checks


def extract_loop_summary_residual_risk_fields(content: str) -> dict[str, str] | None:
    section = extract_markdown_section(content, "Final Residual Risk")
    if section is None:
        return None
    return parse_markdown_fields(section)


def extract_loop_summary_metrics(path: Path) -> dict[str, Any]:
    content = path.read_text(encoding="utf-8")

    def number(pattern: str) -> int | None:
        match = re.search(pattern, content)
        if match:
            return int(match.group(1))
        return None

    final_status_match = re.search(r"Final status:\s*`([^`]+)`", content)
    status_match = re.search(r"\*\*Status:\*\*\s*`([^`]+)`", content)
    return {
        "final_status": (
            final_status_match.group(1)
            if final_status_match
            else status_match.group(1)
            if status_match
            else None
        ),
        "findings_error": number(r"Findings `error`:\s*`(\d+)`"),
        "findings_warning": number(r"Findings `warning`:\s*`(\d+)`"),
        "traceability_gap": number(r"Traceability `gap`:\s*`(\d+)`"),
        "traceability_unclear": number(r"Traceability `unclear`:\s*`(\d+)`"),
        "gap_mentions": len(re.findall(r"`GAP-\d+`", content)),
        "residual_risk_fields": extract_loop_summary_residual_risk_fields(content),
    }


def extract_scope_coverage_metrics(path: Path) -> dict[str, int | str | list[str] | None]:
    content = path.read_text(encoding="utf-8")

    blocking_match = re.search(
        r"blocking gaps:\s*`?(yes|no)`?",
        content,
        flags=re.IGNORECASE,
    )
    total_match = re.search(r"gaps:\s*`?(\d+)", content, flags=re.IGNORECASE)
    impact_blocking = len(
        re.findall(r"\*\*Impact:\*\*\s*`blocking`", content, flags=re.IGNORECASE)
    )
    gap_headers = len(re.findall(r"^###\s+GAP-\d+", content, flags=re.MULTILINE))
    gap_blocks = list(re.finditer(r"^###\s+(GAP-\d+)\s*$", content, flags=re.MULTILINE))
    blocking_gap_ids: list[str] = []
    for index, match in enumerate(gap_blocks):
        block_start = match.end()
        block_end = gap_blocks[index + 1].start() if index + 1 < len(gap_blocks) else len(content)
        block = content[block_start:block_end]
        if re.search(r"\*\*Impact:\*\*\s*`?blocking`?", block, flags=re.IGNORECASE) or re.search(
            r"\*\*Blocks Ready For Review:\*\*\s*`?yes`?",
            block,
            flags=re.IGNORECASE,
        ):
            blocking_gap_ids.append(match.group(1))

    return {
        "blocking_gaps": blocking_match.group(1).lower() if blocking_match else None,
        "impact_blocking": impact_blocking,
        "total": int(total_match.group(1)) if total_match else gap_headers,
        "gap_mentions": gap_headers,
        "blocking_gap_ids": blocking_gap_ids,
    }


def markdown_table_rows_from_text(content: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or "---" in line:
            continue
        cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
        rows.append(cells)
    return rows


def markdown_table_rows(path: Path) -> list[list[str]]:
    return markdown_table_rows_from_text(path.read_text(encoding="utf-8"))


def extract_test_design_applicability_section(content: str) -> str | None:
    match = re.search(
        r"^##\s+Test-design Applicability Matrix\s*$",
        content,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if not match:
        return None

    next_heading = re.search(r"^##\s+", content[match.end():], flags=re.MULTILINE)
    section_end = match.end() + next_heading.start() if next_heading else len(content)
    return content[match.end():section_end]


def extract_markdown_section(content: str, heading: str) -> str | None:
    match = re.search(
        rf"^#{{2,6}}\s+{re.escape(heading)}\s*$",
        content,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if not match:
        return None

    next_heading = re.search(r"^#{1,6}\s+", content[match.end():], flags=re.MULTILINE)
    section_end = match.end() + next_heading.start() if next_heading else len(content)
    return content[match.end():section_end]


def extract_coverage_gaps_section(content: str) -> str | None:
    match = re.search(
        r"^#{2,6}\s+Coverage Gaps\b.*$",
        content,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if not match:
        return None

    next_heading = re.search(r"^#{1,2}\s+", content[match.end():], flags=re.MULTILINE)
    section_end = match.end() + next_heading.start() if next_heading else len(content)
    return content[match.end():section_end]


def declared_coverage_gap_ids(content: str) -> set[str]:
    section = extract_coverage_gaps_section(content)
    if section is None:
        return set()
    return set(extract_gap_ids_from_text(section))


def input_restriction_gap_only_severity(policy: str) -> str:
    if policy in {"strict-canary", "writer-final", "production"}:
        return "error"
    return "warning"


def rolling_date_boundary_severity(policy: str) -> str:
    if policy in {"strict-canary", "writer-final", "production"}:
        return "error"
    return "warning"


def atomicity_coverage_severity(policy: str) -> str:
    if policy in {"strict-canary", "writer-final", "production"}:
        return "error"
    return "warning"


def validate_coverage_gap_inventory(
    content: str,
    path: Path,
    root: Path,
    *,
    input_restriction_gap_policy: str = "compatible",
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    display_path = rel(path, root)
    coverage_gaps_section = extract_coverage_gaps_section(content)
    if coverage_gaps_section is None:
        return findings, [Check("coverage-gap-inventory", "pass", "Coverage gap inventory section not present.", display_path)]

    declared_gap_ids = declared_coverage_gap_ids(content)
    referenced_gap_ids = set(extract_gap_ids_from_text(content))
    missing_gap_ids = sorted(referenced_gap_ids - declared_gap_ids)
    if missing_gap_ids:
        findings.append(
            Finding(
                id="test-case-gap-reference-missing-from-coverage-gaps",
                severity="warning",
                category="traceability",
                title="Canonical file references GAP ids missing from Coverage Gaps",
                details=(
                    "Every GAP-* referenced by atoms, matrices, TC coverage notes, self-checks or expected results "
                    "must be declared in the canonical Coverage Gaps section. Otherwise reviewer cannot distinguish "
                    "a real accepted gap from a stale or invented traceability link."
                ),
                path=display_path,
                evidence=[f"missing={', '.join(missing_gap_ids[:20])}"],
                recommended_action=(
                    "Add the missing GAP-* rows to Coverage Gaps with status/handling, or remove stale references "
                    "from atoms, matrices and test cases."
                ),
            )
        )

    gap_only_input_restrictions = gap_only_input_restriction_rows(coverage_gaps_section)
    if gap_only_input_restrictions:
        gap_only_severity = input_restriction_gap_only_severity(input_restriction_gap_policy)
        findings.append(
            Finding(
                id="source-backed-input-restriction-gap-only",
                severity=gap_only_severity,
                category="coverage",
                title="Source-backed input restriction is routed as gap-only",
                details=(
                    "A visible source-backed input restriction with an unknown exact UI rejection mechanism still "
                    "requires candidate-negative TC coverage. A BA question or parent GAP may document the missing "
                    "mechanism, but it must not replace the candidate TC."
                ),
                path=display_path,
                evidence=gap_only_input_restrictions[:20],
                recommended_action=(
                    "Create candidate-negative TC coverage with a concrete representative invalid value, "
                    "`Статус oracle: ui-calibration-required`, `Статус тест-кейса: candidate-ui-calibration`, "
                    "`Требуется подтверждение`, and an optional linked GAP/BA question for the unknown UI mechanism."
                ),
            )
        )

    checks = [
        Check(
            "coverage-gap-inventory",
            "fail" if any(finding.severity == "error" for finding in findings) else "warn" if findings else "pass",
            "Coverage gap inventory has missing declarations." if findings else "Coverage gap inventory passed.",
            display_path,
        )
    ]
    return findings, checks


def coverage_matrix_group_domain(row_text: str) -> str | None:
    text = row_text.lower()
    if re.search(r"e-?mail|электронн\w*\s+почт", text, flags=re.IGNORECASE):
        return "email"
    if re.search(r"phone|телефон", text, flags=re.IGNORECASE):
        return "phone"
    if re.search(r"postal|почтов\w*\s+индекс", text, flags=re.IGNORECASE):
        return "postal"
    if re.search(r"\bfio\b|фио|surname|patronymic|фамил|отчеств", text, flags=re.IGNORECASE):
        return "fio"
    if re.search(r"birth\s+date|date\s+boundary|дата\s+рожд|дат\w*\s+границ", text, flags=re.IGNORECASE):
        return "date"
    if re.search(r"address|адрес|dadata", text, flags=re.IGNORECASE):
        return "address"
    return None


def coverage_matrix_tc_domain(tc_id: str) -> str | None:
    upper = tc_id.upper()
    for token, domain in (
        ("EMAIL", "email"),
        ("E-MAIL", "email"),
        ("PHONE", "phone"),
        ("POSTAL", "postal"),
        ("FIO", "fio"),
        ("DATE", "date"),
        ("ADDRESS", "address"),
    ):
        if token in upper:
            return domain
    match = re.search(r"TC-AF43-AW4-(\d{3})", upper)
    if not match:
        return None
    number = int(match.group(1))
    if number in {4, 5, 9, 10}:
        return "postal"
    if number in {11, 12, 16, 17, 18, 25, 26, 30}:
        return "phone"
    if number in {13, 14, 15}:
        return "email"
    if number in {20, 21, 22, 23}:
        return "fio"
    if number in {27, 28}:
        return "date"
    if number in {1, 2, 3, 6, 8, 29}:
        return "address"
    return None


def coverage_matrix_domain_mismatch_evidence(content: str) -> list[str]:
    header, rows = parsed_section_table_rows(content, "Representative / Pairwise Coverage Decisions")
    if not rows:
        return []
    normalized_header = {column.strip().lower() for column in header}
    evidence: list[str] = []
    missing_columns = sorted(COVERAGE_MATRIX_REQUIRED_GROUP_COLUMNS - normalized_header)
    if missing_columns:
        evidence.append(f"missing columns: {', '.join(missing_columns)}")
    for row in rows:
        label_text = " ".join(
            row.get(column, "")
            for column in ("fields", "field_family", "shared_restriction", "source_restriction")
        )
        expected_domain = coverage_matrix_group_domain(label_text)
        if not expected_domain:
            continue
        tc_text = row.get("tc_ids", "") or row.get("selected_combinations", "") or row.get("selected_strategy", "")
        for tc_id in sorted(set(re.findall(r"TC-[A-Z0-9-]+", tc_text, flags=re.IGNORECASE))):
            actual_domain = coverage_matrix_tc_domain(tc_id)
            if actual_domain and actual_domain != expected_domain:
                evidence.append(f"{label_text[:120]}: expected={expected_domain}; {tc_id}={actual_domain}")
    return evidence


def validate_generated_artifact_source_basis(
    content: str,
    path: Path,
    root: Path,
    *,
    atomicity_coverage_policy: str = "compatible",
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    display_path = rel(path, root)
    direct_sole_source = GENERATED_ARTIFACT_SOLE_SOURCE_RE.search(content)
    generated_decision_basis = GENERATED_ARTIFACT_DECISION_BASIS_RE.search(content)
    has_failure_fixture_guard = GENERATED_ARTIFACT_FAILURE_FIXTURE_RE.search(content)
    has_source_cross_check = SOURCE_BASIS_CROSS_CHECK_RE.search(content)

    evidence: list[str] = []
    if direct_sole_source and not has_failure_fixture_guard:
        evidence.append(direct_sole_source.group(0).strip()[:220])
    if generated_decision_basis and not has_failure_fixture_guard and not has_source_cross_check:
        evidence.append(generated_decision_basis.group(0).strip()[:220])

    if evidence:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="generated-artifact-used-as-source-of-truth",
                severity=severity,
                category="source-selection",
                title="Generated artifact is used as source of truth",
                details=(
                    "Canary or evaluation artifacts may use older generated outputs as diagnostic failure fixtures, "
                    "but TC decisions, split/grouping decisions and representative coverage decisions must be backed "
                    "by source rows, BSR/GSR/REQ references or FT source artifacts."
                ),
                path=display_path,
                evidence=evidence[:20],
                recommended_action=(
                    "State that the generated artifact is diagnostic-only and cite source rows/BSR/FT artifacts used "
                    "for each decision, or remove decisions derived solely from generated output."
                ),
            )
        )

    sampled_group_evidence: list[str] = []
    coverage_matrix_domain_mismatches: list[str] = []
    field_level_canary_without_persistence_scope_note: list[str] = []
    persistence_calibration_package_missing: list[str] = []
    if PERSISTENCE_CANDIDATE_STATUS_RE.search(content):
        missing_files = persistence_calibration_package_missing_files(path, root)
        if missing_files:
            persistence_calibration_package_missing.append(
                f"missing files: {', '.join(missing_files)}"
            )
    if path.name == "coverage-matrix.md":
        representative_section = extract_markdown_section(content, "Representative / Pairwise Coverage Decisions") or content
        if re.search(r"e-?mail|e-mail|электронн\w*\s+почт", content, flags=re.IGNORECASE) and not re.search(
            r"e-?mail\s+(?:restrictions|fields?|field)|e-mail\s+(?:restrictions|fields?|field)|электронн\w*\s+почт",
            representative_section,
            flags=re.IGNORECASE,
        ):
            sampled_group_evidence.append("email restrictions are covered/sampled but have no explicit group strategy row")
        for label, pattern in (
            ("postal indexes", r"postal\s+indexes|почтов\w*\s+индекс"),
            ("phone fields", r"phone\s+fields|телефон"),
        ):
            if re.search(pattern, content, flags=re.IGNORECASE) and not re.search(pattern, representative_section, flags=re.IGNORECASE):
                sampled_group_evidence.append(f"{label} are covered/sampled but have no explicit group strategy row")
        coverage_matrix_domain_mismatches = coverage_matrix_domain_mismatch_evidence(content)
    if path.name == "canary-evaluation-report.md" and FIELD_LEVEL_CANARY_RE.search(content):
        if not PERSISTENCE_SCOPE_NOTE_RE.search(content):
            field_level_canary_without_persistence_scope_note.append(
                "field-level/risk-based canary report lacks persistence follow-up or out-of-scope rationale"
            )
    if sampled_group_evidence:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="sampled-field-group-without-group-strategy",
                severity=severity,
                category="test-design",
                title="Sampled similar-field group lacks explicit group strategy",
                details=(
                    "When invalid classes are sampled across similar postal, phone, e-mail or FIO fields, the coverage "
                    "matrix must state the selected classes, omitted combinations and residual risk for that group."
                ),
                path=display_path,
                evidence=sampled_group_evidence[:20],
                recommended_action="Add a representative/pairwise group strategy row for each sampled field family.",
            )
        )
    if coverage_matrix_domain_mismatches:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="coverage-matrix-tc-domain-mismatch",
                severity=severity,
                category="test-design",
                title="Coverage matrix group references TC from another field domain",
                details=(
                    "Representative/pairwise group rows must reference TC from the same field family. "
                    "Postal, phone, e-mail, FIO and date groups must not borrow unrelated TC ids."
                ),
                path=display_path,
                evidence=coverage_matrix_domain_mismatches[:20],
                recommended_action="Move the TC id to the correct group or update the group label/source rows so the domain is explicit.",
            )
        )
    if field_level_canary_without_persistence_scope_note:
        findings.append(
            Finding(
                id="field-level-canary-without-persistence-scope-note",
                severity="warning",
                category="test-design",
                title="Field-level canary lacks persistence scope note",
                details=(
                    "A field-level / risk-based canary that does not cover save/persistence must state that "
                    "persistence is out of scope or planned as a separate follow-up suite."
                ),
                path=display_path,
                evidence=field_level_canary_without_persistence_scope_note[:20],
                recommended_action="Add an explicit save/persistence follow-up or out-of-scope rationale to the canary evaluation report.",
            )
        )
    if persistence_calibration_package_missing:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="persistence-calibration-package-missing",
                severity=severity,
                category="test-design",
                title="Persistence candidate artifacts lack calibration package",
                details="Candidate persistence smoke artifacts require a BA/UI save-flow calibration package before they can be treated as controlled handoff material.",
                path=display_path,
                evidence=persistence_calibration_package_missing[:20],
                recommended_action="Add `ba-ui-calibration-questions.md`, `persistence-tc-conversion-plan.md`, `save-flow-calibration-checklist.md` and `persistence-calibration-evaluation-report.md` under `work/calibration/persistence-save-flow/`.",
            )
        )

    checks = [
        Check(
            "generated-artifact-source-basis",
            "fail" if any(finding.severity == "error" for finding in findings) else "warn" if findings else "pass",
            "Generated artifact source-basis issues found." if findings else "Generated artifact source-basis guard passed.",
            display_path,
        )
    ]
    return findings, checks


def gap_only_input_restriction_rows(coverage_gaps_section: str) -> list[str]:
    table_rows = markdown_table_rows_from_text(coverage_gaps_section)
    if len(table_rows) < 2:
        return []

    header = normalize_table_header(table_rows[0])
    if "gap_type" not in header:
        return []

    evidence: list[str] = []
    for row_index, raw_row in enumerate(table_rows[1:], start=2):
        if not any(cell.strip().strip("-:|`") for cell in raw_row):
            continue
        row = {
            column_name: raw_row[column_index].strip().strip("`") if column_index < len(raw_row) else ""
            for column_index, column_name in enumerate(header)
        }
        gap_type = normalize_markdown_field_value(row.get("gap_type", "")).lower()
        if "missing-ui-oracle" not in gap_type:
            continue

        combined = " | ".join(row.values())
        if GAP_ONLY_CANDIDATE_LINK_RE.search(combined):
            continue
        if not GAP_ONLY_INPUT_RESTRICTION_RE.search(combined):
            continue
        if not GAP_ONLY_UI_CALIBRATION_ROUTE_RE.search(combined):
            continue

        gap_id = row.get("gap_id", "").strip() or raw_row[0].strip() or f"row-{row_index}"
        source_ref = row.get("source_ref", "").strip() or row.get("related_req", "").strip() or "-"
        description = re.sub(r"\s+", " ", row.get("description", "").strip())
        downstream = re.sub(r"\s+", " ", row.get("downstream_handling", "").strip())
        evidence.append(
            f"{gap_id}: source={source_ref}; description={description[:160]}; downstream={downstream[:160]}"
        )
    return evidence


def markdown_section_is_empty(section: str) -> bool:
    meaningful_lines = [
        line.strip()
        for line in section.splitlines()
        if line.strip() and not re.fullmatch(r"[-|:`\s]+", line.strip())
    ]
    return not meaningful_lines


def validate_writer_self_check_sections(content: str, path: Path, root: Path) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    display_path = rel(path, root)
    empty_sections: list[str] = []
    for heading in ("Writer Self-Check", "Artifact Write Evidence"):
        section = extract_markdown_section(content, heading)
        if section is not None and markdown_section_is_empty(section):
            empty_sections.append(heading)

    if empty_sections:
        findings.append(
            Finding(
                id="writer-self-check-empty-section",
                severity="warning",
                category="test-case-format",
                title="Writer self-check has empty evidence sections",
                details=(
                    "Writer self-check sections must contain explicit evidence, a table, a link to the session log, "
                    "or a concrete not-applicable rationale. Empty headings create false assurance."
                ),
                path=display_path,
                evidence=empty_sections,
                recommended_action=(
                    "Fill each self-check section with evidence or remove the heading. For artifact write evidence, "
                    "link the session log `Artifact Write Strategy` table or the split `artifact-write-strategy.md`."
                ),
            )
        )

    checks = [
        Check(
            "writer-self-check-sections",
            "warn" if findings else "pass",
            "Writer self-check has empty sections." if findings else "Writer self-check sections passed.",
            display_path,
        )
    ]
    return findings, checks


def parse_bullet_context_fields(section: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in section.splitlines():
        match = re.match(r"^\s*(?:[-*]\s*)?([^:|\n]+):\s*(.*?)\s*$", line)
        if not match:
            continue
        key = normalize_markdown_field_name(match.group(1))
        value = normalize_markdown_field_value(match.group(2))
        fields[key] = value
    return fields


def source_selection_routes_downstream(state: dict[str, Any]) -> bool:
    return (
        state.get("stage_status") in {"ready-for-next-stage", "ready-for-review", "ready-for-writer-revision"}
        and state.get("next_skill")
        in {"ft-scope-analyzer", "ft-test-case-writer", "ft-test-case-iteration", "ft-test-case-reviewer"}
    )


def source_selection_has_downstream_next_skill(state: dict[str, Any]) -> bool:
    return state.get("next_skill") in {
        "ft-scope-analyzer",
        "ft-test-case-writer",
        "ft-test-case-iteration",
        "ft-test-case-reviewer",
    }


def validate_source_selection_artifact(
    path: Path,
    root: Path,
    state: dict[str, Any],
    workflow_path: Path,
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        findings.append(
            Finding(
                id="source-selection-unreadable",
                severity="error",
                category="source-selection",
                title="source-selection.md is not readable as UTF-8",
                details=str(exc),
                path=display_path,
                evidence=[],
                recommended_action="Save source-selection.md as UTF-8.",
            )
        )
        checks.append(Check("source-selection-readable", "fail", "File is not UTF-8.", display_path))
        return findings, checks

    missing_sections = [
        section
        for section in sorted(REQUIRED_SOURCE_SELECTION_SECTIONS)
        if extract_markdown_section(content, section) is None
    ]
    if missing_sections:
        findings.append(
            Finding(
                id="source-selection-missing-required-sections",
                severity="warning",
                category="source-selection",
                title="source-selection.md misses required sections",
                details="The source selection artifact must be a reproducible handoff, not only a placeholder file.",
                path=display_path,
                evidence=missing_sections,
                recommended_action=(
                    "Add the required sections from references/agent/source-selection-format.md before routing "
                    "to ft-scope-analyzer."
                ),
            )
        )
        checks.append(Check("source-selection-required-sections", "fail", "Required sections are missing.", display_path))
    else:
        checks.append(Check("source-selection-required-sections", "pass", "Required sections are present.", display_path))

    context_section = extract_markdown_section(content, "Context") or ""
    context_fields = parse_bullet_context_fields(context_section)
    xhtml_section = extract_markdown_section(content, "Machine-Readable XHTML Source")
    xhtml_fields = parse_bullet_context_fields(xhtml_section or "")
    xhtml_available = normalize_markdown_field_value(xhtml_fields.get("xhtml_available", "")).lower()
    xhtml_missing_or_unconfirmed = xhtml_available != "yes"

    if xhtml_section is None:
        findings.append(
            Finding(
                id="source-selection-missing-xhtml-section",
                severity="warning",
                category="source-selection",
                title="source-selection.md misses mandatory XHTML source section",
                details="Main FT XHTML availability must be recorded before scope, writer, reviewer or iteration routing.",
                path=display_path,
                evidence=["Machine-Readable XHTML Source"],
                recommended_action="Add `Machine-Readable XHTML Source` with `xhtml_available: yes | no`.",
            )
        )
        checks.append(Check("source-selection-xhtml-section", "fail", "Mandatory XHTML source section is missing.", display_path))
    else:
        checks.append(Check("source-selection-xhtml-section", "pass", "Mandatory XHTML source section is present.", display_path))

    missing_context_fields = sorted(REQUIRED_SOURCE_SELECTION_CONTEXT_FIELDS - set(context_fields))
    if missing_context_fields:
        findings.append(
            Finding(
                id="source-selection-missing-context-fields",
                severity="warning",
                category="source-selection",
                title="source-selection.md misses required context fields",
                details="Downstream stages need an explicit FT slug and selection status from the source locator.",
                path=display_path,
                evidence=missing_context_fields,
                recommended_action="Add `selected_ft_slug` and `selection_status` to the Context section.",
            )
        )
        checks.append(Check("source-selection-context-fields", "fail", "Required context fields are missing.", display_path))
    else:
        checks.append(Check("source-selection-context-fields", "pass", "Required context fields are present.", display_path))

    raw_status = context_fields.get("selection_status", "")
    selection_status = normalize_markdown_field_value(raw_status).lower()
    if raw_status and selection_status not in ALLOWED_SOURCE_SELECTION_STATUSES:
        findings.append(
            Finding(
                id="source-selection-invalid-selection-status",
                severity="error",
                category="source-selection",
                title="source-selection.md has invalid selection_status",
                details="Source selection status controls whether downstream stages may start.",
                path=display_path,
                evidence=[f"selection_status={raw_status}"],
                recommended_action="Use one of: `selected`, `ambiguous`, `blocked-input`.",
            )
        )
        checks.append(Check("source-selection-status", "fail", "selection_status is invalid.", display_path))
    elif raw_status:
        checks.append(Check("source-selection-status", "pass", "selection_status is canonical.", display_path))

    if selection_status == "selected" and xhtml_missing_or_unconfirmed:
        findings.append(
            Finding(
                id="workflow-state-source-selection-missing-required-xhtml",
                severity="error",
                category="source-selection",
                title="Selected source selection lacks required main FT XHTML",
                details="`selection_status: selected` is allowed only when main FT XHTML is confirmed with `xhtml_available: yes`.",
                path=display_path,
                evidence=[f"xhtml_available={xhtml_fields.get('xhtml_available', '<missing>')}"],
                recommended_action="Set `selection_status: blocked-input` until matching main FT XHTML is added under `source/`.",
            )
        )
        checks.append(Check("source-selection-required-xhtml", "fail", "Selected source selection lacks XHTML.", display_path))
    elif selection_status:
        checks.append(Check("source-selection-required-xhtml", "pass", "XHTML availability matches selection status.", display_path))

    if xhtml_missing_or_unconfirmed and source_selection_has_downstream_next_skill(state):
        findings.append(
            Finding(
                id="workflow-state-source-selection-xhtml-missing-routes-downstream",
                severity="error",
                category="workflow-state",
                title="Workflow routes downstream without mandatory main FT XHTML",
                details="Missing or unconfirmed XHTML must keep the workflow blocked before scope, writer, reviewer or iteration work.",
                path=rel(workflow_path, root),
                evidence=[f"{rel(path, root)} xhtml_available={xhtml_fields.get('xhtml_available', '<missing>')}", f"next_skill={state.get('next_skill')}"],
                recommended_action="Set `next_skill: none` or keep the workflow blocked until `xhtml_available: yes` is confirmed.",
            )
        )
        checks.append(Check("workflow-state-source-selection-xhtml", "fail", "Missing XHTML routes downstream.", rel(workflow_path, root)))
    else:
        checks.append(Check("workflow-state-source-selection-xhtml", "pass", "XHTML routing guard passed.", rel(workflow_path, root)))

    if selection_status and selection_status != "selected" and source_selection_routes_downstream(state):
        findings.append(
            Finding(
                id="workflow-state-source-selection-not-selected",
                severity="error",
                category="workflow-state",
                title="Workflow routes downstream with unresolved source selection",
                details=(
                    "`source-selection.md` is not `selected`, so `ft-scope-analyzer`/writer/reviewer work must "
                    "not start from this handoff."
                ),
                path=rel(workflow_path, root),
                evidence=[f"{rel(path, root)} selection_status={selection_status}"],
                recommended_action="Keep the workflow in `blocked-input` or update source-selection.md to `selected` after resolution.",
            )
        )
        checks.append(Check("workflow-state-source-selection-selected", "fail", "Source selection is not selected.", rel(workflow_path, root)))
    elif selection_status:
        checks.append(Check("workflow-state-source-selection-selected", "pass", "Source selection status does not block routing.", rel(workflow_path, root)))

    return findings, checks


def source_parity_requires_source_row_inventory(path: Path) -> bool:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False

    section = extract_markdown_section(content, "Table / Row Parity")
    if section is None:
        return False

    rows = markdown_table_rows_from_text(section)
    return len(rows) > 1


def normalize_table_header(cells: list[str]) -> list[str]:
    return [normalize_markdown_field_name(cell.strip().strip("`")) for cell in cells]


def is_dash_placeholder(value: str) -> bool:
    normalized = value.strip().strip("`").strip().lower()
    return normalized in DASH_PLACEHOLDER_VALUES


def placeholder_sentinel_evidence_for_rows(
    rows: list[list[str]],
    section_title: str,
    prohibited_columns: set[str],
) -> list[str]:
    if not rows:
        return []
    header = normalize_table_header(rows[0])
    column_indexes = [
        (column_name, index)
        for index, column_name in enumerate(header)
        if column_name in prohibited_columns
    ]
    if not column_indexes:
        return []

    evidence: list[str] = []
    for row_number, row in enumerate(rows[1:], start=2):
        row_label = ""
        for preferred_column in (
            "atom_id",
            "decision_id",
            "obligation_id",
            "design_item_id",
            "dependency_id",
            "review_item",
            "source_row_id",
        ):
            if preferred_column in header:
                preferred_index = header.index(preferred_column)
                if preferred_index < len(row):
                    row_label = row[preferred_index].strip().strip("`")
                break
        if not row_label:
            row_label = f"row-{row_number}"
        for column_name, index in column_indexes:
            if index < len(row) and is_dash_placeholder(row[index]):
                evidence.append(f"{section_title}:{row_label}:{column_name}={row[index].strip() or '<empty>'}")
    return evidence


def validate_traceability_placeholder_sentinels(
    content: str,
    path: Path,
    root: Path,
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    evidence: list[str] = []

    if path.name.endswith("traceability-matrix.md"):
        evidence.extend(
            placeholder_sentinel_evidence_for_rows(
                markdown_table_rows_from_text(content),
                "Traceability Matrix",
                TRACEABILITY_MATRIX_PLACEHOLDER_COLUMNS,
            )
        )

    for section_title, prohibited_columns in TRACEABILITY_PLACEHOLDER_COLUMNS_BY_SECTION.items():
        section = extract_markdown_section(content, section_title)
        if section is None:
            continue
        evidence.extend(
            placeholder_sentinel_evidence_for_rows(
                markdown_table_rows_from_text(section),
                section_title,
                prohibited_columns,
            )
        )

    if evidence:
        findings.append(
            Finding(
                id="traceability-placeholder-sentinel",
                severity="warning",
                category="traceability",
                title="Traceability artifacts use placeholder sentinels in link/source columns",
                details=(
                    "Literal `-` / `N/A` in traceability-bearing table columns hides whether data is absent, "
                    "not applicable, not covered, or intentionally routed to GAP/unclear. Use explicit sentinels "
                    "such as `not_applicable:covered`, `not_covered:<GAP-ID>`, `unclear:<GAP-ID>`, "
                    "`no_requirement_code:<source_ref>` or `none_required:<reason>`."
                ),
                path=display_path,
                evidence=evidence[:30],
                recommended_action=(
                    "Replace placeholder cells in traceability/link columns with explicit semantic sentinel values "
                    "or concrete TC/GAP/ATOM/source references."
                ),
            )
        )

    checks.append(
        Check(
            "traceability-placeholder-sentinel",
            "warn" if evidence else "pass",
            (
                "Traceability-bearing tables use placeholder sentinels."
                if evidence
                else "Traceability-bearing placeholder sentinel check passed."
            ),
            display_path,
        )
    )
    return findings, checks


def atomic_requirement_ledger_atom_ids(content: str) -> set[str]:
    section = extract_markdown_section(content, "Atomic Requirements Ledger")
    if section is None:
        return set()

    rows = markdown_table_rows_from_text(section)
    if not rows:
        return set()

    header = normalize_table_header(rows[0])
    if "atom_id" not in header:
        return set()

    atom_id_index = header.index("atom_id")
    atom_ids: set[str] = set()
    for row in rows[1:]:
        if atom_id_index >= len(row):
            continue
        atom_id = row[atom_id_index].strip().strip("`")
        if atom_id:
            atom_ids.add(atom_id)
    return atom_ids


def parsed_atomic_requirement_ledger_rows(content: str) -> tuple[list[str], list[dict[str, str]]]:
    section = extract_markdown_section(content, "Atomic Requirements Ledger")
    if section is None:
        return [], []

    rows = markdown_table_rows_from_text(section)
    if not rows:
        return [], []

    header = normalize_table_header(rows[0])
    parsed_rows: list[dict[str, str]] = []
    for row in rows[1:]:
        parsed_row: dict[str, str] = {}
        for index, column_name in enumerate(header):
            parsed_row[column_name] = row[index].strip().strip("`") if index < len(row) else ""
        parsed_rows.append(parsed_row)
    return header, parsed_rows


def ledger_rows_with_real_gap_ids(content: str) -> list[dict[str, str]]:
    _, ledger_rows = parsed_atomic_requirement_ledger_rows(content)
    gap_rows: list[dict[str, str]] = []
    for row in ledger_rows:
        coverage_status = row.get("coverage_status", "").strip().strip("`").lower()
        if coverage_status not in {"gap", "unclear"}:
            continue
        if not real_gap_ids(" | ".join(row.values())):
            continue
        gap_rows.append(row)
    return gap_rows


def is_valid_atom_id_value(atom_id: str) -> bool:
    return bool(re.fullmatch(r"ATOM-\d{3,}", atom_id) or SCOPED_ATOM_ID_RE.fullmatch(atom_id))


def is_valid_risk_priority_atom_id(atom_id: str, ledger_atom_ids: set[str]) -> bool:
    if re.fullmatch(r"ATOM-\d{3,}", atom_id):
        return True
    if SCOPED_ATOM_ID_RE.fullmatch(atom_id):
        return atom_id in ledger_atom_ids
    return False


def meaningful_matrix_value(value: str) -> bool:
    normalized = value.strip().strip("`").strip().lower()
    return bool(normalized and normalized not in {"-", "n/a", "na", "none", "null"})


def is_production_test_case_path(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    return path.suffix.lower() == ".md" and "fts" in parts and "test-cases" in parts and "work" not in parts


def parsed_test_design_applicability_rows(content: str) -> list[dict[str, str]]:
    section = extract_test_design_applicability_section(content)
    if section is None:
        return []

    rows = markdown_table_rows_from_text(section)
    if not rows:
        return []

    header = normalize_table_header(rows[0])
    if not APPLICABILITY_MATRIX_REQUIRED_COLUMNS.issubset(set(header)):
        return []

    column_index = {name: index for index, name in enumerate(header)}
    parsed_rows: list[dict[str, str]] = []
    for row in rows[1:]:
        parsed_row: dict[str, str] = {}
        for name in APPLICABILITY_MATRIX_REQUIRED_COLUMNS:
            index = column_index[name]
            parsed_row[name] = row[index].strip().strip("`") if index < len(row) else ""
        parsed_rows.append(parsed_row)
    return parsed_rows


def validate_test_design_applicability_matrix(
    content: str,
    path: Path,
    root: Path,
    *,
    structural_severity: str,
    known_test_case_ids: set[str] | None = None,
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    section = extract_test_design_applicability_section(content)

    if section is None:
        if is_production_test_case_path(path):
            checks.append(
                Check(
                    "test-design-applicability-matrix",
                    "pass",
                    "Applicability matrix is not required inside production runtime test-case files.",
                    display_path,
                )
            )
            return findings, checks
        findings.append(
            Finding(
                id="test-design-applicability-matrix-missing",
                severity=structural_severity,
                category="test-design",
                title="Test-case file has no Test-design applicability matrix",
                details=(
                    "Canonical initial drafts should explicitly record which coverage dimensions apply, "
                    "do not apply, or remain unclear."
                ),
                path=display_path,
                evidence=[],
                recommended_action="Add a Test-design Applicability Matrix before review handoff.",
            )
        )
        checks.append(
            Check(
                "test-design-applicability-matrix",
                "warn" if structural_severity == "warning" else "pass",
                "Applicability matrix is missing." if structural_severity == "warning" else "Applicability matrix missing recorded as legacy info.",
                display_path,
            )
        )
        return findings, checks

    rows = markdown_table_rows_from_text(section)
    if not rows:
        findings.append(
            Finding(
                id="test-design-applicability-matrix-no-table",
                severity="warning",
                category="test-design",
                title="Test-design applicability matrix has no Markdown table",
                details="The matrix section exists but has no parseable Markdown table.",
                path=display_path,
                evidence=[],
                recommended_action="Use the canonical table columns: dimension, applicable, source_ref, reason, linked_atoms, linked_test_cases, gap_id.",
            )
        )
        checks.append(Check("test-design-applicability-matrix", "warn", "Applicability matrix table is missing.", display_path))
        return findings, checks

    header = normalize_table_header(rows[0])
    missing_columns = sorted(APPLICABILITY_MATRIX_REQUIRED_COLUMNS - set(header))
    if missing_columns:
        findings.append(
            Finding(
                id="test-design-applicability-matrix-missing-columns",
                severity="warning",
                category="test-design",
                title="Test-design applicability matrix misses required columns",
                details="The matrix must expose all required columns so reviewer can audit coverage decisions.",
                path=display_path,
                evidence=[f"missing={', '.join(missing_columns)}", f"columns={', '.join(header[:12])}"],
                recommended_action="Add the missing columns from writer-output-format.md.",
            )
        )
        checks.append(Check("test-design-applicability-matrix", "warn", "Applicability matrix columns are incomplete.", display_path))
        return findings, checks

    column_index = {name: index for index, name in enumerate(header)}
    invalid_applicability: list[str] = []
    unknown_dimensions: list[str] = []
    missing_yes_links: list[str] = []
    missing_unclear_gap: list[str] = []
    unsupported_no_rows: list[str] = []
    unknown_test_case_ids: list[str] = []
    invalid_gap_refs: list[str] = []
    hidden_integration_gap_rows: list[str] = []
    hidden_numeric_equivalence_rows: list[str] = []
    hidden_numeric_rows: list[str] = []
    linked_tc_dimension_mismatches: list[str] = []
    linked_atom_contamination_rows: list[str] = []
    has_integration_gap_evidence = bool(INTEGRATION_GAP_EVIDENCE_RE.search(content))
    has_numeric_only_evidence = bool(NUMERIC_ONLY_CONTEXT_RE.search(content))
    test_case_blocks_by_id = {test_case_id: block for test_case_id, block in extract_test_case_blocks(content)}

    for row_number, row in enumerate(rows[1:], start=2):
        def cell(name: str) -> str:
            index = column_index[name]
            return row[index].strip().strip("`") if index < len(row) else ""

        dimension = cell("dimension").lower()
        applicable = cell("applicable").lower()
        linked_atoms = cell("linked_atoms")
        linked_test_cases = cell("linked_test_cases")
        gap_id = cell("gap_id")
        source_ref = cell("source_ref")
        reason = cell("reason")
        row_label = f"row {row_number}:{dimension or '<missing dimension>'}"

        if dimension and dimension not in ALLOWED_COVERAGE_DIMENSIONS:
            unknown_dimensions.append(row_label)
        if applicable not in {"yes", "no", "unclear"}:
            invalid_applicability.append(f"{row_label}:applicable={applicable or '<missing>'}")
            continue

        atom_ids = extract_atom_ids_from_text(linked_atoms)
        test_case_ids = extract_test_case_ids_from_text(linked_test_cases)
        gap_ids = extract_gap_ids_from_text(gap_id)

        if meaningful_matrix_value(gap_id) and not gap_ids:
            invalid_gap_refs.append(f"{row_label}:gap_id={gap_id}")

        if known_test_case_ids:
            for test_case_id in test_case_ids:
                if test_case_id not in known_test_case_ids:
                    unknown_test_case_ids.append(f"{row_label}:{test_case_id}")

        if applicable == "yes" and (not atom_ids or (not test_case_ids and not gap_ids)):
            missing_yes_links.append(
                f"{row_label}:atoms={linked_atoms or '-'}; test_cases={linked_test_cases or '-'}; gap={gap_id or '-'}"
            )
        if applicable == "yes" and test_case_ids:
            linked_tc_atom_ids: set[str] = set()
            dimension_context_re = APPLICABILITY_LINKED_TC_DIMENSION_CONTEXT_RE.get(dimension)
            for test_case_id in test_case_ids:
                block = test_case_blocks_by_id.get(test_case_id, "")
                if not block:
                    continue
                linked_tc_atom_ids.update(extract_any_atom_ids_from_text(block))
                if dimension_context_re is not None:
                    tc_context = " ".join(
                        [
                            extract_test_case_field_block(block, ["Title", "title", "Название"]),
                            extract_test_case_field_block(block, ["Goal", "goal", "Цель"]),
                            extract_test_case_field_block(block, ["Test Data", "test_data", "test data", "Тестовые данные"]),
                            extract_test_case_field_block(block, ["Steps", "steps", "Шаги"]),
                            extract_test_case_expected_result(block),
                        ]
                    )
                    if not dimension_context_re.search(tc_context):
                        linked_tc_dimension_mismatches.append(
                            f"{row_label}:{test_case_id}:context={tc_context[:140] or '<empty>'}"
                        )
            if atom_ids and not gap_ids:
                unmapped_atom_ids = [atom_id for atom_id in atom_ids if atom_id not in linked_tc_atom_ids]
                if unmapped_atom_ids:
                    linked_atom_contamination_rows.append(
                        f"{row_label}:unmapped_atoms={', '.join(unmapped_atom_ids[:12])}; linked_tcs={', '.join(test_case_ids[:8])}"
                    )
        if applicable == "unclear" and not gap_ids:
            missing_unclear_gap.append(f"{row_label}:gap={gap_id or '-'}")
        if applicable == "no" and not (meaningful_matrix_value(source_ref) or meaningful_matrix_value(reason)):
            unsupported_no_rows.append(row_label)
        if applicable == "no" and dimension in INTEGRATION_RELATED_DIMENSIONS and has_integration_gap_evidence:
            hidden_integration_gap_rows.append(f"{row_label}:source_ref={source_ref or '-'}; reason={reason or '-'}")
        if applicable == "no" and dimension == "equivalence" and has_numeric_only_evidence:
            hidden_numeric_equivalence_rows.append(f"{row_label}:source_ref={source_ref or '-'}; reason={reason or '-'}")
        if applicable == "no" and dimension == "numeric" and has_numeric_only_evidence:
            hidden_numeric_rows.append(f"{row_label}:source_ref={source_ref or '-'}; reason={reason or '-'}")

    if invalid_applicability:
        findings.append(
            Finding(
                id="test-design-applicability-matrix-invalid-applicable",
                severity="warning",
                category="test-design",
                title="Test-design applicability matrix has invalid applicable values",
                details="The applicable column must use exactly yes, no, or unclear.",
                path=display_path,
                evidence=invalid_applicability[:20],
                recommended_action="Normalize applicable values to yes, no, or unclear.",
            )
        )
    if unknown_dimensions:
        findings.append(
            Finding(
                id="test-design-applicability-matrix-unknown-dimension",
                severity="warning",
                category="test-design",
                title="Test-design applicability matrix uses unknown coverage dimensions",
                details="Dimension values should use the coverage_dimension vocabulary from review-findings-format.md.",
                path=display_path,
                evidence=unknown_dimensions[:20],
                recommended_action="Use a canonical coverage_dimension value or `other` with an explanation.",
            )
        )
    if missing_yes_links:
        findings.append(
            Finding(
                id="test-design-applicability-matrix-uncovered-applicable-dimension",
                severity="warning",
                category="test-design",
                title="Applicable test-design dimensions lack test-case or gap links",
                details="Rows with applicable = yes must link at least one ATOM-* and either TC-* or GAP-*.",
                path=display_path,
                evidence=missing_yes_links[:20],
                recommended_action="Link the applicable dimension to covered test cases or record a coverage gap before ready-for-review.",
            )
        )
    if missing_unclear_gap:
        findings.append(
            Finding(
                id="test-design-applicability-matrix-unclear-without-gap",
                severity="warning",
                category="test-design",
                title="Unclear applicability rows lack gap ids",
                details="Rows with applicable = unclear must link a GAP-* so the missing decision is traceable.",
                path=display_path,
                evidence=missing_unclear_gap[:20],
                recommended_action="Create a GAP-* with the analyst question and link it from the matrix row.",
            )
        )
    if unsupported_no_rows:
        findings.append(
            Finding(
                id="test-design-applicability-matrix-unsupported-no",
                severity="warning",
                category="test-design",
                title="Not-applicable rows lack source-based reason",
                details="Rows with applicable = no need source_ref or reason; otherwise reviewer cannot distinguish non-applicability from omission.",
                path=display_path,
                evidence=unsupported_no_rows[:20],
                recommended_action="Add a concrete source_ref or reason proving the dimension is absent or out of scope.",
            )
        )
    if invalid_gap_refs:
        findings.append(
            Finding(
                id="test-design-applicability-matrix-invalid-gap-id",
                severity="warning",
                category="test-design",
                title="Test-design applicability matrix has invalid gap ids",
                details="Gap links must use GAP-* or coverage_gap:<short-id>.",
                path=display_path,
                evidence=invalid_gap_refs[:20],
                recommended_action="Replace noncanonical gap references with stable GAP-* ids.",
            )
        )
    if linked_tc_dimension_mismatches:
        findings.append(
            Finding(
                id="test-design-applicability-matrix-linked-tc-dimension-mismatch",
                severity="warning",
                category="test-design",
                title="Applicability matrix links a dimension to TC-* that does not exercise it",
                details=(
                    "A matrix row is not covered merely because it names a TC id. The linked TC must contain steps, "
                    "data and an expected result that actually exercise the declared coverage dimension."
                ),
                path=display_path,
                evidence=linked_tc_dimension_mismatches[:20],
                recommended_action=(
                    "Link the matrix row to TC-* that really cover the dimension, add missing TC-* coverage, "
                    "or replace the link with a concrete GAP-*."
                ),
            )
        )
    if linked_atom_contamination_rows:
        findings.append(
            Finding(
                id="test-design-applicability-matrix-linked-atom-contamination",
                severity="warning",
                category="test-design",
                title="Applicability matrix linked atoms are not exercised by linked test cases",
                details=(
                    "Rows with applicable = yes should not inflate coverage by listing ATOM-* ids that are not "
                    "referenced by the linked TC-* blocks and are not routed to a GAP-*. This often means metadata "
                    "or source-property atoms were counted as coverage for the row dimension."
                ),
                path=display_path,
                evidence=linked_atom_contamination_rows[:20],
                recommended_action=(
                    "Remove unrelated metadata/source-property atoms from the matrix row, add real TC-* coverage "
                    "for them, or link the blocked/non-executable atoms to a concrete GAP-*."
                ),
            )
        )
    if unknown_test_case_ids:
        findings.append(
            Finding(
                id="test-design-applicability-matrix-unknown-test-case-id",
                severity="warning",
                category="test-design",
                title="Test-design applicability matrix references unknown test-case ids",
                details="linked_test_cases must point to canonical ## TC-* sections in the same FT package.",
                path=display_path,
                evidence=unknown_test_case_ids[:20],
                recommended_action="Create the referenced test cases or update linked_test_cases to existing TC-* ids.",
            )
        )
    if hidden_integration_gap_rows:
        findings.append(
            Finding(
                id="test-design-applicability-matrix-hidden-integration-gap",
                severity="warning",
                category="test-design",
                title="Applicability matrix marks integration/API-like dimension as not applicable despite GAP evidence",
                details=(
                    "If the artifact contains GAP evidence for API, RabbitMQ, DaData, kladr, Connect, backend, "
                    "database, async or external reference behavior, related applicability rows cannot be hidden "
                    "as `no`. They should be `yes` or `unclear` and linked to the relevant GAP-*."
                ),
                path=display_path,
                evidence=hidden_integration_gap_rows[:20],
                recommended_action=(
                    "Change the affected dimension to `yes` with TC/GAP links or to `unclear` with GAP-* links. "
                    "Do not classify unresolved integration/internal behavior as not applicable."
                ),
            )
        )
    if hidden_numeric_equivalence_rows:
        findings.append(
            Finding(
                id="test-design-applicability-matrix-hidden-numeric-equivalence-gap",
                severity="warning",
                category="test-design",
                title="Applicability matrix marks equivalence as not applicable despite numeric-only rules",
                details=(
                    "A numeric-only or digits-only source rule creates equivalence classes for valid numeric values "
                    "and invalid nonnumeric values. The matrix should not mark `equivalence = no` unless the file "
                    "gives a source-based reason why those classes are intentionally out of scope."
                ),
                path=display_path,
                evidence=hidden_numeric_equivalence_rows[:20],
                recommended_action=(
                    "Change equivalence to `yes` and link the relevant TC/GAP rows, or document an explicit "
                    "source-based non-applicability decision that does not hide numeric-only invalid classes."
                ),
            )
        )
    if hidden_numeric_rows:
        findings.append(
            Finding(
                id="test-design-applicability-matrix-hidden-numeric-gap",
                severity="warning",
                category="test-design",
                title="Applicability matrix marks numeric as not applicable despite numeric-only rules",
                details=(
                    "A numeric-only or digits-only source rule makes numeric input coverage applicable. "
                    "The matrix should not mark `numeric = no` while the same artifact contains numeric/digits-only "
                    "requirements or numeric invalid-class coverage."
                ),
                path=display_path,
                evidence=hidden_numeric_rows[:20],
                recommended_action=(
                    "Change numeric to `yes` and link the relevant ATOM/TC/GAP rows, or document a source-backed "
                    "reason why numeric coverage is genuinely outside the selected scope."
                ),
            )
        )

    has_warnings = any(finding.severity == "warning" for finding in findings)
    checks.append(
        Check(
            "test-design-applicability-matrix",
            "warn" if has_warnings else "pass",
            "Applicability matrix contract has issues." if has_warnings else "Applicability matrix contract passed.",
            display_path,
        )
    )
    return findings, checks


def validate_pairwise_supporting_table(
    content: str,
    path: Path,
    root: Path,
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    rows = parsed_test_design_applicability_rows(content)
    pairwise_yes_rows = [
        row
        for row in rows
        if row.get("dimension", "").strip().lower() == "pairwise"
        and row.get("applicable", "").strip().lower() == "yes"
    ]
    if not pairwise_yes_rows:
        return findings, checks

    section = extract_markdown_section(content, "Combinatorial Coverage Table")
    if section is None:
        findings.append(
            Finding(
                id="test-case-pairwise-table-missing",
                severity="warning",
                category="test-design",
                title="Pairwise applicability has no Combinatorial Coverage Table",
                details=(
                    "When the applicability matrix marks pairwise as applicable, the canonical test-case file "
                    "must record factors, constraints, selected combinations, high-risk additions, and TC/GAP links."
                ),
                path=display_path,
                evidence=[
                    f"pairwise row: source_ref={row.get('source_ref', '-')}; linked_test_cases={row.get('linked_test_cases', '-')}; gap_id={row.get('gap_id', '-')}"
                    for row in pairwise_yes_rows[:5]
                ],
                recommended_action="Add a ## Combinatorial Coverage Table section or link the unresolved decision to GAP-* before review.",
            )
        )
        checks.append(Check("test-case-pairwise-supporting-table", "warn", "Pairwise table is missing.", display_path))
        return findings, checks

    table_rows = markdown_table_rows_from_text(section)
    headers = [normalize_table_header(row) for row in table_rows]
    has_factor_table = any(
        {"factor", "values", "source_ref"}.issubset(set(header))
        and any("constraints" in column for column in header)
        for header in headers
    )
    has_combination_table = any(
        {"combination_id", "factor_values", "reason", "linked_atoms"}.issubset(set(header))
        and any(column in {"tc_gap", "tc_or_gap", "tc_gap"} or "tc" in column and "gap" in column for column in header)
        for header in headers
    )

    if not has_factor_table or not has_combination_table:
        missing_parts = []
        if not has_factor_table:
            missing_parts.append("factor table")
        if not has_combination_table:
            missing_parts.append("combination table")
        findings.append(
            Finding(
                id="test-case-pairwise-table-incomplete",
                severity="warning",
                category="test-design",
                title="Combinatorial Coverage Table misses required pairwise structure",
                details="Pairwise coverage needs both a factors/values table and a selected combinations table.",
                path=display_path,
                evidence=missing_parts,
                recommended_action=(
                    "Add factor | values | source_ref | constraints / impossible combinations and "
                    "combination_id | factor_values | reason | linked_atoms | TC/gap tables."
                ),
            )
        )

    has_warnings = any(finding.severity == "warning" for finding in findings)
    checks.append(
        Check(
            "test-case-pairwise-supporting-table",
            "warn" if has_warnings else "pass",
            "Pairwise supporting table has issues." if has_warnings else "Pairwise supporting table contract passed.",
            display_path,
        )
    )
    return findings, checks


def extract_test_case_expected_result(block: str) -> str:
    match = re.search(
        r"^\*\*(?:Expected Result|expected_result|expected result|Итоговый ожидаемый результат|Ожидаемый результат):\*\*\s*(.*)$",
        block,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    return match.group(1).strip() if match else ""


def extract_test_case_type(block: str) -> str:
    match = re.search(
        r"^\*\*(?:Type|\u0422\u0438\u043f):\*\*\s*`?([^`\n]+?)`?\s*$",
        block,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    return match.group(1).strip().lower() if match else ""


def calculation_oracle_issue(test_case_id: str, block: str) -> str | None:
    block_lower = block.lower()
    expected_result = extract_test_case_expected_result(block)
    expected_lower = expected_result.lower()

    vague_expected = bool(
        re.search(
            r"(корректн|согласно\s+формул|according\s+to\s+formula|calculated\s+correctly)",
            expected_lower,
        )
    )
    has_formula_or_source = bool(
        re.search(r"(formula|формул|source|источник|req[-\s]?\d+|gsr\s+\d+|=|×|\bx\b|\*|%)", block_lower)
    )
    has_input_values = bool(
        re.search(
            r"(test data|тестовые данные|input|входн|сумм|amount|rate|ставк)[\s\S]{0,200}\d",
            block_lower,
        )
    )
    has_expected_numeric_result = bool(expected_result and re.search(r"\d", expected_result))

    missing_parts: list[str] = []
    if vague_expected:
        missing_parts.append("expected result is vague")
    if not has_formula_or_source:
        missing_parts.append("formula/source reference")
    if not has_input_values:
        missing_parts.append("input values")
    if not has_expected_numeric_result:
        missing_parts.append("manually calculated expected result")

    return f"{test_case_id}: missing {', '.join(missing_parts)}" if missing_parts else None


def validate_calculation_oracles(
    content: str,
    path: Path,
    root: Path,
    blocks: list[tuple[str, str]],
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    rows = parsed_test_design_applicability_rows(content)
    calculation_rows = [
        row
        for row in rows
        if row.get("dimension", "").strip().lower() == "calculation"
        and row.get("applicable", "").strip().lower() == "yes"
    ]
    if not calculation_rows:
        return findings, checks

    block_by_id = {test_case_id: block for test_case_id, block in blocks}
    linked_case_ids: set[str] = set()
    for row in calculation_rows:
        linked_case_ids.update(extract_test_case_ids_from_text(row.get("linked_test_cases", "")))

    if not linked_case_ids:
        return findings, checks

    oracle_issues = [
        issue
        for test_case_id in sorted(linked_case_ids)
        if (block := block_by_id.get(test_case_id))
        if (issue := calculation_oracle_issue(test_case_id, block))
    ]

    if oracle_issues:
        findings.append(
            Finding(
                id="test-case-calculation-oracle-missing",
                severity="warning",
                category="test-design",
                title="Calculation test cases miss required calculation oracle",
                details=(
                    "Calculation cases linked from the applicability matrix must include a formula/source reference, "
                    "concrete input values, and a manually calculated expected result."
                ),
                path=display_path,
                evidence=oracle_issues[:20],
                recommended_action=(
                    "Add calculation oracle details to each affected TC-* or move undefined formula/rounding behavior "
                    "to a traceable GAP-*."
                ),
            )
        )

    checks.append(
        Check(
            "test-case-calculation-oracle",
            "warn" if oracle_issues else "pass",
            "Calculation oracle has issues." if oracle_issues else "Calculation oracle contract passed.",
            display_path,
        )
    )
    return findings, checks


def extract_test_case_priority(block: str) -> str | None:
    match = re.search(
        r"^\*\*(?:Priority|Приоритет):\*\*\s*`?(High|Medium|Low)`?",
        block,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    return match.group(1).capitalize() if match else None


def validate_risk_priority_map(
    content: str,
    path: Path,
    root: Path,
    blocks: list[tuple[str, str]],
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    applicability_rows = parsed_test_design_applicability_rows(content)
    high_risk_applicable_rows = [
        row
        for row in applicability_rows
        if row.get("dimension", "").strip().lower() in HIGH_RISK_DIMENSION_CANDIDATES
        and row.get("applicable", "").strip().lower() == "yes"
    ]

    section = extract_markdown_section(content, "Risk / Priority Map")
    if section is None:
        if high_risk_applicable_rows:
            findings.append(
                Finding(
                    id="test-case-risk-priority-map-missing",
                    severity="warning",
                    category="test-design",
                    title="High-risk applicability has no Risk / Priority Map",
                    details=(
                        "When high-risk dimensions are applicable, the canonical test-case file must map "
                        "high-risk atoms to required priority, linked High TC-* cases, or blocking GAP-* ids."
                    ),
                    path=display_path,
                    evidence=[
                        f"{row.get('dimension', '-')}: source_ref={row.get('source_ref', '-')}; linked_atoms={row.get('linked_atoms', '-')}"
                        for row in high_risk_applicable_rows[:10]
                    ],
                    recommended_action="Add a ## Risk / Priority Map section or mark the unresolved high-risk coverage as GAP-*.",
                )
            )
            checks.append(Check("test-case-risk-priority-map", "warn", "Risk / Priority Map is missing.", display_path))
        return findings, checks

    rows = markdown_table_rows_from_text(section)
    if not rows:
        findings.append(
            Finding(
                id="test-case-risk-priority-map-no-table",
                severity="warning",
                category="test-design",
                title="Risk / Priority Map has no Markdown table",
                details="The section exists but has no parseable Markdown table.",
                path=display_path,
                evidence=[],
                recommended_action="Use the canonical Risk / Priority Map columns from writer-output-format.md.",
            )
        )
        checks.append(Check("test-case-risk-priority-map", "warn", "Risk / Priority Map table is missing.", display_path))
        return findings, checks

    header = normalize_table_header(rows[0])
    missing_columns = sorted(RISK_PRIORITY_MAP_REQUIRED_COLUMNS - set(header))
    if missing_columns:
        findings.append(
            Finding(
                id="test-case-risk-priority-map-missing-columns",
                severity="warning",
                category="test-design",
                title="Risk / Priority Map misses required columns",
                details="The map must expose atom id, risk, required priority, TC/GAP links, and rationale.",
                path=display_path,
                evidence=[f"missing={', '.join(missing_columns)}", f"columns={', '.join(header[:12])}"],
                recommended_action="Add the missing columns from writer-output-format.md.",
            )
        )
        checks.append(Check("test-case-risk-priority-map", "warn", "Risk / Priority Map columns are incomplete.", display_path))
        return findings, checks

    column_index = {name: index for index, name in enumerate(header)}
    ledger_atom_ids = atomic_requirement_ledger_atom_ids(content)
    priority_by_tc = {test_case_id: extract_test_case_priority(block) for test_case_id, block in blocks}
    invalid_risk_levels: list[str] = []
    invalid_priorities: list[str] = []
    invalid_atom_ids: list[str] = []
    unknown_test_case_ids: list[str] = []
    high_without_high_priority: list[str] = []
    high_without_coverage: list[str] = []
    high_without_high_tc_or_gap: list[str] = []

    for row_number, row in enumerate(rows[1:], start=2):
        def cell(name: str) -> str:
            index = column_index[name]
            return row[index].strip().strip("`") if index < len(row) else ""

        atom_id = cell("atom_id")
        risk_level = cell("risk_level").lower()
        required_priority = cell("required_priority").lower()
        linked_test_cases = cell("linked_test_cases")
        gap_id = cell("gap_id")
        row_label = f"row {row_number}:{atom_id or '<missing atom>'}"

        if atom_id and not is_valid_risk_priority_atom_id(atom_id, ledger_atom_ids):
            invalid_atom_ids.append(row_label)
        if risk_level not in {"high", "medium", "low"}:
            invalid_risk_levels.append(f"{row_label}:risk_level={risk_level or '<missing>'}")
            continue
        if required_priority not in {"high", "medium", "low"}:
            invalid_priorities.append(f"{row_label}:required_priority={required_priority or '<missing>'}")

        test_case_ids = extract_test_case_ids_from_text(linked_test_cases)
        gap_ids = extract_gap_ids_from_text(gap_id)
        unknown_ids = [test_case_id for test_case_id in test_case_ids if test_case_id not in priority_by_tc]
        unknown_test_case_ids.extend(f"{row_label}:{test_case_id}" for test_case_id in unknown_ids)

        if risk_level == "high":
            has_high_tc = any(priority_by_tc.get(test_case_id) == "High" for test_case_id in test_case_ids)
            if required_priority != "high":
                high_without_high_priority.append(f"{row_label}:required_priority={required_priority or '<missing>'}")
            if not test_case_ids and not gap_ids:
                high_without_coverage.append(row_label)
            if test_case_ids and not has_high_tc and not gap_ids:
                priorities = ", ".join(f"{test_case_id}={priority_by_tc.get(test_case_id) or '<missing>'}" for test_case_id in test_case_ids)
                high_without_high_tc_or_gap.append(f"{row_label}:{priorities}")

    if invalid_atom_ids:
        findings.append(
            Finding(
                id="test-case-risk-priority-map-invalid-atom-id",
                severity="warning",
                category="test-design",
                title="Risk / Priority Map contains invalid atom ids",
                details="Risk rows should point to stable ATOM-* ids or scoped *-ATOM-* ids declared in the Atomic Requirements Ledger.",
                path=display_path,
                evidence=invalid_atom_ids[:20],
                recommended_action="Use stable ATOM-* ids or existing scoped *-ATOM-* ids from the Atomic Requirements Ledger.",
            )
        )
    if invalid_risk_levels:
        findings.append(
            Finding(
                id="test-case-risk-priority-map-invalid-risk-level",
                severity="warning",
                category="test-design",
                title="Risk / Priority Map has invalid risk levels",
                details="risk_level must be high, medium, or low.",
                path=display_path,
                evidence=invalid_risk_levels[:20],
                recommended_action="Normalize risk_level values to high, medium, or low.",
            )
        )
    if invalid_priorities:
        findings.append(
            Finding(
                id="test-case-risk-priority-map-invalid-required-priority",
                severity="warning",
                category="test-design",
                title="Risk / Priority Map has invalid required priorities",
                details="required_priority must be High, Medium, or Low.",
                path=display_path,
                evidence=invalid_priorities[:20],
                recommended_action="Normalize required_priority values to High, Medium, or Low.",
            )
        )
    if unknown_test_case_ids:
        findings.append(
            Finding(
                id="test-case-risk-priority-map-unknown-test-case-id",
                severity="warning",
                category="test-design",
                title="Risk / Priority Map references unknown test-case ids",
                details="linked_test_cases must point to canonical ## TC-* sections in the same file.",
                path=display_path,
                evidence=unknown_test_case_ids[:20],
                recommended_action="Create the referenced test cases or update linked_test_cases to existing TC-* ids.",
            )
        )
    if high_without_high_priority:
        findings.append(
            Finding(
                id="test-case-risk-priority-map-high-risk-without-high-required-priority",
                severity="warning",
                category="test-design",
                title="High-risk atoms do not require High priority",
                details="Rows with risk_level = high must use required_priority = High.",
                path=display_path,
                evidence=high_without_high_priority[:20],
                recommended_action="Set required_priority to High or downgrade risk only with source-backed rationale.",
            )
        )
    if high_without_coverage:
        findings.append(
            Finding(
                id="test-case-risk-priority-map-high-risk-uncovered",
                severity="warning",
                category="test-design",
                title="High-risk atoms have no linked test case or gap",
                details="High-risk atoms must link to at least one TC-* or to a blocking GAP-*.",
                path=display_path,
                evidence=high_without_coverage[:20],
                recommended_action="Link a High priority test case or create a blocking coverage gap.",
            )
        )
    if high_without_high_tc_or_gap:
        findings.append(
            Finding(
                id="test-case-risk-priority-map-high-risk-without-high-test-case",
                severity="warning",
                category="test-design",
                title="High-risk atoms are not covered by High priority test cases",
                details="High-risk rows with linked TC-* ids need at least one linked test case with Priority: High unless a blocking GAP-* is recorded.",
                path=display_path,
                evidence=high_without_high_tc_or_gap[:20],
                recommended_action="Raise at least one linked test case to Priority: High or record a blocking GAP-*.",
            )
        )

    has_warnings = any(finding.severity == "warning" for finding in findings)
    checks.append(
        Check(
            "test-case-risk-priority-map",
            "warn" if has_warnings else "pass",
            "Risk / Priority Map contract has issues." if has_warnings else "Risk / Priority Map contract passed.",
            display_path,
        )
    )
    return findings, checks


def validate_traceability_matrix(
    path: Path,
    root: Path,
    *,
    known_test_case_ids: set[str] | None = None,
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)

    try:
        content = path.read_text(encoding="utf-8")
        rows = markdown_table_rows_from_text(content)
    except UnicodeDecodeError:
        findings.append(
            Finding(
                id="traceability-matrix-not-utf8",
                severity="error",
                category="traceability",
                title="Traceability matrix is not UTF-8",
                details="Traceability matrix artifacts must be readable as UTF-8 Markdown.",
                path=display_path,
                evidence=[],
                recommended_action="Save the matrix as UTF-8 Markdown.",
            )
        )
        checks.append(Check("traceability-matrix-format", "fail", "Traceability matrix is not UTF-8.", display_path))
        return findings, checks

    if not rows:
        findings.append(
            Finding(
                id="traceability-matrix-no-table",
                severity="warning",
                category="traceability",
                title="Traceability matrix has no Markdown table",
                details="The validator could not find a Markdown table in the matrix artifact.",
                path=display_path,
                evidence=[],
                recommended_action="Use the canonical traceability matrix table format.",
            )
        )
        checks.append(Check("traceability-matrix-format", "warn", "Traceability matrix table is missing.", display_path))
        return findings, checks

    placeholder_findings, placeholder_checks = validate_traceability_placeholder_sentinels(content, path, root)
    findings.extend(placeholder_findings)
    checks.extend(placeholder_checks)

    header = [cell.strip().strip("`").lower() for cell in rows[0]]
    if "atom_id" not in header:
        findings.append(
            Finding(
                id="traceability-matrix-legacy-missing-atom-id",
                severity="info",
                category="traceability",
                title="Legacy traceability matrix has no atom_id column",
                details=(
                    "This matrix predates the atom_id / traceability_ref contract. "
                    "Do not mechanically migrate it without a reviewer pass."
                ),
                path=display_path,
                evidence=[f"columns={', '.join(header[:10])}"],
                recommended_action=(
                    "Treat this as a legacy baseline. New or updated matrices should add stable ATOM-* ids."
                ),
            )
        )
        checks.append(Check("traceability-matrix-atom-id", "pass", "Legacy matrix without atom_id recorded as info.", display_path))
        return findings, checks

    atom_index = header.index("atom_id")
    covered_by_tc_index = header.index("covered_by_tc") if "covered_by_tc" in header else None
    atom_ids: list[str] = []
    invalid_atom_ids: list[str] = []
    legacy_unclear_ids: list[str] = []
    unknown_test_case_ids: list[str] = []
    for row in rows[1:]:
        atom_id = row[atom_index].strip().strip("`") if atom_index < len(row) else ""
        if not re.fullmatch(r"ATOM-\d{3,}", atom_id):
            if re.fullmatch(r"UNCLEAR-\d{3,}", atom_id):
                legacy_unclear_ids.append(atom_id)
            else:
                invalid_atom_ids.append(atom_id or "<missing>")
        else:
            atom_ids.append(atom_id)
        if known_test_case_ids and covered_by_tc_index is not None and covered_by_tc_index < len(row):
            referenced_ids = extract_test_case_ids_from_text(row[covered_by_tc_index])
            for test_case_id in referenced_ids:
                if test_case_id not in known_test_case_ids:
                    unknown_test_case_ids.append(f"{atom_id or '<missing>'}:{test_case_id}")

    duplicate_atom_ids = [
        atom_id
        for atom_id, count in Counter(atom_ids).items()
        if count > 1
    ]
    if invalid_atom_ids:
        findings.append(
            Finding(
                id="traceability-matrix-invalid-atom-id",
                severity="warning",
                category="traceability",
                title="Traceability matrix contains invalid atom_id values",
                details="New traceability matrices must use stable ATOM-* ids for every row.",
                path=display_path,
                evidence=invalid_atom_ids[:10],
                recommended_action="Assign stable ids like ATOM-001 without reusing ids for different statements.",
            )
        )
    if legacy_unclear_ids:
        findings.append(
            Finding(
                id="traceability-matrix-legacy-unclear-atom-id",
                severity="info",
                category="traceability",
                title="Traceability matrix uses legacy UNCLEAR-* ids",
                details=(
                    "The matrix has an atom_id column, but some rows use a legacy UNCLEAR-* "
                    "identifier scheme instead of canonical ATOM-* ids."
                ),
                path=display_path,
                evidence=legacy_unclear_ids[:10],
                recommended_action=(
                    "Keep as legacy baseline until the next reviewer pass; new or updated rows should use ATOM-* ids."
                ),
            )
        )
    if duplicate_atom_ids:
        findings.append(
            Finding(
                id="traceability-matrix-duplicate-atom-id",
                severity="warning",
                category="traceability",
                title="Traceability matrix contains duplicate atom_id values",
                details="Each atom_id must identify one atomic statement within the matrix.",
                path=display_path,
                evidence=duplicate_atom_ids[:10],
                recommended_action="Split or rename duplicated atom ids so findings can target one row unambiguously.",
            )
        )
    if unknown_test_case_ids:
        findings.append(
            Finding(
                id="traceability-matrix-unknown-test-case-id",
                severity="warning",
                category="traceability",
                title="Traceability matrix references unknown test-case ids",
                details="covered_by_tc values must point to canonical ## TC-* sections in the same FT package.",
                path=display_path,
                evidence=unknown_test_case_ids[:20],
                recommended_action="Create the referenced test cases or update covered_by_tc to existing TC-* ids.",
            )
        )

    has_warnings = bool(invalid_atom_ids or duplicate_atom_ids or unknown_test_case_ids)
    checks.append(
        Check(
            "traceability-matrix-atom-id",
            "warn" if has_warnings else "pass",
            "Traceability matrix atom_id contract has issues." if has_warnings else "Traceability matrix atom_id contract passed.",
            display_path,
        )
    )
    return findings, checks


def normalize_markdown_field_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")


def normalize_markdown_field_value(value: str) -> str:
    return strip_quotes(value.strip().strip("`").strip())


def extract_finding_blocks(content: str) -> list[tuple[str, str]]:
    matches = list(
        re.finditer(
            r"^###\s+(FINDING(?:-[A-Z]+)?-\d{3,})\s*$",
            content,
            flags=re.MULTILINE,
        )
    )
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        body_start = match.end()
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        blocks.append((match.group(1), content[body_start:body_end]))
    return blocks


def extract_response_blocks(content: str) -> list[tuple[str, str]]:
    matches = list(
        re.finditer(
            r"^###\s+((?:USER-)?FINDING(?:-[A-Z]+)?-\d{3,})\s*$",
            content,
            flags=re.MULTILINE,
        )
    )
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        body_start = match.end()
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        blocks.append((match.group(1), content[body_start:body_end]))
    return blocks


def parse_markdown_fields(block: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in block.splitlines():
        match = re.match(r"^\*\*([^*:\n]+):\*\*\s*(.*)$", line.strip())
        if not match:
            continue
        key = normalize_markdown_field_name(match.group(1))
        fields[key] = normalize_markdown_field_value(match.group(2))
    return fields


def extract_reviewer_signoff_fields(content: str) -> dict[str, str] | None:
    match = re.search(
        r"^##\s+Reviewer Sign-off Self-check\s*$",
        content,
        flags=re.MULTILINE,
    )
    if not match:
        return None

    next_heading = re.search(r"^##\s+", content[match.end():], flags=re.MULTILINE)
    body_end = match.end() + next_heading.start() if next_heading else len(content)
    return parse_markdown_fields(content[match.end():body_end])


def reviewer_signoff_field_issues(fields: dict[str, str]) -> list[str]:
    issues: list[str] = []
    missing = sorted(REQUIRED_REVIEWER_SIGNOFF_FIELDS - set(fields))
    issues.extend(f"missing:{field}" for field in missing)

    for field in sorted(REVIEWER_SIGNOFF_YES_FIELDS):
        value = fields.get(field)
        if value is not None and value != "yes":
            issues.append(f"{field}={value or '<empty>'}")

    for field in sorted(REVIEWER_SIGNOFF_YES_OR_NA_FIELDS):
        value = fields.get(field)
        if value is not None and value not in {"yes", "not-applicable"}:
            issues.append(f"{field}={value or '<empty>'}")

    known_unclear_items = fields.get("known_unclear_items")
    if known_unclear_items is not None and (not known_unclear_items or "<" in known_unclear_items):
        issues.append(f"known_unclear_items={known_unclear_items or '<empty>'}")

    rationale = fields.get("sign_off_rationale")
    if rationale is not None:
        normalized = re.sub(r"[^a-z]+", "", rationale.lower())
        if not rationale or normalized in {"signedoff", "signoff"} or "<" in rationale:
            issues.append(f"sign_off_rationale={rationale or '<empty>'}")

    return issues


def finding_refs_by_id(path: Path) -> dict[str, list[str]]:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return {}

    refs: dict[str, list[str]] = {}
    for finding_id, block in extract_finding_blocks(content):
        fields = parse_markdown_fields(block)
        if fields.get("review_mode") != "traceability":
            continue

        candidates = [
            fields.get("traceability_ref", ""),
            fields.get("coverage_gap", ""),
        ]
        values: list[str] = []
        for candidate in candidates:
            values.extend(
                match.group(1)
                for match in re.finditer(
                    r"\b(ATOM-\d{3,}|coverage_gap:[a-z0-9][a-z0-9_-]*)\b",
                    candidate,
                )
            )
        if values:
            refs[finding_id] = sorted(set(values))
    return refs


def response_traceability_refs(block: str, fields: dict[str, str]) -> list[str]:
    values: list[str] = []
    field_value = fields.get("affected_traceability_refs", "")
    candidates = [field_value, block]
    for candidate in candidates:
        values.extend(
            match.group(1)
            for match in re.finditer(
                r"\b(ATOM-\d{3,}|coverage_gap:[a-z0-9][a-z0-9_-]*)\b",
                candidate,
            )
        )
    return sorted(set(values))


def validate_review_findings(
    path: Path,
    root: Path,
    *,
    findings_policy: str = "compatible",
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        findings.append(
            Finding(
                id="review-findings-not-utf8",
                severity="error",
                category="review-findings",
                title="Review findings artifact is not UTF-8",
                details=str(exc),
                path=display_path,
                evidence=[],
                recommended_action="Save the findings artifact as UTF-8 Markdown.",
            )
        )
        checks.append(Check("review-findings-format", "fail", "Review findings artifact is not UTF-8.", display_path))
        return findings, checks

    blocks = extract_finding_blocks(content)
    if not blocks:
        checks.append(Check("review-findings-format", "pass", "No structured findings blocks found.", display_path))
        return findings, checks

    seen_ids: set[str] = set()
    missing_fields: list[str] = []
    invalid_enums: list[str] = []
    invalid_traceability_refs: list[str] = []
    missing_traceability_refs: list[str] = []
    duplicate_ids: list[str] = []

    for finding_id, block in blocks:
        if finding_id in seen_ids:
            duplicate_ids.append(finding_id)
        seen_ids.add(finding_id)

        fields = parse_markdown_fields(block)
        missing = sorted(REQUIRED_FINDING_FIELDS - set(fields))
        if "test_case_id" not in fields and "coverage_gap" not in fields:
            missing.append("test_case_id|coverage_gap")
        missing_fields.extend(f"{finding_id}:{field}" for field in missing)

        review_mode = fields.get("review_mode")
        severity = fields.get("severity")
        category = fields.get("category")
        status = fields.get("status")
        if review_mode is not None and review_mode not in ALLOWED_REVIEW_MODES:
            invalid_enums.append(f"{finding_id}:review_mode={review_mode}")
        if severity is not None and severity not in ALLOWED_FINDING_SEVERITIES:
            invalid_enums.append(f"{finding_id}:severity={severity}")
        if category is not None and category not in ALLOWED_FINDING_CATEGORIES:
            invalid_enums.append(f"{finding_id}:category={category}")
        if status is not None and status not in ALLOWED_FINDING_STATUSES:
            invalid_enums.append(f"{finding_id}:status={status}")

        if review_mode == "traceability":
            traceability_ref = fields.get("traceability_ref")
            if traceability_ref:
                if not re.fullmatch(r"(ATOM-\d{3,}|coverage_gap:[a-z0-9][a-z0-9_-]*)", traceability_ref):
                    invalid_traceability_refs.append(f"{finding_id}:{traceability_ref}")
            else:
                fallback_ref = fields.get("coverage_gap", "")
                missing_traceability_refs.append(
                    f"{finding_id}:legacy coverage_gap={fallback_ref}" if fallback_ref else f"{finding_id}:<missing traceability_ref>"
                )

    if duplicate_ids:
        findings.append(
            Finding(
                id="review-findings-duplicate-id",
                severity="warning",
                category="review-findings",
                title="Review findings artifact contains duplicate finding ids",
                details="Each finding id should identify one reviewer finding.",
                path=display_path,
                evidence=duplicate_ids[:10],
                recommended_action="Rename duplicate findings so writer responses can target one finding unambiguously.",
            )
        )
    if missing_fields:
        findings.append(
            Finding(
                id="review-findings-missing-required-fields",
                severity="warning",
                category="review-findings",
                title="Review findings artifact misses required fields",
                details="Structured findings must include the canonical fields from review-findings-format.md.",
                path=display_path,
                evidence=missing_fields[:20],
                recommended_action="Add the missing canonical fields to every structured finding block.",
            )
        )
    if invalid_enums:
        findings.append(
            Finding(
                id="review-findings-invalid-enum",
                severity="warning",
                category="review-findings",
                title="Review findings artifact contains invalid enum values",
                details="Structured finding enum values must match review-findings-format.md.",
                path=display_path,
                evidence=invalid_enums[:20],
                recommended_action="Replace non-canonical enum values with the allowed values.",
            )
        )
    if invalid_traceability_refs:
        findings.append(
            Finding(
                id="review-findings-invalid-traceability-ref",
                severity="warning",
                category="review-findings",
                title="Traceability findings have invalid traceability_ref values",
                details="Traceability findings must point to ATOM-* or coverage_gap:<short-id>.",
                path=display_path,
                evidence=invalid_traceability_refs[:20],
                recommended_action="Use traceability_ref from the matrix atom_id column or a coverage_gap:<short-id> placeholder.",
            )
        )
    if missing_traceability_refs:
        severity = "warning" if findings_policy == "strict" else "info"
        findings.append(
            Finding(
                id="review-findings-legacy-missing-traceability-ref",
                severity=severity,
                category="review-findings",
                title="Traceability findings use legacy coverage_gap instead of traceability_ref",
                details=(
                    "The finding is targetable through coverage_gap text, but it does not use the canonical "
                    "traceability_ref field required for stable reviewer-writer handoff."
                ),
                path=display_path,
                evidence=missing_traceability_refs[:20],
                recommended_action="When this artifact is next updated, add Traceability Ref with the same ATOM-* or coverage_gap:<short-id> key.",
            )
        )

    has_warnings = any(finding.severity == "warning" for finding in findings)
    checks.append(
        Check(
            "review-findings-format",
            "warn" if has_warnings else "pass",
            "Review findings format contract has issues." if has_warnings else "Review findings format contract passed.",
            display_path,
        )
    )
    return findings, checks


def validate_writer_response(
    path: Path,
    root: Path,
    *,
    writer_response_policy: str = "compatible",
    known_test_case_ids: set[str] | None = None,
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    legacy_severity = "warning" if writer_response_policy == "strict" else "info"

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        findings.append(
            Finding(
                id="writer-response-not-utf8",
                severity="error",
                category="writer-response",
                title="Writer response artifact is not UTF-8",
                details=str(exc),
                path=display_path,
                evidence=[],
                recommended_action="Save the writer response artifact as UTF-8 Markdown.",
            )
        )
        checks.append(Check("writer-response-format", "fail", "Writer response artifact is not UTF-8.", display_path))
        return findings, checks

    blocks = extract_response_blocks(content)
    if not blocks:
        findings.append(
            Finding(
                id="writer-response-legacy-noncanonical",
                severity=legacy_severity,
                category="writer-response",
                title="Writer response artifact has no canonical response blocks",
                details="Canonical writer response artifacts use one ### FINDING-* block per handled finding.",
                path=display_path,
                evidence=[],
                recommended_action="When this artifact is next updated, rewrite it using canonical writer response blocks.",
            )
        )
        checks.append(
            Check(
                "writer-response-format",
                "warn" if legacy_severity == "warning" else "pass",
                "Legacy writer response recorded." if legacy_severity == "info" else "Writer response format contract has issues.",
                display_path,
            )
        )
        return findings, checks

    sibling_findings = path.with_name(path.name.replace("-writer-response.md", "-findings.md"))
    related_traceability_refs = finding_refs_by_id(sibling_findings) if sibling_findings.exists() else {}

    seen_ids: set[str] = set()
    duplicate_ids: list[str] = []
    missing_fields: list[str] = []
    invalid_statuses: list[str] = []
    missing_traceability_refs: list[str] = []
    missing_response_ids: list[str] = []
    unknown_test_case_ids: list[str] = []

    for response_id, block in blocks:
        if response_id in seen_ids:
            duplicate_ids.append(response_id)
        seen_ids.add(response_id)

        fields = parse_markdown_fields(block)
        missing_fields.extend(
            f"{response_id}:{field}"
            for field in sorted(REQUIRED_WRITER_RESPONSE_FIELDS - set(fields))
        )

        resolution_status = fields.get("resolution_status")
        if resolution_status is not None and resolution_status not in ALLOWED_RESOLUTION_STATUSES:
            invalid_statuses.append(f"{response_id}:resolution_status={resolution_status}")

        expected_refs = related_traceability_refs.get(response_id, [])
        if expected_refs:
            actual_refs = response_traceability_refs(block, fields)
            missing_expected_refs = [ref for ref in expected_refs if ref not in actual_refs]
            if missing_expected_refs:
                missing_traceability_refs.append(f"{response_id}:{', '.join(missing_expected_refs)}")

        if known_test_case_ids:
            for test_case_id in extract_test_case_ids_from_text(block):
                if test_case_id not in known_test_case_ids:
                    unknown_test_case_ids.append(f"{response_id}:{test_case_id}")

    if related_traceability_refs:
        missing_response_ids = sorted(set(related_traceability_refs) - seen_ids)

    if duplicate_ids:
        findings.append(
            Finding(
                id="writer-response-duplicate-id",
                severity="warning",
                category="writer-response",
                title="Writer response contains duplicate response ids",
                details="Each writer response block should target one finding id.",
                path=display_path,
                evidence=duplicate_ids[:10],
                recommended_action="Rename or merge duplicate response blocks so each finding has one response.",
            )
        )
    if missing_fields:
        findings.append(
            Finding(
                id="writer-response-missing-required-fields",
                severity="warning",
                category="writer-response",
                title="Writer response misses required canonical fields",
                details="Each writer response block must include resolution status, change summary, and affected test case ids.",
                path=display_path,
                evidence=missing_fields[:20],
                recommended_action="Add the missing canonical fields from review-findings-format.md.",
            )
        )
    if invalid_statuses:
        findings.append(
            Finding(
                id="writer-response-invalid-resolution-status",
                severity="warning",
                category="writer-response",
                title="Writer response uses invalid resolution status",
                details="Resolution status must be fixed, not-fixed-scope, or needs-clarification.",
                path=display_path,
                evidence=invalid_statuses[:20],
                recommended_action="Replace non-canonical statuses with an allowed resolution_status value.",
            )
        )
    if missing_response_ids:
        findings.append(
            Finding(
                id="writer-response-missing-finding-responses",
                severity=legacy_severity,
                category="writer-response",
                title="Writer response does not answer every traceability finding",
                details="The sibling findings artifact contains traceability findings with stable refs that have no response block.",
                path=display_path,
                evidence=missing_response_ids[:20],
                recommended_action="Add one response block for every finding in the related findings artifact.",
            )
        )
    if missing_traceability_refs:
        findings.append(
            Finding(
                id="writer-response-missing-affected-traceability-refs",
                severity=legacy_severity,
                category="writer-response",
                title="Writer response does not preserve affected traceability refs",
                details="Responses to traceability findings should keep the same ATOM-* or coverage_gap:<short-id> refs.",
                path=display_path,
                evidence=missing_traceability_refs[:20],
                recommended_action="Add Affected Traceability Refs or explicitly explain split/merge in Change Summary.",
            )
        )
    if unknown_test_case_ids:
        findings.append(
            Finding(
                id="writer-response-unknown-test-case-id",
                severity="warning",
                category="writer-response",
                title="Writer response references unknown test-case ids",
                details="Affected Test Case IDs should point to canonical ## TC-* sections in the same FT package.",
                path=display_path,
                evidence=unknown_test_case_ids[:20],
                recommended_action="Create the referenced test cases or update Affected Test Case IDs to existing TC-* ids.",
            )
        )

    has_warnings = any(finding.severity == "warning" for finding in findings)
    checks.append(
        Check(
            "writer-response-format",
            "warn" if has_warnings else "pass",
            "Writer response format contract has issues." if has_warnings else "Writer response format contract passed.",
            display_path,
        )
    )
    return findings, checks


def validate_dependency_matrix_support(
    content: str,
    path: Path,
    root: Path,
    *,
    structural_severity: str,
    known_test_case_ids: set[str] | None = None,
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    rows = parsed_test_design_applicability_rows(content)
    dependency_required = any(
        row.get("dimension", "").strip().lower() == "dependency"
        and row.get("applicable", "").strip().lower() == "yes"
        and not extract_gap_ids_from_text(row.get("gap_id", ""))
        for row in rows
    )
    if not dependency_required:
        return findings, checks

    section = extract_markdown_section(content, "Dependency Matrix")
    if section is None:
        findings.append(
            Finding(
                id="test-case-dependency-matrix-missing",
                severity=structural_severity,
                category="test-design",
                title="Dependency applicability has no Dependency Matrix",
                details=(
                    "When dependency is applicable and not fully deferred to GAP-*, the canonical test-case file "
                    "must record controlling values, dependent fields, expected properties, and TC/GAP links."
                ),
                path=display_path,
                evidence=[],
                recommended_action="Add a ## Dependency Matrix section or link unresolved dependency behavior to GAP-*.",
            )
        )
        checks.append(
            Check(
                "test-case-dependency-matrix",
                "warn" if structural_severity == "warning" else "pass",
                "Dependency matrix is missing." if structural_severity == "warning" else "Dependency matrix missing recorded as legacy info.",
                display_path,
            )
        )
        return findings, checks

    table_rows = markdown_table_rows_from_text(section)
    if not table_rows:
        findings.append(
            Finding(
                id="test-case-dependency-matrix-no-table",
                severity=structural_severity,
                category="test-design",
                title="Dependency Matrix has no Markdown table",
                details="The dependency matrix section exists but contains no parseable table.",
                path=display_path,
                evidence=[],
                recommended_action="Use the canonical dependency matrix columns from coverage-checklist.md.",
            )
        )
        checks.append(
            Check(
                "test-case-dependency-matrix",
                "warn" if structural_severity == "warning" else "pass",
                "Dependency matrix table is missing." if structural_severity == "warning" else "Dependency matrix table missing recorded as legacy info.",
                display_path,
            )
        )
        return findings, checks

    header = normalize_table_header(table_rows[0])
    required_any = {
        "controlling_value": {"controlling_value", "trigger_field", "trigger"},
        "dependent_field": {"dependent_field", "dependent"},
        "tc_gap": {"tc_gap", "tc_gaps", "tc_or_gap"},
    }
    missing_groups = [
        group_name
        for group_name, alternatives in required_any.items()
        if not alternatives.intersection(header)
    ]
    if missing_groups:
        findings.append(
            Finding(
                id="test-case-dependency-matrix-missing-columns",
                severity=structural_severity,
                category="test-design",
                title="Dependency Matrix misses required columns",
                details="The matrix must expose controlling value, dependent field, and TC/GAP links.",
                path=display_path,
                evidence=[f"missing={', '.join(missing_groups)}", f"columns={', '.join(header[:12])}"],
                recommended_action="Add controlling_value, dependent_field, and TC/gap columns.",
            )
        )

    if not missing_groups and known_test_case_ids:
        column_index = {name: index for index, name in enumerate(header)}
        tc_gap_column = next(
            (column for column in ("tc_gap", "tc_gaps", "tc_or_gap") if column in column_index),
            None,
        )
        unknown_test_case_ids: list[str] = []
        if tc_gap_column:
            tc_gap_index = column_index[tc_gap_column]
            for row_number, raw_row in enumerate(table_rows[1:], start=2):
                value = raw_row[tc_gap_index].strip() if tc_gap_index < len(raw_row) else ""
                for test_case_id in extract_test_case_ids_from_text(value):
                    if test_case_id not in known_test_case_ids:
                        unknown_test_case_ids.append(f"row {row_number}:{test_case_id}")
        if unknown_test_case_ids:
            findings.append(
                Finding(
                    id="test-case-dependency-matrix-unknown-tc-id",
                    severity=structural_severity,
                    category="traceability",
                    title="Dependency Matrix references unknown TC ids",
                    details="Dependency Matrix TC/GAP links must point to existing TC-* sections or GAP-* ids.",
                    path=display_path,
                    evidence=unknown_test_case_ids[:20],
                    recommended_action="Update Dependency Matrix TC links to existing test cases or replace unresolved checks with GAP-*.",
                )
            )

    checks.append(
        Check(
            "test-case-dependency-matrix",
            "warn" if findings and structural_severity == "warning" else "pass",
            "Dependency matrix contract has issues." if findings and structural_severity == "warning" else "Dependency matrix contract passed or legacy info only.",
            display_path,
        )
    )
    return findings, checks


SOURCE_TABLE_RESIDUE_PATTERNS = [
    re.compile(
        r"Название\s+Видимость\s+О\s+Р\s+Тип\s+ввода\s+поля\s+Тип\s+значения\s+Примечание",
        flags=re.IGNORECASE,
    ),
    re.compile(r"Тип\s+ввода\s+поля\s+Тип\s+значения\s+Примечание", flags=re.IGNORECASE),
    re.compile(r"\b\d{1,3}\s+Название\s+Видимость\b", flags=re.IGNORECASE),
    re.compile(r"\bО\s+Р\s+Тип\s+ввода\s+поля\b", flags=re.IGNORECASE),
]

COMBINED_BEHAVIOR_SMELL_PATTERNS = [
    re.compile(r"\brequiredness\s+and\s+format\b", flags=re.IGNORECASE),
    re.compile(r"\bvisibility\s+and\s+format\b", flags=re.IGNORECASE),
    re.compile(r"\bconditional\s+visibility\s+and\s+format\b", flags=re.IGNORECASE),
    re.compile(r"\bdependency\s+and\s+validation\b", flags=re.IGNORECASE),
    re.compile(r"\blength\s+and\s+repeated\s+digits\b", flags=re.IGNORECASE),
    re.compile(r"\bvisibility\s+and\s+requiredness\b", flags=re.IGNORECASE),
    re.compile(r"\b(?:visible|displayed|hidden|visibility)\b[\s\S]{0,100}\b(?:required|requiredness|mandatory)\b", flags=re.IGNORECASE),
    re.compile(r"\b(?:required|requiredness|mandatory)\b[\s\S]{0,100}\b(?:visible|displayed|hidden|visibility)\b", flags=re.IGNORECASE),
    re.compile(r"(?:видим|отображ|скрыт)[\s\S]{0,120}(?:обязател|не\s+обязател)", flags=re.IGNORECASE),
    re.compile(r"(?:обязател|не\s+обязател)[\s\S]{0,120}(?:видим|отображ|скрыт)", flags=re.IGNORECASE),
    re.compile(r"(?:длин[аы]|формат|числов\w+\s+символ\w*|цифр\w*)[\s\S]{0,90}\bи\b[\s\S]{0,90}(?:повтор|одинаков)", flags=re.IGNORECASE),
    re.compile(r"допустим\w+\s+только[\s\S]{0,90}\bи\b[\s\S]{0,90}(?:нет|не\s+долж\w*)", flags=re.IGNORECASE),
    re.compile(r"\bcondition\s*=\s*true\s*/\s*false\b", flags=re.IGNORECASE),
    re.compile(r"\bprevious\s+data\s+branches\b", flags=re.IGNORECASE),
    re.compile(r"\bvalidate\s+by\s+FT\s+rules\b", flags=re.IGNORECASE),
    re.compile(r"\bsame\s+constraints\b", flags=re.IGNORECASE),
    re.compile(r"\brequiredness\s*/\s*editability\b", flags=re.IGNORECASE),
    re.compile(r"\bformat\s*/\s*date\b", flags=re.IGNORECASE),
    re.compile(r"\bvisibility\s*/\s*requiredness\b", flags=re.IGNORECASE),
]

SOURCE_NORMALIZATION_PROPERTY_CLASS_PATTERNS = {
    "visibility": re.compile(r"\bvisibility\b|\bvisible\b|\bhidden\b|видим|отображ|скрыт", flags=re.IGNORECASE),
    "requiredness": re.compile(r"\brequired(?:ness)?\b|\bmandatory\b|обязател", flags=re.IGNORECASE),
    "editability": re.compile(r"\bedit(?:able|ability)\b|\benabled\b|редактир", flags=re.IGNORECASE),
    "input-widget": re.compile(r"\bwidget\b|\binput[-_ ]?type\b|\bdropdown\b|\bselect\b|\bcheckbox\b|тип\s+ввода|список|переключ", flags=re.IGNORECASE),
    "dictionary-source": re.compile(r"\bdictionary\b|\breference[-_ ]?list\b|справочник|справочн|перечень", flags=re.IGNORECASE),
    "numeric-format": re.compile(r"\bnumeric\b|\bnumber\b|\bdigits?\b|числов|цифр", flags=re.IGNORECASE),
    "length-format": re.compile(r"\blength\b|длин", flags=re.IGNORECASE),
    "max-boundary": re.compile(r"\bmax(?:imum)?\b|максимальн|верхн", flags=re.IGNORECASE),
    "min-boundary": re.compile(r"\bmin(?:imum)?\b|минимальн|нижн", flags=re.IGNORECASE),
    "default-value": re.compile(r"\bdefault\b|по\s+умолч|предзаполн", flags=re.IGNORECASE),
    "integration-prefill": re.compile(r"\bprefill\b|\bauto[-_ ]?fill\b|\bapi\b|dadata|автозаполн|интеграц", flags=re.IGNORECASE),
}

DICTIONARY_SOURCE_TEXT_RE = re.compile(
    r"\bdictionary\b|\breference[-_ ]?(?:list|source)\b|справочн|справочник|перечень\s+значени",
    flags=re.IGNORECASE,
)
DICTIONARY_PROPERTY_TYPE_RE = re.compile(
    r"dictionary|reference[-_ ]?list|amount-tags|tag-values|table-list|checkbox-list|"
    r"справочн|справочник|выбор-из-списка|список-чекбоксов|теги-суммы",
    flags=re.IGNORECASE,
)

WRITER_QUALITY_GATE_REQUIRED_COLUMNS = {
    "gate_item",
    "status",
    "evidence",
    "affected_package",
    "required_action",
    "blocks_ready_for_review",
}

WRITER_QUALITY_GATE_REQUIRED_ITEMS = {
    "artifact-write-strategy",
    "mockup-visual-inventory",
    "source-row-inventory",
    "source-normalization-atomic",
    "test-design-decision-table",
    "test-design-review",
    "gap-admissibility",
    "ledger-atomicity",
    "gsr-range-compression",
    "design-plan-atomicity",
    "scenario-does-not-replace-atomic",
    "tc-atomicity",
    "test-data-specificity",
    "internal-observability",
    "action-observability",
    "semantic-req-id-parity",
    "scoped-validator-findings",
    "package-ready",
}

WRITER_QUALITY_GATE_FAIL_STATUSES = {"fail", "blocked", "needs-rewrite"}
WRITER_QUALITY_GATE_PASS_STATUSES = {"pass"}
WRITER_QUALITY_GATE_BLOCK_VALUES = {"yes", "no"}
SCOPED_VALIDATOR_PROFILE_REQUIRED_KEYS = {
    "command",
    "generated_by",
    "scope_slug",
    "canonical_test_cases",
    "test_design_dir",
    "current_scope_findings",
    "unresolved_warning_error_count",
}

TEST_DESIGN_REVIEW_REQUIRED_COLUMNS = {
    "review_item",
    "status",
    "severity",
    "affected_package",
    "evidence",
    "required_action",
    "blocks_ready_for_review",
}
TEST_DESIGN_REVIEW_REQUIRED_ITEMS = {
    "decision-table-classification",
    "ledger-plan-alignment",
    "coverage-class-completeness",
    "numeric-length-boundaries",
    "unsupported-ui-mechanism",
    "mask-format-coverage",
    "dictionary-closed-set",
    "conditional-branches",
    "negative-fixture-isolation",
    "applicability-linked-tc-semantics",
    "gap-specificity",
    "gap-admissibility",
    "internal-observability",
    "metadata-only-exclusion",
    "tc-mapping-atomicity",
    "ready-for-tc-writing",
}
TEST_DESIGN_REVIEW_FAIL_STATUSES = {"fail", "blocked", "needs-rewrite"}
TEST_DESIGN_REVIEW_PASS_STATUSES = {"pass"}
TEST_DESIGN_REVIEW_SEVERITIES = {"error", "warning", "info"}
TEST_DESIGN_REVIEW_BLOCK_VALUES = {"yes", "no"}
SCOPED_VALIDATOR_PROFILE_PLACEHOLDER_COMMANDS = {
    "",
    "-",
    "n/a",
    "na",
    "none",
    "tbd",
    "todo",
    "pending",
    "<pending>",
    "<todo>",
    "<...>",
}
WRITER_GATE_FORBIDDEN_SCOPED_PROFILE_STAGE_RE = re.compile(
    r"scoped-validator-profile\."
    r"(?:structure-preflight|semantic-review|format-review|semantic-regression|reviewer)"
    r"[^/\\]*\.json$",
    flags=re.IGNORECASE,
)

READY_FOR_REVIEW_BLOCKING_TEST_CASE_FINDING_IDS = {
    "source-row-inventory-missing",
    "source-row-inventory-no-table",
    "source-row-inventory-missing-columns",
    "source-row-inventory-invalid-in-scope",
    "source-row-inventory-in-scope-row-without-atom-or-gap",
    "source-row-inventory-unknown-atom-id",
    "source-row-inventory-misses-normalized-source-row",
    "source-table-normalization-missing-for-dirty-ledger",
    "source-table-normalization-no-table",
    "source-table-normalization-missing-columns",
    "source-table-normalization-low-confidence-without-gap",
    "source-table-normalization-residue-smell",
    "source-normalization-combined-property-smell",
    "source-normalization-combined-property-class-smell",
    "source-normalization-missing-property-id",
    "source-normalization-duplicate-property-id",
    "source-normalization-row-has-multiple-gsr",
    "source-row-completeness-matrix-missing",
    "source-row-gsr-count-mismatch",
    "source-normalization-unmapped-property",
    "source-table-normalization-missing-ledger-gap-atom",
    "source-table-normalization-unknown-atom-id",
    "test-design-decision-table-missing",
    "test-design-decision-table-no-table",
    "test-design-decision-table-missing-columns",
    "test-design-decision-table-missing-source-property",
    "test-design-decision-table-duplicate-source-property",
    "test-design-decision-table-invalid-decision",
    "test-design-decision-table-metadata-links-tc",
    "test-design-decision-table-metadata-cross-section-conflict",
    "test-design-decision-table-gap-without-gap-id",
    "test-design-decision-table-missing-ledger-gap-decision",
    "test-design-decision-table-gap-cross-section-conflict",
    "test-design-decision-table-gap-executable-behavior-smell",
    "test-design-decision-table-overbroad-gap-smell",
    "test-design-decision-table-metadata-behavior-smell",
    "test-design-decision-table-date-window-gap-smell",
    "test-design-decision-table-standalone-without-tc-or-oracle",
    "test-design-decision-table-covered-existing-without-tc",
    "test-design-decision-table-scenario-without-tc",
    "test-design-decision-table-scenario-remap-executable-conflict",
    "test-design-decision-table-executable-cross-section-conflict",
    "test-design-decision-table-out-of-scope-without-reason",
    "test-design-decision-table-value-type-standalone-smell",
    "test-design-decision-table-merged-numeric-class-decision",
    "test-design-decision-table-unknown-test-case-id",
    "coverage-obligation-table-missing",
    "coverage-obligation-table-no-table",
    "coverage-obligation-table-missing-columns",
    "coverage-obligation-table-missing-required-class",
    "coverage-obligation-table-unknown-source-property",
    "coverage-obligation-table-duplicate-class",
    "coverage-obligation-table-missing-tc-or-gap",
    "coverage-obligation-table-invalid-status",
    "coverage-obligation-table-unknown-test-case-id",
    "coverage-obligation-table-mask-oracle-missing",
    "test-design-review-missing",
    "test-design-review-no-table",
    "test-design-review-missing-columns",
    "test-design-review-missing-required-items",
    "test-design-review-unknown-items",
    "test-design-review-invalid-status",
    "test-design-review-invalid-severity",
    "test-design-review-invalid-blocks-value",
    "test-design-review-failed",
    "artifact-write-strategy-forbidden-initial-method",
    "atomic-ledger-generic-atom-smell",
    "atomic-ledger-compressed-range-smell",
    "covered-atom-gsr-range-compression-smell",
    "atomic-ledger-combined-behavior-smell",
    "atomic-ledger-source-table-residue-smell",
    "test-case-package-design-plan-missing",
    "test-case-package-design-plan-empty",
    "test-case-package-design-plan-missing-columns",
    "test-case-package-design-plan-missing-package",
    "test-case-package-design-plan-missing-atoms",
    "test-case-package-design-plan-missing-tc-or-gap",
    "test-case-package-design-plan-unknown-test-case-id",
    "test-case-package-design-plan-generic-check-smell",
    "test-case-package-design-plan-generic-gap-row",
    "test-case-package-design-plan-missing-exact-length-boundary",
    "test-case-package-design-plan-missing-repeated-digits-check",
    "test-case-package-design-plan-merged-check-smell",
    "test-case-package-design-plan-merged-numeric-class-row",
    "design-plan-combined-class-smell",
    "test-case-package-design-plan-missing-conditional-branch",
    "test-case-package-design-plan-negative-without-positive-acceptance",
    "test-case-package-design-plan-many-rows-one-tc-smell",
    "scenario-plan-replaces-atomic-coverage-smell",
    "test-case-generic-title-smell",
    "test-case-generic-executable-smell",
    "test-case-value-type-list-selection-smell",
    "test-case-dependency-placeholder-setup-smell",
    "test-case-mockup-interaction-hints-not-used",
    "test-case-positive-type-with-negative-oracle",
    "test-case-negative-type-without-negative-oracle",
    "test-case-generic-valid-fixture-smell",
    "test-case-generic-test-data-reference-smell",
    "test-case-generic-expected-result-smell",
    "test-case-generic-test-data-oracle-smell",
    "test-case-generic-rule-oracle-smell",
    "test-case-source-dump-oracle-smell",
    "test-case-value-type-metadata-as-behavior-smell",
    "test-case-extraction-artifact-oracle-smell",
    "test-case-requiredness-without-empty-or-marker-check",
    "test-case-boundary-without-boundary-classes",
    "test-case-boundary-rejection-without-on-boundary-acceptance",
    "test-case-merged-valid-invalid-smell",
    "test-case-numeric-only-valid-data-invalid-smell",
    "test-case-valid-data-class-label-mismatch-smell",
    "test-case-numeric-class-label-raw-literal-smell",
    "test-case-unsupported-input-filtering-oracle-smell",
    "test-case-input-restriction-transition-oracle-smell",
    "test-case-unsupported-numeric-validation-feedback-smell",
    "test-case-mechanical-field-step-smell",
    "test-case-negative-transition-without-valid-fixture-smell",
    "test-case-forbidden-formulation-smell",
    "test-case-abstract-oracle-smell",
    "test-case-negative-input-without-observable-oracle",
    "test-case-date-dependent-absolute-date-smell",
    "test-case-action-treated-as-required-field-smell",
    "test-case-action-without-observable-artifact-smell",
    "test-case-gap-reference-missing-from-coverage-gaps",
    "test-case-gap-placeholder-section-smell",
    "test-case-nondeterministic-alternative-oracle-smell",
    "scenario-tc-replaces-atomic-coverage-smell",
    "test-case-excessive-atom-fan-in",
    "test-design-applicability-matrix-hidden-integration-gap",
    "test-design-applicability-matrix-hidden-numeric-equivalence-gap",
    "test-design-applicability-matrix-hidden-numeric-gap",
    "test-design-applicability-matrix-linked-tc-dimension-mismatch",
    "test-design-applicability-matrix-linked-atom-contamination",
    "source-normalization-dictionary-misclassified-smell",
    "test-case-file-no-structured-cases",
    "test-case-file-not-utf8",
    "test-case-noncanonical-heading-level",
    "split-artifact-not-utf8",
    "split-artifact-canonical-heading-missing",
    "split-artifact-redundant-section-heading",
    "test-case-duplicate-id",
    "test-case-mixed-schema-duplicate-fields",
    "test-case-runtime-field-duplicated",
    "test-case-missing-required-template-sections",
    "test-case-missing-package-id",
    "test-case-sparse-required-fields",
    "test-case-missing-numbered-steps",
    "test-case-missing-traceability-token",
    "writer-quality-gate-scoped-validator-profile-invalid",
}

ARTIFACT_WRITE_STRATEGY_MIN_TC_COUNT = 20
ARTIFACT_WRITE_STRATEGY_MIN_ATOM_COUNT = 30
ARTIFACT_WRITE_STRATEGY_MIN_CHARS = 20_000

ARTIFACT_WRITE_STRATEGY_SAFE_METHOD_RE = re.compile(
    r"("
    r"file[-\s]?based|chunked|"
    r"write_artifact_sections\.py|"
    r"update_markdown_section\.py|"
    r"--content-file|--stdin"
    r")",
    re.IGNORECASE,
)

ARTIFACT_WRITE_STRATEGY_PREFLIGHT_RE = re.compile(
    r"preflight|write\s+strategy|artifact\s+write|tc\s+count|atom\s+count|packages?|WP-\d{2}|"
    r"declared_before_first_write|forbidden_methods_checked|artifact_size_class",
    re.IGNORECASE,
)

ARTIFACT_WRITE_STRATEGY_TMP_GENERATOR_RE = re.compile(
    r"(?:^|[`'\s]|[\\/])tmp[\\/][^\n|`]*generate[^\n|`]*\.py|"
    r"(?:^|[`'\s]|[\\/])tmp[\\/][^\n|`]*generator",
    re.IGNORECASE,
)

ARTIFACT_WRITE_STRATEGY_METHOD_ITEM_RE = re.compile(
    r"write[_\s-]?method|selected[_\s-]?method|method|transport",
    re.IGNORECASE,
)

DICTIONARY_INVENTORY_NAME = "dictionary-inventory.md"
DICTIONARY_INVENTORY_EXTRACTED_STATUSES = {"extracted"}
DICTIONARY_INVENTORY_INCOMPLETE_STATUSES = {"partial", "missing", "ambiguous"}
DICTIONARY_INVENTORY_ALLOWED_STATUSES = (
    DICTIONARY_INVENTORY_EXTRACTED_STATUSES
    | DICTIONARY_INVENTORY_INCOMPLETE_STATUSES
    | {"not-needed"}
)

MOCKUP_VISUAL_INVENTORY_NAME = "mockup-visual-inventory.md"
NEGATIVE_ORACLE_INVENTORY_NAME = "negative-oracle-inventory.md"
REQUIREDNESS_ORACLE_INVENTORY_NAME = "requiredness-oracle-inventory.md"
ORACLE_INVENTORY_NAMES = {NEGATIVE_ORACLE_INVENTORY_NAME, REQUIREDNESS_ORACLE_INVENTORY_NAME}
ALLOWED_ORACLE_STATUSES = {
    "source-backed",
    "common-standard-backed",
    "analyst-confirmed",
    "ui-calibration-required",
    "observed-ui-backed",
    "not-testable-gap",
}
ALLOWED_ORACLE_INVENTORY_DECISIONS = {
    "executable_tc",
    "candidate_tc_required",
    "gap_required",
    "clarification_required",
    "not_applicable",
}
UI_CALIBRATION_REQUIRED_RE = re.compile(r"\bui-calibration-required\b", flags=re.IGNORECASE)
CANDIDATE_UI_CALIBRATION_RE = re.compile(
    r"\b(?:candidate-ui-calibration|requires-ui-calibration)\b",
    flags=re.IGNORECASE,
)
GAP_ONLY_INPUT_RESTRICTION_RE = re.compile(
    (
        r"\b(?:numeric|digits?|chars?|characters?|length|date|email|e-mail|mask|format|"
        r"phone|postal|index|text|symbol|letters?|invalid|non-numeric|future-date|"
        r"\u0446\u0438\u0444\u0440|\u0447\u0438\u0441\u043b|\u0441\u0438\u043c\u0432\u043e\u043b|\u043c\u0430\u0441\u043a|"
        r"\u0444\u043e\u0440\u043c\u0430\u0442|\u0434\u043b\u0438\u043d|\u0434\u0430\u0442|"
        r"\u0442\u0435\u043b\u0435\u0444\u043e\u043d|\u0438\u043d\u0434\u0435\u043a\u0441|\u043f\u043e\u0447\u0442)"
    ),
    flags=re.IGNORECASE,
)
GAP_ONLY_UI_CALIBRATION_ROUTE_RE = re.compile(
    (
        r"(?:positive\b.{0,120}\bonly|invalid\b.{0,120}\brequire.{0,80}ui calibration|"
        r"invalid\b.{0,120}\bdefer.{0,80}ui calibration|require.{0,80}explicit validation oracle|"
        r"\u043d\u0435\u0434\u043e\u043f\u0443\u0441\u0442.{0,120}ui calibration|"
        r"\u0442\u0440\u0435\u0431\u0443.{0,80}\u043a\u0430\u043b\u0438\u0431\u0440)"
    ),
    flags=re.IGNORECASE | re.DOTALL,
)
GAP_ONLY_CANDIDATE_LINK_RE = re.compile(
    r"\b(?:candidate_tc_required|candidate-ui-calibration|ui-calibration-required|SO-NEG-|SO-REQ-)\b",
    flags=re.IGNORECASE,
)
UI_CALIBRATION_NOTE_RE = re.compile(
    r"Требуется\s+подтверждение|"
    r"Что\s+нужно\s+зафиксировать\s+при\s+UI\s+calibration|"
    r"what\s+to\s+record\s+during\s+UI\s+calibration|"
    r"requires\s+confirmation|"
    r"calibration_notes?",
    flags=re.IGNORECASE,
)
UI_CALIBRATION_ALLOWED_EXPECTED_RE = re.compile(
    r"Конкретн\w+\s+(?:наблюдаем\w+\s+)?механизм\w*[^.\n]{0,120}"
    r"требу\w+\s+зафиксир\w+\s+при\s+UI\s+calibration",
    flags=re.IGNORECASE,
)
CONCRETE_UI_REACTION_WITHOUT_EVIDENCE_RE = re.compile(
    r"(?:сообщени[ея]|ошибк[аи]|message|error)\s*(?:[:=]|[\"«`])|"
    r"(?:красн\w+\s+подсвет|подсвечива\w+\s+красн|red\s+highlight)|"
    r"(?:кнопк[ауы]\s+[^.\n]{0,60}(?:disabled|недоступн|заблокирован))|"
    r"(?:точн\w+\s+текст|exact\s+(?:message|text))|"
    r"(?:значени[ея]\s+[^.\n]{0,80}(?:очища\w+|удаля\w+|не\s+сохраня\w+))",
    flags=re.IGNORECASE,
)
CANDIDATE_CONFIRMATION_FIELD_RE = re.compile(
    r"^\*\*(?:Требуется\s+подтверждение|Requires\s+confirmation):\*\*\s*(.+)$",
    flags=re.IGNORECASE | re.MULTILINE,
)
GENERIC_CONFIRMATION_QUESTION_RE = re.compile(
    r"^\s*(?:-|n/?a|none|уточнить|требуется\s+подтверждение|unknown|tbd)\.?\s*$",
    flags=re.IGNORECASE,
)
UI_CALIBRATION_NOTE_RE = re.compile(
    r"Требуется\s+подтверждение|"
    r"Что\s+нужно\s+зафиксировать\s+при\s+UI\s+calibration|"
    + UI_CALIBRATION_NOTE_RE.pattern,
    flags=re.IGNORECASE,
)
CANDIDATE_CONFIRMATION_FIELD_RE = re.compile(
    r"^\*\*(?:Требуется\s+подтверждение|"
    + CANDIDATE_CONFIRMATION_FIELD_RE.pattern.removeprefix(r"^\*\*(?:"),
    flags=re.IGNORECASE | re.MULTILINE,
)
GENERIC_CONFIRMATION_QUESTION_RE = re.compile(
    r"^\s*(?:-|n/?a|none|уточнить|требуется\s+подтверждение|unknown|tbd)\.?\s*$|"
    + GENERIC_CONFIRMATION_QUESTION_RE.pattern,
    flags=re.IGNORECASE,
)
CONCRETE_BACKTICK_VALUE_RE = re.compile(r"`([^`\n]{1,80})`")
GENERIC_INVALID_VALUE_TEXT_RE = re.compile(
    r"(?:invalid|невалидн\w*|недопустим\w*)\s+(?:value|значени[ея])",
    flags=re.IGNORECASE,
)
ENTER_CONCRETE_VALUE_RE = re.compile(
    r"(?:enter|type|input|ввести|указать|заполнить)[^.\n]{0,80}`([^`\n]{1,80})`",
    flags=re.IGNORECASE,
)
TEST_CASE_TITLE_PROCESS_MARKER_RE = re.compile(
    r"\bUI\s+calibration\b|\bcandidate\b|\boracle\b|\brequires\s+confirmation\b|"
    r"требу(?:ет|ется)\s+подтверждени[ея]",
    flags=re.IGNORECASE,
)

MOCKUP_VISUAL_INVENTORY_REQUIRED_TERMS = {
    "mockup_path",
    "opened",
    "method",
    "screen_name",
    "visible_blocks",
    "visible_fields",
    "visible_actions",
    "interaction_hints",
    "mockup_only_items",
    "ft_conflicts",
    "used_for_steps",
    "not_used_as_requirement_source",
}

MOCKUP_SOURCE_RE = re.compile(
    r"\bmockup\b|mockups?[\\/]|макет|макеты|\.(?:png|jpe?g|webp)\b",
    re.IGNORECASE,
)
NEGATIVE_ORACLE_SCOPE_RE = re.compile(
    r"\b(?:validation_domains|validation|numeric|digits?|date[-_ ]?time|email|e-mail|length|"
    r"allowed[-_ ]?values?|dictionary|reference[-_ ]?list|mask|invalid|negative)\b|"
    r"\b(?:(?:input|value|field)[-_ ]?format|format[-_ ]?(?:rule|restriction|validation|mask))\b|"
    r"(?:валидац|числов|цифр|e-mail|email|длин|маск|справочн|перечень|недопуст|"
    r"не\s+долж|только\s+\w+|формат.{0,40}(?:пол|знач|ввод|валид|маск)|"
    r"дат[аы].{0,40}(?:валид|формат|будущ|прошед|раньше|позже))",
    flags=re.IGNORECASE,
)
REQUIREDNESS_ORACLE_SCOPE_RE = re.compile(
    r"\b(?:requiredness|mandatory|required[-_ ]?(?:field|when|source|marker))\b|"
    r"(?:обязател|колонк[аи]\s+`?О`?|`О`\s*=|^|\s)О\s*(?:=|:|yes|да|\|)",
    flags=re.IGNORECASE,
)


def has_source_table_residue(value: str) -> bool:
    return any(pattern.search(value) for pattern in SOURCE_TABLE_RESIDUE_PATTERNS)


def has_combined_behavior_smell(value: str) -> bool:
    return any(pattern.search(value) for pattern in COMBINED_BEHAVIOR_SMELL_PATTERNS)


def source_normalization_property_classes(row: dict[str, str]) -> list[str]:
    inspected_text = " | ".join(
        row.get(field, "")
        for field in ("property", "expected_behavior")
        if row.get(field)
    )
    if not inspected_text:
        return []
    return sorted(
        class_name
        for class_name, pattern in SOURCE_NORMALIZATION_PROPERTY_CLASS_PATTERNS.items()
        if pattern.search(inspected_text)
    )


def real_gap_ids(value: str) -> list[str]:
    return [gap_id for gap_id in extract_gap_ids_from_text(value) if gap_id.upper() != "GAP-900"]


def should_require_writer_quality_gate(content: str) -> bool:
    return any(
        marker in content
        for marker in (
            "Package Test Design Plan",
            "Internal Work Package Coverage",
            "Source Table Normalization",
            "package_id",
        )
    )


def parsed_writer_quality_gate_rows(content: str) -> tuple[list[str], list[dict[str, str]]]:
    section = extract_markdown_section(content, "Writer Quality Gate")
    if section is None:
        return [], []

    rows = markdown_table_rows_from_text(section)
    if not rows:
        return [], []

    header = normalize_table_header(rows[0])
    parsed_rows: list[dict[str, str]] = []
    for row in rows[1:]:
        parsed_rows.append(
            {
                column_name: row[index].strip().strip("`") if index < len(row) else ""
                for index, column_name in enumerate(header)
            }
        )
    return header, parsed_rows


def writer_quality_gate_summary(content: str) -> dict[str, Any]:
    section = extract_markdown_section(content, "Writer Quality Gate")
    header, rows = parsed_writer_quality_gate_rows(content)
    missing_columns = sorted(WRITER_QUALITY_GATE_REQUIRED_COLUMNS - set(header))
    present_items = {
        row.get("gate_item", "").strip().strip("`")
        for row in rows
        if row.get("gate_item", "").strip()
    }
    missing_items = sorted(WRITER_QUALITY_GATE_REQUIRED_ITEMS - present_items)

    invalid_status_rows: list[str] = []
    invalid_blocks_rows: list[str] = []
    failed_rows: list[str] = []
    package_ready_pass = False
    for index, row in enumerate(rows, start=2):
        gate_item = row.get("gate_item", "").strip().strip("`") or f"row-{index}"
        status = row.get("status", "").strip().strip("`").lower()
        blocks = row.get("blocks_ready_for_review", "").strip().strip("`").lower()
        if gate_item == "package-ready" and status in WRITER_QUALITY_GATE_PASS_STATUSES:
            package_ready_pass = True
        if status and status not in WRITER_QUALITY_GATE_PASS_STATUSES | WRITER_QUALITY_GATE_FAIL_STATUSES:
            invalid_status_rows.append(f"{gate_item}:status={status}")
        if blocks and blocks not in WRITER_QUALITY_GATE_BLOCK_VALUES:
            invalid_blocks_rows.append(f"{gate_item}:blocks_ready_for_review={blocks}")
        if status in WRITER_QUALITY_GATE_FAIL_STATUSES:
            failed_rows.append(f"{gate_item}:status={status};blocks={blocks or '-'}")
        if blocks == "yes" and status not in WRITER_QUALITY_GATE_PASS_STATUSES:
            failed_rows.append(f"{gate_item}:status={status or '-'};blocks=yes")
        if blocks == "yes" and status in WRITER_QUALITY_GATE_PASS_STATUSES:
            failed_rows.append(f"{gate_item}:status={status};blocks=yes")
            invalid_blocks_rows.append(f"{gate_item}:status={status};blocks_ready_for_review=yes")

    failed_rows = sorted(set(failed_rows))
    package_ready_conflicts = failed_rows if package_ready_pass and failed_rows else []

    known_risk_not_blocking = False
    if rows and not failed_rows:
        known_risk_not_blocking = bool(
            re.search(
                r"possible\s+merged\s+checks\s*(?:=|:|\|)?\s*known\s+risk|"
                r"merged\s+checks[\s\S]{0,80}known\s+risk|"
                r"semantic\s+compression[\s\S]{0,80}known\s+risk",
                content,
                flags=re.IGNORECASE,
            )
        )

    return {
        "present": section is not None,
        "parseable": bool(header and rows),
        "missing_columns": missing_columns,
        "missing_items": missing_items,
        "invalid_status_rows": invalid_status_rows,
        "invalid_blocks_rows": invalid_blocks_rows,
        "failed_rows": failed_rows,
        "package_ready_conflicts": package_ready_conflicts,
        "known_risk_not_blocking": known_risk_not_blocking,
    }


def extract_json_artifact_paths(text: str) -> list[str]:
    paths: list[str] = []
    for match in re.finditer(r"`?([^`|\s]+\.json)`?", text):
        raw_path = match.group(1).strip().strip("`").rstrip(".,;")
        if raw_path and raw_path not in paths:
            paths.append(raw_path)
    return paths


def validate_scoped_validator_profile(
    profile_path: Path,
    *,
    display_source_path: str,
) -> tuple[list[str], list[str]]:
    issues: list[str] = []
    evidence: list[str] = []
    try:
        payload = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"{display_source_path}:profile-not-readable:{profile_path.name}:{type(exc).__name__}"], evidence

    if not isinstance(payload, dict):
        return [f"{display_source_path}:profile-not-object:{profile_path.name}"], evidence

    missing_keys = sorted(SCOPED_VALIDATOR_PROFILE_REQUIRED_KEYS - set(payload))
    if missing_keys:
        issues.append(f"{display_source_path}:profile-missing-keys:{profile_path.name}:{', '.join(missing_keys)}")

    generated_by = str(payload.get("generated_by") or "").strip()
    if generated_by != "codex_review_cycle_runner":
        issues.append(
            f"{display_source_path}:profile-not-runner-generated:{profile_path.name}:generated_by={generated_by or '-'}"
        )

    findings = payload.get("current_scope_findings")
    if not isinstance(findings, list):
        issues.append(f"{display_source_path}:current_scope_findings-not-list:{profile_path.name}")
    else:
        unresolved_from_rows = []
        for index, finding in enumerate(findings, start=1):
            if not isinstance(finding, dict):
                continue
            severity = str(finding.get("severity") or "").strip().lower()
            status = str(finding.get("status") or "").strip().lower()
            if severity in {"warning", "error"} and status not in {"fixed", "waived", "false-positive", "accepted-nonblocking"}:
                unresolved_from_rows.append(
                    f"row-{index}:{finding.get('id', '<missing-id>')}:{severity}:status={status or '-'}"
                )
        if unresolved_from_rows:
            issues.append(
                f"{display_source_path}:profile-has-unresolved-current-scope-findings:{'; '.join(unresolved_from_rows[:8])}"
            )

    unresolved_count_raw = payload.get("unresolved_warning_error_count")
    try:
        unresolved_count = int(unresolved_count_raw)
    except (TypeError, ValueError):
        issues.append(f"{display_source_path}:unresolved_warning_error_count-not-integer:{unresolved_count_raw!r}")
        unresolved_count = 0
    if unresolved_count > 0:
        issues.append(f"{display_source_path}:unresolved_warning_error_count={unresolved_count}")

    command = str(payload.get("command") or "").strip()
    normalized_command = command.strip("`").lower()
    if (
        normalized_command in SCOPED_VALIDATOR_PROFILE_PLACEHOLDER_COMMANDS
        or (normalized_command.startswith("<") and normalized_command.endswith(">"))
    ):
        issues.append(f"{display_source_path}:profile-command-placeholder:{profile_path.name}:{command or '-'}")
    evidence.append(f"{profile_path.as_posix()}:command={command or '-'}")
    evidence.append(f"{profile_path.as_posix()}:unresolved_warning_error_count={unresolved_count_raw!r}")
    return issues, evidence


def validate_writer_quality_gate_scoped_validator_profile(
    content: str,
    path: Path,
    root: Path,
) -> tuple[list[str], list[str]]:
    display_path = rel(path, root)
    _, rows = parsed_writer_quality_gate_rows(content)
    issues: list[str] = []
    evidence: list[str] = []
    validation_root = root.parent if root.is_file() else root
    for index, row in enumerate(rows, start=2):
        gate_item = row.get("gate_item", "").strip().strip("`")
        status = row.get("status", "").strip().strip("`").lower()
        if gate_item != "scoped-validator-findings" or status != "pass":
            continue
        profile_refs = extract_json_artifact_paths(row.get("evidence", ""))
        if not profile_refs:
            issues.append(f"{display_path}:row-{index}:missing scoped validator JSON profile path")
            continue
        forbidden_stage_refs = [
            profile_ref
            for profile_ref in profile_refs
            if WRITER_GATE_FORBIDDEN_SCOPED_PROFILE_STAGE_RE.search(Path(profile_ref).name)
        ]
        if forbidden_stage_refs:
            issues.append(
                f"{display_path}:row-{index}:writer gate references reviewer/future scoped validator profile: "
                f"{', '.join(forbidden_stage_refs[:4])}"
            )
        resolved_profiles: list[Path] = []
        for profile_ref in profile_refs:
            resolved = resolve_artifact_path(profile_ref, path, root, validation_root)
            if resolved is not None:
                resolved_profiles.append(resolved)
        if not resolved_profiles:
            issues.append(
                f"{display_path}:row-{index}:profile path not found: {', '.join(profile_refs[:4])}"
            )
            continue
        for profile_path in resolved_profiles:
            profile_issues, profile_evidence = validate_scoped_validator_profile(
                profile_path,
                display_source_path=f"{display_path}:row-{index}",
            )
            issues.extend(profile_issues)
            evidence.extend(profile_evidence)
    return issues, evidence


def should_require_test_design_review(content: str) -> bool:
    return extract_markdown_section(content, "Package Test Design Plan") is not None


def parsed_test_design_review_rows(content: str) -> tuple[list[str], list[dict[str, str]]]:
    section = extract_markdown_section(content, "Test Design Review")
    if section is None:
        return [], []

    rows = markdown_table_rows_from_text(section)
    if not rows:
        return [], []

    header = normalize_table_header(rows[0])
    parsed_rows: list[dict[str, str]] = []
    for row in rows[1:]:
        parsed_rows.append(
            {
                column_name: row[index].strip().strip("`") if index < len(row) else ""
                for index, column_name in enumerate(header)
            }
        )
    return header, parsed_rows


def test_design_review_summary(content: str) -> dict[str, Any]:
    section = extract_markdown_section(content, "Test Design Review")
    header, rows = parsed_test_design_review_rows(content)
    missing_columns = sorted(TEST_DESIGN_REVIEW_REQUIRED_COLUMNS - set(header))
    present_items = {
        row.get("review_item", "").strip().strip("`")
        for row in rows
        if row.get("review_item", "").strip()
    }
    missing_items = sorted(TEST_DESIGN_REVIEW_REQUIRED_ITEMS - present_items)
    unknown_items = sorted(present_items - TEST_DESIGN_REVIEW_REQUIRED_ITEMS)

    invalid_status_rows: list[str] = []
    invalid_severity_rows: list[str] = []
    invalid_blocks_rows: list[str] = []
    failed_rows: list[str] = []
    for index, row in enumerate(rows, start=2):
        review_item = row.get("review_item", "").strip().strip("`") or f"row-{index}"
        status = row.get("status", "").strip().strip("`").lower()
        severity = row.get("severity", "").strip().strip("`").lower()
        blocks = row.get("blocks_ready_for_review", "").strip().strip("`").lower()
        if status and status not in TEST_DESIGN_REVIEW_PASS_STATUSES | TEST_DESIGN_REVIEW_FAIL_STATUSES:
            invalid_status_rows.append(f"{review_item}:status={status}")
        if severity and severity not in TEST_DESIGN_REVIEW_SEVERITIES:
            invalid_severity_rows.append(f"{review_item}:severity={severity}")
        if blocks and blocks not in TEST_DESIGN_REVIEW_BLOCK_VALUES:
            invalid_blocks_rows.append(f"{review_item}:blocks_ready_for_review={blocks}")
        if status in TEST_DESIGN_REVIEW_FAIL_STATUSES:
            failed_rows.append(f"{review_item}:status={status};blocks={blocks or '-'}")
        if blocks == "yes" and status not in TEST_DESIGN_REVIEW_PASS_STATUSES:
            failed_rows.append(f"{review_item}:status={status or '-'};blocks=yes")
        if blocks == "yes" and status in TEST_DESIGN_REVIEW_PASS_STATUSES:
            invalid_blocks_rows.append(f"{review_item}:status={status};blocks_ready_for_review=yes")

    return {
        "required": should_require_test_design_review(content),
        "present": section is not None,
        "parseable": bool(header and rows),
        "missing_columns": missing_columns,
        "missing_items": missing_items,
        "unknown_items": unknown_items,
        "invalid_status_rows": invalid_status_rows,
        "invalid_severity_rows": invalid_severity_rows,
        "invalid_blocks_rows": invalid_blocks_rows,
        "failed_rows": sorted(set(failed_rows)),
    }


def parsed_section_table_rows(content: str, section_title: str) -> tuple[list[str], list[dict[str, str]]]:
    section = extract_markdown_section(content, section_title)
    if section is None:
        return [], []
    rows = markdown_table_rows_from_text(section)
    if not rows:
        return [], []
    header = normalize_table_header(rows[0])
    parsed_rows: list[dict[str, str]] = []
    for row in rows[1:]:
        parsed_rows.append(
            {
                column_name: row[index].strip().strip("`") if index < len(row) else ""
                for index, column_name in enumerate(header)
            }
        )
    return header, parsed_rows


def test_case_type_from_block(block: str) -> str:
    return normalize_markdown_field_value(
        extract_test_case_field_block(block, ["type", "Type", "Тип"])
    ).strip("`").lower()


def test_case_is_traceability_remap(block: str) -> bool:
    return test_case_type_from_block(block) in TRACEABILITY_REMAP_TEST_CASE_TYPES


def test_case_has_remap_language(block: str) -> bool:
    return bool(TRACEABILITY_REMAP_TEXT_RE.search(block))


def validate_test_design_decision_table(
    content: str,
    path: Path,
    root: Path,
    *,
    known_test_case_ids: set[str] | None = None,
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    normalization_header, normalization_rows = parsed_section_table_rows(content, "Source Table Normalization")
    source_property_ids = [
        row.get("source_property_id", "").strip()
        for row in normalization_rows
        if row.get("source_property_id", "").strip() not in {"", "-"}
    ]
    is_required = bool(source_property_ids) and (
        extract_markdown_section(content, "Package Test Design Plan") is not None
        or extract_markdown_section(content, "Atomic Requirements Ledger") is not None
        or bool(extract_test_case_blocks(content))
    )
    section = extract_markdown_section(content, "Test Design Decision Table")

    if not is_required and section is None:
        checks.append(
            Check(
                "test-design-decision-table",
                "pass",
                "Test Design Decision Table is not required for this artifact.",
                display_path,
            )
        )
        return findings, checks

    if section is None:
        findings.append(
            Finding(
                id="test-design-decision-table-missing",
                severity="warning",
                category="test-design",
                title="Test Design Decision Table is missing",
                details=(
                    "A table/extraction writer output with Source Table Normalization must decide whether each "
                    "normalized source property becomes a standalone TC, is covered by another TC, remains GAP/unclear, "
                    "is metadata-only, scenario-only, or out of scope before creating ledger and TC-*."
                ),
                path=display_path,
                evidence=[f"normalized_source_properties={len(set(source_property_ids))}"],
                recommended_action=(
                    "Add `## Test Design Decision Table` after Source Table Normalization and before Atomic "
                    "Requirements Ledger. Do not mechanically create TC-* for metadata-only source properties."
                ),
            )
        )
        checks.append(Check("test-design-decision-table", "warn", "Test Design Decision Table is missing.", display_path))
        return findings, checks

    header, rows = parsed_section_table_rows(content, "Test Design Decision Table")
    if not rows:
        findings.append(
            Finding(
                id="test-design-decision-table-no-table",
                severity="warning",
                category="test-design",
                title="Test Design Decision Table has no parseable table",
                details="The section exists but has no Markdown table rows.",
                path=display_path,
                evidence=[],
                recommended_action="Use the canonical Test Design Decision Table columns from test-design-decision-table-format.md.",
            )
        )
        checks.append(Check("test-design-decision-table", "warn", "Test Design Decision Table table is missing.", display_path))
        return findings, checks

    missing_columns = sorted(TEST_DESIGN_DECISION_TABLE_REQUIRED_COLUMNS - set(header))
    if missing_columns:
        findings.append(
            Finding(
                id="test-design-decision-table-missing-columns",
                severity="warning",
                category="test-design",
                title="Test Design Decision Table misses required columns",
                details="The decision table must expose source property identity, design decision, planned TC/GAP, oracle source and execution decision.",
                path=display_path,
                evidence=[f"missing={', '.join(missing_columns)}", f"columns={', '.join(header[:14])}"],
                recommended_action="Rewrite the table with the canonical columns from test-design-decision-table-format.md.",
            )
        )

    decision_source_ids: list[str] = []
    invalid_decisions: list[str] = []
    metadata_links_tc: list[str] = []
    gap_without_gap: list[str] = []
    standalone_without_tc_or_oracle: list[str] = []
    covered_without_tc: list[str] = []
    scenario_without_tc: list[str] = []
    out_of_scope_without_reason: list[str] = []
    value_type_standalone: list[str] = []
    unknown_test_case_ids: list[str] = []
    metadata_cross_section_conflicts: list[str] = []
    gap_cross_section_conflicts: list[str] = []
    scenario_remap_executable_conflicts: list[str] = []
    executable_cross_section_conflicts: list[str] = []
    gap_executable_behavior_smells: list[str] = []
    gap_overbroad_smells: list[str] = []
    metadata_behavior_smells: list[str] = []
    date_window_gap_smells: list[str] = []
    merged_numeric_class_decisions: list[str] = []
    artificial_numeric_type_decisions: list[str] = []
    missing_ledger_gap_decisions: list[str] = []

    _, ledger_rows = parsed_atomic_requirement_ledger_rows(content)
    ledger_rows_by_atom: dict[str, list[dict[str, str]]] = defaultdict(list)
    for ledger_row in ledger_rows:
        atom_id = ledger_row.get("atom_id", "").strip().strip("`")
        if atom_id:
            ledger_rows_by_atom[atom_id].append(ledger_row)

    normalization_rows_by_property_id = {
        row.get("source_property_id", "").strip(): row
        for row in normalization_rows
        if row.get("source_property_id", "").strip()
    }

    _, plan_rows = parsed_section_table_rows(content, "Package Test Design Plan")
    plan_rows_by_atom: dict[str, list[dict[str, str]]] = defaultdict(list)
    for plan_row in plan_rows:
        for atom_id in extract_any_atom_ids_from_text(plan_row.get("linked_atoms", "")):
            plan_rows_by_atom[atom_id].append(plan_row)

    _, risk_rows = parsed_section_table_rows(content, "Risk / Priority Map")
    risk_rows_by_atom: dict[str, list[dict[str, str]]] = defaultdict(list)
    for risk_row in risk_rows:
        atom_id = risk_row.get("atom_id", "").strip().strip("`")
        if atom_id:
            risk_rows_by_atom[atom_id].append(risk_row)

    test_case_blocks_by_id = {test_case_id: block for test_case_id, block in extract_test_case_blocks(content)}
    test_case_blocks_by_atom: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for test_case_id, block in test_case_blocks_by_id.items():
        for atom_id in extract_any_atom_ids_from_text(block):
            test_case_blocks_by_atom[atom_id].append((test_case_id, block))

    executable_tddt_test_case_ids_by_atom: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        decision = row.get("decision", "").strip().strip("`").lower()
        if decision not in {"standalone_tc", "covered_by_existing_tc"}:
            continue
        test_case_ids = extract_test_case_ids_from_text(row.get("planned_tc_or_gap", ""))
        for atom_id in extract_any_atom_ids_from_text(row.get("linked_atom_id", "")):
            executable_tddt_test_case_ids_by_atom[atom_id].update(test_case_ids)

    for index, row in enumerate(rows, start=2):
        source_property_id = row.get("source_property_id", "").strip()
        decision_id = row.get("decision_id", "").strip() or f"row {index}"
        decision = row.get("decision", "").strip().strip("`").lower()
        property_type = row.get("property_type", "").strip().strip("`").lower()
        decision_reason = row.get("decision_reason", "").strip()
        planned = row.get("planned_tc_or_gap", "").strip()
        oracle_source = row.get("oracle_source", "").strip()
        row_label = f"{decision_id}:{source_property_id or '<missing source_property_id>'}"

        if source_property_id and source_property_id != "-":
            decision_source_ids.append(source_property_id)
        if property_type in ARTIFICIAL_NUMERIC_PROPERTY_TYPES:
            artificial_numeric_type_decisions.append(f"{row_label}:property_type={property_type}")

        test_case_ids = extract_test_case_ids_from_text(planned)
        gap_ids = extract_gap_ids_from_text(planned)
        linked_atom_ids = extract_any_atom_ids_from_text(row.get("linked_atom_id", ""))
        if known_test_case_ids:
            for test_case_id in test_case_ids:
                if test_case_id not in known_test_case_ids:
                    unknown_test_case_ids.append(f"{row_label}:{test_case_id}")

        if decision not in ALLOWED_TEST_DESIGN_DECISIONS:
            invalid_decisions.append(f"{row_label}:decision={decision or '<missing>'}")
            continue

        if (
            decision in {"standalone_tc", "covered_by_existing_tc"}
            and property_type != "text-symbol-restriction"
            and row_has_numeric_format_context(
                row,
                (
                    "property_type",
                    "decision_reason",
                    "oracle_source",
                    "observable_oracle",
                    "testable_part",
                ),
            )
            and row_has_merged_numeric_invalid_classes(
                row,
                (
                    "property_type",
                    "decision_reason",
                    "oracle_source",
                    "observable_oracle",
                    "testable_part",
                    "planned_tc_or_gap",
                ),
            )
        ):
            merged_numeric_class_decisions.append(
                f"{row_label}:planned_tc_or_gap={planned or '-'};"
                f"testable_part={row.get('testable_part', '-') or row.get('decision_reason', '-') or '-'}"
            )

        normalization_row = normalization_rows_by_property_id.get(source_property_id, {})
        normalization_context = " | ".join(
            value
            for value in (
                normalization_row.get("field_or_block", ""),
                normalization_row.get("property", ""),
                normalization_row.get("condition", ""),
                normalization_row.get("expected_behavior", ""),
                normalization_row.get("source_ref", ""),
                normalization_row.get("source_text_fragment", ""),
            )
            if value
        )
        row_context = " | ".join(
            value
            for value in (
                property_type,
                decision_reason,
                oracle_source,
                row.get("observable_oracle", ""),
                row.get("testable_part", ""),
                row.get("blocked_part", ""),
                row.get("gap_admissibility", ""),
                normalization_context,
            )
            if value
        )
        has_visible_result = bool(GAP_ADMISSIBILITY_VISIBLE_RESULT_RE.search(row_context))
        has_executable_property = bool(GAP_ADMISSIBILITY_EXECUTABLE_PROPERTY_RE.search(property_type))
        has_blocker_evidence = bool(
            GAP_ADMISSIBILITY_BLOCKER_RE.search(
                " | ".join(
                    value
                    for value in (
                        decision_reason,
                        oracle_source,
                        row.get("blocked_part", ""),
                        row.get("gap_admissibility", ""),
                    )
                    if value
                )
            )
        )
        has_testable_part = meaningful_matrix_value(row.get("testable_part", ""))
        is_internal_only_gap = (
            bool(INTEGRATION_OR_INTERNAL_PROPERTY_RE.search(row_context))
            and not has_visible_result
            and not has_executable_property
            and not has_testable_part
        )
        has_passport_window = bool(PASSPORT_VALIDITY_WINDOW_RE.search(row_context))

        if decision == "metadata_only" and (has_visible_result or has_executable_property or has_testable_part):
            metadata_behavior_smells.append(
                f"{row_label}:property_type={property_type or '-'};source={normalization_context[:160] or '-'}"
            )
        if decision == "gap_unclear" and not is_internal_only_gap:
            if has_executable_property or has_testable_part or (has_visible_result and not has_blocker_evidence):
                gap_executable_behavior_smells.append(
                    f"{row_label}:property_type={property_type or '-'};source={normalization_context[:160] or '-'}"
                )
            if has_passport_window:
                date_window_gap_smells.append(
                    f"{row_label}:property_type={property_type or '-'};source={normalization_context[:160] or '-'}"
                )
            if has_blocker_evidence and (has_executable_property or has_testable_part):
                gap_overbroad_smells.append(
                    f"{row_label}:blocker={decision_reason[:120] or oracle_source[:120] or '-'};source={normalization_context[:160] or '-'}"
                )

        if decision == "metadata_only" and test_case_ids:
            metadata_links_tc.append(f"{row_label}:planned_tc_or_gap={planned}")
        if decision == "metadata_only":
            for atom_id in linked_atom_ids:
                for ledger_row in ledger_rows_by_atom.get(atom_id, []):
                    ledger_status = ledger_row.get("coverage_status", "").strip().strip("`").lower()
                    ledger_tc_ids = extract_test_case_ids_from_text(ledger_row.get("covered_by_tc", ""))
                    if ledger_status == "covered" or ledger_tc_ids:
                        metadata_cross_section_conflicts.append(
                            f"{row_label}:{atom_id}:ledger coverage_status={ledger_status or '-'};covered_by_tc={ledger_row.get('covered_by_tc', '-') or '-'}"
                        )
                for plan_row in plan_rows_by_atom.get(atom_id, []):
                    plan_tc_ids = extract_test_case_ids_from_text(plan_row.get("planned_tc_or_gap", ""))
                    if plan_tc_ids:
                        metadata_cross_section_conflicts.append(
                            f"{row_label}:{atom_id}:plan {plan_row.get('design_item_id', '<row>')}:planned_tc_or_gap={plan_row.get('planned_tc_or_gap', '-') or '-'}"
                        )
                for risk_row in risk_rows_by_atom.get(atom_id, []):
                    risk_tc_ids = extract_test_case_ids_from_text(risk_row.get("linked_test_cases", ""))
                    if risk_tc_ids:
                        metadata_cross_section_conflicts.append(
                            f"{row_label}:{atom_id}:risk linked_test_cases={risk_row.get('linked_test_cases', '-') or '-'}"
                        )
                for test_case_id, block in test_case_blocks_by_atom.get(atom_id, []):
                    if not test_case_is_traceability_remap(block):
                        metadata_cross_section_conflicts.append(
                            f"{row_label}:{atom_id}:{test_case_id}:type={test_case_type_from_block(block) or '-'}"
                        )
        if decision == "gap_unclear" and not gap_ids:
            gap_without_gap.append(f"{row_label}:planned_tc_or_gap={planned or '-'}")
        if decision == "gap_unclear":
            expected_gap_ids = set(gap_ids)
            for atom_id in linked_atom_ids:
                for ledger_row in ledger_rows_by_atom.get(atom_id, []):
                    ledger_status = ledger_row.get("coverage_status", "").strip().strip("`").lower()
                    ledger_text = " | ".join(ledger_row.values())
                    ledger_tc_ids = extract_test_case_ids_from_text(ledger_row.get("covered_by_tc", ""))
                    ledger_gap_ids = set(extract_gap_ids_from_text(ledger_text))
                    if ledger_status == "covered" or ledger_tc_ids:
                        gap_cross_section_conflicts.append(
                            f"{row_label}:{atom_id}:ledger coverage_status={ledger_status or '-'};covered_by_tc={ledger_row.get('covered_by_tc', '-') or '-'}"
                        )
                    elif expected_gap_ids and not expected_gap_ids.intersection(ledger_gap_ids):
                        gap_cross_section_conflicts.append(
                            f"{row_label}:{atom_id}:ledger missing expected gap {', '.join(sorted(expected_gap_ids))}"
                        )
                for plan_row in plan_rows_by_atom.get(atom_id, []):
                    plan_text = " | ".join(plan_row.values())
                    plan_tc_ids = extract_test_case_ids_from_text(plan_row.get("planned_tc_or_gap", ""))
                    plan_gap_ids = set(extract_gap_ids_from_text(plan_text))
                    if plan_tc_ids:
                        gap_cross_section_conflicts.append(
                            f"{row_label}:{atom_id}:plan {plan_row.get('design_item_id', '<row>')}:planned_tc_or_gap={plan_row.get('planned_tc_or_gap', '-') or '-'}"
                        )
                    elif expected_gap_ids and not expected_gap_ids.intersection(plan_gap_ids):
                        gap_cross_section_conflicts.append(
                            f"{row_label}:{atom_id}:plan {plan_row.get('design_item_id', '<row>')} missing expected gap {', '.join(sorted(expected_gap_ids))}"
                        )
                for risk_row in risk_rows_by_atom.get(atom_id, []):
                    risk_tc_ids = extract_test_case_ids_from_text(risk_row.get("linked_test_cases", ""))
                    risk_gap_ids = set(extract_gap_ids_from_text(" | ".join(risk_row.values())))
                    if risk_tc_ids:
                        gap_cross_section_conflicts.append(
                            f"{row_label}:{atom_id}:risk linked_test_cases={risk_row.get('linked_test_cases', '-') or '-'}"
                        )
                    elif expected_gap_ids and not expected_gap_ids.intersection(risk_gap_ids):
                        gap_cross_section_conflicts.append(
                            f"{row_label}:{atom_id}:risk missing expected gap {', '.join(sorted(expected_gap_ids))}"
                        )
        if decision == "standalone_tc" and (not test_case_ids or not meaningful_matrix_value(oracle_source)):
            standalone_without_tc_or_oracle.append(
                f"{row_label}:planned_tc_or_gap={planned or '-'};oracle_source={oracle_source or '-'}"
            )
        if decision == "covered_by_existing_tc" and not test_case_ids:
            covered_without_tc.append(f"{row_label}:planned_tc_or_gap={planned or '-'}")
        if decision == "scenario_only" and not test_case_ids:
            scenario_without_tc.append(f"{row_label}:planned_tc_or_gap={planned or '-'}")
        if decision == "scenario_only":
            for test_case_id in test_case_ids:
                block = test_case_blocks_by_id.get(test_case_id)
                if block and test_case_has_remap_language(block) and not test_case_is_traceability_remap(block):
                    scenario_remap_executable_conflicts.append(
                        f"{row_label}:{test_case_id}:type={test_case_type_from_block(block) or '-'}"
                    )
        if decision in {"standalone_tc", "covered_by_existing_tc"}:
            row_test_case_ids = set(test_case_ids)
            for atom_id in linked_atom_ids:
                ledger_test_case_ids: set[str] = set()
                ledger_statuses: set[str] = set()
                for ledger_row in ledger_rows_by_atom.get(atom_id, []):
                    ledger_status = ledger_row.get("coverage_status", "").strip().strip("`").lower()
                    ledger_statuses.add(ledger_status or "-")
                    ledger_test_case_ids.update(extract_test_case_ids_from_text(ledger_row.get("covered_by_tc", "")))
                if ledger_rows_by_atom.get(atom_id):
                    if not ledger_test_case_ids:
                        executable_cross_section_conflicts.append(
                            f"{row_label}:{atom_id}:ledger has no covered_by_tc for executable decision"
                        )
                    if ledger_statuses and ledger_statuses != {"covered"}:
                        executable_cross_section_conflicts.append(
                            f"{row_label}:{atom_id}:ledger coverage_status={', '.join(sorted(ledger_statuses))}"
                        )
                    extra_test_case_ids = sorted(row_test_case_ids - ledger_test_case_ids)
                    missing_test_case_ids = sorted(ledger_test_case_ids - row_test_case_ids)
                    if extra_test_case_ids:
                        executable_cross_section_conflicts.append(
                            f"{row_label}:{atom_id}:planned_tc_or_gap has TC not in ledger covered_by_tc: {', '.join(extra_test_case_ids)}"
                        )
                    group_missing_test_case_ids = sorted(
                        ledger_test_case_ids - executable_tddt_test_case_ids_by_atom.get(atom_id, set())
                    )
                    if group_missing_test_case_ids:
                        executable_cross_section_conflicts.append(
                            f"{row_label}:{atom_id}:ledger covered_by_tc missing from executable TDDT rows: {', '.join(group_missing_test_case_ids)}"
                        )

                plan_test_case_ids: set[str] = set()
                for plan_row in plan_rows_by_atom.get(atom_id, []):
                    plan_test_case_ids.update(extract_test_case_ids_from_text(plan_row.get("planned_tc_or_gap", "")))
                if plan_test_case_ids:
                    extra_test_case_ids = sorted(row_test_case_ids - plan_test_case_ids)
                    missing_test_case_ids = sorted(plan_test_case_ids - row_test_case_ids)
                    if extra_test_case_ids:
                        executable_cross_section_conflicts.append(
                            f"{row_label}:{atom_id}:planned_tc_or_gap has TC not in Package Test Design Plan: {', '.join(extra_test_case_ids)}"
                        )
                    group_missing_test_case_ids = sorted(
                        plan_test_case_ids - executable_tddt_test_case_ids_by_atom.get(atom_id, set())
                    )
                    if group_missing_test_case_ids:
                        executable_cross_section_conflicts.append(
                            f"{row_label}:{atom_id}:Package Test Design Plan TC missing from executable TDDT rows: {', '.join(group_missing_test_case_ids)}"
                        )

                block_test_case_ids = {test_case_id for test_case_id, _ in test_case_blocks_by_atom.get(atom_id, [])}
                if block_test_case_ids:
                    extra_test_case_ids = sorted(row_test_case_ids - block_test_case_ids)
                    missing_test_case_ids = sorted(block_test_case_ids - row_test_case_ids)
                    if extra_test_case_ids:
                        executable_cross_section_conflicts.append(
                            f"{row_label}:{atom_id}:planned_tc_or_gap references TC without this atom: {', '.join(extra_test_case_ids)}"
                        )
                    group_missing_test_case_ids = sorted(
                        block_test_case_ids - executable_tddt_test_case_ids_by_atom.get(atom_id, set())
                    )
                    if group_missing_test_case_ids:
                        executable_cross_section_conflicts.append(
                            f"{row_label}:{atom_id}:TC sections with atom missing from executable TDDT rows: {', '.join(group_missing_test_case_ids)}"
                        )
        if decision == "out_of_scope" and not (meaningful_matrix_value(decision_reason) or meaningful_matrix_value(oracle_source)):
            out_of_scope_without_reason.append(f"{row_label}:decision_reason={decision_reason or '-'}")

        value_type_text = " | ".join(
            value
            for value in (
                property_type,
                decision_reason.lower(),
                oracle_source.lower(),
            )
            if value
        )
        if decision == "standalone_tc" and re.search(r"value[-_\s]?type|тип\s+значения|metadata[-_\s]?only|тип\s+контрола", value_type_text):
            if not re.search(
                r"format|input|widget|control|numeric|date|phone|email|length|"
                r"формат|ввод|контрол|числ|дат|телефон|почт|длин",
                value_type_text,
                flags=re.IGNORECASE,
            ):
                value_type_standalone.append(f"{row_label}:property_type={property_type or '-'};oracle_source={oracle_source or '-'}")

    for ledger_row in ledger_rows_with_real_gap_ids(content):
        atom_id = ledger_row.get("atom_id", "").strip().strip("`")
        source_property_id = ledger_row.get("source_property_id", "").strip().strip("`")
        ledger_gap_ids = set(real_gap_ids(" | ".join(ledger_row.values())))
        represented = False
        for row in rows:
            decision = row.get("decision", "").strip().strip("`").lower()
            row_source_property_id = row.get("source_property_id", "").strip().strip("`")
            linked_atom_ids = set(extract_any_atom_ids_from_text(row.get("linked_atom_id", "")))
            row_gap_ids = set(real_gap_ids(" | ".join(row.values())))
            matches_atom = bool(atom_id and atom_id in linked_atom_ids)
            matches_gap = bool(ledger_gap_ids and ledger_gap_ids.intersection(row_gap_ids))
            matches_source_property = (
                not source_property_id
                or not row_source_property_id
                or row_source_property_id == source_property_id
            )
            if (matches_atom and decision == "gap_unclear") or (matches_gap and matches_source_property):
                represented = True
                break
        if not represented:
            missing_ledger_gap_decisions.append(
                f"{atom_id or '<missing atom>'}:source_property_id={source_property_id or '-'};"
                f"gap_id={', '.join(sorted(ledger_gap_ids)) or '-'}"
            )

    source_id_counts = Counter(decision_source_ids)
    duplicate_source_ids = [source_id for source_id, count in source_id_counts.items() if count > 1]
    missing_source_ids = sorted(set(source_property_ids) - set(decision_source_ids))

    if missing_source_ids:
        findings.append(
            Finding(
                id="test-design-decision-table-missing-source-property",
                severity="warning",
                category="traceability",
                title="Test Design Decision Table misses normalized source properties",
                details="Every source_property_id from Source Table Normalization must have exactly one design decision before ledger and TC writing.",
                path=display_path,
                evidence=missing_source_ids[:20],
                recommended_action="Add one decision row for each missing source_property_id.",
            )
        )
    if duplicate_source_ids:
        findings.append(
            Finding(
                id="test-design-decision-table-duplicate-source-property",
                severity="warning",
                category="traceability",
                title="Test Design Decision Table has duplicate source property decisions",
                details="A normalized source property should have one design decision, not competing rows.",
                path=display_path,
                evidence=duplicate_source_ids[:20],
                recommended_action="Keep exactly one decision row per source_property_id.",
            )
        )
    if invalid_decisions:
        findings.append(
            Finding(
                id="test-design-decision-table-invalid-decision",
                severity="warning",
                category="test-design",
                title="Test Design Decision Table uses invalid decision values",
                details="Decision must be one of standalone_tc, covered_by_existing_tc, gap_unclear, metadata_only, scenario_only or out_of_scope.",
                path=display_path,
                evidence=invalid_decisions[:20],
                recommended_action="Normalize decision values to the canonical vocabulary.",
            )
        )
    if metadata_links_tc:
        findings.append(
            Finding(
                id="test-design-decision-table-metadata-links-tc",
                severity="warning",
                category="test-design",
                title="Metadata-only source properties are linked to TC-*",
                details="Metadata-only rows such as value type must not create pseudo test cases. They should be covered through concrete behavior, GAP/unclear, or traceability only.",
                path=display_path,
                evidence=metadata_links_tc[:20],
                recommended_action="Remove TC-* links from metadata_only rows or change the decision to a concrete source-backed executable behavior.",
            )
        )
    if metadata_cross_section_conflicts:
        findings.append(
            Finding(
                id="test-design-decision-table-metadata-cross-section-conflict",
                severity="warning",
                category="test-design",
                title="Metadata-only decisions conflict with executable coverage in other sections",
                details=(
                    "A metadata_only TDDT decision is not enough if the same atom is still marked covered in the "
                    "ledger, planned as an executable TC in Package Test Design Plan, linked from Risk / Priority Map, "
                    "or present in non-remap TC sections."
                ),
                path=display_path,
                evidence=metadata_cross_section_conflicts[:20],
                recommended_action=(
                    "Synchronize TDDT, Atomic Requirements Ledger, Package Test Design Plan, Risk / Priority Map and TC sections: "
                    "metadata-only atoms must route to GAP/unclear or traceability-remap, not executable coverage."
                ),
            )
        )
    if gap_without_gap:
        findings.append(
            Finding(
                id="test-design-decision-table-gap-without-gap-id",
                severity="warning",
                category="traceability",
                title="Gap/unclear decisions have no GAP-* link",
                details="A gap_unclear decision needs a canonical GAP-* reference so the limitation is reviewable.",
                path=display_path,
                evidence=gap_without_gap[:20],
                recommended_action="Declare and link GAP-* for every gap_unclear row.",
            )
        )
    if missing_ledger_gap_decisions:
        findings.append(
            Finding(
                id="test-design-decision-table-missing-ledger-gap-decision",
                severity="warning",
                category="test-design",
                title="Test Design Decision Table misses ledger GAP/unclear decisions",
                details=(
                    "Every Atomic Requirements Ledger row with coverage_status = gap/unclear and a real GAP-* "
                    "must be represented in TDDT by a matching gap_unclear row or by the same GAP-* on the matching "
                    "source_property_id. Keeping the gap only in ledger leaves the test-design rationale and "
                    "admissibility unaudited."
                ),
                path=display_path,
                evidence=missing_ledger_gap_decisions[:20],
                recommended_action=(
                    "Add a gap_unclear TDDT row linked to the same ATOM-* and GAP-*, or carry the same GAP-* in "
                    "the blocked/gap-admissibility fields for the matching source_property_id."
                ),
            )
        )
    if gap_cross_section_conflicts:
        findings.append(
            Finding(
                id="test-design-decision-table-gap-cross-section-conflict",
                severity="warning",
                category="test-design",
                title="Gap/unclear decisions conflict with covered status in other sections",
                details=(
                    "A gap_unclear TDDT row must stay gap/unclear throughout the canonical file. "
                    "It must not be covered in the ledger, planned as an executable TC, or linked as executable risk coverage."
                ),
                path=display_path,
                evidence=gap_cross_section_conflicts[:20],
                recommended_action=(
                    "Make the gap decision consistent across Coverage Gaps, Atomic Requirements Ledger, "
                    "Package Test Design Plan and Risk / Priority Map, or reclassify the TDDT row as executable with a real oracle."
                ),
            )
        )
    if gap_executable_behavior_smells:
        findings.append(
            Finding(
                id="test-design-decision-table-gap-executable-behavior-smell",
                severity="warning",
                category="test-design",
                title="Gap/unclear decisions hide source-backed executable behavior",
                details=(
                    "A gap_unclear row is admissible only for the part that is not derivable from sources. "
                    "If the source names a visible UI result, validation message, highlight, navigation, mask, "
                    "dictionary/tag behavior, or another observable oracle, that executable part must become "
                    "standalone_tc or covered_by_existing_tc; only the blocked remainder may stay GAP-*."
                ),
                path=display_path,
                evidence=gap_executable_behavior_smells[:20],
                recommended_action=(
                    "Split each broad gap into executable TC coverage plus a narrow GAP-* for the actually missing fixture, "
                    "catalog, backend artifact, status, or source detail."
                ),
            )
        )
    if gap_overbroad_smells:
        findings.append(
            Finding(
                id="test-design-decision-table-overbroad-gap-smell",
                severity="warning",
                category="test-design",
                title="Gap/unclear decisions mix blocked input with testable behavior",
                details=(
                    "A missing catalog, fixture, status, backend artifact, or source detail can block a specific branch, "
                    "but it must not erase visible behavior that is already stated in the FT/support materials."
                ),
                path=display_path,
                evidence=gap_overbroad_smells[:20],
                recommended_action=(
                    "Move the visible/testable part to planned TC coverage and keep GAP-* only for the named blocker."
                ),
            )
        )
    if metadata_behavior_smells:
        findings.append(
            Finding(
                id="test-design-decision-table-metadata-behavior-smell",
                severity="warning",
                category="test-design",
                title="Metadata-only decisions contain observable behavior",
                details=(
                    "metadata_only is only for structural context or input classification. Source-backed visible behavior "
                    "such as hints, messages, highlights, actions, masks, dictionaries, tags, or navigation must be routed "
                    "to executable coverage or a narrow GAP-*."
                ),
                path=display_path,
                evidence=metadata_behavior_smells[:20],
                recommended_action=(
                    "Reclassify the row as standalone_tc/covered_by_existing_tc, or split it into a metadata row and a "
                    "separate executable/gap row."
                ),
            )
        )
    if date_window_gap_smells:
        findings.append(
            Finding(
                id="test-design-decision-table-date-window-gap-smell",
                severity="warning",
                category="test-design",
                title="Date validity windows are routed to gap/unclear despite source-backed boundaries",
                details=(
                    "Passport/date validity rules with source-backed age windows, boundary days, or exact hint texts "
                    "must be decomposed into boundary/equivalence obligations. A GAP-* is valid only for a missing "
                    "test clock, fixture, or unresolved boundary convention."
                ),
                path=display_path,
                evidence=date_window_gap_smells[:20],
                recommended_action=(
                    "Create date-window obligation rows and TC coverage for stated boundaries; keep GAP-* only for "
                    "unavailable clock/fixture semantics."
                ),
            )
        )
    if standalone_without_tc_or_oracle:
        findings.append(
            Finding(
                id="test-design-decision-table-standalone-without-tc-or-oracle",
                severity="warning",
                category="test-design",
                title="Standalone TC decisions lack TC-* or observable oracle source",
                details="A standalone_tc decision is valid only when it names the planned/existing TC and the source-backed observable oracle.",
                path=display_path,
                evidence=standalone_without_tc_or_oracle[:20],
                recommended_action="Add planned TC-* and a concrete oracle_source, or change the decision to gap_unclear/metadata_only.",
            )
        )
    if covered_without_tc:
        findings.append(
            Finding(
                id="test-design-decision-table-covered-existing-without-tc",
                severity="warning",
                category="test-design",
                title="Covered-by-existing decisions do not name a TC-*",
                details="covered_by_existing_tc must point to the executable TC that really covers the source property.",
                path=display_path,
                evidence=covered_without_tc[:20],
                recommended_action="Link the existing/planned executable TC-* or use gap_unclear/metadata_only.",
            )
        )
    if scenario_without_tc:
        findings.append(
            Finding(
                id="test-design-decision-table-scenario-without-tc",
                severity="warning",
                category="test-design",
                title="Scenario-only decisions do not name a scenario TC",
                details="scenario_only is allowed only when the scenario TC is named and atomic coverage is not silently replaced.",
                path=display_path,
                evidence=scenario_without_tc[:20],
                recommended_action="Link a scenario TC or split the property into standalone/gap decisions.",
            )
        )
    if scenario_remap_executable_conflicts:
        findings.append(
            Finding(
                id="test-design-decision-table-scenario-remap-executable-conflict",
                severity="warning",
                category="test-design",
                title="Scenario-only remap anchors look like executable scenario test cases",
                details=(
                    "scenario_only rows may point to retained executable scenario TC, but compatibility/remap anchors "
                    "must not present themselves as executable scenario-use-case test cases."
                ),
                path=display_path,
                evidence=scenario_remap_executable_conflicts[:20],
                recommended_action=(
                    "Change remap/compatibility sections to type `traceability-remap` or point scenario_only rows to the actual retained executable scenario TC."
                ),
            )
        )
    if executable_cross_section_conflicts:
        findings.append(
            Finding(
                id="test-design-decision-table-executable-cross-section-conflict",
                severity="warning",
                category="test-design",
                title="Executable TDDT decisions conflict with ledger, plan, or TC links",
                details=(
                    "A standalone_tc or covered_by_existing_tc decision must stay synchronized with the same atom in "
                    "Atomic Requirements Ledger, Package Test Design Plan and real TC sections. Extra or missing TC-* "
                    "links create false coverage in the decision table."
                ),
                path=display_path,
                evidence=executable_cross_section_conflicts[:20],
                recommended_action=(
                    "Synchronize planned_tc_or_gap with the atom's covered_by_tc, package plan row and TC sections, "
                    "or reclassify the row as gap_unclear/metadata_only when no executable coverage exists."
                ),
            )
        )
    if out_of_scope_without_reason:
        findings.append(
            Finding(
                id="test-design-decision-table-out-of-scope-without-reason",
                severity="warning",
                category="scope",
                title="Out-of-scope decisions lack a source or scope reason",
                details="out_of_scope rows need a concrete scope/source reason to avoid hiding omissions.",
                path=display_path,
                evidence=out_of_scope_without_reason[:20],
                recommended_action="Add the scope decision/source reference that excludes the property.",
            )
        )
    if value_type_standalone:
        findings.append(
            Finding(
                id="test-design-decision-table-value-type-standalone-smell",
                severity="warning",
                category="test-design",
                title="Value-type or control-type metadata is planned as standalone TC without concrete behavior",
                details="Rows such as `тип значения` or `тип контрола` should not become standalone pseudo tests unless the oracle names concrete observable input/widget/format behavior.",
                path=display_path,
                evidence=value_type_standalone[:20],
                recommended_action="Use metadata_only, gap_unclear, or covered_by_existing_tc through concrete format/input/widget checks.",
            )
        )
    if merged_numeric_class_decisions:
        findings.append(
            Finding(
                id="test-design-decision-table-merged-numeric-class-decision",
                severity="warning",
                category="test-design",
                title="Test Design Decision Table merges numeric invalid classes in one decision",
                details=(
                    "A numeric-format decision should not compress independent invalid classes such as letters, "
                    "decimal separators, signs, spaces and special characters into one decision row with multiple "
                    "TC-* links. That makes the decision table inconsistent with class-level coverage obligations."
                ),
                path=display_path,
                evidence=merged_numeric_class_decisions[:20],
                recommended_action=(
                    "Split the decision into class-level numeric-format rows or align each decision to one "
                    "Coverage Obligation Table class and one primary TC-* or GAP-*."
                ),
            )
        )
    if artificial_numeric_type_decisions:
        findings.append(
            Finding(
                id="test-design-decision-table-artificial-numeric-property-type",
                severity="warning",
                category="test-design",
                title="Test Design Decision Table uses artificial numeric property types",
                details=(
                    "TDDT property_type must preserve the normalized source property type. Invalid numeric classes "
                    "are class-level obligations under `numeric-format`, not property types such as "
                    "`numeric-format-invalid`, `numeric-negative` or `non-digit-rejection`."
                ),
                path=display_path,
                evidence=artificial_numeric_type_decisions[:20],
                recommended_action=(
                    "Use `numeric-format` as property_type and point each class-level decision to one "
                    "Coverage Obligation Table class, TC-* or GAP-*."
                ),
            )
        )
    if unknown_test_case_ids:
        findings.append(
            Finding(
                id="test-design-decision-table-unknown-test-case-id",
                severity="warning",
                category="traceability",
                title="Test Design Decision Table references unknown TC-* ids",
                details="planned_tc_or_gap must point to canonical TC-* sections in the same artifact/package.",
                path=display_path,
                evidence=unknown_test_case_ids[:20],
                recommended_action="Create the referenced TC-* or update planned_tc_or_gap to existing ids.",
            )
        )

    has_warnings = any(finding.severity == "warning" for finding in findings)
    checks.append(
        Check(
            "test-design-decision-table",
            "warn" if has_warnings else "pass",
            "Test Design Decision Table has issues." if has_warnings else "Test Design Decision Table contract passed.",
            display_path,
        )
    )
    return findings, checks


def coverage_obligation_relevant_source_rows(content: str) -> list[dict[str, str]]:
    _, normalization_rows = parsed_section_table_rows(content, "Source Table Normalization")
    relevant_rows: list[dict[str, str]] = []
    for row in normalization_rows:
        source_property_id = row.get("source_property_id", "").strip()
        property_type = row.get("property", "").strip().strip("`").lower()
        if not source_property_id or source_property_id == "-":
            continue
        if property_type not in COVERAGE_OBLIGATION_REQUIRED_CLASSES_BY_PROPERTY_TYPE:
            continue
        if real_gap_ids(row.get("gap_id", "")):
            continue
        relevant_rows.append(row)
    return relevant_rows


def should_require_coverage_obligation_table(content: str) -> bool:
    if not coverage_obligation_relevant_source_rows(content):
        return False
    return (
        extract_markdown_section(content, "Test Design Decision Table") is not None
        or extract_markdown_section(content, "Package Test Design Plan") is not None
        or extract_markdown_section(content, "Atomic Requirements Ledger") is not None
        or bool(extract_test_case_blocks(content))
    )


def validate_coverage_obligation_table(
    content: str,
    path: Path,
    root: Path,
    *,
    known_test_case_ids: set[str] | None = None,
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    relevant_source_rows = coverage_obligation_relevant_source_rows(content)
    relevant_by_source_property = {
        row.get("source_property_id", "").strip(): row
        for row in relevant_source_rows
        if row.get("source_property_id", "").strip()
    }
    is_required = should_require_coverage_obligation_table(content)
    section = extract_markdown_section(content, "Coverage Obligation Table")

    if not is_required and section is None:
        checks.append(
            Check(
                "coverage-obligation-table",
                "pass",
                "Coverage Obligation Table is not required for this artifact.",
                display_path,
            )
        )
        return findings, checks

    if section is None:
        evidence = [
            (
                f"{row.get('source_property_id', '-')}:"
                f"{row.get('property', '-')}:"
                f"{row.get('requirement_code', '-')}"
            )
            for row in relevant_source_rows[:20]
        ]
        findings.append(
            Finding(
                id="coverage-obligation-table-missing",
                severity="warning",
                category="test-design",
                title="Coverage Obligation Table is missing",
                details=(
                    "Source properties with mandatory coverage classes, such as numeric-format and amount-tags, "
                    "must be expanded into explicit coverage obligations before Package Test Design Plan and TC-* "
                    "can be trusted."
                ),
                path=display_path,
                evidence=evidence,
                recommended_action=(
                    "Add `## Coverage Obligation Table` after Test Design Decision Table. For each relevant "
                    "source_property_id, list every required obligation_class and map it to a TC-* or GAP-*."
                ),
            )
        )
        checks.append(Check("coverage-obligation-table", "warn", "Coverage Obligation Table is missing.", display_path))
        return findings, checks

    header, rows = parsed_section_table_rows(content, "Coverage Obligation Table")
    if not rows:
        findings.append(
            Finding(
                id="coverage-obligation-table-no-table",
                severity="warning",
                category="test-design",
                title="Coverage Obligation Table has no parseable table",
                details="The section exists but has no Markdown table rows.",
                path=display_path,
                evidence=[],
                recommended_action="Use the canonical Coverage Obligation Table columns from coverage-obligation-table-format.md.",
            )
        )
        checks.append(Check("coverage-obligation-table", "warn", "Coverage Obligation Table table is missing.", display_path))
        return findings, checks

    missing_columns = sorted(COVERAGE_OBLIGATION_TABLE_REQUIRED_COLUMNS - set(header))
    if missing_columns:
        findings.append(
            Finding(
                id="coverage-obligation-table-missing-columns",
                severity="warning",
                category="test-design",
                title="Coverage Obligation Table misses required columns",
                details="The obligation table must expose source property, atom, obligation class, required behavior and TC/GAP mapping.",
                path=display_path,
                evidence=[f"missing={', '.join(missing_columns)}", f"columns={', '.join(header[:14])}"],
                recommended_action="Rewrite the table with the canonical columns from coverage-obligation-table-format.md.",
            )
        )

    classes_by_source_property: dict[str, set[str]] = defaultdict(set)
    duplicate_keys: list[str] = []
    unknown_source_properties: list[str] = []
    missing_tc_or_gap_rows: list[str] = []
    invalid_status_rows: list[str] = []
    unknown_test_case_ids: list[str] = []
    mask_obligations_without_mask_oracle: list[str] = []
    artificial_numeric_obligation_rows: list[str] = []
    seen_keys: set[tuple[str, str]] = set()
    test_case_blocks_by_id = {test_case_id: block for test_case_id, block in extract_test_case_blocks(content)}

    for index, row in enumerate(rows, start=2):
        obligation_id = row.get("obligation_id", "").strip() or f"row {index}"
        source_property_id = row.get("source_property_id", "").strip()
        property_type = row.get("property_type", "").strip().strip("`").lower()
        obligation_class = row.get("obligation_class", "").strip().strip("`").lower()
        status = row.get("status", "").strip().strip("`").lower()
        planned_tc_or_gap = row.get("planned_tc_or_gap", "").strip()
        row_label = f"{obligation_id}:{source_property_id or '<missing source_property_id>'}:{obligation_class or '<missing class>'}"

        if property_type in ARTIFICIAL_NUMERIC_PROPERTY_TYPES:
            artificial_numeric_obligation_rows.append(f"{row_label}:property_type={property_type}")
        if source_property_id and source_property_id not in relevant_by_source_property:
            unknown_source_properties.append(row_label)

        if source_property_id and obligation_class:
            key = (source_property_id, obligation_class)
            if key in seen_keys:
                duplicate_keys.append(row_label)
            seen_keys.add(key)
            classes_by_source_property[source_property_id].add(obligation_class)

        if status and status not in COVERAGE_OBLIGATION_ALLOWED_STATUSES:
            invalid_status_rows.append(f"{row_label}:status={status}")

        planned_test_case_ids = extract_test_case_ids_from_text(planned_tc_or_gap)
        planned_gap_ids = extract_gap_ids_from_text(planned_tc_or_gap)
        if status not in {"not-applicable", "n/a"} and not planned_test_case_ids and not planned_gap_ids:
            missing_tc_or_gap_rows.append(f"{row_label}:planned_tc_or_gap={planned_tc_or_gap or '-'}")

        if known_test_case_ids:
            for test_case_id in planned_test_case_ids:
                if test_case_id not in known_test_case_ids:
                    unknown_test_case_ids.append(f"{row_label}:{test_case_id}")
        if planned_test_case_ids and MASK_OBLIGATION_CLASS_RE.search(obligation_class):
            for test_case_id in planned_test_case_ids:
                block = test_case_blocks_by_id.get(test_case_id, "")
                if not block:
                    continue
                tc_context = " ".join(
                    [
                        extract_test_case_field_block(block, ["Title", "title", "Название"]),
                        extract_test_case_field_block(block, ["Goal", "goal", "Цель"]),
                        extract_test_case_field_block(block, ["Test Data", "test_data", "test data", "Тестовые данные"]),
                        extract_test_case_field_block(block, ["Steps", "steps", "Шаги"]),
                        extract_test_case_expected_result(block),
                    ]
                )
                if not MASK_OBSERVABLE_ORACLE_RE.search(tc_context):
                    mask_obligations_without_mask_oracle.append(
                        f"{row_label}:{test_case_id}:context={tc_context[:160] or '<empty>'}"
                    )

    missing_required_classes: list[str] = []
    for source_property_id, source_row in sorted(relevant_by_source_property.items()):
        property_type = source_row.get("property", "").strip().strip("`").lower()
        required_classes = set(COVERAGE_OBLIGATION_REQUIRED_CLASSES_BY_PROPERTY_TYPE.get(property_type, ()))
        missing_classes = sorted(required_classes - classes_by_source_property.get(source_property_id, set()))
        if missing_classes:
            missing_required_classes.append(
                (
                    f"{source_property_id}:"
                    f"{property_type}:"
                    f"{source_row.get('requirement_code', '-')}:"
                    f"missing={', '.join(missing_classes)}"
                )
            )

    if missing_required_classes:
        findings.append(
            Finding(
                id="coverage-obligation-table-missing-required-class",
                severity="warning",
                category="test-design",
                title="Coverage Obligation Table misses required coverage classes",
                details=(
                    "A covered source property can still be under-tested when required obligation classes are absent. "
                    "For example, numeric-format needs valid digits plus separate rejection classes for letters, spaces, "
                    "special characters, decimal separators and signs."
                ),
                path=display_path,
                evidence=missing_required_classes[:20],
                recommended_action="Add one obligation row for each missing class and map it to a TC-* or a source-specific GAP-*.",
            )
        )
    if unknown_source_properties:
        findings.append(
            Finding(
                id="coverage-obligation-table-unknown-source-property",
                severity="warning",
                category="traceability",
                title="Coverage Obligation Table references unknown or non-obligatory source properties",
                details="Obligation rows must point to source_property_id values from Source Table Normalization that need obligation expansion.",
                path=display_path,
                evidence=unknown_source_properties[:20],
                recommended_action="Use the exact source_property_id from Source Table Normalization or remove the row if it is not an obligation-bearing property.",
            )
        )
    if artificial_numeric_obligation_rows:
        findings.append(
            Finding(
                id="coverage-obligation-table-artificial-numeric-property-type",
                severity="warning",
                category="test-design",
                title="Coverage Obligation Table uses artificial numeric property types",
                details=(
                    "Coverage obligations must keep `property_type = numeric-format` and express invalid inputs "
                    "through `obligation_class`, for example `reject-letters`, `reject-spaces`, "
                    "`reject-special-chars`, `reject-decimal-separator` and `reject-sign`."
                ),
                path=display_path,
                evidence=artificial_numeric_obligation_rows[:20],
                recommended_action=(
                    "Move artificial property types such as `numeric-format-invalid`, `numeric-negative` or "
                    "`non-digit-rejection` into class-level obligation rows under the original numeric-format "
                    "source_property_id."
                ),
            )
        )
    if duplicate_keys:
        findings.append(
            Finding(
                id="coverage-obligation-table-duplicate-class",
                severity="warning",
                category="test-design",
                title="Coverage Obligation Table has duplicate source/class rows",
                details="A source_property_id should have at most one row per obligation_class. Split behavior only when it is a different class.",
                path=display_path,
                evidence=duplicate_keys[:20],
                recommended_action="Merge duplicate obligation rows or give each row a distinct obligation_class.",
            )
        )
    if missing_tc_or_gap_rows:
        findings.append(
            Finding(
                id="coverage-obligation-table-missing-tc-or-gap",
                severity="warning",
                category="traceability",
                title="Coverage obligation rows have no TC-* or GAP-* mapping",
                details="Every required coverage obligation must resolve to executable coverage or an explicit source-specific gap.",
                path=display_path,
                evidence=missing_tc_or_gap_rows[:20],
                recommended_action="Fill planned_tc_or_gap with an existing/planned TC-* or GAP-*.",
            )
        )
    if invalid_status_rows:
        findings.append(
            Finding(
                id="coverage-obligation-table-invalid-status",
                severity="warning",
                category="test-design",
                title="Coverage Obligation Table uses invalid status values",
                details="Status must be one of covered, gap, unclear, blocked, not-applicable or n/a.",
                path=display_path,
                evidence=invalid_status_rows[:20],
                recommended_action="Normalize status values to the canonical vocabulary.",
            )
        )
    if unknown_test_case_ids:
        findings.append(
            Finding(
                id="coverage-obligation-table-unknown-test-case-id",
                severity="warning",
                category="traceability",
                title="Coverage Obligation Table references unknown TC-* ids",
                details="planned_tc_or_gap must point to canonical TC-* sections in the same artifact/package.",
                path=display_path,
                evidence=unknown_test_case_ids[:20],
                recommended_action="Create the referenced TC-* or update planned_tc_or_gap to existing ids.",
            )
        )
    if mask_obligations_without_mask_oracle:
        findings.append(
            Finding(
                id="coverage-obligation-table-mask-oracle-missing",
                severity="warning",
                category="test-design",
                title="Mask coverage obligations are linked to TC-* without mask oracle",
                details=(
                    "A format-mask/default-mask obligation is not covered by generic numeric input or letter rejection. "
                    "The linked TC must verify the displayed mask/template or route the exact mask behavior to GAP-*."
                ),
                path=display_path,
                evidence=mask_obligations_without_mask_oracle[:20],
                recommended_action=(
                    "Rewrite the linked TC to assert the source-backed mask/template, or replace the TC mapping "
                    "with a source-specific GAP-* if exact mask rendering is unclear."
                ),
            )
        )

    has_warnings = any(finding.severity == "warning" for finding in findings)
    checks.append(
        Check(
            "coverage-obligation-table",
            "warn" if has_warnings else "pass",
            "Coverage Obligation Table has issues." if has_warnings else "Coverage Obligation Table contract passed.",
            display_path,
        )
    )
    return findings, checks


def validate_writer_quality_gate(
    content: str,
    path: Path,
    root: Path,
    *,
    suppress_blocked_input_failures: bool = False,
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    summary = writer_quality_gate_summary(content)

    if not summary["present"]:
        if should_require_writer_quality_gate(content):
            findings.append(
                Finding(
                    id="writer-quality-gate-missing",
                    severity="warning",
                    category="test-case-format",
                    title="Package-based test-case file has no Writer Quality Gate",
                    details=(
                        "Package-based writer output must self-reject semantic compression, merged TC, "
                        "broad GSR ranges and unobservable internal behavior before it is sent to reviewer."
                    ),
                    path=display_path,
                    evidence=[],
                    recommended_action="Add `## Writer Quality Gate` with the canonical gate items and block failed packages before ready-for-review.",
                )
            )
            checks.append(Check("writer-quality-gate", "warn", "Writer Quality Gate is missing.", display_path))
        else:
            checks.append(Check("writer-quality-gate", "pass", "Writer Quality Gate is not required for this legacy/simple file.", display_path))
        return findings, checks

    if not summary["parseable"]:
        findings.append(
            Finding(
                id="writer-quality-gate-no-table",
                severity="warning",
                category="test-case-format",
                title="Writer Quality Gate has no parseable Markdown table",
                details="The section exists but has no canonical Markdown table.",
                path=display_path,
                evidence=[],
                recommended_action="Use the canonical Writer Quality Gate table format.",
            )
        )
    if summary["missing_columns"]:
        findings.append(
            Finding(
                id="writer-quality-gate-missing-columns",
                severity="warning",
                category="test-case-format",
                title="Writer Quality Gate misses required columns",
                details="The gate must expose item, status, evidence, affected package, required action and blocking flag.",
                path=display_path,
                evidence=[f"missing={', '.join(summary['missing_columns'])}"],
                recommended_action="Rewrite the gate table with the canonical columns from writer-quality-gate-format.md.",
            )
        )
    if summary["missing_items"]:
        findings.append(
            Finding(
                id="writer-quality-gate-missing-required-items",
                severity="warning",
                category="test-design",
                title="Writer Quality Gate misses required gate items",
                details="The gate must explicitly check artifact write strategy, mockup visual inventory, source normalization, ledger atomicity, GSR compression, plan atomicity, scenarios, TC atomicity, observability and package readiness.",
                path=display_path,
                evidence=summary["missing_items"][:20],
                recommended_action="Add one row for each required gate item before moving the writer artifact to review.",
            )
        )
    if summary["invalid_status_rows"]:
        findings.append(
            Finding(
                id="writer-quality-gate-invalid-status",
                severity="warning",
                category="test-case-format",
                title="Writer Quality Gate has noncanonical status values",
                details="Gate status values must be canonical pass/fail-style values.",
                path=display_path,
                evidence=summary["invalid_status_rows"][:20],
                recommended_action="Use `pass` for passed checks or `fail`/`blocked`/`needs-rewrite` for failed checks.",
            )
        )
    if summary["invalid_blocks_rows"]:
        findings.append(
            Finding(
                id="writer-quality-gate-invalid-blocks-value",
                severity="warning",
                category="test-case-format",
                title="Writer Quality Gate has invalid blocks_ready_for_review values",
                details="The blocking flag must be `yes` or `no`.",
                path=display_path,
                evidence=summary["invalid_blocks_rows"][:20],
                recommended_action="Set `blocks_ready_for_review` to `yes` only for blocking failed gate rows, otherwise `no`.",
            )
        )
    if summary["failed_rows"] and not suppress_blocked_input_failures:
        findings.append(
            Finding(
                id="writer-quality-gate-failed",
                severity="warning",
                category="test-design",
                title="Writer Quality Gate contains blocking failures",
                details="The writer file self-identifies failed quality gates. It must not be routed to reviewer until the affected packages are rewritten or the workflow is blocked.",
                path=display_path,
                evidence=summary["failed_rows"][:20],
                recommended_action="Rewrite affected packages from Source Table Normalization through TC, or set workflow-state to blocked-input.",
            )
        )
    if summary["package_ready_conflicts"]:
        findings.append(
            Finding(
                id="writer-quality-gate-package-ready-conflict",
                severity="warning",
                category="test-design",
                title="Writer Quality Gate marks package-ready despite failed gates",
                details=(
                    "`package-ready` cannot pass while any other gate item is failed or blocking. "
                    "This creates a false ready-for-review signal."
                ),
                path=display_path,
                evidence=summary["package_ready_conflicts"][:20],
                recommended_action=(
                    "Either fix the failed gate rows and then mark package-ready pass, or set package-ready to fail/blocking."
                ),
            )
        )
    if summary["known_risk_not_blocking"]:
        findings.append(
            Finding(
                id="writer-quality-gate-known-risk-not-blocking",
                severity="warning",
                category="test-design",
                title="Writer self-check reports merged checks as known risk without blocking the gate",
                details="A known semantic-compression or merged-check risk cannot be accepted in ready-for-review output.",
                path=display_path,
                evidence=["possible merged checks / semantic compression marked as known risk"],
                recommended_action="Add a failed blocking Writer Quality Gate row and rewrite the affected package before review.",
            )
        )
    scoped_profile_issues, scoped_profile_evidence = validate_writer_quality_gate_scoped_validator_profile(
        content,
        path,
        root,
    )
    if scoped_profile_issues:
        findings.append(
            Finding(
                id="writer-quality-gate-scoped-validator-profile-invalid",
                severity="warning",
                category="test-design",
                title="Writer Quality Gate claims clean scoped validator without a valid profile",
                details=(
                    "`scoped-validator-findings = pass` must be backed by a persisted scoped validator JSON profile "
                    "with command, scope, canonical/test-design paths, current-scope findings and unresolved warning/error count."
                ),
                path=display_path,
                evidence=[*scoped_profile_issues[:20], *scoped_profile_evidence[:8]],
                recommended_action=(
                    "Write `outputs/scoped-validator-profile.<stage>.json` after the final validator run and set "
                    "`unresolved_warning_error_count` to 0 only when every current-scope warning/error is fixed or validly waived."
                ),
            )
        )

    has_findings = any(finding.id.startswith("writer-quality-gate") for finding in findings)
    checks.append(
        Check(
            "writer-quality-gate",
            "warn" if has_findings else "pass",
            "Writer Quality Gate has issues." if has_findings else "Writer Quality Gate passed.",
            display_path,
        )
    )
    return findings, checks


def should_require_artifact_write_strategy(content: str, blocks: list[tuple[str, str]]) -> bool:
    return should_require_artifact_write_strategy_for_content(content, blocks)


def should_require_artifact_write_strategy_for_content(content: str, blocks: list[tuple[str, str]]) -> bool:
    atom_count = len(atomic_requirement_ledger_atom_ids(content))
    has_internal_work_packages = bool(re.search(r"\bWP-\d{2}\b|Internal Work Package Coverage", content))
    return (
        len(blocks) > ARTIFACT_WRITE_STRATEGY_MIN_TC_COUNT
        or atom_count > ARTIFACT_WRITE_STRATEGY_MIN_ATOM_COUNT
        or len(content) > ARTIFACT_WRITE_STRATEGY_MIN_CHARS
        or has_internal_work_packages
    )


def validate_artifact_write_strategy(
    content: str,
    path: Path,
    root: Path,
    *,
    blocks: list[tuple[str, str]],
    structural_severity: str,
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    section = extract_markdown_section(content, "Artifact Write Strategy")
    required = should_require_artifact_write_strategy_for_content(content, blocks) and not is_production_test_case_path(path)

    if not required:
        checks.append(
            Check(
                "artifact-write-strategy",
                "pass",
                "Artifact Write Strategy is not required for this small/simple file.",
                display_path,
            )
        )
        return findings, checks

    atom_count = len(atomic_requirement_ledger_atom_ids(content))
    requirement_evidence = [
        f"chars={len(content)}",
        f"tc_count={len(blocks)}",
        f"atom_count={atom_count}",
        "has_wp=yes" if re.search(r"\bWP-\d{2}\b|Internal Work Package Coverage", content) else "has_wp=no",
    ]

    if section is None:
        findings.append(
            Finding(
                id="artifact-write-strategy-missing",
                severity="warning",
                category="test-case-format",
                title="Large canonical test-case file has no Artifact Write Strategy",
                details=(
                    "Large or package-based writer outputs must record the preflight write strategy before "
                    "content generation so the writer does not hit Windows command-line limits or switch to "
                    "compact/ad-hoc generation."
                ),
                path=display_path,
                evidence=requirement_evidence,
                recommended_action=(
                    "Add `## Artifact Write Strategy` with preflight result, file-based/chunked write method, "
                    "WP chunk plan, helper artifact policy and validation plan."
                ),
            )
        )
        checks.append(Check("artifact-write-strategy", "warn", "Artifact Write Strategy is missing.", display_path))
        return findings, checks

    if not ARTIFACT_WRITE_STRATEGY_PREFLIGHT_RE.search(section) or not ARTIFACT_WRITE_STRATEGY_SAFE_METHOD_RE.search(section):
        findings.append(
            Finding(
                id="artifact-write-strategy-unsafe-or-vague",
                severity="warning",
                category="test-case-format",
                title="Artifact Write Strategy does not prove safe file-based writing",
                details=(
                    "The strategy must show a preflight decision and an explicitly safe file-based/chunked method "
                    "such as `scripts/update_markdown_section.py --content-file` or `--stdin`."
                ),
                path=display_path,
                evidence=[section.strip()[:500]],
                recommended_action=(
                    "State the preflight trigger, selected write method, chunk plan by `WP-*`, forbidden methods "
                    "and validation checkpoints."
                ),
            )
        )

    unsafe_method_rows: list[str] = []
    strategy_rows = markdown_table_rows_from_text(section)
    if strategy_rows:
        header = normalize_table_header(strategy_rows[0])
        for row in strategy_rows[1:]:
            row_map = {
                column_name: row[index].strip().strip("`") if index < len(row) else ""
                for index, column_name in enumerate(header)
            }
            item = row_map.get("item", "") or row_map.get("field", "") or row_map.get("name", "")
            if "forbidden" in item.lower():
                continue
            if not ARTIFACT_WRITE_STRATEGY_METHOD_ITEM_RE.search(item):
                continue
            inspected = " | ".join(value for value in row_map.values() if value)
            if SESSION_LOG_FORBIDDEN_INITIAL_WRITE_RE.search(inspected):
                unsafe_method_rows.append(inspected[:220])
    else:
        unsafe_method_rows = [
            line.strip()[:220]
            for line in section.splitlines()
            if ARTIFACT_WRITE_STRATEGY_METHOD_ITEM_RE.search(line)
            and SESSION_LOG_FORBIDDEN_INITIAL_WRITE_RE.search(line)
        ]

    if unsafe_method_rows:
        findings.append(
            Finding(
                id="artifact-write-strategy-forbidden-initial-method",
                severity="warning",
                category="test-case-format",
                title="Artifact Write Strategy selects a forbidden one-shot write method",
                details=(
                    "Large/package-based canonical files must not start with one-shot PowerShell, here-string, "
                    "inline giant command or command-line transport. The safe file/chunked method must be selected "
                    "before the first write attempt."
                ),
                path=display_path,
                evidence=unsafe_method_rows[:10],
                recommended_action=(
                    "Rewrite the strategy to use `scripts/update_markdown_section.py --content-file` / `--stdin` "
                    "or another committed file-based helper before content generation."
                ),
            )
        )

    if ARTIFACT_WRITE_STRATEGY_TMP_GENERATOR_RE.search(section):
        findings.append(
            Finding(
                id="artifact-write-strategy-ad-hoc-tmp-generator",
                severity="warning",
                category="test-case-format",
                title="Artifact Write Strategy uses an ad-hoc tmp generator",
                details=(
                    "A temporary `tmp/generate_*.py` writer can turn test-case writing into template generation and "
                    "hide quality risks. Large canonical files should use the project section updater or a committed, "
                    "reviewable helper under `scripts/`."
                ),
                path=display_path,
                evidence=[match.group(0) for match in ARTIFACT_WRITE_STRATEGY_TMP_GENERATOR_RE.finditer(section)][:10],
                recommended_action=(
                    "Use `scripts/update_markdown_section.py --content-file` / `--stdin`, or move the helper into "
                    "`scripts/` with tests before relying on it."
                ),
            )
        )

    if not SESSION_LOG_ARTIFACT_WRITER_HELPER_RE.search(section):
        findings.append(
            Finding(
                id="artifact-write-strategy-helper-missing",
                severity="warning",
                category="test-case-format",
                title="Artifact Write Strategy does not use the canonical artifact writer helper",
                details=(
                    "Large/package-based canonical files must use `scripts/write_artifact_sections.py` as the "
                    "default write path. Older single-section helpers are acceptable for small targeted edits, but "
                    "not as the primary path for large generated artifacts."
                ),
                path=display_path,
                evidence=[section.strip()[:500]],
                recommended_action="Use `scripts/write_artifact_sections.py --manifest <manifest.json>`.",
            )
        )

    has_findings = any(finding.id.startswith("artifact-write-strategy") for finding in findings)
    checks.append(
        Check(
            "artifact-write-strategy",
            "warn" if has_findings else "pass",
            "Artifact Write Strategy has issues." if has_findings else "Artifact Write Strategy contract passed.",
            display_path,
        )
    )
    return findings, checks


def ledger_source_table_residue_evidence(content: str) -> list[str]:
    _, ledger_rows = parsed_atomic_requirement_ledger_rows(content)
    evidence: list[str] = []
    for row in ledger_rows:
        atom_id = row.get("atom_id", "").strip() or "<missing>"
        inspected_text = " | ".join(
            row.get(field, "")
            for field in ("atomic_statement", "expected_behavior", "condition")
            if row.get(field)
        )
        if inspected_text and has_source_table_residue(inspected_text):
            evidence.append(f"{atom_id}:{inspected_text[:180]}")
    return evidence


def validate_source_table_normalization(
    content: str,
    path: Path,
    root: Path,
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    section = extract_markdown_section(content, "Source Table Normalization")
    residue_evidence = ledger_source_table_residue_evidence(content)

    if section is None:
        if residue_evidence:
            findings.append(
                Finding(
                    id="source-table-normalization-missing-for-dirty-ledger",
                    severity="warning",
                    category="traceability",
                    title="Source table normalization is missing while ledger contains table extraction residue",
                    details=(
                        "Ledger rows appear to include source table headers, neighboring fields, or extraction residue. "
                        "A Source Table Normalization section is required before such rows can become ATOM-* coverage."
                    ),
                    path=display_path,
                    evidence=residue_evidence[:20],
                    recommended_action=(
                        "Add Source Table Normalization, split dirty source rows into clean field/property/condition/"
                        "expected_behavior rows, and route low-confidence rows to GAP-* instead of covered atoms."
                    ),
                )
            )
            checks.append(
                Check(
                    "source-table-normalization",
                    "warn",
                    "Source Table Normalization is missing for dirty ledger rows.",
                    display_path,
                )
            )
        return findings, checks

    rows = markdown_table_rows_from_text(section)
    if not rows:
        findings.append(
            Finding(
                id="source-table-normalization-no-table",
                severity="warning",
                category="traceability",
                title="Source Table Normalization has no Markdown table",
                details="The section exists but has no parseable Markdown table.",
                path=display_path,
                evidence=[],
                recommended_action="Use the canonical Source Table Normalization table.",
            )
        )
        checks.append(Check("source-table-normalization", "warn", "Source Table Normalization table is missing.", display_path))
        return findings, checks

    header = normalize_table_header(rows[0])
    required_columns = {
        "source_row_id",
        "package_id",
        "field_or_block",
        "property",
        "condition",
        "expected_behavior",
        "requirement_code",
        "source_ref",
        "confidence",
        "gap_id",
    }
    missing_columns = sorted(required_columns - set(header))
    if missing_columns:
        findings.append(
            Finding(
                id="source-table-normalization-missing-columns",
                severity="warning",
                category="traceability",
                title="Source Table Normalization misses required columns",
                details="Normalization rows must expose source row, package, field/block, property, condition, expected behavior, requirement code, source ref, confidence and gap.",
                path=display_path,
                evidence=[f"missing={', '.join(missing_columns)}", f"columns={', '.join(header[:14])}"],
                recommended_action="Rewrite the table with the canonical columns from source-table-normalization-format.md.",
            )
        )

    parsed_rows: list[dict[str, str]] = []
    for row in rows[1:]:
        parsed_rows.append(
            {
                column_name: row[index].strip().strip("`") if index < len(row) else ""
                for index, column_name in enumerate(header)
            }
        )

    low_conf_without_gap: list[str] = []
    residue_rows: list[str] = []
    combined_rows: list[str] = []
    combined_property_class_rows: list[str] = []
    dictionary_source_rows: list[str] = []
    dictionary_misclassified_rows: list[str] = []
    missing_property_ids: list[str] = []
    duplicate_property_ids: list[str] = []
    multiple_gsr_rows: list[str] = []
    unmapped_property_rows: list[str] = []
    missing_ledger_gap_atoms: list[str] = []
    unknown_atoms: list[str] = []
    artificial_numeric_property_rows: list[str] = []
    property_ids_seen: set[str] = set()
    normalization_rows_by_source: dict[str, list[dict[str, str]]] = {}
    ledger_atom_ids = atomic_requirement_ledger_atom_ids(content)
    has_source_property_id_column = "source_property_id" in header
    for index, row in enumerate(parsed_rows, start=2):
        row_id = row.get("source_row_id", "").strip() or f"row {index}"
        source_property_id = row.get("source_property_id", "").strip()
        normalization_rows_by_source.setdefault(row_id, []).append(row)
        if not has_source_property_id_column or source_property_id in {"", "-"}:
            missing_property_ids.append(f"{row_id}:source_property_id={source_property_id or '-'}")
        elif source_property_id in property_ids_seen:
            duplicate_property_ids.append(f"{row_id}:source_property_id={source_property_id}")
        else:
            property_ids_seen.add(source_property_id)

        confidence = row.get("confidence", "").strip().lower()
        gap_id = row.get("gap_id", "").strip()
        if confidence in {"low", "unclear"} and not re.search(r"\bGAP-\d+\b", gap_id):
            low_conf_without_gap.append(f"{row_id}:confidence={confidence};gap_id={gap_id or '-'}")

        requirement_codes = extract_requirement_codes_from_text(row.get("requirement_code", ""))
        if len(requirement_codes) > 1:
            property_ref = source_property_id or "-"
            multiple_gsr_rows.append(f"{row_id}:{property_ref}:{'; '.join(requirement_codes[:12])}")

        inspected_text = " | ".join(
            row.get(field, "")
            for field in ("field_or_block", "property", "condition", "expected_behavior")
            if row.get(field)
        )
        if inspected_text and has_source_table_residue(inspected_text):
            residue_rows.append(f"{row_id}:{inspected_text[:180]}")
        if inspected_text and has_combined_behavior_smell(inspected_text):
            combined_rows.append(f"{row_id}:{inspected_text[:180]}")
        property_classes = source_normalization_property_classes(row)
        if len(property_classes) > 1:
            property_ref = source_property_id or "-"
            combined_property_class_rows.append(
                f"{row_id}:{property_ref}:classes={', '.join(property_classes)}:{inspected_text[:160]}"
            )
        property_type = row.get("property", "").strip().strip("`")
        normalized_property_type = property_type.lower()
        if normalized_property_type in ARTIFICIAL_NUMERIC_PROPERTY_TYPES:
            property_ref = source_property_id or "-"
            artificial_numeric_property_rows.append(f"{row_id}:{property_ref}:property={property_type}")
        if (
            "dictionary-source" in property_classes
            or DICTIONARY_PROPERTY_TYPE_RE.search(property_type)
            or (inspected_text and DICTIONARY_SOURCE_TEXT_RE.search(inspected_text))
        ):
            property_ref = source_property_id or "-"
            dictionary_source_rows.append(f"{row_id}:{property_ref}:property={property_type or '-'}")
        if (
            inspected_text
            and DICTIONARY_SOURCE_TEXT_RE.search(inspected_text)
            and not DICTIONARY_PROPERTY_TYPE_RE.search(property_type)
            and not real_gap_ids(gap_id)
        ):
            property_ref = source_property_id or "-"
            dictionary_misclassified_rows.append(
                f"{row_id}:{property_ref}:property={property_type or '-'}:{inspected_text[:160]}"
            )

        linked_atoms_value = row.get("linked_atoms", "")
        if not extract_any_atom_ids_from_text(linked_atoms_value) and not extract_gap_ids_from_text(gap_id):
            property_ref = source_property_id or "-"
            unmapped_property_rows.append(f"{row_id}:{property_ref}:linked_atoms={linked_atoms_value or '-'};gap_id={gap_id or '-'}")
        if linked_atoms_value and ledger_atom_ids:
            for atom_id in extract_any_atom_ids_from_text(linked_atoms_value):
                if atom_id not in ledger_atom_ids:
                    unknown_atoms.append(f"{row_id}:{atom_id}")

    for ledger_row in ledger_rows_with_real_gap_ids(content):
        atom_id = ledger_row.get("atom_id", "").strip().strip("`")
        source_property_id = ledger_row.get("source_property_id", "").strip().strip("`")
        ledger_gap_ids = set(real_gap_ids(" | ".join(ledger_row.values())))
        represented = False
        for row in parsed_rows:
            row_source_property_id = row.get("source_property_id", "").strip().strip("`")
            linked_atom_ids = set(extract_any_atom_ids_from_text(row.get("linked_atoms", "")))
            row_gap_ids = set(real_gap_ids(row.get("gap_id", "")))
            if atom_id and atom_id in linked_atom_ids:
                represented = True
                break
            if ledger_gap_ids and ledger_gap_ids.intersection(row_gap_ids):
                if not source_property_id or not row_source_property_id or row_source_property_id == source_property_id:
                    represented = True
                    break
        if not represented:
            missing_ledger_gap_atoms.append(
                f"{atom_id or '<missing atom>'}:source_property_id={source_property_id or '-'};"
                f"gap_id={', '.join(sorted(ledger_gap_ids)) or '-'}"
            )

    inventory_rows = parsed_source_row_inventory_rows(content)
    source_rows_with_many_codes: list[str] = []
    source_row_code_mismatches: list[str] = []
    for index, inventory_row in enumerate(inventory_rows, start=2):
        source_row_id = inventory_row.get("source_row_id", "").strip() or f"row {index}"
        in_scope = inventory_row.get("in_scope", "").strip().strip("`").lower()
        if in_scope not in {"yes", "unclear"}:
            continue
        inventory_codes = extract_requirement_codes_from_text(inventory_row.get("requirement_codes", ""))
        if len(inventory_codes) <= 1:
            continue
        source_rows_with_many_codes.append(f"{source_row_id}:{'; '.join(inventory_codes[:12])}")
        normalized_rows = normalization_rows_by_source.get(source_row_id, [])
        normalized_codes: set[str] = set()
        normalized_property_ids: set[str] = set()
        for normalized_row in normalized_rows:
            row_codes = set(extract_requirement_codes_from_text(normalized_row.get("requirement_code", "")))
            normalized_codes.update(row_codes)
            if row_codes.intersection(inventory_codes):
                property_id = normalized_row.get("source_property_id", "").strip()
                if property_id and property_id != "-":
                    normalized_property_ids.add(property_id)
        missing_codes = [code for code in inventory_codes if code not in normalized_codes]
        if missing_codes or len(normalized_property_ids) < len(inventory_codes):
            source_row_code_mismatches.append(
                (
                    f"{source_row_id}:inventory_codes={len(inventory_codes)};"
                    f"normalized_property_ids={len(normalized_property_ids)};"
                    f"missing_codes={', '.join(missing_codes[:12]) or '-'}"
                )
            )

    if source_rows_with_many_codes and extract_markdown_section(content, "Source Row Completeness Matrix") is None:
        findings.append(
            Finding(
                id="source-row-completeness-matrix-missing",
                severity="warning",
                category="traceability",
                title="Source rows with multiple requirement codes have no completeness matrix",
                details=(
                    "When one source row contains multiple GSR/REQ codes, writer must prove that each code was split "
                    "into an explicit normalized property, ATOM-* or GAP-* before test design."
                ),
                path=display_path,
                evidence=source_rows_with_many_codes[:20],
                recommended_action=(
                    "Add `## Source Row Completeness Matrix` with source_row_id, source_requirement_codes, "
                    "normalized_property_ids, linked_atoms, gap_ids and coverage_decision."
                ),
            )
        )

    has_embedded_dictionary_inventory = extract_markdown_section(content, "Dictionary Inventory") is not None
    sibling_dictionary_inventory = path.parent / DICTIONARY_INVENTORY_NAME
    if (
        dictionary_source_rows
        and path.name != "source-normalization-diagnostic.md"
        and not has_embedded_dictionary_inventory
        and not sibling_dictionary_inventory.is_file()
    ):
        findings.append(
            Finding(
                id="dictionary-inventory-missing-for-source-normalization",
                severity="warning",
                category="test-design",
                title="Dictionary-source normalization rows have no Dictionary Inventory",
                details=(
                    "When Source Table Normalization contains dictionary/reference-list properties, writer must "
                    "extract the referenced support/source dictionary into dictionary-inventory.md before TDDT, "
                    "plan and TC writing."
                ),
                path=display_path,
                evidence=dictionary_source_rows[:20],
                recommended_action=(
                    "Create `dictionary-inventory.md` with DICT-* rows for the referenced dictionaries, or link a "
                    "source-specific GAP-* if the dictionary cannot be extracted."
                ),
            )
        )

    if missing_property_ids:
        findings.append(
            Finding(
                id="source-normalization-missing-property-id",
                severity="warning",
                category="traceability",
                title="Source Table Normalization rows have no source_property_id",
                details=(
                    "`source_property_id` is the stable identity of one extracted source property. Without it, "
                    "reviewer cannot prove that a multi-rule source row was decomposed instead of compressed."
                ),
                path=display_path,
                evidence=missing_property_ids[:20],
                recommended_action=(
                    "Add `source_property_id` values such as `SRC-003.P01`, `SRC-003.P02` and link each one to "
                    "exactly one atomic rule, ATOM-* or GAP-*."
                ),
            )
        )
    if duplicate_property_ids:
        findings.append(
            Finding(
                id="source-normalization-duplicate-property-id",
                severity="warning",
                category="traceability",
                title="Source Table Normalization reuses source_property_id values",
                details="Each normalized source property must have a unique source_property_id.",
                path=display_path,
                evidence=duplicate_property_ids[:20],
                recommended_action="Give each normalization row a unique source_property_id.",
            )
        )
    if multiple_gsr_rows:
        findings.append(
            Finding(
                id="source-normalization-row-has-multiple-gsr",
                severity="warning",
                category="atomarity",
                title="Source Table Normalization rows still combine multiple requirement codes",
                details=(
                    "A normalized property row should not carry several GSR/REQ codes when those codes can pass/fail "
                    "independently. This usually creates one broad ATOM-* and false coverage."
                ),
                path=display_path,
                evidence=multiple_gsr_rows[:20],
                recommended_action=(
                    "Split the row into one source_property_id per independent GSR/REQ assertion, or route "
                    "unobservable/ambiguous assertions to GAP-*."
                ),
            )
        )
    if source_row_code_mismatches:
        findings.append(
            Finding(
                id="source-row-gsr-count-mismatch",
                severity="warning",
                category="traceability",
                title="Source row requirement codes are not preserved as distinct normalized properties",
                details=(
                    "Every in-scope source row requirement code must be represented by a distinct normalized property "
                    "when the codes describe independent assertions."
                ),
                path=display_path,
                evidence=source_row_code_mismatches[:20],
                recommended_action=(
                    "Compare Source Row Inventory with Source Table Normalization and add missing `source_property_id` "
                    "rows before building ledger and TC."
                ),
            )
        )
    if unmapped_property_rows:
        findings.append(
            Finding(
                id="source-normalization-unmapped-property",
                severity="warning",
                category="traceability",
                title="Source Table Normalization rows are not mapped to ATOM-* or GAP-*",
                details="Each normalized source property must become explicit coverage or an explicit gap.",
                path=display_path,
                evidence=unmapped_property_rows[:20],
                recommended_action="Fill linked_atoms or gap_id for every normalized property row.",
            )
        )
    if missing_ledger_gap_atoms:
        findings.append(
            Finding(
                id="source-table-normalization-missing-ledger-gap-atom",
                severity="warning",
                category="traceability",
                title="Source Table Normalization misses ledger GAP/unclear atoms",
                details=(
                    "Every Atomic Requirements Ledger row with coverage_status = gap/unclear and a real GAP-* "
                    "must be traceable back to Source Table Normalization through linked_atoms or the same gap_id. "
                    "Otherwise the gap can disappear from source decomposition while remaining in the ledger."
                ),
                path=display_path,
                evidence=missing_ledger_gap_atoms[:20],
                recommended_action=(
                    "Add the missing normalized source row, link the atom in linked_atoms, or carry the same GAP-* "
                    "on the matching source_property_id."
                ),
            )
        )
    if artificial_numeric_property_rows:
        findings.append(
            Finding(
                id="source-normalization-artificial-numeric-property-type",
                severity="warning",
                category="test-design",
                title="Source Table Normalization uses artificial numeric property types",
                details=(
                    "Invalid numeric classes are not separate source property types. The source property must remain "
                    "`numeric-format`; invalid classes such as letters, spaces, special characters, decimal separators "
                    "and signs belong in Coverage Obligation Table rows mapped to TC-* or GAP-*."
                ),
                path=display_path,
                evidence=artificial_numeric_property_rows[:20],
                recommended_action=(
                    "Replace artificial properties such as `numeric-format-invalid`, `numeric-negative` or "
                    "`non-digit-rejection` with the original `numeric-format` source_property_id and expand "
                    "class-level obligations downstream."
                ),
            )
        )

    if low_conf_without_gap:
        findings.append(
            Finding(
                id="source-table-normalization-low-confidence-without-gap",
                severity="warning",
                category="traceability",
                title="Low-confidence source normalization rows are not linked to GAP-*",
                details="Rows with confidence = low or unclear cannot become covered atoms without an explicit GAP-*.",
                path=display_path,
                evidence=low_conf_without_gap[:20],
                recommended_action="Add GAP-* links or raise confidence only after the row is cleanly confirmed from source.",
            )
        )
    if residue_rows:
        findings.append(
            Finding(
                id="source-table-normalization-residue-smell",
                severity="warning",
                category="traceability",
                title="Source Table Normalization still contains table extraction residue",
                details="Normalization rows must remove table headers, neighboring fields and page/table artifacts before ledger creation.",
                path=display_path,
                evidence=residue_rows[:20],
                recommended_action="Clean the affected normalization rows or mark them low-confidence with GAP-*.",
            )
        )
    if combined_rows:
        findings.append(
            Finding(
                id="source-normalization-combined-property-smell",
                severity="warning",
                category="atomarity",
                title="Source Table Normalization rows combine multiple properties",
                details=(
                    "One normalization row should contain one property, condition or expected behavior. "
                    "Combined phrases such as requiredness+format or condition=true/false usually produce compressed atoms."
                ),
                path=display_path,
                evidence=combined_rows[:20],
                recommended_action=(
                    "Split affected normalization rows into separate rows before creating ledger, design plan and TC. "
                    "If the source is ambiguous, create GAP-* instead of covered atoms."
                ),
            )
        )
    if combined_property_class_rows:
        findings.append(
            Finding(
                id="source-normalization-combined-property-class-smell",
                severity="warning",
                category="atomarity",
                title="Source Table Normalization rows combine different property classes",
                details=(
                    "One normalized source property must represent one semantic property class. Rows that combine "
                    "dictionary/reference source, min boundary, max boundary, format, visibility, requiredness, "
                    "editability or integration behavior hide independent test-design decisions even when they use "
                    "one requirement code or are routed to GAP-*."
                ),
                path=display_path,
                evidence=combined_property_class_rows[:20],
                recommended_action=(
                    "Split affected rows into separate `source_property_id` values, for example "
                    "`dictionary-source`, `min-boundary` and `max-boundary`, then map each row to ATOM-* or GAP-*."
                ),
            )
        )
    if dictionary_misclassified_rows:
        findings.append(
            Finding(
                id="source-normalization-dictionary-misclassified-smell",
                severity="warning",
                category="test-design",
                title="Reference-list source rows are classified as non-dictionary properties",
                details=(
                    "When a normalized row says a field is reference-list/dictionary-backed, test design must either "
                    "use the confirmed support dictionary, assert the closed active value set, or create a source-specific GAP. "
                    "Classifying it as structural context hides list coverage."
                ),
                path=display_path,
                evidence=dictionary_misclassified_rows[:20],
                recommended_action=(
                    "Reclassify affected rows as dictionary/reference-list properties and add closed-set obligations, "
                    "or link a GAP explaining why the support dictionary cannot be used."
                ),
            )
        )
    if unknown_atoms:
        findings.append(
            Finding(
                id="source-table-normalization-unknown-atom-id",
                severity="warning",
                category="traceability",
                title="Source Table Normalization references unknown atom ids",
                details="linked_atoms values should point to ATOM-* rows declared in Atomic Requirements Ledger.",
                path=display_path,
                evidence=unknown_atoms[:20],
                recommended_action="Update linked_atoms to existing ATOM-* ids or create the missing ledger rows.",
            )
        )

    has_warnings = any(finding.severity == "warning" for finding in findings)
    checks.append(
        Check(
            "source-table-normalization",
            "warn" if has_warnings else "pass",
            "Source Table Normalization has issues." if has_warnings else "Source Table Normalization contract passed.",
            display_path,
        )
    )
    return findings, checks


def validate_source_normalization_diagnostic(path: Path, root: Path) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    content = path.read_text(encoding="utf-8")

    missing_sections = sorted(
        section_title
        for section_title in SOURCE_NORMALIZATION_DIAGNOSTIC_REQUIRED_SECTIONS
        if extract_markdown_section(content, section_title) is None
    )
    if missing_sections:
        findings.append(
            Finding(
                id="source-normalization-diagnostic-missing-sections",
                severity="warning",
                category="traceability",
                title="Source normalization diagnostic misses required sections",
                details=(
                    "A diagnostic normalization artifact must be self-contained enough to prove source-row split "
                    "quality before writer creates ledger and TC-* coverage."
                ),
                path=display_path,
                evidence=[f"missing={', '.join(missing_sections)}"],
                recommended_action=(
                    "Add `Source Row Completeness Matrix`, `Source Table Normalization` and `Self-check` sections."
                ),
            )
        )

    normalization_findings, normalization_checks = validate_source_table_normalization(content, path, root)
    findings.extend(normalization_findings)
    checks.extend(normalization_checks)

    matrix_section = extract_markdown_section(content, "Source Row Completeness Matrix")
    matrix_header, matrix_rows = parsed_section_table_rows(content, "Source Row Completeness Matrix")
    matrix_property_ids: set[str] = set()
    matrix_source_ids: set[str] = set()
    matrix_requirement_codes_by_source: dict[str, set[str]] = defaultdict(set)
    placeholder_gap_rows: list[str] = []
    invalid_diagnostic_atom_status_rows: list[str] = []
    linked_atom_status_mismatch_rows: list[str] = []
    if matrix_section is not None and not matrix_rows:
        findings.append(
            Finding(
                id="source-normalization-diagnostic-completeness-matrix-no-table",
                severity="warning",
                category="traceability",
                title="Source Row Completeness Matrix has no parseable table",
                details="The diagnostic must expose which source rows were split into which normalized properties.",
                path=display_path,
                evidence=[],
                recommended_action="Rewrite the matrix as a Markdown table with canonical columns.",
            )
        )
    if matrix_rows:
        missing_columns = sorted(
            SOURCE_NORMALIZATION_DIAGNOSTIC_COMPLETENESS_MATRIX_REQUIRED_COLUMNS - set(matrix_header)
        )
        if missing_columns:
            findings.append(
                Finding(
                    id="source-normalization-diagnostic-completeness-matrix-missing-columns",
                    severity="warning",
                    category="traceability",
                    title="Source Row Completeness Matrix misses required columns",
                    details=(
                        "The completeness matrix must prove the relationship between source rows, source "
                        "requirement codes, normalized property ids, atoms and gaps."
                    ),
                    path=display_path,
                    evidence=[f"missing={', '.join(missing_columns)}", f"columns={', '.join(matrix_header[:12])}"],
                    recommended_action="Use the canonical Source Row Completeness Matrix columns.",
                )
        )
        for row in matrix_rows:
            source_row_id = normalize_markdown_field_value(row.get("source_row_id", "")) or "row"
            matrix_source_ids.add(source_row_id)
            matrix_requirement_codes_by_source[source_row_id].update(
                extract_requirement_codes_from_text(row.get("source_requirement_codes", ""))
            )
            matrix_property_ids.update(SOURCE_PROPERTY_ID_RE.findall(row.get("normalized_property_ids", "")))
            gap_ids = row.get("gap_ids", "")
            if DIAGNOSTIC_PLACEHOLDER_GAP_RE.search(gap_ids):
                placeholder_gap_rows.append(f"{source_row_id}:gap_ids={gap_ids}")
            diagnostic_atom_status = row.get("diagnostic_atom_status", "").strip().strip("`").lower()
            if diagnostic_atom_status not in {"not-created", "created", "not-applicable", "n/a"}:
                invalid_diagnostic_atom_status_rows.append(
                    f"{source_row_id}:diagnostic_atom_status={diagnostic_atom_status or '-'}"
                )
            linked_atoms = row.get("linked_atoms", "").strip()
            if (
                linked_atoms in {"", "-"}
                and diagnostic_atom_status not in {"not-created", "not-applicable", "n/a"}
            ):
                linked_atom_status_mismatch_rows.append(
                    f"{source_row_id}:linked_atoms={linked_atoms or '-'};diagnostic_atom_status={diagnostic_atom_status or '-'}"
                )

    _, normalization_rows = parsed_section_table_rows(content, "Source Table Normalization")
    normalization_source_ids: set[str] = set()
    normalization_requirement_codes_by_source: dict[str, set[str]] = defaultdict(set)
    normalization_property_ids = {
        row.get("source_property_id", "").strip()
        for row in normalization_rows
        if row.get("source_property_id", "").strip() not in {"", "-"}
    }
    normalization_header, _ = parsed_section_table_rows(content, "Source Table Normalization")
    missing_normalization_columns = sorted(
        SOURCE_NORMALIZATION_DIAGNOSTIC_NORMALIZATION_REQUIRED_COLUMNS - set(normalization_header)
    )
    if normalization_rows and missing_normalization_columns:
        findings.append(
            Finding(
                id="source-normalization-diagnostic-missing-source-fragment-columns",
                severity="warning",
                category="traceability",
                title="Source normalization diagnostic misses source fragment columns",
                details=(
                    "A diagnostic row must expose the exact source column and source text fragment it was normalized from. "
                    "Otherwise reviewer cannot tell whether behavior was copied from source or reconstructed from memory."
                ),
                path=display_path,
                evidence=[
                    f"missing={', '.join(missing_normalization_columns)}",
                    f"columns={', '.join(normalization_header[:16])}",
                ],
                recommended_action="Add `source_column` and `source_text_fragment` columns to Source Table Normalization.",
            )
        )

    missing_source_fragment_rows: list[str] = []
    placeholder_normalization_gap_rows: list[str] = []
    gsr_only_expected_rows: list[str] = []
    integration_without_observability_rows: list[str] = []
    for row in normalization_rows:
        source_row_id = normalize_markdown_field_value(row.get("source_row_id", "")) or "row"
        normalization_source_ids.add(source_row_id)
        normalization_requirement_codes_by_source[source_row_id].update(
            extract_requirement_codes_from_text(row.get("requirement_code", ""))
        )
        property_ref = row.get("source_property_id", "").strip() or "-"
        source_column = row.get("source_column", "").strip()
        source_fragment = row.get("source_text_fragment", "").strip()
        if not missing_normalization_columns and (not source_column or not source_fragment or source_fragment == "-"):
            missing_source_fragment_rows.append(
                f"{source_row_id}:{property_ref}:source_column={source_column or '-'};source_text_fragment={source_fragment or '-'}"
            )

        gap_id = row.get("gap_id", "").strip()
        if DIAGNOSTIC_PLACEHOLDER_GAP_RE.search(gap_id):
            placeholder_normalization_gap_rows.append(f"{source_row_id}:{property_ref}:gap_id={gap_id}")

        expected_behavior = row.get("expected_behavior", "").strip()
        if expected_behavior and GSR_ONLY_EXPECTED_BEHAVIOR_RE.search(expected_behavior):
            gsr_only_expected_rows.append(f"{source_row_id}:{property_ref}:{expected_behavior[:160]}")

        integration_text = " | ".join(
            row.get(field, "")
            for field in ("property", "condition", "expected_behavior")
            if row.get(field)
        )
        if (
            integration_text
            and INTEGRATION_OR_INTERNAL_PROPERTY_RE.search(integration_text)
            and not real_gap_ids(gap_id)
            and not OBSERVABLE_BEHAVIOR_RE.search(expected_behavior)
        ):
            integration_without_observability_rows.append(
                f"{source_row_id}:{property_ref}:gap_id={gap_id or '-'}:{integration_text[:160]}"
            )

    unknown_matrix_property_ids = sorted(matrix_property_ids - normalization_property_ids)
    missing_from_matrix = sorted(normalization_property_ids - matrix_property_ids) if matrix_rows else []
    inventory_path = path.with_name("source-row-inventory.md")
    missing_inventory_rows: list[str] = []
    missing_inventory_codes: list[str] = []
    if inventory_path.exists():
        try:
            inventory_content = inventory_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            inventory_content = ""
        for index, inventory_row in enumerate(parsed_source_row_inventory_rows(inventory_content), start=2):
            source_row_id = normalize_markdown_field_value(inventory_row.get("source_row_id", "")) or f"row {index}"
            in_scope = normalize_markdown_field_value(inventory_row.get("in_scope", "")).lower()
            if in_scope not in {"yes", "unclear"}:
                continue
            missing_parts: list[str] = []
            if source_row_id not in matrix_source_ids:
                missing_parts.append("matrix")
            if source_row_id not in normalization_source_ids:
                missing_parts.append("normalization")
            if missing_parts:
                missing_inventory_rows.append(f"{source_row_id}:missing={','.join(missing_parts)}")

            inventory_codes = set(extract_requirement_codes_from_text(inventory_row.get("requirement_codes", "")))
            if inventory_codes:
                missing_matrix_codes = sorted(inventory_codes - matrix_requirement_codes_by_source[source_row_id])
                missing_normalization_codes = sorted(
                    inventory_codes - normalization_requirement_codes_by_source[source_row_id]
                )
                if missing_matrix_codes or missing_normalization_codes:
                    missing_inventory_codes.append(
                        (
                            f"{source_row_id}:"
                            f"missing_matrix={'; '.join(missing_matrix_codes) or '-'};"
                            f"missing_normalization={'; '.join(missing_normalization_codes) or '-'}"
                        )
                    )
    if placeholder_gap_rows or placeholder_normalization_gap_rows:
        findings.append(
            Finding(
                id="source-normalization-diagnostic-placeholder-gap-used",
                severity="warning",
                category="traceability",
                title="Source normalization diagnostic uses placeholder GAP-900 as a coverage gap",
                details=(
                    "`GAP-900` must not be used as a real gap. Diagnostic runs should record atom absence with "
                    "`diagnostic_atom_status = not-created`; functional uncertainty must use a real GAP-* from the scope."
                ),
                path=display_path,
                evidence=[*placeholder_gap_rows[:10], *placeholder_normalization_gap_rows[:10]],
                recommended_action=(
                    "Remove `GAP-900` from gap columns. Use `diagnostic_atom_status` for the no-ATOM diagnostic state "
                    "and keep only functional GAP-* values in `gap_ids` / `gap_id`."
                ),
            )
        )
    if invalid_diagnostic_atom_status_rows:
        findings.append(
            Finding(
                id="source-normalization-diagnostic-invalid-atom-status",
                severity="warning",
                category="traceability",
                title="Source Row Completeness Matrix has invalid diagnostic atom status",
                details="Diagnostic runs must state whether atoms were intentionally not created.",
                path=display_path,
                evidence=invalid_diagnostic_atom_status_rows[:20],
                recommended_action="Use `diagnostic_atom_status` values `not-created`, `created`, or `not-applicable`.",
            )
        )
    if linked_atom_status_mismatch_rows:
        findings.append(
            Finding(
                id="source-normalization-diagnostic-linked-atom-status-mismatch",
                severity="warning",
                category="traceability",
                title="Source Row Completeness Matrix does not explain missing linked atoms",
                details="When linked_atoms is empty in a diagnostic-only run, the matrix must explicitly say atoms were not created.",
                path=display_path,
                evidence=linked_atom_status_mismatch_rows[:20],
                recommended_action="Set `diagnostic_atom_status = not-created` for rows where linked_atoms is `-`.",
            )
        )
    if missing_source_fragment_rows:
        findings.append(
            Finding(
                id="source-normalization-diagnostic-missing-source-fragment",
                severity="warning",
                category="traceability",
                title="Source normalization diagnostic rows miss source text fragments",
                details="Each diagnostic normalization row must point to the source column and exact text fragment it normalized.",
                path=display_path,
                evidence=missing_source_fragment_rows[:20],
                recommended_action="Fill `source_column` and `source_text_fragment` for every Source Table Normalization row.",
            )
        )
    if gsr_only_expected_rows:
        findings.append(
            Finding(
                id="source-normalization-diagnostic-gsr-only-expected-behavior",
                severity="warning",
                category="expected-result",
                title="Source normalization diagnostic uses GSR reference instead of expected behavior",
                details=(
                    "`expected_behavior` must restate the observable source behavior itself. "
                    "A phrase like `follows GSR 10` preserves a code but loses the test oracle."
                ),
                path=display_path,
                evidence=gsr_only_expected_rows[:20],
                recommended_action="Replace GSR-only wording with the concrete behavior from the source row.",
            )
        )
    if integration_without_observability_rows:
        findings.append(
            Finding(
                id="source-normalization-diagnostic-integration-without-observability-decision",
                severity="warning",
                category="expected-result",
                title="Source normalization diagnostic treats integration/internal behavior as directly testable",
                details=(
                    "Integration, API, model, DB, async and queue effects need either an observable UI/artifact oracle "
                    "or a real GAP-* decision. A diagnostic placeholder is not enough."
                ),
                path=display_path,
                evidence=integration_without_observability_rows[:20],
                recommended_action=(
                    "Split observable behavior from internal effects. Link internal effects to a real GAP-* unless the "
                    "source provides a visible artifact, log, API, DB or queue evidence rule."
                ),
            )
        )
    if unknown_matrix_property_ids:
        findings.append(
            Finding(
                id="source-normalization-diagnostic-matrix-unknown-property-id",
                severity="warning",
                category="traceability",
                title="Source Row Completeness Matrix references unknown source_property_id values",
                details="Every normalized_property_ids value must exist in Source Table Normalization.",
                path=display_path,
                evidence=unknown_matrix_property_ids[:20],
                recommended_action="Fix normalized_property_ids or add the missing Source Table Normalization rows.",
            )
        )
    if missing_from_matrix:
        findings.append(
            Finding(
                id="source-normalization-diagnostic-property-missing-from-matrix",
                severity="warning",
                category="traceability",
                title="Source Table Normalization rows are missing from completeness matrix",
                details="Diagnostic normalization must prove every normalized property in the completeness matrix.",
                path=display_path,
                evidence=missing_from_matrix[:20],
                recommended_action="Add every Source Table Normalization source_property_id to the matrix.",
            )
        )
    if missing_inventory_rows:
        findings.append(
            Finding(
                id="source-normalization-diagnostic-missing-inventory-row",
                severity="warning",
                category="traceability",
                title="Source normalization diagnostic does not cover all in-scope inventory rows",
                details=(
                    "When a source-normalization diagnostic sits next to source-row-inventory.md, it is a handoff "
                    "input for writer and must normalize every inventory row with in_scope = yes/unclear, not only "
                    "high-risk or gap rows."
                ),
                path=display_path,
                evidence=missing_inventory_rows[:30],
                recommended_action=(
                    "Add every in-scope/unclear source_row_id from source-row-inventory.md to both Source Row "
                    "Completeness Matrix and Source Table Normalization, or mark it out of scope in the inventory."
                ),
            )
        )
    if missing_inventory_codes:
        findings.append(
            Finding(
                id="source-normalization-diagnostic-inventory-code-mismatch",
                severity="warning",
                category="traceability",
                title="Source normalization diagnostic loses requirement codes from inventory",
                details=(
                    "Every GSR/REQ code on an in-scope/unclear source-row-inventory.md row must remain attached to "
                    "the same source_row_id in the completeness matrix and at least one normalized property row."
                ),
                path=display_path,
                evidence=missing_inventory_codes[:30],
                recommended_action=(
                    "Copy the missing requirement codes into Source Row Completeness Matrix and split them into "
                    "source_property_id rows, or link the non-testable code to a real GAP-* without dropping it."
                ),
            )
        )

    self_check_section = extract_markdown_section(content, "Self-check") or ""
    if re.search(r"\b(?:fail|failed|blocked|needs[- ]rewrite)\b|не\s+пройден|провален", self_check_section, flags=re.IGNORECASE):
        findings.append(
            Finding(
                id="source-normalization-diagnostic-self-check-failed",
                severity="warning",
                category="traceability",
                title="Source normalization diagnostic self-check is failed",
                details="A failed diagnostic self-check must block writer progression to ledger and TC generation.",
                path=display_path,
                evidence=[self_check_section.strip()[:500]],
                recommended_action="Fix the diagnostic normalization or keep the workflow blocked before writer-pass.",
            )
        )

    has_warnings = any(finding.severity == "warning" for finding in findings)
    checks.append(
        Check(
            "source-normalization-diagnostic",
            "warn" if has_warnings else "pass",
            "Source normalization diagnostic has issues." if has_warnings else "Source normalization diagnostic passed.",
            display_path,
        )
    )
    return findings, checks


def source_row_inventory_required(content: str) -> bool:
    return (
        "Source Table Normalization" in content
        or "Package Test Design Plan" in content
        or "Internal Work Package Coverage" in content
        or re.search(r"\bpackage_id\b", content, flags=re.IGNORECASE) is not None
    )


def parsed_source_row_inventory_rows(content: str) -> list[dict[str, str]]:
    normalized_content = collapse_redundant_section_heading(content, "Source Row Inventory")
    if re.search(r"^#\s+Source Row Inventory\s*$", normalized_content, flags=re.MULTILINE):
        normalized_content = re.sub(
            r"^#\s+Source Row Inventory\s*$",
            "## Source Row Inventory",
            normalized_content,
            count=1,
            flags=re.MULTILINE,
        )
    elif extract_markdown_section(normalized_content, "Source Row Inventory") is None:
        normalized_content = "## Source Row Inventory\n\n" + normalized_content

    section = extract_markdown_section(normalized_content, "Source Row Inventory")
    if section is None:
        return []
    table_rows = markdown_table_rows_from_text(section)
    if not table_rows:
        return []

    header = normalize_table_header(table_rows[0])
    parsed_rows: list[dict[str, str]] = []
    for raw_row in table_rows[1:]:
        row: dict[str, str] = {}
        for index, column_name in enumerate(header):
            row[column_name] = raw_row[index].strip().strip("`") if index < len(raw_row) else ""
        parsed_rows.append(row)
    return parsed_rows


def source_row_inventory_required_source_ids(content: str) -> set[str]:
    source_ids: set[str] = set()
    for index, row in enumerate(parsed_source_row_inventory_rows(content), start=2):
        source_row_id = row.get("source_row_id", "").strip() or f"row {index}"
        in_scope = row.get("in_scope", "").strip().strip("`").lower()
        if in_scope in {"yes", "unclear"}:
            source_ids.add(source_row_id)
    return source_ids


def source_row_inventory_all_source_ids(content: str) -> set[str]:
    source_ids: set[str] = set()
    for index, row in enumerate(parsed_source_row_inventory_rows(content), start=2):
        source_row_id = row.get("source_row_id", "").strip() or f"row {index}"
        source_ids.add(source_row_id)
    return source_ids


def validate_source_row_inventory(
    content: str,
    path: Path,
    root: Path,
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    required = source_row_inventory_required(content)
    section = extract_markdown_section(content, "Source Row Inventory")

    if section is None:
        if required:
            findings.append(
                Finding(
                    id="source-row-inventory-missing",
                    severity="warning",
                    category="traceability",
                    title="Package-based test-case file has no Source Row Inventory",
                    details=(
                        "Writer output must inventory every source row in the confirmed scope before normalization, "
                        "so a source row cannot silently disappear from the ledger and TC coverage."
                    ),
                    path=display_path,
                    evidence=[],
                    recommended_action=(
                        "Add `## Source Row Inventory` with source_row_id, package_id, field_or_action, "
                        "source_ref, requirement_codes, in_scope and mapped_atom_or_gap."
                    ),
                )
            )
            checks.append(Check("source-row-inventory", "warn", "Source Row Inventory is missing.", display_path))
        else:
            checks.append(Check("source-row-inventory", "pass", "Source Row Inventory is not required for this file.", display_path))
        return findings, checks

    table_rows = markdown_table_rows_from_text(section)
    if not table_rows:
        findings.append(
            Finding(
                id="source-row-inventory-no-table",
                severity="warning",
                category="traceability",
                title="Source Row Inventory has no Markdown table",
                details="The inventory section exists but has no parseable table.",
                path=display_path,
                evidence=[],
                recommended_action="Use the canonical Source Row Inventory table.",
            )
        )
        checks.append(Check("source-row-inventory", "warn", "Source Row Inventory table is missing.", display_path))
        return findings, checks

    header = normalize_table_header(table_rows[0])
    missing_columns = sorted(SOURCE_ROW_INVENTORY_REQUIRED_COLUMNS - set(header))
    if missing_columns:
        findings.append(
            Finding(
                id="source-row-inventory-missing-columns",
                severity="warning",
                category="traceability",
                title="Source Row Inventory misses required columns",
                details="The inventory must expose source row identity, package, scope decision and ATOM/GAP mapping.",
                path=display_path,
                evidence=[f"missing={', '.join(missing_columns)}", f"columns={', '.join(header[:12])}"],
                recommended_action="Rewrite the table with the canonical columns from source-row-inventory-format.md.",
            )
        )

    parsed_rows = parsed_source_row_inventory_rows(content)

    ledger_atom_ids = atomic_requirement_ledger_atom_ids(content)
    inventory_source_ids: set[str] = set()
    missing_mapping: list[str] = []
    unknown_atom_refs: list[str] = []
    invalid_in_scope: list[str] = []
    for index, row in enumerate(parsed_rows, start=2):
        source_row_id = row.get("source_row_id", "").strip() or f"row {index}"
        inventory_source_ids.add(source_row_id)
        in_scope = row.get("in_scope", "").strip().strip("`").lower()
        mapped = row.get("mapped_atom_or_gap", "")
        if in_scope and in_scope not in {"yes", "no", "unclear", "out-of-scope"}:
            invalid_in_scope.append(f"{source_row_id}:in_scope={in_scope}")
        if in_scope == "yes" and not (extract_any_atom_ids_from_text(mapped) or extract_gap_ids_from_text(mapped)):
            missing_mapping.append(f"{source_row_id}:mapped_atom_or_gap={mapped or '-'}")
        for atom_id in extract_any_atom_ids_from_text(mapped):
            if ledger_atom_ids and atom_id not in ledger_atom_ids:
                unknown_atom_refs.append(f"{source_row_id}:{atom_id}")

    normalization_section = extract_markdown_section(content, "Source Table Normalization")
    normalization_missing_inventory: list[str] = []
    if normalization_section:
        normalization_rows = markdown_table_rows_from_text(normalization_section)
        if normalization_rows:
            normalization_header = normalize_table_header(normalization_rows[0])
            if "source_row_id" in normalization_header:
                source_row_index = normalization_header.index("source_row_id")
                for row in normalization_rows[1:]:
                    source_row_id = row[source_row_index].strip().strip("`") if source_row_index < len(row) else ""
                    if source_row_id and source_row_id not in inventory_source_ids:
                        normalization_missing_inventory.append(source_row_id)

    if invalid_in_scope:
        findings.append(
            Finding(
                id="source-row-inventory-invalid-in-scope",
                severity="warning",
                category="traceability",
                title="Source Row Inventory uses noncanonical in_scope values",
                details="in_scope must be yes, no, unclear or out-of-scope.",
                path=display_path,
                evidence=invalid_in_scope[:20],
                recommended_action="Normalize in_scope values and keep ambiguous rows linked to GAP-*.",
            )
        )
    if missing_mapping:
        findings.append(
            Finding(
                id="source-row-inventory-in-scope-row-without-atom-or-gap",
                severity="warning",
                category="traceability",
                title="In-scope source rows are not mapped to ATOM-* or GAP-*",
                details="Every in-scope source row must become either explicit coverage or an explicit gap.",
                path=display_path,
                evidence=missing_mapping[:20],
                recommended_action="Map each in-scope source row to ATOM-* or GAP-* before handing off to reviewer.",
            )
        )
    if unknown_atom_refs:
        findings.append(
            Finding(
                id="source-row-inventory-unknown-atom-id",
                severity="warning",
                category="traceability",
                title="Source Row Inventory references unknown atom ids",
                details="mapped_atom_or_gap values should point to ATOM-* rows declared in Atomic Requirements Ledger.",
                path=display_path,
                evidence=unknown_atom_refs[:20],
                recommended_action="Update mapped_atom_or_gap to existing ATOM-* ids or create the missing ledger rows.",
            )
        )
    if normalization_missing_inventory:
        findings.append(
            Finding(
                id="source-row-inventory-misses-normalized-source-row",
                severity="warning",
                category="traceability",
                title="Source Table Normalization contains rows absent from Source Row Inventory",
                details="The inventory should be the source completeness checklist; normalization rows must not appear outside it.",
                path=display_path,
                evidence=sorted(set(normalization_missing_inventory))[:20],
                recommended_action="Add missing source rows to Source Row Inventory or correct the normalization source_row_id.",
            )
        )

    has_warnings = any(finding.id.startswith("source-row-inventory") for finding in findings)
    checks.append(
        Check(
            "source-row-inventory",
            "warn" if has_warnings else "pass",
            "Source Row Inventory has issues." if has_warnings else "Source Row Inventory contract passed.",
            display_path,
        )
    )
    return findings, checks


def validate_atomic_ledger_structure(
    content: str,
    path: Path,
    root: Path,
    *,
    structural_severity: str,
    blocks: list[tuple[str, str]],
    known_test_case_ids: set[str] | None = None,
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    header, rows = parsed_atomic_requirement_ledger_rows(content)
    if not header and not rows:
        return findings, checks

    if "atom_id" not in header:
        findings.append(
            Finding(
                id="test-case-ledger-missing-atom-id-column",
                severity=structural_severity,
                category="traceability",
                title="Atomic Requirements Ledger has no atom_id column",
                details="Canonical test-case files need stable ATOM-* ids for review findings and coverage closure.",
                path=display_path,
                evidence=[f"columns={', '.join(header[:12])}"],
                recommended_action="Add atom_id to the Atomic Requirements Ledger.",
            )
        )
        checks.append(Check("test-case-atomic-ledger", "warn" if structural_severity == "warning" else "pass", "Ledger atom_id column missing.", display_path))
        return findings, checks

    atom_ids: list[str] = []
    invalid_atom_ids: list[str] = []
    invalid_statuses: list[str] = []
    covered_without_tc: list[str] = []
    unknown_test_case_ids: list[str] = []
    missing_package_rows: list[str] = []

    tc_text_by_id = {test_case_id: block for test_case_id, block in blocks}
    atoms_referenced_by_tc: set[str] = set()
    for _, block in blocks:
        atoms_referenced_by_tc.update(extract_any_atom_ids_from_text(block))

    has_package_contract = "package_id" in header or "Internal Work Package Coverage" in content
    has_covered_by_tc = "covered_by_tc" in header
    all_test_case_ids = known_test_case_ids or set(tc_text_by_id)

    for row_number, row in enumerate(rows, start=2):
        atom_id = row.get("atom_id", "").strip()
        if atom_id:
            atom_ids.append(atom_id)
        row_label = f"row {row_number}:{atom_id or '<missing>'}"
        if not atom_id or not is_valid_atom_id_value(atom_id):
            invalid_atom_ids.append(row_label)

        status = row.get("coverage_status", "").strip().lower()
        if status and status not in ALLOWED_COVERAGE_STATUSES:
            invalid_statuses.append(f"{row_label}:coverage_status={status}")

        if has_package_contract and not meaningful_matrix_value(row.get("package_id", "")):
            missing_package_rows.append(row_label)

        covered_refs: list[str] = []
        if has_covered_by_tc:
            covered_refs = extract_test_case_ids_from_text(row.get("covered_by_tc", ""))
            for test_case_id in covered_refs:
                if all_test_case_ids and test_case_id not in all_test_case_ids:
                    unknown_test_case_ids.append(f"{row_label}:{test_case_id}")
        if status == "covered":
            if has_covered_by_tc:
                if not covered_refs:
                    covered_without_tc.append(f"{row_label}:covered_by_tc=-")
            elif atom_id and atom_id not in atoms_referenced_by_tc:
                covered_without_tc.append(f"{row_label}:not referenced by any TC-* block")

    duplicate_atom_ids = [
        atom_id
        for atom_id, count in Counter(atom_ids).items()
        if count > 1
    ]
    if invalid_atom_ids:
        findings.append(
            Finding(
                id="test-case-ledger-invalid-atom-id",
                severity=structural_severity,
                category="traceability",
                title="Atomic Requirements Ledger contains invalid atom ids",
                details="Ledger atom ids must use stable ATOM-* ids or declared scoped *-ATOM-* ids.",
                path=display_path,
                evidence=invalid_atom_ids[:20],
                recommended_action="Rename invalid atom ids to stable ATOM-* values and update all TC/matrix references.",
            )
        )
    if duplicate_atom_ids:
        findings.append(
            Finding(
                id="test-case-ledger-duplicate-atom-id",
                severity=structural_severity,
                category="traceability",
                title="Atomic Requirements Ledger contains duplicate atom ids",
                details="Each atom_id must identify one atomic statement.",
                path=display_path,
                evidence=duplicate_atom_ids[:20],
                recommended_action="Split or rename duplicate atom ids so reviewer findings can target one row.",
            )
        )
    if invalid_statuses:
        findings.append(
            Finding(
                id="test-case-ledger-invalid-coverage-status",
                severity=structural_severity,
                category="traceability",
                title="Atomic Requirements Ledger contains invalid coverage statuses",
                details="coverage_status must be covered, gap, or unclear.",
                path=display_path,
                evidence=invalid_statuses[:20],
                recommended_action="Normalize coverage_status values to covered, gap, or unclear.",
            )
        )
    if covered_without_tc:
        findings.append(
            Finding(
                id="test-case-ledger-covered-without-tc",
                severity=structural_severity,
                category="traceability",
                title="Atomic Requirements Ledger marks atoms covered without TC references",
                details="An atom with coverage_status = covered must be linked to at least one executable TC-* block.",
                path=display_path,
                evidence=covered_without_tc[:20],
                recommended_action="Link each covered atom to a TC-* or change coverage_status to gap/unclear.",
            )
        )
    if unknown_test_case_ids:
        findings.append(
            Finding(
                id="test-case-ledger-unknown-test-case-id",
                severity=structural_severity,
                category="traceability",
                title="Atomic Requirements Ledger references unknown test-case ids",
                details="covered_by_tc values must point to canonical ## TC-* sections.",
                path=display_path,
                evidence=unknown_test_case_ids[:20],
                recommended_action="Create the referenced test cases or update covered_by_tc to existing TC-* ids.",
            )
        )
    if missing_package_rows:
        findings.append(
            Finding(
                id="test-case-ledger-missing-package-id",
                severity=structural_severity,
                category="test-design",
                title="Package-based ledger rows are missing package_id",
                details="When internal work packages are used, every atomic ledger row must carry package_id.",
                path=display_path,
                evidence=missing_package_rows[:20],
                recommended_action="Add package_id to every ledger row or remove the package-based coverage claim.",
            )
        )

    has_blocking = any(finding.severity == "warning" for finding in findings)
    checks.append(
        Check(
            "test-case-atomic-ledger",
            "warn" if has_blocking else "pass",
            "Atomic ledger structural contract has issues." if has_blocking else "Atomic ledger structural contract passed.",
            display_path,
        )
    )
    return findings, checks


def validate_test_case_package_ids(
    content: str,
    path: Path,
    root: Path,
    *,
    structural_severity: str,
    blocks: list[tuple[str, str]],
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    header, _ = parsed_atomic_requirement_ledger_rows(content)
    package_contract_active = "Internal Work Package Coverage" in content or "package_id" in header
    if not package_contract_active or not blocks:
        return findings, checks

    package_id_severity = "warning" if structural_severity == "info" else structural_severity
    missing_package_id = [
        test_case_id
        for test_case_id, block in blocks
        if not re.search(r"(?im)^\*\*package_id:\*\*|package_id\s*=", block)
    ]
    if missing_package_id:
        findings.append(
            Finding(
                id="test-case-missing-package-id",
                severity=package_id_severity,
                category="test-design",
                title="Package-based test-case file has TC blocks without package_id",
                details="When internal work packages are used, every TC-* must identify its package so reviewer can detect cross-package leakage.",
                path=display_path,
                evidence=missing_package_id[:20],
                recommended_action="Add `package_id` to every affected TC-* or remove the package-based coverage claim.",
            )
        )

    checks.append(
        Check(
            "test-case-package-id",
            "warn" if missing_package_id else "pass",
            "Some TC blocks miss package_id." if missing_package_id else "Package id contract passed.",
            display_path,
        )
    )
    return findings, checks


def package_ids_from_test_case_file(content: str) -> set[str]:
    package_ids: set[str] = set()

    package_section = extract_markdown_section(content, "Internal Work Package Coverage")
    if package_section:
        rows = markdown_table_rows_from_text(package_section)
        if rows:
            header = normalize_table_header(rows[0])
            if "package_id" in header:
                package_id_index = header.index("package_id")
                for row in rows[1:]:
                    if package_id_index < len(row):
                        package_id = row[package_id_index].strip().strip("`")
                        if meaningful_matrix_value(package_id):
                            package_ids.add(package_id)

    ledger_header, ledger_rows = parsed_atomic_requirement_ledger_rows(content)
    if "package_id" in ledger_header:
        for row in ledger_rows:
            package_id = row.get("package_id", "").strip().strip("`")
            if meaningful_matrix_value(package_id):
                package_ids.add(package_id)

    return package_ids


PACKAGE_DESIGN_PLAN_REQUIRED_COLUMNS = {
    "design_item_id",
    "package_id",
    "design_dimension",
    "source_ref",
    "linked_atoms",
    "planned_check",
    "check_type",
    "coverage_class",
    "input_class",
    "single_expected_behavior",
    "oracle_source",
    "planned_tc_or_gap",
    "status",
}

GENERIC_PLAN_SMELL_PATTERNS = [
    re.compile(r"проверить\s+требован", flags=re.IGNORECASE),
    re.compile(r"проверить\s+выполнени", flags=re.IGNORECASE),
    re.compile(r"валидн\w+\s*/\s*невалидн", flags=re.IGNORECASE),
    re.compile(r"валидное\s+и\s+невалидное\s+значение", flags=re.IGNORECASE),
    re.compile(r"(?:принима\w*|valid|accepted)[\s\S]{0,120}(?:не\s+принима\w*|отклон\w*|invalid|rejected)", flags=re.IGNORECASE),
    re.compile(r"(?:не\s+принима\w*|отклон\w*|invalid|rejected)[\s\S]{0,120}(?:принима\w*|valid|accepted)", flags=re.IGNORECASE),
    re.compile(r"установить\s+условие", flags=re.IGNORECASE),
    re.compile(r"выполнить\s+действие\s+согласно\s+фт", flags=re.IGNORECASE),
    re.compile(r"видимое\s+состояние\s+после\s+действия\s+соответствует\s+одному\s+наблюдаемому\s+правилу", flags=re.IGNORECASE),
    re.compile(r"поле\s+изменяет,\s*отображает\s+или\s+ограничивает\s+значение\s+без\s+утверждения\s+внутренних\s+эффектов", flags=re.IGNORECASE),
]

GENERIC_GAP_PLAN_ROW_RE = re.compile(
    r"зафиксировать\s+непроверяем\w+\s+поведение(?:\s+[^|]{0,80})?\s+как\s+gap|"
    r"непроверяем\w+\s+поведение[^|]{0,80}\bgap\b|"
    r"record\s+unverifiable\s+behavior[^|]{0,80}\bgap\b|"
    r"unverifiable\s+behavior[^|]{0,80}\bgap\b",
    flags=re.IGNORECASE,
)

EXACT_DIGIT_COUNT_RE = re.compile(
    r"\bexact\s+(\d+)\s+digits?\b|"
    r"(?:ровно|точн(?:о|ое|ых|ая)?)\s+(\d+)\s+цифр",
    flags=re.IGNORECASE,
)
PLAN_DIGIT_BOUNDARY_RE_TEMPLATE = (
    r"\bN\s*{sign}\s*1\b|"
    r"\b{target}\s+digits?\b|"
    r"\b{target}\s+цифр"
)
PLAN_DIGIT_ONLY_RE = re.compile(r"\bdigit[-\s]?only\b|\bdigits?\b|цифр", flags=re.IGNORECASE)
REPEATED_DIGITS_REQUIREMENT_RE = re.compile(
    r"same\s+consecutive\s+digits?|repeated\s+digits?|"
    r"повтор\w+\s+цифр|одинаков\w+\s+(?:подряд|цифр)|"
    r"(?:три|шесть)\s+одинаков\w+",
    flags=re.IGNORECASE,
)
REPEATED_DIGITS_NEGATIVE_PLAN_RE = re.compile(
    r"same\s+consecutive\s+digits?|repeated\s+digits?|"
    r"повтор\w+\s+цифр|одинаков\w+\s+(?:подряд|цифр)|"
    r"(?:три|шесть)\s+одинаков\w+|\b1{3,6}\b",
    flags=re.IGNORECASE,
)

MERGED_PLAN_CHECK_TYPE_RE = re.compile(
    r"\b(?:positive|negative|boundary|format|dependency|integration|async|gap|scenario|action[- ]flow)\b\s*/\s*"
    r"\b(?:positive|negative|boundary|format|dependency|integration|async|gap|scenario|action[- ]flow)\b",
    flags=re.IGNORECASE,
)

CONDITIONAL_BRANCH_PLAN_RE = re.compile(
    r"\bdependency\b|\bconditional[- ]visibility\b|condition\s*=\s*true|true\s+branch|"
    r"\bonly\s+if\b|\bvisible\s+when\b|\brequired\s+when\b|\beditable\s+when\b|"
    r"если|только\s+если|при\s+`?(?:да|нет)|отобража\w*\s+при|видим\w*\s+при|"
    r"обязател\w*\s+при|доступн\w*\s+при",
    flags=re.IGNORECASE,
)

INVERSE_OR_GAP_BRANCH_PLAN_RE = re.compile(
    r"\bnegative\b|\bgap\b|GAP-\d+|condition\s*=\s*false|false\s+branch|otherwise|else|"
    r"not\s+visible|hidden|not\s+required|unavailable|forbidden|"
    r"невыполн|обратн|иначе|не\s+отображ|скрыт|не\s+обязател|недоступ|запрещ",
    flags=re.IGNORECASE,
)

OPTIONAL_NO_BLOCKING_PLAN_RE = re.compile(
    r"may\s+remain\s+empty|may\s+remain\s+unset|optional|not\s+block|no[-\s]?blocking|"
    r"\u043c\u043e\u0436\u0435\u0442\s+\u043e\u0441\u0442\u0430\u0432\u0430\u0442\u044c\u0441\u044f\s+\u0431\u0435\u0437\s+\u043e\u0442\u0434\u0435\u043b\u044c\u043d\u043e\u0433\u043e\s+\u0432\u044b\u0431\u043e\u0440\u0430|"
    r"\u043c\u043e\u0436\u0435\u0442\s+\u043e\u0441\u0442\u0430\u0432\u0430\u0442\u044c\u0441\u044f\s+\u043f\u0443\u0441\u0442|"
    r"\u043d\u0435\s+\u0431\u043b\u043e\u043a\u0438\u0440\u0443\w+",
    flags=re.IGNORECASE,
)

PLAN_NEGATIVE_OR_REJECTION_RE = re.compile(
    r"\bnegative\b|\binvalid\b|not\s+accepted|rejected?|forbidden|"
    r"не\s+принима\w*|отклон\w*|невалидн\w*|недопустим\w*|нечислов\w*|"
    r"букв\w*|спецсимвол|пробел|слишком|выше\s+(?:max|p_max)|ниже\s+(?:min|p_min)|"
    r"\b(?:p_)?max\s*\+|\b(?:p_)?min\s*-|\bn\+1\b|\bn-1\b",
    flags=re.IGNORECASE,
)

PLAN_POSITIVE_ACCEPTANCE_RE = re.compile(
    r"\bpositive\b|\bvalid\b|accepted?|accepts?|saved|displayed|"
    r"принима\w*|валидн\w*|допустим\w*|корректн\w*|сохраня\w*|отображ\w*|применя\w*",
    flags=re.IGNORECASE,
)

NUMERIC_INVALID_CLASS_PATTERNS = {
    "letters": re.compile(r"\bletters?\b|\balpha(?:betic)?\b|Р±СѓРєРІ", flags=re.IGNORECASE),
    "spaces": re.compile(r"\bspaces?\b|\bwhitespace\b|РїСЂРѕР±РµР»", flags=re.IGNORECASE),
    "special-chars": re.compile(r"\bspecial[-\s]?(?:chars?|characters?|symbols?)\b|СЃРїРµС†", flags=re.IGNORECASE),
    "decimal-separator": re.compile(r"\bdecimal[-\s]?(?:separator|point|comma)\b|РґРµСЃСЏС‚РёС‡|Р·Р°РїСЏС‚", flags=re.IGNORECASE),
    "sign": re.compile(r"\bsign\b|\bplus\b|\bminus\b|[+-]\s*\d|Р·РЅР°Рє", flags=re.IGNORECASE),
}

PLAN_DIMENSIONS_REQUIRING_POSITIVE_ACCEPTANCE = {
    "boundary",
    "date-time",
    "dependency",
    "equivalence",
    "format",
    "length",
    "numeric",
    "validation",
    "conditional-visibility",
}


def numeric_invalid_classes_in_text(value: str) -> set[str]:
    return {
        class_name
        for class_name, pattern in NUMERIC_INVALID_CLASS_PATTERNS.items()
        if pattern.search(value)
    }


def row_has_numeric_format_context(row: dict[str, str], fields: tuple[str, ...]) -> bool:
    text = " | ".join(row.get(field, "") for field in fields)
    return bool(
        re.search(
            r"numeric[-_\s]?format|\bnumeric\b|digits?|С‡РёСЃР»|С†РёС„СЂ",
            text,
            flags=re.IGNORECASE,
        )
    )


def row_has_merged_numeric_invalid_classes(row: dict[str, str], fields: tuple[str, ...]) -> bool:
    text = " | ".join(row.get(field, "") for field in fields)
    invalid_classes = numeric_invalid_classes_in_text(text)
    if len(invalid_classes) < 2:
        return False
    test_case_count = len(extract_test_case_ids_from_text(row.get("planned_tc_or_gap", "")))
    class_fields = " | ".join(
        row.get(field, "")
        for field in ("coverage_class", "input_class", "testable_part", "planned_tc_or_gap")
    )
    has_list_separator = bool(
        re.search(
            r";|,\s*(?:decimal|sign|spaces?|special|letters?)\b",
            class_fields,
            flags=re.IGNORECASE,
        )
    )
    return test_case_count > 1 or has_list_separator


def plan_row_allows_multi_row_tc(row: dict[str, str]) -> bool:
    text = " ".join(
        row.get(field, "")
        for field in ("design_dimension", "planned_check", "check_type", "coverage_class")
    )
    return bool(re.search(r"scenario|use[-\s]?case|сценар|e2e|end[-\s]?to[-\s]?end|recovery|восстанов", text, flags=re.IGNORECASE))


def plan_row_semantic_text(row: dict[str, str]) -> str:
    return " | ".join(
        row.get(field, "")
        for field in (
            "design_dimension",
            "source_ref",
            "linked_atoms",
            "planned_check",
            "check_type",
            "coverage_class",
            "input_class",
            "single_expected_behavior",
            "planned_tc_or_gap",
        )
        if row.get(field)
    )


def plan_row_backtick_terms(row: dict[str, str]) -> set[str]:
    terms: set[str] = set()
    for value in (
        row.get("planned_check", ""),
        row.get("input_class", ""),
        row.get("single_expected_behavior", ""),
    ):
        for term in re.findall(r"`([^`=]{2,80})(?:\s*=\s*[^`]*)?`", value):
            normalized = re.sub(r"\s+", " ", term.strip()).casefold()
            if normalized:
                terms.add(normalized)
    return terms


def plan_rows_share_branch_context(row: dict[str, str], other: dict[str, str]) -> bool:
    if row is other:
        return False
    if row.get("package_id", "").strip() != other.get("package_id", "").strip():
        return False

    row_atoms = set(extract_any_atom_ids_from_text(row.get("linked_atoms", "")))
    other_atoms = set(extract_any_atom_ids_from_text(other.get("linked_atoms", "")))
    if row_atoms and other_atoms and row_atoms.intersection(other_atoms):
        return True

    source_ref = row.get("source_ref", "").strip().strip("`")
    other_source_ref = other.get("source_ref", "").strip().strip("`")
    if meaningful_matrix_value(source_ref) and source_ref == other_source_ref:
        return True

    row_terms = plan_row_backtick_terms(row)
    other_terms = plan_row_backtick_terms(other)
    return bool(row_terms and other_terms and row_terms.intersection(other_terms))


def plan_row_requires_inverse_branch(row: dict[str, str]) -> bool:
    text = plan_row_semantic_text(row)
    return bool(
        text
        and CONDITIONAL_BRANCH_PLAN_RE.search(text)
        and not OPTIONAL_NO_BLOCKING_PLAN_RE.search(text)
    )


def plan_row_is_inverse_or_gap_branch(row: dict[str, str]) -> bool:
    text = plan_row_semantic_text(row)
    if extract_gap_ids_from_text(row.get("planned_tc_or_gap", "")):
        return True
    return bool(INVERSE_OR_GAP_BRANCH_PLAN_RE.search(text))


def plan_row_dimension(row: dict[str, str]) -> str:
    return row.get("design_dimension", "").strip().strip("`").lower()


def plan_row_is_gap_or_scenario(row: dict[str, str]) -> bool:
    text = plan_row_semantic_text(row)
    check_type = row.get("check_type", "").strip().strip("`").lower()
    return bool(
        extract_gap_ids_from_text(row.get("planned_tc_or_gap", ""))
        or check_type in {"gap", "scenario"}
        or re.search(r"\bgap\b|scenario|use[-\s]?case|сценар", text, flags=re.IGNORECASE)
    )


def plan_row_requires_positive_acceptance_sibling(row: dict[str, str]) -> bool:
    if plan_row_is_gap_or_scenario(row):
        return False
    dimension = plan_row_dimension(row)
    if dimension and dimension not in PLAN_DIMENSIONS_REQUIRING_POSITIVE_ACCEPTANCE:
        return False
    text = plan_row_semantic_text(row)
    return bool(PLAN_NEGATIVE_OR_REJECTION_RE.search(text))


def plan_row_is_positive_acceptance(row: dict[str, str]) -> bool:
    if plan_row_is_gap_or_scenario(row):
        return False
    text = plan_row_semantic_text(row)
    check_type = row.get("check_type", "").strip().strip("`").lower()
    if "negative" in check_type or PLAN_NEGATIVE_OR_REJECTION_RE.search(text):
        return False
    return bool(PLAN_POSITIVE_ACCEPTANCE_RE.search(text))


def plan_row_exact_digit_count(row: dict[str, str]) -> int | None:
    if plan_row_is_gap_or_scenario(row) or not plan_row_is_positive_acceptance(row):
        return None
    text = plan_row_semantic_text(row)
    match = EXACT_DIGIT_COUNT_RE.search(text)
    if not match:
        return None
    for group in match.groups():
        if group:
            return int(group)
    return None


def plan_row_covers_digit_boundary(row: dict[str, str], atom_id: str, exact_count: int, offset: int) -> bool:
    linked_atoms = set(extract_any_atom_ids_from_text(row.get("linked_atoms", "")))
    if atom_id not in linked_atoms:
        return False
    text = plan_row_semantic_text(row)
    if not text or not PLAN_DIGIT_ONLY_RE.search(text):
        return False
    target_count = exact_count + offset
    if target_count < 0:
        return False
    sign = r"\+" if offset > 0 else "-"
    boundary_re = re.compile(
        PLAN_DIGIT_BOUNDARY_RE_TEMPLATE.format(sign=sign, target=target_count),
        flags=re.IGNORECASE,
    )
    if not boundary_re.search(text):
        return False
    if plan_row_is_gap_or_scenario(row):
        return bool(extract_gap_ids_from_text(row.get("planned_tc_or_gap", "")))
    return bool(PLAN_NEGATIVE_OR_REJECTION_RE.search(text))


def plan_row_has_repeated_digits_negative_check(row: dict[str, str], atom_id: str) -> bool:
    linked_atoms = set(extract_any_atom_ids_from_text(row.get("linked_atoms", "")))
    if atom_id not in linked_atoms:
        return False
    text = plan_row_semantic_text(row)
    if not text or not REPEATED_DIGITS_NEGATIVE_PLAN_RE.search(text):
        return False
    if plan_row_is_gap_or_scenario(row):
        return bool(extract_gap_ids_from_text(row.get("planned_tc_or_gap", "")))
    return bool(PLAN_NEGATIVE_OR_REJECTION_RE.search(text))


def validate_package_test_design_plan(
    content: str,
    path: Path,
    root: Path,
    *,
    structural_severity: str,
    known_test_case_ids: set[str] | None = None,
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    package_ids = package_ids_from_test_case_file(content)
    package_contract_active = bool(package_ids) or "Internal Work Package Coverage" in content
    plan_section = extract_markdown_section(content, "Package Test Design Plan")
    if not package_contract_active and not plan_section:
        return findings, checks

    plan_severity = "warning" if structural_severity == "info" else structural_severity
    if not plan_section:
        findings.append(
            Finding(
                id="test-case-package-design-plan-missing",
                severity=plan_severity,
                category="test-design",
                title="Package-based test-case file has no Package Test Design Plan",
                details="New package-based writer flow must record planned positive, negative, boundary, dependency/action and gap decisions before TC-* sections.",
                path=display_path,
                evidence=sorted(package_ids)[:20],
                recommended_action="Add `## Package Test Design Plan` with one row per planned check or GAP before handing the file to review.",
            )
        )
        checks.append(
            Check(
                "test-case-package-design-plan",
                "warn",
                "Package Test Design Plan is missing.",
                display_path,
            )
        )
        return findings, checks

    rows = markdown_table_rows_from_text(plan_section)
    if not rows:
        findings.append(
            Finding(
                id="test-case-package-design-plan-empty",
                severity=plan_severity,
                category="test-design",
                title="Package Test Design Plan has no table rows",
                details="The plan must be a structured table so reviewer and validator can trace planned checks.",
                path=display_path,
                evidence=[],
                recommended_action="Add the canonical Package Test Design Plan table.",
            )
        )
        checks.append(Check("test-case-package-design-plan", "warn", "Package Test Design Plan is empty.", display_path))
        return findings, checks

    header = normalize_table_header(rows[0])
    missing_columns = sorted(PACKAGE_DESIGN_PLAN_REQUIRED_COLUMNS - set(header))
    if missing_columns:
        findings.append(
            Finding(
                id="test-case-package-design-plan-missing-columns",
                severity=plan_severity,
                category="test-design",
                title="Package Test Design Plan is missing required columns",
                details="The design plan must expose package, dimension, linked atoms, planned check, coverage class and TC/GAP mapping.",
                path=display_path,
                evidence=missing_columns,
                recommended_action="Use the canonical columns from references/agent/package-test-design-plan-format.md.",
            )
        )

    plan_rows: list[dict[str, str]] = []
    for raw_row in rows[1:]:
        row: dict[str, str] = {}
        for index, column_name in enumerate(header):
            row[column_name] = raw_row[index].strip().strip("`") if index < len(raw_row) else ""
        plan_rows.append(row)

    plan_package_ids = {
        row.get("package_id", "").strip().strip("`")
        for row in plan_rows
        if meaningful_matrix_value(row.get("package_id", ""))
    }
    missing_package_ids = sorted(package_ids - plan_package_ids)
    if missing_package_ids:
        findings.append(
            Finding(
                id="test-case-package-design-plan-missing-package",
                severity=plan_severity,
                category="test-design",
                title="Package Test Design Plan does not cover every package",
                details="Every internal work package must have at least one design-plan row.",
                path=display_path,
                evidence=missing_package_ids[:20],
                recommended_action="Add design-plan rows for every missing package_id.",
            )
        )

    rows_missing_atoms: list[str] = []
    rows_missing_tc_or_gap: list[str] = []
    unknown_test_case_ids: list[str] = []
    generic_plan_rows: list[str] = []
    generic_gap_rows: list[str] = []
    merged_plan_rows: list[str] = []
    merged_numeric_plan_rows: list[str] = []
    combined_plan_rows: list[str] = []
    broad_scenario_plan_rows: list[str] = []
    missing_conditional_branch_rows: list[str] = []
    missing_positive_acceptance_rows: list[str] = []
    exact_digit_boundary_candidates: list[tuple[str, str, int]] = []
    tc_to_plan_rows: dict[str, list[str]] = {}
    multi_row_tc_allowed: dict[str, bool] = {}
    _, ledger_rows_for_plan = parsed_atomic_requirement_ledger_rows(content)
    ledger_req_by_atom = {
        row.get("atom_id", "").strip().strip("`"): (
            row.get("req_id", "")
            or row.get("source_reference", "")
            or row.get("source_ref", "")
            or row.get("atomic_statement", "")
        )
        for row in ledger_rows_for_plan
    }
    repeated_digit_atoms = {
        row.get("atom_id", "").strip().strip("`")
        for row in ledger_rows_for_plan
        if row.get("atom_id", "").strip()
        and REPEATED_DIGITS_REQUIREMENT_RE.search(
            " | ".join(
                row.get(field, "")
                for field in ("atomic_statement", "expected_behavior", "condition", "source_reference", "gap_note")
                if row.get(field)
            )
        )
    }
    all_test_case_ids = known_test_case_ids or {
        test_case_id for test_case_id, _ in extract_test_case_blocks(content)
    }
    for index, row in enumerate(plan_rows, start=2):
        design_item_id = row.get("design_item_id", "").strip() or f"row {index}"
        linked_atoms = row.get("linked_atoms", "")
        planned_tc_or_gap = row.get("planned_tc_or_gap", "")
        planned_check = row.get("planned_check", "")
        check_type = row.get("check_type", "")
        semantic_plan_text = " | ".join(
            row.get(field, "")
            for field in ("planned_check", "check_type", "coverage_class", "input_class", "single_expected_behavior")
            if row.get(field)
        )
        full_semantic_plan_text = plan_row_semantic_text(row)

        if not extract_any_atom_ids_from_text(linked_atoms):
            rows_missing_atoms.append(design_item_id)
        if not extract_test_case_ids_from_text(planned_tc_or_gap) and not extract_gap_ids_from_text(planned_tc_or_gap):
            rows_missing_tc_or_gap.append(design_item_id)
        for test_case_id in extract_test_case_ids_from_text(planned_tc_or_gap):
            if all_test_case_ids and test_case_id not in all_test_case_ids:
                unknown_test_case_ids.append(f"{design_item_id}:{test_case_id}")
            tc_to_plan_rows.setdefault(test_case_id, []).append(design_item_id)
            multi_row_tc_allowed[test_case_id] = (
                multi_row_tc_allowed.get(test_case_id, False)
                or plan_row_allows_multi_row_tc(row)
            )
        if planned_check and any(pattern.search(planned_check) for pattern in GENERIC_PLAN_SMELL_PATTERNS):
            generic_plan_rows.append(f"{design_item_id}:{planned_check[:160]}")
        if plan_row_is_gap_or_scenario(row) and GENERIC_GAP_PLAN_ROW_RE.search(full_semantic_plan_text):
            generic_gap_rows.append(f"{design_item_id}:{full_semantic_plan_text[:180]}")
        exact_digit_count = plan_row_exact_digit_count(row)
        if exact_digit_count is not None:
            for atom_id in extract_any_atom_ids_from_text(linked_atoms):
                exact_digit_boundary_candidates.append((design_item_id, atom_id, exact_digit_count))
        if check_type and MERGED_PLAN_CHECK_TYPE_RE.search(check_type):
            merged_plan_rows.append(f"{design_item_id}:check_type={check_type}; planned_check={planned_check[:120]}")
        if (
            row_has_numeric_format_context(
                row,
                (
                    "design_dimension",
                    "planned_check",
                    "check_type",
                    "coverage_class",
                    "input_class",
                    "single_expected_behavior",
                ),
            )
            and row_has_merged_numeric_invalid_classes(
                row,
                (
                    "planned_check",
                    "check_type",
                    "coverage_class",
                    "input_class",
                    "single_expected_behavior",
                    "planned_tc_or_gap",
                ),
            )
        ):
            merged_numeric_plan_rows.append(
                f"{design_item_id}:coverage_class={row.get('coverage_class', '-') or '-'};"
                f"input_class={row.get('input_class', '-') or '-'};"
                f"planned_tc_or_gap={planned_tc_or_gap or '-'}"
            )
        if semantic_plan_text and has_combined_behavior_smell(semantic_plan_text):
            combined_plan_rows.append(f"{design_item_id}:{semantic_plan_text[:180]}")
        if (
            plan_row_requires_inverse_branch(row)
            and not plan_row_is_inverse_or_gap_branch(row)
            and not any(
                plan_rows_share_branch_context(row, other) and plan_row_is_inverse_or_gap_branch(other)
                for other in plan_rows
            )
        ):
            missing_conditional_branch_rows.append(f"{design_item_id}:{full_semantic_plan_text[:180]}")
        if (
            full_semantic_plan_text
            and plan_row_requires_positive_acceptance_sibling(row)
            and not any(
                plan_rows_share_branch_context(row, other) and plan_row_is_positive_acceptance(other)
                for other in plan_rows
            )
        ):
            missing_positive_acceptance_rows.append(f"{design_item_id}:{full_semantic_plan_text[:180]}")
        if re.search(r"scenario|use[-\s]?case|сценар", check_type + " " + row.get("design_dimension", ""), flags=re.IGNORECASE):
            linked_atom_ids = extract_any_atom_ids_from_text(linked_atoms)
            broad_refs = [
                f"{atom_id}:{ledger_req_by_atom.get(atom_id, '')}"
                for atom_id in linked_atom_ids
                if max_requirement_range_span(ledger_req_by_atom.get(atom_id, "")) >= 4
            ]
            if broad_refs:
                broad_scenario_plan_rows.append(
                    f"{design_item_id}:linked={','.join(broad_refs[:4])}; planned_check={planned_check[:120]}"
                )
    tc_reused_by_plan_rows = [
        f"{test_case_id}:{','.join(design_item_ids[:8])}"
        for test_case_id, design_item_ids in sorted(tc_to_plan_rows.items())
        if len(design_item_ids) > 1 and not multi_row_tc_allowed.get(test_case_id, False)
    ]
    missing_exact_length_boundary_rows: list[str] = []
    for design_item_id, atom_id, exact_digit_count in exact_digit_boundary_candidates:
        missing_offsets = [
            label
            for label, offset in (("N-1", -1), ("N+1", 1))
            if not any(plan_row_covers_digit_boundary(other, atom_id, exact_digit_count, offset) for other in plan_rows)
        ]
        if missing_offsets:
            missing_exact_length_boundary_rows.append(
                f"{design_item_id}:{atom_id}:exact {exact_digit_count} digits missing={','.join(missing_offsets)}"
            )
    missing_repeated_digit_rows = [
        f"{atom_id}:{ledger_req_by_atom.get(atom_id, '')}"
        for atom_id in sorted(repeated_digit_atoms)
        if atom_id and not any(plan_row_has_repeated_digits_negative_check(row, atom_id) for row in plan_rows)
    ]

    if rows_missing_atoms:
        findings.append(
            Finding(
                id="test-case-package-design-plan-missing-atoms",
                severity=plan_severity,
                category="traceability",
                title="Package Test Design Plan rows are missing linked atoms",
                details="Each design-plan row must point to the exact ATOM-* it plans to cover or gap.",
                path=display_path,
                evidence=rows_missing_atoms[:20],
                recommended_action="Fill linked_atoms with ATOM-* ids from the Atomic Requirements Ledger.",
            )
        )
    if rows_missing_tc_or_gap:
        findings.append(
            Finding(
                id="test-case-package-design-plan-missing-tc-or-gap",
                severity=plan_severity,
                category="test-design",
                title="Package Test Design Plan rows have no planned TC or GAP",
                details="Each planned check must resolve to an executable TC-* or an explicit GAP-* before ready-for-review.",
                path=display_path,
                evidence=rows_missing_tc_or_gap[:20],
                recommended_action="Set planned_tc_or_gap to an existing/planned TC-* or GAP-*.",
            )
        )
    if unknown_test_case_ids:
        findings.append(
            Finding(
                id="test-case-package-design-plan-unknown-test-case-id",
                severity=plan_severity,
                category="traceability",
                title="Package Test Design Plan references unknown test-case ids",
                details="planned_tc_or_gap values must point to canonical ## TC-* sections or GAP-* ids.",
                path=display_path,
                evidence=unknown_test_case_ids[:20],
                recommended_action="Create the referenced TC-* sections or update planned_tc_or_gap.",
            )
        )
    if generic_plan_rows:
        findings.append(
            Finding(
                id="test-case-package-design-plan-generic-check-smell",
                severity="warning",
                category="test-design",
                title="Package Test Design Plan contains generic planned checks",
                details="Plan rows must name a concrete positive, negative, boundary, dependency/action or gap decision, not a placeholder.",
                path=display_path,
                evidence=generic_plan_rows[:20],
                recommended_action="Rewrite generic planned checks into explicit test-design classes before writing TC-* sections.",
            )
        )
    if generic_gap_rows:
        findings.append(
            Finding(
                id="test-case-package-design-plan-generic-gap-row",
                severity="warning",
                category="test-design",
                title="Package Test Design Plan has generic GAP rows",
                details=(
                    "A GAP row must explain the concrete untestable behavior and the missing fixture, source, "
                    "integration evidence or environment dependency. Generic `record as GAP` rows hide coverage "
                    "holes from reviewers."
                ),
                path=display_path,
                evidence=generic_gap_rows[:20],
                recommended_action=(
                    "Rewrite each GAP row so planned_check and single_expected_behavior name the exact missing "
                    "catalog value, backend branch, DaData behavior, dirty-state trigger, role/status fixture, "
                    "or other source-backed blocker."
                ),
            )
        )
    if missing_exact_length_boundary_rows:
        findings.append(
            Finding(
                id="test-case-package-design-plan-missing-exact-length-boundary",
                severity="warning",
                category="test-design",
                title="Package Test Design Plan misses exact-length digit boundaries",
                details=(
                    "For an exact N-digits rule, a positive exact-N row is not enough. The design plan needs "
                    "separate digit-only N-1 and N+1 rejection/GAP rows; a letters-only negative row does not "
                    "prove length-boundary behavior."
                ),
                path=display_path,
                evidence=missing_exact_length_boundary_rows[:20],
                recommended_action=(
                    "Add separate plan rows and TC/GAP links for digit-only N-1 and N+1 classes for each affected atom."
                ),
            )
        )
    if missing_repeated_digit_rows:
        findings.append(
            Finding(
                id="test-case-package-design-plan-missing-repeated-digits-check",
                severity="warning",
                category="test-design",
                title="Package Test Design Plan misses repeated-digits rejection checks",
                details=(
                    "Ledger atoms that forbid repeated/same consecutive digits need a negative plan row for "
                    "that class, not only a positive non-repeating example."
                ),
                path=display_path,
                evidence=missing_repeated_digit_rows[:20],
                recommended_action=(
                    "Add a separate negative TC/GAP row for each repeated-digits atom, with the concrete repeated "
                    "digit class in input_class or planned_check."
                ),
            )
        )
    if merged_plan_rows:
        findings.append(
            Finding(
                id="test-case-package-design-plan-merged-check-smell",
                severity="warning",
                category="test-design",
                title="Package Test Design Plan merges multiple check types in one row",
                details=(
                    "One design-plan row should represent one planned check or one GAP. "
                    "Slash-combined check_type values often hide positive/negative, boundary/format, "
                    "dependency/integration, or async/gap decomposition."
                ),
                path=display_path,
                evidence=merged_plan_rows[:20],
                recommended_action="Split merged design-plan rows so each row has one check_type and one planned check or GAP.",
            )
        )
    if merged_numeric_plan_rows:
        findings.append(
            Finding(
                id="test-case-package-design-plan-merged-numeric-class-row",
                severity="warning",
                category="test-design",
                title="Package Test Design Plan merges numeric invalid classes in one row",
                details=(
                    "For numeric-format coverage, each executable PDP row must represent one class-level check. "
                    "Rows that combine letters, decimal separators, signs, spaces and special characters hide "
                    "multiple independent negative-input checks behind one design_item_id."
                ),
                path=display_path,
                evidence=merged_numeric_plan_rows[:20],
                recommended_action=(
                    "Split the row into class-level PDP rows aligned with Coverage Obligation Table: one invalid "
                    "class, one single_expected_behavior and one primary TC-* or GAP-* per row."
                ),
            )
        )
    if combined_plan_rows:
        findings.append(
            Finding(
                id="design-plan-combined-class-smell",
                severity="warning",
                category="atomarity",
                title="Package Test Design Plan rows combine multiple classes",
                details=(
                    "Design-plan rows should describe one check type, one input class and one expected behavior. "
                    "Combined classes such as condition=true/false, length and repeated digits, or previous data branches "
                    "hide multiple executable checks."
                ),
                path=display_path,
                evidence=combined_plan_rows[:20],
                recommended_action="Split affected rows into separate positive, negative, boundary, dependency/action or GAP rows.",
            )
        )
    if broad_scenario_plan_rows:
        findings.append(
            Finding(
                id="scenario-plan-replaces-atomic-coverage-smell",
                severity="warning",
                category="atomarity",
                title="Scenario plan rows appear to replace broad atomic coverage",
                details=(
                    "Scenario/use-case rows may supplement atomic coverage, but they must not replace decomposition "
                    "of broad GSR/REQ ranges into atomic plan rows and TC/GAP items."
                ),
                path=display_path,
                evidence=broad_scenario_plan_rows[:20],
                recommended_action="Create atomic design rows and TC/GAP items for the underlying requirements; keep scenario rows only as additional use-case coverage.",
            )
        )
    if missing_conditional_branch_rows:
        findings.append(
            Finding(
                id="test-case-package-design-plan-missing-conditional-branch",
                severity="warning",
                category="test-design",
                title="Package Test Design Plan misses inverse conditional/dependency branches",
                details=(
                    "Rules such as `only if`, conditional visibility, required-when and dependency checks need "
                    "both the applicable/true branch and the inverse/negative branch, or an explicit GAP-* if the "
                    "inverse behavior is not derivable from the source."
                ),
                path=display_path,
                evidence=missing_conditional_branch_rows[:20],
                recommended_action=(
                    "Add a separate negative/false-branch design row and TC, or link the unresolved inverse "
                    "branch to GAP-* before marking the package ready for review."
                ),
            )
        )
    if missing_positive_acceptance_rows:
        findings.append(
            Finding(
                id="test-case-package-design-plan-negative-without-positive-acceptance",
                severity="warning",
                category="test-design",
                title="Package Test Design Plan has rejection/invalid checks without positive acceptance",
                details=(
                    "For field/input validation classes, rejection of invalid input does not prove that a valid "
                    "representative is accepted. The plan needs a sibling positive acceptance row for the same "
                    "source/atom context, or an explicit GAP-* if the acceptance oracle cannot be derived."
                ),
                path=display_path,
                evidence=missing_positive_acceptance_rows[:20],
                recommended_action=(
                    "Add a separate positive acceptance design row and TC for a valid representative value, "
                    "or link the missing acceptance oracle to GAP-*."
                ),
            )
        )
    if tc_reused_by_plan_rows:
        findings.append(
            Finding(
                id="test-case-package-design-plan-many-rows-one-tc-smell",
                severity="warning",
                category="atomarity",
                title="Package Test Design Plan maps multiple independent rows to one test case",
                details=(
                    "One executable plan row should resolve to one TC-* or GAP-*. Reusing one TC-* for several "
                    "independent rows is usually a sign that writer merged positive, negative, boundary, dependency "
                    "or action checks to reduce TC count."
                ),
                path=display_path,
                evidence=tc_reused_by_plan_rows[:20],
                recommended_action=(
                    "Split the affected TC-* into separate executable cases, or model the row as an explicit "
                    "scenario/recovery check that does not replace atomic TC coverage."
                ),
            )
        )

    has_findings = bool(
        missing_columns
        or missing_package_ids
        or rows_missing_atoms
        or rows_missing_tc_or_gap
        or unknown_test_case_ids
        or generic_plan_rows
        or generic_gap_rows
        or missing_exact_length_boundary_rows
        or missing_repeated_digit_rows
        or merged_plan_rows
        or combined_plan_rows
        or broad_scenario_plan_rows
        or missing_conditional_branch_rows
        or missing_positive_acceptance_rows
        or tc_reused_by_plan_rows
    )
    checks.append(
        Check(
            "test-case-package-design-plan",
            "warn" if has_findings else "pass",
            "Package Test Design Plan has issues." if has_findings else "Package Test Design Plan contract passed.",
            display_path,
        )
    )
    return findings, checks


def validate_test_design_review(
    content: str,
    path: Path,
    root: Path,
    *,
    suppress_blocked_input_failures: bool = False,
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    summary = test_design_review_summary(content)

    if not summary["required"]:
        checks.append(
            Check(
                "test-design-review",
                "pass",
                "Test Design Review is not required for this artifact.",
                display_path,
            )
        )
        return findings, checks

    if not summary["present"]:
        findings.append(
            Finding(
                id="test-design-review-missing",
                severity="warning",
                category="test-design",
                title="Package Test Design Plan has no Test Design Review",
                details=(
                    "Package-based writer output must include an explicit critical review of TDDT, ledger, "
                    "Package Test Design Plan and coverage gaps before it is routed to reviewer."
                ),
                path=display_path,
                evidence=["Package Test Design Plan present", "Test Design Review missing"],
                recommended_action=(
                    "Create `test-design-review.md` with the canonical required review items, then fix or block "
                    "any failed package before ready-for-review."
                ),
            )
        )
        checks.append(Check("test-design-review", "warn", "Test Design Review is missing.", display_path))
        return findings, checks

    if not summary["parseable"]:
        findings.append(
            Finding(
                id="test-design-review-no-table",
                severity="warning",
                category="test-design",
                title="Test Design Review has no parseable Markdown table",
                details="The section exists but has no canonical Markdown table.",
                path=display_path,
                evidence=[],
                recommended_action="Use the canonical Test Design Review table from test-design-review-format.md.",
            )
        )
    if summary["missing_columns"]:
        findings.append(
            Finding(
                id="test-design-review-missing-columns",
                severity="warning",
                category="test-design",
                title="Test Design Review misses required columns",
                details=(
                    "The review gate must expose item, status, severity, affected package, evidence, "
                    "required action and blocking flag."
                ),
                path=display_path,
                evidence=[f"missing={', '.join(summary['missing_columns'])}"],
                recommended_action="Rewrite the table with the canonical columns from test-design-review-format.md.",
            )
        )
    if summary["missing_items"]:
        findings.append(
            Finding(
                id="test-design-review-missing-required-items",
                severity="warning",
                category="test-design",
                title="Test Design Review misses required review items",
                details=(
                    "The review must explicitly criticize decision-table classification, ledger/plan alignment, "
                    "coverage classes, numeric length/boundary classes, conditional branches, gap specificity, "
                    "internal observability, metadata-only exclusion and TC mapping atomicity."
                ),
                path=display_path,
                evidence=summary["missing_items"][:20],
                recommended_action="Add one row for each required review item before moving the writer artifact to review.",
            )
        )
    if summary["unknown_items"]:
        findings.append(
            Finding(
                id="test-design-review-unknown-items",
                severity="warning",
                category="test-design",
                title="Test Design Review uses noncanonical review items",
                details=(
                    "Extra review_item values are not part of the canonical Test Design Review contract. "
                    "They may be useful as evidence, but they do not replace the required canonical items."
                ),
                path=display_path,
                evidence=summary["unknown_items"][:20],
                recommended_action=(
                    "Move extra checks into evidence or use only canonical review_item identifiers from "
                    "test-design-review-format.md."
                ),
            )
        )
    if summary["invalid_status_rows"]:
        findings.append(
            Finding(
                id="test-design-review-invalid-status",
                severity="warning",
                category="test-design",
                title="Test Design Review has noncanonical status values",
                details="Review status values must be pass/fail-style values.",
                path=display_path,
                evidence=summary["invalid_status_rows"][:20],
                recommended_action="Use `pass` for passed checks or `fail`/`blocked`/`needs-rewrite` for failed checks.",
            )
        )
    if summary["invalid_severity_rows"]:
        findings.append(
            Finding(
                id="test-design-review-invalid-severity",
                severity="warning",
                category="test-design",
                title="Test Design Review has invalid severity values",
                details="Review severity values must be `error`, `warning` or `info`.",
                path=display_path,
                evidence=summary["invalid_severity_rows"][:20],
                recommended_action="Use `error`, `warning` or `info` in the severity column.",
            )
        )
    if summary["invalid_blocks_rows"]:
        findings.append(
            Finding(
                id="test-design-review-invalid-blocks-value",
                severity="warning",
                category="test-design",
                title="Test Design Review has invalid blocks_ready_for_review values",
                details="The blocking flag must be `yes` or `no`, and passing rows must not keep `blocks_ready_for_review = yes`.",
                path=display_path,
                evidence=summary["invalid_blocks_rows"][:20],
                recommended_action="Set `blocks_ready_for_review` to `yes` only for failed blocking rows, otherwise `no`.",
            )
        )
    if summary["failed_rows"] and not suppress_blocked_input_failures:
        findings.append(
            Finding(
                id="test-design-review-failed",
                severity="warning",
                category="test-design",
                title="Test Design Review contains blocking failures",
                details=(
                    "The writer-side design critique found issues that block ready-for-review. The affected "
                    "package must be rewritten or the workflow must be blocked."
                ),
                path=display_path,
                evidence=summary["failed_rows"][:20],
                recommended_action=(
                    "Rewrite affected packages from Source Table Normalization/TDDT through Package Test Design Plan "
                    "and TC, or set workflow-state to blocked-input."
                ),
            )
        )

    has_findings = any(finding.id.startswith("test-design-review") for finding in findings)
    checks.append(
        Check(
            "test-design-review",
            "warn" if has_findings else "pass",
            "Test Design Review has issues." if has_findings else "Test Design Review passed.",
            display_path,
        )
    )
    return findings, checks


GENERIC_ATOM_SMELL_PATTERNS = [
    re.compile(r"требовани[ея]\s+[a-zа-я]+\s*\d+.*выполня", flags=re.IGNORECASE),
    re.compile(r"см\.\s*(?:gsr|source\s+row|строк[ауи])", flags=re.IGNORECASE),
    re.compile(r"поведение\s+.*соответствует\s+фт", flags=re.IGNORECASE),
    re.compile(r"без\s+проверяемого\s+expected\s+behavior", flags=re.IGNORECASE),
]

GENERIC_TC_NOT_REQUIRED_RE = re.compile(r"\u043d\u0435\s+\u0442\u0440\u0435\u0431\u0443\u044e\u0442\u0441\u044f", flags=re.IGNORECASE)

GENERIC_TC_SMELL_PATTERNS = [
    re.compile(r"\u043f\u0440\u0438\u0432\u0435\u0441\u0442\u0438\s+\u0434\u0430\u043d\u043d\u044b\u0435\s+\u043a\s+\u0441\u043e\u0441\u0442\u043e\u044f\u043d\u0438\u044e", flags=re.IGNORECASE),
    re.compile(r"\u0432\u0432\u0435\u0441\u0442\u0438\s+\u0438\u043b\u0438\s+\u0432\u044b\u0431\u0440\u0430\u0442\u044c", flags=re.IGNORECASE),
    re.compile(r"\u0441\u043e\u0433\u043b\u0430\u0441\u043d\u043e\s+\u0442\u0435\u0441\u0442\u043e\u0432\u044b\u043c\s+\u0434\u0430\u043d\u043d\u044b\u043c", flags=re.IGNORECASE),
    re.compile(r"\u0437\u043d\u0430\u0447\u0435\u043d\u0438\w+\s+\u0438\u0437\s+\u0442\u0435\u0441\u0442\u043e\u0432\u044b\w+\s+\u0434\u0430\u043d\u043d\w+\s+\u0434\u043b\u044f\s+\u044d\u0442\u043e\u0439\s+\u0441\u0442\u0440\u043e\u043a\u0438", flags=re.IGNORECASE),
    re.compile(r"\u043f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c\s+\u043d\u0430\u0431\u043b\u044e\u0434\u0430\u0435\u043c\w*\s+\u0441\u043e\u0441\u0442\u043e\u044f\u043d\u0438\w*\s+\u044d\u043b\u0435\u043c\u0435\u043d\u0442", flags=re.IGNORECASE),
    re.compile(r"\u0441\u0440\u0430\u0432\u043d\u0438\u0442\u044c\s+\u043d\u0430\u0431\u043b\u044e\u0434\u0430\u0435\u043c\w*\s+\u0441\u043e\u0441\u0442\u043e\u044f\u043d\u0438\w*", flags=re.IGNORECASE),
    re.compile(r"\u0437\u0430\u0444\u0438\u043a\u0441\u0438\u0440\u043e\u0432\u0430\w*\s+\u0432\u0438\u0434\u0438\u043c\w*\s+\u0441\u043e\u0441\u0442\u043e\u044f\u043d\u0438\w*[\s\S]{0,120}\u043f\u043e\u0441\u043b\u0435\s+\u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d\w*\s+\u0434\u0435\u0439\u0441\u0442\u0432\w*", flags=re.IGNORECASE),
    re.compile(r"\u0441\u043e\u0433\u043b\u0430\u0441\u043d\u043e\s+\u0447\u0435\u043a-?\u043b\u0438\u0441\u0442", flags=re.IGNORECASE),
    GENERIC_TC_NOT_REQUIRED_RE,
    re.compile(r"\u0435\u0441\u043b\u0438\s+\u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430\s+\u0442\u0440\u0435\u0431\u0443\u0435\u0442", flags=re.IGNORECASE),
    re.compile(r"подготовить\s+состояние(?:\s+раздела)?", flags=re.IGNORECASE),
    re.compile(r"установить\s+условие", flags=re.IGNORECASE),
    re.compile(r"выполнить\s+проверяемое\s+действие", flags=re.IGNORECASE),
    re.compile(r"выполнить\s+действие\s+согласно\s+фт", flags=re.IGNORECASE),
    re.compile(r"проверить\s+выполнени[ея]\s+требован", flags=re.IGNORECASE),
    re.compile(r"проверить\s+итоговое\s+состояние", flags=re.IGNORECASE),
    re.compile(r"данные,\s+достаточные\s+для\s+проверки", flags=re.IGNORECASE),
    re.compile(r"значени[ея],?\s+нарушающ\w+\s+(?:указанн\w+\s+)?(?:числов\w+|length|форматн\w+|правил)", flags=re.IGNORECASE),
    re.compile(r"значени[ея]\s+из\s+проверяемого\s+класс[а-я\s]+по\s+фт", flags=re.IGNORECASE),
    re.compile(r"дат[аы],?\s+соответствующ\w+\s+проверяем\w+\s+календарн\w+\s+ветк\w+\s+фт", flags=re.IGNORECASE),
    re.compile(r"ввести\s+или\s+выбрать\s+значени[ея]\s+из\s+тестовых\s+данных", flags=re.IGNORECASE),
    re.compile(r"выполнены\s+условия\s+применимости", flags=re.IGNORECASE),
    re.compile(r"см\.\s+связанн\w+\s+строк\w+\s+atomic\s+requirements\s+ledger", flags=re.IGNORECASE),
    re.compile(r"поведение\s+наблюдаемо\s+через\s+ui\s+и\s+соответствует\s+фт", flags=re.IGNORECASE),
    re.compile(r"подготовить\s+ветку", flags=re.IGNORECASE),
    re.compile(r"сравнить\s+состояние\s+поля\s+с\s+ожидаемым\s+правилом\s+фт", flags=re.IGNORECASE),
    re.compile(r"проверить\s+соответствие\s+фт", flags=re.IGNORECASE),
    re.compile(r"убедиться,\s+что\s+правило\s+выполнено", flags=re.IGNORECASE),
    re.compile(r"проверить\s+поле\s+согласно\s+фт", flags=re.IGNORECASE),
    re.compile(r"выполнить\s+проверку\s+значения", flags=re.IGNORECASE),
    re.compile(r"при\s+необходимости", flags=re.IGNORECASE),
]

GENERIC_VALID_FIXTURE_PLACEHOLDER_RE = re.compile(
    r"минимальн\w+\s+валидн\w+\s+набор|"
    r"валидн\w+\s+(?:заявк|анкет|карточк|данн\w+)|"
    r"валидн\w+\s+значени[ея]\s+из\s+предуслови|"
    r"source-backed\s+baseline|"
    r"если\s+требуется\s+запуск\s+действи|"
    r"full\s+valid\s+(?:fixture|data|set)",
    flags=re.IGNORECASE,
)
GENERIC_TEST_DATA_REFERENCE_RE = re.compile(
    r"значени[ея]\s+из\s+тестов\w+\s+данн\w+|"
    r"использовать\s+воспроизводим\w+\s+тестов\w+\s+значени[ея]\s+из\s+шага|"
    r"невалидн\w+\s+или\s+пуст\w+\s+значени[ея]\s+указан\w+",
    flags=re.IGNORECASE,
)
GENERIC_TEST_DATA_ORACLE_RE = re.compile(
    r"значени[ея]\s+из\s+тестов\w+\s+данн\w+\s+"
    r"(?:принят\w*|не\s+принима\w*|отобража\w*|сохран\w*)",
    flags=re.IGNORECASE,
)

VALUE_TYPE_PROPERTY_RE = re.compile(r"\bvalue[-_ ]?type\b|тип\s+значени", flags=re.IGNORECASE)
NON_LIST_VALUE_TYPE_RE = re.compile(
    r"тип\s+значени\w*\s*:\s*(?:строка|дата|логическ|числ|number|string|date|boolean)",
    flags=re.IGNORECASE,
)
LIST_VALUE_TYPE_RE = re.compile(
    r"тип\s+значени\w*\s*:\s*(?:значени[ея]\s+из|список|справочник|перечень|list|dictionary|dropdown)",
    flags=re.IGNORECASE,
)
VALUE_TYPE_LIST_SELECTION_RE = re.compile(
    r"значени[ея]\s+выбира\w+\s+из\s+отображаем\w+\s+списк|"
    r"открыть\s+контрол[\s\S]{0,120}выбрать\s+доступн\w+\s+значени|"
    r"открывает\s+список\s+или\s+выбор\s+значени",
    flags=re.IGNORECASE,
)
DEPENDENCY_PLACEHOLDER_SETUP_RE = re.compile(
    r"в\s+форме\s+задать\s+данные,\s+при\s+которых(?:\s+условие\s+источника)?",
    flags=re.IGNORECASE,
)
GENERIC_RULE_ORACLE_RE = re.compile(
    r"видимое\s+состояние\s+после\s+действия\s+соответствует\s+одному\s+наблюдаемому\s+правилу|"
    r"поле\s+изменяет,\s*отображает\s+или\s+ограничивает\s+значение\s+без\s+утверждения\s+внутренних\s+эффектов",
    flags=re.IGNORECASE,
)
SOURCE_DUMP_RULE_ORACLE_RE = re.compile(
    r"наблюда\w+\s+правило\s+из\s+`?(?:GSR|REQ|[A-ZА-Я]{2,}[-\s]?\d+)\b|"
    r"для\s+`?[^`\n]{1,120}`?\s+наблюда\w+\s+правило\s+из\s+`?(?:GSR|REQ|[A-ZА-Я]{2,}[-\s]?\d+)\b",
    flags=re.IGNORECASE,
)
VALUE_TYPE_METADATA_AS_BEHAVIOR_RE = re.compile(
    r"контрольн\w+\s+строков\w+\s+значени\w+|"
    r"принима\w+\s+и\s+отобража\w+\s+введенн\w+\s+строков\w+\s+значени\w+",
    flags=re.IGNORECASE,
)
EXTRACTION_ARTIFACT_ORACLE_PATTERNS = [
    re.compile(r"\b[ДП]\s+[ао]\b", flags=re.IGNORECASE),
    re.compile(r"Рефинансировани\s+е", flags=re.IGNORECASE),
    re.compile(r"Переключат\s+ель", flags=re.IGNORECASE),
    re.compile(r"выведенног\s+о", flags=re.IGNORECASE),
    re.compile(r"подразде\s+ление", flags=re.IGNORECASE),
    re.compile(r"активир\s+ован", flags=re.IGNORECASE),
    re.compile(r"остальн\s+ых", flags=re.IGNORECASE),
    re.compile(r"клиент\s+прожива\s+ет", flags=re.IGNORECASE),
]

MOCKUP_INTERACTION_HINT_RE = re.compile(
    r"segmented\s+tab|amount\s+tag|slider|toggle|checkbox|dropdown|calendar|date\s+field|"
    r"переключател|тумблер|чек-?бокс|checkbox|список|dropdown|выпадающ|календар|слайдер|вкладк",
    flags=re.IGNORECASE,
)
MOCKUP_GENERIC_UI_STEP_RE = re.compile(
    r"в\s+поле\s+`?[^`\n]+`?\s+ввести\s+значени[ея]\s+из\s+тестовых\s+данных|"
    r"найти\s+(?:область|элемент|поле)|"
    r"перейти\s+к\s+нужн\w+\s+(?:элемент|пол|област)|"
    r"выполнить\s+действие\s+согласно\s+(?:макету|фт)|"
    r"установить\s+значение\s+из\s+тестовых\s+данных",
    flags=re.IGNORECASE,
)

GENERIC_TC_TITLE_PATTERNS = [
    re.compile(r"проверяет\s+поле\b", flags=re.IGNORECASE),
    re.compile(r"отображает\s+отображ", flags=re.IGNORECASE),
    re.compile(r"отклоняет\s+значен", flags=re.IGNORECASE),
    re.compile(r"^\s*.+:\s+(?:проверяет|отклоняет|отображает)\s+.+$", flags=re.IGNORECASE),
]

ATOM_COMPRESSION_MARKERS: dict[str, re.Pattern[str]] = {
    "visibility": re.compile(r"\bвидим|отображ|скрыт", flags=re.IGNORECASE),
    "requiredness": re.compile(r"обязател|не\s+обязател", flags=re.IGNORECASE),
    "editability": re.compile(r"редакт|доступн|enabled|disabled", flags=re.IGNORECASE),
    "default": re.compile(r"default|по\s+умолчан|дефолт", flags=re.IGNORECASE),
    "format": re.compile(r"формат|маск|только\s+цифр|только\s+числ|текст|символ", flags=re.IGNORECASE),
    "boundary": re.compile(r"\bmin\b|\bmax\b|границ|лимит|длин|n-1|n\+1", flags=re.IGNORECASE),
    "dictionary": re.compile(r"список|справочник|каталог|тег", flags=re.IGNORECASE),
    "validation": re.compile(r"принима|отклон|валид|ошибк|подсказ", flags=re.IGNORECASE),
    "dependency": re.compile(r"завис|при\s+`?да|при\s+`?нет|если|услов", flags=re.IGNORECASE),
    "integration": re.compile(r"dadata|api|rabbitmq|connect|цп|интеграц", flags=re.IGNORECASE),
    "persistence": re.compile(r"сохран|модел|database|db|kladr|esiauserid|correlationid", flags=re.IGNORECASE),
    "status-action": re.compile(r"статус|переход|инициир|кнопк|действи|отправ", flags=re.IGNORECASE),
}

MERGED_VALID_INVALID_EXPECTED_PATTERNS = [
    re.compile(
        r"(?:не\s+принима\w*|отклон\w*|не\s+сохраня\w*|счита[её]тся\s+невалидн\w*)"
        r"[\s\S]{0,180}\bи\b[\s\S]{0,180}"
        r"(?:принима\w*|сохраня\w*|счита[её]тся\s+валидн\w*)",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"(?:принима\w*|сохраня\w*|счита[её]тся\s+валидн\w*)"
        r"[\s\S]{0,180}\bи\b[\s\S]{0,180}"
        r"(?:не\s+принима\w*|отклон\w*|не\s+сохраня\w*|счита[её]тся\s+невалидн\w*)",
        flags=re.IGNORECASE,
    ),
    re.compile(r"(?:invalid|rejected|not\s+accepted)[\s\S]{0,180}(?:valid|accepted)", flags=re.IGNORECASE),
    re.compile(r"(?:valid|accepted)[\s\S]{0,180}(?:invalid|rejected|not\s+accepted)", flags=re.IGNORECASE),
]

MERGED_VALID_INVALID_DATA_STEP_RE = re.compile(
    r"(?:невалидн\w*|недопустим\w*|нечислов\w*|invalid|forbidden|non[-\s]?numeric)"
    r"[\s\S]{0,260}"
    r"(?:валидн\w*|допустим\w*|valid|allowed)",
    flags=re.IGNORECASE,
)

ACTION_INITIATION_WITHOUT_ARTIFACT_RE = re.compile(
    r"(?:действи[ея]\s+)?(?:проверить|отправить\s+повторно|[\w\s]+)?\s*"
    r"(?:инициир\w+|запуска\w+|started|initiated)",
    flags=re.IGNORECASE,
)

CONCRETE_OBSERVABLE_ARTIFACT_RE = re.compile(
    r"уведомлен|сообщен|подсказ|ошибк|отображ|открыва|переход|статус\s+измен|"
    r"значени[ея]\s+(?:отображ|измен|сохран)|поле\s+(?:отображ|заполн|очищ)|"
    r"документ|журнал|лог\s+`|api\s+response|http|mock|fixture|artifact|evidence",
    flags=re.IGNORECASE,
)

NEGATIVE_OR_REJECTION_EXPECTED_RE = re.compile(
    r"не\s+принима\w*|отклон\w*|не\s+сохраня\w*|невалидн\w*|ошибк|"
    r"не\s+применя\w*|выше\s+(?:max|p_max|максим)|ниже\s+(?:min|p_min|миним)|"
    r"переход\s+не\s+выполня\w*|переход\s+заблок\w*|заблок\w*|"
    r"(?:раздел|экран|форма)\s+[^.\n;]{0,120}не\s+откры\w*|подсвеч\w*\s+красн\w*|"
    r"above\s+max|below\s+min|reject|rejected|not\s+accepted|invalid|transition\s+blocked|does\s+not\s+proceed",
    flags=re.IGNORECASE,
)

NONDETERMINISTIC_ALTERNATIVE_ORACLE_RE = re.compile(
    r"(?:значени[ея]\s+)?(?:очищ\w+|не\s+сохран\w+|не\s+принима\w+|отклон\w+|подсвеч\w+|ошибк\w+|"
    r"оста[её]тся\s+(?:незаполн\w+|предыдущ\w+|неизмен\w+|пуст\w+))"
    r"[\s\S]{0,140}\bили\b[\s\S]{0,140}"
    r"(?:значени[ея]\s+)?(?:очищ\w+|не\s+сохран\w+|не\s+принима\w+|отклон\w+|подсвеч\w+|ошибк\w+|"
    r"оста[её]тся\s+(?:незаполн\w+|предыдущ\w+|неизмен\w+|пуст\w+))",
    flags=re.IGNORECASE,
)

GAP_PLACEHOLDER_EXPECTED_RE = re.compile(
    r"(?:^|\b)GAP-\d{3,}\b[\s\S]{0,220}"
    r"(?:нет\s+отдельн|не\s+выводится|не\s+задает\s+отдельн|metadata-only|no\s+standalone|no\s+observable)",
    flags=re.IGNORECASE,
)

GENERIC_EXPECTED_RESULT_PATTERNS = [
    re.compile(r"соответствует\s+(?:фт|gsr|ожидаем\w+\s+правил)", flags=re.IGNORECASE),
    re.compile(r"\u0441\u043e\u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\w+\s+\u043f\u0440\u0430\u0432\u0438\u043b\w+\s+\u0438\u0441\u0442\u043e\u0447\u043d\u0438\u043a\w+", flags=re.IGNORECASE),
    re.compile(r"\u0441\u0432\u043e\u0439\u0441\u0442\u0432\w+[\s\S]{0,120}\u0437\u0430\u0444\u0438\u043a\u0441\u0438\u0440\u043e\u0432\u0430\w+\s+\u0438\u0441\u0442\u043e\u0447\u043d\u0438\u043a\w+\s+\u043a\u0430\u043a\s+gsr", flags=re.IGNORECASE),
    re.compile(r"\u0432\u0435\u0434\w+\s+\u043a\s+\u0431\u0438\u0437\u043d\u0435\u0441-\u0446\u0435\u043b\w+|business-need", flags=re.IGNORECASE),
    re.compile(r"gsr\s+\d+\s*/\s*[^/]+/\s*(?:format|visibility|requiredness|editability|dictionary|source|action|validation)", flags=re.IGNORECASE),
    re.compile(r"\u0446\u0435\u043b\u0435\u0432\w+\s+(?:\u044d\u043a\u0440\u0430\u043d|\u0440\u0430\u0437\u0434\u0435\u043b)[\s\S]{0,160}\u0443\u043a\u0430\u0437\u0430\w+[\s\S]{0,80}\u0432\s+\u0444\u0442", flags=re.IGNORECASE),
    re.compile(r"\u0443\u043a\u0430\u0437\u0430\w+\s+\u0434\u043b\u044f\s+\u044d\u0442\u043e\u0433\u043e\s+\u0434\u0435\u0439\u0441\u0442\u0432\w+\s+\u0432\s+\u0444\u0442", flags=re.IGNORECASE),
    re.compile(r"согласно\s+фт", flags=re.IGNORECASE),
    re.compile(r"ожидаем\w+\s+правил\w+\s+фт", flags=re.IGNORECASE),
    re.compile(r"^поле\s+.+\s+принимает\s+только\s+.+$", flags=re.IGNORECASE),
    re.compile(r"^поле\s+.+\s+обязательно\s+к\s+заполнению\.?$", flags=re.IGNORECASE),
    re.compile(r"целев\w+\s+пользовательск\w+\s+переход", flags=re.IGNORECASE),
]

REQUIREDNESS_RE = re.compile(r"обязател", flags=re.IGNORECASE)
EMPTY_REQUIREDNESS_CHECK_RE = re.compile(r"\bпуст|\bочист|не\s+заполня|без\s+значени", flags=re.IGNORECASE)
REQUIREDNESS_MARKER_RE = re.compile(r"признак|маркер|зв[её]здоч|asterisk|label|обознач", flags=re.IGNORECASE)
BOUNDARY_CLASS_RE = re.compile(r"\bmin(?:[-+]|$)|\bmax(?:[-+]|$)|p_min|p_max|n-1|n\+1|границ|\d+\s*(?:символ|цифр)", flags=re.IGNORECASE)
OFF_BOUNDARY_MAX_RE = re.compile(
    r"\b(?:p_)?max\s*(?:\+\s*(?:delta|1|\d+)|\+\d)|above\s+(?:p_)?max|>\s*(?:p_)?max|"
    r"выше\s+(?:p_)?max|больше\s+(?:p_)?max",
    flags=re.IGNORECASE,
)
OFF_BOUNDARY_MIN_RE = re.compile(
    r"\b(?:p_)?min\s*(?:-\s*(?:delta|1|\d+)|-\d)|below\s+(?:p_)?min|<\s*(?:p_)?min|"
    r"ниже\s+(?:p_)?min|меньше\s+(?:p_)?min",
    flags=re.IGNORECASE,
)
EXACT_BOUNDARY_MAX_RE = re.compile(r"\b(?:p_)?max\b|максимальн\w+\s+границ", flags=re.IGNORECASE)
EXACT_BOUNDARY_MIN_RE = re.compile(r"\b(?:p_)?min\b|минимальн\w+\s+границ", flags=re.IGNORECASE)
BOUNDARY_ACCEPTANCE_RESULT_RE = re.compile(
    r"accept\w*|accepted|saved|displayed|принима\w*|сохраня\w*|отображ\w*|применя\w*",
    flags=re.IGNORECASE,
)
POSITIVE_ACCEPTANCE_EXPECTED_RE = re.compile(
    r"accept\w*|accepted|valid|saved|displayed|принима\w*|валидн\w*|допустим\w*|"
    r"корректн\w*|сохраня\w*|отображ\w*|применя\w*",
    flags=re.IGNORECASE,
)
NUMERIC_ONLY_CONTEXT_RE = re.compile(
    r"numeric|number|digits?|\u0447\u0438\u0441\u043b\u043e\u0432|\u0446\u0438\u0444\u0440|"
    r"\u0442\u043e\u043b\u044c\u043a\u043e\s+(?:\u0447\u0438\u0441\u043b|\u0446\u0438\u0444\u0440)",
    flags=re.IGNORECASE,
)
INPUT_FILTERING_ORACLE_RE = re.compile(
    r"(?:букв|символ|пробел|знак|спецсимвол)[^.\n;]{0,80}не\s+(?:появля|отображ|добавля|ввод)|"
    r"не\s+(?:появля|отображ|добавля|ввод)[^.\n;]{0,80}(?:букв|символ|пробел|знак|спецсимвол)|"
    r"отобража\w+\s+только\s+(?:цифров|числов)|"
    r"поле\s+[^.\n;]{0,80}(?:содержит|отображает)\s+только\s+(?:цифров|числов)|"
    r"фильтр\w+|отфильтр\w+|игнорир\w+\s+(?:ввод|символ)|"
    r"(?:does\s+not|not)\s+appear|filtered|stripped|input\s+is\s+ignored",
    flags=re.IGNORECASE,
)

FIELD_LEVEL_INPUT_RESTRICTION_RE = re.compile(
    r"только\s+(?:\d+\s+)?(?:цифр|числов|текстов)|"
    r"содержит\s+только\s+\d+\s+цифр|"
    r"содержит\s+\d+\s+цифр|"
    r"маск\w+|максимальн\w+\s+длин|точн\w+\s+длин|"
    r"exact\s+\d+\s+digits?|only\s+\d+\s+digits?|digits?\s+only|numeric[-\s]?only|"
    r"allowed\s+characters?|forbidden\s+characters?",
    flags=re.IGNORECASE,
)

OVERLIMIT_INPUT_RESTRICTION_RE = re.compile(
    r"длиннее|лишн\w+\s+(?:цифр|символ)|сверх\s+(?:лимит|длин)|"
    r"\b(?:n|max)\s*\+\s*1\b|above\s+max|longer\s+than|max(?:imum)?\s*\+\s*1|"
    r"седьм\w+\s+цифр|пят\w+\s+цифр|одиннадцат\w+\s+цифр",
    flags=re.IGNORECASE,
)

INVALID_CHARACTER_INPUT_RESTRICTION_RE = re.compile(
    r"букв|пробел|спецсимвол|символ\s*#|запят|минус|нечислов|"
    r"недопустим\w+\s+символ|letter|space|special\s+character|comma|minus|non[-\s]?digit",
    flags=re.IGNORECASE,
)

UNDERLIMIT_INPUT_RESTRICTION_RE = re.compile(
    r"короче|меньше\s+(?:требуем|миним)|ниже\s+(?:min|миним)|under\s+min|below\s+min|shorter",
    flags=re.IGNORECASE,
)

TRANSITION_VALIDATION_ORACLE_RE = re.compile(
    r"переход\s+(?:отклон|заблок|не\s+выполня)|"
    r"(?:раздел|экран|форма)\s+[^.\n;]{0,120}не\s+открыва|"
    r"нажатие\s+[^.\n;]{0,120}заблок|"
    r"transition\s+(?:blocked|rejected)|does\s+not\s+proceed",
    flags=re.IGNORECASE,
)
NUMERIC_INVALID_INPUT_CONTEXT_RE = re.compile(
    r"numeric[-\s]?only|digits?\s+only|only\s+(?:numeric|digits?)|non[-\s]?digit|letters?|spaces?|"
    r"special\s+characters?|decimal[-\s]?separator|sign|comma|minus|below\s+(?:min|minimum)|under\s+(?:min|minimum)|"
    r"\u0442\u043e\u043b\u044c\u043a\u043e\s+(?:\u0447\u0438\u0441\u043b|\u0446\u0438\u0444\u0440)|"
    r"\u043d\u0435\u0447\u0438\u0441\u043b\u043e\u0432|\u0431\u0443\u043a\u0432|\u043f\u0440\u043e\u0431\u0435\u043b|"
    r"\u0441\u043f\u0435\u0446\w*\s*\u0441\u0438\u043c\u0432\u043e\u043b|\u0441\u043f\u0435\u0446\u0441\u0438\u043c\u0432\u043e\u043b|"
    r"\u0434\u0435\u0441\u044f\u0442\u0438\u0447\w*\s+\u0440\u0430\u0437\u0434\u0435\u043b|\u0437\u0430\u043f\u044f\u0442|"
    r"\u0437\u043d\u0430\u043a\s+[`'\"]?-|\u043c\u0438\u043d\u0443\u0441|\u043d\u0438\u0436\u0435\s+\d+|\u043d\u0438\u0436\u0435\s+(?:min|\u043c\u0438\u043d\u0438\u043c)|"
    r"\u043c\u0435\u043d\u044c\u0448\u0435\s+(?:\d+|\u043c\u0438\u043d\u0438\u043c)",
    flags=re.IGNORECASE,
)
NUMERIC_VALIDATION_FEEDBACK_ORACLE_RE = re.compile(
    r"red[-\s]?highlight|highlighted\s+red|field\s+[^.\n;]{0,120}highlighted|"
    r"(?:section|screen|form)\s+[^.\n;]{0,120}does\s+not\s+open|"
    r"transition\s+(?:blocked|rejected)|does\s+not\s+proceed|"
    r"\u043f\u043e\u0434\u0441\u0432\u0435\u0447\w*\s+\u043a\u0440\u0430\u0441\u043d|"
    r"\u043a\u0440\u0430\u0441\u043d\w*\s+[^.\n;]{0,80}\u043f\u043e\u0434\u0441\u0432\u0435\u0447|"
    r"\u0440\u0430\u0437\u0434\u0435\u043b\s+[^.\n;]{0,120}\u043d\u0435\s+\u043e\u0442\u043a\u0440\u044b",
    flags=re.IGNORECASE,
)
POSITIVE_TRANSITION_ORACLE_RE = re.compile(
    r"(?:раздел\w*|экран\w*|форм\w*)\s+[^.\n;]{0,160}(?:открыт|открыва|доступн|сформирован)|"
    r"(?:открыт|открыва|доступн|сформирован)\w*\s+[^.\n;]{0,120}(?:раздел|экран|форм)|"
    r"(?:opened|available|generated)",
    flags=re.IGNORECASE,
)

FORBIDDEN_TEST_CASE_FORMULATION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("standalone validity verdict", re.compile(r"счита[её]тся\s+(?:не)?валидн\w*", flags=re.IGNORECASE)),
    ("abstract validation pass/fail", re.compile(r"не\s+проходит\s+валидац\w*", flags=re.IGNORECASE)),
    ("generic whitespace character", re.compile(r"пробельн\w+\s+символ", flags=re.IGNORECASE)),
    ("generic alphabetic character", re.compile(r"буквенн\w+\s+символ", flags=re.IGNORECASE)),
    ("negative data residue", re.compile(r"недопустим\w+\s+символ\w*\s+из\s+ввода", flags=re.IGNORECASE)),
    ("generic decimal separator", re.compile(r"десятичн\w+\s+разделител", flags=re.IGNORECASE)),
    ("fixture shorthand dictionary values", re.compile(r"\bDictionary\s+values?\b", flags=re.IGNORECASE)),
    ("fixture shorthand selected tag", re.compile(r"\bSelected\s+tag\b", flags=re.IGNORECASE)),
    ("fixture shorthand branch state", re.compile(r"\bBranch\s+state\b|\bcondition\s*=\s*false\b", flags=re.IGNORECASE)),
    ("generic corresponding block", re.compile(r"соответствующ\w+\s+блок", flags=re.IGNORECASE)),
    ("abstract ordinary state", re.compile(r"обычн\w+\s+состояни", flags=re.IGNORECASE)),
    ("undefined UI reaction", re.compile(r"способ\s+реакции\s+UI", flags=re.IGNORECASE)),
    ("duplicated default placeholder", re.compile(r"значени[ея]\s+по\s+умолчанию\s+значени[ея]\s+по\s+умолчанию", flags=re.IGNORECASE)),
]

ABSTRACT_TEST_CASE_ORACLE_RE = re.compile(
    r"счита[её]тся\s+(?:не)?валидн\w*|"
    r"не\s+проходит\s+валидац\w*|"
    r"не\s+соответствует\s+правил\w+|"
    r"соответствует\s+правил\w+|"
    r"по\s+правил\w+\s+[`«\"]?[^`»\"]+[`»\"]?\s*\.?$",
    flags=re.IGNORECASE,
)

OBSERVABLE_TEST_CASE_ORACLE_RE = re.compile(
    r"отображ|подсказ|сообщен|ошибк|подсвеч|"
    r"переход\s+(?:не\s+выполня|заблок|отклон)|"
    r"(?:раздел|экран|форма)\s+[^.\n;]{0,100}не\s+открыва|"
    r"сохранени[ея]\s+не\s+выполня|не\s+сохраня|"
    r"очищ|заполн|доступн|недоступн|скрыт|видим|выбран|"
    r"значени[ея]\s+[^.\n;]{0,100}(?:принима|не\s+принима)",
    flags=re.IGNORECASE,
)

NEGATIVE_INPUT_ACTION_RE = re.compile(r"\b(?:ввести|набрать|указать|enter|type)\b", flags=re.IGNORECASE)
MECHANICAL_FIELD_STEP_RE = re.compile(
    r"(?:\u0449\u0435\u043b\u043a\u043d\u0443\u0442\u044c\s+\u043f\u043e\u043b\u0435|"
    r"\u043a\u043b\u0438\u043a\u043d\u0443\u0442\u044c\s+\u043f\u043e\u043b\u0435|"
    r"\u043d\u0430\u0436\u0430\u0442\u044c\s+\u043d\u0430\s+\u043f\u043e\u043b\u0435|"
    r"\u043d\u0430\u0431\u0440\u0430\u0442\u044c)",
    flags=re.IGNORECASE,
)

FIELD_LEVEL_OBSERVABLE_ORACLE_RE = re.compile(
    r"отображ|подсказ|сообщен|ошибк|подсвеч|очищ|не\s+сохраня|сохранени[ея]\s+не\s+выполня|"
    r"значени[ея]\s+[^.\n;]{0,100}не\s+принима\w*\s+в\s+поле|"
    r"переход\s+(?:не\s+выполня|заблок|отклон)|(?:раздел|экран|форма)\s+[^.\n;]{0,100}не\s+открыва",
    flags=re.IGNORECASE,
)

DATE_DEPENDENT_SOURCE_RE = re.compile(r"текущ\w+\s+дат|current\s+date|минус\s+\d+\s+лет", flags=re.IGNORECASE)
ABSOLUTE_DATE_RE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")
STATIC_CALENDAR_DATE_RE = re.compile(r"\b(?:\d{2}\.\d{2}\.\d{4}|20\d{2}-\d{2}-\d{2})\b")
ROLLING_DATE_BOUNDARY_SIGNAL_RE = re.compile(
    r"текущ\w*\s+дат|"
    r"больше\s+текущ\w*\s+дат|"
    r"не\s+позже\s+текущ\w*\s+дат|"
    r"будущ\w*\s+дат|"
    r"возраст|"
    r"future\s+date|current\s+date|today|tomorrow|"
    r"\bD\s*[+-]",
    flags=re.IGNORECASE,
)
ROLLING_DATE_FORMULA_RE = re.compile(
    r"(?<![A-Za-zА-Яа-яЁё])D(?![A-Za-zА-Яа-яЁё])|"
    r"текущая\s+дата\s+приложения|"
    r"дата\s+выполнения\s+теста|"
    r"current\s+application\s+date|execution\s+date|"
    r"[+-]\s*\d+\s*(?:календарн\w*\s+день|calendar\s+day)",
    flags=re.IGNORECASE,
)
FIXED_BUSINESS_DATE_CONTEXT_RE = re.compile(
    r"бизнес-дата|системн\w+\s+дат\w+\s+зафиксирован|"
    r"дата\s+проверки\s+зафиксирован|тестов\w+\s+дат\w+\s+зафиксирован|fixed\s+(?:business\s+)?date",
    flags=re.IGNORECASE,
)
REPRESENTATIVE_PARTIAL_COVERAGE_RE = re.compile(
    r"partial(?:ly)?\s+(?:representative\s+)?coverage|"
    r"sampled\s+coverage|"
    r"similar\s+fields[\s\S]{0,160}(?:same|shared)\s+(?:restriction|rule)|"
    r"covered\s+(?:only\s+)?(?:one|some)\s+of\s+(?:the\s+)?similar\s+fields|"
    r"field\s+family[\s\S]{0,160}(?:partial|sampled|representative)",
    flags=re.IGNORECASE,
)
REPRESENTATIVE_STRATEGY_RE = re.compile(
    r"representative[-_\s]?strategy|"
    r"pairwise[-_\s]?strategy|"
    r"representative\s+selection\s+rationale|"
    r"why\s+(?:this|these)\s+representative",
    flags=re.IGNORECASE,
)
REPRESENTATIVE_OMITTED_COMBINATIONS_RE = re.compile(
    r"omitted\s+combinations|excluded\s+(?:combinations|fields|classes)|"
    r"not\s+covered|not\s+selected|uncovered\s+(?:combinations|fields|classes)",
    flags=re.IGNORECASE,
)
REPRESENTATIVE_RESIDUAL_RISK_RE = re.compile(r"residual\s+risk", flags=re.IGNORECASE)
SCENARIO_RATIONALE_RE = re.compile(
    r"\*\*(?:Scenario\s+rationale|Сценарное\s+обоснование|РЎС†РµРЅР°СЂРЅРѕРµ\s+РѕР±РѕСЃРЅРѕРІР°РЅРёРµ):\*\*",
    flags=re.IGNORECASE,
)
SCENARIO_RATIONALE_FIELD_LINE_RE = re.compile(
    r"^\*\*(Scenario\s+rationale|Сценарное\s+обоснование):\*\*\s*(.*)$",
    flags=re.IGNORECASE | re.MULTILINE,
)
CANONICAL_SCENARIO_RATIONALE_FIELD_RE = re.compile(
    r"^\*\*Сценарное\s+обоснование:\*\*",
    flags=re.IGNORECASE,
)
SCENARIO_RATIONALE_GENERIC_ONLY_RE = re.compile(
    r"\b(?:one\s+visible\s+(?:ui\s+)?(?:workflow|row)|one\s+visible\s+user\s+workflow|"
    r"these\s+source\s+rows\s+form\s+one\s+visible|current\s+block|composed\s+section)\b",
    flags=re.IGNORECASE,
)
SCENARIO_RATIONALE_CONCRETE_TARGET_RE = re.compile(
    r"\b(?:BSR|GSR|Table\s+\d+|row\s+\d+|address|postal|index|phone|email|surname|first[-\s]?name|"
    r"patronymic|passport|birth[-\s]?date|citizenship|relation)\b|"
    r"адрес|индекс|телефон|почт|фамил|имя|отчеств|паспорт|дат[ауы]\s+рожд|гражданств|отношен",
    flags=re.IGNORECASE,
)
SCENARIO_RATIONALE_DOMAIN_GROUPS = (
    (
        "phone-email",
        re.compile(r"\b(?:phone|email|e-mail)\b|телефон|электронн\w*\s+почт", flags=re.IGNORECASE),
        re.compile(r"\b(?:phone|email|e-mail)\b|телефон|электронн\w*\s+почт", flags=re.IGNORECASE),
    ),
    (
        "fio",
        re.compile(r"\b(?:surname|first[-\s]?name|patronymic|fio)\b|фио|фамил|имя|отчеств", flags=re.IGNORECASE),
        re.compile(r"\b(?:surname|first[-\s]?name|patronymic|fio)\b|фио|фамил|имя|отчеств", flags=re.IGNORECASE),
    ),
    (
        "birth-date-current-date",
        re.compile(r"\b(?:birth[-\s]?date|current[-\s]?date)\b|дат[ауы]\s+рожд|текущ\w*\s+дат", flags=re.IGNORECASE),
        re.compile(r"\b(?:birth[-\s]?date|current[-\s]?date)\b|дат[ауы]\s+рожд|текущ\w*\s+дат", flags=re.IGNORECASE),
    ),
    (
        "citizenship-relation",
        re.compile(r"\b(?:citizenship|relation)\b|гражданств|отношен", flags=re.IGNORECASE),
        re.compile(r"\b(?:citizenship|relation)\b|гражданств|отношен", flags=re.IGNORECASE),
    ),
    (
        "passport-document",
        re.compile(r"\bpassport\b|сер[иия]\w*\s*/?\s*номер|паспорт", flags=re.IGNORECASE),
        re.compile(r"\bpassport\b|сер[иия]\w*\s*/?\s*номер|паспорт", flags=re.IGNORECASE),
    ),
)
PRODUCTION_TEST_CASE_METADATA_FIELDS = (
    "**Название:**",
    "**Тип:**",
    "**Приоритет:**",
    "**package_id:**",
    "**Трассировка:**",
    "**Сценарное обоснование:**",
    "**Scenario rationale:**",
    "**Предусловия:**",
    "**Тестовые данные:**",
    "**Шаги:**",
    "**Ожидаемый результат:**",
    "**Постусловия:**",
    "**Статус oracle:**",
    "**Статус тест-кейса:**",
    "**Требуется подтверждение:**",
)
VALIDATION_ERROR_EXPECTED_RE = re.compile(
    r"подсвеч|подсказ|не\s+должно\s+быть\s+принято|не\s+принимается|некорректн|ошибк|"
    r"обязательн|требует|required|error|invalid|highlight|validation",
    flags=re.IGNORECASE,
)
NORMAL_STATE_HINT_EXCEPTION_RE = re.compile(
    r"информационн\w*\s+подсказ|normal[-\s]?state\s+hint|presence\s+of\s+(?:an\s+)?informational\s+hint",
    flags=re.IGNORECASE,
)
DICTIONARY_AND_BRANCH_ASSERTION_RE = re.compile(
    r"(?:список\s+содержит|содержит\s+перечисленные\s+значения)[\s\S]{0,240}"
    r"(?:при\s+выборе|отображается\s+поле)",
    flags=re.IGNORECASE,
)
INTERNAL_ENGLISH_STRATEGY_FIELD_RE = re.compile(
    r"(?m)^\*\*(?:Representative/pairwise strategy|Omitted combinations|Residual risk):\*\*",
    flags=re.IGNORECASE,
)
NEUTRAL_VALIDATION_TRIGGER_RE = re.compile(
    r"завершить\s+ввод|перевести\s+фокус|инициир\w*\s+проверк|попытаться\s+сохранить|"
    r"move\s+focus|complete\s+input|trigger\s+validation|attempt\s+to\s+save",
    flags=re.IGNORECASE,
)
TRIGGER_BA_QUESTION_RE = re.compile(
    r"(?:BAQ|Требуется\s+подтверждение|вопрос)[\s\S]{0,160}(?:trigger|фокус|проверк|завершить\s+ввод)",
    flags=re.IGNORECASE,
)
SAVE_PERSISTENCE_COVERAGE_RE = re.compile(
    r"save\s*/\s*persistence\s+coverage\s+plan|"
    r"persist(?:ence)?\s+(?:coverage|smoke|plan)|"
    r"save\s+(?:smoke|coverage|plan)|"
    r"сохран\w*[\s\S]{0,120}(?:smoke|план|покрыт|провер|повторн\w*\s+открыт|перезагруз)",
    flags=re.IGNORECASE,
)
PERSISTENCE_OUT_OF_SCOPE_RE = re.compile(
    r"save\s*/\s*persistence\s+coverage\s+plan|out[-\s]?of[-\s]?scope[\s\S]{0,80}persist|"
    r"сохран\w*[\s\S]{0,120}(?:out[-\s]?of[-\s]?scope|вне\s+scope|не\s+входит)",
    flags=re.IGNORECASE,
)
EDITABLE_CARD_SCOPE_RE = re.compile(
    r"карточк\w*\s+заявк|application\s+card|доступн\w*\s+для\s+редакт",
    flags=re.IGNORECASE,
)
SAMPLED_GROUP_STRATEGY_RE = re.compile(
    r"Representative\s*/\s*Pairwise\s+Coverage\s+Decisions|group\s+strategy|стратег\w*\s+групп|"
    r"postal\s+indexes|phone\s+fields|email\s+restrictions|e-mail\s+restrictions|fio",
    flags=re.IGNORECASE,
)
DADATA_SELECTION_SIGNAL_RE = re.compile(
    r"dadata|подсказк|найденн\w*\s+адрес|выбр\w*\s+.*(?:адрес|suggest)|suggestion",
    flags=re.IGNORECASE,
)
INITIAL_VISIBILITY_RATIONALE_RE = re.compile(
    r"стартов\w*\s+отображ|исходн\w*\s+ui-состоя|initial\s+(?:visibility|state)|default\s+state",
    flags=re.IGNORECASE,
)
VISIBILITY_ONLY_TITLE_RE = re.compile(
    r"(?:поле|блок|field|block)[^.\n]{0,80}(?:отображ|visible|shown)|"
    r"(?:отображ|visible|shown)[^.\n]{0,80}(?:поле|блок|field|block)",
    flags=re.IGNORECASE,
)
TITLE_SCENARIO_ACTION_RE = re.compile(
    r"dadata|принима\w*|выбр\w*|selection|accept",
    flags=re.IGNORECASE,
)
CANDIDATE_TRIGGER_TOO_SPECIFIC_RE = re.compile(
    r"перевести\s+фокус[\s\S]{0,80}(?:чтобы|для)\s+инициир|move\s+focus[\s\S]{0,80}trigger",
    flags=re.IGNORECASE,
)
CANDIDATE_TRIGGER_ALTERNATIVE_RE = re.compile(
    r"\bили\b|\bor\b|доступн\w*\s+в\s+ui|выполнить\s+действие|при\s+вводе|сохранени|переходе\s+дальше|другом\s+действии",
    flags=re.IGNORECASE,
)
COVERAGE_MATRIX_REQUIRED_GROUP_COLUMNS = {
    "fields",
    "shared_restriction",
    "source_rows_bsr",
    "selected_strategy",
    "tc_ids",
    "covered_classes",
    "omitted_combinations",
    "residual_risk",
    "reason",
}
FIELD_LEVEL_CANARY_RE = re.compile(r"field[-\s]?level|risk[-\s]?based", flags=re.IGNORECASE)
PERSISTENCE_SCOPE_NOTE_RE = re.compile(
    r"(?:persist|save)[\s\S]{0,160}(?:follow[-\s]?up|out\s+of\s+scope|separate\s+(?:suite|smoke)|not\s+a\s+full)|"
    r"(?:follow[-\s]?up|out\s+of\s+scope|separate\s+(?:suite|smoke)|not\s+a\s+full)[\s\S]{0,160}(?:persist|save)",
    flags=re.IGNORECASE,
)
PERSISTENCE_TC_SIGNAL_RE = re.compile(
    r"persist|save\s*/\s*reopen|save\s+and\s+reopen|saved\s+value|reopen(?:ed)?\s+card|"
    r"сохран\w*[\s\S]{0,80}(?:повторн\w*\s+откры|отображ|значен|карточ)|"
    r"повторн\w*\s+откры[\s\S]{0,80}(?:сохран\w*|значен)",
    flags=re.IGNORECASE,
)
PERSISTENCE_CANDIDATE_STATUS_RE = re.compile(
    r"candidate-persistence-calibration",
    flags=re.IGNORECASE,
)
PERSISTENCE_CALIBRATION_LINK_RE = re.compile(
    r"BA-PS-\d{3}|persistence-save-flow|ba-ui-calibration-questions|calibration\s+package",
    flags=re.IGNORECASE,
)
PERSISTENCE_SAVE_FLOW_CONFIRMED_RE = re.compile(
    r"save[-\s]?flow\s*[:=]\s*confirmed|save\s+flow\s+confirmed|"
    r"exact\s+save\s+action\s*[:=]\s*(?!not\s+found)(?:confirmed|source-backed|found)|"
    r"точн\w*\s+действ\w*\s+сохран\w*[\s\S]{0,80}(?:подтвержден|source-backed)",
    flags=re.IGNORECASE,
)
PERSISTENCE_SAVE_FLOW_UNCONFIRMED_RE = re.compile(
    r"save[-\s]?flow-calibration-required|exact\s+save\s+action\s+(?:is\s+)?not\s+source-backed|"
    r"exact\s+save\s+action\s+found\s*\|\s*no|save\s+success\s+oracle\s+found\s*\|\s*no|"
    r"exit-after-save\s+flow\s+found\s*\|\s*no|cleanup/isolation\s+found\s*\|\s*no|"
    r"точн\w*\s+UI-механизм\s+сохран\w*[\s\S]{0,120}не\s+найден|"
    r"точн\w*\s+действ\w*\s+сохран\w*[\s\S]{0,120}не\s+source-backed",
    flags=re.IGNORECASE,
)
PERSISTENCE_SAVE_PLACEHOLDER_RE = re.compile(
    r"подтвержденн\w*\s+(?:для\s+[^.\n]{0,80}\s+)?способ\w*|source-backed\s+способ|confirmed\s+method",
    flags=re.IGNORECASE,
)
PERSISTENCE_RELATION_CLIENT_RE = re.compile(r"Отношение\s+к\s+клиенту", flags=re.IGNORECASE)
PERSISTENCE_RELATION_APPLICANT_RE = re.compile(r"Отношение\s+к\s+заявителю", flags=re.IGNORECASE)
PERSISTENCE_TERMINOLOGY_MAPPING_RE = re.compile(
    r"Terminology evidence|terminology\s+mapping|source-backed\s+term|терминолог\w*\s+mapping|"
    r"source-backed\s+terminology|UI\s+alias",
    flags=re.IGNORECASE,
)
PERSISTENCE_CALIBRATION_PACKAGE_REQUIRED_FILES = (
    "ba-ui-calibration-questions.md",
    "persistence-tc-conversion-plan.md",
    "save-flow-calibration-checklist.md",
    "persistence-calibration-evaluation-report.md",
)
PERSISTENCE_SAVE_ACTION_RE = re.compile(
    r"\bsave\b|save\s+card|save\s+application|сохран\w*\s+(?:карточк|заявк|данн|изменен|значен)",
    flags=re.IGNORECASE,
)
PERSISTENCE_REOPEN_ACTION_RE = re.compile(
    r"(?:close|leave|exit|reload|refresh|reopen)[\s\S]{0,180}(?:reopen|reload|refresh|open\s+the\s+same\s+card|same\s+card)|"
    r"(?:закры|покин|перезагруз)[\s\S]{0,180}(?:повторн\w*\s+откры|открыть\s+ту\s+же|перезагруз)",
    flags=re.IGNORECASE,
)
PERSISTENCE_REOPEN_VERIFICATION_RE = re.compile(
    r"(?:after|после)\s+(?:reopen|reload|refresh|повторн\w*\s+откры|перезагруз)[\s\S]{0,180}"
    r"(?:display|shown|visible|saved|отображ|видн|сохран)",
    flags=re.IGNORECASE,
)
PERSISTENCE_CLOSE_WITHOUT_SAVE_RE = re.compile(
    r"close\s+without\s+sav|without\s+saving|закры\w*[\s\S]{0,60}без\s+сохран|без\s+сохран\w*[\s\S]{0,60}закры",
    flags=re.IGNORECASE,
)
PERSISTENCE_CONCRETE_UNSOURCED_SAVE_RE = re.compile(
    r"(?:click|press|select|tap)\s+(?:the\s+)?[`\"']?(?:save|сохранить)[`\"']?|"
    r"(?:нажать|выбрать|кликнуть)\s+(?:кнопк\w*\s+)?[`\"'«]?(?:сохранить|сохранение|сохранить заявку)[`\"'»]?",
    flags=re.IGNORECASE,
)
PERSISTENCE_SAVE_SOURCE_OR_CONFIRMATION_RE = re.compile(
    r"source[-\s]?backed|source\s+inventory|подтвержден\w*|Требуется\s+подтверждение[\s\S]{0,180}сохран|"
    r"BA\s+question[\s\S]{0,180}save|вопрос[\s\S]{0,180}сохран",
    flags=re.IGNORECASE,
)
PERSISTENCE_CLEANUP_STRATEGY_RE = re.compile(
    r"cleanup|isolation|restore|delete\s+test|reset|вернуть|восстанов|удалить\s+тест|очистить|изолирован",
    flags=re.IGNORECASE,
)
PERSISTENCE_PASSIVE_PRECONDITION_RE = re.compile(
    r"(?m)^\s*(?:\d+\.\s*)?(?:"
    r"(?:application|card|form|block|field|record|entity|contact|phone|address)[^\n]{0,80}\b(?:is|are)\s+(?:open|opened|available|filled|created|present|displayed|selected|set|exists)\b|"
    r"(?:existing|created|available|filled|selected)\s+(?:application|card|form|block|field|record|entity|contact|phone|address)\b|"
    r"(?:Открыт|Открыта|Открыто|Открыты|Заполнен|Заполнена|Заполнено|Заполнены|Создан|Создана|Создано|Созданы|Выбран|Выбрана|Выбрано|Выбраны)\b|"
    r"(?:В\s+блоке|На\s+форме)[^\n]{0,120}\b(?:есть|отображается|заполнен|заполнена|создан)"
    r")",
    flags=re.IGNORECASE,
)
PERSISTENCE_TRACE_NOT_EXERCISED_RULES: tuple[tuple[str, re.Pattern[str], re.Pattern[str]], ...] = (
    (
        "BSR 119",
        re.compile(r"\bBSR\s*119\b", flags=re.IGNORECASE),
        re.compile(r"ручн|manual|decompos|разлож|компонент|пол[ея]", flags=re.IGNORECASE),
    ),
    (
        "BSR 148",
        re.compile(r"\bBSR\s*148\b", flags=re.IGNORECASE),
        re.compile(r"ручн|manual|видим|visibility", flags=re.IGNORECASE),
    ),
    (
        "BSR 167",
        re.compile(r"\bBSR\s*167\b", flags=re.IGNORECASE),
        re.compile(r"добав\w*\s+(?:телефон|phone)|add\s+(?:phone|telephone)|кнопк\w*\s+добав", flags=re.IGNORECASE),
    ),
)
PERSISTENCE_DELETE_TC_SIGNAL_RE = re.compile(
    r"delete|deleted|deletion|remove|removed|removal|удал\w*",
    flags=re.IGNORECASE,
)
PERSISTENCE_DELETE_SELF_CONTAINED_SETUP_RE = re.compile(
    r"(?:add|create|созда|добав)[\s\S]{0,240}(?:save|сохран)[\s\S]{0,240}"
    r"(?:reopen|open\s+the\s+same|повторн\w*\s+откры|открыть\s+ту\s+же)[\s\S]{0,240}"
    r"(?:verify|ensure|убедиться|проверить|отображ)",
    flags=re.IGNORECASE,
)
PERSISTENCE_DELETE_FIXTURE_RE = re.compile(
    r"fixture|test\s+fixture|defined\s+test\s+data|предопределенн\w*\s+фикстур|определенн\w*\s+фикстур",
    flags=re.IGNORECASE,
)
ROLLING_DATE_UNFORMALIZED_RELATIVE_RE = re.compile(
    r"\bD\s*[-+]\s*\d+\s*(?:years?|лет|год|года|calendar\s+years?)\b",
    flags=re.IGNORECASE,
)
ROLLING_DATE_FORMALIZATION_RE = re.compile(
    r"(?:DD\.MM\.YYYY|ДД\.ММ\.ГГГГ)[\s\S]{0,220}(?:example|пример|\d{2}\.\d{2}\.\d{4})|"
    r"(?:example|пример|\d{2}\.\d{2}\.\d{4})[\s\S]{0,220}(?:DD\.MM\.YYYY|ДД\.ММ\.ГГГГ)",
    flags=re.IGNORECASE,
)
PERSISTENCE_GROUPED_PHONE_EMAIL_RE = re.compile(
    r"(?:phone|телефон|мобильн)[\s\S]{0,420}(?:e-?mail|email|электронн)|"
    r"(?:e-?mail|email|электронн)[\s\S]{0,420}(?:phone|телефон|мобильн)",
    flags=re.IGNORECASE,
)
PERSISTENCE_GROUPED_SMOKE_RISK_RE = re.compile(
    r"(?:grouped|representative|smoke|сгрупп|минимальн)[\s\S]{0,260}(?:residual\s+risk|остаточн\w*\s+риск|риск)|"
    r"(?:residual\s+risk|остаточн\w*\s+риск|риск)[\s\S]{0,260}(?:grouped|representative|smoke|сгрупп|минимальн)",
    flags=re.IGNORECASE,
)
SOURCE_BACKED_UI_TERM_INCONSISTENCY_RE = re.compile(
    r"(?:Контакты клиента[\s\S]{0,1200}Контактная информация|Контактная информация[\s\S]{0,1200}Контакты клиента|"
    r"Контактные лица[\s\S]{0,1200}[`\"'«]Контактное лицо[`\"'»]|[`\"'«]Контактное лицо[`\"'»][\s\S]{0,1200}Контактные лица)",
    flags=re.IGNORECASE,
)
SOURCE_BACKED_UI_TERM_DECISION_RE = re.compile(
    r"UI\s+Block\s+Naming|UI\s+block\s+naming|source-backed\s+term|Блок\s+«Контакты клиента»|Блок\s+«Контактные лица»",
    flags=re.IGNORECASE,
)
GENERATED_ARTIFACT_SOLE_SOURCE_RE = re.compile(
    r"(?:generated|previous|old|v\d+)[^\n.;|]{0,120}"
    r"(?:used\s+as|is|was|treated\s+as|became)[^\n.;|]{0,60}"
    r"(?:source\s+of\s+truth|authoritative\s+source|sole\s+source|only\s+source)|"
    r"(?:decisions?|coverage|tc|test[-\s]?cases?|representative\s+strategy)[^\n.;|]{0,120}"
    r"(?:derived|based|copied|taken)[^\n.;|]{0,80}"
    r"(?:only|solely|exclusively)[^\n.;|]{0,80}"
    r"(?:generated|previous|old|v\d+|wide[-\s]?canary)",
    flags=re.IGNORECASE,
)
GENERATED_ARTIFACT_DECISION_BASIS_RE = re.compile(
    r"(?:generated|previous|old|v\d+|wide[-\s]?canary)[^\n.;|]{0,120}"
    r"(?:basis|source|input|used)[^\n.;|]{0,80}"
    r"(?:decisions?|coverage|tc|test[-\s]?cases?|representative|atomicity)|"
    r"(?:decisions?|coverage|tc|test[-\s]?cases?|representative|atomicity)[^\n.;|]{0,120}"
    r"(?:generated|previous|old|v\d+|wide[-\s]?canary)",
    flags=re.IGNORECASE,
)
GENERATED_ARTIFACT_FAILURE_FIXTURE_RE = re.compile(
    r"failure\s+fixture|diagnostic(?:/failure)?\s+fixture|diagnostic\s+input|"
    r"not\s+(?:a\s+)?source\s+of\s+truth|not\s+as\s+(?:a\s+)?source\s+of\s+truth|"
    r"diagnostic\s+result\s+only",
    flags=re.IGNORECASE,
)
SOURCE_BASIS_CROSS_CHECK_RE = re.compile(
    r"\b(?:BSR|GSR)\s+\d+\b|\bREQ[-\s]?\d+\b|source\s+rows?|source\s+artifact|"
    r"FT4AutoFinFinal|\.xhtml|\.docx|main_ft|ФТ|cross[-\s]?check|Table\s+\d+\s+row",
    flags=re.IGNORECASE,
)
VALID_TEST_DATA_VALUE_RE = re.compile(
    r"(?<![A-Za-z\u0410-\u042f\u0430-\u044f\u0401\u0451])(?:valid(?:\s+value)?|allowed(?:\s+value)?|"
    r"\u0434\u043e\u043f\u0443\u0441\u0442\u0438\u043c\w*\s+\u0437\u043d\u0430\u0447\u0435\u043d\w*)\s*:\s*`?([^`;\n]+)`?",
    flags=re.IGNORECASE,
)
VALID_TEST_DATA_CLASS_RE = re.compile(
    r"(?:class|\u043a\u043b\u0430\u0441\u0441)\s*:\s*`?([^`;\n.]+)`?",
    flags=re.IGNORECASE,
)
NUMERIC_PARAMETER_VALUE_RE = re.compile(
    r"(?:p_)?(?:min|max)(?:\s*[-+]\s*(?:delta|1|\d+))?|delta|n(?:[-+]\d+)?|"
    r"\d+(?:[\s.,]\d+)*(?:[.,]\d+)?",
    flags=re.IGNORECASE,
)
ACTION_CONTROL_CONTEXT_RE = re.compile(
    r"\b(?:button|action|next\s+step|back|edit|retry)\b|"
    r"\u043a\u043d\u043e\u043f\u043a|\u0421\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u0439\s+\u0448\u0430\u0433|"
    r"\u041d\u0430\u0437\u0430\u0434|\u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c|"
    r"\u041f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c|\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c\s+\u043f\u043e\u0432\u0442\u043e\u0440\u043d\u043e",
    flags=re.IGNORECASE,
)
ACTION_CONTROL_AS_FIELD_RE = re.compile(
    r"(?:Следующий\s+шаг|Назад|Редактировать|Отправить\s+повторно|button|action|"
    r"кнопк[^\n.;]{0,40}Проверить|`Проверить`)"
    r"[\s\S]{0,140}(?:как\s+обязател\w+\s+пол|обрабатыва\w+[\s\S]{0,80}как\s+обязател\w+\s+пол|пуст|empty|required\s+field)",
    flags=re.IGNORECASE,
)
ACTION_EMPTY_CONTROL_MISUSE_RE = re.compile(
    r"(?:\u043e\u0441\u0442\u0430\u0432\u0438\w+|leave)[^\n.;]{0,80}"
    r"(?:\u0421\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u0439\s+\u0448\u0430\u0433|\u041d\u0430\u0437\u0430\u0434|"
    r"\u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c|\u041f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c|"
    r"\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c\s+\u043f\u043e\u0432\u0442\u043e\u0440\u043d\u043e|button|action)[^\n.;]{0,80}"
    r"(?:\u043f\u0443\u0441\u0442|empty)",
    flags=re.IGNORECASE,
)
VALID_FIXTURE_CONTEXT_RE = re.compile(
    r"\bVALID_[A-Z0-9_]+\b|full\s+valid|valid\s+fixture|"
    r"валидн\w+\s+(?:fixture|набор|баз|сценар)|"
    r"все\s+поля,\s+кроме\s+проверяемого,\s+заполнены\s+валидн\w*|"
    r"(?:все\s+)?остальн\w+\s+обязательн\w+\s+пол[яе]\s+[^.\n;]{0,80}(?:заполн|валид)",
    flags=re.IGNORECASE,
)
NEXT_STEP_ACTION_RE = re.compile(r"Следующий\s+шаг|next\s+step|continue|продолж", flags=re.IGNORECASE)
INTEGRATION_GAP_EVIDENCE_RE = re.compile(
    r"(?:gap-\d+[\s\S]{0,260}(?:api|rabbitmq|dadata|kladr|connect|internal|backend|model|database|db|async|"
    r"\u0438\u043d\u0442\u0435\u0433\u0440\u0430\u0446|\u0441\u043f\u0440\u0430\u0432\u043e\u0447\u043d|\u0432\u043d\u0435\u0448\u043d)|"
    r"(?:api|rabbitmq|dadata|kladr|connect|internal|backend|model|database|db|async|"
    r"\u0438\u043d\u0442\u0435\u0433\u0440\u0430\u0446|\u0441\u043f\u0440\u0430\u0432\u043e\u0447\u043d|\u0432\u043d\u0435\u0448\u043d)[\s\S]{0,260}gap-\d+)",
    flags=re.IGNORECASE,
)
INTEGRATION_RELATED_DIMENSIONS = {
    "integration",
    "api-server-validation",
    "async",
    "persistence",
}

APPLICABILITY_LINKED_TC_DIMENSION_CONTEXT_RE = {
    "numeric": re.compile(
        r"\bnumeric\b|\bdigits?\b|\bnumber\b|числов|цифр|только\s+(?:числ|цифр)|\b\d{2,}\b",
        flags=re.IGNORECASE,
    ),
    "length": re.compile(
        r"\blength\b|длин|n-1|n\+1|коротк|длинн|\b\d+\s*(?:digit|digits|цифр|символ)",
        flags=re.IGNORECASE,
    ),
    "format": re.compile(
        r"\bformat\b|формат|маск|mask|шаблон|xxx|@\b|email|почт",
        flags=re.IGNORECASE,
    ),
    "table-list": re.compile(
        r"\blist\b|\bdictionary\b|список|справочн|перечень|значени|checkbox|чекбокс",
        flags=re.IGNORECASE,
    ),
}

MASK_OBLIGATION_CLASS_RE = re.compile(r"mask|маск|шаблон", flags=re.IGNORECASE)
MASK_OBSERVABLE_ORACLE_RE = re.compile(
    r"mask|маск|шаблон|формат|xxx|x{2,}\s*[-–—]\s*x{2,}|\d{2,}\s*[-–—]\s*\d{2,}|\+7\s*\(",
    flags=re.IGNORECASE,
)


def max_requirement_range_span(value: str) -> int:
    max_span = 1
    for match in REQUIREMENT_CODE_RANGE_RE.finditer(value):
        start = int(match.group(2))
        end = int(match.group(3))
        if end >= start:
            max_span = max(max_span, end - start + 1)
    return max_span


def extract_requirement_codes_from_text(value: str) -> list[str]:
    codes: list[str] = []
    occupied_spans: list[tuple[int, int]] = []

    def add_code(prefix: str, number: int) -> None:
        normalized_prefix = prefix.upper()
        if normalized_prefix in NON_REQUIREMENT_CODE_PREFIXES:
            return
        code = f"{normalized_prefix} {number}"
        if code not in codes:
            codes.append(code)

    for match in REQUIREMENT_CODE_RANGE_RE.finditer(value):
        prefix = match.group(1)
        start = int(match.group(2))
        end = int(match.group(3))
        occupied_spans.append(match.span())
        if end >= start and end - start <= 500:
            for number in range(start, end + 1):
                add_code(prefix, number)
        else:
            add_code(prefix, start)
            add_code(prefix, end)

    for match in REQUIREMENT_CODE_TOKEN_RE.finditer(value):
        start, end = match.span()
        if any(range_start <= start and end <= range_end for range_start, range_end in occupied_spans):
            continue
        add_code(match.group(1), int(match.group(2)))

    return codes


def atom_compression_marker_names(text: str) -> list[str]:
    return [
        name
        for name, pattern in ATOM_COMPRESSION_MARKERS.items()
        if pattern.search(text)
    ]


def extract_test_case_table_field(block: str, field_names: list[str]) -> str:
    normalized_names = {
        re.sub(r"\s+", " ", name.strip().strip("`*_")).casefold()
        for name in field_names
    }
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or set(stripped.replace("|", "").strip()) <= {"-", ":", " "}:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue
        field_label = re.sub(r"\s+", " ", cells[0].strip().strip("`*_")).casefold()
        if field_label in normalized_names:
            return cells[1].strip()
    return ""


def extract_test_case_field_block(block: str, field_names: list[str]) -> str:
    aliases_by_casefold_name = {
        "title": ["\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435"],
        "goal": ["\u0426\u0435\u043b\u044c"],
        "preconditions": ["\u041f\u0440\u0435\u0434\u0443\u0441\u043b\u043e\u0432\u0438\u044f"],
        "test data": ["\u0422\u0435\u0441\u0442\u043e\u0432\u044b\u0435 \u0434\u0430\u043d\u043d\u044b\u0435"],
        "test_data": ["\u0422\u0435\u0441\u0442\u043e\u0432\u044b\u0435 \u0434\u0430\u043d\u043d\u044b\u0435"],
        "steps": ["\u0428\u0430\u0433\u0438"],
        "postconditions": ["\u041f\u043e\u0441\u0442\u0443\u0441\u043b\u043e\u0432\u0438\u044f"],
        "traceability": ["\u0422\u0440\u0430\u0441\u0441\u0438\u0440\u043e\u0432\u043a\u0430"],
        "ft reference": ["\u0421\u0441\u044b\u043b\u043a\u0430 \u043d\u0430 \u0424\u0422"],
        "ft_reference": ["\u0421\u0441\u044b\u043b\u043a\u0430 \u043d\u0430 \u0424\u0422"],
        "requirement source": ["\u0418\u0441\u0442\u043e\u0447\u043d\u0438\u043a \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u044f"],
        "requirement_source": ["\u0418\u0441\u0442\u043e\u0447\u043d\u0438\u043a \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u044f"],
        "requirement quote": ["\u0418\u0441\u0442\u043e\u0447\u043d\u0438\u043a / \u0446\u0438\u0442\u0430\u0442\u0430 \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u044f"],
        "requirement source quote": ["\u0418\u0441\u0442\u043e\u0447\u043d\u0438\u043a / \u0446\u0438\u0442\u0430\u0442\u0430 \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u044f"],
        "source requirement quote": ["\u0418\u0441\u0442\u043e\u0447\u043d\u0438\u043a / \u0446\u0438\u0442\u0430\u0442\u0430 \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u044f"],
        "status": ["\u0421\u0442\u0430\u0442\u0443\u0441"],
    }
    expanded_field_names = list(field_names)
    for name in field_names:
        normalized_name = re.sub(r"\s+", " ", name.strip().strip("`*_")).casefold()
        for alias in aliases_by_casefold_name.get(normalized_name, []):
            if alias not in expanded_field_names:
                expanded_field_names.append(alias)
    names_pattern = "|".join(re.escape(name) for name in expanded_field_names)
    match = re.search(
        rf"^\*\*(?:{names_pattern}):\*\*\s*(.*)$",
        block,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if not match and any(name.lower() == "steps" or name == "Шаги" for name in expanded_field_names):
        match = re.search(
            rf"^(?:{names_pattern}):\s*$",
            block,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        if not match:
            return extract_test_case_table_field(block, expanded_field_names)
        start = match.end()
    else:
        if not match:
            return extract_test_case_table_field(block, expanded_field_names)
        start = match.start(1)
    next_field = re.search(
        r"^(?:\*\*[^*\n]+:\*\*|(?:Steps|steps|Шаги):\s*$)",
        block[match.end() :],
        flags=re.IGNORECASE | re.MULTILINE,
    )
    end = match.end() + next_field.start() if next_field else len(block)
    return block[start:end].strip()


def is_ui_calibration_candidate_block(block: str) -> bool:
    return bool(
        UI_CALIBRATION_REQUIRED_RE.search(block)
        or CANDIDATE_UI_CALIBRATION_RE.search(block)
    )


def candidate_has_concrete_invalid_value(test_data: str, steps: str) -> bool:
    if CONCRETE_BACKTICK_VALUE_RE.search(test_data or ""):
        return True
    for match in ENTER_CONCRETE_VALUE_RE.finditer(steps or ""):
        value = match.group(1).strip()
        matched_text = match.group(0)
        if GENERIC_INVALID_VALUE_TEXT_RE.search(matched_text):
            continue
        if value and not GENERIC_INVALID_VALUE_TEXT_RE.search(value):
            return True
    return False


def validate_ui_calibration_candidate_test_cases(
    blocks: list[tuple[str, str]],
    path: Path,
    root: Path,
) -> tuple[list[Finding], list[Check]]:
    display_path = rel(path, root)
    missing_markers: list[str] = []
    missing_confirmation_questions: list[str] = []
    missing_concrete_values: list[str] = []
    invented_reactions: list[str] = []
    for test_case_id, block in blocks:
        if not is_ui_calibration_candidate_block(block):
            continue
        has_oracle_status = bool(UI_CALIBRATION_REQUIRED_RE.search(block))
        has_candidate_status = bool(CANDIDATE_UI_CALIBRATION_RE.search(block))
        has_calibration_note = bool(UI_CALIBRATION_NOTE_RE.search(block))
        confirmation_match = CANDIDATE_CONFIRMATION_FIELD_RE.search(block)
        if not (has_oracle_status and has_candidate_status and has_calibration_note):
            missing = []
            if not has_oracle_status:
                missing.append("oracle_status/ui-calibration-required")
            if not has_candidate_status:
                missing.append("candidate-ui-calibration")
            if not has_calibration_note:
                missing.append("Требуется подтверждение")
            missing_markers.append(f"{test_case_id}:missing={', '.join(missing)}")
        if not confirmation_match or GENERIC_CONFIRMATION_QUESTION_RE.fullmatch(confirmation_match.group(1).strip()):
            missing_confirmation_questions.append(f"{test_case_id}:missing specific confirmation question")

        test_data = extract_test_case_field_block(block, ["Тестовые данные", "Test Data", "test_data", "test data"])
        steps = extract_test_case_field_block(block, ["Шаги", "Steps", "steps"])
        if not candidate_has_concrete_invalid_value(test_data, steps):
            missing_concrete_values.append(
                f"{test_case_id}:test_data={test_data[:120] or '-'}; steps={steps[:120] or '-'}"
            )

        expected_result = extract_test_case_field_block(
            block,
            ["Итоговый ожидаемый результат", "Ожидаемый результат", "Expected Result"],
        )
        if (
            has_oracle_status
            and expected_result
            and CONCRETE_UI_REACTION_WITHOUT_EVIDENCE_RE.search(expected_result)
            and not UI_CALIBRATION_ALLOWED_EXPECTED_RE.search(expected_result)
        ):
            invented_reactions.append(f"{test_case_id}:expected={expected_result[:180]}")

    findings: list[Finding] = []
    if missing_markers:
        findings.append(
            Finding(
                id="test-case-ui-calibration-candidate-missing-marker",
                severity="warning",
                category="test-case-format",
                title="UI calibration candidate test cases miss required markers",
                details=(
                    "A candidate TC must explicitly expose `ui-calibration-required`, "
                    "`candidate-ui-calibration` and a specific confirmation question."
                ),
                path=display_path,
                evidence=missing_markers[:20],
                recommended_action=(
                    "Add `Статус oracle: ui-calibration-required`, `Статус тест-кейса: "
                    "candidate-ui-calibration`, and `Требуется подтверждение: <specific missing oracle question>`."
                ),
            )
        )
    if missing_confirmation_questions:
        findings.append(
            Finding(
                id="test-case-ui-calibration-candidate-missing-confirmation-question",
                severity="warning",
                category="test-case-format",
                title="UI calibration candidate has no specific confirmation question",
                details=(
                    "Candidate status is useful only when it states the exact missing oracle that BA/UI calibration "
                    "must resolve."
                ),
                path=display_path,
                evidence=missing_confirmation_questions[:20],
                recommended_action="Add `Требуется подтверждение: <specific missing oracle question>` to the candidate body.",
            )
        )
    if missing_concrete_values:
        findings.append(
            Finding(
                id="test-case-ui-calibration-candidate-missing-concrete-invalid-value",
                severity="warning",
                category="test-case-format",
                title="UI calibration candidate has no concrete invalid value",
                details=(
                    "A candidate negative TC must still exercise a representative invalid class. Generic wording "
                    "such as `invalid value` is not executable manual test data."
                ),
                path=display_path,
                evidence=missing_concrete_values[:20],
                recommended_action="Put a concrete representative invalid value in `Тестовые данные` or in the validation action step.",
            )
        )
    if invented_reactions:
        findings.append(
            Finding(
                id="test-case-ui-calibration-candidate-invents-ui-reaction",
                severity="warning",
                category="expected-result",
                title="UI calibration candidate asserts a concrete UI reaction",
                details=(
                    "`ui-calibration-required` means the exact UI reaction is not known yet. "
                    "The expected result may state that invalid/empty input must not be accepted, "
                    "but must not invent a concrete message, highlight, filtering, blocked transition or save behavior."
                ),
                path=display_path,
                evidence=invented_reactions[:20],
                recommended_action="Replace the invented UI reaction with the canonical calibration wording.",
            )
        )
    has_findings = bool(missing_markers or missing_confirmation_questions or missing_concrete_values or invented_reactions)
    return findings, [
        Check(
            "test-case-ui-calibration-candidates",
            "warn" if has_findings else "pass",
            "UI calibration candidate markers have issues." if has_findings else "UI calibration candidate markers passed.",
            display_path,
        )
    ]


def generic_test_case_smell_matches(test_case_id: str, field_values: list[tuple[str, str]]) -> list[str]:
    matches: list[str] = []
    for field_name, value in field_values:
        if not value:
            continue
        inspected_value = value
        if field_name == "steps":
            inspected_value = re.split(
                (
                    r"(?im)^\s*(?:"
                    r"Expected Result|expected_result|expected result|"
                    r"\u0418\u0442\u043e\u0433\u043e\u0432\u044b\u0439\s+\u043e\u0436\u0438\u0434\u0430\u0435\u043c\u044b\u0439\s+\u0440\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442|"
                    r"\u041e\u0436\u0438\u0434\u0430\u0435\u043c\u044b\u0439\s+\u0440\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442|"
                    r"Postconditions|postconditions|\u041f\u043e\u0441\u0442\u0443\u0441\u043b\u043e\u0432\u0438\u044f"
                    r"):\s*"
                ),
                value,
                maxsplit=1,
            )[0]
        for pattern in GENERIC_TC_SMELL_PATTERNS:
            if pattern is GENERIC_TC_NOT_REQUIRED_RE and field_name != "steps":
                continue
            match = pattern.search(inspected_value)
            if not match:
                continue
            snippet = re.sub(r"\s+", " ", match.group(0).strip())
            matches.append(f"{test_case_id}:field={field_name}; match={snippet[:140]}")
    return matches


TEST_CASE_PLAIN_FIELD_BOUNDARY_RE = re.compile(
    (
        r"(?im)^\s*(?:"
        r"Expected Result|expected_result|expected result|"
        r"\u0418\u0442\u043e\u0433\u043e\u0432\u044b\u0439\s+\u043e\u0436\u0438\u0434\u0430\u0435\u043c\u044b\u0439\s+\u0440\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442|"
        r"\u041e\u0436\u0438\u0434\u0430\u0435\u043c\u044b\u0439\s+\u0440\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442|"
        r"Postconditions|postconditions|\u041f\u043e\u0441\u0442\u0443\u0441\u043b\u043e\u0432\u0438\u044f"
        r"):\s*"
    )
)


def trim_test_case_plain_field_boundary(value: str) -> str:
    return TEST_CASE_PLAIN_FIELD_BOUNDARY_RE.split(value, maxsplit=1)[0].strip()


def normalize_test_case_ref_tokens(value: str) -> list[str]:
    normalized = value.replace("`", "")
    return [
        re.sub(r"\s+", " ", part.strip()).casefold()
        for part in normalized.split(";")
        if part.strip()
    ]


def normalized_text_for_comparison(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("`", "").strip()).casefold()


ACTION_CREATED_BLOCK_RE = re.compile(
    r"\b(?:click|press)\s+(?:the\s+)?`?(?:add|create)\b|"
    r"\u043d\u0430\u0436\u0430\u0442\u044c\s+(?:\u043a\u043d\u043e\u043f\u043a\u0443\s+)?`?\u0434\u043e\u0431\u0430\u0432\u0438\u0442\u044c\b|"
    r"\u0434\u043e\u0431\u0430\u0432\u0438\u0442\u044c\s+(?:\u0431\u043b\u043e\u043a|"
    r"\u0434\u043e\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b|\u0440\u0430\u0431\u043e\u0442)",
    flags=re.IGNORECASE,
)

INPUT_FILTERING_ORACLE_SUPPLEMENTAL_RE = re.compile(
    r"field\s+[^.\n;]{0,80}clear(?:ed|s)|(?:does\s+not|not)\s+display|(?:does\s+not|not)\s+show|"
    r"entered\s+value\s+[^.\n;]{0,80}(?:does\s+not|not)\s+(?:display|show|appear)|"
    r"\u043f\u043e\u043b\u0435\s+[^.\n;]{0,80}\u043e\u0447\u0438\u0449\w+|"
    r"\u0432\u0432\u0435\u0434\w+\s+\u0437\u043d\u0430\u0447\u0435\u043d\w+\s+[^.\n;]{0,100}\u043d\u0435\s+\u043e\u0442\u043e\u0431\u0440\u0430\u0436\w+|"
    r"\u0437\u043d\u0430\u0447\u0435\u043d\w+\s+[^.\n;]{0,100}\u043d\u0435\s+\u043e\u0442\u043e\u0431\u0440\u0430\u0436\w+|"
    r"\u043d\u0435\s+\u043e\u0442\u043e\u0431\u0440\u0430\u0436\w+[^.\n;]{0,100}(?:\u0432\u0432\u0435\u0434\w+\s+)?\u0437\u043d\u0430\u0447\u0435\u043d",
    flags=re.IGNORECASE,
)

ACTION_CREATED_BLOCK_CLEANUP_RE = re.compile(
    r"\bdelete\b|\bremove\b|\btrash\b|\bdiscard\b|without\s+sav|"
    r"\u0443\u0434\u0430\u043b\u0438\w+|\u043a\u043e\u0440\u0437\u0438\u043d|"
    r"\u0437\u0430\u043a\u0440\u044b\w+[^\n]{0,80}\u0431\u0435\u0437\s+\u0441\u043e\u0445\u0440\u0430\u043d|"
    r"\u0431\u0435\u0437\s+\u0441\u043e\u0445\u0440\u0430\u043d",
    flags=re.IGNORECASE,
)

NO_POSTCONDITIONS_RE = re.compile(
    r"^\s*(?:not\s+required|none|n/a|"
    r"\u043d\u0435\s+\u0442\u0440\u0435\u0431\u0443\u044e\u0442\u0441\u044f|"
    r"\u043d\u0435\s+\u0442\u0440\u0435\u0431\u0443\u0435\u0442\u0441\u044f)"
    r"\.?\s*$",
    flags=re.IGNORECASE,
)

BRANCH_CHOICE_RE = re.compile(
    r"`?(yes|no|confirm|cancel|save|discard|да|нет)`?",
    flags=re.IGNORECASE,
)

SYNTHETIC_QUOTE_RE = re.compile(
    r"\bDICT-\d{3,}\b|\bGAP-\d{3,}\b|"
    r"derived|normalized|точн\w*\s+UI-\w*|"
    r"использу\w+\s+все\s+и\s+только\s+активн\w+\s+значен",
    flags=re.IGNORECASE,
)

MULTI_INVALID_CLASS_RE = re.compile(
    r"\bfor\s+each\b|\beach\s+value\b|"
    r"\u043a\u0430\u0436\u0434\w+\s+(?:\u043d\u0435\u0434\u043e\u043f\u0443\u0441\u0442\u0438\u043c\w+\s+)?(?:\u0437\u043d\u0430\u0447\u0435\u043d|\u0432\u0432\u043e\u0434)|"
    r"\u0434\u043b\u044f\s+\u043a\u0430\u0436\u0434\w+\s+"
    r"(?:\u043f\u0440\u043e\u0432\u0435\u0440\u044f\u0435\u043c\w+\s+)?"
    r"(?:\u0437\u043d\u0430\u0447\u0435\u043d|\u0432\u0432\u043e\u0434)|"
    r"\u043f\u043e\s+\u043e\u0447\u0435\u0440\u0435\u0434\u0438",
    flags=re.IGNORECASE,
)

NON_REPRODUCIBLE_PRECONDITION_STATE_RE = re.compile(
    r"(?:отображается\s+подсказк|дождаться\s+отображени[яю]\s+подсказк|"
    r"убедиться[^.\n;]{0,120}(?:отображается|заполнен[аоы]?|установлен[аоы]?|включен[аоы]?|добавлен[аоы]?)|"
    r"поле\s+[^.\n;]{0,80}заполнено|ручн\w+\s+пол[яе][^.\n;]{0,120}заполнен[аоы]?|"
    r"поле\s+[^.\n;]{0,80}оставлено\s+пустым|переключател[ья]\s+[^.\n;]{0,120}установлен[аоы]?|"
    r"создана\s+строк|добавлена\s+строк|включен\s+ручной\s+ввод|выбран\s+адрес|"
    r"добавлен\s+телефон|добавлено\s+контактное\s+лицо|"
    r"hint\s+is\s+(?:shown|displayed)|field\s+[^.\n;]{0,80}is\s+filled|row\s+is\s+(?:created|added)|"
    r"wait\s+for\s+(?:a\s+)?hint\s+to\s+(?:appear|be\s+shown|be\s+displayed)|"
    r"manual\s+input\s+is\s+enabled|switch\s+[^.\n;]{0,80}is\s+set|address\s+is\s+selected|"
    r"phone\s+is\s+added|contact\s+person\s+is\s+added)",
    flags=re.IGNORECASE,
)
PRECONDITION_SETUP_ACTION_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:\d+\.\s*)?"
    r"(?:нажать|ввести|выбрать|открыть|перейти|установить|заполнить|очистить|оставить|"
    r"создать|добавить|авторизоваться|подготовить|закрыть|"
    r"click|press|enter|type|select|open|navigate|set|fill|clear|leave|create|add|"
    r"log\s+in|sign\s+in|prepare|close)\b",
    flags=re.IGNORECASE | re.MULTILINE,
)
PRECONDITION_FIXTURE_OR_API_RE = re.compile(
    r"\b(?:fixture|api|setup\s+profile|test\s+data\s+builder|seed|factory)\b|"
    r"(?:фикстур|api-фикстур|api\s+фикстур|профиль\s+подготовки|тестовый\s+профиль)",
    flags=re.IGNORECASE,
)
AMBIGUOUS_PRECONDITION_SETUP_RE = re.compile(
    r"(?:выбрать\s+или\s+ввести|ввести\s+или\s+выбрать|при\s+необходимости|если\s+нужно|"
    r"select\s+or\s+enter|enter\s+or\s+select|if\s+needed|when\s+needed|as\s+needed)",
    flags=re.IGNORECASE,
)
PRODUCTION_SETUP_PROFILE_REFERENCE_RE = re.compile(
    r"Выполнить\s+setup\s+profile|setup\s+profile|SETUP-CANARY|SETUP-AUTOFIN",
    flags=re.IGNORECASE,
)
ENVIRONMENT_SPECIFIC_PRECONDITION_RE = re.compile(
    r"из\s+тестового\s+стенд|на\s+тестовом\s+стенд|в\s+тестовой\s+сред|"
    r"test\s+stand|test\s+environment",
    flags=re.IGNORECASE,
)
PROJECT_NAME_LEAK_RE = re.compile(r"\bAutoFin\b", flags=re.IGNORECASE)
AMBIGUOUS_CREATE_OR_TAKE_SETUP_RE = re.compile(
    r"создать\s+или\s+взять|создать\s*/\s*взять|взять\s+существующ",
    flags=re.IGNORECASE,
)
CONTACT_PERSON_FIELD_RE = re.compile(
    r"(?<![А-Яа-яЁё])(?:Фамилия|Имя|Отчество)(?![А-Яа-яЁё])",
    flags=re.IGNORECASE,
)
CONTACT_PERSON_REVEAL_ACTION_RE = re.compile(r"Добавить\s+контактное\s+лицо", flags=re.IGNORECASE)
PRODUCTION_DIAGNOSTIC_SECTIONS = (
    "Artifact Write Strategy",
    "Source Row Inventory",
    "Source Table Normalization",
    "Test Design Decision Table",
    "Test-design Applicability Matrix",
    "Atomic Requirements Ledger",
    "Coverage Obligation Table",
    "Writer Quality Gate",
)


def has_precondition_setup_path(preconditions: str) -> bool:
    return bool(
        preconditions
        and (
            PRECONDITION_SETUP_ACTION_RE.search(preconditions)
            or PRECONDITION_FIXTURE_OR_API_RE.search(preconditions)
        )
    )


def branch_choices_in_text(value: str) -> set[str]:
    return {match.group(1).casefold() for match in BRANCH_CHOICE_RE.finditer(value or "")}


def normalized_branch_title(value: str) -> str:
    normalized = normalized_text_for_comparison(value)
    return BRANCH_CHOICE_RE.sub("<branch>", normalized)


def action_required_field_smell_matches(
    test_case_id: str,
    *,
    action_requiredness_fields: list[tuple[str, str]],
    action_step_fields: list[tuple[str, str]],
) -> list[str]:
    matches: list[str] = []
    for field_name, value in action_requiredness_fields:
        if match := ACTION_CONTROL_AS_FIELD_RE.search(value or ""):
            snippet = re.sub(r"\s+", " ", match.group(0).strip())
            matches.append(f"{test_case_id}:field={field_name}; kind=action-as-required-field; match={snippet[:140]}")
    for field_name, value in action_step_fields:
        if match := ACTION_EMPTY_CONTROL_MISUSE_RE.search(value or ""):
            snippet = re.sub(r"\s+", " ", match.group(0).strip())
            matches.append(f"{test_case_id}:field={field_name}; kind=empty-action-control; match={snippet[:140]}")
    return matches


def validate_required_test_case_template_sections(
    blocks: list[tuple[str, str]],
    path: Path,
    root: Path,
    *,
    structural_severity: str,
) -> tuple[list[Finding], list[Check]]:
    display_path = rel(path, root)
    missing_by_case: list[str] = []
    for test_case_id, block in blocks:
        missing_fields = [
            field_name
            for field_name, aliases in REQUIRED_TEST_CASE_TEMPLATE_FIELDS.items()
            if not extract_test_case_field_block(block, aliases)
        ]
        if missing_fields:
            missing_by_case.append(f"{test_case_id}: {', '.join(missing_fields)}")

    if not missing_by_case:
        return [], [
            Check(
                "test-case-template-sections",
                "pass",
                "Required test-case template sections are present.",
                display_path,
            )
        ]

    return [
        Finding(
            id="test-case-missing-required-template-sections",
            severity=structural_severity,
            category="test-case-format",
            title="Some test cases miss required source-link field",
            details=(
                "Each TC-* must keep a source-link field, preferably `Трассировка`, with real "
                "`ATOM-*`, requirement, `SRC-*`, `DICT-*`, section/table/page or source-locator "
                "tokens. Legacy `Ссылка на ФТ` is accepted as a source-link field for backward "
                "compatibility. Separate `Ссылка на ФТ`, `Источник требования`, and quote fields "
                "are allowed only when they add non-duplicative navigation or source evidence."
            ),
            path=display_path,
            evidence=missing_by_case[:20],
            recommended_action=(
                "Add the missing `Трассировка` or legacy source-link field and avoid duplicating "
                "the same source tokens across optional source fields."
            ),
        )
    ], [
        Check(
            "test-case-template-sections",
            "warn" if structural_severity == "warning" else "pass",
            "Required test-case template sections are missing.",
            display_path,
        )
    ]


def numeric_only_valid_values_that_look_invalid(test_data: str) -> list[str]:
    invalid_values: list[str] = []
    has_valid_value = bool(VALID_TEST_DATA_VALUE_RE.search(test_data))
    for match in VALID_TEST_DATA_VALUE_RE.finditer(test_data):
        value = match.group(1).strip().strip("`'\" ")
        if not value:
            continue
        normalized = re.sub(r"\s+", " ", value)
        if NUMERIC_PARAMETER_VALUE_RE.fullmatch(normalized):
            continue
        if re.search(r"[A-Za-zА-Яа-я]", normalized) or re.search(r"[^0-9\s.,+\-]", normalized):
            invalid_values.append(value)
    if has_valid_value:
        for match in VALID_TEST_DATA_CLASS_RE.finditer(test_data):
            value = match.group(1).strip().strip("`'\" ")
            if not value:
                continue
            normalized = re.sub(r"\s+", " ", value)
            if NUMERIC_PARAMETER_VALUE_RE.fullmatch(normalized):
                continue
            if re.search(r"[A-Za-zА-Яа-я]", normalized) or re.search(r"[^0-9\s.,+\-]", normalized):
                invalid_values.append(f"class:{value}")
    return invalid_values


def valid_data_class_label_mismatches(test_data: str) -> list[str]:
    valid_match = next(VALID_TEST_DATA_VALUE_RE.finditer(test_data), None)
    class_match = next(VALID_TEST_DATA_CLASS_RE.finditer(test_data), None)
    if not valid_match or not class_match:
        return []
    value = valid_match.group(1).strip().strip("`'\" ")
    class_label = class_match.group(1).strip().strip("`'\" ")
    if not value or not class_label:
        return []
    value_is_numeric = bool(NUMERIC_PARAMETER_VALUE_RE.fullmatch(re.sub(r"\s+", " ", value)))
    class_is_alpha_or_invalid = bool(
        re.search(r"\b(?:abc|letters?|alpha|alphabetic|special|symbols?|nonnumeric|non[-\s]?numeric)\b", class_label, flags=re.IGNORECASE)
        or re.search(r"\b(?:букв|символ|нечисл)", class_label, flags=re.IGNORECASE)
    )
    if value_is_numeric and class_is_alpha_or_invalid:
        return [f"value={value}; class={class_label}"]
    return []


def numeric_class_label_raw_literal_mismatches(test_data: str) -> list[str]:
    raw_literal_mismatches: list[str] = []
    valid_matches = list(VALID_TEST_DATA_VALUE_RE.finditer(test_data))
    class_matches = list(VALID_TEST_DATA_CLASS_RE.finditer(test_data))
    if not valid_matches or not class_matches:
        return raw_literal_mismatches

    for valid_match, class_match in zip(valid_matches, class_matches):
        value = valid_match.group(1).strip().strip("`'\" ")
        class_label = class_match.group(1).strip().strip("`'\" ")
        if not value or not class_label:
            continue
        value_digits = re.sub(r"\D", "", value)
        class_digits = re.sub(r"\D", "", class_label)
        value_is_numeric = bool(value_digits) and bool(NUMERIC_PARAMETER_VALUE_RE.fullmatch(re.sub(r"\s+", " ", value)))
        class_is_raw_numeric = bool(class_digits) and not re.search(r"[A-Za-zА-Яа-я]", class_label)
        if value_is_numeric and class_is_raw_numeric and value_digits != class_digits:
            raw_literal_mismatches.append(f"value={value}; class={class_label}")
    return raw_literal_mismatches


def boundary_group_label(title: str, goal: str) -> str:
    source = title or goal or "<unknown>"
    label = re.split(r"\s*[:—–-]\s*", source, maxsplit=1)[0].strip().lower()
    return label or "<unknown>"


def is_positive_test_case_type(test_case_type: str) -> bool:
    return (
        test_case_type.startswith("positive")
        or test_case_type.startswith("позитив")
        or test_case_type == "positive"
    )


def is_negative_test_case_type(test_case_type: str) -> bool:
    return test_case_type.startswith("negative") or test_case_type.startswith("негатив")


def extract_scenario_rationale_field(block: str) -> tuple[str, str, str]:
    match = SCENARIO_RATIONALE_FIELD_LINE_RE.search(block)
    if not match:
        return "", "", ""
    return match.group(0), match.group(1), match.group(2).strip()


def scenario_rationale_domain_mismatch_groups(rationale: str, context: str) -> list[str]:
    mismatches: list[str] = []
    if not rationale:
        return mismatches
    for group_name, rationale_pattern, context_pattern in SCENARIO_RATIONALE_DOMAIN_GROUPS:
        if rationale_pattern.search(rationale) and not context_pattern.search(context):
            mismatches.append(group_name)
    return mismatches


def production_line_structure_evidence(content: str) -> tuple[list[str], list[str]]:
    heading_evidence: list[str] = []
    metadata_evidence: list[str] = []
    # Split only on LF: bare CR is not a physical Markdown line break in GitHub raw/rendered views.
    for line_number, line in enumerate(content.split("\n"), start=1):
        line = line.rstrip("\r")
        display_line = line.replace("\r", "\\r")
        for heading_match in re.finditer(r"## TC-", line):
            heading_index = heading_match.start()
            if heading_index > 0:
                heading_evidence.append(
                    f"line {line_number}: heading starts at column {heading_index + 1}: {display_line[:160]}"
                )
        for field in PRODUCTION_TEST_CASE_METADATA_FIELDS:
            for field_match in re.finditer(re.escape(field), line):
                field_index = field_match.start()
                if field_index > 0:
                    metadata_evidence.append(
                        f"line {line_number}: field {field} starts at column {field_index + 1}: {display_line[:160]}"
                    )
    return heading_evidence, metadata_evidence


def quoted_values(text: str) -> list[str]:
    return [match.group(1) for match in re.finditer(r"`([^`]+)`", text or "")]


def value_has_special_symbol(value: str) -> bool:
    return bool(re.search(r"[^A-Za-zА-Яа-яЁё0-9\s-]", value))


def representative_strategy_data_mismatch_evidence(test_case_id: str, strategy_text: str, test_data: str) -> list[str]:
    evidence: list[str] = []
    if not strategy_text:
        return evidence

    text = strategy_text.lower()
    values = quoted_values(test_data)
    if not values:
        return evidence

    surname_value = ""
    first_name_value = ""
    patronymic_value = ""
    for line in test_data.splitlines():
        value_match = re.search(r"`([^`]+)`", line)
        if not value_match:
            continue
        value = value_match.group(1)
        if re.search(r"фамил|surname", line, flags=re.IGNORECASE):
            surname_value = value
        elif re.search(r"\bимя\b|first[-\s]?name", line, flags=re.IGNORECASE):
            first_name_value = value
        elif re.search(r"отчеств|patronymic", line, flags=re.IGNORECASE):
            patronymic_value = value

    class_checks = [
        ("surname letters", surname_value),
        ("фамилия только буквы", surname_value),
        ("first-name letters", first_name_value),
        ("имя только буквы", first_name_value),
        ("patronymic letters", patronymic_value),
        ("отчество только буквы", patronymic_value),
    ]
    for marker, value in class_checks:
        if marker in text and value and re.search(r"[-\d]", value):
            evidence.append(f"{test_case_id}:{marker}; value={value}")

    if re.search(r"with\s+hyphen|с\s+дефис", text) and not any("-" in value for value in values):
        evidence.append(f"{test_case_id}:strategy expects hyphen but no test value contains hyphen")
    if re.search(r"\bdigit\b|цифр", text) and not any(re.search(r"\d", value) for value in values):
        evidence.append(f"{test_case_id}:strategy expects digit but no test value contains digit")
    if re.search(r"special\s+symbol|спец", text) and not any(value_has_special_symbol(value) for value in values):
        evidence.append(f"{test_case_id}:strategy expects special symbol but no test value contains one")
    return evidence


def ft_package_root_for_path(path: Path) -> Path | None:
    parts = list(path.resolve().parts)
    if "fts" not in parts:
        return None
    fts_index = parts.index("fts")
    if len(parts) <= fts_index + 1:
        return None
    return Path(*parts[: fts_index + 2])


def persistence_calibration_package_dir(path: Path, root: Path) -> Path:
    package_root = ft_package_root_for_path(path) or ft_package_root_for_path(root)
    if package_root is not None:
        return package_root / "work" / "calibration" / "persistence-save-flow"
    root_dir = root if root.is_dir() else root.parent
    return root_dir / "work" / "calibration" / "persistence-save-flow"


def persistence_calibration_package_missing_files(path: Path, root: Path) -> list[str]:
    package_dir = persistence_calibration_package_dir(path, root)
    return [
        name
        for name in PERSISTENCE_CALIBRATION_PACKAGE_REQUIRED_FILES
        if not (package_dir / name).is_file()
    ]


def has_persistence_calibration_package(path: Path, root: Path) -> bool:
    return not persistence_calibration_package_missing_files(path, root)


def validate_test_case_quality_smells(
    content: str,
    path: Path,
    root: Path,
    *,
    blocks: list[tuple[str, str]],
    rolling_date_boundary_policy: str = "compatible",
    atomicity_coverage_policy: str = "compatible",
    physical_content: str | None = None,
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    production_test_case_file = is_production_test_case_path(path)

    _, ledger_rows = parsed_atomic_requirement_ledger_rows(content)
    mockup_usage_section = extract_markdown_section(content, "Mockup Usage") or ""
    mockup_hints_expected = (
        "mockup-visual-inventory" in content.lower()
        and re.search(r"used_for_steps\s*\|\s*yes|used_for_steps\s*[:=]\s*yes", mockup_usage_section, flags=re.IGNORECASE)
        and MOCKUP_INTERACTION_HINT_RE.search(mockup_usage_section)
    )
    generic_atoms: list[str] = []
    production_diagnostic_sections: list[str] = []
    production_setup_profile_refs: list[str] = []
    environment_specific_preconditions: list[str] = []
    project_name_precondition_leaks: list[str] = []
    ambiguous_create_or_take_preconditions: list[str] = []
    missing_target_revealing_actions: list[str] = []
    if production_test_case_file:
        production_diagnostic_sections = [
            section_title
            for section_title in PRODUCTION_DIAGNOSTIC_SECTIONS
            if extract_markdown_section(content, section_title) is not None
        ]
        production_setup_profile_refs = sorted(set(PRODUCTION_SETUP_PROFILE_REFERENCE_RE.findall(content)))
    compressed_atoms: list[str] = []
    covered_range_atoms: list[str] = []
    combined_atoms: list[str] = []
    table_residue_atoms: list[str] = []
    ledger_text_by_atom: dict[str, str] = {}
    for row in ledger_rows:
        atom_id = row.get("atom_id", "").strip() or "<missing>"
        inspected_text = " | ".join(
            row.get(field, "")
            for field in ("atomic_statement", "expected_behavior", "condition")
            if row.get(field)
        )
        ledger_text_by_atom[atom_id] = " | ".join(
            row.get(field, "")
            for field in (
                "source_property_id",
                "property",
                "atomic_statement",
                "expected_behavior",
                "condition",
                "source_ref",
                "source_reference",
            )
            if row.get(field)
        )
        if inspected_text and any(pattern.search(inspected_text) for pattern in GENERIC_ATOM_SMELL_PATTERNS):
            generic_atoms.append(f"{atom_id}:{inspected_text[:160]}")
        req_id = row.get("req_id", "") or row.get("source_reference", "") or row.get("source_ref", "")
        req_span = max_requirement_range_span(req_id)
        marker_names = atom_compression_marker_names(inspected_text)
        if req_span >= 3 and len(marker_names) >= 3:
            compressed_atoms.append(
                f"{atom_id}:req_span={req_span}; markers={','.join(marker_names[:6])}; text={inspected_text[:140]}"
            )
        coverage_status = row.get("coverage_status", "").strip().strip("`").lower()
        if coverage_status == "covered" and req_span >= 4:
            covered_range_atoms.append(f"{atom_id}:req_span={req_span}; req_id={req_id[:120]}; text={inspected_text[:140]}")
        if inspected_text and has_combined_behavior_smell(inspected_text):
            combined_atoms.append(f"{atom_id}:{inspected_text[:180]}")
        if inspected_text and has_source_table_residue(inspected_text):
            table_residue_atoms.append(f"{atom_id}:{inspected_text[:180]}")

    generic_test_cases: list[str] = []
    value_type_list_selection_smells: list[str] = []
    dependency_placeholder_setup_smells: list[str] = []
    merged_valid_invalid_test_cases: list[str] = []
    numeric_only_valid_data_invalid: list[str] = []
    valid_data_class_label_mismatch: list[str] = []
    numeric_class_label_raw_literal_mismatch: list[str] = []
    unsupported_input_filtering_oracles: list[str] = []
    input_restriction_transition_oracles: list[str] = []
    unsupported_numeric_validation_feedback: list[str] = []
    mechanical_field_steps: list[str] = []
    negative_transition_without_valid_fixture: list[str] = []
    forbidden_formulations: list[str] = []
    abstract_oracles: list[str] = []
    negative_input_without_observable_oracle: list[str] = []
    date_dependent_absolute_dates: list[str] = []
    rolling_date_boundary_static_data: list[str] = []
    missing_representative_strategy: list[str] = []
    representative_strategy_without_omitted_combinations: list[str] = []
    representative_strategy_without_residual_risk: list[str] = []
    action_treated_as_required_field: list[str] = []
    action_without_observable_artifact: list[str] = []
    broad_scenario_test_cases: list[str] = []
    excessive_atom_fan_in: list[str] = []
    mockup_generic_ui_steps: list[str] = []
    generic_titles: list[str] = []
    process_marker_titles: list[str] = []
    positive_type_negative_oracle: list[str] = []
    negative_type_without_negative_oracle: list[str] = []
    generic_valid_fixture_placeholders: list[str] = []
    generic_test_data_references: list[str] = []
    generic_expected_results: list[str] = []
    generic_test_data_oracles: list[str] = []
    generic_rule_oracles: list[str] = []
    source_dump_oracles: list[str] = []
    value_type_metadata_as_behavior: list[str] = []
    extraction_artifact_oracles: list[str] = []
    requiredness_without_empty_or_marker: list[str] = []
    boundary_without_classes: list[str] = []
    boundary_rejection_without_acceptance: list[str] = []
    gap_placeholder_sections: list[str] = []
    nondeterministic_alternative_oracles: list[str] = []
    duplicated_source_reference_fields: list[str] = []
    dictionary_body_missing_traceability: list[str] = []
    synthetic_requirement_quotes: list[str] = []
    action_created_block_without_cleanup: list[str] = []
    bundled_negative_input_classes: list[str] = []
    overmerged_test_cases: list[str] = []
    noncanonical_scenario_rationale_fields: list[str] = []
    scenario_rationale_domain_mismatches: list[str] = []
    scenario_rationale_too_generic: list[str] = []
    production_glued_headings: list[str] = []
    production_glued_metadata_fields: list[str] = []
    tc_type_expected_result_mismatch: list[str] = []
    trace_not_exercised_by_steps: list[str] = []
    multiple_independent_assertions: list[str] = []
    representative_strategy_data_mismatches: list[str] = []
    production_internal_language_leaks: list[str] = []
    candidate_negative_trigger_missing: list[str] = []
    candidate_negative_trigger_too_specific: list[str] = []
    scenario_rationale_stimulus_mismatches: list[str] = []
    persist_coverage_missing: list[str] = []
    persistence_tc_without_save_action: list[str] = []
    persistence_tc_without_reopen_verification: list[str] = []
    persistence_tc_closes_without_saving: list[str] = []
    persistence_tc_unsourced_save_action: list[str] = []
    persistence_smoke_without_cleanup_strategy: list[str] = []
    persistence_trace_not_exercised: list[str] = []
    persistence_precondition_passive_state: list[str] = []
    persistence_delete_tc_not_self_contained: list[str] = []
    rolling_date_boundary_unformalized_relative_value: list[str] = []
    persistence_grouped_smoke_without_residual_risk: list[str] = []
    source_backed_ui_term_inconsistency: list[str] = []
    persistence_candidate_without_calibration_questions: list[str] = []
    executable_persistence_with_unconfirmed_save_flow: list[str] = []
    persistence_save_placeholder_in_executable_tc: list[str] = []
    persistence_terminology_source_mismatch: list[str] = []
    non_reproducible_preconditions: list[str] = []
    ambiguous_precondition_setup: list[str] = []
    branch_oracle_records: list[dict[str, str]] = []
    boundary_groups: dict[str, dict[str, Any]] = {}
    if production_test_case_file:
        production_glued_headings, production_glued_metadata_fields = production_line_structure_evidence(
            physical_content if physical_content is not None else content
        )
    if REPRESENTATIVE_PARTIAL_COVERAGE_RE.search(content) and not REPRESENTATIVE_STRATEGY_RE.search(content):
        missing_representative_strategy.append("partial representative coverage is declared without representative/pairwise strategy or residual risk")
    if REPRESENTATIVE_PARTIAL_COVERAGE_RE.search(content) and REPRESENTATIVE_STRATEGY_RE.search(content):
        if not REPRESENTATIVE_OMITTED_COMBINATIONS_RE.search(content):
            representative_strategy_without_omitted_combinations.append(
                "representative/pairwise strategy does not list omitted or excluded combinations/fields/classes"
            )
        if not REPRESENTATIVE_RESIDUAL_RISK_RE.search(content):
            representative_strategy_without_residual_risk.append(
                "representative/pairwise strategy does not state residual risk"
            )
    for test_case_id, block in blocks:
        is_calibration_candidate = is_ui_calibration_candidate_block(block)
        expected_result = extract_test_case_expected_result(block)
        test_case_type = extract_test_case_type(block)
        title = extract_test_case_field_block(block, ["Title", "title", "Название"])
        goal = extract_test_case_field_block(block, ["Goal", "goal", "Цель"])
        preconditions = extract_test_case_field_block(
            block, ["Preconditions", "preconditions", "Предусловия"]
        )
        test_data = extract_test_case_field_block(block, ["Test Data", "test_data", "test data", "Тестовые данные"])
        steps = extract_test_case_field_block(block, ["Steps", "steps", "Шаги"])
        steps = trim_test_case_plain_field_boundary(steps)
        postconditions = extract_test_case_field_block(block, ["Postconditions", "postconditions", "Постусловия"])
        traceability = extract_test_case_field_block(block, ["Traceability", "traceability", "Трассировка"])
        ft_reference = extract_test_case_field_block(block, ["FT Reference", "ft_reference", "Ссылка на ФТ"])
        requirement_source = extract_test_case_field_block(block, ["Requirement Source", "requirement_source", "Источник требования"])
        requirement_quote = extract_test_case_field_block(
            block,
            [
                "Requirement Quote",
                "Requirement Source Quote",
                "Source Requirement Quote",
                "Источник / цитата требования",
            ],
        )
        status = extract_test_case_field_block(block, ["Status", "status", "Статус"]).lower()
        scenario_rationale_line, _, scenario_rationale = extract_scenario_rationale_field(block)
        if scenario_rationale_line and not CANONICAL_SCENARIO_RATIONALE_FIELD_RE.match(scenario_rationale_line):
            noncanonical_scenario_rationale_fields.append(f"{test_case_id}:{scenario_rationale_line[:180]}")
        if scenario_rationale:
            rationale_context = " ".join(
                [
                    title,
                    goal,
                    preconditions,
                    test_data,
                    steps,
                    expected_result,
                    traceability,
                    ft_reference,
                    requirement_source,
                    requirement_quote,
                ]
            )
            mismatch_groups = scenario_rationale_domain_mismatch_groups(scenario_rationale, rationale_context)
            if mismatch_groups:
                scenario_rationale_domain_mismatches.append(
                    f"{test_case_id}:groups={','.join(mismatch_groups)}; rationale={scenario_rationale[:180]}"
                )
            if (
                SCENARIO_RATIONALE_GENERIC_ONLY_RE.search(scenario_rationale)
                and not SCENARIO_RATIONALE_CONCRETE_TARGET_RE.search(scenario_rationale)
            ):
                scenario_rationale_too_generic.append(f"{test_case_id}:rationale={scenario_rationale[:180]}")
            stimulus_context = " ".join([title, test_data, steps, expected_result])
            if DADATA_SELECTION_SIGNAL_RE.search(stimulus_context) and INITIAL_VISIBILITY_RATIONALE_RE.search(scenario_rationale):
                scenario_rationale_stimulus_mismatches.append(
                    f"{test_case_id}:DaData stimulus with visibility/default-state rationale={scenario_rationale[:180]}"
                )
            if (
                VISIBILITY_ONLY_TITLE_RE.search(title)
                and not TITLE_SCENARIO_ACTION_RE.search(title)
                and DADATA_SELECTION_SIGNAL_RE.search(" ".join([steps, expected_result]))
            ):
                scenario_rationale_stimulus_mismatches.append(
                    f"{test_case_id}:visibility-only title with input/select DaData steps; title={title[:120]}"
                )
        if (
            is_positive_test_case_type(test_case_type)
            and expected_result
            and VALIDATION_ERROR_EXPECTED_RE.search(expected_result)
            and not NORMAL_STATE_HINT_EXCEPTION_RE.search(" ".join([title, scenario_rationale, expected_result]))
        ):
            tc_type_expected_result_mismatch.append(
                f"{test_case_id}:type={test_case_type}; expected={expected_result[:180]}"
            )
        exercised_context = " ".join([title, test_data, steps, expected_result, scenario_rationale])
        executable_context = " ".join([title, test_data, steps, expected_result])
        if (
            re.search(r"\bBSR\s+167\b", traceability)
            and re.search(r"\bBSR\s+17[12]\b", traceability)
            and re.search(r"домашн|home", executable_context, flags=re.IGNORECASE)
            and not re.search(r"рабоч|work", executable_context, flags=re.IGNORECASE)
        ):
            trace_not_exercised_by_steps.append(
                f"{test_case_id}:trace={traceability[:160]}; exercised={executable_context[:180]}"
            )
        if expected_result and DICTIONARY_AND_BRANCH_ASSERTION_RE.search(expected_result):
            multiple_independent_assertions.append(f"{test_case_id}:expected={expected_result[:180]}")
        strategy_text = "\n".join(
            line
            for line in block.splitlines()
            if re.search(
                r"Representative/pairwise strategy|Omitted combinations|Residual risk|"
                r"РџСЂРµРґСЃС‚Р°РІРёС‚РµР»|РћРїСѓС‰РµРЅ|РћСЃС‚Р°С‚РѕС‡РЅ",
                line,
                flags=re.IGNORECASE,
            )
        )
        representative_strategy_data_mismatches.extend(
            representative_strategy_data_mismatch_evidence(test_case_id, strategy_text, test_data)
        )
        if production_test_case_file and INTERNAL_ENGLISH_STRATEGY_FIELD_RE.search(block):
            production_internal_language_leaks.append(f"{test_case_id}:internal English strategy labels")
        if (
            is_calibration_candidate
            and not NEUTRAL_VALIDATION_TRIGGER_RE.search(steps)
            and not TRIGGER_BA_QUESTION_RE.search(block)
        ):
            candidate_negative_trigger_missing.append(f"{test_case_id}:steps={steps[:180]}")
        if (
            is_calibration_candidate
            and CANDIDATE_TRIGGER_TOO_SPECIFIC_RE.search(steps)
            and not CANDIDATE_TRIGGER_ALTERNATIVE_RE.search(" ".join([steps, block]))
        ):
            candidate_negative_trigger_too_specific.append(f"{test_case_id}:steps={steps[:180]}")
        persistence_context = " ".join([title, scenario_rationale, expected_result])
        persistence_body = " ".join([steps, expected_result, postconditions])
        if PERSISTENCE_TC_SIGNAL_RE.search(persistence_context):
            is_persistence_candidate = bool(PERSISTENCE_CANDIDATE_STATUS_RE.search(block))
            if is_persistence_candidate and not (
                PERSISTENCE_CALIBRATION_LINK_RE.search(block)
                or PERSISTENCE_CALIBRATION_LINK_RE.search(content[:2000])
                or has_persistence_calibration_package(path, root)
            ):
                persistence_candidate_without_calibration_questions.append(
                    f"{test_case_id}:candidate status lacks BA/UI calibration links or package"
                )
            if (
                not is_persistence_candidate
                and PERSISTENCE_SAVE_FLOW_UNCONFIRMED_RE.search(" ".join([content[:2500], block]))
                and not PERSISTENCE_SAVE_FLOW_CONFIRMED_RE.search(" ".join([content[:2500], block]))
            ):
                executable_persistence_with_unconfirmed_save_flow.append(
                    f"{test_case_id}:persistence TC is executable while save/reopen/cleanup flow remains unconfirmed"
                )
            if not is_persistence_candidate and PERSISTENCE_SAVE_PLACEHOLDER_RE.search(block):
                persistence_save_placeholder_in_executable_tc.append(
                    f"{test_case_id}:placeholder save wording remains in executable persistence TC"
                )
            if preconditions and PERSISTENCE_PASSIVE_PRECONDITION_RE.search(preconditions):
                persistence_precondition_passive_state.append(
                    f"{test_case_id}:preconditions={preconditions[:180] or '<missing>'}"
                )
            exercise_context = " ".join([title, scenario_rationale, preconditions, steps, expected_result])
            for ref_label, ref_re, exercise_re in PERSISTENCE_TRACE_NOT_EXERCISED_RULES:
                if ref_re.search(traceability) and not exercise_re.search(exercise_context):
                    persistence_trace_not_exercised.append(
                        f"{test_case_id}:{ref_label} not exercised by steps/rationale"
                    )
            delete_context = " ".join([title, scenario_rationale, preconditions, steps, expected_result])
            if (
                PERSISTENCE_DELETE_TC_SIGNAL_RE.search(delete_context)
                and not PERSISTENCE_DELETE_SELF_CONTAINED_SETUP_RE.search(preconditions)
                and not PERSISTENCE_DELETE_FIXTURE_RE.search(preconditions)
            ):
                persistence_delete_tc_not_self_contained.append(
                    f"{test_case_id}:preconditions={preconditions[:180] or '<missing>'}"
                )
            rolling_date_context = " ".join([test_data, steps, expected_result])
            if (
                ROLLING_DATE_UNFORMALIZED_RELATIVE_RE.search(rolling_date_context)
                and not ROLLING_DATE_FORMALIZATION_RE.search(rolling_date_context)
            ):
                rolling_date_boundary_unformalized_relative_value.append(
                    f"{test_case_id}:date_data={rolling_date_context[:180]}"
                )
            grouped_context = " ".join([title, scenario_rationale, test_data, steps, expected_result])
            if (
                PERSISTENCE_GROUPED_PHONE_EMAIL_RE.search(grouped_context)
                and not PERSISTENCE_GROUPED_SMOKE_RISK_RE.search(grouped_context)
            ):
                persistence_grouped_smoke_without_residual_risk.append(
                    f"{test_case_id}:scenario_rationale={scenario_rationale[:180] or '<missing>'}"
                )
            if not PERSISTENCE_SAVE_ACTION_RE.search(steps):
                persistence_tc_without_save_action.append(f"{test_case_id}:steps={steps[:180] or '<missing>'}")
            if not (
                PERSISTENCE_REOPEN_ACTION_RE.search(steps)
                and (
                    PERSISTENCE_REOPEN_VERIFICATION_RE.search(expected_result)
                    or PERSISTENCE_REOPEN_VERIFICATION_RE.search(" ".join([steps, expected_result]))
                )
            ):
                persistence_tc_without_reopen_verification.append(
                    f"{test_case_id}:steps={steps[:180] or '<missing>'}; expected={expected_result[:160] or '<missing>'}"
                )
            if PERSISTENCE_CLOSE_WITHOUT_SAVE_RE.search(persistence_body):
                persistence_tc_closes_without_saving.append(
                    f"{test_case_id}:steps={steps[:140]}; postconditions={postconditions[:140] or '-'}"
                )
            if (
                PERSISTENCE_CONCRETE_UNSOURCED_SAVE_RE.search(steps)
                and not PERSISTENCE_SAVE_SOURCE_OR_CONFIRMATION_RE.search(block)
            ):
                persistence_tc_unsourced_save_action.append(f"{test_case_id}:steps={steps[:180]}")
            if not PERSISTENCE_CLEANUP_STRATEGY_RE.search(postconditions):
                persistence_smoke_without_cleanup_strategy.append(
                    f"{test_case_id}:postconditions={postconditions[:180] or '<missing>'}"
                )
        if (
            SOURCE_BACKED_UI_TERM_INCONSISTENCY_RE.search(block)
            and not SOURCE_BACKED_UI_TERM_DECISION_RE.search(content)
        ):
            source_backed_ui_term_inconsistency.append(f"{test_case_id}:mixed section/appended UI block terms")
        if (
            PERSISTENCE_RELATION_CLIENT_RE.search(block)
            and PERSISTENCE_RELATION_APPLICANT_RE.search(content)
            and not PERSISTENCE_TERMINOLOGY_MAPPING_RE.search(content)
        ):
            persistence_terminology_source_mismatch.append(
                f"{test_case_id}:mixed `Отношение к клиенту` / `Отношение к заявителю` without mapping"
            )
        if production_test_case_file:
            if preconditions and ENVIRONMENT_SPECIFIC_PRECONDITION_RE.search(preconditions):
                environment_specific_preconditions.append(f"{test_case_id}:preconditions={preconditions[:180]}")
            if preconditions and PROJECT_NAME_LEAK_RE.search(preconditions):
                project_name_precondition_leaks.append(f"{test_case_id}:preconditions={preconditions[:180]}")
            if preconditions and AMBIGUOUS_CREATE_OR_TAKE_SETUP_RE.search(preconditions):
                ambiguous_create_or_take_preconditions.append(f"{test_case_id}:preconditions={preconditions[:180]}")
            if CONTACT_PERSON_FIELD_RE.search(block) and not CONTACT_PERSON_REVEAL_ACTION_RE.search(preconditions):
                missing_target_revealing_actions.append(f"{test_case_id}:preconditions={preconditions[:180] or '<missing>'}")
        traceability_tokens = normalize_test_case_ref_tokens(traceability)
        ft_reference_tokens = normalize_test_case_ref_tokens(ft_reference)
        requirement_source_tokens = normalize_test_case_ref_tokens(requirement_source)
        if preconditions and AMBIGUOUS_PRECONDITION_SETUP_RE.search(preconditions):
            ambiguous_precondition_setup.append(f"{test_case_id}:preconditions={preconditions[:180]}")
        if (
            preconditions
            and NON_REPRODUCIBLE_PRECONDITION_STATE_RE.search(preconditions)
            and not has_precondition_setup_path(preconditions)
        ):
            non_reproducible_preconditions.append(f"{test_case_id}:preconditions={preconditions[:180]}")
        if ft_reference_tokens and traceability_tokens and ft_reference_tokens == traceability_tokens:
            duplicated_source_reference_fields.append(
                f"{test_case_id}:FT Reference duplicates Traceability={traceability[:160]}"
            )
        elif (
            requirement_source_tokens
            and traceability_tokens
            and set(requirement_source_tokens).issubset(set(traceability_tokens))
            and not set(requirement_source_tokens) - set(ft_reference_tokens)
        ):
            duplicated_source_reference_fields.append(
                f"{test_case_id}:Requirement Source duplicates source/trace refs={requirement_source[:160]}"
            )
        dict_ids_in_body = sorted(set(DICT_ID_RE.findall(block)))
        if dict_ids_in_body:
            missing_dict_refs = [dict_id for dict_id in dict_ids_in_body if dict_id not in set(DICT_ID_RE.findall(traceability))]
            if missing_dict_refs:
                dictionary_body_missing_traceability.append(
                    f"{test_case_id}:missing={', '.join(missing_dict_refs)}; traceability={traceability[:160] or '-'}"
                )
        if requirement_quote and SYNTHETIC_QUOTE_RE.search(requirement_quote):
            synthetic_requirement_quotes.append(f"{test_case_id}:{requirement_quote[:180]}")
        if (
            ACTION_CREATED_BLOCK_RE.search(steps)
            and NO_POSTCONDITIONS_RE.search(postconditions or "")
            and not ACTION_CREATED_BLOCK_CLEANUP_RE.search(steps)
        ):
            action_created_block_without_cleanup.append(
                f"{test_case_id}:steps={steps[:160]}; postconditions={postconditions or '-'}"
            )
        invalid_class_context = " ".join([test_data, steps, expected_result])
        if (
            is_negative_test_case_type(test_case_type)
            and MULTI_INVALID_CLASS_RE.search(invalid_class_context)
            and len(re.findall(r"`[^`]+`", invalid_class_context)) >= 3
        ):
            bundled_negative_input_classes.append(
                f"{test_case_id}:test_data={test_data[:160]}; expected={expected_result[:120]}"
            )
        branch_choices = branch_choices_in_text(" ".join([title, test_data, steps]))
        if branch_choices and expected_result:
            branch_oracle_records.append(
                {
                    "test_case_id": test_case_id,
                    "branch_key": normalized_branch_title(title),
                    "choices": ",".join(sorted(branch_choices)),
                    "expected": normalized_text_for_comparison(expected_result),
                    "evidence": f"{test_case_id}:title={title[:90]}; expected={expected_result[:120]}",
                }
            )
        generic_test_cases.extend(
            generic_test_case_smell_matches(
                test_case_id,
                [
                    ("preconditions", preconditions),
                    ("test_data", test_data),
                    ("steps", steps),
                    ("expected_result", expected_result),
                ],
            )
        )
        atom_ids_in_block = extract_any_atom_ids_from_text(block)
        source_refs_in_block = extract_source_backed_test_case_refs(block)
        for formulation_label, formulation_pattern in FORBIDDEN_TEST_CASE_FORMULATION_PATTERNS:
            if match := formulation_pattern.search(block):
                forbidden_formulations.append(
                    f"{test_case_id}:{formulation_label}: {match.group(0).strip()[:120]}"
                )
        if (
            expected_result
            and ABSTRACT_TEST_CASE_ORACLE_RE.search(expected_result)
            and not OBSERVABLE_TEST_CASE_ORACLE_RE.search(expected_result)
        ):
            abstract_oracles.append(f"{test_case_id}:expected={expected_result[:180]}")
        if (
            not is_calibration_candidate
            and
            is_negative_test_case_type(test_case_type)
            and steps
            and expected_result
            and NEGATIVE_INPUT_ACTION_RE.search(steps)
            and not NEXT_STEP_ACTION_RE.search(steps)
            and not FIELD_LEVEL_OBSERVABLE_ORACLE_RE.search(expected_result)
        ):
            negative_input_without_observable_oracle.append(
                f"{test_case_id}:steps={steps[:100]}; expected={expected_result[:160]}"
            )
        if (
            DATE_DEPENDENT_SOURCE_RE.search(block)
            and ABSOLUTE_DATE_RE.search(" ".join([test_data, steps]))
            and not FIXED_BUSINESS_DATE_CONTEXT_RE.search(preconditions)
        ):
            date_dependent_absolute_dates.append(
                f"{test_case_id}:preconditions={preconditions[:100] or '-'}"
            )
        rolling_boundary_context = " ".join(
            [
                title,
                goal,
                expected_result,
                traceability,
                ft_reference,
                requirement_source,
                requirement_quote,
            ]
        )
        rolling_boundary_data = " ".join([test_data, steps])
        if (
            ROLLING_DATE_BOUNDARY_SIGNAL_RE.search(rolling_boundary_context)
            and STATIC_CALENDAR_DATE_RE.search(rolling_boundary_data)
            and not ROLLING_DATE_FORMULA_RE.search(rolling_boundary_data)
            and not FIXED_BUSINESS_DATE_CONTEXT_RE.search(preconditions)
        ):
            dates = ", ".join(sorted(set(STATIC_CALENDAR_DATE_RE.findall(rolling_boundary_data)))[:5])
            rolling_date_boundary_static_data.append(
                f"{test_case_id}:dates={dates}; title={title[:120] or '<missing>'}"
            )
        linked_atom_text = " | ".join(
            ledger_text_by_atom.get(atom_id, "")
            for atom_id in atom_ids_in_block
            if ledger_text_by_atom.get(atom_id)
        )
        value_type_context = " ".join([title, goal, linked_atom_text])
        if (
            VALUE_TYPE_PROPERTY_RE.search(value_type_context)
            and VALUE_TYPE_LIST_SELECTION_RE.search(" ".join([test_data, steps, expected_result]))
            and (not linked_atom_text or NON_LIST_VALUE_TYPE_RE.search(linked_atom_text) or not LIST_VALUE_TYPE_RE.search(linked_atom_text))
        ):
            value_type_list_selection_smells.append(
                f"{test_case_id}:title={title[:80]}; atoms={','.join(atom_ids_in_block[:5])}; data={test_data[:120]}"
            )
        if steps and DEPENDENCY_PLACEHOLDER_SETUP_RE.search(steps):
            dependency_placeholder_setup_smells.append(f"{test_case_id}:{steps[:180]}")
        if steps and MECHANICAL_FIELD_STEP_RE.search(steps):
            mechanical_field_steps.append(f"{test_case_id}:steps={steps[:180]}")
        rule_oracle_context = " ".join([steps, expected_result])
        if rule_oracle_context and GENERIC_RULE_ORACLE_RE.search(rule_oracle_context):
            generic_rule_oracles.append(f"{test_case_id}:{rule_oracle_context[:180]}")
        if rule_oracle_context and SOURCE_DUMP_RULE_ORACLE_RE.search(rule_oracle_context):
            source_dump_oracles.append(f"{test_case_id}:{rule_oracle_context[:220]}")
        if (
            VALUE_TYPE_PROPERTY_RE.search(value_type_context)
            and NON_LIST_VALUE_TYPE_RE.search(value_type_context)
            and VALUE_TYPE_METADATA_AS_BEHAVIOR_RE.search(" ".join([test_data, steps, expected_result]))
        ):
            value_type_metadata_as_behavior.append(
                f"{test_case_id}:title={title[:80]}; atoms={','.join(atom_ids_in_block[:5])}; expected={expected_result[:140]}"
            )
        extraction_context = " ".join([steps, expected_result])
        if extraction_context and (
            has_source_table_residue(extraction_context)
            or any(pattern.search(extraction_context) for pattern in EXTRACTION_ARTIFACT_ORACLE_PATTERNS)
        ):
            extraction_artifact_oracles.append(f"{test_case_id}:{extraction_context[:220]}")
        if mockup_hints_expected and steps and MOCKUP_GENERIC_UI_STEP_RE.search(steps):
            mockup_generic_ui_steps.append(f"{test_case_id}:{steps[:180]}")
        boundary_context = " ".join([title, goal, test_data, steps, expected_result])
        boundary_group = boundary_groups.setdefault(
            boundary_group_label(title, goal),
            {
                "above_max_rejection": [],
                "below_min_rejection": [],
                "max_acceptance": False,
                "min_acceptance": False,
            },
        )
        negative_oracle = bool(
            expected_result
            and (
                NEGATIVE_OR_REJECTION_EXPECTED_RE.search(expected_result)
                or (
                    VALIDATION_ERROR_EXPECTED_RE.search(expected_result)
                    and not NORMAL_STATE_HINT_EXCEPTION_RE.search(expected_result)
                )
            )
        )
        if negative_oracle and OFF_BOUNDARY_MAX_RE.search(boundary_context):
            boundary_group["above_max_rejection"].append(test_case_id)
        if negative_oracle and OFF_BOUNDARY_MIN_RE.search(boundary_context):
            boundary_group["below_min_rejection"].append(test_case_id)
        acceptance_context = " ".join([test_case_type, title, test_data, steps, expected_result])
        boundary_acceptance = (
            bool(expected_result)
            and not negative_oracle
            and BOUNDARY_ACCEPTANCE_RESULT_RE.search(expected_result)
            and not test_case_type.startswith("negative")
            and not test_case_type.startswith("негатив")
        )
        if boundary_acceptance and EXACT_BOUNDARY_MAX_RE.search(acceptance_context):
            boundary_group["max_acceptance"] = True
        if boundary_acceptance and EXACT_BOUNDARY_MIN_RE.search(acceptance_context):
            boundary_group["min_acceptance"] = True
        if title and any(pattern.search(title) for pattern in GENERIC_TC_TITLE_PATTERNS):
            generic_titles.append(f"{test_case_id}:{title[:140]}")
        if title and TEST_CASE_TITLE_PROCESS_MARKER_RE.search(title):
            process_marker_titles.append(f"{test_case_id}:{title[:160]}")
        if is_positive_test_case_type(test_case_type) and expected_result and NEGATIVE_OR_REJECTION_EXPECTED_RE.search(expected_result):
            positive_type_negative_oracle.append(f"{test_case_id}:type={test_case_type}; expected={expected_result[:150]}")
        if is_negative_test_case_type(test_case_type) and not negative_oracle:
            if expected_result and POSITIVE_ACCEPTANCE_EXPECTED_RE.search(expected_result):
                negative_type_without_negative_oracle.append(
                    f"{test_case_id}:type={test_case_type}; expected={expected_result[:150]}"
                )
            elif expected_result:
                negative_type_without_negative_oracle.append(
                    f"{test_case_id}:type={test_case_type}; expected_has_no_negative_oracle={expected_result[:150]}"
                )
        generic_fixture_context = " ".join([preconditions, test_data])
        if generic_fixture_context and GENERIC_VALID_FIXTURE_PLACEHOLDER_RE.search(generic_fixture_context):
            generic_valid_fixture_placeholders.append(
                f"{test_case_id}:preconditions={preconditions[:100] or '-'}; test_data={test_data[:120] or '-'}"
            )
        if (
            steps
            and GENERIC_TEST_DATA_REFERENCE_RE.search(steps)
            and test_data
            and GENERIC_VALID_FIXTURE_PLACEHOLDER_RE.search(test_data)
        ):
            generic_test_data_references.append(
                f"{test_case_id}:steps={steps[:120]}; test_data={test_data[:120]}"
            )
        if expected_result and any(pattern.search(expected_result) for pattern in GENERIC_EXPECTED_RESULT_PATTERNS):
            generic_expected_results.append(f"{test_case_id}:{expected_result[:150]}")
        if expected_result and GENERIC_TEST_DATA_ORACLE_RE.search(expected_result):
            generic_test_data_oracles.append(f"{test_case_id}:expected={expected_result[:150]}; test_data={test_data[:120] or '-'}")
        if (
            not is_calibration_candidate
            and
            is_negative_test_case_type(test_case_type)
            and expected_result
            and NONDETERMINISTIC_ALTERNATIVE_ORACLE_RE.search(expected_result)
        ):
            nondeterministic_alternative_oracles.append(f"{test_case_id}:expected={expected_result[:180]}")
        gap_placeholder_context = " ".join([test_case_type, status, expected_result, steps])
        if (
            extract_gap_ids_from_text(gap_placeholder_context)
            and ("gap" in test_case_type or "gap" in status or "unclear" in status)
            and GAP_PLACEHOLDER_EXPECTED_RE.search(" ".join([expected_result, steps]))
        ):
            gap_placeholder_sections.append(
                f"{test_case_id}:type={test_case_type or '-'}; status={status or '-'}; expected={expected_result[:160]}"
            )
        action_identity_context = " ".join([title, goal])
        action_step_context = " ".join([test_data, steps, expected_result])
        is_positive_action_transition_check = bool(
            action_identity_context
            and ACTION_CONTROL_CONTEXT_RE.search(action_identity_context)
            and NEXT_STEP_ACTION_RE.search(steps)
            and POSITIVE_TRANSITION_ORACLE_RE.search(expected_result)
        )
        requiredness_context = " ".join([title, goal, test_data, steps, expected_result])
        if (
            requiredness_context
            and REQUIREDNESS_RE.search(requiredness_context)
            and not EMPTY_REQUIREDNESS_CHECK_RE.search(requiredness_context)
            and not REQUIREDNESS_MARKER_RE.search(requiredness_context)
            and not is_positive_action_transition_check
        ):
            requiredness_without_empty_or_marker.append(f"{test_case_id}:{requiredness_context[:150]}")
        action_treated_as_required_field.extend(
            action_required_field_smell_matches(
                test_case_id,
                action_requiredness_fields=[
                    ("title", title),
                    ("goal", goal),
                    ("test_data", test_data),
                    ("expected_result", expected_result),
                ],
                action_step_fields=[
                    ("test_data", test_data),
                    ("steps", steps),
                    ("expected_result", expected_result),
                ],
            )
        )
        if test_data and NUMERIC_ONLY_CONTEXT_RE.search(boundary_context):
            invalid_valid_values = numeric_only_valid_values_that_look_invalid(test_data)
            if invalid_valid_values:
                numeric_only_valid_data_invalid.append(
                    f"{test_case_id}:valid_values={', '.join(invalid_valid_values[:3])}; context={boundary_context[:130]}"
                )
        if (
            expected_result
            and NEXT_STEP_ACTION_RE.search(steps)
            and TRANSITION_VALIDATION_ORACLE_RE.search(expected_result)
            and FIELD_LEVEL_INPUT_RESTRICTION_RE.search(block)
            and not UNDERLIMIT_INPUT_RESTRICTION_RE.search(boundary_context)
            and (
                INVALID_CHARACTER_INPUT_RESTRICTION_RE.search(boundary_context)
                or OVERLIMIT_INPUT_RESTRICTION_RE.search(boundary_context)
            )
        ):
            input_restriction_transition_oracles.append(
                f"{test_case_id}:steps={steps[:100]}; expected={expected_result[:160]}"
            )
        source_backed_feedback_context = " ".join([requirement_quote, linked_atom_text])
        numeric_invalid_context = " ".join([title, goal, test_data, steps, block])
        source_backed_filtering_context = " ".join([requirement_quote, linked_atom_text])
        expected_assumes_input_filtering = bool(
            INPUT_FILTERING_ORACLE_RE.search(expected_result or "")
            or INPUT_FILTERING_ORACLE_SUPPLEMENTAL_RE.search(expected_result or "")
        )
        source_defines_input_filtering = bool(
            INPUT_FILTERING_ORACLE_RE.search(source_backed_filtering_context)
            or INPUT_FILTERING_ORACLE_SUPPLEMENTAL_RE.search(source_backed_filtering_context)
        )
        if (
            not is_calibration_candidate
            and
            is_negative_test_case_type(test_case_type)
            and expected_assumes_input_filtering
            and NUMERIC_INVALID_INPUT_CONTEXT_RE.search(numeric_invalid_context)
            and not source_defines_input_filtering
        ):
            unsupported_input_filtering_oracles.append(
                f"{test_case_id}:expected={expected_result[:160]}; source={source_backed_filtering_context[:120] or '-'}"
            )
        if (
            not is_calibration_candidate
            and
            is_negative_test_case_type(test_case_type)
            and expected_result
            and NUMERIC_VALIDATION_FEEDBACK_ORACLE_RE.search(expected_result)
            and NUMERIC_INVALID_INPUT_CONTEXT_RE.search(numeric_invalid_context)
            and not NUMERIC_VALIDATION_FEEDBACK_ORACLE_RE.search(source_backed_feedback_context)
        ):
            unsupported_numeric_validation_feedback.append(
                f"{test_case_id}:expected={expected_result[:160]}; source={source_backed_feedback_context[:120] or '-'}"
            )
        transition_context = " ".join([title, goal, preconditions, test_data, steps, expected_result])
        if (
            NEXT_STEP_ACTION_RE.search(steps)
            and NEGATIVE_OR_REJECTION_EXPECTED_RE.search(expected_result)
            and not VALID_FIXTURE_CONTEXT_RE.search(transition_context)
        ):
            negative_transition_without_valid_fixture.append(
                f"{test_case_id}:steps={steps[:90]}; expected={expected_result[:140]}"
            )
        if test_data:
            class_mismatches = valid_data_class_label_mismatches(test_data)
            if class_mismatches:
                valid_data_class_label_mismatch.append(f"{test_case_id}:{'; '.join(class_mismatches[:3])}")
            raw_literal_mismatches = numeric_class_label_raw_literal_mismatches(test_data)
            if raw_literal_mismatches:
                numeric_class_label_raw_literal_mismatch.append(f"{test_case_id}:{'; '.join(raw_literal_mismatches[:3])}")
        if (
            test_case_type.startswith("boundary")
            or test_case_type.startswith("границ")
        ) and not BOUNDARY_CLASS_RE.search(" ".join([test_data, steps, expected_result])):
            boundary_without_classes.append(f"{test_case_id}:type={test_case_type}")
        if expected_result and any(pattern.search(expected_result) for pattern in MERGED_VALID_INVALID_EXPECTED_PATTERNS):
            merged_valid_invalid_test_cases.append(f"{test_case_id}:expected={expected_result[:160]}")
        else:
            test_data_and_steps = " ".join(
                [
                    test_data,
                    steps,
                ]
            )
            if (
                test_data_and_steps
                and MERGED_VALID_INVALID_DATA_STEP_RE.search(test_data_and_steps)
                and re.search(r"^\*\*(?:Type|Тип):\*\*\s*`?(?:Negative|Негативн\w*)`?", block, flags=re.IGNORECASE | re.MULTILINE)
            ):
                merged_valid_invalid_test_cases.append(f"{test_case_id}:data/steps={test_data_and_steps[:160]}")
        action_context = " ".join(
            [
                title,
                goal,
                expected_result,
            ]
        )
        if (
            action_context
            and ACTION_INITIATION_WITHOUT_ARTIFACT_RE.search(action_context)
            and not CONCRETE_OBSERVABLE_ARTIFACT_RE.search(action_context)
        ):
            action_without_observable_artifact.append(f"{test_case_id}:{action_context[:180]}")
        if re.search(r"^\*\*(?:Type|Тип):\*\*\s*`?(?:Scenario|Сценар\w*)`?", block, flags=re.IGNORECASE | re.MULTILINE):
            if max_requirement_range_span(block) >= 4 or re.search(
                r"same\s+constraints|те\s+же\s+огранич|соответствуют\s+`?GSR|validate\s+by\s+FT\s+rules",
                block,
                flags=re.IGNORECASE,
            ):
                broad_scenario_test_cases.append(f"{test_case_id}:scenario_range_or_deferred_oracle")

        source_ref_count = max(len(atom_ids_in_block), len(source_refs_in_block))
        if source_ref_count > 5 and not re.search(
            r"(?i)\bscenario\b|\buse[-\s]?case\b|сценар|сквозн|e2e|end[-\s]?to[-\s]?end",
            block,
        ):
            excessive_atom_fan_in.append(f"{test_case_id}:source_refs={source_ref_count}")
        if (
            source_ref_count > 2
            and not re.search(r"(?i)\bscenario\b|\buse[-\s]?case\b|сценар|сквозн|e2e|end[-\s]?to[-\s]?end", block)
            and not SCENARIO_RATIONALE_RE.search(block)
        ):
            overmerged_test_cases.append(
                f"{test_case_id}:source_refs={source_ref_count}; refs={','.join(source_refs_in_block[:8])}"
            )

    for group, boundary_flags in boundary_groups.items():
        above_max_rejection = boundary_flags["above_max_rejection"]
        below_min_rejection = boundary_flags["below_min_rejection"]
        if above_max_rejection and not boundary_flags["max_acceptance"]:
            boundary_rejection_without_acceptance.append(
                f"{group}: above-max rejection without exact max acceptance; examples={','.join(above_max_rejection[:5])}"
            )
        if below_min_rejection and not boundary_flags["min_acceptance"]:
            boundary_rejection_without_acceptance.append(
                f"{group}: below-min rejection without exact min acceptance; examples={','.join(below_min_rejection[:5])}"
            )

    branch_oracles_without_distinction: list[str] = []
    for index, record in enumerate(branch_oracle_records):
        for other in branch_oracle_records[index + 1 :]:
            if record["test_case_id"] == other["test_case_id"]:
                continue
            if record["branch_key"] != other["branch_key"]:
                continue
            if record["expected"] != other["expected"]:
                continue
            if set(record["choices"].split(",")) == set(other["choices"].split(",")):
                continue
            branch_oracles_without_distinction.append(
                f"{record['test_case_id']} vs {other['test_case_id']}: same expected result; "
                f"{record['evidence']} | {other['evidence']}"
            )

    if production_diagnostic_sections:
        findings.append(
            Finding(
                id="internal-diagnostic-section-in-production-testcases",
                severity="warning",
                category="test-case-format",
                title="Production test-case file contains internal diagnostic sections",
                details=(
                    "Files under fts/**/test-cases/*.md must be manual-ready runtime artifacts. "
                    "Design/debug sections belong under fts/**/work/**, evals/**, or dedicated diagnostic reports."
                ),
                path=display_path,
                evidence=production_diagnostic_sections[:20],
                recommended_action="Move diagnostic sections to a work/canary report and keep only test cases in the production file.",
            )
        )

    if production_setup_profile_refs:
        findings.append(
            Finding(
                id="production-setup-profile-reference",
                severity="warning",
                category="preconditions",
                title="Production test cases reference setup profiles",
                details=(
                    "Production test-case files must be self-contained for manual execution and automation. "
                    "Do not replace inline preconditions with reusable setup profile references."
                ),
                path=display_path,
                evidence=production_setup_profile_refs[:20],
                recommended_action="Expand setup profile references into numbered inline precondition steps in each TC.",
            )
        )

    if environment_specific_preconditions:
        findings.append(
            Finding(
                id="environment-specific-precondition",
                severity="warning",
                category="preconditions",
                title="Production preconditions contain environment-specific wording",
                details=(
                    "Production TC preconditions should be environment-agnostic unless a specific stand or environment "
                    "is source-backed execution context."
                ),
                path=display_path,
                evidence=environment_specific_preconditions[:20],
                recommended_action="Replace stand/environment wording with action-oriented setup steps.",
            )
        )

    if project_name_precondition_leaks:
        findings.append(
            Finding(
                id="project-name-leak-in-preconditions",
                severity="warning",
                category="preconditions",
                title="Production preconditions leak project/package names",
                details="Preconditions must not mention project/package names such as AutoFin unless explicitly source-backed as UI or business text.",
                path=display_path,
                evidence=project_name_precondition_leaks[:20],
                recommended_action="Remove project/package names from preconditions or document a source-backed allowlist.",
            )
        )

    if ambiguous_create_or_take_preconditions:
        findings.append(
            Finding(
                id="ambiguous-create-or-take-setup",
                severity="warning",
                category="preconditions",
                title="Production preconditions use ambiguous create-or-take setup",
                details="Manual-ready preconditions must define one reproducible setup path, not alternatives such as create or take an existing record.",
                path=display_path,
                evidence=ambiguous_create_or_take_preconditions[:20],
                recommended_action="Choose one setup path and write it as deterministic numbered steps.",
            )
        )

    if missing_target_revealing_actions:
        findings.append(
            Finding(
                id="missing-target-revealing-action",
                severity="warning",
                category="preconditions",
                title="Contact-person field checks miss the action that reveals the target fields",
                details=(
                    "When a checked field is inside a dynamically created contact-person block, preconditions must "
                    "include the action that creates or reveals that block."
                ),
                path=display_path,
                evidence=missing_target_revealing_actions[:20],
                recommended_action="Add `Нажать кнопку «Добавить контактное лицо»` to preconditions before field input steps.",
            )
        )

    if non_reproducible_preconditions:
        findings.append(
            Finding(
                id="test-case-non-reproducible-precondition",
                severity="warning",
                category="test-case-format",
                title="Test cases use magic UI states in preconditions",
                details=(
                    "`Предусловия` must describe reproducible setup steps, a fixture/API setup, or a reusable setup "
                    "profile. A bare or numbered passive UI state such as a displayed hint, filled field, configured "
                    "switch, created row, enabled manual mode, selected address, added phone or contact person is not "
                    "enough for manual execution or automation. Wait/assertion lines such as `Дождаться...` or "
                    "`Убедиться...` are valid only after an action/setup step that can create the state."
                ),
                path=display_path,
                evidence=non_reproducible_preconditions[:30],
                recommended_action=(
                    "Rewrite preconditions as numbered action setup steps that reach the state, then add any required "
                    "wait/assertion as a separate result check, or name the exact fixture/API setup. If the setup path "
                    "is unknown, use `GAP-*` / `unclear` instead of an executable TC."
                ),
            )
        )

    if ambiguous_precondition_setup:
        findings.append(
            Finding(
                id="test-case-ambiguous-precondition-setup",
                severity="warning",
                category="test-case-format",
                title="Test cases use ambiguous setup alternatives in preconditions",
                details=(
                    "Preconditions must choose one reproducible setup path. Phrases such as `выбрать или ввести`, "
                    "`при необходимости`, `если нужно`, `select or enter` or `if needed` leave automation agents "
                    "without a deterministic preparation path."
                ),
                path=display_path,
                evidence=ambiguous_precondition_setup[:30],
                recommended_action=(
                    "Choose one setup path, split setup variants into separate test cases, or document the exact "
                    "condition that selects the branch."
                ),
            )
        )

    if duplicated_source_reference_fields:
        findings.append(
            Finding(
                id="test-case-duplicated-source-reference-fields",
                severity="warning",
                category="test-case-format",
                title="Test cases duplicate the same source references across metadata fields",
                details=(
                    "`FT Reference`, `Traceability` and `Requirement Source` must have distinct responsibilities. "
                    "Repeating the same ATOM/SRC/DOCX/PDF tuple in multiple fields creates noisy TC metadata and "
                    "makes traceability drift harder to detect."
                ),
                path=display_path,
                evidence=duplicated_source_reference_fields[:30],
                recommended_action=(
                    "Keep machine coverage ids in `Traceability`, keep DOCX/PDF/table/page locator in one source "
                    "reference field, and remove/deprecate redundant `Requirement Source` copies."
                ),
            )
        )

    if dictionary_body_missing_traceability:
        findings.append(
            Finding(
                id="test-case-dictionary-reference-missing-from-traceability",
                severity="warning",
                category="traceability",
                title="Test cases use DICT-* values without DICT-* traceability",
                details=(
                    "When a TC's test data, steps or oracle depend on a dictionary inventory, the same DICT-* id "
                    "must be present in the TC traceability field. Otherwise dictionary coverage is not machine-checkable."
                ),
                path=display_path,
                evidence=dictionary_body_missing_traceability[:30],
                recommended_action="Add every referenced DICT-* id to the affected TC traceability field.",
            )
        )

    if synthetic_requirement_quotes:
        findings.append(
            Finding(
                id="test-case-synthetic-requirement-quote-smell",
                severity="warning",
                category="traceability",
                title="Requirement quote field contains normalized or derived behavior",
                details=(
                    "The requirement quote field should hold a short source quote or explicitly say that the row is "
                    "normalized/derived. Synthetic statements such as `all and only DICT-* values` or GAP-based "
                    "mechanism notes are not source quotes."
                ),
                path=display_path,
                evidence=synthetic_requirement_quotes[:30],
                recommended_action=(
                    "Replace synthetic quote text with the actual source quote, or label it as normalized/derived "
                    "and keep DICT/GAP rationale in traceability or coverage notes."
                ),
            )
        )

    if action_created_block_without_cleanup:
        findings.append(
            Finding(
                id="test-case-action-created-block-without-cleanup",
                severity="warning",
                category="test-design",
                title="Action-created block tests have no cleanup postcondition",
                details=(
                    "A TC that clicks an add/create action usually mutates the form state. `Postconditions: Not "
                    "required` is valid only when the steps themselves delete/discard the created block or the TC "
                    "states that no persistent state is created."
                ),
                path=display_path,
                evidence=action_created_block_without_cleanup[:30],
                recommended_action=(
                    "Add a concrete cleanup postcondition such as deleting the created block or closing without "
                    "saving; keep `Not required` only for self-deleting delete-flow cases."
                ),
            )
        )

    if branch_oracles_without_distinction:
        findings.append(
            Finding(
                id="test-case-branch-oracle-not-distinct",
                severity="warning",
                category="expected-result",
                title="Branch choices have indistinguishable expected results",
                details=(
                    "Separate branch TC for Yes/No, confirm/cancel or save/discard must prove the branch-specific "
                    "effect. If both cases only assert the same destination screen, the TC does not verify the "
                    "semantic difference between the choices."
                ),
                path=display_path,
                evidence=branch_oracles_without_distinction[:20],
                recommended_action=(
                    "Add a branch-specific oracle such as saved/not-saved data, modal remaining/closing, blocked "
                    "navigation or a GAP if the source does not define the difference."
                ),
            )
        )

    if bundled_negative_input_classes:
        findings.append(
            Finding(
                id="test-case-bundled-negative-input-classes",
                severity="warning",
                category="test-design",
                title="Negative input TC bundles multiple invalid classes under one oracle",
                details=(
                    "Several invalid input classes can share one TC only when the TC is explicitly parameterized "
                    "with a value-to-oracle table. A prose list of values checked 'one by one' hides which class failed."
                ),
                path=display_path,
                evidence=bundled_negative_input_classes[:30],
                recommended_action=(
                    "Split materially different invalid classes into separate TC or add a parameter table with "
                    "`value`, `class` and exact observable expected result for each row."
                ),
            )
        )

    if generic_atoms:
        findings.append(
            Finding(
                id="atomic-ledger-generic-atom-smell",
                severity="warning",
                category="traceability",
                title="Atomic ledger contains generic non-verifiable atom statements",
                details=(
                    "Ledger rows should decompose source requirements into concrete, checkable behavior. "
                    "Generic rows such as 'Требование GSR N выполняется' hide missing decomposition."
                ),
                path=display_path,
                evidence=generic_atoms[:20],
                recommended_action="Rewrite affected atoms into concrete field/action/condition/expected behavior rows or mark non-observable parts as GAP/unclear.",
            )
        )
    if compressed_atoms:
        findings.append(
            Finding(
                id="atomic-ledger-compressed-range-smell",
                severity="warning",
                category="atomarity",
                title="Atomic ledger appears to compress multiple requirement codes into broad atoms",
                details=(
                    "A ledger row that spans several requirement codes and mixes multiple independent behavior "
                    "markers is likely a compact draft. Writer should split it instead of optimizing for a shorter, "
                    "validator-friendly artifact."
                ),
                path=display_path,
                evidence=compressed_atoms[:20],
                recommended_action=(
                    "Split the affected ATOM-* rows by independent rule/property, or leave non-observable parts "
                    "as GAP/unclear. If the file was shortened because of a command/context limit, rewrite it "
                    "package-by-package with chunked artifact writing."
                ),
            )
        )
    if covered_range_atoms:
        findings.append(
            Finding(
                id="covered-atom-gsr-range-compression-smell",
                severity="warning",
                category="atomarity",
                title="Covered atoms use broad requirement-code ranges",
                details=(
                    "A covered ATOM-* that spans a broad GSR/REQ range is likely compressing independent rules. "
                    "Traceability preservation is not enough; each independent rule needs its own atom or GAP."
                ),
                path=display_path,
                evidence=covered_range_atoms[:20],
                recommended_action="Split broad covered atoms into atomic rows, or mark unobservable/ambiguous parts as GAP/unclear.",
            )
        )
    if combined_atoms:
        findings.append(
            Finding(
                id="atomic-ledger-combined-behavior-smell",
                severity="warning",
                category="atomarity",
                title="Atomic ledger rows combine multiple behaviors",
                details=(
                    "ATOM-* rows should not combine independent properties such as visibility, requiredness, "
                    "editability, format, dependency branches and validation classes."
                ),
                path=display_path,
                evidence=combined_atoms[:20],
                recommended_action="Split affected ATOM-* rows into one behavior per atom before mapping them to plan rows and TC.",
            )
        )
    if table_residue_atoms:
        findings.append(
            Finding(
                id="atomic-ledger-source-table-residue-smell",
                severity="warning",
                category="traceability",
                title="Atomic ledger contains source table extraction residue",
                details=(
                    "ATOM-* rows should be built from clean normalized source rows. Table headers, neighboring fields "
                    "and page/table residue make coverage claims unreliable."
                ),
                path=display_path,
                evidence=table_residue_atoms[:20],
                recommended_action=(
                    "Add or fix Source Table Normalization, split polluted rows into clean atoms, and change partial or "
                    "low-confidence rows to GAP/unclear until the source is confirmed."
                ),
            )
        )

    if generic_titles:
        findings.append(
            Finding(
                id="test-case-generic-title-smell",
                severity="warning",
                category="test-case-format",
                title="Test-case titles are templated instead of naming the concrete check",
                details=(
                    "A TC title should name the field/action and the single behavior under test. "
                    "Template phrases such as 'проверяет Поле...' hide weak decomposition."
                ),
                path=display_path,
                evidence=generic_titles[:20],
                recommended_action="Rewrite titles so each one states one concrete positive, negative, boundary, dependency or gap check.",
            )
        )

    if process_marker_titles:
        findings.append(
            Finding(
                id="test-case-title-process-marker-smell",
                severity="warning",
                category="test-case-format",
                title="Test-case title contains process markers",
                details=(
                    "`Название` must describe the business check. Candidate/oracle/UI calibration status belongs "
                    "in body metadata fields, not in the title taxonomy."
                ),
                path=display_path,
                evidence=process_marker_titles[:20],
                recommended_action=(
                    "Remove process markers from `Название` and keep candidate status in `Статус oracle`, "
                    "`Статус тест-кейса` and `Требуется подтверждение` fields."
                ),
            )
        )

    if generic_test_cases:
        findings.append(
            Finding(
                id="test-case-generic-executable-smell",
                severity="warning",
                category="test-case-format",
                title="Test cases contain generic non-executable steps or data",
                details=(
                    "Manual TC steps must be executable without reconstructing the action from the ledger. "
                    "Generic phrases such as 'Выполнить проверяемое действие' are not enough for pass/fail execution."
                ),
                path=display_path,
                evidence=generic_test_cases[:20],
                recommended_action="Replace generic placeholders with concrete preconditions, data, steps, and observable expected results.",
            )
        )

    if value_type_list_selection_smells:
        findings.append(
            Finding(
                id="test-case-value-type-list-selection-smell",
                severity="warning",
                category="traceability",
                title="Value-type atoms are covered by list-selection checks",
                details=(
                    "A source property such as `тип значения: Строка/Дата/Логическое` is metadata or an input "
                    "class, not proof that the control opens a reference list. Covering value-type atoms with "
                    "generic list-selection TC creates fake coverage and masks missing format/input checks."
                ),
                path=display_path,
                evidence=value_type_list_selection_smells[:20],
                recommended_action=(
                    "Remap non-list value-type atoms to observable format/input behavior or GAP/unclear. "
                    "Use list-selection TC only for source rows that explicitly define a list/dictionary value source."
                ),
            )
        )

    if dependency_placeholder_setup_smells:
        findings.append(
            Finding(
                id="test-case-dependency-placeholder-setup-smell",
                severity="warning",
                category="test-case-format",
                title="Dependency test cases use placeholder setup instead of concrete controlling values",
                details=(
                    "A dependency TC is not executable when it says only `В форме задать данные, при которых ...`. "
                    "The steps must name the controlling field, exact value/action, and the branch being exercised."
                ),
                path=display_path,
                evidence=dependency_placeholder_setup_smells[:20],
                recommended_action=(
                    "Rewrite each dependency setup as concrete UI actions, for example set the named toggle/list field "
                    "to the exact value that makes the condition true or false."
                ),
            )
        )

    if mockup_generic_ui_steps:
        findings.append(
            Finding(
                id="test-case-mockup-interaction-hints-not-used",
                severity="warning",
                category="test-case-format",
                title="UI steps stay generic despite available mockup interaction hints",
                details=(
                    "When `mockup-visual-inventory.md` is opened and `used_for_steps = yes`, TC steps should use "
                    "the recorded UI mechanics such as click/select/toggle/check/open calendar. Generic instructions "
                    "like entering a value from test data into every field ignore the mockup's purpose."
                ),
                path=display_path,
                evidence=mockup_generic_ui_steps[:20],
                recommended_action=(
                    "Rewrite affected UI steps using the interaction hints from mockup-visual-inventory.md. "
                    "Keep FT/source artifacts as the source of business rules and expected results."
                ),
            )
        )

    if positive_type_negative_oracle:
        findings.append(
            Finding(
                id="test-case-positive-type-with-negative-oracle",
                severity="warning",
                category="expected-result",
                title="Positive test-case type conflicts with rejection/invalid expected result",
                details=(
                    "`Type: Positive` cannot be used for TC whose primary oracle is rejection, invalid state, "
                    "no-save behavior or a value outside min/max. This hides missing negative/boundary coverage."
                ),
                path=display_path,
                evidence=positive_type_negative_oracle[:20],
                recommended_action="Change the TC type to Negative/Boundary or split positive acceptance and negative rejection into separate cases.",
            )
        )

    if negative_type_without_negative_oracle:
        findings.append(
            Finding(
                id="test-case-negative-type-without-negative-oracle",
                severity="warning",
                category="expected-result",
                title="Negative test-case type has no negative oracle",
                details=(
                    "`Type: Negative` must prove a rejection, invalid state, no-save behavior or another negative "
                    "outcome. A negative TC that only shows acceptance/valid behavior is not negative coverage."
                ),
                path=display_path,
                evidence=negative_type_without_negative_oracle[:20],
                recommended_action=(
                    "Replace the expected result with an observable negative oracle and invalid input class, "
                    "or change the TC type to Positive if it is a valid acceptance check."
                ),
            )
        )

    if generic_valid_fixture_placeholders:
        findings.append(
            Finding(
                id="test-case-generic-valid-fixture-smell",
                severity="warning",
                category="test-case-format",
                title="Test cases use unresolved generic valid fixture data",
                details=(
                    "A manual TC is not reproducible when it relies on `Минимальный валидный набор данных`, "
                    "`валидные данные` or conditional baseline wording without a concrete fixture, values or "
                    "explicitly linked artifact."
                ),
                path=display_path,
                evidence=generic_valid_fixture_placeholders[:20],
                recommended_action=(
                    "Replace generic baseline wording with executable preconditions/test data, link a concrete "
                    "fixture artifact, or move the blocked setup to GAP/unclear."
                ),
            )
        )

    if generic_test_data_references:
        findings.append(
            Finding(
                id="test-case-generic-test-data-reference-smell",
                severity="warning",
                category="test-case-format",
                title="Steps refer to test data while the data are only a generic baseline",
                details=(
                    "A step such as `ввести значение из тестовых данных` is executable only when the test data "
                    "contain the concrete input value. If test data contain a generic valid baseline, the TC has "
                    "no actual value to enter."
                ),
                path=display_path,
                evidence=generic_test_data_references[:20],
                recommended_action="Put the concrete literal/parameter in Test Data and name it in the step, or create a GAP/unclear.",
            )
        )

    if generic_expected_results:
        findings.append(
            Finding(
                id="test-case-generic-expected-result-smell",
                severity="warning",
                category="expected-result",
                title="Expected results restate the FT rule instead of a pass/fail oracle",
                details=(
                    "Expected results must describe an observable state. Repeating 'соответствует ФТ' or "
                    "'поле принимает только ...' forces the executor to reconstruct the oracle from the source."
                ),
                path=display_path,
                evidence=generic_expected_results[:20],
                recommended_action="Replace rule restatements with observable UI/API/document/log outcomes or move unobservable behavior to GAP/unclear.",
            )
        )

    if generic_test_data_oracles:
        findings.append(
            Finding(
                id="test-case-generic-test-data-oracle-smell",
                severity="warning",
                category="expected-result",
                title="Expected results refer to test data instead of naming the checked value",
                details=(
                    "Expected results such as `Значение из тестовых данных принято` force the executor or reviewer "
                    "to look elsewhere for the oracle. The expected result should name the exact value or the "
                    "observable field state directly."
                ),
                path=display_path,
                evidence=generic_test_data_oracles[:20],
                recommended_action=(
                    "Rewrite expected results to name the concrete value and observable result, for example "
                    "`значение 2000 отображается в поле` or `значение 1999 не добавляется/не принимается`."
                ),
            )
        )

    if generic_rule_oracles:
        findings.append(
            Finding(
                id="test-case-generic-rule-oracle-smell",
                severity="warning",
                category="expected-result",
                title="Test cases use a generic rule-oracle instead of a concrete observable result",
                details=(
                    "Phrases such as `видимое состояние после действия соответствует одному наблюдаемому правилу` "
                    "do not tell the tester what state to observe. They restate that some rule exists instead of "
                    "providing an executable oracle."
                ),
                path=display_path,
                evidence=generic_rule_oracles[:20],
                recommended_action=(
                    "Replace the generic rule-oracle with the exact observable UI state, value, marker, rejection, "
                    "transition or GAP/unclear for the affected atom."
                ),
            )
        )

    if source_dump_oracles:
        findings.append(
            Finding(
                id="test-case-source-dump-oracle-smell",
                severity="warning",
                category="expected-result",
                title="Test cases paste source/GSR text instead of an executable oracle",
                details=(
                    "Expected results must describe what the tester observes. Phrases such as "
                    "`наблюдается правило из GSR ...` followed by a source fragment make the TC depend on "
                    "re-interpreting the FT instead of providing a concrete pass/fail oracle."
                ),
                path=display_path,
                evidence=source_dump_oracles[:20],
                recommended_action=(
                    "Rewrite the affected expected results into explicit observable states, values, validation "
                    "outcomes, control availability or GAP/unclear. Keep raw GSR/source text only in traceability "
                    "or source quote fields."
                ),
            )
        )

    if value_type_metadata_as_behavior:
        findings.append(
            Finding(
                id="test-case-value-type-metadata-as-behavior-smell",
                severity="warning",
                category="traceability",
                title="Value-type metadata is treated as standalone executable behavior",
                details=(
                    "`тип значения: Строка/Дата/Логическое` is metadata unless the source also defines a concrete "
                    "observable UI/input behavior. Turning it into a standalone TC such as `field accepts a string "
                    "value` creates fake coverage, especially when the same field has numeric, date, phone, email, "
                    "length or format constraints."
                ),
                path=display_path,
                evidence=value_type_metadata_as_behavior[:20],
                recommended_action=(
                    "Cover non-list value-type rows through the concrete input/format/widget rules derived from "
                    "source artifacts, or mark the metadata-only row as GAP/unclear. Do not create separate positive "
                    "TC for generic string acceptance."
                ),
            )
        )

    if extraction_artifact_oracles:
        findings.append(
            Finding(
                id="test-case-extraction-artifact-oracle-smell",
                severity="warning",
                category="expected-result",
                title="Expected results contain DOCX/PDF extraction artifacts",
                details=(
                    "Split words, table-header residue and column spillover in expected results indicate that the "
                    "writer copied raw extraction text instead of normalizing it into executable UI behavior."
                ),
                path=display_path,
                evidence=extraction_artifact_oracles[:20],
                recommended_action=(
                    "Clean the source fragment in Source Table Normalization first, then rewrite TC expected "
                    "results as observable behavior. Put uncertain extraction fragments into GAP/unclear."
                ),
            )
        )

    if requiredness_without_empty_or_marker:
        findings.append(
            Finding(
                id="test-case-requiredness-without-empty-or-marker-check",
                severity="warning",
                category="test-design",
                title="Requiredness checks do not test an empty value or a visible required marker",
                details=(
                    "Requiredness marker coverage and requiredness enforcement are different checks. "
                    "Filling a required field does not prove either unless the TC observes a marker or validates an empty value."
                ),
                path=display_path,
                evidence=requiredness_without_empty_or_marker[:20],
                recommended_action=(
                    "For UI marker checks, observe the required indicator. For enforcement checks, leave the field empty "
                    "and trigger the confirmed validation action; if that action is out of scope, use GAP/unclear."
                ),
            )
        )

    if boundary_without_classes:
        findings.append(
            Finding(
                id="test-case-boundary-without-boundary-classes",
                severity="warning",
                category="test-design",
                title="Boundary test cases do not name boundary classes",
                details="Boundary TC need concrete or parameterized classes such as min-1/min/min+1 and max-1/max/max+1.",
                path=display_path,
                evidence=boundary_without_classes[:20],
                recommended_action="Add concrete values or named parameterized boundary classes, or move unknown limits to GAP/unclear.",
            )
        )

    if boundary_rejection_without_acceptance:
        findings.append(
            Finding(
                id="test-case-boundary-rejection-without-on-boundary-acceptance",
                severity="warning",
                category="test-design",
                title="Boundary rejection checks do not prove acceptance at the boundary",
                details=(
                    "Rejecting min-1/max+1 values is not enough for boundary coverage. The suite also needs "
                    "separate acceptance checks for exact min and exact max, or a GAP if the exact limits are not known."
                ),
                path=display_path,
                evidence=boundary_rejection_without_acceptance[:20],
                recommended_action=(
                    "Add separate positive/boundary-positive TC for exact min and exact max values using concrete "
                    "or parameterized values, or link the missing boundary oracle to GAP/unclear."
                ),
            )
        )

    if merged_valid_invalid_test_cases:
        findings.append(
            Finding(
                id="test-case-merged-valid-invalid-smell",
                severity="warning",
                category="atomarity",
                title="Test cases merge valid and invalid checks",
                details=(
                    "A TC should have one primary pass/fail oracle. Checking that invalid input is rejected and "
                    "valid input is accepted in the same executable TC hides two independent checks."
                ),
                path=display_path,
                evidence=merged_valid_invalid_test_cases[:20],
                recommended_action=(
                    "Split valid acceptance and invalid rejection into separate TC-* sections. If valid input is "
                    "used only to recover after an error, mark the TC as an explicit recovery scenario and make "
                    "recovery the single expected behavior."
                ),
            )
        )

    if numeric_only_valid_data_invalid:
        findings.append(
            Finding(
                id="test-case-numeric-only-valid-data-invalid-smell",
                severity="warning",
                category="test-data",
                title="Numeric-only checks use non-numeric data as valid input",
                details=(
                    "When a TC claims a numeric-only rule, the marked valid value must be numeric or an explicit "
                    "numeric boundary parameter. A value such as `A-123` is an invalid class, not positive data."
                ),
                path=display_path,
                evidence=numeric_only_valid_data_invalid[:20],
                recommended_action=(
                    "Replace the valid value with a concrete numeric value or parameterized numeric boundary, and keep "
                    "non-numeric values in separate negative TC-* sections."
                ),
            )
        )

    if valid_data_class_label_mismatch:
        findings.append(
            Finding(
                id="test-case-valid-data-class-label-mismatch-smell",
                severity="warning",
                category="test-data",
                title="Valid test data has a contradictory equivalence class label",
                details=(
                    "A positive test datum must not pair a numeric value with an alphabetic/special-character class "
                    "label such as `ABC` or `letters`. That makes the intended equivalence class ambiguous."
                ),
                path=display_path,
                evidence=valid_data_class_label_mismatch[:20],
                recommended_action=(
                    "Align the class label with the valid value, or split the alphabetic/special-character class into "
                    "a separate negative TC/GAP."
                ),
            )
        )

    if numeric_class_label_raw_literal_mismatch:
        findings.append(
            Finding(
                id="test-case-numeric-class-label-raw-literal-smell",
                severity="warning",
                category="test-data",
                title="Numeric test data uses a raw literal as an equivalence class label",
                details=(
                    "The `class` field should name the equivalence or boundary class, not a second numeric value. "
                    "Pairs such as `Допустимое значение: 123456; класс: 12345` make it unclear which input is "
                    "actually valid and often hide off-by-one length mistakes."
                ),
                path=display_path,
                evidence=numeric_class_label_raw_literal_mismatch[:20],
                recommended_action=(
                    "Replace numeric raw class labels with semantic classes such as `6 digits`, `N digits`, "
                    "`exact max length`, or split the second numeric value into a separate TC if it is a real input."
                ),
            )
        )

    if input_restriction_transition_oracles:
        findings.append(
            Finding(
                id="test-case-input-restriction-transition-oracle-smell",
                severity="warning",
                category="expected-result",
                title="Field-level input restriction is tested through transition validation",
                details=(
                    "When the source defines an input or format restriction for a field, such as `only N digits`, "
                    "`only numeric characters`, a mask, maximum/exact length or allowed characters, the TC should "
                    "verify the displayed field value after input. Transition/save validation is a different "
                    "mechanism and should be used only when the source explicitly defines validation on that action. "
                    "Underlength or empty required values may still require a validation action."
                ),
                path=display_path,
                evidence=input_restriction_transition_oracles[:30],
                recommended_action=(
                    "Remove the transition action from the input-restriction TC and assert the field state after "
                    "the attempted input, for example `123456` is displayed and the seventh digit is not added."
                ),
            )
        )

    if unsupported_numeric_validation_feedback:
        findings.append(
            Finding(
                id="test-case-unsupported-numeric-validation-feedback-smell",
                severity="warning",
                category="expected-result",
                title="Numeric rejection test assumes unsupported UI validation feedback",
                details=(
                    "A numeric/input-restriction rule such as `only digits`, `non-digit values are not accepted` or "
                    "`below minimum is not accepted` does not by itself prove red highlighting or blocked navigation. "
                    "Those are separate UI feedback mechanisms and need direct source evidence."
                ),
                path=display_path,
                evidence=unsupported_numeric_validation_feedback[:30],
                recommended_action=(
                    "Replace red-highlight/blocked-transition expected results with a source-backed field-state "
                    "oracle, or add explicit source evidence for the validation marker/navigation behavior."
                ),
            )
        )

    if mechanical_field_steps:
        findings.append(
            Finding(
                id="test-case-mechanical-field-step-smell",
                severity="warning",
                category="steps",
                title="Test-case step uses mechanical field interaction wording",
                details=(
                    "Manual TC steps should describe the user's intent, not mouse-specific field mechanics. "
                    "For ordinary text input use `Ввести <значение> в поле <название>`; for dates use "
                    "`Указать <дату> в поле <название>`. Use field activation wording only when activation/focus "
                    "is the source-backed behavior under test."
                ),
                path=display_path,
                evidence=mechanical_field_steps[:30],
                recommended_action=(
                    "Replace `щелкнуть поле ... и набрать ...` / `набрать ...` with intention-level steps such as "
                    "`Ввести <значение> в поле <название>`."
                ),
            )
        )

    if unsupported_input_filtering_oracles:
        findings.append(
            Finding(
                id="test-case-unsupported-input-filtering-oracle-smell",
                severity="warning",
                category="expected-result",
                title="Numeric-only test cases assume input filtering without source evidence",
                details=(
                    "A source rule such as `only digits` defines the allowed value class, but it does not by itself "
                    "prove the UI mechanism. Filtering, ignored characters, stripped symbols, field-level errors and "
                    "transition validation are different observable behaviors."
                ),
                path=display_path,
                evidence=unsupported_input_filtering_oracles[:20],
                recommended_action=(
                    "Rewrite the expected result to a source-backed validation outcome, add evidence that the UI "
                    "filters input, or move the exact enforcement mechanism to GAP/unclear."
                ),
            )
        )

    if negative_transition_without_valid_fixture:
        findings.append(
            Finding(
                id="test-case-negative-transition-without-valid-fixture-smell",
                severity="warning",
                category="test-design",
                title="Negative transition validation is not isolated by a full valid fixture",
                details=(
                    "When a negative TC clicks `Следующий шаг` or another transition action, all unrelated required "
                    "fields in the selected branch must be valid. Otherwise the rejected transition cannot be "
                    "attributed to the field under test."
                ),
                path=display_path,
                evidence=negative_transition_without_valid_fixture[:20],
                recommended_action=(
                    "Add a named full-valid fixture for every other required field, or limit the TC to a field-level "
                    "validation marker that does not depend on the transition action."
                ),
            )
        )

    if forbidden_formulations:
        findings.append(
            Finding(
                id="test-case-forbidden-formulation-smell",
                severity="warning",
                category="test-case-format",
                title="Test cases contain forbidden or noncanonical formulations",
                details=(
                    "Canonical TC wording must name a concrete value, action and observable oracle. Phrases such as "
                    "`считается невалидным`, generic `пробельный/буквенный символ`, fixture shorthands and "
                    "`соответствующий блок` let weak wording pass as a test oracle."
                ),
                path=display_path,
                evidence=forbidden_formulations[:30],
                recommended_action=(
                    "Replace every listed phrase with a concrete input value and observable UI outcome, or move the "
                    "undefined behavior to Coverage Gaps instead of keeping it inside an executable TC."
                ),
            )
        )

    if abstract_oracles:
        findings.append(
            Finding(
                id="test-case-abstract-oracle-smell",
                severity="warning",
                category="expected-result",
                title="Expected result is an abstract rule verdict, not an observable oracle",
                details=(
                    "A manual TC cannot be passed or failed from `valid/invalid according to the rule` alone. The "
                    "expected result must name what the tester observes: displayed value, blocked transition, "
                    "message, marker, hidden/visible element, saved value, or another concrete artifact."
                ),
                path=display_path,
                evidence=abstract_oracles[:30],
                recommended_action="Rewrite the expected result using one concrete oracle class from the canonical test-case format reference.",
            )
        )

    if negative_input_without_observable_oracle:
        findings.append(
            Finding(
                id="test-case-negative-input-without-observable-oracle",
                severity="warning",
                category="expected-result",
                title="Negative input TC lacks an observable enforcement point",
                details=(
                    "Typing an invalid value and saying it is invalid does not define how the tester verifies the "
                    "system response. A negative input TC must either check a field-level observable state or perform "
                    "a validated action with all unrelated required fields isolated by a valid baseline."
                ),
                path=display_path,
                evidence=negative_input_without_observable_oracle[:30],
                recommended_action=(
                    "Add a source-backed field-level oracle, or trigger a validation action such as `Следующий шаг` "
                    "and include a valid baseline for all unrelated required fields."
                ),
            )
        )

    if date_dependent_absolute_dates:
        findings.append(
            Finding(
                id="test-case-date-dependent-absolute-date-smell",
                severity="warning",
                category="test-data",
                title="Date-dependent TC uses absolute dates without a fixed baseline date",
                details=(
                    "Rules tied to the current date are not stable unless the TC fixes the business/system date in "
                    "preconditions. Putting `Дата проверки` only in test data does not isolate the environment."
                ),
                path=display_path,
                evidence=date_dependent_absolute_dates[:30],
                recommended_action=(
                    "Move the fixed business/system date to preconditions, then calculate every absolute test date "
                    "relative to that baseline."
                ),
            )
        )

    if rolling_date_boundary_static_data:
        severity = rolling_date_boundary_severity(rolling_date_boundary_policy)
        findings.append(
            Finding(
                id="rolling-date-boundary-static-test-data",
                severity=severity,
                category="test-data",
                title="Rolling date boundary TC uses static calendar test data",
                details=(
                    "A TC tied to the current application date, future date, today/tomorrow or an age/current-date "
                    "boundary must not use a fixed absolute calendar date as the only boundary or negative value. "
                    "The test data must define an execution-relative formula such as D or D + 1 calendar day."
                ),
                path=display_path,
                evidence=rolling_date_boundary_static_data[:30],
                recommended_action=(
                    "Replace the fixed boundary value with calculated test data: define D as the current application "
                    "date at test execution, state the date format, and include an example. If the source of D is "
                    "unclear, add a BA question for application/server/business/browser date source."
                ),
            )
        )

    if action_treated_as_required_field:
        findings.append(
            Finding(
                id="test-case-action-treated-as-required-field-smell",
                severity="warning",
                category="traceability",
                title="Action/button is treated as a required input field",
                details=(
                    "Actions such as `Следующий шаг`, `Назад`, `Проверить` or `Отправить повторно` are not input "
                    "fields. Requiredness or empty-value checks for these controls usually indicate semantic drift "
                    "from the source requirement."
                ),
                path=display_path,
                evidence=action_treated_as_required_field[:20],
                recommended_action=(
                    "Re-map the action requirement to availability, click result, transition or GAP/unclear; do not "
                    "test action controls by leaving them empty as fields."
                ),
            )
        )

    if action_without_observable_artifact:
        findings.append(
            Finding(
                id="test-case-action-without-observable-artifact-smell",
                severity="warning",
                category="expected-result",
                title="Action test cases claim initiation without an observable artifact",
                details=(
                    "A TC cannot mark an async/API/internal action as covered by saying the action is initiated "
                    "unless the expected result names a concrete UI, log, API, mock, document or other artifact "
                    "that proves the initiation."
                ),
                path=display_path,
                evidence=action_without_observable_artifact[:20],
                recommended_action=(
                    "Name the confirmed observable artifact and expected state, or move the affected action atom "
                    "to GAP/unclear instead of `covered`."
                ),
            )
        )

    if gap_placeholder_sections:
        findings.append(
            Finding(
                id="test-case-gap-placeholder-section-smell",
                severity="warning",
                category="test-case-format",
                title="Gap-only placeholder sections are listed as TC cases",
                details=(
                    "A GAP/unclear note is not an executable manual test case. Keeping metadata-only GAP placeholders "
                    "under `## TC-*` inflates TC counts and makes downstream coverage look stronger than it is."
                ),
                path=display_path,
                evidence=gap_placeholder_sections[:20],
                recommended_action=(
                    "Move gap-only placeholders to Coverage Gaps, Atomic Requirements Ledger, Package Test Design Plan "
                    "or traceability matrix. Keep `## TC-*` sections for executable checks with steps and observable oracle."
                ),
            )
        )

    if nondeterministic_alternative_oracles:
        findings.append(
            Finding(
                id="test-case-nondeterministic-alternative-oracle-smell",
                severity="warning",
                category="expected-result",
                title="Negative expected results use alternative possible outcomes",
                details=(
                    "Expected results such as `value is cleared, not saved, or highlighted` are not deterministic "
                    "pass/fail oracles. They allow several materially different UI behaviors without source-backed "
                    "selection of the expected one."
                ),
                path=display_path,
                evidence=nondeterministic_alternative_oracles[:20],
                recommended_action=(
                    "Choose one confirmed observable outcome from FT/mockup/API evidence, or mark the exact UI reaction "
                    "as GAP/unclear instead of allowing alternative outcomes in one TC."
                ),
            )
        )

    if (
        production_test_case_file
        and source_row_inventory_required(content)
        and EDITABLE_CARD_SCOPE_RE.search(content)
        and not SAVE_PERSISTENCE_COVERAGE_RE.search(content)
        and not PERSISTENCE_OUT_OF_SCOPE_RE.search(content)
    ):
        persist_coverage_missing.append("editable application-card scope has no save/persist smoke plan or out-of-scope rationale")

    if missing_representative_strategy:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="missing-representative-strategy",
                severity=severity,
                category="test-design",
                title="Partial similar-field coverage lacks representative strategy",
                details=(
                    "When an artifact explicitly says coverage is partial, sampled or representative for similar "
                    "fields with a shared rule, it must document why the selected representatives are enough and "
                    "what residual risk remains."
                ),
                path=display_path,
                evidence=missing_representative_strategy[:20],
                recommended_action=(
                    "Add a representative or pairwise strategy with selected fields/classes, excluded similar "
                    "fields, rationale and residual risk; otherwise add the missing TC/GAP coverage."
                ),
            )
        )

    if representative_strategy_without_omitted_combinations:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="representative-strategy-without-omitted-combinations",
                severity=severity,
                category="test-design",
                title="Representative strategy omits untested combinations",
                details=(
                    "A representative or pairwise strategy is only auditable when it states which similar fields, "
                    "classes or combinations are intentionally not covered by executable TC."
                ),
                path=display_path,
                evidence=representative_strategy_without_omitted_combinations[:20],
                recommended_action=(
                    "List omitted fields/classes/combinations, or add the missing TC/GAP items instead of relying "
                    "on an implicit representative shortcut."
                ),
            )
        )

    if representative_strategy_without_residual_risk:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="representative-strategy-without-residual-risk",
                severity=severity,
                category="test-design",
                title="Representative strategy omits residual risk",
                details=(
                    "Representative or pairwise coverage still leaves field-specific and combination-specific risk. "
                    "The artifact must make that risk explicit so reviewer sign-off is not based on hidden coverage debt."
                ),
                path=display_path,
                evidence=representative_strategy_without_residual_risk[:20],
                recommended_action="Add a residual risk statement or expand executable TC/GAP coverage.",
            )
        )

    if broad_scenario_test_cases:
        findings.append(
            Finding(
                id="scenario-tc-replaces-atomic-coverage-smell",
                severity="warning",
                category="atomarity",
                title="Scenario test cases appear to replace atomic coverage",
                details=(
                    "Scenario/use-case TC are allowed as an additional flow check, but they must not replace atomic "
                    "positive, negative, boundary, dependency or action checks for broad requirement ranges."
                ),
                path=display_path,
                evidence=broad_scenario_test_cases[:20],
                recommended_action="Keep scenario TC only as supplemental coverage and add atomic TC/GAP items for the underlying requirement classes.",
            )
        )

    if excessive_atom_fan_in:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="test-case-excessive-atom-fan-in",
                severity=severity,
                category="atomarity",
                title="Some test cases reference too many atoms without scenario rationale",
                details=(
                    "A TC that closes many atoms often hides independent checks and makes coverage unverifiable. "
                    "Use separate cases unless this is an explicit scenario/use-case package."
                ),
                path=display_path,
                evidence=excessive_atom_fan_in[:20],
                recommended_action="Split high fan-in TC blocks into atomic checks or add an explicit scenario/use-case rationale and keep atomic checks elsewhere.",
            )
        )

    if overmerged_test_cases:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="test-case-overmerged-atoms-without-rationale",
                severity=severity,
                category="atomarity",
                title="Test cases reference more than two atoms without scenario rationale",
                details=(
                    "More than two linked atoms usually means the TC is carrying independent checks. This is allowed "
                    "only for an explicit scenario/use-case case with a scenario rationale and separate atomic coverage elsewhere."
                ),
                path=display_path,
                evidence=overmerged_test_cases[:20],
                recommended_action="Split the TC or add `Сценарное обоснование` and keep independent atomic TC/GAP coverage.",
            )
        )

    if tc_type_expected_result_mismatch:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="tc-type-expected-result-mismatch",
                severity=severity,
                category="test-design",
                title="TC type conflicts with validation/error expected result",
                details="Positive TC must not expect validation error, highlight, rejection or required-field feedback.",
                path=display_path,
                evidence=tc_type_expected_result_mismatch[:20],
                recommended_action="Change type to Negative / Validation Negative or split/add a positive pair.",
            )
        )

    if trace_not_exercised_by_steps:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="trace-not-exercised-by-steps",
                severity=severity,
                category="traceability",
                title="Trace references behavior not exercised by the TC",
                details="Each traced source behavior must be exercised by title, test data, steps, expected result or scenario rationale.",
                path=display_path,
                evidence=trace_not_exercised_by_steps[:20],
                recommended_action="Remove the unexercised trace or split/add a TC for that source behavior.",
            )
        )

    if multiple_independent_assertions:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="multiple-independent-assertions-in-one-tc",
                severity=severity,
                category="atomarity",
                title="TC combines independent assertions",
                details="Dictionary completeness and conditional branch display are independent pass/fail checks and must not be bundled in one TC.",
                path=display_path,
                evidence=multiple_independent_assertions[:20],
                recommended_action="Split into separate TC for dictionary values and conditional branch behavior.",
            )
        )

    if representative_strategy_data_mismatches:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="representative-strategy-data-mismatch",
                severity=severity,
                category="test-design",
                title="Representative strategy does not match concrete test data",
                details="Representative/pairwise strategy must describe the actual concrete values and invalid classes used by the TC.",
                path=display_path,
                evidence=representative_strategy_data_mismatches[:20],
                recommended_action="Align strategy text with test data or change data to match the stated representative class.",
            )
        )

    if production_internal_language_leaks:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="production-artifact-internal-language-leak",
                severity=severity,
                category="test-case-format",
                title="Production TC leaks internal English strategy labels",
                details="Russian production TC should not expose internal English strategy fields.",
                path=display_path,
                evidence=production_internal_language_leaks[:20],
                recommended_action="Use Russian production labels or move detailed strategy to work artifacts.",
            )
        )

    if candidate_negative_trigger_missing:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="candidate-negative-validation-trigger-missing",
                severity=severity,
                category="test-design",
                title="Candidate-negative TC lacks neutral validation trigger",
                details="Entering an invalid value is not enough; the TC must complete input or initiate an available validation point without inventing exact rejection mechanics.",
                path=display_path,
                evidence=candidate_negative_trigger_missing[:20],
                recommended_action="Add focus/completion/validation/save-attempt trigger step or a BA question about trigger selection.",
            )
        )

    if candidate_negative_trigger_too_specific:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="candidate-negative-trigger-too-specific",
                severity=severity,
                category="test-design",
                title="Candidate-negative trigger assumes a specific UI validation mechanism",
                details=(
                    "A UI-calibration candidate may trigger validation, but it must not imply that blur/focus loss is "
                    "the confirmed mechanism unless that is source-backed or calibrated."
                ),
                path=display_path,
                evidence=candidate_negative_trigger_too_specific[:20],
                recommended_action=(
                    "Use neutral wording such as focus loss or another available validation action, and record the "
                    "actual trigger during UI calibration."
                ),
            )
        )

    if scenario_rationale_stimulus_mismatches:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="scenario-rationale-stimulus-mismatch",
                severity=severity,
                category="atomarity",
                title="Scenario rationale does not match the stimulus exercised by steps",
                details=(
                    "A TC that enters data and selects a DaData suggestion must not be justified only as initial "
                    "visibility/default-state coverage, and a visibility-only title must not hide input/selection steps."
                ),
                path=display_path,
                evidence=scenario_rationale_stimulus_mismatches[:20],
                recommended_action="Rewrite the title/rationale to match the exercised stimulus or split visibility and selection checks.",
            )
        )

    if persistence_tc_without_save_action:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="persistence-tc-without-save-action",
                severity=severity,
                category="test-design",
                title="Persistence TC has no save action",
                details="A persistence/save-reopen TC must perform a save action before leaving or reopening the card.",
                path=display_path,
                evidence=persistence_tc_without_save_action[:20],
                recommended_action="Add a source-backed save action, or mark the TC as requiring confirmation if the exact save flow is unknown.",
            )
        )

    if persistence_tc_without_reopen_verification:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="persistence-tc-without-reopen-verification",
                severity=severity,
                category="test-design",
                title="Persistence TC lacks reopen verification",
                details="Saving data in the same open form does not prove persistence; the TC must reopen/reload the card and verify the value after reopen.",
                path=display_path,
                evidence=persistence_tc_without_reopen_verification[:20],
                recommended_action="Close/leave/reload, reopen the same card, and assert the saved value after reopen.",
            )
        )

    if persistence_tc_closes_without_saving:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="persistence-tc-closes-without-saving",
                severity=severity,
                category="test-design",
                title="Persistence TC closes without saving",
                details="A save/reopen smoke TC must not use close-without-saving as its cleanup or primary exit path.",
                path=display_path,
                evidence=persistence_tc_closes_without_saving[:20],
                recommended_action="Save first, verify after reopen, then use a separate cleanup/isolation strategy.",
            )
        )

    if persistence_tc_unsourced_save_action:
        findings.append(
            Finding(
                id="persistence-tc-unsourced-save-action",
                severity="warning",
                category="test-design",
                title="Persistence TC uses an unsourced concrete save action",
                details="A named save button/action must be source-backed or explicitly marked for BA/UI confirmation.",
                path=display_path,
                evidence=persistence_tc_unsourced_save_action[:20],
                recommended_action="Cite the source inventory for the save action, or replace the concrete action with a confirmation-required save step.",
            )
        )

    if persistence_smoke_without_cleanup_strategy:
        findings.append(
            Finding(
                id="persistence-smoke-without-cleanup-strategy",
                severity="warning",
                category="test-design",
                title="Persistence smoke TC lacks cleanup or isolation strategy",
                details="A persistence smoke TC leaves saved data behind unless postconditions describe cleanup, reset, deletion or isolated test data.",
                path=display_path,
                evidence=persistence_smoke_without_cleanup_strategy[:20],
                recommended_action="Add cleanup/isolation postconditions or state why no persistent cleanup is required.",
            )
        )

    if persistence_trace_not_exercised:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="persistence-trace-not-exercised",
                severity=severity,
                category="traceability",
                title="Persistence TC traces a requirement it does not exercise",
                details="A persistence smoke TC must not list a BSR as primary trace when the steps and rationale only use it as setup or do not exercise it at all.",
                path=display_path,
                evidence=persistence_trace_not_exercised[:20],
                recommended_action="Remove the BSR from primary trace, move it to supporting/setup notes, or add a TC that directly exercises it.",
            )
        )

    if persistence_precondition_passive_state:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="persistence-precondition-passive-state",
                severity=severity,
                category="test-design",
                title="Persistence TC uses passive state as a precondition",
                details="Persistence smoke preconditions must describe how to reach the setup state, not only state that the card/block/entity is already open or present.",
                path=display_path,
                evidence=persistence_precondition_passive_state[:20],
                recommended_action="Rewrite preconditions as action-oriented setup steps such as open the card, navigate to the block, add the entity and verify readiness.",
            )
        )

    if persistence_delete_tc_not_self_contained:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="persistence-delete-tc-not-self-contained",
                severity=severity,
                category="test-design",
                title="Persistence deletion TC is not self-contained",
                details="A deletion persistence TC that depends on an existing row/entity is not reproducible unless it creates the row itself or references a defined fixture.",
                path=display_path,
                evidence=persistence_delete_tc_not_self_contained[:20],
                recommended_action="Create and save the entity in setup, reopen and verify it exists, then perform the delete/save/reopen check; alternatively cite a defined fixture.",
            )
        )

    if rolling_date_boundary_unformalized_relative_value:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="rolling-date-boundary-unformalized-relative-value",
                severity=severity,
                category="test-data",
                title="Relative rolling date value is not formalized",
                details="Relative date data such as `D - 30 years` must define D, the output format and an example value so execution is reproducible.",
                path=display_path,
                evidence=rolling_date_boundary_unformalized_relative_value[:20],
                recommended_action="Define D, use an explicit format such as DD.MM.YYYY, include an example, and assert the calculated value rather than a raw placeholder string.",
            )
        )

    if persistence_grouped_smoke_without_residual_risk:
        findings.append(
            Finding(
                id="persistence-grouped-smoke-without-residual-risk",
                severity="warning",
                category="test-design",
                title="Grouped persistence smoke lacks residual risk",
                details="A grouped phone/e-mail persistence smoke may be acceptable, but the TC or matrix must state the grouping rationale and residual risk.",
                path=display_path,
                evidence=persistence_grouped_smoke_without_residual_risk[:20],
                recommended_action="Add explicit grouped-smoke rationale and residual risk, or split into atomic persistence TC.",
            )
        )

    if source_backed_ui_term_inconsistency:
        findings.append(
            Finding(
                id="source-backed-ui-term-inconsistency",
                severity="warning",
                category="traceability",
                title="Artifact mixes source-backed UI block terms",
                details="A scope should consistently use the source-backed UI block term unless a naming decision documents why another term is present.",
                path=display_path,
                evidence=source_backed_ui_term_inconsistency[:20],
                recommended_action="Normalize to the section source term or add a UI block naming decision that maps source and appendix terms.",
            )
        )

    if persistence_candidate_without_calibration_questions:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="persistence-candidate-without-calibration-questions",
                severity=severity,
                category="test-design",
                title="Candidate persistence TC lacks calibration handoff links",
                details="A candidate persistence TC must link BA/UI calibration questions or a calibration package so it cannot be mistaken for fully executable coverage.",
                path=display_path,
                evidence=persistence_candidate_without_calibration_questions[:20],
                recommended_action="Link the TC to BA/UI calibration question IDs or add the persistence save-flow calibration package.",
            )
        )

    if executable_persistence_with_unconfirmed_save_flow:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="executable-persistence-with-unconfirmed-save-flow",
                severity=severity,
                category="test-design",
                title="Executable persistence TC has unconfirmed save flow",
                details="Persistence TC must not be converted from candidate status while save action, save success oracle, exit/reopen and cleanup remain unconfirmed.",
                path=display_path,
                evidence=executable_persistence_with_unconfirmed_save_flow[:20],
                recommended_action="Restore `candidate-persistence-calibration` or add source-backed/BA-confirmed save-flow evidence before conversion.",
            )
        )

    if persistence_save_placeholder_in_executable_tc:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="persistence-save-placeholder-in-executable-tc",
                severity=severity,
                category="test-design",
                title="Executable persistence TC still uses save placeholder wording",
                details="Placeholder save wording is allowed only while the TC remains `candidate-persistence-calibration`.",
                path=display_path,
                evidence=persistence_save_placeholder_in_executable_tc[:20],
                recommended_action="Replace placeholder wording with the confirmed exact save action or restore candidate calibration status.",
            )
        )

    if persistence_terminology_source_mismatch:
        findings.append(
            Finding(
                id="persistence-terminology-source-mismatch",
                severity="warning",
                category="traceability",
                title="Persistence artifact mixes relation-field terminology",
                details="Artifacts must not mix `Отношение к клиенту` and `Отношение к заявителю` without an explicit source-backed terminology mapping.",
                path=display_path,
                evidence=persistence_terminology_source_mismatch[:20],
                recommended_action="Normalize to the source-backed term or add a terminology mapping with source evidence.",
            )
        )

    if persist_coverage_missing:
        findings.append(
            Finding(
                id="persist-coverage-missing-for-crud-scope",
                severity="warning",
                category="test-design",
                title="Editable card scope lacks save/persist coverage plan",
                details="CRUD/card scopes need explicit save/persist smoke coverage or a documented out-of-scope rationale.",
                path=display_path,
                evidence=persist_coverage_missing[:20],
                recommended_action="Add save/persist smoke TC or an explicit Save / persistence coverage plan.",
            )
        )

    if noncanonical_scenario_rationale_fields:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="scenario-rationale-noncanonical-field",
                severity=severity,
                category="atomarity",
                title="Scenario rationale uses non-canonical field label",
                details=(
                    "Production TC files must use the canonical Russian field `Сценарное обоснование`. "
                    "The English `Scenario rationale` label is treated as legacy/diagnostic notation only."
                ),
                path=display_path,
                evidence=noncanonical_scenario_rationale_fields[:20],
                recommended_action="Rename the field to `**Сценарное обоснование:**` and keep the rationale content intact if it is still valid.",
            )
        )

    if scenario_rationale_domain_mismatches:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="scenario-rationale-domain-mismatch",
                severity=severity,
                category="atomarity",
                title="Scenario rationale appears unrelated to the test case domain",
                details=(
                    "A scenario rationale must justify why this TC may group the source-backed checks it actually "
                    "executes. Rationale text that talks about another field family is likely copied from a different TC."
                ),
                path=display_path,
                evidence=scenario_rationale_domain_mismatches[:20],
                recommended_action="Rewrite the rationale so it names the tested field/block, source rows and separate TC/GAP coverage for independently failing checks.",
            )
        )

    if scenario_rationale_too_generic:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="scenario-rationale-too-generic",
                severity=severity,
                category="atomarity",
                title="Scenario rationale is too generic to justify grouping",
                details=(
                    "Generic phrases such as `one visible workflow` are not enough when they do not name the tested "
                    "target, source rows or why separate atomic coverage remains traceable."
                ),
                path=display_path,
                evidence=scenario_rationale_too_generic[:20],
                recommended_action="Replace generic wording with a target-specific grouping rationale tied to source-backed fields and residual atomic coverage.",
            )
        )

    if production_glued_headings:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="production-markdown-heading-not-at-line-start",
                severity=severity,
                category="structure",
                title="Production TC heading is glued to preceding text",
                details="A TC heading must begin at the start of its own line so extraction and review do not silently drop the case.",
                path=display_path,
                evidence=production_glued_headings[:20],
                recommended_action="Move every `## TC-*` heading to the start of a separate line.",
            )
        )

    if production_glued_metadata_fields:
        severity = atomicity_coverage_severity(atomicity_coverage_policy)
        findings.append(
            Finding(
                id="production-metadata-field-not-at-line-start",
                severity=severity,
                category="structure",
                title="Production TC metadata field is glued to preceding text",
                details="Runtime metadata fields must start at the beginning of a line to remain parseable and reviewable.",
                path=display_path,
                evidence=production_glued_metadata_fields[:20],
                recommended_action="Move every TC metadata field to the start of its own line.",
            )
        )

    has_smells = bool(
        generic_atoms
        or compressed_atoms
        or covered_range_atoms
        or combined_atoms
        or table_residue_atoms
        or generic_titles
        or process_marker_titles
        or generic_test_cases
        or value_type_list_selection_smells
        or dependency_placeholder_setup_smells
        or mockup_generic_ui_steps
        or positive_type_negative_oracle
        or negative_type_without_negative_oracle
        or generic_valid_fixture_placeholders
        or generic_test_data_references
        or generic_expected_results
        or generic_test_data_oracles
        or generic_rule_oracles
        or source_dump_oracles
        or value_type_metadata_as_behavior
        or extraction_artifact_oracles
        or requiredness_without_empty_or_marker
        or boundary_without_classes
        or boundary_rejection_without_acceptance
        or merged_valid_invalid_test_cases
        or numeric_only_valid_data_invalid
        or valid_data_class_label_mismatch
        or numeric_class_label_raw_literal_mismatch
        or unsupported_input_filtering_oracles
        or input_restriction_transition_oracles
        or unsupported_numeric_validation_feedback
        or mechanical_field_steps
        or negative_transition_without_valid_fixture
        or forbidden_formulations
        or abstract_oracles
        or negative_input_without_observable_oracle
        or date_dependent_absolute_dates
        or rolling_date_boundary_static_data
        or missing_representative_strategy
        or representative_strategy_without_omitted_combinations
        or representative_strategy_without_residual_risk
        or action_treated_as_required_field
        or action_without_observable_artifact
        or gap_placeholder_sections
        or nondeterministic_alternative_oracles
        or duplicated_source_reference_fields
        or dictionary_body_missing_traceability
        or synthetic_requirement_quotes
        or action_created_block_without_cleanup
        or branch_oracles_without_distinction
        or bundled_negative_input_classes
        or non_reproducible_preconditions
        or ambiguous_precondition_setup
        or broad_scenario_test_cases
        or excessive_atom_fan_in
        or overmerged_test_cases
        or tc_type_expected_result_mismatch
        or trace_not_exercised_by_steps
        or multiple_independent_assertions
        or representative_strategy_data_mismatches
        or production_internal_language_leaks
        or candidate_negative_trigger_missing
        or candidate_negative_trigger_too_specific
        or scenario_rationale_stimulus_mismatches
        or persist_coverage_missing
        or persistence_tc_without_save_action
        or persistence_tc_without_reopen_verification
        or persistence_tc_closes_without_saving
        or persistence_tc_unsourced_save_action
        or persistence_smoke_without_cleanup_strategy
        or persistence_trace_not_exercised
        or persistence_precondition_passive_state
        or persistence_delete_tc_not_self_contained
        or rolling_date_boundary_unformalized_relative_value
        or persistence_grouped_smoke_without_residual_risk
        or source_backed_ui_term_inconsistency
        or persistence_candidate_without_calibration_questions
        or executable_persistence_with_unconfirmed_save_flow
        or persistence_save_placeholder_in_executable_tc
        or persistence_terminology_source_mismatch
        or noncanonical_scenario_rationale_fields
        or scenario_rationale_domain_mismatches
        or scenario_rationale_too_generic
        or production_glued_headings
        or production_glued_metadata_fields
    )
    checks.append(
        Check(
            "test-case-quality-smells",
            "warn" if has_smells else "pass",
            "Generic atom/TC quality smells found." if has_smells else "No generic atom/TC quality smells found.",
            display_path,
        )
    )
    return findings, checks


def extract_test_case_blocks(content: str) -> list[tuple[str, str]]:
    matches = list(
        re.finditer(
            r"^(#{2,6})[^\S\r\n]+(TC-[A-Za-z0-9_-]+)(?:[^\S\r\n]+(?:[-—:][^\S\r\n]*)?.*)?$",
            content,
            flags=re.MULTILINE,
        )
    )
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        heading_level = len(match.group(1))
        body_start = match.end()
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        next_section_match = re.search(
            rf"^#{{2,{heading_level}}}[^\S\r\n]+(?!TC-[A-Za-z0-9_-]+(?:[^\S\r\n]+(?:[-—:][^\S\r\n]*)?.*)?$).+",
            content[body_start:],
            flags=re.MULTILINE,
        )
        if next_section_match:
            body_end = min(body_end, body_start + next_section_match.start())
        blocks.append((match.group(2), content[body_start:body_end]))
    return blocks


def noncanonical_test_case_heading_evidence(content: str) -> list[str]:
    evidence: list[str] = []
    for match in re.finditer(
        r"^(#{3,6})[^\S\r\n]+(TC-[A-Za-z0-9_-]+)(?:[^\S\r\n]+.*)?$",
        content,
        flags=re.MULTILINE,
    ):
        evidence.append(f"{match.group(2)}: heading_level={len(match.group(1))}, expected=2")
    return evidence


def has_test_case_bold_metadata_field(block: str, aliases: tuple[str, ...]) -> bool:
    names_pattern = "|".join(re.escape(alias) for alias in aliases)
    return re.search(rf"(?im)^\*\*(?:{names_pattern}):\*\*\s*\S", block) is not None


def has_test_case_runtime_section_or_field(block: str, aliases: tuple[str, ...]) -> bool:
    names_pattern = "|".join(re.escape(alias) for alias in aliases)
    pattern = re.compile(
        rf"(?im)^(?:###\s+(?:{names_pattern})\s*|\*\*(?:{names_pattern}):\*\*)\s*(.*)$"
    )
    for match in pattern.finditer(block):
        inline_value = match.group(1).strip()
        if inline_value:
            return True
        following = block[match.end() :]
        boundary = re.search(
            r"(?m)^(?:#{2,6}\s+|\*\*[^*\n:]+:\*\*|###\s+\S)",
            following,
        )
        section_body = following[: boundary.start()] if boundary else following
        if section_body.strip():
            return True
    return False


def is_runtime_complete_test_case(block: str) -> bool:
    metadata_complete = all(
        has_test_case_bold_metadata_field(block, aliases)
        for aliases in RUNTIME_METADATA_FIELD_ALIASES
    )
    sections_complete = all(
        has_test_case_runtime_section_or_field(block, aliases)
        for aliases in RUNTIME_SECTION_FIELD_ALIASES
    )
    has_numbered_step = re.search(r"(?m)^\d+\.\s+\S", block) is not None
    return metadata_complete and sections_complete and has_numbered_step


def test_case_numbering_issues(test_case_ids: list[str]) -> list[str]:
    parsed_numbers: list[tuple[str, int]] = []
    unnumbered: list[str] = []
    for test_case_id in test_case_ids:
        match = re.search(r"-(\d+)$", test_case_id)
        if match:
            parsed_numbers.append((test_case_id, int(match.group(1))))
        else:
            unnumbered.append(test_case_id)

    issues: list[str] = []
    if unnumbered:
        issues.append("missing_numeric_suffix:" + ", ".join(unnumbered[:10]))

    if len(parsed_numbers) != len(test_case_ids):
        return issues

    expected_numbers = list(range(1, len(parsed_numbers) + 1))
    actual_numbers = [number for _, number in parsed_numbers]
    if actual_numbers == expected_numbers:
        return issues

    missing = [number for number in expected_numbers if number not in actual_numbers]
    duplicate_numbers = [
        number
        for number, count in Counter(actual_numbers).items()
        if count > 1
    ]
    out_of_range = [
        number
        for number in actual_numbers
        if number < 1 or number > len(parsed_numbers)
    ]
    if missing:
        issues.append("missing_numbers:" + ", ".join(f"{number:03d}" for number in missing[:20]))
    if duplicate_numbers:
        issues.append("duplicate_numbers:" + ", ".join(f"{number:03d}" for number in sorted(duplicate_numbers)[:20]))
    if out_of_range:
        issues.append("out_of_range:" + ", ".join(f"{number:03d}" for number in sorted(out_of_range)[:20]))
    issues.append(
        "actual_order:"
        + ", ".join(f"{test_case_id}={number:03d}" for test_case_id, number in parsed_numbers[:20])
    )
    return issues


def validate_test_case_mixed_schema_duplicates(
    blocks: list[tuple[str, str]],
    path: Path,
    root: Path,
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)

    metadata_duplicate_evidence: list[str] = []
    runtime_duplicate_evidence: list[str] = []
    metadata_fields = ("Название", "Тип", "Приоритет", "Трассировка", "package_id")
    runtime_fields = ("Тестовые данные", "Шаги", "Итоговый ожидаемый результат")

    for test_case_id, block in blocks:
        has_metadata_table = re.search(
            r"(?im)^\|\s*(?:Поле|field)\s*\|\s*(?:Значение|value)\s*\|",
            block,
        ) is not None or re.search(
            r"(?im)^\|\s*(?:Название|Title|Тип|Type|Приоритет|Priority|Трассировка|Traceability|package_id)\s*\|",
            block,
        ) is not None
        if has_metadata_table:
            duplicated_fields = [
                field
                for field in metadata_fields
                if re.search(rf"(?im)^\*\*{re.escape(field)}:\*\*", block)
            ]
            if duplicated_fields:
                metadata_duplicate_evidence.append(
                    f"{test_case_id}:metadata table + bold fields={', '.join(duplicated_fields)}"
                )

        duplicated_runtime_fields = [
            field
            for field in runtime_fields
            if re.search(rf"(?im)^###\s+{re.escape(field)}\s*$", block)
            and re.search(rf"(?im)^\*\*{re.escape(field)}:\*\*", block)
        ]
        if duplicated_runtime_fields:
            runtime_duplicate_evidence.append(
                f"{test_case_id}:section + bold fields={', '.join(duplicated_runtime_fields)}"
            )

    if metadata_duplicate_evidence:
        findings.append(
            Finding(
                id="test-case-mixed-schema-duplicate-fields",
                severity="warning",
                category="test-case-format",
                title="Test case mixes metadata table and bold metadata fields",
                details=(
                    "A TC-* block must use one canonical field representation. Metadata table rows and "
                    "duplicated `**field:**` lines make the manual case noisy and create two values to maintain."
                ),
                path=display_path,
                evidence=metadata_duplicate_evidence[:20],
                recommended_action=(
                    "Keep one format for TC metadata. Prefer the canonical `**Название:**`, `**Тип:**`, "
                    "`**Приоритет:**`, `**Трассировка:**`, `**package_id:**` fields and remove the duplicate table."
                ),
            )
        )
    if runtime_duplicate_evidence:
        findings.append(
            Finding(
                id="test-case-runtime-field-duplicated",
                severity="warning",
                category="test-case-format",
                title="Test case duplicates runtime sections as bold inline fields",
                details=(
                    "A TC-* block must not contain both a runtime section heading and a duplicated inline field "
                    "for the same data, steps or expected result."
                ),
                path=display_path,
                evidence=runtime_duplicate_evidence[:20],
                recommended_action=(
                    "Keep `### Тестовые данные`, `### Шаги`, and `### Итоговый ожидаемый результат` sections "
                    "or the inline field style, but not both in the same TC-*."
                ),
            )
        )

    has_duplicates = bool(metadata_duplicate_evidence or runtime_duplicate_evidence)
    checks.append(
        Check(
            "test-case-mixed-schema",
            "warn" if has_duplicates else "pass",
            "Test cases duplicate runtime/metadata fields." if has_duplicates else "No mixed TC schema duplicates found.",
            display_path,
        )
    )
    return findings, checks


def validate_test_case_file(
    path: Path,
    root: Path,
    *,
    test_case_policy: str = "compatible",
    input_restriction_gap_policy: str = "compatible",
    rolling_date_boundary_policy: str = "compatible",
    atomicity_coverage_policy: str = "compatible",
    known_test_case_ids: set[str] | None = None,
    suppress_blocked_input_gate_failures: bool = False,
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    structural_severity = "warning" if test_case_policy == "strict" else "info"

    try:
        raw_file_bytes = path.read_bytes()
        raw_content = raw_file_bytes.decode("utf-8")
        content = test_case_validation_content(path, root)
    except UnicodeDecodeError as exc:
        findings.append(
            Finding(
                id="test-case-file-not-utf8",
                severity="error",
                category="test-case-format",
                title="Test-case file is not UTF-8",
                details=str(exc),
                path=display_path,
                evidence=[],
                recommended_action="Save the canonical test-case file as UTF-8 Markdown.",
            )
        )
        checks.append(Check("test-case-format", "fail", "Test-case file is not UTF-8.", display_path))
        return findings, checks

    for section_title, artifact_path in split_test_design_artifact_paths(path).items():
        artifact_findings, artifact_checks = validate_split_artifact_heading_shape(
            section_title,
            artifact_path,
            root,
        )
        findings.extend(artifact_findings)
        checks.extend(artifact_checks)

    duplicated_split_sections = duplicate_split_sections_in_test_case(raw_content, path)
    if duplicated_split_sections:
        findings.append(
            Finding(
                id="test-case-split-artifact-duplicated-sections",
                severity="warning",
                category="test-case-format",
                title="Test-case file duplicates canonical split artifact tables",
                details=(
                    "When `work/test-design/<scope>/` contains canonical table artifacts, the canonical test-case "
                    "file should keep only links and summaries. Keeping full table copies in both places creates "
                    "two sources of truth."
                ),
                path=display_path,
                evidence=duplicated_split_sections[:20],
                recommended_action=(
                    "Remove the duplicated table sections from the test-case file and keep the canonical tables in "
                    "`work/test-design/<scope>/`."
                ),
            )
        )

    placeholder_findings, placeholder_checks = validate_traceability_placeholder_sentinels(content, path, root)
    findings.extend(placeholder_findings)
    checks.extend(placeholder_checks)

    gap_inventory_findings, gap_inventory_checks = validate_coverage_gap_inventory(
        content,
        path,
        root,
        input_restriction_gap_policy=input_restriction_gap_policy,
    )
    findings.extend(gap_inventory_findings)
    checks.extend(gap_inventory_checks)

    matrix_findings, matrix_checks = validate_test_design_applicability_matrix(
        content,
        path,
        root,
        structural_severity=structural_severity,
        known_test_case_ids=known_test_case_ids,
    )
    findings.extend(matrix_findings)
    checks.extend(matrix_checks)

    dependency_findings, dependency_checks = validate_dependency_matrix_support(
        content,
        path,
        root,
        structural_severity=structural_severity,
        known_test_case_ids=known_test_case_ids,
    )
    findings.extend(dependency_findings)
    checks.extend(dependency_checks)

    pairwise_findings, pairwise_checks = validate_pairwise_supporting_table(content, path, root)
    findings.extend(pairwise_findings)
    checks.extend(pairwise_checks)

    blocks = extract_test_case_blocks(content)
    if not blocks:
        if is_production_test_case_path(path):
            production_glued_headings, production_glued_metadata_fields = production_line_structure_evidence(raw_content)
            if production_glued_headings:
                findings.append(
                    Finding(
                        id="production-markdown-heading-not-at-line-start",
                        severity=atomicity_coverage_severity(atomicity_coverage_policy),
                        category="structure",
                        title="Production TC heading is glued to preceding text",
                        details="A TC heading must begin at the start of its own line so extraction and review do not silently drop the case.",
                        path=display_path,
                        evidence=production_glued_headings[:20],
                        recommended_action="Move every `## TC-*` heading to the start of a separate line.",
                    )
                )
            if production_glued_metadata_fields:
                findings.append(
                    Finding(
                        id="production-metadata-field-not-at-line-start",
                        severity=atomicity_coverage_severity(atomicity_coverage_policy),
                        category="structure",
                        title="Production TC metadata field is glued to preceding text",
                        details="Runtime metadata fields must start at the beginning of a line to remain parseable and reviewable.",
                        path=display_path,
                        evidence=production_glued_metadata_fields[:20],
                        recommended_action="Move every TC metadata field to the start of its own line.",
                    )
                )
        findings.append(
            Finding(
                id="test-case-file-no-structured-cases",
                severity=structural_severity,
                category="test-case-format",
                title="Test-case file has no structured TC-* cases",
                details="Canonical test-case files should contain one ## TC-* section per test case.",
                path=display_path,
                evidence=[],
                recommended_action="When this artifact is next updated, rewrite test cases as canonical ## TC-* sections.",
            )
        )
        checks.append(
            Check(
                "test-case-format",
                "warn" if structural_severity == "warning" else "pass",
                "No structured test cases found." if structural_severity == "info" else "Test-case format contract has issues.",
                display_path,
            )
        )
        return findings, checks

    noncanonical_heading_evidence = noncanonical_test_case_heading_evidence(content)
    if noncanonical_heading_evidence:
        findings.append(
            Finding(
                id="test-case-noncanonical-heading-level",
                severity="warning",
                category="test-case-format",
                title="Test-case sections use noncanonical heading levels",
                details="Canonical test-case files must use one top-level `## TC-*` section per test case.",
                path=display_path,
                evidence=noncanonical_heading_evidence[:20],
                recommended_action="Promote each `TC-*` heading to `## TC-*`; keep runtime fields under the TC as bold fields or allowed subsections.",
            )
        )

    if test_case_policy == "strict":
        template_findings, template_checks = validate_required_test_case_template_sections(
            blocks,
            path,
            root,
            structural_severity=structural_severity,
        )
        findings.extend(template_findings)
        checks.extend(template_checks)

    mixed_schema_findings, mixed_schema_checks = validate_test_case_mixed_schema_duplicates(
        blocks,
        path,
        root,
    )
    findings.extend(mixed_schema_findings)
    checks.extend(mixed_schema_checks)

    calibration_findings, calibration_checks = validate_ui_calibration_candidate_test_cases(
        blocks,
        path,
        root,
    )
    findings.extend(calibration_findings)
    checks.extend(calibration_checks)

    calculation_findings, calculation_checks = validate_calculation_oracles(content, path, root, blocks)
    findings.extend(calculation_findings)
    checks.extend(calculation_checks)

    risk_findings, risk_checks = validate_risk_priority_map(content, path, root, blocks)
    findings.extend(risk_findings)
    checks.extend(risk_checks)

    normalization_findings, normalization_checks = validate_source_table_normalization(content, path, root)
    findings.extend(normalization_findings)
    checks.extend(normalization_checks)

    inventory_findings, inventory_checks = validate_source_row_inventory(content, path, root)
    findings.extend(inventory_findings)
    checks.extend(inventory_checks)

    decision_findings, decision_checks = validate_test_design_decision_table(
        content,
        path,
        root,
        known_test_case_ids=known_test_case_ids,
    )
    findings.extend(decision_findings)
    checks.extend(decision_checks)

    obligation_findings, obligation_checks = validate_coverage_obligation_table(
        content,
        path,
        root,
        known_test_case_ids=known_test_case_ids,
    )
    findings.extend(obligation_findings)
    checks.extend(obligation_checks)

    ledger_findings, ledger_checks = validate_atomic_ledger_structure(
        content,
        path,
        root,
        structural_severity=structural_severity,
        blocks=blocks,
        known_test_case_ids=known_test_case_ids,
    )
    findings.extend(ledger_findings)
    checks.extend(ledger_checks)

    package_findings, package_checks = validate_test_case_package_ids(
        content,
        path,
        root,
        structural_severity=structural_severity,
        blocks=blocks,
    )
    findings.extend(package_findings)
    checks.extend(package_checks)

    design_plan_findings, design_plan_checks = validate_package_test_design_plan(
        content,
        path,
        root,
        structural_severity=structural_severity,
        known_test_case_ids=known_test_case_ids,
    )
    findings.extend(design_plan_findings)
    checks.extend(design_plan_checks)

    design_review_findings, design_review_checks = validate_test_design_review(
        content,
        path,
        root,
        suppress_blocked_input_failures=suppress_blocked_input_gate_failures,
    )
    findings.extend(design_review_findings)
    checks.extend(design_review_checks)

    writer_gate_findings, writer_gate_checks = validate_writer_quality_gate(
        content,
        path,
        root,
        suppress_blocked_input_failures=suppress_blocked_input_gate_failures,
    )
    findings.extend(writer_gate_findings)
    checks.extend(writer_gate_checks)

    self_check_findings, self_check_checks = validate_writer_self_check_sections(content, path, root)
    findings.extend(self_check_findings)
    checks.extend(self_check_checks)

    write_strategy_findings, write_strategy_checks = validate_artifact_write_strategy(
        content,
        path,
        root,
        blocks=blocks,
        structural_severity=structural_severity,
    )
    findings.extend(write_strategy_findings)
    checks.extend(write_strategy_checks)

    smell_findings, smell_checks = validate_test_case_quality_smells(
        content,
        path,
        root,
        blocks=blocks,
        rolling_date_boundary_policy=rolling_date_boundary_policy,
        atomicity_coverage_policy=atomicity_coverage_policy,
        physical_content=raw_content,
    )
    findings.extend(smell_findings)
    checks.extend(smell_checks)

    test_case_ids = [test_case_id for test_case_id, _ in blocks]
    duplicate_ids = [
        test_case_id
        for test_case_id, count in Counter(test_case_ids).items()
        if count > 1
    ]
    if duplicate_ids:
        findings.append(
            Finding(
                id="test-case-duplicate-id",
                severity="warning",
                category="test-case-format",
                title="Test-case file contains duplicate TC ids",
                details="Each test case id should identify one manual test case.",
                path=display_path,
                evidence=duplicate_ids[:20],
                recommended_action="Rename duplicate test cases and update traceability references.",
            )
        )

    numbering_issues = test_case_numbering_issues(test_case_ids)
    if numbering_issues:
        findings.append(
            Finding(
                id="test-case-nonsequential-id-numbering",
                severity=structural_severity,
                category="test-case-format",
                title="Test-case file does not use continuous TC numbering",
                details=(
                    "TC numeric suffixes should be continuous in file order; numbering must not restart "
                    "inside functional groups."
                ),
                path=display_path,
                evidence=numbering_issues[:20],
                recommended_action=(
                    "Renumber TC-* sections sequentially across the canonical file and update traceability, "
                    "coverage-map, matrix, and writer-response references."
                ),
            )
        )

    sparse_fields: list[str] = []
    missing_steps: list[str] = []
    missing_traceability: list[str] = []
    for test_case_id, block in blocks:
        field_count = len(re.findall(r"^\*\*[^*\n:]+:\*\*", block, flags=re.MULTILINE))
        if field_count < MIN_TEST_CASE_FIELD_COUNT and not is_runtime_complete_test_case(block):
            sparse_fields.append(f"{test_case_id}:fields={field_count}")
        if not re.search(r"(?m)^\d+\.\s+\S", block):
            missing_steps.append(test_case_id)
        if not TEST_CASE_TRACEABILITY_TOKEN_RE.search(block):
            missing_traceability.append(test_case_id)

    if sparse_fields:
        findings.append(
            Finding(
                id="test-case-sparse-required-fields",
                severity=structural_severity,
                category="test-case-format",
                title="Some test cases have too few structured fields",
                details="Canonical test cases should expose the main fields from test-case-format.md.",
                path=display_path,
                evidence=sparse_fields[:20],
                recommended_action="Add the missing canonical fields such as title, priority, type, goal, steps, expected result, and source references.",
            )
        )
    if missing_steps:
        findings.append(
            Finding(
                id="test-case-missing-numbered-steps",
                severity=structural_severity,
                category="test-case-format",
                title="Some test cases have no numbered steps",
                details="Manual test cases need reproducible numbered steps.",
                path=display_path,
                evidence=missing_steps[:20],
                recommended_action="Add deterministic numbered steps to each test case.",
            )
        )
    if missing_traceability:
        findings.append(
            Finding(
                id="test-case-missing-traceability-token",
                severity=structural_severity,
                category="test-case-format",
                title="Some test cases lack an obvious requirement traceability token",
                details="Each test case should reference an ATOM-*, BSR/GSR/REQ, PDF page, or another explicit source locator.",
                path=display_path,
                evidence=missing_traceability[:20],
                recommended_action="Add concrete FT/source references to the affected test cases.",
            )
        )

    has_warning = any(finding.severity == "warning" for finding in findings)
    checks.append(
        Check(
            "test-case-format",
            "warn" if has_warning else "pass",
            "Test-case format contract has issues." if has_warning else "Test-case format contract passed.",
            display_path,
        )
    )
    return findings, checks


def simple_markdown_scalar_field(content: str, field: str) -> str:
    match = re.search(
        rf"(?im)^\s*(?:[-*]\s*)?{re.escape(field)}\s*:\s*`?([^`\n]+?)`?\s*$",
        content,
    )
    if not match:
        return ""
    return match.group(1).strip().strip("`").strip().lower()


def writer_process_diagnostic_status(path: Path) -> dict[str, Any]:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return {
            "readable": False,
            "fields": {},
            "is_failed": True,
            "is_contaminated": True,
            "validator_gap_suspected": False,
            "blocking": True,
        }

    fields = {
        field: simple_markdown_scalar_field(content, field)
        for field in WRITER_PROCESS_DIAGNOSTIC_REQUIRED_FIELDS
    }
    active_raw = fields.get("active_for_current_workflow", "")
    is_active = active_raw not in WRITER_PROCESS_DIAGNOSTIC_NO_VALUES
    active_known = active_raw in WRITER_PROCESS_DIAGNOSTIC_YES_VALUES | WRITER_PROCESS_DIAGNOSTIC_NO_VALUES
    is_failed = fields.get("verdict", "") in WRITER_PROCESS_DIAGNOSTIC_FAIL_VALUES
    is_contaminated = fields.get("process_readiness", "") in WRITER_PROCESS_DIAGNOSTIC_CONTAMINATED_VALUES
    validator_gap_suspected = fields.get("validator_gap_suspected", "") in WRITER_PROCESS_DIAGNOSTIC_YES_VALUES
    return {
        "readable": True,
        "fields": fields,
        "is_active": is_active,
        "active_known": active_known,
        "is_failed": is_failed,
        "is_contaminated": is_contaminated,
        "validator_gap_suspected": validator_gap_suspected,
        "blocking": is_active and (is_failed or is_contaminated or validator_gap_suspected),
    }


def validate_writer_process_diagnostic(path: Path, root: Path) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        findings.append(
            Finding(
                id="writer-process-diagnostic-not-utf8",
                severity="error",
                category="session-log",
                title="Writer process diagnostic is not UTF-8",
                details=str(exc),
                path=display_path,
                evidence=[],
                recommended_action="Save writer-process-diagnostic.md as UTF-8 Markdown.",
            )
        )
        checks.append(Check("writer-process-diagnostic", "fail", "Writer process diagnostic is not UTF-8.", display_path))
        return findings, checks

    fields = {
        field: simple_markdown_scalar_field(content, field)
        for field in WRITER_PROCESS_DIAGNOSTIC_REQUIRED_FIELDS
    }
    missing_fields = sorted(field for field, value in fields.items() if not value)
    if missing_fields:
        findings.append(
            Finding(
                id="writer-process-diagnostic-missing-required-fields",
                severity="warning",
                category="session-log",
                title="Writer process diagnostic misses required fields",
                details=(
                    "A writer-process-diagnostic.md artifact must expose verdict, process_readiness and "
                    "validator_gap_suspected plus diagnostic_scope, diagnostic_target and "
                    "active_for_current_workflow so workflow-state validation can distinguish active clean-rerun "
                    "diagnostics from historical failed evidence."
                ),
                path=display_path,
                evidence=missing_fields,
                recommended_action=(
                    "Add top-level fields `diagnostic_scope`, `diagnostic_target`, `active_for_current_workflow`, "
                    "`verdict`, `process_readiness` and `validator_gap_suspected` with canonical values."
                ),
            )
        )
        checks.append(Check("writer-process-diagnostic", "warn", "Writer process diagnostic fields are incomplete.", display_path))
        return findings, checks

    invalid_values: list[str] = []
    if fields["verdict"] not in {"pass", "fail", "failed"}:
        invalid_values.append(f"verdict={fields['verdict']}")
    if fields["process_readiness"] not in {"clean", "contaminated", "technical-contaminated", "not-clean", "dirty"}:
        invalid_values.append(f"process_readiness={fields['process_readiness']}")
    if fields["validator_gap_suspected"] not in {"yes", "no", "true", "false"}:
        invalid_values.append(f"validator_gap_suspected={fields['validator_gap_suspected']}")
    if fields["active_for_current_workflow"] not in {"yes", "no", "true", "false"}:
        invalid_values.append(f"active_for_current_workflow={fields['active_for_current_workflow']}")
    if invalid_values:
        findings.append(
            Finding(
                id="writer-process-diagnostic-invalid-field-values",
                severity="warning",
                category="session-log",
                title="Writer process diagnostic has invalid field values",
                details="Use canonical values so the validator can reason about writer process readiness.",
                path=display_path,
                evidence=invalid_values,
                recommended_action=(
                    "Use `verdict: pass|fail`, `process_readiness: clean|contaminated`, and "
                    "`validator_gap_suspected: yes|no`."
                ),
            )
        )
        checks.append(Check("writer-process-diagnostic", "warn", "Writer process diagnostic has invalid fields.", display_path))
        return findings, checks

    checks.append(
        Check(
            "writer-process-diagnostic",
            "pass",
            "Writer process diagnostic format passed.",
            display_path,
        )
    )
    return findings, checks


def resolve_workflow_writer_process_diagnostics(
    state: dict[str, Any],
    workflow_path: Path,
    root: Path,
    ft_root: Path,
) -> list[Path]:
    paths: list[Path] = []
    for value in [
        *flatten_string_values(state.get("required_inputs")),
        *flatten_string_values(state.get("latest_artifacts")),
    ]:
        candidate_name = Path(strip_quotes(value)).name
        if not (candidate_name.startswith("writer-process-diagnostic") and candidate_name.endswith(".md")):
            continue
        resolved = resolve_artifact_path(value, workflow_path, root, ft_root)
        if resolved is not None:
            paths.append(resolved)

    paths.extend(sorted(workflow_path.parent.glob("writer-process-diagnostic*.md")))

    return dedupe_paths(paths)


def diagnostic_target_matches_test_case_artifacts(
    target: str,
    *,
    test_case_artifacts: list[Path],
    workflow_path: Path,
    root: Path,
    ft_root: Path,
) -> bool:
    normalized_target = strip_quotes(target).strip("`").replace("\\", "/")
    if not normalized_target:
        return False

    target_path = resolve_artifact_path(normalized_target, workflow_path, root, ft_root)
    if target_path is not None:
        try:
            resolved_target = target_path.resolve()
            return any(test_case_artifact.resolve() == resolved_target for test_case_artifact in test_case_artifacts)
        except OSError:
            return any(test_case_artifact == target_path for test_case_artifact in test_case_artifacts)

    for test_case_artifact in test_case_artifacts:
        artifact_candidates = {
            test_case_artifact.name,
            test_case_artifact.as_posix(),
        }
        try:
            artifact_candidates.add(test_case_artifact.relative_to(ft_root).as_posix())
        except ValueError:
            pass
        try:
            artifact_candidates.add(test_case_artifact.relative_to(root.parent if root.is_file() else root).as_posix())
        except ValueError:
            pass
        if normalized_target in artifact_candidates:
            return True
    return False


def validate_dictionary_inventory(path: Path, root: Path) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    content = path.read_text(encoding="utf-8")
    section = extract_markdown_section(content, "Dictionary Inventory") or content
    rows = markdown_table_rows_from_text(section)

    if not rows:
        findings.append(
            Finding(
                id="dictionary-inventory-no-table",
                severity="warning",
                category="test-design",
                title="Dictionary Inventory has no Markdown table",
                details="dictionary-inventory.md must expose referenced dictionaries in a canonical Markdown table.",
                path=display_path,
                evidence=[],
                recommended_action="Add the canonical table from dictionary-inventory-format.md.",
            )
        )
        checks.append(Check("dictionary-inventory", "warn", "Dictionary Inventory table is missing.", display_path))
        return findings, checks

    header = normalize_table_header(rows[0])
    missing_columns = sorted(DICTIONARY_INVENTORY_REQUIRED_COLUMNS - set(header))
    if missing_columns:
        findings.append(
            Finding(
                id="dictionary-inventory-missing-columns",
                severity="warning",
                category="test-design",
                title="Dictionary Inventory misses required columns",
                details="Dictionary Inventory must include source locator, extraction status, active/archived values and source-property links.",
                path=display_path,
                evidence=[f"missing={', '.join(missing_columns)}", f"columns={', '.join(header[:12])}"],
                recommended_action="Rewrite the table with the canonical columns from dictionary-inventory-format.md.",
            )
        )

    invalid_rows: list[str] = []
    extracted_without_values: list[str] = []
    incomplete_without_gap: list[str] = []
    missing_source_property_links: list[str] = []

    for index, raw_row in enumerate(rows[1:], start=2):
        row = {
            column_name: raw_row[column_index].strip().strip("`") if column_index < len(raw_row) else ""
            for column_index, column_name in enumerate(header)
        }
        dictionary_id = row.get("dictionary_id", "").strip()
        status = normalize_markdown_field_value(row.get("extraction_status", "")).lower()
        active_values = normalize_markdown_field_value(row.get("active_values", ""))
        used_by = normalize_markdown_field_value(row.get("used_by_source_properties", ""))
        gap_id = row.get("gap_id", "").strip()

        if not re.fullmatch(r"DICT-\d{3,}", dictionary_id):
            invalid_rows.append(f"row {index}:dictionary_id={dictionary_id or '-'}")
        if status not in DICTIONARY_INVENTORY_ALLOWED_STATUSES:
            invalid_rows.append(f"row {index}:extraction_status={status or '-'}")
        if status in DICTIONARY_INVENTORY_EXTRACTED_STATUSES and active_values in {"", "-"}:
            extracted_without_values.append(f"{dictionary_id or f'row {index}'}:active_values={active_values or '-'}")
        if status in DICTIONARY_INVENTORY_INCOMPLETE_STATUSES and not real_gap_ids(gap_id):
            incomplete_without_gap.append(f"{dictionary_id or f'row {index}'}:status={status};gap_id={gap_id or '-'}")
        if used_by in {"", "-"}:
            missing_source_property_links.append(f"{dictionary_id or f'row {index}'}:used_by_source_properties={used_by or '-'}")

    if invalid_rows:
        findings.append(
            Finding(
                id="dictionary-inventory-invalid-row",
                severity="warning",
                category="test-design",
                title="Dictionary Inventory has invalid ids or statuses",
                details="dictionary_id must be DICT-* and extraction_status must use canonical values.",
                path=display_path,
                evidence=invalid_rows[:20],
                recommended_action="Use DICT-001-style ids and extraction_status = extracted | partial | missing | ambiguous | not-needed.",
            )
        )
    if extracted_without_values:
        findings.append(
            Finding(
                id="dictionary-inventory-extracted-without-active-values",
                severity="warning",
                category="test-design",
                title="Extracted dictionaries have no active values",
                details="When extraction_status = extracted, active_values must list the extracted active values or point to a DICT-* values section.",
                path=display_path,
                evidence=extracted_without_values[:20],
                recommended_action="Fill active_values from the source/support dictionary, or change status and add a GAP-* if extraction is blocked.",
            )
        )
    if incomplete_without_gap:
        findings.append(
            Finding(
                id="dictionary-inventory-incomplete-without-gap",
                severity="warning",
                category="test-design",
                title="Incomplete dictionary extraction has no GAP link",
                details="Partial, missing or ambiguous dictionary extraction must be traceable to a GAP-*.",
                path=display_path,
                evidence=incomplete_without_gap[:20],
                recommended_action="Add a narrow GAP-* for the blocked dictionary extraction or complete the inventory.",
            )
        )
    if missing_source_property_links:
        findings.append(
            Finding(
                id="dictionary-inventory-missing-source-property-link",
                severity="warning",
                category="traceability",
                title="Dictionary Inventory rows are not linked to source_property_id",
                details="Every dictionary row must show which normalized source properties use it.",
                path=display_path,
                evidence=missing_source_property_links[:20],
                recommended_action="Fill used_by_source_properties with source_property_id values from Source Table Normalization.",
            )
        )

    has_findings = any(finding.id.startswith("dictionary-inventory") for finding in findings)
    checks.append(
        Check(
            "dictionary-inventory",
            "warn" if has_findings else "pass",
            "Dictionary Inventory has issues." if has_findings else "Dictionary Inventory contract passed.",
            display_path,
        )
    )
    return findings, checks


def validate_mockup_visual_inventory(path: Path, root: Path) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        findings.append(
            Finding(
                id="mockup-visual-inventory-not-utf8",
                severity="error",
                category="mockup",
                title="Mockup visual inventory is not UTF-8",
                details=str(exc),
                path=display_path,
                evidence=[],
                recommended_action="Save mockup-visual-inventory.md as UTF-8 Markdown.",
            )
        )
        checks.append(Check("mockup-visual-inventory", "fail", "Mockup visual inventory is not UTF-8.", display_path))
        return findings, checks

    normalized = content.lower()
    missing_terms = sorted(
        term
        for term in MOCKUP_VISUAL_INVENTORY_REQUIRED_TERMS
        if term.lower() not in normalized
    )
    if missing_terms:
        findings.append(
            Finding(
                id="mockup-visual-inventory-missing-required-items",
                severity="warning",
                category="mockup",
                title="Mockup visual inventory misses required items",
                details=(
                    "UI-scope mockup inventory must prove that the mockup was opened and record visible blocks, "
                    "fields, actions, interaction hints, mockup-only items, FT conflicts and usage decisions."
                ),
                path=display_path,
                evidence=missing_terms[:20],
                recommended_action="Rewrite the inventory using references/agent/mockup-visual-inventory-format.md.",
            )
        )

    opened_no = re.search(
        r"(?im)^\|\s*opened\s*\|\s*`?(?:no|false|blocked|not[-\s]?opened)",
        content,
    )
    if opened_no:
        findings.append(
            Finding(
                id="mockup-visual-inventory-not-opened",
                severity="warning",
                category="mockup",
                title="Mockup visual inventory says the mockup was not opened",
                details=(
                    "For UI scopes with a mockup, the inventory must be based on an opened/viewed image. "
                    "If the mockup cannot be opened, keep the workflow blocked instead of producing UI steps."
                ),
                path=display_path,
                evidence=[opened_no.group(0).strip()],
                recommended_action="Open the mockup visually and update the inventory, or set workflow-state to blocked-input.",
            )
        )

    no_requirement_guard = re.search(
        r"(?im)^\|\s*not_used_as_requirement_source\s*\|\s*`?(?:no|false)",
        content,
    ) or re.search(
        (
            r"(?im)^\|\s*used_for_steps\s*\|\s*not_used_as_requirement_source\s*\|[^\n]*\n"
            r"^\|[-:\s|]+\|\s*\n"
            r"^\|\s*`?[^|`]+`?\s*\|\s*`?(?:no|false)"
        ),
        content,
    )
    if no_requirement_guard:
        findings.append(
            Finding(
                id="mockup-visual-inventory-missing-requirement-source-guard",
                severity="warning",
                category="mockup",
                title="Mockup inventory does not guard against mockup-derived requirements",
                details=(
                    "The mockup may refine UI interaction steps, but it must not replace FT text as the source "
                    "for business rules, validations, allowed values or expected results."
                ),
                path=display_path,
                evidence=[no_requirement_guard.group(0).strip()],
                recommended_action="Set not_used_as_requirement_source to yes and document mockup-only items as gaps/conflicts.",
            )
        )

    has_findings = any(finding.id.startswith("mockup-visual-inventory") for finding in findings)
    checks.append(
        Check(
            "mockup-visual-inventory",
            "warn" if has_findings else "pass",
            "Mockup visual inventory has issues." if has_findings else "Mockup visual inventory contract passed.",
            display_path,
        )
    )
    return findings, checks


def ready_for_review_blocking_test_case_findings(
    path: Path,
    root: Path,
) -> list[Finding]:
    findings, _ = validate_test_case_file(path, root, test_case_policy="strict")
    return [
        finding
        for finding in findings
        if finding.id in READY_FOR_REVIEW_BLOCKING_TEST_CASE_FINDING_IDS
    ]


def validate_session_log(
    path: Path,
    root: Path,
    *,
    session_log_policy: str = "compatible",
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    strict_like = session_log_policy in {"strict", "audit"}
    severity = "warning" if strict_like else "info"
    warn_status = "warn" if strict_like else "pass"

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        findings.append(
            Finding(
                id="session-log-not-utf8",
                severity="error",
                category="session-log",
                title="Session log is not UTF-8",
                details=str(exc),
                path=display_path,
                evidence=[],
                recommended_action="Save the session log as UTF-8 Markdown.",
            )
        )
        checks.append(Check("session-log-format", "fail", "Session log is not UTF-8.", display_path))
        return findings, checks

    required_sections = set(SESSION_LOG_REQUIRED_SECTIONS)
    if session_log_policy == "audit":
        required_sections.update(SESSION_LOG_AUDIT_SECTIONS)

    missing_sections = sorted(
        section
        for section in required_sections
        if extract_markdown_section(content, section) is None
    )
    if missing_sections:
        findings.append(
            Finding(
                id="session-log-missing-required-sections",
                severity=severity,
                category="session-log",
                title="Session log misses required audit sections",
                details=(
                    "A stage session log should capture inputs read, inputs intentionally not used, key decisions, "
                    "risks/fallbacks, validation and contamination check."
                ),
                path=display_path,
                evidence=missing_sections,
                recommended_action="Rewrite the session log using references/agent/session-log-format.md.",
            )
        )
        checks.append(Check("session-log-format", warn_status, "Session log misses required sections.", display_path))
        return findings, checks

    weak_sections: list[str] = []
    for section in required_sections - {"Session Metadata"}:
        section_body = extract_markdown_section(content, section) or ""
        meaningful_lines = [
            line.strip()
            for line in section_body.splitlines()
            if line.strip() and not re.fullmatch(r"[-|:`\s]+", line.strip())
        ]
        if not meaningful_lines:
            weak_sections.append(section)
    if weak_sections:
        findings.append(
            Finding(
                id="session-log-empty-required-sections",
                severity=severity,
                category="session-log",
                title="Session log has empty required audit sections",
                details="Required sections should contain explicit audit entries, not only headings.",
                path=display_path,
                evidence=weak_sections,
                recommended_action="Add concise entries or `none` with rationale for each empty section.",
            )
        )
        checks.append(Check("session-log-format", warn_status, "Session log has empty required sections.", display_path))
    else:
        checks.append(Check("session-log-format", "pass", "Session log format passed.", display_path))

    if session_log_policy == "audit":
        strategy_hint_sources = "\n".join(
            extract_markdown_section(content, section) or ""
            for section in (
                "Event Timeline",
                "Key Decisions",
                "Risks And Fallbacks",
                "Quality Checkpoints",
                "Validation",
                "Handoff Notes For Next Session",
            )
        )
        strategy_hints = sorted(
            {
                match.group(0).strip()
                for match in SESSION_LOG_ARTIFACT_WRITE_STRATEGY_HINT_RE.finditer(strategy_hint_sources)
            }
        )
        strategy_section = extract_markdown_section(content, "Artifact Write Strategy") or ""
        if strategy_hints and not strategy_section:
            findings.append(
                Finding(
                    id="session-log-artifact-write-strategy-missing",
                    severity=severity,
                    category="session-log",
                    title="Session log does not declare Artifact Write Strategy before generated artifact writes",
                    details=(
                        "Audit logs that create large/table-heavy/generated artifacts must declare the write strategy "
                        "before the first write. This prevents an initial one-shot PowerShell/here-string attempt from "
                        "becoming a hidden technical fallback."
                    ),
                    path=display_path,
                    evidence=strategy_hints[:10],
                    recommended_action=(
                        "Add `## Artifact Write Strategy` with artifact_path, artifact_size_class, write_strategy, "
                        "declared_before_first_write, helper and forbidden_methods_checked. For large artifacts use "
                        "`scripts/write_artifact_sections.py` from the start."
                    ),
                )
            )
            checks.append(
                Check(
                    "session-log-artifact-write-strategy",
                    warn_status,
                    "Artifact Write Strategy is missing from audit session log.",
                    display_path,
                )
            )
        elif strategy_section:
            strategy_rows = markdown_table_rows_from_text(strategy_section)
            strategy_has_valid_shape = False
            non_preflight_rows: list[str] = []
            missing_helper_rows: list[str] = []
            unsafe_strategy_rows: list[str] = []
            if strategy_rows:
                header = normalize_table_header(strategy_rows[0])
                missing_columns = sorted(SESSION_LOG_ARTIFACT_WRITE_STRATEGY_REQUIRED_COLUMNS - set(header))
                if not missing_columns:
                    strategy_has_valid_shape = True
                    for row in strategy_rows[1:]:
                        row_map = {header[index]: row[index].strip() for index in range(min(len(header), len(row)))}
                        artifact_path = row_map.get("artifact_path", "<missing>").strip()
                        row_values = [value.strip().strip("`").lower() for value in row_map.values()]
                        declares_none = all(value in SESSION_LOG_NONE_VALUES for value in row_values)
                        if declares_none:
                            continue
                        artifact_size = row_map.get("artifact_size_class", "")
                        write_strategy = row_map.get("write_strategy", "")
                        declared_before = row_map.get("declared_before_first_write", "").strip().strip("`")
                        helper = row_map.get("helper", "")
                        forbidden_checked = row_map.get("forbidden_methods_checked", "").strip().strip("`").lower()
                        inspected = " ".join(row_map.values())
                        if SESSION_LOG_LARGE_ARTIFACT_SIZE_RE.search(artifact_size):
                            if not SESSION_LOG_DECLARED_BEFORE_WRITE_RE.fullmatch(declared_before):
                                non_preflight_rows.append(f"{artifact_path}: declared_before_first_write={declared_before or '-'}")
                            if not SESSION_LOG_ARTIFACT_WRITER_HELPER_RE.search(f"{write_strategy} {helper}"):
                                missing_helper_rows.append(f"{artifact_path}: helper={helper or '-'}; write_strategy={write_strategy or '-'}")
                        if SESSION_LOG_FORBIDDEN_INITIAL_WRITE_RE.search(inspected) or forbidden_checked not in {
                            "yes",
                            "true",
                            "pass",
                            "passed",
                        }:
                            unsafe_strategy_rows.append(f"{artifact_path}: {inspected[:220]}")
                else:
                    findings.append(
                        Finding(
                            id="session-log-artifact-write-strategy-invalid-table",
                            severity=severity,
                            category="session-log",
                            title="Artifact Write Strategy table misses required columns",
                            details=(
                                "`Artifact Write Strategy` must be a table with artifact_path, artifact_size_class, "
                                "write_strategy, declared_before_first_write, helper and forbidden_methods_checked."
                            ),
                            path=display_path,
                            evidence=missing_columns,
                            recommended_action="Rewrite the section using references/agent/session-log-format.md.",
                        )
                    )
            else:
                findings.append(
                    Finding(
                        id="session-log-artifact-write-strategy-invalid-table",
                        severity=severity,
                        category="session-log",
                        title="Artifact Write Strategy section is not structured",
                        details="`Artifact Write Strategy` must contain a Markdown table.",
                        path=display_path,
                        evidence=["no artifact write strategy table rows"],
                        recommended_action="Add structured rows for each generated artifact written by the stage.",
                    )
                )

            if non_preflight_rows:
                findings.append(
                    Finding(
                        id="session-log-artifact-write-strategy-not-preflight",
                        severity=severity,
                        category="session-log",
                        title="Artifact Write Strategy was not declared before the first write",
                        details=(
                            "For large generated artifacts, the safe file-based/chunked strategy must be selected "
                            "before any write attempt. A later fallback is not a clean run."
                        ),
                        path=display_path,
                        evidence=non_preflight_rows[:10],
                        recommended_action=(
                            "Restart the stage or mark it blocked-technical; do not continue as ready-for-review/"
                            "ready-for-next-stage from a contaminated write path."
                        ),
                    )
                )
            if missing_helper_rows:
                findings.append(
                    Finding(
                        id="session-log-artifact-writer-helper-missing",
                        severity=severity,
                        category="session-log",
                        title="Large artifact write strategy does not use the canonical artifact writer helper",
                        details=(
                            "Large/table-heavy/package-based artifacts must be written with "
                            "`scripts/write_artifact_sections.py` so large Markdown travels through files, not shell "
                            "arguments or ad-hoc generators."
                        ),
                        path=display_path,
                        evidence=missing_helper_rows[:10],
                        recommended_action="Use `scripts/write_artifact_sections.py --manifest <manifest.json>`.",
                    )
                )
            if unsafe_strategy_rows:
                findings.append(
                    Finding(
                        id="session-log-artifact-write-strategy-unsafe",
                        severity=severity,
                        category="session-log",
                        title="Artifact Write Strategy includes unsafe or unchecked write methods",
                        details=(
                            "The declared strategy must explicitly exclude one-shot PowerShell, here-string, inline "
                            "giant commands and command-line transport for large generated artifacts."
                        ),
                        path=display_path,
                        evidence=unsafe_strategy_rows[:10],
                        recommended_action="Set forbidden_methods_checked to `yes` only after selecting the helper path.",
                    )
                )

            strategy_has_findings = any(
                finding.id.startswith("session-log-artifact-write-strategy")
                or finding.id == "session-log-artifact-writer-helper-missing"
                for finding in findings
            )
            if strategy_has_valid_shape and not strategy_has_findings:
                checks.append(
                    Check(
                        "session-log-artifact-write-strategy",
                        "pass",
                        "Artifact Write Strategy disclosure passed.",
                        display_path,
                    )
                )
            elif strategy_section:
                checks.append(
                    Check(
                        "session-log-artifact-write-strategy",
                        warn_status,
                        "Artifact Write Strategy disclosure has issues.",
                        display_path,
                    )
                )

        technical_section = extract_markdown_section(content, "Technical Fallbacks") or ""
        technical_rows = markdown_table_rows_from_text(technical_section)
        technical_fallback_rows: list[dict[str, str]] = []
        technical_section_has_valid_shape = False

        if technical_rows:
            header = normalize_table_header(technical_rows[0])
            missing_columns = sorted(SESSION_LOG_TECHNICAL_FALLBACK_REQUIRED_COLUMNS - set(header))
            if not missing_columns:
                technical_section_has_valid_shape = True
                for row in technical_rows[1:]:
                    row_map = {header[index]: row[index].strip() for index in range(min(len(header), len(row)))}
                    fallback_id = row_map.get("fallback_id", "").strip().strip("`").lower()
                    row_values = [value.strip().strip("`").lower() for value in row_map.values()]
                    declares_none = fallback_id in SESSION_LOG_NONE_VALUES or all(
                        value in SESSION_LOG_NONE_VALUES for value in row_values
                    )
                    if not declares_none:
                        technical_fallback_rows.append(row_map)
            else:
                findings.append(
                    Finding(
                        id="session-log-technical-fallbacks-invalid-table",
                        severity=severity,
                        category="session-log",
                        title="Technical Fallbacks table misses required columns",
                        details=(
                            "`Technical Fallbacks` must be a table with fallback_id, trigger, failed_method, "
                            "fallback_method, helper_artifact_path, retained, quality_risk and follow_up."
                        ),
                        path=display_path,
                        evidence=missing_columns,
                        recommended_action="Rewrite `Technical Fallbacks` using references/agent/session-log-format.md.",
                    )
                )
                checks.append(
                    Check("session-log-technical-fallbacks", warn_status, "Technical Fallbacks table is invalid.", display_path)
                )
        else:
            findings.append(
                Finding(
                    id="session-log-technical-fallbacks-invalid-table",
                    severity=severity,
                    category="session-log",
                    title="Technical Fallbacks section is not structured",
                    details="`Technical Fallbacks` must contain a Markdown table, even when no fallback occurred.",
                    path=display_path,
                    evidence=["no technical fallback table rows"],
                    recommended_action="Add a one-row `none` table or structured `TF-*` rows.",
                )
            )
            checks.append(
                Check("session-log-technical-fallbacks", warn_status, "Technical Fallbacks table is missing.", display_path)
            )

        fallback_hint_sources = "\n".join(
            extract_markdown_section(content, section) or ""
            for section in ("Event Timeline", "Risks And Fallbacks", "Key Decisions", "Quality Checkpoints")
        )
        fallback_hints = sorted(
            {
                match.group(0).strip()
                for match in SESSION_LOG_TECHNICAL_FALLBACK_HINT_RE.finditer(fallback_hint_sources)
            }
        )
        if fallback_hints and not technical_fallback_rows:
            findings.append(
                Finding(
                    id="session-log-technical-fallback-undisclosed",
                    severity=severity,
                    category="session-log",
                    title="Technical fallback hints are not disclosed structurally",
                    details=(
                        "The session log mentions command/patch/chunked/helper fallback symptoms outside "
                        "`Technical Fallbacks`, but `Technical Fallbacks` has no `TF-*` row."
                    ),
                    path=display_path,
                    evidence=fallback_hints[:10],
                    recommended_action=(
                        "Add a structured `TF-*` row with trigger, failed method, fallback method, helper artifact "
                        "path, retention status, quality risk and follow-up."
                    ),
                )
            )
            checks.append(
                Check(
                    "session-log-technical-fallbacks",
                    warn_status,
                    "Technical fallback hints are not structurally disclosed.",
                    display_path,
                )
            )

        incomplete_rows: list[str] = []
        helper_path_rows: list[str] = []
        forbidden_initial_write_rows: list[str] = []
        encoding_source_fidelity_rows: list[str] = []
        for row_map in technical_fallback_rows:
            fallback_id = row_map.get("fallback_id", "<missing>").strip()
            required_text_fields = ["trigger", "failed_method", "fallback_method", "quality_risk", "follow_up"]
            missing_text_fields = [
                field
                for field in required_text_fields
                if row_map.get(field, "").strip().strip("`").lower() in SESSION_LOG_NONE_VALUES
            ]
            retained = row_map.get("retained", "").strip().strip("`").lower()
            if retained not in {"yes", "no", "n/a", "not-applicable", "not applicable"}:
                missing_text_fields.append("retained")
            fallback_method = row_map.get("fallback_method", "").lower()
            helper_path = row_map.get("helper_artifact_path", "").strip().strip("`").lower()
            if re.search(r"helper|script|generator|generate_|temp|temporary", fallback_method) and helper_path in SESSION_LOG_NONE_VALUES:
                helper_path_rows.append(fallback_id)
            if missing_text_fields:
                incomplete_rows.append(f"{fallback_id}: {', '.join(missing_text_fields)}")
            trigger = row_map.get("trigger", "")
            failed_method = row_map.get("failed_method", "")
            if SESSION_LOG_FORBIDDEN_INITIAL_WRITE_RE.search(f"{trigger} {failed_method}"):
                forbidden_initial_write_rows.append(
                    f"{fallback_id}: trigger={trigger.strip() or '-'}; failed_method={failed_method.strip() or '-'}"
                )
            quality_risk = row_map.get("quality_risk", "")
            follow_up = row_map.get("follow_up", "")
            encoding_context = f"{trigger} {failed_method} {fallback_method} {quality_risk} {follow_up}"
            if SESSION_LOG_ENCODING_FALLBACK_RE.search(encoding_context):
                missing_encoding_proofs: list[str] = []
                if not SESSION_LOG_ENCODING_UTF8_REREAD_RE.search(encoding_context):
                    missing_encoding_proofs.append("explicit UTF-8 reread")
                if not SESSION_LOG_ENCODING_STDOUT_NOT_USED_RE.search(encoding_context):
                    missing_encoding_proofs.append("distorted stdout not used as evidence")
                if missing_encoding_proofs:
                    encoding_source_fidelity_rows.append(
                        f"{fallback_id}: missing {', '.join(missing_encoding_proofs)}"
                    )

        if forbidden_initial_write_rows:
            findings.append(
                Finding(
                    id="session-log-forbidden-initial-one-shot-write",
                    severity=severity,
                    category="session-log",
                    title="Session log records a forbidden initial one-shot write attempt",
                    details=(
                        "For large/package-based writer artifacts, hitting a Windows command-line or here-string "
                        "limit and then switching to chunked writing is not a clean fallback. The writer must choose "
                        "file-based/chunked writing during Artifact Write Strategy preflight before the first write."
                    ),
                    path=display_path,
                    evidence=forbidden_initial_write_rows[:10],
                    recommended_action=(
                        "Treat this run as technically contaminated for clean eval purposes. Update the writer "
                        "instructions/run to start with `scripts/update_markdown_section.py --content-file` / `--stdin` "
                        "or a committed helper, not one-shot PowerShell/here-string."
                    ),
                )
            )
            checks.append(
                Check(
                    "session-log-forbidden-initial-write",
                    warn_status,
                    "Forbidden initial one-shot write fallback was recorded.",
                    display_path,
                )
            )

        if encoding_source_fidelity_rows:
            findings.append(
                Finding(
                    id="session-log-encoding-fallback-source-fidelity-missing",
                    severity=severity,
                    category="session-log",
                    title="Encoding fallback does not prove source fidelity",
                    details=(
                        "When PowerShell/console output corrupts Cyrillic or another UTF-8 source, the session log "
                        "must state that the source was re-read through an explicit UTF-8 file/script path and that "
                        "the distorted stdout was not used as evidence for analysis or traceability."
                    ),
                    path=display_path,
                    evidence=encoding_source_fidelity_rows[:10],
                    recommended_action=(
                        "Complete the `TF-*` row: name the UTF-8 reread method and explicitly state that mojibake/"
                        "distorted console output was discarded or not used as evidence."
                    ),
                )
            )
            checks.append(
                Check(
                    "session-log-encoding-fallback",
                    warn_status,
                    "Encoding fallback source fidelity disclosure is incomplete.",
                    display_path,
                )
            )

        if incomplete_rows or helper_path_rows:
            evidence = []
            if incomplete_rows:
                evidence.extend(incomplete_rows[:10])
            if helper_path_rows:
                evidence.extend([f"{fallback_id}: helper_artifact_path required" for fallback_id in helper_path_rows[:10]])
            findings.append(
                Finding(
                    id="session-log-technical-fallbacks-incomplete",
                    severity=severity,
                    category="session-log",
                    title="Technical fallback rows are incomplete",
                    details=(
                        "Each real technical fallback row must describe the trigger, failed method, fallback method, "
                        "retention status, quality risk and follow-up. Helper/script/temp fallbacks must include a "
                        "helper artifact path or explain retention."
                    ),
                    path=display_path,
                    evidence=evidence,
                    recommended_action="Complete the `Technical Fallbacks` row before ending the stage.",
                )
            )
            checks.append(
                Check("session-log-technical-fallbacks", warn_status, "Technical fallback rows are incomplete.", display_path)
            )
        elif technical_section_has_valid_shape and not fallback_hints:
            checks.append(
                Check("session-log-technical-fallbacks", "pass", "Technical fallback disclosure passed.", display_path)
            )

        metadata_section = extract_markdown_section(content, "Session Metadata") or ""
        skill_match = re.search(r"\|\s*skill\s*\|\s*`?([^`|\s]+)`?\s*\|", metadata_section)
        log_skill = skill_match.group(1).strip() if skill_match else ""
        is_source_locator_log = path.name.lower() == "source-locator-session-log.md" or log_skill == "ft-source-locator"
        if is_source_locator_log:
            ft_slug_match = re.search(r"\|\s*ft_slug\s*\|\s*`?([^`|\s]+)`?\s*\|", metadata_section)
            ft_slug = ft_slug_match.group(1).strip() if ft_slug_match else ""
            clean_boundary_sections = "\n".join(
                extract_markdown_section(content, section) or ""
                for section in ("Inputs Not Used", "Contamination Check")
            )
            clean_boundary_lower = clean_boundary_sections.lower()
            has_ft_package_ref = bool(ft_slug and ft_slug in clean_boundary_sections)
            has_neighbor_ref = any(
                token in clean_boundary_lower
                for token in (
                    "fts/",
                    "fts\\",
                    "sibling",
                    "neighbor",
                    "baseline",
                    "old version",
                    "стар",
                    "сосед",
                )
            )
            has_exclusion_ref = any(
                token in clean_boundary_lower
                for token in (
                    "not used",
                    "not opened",
                    "excluded",
                    "forbidden",
                    "не использ",
                    "не откры",
                    "запрещ",
                    "исключ",
                )
            )
            if not (has_ft_package_ref and has_neighbor_ref and has_exclusion_ref):
                evidence = []
                if ft_slug and not has_ft_package_ref:
                    evidence.append(f"ft_slug `{ft_slug}` is not referenced in Inputs Not Used / Contamination Check")
                if not has_neighbor_ref:
                    evidence.append("neighbor/baseline package exclusion is not explicit")
                if not has_exclusion_ref:
                    evidence.append("exclusion/not-used wording is not explicit")
                findings.append(
                    Finding(
                        id="session-log-source-locator-clean-boundary-missing",
                        severity=severity,
                        category="session-log",
                        title="Source locator session log does not prove clean package boundary",
                        details=(
                            "A source-locator audit log must explicitly name the selected FT package boundary and "
                            "neighbor/baseline inputs that were not opened or used."
                        ),
                        path=display_path,
                        evidence=evidence or ["Inputs Not Used / Contamination Check are too generic"],
                        recommended_action=(
                            "Update `Inputs Not Used` and `Contamination Check` with the selected `fts/<ft-slug>` "
                            "and the excluded sibling/baseline package pattern."
                        ),
                    )
                )
                checks.append(
                    Check(
                        "session-log-source-locator-clean-boundary",
                        warn_status,
                        "Source locator clean package boundary is not explicit.",
                        display_path,
                    )
                )
            else:
                checks.append(
                    Check(
                        "session-log-source-locator-clean-boundary",
                        "pass",
                        "Source locator clean package boundary is explicit.",
                        display_path,
                    )
                )

    return findings, checks


def validate_decision_log(
    path: Path,
    root: Path,
    *,
    decision_log_policy: str = "compatible",
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    severity = "warning" if decision_log_policy == "strict" else "info"
    warn_status = "warn" if decision_log_policy == "strict" else "pass"

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        findings.append(
            Finding(
                id="decision-log-not-utf8",
                severity="error",
                category="decision-log",
                title="Decision log is not UTF-8",
                details=str(exc),
                path=display_path,
                evidence=[],
                recommended_action="Save agent-decision-log.md as UTF-8 Markdown.",
            )
        )
        checks.append(Check("decision-log-format", "fail", "Decision log is not UTF-8.", display_path))
        return findings, checks

    section = extract_markdown_section(content, "Decision Log")
    if section is None:
        findings.append(
            Finding(
                id="decision-log-missing-required-section",
                severity=severity,
                category="decision-log",
                title="Decision log misses Decision Log section",
                details=(
                    "agent-decision-log.md must contain a `## Decision Log` table with observable "
                    "intermediate decisions, not hidden chain-of-thought."
                ),
                path=display_path,
                evidence=["Decision Log"],
                recommended_action="Rewrite the artifact using references/agent/agent-decision-log-format.md.",
            )
        )
        checks.append(Check("decision-log-format", warn_status, "Decision log misses required section.", display_path))
        return findings, checks

    rows = markdown_table_rows_from_text(section)
    if not rows:
        findings.append(
            Finding(
                id="decision-log-missing-table",
                severity=severity,
                category="decision-log",
                title="Decision log has no Markdown table",
                details="The Decision Log section must be a parseable Markdown table.",
                path=display_path,
                evidence=[],
                recommended_action="Add the canonical decision table from references/agent/agent-decision-log-format.md.",
            )
        )
        checks.append(Check("decision-log-format", warn_status, "Decision log table is missing.", display_path))
        return findings, checks

    header = normalize_table_header(rows[0])
    missing_columns = sorted(DECISION_LOG_REQUIRED_COLUMNS - set(header))
    if missing_columns:
        findings.append(
            Finding(
                id="decision-log-missing-required-columns",
                severity=severity,
                category="decision-log",
                title="Decision log misses required columns",
                details="The decision table must expose the decision, source/input, rationale, output artifact and risk.",
                path=display_path,
                evidence=missing_columns,
                recommended_action="Use the canonical columns from references/agent/agent-decision-log-format.md.",
            )
        )
        checks.append(Check("decision-log-format", warn_status, "Decision log columns are incomplete.", display_path))
        return findings, checks

    parsed_rows: list[dict[str, str]] = []
    for raw_row in rows[1:]:
        parsed_rows.append(
            {
                column_name: raw_row[index].strip().strip("`") if index < len(raw_row) else ""
                for index, column_name in enumerate(header)
            }
        )

    meaningful_rows = [
        row
        for row in parsed_rows
        if any((row.get(column) or "").strip().lower() not in SESSION_LOG_NONE_VALUES for column in header)
    ]
    if not meaningful_rows:
        findings.append(
            Finding(
                id="decision-log-empty",
                severity=severity,
                category="decision-log",
                title="Decision log has no decision rows",
                details="A stage decision log must contain at least one observable decision row.",
                path=display_path,
                evidence=[],
                recommended_action="Record the source/scope/write/review decisions that shaped the output.",
            )
        )
        checks.append(Check("decision-log-format", warn_status, "Decision log has no rows.", display_path))
        return findings, checks

    incomplete_rows: list[str] = []
    invalid_ids: list[str] = []
    for row_index, row in enumerate(meaningful_rows, start=1):
        decision_id = (row.get("decision_id") or "").strip()
        if not DECISION_LOG_ID_RE.fullmatch(decision_id):
            invalid_ids.append(decision_id or f"row {row_index}")
        missing_in_row = [
            column
            for column in sorted(DECISION_LOG_REQUIRED_COLUMNS)
            if (row.get(column) or "").strip().lower() in SESSION_LOG_NONE_VALUES
        ]
        if missing_in_row:
            incomplete_rows.append(f"{decision_id or f'row {row_index}'}: {', '.join(missing_in_row)}")

    if invalid_ids:
        findings.append(
            Finding(
                id="decision-log-invalid-decision-id",
                severity=severity,
                category="decision-log",
                title="Decision log has invalid decision ids",
                details="Decision ids must be stable IDs such as `DEC-001` so later artifacts can reference them.",
                path=display_path,
                evidence=invalid_ids[:20],
                recommended_action="Rename decision ids to `DEC-001`, `DEC-002`, ... or `DL-001`, `DL-002`, ... .",
            )
        )

    if incomplete_rows:
        findings.append(
            Finding(
                id="decision-log-incomplete-rows",
                severity=severity,
                category="decision-log",
                title="Decision log rows are incomplete",
                details="Each decision row must explain what changed, why, which input triggered it and where it landed.",
                path=display_path,
                evidence=incomplete_rows[:20],
                recommended_action="Fill every required column; do not use `none` for real decisions.",
            )
        )

    hidden_reasoning_match = re.search(
        r"chain[-\s]?of[-\s]?thought|hidden\s+reasoning|скрыт\w*\s+рассужд|внутренн\w*\s+рассужд",
        content,
        flags=re.IGNORECASE,
    )
    if hidden_reasoning_match:
        findings.append(
            Finding(
                id="decision-log-hidden-reasoning-smell",
                severity=severity,
                category="decision-log",
                title="Decision log appears to reference hidden reasoning",
                details=(
                    "Decision logs must capture observable actions, inputs, decisions and rationale, "
                    "not private chain-of-thought."
                ),
                path=display_path,
                evidence=[hidden_reasoning_match.group(0)],
                recommended_action="Rewrite the row as an observable decision with source/input, rationale and risk.",
            )
        )

    has_decision_log_findings = any(finding.category == "decision-log" for finding in findings)
    checks.append(
        Check(
            "decision-log-format",
            warn_status if has_decision_log_findings else "pass",
            "Decision log has issues." if has_decision_log_findings else "Decision log format passed.",
            display_path,
        )
    )
    return findings, checks


def validate_ui_evidence_index(path: Path, root: Path) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    content = path.read_text(encoding="utf-8")
    content_lower = content.lower()
    rows = markdown_table_rows(path)
    local_output_policy = (
        "evidence_export_policy" in content_lower
        and "local-output-index-only" in content_lower
    )
    dom_seeded_policy = (
        "dom_seeded_policy" in content_lower
        and "non-canonical-observation" in content_lower
    )
    trace_not_collected_policy = (
        "trace_policy" in content_lower
        and "not-collected" in content_lower
    )

    output_paths: list[str] = []
    missing_paths: list[str] = []
    dom_seeded_entries: list[str] = []

    for row in rows[1:]:
        if len(row) < 4:
            continue
        test_case_id, artifact_type, artifact_path, note = row[:4]
        if artifact_path.startswith("output/"):
            output_paths.append(artifact_path)
        if "dom-seeded" in artifact_type.lower() or "dom-seeded" in note.lower():
            dom_seeded_entries.append(test_case_id)
        if artifact_path and not artifact_path.startswith(("http://", "https://")):
            candidate = root / artifact_path
            if not candidate.exists():
                missing_paths.append(artifact_path)

    if output_paths and local_output_policy:
        findings.append(
            Finding(
                id="ui-evidence-output-paths-declared-local",
                severity="info",
                category="ui-evidence",
                title="UI evidence explicitly declares local output paths",
                details="Evidence under output/ is intentionally treated as local-only and non-portable.",
                path=display_path,
                evidence=output_paths[:10],
                recommended_action="Export durable artifacts when this evidence must be independently reproducible.",
            )
        )
    elif output_paths:
        findings.append(
            Finding(
                id="ui-evidence-output-paths-are-local",
                severity="warning",
                category="ui-evidence",
                title="UI evidence points to ignored local output paths",
                details="Evidence under output/ is usually ignored and may not be available in another checkout.",
                path=display_path,
                evidence=output_paths[:10],
                recommended_action="Add an artifact export policy or mark these paths as local/ignored explicitly.",
            )
        )
    unqualified_missing_paths = [
        artifact_path
        for artifact_path in missing_paths
        if not (local_output_policy and artifact_path.startswith("output/"))
    ]
    if unqualified_missing_paths:
        findings.append(
            Finding(
                id="ui-evidence-artifacts-missing",
                severity="warning",
                category="ui-evidence",
                title="UI evidence artifact paths are missing",
                details="The evidence index references files that are not present in the current checkout.",
                path=display_path,
                evidence=unqualified_missing_paths[:10],
                recommended_action="Restore the artifacts, export them, or mark them as external/local-only.",
            )
        )
    if dom_seeded_entries and dom_seeded_policy:
        findings.append(
            Finding(
                id="ui-evidence-dom-seeded-observations-declared",
                severity="info",
                category="ui-evidence",
                title="UI evidence explicitly separates DOM-seeded observations",
                details="DOM-seeded observations are documented as non-canonical and should not count as normal confirmed UI paths.",
                path=display_path,
                evidence=dom_seeded_entries[:10],
                recommended_action="Keep corresponding UI validation statuses blocked or limited unless a normal UI path is reproduced.",
            )
        )
    elif dom_seeded_entries:
        findings.append(
            Finding(
                id="ui-evidence-dom-seeded-observations",
                severity="warning",
                category="ui-evidence",
                title="UI evidence includes DOM-seeded observations",
                details="DOM seeding is not equivalent to a normal user-confirmed UI path.",
                path=display_path,
                evidence=dom_seeded_entries[:10],
                recommended_action="Keep DOM-seeded observations separate from canonical confirmed UI checks.",
            )
        )
    traces_not_saved = bool(
        re.search(r"traces?\s+не\s+сохран", content, flags=re.IGNORECASE)
    )
    if traces_not_saved and trace_not_collected_policy:
        findings.append(
            Finding(
                id="ui-evidence-traces-not-collected-declared",
                severity="info",
                category="ui-evidence",
                title="UI evidence explicitly declares traces were not collected",
                details="The run records trace absence as an intentional limitation instead of implying replayable evidence.",
                path=display_path,
                evidence=[],
                recommended_action="Collect traces for future confirmed or mismatch UI checks when reproducibility is required.",
            )
        )
    elif traces_not_saved:
        findings.append(
            Finding(
                id="ui-evidence-traces-not-saved",
                severity="warning",
                category="ui-evidence",
                title="UI evidence says Playwright traces were not saved",
                details="Confirmed or mismatch cases are harder to reproduce without traces.",
                path=display_path,
                evidence=[],
                recommended_action="Save traces for confirmed/mismatch cases or record a deliberate limitation.",
            )
        )

    has_warning_or_error = any(finding.severity in {"error", "warning"} for finding in findings)
    status = "warn" if has_warning_or_error else "pass"
    details = (
        "UI evidence policy findings present."
        if has_warning_or_error
        else "UI evidence policy checks passed with documented limitations."
        if findings
        else "UI evidence policy checks passed."
    )
    checks.append(
        Check(
            "ui-evidence-policy",
            status,
            details,
            display_path,
        )
    )
    return findings, checks


def validate_ui_validation_report(path: Path, root: Path) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)
    rows = markdown_table_rows(path)
    noncanonical: list[str] = []

    for row in rows[1:]:
        if len(row) < 2:
            continue
        test_case_id, status = row[0], row[1]
        if not test_case_id.startswith("TC-"):
            continue
        if status and status not in ALLOWED_UI_STATUSES:
            noncanonical.append(f"{test_case_id}: {status}")

    if noncanonical:
        findings.append(
            Finding(
                id="ui-validation-report-noncanonical-statuses",
                severity="warning",
                category="ui-evidence",
                title="UI validation report contains noncanonical statuses",
                details="UI verification statuses should use the canonical enum or document an explicit extension.",
                path=display_path,
                evidence=noncanonical[:10],
                recommended_action="Map these statuses to the canonical enum or extend the enum in references first.",
            )
        )

    checks.append(
        Check(
            "ui-validation-status-enum",
            "warn" if findings else "pass",
            "Noncanonical UI statuses found." if findings else "UI statuses are canonical.",
            display_path,
        )
    )
    return findings, checks


def get_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"-?\d+", value.strip()):
        return int(value)
    return None


def residual_risk_value_is_meaningful(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip().strip("`").strip().lower()
    return bool(normalized and normalized not in {"none", "-", "n/a", "na", "null", "0"})


def collect_residual_risk_source_refs(source_paths: list[Path]) -> dict[str, Any]:
    refs: dict[str, Any] = {
        "finding_ids": set(),
        "gap_ids": set(),
        "atom_ids": set(),
        "finding_records": {},
        "gap_records": {},
        "atom_records": {},
        "finding_sources": [],
        "gap_sources": [],
        "atom_sources": [],
    }

    for source_path in dedupe_paths(source_paths):
        try:
            content = source_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        name = source_path.name
        is_findings = bool(re.fullmatch(r"round-\d+-findings\.md", name) or name.endswith("findings.md"))
        is_traceability = name.endswith("traceability-matrix.md")
        is_gap_artifact = name == "scope-coverage-gaps.md"

        finding_ids = set(extract_finding_ids_from_text(content))
        gap_ids = set(extract_gap_ids_from_text(content))
        atom_ids = set(extract_atom_ids_from_text(content))

        if is_findings:
            refs["finding_sources"].append(source_path)
            refs["finding_ids"].update(finding_ids)
            refs["gap_ids"].update(gap_ids)
            for finding_id, block in extract_finding_blocks(content):
                refs["finding_records"].setdefault(finding_id, []).append(
                    {
                        "path": source_path,
                        "fields": parse_markdown_fields(block),
                    }
                )
            if gap_ids:
                refs["gap_sources"].append(source_path)
        if is_traceability:
            refs["atom_sources"].append(source_path)
            refs["atom_ids"].update(atom_ids)
            refs["gap_ids"].update(gap_ids)
            rows = markdown_table_rows_from_text(content)
            if rows:
                header = normalize_table_header(rows[0])
                atom_index = header.index("atom_id") if "atom_id" in header else None
                coverage_index = header.index("coverage_status") if "coverage_status" in header else None
                if atom_index is not None:
                    for row in rows[1:]:
                        if atom_index >= len(row):
                            continue
                        atom_id = row[atom_index].strip().strip("`")
                        if not re.fullmatch(r"ATOM-\d{3,}", atom_id):
                            continue
                        fields: dict[str, str] = {}
                        if coverage_index is not None and coverage_index < len(row):
                            fields["coverage_status"] = normalize_markdown_field_value(row[coverage_index]).lower()
                        refs["atom_records"].setdefault(atom_id, []).append(
                            {
                                "path": source_path,
                                "fields": fields,
                            }
                        )
            if gap_ids:
                refs["gap_sources"].append(source_path)
        if is_gap_artifact:
            refs["gap_sources"].append(source_path)
            refs["gap_ids"].update(gap_ids)
            for gap_match in re.finditer(r"^###\s+(GAP-\d{3,})\s*$", content, flags=re.MULTILINE):
                next_heading = re.search(r"^###\s+", content[gap_match.end():], flags=re.MULTILINE)
                block_end = gap_match.end() + next_heading.start() if next_heading else len(content)
                refs["gap_records"].setdefault(gap_match.group(1), []).append(
                    {
                        "path": source_path,
                        "fields": parse_markdown_fields(content[gap_match.end():block_end]),
                    }
                )

    return refs


def residual_finding_record_is_open_blocking(record: dict[str, Any]) -> bool:
    fields = record.get("fields")
    if not isinstance(fields, dict):
        return False
    return fields.get("severity") in {"error", "warning"} and fields.get("status") == "open"


def residual_gap_record_has_canonical_semantics(record: dict[str, Any]) -> bool:
    fields = record.get("fields")
    if not isinstance(fields, dict):
        return False

    impact = fields.get("impact")
    blocks_ready = fields.get("blocks_ready_for_review")
    if impact not in {"blocking", "non-blocking"} or blocks_ready not in {"yes", "no"}:
        return False
    return (impact == "blocking" and blocks_ready == "yes") or (
        impact == "non-blocking" and blocks_ready == "no"
    )


def residual_atom_record_has_expected_status(record: dict[str, Any], expected_status: str) -> bool:
    fields = record.get("fields")
    if not isinstance(fields, dict):
        return False
    return fields.get("coverage_status") == expected_status


def residual_record_summary(record: dict[str, Any], field_names: tuple[str, ...]) -> str:
    fields = record.get("fields") if isinstance(record, dict) else None
    if not isinstance(fields, dict):
        return "<unparseable>"
    return ", ".join(f"{field_name}={fields.get(field_name) or '<missing>'}" for field_name in field_names)


def residual_risk_unknown_refs(fields: dict[str, str], source_paths: list[Path]) -> list[str]:
    source_refs = collect_residual_risk_source_refs(source_paths)
    issues: list[str] = []

    remaining_blocking = fields.get("remaining_blocking_findings", "")
    finding_refs = set(extract_finding_ids_from_text(remaining_blocking))
    finding_sources = source_refs["finding_sources"]
    if finding_refs and not finding_sources:
        issues.append(
            "remaining_blocking_findings cannot be verified: no linked final/round findings artifact"
        )
    elif finding_refs:
        missing = sorted(finding_refs - source_refs["finding_ids"])
        issues.extend(f"remaining_blocking_findings:{finding_id} not found in linked findings artifacts" for finding_id in missing)

    gap_field_names = (
        "remaining_traceability_gaps",
        "remaining_coverage_gaps",
        "remaining_unclear_items",
    )
    gap_sources = source_refs["gap_sources"]
    for field_name in gap_field_names:
        gap_refs = set(extract_gap_ids_from_text(fields.get(field_name, "")))
        if gap_refs and not gap_sources:
            issues.append(f"{field_name} cannot be verified: no linked coverage/traceability gap artifact")
            continue
        missing = sorted(gap_refs - source_refs["gap_ids"])
        issues.extend(f"{field_name}:{gap_id} not found in linked gap artifacts" for gap_id in missing)

    atom_field_names = ("remaining_traceability_gaps", "remaining_unclear_items")
    atom_sources = source_refs["atom_sources"]
    for field_name in atom_field_names:
        atom_refs = set(extract_atom_ids_from_text(fields.get(field_name, "")))
        if atom_refs and not atom_sources:
            issues.append(f"{field_name} cannot be verified: no linked final traceability matrix")
            continue
        missing = sorted(atom_refs - source_refs["atom_ids"])
        issues.extend(f"{field_name}:{atom_id} not found in linked traceability matrix" for atom_id in missing)

    return issues[:20]


def residual_risk_semantic_issues(fields: dict[str, str], source_paths: list[Path]) -> list[str]:
    source_refs = collect_residual_risk_source_refs(source_paths)
    issues: list[str] = []

    finding_records: dict[str, list[dict[str, Any]]] = source_refs["finding_records"]
    for finding_id in extract_finding_ids_from_text(fields.get("remaining_blocking_findings", "")):
        records = finding_records.get(finding_id, [])
        if not records:
            continue
        if any(residual_finding_record_is_open_blocking(record) for record in records):
            continue
        summaries = "; ".join(
            residual_record_summary(record, ("severity", "status"))
            for record in records[:3]
        )
        issues.append(
            f"remaining_blocking_findings:{finding_id} is not an open blocking finding ({summaries})"
        )

    remaining_coverage_gaps = fields.get("remaining_coverage_gaps", "")
    coverage_gap_placeholders = [
        gap_id
        for gap_id in extract_gap_ids_from_text(remaining_coverage_gaps)
        if gap_id.startswith("coverage_gap:")
    ]
    issues.extend(
        f"remaining_coverage_gaps:{gap_id} is a placeholder; use a GAP-* from scope-coverage-gaps.md"
        for gap_id in coverage_gap_placeholders
    )

    gap_records: dict[str, list[dict[str, Any]]] = source_refs["gap_records"]
    for gap_id in extract_gap_ids_from_text(remaining_coverage_gaps):
        if not gap_id.startswith("GAP-"):
            continue
        records = gap_records.get(gap_id, [])
        if not records:
            issues.append(
                f"remaining_coverage_gaps:{gap_id} has no scope-coverage-gaps block with Impact/Blocks Ready For Review"
            )
            continue
        if any(residual_gap_record_has_canonical_semantics(record) for record in records):
            continue
        summaries = "; ".join(
            residual_record_summary(record, ("impact", "blocks_ready_for_review"))
            for record in records[:3]
        )
        issues.append(f"remaining_coverage_gaps:{gap_id} has inconsistent gap semantics ({summaries})")

    atom_records: dict[str, list[dict[str, Any]]] = source_refs["atom_records"]
    for field_name, expected_status in (
        ("remaining_traceability_gaps", "gap"),
        ("remaining_unclear_items", "unclear"),
    ):
        for atom_id in extract_atom_ids_from_text(fields.get(field_name, "")):
            records = atom_records.get(atom_id, [])
            if not records:
                issues.append(
                    f"{field_name}:{atom_id} has no parseable traceability matrix row with coverage_status"
                )
                continue
            if any(residual_atom_record_has_expected_status(record, expected_status) for record in records):
                continue
            summaries = "; ".join(
                residual_record_summary(record, ("coverage_status",))
                for record in records[:3]
            )
            issues.append(
                f"{field_name}:{atom_id} has coverage_status mismatch ({summaries}; expected={expected_status})"
            )

    return issues[:20]


def residual_risk_source_artifacts(
    latest_artifacts: Any,
    latest_artifact_values: list[str],
    workflow_path: Path,
    root: Path,
    ft_root: Path,
) -> list[Path]:
    source_values: list[str] = []
    if isinstance(latest_artifacts, dict):
        for key in (
            "final_findings",
            "findings",
            "review_findings",
            "final_traceability_matrix",
            "traceability_matrix",
            "scope_coverage_gaps",
        ):
            value = latest_artifacts.get(key)
            if isinstance(value, str):
                source_values.append(value)

    for value in latest_artifact_values:
        name = Path(strip_quotes(value)).name
        if (
            re.fullmatch(r"round-\d+-findings\.md", name)
            or name.endswith("traceability-matrix.md")
            or name == "scope-coverage-gaps.md"
        ):
            source_values.append(value)

    resolved_paths = [
        resolved
        for value in source_values
        for resolved in [resolve_artifact_path(value, workflow_path, root, ft_root)]
        if resolved is not None
    ]
    return dedupe_paths(resolved_paths)


def validate_loop_summary_residual_risk(
    loop_path: Path,
    root: Path,
    metrics: dict[str, Any],
    source_paths: list[Path] | None = None,
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(loop_path, root)

    if metrics.get("final_status") != "round-cap-reached":
        return findings, checks

    fields = metrics.get("residual_risk_fields")
    if not isinstance(fields, dict):
        findings.append(
            Finding(
                id="loop-summary-round-cap-missing-residual-risk",
                severity="warning",
                category="status-model",
                title="round-cap loop summary has no Final Residual Risk block",
                details=(
                    "`round-cap-reached` means unresolved work remains, so loop-summary.md "
                    "must list residual blocking findings, gaps, unclear items, rationale and next action."
                ),
                path=display_path,
                evidence=[],
                recommended_action=(
                    "Add ## Final Residual Risk with remaining_blocking_findings, "
                    "remaining_traceability_gaps, remaining_coverage_gaps, remaining_unclear_items, "
                    "decision_rationale and next_action."
                ),
            )
        )
        checks.append(
            Check(
                "loop-summary-final-residual-risk",
                "warn",
                "Final Residual Risk block is missing.",
                display_path,
            )
        )
        return findings, checks

    missing_fields = sorted(REQUIRED_RESIDUAL_RISK_FIELDS - set(fields))
    if missing_fields:
        findings.append(
            Finding(
                id="loop-summary-round-cap-residual-risk-missing-fields",
                severity="warning",
                category="status-model",
                title="Final Residual Risk misses required fields",
                details="A round-cap loop summary must expose all residual-risk fields in a machine-checkable format.",
                path=display_path,
                evidence=missing_fields,
                recommended_action="Add the missing fields from references/agent/iteration-lifecycle-format.md.",
            )
        )

    inconsistencies: list[str] = []
    blocking_findings = (get_int(metrics.get("findings_error")) or 0) + (
        get_int(metrics.get("findings_warning")) or 0
    )
    if blocking_findings > 0 and not residual_risk_value_is_meaningful(
        fields.get("remaining_blocking_findings")
    ):
        inconsistencies.append(
            f"remaining_blocking_findings=none while findings error/warning={blocking_findings}"
        )

    traceability_gaps = get_int(metrics.get("traceability_gap")) or 0
    if traceability_gaps > 0 and not residual_risk_value_is_meaningful(
        fields.get("remaining_traceability_gaps")
    ):
        inconsistencies.append(f"remaining_traceability_gaps=none while traceability gap={traceability_gaps}")

    traceability_unclear = get_int(metrics.get("traceability_unclear")) or 0
    if traceability_unclear > 0 and not residual_risk_value_is_meaningful(
        fields.get("remaining_unclear_items")
    ):
        inconsistencies.append(
            f"remaining_unclear_items=none while traceability unclear={traceability_unclear}"
        )

    gap_mentions = get_int(metrics.get("gap_mentions")) or 0
    if gap_mentions > 0 and not residual_risk_value_is_meaningful(fields.get("remaining_coverage_gaps")):
        inconsistencies.append("remaining_coverage_gaps=none while GAP-* references are mentioned")

    if not residual_risk_value_is_meaningful(fields.get("decision_rationale")):
        inconsistencies.append("decision_rationale missing/empty")
    if not residual_risk_value_is_meaningful(fields.get("next_action")):
        inconsistencies.append("next_action missing/empty")

    if inconsistencies:
        findings.append(
            Finding(
                id="loop-summary-round-cap-residual-risk-inconsistent",
                severity="warning",
                category="status-model",
                title="Final Residual Risk contradicts loop-summary metrics",
                details="The residual-risk block must not claim `none` for categories that still have open metrics.",
                path=display_path,
                evidence=inconsistencies[:10],
                recommended_action="List the remaining blocker/gap IDs or change the loop metrics/status.",
            )
        )

    unknown_refs = residual_risk_unknown_refs(fields, source_paths or [])
    if unknown_refs:
        findings.append(
            Finding(
                id="loop-summary-round-cap-residual-risk-unknown-refs",
                severity="warning",
                category="status-model",
                title="Final Residual Risk references are not backed by linked artifacts",
                details=(
                    "Residual-risk IDs must resolve to the final/round findings, traceability matrix, "
                    "or scope coverage gaps linked from workflow-state.yaml."
                ),
                path=display_path,
                evidence=unknown_refs,
                recommended_action=(
                    "Fix the IDs in Final Residual Risk or add the missing final_* / scope coverage artifacts "
                    "to latest_artifacts."
                ),
            )
        )

    semantic_issues = residual_risk_semantic_issues(fields, source_paths or [])
    if semantic_issues:
        findings.append(
            Finding(
                id="loop-summary-round-cap-residual-risk-semantic-mismatch",
                severity="warning",
                category="status-model",
                title="Final Residual Risk references do not match residual-risk semantics",
                details=(
                    "Residual-risk references must point to unresolved blocking findings or canonical coverage "
                    "gap records, not merely to any existing ID."
                ),
                path=display_path,
                evidence=semantic_issues,
                recommended_action=(
                    "Point remaining_blocking_findings to open error/warning findings and keep remaining_coverage_gaps "
                    "aligned with scope-coverage-gaps Impact / Blocks Ready For Review fields."
                ),
            )
        )

    has_issues = bool(missing_fields or inconsistencies or unknown_refs or semantic_issues)
    checks.append(
        Check(
            "loop-summary-final-residual-risk",
            "warn" if has_issues else "pass",
            "Final Residual Risk block has issues." if has_issues else "Final Residual Risk block is consistent.",
            display_path,
        )
    )
    return findings, checks


def accepted_risk_gap_ids(state: dict[str, Any]) -> set[str]:
    accepted_risks = state.get("accepted_risks")
    if not isinstance(accepted_risks, list):
        return set()
    accepted_text = "\n".join(str(item) for item in accepted_risks)
    return set(extract_gap_ids_from_text(accepted_text))


def accepted_risk_entries_are_qualified(state: dict[str, Any]) -> bool:
    accepted_risks = state.get("accepted_risks")
    if not isinstance(accepted_risks, list) or not accepted_risks:
        return False
    for item in accepted_risks:
        raw_text = str(item)
        text = raw_text.lower()
        if not extract_gap_ids_from_text(raw_text):
            return False
        if "accepted-risk" not in text and "accepted risk" not in text:
            return False
        if "owner:" not in text or "rationale:" not in text or "revisit:" not in text:
            return False
    return True


def workflow_final_status(state: dict[str, Any]) -> str | None:
    iteration_result = state.get("iteration_result")
    if isinstance(iteration_result, dict) and isinstance(iteration_result.get("final_status"), str):
        return iteration_result["final_status"]

    review_loop = state.get("review_loop")
    if isinstance(review_loop, dict) and isinstance(review_loop.get("final_status"), str):
        return review_loop["final_status"]

    if isinstance(state.get("review_loop_status"), str):
        return state["review_loop_status"]

    if state.get("stage_status") in {"signed-off", "round-cap-reached"}:
        return state["stage_status"]

    return None


def expected_transition_prompt(state: dict[str, Any]) -> str | None:
    stage_status = state.get("stage_status")
    next_skill = state.get("next_skill")
    current_stage = state.get("current_stage")
    current_round = get_int(state.get("current_round")) or 1

    if next_skill == "ft-ui-automation-prep":
        return "prompt.reviewer-to-ui-prep.md"
    if (
        current_stage == "ft-test-case-reviewer"
        and stage_status == "ready-for-next-stage"
        and next_skill == "ft-test-case-writer"
    ):
        return "prompt.scope-to-writer.md"
    if (
        current_stage == "ft-scope-analyzer"
        and stage_status == "ready-for-gap-review"
        and next_skill == "ft-test-case-reviewer"
    ):
        return "prompt.scope-gaps-to-reviewer.md"
    if stage_status == "ready-for-review" or next_skill == "ft-test-case-reviewer":
        return f"prompt.writer-to-reviewer.round-{current_round}.md"
    if stage_status == "ready-for-writer-revision":
        return f"prompt.reviewer-to-writer.round-{max(current_round - 1, 1)}.md"
    if next_skill == "ft-test-case-writer" and current_stage in {"ft-source-locator", "ft-scope-analyzer"}:
        return "prompt.scope-to-writer.md"
    if next_skill == "ft-test-case-iteration":
        return "prompt.scope-to-iteration.md"

    return None


def transition_prompt_kind(prompt_name: str | None) -> str | None:
    if not prompt_name:
        return None
    name = Path(strip_quotes(prompt_name)).name.lower()
    if name.startswith("prompt.writer-to-reviewer."):
        return "writer-to-reviewer"
    if name.startswith("prompt.reviewer-to-writer."):
        return "reviewer-to-writer"
    if name == "prompt.reviewer-to-ui-prep.md":
        return "reviewer-to-ui-prep"
    if name == "prompt.scope-gaps-to-reviewer.md":
        return "scope-gaps-to-reviewer"
    if name == "prompt.scope-to-writer.md":
        return "scope-to-writer"
    if name == "prompt.scope-to-iteration.md":
        return "scope-to-iteration"
    return None


def explicit_active_transition_prompt_value(state: dict[str, Any]) -> str | None:
    latest_artifacts = state.get("latest_artifacts")
    if not isinstance(latest_artifacts, dict):
        return None
    value = latest_artifacts.get("active_transition_prompt")
    if isinstance(value, str) and value.strip():
        return value
    return None


def artifact_values_contain_resolving_name(
    expected_name: str,
    values: list[str],
    workflow_path: Path,
    root: Path,
    ft_root: Path,
) -> bool:
    return any(
        Path(value).name == expected_name and artifact_exists(value, workflow_path, root, ft_root)
        for value in values
    )


def is_signed_off_state(state: dict[str, Any]) -> bool:
    if state.get("stage_status") == "signed-off":
        return True
    if state.get("review_loop_status") == "signed-off":
        return True

    return workflow_final_status(state) == "signed-off"


def is_ready_for_review_state(state: dict[str, Any]) -> bool:
    return state.get("stage_status") == "ready-for-review" or (
        state.get("next_skill") == "ft-test-case-reviewer"
        and not (
            state.get("current_stage") == "ft-scope-analyzer"
            and state.get("stage_status") == "ready-for-gap-review"
        )
    )


def validate_reviewer_signoff_self_check(
    *,
    source_paths: list[Path],
    workflow_path: Path,
    root: Path,
    reviewer_signoff_policy: str,
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    severity = "warning" if reviewer_signoff_policy == "strict" else "info"
    check_status = "warn" if reviewer_signoff_policy == "strict" else "pass"
    readable_sources: list[tuple[Path, str]] = []

    for source_path in dedupe_paths(source_paths):
        try:
            readable_sources.append((source_path, source_path.read_text(encoding="utf-8")))
        except UnicodeDecodeError as exc:
            findings.append(
                Finding(
                    id="reviewer-signoff-self-check-unreadable",
                    severity="warning",
                    category="stage-transition",
                    title="Reviewer sign-off source is not UTF-8",
                    details=str(exc),
                    path=rel(source_path, root),
                    evidence=[],
                    recommended_action="Save the reviewer sign-off source as UTF-8 Markdown.",
                )
            )

    for source_path, content in readable_sources:
        fields = extract_reviewer_signoff_fields(content)
        if fields is None:
            continue

        issues = reviewer_signoff_field_issues(fields)
        if issues:
            findings.append(
                Finding(
                    id="reviewer-signoff-self-check-invalid",
                    severity=severity,
                    category="stage-transition",
                    title="Reviewer Sign-off Self-check is incomplete or invalid",
                    details=(
                        "The UI-prep handoff has a Reviewer Sign-off Self-check block, "
                        "but the block does not satisfy the reviewer-output-format.md contract."
                    ),
                    path=rel(source_path, root),
                    evidence=issues[:20],
                    recommended_action=(
                        "Fill all required self-check fields with canonical values before creating "
                        "prompt.reviewer-to-ui-prep.md."
                    ),
                )
            )
            checks.append(
                Check(
                    "reviewer-signoff-self-check",
                    check_status,
                    "Reviewer Sign-off Self-check has field issues.",
                    rel(source_path, root),
                )
            )
        else:
            checks.append(
                Check(
                    "reviewer-signoff-self-check",
                    "pass",
                    "Reviewer Sign-off Self-check is present and structurally valid.",
                    rel(source_path, root),
                )
            )
        return findings, checks

    findings.append(
        Finding(
            id="reviewer-signoff-self-check-missing",
            severity=severity,
            category="stage-transition",
            title="UI-prep handoff has no Reviewer Sign-off Self-check",
            details=(
                "A reviewer-to-UI-prep handoff must show that traceability, structure, grouping, "
                "test-case numbering, test-design, blocking findings, and traceability gaps were explicitly checked."
            ),
            path=rel(workflow_path, root),
            evidence=[rel(source_path, root) for source_path, _ in readable_sources] or ["<no sign-off sources resolved>"],
            recommended_action=(
                "Add `## Reviewer Sign-off Self-check` to loop-summary.md or the final findings artifact "
                "before treating the handoff as UI-prep ready."
            ),
        )
    )
    checks.append(
        Check(
            "reviewer-signoff-self-check",
            check_status,
            "Reviewer Sign-off Self-check is missing.",
            rel(workflow_path, root),
        )
    )
    return findings, checks


def validate_workflow_state(
    path: Path,
    root: Path,
    *,
    reviewer_signoff_policy: str = "compatible",
    final_alias_policy: str = "compatible",
    session_log_policy: str = "compatible",
    decision_log_policy: str = "compatible",
) -> tuple[list[Finding], list[Check]]:
    findings: list[Finding] = []
    checks: list[Check] = []
    display_path = rel(path, root)

    try:
        state = parse_workflow_state(path)
    except UnicodeDecodeError as exc:
        findings.append(
            Finding(
                id="workflow-state-unreadable",
                severity="error",
                category="workflow-state",
                title="workflow-state.yaml is not readable as UTF-8",
                details=str(exc),
                path=display_path,
                evidence=[],
                recommended_action="Save workflow-state.yaml as UTF-8.",
            )
        )
        checks.append(Check("workflow-state-readable", "fail", "File is not UTF-8.", display_path))
        return findings, checks

    missing_fields = sorted(REQUIRED_WORKFLOW_FIELDS - set(state))
    if missing_fields:
        findings.append(
            Finding(
                id="workflow-state-missing-required-fields",
                severity="error",
                category="workflow-state",
                title="workflow-state.yaml misses required fields",
                details="The handoff state is incomplete.",
                path=display_path,
                evidence=missing_fields,
                recommended_action="Add the missing fields from references/agent/workflow-state-format.md.",
            )
        )
        checks.append(Check("workflow-state-required-fields", "fail", "Missing required fields.", display_path))
    else:
        checks.append(Check("workflow-state-required-fields", "pass", "Required fields present.", display_path))

    ft_root = find_ft_root(path, root, state)
    authoritative_cycle_state = find_authoritative_session_cycle_state(state, path, root, ft_root)
    workflow_superseded_by_session_cycle = authoritative_cycle_state is not None
    if authoritative_cycle_state is not None:
        cycle_path, cycle_state = authoritative_cycle_state
        findings.append(
            Finding(
                id="workflow-state-superseded-by-session-cycle",
                severity="info",
                category="workflow-state",
                title="workflow-state.yaml is superseded by session-based cycle-state.yaml",
                details=(
                    "A matching session-based review cycle state is newer than this workflow-state. "
                    "The validator keeps basic handoff/link checks for this file, but active routing and "
                    "ready-for-review writer gates are evaluated from cycle-state.yaml instead."
                ),
                path=display_path,
                evidence=[
                    f"cycle_state={rel(cycle_path, root)}",
                    f"cycle_stage={cycle_state.get('current_stage')}",
                    f"cycle_status={cycle_state.get('stage_status')}",
                ],
                recommended_action=(
                    "Use the matching `work/review-cycles/<scope>/cycle-state.yaml` as the process-status "
                    "source of truth for this scope."
                ),
            )
        )
        checks.append(
            Check(
                "workflow-state-session-cycle-superseded",
                "pass",
                "Matching session-based cycle-state is authoritative for active routing.",
                display_path,
            )
        )
    latest_artifacts = state.get("latest_artifacts")
    latest_artifact_values = flatten_string_values(latest_artifacts)
    required_inputs = state.get("required_inputs")
    required_input_values = flatten_string_values(required_inputs)
    scope_metrics: dict[str, int | str | None] | None = None
    loop_summary_metrics: dict[str, Any] | None = None
    loop_summary_path: Path | None = None

    if isinstance(required_inputs, list):
        missing_required_inputs = [
            item
            for item in required_inputs
            if isinstance(item, str)
            and not artifact_exists(item, path, root, ft_root)
            and item not in {Path(value).name for value in latest_artifact_values}
        ]
        if missing_required_inputs:
            findings.append(
                Finding(
                    id="workflow-state-missing-required-input-artifacts",
                    severity="error",
                    category="artifact-links",
                    title="Required input artifacts are missing",
                    details="A next stage should not start while required inputs cannot be resolved.",
                    path=display_path,
                    evidence=missing_required_inputs,
                    recommended_action="Create the missing artifacts or update required_inputs/latest_artifacts.",
                )
            )
            checks.append(Check("workflow-state-required-input-artifacts", "fail", "Missing required input artifacts.", display_path))
        else:
            checks.append(Check("workflow-state-required-input-artifacts", "pass", "Required input artifacts resolve.", display_path))

    if isinstance(latest_artifacts, dict):
        missing_latest_artifacts = [
            item
            for item in latest_artifact_values
            if not artifact_exists(item, path, root, ft_root)
        ]
        if missing_latest_artifacts:
            findings.append(
                Finding(
                    id="workflow-state-missing-latest-artifacts",
                    severity="warning",
                    category="artifact-links",
                    title="Latest artifact links do not resolve",
                    details="Some latest_artifacts paths are not present in the current checkout.",
                    path=display_path,
                    evidence=missing_latest_artifacts[:10],
                    recommended_action="Fix stale latest_artifacts paths or mark external/local artifacts explicitly.",
                )
            )
            checks.append(Check("workflow-state-latest-artifact-links", "warn", "Some latest artifact links are missing.", display_path))
        else:
            checks.append(Check("workflow-state-latest-artifact-links", "pass", "Latest artifact links resolve.", display_path))

        scope_requires_mockup_inventory = workflow_requires_mockup_visual_inventory(state, path, root, ft_root)
        if scope_requires_mockup_inventory and state.get("current_stage") in {"ft-scope-analyzer", "ft-test-case-writer"}:
            inventory_paths = workflow_mockup_visual_inventory_paths(state, path, root, ft_root)
            if not inventory_paths:
                ready_for_review = is_ready_for_review_state(state)
                findings.append(
                    Finding(
                        id=(
                            "workflow-state-ready-for-review-missing-mockup-visual-inventory"
                            if ready_for_review
                            else "workflow-state-ui-scope-missing-mockup-visual-inventory"
                        ),
                        severity="error" if ready_for_review else "warning",
                        category="mockup",
                        title="UI scope with mockup has no mockup visual inventory",
                        details=(
                            "When a confirmed UI scope includes a mockup source, downstream writer work must have a "
                            "mockup-visual-inventory.md proving that the image was opened and used only for UI interaction steps."
                        ),
                        path=display_path,
                        evidence=[*required_input_values[:10], *latest_artifact_values[:10]],
                        recommended_action=(
                            "Create and link mockup-visual-inventory.md before writer TC generation or keep the workflow blocked."
                        ),
                    )
                )
                checks.append(
                    Check(
                        "workflow-state-mockup-visual-inventory",
                        "fail" if ready_for_review else "warn",
                        "Mockup visual inventory is missing.",
                        display_path,
                    )
                )
            else:
                checks.append(
                    Check(
                        "workflow-state-mockup-visual-inventory",
                        "pass",
                        "Mockup visual inventory resolves.",
                        display_path,
                    )
                )

        final_status = workflow_final_status(state) or state.get("stage_status")
        if final_status in {"signed-off", "round-cap-reached"}:
            required_final_aliases = set(REQUIRED_FINAL_ARTIFACT_ALIASES)
            if final_status == "signed-off":
                required_final_aliases.add("signed_off_snapshot")
            if final_status == "round-cap-reached":
                required_final_aliases.add("round_cap_snapshot")
            current_round_value = get_int(state.get("current_round"))
            if current_round_value is not None and current_round_value > 1:
                required_final_aliases.add("final_writer_response")

            missing_final_aliases = sorted(required_final_aliases - set(latest_artifacts))
            if missing_final_aliases:
                final_alias_severity = "warning" if final_alias_policy == "strict" else "info"
                final_alias_check_status = "warn" if final_alias_policy == "strict" else "pass"
                findings.append(
                    Finding(
                        id="workflow-state-missing-final-artifact-aliases",
                        severity=final_alias_severity,
                        category="traceability",
                        title="Completed reviewer-loop state has no canonical final artifact aliases",
                        details=(
                            "The state resolves round-specific artifacts, but new runtime handoffs should "
                            "also expose final_* aliases for traceability closure."
                        ),
                        path=display_path,
                        evidence=missing_final_aliases,
                        recommended_action=(
                            "Add final_findings, final_traceability_matrix, final_traceability_matrix_xlsx, "
                            "loop_summary, and final_writer_response when applicable."
                        ),
                    )
                )
                checks.append(
                    Check(
                        "workflow-state-final-artifact-aliases",
                        final_alias_check_status,
                        (
                            "Completed reviewer-loop state is missing canonical final aliases."
                            if final_alias_policy == "strict"
                            else "Legacy state missing final aliases recorded as info."
                        ),
                        display_path,
                    )
                )
            else:
                checks.append(Check("workflow-state-final-artifact-aliases", "pass", "Final artifact aliases are present.", display_path))

    current_stage = state.get("current_stage")
    if current_stage not in ALLOWED_CURRENT_STAGES:
        findings.append(
            Finding(
                id="workflow-state-invalid-current-stage",
                severity="error",
                category="workflow-state",
                title="Invalid current_stage",
                details=f"Unsupported current_stage: {current_stage!r}",
                path=display_path,
                evidence=[str(current_stage)],
                recommended_action="Use one of the canonical current_stage values.",
            )
        )

    stage_status = state.get("stage_status")
    if stage_status not in ALLOWED_STAGE_STATUSES:
        findings.append(
            Finding(
                id="workflow-state-invalid-stage-status",
                severity="error",
                category="workflow-state",
                title="Invalid stage_status",
                details=f"Unsupported stage_status: {stage_status!r}",
                path=display_path,
                evidence=[str(stage_status)],
                recommended_action=(
                    "Use one of the canonical stage_status values. For a not-signed-off reviewer verdict, "
                    "use `ready-for-writer-revision`; use `round-cap-reached` only after the review round cap, "
                    "or `blocked-input` when external input is required."
                ),
            )
        )

    next_skill = state.get("next_skill")
    if next_skill not in ALLOWED_NEXT_SKILLS:
        findings.append(
            Finding(
                id="workflow-state-invalid-next-skill",
                severity="error",
                category="workflow-state",
                title="Invalid next_skill",
                details=f"Unsupported next_skill: {next_skill!r}",
                path=display_path,
                evidence=[str(next_skill)],
                recommended_action="Use a canonical skill name, `none`, or `null`.",
            )
        )

    linked_source_selection_paths = dedupe_paths(
        [
            resolved
            for value in [*required_input_values, *latest_artifact_values]
            if Path(strip_quotes(value)).name == "source-selection.md"
            for resolved in [resolve_artifact_path(value, path, root, ft_root)]
            if resolved is not None
        ]
    )
    for source_selection_path in linked_source_selection_paths:
        source_selection_findings, source_selection_checks = validate_source_selection_artifact(
            source_selection_path,
            root,
            state,
            path,
        )
        findings.extend(source_selection_findings)
        checks.extend(source_selection_checks)

    linked_source_row_inventory_paths = dedupe_paths(
        [
            resolved
            for value in [*required_input_values, *latest_artifact_values]
            if Path(strip_quotes(value)).name == "source-row-inventory.md"
            for resolved in [resolve_artifact_path(value, path, root, ft_root)]
            if resolved is not None
        ]
    )
    for source_row_inventory_path in linked_source_row_inventory_paths:
        try:
            source_row_inventory_content = source_row_inventory_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            findings.append(
                Finding(
                    id="source-row-inventory-unreadable",
                    severity="warning",
                    category="traceability",
                    title="source-row-inventory.md is not readable as UTF-8",
                    details=str(exc),
                    path=rel(source_row_inventory_path, root),
                    evidence=[],
                    recommended_action="Save source-row-inventory.md as UTF-8.",
                )
            )
            checks.append(Check("source-row-inventory-handoff", "warn", "source-row-inventory.md is not UTF-8.", rel(source_row_inventory_path, root)))
            continue
        normalized_inventory_content = source_row_inventory_content
        if re.search(r"^#\s+Source Row Inventory\s*$", normalized_inventory_content, flags=re.MULTILINE):
            normalized_inventory_content = re.sub(
                r"^#\s+Source Row Inventory\s*$",
                "## Source Row Inventory",
                normalized_inventory_content,
                count=1,
                flags=re.MULTILINE,
            )
        elif extract_markdown_section(normalized_inventory_content, "Source Row Inventory") is None:
            normalized_inventory_content = "## Source Row Inventory\n\n" + normalized_inventory_content

        inventory_findings, inventory_checks = validate_source_row_inventory(
            normalized_inventory_content,
            source_row_inventory_path,
            root,
        )
        findings.extend(inventory_findings)
        checks.extend(inventory_checks)

    scope_analyzer_ready_state = (
        current_stage == "ft-scope-analyzer"
        and stage_status in {"ready-for-gap-review", "ready-for-next-stage"}
        and next_skill in {"ft-test-case-reviewer", "ft-test-case-writer", "ft-test-case-iteration"}
    )
    if scope_analyzer_ready_state:
        oracle_requirements = [
            (
                NEGATIVE_ORACLE_INVENTORY_NAME,
                "workflow-state-scope-analyzer-missing-negative-oracle-inventory",
                "Negative oracle inventory is required for validation restrictions",
                (
                    "Scope analysis found validation/format/date/email/length/numeric/allowed-values signals. "
                    "Before routing downstream, it must decide whether each invalid class has an observable oracle "
                    "or must become a GAP/clarification."
                ),
                scope_oracle_signal_evidence(state, path, root, ft_root, NEGATIVE_ORACLE_SCOPE_RE),
            ),
            (
                REQUIREDNESS_ORACLE_INVENTORY_NAME,
                "workflow-state-scope-analyzer-missing-requiredness-oracle-inventory",
                "Requiredness oracle inventory is required for mandatory fields",
                (
                    "Scope analysis found requiredness/mandatory-field signals. Before routing downstream, it must "
                    "decide whether requiredness is testable through a visible marker or empty-value validation oracle, "
                    "or must become a GAP/clarification."
                ),
                scope_oracle_signal_evidence(state, path, root, ft_root, REQUIREDNESS_ORACLE_SCOPE_RE),
            ),
        ]

        for inventory_name, finding_id, title, details, signal_evidence in oracle_requirements:
            check_name = finding_id.replace("workflow-state-", "")
            if not signal_evidence:
                checks.append(Check(check_name, "pass", f"{inventory_name} not required by scope signals.", display_path))
                continue

            inventory_paths = workflow_artifact_paths_by_name(state, path, root, ft_root, inventory_name)
            if not inventory_paths:
                findings.append(
                    Finding(
                        id=finding_id,
                        severity="error",
                        category="artifact-links",
                        title=title,
                        details=details,
                        path=display_path,
                        evidence=signal_evidence[:10],
                        recommended_action=(
                            f"Create/link `{inventory_name}` in required_inputs/latest_artifacts, or keep the "
                            "scope workflow blocked until oracle/gap handling is explicit."
                        ),
                    )
                )
                checks.append(Check(check_name, "fail", f"{inventory_name} is missing.", display_path))
                continue

            inventory_errors: list[str] = []
            for inventory_path in inventory_paths:
                try:
                    summary = oracle_inventory_summary(inventory_path)
                except UnicodeDecodeError:
                    inventory_errors.append(f"{rel(inventory_path, root)}:not-utf8")
                    continue
                if not summary["has_table"]:
                    inventory_errors.append(f"{rel(inventory_path, root)}:no parseable table")
                elif summary["row_count"] == 0:
                    inventory_errors.append(f"{rel(inventory_path, root)}:no child obligation rows")
                if summary["missing_columns"]:
                    inventory_errors.append(
                        f"{rel(inventory_path, root)}:missing columns {', '.join(summary['missing_columns'][:8])}"
                    )
                if summary["invalid_rows"]:
                    inventory_errors.extend(
                        f"{rel(inventory_path, root)}:{error}"
                        for error in summary["invalid_rows"][:8]
                    )
                if summary["gap_rows_without_gap"]:
                    inventory_errors.extend(
                        f"{rel(inventory_path, root)}:{error}"
                        for error in summary["gap_rows_without_gap"][:8]
                    )

            if inventory_errors:
                findings.append(
                    Finding(
                        id=finding_id.replace("missing", "invalid"),
                        severity="error",
                        category="artifact-format",
                        title=f"{inventory_name} is incomplete",
                        details=(
                            "Scope-level oracle inventories must use the canonical columns and every "
                            "`candidate_tc_required` row must use `oracle_status = ui-calibration-required`; "
                            "`gap_required` / `clarification_required` rows must link a real GAP-*."
                        ),
                        path=display_path,
                        evidence=inventory_errors[:12],
                        recommended_action=f"Rewrite `{inventory_name}` using the canonical reference format.",
                    )
                )
                checks.append(Check(check_name.replace("missing", "invalid"), "fail", f"{inventory_name} is invalid.", display_path))
            else:
                checks.append(Check(check_name, "pass", f"{inventory_name} resolves and has required shape.", display_path))

    if current_stage == "ft-source-locator":
        if not linked_source_selection_paths:
            findings.append(
                Finding(
                    id="workflow-state-source-locator-missing-source-selection",
                    severity="error",
                    category="artifact-links",
                    title="Source locator workflow does not link source-selection.md",
                    details=(
                        "`ft-source-locator` must produce and link `source-selection.md`; otherwise the package/source "
                        "choice is not reproducible for `ft-scope-analyzer`."
                    ),
                    path=display_path,
                    evidence=[*required_input_values[:10], *latest_artifact_values[:10]],
                    recommended_action=(
                        "Create `source-selection.md` in the current handoff folder and link it from "
                        "`latest_artifacts.source_selection` and/or `required_inputs`."
                    ),
                )
            )
            checks.append(Check("workflow-state-source-selection", "fail", "source-selection.md is not linked.", display_path))
        else:
            checks.append(Check("workflow-state-source-selection", "pass", "source-selection.md resolves.", display_path))

        premature_names = {"scope-contract.md", "prompt.scope-to-writer.md", "prompt.scope-to-iteration.md"}
        premature_paths: list[str] = []
        for value in [*required_input_values, *latest_artifact_values]:
            name = Path(strip_quotes(value)).name
            if name not in premature_names:
                continue
            resolved = resolve_artifact_path(value, path, root, ft_root)
            premature_paths.append(rel(resolved, root) if resolved is not None else value)
        for name in sorted(premature_names):
            candidate = path.parent / name
            if candidate.exists():
                premature_paths.append(rel(candidate, root))
        premature_paths = sorted(set(premature_paths))
        if premature_paths:
            findings.append(
                Finding(
                    id="workflow-state-source-locator-premature-scope-artifacts",
                    severity="error",
                    category="skill-boundary",
                    title="Source locator handoff contains scope-stage artifacts",
                    details=(
                        "`ft-source-locator` selects sources only. `scope-contract.md` and scope-to-writer/iteration "
                        "prompts belong to `ft-scope-analyzer` after scope selection."
                    ),
                    path=display_path,
                    evidence=premature_paths[:10],
                    recommended_action=(
                        "Remove premature scope artifacts from the source-locator handoff or move the workflow to the "
                        "appropriate `ft-scope-analyzer` stage."
                    ),
                )
            )
            checks.append(Check("workflow-state-source-locator-boundary", "fail", "Premature scope artifacts found.", display_path))
        else:
            checks.append(Check("workflow-state-source-locator-boundary", "pass", "No premature scope artifacts found.", display_path))

    if (
        current_stage == "ft-scope-analyzer"
        and stage_status == "ready-for-gap-review"
        and next_skill == "ft-test-case-reviewer"
    ):
        scope_handoff_values = [*required_input_values, *latest_artifact_values]
        required_scope_gap_review_names = {
            "source-selection.md",
            "scope-contract.md",
            "scope-coverage-gaps.md",
            "scope-clarification-requests.md",
            "prompt.scope-gaps-to-reviewer.md",
        }
        missing_scope_gap_review_names = [
            name
            for name in sorted(required_scope_gap_review_names)
            if resolving_artifact_by_name(name, scope_handoff_values, path, root, ft_root) is None
        ]
        if missing_scope_gap_review_names:
            findings.append(
                Finding(
                    id="workflow-state-scope-gap-review-missing-handoff-artifacts",
                    severity="error",
                    category="artifact-links",
                    title="Scope gap review handoff misses required artifacts",
                    details=(
                        "`ready-for-gap-review` cannot route to reviewer without resolving scope, gap, "
                        "clarification and scope-gaps-to-reviewer prompt artifacts."
                    ),
                    path=display_path,
                    evidence=missing_scope_gap_review_names,
                    recommended_action=(
                        "Create/link the missing artifacts or keep the workflow blocked until scope gaps are ready "
                        "for independent review."
                    ),
                )
            )
            checks.append(Check("workflow-state-scope-gap-review-handoff-artifacts", "fail", "Required scope gap review artifacts are missing.", display_path))
        else:
            checks.append(Check("workflow-state-scope-gap-review-handoff-artifacts", "pass", "Required scope gap review artifacts resolve.", display_path))

        scope_gaps_path = resolving_artifact_by_name(
            "scope-coverage-gaps.md",
            scope_handoff_values,
            path,
            root,
            ft_root,
        )
        if scope_gaps_path is not None:
            try:
                scope_gap_total = get_int(extract_scope_coverage_metrics(scope_gaps_path).get("total")) or 0
            except UnicodeDecodeError:
                scope_gap_total = 0
            if scope_gap_total <= 0:
                findings.append(
                    Finding(
                        id="workflow-state-ready-for-gap-review-without-gaps",
                        severity="error",
                        category="stage-transition",
                        title="ready-for-gap-review has no GAP-* items",
                        details=(
                            "`ready-for-gap-review` is only valid when `scope-coverage-gaps.md` contains at least "
                            "one concrete `GAP-*` item."
                        ),
                        path=display_path,
                        evidence=[f"scope_gaps={rel(scope_gaps_path, root)}", f"gap_count={scope_gap_total}"],
                        recommended_action=(
                            "Route directly to writer with `ready-for-next-stage`, or add the missing concrete "
                            "gap entries if the scope really has unresolved coverage gaps."
                        ),
                    )
                )
                checks.append(Check("workflow-state-scope-gap-review-gap-count", "fail", "No concrete GAP-* entries found.", display_path))
            else:
                checks.append(Check("workflow-state-scope-gap-review-gap-count", "pass", "Concrete GAP-* entries found.", display_path))

        source_parity_path = resolving_artifact_by_name(
            "source-parity-check.md",
            scope_handoff_values,
            path,
            root,
            ft_root,
        )
        if (
            source_parity_path is not None
            and source_parity_requires_source_row_inventory(source_parity_path)
            and resolving_artifact_by_name("source-row-inventory.md", scope_handoff_values, path, root, ft_root) is None
        ):
            findings.append(
                Finding(
                    id="workflow-state-scope-gap-review-missing-source-row-inventory",
                    severity="error",
                    category="artifact-links",
                    title="Scope gap review lacks required source row inventory",
                    details=(
                        "`source-parity-check.md` contains `Table / Row Parity`, so the gap reviewer needs "
                        "`source-row-inventory.md` before checking row-level gap completeness."
                    ),
                    path=display_path,
                    evidence=[rel(source_parity_path, root)],
                    recommended_action="Create and link `source-row-inventory.md`, or keep the workflow blocked.",
                )
            )
            checks.append(Check("workflow-state-scope-gap-review-source-row-inventory", "fail", "Row-level source inventory handoff is missing.", display_path))
        else:
            checks.append(Check("workflow-state-scope-gap-review-source-row-inventory", "pass", "Row-level source inventory handoff is present or not required.", display_path))

    if (
        current_stage == "ft-scope-analyzer"
        and stage_status == "ready-for-next-stage"
        and next_skill in {"ft-test-case-writer", "ft-test-case-iteration"}
    ):
        scope_handoff_values = [*required_input_values, *latest_artifact_values]
        required_scope_handoff_names = {
            "source-selection.md",
            "scope-contract.md",
            "scope-coverage-gaps.md",
        }
        required_scope_handoff_names.add(
            "prompt.scope-to-writer.md"
            if next_skill == "ft-test-case-writer"
            else "prompt.scope-to-iteration.md"
        )

        missing_scope_handoff_names = [
            name
            for name in sorted(required_scope_handoff_names)
            if resolving_artifact_by_name(name, scope_handoff_values, path, root, ft_root) is None
        ]
        if missing_scope_handoff_names:
            findings.append(
                Finding(
                    id="workflow-state-scope-analyzer-missing-handoff-artifacts",
                    severity="error",
                    category="artifact-links",
                    title="Scope analyzer ready handoff misses required artifacts",
                    details=(
                        "`ft-scope-analyzer` cannot route to writer/iteration without a resolving scope contract, "
                        "coverage-gaps artifact, and the matching scope-to-* prompt."
                    ),
                    path=display_path,
                    evidence=missing_scope_handoff_names,
                    recommended_action=(
                        "Create and link the missing scope handoff artifacts from required_inputs/latest_artifacts, "
                        "or keep the workflow blocked."
                    ),
                )
            )
            checks.append(Check("workflow-state-scope-analyzer-handoff-artifacts", "fail", "Required scope handoff artifacts are missing.", display_path))
        else:
            checks.append(Check("workflow-state-scope-analyzer-handoff-artifacts", "pass", "Required scope handoff artifacts resolve.", display_path))

        scope_gaps_path = resolving_artifact_by_name(
            "scope-coverage-gaps.md",
            scope_handoff_values,
            path,
            root,
            ft_root,
        )
        if scope_gaps_path is not None:
            try:
                scope_gap_total = get_int(extract_scope_coverage_metrics(scope_gaps_path).get("total")) or 0
            except UnicodeDecodeError:
                scope_gap_total = 0
            if scope_gap_total > 0 and resolving_artifact_by_name(
                "scope-clarification-requests.md",
                scope_handoff_values,
                path,
                root,
                ft_root,
            ) is None:
                findings.append(
                    Finding(
                        id="workflow-state-scope-analyzer-missing-clarification-requests",
                        severity="error",
                        category="artifact-links",
                        title="Scope gaps have no clarification request artifact",
                        details=(
                            "`scope-coverage-gaps.md` lists GAP-* items, so the scope handoff must include "
                            "`scope-clarification-requests.md` before downstream writer/iteration work."
                        ),
                        path=display_path,
                        evidence=[f"scope_gaps={rel(scope_gaps_path, root)}", f"gap_count={scope_gap_total}"],
                        recommended_action=(
                            "Create/link scope-clarification-requests.md or keep the workflow blocked until gap handling is explicit."
                        ),
                    )
                )
                checks.append(Check("workflow-state-scope-clarification-requests", "fail", "Scope gaps lack clarification requests.", display_path))
            else:
                checks.append(Check("workflow-state-scope-clarification-requests", "pass", "Scope gap clarification handoff is explicit or not needed.", display_path))

        source_parity_path = resolving_artifact_by_name(
            "source-parity-check.md",
            scope_handoff_values,
            path,
            root,
            ft_root,
        )
        if (
            source_parity_path is not None
            and source_parity_requires_source_row_inventory(source_parity_path)
            and resolving_artifact_by_name("source-row-inventory.md", scope_handoff_values, path, root, ft_root) is None
        ):
            findings.append(
                Finding(
                    id="workflow-state-scope-analyzer-missing-source-row-inventory",
                    severity="error",
                    category="artifact-links",
                    title="Row-level source parity has no source row inventory handoff",
                    details=(
                        "`source-parity-check.md` contains `Table / Row Parity`, so writer needs an independent "
                        "`source-row-inventory.md` from scope-analyzer before normalization and ledger creation."
                    ),
                    path=display_path,
                    evidence=[rel(source_parity_path, root)],
                    recommended_action=(
                        "Create and link `source-row-inventory.md`, or keep the workflow blocked until source rows "
                        "are inventoried independently of writer output."
                    ),
                )
            )
            checks.append(Check("workflow-state-scope-source-row-inventory", "fail", "Row-level source inventory handoff is missing.", display_path))
        else:
            checks.append(Check("workflow-state-scope-source-row-inventory", "pass", "Row-level source inventory handoff is present or not required.", display_path))

    coverage_gaps = state.get("coverage_gaps")
    blocking_gaps = None
    if isinstance(coverage_gaps, dict):
        blocking_gaps = get_int(coverage_gaps.get("blocking"))
    accepted_gap_ids = accepted_risk_gap_ids(state)
    accepted_risks_qualified = accepted_risk_entries_are_qualified(state)

    scope_coverage_values = [
        value
        for value in latest_artifact_values
        if Path(value).name == "scope-coverage-gaps.md" and artifact_exists(value, path, root, ft_root)
    ]
    for scope_coverage_value in scope_coverage_values[:1]:
        scope_path = next(
            candidate
            for candidate in candidate_artifact_paths(scope_coverage_value, path, root, ft_root)
            if candidate.exists()
        )
        scope_metrics = extract_scope_coverage_metrics(scope_path)
        scope_blocking_gap_ids = scope_metrics.get("blocking_gap_ids")
        if is_signed_off_state(state) and scope_metrics["blocking_gaps"] == "yes":
            scope_blocking_count = get_int(scope_metrics.get("impact_blocking")) or get_int(scope_metrics.get("total")) or 1
            findings.append(
                Finding(
                    id="workflow-state-signed-off-with-scope-blocking-gaps",
                    severity="error",
                    category="status-model",
                    title="signed-off conflicts with scope blocking gaps",
                    details=(
                        "`scope-coverage-gaps.md` declares blocking gaps, so the handoff "
                        "must not be treated as a signed-off downstream baseline."
                    ),
                    path=display_path,
                    evidence=[
                        f"scope-coverage-gaps blocking=yes",
                        f"blocking impacts={scope_blocking_count}",
                    ],
                    recommended_action=(
                        "Downgrade the handoff to `round-cap-reached` or resolve the "
                        "blocking scope gaps before downstream use."
                    ),
                )
            )
        if (
            is_ready_for_review_state(state)
            and not workflow_superseded_by_session_cycle
            and scope_metrics["blocking_gaps"] == "yes"
        ):
            scope_blocking_count = get_int(scope_metrics.get("impact_blocking")) or get_int(scope_metrics.get("total")) or 1
            missing_scope_accepted_risks: list[str] = []
            if isinstance(scope_blocking_gap_ids, list) and scope_blocking_gap_ids:
                missing_scope_accepted_risks = sorted(set(scope_blocking_gap_ids) - accepted_gap_ids)
            elif len(accepted_gap_ids) < scope_blocking_count:
                missing_scope_accepted_risks = [f"blocking_count={scope_blocking_count}; accepted_risks={len(accepted_gap_ids)}"]
            if missing_scope_accepted_risks or not accepted_risks_qualified:
                findings.append(
                    Finding(
                        id="workflow-state-ready-for-review-with-scope-blocking-gaps",
                        severity="error",
                        category="status-model",
                        title="ready-for-review conflicts with scope blocking gaps",
                        details=(
                            "`scope-coverage-gaps.md` declares blocking gaps. A writer handoff cannot be ready for review "
                            "unless each blocking GAP-* is resolved, moved to blocked-input, or explicitly accepted as risk."
                        ),
                        path=display_path,
                        evidence=[
                            "scope-coverage-gaps blocking=yes",
                            *missing_scope_accepted_risks[:10],
                        ],
                        recommended_action=(
                            "Set `stage_status: blocked-input`, resolve the blocking gaps, or add qualified `accepted_risks` "
                            "entries with GAP id, owner, rationale and revisit condition."
                        ),
                    )
                )

    if is_signed_off_state(state) and blocking_gaps and blocking_gaps > 0:
        findings.append(
            Finding(
                id="workflow-state-signed-off-with-blocking-gaps",
                severity="error",
                category="status-model",
                title="signed-off conflicts with blocking coverage gaps",
                details=(
                    "`signed-off` must not be treated as fully ready while "
                    "`coverage_gaps.blocking` is greater than zero."
                ),
                path=display_path,
                evidence=[f"coverage_gaps.blocking={blocking_gaps}"],
                recommended_action=(
                    "Downgrade the handoff state or add an explicit qualified status "
                    "before downstream use."
                ),
            )
        )
        checks.append(Check("workflow-state-signed-off-gate", "fail", "signed-off has blocking gaps.", display_path))
    else:
        checks.append(Check("workflow-state-signed-off-gate", "pass", "No signed-off blocking-gap conflict.", display_path))

    if (
        is_ready_for_review_state(state)
        and not workflow_superseded_by_session_cycle
        and blocking_gaps
        and blocking_gaps > 0
    ):
        if len(accepted_gap_ids) < blocking_gaps or not accepted_risks_qualified:
            findings.append(
                Finding(
                    id="workflow-state-ready-for-review-with-blocking-gaps",
                    severity="error",
                    category="status-model",
                    title="ready-for-review conflicts with blocking coverage gaps",
                    details=(
                        "`ready-for-review` must not be used while `coverage_gaps.blocking` is greater than zero "
                        "unless the blocking gaps are explicitly accepted as residual risk."
                    ),
                    path=display_path,
                    evidence=[
                        f"coverage_gaps.blocking={blocking_gaps}",
                        f"accepted_risks={len(accepted_gap_ids)}",
                    ],
                    recommended_action=(
                        "Set `stage_status: blocked-input`, resolve blocking gaps, or add qualified `accepted_risks` "
                        "entries with GAP id, owner, rationale and revisit condition."
                    ),
                )
            )
            checks.append(Check("workflow-state-ready-for-review-gap-gate", "fail", "ready-for-review has unaccepted blocking gaps.", display_path))
        else:
            checks.append(Check("workflow-state-ready-for-review-gap-gate", "pass", "Blocking gaps are explicitly accepted as residual risk.", display_path))

    if (
        current_stage == "ft-test-case-writer"
        and is_ready_for_review_state(state)
        and not workflow_superseded_by_session_cycle
    ):
        test_case_artifacts = resolve_workflow_test_case_artifacts(state, path, root, ft_root)
        writer_process_diagnostics = resolve_workflow_writer_process_diagnostics(state, path, root, ft_root)
        writer_process_statuses = [
            (diagnostic_path, writer_process_diagnostic_status(diagnostic_path))
            for diagnostic_path in writer_process_diagnostics
        ]
        active_writer_process_statuses = [
            (diagnostic_path, diagnostic_status)
            for diagnostic_path, diagnostic_status in writer_process_statuses
            if diagnostic_status.get("is_active")
        ]
        writer_process_errors: list[str] = []
        if writer_process_statuses and not active_writer_process_statuses:
            writer_process_errors.append("no active writer-process diagnostic for current workflow")
        if len(active_writer_process_statuses) > 1:
            writer_process_errors.extend(
                f"multiple active diagnostics: {rel(diagnostic_path, root)}"
                for diagnostic_path, _ in active_writer_process_statuses[:10]
            )
        for diagnostic_path, diagnostic_status in active_writer_process_statuses:
            fields = diagnostic_status.get("fields", {})
            if not diagnostic_status.get("active_known"):
                writer_process_errors.append(
                    f"{rel(diagnostic_path, root)}:active_for_current_workflow={fields.get('active_for_current_workflow', '-')}"
                )
            if diagnostic_status.get("blocking"):
                writer_process_errors.append(
                    (
                        f"{rel(diagnostic_path, root)}:"
                        f"verdict={fields.get('verdict', '-')};"
                        f"process_readiness={fields.get('process_readiness', '-')};"
                        f"validator_gap_suspected={fields.get('validator_gap_suspected', '-')}"
                    )
                )
            if test_case_artifacts and not diagnostic_target_matches_test_case_artifacts(
                str(fields.get("diagnostic_target", "")),
                test_case_artifacts=test_case_artifacts,
                workflow_path=path,
                root=root,
                ft_root=ft_root,
            ):
                writer_process_errors.append(
                    (
                        f"{rel(diagnostic_path, root)}:diagnostic_target="
                        f"{fields.get('diagnostic_target', '-')};active_test_cases="
                        f"{', '.join(rel(test_case_artifact, root) for test_case_artifact in test_case_artifacts[:5])}"
                    )
                )
        if writer_process_errors:
            findings.append(
                Finding(
                    id="workflow-state-ready-for-review-with-contaminated-writer-process",
                    severity="error",
                    category="status-model",
                    title="ready-for-review conflicts with writer process diagnostic",
                    details=(
                        "A writer handoff cannot be routed to reviewer unless exactly one active "
                        "writer-process-diagnostic*.md applies to the active canonical test-case file and reports a "
                        "clean/pass process without a suspected validator gap. Historical diagnostics must be marked "
                        "`active_for_current_workflow: no` and must not be used as active evidence."
                    ),
                    path=display_path,
                    evidence=writer_process_errors[:15],
                    recommended_action=(
                        "Set `stage_status: blocked-input`, rerun the writer from a clean file-based strategy, "
                        "or link exactly one passing active writer-process diagnostic whose diagnostic_target matches "
                        "the active canonical test-case file."
                    ),
                )
            )
            checks.append(
                Check(
                    "workflow-state-ready-for-review-writer-process",
                    "fail",
                    "Writer process diagnostic blocks ready-for-review.",
                    display_path,
                )
            )
        elif writer_process_statuses:
            checks.append(
                Check(
                    "workflow-state-ready-for-review-writer-process",
                    "pass",
                    "Exactly one active writer process diagnostic matches the ready-for-review artifact.",
                    display_path,
                )
            )
        else:
            checks.append(
                Check(
                    "workflow-state-ready-for-review-writer-process",
                    "pass",
                    "No writer process diagnostics found for this legacy ready-for-review handoff.",
                    display_path,
                )
            )

        if not test_case_artifacts:
            findings.append(
                Finding(
                    id="workflow-state-ready-for-review-missing-test-case-artifact",
                    severity="error",
                    category="status-model",
                    title="ready-for-review has no resolving canonical test-case artifact",
                    details="Writer handoff must expose the canonical test-case file that reviewer is expected to review.",
                    path=display_path,
                    evidence=[*required_input_values[:10], *latest_artifact_values[:10]],
                    recommended_action="Add the canonical test-case markdown file to required_inputs/latest_artifacts before setting ready-for-review.",
                )
            )
            checks.append(Check("workflow-state-ready-for-review-writer-quality-gate", "fail", "No test-case artifact resolves.", display_path))
        else:
            handoff_source_row_ids: set[str] = set()
            handoff_read_errors: list[str] = []
            for source_row_inventory_path in linked_source_row_inventory_paths:
                try:
                    handoff_source_row_ids.update(
                        source_row_inventory_required_source_ids(
                            source_row_inventory_path.read_text(encoding="utf-8")
                        )
                    )
                except UnicodeDecodeError:
                    handoff_read_errors.append(f"{rel(source_row_inventory_path, root)}:not-utf8")

            if handoff_source_row_ids:
                writer_source_row_ids: set[str] = set()
                writer_read_errors: list[str] = []
                for test_case_artifact in test_case_artifacts:
                    try:
                        writer_source_row_ids.update(
                            source_row_inventory_all_source_ids(
                                test_case_validation_content(test_case_artifact, root)
                            )
                        )
                    except UnicodeDecodeError:
                        writer_read_errors.append(f"{rel(test_case_artifact, root)}:not-utf8")
                missing_handoff_rows = sorted(handoff_source_row_ids - writer_source_row_ids)
                if missing_handoff_rows or handoff_read_errors or writer_read_errors:
                    findings.append(
                        Finding(
                            id="workflow-state-ready-for-review-missing-handoff-source-rows",
                            severity="error",
                            category="traceability",
                            title="Writer output lost source rows from handoff inventory",
                            details=(
                                "`source-row-inventory.md` is an independent handoff from scope analysis. "
                                "Writer cannot be ready for review if its canonical Source Row Inventory drops "
                                "in-scope or unclear rows from that handoff."
                            ),
                            path=display_path,
                            evidence=[
                                *[f"missing={source_row_id}" for source_row_id in missing_handoff_rows[:20]],
                                *handoff_read_errors[:5],
                                *writer_read_errors[:5],
                            ],
                            recommended_action=(
                                "Copy every in-scope/unclear source_row_id from handoff `source-row-inventory.md` "
                                "into the canonical Source Row Inventory and map it to ATOM-* or GAP-* before "
                                "setting ready-for-review."
                            ),
                        )
                    )
                    checks.append(
                        Check(
                            "workflow-state-ready-for-review-source-row-inventory-carryover",
                            "fail",
                            "Writer output dropped source rows from handoff inventory.",
                            display_path,
                        )
                    )
                else:
                    checks.append(
                        Check(
                            "workflow-state-ready-for-review-source-row-inventory-carryover",
                            "pass",
                            "Writer output preserves handoff source-row inventory ids.",
                            display_path,
                        )
                    )

            gate_errors: list[str] = []
            blocking_quality_errors: list[str] = []
            for test_case_artifact in test_case_artifacts:
                try:
                    test_case_content = test_case_validation_content(test_case_artifact, root)
                except UnicodeDecodeError:
                    gate_errors.append(f"{rel(test_case_artifact, root)}:not-utf8")
                    continue
                gate_summary = writer_quality_gate_summary(test_case_content)
                artifact_label = rel(test_case_artifact, root)
                blocking_findings = ready_for_review_blocking_test_case_findings(test_case_artifact, root)
                for blocking_finding in blocking_findings:
                    evidence = "; ".join(blocking_finding.evidence[:2]) if blocking_finding.evidence else "-"
                    blocking_quality_errors.append(f"{artifact_label}:{blocking_finding.id}:{evidence[:180]}")
                if not gate_summary["present"]:
                    gate_errors.append(f"{artifact_label}:missing Writer Quality Gate")
                    continue
                if not gate_summary["parseable"]:
                    gate_errors.append(f"{artifact_label}:Writer Quality Gate has no parseable table")
                if gate_summary["missing_columns"]:
                    gate_errors.append(
                        f"{artifact_label}:missing columns {', '.join(gate_summary['missing_columns'][:8])}"
                    )
                if gate_summary["missing_items"]:
                    gate_errors.append(
                        f"{artifact_label}:missing items {', '.join(gate_summary['missing_items'][:8])}"
                    )
                if gate_summary["invalid_status_rows"]:
                    gate_errors.append(f"{artifact_label}:invalid status values")
                if gate_summary["invalid_blocks_rows"]:
                    gate_errors.append(f"{artifact_label}:invalid blocks_ready_for_review values")
                if gate_summary["failed_rows"]:
                    gate_errors.append(f"{artifact_label}:failed gate rows {', '.join(gate_summary['failed_rows'][:5])}")
                if gate_summary["known_risk_not_blocking"]:
                    gate_errors.append(f"{artifact_label}:known merged-check risk is not blocking")

            if gate_errors:
                findings.append(
                    Finding(
                        id="workflow-state-ready-for-review-without-passing-writer-quality-gate",
                        severity="error",
                        category="status-model",
                        title="ready-for-review conflicts with Writer Quality Gate",
                        details=(
                            "Writer handoff cannot be ready for reviewer unless each canonical test-case file has "
                            "a complete passing Writer Quality Gate."
                        ),
                        path=display_path,
                        evidence=gate_errors[:20],
                        recommended_action=(
                            "Rewrite affected packages, complete the Writer Quality Gate, or set stage_status to "
                            "blocked-input instead of ready-for-review."
                        ),
                    )
                )
                checks.append(Check("workflow-state-ready-for-review-writer-quality-gate", "fail", "Writer Quality Gate failed.", display_path))
            else:
                checks.append(Check("workflow-state-ready-for-review-writer-quality-gate", "pass", "Writer Quality Gate passed for ready-for-review.", display_path))

            if blocking_quality_errors:
                findings.append(
                    Finding(
                        id="workflow-state-ready-for-review-with-blocking-test-case-smells",
                        severity="error",
                        category="test-design",
                        title="ready-for-review conflicts with blocking test-case quality smells",
                        details=(
                            "Writer handoff cannot be routed to reviewer while canonical test-case artifacts still "
                            "contain known blocking smells such as generic executable steps, merged checks, "
                            "compressed atoms, source-row loss, unobservable actions or contradictory TC type/oracle."
                        ),
                        path=display_path,
                        evidence=blocking_quality_errors[:20],
                        recommended_action=(
                            "Rewrite the affected package(s) from source inventory/normalization through ledger, "
                            "Package Test Design Plan and TC, or set stage_status to blocked-input instead of "
                            "ready-for-review."
                        ),
                    )
                )
                checks.append(
                    Check(
                        "workflow-state-ready-for-review-test-case-quality",
                        "fail",
                        "Blocking test-case quality smells found in ready-for-review artifact.",
                        display_path,
                    )
                )
            else:
                checks.append(
                    Check(
                        "workflow-state-ready-for-review-test-case-quality",
                        "pass",
                        "No blocking test-case quality smells found for ready-for-review.",
                        display_path,
                    )
                )

    if state.get("stage_status") == "blocked-input":
        blocking_reasons = state.get("blocking_reasons")
        if not isinstance(blocking_reasons, list) or not blocking_reasons:
            findings.append(
                Finding(
                    id="workflow-state-blocked-without-reasons",
                    severity="error",
                    category="workflow-state",
                    title="blocked-input state has no blocking reasons",
                    details="Blocked handoffs must explain why the pipeline cannot proceed.",
                    path=display_path,
                    evidence=[],
                    recommended_action="Populate blocking_reasons with concrete blockers.",
                )
            )
        elif "writer" in str(current_stage or ""):
            validator_not_run_reasons = [
                str(reason)
                for reason in blocking_reasons
                if any(
                    pattern in str(reason).lower().replace("-", " ")
                    for pattern in (
                        "validator not run",
                        "validator has not been run",
                        "validator not executed",
                        "validator was not run",
                        "scoped validator not run",
                        "scoped validator has not been run",
                    )
                )
            ]
            if validator_not_run_reasons:
                findings.append(
                    Finding(
                        id="workflow-state-blocked-input-validator-not-run",
                        severity="error",
                        category="workflow-state",
                        title="writer blocked-input skips required post-write validator",
                        details=(
                            "A writer terminal blocked-input state may contain unresolved validator findings, "
                            "but it must not use blocked-input merely because the scoped validator was not run."
                        ),
                        path=display_path,
                        evidence=validator_not_run_reasons[:5],
                        recommended_action=(
                            "Run the scoped validator after final artifact write and record the command/evidence, "
                            "or record a concrete validator execution failure with attempted command and stderr."
                        ),
                    )
                )

    if current_stage in SESSION_LOG_REQUIRED_STAGES:
        session_log_paths = resolve_workflow_session_logs(state, path, root, ft_root)
        session_log_severity = "warning" if session_log_policy == "strict" else "info"
        session_log_check_status = "warn" if session_log_policy == "strict" else "pass"
        if not session_log_paths:
            findings.append(
                Finding(
                    id="workflow-state-missing-session-log",
                    severity=session_log_severity,
                    category="session-log",
                    title="Workflow state does not link a stage session log",
                    details=(
                        "Source locator, scope analyzer, writer, reviewer and iteration stages should persist a decision/audit "
                        "session log so later analysis does not depend on chat history."
                    ),
                    path=display_path,
                    evidence=[f"current_stage={current_stage}", f"stage_status={stage_status}"],
                    recommended_action=(
                        "Create `<stage>-session-log.md` in the current handoff folder and link it from "
                        "`latest_artifacts` as `session_log` or `<stage>_session_log`."
                    ),
                )
            )
            checks.append(
                Check(
                    "workflow-state-session-log",
                    session_log_check_status,
                    "Stage session log is not linked.",
                    display_path,
                )
            )
        else:
            checks.append(Check("workflow-state-session-log", "pass", "Stage session log resolves.", display_path))
            if not any(session_log_matches_stage(session_log_path, str(current_stage)) for session_log_path in session_log_paths):
                expected_hints = ", ".join(SESSION_LOG_STAGE_FILE_HINTS.get(str(current_stage), ()))
                finding_id = (
                    "workflow-state-source-locator-wrong-session-log"
                    if current_stage == "ft-source-locator"
                    else "workflow-state-wrong-stage-session-log"
                )
                findings.append(
                    Finding(
                        id=finding_id,
                        severity=session_log_severity,
                        category="session-log",
                        title="Workflow state links a session log from another stage",
                        details=(
                            "`current_stage` must link a session log for the same stage, either by expected file "
                            "name or by `Session Metadata` / `skill`."
                        ),
                        path=display_path,
                        evidence=[
                            f"current_stage={current_stage}",
                            f"expected={expected_hints or current_stage}",
                            *[rel(session_log_path, root) for session_log_path in session_log_paths],
                        ],
                        recommended_action=(
                            "Create/link the session log for the current stage instead of reusing another stage's "
                            "session log."
                        ),
                    )
                )
                checks.append(
                    Check(
                        "workflow-state-session-log-kind",
                        session_log_check_status,
                        "Workflow state does not link a same-stage session log.",
                        display_path,
                    )
                )
            else:
                checks.append(
                    Check(
                        "workflow-state-session-log-kind",
                        "pass",
                        "Workflow state links a same-stage session log.",
                        display_path,
                    )
                )

    if current_stage in DECISION_LOG_REQUIRED_STAGES:
        decision_log_paths = resolve_workflow_decision_logs(state, path, root, ft_root)
        decision_log_severity = "warning" if decision_log_policy == "strict" else "info"
        decision_log_check_status = "warn" if decision_log_policy == "strict" else "pass"
        if not decision_log_paths:
            findings.append(
                Finding(
                    id="workflow-state-missing-decision-log",
                    severity=decision_log_severity,
                    category="decision-log",
                    title="Workflow state does not link an intermediate decision log",
                    details=(
                        "Stages that make source, scope, writing, review or routing decisions should persist "
                        "agent-decision-log.md so later review does not depend on chat history."
                    ),
                    path=display_path,
                    evidence=[f"current_stage={current_stage}", f"stage_status={stage_status}"],
                    recommended_action=(
                        "Create `agent-decision-log.md` in the current handoff folder and link it from "
                        "`required_inputs` and `latest_artifacts.decision_log`."
                    ),
                )
            )
            checks.append(
                Check(
                    "workflow-state-decision-log",
                    decision_log_check_status,
                    "Stage decision log is not linked.",
                    display_path,
                )
            )
        else:
            checks.append(Check("workflow-state-decision-log", "pass", "Stage decision log resolves.", display_path))

    loop_summary_values = [
        value
        for value in latest_artifact_values
        if Path(value).name == "loop-summary.md" and artifact_exists(value, path, root, ft_root)
    ]
    for loop_summary_value in loop_summary_values[:1]:
        loop_path = next(
            candidate
            for candidate in candidate_artifact_paths(loop_summary_value, path, root, ft_root)
            if candidate.exists()
        )
        loop_summary_path = loop_path
        metrics = extract_loop_summary_metrics(loop_path)
        loop_summary_metrics = metrics
        final_status = workflow_final_status(state)
        if final_status and metrics["final_status"] and final_status != metrics["final_status"]:
            findings.append(
                Finding(
                    id="workflow-state-loop-summary-status-mismatch",
                    severity="error",
                    category="status-model",
                    title="workflow-state and loop-summary final statuses differ",
                    details="The workflow handoff and loop summary must not disagree about final status.",
                    path=display_path,
                    evidence=[
                        f"workflow-state={final_status}",
                        f"loop-summary={metrics['final_status']}",
                    ],
                    recommended_action="Update workflow-state.yaml or loop-summary.md so both status fields match.",
                )
            )
        residual_findings, residual_checks = validate_loop_summary_residual_risk(
            loop_path,
            root,
            metrics,
            residual_risk_source_artifacts(
                latest_artifacts,
                latest_artifact_values,
                path,
                root,
                ft_root,
            ),
        )
        findings.extend(residual_findings)
        checks.extend(residual_checks)
        if (
            is_signed_off_state(state)
            and metrics["gap_mentions"]
            and (scope_metrics is None or scope_metrics["blocking_gaps"] is None)
        ):
            findings.append(
                Finding(
                    id="workflow-state-signed-off-with-loop-summary-gaps",
                    severity="warning",
                    category="status-model",
                    title="signed-off loop summary still lists clarification gaps",
                    details=(
                        "Open GAP-* items can be valid, but the signed-off handoff needs an explicit "
                    "qualified meaning so downstream users do not read it as complete coverage."
                ),
                    path=display_path,
                    evidence=[f"loop-summary gap mentions={metrics['gap_mentions']}"],
                    recommended_action="Keep the gaps explicit and prefer a qualified signed-off status.",
                )
            )

    all_artifact_values = [*required_input_values, *latest_artifact_values]
    expected_prompt = None if workflow_superseded_by_session_cycle else expected_transition_prompt(state)
    if expected_prompt == "prompt.reviewer-to-ui-prep.md":
        signoff_source_paths: list[Path] = []
        if loop_summary_path is not None:
            signoff_source_paths.append(loop_summary_path)
        if isinstance(latest_artifacts, dict):
            for key in ("final_findings", "findings", "review_findings"):
                value = latest_artifacts.get(key)
                if isinstance(value, str):
                    resolved = resolve_artifact_path(value, path, root, ft_root)
                    if resolved is not None:
                        signoff_source_paths.append(resolved)
        for value in latest_artifact_values:
            if re.fullmatch(r"round-\d+-findings\.md", Path(strip_quotes(value)).name):
                resolved = resolve_artifact_path(value, path, root, ft_root)
                if resolved is not None:
                    signoff_source_paths.append(resolved)

        signoff_findings, signoff_checks = validate_reviewer_signoff_self_check(
            source_paths=signoff_source_paths,
            workflow_path=path,
            root=root,
            reviewer_signoff_policy=reviewer_signoff_policy,
        )
        findings.extend(signoff_findings)
        checks.extend(signoff_checks)

    if expected_prompt:
        expected_prompt_kind = transition_prompt_kind(expected_prompt)
        explicit_prompt_value = explicit_active_transition_prompt_value(state)
        active_prompt_path: Path | None = None
        if explicit_prompt_value:
            active_prompt_path = resolve_artifact_path(explicit_prompt_value, path, root, ft_root)
            explicit_prompt_kind = transition_prompt_kind(explicit_prompt_value)
            if active_prompt_path is None:
                findings.append(
                    Finding(
                        id="workflow-state-active-transition-prompt-unresolved",
                        severity="error",
                        category="stage-transition",
                        title="Explicit active transition prompt does not resolve",
                        details=(
                            "`latest_artifacts.active_transition_prompt` is present, so it is the active handoff "
                            "prompt. The referenced file must exist before the next stage can start."
                        ),
                        path=display_path,
                        evidence=[f"active_transition_prompt={explicit_prompt_value}"],
                        recommended_action="Fix `latest_artifacts.active_transition_prompt` or create the referenced handoff prompt.",
                    )
                )
            elif expected_prompt_kind and explicit_prompt_kind != expected_prompt_kind:
                findings.append(
                    Finding(
                        id="workflow-state-active-transition-prompt-kind-mismatch",
                        severity="error",
                        category="stage-transition",
                        title="Explicit active transition prompt routes to the wrong stage kind",
                        details=(
                            "`latest_artifacts.active_transition_prompt` resolves, but its filename kind does not "
                            "match the current stage/status/next_skill transition."
                        ),
                        path=display_path,
                        evidence=[
                            f"expected_kind={expected_prompt_kind}",
                            f"active_kind={explicit_prompt_kind or 'unknown'}",
                            f"active_transition_prompt={explicit_prompt_value}",
                            f"next_skill={state.get('next_skill')}",
                            f"stage_status={state.get('stage_status')}",
                        ],
                        recommended_action="Point `active_transition_prompt` to the prompt for the actual next skill.",
                    )
                )
            else:
                conventional_prompt_path = resolving_artifact_by_name(
                    expected_prompt,
                    all_artifact_values,
                    path,
                    root,
                    ft_root,
                )
                if conventional_prompt_path is not None and conventional_prompt_path != active_prompt_path:
                    findings.append(
                        Finding(
                            id="workflow-state-stale-transition-prompt-alias",
                            severity="warning",
                            category="stage-transition",
                            title="Workflow keeps a stale same-kind transition prompt next to the active prompt",
                            details=(
                                "`latest_artifacts.active_transition_prompt` overrides the conventional round prompt, "
                                "but the conventional same-kind prompt still resolves from required_inputs/latest_artifacts. "
                                "This can route a later session to stale handoff instructions."
                            ),
                            path=display_path,
                            evidence=[
                                f"active_transition_prompt={rel(active_prompt_path, root)}",
                                f"stale_conventional_prompt={rel(conventional_prompt_path, root)}",
                                f"conventional_name={expected_prompt}",
                            ],
                            recommended_action=(
                                "Update the conventional prompt alias to the active content or remove the stale "
                                "same-kind prompt reference from required_inputs/latest_artifacts."
                            ),
                        )
                    )
        else:
            active_prompt_path = resolving_artifact_by_name(
                expected_prompt,
                all_artifact_values,
                path,
                root,
                ft_root,
            )
        if active_prompt_path is None and not explicit_prompt_value:
            findings.append(
                Finding(
                    id="workflow-state-missing-active-transition-prompt",
                    severity="error",
                    category="stage-transition",
                    title="Active next stage has no resolving handoff prompt reference",
                    details=(
                        f"The current stage/status requires {expected_prompt!r}, but required_inputs/latest_artifacts "
                        "do not contain a resolving reference to it."
                    ),
                    path=display_path,
                    evidence=[f"next_skill={state.get('next_skill')}", f"stage_status={state.get('stage_status')}", f"expected_prompt={expected_prompt}"],
                    recommended_action="Add the prompt to required_inputs or latest_artifacts, or fix next_skill/stage_status.",
                )
            )
        else:
            checks.append(Check("workflow-state-active-transition-prompt", "pass", "Active transition prompt resolves.", display_path))
            prompt_findings, prompt_checks = validate_active_transition_prompt(
                active_prompt_path,
                path,
                root,
                ft_root,
            )
            findings.extend(prompt_findings)
            checks.extend(prompt_checks)

    stage_status = state.get("stage_status")
    next_skill = state.get("next_skill")
    if (
        stage_status == "ready-for-next-stage"
        and next_skill in {None, "none"}
        and not workflow_superseded_by_session_cycle
    ):
        findings.append(
            Finding(
                id="workflow-state-ready-without-next-skill",
                severity="error",
                category="stage-transition",
                title="ready-for-next-stage has no next_skill",
                details="A handoff marked ready for the next stage must name the next skill.",
                path=display_path,
                evidence=[f"stage_status={stage_status}", f"next_skill={next_skill}"],
                recommended_action="Set next_skill to the intended downstream skill or downgrade the stage_status.",
            )
        )
    if stage_status == "round-cap-reached" and next_skill not in {None, "none"}:
        findings.append(
            Finding(
                id="workflow-state-round-cap-with-next-skill",
                severity="error",
                category="stage-transition",
                title="round-cap-reached must not route to another skill",
                details="A round-cap handoff contains unresolved work and should not automatically advance downstream.",
                path=display_path,
                evidence=[f"stage_status={stage_status}", f"next_skill={next_skill}"],
                recommended_action="Set next_skill to null/none or resolve blockers before routing to the next stage.",
            )
        )
    if next_skill == "ft-ui-automation-prep" and not workflow_superseded_by_session_cycle:
        loop_final_status = loop_summary_metrics.get("final_status") if loop_summary_metrics else None
        if not (is_signed_off_state(state) or loop_final_status == "signed-off"):
            findings.append(
                Finding(
                    id="workflow-state-ui-prep-without-signed-off",
                    severity="error",
                    category="stage-transition",
                    title="ft-ui-automation-prep handoff is not signed off",
                    details="UI automation prep must start only from a signed-off reviewer-loop baseline.",
                    path=display_path,
                    evidence=[f"stage_status={stage_status}", f"workflow_final_status={workflow_final_status(state)}", f"loop_summary_final_status={loop_final_status}"],
                    recommended_action="Downgrade the handoff or complete reviewer-loop sign-off before routing to ft-ui-automation-prep.",
                )
            )
    transition_errors = any(finding.category == "stage-transition" and finding.severity == "error" for finding in findings)
    if not expected_prompt and not transition_errors:
        checks.append(Check("workflow-state-stage-transition", "pass", "Stage transition contract has no active prompt requirement.", display_path))
    else:
        checks.append(
            Check(
                "workflow-state-stage-transition",
                "fail" if transition_errors else "pass",
                "Stage transition contract failed." if transition_errors else "Stage transition contract passed.",
                display_path,
            )
        )

    return findings, checks


def validate(
    root: Path,
    *,
    source_quality_policy: str = "compatible",
    findings_policy: str = "compatible",
    writer_response_policy: str = "compatible",
    test_case_policy: str = "compatible",
    input_restriction_gap_policy: str = "compatible",
    rolling_date_boundary_policy: str = "compatible",
    atomicity_coverage_policy: str = "compatible",
    reviewer_signoff_policy: str = "compatible",
    final_alias_policy: str = "compatible",
    session_log_policy: str = "compatible",
    decision_log_policy: str = "compatible",
) -> dict[str, Any]:
    root_is_standalone_source_normalization_diagnostic = root.is_file() and root.name == "source-normalization-diagnostic.md"
    root_is_standalone_source_table_normalization = root.is_file() and root.name == "source-table-normalization.md"
    root_is_standalone_dictionary_inventory = root.is_file() and root.name == DICTIONARY_INVENTORY_NAME
    root_is_standalone_test_case_file = (
        root.is_file()
        and root.suffix == ".md"
        and root.parent.name == "test-cases"
        and root.name != "README.md"
    )
    workflow_states = iter_workflow_states(root)
    session_cycle_states = iter_session_cycle_states(root)
    artifact_manifests = iter_artifact_manifests(root)
    traceability_matrices = iter_traceability_matrices(root)
    review_findings = iter_review_findings(root)
    writer_responses = iter_writer_responses(root)
    test_case_files = iter_test_case_files(root)
    source_normalization_diagnostics = iter_source_normalization_diagnostics(root)
    writer_process_diagnostics = iter_writer_process_diagnostics(root)
    writer_self_checks = iter_writer_self_checks(root)
    coverage_gap_artifacts = dedupe_paths(
        [
            *iter_named_markdown(root, "coverage-gaps.md"),
            *iter_named_markdown(root, "scope-coverage-gaps.md"),
        ]
    )
    session_logs = iter_session_logs(root)
    decision_logs = iter_decision_logs(root)
    active_text_artifacts = iter_active_text_artifacts(root)
    generated_source_basis_artifacts = iter_generated_source_basis_artifacts(root)
    source_table_normalizations = iter_source_table_normalizations(root)
    dictionary_inventories = iter_dictionary_inventories(root)
    mockup_visual_inventories = iter_mockup_visual_inventories(root)
    oracle_inventories = [
        *iter_named_markdown(root, NEGATIVE_ORACLE_INVENTORY_NAME),
        *iter_named_markdown(root, REQUIREDNESS_ORACLE_INVENTORY_NAME),
    ]
    if root_is_standalone_source_normalization_diagnostic:
        workflow_states = []
        session_cycle_states = []
        artifact_manifests = []
        traceability_matrices = []
        review_findings = []
        writer_responses = []
        test_case_files = []
        source_normalization_diagnostics = [root]
        writer_process_diagnostics = []
        writer_self_checks = []
        coverage_gap_artifacts = []
        session_logs = []
        decision_logs = []
        active_text_artifacts = []
        generated_source_basis_artifacts = []
        source_table_normalizations = []
        dictionary_inventories = []
        mockup_visual_inventories = []
        oracle_inventories = []
    if root_is_standalone_source_table_normalization:
        workflow_states = []
        session_cycle_states = []
        artifact_manifests = []
        traceability_matrices = []
        review_findings = []
        writer_responses = []
        test_case_files = []
        source_normalization_diagnostics = []
        writer_process_diagnostics = []
        writer_self_checks = []
        coverage_gap_artifacts = []
        session_logs = []
        decision_logs = []
        active_text_artifacts = []
        generated_source_basis_artifacts = []
        dictionary_inventories = []
        mockup_visual_inventories = []
        oracle_inventories = []
    if root_is_standalone_dictionary_inventory:
        workflow_states = []
        session_cycle_states = []
        artifact_manifests = []
        traceability_matrices = []
        review_findings = []
        writer_responses = []
        test_case_files = []
        source_normalization_diagnostics = []
        source_table_normalizations = []
        writer_process_diagnostics = []
        writer_self_checks = []
        coverage_gap_artifacts = []
        session_logs = []
        decision_logs = []
        active_text_artifacts = []
        generated_source_basis_artifacts = []
        mockup_visual_inventories = []
        oracle_inventories = []
    test_case_id_index = build_test_case_id_index(test_case_files, root)
    findings: list[Finding] = []
    checks: list[Check] = []
    declared_artifact_paths: set[str] = set()
    active_source_documents: set[Path] = set()

    standalone_artifact = (
        root_is_standalone_source_normalization_diagnostic
        or root_is_standalone_source_table_normalization
        or root_is_standalone_dictionary_inventory
    )

    if not standalone_artifact:
        path_findings, path_checks = validate_ft_package_handoff_layout(root)
        findings.extend(path_findings)
        checks.extend(path_checks)

    if (
        not workflow_states
        and not standalone_artifact
        and not root_is_standalone_test_case_file
    ):
        findings.append(
            Finding(
                id="workflow-state-not-found",
                severity="warning",
                category="workflow-state",
                title="No workflow-state.yaml files found",
                details="The validator did not find any handoff state files.",
                path=rel(root, root),
                evidence=[],
                recommended_action="Run the validator against a repository or fixture containing workflow-state.yaml.",
            )
        )
        checks.append(Check("workflow-state-discovery", "warn", "No workflow-state.yaml files found.", rel(root, root)))

    for path in workflow_states:
        path_findings, path_checks = validate_workflow_state(
            path,
            root,
            reviewer_signoff_policy=reviewer_signoff_policy,
            final_alias_policy=final_alias_policy,
            session_log_policy=session_log_policy,
            decision_log_policy=decision_log_policy,
        )
        findings.extend(path_findings)
        checks.extend(path_checks)
        try:
            active_source_documents.update(collect_active_source_documents(path, root))
        except UnicodeDecodeError:
            pass

    for path in session_cycle_states:
        path_findings, path_checks = validate_session_cycle_state_artifacts(path, root)
        findings.extend(path_findings)
        checks.extend(path_checks)

    for path in sorted(active_source_documents):
        path_findings, path_checks = validate_active_source_document(
            path,
            root,
            source_quality_policy=source_quality_policy,
        )
        findings.extend(path_findings)
        checks.extend(path_checks)

    for path in artifact_manifests:
        path_findings, path_checks, path_declared_paths = validate_artifact_manifest(path, root)
        findings.extend(path_findings)
        checks.extend(path_checks)
        declared_artifact_paths.update(path_declared_paths)

    if not standalone_artifact:
        path_findings, path_checks = validate_source_support_duplicates(root, declared_artifact_paths)
        findings.extend(path_findings)
        checks.extend(path_checks)

        candidate_findings, candidate_checks = validate_candidate_oracle_obligation_coverage(
            root,
            oracle_inventories,
            test_case_files,
        )
        findings.extend(candidate_findings)
        checks.extend(candidate_checks)

    blocked_writer_gate_suppression_paths = blocked_writer_gate_suppression_test_case_paths(
        workflow_states,
        root,
    )

    for path in traceability_matrices:
        path_findings, path_checks = validate_traceability_matrix(
            path,
            root,
            known_test_case_ids=known_test_case_ids_for_artifact(path, root, test_case_id_index),
        )
        findings.extend(path_findings)
        checks.extend(path_checks)

    for path in review_findings:
        path_findings, path_checks = validate_review_findings(
            path,
            root,
            findings_policy=findings_policy,
        )
        findings.extend(path_findings)
        checks.extend(path_checks)

    for path in writer_responses:
        path_findings, path_checks = validate_writer_response(
            path,
            root,
            writer_response_policy=writer_response_policy,
            known_test_case_ids=known_test_case_ids_for_artifact(path, root, test_case_id_index),
        )
        findings.extend(path_findings)
        checks.extend(path_checks)

    for path in test_case_files:
        path_findings, path_checks = validate_test_case_file(
            path,
            root,
            test_case_policy=test_case_policy,
            input_restriction_gap_policy=input_restriction_gap_policy,
            rolling_date_boundary_policy=rolling_date_boundary_policy,
            atomicity_coverage_policy=atomicity_coverage_policy,
            known_test_case_ids=known_test_case_ids_for_artifact(path, root, test_case_id_index),
            suppress_blocked_input_gate_failures=path.resolve() in blocked_writer_gate_suppression_paths,
        )
        findings.extend(path_findings)
        checks.extend(path_checks)

    for path in source_normalization_diagnostics:
        path_findings, path_checks = validate_source_normalization_diagnostic(path, root)
        findings.extend(path_findings)
        checks.extend(path_checks)

    for path in source_table_normalizations:
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            findings.append(
                Finding(
                    id="source-table-normalization-not-utf8",
                    severity="warning",
                    category="source-quality",
                    title="Source Table Normalization is not valid UTF-8",
                    details=str(exc),
                    path=rel(path, root),
                    evidence=[],
                    recommended_action="Save source-table-normalization.md as UTF-8 Markdown.",
                )
            )
            checks.append(Check("source-table-normalization", "warn", "Source Table Normalization is not UTF-8.", rel(path, root)))
            continue
        path_findings, path_checks = validate_source_table_normalization(content, path, root)
        findings.extend(path_findings)
        checks.extend(path_checks)

    for path in dictionary_inventories:
        path_findings, path_checks = validate_dictionary_inventory(path, root)
        findings.extend(path_findings)
        checks.extend(path_checks)

    for path in writer_process_diagnostics:
        path_findings, path_checks = validate_writer_process_diagnostic(path, root)
        findings.extend(path_findings)
        checks.extend(path_checks)

    for path in writer_self_checks:
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            findings.append(
                Finding(
                    id="writer-self-check-not-utf8",
                    severity="error",
                    category="test-case-format",
                    title="Writer self-check is not UTF-8",
                    details=str(exc),
                    path=rel(path, root),
                    evidence=[],
                    recommended_action="Save writer-self-check.md as UTF-8 Markdown.",
                )
            )
            checks.append(Check("writer-self-check-sections", "fail", "Writer self-check is not UTF-8.", rel(path, root)))
            continue
        path_findings, path_checks = validate_writer_self_check_sections(content, path, root)
        findings.extend(path_findings)
        checks.extend(path_checks)

    for path in coverage_gap_artifacts:
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            findings.append(
                Finding(
                    id="coverage-gaps-not-utf8",
                    severity="warning",
                    category="coverage",
                    title="Coverage gaps artifact is not valid UTF-8",
                    details=str(exc),
                    path=rel(path, root),
                    evidence=[],
                    recommended_action="Save coverage gaps artifacts as UTF-8 Markdown.",
                )
            )
            checks.append(Check("coverage-gap-inventory", "warn", "Coverage gaps artifact is not UTF-8.", rel(path, root)))
            continue
        path_findings, path_checks = validate_coverage_gap_inventory(
            content,
            path,
            root,
            input_restriction_gap_policy=input_restriction_gap_policy,
        )
        findings.extend(path_findings)
        checks.extend(path_checks)

    for path in session_logs:
        path_findings, path_checks = validate_session_log(
            path,
            root,
            session_log_policy=session_log_policy,
        )
        findings.extend(path_findings)
        checks.extend(path_checks)

    for path in decision_logs:
        path_findings, path_checks = validate_decision_log(
            path,
            root,
            decision_log_policy=decision_log_policy,
        )
        findings.extend(path_findings)
        checks.extend(path_checks)

    for path in mockup_visual_inventories:
        path_findings, path_checks = validate_mockup_visual_inventory(path, root)
        findings.extend(path_findings)
        checks.extend(path_checks)

    for path in active_text_artifacts:
        path_findings, path_checks = validate_text_encoding_damage(path, root)
        findings.extend(path_findings)
        checks.extend(path_checks)

    for path in generated_source_basis_artifacts:
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            findings.append(
                Finding(
                    id="generated-source-basis-not-utf8",
                    severity="warning",
                    category="source-selection",
                    title="Generated source-basis artifact is not valid UTF-8",
                    details=str(exc),
                    path=rel(path, root),
                    evidence=[],
                    recommended_action="Save the artifact as UTF-8 Markdown.",
                )
            )
            checks.append(Check("generated-artifact-source-basis", "warn", "Artifact is not UTF-8.", rel(path, root)))
            continue
        path_findings, path_checks = validate_generated_artifact_source_basis(
            content,
            path,
            root,
            atomicity_coverage_policy=atomicity_coverage_policy,
        )
        findings.extend(path_findings)
        checks.extend(path_checks)

    for path in iter_named_markdown(root, "ui-evidence-index.md"):
        path_findings, path_checks = validate_ui_evidence_index(path, root)
        findings.extend(path_findings)
        checks.extend(path_checks)

    for path in iter_named_markdown(root, "ui-validation-report.md"):
        path_findings, path_checks = validate_ui_validation_report(path, root)
        findings.extend(path_findings)
        checks.extend(path_checks)

    counts = Counter(finding.severity for finding in findings)
    return {
        "summary": {
            "workflow_states_checked": len(workflow_states),
            "source_documents_checked": len(active_source_documents),
            "artifact_manifests_checked": len(artifact_manifests),
            "traceability_matrices_checked": len(traceability_matrices),
            "review_findings_checked": len(review_findings),
            "writer_responses_checked": len(writer_responses),
            "test_case_files_checked": len(test_case_files),
            "source_normalization_diagnostics_checked": len(source_normalization_diagnostics),
            "source_table_normalizations_checked": len(source_table_normalizations),
            "dictionary_inventories_checked": len(dictionary_inventories),
            "writer_process_diagnostics_checked": len(writer_process_diagnostics),
            "writer_self_checks_checked": len(writer_self_checks),
            "coverage_gap_artifacts_checked": len(coverage_gap_artifacts),
            "session_logs_checked": len(session_logs),
            "decision_logs_checked": len(decision_logs),
            "active_text_artifacts_checked": len(active_text_artifacts),
            "generated_source_basis_artifacts_checked": len(generated_source_basis_artifacts),
            "mockup_visual_inventories_checked": len(mockup_visual_inventories),
            "ui_evidence_indexes_checked": len(iter_named_markdown(root, "ui-evidence-index.md")),
            "ui_validation_reports_checked": len(iter_named_markdown(root, "ui-validation-report.md")),
            "findings_count": len(findings),
            "errors_count": counts["error"],
            "warnings_count": counts["warning"],
            "info_count": counts["info"],
            "checks_count": len(checks),
        },
        "findings": [
            asdict(finding)
            for finding in sorted(findings, key=lambda item: (SEVERITY_ORDER[item.severity], item.id, item.path))
        ],
        "checks": [asdict(check) for check in checks],
    }


def text_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "Agent artifact validation summary",
        f"- workflow states: {summary['workflow_states_checked']}",
        f"- source documents: {summary['source_documents_checked']}",
        f"- artifact manifests: {summary['artifact_manifests_checked']}",
        f"- traceability matrices: {summary['traceability_matrices_checked']}",
        f"- review findings: {summary['review_findings_checked']}",
        f"- writer responses: {summary['writer_responses_checked']}",
        f"- test-case files: {summary['test_case_files_checked']}",
        f"- source normalization diagnostics: {summary['source_normalization_diagnostics_checked']}",
        f"- source table normalizations: {summary['source_table_normalizations_checked']}",
        f"- dictionary inventories: {summary['dictionary_inventories_checked']}",
        f"- writer process diagnostics: {summary['writer_process_diagnostics_checked']}",
        f"- writer self-checks: {summary['writer_self_checks_checked']}",
        f"- coverage gap artifacts: {summary['coverage_gap_artifacts_checked']}",
        f"- session logs: {summary['session_logs_checked']}",
        f"- decision logs: {summary['decision_logs_checked']}",
        f"- active text artifacts: {summary['active_text_artifacts_checked']}",
        f"- generated source-basis artifacts: {summary['generated_source_basis_artifacts_checked']}",
        f"- mockup visual inventories: {summary['mockup_visual_inventories_checked']}",
        f"- UI evidence indexes: {summary['ui_evidence_indexes_checked']}",
        f"- UI validation reports: {summary['ui_validation_reports_checked']}",
        (
            f"- findings: {summary['findings_count']} "
            f"(errors: {summary['errors_count']}, "
            f"warnings: {summary['warnings_count']}, info: {summary['info_count']})"
        ),
        f"- checks: {summary['checks_count']}",
    ]
    if report["findings"]:
        lines.append("- top findings:")
        for finding in report["findings"][:5]:
            lines.append(
                f"  - [{finding['severity']}] {finding['id']}: "
                f"{finding['title']} ({finding['path']})"
            )
    else:
        lines.append("- top findings: none")
    return "\n".join(lines)


def should_fail(report: dict[str, Any], fail_on: str | None) -> bool:
    summary = report["summary"]
    if fail_on == "error":
        return summary["errors_count"] > 0
    if fail_on == "warning":
        return summary["errors_count"] > 0 or summary["warnings_count"] > 0
    return False


def write_stdout(text: str = "") -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    report = validate(
        root,
        source_quality_policy=args.source_quality_policy,
        findings_policy=args.findings_policy,
        writer_response_policy=args.writer_response_policy,
        test_case_policy=args.test_case_policy,
        input_restriction_gap_policy=args.input_restriction_gap_policy,
        rolling_date_boundary_policy=args.rolling_date_boundary_policy,
        atomicity_coverage_policy=args.atomicity_coverage_policy,
        reviewer_signoff_policy=args.reviewer_signoff_policy,
        final_alias_policy=args.final_alias_policy,
        session_log_policy=args.session_log_policy,
        decision_log_policy=args.decision_log_policy,
    )
    json_report = json.dumps(report, ensure_ascii=False, indent=2)
    plain_report = text_report(report)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json_report + "\n", encoding="utf-8")

    emit_json = args.json_only or (not args.json_only and not args.text_only)
    emit_text = args.text_only or (not args.json_only and not args.text_only)

    if emit_text:
        write_stdout(plain_report)
    if emit_text and emit_json:
        write_stdout()
    if emit_json:
        write_stdout(json_report)

    return 1 if should_fail(report, args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
