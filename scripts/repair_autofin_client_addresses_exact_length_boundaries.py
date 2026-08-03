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


BOUNDARIES = (
    {
        "source_row_id": "SRC-021",
        "base_assertion_id": "ASSERT-034",
        "requirement_code": "BSR 124",
        "entries": (
            ("ASSERT-130", "ATOM-130", "OBL-112", "TC-112", "66001", "N-1"),
            ("ASSERT-131", "ATOM-131", "OBL-113", "TC-113", "6600170", "N+1"),
        ),
    },
    {
        "source_row_id": "SRC-043",
        "base_assertion_id": "ASSERT-126",
        "requirement_code": "BSR 161",
        "entries": (
            ("ASSERT-132", "ATOM-132", "OBL-114", "TC-114", "6600000", "N+1"),
        ),
    },
)


def _load(path: Path, *, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object: {path}")
    return payload


def _resolve(root: Path, value: Path) -> Path:
    return (value if value.is_absolute() else root / value).resolve()


def _source_designs(design: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item["source_row_id"]): item
        for item in design.get("source_designs", [])
        if isinstance(item, dict) and isinstance(item.get("source_row_id"), str)
    }


def _obligations(design: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item["obligation_id"]): item
        for item in design.get("obligations", [])
        if isinstance(item, dict) and isinstance(item.get("obligation_id"), str)
    }


def _new_assertion(
    base: Mapping[str, Any],
    *,
    assertion_id: str,
    atom_id: str,
    obligation_id: str,
    value: str,
    boundary_class: str,
    requirement_code: str,
) -> dict[str, Any]:
    assertion = deepcopy(dict(base))
    digit_count = len(value)
    assertion.update(
        {
            "assertion_id": assertion_id,
            "canonical_statement": (
                f"Значение класса {boundary_class} длиной {digit_count} цифр не "
                "соответствует правилу точной длины почтового индекса; точная "
                "UI-реакция требует калибровки."
            ),
            "polarity": "negative",
            "risk": "high",
            "action_clauses": [
                f"Попытаться ввести в поле «Почтовый индекс» значение «{value}»."
            ],
            "oracle_clauses": [
                f"Точная наблюдаемая UI-реакция на значение «{value}» класса "
                f"{boundary_class} требует candidate-ui-calibration; фильтрация, "
                "сообщение, очистка и блокировка перехода не утверждаются."
            ],
            "requirement_codes": [requirement_code],
            "atom_id": atom_id,
            "obligation_ids": [obligation_id],
            "disposition_rationale": (
                f"Отдельный {boundary_class} boundary обязателен для exact-length; "
                "источник задаёт запрещённый класс, но не конкретный UI-механизм."
            ),
        }
    )
    return assertion


def _new_obligation(
    base: Mapping[str, Any],
    *,
    obligation_id: str,
    atom_id: str,
    test_case_id: str,
    value: str,
    boundary_class: str,
    source_row_id: str,
    requirement_code: str,
) -> dict[str, Any]:
    obligation = deepcopy(dict(base))
    obligation.update(
        {
            "obligation_id": obligation_id,
            "linked_atom_id": atom_id,
            "property_type": "exact-length",
            "obligation_class": "candidate-ui-calibration",
            "required_behavior": (
                f"Проверить отдельный boundary {boundary_class} для шестизначного "
                "почтового индекса без выдумывания UI-реакции."
            ),
            "source_ref": f"{source_row_id} {requirement_code}",
            "planned_tc_id": test_case_id,
            "review_notes": "candidate-ui-calibration",
            "design_dimension": "boundary",
            "planned_check": (
                f"Ввести {value} ({boundary_class}) и зафиксировать фактическую "
                "наблюдаемую UI-реакцию."
            ),
            "check_type": "boundary",
            "coverage_class": (
                "shorter-rejected" if boundary_class == "N-1" else "longer-rejected"
            ),
            "input_class": f"{boundary_class}:{value}",
            "single_expected_behavior": (
                f"Точная реакция на {value} ({boundary_class}) устанавливается "
                "наблюдением UI без предписания механизма."
            ),
            "oracle_source": "not_found",
            "test_data": value,
            "scope_obligation_ids": [],
        }
    )
    return obligation


def apply_repair(design_value: Mapping[str, Any]) -> dict[str, Any]:
    repaired = deepcopy(dict(design_value))
    source_designs = _source_designs(repaired)
    obligations_by_id = _obligations(repaired)
    existing_assertion_ids = {
        str(assertion.get("assertion_id", ""))
        for item in source_designs.values()
        for assertion in item.get("assertions", [])
        if isinstance(assertion, Mapping)
    }
    reserved_assertion_ids = {
        entry[0] for boundary in BOUNDARIES for entry in boundary["entries"]
    }
    reserved_obligation_ids = {
        entry[2] for boundary in BOUNDARIES for entry in boundary["entries"]
    }
    if existing_assertion_ids & reserved_assertion_ids:
        raise ValueError("exact-length repair assertion IDs already exist")
    if set(obligations_by_id) & reserved_obligation_ids:
        raise ValueError("exact-length repair obligation IDs already exist")
    new_obligations: list[dict[str, Any]] = []
    new_atoms: list[str] = []
    new_test_cases: list[str] = []
    for boundary in BOUNDARIES:
        source_row_id = str(boundary["source_row_id"])
        source_design = source_designs.get(source_row_id)
        if source_design is None:
            raise ValueError(f"semantic design misses {source_row_id}")
        assertions = source_design.get("assertions")
        if not isinstance(assertions, list):
            raise ValueError(f"{source_row_id} assertions must be an array")
        base = next(
            (
                item
                for item in assertions
                if isinstance(item, Mapping)
                and item.get("assertion_id") == boundary["base_assertion_id"]
            ),
            None,
        )
        if base is None:
            raise ValueError(f"semantic design misses {boundary['base_assertion_id']}")
        for (
            assertion_id,
            atom_id,
            obligation_id,
            test_case_id,
            value,
            boundary_class,
        ) in boundary["entries"]:
            assertions.append(
                _new_assertion(
                    base,
                    assertion_id=assertion_id,
                    atom_id=atom_id,
                    obligation_id=obligation_id,
                    value=value,
                    boundary_class=boundary_class,
                    requirement_code=str(boundary["requirement_code"]),
                )
            )
            new_obligations.append(
                _new_obligation(
                    obligations_by_id["OBL-110"],
                    obligation_id=obligation_id,
                    atom_id=atom_id,
                    test_case_id=test_case_id,
                    value=value,
                    boundary_class=boundary_class,
                    source_row_id=source_row_id,
                    requirement_code=str(boundary["requirement_code"]),
                )
            )
            new_atoms.append(atom_id)
            new_test_cases.append(test_case_id)
    repaired["obligations"].extend(new_obligations)
    for row in repaired["applicability"]:
        if row.get("dimension") in {"traceability", "boundary"}:
            row["linked_atoms"].extend(new_atoms)
            row["linked_test_cases"].extend(new_test_cases)
            if row.get("dimension") == "boundary":
                row["reason"] = (
                    str(row.get("reason", "")).rstrip(". ")
                    + ". Exact-length индексов разложен на отдельные N, N-1 и "
                    "N+1 classes без выдумывания UI-механизма."
                )
    return repaired


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Add the missing exact-length boundary model to AutoFin addresses."
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
        "added_assertion_ids": sorted(
            entry[0] for boundary_item in BOUNDARIES for entry in boundary_item["entries"]
        ),
        "added_obligation_ids": sorted(
            entry[2] for boundary_item in BOUNDARIES for entry in boundary_item["entries"]
        ),
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
