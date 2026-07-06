from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def main() -> int:
    parser = argparse.ArgumentParser(description="Build reviewer-facing agent suggestions for manual decision answers.")
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--test-cases-dir", required=True, type=Path)
    parser.add_argument("--package-id", default="WPKG-000001")
    args = parser.parse_args()

    work_dir = args.work_dir
    package_id = args.package_id
    base_csv = work_dir / f"manual-decision-reviewer-answer-pack-{package_id}.ru.utf8-bom.csv"
    matrix_path = work_dir / f"manual-decision-matrix-{package_id}.json"
    bundle_path = work_dir / f"create-new-tc-context-bundle-{package_id}.json"
    out_csv = work_dir / f"manual-decision-reviewer-answer-pack-{package_id}.agent-suggestions.ru.utf8-bom.csv"
    out_md = work_dir / f"manual-decision-reviewer-answer-pack-{package_id}.agent-suggestions.ru.md"

    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    reqs = {item.get("req_uid"): item for item in bundle.get("candidate_requirements", [])}
    rows = list(csv.DictReader(base_csv.open("r", encoding="utf-8-sig", newline="")))
    row_meta = {row["row_id"]: row for row in matrix["reviewer_decision_rows"]}
    cluster_meta = {cluster["cluster_id"]: cluster for cluster in matrix["decision_clusters"]}
    label_by_id = _option_labels(rows)

    extra_cols = [
        "agent_suggested_option_id",
        "agent_suggested_option_label",
        "agent_confidence",
        "agent_rationale_ru",
        "where_to_check_source",
        "where_to_check_existing_tc",
        "what_to_verify_before_confirming",
        "how_to_confirm",
        "agent_warning",
    ]
    fieldnames = list(rows[0].keys()) + extra_cols
    for row in rows:
        meta = row_meta[row["row_id"]]
        suggestion = _suggestion(row, meta, cluster_meta)
        req_refs = meta.get("affected_requirements") or []
        tc_refs = meta.get("existing_tc_evidence_refs") or []
        row["agent_suggested_option_id"] = suggestion["option"]
        row["agent_suggested_option_label"] = label_by_id.get(suggestion["option"], suggestion["option"])
        row["agent_confidence"] = suggestion["confidence"]
        row["agent_rationale_ru"] = suggestion["why"]
        row["where_to_check_source"] = " || ".join(_req_summary(reqs, req_uid) for req_uid in req_refs[:5])
        row["where_to_check_existing_tc"] = (
            " || ".join(_tc_summary(args.test_cases_dir, ref) for ref in tc_refs[:5])
            if tc_refs
            else "Нет linked existing TC в этой строке; проверяйте source artifacts по affected_requirements."
        )
        row["what_to_verify_before_confirming"] = suggestion["verify"]
        row["how_to_confirm"] = (
            "Если согласны, скопируйте agent_suggested_option_id в selected_option_id и заполните "
            "reviewer_rationale/source_evidence/etc. Если не согласны, выберите другой ID из allowed_option_ids."
        )
        row["agent_warning"] = (
            "Это рекомендация агента, не reviewer answer. Existing TC используется только как coverage evidence, "
            "не как источник бизнес-правил."
        )

    with out_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    out_md.write_text(_render_markdown(rows, out_csv), encoding="utf-8", newline="\n")
    print(json.dumps({"csv_path": str(out_csv), "markdown_path": str(out_md), "rows": len(rows)}, ensure_ascii=False, indent=2))
    return 0


def _option_labels(rows: list[dict[str, str]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in rows:
        ids = [value.strip() for value in row["allowed_option_ids"].split(";") if value.strip()]
        labels = [value.strip() for value in row["allowed_option_labels"].split(";") if value.strip()]
        result.update(dict(zip(ids, labels)))
    return result


def _suggestion(row: dict[str, str], meta: dict[str, Any], cluster_meta: dict[str, dict[str, Any]]) -> dict[str, str]:
    cluster_type = (cluster_meta.get(row["cluster_id"]) or {}).get("cluster_type", "")
    evidence = f"{row.get('evidence_summary', '')} {meta.get('evidence_summary', '')}"
    unreadable = "�" in evidence or "����" in evidence
    if cluster_type == "duplicate_risk":
        return {
            "option": "OPT-DEFER",
            "confidence": "medium",
            "why": (
                "Есть duplicate risk и ссылки на похожие existing TC. Агент не должен решать за reviewer, "
                "покрыт ли candidate уже существующим TC. Без ручного сравнения безопаснее отложить решение."
            ),
            "verify": (
                "Откройте listed existing TC и сравните с affected_requirements. Если поведение уже покрыто -> "
                "OPT-NO-NEW; если нужен апдейт existing TC -> OPT-EXTEND; если candidate явно отдельный -> OPT-SEPARATE."
            ),
        }
    if cluster_type == "source_grounding":
        return {
            "option": "OPT-CLARIFY",
            "confidence": "high" if unreadable else "medium",
            "why": (
                "Строка заблокирована source-grounding вопросом: не хватает безопасно подтвержденного "
                "action/oracle/object/condition. Часть source evidence в artifact нечитаема или неоднозначна."
                if unreadable
                else "Строка требует подтвержденный source-backed факт перед revised draft."
            ),
            "verify": (
                "Проверьте ФТ/source по affected_requirements и укажите конкретный факт: действие пользователя, "
                "объект/экран/поле, условие и наблюдаемый expected result. Если факт найден -> можно заменить "
                "на OPT-REVISE или OPT-SPLIT."
            ),
        }
    if cluster_type == "replacement_strategy":
        return {
            "option": "OPT-DEFER",
            "confidence": "medium",
            "why": (
                "Draft помечен как rejected/weak. Пока source/duplicate evidence недостаточно, чтобы агент "
                "безопасно выбрал rewrite/split вместо reviewer."
            ),
            "verify": (
                "Если источник достаточен для полного переписывания без догадок -> OPT-REPLACE. Если в одном "
                "candidate несколько проверок -> OPT-SPLIT. Если это фактически existing coverage -> OPT-EXTEND "
                "или OPT-DEFER."
            ),
        }
    return {
        "option": "OPT-DEFER",
        "confidence": "high",
        "why": "Группа уже агрегирует unresolved/manual-only decisions. Без явных reviewer answers продвижение к Stage 9E небезопасно.",
        "verify": "Подтвердите, нужно ли закрыть как no-new-TC, запросить clarification, оставить manual-only или отложить.",
    }


def _req_summary(reqs: dict[str, dict[str, Any]], req_uid: str) -> str:
    item = reqs.get(req_uid) or {}
    parts = [req_uid]
    for label, key in [
        ("source_req_id", "source_req_id"),
        ("object", "object"),
        ("condition", "condition"),
        ("expected", "expected_behavior"),
        ("source_text", "source_text"),
    ]:
        value = item.get(key)
        if value:
            parts.append(f"{label}: {str(value).replace(chr(10), ' ').strip()[:260]}")
    if len(parts) == 1:
        parts.append("подробности см. create-new-tc-context-bundle по req_uid")
    return " | ".join(parts)


def _tc_summary(test_cases_dir: Path, ref: str) -> str:
    match = re.match(r"([^\s(]+) \((.+)\)", ref)
    if not match:
        return ref
    tc_id, raw_path = match.group(1), match.group(2)
    path = Path(raw_path)
    if not path.exists():
        path = test_cases_dir / Path(raw_path).name
    if not path.exists():
        return f"{tc_id} -> {raw_path} (файл не найден)"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:  # noqa: BLE001 - reviewer context should keep going.
        return f"{tc_id} -> {raw_path} (не прочитан: {exc})"
    starts = [
        index
        for index, line in enumerate(lines)
        if re.match(r"^#{2,6}\s+" + re.escape(tc_id) + r"\b", line.strip())
    ]
    if not starts:
        return f"{tc_id} -> {raw_path} (TC block не найден)"
    start = starts[0]
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if re.match(r"^#{2,6}\s+TC-[A-Za-z0-9_-]+\b", lines[index].strip()):
            end = index
            break
    block = lines[start:end]
    title = ""
    trace = ""
    for line in block[:50]:
        lowered = line.casefold()
        if ("title" in lowered or "название" in lowered) and ":" in line and not title:
            title = line.strip()
        if ("traceability" in lowered or "трасс" in lowered) and ":" in line and not trace:
            trace = line.strip()
    parts = [tc_id, str(path)]
    if title:
        parts.append(title[:180])
    if trace:
        parts.append(trace[:220])
    return " | ".join(parts)


def _render_markdown(rows: list[dict[str, str]], csv_path: Path) -> str:
    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    lines = [
        "# Agent Suggested Reviewer Decisions WPKG-000001",
        "",
        "Это не утвержденные reviewer answers и не Stage 9E. Файл помогает понять, где смотреть требования и existing TC перед подтверждением.",
        "",
        f"- Created: {created}",
        f"- CSV: `{csv_path}`",
        f"- Rows: `{len(rows)}`",
        "- Настоящие поля `selected_option_id` оставлены пустыми.",
        "- Чтобы подтвердить строку: скопируйте `agent_suggested_option_id` в `selected_option_id` и заполните rationale/evidence поля.",
        "",
        "## Как читать рекомендации",
        "",
        "- `agent_suggested_option_id`: безопасный вариант, который предлагает агент.",
        "- `where_to_check_source`: req_uid/source facts из context bundle.",
        "- `where_to_check_existing_tc`: linked TC и краткий traceability/title, если есть.",
        "- `what_to_verify_before_confirming`: что проверить перед подтверждением.",
        "",
        "## Rows",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"### {row['row_id']} {row['cluster_id']}",
                "",
                f"- Suggested: `{row['agent_suggested_option_id']}` - {row['agent_suggested_option_label']} (`{row['agent_confidence']}` confidence)",
                f"- Drafts: `{row['affected_drafts'] or 'none'}`",
                f"- Requirements: `{row['affected_requirements'] or 'none'}`",
                f"- Why: {row['agent_rationale_ru']}",
                f"- Check source: {row['where_to_check_source']}",
                f"- Check existing TC: {row['where_to_check_existing_tc']}",
                f"- Verify before confirming: {row['what_to_verify_before_confirming']}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
