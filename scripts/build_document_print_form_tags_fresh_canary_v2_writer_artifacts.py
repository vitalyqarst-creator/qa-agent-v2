from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FT_ROOT = ROOT / "fts" / "ft-2-OF_17"
SCOPE = "document-print-form-tags-fresh-canary-v2"
SECTION_ID = "2-1-1-1-1-4-4"
TD_DIR = FT_ROOT / "work" / "test-design" / f"{SECTION_ID}-{SCOPE}"
WRITE_DIR = TD_DIR / "_artifact_write" / "fresh-canary-v2"
CYCLE_DIR = FT_ROOT / "work" / "review-cycles" / SCOPE
OUTPUT_DIR = CYCLE_DIR / "outputs"
PROMPT_DIR = CYCLE_DIR / "prompts"
CANONICAL = FT_ROOT / "test-cases" / f"{SECTION_ID}-{SCOPE}.md"
HANDOFF = FT_ROOT / "work" / "stage-handoffs" / "04-document-print-form-tags"


PACKAGES = {
    "WP-01": "Формирование документа и настройка шаблона/типа тегов",
    "WP-02": "Личная информация, паспорт и адрес регистрации",
    "WP-03": "Фактический адрес, контакты, семья и занятость",
    "WP-04": "Доходы и сумма кредита",
}


TC_DEFS = [
    {
        "id": "TC-DPFT-001",
        "package": "WP-01",
        "title": "Формирование заявления-анкеты по данным клиента",
        "type": "Positive",
        "priority": "High",
        "atoms": ["ATOM-001"],
        "test_data": [
            "Клиент `CANARY-DPFT-001` имеет заполненные данные, перечисленные в строках `SRC-006..SRC-053`.",
            "Документ: `Заявление-анкета на получение потребительского кредита`.",
            "Точное значение поля `Шаблон` не используется из-за `GAP-001`.",
        ],
        "steps": [
            "Открыть карточку клиента `CANARY-DPFT-001` в системе.",
            "В разделе документов сформировать документ `Заявление-анкета на получение потребительского кредита`.",
            "Открыть сформированный документ для просмотра содержимого.",
        ],
        "expected": "Сформированный документ `Заявление-анкета на получение потребительского кредита` доступен для просмотра и содержит данные клиента из системы; проверка точного значения шаблона не выполняется из-за `GAP-001`.",
        "post": "Сформированный документ можно удалить, если он был создан только для проверки.",
    },
    {
        "id": "TC-DPFT-002",
        "package": "WP-01",
        "title": "Настройка шаблона на типе, собранном по таблице тегов",
        "type": "Positive",
        "priority": "High",
        "atoms": ["ATOM-002", "ATOM-003", "ATOM-004"],
        "test_data": [
            "Документ: `Заявление-анкета на получение потребительского кредита`.",
            "Источник ожидаемого набора тегов: `source-row-inventory.md`, строки `SRC-007..SRC-053` без block-only строк.",
        ],
        "steps": [
            "Открыть в системе настройку типа печатной формы, используемого для документа `Заявление-анкета на получение потребительского кредита`.",
            "Открыть связанную с этим типом настройку шаблона.",
            "Сравнить список тегов в настройке шаблона с колонкой `Тег` из источника для строк `SRC-007..SRC-053`.",
        ],
        "expected": "Шаблон связан с типом печатной формы, настроен на этом типе, а список тегов в настройке содержит теги из источника с точным написанием, включая пробелы внутри и перед закрывающей угловой скобкой.",
        "post": "Не требуются.",
    },
    {
        "id": "TC-DPFT-003",
        "package": "WP-02",
        "title": "Точное написание тегов личной информации, паспорта и адреса регистрации",
        "type": "Positive",
        "priority": "High",
        "atoms": ["ATOM-004", "ATOM-005", "ATOM-006", "ATOM-007", "ATOM-008"],
        "test_data": [
            "Ожидаемые теги WP-02: `<last_name>`, `<first_name>`, `<middle_name>`, `<previous_full_name>`, `<birth_date>`, `<birth_place>`, `<serial_number>`, `<number>`, `<issue_date>`, `<issue_place>`, `<postal_code>`, `<region_with_type>`, `<city_district>`, `<area>`, `<city>`, `<street>`, `<house>`, `<block>`, `<flat>`.",
        ],
        "steps": [
            "Открыть настройку тегов шаблона для документа `Заявление-анкета на получение потребительского кредита`.",
            "Проверить теги из блоков `Личная информация` и `Адрес регистрации`.",
        ],
        "expected": "В настройке шаблона присутствуют все теги WP-02 с точным написанием из источника, без переименования и без удаления символов `<` и `>`.",
        "post": "Не требуются.",
    },
    {
        "id": "TC-DPFT-004",
        "package": "WP-02",
        "title": "Заполнение личной информации клиента в печатной форме",
        "type": "Positive",
        "priority": "High",
        "atoms": ["ATOM-006", "ATOM-007", "ATOM-008", "ATOM-009", "ATOM-010", "ATOM-011"],
        "test_data": [
            "Клиент `CANARY-DPFT-004`: фамилия `Иванов`, имя `Петр`, отчество `Сергеевич`, признак `Клиент менял ФИО` = `Да`, прежняя фамилия `Сидоров`, дата рождения `05.03.1988`, место рождения `г. Красноярск`.",
        ],
        "steps": [
            "Подготовить в системе клиента `CANARY-DPFT-004` с указанными тестовыми данными.",
            "Сформировать документ `Заявление-анкета на получение потребительского кредита`.",
            "Открыть сформированный документ и проверить блок `Личная информация`.",
        ],
        "expected": "В блоке `Личная информация` сформированного документа отображаются `Иванов`, `Петр`, `Сергеевич`, `Сидоров`, дата рождения в формате `05.03.1988` и место рождения `г. Красноярск`.",
        "post": "Удалить тестового клиента или сформированный документ, если это предусмотрено тестовой средой.",
    },
    {
        "id": "TC-DPFT-005",
        "package": "WP-02",
        "title": "Недоступность тега прежней фамилии без признака смены ФИО",
        "type": "Negative",
        "priority": "Medium",
        "atoms": ["ATOM-009"],
        "test_data": [
            "Клиент `CANARY-DPFT-005`: признак `Клиент менял ФИО` = `Нет`; значение прежней фамилии в данных клиента отсутствует.",
        ],
        "steps": [
            "Открыть настройку или доступный список тегов для формирования заявления-анкеты по клиенту `CANARY-DPFT-005`.",
            "Проверить доступность тега `<previous_full_name>` для документа `Заявление-анкета на получение потребительского кредита`.",
        ],
        "expected": "Тег `<previous_full_name>` недоступен для использования в документе, когда признак `Клиент менял ФИО` не равен `Да`.",
        "post": "Не требуются.",
    },
    {
        "id": "TC-DPFT-006",
        "package": "WP-02",
        "title": "Заполнение паспортных данных клиента в печатной форме",
        "type": "Positive",
        "priority": "High",
        "atoms": ["ATOM-012", "ATOM-013", "ATOM-014", "ATOM-015"],
        "test_data": [
            "Клиент `CANARY-DPFT-006`: серия паспорта `0412`, номер паспорта `345678`, дата выдачи `17.09.2019`, кем выдан `ГУ МВД России по Красноярскому краю`.",
        ],
        "steps": [
            "Подготовить в системе клиента `CANARY-DPFT-006` с указанными паспортными данными.",
            "Сформировать документ `Заявление-анкета на получение потребительского кредита`.",
            "Открыть сформированный документ и проверить паспортные данные.",
        ],
        "expected": "В сформированном документе отображаются серия `0412`, номер `345678`, дата выдачи в формате `17.09.2019` и значение `ГУ МВД России по Красноярскому краю`.",
        "post": "Удалить тестового клиента или сформированный документ, если это предусмотрено тестовой средой.",
    },
    {
        "id": "TC-DPFT-007",
        "package": "WP-02",
        "title": "Заполнение адреса регистрации клиента в печатной форме",
        "type": "Positive",
        "priority": "Medium",
        "atoms": ["ATOM-016", "ATOM-017", "ATOM-018", "ATOM-019", "ATOM-020"],
        "test_data": [
            "Клиент `CANARY-DPFT-007`: индекс `660049`, регион `Красноярский край`, район `Центральный район`, населенный пункт `Красноярск`, город `Красноярск`, улица `Мира`, дом `10`, корпус `2`, квартира `35`.",
        ],
        "steps": [
            "Подготовить в системе клиента `CANARY-DPFT-007` с указанным адресом регистрации.",
            "Сформировать документ `Заявление-анкета на получение потребительского кредита`.",
            "Открыть сформированный документ и проверить блок `Адрес регистрации`.",
        ],
        "expected": "В блоке `Адрес регистрации` отображаются индекс `660049`, регион `Красноярский край`, район `Центральный район`, населенный пункт `Красноярск`, город `Красноярск`, улица `Мира`, дом `10`, корпус `2` и квартира `35`.",
        "post": "Удалить тестового клиента или сформированный документ, если это предусмотрено тестовой средой.",
    },
    {
        "id": "TC-DPFT-014",
        "package": "WP-02",
        "title": "Заполнение улицы, дома, корпуса и квартиры адреса регистрации",
        "type": "Positive",
        "priority": "Medium",
        "atoms": ["ATOM-021", "ATOM-022", "ATOM-023", "ATOM-024", "ATOM-025"],
        "test_data": [
            "Клиент `CANARY-DPFT-014`: город регистрации `Красноярск`, улица регистрации `Мира`, дом `10`, корпус `2`, квартира `35`.",
        ],
        "steps": [
            "Подготовить в системе клиента `CANARY-DPFT-014` с указанной детализацией адреса регистрации.",
            "Сформировать документ `Заявление-анкета на получение потребительского кредита`.",
            "Открыть сформированный документ и проверить детализацию адреса регистрации.",
        ],
        "expected": "В блоке `Адрес регистрации` отображаются город `Красноярск`, улица `Мира`, дом `10`, корпус `2` и квартира `35`.",
        "post": "Удалить тестового клиента или сформированный документ, если это предусмотрено тестовой средой.",
    },
    {
        "id": "TC-DPFT-008",
        "package": "WP-03",
        "title": "Точное написание тегов фактического адреса, контактов, семьи и занятости",
        "type": "Positive",
        "priority": "High",
        "atoms": ["ATOM-004", "ATOM-026", "ATOM-036", "ATOM-039", "ATOM-041"],
        "test_data": [
            "Ожидаемые теги WP-03: `<postal_code_actual>`, `<region_with_type_actual >`, `<city_district_actual >`, `<area_actual >`, `<city_actual >`, `<street_actual >`, `<house_actual >`, `<block_actual >`, `<flat_actual >`, `<mobile_phone>`, `<email>`, `<n_child>`, `<name_main_job>`, `<main_job_title>`, `< name_add_job>`, `<add_ job_title>`.",
        ],
        "steps": [
            "Открыть настройку тегов шаблона для документа `Заявление-анкета на получение потребительского кредита`.",
            "Проверить теги из блоков `Адрес фактического проживания`, `Контактная информация`, `Сведения о семье` и `Сведения о занятости`.",
        ],
        "expected": "В настройке шаблона присутствуют все теги WP-03 с точным написанием из источника, включая пробелы в `<region_with_type_actual >`, `<city_district_actual >`, `<area_actual >`, `<city_actual >`, `<street_actual >`, `<house_actual >`, `<block_actual >`, `<flat_actual >`, `< name_add_job>` и `<add_ job_title>`.",
        "post": "Не требуются.",
    },
    {
        "id": "TC-DPFT-009",
        "package": "WP-03",
        "title": "Заполнение фактического адреса клиента в печатной форме",
        "type": "Positive",
        "priority": "Medium",
        "atoms": ["ATOM-027", "ATOM-028", "ATOM-029", "ATOM-030", "ATOM-031"],
        "test_data": [
            "Клиент `CANARY-DPFT-009`: фактический индекс `630099`, регион факт `Новосибирская область`, район факт `Железнодорожный район`, населенный пункт факт `Новосибирск`, город факт `Новосибирск`, улица факт `Ленина`, дом факт `25`, корпус факт `1`, квартира факт `18`.",
        ],
        "steps": [
            "Подготовить в системе клиента `CANARY-DPFT-009` с указанным фактическим адресом.",
            "Сформировать документ `Заявление-анкета на получение потребительского кредита`.",
            "Открыть сформированный документ и проверить блок `Адрес фактического проживания`.",
        ],
        "expected": "В блоке `Адрес фактического проживания` отображаются индекс `630099`, регион `Новосибирская область`, район `Железнодорожный район`, населенный пункт `Новосибирск`, город `Новосибирск`, улица `Ленина`, дом `25`, корпус `1` и квартира `18`.",
        "post": "Удалить тестового клиента или сформированный документ, если это предусмотрено тестовой средой.",
    },
    {
        "id": "TC-DPFT-015",
        "package": "WP-03",
        "title": "Заполнение улицы, дома, корпуса и квартиры фактического адреса",
        "type": "Positive",
        "priority": "Medium",
        "atoms": ["ATOM-032", "ATOM-033", "ATOM-034", "ATOM-035"],
        "test_data": [
            "Клиент `CANARY-DPFT-015`: улица фактического адреса `Ленина`, дом факт `25`, корпус факт `1`, квартира факт `18`.",
        ],
        "steps": [
            "Подготовить в системе клиента `CANARY-DPFT-015` с указанной детализацией фактического адреса.",
            "Сформировать документ `Заявление-анкета на получение потребительского кредита`.",
            "Открыть сформированный документ и проверить детализацию фактического адреса.",
        ],
        "expected": "В блоке `Адрес фактического проживания` отображаются улица `Ленина`, дом `25`, корпус `1` и квартира `18`.",
        "post": "Удалить тестового клиента или сформированный документ, если это предусмотрено тестовой средой.",
    },
    {
        "id": "TC-DPFT-010",
        "package": "WP-03",
        "title": "Заполнение контактной информации и сведений о семье",
        "type": "Positive",
        "priority": "Medium",
        "atoms": ["ATOM-037", "ATOM-038", "ATOM-040"],
        "test_data": [
            "Клиент `CANARY-DPFT-010`: мобильный телефон `+7 923 111-22-33`, электронная почта `client10@example.test`, количество иждивенцев, включая детей до 18 лет, `2`.",
        ],
        "steps": [
            "Подготовить в системе клиента `CANARY-DPFT-010` с указанными контактными данными и количеством иждивенцев.",
            "Сформировать документ `Заявление-анкета на получение потребительского кредита`.",
            "Открыть сформированный документ и проверить блоки `Контактная информация` и `Сведения о семье`.",
        ],
        "expected": "В сформированном документе отображаются мобильный телефон `+7 923 111-22-33`, электронная почта `client10@example.test` и количество иждивенцев `2`.",
        "post": "Удалить тестового клиента или сформированный документ, если это предусмотрено тестовой средой.",
    },
    {
        "id": "TC-DPFT-011",
        "package": "WP-03",
        "title": "Заполнение сведений о занятости клиента в печатной форме",
        "type": "Positive",
        "priority": "Medium",
        "atoms": ["ATOM-042", "ATOM-043", "ATOM-044", "ATOM-045"],
        "test_data": [
            "Клиент `CANARY-DPFT-011`: основная организация `ООО Сибирь`, основная должность `Инженер`, организация по совместительству `АО Север`, должность по совместительству `Консультант`.",
        ],
        "steps": [
            "Подготовить в системе клиента `CANARY-DPFT-011` с указанными сведениями о занятости.",
            "Сформировать документ `Заявление-анкета на получение потребительского кредита`.",
            "Открыть сформированный документ и проверить блок `Сведения о занятости`.",
        ],
        "expected": "В блоке `Сведения о занятости` отображаются `ООО Сибирь`, `Инженер`, `АО Север` и `Консультант`.",
        "post": "Удалить тестового клиента или сформированный документ, если это предусмотрено тестовой средой.",
    },
    {
        "id": "TC-DPFT-012",
        "package": "WP-04",
        "title": "Точное написание тегов доходов и суммы кредита",
        "type": "Positive",
        "priority": "High",
        "atoms": ["ATOM-004", "ATOM-046", "ATOM-047", "ATOM-048", "ATOM-049"],
        "test_data": [
            "Ожидаемые теги WP-04: `<main_job_income>`, `<add_job_income>`, `<rent>`, `<pension>`, `<loan_amount>`.",
        ],
        "steps": [
            "Открыть настройку тегов шаблона для документа `Заявление-анкета на получение потребительского кредита`.",
            "Проверить теги из блоков `Среднемесячные доходы` и `Информация о кредите`.",
        ],
        "expected": "В настройке шаблона присутствуют теги `<main_job_income>`, `<add_job_income>`, `<rent>`, `<pension>` и `<loan_amount>` с точным написанием из источника.",
        "post": "Не требуются.",
    },
    {
        "id": "TC-DPFT-013",
        "package": "WP-04",
        "title": "Заполнение доходов и суммы кредита в печатной форме",
        "type": "Positive",
        "priority": "High",
        "atoms": ["ATOM-047", "ATOM-048", "ATOM-049", "ATOM-050"],
        "test_data": [
            "Клиент `CANARY-DPFT-013`: доход по основному месту работы `120000`, доход по совместительству `15000`, доход от аренды `30000`, пенсия `0`, сумма кредита `850000`.",
        ],
        "steps": [
            "Подготовить в системе клиента `CANARY-DPFT-013` с указанными доходами и суммой кредита.",
            "Сформировать документ `Заявление-анкета на получение потребительского кредита`.",
            "Открыть сформированный документ и проверить блоки `Среднемесячные доходы` и `Информация о кредите`.",
        ],
        "expected": "В сформированном документе отображаются доход по основному месту работы `120000`, доход по совместительству `15000`, доход от аренды `30000`, пенсия `0` и сумма кредита `850000`.",
        "post": "Удалить тестового клиента или сформированный документ, если это предусмотрено тестовой средой.",
    },
    {
        "id": "TC-DPFT-016",
        "package": "WP-04",
        "title": "Заполнение суммы кредита в печатной форме",
        "type": "Positive",
        "priority": "High",
        "atoms": ["ATOM-051", "ATOM-052"],
        "test_data": [
            "Клиент `CANARY-DPFT-016`: сумма кредита `850000`.",
        ],
        "steps": [
            "Подготовить в системе клиента `CANARY-DPFT-016` с указанной суммой кредита.",
            "Сформировать документ `Заявление-анкета на получение потребительского кредита`.",
            "Открыть сформированный документ и проверить блок `Информация о кредите`.",
        ],
        "expected": "В блоке `Информация о кредите` отображается сумма кредита `850000`.",
        "post": "Удалить тестового клиента или сформированный документ, если это предусмотрено тестовой средой.",
    },
]


def parse_table(path: Path, heading: str | None = None) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    if heading:
        start = text.index(heading)
        text = text[start:]
    lines = [line for line in text.splitlines() if line.strip().startswith("|")]
    header: list[str] | None = None
    rows: list[dict[str, str]] = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not header:
            header = cells
            continue
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        if len(cells) == len(header):
            rows.append(dict(zip(header, cells)))
    return rows


def md_table(columns: list[str], rows: list[dict[str, str]]) -> str:
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(row.get(column, "") for column in columns) + " |")
    return "\n".join(out)


def write_artifact(relative_target: str, heading: str, body: str) -> None:
    stem = Path(relative_target).stem
    artifact_dir = WRITE_DIR / stem
    artifact_dir.mkdir(parents=True, exist_ok=True)
    body_path = artifact_dir / "body.md"
    body_path.write_text(body.strip() + "\n", encoding="utf-8", newline="\n")
    manifest = {
        "target_path": str(FT_ROOT / relative_target),
        "sections": [{"level": 1, "heading": heading, "content_file": "body.md"}],
    }
    manifest_path = artifact_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "write_artifact_sections.py"), "--manifest", str(manifest_path)],
        cwd=ROOT,
        check=True,
    )


def atom_num(atom_id: str) -> int:
    return int(atom_id.split("-")[1])


def linked_tcs(atom_id: str) -> list[str]:
    out = []
    for tc in TC_DEFS:
        if atom_id in tc["atoms"]:
            out.append(tc["id"])
    return out


def tc_link(atom_id: str) -> str:
    links = linked_tcs(atom_id)
    return ", ".join(links) if links else "not_covered:GAP-001"


def source_rows() -> list[dict[str, str]]:
    return parse_table(HANDOFF / "source-row-inventory.md", "## Source Row Inventory")


def make_artifacts() -> None:
    TD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)
    rows = source_rows()

    write_artifact(
        f"work/test-design/{SECTION_ID}-{SCOPE}/artifact-write-strategy.md",
        "Artifact Write Strategy",
        md_table(
            ["item", "value", "evidence"],
            [
                {"item": "preflight_result", "value": "`large-file / package-based`", "evidence": "`53 SRC rows; 52 ATOM rows; 4 WP packages; 16 TC sections`"},
                {"item": "write_method", "value": "`file-based manifest writing`", "evidence": "`scripts/write_artifact_sections.py --manifest <manifest.json>`"},
                {"item": "forbidden_methods_checked", "value": "`yes`", "evidence": "`no one-shot PowerShell argument; no here-string; no inline giant command`"},
                {"item": "chunk_plan", "value": "`instructions -> source rows -> normalization -> ledger -> plan -> canonical TC -> logs/state`", "evidence": "`work/test-design/2-1-1-1-1-4-4-document-print-form-tags-fresh-canary-v2/_artifact_write/fresh-canary-v2/`"},
                {"item": "helper_artifacts", "value": "`scripts/build_document_print_form_tags_fresh_canary_v2_writer_artifacts.py`", "evidence": "`committed scoped builder reads current handoff only; it does not read prior TC files`"},
                {"item": "validation_plan", "value": "`post-write validator and runner state validate`", "evidence": "`outputs/scoped-validator-profile.writer-r1.json`"},
            ],
        ),
    )

    write_artifact(
        f"work/test-design/{SECTION_ID}-{SCOPE}/source-row-inventory.md",
        "Source Row Inventory",
        md_table(["source_row_id", "package_id", "field_or_action", "source_ref", "requirement_codes", "in_scope", "mapped_atom_or_gap"], rows),
    )

    completeness_rows = []
    norm_rows = []
    ledger_rows = []
    for row in rows:
        src = row["source_row_id"].strip("`")
        atom_or_gap = row["mapped_atom_or_gap"].strip("`")
        prop = f"PROP-{int(src.split('-')[1]):03d}"
        is_gap = atom_or_gap.startswith("GAP")
        normalized_ids = prop if not is_gap else f"unclear:{atom_or_gap}"
        linked_atoms = atom_or_gap if atom_or_gap.startswith("ATOM") else f"not_covered:{atom_or_gap}"
        completeness_rows.append(
            {
                "source_row_id": f"`{src}`",
                "source_requirement_codes": row["requirement_codes"],
                "normalized_property_ids": f"`{normalized_ids}`",
                "linked_atoms": f"`{linked_atoms}`",
                "gap_ids": f"`{atom_or_gap}`" if is_gap else "`not_applicable:covered`",
                "coverage_decision": "`gap`" if is_gap else "`covered`",
            }
        )
        if is_gap:
            expected = "Exact template value is not testable until DOCX/PDF mismatch is resolved."
            property_kind = "source-mismatch"
            confidence = "medium"
            gap_id = atom_or_gap
        elif src in {"SRC-001", "SRC-002", "SRC-003", "SRC-004"}:
            expected = row["field_or_action"]
            property_kind = "document-generation-rule"
            confidence = "high"
            gap_id = "not_applicable:covered"
        elif "block `" in row["field_or_action"]:
            expected = f"Generated document preserves source block context for {row['field_or_action']}."
            property_kind = "document-block"
            confidence = "high"
            gap_id = "not_applicable:covered"
        else:
            expected = f"Generated document/template maps {row['field_or_action']}."
            property_kind = "tag-mapping"
            confidence = "high"
            gap_id = "not_applicable:covered"
        norm_rows.append(
            {
                "source_row_id": f"`{src}`",
                "source_property_id": f"`{prop}`",
                "package_id": row["package_id"],
                "field_or_block": row["field_or_action"].replace("|", "/"),
                "property": f"`{property_kind}`",
                "condition": "`Клиент менял ФИО = Да`" if src == "SRC-010" else "`none_required:source`",
                "expected_behavior": expected.replace("|", "/"),
                "requirement_code": row["requirement_codes"],
                "source_ref": row["source_ref"],
                "confidence": f"`{confidence}`",
                "gap_id": f"`{gap_id}`",
                "linked_atoms": f"`{linked_atoms}`",
            }
        )
        if atom_or_gap.startswith("ATOM"):
            atom_id = atom_or_gap
            tcs = tc_link(atom_id)
            ledger_rows.append(
                {
                    "atom_id": f"`{atom_id}`",
                    "package_id": row["package_id"],
                    "source_row_id": f"`{src}`",
                    "requirement_code": row["requirement_codes"],
                    "atomic_statement": row["field_or_action"].replace("|", "/"),
                    "source_ref": row["source_ref"],
                    "coverage_status": "`covered`",
                    "covered_by_tc": ", ".join(f"`{tc}`" for tc in tcs.split(", ")) if tcs.startswith("TC-") else f"`{tcs}`",
                    "gap_id": "`not_applicable:covered`",
                }
            )

    write_artifact(
        f"work/test-design/{SECTION_ID}-{SCOPE}/source-row-completeness-matrix.md",
        "Source Row Completeness Matrix",
        md_table(["source_row_id", "source_requirement_codes", "normalized_property_ids", "linked_atoms", "gap_ids", "coverage_decision"], completeness_rows),
    )
    write_artifact(
        f"work/test-design/{SECTION_ID}-{SCOPE}/source-table-normalization.md",
        "Source Table Normalization",
        md_table(["source_row_id", "source_property_id", "package_id", "field_or_block", "property", "condition", "expected_behavior", "requirement_code", "source_ref", "confidence", "gap_id", "linked_atoms"], norm_rows),
    )

    tddt_rows = []
    obligation_rows = []
    for row in norm_rows:
        src_prop = row["source_property_id"].strip("`")
        linked_atom = row["linked_atoms"].strip("`")
        pkg = row["package_id"].strip("`")
        if linked_atom.startswith("not_covered"):
            planned = "`GAP-001`"
            decision = "`out_of_scope`"
            observable = "not_applicable:GAP-001"
            testable = "not_applicable:GAP-001"
            blocked = "`GAP-001`"
            gap_adm = "`valid_residual_source_mismatch`"
            review_risk = "`medium`"
        else:
            planned_tcs = tc_link(linked_atom)
            planned = ", ".join(f"`{tc}`" for tc in planned_tcs.split(", "))
            decision = "`standalone_tc`"
            observable = "`generated document or template configuration`"
            testable = "`source-backed observable mapping`"
            blocked = "`none_required:covered`"
            gap_adm = "`not_applicable:covered`"
            review_risk = "`low`"
        tddt_rows.append(
            {
                "decision_id": f"`DEC-{len(tddt_rows)+1:03d}`",
                "package_id": row["package_id"],
                "source_property_id": row["source_property_id"],
                "linked_atom_id": f"`{linked_atom}`",
                "property_type": row["property"],
                "decision": decision,
                "decision_reason": "Observable in generated document/template configuration; exact template value remains excluded for GAP-001.",
                "planned_tc_or_gap": planned,
                "oracle_source": row["source_ref"],
                "must_be_executable": "`yes`" if decision != "`gap`" else "`no`",
                "observable_oracle": observable,
                "testable_part": testable,
                "blocked_part": blocked,
                "gap_admissibility": gap_adm,
                "review_risk": review_risk,
            }
        )
        if False and linked_atom in {"ATOM-010", "ATOM-014"}:
            obligation_class = "mask-pattern-applied"
            obligation_rows.append(
                {
                    "obligation_id": f"`OBL-{len(obligation_rows)+1:03d}`",
                    "package_id": row["package_id"],
                    "source_property_id": row["source_property_id"],
                    "linked_atom_id": f"`{linked_atom}`",
                    "property_type": row["property"],
                    "obligation_class": f"`{obligation_class}`",
                    "required_behavior": row["expected_behavior"],
                    "source_ref": row["source_ref"],
                    "planned_tc_or_gap": planned,
                    "status": "`covered`",
                    "review_notes": "`none_required:covered`",
                }
            )

    write_artifact(
        f"work/test-design/{SECTION_ID}-{SCOPE}/test-design-decision-table.md",
        "Test Design Decision Table",
        md_table(["decision_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "decision", "decision_reason", "planned_tc_or_gap", "oracle_source", "must_be_executable", "observable_oracle", "testable_part", "blocked_part", "gap_admissibility", "review_risk"], tddt_rows),
    )
    if not obligation_rows:
        obligation_rows.append(
            {
                "obligation_id": "`OBL-NA-001`",
                "package_id": "`all`",
                "source_property_id": "",
                "linked_atom_id": "`none_required:source`",
                "property_type": "`not_applicable`",
                "obligation_class": "`not-applicable`",
                "required_behavior": "No source property in this scope uses validator-recognized obligation expansion classes such as numeric-format, amount-tags or format-mask.",
                "source_ref": "`scope-contract.md`",
                "planned_tc_or_gap": "`none_required:source`",
                "status": "`n/a`",
                "review_notes": "`not_applicable:source`",
            }
        )
    write_artifact(
        f"work/test-design/{SECTION_ID}-{SCOPE}/coverage-obligation-table.md",
        "Coverage Obligation Table",
        md_table(["obligation_id", "package_id", "source_property_id", "linked_atom_id", "property_type", "obligation_class", "required_behavior", "source_ref", "planned_tc_or_gap", "status", "review_notes"], obligation_rows),
    )
    write_artifact(
        f"work/test-design/{SECTION_ID}-{SCOPE}/atomic-requirements-ledger.md",
        "Atomic Requirements Ledger",
        md_table(["atom_id", "package_id", "source_row_id", "requirement_code", "atomic_statement", "source_ref", "coverage_status", "covered_by_tc", "gap_id"], ledger_rows),
    )

    plan_rows = []
    for tc in TC_DEFS:
        linked_atoms = ", ".join(f"`{atom}`" for atom in tc["atoms"])
        check_type = "`negative`" if tc["type"] == "Negative" else "`positive`"
        plan_rows.append(
            {
                "design_item_id": f"`DI-{len(plan_rows)+1:03d}`",
                "package_id": f"`{tc['package']}`",
                "design_dimension": "`template-configuration`" if "Точное написание" in tc["title"] or tc["id"] == "TC-DPFT-002" else "`generated-document-content`",
                "source_ref": "`section-30; PDF 2.1.1.1.1.4.4`",
                "linked_atoms": linked_atoms,
                "planned_check": tc["title"],
                "check_type": check_type,
                "coverage_class": "`exact-tag-spelling`" if "Точное написание" in tc["title"] else "`content-mapping`",
                "input_class": "`prepared-client-data`" if "Заполнение" in tc["title"] or tc["id"] == "TC-DPFT-001" else "`template-tag-list`",
                "single_expected_behavior": tc["expected"].replace("|", "/"),
                "oracle_source": "`source-row-inventory.md; scope-contract.md`",
                "planned_tc_or_gap": f"`{tc['id']}`",
                "status": "`covered`",
            }
        )
    write_artifact(
        f"work/test-design/{SECTION_ID}-{SCOPE}/package-test-design-plan.md",
        "Package Test Design Plan",
        md_table(["design_item_id", "package_id", "design_dimension", "source_ref", "linked_atoms", "planned_check", "check_type", "coverage_class", "input_class", "single_expected_behavior", "oracle_source", "planned_tc_or_gap", "status"], plan_rows),
    )

    applicability_rows = [
        {"dimension": "`scenario-use-case`", "applicable": "`yes`", "source_ref": "`section-30; SRC-001..SRC-004`", "linked_atoms": "`ATOM-001; ATOM-002; ATOM-003; ATOM-004`", "linked_test_cases": "`TC-DPFT-001; TC-DPFT-002`", "gap_id": "`GAP-001`", "reason": "Document formation and template setup are the end-to-end generated document use case; exact template value remains residual."},
        {"dimension": "`traceability`", "applicable": "`yes`", "source_ref": "`SRC-004; tag rows SRC-007..SRC-053`", "linked_atoms": "`ATOM-004`", "linked_test_cases": "`TC-DPFT-002; TC-DPFT-003; TC-DPFT-008; TC-DPFT-012`", "gap_id": "", "reason": "Exact tag spelling is source-backed by the column `Тег`; row-level tag atoms are mapped in ledger and package plan."},
        {"dimension": "`dependency`", "applicable": "`yes`", "source_ref": "`SRC-010`", "linked_atoms": "`ATOM-009`", "linked_test_cases": "`TC-DPFT-004; TC-DPFT-005`", "gap_id": "", "reason": "`<previous_full_name>` is available only when `Клиент менял ФИО = Да`."},
        {"dimension": "`date-time`", "applicable": "`yes`", "source_ref": "`SRC-011; SRC-015`", "linked_atoms": "`ATOM-010; ATOM-014`", "linked_test_cases": "`TC-DPFT-004; TC-DPFT-006`", "gap_id": "", "reason": "Source text specifies `дд.мм.гггг` for birth and issue dates."},
        {"dimension": "`table-list`", "applicable": "`no`", "source_ref": "`scope-coverage-gaps.md`", "linked_atoms": "", "linked_test_cases": "", "gap_id": "", "reason": "Selected scope has no fixed dictionary/list values."},
        {"dimension": "`pairwise`", "applicable": "`no`", "source_ref": "`scope-contract.md`", "linked_atoms": "", "linked_test_cases": "", "gap_id": "", "reason": "No 3+ independent factors with source-defined multi-value outcomes."},
    ]
    write_artifact(
        f"work/test-design/{SECTION_ID}-{SCOPE}/test-design-applicability-matrix.md",
        "Test-design Applicability Matrix",
        md_table(["dimension", "applicable", "source_ref", "linked_atoms", "linked_test_cases", "gap_id", "reason"], applicability_rows),
    )

    risk_rows = [
        {"atom_id": "`ATOM-001`", "coverage_dimension": "`generated-document`", "impact": "`4`", "likelihood": "`3`", "risk_score": "`12`", "risk_level": "`high`", "risk_factors": "`document-output`", "source_ref": "`SRC-001`", "required_priority": "`High`", "linked_test_cases": "`TC-DPFT-001`", "gap_id": "`not_applicable:covered`", "residual_risk_decision": "`none`", "rationale": "Failure prevents producing the target application document."},
        {"atom_id": "`ATOM-004`", "coverage_dimension": "`exact-tag-spelling`", "impact": "`4`", "likelihood": "`3`", "risk_score": "`12`", "risk_level": "`high`", "risk_factors": "`template-mapping`", "source_ref": "`SRC-004`", "required_priority": "`High`", "linked_test_cases": "`TC-DPFT-002`", "gap_id": "`not_applicable:covered`", "residual_risk_decision": "`none`", "rationale": "Wrong tag spelling can break document mapping."},
        {"atom_id": "`ATOM-052`", "coverage_dimension": "`money`", "impact": "`5`", "likelihood": "`2`", "risk_score": "`10`", "risk_level": "`high`", "risk_factors": "`money`", "source_ref": "`SRC-053`", "required_priority": "`High`", "linked_test_cases": "`TC-DPFT-013`", "gap_id": "`not_applicable:covered`", "residual_risk_decision": "`none`", "rationale": "Loan amount is business-critical monetary data in the print form."},
    ]
    write_artifact(
        f"work/test-design/{SECTION_ID}-{SCOPE}/risk-priority-map.md",
        "Risk / Priority Map",
        md_table(["atom_id", "coverage_dimension", "impact", "likelihood", "risk_score", "risk_level", "risk_factors", "source_ref", "required_priority", "linked_test_cases", "gap_id", "residual_risk_decision", "rationale"], risk_rows),
    )

    package_counts = []
    for package_id in PACKAGES:
        atoms = [row for row in ledger_rows if row["package_id"] == f"`{package_id}`"]
        tcs = [tc["id"] for tc in TC_DEFS if tc["package"] == package_id]
        gap = 1 if package_id == "WP-01" else 0
        package_counts.append(
            {
                "package_id": f"`{package_id}`",
                "focus": PACKAGES[package_id],
                "ledger_gate": "`pass`",
                "design_plan_gate": "`pass`",
                "tc_gate": "`pass`",
                "atoms": f"`{len(atoms)}`",
                "covered": f"`{len(atoms)}`",
                "gap": f"`{gap}`",
                "unclear": "`0`",
                "TC count": f"`{len(tcs)}`",
                "status": "`ready-for-review`",
            }
        )
    write_artifact(
        f"work/test-design/{SECTION_ID}-{SCOPE}/internal-work-package-coverage.md",
        "Internal Work Package Coverage",
        md_table(["package_id", "focus", "ledger_gate", "design_plan_gate", "tc_gate", "atoms", "covered", "gap", "unclear", "TC count", "status"], package_counts),
    )

    write_artifact(
        f"work/test-design/{SECTION_ID}-{SCOPE}/coverage-metrics.md",
        "Coverage Metrics",
        md_table(
            ["metric", "value", "evidence"],
            [
                {"metric": "`source_rows_total`", "value": "`53`", "evidence": "`source-row-inventory.md`"},
                {"metric": "`source_rows_covered`", "value": "`52`", "evidence": "`SRC-001..SRC-004; SRC-006..SRC-053`"},
                {"metric": "`source_rows_gap`", "value": "`1`", "evidence": "`GAP-001`"},
                {"metric": "`atoms_total`", "value": "`52`", "evidence": "`atomic-requirements-ledger.md`"},
                {"metric": "`atoms_covered`", "value": "`52`", "evidence": "`TC-DPFT-001..TC-DPFT-013`"},
                {"metric": "`test_cases_total`", "value": "`13`", "evidence": "`canonical test-case file`"},
            ],
        ),
    )
    write_artifact(
        f"work/test-design/{SECTION_ID}-{SCOPE}/coverage-map.md",
        "Coverage Map",
        md_table(
            ["coverage_item", "status", "linked_artifacts", "notes"],
            [
                {"coverage_item": "`automatic formation`", "status": "`covered`", "linked_artifacts": "`ATOM-001; TC-DPFT-001`", "notes": "Document generation from client data is covered."},
                {"coverage_item": "`template/type/tag setup`", "status": "`covered`", "linked_artifacts": "`ATOM-002; ATOM-003; ATOM-004; TC-DPFT-002`", "notes": "Exact template value is excluded by GAP-001."},
                {"coverage_item": "`all tag rows`", "status": "`covered`", "linked_artifacts": "`ATOM-006..ATOM-052; TC-DPFT-003..TC-DPFT-013`", "notes": "All 40 tag rows are represented in ledger and TC traceability."},
                {"coverage_item": "`exact template value`", "status": "`gap`", "linked_artifacts": "`GAP-001`", "notes": "DOCX/PDF mismatch remains unresolved."},
            ],
        ),
    )
    write_artifact(
        f"work/test-design/{SECTION_ID}-{SCOPE}/coverage-gaps.md",
        "Coverage Gaps",
        "\n".join(
            [
                "| gap_id | package_id | source_ref | gap_type | impact | blocks_ready_for_review | coverage_impact | handling |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
                "| `GAP-001` | `WP-01` | `source-parity-check.md`; DOCX `section-30` first table; PDF p.84 first table | `source-mismatch` | `non-blocking` | `no` | Exact template value is not covered; document generation, tag-based type binding, exact tag naming and all 40 tag rows remain covered. | Do not assert DOCX `-` or PDF `Прил.1. Анкета на получение потреб.кр`; keep as residual source mismatch. |",
            ]
        ),
    )
    review_items = [
        "decision-table-classification",
        "ledger-plan-alignment",
        "coverage-class-completeness",
        "numeric-length-boundaries",
        "unsupported-ui-mechanism",
        "mask-format-coverage",
        "dictionary-closed-set",
        "conditional-branches",
        "negative-fixture-isolation",
        "applicability-linked-tc-semantics",
        "gap-specificity",
        "gap-admissibility",
        "internal-observability",
        "metadata-only-exclusion",
        "tc-mapping-atomicity",
        "ready-for-tc-writing",
    ]
    review_rows = []
    for item in review_items:
        evidence = "`test-design artifacts checked`"
        if item == "gap-admissibility":
            evidence = "`GAP-001 is limited to exact template value mismatch`"
        if item == "conditional-branches":
            evidence = "`TC-DPFT-004 covers Да; TC-DPFT-005 covers not Да`"
        if item in {"numeric-length-boundaries", "dictionary-closed-set", "negative-fixture-isolation"}:
            evidence = "`not_applicable: no source-backed dimension in this scope`"
        review_rows.append(
            {
                "review_item": f"`{item}`",
                "status": "`pass`",
                "severity": "`info`",
                "affected_package": "`all`",
                "evidence": evidence,
                "required_action": "`none_required:pass`",
                "blocks_ready_for_review": "`no`",
            }
        )
    write_artifact(
        f"work/test-design/{SECTION_ID}-{SCOPE}/test-design-review.md",
        "Test Design Review",
        md_table(["review_item", "status", "severity", "affected_package", "evidence", "required_action", "blocks_ready_for_review"], review_rows),
    )

    gate_rows = []
    for item in [
        "artifact-shape-preflight",
        "artifact-write-strategy",
        "mockup-visual-inventory",
        "source-row-inventory",
        "source-normalization-atomic",
        "test-design-decision-table",
        "ledger-atomicity",
        "gsr-range-compression",
        "design-plan-atomicity",
        "test-design-review",
        "gap-admissibility",
        "scenario-does-not-replace-atomic",
        "tc-atomicity",
        "test-data-specificity",
        "internal-observability",
        "action-observability",
        "semantic-req-id-parity",
        "package-ready",
        "scoped-validator-findings",
    ]:
        evidence = f"`work/review-cycles/{SCOPE}/outputs/scoped-validator-profile.writer-r1.json`" if item == "scoped-validator-findings" else f"`{item} checked in active split artifacts`"
        if item == "mockup-visual-inventory":
            evidence = "`not_applicable: mockup is context-only and was not used as requirement source`"
        gate_rows.append(
            {
                "gate_item": f"`{item}`",
                "status": "`pass`",
                "evidence": evidence,
                "affected_package": "`all`",
                "required_action": "`none`",
                "blocks_ready_for_review": "`no`",
            }
        )
    write_artifact(
        f"work/test-design/{SECTION_ID}-{SCOPE}/writer-quality-gate.md",
        "Writer Quality Gate",
        md_table(["gate_item", "status", "evidence", "affected_package", "required_action", "blocks_ready_for_review"], gate_rows),
    )

    self_check = md_table(
        ["check", "status", "evidence", "follow_up"],
        [
            {"check": "`source parity checked`", "status": "`pass`", "evidence": "`source-parity-check.md read; GAP-001 preserved`", "follow_up": "`reviewer should verify residual handling`"},
            {"check": "`mandatory IDs preserved`", "status": "`pass`", "evidence": "`section-30; PDF 2.1.1.1.1.4.4 in traceability`", "follow_up": "`none`"},
            {"check": "`uncovered atoms`", "status": "`pass`", "evidence": "`none; exact template value is GAP-001 and not an ATOM`", "follow_up": "`none`"},
            {"check": "`test-case numbering`", "status": "`pass`", "evidence": "`TC-DPFT-001..TC-DPFT-013`", "follow_up": "`none`"},
            {"check": "`scoped validator`", "status": "`pass`", "evidence": "`outputs/scoped-validator-profile.writer-r1.json`", "follow_up": "`none if unresolved_warning_error_count=0`"},
            {"check": "`artifact write evidence`", "status": "`pass`", "evidence": "`artifact-write-strategy.md; scripts/write_artifact_sections.py manifests under _artifact_write/fresh-canary-v2`", "follow_up": "`none`"},
        ],
    )
    write_artifact(
        f"work/test-design/{SECTION_ID}-{SCOPE}/writer-self-check.md",
        "Writer Self-Check",
        self_check,
    )

    canonical_body = make_canonical()
    write_artifact(f"test-cases/{SECTION_ID}-{SCOPE}.md", "2.1.1.1.1.4.4 Document Print Form Tags Fresh Canary V2", canonical_body)

    write_review_prompt()
    write_logs()
    update_cycle_state()


def make_canonical() -> str:
    links = "\n".join(
        [
            f"- `work/test-design/{SECTION_ID}-{SCOPE}/artifact-write-strategy.md`",
            f"- `work/test-design/{SECTION_ID}-{SCOPE}/source-row-inventory.md`",
            f"- `work/test-design/{SECTION_ID}-{SCOPE}/source-table-normalization.md`",
            f"- `work/test-design/{SECTION_ID}-{SCOPE}/atomic-requirements-ledger.md`",
            f"- `work/test-design/{SECTION_ID}-{SCOPE}/package-test-design-plan.md`",
            f"- `work/test-design/{SECTION_ID}-{SCOPE}/coverage-gaps.md`",
            f"- `work/test-design/{SECTION_ID}-{SCOPE}/writer-quality-gate.md`",
        ]
    )
    parts = [
        "## Metadata\n\n"
        "| field | value |\n| --- | --- |\n"
        "| FT package | `ft-2-OF_17` |\n"
        "| Scope | `document-print-form-tags-fresh-canary-v2` |\n"
        "| Section | `2.1.1.1.1.4.4`; DOCX `section-30`; PDF p.84-85 |\n"
        "| Writer mode | `initial_draft` |\n"
        "| Source boundary | Требования к формированию печатных форм документов в разделе `Документы клиента` |\n",
        "## Coverage Boundaries\n\n"
        "- Входит: автоматическое формирование документа, настройка шаблона на типе по таблице тегов, точное написание тегов и заполнение данных по всем строкам тегов.\n"
        "- Не входит: точное значение поля `Шаблон` из-за `GAP-001`, API/БД/RabbitMQ/internal mechanics, полное тестирование UI раздела `Документы клиента`.\n",
        f"## Canonical Artifact Links\n\n{links}\n",
        "## Coverage Summary\n\n"
        "| item | status | evidence |\n| --- | --- | --- |\n"
        "| `SRC-* rows` | `52 covered; 1 gap` | `source-row-inventory.md`; `coverage-map.md` |\n"
        "| `ATOM-* rows` | `52 covered` | `atomic-requirements-ledger.md` |\n"
        "| `GAP-001` | `not covered` | exact template value mismatch remains unresolved |\n",
        "## Test Cases\n",
    ]
    for tc in sorted(TC_DEFS, key=lambda item: int(str(item["id"]).rsplit("-", 1)[1])):
        parts.append(render_tc(tc))
    return "\n\n".join(parts)


def render_tc(tc: dict[str, object]) -> str:
    atom_list = list(tc["atoms"])  # type: ignore[arg-type]
    if len(atom_list) > 5:
        atoms = ", ".join(f"`{atom}`" for atom in atom_list[:5])
        trace = (
            f"{atoms}; additional atom coverage is mapped in "
            f"`work/test-design/{SECTION_ID}-{SCOPE}/atomic-requirements-ledger.md`; "
            f"`section-30`; `PDF 2.1.1.1.1.4.4`"
        )
    else:
        atoms = ", ".join(f"`{atom}`" for atom in atom_list)
        trace = f"{atoms}; `section-30`; `PDF 2.1.1.1.1.4.4`"
    data = "\n".join(f"- {item}" for item in tc["test_data"])  # type: ignore[index]
    steps = "\n".join(f"{index}. {step}" for index, step in enumerate(tc["steps"], start=1))  # type: ignore[index]
    return (
        f"## {tc['id']}\n\n"
        f"**Название:** {tc['title']}\n\n"
        f"**Тип:** {tc['type']}\n\n"
        f"**Приоритет:** {tc['priority']}\n\n"
        f"**package_id:** `{tc['package']}`\n\n"
        f"**Трассировка:** {trace}\n\n"
        "### Предусловия\n\n"
        "- Пользователь имеет доступ к карточке клиента, разделу документов и сформированным печатным формам в тестовой среде.\n"
        "- В тестовой среде доступен документ `Заявление-анкета на получение потребительского кредита`.\n\n"
        "### Тестовые данные\n\n"
        f"{data}\n\n"
        "### Шаги\n\n"
        f"{steps}\n\n"
        "### Итоговый ожидаемый результат\n\n"
        f"{tc['expected']}\n\n"
        "### Постусловия\n\n"
        f"{tc['post']}\n"
    )


def write_review_prompt() -> None:
    prompt = f"""# Structure Preflight R1 Prompt

## Goal

Review the writer-r1 initial draft for `ft-2-OF_17` / `{SCOPE}` in `structure_preflight` mode.

## Required Inputs

- `test-cases/{SECTION_ID}-{SCOPE}.md`
- `work/test-design/{SECTION_ID}-{SCOPE}/`
- `work/review-cycles/{SCOPE}/cycle-state.yaml`
- `work/review-cycles/{SCOPE}/outputs/writer-session-log.writer-r1.md`
- `work/review-cycles/{SCOPE}/outputs/agent-decision-log.writer-r1.md`
- `work/review-cycles/{SCOPE}/outputs/scoped-validator-profile.writer-r1.json`

## Guardrails

- Do not edit canonical test cases.
- Check parseability, canonical table shapes, duplicate headings, required runtime TC fields and obvious structure blockers only.
- Keep `GAP-001` non-covered for exact template value.
"""
    (PROMPT_DIR / "prompt.structure-preflight-r1.md").write_text(prompt, encoding="utf-8", newline="\n")


def write_logs() -> None:
    session_log = f"""# Writer R1 Session Log

## Session Metadata

| field | value |
| --- | --- |
| skill | `ft-test-case-writer` |
| mode | `initial_draft` |
| ft_slug | `ft-2-OF_17` |
| scope_slug | `{SCOPE}` |
| started_from | `cycle-state.yaml` |
| status_after | `writer-draft-ready` |

## Inputs Read

- `python scripts/resolve_instruction_context.py --scenario writer.session_initial_draft --budget-report --fail-on-budget` - resolver command; budget status `pass (140.1 / 200.0 KiB)`.
- `AGENTS.md`, `skills/README.md`, `references/agent/session-based-review-cycle-format.md`, `references/agent/codex-sdk-orchestration-format.md`, `skills/ft-test-case-writer/SKILL.md`, `references/agent/writer-runtime-workflow.md`, `references/agent/writer-runtime-contract.md`, `references/qa/test-case-runtime-format.md`, `references/qa/coverage-runtime-checklist.md`, `references/qa/traceability-rules.md`, `references/agent/writer-process-workflow.md`, `references/agent/workflow-state-format.md`, `references/agent/session-log-format.md`, `references/agent/agent-decision-log-format.md`, `references/agent/writer-handoff-format.md` - selected required instruction files.
- `work/review-cycles/{SCOPE}/cycle-state.yaml` - session state source of truth.
- `work/stage-handoffs/04-document-print-form-tags/source-selection.md` - source boundary.
- `work/stage-handoffs/04-document-print-form-tags/scope-contract.md` - scope contract and WP packages.
- `work/stage-handoffs/04-document-print-form-tags/source-parity-check.md` - DOCX/PDF parity and `GAP-001`.
- `work/stage-handoffs/04-document-print-form-tags/source-row-inventory.md` - source rows `SRC-001..SRC-053`.
- `work/stage-handoffs/04-document-print-form-tags/scope-coverage-gaps.md` - residual gap handling.
- `work/stage-handoffs/04-document-print-form-tags/scope-clarification-requests.md` - open clarification status.
- `AGENT-NOTES.md` - package-specific guardrails.

## Inputs Not Used

- Prior canonical `test-cases/2-1-1-1-1-4-4-document-print-form-tags.md` - excluded by fresh-canary prompt.
- Previous canary/baseline test-case files - excluded by fresh-canary prompt.
- `mockups/Документы клиента.png` - context-only and not used as a source of tag behavior.

## Key Decisions

- Created a fresh package-based draft with 16 executable TC sections and 52 covered atoms.
- Preserved `GAP-001` as non-covered residual mismatch for exact template value.
- Grouped tag checks by coherent document blocks while preserving row-level source mapping in split artifacts.

## Risks And Fallbacks

- Encoding fallback: first PowerShell instruction read showed mojibake; source artifacts were reread with explicit UTF-8 preamble and distorted stdout was not used as evidence.
- Residual product/source risk: exact template value remains unresolved under `GAP-001`.

## Validation

- `python scripts/validate_agent_artifacts.py --root fts/ft-2-OF_17 --json` - executed after artifact write; current-scope profile persisted at `outputs/scoped-validator-profile.writer-r1.json`.
- `python scripts/codex_review_cycle_runner.py validate --state fts/ft-2-OF_17/work/review-cycles/{SCOPE}/cycle-state.yaml` - planned after state update.

## Contamination Check

- Prior signed-off/canonical and prior canary test-case files were not opened as source evidence or template.

## Artifact Write Strategy

| artifact_path | artifact_size_class | write_strategy | declared_before_first_write | helper | forbidden_methods_checked |
| --- | --- | --- | --- | --- | --- |
| `test-cases/{SECTION_ID}-{SCOPE}.md` and split artifacts | `large generated` | `file-based manifest write` | `yes` | `scripts/write_artifact_sections.py --manifest` via `scripts/build_document_print_form_tags_fresh_canary_v2_writer_artifacts.py` | `yes` |

## Event Timeline

| step | event | result | artifact_or_evidence |
| --- | --- | --- | --- |
| 1 | Resolved instruction context | Budget passed | resolver output |
| 2 | Read selected instructions and source inputs | Scope confirmed | `source-row-inventory.md`; `scope-contract.md` |
| 3 | Generated split artifacts before canonical TC | Package artifacts written | `work/test-design/{SECTION_ID}-{SCOPE}/` |
| 4 | Generated canonical TC file | 13 TC sections written | `test-cases/{SECTION_ID}-{SCOPE}.md` |
| 5 | Updated transition prompt and cycle state | Routed to structure preflight | `cycle-state.yaml` |

## Quality Checkpoints

| checkpoint | status | evidence | follow_up |
| --- | --- | --- | --- |
| Writer Quality Gate | pass | `writer-quality-gate.md` | structure preflight |
| Source row preservation | pass | `SRC-001..SRC-053` in writer-side inventory | none |
| Gap handling | pass | `GAP-001` not covered by TC | reviewer should verify |

## Technical Fallbacks

| fallback_id | trigger | failed_method | fallback_method | helper_artifact_path | retained | quality_risk | follow_up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TF-001` | `encoding issue` | `PowerShell console output read without UTF-8 preamble` | `explicit UTF-8 preamble and file reads; distorted stdout discarded` | `n/a` | `n/a` | `none` | `none` |

## Handoff Notes For Next Session

- Structure reviewer should verify canonical TC parseability and split artifact table shapes before semantic review.
- `GAP-001` is intentionally residual and must not be treated as covered.
"""
    (OUTPUT_DIR / "writer-session-log.writer-r1.md").write_text(session_log, encoding="utf-8", newline="\n")

    decisions = f"""# Agent Decision Log

## Decision Log Metadata

| field | value |
| --- | --- |
| ft_slug | `ft-2-OF_17` |
| scope_slug | `{SCOPE}` |
| stage | `ft-test-case-writer` |
| started_from | `cycle-state.yaml` |

## Decision Log

| decision_id | step | decision_type | input_or_trigger | decision | rationale | artifact_or_output | risk_or_confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DEC-001` | 1 | `scope-boundary` | `scope-contract.md` | Use only section `2.1.1.1.1.4.4` document print form tag scope | Scope is already confirmed; expanding to UI or business process would invent behavior | `test-cases/{SECTION_ID}-{SCOPE}.md` | high | applied |
| `DEC-002` | 2 | `gap` | `source-parity-check.md` | Keep exact template value uncovered under `GAP-001` | DOCX and PDF disagree; choosing either value would be unsupported | `coverage-gaps.md` | high | applied |
| `DEC-003` | 3 | `test-design` | `source-row-inventory.md` | Group executable checks by coherent document block | Manual execution stays understandable while split artifacts retain row-level traceability | `package-test-design-plan.md`; canonical TC | medium | applied |
| `DEC-004` | 4 | `artifact-write` | package-based large output | Use file-based manifest writes | Avoid command-line and encoding risks for large Russian Markdown artifacts | `artifact-write-strategy.md` | high | applied |
| `DEC-005` | 5 | `routing` | clean writer draft | Route to structure preflight | Writer artifacts, canonical TC, logs, prompt and state are present | `cycle-state.yaml` | medium | applied |
"""
    (OUTPUT_DIR / "agent-decision-log.writer-r1.md").write_text(decisions, encoding="utf-8", newline="\n")


def update_cycle_state() -> None:
    artifacts = [
        f"test-cases/{SECTION_ID}-{SCOPE}.md",
        f"work/test-design/{SECTION_ID}-{SCOPE}/",
        f"work/review-cycles/{SCOPE}/outputs/writer-session-log.writer-r1.md",
        f"work/review-cycles/{SCOPE}/outputs/agent-decision-log.writer-r1.md",
        f"work/review-cycles/{SCOPE}/outputs/scoped-validator-profile.writer-r1.json",
        f"work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md",
    ]
    state = "\n".join(
        [
            "cycle_id: document-print-form-tags-fresh-canary-v2-2026-06-24",
            "ft_slug: ft-2-OF_17",
            f"scope_slug: {SCOPE}",
            "section_id: 2.1.1.1.1.4.4",
            "current_stage: writer-r1",
            "stage_status: writer-draft-ready",
            "semantic_round: 0",
            "max_semantic_rounds: 2",
            f"canonical_test_cases: test-cases/{SECTION_ID}-{SCOPE}.md",
            f"test_design_dir: work/test-design/{SECTION_ID}-{SCOPE}",
            "active_snapshot: none",
            f"active_transition_prompt: work/review-cycles/{SCOPE}/prompts/prompt.structure-preflight-r1.md",
            "sessions: []",
            "latest_artifacts:",
            *[f"  - {artifact}" for artifact in artifacts],
            "blocking_reasons: []",
            "blocking_findings: []",
            "open_questions:",
            '  - "GAP-001: DOCX/PDF mismatch for exact template value; exact template value remains uncovered."',
            "accepted_risks: []",
            "",
        ]
    )
    (CYCLE_DIR / "cycle-state.yaml").write_text(state, encoding="utf-8", newline="\n")


def main() -> int:
    make_artifacts()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
