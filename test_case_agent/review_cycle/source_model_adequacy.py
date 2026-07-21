from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from .prepared_compiler import evaluate_reference_fixture_action_adequacy


VALIDATOR_NAME = "exact-length-source-model-adequacy-v1"
EXACT_LENGTH_RE = re.compile(
    r"\b(?:только|ровно)\s+(?P<length>[1-9][0-9]*)\s+"
    r"(?:числов(?:ых|ого)\s+символ(?:ов|а)|цифр(?:ы|а|у)?)\b",
    re.IGNORECASE,
)
QUOTED_DIGITS_RE = re.compile(
    r"(?:`(?P<backtick>[0-9]+)`|«(?P<guillemet>[0-9]+)»|"
    r"[\"'](?P<quote>[0-9]+)[\"'])"
)
SHORT_CLASS_RE = re.compile(
    r"(?:\bN\s*[-−]\s*1\b|\bкороч\w*\b|\bменьш\w*\b)",
    re.IGNORECASE,
)
LONG_CLASS_RE = re.compile(
    r"(?:\bN\s*\+\s*1\b|\bдлинн\w*\b|\bбольш\w*\b)",
    re.IGNORECASE,
)
REQUIREMENT_CODE_RE = re.compile(r"\b(?:BSR|GSR|DIT)\s+[A-Za-z0-9._/-]+\b")


class SourceModelAdequacyError(ValueError):
    pass


def _load_manifest(value: Path | Mapping[str, Any]) -> Mapping[str, Any]:
    if isinstance(value, Path):
        payload = json.loads(value.read_text(encoding="utf-8"))
    else:
        payload = value
    if not isinstance(payload, Mapping):
        raise SourceModelAdequacyError("source assertion manifest must be an object")
    if not isinstance(payload.get("source_rows"), list):
        raise SourceModelAdequacyError("source assertion manifest misses source_rows")
    if not isinstance(payload.get("assertions"), list):
        raise SourceModelAdequacyError("source assertion manifest misses assertions")
    return payload


def _quoted_digit_values(values: Sequence[Any]) -> tuple[str, ...]:
    result: list[str] = []
    for raw in values:
        if not isinstance(raw, str):
            continue
        for match in QUOTED_DIGITS_RE.finditer(raw):
            value = next(item for item in match.groups() if item is not None)
            if value not in result:
                result.append(value)
    return tuple(result)


def _declared_gap_classes(assertion: Mapping[str, Any]) -> frozenset[str]:
    if assertion.get("semantic_disposition") != "ambiguous" or not assertion.get(
        "primary_gap_id"
    ):
        return frozenset()
    text = " ".join(
        str(value)
        for key in (
            "canonical_statement",
            "disposition_rationale",
            "action_clauses",
            "oracle_clauses",
        )
        for value in (
            assertion.get(key, [])
            if isinstance(assertion.get(key), list)
            else [assertion.get(key, "")]
        )
    )
    result: set[str] = set()
    if SHORT_CLASS_RE.search(text):
        result.add("N-1")
    if LONG_CLASS_RE.search(text):
        result.add("N+1")
    return frozenset(result)


def evaluate_exact_length_adequacy(
    manifest_value: Path | Mapping[str, Any],
) -> dict[str, Any]:
    """Require distinct N, N-1 and N+1 evidence for exact digit lengths."""

    manifest = _load_manifest(manifest_value)
    assertions = tuple(
        item for item in manifest["assertions"] if isinstance(item, Mapping)
    )
    rules: list[dict[str, Any]] = []
    for source_row in manifest["source_rows"]:
        if not isinstance(source_row, Mapping):
            continue
        source_text = str(source_row.get("bounded_source_text", ""))
        length_match = EXACT_LENGTH_RE.search(source_text)
        if length_match is None:
            continue
        exact_length = int(length_match.group("length"))
        source_row_id = str(source_row.get("source_row_id", ""))
        preceding_codes = REQUIREMENT_CODE_RE.findall(
            source_text[: length_match.start()]
        )
        exact_requirement_code = preceding_codes[-1] if preceding_codes else ""
        row_assertions = tuple(
            item
            for item in assertions
            if item.get("source_row_id") == source_row_id
            and (
                not exact_requirement_code
                or exact_requirement_code in item.get("requirement_codes", [])
            )
        )
        evidence: dict[str, list[str]] = {"N": [], "N-1": [], "N+1": []}
        for assertion in row_assertions:
            assertion_id = str(assertion.get("assertion_id", ""))
            values = _quoted_digit_values(assertion.get("action_clauses", []))
            for value in values:
                delta = len(value) - exact_length
                class_id = {0: "N", -1: "N-1", 1: "N+1"}.get(delta)
                if class_id is not None and assertion_id not in evidence[class_id]:
                    evidence[class_id].append(assertion_id)
            for class_id in _declared_gap_classes(assertion):
                marker = f"{assertion_id}:{assertion.get('primary_gap_id')}"
                if marker not in evidence[class_id]:
                    evidence[class_id].append(marker)
        missing = [class_id for class_id, items in evidence.items() if not items]
        requirement_codes = (
            [exact_requirement_code]
            if exact_requirement_code
            else sorted(
                {
                    str(code)
                    for item in row_assertions
                    for code in item.get("requirement_codes", [])
                    if isinstance(code, str) and code.strip()
                }
            )
        )
        rules.append(
            {
                "source_row_id": source_row_id,
                "requirement_codes": requirement_codes,
                "exact_length": exact_length,
                "evidence": evidence,
                "missing_classes": missing,
                "passed": not missing,
            }
        )
    missing_rule_count = sum(not item["passed"] for item in rules)
    return {
        "version": 1,
        "validator": VALIDATOR_NAME,
        "passed": missing_rule_count == 0,
        "rule_count": len(rules),
        "failed_rule_count": missing_rule_count,
        "rules": rules,
    }


def evaluate_pre_review_source_model_adequacy(
    manifest_value: Path | Mapping[str, Any],
    *,
    coverage_obligation_table: Path,
    package_test_design_plan: Path,
    dictionary_inventory: Path | None,
) -> dict[str, Any]:
    """Run every deterministic source-model check before model review."""

    exact_length = evaluate_exact_length_adequacy(manifest_value)
    reference_fixture_actions = evaluate_reference_fixture_action_adequacy(
        manifest_value,
        coverage_obligation_table=coverage_obligation_table,
        package_test_design_plan=package_test_design_plan,
        dictionary_inventory=dictionary_inventory,
    )
    return {
        "version": 2,
        "validator": "pre-review-source-model-adequacy-v2",
        "passed": bool(exact_length["passed"])
        and bool(reference_fixture_actions["passed"]),
        "exact_length": exact_length,
        "reference_fixture_actions": reference_fixture_actions,
    }
