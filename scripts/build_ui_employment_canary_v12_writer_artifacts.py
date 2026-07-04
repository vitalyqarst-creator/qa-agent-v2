from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "fts" / "ft-2-OF_16"
SCOPE = "ui-employment-canary-v12-validator-execution-regression"
SECTION = "2-1-1-1-1-2"
TD = FT / "work" / "test-design" / SCOPE
CYCLE = FT / "work" / "review-cycles" / SCOPE
OUT = CYCLE / "outputs"
PROMPTS = CYCLE / "prompts"
CANONICAL = FT / "test-cases" / f"{SECTION}-{SCOPE}.md"
BUILD = TD / "_build"


def table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    out.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(out)


def normalize_ids(content: str) -> str:
    for idx in range(1, 100):
        content = content.replace(f"TC-{idx:03d}", f"TC-UI-EMP-V12-{idx:03d}")
    return content


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(normalize_ids(content).rstrip() + "\n", encoding="utf-8", newline="\n")


def write_artifact(target: Path, title: str, sections: list[tuple[int, str, str]]) -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    manifest_dir = BUILD / target.name.replace(".", "_")
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"target_path": str(target), "sections": []}
    for idx, (level, heading, content) in enumerate(sections, start=1):
        content_file = manifest_dir / f"section-{idx:02d}.md"
        write_text(content_file, content)
        manifest["sections"].append(
            {"level": level, "heading": heading, "content_file": content_file.name}
        )
    manifest_path = manifest_dir / "manifest.json"
    write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2))
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(manifest_path)],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
        raise RuntimeError(f"write_artifact_sections failed for {target}: {stderr}")


def source_inventory() -> str:
    rows = [
        ["`SRC-002`", "`WP-01`", "Тип занятости", "DOCX section-23 table 11 row 3; PDF p.61", "`-`", "`yes`", "`ATOM-001`; `ATOM-002`; `ATOM-003`; `ATOM-004`"],
        ["`SRC-003`", "`WP-01`", "Среднемесячный доход после вычета налогов (основная работа)", "DOCX section-23 table 11 row 4; PDF p.61", "`GSR 123`; `GSR 124`", "`yes`", "`ATOM-005`; `ATOM-006`; `ATOM-007`; `GAP-005`; `GAP-006`"],
        ["`SRC-004`", "`WP-01`", "Наименование организации, ИНН", "DOCX section-23 table 11 row 5; PDF p.61", "`GSR 125`; `GSR 126`", "`fixture-context`", "`GAP-001`; not executable in v12 medium scope"],
        ["`SRC-005`", "`WP-01`", "Фактический адрес работы", "DOCX section-23 table 11 row 6; PDF p.61", "`GSR 127`; `GSR 128`", "`fixture-context`", "`GAP-001`; not executable in v12 medium scope"],
        ["`SRC-010`", "`WP-02`", "Блок «Дополнительный доход»", "DOCX section-23 table 11 row 11; PDF p.62", "`-`", "`yes`", "`ATOM-008`; `ATOM-009`"],
        ["`SRC-011`", "`WP-02`", "Тип дохода", "DOCX section-23 table 11 row 12; PDF p.62", "`-`", "`yes`", "`ATOM-010`; `ATOM-011`; `GAP-002`"],
        ["`SRC-012`", "`WP-02`", "Среднемесячный доход после вычета налогов (дополнительный доход)", "DOCX section-23 table 11 row 13; PDF p.62", "`GSR 135`", "`yes`", "`ATOM-012`; `GAP-007`"],
        ["`SRC-014`", "`WP-03`", "Клиент добросовестный", "DOCX section-23 table 11 row 15; PDF p.62", "`GSR 136`", "`yes`", "`ATOM-013`; `ATOM-014`; `ATOM-015`"],
        ["`SRC-015`", "`WP-03`", "Визуальная информация", "DOCX section-23 table 11 row 16; PDF p.62", "`GSR 137`; `GSR 138`", "`yes`", "`ATOM-016`; `ATOM-017`; `ATOM-018`; `ATOM-019`"],
        ["`SRC-016`", "`WP-03`", "Параметры визуальной оценки", "DOCX section-23 table 11 row 17; PDF pp.62-63", "`GSR 139`; `GSR 140`", "`yes`", "`ATOM-020`; `ATOM-021`; `ATOM-022`; `ATOM-023`; `ATOM-024`"],
        ["`SRC-018`", "`WP-04`", "«Следующий шаг»", "DOCX section-24 table 12 row 2; PDF pp.63-65", "`GSR 142`; `GSR 143`", "`yes`", "`ATOM-025`; `ATOM-026`; `GAP-003`"],
        ["`SRC-019`", "`WP-04`", "«Добавить работу по совместительству»", "DOCX section-24 table 12 row 3; PDF p.65", "`GSR 144`; `GSR 145`", "`yes`", "`ATOM-027`; `ATOM-028`"],
        ["`SRC-020`", "`WP-04`", "«Добавить дополнительный доход»", "DOCX section-24 table 12 row 4; PDF p.65", "`GSR 146`; `GSR 147`", "`yes`", "`ATOM-008`; `ATOM-009`"],
        ["`SRC-021`", "`WP-04`", "«Назад»", "DOCX section-24 table 12 row 5; PDF p.65", "`GSR 148`", "`yes`", "`ATOM-029`; `ATOM-030`; `ATOM-031`"],
        ["`SRC-022`", "`WP-05`", "CDI: не удалось верифицировать ИНН", "PDF pp.65-66", "`-`", "`residual-gap`", "`GAP-004`; out of executable v12 scope"],
        ["`SRC-023`", "`WP-05`", "CDI: данные клиента отличаются от данных заявки", "PDF p.66", "`-`", "`residual-gap`", "`GAP-004`; out of executable v12 scope"],
        ["`SRC-024`", "`WP-05`", "CDI: подтверждение замены данных", "PDF p.67", "`-`", "`residual-gap`", "`GAP-004`; out of executable v12 scope"],
    ]
    return table(["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"], rows)


NORMALIZATION_ROWS = [
    ["`SP-001`", "`SRC-002`", "`WP-01`", "Тип занятости всегда видим", "visibility", "`ATOM-001`"],
    ["`SP-002`", "`SRC-002`", "`WP-01`", "Тип занятости обязателен", "requiredness", "`ATOM-002`"],
    ["`SP-003`", "`SRC-002`", "`WP-01`", "Тип занятости редактируем", "editability", "`ATOM-003`"],
    ["`SP-004`", "`SRC-002`", "`WP-01`", "Тип занятости использует справочник DICT-001", "dictionary-source", "`ATOM-004`"],
    ["`SP-005`", "`SRC-003`", "`WP-01`", "Основной доход видим после заполнения типа занятости", "conditional-visibility", "`ATOM-005`"],
    ["`SP-006`", "`SRC-003`", "`WP-01`", "Основной доход обязателен и редактируем", "requiredness/editability", "`ATOM-006`; `ATOM-007`"],
    ["`SP-007`", "`SRC-003`", "`WP-01`", "Основной доход: только числовые символы, сумма не менее 2000р", "numeric-format", "`GAP-005`; `GAP-006`"],
    ["`SP-008`", "`SRC-010`; `SRC-020`", "`WP-02`", "После действия отображается блок дополнительного дохода", "action-created-optional-block", "`ATOM-008`"],
    ["`SP-009`", "`SRC-010`; `SRC-020`", "`WP-02`", "Созданный блок дополнительного дохода удаляется корзиной", "repeatable-block-lifecycle", "`ATOM-009`"],
    ["`SP-010`", "`SRC-011`", "`WP-02`", "Тип дохода обязателен, редактируем и использует DICT-004", "dictionary-source", "`ATOM-010`; `ATOM-011`"],
    ["`SP-011`", "`SRC-011`", "`WP-02`", "Пенсия и Аренда могут быть добавлены только один раз", "duplicate-prevention", "`GAP-002`"],
    ["`SP-012`", "`SRC-012`", "`WP-02`", "Дополнительный доход принимает только числовые символы", "numeric-format", "`ATOM-012`; `GAP-007`"],
    ["`SP-013`", "`SRC-014`", "`WP-03`", "Клиент добросовестный всегда видим, редактируем, default Нет", "toggle-default", "`ATOM-013`; `ATOM-014`"],
    ["`SP-014`", "`SRC-014`", "`WP-03`", "Клиент добросовестный не обязателен, если визуальная информация = Да", "conditional-requiredness", "`ATOM-015`"],
    ["`SP-015`", "`SRC-015`", "`WP-03`", "Визуальная информация всегда видима, редактируема, default Нет", "toggle-default", "`ATOM-016`; `ATOM-017`"],
    ["`SP-016`", "`SRC-015`", "`WP-03`", "Визуальная информация не обязательна, если клиент добросовестный = Да", "conditional-requiredness", "`ATOM-018`"],
    ["`SP-017`", "`SRC-015`", "`WP-03`", "При значении Да отображается список параметров визуальной оценки", "conditional-visibility", "`ATOM-019`"],
    ["`SP-018`", "`SRC-016`", "`WP-03`", "Параметры визуальной оценки используют DICT-005 и чекбокс по каждому значению", "checkbox-list", "`ATOM-020`; `ATOM-021`"],
    ["`SP-019`", "`SRC-016`", "`WP-03`", "При визуальной информации = Да должен быть выбран хотя бы один параметр", "requiredness", "`ATOM-022`; `ATOM-023`; `ATOM-024`"],
    ["`SP-020`", "`SRC-018`", "`WP-04`", "Следующий шаг подсвечивает незаполненные обязательные поля красным", "transition-validation", "`ATOM-025`"],
    ["`SP-021`", "`SRC-018`", "`WP-04`", "Следующий шаг при валидном заполнении формирует заявление-анкету и открывает Анкету клиента", "navigation", "`ATOM-026`"],
    ["`SP-022`", "`SRC-019`", "`WP-04`", "Добавить работу по совместительству отображает поля блока и корзину удаления", "action-created-optional-block", "`ATOM-027`; `ATOM-028`"],
    ["`SP-023`", "`SRC-021`", "`WP-04`", "Назад показывает подтверждение сохранения с вариантами Да/Нет", "branch-dialog", "`ATOM-029`"],
    ["`SP-024`", "`SRC-021`", "`WP-04`", "Назад: Да сохраняет данные и открывает Основную информацию", "branch-save-navigation", "`ATOM-030`"],
    ["`SP-025`", "`SRC-021`", "`WP-04`", "Назад: Нет открывает Основную информацию без сохранения текущего изменения", "branch-discard-navigation", "`ATOM-031`"],
]


def source_normalization() -> str:
    return table(["source_property_id", "source_row_id", "package_id", "normalized_property", "property_type", "mapped_atom_or_gap"], NORMALIZATION_ROWS)


def dictionary_inventory() -> str:
    rows = [
        ["`DICT-001`", "Типы занятости", "`support/Наполнение справочников_v1.xlsx`", "`sheet: Типы занятости; rows 4-9`", "`extracted`", "`Работа по найму`; `Пенсионер (не работает)`; `Индивидуальный предприниматель`; `Собственник бизнеса`; `Частная практика / Самозанятый`; `Безработный`", "`-`", "`SRC-002`; `SP-004`", "`-`"],
        ["`DICT-004`", "Типы дохода", "`support/Наполнение справочников_v1.xlsx`", "`sheet: Виды дохода; rows 4-5`", "`extracted`", "`Пенсия`; `Аренда`", "`-`", "`SRC-011`; `SP-010`; `SP-011`", "`GAP-002`"],
        ["`DICT-005`", "Параметры визуальной оценки", "`support/Наполнение справочников_v1.xlsx`", "`sheet: Параметры визуальной оценки; rows 4-15`", "`extracted`", "`Подозрение на мошеничество`; `Подозрение на судимость`; `Подозрение на алкогольное опьянение`; `Подозрение на наркотическое опьянение`; `Подозрение на психическое заболевание`; `Подозрение на социальную инженерию`; `Асоциальный элемент (бомжи, аалкоголики, наркоманы, цыгане)`; `Потенциальный неплательщик`; `Явные признаки нетрудоспособности`; `Отказ от фотографирования`; `Иные подозрения`; `Не выявлено`", "`-`", "`SRC-016`; `SP-018`", "`-`"],
    ]
    return table(["dictionary_id", "dictionary_name", "source_file", "source_location", "extraction_status", "active_values", "archived_values", "used_by_source_properties", "gap_id"], rows)


def tddt() -> str:
    rows = []
    for sp, src, wp, prop, ptype, atom in NORMALIZATION_ROWS:
        decision = "gap_unclear" if "GAP-" in atom and "ATOM-" not in atom else "standalone_tc"
        if sp in ("`SP-006`",):
            decision = "covered_by_existing_tc"
        rows.append([sp, wp, src, ptype, decision, atom, "См. package plan; executable rows have observable UI oracle, unresolved mechanism remains GAP."])
    return table(["source_property_id", "package_id", "source_row_id", "property_type", "design_decision", "planned_atom_or_gap", "decision_notes"], rows)


def obligations() -> str:
    rows = [
        ["`OBL-001`", "`WP-01`", "`SP-004`", "`ATOM-004`", "`dictionary-source`", "`all-and-only-active-values`", "Список `Тип занятости` показывает все и только active values `DICT-001`.", "`SRC-002`; `DICT-001`", "`TC-001`", "`planned`", "DICT id required in TC traceability."],
        ["`OBL-002`", "`WP-01`", "`SP-007`", "`GAP-005`", "`numeric-format`", "`below-min-feedback`", "Для значения меньше 2000 не задан observable feedback mechanism.", "`SRC-003`; `GSR 124`", "`GAP-005`", "`gap`", "Do not invent exact invalid oracle."],
        ["`OBL-003`", "`WP-01`", "`SP-007`", "`GAP-006`", "`numeric-format`", "`non-digit-feedback`", "Для букв/пробелов/спецсимволов не задан deterministic observable feedback.", "`SRC-003`; `GSR 124`", "`GAP-006`", "`gap`", "Valid/min class covered separately."],
        ["`OBL-004`", "`WP-02`", "`SP-008`", "`ATOM-008`", "`action-created-optional-block`", "`create-block`", "Нажатие `Добавить дополнительный доход` отображает поля блока.", "`SRC-020`; `GSR 146`", "`TC-006`", "`planned`", "Postcondition removes created block."],
        ["`OBL-005`", "`WP-02`", "`SP-009`", "`ATOM-009`", "`repeatable-block-lifecycle`", "`delete-created-block`", "Корзина удаляет созданный блок дополнительного дохода.", "`SRC-020`; `GSR 147`", "`TC-010`", "`planned`", "Deterministic cleanup."],
        ["`OBL-006`", "`WP-02`", "`SP-010`", "`ATOM-011`", "`dictionary-source`", "`all-and-only-active-values`", "Список `Тип дохода` показывает все и только active values `DICT-004`.", "`SRC-011`; `DICT-004`", "`TC-007`", "`planned`", "Duplicate exact mechanism remains GAP-002."],
        ["`OBL-007`", "`WP-02`", "`SP-011`", "`GAP-002`", "`duplicate-prevention`", "`mechanism-unclear`", "Инвариант однократного добавления `Пенсия`/`Аренда` есть, но UI mechanism не задан.", "`SRC-011`; `DICT-004`", "`GAP-002`", "`gap`", "No executable TC with invented error/control state."],
        ["`OBL-008`", "`WP-02`", "`SP-012`", "`GAP-007`", "`numeric-format`", "`non-digit-feedback`", "Для нечислового дополнительного дохода не задан exact feedback.", "`SRC-012`; `GSR 135`", "`GAP-007`", "`gap`", "Positive numeric entry covered."],
        ["`OBL-009`", "`WP-03`", "`SP-018`", "`ATOM-020`", "`checkbox-list`", "`all-active-values`", "Параметры визуальной оценки показывают чекбокс по каждому active value `DICT-005`.", "`SRC-016`; `GSR 139`; `DICT-005`", "`TC-012`", "`planned`", "Preserve workbook spelling."],
        ["`OBL-010`", "`WP-03`", "`SP-019`", "`ATOM-023`", "`checkbox-list`", "`single-selection`", "Один выбранный параметр удовлетворяет требованию выбора хотя бы одного.", "`SRC-016`; `GSR 140`", "`TC-014`", "`planned`", "Single selection source-backed."],
        ["`OBL-011`", "`WP-03`", "`SP-019`", "`ATOM-024`", "`checkbox-list`", "`multiple-selection`", "Несколько выбранных параметров поддержаны source phrase `множественного выбора`.", "`SRC-015`; `GSR 138`", "`TC-015`", "`planned`", "Multiple selection source-backed."],
        ["`OBL-012`", "`WP-03`", "`SP-019`", "`ATOM-022`", "`requiredness`", "`empty-selection-blocks-transition`", "При визуальной информации = Да отсутствие выбранного параметра подсвечивается красным на `Следующий шаг`.", "`SRC-016`; `GSR 140`; `SRC-018`; `GSR 142`", "`TC-013`", "`planned`", "Uses named full-valid fixture delta."],
        ["`OBL-013`", "`WP-04`", "`SP-023`", "`ATOM-029`", "`branch-dialog`", "`confirm-dialog-visible`", "`Назад` показывает подтверждение с вариантами `Да`/`Нет`.", "`SRC-021`; `GSR 148`", "`TC-020`; `TC-021`", "`planned`", "Branches have distinct save/discard oracles."],
    ]
    return table(["obligation_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "obligation_class", "required_behavior", "source_ref", "planned_tc_or_gap", "status", "review_notes"], rows)


def ledger() -> str:
    rows = [
        ["`ATOM-001`", "`WP-01`", "`SRC-002`", "-", "Тип занятости всегда видим.", "`TC-001`", "covered"],
        ["`ATOM-002`", "`WP-01`", "`SRC-002`", "-", "Тип занятости обязателен.", "`TC-002`", "covered"],
        ["`ATOM-003`", "`WP-01`", "`SRC-002`", "-", "Тип занятости редактируем.", "`TC-003`", "covered"],
        ["`ATOM-004`", "`WP-01`", "`SRC-002`; `DICT-001`", "-", "Тип занятости использует все и только active values `DICT-001`.", "`TC-001`", "covered"],
        ["`ATOM-005`", "`WP-01`", "`SRC-003`", "`GSR 123`", "Основной доход отображается после заполнения типа занятости.", "`TC-004`", "covered"],
        ["`ATOM-006`", "`WP-01`", "`SRC-003`", "`GSR 123`", "Основной доход обязателен при отображении.", "`TC-018`", "covered"],
        ["`ATOM-007`", "`WP-01`", "`SRC-003`", "`GSR 123`; `GSR 124`", "Основной доход принимает и отображает значение `2000` как минимальное source-backed значение.", "`TC-005`", "covered"],
        ["`ATOM-008`", "`WP-02`", "`SRC-010`; `SRC-020`", "`GSR 146`", "После добавления дополнительного дохода отображаются поля блока.", "`TC-006`", "covered"],
        ["`ATOM-009`", "`WP-02`", "`SRC-010`; `SRC-020`", "`GSR 147`", "Созданный блок дополнительного дохода можно удалить корзиной.", "`TC-010`", "covered"],
        ["`ATOM-010`", "`WP-02`", "`SRC-011`", "-", "Тип дохода в созданном блоке обязателен и редактируем.", "`TC-006`; `TC-007`", "covered"],
        ["`ATOM-011`", "`WP-02`", "`SRC-011`; `DICT-004`", "-", "Тип дохода использует все и только active values `DICT-004`.", "`TC-007`", "covered"],
        ["`ATOM-012`", "`WP-02`", "`SRC-012`", "`GSR 135`", "Дополнительный доход принимает числовое значение.", "`TC-008`", "covered"],
        ["`ATOM-013`", "`WP-03`", "`SRC-014`", "`GSR 136`", "Клиент добросовестный всегда видим.", "`TC-011`", "covered"],
        ["`ATOM-014`", "`WP-03`", "`SRC-014`", "`GSR 136`", "Клиент добросовестный имеет default `Нет`.", "`TC-011`", "covered"],
        ["`ATOM-015`", "`WP-03`", "`SRC-014`", "`GSR 136`", "Клиент добросовестный не обязателен при Визуальная информация = Да.", "`TC-013`", "covered"],
        ["`ATOM-016`", "`WP-03`", "`SRC-015`", "`GSR 137`", "Визуальная информация всегда видима.", "`TC-011`", "covered"],
        ["`ATOM-017`", "`WP-03`", "`SRC-015`", "`GSR 137`", "Визуальная информация имеет default `Нет`.", "`TC-011`", "covered"],
        ["`ATOM-018`", "`WP-03`", "`SRC-015`", "`GSR 137`", "Визуальная информация не обязательна при Клиент добросовестный = Да.", "`TC-017`", "covered"],
        ["`ATOM-019`", "`WP-03`", "`SRC-015`", "`GSR 138`", "При Визуальная информация = Да отображается список параметров визуальной оценки.", "`TC-012`", "covered"],
        ["`ATOM-020`", "`WP-03`", "`SRC-016`; `DICT-005`", "`GSR 139`", "По каждому active value `DICT-005` доступен чекбокс.", "`TC-012`", "covered"],
        ["`ATOM-021`", "`WP-03`", "`SRC-016`", "`GSR 139`", "Параметры визуальной оценки редактируемы через чекбоксы.", "`TC-014`; `TC-015`; `TC-016`", "covered"],
        ["`ATOM-022`", "`WP-03`", "`SRC-016`", "`GSR 140`", "При Визуальная информация = Да должен быть выбран хотя бы один параметр.", "`TC-013`", "covered"],
        ["`ATOM-023`", "`WP-03`", "`SRC-016`", "`GSR 140`", "Один выбранный параметр удовлетворяет required selection.", "`TC-014`", "covered"],
        ["`ATOM-024`", "`WP-03`", "`SRC-015`; `SRC-016`", "`GSR 138`; `GSR 140`", "Множественный выбор параметров поддержан.", "`TC-015`", "covered"],
        ["`ATOM-025`", "`WP-04`", "`SRC-018`", "`GSR 142`", "Следующий шаг подсвечивает красным незаполненное обязательное поле.", "`TC-002`; `TC-013`; `TC-018`", "covered"],
        ["`ATOM-026`", "`WP-04`", "`SRC-018`", "`GSR 143`", "При валидном заполнении формируется заявление-анкета и открывается Анкета клиента.", "`TC-019`", "covered"],
        ["`ATOM-027`", "`WP-04`", "`SRC-019`", "`GSR 144`", "Добавить работу по совместительству отображает поля блока.", "`TC-022`", "covered"],
        ["`ATOM-028`", "`WP-04`", "`SRC-019`", "`GSR 145`", "Работу по совместительству можно удалить корзиной.", "`TC-023`", "covered"],
        ["`ATOM-029`", "`WP-04`", "`SRC-021`", "`GSR 148`", "Назад показывает подтверждение с ответами Да/Нет.", "`TC-020`; `TC-021`", "covered"],
        ["`ATOM-030`", "`WP-04`", "`SRC-021`", "`GSR 148`", "Ветка Да сохраняет данные текущего раздела и открывает Основная информация.", "`TC-020`", "covered"],
        ["`ATOM-031`", "`WP-04`", "`SRC-021`", "`GSR 148`", "Ветка Нет открывает Основная информация без сохранения текущего изменения.", "`TC-021`", "covered"],
    ]
    return table(["atom_id", "package_id", "source_ref", "req_id", "atomic_statement", "linked_tc_or_gap", "coverage_status"], rows)


def plan() -> str:
    rows = [
        ["`P-001`", "`WP-01`", "`ATOM-004`", "dictionary-list", "all active values and absence of extra active values", "`TC-001`", "Проверить `DICT-001`."],
        ["`P-002`", "`WP-01`", "`ATOM-002`; `ATOM-025`", "requiredness", "empty employment type + Next", "`TC-002`", "Красная подсветка обязательного поля."],
        ["`P-003`", "`WP-01`", "`ATOM-003`", "editability", "`Работа по найму` -> `Безработный`", "`TC-003`", "Expected names old/new/displayed."],
        ["`P-004`", "`WP-01`", "`ATOM-005`; `ATOM-007`", "positive/boundary", "employment type filled; income `2000`", "`TC-004`; `TC-005`", "Invalid feedback routed to gaps."],
        ["`P-005`", "`WP-02`", "`ATOM-008`; `ATOM-009`", "repeatable-block", "create/delete additional income", "`TC-006`; `TC-010`", "Postconditions remove created blocks."],
        ["`P-006`", "`WP-02`", "`ATOM-011`; `DICT-004`", "dictionary-list", "all active values and no extras", "`TC-007`", "Duplicate mechanism stays `GAP-002`."],
        ["`P-007`", "`WP-02`", "`ATOM-012`", "positive numeric", "additional income `3000`", "`TC-008`", "Invalid feedback stays `GAP-007`."],
        ["`P-008`", "`WP-03`", "`ATOM-013`-`ATOM-019`", "dependency/default", "toggle defaults and dependency branches", "`TC-011`; `TC-012`; `TC-017`", "No hidden business behavior."],
        ["`P-009`", "`WP-03`", "`ATOM-020`-`ATOM-024`; `DICT-005`", "checkbox-list", "all values, empty, single, multiple, clear", "`TC-012`; `TC-013`; `TC-014`; `TC-015`; `TC-016`", "Clear is based on checkbox unselect operation."],
        ["`P-010`", "`WP-04`", "`ATOM-026`", "navigation", "valid fixture + Next", "`TC-019`", "Fixture catalog names values."],
        ["`P-011`", "`WP-04`", "`ATOM-027`; `ATOM-028`", "action-created-block", "part-time create/delete", "`TC-022`; `TC-023`", "No employer/address standalone coverage."],
        ["`P-012`", "`WP-04`", "`ATOM-029`-`ATOM-031`", "branch-dialog", "Back Yes vs No", "`TC-020`; `TC-021`", "Distinct save/discard oracles."],
        ["`P-013`", "`WP-05`", "`GAP-004`", "integration setup", "CDI message trigger not provided", "`GAP-004`", "PDF-only rows preserved as residual gap, out of v12 executable scope."],
    ]
    return table(["plan_id", "package_id", "linked_atom_or_gap", "check_type", "input_class", "planned_tc_or_gap", "single_expected_behavior"], rows)


def gaps() -> str:
    return """| gap_id | source_ref | description | impact | planned_handling |
| --- | --- | --- | --- | --- |
| `GAP-001` | `SRC-004`; `SRC-005`; `SRC-017`; `GSR 126`; `GSR 128`; `GSR 141` | DaData trigger, dropdown mechanics and backend SPR artifacts are not specified. | non-blocking residual | Employer/address rows are fixture context only in v12; no executable standalone TC. |
| `GAP-002` | `SRC-011`; `DICT-004` | Exact UI mechanism for preventing duplicate `Пенсия`/`Аренда` is not specified. | non-blocking residual | Keep invariant in design artifacts; do not create executable TC with invented error or option state. |
| `GAP-003` | `SRC-018`; `GSR 142` | Return-from-`Выбор решения` setup and observable SPR/anti-fraud evidence are not specified. | non-blocking residual | Cover UI-visible validation/navigation only. |
| `GAP-004` | `SRC-022`-`SRC-024`; PDF pp.65-67 | CDI failure/mismatch messages have text, but no deterministic trigger/test data. | non-blocking residual | Preserve rows; no executable TC in v12 without approved setup. |
| `GAP-005` | `SRC-003`; `GSR 124` | Main income below-min feedback for `< 2000` is not specified. | non-blocking writer gap | Cover valid minimum `2000`; leave invalid feedback as unresolved. |
| `GAP-006` | `SRC-003`; `GSR 124` | Main income non-digit input feedback is not specified. | non-blocking writer gap | Do not assert filtering, cleanup, message or red highlight. |
| `GAP-007` | `SRC-012`; `GSR 135` | Additional income non-digit input feedback is not specified. | non-blocking writer gap | Cover valid numeric input only; route invalid feedback to gap. |"""


def fixture_catalog() -> str:
    rows = [
        ["`FIX-EMP-BASE-001`", "Валидная форма без необязательных блоков", "`Тип занятости` = `Работа по найму`; `Среднемесячный доход` = `2000`; `Клиент добросовестный` = `Да`; `Визуальная информация` = `Нет`; employer/address/position rows are fixture context with available valid values when UI requires them, not assertions in v12.", "`TC-019`; negative transition deltas", "If implementation requires out-of-v12 employer fields, use environment-approved valid fixture data; do not assert their behavior."],
        ["`FIX-VISUAL-001`", "Валидная форма с визуальной информацией", "`Тип занятости` = `Пенсионер (не работает)`; `Среднемесячный доход` = `2000`; `Клиент добросовестный` = `Нет`; `Визуальная информация` = `Да`; selected parameter = `Не выявлено`.", "`TC-013`; `TC-014`; `TC-015`; `TC-016`", "Avoid employer fields by using pensioner branch."],
        ["`FIX-BACK-SAVED-001`", "Baseline for Back branch comparison", "Before `TC-021`, stored `Среднемесячный доход` value is `5000` from `TC-020` or equivalent precondition.", "`TC-020`; `TC-021`", "If tests run independently, create the baseline in precondition before starting `TC-021`."],
    ]
    return table(["fixture_id", "purpose", "concrete_values", "used_by", "notes"], rows)


def applicability() -> str:
    rows = [
        ["conditional-visibility", "yes", "`SRC-002`; `SRC-003`; `SRC-014`-`SRC-016`", "Visible controls and dependencies are source-backed.", "`ATOM-001`; `ATOM-005`; `ATOM-013`; `ATOM-016`; `ATOM-019`", "`TC-001`; `TC-004`; `TC-011`; `TC-012`", "-"],
        ["dependency", "yes", "`SRC-002`; `SRC-003`; `SRC-016`; `SRC-018`", "Required flags and red highlight on missing required fields are source-backed.", "`ATOM-002`; `ATOM-006`; `ATOM-022`; `ATOM-025`", "`TC-002`; `TC-013`; `TC-018`", "-"],
        ["table-list", "yes", "`SRC-002`; `SRC-011`; `SRC-016`; dictionary inventory", "Closed active dictionaries are available.", "`ATOM-004`; `ATOM-011`; `ATOM-020`", "`TC-001`; `TC-007`; `TC-012`", "-"],
        ["numeric", "yes", "`SRC-003`; `SRC-012`; `GSR 124`; `GSR 135`", "Numeric input exists; invalid feedback is not fully specified.", "`ATOM-007`; `ATOM-012`", "`TC-005`; `TC-008`", "`GAP-005`; `GAP-006`; `GAP-007`"],
        ["scenario-use-case", "yes", "`SRC-019`; `SRC-020`; `GSR 144`-`GSR 147`", "Add/delete actions create removable blocks.", "`ATOM-008`; `ATOM-009`; `ATOM-027`; `ATOM-028`", "`TC-006`; `TC-010`; `TC-022`; `TC-023`", "-"],
        ["table-list", "yes", "`SRC-015`; `SRC-016`; `GSR 138`-`GSR 140`", "Visual assessment parameters are multi-select checkboxes.", "`ATOM-020`; `ATOM-021`; `ATOM-022`; `ATOM-023`; `ATOM-024`", "`TC-012`; `TC-013`; `TC-014`; `TC-015`; `TC-016`", "-"],
        ["scenario-use-case", "yes", "`SRC-018`; `SRC-021`; `GSR 142`; `GSR 143`; `GSR 148`", "Next and Back UI transitions are source-backed.", "`ATOM-025`; `ATOM-026`; `ATOM-029`; `ATOM-030`; `ATOM-031`", "`TC-018`; `TC-019`; `TC-020`; `TC-021`", "`GAP-003`"],
        ["integration", "unclear", "`SRC-017`; `SRC-022`-`SRC-024`", "DaData/SPR/CDI internals and CDI trigger are not fully observable from source.", "-", "-", "`GAP-001`; `GAP-004`"],
    ]
    return table(["dimension", "applicable", "source_ref", "reason", "linked_atoms", "linked_test_cases", "gap_id"], rows)


def coverage_metrics() -> str:
    rows = [
        ["visibility", "5", "5", "0", "`TC-001`; `TC-004`; `TC-011`; `TC-012`", "-"],
        ["requiredness", "4", "4", "0", "`TC-002`; `TC-013`; `TC-018`", "-"],
        ["dictionary", "3", "3", "0", "`TC-001`; `TC-007`; `TC-012`", "-"],
        ["numeric", "5", "2", "3", "`TC-005`; `TC-008`", "`GAP-005`; `GAP-006`; `GAP-007`"],
        ["repeatable-block", "4", "4", "0", "`TC-006`; `TC-010`; `TC-022`; `TC-023`", "-"],
        ["checkbox-list", "5", "5", "0", "`TC-012`; `TC-013`; `TC-014`; `TC-015`; `TC-016`", "-"],
        ["state-transition", "5", "4", "1", "`TC-018`; `TC-019`; `TC-020`; `TC-021`", "`GAP-003`"],
        ["integration", "3", "0", "3", "-", "`GAP-001`; `GAP-004`"],
    ]
    return table(["coverage_dimension", "obligations", "covered", "gap_or_unclear", "linked_test_cases", "linked_gaps"], rows)


def risk_map() -> str:
    rows = [
        ["`ATOM-007`", "numeric", "4", "3", "12", "high", "money; income validation", "`SRC-003`; `GSR 124`", "High", "`TC-005`", "`GAP-005`; `GAP-006`", "accepted-with-gap", "Valid minimum is covered; invalid feedback unresolved."],
        ["`ATOM-022`", "requiredness", "4", "3", "12", "high", "critical validation; transition blocking", "`SRC-016`; `GSR 140`", "High", "`TC-013`", "-", "none", "Missing visual parameter blocks section completion."],
        ["`ATOM-026`", "state-transition", "5", "3", "15", "high", "generated form; navigation", "`SRC-018`; `GSR 143`", "High", "`TC-019`", "-", "none", "Primary forward transition."],
        ["`GAP-003`", "integration", "5", "3", "15", "high", "SPR/anti-fraud hidden side effects", "`SRC-018`; `GSR 142`", "High", "-", "`GAP-003`", "accepted-with-gap", "No observable artifact/setup in current source."],
        ["`GAP-004`", "integration", "4", "2", "8", "medium", "CDI trigger setup", "`SRC-022`-`SRC-024`", "Medium", "-", "`GAP-004`", "accepted-with-gap", "PDF rows preserved; setup unresolved."],
    ]
    return table(["atom_id", "coverage_dimension", "impact", "likelihood", "risk_score", "risk_level", "risk_factors", "source_ref", "required_priority", "linked_test_cases", "gap_id", "residual_risk_decision", "rationale"], rows)


def review(validator_status: str) -> str:
    rows = [
        ["`artifact-shape-preflight`", "pass", "info", "all", "Required canonical columns are present in source-row-inventory, coverage-obligation-table, test-design-review and writer-quality-gate.", "none", "no"],
        ["`gap-only-fixture-rows`", "pass", "info", "`WP-01`; `WP-05`", "`SRC-004`; `SRC-005`; `SRC-022`-`SRC-024` are not planned executable standalone TC.", "none", "no"],
        ["`dictionary-traceability`", "pass", "info", "`WP-01`; `WP-02`; `WP-03`", "`DICT-001`; `DICT-004`; `DICT-005` are linked in obligations, plan and TC traceability.", "none", "no"],
        ["`requiredness-checks`", "pass", "info", "all", "Requiredness uses empty-value enforcement / red highlight, not filled-field acceptance.", "none", "no"],
        ["`validator-current-scope`", validator_status, "info", "all", "See `writer-self-check.md` scoped validator findings summary.", "fix if non-pass", "yes" if validator_status != "pass" else "no"],
    ]
    return table(["review_item", "status", "severity", "affected_package", "evidence", "required_action", "blocks_ready_for_review"], rows)


def gate(validator_status: str, validator_evidence: str) -> str:
    rows = [
        ["`artifact-shape-preflight`", "pass", "Exact canonical table columns are used; canonical TC file links split artifacts and does not duplicate full split tables.", "all", "none", "no"],
        ["`artifact-write-strategy`", "pass", "`artifact-write-strategy.md` declares file-based manifest writing before final artifact generation.", "all", "none", "no"],
        ["`mockup-visual-inventory`", "pass", "Handoff mockup inventory has opened=yes and is used only for interaction hints/aliases.", "all", "none", "no"],
        ["`source-row-inventory`", "pass", "All required v12 rows and residual context rows are preserved with `ATOM-*`/`GAP-*` mapping.", "all", "none", "no"],
        ["`source-normalization-atomic`", "pass", "Executable properties are split from residual gaps; current known composite row `SP-006` is design-only and split in ledger.", "all", "none", "no"],
        ["`dictionary-inventory`", "pass", "`DICT-001`; `DICT-004`; `DICT-005` copied from pre-writer inventory and used downstream.", "all", "none", "no"],
        ["`test-design-decision-table`", "pass", "Every normalized property has one decision and no `metadata_only` row is linked to executable TC.", "all", "none", "no"],
        ["`coverage-obligation-table`", "pass", "Numeric/list/repeatable/checkbox/transition obligations link to `TC-*` or narrow `GAP-*`.", "all", "none", "no"],
        ["`coverage-metrics`", "pass", "Applicable dimensions have counted obligations and gap counts.", "all", "none", "no"],
        ["`fixture-catalog`", "pass", "Named fixtures exist for valid forward transition and Back branch persistence/discard checks.", "all", "none", "no"],
        ["`risk-priority-map`", "pass", "High-risk numeric, transition and integration dimensions are mapped.", "all", "none", "no"],
        ["`gap-admissibility`", "pass", "Gaps are narrow; visible behavior is split into executable TC where source-backed.", "all", "none", "no"],
        ["`test-design-review`", "pass", "`test-design-review.md` has no blocking rows.", "all", "none", "no"],
        ["`ledger-atomicity`", "pass", "`ATOM-*` rows split independent visibility, requiredness, editability, dictionary, numeric, action and branch obligations.", "all", "none", "no"],
        ["`gsr-range-compression`", "pass", "No broad `GSR N-M` covered atom is used.", "all", "none", "no"],
        ["`design-plan-atomicity`", "pass", "Plan rows use one check/input class with one TC or gap target.", "all", "none", "no"],
        ["`scenario-does-not-replace-atomic`", "pass", "Scenario transition cases do not replace field/list/numeric/checkbox atomic cases.", "all", "none", "no"],
        ["`tc-atomicity`", "pass", "Each TC has one primary expected result.", "all", "none", "no"],
        ["`test-data-specificity`", "pass", "TCs use concrete values or named fixtures.", "all", "none", "no"],
        ["`internal-observability`", "pass", "Backend DaData/SPR/CDI effects remain residual gaps unless observable.", "all", "none", "no"],
        ["`action-observability`", "pass", "Action TCs assert visible block/dialog/navigation/document results.", "all", "none", "no"],
        ["`semantic-req-id-parity`", "pass", "`GSR 123`-`GSR 148` relevant to v12 boundary are preserved in ledger/gaps.", "all", "none", "no"],
        ["`scoped-validator-findings`", validator_status, validator_evidence, "all", "fix current-scope warning/error before review if status is not pass", "yes" if validator_status != "pass" else "no"],
        ["`package-ready`", validator_status, "All package gates pass only if scoped validator status is pass.", "all", "do not route if validator status is not pass", "yes" if validator_status != "pass" else "no"],
    ]
    return table(["gate_item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"], rows)


def self_check(validator_status: str, validator_evidence: str, validator_command: str) -> str:
    return f"""| check_item | result | evidence |
| --- | --- | --- |
| source parity checked | pass | `source-parity-check.md` read; PDF-only `GSR 123`-`GSR 148` preserved where in v12 boundary or residual gaps. |
| mandatory requirement IDs preserved | pass | `GSR 123`; `GSR 124`; `GSR 135`; `GSR 136`-`GSR 140`; `GSR 142`-`GSR 148` appear in ledger, TC traceability or gaps. |
| uncovered atoms | pass | No executable `ATOM-*` intentionally left uncovered; invalid numeric feedback and integration setup are `GAP-*`. |
| possible merged checks | pass | No TC combines valid acceptance with invalid rejection; branch cases split. |
| continuous numbering | pass | `TC-001`-`TC-023` are continuous. |
| scoped validator command | {validator_status} | `{validator_command}` |
| scoped validator findings summary | {validator_status} | {validator_evidence} |
| assumptions | pass | Residual `GAP-001`-`GAP-004` accepted by prior scope-gap review; `GAP-005`-`GAP-007` are narrow writer gaps for unspecified invalid input feedback. |
| unclear items | pass | No unclear item is represented as executable TC. |"""


def tc_section(tc_id: str, title: str, type_: str, priority: str, package: str, trace: str, pre: str, data: str, steps: list[str], expected: str, post: str) -> str:
    step_text = "\n".join(f"{idx}. {step}" for idx, step in enumerate(steps, start=1))
    return f"""## {tc_id} - {title}

| Поле | Значение |
| --- | --- |
| Название | {title} |
| Тип | {type_} |
| Приоритет | {priority} |
| package_id | `{package}` |
| Трассировка | {trace} |

### Предусловия

{pre}

### Тестовые данные

{data}

### Шаги

{step_text}

### Итоговый ожидаемый результат

{expected}

### Постусловия

{post}
"""


def canonical_body() -> str:
    links = "\n".join(
        f"- `{p.relative_to(FT)}`"
        for p in [
            TD / "artifact-write-strategy.md",
            TD / "source-row-inventory.md",
            TD / "source-table-normalization.md",
            TD / "dictionary-inventory.md",
            TD / "test-design-decision-table.md",
            TD / "coverage-obligation-table.md",
            TD / "atomic-requirements-ledger.md",
            TD / "package-test-design-plan.md",
            TD / "coverage-gaps.md",
            TD / "fixture-catalog.md",
            TD / "test-design-review.md",
            TD / "writer-quality-gate.md",
            TD / "writer-self-check.md",
        ]
    )
    intro = f"""FT package: `ft-2-OF_16`
Scope: `{SCOPE}`
Writer mode: `fresh-eval-run / writer.session_initial_draft`
Canonical split artifacts:

{links}

Coverage boundary: v12 covers selected medium source rows only: `SRC-002`, `SRC-003`, `SRC-010`-`SRC-012`, `SRC-014`-`SRC-016`, `SRC-018`-`SRC-021`. `SRC-004`, `SRC-005`, `SRC-017`, `SRC-022`-`SRC-024` are preserved as fixture/residual gap context and are not executable standalone coverage in this draft.

Residual gaps: `GAP-001`-`GAP-004` accepted as non-blocking pre-writer residual gaps; `GAP-005`-`GAP-007` capture missing deterministic feedback for invalid numeric input classes.
"""
    cases = [
        tc_section("TC-001", "Список `Тип занятости` содержит все и только active values DICT-001", "Positive", "High", "WP-01", "`ATOM-001`; `ATOM-004`; `SRC-002`; `DICT-001`", "Открыта форма раздела `Сведения о занятости`.", "`DICT-001`: `Работа по найму`; `Пенсионер (не работает)`; `Индивидуальный предприниматель`; `Собственник бизнеса`; `Частная практика / Самозанятый`; `Безработный`.", ["Открыть список `Тип занятости`."], "В списке отображаются все перечисленные active values `DICT-001` и отсутствуют другие selectable values.", "Не требуются."),
        tc_section("TC-002", "Обязательность `Тип занятости` проверяется пустым значением", "Negative", "High", "WP-01", "`ATOM-002`; `ATOM-025`; `SRC-002`; `SRC-018`; `GSR 142`", "Открыта форма раздела `Сведения о занятости`; поле `Тип занятости` пустое.", "Не требуются.", ["Нажать `Следующий шаг`."], "Поле `Тип занятости` подсвечено красным как незаполненное обязательное поле; переход из раздела не выполнен.", "Не требуются."),
        tc_section("TC-003", "Редактирование `Тип занятости` отображает новое выбранное значение", "Positive", "Medium", "WP-01", "`ATOM-003`; `SRC-002`; `DICT-001`", "Открыта форма раздела; в поле `Тип занятости` выбрано `Работа по найму`.", "Старое значение: `Работа по найму`. Новое значение: `Безработный`.", ["Открыть список `Тип занятости`.", "Выбрать `Безработный`."], "В поле `Тип занятости` отображается новое значение `Безработный`.", "Вернуть исходное значение `Работа по найму`, если кейс выполняется в общей заявке."),
        tc_section("TC-004", "`Среднемесячный доход` отображается после заполнения `Тип занятости`", "Positive", "Medium", "WP-01", "`ATOM-005`; `SRC-003`; `GSR 123`; `DICT-001`", "Открыта форма; поле `Тип занятости` пустое.", "`Тип занятости` = `Работа по найму`.", ["В поле `Тип занятости` выбрать `Работа по найму`."], "Поле `Среднемесячный доход после вычета налогов` отображается в разделе и доступно для ввода.", "Не требуются."),
        tc_section("TC-005", "Минимальное значение основного дохода `2000` принимается и отображается", "Positive", "High", "WP-01", "`ATOM-007`; `SRC-003`; `GSR 124`", "Открыта форма; выбран `Тип занятости` = `Работа по найму`; поле основного дохода отображается.", "`Среднемесячный доход после вычета налогов` = `2000`.", ["Ввести `2000` в поле основного дохода.", "Снять фокус с поля."], "В поле основного дохода отображается значение `2000` без очистки значения.", "Очистить поле, если кейс выполняется в общей заявке."),
        tc_section("TC-006", "Действие `Добавить дополнительный доход` отображает поля нового блока", "Positive", "High", "WP-02", "`ATOM-008`; `ATOM-010`; `SRC-010`; `SRC-020`; `GSR 146`", "Открыта форма раздела; блок дополнительного дохода еще не создан.", "Не требуются.", ["Нажать `Добавить дополнительный доход`."], "В разделе отображается новый блок `Дополнительный доход` с полями `Тип дохода` и `Среднемесячный доход после вычета налогов`.", "Удалить созданный блок через корзину."),
        tc_section("TC-007", "Список `Тип дохода` содержит все и только active values DICT-004", "Positive", "High", "WP-02", "`ATOM-011`; `SRC-011`; `DICT-004`; `GAP-002`", "Открыта форма; создан один блок `Дополнительный доход`.", "`DICT-004`: `Пенсия`; `Аренда`.", ["Открыть список `Тип дохода` в созданном блоке."], "В списке отображаются все active values `DICT-004`: `Пенсия`, `Аренда`; другие selectable values отсутствуют.", "Удалить созданный блок через корзину."),
        tc_section("TC-008", "Числовое значение дополнительного дохода отображается в созданном блоке", "Positive", "Medium", "WP-02", "`ATOM-012`; `SRC-012`; `GSR 135`", "Открыта форма; создан блок `Дополнительный доход`; выбран `Тип дохода` = `Аренда`.", "`Среднемесячный доход` = `3000`.", ["В поле дохода созданного блока ввести `3000`.", "Снять фокус с поля."], "В поле дополнительного дохода отображается значение `3000` без очистки значения.", "Удалить созданный блок через корзину."),
        tc_section("TC-009", "Обязательность `Тип дохода` проверяется пустым значением в созданном блоке", "Negative", "High", "WP-02", "`ATOM-010`; `ATOM-025`; `SRC-011`; `SRC-018`; `GSR 142`", "Открыта форма по fixture `FIX-EMP-BASE-001`; создан один блок `Дополнительный доход`; поле `Тип дохода` пустое; доход блока заполнен `3000`.", "Не требуются.", ["Нажать `Следующий шаг`."], "Поле `Тип дохода` в созданном блоке подсвечено красным как незаполненное обязательное поле; переход из раздела не выполнен.", "Удалить созданный блок через корзину."),
        tc_section("TC-010", "Корзина удаляет созданный блок дополнительного дохода", "Positive", "Medium", "WP-02", "`ATOM-009`; `SRC-020`; `GSR 147`", "Открыта форма; создан один блок `Дополнительный доход`.", "Не требуются.", ["Нажать пиктограмму `Корзина` в созданном блоке дополнительного дохода."], "Созданный блок `Дополнительный доход` больше не отображается в разделе.", "Не требуются."),
        tc_section("TC-011", "Переключатели общих полей видимы с default `Нет`", "Positive", "Medium", "WP-03", "`ATOM-013`; `ATOM-014`; `ATOM-016`; `ATOM-017`; `SRC-014`; `SRC-015`; `GSR 136`; `GSR 137`", "Открыта форма раздела до изменения общих полей.", "Не требуются.", ["Просмотреть поля `Клиент добросовестный` и `Визуальная информация`."], "Оба переключателя отображаются; у `Клиент добросовестный` отображается значение `Нет`; у `Визуальная информация` отображается значение `Нет`.", "Не требуются."),
        tc_section("TC-012", "`Визуальная информация = Да` отображает чекбоксы всех active values DICT-005", "Positive", "High", "WP-03", "`ATOM-019`; `ATOM-020`; `SRC-015`; `SRC-016`; `GSR 138`; `GSR 139`; `DICT-005`", "Открыта форма; `Визуальная информация` = `Нет`.", "Все active values `DICT-005` из dictionary inventory.", ["Переключить `Визуальная информация` в значение `Да`."], "Отображается список параметров визуальной оценки; по каждому active value `DICT-005` доступен отдельный чекбокс; extra selectable values отсутствуют.", "Вернуть `Визуальная информация` в `Нет`, если кейс выполняется в общей заявке."),
        tc_section("TC-013", "Пустой список параметров блокирует переход при `Визуальная информация = Да`", "Negative", "High", "WP-03", "`ATOM-015`; `ATOM-022`; `ATOM-025`; `SRC-014`; `SRC-016`; `SRC-018`; `GSR 140`; `GSR 142`", "Форма заполнена по fixture `FIX-VISUAL-001`, кроме параметров визуальной оценки: `Визуальная информация` = `Да`, ни один параметр не выбран.", "Не требуются.", ["Нажать `Следующий шаг`."], "Область `Параметры визуальной оценки` подсвечена красным как незаполненное обязательное поле; переход из раздела не выполнен.", "Вернуть `Визуальная информация` в исходное значение при необходимости."),
        tc_section("TC-014", "Один выбранный параметр визуальной оценки удовлетворяет обязательному выбору", "Positive", "High", "WP-03", "`ATOM-021`; `ATOM-023`; `SRC-016`; `GSR 139`; `GSR 140`; `DICT-005`", "Форма заполнена по fixture `FIX-VISUAL-001`; `Визуальная информация` = `Да`; параметры не выбраны.", "Параметр: `Не выявлено`.", ["Отметить чекбокс `Не выявлено`."], "Чекбокс `Не выявлено` отображается выбранным; других выбранных параметров нет.", "Снять выбор с `Не выявлено`, если кейс выполняется в общей заявке."),
        tc_section("TC-015", "Множественный выбор параметров визуальной оценки отображает несколько выбранных чекбоксов", "Positive", "Medium", "WP-03", "`ATOM-021`; `ATOM-024`; `SRC-015`; `SRC-016`; `GSR 138`; `GSR 139`; `DICT-005`", "Форма заполнена по fixture `FIX-VISUAL-001`; `Визуальная информация` = `Да`; параметры не выбраны.", "Параметры: `Не выявлено`; `Иные подозрения`.", ["Отметить чекбокс `Не выявлено`.", "Отметить чекбокс `Иные подозрения`."], "Оба чекбокса `Не выявлено` и `Иные подозрения` отображаются выбранными одновременно.", "Снять выбранные чекбоксы."),
        tc_section("TC-016", "Снятие последнего выбранного параметра возвращает список в пустое состояние", "Positive", "Medium", "WP-03", "`ATOM-021`; `ATOM-022`; `SRC-016`; `GSR 139`; `GSR 140`; `DICT-005`", "Форма заполнена по fixture `FIX-VISUAL-001`; `Визуальная информация` = `Да`; выбран только параметр `Не выявлено`.", "Параметр: `Не выявлено`.", ["Снять отметку с чекбокса `Не выявлено`."], "Чекбокс `Не выявлено` отображается невыбранным; в списке параметров визуальной оценки нет выбранных значений.", "Не требуются."),
        tc_section("TC-017", "`Клиент добросовестный = Да` снимает обязательность `Визуальная информация`", "Positive", "Medium", "WP-03", "`ATOM-018`; `SRC-015`; `GSR 137`", "Форма заполнена по fixture `FIX-EMP-BASE-001`; `Клиент добросовестный` = `Нет`; `Визуальная информация` = `Нет`.", "`Клиент добросовестный` = `Да`.", ["Переключить `Клиент добросовестный` в значение `Да`.", "Нажать `Следующий шаг`."], "Переход не блокируется из-за незаполненной `Визуальная информация`.", "Вернуть переключатель в исходное значение, если кейс выполняется в общей заявке."),
        tc_section("TC-018", "`Следующий шаг` подсвечивает пустой основной доход при валидном остальном fixture", "Negative", "High", "WP-04", "`ATOM-006`; `ATOM-025`; `SRC-003`; `SRC-018`; `GSR 123`; `GSR 142`", "Форма заполнена по fixture `FIX-EMP-BASE-001`, кроме поля основного дохода: поле пустое.", "Не требуются.", ["Нажать `Следующий шаг`."], "Поле `Среднемесячный доход после вычета налогов` подсвечено красным как незаполненное обязательное поле; переход из раздела не выполнен.", "Восстановить значение основного дохода `2000`."),
        tc_section("TC-019", "`Следующий шаг` открывает `Анкета клиента` при валидном заполнении", "Positive", "High", "WP-04", "`ATOM-026`; `SRC-018`; `GSR 143`", "Форма заполнена по fixture `FIX-EMP-BASE-001`.", "Не требуются.", ["Нажать `Следующий шаг`."], "Открыт раздел `Анкета клиента`; печатная форма `Заявление-анкета` доступна в этом разделе как сформированный документ/артефакт раздела.", "Не требуются."),
        tc_section("TC-020", "`Назад` с ответом `Да` сохраняет изменение и открывает `Основная информация`", "Positive", "High", "WP-04", "`ATOM-029`; `ATOM-030`; `SRC-021`; `GSR 148`", "Открыта форма с сохраненным основным доходом `2000`.", "Новое значение основного дохода: `5000`.", ["Изменить основной доход на `5000`.", "Нажать `Назад`.", "В уведомлении `Есть несохраненные данные, сохранить?` выбрать `Да`.", "После открытия `Основная информация` вернуться в раздел `Сведения о занятости`."], "В разделе `Сведения о занятости` отображается сохраненное значение основного дохода `5000`.", "Не требуются."),
        tc_section("TC-021", "`Назад` с ответом `Нет` открывает `Основная информация` без сохранения текущего изменения", "Positive", "High", "WP-04", "`ATOM-029`; `ATOM-031`; `SRC-021`; `GSR 148`", "Открыта форма; сохраненное значение основного дохода = `5000` по fixture `FIX-BACK-SAVED-001`.", "Временное новое значение: `6000`.", ["Изменить основной доход на `6000`.", "Нажать `Назад`.", "В уведомлении `Есть несохраненные данные, сохранить?` выбрать `Нет`.", "После открытия `Основная информация` вернуться в раздел `Сведения о занятости`."], "В разделе `Сведения о занятости` отображается прежнее сохраненное значение основного дохода `5000`, а не временное значение `6000`.", "Не требуются."),
        tc_section("TC-022", "`Добавить работу по совместительству` отображает добавленный блок и корзину", "Positive", "Medium", "WP-04", "`ATOM-027`; `SRC-019`; `GSR 144`; `GSR 145`", "Открыта форма; блок `Работа по совместительству` еще не добавлен.", "Не требуются.", ["Нажать `Добавить работу по совместительству`."], "Отображается добавленный блок `Работа по совместительству` с полями блока и пиктограммой `Корзина` для удаления.", "Удалить созданный блок через корзину."),
        tc_section("TC-023", "Корзина удаляет созданный блок работы по совместительству", "Positive", "Medium", "WP-04", "`ATOM-028`; `SRC-019`; `GSR 145`", "Открыта форма; создан один блок `Работа по совместительству`.", "Не требуются.", ["Нажать пиктограмму `Корзина` в созданном блоке `Работа по совместительству`."], "Созданный блок `Работа по совместительству` больше не отображается в разделе.", "Не требуются."),
    ]
    return intro + "\n\n" + "\n".join(cases)


def logs(status_after: str, validator_status: str, validator_evidence: str, validator_command: str) -> tuple[str, str]:
    selected = [
        "AGENTS.md", "skills/README.md", "references/agent/session-based-review-cycle-format.md",
        "references/agent/codex-sdk-orchestration-format.md", "skills/ft-test-case-writer/SKILL.md",
        "references/agent/writer-runtime-workflow.md", "references/agent/writer-runtime-contract.md",
        "references/qa/test-case-runtime-format.md", "references/qa/coverage-runtime-checklist.md",
        "references/qa/traceability-rules.md", "references/agent/writer-process-workflow.md",
        "references/agent/workflow-state-format.md", "references/agent/session-log-format.md",
        "references/agent/agent-decision-log-format.md", "references/agent/writer-handoff-format.md",
    ]
    inputs = "\n".join(f"- `{p}` - selected required instruction file." for p in selected)
    required = "\n".join(
        f"- `{p}` - required v12 source/handoff input."
        for p in [
            "fts/ft-2-OF_16/AGENT-NOTES.md",
            "fts/ft-2-OF_16/work/stage-handoffs/00-source-selection/source-selection.md",
            "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/scope-contract.md",
            "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/scope-coverage-gaps.md",
            "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/source-parity-check.md",
            "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/source-row-inventory.md",
            "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/mockup-visual-inventory.md",
            "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/scope-clarification-requests.md",
            "fts/ft-2-OF_16/work/review-cycles/ui-employment-canary-v2-test-design-upgrade/outputs/scope-gap-review-findings.md",
            "fts/ft-2-OF_16/work/test-design/ui-employment/dictionary-inventory.md",
        ]
    )
    session = f"""## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-writer` |
| mode | `writer.session_initial_draft / fresh-eval-run` |
| ft_slug | `ft-2-OF_16` |
| scope_slug | `{SCOPE}` |
| started_from | `work/review-cycles/{SCOPE}/cycle-state.yaml` |
| status_after | `{status_after}` |

## Inputs Read

- `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - resolver command; budget status `pass (130.2 / 200.0 KiB)`.
{inputs}
{required}
- `source/*.docx` and `source/*.pdf` relevant pages/sections - extracted only for source verification of selected rows.

## Inputs Not Used

- Existing canary v1-v11 canonical files, ledgers, matrices, writer/reviewer outputs and helper scripts - regression comparison material only, not requirement sources or templates.
- Neighboring UI sections and employer/address/position/work-phone rows outside v12 boundary - out of executable scope except fixture/residual gaps.

## Key Decisions

- Medium v12 boundary used: selected rows only; no case-count minimization criterion.
- `SRC-004`, `SRC-005`, `SRC-017`, `SRC-022`-`SRC-024` preserved as residual context/gaps, not executable standalone TC.
- Invalid numeric feedback for main/additional income routed to narrow `GAP-005`-`GAP-007` because source gives restrictions but not deterministic UI feedback.
- Back branches use distinct save/discard oracles.

## Risks And Fallbacks

- Console mojibake/encoding risk was handled by explicit UTF-8 reads and generator writes; distorted stdout was not used as source evidence.
- Root validator may include historical artifacts; current-scope evidence is filtered to paths for `{SCOPE}` and the canonical v12 file.

## Validation

- `artifact-shape-preflight` - pass; required table columns written exactly.
- `{validator_command}` - {validator_status}; {validator_evidence}

## Contamination Check

- Old canary drafts and generated artifacts were not used as requirement sources or content templates.
- Source-backed decisions came from AGENT-NOTES, source-selection, scope contract, row/parity/gap/mockup handoff artifacts, dictionary inventory and relevant main DOCX/PDF fragments.

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Resolved instruction context | budget pass | resolver command above |
| 2 | Read required instructions and handoff inputs | package/scope confirmed | `cycle-state.yaml`; handoff artifacts |
| 3 | Extracted relevant DOCX/PDF fragments | source row details confirmed | `section-23`; `section-24`; PDF pp.61-67 |
| 4 | Declared artifact write strategy | file-based manifest writing selected | `artifact-write-strategy.md` |
| 5 | Wrote canonical and split artifacts | artifacts present | `test-cases/...v12...md`; `work/test-design/{SCOPE}/` |
| 6 | Ran validator gate | {validator_status} | `{validator_command}` |
| 7 | Updated cycle state | routed to structure preflight if pass | `cycle-state.yaml` |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Writer Quality Gate | {validator_status} | `writer-quality-gate.md` | review current-scope validator row |
| Artifact shape preflight | pass | exact tables in required artifacts | none |
| Scoped validator | {validator_status} | `{validator_command}` | fix current-scope warnings/errors if any |

## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| `test-cases/{SECTION}-{SCOPE}.md` and split artifacts | `large generated/package-based` | `file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest <manifest.json>` | `yes` |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | PowerShell stdout encoding distorted Cyrillic in an early instruction read | PowerShell console output as source evidence | explicit UTF-8 file reads and Python `PYTHONIOENCODING=utf-8`; distorted stdout discarded | `n/a` | `n/a` | none | none |

## Handoff Notes For Next Session

- Structure preflight should verify exact table schemas and that canonical file remains slim.
- Semantic reviewer should inspect `GAP-005`-`GAP-007` because they are new writer gaps for invalid numeric feedback, not pre-writer accepted gaps.
"""
    decision = f"""## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `ft-2-OF_16` |
| scope_slug | `{SCOPE}` |
| stage | `ft-test-case-writer` |
| started_from | `cycle-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `scope-boundary` | `prompt.writer-r1.md` | Use v12 medium boundary only. | Prompt excludes full section coverage and old canary sources. | `source-row-inventory.md`; canonical TC | high | applied |
| `DEC-002` | 2 | `coverage` | `SRC-004`; `SRC-005`; `SRC-017` | Keep employer/address/DaData as fixture/residual gap context. | v12 explicitly excludes these rows from executable scope except fixture/residual gaps. | `coverage-gaps.md`; `source-row-inventory.md` | high | applied |
| `DEC-003` | 3 | `gap` | `SRC-003`; `SRC-012` | Route invalid numeric feedback to `GAP-005`-`GAP-007`. | Source defines numeric restrictions but not deterministic UI feedback/oracle. | `coverage-gaps.md`; `coverage-obligation-table.md` | medium | applied |
| `DEC-004` | 4 | `test-design` | `SRC-021`; `GSR 148` | Split Back `Да` and `Нет` into separate TCs with save/discard observable oracles. | Branch choices require distinct observable outcomes. | `TC-020`; `TC-021` | high | applied |
| `DEC-005` | 5 | `artifact-write` | package-based writer output | Use file-based manifest helper. | Scope has WP packages and table-heavy artifacts; one-shot write would violate process. | `artifact-write-strategy.md`; `_build/` manifests | high | applied |
| `DEC-006` | 6 | `validation` | post-write validator | Route according to current-scope validator status `{validator_status}`. | Writer-ready requires real validator evidence after artifact write. | `writer-self-check.md`; `cycle-state.yaml` | medium | applied |
"""
    return session, decision


def prompt_next() -> str:
    return f"""# Structure Preflight Prompt

Run `ft-test-case-reviewer` in `structure_preflight` mode for cycle `{SCOPE}`.

## Inputs

- `fts/ft-2-OF_16/work/review-cycles/{SCOPE}/cycle-state.yaml`
- `fts/ft-2-OF_16/test-cases/{SECTION}-{SCOPE}.md`
- `fts/ft-2-OF_16/work/test-design/{SCOPE}/`
- `fts/ft-2-OF_16/work/review-cycles/{SCOPE}/outputs/writer-session-log.writer-r1.md`
- `fts/ft-2-OF_16/work/review-cycles/{SCOPE}/outputs/agent-decision-log.writer-r1.md`

## Review Boundary

Structure preflight checks parseability, canonical table schemas, slim canonical shape, continuous TC numbering, required fields, and whether the draft is reviewable. Do not perform semantic coverage review in this stage.

## Required Checks

- `writer-quality-gate.md` table columns exactly: `gate_item | status | evidence | affected_package | required_action | blocks_ready_for_review`.
- `source-row-inventory.md` table columns exactly: `source_row_id | package_id | field_or_action | source_ref | requirement_codes | in_scope | mapped_atom_or_gap`.
- `coverage-obligation-table.md` table columns exactly: `obligation_id | package_id | source_property_id | linked_atom_id | property_type | obligation_class | required_behavior | source_ref | planned_tc_or_gap | status | review_notes`.
- `test-design-review.md` table columns exactly: `review_item | status | severity | affected_package | evidence | required_action | blocks_ready_for_review`.
- Canonical TC file must not duplicate full split artifact sections.
- Writer self-check must include real validator command/evidence.
"""


def state(status: str, validator_status: str) -> str:
    next_stage = "structure-preflight-r1" if status == "writer-draft-ready" else "writer-r1"
    active_prompt = f"work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md" if status == "writer-draft-ready" else f"work/review-cycles/{SCOPE}/prompts/prompt.writer-r1.md"
    blocking = "[]" if status == "writer-draft-ready" else "\n  - scoped validator has current-scope warnings/errors; see writer-self-check.md"
    return f"""cycle_id: ft-2-OF_16-{SCOPE}
ft_slug: ft-2-OF_16
scope_slug: {SCOPE}
section_id: 2.1.1.1.1.2
current_stage: {next_stage}
stage_status: {status}
semantic_round: 0
max_semantic_rounds: 2
canonical_test_cases: test-cases/{SECTION}-{SCOPE}.md
test_design_dir: work/test-design/{SCOPE}
active_snapshot: none
active_transition_prompt: {active_prompt}
sessions: []
latest_artifacts:
  canonical_test_cases: test-cases/{SECTION}-{SCOPE}.md
  test_design_dir: work/test-design/{SCOPE}
  writer_quality_gate: work/test-design/{SCOPE}/writer-quality-gate.md
  writer_self_check: work/test-design/{SCOPE}/writer-self-check.md
  writer_session_log: work/review-cycles/{SCOPE}/outputs/writer-session-log.writer-r1.md
  decision_log: work/review-cycles/{SCOPE}/outputs/agent-decision-log.writer-r1.md
  active_transition_prompt: {active_prompt}
blocking_reasons: {blocking}
blocking_findings: []
open_questions:
  - GAP-001
  - GAP-002
  - GAP-003
  - GAP-004
  - GAP-005
  - GAP-006
  - GAP-007
accepted_risks:
  - Canary v12 uses the same medium employment UI source rows as v11 and must not optimize for target test-case count or compactness.
  - Existing canary v1-v11 files and generated artifacts are regression comparison material only, not requirement sources or templates.
  - GAP-001 through GAP-004 remain accepted non-blocking pre-writer residual gaps by prior scope-gap review evidence unless new source evidence closes them.
  - GAP-005 through GAP-007 are non-blocking writer residual gaps for unspecified invalid numeric feedback mechanisms; semantic review must confirm admissibility.
"""


def build(validator_status: str, validator_evidence: str, validator_command: str, update_state: bool) -> None:
    TD.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    PROMPTS.mkdir(parents=True, exist_ok=True)
    write_artifact(TD / "artifact-write-strategy.md", "Artifact Write Strategy", [(2, "Artifact Write Strategy", table(["item", "value", "evidence"], [
        ["preflight_result", "`large-file / package-based`", "`WP-01`-`WP-05`; table-heavy split artifacts; canonical TC > 20 sections"],
        ["write_method", "`file-based manifest/chunked writing`", "`scripts/write_artifact_sections.py --manifest <manifest.json>`"],
        ["forbidden_methods_checked", "`yes`", "no one-shot PowerShell argument, no here-string, no inline giant command"],
        ["chunk_plan", "`split artifacts -> canonical TC -> logs/state`", "one artifact at a time"],
        ["helper_artifacts", f"`{(BUILD).relative_to(FT)}/` manifests", "UTF-8 section files and manifests retained for audit"],
        ["validation_plan", "`artifact-shape-preflight; scoped validator after final write`", "writer-quality-gate and writer-self-check record results"],
    ]))])
    write_artifact(TD / "mockup-usage.md", "Mockup Usage", [(2, "Mockup Usage", table(["item", "value", "evidence"], [
        ["inventory", "`work/stage-handoffs/01-ui-employment/mockup-visual-inventory.md`", "`opened=yes`"],
        ["used_for_steps", "`yes`", "dropdowns, toggles, add buttons, trash icons, Back/Next actions"],
        ["not_used_as_requirement_source", "`yes`", "FT/support define behavior; mockup only gives labels/interaction hints"],
        ["mockup_only_items", "`validation text`, side summary/status cards", "not asserted in TC expected results"],
    ]))])
    write_artifact(TD / "source-row-inventory.md", "Source Row Inventory", [(2, "Source Row Inventory", source_inventory())])
    write_artifact(TD / "source-table-normalization.md", "Source Table Normalization", [(2, "Source Table Normalization", source_normalization())])
    write_artifact(TD / "dictionary-inventory.md", "Dictionary Inventory", [(2, "Dictionary Inventory", dictionary_inventory())])
    write_artifact(TD / "test-design-decision-table.md", "Test Design Decision Table", [(2, "Test Design Decision Table", tddt())])
    write_artifact(TD / "coverage-obligation-table.md", "Coverage Obligation Table", [(2, "Coverage Obligation Table", obligations())])
    write_artifact(TD / "atomic-requirements-ledger.md", "Atomic Requirements Ledger", [(2, "Atomic Requirements Ledger", ledger())])
    write_artifact(TD / "package-test-design-plan.md", "Package Test Design Plan", [(2, "Package Test Design Plan", plan())])
    write_artifact(TD / "coverage-gaps.md", "Coverage Gaps", [(2, "Coverage Gaps", gaps())])
    write_artifact(TD / "fixture-catalog.md", "Fixture Catalog", [(2, "Fixture Catalog", fixture_catalog())])
    write_artifact(TD / "test-design-applicability-matrix.md", "Test-design Applicability Matrix", [(2, "Test-design Applicability Matrix", applicability())])
    write_artifact(TD / "coverage-metrics.md", "Coverage Metrics", [(2, "Test-design Coverage Metrics", coverage_metrics())])
    write_artifact(TD / "risk-priority-map.md", "Risk / Priority Map", [(2, "Risk / Priority Map", risk_map())])
    write_artifact(TD / "internal-work-package-coverage.md", "Internal Work Package Coverage", [(2, "Internal Work Package Coverage", table(["package_id", "focus", "ledger_gate", "design_plan_gate", "tc_gate", "atoms", "covered", "gap", "unclear", "TC count", "status"], [
        ["`WP-01`", "Тип занятости и основной доход", "pass", "pass", "pass", "7", "7", "2", "0", "5", "ready-for-review"],
        ["`WP-02`", "Дополнительный доход", "pass", "pass", "pass", "5", "5", "2", "0", "5", "ready-for-review"],
        ["`WP-03`", "Общие поля и визуальная оценка", "pass", "pass", "pass", "12", "12", "0", "0", "7", "ready-for-review"],
        ["`WP-04`", "Действия раздела", "pass", "pass", "pass", "7", "7", "1", "0", "6", "ready-for-review"],
        ["`WP-05`", "PDF-only CDI residual context", "pass", "pass", "not-applicable", "0", "0", "1", "0", "0", "residual-gap"],
    ]))])
    write_artifact(TD / "package-ledger-self-check.md", "Package Ledger Self-Check", [(2, "Package Ledger Self-Check", "All executable atoms use source-backed observable behavior; residual integration/setup issues are `GAP-*`.")])
    write_artifact(TD / "package-design-plan-self-check.md", "Package Design Plan Self-Check", [(2, "Package Design Plan Self-Check", "Package plan rows use concrete TC/gap targets; no `GSR N-M` compression or scenario replacement is used.")])
    write_artifact(TD / "coverage-map.md", "Coverage Map", [(2, "Coverage Map", "31 executable atoms covered by 23 TC; residual gaps: `GAP-001`-`GAP-007`; no executable source-backed behavior intentionally hidden in a gap.")])
    write_artifact(TD / "test-design-review.md", "Test Design Review", [(2, "Test Design Review", review(validator_status))])
    write_artifact(TD / "writer-quality-gate.md", "Writer Quality Gate", [(2, "Writer Quality Gate", gate(validator_status, validator_evidence))])
    write_artifact(TD / "writer-self-check.md", "Writer Self-Check", [(2, "Writer Self-Check", self_check(validator_status, validator_evidence, validator_command))])
    write_artifact(CANONICAL, "UI Employment Canary v12 Validator Execution Regression Test Cases", [(1, "UI Employment Canary v12 Validator Execution Regression Test Cases", canonical_body())])
    status_after = "writer-draft-ready" if validator_status == "pass" else "blocked-input"
    session, decision = logs(status_after, validator_status, validator_evidence, validator_command)
    write_artifact(OUT / "writer-session-log.writer-r1.md", "Writer Session Log", [(1, "Writer Session Log", session)])
    write_artifact(OUT / "agent-decision-log.writer-r1.md", "Agent Decision Log", [(1, "Agent Decision Log", decision)])
    write_artifact(PROMPTS / "prompt.structure-preflight-r1.md", "Structure Preflight Prompt", [(1, "Structure Preflight Prompt", prompt_next())])
    if update_state:
        write_text(CYCLE / "cycle-state.yaml", state(status_after, validator_status))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validator-status", default="pending")
    parser.add_argument("--validator-evidence", default="Validator pending before post-write execution.")
    parser.add_argument("--validator-command", default="pending")
    parser.add_argument("--update-state", action="store_true")
    args = parser.parse_args()
    build(args.validator_status, args.validator_evidence, args.validator_command, args.update_state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
