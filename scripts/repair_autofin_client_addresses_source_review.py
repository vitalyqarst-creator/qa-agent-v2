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

from test_case_agent.semantic_design_bridge import (  # noqa: E402
    canonical_payload_sha256,
    load_approved_clarifications,
    validate_semantic_design_binding,
)


EXPECTED_INCORRECT_ASSERTIONS = {
    "ASSERT-018",
    "ASSERT-020",
    "ASSERT-040",
    "ASSERT-078",
    "ASSERT-088",
}


def _load(path: Path, *, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object: {path}")
    return payload


def _resolve(root: Path, value: Path) -> Path:
    return (value if value.is_absolute() else root / value).resolve()


def _replace(record: dict[str, Any], expected: Mapping[str, Any], updates: Mapping[str, Any]) -> None:
    for key, value in expected.items():
        if record.get(key) != value:
            raise ValueError(
                f"repair precondition failed for {record.get('assertion_id') or record.get('obligation_id')}.{key}"
            )
    record.update(deepcopy(dict(updates)))


def _assertion_registry(design: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for source_design in design.get("source_designs", []):
        if not isinstance(source_design, Mapping):
            continue
        for assertion in source_design.get("assertions", []):
            if isinstance(assertion, dict) and isinstance(assertion.get("assertion_id"), str):
                registry[assertion["assertion_id"]] = assertion
    return registry


def _obligation_registry(design: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["obligation_id"]: item
        for item in design.get("obligations", [])
        if isinstance(item, dict) and isinstance(item.get("obligation_id"), str)
    }


def apply_repair(design: Mapping[str, Any]) -> dict[str, Any]:
    repaired = deepcopy(dict(design))
    assertions = _assertion_registry(repaired)
    obligations = _obligation_registry(repaired)
    if not EXPECTED_INCORRECT_ASSERTIONS <= set(assertions):
        raise ValueError("semantic design misses one or more reviewed assertions")

    _replace(
        assertions["ASSERT-018"],
        {"oracle_clauses": ["На экране отображается заголовок «Блок «Адреса клиента»»."]},
        {"oracle_clauses": ["На экране отображается заголовок «Адреса клиента»."]},
    )
    _replace(
        assertions["ASSERT-020"],
        {
            "oracle_clauses": [
                "Выбранный адрес DaData отображается и сохраняется в поле «Адрес регистрации»."
            ]
        },
        {
            "oracle_clauses": [
                "DaData отображает предложения; после выбора поле «Адрес регистрации» отображает выбранное предложение."
            ]
        },
    )
    _replace(
        obligations["OBL-003"],
        {
            "required_behavior": "Выбрать и сохранить предложенный адрес через UI.",
            "single_expected_behavior": "Выбранный адрес удерживается полем.",
        },
        {
            "required_behavior": "Отобразить предложения DaData и выбранное предложение в поле.",
            "single_expected_behavior": "Поле отображает выбранное предложение DaData.",
        },
    )
    _replace(
        assertions["ASSERT-040"],
        {
            "action_clauses": [
                "Выбрать в поле «Регион» предложенное значение «Красноярский край»."
            ],
            "oracle_clauses": [
                "Поле «Регион» отображает выбранное значение «Красноярский край»."
            ],
        },
        {
            "action_clauses": [
                "Выбрать в поле «Регион» значение из актуального списка предложений."
            ],
            "oracle_clauses": [
                "Поле «Регион» отображает выбранное значение из актуального списка предложений."
            ],
            "disposition_rationale": (
                "Типизированное Р=Да покрывается самостоятельным выбором и "
                "отображением актуального предложенного значения."
            ),
        },
    )
    _replace(
        obligations["OBL-023"],
        {
            "required_behavior": "Выбрать и сохранить предложенный регион.",
            "planned_check": "Выбрать Красноярский край.",
            "test_data": "Красноярский край",
        },
        {
            "required_behavior": "Выбрать предложенный регион и отобразить его в поле.",
            "planned_check": "Выбрать значение из актуального списка предложений.",
            "test_data": "Значение региона из актуального списка предложений",
        },
    )
    _replace(
        assertions["ASSERT-078"],
        {
            "oracle_clauses": [
                "Выбранный адрес DaData сохраняется в поле «Адрес фактического места жительства»."
            ]
        },
        {
            "oracle_clauses": [
                "DaData отображает предложения; после выбора поле фактического адреса отображает выбранное предложение."
            ]
        },
    )
    _replace(
        obligations["OBL-061"],
        {
            "required_behavior": "Выбрать и сохранить предложение DaData через UI поля.",
            "planned_check": "Ввести адрес, выбрать предложение и проверить retained value.",
            "single_expected_behavior": "Выбранный адрес сохранён.",
        },
        {
            "required_behavior": "Отобразить предложения DaData и выбранное предложение в поле.",
            "planned_check": "Ввести адрес, выбрать предложение и проверить отображённое значение.",
            "single_expected_behavior": "Поле отображает выбранное предложение DaData.",
        },
    )
    _replace(
        assertions["ASSERT-088"],
        {
            "condition_clauses": [
                "Признак совпадения адресов имеет значение «Да», а в фактическом адресе квартира не указана."
            ],
            "action_clauses": [
                "Установить совпадение адресов и сохранить фактический адрес без квартиры."
            ],
        },
        {
            "condition_clauses": [
                "При значении признака совпадения «Нет» фактический адрес заполнен без квартиры."
            ],
            "action_clauses": [
                "Изменить признак совпадения адресов с «Нет» на «Да»."
            ],
        },
    )
    _replace(
        obligations["OBL-071"],
        {"planned_check": "Совпадение адресов плюс отсутствие квартиры."},
        {
            "planned_check": (
                "Заполнить фактический адрес без квартиры при совпадении=Нет, "
                "затем изменить совпадение на Да."
            )
        },
    )
    return repaired


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Apply the bounded reviewed AutoFin address semantic repair.")
    result.add_argument("--repo-root", type=Path, default=ROOT_DIR)
    result.add_argument("--context", type=Path, required=True)
    result.add_argument("--scope-boundary-decision", type=Path, required=True)
    result.add_argument("--semantic-design", type=Path, required=True)
    result.add_argument("--source-review", type=Path, required=True)
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
            "review": args.source_review,
            "output": args.output,
            "receipt": args.receipt_output,
        }.items()
    }
    if paths["output"].exists() or paths["receipt"].exists():
        raise FileExistsError("repair outputs must be fresh")
    input_bytes = paths["design"].read_bytes()
    input_sha256 = hashlib.sha256(input_bytes).hexdigest()
    if input_sha256 != args.expected_input_sha256:
        raise ValueError("semantic design SHA-256 does not match the reviewed input")
    review = _load(paths["review"], label="source review")
    incorrect = {
        item.get("assertion_id")
        for item in review.get("assertion_reviews", [])
        if isinstance(item, Mapping) and item.get("verdict") != "verified"
    }
    if review.get("decision") != "changes-required" or incorrect != EXPECTED_INCORRECT_ASSERTIONS:
        raise ValueError("source review does not match the bounded five-assertion repair")
    context = _load(paths["context"], label="context")
    boundary = _load(paths["boundary"], label="scope boundary")
    repaired = apply_repair(_load(paths["design"], label="semantic design"))
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
        "repaired_assertion_ids": sorted(EXPECTED_INCORRECT_ASSERTIONS),
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
