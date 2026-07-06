from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


AGGREGATE_MARKERS = (
    "assembled_from",
    "test_case_count",
    "aggregate",
    "Порядок Сборки",
    "source files assembled",
)

STOPWORDS = {
    "для",
    "при",
    "если",
    "или",
    "что",
    "как",
    "это",
    "все",
    "без",
    "над",
    "под",
    "после",
    "перед",
    "должен",
    "должна",
    "должны",
    "система",
    "поле",
    "поля",
    "значение",
    "значения",
    "заявка",
    "заявки",
    "форме",
    "форма",
    "тестовые",
    "данные",
    "ожидаемый",
    "результат",
    "пользователь",
    "отображается",
    "отображаются",
    "отображать",
}


RECOMMENDATION_OVERRIDES: dict[str, dict[str, str]] = {
    "MDR-000001": {
        "option": "OPT-NO-NEW",
        "confidence": "high",
        "rationale": "Требование про заголовок карточки при редактировании уже напрямую покрыто TC-AF-CARD-002: existing TC проверяет заголовок существующей заявки и ожидает формат с номером заявки.",
        "no_new": "Новый TC не нужен: покрытие есть в TC-AF-CARD-002. Если потребуется только новая трассировка REQ-*, это не create-new, а traceability maintenance.",
    },
    "MDR-000002": {
        "option": "OPT-NO-NEW",
        "confidence": "high",
        "rationale": "Требование про первичную загрузку/очистку фильтров и активные заявки текущего автора уже покрыто TC-AMSR-001.",
        "no_new": "Новый TC не нужен: TC-AMSR-001 проверяет, что показываются активные заявки текущего автора и не показывается заявка другого автора.",
    },
    "MDR-000003": {
        "option": "OPT-NO-NEW",
        "confidence": "high",
        "rationale": "Требование про справочник значений поля «Социальный статус» уже покрыто TC-AFEIG-002.",
        "no_new": "Новый TC не нужен: TC-AFEIG-002 проверяет состав значений раскрывающегося списка социального статуса.",
    },
    "MDR-000004": {
        "option": "OPT-NO-NEW",
        "confidence": "medium",
        "rationale": "Основной duplicate-risk по ОПФ покрыт TC-AFEIG-008. В требовании также есть видимость и автозаполнение DaData, которые выглядят покрытыми соседними TC в том же файле, но перед подтверждением стоит проверить не только TC-AFEIG-008.",
        "no_new": "Новый TC по составу ОПФ не нужен. Если reviewer сочтет, что visibility/autofill часть не покрыта существующими TC, это лучше оформить как EXTEND/отдельный split, а не дублировать TC-AFEIG-008.",
    },
    "MDR-000005": {
        "option": "OPT-SEPARATE",
        "confidence": "medium",
        "rationale": "Связанный TC-ACCA-007 относится к автосборке адреса регистрации, а требование в строке про ОПФ/занятость. Это похоже на ложное similarity-срабатывание по общим словам, а не на покрытие.",
    },
    "MDR-000006": {
        "option": "OPT-SEPARATE",
        "confidence": "medium",
        "rationale": "Связанные TC-ACCA-004/005 относятся к адресам и DaData-подсказкам, а требование про среднемесячный доход, числовой ввод и проверки X/Y. Это не покрытие указанного поведения.",
    },
    "MDR-000007": {
        "option": "OPT-NO-NEW",
        "confidence": "medium",
        "rationale": "Поведение способа подтверждения дохода уже покрыто набором TC-AFEIG-026/027/043 и связанными print-form проверками. Нужна ручная сверка, что все части требования действительно уже покрыты.",
        "no_new": "Новый TC не нужен, если reviewer подтверждает существующее покрытие default «Бумажное», сценарий «Госуслуги», QR/запрос после сохранения и бумажное подтверждение.",
    },
    "MDR-000008": {
        "option": "OPT-SEPARATE",
        "confidence": "medium",
        "rationale": "Связанный TC-ACCEI-003 про редактируемость контактов, а требование про способ подтверждения дохода/Госуслуги. Это не выглядит как существующее покрытие.",
    },
    "MDR-000009": {
        "option": "OPT-REVISE",
        "confidence": "medium",
        "rationale": "Источник по серии паспорта достаточно конкретен для revised draft: поле «Серия паспорта», видимость всегда, формат 4 цифры.",
    },
    "MDR-000010": {
        "option": "OPT-SPLIT",
        "confidence": "medium",
        "rationale": "Строка объединяет разные требования: серия паспорта и социальный статус. Их нельзя безопасно превращать в один draft; нужно разделить решения.",
    },
    "MDR-000011": {
        "option": "OPT-REVISE",
        "confidence": "medium",
        "rationale": "Источник содержит конкретные observable outcomes для заголовка заявки и первичной загрузки списка; при этом duplicate rows рекомендуют закрыть их existing coverage. Revised stage должен учитывать no-new решения и не создавать дубликаты.",
    },
    "MDR-000012": {
        "option": "OPT-SPLIT",
        "confidence": "high",
        "rationale": "Строка объединяет набор разных требований без draft: регион, кнопка «Продолжить» и другие независимые behaviors. Это нужно разделить по объектам/поведениям.",
    },
    "MDR-000013": {
        "option": "OPT-REPLACE",
        "confidence": "medium",
        "rationale": "Rejected draft по серии паспорта лучше переписать из source facts, а не патчить на месте.",
    },
    "MDR-000014": {
        "option": "OPT-SPLIT",
        "confidence": "high",
        "rationale": "Группа содержит несколько rejected drafts и разных требований. Без split получится один неатомарный draft с риском выдумать шаги.",
    },
    "MDR-000015": {
        "option": "OPT-MANUAL",
        "confidence": "medium",
        "rationale": "Это агрегирующая manual-only строка по нескольким unresolved decisions. Ее нельзя закрыть одним no-new/defer без подтверждения предыдущих строк.",
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Russian reviewer assist artifacts for manual decision rows.")
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--test-cases-dir", required=True, type=Path)
    parser.add_argument("--package-id", default="WPKG-000001")
    args = parser.parse_args()

    work_dir = args.work_dir
    package_id = args.package_id
    matrix_path = work_dir / f"manual-decision-matrix-{package_id}.json"
    bundle_path = work_dir / f"create-new-tc-context-bundle-{package_id}.json"
    proposal_path = work_dir / f"new-tc-draft-proposal-{package_id}.json"
    base_csv_path = work_dir / f"manual-decision-reviewer-answer-pack-{package_id}.ru.utf8-bom.csv"

    matrix = _read_json(matrix_path)
    bundle = _read_json(bundle_path)
    proposal = _read_json(proposal_path)
    base_rows = list(csv.DictReader(base_csv_path.open("r", encoding="utf-8-sig", newline="")))

    clusters = {item["cluster_id"]: item for item in matrix.get("decision_clusters", [])}
    row_meta = {item["row_id"]: item for item in matrix.get("reviewer_decision_rows", [])}
    reqs = {item["req_uid"]: item for item in bundle.get("candidate_requirements", [])}
    drafts = {item["draft_id"]: item for item in proposal.get("draft_test_cases", [])}
    tc_blocks = _load_tc_blocks(args.test_cases_dir)

    analyses = []
    filled_rows = []
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    for row in base_rows:
        meta = row_meta[row["row_id"]]
        cluster = clusters.get(row["cluster_id"], {})
        analysis = _analyze_row(row, meta, cluster, reqs, drafts, tc_blocks)
        analyses.append(analysis)
        filled_rows.append(_filled_answer_row(row, analysis, now))

    report = {
        "package_id": package_id,
        "report_status": "pass-with-warnings",
        "rows_total": len(analyses),
        "recommendation_counts": dict(Counter(item["recommended_option_id"] for item in analyses)),
        "high_confidence_count": sum(1 for item in analyses if item["agent_confidence"] == "high"),
        "medium_confidence_count": sum(1 for item in analyses if item["agent_confidence"] == "medium"),
        "low_confidence_count": sum(1 for item in analyses if item["agent_confidence"] == "low"),
        "tc_blocks_indexed": len(tc_blocks),
        "canonical_write_allowed": False,
        "selected_options_are_agent_proposal_only": True,
        "row_analyses": analyses,
        "input_paths": {
            "manual_decision_matrix": str(matrix_path),
            "context_bundle": str(bundle_path),
            "draft_proposal": str(proposal_path),
            "base_answer_pack": str(base_csv_path),
            "test_cases_dir": str(args.test_cases_dir),
        },
        "warnings": [
            "Файл с заполненными selected_option_id является вариантом агента для подтверждения, а не reviewer approval.",
            "Existing TC используется только как coverage evidence; источником бизнес-правил остается ФТ.",
            "Для строк с confidence=medium/high все равно нужна финальная проверка reviewer перед import.",
        ],
        "created_at_utc": now,
        "created_by_tool": "scripts/build_manual_decision_review_assist.py",
    }

    out_json = work_dir / f"manual-decision-review-assist-{package_id}.json"
    out_md = work_dir / f"manual-decision-review-assist-{package_id}.md"
    out_csv = work_dir / f"manual-decision-reviewer-answer-pack-{package_id}.agent-filled-for-confirmation.ru.utf8-bom.csv"
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    out_md.write_text(_render_markdown(report), encoding="utf-8-sig", newline="\n")
    _write_csv(out_csv, filled_rows)

    print(
        json.dumps(
            {
                "json_path": str(out_json),
                "markdown_path": str(out_md),
                "csv_path": str(out_csv),
                "rows_total": len(analyses),
                "recommendation_counts": report["recommendation_counts"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_tc_blocks(test_cases_dir: Path) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for path in sorted(test_cases_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        first_lines = "\n".join(text.splitlines()[:80]).casefold()
        if any(marker.casefold() in first_lines for marker in AGGREGATE_MARKERS):
            continue
        lines = text.splitlines()
        starts = [
            index
            for index, line in enumerate(lines)
            if re.match(r"^#{2,6}\s+TC-[A-Za-z0-9_-]+\b", line.strip())
        ]
        for pos, start in enumerate(starts):
            end = starts[pos + 1] if pos + 1 < len(starts) else len(lines)
            block_lines = lines[start:end]
            heading = block_lines[0].strip()
            match = re.match(r"^#{2,6}\s+(TC-[A-Za-z0-9_-]+)\b", heading)
            if not match:
                continue
            text_block = "\n".join(block_lines).strip()
            meta = _extract_meta(block_lines)
            sections = _extract_sections(block_lines)
            blocks.append(
                {
                    "tc_id": match.group(1),
                    "file_path": str(path),
                    "start_line": start + 1,
                    "heading": heading,
                    "title": meta.get("Название") or meta.get("Title") or "",
                    "traceability": meta.get("Трассировка") or meta.get("Traceability") or "",
                    "test_data": _section_by_keywords(sections, ("тестовые данные", "test data")),
                    "steps": _section_by_keywords(sections, ("шаги", "steps")),
                    "expected": _section_by_keywords(sections, ("ожидаемый", "expected")),
                    "text": text_block,
                    "tokens": _tokens(text_block),
                }
            )
    return blocks


def _extract_meta(lines: list[str]) -> dict[str, str]:
    meta: dict[str, str] = {}
    for line in lines[:80]:
        match = re.match(r"^\*\*(.+?):\*\*\s*(.*)$", line.strip())
        if match:
            meta[match.group(1).strip()] = match.group(2).strip()
    return meta


def _extract_sections(lines: list[str]) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines:
        match = re.match(r"^#{3,6}\s+(.+?)\s*$", line)
        if match:
            current = match.group(1).strip()
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line)
    return {name: _collapse("\n".join(value)) for name, value in sections.items()}


def _section_by_keywords(sections: dict[str, str], keywords: tuple[str, ...]) -> str:
    for name, value in sections.items():
        lowered = name.casefold()
        if any(keyword in lowered for keyword in keywords):
            return value
    return ""


def _analyze_row(
    row: dict[str, str],
    meta: dict[str, Any],
    cluster: dict[str, Any],
    reqs: dict[str, dict[str, Any]],
    drafts: dict[str, dict[str, Any]],
    tc_blocks: list[dict[str, Any]],
) -> dict[str, Any]:
    req_ids = meta.get("affected_requirements") or _split_cell(row.get("affected_requirements", ""))
    draft_ids = meta.get("affected_drafts") or _split_cell(row.get("affected_drafts", ""))
    req_summaries = [_requirement_summary(reqs.get(req_uid, {"req_uid": req_uid})) for req_uid in req_ids]
    draft_summaries = [_draft_summary(drafts.get(draft_id, {"draft_id": draft_id})) for draft_id in draft_ids]
    source_text = " ".join(summary["source_text"] for summary in req_summaries)
    linked_tc_refs = meta.get("existing_tc_evidence_refs") or []
    linked_tc = [_tc_ref_summary(ref, tc_blocks) for ref in linked_tc_refs]
    top_matches = _top_tc_matches(source_text, tc_blocks, limit=8)
    recommendation = RECOMMENDATION_OVERRIDES.get(row["row_id"]) or _fallback_recommendation(cluster, top_matches)

    row_kind = cluster.get("cluster_type") or "unknown"
    checks = _checks_to_make(row_kind, recommendation["option"], req_summaries, linked_tc, top_matches)
    return {
        "row_id": row["row_id"],
        "cluster_id": row["cluster_id"],
        "cluster_type": row_kind,
        "priority": row.get("priority", ""),
        "affected_drafts": draft_ids,
        "affected_requirements": req_ids,
        "decision_required_ru": row.get("decision_required", ""),
        "allowed_option_ids": _split_cell(row.get("allowed_option_ids", "")),
        "recommended_option_id": recommendation["option"],
        "recommended_option_label_ru": _label_for_option(row, recommendation["option"]),
        "agent_confidence": recommendation["confidence"],
        "agent_rationale_ru": recommendation["rationale"],
        "no_new_tc_rationale_ru": recommendation.get("no_new", ""),
        "source_evidence_ru": _join_source_evidence(req_summaries),
        "existing_tc_review_notes_ru": _join_tc_evidence(linked_tc, top_matches),
        "what_to_check_before_confirming_ru": checks,
        "requirements_to_check": req_summaries,
        "drafts_to_check": draft_summaries,
        "linked_existing_test_cases": linked_tc,
        "top_existing_tc_matches": top_matches,
        "manual_confirmation_required": True,
    }


def _requirement_summary(item: dict[str, Any]) -> dict[str, Any]:
    table = (item.get("table_source_contexts") or [{}])[0]
    row_text = table.get("row_text") or ""
    header_cells = table.get("header_cells") or []
    row_cells = table.get("row_cells") or []
    source_text = item.get("source_text") or item.get("normalized_text") or row_text
    field_name = ""
    if row_cells:
        field_name = str(row_cells[0])
    return {
        "req_uid": item.get("req_uid"),
        "source_req_id": item.get("source_req_id"),
        "change_type": item.get("change_type"),
        "requirement_type": item.get("requirement_type"),
        "field_or_object": field_name or item.get("object") or "",
        "source_text": _collapse(source_text),
        "table_headers": header_cells,
        "table_row": _collapse(row_text),
        "source_anchor": (item.get("source_anchors") or [{}])[0],
        "source_doc": ((item.get("source_anchors") or [{}])[0]).get("source_doc"),
    }


def _draft_summary(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "draft_id": item.get("draft_id"),
        "proposed_tc_id": item.get("proposed_tc_id"),
        "target_file_path": item.get("target_file_path"),
        "title": item.get("title"),
        "coverage_intent": item.get("coverage_intent"),
        "duplicate_risk_level": item.get("duplicate_risk_level"),
        "draft_confidence": item.get("draft_confidence"),
        "is_executable_draft": item.get("is_executable_draft"),
    }


def _tc_ref_summary(ref: str, tc_blocks: list[dict[str, Any]]) -> dict[str, Any]:
    match = re.match(r"(TC-[A-Za-z0-9_-]+) \((.+)\)", ref)
    if not match:
        return {"ref": ref, "found": False, "reason": "unparseable_ref"}
    tc_id, file_path = match.groups()
    normalized_path = str(Path(file_path))
    candidates = [
        block
        for block in tc_blocks
        if block["tc_id"] == tc_id
        and (block["file_path"].endswith(normalized_path) or Path(block["file_path"]).name == Path(file_path).name)
    ]
    if not candidates:
        return {"ref": ref, "tc_id": tc_id, "file_path": file_path, "found": False, "reason": "tc_block_not_found"}
    block = candidates[0]
    return _public_tc_block(block, score=None)


def _top_tc_matches(source_text: str, tc_blocks: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    source_tokens = set(_tokens(source_text))
    if not source_tokens:
        return []
    scored = []
    for block in tc_blocks:
        common = source_tokens & set(block["tokens"])
        if not common:
            continue
        score = len(common) / math.sqrt(len(source_tokens) * max(1, len(set(block["tokens"]))))
        if score >= 0.08:
            public = _public_tc_block(block, score=round(score, 3))
            public["overlap_keywords"] = sorted(common)[:20]
            scored.append(public)
    scored.sort(key=lambda item: item["score"] or 0, reverse=True)
    return scored[:limit]


def _public_tc_block(block: dict[str, Any], score: float | None) -> dict[str, Any]:
    return {
        "tc_id": block["tc_id"],
        "file_path": block["file_path"],
        "line": block["start_line"],
        "found": True,
        "score": score,
        "title": block["title"],
        "traceability": block["traceability"],
        "test_data_excerpt": _short(block["test_data"], 240),
        "steps_excerpt": _short(block["steps"], 280),
        "expected_excerpt": _short(block["expected"], 280),
    }


def _fallback_recommendation(cluster: dict[str, Any], top_matches: list[dict[str, Any]]) -> dict[str, str]:
    cluster_type = cluster.get("cluster_type")
    if cluster_type == "duplicate_risk":
        if top_matches and (top_matches[0].get("score") or 0) >= 0.30:
            return {
                "option": "OPT-NO-NEW",
                "confidence": "medium",
                "rationale": "По автоматическому поиску есть сильное совпадение с existing TC; безопаснее сначала закрыть как existing coverage, если reviewer подтверждает.",
            }
        return {
            "option": "OPT-SEPARATE",
            "confidence": "low",
            "rationale": "Сильного existing TC покрытия не найдено; возможно нужен отдельный TC, но требуется reviewer check.",
        }
    if cluster_type == "source_grounding":
        return {
            "option": "OPT-CLARIFY",
            "confidence": "medium",
            "rationale": "Нужно уточнить source-backed action/object/condition/oracle перед revised draft.",
        }
    if cluster_type == "replacement_strategy":
        return {
            "option": "OPT-SPLIT",
            "confidence": "medium",
            "rationale": "Rejected draft лучше не чинить на месте; нужно split/replace после source grounding.",
        }
    return {
        "option": "OPT-DEFER",
        "confidence": "medium",
        "rationale": "Агрегирующая manual-only строка; без подтверждения предыдущих решений продвигать ее небезопасно.",
    }


def _checks_to_make(
    row_kind: str,
    option: str,
    req_summaries: list[dict[str, Any]],
    linked_tc: list[dict[str, Any]],
    top_matches: list[dict[str, Any]],
) -> str:
    req_names = "; ".join(
        f"{item.get('req_uid')}: {item.get('field_or_object') or _short(item.get('source_text', ''), 80)}"
        for item in req_summaries[:5]
    )
    found_linked = [item for item in linked_tc if item.get("found")]
    top = found_linked[:3] or top_matches[:3]
    tc_names = "; ".join(
        f"{item.get('tc_id')} ({Path(item.get('file_path', '')).name}:{item.get('line')}) - {item.get('title')}"
        for item in top
    )
    if option == "OPT-NO-NEW":
        return f"Проверьте, что listed/top TC действительно покрывают источник: {req_names}. Основные TC для проверки: {tc_names}."
    if option == "OPT-EXTEND":
        return f"Проверьте, какую недостающую часть надо добавить к existing TC, не создавая дубликат. Источник: {req_names}. TC: {tc_names}."
    if option in {"OPT-SEPARATE", "OPT-REPLACE"}:
        return f"Проверьте, что existing TC не покрывают behavior полностью, и что источник достаточен для отдельного/replacement draft. Источник: {req_names}. Ближайшие TC: {tc_names or 'нет сильных совпадений'}."
    if option == "OPT-SPLIT":
        return f"Разделите решение по независимым требованиям/объектам. В этой строке затронуто: {req_names}."
    if option == "OPT-REVISE":
        return f"Используйте source facts для revised draft без выдумывания UI behavior. Источник: {req_names}. Сверьте ближайшие TC: {tc_names or 'нет linked TC'}."
    return f"Не продвигайте в Stage 9E до ручного решения. Источник: {req_names}. Проверяемые TC: {tc_names or 'нет linked TC'}."


def _filled_answer_row(row: dict[str, str], analysis: dict[str, Any], now: str) -> dict[str, str]:
    result = dict(row)
    result["selected_option_id"] = analysis["recommended_option_id"]
    result["reviewer_rationale"] = f"[ПРЕДЗАПОЛНЕНО АГЕНТОМ, НУЖНО ПОДТВЕРДИТЬ] {analysis['agent_rationale_ru']}"
    result["source_evidence"] = analysis["source_evidence_ru"]
    result["existing_tc_review_notes"] = analysis["existing_tc_review_notes_ru"]
    result["no_new_tc_rationale"] = analysis["no_new_tc_rationale_ru"] if analysis["recommended_option_id"] == "OPT-NO-NEW" else ""
    result["defer_reason"] = "Отложено по рекомендации агента до ручного подтверждения source/coverage." if analysis["recommended_option_id"] == "OPT-DEFER" else ""
    result["split_guidance"] = analysis["agent_rationale_ru"] if analysis["recommended_option_id"] == "OPT-SPLIT" else ""
    result["business_clarification"] = (
        analysis["what_to_check_before_confirming_ru"]
        if analysis["recommended_option_id"] in {"OPT-CLARIFY", "OPT-MANUAL"}
        else ""
    )
    result["answered_by"] = "agent-proposed-not-reviewer-approved"
    result["answered_at_utc"] = now
    result["agent_confidence"] = analysis["agent_confidence"]
    result["agent_what_to_check_before_confirming"] = analysis["what_to_check_before_confirming_ru"]
    result["agent_recommended_option_label"] = analysis["recommended_option_label_ru"]
    return result


def _label_for_option(row: dict[str, str], option_id: str) -> str:
    ids = _split_cell(row.get("allowed_option_ids", ""))
    labels = _split_cell(row.get("allowed_option_labels", ""))
    mapping = dict(zip(ids, labels))
    return mapping.get(option_id, option_id)


def _join_source_evidence(req_summaries: list[dict[str, Any]]) -> str:
    parts = []
    for item in req_summaries[:8]:
        text = item["table_row"] or item["source_text"]
        source_doc = item.get("source_doc") or "source registry/context bundle"
        parts.append(f"{item['req_uid']}: {source_doc}; {text}")
    return " || ".join(_short(part, 900) for part in parts)


def _join_tc_evidence(linked_tc: list[dict[str, Any]], top_matches: list[dict[str, Any]]) -> str:
    parts = []
    for item in linked_tc[:8]:
        if item.get("found"):
            parts.append(
                f"{item['tc_id']} {item['file_path']}:{item['line']} title={item.get('title')}; traceability={item.get('traceability')}; expected={item.get('expected_excerpt')}"
            )
        else:
            parts.append(f"{item.get('tc_id') or item.get('ref')}: не найдено ({item.get('reason')})")
    if not parts and top_matches:
        for item in top_matches[:5]:
            parts.append(
                f"top-match {item['tc_id']} {item['file_path']}:{item['line']} score={item.get('score')} title={item.get('title')}"
            )
    return " || ".join(_short(part, 700) for part in parts)


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Manual Decision Review Assist WPKG-000001",
        "",
        "Это не утвержденные reviewer answers. Это вариант агента для подтверждения: я сопоставил строки decision matrix с source facts и существующими TC-блоками.",
        "",
        "## Summary",
        "",
        f"- Status: `{report['report_status']}`",
        f"- Rows: `{report['rows_total']}`",
        f"- Recommendation counts: `{json.dumps(report['recommendation_counts'], ensure_ascii=False)}`",
        f"- TC blocks indexed: `{report['tc_blocks_indexed']}`",
        "- Canonical test-cases were not edited.",
        "",
        "## Что проверять",
        "",
        "В каждой строке ниже есть: предложенный option, требования, существующие TC для проверки и причина. Если согласны, используйте CSV `agent-filled-for-confirmation` как черновик reviewer answer pack.",
        "",
    ]
    for item in report["row_analyses"]:
        lines.extend(
            [
                f"### {item['row_id']} / {item['cluster_id']}",
                "",
                f"- Recommendation: `{item['recommended_option_id']}` - {item['recommended_option_label_ru']} (`{item['agent_confidence']}`)",
                f"- Why: {item['agent_rationale_ru']}",
                f"- Check before confirming: {item['what_to_check_before_confirming_ru']}",
                "- Requirements:",
            ]
        )
        for req in item["requirements_to_check"][:8]:
            source = req["table_row"] or req["source_text"]
            lines.append(f"  - `{req['req_uid']}`: {_short(source, 360)}")
        lines.append("- Existing TC evidence:")
        evidence_items = [tc for tc in item["linked_existing_test_cases"] if tc.get("found")]
        missing_items = [tc for tc in item["linked_existing_test_cases"] if not tc.get("found")]
        top_items = item["top_existing_tc_matches"][:5]
        if evidence_items:
            for tc in evidence_items[:8]:
                lines.append(
                    f"  - `{tc['tc_id']}` [{Path(tc['file_path']).name}:{tc['line']}] title={tc.get('title')}; expected={_short(tc.get('expected_excerpt', ''), 220)}"
                )
        elif top_items:
            for tc in top_items:
                lines.append(
                    f"  - top `{tc['tc_id']}` [{Path(tc['file_path']).name}:{tc['line']}] score={tc.get('score')} title={tc.get('title')}"
                )
        else:
            lines.append("  - Нет найденных linked/top TC.")
        if missing_items:
            lines.append("- Missing/noisy linked TC refs:")
            for tc in missing_items[:8]:
                lines.append(f"  - `{tc.get('tc_id') or tc.get('ref')}`: {tc.get('reason')}")
        lines.append("")
    return "\n".join(lines) + "\n"


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _tokens(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-zА-Яа-яЁё0-9]+", text.casefold())
    return [token for token in tokens if len(token) > 2 and token not in STOPWORDS]


def _split_cell(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[;,]", value or "") if part.strip()]


def _collapse(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _short(value: str, limit: int) -> str:
    value = _collapse(value)
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


if __name__ == "__main__":
    raise SystemExit(main())
