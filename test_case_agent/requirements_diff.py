from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Literal

from test_case_agent.requirements_registry import (
    RequirementRegistryEntry,
    SourceAnchor,
    load_requirements_registry_jsonl,
)

CREATED_BY_TOOL = "test_case_agent.requirements_diff"
DIFF_PREFIX = "requirements-diff"
DIFF_SUMMARY_PREFIX = "requirements-diff-summary"
HIGH_SIMILARITY_THRESHOLD = 0.92
FALLBACK_SIMILARITY_THRESHOLD = 0.75
SPLIT_MERGE_SIMILARITY_THRESHOLD = 0.60
DUPLICATE_BLOCKER = (
    "registry contains duplicate req_uid among diff_eligible entries; rerun with allow_duplicate_req_uid only after reviewing anchors."
)

ChangeType = Literal[
    "unchanged",
    "text_changed_no_behavior_change",
    "behavior_modified",
    "added",
    "deleted",
    "moved",
    "renumbered",
    "split",
    "merged",
    "source_anchor_changed",
    "unclear_match",
]
DiffConfidence = Literal["high", "medium", "low"]
DiffStatus = Literal["pass", "pass-with-warnings", "blocked"]


@dataclass(frozen=True)
class RequirementsDiffEntry:
    change_id: str
    change_type: ChangeType
    old_req_uid: str | None
    new_req_uid: str | None
    old_atom_id: str | None
    new_atom_id: str | None
    old_source_req_id: str | None
    new_source_req_id: str | None
    old_requirement_type: str | None
    new_requirement_type: str | None
    old_status: str | None
    new_status: str | None
    old_normalized_text: str | None
    new_normalized_text: str | None
    old_semantic_fingerprint: str | None
    new_semantic_fingerprint: str | None
    old_text_hash: str | None
    new_text_hash: str | None
    old_source_anchors: list[SourceAnchor]
    new_source_anchors: list[SourceAnchor]
    similarity_score: float | None
    confidence: DiffConfidence
    requires_manual_review: bool
    reasons: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "change_id": self.change_id,
            "change_type": self.change_type,
            "old_req_uid": self.old_req_uid,
            "new_req_uid": self.new_req_uid,
            "old_atom_id": self.old_atom_id,
            "new_atom_id": self.new_atom_id,
            "old_source_req_id": self.old_source_req_id,
            "new_source_req_id": self.new_source_req_id,
            "old_requirement_type": self.old_requirement_type,
            "new_requirement_type": self.new_requirement_type,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "old_normalized_text": self.old_normalized_text,
            "new_normalized_text": self.new_normalized_text,
            "old_semantic_fingerprint": self.old_semantic_fingerprint,
            "new_semantic_fingerprint": self.new_semantic_fingerprint,
            "old_text_hash": self.old_text_hash,
            "new_text_hash": self.new_text_hash,
            "old_source_anchors": [anchor.to_dict() for anchor in self.old_source_anchors],
            "new_source_anchors": [anchor.to_dict() for anchor in self.new_source_anchors],
            "similarity_score": self.similarity_score,
            "confidence": self.confidence,
            "requires_manual_review": self.requires_manual_review,
            "reasons": self.reasons,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RequirementsDiffEntry":
        return cls(
            change_id=str(data["change_id"]),
            change_type=data["change_type"],
            old_req_uid=data.get("old_req_uid"),
            new_req_uid=data.get("new_req_uid"),
            old_atom_id=data.get("old_atom_id"),
            new_atom_id=data.get("new_atom_id"),
            old_source_req_id=data.get("old_source_req_id"),
            new_source_req_id=data.get("new_source_req_id"),
            old_requirement_type=data.get("old_requirement_type"),
            new_requirement_type=data.get("new_requirement_type"),
            old_status=data.get("old_status"),
            new_status=data.get("new_status"),
            old_normalized_text=data.get("old_normalized_text"),
            new_normalized_text=data.get("new_normalized_text"),
            old_semantic_fingerprint=data.get("old_semantic_fingerprint"),
            new_semantic_fingerprint=data.get("new_semantic_fingerprint"),
            old_text_hash=data.get("old_text_hash"),
            new_text_hash=data.get("new_text_hash"),
            old_source_anchors=[
                SourceAnchor.from_dict(anchor)
                for anchor in data.get("old_source_anchors", [])
            ],
            new_source_anchors=[
                SourceAnchor.from_dict(anchor)
                for anchor in data.get("new_source_anchors", [])
            ],
            similarity_score=data.get("similarity_score"),
            confidence=data["confidence"],
            requires_manual_review=bool(data["requires_manual_review"]),
            reasons=list(data.get("reasons") or []),
            warnings=list(data.get("warnings") or []),
        )


@dataclass
class RequirementsDiff:
    old_registry_path: str
    new_registry_path: str
    old_source_version: str
    new_source_version: str
    created_at_utc: str
    created_by_tool: str
    entries: list[RequirementsDiffEntry]
    summary: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "old_registry_path": self.old_registry_path,
            "new_registry_path": self.new_registry_path,
            "old_source_version": self.old_source_version,
            "new_source_version": self.new_source_version,
            "created_at_utc": self.created_at_utc,
            "created_by_tool": self.created_by_tool,
            "entries": [entry.to_dict() for entry in self.entries],
            "summary": self.summary,
            "warnings": self.warnings,
            "blocking_reasons": self.blocking_reasons,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RequirementsDiff":
        return cls(
            old_registry_path=str(data["old_registry_path"]),
            new_registry_path=str(data["new_registry_path"]),
            old_source_version=str(data["old_source_version"]),
            new_source_version=str(data["new_source_version"]),
            created_at_utc=str(data["created_at_utc"]),
            created_by_tool=str(data["created_by_tool"]),
            entries=[
                RequirementsDiffEntry.from_dict(entry)
                for entry in data.get("entries", [])
            ],
            summary=dict(data.get("summary") or {}),
            warnings=list(data.get("warnings") or []),
            blocking_reasons=list(data.get("blocking_reasons") or []),
        )


@dataclass(frozen=True)
class CanonicalizationReport:
    input_entries_total: int
    output_entries_total: int
    duplicate_groups_total: int
    canonicalized_groups_total: int
    unresolved_duplicate_groups_total: int
    canonicalized_req_uids: list[str]
    unresolved_req_uids: list[str]
    warnings: list[str]


def build_requirements_diff(
    *,
    old_registry_path: Path,
    new_registry_path: Path,
    old_summary_path: Path | None = None,
    new_summary_path: Path | None = None,
    allow_duplicate_req_uid: bool = False,
    created_by_tool: str = CREATED_BY_TOOL,
) -> RequirementsDiff:
    old_registry_path = Path(old_registry_path)
    new_registry_path = Path(new_registry_path)
    old_summary_path = Path(old_summary_path) if old_summary_path else _infer_summary_path(old_registry_path)
    new_summary_path = Path(new_summary_path) if new_summary_path else _infer_summary_path(new_registry_path)

    blocking_reasons: list[str] = []
    warnings: list[str] = []
    old_summary = _load_optional_summary(old_summary_path, warnings)
    new_summary = _load_optional_summary(new_summary_path, warnings)

    old_entries: list[RequirementRegistryEntry] = []
    new_entries: list[RequirementRegistryEntry] = []

    if not old_registry_path.exists():
        blocking_reasons.append(f"old registry file is missing: {old_registry_path}")
    if not new_registry_path.exists():
        blocking_reasons.append(f"new registry file is missing: {new_registry_path}")

    if _summary_status(old_summary) == "blocked":
        blocking_reasons.append(f"old registry summary is blocked: {old_summary_path}")
    if _summary_status(new_summary) == "blocked":
        blocking_reasons.append(f"new registry summary is blocked: {new_summary_path}")

    if old_registry_path.exists():
        try:
            old_entries = load_requirements_registry_jsonl(old_registry_path)
        except Exception as exc:  # noqa: BLE001 - diff must report parse blockers.
            blocking_reasons.append(f"old registry JSONL cannot be parsed: {old_registry_path}: {exc}")
    if new_registry_path.exists():
        try:
            new_entries = load_requirements_registry_jsonl(new_registry_path)
        except Exception as exc:  # noqa: BLE001 - diff must report parse blockers.
            blocking_reasons.append(f"new registry JSONL cannot be parsed: {new_registry_path}: {exc}")

    old_source_version = _source_version(old_summary, old_entries, old_registry_path)
    new_source_version = _source_version(new_summary, new_entries, new_registry_path)

    old_duplicate_entry_uids = _duplicate_entry_uids(old_entries)
    new_duplicate_entry_uids = _duplicate_entry_uids(new_entries)
    if old_duplicate_entry_uids:
        blocking_reasons.append("old registry contains duplicate entry_uid values")
    if new_duplicate_entry_uids:
        blocking_reasons.append("new registry contains duplicate entry_uid values")

    old_diff_entries = _diff_eligible_entries(old_entries)
    new_diff_entries = _diff_eligible_entries(new_entries)
    old_canonical_entries, old_canonical_report = _canonicalize_diff_entries(old_diff_entries)
    new_canonical_entries, new_canonical_report = _canonicalize_diff_entries(new_diff_entries)
    warnings.extend(old_canonical_report.warnings)
    warnings.extend(new_canonical_report.warnings)
    unresolved_duplicate_uids = sorted(
        set(old_canonical_report.unresolved_req_uids + new_canonical_report.unresolved_req_uids)
    )
    if unresolved_duplicate_uids:
        duplicate_warning = (
            "Unresolved duplicate req_uid values detected among diff_eligible entries: "
            f"{', '.join(unresolved_duplicate_uids)}"
        )
        warnings.append(duplicate_warning)
        if not allow_duplicate_req_uid:
            if old_canonical_report.unresolved_req_uids:
                blocking_reasons.append("old registry contains unresolved duplicate req_uid among diff_eligible entries")
            if new_canonical_report.unresolved_req_uids:
                blocking_reasons.append("new registry contains unresolved duplicate req_uid among diff_eligible entries")

    if blocking_reasons:
        return _make_diff(
            old_registry_path=old_registry_path,
            new_registry_path=new_registry_path,
            old_source_version=old_source_version,
            new_source_version=new_source_version,
            old_entries_total=len(old_entries),
            new_entries_total=len(new_entries),
            old_diff_eligible_entries=len(old_diff_entries),
            new_diff_eligible_entries=len(new_diff_entries),
            old_duplicate_req_uid_diff_eligible_count=old_canonical_report.duplicate_groups_total,
            new_duplicate_req_uid_diff_eligible_count=new_canonical_report.duplicate_groups_total,
            old_canonical_report=old_canonical_report,
            new_canonical_report=new_canonical_report,
            entries=[],
            warnings=warnings,
            blocking_reasons=blocking_reasons,
            created_by_tool=created_by_tool,
        )

    entries = match_requirement_entries(old_canonical_entries, new_canonical_entries)
    warnings.extend(_entry_warnings(entries))
    return _make_diff(
        old_registry_path=old_registry_path,
        new_registry_path=new_registry_path,
        old_source_version=old_source_version,
        new_source_version=new_source_version,
        old_entries_total=len(old_entries),
        new_entries_total=len(new_entries),
        old_diff_eligible_entries=len(old_diff_entries),
        new_diff_eligible_entries=len(new_diff_entries),
        old_duplicate_req_uid_diff_eligible_count=old_canonical_report.duplicate_groups_total,
        new_duplicate_req_uid_diff_eligible_count=new_canonical_report.duplicate_groups_total,
        old_canonical_report=old_canonical_report,
        new_canonical_report=new_canonical_report,
        entries=entries,
        warnings=sorted(set(warnings)),
        blocking_reasons=[],
        created_by_tool=created_by_tool,
    )


def write_requirements_diff(diff: RequirementsDiff, out_dir: Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    diff_path = _diff_path(out_dir, diff.old_source_version, diff.new_source_version)
    summary_path = _summary_path(out_dir, diff.old_source_version, diff.new_source_version)

    diff_path.write_text(
        json.dumps(diff.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    summary_path.write_text(
        json.dumps(diff.summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return diff_path, summary_path


def load_requirements_diff(path: Path) -> RequirementsDiff:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Requirements diff root must be a JSON object.")
    return RequirementsDiff.from_dict(payload)


def compute_text_similarity(old_text: str | None, new_text: str | None) -> float:
    old_normalized = _normalize_for_similarity(old_text)
    new_normalized = _normalize_for_similarity(new_text)
    if not old_normalized and not new_normalized:
        return 1.0
    if not old_normalized or not new_normalized:
        return 0.0

    sequence_score = SequenceMatcher(None, old_normalized, new_normalized).ratio()
    old_tokens = _tokens(old_normalized)
    new_tokens = _tokens(new_normalized)
    if old_tokens or new_tokens:
        token_score = len(old_tokens & new_tokens) / max(len(old_tokens), len(new_tokens))
    else:
        token_score = 0.0
    return round(max(sequence_score, token_score), 4)


def match_requirement_entries(
    old_entries: list[RequirementRegistryEntry],
    new_entries: list[RequirementRegistryEntry],
) -> list[RequirementsDiffEntry]:
    entries: list[RequirementsDiffEntry] = []
    matched_old: set[int] = set()
    matched_new: set[int] = set()

    def add_pair(
        old_index: int,
        new_index: int,
        match_reason: str,
        change_type_override: ChangeType | None = None,
    ) -> None:
        old_entry = old_entries[old_index]
        new_entry = new_entries[new_index]
        similarity = compute_text_similarity(old_entry.normalized_text, new_entry.normalized_text)
        entries.append(
            _diff_entry_for_pair(
                old_entry,
                new_entry,
                change_id=_change_id(len(entries)),
                similarity_score=similarity,
                match_reason=match_reason,
                change_type_override=change_type_override,
            )
        )
        matched_old.add(old_index)
        matched_new.add(new_index)

    old_by_req_uid = _index_by_value(old_entries, "req_uid")
    new_by_req_uid = _index_by_value(new_entries, "req_uid")
    for req_uid in sorted(set(old_by_req_uid) & set(new_by_req_uid)):
        for old_index, new_index in zip(old_by_req_uid[req_uid], new_by_req_uid[req_uid]):
            if old_index not in matched_old and new_index not in matched_new:
                add_pair(old_index, new_index, "exact req_uid match")

    old_by_fingerprint = _index_by_value(old_entries, "semantic_fingerprint")
    new_by_fingerprint = _index_by_value(new_entries, "semantic_fingerprint")
    for fingerprint in sorted(set(old_by_fingerprint) & set(new_by_fingerprint)):
        for old_index in old_by_fingerprint[fingerprint]:
            if old_index in matched_old:
                continue
            new_index = _first_unmatched(new_by_fingerprint[fingerprint], matched_new)
            if new_index is not None:
                add_pair(old_index, new_index, "exact semantic_fingerprint match")

    old_by_source_req_id = _index_by_value(old_entries, "source_req_id")
    new_by_source_req_id = _index_by_value(new_entries, "source_req_id")
    for source_req_id in sorted(set(old_by_source_req_id) & set(new_by_source_req_id)):
        for old_index in old_by_source_req_id[source_req_id]:
            if old_index in matched_old:
                continue
            new_index = _best_unmatched_by_similarity(
                old_entries[old_index],
                new_entries,
                new_by_source_req_id[source_req_id],
                matched_new,
                minimum_similarity=0.0,
            )
            if new_index is not None:
                add_pair(old_index, new_index, "exact source_req_id match")

    split_old_indexes: set[int] = set()
    split_new_indexes: set[int] = set()
    for old_index, old_entry in enumerate(old_entries):
        if old_index in matched_old:
            continue
        similar_new_indexes = [
            new_index
            for new_index, new_entry in enumerate(new_entries)
            if new_index not in matched_new
            and compute_text_similarity(old_entry.normalized_text, new_entry.normalized_text)
            >= SPLIT_MERGE_SIMILARITY_THRESHOLD
        ]
        if len(similar_new_indexes) >= 2:
            for new_index in similar_new_indexes:
                add_pair(old_index, new_index, "split candidate similarity", "split")
            split_old_indexes.add(old_index)
            split_new_indexes.update(similar_new_indexes)

    for new_index, new_entry in enumerate(new_entries):
        if new_index in matched_new or new_index in split_new_indexes:
            continue
        similar_old_indexes = [
            old_index
            for old_index, old_entry in enumerate(old_entries)
            if old_index not in matched_old
            and old_index not in split_old_indexes
            and compute_text_similarity(old_entry.normalized_text, new_entry.normalized_text)
            >= SPLIT_MERGE_SIMILARITY_THRESHOLD
        ]
        if len(similar_old_indexes) >= 2:
            for old_index in similar_old_indexes:
                add_pair(old_index, new_index, "merged candidate similarity", "merged")

    for old_index, old_entry in enumerate(old_entries):
        if old_index in matched_old:
            continue
        new_index = _best_unmatched_by_similarity(
            old_entry,
            new_entries,
            range(len(new_entries)),
            matched_new,
            minimum_similarity=FALLBACK_SIMILARITY_THRESHOLD,
        )
        if new_index is not None:
            add_pair(old_index, new_index, "similarity fallback")

    for old_index, old_entry in enumerate(old_entries):
        if old_index not in matched_old:
            entries.append(
                _diff_entry_for_single(
                    old_entry=old_entry,
                    new_entry=None,
                    change_id=_change_id(len(entries)),
                    change_type="deleted",
                    reason="old entry has no automatic match",
                )
            )
    for new_index, new_entry in enumerate(new_entries):
        if new_index not in matched_new:
            entries.append(
                _diff_entry_for_single(
                    old_entry=None,
                    new_entry=new_entry,
                    change_id=_change_id(len(entries)),
                    change_type="added",
                    reason="new entry has no automatic match",
                )
            )
    return entries


def _diff_entry_for_pair(
    old_entry: RequirementRegistryEntry,
    new_entry: RequirementRegistryEntry,
    *,
    change_id: str,
    similarity_score: float,
    match_reason: str,
    change_type_override: ChangeType | None = None,
) -> RequirementsDiffEntry:
    if change_type_override:
        change_type = change_type_override
        reasons = [match_reason]
    else:
        change_type, reasons = _classify_pair(old_entry, new_entry, similarity_score, match_reason)

    warnings = _combined_warnings(old_entry, new_entry)
    requires_manual_review = _requires_manual_review(old_entry, new_entry, change_type, warnings)
    confidence = _confidence(old_entry, new_entry, change_type, requires_manual_review)
    return RequirementsDiffEntry(
        change_id=change_id,
        change_type=change_type,
        old_req_uid=old_entry.req_uid,
        new_req_uid=new_entry.req_uid,
        old_atom_id=old_entry.atom_id,
        new_atom_id=new_entry.atom_id,
        old_source_req_id=old_entry.source_req_id,
        new_source_req_id=new_entry.source_req_id,
        old_requirement_type=old_entry.requirement_type,
        new_requirement_type=new_entry.requirement_type,
        old_status=old_entry.status,
        new_status=new_entry.status,
        old_normalized_text=old_entry.normalized_text,
        new_normalized_text=new_entry.normalized_text,
        old_semantic_fingerprint=old_entry.semantic_fingerprint,
        new_semantic_fingerprint=new_entry.semantic_fingerprint,
        old_text_hash=old_entry.text_hash,
        new_text_hash=new_entry.text_hash,
        old_source_anchors=old_entry.source_anchors,
        new_source_anchors=new_entry.source_anchors,
        similarity_score=similarity_score,
        confidence=confidence,
        requires_manual_review=requires_manual_review,
        reasons=reasons,
        warnings=warnings,
    )


def _diff_entry_for_single(
    *,
    old_entry: RequirementRegistryEntry | None,
    new_entry: RequirementRegistryEntry | None,
    change_id: str,
    change_type: ChangeType,
    reason: str,
) -> RequirementsDiffEntry:
    warnings = _combined_warnings(old_entry, new_entry)
    requires_manual_review = _requires_manual_review(old_entry, new_entry, change_type, warnings)
    confidence = _confidence(old_entry, new_entry, change_type, requires_manual_review)
    return RequirementsDiffEntry(
        change_id=change_id,
        change_type=change_type,
        old_req_uid=old_entry.req_uid if old_entry else None,
        new_req_uid=new_entry.req_uid if new_entry else None,
        old_atom_id=old_entry.atom_id if old_entry else None,
        new_atom_id=new_entry.atom_id if new_entry else None,
        old_source_req_id=old_entry.source_req_id if old_entry else None,
        new_source_req_id=new_entry.source_req_id if new_entry else None,
        old_requirement_type=old_entry.requirement_type if old_entry else None,
        new_requirement_type=new_entry.requirement_type if new_entry else None,
        old_status=old_entry.status if old_entry else None,
        new_status=new_entry.status if new_entry else None,
        old_normalized_text=old_entry.normalized_text if old_entry else None,
        new_normalized_text=new_entry.normalized_text if new_entry else None,
        old_semantic_fingerprint=old_entry.semantic_fingerprint if old_entry else None,
        new_semantic_fingerprint=new_entry.semantic_fingerprint if new_entry else None,
        old_text_hash=old_entry.text_hash if old_entry else None,
        new_text_hash=new_entry.text_hash if new_entry else None,
        old_source_anchors=old_entry.source_anchors if old_entry else [],
        new_source_anchors=new_entry.source_anchors if new_entry else [],
        similarity_score=None,
        confidence=confidence,
        requires_manual_review=requires_manual_review,
        reasons=[reason],
        warnings=warnings,
    )


def _classify_pair(
    old_entry: RequirementRegistryEntry,
    new_entry: RequirementRegistryEntry,
    similarity_score: float,
    match_reason: str,
) -> tuple[ChangeType, list[str]]:
    reasons = [match_reason]
    anchors_changed = _anchors_signature(old_entry.source_anchors) != _anchors_signature(new_entry.source_anchors)

    if old_entry.req_uid == new_entry.req_uid:
        if old_entry.text_hash == new_entry.text_hash:
            if anchors_changed:
                return "source_anchor_changed", reasons + ["text unchanged but source anchors changed"]
            return "unchanged", reasons + ["req_uid and text_hash are unchanged"]
        if (
            old_entry.requirement_type == new_entry.requirement_type
            and old_entry.status == new_entry.status
            and old_entry.source_req_id == new_entry.source_req_id
            and similarity_score >= HIGH_SIMILARITY_THRESHOLD
        ):
            return "text_changed_no_behavior_change", reasons + ["same req_uid with high text similarity"]
        return "behavior_modified", reasons + ["same req_uid but text_hash changed"]

    if old_entry.semantic_fingerprint == new_entry.semantic_fingerprint:
        if old_entry.text_hash == new_entry.text_hash and anchors_changed:
            return "source_anchor_changed", reasons + ["semantic fingerprint and text match but anchors changed"]
        if old_entry.source_req_id != new_entry.source_req_id:
            return "renumbered", reasons + ["semantic fingerprint match with changed source_req_id"]
        return "renumbered", reasons + ["semantic fingerprint match with changed req_uid"]

    if old_entry.source_req_id and old_entry.source_req_id == new_entry.source_req_id:
        if old_entry.requirement_type != new_entry.requirement_type:
            return "behavior_modified", reasons + ["same source_req_id but requirement_type changed"]
        if old_entry.text_hash == new_entry.text_hash and anchors_changed:
            return "source_anchor_changed", reasons + ["same source_req_id and text but anchors changed"]
        if (
            old_entry.status == new_entry.status
            and similarity_score >= HIGH_SIMILARITY_THRESHOLD
        ):
            return "text_changed_no_behavior_change", reasons + ["same source_req_id with high text similarity"]
        return "behavior_modified", reasons + ["same source_req_id with changed text"]

    if (
        similarity_score >= HIGH_SIMILARITY_THRESHOLD
        and old_entry.requirement_type == new_entry.requirement_type
        and old_entry.status == new_entry.status
    ):
        return "text_changed_no_behavior_change", reasons + ["high similarity fallback with same type and status"]
    if similarity_score >= FALLBACK_SIMILARITY_THRESHOLD:
        return "behavior_modified", reasons + ["similarity fallback requires manual review"]
    return "unclear_match", reasons + ["low-confidence fallback match"]


def _requires_manual_review(
    old_entry: RequirementRegistryEntry | None,
    new_entry: RequirementRegistryEntry | None,
    change_type: ChangeType,
    warnings: list[str],
) -> bool:
    if change_type in {"behavior_modified", "split", "merged", "unclear_match"}:
        return True
    if _has_risky_zone(old_entry) or _has_risky_zone(new_entry):
        return True
    if any(_is_risky_warning(warning) for warning in warnings):
        return True
    if old_entry and new_entry and old_entry.requirement_type != new_entry.requirement_type:
        return True
    return False


def _confidence(
    old_entry: RequirementRegistryEntry | None,
    new_entry: RequirementRegistryEntry | None,
    change_type: ChangeType,
    requires_manual_review: bool,
) -> DiffConfidence:
    if change_type == "unchanged" and not requires_manual_review:
        confidence: DiffConfidence = "high"
    elif change_type in {"split", "merged", "behavior_modified", "unclear_match"} or requires_manual_review:
        confidence = "low"
    else:
        confidence = "medium"

    if _has_risky_status(old_entry) or _has_risky_status(new_entry):
        return _cap_confidence(confidence, "medium")
    return confidence


def _summary(
    *,
    old_registry_path: Path,
    new_registry_path: Path,
    old_source_version: str,
    new_source_version: str,
    old_entries_total: int,
    new_entries_total: int,
    old_diff_eligible_entries: int,
    new_diff_eligible_entries: int,
    old_duplicate_req_uid_diff_eligible_count: int,
    new_duplicate_req_uid_diff_eligible_count: int,
    old_canonical_report: CanonicalizationReport,
    new_canonical_report: CanonicalizationReport,
    entries: list[RequirementsDiffEntry],
    warnings: list[str],
    blocking_reasons: list[str],
) -> dict[str, Any]:
    counts = Counter(entry.change_type for entry in entries)
    summary_warnings = sorted(set(warnings))
    if blocking_reasons:
        diff_status: DiffStatus = "blocked"
    elif summary_warnings or any(entry.requires_manual_review for entry in entries):
        diff_status = "pass-with-warnings"
    else:
        diff_status = "pass"
    return {
        "old_registry_path": str(old_registry_path),
        "new_registry_path": str(new_registry_path),
        "old_source_version": old_source_version,
        "new_source_version": new_source_version,
        "diff_status": diff_status,
        "old_entries_total": old_entries_total,
        "new_entries_total": new_entries_total,
        "old_diff_eligible_entries": old_diff_eligible_entries,
        "new_diff_eligible_entries": new_diff_eligible_entries,
        "old_diff_canonical_entries": old_canonical_report.output_entries_total,
        "new_diff_canonical_entries": new_canonical_report.output_entries_total,
        "old_diff_excluded_entries": old_entries_total - old_diff_eligible_entries,
        "new_diff_excluded_entries": new_entries_total - new_diff_eligible_entries,
        "old_duplicate_req_uid_diff_eligible_count": old_duplicate_req_uid_diff_eligible_count,
        "new_duplicate_req_uid_diff_eligible_count": new_duplicate_req_uid_diff_eligible_count,
        "old_canonicalized_duplicate_groups": old_canonical_report.canonicalized_groups_total,
        "new_canonicalized_duplicate_groups": new_canonical_report.canonicalized_groups_total,
        "old_unresolved_duplicate_groups": old_canonical_report.unresolved_duplicate_groups_total,
        "new_unresolved_duplicate_groups": new_canonical_report.unresolved_duplicate_groups_total,
        "old_unresolved_duplicate_req_uids": old_canonical_report.unresolved_req_uids,
        "new_unresolved_duplicate_req_uids": new_canonical_report.unresolved_req_uids,
        "entries_total": len(entries),
        "unchanged": counts.get("unchanged", 0),
        "text_changed_no_behavior_change": counts.get("text_changed_no_behavior_change", 0),
        "behavior_modified": counts.get("behavior_modified", 0),
        "added": counts.get("added", 0),
        "deleted": counts.get("deleted", 0),
        "moved": counts.get("moved", 0),
        "renumbered": counts.get("renumbered", 0),
        "split": counts.get("split", 0),
        "merged": counts.get("merged", 0),
        "source_anchor_changed": counts.get("source_anchor_changed", 0),
        "unclear_match": counts.get("unclear_match", 0),
        "requires_manual_review_count": sum(1 for entry in entries if entry.requires_manual_review),
        "warnings": summary_warnings,
        "blocking_reasons": blocking_reasons,
    }


def _make_diff(
    *,
    old_registry_path: Path,
    new_registry_path: Path,
    old_source_version: str,
    new_source_version: str,
    old_entries_total: int,
    new_entries_total: int,
    old_diff_eligible_entries: int,
    new_diff_eligible_entries: int,
    old_duplicate_req_uid_diff_eligible_count: int,
    new_duplicate_req_uid_diff_eligible_count: int,
    old_canonical_report: CanonicalizationReport,
    new_canonical_report: CanonicalizationReport,
    entries: list[RequirementsDiffEntry],
    warnings: list[str],
    blocking_reasons: list[str],
    created_by_tool: str,
) -> RequirementsDiff:
    warnings = sorted(set(warnings))
    summary = _summary(
        old_registry_path=old_registry_path,
        new_registry_path=new_registry_path,
        old_source_version=old_source_version,
        new_source_version=new_source_version,
        old_entries_total=old_entries_total,
        new_entries_total=new_entries_total,
        old_diff_eligible_entries=old_diff_eligible_entries,
        new_diff_eligible_entries=new_diff_eligible_entries,
        old_duplicate_req_uid_diff_eligible_count=old_duplicate_req_uid_diff_eligible_count,
        new_duplicate_req_uid_diff_eligible_count=new_duplicate_req_uid_diff_eligible_count,
        old_canonical_report=old_canonical_report,
        new_canonical_report=new_canonical_report,
        entries=entries,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
    )
    return RequirementsDiff(
        old_registry_path=str(old_registry_path),
        new_registry_path=str(new_registry_path),
        old_source_version=old_source_version,
        new_source_version=new_source_version,
        created_at_utc=_utc_now_iso(),
        created_by_tool=created_by_tool,
        entries=entries,
        summary=summary,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
    )


def _index_by_value(
    entries: list[RequirementRegistryEntry],
    attribute: str,
) -> dict[str, list[int]]:
    indexed: dict[str, list[int]] = defaultdict(list)
    for index, entry in enumerate(entries):
        value = getattr(entry, attribute)
        if value:
            indexed[str(value)].append(index)
    return indexed


def _first_unmatched(indexes: list[int], matched: set[int]) -> int | None:
    for index in indexes:
        if index not in matched:
            return index
    return None


def _best_unmatched_by_similarity(
    old_entry: RequirementRegistryEntry,
    new_entries: list[RequirementRegistryEntry],
    candidate_indexes: Any,
    matched_new: set[int],
    *,
    minimum_similarity: float,
) -> int | None:
    best_index: int | None = None
    best_similarity = minimum_similarity
    for new_index in candidate_indexes:
        if new_index in matched_new:
            continue
        similarity = compute_text_similarity(old_entry.normalized_text, new_entries[new_index].normalized_text)
        if similarity >= best_similarity:
            best_index = new_index
            best_similarity = similarity
    return best_index


def _combined_warnings(
    old_entry: RequirementRegistryEntry | None,
    new_entry: RequirementRegistryEntry | None,
) -> list[str]:
    warnings: list[str] = []
    if old_entry:
        warnings.extend(old_entry.warnings)
    if new_entry:
        warnings.extend(new_entry.warnings)
    return sorted(set(warnings))


def _entry_warnings(entries: list[RequirementsDiffEntry]) -> list[str]:
    warnings: list[str] = []
    for entry in entries:
        warnings.extend(entry.warnings)
    return sorted(set(warnings))


def _canonicalize_diff_entries(
    entries: list[RequirementRegistryEntry],
) -> tuple[list[RequirementRegistryEntry], CanonicalizationReport]:
    groups: dict[str, list[RequirementRegistryEntry]] = defaultdict(list)
    for entry in entries:
        groups[entry.req_uid].append(entry)

    output_entries: list[RequirementRegistryEntry] = []
    canonicalized_req_uids: list[str] = []
    unresolved_req_uids: list[str] = []
    warnings: list[str] = []

    for req_uid in sorted(groups):
        group = sorted(groups[req_uid], key=_canonical_entry_sort_key)
        if len(group) == 1:
            output_entries.append(group[0])
            continue
        if _is_benign_duplicate_group(group):
            output_entries.append(_canonical_entry_for_group(group))
            canonicalized_req_uids.append(req_uid)
            warnings.append(
                f"Canonicalized repeated source occurrences for duplicate req_uid: {req_uid}"
            )
        else:
            output_entries.extend(group)
            unresolved_req_uids.append(req_uid)

    duplicate_groups_total = sum(1 for group in groups.values() if len(group) > 1)
    return output_entries, CanonicalizationReport(
        input_entries_total=len(entries),
        output_entries_total=len(output_entries),
        duplicate_groups_total=duplicate_groups_total,
        canonicalized_groups_total=len(canonicalized_req_uids),
        unresolved_duplicate_groups_total=len(unresolved_req_uids),
        canonicalized_req_uids=canonicalized_req_uids,
        unresolved_req_uids=unresolved_req_uids,
        warnings=sorted(set(warnings)),
    )


def _is_benign_duplicate_group(group: list[RequirementRegistryEntry]) -> bool:
    if len(group) <= 1:
        return False
    fingerprints = {_canonical_duplicate_fingerprint(entry) for entry in group}
    return len(fingerprints) == 1


def _canonical_duplicate_fingerprint(entry: RequirementRegistryEntry) -> tuple[Any, ...]:
    return (
        entry.req_uid,
        entry.normalized_text,
        entry.requirement_type,
        entry.status,
        entry.source_req_id,
        entry.semantic_fingerprint,
        getattr(entry, "context_hash", None),
        getattr(entry, "context_text", None),
        entry.object,
        entry.condition,
        entry.expected_behavior,
    )


def _canonical_entry_for_group(group: list[RequirementRegistryEntry]) -> RequirementRegistryEntry:
    canonical = min(group, key=_canonical_entry_sort_key)
    merged_anchors = _merged_source_anchors(group)
    merged_warnings = sorted(
        {
            *canonical.warnings,
            *(
                warning
                for entry in group
                for warning in entry.warnings
            ),
            "Canonicalized repeated source occurrences for duplicate req_uid.",
        }
    )
    merged_context_warnings = sorted(
        {
            warning
            for entry in group
            for warning in getattr(entry, "context_warnings", [])
        }
    )
    return replace(
        canonical,
        source_anchors=merged_anchors,
        warnings=merged_warnings,
        context_warnings=merged_context_warnings,
    )


def _merged_source_anchors(group: list[RequirementRegistryEntry]) -> list[SourceAnchor]:
    anchors_by_signature: dict[tuple[Any, ...], SourceAnchor] = {}
    for entry in group:
        for anchor in entry.source_anchors:
            anchors_by_signature[_source_anchor_signature(anchor)] = anchor
    return [
        anchors_by_signature[signature]
        for signature in sorted(anchors_by_signature)
    ]


def _canonical_entry_sort_key(entry: RequirementRegistryEntry) -> tuple[Any, ...]:
    return (
        entry.entry_uid,
        _anchors_signature(entry.source_anchors),
        entry.atom_id,
    )


def _source_anchor_signature(anchor: SourceAnchor) -> tuple[Any, ...]:
    return (
        anchor.source_doc,
        anchor.source_version,
        anchor.part,
        anchor.xpath,
        anchor.node_id,
        anchor.value_type,
        tuple(anchor.flags),
        anchor.aggregate_kind,
        anchor.aggregate_confidence,
    )


def _has_risky_status(entry: RequirementRegistryEntry | None) -> bool:
    return bool(entry and entry.status in {"unclear", "gap", "source_only"})


def _has_risky_zone(entry: RequirementRegistryEntry | None) -> bool:
    if entry is None:
        return False
    if any(_is_risky_warning(warning) for warning in entry.warnings):
        return True
    for anchor in entry.source_anchors:
        if anchor.aggregate_kind or anchor.value_type == "aggregate":
            return True
        if set(anchor.flags) & {"tracked_delete", "hidden_text", "comment"}:
            return True
    return False


def _is_risky_warning(warning: str) -> bool:
    lowered = warning.casefold()
    return any(
        token in lowered
        for token in ["tracked deletion", "hidden text", "comment source", "aggregate source"]
    )


def _anchors_signature(anchors: list[SourceAnchor]) -> list[tuple[Any, ...]]:
    return sorted(
        (
            anchor.source_doc,
            anchor.part,
            anchor.xpath,
            anchor.node_id,
            anchor.value_type,
            tuple(anchor.flags),
            anchor.aggregate_kind,
            anchor.aggregate_confidence,
        )
        for anchor in anchors
    )


def _cap_confidence(confidence: DiffConfidence, maximum: DiffConfidence) -> DiffConfidence:
    rank = {"low": 0, "medium": 1, "high": 2}
    if rank[confidence] <= rank[maximum]:
        return confidence
    return maximum


def _duplicate_req_uids(entries: list[RequirementRegistryEntry]) -> list[str]:
    counts = Counter(entry.req_uid for entry in entries)
    return sorted(req_uid for req_uid, count in counts.items() if count > 1)


def _duplicate_entry_uids(entries: list[RequirementRegistryEntry]) -> list[str]:
    counts = Counter(_entry_uid(entry) for entry in entries)
    return sorted(entry_uid for entry_uid, count in counts.items() if entry_uid and count > 1)


def _diff_eligible_entries(entries: list[RequirementRegistryEntry]) -> list[RequirementRegistryEntry]:
    return [entry for entry in entries if _is_diff_eligible(entry)]


def _is_diff_eligible(entry: RequirementRegistryEntry) -> bool:
    return bool(getattr(entry, "diff_eligible", entry.status != "source_only"))


def _entry_uid(entry: RequirementRegistryEntry) -> str | None:
    return getattr(entry, "entry_uid", None)


def _load_optional_summary(path: Path, warnings: list[str]) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - missing summary should not crash diff.
        warnings.append(f"registry summary could not be read: {path}: {exc}")
        return {}
    if not isinstance(payload, dict):
        warnings.append(f"registry summary root is not a JSON object: {path}")
        return {}
    return payload


def _summary_status(summary: dict[str, Any]) -> str | None:
    status = summary.get("registry_status")
    return str(status) if status is not None else None


def _source_version(
    summary: dict[str, Any],
    entries: list[RequirementRegistryEntry],
    registry_path: Path,
) -> str:
    if summary.get("source_version"):
        return str(summary["source_version"])
    if entries:
        return entries[0].source_version
    return _version_from_registry_path(registry_path)


def _version_from_registry_path(path: Path) -> str:
    name = path.name
    if name.startswith("requirements.") and name.endswith(".jsonl"):
        return name[len("requirements.") : -len(".jsonl")]
    return "unknown"


def _infer_summary_path(registry_path: Path) -> Path:
    source_version = _version_from_registry_path(registry_path)
    if source_version != "unknown":
        return registry_path.with_name(f"requirements-summary.{source_version}.json")
    return registry_path.with_name(f"{registry_path.stem}-summary.json")


def _diff_path(out_dir: Path, old_source_version: str, new_source_version: str) -> Path:
    return Path(out_dir) / f"{DIFF_PREFIX}.{old_source_version}-to-{new_source_version}.json"


def _summary_path(out_dir: Path, old_source_version: str, new_source_version: str) -> Path:
    return Path(out_dir) / f"{DIFF_SUMMARY_PREFIX}.{old_source_version}-to-{new_source_version}.json"


def _change_id(index: int) -> str:
    return f"CHG-{index + 1:06d}"


def _normalize_for_similarity(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", value.casefold()).strip()


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[\wА-Яа-яЁё]+", value.casefold()))


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
