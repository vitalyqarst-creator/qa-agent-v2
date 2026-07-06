from __future__ import annotations

from collections import defaultdict
from typing import Any

CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}
REQ_PREFIX = "REQ-"


def build_req_to_draft_map(
    *,
    draft_proposal: dict[str, Any] | None = None,
    decision_pack: dict[str, Any] | None = None,
    draft_review: dict[str, Any] | None = None,
    draft_revision_plan: dict[str, Any] | None = None,
    context_bundle: dict[str, Any] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Build a conservative req_uid -> real source-proposal draft mapping."""

    proposal = draft_proposal or {}
    proposal_drafts = {
        str(draft.get("draft_id")): draft
        for draft in proposal.get("draft_test_cases") or []
        if draft.get("draft_id")
    }
    if not proposal_drafts:
        return {}

    source_req_to_req_uids = _source_req_to_req_uids(context_bundle or {}, proposal_drafts)
    review_by_draft = _index_by_draft_id((draft_review or {}).get("draft_reviews"))
    revision_by_draft = _index_by_draft_id((draft_revision_plan or {}).get("revision_items"))
    decision_by_draft = _index_by_draft_id((decision_pack or {}).get("draft_decisions"))

    entries: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for draft_id, draft in proposal_drafts.items():
        proposed_tc_id = str(draft.get("proposed_tc_id") or "")
        direct_req_uids = _unique(
            [
                *_string_list(draft.get("source_requirement_uids")),
                *_string_list(draft.get("candidate_req_uids")),
                *_string_list(draft.get("req_uids")),
                *_req_uids_from_grounding_profiles(draft),
            ]
        )
        for req_uid in direct_req_uids:
            _add_mapping_entry(
                entries,
                req_uid=req_uid,
                draft_id=draft_id,
                proposed_tc_id=proposed_tc_id,
                source="new_tc_draft_proposal",
                confidence="high",
                evidence=[
                    "source proposal directly lists req_uid for draft",
                    *_draft_status_evidence(draft_id, review_by_draft, revision_by_draft, decision_by_draft),
                ],
            )

        for source_req_id in _string_list(draft.get("source_req_ids")):
            mapped_req_uids = source_req_to_req_uids.get(source_req_id, [])
            confidence = "medium" if len(mapped_req_uids) == 1 else "low"
            for req_uid in mapped_req_uids:
                _add_mapping_entry(
                    entries,
                    req_uid=req_uid,
                    draft_id=draft_id,
                    proposed_tc_id=proposed_tc_id,
                    source="new_tc_draft_proposal.source_req_id",
                    confidence=confidence,
                    evidence=[
                        f"source_req_id {source_req_id} maps to {len(mapped_req_uids)} req_uid(s)",
                        *_draft_status_evidence(draft_id, review_by_draft, revision_by_draft, decision_by_draft),
                    ],
                )

    for item in (decision_pack or {}).get("draft_decisions") or []:
        draft_id = str(item.get("draft_id") or "")
        if draft_id not in proposal_drafts:
            continue
        proposed_tc_id = str(item.get("proposed_tc_id") or proposal_drafts[draft_id].get("proposed_tc_id") or "")
        for req_uid in _string_list(item.get("candidate_req_uids")):
            _add_mapping_entry(
                entries,
                req_uid=req_uid,
                draft_id=draft_id,
                proposed_tc_id=proposed_tc_id,
                source="new_tc_revision_decision_pack",
                confidence="medium",
                evidence=["decision pack lists candidate_req_uids for an existing source proposal draft"],
            )
        for source_req_id in _string_list(item.get("source_req_ids")):
            mapped_req_uids = source_req_to_req_uids.get(source_req_id, [])
            confidence = "medium" if len(mapped_req_uids) == 1 else "low"
            for req_uid in mapped_req_uids:
                _add_mapping_entry(
                    entries,
                    req_uid=req_uid,
                    draft_id=draft_id,
                    proposed_tc_id=proposed_tc_id,
                    source="new_tc_revision_decision_pack.source_req_id",
                    confidence=confidence,
                    evidence=[f"source_req_id {source_req_id} maps to {len(mapped_req_uids)} req_uid(s)"],
                )

    return {
        req_uid: sorted(draft_entries.values(), key=lambda entry: (entry["draft_id"], entry["source"]))
        for req_uid, draft_entries in sorted(entries.items())
        if draft_entries
    }


def draft_ids_for_req_uids(
    req_uids: list[str],
    req_to_draft_map: dict[str, list[dict[str, Any]]],
    *,
    min_confidence: str = "medium",
) -> list[str]:
    min_rank = CONFIDENCE_RANK[min_confidence]
    return _unique(
        entry["draft_id"]
        for req_uid in req_uids
        for entry in req_to_draft_map.get(str(req_uid), [])
        if CONFIDENCE_RANK.get(str(entry.get("confidence")), -1) >= min_rank
    )


def draft_mapping_entries_for_req_uids(
    req_uids: list[str],
    req_to_draft_map: dict[str, list[dict[str, Any]]],
    *,
    min_confidence: str = "medium",
) -> list[dict[str, Any]]:
    min_rank = CONFIDENCE_RANK[min_confidence]
    return [
        entry
        for req_uid in req_uids
        for entry in req_to_draft_map.get(str(req_uid), [])
        if CONFIDENCE_RANK.get(str(entry.get("confidence")), -1) >= min_rank
    ]


def draft_mapping_diagnostics_for_rows(
    rows: list[Any],
    req_to_draft_map: dict[str, list[dict[str, Any]]],
    *,
    fixed_rows: list[str] | None = None,
) -> dict[str, Any]:
    rows_with_missing_affected_drafts = []
    unmapped_req_uids: set[str] = set()
    for row in rows:
        if isinstance(row, dict):
            row_id = row.get("row_id")
            affected_drafts = list(row.get("affected_drafts") or row.get("affected_draft_ids") or [])
            affected_requirements = list(row.get("affected_requirements") or row.get("affected_req_uids") or [])
        else:
            row_id = getattr(row, "row_id", None)
            affected_drafts = list(getattr(row, "affected_drafts", []) or [])
            affected_requirements = list(getattr(row, "affected_requirements", []) or [])
        if affected_requirements and not affected_drafts:
            rows_with_missing_affected_drafts.append(row_id)
        for req_uid in affected_requirements:
            if not draft_mapping_entries_for_req_uids([str(req_uid)], req_to_draft_map, min_confidence="medium"):
                unmapped_req_uids.add(str(req_uid))

    return {
        "req_to_draft_map_count": len(req_to_draft_map),
        "req_to_draft_entry_count": sum(len(entries) for entries in req_to_draft_map.values()),
        "unmapped_req_uids": sorted(unmapped_req_uids),
        "rows_with_missing_affected_drafts": sorted(str(row_id) for row_id in rows_with_missing_affected_drafts if row_id),
        "fixed_rows": sorted(fixed_rows or []),
    }


def _add_mapping_entry(
    entries: dict[str, dict[str, dict[str, Any]]],
    *,
    req_uid: str,
    draft_id: str,
    proposed_tc_id: str,
    source: str,
    confidence: str,
    evidence: list[str],
) -> None:
    if not req_uid or not draft_id:
        return
    entry = entries[str(req_uid)].setdefault(
        str(draft_id),
        {
            "draft_id": str(draft_id),
            "proposed_tc_id": proposed_tc_id,
            "source": source,
            "sources": [],
            "confidence": confidence,
            "evidence": [],
        },
    )
    entry["sources"] = _unique([*entry.get("sources", []), source])
    if CONFIDENCE_RANK[confidence] > CONFIDENCE_RANK.get(str(entry.get("confidence")), -1):
        entry["confidence"] = confidence
        entry["source"] = source
    entry["evidence"] = _unique([*entry.get("evidence", []), *evidence])


def _source_req_to_req_uids(
    context_bundle: dict[str, Any],
    proposal_drafts: dict[str, dict[str, Any]],
) -> dict[str, list[str]]:
    result: dict[str, list[str]] = defaultdict(list)
    for item in context_bundle.get("candidate_requirements") or []:
        req_uid = str(item.get("req_uid") or "")
        source_req_id = str(item.get("source_req_id") or "")
        if req_uid and source_req_id:
            result[source_req_id].append(req_uid)
    for draft in proposal_drafts.values():
        for profile in draft.get("source_grounding_profiles") or []:
            req_uid = str(profile.get("req_uid") or "")
            source_req_id = str(profile.get("source_req_id") or "")
            if req_uid and source_req_id:
                result[source_req_id].append(req_uid)
    return {key: _unique(values) for key, values in result.items()}


def _req_uids_from_grounding_profiles(draft: dict[str, Any]) -> list[str]:
    return _unique(
        str(profile.get("req_uid"))
        for profile in draft.get("source_grounding_profiles") or []
        if str(profile.get("req_uid") or "").startswith(REQ_PREFIX)
    )


def _draft_status_evidence(
    draft_id: str,
    review_by_draft: dict[str, dict[str, Any]],
    revision_by_draft: dict[str, dict[str, Any]],
    decision_by_draft: dict[str, dict[str, Any]],
) -> list[str]:
    evidence = []
    if draft_id in review_by_draft:
        evidence.append(f"draft review status={review_by_draft[draft_id].get('review_status')}")
    if draft_id in revision_by_draft:
        evidence.append(f"revision target={revision_by_draft[draft_id].get('target_revision_status')}")
    if draft_id in decision_by_draft:
        evidence.append(f"decision pack decision={decision_by_draft[draft_id].get('decision')}")
    return evidence


def _index_by_draft_id(items: Any) -> dict[str, dict[str, Any]]:
    return {str(item.get("draft_id")): item for item in items or [] if item.get("draft_id")}


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item or "").strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _unique(values: Any) -> list[str]:
    result = []
    seen = set()
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result
