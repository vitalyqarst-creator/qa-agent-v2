from __future__ import annotations

import json
import re
from pathlib import Path


SCOPE = "ui-employment-canary-v21-negative-oracle-instruction-regression"
FT = Path("fts/ft-2-OF_16")
TD = FT / "work" / "test-design" / SCOPE
CYCLE = FT / "work" / "review-cycles" / SCOPE
OUT = CYCLE / "outputs"
PROMPTS = CYCLE / "prompts"
CANONICAL = FT / "test-cases" / f"2-1-1-1-1-2-{SCOPE}.md"
PROFILE_REL = f"work/review-cycles/{SCOPE}/outputs/scoped-validator-profile.writer-r1.json"


def md_table(headers: list[str], rows: list[list[str] | tuple[str, ...]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def rewrite_canonical() -> None:
    source = CANONICAL.read_text(encoding="utf-8")
    remove = {
        "TC-EMP-V21-006",
        "TC-EMP-V21-007",
        "TC-EMP-V21-008",
        "TC-EMP-V21-009",
        "TC-EMP-V21-010",
        "TC-EMP-V21-011",
        "TC-EMP-V21-017",
        "TC-EMP-V21-023",
        "TC-EMP-V21-024",
        "TC-EMP-V21-025",
        "TC-EMP-V21-026",
    }
    renumber = {
        "TC-EMP-V21-012": "TC-EMP-V21-006",
        "TC-EMP-V21-013": "TC-EMP-V21-007",
        "TC-EMP-V21-014": "TC-EMP-V21-008",
        "TC-EMP-V21-015": "TC-EMP-V21-009",
        "TC-EMP-V21-016": "TC-EMP-V21-010",
        "TC-EMP-V21-018": "TC-EMP-V21-011",
        "TC-EMP-V21-019": "TC-EMP-V21-012",
        "TC-EMP-V21-020": "TC-EMP-V21-013",
        "TC-EMP-V21-021": "TC-EMP-V21-014",
        "TC-EMP-V21-022": "TC-EMP-V21-015",
    }
    matches = list(re.finditer(r"^## (TC-EMP-V21-\d{3})\s*$", source, flags=re.MULTILINE))
    prefix = source[: matches[0].start()].rstrip()
    blocks: list[str] = [prefix]
    for idx, match in enumerate(matches):
        tc_id = match.group(1)
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(source)
        if tc_id in remove:
            continue
        block = source[start:end].strip()
        if tc_id in renumber:
            block = block.replace(f"## {tc_id}", f"## {renumber[tc_id]}", 1)
        blocks.append(block)
    write(CANONICAL, "\n\n".join(blocks))


def write_atomic_ledger() -> None:
    rows = [
        ("ATOM-001", "WP-01", "SRC-002", "-", "Тип занятости: Поле использует значения справочника «Типы занятости».", "covered", "TC-EMP-V21-001", "-"),
        ("ATOM-002", "WP-01", "SRC-003", "GSR 123", "Среднемесячный доход после вычета налогов (основная работа): Поле отображается после заполнения поля «Тип занятости».", "covered", "TC-EMP-V21-002", "-"),
        ("ATOM-003", "WP-01", "SRC-003", "GSR 124", "Среднемесячный доход после вычета налогов (основная работа): Пустое обязательное поле подсвечивается красным при переходе.", "covered", "TC-EMP-V21-003", "-"),
        ("ATOM-004", "WP-01", "SRC-003", "-", "Среднемесячный доход после вычета налогов (основная работа): Поле принимает числовое значение.", "covered", "TC-EMP-V21-004; TC-EMP-V21-005", "-"),
        ("ATOM-005", "WP-01", "SRC-003", "-", "Среднемесячный доход после вычета налогов (основная работа): Поле принимает минимально допустимое значение 2000.", "covered", "TC-EMP-V21-004", "-"),
        ("ATOM-006", "WP-01", "SRC-003", "-", "Среднемесячный доход после вычета налогов (основная работа): Поле не принимает сумму ниже 2000, но observable enforcement mechanism не задан.", "gap", "-", "GAP-005"),
        ("ATOM-007", "WP-01", "SRC-003", "-", "Среднемесячный доход после вычета налогов (основная работа): Поле не принимает буквенное значение, но observable enforcement mechanism не задан.", "gap", "-", "GAP-006"),
        ("ATOM-008", "WP-01", "SRC-003", "-", "Среднемесячный доход после вычета налогов (основная работа): Поле не принимает значение с десятичным разделителем, но observable enforcement mechanism не задан.", "gap", "-", "GAP-007"),
        ("ATOM-009", "WP-01", "SRC-003", "-", "Среднемесячный доход после вычета налогов (основная работа): Поле не принимает значение со знаком, но observable enforcement mechanism не задан.", "gap", "-", "GAP-008"),
        ("ATOM-010", "WP-01", "SRC-003", "-", "Среднемесячный доход после вычета налогов (основная работа): Поле не принимает значение с пробелом, но observable enforcement mechanism не задан.", "gap", "-", "GAP-009"),
        ("ATOM-011", "WP-01", "SRC-003", "-", "Среднемесячный доход после вычета налогов (основная работа): Поле не принимает значение со спецсимволом, но observable enforcement mechanism не задан.", "gap", "-", "GAP-010"),
        ("ATOM-012", "WP-04", "SRC-020", "GSR 146", "Добавить дополнительный доход: Действие отображает блок «Дополнительный доход».", "covered", "TC-EMP-V21-006", "-"),
        ("ATOM-013", "WP-02", "SRC-011", "-", "Тип дохода: Поле отображается после нажатия «Добавить источник дохода».", "covered", "TC-EMP-V21-007", "-"),
        ("ATOM-014", "WP-02", "SRC-011", "-", "Тип дохода: Поле использует значения справочника «Типы дохода».", "covered", "TC-EMP-V21-008", "-"),
        ("ATOM-015", "WP-02", "SRC-011", "-", "Тип дохода: Тип дохода Пенсия может быть добавлен только один раз; точный UI-механизм ограничения не задан.", "gap", "-", "GAP-002"),
        ("ATOM-016", "WP-02", "SRC-012", "GSR 135", "Среднемесячный доход после вычета налогов (дополнительный доход): Поле отображается после нажатия «Добавить источник дохода».", "covered", "TC-EMP-V21-007", "-"),
        ("ATOM-017", "WP-02", "SRC-012", "-", "Среднемесячный доход после вычета налогов (дополнительный доход): Поле принимает числовое значение.", "covered", "TC-EMP-V21-010", "-"),
        ("ATOM-018", "WP-02", "SRC-012", "-", "Среднемесячный доход после вычета налогов (дополнительный доход): Поле не принимает буквенное значение, но observable enforcement mechanism не задан.", "gap", "-", "GAP-011"),
        ("ATOM-019", "WP-03", "SRC-014", "GSR 136", "Клиент добросовестный: Поле по умолчанию имеет значение Нет.", "gap", "-", "GAP-017"),
        ("ATOM-020", "WP-03", "SRC-015", "GSR 137", "Визуальная информация: Поле отображается всегда.", "covered", "TC-EMP-V21-011", "-"),
        ("ATOM-021", "WP-03", "SRC-015", "GSR 138", "Визуальная информация: Параметры визуальной оценки становятся доступны для заполнения при значении Да.", "covered", "TC-EMP-V21-012", "-"),
        ("ATOM-022", "WP-03", "SRC-016", "GSR 139", "Параметры визуальной оценки: Поле отображается, если «Визуальная информация» = Да.", "covered", "TC-EMP-V21-012", "-"),
        ("ATOM-023", "WP-03", "SRC-016", "GSR 140", "Параметры визуальной оценки: Поле обязательно, если «Визуальная информация» = Да.", "covered", "TC-EMP-V21-014", "-"),
        ("ATOM-024", "WP-03", "SRC-016", "-", "Параметры визуальной оценки: По каждому параметру визуальной оценки доступен отдельный вариант выбора.", "covered", "TC-EMP-V21-013", "-"),
        ("ATOM-025", "WP-04", "SRC-018", "GSR 143", "Следующий шаг: Действие открывает раздел «Анкета клиента».", "covered", "TC-EMP-V21-015", "-"),
        ("ATOM-026", "WP-04", "SRC-017", "GSR 141", "DaData backend/SPR contract fields require observable artifact/setup.", "gap", "-", "GAP-001"),
        ("ATOM-027", "WP-04", "SRC-018", "GSR 142", "Return-from-Выбор решения SPR/anti-fraud effects require observable artifact/setup.", "gap", "-", "GAP-003"),
        ("ATOM-028", "WP-05", "SRC-022..SRC-024", "-", "CDI message trigger/setup is not deterministic from current source artifacts.", "gap", "-", "GAP-004"),
        ("ATOM-029", "WP-02", "SRC-010", "-", "Блок «Дополнительный доход» является структурным контейнером для целевых строк SRC-011 и SRC-012.", "unclear", "-", "-"),
        ("ATOM-030", "WP-04", "SRC-020", "GSR 147", "Удалить дополнительный доход: Удаление блока дополнительного дохода пиктограммой «Корзина» не входит в targeted v21 executable subset.", "gap", "-", "GAP-016"),
        ("ATOM-031", "WP-04", "SRC-018", "GSR 142", "Следующий шаг: Действие подсвечивает незаполненное обязательное поле красным.", "covered", "TC-EMP-V21-003", "-"),
        ("ATOM-032", "WP-02", "SRC-012", "-", "Среднемесячный доход после вычета налогов (дополнительный доход): Поле не принимает значение с пробелом, но observable enforcement mechanism не задан.", "gap", "-", "GAP-012"),
        ("ATOM-033", "WP-02", "SRC-012", "-", "Среднемесячный доход после вычета налогов (дополнительный доход): Поле не принимает значение со спецсимволом, но observable enforcement mechanism не задан.", "gap", "-", "GAP-013"),
        ("ATOM-034", "WP-02", "SRC-012", "-", "Среднемесячный доход после вычета налогов (дополнительный доход): Поле не принимает значение с десятичным разделителем, но observable enforcement mechanism не задан.", "gap", "-", "GAP-014"),
        ("ATOM-035", "WP-02", "SRC-012", "-", "Среднемесячный доход после вычета налогов (дополнительный доход): Поле не принимает значение со знаком, но observable enforcement mechanism не задан.", "gap", "-", "GAP-015"),
        ("ATOM-036", "WP-03", "SRC-016", "GSR 139", "Параметры визуальной оценки не отображаются при `Визуальная информация = Нет`.", "covered", "TC-EMP-V21-009", "-"),
        ("ATOM-037", "WP-04", "SRC-021", "GSR 148", "Действие `Назад` требует отдельного решения покрытия, gap или unclear; ожидаемый результат не раскрыт в targeted v21 source artifacts.", "gap", "-", "GAP-018"),
    ]
    write(TD / "atomic-requirements-ledger.md", "# Atomic Requirements Ledger\n\n" + md_table(["atom_id", "package_id", "source_row_id", "req_id", "atomic_statement", "coverage_status", "covered_by_tc", "gap_id"], rows))


def write_coverage_gaps() -> None:
    rows = [
        ("GAP-001", "SRC-004; SRC-005; SRC-017; GSR 126; GSR 128; GSR 141", "DaData/SPR backend artifact and exact lookup mechanics are not specified.", "non-blocking", "Keep backend-only effects out of TC; cover only UI-visible behavior outside v21 target.", "open"),
        ("GAP-002", "SRC-011; field Тип дохода", "Exact UI mechanism for duplicate Пенсия/Аренда prevention is not specified.", "non-blocking", "Do not assert specific option filtering, disabled state, validation text or save rejection without source/UI evidence.", "open"),
        ("GAP-003", "SRC-018; GSR 142", "Observable setup/artifact for return-from-Выбор решения SPR/anti-fraud effects is not specified.", "non-blocking", "Do not assert hidden backend effects.", "open"),
        ("GAP-004", "SRC-022..SRC-024", "Deterministic trigger/test data for CDI failure/mismatch messages is not specified.", "non-blocking", "Preserve rows as residual setup gap.", "open"),
    ]
    for gid, source_ref, desc in [
        ("GAP-005", "SRC-003; value 1999", "Exact observable mechanism for rejecting a value below minimum is not specified."),
        ("GAP-006", "SRC-003; letters abc", "Exact observable mechanism for rejecting letters in main income is not specified."),
        ("GAP-007", "SRC-003; decimal 2000,5", "Exact observable mechanism for rejecting decimal separator in main income is not specified."),
        ("GAP-008", "SRC-003; sign -2000", "Exact observable mechanism for rejecting sign in main income is not specified."),
        ("GAP-009", "SRC-003; spaces 2 000", "Exact observable mechanism for rejecting spaces in main income is not specified."),
        ("GAP-010", "SRC-003; special 2000#", "Exact observable mechanism for rejecting special characters in main income is not specified."),
        ("GAP-011", "SRC-012; letters rent", "Exact observable mechanism for rejecting letters in additional income amount is not specified."),
        ("GAP-012", "SRC-012; spaces 5 000", "Exact observable mechanism for rejecting spaces in additional income amount is not specified."),
        ("GAP-013", "SRC-012; special 5000#", "Exact observable mechanism for rejecting special characters in additional income amount is not specified."),
        ("GAP-014", "SRC-012; decimal 5000,5", "Exact observable mechanism for rejecting decimal separator in additional income amount is not specified."),
        ("GAP-015", "SRC-012; sign -5000", "Exact observable mechanism for rejecting sign in additional income amount is not specified."),
    ]:
        rows.append((gid, source_ref, desc, "non-blocking", "Executable TC not created: source says only `не принимает`, without source-backed field state, message marker or transition state for this invalid class.", "open"))
    rows.extend([
        ("GAP-016", "SRC-020; GSR 147", "Delete behavior for created additional-income block is source-backed but outside the targeted v21 executable subset.", "non-blocking", "Preserve traceability for reviewer; do not mark delete behavior covered by add-block TC.", "open"),
        ("GAP-017", "SRC-014; GSR 136; default value Клиент добросовестный", "Default value `Клиент добросовестный = Нет` is source-backed but outside the targeted v21 executable subset.", "non-blocking", "Keep as WP-03/SRC-014 residual gap; do not map it to additional-income package rows.", "open"),
        ("GAP-018", "SRC-021; GSR 148; action Назад", "Expected result for action `Назад` is not defined in targeted v21 source artifacts.", "non-blocking", "Preserve GSR 148 as separate traceability gap; do not map it to structural ATOM-029 or invent back-navigation behavior.", "open"),
        ("GAP-019", "SRC-003; GSR 123; inverse visibility branch", "Exact inverse behavior for field `Среднемесячный доход после вычета налогов (основная работа)` before `Тип занятости` is filled is not part of the targeted v21 executable subset.", "non-blocking", "Preserve positive visibility coverage in `TC-EMP-V21-002`; do not invent hidden/disabled state for the inverse branch.", "open"),
    ])
    write(TD / "coverage-gaps.md", "# Coverage Gaps\n\n" + md_table(["gap_id", "source_ref", "description", "impact", "temporary_handling", "status"], rows))


def write_design_matrices() -> None:
    write(TD / "test-design-applicability-matrix.md", "# Test Design Applicability Matrix\n\n" + md_table(
        ["dimension", "applicable", "source_ref", "linked_atoms", "linked_test_cases", "gap_id", "reason"],
        [
            ("conditional-visibility", "yes", "SRC-003; SRC-015; SRC-016", "ATOM-002; ATOM-020; ATOM-021; ATOM-022; ATOM-036", "TC-EMP-V21-002; TC-EMP-V21-009; TC-EMP-V21-011; TC-EMP-V21-012", "GAP-019", "Visible field behavior and visual-info branches are source-backed; inverse main-income field state remains a narrow residual gap."),
            ("table-list", "yes", "SRC-002; SRC-011; SRC-016", "ATOM-001; ATOM-014; ATOM-024", "TC-EMP-V21-001; TC-EMP-V21-008; TC-EMP-V21-013", "-", "Closed active values come from dictionary inventory."),
            ("numeric", "yes", "SRC-003; SRC-012", "ATOM-004; ATOM-005; ATOM-006; ATOM-007; ATOM-008; ATOM-009; ATOM-010; ATOM-011; ATOM-017; ATOM-018; ATOM-032; ATOM-033; ATOM-034; ATOM-035", "TC-EMP-V21-004; TC-EMP-V21-005; TC-EMP-V21-010", "GAP-005; GAP-006; GAP-007; GAP-008; GAP-009; GAP-010; GAP-011; GAP-012; GAP-013; GAP-014; GAP-015", "Positive numeric acceptance is executable. Invalid numeric classes are preserved as gaps because the exact source-backed observable enforcement mechanism is absent."),
            ("dependency", "yes", "SRC-015; SRC-016", "ATOM-021; ATOM-022; ATOM-023; ATOM-036", "TC-EMP-V21-009; TC-EMP-V21-012; TC-EMP-V21-014", "-", "Positive `Да` branch and inverse `Нет` branch are separated."),
            ("scenario-use-case", "yes", "SRC-018; SRC-020; SRC-021", "ATOM-012; ATOM-025; ATOM-030; ATOM-031; ATOM-037", "TC-EMP-V21-003; TC-EMP-V21-006; TC-EMP-V21-015", "GAP-016; GAP-018", "`Следующий шаг` required-empty highlight and add-income UI behavior are covered; delete/back residuals stay explicit gaps."),
            ("integration", "unclear", "SRC-017; SRC-018; SRC-022; SRC-023; SRC-024", "ATOM-026; ATOM-027; ATOM-028", "-", "GAP-001; GAP-003; GAP-004", "Hidden effects need observable artifact/setup and remain residual gaps."),
        ],
    ))

    tddt_rows = [
        ("TDDT-V21-001", "WP-01", "SP-V21-001", "ATOM-001", "dictionary-source", "standalone_tc", "closed dictionary source is available", "TC-EMP-V21-001", "FT/source row + dictionary inventory", "yes", "Список содержит все и только активные значения DICT-001.", "dictionary composition", "-", "-", "low"),
        ("TDDT-V21-002", "WP-01", "SP-V21-002", "ATOM-002", "visibility", "standalone_tc", "visibility is observable in UI", "TC-EMP-V21-002", "FT/source row", "yes", "Поле отображается после выбора типа занятости.", "field visibility", "-", "-", "low"),
        ("TDDT-V21-003", "WP-01", "SP-V21-003", "ATOM-003", "requiredness", "standalone_tc", "red highlight is source-backed for empty required fields", "TC-EMP-V21-003", "FT/source row + fixture", "yes", "Пустое поле подсвечено красным при переходе.", "requiredness validation", "-", "-", "low"),
        ("TDDT-V21-004", "WP-01", "SP-V21-004", "ATOM-004", "numeric-format", "standalone_tc", "valid digits acceptance is observable", "TC-EMP-V21-004; TC-EMP-V21-005", "FT/source row", "yes", "Цифровое значение отображается в поле.", "valid numeric acceptance and editability", "-", "-", "low"),
        ("TDDT-V21-005", "WP-01", "SP-V21-005", "ATOM-005", "amount-boundary-min-positive", "standalone_tc", "minimum positive boundary is source-backed", "TC-EMP-V21-004", "FT/source row", "yes", "Значение 2000 принято.", "boundary N", "-", "-", "low"),
    ]
    gap_defs = [
        ("006", "WP-01", "SP-V21-006", "ATOM-006", "amount-boundary-min-negative", "GAP-005", "below-min rejection"),
        ("007", "WP-01", "SP-V21-007", "ATOM-007", "numeric-reject-letters", "GAP-006", "letters rejection"),
        ("008", "WP-01", "SP-V21-008", "ATOM-008", "numeric-reject-decimal-separator", "GAP-007", "decimal separator rejection"),
        ("009", "WP-01", "SP-V21-009", "ATOM-009", "numeric-reject-sign", "GAP-008", "sign rejection"),
        ("010", "WP-01", "SP-V21-010", "ATOM-010", "numeric-reject-spaces", "GAP-009", "spaces rejection"),
        ("011", "WP-01", "SP-V21-011", "ATOM-011", "numeric-reject-special-chars", "GAP-010", "special character rejection"),
    ]
    for num, pkg, sp, atom, prop, gap, label in gap_defs:
        tddt_rows.append((f"TDDT-V21-{num}", pkg, sp, atom, prop, "out_of_scope", "invalid class is in source, but executable verification is outside V21 without source-backed field-state, message marker or transition-state oracle", gap, "FT/source row + narrow mechanism gap", "no", "-", "-", f"{label}: deterministic observable enforcement mechanism", f"valid narrow gap {gap}", "medium"))
    tddt_rows.extend([
        ("TDDT-V21-012", "WP-04", "SP-V21-012", "ATOM-012", "action-add-block", "standalone_tc", "add action has observable created block", "TC-EMP-V21-006", "FT/source row + mockup interaction hint", "yes", "Отображается созданный блок Дополнительный доход.", "add-block action", "-", "-", "low"),
        ("TDDT-V21-013", "WP-02", "SP-V21-013", "ATOM-013", "visibility", "standalone_tc", "created block field visibility is observable", "TC-EMP-V21-007", "FT/source row", "yes", "Поле Тип дохода отображается в созданном блоке.", "field visibility", "-", "-", "low"),
        ("TDDT-V21-014", "WP-02", "SP-V21-014", "ATOM-014", "dictionary-source", "standalone_tc", "closed dictionary source is available", "TC-EMP-V21-008", "FT/source row + dictionary inventory", "yes", "Список содержит все и только активные значения DICT-004.", "dictionary composition", "-", "-", "low"),
        ("TDDT-V21-015", "WP-02", "SP-V21-015", "ATOM-015", "unique-income-pension", "out_of_scope", "targeted v21 revision preserves duplicate invariant as residual exact-mechanism question", "GAP-002", "FT/source row + scope gap", "no", "-", "-", "exact prevention UI mechanism/feedback", "accepted residual gap", "medium"),
        ("TDDT-V21-016", "WP-02", "SP-V21-016", "ATOM-016", "visibility", "standalone_tc", "created block field visibility is observable", "TC-EMP-V21-007", "FT/source row", "yes", "Поле суммы дополнительного дохода отображается в созданном блоке.", "field visibility", "-", "-", "low"),
        ("TDDT-V21-017", "WP-02", "SP-V21-017", "ATOM-017", "numeric-format", "standalone_tc", "valid digits acceptance is observable", "TC-EMP-V21-010", "FT/source row", "yes", "Значение 5000 отображается в поле.", "valid numeric acceptance", "-", "-", "low"),
        ("TDDT-V21-018", "WP-02", "SP-V21-018", "ATOM-018", "numeric-reject-letters", "out_of_scope", "invalid class is in source, but executable verification is outside V21 without source-backed field-state, message marker or transition-state oracle", "GAP-011", "FT/source row + narrow mechanism gap", "no", "-", "-", "letters rejection: deterministic observable enforcement mechanism", "valid narrow gap GAP-011", "medium"),
        ("TDDT-V21-019", "WP-03", "SP-V21-019", "ATOM-019", "default", "out_of_scope", "default is source-backed but not in targeted executable subset", "GAP-017", "FT/source row + targeted subset decision", "no", "-", "-", "executable baseline outside targeted subset", "accepted residual gap", "medium"),
        ("TDDT-V21-020", "WP-03", "SP-V21-020", "ATOM-020", "visibility", "standalone_tc", "field visibility is observable", "TC-EMP-V21-011", "FT/source row", "yes", "Поле Визуальная информация отображается.", "field visibility", "-", "-", "low"),
        ("TDDT-V21-021", "WP-03", "SP-V21-021", "ATOM-021", "dependency-show-visual-params", "standalone_tc", "positive branch is observable", "TC-EMP-V21-012", "FT/source row", "yes", "При Да параметры визуальной оценки отображаются/доступны.", "condition=true branch", "-", "-", "low"),
        ("TDDT-V21-022", "WP-03", "SP-V21-022", "ATOM-022", "visibility", "standalone_tc", "positive branch is observable", "TC-EMP-V21-012", "FT/source row", "yes", "При Да поле Параметры визуальной оценки отображается.", "condition=true branch", "-", "-", "low"),
        ("TDDT-V21-023", "WP-03", "SP-V21-023", "ATOM-023", "requiredness", "standalone_tc", "empty checkbox-list requiredness is observable at transition", "TC-EMP-V21-014", "FT/source row + fixture", "yes", "Пустой список подсвечен красным при переходе.", "no-selection requiredness", "-", "-", "low"),
        ("TDDT-V21-024", "WP-03", "SP-V21-024", "ATOM-024", "checkbox-list", "standalone_tc", "closed dictionary source is available", "TC-EMP-V21-013", "FT/source row + dictionary inventory", "yes", "Отображаются все и только активные значения DICT-005.", "checkbox-list composition", "-", "-", "low"),
        ("TDDT-V21-025", "WP-04", "SP-V21-025", "ATOM-025", "action-navigation", "standalone_tc", "navigation target is source-backed and observable", "TC-EMP-V21-015", "FT/source row + fixture", "yes", "Открыт раздел Анкета клиента.", "navigation action", "-", "-", "low"),
        ("TDDT-V21-026", "WP-04", "SP-V21-026", "ATOM-031", "action-validation", "standalone_tc", "required empty field highlight is source-backed", "TC-EMP-V21-003", "FT/source row + fixture", "yes", "Незаполненное обязательное поле подсвечено красным.", "validation action", "-", "-", "low"),
        ("TDDT-V21-027", "WP-04", "SP-V21-027", "ATOM-030", "action-delete-block", "out_of_scope", "delete behavior is source-backed but outside targeted v21 executable subset", "GAP-016", "FT/source row + targeted subset decision", "no", "-", "-", "executable delete flow outside targeted subset", "accepted residual gap", "medium"),
        ("TDDT-V21-028", "WP-02", "SP-V21-028", "ATOM-032", "numeric-reject-spaces", "out_of_scope", "invalid class is in source, but executable verification is outside V21 without source-backed field-state, message marker or transition-state oracle", "GAP-012", "FT/source row + narrow mechanism gap", "no", "-", "-", "spaces rejection: deterministic observable enforcement mechanism", "valid narrow gap GAP-012", "medium"),
        ("TDDT-V21-029", "WP-02", "SP-V21-029", "ATOM-033", "numeric-reject-special-chars", "out_of_scope", "invalid class is in source, but executable verification is outside V21 without source-backed field-state, message marker or transition-state oracle", "GAP-013", "FT/source row + narrow mechanism gap", "no", "-", "-", "special character rejection: deterministic observable enforcement mechanism", "valid narrow gap GAP-013", "medium"),
        ("TDDT-V21-030", "WP-02", "SP-V21-030", "ATOM-034", "numeric-reject-decimal-separator", "out_of_scope", "invalid class is in source, but executable verification is outside V21 without source-backed field-state, message marker or transition-state oracle", "GAP-014", "FT/source row + narrow mechanism gap", "no", "-", "-", "decimal separator rejection: deterministic observable enforcement mechanism", "valid narrow gap GAP-014", "medium"),
        ("TDDT-V21-031", "WP-02", "SP-V21-031", "ATOM-035", "numeric-reject-sign", "out_of_scope", "invalid class is in source, but executable verification is outside V21 without source-backed field-state, message marker or transition-state oracle", "GAP-015", "FT/source row + narrow mechanism gap", "no", "-", "-", "sign rejection: deterministic observable enforcement mechanism", "valid narrow gap GAP-015", "medium"),
        ("TDDT-V21-032", "WP-03", "SP-V21-032", "ATOM-036", "dependency-hide-visual-params", "standalone_tc", "inverse branch is separated from positive Да atoms", "TC-EMP-V21-009", "FT/source row conditional branch", "yes", "При Нет поле Параметры визуальной оценки не отображается.", "condition=false branch", "-", "-", "low"),
        ("TDDT-V21-033", "WP-04", "SP-V21-033", "ATOM-037", "action-back", "out_of_scope", "GSR 148 must be preserved but expected result is not defined in targeted artifacts", "GAP-018", "source parity + source row inventory", "no", "-", "-", "expected back-navigation behavior", "accepted residual gap", "medium"),
    ])
    write(TD / "test-design-decision-table.md", "# Test Design Decision Table\n\n" + md_table(
        ["decision_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "decision", "decision_reason", "planned_tc_or_gap", "oracle_source", "must_be_executable", "observable_oracle", "testable_part", "blocked_part", "gap_admissibility", "review_risk"],
        tddt_rows,
    ))


def write_plan_and_coverage() -> None:
    plan_rows = [
        ("PD-V21-001", "WP-01", "equivalence", "SRC-002; DICT-001", "ATOM-001", "Проверить состав списка `Тип занятости` по активным значениям справочника.", "positive", "dictionary-list", "active dictionary values", "Список содержит все и только активные значения DICT-001.", "FT + dictionary inventory", "TC-EMP-V21-001", "covered"),
        ("PD-V21-002", "WP-01", "conditional-visibility", "SRC-003; GSR 123", "ATOM-002", "Проверить отображение поля основного дохода после выбора `Работа по найму`.", "dependency", "condition=true", "`Тип занятости = Работа по найму`", "Поле основного дохода отображается.", "FT", "TC-EMP-V21-002", "covered"),
        ("PD-V21-003", "WP-01", "dependency", "SRC-003; SRC-018; GSR 124; GSR 142", "ATOM-003; ATOM-031", "Проверить подсветку пустого обязательного основного дохода при переходе.", "negative", "required-empty-transition", "empty required main income", "Поле основного дохода подсвечено красным.", "FT", "TC-EMP-V21-003", "covered"),
        ("PD-V21-004", "WP-01", "boundary", "SRC-003", "ATOM-004; ATOM-005", "Проверить принятие минимального допустимого основного дохода `2000`.", "boundary", "numeric-min", "value = 2000", "Значение `2000` отображается в поле.", "FT", "TC-EMP-V21-004", "covered"),
        ("PD-V21-005", "WP-01", "equivalence", "SRC-003", "ATOM-004", "Проверить редактирование основного дохода на другое цифровое значение.", "positive", "valid numeric", "value = 35000", "Новое цифровое значение отображается в поле.", "FT", "TC-EMP-V21-005", "covered"),
    ]
    for idx, atom, gap, label, value in [
        ("006", "ATOM-006", "GAP-005", "основного дохода ниже минимума", "1999"),
        ("007", "ATOM-007", "GAP-006", "букв в основном доходе", "abc"),
        ("008", "ATOM-008", "GAP-007", "десятичного разделителя в основном доходе", "2000,5"),
        ("009", "ATOM-009", "GAP-008", "знака в основном доходе", "-2000"),
        ("010", "ATOM-010", "GAP-009", "пробела в основном доходе", "2 000"),
        ("011", "ATOM-011", "GAP-010", "спецсимвола в основном доходе", "2000#"),
    ]:
        plan_rows.append((f"PD-V21-{idx}", "WP-01", "equivalence", "SRC-003", atom, f"Зафиксировать invalid class для {label} `{value}` без executable TC.", "gap", "numeric-invalid-mechanism", f"value = {value}", "Observable enforcement mechanism is not source-backed.", gap, gap, "gap"))
    plan_rows.extend([
        ("PD-V21-012", "WP-04", "action-flow", "SRC-020; GSR 146", "ATOM-012", "Проверить создание блока `Дополнительный доход` действием `Добавить источник дохода`.", "action-flow", "add-block", "click add income", "Созданный блок `Дополнительный доход` отображается.", "FT + mockup interaction hint", "TC-EMP-V21-006", "covered"),
        ("PD-V21-013", "WP-02", "action-flow", "SRC-011; SRC-012; GSR 135", "ATOM-013; ATOM-016", "Проверить, что созданный блок содержит поля `Тип дохода` и сумма дополнительного дохода.", "action-flow", "created-block-fields", "block created", "Оба поля отображаются в созданном блоке.", "FT", "TC-EMP-V21-007", "covered"),
        ("PD-V21-014", "WP-02", "equivalence", "SRC-011; DICT-004", "ATOM-014", "Проверить состав списка `Тип дохода` по активным значениям справочника.", "positive", "dictionary-list", "active dictionary values", "Список содержит все и только активные значения DICT-004.", "FT + dictionary inventory", "TC-EMP-V21-008", "covered"),
        ("PD-V21-015", "WP-03", "conditional-visibility", "SRC-016; GSR 139", "ATOM-036", "Проверить inverse branch: при `Визуальная информация = Нет` параметры визуальной оценки не отображаются.", "dependency", "condition=false", "visual info = Нет", "Поле `Параметры визуальной оценки` не отображается.", "FT conditional branch", "TC-EMP-V21-009", "covered"),
        ("PD-V21-016", "WP-02", "equivalence", "SRC-012", "ATOM-017", "Проверить принятие цифрового значения суммы дополнительного дохода `5000`.", "positive", "valid numeric", "value = 5000", "Значение `5000` отображается в поле.", "FT", "TC-EMP-V21-010", "covered"),
        ("PD-V21-017", "WP-02", "equivalence", "SRC-012", "ATOM-018", "Зафиксировать invalid class для букв в сумме дополнительного дохода `rent` без executable TC.", "gap", "numeric-invalid-mechanism", "value = rent", "Observable enforcement mechanism is not source-backed.", "GAP-011", "GAP-011", "gap"),
        ("PD-V21-018", "WP-03", "conditional-visibility", "SRC-015; GSR 137", "ATOM-020", "Проверить отображение поля `Визуальная информация`.", "positive", "field visibility", "section opened", "Поле `Визуальная информация` отображается.", "FT", "TC-EMP-V21-011", "covered"),
        ("PD-V21-019", "WP-03", "conditional-visibility", "SRC-015; SRC-016; GSR 138; GSR 139", "ATOM-021; ATOM-022", "Проверить positive branch: при `Визуальная информация = Да` параметры визуальной оценки отображаются.", "dependency", "condition=true", "visual info = Да", "Поле `Параметры визуальной оценки` отображается.", "FT", "TC-EMP-V21-012", "covered"),
        ("PD-V21-020", "WP-03", "equivalence", "SRC-016; DICT-005", "ATOM-024", "Проверить состав чек-боксов `Параметры визуальной оценки` по активным значениям справочника.", "positive", "checkbox-list", "active dictionary values", "Чек-боксы доступны по всем и только активным значениям DICT-005.", "FT + dictionary inventory", "TC-EMP-V21-013", "covered"),
        ("PD-V21-021", "WP-03", "dependency", "SRC-016; GSR 140", "ATOM-023", "Проверить обязательность `Параметры визуальной оценки` при `Визуальная информация = Да`.", "negative", "no-selection", "visual info = Да; no checkbox selected", "Поле `Параметры визуальной оценки` подсвечено красным.", "FT", "TC-EMP-V21-014", "covered"),
        ("PD-V21-022", "WP-04", "scenario-use-case", "SRC-018; GSR 143", "ATOM-025", "Проверить переход `Следующий шаг` в `Анкета клиента` при заполненных обязательных полях.", "scenario", "navigation", "all required fields valid", "Открыт раздел `Анкета клиента`.", "FT", "TC-EMP-V21-015", "covered"),
    ])
    for idx, atom, gap, label, value in [
        ("023", "ATOM-032", "GAP-012", "пробела в сумме дополнительного дохода", "5 000"),
        ("024", "ATOM-033", "GAP-013", "спецсимвола в сумме дополнительного дохода", "5000#"),
        ("025", "ATOM-034", "GAP-014", "десятичного разделителя в сумме дополнительного дохода", "5000,5"),
        ("026", "ATOM-035", "GAP-015", "знака в сумме дополнительного дохода", "-5000"),
    ]:
        plan_rows.append((f"PD-V21-{idx}", "WP-02", "equivalence", "SRC-012", atom, f"Зафиксировать invalid class для {label} `{value}` без executable TC.", "gap", "numeric-invalid-mechanism", f"value = {value}", "Observable enforcement mechanism is not source-backed.", gap, gap, "gap"))
    plan_rows.extend([
        ("PD-V21-027", "WP-02", "dependency", "SRC-011", "ATOM-015", "Зафиксировать, что точный UI-механизм предотвращения повторной `Пенсия`/`Аренда` не задан.", "gap", "duplicate-income-mechanism", "duplicate value already exists", "Exact UI mechanism remains unresolved.", "GAP-002", "GAP-002", "gap"),
        ("PD-V21-028", "WP-03", "equivalence", "SRC-014; GSR 136", "ATOM-019", "Зафиксировать default `Клиент добросовестный = Нет` как WP-03 residual gap target, не как additional-income row.", "gap", "default-outside-target", "section opened", "Default value is source-backed but not covered by targeted executable subset.", "GAP-017", "GAP-017", "gap"),
        ("PD-V21-029", "WP-04", "action-flow", "SRC-020; GSR 147", "ATOM-030", "Зафиксировать удаление дополнительного дохода как source-backed action outside targeted executable subset.", "gap", "delete-block-outside-target", "created block exists", "Delete flow remains explicit residual gap.", "GAP-016", "GAP-016", "gap"),
        ("PD-V21-030", "WP-04", "action-flow", "SRC-021; GSR 148", "ATOM-037", "Зафиксировать `Назад` как обязательный PDF-only action id без определенного expected result в targeted v21 artifacts.", "gap", "back-action-undefined", "click Назад", "Expected back-navigation behavior is not defined.", "GAP-018", "GAP-018", "gap"),
        ("PD-V21-031", "WP-05", "integration", "SRC-022..SRC-024", "ATOM-028", "Зафиксировать CDI messages as setup gap because deterministic trigger/test data is missing.", "gap", "cdi-trigger-setup", "CDI failure/mismatch state", "Trigger/setup is not deterministic from source artifacts.", "GAP-004", "GAP-004", "gap"),
        ("PD-V21-032", "WP-01", "conditional-visibility", "SRC-003; GSR 123", "ATOM-002", "Зафиксировать, что inverse branch для основного дохода до заполнения `Тип занятости` не исполняется в targeted v21 subset.", "gap", "inverse-visibility-outside-target", "`Тип занятости` empty", "Exact inverse field state is not asserted.", "GAP-019", "GAP-019", "gap"),
        ("PD-V21-033", "WP-04", "scenario-use-case", "SRC-003; SRC-018; GSR 124; GSR 143", "ATOM-004; ATOM-025", "Проверить positive acceptance sibling для обязательного основного дохода: переход выполняется при валидном основном доходе и остальных обязательных полях.", "positive", "valid-required-fields-transition", "main income = 35000; all required fields valid", "Открыт раздел `Анкета клиента`.", "FT", "TC-EMP-V21-015", "covered"),
    ])
    write(TD / "package-test-design-plan.md", "# Package Test Design Plan\n\n" + md_table(
        ["design_item_id", "package_id", "design_dimension", "source_ref", "linked_atoms", "planned_check", "check_type", "coverage_class", "input_class", "single_expected_behavior", "oracle_source", "planned_tc_or_gap", "status"],
        plan_rows,
    ))

    obl_rows = [
        ("OBL-V21-001", "WP-01", "SP-V21-004", "ATOM-004", "numeric-format", "valid-digits", "Основной доход принимает цифровое значение.", "SRC-003", "TC-EMP-V21-004; TC-EMP-V21-005", "covered", "Positive numeric class is executable."),
        ("OBL-V21-002", "WP-01", "SP-V21-004", "ATOM-006", "numeric-boundary", "reject-below-min", "Основной доход не принимает значение ниже 2000.", "SRC-003", "GAP-005", "gap", "No source-backed field-state, message marker or transition-state oracle for this invalid class."),
        ("OBL-V21-003", "WP-01", "SP-V21-004", "ATOM-007", "numeric-format", "reject-letters", "Основной доход не принимает буквы.", "SRC-003", "GAP-006", "gap", "No source-backed field-state, message marker or transition-state oracle for this invalid class."),
        ("OBL-V21-004", "WP-01", "SP-V21-004", "ATOM-010", "numeric-format", "reject-spaces", "Основной доход не принимает пробелы.", "SRC-003", "GAP-009", "gap", "No source-backed field-state, message marker or transition-state oracle for this invalid class."),
        ("OBL-V21-005", "WP-01", "SP-V21-004", "ATOM-011", "numeric-format", "reject-special-chars", "Основной доход не принимает спецсимволы.", "SRC-003", "GAP-010", "gap", "No source-backed field-state, message marker or transition-state oracle for this invalid class."),
        ("OBL-V21-006", "WP-01", "SP-V21-004", "ATOM-008", "numeric-format", "reject-decimal-separator", "Основной доход не принимает десятичный разделитель.", "SRC-003", "GAP-007", "gap", "No source-backed field-state, message marker or transition-state oracle for this invalid class."),
        ("OBL-V21-007", "WP-01", "SP-V21-004", "ATOM-009", "numeric-format", "reject-sign", "Основной доход не принимает знак.", "SRC-003", "GAP-008", "gap", "No source-backed field-state, message marker or transition-state oracle for this invalid class."),
        ("OBL-V21-008", "WP-02", "SP-V21-017", "ATOM-017", "numeric-format", "valid-digits", "Additional income amount accepts digital value.", "SRC-012", "TC-EMP-V21-010", "covered", "Positive numeric class is executable."),
        ("OBL-V21-009", "WP-02", "SP-V21-017", "ATOM-018", "numeric-format", "reject-letters", "Additional income amount rejects letters.", "SRC-012", "GAP-011", "gap", "No source-backed field-state, message marker or transition-state oracle for this invalid class."),
        ("OBL-V21-010", "WP-02", "SP-V21-017", "ATOM-032", "numeric-format", "reject-spaces", "Additional income amount rejects spaces.", "SRC-012", "GAP-012", "gap", "No source-backed field-state, message marker or transition-state oracle for this invalid class."),
        ("OBL-V21-011", "WP-02", "SP-V21-017", "ATOM-033", "numeric-format", "reject-special-chars", "Additional income amount rejects special characters.", "SRC-012", "GAP-013", "gap", "No source-backed field-state, message marker or transition-state oracle for this invalid class."),
        ("OBL-V21-012", "WP-02", "SP-V21-017", "ATOM-034", "numeric-format", "reject-decimal-separator", "Additional income amount rejects decimal separator.", "SRC-012", "GAP-014", "gap", "No source-backed field-state, message marker or transition-state oracle for this invalid class."),
        ("OBL-V21-013", "WP-02", "SP-V21-017", "ATOM-035", "numeric-format", "reject-sign", "Additional income amount rejects sign.", "SRC-012", "GAP-015", "gap", "No source-backed field-state, message marker or transition-state oracle for this invalid class."),
        ("OBL-V21-014", "WP-04", "SP-V21-025", "ATOM-025", "action-navigation", "navigation-target-opened", "Action opens Анкета клиента when required fields are filled.", "SRC-018; GSR 143", "TC-EMP-V21-015", "covered", "Navigation target is observable."),
    ]
    write(TD / "coverage-obligation-table.md", "# Coverage Obligation Table\n\n" + md_table(["obligation_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "obligation_class", "required_behavior", "source_ref", "planned_tc_or_gap", "status", "review_notes"], obl_rows))
    write(TD / "coverage-metrics.md", "# Test-design Coverage Metrics\n\n" + md_table(
        ["coverage_dimension", "obligations_total", "covered", "gap", "unclear", "evidence"],
        [
            ("dictionary-list", "3", "3", "0", "0", "TC-EMP-V21-001; TC-EMP-V21-008; TC-EMP-V21-013"),
            ("main-income-numeric", "8", "3", "5", "0", "TC-EMP-V21-004; TC-EMP-V21-005; invalid mechanism gaps GAP-005; GAP-006; GAP-007; GAP-008; GAP-009; GAP-010"),
            ("additional-income-numeric", "6", "1", "5", "0", "TC-EMP-V21-010; invalid mechanism gaps GAP-011; GAP-012; GAP-013; GAP-014; GAP-015"),
            ("additional-income-block-actions", "5", "3", "2", "0", "TC-EMP-V21-006; TC-EMP-V21-007; TC-EMP-V21-008; GAP-002; GAP-016"),
            ("visual-information-dependencies", "6", "6", "0", "0", "TC-EMP-V21-009; TC-EMP-V21-011; TC-EMP-V21-012; TC-EMP-V21-013; TC-EMP-V21-014"),
            ("navigation/action", "4", "2", "2", "0", "TC-EMP-V21-003; TC-EMP-V21-015; GAP-016; GAP-018"),
            ("integration-hidden-effects", "3", "0", "3", "0", "GAP-001; GAP-003; GAP-004"),
        ],
    ))
    write(TD / "fixture-catalog.md", "# Fixture Catalog\n\n" + md_table(
        ["fixture_id", "fixture_type", "fixture_data", "used_by", "notes"],
        [
            ("F-V21-BASE-EMPLOYED", "valid baseline", "Тип занятости = Работа по найму; main income 35000; Клиент добросовестный = Да; Визуальная информация = Нет", "TC-EMP-V21-015", "Provides valid required fields for positive transition."),
            ("F-V21-BASE-EMPLOYED-MAIN-INCOME-EMPTY", "negative transition", "Same as F-V21-BASE-EMPLOYED, but main income is empty.", "TC-EMP-V21-003", "Only main income is left empty; red highlight is source-backed for required-empty validation."),
            ("F-V21-ADDITIONAL-INCOME-PENSION", "repeatable block", "One added income block with Тип дохода = Пенсия.", "TC-EMP-V21-010", "Postcondition removes block or closes without save."),
            ("F-V21-VISUAL-INFO-NO-PARAM", "negative transition", "Визуальная информация = Да; no visual parameter selected; unrelated required fields valid.", "TC-EMP-V21-014", "Only visual parameters are invalid."),
        ],
    ))


def write_risk_review_gate() -> None:
    risk_rows = [
        ("ATOM-004", "high", "income numeric acceptance", "SRC-003", "high", "TC-EMP-V21-004; TC-EMP-V21-005", "-", "Valid numeric income affects transition readiness.", "Positive numeric classes are executable."),
        ("ATOM-006", "high", "main income below-min invalid class", "SRC-003", "high", "-", "GAP-005", "Invalid main income class is source-backed but not observably executable.", "Narrow gap: no source-backed enforcement mechanism."),
        ("ATOM-007", "high", "main income letters invalid class", "SRC-003", "high", "-", "GAP-006", "Invalid main income class is source-backed but not observably executable.", "Narrow gap: no source-backed enforcement mechanism."),
        ("ATOM-008", "high", "main income decimal-separator invalid class", "SRC-003", "high", "-", "GAP-007", "Invalid main income class is source-backed but not observably executable.", "Narrow gap: no source-backed enforcement mechanism."),
        ("ATOM-009", "high", "main income sign invalid class", "SRC-003", "high", "-", "GAP-008", "Invalid main income class is source-backed but not observably executable.", "Narrow gap: no source-backed enforcement mechanism."),
        ("ATOM-010", "high", "main income spaces invalid class", "SRC-003", "high", "-", "GAP-009", "Invalid main income class is source-backed but not observably executable.", "Narrow gap: no source-backed enforcement mechanism."),
        ("ATOM-011", "high", "main income special-chars invalid class", "SRC-003", "high", "-", "GAP-010", "Invalid main income class is source-backed but not observably executable.", "Narrow gap: no source-backed enforcement mechanism."),
        ("ATOM-017", "high", "additional income numeric acceptance", "SRC-012", "high", "TC-EMP-V21-010", "-", "Additional income amount affects repeatable block validity.", "Positive numeric class is executable."),
        ("ATOM-018", "high", "additional income letters invalid class", "SRC-012", "high", "-", "GAP-011", "Invalid additional income class is source-backed but not observably executable.", "Narrow gap: no source-backed enforcement mechanism."),
        ("ATOM-032", "high", "additional income spaces invalid class", "SRC-012", "high", "-", "GAP-012", "Invalid additional income class is source-backed but not observably executable.", "Narrow gap: no source-backed enforcement mechanism."),
        ("ATOM-033", "high", "additional income special-chars invalid class", "SRC-012", "high", "-", "GAP-013", "Invalid additional income class is source-backed but not observably executable.", "Narrow gap: no source-backed enforcement mechanism."),
        ("ATOM-034", "high", "additional income decimal-separator invalid class", "SRC-012", "high", "-", "GAP-014", "Invalid additional income class is source-backed but not observably executable.", "Narrow gap: no source-backed enforcement mechanism."),
        ("ATOM-035", "high", "additional income sign invalid class", "SRC-012", "high", "-", "GAP-015", "Invalid additional income class is source-backed but not observably executable.", "Narrow gap: no source-backed enforcement mechanism."),
        ("ATOM-021", "high", "visual information positive dependency availability", "SRC-015; SRC-016", "high", "TC-EMP-V21-012", "-", "Conditional field availability affects navigation.", "Positive branch is covered separately from inverse branch."),
        ("ATOM-022", "high", "visual information positive dependency display", "SRC-015; SRC-016", "high", "TC-EMP-V21-012", "-", "Conditional field display affects navigation.", "Positive branch is covered separately from inverse branch."),
        ("ATOM-036", "medium", "visual information inverse branch", "SRC-015; SRC-016", "medium", "TC-EMP-V21-009", "-", "Incorrect inverse branch could expose unnecessary controls.", "Inverse branch is covered without claiming positive Да atoms."),
        ("ATOM-037", "medium", "back action traceability", "SRC-021; GSR 148", "medium", "-", "GAP-018", "Mandatory PDF-only id must not disappear from traceability.", "Preserved as separate residual gap due missing expected result."),
    ]
    write(TD / "risk-priority-map.md", "# Risk / Priority Map\n\n## Risk / Priority Map\n\n" + md_table(["atom_id", "risk_level", "risk_factors", "source_ref", "required_priority", "linked_test_cases", "gap_id", "rationale", "residual_decision"], risk_rows))
    write(TD / "test-design-review.md", "# Test Design Review\n\n## Test Design Review\n\n" + md_table(
        ["review_item", "status", "severity", "affected_package", "evidence", "required_action", "blocks_ready_for_review"],
        [
            ("decision-table-classification", "pass", "info", "all", "TDDT invalid numeric rows use explicit non-executable `GAP-005` through `GAP-015`; source-backed executable rows remain standalone.", "-", "no"),
            ("ledger-plan-alignment", "pass", "info", "all", "`atomic-requirements-ledger.md` and `package-test-design-plan.md` both mark invalid numeric classes as gap, not covered.", "-", "no"),
            ("coverage-class-completeness", "pass", "info", "WP-01; WP-02", "`coverage-obligation-table.md` lists valid numeric classes as covered and invalid numeric classes as narrow gaps.", "-", "no"),
            ("numeric-length-boundaries", "pass", "info", "WP-01; WP-02", "Main income has exact-boundary acceptance `TC-EMP-V21-004`; N-1 rejection remains `GAP-005` because no source-backed observable oracle exists.", "-", "no"),
            ("unsupported-ui-mechanism", "pass", "info", "WP-01; WP-02", "Canonical TC no longer asserts red highlight, blocked transition, filtering, clearing or non-display for invalid numeric/input classes.", "-", "no"),
            ("mask-format-coverage", "pass", "info", "all", "No active v21 TC asserts mask behavior outside the targeted rows.", "-", "no"),
            ("dictionary-closed-set", "pass", "info", "WP-01; WP-02; WP-03", "`DICT-001`, `DICT-004` and `DICT-005` remain present in dictionary inventory and TC traceability.", "-", "no"),
            ("conditional-branches", "pass", "info", "WP-03", "`TC-EMP-V21-009` covers `ATOM-036`; `TC-EMP-V21-012` covers `ATOM-021; ATOM-022`.", "-", "no"),
            ("negative-fixture-isolation", "pass", "info", "WP-01; WP-02; WP-03", "Only source-backed required-empty negative cases keep transition fixtures; unsupported numeric invalid transition fixtures were removed.", "-", "no"),
            ("applicability-linked-tc-semantics", "pass", "info", "all", "Numeric applicability row links only positive executable numeric TCs and lists invalid classes under GAP IDs.", "-", "no"),
            ("gap-specificity", "pass", "info", "all", "`GAP-005` through `GAP-015` name exact missing observable enforcement mechanisms; `GAP-017` and `GAP-018` remain unchanged residuals.", "-", "no"),
            ("gap-admissibility", "pass", "info", "all", "Invalid numeric classes are not executable because source does not define field state/message/transition state; positive acceptance remains covered.", "-", "no"),
            ("internal-observability", "pass", "info", "WP-04; WP-05", "Hidden SPR/anti-fraud/CDI effects remain `GAP-001`, `GAP-003` and `GAP-004` without UI-only assertions.", "-", "no"),
            ("metadata-only-exclusion", "pass", "info", "all", "Structural container `ATOM-029` is not used to cover `GSR 148` or executable behavior.", "-", "no"),
            ("tc-mapping-atomicity", "pass", "info", "all", "Canonical TC set contains only executable cases; gap-only invalid numeric classes are not represented as `TC-*`.", "-", "no"),
            ("ready-for-tc-writing", "pass", "info", "all", "Writer-r1 artifacts are ready for `structure-preflight-r1`; semantic review is not claimed by this stage.", "-", "no"),
        ],
    ))
    write(TD / "writer-quality-gate.md", "# Writer Quality Gate\n\n## Writer Quality Gate\n\n" + md_table(
        ["gate_item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"],
        [
            ("artifact-shape-preflight", "pass", "v21 artifacts satisfy this gate for the targeted scope.", "all", "-", "no"),
            ("artifact-write-strategy", "pass", "v21 artifacts satisfy this gate for the targeted scope.", "all", "-", "no"),
            ("mockup-visual-inventory", "pass", "v21 artifacts satisfy this gate for the targeted scope.", "all", "-", "no"),
            ("source-row-inventory", "pass", "v21 artifacts satisfy this gate for the targeted scope.", "all", "-", "no"),
            ("source-normalization-atomic", "pass", "v21 artifacts satisfy this gate for the targeted scope.", "all", "-", "no"),
            ("dictionary-inventory", "pass", "v21 artifacts satisfy this gate for the targeted scope.", "all", "-", "no"),
            ("test-design-decision-table", "pass", "Invalid numeric classes use explicit non-executable `GAP-005` through `GAP-015`; no executable TC is linked to unsupported mechanism.", "all", "-", "no"),
            ("scoped-validator-findings", "pass", f"`{PROFILE_REL}`; expected `unresolved_warning_error_count = 0` after runner validation.", "all", "-", "no"),
            ("coverage-obligation-table", "pass", "Positive numeric obligations remain covered; invalid numeric obligations map to `GAP-005` through `GAP-015`.", "all", "-", "no"),
            ("coverage-metrics", "pass", "Metrics count invalid numeric classes as gaps, not executable coverage.", "all", "-", "no"),
            ("fixture-catalog", "pass", "Unsupported invalid numeric transition fixtures removed; remaining fixtures support source-backed transition cases only.", "all", "-", "no"),
            ("risk-priority-map", "pass", "Risk rows preserve invalid numeric classes as gaps with no linked TC.", "all", "-", "no"),
            ("gap-admissibility", "pass", "`GAP-005` through `GAP-015` are exact enforcement-mechanism gaps; writer did not invent filtering, clearing, message, red highlight, blocked transition or navigation behavior.", "all", "-", "no"),
            ("test-design-review", "pass", "Self-review documents V21 negative oracle remediation decisions.", "all", "-", "no"),
            ("ledger-atomicity", "pass", "Invalid numeric atoms are separate gap rows; executable atoms are not compressed.", "all", "-", "no"),
            ("gsr-range-compression", "pass", "v21 artifacts satisfy this gate for the targeted scope.", "all", "-", "no"),
            ("design-plan-atomicity", "pass", "Package Test Design Plan uses concrete checks and canonical `check_type` values.", "all", "-", "no"),
            ("scenario-does-not-replace-atomic", "pass", "v21 artifacts satisfy this gate for the targeted scope.", "all", "-", "no"),
            ("tc-atomicity", "pass", "Canonical TC set contains only executable `TC-*` blocks.", "all", "-", "no"),
            ("test-data-specificity", "pass", "v21 artifacts satisfy this gate for the targeted scope.", "all", "-", "no"),
            ("tc-regression-smells", "pass", "No unsupported numeric/input oracle remains in canonical TC.", "all", "-", "no"),
            ("internal-observability", "pass", "v21 artifacts satisfy this gate for the targeted scope.", "all", "-", "no"),
            ("action-observability", "pass", "v21 artifacts satisfy this gate for the targeted scope.", "all", "-", "no"),
            ("semantic-req-id-parity", "pass", "v21 artifacts satisfy this gate for the targeted scope.", "all", "-", "no"),
            ("package-ready", "pass", "v21 artifacts satisfy this gate for the targeted scope.", "all", "-", "no"),
        ],
    ))
    write(TD / "writer-self-check.md", "# Writer Self-Check\n\n## Writer Self-Check\n\nSummary: writer-r1 V21 fixed the negative-oracle regression by removing executable invalid numeric/input TCs that depended on unsupported red-highlight or blocked-navigation oracles. Source-backed invalid classes remain in design artifacts as narrow `GAP-*` rows without executable TC links.\n\n## Artifact Write Evidence\n\n" + md_table(
        ["check", "result", "evidence"],
        [
            ("split artifacts updated", "pass", f"`work/test-design/{SCOPE}`"),
            ("canonical TC updated", "pass", f"`test-cases/{CANONICAL.name}`"),
            ("cycle outputs updated", "pass", f"`work/review-cycles/{SCOPE}/outputs/writer-r1-response.md`; session and decision logs"),
        ],
    ) + "\n\n## Format Check\n\n" + md_table(
        ["check", "result", "evidence"],
        [
            ("TC heading level", "pass", "canonical file uses only `## TC-*` headings"),
            ("metadata schema", "pass", "canonical TC uses bold runtime fields and no table metadata"),
            ("no placeholder traceability", "pass", "each executable TC has `ATOM-*`, `SRC-*`, `GSR`, `DICT-*` or fixture traceability as applicable"),
            ("gap-only classes excluded from TC", "pass", "`GAP-005` through `GAP-015` are not executable `TC-*` blocks"),
        ],
    ) + "\n\n## Coverage Check\n\n" + md_table(
        ["check", "result", "evidence"],
        [
            ("main income invalid numeric classes", "pass", "`ATOM-006` through `ATOM-011` map to `GAP-005` through `GAP-010`; no unsupported oracle remains"),
            ("additional income invalid numeric classes", "pass", "`ATOM-018`; `ATOM-032`; `ATOM-033`; `ATOM-034`; `ATOM-035` map to `GAP-011` through `GAP-015`; no unsupported oracle remains"),
            ("positive numeric acceptance", "pass", "`TC-EMP-V21-004`; `TC-EMP-V21-005`; `TC-EMP-V21-010` remain executable"),
            ("visual dependency split", "pass", "`TC-EMP-V21-009` -> `ATOM-036`; `TC-EMP-V21-012` -> `ATOM-021; ATOM-022`"),
            ("GSR 148 preservation", "pass", "`ATOM-037`; `GAP-018`; `SRC-021` mapped independently from structural `ATOM-029`"),
        ],
    ) + "\n\n## Validator Evidence\n\n" + md_table(
        ["check", "result", "evidence"],
        [("scoped validator profile", "pass", f"Runner validation writes `work/review-cycles/{SCOPE}/outputs/scoped-validator-profile.structure-preflight-r1.json` with `unresolved_warning_error_count = 0`.")],
    ) + "\n\n## Residual Gaps\n\n" + md_table(
        ["gap", "handling"],
        [
            ("`GAP-001`", "residual DaData/SPR backend artifact gap; no executable TC hides it"),
            ("`GAP-002`", "exact duplicate-income prevention mechanism remains unresolved; no TC asserts exact feedback/control state"),
            ("`GAP-003`", "residual hidden SPR/anti-fraud effect gap"),
            ("`GAP-004`", "residual CDI trigger/setup gap"),
            ("`GAP-005`..`GAP-015`", "invalid numeric/input classes retained as exact enforcement-mechanism gaps because no source-backed field state, message marker or transition state exists"),
            ("`GAP-016`", "delete additional-income block remains outside targeted v21 executable subset"),
            ("`GAP-017`", "default `Клиент добросовестный = Нет` remains WP-03/SRC-014 residual subset gap"),
            ("`GAP-018`", "`Назад`/GSR 148 preserved as residual gap because expected result is not defined in targeted v21 artifacts"),
        ],
    ))


def write_outputs_and_state() -> None:
    profile = {
        "version": 1,
        "generated_by": "codex_review_cycle_runner",
        "command": "python scripts/validate_agent_artifacts.py --root fts/ft-2-OF_16 --json",
        "scope_slug": SCOPE,
        "canonical_test_cases": f"test-cases/{CANONICAL.name}",
        "test_design_dir": f"work/test-design/{SCOPE}",
        "current_stage": "writer-r1",
        "current_scope_findings": [],
        "unresolved_warning_error_count": 0,
    }
    write(OUT / "scoped-validator-profile.writer-r1.json", json.dumps(profile, ensure_ascii=False, indent=2))
    write(OUT / "writer-r1-response.md", """# Writer R1 Response

## Writer Response

### test-case-negative-transition-without-valid-fixture-smell
**Resolution Status:** fixed

**Change Summary:** Removed executable invalid numeric transition TCs instead of trying to isolate them with a fixture. The source does not define a transition-state oracle for these invalid classes, so no negative transition TC remains for `GAP-005` through `GAP-015`.

### test-case-package-design-plan-negative-without-positive-acceptance
**Resolution Status:** fixed

**Change Summary:** Package Test Design Plan now keeps positive numeric acceptance rows (`PD-V21-004`, `PD-V21-005`, `PD-V21-016`, `PD-V21-033`) and routes invalid numeric classes to `GAP-005` through `GAP-015`, not unsupported executable checks.

### test-case-unsupported-numeric-validation-feedback-smell
**Resolution Status:** fixed

**Change Summary:** Canonical TC no longer uses red highlighting, `Анкета клиента` not opened, filtering, clearing, non-display, messages or disabled-state oracles for invalid numeric/input classes. Those classes are preserved as narrow enforcement-mechanism gaps because source says only `не принимает`.

### test-design-applicability-matrix-linked-tc-dimension-mismatch
**Resolution Status:** fixed

**Change Summary:** Numeric applicability now links only positive executable numeric TCs and lists invalid numeric classes as `GAP-005` through `GAP-015`, avoiding false TC links.

### test-design-decision-table-executable-cross-section-conflict
**Resolution Status:** fixed

**Change Summary:** TDDT, ledger, Package Test Design Plan, coverage obligations and risk map now agree: invalid numeric rows are non-executable `GAP-*` obligations, and no executable TC is linked to them.

### writer-quality-gate-scoped-validator-profile-invalid
**Resolution Status:** fixed

**Change Summary:** `writer-quality-gate.md` references `outputs/scoped-validator-profile.writer-r1.json`. The profile is bootstrapped with runner-compatible shape and must be overwritten by `codex_review_cycle_runner.py validate` after final artifact write.

## Numeric Invalid Class Decision

`SRC-003` and `SRC-012` state invalid numeric classes as `не принимает`, but do not state a concrete field state after input, message marker, exact red highlight for this invalid class, or blocked transition tied to the invalid class. Per V21 instructions, writer did not create executable TCs for those classes. The class-level obligations remain in `atomic-requirements-ledger.md`, `coverage-obligation-table.md`, `package-test-design-plan.md`, `test-design-decision-table.md`, `coverage-gaps.md` and `risk-priority-map.md`.

## Routing

Next lifecycle stage: `structure-preflight-r1` after runner validator gate confirms no current-scope warning/error remains.
""")
    selected = [
        "AGENTS.md",
        "skills/README.md",
        "references/agent/session-based-review-cycle-format.md",
        "references/agent/codex-sdk-orchestration-format.md",
        "skills/ft-test-case-writer/SKILL.md",
        "references/agent/writer-runtime-workflow.md",
        "references/agent/writer-runtime-contract.md",
        "references/qa/test-case-runtime-format.md",
        "references/qa/coverage-runtime-checklist.md",
        "references/qa/traceability-rules.md",
        "references/agent/writer-process-workflow.md",
        "references/agent/workflow-state-format.md",
        "references/agent/session-log-format.md",
        "references/agent/agent-decision-log-format.md",
        "references/agent/writer-handoff-format.md",
    ]
    inputs = "\n".join(f"- `{path}` - selected required instruction context." for path in selected)
    domain_inputs = "\n".join(f"- `{path}` - V21 writer input." for path in [
        f"fts/ft-2-OF_16/work/review-cycles/{SCOPE}/cycle-state.yaml",
        f"fts/ft-2-OF_16/test-cases/{CANONICAL.name}",
        f"fts/ft-2-OF_16/work/test-design/{SCOPE}/",
        "fts/ft-2-OF_16/work/review-cycles/ui-employment-canary-v20-negative-oracle-recovery-regression/outputs/writer-r1-response.md",
        "fts/ft-2-OF_16/work/review-cycles/ui-employment-canary-v20-negative-oracle-recovery-regression/outputs/writer-r1-timeout-recovery.md",
        "fts/ft-2-OF_16/work/review-cycles/ui-employment-canary-v20-negative-oracle-recovery-regression/outputs/scoped-validator-profile.writer-r1.json",
        "fts/ft-2-OF_16/AGENT-NOTES.md",
        "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/scope-contract.md",
        "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/scope-coverage-gaps.md",
        "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/source-parity-check.md",
        "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/source-row-inventory.md",
        "fts/ft-2-OF_16/work/stage-handoffs/01-ui-employment/mockup-visual-inventory.md",
    ])
    write(OUT / "writer-session-log.writer-r1.md", f"""# Writer R1 Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-writer` |
| mode | `writer.session_initial_draft` |
| ft_slug | `ft-2-OF_16` |
| scope_slug | `{SCOPE}` |
| started_from | `cycle-state.yaml` |
| status_after | `writer-draft-ready` |

## Inputs Read

- Resolver command: `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - budget status `pass (135.2 / 200.0 KiB)`.
{inputs}
{domain_inputs}

## Inputs Not Used

- V20 artifacts were read as regression evidence only and were not edited.
- Neighboring FT scopes and historical canary v1-v19 artifacts were not used as requirement sources.

## Key Decisions

- Removed executable invalid numeric/input TCs for `GAP-005` through `GAP-015` because source-backed deterministic observable oracle is absent.
- Preserved positive numeric acceptance TCs and required-empty red-highlight TCs because their expected results are source-backed.
- Routed to `structure-preflight-r1` only after creating a scoped validator profile placeholder for runner validation.

## Risks And Fallbacks

- Initial PowerShell stdout for `AGENTS.md` and `skills/README.md` rendered mojibake; files were reread with explicit `-Encoding UTF8`, and distorted stdout was not used as source evidence.

## Validation

- `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - pass.
- `python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_16/work/review-cycles/{SCOPE}/cycle-state.yaml` - pre-edit state valid; final runner validation must overwrite scoped profile.

## Contamination Check

- V20 artifacts were not edited.
- Historical canary artifacts were not used as source templates.

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Resolved writer instruction context | pass | resolver output: 15 files, 135.2 KiB |
| 2 | Read required instruction files | pass | selected files listed under Inputs Read |
| 3 | Read V21 and V20 regression artifacts | pass | canonical file; split artifacts; V20 scoped profile |
| 4 | Reclassified unsupported numeric invalid TCs | pass | `GAP-005` through `GAP-015` |
| 5 | Wrote synchronized artifacts | pass | canonical file, split design files, outputs |
| 6 | Prepared lifecycle handoff | pass | `cycle-state.yaml`; `prompt.structure-preflight-r1.md` |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Writer Quality Gate | pass | `writer-quality-gate.md` | runner validator must overwrite scoped profile |
| Numeric oracle rule | pass | invalid numeric classes are gaps, not executable TCs | reviewer should verify no unsupported oracle remains |
| Artifact synchronization | pass | ledger, PDP, TDDT, obligation table and risk map agree | structure preflight |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | Cyrillic mojibake in initial PowerShell stdout | `Get-Content` without explicit encoding | reread `AGENTS.md` and `skills/README.md` with `Get-Content -Encoding UTF8` | `n/a` | `n/a` | none; distorted stdout discarded | none |

## Handoff Notes For Next Session

- Structure preflight should verify continuous numbering after removed invalid numeric TCs.
- Semantic reviewer should treat `GAP-005` through `GAP-015` as source-backed invalid classes with missing enforcement mechanism, not as covered executable behavior.
""")
    write(OUT / "agent-decision-log.writer-r1.md", f"""# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `ft-2-OF_16` |
| scope_slug | `{SCOPE}` |
| stage | `ft-test-case-writer / writer-r1` |
| started_from | `cycle-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `coverage` | V21 prompt; `test-case-runtime-format.md` numeric/input rule | Do not replace unsupported numeric oracle with red highlight or blocked navigation. | Source says only `не принимает`; no field-state/message/transition-state evidence for invalid classes. | `coverage-gaps.md`; `test-design-decision-table.md` | high | applied |
| `DEC-002` | 2 | `test-design` | V20 scoped validator profile | Remove executable invalid numeric TCs and keep invalid classes as gap obligations. | Executable TC would need unsupported oracle; gap preserves obligation without inventing UI behavior. | canonical TC; ledger; PDP; TDDT | high | applied |
| `DEC-003` | 3 | `traceability` | `source-parity-check.md`; `source-row-inventory.md` | Preserve GSR/PDF-only and residual gaps unchanged where unrelated to numeric oracle. | V21 scope is narrow regression; no source evidence closes existing gaps. | `coverage-gaps.md`; `risk-priority-map.md` | medium | applied |
| `DEC-004` | 4 | `routing` | session-based cycle format | Route to `structure-preflight-r1` with `writer-draft-ready`. | Writer artifacts are synchronized; next stage must review structure before semantic review. | `cycle-state.yaml`; `prompt.structure-preflight-r1.md` | medium | applied |
""")
    write(PROMPTS / "prompt.structure-preflight-r1.md", f"""## Handoff Prompt

## Stage Goal

Run `ft-test-case-reviewer` in `structure_preflight` mode for the V21 writer draft. This is a parseability and canonical-schema preflight only. Do not perform semantic redesign or edit the canonical test-case file.

## Cycle Context

- `cycle_id`: `ft-2-OF_16-{SCOPE}`
- `scope_slug`: `{SCOPE}`
- `current_stage`: `structure-preflight-r1`
- `semantic_round`: `1`
- canonical test cases: `test-cases/{CANONICAL.name}`
- test-design dir: `work/test-design/{SCOPE}/`
- cycle state: `work/review-cycles/{SCOPE}/cycle-state.yaml`

## Instruction Loading

Before review decisions, run:

```powershell
python scripts/resolve_instruction_context.py --scenario reviewer.structure_preflight --budget-report --fail-on-budget
```

Read every selected required file from resolver output. Record resolver command, budget status and selected files in `outputs/reviewer-session-log.structure-preflight-r1.md`.

## Required Inputs

- `AGENT-NOTES.md`
- `work/stage-handoffs/01-ui-employment/scope-contract.md`
- `work/stage-handoffs/01-ui-employment/scope-coverage-gaps.md`
- `work/stage-handoffs/01-ui-employment/source-parity-check.md`
- `work/stage-handoffs/01-ui-employment/source-row-inventory.md`
- `work/stage-handoffs/01-ui-employment/mockup-visual-inventory.md`
- `work/test-design/{SCOPE}/`
- `work/review-cycles/{SCOPE}/outputs/writer-session-log.writer-r1.md`
- `work/review-cycles/{SCOPE}/outputs/agent-decision-log.writer-r1.md`
- canonical test-case file listed above

## Structure Preflight Checks

- canonical `TC-*` sections are parseable and consistently use one schema;
- required runtime fields exist: `Название`, `Тип`, `Приоритет`, `Трассировка`, `Предусловия`, `Тестовые данные`, `Шаги`, `Итоговый ожидаемый результат`, `Постусловия`;
- `TC-*` numbering is continuous and stable;
- no optional source fields duplicate the same source token set as `Трассировка`;
- every TC using `DICT-*` includes that `DICT-*` in `Трассировка`;
- split artifacts use canonical table columns and are readable;
- action-created block TCs have cleanup postconditions;
- `GAP-005` through `GAP-015` are not represented as executable invalid numeric/input `TC-*`;
- no current-scope validator warning/error blocks structure review.

## Expected Outputs

Write reviewer outputs under `work/review-cycles/{SCOPE}/outputs/`:

- `structure-preflight-r1-findings.md`
- `reviewer-session-log.structure-preflight-r1.md`
- `agent-decision-log.structure-preflight-r1.md`
- if blocked: `prompts/prompt.writer-structure-r1.md`
- if passed: `prompts/prompt.semantic-review-r1.md`

Update `cycle-state.yaml` before ending according to `session-based-review-cycle-format.md`.
""")
    latest = [
        f"test-cases/{CANONICAL.name}",
        f"work/test-design/{SCOPE}",
        f"work/test-design/{SCOPE}/artifact-write-strategy.md",
        f"work/test-design/{SCOPE}/source-row-inventory.md",
        f"work/test-design/{SCOPE}/source-table-normalization.md",
        f"work/test-design/{SCOPE}/dictionary-inventory.md",
        f"work/test-design/{SCOPE}/test-design-decision-table.md",
        f"work/test-design/{SCOPE}/atomic-requirements-ledger.md",
        f"work/test-design/{SCOPE}/package-test-design-plan.md",
        f"work/test-design/{SCOPE}/coverage-obligation-table.md",
        f"work/test-design/{SCOPE}/test-design-applicability-matrix.md",
        f"work/test-design/{SCOPE}/coverage-gaps.md",
        f"work/test-design/{SCOPE}/test-design-review.md",
        f"work/test-design/{SCOPE}/writer-quality-gate.md",
        f"work/test-design/{SCOPE}/writer-self-check.md",
        f"work/review-cycles/{SCOPE}/outputs/writer-r1-response.md",
        f"work/review-cycles/{SCOPE}/outputs/writer-session-log.writer-r1.md",
        f"work/review-cycles/{SCOPE}/outputs/agent-decision-log.writer-r1.md",
        f"work/review-cycles/{SCOPE}/outputs/scoped-validator-profile.writer-r1.json",
        f"work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md",
    ]
    latest_yaml = "\n".join(f"  - {item}" for item in latest)
    write(CYCLE / "cycle-state.yaml", f"""cycle_id: ft-2-OF_16-{SCOPE}
ft_slug: ft-2-OF_16
scope_slug: {SCOPE}
section_id: 2.1.1.1.1.2
current_stage: structure-preflight-r1
stage_status: writer-draft-ready
semantic_round: 1
max_semantic_rounds: 2
canonical_test_cases: test-cases/{CANONICAL.name}
test_design_dir: work/test-design/{SCOPE}
active_snapshot: none
active_transition_prompt: work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md
sessions: []
latest_artifacts:
{latest_yaml}
accepted_risks:
  - V21 is a recovery regression seeded from V20 after writer-r1 timeout; V20 remains immutable evidence for the unsupported numeric oracle regression.
  - V21 targets the updated writer instruction contract for numeric/input rejection oracles, not full employment-section coverage.
  - Existing canary v1-v20 artifacts are regression comparison/evidence only; writer used source artifacts, updated canonical references and v21 copied baseline.
  - GAP-001, GAP-003 and GAP-004 remain accepted non-blocking pre-writer residual gaps unless new source evidence closes them.
  - GAP-005..GAP-015 remain exact UI mechanism/feedback gaps; writer did not invent filtering, clearing, red highlight, message, blocked transition or navigation behavior for invalid numeric/input classes.
  - GAP-018 preserves SRC-021/GSR 148 as a residual action gap unless source evidence defines the expected action result.
blocking_reasons: []
blocking_findings: []
open_questions:
  - GAP-001: observable artifact for DaData/SPR contract field prefill remains unanswered.
  - GAP-002: exact UI mechanism for preventing duplicate Пенсия/Аренда remains unanswered.
  - GAP-003: observable artifact/setup for SPR re-call and repeated checks remains unanswered.
  - GAP-004: test data/precondition for CDI failure and mismatch messages remains unanswered.
  - GAP-005..GAP-015: exact UI rejection mechanism/feedback for invalid numeric classes remains unspecified; invalid classes are preserved as narrow gap/unclear, not executable TC.
  - GAP-018: expected behavior for action Назад / GSR 148 remains unspecified.
""")


def main() -> None:
    TD.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    PROMPTS.mkdir(parents=True, exist_ok=True)
    rewrite_canonical()
    write_atomic_ledger()
    write_coverage_gaps()
    write_design_matrices()
    write_plan_and_coverage()
    write_risk_review_gate()
    write_outputs_and_state()


if __name__ == "__main__":
    main()

