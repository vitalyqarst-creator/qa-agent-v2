from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[7]
FT_ROOT = ROOT / "fts" / "AutoFin" / "PostFinal-v2-rc5"
HANDOFF = FT_ROOT / "work" / "stage-handoffs" / "07-4.3-client-addresses"
PREPARED = FT_ROOT / "work" / "review-cycles" / "07-4.3-client-addresses" / "prepared-input" / "WP-ALL-v2"
FIXTURE_ROOT = FT_ROOT / "work" / "vendor-references" / "dadata-fixtures"


ADDR_POS = {
    "fixture_id": "FX-DADATA-ADDR-POS-001",
    "query": "самара авроры 7 12",
    "exact_suggestion": "г Самара, ул Авроры, д 7, кв 12",
    "response": "work/vendor-references/dadata-fixtures/FX-DADATA-ADDR-POS-001.response.json",
    "verification": "work/vendor-references/dadata-fixtures/FX-DADATA-ADDR-POS-001.verification.json",
    "components": {
        "region_with_type": "Самарская обл",
        "city_with_type": "г Самара",
        "street_with_type": "ул Авроры",
        "house": "7",
        "flat": "12",
        "postal_code": "443017",
    },
}

ADDR_NEG = {
    "fixture_id": "FX-DADATA-ADDR-NEG-001",
    "query": "ZZZNOADDRESS7F3A9C2E20260721",
    "response": "work/vendor-references/dadata-fixtures/FX-DADATA-ADDR-NEG-001.response.json",
    "verification": "work/vendor-references/dadata-fixtures/FX-DADATA-ADDR-NEG-001.verification.json",
    "expected": "suggestions=[]",
}

REGION_FIXTURE = {
    "fixture_id": "FX-DADATA-REGION-POS-001",
    "query": "Саратов",
    "bounds": "from_bound=region; to_bound=region",
    "exact_suggestion": "Саратовская обл",
    "response": "work/vendor-references/dadata-fixtures/FX-DADATA-REGION-POS-001.response.json",
    "verification": "work/vendor-references/dadata-fixtures/FX-DADATA-REGION-POS-001.verification.json",
    "usage_note": "available only for DaData region suggestion checks; not used by ordinary manual Region field TC",
}

PAB_REGIONS = {
    "source": "support/PAB_справочники_выгрузка_v2.md",
    "section": "## Регионы",
    "active_count": 91,
    "representative_values": [
        {"value": "г. Москва", "internal_code": "77", "okato": "45"},
        {"value": "Красноярский край", "internal_code": "24", "okato": "04"},
        {"value": "Саратовская область", "internal_code": "64", "okato": "63"},
    ],
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_dictionary_inventory() -> None:
    rows = [
        "# Dictionary Inventory",
        "",
        "| dictionary_id | dictionary_name | source_file | source_location | extraction_status | active_values | archived_values | used_by_source_properties | gap_id | notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        "| `DICT-DADATA-ADDRESS-SUGGESTIONS` | `DaData address suggestions` | `work/vendor-references/dadata-fixture-catalog.md`; `work/vendor-references/dadata-fixtures/` | `verified local snapshots FX-DADATA-ADDR-POS-001 and FX-DADATA-ADDR-NEG-001` | `verified-fixtures` | `FX-DADATA-ADDR-POS-001: query=самара авроры 7 12, suggestion=г Самара, ул Авроры, д 7, кв 12`; `FX-DADATA-ADDR-NEG-001: query=ZZZNOADDRESS7F3A9C2E20260721, expected suggestions=[]` | `-` | `PROP-ADDR-004; PROP-ADDR-028; PROP-ADDR-052` | `none` | `fixture-backed; do not infer trigger, debounce, ordering, count or fallback behavior` |",
        "| `DICT-DADATA-REGION` | `PAB region dictionary for manual Region fields` | `support/PAB_справочники_выгрузка_v2.md` | `section ## Регионы, lines 614-707` | `extracted` | `91 active values; representative: Саратовская область/code 64/OKATO 63; checked: г. Москва/code 77/OKATO 45; Красноярский край/code 24/OKATO 04` | `-` | `PROP-ADDR-014; PROP-ADDR-041` | `none` | `manual Region fields use PAB dictionary; FX-DADATA-REGION-POS-001 is reserved for DaData region suggestion checks only` |",
        "",
    ]
    (HANDOFF / "dictionary-inventory.md").write_text("\n".join(rows), encoding="utf-8", newline="\n")


def dictionary_requirement(dictionary_id: str, coverage_mode: str, fixture_values: list[str], required_values: list[dict[str, str]]) -> dict[str, object]:
    return {
        "coverage_mode": coverage_mode,
        "dictionary_id": dictionary_id,
        "fixture_values": fixture_values,
        "required_values": required_values,
    }


def update_atomic_obligations() -> None:
    path = PREPARED / "atomic-obligations.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    obligations = data["obligations"] if isinstance(data, dict) else data
    by_id = {item["obligation_id"]: item for item in obligations}

    pos_ids = {"OBL-ADDR-004", "OBL-ADDR-030"}
    pos_decomposition_ids = {"OBL-ADDR-008", "OBL-ADDR-034", "OBL-ADDR-054"}
    neg_ids = {"OBL-ADDR-007", "OBL-ADDR-033"}
    region_ids = {"OBL-ADDR-014", "OBL-ADDR-040"}

    for oid in pos_ids | pos_decomposition_ids:
        item = by_id[oid]
        refs = set(item.get("dictionary_refs") or [])
        refs.add("DICT-DADATA-ADDRESS-SUGGESTIONS")
        item["dictionary_refs"] = sorted(refs)
        item["dictionary_requirements"] = [
            dictionary_requirement("DICT-DADATA-ADDRESS-SUGGESTIONS", "fixture-backed", [ADDR_POS["fixture_id"]], [])
        ]
        source_refs = list(dict.fromkeys([*(item.get("source_refs") or []), "FX-DADATA-ADDR-POS-001"]))
        item["source_refs"] = source_refs
        item["test_intent"] = item["test_intent"] + (
            f"; Fixture: {ADDR_POS['fixture_id']}, query `{ADDR_POS['query']}`, "
            f"suggestion `{ADDR_POS['exact_suggestion']}`"
        )

    for oid in neg_ids:
        item = by_id[oid]
        refs = set(item.get("dictionary_refs") or [])
        refs.add("DICT-DADATA-ADDRESS-SUGGESTIONS")
        item["dictionary_refs"] = sorted(refs)
        item["dictionary_requirements"] = [
            dictionary_requirement("DICT-DADATA-ADDRESS-SUGGESTIONS", "negative-fixture-backed", [ADDR_NEG["fixture_id"]], [])
        ]
        source_refs = list(dict.fromkeys([*(item.get("source_refs") or []), "FX-DADATA-ADDR-NEG-001"]))
        item["source_refs"] = source_refs
        item["test_intent"] = item["test_intent"] + (
            f"; Fixture: {ADDR_NEG['fixture_id']}, query `{ADDR_NEG['query']}`, expected `{ADDR_NEG['expected']}`"
        )

    required_regions = PAB_REGIONS["representative_values"]
    for oid in region_ids:
        item = by_id[oid]
        item["dictionary_refs"] = ["DICT-DADATA-REGION"]
        item["dictionary_requirements"] = [
            dictionary_requirement("DICT-DADATA-REGION", "pab-representative-values", [], required_regions)
        ]
        item["source_refs"] = list(dict.fromkeys([*(item.get("source_refs") or []), "PAB-REGIONS"]))
        if oid == "OBL-ADDR-014":
            item["observable_oracle"] = "Поле «Регион» отображается в ручном режиме адреса регистрации и позволяет выбрать значение из PAB справочника регионов."
        else:
            item["observable_oracle"] = "Поле «Регион» отображается в ручном режиме фактического адреса и позволяет выбрать значение из PAB справочника регионов."
        item["test_intent"] = item["test_intent"] + "; Dictionary fixture: PAB regions representative `Саратовская область`, code `64`, OKATO `63`"

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def replace_dictionary_block(text: str, dictionary_id: str, payload: dict[str, object]) -> str:
    pattern = rf"(## {re.escape(dictionary_id)}\n\n```json\n)(.*?)(\n```)"
    replacement = rf"\1{json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}\3"
    return re.sub(pattern, replacement, text, flags=re.S)


def update_source_evidence() -> None:
    path = PREPARED / "source-evidence.md"
    text = path.read_text(encoding="utf-8")
    address_payload = {
        "dictionary_id": "DICT-DADATA-ADDRESS-SUGGESTIONS",
        "dictionary_name": "DaData address suggestions",
        "source_file": "work/vendor-references/dadata-fixture-catalog.md",
        "source_location": "verified local DaData snapshots",
        "extraction_status": "verified-fixtures",
        "active_values": [ADDR_POS, ADDR_NEG],
        "archived_values": "-",
    }
    region_payload = {
        "dictionary_id": "DICT-DADATA-REGION",
        "dictionary_name": "PAB region dictionary for manual Region fields",
        "source_file": PAB_REGIONS["source"],
        "source_location": PAB_REGIONS["section"],
        "extraction_status": "extracted",
        "active_values": PAB_REGIONS,
        "archived_values": "-",
        "usage_note": REGION_FIXTURE["usage_note"],
    }
    text = replace_dictionary_block(text, "DICT-DADATA-ADDRESS-SUGGESTIONS", address_payload)
    text = replace_dictionary_block(text, "DICT-DADATA-REGION", region_payload)
    marker = "\n## Client Addresses Fixture Evidence\n"
    fixture_section = (
        marker
        + "\n```json\n"
        + json.dumps(
            {
                "dadata_address_positive": ADDR_POS,
                "dadata_address_negative": ADDR_NEG,
                "dadata_region_positive_available_not_manual_region": REGION_FIXTURE,
                "pab_regions": PAB_REGIONS,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n```\n"
    )
    if marker in text:
        text = text[: text.index(marker)] + fixture_section
    else:
        text = text.rstrip() + "\n" + fixture_section
    path.write_text(text, encoding="utf-8", newline="\n")


def update_stage_package() -> None:
    path = PREPARED / "stage-package.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    source_paths = [
        ("support-dictionary", FT_ROOT / "support" / "PAB_справочники_выгрузка_v2.md"),
        ("vendor-fixture-catalog", FT_ROOT / "work" / "vendor-references" / "dadata-fixture-catalog.md"),
        ("vendor-fixture", FIXTURE_ROOT / "FX-DADATA-ADDR-POS-001.response.json"),
        ("vendor-fixture", FIXTURE_ROOT / "FX-DADATA-ADDR-POS-001.verification.json"),
        ("vendor-fixture", FIXTURE_ROOT / "FX-DADATA-ADDR-NEG-001.response.json"),
        ("vendor-fixture", FIXTURE_ROOT / "FX-DADATA-ADDR-NEG-001.verification.json"),
        ("vendor-fixture", FIXTURE_ROOT / "FX-DADATA-REGION-POS-001.response.json"),
        ("vendor-fixture", FIXTURE_ROOT / "FX-DADATA-REGION-POS-001.verification.json"),
    ]
    registry = {item["path"]: item for item in data.get("source_registry", [])}
    for role, p in source_paths:
        registry[rel(p)] = {
            "locator": "controlled baseline evidence repair",
            "path": rel(p),
            "role": role,
            "sha256": sha256(p),
        }
    data["source_registry"] = list(registry.values())

    for artifact in data.get("package_artifacts", []):
        artifact_path = ROOT / artifact["path"]
        artifact["bytes"] = artifact_path.stat().st_size
        artifact["sha256"] = sha256(artifact_path)

    digest_input = {
        "package_artifacts": data.get("package_artifacts", []),
        "source_registry": data.get("source_registry", []),
        "package_id": data.get("package_id"),
        "scope_slug": data.get("scope_slug"),
    }
    data["package_digest"] = hashlib.sha256(json.dumps(digest_input, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    required = [
        FIXTURE_ROOT / "FX-DADATA-ADDR-POS-001.response.json",
        FIXTURE_ROOT / "FX-DADATA-ADDR-POS-001.verification.json",
        FIXTURE_ROOT / "FX-DADATA-ADDR-NEG-001.response.json",
        FIXTURE_ROOT / "FX-DADATA-ADDR-NEG-001.verification.json",
        FIXTURE_ROOT / "FX-DADATA-REGION-POS-001.response.json",
        FIXTURE_ROOT / "FX-DADATA-REGION-POS-001.verification.json",
        FT_ROOT / "support" / "PAB_справочники_выгрузка_v2.md",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit(json.dumps({"status": "missing-input", "missing": missing}, ensure_ascii=False))
    write_dictionary_inventory()
    update_atomic_obligations()
    update_source_evidence()
    update_stage_package()
    print(json.dumps({"status": "updated", "prepared": rel(PREPARED)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
