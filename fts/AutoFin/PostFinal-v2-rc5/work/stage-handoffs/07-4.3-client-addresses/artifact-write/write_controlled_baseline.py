from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[7]
FT_ROOT = ROOT / "fts" / "AutoFin" / "PostFinal-v2-rc5"
HANDOFF = FT_ROOT / "work" / "stage-handoffs" / "07-4.3-client-addresses"
TARGET = FT_ROOT / "test-cases" / "4-3-client-addresses.md"

NEEDS_TEST_DATA: dict[str, str] = {}

DADATA_POSITIVE_DATA = (
    "Fixture `FX-DADATA-ADDR-POS-001`: query `самара авроры 7 12`; "
    "expected suggestion `г Самара, ул Авроры, д 7, кв 12`; "
    "response `work/vendor-references/dadata-fixtures/FX-DADATA-ADDR-POS-001.response.json`; "
    "verification `work/vendor-references/dadata-fixtures/FX-DADATA-ADDR-POS-001.verification.json`; "
    "exact components: `region_with_type=Самарская обл`, `city_with_type=г Самара`, "
    "`street_with_type=ул Авроры`, `house=7`, `flat=12`, `postal_code=443017`."
)

DADATA_NEGATIVE_DATA = (
    "Fixture `FX-DADATA-ADDR-NEG-001`: query `ZZZNOADDRESS7F3A9C2E20260721`; "
    "response `work/vendor-references/dadata-fixtures/FX-DADATA-ADDR-NEG-001.response.json`; "
    "verification `work/vendor-references/dadata-fixtures/FX-DADATA-ADDR-NEG-001.verification.json`; "
    "verified expected DaData response: `suggestions=[]`."
)

PAB_REGION_DATA = (
    "PAB dictionary `support/PAB_справочники_выгрузка_v2.md`, section `## Регионы`, "
    "91 active values. Representative value: `Саратовская область`, internal code `64`, OKATO `63`; "
    "additional checked values include `г. Москва`/`77`/`45` and `Красноярский край`/`24`/`04`."
)

TEST_DATA_OVERRIDES = {
    "OBL-ADDR-004": DADATA_POSITIVE_DATA,
    "OBL-ADDR-007": DADATA_NEGATIVE_DATA,
    "OBL-ADDR-008": DADATA_POSITIVE_DATA,
    "OBL-ADDR-014": PAB_REGION_DATA,
    "OBL-ADDR-030": DADATA_POSITIVE_DATA,
    "OBL-ADDR-033": DADATA_NEGATIVE_DATA,
    "OBL-ADDR-034": DADATA_POSITIVE_DATA,
    "OBL-ADDR-040": PAB_REGION_DATA,
    "OBL-ADDR-054": DADATA_POSITIVE_DATA + " Internal `kladr` persistence is excluded from UI TC by approved clarification.",
}

ORACLE_OVERRIDES = {
    "OBL-ADDR-014": (
        "Поле «Регион» отображается в ручном режиме адреса регистрации и позволяет выбрать "
        "значение из PAB справочника регионов; проверочное значение: `Саратовская область`, "
        "код `64`, ОКАТО `63`."
    ),
    "OBL-ADDR-040": (
        "Поле «Регион» отображается в ручном режиме фактического адреса и позволяет выбрать "
        "значение из PAB справочника регионов; проверочное значение: `Саратовская область`, "
        "код `64`, ОКАТО `63`."
    ),
}

TYPE_OVERRIDES = {
    "OBL-ADDR-007": "негативный/валидационный",
    "OBL-ADDR-033": "негативный/валидационный",
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
    oracle = ORACLE_OVERRIDES.get(obligation_id, one(list(assertion.get("oracle_clauses") or [])))
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
    data = TEST_DATA_OVERRIDES.get(obligation_id, "Source-backed representative value from action/condition.")
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
        f"- **Тип:** `{TYPE_OVERRIDES.get(obligation_id, 'негативный/валидационный' if status == 'candidate-ui-calibration' else 'позитивный/функциональный')}`",
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
        "- DaData-specific cases use verified local snapshot fixtures and do not invent suggestion ordering, trigger length, debounce, count or fallback behavior.",
        "- Manual `Регион` fields use PAB dictionary values from `support/PAB_справочники_выгрузка_v2.md` section `## Регионы`; `FX-DADATA-REGION-POS-001` is not used for ordinary manual region field checks.",
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
