from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

CREATED_BY_TOOL = "test_case_agent.create_new_tc_context_bundle"
BUNDLE_PREFIX = "create-new-tc-context-bundle"
DEFAULT_PACKAGE_ID = "WPKG-000001"

BundleStatus = Literal["pass", "pass-with-warnings", "blocked"]
SimilarityRisk = Literal["low", "medium", "high"]

TC_HEADING_RE = re.compile(r"^(#{2,6})\s+(TC-[A-Za-z0-9][A-Za-z0-9_-]*)\b[:\-\s]*(.*)$")
REF_RE = re.compile(
    r"\b(?:REQ-[A-Z0-9-]+|ATOM-[A-Z0-9-]+|BSR\s+\d+|GSR\s+\d+|SRC-[A-Z0-9-]+|GAP-\d+|DICT-[A-Z0-9-]+|WP-\d+)\b",
    re.IGNORECASE,
)
WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9]{4,}")
AGGREGATE_MARKERS = [
    "assembled_from",
    "test_case_count",
    "aggregate",
    "порядок сборки",
    "РїРѕСЂСЏРґРѕРє СЃР±РѕСЂРєРё",
    "source files assembled",
]


@dataclass(frozen=True)
class CandidateRequirement:
    req_uid: str | None
    source_req_id: str | None
    source_version: str | None
    change_type: str | None
    requirement_type: str | None
    object: str | None
    condition: str | None
    expected_behavior: str | None
    source_text: str | None
    normalized_text: str | None
    source_anchors: list[dict[str, Any]]
    diff_entry_id: str | None
    impact_id: str | None
    plan_item_id: str | None
    confidence: str
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "req_uid": self.req_uid,
            "source_req_id": self.source_req_id,
            "source_version": self.source_version,
            "change_type": self.change_type,
            "requirement_type": self.requirement_type,
            "object": self.object,
            "condition": self.condition,
            "expected_behavior": self.expected_behavior,
            "source_text": self.source_text,
            "normalized_text": self.normalized_text,
            "source_anchors": self.source_anchors,
            "diff_entry_id": self.diff_entry_id,
            "impact_id": self.impact_id,
            "plan_item_id": self.plan_item_id,
            "confidence": self.confidence,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CandidateRequirement":
        return cls(
            req_uid=data.get("req_uid"),
            source_req_id=data.get("source_req_id"),
            source_version=data.get("source_version"),
            change_type=data.get("change_type"),
            requirement_type=data.get("requirement_type"),
            object=data.get("object"),
            condition=data.get("condition"),
            expected_behavior=data.get("expected_behavior"),
            source_text=data.get("source_text"),
            normalized_text=data.get("normalized_text"),
            source_anchors=list(data.get("source_anchors") or []),
            diff_entry_id=data.get("diff_entry_id"),
            impact_id=data.get("impact_id"),
            plan_item_id=data.get("plan_item_id"),
            confidence=str(data.get("confidence") or "low"),
            warnings=list(data.get("warnings") or []),
        )


@dataclass(frozen=True)
class CandidateGroup:
    group_id: str
    group_reason: str
    candidate_req_uids: list[str]
    source_req_ids: list[str]
    suggested_tc_count: int
    suggested_tc_theme: str
    draft_allowed: bool
    requires_manual_review: bool
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_id": self.group_id,
            "group_reason": self.group_reason,
            "candidate_req_uids": self.candidate_req_uids,
            "source_req_ids": self.source_req_ids,
            "suggested_tc_count": self.suggested_tc_count,
            "suggested_tc_theme": self.suggested_tc_theme,
            "draft_allowed": self.draft_allowed,
            "requires_manual_review": self.requires_manual_review,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CandidateGroup":
        return cls(
            group_id=str(data["group_id"]),
            group_reason=str(data["group_reason"]),
            candidate_req_uids=list(data.get("candidate_req_uids") or []),
            source_req_ids=list(data.get("source_req_ids") or []),
            suggested_tc_count=int(data.get("suggested_tc_count") or 0),
            suggested_tc_theme=str(data.get("suggested_tc_theme") or ""),
            draft_allowed=bool(data.get("draft_allowed")),
            requires_manual_review=bool(data.get("requires_manual_review")),
            warnings=list(data.get("warnings") or []),
        )


@dataclass(frozen=True)
class ExistingTcSimilarity:
    candidate_req_uid: str | None
    similar_tc_id: str
    similar_file_path: str
    similarity_reason: str
    overlap_refs: list[str]
    overlap_keywords: list[str]
    risk: SimilarityRisk

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_req_uid": self.candidate_req_uid,
            "similar_tc_id": self.similar_tc_id,
            "similar_file_path": self.similar_file_path,
            "similarity_reason": self.similarity_reason,
            "overlap_refs": self.overlap_refs,
            "overlap_keywords": self.overlap_keywords,
            "risk": self.risk,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExistingTcSimilarity":
        return cls(
            candidate_req_uid=data.get("candidate_req_uid"),
            similar_tc_id=str(data["similar_tc_id"]),
            similar_file_path=str(data["similar_file_path"]),
            similarity_reason=str(data["similarity_reason"]),
            overlap_refs=list(data.get("overlap_refs") or []),
            overlap_keywords=list(data.get("overlap_keywords") or []),
            risk=data["risk"],
        )


@dataclass(frozen=True)
class RecommendedDraftTarget:
    target_file_path: str
    target_section: str | None
    suggested_tc_id_prefix: str
    reason: str
    requires_new_file: bool
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_file_path": self.target_file_path,
            "target_section": self.target_section,
            "suggested_tc_id_prefix": self.suggested_tc_id_prefix,
            "reason": self.reason,
            "requires_new_file": self.requires_new_file,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RecommendedDraftTarget":
        return cls(
            target_file_path=str(data["target_file_path"]),
            target_section=data.get("target_section"),
            suggested_tc_id_prefix=str(data.get("suggested_tc_id_prefix") or "TC-DRAFT"),
            reason=str(data.get("reason") or ""),
            requires_new_file=bool(data.get("requires_new_file")),
            warnings=list(data.get("warnings") or []),
        )


@dataclass
class CreateNewTcContextBundle:
    package_id: str
    bundle_status: BundleStatus
    package_type: str | None
    plan_item_ids: list[str]
    impact_ids: list[str]
    change_ids: list[str]
    candidate_requirements: list[CandidateRequirement]
    candidate_groups: list[CandidateGroup]
    existing_tc_similarity: list[ExistingTcSimilarity]
    recommended_draft_targets: list[RecommendedDraftTarget]
    coverage_obligations: list[dict[str, Any]]
    duplicate_risks: list[dict[str, Any]]
    source_context: dict[str, Any]
    registry_context: dict[str, Any]
    input_paths: dict[str, str]
    warnings: list[str]
    blocking_reasons: list[str]
    created_at_utc: str
    created_by_tool: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "bundle_status": self.bundle_status,
            "package_type": self.package_type,
            "plan_item_ids": self.plan_item_ids,
            "impact_ids": self.impact_ids,
            "change_ids": self.change_ids,
            "candidate_requirements": [item.to_dict() for item in self.candidate_requirements],
            "candidate_groups": [item.to_dict() for item in self.candidate_groups],
            "existing_tc_similarity": [item.to_dict() for item in self.existing_tc_similarity],
            "recommended_draft_targets": [item.to_dict() for item in self.recommended_draft_targets],
            "coverage_obligations": self.coverage_obligations,
            "duplicate_risks": self.duplicate_risks,
            "source_context": self.source_context,
            "registry_context": self.registry_context,
            "input_paths": self.input_paths,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CreateNewTcContextBundle":
        return cls(
            package_id=str(data["package_id"]),
            bundle_status=data["bundle_status"],
            package_type=data.get("package_type"),
            plan_item_ids=list(data.get("plan_item_ids") or []),
            impact_ids=list(data.get("impact_ids") or []),
            change_ids=list(data.get("change_ids") or []),
            candidate_requirements=[
                CandidateRequirement.from_dict(item)
                for item in data.get("candidate_requirements", [])
            ],
            candidate_groups=[
                CandidateGroup.from_dict(item)
                for item in data.get("candidate_groups", [])
            ],
            existing_tc_similarity=[
                ExistingTcSimilarity.from_dict(item)
                for item in data.get("existing_tc_similarity", [])
            ],
            recommended_draft_targets=[
                RecommendedDraftTarget.from_dict(item)
                for item in data.get("recommended_draft_targets", [])
            ],
            coverage_obligations=list(data.get("coverage_obligations") or []),
            duplicate_risks=list(data.get("duplicate_risks") or []),
            source_context=dict(data.get("source_context") or {}),
            registry_context=dict(data.get("registry_context") or {}),
            input_paths=dict(data.get("input_paths") or {}),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
        )


@dataclass(frozen=True)
class ParsedTcBlock:
    test_case_id: str
    file_path: str
    title: str | None
    traceability_line: str | None
    refs: list[str]
    keywords: list[str]
    text: str


def build_create_new_tc_context_bundle(
    *,
    package_id: str,
    manual_update_packages_path: Path,
    writer_package_tasks_path: Path,
    update_plan_path: Path,
    impact_report_path: Path,
    requirements_diff_path: Path,
    old_registry_path: Path,
    new_registry_path: Path,
    old_source_manifest_path: Path,
    new_source_manifest_path: Path,
    test_cases_dir: Path,
    created_by_tool: str = CREATED_BY_TOOL,
) -> CreateNewTcContextBundle:
    paths = {
        "manual_update_packages_path": manual_update_packages_path,
        "writer_package_tasks_path": writer_package_tasks_path,
        "update_plan_path": update_plan_path,
        "impact_report_path": impact_report_path,
        "requirements_diff_path": requirements_diff_path,
        "old_registry_path": old_registry_path,
        "new_registry_path": new_registry_path,
        "old_source_manifest_path": old_source_manifest_path,
        "new_source_manifest_path": new_source_manifest_path,
        "test_cases_dir": test_cases_dir,
    }
    input_paths = {key: str(Path(value)) for key, value in paths.items()}
    warnings: list[str] = []
    blocking_reasons: list[str] = []

    if package_id != DEFAULT_PACKAGE_ID:
        blocking_reasons.append(f"this context bundle builder is scoped to {DEFAULT_PACKAGE_ID}; got {package_id}.")

    for label, path in paths.items():
        path = Path(path)
        if label == "test_cases_dir":
            if not path.exists() or not path.is_dir():
                blocking_reasons.append(f"test-cases dir is missing: {path}")
        elif not path.exists():
            blocking_reasons.append(f"required input artifact is missing: {path}")

    packages = _load_json_object(manual_update_packages_path, "manual update packages", blocking_reasons)
    tasks = _load_json_object(writer_package_tasks_path, "writer package tasks", blocking_reasons)
    update_plan = _load_json_object(update_plan_path, "test-case update plan", blocking_reasons)
    impact_report = _load_json_object(impact_report_path, "impact report", blocking_reasons)
    requirements_diff = _load_json_object(requirements_diff_path, "requirements diff", blocking_reasons)
    old_manifest = _load_json_object(old_source_manifest_path, "old source manifest", warnings, required=False)
    new_manifest = _load_json_object(new_source_manifest_path, "new source manifest", warnings, required=False)

    old_registry = _load_registry(old_registry_path, warnings, blocking_reasons)
    new_registry = _load_registry(new_registry_path, warnings, blocking_reasons)

    package = _find_by_id(packages.get("packages") if packages else [], "package_id", package_id)
    task = _find_by_id(tasks.get("tasks") if tasks else [], "package_id", package_id)
    plan_items_by_id = _index_by_id(update_plan.get("plan_items") if update_plan else [], "plan_item_id")
    impacts_by_id = _index_by_id(impact_report.get("impact_entries") if impact_report else [], "impact_id")
    diff_by_id = _index_by_id(requirements_diff.get("entries") if requirements_diff else [], "change_id")

    package_type = package.get("package_type") if package else None
    plan_item_ids = list(package.get("plan_item_ids") or []) if package else []
    impact_ids = list(package.get("impact_ids") or []) if package else []
    change_ids = list(package.get("change_ids") or []) if package else []

    if package is None:
        blocking_reasons.append(f"manual update package not found: {package_id}")
    elif package.get("package_type") != "create_new_candidate":
        blocking_reasons.append(
            f"package {package_id} must be create_new_candidate; got {package.get('package_type')}"
        )
    elif package.get("file_path") or package.get("test_case_ids"):
        blocking_reasons.append(f"package {package_id} must be unbound to existing canonical TC files.")
    elif package.get("plan_items_count") != len(plan_item_ids):
        warnings.append(f"package {package_id} plan_items_count differs from listed plan_item_ids.")

    if task is None:
        blocking_reasons.append(f"writer package task not found: {package_id}")
    else:
        blocking_reasons.extend(_task_gate_reasons(task))
        warnings.extend(str(value) for value in task.get("warnings") or [])

    selected_plan_items = [plan_items_by_id.get(plan_item_id) for plan_item_id in plan_item_ids]
    for plan_item_id, item in zip(plan_item_ids, selected_plan_items):
        if item is None:
            blocking_reasons.append(f"plan item not found for package {package_id}: {plan_item_id}")
            continue
        if item.get("action") != "create_new_candidate":
            blocking_reasons.append(
                f"plan item {plan_item_id} is not create_new_candidate: {item.get('action')}"
            )
        if item.get("file_path") or item.get("test_case_id"):
            blocking_reasons.append(f"plan item {plan_item_id} unexpectedly targets an existing TC.")

    old_by_req, old_by_source = _registry_indexes(old_registry)
    new_by_req, new_by_source = _registry_indexes(new_registry)

    candidate_requirements: list[CandidateRequirement] = []
    if not blocking_reasons:
        for item in selected_plan_items:
            if item is None:
                continue
            impact = impacts_by_id.get(str(item.get("impact_id")))
            diff_entry = diff_by_id.get(str(item.get("change_id")))
            if impact is None:
                blocking_reasons.append(f"impact entry not found for {item.get('plan_item_id')}: {item.get('impact_id')}")
                continue
            if diff_entry is None:
                blocking_reasons.append(f"diff entry not found for {item.get('plan_item_id')}: {item.get('change_id')}")
                continue
            candidate_requirements.append(
                _candidate_requirement(
                    item=item,
                    impact=impact,
                    diff_entry=diff_entry,
                    old_by_req=old_by_req,
                    old_by_source=old_by_source,
                    new_by_req=new_by_req,
                    new_by_source=new_by_source,
                )
            )

    if not blocking_reasons and len(candidate_requirements) != len(plan_item_ids):
        warnings.append(
            f"candidate requirement count {len(candidate_requirements)} differs from plan item count {len(plan_item_ids)}."
        )

    tc_blocks: list[ParsedTcBlock] = []
    if Path(test_cases_dir).exists() and Path(test_cases_dir).is_dir():
        tc_blocks, tc_warnings = _read_existing_tc_blocks(Path(test_cases_dir))
        warnings.extend(tc_warnings)

    candidate_groups = _candidate_groups(candidate_requirements)
    existing_tc_similarity = _existing_tc_similarity(candidate_requirements, tc_blocks)
    duplicate_risks = [
        item.to_dict()
        for item in existing_tc_similarity
        if item.risk in {"medium", "high"}
    ]
    recommended_draft_targets = _recommended_draft_targets(candidate_groups, existing_tc_similarity)
    coverage_obligations = _coverage_obligations(candidate_requirements)
    source_context = _source_context(old_manifest, new_manifest)
    registry_context = _registry_context(old_registry, new_registry, candidate_requirements)

    if duplicate_risks:
        warnings.append("possible existing TC coverage detected; treat as duplicate risk before drafting new TC.")
    if any(candidate.confidence == "low" for candidate in candidate_requirements):
        warnings.append("one or more candidate requirements have low confidence and require manual review.")
    if candidate_requirements:
        warnings.append("manual review is required before any canonical TC creation.")

    warnings = _unique(warnings)
    blocking_reasons = _unique(blocking_reasons)
    if blocking_reasons:
        bundle_status: BundleStatus = "blocked"
    elif warnings:
        bundle_status = "pass-with-warnings"
    else:
        bundle_status = "pass"

    return CreateNewTcContextBundle(
        package_id=package_id,
        bundle_status=bundle_status,
        package_type=package_type,
        plan_item_ids=plan_item_ids,
        impact_ids=impact_ids,
        change_ids=change_ids,
        candidate_requirements=candidate_requirements,
        candidate_groups=candidate_groups,
        existing_tc_similarity=existing_tc_similarity,
        recommended_draft_targets=recommended_draft_targets,
        coverage_obligations=coverage_obligations,
        duplicate_risks=duplicate_risks,
        source_context=source_context,
        registry_context=registry_context,
        input_paths=input_paths,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
    )


def write_create_new_tc_context_bundle(
    bundle: CreateNewTcContextBundle,
    out_dir: Path,
) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{BUNDLE_PREFIX}-{bundle.package_id}.json"
    markdown_path = out_dir / f"{BUNDLE_PREFIX}-{bundle.package_id}.md"
    json_path.write_text(
        json.dumps(bundle.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    markdown_path.write_text(
        render_create_new_tc_context_bundle_markdown(bundle),
        encoding="utf-8",
        newline="\n",
    )
    return json_path, markdown_path


def load_create_new_tc_context_bundle(path: Path) -> CreateNewTcContextBundle:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Create-new TC context bundle root must be a JSON object.")
    return CreateNewTcContextBundle.from_dict(payload)


def render_create_new_tc_context_bundle_markdown(bundle: CreateNewTcContextBundle) -> str:
    lines = [
        f"# Create New TC Context Bundle {bundle.package_id}",
        "",
        "## Summary",
        "",
        f"- Bundle status: `{bundle.bundle_status}`",
        f"- Package type: `{bundle.package_type}`",
        f"- Plan items: `{len(bundle.plan_item_ids)}`",
        f"- Candidate requirements: `{len(bundle.candidate_requirements)}`",
        f"- Candidate groups: `{len(bundle.candidate_groups)}`",
        f"- Duplicate risks: `{len(bundle.duplicate_risks)}`",
        f"- Recommended draft targets: `{len(bundle.recommended_draft_targets)}`",
        "",
        "No canonical test-case file was created or modified by this bundle.",
        "",
        "## Candidate Requirements",
        "",
        "| Plan item | Impact | Change | Req UID | Source req | Type | Confidence |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for candidate in bundle.candidate_requirements:
        lines.append(
            "| "
            f"`{candidate.plan_item_id or 'n/a'}` | "
            f"`{candidate.impact_id or 'n/a'}` | "
            f"`{candidate.change_type or 'n/a'}` | "
            f"`{candidate.req_uid or 'n/a'}` | "
            f"`{candidate.source_req_id or 'n/a'}` | "
            f"`{candidate.requirement_type or 'n/a'}` | "
            f"`{candidate.confidence}` |"
        )
    if not bundle.candidate_requirements:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a |")

    lines.extend(["", "## Candidate Groups", ""])
    if bundle.candidate_groups:
        for group in bundle.candidate_groups:
            lines.append(
                f"- `{group.group_id}`: {group.suggested_tc_theme}; "
                f"reqs `{len(group.candidate_req_uids)}`, suggested TC count `{group.suggested_tc_count}`"
            )
            lines.append(f"  - rationale: {group.group_reason}")
    else:
        lines.append("- none")

    lines.extend(["", "## Duplicate Risks", ""])
    if bundle.duplicate_risks:
        for risk in bundle.duplicate_risks:
            lines.append(
                f"- `{risk['candidate_req_uid']}` may overlap `{risk['similar_tc_id']}` "
                f"in `{risk['similar_file_path']}`; risk `{risk['risk']}`; {risk['similarity_reason']}"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Recommended Draft Targets", ""])
    if bundle.recommended_draft_targets:
        for target in bundle.recommended_draft_targets:
            lines.append(
                f"- `{target.target_file_path}` section `{target.target_section or 'n/a'}` "
                f"prefix `{target.suggested_tc_id_prefix}`; new file `{str(target.requires_new_file).lower()}`"
            )
            lines.append(f"  - reason: {target.reason}")
    else:
        lines.append("- none")

    lines.extend(["", "## Coverage Obligations", ""])
    if bundle.coverage_obligations:
        for obligation in bundle.coverage_obligations:
            lines.append(
                f"- `{obligation.get('req_uid') or 'n/a'}`: {obligation.get('obligation') or 'n/a'}"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Warnings", ""])
    _append_list(lines, bundle.warnings)
    lines.extend(["", "## Blocking Reasons", ""])
    _append_list(lines, bundle.blocking_reasons)
    lines.extend(["", "## Safety Statement", ""])
    lines.append("- This is a read-only context bundle.")
    lines.append("- It does not create canonical TC markdown.")
    lines.append("- It does not edit existing canonical test-cases.")
    lines.append("- Future TC creation must use a separate draft-only proposal and review.")
    return "\n".join(lines).rstrip() + "\n"


def _candidate_requirement(
    *,
    item: dict[str, Any],
    impact: dict[str, Any],
    diff_entry: dict[str, Any],
    old_by_req: dict[str, dict[str, Any]],
    old_by_source: dict[str, dict[str, Any]],
    new_by_req: dict[str, dict[str, Any]],
    new_by_source: dict[str, dict[str, Any]],
) -> CandidateRequirement:
    req_uid = diff_entry.get("new_req_uid") or impact.get("new_req_uid") or _first(item.get("new_refs"))
    source_req_id = diff_entry.get("new_source_req_id") or impact.get("new_source_req_id")
    registry_entry = _registry_entry(req_uid, source_req_id, new_by_req, new_by_source)
    old_registry_entry = None
    if registry_entry is None:
        old_req_uid = diff_entry.get("old_req_uid") or impact.get("old_req_uid") or _first(item.get("old_refs"))
        old_source_req_id = diff_entry.get("old_source_req_id") or impact.get("old_source_req_id")
        old_registry_entry = _registry_entry(old_req_uid, old_source_req_id, old_by_req, old_by_source)

    warnings = _unique([
        *(item.get("warnings") or []),
        *(impact.get("warnings") or []),
        *(diff_entry.get("warnings") or []),
        *(registry_entry.get("warnings") if registry_entry else []),
    ])
    if registry_entry is None:
        warnings.append("registry entry missing for candidate requirement.")
    if registry_entry is None and old_registry_entry is not None:
        warnings.append("old registry context exists, but new registry entry is missing for create-new candidate.")

    return CandidateRequirement(
        req_uid=req_uid,
        source_req_id=source_req_id or (registry_entry.get("source_req_id") if registry_entry else None),
        source_version=registry_entry.get("source_version") if registry_entry else None,
        change_type=impact.get("change_type") or diff_entry.get("change_type"),
        requirement_type=(registry_entry or {}).get("requirement_type") or diff_entry.get("new_requirement_type"),
        object=(registry_entry or {}).get("object"),
        condition=(registry_entry or {}).get("condition"),
        expected_behavior=(registry_entry or {}).get("expected_behavior"),
        source_text=(registry_entry or {}).get("source_text") or diff_entry.get("new_normalized_text"),
        normalized_text=(registry_entry or {}).get("normalized_text") or diff_entry.get("new_normalized_text"),
        source_anchors=list((registry_entry or {}).get("source_anchors") or diff_entry.get("new_source_anchors") or []),
        diff_entry_id=diff_entry.get("change_id"),
        impact_id=impact.get("impact_id"),
        plan_item_id=item.get("plan_item_id"),
        confidence=str((registry_entry or {}).get("confidence") or diff_entry.get("confidence") or "low"),
        warnings=warnings,
    )


def _candidate_groups(candidates: list[CandidateRequirement]) -> list[CandidateGroup]:
    grouped: dict[tuple[str, str, str], list[CandidateRequirement]] = defaultdict(list)
    for candidate in candidates:
        anchor_key = _anchor_group_key(candidate.source_anchors)
        object_key = _stable_text_key(candidate.object or candidate.expected_behavior or candidate.normalized_text)
        grouped[(anchor_key, candidate.requirement_type or "unknown", object_key)].append(candidate)

    groups: list[CandidateGroup] = []
    for index, (signature, items) in enumerate(sorted(grouped.items()), start=1):
        anchor_key, requirement_type, object_key = signature
        req_uids = _unique(item.req_uid for item in items if item.req_uid)
        source_req_ids = _unique(item.source_req_id for item in items if item.source_req_id)
        warnings = _unique(
            [
                *(
                    warning
                    for item in items
                    for warning in item.warnings
                ),
                "Grouping is a drafting hint only; writer must not merge independent checks without review.",
            ]
        )
        groups.append(
            CandidateGroup(
                group_id=f"CGRP-{index:06d}",
                group_reason=(
                    "Grouped by source anchor context, requirement type and object/behavior keywords: "
                    f"{anchor_key} / {requirement_type} / {object_key}."
                ),
                candidate_req_uids=req_uids,
                source_req_ids=source_req_ids,
                suggested_tc_count=len(items),
                suggested_tc_theme=_theme(items),
                draft_allowed=True,
                requires_manual_review=True,
                warnings=warnings,
            )
        )
    return groups


def _existing_tc_similarity(
    candidates: list[CandidateRequirement],
    tc_blocks: list[ParsedTcBlock],
) -> list[ExistingTcSimilarity]:
    similarities: list[ExistingTcSimilarity] = []
    for candidate in candidates:
        candidate_refs = _candidate_refs(candidate)
        candidate_keywords = _candidate_keywords(candidate)
        for block in tc_blocks:
            overlap_refs = sorted(candidate_refs & set(ref.upper() for ref in block.refs))
            overlap_keywords = sorted(candidate_keywords & set(block.keywords))
            if overlap_refs:
                risk: SimilarityRisk = "high"
                reason = "traceability/source refs overlap with existing TC"
            elif len(overlap_keywords) >= 4:
                risk = "medium"
                reason = "keyword overlap with existing TC content"
            elif len(overlap_keywords) >= 2:
                risk = "low"
                reason = "weak keyword overlap with existing TC content"
            else:
                continue
            similarities.append(
                ExistingTcSimilarity(
                    candidate_req_uid=candidate.req_uid,
                    similar_tc_id=block.test_case_id,
                    similar_file_path=block.file_path,
                    similarity_reason=reason,
                    overlap_refs=overlap_refs,
                    overlap_keywords=overlap_keywords[:10],
                    risk=risk,
                )
            )
    return sorted(
        similarities,
        key=lambda item: (
            {"high": 0, "medium": 1, "low": 2}[item.risk],
            item.candidate_req_uid or "",
            item.similar_file_path,
            item.similar_tc_id,
        ),
    )


def _recommended_draft_targets(
    groups: list[CandidateGroup],
    similarities: list[ExistingTcSimilarity],
) -> list[RecommendedDraftTarget]:
    best_similarity_by_req: dict[str, ExistingTcSimilarity] = {}
    for similarity in similarities:
        if not similarity.candidate_req_uid:
            continue
        current = best_similarity_by_req.get(similarity.candidate_req_uid)
        if current is None or _risk_rank(similarity.risk) < _risk_rank(current.risk):
            best_similarity_by_req[similarity.candidate_req_uid] = similarity

    targets: list[RecommendedDraftTarget] = []
    for group in groups:
        related = [
            best_similarity_by_req[req_uid]
            for req_uid in group.candidate_req_uids
            if req_uid in best_similarity_by_req
        ]
        medium_or_high = [item for item in related if item.risk in {"medium", "high"}]
        if medium_or_high:
            file_path = Counter(item.similar_file_path for item in medium_or_high).most_common(1)[0][0]
            reason = "Existing TC file has overlapping refs/keywords; use only as draft target after duplicate review."
            requires_new_file = False
            warnings = ["Do not append to this canonical file during Stage 9A."]
        else:
            file_path = f"draft-only/{DEFAULT_PACKAGE_ID}/{group.group_id}.md"
            reason = "No strong existing canonical target found; recommend separate draft artifact first."
            requires_new_file = True
            warnings = ["Draft target only; do not create canonical file during Stage 9A."]
        targets.append(
            RecommendedDraftTarget(
                target_file_path=file_path,
                target_section=group.suggested_tc_theme,
                suggested_tc_id_prefix=_tc_prefix(group),
                reason=reason,
                requires_new_file=requires_new_file,
                warnings=warnings,
            )
        )
    return targets


def _coverage_obligations(candidates: list[CandidateRequirement]) -> list[dict[str, Any]]:
    obligations: list[dict[str, Any]] = []
    for candidate in candidates:
        obligations.append(
            {
                "req_uid": candidate.req_uid,
                "source_req_id": candidate.source_req_id,
                "plan_item_id": candidate.plan_item_id,
                "impact_id": candidate.impact_id,
                "change_type": candidate.change_type,
                "obligation": "Draft at least one reviewed TC candidate or record an explicit duplicate/no-new-TC rationale.",
                "requires_manual_review": True,
            }
        )
    return obligations


def _read_existing_tc_blocks(test_cases_dir: Path) -> tuple[list[ParsedTcBlock], list[str]]:
    warnings: list[str] = []
    blocks: list[ParsedTcBlock] = []
    for file_path in sorted(test_cases_dir.glob("*.md")):
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as exc:  # noqa: BLE001 - diagnostic context should continue.
            warnings.append(f"test-case file could not be read for similarity scan: {file_path}: {exc}")
            continue
        if _is_aggregate_file(content):
            continue
        blocks.extend(_parse_tc_blocks(file_path, content))
    return blocks, warnings


def _parse_tc_blocks(file_path: Path, content: str) -> list[ParsedTcBlock]:
    lines = content.splitlines()
    headings: list[tuple[int, str, str]] = []
    for index, line in enumerate(lines):
        match = TC_HEADING_RE.match(line.strip())
        if match:
            headings.append((index, match.group(2), match.group(3).strip()))
    blocks: list[ParsedTcBlock] = []
    for index, (start, test_case_id, heading_tail) in enumerate(headings):
        end = headings[index + 1][0] if index + 1 < len(headings) else len(lines)
        block_lines = lines[start:end]
        block_text = "\n".join(block_lines)
        traceability_line = _traceability_line(block_lines)
        title = _title(block_lines) or heading_tail or None
        blocks.append(
            ParsedTcBlock(
                test_case_id=test_case_id,
                file_path=str(file_path),
                title=title,
                traceability_line=traceability_line,
                refs=sorted(set(ref.upper() for ref in REF_RE.findall(block_text))),
                keywords=sorted(_keywords(" ".join([title or "", traceability_line or "", block_text]))),
                text=block_text,
            )
        )
    return blocks


def _traceability_line(lines: list[str]) -> str | None:
    for line in lines:
        lowered = line.casefold()
        if "traceability" in lowered or "трассиров" in lowered or "СЂР°СЃСЃ" in line:
            return line.strip()
    return None


def _title(lines: list[str]) -> str | None:
    for line in lines:
        lowered = line.casefold()
        if "title" in lowered or "название" in lowered or "РќР°Р·РІР°РЅРёРµ" in line:
            if ":**" in line:
                return line.split(":**", 1)[1].strip()
            if ":" in line:
                return line.split(":", 1)[1].strip()
    return None


def _task_gate_reasons(task: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if task.get("package_type") != "create_new_candidate" and "create_new_candidate" not in (task.get("actions") or []):
        reasons.append(f"writer task is not create-new oriented: {task.get('package_type')}")
    if task.get("file_path") or task.get("affected_test_case_ids"):
        reasons.append("create-new writer task must not be file-bound to canonical TC.")
    allowed = " ".join(str(value).casefold() for value in task.get("allowed_operations") or [])
    forbidden = " ".join(str(value).casefold() for value in task.get("forbidden_operations") or [])
    scope = str(task.get("scope_instruction") or "").casefold()
    if "draft" not in allowed and "draft" not in scope:
        reasons.append("writer task does not explicitly allow draft/proposal-only work.")
    if "canonical" not in forbidden and "do not write canonical" not in scope:
        reasons.append("writer task does not explicitly forbid canonical writes.")
    if task.get("large_package"):
        reasons.append("large create-new package requires a separate split/map flow.")
    return reasons


def _registry_indexes(entries: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_req: dict[str, dict[str, Any]] = {}
    by_source: dict[str, dict[str, Any]] = {}
    for entry in entries:
        req_uid = entry.get("req_uid")
        source_req_id = entry.get("source_req_id")
        if req_uid and req_uid not in by_req:
            by_req[str(req_uid)] = entry
        if source_req_id and source_req_id not in by_source:
            by_source[str(source_req_id).upper()] = entry
    return by_req, by_source


def _registry_entry(
    req_uid: str | None,
    source_req_id: str | None,
    by_req: dict[str, dict[str, Any]],
    by_source: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    if req_uid and req_uid in by_req:
        return by_req[req_uid]
    if source_req_id and source_req_id.upper() in by_source:
        return by_source[source_req_id.upper()]
    return None


def _load_registry(
    path: Path,
    warnings: list[str],
    blocking_reasons: list[str],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if not Path(path).exists():
        return entries
    try:
        for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                warnings.append(f"registry line is not an object: {path}:{line_number}")
                continue
            entries.append(payload)
    except Exception as exc:  # noqa: BLE001 - artifact builders report parse failures.
        blocking_reasons.append(f"registry JSONL cannot be parsed: {path}: {exc}")
    return entries


def _load_json_object(
    path: Path,
    label: str,
    messages: list[str],
    *,
    required: bool = True,
) -> dict[str, Any]:
    if not Path(path).exists():
        if required:
            messages.append(f"{label} file is missing: {path}")
        return {}
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - artifact builders report parse failures.
        messages.append(f"{label} file cannot be parsed: {path}: {exc}")
        return {}
    if not isinstance(payload, dict):
        messages.append(f"{label} root must be a JSON object: {path}")
        return {}
    return payload


def _find_by_id(items: Any, key: str, expected: str) -> dict[str, Any] | None:
    for item in items or []:
        if isinstance(item, dict) and item.get(key) == expected:
            return item
    return None


def _index_by_id(items: Any, key: str) -> dict[str, dict[str, Any]]:
    return {
        str(item[key]): item
        for item in items or []
        if isinstance(item, dict) and item.get(key) is not None
    }


def _source_context(old_manifest: dict[str, Any], new_manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "old_source_version": old_manifest.get("source_version"),
        "new_source_version": new_manifest.get("source_version"),
        "old_manifest_status": (old_manifest.get("summary") or {}).get("manifest_status") or old_manifest.get("manifest_status"),
        "new_manifest_status": (new_manifest.get("summary") or {}).get("manifest_status") or new_manifest.get("manifest_status"),
        "old_primary_docx": old_manifest.get("primary_docx_path") or old_manifest.get("docx_path"),
        "new_primary_docx": new_manifest.get("primary_docx_path") or new_manifest.get("docx_path"),
    }


def _registry_context(
    old_registry: list[dict[str, Any]],
    new_registry: list[dict[str, Any]],
    candidates: list[CandidateRequirement],
) -> dict[str, Any]:
    missing = [
        candidate.req_uid
        for candidate in candidates
        if candidate.req_uid and candidate.source_version is None
    ]
    return {
        "old_entries_total": len(old_registry),
        "new_entries_total": len(new_registry),
        "candidate_registry_entries_found": len(candidates) - len(missing),
        "candidate_registry_entries_missing": missing,
    }


def _candidate_refs(candidate: CandidateRequirement) -> set[str]:
    refs = {value.upper() for value in [candidate.req_uid, candidate.source_req_id] if value}
    return refs


def _candidate_keywords(candidate: CandidateRequirement) -> set[str]:
    return _keywords(
        " ".join(
            value or ""
            for value in [
                candidate.object,
                candidate.condition,
                candidate.expected_behavior,
                candidate.source_text,
                candidate.normalized_text,
                candidate.requirement_type,
            ]
        )
    )


def _keywords(value: str) -> set[str]:
    stop = {
        "если",
        "для",
        "при",
        "или",
        "and",
        "the",
        "with",
        "must",
        "should",
        "visible",
        "active",
    }
    return {
        match.group(0).casefold()
        for match in WORD_RE.finditer(value)
        if match.group(0).casefold() not in stop
    }


def _anchor_group_key(anchors: list[dict[str, Any]]) -> str:
    if not anchors:
        return "unknown-anchor"
    anchor = anchors[0]
    xpath = str(anchor.get("xpath") or "")
    table = re.search(r"w:tbl\[(\d+)\]", xpath)
    row = re.search(r"w:tr\[(\d+)\]", xpath)
    if table:
        if row:
            return f"{anchor.get('part') or 'source'}:table-{table.group(1)}:row-{row.group(1)}"
        return f"{anchor.get('part') or 'source'}:table-{table.group(1)}"
    return str(anchor.get("part") or "unknown-anchor")


def _stable_text_key(value: str | None) -> str:
    words = sorted(_keywords(value or ""))
    return "-".join(words[:4]) if words else "unknown-object"


def _theme(items: list[CandidateRequirement]) -> str:
    for item in items:
        if item.object:
            return item.object[:120]
    for item in items:
        if item.expected_behavior:
            return item.expected_behavior[:120]
    for item in items:
        if item.normalized_text:
            return item.normalized_text[:120]
    return "new coverage candidate"


def _tc_prefix(group: CandidateGroup) -> str:
    words = re.findall(r"[A-Za-z0-9]+", group.suggested_tc_theme.upper())
    suffix = "".join(word[:3] for word in words[:2])[:6] or group.group_id[-3:]
    return f"TC-DRAFT-{suffix}"


def _risk_rank(risk: SimilarityRisk) -> int:
    return {"high": 0, "medium": 1, "low": 2}[risk]


def _is_aggregate_file(content: str) -> bool:
    head = "\n".join(content.splitlines()[:80]).casefold()
    return any(marker.casefold() in head for marker in AGGREGATE_MARKERS)


def _append_list(lines: list[str], values: list[str]) -> None:
    if not values:
        lines.append("- none")
        return
    for value in values:
        lines.append(f"- {value}")


def _first(values: Any) -> str | None:
    for value in values or []:
        if value:
            return str(value)
    return None


def _unique(values: Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value is None:
            continue
        text = str(value)
        if text not in seen:
            result.append(text)
            seen.add(text)
    return result


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
