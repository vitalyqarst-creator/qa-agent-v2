from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from test_case_agent.case_identity import assign_stable_ids, semantic_case_key
from test_case_agent.review_cycle.prepared_package import PreparedObligationSet
from test_case_agent.review_cycle.source_assertions import SourceAssertionManifest


class CoverageGraphError(ValueError):
    """The compiler/source projection is incomplete or internally inconsistent."""


_REQ_CODE = re.compile(r"\b(?:BSR|GSR|DIT)\s+[A-Za-z0-9._/-]+\b", re.IGNORECASE)
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]*")
_PROPERTY_DISPOSITIONS = {"tc", "gap", "not-applicable"}
_CASE_STATUSES = {"executable", "candidate-ui-calibration"}
_SHA256 = re.compile(r"[0-9a-f]{64}")


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _typed_key(value: str, label: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise CoverageGraphError(f"{label} must be a stable typed key")
    return value


@dataclass(frozen=True)
class PropertyDerivation:
    source_manifest_digest: str
    obligation_set_digest: str
    assertion_id: str
    source_row_id: str
    atom_id: str
    source_text_sha256: str
    property_key: str
    subject_key: str
    property_kind: str
    obligation_variants: Mapping[str, str]
    condition_key: str = "always"
    validation_trigger: str = ""
    cleanup_strategy: str = ""
    source_oracle_ids: Mapping[str, str] | None = None
    fixture_values: Mapping[str, Sequence[str]] | None = None
    calibration_questions: Mapping[str, str] | None = None

    def validate(self) -> None:
        for value, label in (
            (self.assertion_id, "assertion_id"),
            (self.property_key, "property_key"),
            (self.subject_key, "subject_key"),
            (self.property_kind, "property_kind"),
            (self.condition_key, "condition_key"),
            (self.source_row_id, "source_row_id"),
            (self.atom_id, "atom_id"),
        ):
            _typed_key(value, label)
        for value, label in (
            (self.source_manifest_digest, "source_manifest_digest"),
            (self.obligation_set_digest, "obligation_set_digest"),
            (self.source_text_sha256, "source_text_sha256"),
        ):
            if _SHA256.fullmatch(value) is None:
                raise CoverageGraphError(f"{label} must be a lowercase SHA-256")
        if not self.obligation_variants:
            raise CoverageGraphError(
                f"{self.assertion_id} derivation must map at least one obligation"
            )
        for obligation_id, variant in self.obligation_variants.items():
            _typed_key(obligation_id, "obligation_variants key")
            _typed_key(variant, "coverage_variant")


@dataclass(frozen=True)
class CoverageProperty:
    property_id: str
    assertion_id: str
    property_key: str
    subject_key: str
    property_kind: str
    source_row_id: str
    source_path: str
    source_locator: str
    source_text_sha256: str
    canonical_statement: str
    requirement_codes: tuple[str, ...]
    disposition: str
    condition_clauses: tuple[str, ...] = ()
    polarity: str = "neutral"


@dataclass(frozen=True)
class CoverageObligation:
    obligation_id: str
    property_id: str
    atom_id: str
    coverage_variant: str
    condition_key: str
    atomic_statement: str
    observable_oracle: str
    coverage_status: str
    requirement_codes: tuple[str, ...]
    gap_id: str
    calibration_status: str
    validation_trigger: str
    cleanup_strategy: str
    source_oracle_id: str
    fixture_values: tuple[str, ...]
    calibration_question: str


@dataclass(frozen=True)
class CoverageCase:
    case_key: str
    tc_id: str
    obligation_ids: tuple[str, ...]
    status: str


@dataclass(frozen=True)
class CoverageGap:
    gap_id: str
    property_ids: tuple[str, ...]
    obligation_ids: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class CoverageGraph:
    schema_version: int
    ft_slug: str
    scope_slug: str
    source_manifest_digest: str
    obligation_set_digest: str
    properties: tuple[CoverageProperty, ...]
    obligations: tuple[CoverageObligation, ...]
    cases: tuple[CoverageCase, ...]
    gaps: tuple[CoverageGap, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def digest(self) -> str:
        return _digest(self.to_dict())


@dataclass(frozen=True)
class CoverageFinding:
    finding_id: str
    severity: str
    property_id: str = ""
    obligation_id: str = ""
    tc_id: str = ""
    message: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def _manifest_digest(manifest: SourceAssertionManifest) -> str:
    return _digest(manifest.to_dict())


def _assertion_disposition(semantic_disposition: str) -> str:
    if semantic_disposition == "testable":
        return "tc"
    if semantic_disposition == "ambiguous":
        return "gap"
    if semantic_disposition == "not-applicable":
        return "not-applicable"
    raise CoverageGraphError(
        f"unsupported source assertion disposition: {semantic_disposition}"
    )


def _codes_in_refs(source_refs: Sequence[str]) -> tuple[str, ...]:
    values: list[str] = []
    for source_ref in source_refs:
        values.extend(match.group(0).upper() for match in _REQ_CODE.finditer(source_ref))
    return tuple(dict.fromkeys(values))


def build_coverage_graph(
    *,
    ft_slug: str,
    tc_prefix: str,
    source_manifest: SourceAssertionManifest,
    obligation_set: PreparedObligationSet,
    derivations: Sequence[PropertyDerivation],
) -> CoverageGraph:
    """Build one fail-closed projection over already validated compiler contracts.

    The graph intentionally does not parse FT prose or invent property kinds. Every
    testable assertion requires an explicit typed derivation bound to its existing
    ASSERT/ATOM/OBL chain.
    """

    # SourceAssertionManifest validation needs repository files and an accepted
    # receipt. The orchestration boundary owns that check before calling this
    # pure projection builder; repeating it here would make the graph a second
    # source-validation workflow.
    obligation_set.validate()
    manifest_digest = _manifest_digest(source_manifest)
    derivation_by_assertion: dict[str, PropertyDerivation] = {}
    for derivation in derivations:
        derivation.validate()
        if derivation.source_manifest_digest != manifest_digest:
            raise CoverageGraphError(
                f"{derivation.assertion_id} derivation is stale for this source manifest"
            )
        if derivation.obligation_set_digest != obligation_set.digest:
            raise CoverageGraphError(
                f"{derivation.assertion_id} derivation is stale for this obligation set"
            )
        if derivation.assertion_id in derivation_by_assertion:
            raise CoverageGraphError(
                f"duplicate derivation for {derivation.assertion_id}"
            )
        derivation_by_assertion[derivation.assertion_id] = derivation

    assertions = {item.assertion_id: item for item in source_manifest.assertions}
    unknown_derivations = set(derivation_by_assertion) - set(assertions)
    if unknown_derivations:
        raise CoverageGraphError(
            "derivations reference unknown assertions: "
            + ", ".join(sorted(unknown_derivations))
        )
    prepared = {item.obligation_id: item for item in obligation_set.obligations}
    mapped_obligations: dict[str, str] = {}
    properties: list[CoverageProperty] = []
    obligations: list[CoverageObligation] = []
    case_specs: list[tuple[str, str, str]] = []
    gap_properties: dict[str, list[str]] = {}
    gap_obligations: dict[str, list[str]] = {}
    property_keys: set[str] = set()

    for assertion in source_manifest.assertions:
        disposition = _assertion_disposition(assertion.semantic_disposition)
        derivation = derivation_by_assertion.get(assertion.assertion_id)
        if assertion.semantic_disposition == "testable" and derivation is None:
            raise CoverageGraphError(
                f"testable assertion {assertion.assertion_id} has no typed derivation"
            )
        if derivation is None:
            property_key = f"context:{assertion.assertion_id}"
            subject_key = assertion.source_row_id
            property_kind = "context"
            condition_key = "always"
        else:
            property_key = derivation.property_key
            subject_key = derivation.subject_key
            property_kind = derivation.property_kind
            condition_key = derivation.condition_key
        if property_key in property_keys:
            raise CoverageGraphError(f"duplicate property_key: {property_key}")
        property_keys.add(property_key)
        property_id = "PROP-" + hashlib.sha256(
            f"{source_manifest.scope_slug}|{property_key}".encode("utf-8")
        ).hexdigest()[:16].upper()
        codes = tuple(assertion.requirement_codes)
        properties.append(
            CoverageProperty(
                property_id=property_id,
                assertion_id=assertion.assertion_id,
                property_key=property_key,
                subject_key=subject_key,
                property_kind=property_kind,
                source_row_id=assertion.source_row_id,
                source_path=assertion.source_path,
                source_locator=assertion.locator,
                source_text_sha256=hashlib.sha256(
                    assertion.exact_source_text.encode("utf-8")
                ).hexdigest(),
                canonical_statement=assertion.canonical_statement,
                requirement_codes=codes,
                disposition=disposition,
                condition_clauses=tuple(
                    getattr(assertion, "condition_clauses", ())
                ),
                polarity=getattr(assertion, "polarity", "neutral"),
            )
        )
        if disposition == "gap" and assertion.primary_gap_id:
            gap_properties.setdefault(assertion.primary_gap_id, []).append(property_id)
        if disposition != "tc":
            if assertion.obligation_ids:
                raise CoverageGraphError(
                    f"non-testable assertion {assertion.assertion_id} declares obligations"
                )
            continue
        assert derivation is not None
        if derivation.source_row_id != assertion.source_row_id:
            raise CoverageGraphError(
                f"{assertion.assertion_id} derivation source_row_id mismatch"
            )
        if derivation.atom_id != assertion.atom_id:
            raise CoverageGraphError(
                f"{assertion.assertion_id} derivation atom_id mismatch"
            )
        exact_source_sha256 = hashlib.sha256(
            assertion.exact_source_text.encode("utf-8")
        ).hexdigest()
        if derivation.source_text_sha256 != exact_source_sha256:
            raise CoverageGraphError(
                f"{assertion.assertion_id} derivation exact source hash mismatch"
            )
        if set(assertion.obligation_ids) != set(derivation.obligation_variants):
            raise CoverageGraphError(
                f"{assertion.assertion_id} derivation must map its obligations exactly"
            )
        for obligation_id in assertion.obligation_ids:
            if obligation_id in mapped_obligations:
                raise CoverageGraphError(
                    f"obligation {obligation_id} is mapped by multiple properties"
                )
            item = prepared.get(obligation_id)
            if item is None:
                raise CoverageGraphError(
                    f"assertion {assertion.assertion_id} references missing {obligation_id}"
                )
            mapped_obligations[obligation_id] = property_id
            inherited_codes = _codes_in_refs(item.source_refs)
            foreign_codes = set(inherited_codes) - set(codes)
            if foreign_codes:
                raise CoverageGraphError(
                    f"{obligation_id} inherits foreign requirement codes: "
                    + ", ".join(sorted(foreign_codes))
                )
            variant = derivation.obligation_variants[obligation_id]
            source_oracle_id = (derivation.source_oracle_ids or {}).get(obligation_id, "")
            fixture_values = tuple((derivation.fixture_values or {}).get(obligation_id, ()))
            question = (derivation.calibration_questions or {}).get(obligation_id, "")
            effective_calibration_status = (
                "ui-calibration-required" if question else item.calibration_status
            )
            # A calibration candidate must not retain an unsupported concrete
            # UI/persistence effect from a prepared oracle.  The atomic source
            # restriction is the safe product claim; the question owns the
            # still-unknown trigger and observable UI response.
            observable_oracle = (
                item.atomic_statement
                if effective_calibration_status == "ui-calibration-required"
                else item.observable_oracle
            )
            obligations.append(
                CoverageObligation(
                    obligation_id=obligation_id,
                    property_id=property_id,
                    atom_id=item.traceability_atom_id,
                    coverage_variant=variant,
                    condition_key=condition_key,
                    atomic_statement=item.atomic_statement,
                    observable_oracle=observable_oracle,
                    coverage_status=item.coverage_status,
                    requirement_codes=inherited_codes or codes,
                    gap_id=item.gap_id,
                    calibration_status=effective_calibration_status,
                    validation_trigger=derivation.validation_trigger,
                    cleanup_strategy=derivation.cleanup_strategy,
                    source_oracle_id=source_oracle_id,
                    fixture_values=fixture_values,
                    calibration_question=question,
                )
            )
            if item.coverage_status == "testable":
                case_key = semantic_case_key(
                    scope_slug=source_manifest.scope_slug,
                    subject_key=subject_key,
                    property_kind=property_kind,
                    coverage_variant=variant,
                    condition_key=condition_key,
                )
                status = (
                    "candidate-ui-calibration"
                    if effective_calibration_status == "ui-calibration-required"
                    else "executable"
                )
                case_specs.append((case_key, obligation_id, status))
            elif item.coverage_status in {"gap", "unclear"}:
                gap_properties.setdefault(item.gap_id, []).append(property_id)
                gap_obligations.setdefault(item.gap_id, []).append(obligation_id)

    orphan_obligations = set(prepared) - set(mapped_obligations)
    assertions_by_atom = {
        item.atom_id: item for item in source_manifest.assertions
    }
    if len(assertions_by_atom) != len(source_manifest.assertions):
        raise CoverageGraphError("source assertions repeat an ATOM id")
    unsafe_orphans: list[str] = []
    for obligation_id in sorted(orphan_obligations):
        item = prepared[obligation_id]
        assertion = assertions_by_atom.get(item.traceability_atom_id)
        if (
            assertion is None
            or assertion.semantic_disposition == "testable"
            or item.coverage_status != "not-applicable"
            or item.observable_oracle
            or item.gap_id
            or item.dictionary_refs
            or item.dictionary_requirements
            or item.calibration_status != "none"
            or item.planned_test_case_id
            or assertion.source_row_id not in item.source_refs
        ):
            unsafe_orphans.append(obligation_id)
    if unsafe_orphans:
        raise CoverageGraphError(
            "prepared obligations are not owned by a source property: "
            + ", ".join(unsafe_orphans)
        )
    ids = assign_stable_ids(
        (case_key for case_key, _, _ in case_specs),
        prefix=tc_prefix,
    )
    cases = tuple(
        CoverageCase(
            case_key=case_key,
            tc_id=ids[case_key],
            obligation_ids=(obligation_id,),
            status=status,
        )
        for case_key, obligation_id, status in sorted(case_specs)
    )
    gap_by_id = {item.gap_id: item for item in obligation_set.coverage_gaps}
    gaps = tuple(
        CoverageGap(
            gap_id=gap_id,
            property_ids=tuple(dict.fromkeys(gap_properties.get(gap_id, ()))),
            obligation_ids=tuple(dict.fromkeys(gap_obligations.get(gap_id, ()))),
            reason=(
                gap_by_id[gap_id].problem
                if gap_id in gap_by_id
                else "source assertion is ambiguous"
            ),
        )
        for gap_id in sorted(set(gap_properties) | set(gap_obligations))
    )
    graph = CoverageGraph(
        schema_version=1,
        ft_slug=ft_slug,
        scope_slug=source_manifest.scope_slug,
        source_manifest_digest=_manifest_digest(source_manifest),
        obligation_set_digest=obligation_set.digest,
        properties=tuple(sorted(properties, key=lambda item: item.property_id)),
        obligations=tuple(sorted(obligations, key=lambda item: item.obligation_id)),
        cases=cases,
        gaps=gaps,
    )
    findings = validate_coverage_graph(graph)
    blockers = [item for item in findings if item.severity == "error"]
    if blockers:
        raise CoverageGraphError(
            "coverage graph failed validation: "
            + "; ".join(f"{item.finding_id}: {item.message}" for item in blockers)
        )
    return graph


def validate_coverage_graph(graph: CoverageGraph) -> tuple[CoverageFinding, ...]:
    findings: list[CoverageFinding] = []
    properties = {item.property_id: item for item in graph.properties}
    obligations = {item.obligation_id: item for item in graph.obligations}
    gaps = {item.gap_id: item for item in graph.gaps}
    case_owner: dict[str, str] = {}
    if graph.schema_version != 1:
        findings.append(
            CoverageFinding(
                "CG-UNSUPPORTED-SCHEMA", "error", message=str(graph.schema_version)
            )
        )
    for label, value in (
        ("source_manifest_digest", graph.source_manifest_digest),
        ("obligation_set_digest", graph.obligation_set_digest),
    ):
        if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
            findings.append(
                CoverageFinding(
                    "CG-INVALID-DIGEST", "error", message=f"{label} is invalid"
                )
            )
    if len(properties) != len(graph.properties):
        findings.append(
            CoverageFinding(
                "CG-DUPLICATE-PROPERTY", "error", message="duplicate property_id"
            )
        )
    if len(obligations) != len(graph.obligations):
        findings.append(
            CoverageFinding(
                "CG-DUPLICATE-OBLIGATION", "error", message="duplicate obligation_id"
            )
        )
    unique_fields: tuple[tuple[str, Sequence[str]], ...] = (
        ("assertion_id", [item.assertion_id for item in graph.properties]),
        ("property_key", [item.property_key for item in graph.properties]),
        ("gap_id", [item.gap_id for item in graph.gaps]),
    )
    for label, values in unique_fields:
        if len(values) != len(set(values)):
            findings.append(
                CoverageFinding(
                    f"CG-DUPLICATE-{label.replace('_', '-').upper()}",
                    "error",
                    message=f"duplicate {label}",
                )
            )
    property_obligations: dict[str, list[str]] = {key: [] for key in properties}
    for item in graph.properties:
        if item.disposition not in _PROPERTY_DISPOSITIONS:
            findings.append(
                CoverageFinding(
                    "CG-INVALID-DISPOSITION",
                    "error",
                    property_id=item.property_id,
                    message=f"unsupported disposition {item.disposition}",
                )
            )
        if item.polarity not in {"positive", "negative", "neutral"}:
            findings.append(
                CoverageFinding(
                    "CG-INVALID-POLARITY",
                    "error",
                    property_id=item.property_id,
                    message=f"unsupported polarity {item.polarity}",
                )
            )
    for item in graph.obligations:
        if item.property_id not in properties:
            findings.append(
                CoverageFinding(
                    "CG-ORPHAN-OBLIGATION",
                    "error",
                    obligation_id=item.obligation_id,
                    message="obligation references an unknown property",
                )
            )
        else:
            property_obligations[item.property_id].append(item.obligation_id)
        if item.coverage_status == "testable":
            if item.gap_id:
                findings.append(
                    CoverageFinding(
                        "CG-TESTABLE-WITH-GAP",
                        "error",
                        property_id=item.property_id,
                        obligation_id=item.obligation_id,
                        message=f"testable obligation links {item.gap_id}",
                    )
                )
        elif item.coverage_status in {"gap", "unclear"}:
            if item.gap_id not in gaps:
                findings.append(
                    CoverageFinding(
                        "CG-UNKNOWN-GAP",
                        "error",
                        property_id=item.property_id,
                        obligation_id=item.obligation_id,
                        message=f"unknown gap {item.gap_id!r}",
                    )
                )
        else:
            findings.append(
                CoverageFinding(
                    "CG-INVALID-COVERAGE-STATUS",
                    "error",
                    property_id=item.property_id,
                    obligation_id=item.obligation_id,
                    message=item.coverage_status,
                )
            )

    gap_property_ids: set[str] = set()
    for gap in graph.gaps:
        unknown_properties = set(gap.property_ids) - set(properties)
        unknown_obligations = set(gap.obligation_ids) - set(obligations)
        if unknown_properties or unknown_obligations:
            findings.append(
                CoverageFinding(
                    "CG-GAP-DANGLING-REFERENCE",
                    "error",
                    message=(
                        f"{gap.gap_id}: properties={sorted(unknown_properties)}, "
                        f"obligations={sorted(unknown_obligations)}"
                    ),
                )
            )
        gap_property_ids.update(gap.property_ids)
        for obligation_id in set(gap.obligation_ids) & set(obligations):
            if obligations[obligation_id].gap_id != gap.gap_id:
                findings.append(
                    CoverageFinding(
                        "CG-GAP-OWNERSHIP-MISMATCH",
                        "error",
                        obligation_id=obligation_id,
                        message=f"{gap.gap_id} does not own the obligation gap link",
                    )
                )
    for prop in graph.properties:
        owned = property_obligations.get(prop.property_id, [])
        if prop.disposition == "tc" and not owned:
            findings.append(
                CoverageFinding(
                    "CG-TESTABLE-PROPERTY-WITHOUT-OBLIGATION",
                    "error",
                    property_id=prop.property_id,
                    message="testable property has no obligation",
                )
            )
        if prop.disposition == "gap" and prop.property_id not in gap_property_ids:
            findings.append(
                CoverageFinding(
                    "CG-GAP-PROPERTY-WITHOUT-GAP",
                    "error",
                    property_id=prop.property_id,
                    message="gap property has no gap",
                )
            )
        if prop.disposition == "not-applicable" and owned:
            findings.append(
                CoverageFinding(
                    "CG-NOT-APPLICABLE-WITH-OBLIGATION",
                    "error",
                    property_id=prop.property_id,
                    message="not-applicable property owns obligations",
                )
            )
    for case in graph.cases:
        if case.status not in _CASE_STATUSES:
            findings.append(
                CoverageFinding(
                    "CG-INVALID-CASE-STATUS", "error", tc_id=case.tc_id, message=case.status
                )
            )
        for obligation_id in case.obligation_ids:
            if obligation_id in case_owner:
                findings.append(
                    CoverageFinding(
                        "CG-DUPLICATE-CASE-COVERAGE",
                        "error",
                        obligation_id=obligation_id,
                        tc_id=case.tc_id,
                        message=f"also covered by {case_owner[obligation_id]}",
                    )
                )
            case_owner[obligation_id] = case.tc_id
            obligation = obligations.get(obligation_id)
            if obligation is None:
                findings.append(
                    CoverageFinding(
                        "CG-CASE-UNKNOWN-OBLIGATION",
                        "error",
                        obligation_id=obligation_id,
                        tc_id=case.tc_id,
                        message="case references an unknown obligation",
                    )
                )
                continue
            if case.status == "candidate-ui-calibration":
                required = {
                    "source oracle": obligation.source_oracle_id,
                    "validation trigger": obligation.validation_trigger,
                    "fixture value": obligation.fixture_values,
                    "calibration question": obligation.calibration_question,
                }
                for label, value in required.items():
                    if not value:
                        findings.append(
                            CoverageFinding(
                                "CG-CALIBRATION-CONTRACT-INCOMPLETE",
                                "error",
                                property_id=obligation.property_id,
                                obligation_id=obligation_id,
                                tc_id=case.tc_id,
                                message=f"missing {label}",
                            )
                        )
                if obligation.source_oracle_id and not obligation.source_oracle_id.startswith("SO-"):
                    findings.append(
                        CoverageFinding(
                            "CG-CALIBRATION-SOURCE-ORACLE-ID",
                            "error",
                            obligation_id=obligation_id,
                            tc_id=case.tc_id,
                            message="source oracle must use an SO-* identifier",
                        )
                    )
            if obligation.property_id in properties:
                kind = properties[obligation.property_id].property_kind
                if kind in {"state-change", "repeater-delete", "repeater-add"} and not obligation.cleanup_strategy:
                    findings.append(
                        CoverageFinding(
                            "CG-STATE-CHANGE-WITHOUT-CLEANUP",
                            "error",
                            property_id=obligation.property_id,
                            obligation_id=obligation_id,
                            tc_id=case.tc_id,
                            message="state-changing case requires cleanup or isolation",
                        )
                    )
    for item in graph.obligations:
        if item.coverage_status == "testable" and item.obligation_id not in case_owner:
            findings.append(
                CoverageFinding(
                    "CG-TESTABLE-OBLIGATION-UNCOVERED",
                    "error",
                    property_id=item.property_id,
                    obligation_id=item.obligation_id,
                    message="testable obligation has no case",
                )
            )
    tc_ids = [item.tc_id for item in graph.cases]
    if len(tc_ids) != len(set(tc_ids)):
        findings.append(CoverageFinding("CG-DUPLICATE-TC-ID", "error", message="duplicate TC-ID"))
    case_keys = [item.case_key for item in graph.cases]
    if len(case_keys) != len(set(case_keys)):
        findings.append(CoverageFinding("CG-DUPLICATE-CASE-KEY", "error", message="duplicate case_key"))
    return tuple(findings)
