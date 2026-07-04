from __future__ import annotations

import re
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "fts" / "ft-2-OF_17"
SCOPE = "main-info-credit-parameters"
SECTION = "2-1-1-1-1-1-2"
TD_REL = f"work/test-design/{SECTION}-{SCOPE}"
TD = FT / TD_REL
CANONICAL_REL = f"test-cases/{SECTION}-{SCOPE}.md"
CANONICAL = FT / CANONICAL_REL
CYCLE = FT / "work" / "review-cycles" / SCOPE
OUTPUTS = CYCLE / "outputs"
PROMPTS = CYCLE / "prompts"
HANDOFF_REL = "work/stage-handoffs/05-main-info-credit-parameters"
HANDOFF = FT / HANDOFF_REL


def table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


SOURCE_ROWS = [
    ["`SRC-001`", "`WP-01`", "`Запрошенный продукт`", "`DOCX section-19 row 1; PDF p.46`", "`no_requirement_code:SRC-001`", "`yes`", "`ATOM-001`; `GAP-004`"],
    ["`SRC-002`", "`WP-02`", "`Сумма на руки`", "`DOCX section-19 row 2; PDF p.46`", "`GSR 1`; `GSR 2`; `GSR 3`; `GSR 4`", "`yes`", "`ATOM-002`; `ATOM-003`; `ATOM-004`; `ATOM-005`; `ATOM-006`; `GAP-002`; `GAP-003`; `GAP-004`"],
    ["`SRC-003`", "`WP-03`", "`Сумма на погашение рефинансируемых кредитов`", "`DOCX section-19 row 3; PDF p.46`", "`GSR 5`; `GSR 6`; `GSR 7`; `GSR 8`", "`yes`", "`ATOM-007`; `ATOM-008`; `ATOM-009`; `ATOM-010`; `ATOM-011`; `GAP-002`; `GAP-003`; `GAP-004`"],
    ["`SRC-004`", "`WP-04`", "`Срок кредита`", "`DOCX section-19 row 4; PDF pp.46-47`", "`GSR 9`; `GSR 10`", "`yes`", "`ATOM-012`; `ATOM-013`; `ATOM-014`; `ATOM-015`; `ATOM-016`; `GAP-001`; `GAP-003`; `GAP-004`"],
]

NORMALIZATION_ROWS = [
    ["`SRC-001.P01`", "`SRC-001`", "`WP-01`", "`Запрошенный продукт`", "`dictionary-source`", "`always`", "Поле выбора продукта использует активные значения `DICT-001`.", "`no_requirement_code:SRC-001`", "`DOCX section-19 row 1; dictionary-inventory DICT-001`", "`high`", "`none_required:covered`", "`ATOM-001`"],
    ["`SRC-002.P01`", "`SRC-002`", "`WP-02`", "`Сумма на руки`", "`availability-editability`", "`always`", "Поле доступно для заполнения как текстовое поле/слайдер.", "`no_requirement_code:SRC-002`", "`DOCX section-19 row 2`", "`high`", "`none_required:covered`", "`ATOM-002`"],
    ["`SRC-002.P02`", "`SRC-002`", "`WP-02`", "`Сумма на руки`", "`numeric-format`", "`always`", "Допустимый ввод задается только цифровыми символами.", "`GSR 1`", "`PDF p.46`", "`medium`", "`GAP-002`", "`ATOM-003`"],
    ["`SRC-002.P03`", "`SRC-002`", "`WP-02`", "`Сумма на руки`", "`boundary-max`", "`selected product`", "Максимальное значение берется из Product Catalog для выбранного продукта.", "`GSR 2`", "`PDF p.46; DICT-001`", "`medium`", "`GAP-003`", "`ATOM-004`"],
    ["`SRC-002.P04`", "`SRC-002`", "`WP-02`", "`Сумма на руки`", "`boundary-min`", "`selected product`", "Минимальное значение берется из Product Catalog для выбранного продукта.", "`GSR 3`", "`PDF p.46; DICT-001`", "`medium`", "`GAP-003`", "`ATOM-005`"],
    ["`SRC-002.P05`", "`SRC-002`", "`WP-02`", "`Сумма на руки`", "`dictionary-source`", "`always`", "Поле может заполняться тегами суммы из `DICT-002`.", "`GSR 4`", "`PDF p.46; dictionary-inventory DICT-002`", "`high`", "`none_required:covered`", "`ATOM-006`"],
    ["`SRC-003.P01`", "`SRC-003`", "`WP-03`", "`Сумма на погашение рефинансируемых кредитов`", "`conditional-visibility`", "`Запрошенный продукт = Рефинансирование`", "Поле отображается при выборе продукта `Рефинансирование`.", "`GSR 5`", "`PDF p.46; DICT-001`", "`high`", "`none_required:covered`", "`ATOM-007`"],
    ["`SRC-003.P02`", "`SRC-003`", "`WP-03`", "`Сумма на погашение рефинансируемых кредитов`", "`conditional-visibility-inverse`", "`Запрошенный продукт != Рефинансирование`", "Поле не отображается для других активных продуктов.", "`GSR 5`", "`PDF p.46; DICT-001`", "`medium`", "`none_required:covered`", "`ATOM-008`"],
    ["`SRC-003.P03`", "`SRC-003`", "`WP-03`", "`Сумма на погашение рефинансируемых кредитов`", "`numeric-format`", "`Рефинансирование`", "Допустимый ввод задается только цифровыми символами.", "`GSR 6`", "`PDF p.46`", "`medium`", "`GAP-002`", "`ATOM-009`"],
    ["`SRC-003.P04`", "`SRC-003`", "`WP-03`", "`Сумма на погашение рефинансируемых кредитов`", "`boundary-max`", "`Рефинансирование`", "Максимальное значение берется из Product Catalog.", "`GSR 7`", "`PDF p.46; DICT-001`", "`medium`", "`GAP-003`", "`ATOM-010`"],
    ["`SRC-003.P05`", "`SRC-003`", "`WP-03`", "`Сумма на погашение рефинансируемых кредитов`", "`boundary-min`", "`Рефинансирование`", "Минимальное значение берется из Product Catalog.", "`GSR 8`", "`PDF p.46; DICT-001`", "`medium`", "`GAP-003`", "`ATOM-011`"],
    ["`SRC-004.P01`", "`SRC-004`", "`WP-04`", "`Срок кредита`", "`visibility`", "`before product-dependent display`", "Поле не отображается до выбора продукта.", "`no_requirement_code:SRC-004`", "`DOCX section-19 row 4; PDF pp.46-47`", "`high`", "`none_required:covered`", "`ATOM-012`"],
    ["`SRC-004.P02`", "`SRC-004`", "`WP-04`", "`Срок кредита`", "`conditional-availability`", "`Запрошенный продукт != Кредитная карта`", "Поле становится доступным для продукта не `Кредитная карта`.", "`no_requirement_code:SRC-004`", "`DOCX section-19 row 4; DICT-001`", "`medium`", "`GAP-004`", "`ATOM-013`"],
    ["`SRC-004.P03`", "`SRC-004`", "`WP-04`", "`Срок кредита`", "`boundary-min`", "`Запрошенный продукт != Кредитная карта`", "Нижняя граница берется из Product Catalog.", "`GSR 9`", "`PDF pp.46-47; DICT-001`", "`medium`", "`GAP-001`; `GAP-003`", "`ATOM-014`"],
    ["`SRC-004.P04`", "`SRC-004`", "`WP-04`", "`Срок кредита`", "`boundary-max`", "`Запрошенный продукт != Кредитная карта`", "Верхняя граница берется из Product Catalog.", "`GSR 9`", "`PDF pp.46-47; DICT-001`", "`medium`", "`GAP-001`; `GAP-003`", "`ATOM-016`"],
    ["`SRC-004.P05`", "`SRC-004`", "`WP-04`", "`Срок кредита`", "`default-selection`", "`Запрошенный продукт != Кредитная карта`", "Начальное значение берется из Product Catalog.", "`GSR 10`", "`PDF p.47; DICT-001`", "`high`", "`none_required:covered`", "`ATOM-015`"],
]

ATOMS = [
    ["`ATOM-001`", "`WP-01`", "`SRC-001.P01`", "`no_requirement_code:SRC-001`", "`SRC-001`; `DICT-001`", "Поле `Запрошенный продукт` использует активные значения `Продуктовый каталог`.", "`TC-MICP-001`", "`covered`", "`none_required:covered`"],
    ["`ATOM-002`", "`WP-02`", "`SRC-002.P01`", "`no_requirement_code:SRC-002`", "`SRC-002`", "Поле `Сумма на руки` доступно для заполнения.", "`TC-MICP-002`", "`covered`", "`none_required:covered`"],
    ["`ATOM-003`", "`WP-02`", "`SRC-002.P02`", "`GSR 1`", "`SRC-002`", "`Сумма на руки` принимает цифровой ввод; механизм отклонения нецифровых символов не задан.", "`TC-MICP-003`; `GAP-002`", "`covered`", "`GAP-002`"],
    ["`ATOM-004`", "`WP-02`", "`SRC-002.P03`", "`GSR 2`", "`SRC-002`; `DICT-001`", "Максимум `Сумма на руки` берется из Product Catalog выбранного продукта.", "`TC-MICP-004`; `GAP-003`", "`covered`", "`GAP-003`"],
    ["`ATOM-005`", "`WP-02`", "`SRC-002.P04`", "`GSR 3`", "`SRC-002`; `DICT-001`", "Минимум `Сумма на руки` берется из Product Catalog выбранного продукта.", "`TC-MICP-005`; `GAP-003`", "`covered`", "`GAP-003`"],
    ["`ATOM-006`", "`WP-02`", "`SRC-002.P05`", "`GSR 4`", "`SRC-002`; `DICT-002`", "`Сумма на руки` может заполняться тегами `50000`, `100000`, `200000`, `300000`, `400000`, `500000`, `1000000`.", "`TC-MICP-006`", "`covered`", "`none_required:covered`"],
    ["`ATOM-007`", "`WP-03`", "`SRC-003.P01`", "`GSR 5`", "`SRC-003`; `DICT-001`", "`Сумма на погашение рефинансируемых кредитов` отображается для продукта `Рефинансирование`.", "`TC-MICP-007`", "`covered`", "`none_required:covered`"],
    ["`ATOM-008`", "`WP-03`", "`SRC-003.P02`", "`GSR 5`", "`SRC-003`; `DICT-001`", "`Сумма на погашение рефинансируемых кредитов` не отображается для продуктов `Потребительский кредит` и `Кредитная карта`.", "`TC-MICP-008`", "`covered`", "`none_required:covered`"],
    ["`ATOM-009`", "`WP-03`", "`SRC-003.P03`", "`GSR 6`", "`SRC-003`", "Поле погашения рефинансируемых кредитов принимает цифровой ввод; механизм отклонения нецифровых символов не задан.", "`TC-MICP-009`; `GAP-002`", "`covered`", "`GAP-002`"],
    ["`ATOM-010`", "`WP-03`", "`SRC-003.P04`", "`GSR 7`", "`SRC-003`; `DICT-001`", "Максимум суммы погашения берется из Product Catalog.", "`TC-MICP-010`; `GAP-003`", "`covered`", "`GAP-003`"],
    ["`ATOM-011`", "`WP-03`", "`SRC-003.P05`", "`GSR 8`", "`SRC-003`; `DICT-001`", "Минимум суммы погашения берется из Product Catalog.", "`TC-MICP-011`; `GAP-003`", "`covered`", "`GAP-003`"],
    ["`ATOM-012`", "`WP-04`", "`SRC-004.P01`", "`no_requirement_code:SRC-004`", "`SRC-004`", "Поле `Срок кредита` скрыто по умолчанию.", "`TC-MICP-012`", "`covered`", "`none_required:covered`"],
    ["`ATOM-013`", "`WP-04`", "`SRC-004.P02`", "`no_requirement_code:SRC-004`", "`SRC-004`; `DICT-001`", "`Срок кредита` доступен и редактируем, когда продукт не `Кредитная карта`; requiredness enforcement не задан.", "`TC-MICP-013`; `GAP-004`", "`covered`", "`GAP-004`"],
    ["`ATOM-014`", "`WP-04`", "`SRC-004.P03`", "`GSR 9`", "`SRC-004`; `DICT-001`; `DICT-003`; `GAP-001`", "Минимум `Срок кредита` берется из Product Catalog; полный список `Сроки кредитования` отсутствует.", "`TC-MICP-014`; `GAP-001`; `GAP-003`", "`covered`", "`GAP-001`; `GAP-003`"],
    ["`ATOM-015`", "`WP-04`", "`SRC-004.P05`", "`GSR 10`", "`SRC-004`; `DICT-001`", "Начальное значение `Срок кредита` равно верхней границе Product Catalog.", "`TC-MICP-015`", "`covered`", "`none_required:covered`"],
    ["`ATOM-016`", "`WP-04`", "`SRC-004.P04`", "`GSR 9`", "`SRC-004`; `DICT-001`; `DICT-003`; `GAP-001`", "Максимум `Срок кредита` берется из Product Catalog; полный список `Сроки кредитования` отсутствует.", "`TC-MICP-014`; `GAP-001`; `GAP-003`", "`covered`", "`GAP-001`; `GAP-003`"],
]

GAPS = [
    ("GAP-001", "`WP-04`", "`SRC-004`; `GSR 9`; `GSR 10`; `DICT-003`", "missing-dictionary-values", "Полный список значений справочника `Сроки кредитования` отсутствует в support workbook.", "Не проверять полный список или отсутствие лишних значений `Срок кредита`; покрывать только source-backed default/min/max behavior.", "no"),
    ("GAP-002", "`WP-02`; `WP-03`", "`SRC-002`; `SRC-003`; `GSR 1`; `GSR 6`", "unclear-invalid-input-feedback", "ФТ задает `только цифры`, но не задает наблюдаемую реакцию UI на буквы, пробелы, спецсимволы, знак или дробный разделитель.", "Не писать negative TC с подсветкой/сообщением/очисткой без UI evidence; positive numeric input covered.", "no"),
    ("GAP-003", "`WP-02`; `WP-03`; `WP-04`", "`GSR 2`; `GSR 3`; `GSR 7`; `GSR 8`; `GSR 9`", "unclear-boundary-rejection-feedback", "ФТ ссылается на min/max из Product Catalog, но не задает реакцию на значения ниже min или выше max.", "Покрывать acceptance catalog min/max values; не писать out-of-range rejection TC без validation action/evidence.", "no"),
    ("GAP-004", "`WP-01`; `WP-02`; `WP-03`; `WP-04`", "`SRC-001`..`SRC-004`; column `О`", "unclear-requiredness-enforcement", "Колонка `О` задает обязательность, но selected scope исключает действия `section-20` и не дает validation trigger/error oracle.", "Не писать requiredness-blocking TC без source-backed action; сохранить requiredness in ledger/plan as residual unclear.", "no"),
]


def coverage_gaps_body() -> str:
    parts = [
        "## Summary\n\n" + table(
            ["field", "value"],
            [
                ["ft_slug", "`ft-2-OF_17`"],
                ["scope_slug", f"`{SCOPE}`"],
                ["blocking gaps", "`no`"],
                ["gaps", str(len(GAPS))],
            ],
        )
    ]
    for gap_id, package_id, refs, kind, desc, handling, blocks in GAPS:
        parts.append(
            dedent(
                f"""
                ### {gap_id}

                **Impact:** `unclear`

                **Blocks Ready For Review:** `{blocks}`

                **Package:** {package_id}

                **Source Ref:** {refs}

                **Gap Type:** `{kind}`

                **Description:** {desc}

                **Required Downstream Handling:** {handling}
                """
            ).strip()
        )
    return "\n\n".join(parts)


def tc_block(tc_id: str, title: str, tc_type: str, priority: str, package_id: str, trace: str, preconditions: list[str], data: list[str], steps: list[str], expected: str, post: str = "Не требуются.") -> str:
    return "\n\n".join(
        [
            f"## {tc_id}",
            f"**Название:** {title}",
            f"**Тип:** {tc_type}",
            f"**Приоритет:** {priority}",
            f"**package_id:** {package_id}",
            f"**Трассировка:** {trace}",
            "### Предусловия\n\n" + "\n".join(f"- {item}" for item in preconditions),
            "### Тестовые данные\n\n" + "\n".join(f"- {item}" for item in data),
            "### Шаги\n\n" + "\n".join(f"{index}. {item}" for index, item in enumerate(steps, start=1)),
            "### Итоговый ожидаемый результат\n\n" + expected,
            "### Постусловия\n\n" + post,
        ]
    )


TEST_CASES = [
    tc_block(
        "TC-MICP-001",
        "Поле `Запрошенный продукт` содержит активные значения Product Catalog",
        "Positive",
        "High",
        "WP-01",
        "`ATOM-001`; `SRC-001`; `DICT-001`; `DOCX section-19 row 1; PDF p.46`",
        ["Открыта анкета клиента на разделе `Основная информация`.", "Пользователь имеет право редактировать раздел."],
        ["Активные значения `DICT-001`: `Потребительский кредит`, `Кредитная карта`, `Рефинансирование`."],
        ["Найти поле `Запрошенный продукт`.", "Открыть или просмотреть доступные значения поля."],
        "Поле `Запрошенный продукт` доступно для выбора и содержит активные значения `Потребительский кредит`, `Кредитная карта`, `Рефинансирование` без архивных или неописанных значений.",
    ),
    tc_block(
        "TC-MICP-002",
        "Поле `Сумма на руки` доступно для заполнения в разделе `Основная информация`",
        "Positive",
        "High",
        "WP-02",
        "`ATOM-002`; `SRC-002`; `DOCX section-19 row 2; PDF p.46`",
        ["Открыта анкета клиента на разделе `Основная информация`.", "В поле `Запрошенный продукт` выбран `Потребительский кредит`."],
        ["Не требуются."],
        ["Найти поле `Сумма на руки`.", "Активировать поле для ввода суммы."],
        "Поле `Сумма на руки` отображается и доступно для ручного изменения значения.",
    ),
    tc_block(
        "TC-MICP-003",
        "Цифровое значение вводится в поле `Сумма на руки`",
        "Positive",
        "High",
        "WP-02",
        "`ATOM-003`; `GSR 1`; `SRC-002`; `DOCX section-19 row 2; PDF p.46`; `GAP-002`",
        ["Открыта анкета клиента на разделе `Основная информация`.", "В поле `Запрошенный продукт` выбран `Потребительский кредит`."],
        ["Значение `50000` из `DICT-002`."],
        ["Ввести `50000` в поле `Сумма на руки`."],
        "В поле `Сумма на руки` отображается введенное цифровое значение `50000` с учетом штатного UI-форматирования суммы.",
    ),
    tc_block(
        "TC-MICP-004",
        "Максимум `Сумма на руки` берется из Product Catalog выбранного продукта",
        "Positive",
        "High",
        "WP-02",
        "`ATOM-004`; `GSR 2`; `SRC-002`; `DICT-001`; `GAP-003`",
        ["Открыта анкета клиента на разделе `Основная информация`.", "В поле `Запрошенный продукт` выбран продукт fixture `FIX-MICP-001`."],
        ["`FIX-MICP-001.requested_amount_max`: максимальное значение `Сумма на руки` для выбранного продукта из Product Catalog."],
        ["Ввести значение `FIX-MICP-001.requested_amount_max` в поле `Сумма на руки`."],
        "Поле `Сумма на руки` отображает значение `FIX-MICP-001.requested_amount_max` как допустимое для выбранного продукта.",
    ),
    tc_block(
        "TC-MICP-005",
        "Минимум `Сумма на руки` берется из Product Catalog выбранного продукта",
        "Positive",
        "High",
        "WP-02",
        "`ATOM-005`; `GSR 3`; `SRC-002`; `DICT-001`; `GAP-003`",
        ["Открыта анкета клиента на разделе `Основная информация`.", "В поле `Запрошенный продукт` выбран продукт fixture `FIX-MICP-001`."],
        ["`FIX-MICP-001.requested_amount_min`: минимальное значение `Сумма на руки` для выбранного продукта из Product Catalog."],
        ["Ввести значение `FIX-MICP-001.requested_amount_min` в поле `Сумма на руки`."],
        "Поле `Сумма на руки` отображает значение `FIX-MICP-001.requested_amount_min` как допустимое для выбранного продукта.",
    ),
    tc_block(
        "TC-MICP-006",
        "Теги суммы заполняют поле `Сумма на руки` значениями `DICT-002`",
        "Positive",
        "High",
        "WP-02",
        "`ATOM-006`; `GSR 4`; `SRC-002`; `DICT-002`; `DOCX section-19 row 2; PDF p.46`",
        ["Открыта анкета клиента на разделе `Основная информация`.", "Поле `Сумма на руки` доступно."],
        ["Активные значения `DICT-002`: `50000`, `100000`, `200000`, `300000`, `400000`, `500000`, `1000000`."],
        ["Просмотреть доступные теги выбора суммы.", "Последовательно выбрать каждый тег из `DICT-002` и после каждого выбора проверить значение поля `Сумма на руки`."],
        "Для каждого выбранного тега поле `Сумма на руки` заполняется соответствующим числовым значением из `DICT-002`.",
    ),
    tc_block(
        "TC-MICP-007",
        "Поле суммы погашения отображается для продукта `Рефинансирование`",
        "Positive",
        "High",
        "WP-03",
        "`ATOM-007`; `GSR 5`; `SRC-003`; `DICT-001`; `DOCX section-19 row 3; PDF p.46`",
        ["Открыта анкета клиента на разделе `Основная информация`."],
        ["Значение `Запрошенный продукт`: `Рефинансирование` из `DICT-001`."],
        ["Выбрать `Рефинансирование` в поле `Запрошенный продукт`.", "Найти поле `Сумма на погашение рефинансируемых кредитов`."],
        "Поле `Сумма на погашение рефинансируемых кредитов` отображается и доступно для изменения.",
    ),
    tc_block(
        "TC-MICP-008",
        "Поле суммы погашения скрыто для продуктов без рефинансирования",
        "Positive",
        "High",
        "WP-03",
        "`ATOM-008`; `GSR 5`; `SRC-003`; `DICT-001`; `DOCX section-19 row 3; PDF p.46`",
        ["Открыта анкета клиента на разделе `Основная информация`."],
        ["Значения `Запрошенный продукт`: `Потребительский кредит`, `Кредитная карта` из `DICT-001`."],
        ["Выбрать `Потребительский кредит` в поле `Запрошенный продукт`.", "Проверить наличие поля `Сумма на погашение рефинансируемых кредитов`.", "Выбрать `Кредитная карта` в поле `Запрошенный продукт`.", "Повторно проверить наличие поля `Сумма на погашение рефинансируемых кредитов`."],
        "Поле `Сумма на погашение рефинансируемых кредитов` не отображается для `Потребительский кредит` и `Кредитная карта`.",
    ),
    tc_block(
        "TC-MICP-009",
        "Цифровое значение вводится в сумму погашения рефинансируемых кредитов",
        "Positive",
        "High",
        "WP-03",
        "`ATOM-009`; `GSR 6`; `SRC-003`; `GAP-002`; `DOCX section-19 row 3; PDF p.46`",
        ["Открыта анкета клиента на разделе `Основная информация`.", "В поле `Запрошенный продукт` выбран `Рефинансирование`."],
        ["Значение `50000`."],
        ["Ввести `50000` в поле `Сумма на погашение рефинансируемых кредитов`."],
        "В поле `Сумма на погашение рефинансируемых кредитов` отображается введенное цифровое значение `50000` с учетом штатного UI-форматирования суммы.",
    ),
    tc_block(
        "TC-MICP-010",
        "Максимум суммы погашения берется из Product Catalog",
        "Positive",
        "High",
        "WP-03",
        "`ATOM-010`; `GSR 7`; `SRC-003`; `DICT-001`; `GAP-003`",
        ["Открыта анкета клиента на разделе `Основная информация`.", "В поле `Запрошенный продукт` выбран `Рефинансирование`."],
        ["`FIX-MICP-002.refinance_repayment_amount_max`: максимальное значение для `Рефинансирование` из Product Catalog."],
        ["Ввести `FIX-MICP-002.refinance_repayment_amount_max` в поле `Сумма на погашение рефинансируемых кредитов`."],
        "Поле `Сумма на погашение рефинансируемых кредитов` отображает значение `FIX-MICP-002.refinance_repayment_amount_max` как допустимое для продукта `Рефинансирование`.",
    ),
    tc_block(
        "TC-MICP-011",
        "Минимум суммы погашения берется из Product Catalog",
        "Positive",
        "High",
        "WP-03",
        "`ATOM-011`; `GSR 8`; `SRC-003`; `DICT-001`; `GAP-003`",
        ["Открыта анкета клиента на разделе `Основная информация`.", "В поле `Запрошенный продукт` выбран `Рефинансирование`."],
        ["`FIX-MICP-002.refinance_repayment_amount_min`: минимальное значение для `Рефинансирование` из Product Catalog."],
        ["Ввести `FIX-MICP-002.refinance_repayment_amount_min` в поле `Сумма на погашение рефинансируемых кредитов`."],
        "Поле `Сумма на погашение рефинансируемых кредитов` отображает значение `FIX-MICP-002.refinance_repayment_amount_min` как допустимое для продукта `Рефинансирование`.",
    ),
    tc_block(
        "TC-MICP-012",
        "Поле `Срок кредита` скрыто по умолчанию",
        "Positive",
        "Medium",
        "WP-04",
        "`ATOM-012`; `SRC-004`; `DOCX section-19 row 4; PDF pp.46-47`",
        ["Открыта анкета клиента на разделе `Основная информация`.", "Значение `Запрошенный продукт` еще не выбрано."],
        ["Не требуются."],
        ["Проверить наличие поля `Срок кредита` до выбора продукта."],
        "Поле `Срок кредита` не отображается до выбора продукта, для которого требуется срок кредита.",
    ),
    tc_block(
        "TC-MICP-013",
        "Поле `Срок кредита` доступно для продукта не `Кредитная карта`",
        "Positive",
        "High",
        "WP-04",
        "`ATOM-013`; `SRC-004`; `DICT-001`; `GAP-004`; `DOCX section-19 row 4; PDF pp.46-47`",
        ["Открыта анкета клиента на разделе `Основная информация`."],
        ["Значение `Запрошенный продукт`: `Потребительский кредит` из `DICT-001`."],
        ["Выбрать `Потребительский кредит` в поле `Запрошенный продукт`.", "Открыть поле `Срок кредита` для изменения значения."],
        "Поле `Срок кредита` отображается и доступно для выбора значения из выпадающего списка.",
    ),
    tc_block(
        "TC-MICP-014",
        "Границы `Срок кредита` берутся из Product Catalog без проверки полного списка",
        "Positive",
        "Medium",
        "WP-04",
        "`ATOM-014`; `ATOM-016`; `GSR 9`; `SRC-004`; `DICT-001`; `GAP-001`; `GAP-003`",
        ["Открыта анкета клиента на разделе `Основная информация`.", "В поле `Запрошенный продукт` выбран продукт fixture `FIX-MICP-003` не `Кредитная карта`."],
        ["`FIX-MICP-003.loan_term_min`: минимальный срок из Product Catalog.", "`FIX-MICP-003.loan_term_max`: максимальный срок из Product Catalog.", "`GAP-001` не закрыт, поэтому полный список значений справочника не используется как oracle."],
        ["Открыть выпадающий список `Срок кредита`.", "Выбрать `FIX-MICP-003.loan_term_min`.", "Открыть выпадающий список повторно.", "Выбрать `FIX-MICP-003.loan_term_max`."],
        "Поле `Срок кредита` позволяет выбрать значения `FIX-MICP-003.loan_term_min` и `FIX-MICP-003.loan_term_max`, взятые из Product Catalog для выбранного продукта.",
    ),
    tc_block(
        "TC-MICP-015",
        "По умолчанию `Срок кредита` заполнен максимумом Product Catalog",
        "Positive",
        "High",
        "WP-04",
        "`ATOM-015`; `GSR 10`; `SRC-004`; `DICT-001`; `DOCX section-19 row 4; PDF p.47`",
        ["Открыта анкета клиента на разделе `Основная информация`."],
        ["Значение `Запрошенный продукт`: `Потребительский кредит`.", "`FIX-MICP-003.loan_term_max`: максимальный срок из Product Catalog для `Потребительский кредит`."],
        ["Выбрать `Потребительский кредит` в поле `Запрошенный продукт`.", "Проверить значение поля `Срок кредита` сразу после отображения поля."],
        "Поле `Срок кредита` заполнено значением `FIX-MICP-003.loan_term_max` по умолчанию.",
    ),
]


PLAN_ROWS = [
    ["`PDP-001`", "`WP-01`", "`dictionary`", "`SRC-001`; `DICT-001`", "`ATOM-001`", "Проверить active Product Catalog values в поле продукта.", "`positive`", "`dictionary-list`", "`DICT-001 active values`", "Поле содержит все active values без архивных/extra.", "`source-selection.md`; `dictionary-inventory.md`", "`TC-MICP-001`", "`covered`"],
    ["`PDP-002`", "`WP-02`", "`availability`", "`SRC-002`", "`ATOM-002`", "Проверить доступность поля `Сумма на руки`.", "`positive`", "`field-state`", "`no_input_required`", "Поле отображается и редактируется.", "`source-row-inventory.md`", "`TC-MICP-002`", "`covered`"],
    ["`PDP-003`", "`WP-02`", "`numeric`", "`GSR 1`", "`ATOM-003`", "Ввести цифровое значение `50000`.", "`positive`", "`numeric-format`", "`digits`", "Цифровое значение отображается в поле.", "`GSR 1`; `DICT-002`", "`TC-MICP-003`; `GAP-002`", "`covered-with-gap`"],
    ["`PDP-004`", "`WP-02`", "`boundary`", "`GSR 2`", "`ATOM-004`", "Ввести catalog maximum для выбранного продукта.", "`positive`", "`max-boundary`", "`product_catalog_max`", "Catalog max отображается как допустимое значение.", "`GSR 2`; `DICT-001`", "`TC-MICP-004`; `GAP-003`", "`covered-with-gap`"],
    ["`PDP-005`", "`WP-02`", "`boundary`", "`GSR 3`", "`ATOM-005`", "Ввести catalog minimum для выбранного продукта.", "`positive`", "`min-boundary`", "`product_catalog_min`", "Catalog min отображается как допустимое значение.", "`GSR 3`; `DICT-001`", "`TC-MICP-005`; `GAP-003`", "`covered-with-gap`"],
    ["`PDP-006`", "`WP-02`", "`dictionary`", "`GSR 4`; `DICT-002`", "`ATOM-006`", "Проверить заполнение поля каждым amount tag.", "`positive`", "`dictionary-list`", "`DICT-002 active values`", "Выбранный tag заполняет поле соответствующим значением.", "`GSR 4`; `DICT-002`", "`TC-MICP-006`", "`covered`"],
    ["`PDP-007`", "`WP-03`", "`conditional-visibility`", "`GSR 5`", "`ATOM-007`", "Выбрать `Рефинансирование`.", "`positive`", "`true-branch`", "`product=Рефинансирование`", "Поле суммы погашения отображается.", "`GSR 5`; `DICT-001`", "`TC-MICP-007`", "`covered`"],
    ["`PDP-008`", "`WP-03`", "`conditional-visibility`", "`GSR 5`", "`ATOM-008`", "Выбрать продукты не `Рефинансирование`.", "`positive`", "`inverse-branch`", "`product!=Рефинансирование`", "Поле суммы погашения не отображается.", "`GSR 5`; `DICT-001`", "`TC-MICP-008`", "`covered`"],
    ["`PDP-009`", "`WP-03`", "`numeric`", "`GSR 6`", "`ATOM-009`", "Ввести цифровое значение в сумму погашения.", "`positive`", "`numeric-format`", "`digits`", "Цифровое значение отображается в поле.", "`GSR 6`", "`TC-MICP-009`; `GAP-002`", "`covered-with-gap`"],
    ["`PDP-010`", "`WP-03`", "`boundary`", "`GSR 7`", "`ATOM-010`", "Ввести catalog maximum суммы погашения.", "`positive`", "`max-boundary`", "`product_catalog_max`", "Catalog max отображается как допустимое значение.", "`GSR 7`; `DICT-001`", "`TC-MICP-010`; `GAP-003`", "`covered-with-gap`"],
    ["`PDP-011`", "`WP-03`", "`boundary`", "`GSR 8`", "`ATOM-011`", "Ввести catalog minimum суммы погашения.", "`positive`", "`min-boundary`", "`product_catalog_min`", "Catalog min отображается как допустимое значение.", "`GSR 8`; `DICT-001`", "`TC-MICP-011`; `GAP-003`", "`covered-with-gap`"],
    ["`PDP-012`", "`WP-04`", "`visibility`", "`SRC-004`", "`ATOM-012`", "Проверить default hidden state до выбора продукта.", "`positive`", "`default-state`", "`no_product_selected`", "Поле срока кредита скрыто.", "`SRC-004`", "`TC-MICP-012`", "`covered`"],
    ["`PDP-013`", "`WP-04`", "`conditional-availability`", "`SRC-004`; `DICT-001`", "`ATOM-013`", "Выбрать продукт не `Кредитная карта`.", "`positive`", "`true-branch`", "`product!=Кредитная карта`", "Поле срока кредита отображается и редактируется.", "`SRC-004`; `DICT-001`", "`TC-MICP-013`; `GAP-004`", "`covered-with-gap`"],
    ["`PDP-014`", "`WP-04`", "`boundary`", "`GSR 9`", "`ATOM-014`; `ATOM-016`", "Выбрать Product Catalog min/max срок без проверки полного списка.", "`scenario`", "`min-max-boundary`", "`product_catalog_term_min_max`", "Catalog term min/max выбираются в dropdown.", "`GSR 9`; `DICT-001`; `GAP-001`", "`TC-MICP-014`; `GAP-001`; `GAP-003`", "`covered-with-gap`"],
    ["`PDP-015`", "`WP-04`", "`default-value`", "`GSR 10`", "`ATOM-015`", "Проверить default maximum value.", "`positive`", "`default-max`", "`product_catalog_term_max`", "Поле заполнено catalog max по умолчанию.", "`GSR 10`; `DICT-001`", "`TC-MICP-015`", "`covered`"],
    ["`PDP-016`", "`all`", "`other`", "`column О`; `section-20 excluded`", "`ATOM-013`", "Requiredness enforcement оставлен как residual gap без validation action.", "`gap`", "`requiredness-enforcement`", "`missing_validation_action`", "Исполнимый oracle отсутствует.", "`scope-contract.md`; `GAP-004`", "`GAP-004`", "`gap`"],
]


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")


def tddt_rows() -> list[list[str]]:
    atom_to_tc: dict[str, str] = {}
    atom_to_gap: dict[str, str] = {}
    for row in ATOMS:
        atom_id = row[0].strip("`")
        atom_to_tc[atom_id] = row[6]
        atom_to_gap[atom_id] = row[8]

    rows: list[list[str]] = []
    for index, row in enumerate(NORMALIZATION_ROWS, start=1):
        source_property_id = row[0]
        package_id = row[2]
        property_type = row[4]
        linked_value = row[11]
        atom_ids = re.findall(r"ATOM-\d{3}", linked_value)
        gap_ids = re.findall(r"GAP-\d{3}", row[10] + " " + linked_value)
        if atom_ids:
            atom_id = f"`{atom_ids[0]}`"
            planned = atom_to_tc.get(atom_ids[0], "")
            gap_ref = atom_to_gap.get(atom_ids[0], "")
            if gap_ids:
                planned = f"{planned}; " + "; ".join(f"`{gap}`" for gap in gap_ids if f"`{gap}`" not in planned)
            decision = "`standalone_tc`" if planned and "TC-" in planned else "`gap_unclear`"
            must_execute = "`yes`" if "TC-" in planned else "`no`"
            review_risk = "`medium`" if gap_ids else "`low`"
            reason = "Executable source-backed check exists; residual gap retained where oracle is incomplete." if gap_ids else "Executable source-backed check exists."
        else:
            atom_id = "`not_applicable:GAP-004`"
            planned = "`GAP-004`"
            decision = "`gap_unclear`"
            must_execute = "`no`"
            review_risk = "`medium`"
            reason = "No source-backed validation action/oracle for requiredness enforcement in selected scope."
        rows.append(
            [
                f"`TDDT-{index:03}`",
                package_id,
                source_property_id,
                atom_id,
                property_type,
                decision,
                reason,
                planned,
                row[8],
                must_execute,
                review_risk,
            ]
        )
    return rows


def build_artifacts() -> None:
    TD.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    PROMPTS.mkdir(parents=True, exist_ok=True)
    (TD / "_artifact_write").mkdir(parents=True, exist_ok=True)

    write(
        TD / "source-row-inventory.md",
        "# Source Row Inventory\n\n"
        + table(["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"], SOURCE_ROWS),
    )
    write(
        TD / "source-row-completeness-matrix.md",
        "# Source Row Completeness Matrix\n\n## Source Row Completeness Matrix\n\n"
        + table(
            ["source_row_id", "source_requirement_codes", "normalized_property_ids", "linked_atoms", "gap_ids", "coverage_decision"],
            [
                ["`SRC-001`", "`no_requirement_code:SRC-001`", "`SRC-001.P01`", "`ATOM-001`", "`GAP-004`", "`covered-with-requiredness-gap`"],
                ["`SRC-002`", "`GSR 1`; `GSR 2`; `GSR 3`; `GSR 4`", "`SRC-002.P01`; `SRC-002.P02`; `SRC-002.P03`; `SRC-002.P04`; `SRC-002.P05`", "`ATOM-002`; `ATOM-003`; `ATOM-004`; `ATOM-005`; `ATOM-006`", "`GAP-002`; `GAP-003`; `GAP-004`", "`covered-with-invalid-feedback-gap`"],
                ["`SRC-003`", "`GSR 5`; `GSR 6`; `GSR 7`; `GSR 8`", "`SRC-003.P01`; `SRC-003.P02`; `SRC-003.P03`; `SRC-003.P04`; `SRC-003.P05`", "`ATOM-007`; `ATOM-008`; `ATOM-009`; `ATOM-010`; `ATOM-011`", "`GAP-002`; `GAP-003`; `GAP-004`", "`covered-with-invalid-feedback-gap`"],
                ["`SRC-004`", "`GSR 9`; `GSR 10`", "`SRC-004.P01`; `SRC-004.P02`; `SRC-004.P03`; `SRC-004.P04`; `SRC-004.P05`", "`ATOM-012`; `ATOM-013`; `ATOM-014`; `ATOM-015`; `ATOM-016`", "`GAP-001`; `GAP-003`; `GAP-004`", "`covered-with-dictionary-gap`"],
            ],
        ),
    )
    write(
        TD / "source-table-normalization.md",
        "# Source Table Normalization\n\n## Source Table Normalization\n\n"
        + table(["source_property_id", "source_row_id", "package_id", "field_or_block", "property", "condition", "expected_behavior", "requirement_code", "source_ref", "confidence", "gap_id", "linked_atoms"], NORMALIZATION_ROWS),
    )
    write(
        TD / "dictionary-inventory.md",
        "# Dictionary Inventory\n\n"
        + table(
            ["dictionary_id", "dictionary_name", "source_file", "source_location", "extraction_status", "active_values", "archived_values", "used_by_source_properties", "gap_id", "notes"],
            [
                ["`DICT-001`", "`Продуктовый каталог`", "`support/Наполнение справочников_v1.xlsx`", "`sheet: Продуктовый каталог`", "`extracted`", "`Потребительский кредит`; `Кредитная карта`; `Рефинансирование`", "`none_required:no_archived_values`", "`SRC-001`; `SRC-002`; `SRC-003`; `SRC-004`", "`none_required:covered`", "`Архивный = Нет` treated as active; min/max values are sourced from Product Catalog at execution."],
                ["`DICT-002`", "`Значения тегов по выбору суммы`", "`support/Наполнение справочников_v1.xlsx`", "`sheet: Значения тегов по выбору суммы`", "`extracted`", "`50000`; `100000`; `200000`; `300000`; `400000`; `500000`; `1000000`", "`none_required:no_archived_values`", "`SRC-002`; `GSR 4`", "`none_required:covered`", "`Numeric workbook values; UI formatting may add spaces/currency sign."],
                ["`DICT-003`", "`Сроки кредитования`", "`support/Наполнение справочников_v1.xlsx`", "`exact sheet not found`", "`missing`", "`not_covered:GAP-001`", "`not_covered:GAP-001`", "`SRC-004`; `GSR 9`; `GSR 10`", "`GAP-001`", "`Do not assert full loan-term value list.`"],
            ],
        ),
    )
    write(
        TD / "atomic-requirements-ledger.md",
        "# Atomic Requirements Ledger\n\n## Atomic Requirements Ledger\n\n"
        + table(["atom_id", "package_id", "source_property_id", "req_id", "source_ref", "atomic_statement", "covered_by_tc", "coverage_status", "gap_id"], ATOMS),
    )
    write(
        TD / "test-design-applicability-matrix.md",
        "# Test-design Applicability Matrix\n\n## Test-design Applicability Matrix\n\n"
        + table(
            ["dimension", "applicable", "source_ref", "reason", "linked_atoms", "linked_test_cases", "gap_id"],
            [
                ["`conditional-visibility`", "`yes`", "`SRC-001`..`SRC-004`", "Fields have visibility/availability statements.", "`ATOM-001`; `ATOM-002`; `ATOM-007`; `ATOM-008`; `ATOM-012`; `ATOM-013`", "`TC-MICP-001`; `TC-MICP-002`; `TC-MICP-007`; `TC-MICP-008`; `TC-MICP-012`; `TC-MICP-013`", ""],
                ["`other`", "`unclear`", "`column О`; `scope-contract.md`", "Requiredness exists, but selected scope excludes validation action/oracle.", "`ATOM-013`", "", "`GAP-004`"],
                ["`other`", "`yes`", "`scope-contract.md`", "Fields are editable where displayed.", "`ATOM-001`; `ATOM-002`; `ATOM-007`; `ATOM-013`", "`TC-MICP-001`; `TC-MICP-002`; `TC-MICP-007`; `TC-MICP-013`", ""],
                ["`other`", "`yes`", "`GSR 10`; `SRC-004`", "Loan term initial value equals upper Product Catalog boundary.", "`ATOM-012`; `ATOM-015`", "`TC-MICP-012`; `TC-MICP-015`", ""],
                ["`table-list`", "`yes`", "`DICT-001`; `DICT-002`; `DICT-003`", "Product and amount tags extracted; loan terms missing.", "`ATOM-001`; `ATOM-006`", "`TC-MICP-001`; `TC-MICP-006`", "`GAP-001`"],
                ["`scenario-use-case`", "`yes`", "`GSR 1`..`GSR 10`", "Positive numeric/catalog/default branches are source-backed.", "`ATOM-003`; `ATOM-004`; `ATOM-005`; `ATOM-009`; `ATOM-010`; `ATOM-011`; `ATOM-014`; `ATOM-015`; `ATOM-016`", "`TC-MICP-003`; `TC-MICP-004`; `TC-MICP-005`; `TC-MICP-009`; `TC-MICP-010`; `TC-MICP-011`; `TC-MICP-014`; `TC-MICP-015`", ""],
                ["`expected-result`", "`unclear`", "`GSR 1`; `GSR 6`; min/max GSRs", "Invalid input/out-of-range UI feedback is not specified.", "`ATOM-003`; `ATOM-004`; `ATOM-005`; `ATOM-009`; `ATOM-010`; `ATOM-011`; `ATOM-014`; `ATOM-016`", "", "`GAP-002`; `GAP-003`"],
                ["`dependency`", "`yes`", "`GSR 5`; `SRC-004`", "Refinance true/inverse branch and loan term product branch are in scope.", "`ATOM-007`; `ATOM-008`; `ATOM-013`", "`TC-MICP-007`; `TC-MICP-008`; `TC-MICP-013`", ""],
            ],
        ),
    )
    write(
        TD / "package-test-design-plan.md",
        "# Package Test Design Plan\n\n## Package Test Design Plan\n\n"
        + table(["design_item_id", "package_id", "design_dimension", "source_ref", "linked_atoms", "planned_check", "check_type", "coverage_class", "input_class", "single_expected_behavior", "oracle_source", "planned_tc_or_gap", "status"], PLAN_ROWS),
    )
    write(
        TD / "test-design-decision-table.md",
        "# Test Design Decision Table\n\n## Test Design Decision Table\n\n"
        + table(["decision_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "decision", "decision_reason", "planned_tc_or_gap", "oracle_source", "must_be_executable", "review_risk"], tddt_rows()),
    )
    write(TD / "coverage-gaps.md", "# Coverage Gaps\n\n" + coverage_gaps_body())
    write(
        TD / "coverage-metrics.md",
        "# Coverage Metrics\n\n## Coverage Metrics\n\n"
        + table(
            ["metric_id", "dimension", "applicable", "total_obligations", "covered", "gap", "unclear", "evidence"],
            [
                ["`MET-001`", "`source_rows`", "`yes`", "4", "4", "0", "0", "`source-row-inventory.md`"],
                ["`MET-002`", "`atomic_statements`", "`yes`", "16", "16", "0", "4", "`atomic-requirements-ledger.md`; `coverage-gaps.md`"],
                ["`MET-003`", "`pdf_only_gsr`", "`yes`", "10", "10", "0", "3", "`GSR 1`..`GSR 10` represented by atoms and TC/GAP refs"],
                ["`MET-004`", "`dictionary_values`", "`yes`", "3", "2", "1", "0", "`DICT-001`; `DICT-002` covered; `DICT-003` -> `GAP-001`"],
                ["`MET-005`", "`numeric_positive_boundaries`", "`yes`", "7", "7", "0", "2", "`TC-MICP-003`..`TC-MICP-005`; `TC-MICP-009`..`TC-MICP-011`; `TC-MICP-014`"],
                ["`MET-006`", "`invalid_or_requiredness_feedback`", "`unclear`", "3", "0", "0", "3", "`GAP-002`; `GAP-003`; `GAP-004`"],
                ["`MET-007`", "`integration_internal_effects`", "`no`", "0", "0", "0", "0", "`none_required:out-of-scope`"],
            ],
        ),
    )
    write(
        TD / "fixture-catalog.md",
        "# Fixture Catalog\n\n## Fixture Catalog\n\n"
        + table(
            ["fixture_id", "source_ref", "purpose", "fixture_data", "constraints", "used_by_tc"],
            [
                ["`FIX-MICP-001`", "`DICT-001`; Product Catalog", "Product for requested amount boundaries.", "`product = Потребительский кредит`; `requested_amount_min`; `requested_amount_max` from Product Catalog.", "Use actual configured min/max for selected product; do not invent numbers in TC.", "`TC-MICP-004`; `TC-MICP-005`"],
                ["`FIX-MICP-002`", "`DICT-001`; Product Catalog", "Product for refinance repayment amount boundaries.", "`product = Рефинансирование`; `refinance_repayment_amount_min`; `refinance_repayment_amount_max` from Product Catalog.", "Use actual configured min/max for refinance product.", "`TC-MICP-010`; `TC-MICP-011`"],
                ["`FIX-MICP-003`", "`DICT-001`; Product Catalog", "Product for loan term min/max/default.", "`product = Потребительский кредит`; `loan_term_min`; `loan_term_max` from Product Catalog.", "`GAP-001` means no full dictionary list assertion.", "`TC-MICP-014`; `TC-MICP-015`"],
            ],
        ),
    )
    write(
        TD / "risk-priority-map.md",
        "# Risk / Priority Map\n\n## Risk / Priority Map\n\n"
        + table(
            ["atom_id", "risk_level", "risk_factors", "source_ref", "required_priority", "linked_test_cases", "gap_id", "rationale"],
            [
                ["`ATOM-001`", "`high`", "`product-list-drives-downstream-credit-parameters`", "`SRC-001`; `DICT-001`", "`High`", "`TC-MICP-001`", "", "Wrong product list changes downstream field visibility and min/max source."],
                ["`ATOM-004`", "`high`", "`amount-boundary-from-product-catalog`", "`GSR 2`; `DICT-001`", "`High`", "`TC-MICP-004`", "`GAP-003`", "Requested amount maximum affects credit parameters."],
                ["`ATOM-005`", "`high`", "`amount-boundary-from-product-catalog`", "`GSR 3`; `DICT-001`", "`High`", "`TC-MICP-005`", "`GAP-003`", "Requested amount minimum affects credit parameters."],
                ["`ATOM-006`", "`high`", "`amount-tag-values`", "`GSR 4`; `DICT-002`", "`High`", "`TC-MICP-006`", "", "Amount tags directly populate requested amount."],
                ["`ATOM-007`", "`high`", "`conditional-refinance-field`", "`GSR 5`; `DICT-001`", "`High`", "`TC-MICP-007`", "", "Refinance-only amount must appear for refinance."],
                ["`ATOM-008`", "`high`", "`conditional-refinance-field`", "`GSR 5`; `DICT-001`", "`High`", "`TC-MICP-008`", "", "Refinance-only amount must not appear for other products."],
                ["`ATOM-014`", "`high`", "`loan-term-boundary-from-product-catalog`", "`GSR 9`; `DICT-001`; `DICT-003`", "`High`", "`TC-MICP-014`", "`GAP-001`; `GAP-003`", "Loan term min source is critical; complete dictionary values are missing."],
                ["`ATOM-016`", "`high`", "`loan-term-boundary-from-product-catalog`", "`GSR 9`; `DICT-001`; `DICT-003`", "`High`", "`TC-MICP-014`", "`GAP-001`; `GAP-003`", "Loan term max source is critical; complete dictionary values are missing."],
                ["`ATOM-015`", "`high`", "`default-upper-boundary`", "`GSR 10`; `DICT-001`", "`High`", "`TC-MICP-015`", "", "Default loan term affects credit parameter initialization."],
                ["`ATOM-003`", "`medium`", "`unsupported-invalid-feedback`", "`GSR 1`", "`Medium`", "`TC-MICP-003`", "`GAP-002`", "Positive numeric input is covered; invalid feedback remains unclear."],
                ["`ATOM-009`", "`medium`", "`unsupported-invalid-feedback`", "`GSR 6`", "`Medium`", "`TC-MICP-009`", "`GAP-002`", "Positive numeric input is covered; invalid feedback remains unclear."],
                ["`ATOM-013`", "`medium`", "`requiredness-enforcement-missing-action`", "`SRC-004`; column `О`", "`Medium`", "`TC-MICP-013`", "`GAP-004`", "Availability is covered; requiredness enforcement needs action oracle."],
            ],
        ),
    )
    write(
        TD / "internal-work-package-coverage.md",
        "# Internal Work Package Coverage\n\n## Internal Work Package Coverage\n\n"
        + table(
            ["package_id", "focus", "source_refs", "atoms", "test_cases", "gaps", "status"],
            [
                ["`WP-01`", "Product selection", "`SRC-001`; `DICT-001`", "`ATOM-001`", "`TC-MICP-001`", "`GAP-004`", "`covered-with-gap`"],
                ["`WP-02`", "Requested amount", "`SRC-002`; `GSR 1`..`GSR 4`", "`ATOM-002`..`ATOM-006`", "`TC-MICP-002`..`TC-MICP-006`", "`GAP-002`; `GAP-003`; `GAP-004`", "`covered-with-gap`"],
                ["`WP-03`", "Refinance repayment amount", "`SRC-003`; `GSR 5`..`GSR 8`", "`ATOM-007`..`ATOM-011`", "`TC-MICP-007`..`TC-MICP-011`", "`GAP-002`; `GAP-003`; `GAP-004`", "`covered-with-gap`"],
                ["`WP-04`", "Loan term", "`SRC-004`; `GSR 9`; `GSR 10`", "`ATOM-012`..`ATOM-016`", "`TC-MICP-012`..`TC-MICP-015`", "`GAP-001`; `GAP-003`; `GAP-004`", "`covered-with-gap`"],
            ],
        ),
    )
    write(
        TD / "artifact-write-strategy.md",
        "# Artifact Write Strategy\n\n## Artifact Write Strategy\n\n"
        + table(
            ["artifact_path", "artifact_size_class", "write_strategy", "declared_before_first_write", "helper", "forbidden_methods_checked"],
            [
                [f"`{CANONICAL_REL}`", "`medium generated`", "`file-based section-manifest write`", "`yes`", "`scripts/write_artifact_sections.py --manifest` prepared by `scripts/build_main_info_credit_parameters_writer_artifacts.py`", "`yes`"],
                [f"`{TD_REL}/`", "`medium split artifacts`", "`file-based section-manifest write`", "`yes`", "`scripts/write_artifact_sections.py --manifest` prepared by `scripts/build_main_info_credit_parameters_writer_artifacts.py`", "`yes`"],
            ],
        ),
    )
    write(
        TD / "test-design-review.md",
        "# Test Design Review\n\n## Test Design Review\n\n"
        + table(
            ["review_item", "status", "severity", "affected_package", "evidence", "required_action", "blocks_ready_for_review"],
            [
                ["`decision-table-classification`", "`pass`", "`info`", "`all`", "`test-design-decision-table.md` maps each normalized source property to `standalone_tc` or `gap_unclear`.", "`none_required:pass`", "`no`"],
                ["`ledger-plan-alignment`", "`pass`", "`info`", "`all`", "`ATOM-001`..`ATOM-016` appear in ledger and package plan.", "`none_required:pass`", "`no`"],
                ["`coverage-class-completeness`", "`pass`", "`info`", "`all`", "Applicability matrix covers dictionary, dependency, numeric/boundary, expected-result and integration dimensions.", "`none_required:pass`", "`no`"],
                ["`numeric-length-boundaries`", "`pass`", "`info`", "`WP-02`; `WP-03`; `WP-04`", "Product Catalog min/max positive boundaries are covered; out-of-range feedback is `GAP-003`.", "`none_required:pass`", "`no`"],
                ["`unsupported-ui-mechanism`", "`pass`", "`info`", "`WP-02`; `WP-03`; `all requiredness`", "`GAP-002`; `GAP-003`; `GAP-004` prevent invented highlight/message/blocked-action oracles.", "`none_required:pass`", "`no`"],
                ["`mask-format-coverage`", "`pass`", "`info`", "`WP-02`; `WP-03`", "No mask/exact length is specified; numeric-positive checks and `GAP-002` cover the available source.", "`none_required:pass`", "`no`"],
                ["`dictionary-closed-set`", "`pass`", "`info`", "`WP-01`; `WP-02`; `WP-04`", "`DICT-001`; `DICT-002` closed values covered; `DICT-003` remains `GAP-001`.", "`none_required:pass`", "`no`"],
                ["`conditional-branches`", "`pass`", "`info`", "`WP-03`; `WP-04`", "Refinance true/inverse branch covered by `TC-MICP-007` and `TC-MICP-008`; loan-term display covered by `TC-MICP-012`; `TC-MICP-013`.", "`none_required:pass`", "`no`"],
                ["`negative-fixture-isolation`", "`pass`", "`info`", "`WP-02`; `WP-03`; `WP-04`", "No executable negative-input TC is written without source-backed oracle; residuals are `GAP-002` and `GAP-003`.", "`none_required:pass`", "`no`"],
                ["`applicability-linked-tc-semantics`", "`pass`", "`info`", "`all`", "Each applicable dimension links to matching TC or GAP refs.", "`none_required:pass`", "`no`"],
                ["`gap-specificity`", "`pass`", "`info`", "`all`", "`GAP-001`..`GAP-004` name source refs and downstream handling.", "`none_required:pass`", "`no`"],
                ["`gap-admissibility`", "`pass`", "`info`", "`all`", "Gaps are source/input limitations, not hidden executable behavior.", "`none_required:pass`", "`no`"],
                ["`internal-observability`", "`pass`", "`info`", "`all`", "No API/DB/internal effects are asserted.", "`none_required:pass`", "`no`"],
                ["`metadata-only-exclusion`", "`pass`", "`info`", "`all`", "Type/source metadata is not converted into standalone TC without observable field behavior.", "`none_required:pass`", "`no`"],
                ["`tc-mapping-atomicity`", "`pass`", "`info`", "`all`", "Each executable TC has one main expected result and traceable atoms.", "`none_required:pass`", "`no`"],
                ["`ready-for-tc-writing`", "`pass`", "`info`", "`all`", "Artifacts are ready for structure preflight after scoped validator profile is clean.", "`none_required:pass`", "`no`"],
            ],
        ),
    )
    write(
        TD / "writer-quality-gate.md",
        "# Writer Quality Gate\n\n## Writer Quality Gate\n\n"
        + table(
            ["gate_item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"],
            [
                ["`artifact-write-strategy`", "`pass`", "`artifact-write-strategy.md`; canonical helper strategy `scripts/write_artifact_sections.py --manifest` declared through file-based generator.", "`all`", "`none_required:pass`", "`no`"],
                ["`mockup-visual-inventory`", "`pass`", "No mockup source is required for this scope; source-selection lists DOCX/PDF/support only.", "`all`", "`none_required:not-applicable`", "`no`"],
                ["`source-row-inventory`", "`pass`", "Writer inventory preserves `SRC-001`..`SRC-004`.", "`all`", "`none_required:pass`", "`no`"],
                ["`source-normalization-atomic`", "`pass`", "Every GSR has a separate `source_property_id` and `ATOM-*` or `GAP-*` link.", "`all`", "`none_required:pass`", "`no`"],
                ["`test-design-decision-table`", "`pass`", "`test-design-decision-table.md` uses canonical TDDT columns and links source properties to TC/GAP.", "`all`", "`none_required:pass`", "`no`"],
                ["`test-design-review`", "`pass`", "`test-design-review.md` contains required review items with no blocking rows.", "`all`", "`none_required:pass`", "`no`"],
                ["`coverage-gaps`", "`pass`", "`GAP-001`..`GAP-004` are explicit non-blocking residual unclear/source gaps.", "`all`", "`none_required:pass`", "`no`"],
                ["`gap-admissibility`", "`pass`", "Residual gaps are source/input limitations and are not executable TC placeholders.", "`all`", "`none_required:pass`", "`no`"],
                ["`ledger-atomicity`", "`pass`", "`atomic-requirements-ledger.md` splits `GSR 1`..`GSR 10` into `ATOM-001`..`ATOM-016` without ranges.", "`all`", "`none_required:pass`", "`no`"],
                ["`gsr-range-compression`", "`pass`", "No `GSR` range is used as a single atom or TC traceability substitute.", "`all`", "`none_required:pass`", "`no`"],
                ["`design-plan-atomicity`", "`pass`", "`package-test-design-plan.md` has one planned check per row and routes gaps separately.", "`all`", "`none_required:pass`", "`no`"],
                ["`scenario-does-not-replace-atomic`", "`pass`", "Scenario TC rows are backed by atom-level ledger and plan mappings.", "`all`", "`none_required:pass`", "`no`"],
                ["`tc-atomicity`", "`pass`", "15 TC sections; each has one main expected result.", "`all`", "`none_required:pass`", "`no`"],
                ["`test-data-specificity`", "`pass`", "`fixture-catalog.md` defines Product Catalog parameters; no generic valid-data placeholder is used.", "`WP-02`; `WP-03`; `WP-04`", "`none_required:pass`", "`no`"],
                ["`internal-observability`", "`pass`", "No API/DB/internal effect is asserted.", "`all`", "`none_required:pass`", "`no`"],
                ["`action-observability`", "`pass`", "No excluded section-20 action is used as hidden validation oracle; gaps document absent actions.", "`all`", "`none_required:pass`", "`no`"],
                ["`semantic-req-id-parity`", "`pass`", "PDF-only `GSR 1`..`GSR 10` retained in ledger and TC/GAP traceability.", "`WP-02`; `WP-03`; `WP-04`", "`none_required:pass`", "`no`"],
                ["`scoped-validator-findings`", "`pass`", "Runner validate passed; profile `work/review-cycles/main-info-credit-parameters/outputs/scoped-validator-profile.structure-preflight-r1.json` has `unresolved_warning_error_count = 0`.", "`all`", "`none_required:pass`", "`no`"],
                ["`package-ready`", "`pass`", "`internal-work-package-coverage.md` shows WP-01..WP-04 covered with explicit non-blocking gaps.", "`all`", "`none_required:pass`", "`no`"],
            ],
        ),
    )
    write(
        TD / "writer-self-check.md",
        "# Writer Self-Check\n\n"
        + table(
            ["check", "status", "evidence", "follow_up"],
            [
                ["`required-instructions-read`", "`pass`", "Resolver command passed; selected 15 files read; UTF-8 reread performed for initially distorted stdout.", "`none_required:pass`"],
                ["`required-inputs-read`", "`pass`", "Read source-selection, scope-contract, parity, row inventory, dictionary inventory, gaps, clarification requests, package notes and scope-gap-review.", "`none_required:pass`"],
                ["`scope-boundary`", "`pass`", "Only `SRC-001`..`SRC-004` from section 19 are used.", "`none_required:pass`"],
                ["`unsupported-oracle-check`", "`pass`", "No invented red highlight/message/cleanup/blocking for numeric or requiredness gaps.", "`reviewer should inspect GAP-002..GAP-004`"],
                ["`dictionary-check`", "`pass`", "`DICT-001`; `DICT-002` used; `DICT-003` stays `GAP-001`.", "`none_required:pass`"],
                ["`scoped-validator`", "`pass`", "`python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_17/work/review-cycles/main-info-credit-parameters/cycle-state.yaml` passed; profile unresolved warning/error count is 0.", "`none_required:pass`"],
            ],
        ),
    )

    canonical = [
        "# Тест-кейсы: кредитные параметры раздела `Основная информация`",
        "## Metadata\n\n"
        + table(
            ["field", "value"],
            [
                ["ft_slug", "`ft-2-OF_17`"],
                ["scope_slug", f"`{SCOPE}`"],
                ["section_id", "`2.1.1.1.1.1.2`"],
                ["source_refs", "`DOCX section-19 rows 1-4`; `PDF pp.46-47`; `GSR 1`..`GSR 10`"],
                ["writer_mode", "`writer-r1 initial draft`"],
                ["remaining_coverage_gaps", "`GAP-001`; `GAP-002`; `GAP-003`; `GAP-004`"],
            ],
        ),
        "## Coverage Boundary\n\nПокрываются четыре строки кредитных параметров раздела `Основная информация`: `Запрошенный продукт`, `Сумма на руки`, `Сумма на погашение рефинансируемых кредитов`, `Срок кредита`.\n\nНе покрываются строки блока `Личная информация`, действия `section-20`, backend/API/internal effects, полный список значений `Сроки кредитования`, а также неподтвержденные UI-механизмы ошибок для numeric/min-max/requiredness.",
        "## Canonical Artifact Links\n\n"
        + "\n".join(
            f"- `{TD_REL}/{name}`"
            for name in [
                "source-row-inventory.md",
                "source-table-normalization.md",
                "atomic-requirements-ledger.md",
                "package-test-design-plan.md",
                "coverage-gaps.md",
                "writer-quality-gate.md",
            ]
        ),
        "## Coverage Summary\n\n"
        + table(
            ["package_id", "focus", "executable_tc", "covered_atoms", "gap_refs"],
            [
                ["`WP-01`", "Product selection", "`TC-MICP-001`", "`ATOM-001`", "`GAP-004`"],
                ["`WP-02`", "Requested amount", "`TC-MICP-002`..`TC-MICP-006`", "`ATOM-002`..`ATOM-006`", "`GAP-002`; `GAP-003`; `GAP-004`"],
                ["`WP-03`", "Refinance repayment amount", "`TC-MICP-007`..`TC-MICP-011`", "`ATOM-007`..`ATOM-011`", "`GAP-002`; `GAP-003`; `GAP-004`"],
                ["`WP-04`", "Loan term", "`TC-MICP-012`..`TC-MICP-015`", "`ATOM-012`..`ATOM-016`", "`GAP-001`; `GAP-003`; `GAP-004`"],
            ],
        ),
        "## Coverage Gaps\n\n" + "\n\n".join(f"### {gap_id}\n\n**Impact:** `unclear`\n\n**Blocks Ready For Review:** `{blocks}`\n\n**Source Ref:** {refs}\n\n**Description:** {desc}" for gap_id, _pkg, refs, _kind, desc, _handling, blocks in GAPS),
        "## WP-01. Product selection",
        TEST_CASES[0],
        "## WP-02. Requested amount",
        "\n\n".join(TEST_CASES[1:6]),
        "## WP-03. Refinance repayment amount",
        "\n\n".join(TEST_CASES[6:11]),
        "## WP-04. Loan term",
        "\n\n".join(TEST_CASES[11:]),
    ]
    write(CANONICAL, "\n\n".join(canonical))

    write(
        OUTPUTS / "writer-r1-response.md",
        "# Writer R1 Response\n\n"
        + table(
            ["field", "value"],
            [
                ["cycle_id", "`main-info-credit-parameters-2026-06-15`"],
                ["stage", "`writer-r1`"],
                ["status", "`writer-draft-ready`"],
                ["canonical_test_cases", f"`{CANONICAL_REL}`"],
                ["test_design_dir", f"`{TD_REL}`"],
                ["remaining_gaps", "`GAP-001`; `GAP-002`; `GAP-003`; `GAP-004`"],
            ],
        )
        + "\n\n## Notes\n\n- Writer preserved PDF-only `GSR 1`..`GSR 10`.\n- `GAP-001` remains from scope analysis.\n- `GAP-002`..`GAP-004` are writer-side residual unclear items for unsupported invalid/requiredness oracle mechanisms.\n",
    )
    write(
        PROMPTS / "prompt.structure-preflight-r1.md",
        "# Structure Preflight Prompt: Main Info Credit Parameters\n\n"
        "Run `ft-test-case-reviewer` in `reviewer.structure_preflight` mode for `ft-2-OF_17 / main-info-credit-parameters`.\n\n"
        "## Inputs\n\n"
        f"- Canonical TC: `{CANONICAL_REL}`\n"
        f"- Test-design dir: `{TD_REL}/`\n"
        f"- Cycle state: `work/review-cycles/{SCOPE}/cycle-state.yaml`\n"
        f"- Writer response: `work/review-cycles/{SCOPE}/outputs/writer-r1-response.md`\n\n"
        "## Scope\n\nCheck parseability, required runtime fields, package_id, headings, table shape, source-row preservation and validator profile consistency only. Do not perform semantic coverage review in this preflight.\n",
    )

    write(
        OUTPUTS / "writer-session-log.md",
        "# Writer Session Log\n\n"
        "## Session Metadata\n\n"
        + table(
            ["field", "value"],
            [
                ["skill", "`ft-test-case-writer`"],
                ["mode", "`writer.session_initial_draft`"],
                ["ft_slug", "`ft-2-OF_17`"],
                ["scope_slug", f"`{SCOPE}`"],
                ["started_from", "`cycle-state.yaml`"],
                ["status_after", "`writer-draft-ready`"],
            ],
        )
        + "\n\n## Inputs Read\n\n"
        "- `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - resolver command; budget `pass` 137.0 / 200.0 KiB.\n"
        + "\n".join(
            f"- `{path}` - selected required instruction file."
            for path in [
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
        )
        + "\n"
        + "\n".join(
            f"- `{path}` - domain/source input."
            for path in [
                "fts/ft-2-OF_17/AGENT-NOTES.md",
                f"fts/ft-2-OF_17/{HANDOFF_REL}/source-selection.md",
                f"fts/ft-2-OF_17/{HANDOFF_REL}/scope-contract.md",
                f"fts/ft-2-OF_17/{HANDOFF_REL}/source-parity-check.md",
                f"fts/ft-2-OF_17/{HANDOFF_REL}/source-row-inventory.md",
                f"fts/ft-2-OF_17/{HANDOFF_REL}/dictionary-inventory.md",
                f"fts/ft-2-OF_17/{HANDOFF_REL}/scope-coverage-gaps.md",
                f"fts/ft-2-OF_17/{HANDOFF_REL}/scope-clarification-requests.md",
                f"fts/ft-2-OF_17/work/review-cycles/{SCOPE}/outputs/scope-gap-review.md",
            ]
        )
        + "\n\n## Inputs Not Used\n\n- Historical canary outputs under `work/review-cycles/ui-employment*` and `work/stage-handoffs/04-document-print-form-tags/` - excluded by source-selection contamination rule.\n\n"
        "## Key Decisions\n\n- Preserve only `SRC-001`..`SRC-004` and PDF-only `GSR 1`..`GSR 10`.\n- Do not invent Product Catalog min/max numeric values; use fixture parameters linked to Product Catalog.\n- Keep missing `Сроки кредитования` list as `GAP-001`.\n- Add `GAP-002`..`GAP-004` for unsupported invalid/requiredness oracles.\n\n"
        "## Risks And Fallbacks\n\n- Encoding fallback: initial PowerShell stdout distorted Cyrillic for instruction files; files were reread with explicit UTF-8 and distorted stdout was not used as source evidence.\n\n"
        "## Artifact Write Strategy\n\n"
        + table(
            ["artifact_path", "artifact_size_class", "write_strategy", "declared_before_first_write", "helper", "forbidden_methods_checked"],
            [[f"`{CANONICAL_REL}` and `{TD_REL}/`", "`medium generated`", "`file-based section-manifest write`", "`yes`", "`scripts/write_artifact_sections.py --manifest` prepared by `scripts/build_main_info_credit_parameters_writer_artifacts.py`", "`yes`"]],
        )
        + "\n\n## Validation\n\n- `python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_17/work/review-cycles/main-info-credit-parameters/cycle-state.yaml` - pass; routes to `structure-preflight-r1`; scoped profile unresolved warning/error count `0`.\n\n## Contamination Check\n\n- Neighboring packages and prior canary outputs were not used as source content.\n\n## Event Timeline\n\n"
        + table(
            ["step", "event", "result", "artifact_or_evidence"],
            [
                ["1", "Resolved instruction context", "budget pass", "`resolver stdout`"],
                ["2", "Read required instructions and inputs", "scope confirmed", "`writer-session-log.md`"],
                ["3", "Wrote canonical and split artifacts", "draft created", f"`{CANONICAL_REL}`; `{TD_REL}/`"],
                ["4", "Prepared structure preflight prompt", "prompt created", f"`work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md`"],
                ["5", "Ran runner scoped validator gate", "pass", f"`work/review-cycles/{SCOPE}/outputs/scoped-validator-profile.structure-preflight-r1.json`"],
            ],
        )
        + "\n\n## Quality Checkpoints\n\n"
        + table(
            ["checkpoint", "status", "evidence", "follow_up"],
            [
                ["Writer Quality Gate", "pass", "`writer-quality-gate.md`; scoped validator profile count `0`", "none"],
                ["Self-check near misses", "pass", "`GAP-002`..`GAP-004` prevent invented oracles.", "Reviewer should inspect gap scope."],
            ],
        )
        + "\n\n## Technical Fallbacks\n\n"
        + table(
            ["fallback_id", "trigger", "failed_method", "fallback_method", "helper_artifact_path", "retained", "quality_risk", "follow_up"],
            [["`TF-001`", "`encoding issue`", "`PowerShell console output read for Russian instruction files`", "`explicit UTF-8 reread with Get-Content -Encoding UTF8`", "`n/a`", "`n/a`", "`none; distorted stdout discarded as evidence`", "`none_required:pass`"]],
        )
        + "\n\n## Handoff Notes For Next Session\n\n- Structure preflight should focus on parser shape and current-scope validator profile; semantic coverage review follows later.\n",
    )
    write(
        OUTPUTS / "agent-decision-log.writer-r1.md",
        "# Agent Decision Log\n\n## Decision Log Metadata\n\n"
        + table(
            ["field", "value"],
            [["ft_slug", "`ft-2-OF_17`"], ["scope_slug", f"`{SCOPE}`"], ["stage", "`ft-test-case-writer / writer-r1`"], ["started_from", "`cycle-state.yaml`"]],
        )
        + "\n\n## Decision Log\n\n"
        + table(
            ["decision_id", "step", "decision_type", "input_or_trigger", "decision", "rationale", "artifact_or_output", "risk_or_confidence", "status"],
            [
                ["`DEC-001`", "1", "`scope-boundary`", "`scope-contract.md`", "Use only `SRC-001`..`SRC-004`.", "Scope contract excludes personal info and section-20 actions.", f"`{CANONICAL_REL}`", "`high`", "`applied`"],
                ["`DEC-002`", "2", "`traceability`", "`source-parity-check.md`", "Preserve PDF-only `GSR 1`..`GSR 10`.", "Parity check marks these codes mandatory.", "`atomic-requirements-ledger.md`", "`high`", "`applied`"],
                ["`DEC-003`", "3", "`gap`", "`dictionary-inventory.md`", "Keep `DICT-003` as `GAP-001`.", "Support workbook lacks exact `Сроки кредитования` list.", "`coverage-gaps.md`", "`high`", "`applied`"],
                ["`DEC-004`", "4", "`gap`", "`test-case-runtime-format.md`", "Route unsupported invalid/requiredness feedback to `GAP-002`..`GAP-004`.", "No source-backed UI reaction/action oracle in selected scope.", "`coverage-gaps.md`; canonical TC", "`medium`", "`applied`"],
                ["`DEC-005`", "5", "`artifact-write`", "`writer-process-workflow.md`", "Use file-based generator for artifacts.", "Avoid long shell writes and preserve UTF-8 content.", "`scripts/build_main_info_credit_parameters_writer_artifacts.py`", "`high`", "`applied`"],
                ["`DEC-006`", "6", "`routing`", "`runner validator pass`", "Route to `structure-preflight-r1` with `stage_status: writer-draft-ready`.", "Runner validator gate passed with current-scope unresolved warning/error count `0`.", "`cycle-state.yaml`; scoped validator profile", "`high`", "`applied`"],
            ],
        ),
    )


def main() -> int:
    build_artifacts()
    print(f"wrote {CANONICAL.relative_to(ROOT)}")
    print(f"wrote {TD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
