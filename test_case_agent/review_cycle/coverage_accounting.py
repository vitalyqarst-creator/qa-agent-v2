"""Deterministic coverage accounting for prepared obligation sets.

The accounting layer intentionally consumes only small Python objects or mappings.
It does not parse workflow YAML and it does not infer risk from requirement text.
Callers must supply criticality, risk and gap-blocking metadata explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


OVERALL_COVERAGE_FLOOR = "overall-coverage-floor"
ASSERTION_COVERAGE_FLOOR = "assertion-coverage-floor"
CRITICAL_COVERAGE_FLOOR = "critical-coverage-floor"
HIGH_RISK_NONBLOCKING_GAP = "high-risk-nonblocking-gap"
BROAD_PRIMARY_GAP = "broad-primary-gap"
TESTABLE_TO_GAP_REGRESSION = "testable-to-gap-regression"
NEW_GAP_DELTA = "new-gap-delta"

_COUNTED_STATUSES = frozenset({"testable", "gap", "unclear"})
_GAP_STATUSES = frozenset({"gap", "unclear"})
_ALL_STATUSES = _COUNTED_STATUSES | {"not-applicable"}
_RISK_LEVELS = frozenset({"low", "medium", "high", "critical"})
_WAIVABLE_FINDINGS = frozenset(
    {
        HIGH_RISK_NONBLOCKING_GAP,
        TESTABLE_TO_GAP_REGRESSION,
        NEW_GAP_DELTA,
    }
)


@dataclass(frozen=True)
class CoverageObligationMetadata:
    """Explicit policy metadata for one obligation.

    ``critical`` is the caller's classification of a critical user-visible,
    action or source-backed obligation. No text heuristics are applied here.
    ``gap_blocking=False`` means that the linked primary gap is proposed as
    non-blocking. ``assertion_count`` lets a caller declare that one nominal
    obligation still contains more than one clear assertion.
    """

    critical: bool = False
    risk: str = "medium"
    gap_blocking: bool | None = None
    assertion_count: int = 1

    def validate(self) -> None:
        if not isinstance(self.critical, bool):
            raise ValueError("coverage metadata critical must be boolean")
        if self.risk not in _RISK_LEVELS:
            raise ValueError(
                "coverage metadata risk must be one of " + ", ".join(sorted(_RISK_LEVELS))
            )
        if self.gap_blocking is not None and not isinstance(self.gap_blocking, bool):
            raise ValueError("coverage metadata gap_blocking must be boolean or None")
        if (
            not isinstance(self.assertion_count, int)
            or isinstance(self.assertion_count, bool)
            or self.assertion_count < 1
        ):
            raise ValueError("coverage metadata assertion_count must be a positive integer")

    @property
    def is_critical(self) -> bool:
        return self.critical or self.risk == "critical"

    @property
    def is_high_risk(self) -> bool:
        return self.is_critical or self.risk == "high"


@dataclass(frozen=True)
class AcceptedRisk:
    """Finding-specific, subject-specific risk acceptance.

    A record can waive only the finding identified by ``finding_code`` for the
    exact obligation or gap in ``subject_id``. Coverage floors and broad gaps
    are deliberately not waivable through this API.
    """

    finding_code: str
    subject_id: str
    rationale: str

    def validate(self) -> None:
        if self.finding_code not in _WAIVABLE_FINDINGS:
            raise ValueError(
                f"accepted risk cannot waive finding code {self.finding_code!r}"
            )
        if not isinstance(self.subject_id, str) or not self.subject_id.strip():
            raise ValueError("accepted risk subject_id must be non-empty text")
        if not isinstance(self.rationale, str) or not self.rationale.strip():
            raise ValueError("accepted risk rationale must be non-empty text")

    def to_dict(self) -> dict[str, str]:
        return {
            "finding_code": self.finding_code,
            "subject_id": self.subject_id,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class CoverageCounts:
    testable: int
    gap: int
    unclear: int
    not_applicable: int

    @property
    def denominator(self) -> int:
        return self.testable + self.gap + self.unclear

    @property
    def ratio(self) -> float:
        if self.denominator == 0:
            return 1.0
        return self.testable / self.denominator

    def to_dict(self) -> dict[str, int | float]:
        return {
            "testable": self.testable,
            "gap": self.gap,
            "unclear": self.unclear,
            "not_applicable": self.not_applicable,
            "denominator": self.denominator,
            "ratio": self.ratio,
        }


@dataclass(frozen=True)
class CoverageFinding:
    code: str
    message: str
    obligation_ids: tuple[str, ...] = ()
    assertion_ids: tuple[str, ...] = ()
    gap_ids: tuple[str, ...] = ()
    accepted_risk: AcceptedRisk | None = None

    @property
    def blocking(self) -> bool:
        return self.accepted_risk is None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "obligation_ids": list(self.obligation_ids),
            "assertion_ids": list(self.assertion_ids),
            "gap_ids": list(self.gap_ids),
            "blocking": self.blocking,
            "accepted_risk": (
                self.accepted_risk.to_dict() if self.accepted_risk is not None else None
            ),
        }


@dataclass(frozen=True)
class CoverageAccountingResult:
    passed: bool
    counts: CoverageCounts
    critical_counts: CoverageCounts
    assertion_counts: CoverageCounts
    overall_floor: float
    critical_floor: float
    assertion_floor: float
    determinacy_floor_enforced: bool
    findings: tuple[CoverageFinding, ...]

    @property
    def ratio(self) -> float:
        return self.counts.ratio

    @property
    def critical_ratio(self) -> float:
        return self.critical_counts.ratio

    @property
    def assertion_ratio(self) -> float:
        return self.assertion_counts.ratio

    @property
    def finding_codes(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(item.code for item in self.findings))

    @property
    def blocking_finding_codes(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(item.code for item in self.findings if item.blocking)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "counts": self.counts.to_dict(),
            "ratio": self.ratio,
            "overall_floor": self.overall_floor,
            "critical_counts": self.critical_counts.to_dict(),
            "critical_ratio": self.critical_ratio,
            "critical_floor": self.critical_floor,
            "assertion_counts": self.assertion_counts.to_dict(),
            "assertion_ratio": self.assertion_ratio,
            "assertion_floor": self.assertion_floor,
            "determinacy_policy": (
                "release-floor"
                if self.determinacy_floor_enforced
                else "descriptive-only"
            ),
            "determinacy_floor_enforced": self.determinacy_floor_enforced,
            "finding_codes": list(self.finding_codes),
            "blocking_finding_codes": list(self.blocking_finding_codes),
            "findings": [item.to_dict() for item in self.findings],
        }


@dataclass(frozen=True)
class _ObligationView:
    obligation_id: str
    coverage_status: str
    gap_id: str
    constraint_gap_ids: tuple[str, ...]


def _field(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _obligation_view(value: Any) -> _ObligationView:
    obligation_id = _field(value, "obligation_id")
    coverage_status = _field(value, "coverage_status")
    gap_id = _field(value, "gap_id", "")
    constraint_gap_ids = _field(value, "constraint_gap_ids", ())
    if not isinstance(obligation_id, str) or not obligation_id.strip():
        raise ValueError("obligation_id must be non-empty text")
    if coverage_status not in _ALL_STATUSES:
        raise ValueError(
            f"{obligation_id}.coverage_status must be one of {sorted(_ALL_STATUSES)}"
        )
    if coverage_status in _GAP_STATUSES and (
        not isinstance(gap_id, str) or not gap_id.strip()
    ):
        raise ValueError(f"{obligation_id} gap/unclear obligation must declare gap_id")
    if coverage_status not in _GAP_STATUSES:
        gap_id = ""
    if not isinstance(constraint_gap_ids, (list, tuple)) or any(
        not isinstance(item, str) or not item.strip()
        for item in constraint_gap_ids
    ):
        raise ValueError(
            f"{obligation_id}.constraint_gap_ids must be a sequence of non-empty text"
        )
    normalized_constraints = tuple(item.strip() for item in constraint_gap_ids)
    if len(normalized_constraints) != len(set(normalized_constraints)):
        raise ValueError(f"{obligation_id}.constraint_gap_ids must not contain duplicates")
    return _ObligationView(
        obligation_id,
        coverage_status,
        gap_id,
        normalized_constraints,
    )


def _obligation_index(values: Sequence[Any], label: str) -> dict[str, _ObligationView]:
    result: dict[str, _ObligationView] = {}
    for value in values:
        item = _obligation_view(value)
        if item.obligation_id in result:
            raise ValueError(f"duplicate {label} obligation_id: {item.obligation_id}")
        result[item.obligation_id] = item
    return result


def _metadata_value(
    value: CoverageObligationMetadata | Mapping[str, Any],
) -> CoverageObligationMetadata:
    if isinstance(value, CoverageObligationMetadata):
        result = value
    elif isinstance(value, Mapping):
        allowed = {"critical", "risk", "gap_blocking", "assertion_count"}
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"unknown coverage metadata fields: {unknown}")
        result = CoverageObligationMetadata(**value)
    else:
        raise ValueError("coverage metadata must be a mapping or CoverageObligationMetadata")
    result.validate()
    return result


def _accepted_risk_value(value: AcceptedRisk | Mapping[str, Any]) -> AcceptedRisk:
    if isinstance(value, AcceptedRisk):
        result = value
    elif isinstance(value, Mapping):
        allowed = {"finding_code", "subject_id", "rationale"}
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise ValueError(f"unknown accepted risk fields: {unknown}")
        try:
            result = AcceptedRisk(
                finding_code=value["finding_code"],
                subject_id=value["subject_id"],
                rationale=value["rationale"],
            )
        except KeyError as exc:
            raise ValueError(f"accepted risk is missing field {exc.args[0]}") from exc
    else:
        raise ValueError("accepted risk must be a mapping or AcceptedRisk")
    result.validate()
    return result


def _counts(
    obligations: Sequence[_ObligationView],
) -> CoverageCounts:
    return CoverageCounts(
        testable=sum(item.coverage_status == "testable" for item in obligations),
        gap=sum(item.coverage_status == "gap" for item in obligations),
        unclear=sum(item.coverage_status == "unclear" for item in obligations),
        not_applicable=sum(
            item.coverage_status == "not-applicable" for item in obligations
        ),
    )


def _assertion_counts(
    values: Mapping[str, str],
) -> CoverageCounts:
    return CoverageCounts(
        testable=sum(status == "testable" for status in values.values()),
        gap=sum(status == "gap" for status in values.values()),
        unclear=sum(status == "unclear" for status in values.values()),
        not_applicable=sum(
            status == "not-applicable" for status in values.values()
        ),
    )


def evaluate_coverage_accounting(
    obligations: Sequence[Any],
    *,
    metadata: Mapping[
        str, CoverageObligationMetadata | Mapping[str, Any]
    ] | None = None,
    baseline_obligations: Sequence[Any] | None = None,
    accepted_risks: Sequence[AcceptedRisk | Mapping[str, Any]] = (),
    assertion_coverage: Mapping[str, str] | None = None,
    constraint_gap_blocking: Mapping[str, bool] | None = None,
    overall_floor: float = 0.85,
    critical_floor: float = 1.0,
    assertion_floor: float | None = None,
    enforce_determinacy_floors: bool = False,
) -> CoverageAccountingResult:
    """Evaluate descriptive determinacy ratios and release guardrails.

    The denominator is ``testable + gap + unclear``. ``not-applicable`` rows are
    reported but excluded.  The resulting ratio describes how much of the source
    model was declared testable; it is not evidence that testable assertions were
    covered and therefore is not a production release floor by default.  Exact
    source/assertion/obligation completeness is enforced by the source-first
    compiler contract.  ``enforce_determinacy_floors`` exists only for explicit
    legacy/diagnostic policy checks.

    Baseline checks run only when ``baseline_obligations`` is supplied; passing
    an empty sequence therefore declares an empty baseline.
    """

    if not isinstance(enforce_determinacy_floors, bool):
        raise ValueError("enforce_determinacy_floors must be boolean")

    if assertion_floor is None:
        assertion_floor = overall_floor
    for value, name in (
        (overall_floor, "overall_floor"),
        (critical_floor, "critical_floor"),
        (assertion_floor, "assertion_floor"),
    ):
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not 0.0 <= float(value) <= 1.0
        ):
            raise ValueError(f"{name} must be a number between 0.0 and 1.0")
    overall_floor = float(overall_floor)
    critical_floor = float(critical_floor)
    assertion_floor = float(assertion_floor)

    current = _obligation_index(obligations, "current")
    if assertion_coverage is None:
        normalized_assertion_coverage = {
            obligation_id: item.coverage_status
            for obligation_id, item in current.items()
        }
    else:
        if not isinstance(assertion_coverage, Mapping):
            raise ValueError("assertion_coverage must be a mapping")
        normalized_assertion_coverage: dict[str, str] = {}
        for assertion_id, status in assertion_coverage.items():
            if not isinstance(assertion_id, str) or not assertion_id.strip():
                raise ValueError("assertion_coverage keys must be non-empty text")
            if status not in _ALL_STATUSES:
                raise ValueError(
                    f"{assertion_id} assertion coverage must be one of "
                    f"{sorted(_ALL_STATUSES)}"
                )
            normalized_assertion_coverage[assertion_id.strip()] = status
        if not normalized_assertion_coverage:
            raise ValueError("assertion_coverage must not be empty")
    normalized_constraint_gap_blocking: dict[str, bool] = {}
    for gap_id, blocking in (constraint_gap_blocking or {}).items():
        if not isinstance(gap_id, str) or not gap_id.strip():
            raise ValueError("constraint_gap_blocking keys must be non-empty text")
        if not isinstance(blocking, bool):
            raise ValueError("constraint_gap_blocking values must be boolean")
        normalized_constraint_gap_blocking[gap_id.strip()] = blocking
    normalized_metadata = {
        obligation_id: _metadata_value(value)
        for obligation_id, value in (metadata or {}).items()
    }
    default_metadata = CoverageObligationMetadata()

    risk_index: dict[tuple[str, str], AcceptedRisk] = {}
    for value in accepted_risks:
        risk = _accepted_risk_value(value)
        key = (risk.finding_code, risk.subject_id)
        if key in risk_index:
            raise ValueError(
                "duplicate accepted risk for "
                f"finding_code={risk.finding_code}, subject_id={risk.subject_id}"
            )
        risk_index[key] = risk

    current_values = tuple(current.values())
    counts = _counts(current_values)
    assertion_counts = _assertion_counts(normalized_assertion_coverage)
    critical_values = tuple(
        item
        for item in current_values
        if normalized_metadata.get(item.obligation_id, default_metadata).is_critical
    )
    critical_counts = _counts(critical_values)
    findings: list[CoverageFinding] = []

    if enforce_determinacy_floors and counts.ratio + 1e-12 < overall_floor:
        findings.append(
            CoverageFinding(
                code=OVERALL_COVERAGE_FLOOR,
                message=(
                    f"coverage ratio {counts.ratio:.6f} is below required floor "
                    f"{overall_floor:.6f}"
                ),
                obligation_ids=tuple(current),
            )
        )

    if (
        enforce_determinacy_floors
        and assertion_counts.ratio + 1e-12 < assertion_floor
    ):
        findings.append(
            CoverageFinding(
                code=ASSERTION_COVERAGE_FLOOR,
                message=(
                    f"assertion coverage ratio {assertion_counts.ratio:.6f} is below "
                    f"required floor {assertion_floor:.6f}"
                ),
                assertion_ids=tuple(
                    assertion_id
                    for assertion_id, status in normalized_assertion_coverage.items()
                    if status != "testable"
                ),
            )
        )

    if critical_counts.ratio + 1e-12 < critical_floor:
        findings.append(
            CoverageFinding(
                code=CRITICAL_COVERAGE_FLOOR,
                message=(
                    f"critical coverage ratio {critical_counts.ratio:.6f} is below "
                    f"required floor {critical_floor:.6f}"
                ),
                obligation_ids=tuple(
                    item.obligation_id
                    for item in critical_values
                    if item.coverage_status != "testable"
                ),
                gap_ids=tuple(
                    dict.fromkeys(
                        item.gap_id
                        for item in critical_values
                        if item.coverage_status in _GAP_STATUSES
                    )
                ),
            )
        )

    gap_groups: dict[str, list[_ObligationView]] = {}
    for item in current_values:
        missing_constraint_classifications = sorted(
            set(item.constraint_gap_ids) - set(normalized_constraint_gap_blocking)
        )
        if missing_constraint_classifications:
            raise ValueError(
                f"{item.obligation_id} constraint gaps require explicit blocking "
                "classification: " + ", ".join(missing_constraint_classifications)
            )
        item_metadata = normalized_metadata.get(item.obligation_id, default_metadata)
        if item_metadata.is_high_risk:
            for constraint_gap_id in item.constraint_gap_ids:
                if normalized_constraint_gap_blocking[constraint_gap_id]:
                    continue
                accepted = risk_index.get(
                    (HIGH_RISK_NONBLOCKING_GAP, constraint_gap_id)
                )
                findings.append(
                    CoverageFinding(
                        code=HIGH_RISK_NONBLOCKING_GAP,
                        message=(
                            "high-risk constraint gap cannot be treated as "
                            "non-blocking without a finding-specific accepted risk"
                        ),
                        obligation_ids=(item.obligation_id,),
                        gap_ids=(constraint_gap_id,),
                        accepted_risk=accepted,
                    )
                )
        if item.coverage_status not in _GAP_STATUSES:
            continue
        if item_metadata.is_high_risk and item_metadata.gap_blocking is False:
            accepted = risk_index.get((HIGH_RISK_NONBLOCKING_GAP, item.obligation_id))
            findings.append(
                CoverageFinding(
                    code=HIGH_RISK_NONBLOCKING_GAP,
                    message=(
                        "high-risk gap cannot be treated as non-blocking without "
                        "a finding-specific accepted risk"
                    ),
                    obligation_ids=(item.obligation_id,),
                    gap_ids=(item.gap_id,),
                    accepted_risk=accepted,
                )
            )
        gap_groups.setdefault(item.gap_id, []).append(item)

    for gap_id, items in gap_groups.items():
        assertion_count = sum(
            normalized_metadata.get(item.obligation_id, default_metadata).assertion_count
            for item in items
        )
        if assertion_count > 1:
            findings.append(
                CoverageFinding(
                    code=BROAD_PRIMARY_GAP,
                    message=(
                        f"primary gap {gap_id} suppresses {assertion_count} clear assertions; "
                        "split it into narrow independently reviewable gaps"
                    ),
                    obligation_ids=tuple(item.obligation_id for item in items),
                    gap_ids=(gap_id,),
                )
            )

    if baseline_obligations is not None:
        baseline = _obligation_index(baseline_obligations, "baseline")
        for item in current_values:
            if item.coverage_status not in _GAP_STATUSES:
                continue
            previous = baseline.get(item.obligation_id)
            if previous is not None and previous.coverage_status == "testable":
                accepted = risk_index.get(
                    (TESTABLE_TO_GAP_REGRESSION, item.obligation_id)
                )
                findings.append(
                    CoverageFinding(
                        code=TESTABLE_TO_GAP_REGRESSION,
                        message=(
                            f"{item.obligation_id} regressed from testable to "
                            f"{item.coverage_status}"
                        ),
                        obligation_ids=(item.obligation_id,),
                        gap_ids=(item.gap_id,),
                        accepted_risk=accepted,
                    )
                )
                continue

            is_new_gap = previous is None or previous.coverage_status == "not-applicable"
            if (
                previous is not None
                and previous.coverage_status in _GAP_STATUSES
                and previous.gap_id != item.gap_id
            ):
                is_new_gap = True
            if is_new_gap:
                accepted = risk_index.get((NEW_GAP_DELTA, item.obligation_id))
                findings.append(
                    CoverageFinding(
                        code=NEW_GAP_DELTA,
                        message=f"{item.obligation_id} introduces new primary gap {item.gap_id}",
                        obligation_ids=(item.obligation_id,),
                        gap_ids=(item.gap_id,),
                        accepted_risk=accepted,
                    )
                )

    result_findings = tuple(findings)
    return CoverageAccountingResult(
        passed=not any(item.blocking for item in result_findings),
        counts=counts,
        critical_counts=critical_counts,
        assertion_counts=assertion_counts,
        overall_floor=overall_floor,
        critical_floor=critical_floor,
        assertion_floor=assertion_floor,
        determinacy_floor_enforced=enforce_determinacy_floors,
        findings=result_findings,
    )
