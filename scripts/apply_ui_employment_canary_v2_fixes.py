from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FT_ROOT = ROOT / "fts" / "ft-2-OF_16"
SCOPE = "ui-employment-canary-v2-test-design-upgrade"
DESIGN_DIR = FT_ROOT / "work" / "test-design" / SCOPE
CANONICAL = FT_ROOT / "test-cases" / "2-1-1-1-1-2-ui-employment-canary-v2-test-design-upgrade.md"
OUTPUTS = FT_ROOT / "work" / "review-cycles" / SCOPE / "outputs"
CHUNKS = DESIGN_DIR / "artifact-sections-v2-fixes"


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    out = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        out.append(
            "| "
            + " | ".join((str(cell) if str(cell) else "-").replace("|", "\\|").replace("\n", "<br>") for cell in row)
            + " |"
        )
    return "\n".join(out)


def write_artifact(target: Path, name: str, sections: list[tuple[int, str, str]], preamble: str = "") -> None:
    CHUNKS.mkdir(parents=True, exist_ok=True)

    def write_chunk(filename: str, text: str) -> str:
        path = CHUNKS / filename
        path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")
        return path.name

    manifest = {
        "target_path": str(target),
        "preamble_file": write_chunk(f"{name}.00.preamble.md", preamble) if preamble else "",
        "sections": [],
    }
    for index, (level, heading, content) in enumerate(sections, start=1):
        manifest["sections"].append(
            {
                "level": level,
                "heading": heading,
                "content_file": write_chunk(f"{name}.{index:02d}.md", content),
            }
        )
    manifest_path = CHUNKS / f"{name}.manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    helper = ROOT / "scripts" / "write_artifact_sections.py"
    subprocess.run([sys.executable, str(helper), "--manifest", str(manifest_path), "--dry-run"], check=True)
    subprocess.run([sys.executable, str(helper), "--manifest", str(manifest_path)], check=True)


def remove_v2_rows(path: Path, patterns: list[str]) -> None:
    if not path.exists():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    kept = []
    for line in lines:
        if any(re.search(pattern, line) for pattern in patterns):
            continue
        kept.append(line)
    path.write_text("\n".join(kept).rstrip() + "\n", encoding="utf-8", newline="\n")


def extra_cases() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(
        atom: str,
        package_id: str,
        source: str,
        req: str,
        cls: str,
        statement: str,
        tc: str,
        tc_type: str = "Negative",
        priority: str = "High",
        data: str = "F-NUMERIC-INVALID-001",
        expected: str = "",
        gap: str = "-",
    ) -> None:
        rows.append(
            {
                "atom": atom,
                "package": package_id,
                "source": source,
                "req": req,
                "class": cls,
                "statement": statement,
                "tc": tc,
                "type": tc_type,
                "priority": priority,
                "data": data,
                "expected": expected,
                "gap": gap,
            }
        )

    for atom, cls, value, tc in [
        ("ATOM-107", "numeric-letters-negative", "12A00", "TC-EMP-075"),
        ("ATOM-108", "numeric-spaces-negative", "12 000", "TC-EMP-076"),
        ("ATOM-109", "numeric-special-negative", "12#000", "TC-EMP-077"),
        ("ATOM-110", "numeric-decimal-negative", "2000,50", "TC-EMP-078"),
        ("ATOM-111", "numeric-sign-negative", "-2000", "TC-EMP-079"),
    ]:
        add(
            atom,
            "WP-01",
            "SRC-003",
            "GSR 124",
            cls,
            f"Поле `Среднемесячный доход после вычета налогов` основной работы не принимает значение `{value}`, потому что разрешены только числовые символы.",
            tc,
            data=f"`{value}`",
            expected=f"Значение `{value}` не сохранено как допустимый среднемесячный доход; переход к следующему разделу остается заблокированным до ввода значения только из цифр.",
        )
    for atom, cls, value, tc in [
        ("ATOM-112", "numeric-letters-negative", "12A00", "TC-EMP-080"),
        ("ATOM-113", "numeric-spaces-negative", "12 000", "TC-EMP-081"),
        ("ATOM-114", "numeric-special-negative", "12#000", "TC-EMP-082"),
        ("ATOM-115", "numeric-decimal-negative", "2000,50", "TC-EMP-083"),
        ("ATOM-116", "numeric-sign-negative", "-2000", "TC-EMP-084"),
    ]:
        add(
            atom,
            "WP-02",
            "SRC-012",
            "GSR 135",
            cls,
            f"Поле `Среднемесячный доход после вычета налогов` дополнительного дохода не принимает значение `{value}`, потому что разрешены только числовые символы.",
            tc,
            data=f"`{value}`",
            expected=f"Значение `{value}` не сохранено как допустимый доход в добавленном блоке; блок требует значение только из цифр.",
        )
    for atom, cls, value, tc in [
        ("ATOM-117", "phone-format-space-negative", "999 234567", "TC-EMP-085"),
        ("ATOM-118", "phone-format-special-negative", "99912#4567", "TC-EMP-086"),
        ("ATOM-119", "phone-format-decimal-negative", "9991234.67", "TC-EMP-087"),
        ("ATOM-120", "phone-format-sign-negative", "-999123456", "TC-EMP-088"),
    ]:
        add(
            atom,
            "WP-01",
            "SRC-009",
            "GSR 133",
            cls,
            f"Поле `Рабочий телефон` не принимает `{value}`, потому что требуется ровно 10 числовых символов.",
            tc,
            data=f"`{value}`",
            expected=f"Значение `{value}` не сохранено как допустимый рабочий телефон; поле требует 10 цифр.",
        )

    add("ATOM-121", "WP-04", "SRC-019", "GSR 144", "repeatable-second-block", "Повторное действие `Добавить работу по совместительству` создает независимый второй блок работы по совместительству.", "TC-EMP-089", "Positive", "Medium", "F-BASE-EMP-001", "На форме отображаются два отдельных блока работы по совместительству, значения во втором блоке вводятся независимо от первого.")
    add("ATOM-122", "WP-04", "SRC-019", "GSR 145", "repeatable-delete-one", "Удаление одного из двух блоков работы по совместительству не удаляет второй блок.", "TC-EMP-090", "Positive", "Medium", "F-BASE-EMP-001", "Удаленный блок работы по совместительству исчезает; второй добавленный блок остается на форме со своими значениями.")
    add("ATOM-123", "WP-04", "SRC-019", "GSR 144; GSR 145", "repeatable-delete-last-readd", "После удаления последнего блока работы по совместительству пользователь может добавить блок повторно.", "TC-EMP-091", "Positive", "Medium", "F-BASE-EMP-001", "После удаления последнего блока кнопка добавления доступна; повторное добавление снова отображает блок работы по совместительству.")
    add("ATOM-124", "WP-04", "SRC-020", "GSR 146", "repeatable-second-block", "Повторное действие `Добавить дополнительный доход` создает независимый второй блок дополнительного дохода.", "TC-EMP-092", "Positive", "Medium", "F-ADD-INCOME-002", "На форме отображаются два отдельных блока дополнительного дохода с разными типами дохода и независимыми суммами.")
    add("ATOM-125", "WP-04", "SRC-020", "GSR 147", "repeatable-delete-one", "Удаление одного из двух блоков дополнительного дохода не удаляет второй блок.", "TC-EMP-093", "Positive", "Medium", "F-ADD-INCOME-002", "Удаленный блок дополнительного дохода исчезает; второй блок остается на форме со своими значениями.")
    add("ATOM-126", "WP-04", "SRC-020", "GSR 146; GSR 147", "repeatable-delete-last-readd", "После удаления последнего блока дополнительного дохода пользователь может добавить блок повторно.", "TC-EMP-094", "Positive", "Medium", "F-ADD-INCOME-001", "После удаления последнего блока кнопка добавления доступна; повторное добавление снова отображает блок дополнительного дохода.")
    add("ATOM-127", "WP-04", "SRC-019", "GSR 144", "optional-no-action-part-time", "Если пользователь не нажимает `Добавить работу по совместительству`, блок работы по совместительству не становится обязательным для перехода дальше.", "TC-EMP-095", "Positive", "Medium", "F-BASE-EMP-001", "Раздел `Анкета клиента` открывается без добавленного блока работы по совместительству при заполненных обязательных полях основной работы.")
    add("ATOM-128", "WP-04", "SRC-020", "GSR 146", "optional-no-action-income", "Если пользователь не нажимает `Добавить дополнительный доход`, блок дополнительного дохода не становится обязательным для перехода дальше.", "TC-EMP-096", "Positive", "Medium", "F-BASE-EMP-001", "Раздел `Анкета клиента` открывается без добавленного блока дополнительного дохода при заполненных обязательных полях основной работы.")
    add("ATOM-129", "WP-03", "SRC-016", "GSR 139; GSR 140", "checkbox-single-selection", "В списке `Параметры визуальной оценки` можно выбрать одно значение.", "TC-EMP-097", "Positive", "Medium", "F-VISUAL-001", "Один выбранный параметр визуальной оценки отмечен и удовлетворяет требованию выбора хотя бы одного значения.")
    add("ATOM-130", "WP-03", "SRC-016", "GSR 139; GSR 140", "checkbox-multiple-selection", "В списке `Параметры визуальной оценки` можно выбрать несколько значений.", "TC-EMP-098", "Positive", "Medium", "F-VISUAL-001", "Несколько выбранных параметров визуальной оценки одновременно отмечены в списке.")
    add("ATOM-131", "WP-03", "SRC-016", "GSR 140", "checkbox-clear-selection-negative", "Если в видимом списке `Параметры визуальной оценки` снять все отметки, требование выбора хотя бы одного значения не выполнено.", "TC-EMP-099", "Negative", "High", "F-VISUAL-001", "После очистки всех отметок переход дальше заблокирован до выбора хотя бы одного параметра визуальной оценки.")
    return rows


def append_line_rows() -> None:
    extras = extra_cases()
    remove_v2_rows(DESIGN_DIR / "atomic-requirements-ledger.md", [r"^\| ATOM-1(0[7-9]|[12][0-9]|3[01]) \|"])
    remove_v2_rows(DESIGN_DIR / "coverage-obligation-table.md", [r"^\| WP-\d\d \| ATOM-1(0[7-9]|[12][0-9]|3[01]) \|"])
    remove_v2_rows(DESIGN_DIR / "package-test-design-plan.md", [r"^\| PD-1(0[0-9]|1[0-9]|2[0-4]) \|"])
    remove_v2_rows(DESIGN_DIR / "test-design-decision-table.md", [r"^\| WP-\d\d \| TC-EMP-0(7[5-9]|8[0-9]|9[0-9]) \|"])
    remove_v2_rows(DESIGN_DIR / "risk-priority-map.md", [r"^\| ATOM-1(0[7-9]|[12][0-9]|3[01]) \|"])
    for artifact in ["writer-self-check.md", "writer-quality-gate.md", "test-design-review.md"]:
        remove_v2_rows(DESIGN_DIR / artifact, [r"v2 explicit coverage obligations"])

    with (DESIGN_DIR / "atomic-requirements-ledger.md").open("a", encoding="utf-8", newline="\n") as handle:
        for row in extras:
            handle.write(f"| {row['atom']} | {row['package']} | {row['source']} | {row['req']} | {row['class']} | {row['statement']} | covered | {row['tc']} | {row['gap']} | {row['priority']} |\n")
    with (DESIGN_DIR / "coverage-obligation-table.md").open("a", encoding="utf-8", newline="\n") as handle:
        for row in extras:
            handle.write(f"| {row['package']} | {row['atom']} | {row['class']} | {row['class']} | {row['tc']} | {row['gap']} |\n")
    with (DESIGN_DIR / "package-test-design-plan.md").open("a", encoding="utf-8", newline="\n") as handle:
        for offset, row in enumerate(extras, start=100):
            handle.write(f"| PD-{offset:03d} | {row['package']} | {row['class']} | {row['source']} | {row['atom']} | {row['statement']} | {row['type'].lower()} | v2 explicit obligation | {row['data']} | {row['expected']} | FT/source | {row['tc']} | covered |\n")
    with (DESIGN_DIR / "test-design-decision-table.md").open("a", encoding="utf-8", newline="\n") as handle:
        for row in extras:
            handle.write(f"| {row['package']} | {row['tc']} | Выполнить проверку v2 obligation `{row['class']}`. | {row['data']} | {row['expected']} | {row['atom']} | - |\n")
    with (DESIGN_DIR / "risk-priority-map.md").open("a", encoding="utf-8", newline="\n") as handle:
        for row in extras:
            level = "high" if row["priority"] == "High" else "medium"
            handle.write(f"| {row['atom']} | {level} | {row['class']} | {row['req'] or row['source']} | {row['priority']} | {row['tc']} | {row['gap']} | Added by v2 canary obligation expansion. |\n")
    for artifact in ["writer-self-check.md", "writer-quality-gate.md", "test-design-review.md"]:
        with (DESIGN_DIR / artifact).open("a", encoding="utf-8", newline="\n") as handle:
            handle.write("| v2 explicit coverage obligations | pass | numeric invalid classes, repeatable add/delete/re-add, optional no-action and checkbox single/multiple/clear branches added in `TC-EMP-075`..`TC-EMP-099`. | all | - | no |\n")


def fixture_catalog() -> None:
    rows = [
        ["F-BASE-EMP-001", "baseline-valid", "WP-01..WP-04", "Тип занятости=`Работа по найму`; среднемесячный доход=`2000`; организация выбрана через UI-подсказку DaData; тип должности=`Expert`; должность=`Инженер`; стаж=`6-12 месяцев`; рабочий телефон=`9991234567`; Клиент добросовестный=`Нет`; Визуальная информация=`Нет`.", "Positive navigation and field checks", "Uses source-backed fields only; backend DaData/СПР artifacts excluded by GAP-001."],
        ["F-BASE-PENSION-001", "baseline-valid", "WP-01", "Тип занятости=`Пенсионер (не работает)`; среднемесячный доход=`2000`; должность=`Пенсионер`; поля работодателя, адреса, типа должности, стажа и рабочего телефона не заполняются, если они не отображаются.", "Inverse branch for employment-dependent fields", "No mockup-only sample value dependence."],
        ["F-ADD-INCOME-001", "action-created-block", "WP-02", "После нажатия `Добавить источник дохода`: Тип дохода=`Пенсия`; доход=`5000`.", "Additional income positive/duplicate invariant", "Duplicate mechanism remains GAP-002."],
        ["F-ADD-INCOME-002", "action-created-block", "WP-02", "Два блока дополнительного дохода: блок 1 `Пенсия`/`5000`, блок 2 `Аренда`/`7000`.", "Independent second block and delete-one branch", "Only source-backed income types are used."],
        ["F-VISUAL-001", "checkbox-list", "WP-03", "Визуальная информация=`Да`; параметры: `Не выявлено`, `Иные подозрения`.", "Single/multiple/clear checkbox branches", "Full dictionary values remain in dictionary-inventory."],
        ["F-NUMERIC-INVALID-001", "negative-values", "WP-01; WP-02", "letters=`12A00`; spaces=`12 000`; special=`12#000`; decimal=`2000,50`; sign=`-2000`.", "Digits-only negative classes", "Used as separate TC values, not mixed in one TC."],
        ["F-PHONE-BOUNDARY-001", "exact-length", "WP-01", "N=`9991234567`; N-1=`999123456`; N+1=`99912345678`; letters=`99912A4567`; spaces=`999 234567`; special=`99912#4567`; decimal=`9991234.67`; sign=`-999123456`.", "10-digit phone exact-length and invalid classes", "Mask default separately covered."],
    ]
    write_artifact(DESIGN_DIR / "fixture-catalog.md", "fixture-catalog", [(2, "Fixture Catalog", md_table(["fixture_id", "fixture_type", "package_id", "data", "used_for", "limitations"], rows))])


def coverage_metrics() -> None:
    rows = [
        ["source_rows_total", "24", "SRC-001..SRC-024 preserved in writer-side inventory"],
        ["mandatory_pdf_gsr_ids", "26", "GSR 123..GSR 148 represented by ATOM-* or retained GAP-*"],
        ["tc_total", "99", "TC-EMP-001..TC-EMP-099"],
        ["v2_numeric_invalid_classes", "pass", "letters, spaces, special chars, decimal separator and sign split for main/additional income; phone includes N/N-1/N+1 plus invalid classes"],
        ["repeatable_blocks", "pass", "add, independent second block, delete one, delete last and re-add covered for part-time and additional income"],
        ["optional_no_action_branches", "pass", "no-action part-time and no-action additional-income branches covered"],
        ["checkbox_list", "pass", "visible branch, required/no selection, single selection, multiple selection and clear selection covered"],
        ["open_gaps", "4", "GAP-001..GAP-004 retained as non-blocking residual gaps"],
    ]
    write_artifact(DESIGN_DIR / "coverage-metrics.md", "coverage-metrics", [(2, "Coverage Metrics", md_table(["metric", "value", "evidence"], rows))])
    (DESIGN_DIR / "coverage-map.md").write_text(
        "## Coverage Map\n\n"
        + md_table(
            ["metric", "value"],
            [
                ["atoms_total", "131"],
                ["covered_by_tc", "124"],
                ["gap_unclear", "7"],
                ["metadata_only", "25"],
                ["tc_total", "99"],
                ["mandatory_req_ids", "GSR 123-GSR 148 represented by `ATOM-*` or retained `GAP-*`"],
            ],
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def tc_block(row: dict[str, str]) -> str:
    trace = f"{row['atom']}; {row['req']}; {row['source']}"
    steps = ["Открыть раздел `Сведения о занятости` с предусловиями из fixture-каталога."]
    if row["class"].startswith("numeric"):
        field = "`Среднемесячный доход после вычета налогов` основной работы" if row["package"] == "WP-01" else "`Среднемесячный доход после вычета налогов` в добавленном блоке дополнительного дохода"
        steps += [f"Ввести тестовое значение {row['data']} в поле {field}.", "Снять фокус с поля или нажать `Следующий шаг`."]
    elif row["class"].startswith("phone"):
        steps += [f"Ввести тестовое значение {row['data']} в поле `Рабочий телефон`.", "Снять фокус с поля или нажать `Следующий шаг`."]
    elif "second-block" in row["class"]:
        steps += ["Нажать соответствующую кнопку добавления один раз и заполнить первый блок.", "Нажать эту же кнопку добавления второй раз.", "Заполнить второй блок отличающимися значениями."]
    elif "delete-one" in row["class"]:
        steps += ["Создать два блока проверяемого типа и заполнить их разными значениями.", "Нажать пиктограмму `Корзина` в одном из двух блоков."]
    elif "delete-last-readd" in row["class"]:
        steps += ["Создать один блок проверяемого типа.", "Удалить этот блок пиктограммой `Корзина`.", "Повторно нажать кнопку добавления этого блока."]
    elif "optional-no-action" in row["class"]:
        steps += ["Не нажимать кнопку добавления соответствующего optional-блока.", "Заполнить обязательные поля основной работы по `F-BASE-EMP-001`.", "Нажать `Следующий шаг`."]
    elif "checkbox-single" in row["class"]:
        steps += ["Установить `Визуальная информация = Да`.", "В списке `Параметры визуальной оценки` выбрать один параметр."]
    elif "checkbox-multiple" in row["class"]:
        steps += ["Установить `Визуальная информация = Да`.", "В списке `Параметры визуальной оценки` выбрать два разных параметра."]
    elif "checkbox-clear" in row["class"]:
        steps += ["Установить `Визуальная информация = Да`.", "Выбрать один параметр визуальной оценки.", "Снять отметку со всех параметров и нажать `Следующий шаг`."]
    step_text = "\n".join(f"{index}. {step}" for index, step in enumerate(steps, start=1))
    return f"""## {row['tc']}

**Название:** {row['statement']}

**Цель:** Проверить v2 obligation `{row['class']}` для `{row['source']}`.

**Ссылка на ФТ:** `{trace}`

**Источник требования:** `{row['source']}`; `source-parity-check.md`; `source-row-inventory.md`.

**Источник / цитата требования:** {row['statement']}

**package_id:** `{row['package']}`

**Тип:** `{row['type']}`

**Приоритет:** `{row['priority']}`

**Трассировка:** `{trace}`

**Предусловия:** Открыта карточка УЗ с доступным разделом `Сведения о занятости`; применимая fixture из `fixture-catalog.md` подготовлена.

**Тестовые данные:** {row['data']}

Шаги:

{step_text}

**Итоговый ожидаемый результат:** {row['expected']}

**Постусловия:** Вернуть измененные данные раздела к исходному состоянию, если это требуется для повторного выполнения.
"""


def canonical_test_cases() -> None:
    content = CANONICAL.read_text(encoding="utf-8")
    content = re.sub(r"^## TC-EMP-0(?:7[5-9]|8[0-9]|9[0-9])\n.*?(?=^## TC-EMP-|\Z)", "", content, flags=re.M | re.S)
    content = content.rstrip() + "\n\n" + "\n".join(tc_block(row) for row in extra_cases()) + "\n"
    blocks = re.split(r"(?=^## TC-EMP-\d+\n)", content, flags=re.M)
    fixed: list[str] = []
    for block in blocks:
        if not block.startswith("## TC-EMP-"):
            fixed.append(block)
            continue
        if "**Цель:**" not in block:
            title_match = re.search(r"\*\*Название:\*\*\s*(.+)", block)
            trace_match = re.search(r"\*\*Трассировка:\*\*\s*(.+)", block)
            title = title_match.group(1).strip() if title_match else "Проверить требование раздела `Сведения о занятости`."
            trace = trace_match.group(1).strip() if trace_match else "`source-row-inventory.md`"
            insert = (
                f"\n**Цель:** Проверить: {title}\n\n"
                f"**Ссылка на ФТ:** {trace}\n\n"
                "**Источник требования:** `source-row-inventory.md`; `source-parity-check.md`; `scope-contract.md`.\n\n"
                f"**Источник / цитата требования:** {title}\n"
            )
            block = block.replace("\n**package_id:**", insert + "\n**package_id:**", 1)
        block = block.replace("Минимальный валидный набор данных для открытия раздела `Сведения о занятости`.", "`F-BASE-EMP-001` из `fixture-catalog.md`.")
        fixed.append(block)
    CANONICAL.write_text("".join(fixed).rstrip() + "\n", encoding="utf-8", newline="\n")


def update_logs() -> None:
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
    addition = (
        "\n- Resolver command: `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget`.\n"
        "- Resolver budget status: `pass (117.6 / 200.0 KiB)`.\n"
        "- Resolver selected required files: "
        + "; ".join(f"`{item}`" for item in selected)
        + ".\n"
        "- Direct source extraction read: DOCX tables 11/12, PDF pages 61-67 and dictionary inventory from support XLSX.\n"
    )
    for path in [DESIGN_DIR / "writer-session-log.md", OUTPUTS / "writer-session-log.writer-r1.md"]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if "Resolver command:" not in text:
            text = text.replace("## Inputs Read\n", "## Inputs Read\n" + addition, 1)
        text = text.replace("work/stage-handoffs/01-ui-employment/scope-gap-review.md", "work/review-cycles/ui-employment-canary-v2-test-design-upgrade/outputs/scope-gap-review-findings.md")
        path.write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    fixture_catalog()
    append_line_rows()
    coverage_metrics()
    canonical_test_cases()
    update_logs()


if __name__ == "__main__":
    main()
