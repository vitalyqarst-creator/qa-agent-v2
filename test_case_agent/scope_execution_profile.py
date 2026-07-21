from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Mapping, Sequence


LEAN_MAX_SOURCE_ROWS = 12
LEAN_MAX_EXPECTED_ASSERTIONS = 10
LEAN_MAX_EXPECTED_TEST_CASES = 14
LEAN_MAX_INTERNAL_PACKAGES = 1

LEAN_PROFILE = "lean-production"
STANDARD_PROFILE = "standard-production"

_LEAN_SCOPE_KINDS = frozenset({"single-section", "contiguous-bounded-fragment"})
_REQUIRED_FACTS = (
    "bounded_scope_kind",
    "expected_testable_assertion_count",
    "expected_tc_count",
    "internal_package_count",
    "has_heterogeneous_integrations",
    "has_large_dictionary",
    "mockups_ready",
)


class ScopeExecutionProfileError(ValueError):
    pass


@dataclass(frozen=True)
class ScopeExecutionProfile:
    version: int
    requested_profile: str
    selected_profile: str
    lean_eligible: bool
    default_contract_version: int
    effective_contract_version: int
    semantic_design_bridge_required: bool
    source_row_count: int
    requirement_code_count: int
    expected_assertion_count: int | None
    expected_test_case_count: int | None
    internal_package_count: int | None
    violations: tuple[dict[str, Any], ...]
    unknown_criteria: tuple[str, ...]

    @property
    def route_action(self) -> str:
        if self.selected_profile == LEAN_PROFILE:
            return "invoke-lean-detailed-v1"
        if self.effective_contract_version == 2:
            return "invoke-standard-scope-boundary-v2"
        return "semantic-design-bridge-required"

    def with_contract_version(self, contract_version: int | None) -> "ScopeExecutionProfile":
        effective = self.default_contract_version if contract_version is None else contract_version
        if effective not in (1, 2):
            raise ScopeExecutionProfileError("contract version must be 1 or 2")
        if self.selected_profile == LEAN_PROFILE and effective != 1:
            raise ScopeExecutionProfileError(
                "lean-production requires detailed contract version 1"
            )
        return replace(self, effective_contract_version=effective)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "requested_profile": self.requested_profile,
            "selected_profile": self.selected_profile,
            "lean_eligible": self.lean_eligible,
            "default_contract_version": self.default_contract_version,
            "effective_contract_version": self.effective_contract_version,
            "semantic_design_bridge_required": self.semantic_design_bridge_required,
            "limits": {
                "source_row_count": LEAN_MAX_SOURCE_ROWS,
                "expected_testable_assertion_count": LEAN_MAX_EXPECTED_ASSERTIONS,
                "expected_tc_count": LEAN_MAX_EXPECTED_TEST_CASES,
                "internal_package_count": LEAN_MAX_INTERNAL_PACKAGES,
            },
            "observed": {
                "source_row_count": self.source_row_count,
                "expected_testable_assertion_count": self.expected_assertion_count,
                "expected_tc_count": self.expected_test_case_count,
                "internal_package_count": self.internal_package_count,
            },
            "diagnostics": {
                "unique_requirement_code_count": self.requirement_code_count,
            },
            "violations": [dict(item) for item in self.violations],
            "unknown_criteria": list(self.unknown_criteria),
            "route_action": self.route_action,
        }


def select_scope_execution_profile(
    context: Mapping[str, Any],
    *,
    requested_profile: str = "auto",
    contract_version: int | None = None,
) -> ScopeExecutionProfile:
    if requested_profile not in {"auto", LEAN_PROFILE, STANDARD_PROFILE}:
        raise ScopeExecutionProfileError(
            f"requested profile must be auto, {LEAN_PROFILE} or {STANDARD_PROFILE}"
        )
    rows = context.get("source_rows")
    if (
        not isinstance(rows, list)
        or not rows
        or any(not isinstance(row, Mapping) for row in rows)
    ):
        raise ScopeExecutionProfileError(
            "context.source_rows must be a non-empty object array"
        )
    facts_value = context.get("scope_execution_facts")
    if facts_value is None:
        facts: Mapping[str, Any] = {}
    elif isinstance(facts_value, Mapping):
        facts = facts_value
        if facts.get("version") != 1:
            raise ScopeExecutionProfileError("scope_execution_facts.version must equal 1")
    else:
        raise ScopeExecutionProfileError("scope_execution_facts must be an object")

    source_row_count = len(rows)
    expected_assertions = _optional_nonnegative_int(
        facts.get("expected_testable_assertion_count"),
        "scope_execution_facts.expected_testable_assertion_count",
    )
    expected_test_cases = _optional_nonnegative_int(
        facts.get("expected_tc_count"),
        "scope_execution_facts.expected_tc_count",
    )
    internal_package_count = _optional_nonnegative_int(
        facts.get("internal_package_count"),
        "scope_execution_facts.internal_package_count",
    )
    violations: list[dict[str, Any]] = []
    if source_row_count > LEAN_MAX_SOURCE_ROWS:
        violations.append(
            _limit_violation(
                "source-row-limit-exceeded", source_row_count, LEAN_MAX_SOURCE_ROWS
            )
        )
    if (
        expected_assertions is not None
        and expected_assertions > LEAN_MAX_EXPECTED_ASSERTIONS
    ):
        violations.append(
            _limit_violation(
                "expected-assertion-limit-exceeded",
                expected_assertions,
                LEAN_MAX_EXPECTED_ASSERTIONS,
            )
        )
    if (
        expected_test_cases is not None
        and expected_test_cases > LEAN_MAX_EXPECTED_TEST_CASES
    ):
        violations.append(
            _limit_violation(
                "expected-tc-limit-exceeded",
                expected_test_cases,
                LEAN_MAX_EXPECTED_TEST_CASES,
            )
        )
    if internal_package_count is not None and internal_package_count != 1:
        violations.append(
            {
                "code": "internal-package-count-not-one",
                "actual": internal_package_count,
                "required": 1,
            }
        )

    scope_kind = facts.get("bounded_scope_kind")
    if scope_kind is not None:
        if not isinstance(scope_kind, str) or not scope_kind.strip():
            raise ScopeExecutionProfileError(
                "scope_execution_facts.bounded_scope_kind must be a non-empty string"
            )
        if scope_kind not in _LEAN_SCOPE_KINDS:
            violations.append(
                {
                    "code": "scope-kind-not-lean-eligible",
                    "actual": scope_kind,
                    "allowed": sorted(_LEAN_SCOPE_KINDS),
                }
            )
    _append_boolean_violation(
        facts,
        "has_heterogeneous_integrations",
        disallowed=True,
        code="heterogeneous-integrations-present",
        violations=violations,
    )
    _append_boolean_violation(
        facts,
        "has_large_dictionary",
        disallowed=True,
        code="large-dictionary-present",
        violations=violations,
    )
    _append_boolean_violation(
        facts,
        "mockups_ready",
        disallowed=False,
        code="mockups-not-ready",
        violations=violations,
    )
    declared_reasons = facts.get("standard_profile_reasons", [])
    if not isinstance(declared_reasons, Sequence) or isinstance(declared_reasons, str):
        raise ScopeExecutionProfileError(
            "scope_execution_facts.standard_profile_reasons must be a string array"
        )
    for reason in declared_reasons:
        if not isinstance(reason, str) or not reason.strip():
            raise ScopeExecutionProfileError(
                "scope_execution_facts.standard_profile_reasons must contain non-empty strings"
            )
        violations.append(
            {"code": "declared-standard-reason", "reason": reason.strip()}
        )

    unknown_criteria = tuple(
        key for key in _REQUIRED_FACTS if key not in facts or facts[key] is None
    )
    lean_eligible = not violations and not unknown_criteria
    selected = (
        LEAN_PROFILE
        if lean_eligible
        and requested_profile in {"auto", LEAN_PROFILE}
        else STANDARD_PROFILE
    )
    default_contract = 1 if selected == LEAN_PROFILE else 2
    profile = ScopeExecutionProfile(
        version=1,
        requested_profile=requested_profile,
        selected_profile=selected,
        lean_eligible=lean_eligible,
        default_contract_version=default_contract,
        effective_contract_version=default_contract,
        semantic_design_bridge_required=(selected == STANDARD_PROFILE),
        source_row_count=source_row_count,
        requirement_code_count=len(_requirement_codes(rows)),
        expected_assertion_count=expected_assertions,
        expected_test_case_count=expected_test_cases,
        internal_package_count=internal_package_count,
        violations=tuple(violations),
        unknown_criteria=unknown_criteria,
    )
    return profile.with_contract_version(contract_version)


def _limit_violation(code: str, actual: int, limit: int) -> dict[str, Any]:
    return {"code": code, "actual": actual, "limit": limit}


def _append_boolean_violation(
    facts: Mapping[str, Any],
    key: str,
    *,
    disallowed: bool,
    code: str,
    violations: list[dict[str, Any]],
) -> None:
    if key not in facts or facts[key] is None:
        return
    value = facts[key]
    if type(value) is not bool:
        raise ScopeExecutionProfileError(f"scope_execution_facts.{key} must be boolean")
    if value is disallowed:
        violations.append({"code": code, "actual": value})


def _requirement_codes(rows: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        raw_codes = row.get("requirement_codes_hint", [])
        if not isinstance(raw_codes, list) or any(not isinstance(code, str) for code in raw_codes):
            raise ScopeExecutionProfileError(
                f"context.source_rows[{index}].requirement_codes_hint must be a string array"
            )
        for code in raw_codes:
            normalized = code.strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                result.append(normalized)
    return tuple(result)


def _optional_nonnegative_int(value: Any, label: str) -> int | None:
    if value is None:
        return None
    if type(value) is not int or value < 0:
        raise ScopeExecutionProfileError(f"{label} must be a non-negative integer")
    return value


__all__ = [
    "LEAN_MAX_EXPECTED_ASSERTIONS",
    "LEAN_MAX_EXPECTED_TEST_CASES",
    "LEAN_MAX_INTERNAL_PACKAGES",
    "LEAN_MAX_SOURCE_ROWS",
    "LEAN_PROFILE",
    "STANDARD_PROFILE",
    "ScopeExecutionProfile",
    "ScopeExecutionProfileError",
    "select_scope_execution_profile",
]
