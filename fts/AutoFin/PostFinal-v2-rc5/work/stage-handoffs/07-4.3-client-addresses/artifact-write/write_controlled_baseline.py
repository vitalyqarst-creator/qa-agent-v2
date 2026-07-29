from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[7]
FT_ROOT = ROOT / "fts" / "AutoFin" / "PostFinal-v2-rc5"
HANDOFF = FT_ROOT / "work" / "stage-handoffs" / "07-4.3-client-addresses"
TARGET = FT_ROOT / "test-cases" / "4-3-client-addresses.md"

NEEDS_TEST_DATA = {
    "OBL-ADDR-004": "нужен сохраненный DaData response/verification для запроса адреса регистрации, подтверждающий появление подсказок; trigger/debounce/count/order не утверждать",
    "OBL-ADDR-007": "нужен сохраненный DaData response/verification для запроса адреса регистрации со статусом «адрес не найден»",
    "OBL-ADDR-008": "нужен сохраненный DaData response/verification для найденного адреса регистрации и ожидаемая раскладка по ручным полям",
    "OBL-ADDR-014": "нужен сохраненный DaData response/verification или UI evidence для актуального значения региона в external dynamic dictionary",
    "OBL-ADDR-030": "нужен сохраненный DaData response/verification для запроса фактического адреса, подтверждающий появление подсказок; trigger/debounce/count/order не утверждать",
    "OBL-ADDR-033": "нужен сохраненный DaData response/verification для запроса фактического адреса со статусом «адрес не найден»",
    "OBL-ADDR-034": "нужен сохраненный DaData response/verification для найденного фактического адреса и ожидаемая раскладка по ручным полям",
    "OBL-ADDR-040": "нужен сохраненный DaData response/verification или UI evidence для актуального значения региона фактического адреса в external dynamic dictionary",
    "OBL-ADDR-054": "нужен сохраненный DaData response/verification для выбранного адреса и ожидаемая раскладка по ручным полям; внутренний kladr исключен",
}

CANDIDATE_UI = {
    "OBL-ADDR-005",
    "OBL-ADDR-013",
    "OBL-ADDR-021",
    "OBL-ADDR-023",
    "OBL-ADDR-031",
    "OBL-ADDR-047",
    "OBL-ADDR-049",
    "OBL-ADDR-051",
    "OBL-ADDR-052",
    "OBL-ADDR-053",
    "OBL-ADDR-056",
    "OBL-ADDR-057",
    "OBL-ADDR-058",
    "OBL-ADDR-059",
    "OBL-ADDR-060",
    "OBL-ADDR-061",
    "OBL-ADDR-062",
}


def one(items: list[str]) -> str:
    return items[0] if items else "Не требуется."


def lines_for_case(assertion: dict[str, object]) -> list[str]:
    obligation_id = assertion["obligation_ids"][0]
    tc_id = "TC-ADDR-" + obligation_id.rsplit("-", 1)[-1]
    req_codes = assertion.get("requirement_codes") or []
    status = "fully-ready"
    oracle_status = "source-backed"
    note = "Не требуется."
    if obligation_id in NEEDS_TEST_DATA:
        status = "needs-test-data"
        oracle_status = "ui-calibration-required"
        note = NEEDS_TEST_DATA[obligation_id]
    elif obligation_id in CANDIDATE_UI:
        status = "candidate-ui-calibration"
        oracle_status = "ui-calibration-required"
        note = (
            "Зафиксировать фактический UI-механизм отклонения/обязательности: "
            "символ не вводится, значение очищается, сообщение, подсветка, блокировка перехода/сохранения или другое наблюдаемое поведение."
        )
    condition = one(list(assertion.get("condition_clauses") or []))
    action = one(list(assertion.get("action_clauses") or []))
    oracle = one(list(assertion.get("oracle_clauses") or []))
    source_ref = "; ".join(
        item
        for item in [
            assertion.get("source_row_id", ""),
            assertion.get("assertion_id", ""),
            assertion.get("atom_id", ""),
            obligation_id,
            "; ".join(req_codes) if req_codes else "",
        ]
        if item
    )
    data = "Source-backed representative value from action/condition."
    if status == "needs-test-data":
        data = note
    elif status == "candidate-ui-calibration":
        data = "Representative invalid or empty value from action clause; exact UI reaction pending calibration."
    return [
        f"### {tc_id} — {assertion['canonical_statement']}",
        "",
        f"- **Статус тест-кейса:** `{status}`",
        f"- **Статус oracle:** `{oracle_status}`",
        f"- **Приоритет:** `{assertion.get('risk', 'medium')}`",
        f"- **Тип:** `{'негативный/валидационный' if status == 'candidate-ui-calibration' else 'позитивный/функциональный'}`",
        f"- **Трассировка:** `{source_ref}`",
        f"- **Тестовые данные:** {data}",
        f"- **Требуется уточнение:** {note}",
        "",
        "**Предусловия:**",
        "",
        "1. Открыта карточка `Заявка`.",
        "2. Доступен блок `Адреса клиента`.",
        "",
        "**Шаги:**",
        "",
        f"1. Подготовить состояние: {condition}",
        f"2. Выполнить действие: {action}",
        "3. Проверить результат в UI.",
        "",
        "**Ожидаемый результат:**",
        "",
        oracle,
        "",
    ]


def main() -> int:
    manifest = json.loads((HANDOFF / "source-assertions.json").read_text(encoding="utf-8-sig"))
    cases = [item for item in manifest["assertions"] if item.get("obligation_ids")]
    cases.sort(key=lambda item: item["obligation_ids"][0])
    ready = sum(1 for item in cases if item["obligation_ids"][0] not in NEEDS_TEST_DATA and item["obligation_ids"][0] not in CANDIDATE_UI)
    test_data = sum(1 for item in cases if item["obligation_ids"][0] in NEEDS_TEST_DATA)
    calibration = sum(1 for item in cases if item["obligation_ids"][0] in CANDIDATE_UI)
    output: list[str] = [
        "# Тест-кейсы: 4.3 Адреса клиента",
        "",
        "## Metadata",
        "",
        "- `scope_slug`: `4-3-client-addresses`",
        "- `source_manifest_digest`: `6455e7cc961a4db024123906a3f2fef5e56ba4f3ca543c8ae25735f06e928538`",
        "- `source_assertion_review`: `source-assertion-review.v11.json`",
        "- `route_status`: `controlled-ft-first-baseline`",
        "- `production_promotion`: `not-performed`",
        f"- `test_case_count`: `{len(cases)}`",
        f"- `execution_ready_count`: `{ready}`",
        f"- `needs_test_data_count`: `{test_data}`",
        f"- `calibration_candidate_count`: `{calibration}`",
        "- `suite_readiness`: `ft-first-reviewed-with-test-data-and-calibration-pending`",
        "",
        "## Scope Notes",
        "",
        "- DOCX остается source of truth; XHTML source rows and PDF parity are bound through the accepted source assertion manifest.",
        "- DaData-specific cases do not invent concrete API responses, suggestion ordering, trigger length, debounce, fallback behavior, or region lists.",
        "- Internal `kladr` verification from BSR 324 is excluded from UI test cases by approved clarification; only observable decomposition into manual address fields is covered.",
        "",
        "## Test Cases",
        "",
    ]
    for case in cases:
        output.extend(lines_for_case(case))
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "path": str(TARGET), "test_case_count": len(cases), "fully_ready": ready, "needs_test_data": test_data, "candidate_ui_calibration": calibration}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
