from __future__ import annotations

import argparse
import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.repair_autofin_client_addresses_exact_length_boundaries import (  # noqa: E402
    apply_repair as apply_exact_length_repair,
)
from test_case_agent.semantic_design_bridge import (  # noqa: E402
    canonical_payload_sha256,
    load_approved_clarifications,
    validate_semantic_design_binding,
)


FACTUAL_ASSERTION_IDS = ("ASSERT-102", "ASSERT-103", "ASSERT-104", "ASSERT-105")
FACTUAL_OBLIGATION_IDS = ("OBL-085", "OBL-086", "OBL-087", "OBL-088")


def _load(path: Path, *, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object: {path}")
    return payload


def _resolve(root: Path, value: Path) -> Path:
    return (value if value.is_absolute() else root / value).resolve()


def _assertions(design: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(assertion["assertion_id"]): assertion
        for source_design in design.get("source_designs", [])
        if isinstance(source_design, dict)
        for assertion in source_design.get("assertions", [])
        if isinstance(assertion, dict)
        and isinstance(assertion.get("assertion_id"), str)
    }


def _obligations(design: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item["obligation_id"]): item
        for item in design.get("obligations", [])
        if isinstance(item, dict) and isinstance(item.get("obligation_id"), str)
    }


def _prefix_factual(value: str) -> str:
    if not value:
        return value
    return "В блоке фактического адреса " + value[0].lower() + value[1:]


def apply_review_finding_repairs(design_value: Mapping[str, Any]) -> dict[str, Any]:
    """Bind ambiguous generated flows to distinct source-backed address branches."""

    repaired = apply_exact_length_repair(deepcopy(dict(design_value)))
    assertions = _assertions(repaired)
    obligations = _obligations(repaired)
    missing = [
        item
        for item in (*FACTUAL_ASSERTION_IDS, *FACTUAL_OBLIGATION_IDS, "ASSERT-128", "OBL-111")
        if item not in assertions and item not in obligations
    ]
    if missing:
        raise ValueError("semantic design misses branch bindings: " + ", ".join(missing))

    for assertion_id in FACTUAL_ASSERTION_IDS:
        assertion = assertions[assertion_id]
        assertion["canonical_statement"] = _prefix_factual(
            str(assertion["canonical_statement"])
        )
        for key in ("condition_clauses", "action_clauses", "oracle_clauses"):
            assertion[key] = [_prefix_factual(str(value)) for value in assertion[key]]
        assertion["field_or_block"] = (
            "Фактический адрес / " + str(assertion["field_or_block"])
        )
        assertion["disposition_rationale"] = (
            str(assertion["disposition_rationale"]).rstrip(". ")
            + ". Ветка фактического адреса закреплена явно, чтобы не смешивать её "
            "с одноимёнными полями адреса регистрации."
        )

    for obligation_id in FACTUAL_OBLIGATION_IDS:
        obligation = obligations[obligation_id]
        for key in (
            "required_behavior",
            "planned_check",
            "single_expected_behavior",
        ):
            obligation[key] = _prefix_factual(str(obligation[key]))
        obligation["review_notes"] = (
            str(obligation["review_notes"]).rstrip(". ")
            + ". Ветка фактического адреса обязательна."
        )

    assertion = assertions["ASSERT-128"]
    assertion.update(
        {
            "canonical_statement": (
                "Адрес фактического места жительства, выбранный посредством "
                "запроса DaData, раскладывается по видимым полям блока ручного ввода."
            ),
            "condition_clauses": [
                "Адрес фактического места жительства заполняется посредством запроса DaData."
            ],
            "action_clauses": [
                "В поле адреса фактического места жительства выбрать предложенный DaData адрес клиента."
            ],
            "oracle_clauses": [
                "Компоненты выбранного фактического адреса отображаются в соответствующих полях блока ручного ввода."
            ],
            "field_or_block": (
                "Фактический адрес / раскладывание DaData-адреса по полям ручного ввода"
            ),
            "disposition_rationale": (
                "Исполняемая цепочка закреплена за веткой фактического адреса и "
                "ограничена наблюдаемым UI-эффектом; внутреннее заполнение kladr "
                "исключено отдельной N/A-цепочкой."
            ),
        }
    )
    obligation = obligations["OBL-111"]
    obligation.update(
        {
            "required_behavior": (
                "Выбранный через DaData фактический адрес раскладывается по видимым "
                "ручным полям фактического адреса."
            ),
            "planned_check": (
                "В ветке фактического адреса выбрать DaData-адрес в UI и сравнить "
                "компоненты с ручными полями этой ветки."
            ),
            "single_expected_behavior": (
                "Компоненты фактического адреса отображаются в ручных полях "
                "фактического адреса."
            ),
            "review_notes": (
                "Ветка фактического адреса отличает кейс от DaData-сценария адреса "
                "регистрации; внутреннее поле kladr не проверяется."
            ),
        }
    )
    return repaired


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Repair deterministic source-model causes of the v17 findings."
    )
    result.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    result.add_argument("--context", type=Path, required=True)
    result.add_argument("--scope-boundary-decision", type=Path, required=True)
    result.add_argument("--semantic-design", type=Path, required=True)
    result.add_argument("--expected-input-sha256", required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--receipt-output", type=Path, required=True)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.repo_root.resolve()
    paths = {
        name: _resolve(root, value)
        for name, value in {
            "context": args.context,
            "boundary": args.scope_boundary_decision,
            "design": args.semantic_design,
            "output": args.output,
            "receipt": args.receipt_output,
        }.items()
    }
    if paths["output"].exists() or paths["receipt"].exists():
        raise FileExistsError("repair outputs must be fresh")
    input_sha256 = hashlib.sha256(paths["design"].read_bytes()).hexdigest()
    if input_sha256 != args.expected_input_sha256:
        raise ValueError("semantic design SHA-256 does not match the reviewed input")
    context = _load(paths["context"], label="context")
    boundary = _load(paths["boundary"], label="scope boundary")
    repaired = apply_review_finding_repairs(
        _load(paths["design"], label="semantic design")
    )
    validation = validate_semantic_design_binding(
        context,
        boundary,
        repaired,
        clarifications=load_approved_clarifications(root, context),
        require_ready=True,
    )
    paths["output"].parent.mkdir(parents=True, exist_ok=True)
    with paths["output"].open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(repaired, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    receipt = {
        "version": 1,
        "status": "completed",
        "input_sha256": input_sha256,
        "output_sha256": hashlib.sha256(paths["output"].read_bytes()).hexdigest(),
        "output_payload_sha256": canonical_payload_sha256(repaired),
        "added_exact_length_obligation_ids": ["OBL-112", "OBL-113", "OBL-114"],
        "factual_branch_assertion_ids": [*FACTUAL_ASSERTION_IDS, "ASSERT-128"],
        "factual_branch_obligation_ids": [*FACTUAL_OBLIGATION_IDS, "OBL-111"],
        "strict_validation": validation,
    }
    paths["receipt"].parent.mkdir(parents=True, exist_ok=True)
    with paths["receipt"].open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
