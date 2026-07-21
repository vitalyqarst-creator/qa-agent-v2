from __future__ import annotations

import re
import unicodedata
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from test_case_agent.review_cycle.prepared_package import load_obligations


HEADING_LINE = re.compile(
    r"^(#{1,6})[^\S\r\n]+(.+?)[^\S\r\n]*#*[^\S\r\n]*$"
)
TC_TITLE = re.compile(r"^(TC-[A-Za-z0-9._-]+)\b")
FENCE_LINE = re.compile(r"^[ \t]*(`{3,}|~{3,})")
TRACEABILITY_FIELD = re.compile(
    r"(?im)^[^\S\r\n]*(?:[-+*][^\S\r\n]+)?"
    r"\*\*(?:Трассировка|Traceability):\*\*[^\S\r\n]*(.+)$"
)
ATOM_REFERENCE = re.compile(r"\bATOM-[A-Za-z0-9._-]+\b")
OBLIGATION_REFERENCE = re.compile(r"\bOBL-[A-Za-z0-9._-]+\b")
DICTIONARY_PROJECTION_START = "runner-dictionary-projection:start"
DICTIONARY_PROJECTION_END = "runner-dictionary-projection:end"
REFERENCE_FIXTURE_START = "runner-reference-fixture:start"
REFERENCE_FIXTURE_END = "runner-reference-fixture:end"

RUNTIME_SECTION_TITLES = {
    "предусловия": "preconditions",
    "тестовые данные": "test_data",
    "шаги": "steps",
    "итоговый ожидаемый результат": "expected_result",
}
RUNTIME_SECTION_NAMES = {
    "preconditions": "Предусловия",
    "test_data": "Тестовые данные",
    "steps": "Шаги",
    "expected_result": "Итоговый ожидаемый результат",
}
NUMBERED_STEP = re.compile(r"(?m)^[^\S\r\n]*\d+[.)][^\S\r\n]+\S")
HTML_COMMENT = re.compile(r"(?s)<!--.*?-->")
RUNTIME_PLACEHOLDER = re.compile(
    r"^(?:не\s+требуется|не\s+применимо)[\s.!;:,\-]*$",
    re.IGNORECASE,
)
LEXICAL_TOKEN = re.compile(r"[^\W_]+", re.UNICODE)
NEGATION_TOKENS = {"не", "нет", "без", "not", "no", "without", "never"}
NEGATION_ROOTS = ("отсутств", "исключен", "absent", "missing")
QUOTED_BOOLEAN_LITERAL = re.compile(
    r"(?:«\s*(?:да|нет|yes|no)\s*»|[\"'“]\s*(?:да|нет|yes|no)\s*[\"'”])",
    re.IGNORECASE,
)
NON_POLARITY_RETENTION_NEGATION = re.compile(
    r"\b(?:без\s+изменени\w*|without\s+change\w*)\b",
    re.IGNORECASE,
)
LEXICAL_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "then",
    "to",
    "when",
    "with",
    "а",
    "бы",
    "в",
    "во",
    "для",
    "до",
    "и",
    "из",
    "или",
    "к",
    "как",
    "на",
    "над",
    "о",
    "об",
    "от",
    "по",
    "под",
    "после",
    "при",
    "с",
    "со",
    "то",
    "что",
    "чтобы",
}
SEMANTIC_FAMILY_ROOTS = {
    "input": ("ввест", "ввод", "заполн", "указ", "enter", "fill", "type"),
    "search": ("поиск", "найт", "ищ", "search", "find"),
    "select": ("выбр", "отмет", "select", "choos", "check"),
    "click": ("нажат", "клик", "click", "tap"),
    "open": ("откр", "open"),
    "clear": ("очист", "сброс", "clear", "reset"),
    "change": ("измен", "change", "edit"),
    "verify": ("провер", "свер", "убед", "просмотр", "verify", "check", "view"),
    "display": ("отображ", "показ", "видим", "появ", "display", "show", "visible", "appear"),
    "accept": ("принима", "принят", "допуст", "accept", "allow"),
    "hide": ("скры", "исчез", "отсутств", "hide", "disappear", "absent"),
    "error": ("ошиб", "валидац", "error", "invalid"),
    "success": ("успеш", "success", "valid"),
    "remain": ("сохран", "оста", "remain", "keep"),
}
REQUIRED_ORACLE_FAMILIES = {"accept"}
CONTRADICTORY_FAMILIES = {
    frozenset(("input", "clear")),
    frozenset(("display", "hide")),
    frozenset(("error", "success")),
    frozenset(("clear", "remain")),
}
ACTION_CHANGE_ROOTS = ("установ", "переключ", "активир", "примен")
ACTION_INPUT_ROOTS = ("примен",)
ACTION_CONTRACT = re.compile(
    r"(?is)(?:^|;\s*)Action\s+contract:\s*(?P<value>.*?)"
    r"(?=;\s*(?:Design\s+fixture|Check\s+type|Test\s+data|Field/block|"
    r"Condition\s+contract):|$)"
)
FIELD_BLOCK_CONTRACT = re.compile(
    r"(?is)(?:^|;\s*)Field/block:\s*(?P<value>.*?)"
    r"(?=;\s*(?:Condition\s+contract|Action\s+contract|Design\s+fixture|"
    r"Check\s+type|Test\s+data):|$)"
)
FIELD_SELECTION_RETENTION_CONTRACT = re.compile(
    r"(?is)\bсохран\w*\b.{0,80}\bв\s+поле\b"
)
FIELD_SELECTION_VISIBLE_AFTER_CHOICE = re.compile(
    r"(?is)\bпосле\s+выбор\w*\b.{0,120}\b(?:отображ\w*|оста\w*|сохран\w*)\b"
)
PERSISTENCE_LIFECYCLE = re.compile(
    r"(?is)\b(?:повторн\w*\s+откр\w*|переоткр\w*|перезагруз\w*|"
    r"после\s+сохранени\w*|нов\w*\s+сесси\w*)\b"
)
NEGATED_REJECTION_ACCEPTANCE = re.compile(
    r"(?is)\bне\s+отклон\w*\b.{0,120}\b(?:недопуст\w*|невалид\w*|invalid)\b"
)
EMPTY_FIELD_CONTRACT = re.compile(
    r"(?is)(?:\bостав\w*\b.{0,100}\bпуст\w*\b|"
    r"\bне\s+заполн\w*\b.{0,100}\bпол\w*\b)"
)
EMPTY_FIELD_ACTION = re.compile(
    r"(?is)(?:\bочист\w*\b.{0,100}\bпол\w*\b|"
    r"\bне\s+заполн\w*\b.{0,100}\bпол\w*\b|"
    r"\bне\s+заполня\w*\b.{0,100}\bпол\w*\b|"
    r"\bостав\w*\b.{0,100}\bпуст\w*\b)"
)
UNCHANGED_CONTROL_STATE = re.compile(
    r"(?is)(?:\bне\s+измен\w*\b|\bне\s+активир\w*\b|"
    r"\bотсутств\w*\b.{0,80}\bактивац\w*\b|"
    r"\bбез\s+(?:обязательн\w*\s+)?активац\w*\b)"
)


def traceability_references(text: str) -> set[str]:
    return {
        item.strip().strip("`").strip()
        for item in re.split(r"[;,]", text)
        if item.strip().strip("`").strip()
    }


def missing_obligation_references(obligation: Any, traced_references: set[str]) -> tuple[str, ...]:
    required_references = tuple(
        dict.fromkeys((*obligation.source_refs, *obligation.dictionary_refs))
    )
    return tuple(
        reference for reference in required_references if reference not in traced_references
    )


def source_reference_finding(
    *, tc_id: str, obligation: Any, missing_references: tuple[str, ...]
) -> dict[str, Any]:
    return {
        "id": "missing-obligation-source-reference",
        "severity": "error",
        "tc_id": tc_id,
        "obligation_id": obligation.obligation_id,
        "atom_id": obligation.traceability_atom_id,
        "missing_references": list(missing_references),
        "message": (
            "TC traceability must preserve every source_refs and "
            "dictionary_refs value of its prepared obligation."
        ),
    }


def exhaustive_dictionary_requirements(obligation: Any) -> tuple[Any, ...]:
    return tuple(
        requirement
        for requirement in obligation.dictionary_requirements
        if requirement.coverage_mode != "reference-only"
    )


def reference_fixture_requirements(obligation: Any) -> tuple[Any, ...]:
    return tuple(
        requirement
        for requirement in obligation.dictionary_requirements
        if requirement.coverage_mode == "reference-only"
        and requirement.fixture_values
    )


def reference_fixture_line(item: Any) -> str:
    label = "Группа fixture" if item.value_kind == "group" else "Значение fixture"
    path = " > ".join(item.hierarchy_path)
    return f"- {label} `{path}`: `{item.value}`"


def _dadata_reference_fixture_lines(requirement: Any) -> tuple[str, ...]:
    values = tuple(item.value for item in requirement.fixture_values)
    if not values or not values[0].startswith("FX-DADATA-"):
        return ()
    fixture_id = values[0]
    if "-ADDR-NEG-" in fixture_id and len(values) >= 3:
        return (
            f"- Fixture DaData: `{fixture_id}`.",
            f"- Запрос: `{values[1]}`.",
            f"- Ожидаемый ответ fixture: `{values[2]}`.",
        )
    if "-REGION-" in fixture_id and len(values) >= 5:
        return (
            f"- Fixture DaData: `{fixture_id}`.",
            f"- Запрос: `{values[1]}`.",
            f"- Параметр `from_bound`: `{values[2]}`.",
            f"- Параметр `to_bound`: `{values[3]}`.",
            f"- Точное предложение: `{values[4]}`.",
        )
    if "-ADDR-" in fixture_id and len(values) >= 9:
        labels = (
            "Fixture DaData",
            "Запрос",
            "Точное предложение",
            "Почтовый индекс",
            "Регион",
            "Город",
            "Улица",
            "Дом",
            "Квартира",
        )
        return tuple(
            f"- {label}: `{value}`." for label, value in zip(labels, values)
        )
    return ()


def reference_fixture_lines(requirement: Any) -> tuple[str, ...]:
    dadata_lines = _dadata_reference_fixture_lines(requirement)
    if dadata_lines:
        return dadata_lines
    return tuple(reference_fixture_line(item) for item in requirement.fixture_values)


def reference_fixture_block(obligation: Any) -> str:
    requirements = reference_fixture_requirements(obligation)
    if not requirements:
        return ""
    lines = [
        f"<!-- {REFERENCE_FIXTURE_START} {obligation.obligation_id} -->",
    ]
    for requirement in requirements:
        if not _dadata_reference_fixture_lines(requirement):
            lines.append(
                "- Использовать точные reference-only fixture values в указанном порядке:"
            )
        lines.extend(reference_fixture_lines(requirement))
    lines.append(f"<!-- {REFERENCE_FIXTURE_END} {obligation.obligation_id} -->")
    return "\n".join(lines)


def reference_fixture_findings(
    *, tc_id: str, block: str, obligation: Any
) -> tuple[dict[str, Any], ...]:
    findings: list[dict[str, Any]] = []
    requirements = reference_fixture_requirements(obligation)
    if not requirements:
        return ()
    marker = re.compile(
        rf"(?ms)^<!--\s*{re.escape(REFERENCE_FIXTURE_START)}\s+"
        rf"{re.escape(obligation.obligation_id)}\s*-->\s*$"
        rf"(.*?)"
        rf"^<!--\s*{re.escape(REFERENCE_FIXTURE_END)}\s+"
        rf"{re.escape(obligation.obligation_id)}\s*-->\s*$"
    )
    match = marker.search(block)
    expected_lines = {
        line: (requirement, item)
        for requirement in requirements
        for line, item in zip(
            reference_fixture_lines(requirement), requirement.fixture_values
        )
    }
    if match is None:
        return (
            {
                "id": "reference-fixture-projection-missing",
                "severity": "error",
                "tc_id": tc_id,
                "obligation_id": obligation.obligation_id,
                "atom_id": obligation.traceability_atom_id,
                "missing_values": [
                    {
                        "dictionary_id": requirement.dictionary_id,
                        "hierarchy_path": list(item.hierarchy_path),
                        "value_kind": item.value_kind,
                        "value": item.value,
                    }
                    for requirement in requirements
                    for item in requirement.fixture_values
                ],
                "message": (
                    "A reference-only obligation with exact fixture values requires "
                    "the runner-owned fixture projection inside its linked TC."
                ),
            },
        )
    recognized_prefixes = (
        "- Группа fixture `",
        "- Значение fixture `",
        "- Fixture DaData:",
        "- Запрос:",
        "- Точное предложение:",
        "- Почтовый индекс:",
        "- Регион:",
        "- Город:",
        "- Улица:",
        "- Дом:",
        "- Квартира:",
        "- Параметр `from_bound`:",
        "- Параметр `to_bound`:",
        "- Ожидаемый ответ fixture:",
    )
    actual_lines = {
        line.strip()
        for line in match.group(1).splitlines()
        if line.strip().startswith(recognized_prefixes)
    }
    missing_lines = sorted(set(expected_lines) - actual_lines)
    unexpected_lines = sorted(actual_lines - set(expected_lines))
    if missing_lines or unexpected_lines:
        findings.append(
            {
                "id": "reference-fixture-projection-incomplete",
                "severity": "error",
                "tc_id": tc_id,
                "obligation_id": obligation.obligation_id,
                "atom_id": obligation.traceability_atom_id,
                "missing_values": [
                    {
                        "dictionary_id": expected_lines[line][0].dictionary_id,
                        "hierarchy_path": list(expected_lines[line][1].hierarchy_path),
                        "value_kind": expected_lines[line][1].value_kind,
                        "value": expected_lines[line][1].value,
                    }
                    for line in missing_lines
                ],
                "unexpected_values": unexpected_lines,
                "message": (
                    "The reference-only fixture projection must preserve every exact "
                    "group/value/path from the prepared obligation."
                ),
            }
        )
    return tuple(findings)


def materialize_draft_reference_fixtures(
    text: str, obligations: Any
) -> tuple[str, dict[str, Any]]:
    by_test_case: dict[str, list[Any]] = {}
    all_by_test_case: dict[str, list[Any]] = {}
    for obligation in obligations.obligations:
        if obligation.planned_test_case_id:
            all_by_test_case.setdefault(
                obligation.planned_test_case_id, []
            ).append(obligation)
        if not reference_fixture_requirements(obligation):
            continue
        if not obligation.planned_test_case_id:
            continue
        by_test_case.setdefault(obligation.planned_test_case_id, []).append(obligation)

    result = text
    materialized: list[dict[str, Any]] = []
    for tc_id, original_block in test_case_sections(text):
        linked = by_test_case.get(tc_id, [])
        cleanup_linked = all_by_test_case.get(tc_id, [])
        if not linked and not cleanup_linked:
            continue
        block = original_block
        for obligation in cleanup_linked:
            existing = re.compile(
                rf"(?ms)^<!--\s*{re.escape(REFERENCE_FIXTURE_START)}\s+"
                rf"{re.escape(obligation.obligation_id)}\s*-->.*?"
                rf"^<!--\s*{re.escape(REFERENCE_FIXTURE_END)}\s+"
                rf"{re.escape(obligation.obligation_id)}\s*-->\s*\n?"
            )
            block = existing.sub("", block)
        if not linked:
            result = result.replace(original_block, block, 1)
            continue
        projection = "\n\n".join(reference_fixture_block(item) for item in linked)
        test_data = re.search(r"(?m)^###\s+Тестовые данные\s*$", block)
        if test_data is None:
            steps = re.search(r"(?m)^###\s+Шаги\s*$", block)
            insertion = steps.start() if steps else len(block)
            prefix = "### Тестовые данные\n\n"
        else:
            following = re.search(r"(?m)^###\s+", block[test_data.end() :])
            insertion = (
                test_data.end() + following.start()
                if following is not None
                else len(block)
            )
            prefix = "\n\n"
        block = (
            block[:insertion].rstrip()
            + "\n\n"
            + prefix
            + projection
            + "\n\n"
            + block[insertion:].lstrip()
        )
        result = result.replace(original_block, block, 1)
        for obligation in linked:
            materialized.append(
                {
                    "obligation_id": obligation.obligation_id,
                    "atom_id": obligation.traceability_atom_id,
                    "test_case_id": tc_id,
                    "requirements": [
                        {
                            "dictionary_id": requirement.dictionary_id,
                            "coverage_mode": requirement.coverage_mode,
                            "fixture_value_count": len(requirement.fixture_values),
                        }
                        for requirement in reference_fixture_requirements(obligation)
                    ],
                }
            )
    return result, {
        "version": 1,
        "validator": "runner-owned-reference-fixture-projection-v1",
        "materialized_count": len(materialized),
        "items": materialized,
    }


def validate_writer_dictionary_ownership(
    text: str,
    obligations: Any,
    *,
    trusted_runner_projected_test_case_ids: Collection[str] = (),
) -> dict[str, Any]:
    """Reject model-owned enumeration that the runner will materialize exactly.

    The structured writer may name one concrete dictionary value when it is useful
    for an action or title, but it must not reproduce an exhaustive value set that
    is already owned by ``materialize_draft_dictionary_projections``.
    """

    trusted_projection_ids = set(trusted_runner_projected_test_case_ids)
    by_test_case: dict[str, list[Any]] = {}
    for obligation in obligations.obligations:
        if not exhaustive_dictionary_requirements(obligation):
            continue
        if not obligation.planned_test_case_id:
            continue
        by_test_case.setdefault(obligation.planned_test_case_id, []).append(obligation)

    findings: list[dict[str, Any]] = []
    checked_obligations = 0
    for tc_id, block in test_case_sections(text):
        for obligation in by_test_case.get(tc_id, []):
            checked_obligations += 1
            writer_owned_block = block
            if tc_id in trusted_projection_ids:
                writer_owned_block = re.sub(
                    rf"(?ms)^<!--\s*{re.escape(DICTIONARY_PROJECTION_START)}\s+"
                    rf"{re.escape(obligation.obligation_id)}\s*-->.*?"
                    rf"^<!--\s*{re.escape(DICTIONARY_PROJECTION_END)}\s+"
                    rf"{re.escape(obligation.obligation_id)}\s*-->\s*$",
                    "",
                    block,
                )
            for requirement in exhaustive_dictionary_requirements(obligation):
                values = tuple(
                    dict.fromkeys(
                        item.value.strip()
                        for item in requirement.required_values
                        if item.value.strip()
                    )
                )
                if len(values) < 2:
                    continue
                mentioned = tuple(
                    value for value in values if value in writer_owned_block
                )
                if len(mentioned) < 2:
                    continue
                findings.append(
                    {
                        "id": "writer-owned-exhaustive-dictionary-values",
                        "severity": "error",
                        "tc_id": tc_id,
                        "obligation_id": obligation.obligation_id,
                        "atom_id": obligation.traceability_atom_id,
                        "dictionary_id": requirement.dictionary_id,
                        "coverage_mode": requirement.coverage_mode,
                        "mentioned_value_count": len(mentioned),
                        "required_value_count": len(requirement.required_values),
                        "mentioned_values_sample": list(mentioned[:5]),
                        "message": (
                            "The structured writer must keep an exhaustive dictionary "
                            "check symbolic; the runner alone materializes the exact values."
                        ),
                    }
                )
    return {
        "passed": not findings,
        "validator": "runner-owned-dictionary-writer-boundary-v1",
        "checked_obligation_count": checked_obligations,
        "finding_count": len(findings),
        "findings": findings,
    }


def dictionary_projection_line(item: Any) -> str:
    label = "Группа" if item.value_kind == "group" else "Значение"
    path = " > ".join(item.hierarchy_path)
    return f"- {label} `{path}`: `{item.value}`"


def dictionary_projection_block(obligation: Any) -> str:
    requirements = exhaustive_dictionary_requirements(obligation)
    if not requirements:
        return ""
    lines = [
        f"<!-- {DICTIONARY_PROJECTION_START} {obligation.obligation_id} -->",
    ]
    for requirement in requirements:
        lines.append(
            f"- Полный набор `{requirement.dictionary_id}` "
            f"(`{requirement.coverage_mode}`):"
        )
        lines.extend(
            dictionary_projection_line(item) for item in requirement.required_values
        )
    lines.append(
        f"<!-- {DICTIONARY_PROJECTION_END} {obligation.obligation_id} -->"
    )
    return "\n".join(lines)


def dictionary_projection_findings(
    *, tc_id: str, block: str, obligation: Any
) -> tuple[dict[str, Any], ...]:
    findings: list[dict[str, Any]] = []
    marker = re.compile(
        rf"(?ms)^<!--\s*{re.escape(DICTIONARY_PROJECTION_START)}\s+"
        rf"{re.escape(obligation.obligation_id)}\s*-->\s*$"
        rf"(.*?)"
        rf"^<!--\s*{re.escape(DICTIONARY_PROJECTION_END)}\s+"
        rf"{re.escape(obligation.obligation_id)}\s*-->\s*$"
    )
    match = marker.search(block)
    for requirement in exhaustive_dictionary_requirements(obligation):
        expected_lines = {
            dictionary_projection_line(item): item
            for item in requirement.required_values
        }
        if match is None:
            findings.append(
                {
                    "id": "dictionary-projection-missing",
                    "severity": "error",
                    "tc_id": tc_id,
                    "obligation_id": obligation.obligation_id,
                    "atom_id": obligation.traceability_atom_id,
                    "dictionary_id": requirement.dictionary_id,
                    "coverage_mode": requirement.coverage_mode,
                    "missing_values": [
                        {
                            "hierarchy_path": list(item.hierarchy_path),
                            "value_kind": item.value_kind,
                            "value": item.value,
                        }
                        for item in requirement.required_values
                    ],
                    "unexpected_values": [],
                    "message": (
                        "An exhaustive dictionary obligation requires the runner-owned "
                        "value projection inside its linked TC."
                    ),
                }
            )
            continue
        requirement_marker = re.compile(
            rf"(?ms)^- Полный набор `{re.escape(requirement.dictionary_id)}` "
            rf"\(`{re.escape(requirement.coverage_mode)}`\):\s*$"
            rf"(.*?)"
            rf"(?=^- Полный набор `|\Z)"
        )
        requirement_match = requirement_marker.search(match.group(1))
        actual_lines = {
            line.strip()
            for line in (
                requirement_match.group(1).splitlines()
                if requirement_match is not None
                else ()
            )
            if line.strip().startswith(("- Группа `", "- Значение `"))
        }
        missing_lines = sorted(set(expected_lines) - actual_lines)
        unexpected_lines = sorted(actual_lines - set(expected_lines))
        if not missing_lines and not unexpected_lines:
            continue
        findings.append(
            {
                "id": "dictionary-projection-incomplete",
                "severity": "error",
                "tc_id": tc_id,
                "obligation_id": obligation.obligation_id,
                "atom_id": obligation.traceability_atom_id,
                "dictionary_id": requirement.dictionary_id,
                "coverage_mode": requirement.coverage_mode,
                "missing_values": [
                    {
                        "hierarchy_path": list(expected_lines[line].hierarchy_path),
                        "value_kind": expected_lines[line].value_kind,
                        "value": expected_lines[line].value,
                    }
                    for line in missing_lines
                ],
                "unexpected_values": unexpected_lines,
                "message": (
                    "The TC dictionary projection must exactly preserve every required "
                    "group/leaf value and hierarchy path from the prepared obligation."
                ),
            }
        )
    return tuple(findings)


def materialize_draft_dictionary_projections(
    text: str, obligations: Any
) -> tuple[str, dict[str, Any]]:
    by_test_case: dict[str, list[Any]] = {}
    all_by_test_case: dict[str, list[Any]] = {}
    for obligation in obligations.obligations:
        if obligation.planned_test_case_id:
            all_by_test_case.setdefault(
                obligation.planned_test_case_id, []
            ).append(obligation)
        if not exhaustive_dictionary_requirements(obligation):
            continue
        if not obligation.planned_test_case_id:
            continue
        by_test_case.setdefault(obligation.planned_test_case_id, []).append(obligation)

    result = text
    materialized: list[dict[str, Any]] = []
    for tc_id, original_block in test_case_sections(text):
        linked = by_test_case.get(tc_id, [])
        cleanup_linked = all_by_test_case.get(tc_id, [])
        if not linked and not cleanup_linked:
            continue
        block = original_block
        for obligation in cleanup_linked:
            existing = re.compile(
                rf"(?ms)^<!--\s*{re.escape(DICTIONARY_PROJECTION_START)}\s+"
                rf"{re.escape(obligation.obligation_id)}\s*-->.*?"
                rf"^<!--\s*{re.escape(DICTIONARY_PROJECTION_END)}\s+"
                rf"{re.escape(obligation.obligation_id)}\s*-->\s*\n?"
            )
            block = existing.sub("", block)
        if not linked:
            result = result.replace(original_block, block, 1)
            continue
        projection = "\n\n".join(
            dictionary_projection_block(obligation) for obligation in linked
        )
        test_data = re.search(r"(?m)^###\s+Тестовые данные\s*$", block)
        if test_data is None:
            steps = re.search(r"(?m)^###\s+Шаги\s*$", block)
            insertion = steps.start() if steps else len(block)
            prefix = "### Тестовые данные\n\n"
        else:
            following = re.search(r"(?m)^###\s+", block[test_data.end() :])
            insertion = (
                test_data.end() + following.start()
                if following is not None
                else len(block)
            )
            prefix = "\n\n"
        block = (
            block[:insertion].rstrip()
            + "\n\n"
            + prefix
            + projection
            + "\n\n"
            + block[insertion:].lstrip()
        )
        result = result.replace(original_block, block, 1)
        for obligation in linked:
            materialized.append(
                {
                    "obligation_id": obligation.obligation_id,
                    "atom_id": obligation.traceability_atom_id,
                    "test_case_id": tc_id,
                    "requirements": [
                        {
                            "dictionary_id": requirement.dictionary_id,
                            "coverage_mode": requirement.coverage_mode,
                            "required_value_count": len(requirement.required_values),
                        }
                        for requirement in exhaustive_dictionary_requirements(obligation)
                    ],
                }
            )
    return result, {
        "version": 1,
        "validator": "runner-owned-dictionary-projection-v1",
        "materialized_count": len(materialized),
        "items": materialized,
    }


@dataclass(frozen=True)
class MarkdownHeading:
    offset: int
    level: int
    title: str
    tc_id: str = ""


def markdown_headings(text: str) -> tuple[MarkdownHeading, ...]:
    headings: list[MarkdownHeading] = []
    offset = 0
    fence_char = ""
    fence_length = 0
    for line_with_end in text.splitlines(keepends=True):
        line = line_with_end.rstrip("\r\n")
        fence = FENCE_LINE.match(line)
        if fence:
            marker = fence.group(1)
            if not fence_char:
                fence_char = marker[0]
                fence_length = len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_length:
                fence_char = ""
                fence_length = 0
            offset += len(line_with_end)
            continue
        if not fence_char:
            match = HEADING_LINE.match(line)
            if match:
                title = match.group(2).strip()
                tc_match = TC_TITLE.match(title)
                headings.append(
                    MarkdownHeading(
                        offset=offset,
                        level=len(match.group(1)),
                        title=title,
                        tc_id=tc_match.group(1) if tc_match else "",
                    )
                )
        offset += len(line_with_end)
    return tuple(headings)


def test_case_sections(text: str) -> tuple[tuple[str, str], ...]:
    headings = markdown_headings(text)
    sections: list[tuple[str, str]] = []
    for index, heading in enumerate(headings):
        if not heading.tc_id:
            continue
        end = len(text)
        for following in headings[index + 1 :]:
            if following.tc_id or following.level <= heading.level:
                end = following.offset
                break
        sections.append((heading.tc_id, text[heading.offset:end]))
    return tuple(sections)


def without_fenced_blocks(text: str) -> str:
    lines: list[str] = []
    fence_char = ""
    fence_length = 0
    for line_with_end in text.splitlines(keepends=True):
        line = line_with_end.rstrip("\r\n")
        fence = FENCE_LINE.match(line)
        if fence:
            marker = fence.group(1)
            if not fence_char:
                fence_char = marker[0]
                fence_length = len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_length:
                fence_char = ""
                fence_length = 0
            continue
        if not fence_char:
            lines.append(line_with_end)
    return "".join(lines)


def _normalized_text(text: str) -> str:
    return " ".join(
        unicodedata.normalize("NFKC", text).casefold().replace("ё", "е").split()
    )


def _runtime_section_content(block: str) -> dict[str, tuple[str, ...]]:
    safe_block = without_fenced_blocks(block)
    heading_matches = list(
        re.finditer(
            r"(?m)^#{1,6}[^\S\r\n]+(.+?)[^\S\r\n]*#*"
            r"[^\S\r\n]*(?:\r?\n|$)",
            safe_block,
        )
    )
    content: dict[str, list[str]] = {}
    for index, match in enumerate(heading_matches):
        title = _normalized_text(match.group(1).strip())
        section_id = RUNTIME_SECTION_TITLES.get(title)
        if section_id is None:
            continue
        end = (
            heading_matches[index + 1].start()
            if index + 1 < len(heading_matches)
            else len(safe_block)
        )
        content.setdefault(section_id, []).append(safe_block[match.end() : end])
    return {key: tuple(value) for key, value in content.items()}


def _visible_section_text(text: str) -> str:
    value = HTML_COMMENT.sub("", text)
    value = TRACEABILITY_FIELD.sub("", value)
    value = re.sub(r"[`*_>#]", "", value)
    return value.strip()


def _placeholder_text(text: str) -> str:
    value = _normalized_text(_visible_section_text(text))
    return re.sub(r"^(?:[-+*]|\d+[.)])\s*", "", value).strip()


def _lexical_tokens(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKC", text).casefold().replace("ё", "е")
    return {
        token
        for token in LEXICAL_TOKEN.findall(normalized)
        if token not in LEXICAL_STOPWORDS
        and token not in NEGATION_TOKENS
        and not token.isdigit()
    }


def _tokens_overlap(left: str, right: str) -> bool:
    if left == right:
        return True
    common_prefix = 0
    for left_char, right_char in zip(left, right):
        if left_char != right_char:
            break
        common_prefix += 1
    return common_prefix >= 5


def _shared_token_count(left: set[str], right: set[str]) -> int:
    return sum(
        1
        for left_token in left
        if any(_tokens_overlap(left_token, right_token) for right_token in right)
    )


def _semantic_families(tokens: set[str]) -> set[str]:
    return {
        family
        for family, roots in SEMANTIC_FAMILY_ROOTS.items()
        if any(token.startswith(root) for token in tokens for root in roots)
    }


def _action_semantic_families(tokens: set[str]) -> set[str]:
    families = _semantic_families(tokens)
    if any(token.startswith(root) for token in tokens for root in ACTION_CHANGE_ROOTS):
        families.add("change")
    if any(token.startswith(root) for token in tokens for root in ACTION_INPUT_ROOTS):
        families.add("input")
    return families


def _has_contradictory_families(left: set[str], right: set[str]) -> bool:
    return any(
        len(pair & left) == 1
        and len(pair & right) == 1
        and (pair & left) != (pair & right)
        for pair in CONTRADICTORY_FAMILIES
    )


def _semantic_contract_matches(
    contract: str, actual: str, *, action_contract: bool = False
) -> bool:
    contract_tokens = _lexical_tokens(contract)
    actual_tokens = _lexical_tokens(actual)
    if not contract_tokens or not actual_tokens:
        return False
    shared_count = _shared_token_count(contract_tokens, actual_tokens)
    family_projection = (
        _action_semantic_families if action_contract else _semantic_families
    )
    contract_families = family_projection(contract_tokens)
    actual_families = family_projection(actual_tokens)
    if (
        action_contract
        and EMPTY_FIELD_CONTRACT.search(contract)
        and EMPTY_FIELD_ACTION.search(actual)
        and shared_count >= 2
    ):
        return True
    if (
        not action_contract
        and "accept" in contract_families
        and NEGATED_REJECTION_ACCEPTANCE.search(actual)
    ):
        actual_families.add("accept")
    if not action_contract and UNCHANGED_CONTROL_STATE.search(actual):
        actual_families.add("remain")
    if (
        action_contract
        and UNCHANGED_CONTROL_STATE.search(contract)
        and UNCHANGED_CONTROL_STATE.search(actual)
        and shared_count >= 1
    ):
        return True
    if _has_contradictory_families(contract_families, actual_families):
        return False
    if (
        not action_contract
        and not PERSISTENCE_LIFECYCLE.search(contract)
        and FIELD_SELECTION_RETENTION_CONTRACT.search(contract)
        and FIELD_SELECTION_VISIBLE_AFTER_CHOICE.search(actual)
        and shared_count >= 2
    ):
        return True
    if (
        not action_contract
        and contract_families.intersection(REQUIRED_ORACLE_FAMILIES)
        - actual_families
    ):
        return False
    if contract_families and not contract_families.intersection(actual_families):
        return False
    if shared_count >= 2:
        return True
    return bool(shared_count and contract_families.intersection(actual_families))


def _prepared_action_contract(test_intent: str) -> str:
    """Use the executable clause, not conditions and fixtures, for step matching."""

    match = ACTION_CONTRACT.search(test_intent)
    if match is None:
        return test_intent
    value = match.group("value").strip()
    if not value:
        return test_intent
    field_match = FIELD_BLOCK_CONTRACT.search(test_intent)
    field_name = field_match.group("value").strip() if field_match else ""
    return f"{value} {field_name}".strip()


def _has_explicit_negation(text: str) -> bool:
    normalized = unicodedata.normalize("NFKC", text).casefold().replace("ё", "е")
    # Quoted boolean values describe control state, not sentence polarity.  For
    # example, `переключатель = «Нет»` must not invert an otherwise positive
    # oracle such as `поле отображается`.
    normalized = QUOTED_BOOLEAN_LITERAL.sub(" ", normalized)
    # `без изменения` describes value retention and does not negate a positive
    # acceptance/display oracle.
    normalized = NON_POLARITY_RETENTION_NEGATION.sub(" ", normalized)
    tokens = LEXICAL_TOKEN.findall(normalized)
    return bool(
        NEGATION_TOKENS.intersection(tokens)
        or any(token.startswith(root) for token in tokens for root in NEGATION_ROOTS)
    )


def _oracle_polarity_conflicts(contract: str, actual: str) -> bool:
    contract_tokens = _lexical_tokens(contract)
    actual_tokens = _lexical_tokens(actual)
    if (
        "accept" in _semantic_families(contract_tokens)
        and NEGATED_REJECTION_ACCEPTANCE.search(actual)
    ):
        return False
    if (
        "hide" in _semantic_families(contract_tokens)
        and any(token.startswith(("отсутств", "absent")) for token in actual_tokens)
    ):
        return False
    shared_families = _semantic_families(contract_tokens).intersection(
        _semantic_families(actual_tokens)
    )
    if not shared_families or not _shared_token_count(contract_tokens, actual_tokens):
        return False
    relevant_clauses = []
    for clause in re.split(r"[.;!?]+|\r?\n+", actual):
        clause_tokens = _lexical_tokens(clause)
        if not clause_tokens:
            continue
        if not _semantic_families(contract_tokens).intersection(
            _semantic_families(clause_tokens)
        ):
            continue
        if not _shared_token_count(contract_tokens, clause_tokens):
            continue
        relevant_clauses.append(clause)
    if not relevant_clauses:
        relevant_clauses = [actual]
    contract_negated = _has_explicit_negation(contract)
    return all(
        _has_explicit_negation(clause) != contract_negated
        for clause in relevant_clauses
    )


def _strict_runtime_contract_findings(
    *,
    sections: tuple[tuple[str, str], ...],
    obligations_by_id: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    findings: list[dict[str, Any]] = []
    occurrences: dict[str, list[str]] = {}
    testable_obligations = {
        obligation_id: obligation
        for obligation_id, obligation in obligations_by_id.items()
        if obligation.coverage_status == "testable"
    }
    planned_by_tc: dict[str, list[Any]] = {}
    for obligation in testable_obligations.values():
        if obligation.planned_test_case_id:
            planned_by_tc.setdefault(obligation.planned_test_case_id, []).append(
                obligation
            )

    for tc_id, block in sections:
        runtime_sections = _runtime_section_content(block)
        for section_id, section_name in RUNTIME_SECTION_NAMES.items():
            values = runtime_sections.get(section_id, ())
            if not values:
                findings.append(
                    {
                        "id": "missing-runtime-section",
                        "severity": "error",
                        "tc_id": tc_id,
                        "section": section_name,
                        "message": (
                            "Strict runtime TCs must contain every required "
                            "execution section."
                        ),
                    }
                )
                continue
            if len(values) > 1:
                findings.append(
                    {
                        "id": "duplicate-runtime-section",
                        "severity": "error",
                        "tc_id": tc_id,
                        "section": section_name,
                        "message": "A required runtime section must occur exactly once per TC.",
                    }
                )
            visible = _visible_section_text(values[0])
            if not visible:
                findings.append(
                    {
                        "id": "empty-runtime-section",
                        "severity": "error",
                        "tc_id": tc_id,
                        "section": section_name,
                        "message": "A required runtime section must not be empty.",
                    }
                )
                continue
            if RUNTIME_PLACEHOLDER.fullmatch(
                _placeholder_text(values[0])
            ) and section_id not in {"preconditions", "test_data"}:
                findings.append(
                    {
                        "id": "forbidden-runtime-placeholder",
                        "severity": "error",
                        "tc_id": tc_id,
                        "section": section_name,
                        "message": (
                            "Only Preconditions and Test data may use an explicit "
                            "not-applicable placeholder."
                        ),
                    }
                )

        step_values = runtime_sections.get("steps", ())
        if step_values and not NUMBERED_STEP.search(step_values[0]):
            findings.append(
                {
                    "id": "runtime-step-missing-numbered-action",
                    "severity": "error",
                    "tc_id": tc_id,
                    "message": "Strict runtime TCs require at least one numbered executable step.",
                }
            )

        safe_block = without_fenced_blocks(block)
        trace_values = TRACEABILITY_FIELD.findall(safe_block)
        trace_text = "; ".join(trace_values)
        traced_references = traceability_references(trace_text)
        traced_atoms = set(ATOM_REFERENCE.findall(trace_text))
        traced_obligations = set(OBLIGATION_REFERENCE.findall(trace_text))
        traced_items: list[Any] = []
        for obligation in testable_obligations.values():
            is_traced = obligation.obligation_id in traced_obligations
            if obligation.obligation_id == obligation.traceability_atom_id:
                is_traced = is_traced or obligation.traceability_atom_id in traced_atoms
            if not is_traced:
                continue
            traced_items.append(obligation)
            occurrences.setdefault(obligation.obligation_id, []).append(tc_id)
            if (
                obligation.planned_test_case_id
                and obligation.planned_test_case_id != tc_id
            ):
                findings.append(
                    {
                        "id": "planned-test-case-mismatch",
                        "severity": "error",
                        "tc_id": tc_id,
                        "obligation_id": obligation.obligation_id,
                        "planned_test_case_id": obligation.planned_test_case_id,
                        "message": "A planned obligation may be covered only by its planned TC id.",
                    }
                )

        mapped_items = list(planned_by_tc.get(tc_id, ()))
        mapped_ids = {item.obligation_id for item in mapped_items}
        mapped_items.extend(
            item
            for item in traced_items
            if not item.planned_test_case_id and item.obligation_id not in mapped_ids
        )
        if not mapped_items:
            findings.append(
                {
                    "id": "unmapped-runtime-test-case",
                    "severity": "error",
                    "tc_id": tc_id,
                        "message": (
                            "Every strict runtime TC must map to at least one "
                            "testable prepared obligation."
                        ),
                }
            )
        expected_references: set[str] = set()
        for obligation in mapped_items:
            expected_references.add(obligation.obligation_id)
            if obligation.traceability_atom_id:
                expected_references.add(obligation.traceability_atom_id)
            expected_references.update(obligation.source_refs)
            expected_references.update(obligation.dictionary_refs)
        missing_references = sorted(expected_references - traced_references)
        unexpected_references = sorted(traced_references - expected_references)
        if missing_references or unexpected_references:
            findings.append(
                {
                    "id": "strict-traceability-contract-mismatch",
                    "severity": "error",
                    "tc_id": tc_id,
                    "missing_references": missing_references,
                    "unexpected_references": unexpected_references,
                    "message": (
                        "TC traceability must equal the exact obligation, atom, "
                        "source and dictionary contract for this TC."
                    ),
                }
            )

        steps = step_values[0] if step_values else ""
        precondition_values = runtime_sections.get("preconditions", ())
        execution_contract_text = "\n".join(
            value
            for value in (
                precondition_values[0] if precondition_values else "",
                steps,
            )
            if value
        )
        expected_values = runtime_sections.get("expected_result", ())
        expected_result = expected_values[0] if expected_values else ""
        for obligation in mapped_items:
            if not _semantic_contract_matches(
                _prepared_action_contract(obligation.test_intent),
                execution_contract_text,
                action_contract=True,
            ):
                findings.append(
                    {
                        "id": "action-contract-mismatch",
                        "severity": "error",
                        "tc_id": tc_id,
                        "obligation_id": obligation.obligation_id,
                        "message": (
                            "Numbered preconditions and steps must have meaningful "
                            "lexical and action overlap with the prepared test_intent."
                        ),
                    }
                )
            if _oracle_polarity_conflicts(
                obligation.observable_oracle, expected_result
            ):
                findings.append(
                    {
                        "id": "oracle-polarity-mismatch",
                        "severity": "error",
                        "tc_id": tc_id,
                        "obligation_id": obligation.obligation_id,
                        "message": (
                            "The final expected result has opposite polarity to the "
                            "prepared observable oracle."
                        ),
                    }
                )
            elif not _semantic_contract_matches(
                obligation.observable_oracle, expected_result
            ):
                findings.append(
                    {
                        "id": "observable-oracle-contract-mismatch",
                        "severity": "error",
                        "tc_id": tc_id,
                        "obligation_id": obligation.obligation_id,
                        "message": (
                            "The final expected result must preserve the prepared "
                            "observable oracle semantics."
                        ),
                    }
                )

    for obligation_id, tc_ids in occurrences.items():
        distinct_tc_ids = tuple(dict.fromkeys(tc_ids))
        if len(distinct_tc_ids) <= 1:
            continue
        for tc_id in distinct_tc_ids:
            findings.append(
                {
                    "id": "duplicate-obligation-coverage",
                    "severity": "error",
                    "tc_id": tc_id,
                    "obligation_id": obligation_id,
                    "test_case_ids": list(distinct_tc_ids),
                    "message": "A prepared obligation must not be claimed by more than one TC.",
                }
            )
    return findings, occurrences


def _strict_valid_coverage(
    *,
    occurrences: dict[str, list[str]],
    obligations_by_id: dict[str, Any],
    findings: list[dict[str, Any]],
) -> set[str]:
    covered: set[str] = set()
    for obligation_id, tc_ids in occurrences.items():
        obligation = obligations_by_id[obligation_id]
        for tc_id in dict.fromkeys(tc_ids):
            if (
                obligation.planned_test_case_id
                and obligation.planned_test_case_id != tc_id
            ):
                continue
            has_local_finding = any(
                finding.get("tc_id") == tc_id
                and (
                    "obligation_id" not in finding
                    or finding.get("obligation_id") == obligation_id
                )
                for finding in findings
            )
            if not has_local_finding:
                covered.add(obligation_id)
                break
    return covered


@dataclass(frozen=True)
class ObligationGateResult:
    passed: bool
    package_id: str
    test_case_count: int
    testable_obligations: int
    covered_obligations: tuple[str, ...]
    findings: tuple[dict[str, Any], ...]
    checked_paths: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "validator": "prepared-package-obligation-gate-v4",
            "package_id": self.package_id,
            "test_case_count": self.test_case_count,
            "testable_obligations": self.testable_obligations,
            "covered_obligations": list(self.covered_obligations),
            "checked_paths": list(self.checked_paths),
            "findings": list(self.findings),
        }


def validate_draft_obligation_coverage(
    *,
    draft_path: Path,
    obligations_path: Path,
    strict_runtime_contract: bool = False,
) -> ObligationGateResult:
    text = draft_path.read_text(encoding="utf-8")
    obligations = load_obligations(obligations_path)
    obligations_by_id = {
        obligation.obligation_id: obligation for obligation in obligations.obligations
    }
    obligations_by_atom: dict[str, list[Any]] = {}
    for obligation in obligations.obligations:
        obligations_by_atom.setdefault(obligation.traceability_atom_id, []).append(obligation)
    testable = {
        obligation.obligation_id
        for obligation in obligations.obligations
        if obligation.coverage_status == "testable"
    }
    covered: set[str] = set()
    findings: list[dict[str, Any]] = []
    sections = test_case_sections(text)

    for tc_id, block in sections:
        safe_block = without_fenced_blocks(block)
        trace_values = TRACEABILITY_FIELD.findall(safe_block)
        projection_block = safe_block if strict_runtime_contract else block
        trace_text = " ".join(trace_values)
        traced_references = traceability_references(trace_text)
        traced_atoms = set(ATOM_REFERENCE.findall(trace_text))
        traced_obligations = set(OBLIGATION_REFERENCE.findall(trace_text))
        for atom_id in sorted(traced_atoms):
            if atom_id not in obligations_by_atom:
                findings.append(
                    {
                        "id": "unknown-atomic-obligation",
                        "severity": "error",
                        "tc_id": tc_id,
                        "atom_id": atom_id,
                        "message": "TC references an ATOM that is absent from the prepared package.",
                    }
                )
        for obligation_id in sorted(traced_obligations):
            obligation = obligations_by_id.get(obligation_id)
            if obligation is None:
                findings.append(
                    {
                        "id": "unknown-prepared-obligation",
                        "severity": "error",
                        "tc_id": tc_id,
                        "obligation_id": obligation_id,
                        "message": "TC references an OBL that is absent from the prepared package.",
                    }
                )
                continue
            atom_id = obligation.traceability_atom_id
            if atom_id not in traced_atoms:
                findings.append(
                    {
                        "id": "obligation-atom-pair-mismatch",
                        "severity": "error",
                        "tc_id": tc_id,
                        "obligation_id": obligation_id,
                        "atom_id": atom_id,
                        "message": "TC must trace both the prepared obligation and its linked atom.",
                    }
                )
            elif obligation.coverage_status != "testable":
                findings.append(
                    {
                        "id": "non-testable-obligation-used-as-test",
                        "severity": "error",
                        "tc_id": tc_id,
                        "obligation_id": obligation_id,
                        "atom_id": atom_id,
                        "coverage_status": obligation.coverage_status,
                        "message": "gap, unclear and not-applicable obligations cannot become executable TC coverage.",
                    }
                )
            else:
                missing_references = missing_obligation_references(
                    obligation, traced_references
                )
                if missing_references:
                    findings.append(
                        source_reference_finding(
                            tc_id=tc_id,
                            obligation=obligation,
                            missing_references=missing_references,
                        )
                    )
                findings.extend(
                    dictionary_projection_findings(
                        tc_id=tc_id,
                        block=projection_block,
                        obligation=obligation,
                    )
                )
                findings.extend(
                    reference_fixture_findings(
                        tc_id=tc_id,
                        block=projection_block,
                        obligation=obligation,
                    )
                )
                covered.add(obligation_id)

        for atom_id in sorted(traced_atoms):
            linked = obligations_by_atom.get(atom_id, [])
            legacy = [item for item in linked if item.obligation_id == atom_id]
            if legacy:
                for obligation in legacy:
                    if obligation.coverage_status != "testable":
                        findings.append(
                            {
                                "id": "non-testable-obligation-used-as-test",
                                "severity": "error",
                                "tc_id": tc_id,
                                "obligation_id": obligation.obligation_id,
                                "atom_id": atom_id,
                                "coverage_status": obligation.coverage_status,
                                "message": "gap, unclear and not-applicable obligations cannot become executable TC coverage.",
                            }
                        )
                    else:
                        missing_references = missing_obligation_references(
                            obligation, traced_references
                        )
                        if missing_references:
                            findings.append(
                                source_reference_finding(
                                    tc_id=tc_id,
                                    obligation=obligation,
                                    missing_references=missing_references,
                                )
                            )
                        findings.extend(
                            dictionary_projection_findings(
                                tc_id=tc_id,
                                block=projection_block,
                                obligation=obligation,
                            )
                        )
                        findings.extend(
                            reference_fixture_findings(
                                tc_id=tc_id,
                                block=projection_block,
                                obligation=obligation,
                            )
                        )
                        covered.add(obligation.obligation_id)
            elif linked and not any(
                item.obligation_id in traced_obligations for item in linked
            ):
                findings.append(
                    {
                        "id": "atom-without-prepared-obligation",
                        "severity": "error",
                        "tc_id": tc_id,
                        "atom_id": atom_id,
                        "message": "Current prepared-package TC traceability must name the linked OBL as well as the ATOM.",
                    }
                )

    if strict_runtime_contract:
        strict_findings, occurrences = _strict_runtime_contract_findings(
            sections=sections,
            obligations_by_id=obligations_by_id,
        )
        findings.extend(strict_findings)
        covered = _strict_valid_coverage(
            occurrences=occurrences,
            obligations_by_id=obligations_by_id,
            findings=findings,
        )

    for obligation_id in sorted(testable - covered):
        obligation = obligations_by_id[obligation_id]
        findings.append(
            {
                "id": "missing-testable-obligation-coverage",
                "severity": "error",
                "obligation_id": obligation_id,
                "atom_id": obligation.traceability_atom_id,
                "message": "A testable prepared obligation has no TC traceability reference.",
            }
        )

    return ObligationGateResult(
        passed=not findings,
        package_id=obligations.package_id,
        test_case_count=len(sections),
        testable_obligations=len(testable),
        covered_obligations=tuple(sorted(covered)),
        findings=tuple(findings),
        checked_paths=(str(draft_path), str(obligations_path)),
    )
